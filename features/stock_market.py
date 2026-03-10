"""Stock prices via Yahoo Finance (unofficial, no API key) and
cryptocurrency prices via CoinGecko (free, no API key).
All symbols/coins are read from data/news.json.
"""
from __future__ import annotations

import json
import os

import requests

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "news.json")

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _load_config() -> dict:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ── Stocks ────────────────────────────────────────────────────────────────────

def get_stock_text() -> str:
    """Return TTS-friendly prices for all stocks listed in news.json."""
    stocks = _load_config().get("stock", {}).get("symbols", [])
    if not stocks:
        return "No stocks configured in news.json."

    parts: list[str] = []

    for s in stocks:
        name   = s.get("name", "")
        ticker = s.get("ticker", "")
        if not ticker:
            continue
        try:
            url = (
                f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
                "?interval=1d&range=1d"
            )
            r = requests.get(url, timeout=8, headers=_HEADERS)
            r.raise_for_status()
            meta = r.json()["chart"]["result"][0]["meta"]

            price = float(meta.get("regularMarketPrice", 0))
            prev  = float(
                meta.get("previousClose")
                or meta.get("chartPreviousClose")
                or price
            )

            if prev:
                pct = (price - prev) / prev * 100
            else:
                pct = 0.0

            if pct > 0.05:
                trend = f"up {pct:.1f} percent"
            elif pct < -0.05:
                trend = f"down {abs(pct):.1f} percent"
            else:
                trend = "unchanged"

            parts.append(f"{name}: {price:.2f} rupees, {trend}.")
        except Exception:
            parts.append(f"{name}: data unavailable.")

    return ("Stock market update. " + " ".join(parts)) if parts else "Stock data unavailable."


# ── Cryptocurrency ────────────────────────────────────────────────────────────

def get_crypto_text() -> str:
    """Return TTS-friendly prices for all cryptocurrencies listed in news.json."""
    cryptos = _load_config().get("crypto", {}).get("symbols", [])
    if not cryptos:
        return "No cryptocurrencies configured in news.json."

    ids = [c["id"] for c in cryptos if "id" in c]
    if not ids:
        return "No crypto IDs configured in news.json."

    try:
        url = (
            "https://api.coingecko.com/api/v3/simple/price"
            f"?ids={','.join(ids)}&vs_currencies=inr"
        )
        r = requests.get(url, timeout=10, headers=_HEADERS)
        r.raise_for_status()
        data = r.json()

        parts: list[str] = []
        for c in cryptos:
            cid   = c.get("id", "")
            name  = c.get("name", cid)
            price = data.get(cid, {}).get("inr", 0)
            if price:
                if price >= 10_000_000:
                    price_str = f"{price / 10_000_000:.2f} crore rupees"
                elif price >= 100_000:
                    price_str = f"{price / 100_000:.1f} lakh rupees"
                else:
                    price_str = f"{price:,.0f} rupees"
                parts.append(f"{name}: {price_str}.")
            else:
                parts.append(f"{name}: data unavailable.")

        return ("Cryptocurrency update. " + " ".join(parts)) if parts else "Crypto data unavailable."
    except Exception as exc:
        return f"Could not fetch cryptocurrency data. {exc}"
