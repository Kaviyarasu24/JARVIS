"""Face authentication helpers for the JARVIS UI."""

from __future__ import annotations

import os

import cv2


def authenticate_face(speak) -> bool:
    """Authenticate the user with the trained OpenCV LBPH face model."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

    speak("Starting face recognition.")
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
                speak("Face recognition done. Welcome back sir.")
                return True

        frame_count += 1

    cam.release()
    cv2.destroyAllWindows()
    speak("Face recognition failed. Access denied.")
    return False
