"""Entertainment features: jokes, trivia, and music playback."""
from __future__ import annotations

import os
import random

import requests

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

_FALLBACK_JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "I would tell you a UDP joke, but you might not get it.",
    "Why did the developer go broke? He used up all his cache.",
    "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?",
    "Why do Java developers wear glasses? Because they don't C sharp.",
    "How many programmers does it take to change a light bulb? None — that's a hardware problem.",
    "Why do Python programmers prefer snake_case? They find it more readable.",
]


def tell_joke() -> str:
    """Fetch a safe random joke or fall back to a local one."""
    try:
        r = requests.get(
            "https://v2.jokeapi.dev/joke/Any?safe-mode&type=single",
            headers=_HEADERS,
            timeout=5,
        )
        data = r.json()
        if data.get("type") == "single":
            return data["joke"]
        setup = data.get("setup", "")
        delivery = data.get("delivery", "")
        if setup and delivery:
            return f"{setup} ... {delivery}"
    except Exception:
        pass
    return random.choice(_FALLBACK_JOKES)


def get_trivia() -> str:
    """Fetch a random trivia question with answer from Open Trivia DB."""
    try:
        r = requests.get(
            "https://opentdb.com/api.php?amount=1&type=multiple",
            headers=_HEADERS,
            timeout=6,
        )
        data = r.json()
        if data.get("response_code") == 0 and data.get("results"):
            item = data["results"][0]
            question = (
                item["question"]
                .replace("&quot;", '"')
                .replace("&#039;", "'")
                .replace("&amp;", "&")
            )
            answer = (
                item["correct_answer"]
                .replace("&quot;", '"')
                .replace("&#039;", "'")
                .replace("&amp;", "&")
            )
            category = item.get("category", "")
            return f"Trivia — {category}. {question} The answer is: {answer}."
    except Exception:
        pass
    return "Could not fetch trivia right now. Please try again later."


def play_music(song: str | None = None) -> str:
    """Play a music file from ~/Music/. Optionally search by name."""
    music_dir = os.path.join(os.path.expanduser("~"), "Music")
    if not os.path.exists(music_dir):
        return "No Music folder found in your home directory."

    audio_exts = (".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma")
    files = [f for f in os.listdir(music_dir) if f.lower().endswith(audio_exts)]

    if not files:
        return "No audio files found in your Music folder."

    if song and song.strip():
        s = song.strip().lower()
        match = next((f for f in files if s in f.lower()), None)
        if not match:
            return f"No music file matching '{song}'. Available: {', '.join(files[:5])}."
        target = match
    else:
        target = random.choice(files)

    path = os.path.join(music_dir, target)
    try:
        os.startfile(path)
        return f"Playing {target}."
    except Exception as exc:
        return f"Could not play {target}: {exc}"
