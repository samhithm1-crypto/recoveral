"""
restore_checkpoint_v4.py
========================
Instantly restores the project to CHECKPOINT V4.

State at this checkpoint:
  ✅ Red & black theme with particle wave background
  ✅ Fragment scan + 4 forensic panels fully working
  ✅ Gemini AI (gemini-flash-lite) active
  ✅ Per-fragment AI Advice floating panel (no table misalignment)
  ✅ Recover Fragment modal + Download working
  ✅ newScan() button working (both navbar + dashboard topbar)
  ✅ Dashboard topbar with FORENSIC SCAN COMPLETE badge + New Scan
  ✅ Recycle Bin scanner + Restore
  ✅ Drive Scanner + Save All to Desktop
  ✅ Temp Artifacts scanner
  ✅ PDF + CSV export

Usage:
    python restore_checkpoint_v4.py
"""
import shutil, os

SRC   = "checkpoint_v4"
FILES = [
    ("index.html",                "frontend/index.html"),
    ("style.css",                 "frontend/style.css"),
    ("app.js",                    "frontend/app.js"),
    ("bg.png",                    "frontend/bg.png"),
    ("app.py",                    "app.py"),
    ("ai_engine.py",              "ai_engine.py"),
    ("deleted_recovery.py",       "deleted_recovery.py"),
    ("analyzer.py",               "analyzer.py"),
    ("recovery_engine.py",        "recovery_engine.py"),
    ("fragment_reconstructor.py", "fragment_reconstructor.py"),
]

for src_name, dest in FILES:
    src_path = os.path.join(SRC, src_name)
    if os.path.exists(src_path):
        os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else ".", exist_ok=True)
        shutil.copy2(src_path, dest)
        print(f"  ✅  {dest}")
    else:
        print(f"  ⚠️  Missing: {src_name}")

print("\n=== CHECKPOINT V4 RESTORED ===")
print("Run:  python app.py")
print("Open: http://localhost:5000")
