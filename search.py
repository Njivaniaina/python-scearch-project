import urllib.parse
import time
import warnings
import requests
import re
from pathlib import Path
from duckduckgo_search import DDGS

# ─────────────────────────────────────────────
# Web search
# ─────────────────────────────────────────────

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def _normalize_query(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return str(value)


def _ddg_html_search(requete, max_results=8):
    # Fallback: scrape DuckDuckGo HTML results page.
    results = []
    try:
        q = urllib.parse.quote(_normalize_query(requete))
        url = f"https://html.duckduckgo.com/html/?q={q}"
        resp = requests.get(url, headers=_HEADERS, timeout=10)
        resp.raise_for_status()
        html = resp.text
        pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
            re.IGNORECASE | re.DOTALL,
        )
        for href, title_html in pattern.findall(html)[:max_results]:
            title = re.sub(r"<[^>]+>", "", title_html).strip()
            if href.startswith("//duckduckgo.com/l/?uddg="):
                from urllib.parse import unquote, urlparse, parse_qs

                parsed = urlparse(href)
                real_urls = parse_qs(parsed.query).get("uddg", [])
                if real_urls:
                    href = unquote(real_urls[0])
            results.append({"title": title, "href": href})
    except Exception as e:
        warnings.warn(f"[search] _ddg_html_search failed: {e}")
    return results


def rechercher_web(requete, max_results=8):
    # Return DDG text results; try API then HTML fallback.
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(requete, max_results=max_results))
            if results:
                return results
    except Exception as e:
        warnings.warn(f"[search] DDGS API failed: {e}")

    time.sleep(0.5)
    html_results = _ddg_html_search(requete, max_results)
    if html_results:
        return html_results
    return []


# ─────────────────────────────────────────────
# Discover images from result pages
# ─────────────────────────────────────────────

_EXTS = re.compile(r"\.(jpg|jpeg|png|webp|gif)(\?.*)?$", re.IGNORECASE)


def _is_image_url(url):
    if not url or not isinstance(url, str):
        return False
    return bool(_EXTS.search(url.split("#")[0]))


def _extract_image_urls_from_html(html):
    # Extract http(s) image URLs from raw HTML.
    urls = []
    for src in re.findall(r'<img[^>]+src="([^"]+)"', html, re.IGNORECASE):
        if src.startswith("//"):
            src = "https:" + src
        if src.startswith("http") and _is_image_url(src):
            urls.append(src)
    return urls


def _download_image(url, dest, timeout=12):
    # Download an image and return True only if it is a valid image file.
    try:
        resp = requests.get(url, timeout=timeout, headers=_HEADERS, stream=True)
        if resp.status_code != 200 or len(resp.content) < 1024:
            return False
        Path(dest).parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            f.write(resp.content)
        # Validate with Pillow if available
        try:
            from PIL import Image as PILImage

            with PILImage.open(dest) as im:
                im.verify()
            with PILImage.open(dest) as im:
                im.convert("RGB").load()
            return True
        except Exception:
            return False
    except Exception:
        return False


def resoudre_illustrations(resultats_web, requete, mots_cle_images=None, max_images=2, base_dir="pdf/images"):
    # Try to obtain real illustrations from the web results.
    # Strategy:
    # 1. Try to search similar images directly via DuckDuckGo Image Search.
    # 2. If direct search fails/returns nothing, scrape web results to find image URLs.
    # 3. Download and validate downloaded images with Pillow.
    # 4. If nothing found, fallback to a Google search page URL.
    # Returns a list of dicts: {"titre": ..., "url": ..., "chemin": ...}
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    # First-party direct image link generator
    def _fallback_search_link(keyword):
        q = urllib.parse.quote(_normalize_query(keyword or requete))
        return f"https://www.google.com/search?tbm=isch&q={q}"

    query_keyword = (mots_cle_images or [requete])[0] if (mots_cle_images or requete) else requete
    base_keywords = [kw.lower() for kw in (mots_cle_images or [requete])]
    expanded_keywords = set(base_keywords)
    for kw in base_keywords:
        for word in re.findall(r'[a-z]{4,}', kw):
            expanded_keywords.add(word)
    keywords = list(expanded_keywords)
    safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", _normalize_query(query_keyword))
    found = []

    # Strategy 1: Direct DuckDuckGo Image Search API
    try:
        with DDGS() as ddgs:
            time.sleep(1)  # avoid rate limits
            img_results = list(ddgs.images(query_keyword, max_results=max_images + 3))
            for r in img_results:
                if len(found) >= max_images:
                    break
                img_url = r.get("image")
                img_title = r.get("title", query_keyword)
                if img_url:
                    if img_url.startswith("//"):
                        img_url = "https:" + img_url
                    dest = str(base_dir / f"{safe_name}_{len(found)+1}.jpg")
                    if _download_image(img_url, dest):
                        found.append({
                            "titre": img_title or query_keyword,
                            "url": img_url,
                            "chemin": dest,
                        })
    except Exception as e:
        warnings.warn(f"[search] Direct DuckDuckGo Image Search failed: {e}")

    # Strategy 2: Web Scraping Fallback
    if len(found) < max_images:
        for page in resultats_web[:6]:
            if len(found) >= max_images:
                break
            page_url = page.get("href") or page.get("url") or ""
            page_title = page.get("title", "")
            if not page_url or not page_url.startswith("http"):
                continue
            title_lower = page_title.lower()
            if not any(kw in title_lower for kw in keywords):
                continue
            try:
                resp = requests.get(page_url, headers=_HEADERS, timeout=12)
                if resp.status_code != 200:
                    continue
                img_candidates = _extract_image_urls_from_html(resp.text)
            except Exception:
                continue

            for img_url in img_candidates:
                if len(found) >= max_images:
                    break
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                dest = str(base_dir / f"{safe_name}_{len(found)+1}.jpg")
                if _download_image(img_url, dest):
                    found.append({
                        "titre": page_title or query_keyword,
                        "url": img_url,
                        "chemin": dest,
                    })

    if not found:
        return [{
            "titre": f"Search: {_normalize_query(query_keyword)}",
            "url": _fallback_search_link(query_keyword),
            "chemin": "",
        }]
    return found



# ─────────────────────────────────────────────
# Search URL builder
# ─────────────────────────────────────────────

def build_search_urls(requete, mots_cle_images, mots_cle_videos):
    # Build deterministic search URLs from keywords.
    q_web = urllib.parse.quote(_normalize_query(requete or ""))
    google_image = f"https://www.google.com/search?tbm=isch&q={urllib.parse.quote(_normalize_query((mots_cle_images or [requete])[0]))}"
    yt_query = _normalize_query((mots_cle_videos or [requete])[0])
    youtube = f"https://www.youtube.com/results?search_query={urllib.parse.quote(yt_query)}"
    return {
        "web": f"https://duckduckgo.com/?q={q_web}",
        "images": [google_image],
        "videos": [youtube],
    }
