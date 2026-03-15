from __future__ import annotations

import datetime
import json
import os
from typing import Any, Dict, List


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODO_FILE = os.path.join(BASE_DIR, "data", "todo_tasks.json")


def _ensure_data_file() -> None:
    os.makedirs(os.path.dirname(TODO_FILE), exist_ok=True)
    if not os.path.exists(TODO_FILE):
        with open(TODO_FILE, "w", encoding="utf-8") as file:
            json.dump({"tasks_by_date": {}}, file, indent=2)


def _load_data() -> Dict[str, Any]:
    _ensure_data_file()
    with open(TODO_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)
    if "tasks_by_date" not in data or not isinstance(data["tasks_by_date"], dict):
        data = {"tasks_by_date": {}}
    return data


def _save_data(data: Dict[str, Any]) -> None:
    with open(TODO_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def _next_id(data: Dict[str, Any]) -> int:
    max_id = 0
    for tasks in data["tasks_by_date"].values():
        for task in tasks:
            if task.get("id", 0) > max_id:
                max_id = task["id"]
    return max_id + 1


def _all_tasks(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    for date_tasks in data["tasks_by_date"].values():
        tasks.extend(date_tasks)
    return tasks


def _validate_date_key(date_key: str) -> str:
    try:
        parsed = datetime.datetime.strptime(date_key, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format. Use YYYY-MM-DD.")
    return parsed.strftime("%Y-%m-%d")


def add_task(task_text: str, date_key: str | None = None) -> str:
    task = task_text.strip()
    if not task:
        return "Please provide a task to add."

    data = _load_data()
    now = datetime.datetime.now()
    target_date = now.strftime("%Y-%m-%d") if date_key is None else _validate_date_key(date_key)
    time_str = now.strftime("%H:%M")

    if target_date not in data["tasks_by_date"]:
        data["tasks_by_date"][target_date] = []

    task_obj = {
        "id": _next_id(data),
        "task": task,
        "added_time": time_str,
        "status": "pending",
    }
    data["tasks_by_date"][target_date].append(task_obj)
    _save_data(data)
    total = len(_all_tasks(data))
    return f"Task added on {target_date} at {time_str}. You now have {total} task{'s' if total != 1 else ''} in total."


def get_tasks_for_date(date_key: str) -> List[Dict[str, Any]]:
    target_date = _validate_date_key(date_key)
    data = _load_data()
    tasks = data["tasks_by_date"].get(target_date, [])
    return [dict(task) for task in tasks]


def update_task(task_selector: str, new_task_text: str, new_date_key: str | None = None) -> str:
    selector = task_selector.strip()
    updated_text = new_task_text.strip()
    if not selector:
        return "Please provide a task number or exact task text to update."
    if not updated_text:
        return "Please provide updated task text."

    data = _load_data()
    if not _all_tasks(data):
        return "Your todo list is empty."

    target_date = None
    if new_date_key is not None:
        try:
            target_date = _validate_date_key(new_date_key)
        except ValueError as exc:
            return str(exc)

    for current_date, date_tasks in list(data["tasks_by_date"].items()):
        for i, task in enumerate(date_tasks):
            is_match = (selector.isdigit() and task["id"] == int(selector)) or \
                       (not selector.isdigit() and task["task"].lower() == selector.lower())
            if not is_match:
                continue

            destination_date = target_date if target_date is not None else current_date
            task["task"] = updated_text

            if destination_date == current_date:
                data["tasks_by_date"][current_date][i] = task
            else:
                moved_task = date_tasks.pop(i)
                if not date_tasks:
                    del data["tasks_by_date"][current_date]
                data["tasks_by_date"].setdefault(destination_date, []).append(moved_task)

            _save_data(data)
            return f"Updated task {task['id']} on {destination_date}: {task['task']}."

    return "Task not found. Please provide the exact task text or number."


def view_tasks() -> str:
    data = _load_data()
    tasks_by_date = data["tasks_by_date"]
    all_tasks = _all_tasks(data)
    if not all_tasks:
        return "Your todo list is empty."

    parts: List[str] = []
    for date_key in sorted(tasks_by_date.keys()):
        tasks = tasks_by_date[date_key]
        if not tasks:
            continue
        day_lines = [f"[ {date_key} ]"]
        for t in tasks:
            status_label = "DONE" if t["status"] == "completed" else "PENDING"
            day_lines.append(f"  {t['id']}. [{status_label}] {t['task']}  (added {t['added_time']})")
        parts.append("\n".join(day_lines))

    total = len(all_tasks)
    return f"You have {total} task{'s' if total != 1 else ''}:\n\n" + "\n\n".join(parts)


def complete_task(task_selector: str) -> str:
    selector = task_selector.strip()
    if not selector:
        return "Please provide a task number or task text to mark as complete."

    data = _load_data()
    if not _all_tasks(data):
        return "Your todo list is empty."

    for date_tasks in data["tasks_by_date"].values():
        for task in date_tasks:
            match = (selector.isdigit() and task["id"] == int(selector)) or \
                    (not selector.isdigit() and task["task"].lower() == selector.lower())
            if match:
                if task["status"] == "completed":
                    return f"Task '{task['task']}' is already marked as completed."
                task["status"] = "completed"
                _save_data(data)
                return f"Task marked as completed: {task['task']}."

    return "Task not found. Please say the task number or exact task text."


def remove_task(task_selector: str) -> str:
    selector = task_selector.strip()
    if not selector:
        return "Please provide a task number or exact task text to remove."

    data = _load_data()
    if not _all_tasks(data):
        return "Your todo list is empty."

    for date_key, date_tasks in list(data["tasks_by_date"].items()):
        for i, task in enumerate(date_tasks):
            match = (selector.isdigit() and task["id"] == int(selector)) or \
                    (not selector.isdigit() and task["task"].lower() == selector.lower())
            if match:
                removed = date_tasks.pop(i)
                if not date_tasks:
                    del data["tasks_by_date"][date_key]
                _save_data(data)
                return f"Removed task: {removed['task']}."

    return "Task not found. Please say the exact task text or number."
