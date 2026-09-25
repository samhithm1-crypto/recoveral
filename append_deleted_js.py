"""
append_deleted_js.py — Appends the deleted recovery JS module to app.js
using Python (utf-8 safe, no PowerShell encoding issues).
"""

DELETED_JS = r"""
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

  const safeRPath   = item.r_path         ? item.r_path.replace(/\\/g, "\\\\").replace(/'/g, "\\'") : "";
  const safeOrigPath= item.original_path  ? item.original_path.replace(/\\/g, "\\\\").replace(/'/g, "\\'") : "";

  const restoreBtn = (src === "recycle_bin" && item.r_path)
    ? `<button class="btn-restore" id="restoreBtn-${item.id}" onclick="restoreFile('${safeRPath}','${name.replace(/'/g,"\\'")}',${item.id})">&#9851; Restore</button>`
    : (src === "temp_artifact" && item.original_path)
    ? `<button class="btn-restore" id="restoreBtn-${item.id}" onclick="downloadArtifact('${safeOrigPath}','${name.replace(/'/g,"\\'")}',${item.id})">&#128190; Save to Desktop</button>`
    : `<span style="font-size:10px;color:var(--text3)">Raw sector &mdash; extract manually</span>`;

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
      if (btn) { btn.className = "btn-restore done"; btn.textContent = "Restored!"; }
      alert("File restored to:\n" + data.restored_to);
    } else {
      if (btn) { btn.disabled = false; btn.textContent = "Restore"; }
      alert("Restore failed: " + data.error);
    }
  } catch(e) {
    if (btn) { btn.disabled = false; btn.textContent = "Restore"; }
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
"""

with open("frontend/app.js", "a", encoding="utf-8") as f:
    f.write(DELETED_JS)

print("Done — deleted recovery JS appended cleanly.")
