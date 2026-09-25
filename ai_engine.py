"""
RecoverAI — Gemini AI Engine  (google-genai SDK, supports AQ. keys)
Uses the new google.genai client which works with AI Studio AQ. keys.
"""

import os
import io
import json
import traceback

# ── API KEY STORAGE ───────────────────────────────────────────────────────────
_runtime_api_key = ""
_active_model    = None   # cached working model name

GEMINI_MODELS = [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.5-pro",
    "models/gemini-flash-latest",
    "models/gemini-3-flash-preview",
    "models/gemini-3.1-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

def _load_env_key() -> str:
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""

def get_api_key() -> str:
    return _runtime_api_key or os.environ.get("GEMINI_API_KEY", "") or _load_env_key()

def set_api_key(key: str):
    global _runtime_api_key
    _runtime_api_key = key.strip()

def is_configured() -> bool:
    return bool(get_api_key())


# ── CLIENT HELPER ─────────────────────────────────────────────────────────────
def _get_client():
    """Return a (client, model_name) tuple using the new google-genai SDK."""
    global _active_model
    key = get_api_key()
    if not key:
        return None, None
    try:
        from google import genai
        client = genai.Client(api_key=key)
        model  = _active_model or "gemini-2.0-flash"
        return client, model
    except ImportError:
        return None, None
    except Exception as e:
        print(f"[AI] Client error: {e}")
        return None, None

def _generate(prompt: str, max_tokens: int = 600, temperature: float = 0.4) -> str | None:
    """
    Run a text prompt through Gemini, trying models in priority order.
    Auto-discovers available models if the hardcoded list fails.
    Returns the response text or None on total failure.
    """
    global _active_model
    key = get_api_key()
    if not key:
        return None
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key)

        # Try cached model first
        models_to_try = list(dict.fromkeys(
            ([_active_model] if _active_model else []) + GEMINI_MODELS
        ))

        for model_name in models_to_try:
            if not model_name:
                continue
            try:
                resp = client.models.generate_content(
                    model    = model_name,
                    contents = prompt,
                    config   = types.GenerateContentConfig(
                        temperature       = temperature,
                        max_output_tokens = max_tokens,
                    ),
                )
                _active_model = model_name
                return resp.text
            except Exception as e:
                err = str(e)
                if "API_KEY_INVALID" in err or "PERMISSION_DENIED" in err:
                    return None
                continue

        # Auto-discover: list models from API and try text-capable ones
        try:
            for m in client.models.list():
                name = m.name
                if any(x in name for x in ("flash", "pro")) and "tts" not in name \
                        and "audio" not in name and "embed" not in name \
                        and "image" not in name and "live" not in name:
                    try:
                        resp = client.models.generate_content(
                            model    = name,
                            contents = prompt,
                            config   = types.GenerateContentConfig(
                                temperature=temperature, max_output_tokens=max_tokens
                            ),
                        )
                        _active_model = name
                        print(f"[AI] Auto-discovered model: {name}")
                        return resp.text
                    except Exception:
                        continue
        except Exception:
            pass

        return None
    except ImportError:
        print("[AI] google-genai not installed. Run: pip install google-genai")
        return None
    except Exception as e:
        print(f"[AI] _generate error: {e}")
        return None


# ── 1. FORENSIC SUMMARY ───────────────────────────────────────────────────────
def ai_forensic_summary(report: dict) -> str | None:
    """Generate a professional AI forensic narrative for the full scan."""
    frags = report.get("fragments", [])
    top5  = sorted(frags, key=lambda x: x["priority"], reverse=True)[:5]
    frag_summary = [
        {
            "name":      f["name"],
            "type":      f["type_name"],
            "integrity": f["integrity"]["score"],
            "status":    f["integrity"]["status"],
            "entropy":   f["integrity"]["entropy"],
            "size_kb":   f["size_kb"],
        }
        for f in top5
    ]
    meta    = report["meta"]
    summary = report["summary"]

    prompt = f"""You are an expert digital forensics analyst working with RecoverAI, an AI-powered data recovery system.

## Scan Report Data
- **Target File:** {meta['filename']} ({meta['filesize_kb']} KB)
- **Total Fragments Detected:** {summary['total_fragments']}
- **Recoverable:** {summary['recoverable']}
- **Partially Recoverable:** {summary['partial']}
- **Critical Loss (unrecoverable):** {summary['critical']}
- **Overall Recovery Rate:** {summary['recovery_rate_pct']}%
- **Data Categories Found:** {json.dumps(summary['categories_found'])}
- **Highest Priority Fragment:** {summary.get('top_priority_fragment', 'N/A')}

## Top Priority Fragments
{json.dumps(frag_summary, indent=2)}

## Your Task
Write a professional 4-paragraph forensic analysis. Cover:

**Paragraph 1 — Damage Assessment:** What type of corruption occurred? How severe is it based on entropy values and null-byte ratios?

**Paragraph 2 — Key Findings:** What data was found and what is its significance?

**Paragraph 3 — Recovery Priority Plan:** Which fragments to recover first and why? Mention the top priority fragment by name.

**Paragraph 4 — Risk & Evidence Integrity:** What risks exist for critical fragments? Comment on SHA-256 chain of custody and what may be permanently lost.

Use precise forensic terminology. Write in first-person as the AI analyst. NO bullet points or markdown headers — flowing professional paragraphs only. Under 350 words."""

    return _generate(prompt, max_tokens=600, temperature=0.4)


# ── 2. FRAGMENT CLASSIFICATION ─────────────────────────────────────────────────
def ai_classify_fragment(hex_sample: str, entropy: float, size_kb: float,
                          null_ratio: float) -> dict | None:
    """Ask Gemini to classify an ambiguous fragment from hex bytes + stats."""
    prompt = f"""You are a digital forensics binary analysis expert.

Analyze this file fragment and identify its type:
- First 64 bytes (hex): {hex_sample}
- Shannon Entropy: {entropy:.3f} (0=zeros, 8=random/encrypted)
- Fragment Size: {size_kb:.2f} KB
- Null Byte Ratio: {null_ratio:.1f}%

Respond ONLY with this JSON (no markdown, no explanation outside JSON):
{{
  "file_type": "human readable type name",
  "category": "image|document|database|media|archive|data|web|binary|unknown",
  "extension": "3-4 char extension without dot",
  "confidence": 0-100,
  "reasoning": "one sentence explaining why"
}}"""

    raw = _generate(prompt, max_tokens=200, temperature=0.1)
    if not raw:
        return None
    try:
        # Strip markdown fences if present
        if "```" in raw:
            for part in raw.split("```"):
                part = part.strip().lstrip("json").strip()
                if part.startswith("{"):
                    raw = part
                    break
        return json.loads(raw.strip())
    except Exception as e:
        print(f"[AI] JSON parse error in classify: {e}")
        return None


# ── 3. IMAGE VISION ANALYSIS ──────────────────────────────────────────────────
def ai_analyze_image(image_bytes: bytes, filename: str) -> str | None:
    """Use Gemini Vision to describe a recovered image."""
    key = get_api_key()
    if not key:
        return None
    try:
        from google import genai
        from google.genai import types
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        client = genai.Client(api_key=key)

        prompt = (
            f"This image '{filename}' was recovered from damaged storage media by RecoverAI forensic system. "
            f"Describe in 2-3 sentences: (1) what the image shows, (2) any visible corruption artifacts or glitches, "
            f"(3) how well-preserved it appears. Be concise and technical."
        )

        models_to_try = ([_active_model] + GEMINI_MODELS) if _active_model else GEMINI_MODELS
        for model_name in models_to_try:
            if not model_name:
                continue
            try:
                resp = client.models.generate_content(
                    model    = model_name,
                    contents = [prompt, img],
                    config   = types.GenerateContentConfig(
                        temperature=0.3, max_output_tokens=200
                    ),
                )
                return resp.text.strip()
            except Exception as e:
                if "API_KEY_INVALID" in str(e) or "PERMISSION_DENIED" in str(e):
                    return None
                continue
        return None
    except ImportError:
        return None
    except Exception as e:
        print(f"[AI] Image analysis error: {e}")
        return None


# ── 4. PER-FRAGMENT RECOMMENDATION ───────────────────────────────────────────
def ai_fragment_recommendation(frag: dict) -> str | None:
    """Generate a 2-sentence AI recovery recommendation for a specific fragment."""
    prompt = f"""You are a digital forensics AI. Give a concise 2-sentence recovery recommendation for this fragment.

Fragment: {frag['name']}
Type: {frag['type_name']}
Category: {frag['category']}
Integrity Score: {frag['integrity']['score']}%
Status: {frag['integrity']['status']}
Shannon Entropy: {frag['integrity']['entropy']}
Null Byte Corruption: {frag['integrity']['null_ratio']}%
Size: {frag['size_kb']} KB

Provide: (1) what the corruption pattern suggests, (2) the specific recovery action to take.
Be direct and technical. Under 60 words."""

    return _generate(prompt, max_tokens=120, temperature=0.3)


# ── 5. API KEY VALIDATION ──────────────────────────────────────────────────────
def validate_api_key(key: str) -> dict:
    """
    Test if the key works using the new google-genai SDK.
    Supports both AQ. (AI Studio) and AIza (Cloud) key formats.
    Auto-discovers working models from the API.
    Returns {"valid": bool, "model": str|None, "error": str|None}
    """
    global _active_model
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=key)

        # First try our known good list
        for model_name in GEMINI_MODELS:
            try:
                resp = client.models.generate_content(
                    model    = model_name,
                    contents = "Reply with exactly: OK",
                    config   = types.GenerateContentConfig(max_output_tokens=5),
                )
                _active_model = model_name
                print(f"[AI] Key validated! Active model: {model_name}")
                return {"valid": True, "model": model_name, "error": None}
            except Exception as e:
                err = str(e)
                if "API_KEY_INVALID" in err or "PERMISSION_DENIED" in err:
                    return {"valid": False, "model": None,
                            "error": "API key rejected by Google — please check and try again"}
                continue

        # Auto-discover: ask the API which models are available
        try:
            for m in client.models.list():
                name = m.name
                if any(x in name for x in ("flash", "pro")) and "tts" not in name \
                        and "audio" not in name and "embed" not in name \
                        and "image" not in name and "live" not in name:
                    try:
                        resp = client.models.generate_content(
                            model    = name,
                            contents = "Reply with exactly: OK",
                            config   = types.GenerateContentConfig(max_output_tokens=5),
                        )
                        _active_model = name
                        print(f"[AI] Auto-discovered model: {name}")
                        return {"valid": True, "model": name, "error": None}
                    except Exception:
                        continue
        except Exception as disc_err:
            print(f"[AI] Model discovery failed: {disc_err}")

        return {"valid": False, "model": None,
                "error": "No Gemini model is available for this key. Check your AI Studio quota."}
    except ImportError:
        return {"valid": False, "model": None,
                "error": "google-genai package not installed. Run: pip install google-genai"}
    except Exception as e:
        return {"valid": False, "model": None, "error": str(e)}


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
            prompt += f"\n\nCurrent scan context: {context}"
        prompt += f"\n\nUser: {message}"
        response = client.models.generate_content(model=model, contents=prompt)
        return response.text or "I could not generate a response. Please try again."
    except Exception as e:
        return f"AI error: {str(e)}"
