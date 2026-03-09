from __future__ import annotations

import re
from typing import Final

import requests

OLLAMA_URL: Final[str] = "http://localhost:11434/api/generate"
DEFAULT_MODEL: Final[str] = "tinyllama"


def _is_normalized_command(text: str) -> bool:
    value = text.strip().lower()
    if value in {"tell time", "system info", "battery", "view tasks", "hello", "exit"}:
        return True
    return bool(re.match(r"^(calculate|open|add task|remove task)\s+.+$", value))


def _cleanup_response(text: str) -> str:
    normalized = text.strip().lower().strip('"').strip("'")
    normalized = normalized.replace("\n", " ").strip()

    prefixes = (
        "normalized command:",
        "command:",
        "output:",
        "answer:",
    )
    for prefix in prefixes:
        if normalized.startswith(prefix):
            return normalized[len(prefix):].strip()
    return normalized


def _extract_allowed_command(text: str) -> str:
    """Extract the first valid command shape from model output."""
    cleaned = text.strip().lower()
    if not cleaned:
        return ""

    exact_keywords = (
        "tell time",
        "system info",
        "battery",
        "view tasks",
        "hello",
        "exit",
    )
    for keyword in exact_keywords:
        if keyword in cleaned:
            return keyword

    patterns = (
        r"calculate\s+[^\n\r]+",
        r"open\s+[^\n\r]+",
        r"add task\s+[^\n\r]+",
        r"remove task\s+[^\n\r]+",
    )
    for pattern in patterns:
        match = re.search(pattern, cleaned)
        if match:
            return re.sub(r"\s+", " ", match.group(0)).strip(" .,:;\"'")

    return ""


def _fallback_normalize(user_input: str) -> str:
    """Fallback when Ollama is unavailable or times out."""
    text = user_input.strip().lower()
    if not text:
        return text

    filler_phrases = (
        "please",
        "can you",
        "could you",
        "would you",
        "jarvis",
        "hey",
        "ok",
        "okay",
        "i want to",
        "i need to",
        "a ",
        " to ",
    )
    for phrase in filler_phrases:
        text = text.replace(phrase, " ")
    text = re.sub(r"\s+", " ", text).strip()

    # Check task-related commands FIRST (before simple keyword checks)
    # to avoid "tomorrow" matching "time"
    
    # Add task commands - need explicit trigger
    for trigger in ("add task", "create task", "new task"):
        if trigger in text:
            task = text.split(trigger, 1)[1].strip()
            if task:
                return f"add task {task}"
    
    # Remove task commands - need explicit trigger
    for trigger in ("remove task", "delete task", "complete task", "done task", "finish task"):
        if trigger in text:
            task = text.split(trigger, 1)[1].strip()
            if task:
                return f"remove task {task}"
    
    # View/list task commands - if mentions tasks without add/remove action
    has_task_word = "task" in text or "todo" in text
    has_view_word = any(word in text for word in ("list", "show", "view", "see", "what", "display", "tell me", "get", "check", "have", "is", "do", "any", "are"))
    # Check for EXPLICIT add/remove triggers (not just words like "completed")
    has_explicit_action = any(phrase in text for phrase in ("add task", "create task", "new task", "remove task", "delete task"))
    
    if has_task_word and has_view_word and not has_explicit_action:
        return "view tasks"

    # Now check simple keyword commands
    if any(word in text for word in ("time", "clock")):
        return "tell time"
    if any(word in text for word in ("system", "cpu", "ram", "memory", "performance", "pc")):
        return "system info"
    if any(word in text for word in ("battery", "charge", "power")):
        return "battery"

    if any(op in text for op in ("plus", "minus", "times", "divided", "+", "-", "*", "/", "x")) and re.search(r"\d", text):
        return f"calculate {text}"

    for trigger in ("open", "launch", "start", "run"):
        if trigger in text:
            app = text.split(trigger, 1)[1].strip()
            if app:
                # Trim polite tail phrases that should not be part of app name.
                for tail in (" for me", " please", " now"):
                    if app.endswith(tail):
                        app = app[: -len(tail)].strip()
                return f"open {app}"

    if any(word in text for word in ("hello", "hi")):
        return "hello"
    if any(word in text for word in ("exit", "quit", "bye", "stop", "sleep")):
        return "exit"

    return user_input.strip().lower()


def normalize_command(user_input: str, model: str = DEFAULT_MODEL) -> str:
    """Normalize natural language input into existing Jarvis command phrases."""
    cleaned_input = user_input.strip()
    if not cleaned_input:
        return ""

    fallback = _fallback_normalize(cleaned_input)

    prompt = (
        "You normalize commands for a Windows assistant. "
        "Return only one normalized command and no explanation.\n"
        "Allowed forms:\n"
        "- tell time\n"
        "- system info\n"
        "- battery\n"
        "- calculate <expression>\n"
        "- open <app>\n"
        "- add task <text>\n"
        "- view tasks\n"
        "- remove task <text>\n"
        "- hello\n"
        "- exit\n"
        "If you are unsure, return the original text lowercased.\n"
        f"Input: {cleaned_input}\n"
        "Normalized:"
    )

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.1, "num_predict": 48},
            },
            timeout=8,
        )
        response.raise_for_status()
        raw = response.json().get("response", "")
        normalized = _cleanup_response(raw)
        extracted = _extract_allowed_command(normalized)
        if extracted:
            # Prefer deterministic parsing when it produced a valid command shape.
            if _is_normalized_command(fallback) and extracted != fallback:
                return fallback
            return extracted
        return fallback
    except Exception:
        return fallback
