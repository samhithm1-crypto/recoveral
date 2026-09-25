import sys
sys.stdout.reconfigure(encoding='ascii', errors='replace')
with open('app.py', encoding='utf-8', errors='replace') as f:
    lines = f.readlines()

for i, l in enumerate(lines, 1):
    if 'import deleted_recovery' in l:
        print('import at line:', i)
    if '/api/deleted/drives' in l:
        print('deleted routes start at line:', i)
    if 'ai-chat' in l and 'route' in l.lower():
        print('ai-chat route at line:', i)
    if 'AI CONFIG' in l.upper() and '#' in l:
        print('AI CONFIG section at line:', i)

print('Total lines:', len(lines))
