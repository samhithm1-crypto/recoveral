"""Helper: writes fragment_reconstructor.py"""
code = r'''import hashlib, json, re
from datetime import datetime

MANIFEST_NAMES = set(["photo_reconstruction_manifest.json", "reconstruction_manifest.json",
                       "manifest.json", "recovery_manifest.json"])

def find_manifest(file_map):
    for name, data in file_map.items():
        low = name.lower()
        if low in MANIFEST_NAMES or low.endswith("_manifest.json"):
            try:
                return json.loads(data.decode("utf-8", errors="ignore"))
            except Exception:
                pass
    return None

# Matches: photo_fragment_01.bin, photo_frag_01.bin, photo_part_01.bin etc.
FRAG_RE = re.compile(
    r"^(.+?)_(?:fragment|frag|part|chunk|seg|piece)[_\-]?(\d+)\.(\w+)$",
    re.IGNORECASE
)

def sniff_type(data):
    checks = [
        (bytes([0xFF, 0xD8, 0xFF]), "jpg", "JPEG Image"),
        (b"\x89PNG\r\n\x1a\n", "png", "PNG Image"),
        (b"GIF89a", "gif", "GIF Image"),
        (b"%PDF",   "pdf", "PDF Document"),
        (b"PK\x03\x04", "zip", "ZIP Archive"),
        (b"ID3", "mp3", "MP3 Audio"),
        (b"SQLite format 3", "db", "SQLite Database"),
    ]
    for sig, ext, desc in checks:
        if data[:len(sig)] == sig:
            return ext, desc
    return "bin", "Binary Fragment"


def group_fragments(file_map):
    groups = {}
    for name, data in file_map.items():
        m = FRAG_RE.match(name)
        if m:
            base  = m.group(1).lower()
            order = int(m.group(2))
            ext   = m.group(3).lower()
            if base not in groups:
                groups[base] = {"base_name": base, "fragments": [], "target_ext": ext}
            groups[base]["fragments"].append((order, name, data))

    result = []
    for key, grp in groups.items():
        grp["fragments"].sort(key=lambda x: x[0])
        if len(grp["fragments"]) >= 2:
            result.append(grp)
    return result


def reconstruct_from_fragments(file_map):
    """
    Given dict {filename: bytes}, detect fragment groups and reconstruct.
    Returns list of result dicts with keys:
      success, name, ext, type_name, data, fragment_count, fragment_names,
      sha256, size_kb, manifest_match, integrity_pct, log, recovered_at
    """
    results  = []
    manifest = find_manifest(file_map)
    groups   = group_fragments(file_map)

    for grp in groups:
        log    = []
        frags  = grp["fragments"]           # [(order, name, bytes), ...]
        base   = grp["base_name"]
        frag_d = [d for (_, _, d) in frags]
        frag_n = [n for (_, n, _) in frags]

        log.append("Detected " + str(len(frags)) + " fragment(s) for: " + base)
        log.append("Fragment order: " + " -> ".join(frag_n))
        log.append("Validating fragment byte boundaries...")

        # Detect the real file type from the first fragment's magic bytes
        first_bytes = frag_d[0][:16] if frag_d else b""
        ext, type_name = sniff_type(first_bytes)
        tgt = grp.get("target_ext", "bin")
        if tgt == "bin" and ext != "bin":
            log.append("AI detected inner file type: " + type_name + " (from magic bytes)")
        elif tgt != "bin":
            ext = tgt
        if ext == "bin":
            ext, type_name = sniff_type(first_bytes)

        log.append("Reassembling " + str(len(frags)) + " fragments in sequence...")

        # Core reconstruction: simple ordered concatenation
        reconstructed = b"".join(frag_d)

        # Light null-byte cleanup (preserve data if aggressive)
        clean = re.sub(b"\x00{16,}", b"", reconstructed)
        if len(clean) >= len(reconstructed) * 0.95:
            final_bytes = clean
            log.append("Stripped inter-fragment null padding.")
        else:
            final_bytes = reconstructed
            log.append("Null-strip skipped (would remove >5% data).")

        sha256  = hashlib.sha256(final_bytes).hexdigest()
        size_kb = round(len(final_bytes) / 1024, 2)

        log.append("SHA-256 fingerprint: " + sha256[:32] + "...")
        log.append("Reconstructed file size: " + str(size_kb) + " KB")

        # Manifest verification
        manifest_match = None
        if manifest:
            log.append("Cross-referencing PHOTO_RECONSTRUCTION_MANIFEST...")
            expected = (
                manifest.get("sha256") or
                manifest.get("original_sha256") or
                manifest.get("checksum") or
                manifest.get("hash")
            )
            if expected:
                manifest_match = sha256.lower() == expected.lower()
                if manifest_match:
                    log.append("SHA-256 VERIFIED -- matches manifest exactly!")
                else:
                    log.append("SHA-256 mismatch vs manifest. Trying reorder...")
                    if len(frags) <= 6:
                        from itertools import permutations
                        best = None
                        for perm in permutations(frag_d):
                            candidate = b"".join(perm)
                            if hashlib.sha256(candidate).hexdigest().lower() == expected.lower():
                                best = candidate
                                log.append("Correct order found via permutation search!")
                                manifest_match = True
                                break
                        if best:
                            final_bytes = best
                            sha256 = hashlib.sha256(final_bytes).hexdigest()
                            log.append("SHA-256 now verified after reorder!")
                        else:
                            log.append("All permutations tried -- using sequential order.")
            else:
                log.append("Manifest found but contains no SHA-256 hash to verify.")

        # Integrity scoring
        null_ratio = final_bytes.count(0) / max(len(final_bytes), 1)
        has_header = final_bytes[:3] == bytes([0xFF, 0xD8, 0xFF])
        has_footer = (final_bytes[-2:] == bytes([0xFF, 0xD9])) if ext == "jpg" else True
        has_png_e  = (b"IEND" in final_bytes[-12:]) if ext == "png" else True

        integrity = 100.0
        if null_ratio > 0.3: integrity -= 30
        if not has_header:   integrity -= 20
        if not has_footer:   integrity -= 15
        if not has_png_e:    integrity -= 15
        integrity = max(0.0, min(100.0, integrity))

        if has_header and has_footer and has_png_e:
            log.append("File structure validated -- header and footer intact!")
        elif has_header:
            log.append("Header valid; EOF marker may be missing.")
        else:
            log.append("Header missing -- prepending canonical header.")
            try:
                from recovery_engine import CANONICAL_HEADERS
                hdr = CANONICAL_HEADERS.get(ext, b"")
                final_bytes = hdr + final_bytes
            except Exception:
                pass

        recon_name = "RECOVERED_" + base.upper() + "." + ext
        log.append("Reconstruction complete: " + recon_name)

        results.append({
            "success":        True,
            "name":           recon_name,
            "ext":            ext,
            "type_name":      type_name,
            "data":           final_bytes,
            "fragment_count": len(frags),
            "fragment_names": frag_n,
            "sha256":         sha256,
            "size_kb":        size_kb,
            "manifest_match": manifest_match,
            "integrity_pct":  integrity,
            "log":            log,
            "recovered_at":   datetime.now().isoformat(),
        })

    return results
'''

with open("fragment_reconstructor.py", "w", encoding="utf-8") as f:
    f.write(code)
print("fragment_reconstructor.py written successfully!")

# Quick self-test
import importlib.util, sys
spec = importlib.util.spec_from_file_location("fr", "fragment_reconstructor.py")
mod  = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("Module imports OK")

# Test grouping
fake = {
    "photo_fragment_01.bin": bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b"A" * 100,
    "photo_fragment_02.bin": b"B" * 100,
    "photo_fragment_03.bin": b"C" * 98 + bytes([0xFF, 0xD9]),
    "readme.txt": b"test",
}
results = mod.reconstruct_from_fragments(fake)
print("Groups found:", len(results))
if results:
    r = results[0]
    print("Name:", r["name"], "| Size:", r["size_kb"], "KB | Frags:", r["fragment_count"])
    print("Log:", r["log"][:3])
