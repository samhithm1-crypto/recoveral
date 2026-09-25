"""append_missing_css.py — appends missing CSS classes to style.css"""

CSS = """
/* ═══════════════════════════════════════════════════════════════════════════
   LOADING OVERLAY (app.js adds/removes .active class)
   ═══════════════════════════════════════════════════════════════════════════ */
.loading-overlay {
  position: fixed; inset: 0; z-index: 900;
  background: rgba(9,14,26,0.96); backdrop-filter: blur(12px);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; pointer-events: none;
  transition: opacity 0.3s ease;
}
.loading-overlay.active { opacity: 1; pointer-events: all; }

.lo-inner { text-align: center; display: flex; flex-direction: column; align-items: center; gap: 24px; }

.lo-orb-ring {
  width: 100px; height: 100px; border-radius: 50%;
  background: conic-gradient(from 0deg, var(--blue) 0deg, var(--purple) 180deg, var(--cyan) 360deg);
  display: flex; align-items: center; justify-content: center;
  animation: spinOrb 2s linear infinite;
  box-shadow: 0 0 40px rgba(96,165,250,0.4);
}
@keyframes spinOrb { to { transform: rotate(360deg); } }
.lo-orb {
  width: 80px; height: 80px; border-radius: 50%;
  background: var(--bg);
}
.lo-title { font-family: var(--font-display); font-size: 20px; font-weight: 700; color: var(--text); }

.lo-steps { display: flex; flex-direction: column; gap: 6px; min-width: 300px; }
.lo-step {
  padding: 10px 16px; border-radius: 10px; font-size: 12px;
  color: var(--text3); background: var(--surface);
  border: 1px solid var(--border); transition: all 0.3s;
  font-family: var(--mono); text-align: left;
}
.lo-step.active {
  color: var(--blue); border-color: rgba(96,165,250,0.4);
  background: rgba(96,165,250,0.08);
  animation: pulseStep 1s ease-in-out infinite;
}
.lo-step.done { color: var(--green); border-color: rgba(52,211,153,0.3); background: rgba(52,211,153,0.06); }
@keyframes pulseStep { 0%,100%{opacity:1} 50%{opacity:0.7} }

/* ── Mode toggle ──────────────────────────────────────────────────────────── */
.mode-toggle-row {
  display: flex; gap: 8px; margin-bottom: 16px;
}
.mode-btn {
  padding: 8px 18px; border-radius: 100px; border: 1px solid var(--border);
  background: transparent; color: var(--text3);
  font-family: var(--font); font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
}
.mode-btn:hover  { color: var(--text); border-color: var(--blue); }
.mode-btn.active { color: var(--blue); background: rgba(96,165,250,0.12); border-color: rgba(96,165,250,0.4); }

/* ── Scan info bar ─────────────────────────────────────────────────────────── */
.scan-info-bar {
  display: flex; align-items: center; gap: 14px; flex-wrap: wrap;
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 12px 20px; margin-bottom: 20px;
}
.scan-id-badge {
  font-family: var(--mono); font-size: 11px; font-weight: 700;
  color: var(--blue); background: rgba(96,165,250,0.1);
  border: 1px solid rgba(96,165,250,0.25); padding: 4px 12px; border-radius: 100px;
}
.scan-file-info { font-size: 12px; color: var(--text3); font-family: var(--mono); flex: 1; }
.scan-actions { display: flex; gap: 8px; }

/* ── Summary cards ─────────────────────────────────────────────────────────── */
.summary-cards {
  display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; margin-bottom: 24px;
}
.summary-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 18px 14px; text-align: center;
  transition: all 0.25s;
}
.summary-card:hover { transform: translateY(-3px); box-shadow: var(--shadow); }
.sc-label { font-size: 10px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 8px; }
.sc-val   { font-family: var(--font-display); font-size: 28px; font-weight: 800; color: var(--text); }
.sc-green .sc-val { color: var(--green); }
.sc-amber .sc-val { color: var(--amber); }
.sc-red   .sc-val { color: var(--red); }
.sc-blue  .sc-val { color: var(--blue); }

.sc-gauge { padding: 10px 14px; }
.gauge-wrap { position: relative; display: flex; flex-direction: column; align-items: center; }
.gauge-svg  { width: 80px; height: 50px; }
.gauge-pct  { font-family: var(--font-display); font-size: 18px; font-weight: 800; color: var(--text); margin-top: 4px; }

/* ── AI Analysis Banner ───────────────────────────────────────────────────── */
.ai-analysis-banner {
  background: linear-gradient(135deg, rgba(96,165,250,0.07), rgba(192,132,252,0.07));
  border: 1px solid rgba(96,165,250,0.2);
  border-radius: var(--radius-lg); padding: 20px 24px; margin-bottom: 24px;
  animation: fadeInBanner 0.5s ease;
}
@keyframes fadeInBanner { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:none} }
.aab-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px; gap: 12px; flex-wrap: wrap;
}
.aab-badge {
  font-size: 12px; font-weight: 700; color: var(--purple);
  background: rgba(192,132,252,0.1); border: 1px solid rgba(192,132,252,0.25);
  padding: 4px 14px; border-radius: 100px;
}
.aab-body { font-size: 13px; color: var(--text2); line-height: 1.75; white-space: pre-wrap; }
.gemini-live-badge {
  font-size: 9px; font-weight: 800; letter-spacing: 2px; color: var(--green);
  background: rgba(52,211,153,0.12); border: 1px solid rgba(52,211,153,0.3);
  padding: 3px 10px; border-radius: 100px; margin-right: 8px;
  animation: blink 1.5s ease-in-out infinite;
}

/* ── Two-col row ──────────────────────────────────────────────────────────── */
.two-col-row { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 24px; margin-top: 24px; }
.info-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 20px; }
.info-card-title { font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 14px; }
.cat-list, .rel-list { display: flex; flex-direction: column; gap: 6px; }

/* ── Reconstruction panel ─────────────────────────────────────────────────── */
.recon-panel { background: var(--surface); border: 1px solid rgba(52,211,153,0.25); border-radius: var(--radius-lg); padding: 20px; margin-bottom: 24px; }

/* ── Recovery modal warning ───────────────────────────────────────────────── */
.recovery-warning {
  padding: 10px 16px; border-radius: 10px; background: rgba(251,191,36,0.08);
  border: 1px solid rgba(251,191,36,0.3); color: var(--amber); font-size: 12px;
  margin-bottom: 12px;
}

/* ── Responsive additions ─────────────────────────────────────────────────── */
@media (max-width: 1100px) {
  .summary-cards { grid-template-columns: repeat(3, 1fr); }
  .two-col-row   { grid-template-columns: 1fr; }
}
@media (max-width: 768px) {
  .summary-cards { grid-template-columns: repeat(2, 1fr); }
  .req-grid { grid-template-columns: 1fr; }
  .scan-info-bar { flex-direction: column; align-items: flex-start; }
}
"""

with open("frontend/style.css", "a", encoding="utf-8") as f:
    f.write(CSS)
print("Missing CSS appended")
