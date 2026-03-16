"""Reminder and scheduling features for JARVIS.

Stores reminders in data/reminders.json and supports:
- set_reminder(message, when)
- list_reminders()
- cancel_reminder(reminder_id)
- schedule_task(task, when)
- pop_due_notifications() for runtime polling
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
from threading import Lock
from typing import Any

from features.todo_list import add_task


_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REMINDER_FILE = os.path.join(_BASE_DIR, "data", "reminders.json")
_IO_LOCK = Lock()


def _ensure_store() -> None:
    os.makedirs(os.path.dirname(_REMINDER_FILE), exist_ok=True)
    if not os.path.exists(_REMINDER_FILE):
        with open(_REMINDER_FILE, "w", encoding="utf-8") as f:
            json.dump({"next_id": 1, "items": []}, f, indent=2)


def _load() -> dict[str, Any]:
    _ensure_store()
    with _IO_LOCK:
        try:
            with open(_REMINDER_FILE, encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {"next_id": 1, "items": []}
    if not isinstance(data, dict):
        return {"next_id": 1, "items": []}
    if "next_id" not in data or not isinstance(data["next_id"], int):
        data["next_id"] = 1
    if "items" not in data or not isinstance(data["items"], list):
        data["items"] = []
    return data


def _save(data: dict[str, Any]) -> None:
    with _IO_LOCK:
        with open(_REMINDER_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def _parse_when(when_text: str) -> dt.datetime:
    text = (when_text or "").strip().lower()
    if not text:
        raise ValueError("Please provide reminder time, for example: 'in 10 minutes' or '2026-03-20 18:30'.")

    now = dt.datetime.now()

    # in N minutes/hours/days
    m = re.fullmatch(r"in\s+(\d+)\s*(minute|minutes|hour|hours|day|days)", text)
    if m:
        value = int(m.group(1))
        unit = m.group(2)
        if value <= 0:
            raise ValueError("Time offset must be greater than zero.")
        if "minute" in unit:
            return now + dt.timedelta(minutes=value)
        if "hour" in unit:
            return now + dt.timedelta(hours=value)
        return now + dt.timedelta(days=value)

    # tomorrow HH:MM
    m = re.fullmatch(r"tomorrow\s+(\d{1,2}):(\d{2})", text)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        if hour > 23 or minute > 59:
            raise ValueError("Invalid time. Use HH:MM in 24-hour format.")
        tomorrow = (now + dt.timedelta(days=1)).date()
        return dt.datetime.combine(tomorrow, dt.time(hour=hour, minute=minute))

    # absolute YYYY-MM-DD HH:MM
    try:
        parsed = dt.datetime.strptime(text, "%Y-%m-%d %H:%M")
        if parsed <= now:
            raise ValueError("Please provide a future date/time.")
        return parsed
    except ValueError:
        pass

    # time today HH:MM (or tomorrow if already passed)
    m = re.fullmatch(r"(\d{1,2}):(\d{2})", text)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        if hour > 23 or minute > 59:
            raise ValueError("Invalid time. Use HH:MM in 24-hour format.")
        candidate = dt.datetime.combine(now.date(), dt.time(hour=hour, minute=minute))
        if candidate <= now:
            candidate += dt.timedelta(days=1)
        return candidate

    raise ValueError("Unsupported time format. Try 'in 10 minutes', 'tomorrow 09:30', or '2026-03-20 18:30'.")


def _format_run_at(value: str) -> str:
    try:
        parsed = dt.datetime.fromisoformat(value)
        return parsed.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return value


def set_reminder(message: str, when: str) -> str:
    """Create a reminder to announce a message at a given time."""
    text = (message or "").strip()
    if not text:
        return "Please tell me what to remind you about."

    try:
        run_at = _parse_when(when)
    except ValueError as exc:
        return str(exc)

    data = _load()
    reminder_id = data["next_id"]
    data["next_id"] += 1
    data["items"].append(
        {
            "id": reminder_id,
            "type": "reminder",
            "message": text,
            "run_at": run_at.isoformat(timespec="minutes"),
            "status": "pending",
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            "fired_at": None,
        }
    )
    _save(data)
    return f"Reminder {reminder_id} set for {_format_run_at(run_at.isoformat(timespec='minutes'))}."


def schedule_task(task: str, when: str) -> str:
    """Schedule a task to be automatically added to todo list at a future time."""
    task_text = (task or "").strip()
    if not task_text:
        return "Please provide a task to schedule."

    try:
        run_at = _parse_when(when)
    except ValueError as exc:
        return str(exc)

    data = _load()
    reminder_id = data["next_id"]
    data["next_id"] += 1
    data["items"].append(
        {
            "id": reminder_id,
            "type": "scheduled_task",
            "task": task_text,
            "message": f"Scheduled task: {task_text}",
            "run_at": run_at.isoformat(timespec="minutes"),
            "status": "pending",
            "created_at": dt.datetime.now().isoformat(timespec="seconds"),
            "fired_at": None,
        }
    )
    _save(data)
    return f"Scheduled task {reminder_id} for {_format_run_at(run_at.isoformat(timespec='minutes'))}."


def list_reminders() -> str:
    """List all pending reminders and scheduled tasks."""
    data = _load()
    pending = [x for x in data["items"] if x.get("status") == "pending"]
    if not pending:
        return "You have no pending reminders or scheduled tasks."

    pending.sort(key=lambda x: x.get("run_at", ""))
    lines: list[str] = []
    for item in pending[:20]:
        kind = "Reminder" if item.get("type") == "reminder" else "Task"
        msg = item.get("message") or item.get("task") or "(no text)"
        lines.append(f"{item.get('id')}. {kind} at {_format_run_at(item.get('run_at', ''))}: {msg}")

    if len(pending) > 20:
        lines.append(f"... and {len(pending) - 20} more.")

    return "Pending items: " + " ; ".join(lines)


def cancel_reminder(reminder_id: int) -> str:
    """Cancel a pending reminder/scheduled task by ID."""
    data = _load()
    rid = int(reminder_id)
    for item in data["items"]:
        if int(item.get("id", -1)) == rid:
            if item.get("status") != "pending":
                return f"Item {rid} is already {item.get('status', 'closed')}."
            item["status"] = "cancelled"
            item["fired_at"] = dt.datetime.now().isoformat(timespec="seconds")
            _save(data)
            return f"Cancelled item {rid}."
    return f"Item {rid} not found."


def pop_due_notifications(limit: int = 5) -> list[str]:
    """Return due reminder notifications and mark them completed.

    This is intended for polling loops in ui.py and jarvis.py.
    """
    data = _load()
    now = dt.datetime.now()
    due_messages: list[str] = []

    # Oldest first to preserve chronological behavior.
    pending = [x for x in data["items"] if x.get("status") == "pending"]
    pending.sort(key=lambda x: x.get("run_at", ""))

    for item in pending:
        if len(due_messages) >= max(1, int(limit)):
            break
        run_at_raw = item.get("run_at")
        try:
            run_at = dt.datetime.fromisoformat(str(run_at_raw))
        except Exception:
            item["status"] = "cancelled"
            continue

        if run_at > now:
            continue

        item["status"] = "completed"
        item["fired_at"] = now.isoformat(timespec="seconds")

        if item.get("type") == "scheduled_task":
            task_text = (item.get("task") or "").strip()
            if task_text:
                add_result = add_task(task_text)
                due_messages.append(f"Scheduled task triggered: {task_text}. {add_result}")
            else:
                due_messages.append("A scheduled task triggered but had no task text.")
        else:
            due_messages.append(f"Reminder: {item.get('message', '(no message)')}")

    _save(data)
    return due_messages
