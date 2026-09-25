with open('frontend/app.js', encoding='utf-8', errors='replace') as f:
    content = f.read()

fixed = content.replace('"?? Start Deep Scan"', '"&#128300; Deep Scan"')
fixed = fixed.replace("'?? Start Deep Scan'", "'&#128300; Deep Scan'")
count = content.count('?? Start Deep Scan')
print(f'Fixed {count} occurrence(s)')

with open('frontend/app.js', 'w', encoding='utf-8') as f:
    f.write(fixed)
print('Done')
