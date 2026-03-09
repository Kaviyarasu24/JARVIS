from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import psutil


@dataclass
class BatteryNotificationState:
    low_battery_notified: bool = False
    charging_sixty_notified: bool = False
    last_power_plugged: Optional[bool] = None


def _format_bytes_gb(value: float) -> float:
    return round(value / (1024 ** 3), 2)


def get_system_info_text() -> str:
    """Return a compact system status summary for speech output."""
    cpu = psutil.cpu_percent(interval=0.6)
    mem = psutil.virtual_memory()

    parts = [
        f"CPU usage is {cpu:.0f} percent.",
        f"RAM usage is {mem.percent:.0f} percent, with {_format_bytes_gb(mem.available)} gigabytes available.",
    ]

    battery_text = get_battery_status_text()
    if battery_text:
        parts.append(battery_text)

    return " ".join(parts)


def get_battery_status_text() -> str:
    """Return battery status text, if battery information is available."""
    battery = psutil.sensors_battery()
    if battery is None:
        return "Battery information is not available on this device."

    status = "charging" if battery.power_plugged else "not charging"
    return f"Battery is at {battery.percent:.0f} percent and is currently {status}."


def check_battery_notifications(state: BatteryNotificationState) -> Optional[str]:
    """Return a one-time notification message based on battery thresholds."""
    battery = psutil.sensors_battery()
    if battery is None:
        return None

    # Detect charger state transitions and announce them immediately.
    if state.last_power_plugged is None:
        state.last_power_plugged = battery.power_plugged
    elif state.last_power_plugged != battery.power_plugged:
        state.last_power_plugged = battery.power_plugged
        if battery.power_plugged:
            state.low_battery_notified = False
            return f"Charger connected. Battery is now at {battery.percent:.0f} percent."

        state.charging_sixty_notified = False
        return f"Charger disconnected. Battery is at {battery.percent:.0f} percent."

    if not battery.power_plugged and battery.percent < 30:
        if not state.low_battery_notified:
            state.low_battery_notified = True
            state.charging_sixty_notified = False
            return f"Battery is low at {battery.percent:.0f} percent. Please charge your system."
    else:
        state.low_battery_notified = False

    if battery.power_plugged and battery.percent >= 60:
        if not state.charging_sixty_notified:
            state.charging_sixty_notified = True
            return f"Battery has reached {battery.percent:.0f} percent while charging. You can unplug the charger now."
    else:
        if battery.power_plugged and battery.percent < 60:
            state.charging_sixty_notified = False
        if not battery.power_plugged:
            state.charging_sixty_notified = False

    return None
