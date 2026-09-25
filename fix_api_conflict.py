"""fix_api_conflict.py — renames _API in ui.js to avoid const API duplicate from app.js"""
# ui.js already uses _API (not API), so no conflict. Just verify.
with open("frontend/app.js", encoding="utf-8", errors="replace") as f:
    app = f.read()
with open("frontend/ui.js", encoding="utf-8", errors="replace") as f:
    ui = f.read()

# Check for duplicate const API
import re
app_api = re.findall(r'const API\s*=', app)
ui_api  = re.findall(r'const API\s*=', ui)
print("app.js const API:", app_api)
print("ui.js  const API:", ui_api)

# Also verify /api/ai-chat in app.py
with open("app.py", encoding="utf-8", errors="replace") as f:
    apy = f.read()
print("ai-chat in app.py:", "/api/ai-chat" in apy)
print("chat() in ai_engine:", end=" ")
with open("ai_engine.py", encoding="utf-8", errors="replace") as f:
    ae = f.read()
print("def chat" in ae)
