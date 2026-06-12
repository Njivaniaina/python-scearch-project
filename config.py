
# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
IMAGE_PATH = ""

# Groq LLM Prompt
# IMPORTANT:
# - You receive ONE user-uploaded image.
# - You CANNOT browse the live web. Do NOT invent URLs, dates, or facts.
# - ALL TEXT MUST BE IN ENGLISH.
# - discussion_theme MUST be exactly the subject's theme, not generic.
ANALYSIS_PROMPT = """
Analyze the uploaded image with strict academic rigor. Respond ONLY with valid JSON, no markdown, using this exact structure:
{
  "description": "2-3 sentences describing ONLY what is visible in the image. Do not invent details.",
  "objet_principal": "main object or subject visible in the image",
  "nom_exact": "The precise specific name (scientific or common) of the object/species/landmark. It is extremely important to provide the most exact name possible.",
  "categorie": "single word: animal, plant, furniture, clothing, food, place, artwork, vehicle, person, object",
  "attributs": ["visual attribute 1", "visual attribute 2", "visual attribute 3"],
  "couleurs_dominantes": ["primary color", "secondary color", "tertiary color"],
  "style": "visual style: photorealistic, cartoon, minimalist, vintage, abstract, sketch, digital art, impressionist",
  "mots_cles_recherche": ["keyword 1", "keyword 2", "keyword 3"],
  "requete_recherche": "concise query to search the web for this object",
  "confiance": 0.9,
  "is_discussable": true or false,
  "discussion_theme": "STRICTLY the educational theme of the image subject (e.g., 'Tropical Plant Biology', 'Renaissance Art Techniques', 'Canine Anatomy'). NOT generic. If uncertain, use the exact subject name.",

  "introduction": "2-3 paragraphs. Write this like the captivating opening of a nature/science documentary script.",
  "developpement": "4-5 paragraphs. The core documentary narrative covering its life, history, engineering, or significance.",
  "conclusion": "2-3 paragraphs concluding the documentary with a memorable final thought.",
  "partie_educative": [
    "Question: What is the primary subject of this image?",
    "Answer: The primary subject is [accurate answer].",
    "Question: What are the most notable visual characteristics?",
    "Answer: The most notable characteristics are [detailed answer]."
  ],
  "caracteristiques_detaillees": {
    "nom_scientifique": "only if 100% certain, else empty",
    "famille": "only if certain",
    "origine": "only if certain",
    "taille": "only if visible/certain",
    "couleur": "only visible colors",
    "duree_vie": "only if certain",
    "habitat": "only if certain",
    "regime": "only if certain",
    "particularites": ["only verified visible facts"]
  }
}

STRICT RULES:
1. Only state what you SEE or are HIGHLY CONFIDENT about. Uncertain fields = empty string or empty array.
2. discussion_theme MUST match the subject EXACTLY. No generic themes.
3. ALL TEXT FIELDS MUST BE IN ENGLISH.
4. Do NOT invent URLs, scientific names, dates, statistics, or uncertain facts.
5. Use academic, well-structured English with proper grammar.
6. confiance is a float 0.0-1.0 for identification certainty.
7. If the image is trivial with no educational value, set is_discussable to false and discussion_theme to empty string.
"""
