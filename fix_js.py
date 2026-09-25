"""
fix_js.py — Rewrites the deleted recovery JS section of app.js with correct emoji/text.
Run once: python fix_js.py
"""
import re

JS_PATH = "frontend/app.js"

# Read existing file (with errors='replace' to handle garbled bytes)
with open(JS_PATH, encoding="utf-8", errors="replace") as f:
    content = f.read()

# Find the marker we inserted and strip everything after it
MARKER = "// ═══════════════════════════════════════════════════════════════════════════\n// ── DELETED FILE RECOVERY MODULE"
cut_idx = content.find(MARKER)
if cut_idx == -1:
    # Try alternate marker
    MARKER = "DELETED FILE RECOVERY MODULE"
    cut_idx = content.find(MARKER)
    if cut_idx != -1:
        # Back up to the start of that comment block
        cut_idx = content.rfind("//", 0, cut_idx)

if cut_idx == -1:
    print("ERROR: Could not find deletion marker in app.js")
    print("Last 200 chars:", content[-200:])
else:
    base = content[:cut_idx].rstrip()
    print(f"Cutting at char {cut_idx}, base length = {len(base)}")
    with open(JS_PATH, "w", encoding="utf-8") as f:
        f.write(base + "\n")
    print("Trimmed app.js successfully")
