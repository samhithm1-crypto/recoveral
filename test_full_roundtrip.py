"""Full round-trip test: upload fragments -> scan -> recover -> verify JPEG"""
import requests, os, sys

BASE = "http://localhost:5000"
FRAG_DIR = r"e:\hack project"
frag_files = []
for f in ["photo_fragment_01.bin", "photo_fragment_02.bin", "photo_fragment_03.bin"]:
    path = os.path.join(FRAG_DIR, f)
    if os.path.exists(path):
        frag_files.append(path)

if not frag_files:
    print("ERROR: fragment files not found in", FRAG_DIR)
    sys.exit(1)

print(f"Using {len(frag_files)} fragment files")

# --- 1. Upload to /api/scan-folder ---
files = [("files", (os.path.basename(p), open(p, "rb"), "application/octet-stream")) for p in frag_files]
r = requests.post(f"{BASE}/api/scan-folder", files=files)
for _, (_, fh, _) in files: fh.close()

assert r.status_code == 200, f"Scan failed: {r.status_code} {r.text[:200]}"
data = r.json()
recons = data.get("report", {}).get("reconstructions", [])
scan_id = data["report"]["scan_id"]
print(f"Scan ID: {scan_id}")
print(f"Reconstructions: {len(recons)}")
assert len(recons) > 0, "No reconstructions found!"

rec = recons[0]
dk = rec["download_key"]
print(f"  Name: {rec['name']}  Size: {rec['size_kb']} KB  Key: {dk}")

# --- 2. Download via /api/download-reconstruction/<key> ---
r2 = requests.get(f"{BASE}/api/download-reconstruction/{dk}")
assert r2.status_code == 200, f"Download-reconstruction failed: {r2.status_code}"
data2 = r2.content
print(f"  /api/download-reconstruction -> {len(data2)} bytes, header: {[hex(b) for b in data2[:4]]}")
assert data2[:3] == bytes([0xFF, 0xD8, 0xFF]), "NOT a valid JPEG!"
assert data2[-2:] == bytes([0xFF, 0xD9]), "Missing JPEG footer!"
print("  ✅ Valid JPEG (header + footer verified)")

# --- 3. Download via /api/recover/<scan_id>/0 (the old button path) ---
r3 = requests.get(f"{BASE}/api/recover/{scan_id}/0")
assert r3.status_code == 200, f"Recover failed: {r3.status_code}"
data3 = r3.content
print(f"  /api/recover/{scan_id}/0 -> {len(data3)} bytes, header: {[hex(b) for b in data3[:4]]}")
assert data3[:3] == bytes([0xFF, 0xD8, 0xFF]), "OLD RECOVER ENDPOINT returned non-JPEG!"
assert data3[-2:] == bytes([0xFF, 0xD9]), "OLD RECOVER ENDPOINT: missing JPEG footer!"
print("  ✅ Old 'Recover' button also returns correct JPEG!")

# --- Verify they're the same file ---
assert data2 == data3, "MISMATCH: two endpoints returned different bytes!"
print("  ✅ Both endpoints return identical file")

print("\n🎉 ALL TESTS PASSED — the recovered image will be correct!")
