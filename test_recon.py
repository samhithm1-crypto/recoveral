import requests

frag1 = bytes([0xFF, 0xD8, 0xFF, 0xE0]) + b'A' * 3000
frag2 = b'B' * 3000
frag3 = b'C' * 3000 + bytes([0xFF, 0xD9])

files = [
    ('files', ('photo_fragment_01.bin', frag1, 'application/octet-stream')),
    ('files', ('photo_fragment_02.bin', frag2, 'application/octet-stream')),
    ('files', ('photo_fragment_03.bin', frag3, 'application/octet-stream')),
]

r = requests.post('http://localhost:5000/api/scan-folder', files=files)
data = r.json()
recons = data.get('report', {}).get('reconstructions', [])
print('Reconstructions found:', len(recons))
if recons:
    rec = recons[0]
    print('Name:', rec['name'], '| Size:', rec['size_kb'], 'KB | Frags:', rec['fragment_count'])
    print('Manifest match:', rec.get('manifest_match'))
    dk = rec.get('download_key')
    print('Download key:', dk)
    if dk:
        r2 = requests.get('http://localhost:5000/api/download-reconstruction/' + dk)
        print('Download status:', r2.status_code, 'Size:', len(r2.content), 'bytes')
        print('First 4 bytes (should be FF D8 FF E0):', [hex(b) for b in r2.content[:4]])
else:
    print('No recons. Summary:', data.get('report', {}).get('summary'))
