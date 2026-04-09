"""JARVIS FastAPI Backend — WebSocket bridge to the goal-based agent.

Endpoints:
    WS  /ws/chat       — bidirectional chat with the JARVIS agent
    WS  /ws/notify     — push battery / network / reminder notifications
    POST /api/tts       — speak text via PowerShell TTS
    POST /api/tts/stop  — stop current speech + clear queue
    POST /api/volume    — set system volume
    POST /api/mute      — toggle mute
    GET  /api/status    — system info snapshot
    GET  /api/health    — health check for Electron startup
"""
from __future__ import annotations

import asyncio
import json
import os
import queue
import subprocess
import sys
import threading
import unicodedata
from contextlib import asynccontextmanager
from typing import Optional

# ── Path setup — allow importing features from parent directory ──────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from features import agent
from features.network_status import (
    NetworkNotificationState,
    check_network_notifications,
)
from features.reminders import pop_due_notifications
from features.system_control import mute_volume, set_volume
from features.system_info import (
    BatteryNotificationState,
    check_battery_notifications,
    get_battery_status_text,
    get_system_info_text,
)


# ─── TTS Engine ───────────────────────────────────────────────────────────────
_speech_queue: queue.Queue = queue.Queue()
_speech_lock = threading.Lock()
_current_speech_process: Optional[subprocess.Popen] = None
_is_speaking = threading.Event()


def _tts_safe(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return ascii_text.replace("'", "''")


def _speech_worker() -> None:
    global _current_speech_process
    while True:
        text = _speech_queue.get()
        if text is None:
            break
        safe = _tts_safe(text)
        _is_speaking.set()
        try:
            ps_cmd = (
                "Add-Type -AssemblyName System.Speech; "
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$s.Speak('{safe}')"
            )
            proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            with _speech_lock:
                _current_speech_process = proc
            proc.wait()
        except Exception as exc:
            print(f"[TTS Error] {exc}")
        finally:
            with _speech_lock:
                _current_speech_process = None
            _is_speaking.clear()
            _speech_queue.task_done()


_speech_thread = threading.Thread(target=_speech_worker, daemon=True, name="TTSWorker")
_speech_thread.start()


def speak(text: str) -> None:
    print(f"[TTS] {text}")
    _speech_queue.put(text)


def stop_speaking() -> None:
    with _speech_lock:
        proc = _current_speech_process
    if proc is not None and proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=0.3)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    # Drain queue
    while True:
        try:
            _speech_queue.get_nowait()
            _speech_queue.task_done()
        except queue.Empty:
            break
    _is_speaking.clear()


# ─── Notification State ───────────────────────────────────────────────────────
_battery_state = BatteryNotificationState()
_network_state = NetworkNotificationState()

# Connected WebSocket clients
_chat_clients: list[WebSocket] = []
_notify_clients: list[WebSocket] = []


# ─── Background Notification Poller ───────────────────────────────────────────
async def _notification_poller() -> None:
    """Poll battery, network, and reminders and push to connected clients."""
    while True:
        await asyncio.sleep(2)
        messages: list[dict] = []

        battery_msg = check_battery_notifications(_battery_state)
        if battery_msg:
            messages.append({"category": "battery", "message": battery_msg})
            speak(battery_msg)

        net_msg = check_network_notifications(_network_state)
        if net_msg:
            messages.append({"category": "network", "message": net_msg})
            speak(net_msg)

        for reminder_msg in pop_due_notifications(limit=3):
            messages.append({"category": "reminder", "message": reminder_msg})
            speak(reminder_msg)

        for msg_data in messages:
            payload = json.dumps({"type": "notification", **msg_data})
            for ws in list(_notify_clients):
                try:
                    await ws.send_text(payload)
                except Exception:
                    _notify_clients.remove(ws) if ws in _notify_clients else None


# ─── FastAPI App ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(_notification_poller())
    yield
    task.cancel()


app = FastAPI(title="JARVIS Backend", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── WebSocket: Chat ─────────────────────────────────────────────────────────
@app.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    await ws.accept()
    _chat_clients.append(ws)
    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            user_text = data.get("text", "").strip()
            if not user_text:
                continue

            # → Processing
            await ws.send_text(json.dumps({"type": "status", "status": "processing"}))

            # Run agent (blocking) in thread pool
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, agent.run, user_text)

            # → Response
            await ws.send_text(json.dumps({"type": "response", "text": response}))

            # TTS
            speak(response)
            await ws.send_text(json.dumps({"type": "status", "status": "speaking"}))

            # Wait until TTS finishes (poll at 200ms)
            await asyncio.sleep(0.3)
            while _is_speaking.is_set():
                await asyncio.sleep(0.2)

            # → Standby
            await ws.send_text(json.dumps({"type": "status", "status": "standby"}))
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        print(f"[WS Chat Error] {exc}")
    finally:
        if ws in _chat_clients:
            _chat_clients.remove(ws)


# ─── WebSocket: Notifications ────────────────────────────────────────────────
@app.websocket("/ws/notify")
async def ws_notify(ws: WebSocket):
    await ws.accept()
    _notify_clients.append(ws)
    try:
        while True:
            await ws.receive_text()  # keepalive
    except WebSocketDisconnect:
        pass
    finally:
        if ws in _notify_clients:
            _notify_clients.remove(ws)


# ─── REST endpoints ──────────────────────────────────────────────────────────
class TTSBody(BaseModel):
    text: str


class VolumeBody(BaseModel):
    level: int


@app.post("/api/tts")
async def api_tts(body: TTSBody):
    speak(body.text)
    return {"ok": True}


@app.post("/api/tts/stop")
async def api_tts_stop():
    stop_speaking()
    return {"ok": True}


@app.post("/api/volume")
async def api_volume(body: VolumeBody):
    result = set_volume(body.level)
    return {"result": result}


@app.post("/api/mute")
async def api_mute():
    result = mute_volume()
    return {"result": result}


@app.get("/api/status")
async def api_status():
    loop = asyncio.get_event_loop()
    sys_info = await loop.run_in_executor(None, get_system_info_text)
    bat_info = await loop.run_in_executor(None, get_battery_status_text)
    return {"system": sys_info, "battery": bat_info}


@app.get("/api/health")
async def api_health():
    return {"status": "ok"}


# ─── Entry ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
