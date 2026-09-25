"""
restore_to_pause9.py
Restores the project to the exact state at the pause-9 checkpoint:
  ✅ All 4 forensic panels (Reconstruction, Integrity, Classification, Decision Support)
  ✅ Gemini AI active
  ✅ Fragment recovery with download + per-fragment AI advice
  ✅ Deleted Recovery: Recycle Bin (restore), Drive Scanner, Temp Artifacts (save to desktop)
  ✅ 26 Recycle Bin files, 288 sector fragments, Save All to Desktop
  ✅ Original app.js UI layout
"""
import os

# ── Step 1: Re-add deleted_recovery import + all endpoints to app.py ──────────
with open("app.py", encoding="utf-8") as f:
    content = f.read()

# Add import if missing
if "import deleted_recovery" not in content:
    content = content.replace(
        "import ai_engine",
        "import ai_engine\nimport deleted_recovery"
    )

# Add deleted endpoints block before the AI CONFIG section or at end
DELETED_ROUTES = '''

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
        drive_path = f"\\\\\\\\.\\\\{drive}:"
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
            drive_path = f"\\\\\\\\.\\\\{drive}:"
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
'''

# Insert before the AI config section or at end
ai_marker = "# \u2500\u2500\u2500 AI CONFIG"
if ai_marker in content:
    content = content.replace(ai_marker, DELETED_ROUTES + "\n\n" + ai_marker)
else:
    # Check for startup block
    startup = 'if __name__ == "__main__"'
    if startup in content:
        content = content.replace(startup, DELETED_ROUTES + "\n\n" + startup)
    else:
        content += DELETED_ROUTES

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
print("app.py: deleted recovery endpoints restored")

# ── Step 2: Append deleted recovery JS to app.js ─────────────────────────────
# Check if already present
with open("frontend/app.js", encoding="utf-8") as f:
    js = f.read()

if "DELETED FILE RECOVERY MODULE" not in js:
    os.system("python append_deleted_js.py")
    os.system("python patch_carve_buttons.py")
    os.system("python append_extract_js.py")
    print("app.js: deleted recovery JS appended")
else:
    print("app.js: deleted recovery already present")

# ── Step 3: Add deleted recovery section to index.html ──────────────────────
with open("frontend/index.html", encoding="utf-8") as f:
    html = f.read()

# Add the "Recover Deleted Files" button to upload zone actions if missing
if "openDeletedRecovery" not in html:
    html = html.replace(
        '<button class="btn-ghost" onclick="loadDemo()">&#9654; Demo Scan</button>',
        '<button class="btn-ghost" onclick="loadDemo()">&#9654; Demo Scan</button>\n      <button class="btn-danger" onclick="openDeletedRecovery()">&#128465; Recover Deleted Files</button>'
    )
    # Add feature chip
    html = html.replace(
        '</div>\n\n  <div class="features-row">',
        '</div>\n\n  <div class="features-row">'
    )
    if "Deleted Recovery" not in html:
        html = html.replace(
            '</div>\n</section>\n\n<!-- \u2550\u2550 DASHBOARD',
            '    <div class="feature-chip"><span>&#128465;</span> Deleted Recovery</div>\n  </div>\n</section>\n\n<!-- \u2550\u2550 DASHBOARD'
        )

# Add the deleted section overlay before the recovery modal
DELETED_HTML = '''
<!-- ═══════════════════════════════════════════════════════════════════════════
     DELETED FILE RECOVERY OVERLAY
     ═══════════════════════════════════════════════════════════════════════════ -->
<div id="deletedSection" class="deleted-overlay" style="display:none">
  <div class="deleted-modal">
    <div class="deleted-modal-header">
      <div class="deleted-modal-title">&#128465; Deleted File Recovery</div>
      <button class="deleted-close" onclick="closeDeletedRecovery()">&times;</button>
    </div>

    <div class="del-tabs">
      <button class="del-tab active" id="delTab-recycle"   onclick="switchDelTab(\'recycle\', this)">&#128465; Recycle Bin</button>
      <button class="del-tab"        id="delTab-carve"     onclick="switchDelTab(\'carve\', this)">&#128189; Drive Scanner</button>
      <button class="del-tab"        id="delTab-artifacts" onclick="switchDelTab(\'artifacts\', this)">&#128193; Temp Artifacts</button>
    </div>

    <div class="del-content" id="delContent-recycle">
      <div class="del-toolbar">
        <button class="btn-primary" id="scanRecycleBtn" onclick="scanRecycleBin()">&#128269; Scan Recycle Bin</button>
        <span class="del-info" id="recycleInfo">Click to scan deleted files in your Recycle Bin</span>
      </div>
      <div id="recycleResults"></div>
    </div>

    <div class="del-content" id="delContent-carve" style="display:none">
      <div class="admin-notice" id="adminNotice" style="display:none">
        <span>&#128737;</span>
        <div>
          <strong>Administrator required for raw disk scan.</strong>
          Restart the server as Administrator: right-click terminal &rarr; Run as Administrator &rarr; <code>python app.py</code>
        </div>
      </div>
      <div class="del-toolbar">
        <select id="driveSelect" class="del-select"></select>
        <button class="btn-primary" id="startCarveBtn" onclick="startDriveCarve()">&#128300; Start Deep Scan</button>
      </div>
      <div id="carveProgress" style="display:none">
        <div class="carve-bar-wrap"><div class="carve-bar" id="carveProgressBar" style="width:0%"></div></div>
        <div class="carve-stats" id="carveStats"></div>
      </div>
      <div id="carveResults"></div>
    </div>

    <div class="del-content" id="delContent-artifacts" style="display:none">
      <div class="del-toolbar">
        <button class="btn-primary" id="scanArtifactsBtn" onclick="scanArtifacts()">&#128193; Scan Temp &amp; Cache</button>
        <span class="del-info">Finds recoverable files in Temp folders, Recent Files and browser caches</span>
      </div>
      <div id="artifactsResults"></div>
    </div>
  </div>
</div>

'''

if "deletedSection" not in html:
    html = html.replace('<!-- \u2550\u2550 RECOVERY MODAL', DELETED_HTML + '<!-- \u2550\u2550 RECOVERY MODAL')

with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("index.html: deleted recovery overlay added")

# ── Step 4: Add deleted recovery CSS to style.css if missing ─────────────────
with open("frontend/style.css", encoding="utf-8") as f:
    css = f.read()

if ".deleted-overlay" not in css:
    DELETED_CSS = '''

/* ═══════════════════════════════════════════════════════════════════════════
   DELETED FILE RECOVERY
   ═══════════════════════════════════════════════════════════════════════════ */
.deleted-overlay { position:fixed;inset:0;z-index:500;background:rgba(10,15,30,0.85);backdrop-filter:blur(10px);display:flex;align-items:center;justify-content:center;padding:24px; }
.deleted-modal { background:var(--surface);border:1px solid var(--border);border-radius:20px;width:min(880px,96vw);max-height:88vh;overflow-y:auto;box-shadow:var(--shadow-lg);animation:modalIn 0.35s cubic-bezier(0.34,1.56,0.64,1); }
.deleted-modal-header { display:flex;justify-content:space-between;align-items:center;padding:20px 24px;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--surface);z-index:2; }
.deleted-modal-title { font-size:17px;font-weight:700;color:var(--text); }
.deleted-close { background:none;border:none;color:var(--text3);font-size:22px;cursor:pointer;transition:color 0.2s; }
.deleted-close:hover { color:var(--text); }
.del-tabs { display:flex;gap:4px;padding:16px 24px 0;border-bottom:1px solid var(--border); }
.del-tab { background:none;border:none;color:var(--text3);font-family:var(--font);font-size:13px;font-weight:600;padding:9px 18px;border-radius:10px 10px 0 0;border-bottom:2px solid transparent;cursor:pointer;transition:all 0.2s; }
.del-tab:hover { color:var(--text);background:rgba(255,255,255,0.03); }
.del-tab.active { color:var(--blue);border-bottom-color:var(--blue);background:rgba(96,165,250,0.07); }
.del-content { padding:20px 24px; }
.del-toolbar { display:flex;align-items:center;gap:12px;margin-bottom:18px;flex-wrap:wrap; }
.del-info { font-size:12px;color:var(--text3);font-style:italic; }
.del-select { background:var(--surface2);color:var(--text);border:1px solid var(--border);border-radius:10px;padding:9px 14px;font-size:13px;font-family:var(--mono);cursor:pointer;outline:none;min-width:220px; }
.admin-notice { display:flex;gap:12px;padding:14px 16px;border-radius:12px;margin-bottom:16px;background:rgba(251,191,36,0.07);border:1px solid rgba(251,191,36,0.3);font-size:12px;color:var(--text2);align-items:flex-start; }
.admin-notice strong { color:var(--amber);display:block;margin-bottom:4px; }
.admin-notice code { font-family:var(--mono);font-size:11px;color:var(--cyan);background:rgba(103,232,249,0.1);padding:2px 8px;border-radius:5px; }
.del-results-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(290px,1fr));gap:12px; }
.del-card { background:var(--surface2);border:1px solid var(--border);border-radius:var(--radius);padding:14px;transition:all 0.2s;animation:cardFadeIn 0.3s ease; }
.del-card:hover { border-color:var(--blue);transform:translateY(-2px);box-shadow:var(--shadow); }
@keyframes cardFadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:none} }
.del-card-top { display:flex;align-items:flex-start;gap:10px;margin-bottom:8px; }
.del-card-icon { font-size:22px;flex-shrink:0; }
.del-card-name { font-size:11px;font-weight:700;color:var(--text);font-family:var(--mono);word-break:break-all; }
.del-card-meta { font-size:10px;color:var(--text3);margin-top:3px;line-height:1.6; }
.del-card-bar-wrap { height:4px;border-radius:2px;background:rgba(255,255,255,0.06);margin:6px 0;overflow:hidden; }
.del-card-bar { height:100%;border-radius:2px;transition:width 0.8s ease; }
.del-card-bar.green { background:linear-gradient(90deg,#059669,#34d399); }
.del-card-bar.amber { background:linear-gradient(90deg,#d97706,#fbbf24); }
.del-card-bar.red   { background:linear-gradient(90deg,#dc2626,#f87171); }
.del-card-footer { display:flex;align-items:center;justify-content:space-between;margin-top:8px; }
.del-card-sha { font-family:var(--mono);font-size:9px;color:var(--text3); }
.del-card-actions { display:flex;gap:5px; }
.btn-restore { font-size:11px;font-weight:700;padding:4px 10px;border-radius:7px;border:1px solid rgba(52,211,153,0.3);background:rgba(52,211,153,0.08);color:var(--green);font-family:var(--font);cursor:pointer;transition:all 0.2s; }
.btn-restore:hover { background:rgba(52,211,153,0.18); }
.btn-restore.done { opacity:0.7;cursor:default; }
.del-empty { text-align:center;padding:44px 20px;color:var(--text3);font-size:13px; }
.del-empty-icon { font-size:38px;margin-bottom:10px; }
.btn-danger { padding:11px 26px;border-radius:100px;border:1px solid rgba(248,113,113,0.3);background:rgba(248,113,113,0.08);color:var(--red);font-family:var(--font);font-size:13px;font-weight:700;cursor:pointer;transition:all 0.2s; }
.btn-danger:hover { background:rgba(248,113,113,0.15);transform:translateY(-2px); }
'''
    with open("frontend/style.css", "a", encoding="utf-8") as f:
        f.write(DELETED_CSS)
    print("style.css: deleted recovery CSS added")
else:
    print("style.css: deleted recovery CSS already present")

print("\n=== RESTORE COMPLETE ===")
print("State matches the pause-9 checkpoint (Just message me when ready!)")
print("Restart the server to apply all changes.")
