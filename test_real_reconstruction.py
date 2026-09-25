"""
Test the real CalmStacks fragment reconstruction.
Looks for the actual .bin files in the project or asks to specify.
"""
import os, hashlib, sys
sys.path.insert(0, r"e:\hack project")
from fragment_reconstructor import reconstruct_from_fragments

# Try to find the test folder
search_roots = [
    r"e:\hack project\demo_files",
    r"e:\hack project\uploads",
    r"e:\hack project",
    r"e:\CalmStacks",
    r"C:\Users\samhi\Desktop",
    r"C:\Users\samhi\Downloads",
]

file_map = {}
for root in search_roots:
    if not os.path.exists(root):
        continue
    for fname in os.listdir(root):
        low = fname.lower()
        if "fragment" in low and low.endswith(".bin"):
            with open(os.path.join(root, fname), "rb") as f:
                file_map[fname] = f.read()
            print("Found fragment:", fname, "(", len(file_map[fname]), "bytes )")
        elif "manifest" in low and low.endswith(".json"):
            with open(os.path.join(root, fname), "rb") as f:
                file_map[fname] = f.read()
            print("Found manifest:", fname)

if len(file_map) < 2:
    print("ERROR: Could not find fragment files. Please specify the folder.")
    sys.exit(1)

print("\n--- Running Reconstruction ---")
results = reconstruct_from_fragments(file_map)
print("Groups found:", len(results))

for rec in results:
    print("\nName:", rec["name"])
    print("Size:", rec["size_kb"], "KB")
    print("Frags:", rec["fragment_count"], "->", rec["fragment_names"])
    print("SHA-256:", rec["sha256"])
    print("Manifest match:", rec["manifest_match"])
    print("First 4 bytes:", [hex(b) for b in rec["data"][:4]])
    print("Last 4 bytes: ", [hex(b) for b in rec["data"][-4:]])
    print("Log:")
    for line in rec["log"]:
        print(" ", line)

    # Save it to test
    out_path = r"e:\hack project\test_reconstruction_output.jpg"
    with open(out_path, "wb") as f:
        f.write(rec["data"])
    print("\nSaved to:", out_path)
    print("File size on disk:", os.path.getsize(out_path), "bytes")
