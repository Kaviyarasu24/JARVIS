from __future__ import annotations

import json
import os
from typing import Any, Dict, List


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODO_FILE = os.path.join(BASE_DIR, "data", "todo_tasks.json")


def _ensure_data_file() -> None:
    os.makedirs(os.path.dirname(TODO_FILE), exist_ok=True)
    if not os.path.exists(TODO_FILE):
        with open(TODO_FILE, "w", encoding="utf-8") as file:
            json.dump({"tasks": []}, file, indent=2)


def _load_data() -> Dict[str, Any]:
    _ensure_data_file()
    with open(TODO_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    if "tasks" not in data or not isinstance(data["tasks"], list):
        data = {"tasks": []}
    return data


def _save_data(data: Dict[str, Any]) -> None:
    with open(TODO_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def add_task(task_text: str) -> str:
    task = task_text.strip()
    if not task:
        return "Please provide a task to add."

    data = _load_data()
    tasks: List[str] = data["tasks"]
    tasks.append(task)
    _save_data(data)
    return f"Task added. You now have {len(tasks)} task{'s' if len(tasks) != 1 else ''}."


def view_tasks() -> str:
    data = _load_data()
    tasks: List[str] = data["tasks"]
    if not tasks:
        return "Your todo list is empty."

    numbered = "; ".join([f"{index + 1}. {task}" for index, task in enumerate(tasks)])
    return f"You have {len(tasks)} tasks: {numbered}."


def remove_task(task_selector: str) -> str:
    selector = task_selector.strip()
    if not selector:
        return "Please provide a task number or exact task text to remove."

    data = _load_data()
    tasks: List[str] = data["tasks"]
    if not tasks:
        return "Your todo list is empty."

    removed_task = None

    if selector.isdigit():
        idx = int(selector) - 1
        if 0 <= idx < len(tasks):
            removed_task = tasks.pop(idx)
        else:
            return "Task number not found."
    else:
        for i, task in enumerate(tasks):
            if task.lower() == selector.lower():
                removed_task = tasks.pop(i)
                break
        if removed_task is None:
            return "Task not found. Please say the exact task text or number."

    _save_data(data)
    return f"Removed task: {removed_task}."
