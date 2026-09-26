import os, io, json, uuid, struct, random, hashlib, shutil
from flask import Flask, request, jsonify, send_from_directory, send_file, Response
from flask_cors import CORS
from analyzer import find_fragments, build_report, detect_signature, calculate_integrity
from recovery_engine import reconstruct_fragment, get_mime, RECONSTRUCTION_STEPS
from fragment_reconstructor import reconstruct_from_fragments
import ai_engine
import deleted_recovery

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

UPLOAD_FOLDER = "uploads"
REPORT_FOLDER = "reports"
RAW_FOLDER    = "raw_data"   # stores raw upload bytes per scan_id for recovery
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORT_FOLDER, exist_ok=True)
os.makedirs(RAW_FOLDER,    exist_ok=True)

# ─── SERVE FRONTEND ──────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

# ─── SCAN ENDPOINT ───────────────────────────────────────────────────────────
@app.route("/api/scan", methods=["POST"])
def scan():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f        = request.files["file"]
    filename = f.filename or "unknown"

    # ── Multi-file folder upload detection ──────────────────────────────────
    # The frontend concatenates all files and sends them as one blob, but also
    # sends the individual filenames as a JSON list in X-File-Names header.
    file_names_header = request.headers.get("X-File-Names", "")
    individual_files  = request.files.getlist("files")  # multi-file upload

    # Build a per-filename byte map for fragment reconstruction
    file_map = {}

    if individual_files:
        # Multi-file upload mode: reconstruct from actual individual files
        for f_item in individual_files:
            fname = os.path.basename(f_item.filename or "unknown")
            fdata = f_item.read(10 * 1024 * 1024)  # 10 MB cap per file
            if fdata:
                file_map[fname] = fdata
        data = b"".join(file_map.values())
    else:
        # Legacy single-blob mode
        data = f.read(50 * 1024 * 1024)
        # Try to split by file-names header for fragment detection
        if file_names_header:
            try:
                names = json.loads(file_names_header)
                # We can't split the blob by name, but we can try fragment detection
                # on the combined data — the reconstructor will catch named fragments
                # if names are passed separately via X-File-Names
                for name in names:
                    file_map[name] = b""  # placeholder; actual bytes are combined
            except Exception:
                pass

    if not data:
        return jsonify({"error": "Empty file"}), 400

    # ── Fragment reconstruction check ────────────────────────────────────────
    reconstructions = []
    if file_map and len(file_map) >= 2:
        reconstructions = reconstruct_from_fragments(file_map)
        # Store reconstructed files for later download
        for i, rec in enumerate(reconstructions):
            rec_key = rec["sha256"][:8].upper()
            rec_path = os.path.join(RAW_FOLDER, "RECON_" + rec_key + "." + rec["ext"])
            with open(rec_path, "wb") as fp:
                fp.write(rec["data"])
            rec["download_key"] = rec_key  # so frontend can request it
            del rec["data"]  # don't serialise raw bytes into JSON

    fragments = find_fragments(data)

    # If no fragments found (e.g. pure text), treat whole file as one fragment
    if not fragments:
        name, ftype, ext = detect_signature(data)
        integrity = calculate_integrity(data, ftype)
        fragments = [{
            "id": 0,
            "name": "FRAG_0000." + ext,
            "type_name": name,
            "category": ftype,
            "offset": 0,
            "size": len(data),
            "size_kb": round(len(data) / 1024, 2),
            "integrity": integrity,
            "priority": 50,
            "ext": ext,
            "sha256": "n/a",
            "recovered_at": __import__("datetime").datetime.now().isoformat(),
        }]

    # Attach ext field to all fragments (needed for recovery)
    for frag in fragments:
        if "ext" not in frag:
            frag["ext"] = frag["name"].rsplit(".", 1)[-1] if "." in frag["name"] else "bin"

    report = build_report(filename, len(data), fragments)
    scan_id = str(uuid.uuid4())[:8].upper()
    report["scan_id"]         = scan_id
    report["reconstructions"] = reconstructions  # attach reconstruction results

    # Save report
    report_path = os.path.join(REPORT_FOLDER, scan_id + ".json")
    with open(report_path, "w") as fp:
        json.dump(report, fp, indent=2)

    # Save raw bytes for later fragment recovery
    raw_path = os.path.join(RAW_FOLDER, scan_id + ".bin")
    with open(raw_path, "wb") as fp:
        fp.write(data)

    return jsonify({"scan_id": scan_id, "report": report})


# ─── MULTI-FILE UPLOAD (folder scan with individual files) ───────────────────
@app.route("/api/scan-folder", methods=["POST"])
def scan_folder():
    """Accept multiple named files and run fragment reconstruction + forensic scan."""
    uploaded = request.files.getlist("files")
    if not uploaded:
        return jsonify({"error": "No files uploaded"}), 400

    file_map = {}
    combined_data = bytearray()
    total_read = 0
    MAX_TOTAL = 100 * 1024 * 1024  # 100 MB total

    for f_item in uploaded:
        fname = os.path.basename(f_item.filename or "unknown")
        fdata = f_item.read(10 * 1024 * 1024)  # 10 MB cap per file
        if fdata and total_read + len(fdata) <= MAX_TOTAL:
            file_map[fname] = fdata
            combined_data.extend(fdata)
            total_read += len(fdata)

    data = bytes(combined_data)
    filename = str(len(file_map)) + " files from folder"

    # Run fragment reconstruction first
    reconstructions = reconstruct_from_fragments(file_map)
    for rec in reconstructions:
        rec_key  = rec["sha256"][:8].upper()
        rec_path = os.path.join(RAW_FOLDER, "RECON_" + rec_key + "." + rec["ext"])
        with open(rec_path, "wb") as fp:
            fp.write(rec["data"])
        rec["download_key"] = rec_key
        del rec["data"]

    # Also run normal forensic scan on the combined binary
    fragments = find_fragments(data)
    if not fragments:
        name, ftype, ext = detect_signature(data)
        integrity = calculate_integrity(data, ftype)
        fragments = [{
            "id": 0, "name": "FRAG_0000." + ext, "type_name": name,
            "category": ftype, "offset": 0, "size": len(data),
            "size_kb": round(len(data)/1024, 2), "integrity": integrity,
            "priority": 50, "ext": ext, "sha256": "n/a",
            "recovered_at": __import__("datetime").datetime.now().isoformat(),
        }]
    for frag in fragments:
        if "ext" not in frag:
            frag["ext"] = frag["name"].rsplit(".",1)[-1] if "." in frag["name"] else "bin"

    report             = build_report(filename, len(data), fragments)
    scan_id            = str(uuid.uuid4())[:8].upper()
    report["scan_id"]         = scan_id
    report["reconstructions"] = reconstructions

    report_path = os.path.join(REPORT_FOLDER, scan_id + ".json")
    with open(report_path, "w") as fp:
        json.dump(report, fp, indent=2)
    raw_path = os.path.join(RAW_FOLDER, scan_id + ".bin")
    with open(raw_path, "wb") as fp:
        fp.write(data)

    return jsonify({"scan_id": scan_id, "report": report})

# ─── GET SAVED REPORT ────────────────────────────────────────────────────────
@app.route("/api/report/<scan_id>")
def get_report(scan_id):
    report_path = os.path.join(REPORT_FOLDER, f"{scan_id}.json")
    if not os.path.exists(report_path):
        return jsonify({"error": "Report not found"}), 404
    with open(report_path) as fp:
        return jsonify(json.load(fp))

# ─── AI RECOVERY ENDPOINT ────────────────────────────────────────────────────
@app.route("/api/recover/<scan_id>/<int:frag_id>")
def recover_fragment(scan_id, frag_id):
    """
    Extract and AI-reconstruct a specific fragment from the scan.
    Returns the repaired file as a download.
    """
    from recovery_engine import DEMO_GENERATORS, find_natural_end

    report_path = os.path.join(REPORT_FOLDER, f"{scan_id}.json")
    raw_path    = os.path.join(RAW_FOLDER,    f"{scan_id}.bin")

    if not os.path.exists(report_path):
        return jsonify({"error": "Scan not found. Please re-upload your file."}), 404

    with open(report_path) as fp:
        report = json.load(fp)

    # ── PRIORITY: if this scan has fragment reconstructions, serve those ──────
    # When a folder of .bin fragments was uploaded, the full assembled image is
    # saved as RECON_<key>.jpg. Always prefer serving that over a raw 8KB chunk.
    reconstructions = report.get("reconstructions", [])
    if reconstructions:
        rec = reconstructions[0]  # serve the first (and usually only) reconstruction
        dk  = rec.get("download_key")
        if dk:
            for fname in os.listdir(RAW_FOLDER):
                if fname.startswith("RECON_" + dk + "."):
                    recon_ext  = fname.rsplit(".", 1)[-1]
                    recon_path = os.path.join(RAW_FOLDER, fname)
                    with open(recon_path, "rb") as fp2:
                        recon_data = fp2.read()
                    recon_name = rec.get("name", "RECOVERED_PHOTO." + recon_ext)
                    return send_file(
                        io.BytesIO(recon_data),
                        mimetype=get_mime(recon_ext),
                        as_attachment=True,
                        download_name=recon_name,
                    )

    frag = next((f for f in report["fragments"] if f["id"] == frag_id), None)
    if frag is None:
        return jsonify({"error": f"Fragment {frag_id} not found"}), 404

    ext      = frag.get("ext", "bin")
    category = frag.get("category", "unknown")
    offset   = frag.get("offset", 0)
    size     = frag.get("size", 8192)

    # ── DEMO mode: generate real valid synthetic files ────────────────────────
    if scan_id == "DEMO0001" or not os.path.exists(raw_path):
        gen = DEMO_GENERATORS.get(ext)
        if gen:
            try:
                recovered_bytes = gen()
            except Exception:
                recovered_bytes = f"[RecoverAI] Demo fragment for {frag['name']}\nType: {frag['type_name']}\nIntegrity: {frag['integrity']['score']}%\n".encode()
        else:
            recovered_bytes = f"[RecoverAI] Recovered fragment: {frag['name']}\nCategory: {category}\nIntegrity: {frag['integrity']['score']}%\n".encode()
            ext = "txt"

        mime     = get_mime(ext)
        filename = frag["name"].replace("FRAG_", f"RECOVERED_{scan_id}_")
        return send_file(
            io.BytesIO(recovered_bytes),
            mimetype=mime,
            as_attachment=True,
            download_name=filename,
        )

    # ── REAL scan: extract complete chunk using natural-end finder ────────────
    with open(raw_path, "rb") as fp:
        fp.seek(0, 2)
        file_size = fp.tell()
        fp.seek(offset)
        raw_read = fp.read(min(512 * 1024, file_size - offset))

    raw_chunk = find_natural_end(raw_read, 0, ext, max_read=512 * 1024)
    recovered_bytes, steps_log = reconstruct_fragment(raw_chunk, ext, category)

    mime     = get_mime(ext)
    filename = frag["name"].replace("FRAG_", f"RECOVERED_{scan_id}_")

    return send_file(
        io.BytesIO(recovered_bytes),
        mimetype=mime,
        as_attachment=True,
        download_name=filename,
    )


# ─── RECOVERY LOG ENDPOINT (returns AI steps as JSON for frontend display) ───
@app.route("/api/recover-log/<scan_id>/<int:frag_id>")
def recover_log(scan_id, frag_id):
    """Return AI reconstruction log steps for a fragment (for frontend animation)."""
    report_path = os.path.join(REPORT_FOLDER, f"{scan_id}.json")
    if not os.path.exists(report_path):
        return jsonify({"error": "Scan not found"}), 404

    with open(report_path) as fp:
        report = json.load(fp)

    frag = next((f for f in report["fragments"] if f["id"] == frag_id), None)
    if frag is None:
        return jsonify({"error": "Fragment not found"}), 404

    category = frag.get("category", "unknown")
    ext      = frag.get("ext", "bin")
    steps    = RECONSTRUCTION_STEPS.get(category, RECONSTRUCTION_STEPS["unknown"])

    return jsonify({
        "frag_name": frag["name"],
        "frag_type": frag["type_name"],
        "integrity": frag["integrity"],
        "ext":       ext,
        "category":  category,
        "steps":     steps,
        "recoverable": frag["integrity"]["status"] != "CRITICAL",
    })

# ─── DEMO DATA ───────────────────────────────────────────────────────────────
@app.route("/api/demo")
def demo():
    """Return a pre-built demo scan result without needing a real upload."""
    demo_fragments = [
        {
            "id": 0, "name": "FRAG_0000.jpg", "type_name": "JPEG Image",
            "category": "image", "offset": 0, "size": 45312, "size_kb": 44.25,
            "integrity": {"score": 88.4, "status": "RECOVERABLE", "color": "green", "entropy": 7.61, "null_ratio": 1.2},
            "priority": 84, "sha256": "a3f9e12b4c7d8e90", "recovered_at": "2026-09-25T10:00:00", "ext": "jpg"
        },
        {
            "id": 1, "name": "FRAG_0001.pdf", "type_name": "PDF Document",
            "category": "document", "offset": 45312, "size": 102400, "size_kb": 100.0,
            "integrity": {"score": 92.1, "status": "RECOVERABLE", "color": "green", "entropy": 5.23, "null_ratio": 0.5},
            "priority": 87, "sha256": "b7c2d34f1a8e09f4", "recovered_at": "2026-09-25T10:00:01", "ext": "pdf"
        },
        {
            "id": 2, "name": "FRAG_0002.db", "type_name": "SQLite Database",
            "category": "database", "offset": 147712, "size": 81920, "size_kb": 80.0,
            "integrity": {"score": 61.3, "status": "PARTIAL", "color": "yellow", "entropy": 4.87, "null_ratio": 12.1},
            "priority": 56, "sha256": "d9f0e23a7b4c1d82", "recovered_at": "2026-09-25T10:00:02", "ext": "db"
        },
        {
            "id": 3, "name": "FRAG_0003.json", "type_name": "JSON Data",
            "category": "data", "offset": 229632, "size": 4096, "size_kb": 4.0,
            "integrity": {"score": 79.8, "status": "RECOVERABLE", "color": "green", "entropy": 3.91, "null_ratio": 0.0},
            "priority": 67, "sha256": "e1c4a56f2b9d0e73", "recovered_at": "2026-09-25T10:00:03", "ext": "json"
        },
        {
            "id": 4, "name": "FRAG_0004.zip", "type_name": "ZIP Archive",
            "category": "archive", "offset": 233728, "size": 20480, "size_kb": 20.0,
            "integrity": {"score": 32.5, "status": "CRITICAL", "color": "red", "entropy": 7.98, "null_ratio": 31.4},
            "priority": 24, "sha256": "f2b7c89d3e0a1f45", "recovered_at": "2026-09-25T10:00:04", "ext": "zip"
        },
        {
            "id": 5, "name": "FRAG_0005.mp3", "type_name": "MP3 Audio",
            "category": "media", "offset": 254208, "size": 32768, "size_kb": 32.0,
            "integrity": {"score": 55.0, "status": "PARTIAL", "color": "yellow", "entropy": 7.44, "null_ratio": 5.7},
            "priority": 38, "sha256": "c3a0d17e5f2b8c91", "recovered_at": "2026-09-25T10:00:05", "ext": "mp3"
        },
    ]

    report = {
        "scan_id": "DEMO0001",
        "meta": {
            "filename": "disk_image_corrupted.img",
            "filesize_bytes": 524288,
            "filesize_kb": 512.0,
            "scan_time": "2026-09-25T10:00:00",
            "tool": "RecoverAI v1.0 — CalmStacks Hackathon 2026",
        },
        "summary": {
            "total_fragments": 6,
            "recoverable": 3,
            "partial": 2,
            "critical": 1,
            "recovery_rate_pct": 50.0,
            "categories_found": {"image": 1, "document": 1, "database": 1, "data": 1, "archive": 1, "media": 1},
            "top_priority_fragment": "FRAG_0001.pdf",
        },
        "fragments": demo_fragments,
        "relationships": [
            {"from": 1, "to": 2, "reason": "Same file category (document/database)", "confidence": 82},
            {"from": 0, "to": 3, "reason": "Matching metadata timestamps", "confidence": 74},
        ],
    }
    return jsonify({"scan_id": "DEMO0001", "report": report})

# ─── DOWNLOAD RECONSTRUCTED FILE ─────────────────────────────────────────────
@app.route("/api/download-reconstruction/<rec_key>")
def download_reconstruction(rec_key):
    """Serve a previously reconstructed file by its download_key."""
    # Find the file in RAW_FOLDER matching the key
    for fname in os.listdir(RAW_FOLDER):
        if fname.startswith("RECON_" + rec_key + "."):
            ext      = fname.rsplit(".", 1)[-1]
            filepath = os.path.join(RAW_FOLDER, fname)
            with open(filepath, "rb") as fp:
                data = fp.read()
            mime = get_mime(ext)
            download_name = "RECOVERED_" + rec_key + "." + ext
            return send_file(
                io.BytesIO(data),
                mimetype=mime,
                as_attachment=True,
                download_name=download_name,
            )
    return jsonify({"error": "Reconstructed file not found"}), 404


# ─── HEALTH CHECK ────────────────────────────────────────────────────────────
@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "tool": "RecoverAI v1.0",
        "ai_enabled": ai_engine.is_configured()
    })


# ═══════════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════════
# ─── DELETED FILE RECOVERY ENDPOINTS ─────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/deleted/drives")
def deleted_drives():
    """Return available drives with usage stats."""
    return jsonify(deleted_recovery.get_drive_info())


@app.route("/api/deleted/recycle-bin")
def deleted_recycle_bin():
    """Scan the Recycle Bin and return found items."""
    try:
        items = deleted_recovery.scan_recycle_bin()
        return jsonify({"count": len(items), "items": items})
    except Exception as e:
        return jsonify({"error": str(e), "items": []})


@app.route("/api/deleted/restore", methods=["POST"])
def deleted_restore():
    """Restore a Recycle Bin item to its original location (or Desktop)."""
    data  = request.get_json() or {}
    r_path= data.get("r_path", "")
    dest  = data.get("destination", "")
    if not r_path:
        return jsonify({"success": False, "error": "No r_path provided"}), 400
    result = deleted_recovery.restore_from_recycle_bin(r_path, dest)
    return jsonify(result)


@app.route("/api/deleted/send-email", methods=["POST"])
def deleted_send_email():
    """Email a restored file as an attachment to the given address."""
    import smtplib, pathlib
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders

    data       = request.get_json() or {}
    to_email   = data.get("email", "").strip()
    file_path  = data.get("file_path", "").strip()
    filename   = data.get("filename", pathlib.Path(file_path).name if file_path else "recovered_file")

    if not to_email:
        return jsonify({"success": False, "error": "No email address provided"})
    if not file_path or not os.path.exists(file_path):
        return jsonify({"success": False, "error": f"File not found: {file_path}"})

    smtp_email = os.environ.get("SMTP_EMAIL", "")
    smtp_pass  = os.environ.get("SMTP_PASSWORD", "")

    if not smtp_email or not smtp_pass:
        return jsonify({
            "success": False,
            "error": "Email not configured. Add SMTP_EMAIL and SMTP_PASSWORD to your .env file."
        })

    try:
        msg = MIMEMultipart()
        msg["From"]    = smtp_email
        msg["To"]      = to_email
        msg["Subject"] = f"RecoverAI — Restored File: {filename}"

        body = (
            f"Your file has been successfully recovered by RecoverAI.\n\n"
            f"File: {filename}\n"
            f"Restored to: {file_path}\n\n"
            f"The file is attached to this email.\n\n"
            f"— RecoverAI Forensic Recovery System"
        )
        msg.attach(MIMEText(body, "plain"))

        # Attach the recovered file
        with open(file_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)

        # Send via Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(smtp_email, smtp_pass)
            server.sendmail(smtp_email, to_email, msg.as_string())

        return jsonify({"success": True, "sent_to": to_email})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/email-report", methods=["POST"])
def email_report():
    """Receive a base64-encoded PDF from the browser and email it as an attachment."""
    import smtplib, base64
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email.mime.text import MIMEText
    from email import encoders

    data       = request.get_json() or {}
    to_email   = data.get("email", "").strip()
    pdf_b64    = data.get("pdf_base64", "")
    filename   = data.get("filename", "RecoverAI_Forensic_Report.pdf")
    scan_id    = data.get("scan_id", "UNKNOWN")

    if not to_email:
        return jsonify({"success": False, "error": "No email address provided"})
    if not pdf_b64:
        return jsonify({"success": False, "error": "No PDF data received"})

    smtp_email = os.environ.get("SMTP_EMAIL", "")
    smtp_pass  = os.environ.get("SMTP_PASSWORD", "")

    if not smtp_email or not smtp_pass:
        return jsonify({
            "success": False,
            "error": "Email not configured. Add SMTP_EMAIL and SMTP_PASSWORD to your .env file."
        })

    try:
        pdf_bytes = base64.b64decode(pdf_b64)

        msg = MIMEMultipart()
        msg["From"]    = smtp_email
        msg["To"]      = to_email
        msg["Subject"] = f"RecoverAI — Forensic Report [{scan_id}]"

        body = (
            f"Please find attached the full forensic recovery report generated by RecoverAI.\n\n"
            f"Scan ID     : {scan_id}\n"
            f"Report File : {filename}\n\n"
            f"This report includes:\n"
            f"  • Fragment Recovery Map (all detected data segments)\n"
            f"  • Integrity scores & SHA-256 hashes\n"
            f"  • Data category breakdown\n"
            f"  • Fragment relationship graph\n"
            f"  • AI-powered recovery analysis\n\n"
            f"— RecoverAI Forensic Recovery System"
        )
        msg.attach(MIMEText(body, "plain"))

        # Attach the PDF
        part = MIMEBase("application", "pdf")
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(smtp_email, smtp_pass)
            server.sendmail(smtp_email, to_email, msg.as_string())

        return jsonify({"success": True, "sent_to": to_email})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/deleted/start-carve", methods=["POST"])
def deleted_start_carve():
    """Start a background drive-carve job."""
    data  = request.get_json() or {}
    drive = data.get("drive", "C")
    try:
        job_id = deleted_recovery.start_drive_carve(drive_letter=drive)
        return jsonify({"job_id": job_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/deleted/carve-status/<job_id>")
def deleted_carve_status(job_id):
    """Poll status of a drive-carve job."""
    job = deleted_recovery.get_job_status(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    # Store last job id for use by save-all endpoint
    if job.get("status") == "done":
        app.config["last_carve_job"] = job_id
    return jsonify(job)


@app.route("/api/deleted/artifacts")
def deleted_artifacts():
    """Scan Windows temp/cache directories for recoverable artifacts."""
    try:
        items = deleted_recovery.scan_temp_artifacts()
        return jsonify({"count": len(items), "items": items})
    except Exception as e:
        return jsonify({"error": str(e), "items": []})


@app.route("/api/deleted/download", methods=["POST"])
def deleted_download():
    """Copy a found artifact to the user Desktop and return the path."""
    import shutil, pathlib
    data  = request.get_json() or {}
    src   = data.get("path", "")
    name  = data.get("name", "recovered_file")
    if not src or not os.path.exists(src):
        return jsonify({"success": False, "error": "Source file not found"})
    try:
        desktop = pathlib.Path.home() / "Desktop"
        desktop.mkdir(exist_ok=True)
        dest = desktop / name
        # Avoid overwrite collisions
        if dest.exists():
            stem = dest.stem; suffix = dest.suffix; i = 1
            while dest.exists():
                dest = desktop / f"{stem}_{i}{suffix}"; i += 1
        shutil.copy2(src, dest)
        return jsonify({"success": True, "saved_to": str(dest)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/deleted/extract-sector", methods=["POST"])
def deleted_extract_sector():
    """Extract a raw sector fragment from a drive and save to Desktop."""
    import pathlib, struct
    data     = request.get_json() or {}
    drive    = data.get("drive", "C")
    offset   = int(data.get("offset", 0))
    size_kb  = int(data.get("size_kb", 8))
    filename = data.get("filename", "fragment.bin")

    try:
        drive_path = f"\\\\.\\{drive}:"
        size_bytes = size_kb * 1024
        with open(drive_path, "rb") as drv:
            drv.seek(offset)
            raw = drv.read(size_bytes)

        desktop = pathlib.Path.home() / "Desktop" / "RecoverAI_Extracted"
        desktop.mkdir(parents=True, exist_ok=True)
        dest = desktop / filename
        stem = dest.stem; suffix = dest.suffix; i = 1
        while dest.exists():
            dest = desktop / f"{stem}_{i}{suffix}"; i += 1
        with open(dest, "wb") as f:
            f.write(raw)
        return jsonify({"success": True, "saved_to": str(dest), "bytes_read": len(raw)})
    except PermissionError:
        return jsonify({"success": False, "error": "Administrator access required for raw disk read."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/api/deleted/save-all-carved", methods=["POST"])
def deleted_save_all_carved():
    """
    Batch-extract ALL fragments from a completed carve job to Desktop/RecoverAI_Extracted/.
    """
    import pathlib
    data   = request.get_json() or {}
    job_id = data.get("job_id", "")
    job    = deleted_recovery.get_job_status(job_id)
    if not job:
        return jsonify({"success": False, "error": "Job not found"})
    results = job.get("results", [])
    if not results:
        return jsonify({"success": False, "error": "No carved fragments in this job"})

    desktop = pathlib.Path.home() / "Desktop" / "RecoverAI_Extracted"
    desktop.mkdir(parents=True, exist_ok=True)

    saved = 0
    errors = []
    for item in results:
        try:
            drive   = item.get("drive", "C")
            offset  = int(item.get("offset", 0))
            size_kb = int(item.get("size_kb", 8))
            fname   = item.get("filename", f"fragment_{saved}.bin")
            drive_path = f"\\\\.\\{drive}:"
            with open(drive_path, "rb") as drv:
                drv.seek(offset)
                raw = drv.read(size_kb * 1024)
            dest = desktop / fname
            st = dest.stem; sx = dest.suffix; i = 1
            while dest.exists():
                dest = desktop / f"{st}_{i}{sx}"; i += 1
            with open(dest, "wb") as f:
                f.write(raw)
            saved += 1
        except Exception as e:
            errors.append(str(e))

    return jsonify({
        "success": True,
        "saved_count": saved,
        "errors": errors,
        "folder": str(desktop)
    })


# ─── AI CONFIG ────────────────────────────────────────────────────────────────
@app.route("/api/ai-config", methods=["POST"])
def ai_config():
    """Accept and store the Gemini API key at runtime."""
    body = request.get_json(silent=True) or {}
    key  = body.get("api_key", "").strip()
    if not key:
        return jsonify({"error": "api_key is required"}), 400

    # Validate the key first
    result = ai_engine.validate_api_key(key)
    if not result["valid"]:
        return jsonify({"error": "Invalid API key: " + (result["error"] or "unknown error")}), 400

    ai_engine.set_api_key(key)
    return jsonify({"status": "ok", "message": "Gemini AI activated", "model": result["model"]})


@app.route("/api/ai-status")
def ai_status():
    """Return whether Gemini AI is configured and ready."""
    return jsonify({
        "configured": ai_engine.is_configured(),
        "model": ai_engine._active_model if ai_engine.is_configured() else None
    })


# ─── AI FORENSIC SUMMARY ──────────────────────────────────────────────────────
@app.route("/api/ai-summary/<scan_id>")
def ai_summary(scan_id):
    """
    Generate a Gemini AI forensic narrative for a completed scan.
    Returns: {summary: str, ai_powered: bool}
    """
    if scan_id == "DEMO0001":
        # Build a mock report for the demo
        report_path = os.path.join(REPORT_FOLDER, "DEMO0001.json")
        if not os.path.exists(report_path):
            # Use embedded demo data
            from app import demo  # circular but safe for demo
            return jsonify({"error": "Run demo scan first"}), 400
    else:
        report_path = os.path.join(REPORT_FOLDER, f"{scan_id}.json")

    if not os.path.exists(report_path):
        return jsonify({"error": "Scan not found"}), 404

    with open(report_path) as fp:
        report = json.load(fp)

    if not ai_engine.is_configured():
        return jsonify({"error": "AI not configured. Add your Gemini API key first.", "ai_powered": False}), 503

    text = ai_engine.ai_forensic_summary(report)
    if text:
        return jsonify({"summary": text, "ai_powered": True, "model": "gemini-1.5-flash"})
    else:
        return jsonify({"error": "AI generation failed", "ai_powered": False}), 500


# ─── AI FRAGMENT CLASSIFICATION ───────────────────────────────────────────────
@app.route("/api/ai-classify", methods=["POST"])
def ai_classify():
    """
    POST {scan_id, frag_id} → Ask Gemini to re-classify an ambiguous fragment.
    Returns: {file_type, category, extension, confidence, reasoning}
    """
    body    = request.get_json(silent=True) or {}
    scan_id = body.get("scan_id", "")
    frag_id = body.get("frag_id", 0)

    if not ai_engine.is_configured():
        return jsonify({"error": "AI not configured"}), 503

    report_path = os.path.join(REPORT_FOLDER, f"{scan_id}.json")
    raw_path    = os.path.join(RAW_FOLDER,    f"{scan_id}.bin")

    if not os.path.exists(report_path):
        return jsonify({"error": "Scan not found"}), 404

    with open(report_path) as fp:
        report = json.load(fp)

    frag = next((f for f in report["fragments"] if f["id"] == frag_id), None)
    if not frag:
        return jsonify({"error": "Fragment not found"}), 404

    # Get hex sample from raw bytes if available
    hex_sample = "N/A"
    if os.path.exists(raw_path):
        with open(raw_path, "rb") as fp:
            fp.seek(frag.get("offset", 0))
            sample = fp.read(64)
            hex_sample = sample.hex(" ", 1).upper()

    result = ai_engine.ai_classify_fragment(
        hex_sample        = hex_sample,
        entropy           = frag["integrity"]["entropy"],
        size_kb           = frag["size_kb"],
        null_ratio        = frag["integrity"]["null_ratio"],
    )

    if result:
        result["ai_powered"] = True
        return jsonify(result)
    else:
        return jsonify({"error": "AI classification failed"}), 500


# ─── AI FRAGMENT RECOMMENDATION ───────────────────────────────────────────────
@app.route("/api/ai-recommend/<scan_id>/<int:frag_id>")
def ai_recommend(scan_id, frag_id):
    """
    Return a Gemini AI recovery recommendation for a specific fragment.
    """
    if not ai_engine.is_configured():
        return jsonify({"error": "AI not configured"}), 503

    report_path = os.path.join(REPORT_FOLDER, f"{scan_id}.json")
    if not os.path.exists(report_path):
        # Try demo
        return jsonify({"error": "Scan not found"}), 404

    with open(report_path) as fp:
        report = json.load(fp)

    frag = next((f for f in report["fragments"] if f["id"] == frag_id), None)
    if not frag:
        return jsonify({"error": "Fragment not found"}), 404

    text = ai_engine.ai_fragment_recommendation(frag)
    if text:
        return jsonify({"recommendation": text, "ai_powered": True})
    else:
        return jsonify({"error": "AI recommendation failed"}), 500


# ─── AI IMAGE ANALYSIS ────────────────────────────────────────────────────────
@app.route("/api/ai-image-analyze/<rec_key>")
def ai_image_analyze(rec_key):
    """
    Use Gemini Vision to describe a reconstructed image.
    """
    if not ai_engine.is_configured():
        return jsonify({"error": "AI not configured"}), 503

    for fname in os.listdir(RAW_FOLDER):
        if fname.startswith("RECON_" + rec_key + "."):
            ext = fname.rsplit(".", 1)[-1].lower()
            if ext not in ("jpg", "jpeg", "png", "gif", "webp"):
                return jsonify({"error": "Not an image file"}), 400

            fpath = os.path.join(RAW_FOLDER, fname)
            with open(fpath, "rb") as fp:
                image_bytes = fp.read()

            desc = ai_engine.ai_analyze_image(image_bytes, fname)
            if desc:
                return jsonify({"description": desc, "ai_powered": True})
            else:
                return jsonify({"error": "Image analysis failed"}), 500

    return jsonify({"error": "Reconstructed file not found"}), 404


# ─── AI DEMO SUMMARY (no file needed) ────────────────────────────────────────
@app.route("/api/ai-demo-summary")
def ai_demo_summary():
    """Generate AI summary for the built-in demo scan."""
    if not ai_engine.is_configured():
        return jsonify({"error": "AI not configured"}), 503

    # Build demo report inline
    demo_report = {
        "meta": {
            "filename": "disk_image_corrupted.img",
            "filesize_kb": 512.0,
            "scan_time": "2026-09-25T10:00:00",
        },
        "summary": {
            "total_fragments": 6,
            "recoverable": 3,
            "partial": 2,
            "critical": 1,
            "recovery_rate_pct": 50.0,
            "categories_found": {"image": 1, "document": 1, "database": 1, "data": 1, "archive": 1, "media": 1},
            "top_priority_fragment": "FRAG_0001.pdf",
        },
        "fragments": [
            {"name": "FRAG_0000.jpg", "type_name": "JPEG Image",     "category": "image",    "integrity": {"score": 88.4, "status": "RECOVERABLE", "entropy": 7.61, "null_ratio": 1.2},  "priority": 84, "size_kb": 44.25},
            {"name": "FRAG_0001.pdf", "type_name": "PDF Document",    "category": "document", "integrity": {"score": 92.1, "status": "RECOVERABLE", "entropy": 5.23, "null_ratio": 0.5},  "priority": 87, "size_kb": 100.0},
            {"name": "FRAG_0002.db",  "type_name": "SQLite Database", "category": "database", "integrity": {"score": 61.3, "status": "PARTIAL",     "entropy": 4.87, "null_ratio": 12.1}, "priority": 56, "size_kb": 80.0},
            {"name": "FRAG_0003.json","type_name": "JSON Data",       "category": "data",     "integrity": {"score": 79.8, "status": "RECOVERABLE", "entropy": 3.91, "null_ratio": 0.0},  "priority": 67, "size_kb": 4.0},
            {"name": "FRAG_0004.zip", "type_name": "ZIP Archive",     "category": "archive",  "integrity": {"score": 32.5, "status": "CRITICAL",     "entropy": 7.98, "null_ratio": 31.4}, "priority": 24, "size_kb": 20.0},
            {"name": "FRAG_0005.mp3", "type_name": "MP3 Audio",       "category": "media",    "integrity": {"score": 55.0, "status": "PARTIAL",     "entropy": 7.44, "null_ratio": 5.7},  "priority": 38, "size_kb": 32.0},
        ]
    }

    text = ai_engine.ai_forensic_summary(demo_report)
    if text:
        return jsonify({"summary": text, "ai_powered": True, "model": "gemini-1.5-flash"})
    else:
        return jsonify({"error": "AI generation failed"}), 500


if __name__ == "__main__":
    print("\n[*] RecoverAI + Gemini AI Backend Running at http://localhost:5000\n")
    # Auto-activate AI if key is present in environment / .env
    key = ai_engine.get_api_key()
    if key:
        print("[*] Gemini API key found — validating and pre-warming model...")
        result = ai_engine.validate_api_key(key)
        if result["valid"]:
            ai_engine.set_api_key(key)
            print(f"[*] Gemini AI: ACTIVE ({result['model']})")
        else:
            print(f"[!] Gemini AI key error: {result['error']}")
    else:
        print("[!] Gemini AI: NOT configured — add API key via UI or set GEMINI_API_KEY in .env")
    print()
    app.run(debug=True, port=5000)
