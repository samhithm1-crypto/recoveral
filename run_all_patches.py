"""
run_all_patches.py — run all JS patches in sequence, clean and append.
"""
import subprocess, sys

# 1. Remove old restoreFile/downloadArtifact from deleted module section
with open("frontend/app.js", encoding="utf-8", errors="replace") as f:
    content = f.read()

# Remove duplicate restoreFile that was in the old appended section (if present)
# The new ones in append_extract_js.py are the canonical versions
# Just trim at DELETED FILE RECOVERY MODULE marker and re-append cleanly
MARKER = "// =============================================================================\n// DELETED FILE RECOVERY MODULE"
cut = content.find(MARKER)
if cut != -1:
    base = content[:cut].rstrip()
    print(f"Trimmed at char {cut}")
else:
    base = content.rstrip()
    print("Marker not found, using full content")

with open("frontend/app.js", "w", encoding="utf-8") as f:
    f.write(base + "\n")

print("Base written. Now running append scripts...")

# 2. Append deleted module
exec(open("append_deleted_js.py").read())

# 3. Append extract functions
exec(open("append_extract_js.py").read())

print("All done!")
