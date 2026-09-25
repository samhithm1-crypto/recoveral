"""
restore_checkpoint_v3.py
========================
Run this script to instantly restore the project to the CHECKPOINT V3 save point.

Usage:
    python restore_checkpoint_v3.py

What it restores:
    - frontend/index.html
    - frontend/style.css
    - frontend/app.js
    - frontend/bg.png
    - app.py
    - ai_engine.py
    - deleted_recovery.py
    - analyzer.py
    - recovery_engine.py
    - fragment_reconstructor.py
"""
import shutil, os

SRC = "checkpoint_v3"
FILES = [
    ("index.html",           "frontend/index.html"),
    ("style.css",            "frontend/style.css"),
    ("app.js",               "frontend/app.js"),
    ("bg.png",               "frontend/bg.png"),
    ("app.py",               "app.py"),
    ("ai_engine.py",         "ai_engine.py"),
    ("deleted_recovery.py",  "deleted_recovery.py"),
    ("analyzer.py",          "analyzer.py"),
    ("recovery_engine.py",   "recovery_engine.py"),
    ("fragment_reconstructor.py", "fragment_reconstructor.py"),
]

for src_name, dest in FILES:
    src_path = os.path.join(SRC, src_name)
    if os.path.exists(src_path):
        os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else ".", exist_ok=True)
        shutil.copy2(src_path, dest)
        print(f"  ✅ Restored: {dest}")
    else:
        print(f"  ⚠️  Missing in checkpoint: {src_name}")

print("\n=== CHECKPOINT V3 RESTORED ===")
print("Run: python app.py")
print("Then open: http://localhost:5000")
