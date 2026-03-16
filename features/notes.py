"""Voice note-taking feature for JARVIS."""
from __future__ import annotations

import datetime
import json
import os
from typing import Any

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_NOTES_FILE = os.path.join(_BASE_DIR, "data", "notes.json")


def _load() -> list[dict[str, Any]]:
    if not os.path.exists(_NOTES_FILE):
        return []
    try:
        with open(_NOTES_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save(notes: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(_NOTES_FILE), exist_ok=True)
    with open(_NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)


def take_note(text: str) -> str:
    """Save a new note."""
    text = text.strip()
    if not text:
        return "Please tell me what to note."
    notes = _load()
    notes.append(
        {
            "id": len(notes) + 1,
            "text": text,
            "created": datetime.datetime.now().isoformat(timespec="seconds"),
        }
    )
    _save(notes)
    return f"Note saved: {text}"


def view_notes(last_n: int = 5) -> str:
    """Read back the most recent notes."""
    notes = _load()
    if not notes:
        return "You have no saved notes."
    recent = notes[-int(last_n):]
    parts = [f"{n['id']}. {n['text']}" for n in recent]
    return f"Your last {len(recent)} note{'s' if len(recent) != 1 else ''}: " + "; ".join(parts) + "."


def delete_note(note_id: int) -> str:
    """Delete a note by ID."""
    notes = _load()
    before = len(notes)
    notes = [n for n in notes if n.get("id") != int(note_id)]
    if len(notes) == before:
        return f"Note {note_id} not found."
    _save(notes)
    return f"Note {note_id} deleted."
