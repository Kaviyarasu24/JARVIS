"""JARVIS Goal-Based Agent — ReAct (Reason + Act) loop over a local Ollama LLM.

Architecture
────────────
1. User speaks → agent.run(user_input) is called
2. LLM receives: system prompt (tool list) + rolling conversation history
3. LLM outputs a JSON step:
     {"thought": "...", "tool": "<name>", "args": {...}}
4. Tool is executed; result is appended as an observation
5. Loop repeats until LLM outputs tool="respond" with the final spoken text
6. If Ollama is unavailable, a fast keyword-dispatch fallback serves the request

Setup
─────
  ollama serve          # start Ollama daemon
  ollama pull llama3.2  # recommended model (3-8 B, JSON-capable)
  python ui.py          # run JARVIS

Model priority (auto-detected from what you have installed):
  llama3.2 > mistral > llama3.1 > llama3 > phi3 > phi3:mini > tinyllama
"""
from __future__ import annotations

import json
import re
from typing import Any

import requests

# ── Configuration ─────────────────────────────────────────────────────────────
_OLLAMA_BASE = "http://localhost:11434"
_CHAT_URL = f"{_OLLAMA_BASE}/api/chat"
_TAGS_URL = f"{_OLLAMA_BASE}/api/tags"

# Preferred models in quality order — first installed one wins
_MODEL_PREFERENCE = [
    "llama3.2", "llama3.2:3b", "llama3.1", "llama3.1:8b",
    "llama3", "mistral", "mistral:7b", "phi3", "phi3:mini",
    "llama2", "tinyllama",
]

MAX_STEPS = 7           # max tool calls before giving up
OLLAMA_TIMEOUT = 40     # seconds before Ollama request times out
MEMORY_TURNS = 12       # rolling conversation turns to keep in context

# ── System Prompt ─────────────────────────────────────────────────────────────
_SYSTEM_TEMPLATE = """\
You are JARVIS, a helpful AI assistant running on a Windows computer.
You fulfill user requests by calling tools, then speaking a concise result.

RESPONSE FORMAT — respond with ONLY a JSON object, no markdown, no extra text:

  To call a tool:
    {{"thought": "brief reason", "tool": "<tool_name>", "args": {{<key>: <value>}}}}

  To give your final spoken answer (no more tools needed):
    {{"thought": "ready", "tool": "respond", "args": {{"text": "<spoken answer>"}}}}

RULES:
- Output ONLY valid JSON every time — no prose, no code fences
- Call exactly ONE tool per response
- Use "respond" when done, or when you can answer from memory
- Keep "text" concise — it will be spoken aloud
- Numbers must be actual numbers: 50 not "50"
- For multi-step goals, chain tool calls automatically

AVAILABLE TOOLS:
{tool_list}
"""


def _build_system_prompt() -> str:
    from features.tools import format_tool_list
    return _SYSTEM_TEMPLATE.format(tool_list=format_tool_list())


# ── Model Detection ───────────────────────────────────────────────────────────
_resolved_model: str | None = None


def _detect_model() -> str:
    """Query Ollama for installed models, pick the best from preference list."""
    global _resolved_model
    if _resolved_model:
        return _resolved_model
    try:
        r = requests.get(_TAGS_URL, timeout=3)
        installed = [m["name"] for m in r.json().get("models", [])]
        installed_bases = {m.split(":")[0]: m for m in installed}
        for pref in _MODEL_PREFERENCE:
            base = pref.split(":")[0]
            if base in installed_bases:
                _resolved_model = installed_bases[base]
                return _resolved_model
        if installed:
            _resolved_model = installed[0]
            return _resolved_model
    except Exception:
        pass
    _resolved_model = _MODEL_PREFERENCE[0]
    return _resolved_model


# ── Ollama Chat Call ──────────────────────────────────────────────────────────

def _call_ollama(messages: list[dict], system: str) -> str:
    """Send messages to Ollama and return raw assistant content."""
    model = _detect_model()
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}] + messages,
        "stream": False,
        "options": {
            "temperature": 0.05,    # near-zero for deterministic JSON
            "num_predict": 300,
        },
    }
    try:
        r = requests.post(_CHAT_URL, json=payload, timeout=OLLAMA_TIMEOUT)
        r.raise_for_status()
        return r.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        raise _OllamaUnavailable(
            f"Ollama is not running. Start with: ollama serve\n"
            f"Then install a model: ollama pull llama3.2"
        )
    except Exception as exc:
        raise _OllamaUnavailable(f"Ollama error: {exc}")


class _OllamaUnavailable(RuntimeError):
    pass


# ── JSON Parsing ──────────────────────────────────────────────────────────────

def _parse_step(raw: str) -> dict[str, Any] | None:
    """Extract a JSON step dict from model output, tolerating common noise."""
    text = raw.strip()
    # Strip markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"```\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Find first {...} block
    m = re.search(r"\{.*?\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


# ── Keyword Fallback ──────────────────────────────────────────────────────────

def _keyword_dispatch(text: str) -> str | None:
    """Fast rule-based dispatch for when Ollama is unavailable."""
    from features.tools import execute

    t = text.lower().strip()

    # Time
    if any(w in t for w in ("what time", "tell time", "current time", "time is it")):
        return execute("get_time", {})

    # Weather
    m = re.search(r"weather (?:in|for|at)\s+(.+)", t)
    if m:
        return execute("get_weather", {"city": m.group(1).strip()})
    if any(w in t for w in ("weather", "temperature", "forecast", "rain")):
        return execute("get_weather", {})

    # News
    if any(w in t for w in ("news", "headlines", "latest")):
        return execute("get_news", {})

    # Wikipedia
    for pfx in ("search wikipedia ", "wikipedia ", "wiki ", "tell me about ", "what is "):
        if t.startswith(pfx) and len(t) > len(pfx) + 2:
            return execute("search_wikipedia", {"query": t[len(pfx):]})

    # System
    if any(w in t for w in ("system info", "system status", "pc status", "computer status", "cpu", "ram")):
        return execute("get_system_info", {})
    if any(w in t for w in ("battery", "battery status", "charge")):
        return execute("get_battery", {})

    # Calculator
    for pfx in ("calculate ", "compute ", "eval ", "solve "):
        if t.startswith(pfx):
            return execute("calculate", {"expression": t[len(pfx):]})

    # Todo
    for pfx in ("add task ", "create task ", "new task ", "add to do "):
        if t.startswith(pfx):
            return execute("add_task", {"task": t[len(pfx):]})
    if any(w in t for w in ("show tasks", "view tasks", "list tasks", "my tasks", "todo", "to do")):
        return execute("view_tasks", {})
    for pfx in ("complete task ", "done task ", "mark done ", "finish task "):
        if t.startswith(pfx):
            return execute("complete_task", {"task": t[len(pfx):]})
    for pfx in ("remove task ", "delete task "):
        if t.startswith(pfx):
            return execute("remove_task", {"task": t[len(pfx):]})

    # Network — order matters: check "turn on/off" before bare "wifi"
    if "wifi" in t or "wi-fi" in t or "wireless" in t:
        if any(w in t for w in ("turn on", "enable", "wifi on")):
            return execute("toggle_wifi", {"enable": True})
        if any(w in t for w in ("turn off", "disable", "wifi off")):
            return execute("toggle_wifi", {"enable": False})
        return execute("get_wifi_status", {})
    if "bluetooth" in t:
        if any(w in t for w in ("turn on", "enable", "bluetooth on")):
            return execute("toggle_bluetooth", {"enable": True})
        if any(w in t for w in ("turn off", "disable", "bluetooth off")):
            return execute("toggle_bluetooth", {"enable": False})
        return execute("get_bluetooth_status", {})
    if any(w in t for w in ("public ip", "external ip", "wan ip")):
        return "Public IP lookup is currently disabled."
    if any(w in t for w in ("ip address", "local ip", "my ip")):
        return execute("get_ip_address", {})
    if any(w in t for w in ("network interfaces", "network adapters")):
        return execute("get_network_interfaces", {})
    if any(w in t for w in ("network usage", "data usage", "bandwidth")):
        return execute("get_network_usage", {})
    if any(w in t for w in ("active connections", "network connections")):
        return execute("get_active_connections", {})
    m = re.match(r"ping\s+(\S+)", t)
    if m:
        return execute("ping", {"host": m.group(1)})

    # Finance
    if any(w in t for w in ("stock", "stocks", "share price", "stock market", "nifty", "sensex")):
        return execute("get_stock_prices", {})
    if any(w in t for w in ("crypto", "cryptocurrency", "bitcoin", "ethereum", "btc")):
        return execute("get_crypto_prices", {})

    # Browser
    for pfx in ("open website ", "go to ", "navigate to ", "visit "):
        if t.startswith(pfx):
            return execute("open_website", {"url": t[len(pfx):]})
    for pfx in ("google ", "search google ", "search for ", "search "):
        if t.startswith(pfx):
            return execute("google_search", {"query": t[len(pfx):]})

    # Apps
    if t.startswith("open "):
        return execute("open_app", {"app": t[5:]})

    # Power
    if any(w in t for w in ("shutdown", "shut down", "power off")):
        if "cancel" in t or "abort" in t:
            return execute("abort_shutdown", {})
        return execute("shutdown", {})
    if any(w in t for w in ("restart", "reboot")):
        return execute("restart", {})
    if any(w in t for w in ("sleep", "hibernate")):
        return execute("sleep", {})
    if any(w in t for w in ("lock screen", "lock the screen", "lock computer")):
        return execute("lock_screen", {})

    # Volume
    m = re.search(r"(?:set\s+)?volume\s+(?:to\s+)?(\d+)", t)
    if m:
        return execute("set_volume", {"level": int(m.group(1))})
    if any(w in t for w in ("volume up", "increase volume", "louder", "turn it up")):
        return execute("volume_up", {})
    if any(w in t for w in ("volume down", "decrease volume", "quieter", "turn it down", "lower")):
        return execute("volume_down", {})
    if "mute" in t:
        return execute("mute", {})

    # Brightness
    m = re.search(r"brightness\s+(?:to\s+)?(\d+)", t)
    if m:
        return execute("set_brightness", {"level": int(m.group(1))})

    # Screenshot
    if "screenshot" in t or "screen capture" in t:
        return execute("take_screenshot", {})

    # Entertainment
    if any(w in t for w in ("tell joke", "tell me a joke", "joke", "funny")):
        return execute("tell_joke", {})
    if any(w in t for w in ("trivia", "quiz me", "random fact", "fun fact")):
        return execute("get_trivia", {})
    if "play music" in t or "play song" in t or "play some music" in t:
        song = re.sub(r"play (?:music|song|some music)\s*", "", t).strip()
        return execute("play_music", {"song": song})

    # Notes
    for pfx in ("take note ", "save note ", "note down ", "remember that ", "note that "):
        if t.startswith(pfx):
            return execute("take_note", {"text": t[len(pfx):]})
    if any(w in t for w in ("view notes", "show notes", "my notes", "read notes", "what notes")):
        return execute("view_notes", {})

    # Greetings — let LLM handle these naturally via "respond"
    if any(w in t for w in ("hello", "hi jarvis", "hey jarvis")):
        return None

    return None  # No match — let LLM decide


# ── Conversation Memory ───────────────────────────────────────────────────────

class ConversationMemory:
    """Rolling window of conversation turns shared across the session."""

    def __init__(self, max_turns: int = MEMORY_TURNS) -> None:
        self._history: list[dict[str, str]] = []
        self._max = max_turns

    def append(self, role: str, content: str) -> None:
        self._history.append({"role": role, "content": content})
        # Trim to max_turns * 2 (user + assistant) + extra tool msgs
        if len(self._history) > self._max * 3:
            self._history = self._history[-(self._max * 3):]

    def get(self) -> list[dict[str, str]]:
        return list(self._history)

    def clear(self) -> None:
        self._history.clear()


# Module-level shared memory used by both jarvis.py and ui.py
memory = ConversationMemory()


# ── Main Entry Point ──────────────────────────────────────────────────────────

def run(user_input: str) -> str:
    """Process a user request through the goal-based ReAct loop.

    Returns the final spoken response string.
    """
    from features.tools import execute

    raw_input = user_input.strip()
    if not raw_input:
        return ""

    system = _build_system_prompt()

    # Working message list for this turn (history + current user message)
    working: list[dict] = memory.get() + [{"role": "user", "content": raw_input}]

    # ── ReAct loop ────────────────────────────────────────────────────────────
    try:
        for step in range(MAX_STEPS):
            raw = _call_ollama(working, system)
            parsed = _parse_step(raw)

            if not parsed:
                # Model returned garbled output — use it as a text response
                reply = raw.strip()[:400]
                memory.append("user", raw_input)
                memory.append("assistant", reply)
                return reply

            tool_name = parsed.get("tool", "respond")
            args: dict[str, Any] = parsed.get("args") or {}

            # ── Final response ────────────────────────────────────────────────
            if tool_name == "respond":
                reply = args.get("text", "").strip() or raw.strip()[:400]
                memory.append("user", raw_input)
                memory.append("assistant", reply)
                return reply

            # ── Execute tool ──────────────────────────────────────────────────
            tool_result = execute(tool_name, args)

            # Append this reasoning step + observation to working context
            working.append({"role": "assistant", "content": raw})
            working.append({
                "role": "user",
                "content": f"[Observation from {tool_name}]: {tool_result}",
            })

        # Exhausted steps — synthesise from last tool result
        last_obs = next(
            (m["content"] for m in reversed(working) if m["role"] == "user" and m["content"].startswith("[Observation")),
            "I could not complete that request.",
        )
        memory.append("user", raw_input)
        memory.append("assistant", last_obs)
        return last_obs

    except _OllamaUnavailable:
        # ── Keyword fallback ──────────────────────────────────────────────────
        result = _keyword_dispatch(raw_input)
        if result:
            memory.append("user", raw_input)
            memory.append("assistant", result)
            return result
        return (
            "Ollama is not running so I cannot process that request. "
            "Start it with: ollama serve — then install a model with: ollama pull llama3.2. "
            "Basic commands like time, weather, and system info still work."
        )
