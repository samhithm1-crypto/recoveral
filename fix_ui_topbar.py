"""
fix_ui_topbar.py
1. Hides navCenter (scan-id / target) from navbar after scan — dashboard topbar already shows it
2. Keeps navbar clean: logo | AI pill | PDF | CSV | New Scan
3. Fixes Health/Gauge card sizing to match other cards
4. Improves dashboard topbar styling
"""

# ── 1. Patch app.js — don't show navCenter after scan ─────────────────────────
with open("frontend/app.js", encoding="utf-8") as f:
    js = f.read()

# Remove the navCenter show line from renderDashboard
OLD_NAV = """    // Show navbar scan info + action buttons
    const _nc = document.getElementById("navCenter");
    const _ep = document.getElementById("exportPdfBtn");
    const _ec = document.getElementById("exportCsvBtn");
    const _ns = document.getElementById("newScanBtn");
    if (_nc) _nc.style.display = "";
    if (_ep) _ep.style.display = "";
    if (_ec) _ec.style.display = "";
    if (_ns) _ns.style.display = "";"""

NEW_NAV = """    // Show navbar action buttons (NOT navCenter — dashboard topbar handles scan info)
    const _ep = document.getElementById("exportPdfBtn");
    const _ec = document.getElementById("exportCsvBtn");
    const _ns = document.getElementById("newScanBtn");
    if (_ep) _ep.style.display = "";
    if (_ec) _ec.style.display = "";
    if (_ns) _ns.style.display = "";"""

if OLD_NAV in js:
    js = js.replace(OLD_NAV, NEW_NAV)
    print("app.js: navCenter removed from post-scan show")
else:
    print("WARNING: nav patch target not found")

# Also patch resetScan to not hide navCenter (it was never shown)
OLD_RESET = """  // Hide navbar scan info + action buttons
  const _nc2 = document.getElementById("navCenter");
  const _ep2 = document.getElementById("exportPdfBtn");
  const _ec2 = document.getElementById("exportCsvBtn");
  const _ns2 = document.getElementById("newScanBtn");
  if (_nc2) _nc2.style.display = "none";
  if (_ep2) _ep2.style.display = "none";
  if (_ec2) _ec2.style.display = "none";
  if (_ns2) _ns2.style.display = "none";"""

NEW_RESET = """  // Hide navbar action buttons
  const _ep2 = document.getElementById("exportPdfBtn");
  const _ec2 = document.getElementById("exportCsvBtn");
  const _ns2 = document.getElementById("newScanBtn");
  if (_ep2) _ep2.style.display = "none";
  if (_ec2) _ec2.style.display = "none";
  if (_ns2) _ns2.style.display = "none";"""

if OLD_RESET in js:
    js = js.replace(OLD_RESET, NEW_RESET)
    print("app.js: resetScan navCenter hide removed")

with open("frontend/app.js", "w", encoding="utf-8") as f:
    f.write(js)

# ── 2. Patch CSS — fix gauge card + topbar styling ────────────────────────────
with open("frontend/style.css", encoding="utf-8") as f:
    css = f.read()

PATCH_CSS = """

/* ═══════════════════════════════════════════════════════════════════════════
   UI TOPBAR + CARDS FIXES
   ═══════════════════════════════════════════════════════════════════════════ */

/* Gauge card — match height of other cards, proper centering */
.sum-card.sum-gauge {
  padding: 18px 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.gauge-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 4px;
}
.gauge-svg { width: 90px; height: 54px; }
.gauge-pct { font-size: 20px; font-weight: 800; color: var(--text); margin-top: -4px; }

/* Summary cards equal height */
.sum-cards { align-items: stretch; }
.sum-card   { display: flex; flex-direction: column; justify-content: center; }

/* Dashboard topbar — remove redundancy with navbar, clean up */
.dash-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 32px;
  border-bottom: 1px solid var(--border);
  background: rgba(15, 22, 41, 0.95);
  flex-wrap: wrap;
  gap: 10px;
  position: sticky;
  top: 60px;
  z-index: 90;
}
.dash-topbar-left  { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.dash-topbar-right { display: flex; align-items: center; gap: 8px; }
.dash-status-badge {
  font-size: 10px; font-weight: 800; letter-spacing: 1.5px;
  color: var(--green); background: rgba(52,211,153,0.1);
  border: 1px solid rgba(52,211,153,0.3);
  padding: 3px 12px; border-radius: 100px;
}
.dash-scan-id {
  font-family: var(--mono); font-size: 10px; font-weight: 700;
  color: var(--blue); background: rgba(96,165,250,0.1);
  border: 1px solid rgba(96,165,250,0.25);
  padding: 2px 10px; border-radius: 100px;
}
.dash-target {
  font-family: var(--mono); font-size: 10px; color: var(--text3);
  max-width: 420px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.btn-new-scan {
  padding: 7px 18px; border-radius: 100px;
  border: 1px solid rgba(248,113,113,0.35);
  background: rgba(248,113,113,0.1); color: var(--red);
  font-family: var(--font); font-size: 12px; font-weight: 700;
  cursor: pointer; transition: all 0.2s;
}
.btn-new-scan:hover { background: rgba(248,113,113,0.2); }

/* Export button in topbar */
.dash-topbar-right .btn-ghost {
  padding: 7px 16px; font-size: 12px; border-radius: 100px;
}

/* Navbar — keep clean when action buttons are visible */
.navbar { gap: 10px; }
.nav-right { gap: 6px; }
.nav-btn   { padding: 5px 12px; font-size: 11px; }
.ai-pill   { padding: 5px 12px; font-size: 11px; }
"""

if "UI TOPBAR + CARDS FIXES" not in css:
    with open("frontend/style.css", "a", encoding="utf-8") as f:
        f.write(PATCH_CSS)
    print("style.css: topbar + gauge card fixes appended")
else:
    print("style.css: already has topbar fixes")

print("\n=== DONE — restart server and hard refresh ===")
