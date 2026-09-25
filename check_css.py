import re

with open("frontend/app.js", encoding="utf-8", errors="replace") as f:
    js = f.read()
with open("frontend/style.css", encoding="utf-8", errors="replace") as f:
    css = f.read()

classes = set(re.findall(r'class=["\' `]([\w\s\-]+)["\' `]', js))
all_cls = set()
for c in classes:
    for part in c.split():
        if part: all_cls.add(part)

missing = sorted(c for c in all_cls if c and ("." + c) not in css)
print("Missing CSS classes from app.js:")
for m in missing:
    print(" ", m)
