import re
with open("frontend/app.js", encoding="utf-8", errors="replace") as f:
    content = f.read()
ids = sorted(set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", content)))
print("\n".join(ids))
