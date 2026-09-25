"""write_ui_js_v2.py — writes the final, fully-compatible ui.js"""

JS = r"""// ═══════════════════════════════════════════════════════════════════════════
// ui.js v2 — RecoverAI: New Shell + Full app.js Compatibility Layer
// ═══════════════════════════════════════════════════════════════════════════
// app.js is already loaded before this file. We intercept its section logic
// and map it to the new page-based navigation.
// ═══════════════════════════════════════════════════════════════════════════

const _API = 'http://localhost:5000/api';

// ── Theme ─────────────────────────────────────────────────────────────────────
function toggleTheme() {
  const html   = document.documentElement;
  const isDark = html.getAttribute('data-theme') === 'dark';
  const next   = isDark ? 'light' : 'dark';
  html.setAttribute('data-theme', next);
  document.getElementById('themeIcon').textContent = next === 'dark' ? '\u263A' : '\u2600\uFE0F';
  localStorage.setItem('recoverAiTheme', next);
}
(function initTheme() {
  const saved = localStorage.getItem('recoverAiTheme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  const icon = document.getElementById('themeIcon');
  if (icon) icon.textContent = saved === 'dark' ? '\u263A' : '\u2600\uFE0F';
})();

// ── Page Navigation ───────────────────────────────────────────────────────────
function showPage(name) {
  // Hide all pages
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));

  // If showing results, make #dashboard visible inside page-results logic
  if (name === 'results') {
    // Activate home page but hide hero/upload, show dashboard
    const pageHome = document.getElementById('page-home');
    if (pageHome) pageHome.classList.add('active');
    const hero  = document.getElementById('hero');
    const upload= document.getElementById('uploadSection');
    const dash  = document.getElementById('dashboard');
    if (hero)   hero.style.display   = 'none';
    if (upload) upload.style.display = 'none';
    if (dash)   dash.style.display   = 'block';
  } else {
    // Show the actual page
    const pg = document.getElementById('page-' + name);
    if (pg) pg.classList.add('active');
  }

  const tab = document.querySelector(`.nav-tab[data-page="${name}"]`);
  if (tab) tab.classList.add('active');

  if (name === 'ai') {
    initAICoach();
    setTimeout(() => document.getElementById('aiChatInput')?.focus(), 400);
  }
  if (name === 'deleted') {
    loadDriveList?.();
  }
}

// ── Intercept app.js: heroSection + uploadSection + dashboard hide/show ───────
// app.js does:
//   heroSection.style.display = 'none'
//   uploadSection.style.display = 'none'
//   dashboard.style.display = 'block'
// We need to detect when dashboard is shown and switch pages.

const _dashEl   = document.getElementById('dashboard');
const _heroEl   = document.getElementById('hero');
const _uploadEl = document.getElementById('uploadSection');

if (_dashEl) {
  // Use a MutationObserver to watch dashboard display changes
  const _dashObs = new MutationObserver(() => {
    if (_dashEl.style.display === 'block') {
      // app.js just showed the dashboard — switch to results nav tab
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      const tab = document.querySelector('.nav-tab[data-page="results"]');
      if (tab) tab.classList.add('active');
      // Make sure home page is active (dashboard lives inside page-home)
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      const pageHome = document.getElementById('page-home');
      if (pageHome) pageHome.classList.add('active');
      // Animate cards
      setTimeout(animateResultCards, 200);
    } else {
      // app.js hid dashboard (newScan) — switch back to home
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      const tab = document.querySelector('.nav-tab[data-page="home"]');
      if (tab) tab.classList.add('active');
      document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
      const pageHome = document.getElementById('page-home');
      if (pageHome) pageHome.classList.add('active');
    }
  });
  _dashObs.observe(_dashEl, { attributes: true, attributeFilter: ['style'] });
}

function animateResultCards() {
  document.querySelectorAll('.summary-card, .req-card').forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(16px)';
    setTimeout(() => {
      el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }, i * 60);
  });
}

// ── Intercept: openDeletedRecovery / closeDeletedRecovery ─────────────────────
// app.js calls these directly — we make them also switch the nav page.
const _origOpenDeleted  = window.openDeletedRecovery;
const _origCloseDeleted = window.closeDeletedRecovery;
window.openDeletedRecovery = function() {
  showPage('deleted');
  if (typeof _origOpenDeleted === 'function') _origOpenDeleted();
};
window.closeDeletedRecovery = function() {
  showPage('home');
  if (typeof _origCloseDeleted === 'function') _origCloseDeleted();
};

// ── Loading overlay — app.js uses .active class on #loadingOverlay ───────────
// Already has the element, just add CSS for it
// (style.css handles .loading-overlay.active)

// ── Onboarding ────────────────────────────────────────────────────────────────
let _selectedGoal = null;

function obNext(step) {
  document.querySelectorAll('.ob-step').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.ob-dot').forEach(d => d.classList.remove('active'));
  const s = document.getElementById('ob-step-' + step);
  const d = document.getElementById('ob-dot-'  + step);
  if (s) s.classList.add('active');
  if (d) d.classList.add('active');
}
function selectGoal(card, goal) {
  document.querySelectorAll('.ob-option-card').forEach(c => c.classList.remove('selected'));
  card.classList.add('selected');
  _selectedGoal = goal;
}
function finishOnboarding() {
  const ov = document.getElementById('onboardingOverlay');
  if (ov) { ov.classList.add('hidden'); setTimeout(() => ov.style.display = 'none', 500); }
  localStorage.setItem('recoverAiOnboarded', '1');
  if (_selectedGoal === 'deleted') setTimeout(() => showPage('deleted'), 800);
  else showPage('home');
}
(function checkOnboarding() {
  if (localStorage.getItem('recoverAiOnboarded')) {
    const ov = document.getElementById('onboardingOverlay');
    if (ov) ov.style.display = 'none';
  }
})();

// ── AI Config Modal ───────────────────────────────────────────────────────────
function openAIConfig() {
  const m = document.getElementById('aiConfigModal');
  if (m) m.style.display = 'flex';
}
function closeAIConfig() {
  const m = document.getElementById('aiConfigModal');
  if (m) m.style.display = 'none';
}
function toggleKeyVisibility() {
  const inp = document.getElementById('geminiKeyInput');
  const btn = document.getElementById('keyToggleBtn');
  if (!inp) return;
  if (inp.type === 'password') { inp.type = 'text'; if (btn) btn.textContent = 'Hide'; }
  else                         { inp.type = 'password'; if (btn) btn.textContent = 'Show'; }
}
async function saveAIKey() {
  // sync both inputs
  const primary = document.getElementById('geminiKeyInput');
  const alias   = document.getElementById('aiKeyInput');
  const key     = primary?.value.trim() || alias?.value.trim() || '';
  const status  = document.getElementById('aiConfigStatus');
  if (!key) { if (status) { status.textContent = 'Please enter an API key.'; status.style.color = 'var(--red)'; } return; }
  if (alias) alias.value = key;

  if (status) { status.textContent = 'Validating\u2026'; status.style.color = 'var(--text3)'; }
  try {
    const res  = await fetch(`${_API}/ai-config`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
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
    const res  = await fetch(`${_API}/ai-status`);
    const data = await res.json();
    const dot  = document.getElementById('aiStatusDot');
    const txt  = document.getElementById('aiStatusText');
    const live = document.getElementById('geminiLiveBadge');
    const regen= document.getElementById('regenerateAIBtn');
    if (data.active) {
      if (dot)  { dot.className = 'ai-status-dot active'; }
      if (txt)  txt.textContent = 'MODELS/' + (data.model || 'GEMINI').replace('models/','').toUpperCase() + ': ON';
      if (live) live.style.display = 'inline';
      if (regen)regen.style.display = 'inline-flex';
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
setInterval(checkAIStatus, 30000);

// ── AI Coach Chat ─────────────────────────────────────────────────────────────
let _aiCoachInited = false;
let _chatContext   = '';

function initAICoach() {
  if (_aiCoachInited) return;
  _aiCoachInited = true;
  const msgs = document.getElementById('aiChatMessages');
  if (!msgs) return;
  msgs.innerHTML = '';
  appendAIMsg('ai', '**Hello, I\'m your Gemini Forensic AI.**\n\nI can help you understand scan results, guide recovery decisions, and explain digital forensics.\n\nTry a quick question on the left, or ask me anything!');
}

function appendAIMsg(role, text) {
  const msgs = document.getElementById('aiChatMessages');
  if (!msgs) return;
  const el  = document.createElement('div');
  el.className = 'ai-msg ' + role;
  const av  = document.createElement('div');
  av.className = 'ai-msg-avatar';
  av.textContent = role === 'ai' ? '\u{1F916}' : '\u{1F464}';
  const bub = document.createElement('div');
  bub.className = 'ai-msg-bubble';
  bub.innerHTML = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br>');
  el.appendChild(av);
  el.appendChild(bub);
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
  const input = document.getElementById('aiChatInput');
  const msg   = input?.value.trim();
  if (!msg) return;
  input.value = '';
  appendAIMsg('user', msg);
  setAIThinking(true);
  const msgs = document.getElementById('aiChatMessages');
  if (msgs) msgs.scrollTop = msgs.scrollHeight;
  try {
    const res  = await fetch(`${_API}/ai-chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, context: _chatContext })
    });
    const data = await res.json();
    setAIThinking(false);
    if (data.response) {
      appendAIMsg('ai', data.response);
    } else {
      appendAIMsg('ai', '\u26A0\uFE0F ' + (data.error || 'No response. Check API key.'));
    }
  } catch(e) {
    setAIThinking(false);
    appendAIMsg('ai', '\u26A0\uFE0F Could not reach the AI backend. Is the server running?');
  }
}

function sendQuickPrompt(prompt) {
  const input = document.getElementById('aiChatInput');
  if (input) input.value = prompt;
  document.getElementById('aiChatForm')?.dispatchEvent(new Event('submit', { cancelable: true }));
}

// Update chat context when scan completes
const _origRenderDash = window.renderDashboard;
if (typeof _origRenderDash === 'function') {
  window.renderDashboard = function(report) {
    _origRenderDash(report);
    // Build AI context
    try {
      const s = report.summary;
      _chatContext = `Scan complete: ${s.total_fragments} fragments, ${s.recoverable} recoverable (${s.recovery_rate_pct}% rate). ` +
        `Categories: ${Object.keys(s.categories_found || {}).join(', ')}.`;
    } catch(e) {}
  };
}

// ── filterFragments (search) ──────────────────────────────────────────────────
function filterFragments(q) {
  const rows = document.querySelectorAll('#fragTableBody tr');
  const lq   = q.toLowerCase();
  rows.forEach(r => { r.style.display = r.textContent.toLowerCase().includes(lq) ? '' : 'none'; });
}

// ── Toast ─────────────────────────────────────────────────────────────────────
if (typeof window.showToast === 'undefined') {
  window.showToast = function(msg, isError) {
    const t = document.getElementById('recoverToast');
    if (!t) return;
    t.className = 'toast' + (isError ? ' error' : '');
    t.textContent = msg;
    clearTimeout(t._tid);
    t._tid = setTimeout(() => t.classList.add('hidden'), 5000);
  };
}

// ── Keyboard shortcuts ────────────────────────────────────────────────────────
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeAIConfig();
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    showPage('ai');
    setTimeout(() => document.getElementById('aiChatInput')?.focus(), 300);
  }
});

// ── Upload zone drag enhancement ──────────────────────────────────────────────
// app.js already adds drag listeners to uploadZone, we just add visual class
const _uz = document.getElementById('uploadZone');
if (_uz) {
  _uz.addEventListener('dragover', () => _uz.classList.add('drag-over'));
  ['dragleave','drop'].forEach(ev => _uz.addEventListener(ev, () => _uz.classList.remove('drag-over')));
}

// ── Stagger entrance animation on page load ───────────────────────────────────
(function() {
  const els = document.querySelectorAll('.feature-card');
  els.forEach((el, i) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }, 300 + i * 100);
  });
})();
"""

with open("frontend/ui.js", "w", encoding="utf-8") as f:
    f.write(JS)
print("ui.js v2 written")
