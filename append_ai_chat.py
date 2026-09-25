"""append_ai_chat.py — adds chat() to ai_engine.py and /api/ai-chat to app.py"""

CHAT_FUNC = '''

def chat(message: str, context: str = "") -> str:
    """General forensic AI chat via Gemini."""
    if not is_configured():
        return "AI is not configured. Please add your Gemini API key via the AI status button."
    try:
        client, model = _get_client()
        system = (
            "You are RecoverAI's expert forensic AI assistant, powered by Gemini. "
            "You help investigators understand data recovery, digital forensics, file carving, "
            "integrity scoring, and fragment reconstruction. Be clear, concise, and practical. "
            "Use markdown bold (**text**) for key terms. Keep responses to 2-3 paragraphs max. "
            "Always be supportive and solution-focused."
        )
        prompt = system
        if context:
            prompt += f"\\n\\nCurrent scan context: {context}"
        prompt += f"\\n\\nUser: {message}"
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text or "I could not generate a response. Please try again."
    except Exception as e:
        return f"AI error: {str(e)}"
'''

with open("ai_engine.py", "a", encoding="utf-8") as f:
    f.write(CHAT_FUNC)
print("ai_engine.py chat() added")

# Add /api/ai-chat endpoint to app.py
import re

with open("app.py", encoding="utf-8") as f:
    app_content = f.read()

# Check if already added
if "/api/ai-chat" in app_content:
    print("ai-chat endpoint already exists")
else:
    # Insert before # ─── AI CONFIG
    INSERT_BEFORE = "# ─── AI CONFIG ──"
    ENDPOINT = '''
@app.route("/api/ai-chat", methods=["POST"])
def ai_chat():
    """General Gemini AI chat for the AI Coach screen."""
    body    = request.get_json(silent=True) or {}
    message = body.get("message", "").strip()
    context = body.get("context", "").strip()
    if not message:
        return jsonify({"error": "No message provided"}), 400
    if not ai_engine.is_configured():
        return jsonify({"error": "AI not configured. Click the AI status button to add your API key."}), 400
    try:
        response = ai_engine.chat(message, context)
        return jsonify({"response": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


'''
    idx = app_content.find(INSERT_BEFORE)
    if idx == -1:
        app_content += ENDPOINT
        print("Appended to end of app.py")
    else:
        app_content = app_content[:idx] + ENDPOINT + app_content[idx:]
        print("Inserted before AI CONFIG section")

    with open("app.py", "w", encoding="utf-8") as f:
        f.write(app_content)

print("Done!")
