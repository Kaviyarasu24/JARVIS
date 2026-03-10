"""News headlines via Google News RSS feed (no API key, stdlib XML only)."""
from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET

import requests

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "news.json")

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def _load_config() -> dict:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"news": {"places": ["India"], "max_headlines": 3}}


def _clean_title(title: str) -> str:
    """Strip trailing ' - Source Name' appended by Google News."""
    return re.sub(r"\s+-\s+[^-]+$", "", title).strip()


def get_news_text() -> str:
    """Return TTS-friendly top headlines for all configured places."""
    cfg = _load_config().get("news", {})
    places  = cfg.get("places", ["India"])
    max_h   = min(int(cfg.get("max_headlines", 3)), 5)

    all_parts: list[str] = []

    for place in places:
        try:
            query = place.replace(" ", "+")
            url = (
                f"https://news.google.com/rss/search"
                f"?q={query}&hl=en-IN&gl=IN&ceid=IN:en"
            )
            r = requests.get(url, timeout=8, headers=_HEADERS)
            r.raise_for_status()

            root = ET.fromstring(r.content)
            items = root.findall(".//item")[:max_h]
            headlines = [
                _clean_title(item.find("title").text)
                for item in items
                if item.find("title") is not None and item.find("title").text
            ]

            if headlines:
                numbered = ". ".join(
                    f"{i + 1}. {h}" for i, h in enumerate(headlines)
                )
                all_parts.append(f"Top news from {place}. {numbered}.")
        except Exception:
            all_parts.append(f"Could not fetch news for {place}.")

    return " ".join(all_parts) if all_parts else "News data unavailable."
