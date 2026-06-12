import json
from datetime import datetime
from pathlib import Path

HISTORIQUE_DIR = "history"
INDEX_FILE = "history/index.json"


# ─────────────────────────────────────────────
# Setup helpers
# ─────────────────────────────────────────────

def init_dossier():
    # Ensure the history directory exists.
    Path(HISTORIQUE_DIR).mkdir(exist_ok=True)


def get_nom_entree(analyse: dict) -> str:
    # Extract the canonical name from the analysis result.
    return analyse.get("nom_exact") or analyse.get("objet_principal", "inconnu")


def nom_vers_fichier(nom: str) -> str:
    # Convert a name to a safe JSON file path.
    nom_propre = nom.strip().replace(" ", "_").replace("/", "-")
    return f"{HISTORIQUE_DIR}/{nom_propre}.json"


# ─────────────────────────────────────────────
# Index management
# ─────────────────────────────────────────────

def charger_index() -> list:
    # Load the index of analyzed names.
    if not Path(INDEX_FILE).exists():
        return []
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def sauvegarder_index(index: list):
    # Persist the index of analyzed names.
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


# ─────────────────────────────────────────────
# Individual entry management
# ─────────────────────────────────────────────

def charger_entree(nom: str) -> dict | None:
    # Load a single history entry.
    chemin = nom_vers_fichier(nom)
    if not Path(chemin).exists():
        return None
    with open(chemin, "r", encoding="utf-8") as f:
        return json.load(f)


def sauvegarder_entree(entree: dict):
    # Save a single history entry.
    chemin = nom_vers_fichier(entree["nom"])
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(entree, f, ensure_ascii=False, indent=2)


def recherche_existe(nom: str) -> dict | None:
    # Return an existing entry if present.
    return charger_entree(nom)


# ─────────────────────────────────────────────
# Add / Update history
# ─────────────────────────────────────────────

def ajouter_entree(
    analyse: dict,
    resultats_web: list,
    resultats_images: list,
    resultats_videos: list | None = None,
):
    # Create or update a history entry for an analyzed image.
    if resultats_videos is None:
        resultats_videos = []

    init_dossier()
    nom = get_nom_entree(analyse)

    nouvelle_entree = {
        "nom":              nom,
        "objet_principal":  analyse.get("objet_principal"),
        "nom_exact":        analyse.get("nom_exact", ""),
        "categorie":        analyse.get("categorie"),
        "description":      analyse.get("description"),
        "attributs":        analyse.get("attributs", []),
        "mots_cles":        analyse.get("mots_cles_recherche", []),
        "requete":          analyse.get("requete_recherche"),
        "is_discussable":   analyse.get("is_discussable", False),
        "discussion_theme": analyse.get("discussion_theme", ""),
        "date":             datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resultats_web":    [{"titre": r.get("title"), "url": r.get("href")} for r in resultats_web],
        "resultats_images": [{"titre": r.get("titre"), "url": r.get("url")} for r in resultats_images],
        "resultats_videos": [{"titre": r.get("titre"), "url": r.get("url")} for r in resultats_videos],
    }
    sauvegarder_entree(nouvelle_entree)

    # Update index
    index = charger_index()
    if nom not in index:
        index.append(nom)
        sauvegarder_index(index)
        print(f"\n[History] New item : '{nom}' -> {nom_vers_fichier(nom)}")
    else:
        print(f"\n[History] Updated : '{nom}' -> {nom_vers_fichier(nom)}")


# ─────────────────────────────────────────────
# Display history
# ─────────────────────────────────────────────

def afficher_historique():
    # Print all analyzed items.
    index = charger_index()
    if not index:
        print("\nHistory is empty.")
        return

    print(f"\n=== History ({len(index)} item(s)) ===")
    for i, nom in enumerate(index, 1):
        entree = charger_entree(nom)
        if entree:
            print(f"\n[{i}] {entree['nom']}")
            print(f"     Category : {entree.get('categorie', '—')}")
            print(f"     Date     : {entree.get('date', '—')}")
            print(f"     File     : {nom_vers_fichier(nom)}")
    print("=" * 35)


def afficher_entree(nom: str):
    # Print details for a single history item.
    entree = charger_entree(nom)
    if not entree:
        print(f"\n[History] No entry found for : '{nom}'")
        return

    print(f"\n=== Details : {entree['nom']} ===")
    print(f"Object      : {entree.get('objet_principal')}")
    print(f"Exact name  : {entree.get('nom_exact') or '—'}")
    print(f"Category    : {entree.get('categorie')}")
    print(f"Discussable : {'Yes' if entree.get('is_discussable') else 'No'}")
    if entree.get("discussion_theme"):
        print(f"Theme       : {entree.get('discussion_theme')}")
    print(f"Description : {entree.get('description')}")
    print(f"Attributes  : {', '.join(entree.get('attributs', []))}")
    print(f"Date        : {entree.get('date')}")

    print("\n--- Web Results ---")
    for i, r in enumerate(entree.get("resultats_web", []), 1):
        print(f"  [{i}] {r.get('titre', '—')}")
        print(f"       {r.get('url', '—')}")

    print("\n--- Image Searches ---")
    for i, r in enumerate(entree.get("resultats_images", []), 1):
        print(f"  [{i}] {r.get('titre', '—')}")
        print(f"       {r.get('url', '—')}")

    videos = entree.get("resultats_videos", [])
    if videos:
        print("\n--- Video Searches ---")
        for i, r in enumerate(videos, 1):
            print(f"  [{i}] {r.get('titre', '—')}")
            print(f"       {r.get('url', '—')}")

    print("=" * 35)
