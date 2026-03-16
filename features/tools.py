"""Unified tool registry for the JARVIS goal-based agent.

Every capability is registered here as a named tool with:
  - description  : what the LLM reads to decide whether to call it
  - parameters   : {param_name: "type - explanation"} dict shown to LLM
  - fn           : callable that executes the tool and returns a str result
"""
from __future__ import annotations

from features.calculator import calculate_text
from features.tell_time import get_current_time_text
from features.weather import get_weather_text
from features.news_headlines import get_news_text
from features.wikipedia_search import search_wikipedia
from features.system_info import get_system_info_text, get_battery_status_text
from features.network_status import (
    get_active_connections_text,
    get_bluetooth_status_text,
    get_ip_address_text,
    get_network_interfaces_text,
    get_network_usage_text,
    get_ping_text,
    get_wifi_status_text,
    toggle_bluetooth,
    toggle_wifi,
)
from features.stock_market import get_crypto_text, get_stock_text
from features.todo_list import add_task, complete_task, remove_task, view_tasks
from features.browser_control import open_website, google_search
from features.system_control import (
    abort_shutdown,
    lock_screen,
    mute_volume,
    open_app,
    restart_pc,
    set_brightness,
    set_volume,
    shutdown_pc,
    sleep_pc,
    take_screenshot,
    volume_down,
    volume_up,
)
from features.entertainment import get_trivia, play_music, tell_joke
from features.notes import delete_note, take_note, view_notes


# ── Registry ──────────────────────────────────────────────────────────────────
# Each tool: {description, parameters, fn}
# parameters maps arg name → "type - description" string (shown in LLM prompt)

TOOLS: dict[str, dict] = {
    # ── Time ──────────────────────────────────────────────────────────────────
    "get_time": {
        "description": "Get the current date and time",
        "parameters": {},
        "fn": lambda: get_current_time_text(),
    },

    # ── Weather ───────────────────────────────────────────────────────────────
    "get_weather": {
        "description": "Get current weather conditions for a city (or default location)",
        "parameters": {"city": "str (optional) - city name, e.g. 'London'"},
        "fn": lambda city="": get_weather_text(city.strip() if city else None),
    },

    # ── News ──────────────────────────────────────────────────────────────────
    "get_news": {
        "description": "Fetch the latest news headlines",
        "parameters": {},
        "fn": lambda: get_news_text(),
    },

    # ── Wikipedia ─────────────────────────────────────────────────────────────
    "search_wikipedia": {
        "description": "Search Wikipedia and return a brief summary for a topic",
        "parameters": {"query": "str - topic to search"},
        "fn": lambda query: search_wikipedia(query),
    },

    # ── System Info ───────────────────────────────────────────────────────────
    "get_system_info": {
        "description": "Get CPU, RAM, and disk usage statistics",
        "parameters": {},
        "fn": lambda: get_system_info_text(),
    },
    "get_battery": {
        "description": "Get battery level and charging status",
        "parameters": {},
        "fn": lambda: get_battery_status_text(),
    },

    # ── Calculator ────────────────────────────────────────────────────────────
    "calculate": {
        "description": "Evaluate a math expression, e.g. '25 plus 5' or '10 * 3 / 2'",
        "parameters": {"expression": "str - the math expression to evaluate"},
        "fn": lambda expression: calculate_text(expression),
    },

    # ── Todo List ─────────────────────────────────────────────────────────────
    "add_task": {
        "description": "Add a new task to the todo list",
        "parameters": {"task": "str - task description"},
        "fn": lambda task: add_task(task),
    },
    "view_tasks": {
        "description": "Show all pending todo list tasks",
        "parameters": {},
        "fn": lambda: view_tasks(),
    },
    "complete_task": {
        "description": "Mark a task as completed by name or ID",
        "parameters": {"task": "str - task name or numeric ID"},
        "fn": lambda task: complete_task(task),
    },
    "remove_task": {
        "description": "Delete a task from the todo list by name or ID",
        "parameters": {"task": "str - task name or numeric ID"},
        "fn": lambda task: remove_task(task),
    },

    # ── Network ───────────────────────────────────────────────────────────────
    "get_wifi_status": {
        "description": "Check current WiFi connection status",
        "parameters": {},
        "fn": lambda: get_wifi_status_text(),
    },
    "toggle_wifi": {
        "description": "Turn WiFi on or off",
        "parameters": {"enable": "bool - true to enable, false to disable"},
        "fn": lambda enable: toggle_wifi(bool(enable)),
    },
    "get_bluetooth_status": {
        "description": "Check current Bluetooth status",
        "parameters": {},
        "fn": lambda: get_bluetooth_status_text(),
    },
    "toggle_bluetooth": {
        "description": "Turn Bluetooth on or off",
        "parameters": {"enable": "bool - true to enable, false to disable"},
        "fn": lambda enable: toggle_bluetooth(bool(enable)),
    },
    "get_ip_address": {
        "description": "Get the local IP address",
        "parameters": {},
        "fn": lambda: get_ip_address_text(),
    },
    "get_network_interfaces": {
        "description": "List all network interfaces",
        "parameters": {},
        "fn": lambda: get_network_interfaces_text(),
    },
    "get_network_usage": {
        "description": "Get current network bandwidth usage",
        "parameters": {},
        "fn": lambda: get_network_usage_text(),
    },
    "get_active_connections": {
        "description": "List active network connections",
        "parameters": {},
        "fn": lambda: get_active_connections_text(),
    },
    "ping": {
        "description": "Ping a hostname or IP address and return latency",
        "parameters": {"host": "str - hostname or IP to ping"},
        "fn": lambda host: get_ping_text(host),
    },

    # ── Finance ───────────────────────────────────────────────────────────────
    "get_stock_prices": {
        "description": "Get current stock market prices for configured symbols",
        "parameters": {},
        "fn": lambda: get_stock_text(),
    },
    "get_crypto_prices": {
        "description": "Get current cryptocurrency prices (Bitcoin and others)",
        "parameters": {},
        "fn": lambda: get_crypto_text(),
    },

    # ── Browser & Web ─────────────────────────────────────────────────────────
    "open_website": {
        "description": "Open a URL in the default web browser",
        "parameters": {"url": "str - URL to open, e.g. 'youtube.com' or 'https://github.com'"},
        "fn": lambda url: open_website(url),
    },
    "google_search": {
        "description": "Search Google and open results. Returns a quick answer if found.",
        "parameters": {"query": "str - search query"},
        "fn": lambda query: google_search(query),
    },

    # ── App Control ───────────────────────────────────────────────────────────
    "open_app": {
        "description": "Open a Windows application by name (notepad, calculator, chrome, etc.)",
        "parameters": {"app": "str - application name"},
        "fn": lambda app: open_app(app),
    },

    # ── Power Control ─────────────────────────────────────────────────────────
    "shutdown": {
        "description": "Shut down the computer",
        "parameters": {"delay": "int (optional) - seconds before shutdown (default 10)"},
        "fn": lambda delay=10: shutdown_pc(int(delay)),
    },
    "abort_shutdown": {
        "description": "Cancel a pending shutdown or restart",
        "parameters": {},
        "fn": lambda: abort_shutdown(),
    },
    "restart": {
        "description": "Restart the computer",
        "parameters": {"delay": "int (optional) - seconds before restart (default 10)"},
        "fn": lambda delay=10: restart_pc(int(delay)),
    },
    "sleep": {
        "description": "Put the computer to sleep",
        "parameters": {},
        "fn": lambda: sleep_pc(),
    },
    "lock_screen": {
        "description": "Lock the Windows screen / workstation",
        "parameters": {},
        "fn": lambda: lock_screen(),
    },

    # ── Audio Control ─────────────────────────────────────────────────────────
    "set_volume": {
        "description": "Set the master volume to a specific level",
        "parameters": {"level": "int - volume percentage, 0 to 100"},
        "fn": lambda level: set_volume(int(level)),
    },
    "volume_up": {
        "description": "Increase the system volume by one step",
        "parameters": {},
        "fn": lambda: volume_up(),
    },
    "volume_down": {
        "description": "Decrease the system volume by one step",
        "parameters": {},
        "fn": lambda: volume_down(),
    },
    "mute": {
        "description": "Toggle mute on the system audio",
        "parameters": {},
        "fn": lambda: mute_volume(),
    },

    # ── Display ───────────────────────────────────────────────────────────────
    "set_brightness": {
        "description": "Set screen brightness (laptops and supported displays only)",
        "parameters": {"level": "int - brightness percentage, 0 to 100"},
        "fn": lambda level: set_brightness(int(level)),
    },
    "take_screenshot": {
        "description": "Capture a full screenshot and save it to Pictures/JARVIS/",
        "parameters": {},
        "fn": lambda: take_screenshot(),
    },

    # ── Entertainment ─────────────────────────────────────────────────────────
    "tell_joke": {
        "description": "Tell a random joke",
        "parameters": {},
        "fn": lambda: tell_joke(),
    },
    "get_trivia": {
        "description": "Get a random trivia question with its answer",
        "parameters": {},
        "fn": lambda: get_trivia(),
    },
    "play_music": {
        "description": "Play music from the local Music folder",
        "parameters": {"song": "str (optional) - song name to search for"},
        "fn": lambda song="": play_music(song.strip() if song else None),
    },

    # ── Notes ─────────────────────────────────────────────────────────────────
    "take_note": {
        "description": "Save a voice note or reminder text",
        "parameters": {"text": "str - the note content to save"},
        "fn": lambda text: take_note(text),
    },
    "view_notes": {
        "description": "Read back your recent saved notes",
        "parameters": {},
        "fn": lambda: view_notes(),
    },
    "delete_note": {
        "description": "Delete a saved note by its ID",
        "parameters": {"note_id": "int - note ID to delete"},
        "fn": lambda note_id: delete_note(int(note_id)),
    },
}


def execute(tool_name: str, args: dict) -> str:
    """Execute a registered tool and return its string result."""
    entry = TOOLS.get(tool_name)
    if entry is None:
        return f"Unknown tool: '{tool_name}'."
    fn = entry.get("fn")
    if fn is None:
        return f"Tool '{tool_name}' has no implementation."
    try:
        return str(fn(**args) if args else fn())
    except TypeError as exc:
        return f"Tool '{tool_name}' called with wrong arguments: {exc}"
    except Exception as exc:
        return f"Tool '{tool_name}' error: {exc}"


def format_tool_list() -> str:
    """Return a formatted tool list string for the LLM system prompt."""
    lines: list[str] = []
    for name, info in TOOLS.items():
        params = info.get("parameters", {})
        if params:
            param_str = ", ".join(f"{k}: {v}" for k, v in params.items())
        else:
            param_str = "no parameters"
        lines.append(f"- {name}({param_str}): {info['description']}")
    return "\n".join(lines)
