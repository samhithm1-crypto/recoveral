"""
deleted_recovery.py — Deleted File Recovery Engine
Handles Recycle Bin parsing, drive free-space carving, and
Windows artifact recovery for RecoverAI.
"""

import os
import io
import struct
import hashlib
import shutil
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ── Import file-type detection from existing analyzer ────────────────────────
try:
    from analyzer import detect_signature, calculate_integrity, PRIORITY_MAP
except ImportError:
    def detect_signature(data):
        return "Unknown", "unknown", "bin"
    def calculate_integrity(data, ftype):
        return {"score": 50, "status": "PARTIAL", "color": "yellow",
                "entropy": 0.0, "null_ratio": 0.0}
    PRIORITY_MAP = {}

# ── Active scan jobs ──────────────────────────────────────────────────────────
_scan_jobs: dict = {}   # job_id → {status, progress, results, error}
_jobs_lock = threading.Lock()

# ═══════════════════════════════════════════════════════════════════════════════
# 1. RECYCLE BIN RECOVERY
# ═══════════════════════════════════════════════════════════════════════════════

FILETIME_EPOCH_DELTA = 116444736000000000  # 100ns intervals from 1601-01-01 to 1970-01-01

def _filetime_to_dt(ft: int) -> str:
    """Convert Windows FILETIME (100-ns intervals since 1601-01-01) to ISO string."""
    try:
        ts = (ft - FILETIME_EPOCH_DELTA) / 10_000_000
        return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return "Unknown"

def _parse_recycle_i_file(i_path: str) -> dict | None:
    """
    Parse a $I metadata file from the Windows Recycle Bin.
    Returns dict with original_path, deleted_at, file_size, or None on error.
    """
    try:
        with open(i_path, "rb") as f:
            data = f.read()
        if len(data) < 24:
            return None

        version   = struct.unpack_from("<q", data, 0)[0]
        file_size = struct.unpack_from("<q", data, 8)[0]
        del_time  = struct.unpack_from("<q", data, 16)[0]

        if version == 1:
            # Windows Vista / 7 / 8: fixed-size 260 UTF-16LE chars at offset 24
            raw_path = data[24:24 + 520]
        elif version == 2:
            # Windows 10+: 4-byte length + UTF-16LE string at offset 24
            if len(data) < 28:
                return None
            path_len = struct.unpack_from("<i", data, 24)[0]
            raw_path = data[28:28 + path_len * 2]
        else:
            raw_path = data[24:]

        original_path = raw_path.decode("utf-16-le", errors="replace").rstrip("\x00")
        return {
            "original_path": original_path,
            "deleted_at":    _filetime_to_dt(del_time),
            "file_size":     file_size,
        }
    except Exception:
        return None


def scan_recycle_bin() -> list:
    """
    Scan the Windows Recycle Bin ($Recycle.Bin) on all drives.
    Parses $I metadata files for original paths, then falls back
    to scanning $R data files directly.
    Returns list of recoverable deleted file dicts.
    """
    results  = []
    item_id  = 0
    seen_r   = set()

    # Build a map of $I metadata first
    i_meta: dict = {}   # r_path → meta dict

    drives = get_available_drives()
    for drive in drives:
        recycle_root = f"{drive}:\\$Recycle.Bin"
        if not os.path.exists(recycle_root):
            continue
        try:
            sids = os.listdir(recycle_root)
        except PermissionError:
            continue

        for sid in sids:
            sid_path = os.path.join(recycle_root, sid)
            if not os.path.isdir(sid_path):
                continue
            try:
                fnames = os.listdir(sid_path)
            except PermissionError:
                continue

            # ── Phase 1: parse $I metadata files ────────────────────────────
            for fname in fnames:
                if not fname.upper().startswith("$I"):
                    continue
                i_path  = os.path.join(sid_path, fname)
                r_fname = "$R" + fname[2:]
                r_path  = os.path.join(sid_path, r_fname)
                meta    = _parse_recycle_i_file(i_path)
                if meta and meta.get("original_path"):
                    i_meta[r_path.upper()] = meta

            # ── Phase 2: enumerate every $R file (actual data) ───────────────
            for fname in fnames:
                if not fname.upper().startswith("$R"):
                    continue
                r_path = os.path.join(sid_path, fname)
                key    = r_path.upper()
                if key in seen_r:
                    continue
                seen_r.add(key)

                # Look up metadata from Phase 1
                meta = i_meta.get(key)
                orig = meta["original_path"] if meta else ""
                deleted_at = meta["deleted_at"] if meta else "Unknown"
                ext  = Path(orig).suffix.lstrip(".").lower() if orig else \
                       Path(fname).suffix.lstrip(".").lower() or "bin"

                try:
                    size_b = os.path.getsize(r_path)
                except Exception:
                    size_b = meta["file_size"] if meta else 0

                # Skip empty files
                if size_b == 0:
                    continue

                # Detect type & integrity
                type_name, category, _ = "Unknown", "unknown", ext
                integrity = {"score": 50, "status": "PARTIAL",
                             "entropy": 0.0, "null_ratio": 0.0}
                sha256 = ""
                try:
                    with open(r_path, "rb") as fh:
                        sample = fh.read(8192)
                    type_name, category, _ = detect_signature(sample)
                    integrity = calculate_integrity(sample, category)
                    sha256    = hashlib.sha256(sample).hexdigest()[:16]
                except Exception:
                    pass

                display_name = Path(orig).name if orig else fname
                results.append({
                    "id":            item_id,
                    "item_key":      f"{sid[:8]}_{fname}",
                    "original_path": orig,
                    "filename":      display_name,
                    "extension":     ext,
                    "deleted_at":    deleted_at,
                    "size_kb":       round(size_b / 1024, 2),
                    "type_name":     type_name,
                    "category":      category,
                    "integrity":     integrity,
                    "sha256":        sha256,
                    "r_path":        r_path,
                    "recoverable":   True,
                    "source":        "recycle_bin",
                    "drive":         drive,
                })
                item_id += 1

    results.sort(key=lambda x: x["integrity"]["score"], reverse=True)
    return results



def restore_from_recycle_bin(r_path: str, destination: str) -> dict:
    """
    Restore a file from Recycle Bin $R file to destination path.
    If destination is empty, restores to Desktop/RecoverAI_Restored/.
    """
    try:
        import pathlib
        if not r_path or not os.path.exists(r_path):
            return {"success": False, "error": f"Source file not found: {r_path}"}

        # Auto-destination: Desktop/RecoverAI_Restored/
        if not destination:
            desktop = pathlib.Path.home() / "Desktop" / "RecoverAI_Restored"
            desktop.mkdir(parents=True, exist_ok=True)
            filename = os.path.basename(r_path)
            destination = str(desktop / filename)

        # Avoid overwriting existing files
        dest_path = pathlib.Path(destination)
        if dest_path.exists():
            stem, suffix = dest_path.stem, dest_path.suffix
            i = 1
            while dest_path.exists():
                dest_path = dest_path.parent / f"{stem}_{i}{suffix}"
                i += 1
            destination = str(dest_path)

        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(r_path, destination)
        return {"success": True, "restored_to": destination}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DRIVE FREE-SPACE CARVER
# ═══════════════════════════════════════════════════════════════════════════════

# File signatures for carving (magic bytes → (name, category, extension))
CARVE_SIGNATURES = [
    (b"\xFF\xD8\xFF",             "JPEG Image",          "image",    "jpg"),
    (b"\x89PNG\r\n\x1a\n",        "PNG Image",           "image",    "png"),
    (b"GIF87a",                   "GIF Image",           "image",    "gif"),
    (b"GIF89a",                   "GIF Image",           "image",    "gif"),
    (b"%PDF-",                    "PDF Document",        "document", "pdf"),
    (b"PK\x03\x04",              "ZIP/Office Archive",  "archive",  "zip"),
    (b"\xD0\xCF\x11\xE0",        "MS Office (legacy)",  "document", "doc"),
    (b"RIFF",                     "WAV/AVI Media",       "media",    "riff"),
    (b"ID3",                      "MP3 Audio",           "media",    "mp3"),
    (b"\x00\x00\x00 ftyp",        "MP4 Video",           "media",    "mp4"),
    (b"SQLite format 3",          "SQLite Database",     "database", "db"),
    (b"\x1f\x8b\x08",            "GZIP Archive",        "archive",  "gz"),
    (b"BZh",                      "BZIP2 Archive",       "archive",  "bz2"),
    (b"7z\xBC\xAF\x27\x1C",      "7-Zip Archive",       "archive",  "7z"),
    (b"<!DOCTYPE html",           "HTML Document",       "web",      "html"),
    (b"<html",                    "HTML Document",       "web",      "html"),
    (b"{\"",                      "JSON Data",           "data",     "json"),
    (b"MZ",                       "Windows Executable",  "binary",   "exe"),
    (b"\x7fELF",                  "ELF Binary",          "binary",   "elf"),
]

MAX_CARVE_RESULTS = 200   # stop after this many finds per drive
SECTOR_SIZE       = 512
READ_CHUNK_SIZE   = 512 * 1024   # 512 KB per read


def get_available_drives() -> list:
    """Return list of available drive letters on Windows."""
    drives = []
    if os.name == "nt":
        import ctypes
        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            if bitmask & (1 << i):
                drives.append(letter)
    else:
        # On Linux/Mac, return mounted volumes
        drives = [""]  # root
    return drives


def get_drive_info() -> list:
    """Return detailed info about each drive."""
    result = []
    for letter in get_available_drives():
        try:
            path = f"{letter}:\\" if os.name == "nt" else "/"
            total, used, free = shutil.disk_usage(path)
            result.append({
                "letter": letter,
                "path":   path,
                "total_gb": round(total / 1e9, 1),
                "used_gb":  round(used  / 1e9, 1),
                "free_gb":  round(free  / 1e9, 1),
                "pct_used": round(used / total * 100, 1),
            })
        except Exception:
            continue
    return result


def _carve_drive_job(job_id: str, drive_letter: str, max_results: int = MAX_CARVE_RESULTS):
    """Background thread: carve deleted files from a drive's raw sectors."""
    global _scan_jobs
    results  = []
    found_id = 0

    # Build (sig_bytes, name, category, ext) lookup
    sigs = [(s, n, c, e) for s, n, c, e in CARVE_SIGNATURES]

    # Try raw volume access on Windows: \\.\C:
    drive_path = f"\\\\.\\{drive_letter}:" if os.name == "nt" else f"/dev/{drive_letter}"

    try:
        fh = open(drive_path, "rb", buffering=0)
    except PermissionError:
        with _jobs_lock:
            _scan_jobs[job_id]["status"] = "error"
            _scan_jobs[job_id]["error"]  = (
                "Administrator privileges required to read raw drive sectors. "
                "Run the server as Administrator and try again."
            )
        return
    except FileNotFoundError:
        with _jobs_lock:
            _scan_jobs[job_id]["status"] = "error"
            _scan_jobs[job_id]["error"]  = f"Drive {drive_letter}: not found."
        return
    except Exception as e:
        with _jobs_lock:
            _scan_jobs[job_id]["status"] = "error"
            _scan_jobs[job_id]["error"]  = str(e)
        return

    try:
        # Estimate total size for progress
        fh.seek(0, 2)
        total_bytes = fh.tell()
        fh.seek(0)
    except Exception:
        total_bytes = 0

    scanned   = 0
    leftover  = b""

    with _jobs_lock:
        _scan_jobs[job_id]["status"] = "running"
        _scan_jobs[job_id]["total_bytes"] = total_bytes

    try:
        while found_id < max_results:
            chunk = fh.read(READ_CHUNK_SIZE)
            if not chunk:
                break
            scanned += len(chunk)
            buf = leftover + chunk

            for sig, name, cat, ext in sigs:
                pos = 0
                while True:
                    idx = buf.find(sig, pos)
                    if idx == -1:
                        break
                    abs_offset = scanned - len(buf) + idx
                    sample     = buf[idx:idx + 8192]
                    if len(sample) < 16:
                        pos = idx + 1
                        continue

                    integrity = calculate_integrity(sample, cat)
                    sha       = hashlib.sha256(sample).hexdigest()[:16]
                    results.append({
                        "id":        found_id,
                        "filename":  f"DELETED_{found_id:05d}.{ext}",
                        "type_name": name,
                        "category":  cat,
                        "extension": ext,
                        "offset":    abs_offset,
                        "offset_hex":f"0x{abs_offset:016X}",
                        "size_kb":   round(len(sample) / 1024, 2),
                        "integrity": integrity,
                        "sha256":    sha,
                        "source":    "drive_carve",
                        "drive":     drive_letter,
                        "recoverable": integrity["score"] >= 40,
                        "sample":    sample.hex()[:128],   # first 64 bytes for AI
                    })
                    found_id += 1
                    pos = idx + 1
                    if found_id >= max_results:
                        break
                if found_id >= max_results:
                    break

            # Keep last 64 bytes as overlap for cross-chunk signatures
            leftover = buf[-64:]

            # Update progress
            pct = round(scanned / total_bytes * 100, 1) if total_bytes else 0
            with _jobs_lock:
                _scan_jobs[job_id]["progress"]     = pct
                _scan_jobs[job_id]["found"]        = found_id
                _scan_jobs[job_id]["scanned_mb"]   = round(scanned / 1e6, 1)

    except Exception as e:
        with _jobs_lock:
            _scan_jobs[job_id]["error"] = str(e)
    finally:
        fh.close()

    results.sort(key=lambda x: x["integrity"]["score"], reverse=True)
    with _jobs_lock:
        _scan_jobs[job_id]["status"]   = "done"
        _scan_jobs[job_id]["progress"] = 100
        _scan_jobs[job_id]["results"]  = results
        _scan_jobs[job_id]["found"]    = len(results)


def start_drive_carve(drive_letter: str) -> str:
    """Launch a background drive carving job. Returns job_id."""
    job_id = str(uuid.uuid4())[:8].upper()
    with _jobs_lock:
        _scan_jobs[job_id] = {
            "status":     "queued",
            "progress":   0,
            "found":      0,
            "scanned_mb": 0,
            "total_bytes": 0,
            "results":    [],
            "error":      None,
            "drive":      drive_letter,
            "started_at": datetime.now().isoformat(),
        }
    t = threading.Thread(
        target=_carve_drive_job,
        args=(job_id, drive_letter),
        daemon=True,
    )
    t.start()
    return job_id


def get_job_status(job_id: str) -> dict | None:
    with _jobs_lock:
        return _scan_jobs.get(job_id)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. WINDOWS ARTIFACT RECOVERY (no admin needed)
# ═══════════════════════════════════════════════════════════════════════════════

def scan_temp_artifacts() -> list:
    """
    Scan common Windows locations for recoverable artifacts:
    - %TEMP% / %TMP%
    - Recent files
    - Windows prefetch
    - Browser cache (Chrome, Edge, Firefox)
    """
    results = []
    item_id = 0
    seen    = set()

    scan_locations = []

    # Windows TEMP directories
    for env_var in ("TEMP", "TMP", "LOCALAPPDATA"):
        base = os.environ.get(env_var, "")
        if base:
            scan_locations.extend([
                (os.path.join(base, "Temp"),                 "Windows Temp"),
                (os.path.join(base, "Microsoft", "Windows", "Recent"), "Recent Files"),
            ])

    # APPDATA
    appdata = os.environ.get("APPDATA", "")
    local   = os.environ.get("LOCALAPPDATA", "")
    if appdata:
        scan_locations.extend([
            (os.path.join(appdata, "Microsoft", "Windows", "Recent"), "Recent Files"),
        ])
    if local:
        scan_locations.extend([
            (os.path.join(local, "Google", "Chrome", "User Data", "Default", "Cache", "Cache_Data"), "Chrome Cache"),
            (os.path.join(local, "Microsoft", "Edge",   "User Data", "Default", "Cache", "Cache_Data"), "Edge Cache"),
        ])

    # Firefox
    ff_profiles = os.path.join(appdata, "Mozilla", "Firefox", "Profiles") if appdata else ""
    if ff_profiles and os.path.exists(ff_profiles):
        for prof in os.listdir(ff_profiles):
            scan_locations.append(
                (os.path.join(ff_profiles, prof, "cache2", "entries"), "Firefox Cache")
            )

    for folder, label in scan_locations:
        if not folder or not os.path.isdir(folder):
            continue
        try:
            for entry in os.scandir(folder):
                if not entry.is_file(follow_symlinks=False):
                    continue
                if entry.path in seen:
                    continue
                seen.add(entry.path)
                try:
                    size_b = entry.stat().st_size
                    if size_b < 64:
                        continue
                    if size_b > 100 * 1024 * 1024:  # skip >100MB
                        continue
                    with open(entry.path, "rb") as fh:
                        sample = fh.read(8192)
                    type_name, category, ext = detect_signature(sample)
                    integrity = calculate_integrity(sample, category)
                    sha = hashlib.sha256(sample).hexdigest()[:16]
                    results.append({
                        "id":            item_id,
                        "filename":      entry.name,
                        "original_path": entry.path,
                        "location":      label,
                        "type_name":     type_name,
                        "category":      category,
                        "extension":     ext,
                        "size_kb":       round(size_b / 1024, 2),
                        "integrity":     integrity,
                        "sha256":        sha,
                        "source":        "temp_artifact",
                        "recoverable":   True,
                        "modified":      datetime.fromtimestamp(
                            entry.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                    })
                    item_id += 1
                except Exception:
                    continue
        except PermissionError:
            continue

    results.sort(key=lambda x: x["integrity"]["score"], reverse=True)
    return results[:300]   # cap at 300 artifacts
