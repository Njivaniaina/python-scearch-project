import argparse
import os
from pathlib import Path
import sys
import requests

from dotenv import load_dotenv
from groq import Groq

from image_utils import analyser_image
from search import rechercher_web, resoudre_illustrations
from display import display_characteristics, display_web_results
from history import ajouter_entree, afficher_historique, afficher_entree, get_nom_entree, recherche_existe
from pdf_utils import generer_pdf_discussion

load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="Image analysis with Groq + DuckDuckGo")
    parser.add_argument("--image",      type=str,           help="Path to the image to analyze")
    parser.add_argument("--historique", action="store_true",help="Display all history")
    parser.add_argument("--detail",     type=str,           help="Display details of an entry by its name")
    args = parser.parse_args()

    # ── History mode ───────────────────────
    if args.historique:
        afficher_historique()
        return

    if args.detail:
        afficher_entree(args.detail)
        return

    # ── Analysis mode ──────────────────────────
    if not args.image:
        print("Error: --image is required. Ex: python3 main.py --image plant.jpg")
        sys.exit(1)

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY is missing in the .env file")
        sys.exit(1)

    if not Path(args.image).exists():
        print(f"Error: image not found -> {args.image}")
        sys.exit(1)

    client = Groq(api_key=api_key)

    try:
        # Image analysis
        print(f"\nAnalyzing image: {args.image} ...")
        analyse = analyser_image(client, args.image)

        # Check if it already exists in history
        nom = get_nom_entree(analyse)
        existant = recherche_existe(nom)
        if existant:
            print(f"\n[History] '{nom}' already analyzed on {existant['date']} - updating...")

        display_characteristics(analyse)

        # Web search (DDG only) - prefer nom_exact for precision
        search_query = analyse["requete_recherche"]
        if analyse.get("nom_exact"):
            search_query = analyse["nom_exact"]
        print(f"\nWeb search in progress (query: {search_query}) ...")
        resultats_web = rechercher_web(search_query)
        display_web_results(resultats_web)

        # Resolve illustrations from web results
        print("\nResolving illustrations ...")
        resultats_images = resoudre_illustrations(
            resultats_web,
            analyse.get("requete_recherche", ""),
            analyse.get("mots_cle_images", []),
            max_images=3,
        )

        # Display image results
        CYAN = "\033[96m"
        BOLD = "\033[1m"
        DIM = "\033[2m"
        RESET = "\033[0m"
        print(f"\n{CYAN}{BOLD}=== Image Results ==={RESET}")
        for i, r in enumerate(resultats_images, 1):
            label = r.get("titre", "Image")
            url = r.get("url", "")
            chemin = r.get("chemin", "")

            print(f"  {BOLD}[{i}]{RESET} {label}")
            if chemin:
                print(f"      Local : {chemin}")
            if url:
                print(f"      URL   : {DIM}{url}{RESET}")
        print(f"{CYAN}{BOLD}{'═' * 40}{RESET}")

        # No separate video search in this flow
        resultats_videos = []

        # Add to history
        ajouter_entree(analyse, resultats_web, resultats_images, resultats_videos)

        print(f"\nQuery used: {analyse['requete_recherche']}\n")

        # PDF Generation for discussable subjects
        if analyse.get("is_discussable"):
            generer_pdf_discussion(analyse, args.image, resultats_web, resultats_images, resultats_videos)

    except requests.exceptions.RequestException as e:
        print(f"\n[Error] Connection error while contacting the web or APIs: {e}")
        print("Please check your internet connection and try again.")
        sys.exit(1)
    except ValueError as e:
        print(f"\n[Error] Corrupted data or parsing error: {e}")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\n[Error] Application error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[Error] An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
