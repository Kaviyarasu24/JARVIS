import datetime
import os
import queue
import subprocess
import threading

import cv2
import speech_recognition as sr

from features import agent
from features.system_info import (
    BatteryNotificationState,
    check_battery_notifications,
)
from features.network_status import (
    NetworkNotificationState,
    check_network_notifications,
)
from features.reminders import pop_due_notifications


def _tts_safe(text: str) -> str:
    """Transliterate to ASCII and escape single quotes for PowerShell."""
    import unicodedata
    ascii_text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return ascii_text.replace("'", "''")


# ─── Speech Queue ─────────────────────────────────────────────────────────────
_speech_queue: queue.Queue = queue.Queue()


def _speech_worker() -> None:
    """Background thread: speaks items from the queue one at a time."""
    while True:
        text = _speech_queue.get()
        if text is None:          # sentinel – shut down worker
            break
        safe = _tts_safe(text)
        try:
            ps_cmd = f'''
Add-Type -AssemblyName System.Speech
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Speak('{safe}')
'''
            subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as exc:
            print(f"Speech error: {exc}")
        finally:
            _speech_queue.task_done()


_speech_thread = threading.Thread(target=_speech_worker, daemon=True, name="SpeechWorker")
_speech_thread.start()


def speak(text: str) -> None:
    """Enqueue text for serial TTS – prevents simultaneous speech collisions."""
    print(text)
    _speech_queue.put(text)


def greeting() -> None:
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour < 12:
        speak("Good morning.")
    elif 12 <= hour < 18:
        speak("Good afternoon.")
    else:
        speak("Good evening.")
    speak("I am JARVIS. How can I assist you?")


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


# open_windows_app is now handled by features/system_control.py -> open_app
# and registered as the 'open_app' tool in features/tools.py


def process_command(cmd: str) -> str:
    """Compatibility wrapper: route commands through the goal-based agent."""
    return agent.run(cmd)


def main() -> None:
    if os.name != "nt":
        print("This simplified script supports Windows only.")
        return

    # Retry face authentication on failure
    while not authenticate_face():
        speak("Please try again.")

    greeting()
    print(
        "\nJARVIS is ready. Speak naturally — examples:\n"
        "  'what's the weather in Paris'  'add milk to my tasks'\n"
        "  'tell me a joke'  'open chrome'  'shutdown in 30 seconds'\n"
    )
    battery_state = BatteryNotificationState()
    network_state = NetworkNotificationState()

    while True:
        battery_message = check_battery_notifications(battery_state)
        if battery_message:
            speak(battery_message)

        net_message = check_network_notifications(network_state)
        if net_message:
            speak(net_message)

        for reminder_message in pop_due_notifications(limit=3):
            speak(reminder_message)

        user_input = take_voice_command().strip()

        if not user_input:
            continue

        response = agent.run(user_input)
        speak(response)

        if user_input.lower() in {"exit", "quit", "goodbye", "bye"}:
            break


if __name__ == "__main__":
    main()


    
