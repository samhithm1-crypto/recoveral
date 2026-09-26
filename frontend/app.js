// ── STATE ──────────────────────────────────────────────────────────────────
const API = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1")
  ? "http://localhost:5000/api"
  : window.location.origin + "/api";
let currentReport = null;
let currentMode   = "file"; // "file" | "folder"

// ── DOM REFS ───────────────────────────────────────────────────────────────
const fileInput      = document.getElementById("fileInput");
const folderInput    = document.getElementById("folderInput");
const uploadZone     = document.getElementById("uploadZone");
const loadingOverlay = document.getElementById("loadingOverlay");
const dashboard      = document.getElementById("dashboard");
const uploadSection  = document.getElementById("uploadSection");
const heroSection    = document.getElementById("hero");

// ── MODE TOGGLE ────────────────────────────────────────────────────────────
function setMode(mode) {
  currentMode = mode;
  document.getElementById("modeBtnFile").classList.toggle("active",   mode === "file");
  document.getElementById("modeBtnFolder").classList.toggle("active", mode === "folder");

  if (mode === "file") {
    document.getElementById("uploadIcon").textContent  = "📄";
    document.getElementById("uploadTitle").textContent = "Drop Corrupted File / Disk Image Here";
    document.getElementById("uploadSub").textContent   = "Supports .img, .dd, .bin, .raw, .pdf, .zip — any binary";
    document.getElementById("browseBtn").textContent   = "Browse & Select File";
  } else {
    document.getElementById("uploadIcon").textContent  = "📂";
    document.getElementById("uploadTitle").textContent = "Select a Folder to Scan All Files Inside";
    document.getElementById("uploadSub").textContent   = "Scans every file recursively — ideal for full drive/partition dumps";
    document.getElementById("browseBtn").textContent   = "Browse & Select Folder";
  }
}

function triggerBrowse() {
  if (currentMode === "folder") {
    folderInput.value = "";
    folderInput.click();
  } else {
    fileInput.value = "";
    fileInput.click();
  }
}

// ── FILE INPUT (single) ────────────────────────────────────────────────────
fileInput.addEventListener("change", (e) => {
  if (e.target.files.length > 0) processFiles(e.target.files, e.target.files[0].name);
});

// ── FOLDER INPUT (webkitdirectory) ─────────────────────────────────────────
folderInput.addEventListener("change", (e) => {
  const files = e.target.files;
  if (files.length === 0) return;

  // Derive folder name from first file's webkitRelativePath
  const folderName = files[0].webkitRelativePath.split("/")[0] || "selected_folder";
  processFiles(files, folderName + "/ [" + files.length + " files]");
});

// ── DRAG & DROP ────────────────────────────────────────────────────────────
["dragenter","dragover"].forEach(ev =>
  uploadZone.addEventListener(ev, (e) => { e.preventDefault(); uploadZone.classList.add("drag-over"); })
);
["dragleave","drop"].forEach(ev =>
  uploadZone.addEventListener(ev, (e) => { e.preventDefault(); uploadZone.classList.remove("drag-over"); })
);
uploadZone.addEventListener("drop", (e) => {
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    const label = files.length === 1 ? files[0].name : files.length + " files dropped";
    processFiles(files, label);
  }
});

// ── PROCESS FILES → combine → send to backend ──────────────────────────────
async function processFiles(fileList, label) {
  showLoading(fileList.length);
  animateLoadingSteps();

  try {
    const files = Array.from(fileList);
    const isFolder = files.length > 1;

    if (isFolder) {
      // ── FOLDER mode: send each file individually to /api/scan-folder ──
      const formData = new FormData();
      let uploaded = 0;
      for (const file of files) {
        try {
          formData.append("files", file, file.name);
          uploaded++;
        } catch (e) {
          console.warn("Skipping file:", file.name, e.message);
        }
      }
      if (uploaded === 0) {
        hideLoading();
        alert("No files could be read.");
        return;
      }

      const res  = await fetch(`${API}/scan-folder`, { method: "POST", body: formData });
      const data = await res.json();
      if (data.error) { hideLoading(); alert("Scan error: " + data.error); return; }
      currentReport = data.report;
      currentReport.meta.filename = label;
      renderDashboard(data.report);

    } else {
      // ── SINGLE FILE mode: legacy blob approach ──
      const MAX_TOTAL = 200 * 1024 * 1024;
      const chunks    = [];
      let   totalRead = 0;
      let   skipped   = 0;

      for (const file of files) {
        if (totalRead + file.size > MAX_TOTAL) { skipped++; continue; }
        try {
          const buf = await readFileAsBuffer(file);
          chunks.push(new Uint8Array(buf));
          totalRead += buf.byteLength;
        } catch (readErr) {
          console.warn("Skipping unreadable file:", file.name, readErr.message);
          skipped++;
        }
      }

      if (chunks.length === 0) {
        hideLoading();
        alert("No files could be read.");
        return;
      }

      const totalLen = chunks.reduce((s, c) => s + c.byteLength, 0);
      const combined = new Uint8Array(totalLen);
      let   offset   = 0;
      for (const c of chunks) { combined.set(c, offset); offset += c.byteLength; }

      const displayLabel = skipped > 0
        ? `${label}  (${skipped} file(s) skipped)`
        : label;

      const blob     = new Blob([combined], { type: "application/octet-stream" });
      const formData = new FormData();
      formData.append("file", blob, displayLabel);

      const res  = await fetch(`${API}/scan`, { method: "POST", body: formData });
      const data = await res.json();
      if (data.error) { hideLoading(); alert("Scan error: " + data.error); return; }
      currentReport = data.report;
      currentReport.meta.filename = displayLabel;
      renderDashboard(data.report);
    }

  } catch (err) {
    hideLoading();
    alert("Could not reach backend. Is app.py running?\n\nError: " + err.message);
  }
}

// ── SAFE FILE READER ────────────────────────────────────────────────────────
// FileReader is more permissive than arrayBuffer() on Windows — avoids the
// "file could not be read due to permission problems" browser security error.
function readFileAsBuffer(file) {
  return new Promise((resolve, reject) => {
    const reader  = new FileReader();
    reader.onload  = (e) => resolve(e.target.result);
    reader.onerror = ()  => reject(new Error("Cannot read: " + file.name));
    reader.readAsArrayBuffer(file);
  });
}

// ── DEMO SCAN ──────────────────────────────────────────────────────────────
async function loadDemo() {
  showLoading(1);
  animateLoadingSteps();
  try {
    const res  = await fetch(`${API}/demo`);
    const data = await res.json();
    currentReport = data.report;
    renderDashboard(data.report);
  } catch (err) {
    alert("Could not reach backend. Is app.py running?");
    hideLoading();
  }
}

// ── LOADING ANIMATION ──────────────────────────────────────────────────────
function showLoading(fileCount) {
  loadingOverlay.classList.add("active");
  ["ls1","ls2","ls3","ls4","ls5","ls6"].forEach(id => {
    const el = document.getElementById(id);
    el.classList.remove("active","done");
  });
  document.getElementById("ls1").classList.add("active");
  if (fileCount > 1) {
    document.getElementById("ls1").textContent = `Reading ${fileCount} files from folder…`;
  } else {
    document.getElementById("ls1").textContent = "Reading file signatures…";
  }
}
function hideLoading() { loadingOverlay.classList.remove("active"); }

function animateLoadingSteps() {
  const steps = ["ls1","ls2","ls3","ls4","ls5","ls6"];
  let i = 0;
  const interval = setInterval(() => {
    if (i > 0) {
      document.getElementById(steps[i-1]).classList.remove("active");
      document.getElementById(steps[i-1]).classList.add("done");
    }
    if (i < steps.length) {
      document.getElementById(steps[i]).classList.add("active");
      i++;
    } else {
      clearInterval(interval);
    }
  }, 350);
}

// ── RENDER DASHBOARD ───────────────────────────────────────────────────────
function renderDashboard(report) {
  setTimeout(() => {
    hideLoading();
    heroSection.style.display    = "none";
    uploadSection.style.display  = "none";
    dashboard.style.display      = "block";
    window.scrollTo(0, 0);

    // Show navbar action buttons (NOT navCenter — dashboard topbar handles scan info)
    const _ep = document.getElementById("exportPdfBtn");
    const _ec = document.getElementById("exportCsvBtn");
    const _ns = document.getElementById("newScanBtn");
    if (_ep) _ep.style.display = "";
    if (_ec) _ec.style.display = "";
    if (_ns) _ns.style.display = "";

    const { meta, summary, fragments, relationships } = report;

    document.getElementById("scanId").textContent   = `SCAN-ID: ${report.scan_id}`;
    document.getElementById("scanFile").textContent =
      `TARGET: ${meta.filename}  (${meta.filesize_kb} KB)  ·  ${new Date(meta.scan_time).toLocaleString()}`;

    // Also fill the in-dashboard top bar
    const _dsi = document.getElementById("dashScanId");
    const _dta = document.getElementById("dashTarget");
    if (_dsi) _dsi.textContent = `SCAN-ID: ${report.scan_id}`;
    if (_dta) _dta.textContent = `TARGET: ${meta.filename}  (${meta.filesize_kb} KB)  ·  ${new Date(meta.scan_time).toLocaleString()}`;

    document.getElementById("cTotal").textContent       = summary.total_fragments;
    document.getElementById("cRecoverable").textContent = summary.recoverable;
    document.getElementById("cPartial").textContent     = summary.partial;
    document.getElementById("cCritical").textContent    = summary.critical;
    document.getElementById("cRate").textContent        = summary.recovery_rate_pct + "%";

    animateGauge(summary.recovery_rate_pct);
    renderFragmentTable(fragments);
    renderCategories(summary.categories_found, summary.total_fragments);
    renderRelationships(relationships, fragments);
    renderAISummary(report);

    // Show reconstruction results if any fragments were reassembled
    if (report.reconstructions && report.reconstructions.length > 0) {
      renderReconstructionPanel(report.reconstructions);
      // Auto-scroll to it so users can't miss the recovered image
      setTimeout(() => {
        const rp = document.getElementById("reconstructionPanel");
        if (rp) rp.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 500);
    } else {
      const existing = document.getElementById("reconstructionPanel");
      if (existing) existing.remove();
    }

  }, 2200);
}

// ── GAUGE ──────────────────────────────────────────────────────────────────
function animateGauge(pct) {
  const arc   = document.getElementById("gaugeArc");
  const pctEl = document.getElementById("gaugePct");
  const total = 251.4;
  const offset = total - (total * pct / 100);
  
  if (pct === 0) arc.style.opacity = "0";
  else arc.style.opacity = "1";

  setTimeout(() => {
    arc.style.strokeDashoffset = offset;
    let cur = 0;
    const timer = setInterval(() => {
      cur += 2;
      if (cur >= pct) { cur = pct; clearInterval(timer); }
      pctEl.textContent = (cur % 1 !== 0 ? cur.toFixed(1) : cur) + "%";
    }, 20);
  }, 300);
}

// ── FRAGMENT TABLE ─────────────────────────────────────────────────────────
let allFragments = [];

function renderFragmentTable(fragments) {
  allFragments = fragments;
  buildTable(fragments);
}

function buildTable(fragments) {
  const tbody = document.getElementById("fragTableBody");
  tbody.innerHTML = "";

  if (fragments.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--text3);padding:32px">No fragments match this filter.</td></tr>`;
    return;
  }

  fragments.forEach(f => {
    const { integrity, priority } = f;
    const colorClass = integrity.color;
    const catClass   = "cat-" + f.category;
    const barWidth   = priority + "%";
    const isCritical = integrity.status === "CRITICAL";

    const tr = document.createElement("tr");
    tr.dataset.status = integrity.status;
    tr.innerHTML = `
      <td>
        <div class="priority-bar">
          <span class="priority-num" style="color:var(--cyan)">${priority}</span>
          <div class="pbar"><div class="pbar-fill" style="width:${barWidth}"></div></div>
        </div>
      </td>
      <td>
        <div class="frag-name">${f.name}</div>
        <div class="frag-type">Offset: 0x${f.offset.toString(16).toUpperCase().padStart(8,"0")}</div>
      </td>
      <td><span class="cat-tag ${catClass}">${f.type_name}</span></td>
      <td style="font-family:var(--mono);font-size:12px">${f.size_kb} KB</td>
      <td class="integrity-cell">
        <div class="int-score ${colorClass}">${integrity.score}%</div>
        <div style="font-size:10px;color:var(--text3)">Entropy: ${integrity.entropy}</div>
      </td>
      <td><span class="status-badge ${colorClass}">${integrity.status}</span></td>
      <td><span class="sha-text">${f.sha256}…</span></td>
      <td>
        <button
          class="btn-recover-frag ${isCritical ? 'critical' : ''}"
          onclick="openRecoveryModal('${currentReport?.scan_id || 'DEMO0001'}', ${f.id})"
          title="${isCritical ? 'CRITICAL: partial recovery only' : 'AI-recover this fragment'}"
        >
          ${isCritical ? '⚠️ Attempt' : '⬇️ Recover'}
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterFragments(status, btn) {
  document.querySelectorAll(".fbtn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  buildTable(status === "all" ? allFragments : allFragments.filter(f => f.integrity.status === status));
}

// ── CATEGORIES ─────────────────────────────────────────────────────────────
const CAT_COLORS = {
  image:"#c084fc", document:"#93c5fd", database:"#67e8f9",
  media:"#fcd34d", archive:"#fca5a5", data:"#86efac",
  web:"#fdba74",   binary:"#94a3b8",  unknown:"#64748b"
};

function renderCategories(cats, total) {
  const el = document.getElementById("catList");
  el.innerHTML = "";
  Object.entries(cats).forEach(([cat, count]) => {
    const pct   = Math.round((count / total) * 100);
    const color = CAT_COLORS[cat] || "#94a3b8";
    el.innerHTML += `
      <div class="cat-item">
        <div class="cat-item-name">
          <div class="cat-dot" style="background:${color}"></div>
          <span>${cat.charAt(0).toUpperCase()+cat.slice(1)}</span>
        </div>
        <span class="cat-count">${count}</span>
      </div>
      <div class="cat-bar-wrap"><div class="cat-bar" style="width:${pct}%;background:${color}"></div></div>
    `;
  });
}

// ── RELATIONSHIPS ──────────────────────────────────────────────────────────
function renderRelationships(rels, fragments) {
  const el = document.getElementById("relList");
  if (!rels || rels.length === 0) {
    el.innerHTML = `<div class="rel-empty">No relationships detected.</div>`;
    return;
  }
  el.innerHTML = "";
  rels.forEach(r => {
    const fromName = fragments.find(f => f.id === r.from)?.name || `FRAG_${r.from}`;
    const toName   = fragments.find(f => f.id === r.to)?.name   || `FRAG_${r.to}`;
    el.innerHTML += `
      <div class="rel-item">
        <div class="rel-frags">${fromName} ↔ ${toName}</div>
        <div class="rel-reason">${r.reason}</div>
        <div class="rel-conf">Confidence: <strong style="color:var(--cyan)">${r.confidence}%</strong></div>
      </div>
    `;
  });
}

// ── AI SUMMARY ─────────────────────────────────────────────────────────────
function renderAISummary(report) {
  const { summary, meta } = report;
  const rate  = summary.recovery_rate_pct;
  const cats  = Object.keys(summary.categories_found).join(", ");
  const rVerb = rate >= 70 ? "HIGH confidence recovery" : rate >= 40 ? "MODERATE partial recovery" : "LOW — significant data loss";

  document.getElementById("aiText").innerHTML = `
    <strong>Scan Target:</strong> ${meta.filename} (${meta.filesize_kb} KB)<br/><br/>
    RecoverAI's fragment analysis engine identified <strong>${summary.total_fragments} recoverable data segments</strong>
    across the corrupted storage media using file-signature detection (magic byte analysis) and Shannon entropy scoring.<br/><br/>
    <strong>${summary.recoverable} fragments</strong> are fully recoverable,
    <strong>${summary.partial}</strong> are partially intact and may be reconstructed with additional processing,
    while <strong>${summary.critical}</strong> show critical corruption levels and are likely unrecoverable.<br/><br/>
    <strong>Overall Recovery Assessment: ${rVerb}</strong> — estimated <strong>${rate}%</strong> of the original data can be restored.<br/><br/>
    Data categories detected: <strong>${cats}</strong>.
    ${summary.top_priority_fragment ? `Highest-priority fragment for immediate recovery: <strong style="color:var(--cyan)">${summary.top_priority_fragment}</strong>.` : ""}
    <br/><br/>
    <em style="color:var(--text3)">Generated by RecoverAI v1.0 · Evidence integrity via SHA-256 checksums · Scanned: ${new Date(meta.scan_time).toLocaleString()}</em>
  `;
}

// ── RECONSTRUCTION PANEL ────────────────────────────────────────────────────
function renderReconstructionPanel(reconstructions) {
  // Remove any existing panel
  const existing = document.getElementById("reconstructionPanel");
  if (existing) existing.remove();

  const container = document.querySelector(".container");
  const panel = document.createElement("div");
  panel.id = "reconstructionPanel";
  panel.className = "panel recon-panel";

  const isImage = ["jpg","jpeg","png","gif","webp"].includes(
    (reconstructions[0]?.ext || "").toLowerCase()
  );

  let reconCards = reconstructions.map((rec, i) => {
    const verified = rec.manifest_match === true
      ? '<span class="recon-badge verified">✅ SHA-256 VERIFIED</span>'
      : rec.manifest_match === false
      ? '<span class="recon-badge warn">⚠️ SHA-256 MISMATCH</span>'
      : '<span class="recon-badge neutral">📋 No Manifest</span>';

    const logHtml = (rec.log || []).map(l =>
      `<div class="rlog-line">${l}</div>`
    ).join("");

    const imgPreview = (isImage && i === 0)
      ? `<div class="recon-img-wrap" id="reconImgWrap_${i}">
          <div class="recon-img-loading">🔄 Loading reconstructed image…</div>
         </div>`
      : "";

    return `
      <div class="recon-card">
        <div class="recon-card-header">
          <div class="recon-card-info">
            <div class="recon-filename">🗂️ ${rec.name}</div>
            <div class="recon-meta">
              <span>${rec.fragment_count} fragments reassembled</span>
              <span>·</span>
              <span>${rec.size_kb} KB</span>
              <span>·</span>
              <span>${rec.type_name}</span>
              <span>·</span>
              ${verified}
            </div>
            <div class="recon-fragments">
              Fragments: ${(rec.fragment_names || []).map(n => `<code>${n}</code>`).join(" + ")}
            </div>
          </div>
          <button class="btn-recover-download recon-dl-btn" onclick="downloadReconstruction('${rec.download_key}', '${rec.name}')">
            ⬇️ Download Reconstructed File
          </button>
        </div>
        ${imgPreview}
        <div class="recon-log-wrap">
          <div class="recon-log-title">⚙️ AI Reconstruction Log</div>
          <div class="recovery-log">${logHtml}</div>
        </div>
      </div>
    `;
  }).join("");

  panel.innerHTML = `
    <div class="panel-header recon-panel-header">
      <h2>🎉 AI FRAGMENT RECONSTRUCTION COMPLETE</h2>
      <span class="ai-badge" style="background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff">
        ${reconstructions.length} FILE${reconstructions.length > 1 ? "S" : ""} RECOVERED
      </span>
    </div>
    <div class="recon-intro">
      RecoverAI successfully <strong>detected, ordered, and concatenated</strong> the binary fragments 
      to reconstruct the original file. The image below is the AI-recovered output.
    </div>
    ${reconCards}
  `;

  // Insert panel BEFORE the AI analysis panel
  const aiPanel = document.querySelector(".ai-panel");
  if (aiPanel) {
    container.insertBefore(panel, aiPanel);
  } else {
    container.appendChild(panel);
  }

  // Load image preview via blob URL (secure, no CORS issues)
  reconstructions.forEach((rec, i) => {
    if (!isImage || i !== 0) return;
    const wrap = document.getElementById("reconImgWrap_" + i);
    if (!wrap) return;

    const imgUrl = `${API}/download-reconstruction/${rec.download_key}`;
    fetch(imgUrl)
      .then(r => r.blob())
      .then(blob => {
        const url = URL.createObjectURL(blob);
        wrap.innerHTML = `
          <div class="recon-img-label">📸 Reconstructed Image Preview</div>
          <img src="${url}" alt="Reconstructed: ${rec.name}" class="recon-img"
               onerror="this.style.display='none';this.nextElementSibling.style.display='block'"/>
          <div style="display:none;color:var(--text3);padding:16px;text-align:center">
            ⚠️ Preview unavailable — download the file to view it.
          </div>
        `;
      })
      .catch(() => {
        wrap.innerHTML = `<div style="color:var(--text3);padding:16px">⚠️ Preview unavailable — use the download button.</div>`;
      });
  });
}

async function downloadReconstruction(downloadKey, name) {
  const url = `${API}/download-reconstruction/${downloadKey}`;
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
}



// ── EXPORT PDF ─────────────────────────────────────────────────────────────
function exportPDF() {
  if (!currentReport) return;

  const btn = document.getElementById("exportPdfBtn");
  btn.textContent = "Generating PDF…";
  btn.disabled = true;

  try {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
    const W   = doc.internal.pageSize.getWidth();
    const { meta, summary, fragments, relationships } = currentReport;

    // ── COLOUR PALETTE ──────────────────────────────────────────────────
    const C = {
      bg:     [7,  9, 15],
      panel:  [13, 17, 27],
      cyan:   [6, 182, 212],
      blue:   [59, 130, 246],
      green:  [34, 197, 94],
      yellow: [245, 158, 11],
      red:    [239, 68, 68],
      purple: [168, 85, 247],
      white:  [226, 232, 240],
      gray:   [100, 116, 139],
    };

    // ── PAGE BACKGROUND ─────────────────────────────────────────────────
    function fillBg() {
      doc.setFillColor(...C.bg);
      doc.rect(0, 0, W, 297, "F");
    }
    fillBg();

    // ── HEADER BANNER ───────────────────────────────────────────────────
    doc.setFillColor(...C.panel);
    doc.rect(0, 0, W, 38, "F");
    // Cyan accent bar
    doc.setFillColor(...C.cyan);
    doc.rect(0, 0, W, 2, "F");

    doc.setTextColor(...C.cyan);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(22);
    doc.text("RecoverAI", 15, 16);
    doc.setFontSize(9);
    doc.setFont("helvetica", "normal");
    doc.setTextColor(...C.gray);
    doc.text("FORENSIC EDITION  |  AI-Powered Data Recovery Platform", 15, 22);

    // Scan ID badge (top right)
    doc.setFillColor(...C.cyan);
    doc.roundedRect(W - 55, 8, 45, 10, 2, 2, "F");
    doc.setTextColor(...C.bg);
    doc.setFont("helvetica", "bold");
    doc.setFontSize(8);
    doc.text(`SCAN: ${currentReport.scan_id}`, W - 32.5, 14.5, { align: "center" });

    // Scan meta row
    doc.setTextColor(...C.gray);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.text(`Target: ${meta.filename}   |   Size: ${meta.filesize_kb} KB   |   Scanned: ${new Date(meta.scan_time).toLocaleString()}`, 15, 32);

    let y = 48;

    // ── SUMMARY CARDS ROW ────────────────────────────────────────────────
    const cards = [
      { label: "Total Fragments", val: summary.total_fragments,   color: C.blue   },
      { label: "Recoverable",     val: summary.recoverable,        color: C.green  },
      { label: "Partial",         val: summary.partial,            color: C.yellow },
      { label: "Critical",        val: summary.critical,           color: C.red    },
      { label: "Recovery Rate",   val: summary.recovery_rate_pct + "%", color: C.purple },
    ];
    const cw = (W - 30) / 5;
    cards.forEach((c, i) => {
      const cx = 15 + i * cw;
      doc.setFillColor(...C.panel);
      doc.roundedRect(cx, y, cw - 3, 20, 2, 2, "F");
      // Colour top accent
      doc.setFillColor(...c.color);
      doc.roundedRect(cx, y, cw - 3, 2, 1, 1, "F");
      // Value
      doc.setTextColor(...c.color);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(14);
      doc.text(String(c.val), cx + (cw - 3) / 2, y + 11, { align: "center" });
      // Label
      doc.setTextColor(...C.gray);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(6.5);
      doc.text(c.label.toUpperCase(), cx + (cw - 3) / 2, y + 17, { align: "center" });
    });
    y += 28;

    // ── SECTION HELPER ───────────────────────────────────────────────────
    function sectionHeader(title, yPos) {
      doc.setFillColor(...C.panel);
      doc.rect(15, yPos, W - 30, 8, "F");
      doc.setFillColor(...C.cyan);
      doc.rect(15, yPos, 3, 8, "F");
      doc.setTextColor(...C.white);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(9);
      doc.text(title, 22, yPos + 5.5);
      return yPos + 12;
    }

    // ── FRAGMENT RECOVERY TABLE ───────────────────────────────────────────
    y = sectionHeader("FRAGMENT RECOVERY MAP", y);

    const statusColor = (s) => {
      if (s === "RECOVERABLE") return [34, 197, 94];
      if (s === "PARTIAL")     return [245, 158, 11];
      return [239, 68, 68];
    };

    doc.autoTable({
      startY: y,
      margin: { left: 15, right: 15 },
      head: [["Priority", "Fragment", "Type", "Size", "Integrity", "Status", "SHA-256"]],
      body: fragments.map(f => [
        f.priority,
        f.name,
        f.type_name,
        f.size_kb + " KB",
        f.integrity.score + "%",
        f.integrity.status,
        f.sha256 + "…",
      ]),
      styles: {
        fontSize: 7.5,
        fillColor: C.panel,
        textColor: C.white,
        lineColor: [30, 40, 60],
        lineWidth: 0.1,
        cellPadding: 2.5,
      },
      headStyles: {
        fillColor: [20, 28, 48],
        textColor: C.cyan,
        fontStyle: "bold",
        fontSize: 7,
      },
      columnStyles: {
        0: { halign: "center", cellWidth: 16 },
        3: { halign: "right",  cellWidth: 18 },
        4: { halign: "center", cellWidth: 18 },
        5: { halign: "center", cellWidth: 24 },
        6: { cellWidth: 28, fontSize: 6.5 },
      },
      didParseCell(data) {
        if (data.section === "body" && data.column.index === 5) {
          const status = data.cell.raw;
          data.cell.styles.textColor = statusColor(status);
          data.cell.styles.fontStyle = "bold";
        }
        if (data.section === "body" && data.column.index === 4) {
          const score = parseFloat(data.cell.raw);
          data.cell.styles.textColor = score >= 75 ? C.green : score >= 45 ? C.yellow : C.red;
          data.cell.styles.fontStyle = "bold";
        }
      },
      alternateRowStyles: { fillColor: [10, 14, 22] },
    });

    y = doc.lastAutoTable.finalY + 10;

    // ── NEW PAGE if needed ───────────────────────────────────────────────
    if (y > 230) { doc.addPage(); fillBg(); y = 20; }

    // ── CATEGORIES ───────────────────────────────────────────────────────
    y = sectionHeader("DATA CATEGORIES DETECTED", y);
    const catEntries = Object.entries(summary.categories_found);
    const colW = (W - 30) / Math.min(catEntries.length, 4);
    catEntries.forEach(([cat, count], i) => {
      if (i > 0 && i % 4 === 0) { y += 16; }
      const cx = 15 + (i % 4) * colW;
      doc.setFillColor(...C.panel);
      doc.roundedRect(cx, y, colW - 4, 12, 2, 2, "F");
      doc.setTextColor(...C.cyan);
      doc.setFont("helvetica", "bold");
      doc.setFontSize(12);
      doc.text(String(count), cx + 6, y + 8);
      doc.setTextColor(...C.gray);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7);
      doc.text(cat.toUpperCase(), cx + 14, y + 8);
    });
    y += 20;

    // ── RELATIONSHIPS ────────────────────────────────────────────────────
    if (relationships && relationships.length > 0) {
      if (y > 230) { doc.addPage(); fillBg(); y = 20; }
      y = sectionHeader("FRAGMENT RELATIONSHIPS", y);
      doc.autoTable({
        startY: y,
        margin: { left: 15, right: 15 },
        head: [["From", "To", "Reason", "Confidence"]],
        body: relationships.map(r => {
          const fn = fragments.find(f => f.id === r.from)?.name || `FRAG_${r.from}`;
          const tn = fragments.find(f => f.id === r.to)?.name   || `FRAG_${r.to}`;
          return [fn, tn, r.reason, r.confidence + "%"];
        }),
        styles: { fontSize: 7.5, fillColor: C.panel, textColor: C.white, lineColor: [30,40,60], lineWidth: 0.1, cellPadding: 2.5 },
        headStyles: { fillColor: [20,28,48], textColor: C.cyan, fontStyle: "bold", fontSize: 7 },
        alternateRowStyles: { fillColor: [10,14,22] },
      });
      y = doc.lastAutoTable.finalY + 10;
    }

    // ── AI ANALYSIS BLOCK ────────────────────────────────────────────────
    if (y > 220) { doc.addPage(); fillBg(); y = 20; }
    y = sectionHeader("AI ANALYSIS SUMMARY", y);

    const rate  = summary.recovery_rate_pct;
    const cats  = Object.keys(summary.categories_found).join(", ");
    const rVerb = rate >= 70 ? "HIGH confidence recovery"
                : rate >= 40 ? "MODERATE partial recovery"
                : "LOW — significant data loss";
    const aiText = [
      `Scan Target: ${meta.filename} (${meta.filesize_kb} KB)`,
      "",
      `RecoverAI identified ${summary.total_fragments} data segments using magic byte analysis and Shannon entropy scoring.`,
      `${summary.recoverable} fragments are fully recoverable, ${summary.partial} are partially intact,`,
      `and ${summary.critical} show critical corruption levels and are likely unrecoverable.`,
      "",
      `Overall Recovery Assessment: ${rVerb} — estimated ${rate}% of original data can be restored.`,
      `Categories detected: ${cats}.`,
      summary.top_priority_fragment ? `Highest-priority fragment: ${summary.top_priority_fragment}` : "",
      "",
      `Generated by RecoverAI v1.0 | Evidence integrity via SHA-256 | ${new Date(meta.scan_time).toLocaleString()}`,
    ].filter(l => l !== null);

    doc.setFillColor(...C.panel);
    const textBlockH = aiText.length * 5 + 10;
    doc.roundedRect(15, y, W - 30, textBlockH, 3, 3, "F");
    doc.setFillColor(...C.purple);
    doc.roundedRect(15, y, 3, textBlockH, 1, 1, "F");

    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    aiText.forEach((line, i) => {
      if (line === "") return;
      if (i === 0 || i === 6) {
        doc.setTextColor(...C.white);
        doc.setFont("helvetica", "bold");
      } else if (i === aiText.length - 1) {
        doc.setTextColor(...C.gray);
        doc.setFont("helvetica", "italic");
      } else {
        doc.setTextColor(...C.white);
        doc.setFont("helvetica", "normal");
      }
      doc.text(line, 22, y + 7 + i * 5);
    });

    // ── FOOTER (all pages) ───────────────────────────────────────────────
    const totalPages = doc.internal.getNumberOfPages();
    for (let p = 1; p <= totalPages; p++) {
      doc.setPage(p);
      doc.setFillColor(...C.panel);
      doc.rect(0, 287, W, 10, "F");
      doc.setFillColor(...C.cyan);
      doc.rect(0, 287, W, 0.5, "F");
      doc.setTextColor(...C.gray);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7);
      doc.text(`RecoverAI v1.0  ·  CalmStacks Hackathon 2026  ·  MCE Hassan  ·  Scan ID: ${currentReport.scan_id}`, 15, 293);
      doc.text(`Page ${p} of ${totalPages}`, W - 15, 293, { align: "right" });
    }

    // ── SAVE ─────────────────────────────────────────────────────────────
    doc.save(`RecoverAI_Forensic_Report_${currentReport.scan_id}.pdf`);

  } catch(err) {
    alert("PDF generation error: " + err.message);
    console.error(err);
  } finally {
    btn.textContent = "📄 Export PDF Report";
    btn.disabled = false;
  }
}

// ── Email Report Modal ──────────────────────────────────────────────────────
function showEmailReportModal() {
  if (!currentReport) { showToast("Run a scan first before emailing a report.", true); return; }

  const old = document.getElementById("emailReportModal");
  if (old) old.remove();

  const modal = document.createElement("div");
  modal.id = "emailReportModal";
  modal.style.cssText = `
    position:fixed;inset:0;z-index:2000;background:rgba(10,0,0,0.82);
    backdrop-filter:blur(12px);display:flex;align-items:center;justify-content:center;
    animation:fadeUp 0.3s ease;
  `;
  modal.innerHTML = `
    <div style="
      background:rgba(22,4,6,0.97);border:1px solid rgba(255,138,101,0.4);
      border-radius:18px;padding:28px 32px;width:min(460px,92vw);
      box-shadow:0 20px 64px rgba(0,0,0,0.85);
    ">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
        <span style="font-size:28px;">📧</span>
        <div>
          <div style="font-size:15px;font-weight:800;color:#FFF0F0;">Email Forensic Report</div>
          <div style="font-size:11px;color:#C8A0A0;margin-top:2px;">Send the full PDF report to your email</div>
        </div>
      </div>

      <div style="background:rgba(255,138,101,0.07);border:1px solid rgba(255,138,101,0.2);border-radius:10px;padding:10px 14px;margin-bottom:16px;font-size:11px;color:#C8A0A0;line-height:1.6;">
        📎 <strong style="color:#FF8A65;">Includes:</strong> Full PDF forensic report (fragment map, integrity scores,
        categories, relationships, AI analysis) for scan <strong style="color:#FFF0F0;">${currentReport.scan_id}</strong>
      </div>

      <label style="font-size:12px;color:#C8A0A0;font-weight:600;display:block;margin-bottom:6px;">📬 Recipient Email</label>
      <input id="emailReportInput" type="email" placeholder="Enter email address"
        style="
          width:100%;padding:10px 14px;border-radius:10px;border:1px solid rgba(255,138,101,0.3);
          background:rgba(255,255,255,0.05);color:#FFF0F0;font-size:13px;
          font-family:inherit;outline:none;margin-bottom:16px;transition:border-color 0.2s;
        "
        onfocus="this.style.borderColor='rgba(255,138,101,0.8)'"
        onblur="this.style.borderColor='rgba(255,138,101,0.3)'"
      />
      <div style="display:flex;gap:10px;">
        <button id="sendReportBtn" onclick="emailReport()"
          style="
            flex:1;padding:11px;border-radius:10px;border:none;
            background:linear-gradient(135deg,#CC0018,#FF8A65);
            color:#fff;font-weight:700;font-size:13px;cursor:pointer;transition:opacity 0.2s;
          "
          onmouseover="this.style.opacity='0.85'" onmouseout="this.style.opacity='1'"
        >📨 Generate PDF &amp; Send</button>
        <button onclick="document.getElementById('emailReportModal').remove();"
          style="
            padding:11px 20px;border-radius:10px;border:1px solid rgba(255,138,101,0.25);
            background:transparent;color:#C8A0A0;font-weight:600;font-size:13px;cursor:pointer;
          "
        >Cancel</button>
      </div>
      <div id="emailReportStatus" style="margin-top:12px;font-size:12px;text-align:center;min-height:18px;"></div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener("click", e => { if (e.target === modal) modal.remove(); });
  setTimeout(() => document.getElementById("emailReportInput")?.focus(), 100);
}

async function emailReport() {
  if (!currentReport) return;

  const emailInput = document.getElementById("emailReportInput");
  const status     = document.getElementById("emailReportStatus");
  const sendBtn    = document.getElementById("sendReportBtn");
  const email      = emailInput?.value?.trim();

  if (!email || !email.includes("@")) {
    if (emailInput) emailInput.style.borderColor = "rgba(255,23,68,0.9)";
    if (status) status.innerHTML = `<span style="color:#FF1744;">⚠ Enter a valid email address</span>`;
    return;
  }

  if (sendBtn) { sendBtn.disabled = true; sendBtn.textContent = "⏳ Generating PDF..."; }
  if (status)  status.innerHTML = `<span style="color:#C8A0A0;">Building forensic report PDF...</span>`;

  try {
    // ── Generate PDF exactly like exportPDF() but return base64 ─────────────
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
    const W   = doc.internal.pageSize.getWidth();
    const { meta, summary, fragments, relationships } = currentReport;

    const C = {
      bg:[7,9,15], panel:[13,17,27], cyan:[6,182,212], blue:[59,130,246],
      green:[34,197,94], yellow:[245,158,11], red:[239,68,68],
      purple:[168,85,247], white:[226,232,240], gray:[100,116,139],
    };
    function fillBg() { doc.setFillColor(...C.bg); doc.rect(0,0,W,297,"F"); }
    fillBg();

    doc.setFillColor(...C.panel); doc.rect(0,0,W,38,"F");
    doc.setFillColor(...C.cyan);  doc.rect(0,0,W,2,"F");
    doc.setTextColor(...C.cyan); doc.setFont("helvetica","bold"); doc.setFontSize(22);
    doc.text("RecoverAI",15,16);
    doc.setFontSize(9); doc.setFont("helvetica","normal"); doc.setTextColor(...C.gray);
    doc.text("FORENSIC EDITION  |  AI-Powered Data Recovery Platform",15,22);
    doc.setFillColor(...C.cyan); doc.roundedRect(W-55,8,45,10,2,2,"F");
    doc.setTextColor(...C.bg); doc.setFont("helvetica","bold"); doc.setFontSize(8);
    doc.text(`SCAN: ${currentReport.scan_id}`,W-32.5,14.5,{align:"center"});
    doc.setTextColor(...C.gray); doc.setFont("helvetica","normal"); doc.setFontSize(8);
    doc.text(`Target: ${meta.filename}   |   Size: ${meta.filesize_kb} KB   |   Scanned: ${new Date(meta.scan_time).toLocaleString()}`,15,32);

    let y = 48;
    const cards = [
      {label:"Total Fragments",val:summary.total_fragments,   color:C.blue},
      {label:"Recoverable",    val:summary.recoverable,        color:C.green},
      {label:"Partial",        val:summary.partial,            color:C.yellow},
      {label:"Critical",       val:summary.critical,           color:C.red},
      {label:"Recovery Rate",  val:summary.recovery_rate_pct+"%",color:C.purple},
    ];
    const cw = (W-30)/5;
    cards.forEach((c,i)=>{
      const cx=15+i*cw;
      doc.setFillColor(...C.panel); doc.roundedRect(cx,y,cw-3,20,2,2,"F");
      doc.setFillColor(...c.color); doc.roundedRect(cx,y,cw-3,2,1,1,"F");
      doc.setTextColor(...c.color); doc.setFont("helvetica","bold"); doc.setFontSize(14);
      doc.text(String(c.val),cx+(cw-3)/2,y+11,{align:"center"});
      doc.setTextColor(...C.gray); doc.setFont("helvetica","normal"); doc.setFontSize(6.5);
      doc.text(c.label.toUpperCase(),cx+(cw-3)/2,y+17,{align:"center"});
    });
    y += 28;

    function sectionHeader(title,yPos){
      doc.setFillColor(...C.panel); doc.rect(15,yPos,W-30,8,"F");
      doc.setFillColor(...C.cyan);  doc.rect(15,yPos,3,8,"F");
      doc.setTextColor(...C.white); doc.setFont("helvetica","bold"); doc.setFontSize(9);
      doc.text(title,22,yPos+5.5);
      return yPos+12;
    }
    const statusColor=(s)=>s==="RECOVERABLE"?[34,197,94]:s==="PARTIAL"?[245,158,11]:[239,68,68];

    y = sectionHeader("FRAGMENT RECOVERY MAP",y);
    doc.autoTable({
      startY:y, margin:{left:15,right:15},
      head:[["Priority","Fragment","Type","Size","Integrity","Status","SHA-256"]],
      body:fragments.map(f=>[f.priority,f.name,f.type_name,f.size_kb+" KB",f.integrity.score+"%",f.integrity.status,f.sha256+"…"]),
      styles:{fontSize:7.5,fillColor:C.panel,textColor:C.white,lineColor:[30,40,60],lineWidth:0.1,cellPadding:2.5},
      headStyles:{fillColor:[20,28,48],textColor:C.cyan,fontStyle:"bold",fontSize:7},
      columnStyles:{0:{halign:"center",cellWidth:16},3:{halign:"right",cellWidth:18},4:{halign:"center",cellWidth:18},5:{halign:"center",cellWidth:24},6:{cellWidth:28,fontSize:6.5}},
      didParseCell(data){
        if(data.section==="body"&&data.column.index===5){data.cell.styles.textColor=statusColor(data.cell.raw);data.cell.styles.fontStyle="bold";}
        if(data.section==="body"&&data.column.index===4){const sc=parseFloat(data.cell.raw);data.cell.styles.textColor=sc>=75?C.green:sc>=45?C.yellow:C.red;data.cell.styles.fontStyle="bold";}
      },
      alternateRowStyles:{fillColor:[10,14,22]},
    });
    y = doc.lastAutoTable.finalY+10;

    if(y>230){doc.addPage();fillBg();y=20;}
    y = sectionHeader("DATA CATEGORIES DETECTED",y);
    const catEntries=Object.entries(summary.categories_found);
    const colW=(W-30)/Math.min(catEntries.length,4);
    catEntries.forEach(([cat,count],i)=>{
      if(i>0&&i%4===0){y+=16;}
      const cx=15+(i%4)*colW;
      doc.setFillColor(...C.panel);doc.roundedRect(cx,y,colW-4,12,2,2,"F");
      doc.setTextColor(...C.cyan);doc.setFont("helvetica","bold");doc.setFontSize(12);doc.text(String(count),cx+6,y+8);
      doc.setTextColor(...C.gray);doc.setFont("helvetica","normal");doc.setFontSize(7);doc.text(cat.toUpperCase(),cx+14,y+8);
    });
    y+=20;

    if(relationships&&relationships.length>0){
      if(y>230){doc.addPage();fillBg();y=20;}
      y=sectionHeader("FRAGMENT RELATIONSHIPS",y);
      doc.autoTable({
        startY:y,margin:{left:15,right:15},
        head:[["From","To","Reason","Confidence"]],
        body:relationships.map(r=>{const fn=fragments.find(f=>f.id===r.from)?.name||`FRAG_${r.from}`;const tn=fragments.find(f=>f.id===r.to)?.name||`FRAG_${r.to}`;return[fn,tn,r.reason,r.confidence+"%"];}),
        styles:{fontSize:7.5,fillColor:C.panel,textColor:C.white,lineColor:[30,40,60],lineWidth:0.1,cellPadding:2.5},
        headStyles:{fillColor:[20,28,48],textColor:C.cyan,fontStyle:"bold",fontSize:7},
        alternateRowStyles:{fillColor:[10,14,22]},
      });
      y=doc.lastAutoTable.finalY+10;
    }

    if(y>220){doc.addPage();fillBg();y=20;}
    y=sectionHeader("AI ANALYSIS SUMMARY",y);
    const rate=summary.recovery_rate_pct;
    const cats=Object.keys(summary.categories_found).join(", ");
    const rVerb=rate>=70?"HIGH confidence recovery":rate>=40?"MODERATE partial recovery":"LOW — significant data loss";
    const aiText=[
      `Scan Target: ${meta.filename} (${meta.filesize_kb} KB)`,"",
      `RecoverAI identified ${summary.total_fragments} data segments using magic byte analysis and Shannon entropy scoring.`,
      `${summary.recoverable} fragments are fully recoverable, ${summary.partial} are partially intact,`,
      `and ${summary.critical} show critical corruption levels and are likely unrecoverable.`,"",
      `Overall Recovery Assessment: ${rVerb} — estimated ${rate}% of original data can be restored.`,
      `Categories detected: ${cats}.`,
      summary.top_priority_fragment?`Highest-priority fragment: ${summary.top_priority_fragment}`:"","",
      `Generated by RecoverAI v1.0 | Evidence integrity via SHA-256 | ${new Date(meta.scan_time).toLocaleString()}`,
    ].filter(l=>l!==null);
    doc.setFillColor(...C.panel);
    const tbH=aiText.length*5+10;
    doc.roundedRect(15,y,W-30,tbH,3,3,"F");
    doc.setFillColor(...C.purple);doc.roundedRect(15,y,3,tbH,1,1,"F");
    doc.setFont("helvetica","normal");doc.setFontSize(8);
    aiText.forEach((line,i)=>{
      if(line==="")return;
      if(i===0||i===6){doc.setTextColor(...C.white);doc.setFont("helvetica","bold");}
      else if(i===aiText.length-1){doc.setTextColor(...C.gray);doc.setFont("helvetica","italic");}
      else{doc.setTextColor(...C.white);doc.setFont("helvetica","normal");}
      doc.text(line,22,y+7+i*5);
    });

    const totalPages=doc.internal.getNumberOfPages();
    for(let p=1;p<=totalPages;p++){
      doc.setPage(p);
      doc.setFillColor(...C.panel);doc.rect(0,287,W,10,"F");
      doc.setFillColor(...C.cyan);doc.rect(0,287,W,0.5,"F");
      doc.setTextColor(...C.gray);doc.setFont("helvetica","normal");doc.setFontSize(7);
      doc.text(`RecoverAI v1.0  ·  CalmStacks Hackathon 2026  ·  MCE Hassan  ·  Scan ID: ${currentReport.scan_id}`,15,293);
      doc.text(`Page ${p} of ${totalPages}`,W-15,293,{align:"right"});
    }

    // ── Convert to base64 and send to backend ────────────────────────────────
    const pdfBase64  = doc.output("datauristring").split(",")[1];
    const filename   = `RecoverAI_Forensic_Report_${currentReport.scan_id}.pdf`;

    if (sendBtn) sendBtn.textContent = "📤 Sending...";
    if (status)  status.innerHTML = `<span style="color:#C8A0A0;">⏳ Sending email with PDF attachment...</span>`;

    const res  = await fetch(`${API}/email-report`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, pdf_base64: pdfBase64, filename, scan_id: currentReport.scan_id })
    });
    const data = await res.json();

    if (data.success) {
      if (status) status.innerHTML = `<span style="color:#00F5A0;">✅ Report sent to ${data.sent_to}</span>`;
      if (sendBtn) { sendBtn.textContent = "✔ Sent!"; }
      setTimeout(() => document.getElementById("emailReportModal")?.remove(), 2500);
    } else {
      if (status) status.innerHTML = `<span style="color:#FF1744;">❌ ${data.error}</span>`;
      if (sendBtn) { sendBtn.disabled = false; sendBtn.textContent = "📨 Generate PDF & Send"; }
    }
  } catch(err) {
    if (status) status.innerHTML = `<span style="color:#FF1744;">❌ Error: ${err.message}</span>`;
    if (sendBtn) { sendBtn.disabled = false; sendBtn.textContent = "📨 Generate PDF & Send"; }
    console.error(err);
  }
}

// ── RESET ──────────────────────────────────────────────────────────────────
function resetScan() {
  currentReport   = null;
  fileInput.value = "";
  folderInput.value = "";
  dashboard.style.display     = "none";
  heroSection.style.display   = "";
  uploadSection.style.display = "";

  // Hide navbar action buttons
  const _ep2 = document.getElementById("exportPdfBtn");
  const _ec2 = document.getElementById("exportCsvBtn");
  const _ns2 = document.getElementById("newScanBtn");
  if (_ep2) _ep2.style.display = "none";
  if (_ec2) _ec2.style.display = "none";
  if (_ns2) _ns2.style.display = "none";
  allFragments = [];
  setMode("file");
  window.scrollTo(0, 0);
}

// Alias — both navbar btn and dashboard topbar btn call newScan()
const newScan = resetScan;

// ── RECOVERY MODAL ─────────────────────────────────────────────────────────
let _recoveryScanId  = null;
let _recoveryFragId  = null;
let _recoveryReady   = false;

function closeRecoveryModalDirect() {
  document.getElementById("recoveryModal").style.display = "none";
  _recoveryScanId = null;
  _recoveryFragId = null;
  _recoveryReady  = false;
}

async function openRecoveryModal(scanId, fragId) {
  _recoveryScanId = scanId;
  _recoveryFragId = fragId;
  _recoveryReady  = false;

  // Disable the download button until recovery log finishes
  const _dlBtn = document.getElementById("activateAIBtn");
  if (_dlBtn) { _dlBtn.disabled = true; _dlBtn.textContent = "⏳ Processing…"; }

  // ── If this scan has a reconstruction, skip the modal and download directly ─
  if (currentReport && currentReport.reconstructions && currentReport.reconstructions.length > 0) {
    const rec = currentReport.reconstructions[0];
    const dk  = rec.download_key;
    if (dk) {
      const a = document.createElement("a");
      a.href = `${API}/download-reconstruction/${dk}`;
      a.download = rec.name || "RECOVERED_PHOTO.jpg";
      a.click();
      return; // skip modal entirely
    }
  }

  // Reset modal state
  const modal = document.getElementById("recoveryModal");
  document.getElementById("recoveryLog").innerHTML = "";
  document.getElementById("recoveryActions").style.display  = "none";
  document.getElementById("recoveryWarning").style.display  = "none";
  document.getElementById("recoveryProgressBar").style.width = "0%";
  document.getElementById("recoveryProgressLabel").textContent = "Fetching fragment metadata…";
  document.getElementById("recoveryFragName").textContent = "Loading…";
  document.getElementById("rInfoType").textContent    = "—";
  document.getElementById("rInfoScore").textContent   = "—";
  document.getElementById("rInfoStatus").textContent  = "—";
  document.getElementById("rInfoEntropy").textContent = "—";

  modal.style.display = "flex";

  try {
    // 1. Fetch AI reconstruction log
    const res  = await fetch(`${API}/recover-log/${scanId}/${fragId}`);
    const data = await res.json();
    if (data.error) { alert(data.error); closeRecoveryModal(); return; }

    // Fill info bar
    document.getElementById("recoveryFragName").textContent  = data.frag_name;
    document.getElementById("rInfoType").textContent         = data.frag_type;
    document.getElementById("rInfoScore").textContent        = data.integrity.score + "%";
    document.getElementById("rInfoStatus").innerHTML =
      `<span class="status-badge ${data.integrity.color}">${data.integrity.status}</span>`;
    document.getElementById("rInfoEntropy").textContent = data.integrity.entropy;

    if (!data.recoverable) {
      document.getElementById("recoveryWarning").style.display = "block";
    }

    // 2. Animate AI steps
    const steps    = data.steps;
    const logEl    = document.getElementById("recoveryLog");
    const progBar  = document.getElementById("recoveryProgressBar");
    const progLbl  = document.getElementById("recoveryProgressLabel");

    for (let i = 0; i < steps.length; i++) {
      await new Promise(r => setTimeout(r, 280 + Math.random() * 180));
      const line = document.createElement("div");
      line.className = "rlog-line";
      line.textContent = steps[i];
      logEl.appendChild(line);
      logEl.scrollTop = logEl.scrollHeight;

      const pct = Math.round(((i + 1) / steps.length) * 90);
      progBar.style.width = pct + "%";
      progLbl.textContent = `Processing… ${pct}%`;
    }

    // Final
    progBar.style.width = "100%";
    progLbl.textContent = "✅ Recovery complete — ready to download!";
    _recoveryReady = true;

    document.getElementById("recoveryActions").style.display = "flex";

    // Enable the footer download button
    const _dlBtn2 = document.getElementById("activateAIBtn");
    if (_dlBtn2) { _dlBtn2.disabled = false; _dlBtn2.innerHTML = "&#11015;&#65039; Download Recovered File"; }

  } catch (err) {
    alert("Recovery error: " + err.message);
    closeRecoveryModal();
  }
}

function closeRecoveryModal(event) {
  // Only close if clicking the overlay backdrop (not the modal itself)
  if (event && event.target !== document.getElementById("recoveryModal")) return;
  document.getElementById("recoveryModal").style.display = "none";
  _recoveryScanId = null;
  _recoveryFragId = null;
  _recoveryReady  = false;
}

async function downloadRecoveredFile() {
  if (!_recoveryScanId || _recoveryFragId === null) return;

  const footerBtn = document.getElementById("activateAIBtn");
  if (footerBtn) { footerBtn.disabled = true; footerBtn.textContent = "\u23f3 Preparing download\u2026"; }

  try {
    const url = `${API}/recover/${_recoveryScanId}/${_recoveryFragId}`;
    const a   = document.createElement("a");
    a.href    = url;
    a.download = "";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    setTimeout(() => {
      if (footerBtn) { footerBtn.disabled = false; footerBtn.innerHTML = "&#11015;&#65039; Download Again"; }
    }, 1500);
  } catch (err) {
    alert("Download failed: " + err.message);
    if (footerBtn) { footerBtn.disabled = false; footerBtn.innerHTML = "&#11015;&#65039; Download Recovered File"; }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// ── GEMINI AI INTEGRATION ───────────────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════════════════

let _aiConfigured = false;

// ── Check AI status on page load ────────────────────────────────────────────
async function checkAIStatus() {
  try {
    const res  = await fetch(`${API}/ai-status`);
    const data = await res.json();
    _aiConfigured = data.configured;
    updateAIStatusPill(data.configured, data.model);
  } catch (e) {
    updateAIStatusPill(false, null);
  }
}

function updateAIStatusPill(active, modelName) {
  const dot  = document.getElementById("aiStatusDot");
  const text = document.getElementById("aiStatusText");
  if (!dot || !text) return;
  if (active) {
    dot.className  = "ai-status-dot active";
    const label = modelName ? modelName.replace("gemini-","").replace("-"," ").toUpperCase() : "GEMINI AI";
    text.textContent = "✨ " + label + ": ON";
    text.style.color = "var(--green)";
    const btn = document.getElementById("regenerateAIBtn");
    if (btn) btn.style.display = "inline-flex";
  } else {
    dot.className  = "ai-status-dot inactive";
    text.textContent = "AI: Click to activate";
    text.style.color = "var(--text2)";
  }
}

// ── AI Config Modal ──────────────────────────────────────────────────────────
function openAIConfig() {
  document.getElementById("aiConfigModal").classList.add("active");
  document.getElementById("aiConfigStatus").style.display = "none";
  document.getElementById("activateAIBtn").disabled = false;
  document.getElementById("activateAIBtn").innerHTML = "<span>✨</span> Activate Gemini AI";
}

function closeAIConfig(event) {
  if (event && event.target !== document.getElementById("aiConfigModal")) return;
  document.getElementById("aiConfigModal").classList.remove("active");
}

function toggleKeyVisibility() {
  const input = document.getElementById("geminiKeyInput");
  const btn   = document.getElementById("keyToggleBtn");
  if (input.type === "password") {
    input.type   = "text";
    btn.textContent = "Hide";
  } else {
    input.type   = "password";
    btn.textContent = "Show";
  }
}

async function activateGeminiAI() {
  const key = document.getElementById("geminiKeyInput").value.trim();
  if (!key) {
    showAIConfigStatus("Please enter your Gemini API key.", "error");
    return;
  }

  const btn = document.getElementById("activateAIBtn");
  btn.disabled = true;
  btn.innerHTML = "<span>⏳</span> Validating key…";

  try {
    const res  = await fetch(`${API}/ai-config`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ api_key: key }),
    });
    const data = await res.json();

    if (res.ok) {
      showAIConfigStatus("✅ Gemini AI activated! Model: " + (data.model || "gemini-2.0-flash"), "success");
      _aiConfigured = true;
      updateAIStatusPill(true, data.model);
      btn.innerHTML = "<span>✨</span> Activated!";
      // Auto-close after 1.5s and trigger summary if dashboard is open
      setTimeout(() => {
        document.getElementById("aiConfigModal").classList.remove("active");
        if (currentReport) requestGeminiSummary();
      }, 1500);
    } else {
      showAIConfigStatus("❌ " + (data.error || "Activation failed"), "error");
      btn.disabled = false;
      btn.innerHTML = "<span>✨</span> Try Again";
    }
  } catch (err) {
    showAIConfigStatus("❌ Could not reach backend: " + err.message, "error");
    btn.disabled = false;
    btn.innerHTML = "<span>✨</span> Activate Gemini AI";
  }
}

function showAIConfigStatus(msg, type) {
  const el = document.getElementById("aiConfigStatus");
  el.textContent  = msg;
  el.className    = "ai-config-status " + type;
  el.style.display = "block";
}

// ── Gemini Forensic Summary (typewriter effect) ──────────────────────────────
async function requestGeminiSummary() {
  if (!currentReport) return;
  if (!_aiConfigured) { openAIConfig(); return; }

  const scanId = currentReport.scan_id;
  const output = document.getElementById("geminiOutput");
  const text   = document.getElementById("geminiText");
  const badge  = document.getElementById("geminiLiveBadge");
  const aiBadge = document.getElementById("aiAnalysisBadge");

  // Show the output box, start animation
  output.style.display = "block";
  text.textContent  = "";
  badge.textContent = "GENERATING…";
  badge.className   = "gemini-live-badge";

  // Add blinking cursor
  const cursor = document.createElement("span");
  cursor.className = "gemini-cursor";
  text.appendChild(cursor);

  // Scroll into view
  setTimeout(() => output.scrollIntoView({ behavior: "smooth", block: "nearest" }), 100);

  try {
    // Use demo endpoint for DEMO0001, otherwise regular
    const endpoint = scanId === "DEMO0001"
      ? `${API}/ai-demo-summary`
      : `${API}/ai-summary/${scanId}`;

    const res  = await fetch(endpoint);
    const data = await res.json();

    if (!res.ok || data.error) {
      text.textContent = "⚠️ " + (data.error || "AI generation failed.");
      badge.textContent = "ERROR";
      return;
    }

    // Typewriter effect
    const fullText = data.summary || "";
    text.textContent = "";
    text.appendChild(cursor);
    await typewriterEffect(text, fullText, cursor);

    // Done
    badge.textContent = "✅ COMPLETE";
    badge.className   = "gemini-live-badge done";
    if (aiBadge) {
      aiBadge.textContent = "✨ POWERED BY GEMINI";
      aiBadge.style.background = "linear-gradient(135deg,rgba(168,85,247,0.25),rgba(99,102,241,0.25))";
      aiBadge.style.color = "var(--purple)";
      aiBadge.style.borderColor = "rgba(168,85,247,0.4)";
    }

  } catch (err) {
    text.textContent = "⚠️ Error: " + err.message;
    badge.textContent = "ERROR";
  }
}

async function typewriterEffect(container, fullText, cursor) {
  const chunkSize = 3; // characters per frame
  let i = 0;
  return new Promise(resolve => {
    function writeChunk() {
      if (i >= fullText.length) {
        // Remove cursor at end
        if (cursor.parentNode) cursor.parentNode.removeChild(cursor);
        resolve();
        return;
      }
      const chunk = fullText.slice(i, i + chunkSize);
      // Insert text before cursor
      container.insertBefore(document.createTextNode(chunk), cursor);
      i += chunkSize;
      // Scroll log
      const panel = document.getElementById("aiAnalysisPanel");
      if (panel) panel.scrollTop = panel.scrollHeight;
      requestAnimationFrame(writeChunk);
    }
    writeChunk();
  });
}

// ── Per-Fragment AI Recommendation ──────────────────────────────────────────
// Track which button opened the AI advice panel
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
    let res = await fetch(`${API}/ai-recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scan_id: scanId,
        frag_id: fragId,
        fragment: frag
      })
    });

    if (res.status === 404 || res.status === 405) {
      res = await fetch(`${API}/ai-recommend/${scanId}/${fragId}`);
    }

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
}

// ── Inject AI Advice buttons into fragment table rows ────────────────────────
function injectAIButtons(fragments) {
  document.querySelectorAll("#fragTableBody tr").forEach((tr, idx) => {
    const frag = fragments[idx];
    if (!frag) return;
    const td = tr.querySelector("td:last-child");
    if (!td) return;
    // Avoid duplicate buttons
    if (td.querySelector(".btn-ai-frag")) return;
    const aiBtn = document.createElement("button");
    aiBtn.className   = "btn-ai-frag";
    aiBtn.textContent = "✨ AI Advice";
    aiBtn.onclick = () => requestFragmentAI(
      currentReport?.scan_id || "DEMO0001", frag.id, aiBtn
    );
    td.appendChild(aiBtn);
  });
}

// ── Hook into renderDashboard to trigger AI features after render ─────────────
const _baseDashboard = renderDashboard;
renderDashboard = function(report) {
  _baseDashboard(report);
  // After the 2200ms loading delay + small buffer, fire AI hooks
  setTimeout(() => {
    injectAIButtons(report.fragments || []);
    if (_aiConfigured) requestGeminiSummary();
    else {
      const btn = document.getElementById("regenerateAIBtn");
      if (btn) btn.style.display = "inline-flex";
    }
  }, 2500);
};

// ── Also re-inject AI buttons when filter changes table ───────────────────────
const _baseFilter = filterFragments;
filterFragments = function(status, btn) {
  _baseFilter(status, btn);
  setTimeout(() => injectAIButtons(
    status === "all" ? allFragments : allFragments.filter(f => f.integrity.status === status)
  ), 50);
};

// ── Kick off AI status check immediately on page load ────────────────────────
checkAIStatus();



// ---------------------------------------------------------------------------
// -- REQUIREMENT PANELS (REQ 1�4) -------------------------------------------
// ---------------------------------------------------------------------------

const CATEGORY_ICONS = {
  image:"???", document:"??", database:"???", media:"??",
  archive:"??", data:"??", web:"??", binary:"??", unknown:"?"
};

// -- REQ 1: Reconstruction Pipeline -----------------------------------------
function renderReconPipeline(fragments) {
  const el = document.getElementById("reconPipeline");
  if (!el) return;
  // Sort by priority descending to show assembly order
  const sorted = [...fragments].sort((a, b) => b.priority - a.priority);
  if (!sorted.length) { el.innerHTML = '<div class="recon-empty">No fragments detected</div>'; return; }

  el.innerHTML = sorted.map((f, i) => {
    const st  = f.integrity.status;
    const cls = st === "RECOVERABLE" ? "ok" : st === "PARTIAL" ? "par" : "crit";
    const stLbl = st === "RECOVERABLE" ? "INTACT" : st === "PARTIAL" ? "PARTIAL" : "CORRUPT";
    const arrow = i < sorted.length - 1 ? `<div class="pipeline-arrow">?</div>` : "";
    return `
      <div class="pipeline-item">
        <div class="pipeline-order">${String(i+1).padStart(2,"0")}</div>
        <div class="pipeline-info">
          <div class="pipeline-name">${f.name}</div>
          <div class="pipeline-meta">
            ${f.type_name} � ${f.size_kb} KB � Entropy: ${f.integrity.entropy}
            � Offset: 0x${(f.offset || 0).toString(16).toUpperCase().padStart(8,"0")}
          </div>
        </div>
        <div class="pipeline-status ${cls}">${stLbl}</div>
      </div>${arrow}`;
  }).join("");
}

// -- REQ 2: Integrity Heatmap ------------------------------------------------
function renderIntegrityHeatmap(fragments) {
  const el = document.getElementById("integrityHeatmap");
  if (!el) return;
  if (!fragments.length) { el.innerHTML = '<div class="recon-empty">No fragments detected</div>'; return; }

  // Sort by score descending
  const sorted = [...fragments].sort((a, b) => b.integrity.score - a.integrity.score);
  el.innerHTML = sorted.map(f => {
    const pct = f.integrity.score;
    const cls = pct >= 70 ? "green" : pct >= 40 ? "amber" : "red";
    return `
      <div class="ih-row">
        <div class="ih-label" title="${f.name}">${f.name}</div>
        <div class="ih-bar-wrap">
          <div class="ih-bar ${cls}" style="width:${pct}%" data-pct="${pct}%"></div>
        </div>
      </div>`;
  }).join("");
}

// -- REQ 3: High-Value Asset Classification ----------------------------------
function renderHighValueAssets(fragments) {
  const el = document.getElementById("highValueList");
  if (!el) return;
  if (!fragments.length) { el.innerHTML = '<div class="recon-empty">No fragments detected</div>'; return; }

  // Priority scoring for high-value determination
  const HIGH_VALUE_CATS = { document:10, database:9, image:7, media:6, archive:5, data:4, web:3 };
  const scored = fragments.map(f => ({
    ...f,
    hvScore: (HIGH_VALUE_CATS[f.category] || 1) * (f.integrity.score / 100) * (f.priority / 100)
  })).sort((a, b) => b.hvScore - a.hvScore).slice(0, 6);

  el.innerHTML = scored.map((f, i) => {
    const integrity = f.integrity.score;
    const scoreCls  = integrity >= 70 ? "s-high" : integrity >= 40 ? "s-mid" : "s-low";
    const icon = CATEGORY_ICONS[f.category] || "??";
    const medals = ["??","??","??"];
    const rank = medals[i] || `#${i+1}`;
    return `
      <div class="hv-item">
        <div class="hv-rank">${rank}</div>
        <div class="hv-icon">${icon}</div>
        <div class="hv-info">
          <div class="hv-name">${f.name}</div>
          <div class="hv-type">${f.type_name} � Priority Score: ${f.priority}</div>
        </div>
        <div class="hv-score ${scoreCls}">${integrity}%</div>
      </div>`;
  }).join("");
}

// -- REQ 4: Investigative Decision Support ----------------------------------
function renderDecisionSupport(report) {
  const el = document.getElementById("decisionSupport");
  if (!el) return;
  const frags   = report.fragments || [];
  const summary = report.summary   || {};

  const canRestore  = frags.filter(f => f.integrity.status === "RECOVERABLE");
  const atRisk      = frags.filter(f => f.integrity.status === "PARTIAL");
  const lost        = frags.filter(f => f.integrity.status === "CRITICAL");
  const rate        = summary.recovery_rate_pct || 0;

  const topCan  = canRestore.slice(0, 3).map(f =>
    `<div class="decision-item"><span class="decision-dot">?</span><span><strong>${f.name}</strong> � ${f.type_name} (${f.integrity.score}% intact)</span></div>`
  ).join("") || '<div class="decision-item"><span class="decision-dot">�</span><span>No fully recoverable fragments</span></div>';

  const topRisk = atRisk.slice(0, 2).map(f =>
    `<div class="decision-item"><span class="decision-dot">??</span><span><strong>${f.name}</strong> � ${f.integrity.null_ratio}% null-byte corruption</span></div>`
  ).join("") || '<div class="decision-item"><span class="decision-dot">�</span><span>No partial fragments</span></div>';

  const topLost = lost.slice(0, 2).map(f =>
    `<div class="decision-item"><span class="decision-dot">?</span><span><strong>${f.name}</strong> � Integrity ${f.integrity.score}% (unrecoverable)</span></div>`
  ).join("") || '<div class="decision-item"><span class="decision-dot">�</span><span>No critically lost fragments</span></div>';

  el.innerHTML = `
    <div class="decision-stat-row">
      <div class="decision-stat">
        <div class="decision-stat-val ds-green">${canRestore.length}</div>
        <div class="decision-stat-lbl">Restorable</div>
      </div>
      <div class="decision-stat">
        <div class="decision-stat-val ds-amber">${atRisk.length}</div>
        <div class="decision-stat-lbl">At Risk</div>
      </div>
      <div class="decision-stat">
        <div class="decision-stat-val ds-red">${lost.length}</div>
        <div class="decision-stat-lbl">Lost</div>
      </div>
    </div>

    <div>
      <div class="decision-section-title">? Can Be Restored</div>
      <div class="decision-can">${topCan}</div>
    </div>
    <div>
      <div class="decision-section-title">?? Partial Recovery Risk</div>
      <div class="decision-risk">${topRisk}</div>
    </div>
    <div>
      <div class="decision-section-title">? Likely Unrecoverable</div>
      <div class="decision-lost">${topLost}</div>
    </div>
    <div style="margin-top:6px;padding:10px 14px;border-radius:10px;background:rgba(6,182,212,0.05);border:1px solid rgba(6,182,212,0.2);font-size:12px;color:var(--text2)">
      <span style="color:var(--cyan);font-weight:700">?? Forensic Verdict:</span>
      ${rate >= 70
        ? `High confidence recovery (${rate}%). Recommend immediate extraction of priority fragments with SHA-256 verification.`
        : rate >= 40
        ? `Moderate recovery possible (${rate}%). Partial reconstruction viable � use AI-assisted header repair for PARTIAL fragments.`
        : `Severe corruption detected (${rate}% recovery rate). Preserve raw sector image before any recovery attempts to avoid further data loss.`
      }
    </div>`;
}

// -- Hook: populate all 4 panels after renderDashboard ----------------------
const _reqBase = renderDashboard;
renderDashboard = function(report) {
  _reqBase(report);
  setTimeout(() => {
    renderReconPipeline(report.fragments  || []);
    renderIntegrityHeatmap(report.fragments || []);
    renderHighValueAssets(report.fragments  || []);
    renderDecisionSupport(report);
  }, 300);
};


// =============================================================================
// DELETED FILE RECOVERY MODULE
// =============================================================================

const DELETED_CATEGORY_ICONS = {
  image: "\u{1F5BC}", document: "\u{1F4C4}", database: "\u{1F5C4}",
  media: "\u{1F3B5}", archive: "\u{1F4E6}", data: "\u{1F4CA}",
  web: "\u{1F310}", binary: "\u2699\uFE0F", unknown: "\u2753"
};

let _carveJobId  = null;
let _carvePollId = null;

function openDeletedRecovery() {
  document.getElementById("deletedSection").style.display = "block";
  document.getElementById("deletedSection").scrollIntoView({ behavior: "smooth" });
  loadDriveList();
}
function closeDeletedRecovery() {
  document.getElementById("deletedSection").style.display = "none";
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function switchDelTab(name, btn) {
  document.querySelectorAll(".del-tab").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".del-content").forEach(c => c.style.display = "none");
  btn.classList.add("active");
  document.getElementById("delContent-" + name).style.display = "block";
}

// Drive list
async function loadDriveList() {
  try {
    const res    = await fetch(`${API}/deleted/drives`);
    const drives = await res.json();
    const sel    = document.getElementById("driveSelect");
    if (!drives.length) return;
    sel.innerHTML = drives.map(d =>
      `<option value="${d.letter}">${d.letter}:\\ &mdash; ${d.total_gb} GB total, ${d.free_gb} GB free</option>`
    ).join("");
  } catch (e) { /* silent */ }
}

// Recycle Bin scanner
async function scanRecycleBin() {
  const btn    = document.getElementById("scanRecycleBtn");
  const info   = document.getElementById("recycleInfo");
  const res_el = document.getElementById("recycleResults");

  btn.disabled = true;
  btn.innerHTML = "&#9203; Scanning...";
  info.textContent = "Reading Recycle Bin entries...";
  res_el.innerHTML = "";

  try {
    const res  = await fetch(`${API}/deleted/recycle-bin`);
    const data = await res.json();
    btn.disabled = false;
    btn.innerHTML = "&#128269; Scan Recycle Bin";

    if (data.error) {
      info.textContent = "Error: " + data.error;
      return;
    }

    if (!data.items || data.items.length === 0) {
      info.textContent = "Recycle Bin is empty or no readable items found.";
      res_el.innerHTML = `<div class="del-empty"><div class="del-empty-icon">&#128465;</div>Recycle Bin is empty or all items are protected</div>`;
      return;
    }

    info.textContent = `Found ${data.count} deleted file(s) \u2014 click Restore to recover`;
    res_el.innerHTML = `<div class="del-results-grid">${data.items.map(buildDelCard).join("")}</div>`;
  } catch (e) {
    btn.disabled = false;
    btn.innerHTML = "&#128269; Scan Recycle Bin";
    info.textContent = "Error: " + e.message;
  }
}

// Drive carver
async function startDriveCarve() {
  const drive  = document.getElementById("driveSelect").value;
  const btn    = document.getElementById("startCarveBtn");
  const prog   = document.getElementById("carveProgress");
  const stats  = document.getElementById("carveStats");
  const res_el = document.getElementById("carveResults");

  if (_carvePollId) { clearInterval(_carvePollId); _carvePollId = null; }

  btn.disabled = true;
  btn.innerHTML = "&#9203; Starting...";
  prog.style.display = "block";
  res_el.innerHTML = "";
  stats.textContent = "Launching drive scan...";

  // Hide admin notice once scan starts
  const notice = document.getElementById("adminNotice");
  if (notice) notice.style.display = "none";

  try {
    const r = await fetch(`${API}/deleted/start-carve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ drive })
    });
    const data = await r.json();

    if (!r.ok || data.error) {
      btn.disabled = false;
      btn.innerHTML = "&#128300; Start Deep Scan";
      if (notice) notice.style.display = "flex";
      stats.textContent = "Error: " + (data.error || "Failed to start");
      return;
    }

    _carveJobId = data.job_id;
    btn.disabled = false;
    btn.innerHTML = "&#9209; Stop";
    btn.onclick = stopCarve;

    _carvePollId = setInterval(() => pollCarveStatus(res_el, btn, stats), 1500);

  } catch (e) {
    btn.disabled = false;
    btn.innerHTML = "&#128300; Start Deep Scan";
    if (notice) notice.style.display = "flex";
    stats.textContent = "Error: " + e.message;
  }
}

function stopCarve() {
  if (_carvePollId) { clearInterval(_carvePollId); _carvePollId = null; }
  const btn = document.getElementById("startCarveBtn");
  btn.innerHTML = "&#128300; Start Deep Scan";
  btn.onclick = startDriveCarve;
}

async function pollCarveStatus(resEl, btn, statsEl) {
  if (!_carveJobId) return;
  try {
    const r    = await fetch(`${API}/deleted/carve-status/${_carveJobId}`);
    const data = await r.json();

    document.getElementById("carveProgressBar").style.width = (data.progress || 0) + "%";
    statsEl.textContent = `Scanned: ${data.scanned_mb || 0} MB  |  Found: ${data.found || 0} fragments  |  ${data.progress || 0}% complete`;

    if (data.status === "error") {
      clearInterval(_carvePollId); _carvePollId = null;
      statsEl.textContent = "Error: " + (data.error || "Scan error");
      btn.innerHTML = "&#128300; Start Deep Scan";
      btn.onclick = startDriveCarve;
      const notice = document.getElementById("adminNotice");
      if (notice) notice.style.display = "flex";
    } else if (data.status === "done") {
      clearInterval(_carvePollId); _carvePollId = null;
      btn.innerHTML = "&#128300; Start Deep Scan";
      btn.onclick = startDriveCarve;
      statsEl.textContent = `Scan complete \u2014 ${data.found} deleted fragments found`;
      if (data.results && data.results.length) {
        resEl.innerHTML = `<div class="del-results-grid">${data.results.map(buildDelCard).join("")}</div>`;
      } else {
        resEl.innerHTML = `<div class="del-empty"><div class="del-empty-icon">&#128189;</div>No deleted files found in free space</div>`;
      }
    }
  } catch(e) { /* silent poll failure */ }
}

// Temp artifacts scanner
async function scanArtifacts() {
  const btn    = document.getElementById("scanArtifactsBtn");
  const res_el = document.getElementById("artifactsResults");

  btn.disabled = true;
  btn.innerHTML = "&#9203; Scanning...";
  res_el.innerHTML = "";

  try {
    const res  = await fetch(`${API}/deleted/artifacts`);
    const data = await res.json();
    btn.disabled = false;
    btn.innerHTML = "&#128193; Scan Temp &amp; Cache";

    if (!data.items || data.items.length === 0) {
      res_el.innerHTML = `<div class="del-empty"><div class="del-empty-icon">&#128193;</div>No recoverable artifacts found</div>`;
      return;
    }

    res_el.innerHTML = `<div class="del-results-grid">${data.items.map(buildDelCard).join("")}</div>`;
  } catch (e) {
    btn.disabled = false;
    btn.innerHTML = "&#128193; Scan Temp &amp; Cache";
  }
}

// Global registry: stores full item data so onclick handlers never embed raw paths in HTML
window._delItemRegistry = window._delItemRegistry || {};

// Build a deleted file card
function buildDelCard(item) {
  const score  = item.integrity?.score || 0;
  const status = item.integrity?.status || "UNKNOWN";
  const barCls = score >= 70 ? "green" : score >= 40 ? "amber" : "red";
  const icon   = DELETED_CATEGORY_ICONS[item.category] || "&#128193;";
  const src    = item.source;

  const name = item.filename || item.original_path?.split(/[\\/]/).pop() || "unknown";

  const metaParts = [
    item.deleted_at  ? "Deleted: " + item.deleted_at   : null,
    item.modified    ? "Modified: " + item.modified     : null,
    item.location    ? "\u{1F4CD} " + item.location     : null,
    item.drive       ? "Drive: " + item.drive + ":"     : null,
    item.offset_hex  ? "Offset: " + item.offset_hex     : null,
    item.size_kb + " KB \u00B7 " + item.type_name,
  ].filter(Boolean).join(" \u00B7 ");

  // Store item in registry — avoids embedding Windows paths in onclick strings
  window._delItemRegistry[item.id] = item;

  // Store job id on window for save-all
  if (src === "drive_carve" && item.job_id) {
    window._lastCarveJobId = item.job_id;
  }

  const restoreBtn = (src === "recycle_bin" && item.r_path)
    ? `<button class="btn-restore" id="restoreBtn-${item.id}" onclick="restoreFileById(${item.id})">&#9851; Restore</button>`
    : (src === "temp_artifact" && item.original_path)
    ? `<button class="btn-restore" id="restoreBtn-${item.id}" onclick="downloadArtifactById(${item.id})">&#128190; Save to Desktop</button>`
    : `<button class="btn-restore" id="restoreBtn-${item.id}" onclick="extractSectorById(${item.id})">&#128229; Save Fragment</button>`;

  return `
    <div class="del-card">
      <div class="del-card-top">
        <div class="del-card-icon">${icon}</div>
        <div>
          <div class="del-card-name">${name}</div>
          <div class="del-card-meta">${metaParts}</div>
        </div>
      </div>
      <div class="del-card-bar-wrap">
        <div class="del-card-bar ${barCls}" style="width:${score}%"></div>
      </div>
      <div class="del-card-footer">
        <span class="del-card-sha">SHA-256: ${item.sha256 || "\u2014"} &middot; ${status}</span>
        <div class="del-card-actions">${restoreBtn}</div>
      </div>
    </div>`;
}

// Registry-based wrappers — look up item data safely, no path escaping in HTML
function restoreFileById(id) {
  const item = window._delItemRegistry[id];
  if (!item) return;
  restoreFile(item.r_path, item.filename || item.original_path?.split(/[\\/]/).pop() || "unknown", id);
}

function downloadArtifactById(id) {
  const item = window._delItemRegistry[id];
  if (!item) return;
  downloadArtifact(item.original_path, item.filename || item.original_path?.split(/[\\/]/).pop() || "unknown", id);
}

function extractSectorById(id) {
  const item = window._delItemRegistry[id];
  if (!item) return;
  extractSector(item.drive, item.offset || 0, item.size_kb || 8, item.filename || "FRAG.bin", id);
}

// Restore and download actions
async function restoreFile(rPath, name, id) {
  const btn = document.getElementById(`restoreBtn-${id}`);
  if (btn) { btn.disabled = true; btn.textContent = "Restoring..."; }
  try {
    const res  = await fetch(`${API}/deleted/restore`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ r_path: rPath, destination: "" })
    });
    const data = await res.json();
    if (data.success) {
      if (btn) { btn.className = "btn-restore done"; btn.textContent = "✔ Restored!"; }
      showEmailModal(data.restored_to, name);
    } else {
      if (btn) { btn.disabled = false; btn.textContent = "⟳ Restore"; }
      showToast("Restore failed: " + data.error, true);
    }
  } catch(e) {
    if (btn) { btn.disabled = false; btn.textContent = "⟳ Restore"; }
    showToast("Network error: " + e.message, true);
  }
}

// ── Email modal after restore ────────────────────────────────────────────────
function showEmailModal(restoredPath, filename) {
  // Remove any existing
  const old = document.getElementById("emailRestoreModal");
  if (old) old.remove();

  const modal = document.createElement("div");
  modal.id = "emailRestoreModal";
  modal.style.cssText = `
    position:fixed;inset:0;z-index:2000;background:rgba(10,0,0,0.82);
    backdrop-filter:blur(12px);display:flex;align-items:center;justify-content:center;
    animation:fadeUp 0.3s ease;
  `;
  modal.innerHTML = `
    <div style="
      background:rgba(22,4,6,0.97);border:1px solid rgba(255,60,60,0.35);
      border-radius:18px;padding:28px 32px;width:min(440px,92vw);
      box-shadow:0 20px 64px rgba(0,0,0,0.85);
    ">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
        <span style="font-size:24px;">✅</span>
        <div>
          <div style="font-size:15px;font-weight:800;color:#FFF0F0;">File Restored!</div>
          <div style="font-size:11px;color:#C8A0A0;margin-top:2px;word-break:break-all;">${filename}</div>
        </div>
      </div>
      <div style="font-size:11px;color:#6B3A3A;margin-bottom:18px;padding:8px 10px;background:rgba(255,60,60,0.07);border-radius:8px;font-family:monospace;">
        📁 ${restoredPath}
      </div>
      <div style="font-size:13px;color:#C8A0A0;margin-bottom:12px;font-weight:600;">
        📧 Send restored file to email?
      </div>
      <input id="emailRestoreInput" type="email" placeholder="Enter your email address"
        style="
          width:100%;padding:10px 14px;border-radius:10px;border:1px solid rgba(255,60,60,0.3);
          background:rgba(255,255,255,0.05);color:#FFF0F0;font-size:13px;
          font-family:inherit;outline:none;margin-bottom:14px;
          transition:border-color 0.2s;
        "
        onfocus="this.style.borderColor='rgba(255,60,60,0.7)'"
        onblur="this.style.borderColor='rgba(255,60,60,0.3)'"
      />
      <div style="display:flex;gap:10px;">
        <button onclick="sendRestoredByEmail('${restoredPath.replace(/\\/g,"\\\\").replace(/'/g,"\\'")}','${filename.replace(/'/g,"\\'")}');"
          style="
            flex:1;padding:10px;border-radius:10px;border:none;
            background:linear-gradient(135deg,#CC0018,#FF3A3A);
            color:#fff;font-weight:700;font-size:13px;cursor:pointer;
            transition:opacity 0.2s;
          "
          onmouseover="this.style.opacity='0.85'" onmouseout="this.style.opacity='1'"
          id="sendEmailBtn"
        >📨 Send Email</button>
        <button onclick="document.getElementById('emailRestoreModal').remove();"
          style="
            padding:10px 20px;border-radius:10px;border:1px solid rgba(255,60,60,0.25);
            background:transparent;color:#C8A0A0;font-weight:600;font-size:13px;cursor:pointer;
          "
        >Skip</button>
      </div>
      <div id="emailRestoreStatus" style="margin-top:10px;font-size:12px;text-align:center;"></div>
    </div>
  `;
  document.body.appendChild(modal);
  modal.addEventListener("click", e => { if (e.target === modal) modal.remove(); });
  setTimeout(() => document.getElementById("emailRestoreInput")?.focus(), 100);
}

async function sendRestoredByEmail(filePath, filename) {
  const emailInput = document.getElementById("emailRestoreInput");
  const status     = document.getElementById("emailRestoreStatus");
  const sendBtn    = document.getElementById("sendEmailBtn");
  const email      = emailInput?.value?.trim();

  if (!email || !email.includes("@")) {
    if (emailInput) emailInput.style.borderColor = "rgba(255,23,68,0.9)";
    if (status) status.innerHTML = `<span style="color:#FF1744;">⚠ Enter a valid email address</span>`;
    return;
  }

  if (sendBtn) { sendBtn.disabled = true; sendBtn.textContent = "Sending..."; }
  if (status)  status.innerHTML = `<span style="color:#C8A0A0;">⏳ Sending email...</span>`;

  try {
    const res  = await fetch(`${API}/deleted/send-email`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, file_path: filePath, filename })
    });
    const data = await res.json();
    if (data.success) {
      if (status) status.innerHTML = `<span style="color:#00F5A0;">✅ Email sent to ${data.sent_to}</span>`;
      if (sendBtn) { sendBtn.textContent = "✔ Sent!"; }
      setTimeout(() => document.getElementById("emailRestoreModal")?.remove(), 2500);
    } else {
      if (status) status.innerHTML = `<span style="color:#FF1744;">❌ ${data.error}</span>`;
      if (sendBtn) { sendBtn.disabled = false; sendBtn.textContent = "📨 Send Email"; }
    }
  } catch(e) {
    if (status) status.innerHTML = `<span style="color:#FF1744;">❌ Network error: ${e.message}</span>`;
    if (sendBtn) { sendBtn.disabled = false; sendBtn.textContent = "📨 Send Email"; }
  }
}

async function downloadArtifact(srcPath, name, id) {
  const btn = document.getElementById(`restoreBtn-${id}`);
  if (btn) { btn.disabled = true; btn.textContent = "Saving..."; }
  try {
    const res  = await fetch(`${API}/deleted/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: srcPath, name: name })
    });
    const data = await res.json();
    if (data.success) {
      if (btn) { btn.className = "btn-restore done"; btn.textContent = "Saved!"; }
      alert("File saved to Desktop:\n" + data.saved_to);
    } else {
      if (btn) { btn.disabled = false; btn.textContent = "Save to Desktop"; }
      alert("Error: " + data.error);
    }
  } catch(e) {
    if (btn) { btn.disabled = false; btn.textContent = "Save to Desktop"; }
  }
}

// ── Extract single raw sector fragment ──────────────────────────────────────
async function extractSector(drive, offset, sizeKb, filename, id) {
  const btn = document.getElementById(`restoreBtn-${id}`);
  if (btn) { btn.disabled = true; btn.textContent = "Saving..."; }
  try {
    const res  = await fetch(`${API}/deleted/extract-sector`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ drive, offset, size_kb: sizeKb, filename })
    });
    const data = await res.json();
    if (data.success) {
      if (btn) { btn.className = "btn-restore done"; btn.textContent = "Saved!"; }
      showToast("Saved to Desktop/RecoverAI_Extracted/" + filename);
    } else {
      if (btn) { btn.disabled = false; btn.textContent = "Save Fragment"; }
      showToast("Error: " + data.error, true);
    }
  } catch(e) {
    if (btn) { btn.disabled = false; btn.textContent = "Save Fragment"; }
    showToast("Network error: " + e.message, true);
  }
}

// ── Save ALL carved fragments at once ────────────────────────────────────────
async function saveAllCarved() {
  const jobId = window._lastCarveJobId;
  if (!jobId) {
    showToast("No completed scan found. Run a Drive Scan first.", true);
    return;
  }

  const btn = document.getElementById("saveAllCarvedBtn");
  if (btn) { btn.disabled = true; btn.textContent = "Saving all fragments..."; }

  try {
    const res  = await fetch(`${API}/deleted/save-all-carved`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: jobId })
    });
    const data = await res.json();
    if (btn) { btn.disabled = false; btn.textContent = "Save All to Desktop"; }
    if (data.success) {
      showToast(data.saved_count + " files saved to Desktop/RecoverAI_Extracted/");
    } else {
      showToast("Error: " + data.error, true);
    }
  } catch(e) {
    if (btn) { btn.disabled = false; btn.textContent = "Save All to Desktop"; }
    showToast("Network error: " + e.message, true);
  }
}

// ── Restore from recycle bin ─────────────────────────────────────────────────
async function restoreFile(rPath, name, id) {
  const btn = document.getElementById(`restoreBtn-${id}`);
  if (btn) { btn.disabled = true; btn.textContent = "Restoring..."; }
  try {
    const res  = await fetch(`${API}/deleted/restore`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ r_path: rPath, destination: "" })
    });
    const data = await res.json();
    if (data.success) {
      if (btn) { btn.className = "btn-restore done"; btn.textContent = "Restored!"; }
      showToast("File restored to: " + data.restored_to);
    } else {
      if (btn) { btn.disabled = false; btn.textContent = "Restore"; }
      showToast("Restore failed: " + data.error, true);
    }
  } catch(e) {
    if (btn) { btn.disabled = false; btn.textContent = "Restore"; }
  }
}

// ── Save artifact to desktop ─────────────────────────────────────────────────
async function downloadArtifact(srcPath, name, id) {
  const btn = document.getElementById(`restoreBtn-${id}`);
  if (btn) { btn.disabled = true; btn.textContent = "Saving..."; }
  try {
    const res  = await fetch(`${API}/deleted/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: srcPath, name: name })
    });
    const data = await res.json();
    if (data.success) {
      if (btn) { btn.className = "btn-restore done"; btn.textContent = "Saved!"; }
      showToast("Saved to Desktop: " + data.saved_to);
    } else {
      if (btn) { btn.disabled = false; btn.textContent = "Save to Desktop"; }
      showToast("Error: " + data.error, true);
    }
  } catch(e) {
    if (btn) { btn.disabled = false; btn.textContent = "Save to Desktop"; }
  }
}

// ── Toast notification ────────────────────────────────────────────────────────
function showToast(msg, isError) {
  let t = document.getElementById("recoverToast");
  if (!t) {
    t = document.createElement("div");
    t.id = "recoverToast";
    t.style.cssText = [
      "position:fixed","bottom:30px","right:30px","z-index:9999",
      "padding:14px 22px","border-radius:12px","font-size:13px",
      "font-family:var(--font)","max-width:360px","line-height:1.5",
      "box-shadow:0 8px 32px rgba(0,0,0,0.4)","transition:opacity 0.4s",
      "white-space:pre-line","cursor:pointer"
    ].join(";");
    t.onclick = () => { t.style.opacity = "0"; };
    document.body.appendChild(t);
  }
  t.style.background = isError ? "rgba(220,38,38,0.92)" : "rgba(22,163,74,0.92)";
  t.style.border     = isError ? "1px solid rgba(248,113,113,0.5)" : "1px solid rgba(74,222,128,0.5)";
  t.style.color      = "#fff";
  t.style.opacity    = "1";
  t.textContent      = msg;
  clearTimeout(t._tid);
  t._tid = setTimeout(() => { t.style.opacity = "0"; }, 5000);
}

// ── After drive scan finishes: inject Save All button + tag job id on items ──
const _origBuildDelCard = buildDelCard;
buildDelCard = function(item) {
  if (window._lastCarveJobId && item.source === "drive_carve") {
    item.job_id = window._lastCarveJobId;
  }
  return _origBuildDelCard(item);
};

// Hook poll to add Save All button when done
const _basePollCarve = pollCarveStatus;
pollCarveStatus = async function(resEl, btn, statsEl) {
  const prevStatus = window._lastCarveStatus;
  await _basePollCarve(resEl, btn, statsEl);

  if (window._lastCarveJobId && !document.getElementById("saveAllCarvedBtn")) {
    const toolbar = document.querySelector("#delContent-carve .del-toolbar");
    if (toolbar) {
      const sab = document.createElement("button");
      sab.id        = "saveAllCarvedBtn";
      sab.className = "btn-primary";
      sab.style.cssText = "font-size:13px;padding:10px 22px;background:linear-gradient(135deg,#16a34a,#22c55e);box-shadow:0 4px 16px rgba(34,197,94,0.35)";
      sab.innerHTML = "&#128190; Save All to Desktop";
      sab.onclick   = saveAllCarved;
      toolbar.appendChild(sab);
    }
  }
};
