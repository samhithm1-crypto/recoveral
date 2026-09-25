"""
fix_dashboard_ui.py
1. Patches renderDashboard in app.js to show navCenter + nav buttons
2. Adds a "New Scan" button at the top of the dashboard HTML
3. Appends all missing CSS classes to style.css
"""

# ── 1. Patch app.js to show nav buttons after scan ────────────────────────────
with open("frontend/app.js", encoding="utf-8") as f:
    js = f.read()

OLD = '''    heroSection.style.display    = "none";
    uploadSection.style.display  = "none";
    dashboard.style.display      = "block";
    window.scrollTo(0, 0);'''

NEW = '''    heroSection.style.display    = "none";
    uploadSection.style.display  = "none";
    dashboard.style.display      = "block";
    window.scrollTo(0, 0);

    // Show navbar scan info + action buttons
    const _nc = document.getElementById("navCenter");
    const _ep = document.getElementById("exportPdfBtn");
    const _ec = document.getElementById("exportCsvBtn");
    const _ns = document.getElementById("newScanBtn");
    if (_nc) _nc.style.display = "";
    if (_ep) _ep.style.display = "";
    if (_ec) _ec.style.display = "";
    if (_ns) _ns.style.display = "";'''

if OLD in js:
    js = js.replace(OLD, NEW)
    print("app.js: nav buttons patch applied")
else:
    print("WARNING: Could not find renderDashboard target in app.js")

# Also patch resetScan to hide them again
OLD_RESET = '''  dashboard.style.display     = "none";
  heroSection.style.display   = "";
  uploadSection.style.display = "";'''

NEW_RESET = '''  dashboard.style.display     = "none";
  heroSection.style.display   = "";
  uploadSection.style.display = "";

  // Hide navbar scan info + action buttons
  const _nc2 = document.getElementById("navCenter");
  const _ep2 = document.getElementById("exportPdfBtn");
  const _ec2 = document.getElementById("exportCsvBtn");
  const _ns2 = document.getElementById("newScanBtn");
  if (_nc2) _nc2.style.display = "none";
  if (_ep2) _ep2.style.display = "none";
  if (_ec2) _ec2.style.display = "none";
  if (_ns2) _ns2.style.display = "none";'''

if OLD_RESET in js:
    js = js.replace(OLD_RESET, NEW_RESET)
    print("app.js: resetScan hide buttons patch applied")

with open("frontend/app.js", "w", encoding="utf-8") as f:
    f.write(js)

# ── 2. Add "New Scan" button at top of dashboard in index.html ────────────────
with open("frontend/index.html", encoding="utf-8") as f:
    html = f.read()

SCAN_BANNER = '''
<!-- Dashboard top bar -->
<div class="dash-topbar">
  <div class="dash-topbar-left">
    <span class="dash-status-badge">&#9989; FORENSIC SCAN COMPLETE</span>
    <span class="dash-scan-id" id="dashScanId"></span>
    <span class="dash-target"  id="dashTarget"></span>
  </div>
  <div class="dash-topbar-right">
    <button class="btn-ghost" onclick="exportPDF()" id="dashExportPdf">&#128196; Export PDF Report</button>
    <button class="btn-new-scan" onclick="newScan()">&#8634; New Scan</button>
  </div>
</div>

'''

if "dash-topbar" not in html:
    html = html.replace(
        '<div id="dashboard" style="display:none">',
        '<div id="dashboard" style="display:none">\n' + SCAN_BANNER
    )
    print("index.html: scan banner added inside dashboard")
else:
    print("index.html: scan banner already present")

# Also sync dashScanId and dashTarget from the scan data
# We do this by patching app.js to also fill those
with open("frontend/app.js", encoding="utf-8") as f:
    js2 = f.read()

SYNC = '''    document.getElementById("scanId").textContent   = `SCAN-ID: ${report.scan_id}`;
    document.getElementById("scanFile").textContent =
      `TARGET: ${meta.filename}  (${meta.filesize_kb} KB)  ·  ${new Date(meta.scan_time).toLocaleString()}`;'''

SYNC_NEW = '''    document.getElementById("scanId").textContent   = `SCAN-ID: ${report.scan_id}`;
    document.getElementById("scanFile").textContent =
      `TARGET: ${meta.filename}  (${meta.filesize_kb} KB)  ·  ${new Date(meta.scan_time).toLocaleString()}`;

    // Also fill the in-dashboard top bar
    const _dsi = document.getElementById("dashScanId");
    const _dta = document.getElementById("dashTarget");
    if (_dsi) _dsi.textContent = `SCAN-ID: ${report.scan_id}`;
    if (_dta) _dta.textContent = `TARGET: ${meta.filename}  (${meta.filesize_kb} KB)  ·  ${new Date(meta.scan_time).toLocaleString()}`;'''

if SYNC in js2:
    js2 = js2.replace(SYNC, SYNC_NEW)
    print("app.js: dashScanId/dashTarget sync added")

with open("frontend/app.js", "w", encoding="utf-8") as f:
    f.write(js2)

with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(html)

# ── 3. Append all missing CSS classes to style.css ────────────────────────────
with open("frontend/style.css", encoding="utf-8") as f:
    css = f.read()

MISSING_CSS = """

/* ═══════════════════════════════════════════════════════════════════════════
   DASHBOARD TOP BAR + NEW SCAN BUTTON
   ═══════════════════════════════════════════════════════════════════════════ */
.dash-topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 40px; border-bottom: 1px solid var(--border);
  background: rgba(20, 30, 53, 0.9); flex-wrap: wrap; gap: 12px;
}
.dash-topbar-left  { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.dash-topbar-right { display: flex; align-items: center; gap: 10px; }

.dash-status-badge {
  font-size: 11px; font-weight: 800; letter-spacing: 1.2px;
  color: var(--green); background: rgba(52,211,153,0.1);
  border: 1px solid rgba(52,211,153,0.3); padding: 4px 12px; border-radius: 100px;
}
.dash-scan-id {
  font-family: var(--mono); font-size: 11px; font-weight: 700;
  color: var(--blue); background: rgba(96,165,250,0.1);
  border: 1px solid rgba(96,165,250,0.25); padding: 3px 10px; border-radius: 100px;
}
.dash-target { font-family: var(--mono); font-size: 10px; color: var(--text3); }

.btn-new-scan {
  padding: 9px 22px; border-radius: 100px; border: 1px solid rgba(248,113,113,0.35);
  background: rgba(248,113,113,0.1); color: var(--red);
  font-family: var(--font); font-size: 13px; font-weight: 700;
  cursor: pointer; transition: all 0.2s;
}
.btn-new-scan:hover { background: rgba(248,113,113,0.2); transform: translateY(-2px); }

/* ═══════════════════════════════════════════════════════════════════════════
   FRAGMENT TABLE — app.js generated classes
   ═══════════════════════════════════════════════════════════════════════════ */
.priority-bar {
  display: flex; align-items: center; gap: 8px; min-width: 80px;
}
.priority-num {
  font-family: var(--mono); font-size: 12px; font-weight: 800;
  color: var(--cyan); width: 26px; text-align: right; flex-shrink: 0;
}
.pbar {
  flex: 1; height: 4px; background: rgba(255,255,255,0.07);
  border-radius: 2px; overflow: hidden; min-width: 40px;
}
.pbar-fill {
  height: 100%; border-radius: 2px;
  background: linear-gradient(90deg, var(--blue-d), var(--cyan));
  transition: width 0.8s ease;
}

.frag-name {
  font-family: var(--mono); font-size: 12px; font-weight: 700; color: var(--text);
}
.frag-type {
  font-size: 10px; color: var(--text3); margin-top: 2px; font-family: var(--mono);
}

/* Category tags in table */
.cat-tag {
  display: inline-block; font-size: 10px; font-weight: 700;
  padding: 3px 10px; border-radius: 100px; font-family: var(--mono);
  letter-spacing: 0.5px; white-space: nowrap;
}
.cat-image    { background: rgba(192,132,252,0.15); color: #c084fc; border: 1px solid rgba(192,132,252,0.3); }
.cat-document { background: rgba(147,197,253,0.15); color: #93c5fd; border: 1px solid rgba(147,197,253,0.3); }
.cat-database { background: rgba(103,232,249,0.15); color: #67e8f9; border: 1px solid rgba(103,232,249,0.3); }
.cat-media    { background: rgba(252,211,77,0.15);  color: #fcd34d; border: 1px solid rgba(252,211,77,0.3); }
.cat-archive  { background: rgba(252,165,165,0.15); color: #fca5a5; border: 1px solid rgba(252,165,165,0.3); }
.cat-data     { background: rgba(134,239,172,0.15); color: #86efac; border: 1px solid rgba(134,239,172,0.3); }
.cat-web      { background: rgba(253,186,116,0.15); color: #fdba74; border: 1px solid rgba(253,186,116,0.3); }
.cat-binary   { background: rgba(148,163,184,0.1);  color: #94a3b8; border: 1px solid rgba(148,163,184,0.2); }
.cat-unknown  { background: rgba(100,116,139,0.1);  color: #64748b; border: 1px solid rgba(100,116,139,0.2); }

/* Integrity score cell */
.integrity-cell { text-align: center; }
.int-score {
  font-family: var(--mono); font-size: 13px; font-weight: 800;
}
.int-score.green  { color: var(--green); }
.int-score.yellow { color: var(--amber); }
.int-score.red    { color: var(--red); }

/* Status badge */
.status-badge {
  display: inline-block; font-size: 10px; font-weight: 800;
  padding: 3px 10px; border-radius: 100px; font-family: var(--mono);
  letter-spacing: 0.5px; white-space: nowrap;
}
.status-badge.green  { background: rgba(52,211,153,0.12); color: var(--green); border: 1px solid rgba(52,211,153,0.25); }
.status-badge.yellow { background: rgba(251,191,36,0.12);  color: var(--amber); border: 1px solid rgba(251,191,36,0.25); }
.status-badge.red    { background: rgba(248,113,113,0.12); color: var(--red);   border: 1px solid rgba(248,113,113,0.25); }
.status-badge.neutral{ background: rgba(148,163,184,0.1);  color: var(--text3); border: 1px solid rgba(148,163,184,0.2); }

/* SHA text */
.sha-text { font-family: var(--mono); font-size: 10px; color: var(--text3); }

/* Recover fragment button */
.btn-recover-frag {
  padding: 5px 14px; border-radius: 8px; border: 1px solid rgba(96,165,250,0.35);
  background: rgba(96,165,250,0.1); color: var(--blue);
  font-family: var(--font); font-size: 11px; font-weight: 700;
  cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.btn-recover-frag:hover  { background: rgba(96,165,250,0.2); transform: translateY(-1px); }
.btn-recover-frag.critical {
  border-color: rgba(251,191,36,0.35); background: rgba(251,191,36,0.1); color: var(--amber);
}
.btn-recover-frag.critical:hover { background: rgba(251,191,36,0.2); }
.btn-recover-download {
  padding: 5px 14px; border-radius: 8px; border: 1px solid rgba(52,211,153,0.35);
  background: rgba(52,211,153,0.1); color: var(--green);
  font-family: var(--font); font-size: 11px; font-weight: 700;
  cursor: pointer; transition: all 0.2s;
}
.btn-recover-download:hover { background: rgba(52,211,153,0.2); }

/* ═══════════════════════════════════════════════════════════════════════════
   CATEGORIES LIST
   ═══════════════════════════════════════════════════════════════════════════ */
.cat-item { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
.cat-item-name { display: flex; align-items: center; gap: 8px; font-size: 12px; color: var(--text2); }
.cat-dot  { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.cat-count{ font-family: var(--mono); font-size: 12px; font-weight: 700; color: var(--text); }
.cat-bar-wrap { height: 4px; border-radius: 2px; background: rgba(255,255,255,0.05); margin-bottom: 8px; overflow: hidden; }
.cat-bar  { height: 100%; border-radius: 2px; transition: width 0.8s ease; }

/* ═══════════════════════════════════════════════════════════════════════════
   RELATIONSHIPS LIST
   ═══════════════════════════════════════════════════════════════════════════ */
.rel-item   { padding: 10px 0; border-bottom: 1px solid var(--border2); }
.rel-item:last-child { border-bottom: none; }
.rel-frags  { font-family: var(--mono); font-size: 12px; font-weight: 700; color: var(--text); margin-bottom: 3px; }
.rel-reason { font-size: 11px; color: var(--text2); margin-bottom: 3px; }
.rel-conf   { font-size: 11px; color: var(--text3); }
.rel-empty  { font-size: 12px; color: var(--text3); text-align: center; padding: 20px 0; font-style: italic; }

/* ═══════════════════════════════════════════════════════════════════════════
   RECONSTRUCTION PANEL (renderReconstructionPanel)
   ═══════════════════════════════════════════════════════════════════════════ */
.recon-intro  { font-size: 13px; color: var(--text2); margin-bottom: 16px; line-height: 1.6; }
.recon-card   { background: var(--surface2); border: 1px solid rgba(52,211,153,0.2); border-radius: var(--radius); overflow: hidden; margin-bottom: 14px; }
.recon-card-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; border-bottom: 1px solid var(--border); }
.recon-filename { font-family: var(--mono); font-size: 13px; font-weight: 700; color: var(--text); }
.recon-badge { font-size: 10px; font-weight: 800; padding: 3px 10px; border-radius: 100px; font-family: var(--mono); }
.verified { background: rgba(52,211,153,0.1); color: var(--green); border: 1px solid rgba(52,211,153,0.3); }
.warn     { background: rgba(251,191,36,0.1);  color: var(--amber); border: 1px solid rgba(251,191,36,0.3); }
.recon-card-info { display: flex; gap: 20px; padding: 10px 16px 0; flex-wrap: wrap; }
.recon-meta { font-size: 11px; color: var(--text3); font-family: var(--mono); }
.recon-fragments { font-size: 11px; color: var(--text3); }
.recon-img-wrap  { padding: 12px 16px; text-align: center; }
.recon-img { max-width: 100%; max-height: 260px; border-radius: 8px; border: 1px solid var(--border); object-fit: contain; }
.recon-img-label { font-size: 10px; color: var(--text3); margin-top: 6px; font-style: italic; }
.recon-img-loading { font-size: 12px; color: var(--text3); padding: 20px; }
.recon-dl-btn { display: block; margin: 0 16px 16px; }
.recon-log-title { font-size: 11px; font-weight: 700; color: var(--text3); letter-spacing: 1px; text-transform: uppercase; padding: 8px 16px 4px; }
.recon-log-wrap  { padding: 0 16px 12px; }
.recon-empty { text-align: center; padding: 24px; font-size: 13px; color: var(--text3); font-style: italic; }
.rlog-line { font-family: var(--mono); font-size: 11px; color: var(--text3); line-height: 1.8; }
.ai-rec-label { font-size: 10px; color: var(--purple); font-style: italic; margin-top: 4px; }
.panel-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; gap: 10px; flex-wrap: wrap; }
.neutral { color: var(--text3); }
"""

if ".dash-topbar" not in css:
    with open("frontend/style.css", "a", encoding="utf-8") as f:
        f.write(MISSING_CSS)
    print("style.css: all missing CSS classes appended")
else:
    print("style.css: already patched")

print("\n=== DONE ===")
print("Restart the server and hard refresh the browser (Ctrl+Shift+R)")
