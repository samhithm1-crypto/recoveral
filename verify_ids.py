"""verify_ids.py — checks every ID app.js needs is in index.html"""
import re

with open("frontend/app.js", encoding="utf-8", errors="replace") as f:
    js = f.read()
with open("frontend/index.html", encoding="utf-8", errors="replace") as f:
    html = f.read()

needed = sorted(set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", js)))
missing = [i for i in needed if f'id="{i}"' not in html]

print(f"Total IDs needed: {len(needed)}")
print(f"Missing from HTML: {len(missing)}")
if missing:
    for m in missing:
        print(" MISSING:", m)
else:
    print("ALL IDs PRESENT - everything should work!")
