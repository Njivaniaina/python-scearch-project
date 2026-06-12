
# -----------------------------------------------------------------
# Display functions
# -----------------------------------------------------------------

import textwrap

# ANSI color constants
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _confidence_bar(score):
    # Render a visual confidence bar with color coding.
    filled = int(score * 10)
    empty = 10 - filled
    if score >= 0.8:
        color = GREEN
    elif score >= 0.5:
        color = YELLOW
    else:
        color = RED
    bar = f"{color}{'█' * filled}{DIM}{'░' * empty}{RESET}"
    return f"{bar} {BOLD}{score:.0%}{RESET}"


def display_characteristics(data):
    # Print analysis characteristics in a rich stylized block.
    print(f"\n{CYAN}{BOLD}╔══════════════════════════════════════╗{RESET}")
    print(f"{CYAN}{BOLD}║     ANALYSIS CHARACTERISTICS         ║{RESET}")
    print(f"{CYAN}{BOLD}╚══════════════════════════════════════╝{RESET}")

    print(f"  {BOLD}Object      :{RESET} {GREEN}{data['objet_principal']}{RESET}")
    print(f"  {BOLD}Category    :{RESET} {data['categorie']}")

    if data.get('nom_exact'):
        print(f"  {BOLD}Exact Name  :{RESET} {YELLOW}{data['nom_exact']}{RESET}")

    # Confidence bar
    conf = data.get('confiance', 0.5)
    print(f"  {BOLD}Confidence  :{RESET} {_confidence_bar(conf)}")

    # Theme
    theme = data.get('discussion_theme', '')
    if theme:
        print(f"  {BOLD}Theme       :{RESET} {MAGENTA}{theme}{RESET}")

    # Description (wrapped)
    print(f"  {BOLD}Description :{RESET}")
    desc_wrapped = textwrap.fill(data.get('description', ''), width=76, initial_indent="    ", subsequent_indent="    ")
    print(desc_wrapped)

    # Colors
    colors = data.get('couleurs_dominantes', [])
    if colors:
        print(f"  {BOLD}Colors      :{RESET} {', '.join(colors)}")

    print(f"  {BOLD}Attributes  :{RESET} {', '.join(data.get('attributs', []))}")
    print(f"  {BOLD}Keywords    :{RESET} {', '.join(data.get('mots_cles_recherche', []))}")

    # Scientific details (if available)
    caracs = data.get('caracteristiques_detaillees', {})
    sci_name = caracs.get('nom_scientifique', '')
    famille = caracs.get('famille', '')
    origine = caracs.get('origine', '')
    habitat = caracs.get('habitat', '')

    has_details = any([sci_name, famille, origine, habitat])
    if has_details:
        print(f"\n  {CYAN}{BOLD}── Scientific Details ──{RESET}")
        if sci_name:
            print(f"  {BOLD}Scientific  :{RESET} {DIM}{sci_name}{RESET}")
        if famille:
            print(f"  {BOLD}Family      :{RESET} {DIM}{famille}{RESET}")
        if origine:
            print(f"  {BOLD}Origin      :{RESET} {DIM}{origine}{RESET}")
        if habitat:
            print(f"  {BOLD}Habitat     :{RESET} {DIM}{habitat}{RESET}")

    print(f"{CYAN}{BOLD}{'═' * 40}{RESET}")


def display_web_results(results):
    # Print DuckDuckGo web search results.
    print(f"\n{CYAN}{BOLD}=== Web Search Results ==={RESET}")
    for i, r in enumerate(results, 1):
        print(f"  {BOLD}[{i}]{RESET} {r.get('title', '—')}")
        print(f"      {DIM}{r.get('href', '—')}{RESET}")
    print(f"{CYAN}{BOLD}{'═' * 40}{RESET}")


def display_search_links(resultats_images, resultats_videos):
    # Display generated image/video search links based on Groq keywords.
    print(f"\n{CYAN}{BOLD}=== Generated Search Links ==={RESET}")
    print(f"\n  {BOLD}-- Images --{RESET}")
    for i, r in enumerate(resultats_images, 1):
        print(f"  [{i}] {r.get('titre', '—')}")
        print(f"      {DIM}{r.get('url', '—')}{RESET}")

    print(f"\n  {BOLD}-- Videos --{RESET}")
    for i, r in enumerate(resultats_videos, 1):
        print(f"  [{i}] {r.get('titre', '—')}")
        print(f"      {DIM}{r.get('url', '—')}{RESET}")
    print(f"{CYAN}{BOLD}{'═' * 40}{RESET}")
