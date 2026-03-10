"""Weather feature — current conditions using wttr.in JSON (no API key)."""
from __future__ import annotations

import json
import os

import requests

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "news.json")


def _load_places() -> list[str]:
    try:
        with open(_CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f).get("weather", {}).get("places", ["Chennai"])
    except Exception:
        return ["Chennai"]


def get_weather_text(place: str | None = None) -> str:
    """Return a TTS-friendly weather report for configured places (or a specific place)."""
    places = [place] if place else _load_places()
    parts: list[str] = []

    for city in places:
        try:
            r = requests.get(
                f"https://wttr.in/{city.replace(' ', '+')}?format=j1",
                timeout=8,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            r.raise_for_status()
            data = r.json()
            cur = data["current_condition"][0]
            temp     = cur["temp_C"]
            humidity = cur["humidity"]
            wind     = cur["windspeedKmph"]
            desc     = cur["weatherDesc"][0]["value"]
            feels    = cur.get("FeelsLikeC", temp)
            parts.append(
                f"{city}: {temp} degrees Celsius, feels like {feels} degrees, "
                f"{desc}, humidity {humidity} percent, wind {wind} kilometres per hour."
            )
        except Exception:
            parts.append(f"Could not fetch weather for {city}.")

    return ("Weather report. " + " ".join(parts)) if parts else "Weather data unavailable."
