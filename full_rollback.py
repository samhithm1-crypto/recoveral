"""
full_rollback.py — Reverts everything to the pause-4 state:
  ✅ 4 forensic panels + Gemini AI + fragment recovery
  ❌ No deleted recovery
  ❌ No ui redesign files
  ❌ No ai-chat endpoint
"""
import os, re

# ── 1. Strip app.py: remove import + all deleted/ai-chat endpoints ────────────
with open("app.py", encoding="utf-8", errors="replace") as f:
    lines = f.readlines()

clean = []
skip  = False
for i, line in enumerate(lines):
    # Remove deleted_recovery import (line 8)
    if "import deleted_recovery" in line:
        continue
    # Remove from "DELETED FILE RECOVERY" header onward → stop at AI CONFIG
    if "DELETED FILE RECOVERY ENDPOINTS" in line or "DELETED FILE RECOVERY" in line:
        skip = True
    if skip and ("# \u2500\u2500\u2500 AI CONFIG" in line or "# \u2550" in line and "AI CONFIG" in line.upper()):
        skip = False
    # Also remove the ai-chat endpoint block (added later)
    if '@app.route("/api/ai-chat"' in line:
        skip = True
    # Stop skip at the # \u2500\u2500\u2500 AI CONFIG marker
    if skip and "AI CONFIG" in line.upper() and "#" in line and "ai-chat" not in line.lower():
        skip = False
    if not skip:
        clean.append(line)

# Ensure the startup block is present at the end
startup = '''

# \u2500\u2500\u2500 AI CONFIG \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
'''

with open("app.py", "w", encoding="utf-8") as f:
    content = "".join(clean)
    f.write(content)

# Verify AI CONFIG section is still there
with open("app.py", encoding="utf-8") as f:
    app_content = f.read()

if "AI CONFIG" not in app_content.upper():
    print("WARNING: AI CONFIG section missing - check app.py")
else:
    print("app.py cleaned - deleted routes removed, AI config kept")

# ── 2. Strip app.js at line 1404 (start of DELETED FILE RECOVERY MODULE) ──────
with open("frontend/app.js", encoding="utf-8", errors="replace") as f:
    js_lines = f.readlines()

# Find exact cut line
cut = None
for i, l in enumerate(js_lines):
    if "DELETED FILE RECOVERY MODULE" in l or "DELETED FILE RECOVERY" in l:
        # Go back to the separator comment
        cut = max(0, i - 3)
        break

if cut:
    with open("frontend/app.js", "w", encoding="utf-8") as f:
        f.writelines(js_lines[:cut])
    print(f"app.js trimmed at line {cut+1} - deleted recovery module removed")
else:
    print("WARNING: Could not find DELETED FILE RECOVERY MODULE in app.js")

print(f"app.js now has {len(js_lines[:cut])} lines")

# ── 3. Remove ui.js if it exists ─────────────────────────────────────────────
for fname in ["frontend/ui.js", "frontend/build_ui.py"]:
    if os.path.exists(fname):
        os.remove(fname)
        print(f"Removed {fname}")

# ── 4. Write original clean index.html (no deleted recovery, no onboarding) ───
HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>RecoverAI \u2014 Forensic Data Recovery</title>
  <meta name="description" content="AI-powered forensic data recovery: reconstruct, classify and restore deleted or corrupted files with Gemini AI assistance."/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet"/>
  <link rel="stylesheet" href="style.css"/>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.8.2/jspdf.plugin.autotable.min.js"></script>
</head>
<body>

<!-- \u2550\u2550 LOADING OVERLAY \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 -->
<div id="loadingOverlay" class="loading-overlay">
  <div class="lo-content">
    <div class="lo-spinner">
      <svg class="lo-ring" viewBox="0 0 80 80">
        <circle cx="40" cy="40" r="32" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="6"/>
        <circle cx="40" cy="40" r="32" fill="none" stroke="url(#loGrad)" stroke-width="6"
          stroke-linecap="round" stroke-dasharray="200.96" stroke-dashoffset="150"
          style="animation:loSpin 1.4s linear infinite"/>
        <defs>
          <linearGradient id="loGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#60A5FA"/>
            <stop offset="100%" stop-color="#A78BFA"/>
          </linearGradient>
        </defs>
      </svg>
      <span class="lo-icon">&#129302;</span>
    </div>
    <h2 class="lo-title">Analyzing&hellip;</h2>
    <div class="lo-steps">
      <div class="lo-step" id="ls1">Reading file signatures&hellip;</div>
      <div class="lo-step" id="ls2">Detecting file types&hellip;</div>
      <div class="lo-step" id="ls3">Calculating integrity scores&hellip;</div>
      <div class="lo-step" id="ls4">Running AI reconstruction&hellip;</div>
      <div class="lo-step" id="ls5">Classifying fragments&hellip;</div>
      <div class="lo-step" id="ls6">Building forensic report&hellip;</div>
    </div>
  </div>
</div>

<!-- \u2550\u2550 NAVBAR \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 -->
<nav class="navbar">
  <div class="nav-brand">
    <span class="nav-brand-icon">&#x26E1;</span>
    <span class="nav-brand-text">Recover<span class="brand-accent">AI</span></span>
    <span class="nav-badge">FORENSIC</span>
  </div>
  <div class="nav-center" id="navCenter" style="display:none">
    <span class="nav-scan-id" id="scanId"></span>
    <span class="nav-scan-file" id="scanFile"></span>
  </div>
  <div class="nav-right">
    <div class="ai-pill" id="aiStatusPill" onclick="openAIConfig()" title="Configure Gemini AI">
      <span class="ai-pill-dot" id="aiStatusDot"></span>
      <span id="aiStatusText">AI: Checking&hellip;</span>
    </div>
    <button class="nav-btn" id="exportPdfBtn" style="display:none" onclick="exportPDF()">&#128196; PDF</button>
    <button class="nav-btn" style="display:none" id="exportCsvBtn" onclick="exportCSV()">&#128202; CSV</button>
    <button class="nav-btn danger" style="display:none" id="newScanBtn" onclick="newScan()">&#8634; New Scan</button>
  </div>
</nav>

<!-- \u2550\u2550 HERO \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 -->
<section id="hero" class="hero-section">
  <div class="hero-bg-orbs">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>
  </div>
  <div class="hero-inner">
    <div class="hero-badge">&#129302; Powered by Gemini AI</div>
    <h1 class="hero-title">Recover What<br/><span class="hero-grad">Others Miss</span></h1>
    <p class="hero-sub">Intelligent fragment reconstruction &middot; Integrity scoring &middot; AI-guided forensic investigation</p>
  </div>
</section>

<!-- \u2550\u2550 UPLOAD SECTION \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 -->
<section id="uploadSection" class="upload-section">
  <input type="file" id="fileInput"   hidden accept="*/*"/>
  <input type="file" id="folderInput" hidden webkitdirectory multiple/>

  <div class="mode-row">
    <button class="mode-btn active" id="modeBtnFile"   onclick="setMode(\'file\')">&#128196; File Mode</button>
    <button class="mode-btn"        id="modeBtnFolder" onclick="setMode(\'folder\')">&#128193; Folder Mode</button>
  </div>

  <div class="upload-zone" id="uploadZone">
    <div class="uz-icon-wrap">
      <span class="uz-icon" id="uploadIcon">&#128196;</span>
    </div>
    <div class="uz-title" id="uploadTitle">Drop Corrupted File / Disk Image Here</div>
    <div class="uz-sub"   id="uploadSub">Supports .img, .dd, .bin, .raw, .pdf, .zip \u2014 any binary</div>
    <div class="uz-actions">
      <button class="btn-primary" id="browseBtn" onclick="triggerBrowse()">&#128269; Browse &amp; Select File</button>
      <button class="btn-ghost" onclick="loadDemo()">&#9654; Demo Scan</button>
    </div>
  </div>

  <div class="features-row">
    <div class="feature-chip"><span>&#128270;</span> Fragment Reconstruction</div>
    <div class="feature-chip"><span>&#128202;</span> Integrity Scoring</div>
    <div class="feature-chip"><span>&#129302;</span> Gemini AI Analysis</div>
    <div class="feature-chip"><span>&#127381;</span> Priority Triage</div>
    <div class="feature-chip"><span>&#128196;</span> PDF / CSV Export</div>
  </div>
</section>

<!-- \u2550\u2550 DASHBOARD \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 -->
<div id="dashboard" style="display:none">

  <section class="summary-section">
    <div class="sum-cards">
      <div class="sum-card">
        <div class="sum-label">Total Fragments</div>
        <div class="sum-val" id="cTotal">0</div>
      </div>
      <div class="sum-card sum-green">
        <div class="sum-label">Recoverable</div>
        <div class="sum-val" id="cRecoverable">0</div>
      </div>
      <div class="sum-card sum-amber">
        <div class="sum-label">Partial</div>
        <div class="sum-val" id="cPartial">0</div>
      </div>
      <div class="sum-card sum-red">
        <div class="sum-label">Critical</div>
        <div class="sum-val" id="cCritical">0</div>
      </div>
      <div class="sum-card sum-blue">
        <div class="sum-label">Recovery Rate</div>
        <div class="sum-val" id="cRate">0%</div>
      </div>
      <div class="sum-card sum-gauge">
        <div class="sum-label">Health</div>
        <div class="gauge-wrap">
          <svg class="gauge-svg" viewBox="0 0 100 60">
            <path d="M12,50 A38,38 0 0,1 88,50" fill="none" stroke="rgba(255,255,255,0.07)" stroke-width="9" stroke-linecap="round"/>
            <path id="gaugeArc" d="M12,50 A38,38 0 0,1 88,50" fill="none" stroke="url(#gaugeGrad)" stroke-width="9"
              stroke-linecap="round" stroke-dasharray="119.38" stroke-dashoffset="119.38"
              style="transition:stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1)"/>
            <defs>
              <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%"   stop-color="#F87171"/>
                <stop offset="50%"  stop-color="#FBBF24"/>
                <stop offset="100%" stop-color="#34D399"/>
              </linearGradient>
            </defs>
          </svg>
          <div class="gauge-pct" id="gaugePct">0%</div>
        </div>
      </div>
    </div>
  </section>

  <section class="ai-panel" id="aiAnalysisPanel" style="display:none">
    <div class="ai-panel-header">
      <div class="ai-panel-left">
        <span class="ai-panel-icon">&#129302;</span>
        <span class="ai-panel-title">Gemini AI Forensic Analysis</span>
        <span class="ai-live-badge" id="geminiLiveBadge" style="display:none">LIVE</span>
      </div>
      <div class="ai-panel-right">
        <span class="ai-badge" id="aiAnalysisBadge" style="display:none"></span>
        <button class="btn-sm" id="regenerateAIBtn" onclick="regenerateAI()" style="display:none">&#8635; Regenerate</button>
      </div>
    </div>
    <div class="ai-panel-body">
      <div id="aiText" class="ai-text">Generating analysis&hellip;</div>
      <div id="geminiOutput" style="display:none"></div>
      <div id="geminiText"   style="display:none"></div>
    </div>
  </section>

  <section class="req-section">
    <div class="req-grid">
      <div class="req-card">
        <div class="req-header req-blue"><span class="req-num">REQ 01</span><span class="req-title">Fragment Reconstruction Pipeline</span></div>
        <div id="reconPipeline" class="req-body"><div class="req-empty">Run a scan to populate</div></div>
      </div>
      <div class="req-card">
        <div class="req-header req-amber"><span class="req-num">REQ 02</span><span class="req-title">Integrity Heatmap</span></div>
        <div id="integrityHeatmap" class="req-body"><div class="req-empty">Run a scan to populate</div></div>
      </div>
      <div class="req-card">
        <div class="req-header req-purple"><span class="req-num">REQ 03</span><span class="req-title">High-Value Asset Classification</span></div>
        <div id="highValueList" class="req-body"><div class="req-empty">Run a scan to populate</div></div>
      </div>
      <div class="req-card">
        <div class="req-header req-green"><span class="req-num">REQ 04</span><span class="req-title">Decision Support</span></div>
        <div id="decisionSupport" class="req-body"><div class="req-empty">Run a scan to populate</div></div>
      </div>
    </div>
  </section>

  <section class="meta-section">
    <div class="meta-grid">
      <div class="meta-card">
        <div class="meta-card-title">&#127891; File Type Categories</div>
        <div id="catList"></div>
      </div>
      <div class="meta-card">
        <div class="meta-card-title">&#128279; Fragment Relationships</div>
        <div id="relList"></div>
      </div>
    </div>
  </section>

  <div id="reconstructionPanel" style="display:none" class="recon-panel-wrap">
    <div class="recon-panel-title">&#9883; Reconstructed Files</div>
  </div>

  <section class="table-section">
    <div class="table-header">
      <h3 class="table-title">&#128202; Fragment Index</h3>
      <div class="table-search-wrap">
        <span class="search-icon">&#128269;</span>
        <input class="table-search" id="fragSearch" placeholder="Filter fragments&hellip;" oninput="filterFragments(this.value)"/>
      </div>
    </div>
    <div class="table-scroll">
      <table class="frag-table">
        <thead>
          <tr>
            <th>#</th><th>Filename</th><th>Type</th><th>Size</th>
            <th>Integrity</th><th>Priority</th><th>SHA-256</th><th>Actions</th>
          </tr>
        </thead>
        <tbody id="fragTableBody"></tbody>
      </table>
    </div>
  </section>

</div><!-- /#dashboard -->

<!-- \u2550\u2550 RECOVERY MODAL \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 -->
<div id="recoveryModal" class="modal-overlay" style="display:none">
  <div class="modal-box">
    <div class="modal-header">
      <h3 class="modal-title" id="recoveryFragName">Fragment Recovery</h3>
      <button class="modal-close" onclick="document.getElementById(\'recoveryModal\').style.display=\'none\'">&times;</button>
    </div>
    <div class="modal-body">
      <div class="rinfo-grid">
        <div class="rinfo-row"><span class="rinfo-lbl">Score</span>   <span id="rInfoScore"></span></div>
        <div class="rinfo-row"><span class="rinfo-lbl">Status</span>  <span id="rInfoStatus"></span></div>
        <div class="rinfo-row"><span class="rinfo-lbl">Entropy</span> <span id="rInfoEntropy"></span></div>
        <div class="rinfo-row"><span class="rinfo-lbl">Type</span>    <span id="rInfoType"></span></div>
      </div>
      <div id="recoveryWarning" class="recovery-warn" style="display:none">
        &#9888; This fragment has integrity issues. Recovery may be partial.
      </div>
      <div id="recoveryActions" style="display:none;flex-direction:column;gap:10px">
        <div class="carve-bar-wrap"><div class="carve-bar" id="recoveryProgressBar" style="width:0%"></div></div>
        <div id="recoveryProgressLabel" style="font-size:11px;color:var(--text3)"></div>
        <div id="recoveryLog" class="recovery-log"></div>
        <button class="btn-primary" id="recoveryDownloadBtn" style="display:none">&#128229; Download Recovered File</button>
      </div>
    </div>
    <div class="modal-footer">
      <button class="btn-ghost" onclick="document.getElementById(\'recoveryModal\').style.display=\'none\'">Close</button>
      <button class="btn-primary" id="activateAIBtn" onclick="recoverFragment(currentRecoveryId)">&#9083; Recover Fragment</button>
    </div>
  </div>
</div>

<!-- \u2550\u2550 AI CONFIG MODAL \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550 -->
<div id="aiConfigModal" class="modal-overlay" style="display:none">
  <div class="modal-box">
    <div class="modal-header">
      <h3 class="modal-title">&#129302; Configure Gemini AI</h3>
      <button class="modal-close" onclick="closeAIConfig()">&times;</button>
    </div>
    <div class="modal-body">
      <p style="color:var(--text2);font-size:13px;margin-bottom:16px">Enter your Google AI Studio API key to enable AI-powered forensic analysis.</p>
      <div style="position:relative">
        <input class="modal-input" id="geminiKeyInput" type="password" placeholder="AQ.Ab8RN6..." style="padding-right:70px"/>
        <button class="key-toggle-btn" id="keyToggleBtn" onclick="toggleKeyVisibility()">Show</button>
      </div>
      <div id="aiConfigStatus" style="font-size:12px;margin-top:10px;color:var(--text3)"></div>
    </div>
    <div class="modal-footer">
      <button class="btn-ghost" onclick="closeAIConfig()">Cancel</button>
      <button class="btn-primary" onclick="saveGeminiKey()">Save &amp; Activate</button>
    </div>
  </div>
</div>

<!-- Toast -->
<div id="recoverToast" class="toast" style="display:none"></div>

<script src="app.js"></script>
</body>
</html>
'''

with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print("index.html restored (no deleted recovery)")

# ── 5. Write clean style.css ──────────────────────────────────────────────────
CSS = open("frontend/style.css", encoding="utf-8", errors="replace").read()

# Check if it already has the right content (no deleted-overlay classes needed)
# Just ensure it doesn't have onboarding / multi-page nav that was added
# We'll write a clean version
STYLE = ''':root {
  --bg:       #0A0F1E;
  --bg2:      #0F1629;
  --surface:  #141E35;
  --surface2: #1A2540;
  --surface3: #212E4A;
  --border:   rgba(148,163,184,0.1);
  --border2:  rgba(148,163,184,0.06);
  --text:     #E2E8F0;
  --text2:    #94A3B8;
  --text3:    #64748B;
  --blue:     #60A5FA;
  --blue-d:   #3B82F6;
  --green:    #34D399;
  --amber:    #FBBF24;
  --red:      #F87171;
  --purple:   #A78BFA;
  --cyan:     #67E8F9;
  --font:     "Inter", sans-serif;
  --mono:     "JetBrains Mono", monospace;
  --radius:   12px;
  --radius-lg:18px;
  --shadow:   0 4px 24px rgba(0,0,0,0.5);
  --shadow-lg:0 12px 48px rgba(0,0,0,0.6);
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { font-family: var(--font); background: var(--bg); color: var(--text); line-height: 1.6; min-height: 100vh; overflow-x: hidden; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--surface3); border-radius: 3px; }

/* Loading overlay */
.loading-overlay { position:fixed;inset:0;z-index:1000;background:rgba(10,15,30,0.97);backdrop-filter:blur(12px);display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity 0.35s ease; }
.loading-overlay.active { opacity:1;pointer-events:all; }
.lo-content { text-align:center;display:flex;flex-direction:column;align-items:center;gap:20px; }
.lo-spinner { position:relative;width:80px;height:80px;display:flex;align-items:center;justify-content:center; }
.lo-ring { width:80px;height:80px;position:absolute;animation:loSpin 1.4s linear infinite; }
@keyframes loSpin { to { transform:rotate(360deg); } }
.lo-icon { font-size:28px;position:relative;z-index:1; }
.lo-title { font-size:20px;font-weight:700;color:var(--text); }
.lo-steps { display:flex;flex-direction:column;gap:6px;min-width:300px;text-align:left; }
.lo-step { padding:9px 16px;border-radius:10px;font-size:12px;color:var(--text3);background:var(--surface);border:1px solid var(--border);font-family:var(--mono);transition:all 0.3s; }
.lo-step.active { color:var(--blue);border-color:rgba(96,165,250,0.4);background:rgba(96,165,250,0.08);animation:stepPulse 1s ease infinite; }
.lo-step.done { color:var(--green);border-color:rgba(52,211,153,0.3);background:rgba(52,211,153,0.06); }
@keyframes stepPulse { 0%,100%{opacity:1} 50%{opacity:0.65} }

/* Navbar */
.navbar { position:sticky;top:0;z-index:100;display:flex;align-items:center;gap:16px;padding:0 28px;height:60px;background:rgba(10,15,30,0.85);backdrop-filter:blur(20px);border-bottom:1px solid var(--border); }
.nav-brand { display:flex;align-items:center;gap:10px;flex-shrink:0; }
.nav-brand-icon { font-size:20px; }
.nav-brand-text { font-size:17px;font-weight:800;color:var(--text);letter-spacing:-0.3px; }
.brand-accent { color:var(--blue); }
.nav-badge { font-size:9px;font-weight:700;letter-spacing:1.5px;padding:2px 8px;border-radius:100px;border:1px solid rgba(96,165,250,0.35);color:var(--blue);background:rgba(96,165,250,0.08); }
.nav-center { display:flex;align-items:center;gap:12px;flex:1;justify-content:center; }
.nav-scan-id { font-family:var(--mono);font-size:10px;font-weight:700;color:var(--blue);background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.25);padding:3px 10px;border-radius:100px; }
.nav-scan-file { font-family:var(--mono);font-size:10px;color:var(--text3); }
.nav-right { display:flex;align-items:center;gap:8px;flex-shrink:0; }
.ai-pill { display:flex;align-items:center;gap:7px;padding:6px 14px;border-radius:100px;border:1px solid var(--border);background:var(--surface);font-size:11px;font-weight:600;cursor:pointer;color:var(--text2);transition:all 0.2s; }
.ai-pill:hover { border-color:var(--blue);color:var(--text); }
.ai-pill-dot { width:7px;height:7px;border-radius:50%;background:var(--text3);transition:background 0.3s; }
.ai-pill-dot.active { background:var(--green);box-shadow:0 0 8px rgba(52,211,153,0.5); }
.ai-pill-dot.error  { background:var(--red); }
.nav-btn { padding:6px 14px;border-radius:8px;border:1px solid var(--border);background:var(--surface);color:var(--text2);font-family:var(--font);font-size:12px;font-weight:600;cursor:pointer;transition:all 0.2s;white-space:nowrap; }
.nav-btn:hover { border-color:var(--blue);color:var(--blue); }
.nav-btn.danger:hover { border-color:var(--red);color:var(--red); }

/* Hero */
.hero-section { position:relative;overflow:hidden;padding:60px 40px 48px;text-align:center;border-bottom:1px solid var(--border); }
.hero-bg-orbs { position:absolute;inset:0;pointer-events:none; }
.orb { position:absolute;border-radius:50%;filter:blur(70px);opacity:0.35;animation:orbFloat 20s ease-in-out infinite; }
.orb-1 { width:350px;height:350px;background:var(--blue);top:-100px;left:-80px;animation-duration:22s; }
.orb-2 { width:300px;height:300px;background:var(--purple);top:-80px;right:-60px;animation-duration:28s;animation-delay:-8s; }
.orb-3 { width:250px;height:250px;background:var(--cyan);bottom:-80px;left:40%;animation-duration:18s;animation-delay:-4s; }
@keyframes orbFloat { 0%,100%{transform:translate(0,0)scale(1)} 33%{transform:translate(15px,-12px)scale(1.04)} 66%{transform:translate(-8px,18px)scale(0.96)} }
.hero-inner { position:relative;z-index:1;max-width:700px;margin:0 auto; }
.hero-badge { display:inline-flex;align-items:center;gap:7px;padding:6px 16px;border-radius:100px;margin-bottom:20px;background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.25);color:var(--blue);font-size:12px;font-weight:700; }
.hero-title { font-size:clamp(2rem,5vw,3.2rem);font-weight:900;color:var(--text);line-height:1.1;margin-bottom:16px;letter-spacing:-1px; }
.hero-grad { background:linear-gradient(135deg,var(--blue),var(--purple),var(--cyan));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text; }
.hero-sub { font-size:14px;color:var(--text2);line-height:1.7; }

/* Upload */
.upload-section { padding:32px 40px; }
.mode-row { display:flex;gap:8px;margin-bottom:20px; }
.mode-btn { padding:8px 20px;border-radius:100px;border:1px solid var(--border);background:transparent;color:var(--text3);font-family:var(--font);font-size:13px;font-weight:600;cursor:pointer;transition:all 0.2s; }
.mode-btn:hover { color:var(--text);border-color:var(--blue); }
.mode-btn.active { color:var(--blue);background:rgba(96,165,250,0.1);border-color:rgba(96,165,250,0.4); }
.upload-zone { background:var(--surface);border:2px dashed var(--border);border-radius:20px;padding:48px 32px;text-align:center;position:relative;overflow:hidden;transition:all 0.3s;margin-bottom:24px; }
.upload-zone:hover,.upload-zone.drag-over { border-color:var(--blue);background:rgba(96,165,250,0.04); }
.uz-icon-wrap { width:80px;height:80px;border-radius:50%;margin:0 auto 18px;background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.2);display:flex;align-items:center;justify-content:center;transition:transform 0.3s; }
.upload-zone:hover .uz-icon-wrap { transform:scale(1.08); }
.uz-icon  { font-size:32px;display:block; }
.uz-title { font-size:18px;font-weight:700;color:var(--text);margin-bottom:8px; }
.uz-sub   { font-size:13px;color:var(--text3);margin-bottom:28px; }
.uz-actions { display:flex;gap:12px;justify-content:center;flex-wrap:wrap; }
.btn-primary { padding:11px 26px;border-radius:100px;border:none;background:linear-gradient(135deg,var(--blue-d),var(--purple));color:#fff;font-family:var(--font);font-size:13px;font-weight:700;cursor:pointer;transition:all 0.25s;box-shadow:0 4px 18px rgba(96,165,250,0.3); }
.btn-primary:hover { transform:translateY(-2px);box-shadow:0 8px 24px rgba(96,165,250,0.4); }
.btn-primary:active { transform:scale(0.97); }
.btn-primary:disabled { opacity:0.55;cursor:default;transform:none; }
.btn-ghost { padding:11px 26px;border-radius:100px;border:1px solid var(--border);background:transparent;color:var(--text2);font-family:var(--font);font-size:13px;font-weight:600;cursor:pointer;transition:all 0.2s; }
.btn-ghost:hover { border-color:var(--blue);color:var(--blue); }
.btn-sm { padding:6px 14px;border-radius:8px;border:1px solid var(--border);background:var(--surface);color:var(--text2);font-family:var(--font);font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s; }
.btn-sm:hover { border-color:var(--blue);color:var(--blue); }
.features-row { display:flex;flex-wrap:wrap;gap:10px; }
.feature-chip { display:flex;align-items:center;gap:6px;padding:7px 14px;border-radius:100px;background:var(--surface);border:1px solid var(--border);font-size:12px;color:var(--text2);transition:all 0.2s; }
.feature-chip:hover { border-color:var(--blue);color:var(--blue); }

/* Summary */
.summary-section { padding:24px 40px; }
.sum-cards { display:grid;grid-template-columns:repeat(6,1fr);gap:14px; }
.sum-card { background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);padding:18px 14px;text-align:center;transition:transform 0.2s,box-shadow 0.2s; }
.sum-card:hover { transform:translateY(-3px);box-shadow:var(--shadow); }
.sum-label { font-size:10px;text-transform:uppercase;letter-spacing:0.8px;color:var(--text3);margin-bottom:8px; }
.sum-val   { font-size:28px;font-weight:800;color:var(--text); }
.sum-green .sum-val { color:var(--green); }
.sum-amber .sum-val { color:var(--amber); }
.sum-red   .sum-val { color:var(--red); }
.sum-blue  .sum-val { color:var(--blue); }
.sum-gauge { padding:10px 8px; }
.gauge-wrap { display:flex;flex-direction:column;align-items:center; }
.gauge-svg  { width:100px;height:60px; }
.gauge-pct  { font-size:18px;font-weight:800;color:var(--text);margin-top:2px; }

/* AI Panel */
.ai-panel { margin:0 40px 24px;background:linear-gradient(135deg,rgba(96,165,250,0.06),rgba(167,139,250,0.06));border:1px solid rgba(96,165,250,0.2);border-radius:var(--radius-lg);padding:20px 24px;animation:fadeUp 0.4s ease; }
@keyframes fadeUp { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:none} }
.ai-panel-header { display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:10px; }
.ai-panel-left  { display:flex;align-items:center;gap:10px; }
.ai-panel-right { display:flex;align-items:center;gap:8px; }
.ai-panel-icon  { font-size:20px; }
.ai-panel-title { font-size:14px;font-weight:700;color:var(--text); }
.ai-live-badge  { font-size:9px;font-weight:800;letter-spacing:2px;padding:3px 8px;border-radius:100px;color:var(--green);background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.3);animation:blink 1.5s ease infinite; }
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.4} }
.ai-text { font-size:13px;color:var(--text2);line-height:1.8;white-space:pre-wrap; }
.ai-badge { font-size:11px;font-weight:700;padding:4px 12px;border-radius:100px;background:rgba(167,139,250,0.1);color:var(--purple);border:1px solid rgba(167,139,250,0.25); }

/* Requirements */
.req-section { padding:0 40px 24px; }
.req-grid { display:grid;grid-template-columns:1fr 1fr;gap:16px; }
.req-card { background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden; }
.req-header { display:flex;align-items:center;gap:10px;padding:14px 18px;border-bottom:1px solid var(--border);background:var(--surface2); }
.req-num   { font-family:var(--mono);font-size:10px;font-weight:800;padding:3px 8px;border-radius:100px; }
.req-title { font-size:13px;font-weight:700;color:var(--text); }
.req-body  { padding:16px 18px; }
.req-empty { color:var(--text3);font-size:13px;text-align:center;padding:36px 0;font-style:italic; }
.req-blue   .req-num { color:var(--blue);background:rgba(96,165,250,0.1);border:1px solid rgba(96,165,250,0.25); }
.req-amber  .req-num { color:var(--amber);background:rgba(251,191,36,0.1);border:1px solid rgba(251,191,36,0.25); }
.req-purple .req-num { color:var(--purple);background:rgba(167,139,250,0.1);border:1px solid rgba(167,139,250,0.25); }
.req-green  .req-num { color:var(--green);background:rgba(52,211,153,0.1);border:1px solid rgba(52,211,153,0.25); }

/* Meta */
.meta-section { padding:0 40px 24px; }
.meta-grid { display:grid;grid-template-columns:1fr 1fr;gap:16px; }
.meta-card { background:var(--surface);border:1px solid var(--border);border-radius:var(--radius-lg);padding:20px; }
.meta-card-title { font-size:13px;font-weight:700;color:var(--text);margin-bottom:14px; }
.recon-panel-wrap { margin:0 40px 24px;background:var(--surface);border:1px solid rgba(52,211,153,0.25);border-radius:var(--radius-lg);padding:20px; }
.recon-panel-title { font-size:14px;font-weight:700;color:var(--green);margin-bottom:14px; }

/* Table */
.table-section { padding:0 40px 48px; }
.table-header { display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;flex-wrap:wrap;gap:12px; }
.table-title { font-size:15px;font-weight:700;color:var(--text); }
.table-search-wrap { display:flex;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--border);border-radius:100px;padding:7px 16px; }
.search-icon  { font-size:13px;color:var(--text3); }
.table-search { background:none;border:none;outline:none;font-family:var(--font);font-size:13px;color:var(--text);width:200px; }
.table-search::placeholder { color:var(--text3); }
.table-scroll { overflow-x:auto; }
.frag-table { width:100%;border-collapse:collapse;font-size:12px; }
.frag-table th { padding:11px 14px;text-align:left;white-space:nowrap;font-size:10px;font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--text3);border-bottom:1px solid var(--border);background:var(--surface);position:sticky;top:0;z-index:1; }
.frag-table td { padding:10px 14px;border-bottom:1px solid var(--border2);font-family:var(--mono);color:var(--text2);vertical-align:middle;white-space:nowrap; }
.frag-table tbody tr { transition:background 0.15s;animation:rowFade 0.3s ease forwards; }
.frag-table tbody tr:hover { background:var(--surface2); }
@keyframes rowFade { from{opacity:0;transform:translateX(-6px)} to{opacity:1;transform:none} }

/* Badges */
.badge { display:inline-flex;align-items:center;gap:4px;padding:3px 10px;border-radius:100px;font-size:10px;font-weight:700;font-family:var(--mono); }
.badge-green  { background:rgba(52,211,153,0.1);color:var(--green);border:1px solid rgba(52,211,153,0.2); }
.badge-amber  { background:rgba(251,191,36,0.1);color:var(--amber);border:1px solid rgba(251,191,36,0.2); }
.badge-red    { background:rgba(248,113,113,0.1);color:var(--red);border:1px solid rgba(248,113,113,0.2); }
.badge-blue   { background:rgba(96,165,250,0.1);color:var(--blue);border:1px solid rgba(96,165,250,0.2); }
.badge-purple { background:rgba(167,139,250,0.1);color:var(--purple);border:1px solid rgba(167,139,250,0.2); }
.action-btn { padding:4px 10px;border-radius:7px;border:1px solid var(--border);background:var(--surface2);color:var(--text2);font-family:var(--font);font-size:11px;font-weight:600;cursor:pointer;transition:all 0.2s;white-space:nowrap;margin-right:4px; }
.action-btn:hover { border-color:var(--blue);color:var(--blue); }
.action-btn.ai-btn { border-color:rgba(167,139,250,0.3);color:var(--purple);background:rgba(167,139,250,0.06); }
.action-btn.ai-btn:hover { background:rgba(167,139,250,0.14); }

/* Modals */
.modal-overlay { position:fixed;inset:0;z-index:800;background:rgba(10,15,30,0.75);backdrop-filter:blur(10px);display:flex;align-items:center;justify-content:center; }
.modal-box { background:var(--surface);border:1px solid var(--border);border-radius:20px;padding:28px;width:min(460px,94vw);box-shadow:var(--shadow-lg);animation:modalIn 0.35s cubic-bezier(0.34,1.56,0.64,1); }
@keyframes modalIn { from{opacity:0;transform:scale(0.92)translateY(14px)} to{opacity:1;transform:none} }
.modal-header { display:flex;justify-content:space-between;align-items:center;margin-bottom:18px; }
.modal-title  { font-size:16px;font-weight:700;color:var(--text); }
.modal-close  { background:none;border:none;color:var(--text3);font-size:20px;cursor:pointer;transition:color 0.2s; }
.modal-close:hover { color:var(--text); }
.modal-body   { margin-bottom:20px; }
.modal-footer { display:flex;gap:10px;justify-content:flex-end; }
.modal-input { width:100%;background:var(--bg2);border:1px solid var(--border);border-radius:10px;padding:11px 16px;font-family:var(--mono);font-size:13px;color:var(--text);outline:none;transition:border-color 0.2s; }
.modal-input:focus { border-color:var(--blue); }
.key-toggle-btn { position:absolute;right:10px;top:50%;transform:translateY(-50%);background:var(--surface2);border:1px solid var(--border);color:var(--text2);border-radius:6px;padding:3px 10px;font-size:11px;cursor:pointer;font-family:var(--font); }
.rinfo-grid { display:flex;flex-direction:column;gap:8px;margin-bottom:14px; }
.rinfo-row  { display:flex;align-items:center;gap:10px; }
.rinfo-lbl  { font-size:11px;color:var(--text3);width:60px;font-weight:600; }
.recovery-warn { padding:10px 14px;border-radius:10px;margin-bottom:12px;background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.3);color:var(--amber);font-size:12px; }
.recovery-log { font-family:var(--mono);font-size:11px;color:var(--text3);max-height:100px;overflow-y:auto;background:var(--bg2);border:1px solid var(--border);border-radius:8px;padding:8px 12px;line-height:1.8; }
.carve-bar-wrap { height:6px;border-radius:3px;background:rgba(255,255,255,0.06);overflow:hidden;margin-bottom:8px; }
.carve-bar { height:100%;border-radius:3px;background:linear-gradient(90deg,var(--blue-d),var(--purple));transition:width 0.5s ease; }

/* Toast */
.toast { position:fixed;bottom:28px;right:28px;z-index:9999;padding:14px 22px;border-radius:14px;font-family:var(--font);font-size:13px;font-weight:600;max-width:360px;line-height:1.5;box-shadow:0 8px 32px rgba(0,0,0,0.4);background:rgba(22,163,74,0.92);border:1px solid rgba(74,222,128,0.4);color:#fff;transition:opacity 0.4s ease; }
.toast.error { background:rgba(220,38,38,0.92);border-color:rgba(248,113,113,0.4); }

/* Pipeline, Integrity Heatmap, High-Value, Decision — all used by app.js */
.pipeline-item { display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:10px;background:rgba(255,255,255,0.03);border:1px solid var(--border);margin-bottom:6px; }
.pipeline-order { width:28px;height:28px;border-radius:50%;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;font-family:var(--mono);background:rgba(96,165,250,0.12);color:var(--blue);border:1px solid rgba(96,165,250,0.25); }
.pipeline-arrow { color:var(--text3);font-size:10px;padding:3px 0;text-align:center; }
.pipeline-info  { flex:1; }
.pipeline-name  { font-size:12px;font-weight:700;color:var(--text);font-family:var(--mono); }
.pipeline-meta  { font-size:10px;color:var(--text3);margin-top:2px; }
.pipeline-status { font-size:10px;font-weight:700;font-family:var(--mono);padding:3px 8px;border-radius:6px; }
.pipeline-status.ok   { background:rgba(52,211,153,0.1);color:var(--green); }
.pipeline-status.par  { background:rgba(251,191,36,0.1);color:var(--amber); }
.pipeline-status.crit { background:rgba(248,113,113,0.1);color:var(--red); }
.ih-row { display:flex;align-items:center;gap:8px;margin-bottom:6px; }
.ih-label { font-family:var(--mono);font-size:10px;color:var(--text3);width:110px;flex-shrink:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
.ih-bar-wrap { flex:1;height:16px;border-radius:4px;background:rgba(255,255,255,0.05);overflow:hidden; }
.ih-bar { height:100%;border-radius:4px;transition:width 1s ease;position:relative; }
.ih-bar::after { content:attr(data-pct);position:absolute;right:6px;top:50%;transform:translateY(-50%);font-size:9px;font-weight:700;color:#fff;font-family:var(--mono); }
.ih-bar.green { background:linear-gradient(90deg,#059669,#34d399); }
.ih-bar.amber { background:linear-gradient(90deg,#d97706,#fbbf24); }
.ih-bar.red   { background:linear-gradient(90deg,#dc2626,#f87171); }
.hv-item { display:flex;align-items:center;gap:12px;padding:10px 14px;border-radius:10px;background:rgba(255,255,255,0.03);border:1px solid var(--border);margin-bottom:6px;transition:border-color 0.2s; }
.hv-item:hover { border-color:var(--purple); }
.hv-rank { font-size:13px;font-weight:800;font-family:var(--mono);color:var(--purple);width:24px;flex-shrink:0;text-align:center; }
.hv-icon { font-size:20px;flex-shrink:0; }
.hv-info { flex:1; }
.hv-name { font-size:12px;font-weight:700;color:var(--text);font-family:var(--mono); }
.hv-type { font-size:10px;color:var(--text3);margin-top:2px; }
.hv-score { font-size:11px;font-weight:800;font-family:var(--mono);padding:4px 10px;border-radius:100px; }
.hv-score.s-high { background:rgba(52,211,153,0.1);color:var(--green);border:1px solid rgba(52,211,153,0.25); }
.hv-score.s-mid  { background:rgba(251,191,36,0.1);color:var(--amber);border:1px solid rgba(251,191,36,0.25); }
.hv-score.s-low  { background:rgba(248,113,113,0.1);color:var(--red);border:1px solid rgba(248,113,113,0.25); }
.decision-stat-row { display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:12px; }
.decision-stat { text-align:center;padding:10px 6px;border-radius:10px;background:rgba(255,255,255,0.03);border:1px solid var(--border); }
.decision-stat-val { font-size:20px;font-weight:800; }
.decision-stat-lbl { font-size:9px;color:var(--text3);letter-spacing:0.5px;margin-top:2px;text-transform:uppercase; }
.ds-green{color:var(--green)} .ds-amber{color:var(--amber)} .ds-red{color:var(--red)}
.decision-section-title { font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--text3);margin-bottom:6px;margin-top:10px;display:flex;align-items:center;gap:6px; }
.decision-section-title::after { content:"";flex:1;height:1px;background:var(--border); }
.decision-can  { border-left:3px solid var(--green);padding:10px 14px;border-radius:0 8px 8px 0;background:rgba(52,211,153,0.05);margin-bottom:8px; }
.decision-risk { border-left:3px solid var(--amber);padding:10px 14px;border-radius:0 8px 8px 0;background:rgba(251,191,36,0.05);margin-bottom:8px; }
.decision-lost { border-left:3px solid var(--red);padding:10px 14px;border-radius:0 8px 8px 0;background:rgba(248,113,113,0.05);margin-bottom:8px; }
.decision-item { font-size:12px;color:var(--text2);line-height:1.6;display:flex;align-items:flex-start;gap:6px;margin-bottom:4px; }
.decision-dot  { flex-shrink:0;margin-top:4px; }

/* Responsive */
@media (max-width:1100px) { .sum-cards{grid-template-columns:repeat(3,1fr)} .req-grid{grid-template-columns:1fr} .meta-grid{grid-template-columns:1fr} }
@media (max-width:768px) { .upload-section,.summary-section,.req-section,.meta-section,.table-section{padding-left:16px;padding-right:16px} .hero-section{padding:40px 20px 32px} .sum-cards{grid-template-columns:repeat(2,1fr)} .uz-actions{flex-direction:column;align-items:center} .navbar{padding:0 16px;gap:8px} .nav-scan-file{display:none} .ai-panel{margin-left:16px;margin-right:16px} }
'''

with open("frontend/style.css", "w", encoding="utf-8") as f:
    f.write(STYLE)
print("style.css restored")

print("\n=== ROLLBACK COMPLETE ===")
print("- app.py: deleted recovery routes removed, AI config kept")
print("- app.js: trimmed at DELETED FILE RECOVERY MODULE")
print("- index.html: no deleted recovery overlay, no ui redesign")
print("- style.css: clean original design")
print("- ui.js: removed")
print("\nRestart the server and reload http://localhost:5000")
