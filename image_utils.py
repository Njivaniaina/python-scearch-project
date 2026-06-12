import base64
import json
import re
from pathlib import Path

from config import GROQ_MODEL, ANALYSIS_PROMPT

# ─────────────────────────────────────────────
# Functions - image analysis
# ─────────────────────────────────────────────

# Extract file suffix to determine MIME type and validate the image
def encode_image(image_path):
    suffix = Path(image_path).suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png",  ".webp": "image/webp"}
    mime_type = mime_map.get(suffix, "image/jpeg")

    # Validate image is not corrupted before sending to API
    try:
        from PIL import Image as PILImage
        with PILImage.open(image_path) as img:
            img.verify()
    except Exception as e:
        raise ValueError(f"Image file is corrupted or unreadable: {image_path} ({e})")

    try:
        with open(image_path, "rb") as f:
            data = base64.b64encode(f.read()).decode("utf-8")
        if not data:
            raise ValueError(f"Image file is empty: {image_path}")
        return data, mime_type
    except ValueError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to read image '{image_path}': {e}")


# Send image to Groq LLM and parse the JSON response.
# Returns validated dict with fallback values for uncertain fields.
# Retries up to MAX_RETRIES times on transient failures.
MAX_RETRIES = 2

def analyser_image(client, image_path):
    image_data, mime_type = encode_image(image_path)

    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}"}},
                        {"type": "text", "text": ANALYSIS_PROMPT}
                    ]
                }],
                max_tokens=2048,
                temperature=0.1,
            )
            break
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            # Retry on transient errors (rate limit, timeout, connection)
            if any(kw in error_str for kw in ["rate", "timeout", "connection", "503", "429"]):
                import time
                wait = attempt * 3
                print(f"  [Retry {attempt}/{MAX_RETRIES}] API error: {e}. Retrying in {wait}s...")
                time.sleep(wait)
                continue
            # Non-transient error, fail immediately
            raise RuntimeError(f"Failed to communicate with Groq API: {e}")
    else:
        raise RuntimeError(f"Groq API failed after {MAX_RETRIES} retries: {last_error}")

    # Safely extract the response content
    if not response.choices:
        raise ValueError("Groq API returned an empty response (no choices)")

    raw = response.choices[0].message.content
    if not raw or not raw.strip():
        raise ValueError("Groq API returned an empty text response")
    raw = raw.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        data = json.loads(raw.strip())
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response from LLM: {e}\nRaw output: {raw[:200]}...")

    # ── Validation & sanitization ──────────────
    # Ensure required fields exist with safe defaults
    defaults = {
        "description": "",
        "objet_principal": data.get("nom_exact") or "objet non identifie",
        "nom_exact": "",
        "categorie": "object",
        "attributs": [],
        "couleurs_dominantes": [],
        "style": "",
        "mots_cles_recherche": [],
        "requete_recherche": data.get("objet_principal", "objet"),
        "confiance": 0.5,
        "is_discussable": False,
        "discussion_theme": "",
        "mots_cle_images": [],
        "mots_cle_videos": [],
        "upload_type": "primary",
        "comparison_note": "",
        "introduction": "",
        "developpement": "",
        "conclusion": "",
        "partie_educative": [],
        "caracteristiques_detaillees": {},
    }
    for key, default_val in defaults.items():
        if key not in data or data[key] is None:
            data[key] = default_val

    # Fallback: populate mots_cle_images and mots_cle_videos from mots_cles_recherche
    if not data.get("mots_cle_images") and data.get("mots_cles_recherche"):
        data["mots_cle_images"] = list(data["mots_cles_recherche"])
    if not data.get("mots_cle_videos") and data.get("mots_cles_recherche"):
        data["mots_cle_videos"] = list(data["mots_cles_recherche"])

    # Clamp confiance to [0, 1]
    try:
        data["confiance"] = max(0.0, min(1.0, float(data.get("confiance", 0.5))))
    except (TypeError, ValueError):
        data["confiance"] = 0.5

    # If nom_exact is present but confiance is very low, clear it to avoid hallucinations
    if data.get("nom_exact") and data.get("confiance", 1.0) < 0.4:
        data["nom_exact"] = ""

    # Sanitize texte fields to remove markdown artifacts
    for key in ["description", "introduction", "developpement", "conclusion", "discussion_theme"]:
        val = data.get(key, "")
        if isinstance(val, str):
            data[key] = re.sub(r'\*+', '', val).strip()

    # Ensure arrays are lists
    for key in ["attributs", "couleurs_dominantes", "mots_cles_recherche",
                "mots_cle_images", "mots_cle_videos", "partie_educative",
                "particularites"]:
        val = data.get(key, [])
        if not isinstance(val, list):
            data[key] = [str(val)] if val else []

    # Ensure caracteristiques_detaillees keys
    expected_caracs = ["nom_scientifique", "famille", "origine", "taille",
                       "couleur", "duree_vie", "habitat", "regime", "particularites"]
    caracs = data.get("caracteristiques_detaillees", {})
    if not isinstance(caracs, dict):
        caracs = {}
    for k in expected_caracs:
        if k not in caracs:
            caracs[k] = ""
    data["caracteristiques_detaillees"] = caracs

    return data
