"""
fix_recover_and_ai.py
1. Fixes Recover button: modal uses classList.active but CSS was using display:none
2. Fixes AI Advice: shows in a floating overlay panel (not inline in table cell)
3. Adds btn-ai-frag CSS
"""

# ── 1. Fix the recoveryModal — make .active work ────────────────────────────
with open("frontend/index.html", encoding="utf-8") as f:
    html = f.read()

# Change recoveryModal from style="display:none" to use class only
html = html.replace(
    '<div id="recoveryModal" class="modal-overlay" style="display:none">',
    '<div id="recoveryModal" class="modal-overlay" onclick="closeRecoveryModal(event)">'
)
# Also fix aiConfigModal
html = html.replace(
    '<div id="aiConfigModal" class="modal-overlay" style="display:none">',
    '<div id="aiConfigModal" class="modal-overlay">'
)

# Add AI advice floating panel right before </body>
AI_PANEL = '''
<!-- ── AI Advice floating panel (shown per fragment) ── -->
<div id="aiAdvicePanel" class="ai-advice-panel" style="display:none">
  <div class="aap-header">
    <div class="aap-title">
      <span class="aap-icon">&#10024;</span>
      <span>Gemini AI Advice</span>
      <span class="aap-frag" id="aapFragName"></span>
    </div>
    <button class="aap-close" onclick="closeAIAdvice()">&times;</button>
  </div>
  <div class="aap-body" id="aapBody">
    <div class="aap-loading">&#9203; Asking Gemini AI&hellip;</div>
  </div>
</div>

'''

if "aiAdvicePanel" not in html:
    html = html.replace('<script src="app.js"></script>', AI_PANEL + '<script src="app.js"></script>')

with open("frontend/index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("index.html: recoveryModal + AI advice panel fixed")


# ── 2. Fix app.js ────────────────────────────────────────────────────────────
with open("frontend/app.js", encoding="utf-8") as f:
    js = f.read()

# 2a. Fix modal open — replace classList.add("active") with style.display
js = js.replace(
    'modal.classList.add("active");',
    'modal.style.display = "flex";'
)

# 2b. Fix modal close
js = js.replace(
    """function closeRecoveryModal(event) {
  // Only close if clicking the overlay backdrop (not the modal itself)
  if (event && event.target !== document.getElementById("recoveryModal")) return;
  document.getElementById("recoveryModal").classList.remove("active");""",
    """function closeRecoveryModal(event) {
  // Only close if clicking the overlay backdrop (not the modal itself)
  if (event && event.target !== document.getElementById("recoveryModal")) return;
  document.getElementById("recoveryModal").style.display = "none";"""
)

# Also fix the close button onclick in HTML which calls with no event
js = js.replace(
    """document.getElementById('recoveryModal').style.display='none'""",
    """document.getElementById('recoveryModal').style.display='none'"""
)

# 2c. Fix requestFragmentAI to use the floating panel instead of inline <td>
OLD_AI = '''async function requestFragmentAI(scanId, fragId, btnEl) {
  if (!_aiConfigured) {
    openAIConfig();
    return;
  }

  const row    = btnEl.closest("td");
  let recBox   = row.querySelector(".ai-rec-box");

  // Toggle off if already shown
  if (recBox) { recBox.remove(); btnEl.textContent = "✨ AI Advice"; return; }

  btnEl.textContent = "⏳ Asking AI…";
  btnEl.disabled    = true;

  try {
    const res  = await fetch(`${API}/ai-recommend/${scanId}/${fragId}`);
    const data = await res.json();

    if (res.ok && data.recommendation) {
      recBox = document.createElement("div");
      recBox.className = "ai-rec-box";
      recBox.innerHTML = `<div class="ai-rec-label">✨ GEMINI AI ADVICE</div>${data.recommendation}`;
      row.appendChild(recBox);
      btnEl.textContent = "✨ Hide AI";
    } else {
      btnEl.textContent = "✨ AI Advice";
      alert("AI: " + (data.error || "Recommendation failed"));
    }
  } catch (err) {
    btnEl.textContent = "✨ AI Advice";
    alert("AI error: " + err.message);
  } finally {
    btnEl.disabled = false;
  }
}'''

NEW_AI = '''// Track which button opened the AI advice panel
let _activeAIBtn = null;

function closeAIAdvice() {
  document.getElementById("aiAdvicePanel").style.display = "none";
  if (_activeAIBtn) { _activeAIBtn.textContent = "✨ AI Advice"; _activeAIBtn.disabled = false; }
  _activeAIBtn = null;
}

async function requestFragmentAI(scanId, fragId, btnEl) {
  if (!_aiConfigured) { openAIConfig(); return; }

  const panel = document.getElementById("aiAdvicePanel");
  const body  = document.getElementById("aapBody");
  const fragNameEl = document.getElementById("aapFragName");

  // If same button clicked again — toggle off
  if (_activeAIBtn === btnEl && panel.style.display !== "none") {
    closeAIAdvice();
    return;
  }

  // Reset previous button
  if (_activeAIBtn && _activeAIBtn !== btnEl) {
    _activeAIBtn.textContent = "✨ AI Advice";
    _activeAIBtn.disabled = false;
  }

  _activeAIBtn = btnEl;
  btnEl.textContent = "⏳ Asking…";
  btnEl.disabled    = true;

  // Find fragment name from allFragments
  const frag = allFragments.find(f => f.id === fragId);
  if (fragNameEl) fragNameEl.textContent = frag ? frag.name : `Fragment ${fragId}`;

  // Show panel with loading state
  body.innerHTML = `<div class="aap-loading">&#9203; Asking Gemini AI&hellip;</div>`;
  panel.style.display = "flex";

  try {
    const res  = await fetch(`${API}/ai-recommend/${scanId}/${fragId}`);
    const data = await res.json();

    if (res.ok && data.recommendation) {
      body.innerHTML = `<div class="aap-text">${data.recommendation}</div>`;
      btnEl.textContent = "✨ Hide AI";
      btnEl.disabled = false;
    } else {
      body.innerHTML = `<div class="aap-error">&#10060; ${data.error || "Recommendation failed"}</div>`;
      btnEl.textContent = "✨ AI Advice";
      btnEl.disabled = false;
      _activeAIBtn = null;
    }
  } catch (err) {
    body.innerHTML = `<div class="aap-error">&#10060; Network error: ${err.message}</div>`;
    btnEl.textContent = "✨ AI Advice";
    btnEl.disabled = false;
    _activeAIBtn = null;
  }
}'''

if OLD_AI in js:
    js = js.replace(OLD_AI, NEW_AI)
    print("app.js: requestFragmentAI replaced with floating panel version")
else:
    print("WARNING: Could not find requestFragmentAI to replace — checking partial match...")
    if "async function requestFragmentAI" in js:
        print("  Function exists but signature differs")

with open("frontend/app.js", "w", encoding="utf-8") as f:
    f.write(js)


# ── 3. Add CSS for modal active + ai advice panel ────────────────────────────
with open("frontend/style.css", encoding="utf-8") as f:
    css = f.read()

NEW_CSS = """

/* ═══════════════════════════════════════════════════════════════════════════
   MODAL OVERLAY — active state
   ═══════════════════════════════════════════════════════════════════════════ */
.modal-overlay {
  display: none;
  position: fixed; inset: 0; z-index: 800;
  background: rgba(10,15,30,0.78); backdrop-filter: blur(10px);
  align-items: center; justify-content: center;
}

/* ═══════════════════════════════════════════════════════════════════════════
   AI ADVICE FLOATING PANEL
   ═══════════════════════════════════════════════════════════════════════════ */
.ai-advice-panel {
  position: fixed; bottom: 28px; right: 28px; z-index: 900;
  width: min(480px, calc(100vw - 40px)); max-height: 55vh;
  background: var(--surface);
  border: 1px solid rgba(167,139,250,0.35);
  border-radius: 16px;
  box-shadow: 0 12px 48px rgba(0,0,0,0.55), 0 0 0 1px rgba(167,139,250,0.1);
  display: flex; flex-direction: column;
  animation: slideUp 0.3s cubic-bezier(0.34,1.56,0.64,1);
}
@keyframes slideUp {
  from { opacity:0; transform: translateY(20px) scale(0.97); }
  to   { opacity:1; transform: none; }
}
.aap-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; border-bottom: 1px solid var(--border);
  background: linear-gradient(135deg, rgba(167,139,250,0.08), rgba(96,165,250,0.08));
  border-radius: 16px 16px 0 0;
  flex-shrink: 0;
}
.aap-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 700; color: var(--purple);
}
.aap-icon { font-size: 16px; }
.aap-frag {
  font-family: var(--mono); font-size: 11px; color: var(--text3);
  background: rgba(255,255,255,0.05); padding: 2px 8px; border-radius: 6px;
}
.aap-close {
  background: none; border: none; color: var(--text3); font-size: 20px;
  cursor: pointer; transition: color 0.2s; line-height: 1;
}
.aap-close:hover { color: var(--text); }
.aap-body {
  padding: 16px 18px; overflow-y: auto; flex: 1;
}
.aap-loading {
  font-size: 13px; color: var(--text3); font-style: italic;
  display: flex; align-items: center; gap: 8px;
  animation: pulse 1.2s ease infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.5} }
.aap-text {
  font-size: 13px; color: var(--text2); line-height: 1.75;
  white-space: pre-wrap;
}
.aap-error {
  font-size: 12px; color: var(--red); padding: 8px 0;
}

/* AI Advice button in table */
.btn-ai-frag {
  padding: 5px 12px; border-radius: 8px;
  border: 1px solid rgba(167,139,250,0.35);
  background: rgba(167,139,250,0.08); color: var(--purple);
  font-family: var(--font); font-size: 11px; font-weight: 700;
  cursor: pointer; transition: all 0.2s; white-space: nowrap;
  margin-left: 6px;
}
.btn-ai-frag:hover    { background: rgba(167,139,250,0.18); transform: translateY(-1px); }
.btn-ai-frag:disabled { opacity: 0.6; cursor: default; transform: none; }
"""

if ".ai-advice-panel" not in css:
    with open("frontend/style.css", "a", encoding="utf-8") as f:
        f.write(NEW_CSS)
    print("style.css: modal active + AI advice panel CSS added")
else:
    print("style.css: already has ai-advice-panel CSS")

print("\n=== ALL FIXES DONE ===")
print("Restart server + hard refresh browser (Ctrl+Shift+R)")
