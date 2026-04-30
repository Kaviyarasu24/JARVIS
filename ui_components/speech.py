"""Queued Windows TTS helpers for the JARVIS UI."""

from __future__ import annotations

import queue
import subprocess
import threading
from typing import Optional


def _tts_safe(text: str) -> str:
    """Transliterate to ASCII and escape single quotes for PowerShell."""
    import unicodedata

    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return ascii_text.replace("'", "''")


_speech_queue: queue.Queue = queue.Queue()
_speech_lock = threading.Lock()
_current_speech_process: Optional[subprocess.Popen] = None
_listening_mode = threading.Event()


def _speech_worker() -> None:
    """Background thread: speaks items from the queue one at a time."""
    global _current_speech_process
    while True:
        text = _speech_queue.get()
        if text is None:
            break
        safe = _tts_safe(text)
        try:
            ps_cmd = f"""
Add-Type -AssemblyName System.Speech
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Speak('{safe}')
"""
            proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            with _speech_lock:
                _current_speech_process = proc
            proc.wait()
        except Exception as exc:
            print(f"Speech error: {exc}")
        finally:
            with _speech_lock:
                _current_speech_process = None
            _speech_queue.task_done()


_speech_thread = threading.Thread(target=_speech_worker, daemon=True, name="SpeechWorker")
_speech_thread.start()


def speak(text: str) -> None:
    """Enqueue text for serial TTS and avoid speech overlap while listening."""
    print(text)
    if _listening_mode.is_set():
        return
    _speech_queue.put(text)


def set_listening_mode(active: bool) -> None:
    if active:
        _listening_mode.set()
    else:
        _listening_mode.clear()


def stop_speaking() -> None:
    """Stop current speech immediately and clear any pending queued speech."""
    global _current_speech_process

    with _speech_lock:
        proc = _current_speech_process

    if proc is not None and proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=0.2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    while True:
        try:
            _speech_queue.get_nowait()
            _speech_queue.task_done()
        except queue.Empty:
            break
