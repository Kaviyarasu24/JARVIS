import datetime
import os
import subprocess

import cv2
import speech_recognition as sr


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


def open_windows_app(app_name: str) -> None:
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
        speak("I only support a few built-in Windows apps right now.")
        print("Supported apps:", ", ".join(sorted(app_map.keys())))
        return

    try:
        if target.endswith(":"):
            os.startfile(target)
        else:
            subprocess.Popen([target], shell=False)
        speak(f"Opening {key}.")
    except Exception as exc:
        speak(f"I could not open {key}.")
        print(f"Error: {exc}")


def main() -> None:
    if os.name != "nt":
        print("This simplified script supports Windows only.")
        return

    # Retry face authentication on failure
    while not authenticate_face():
        speak("Please try again.")

    greeting()
    print("Speak commands like: 'open notepad', 'open calculator', 'hello', 'exit'")

    while True:
        cmd = take_voice_command().strip().lower()

        if not cmd:
            continue
        if cmd in {"exit", "quit", "sleep"}:
            speak("Goodbye.")
            break
        if cmd in {"hello", "hi", "hey"}:
            greeting()
            continue
        if cmd.startswith("open "):
            open_windows_app(cmd.replace("open ", "", 1))
            continue

        speak("Please say hello, or use open command for a Windows app.")


if __name__ == "__main__":
    main()


    
