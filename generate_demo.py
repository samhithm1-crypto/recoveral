"""
generate_demo.py  —  Creates sample 'corrupted' binary files for demo purposes.
Run once before the hackathon demo: python generate_demo.py
"""
import os, struct, random

os.makedirs("demo_files", exist_ok=True)

def corrupt(data: bytes, corruption: float = 0.15) -> bytes:
    """Randomly corrupt a portion of bytes to simulate storage damage."""
    arr = bytearray(data)
    n   = int(len(arr) * corruption)
    for _ in range(n):
        arr[random.randint(0, len(arr)-1)] = random.randint(0, 255)
    # Add null byte clusters (common in damaged sectors)
    for _ in range(5):
        start = random.randint(0, max(0, len(arr)-32))
        arr[start:start+random.randint(4, 16)] = b'\x00' * random.randint(4, 16)
    return bytes(arr)

# ── 1. Fake corrupted JPEG ──────────────────────────────────────────────────
jpeg_header = b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
jpeg_data   = jpeg_header + bytes(random.getrandbits(8) for _ in range(8000)) + b'\xFF\xD9'
with open("demo_files/photo_vacation.jpg.corrupted", "wb") as f:
    f.write(corrupt(jpeg_data, 0.10))
print("[OK] Created: photo_vacation.jpg.corrupted")

# ── 2. Fake corrupted PDF ───────────────────────────────────────────────────
pdf_content = b'%PDF-1.4\n1 0 obj\n<</Type /Catalog>>\nendobj\n'
pdf_content += b'2 0 obj\n<</Type /Page /MediaBox [0 0 612 792]>>\nendobj\n'
pdf_content += b'xref\n0 3\n0000000000 65535 f\n%%EOF'
pdf_data    = pdf_content + bytes(random.getrandbits(8) for _ in range(5000))
with open("demo_files/contract_2026.pdf.corrupted", "wb") as f:
    f.write(corrupt(pdf_data, 0.08))
print("[OK] Created: contract_2026.pdf.corrupted")

# ── 3. Fake corrupted disk image (mixed fragments) ─────────────────────────
# Simulates a disk sector dump with multiple file types embedded
disk = bytearray(b'\x00' * 65536)
# Embed JPEG at offset 0
jpeg_frag = corrupt(jpeg_header + bytes(random.getrandbits(8) for _ in range(4000)), 0.05)
disk[0:len(jpeg_frag)] = jpeg_frag
# Embed PDF at offset 10000
pdf_frag = corrupt(pdf_content + bytes(random.getrandbits(8) for _ in range(2000)), 0.07)
disk[10000:10000+len(pdf_frag)] = pdf_frag
# Embed SQLite at offset 25000
sqlite_frag = b'SQLite format 3\x00' + bytes(random.getrandbits(8) for _ in range(3000))
disk[25000:25000+len(sqlite_frag)] = corrupt(sqlite_frag, 0.12)
# Embed ZIP at offset 40000
zip_frag = b'PK\x03\x04\x14\x00\x00\x00' + bytes(random.getrandbits(8) for _ in range(2000))
disk[40000:40000+len(zip_frag)] = corrupt(zip_frag, 0.25)
# Embed MP3 at offset 55000
mp3_frag = b'ID3\x03\x00\x00\x00' + bytes(random.getrandbits(8) for _ in range(2000))
disk[55000:55000+len(mp3_frag)] = corrupt(mp3_frag, 0.15)

with open("demo_files/disk_image.img", "wb") as f:
    f.write(bytes(disk))
print("[OK] Created: disk_image.img (64 KB simulated disk with 5 embedded fragments)")

print("\n[DONE] Demo files ready in ./demo_files/")
print("   Upload any of these in RecoverAI to see recovery in action!")
