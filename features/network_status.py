"""Network status features for JARVIS — WiFi, Bluetooth, IP, ping, and more."""
from __future__ import annotations

import re
import socket
import subprocess
import urllib.request

import psutil


# ---------------------------------------------------------------------------
# WiFi
# ---------------------------------------------------------------------------

def get_wifi_status_text() -> str:
    """Return WiFi connection status, SSID, and signal strength (Windows)."""
    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        output = result.stdout

        if not output.strip() or "There is no wireless interface" in output:
            return "No wireless adapter found on this system."

        state_match = re.search(r"^\s+State\s*:\s*(.+)", output, re.MULTILINE | re.IGNORECASE)
        ssid_match = re.search(r"^\s+SSID\s*:\s*(?!BSSID)(.+)", output, re.MULTILINE | re.IGNORECASE)
        signal_match = re.search(r"Signal\s*:\s*(.+)", output, re.IGNORECASE)
        recv_match = re.search(r"Receive rate \(Mbps\)\s*:\s*(.+)", output, re.IGNORECASE)

        state = state_match.group(1).strip() if state_match else "unknown"

        if state.lower() != "connected":
            return f"Wi-Fi is not connected. Current state: {state}."

        ssid = ssid_match.group(1).strip() if ssid_match else "Unknown network"
        signal = signal_match.group(1).strip() if signal_match else "unknown"
        recv = recv_match.group(1).strip() if recv_match else None

        parts = [f"Wi-Fi is connected to '{ssid}' with {signal} signal strength."]
        if recv:
            parts.append(f"Receive rate is {recv} Megabits per second.")
        return " ".join(parts)
    except FileNotFoundError:
        return "Wi-Fi check requires Windows (netsh not found)."
    except Exception as exc:
        return f"Could not retrieve Wi-Fi status: {exc}"


# ---------------------------------------------------------------------------
# Bluetooth
# ---------------------------------------------------------------------------

# BT protocol/service/adapter keywords to strip — these are OS-level entries, not user devices
_BT_NOISE_PATTERNS: tuple[str, ...] = (
    "avrcp", " transport",
    "generic attribute", "generic access",
    "personal area network", "pan service", "nap service",
    "device information", "device identification",
    "headset audio gateway", "audio gateway",
    "hands-free", "handsfree",
    "bluetooth device", "bluetooth le",
    "object push", "phonebook access",
    "microsoft bluetooth", "android bluedroid", "bluedroid",
    "realtek bluetooth", "intel wireless bluetooth",
    "bluetooth adapter", "bluetooth enumerator", "ble enumerator",
    "bluetooth host", "bluetooth radio",
    "rfcomm", "l2cap", "serial port profile",
    "pnp information", "service discovery",
)


def _is_real_bt_device(name: str) -> bool:
    lower = name.lower()
    return not any(noise in lower for noise in _BT_NOISE_PATTERNS)


def get_bluetooth_status_text() -> str:
    """Return Bluetooth service state and actual connected device names (Windows)."""
    try:
        svc_cmd = (
            "Get-Service bthserv -ErrorAction SilentlyContinue | "
            "Select-Object -ExpandProperty Status"
        )
        svc_result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", svc_cmd],
            capture_output=True,
            text=True,
            timeout=10,
        )
        status = svc_result.stdout.strip()

        if not status:
            return "Bluetooth service not found. Bluetooth may not be available on this device."

        if status.lower() != "running":
            return "Bluetooth is off."

        dev_cmd = (
            "Get-PnpDevice -Class Bluetooth -Status OK -ErrorAction SilentlyContinue | "
            "Select-Object -ExpandProperty FriendlyName"
        )
        dev_result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", dev_cmd],
            capture_output=True,
            text=True,
            timeout=10,
        )
        raw = [ln.strip() for ln in dev_result.stdout.strip().splitlines() if ln.strip()]

        # Filter system/protocol/adapter entries and deduplicate
        seen: set[str] = set()
        devices: list[str] = []
        for d in raw:
            key = d.lower()
            if _is_real_bt_device(d) and key not in seen:
                seen.add(key)
                devices.append(d)

        if not devices:
            return "Bluetooth is on, but no devices are currently connected."

        # Cap output to avoid TTS timeout — speak first 3, show count if more
        if len(devices) == 1:
            return f"Bluetooth is on. Connected: {devices[0]}."
        if len(devices) <= 3:
            return f"Bluetooth is on. Connected: {', '.join(devices)}."
        preview = ", ".join(devices[:3])
        return f"Bluetooth is on. {len(devices)} devices connected: {preview}, and {len(devices) - 3} more."
    except Exception as exc:
        return f"Could not retrieve Bluetooth status: {exc}"


def _radio_toggle(kind: str, enable: bool) -> str:
    """Toggle a Windows radio (Bluetooth or WiFi) using the WinRT Radios API — no admin needed."""
    label = "on" if enable else "off"
    state = "On" if enable else "Off"
    ps_cmd = r"""
Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
$asTaskG = ([System.WindowsRuntimeSystemExtensions].GetMethods() |
    Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($task, $type) {
    $m = $asTaskG.MakeGenericMethod($type); $t = $m.Invoke($null,@($task)); $t.Wait(-1)|Out-Null; $t.Result
}
[Windows.Devices.Radios.Radio,Windows.System.Devices,ContentType=WindowsRuntime]|Out-Null
[Windows.Devices.Radios.RadioAccessStatus,Windows.System.Devices,ContentType=WindowsRuntime]|Out-Null
$radios = Await ([Windows.Devices.Radios.Radio]::GetRadiosAsync()) ([System.Collections.Generic.IReadOnlyList[Windows.Devices.Radios.Radio]])
$radio  = $radios | Where-Object { $_.Kind -eq 'KIND_PLACEHOLDER' } | Select-Object -First 1
if (-not $radio) { 'NOT_FOUND'; exit }
$result = Await ($radio.SetStateAsync('STATE_PLACEHOLDER')) ([Windows.Devices.Radios.RadioAccessStatus])
$result.ToString()
""".replace("KIND_PLACEHOLDER", kind).replace("STATE_PLACEHOLDER", state)

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=20,
        )
        out = result.stdout.strip().splitlines()
        last = out[-1].strip() if out else ""
        if last == "NOT_FOUND":
            return f"No {kind} radio found on this device."
        if last in ("Allowed", "Unspecified"):
            return f"{kind} turned {label}."
        if last == "DeniedBySystem":
            return f"Cannot turn {kind} {label}: Windows denied the request (Airplane mode may be on)."
        if last == "DeniedByUser":
            return f"Cannot turn {kind} {label}: blocked by user setting."
        return f"{kind} turned {label}."
    except subprocess.TimeoutExpired:
        return f"Could not toggle {kind}: operation timed out."
    except Exception as exc:
        return f"Could not toggle {kind}: {exc}"


def toggle_bluetooth(enable: bool) -> str:
    """Turn Bluetooth on/off using the Windows Radios API (no admin required)."""
    return _radio_toggle("Bluetooth", enable)


def toggle_wifi(enable: bool) -> str:
    """Turn Wi-Fi on/off using the Windows Radios API (no admin required)."""
    result = _radio_toggle("WiFi", enable)
    return result.replace("WiFi", "Wi-Fi")


# ---------------------------------------------------------------------------
# IP Addresses
# ---------------------------------------------------------------------------

def get_ip_address_text() -> str:
    """Return the local (LAN) IP address."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(3)
            sock.connect(("8.8.8.8", 80))
            local_ip = sock.getsockname()[0]
        return f"Your local IP address is {local_ip}."
    except Exception:
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return f"Your local IP address is {local_ip}."
        except Exception as exc:
            return f"Could not determine local IP address: {exc}"


def get_public_ip_text() -> str:
    """Return the public (WAN) IP address by querying an external service."""
    services = [
        "https://api.ipify.org",
        "https://icanhazip.com",
        "https://ifconfig.me/ip",
    ]
    for url in services:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "JARVIS/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:  # noqa: S310
                public_ip = resp.read().decode().strip()
                if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", public_ip):
                    return f"Your public IP address is {public_ip}."
        except Exception:
            continue
    return "Could not retrieve public IP. Check your internet connection."


# ---------------------------------------------------------------------------
# Network Interfaces
# ---------------------------------------------------------------------------

def get_network_interfaces_text() -> str:
    """Return a summary of active (up) network interfaces — capped for TTS."""
    try:
        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        active: list[str] = []

        for iface, stat in stats.items():
            if not stat.isup:
                continue
            ip = next(
                (a.address for a in addrs.get(iface, []) if a.family == socket.AF_INET),
                None,
            )
            line = iface
            if ip:
                line += f" ({ip})"
            active.append(line)

        if not active:
            return "No active network interfaces found."
        if len(active) == 1:
            return f"Active interface: {active[0]}."
        # Cap at 3 names to keep TTS response short
        preview = ", ".join(active[:3])
        suffix = f", and {len(active) - 3} more" if len(active) > 3 else ""
        return f"{len(active)} active interfaces: {preview}{suffix}."
    except Exception as exc:
        return f"Could not retrieve network interfaces: {exc}"


# ---------------------------------------------------------------------------
# Network Usage (data sent / received since boot)
# ---------------------------------------------------------------------------

def get_network_usage_text() -> str:
    """Return data sent and received since the last system boot."""
    try:
        io = psutil.net_io_counters()
        sent = io.bytes_sent
        recv = io.bytes_recv

        def _fmt(b: int) -> str:
            if b >= 1024 ** 3:
                return f"{b / 1024**3:.1f} gigabytes"
            return f"{b / 1024**2:.0f} megabytes"

        return (
            f"Since last boot: sent {_fmt(sent)}, received {_fmt(recv)}."
        )
    except Exception as exc:
        return f"Could not retrieve network usage: {exc}"


# ---------------------------------------------------------------------------
# Ping
# ---------------------------------------------------------------------------

def get_ping_text(host: str) -> str:
    """Ping a host 4 times and return latency and packet-loss result."""
    host = host.strip()
    # Validate to prevent command injection
    if not re.match(r"^[a-zA-Z0-9.\-]+$", host):
        return "Invalid hostname. Use only letters, numbers, dots, and hyphens."
    try:
        result = subprocess.run(
            ["ping", "-n", "4", host],
            capture_output=True,
            text=True,
            timeout=20,
        )
        output = result.stdout
        avg_match = re.search(r"Average\s*=\s*(\d+)ms", output, re.IGNORECASE)
        loss_match = re.search(r"\((\d+)%\s+loss\)", output, re.IGNORECASE)

        if result.returncode != 0 or not avg_match:
            return f"Could not reach {host}. The host may be unreachable or offline."

        avg_ms = avg_match.group(1)
        loss = loss_match.group(1) if loss_match else "0"

        if loss == "0":
            return (
                f"Ping to {host}: average response time {avg_ms} milliseconds "
                f"with no packet loss."
            )
        return (
            f"Ping to {host}: average {avg_ms} milliseconds with {loss} percent packet loss."
        )
    except subprocess.TimeoutExpired:
        return f"Ping to {host} timed out after 20 seconds."
    except Exception as exc:
        return f"Could not ping {host}: {exc}"


# ---------------------------------------------------------------------------
# Active Connections
# ---------------------------------------------------------------------------

def get_active_connections_text() -> str:
    """Return the count of established TCP connections and total sockets."""
    try:
        conns = psutil.net_connections(kind="inet")
        established = [c for c in conns if c.status == "ESTABLISHED"]
        return (
            f"There are {len(established)} established connections "
            f"and {len(conns)} total network sockets currently in use."
        )
    except Exception as exc:
        return f"Could not retrieve active connections: {exc}"
