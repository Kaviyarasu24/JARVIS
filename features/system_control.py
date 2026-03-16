"""System power, volume, brightness, screenshot and app-launch control for JARVIS (Windows)."""
from __future__ import annotations

import ctypes
import datetime
import os
import subprocess

# ── App launcher ──────────────────────────────────────────────────────────────

_APP_MAP: dict[str, str] = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "powershell": "powershell.exe",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "settings": "ms-settings:",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "vlc": "vlc.exe",
    "spotify": "spotify.exe",
    "discord": "discord.exe",
    "snipping tool": "SnippingTool.exe",
    "camera": "microsoft.windows.camera:",
}


def open_app(app_name: str) -> str:
    """Launch a Windows application by name."""
    key = app_name.strip().lower()
    target = _APP_MAP.get(key)
    if not target:
        # Try partial match
        for k, v in _APP_MAP.items():
            if key in k or k in key:
                target = v
                key = k
                break
    if not target:
        return (
            f"I don't know how to open '{app_name}'. "
            f"Supported apps: {', '.join(sorted(_APP_MAP.keys()))}."
        )
    try:
        if target.endswith(":"):
            os.startfile(target)
        else:
            subprocess.Popen([target], shell=False)
        return f"Opening {key}."
    except FileNotFoundError:
        return f"'{app_name}' is not installed or not found in PATH."
    except Exception as exc:
        return f"Could not open {key}: {exc}"


# ── Power control ─────────────────────────────────────────────────────────────

def shutdown_pc(delay: int = 10) -> str:
    """Schedule a Windows shutdown."""
    try:
        subprocess.Popen(["shutdown", "/s", "/t", str(int(delay))])
        return f"Shutting down in {delay} seconds. Say 'cancel shutdown' to abort."
    except Exception as exc:
        return f"Shutdown failed: {exc}"


def abort_shutdown() -> str:
    """Cancel a pending shutdown or restart."""
    try:
        subprocess.Popen(["shutdown", "/a"])
        return "Shutdown cancelled."
    except Exception:
        return "No pending shutdown to cancel."


def restart_pc(delay: int = 10) -> str:
    """Schedule a Windows restart."""
    try:
        subprocess.Popen(["shutdown", "/r", "/t", str(int(delay))])
        return f"Restarting in {delay} seconds."
    except Exception as exc:
        return f"Restart failed: {exc}"


def lock_screen() -> str:
    """Lock the Windows workstation."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Screen locked."
    except Exception as exc:
        return f"Could not lock screen: {exc}"


def sleep_pc() -> str:
    """Put the computer to sleep."""
    try:
        subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
        return "Going to sleep."
    except Exception as exc:
        return f"Could not sleep: {exc}"


# ── Audio control ─────────────────────────────────────────────────────────────

def set_volume(level: int) -> str:
    """Set master volume to 0–100 using the Windows winmm API."""
    level = max(0, min(100, int(level)))
    try:
        vol = int(level * 65535 / 100)
        packed = ctypes.c_uint32(vol | (vol << 16))
        ctypes.windll.winmm.waveOutSetVolume(0, packed)
        return f"Volume set to {level} percent."
    except Exception as exc:
        return f"Volume change failed: {exc}"


def _send_media_key(key_code: int) -> None:
    """Send a media/volume key via SendKeys."""
    ps = f"(New-Object -ComObject WScript.Shell).SendKeys([char]{key_code})"
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=4,
    )


def volume_up() -> str:
    try:
        _send_media_key(175)   # VK_VOLUME_UP
        return "Volume increased."
    except Exception:
        return "Could not increase volume."


def volume_down() -> str:
    try:
        _send_media_key(174)   # VK_VOLUME_DOWN
        return "Volume decreased."
    except Exception:
        return "Could not decrease volume."


def mute_volume() -> str:
    try:
        _send_media_key(173)   # VK_VOLUME_MUTE
        return "Audio muted or unmuted."
    except Exception:
        return "Could not toggle mute."


# ── Brightness ────────────────────────────────────────────────────────────────

def set_brightness(level: int) -> str:
    """Set screen brightness 0–100 (requires WMI; works on most laptops)."""
    level = max(0, min(100, int(level)))
    ps = (
        f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods)"
        f".WmiSetBrightness(5, {level})"
    )
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=6,
        )
        if result.returncode == 0:
            return f"Brightness set to {level} percent."
        return "Brightness control not supported on this display."
    except Exception as exc:
        return f"Brightness change failed: {exc}"


# ── Screenshot ────────────────────────────────────────────────────────────────

def take_screenshot(filename: str | None = None) -> str:
    """Capture a screenshot and save it to ~/Pictures/JARVIS/."""
    try:
        from PIL import ImageGrab
    except ImportError:
        return "Pillow is not installed. Run: pip install Pillow"

    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    folder = os.path.join(os.path.expanduser("~"), "Pictures", "JARVIS")
    os.makedirs(folder, exist_ok=True)
    path = filename or os.path.join(folder, f"screenshot_{ts}.png")

    try:
        img = ImageGrab.grab()
        img.save(path)
        return f"Screenshot saved to {path}."
    except Exception as exc:
        return f"Screenshot failed: {exc}"
