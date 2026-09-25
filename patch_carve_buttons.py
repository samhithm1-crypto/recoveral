"""
patch_carve_buttons.py — patches the buildDelCard function in app.js
to show Save Fragment / Save All buttons for drive_carve results.
"""

PATCH_FIND = "const restoreBtn = (src === \"recycle_bin\" && item.r_path)"

PATCH_REPLACE = """// Store job id on window for save-all
  if (src === "drive_carve" && item.job_id) {
    window._lastCarveJobId = item.job_id;
  }

  const restoreBtn = (src === "recycle_bin" && item.r_path)"""

with open("frontend/app.js", encoding="utf-8", errors="replace") as f:
    content = f.read()

if PATCH_FIND not in content:
    print("ERROR: target string not found in app.js")
else:
    content = content.replace(PATCH_FIND, PATCH_REPLACE, 1)
    # Also fix the raw sector line
    OLD_RAW = ': `<span style="font-size:10px;color:var(--text3)">Raw sector &mdash; extract manually</span>`'
    NEW_RAW = ''': `<button class="btn-restore" id="restoreBtn-${item.id}"
        onclick="extractSector('${item.drive}',${item.offset || 0},${item.size_kb || 8},'${(item.filename||"FRAG.bin").replace(/'/g,"\\\\'")}',${item.id})">
        &#128229; Save Fragment</button>`'''
    content = content.replace(OLD_RAW, NEW_RAW, 1)
    with open("frontend/app.js", "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched successfully")
