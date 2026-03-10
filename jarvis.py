import datetime
import os
import subprocess

import cv2
import speech_recognition as sr

from features.calculator import calculate_text
from features.command_normalizer import normalize_command
from features.system_info import (
    BatteryNotificationState,
    check_battery_notifications,
    get_battery_status_text,
    get_system_info_text,
)
from features.network_status import (
    get_active_connections_text,
    get_bluetooth_status_text,
    get_ip_address_text,
    get_network_interfaces_text,
    get_network_usage_text,
    get_ping_text,
    get_public_ip_text,
    get_wifi_status_text,
    toggle_bluetooth,
    toggle_wifi,
)
from features.tell_time import get_current_time_text
from features.todo_list import add_task, remove_task, view_tasks


def speak(text: str) -> None:
    """Use PowerShell's native System.Speech for reliable Windows text-to-speech."""
    message = f"{text}"
    print(message)
    try:
        ps_cmd = f'''
Add-Type -AssemblyName System.Speech
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Speak('{message}')
'''
        subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_cmd],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15
        )
    except Exception as exc:
        print(f"Speech error: {exc}")


def greeting() -> None:
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour < 12:
        speak("Good morning.")
    elif 12 <= hour < 18:
        speak("Good afternoon.")
    else:
        speak("Good evening.")
    speak("I am JARVIS. I can open Windows apps for you.")


def take_voice_command() -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.pause_threshold = 1
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)

    try:
        print("Recognizing...")
        query = recognizer.recognize_google(audio, language="en-in")
        print(f"You said: {query}")
        return query.lower()
    except Exception:
        print("Could not understand. Please speak again.")
        return ""


def authenticate_face() -> bool:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    trainer_path = os.path.join(base_dir, "Face-Recognition", "trainer", "trainer.yml")
    local_cascade = os.path.join(base_dir, "Face-Recognition", "haarcascade_frontalface_default.xml")
    cascade_path = local_cascade if os.path.exists(local_cascade) else os.path.join(
        cv2.data.haarcascades, "haarcascade_frontalface_default.xml"
    )

    if not os.path.exists(trainer_path):
        print("Trainer model not found. Run Face-Recognition/Model Trainer.py first.")
        return False

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(trainer_path)

    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        print("Failed to load face cascade classifier.")
        return False

    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cam.isOpened():
        print("Could not access webcam.")
        return False

    speak("Starting face recognition. Please look at the camera.")
    matched_frames = 0
    max_frames = 120
    frame_count = 0

    while frame_count < max_frames:
        ret, img = cam.read()
        if not ret:
            frame_count += 1
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        for (x, y, w, h) in faces:
            _, confidence = recognizer.predict(gray[y:y + h, x:x + w])
            if confidence < 70:
                matched_frames += 1
            if matched_frames >= 3:
                cam.release()
                cv2.destroyAllWindows()
                speak("Optical Face Recognition Done. Welcome.")
                return True

        frame_count += 1

    cam.release()
    cv2.destroyAllWindows()
    speak("Optical Face Recognition Failed.")
    return False


def open_windows_app(app_name: str) -> str:
    app_map = {
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
    }

    key = app_name.strip().lower()
    target = app_map.get(key)
    if not target:
        message = "I only support a few built-in Windows apps right now."
        print("Supported apps:", ", ".join(sorted(app_map.keys())))
        return message

    try:
        if target.endswith(":"):
            os.startfile(target)
        else:
            subprocess.Popen([target], shell=False)
        return f"Opening {key}."
    except Exception as exc:
        print(f"Error: {exc}")
        return f"I could not open {key}."


def process_command(cmd: str) -> str:
    """Route voice command text to the corresponding feature response."""
    cmd = normalize_command(cmd).strip().lower()

    if cmd in {"exit", "quit", "sleep"}:
        return "Goodbye."

    if cmd in {"hello", "hi", "hey"}:
        hour = int(datetime.datetime.now().hour)
        if 0 <= hour < 12:
            return "Good morning. I am JARVIS."
        if 12 <= hour < 18:
            return "Good afternoon. I am JARVIS."
        return "Good evening. I am JARVIS."

    if cmd.startswith("open "):
        app_name = cmd.replace("open ", "", 1)
        return open_windows_app(app_name)

    if cmd in {"tell time", "what time is it", "time"}:
        return get_current_time_text()

    if cmd in {"system info", "system information", "pc status"}:
        return get_system_info_text()

    if cmd in {"battery", "battery status"}:
        return get_battery_status_text()

    if cmd.startswith("calculate "):
        return calculate_text(cmd.replace("calculate ", "", 1))

    if cmd.startswith("what is "):
        return calculate_text(cmd.replace("what is ", "", 1))

    if cmd.startswith("add task "):
        return add_task(cmd.replace("add task ", "", 1))

    if cmd in {"show tasks", "view tasks", "list tasks", "todo list"}:
        return view_tasks()

    if cmd.startswith("remove task "):
        return remove_task(cmd.replace("remove task ", "", 1))

    # ---- Network features ----
    if cmd in {"wifi", "wifi status", "wi-fi", "wi-fi status", "wireless"}:
        return get_wifi_status_text()

    if cmd in {"turn on wifi", "enable wifi", "wifi on"}:
        return toggle_wifi(True)

    if cmd in {"turn off wifi", "disable wifi", "wifi off"}:
        return toggle_wifi(False)

    if cmd in {"bluetooth", "bluetooth status", "bt status"}:
        return get_bluetooth_status_text()

    if cmd in {"turn on bluetooth", "enable bluetooth", "bluetooth on"}:
        return toggle_bluetooth(True)

    if cmd in {"turn off bluetooth", "disable bluetooth", "bluetooth off"}:
        return toggle_bluetooth(False)

    if cmd in {"ip address", "my ip", "local ip", "ip"}:
        return get_ip_address_text()

    if cmd in {"public ip", "external ip", "my public ip", "wan ip"}:
        return get_public_ip_text()

    if cmd in {"network interfaces", "network adapters", "interfaces"}:
        return get_network_interfaces_text()

    if cmd in {"network usage", "data usage", "bandwidth usage", "network stats"}:
        return get_network_usage_text()

    if cmd in {"active connections", "connections", "network connections"}:
        return get_active_connections_text()

    if cmd.startswith("ping "):
        return get_ping_text(cmd.replace("ping ", "", 1))

    return "Unknown command. Try: tell time, system info, wifi, bluetooth, ip address, or todo commands."


def main() -> None:
    if os.name != "nt":
        print("This simplified script supports Windows only.")
        return

    # Retry face authentication on failure
    while not authenticate_face():
        speak("Please try again.")

    greeting()
    print(
        "Speak commands like: 'open notepad', 'tell time', 'system info', "
        "'calculate 25 plus 5', 'add task buy milk', 'view tasks', 'exit'"
    )
    battery_state = BatteryNotificationState()

    while True:
        battery_message = check_battery_notifications(battery_state)
        if battery_message:
            speak(battery_message)

        cmd = take_voice_command().strip().lower()

        if not cmd:
            continue
        response = process_command(cmd)
        speak(response)

        if cmd in {"exit", "quit", "sleep"}:
            break


if __name__ == "__main__":
    main()


    
