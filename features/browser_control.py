"""Browser control and web search features for JARVIS."""
from __future__ import annotations

import urllib.parse
import webbrowser

import requests

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def open_website(url: str) -> str:
    """Open a URL in the system default browser."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return f"Opening {url}."
    except Exception as exc:
        return f"Could not open browser: {exc}"


def google_search(query: str) -> str:
    """Open a Google search in the browser and try to return a quick answer."""
    query = query.strip()
    encoded = urllib.parse.quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded}"

    # Open in browser
    try:
        webbrowser.open(search_url)
    except Exception:
        pass

    # Try to scrape a quick answer snippet
    try:
        r = requests.get(search_url, headers=_HEADERS, timeout=8)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "lxml")
        for sel in ("div.BNeawe", "div.IZ6rdc", "span.hgKElc", "div.LGOjhe"):
            tag = soup.select_one(sel)
            if tag:
                text = tag.get_text(strip=True)
                if len(text) > 20:
                    return f"Quick answer for '{query}': {text[:300]}"
    except Exception:
        pass

    return f"Opened Google search for: {query}."
