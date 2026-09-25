"""
write_ui_js.py — writes frontend/ui.js with UTF-8 encoding
"""

JS = r"""// ═══════════════════════════════════════════════════════════════════════════
// ui.js — RecoverAI Navigation, Animations & AI Chat
// ═══════════════════════════════════════════════════════════════════════════

const API = 'http://localhost:5000/api';

// ── Theme ────────────────────────────────────────────────────────────────────
function toggleTheme() {
  const html = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  html.setAttribute('data-theme', isDark ? 'light' : 'dark');
  document.getElementById('themeIcon').textContent = isDark ? '\u2600\uFE0F' : '\u263A';
  localStorage.setItem('recoverAiTheme', isDark ? 'light' : 'dark');
}

(function initTheme() {
  const saved = localStorage.getItem('recoverAiTheme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  const icon = document.getElementById('themeIcon');
  if (icon) icon.textContent = saved === 'dark' ? '\u263A' : '\u2600\uFE0F';
})();

// ── Onboarding ───────────────────────────────────────────────────────────────
let _selectedGoal = null;

function obNext(step) {
  document.querySelectorAll('.ob-step').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.ob-dot').forEach(d => d.classList.remove('active'));
  const stepEl = document.getElementById(`ob-step-${step}`);
  const dotEl  = document.getElementById(`ob-dot-${step}`);
  if (stepEl) stepEl.classList.add('active');
  if (dotEl)  dotEl.classList.add('active');
}

function selectGoal(card, goal) {
  document.querySelectorAll('.ob-option-card').forEach(c => c.classList.remove('selected'));
  card.classList.add('selected');
  _selectedGoal = goal;
}

function finishOnboarding() {
  const overlay = document.getElementById('onboardingOverlay');
  overlay.classList.add('hidden');
  localStorage.setItem('recoverAiOnboarded', '1');
  setTimeout(() => { overlay.style.display = 'none'; }, 500);

  // Show home page
  showPage('home');

  // If goal was deleted files, auto-show deleted page after brief delay
  if (_selectedGoal === 'deleted') {
    setTimeout(() => showPage('deleted'), 1200);
  }
}

// Check if already onboarded
(function checkOnboarding() {
  if (localStorage.getItem('recoverAiOnboarded')) {
    const overlay = document.getElementById('onboardingOverlay');
    if (overlay) { overlay.style.display = 'none'; }
    showPage('home');
  }
})();

// ── Page Navigation ──────────────────────────────────────────────────────────
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));

  const page = document.getElementById(`page-${name}`);
  if (page) page.classList.add('active');

  const tab = document.querySelector(`.nav-tab[data-page="${name}"]`);
  if (tab) tab.classList.add('active');

  // Special handling
  if (name === 'ai') {
    initAICoach();
    setTimeout(() => {
      document.getElementById('aiChatInput')?.focus();
    }, 400);
  }
  if (name === 'deleted') {
    loadDriveList();
  }
  if (name === 'results') {
    // Trigger chart animations
    animateIntegrityBars();
  }
}

// ── Scan Progress Overlay ────────────────────────────────────────────────────
function showScanOverlay() {
  const overlay = document.getElementById('scanProgressOverlay');
  if (overlay) {
    overlay.classList.remove('hidden');
  }
}

function hideScanOverlay() {
  const overlay = document.getElementById('scanProgressOverlay');
  if (overlay) {
    overlay.classList.add('hidden');
  }
}

// Update the SVG ring from 0–100
function updateScanRing(pct) {
  const fill = document.getElementById('scanRingFill');
  if (!fill) return;
  const circumference = 326.7;
  const offset = circumference - (pct / 100) * circumference;
  fill.style.strokeDashoffset = offset;
}

// Inject SVG gradient into DOM for the scan ring
(function injectSVGDefs() {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', '0'); svg.setAttribute('height', '0');
  svg.style.position = 'absolute';
  svg.innerHTML = `
    <defs>
      <linearGradient id="scanGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%"   stop-color="#60A5FA"/>
        <stop offset="50%"  stop-color="#C084FC"/>
        <stop offset="100%" stop-color="#67E8F9"/>
      </linearGradient>
    </defs>`;
  document.body.prepend(svg);
})();

// Intercept app.js scan functions to use overlay
const _origUpdateProgress = window.updateProgress;
window.updateProgress = function(pct, msg) {
  // Show overlay on first call
  const overlay = document.getElementById('scanProgressOverlay');
  if (overlay && overlay.classList.contains('hidden')) {
    overlay.classList.remove('hidden');
  }
  // Update ring
  updateScanRing(pct);
  // Update pct label
  const pctEl = document.getElementById('progressPct');
  if (pctEl) pctEl.textContent = Math.round(pct) + '%';
  // Call original if exists
  if (typeof _origUpdateProgress === 'function') _origUpdateProgress(pct, msg);
};

// Hide overlay when report is ready
const _origRenderDashboard = window.renderDashboard;
window.renderDashboard = function(data) {
  if (typeof _origRenderDashboard === 'function') _origRenderDashboard(data);
  // Switch to results page and show stats
  hideScanOverlay();
  showPage('results');
  showHomeStats(data);
  animateStatCards();
};

function showHomeStats(data) {
  const row = document.getElementById('homeStatsRow');
  if (row) row.style.display = 'grid';
}

function animateStatCards() {
  const vals = ['fragmentCount','recoverable','corrupt','totalSize','recoveryRate'];
  vals.forEach((id, i) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.animationDelay = `${i * 0.1}s`;
  });
}

function animateIntegrityBars() {
  document.querySelectorAll('.ih-bar').forEach(bar => {
    const w = bar.style.width;
    bar.style.width = '0%';
    setTimeout(() => { bar.style.width = w; }, 100);
  });
}

// openDeletedRecovery compat
window.openDeletedRecovery = function() {
  showPage('deleted');
};
window.closeDeletedRecovery = function() {
  showPage('home');
};

// ── AI Coach ─────────────────────────────────────────────────────────────────
let _aiCoachInited = false;
let _scanContext = '';

function initAICoach() {
  if (_aiCoachInited) return;
  _aiCoachInited = true;

  const msgs = document.getElementById('aiChatMessages');
  if (!msgs) return;
  msgs.innerHTML = '';

  // Welcome message
  appendAIMessage('ai', `\u{1F50D} **Hello, I\u2019m your Gemini Forensic AI.**\n\nI\u2019m here to help you understand your scan results, guide recovery decisions, and explain digital forensics concepts.\n\nTry asking me about your recovered fragments, or use the quick questions on the left!`);
}

function appendAIMessage(role, text) {
  const msgs = document.getElementById('aiChatMessages');
  if (!msgs) return;

  const el = document.createElement('div');
  el.className = `ai-msg ${role}`;

  const avatar = document.createElement('div');
  avatar.className = 'ai-msg-avatar';
  avatar.textContent = role === 'ai' ? '\u{1F916}' : '\u{1F464}';

  const bubble = document.createElement('div');
  bubble.className = 'ai-msg-bubble';
  // Simple markdown-lite: bold, line breaks
  bubble.innerHTML = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');

  el.appendChild(avatar);
  el.appendChild(bubble);
  msgs.appendChild(el);
  msgs.scrollTop = msgs.scrollHeight;
}

function setAIThinking(active) {
  const typing = document.getElementById('aiTyping');
  const orb    = document.getElementById('aiOrb');
  const status = document.getElementById('aiCoachStatus');

  if (typing) typing.classList.toggle('hidden', !active);
  if (orb)    orb.classList.toggle('thinking', active);
  if (status) status.textContent = active ? 'Thinking\u2026' : 'Ready to assist';
}

async function sendAIChat(event) {
  event?.preventDefault();
  const input  = document.getElementById('aiChatInput');
  const msg    = input?.value.trim();
  if (!msg) return;

  input.value = '';
  appendAIMessage('user', msg);
  setAIThinking(true);

  // Scroll
  const msgs = document.getElementById('aiChatMessages');
  if (msgs) msgs.scrollTop = msgs.scrollHeight;

  try {
    const res  = await fetch(`${API}/ai-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, context: _scanContext })
    });
    const data = await res.json();
    setAIThinking(false);
    if (data.response) {
      appendAIMessage('ai', data.response);
    } else if (data.error) {
      appendAIMessage('ai', `\u26A0\uFE0F ${data.error}\n\nMake sure your Gemini API key is configured.`);
    }
  } catch (e) {
    setAIThinking(false);
    appendAIMessage('ai', '\u26A0\uFE0F Could not reach the AI backend. Is the server running?');
  }
}

function sendQuickPrompt(prompt) {
  const input = document.getElementById('aiChatInput');
  if (input) {
    input.value = prompt;
    document.getElementById('aiChatForm')?.dispatchEvent(new Event('submit', {cancelable:true}));
  }
}

// Update scan context when results come in
const _origPopulateDashboard = window.populateDashboardPanels;
window.populateDashboardPanels = function(scanData) {
  if (typeof _origPopulateDashboard === 'function') _origPopulateDashboard(scanData);
  // Build context string for AI
  if (scanData && scanData.fragments) {
    const total = scanData.fragments.length;
    const good  = scanData.fragments.filter(f => f.integrity?.score >= 70).length;
    _scanContext = `Scan results: ${total} fragments found, ${good} recoverable (${Math.round(good/total*100)}% recovery rate). ` +
      `Top categories: ${[...new Set(scanData.fragments.slice(0,5).map(f => f.category))].join(', ')}.`;
  }
};

// ── AI Config Modal ───────────────────────────────────────────────────────────
function openAIConfig() {
  const modal = document.getElementById('aiConfigModal');
  if (modal) modal.style.display = 'flex';
}
function closeAIConfig() {
  const modal = document.getElementById('aiConfigModal');
  if (modal) modal.style.display = 'none';
}
async function saveAIKey() {
  const key    = document.getElementById('aiKeyInput')?.value.trim();
  const status = document.getElementById('aiConfigStatus');
  if (!key) { if (status) { status.textContent = 'Please enter an API key.'; status.style.color = 'var(--red)'; } return; }

  if (status) { status.textContent = 'Validating\u2026'; status.style.color = 'var(--text3)'; }
  try {
    const res  = await fetch(`${API}/ai-config`, {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ api_key: key })
    });
    const data = await res.json();
    if (data.status === 'ok') {
      if (status) { status.textContent = '\u2705 ' + data.message; status.style.color = 'var(--green)'; }
      setTimeout(closeAIConfig, 1500);
      checkAIStatus();
    } else {
      if (status) { status.textContent = '\u274C ' + data.message; status.style.color = 'var(--red)'; }
    }
  } catch(e) {
    if (status) { status.textContent = 'Error: ' + e.message; status.style.color = 'var(--red)'; }
  }
}

async function checkAIStatus() {
  try {
    const res  = await fetch(`${API}/ai-status`);
    const data = await res.json();
    const dot  = document.getElementById('aiStatusDot');
    const txt  = document.getElementById('aiStatusText');
    if (data.active) {
      if (dot) { dot.className = 'ai-status-dot active'; }
      if (txt) txt.textContent = 'AI: ' + (data.model || 'ACTIVE').replace('models/','').toUpperCase();
    } else {
      if (dot) { dot.className = 'ai-status-dot'; }
      if (txt) txt.textContent = 'AI: Inactive';
    }
  } catch(e) {
    const txt = document.getElementById('aiStatusText');
    if (txt) txt.textContent = 'AI: Offline';
  }
}
checkAIStatus();

// ── Upload zone drag & drop enhancements ─────────────────────────────────────
(function enhanceUploadZone() {
  const zone = document.getElementById('uploadZone');
  if (!zone) return;

  zone.addEventListener('dragover', e => {
    e.preventDefault();
    zone.classList.add('drag-over');
  });
  zone.addEventListener('dragleave', () => zone.classList.remove('drag-over'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0 && typeof handleFileSelect === 'function') {
      handleFileSelect(files[0]);
    }
  });
})();

// ── logContainer enhancements ─────────────────────────────────────────────────
const _logObserver = new MutationObserver(() => {
  const lc = document.getElementById('logContainer');
  if (lc) lc.scrollTop = lc.scrollHeight;
});
(function observeLog() {
  const lc = document.getElementById('logContainer');
  if (lc) _logObserver.observe(lc, { childList: true });
})();

// ── Toast override (if not defined in app.js) ──────────────────────────────
if (typeof showToast === 'undefined') {
  window.showToast = function(msg, isError) {
    let t = document.getElementById('recoverToast');
    if (!t) return;
    t.className = 'toast' + (isError ? ' error' : '');
    t.textContent = msg;
    clearTimeout(t._tid);
    t._tid = setTimeout(() => { t.classList.add('hidden'); }, 5000);
  };
}

// ── Keyboard shortcuts ─────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    closeAIConfig();
  }
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    showPage('ai');
    setTimeout(() => document.getElementById('aiChatInput')?.focus(), 300);
  }
});

// ── Staggered page-load animation ────────────────────────────────────────────
(function staggerEntrance() {
  const cards = document.querySelectorAll('.feature-card, .hstat-card, .req-card');
  cards.forEach((card, i) => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    setTimeout(() => {
      card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      card.style.opacity = '1';
      card.style.transform = 'translateY(0)';
    }, 200 + i * 80);
  });
})();

// ── filterFragments (table search) ────────────────────────────────────────────
function filterFragments(q) {
  const rows = document.querySelectorAll('#fragmentTableBody tr');
  const lq   = q.toLowerCase();
  rows.forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(lq) ? '' : 'none';
  });
}
"""

with open("frontend/ui.js", "w", encoding="utf-8") as f:
    f.write(JS)
print("ui.js written")
