"""
append_extract_js.py — appends extractSector + saveAllCarved to app.js (UTF-8 safe)
"""

JS = """
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
"""

with open("frontend/app.js", "a", encoding="utf-8") as f:
    f.write(JS)

print("Done — extract JS appended.")
