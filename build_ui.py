"""
build_ui.py — writes all new frontend files for the RecoverAI redesign.
Run: python build_ui.py
"""
import os

# ── 1. index.html ─────────────────────────────────────────────────────────────
HTML = '''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>RecoverAI — Forensic Data Recovery Platform</title>
  <meta name="description" content="AI-powered forensic data recovery: reconstruct, classify and restore deleted or corrupted files with Gemini AI assistance."/>
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
    <!-- Step 1 -->
    <div class="ob-step active" id="ob-step-1">
      <div class="ob-logo-ring">
        <div class="ob-logo-orb"></div>
        <span class="ob-logo-icon">&#x26E1;</span>
      </div>
      <h1 class="ob-title">Welcome to<br/><span class="grad-text">RecoverAI</span></h1>
      <p class="ob-body">Your AI-powered forensic companion.<br/>We find, reconstruct and restore what others miss.</p>
      <button class="ob-btn" onclick="obNext(2)">Get Started &rarr;</button>
    </div>

    <!-- Step 2 -->
    <div class="ob-step" id="ob-step-2">
      <h2 class="ob-title" style="font-size:1.6rem">What are you trying to recover?</h2>
      <div class="ob-cards">
        <div class="ob-option-card" onclick="selectGoal(this,'deleted')">
          <div class="ob-opt-icon">&#128465;</div>
          <div class="ob-opt-label">Deleted Files</div>
          <div class="ob-opt-sub">Recycle Bin &amp; free space</div>
        </div>
        <div class="ob-option-card" onclick="selectGoal(this,'corrupted')">
          <div class="ob-opt-icon">&#128190;</div>
          <div class="ob-opt-label">Corrupted Storage</div>
          <div class="ob-opt-sub">Disk images &amp; fragments</div>
        </div>
        <div class="ob-option-card" onclick="selectGoal(this,'forensic')">
          <div class="ob-opt-icon">&#128270;</div>
          <div class="ob-opt-label">Full Forensic Analysis</div>
          <div class="ob-opt-sub">Deep AI-assisted investigation</div>
        </div>
      </div>
      <button class="ob-btn" onclick="obNext(3)">Continue &rarr;</button>
      <button class="ob-skip" onclick="obNext(3)">Skip</button>
    </div>

    <!-- Step 3 -->
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

    <!-- Progress dots -->
    <div class="ob-dots">
      <span class="ob-dot active" id="ob-dot-1"></span>
      <span class="ob-dot" id="ob-dot-2"></span>
      <span class="ob-dot" id="ob-dot-3"></span>
    </div>
  </div>
</div>

<!-- ══ SCAN PROGRESS OVERLAY ════════════════════════════════════════════════ -->
<div id="scanProgressOverlay" class="scan-overlay hidden">
  <div class="scan-overlay-inner">
    <div class="scan-ring-wrap">
      <svg class="scan-ring-svg" viewBox="0 0 120 120">
        <circle class="scan-ring-bg"   cx="60" cy="60" r="52"/>
        <circle class="scan-ring-fill" cx="60" cy="60" r="52" id="scanRingFill"/>
      </svg>
      <div class="scan-ring-center">
        <div class="scan-pct" id="progressPct">0%</div>
        <div class="scan-lbl">Analyzing</div>
      </div>
    </div>
    <div class="scan-log-box">
      <div class="scan-log-header">
        <span class="scan-log-dot"></span> Live forensic log
      </div>
      <div id="logContainer" class="scan-log"></div>
    </div>
    <!-- hidden progress bar kept for JS compatibility -->
    <progress id="progressBar" value="0" max="100" style="display:none"></progress>
    <div id="scanProgress" style="display:none"></div>
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
    <div class="ai-status-pill" id="aiStatusPill" onclick="openAIConfig()" title="Click to configure Gemini AI">
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
  <section class="page active" id="page-home">

    <!-- Animated hero banner -->
    <div class="hero-banner">
      <div class="hero-orbs">
        <div class="hero-orb hero-orb-1"></div>
        <div class="hero-orb hero-orb-2"></div>
        <div class="hero-orb hero-orb-3"></div>
      </div>
      <div class="hero-content">
        <div class="hero-chip">&#129302; Powered by Gemini AI</div>
        <h1 class="hero-headline">Recover What<br/><span class="grad-text">Others Miss</span></h1>
        <p class="hero-sub">Intelligent fragment reconstruction, integrity scoring &amp;<br/>AI-guided forensic investigation — all in one platform.</p>
      </div>
    </div>

    <!-- Stats row (count-up, shown after scan) -->
    <div class="home-stats-row" id="homeStatsRow" style="display:none">
      <div class="hstat-card">
        <div class="hstat-icon">&#128202;</div>
        <div class="hstat-val" id="fragmentCount">0</div>
        <div class="hstat-lbl">Fragments Found</div>
      </div>
      <div class="hstat-card">
        <div class="hstat-icon" style="color:var(--green)">&#9989;</div>
        <div class="hstat-val" style="color:var(--green)" id="recoverable">0</div>
        <div class="hstat-lbl">Recoverable</div>
      </div>
      <div class="hstat-card">
        <div class="hstat-icon" style="color:var(--amber)">&#9888;</div>
        <div class="hstat-val" style="color:var(--amber)" id="corrupt">0</div>
        <div class="hstat-lbl">Partial / Corrupt</div>
      </div>
      <div class="hstat-card">
        <div class="hstat-icon" style="color:var(--blue)">&#128190;</div>
        <div class="hstat-val" style="color:var(--blue)" id="totalSize">0 KB</div>
        <div class="hstat-lbl">Total Data</div>
      </div>
      <div class="hstat-card">
        <div class="hstat-icon" style="color:var(--purple)">&#127381;</div>
        <div class="hstat-val" style="color:var(--purple)" id="recoveryRate">0%</div>
        <div class="hstat-lbl">Recovery Rate</div>
      </div>
    </div>

    <!-- Upload zone -->
    <div class="upload-section">
      <input type="file" id="fileInput" hidden accept="*/*"/>
      <input type="file" id="folderInput" hidden webkitdirectory multiple/>

      <div class="upload-zone" id="uploadZone">
        <div class="upload-anim">
          <div class="upload-ring"></div>
          <div class="upload-icon-wrap">
            <span class="upload-icon" id="uploadIcon">&#128194;</span>
          </div>
        </div>
        <div class="upload-text">
          <div class="upload-title" id="uploadTitle">Drop your storage file here</div>
          <div class="upload-sub" id="uploadSub">Disk images, folders, corrupted drives &mdash; any format</div>
        </div>
        <div class="upload-actions">
          <button class="btn-upload" id="heroUploadBtn" onclick="document.getElementById(\'fileInput\').click()">
            &#128269; Analyze File
          </button>
          <button class="btn-upload-sec" id="heroFolderBtn" onclick="document.getElementById(\'folderInput\').click()">
            &#128193; Analyze Folder
          </button>
          <button class="btn-upload-ghost" id="demoBtn" onclick="loadDemo()">
            &#9654; Demo Scan
          </button>
          <button class="btn-upload-danger" id="deletedBtn" onclick="showPage(\'deleted\')">
            &#128465; Recover Deleted
          </button>
        </div>
      </div>
    </div>

    <!-- Feature cards row -->
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
        <div class="feature-card-body">Real-time AI explanations, coping strategies and action recommendations.</div>
      </div>
      <div class="feature-card" style="--fc-delay:0.3s">
        <div class="feature-card-icon">&#128465;</div>
        <div class="feature-card-title">Deleted Recovery</div>
        <div class="feature-card-body">Scan Recycle Bin, free disk sectors and temp caches for lost data.</div>
      </div>
    </div>

  </section>

  <!-- ── RESULTS PAGE ────────────────────────────────────────────────────────── -->
  <section class="page" id="page-results">
    <div id="reportSection">
      <div class="page-header">
        <div>
          <h2 class="page-title">Scan Results</h2>
          <p class="page-sub">Full forensic report &mdash; fragments, integrity &amp; AI analysis</p>
        </div>
        <div class="page-header-actions">
          <button class="btn-sm btn-outline" onclick="exportPDF()">&#128196; Export PDF</button>
          <button class="btn-sm btn-outline" onclick="exportCSV()">&#128202; Export CSV</button>
        </div>
      </div>

      <!-- 4 Requirement panels -->
      <div class="req-grid">
        <div class="req-card">
          <div class="req-card-header">
            <span class="req-badge req-blue">REQ 01</span>
            <span class="req-card-title">Reconstruction Pipeline</span>
          </div>
          <div id="reconPipeline" class="req-card-body"><div class="req-empty">Run a scan to populate</div></div>
        </div>
        <div class="req-card">
          <div class="req-card-header">
            <span class="req-badge req-amber">REQ 02</span>
            <span class="req-card-title">Integrity Heatmap</span>
          </div>
          <div id="integrityHeatmap" class="req-card-body"><div class="req-empty">Run a scan to populate</div></div>
        </div>
        <div class="req-card">
          <div class="req-card-header">
            <span class="req-badge req-purple">REQ 03</span>
            <span class="req-card-title">High-Value Assets</span>
          </div>
          <div id="highValueList" class="req-card-body"><div class="req-empty">Run a scan to populate</div></div>
        </div>
        <div class="req-card">
          <div class="req-card-header">
            <span class="req-badge req-green">REQ 04</span>
            <span class="req-card-title">Decision Support</span>
          </div>
          <div id="decisionSupport" class="req-card-body"><div class="req-empty">Run a scan to populate</div></div>
        </div>
      </div>

      <!-- Fragment Table -->
      <div class="frag-table-wrap">
        <div class="frag-table-header">
          <h3 class="frag-table-title">Fragment Index</h3>
          <div class="frag-search-wrap">
            <span>&#128269;</span>
            <input class="frag-search" id="fragSearch" placeholder="Filter fragments..." oninput="filterFragments(this.value)"/>
          </div>
        </div>
        <div class="table-scroll">
          <table class="frag-table">
            <thead>
              <tr>
                <th>ID</th><th>Name</th><th>Type</th><th>Size</th>
                <th>Integrity</th><th>Priority</th><th>SHA-256</th><th>Actions</th>
              </tr>
            </thead>
            <tbody id="fragmentTableBody"></tbody>
          </table>
        </div>
      </div>
    </div>
  </section>

  <!-- ── AI COACH PAGE ──────────────────────────────────────────────────────── -->
  <section class="page" id="page-ai">
    <div class="ai-coach-layout">

      <!-- Left: breathing orb + status -->
      <div class="ai-coach-sidebar">
        <div class="ai-orb-wrap" id="aiOrbWrap">
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

        <!-- Quick prompts -->
        <div class="ai-quick-prompts">
          <div class="aqp-label">Quick questions</div>
          <button class="aqp-btn" onclick="sendQuickPrompt(\'What files are most critical to recover?\')">Most critical files?</button>
          <button class="aqp-btn" onclick="sendQuickPrompt(\'Explain the integrity score system\')">Integrity scoring?</button>
          <button class="aqp-btn" onclick="sendQuickPrompt(\'What is file carving and how does it work?\')">File carving?</button>
          <button class="aqp-btn" onclick="sendQuickPrompt(\'How can I maximize data recovery?\')">Maximize recovery?</button>
        </div>
      </div>

      <!-- Right: chat -->
      <div class="ai-chat-panel">
        <div class="ai-chat-messages" id="aiChatMessages">
          <!-- Welcome message injected by JS -->
        </div>
        <div class="ai-typing-indicator hidden" id="aiTyping">
          <div class="ai-typing-dot"></div>
          <div class="ai-typing-dot"></div>
          <div class="ai-typing-dot"></div>
        </div>
        <form class="ai-chat-input-row" id="aiChatForm" onsubmit="sendAIChat(event)">
          <input class="ai-chat-input" id="aiChatInput"
            placeholder="Ask anything about data recovery..." autocomplete="off"/>
          <button type="submit" class="ai-send-btn" id="aiSendBtn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
        </form>
      </div>
    </div>
  </section>

  <!-- ── DELETED RECOVERY PAGE ────────────────────────────────────────────── -->
  <section class="page" id="page-deleted">
    <div id="deletedSection">
      <div class="page-header">
        <div>
          <h2 class="page-title">&#128465; Deleted File Recovery</h2>
          <p class="page-sub">Recover files from Recycle Bin, free disk space, and system caches</p>
        </div>
      </div>

      <div class="del-tabs">
        <button class="del-tab active" id="delTab-recycle" onclick="switchDelTab(\'recycle\', this)">&#128465; Recycle Bin</button>
        <button class="del-tab" id="delTab-carve"   onclick="switchDelTab(\'carve\', this)">&#128189; Drive Scanner</button>
        <button class="del-tab" id="delTab-artifacts" onclick="switchDelTab(\'artifacts\', this)">&#128193; Temp Artifacts</button>
      </div>

      <!-- Recycle Bin -->
      <div class="del-content" id="delContent-recycle">
        <div class="del-toolbar">
          <button class="btn-primary" id="scanRecycleBtn" onclick="scanRecycleBin()">&#128269; Scan Recycle Bin</button>
          <span class="del-info" id="recycleInfo">Click to scan deleted files still in your Recycle Bin</span>
        </div>
        <div id="recycleResults"></div>
      </div>

      <!-- Drive Carver -->
      <div class="del-content" id="delContent-carve" style="display:none">
        <div class="admin-notice" id="adminNotice">
          <div class="admin-notice-icon">&#128737;</div>
          <div>
            <strong>Administrator Required for Raw Disk Scan</strong>
            <p>To scan free disk space, restart the server as Administrator:</p>
            <code>Right-click &rarr; Run as Administrator &rarr; python app.py</code>
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

      <!-- Temp Artifacts -->
      <div class="del-content" id="delContent-artifacts" style="display:none">
        <div class="del-toolbar">
          <button class="btn-primary" id="scanArtifactsBtn" onclick="scanArtifacts()">&#128193; Scan Temp &amp; Cache</button>
          <span class="del-info">Finds recoverable files in Temp folders, Recent Files and browser caches</span>
        </div>
        <div id="artifactsResults"></div>
      </div>
    </div>
  </section>

</main>

<!-- ══ AI CONFIG MODAL ═══════════════════════════════════════════════════════ -->
<div id="aiConfigModal" class="modal-overlay" style="display:none">
  <div class="modal-box">
    <div class="modal-header">
      <h3 class="modal-title">&#129302; Configure Gemini AI</h3>
      <button class="modal-close" onclick="closeAIConfig()">&times;</button>
    </div>
    <div class="modal-body">
      <p style="color:var(--text2);font-size:13px;margin-bottom:16px">Enter your Google AI Studio API key to enable AI-powered forensic analysis.</p>
      <input class="modal-input" id="aiKeyInput" type="password" placeholder="AQ.Ab8RN6..."/>
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

os.makedirs("frontend", exist_ok=True)
with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print("index.html written")

# ── 2. style.css ──────────────────────────────────────────────────────────────
CSS = '''/* ═══════════════════════════════════════════════════════════════════════════
   RecoverAI — Complete Design System v2
   ═══════════════════════════════════════════════════════════════════════════ */

/* ── Variables ─────────────────────────────────────────────────────────────── */
:root {
  --font:         \'Plus Jakarta Sans\', sans-serif;
  --font-display: \'Sora\', sans-serif;
  --mono:         \'JetBrains Mono\', monospace;
  --radius:        14px;
  --radius-sm:     8px;
  --radius-lg:     20px;
}

[data-theme="dark"] {
  --bg:        #090E1A;
  --bg2:       #0F1629;
  --surface:   #141D35;
  --surface2:  #1C2845;
  --surface3:  #243058;
  --border:    rgba(148,163,184,0.1);
  --border2:   rgba(148,163,184,0.06);
  --text:      #E2E8F0;
  --text2:     #94A3B8;
  --text3:     #64748B;
  --blue:      #60A5FA;
  --blue-deep: #3B82F6;
  --green:     #34D399;
  --amber:     #FBBF24;
  --red:       #F87171;
  --purple:    #C084FC;
  --cyan:      #67E8F9;
  --shadow:    0 4px 24px rgba(0,0,0,0.5);
  --shadow-lg: 0 12px 48px rgba(0,0,0,0.6);
  --glow-blue: 0 0 30px rgba(96,165,250,0.2);
  --glow-green:0 0 30px rgba(52,211,153,0.2);
}

[data-theme="light"] {
  --bg:        #EEF2FF;
  --bg2:       #E0E7FF;
  --surface:   #FFFFFF;
  --surface2:  #F8FAFF;
  --surface3:  #EEF2FF;
  --border:    rgba(99,102,241,0.12);
  --border2:   rgba(99,102,241,0.06);
  --text:      #1E293B;
  --text2:     #475569;
  --text3:     #94A3B8;
  --blue:      #2563EB;
  --blue-deep: #1D4ED8;
  --green:     #059669;
  --amber:     #D97706;
  --red:       #DC2626;
  --purple:    #7C3AED;
  --cyan:      #0891B2;
  --shadow:    0 4px 24px rgba(99,102,241,0.12);
  --shadow-lg: 0 12px 48px rgba(99,102,241,0.18);
  --glow-blue: 0 0 30px rgba(37,99,235,0.15);
  --glow-green:0 0 30px rgba(5,150,105,0.12);
}

/* ── Reset ────────────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  font-family: var(--font);
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  min-height: 100vh;
  overflow-x: hidden;
  transition: background 0.4s ease, color 0.4s ease;
}

/* ── Gradient text ─────────────────────────────────────────────────────────── */
.grad-text {
  background: linear-gradient(135deg, var(--blue) 0%, var(--purple) 50%, var(--cyan) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ── Scrollbar ─────────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--surface3); border-radius: 3px; }

/* ═══════════════════════════════════════════════════════════════════════════
   ONBOARDING
   ═══════════════════════════════════════════════════════════════════════════ */
.ob-overlay {
  position: fixed; inset: 0; z-index: 1000;
  display: flex; align-items: center; justify-content: center;
  background: radial-gradient(ellipse at 50% 30%, rgba(96,165,250,0.15) 0%, var(--bg) 70%);
  backdrop-filter: blur(4px);
  transition: opacity 0.5s ease;
}
.ob-overlay.hidden { opacity: 0; pointer-events: none; }

.ob-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 24px;
  padding: 48px 40px;
  width: min(520px, 94vw);
  text-align: center;
  box-shadow: var(--shadow-lg), 0 0 80px rgba(96,165,250,0.08);
  position: relative;
  overflow: hidden;
}
.ob-card::before {
  content: \'\';
  position: absolute; top: 0; left: 0; right: 0; height: 3px;
  background: linear-gradient(90deg, var(--blue), var(--purple), var(--cyan));
}

.ob-step { display: none; animation: obFadeIn 0.5s ease; }
.ob-step.active { display: block; }

@keyframes obFadeIn {
  from { opacity:0; transform: translateY(16px); }
  to   { opacity:1; transform: translateY(0); }
}

.ob-logo-ring {
  width: 100px; height: 100px; margin: 0 auto 24px;
  border-radius: 50%; position: relative;
  background: linear-gradient(135deg, rgba(96,165,250,0.15), rgba(192,132,252,0.15));
  border: 1px solid var(--border);
  display: flex; align-items: center; justify-content: center;
  animation: breathe 4s ease-in-out infinite;
}
.ob-logo-orb {
  position: absolute; inset: -8px; border-radius: 50%;
  background: conic-gradient(from 0deg, var(--blue), var(--purple), var(--cyan), var(--blue));
  opacity: 0.3; animation: spin 8s linear infinite;
}
.ob-logo-icon { font-size: 36px; position: relative; z-index: 1; }

@keyframes breathe {
  0%,100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(96,165,250,0); }
  50%      { transform: scale(1.04); box-shadow: 0 0 0 12px rgba(96,165,250,0.08); }
}
@keyframes spin { to { transform: rotate(360deg); } }

.ob-title { font-family: var(--font-display); font-size: 2rem; font-weight: 700; color: var(--text); line-height: 1.2; margin-bottom: 12px; }
.ob-body  { font-size: 14px; color: var(--text2); line-height: 1.7; margin-bottom: 28px; }

.ob-btn {
  display: inline-block; padding: 13px 36px;
  background: linear-gradient(135deg, var(--blue-deep), var(--purple));
  color: #fff; border: none; border-radius: 100px;
  font-family: var(--font); font-size: 15px; font-weight: 700;
  cursor: pointer; transition: all 0.25s;
  box-shadow: 0 6px 20px rgba(96,165,250,0.3);
}
.ob-btn:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(96,165,250,0.4); }
.ob-btn:active { transform: translateY(0) scale(0.98); }

.ob-skip {
  display: block; margin: 10px auto 0;
  background: none; border: none; color: var(--text3);
  font-family: var(--font); font-size: 13px; cursor: pointer;
  transition: color 0.2s;
}
.ob-skip:hover { color: var(--text2); }

.ob-cards {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
  margin-bottom: 24px;
}
.ob-option-card {
  padding: 20px 12px; border-radius: 14px; border: 2px solid var(--border);
  cursor: pointer; transition: all 0.25s;
  background: var(--bg2);
}
.ob-option-card:hover { border-color: var(--blue); background: rgba(96,165,250,0.08); }
.ob-option-card.selected { border-color: var(--blue-deep); background: rgba(96,165,250,0.12); }
.ob-opt-icon  { font-size: 26px; margin-bottom: 8px; }
.ob-opt-label { font-size: 12px; font-weight: 700; color: var(--text); margin-bottom: 4px; }
.ob-opt-sub   { font-size: 11px; color: var(--text3); }

.ob-ready-ring {
  width: 90px; height: 90px; margin: 0 auto 24px;
  border-radius: 50%;
}
.ob-check-svg { width: 90px; height: 90px; }
.ob-check-circle {
  fill: none; stroke: var(--green); stroke-width: 4;
  stroke-dasharray: 226; stroke-dashoffset: 226;
  animation: drawCircle 0.8s ease forwards 0.2s;
}
.ob-check-mark {
  fill: none; stroke: var(--green); stroke-width: 5;
  stroke-linecap: round; stroke-linejoin: round;
  stroke-dasharray: 60; stroke-dashoffset: 60;
  animation: drawCheck 0.5s ease forwards 0.9s;
}
@keyframes drawCircle { to { stroke-dashoffset: 0; } }
@keyframes drawCheck  { to { stroke-dashoffset: 0; } }

.ob-dots { display: flex; gap: 8px; justify-content: center; margin-top: 28px; }
.ob-dot  { width: 8px; height: 8px; border-radius: 50%; background: var(--border); transition: all 0.3s; }
.ob-dot.active { width: 24px; border-radius: 4px; background: var(--blue); }

/* ═══════════════════════════════════════════════════════════════════════════
   SCAN OVERLAY
   ═══════════════════════════════════════════════════════════════════════════ */
.scan-overlay {
  position: fixed; inset: 0; z-index: 900;
  background: rgba(9,14,26,0.95);
  backdrop-filter: blur(12px);
  display: flex; align-items: center; justify-content: center;
  transition: opacity 0.4s ease;
}
.scan-overlay.hidden { opacity: 0; pointer-events: none; }

.scan-overlay-inner {
  display: flex; flex-direction: column; align-items: center; gap: 32px;
  padding: 40px; max-width: 600px; width: 100%;
}

.scan-ring-wrap { position: relative; width: 160px; height: 160px; }
.scan-ring-svg  { width: 160px; height: 160px; transform: rotate(-90deg); }
.scan-ring-bg   { fill: none; stroke: rgba(255,255,255,0.06); stroke-width: 8; }
.scan-ring-fill {
  fill: none; stroke: url(#scanGrad); stroke-width: 8;
  stroke-linecap: round;
  stroke-dasharray: 326.7;
  stroke-dashoffset: 326.7;
  transition: stroke-dashoffset 0.5s ease;
  filter: drop-shadow(0 0 8px rgba(96,165,250,0.6));
}
.scan-ring-center {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
}
.scan-pct { font-family: var(--font-display); font-size: 28px; font-weight: 800; color: var(--blue); }
.scan-lbl { font-size: 11px; color: var(--text3); letter-spacing: 1px; text-transform: uppercase; }

.scan-log-box {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 16px; width: 100%; max-width: 520px;
}
.scan-log-header {
  display: flex; align-items: center; gap: 8px;
  font-size: 11px; font-weight: 700; letter-spacing: 1px; text-transform: uppercase;
  color: var(--text3); margin-bottom: 10px;
}
.scan-log-dot {
  width: 8px; height: 8px; border-radius: 50%; background: var(--green);
  animation: blink 1s ease-in-out infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }
.scan-log {
  font-family: var(--mono); font-size: 11px; color: var(--text3);
  max-height: 180px; overflow-y: auto; line-height: 1.8;
}

/* ═══════════════════════════════════════════════════════════════════════════
   TOP NAVIGATION
   ═══════════════════════════════════════════════════════════════════════════ */
.top-nav {
  position: sticky; top: 0; z-index: 100;
  display: flex; align-items: center; gap: 20px;
  padding: 0 28px; height: 64px;
  background: rgba(9,14,26,0.8);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
  transition: background 0.4s ease;
}
[data-theme="light"] .top-nav { background: rgba(238,242,255,0.8); }

.nav-logo {
  display: flex; align-items: center; gap: 10px;
  cursor: pointer; text-decoration: none;
  flex-shrink: 0;
}
.nav-logo-icon { font-size: 22px; }
.nav-logo-text {
  font-family: var(--font-display); font-size: 18px; font-weight: 800; color: var(--text);
}
.nav-logo-accent { color: var(--blue); }
.nav-logo-badge {
  font-size: 9px; font-weight: 700; letter-spacing: 1.5px;
  padding: 2px 8px; border-radius: 100px;
  border: 1px solid rgba(96,165,250,0.35);
  color: var(--blue); background: rgba(96,165,250,0.08);
}

.nav-tabs { display: flex; align-items: center; gap: 4px; margin: 0 auto; }
.nav-tab {
  padding: 8px 18px; border-radius: 100px; border: none;
  background: transparent; color: var(--text3);
  font-family: var(--font); font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
  white-space: nowrap;
}
.nav-tab:hover  { color: var(--text); background: var(--border); }
.nav-tab.active { color: var(--blue); background: rgba(96,165,250,0.12); }

.nav-right { display: flex; align-items: center; gap: 12px; flex-shrink: 0; }

.ai-status-pill {
  display: flex; align-items: center; gap: 7px;
  padding: 6px 14px; border-radius: 100px;
  border: 1px solid var(--border); background: var(--surface);
  font-size: 12px; font-weight: 600; cursor: pointer;
  color: var(--text2); transition: all 0.2s;
}
.ai-status-pill:hover { border-color: var(--blue); color: var(--text); }
.ai-status-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--text3); transition: background 0.3s;
}
.ai-status-dot.active { background: var(--green); box-shadow: 0 0 8px rgba(52,211,153,0.5); }
.ai-status-dot.error  { background: var(--red); }

.theme-toggle {
  width: 36px; height: 36px; border-radius: 10px; border: 1px solid var(--border);
  background: var(--surface); color: var(--text2);
  font-size: 16px; cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; justify-content: center;
}
.theme-toggle:hover { border-color: var(--blue); color: var(--blue); }

/* ═══════════════════════════════════════════════════════════════════════════
   PAGES
   ═══════════════════════════════════════════════════════════════════════════ */
.app-main { padding: 32px 28px 80px; max-width: 1400px; margin: 0 auto; }

.page {
  display: none;
  animation: pageFadeIn 0.4s ease;
}
.page.active { display: block; }
@keyframes pageFadeIn {
  from { opacity:0; transform: translateY(12px); }
  to   { opacity:1; transform: translateY(0); }
}

.page-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 28px; gap: 16px; flex-wrap: wrap;
}
.page-title { font-family: var(--font-display); font-size: 24px; font-weight: 700; color: var(--text); }
.page-sub   { font-size: 13px; color: var(--text3); margin-top: 4px; }
.page-header-actions { display: flex; gap: 10px; align-items: center; }

/* ═══════════════════════════════════════════════════════════════════════════
   HOME PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
.hero-banner {
  position: relative; overflow: hidden;
  border-radius: 24px; margin-bottom: 28px;
  padding: 64px 48px;
  background: linear-gradient(135deg, var(--surface) 0%, var(--surface2) 100%);
  border: 1px solid var(--border);
  min-height: 260px; display: flex; align-items: center;
}
.hero-orbs { position: absolute; inset: 0; pointer-events: none; overflow: hidden; }
.hero-orb  {
  position: absolute; border-radius: 50%;
  filter: blur(60px); opacity: 0.4;
  animation: floatOrb linear infinite;
}
.hero-orb-1 { width:300px; height:300px; background:var(--blue);   top:-80px;  left:-60px;  animation-duration:20s; }
.hero-orb-2 { width:250px; height:250px; background:var(--purple); top:-40px;  right:-40px; animation-duration:25s; animation-delay:-8s; }
.hero-orb-3 { width:200px; height:200px; background:var(--cyan);   bottom:-60px; left:40%;  animation-duration:18s; animation-delay:-4s; }
@keyframes floatOrb {
  0%,100% { transform: translate(0,0) scale(1); }
  33%      { transform: translate(20px,-15px) scale(1.05); }
  66%      { transform: translate(-10px,20px) scale(0.95); }
}

.hero-content { position: relative; z-index: 1; }
.hero-chip {
  display: inline-flex; align-items: center; gap: 7px;
  padding: 6px 16px; border-radius: 100px;
  background: rgba(96,165,250,0.12); border: 1px solid rgba(96,165,250,0.25);
  color: var(--blue); font-size: 12px; font-weight: 700; margin-bottom: 20px;
}
.hero-headline {
  font-family: var(--font-display); font-size: 3rem; font-weight: 800;
  color: var(--text); line-height: 1.1; margin-bottom: 16px;
}
.hero-sub { font-size: 15px; color: var(--text2); line-height: 1.7; max-width: 480px; }

/* Home stats */
.home-stats-row {
  display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px;
  margin-bottom: 28px;
}
.hstat-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 20px 16px; text-align: center;
  transition: transform 0.2s, box-shadow 0.2s;
  animation: statSlideIn 0.5s ease forwards;
}
.hstat-card:hover { transform: translateY(-3px); box-shadow: var(--shadow); }
.hstat-icon { font-size: 22px; margin-bottom: 8px; }
.hstat-val  { font-family: var(--font-display); font-size: 26px; font-weight: 800; color: var(--text); }
.hstat-lbl  { font-size: 11px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }
@keyframes statSlideIn { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }

/* Upload zone */
.upload-section { margin-bottom: 28px; }
.upload-zone {
  background: var(--surface); border: 2px dashed var(--border);
  border-radius: 20px; padding: 40px 32px;
  text-align: center; transition: all 0.3s;
  cursor: pointer; position: relative; overflow: hidden;
}
.upload-zone:hover, .upload-zone.drag-over {
  border-color: var(--blue); background: rgba(96,165,250,0.04);
}
.upload-zone.drag-over { transform: scale(1.01); }

.upload-anim {
  position: relative; width: 80px; height: 80px; margin: 0 auto 20px;
  display: flex; align-items: center; justify-content: center;
}
.upload-ring {
  position: absolute; inset: -6px; border-radius: 50%;
  border: 2px solid transparent;
  border-top-color: var(--blue); border-right-color: var(--purple);
  animation: spinRing 3s linear infinite;
}
.upload-ring::after {
  content: \'\'; position: absolute; inset: 4px; border-radius: 50%;
  border: 1px dashed rgba(96,165,250,0.2);
}
@keyframes spinRing { to { transform: rotate(360deg); } }
.upload-icon-wrap {
  width: 72px; height: 72px; border-radius: 50%;
  background: rgba(96,165,250,0.1); border: 1px solid rgba(96,165,250,0.2);
  display: flex; align-items: center; justify-content: center;
  transition: transform 0.3s;
}
.upload-zone:hover .upload-icon-wrap { transform: scale(1.08); }
.upload-icon { font-size: 28px; display: block; }

.upload-title { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 6px; }
.upload-sub   { font-size: 13px; color: var(--text3); margin-bottom: 28px; }

.upload-actions { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }

.btn-upload {
  padding: 12px 26px; border-radius: 100px; border: none;
  background: linear-gradient(135deg, var(--blue-deep), var(--purple));
  color: #fff; font-family: var(--font); font-size: 14px; font-weight: 700;
  cursor: pointer; transition: all 0.25s;
  box-shadow: 0 6px 20px rgba(96,165,250,0.3);
}
.btn-upload:hover { transform: translateY(-2px); box-shadow: 0 10px 28px rgba(96,165,250,0.4); }
.btn-upload:active { transform: scale(0.97); }

.btn-upload-sec {
  padding: 12px 26px; border-radius: 100px;
  border: 1px solid rgba(192,132,252,0.4);
  background: rgba(192,132,252,0.1); color: var(--purple);
  font-family: var(--font); font-size: 14px; font-weight: 700;
  cursor: pointer; transition: all 0.25s;
}
.btn-upload-sec:hover { background: rgba(192,132,252,0.2); transform: translateY(-2px); }

.btn-upload-ghost {
  padding: 12px 26px; border-radius: 100px;
  border: 1px solid var(--border); background: transparent;
  color: var(--text2); font-family: var(--font); font-size: 14px; font-weight: 600;
  cursor: pointer; transition: all 0.25s;
}
.btn-upload-ghost:hover { border-color: var(--blue); color: var(--blue); }

.btn-upload-danger {
  padding: 12px 26px; border-radius: 100px;
  border: 1px solid rgba(248,113,113,0.3);
  background: rgba(248,113,113,0.08); color: var(--red);
  font-family: var(--font); font-size: 14px; font-weight: 700;
  cursor: pointer; transition: all 0.25s;
}
.btn-upload-danger:hover { background: rgba(248,113,113,0.15); transform: translateY(-2px); }

/* Feature cards */
.feature-row {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;
}
.feature-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 24px 20px;
  transition: all 0.3s; cursor: default;
  animation: featureIn 0.5s ease calc(var(--fc-delay,0s)) backwards;
}
.feature-card:hover {
  border-color: var(--blue); transform: translateY(-4px);
  box-shadow: var(--shadow), var(--glow-blue);
}
.feature-card-icon { font-size: 28px; margin-bottom: 14px; display: block; }
.feature-card-title { font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 8px; }
.feature-card-body  { font-size: 12px; color: var(--text3); line-height: 1.6; }
@keyframes featureIn { from{opacity:0;transform:translateY(20px)} to{opacity:1;transform:translateY(0)} }

/* ═══════════════════════════════════════════════════════════════════════════
   RESULTS PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
.req-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 24px;
}
.req-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); overflow: hidden;
  min-height: 240px;
}
.req-card-header {
  display: flex; align-items: center; gap: 10px;
  padding: 16px 20px; border-bottom: 1px solid var(--border);
  background: var(--surface2);
}
.req-badge {
  font-size: 9px; font-weight: 800; padding: 3px 10px;
  border-radius: 100px; border: 1px solid; letter-spacing: 1px;
}
.req-blue   { color:var(--blue);   border-color:rgba(96,165,250,0.3);  background:rgba(96,165,250,0.08); }
.req-amber  { color:var(--amber);  border-color:rgba(251,191,36,0.3);  background:rgba(251,191,36,0.08); }
.req-purple { color:var(--purple); border-color:rgba(192,132,252,0.3); background:rgba(192,132,252,0.08); }
.req-green  { color:var(--green);  border-color:rgba(52,211,153,0.3);  background:rgba(52,211,153,0.08); }
.req-card-title { font-size: 13px; font-weight: 700; color: var(--text); }
.req-card-body  { padding: 16px 20px; }
.req-empty { color: var(--text3); font-size: 13px; text-align: center; padding: 40px 0; font-style: italic; }

/* Fragment table */
.frag-table-wrap {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-lg); overflow: hidden;
}
.frag-table-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 18px 24px; border-bottom: 1px solid var(--border);
  background: var(--surface2); gap: 12px; flex-wrap: wrap;
}
.frag-table-title { font-size: 15px; font-weight: 700; color: var(--text); }
.frag-search-wrap {
  display: flex; align-items: center; gap: 8px;
  background: var(--bg2); border: 1px solid var(--border);
  border-radius: 100px; padding: 7px 16px;
  font-size: 13px; color: var(--text3);
}
.frag-search {
  background: none; border: none; outline: none;
  font-family: var(--font); font-size: 13px; color: var(--text); width: 200px;
}
.table-scroll { overflow-x: auto; }
.frag-table {
  width: 100%; border-collapse: collapse;
  font-size: 12px;
}
.frag-table th {
  padding: 12px 16px; text-align: left;
  font-size: 10px; font-weight: 700; letter-spacing: 1px;
  text-transform: uppercase; color: var(--text3);
  border-bottom: 1px solid var(--border); background: var(--surface2);
  white-space: nowrap;
}
.frag-table td {
  padding: 11px 16px; border-bottom: 1px solid var(--border2);
  font-family: var(--mono); color: var(--text2); vertical-align: middle;
  white-space: nowrap;
}
.frag-table tbody tr {
  transition: background 0.15s;
  animation: rowFade 0.3s ease forwards;
}
.frag-table tbody tr:hover { background: var(--surface2); }
@keyframes rowFade { from{opacity:0;transform:translateX(-8px)} to{opacity:1;transform:none} }

/* ═══════════════════════════════════════════════════════════════════════════
   AI COACH PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
.ai-coach-layout {
  display: grid; grid-template-columns: 300px 1fr; gap: 24px;
  height: calc(100vh - 160px); min-height: 500px;
}

/* Sidebar */
.ai-coach-sidebar {
  display: flex; flex-direction: column; align-items: center;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 24px; padding: 32px 20px; gap: 12px; overflow-y: auto;
}

/* ── SIGNATURE ANIMATION: Breathing Orb ─────────────────────────────────── */
.ai-orb-wrap {
  position: relative; width: 160px; height: 160px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 8px;
}
.ai-orb-glow {
  position: absolute; inset: -20px; border-radius: 50%;
  background: radial-gradient(ellipse, rgba(96,165,250,0.25) 0%, transparent 70%);
  animation: glowPulse 4s ease-in-out infinite;
}
@keyframes glowPulse {
  0%,100% { opacity:0.6; transform:scale(1); }
  50%      { opacity:1;   transform:scale(1.15); }
}

.ai-orb {
  width: 120px; height: 120px; border-radius: 50%;
  background: conic-gradient(from 0deg,
    var(--blue) 0deg, var(--purple) 120deg,
    var(--cyan) 240deg, var(--blue) 360deg);
  display: flex; align-items: center; justify-content: center;
  position: relative; z-index: 1;
  animation: breatheOrb 5s ease-in-out infinite;
  box-shadow: 0 0 40px rgba(96,165,250,0.35), 0 0 80px rgba(192,132,252,0.2);
  cursor: pointer;
}
.ai-orb::before {
  content: \'\'; position: absolute; inset: 4px; border-radius: 50%;
  background: var(--surface);
}
.ai-orb-icon { font-size: 36px; position: relative; z-index: 1; }

@keyframes breatheOrb {
  0%,100% { transform: scale(1);    box-shadow: 0 0 40px rgba(96,165,250,0.35), 0 0 80px rgba(192,132,252,0.2); }
  50%      { transform: scale(1.07); box-shadow: 0 0 60px rgba(96,165,250,0.5), 0 0 120px rgba(192,132,252,0.3); }
}

.ai-orb.thinking {
  animation: thinkOrb 0.8s ease-in-out infinite;
}
@keyframes thinkOrb {
  0%,100% { transform: scale(1.02); filter: hue-rotate(0deg); }
  50%      { transform: scale(1.10); filter: hue-rotate(30deg); }
}

.ai-orb-rings { position: absolute; inset: 0; pointer-events: none; }
.ai-orb-ring {
  position: absolute; border-radius: 50%;
  border: 1px solid rgba(96,165,250,0.2);
  animation: expandRing 4s ease-in-out infinite;
}
.ai-orb-ring-1 { inset: -20px; animation-delay: 0s; }
.ai-orb-ring-2 { inset: -36px; animation-delay: 1.3s; }
.ai-orb-ring-3 { inset: -52px; animation-delay: 2.6s; }
@keyframes expandRing {
  0%   { opacity:0.6; transform:scale(0.9); }
  60%  { opacity:0.1; transform:scale(1.1); }
  100% { opacity:0; }
}

.ai-coach-name {
  font-family: var(--font-display); font-size: 16px; font-weight: 700; color: var(--text);
}
.ai-coach-status { font-size: 12px; color: var(--green); }

.ai-quick-prompts { width: 100%; margin-top: 8px; }
.aqp-label { font-size: 10px; font-weight: 700; letter-spacing: 1px; color: var(--text3); text-transform: uppercase; margin-bottom: 8px; }
.aqp-btn {
  display: block; width: 100%; text-align: left;
  padding: 10px 14px; border-radius: 10px; border: 1px solid var(--border);
  background: var(--bg2); color: var(--text2);
  font-family: var(--font); font-size: 12px; cursor: pointer;
  transition: all 0.2s; margin-bottom: 6px;
}
.aqp-btn:hover { border-color: var(--blue); color: var(--blue); background: rgba(96,165,250,0.06); }

/* Chat panel */
.ai-chat-panel {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 24px; display: flex; flex-direction: column;
  overflow: hidden;
}

.ai-chat-messages {
  flex: 1; overflow-y: auto; padding: 24px;
  display: flex; flex-direction: column; gap: 16px;
}

.ai-msg {
  display: flex; gap: 10px; align-items: flex-end;
  animation: msgSlide 0.35s cubic-bezier(0.34,1.56,0.64,1) forwards;
}
.ai-msg.user { flex-direction: row-reverse; }
@keyframes msgSlide {
  from { opacity:0; transform: translateY(12px) scale(0.96); }
  to   { opacity:1; transform: none; }
}

.ai-msg-avatar {
  width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 700;
  background: linear-gradient(135deg, var(--blue-deep), var(--purple));
  color: #fff;
}
.ai-msg.user .ai-msg-avatar { background: var(--surface3); color: var(--text2); }

.ai-msg-bubble {
  max-width: 72%; padding: 12px 16px; border-radius: 16px;
  font-size: 13px; line-height: 1.7; color: var(--text);
}
.ai-msg.ai   .ai-msg-bubble { background: var(--surface2); border-bottom-left-radius: 4px; }
.ai-msg.user .ai-msg-bubble {
  background: linear-gradient(135deg, var(--blue-deep), var(--purple));
  color: #fff; border-bottom-right-radius: 4px;
}

.ai-typing-indicator {
  display: flex; gap: 5px; align-items: center;
  padding: 12px 24px;
}
.ai-typing-indicator.hidden { display: none; }
.ai-typing-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--blue); opacity: 0.6;
  animation: typingBounce 1.2s ease-in-out infinite;
}
.ai-typing-dot:nth-child(2) { animation-delay: 0.2s; }
.ai-typing-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes typingBounce {
  0%,80%,100% { transform: translateY(0); opacity:0.4; }
  40%          { transform: translateY(-8px); opacity:1; }
}

.ai-chat-input-row {
  display: flex; gap: 10px; padding: 16px 20px;
  border-top: 1px solid var(--border); background: var(--surface2);
}
.ai-chat-input {
  flex: 1; background: var(--bg2); border: 1px solid var(--border);
  border-radius: 100px; padding: 12px 20px;
  font-family: var(--font); font-size: 13px; color: var(--text); outline: none;
  transition: border-color 0.2s;
}
.ai-chat-input:focus { border-color: var(--blue); }
.ai-chat-input::placeholder { color: var(--text3); }
.ai-send-btn {
  width: 44px; height: 44px; border-radius: 50%; border: none; flex-shrink: 0;
  background: linear-gradient(135deg, var(--blue-deep), var(--purple));
  color: #fff; cursor: pointer; transition: all 0.2s;
  display: flex; align-items: center; justify-content: center;
}
.ai-send-btn:hover { transform: scale(1.08); box-shadow: 0 4px 16px rgba(96,165,250,0.4); }
.ai-send-btn:active { transform: scale(0.95); }

/* ═══════════════════════════════════════════════════════════════════════════
   DELETED RECOVERY PAGE
   ═══════════════════════════════════════════════════════════════════════════ */
.del-tabs {
  display: flex; gap: 4px; margin-bottom: 24px;
  border-bottom: 1px solid var(--border); padding-bottom: 0;
}
.del-tab {
  background: none; border: none; color: var(--text3);
  font-size: 13px; font-weight: 600; padding: 10px 20px;
  border-radius: 10px 10px 0 0; cursor: pointer;
  border-bottom: 2px solid transparent; transition: all 0.2s;
  font-family: var(--font);
}
.del-tab:hover  { color: var(--text); background: rgba(255,255,255,0.04); }
.del-tab.active { color: var(--blue); border-bottom-color: var(--blue); background: rgba(96,165,250,0.07); }

.del-toolbar { display: flex; align-items: center; gap: 14px; margin-bottom: 20px; flex-wrap: wrap; }
.del-info { font-size: 12px; color: var(--text3); font-style: italic; }
.del-select {
  background: var(--surface2); color: var(--text); border: 1px solid var(--border);
  border-radius: 10px; padding: 10px 16px; font-size: 13px; font-family: var(--mono);
  cursor: pointer; outline: none; min-width: 220px;
}

.admin-notice {
  display: flex; gap: 14px; align-items: flex-start;
  padding: 14px 18px; border-radius: 12px; margin-bottom: 18px;
  background: rgba(251,191,36,0.07); border: 1px solid rgba(251,191,36,0.3);
}
.admin-notice-icon { font-size: 26px; flex-shrink: 0; }
.admin-notice strong { color: var(--amber); font-size: 13px; display: block; margin-bottom: 4px; }
.admin-notice p  { font-size: 12px; color: var(--text3); margin: 0 0 8px; }
.admin-notice code {
  font-family: var(--mono); font-size: 11px; color: var(--cyan);
  background: rgba(103,232,249,0.1); padding: 4px 10px; border-radius: 6px;
  border: 1px solid rgba(103,232,249,0.2); display: inline-block;
}

/* Deleted cards */
.del-results-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px,1fr)); gap: 14px;
}
.del-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 16px;
  transition: all 0.2s;
  animation: cardIn 0.3s ease forwards;
}
.del-card:hover { border-color: var(--blue); transform: translateY(-2px); box-shadow: var(--shadow); }
@keyframes cardIn { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:none} }

.del-card-top { display: flex; align-items: flex-start; gap: 12px; margin-bottom: 10px; }
.del-card-icon { font-size: 24px; flex-shrink: 0; margin-top: 2px; }
.del-card-name { font-size: 12px; font-weight: 700; color: var(--text); font-family: var(--mono); word-break: break-all; }
.del-card-meta { font-size: 11px; color: var(--text3); margin-top: 3px; line-height: 1.6; }
.del-card-bar-wrap { height: 4px; border-radius: 2px; background: rgba(255,255,255,0.06); margin: 8px 0; overflow: hidden; }
.del-card-bar { height: 100%; border-radius: 2px; transition: width 0.8s ease; }
.del-card-bar.green { background: linear-gradient(90deg, #059669, #34d399); }
.del-card-bar.amber { background: linear-gradient(90deg, #d97706, #fbbf24); }
.del-card-bar.red   { background: linear-gradient(90deg, #dc2626, #f87171); }
.del-card-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 10px; }
.del-card-sha { font-family: var(--mono); font-size: 10px; color: var(--text3); }
.del-card-actions { display: flex; gap: 6px; }

.btn-restore {
  font-size: 11px; font-weight: 700; padding: 5px 12px;
  border-radius: 8px; border: 1px solid rgba(52,211,153,0.3);
  cursor: pointer; font-family: var(--font);
  background: rgba(52,211,153,0.1); color: var(--green); transition: all 0.2s;
}
.btn-restore:hover { background: rgba(52,211,153,0.2); }
.btn-restore.done  { background: rgba(52,211,153,0.2); cursor: default; }

.carve-progress-wrap {
  height: 8px; border-radius: 4px; background: rgba(255,255,255,0.06);
  overflow: hidden; margin-bottom: 10px;
}
.carve-progress-bar {
  height: 100%; border-radius: 4px;
  background: linear-gradient(90deg, var(--blue), var(--purple));
  transition: width 0.5s ease; position: relative; overflow: hidden;
}
.carve-progress-bar::after {
  content:\'\'; position:absolute; inset:0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.25), transparent);
  animation: shimmer 1.5s infinite;
}
@keyframes shimmer { from{transform:translateX(-100%)} to{transform:translateX(100%)} }
.carve-stats { font-size: 12px; color: var(--text3); font-family: var(--mono); margin-bottom: 16px; }

.del-empty { text-align: center; padding: 50px 20px; color: var(--text3); font-size: 13px; }
.del-empty-icon { font-size: 40px; margin-bottom: 12px; }

/* ═══════════════════════════════════════════════════════════════════════════
   MODALS & SHARED COMPONENTS
   ═══════════════════════════════════════════════════════════════════════════ */
.modal-overlay {
  position: fixed; inset: 0; z-index: 800;
  background: rgba(9,14,26,0.7); backdrop-filter: blur(8px);
  display: flex; align-items: center; justify-content: center;
}
.modal-box {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 20px; padding: 28px; width: min(460px, 94vw);
  box-shadow: var(--shadow-lg);
  animation: modalIn 0.35s cubic-bezier(0.34,1.56,0.64,1);
}
@keyframes modalIn { from{opacity:0;transform:scale(0.92)translateY(16px)} to{opacity:1;transform:none} }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.modal-title  { font-size: 17px; font-weight: 700; color: var(--text); }
.modal-close  { background:none;border:none;color:var(--text3);font-size:20px;cursor:pointer;transition:color 0.2s; }
.modal-close:hover { color: var(--text); }
.modal-body   { margin-bottom: 20px; }
.modal-input  {
  width: 100%; background: var(--bg2); border: 1px solid var(--border);
  border-radius: 10px; padding: 11px 16px;
  font-family: var(--mono); font-size: 13px; color: var(--text); outline: none;
  transition: border-color 0.2s;
}
.modal-input:focus { border-color: var(--blue); }
.modal-footer { display: flex; gap: 10px; justify-content: flex-end; }

/* Buttons */
.btn-sm {
  padding: 8px 18px; border-radius: 8px;
  font-family: var(--font); font-size: 12px; font-weight: 700;
  cursor: pointer; transition: all 0.2s;
}
.btn-outline {
  background: transparent; border: 1px solid var(--border); color: var(--text2);
}
.btn-outline:hover { border-color: var(--blue); color: var(--blue); }
.btn-primary-sm {
  background: linear-gradient(135deg, var(--blue-deep), var(--purple));
  border: none; color: #fff;
}
.btn-primary-sm:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(96,165,250,0.3); }
.btn-primary {
  padding: 11px 22px; border-radius: 100px; border: none;
  background: linear-gradient(135deg, var(--blue-deep), var(--purple));
  color: #fff; font-family: var(--font); font-size: 13px; font-weight: 700;
  cursor: pointer; transition: all 0.25s;
}
.btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(96,165,250,0.35); }
.btn-primary:active { transform: scale(0.97); }
.btn-primary:disabled { opacity: 0.6; cursor: default; transform: none; }

/* ═══════════════════════════════════════════════════════════════════════════
   EXISTING REQUIREMENT PANEL CLASSES (kept for JS compat)
   ═══════════════════════════════════════════════════════════════════════════ */
.recon-empty,.req-empty { color:var(--text3);font-size:13px;text-align:center;padding:40px 0;font-style:italic; }
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
.hv-score.s-high { background:rgba(52,211,153,0.1); color:var(--green); border:1px solid rgba(52,211,153,0.25); }
.hv-score.s-mid  { background:rgba(251,191,36,0.1); color:var(--amber); border:1px solid rgba(251,191,36,0.25); }
.hv-score.s-low  { background:rgba(248,113,113,0.1);color:var(--red);   border:1px solid rgba(248,113,113,0.25); }

.decision-stat-row { display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-bottom:12px; }
.decision-stat { text-align:center;padding:10px 6px;border-radius:10px;background:rgba(255,255,255,0.03);border:1px solid var(--border); }
.decision-stat-val { font-size:20px;font-weight:800;font-family:var(--font-display); }
.decision-stat-lbl { font-size:9px;color:var(--text3);letter-spacing:0.5px;margin-top:2px;text-transform:uppercase; }
.ds-green { color:var(--green); }
.ds-amber { color:var(--amber); }
.ds-red   { color:var(--red); }
.decision-section-title { font-size:10px;font-weight:700;letter-spacing:1.5px;text-transform:uppercase;color:var(--text3);margin-bottom:6px;margin-top:10px;display:flex;align-items:center;gap:6px; }
.decision-section-title::after { content:\'\';flex:1;height:1px;background:var(--border); }
.decision-can  { border-left:3px solid var(--green); padding:10px 14px;border-radius:0 8px 8px 0;background:rgba(52,211,153,0.05);margin-bottom:8px; }
.decision-risk { border-left:3px solid var(--amber); padding:10px 14px;border-radius:0 8px 8px 0;background:rgba(251,191,36,0.05);margin-bottom:8px; }
.decision-lost { border-left:3px solid var(--red);   padding:10px 14px;border-radius:0 8px 8px 0;background:rgba(248,113,113,0.05);margin-bottom:8px; }
.decision-item { font-size:12px;color:var(--text2);line-height:1.6;display:flex;align-items:flex-start;gap:6px;margin-bottom:4px; }
.decision-dot  { flex-shrink:0;margin-top:4px; }

/* Toast */
.toast {
  position: fixed; bottom: 30px; right: 30px; z-index: 9999;
  padding: 14px 22px; border-radius: 14px;
  font-family: var(--font); font-size: 13px; font-weight: 600;
  max-width: 360px; line-height: 1.5; white-space: pre-line;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
  background: rgba(22,163,74,0.92); border: 1px solid rgba(74,222,128,0.4);
  color: #fff; transition: opacity 0.4s ease; cursor: pointer;
}
.toast.hidden { opacity: 0; pointer-events: none; }
.toast.error  { background: rgba(220,38,38,0.92); border-color: rgba(248,113,113,0.4); }

/* SVG gradient defs for scan ring */
body::after {
  content: \'\';
  position: absolute; width: 0; height: 0; overflow: hidden;
}

/* ── Log entries ───────────────────────────────────────────────────────────── */
.log-entry { padding: 2px 0; transition: opacity 0.3s; }
.log-entry.new { animation: logFadeIn 0.3s ease; }
@keyframes logFadeIn { from{opacity:0;transform:translateX(-6px)} to{opacity:1;transform:none} }
.log-ts   { color: var(--blue); margin-right: 6px; }
.log-info { color: var(--green); }
.log-warn { color: var(--amber); }
.log-err  { color: var(--red); }

/* Badge styles used by fragment table */
.badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 10px; border-radius: 100px; font-size: 10px;
  font-weight: 700; font-family: var(--mono);
}
.badge-green  { background:rgba(52,211,153,0.1); color:var(--green); border:1px solid rgba(52,211,153,0.2); }
.badge-amber  { background:rgba(251,191,36,0.1);  color:var(--amber); border:1px solid rgba(251,191,36,0.2); }
.badge-red    { background:rgba(248,113,113,0.1); color:var(--red);   border:1px solid rgba(248,113,113,0.2); }
.badge-blue   { background:rgba(96,165,250,0.1);  color:var(--blue);  border:1px solid rgba(96,165,250,0.2); }
.badge-purple { background:rgba(192,132,252,0.1); color:var(--purple);border:1px solid rgba(192,132,252,0.2); }

/* Action buttons in table */
.action-btn {
  padding: 4px 10px; border-radius: 6px; border: 1px solid var(--border);
  background: var(--surface2); color: var(--text2);
  font-family: var(--font); font-size: 11px; font-weight: 600;
  cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.action-btn:hover { border-color:var(--blue); color:var(--blue); }
.action-btn.ai-btn { border-color:rgba(192,132,252,0.3); color:var(--purple); background:rgba(192,132,252,0.06); }
.action-btn.ai-btn:hover { background:rgba(192,132,252,0.14); }

/* ── Responsive ────────────────────────────────────────────────────────────── */
@media (max-width: 1100px) {
  .feature-row { grid-template-columns: repeat(2,1fr); }
  .ai-coach-layout { grid-template-columns: 1fr; height: auto; }
  .ai-coach-sidebar { flex-direction: row; flex-wrap: wrap; border-radius: var(--radius); }
  .ai-orb-wrap { width: 100px; height: 100px; }
  .ai-orb { width: 80px; height: 80px; }
}
@media (max-width: 768px) {
  .app-main { padding: 20px 16px 60px; }
  .hero-headline { font-size: 2rem; }
  .hero-banner { padding: 40px 24px; }
  .req-grid { grid-template-columns: 1fr; }
  .home-stats-row { grid-template-columns: repeat(3,1fr); }
  .feature-row { grid-template-columns: 1fr; }
  .nav-tabs .nav-tab span:first-child { display:none; }
  .upload-actions { flex-direction: column; align-items: center; }
}
'''

with open("frontend/style.css", "w", encoding="utf-8") as f:
    f.write(CSS)
print("style.css written")

print("All frontend base files written successfully!")
