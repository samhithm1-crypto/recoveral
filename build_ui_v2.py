"""
build_ui_v2.py — Rewrites index.html to include ALL IDs that app.js needs,
mapped into the new beautiful UI structure.
"""

HTML = '''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>RecoverAI — Forensic Data Recovery Platform</title>
  <meta name="description" content="AI-powered forensic data recovery platform — reconstruct, classify and restore deleted or corrupted files with Gemini AI."/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet"/>
  <link rel="stylesheet" href="style.css"/>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.8.2/jspdf.plugin.autotable.min.js"></script>
</head>
<body>

<!-- ══ ONBOARDING OVERLAY ════════════════════════════════════════════════════ -->
<div id="onboardingOverlay" class="ob-overlay">
  <div class="ob-card">
    <div class="ob-step active" id="ob-step-1">
      <div class="ob-logo-ring">
        <div class="ob-logo-orb"></div>
        <span class="ob-logo-icon">&#x26E1;</span>
      </div>
      <h1 class="ob-title">Welcome to<br/><span class="grad-text">RecoverAI</span></h1>
      <p class="ob-body">Your AI-powered forensic companion.<br/>We find, reconstruct and restore what others miss.</p>
      <button class="ob-btn" onclick="obNext(2)">Get Started &rarr;</button>
    </div>
    <div class="ob-step" id="ob-step-2">
      <h2 class="ob-title" style="font-size:1.5rem">What are you trying to recover?</h2>
      <div class="ob-cards">
        <div class="ob-option-card" onclick="selectGoal(this,\'deleted\')">
          <div class="ob-opt-icon">&#128465;</div>
          <div class="ob-opt-label">Deleted Files</div>
          <div class="ob-opt-sub">Recycle Bin &amp; free space</div>
        </div>
        <div class="ob-option-card" onclick="selectGoal(this,\'corrupted\')">
          <div class="ob-opt-icon">&#128190;</div>
          <div class="ob-opt-label">Corrupted Storage</div>
          <div class="ob-opt-sub">Disk images &amp; fragments</div>
        </div>
        <div class="ob-option-card" onclick="selectGoal(this,\'forensic\')">
          <div class="ob-opt-icon">&#128270;</div>
          <div class="ob-opt-label">Full Forensic Analysis</div>
          <div class="ob-opt-sub">Deep AI-assisted investigation</div>
        </div>
      </div>
      <button class="ob-btn" onclick="obNext(3)">Continue &rarr;</button>
    </div>
    <div class="ob-step" id="ob-step-3">
      <div class="ob-ready-ring">
        <svg class="ob-check-svg" viewBox="0 0 80 80">
          <circle class="ob-check-circle" cx="40" cy="40" r="36"/>
          <polyline class="ob-check-mark" points="24,42 35,53 56,28"/>
        </svg>
      </div>
      <h2 class="ob-title">You\'re all set!</h2>
      <p class="ob-body">Gemini AI is standing by.<br/>Let\'s recover what matters.</p>
      <button class="ob-btn" onclick="finishOnboarding()">Launch RecoverAI &#x2192;</button>
    </div>
    <div class="ob-dots">
      <span class="ob-dot active" id="ob-dot-1"></span>
      <span class="ob-dot" id="ob-dot-2"></span>
      <span class="ob-dot" id="ob-dot-3"></span>
    </div>
  </div>
</div>

<!-- ══ LOADING OVERLAY (app.js uses #loadingOverlay with .active class) ══════ -->
<div id="loadingOverlay" class="loading-overlay">
  <div class="lo-inner">
    <div class="lo-orb-ring">
      <div class="lo-orb"></div>
    </div>
    <h3 class="lo-title">Analyzing your data&hellip;</h3>
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

<!-- ══ TOP NAVIGATION ════════════════════════════════════════════════════════ -->
<nav class="top-nav" id="topNav">
  <div class="nav-logo" onclick="showPage(\'home\')">
    <span class="nav-logo-icon">&#x26E1;</span>
    <span class="nav-logo-text">Recover<span class="nav-logo-accent">AI</span></span>
    <span class="nav-logo-badge">FORENSIC</span>
  </div>
  <div class="nav-tabs" id="navTabs">
    <button class="nav-tab active" data-page="home"    onclick="showPage(\'home\')">&#127968; Home</button>
    <button class="nav-tab"        data-page="results" onclick="showPage(\'results\')">&#128202; Results</button>
    <button class="nav-tab"        data-page="ai"      onclick="showPage(\'ai\')">&#129302; AI Coach</button>
    <button class="nav-tab"        data-page="deleted" onclick="showPage(\'deleted\')">&#128465; Recovery</button>
  </div>
  <div class="nav-right">
    <div class="ai-status-pill" id="aiStatusPill" onclick="openAIConfig()" title="Configure Gemini AI">
      <span class="ai-status-dot" id="aiStatusDot"></span>
      <span class="ai-status-text" id="aiStatusText">AI: Checking&hellip;</span>
    </div>
    <button class="theme-toggle" id="themeToggle" onclick="toggleTheme()" title="Toggle theme">
      <span id="themeIcon">&#9790;</span>
    </button>
  </div>
</nav>

<!-- ══ APP PAGES ═════════════════════════════════════════════════════════════ -->
<main class="app-main">

  <!-- ── HOME PAGE ──────────────────────────────────────────────────────────── -->
  <!-- hero and uploadSection are used by app.js to show/hide — keep them here -->
  <section class="page active" id="page-home">

    <!-- app.js references #hero to hide it after scan -->
    <div id="hero">
      <div class="hero-banner">
        <div class="hero-orbs">
          <div class="hero-orb hero-orb-1"></div>
          <div class="hero-orb hero-orb-2"></div>
          <div class="hero-orb hero-orb-3"></div>
        </div>
        <div class="hero-content">
          <div class="hero-chip">&#129302; Powered by Gemini AI</div>
          <h1 class="hero-headline">Recover What<br/><span class="grad-text">Others Miss</span></h1>
          <p class="hero-sub">Intelligent fragment reconstruction, integrity scoring &amp;<br/>AI-guided forensic investigation &mdash; all in one platform.</p>
        </div>
      </div>
    </div>

    <!-- app.js references #uploadSection to hide it after scan -->
    <div id="uploadSection">
      <!-- hidden real inputs -->
      <input type="file" id="fileInput" hidden accept="*/*"/>
      <input type="file" id="folderInput" hidden webkitdirectory multiple/>

      <!-- Mode toggle (app.js uses #modeBtnFile / #modeBtnFolder) -->
      <div class="mode-toggle-row">
        <button class="mode-btn active" id="modeBtnFile"   onclick="setMode(\'file\')">&#128196; File Mode</button>
        <button class="mode-btn"        id="modeBtnFolder" onclick="setMode(\'folder\')">&#128193; Folder Mode</button>
      </div>

      <div class="upload-zone" id="uploadZone">
        <div class="upload-anim">
          <div class="upload-ring"></div>
          <div class="upload-icon-wrap">
            <span class="upload-icon" id="uploadIcon">&#128196;</span>
          </div>
        </div>
        <div class="upload-text">
          <div class="upload-title" id="uploadTitle">Drop Corrupted File / Disk Image Here</div>
          <div class="upload-sub"   id="uploadSub">Supports .img, .dd, .bin, .raw, .pdf, .zip &mdash; any binary</div>
        </div>
        <div class="upload-actions">
          <button class="btn-upload" id="browseBtn" onclick="triggerBrowse()">&#128269; Analyze File</button>
          <button class="btn-upload-ghost" onclick="loadDemo()">&#9654; Demo Scan</button>
          <button class="btn-upload-danger" onclick="showPage(\'deleted\')">&#128465; Recover Deleted</button>
        </div>
      </div>

      <div class="feature-row">
        <div class="feature-card" style="--fc-delay:0s">
          <div class="feature-card-icon">&#128270;</div>
          <div class="feature-card-title">Fragment Reconstruction</div>
          <div class="feature-card-body">Intelligently orders and reassembles fragmented files from raw byte signatures.</div>
        </div>
        <div class="feature-card" style="--fc-delay:0.1s">
          <div class="feature-card-icon">&#128202;</div>
          <div class="feature-card-title">Integrity Scoring</div>
          <div class="feature-card-body">Every fragment is entropy-analyzed and scored for recoverability.</div>
        </div>
        <div class="feature-card" style="--fc-delay:0.2s">
          <div class="feature-card-icon">&#129302;</div>
          <div class="feature-card-title">Gemini AI Advisor</div>
          <div class="feature-card-body">Real-time AI explanations and action recommendations.</div>
        </div>
        <div class="feature-card" style="--fc-delay:0.3s">
          <div class="feature-card-icon">&#128465;</div>
          <div class="feature-card-title">Deleted Recovery</div>
          <div class="feature-card-body">Scan Recycle Bin, free disk sectors and temp caches.</div>
        </div>
      </div>
    </div>
  </section>

  <!-- ── DASHBOARD PAGE (app.js sets #dashboard display:block after scan) ───── -->
  <!-- Note: app.js shows #dashboard by setting style.display="block" -->
  <!-- We wrap it in a page so it lives in the results tab -->
  <div id="dashboard" style="display:none">
    <!-- This div IS the results view — app.js populates it -->
    <!-- We'll show page-results when dashboard is shown via ui.js -->

    <!-- Scan info bar -->
    <div class="scan-info-bar">
      <span class="scan-id-badge" id="scanId">SCAN-ID: &mdash;</span>
      <span class="scan-file-info" id="scanFile">&mdash;</span>
      <div class="scan-actions">
        <button class="btn-sm btn-outline" id="exportPdfBtn" onclick="exportPDF()">&#128196; PDF</button>
        <button class="btn-sm btn-outline" onclick="exportCSV()">&#128202; CSV</button>
        <button class="btn-sm btn-outline" onclick="newScan()">&#8634; New Scan</button>
      </div>
    </div>

    <!-- Summary cards (app.js populates cTotal, cRecoverable, cPartial, cCritical, cRate) -->
    <div class="summary-cards">
      <div class="summary-card">
        <div class="sc-label">Fragments</div>
        <div class="sc-val" id="cTotal">0</div>
      </div>
      <div class="summary-card sc-green">
        <div class="sc-label">Recoverable</div>
        <div class="sc-val" id="cRecoverable">0</div>
      </div>
      <div class="summary-card sc-amber">
        <div class="sc-label">Partial</div>
        <div class="sc-val" id="cPartial">0</div>
      </div>
      <div class="summary-card sc-red">
        <div class="sc-label">Critical</div>
        <div class="sc-val" id="cCritical">0</div>
      </div>
      <div class="summary-card sc-blue">
        <div class="sc-label">Recovery Rate</div>
        <div class="sc-val" id="cRate">0%</div>
      </div>
      <!-- Gauge (app.js uses #gaugeArc and #gaugePct) -->
      <div class="summary-card sc-gauge">
        <div class="sc-label">Health Score</div>
        <div class="gauge-wrap">
          <svg viewBox="0 0 80 50" class="gauge-svg">
            <path d="M10,40 A30,30 0 0,1 70,40" fill="none" stroke="rgba(255,255,255,0.08)" stroke-width="8" stroke-linecap="round"/>
            <path id="gaugeArc" d="M10,40 A30,30 0 0,1 70,40" fill="none" stroke="url(#gaugeGrad)" stroke-width="8" stroke-linecap="round" stroke-dasharray="94.25" stroke-dashoffset="94.25" style="transition:stroke-dashoffset 1s ease"/>
            <defs>
              <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stop-color="#F87171"/>
                <stop offset="50%" stop-color="#FBBF24"/>
                <stop offset="100%" stop-color="#34D399"/>
              </linearGradient>
            </defs>
          </svg>
          <div class="gauge-pct" id="gaugePct">0%</div>
        </div>
      </div>
    </div>

    <!-- AI Analysis Panel (app.js uses #aiAnalysisPanel, #aiText, etc.) -->
    <div class="ai-analysis-banner" id="aiAnalysisPanel" style="display:none">
      <div class="aab-header">
        <span class="aab-badge">&#129302; Gemini AI Analysis</span>
        <div>
          <span class="gemini-live-badge" id="geminiLiveBadge" style="display:none">LIVE</span>
          <button class="btn-sm btn-outline" id="regenerateAIBtn" onclick="regenerateAI()" style="display:none">&#8635; Regenerate</button>
        </div>
      </div>
      <div class="aab-body" id="aiText">Generating AI summary&hellip;</div>
      <!-- compat aliases -->
      <div id="geminiOutput" style="display:none"></div>
      <div id="geminiText"   style="display:none"></div>
      <div id="aiAnalysisBadge" style="display:none"></div>
    </div>

    <!-- 4 Requirement panels -->
    <div class="req-grid">
      <div class="req-card">
        <div class="req-card-header"><span class="req-badge req-blue">REQ 01</span><span class="req-card-title">Reconstruction Pipeline</span></div>
        <div id="reconPipeline" class="req-card-body"><div class="req-empty">Run a scan to populate</div></div>
      </div>
      <div class="req-card">
        <div class="req-card-header"><span class="req-badge req-amber">REQ 02</span><span class="req-card-title">Integrity Heatmap</span></div>
        <div id="integrityHeatmap" class="req-card-body"><div class="req-empty">Run a scan to populate</div></div>
      </div>
      <div class="req-card">
        <div class="req-card-header"><span class="req-badge req-purple">REQ 03</span><span class="req-card-title">High-Value Assets</span></div>
        <div id="highValueList" class="req-card-body"><div class="req-empty">Run a scan to populate</div></div>
      </div>
      <div class="req-card">
        <div class="req-card-header"><span class="req-badge req-green">REQ 04</span><span class="req-card-title">Decision Support</span></div>
        <div id="decisionSupport" class="req-card-body"><div class="req-empty">Run a scan to populate</div></div>
      </div>
    </div>

    <!-- Categories & Relationships (app.js uses #catList, #relList) -->
    <div class="two-col-row">
      <div class="info-card">
        <div class="info-card-title">&#127891; File Categories</div>
        <div id="catList" class="cat-list"></div>
      </div>
      <div class="info-card">
        <div class="info-card-title">&#128279; Fragment Relationships</div>
        <div id="relList" class="rel-list"></div>
      </div>
    </div>

    <!-- Reconstruction Panel (app.js uses #reconstructionPanel) -->
    <div id="reconstructionPanel" style="display:none" class="recon-panel">
      <div class="info-card-title">&#9883; Reconstructed Files</div>
      <!-- filled by renderReconstructionPanel -->
    </div>

    <!-- Recovery Modal (app.js uses #recoveryModal) -->
    <div id="recoveryModal" class="modal-overlay" style="display:none">
      <div class="modal-box">
        <div class="modal-header">
          <h3 class="modal-title" id="recoveryFragName">Fragment Recovery</h3>
          <button class="modal-close" onclick="document.getElementById(\'recoveryModal\').style.display=\'none\'">&times;</button>
        </div>
        <div class="modal-body">
          <div id="rInfoScore" style="margin-bottom:8px"></div>
          <div id="rInfoStatus" style="margin-bottom:8px"></div>
          <div id="rInfoEntropy" style="margin-bottom:8px"></div>
          <div id="rInfoType" style="margin-bottom:8px"></div>
          <div id="recoveryWarning" style="display:none" class="recovery-warning">&#9888; This fragment has integrity issues. Recovery may be partial.</div>
          <div id="recoveryActions" style="display:none;flex-direction:column;gap:8px">
            <div class="carve-progress-wrap"><div class="carve-progress-bar" id="recoveryProgressBar" style="width:0%"></div></div>
            <div id="recoveryProgressLabel" style="font-size:11px;color:var(--text3)"></div>
            <div id="recoveryLog" class="scan-log" style="max-height:120px"></div>
            <button class="btn-primary" id="recoveryDownloadBtn">&#128229; Download</button>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-sm btn-outline" onclick="document.getElementById(\'recoveryModal\').style.display=\'none\'">Close</button>
          <button class="btn-sm btn-primary-sm" id="activateAIBtn" onclick="recoverFragment(currentRecoveryId)">&#9083; Recover Fragment</button>
        </div>
      </div>
    </div>

    <!-- Fragment table (app.js uses #fragTableBody — note: it uses fragTableBody not fragmentTableBody) -->
    <div class="frag-table-wrap" style="margin-top:20px">
      <div class="frag-table-header">
        <h3 class="frag-table-title">&#128202; Fragment Index</h3>
        <div class="frag-search-wrap">
          <span>&#128269;</span>
          <input class="frag-search" id="fragSearch" placeholder="Filter fragments..." oninput="filterFragments(this.value)"/>
        </div>
      </div>
      <div class="table-scroll">
        <table class="frag-table">
          <thead>
            <tr>
              <th>#</th><th>Name</th><th>Type</th><th>Size</th>
              <th>Integrity</th><th>Priority</th><th>SHA-256</th><th>Actions</th>
            </tr>
          </thead>
          <tbody id="fragTableBody"></tbody>
        </table>
      </div>
    </div>
  </div><!-- /#dashboard -->

  <!-- ── AI COACH PAGE ──────────────────────────────────────────────────────── -->
  <section class="page" id="page-ai">
    <div class="ai-coach-layout">
      <div class="ai-coach-sidebar">
        <div class="ai-orb-wrap">
          <div class="ai-orb-glow"></div>
          <div class="ai-orb" id="aiOrb">
            <span class="ai-orb-icon">&#129302;</span>
          </div>
          <div class="ai-orb-rings">
            <div class="ai-orb-ring ai-orb-ring-1"></div>
            <div class="ai-orb-ring ai-orb-ring-2"></div>
            <div class="ai-orb-ring ai-orb-ring-3"></div>
          </div>
        </div>
        <div class="ai-coach-name">Gemini Forensic AI</div>
        <div class="ai-coach-status" id="aiCoachStatus">Ready to assist</div>
        <div class="ai-quick-prompts">
          <div class="aqp-label">Quick questions</div>
          <button class="aqp-btn" onclick="sendQuickPrompt(\'What files are most critical to recover?\')">Most critical files?</button>
          <button class="aqp-btn" onclick="sendQuickPrompt(\'Explain the integrity score system\')">Integrity scoring?</button>
          <button class="aqp-btn" onclick="sendQuickPrompt(\'What is file carving and how does it work?\')">File carving?</button>
          <button class="aqp-btn" onclick="sendQuickPrompt(\'How can I maximize data recovery?\')">Maximize recovery?</button>
          <button class="aqp-btn" onclick="sendQuickPrompt(\'What does a high entropy score mean?\')">High entropy score?</button>
        </div>
      </div>
      <div class="ai-chat-panel">
        <div class="ai-chat-messages" id="aiChatMessages"></div>
        <div class="ai-typing-indicator hidden" id="aiTyping">
          <div class="ai-typing-dot"></div>
          <div class="ai-typing-dot"></div>
          <div class="ai-typing-dot"></div>
        </div>
        <form class="ai-chat-input-row" id="aiChatForm" onsubmit="sendAIChat(event)">
          <input class="ai-chat-input" id="aiChatInput" placeholder="Ask anything about data recovery..." autocomplete="off"/>
          <button type="submit" class="ai-send-btn" id="aiSendBtn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
        </form>
      </div>
    </div>
  </section>

  <!-- ── DELETED RECOVERY PAGE ────────────────────────────────────────────── -->
  <section class="page" id="page-deleted">
    <!-- app.js toggles #deletedSection via openDeletedRecovery() -->
    <div id="deletedSection">
      <div class="page-header">
        <div>
          <h2 class="page-title">&#128465; Deleted File Recovery</h2>
          <p class="page-sub">Recover files from Recycle Bin, free disk space, and system caches</p>
        </div>
      </div>
      <div class="del-tabs">
        <button class="del-tab active" id="delTab-recycle"   onclick="switchDelTab(\'recycle\', this)">&#128465; Recycle Bin</button>
        <button class="del-tab"        id="delTab-carve"     onclick="switchDelTab(\'carve\', this)">&#128189; Drive Scanner</button>
        <button class="del-tab"        id="delTab-artifacts" onclick="switchDelTab(\'artifacts\', this)">&#128193; Temp Artifacts</button>
      </div>
      <div class="del-content" id="delContent-recycle">
        <div class="del-toolbar">
          <button class="btn-primary" id="scanRecycleBtn" onclick="scanRecycleBin()">&#128269; Scan Recycle Bin</button>
          <span class="del-info" id="recycleInfo">Click to scan deleted files in Recycle Bin</span>
        </div>
        <div id="recycleResults"></div>
      </div>
      <div class="del-content" id="delContent-carve" style="display:none">
        <div class="admin-notice" id="adminNotice">
          <div class="admin-notice-icon">&#128737;</div>
          <div>
            <strong>Administrator Required for Raw Disk Scan</strong>
            <p>Restart the server as Administrator: right-click terminal &rarr; Run as Administrator &rarr; python app.py</p>
          </div>
        </div>
        <div class="del-toolbar">
          <select id="driveSelect" class="del-select"><option value="C">C:\\ &mdash; Loading&hellip;</option></select>
          <button class="btn-primary" id="startCarveBtn" onclick="startDriveCarve()">&#128300; Start Deep Scan</button>
        </div>
        <div id="carveProgress" style="display:none">
          <div class="carve-progress-wrap"><div class="carve-progress-bar" id="carveProgressBar" style="width:0%"></div></div>
          <div class="carve-stats" id="carveStats">Initializing&hellip;</div>
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
  </section>

</main><!-- /.app-main -->

<!-- ══ AI CONFIG MODAL ═══════════════════════════════════════════════════════ -->
<div id="aiConfigModal" class="modal-overlay" style="display:none">
  <div class="modal-box">
    <div class="modal-header">
      <h3 class="modal-title">&#129302; Configure Gemini AI</h3>
      <button class="modal-close" onclick="closeAIConfig()">&times;</button>
    </div>
    <div class="modal-body">
      <p style="color:var(--text2);font-size:13px;margin-bottom:16px">Enter your Google AI Studio API key to enable AI-powered forensic analysis.</p>
      <!-- app.js uses #geminiKeyInput as the primary key input -->
      <input class="modal-input" id="geminiKeyInput" type="password" placeholder="AQ.Ab8RN6..."/>
      <!-- also keep aiKeyInput alias for ui.js compat -->
      <input id="aiKeyInput" type="hidden"/>
      <div style="display:flex;align-items:center;gap:8px;margin-top:12px">
        <button class="btn-sm btn-outline" id="keyToggleBtn" onclick="toggleKeyVisibility()">Show</button>
      </div>
      <div id="aiConfigStatus" style="font-size:12px;margin-top:10px;color:var(--text3)"></div>
    </div>
    <div class="modal-footer">
      <button class="btn-sm btn-outline" onclick="closeAIConfig()">Cancel</button>
      <button class="btn-sm btn-primary-sm" onclick="saveAIKey()">Save &amp; Activate</button>
    </div>
  </div>
</div>

<!-- Toast -->
<div id="recoverToast" class="toast hidden"></div>

<script src="app.js"></script>
<script src="ui.js"></script>
</body>
</html>'''

with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print("index.html v2 written")
