"""
JARVIS - Just A Rather Very Intelligent System
Real-feel cinematic HUD color scheme
Install: pip install customtkinter
"""

import customtkinter as ctk
import tkinter as tk
import threading
import time
import math
import random
import datetime
import os
import subprocess
import cv2
import speech_recognition as sr

from features.calculator import calculate_text
from features.system_info import (
    BatteryNotificationState,
    check_battery_notifications,
    get_battery_status_text,
    get_system_info_text,
)
from features.tell_time import get_current_time_text
from features.todo_list import add_task, remove_task, view_tasks

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ─── CINEMATIC JARVIS PALETTE ─────────────────────────────────────────────────
BG           = "#000810"       # near-black deep space
PANEL        = "#000C1A"       # panel bg
RING_BRIGHT  = "#4DC8FF"       # main bright ring blue
RING_MID     = "#1A7AAF"       # mid blue arcs
RING_DIM     = "#0A3A55"       # dim ring / borders
RING_GLOW    = "#00AAFF"       # glow accent
ARC_CYAN     = "#00E5FF"       # fast-spin cyan arc
ARC_AMBER    = "#FF9500"       # amber accent (like Iron Man HUD)
ARC_GOLD     = "#FFD060"       # gold highlight ticks
TEXT_WHITE   = "#E8F4FF"       # center label
TEXT_SUB     = "#5AAFCC"       # subtitle / dim text
TEXT_GREEN   = "#00FF88"       # online / status green
TEXT_AMBER   = "#FFA030"       # amber status
STATUS_RED   = "#FF3B3B"       # alert red
TICK_MAJOR   = "#2A8EBB"       # major tick marks
TICK_MINOR   = "#0D3A50"       # minor tick marks
SCAN_LINE    = "#1A6A9A"       # hud scan line
INNER_FILL   = "#000D1F"       # inner orb fill
BORDER       = "#0D3550"       # frame borders


# ─── JARVIS Core Functions ────────────────────────────────────────────────────
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


def greeting() -> str:
    hour = int(datetime.datetime.now().hour)
    if 0 <= hour < 12:
        msg = "Good morning."
    elif 12 <= hour < 18:
        msg = "Good afternoon."
    else:
        msg = "Good evening."
    msg += " Welcome back sir. How can I assist you today?"
    return msg


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

    speak("Starting face recognition ")
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
                speak("Face Recognition Done. Welcome back sir.")
                return True

        frame_count += 1

    cam.release()
    cv2.destroyAllWindows()
    speak("Face recognition failed. Access denied.")
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
        msg = "I only support a few built-in Windows apps right now."
        print("Supported apps:", ", ".join(sorted(app_map.keys())))
        return msg

    try:
        if target.endswith(":"):
            os.startfile(target)
        else:
            subprocess.Popen([target], shell=False)
        return f"Opening {key}."
    except Exception as exc:
        msg = f"I could not open {key}."
        print(f"Error: {exc}")
        return msg


# ─── Jarvis Orb ───────────────────────────────────────────────────────────────
class JarvisOrb(tk.Canvas):
    def __init__(self, master, size=520, **kwargs):
        self.orb_size = size
        super().__init__(master, width=size, height=size,
                         bg="#000810", highlightthickness=0, **kwargs)
        self.size = size
        self.cx   = size / 2
        self.cy   = size / 2
        self.angle  = 0.0
        self.pulse  = 0
        self.active = False
        self._animate()

    def _animate(self):
        self.delete("all")
        cx, cy = self.cx, self.cy
        R = self.orb_size / 2 - 8

        # ── Deep radial glow behind orb ───────────────────────────────────
        for i in range(12, 0, -1):
            r  = R * 0.55 * i / 12
            lv = int(12 * i / 12)
            c  = f"#{0:02x}{lv:02x}{lv*2+4:02x}"
            self.create_oval(cx-r, cy-r, cx+r, cy+r, fill=c, outline="")

        # ── Ring 1 — outermost hairline ───────────────────────────────────
        self._oval(cx, cy, R*0.985, outline="#0A1E2E", width=1)
        self._oval(cx, cy, R*0.965, outline=RING_DIM,  width=1)

        # ── Outer tick band (120 ticks, slow CW) ──────────────────────────
        self._ticks(cx, cy, R*0.960, R*0.920,
                    count=120, major_every=10,
                    minor_col=TICK_MINOR, major_col=TICK_MAJOR,
                    offset=self.angle * 0.25)

        # ── Amber accent arc (slow CW, partial) ───────────────────────────
        self.create_arc(cx-R*0.91, cy-R*0.91, cx+R*0.91, cy+R*0.91,
                        start=self.angle*0.4,      extent=40,
                        outline=ARC_AMBER, width=3, style="arc")
        self.create_arc(cx-R*0.91, cy-R*0.91, cx+R*0.91, cy+R*0.91,
                        start=self.angle*0.4+180,  extent=25,
                        outline=ARC_GOLD,  width=2, style="arc")

        # ── Ring 2 — bright separator ────────────────────────────────────
        self._oval(cx, cy, R*0.880, outline=RING_MID,    width=2)
        self._oval(cx, cy, R*0.865, outline=RING_DIM,    width=1)

        # ── Main bold rotating arc (CW, bright blue) ──────────────────────
        self.create_arc(cx-R*0.845, cy-R*0.845, cx+R*0.845, cy+R*0.845,
                        start=self.angle, extent=255,
                        outline=RING_BRIGHT, width=4, style="arc")
        # trailing dim portion
        self.create_arc(cx-R*0.845, cy-R*0.845, cx+R*0.845, cy+R*0.845,
                        start=self.angle+265, extent=85,
                        outline=RING_DIM, width=2, style="arc")

        # ── Cyan fast counter-rotating arc ───────────────────────────────
        self.create_arc(cx-R*0.790, cy-R*0.790, cx+R*0.790, cy+R*0.790,
                        start=-self.angle*1.6, extent=180,
                        outline=ARC_CYAN, width=2, style="arc")
        self.create_arc(cx-R*0.790, cy-R*0.790, cx+R*0.790, cy+R*0.790,
                        start=-self.angle*1.6+190, extent=150,
                        outline=RING_DIM, width=1, style="arc")

        # ── Inner tick band (72 ticks, CCW) ──────────────────────────────
        self._ticks(cx, cy, R*0.755, R*0.715,
                    count=72, major_every=6,
                    minor_col="#0B2A3A", major_col=RING_MID,
                    offset=-self.angle*0.6)

        # ── Ring 3 — mid separator ────────────────────────────────────────
        self._oval(cx, cy, R*0.700, outline=RING_BRIGHT, width=2)
        self._oval(cx, cy, R*0.685, outline=RING_DIM,    width=1)

        # ── Slow inner glow arc ───────────────────────────────────────────
        self.create_arc(cx-R*0.660, cy-R*0.660, cx+R*0.660, cy+R*0.660,
                        start=self.angle*0.55, extent=300,
                        outline=RING_GLOW, width=2, style="arc")

        # ── Amber slow counter arc ────────────────────────────────────────
        self.create_arc(cx-R*0.620, cy-R*0.620, cx+R*0.620, cy+R*0.620,
                        start=-self.angle*0.3+45, extent=120,
                        outline=ARC_AMBER, width=1, style="arc")

        # ── Ring 4 — inner separator ──────────────────────────────────────
        self._oval(cx, cy, R*0.590, outline=RING_MID, width=2)

        # ── Innermost orb (pulsing) ───────────────────────────────────────
        pr = R * 0.470 * (1 + 0.018 * math.sin(self.pulse * 0.07))
        # outer glow layers
        for i in range(5, 0, -1):
            gr  = pr + i * 4
            lv  = int(8 * i / 5)
            gc  = f"#{0:02x}{lv:02x}{lv*3:02x}"
            self.create_oval(cx-gr, cy-gr, cx+gr, cy+gr, fill=gc, outline="")

        self.create_oval(cx-pr, cy-pr, cx+pr, cy+pr,
                         fill=INNER_FILL, outline=RING_BRIGHT, width=2)

        # inner rings inside orb
        for frac, col, w in [
            (0.80, "#0A2A40", 1),
            (0.58, "#081E30", 1),
            (0.35, "#060F20", 1),
        ]:
            r2 = pr * frac
            self.create_oval(cx-r2, cy-r2, cx+r2, cy+r2,
                             fill="", outline=col, width=w)

        # ── J.A.R.V.I.S. lettering ────────────────────────────────────────
        fs  = max(13, int(self.size * 0.050))
        sfs = max(7,  int(self.size * 0.020))

        # shadow/glow pass
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
            self.create_text(cx+dx*2, cy+dy*2 - int(fs*0.3),
                             text="JARVIS",
                             font=("Courier New", fs, "bold"),
                             fill="#003860")

        # main text
        self.create_text(cx, cy - int(fs*0.3),
                         text="JARVIS",
                         font=("Courier New", fs, "bold"),
                         fill=TEXT_WHITE)

        # status line — green=online, amber=active, red=alert
        if self.active:
            st_col, st_txt = TEXT_AMBER,  "ACTIVE"
        else:
            st_col, st_txt = TEXT_GREEN,  "STANDBY"
        self.create_text(cx, cy + int(fs * 1.05),
                         text=st_txt,
                         font=("Courier New", sfs, "bold"),
                         fill=st_col)

        # amber tick at top of inner orb
        a_top = math.radians(-90 + self.angle * 1.2)
        tx = cx + pr * math.cos(a_top)
        ty = cy + pr * math.sin(a_top)
        self.create_oval(tx-3, ty-3, tx+3, ty+3,
                         fill=ARC_AMBER, outline="")

        # center dot
        self.create_oval(cx-3, cy-3, cx+3, cy+3,
                         fill=RING_BRIGHT, outline="")

        self.angle = (self.angle + 1.1) % 360
        self.pulse += 1
        self.after(33, self._animate)

    def _oval(self, cx, cy, r, outline, width=1):
        self.create_oval(cx-r, cy-r, cx+r, cy+r,
                         outline=outline, width=width)

    def _ticks(self, cx, cy, r_out, r_in, count, major_every,
               minor_col, major_col, offset=0):
        for i in range(count):
            a   = math.radians(i * 360 / count + offset)
            ca, sa = math.cos(a), math.sin(a)
            major = (i % major_every == 0)
            ro = r_out
            ri = r_in if major else r_in + (r_out - r_in) * 0.45
            self.create_line(cx + ro*ca, cy + ro*sa,
                             cx + ri*ca, cy + ri*sa,
                             fill=major_col if major else minor_col,
                             width=2 if major else 1)

    def set_active(self, state: bool):
        self.active = state


# ─── HUD Scanline bar ─────────────────────────────────────────────────────────
class HUDBar(tk.Canvas):
    def __init__(self, master, height=14, **kwargs):
        super().__init__(master, height=height,
                         bg=BG, highlightthickness=0, **kwargs)
        self.h   = height
        self.pos = 0
        self._draw()

    def _draw(self):
        self.delete("all")
        w = self.winfo_width() or 1200
        # base line — uses SCAN_LINE color
        self.create_rectangle(0, self.h//2-1, w, self.h//2+1,
                               fill=SCAN_LINE, outline="")
        # STATUS_RED alert pips at far ends
        self.create_rectangle(0,   0, 4,   self.h, fill=STATUS_RED, outline="")
        self.create_rectangle(w-4, 0, w,   self.h, fill=STATUS_RED, outline="")
        # amber inner pips just inside the red ones
        self.create_rectangle(6,   0, 9,   self.h, fill=ARC_AMBER,  outline="")
        self.create_rectangle(w-9, 0, w-6, self.h, fill=ARC_AMBER,  outline="")
        # sweep
        seg = 140
        x   = self.pos % (w + seg) - seg
        for i in range(seg):
            a = i / seg
            c = RING_BRIGHT if a > 0.5 else RING_MID
            self.create_line(x+i, 0, x+i, self.h, fill=c)
        self.pos += 6
        self.after(26, self._draw)


# ─── Main App ─────────────────────────────────────────────────────────────────
class JarvisApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Jarvis  //  Developed by Kavi  //  Version 1")
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{sw}x{sh}+0+0")
        self.resizable(True, True)
        self.configure(fg_color=BG)
        self.authenticated = False
        self.battery_state = BatteryNotificationState()
        self._build_ui()
        self._start_clock()
        self._check_battery_notifications()
        # Start authentication in background
        threading.Thread(target=self._authenticate, daemon=True).start()

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=52)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Left: logo
        ctk.CTkLabel(header,
                     text="◈  Jarvis",
                     font=ctk.CTkFont("Courier New", 20, "bold"),
                     text_color=RING_BRIGHT).pack(side="left", padx=22, pady=10)

        ctk.CTkLabel(header,
                     text="Developed by Kavi  //  Version 1",
                     font=ctk.CTkFont("Courier New", 10),
                     text_color=TEXT_SUB).pack(side="left", padx=0, pady=10)

        # Right: clock + status
        self.clock_lbl = ctk.CTkLabel(header, text="",
                                      font=ctk.CTkFont("Courier New", 11),
                                      text_color=TEXT_SUB)
        self.clock_lbl.pack(side="right", padx=22)

        self.status_lbl = ctk.CTkLabel(header,
                                       text="● ONLINE",
                                       font=ctk.CTkFont("Courier New", 12, "bold"),
                                       text_color=TEXT_GREEN)
        self.status_lbl.pack(side="right", padx=28)

        # ── HUD scanline ──────────────────────────────────────────────────
        HUDBar(self, height=14).pack(fill="x", side="top")

        # ── Center area with orb ──────────────────────────────────────────
        center = ctk.CTkFrame(self, fg_color=BG)
        center.pack(fill="both", expand=True)

        # Left side: Transcript
        left_panel = ctk.CTkFrame(center, fg_color=PANEL, corner_radius=8, width=380)
        left_panel.pack(side="left", fill="both", padx=(20, 10), pady=20, expand=False)
        left_panel.pack_propagate(False)

        ctk.CTkLabel(left_panel,
                     text="◈ COMMAND LINE",
                     font=ctk.CTkFont("Courier New", 14, "bold"),
                     text_color=RING_BRIGHT).pack(pady=(15, 10))

        # Transcript text area
        self.transcript = ctk.CTkTextbox(
            left_panel,
            font=ctk.CTkFont("Courier New", 11),
            fg_color="#000D1F",
            text_color=TEXT_SUB,
            border_color=RING_DIM,
            border_width=1,
            corner_radius=4,
            wrap="word"
        )
        self.transcript.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.transcript.configure(state="disabled")

        # Center: Orb
        orb_frame = ctk.CTkFrame(center, fg_color=BG)
        orb_frame.pack(side="left", fill="both", expand=True)

        self.orb = JarvisOrb(orb_frame, size=486)
        self.orb.place(relx=0.5, rely=0.5, anchor="center")

        # Right side: Controls
        right_panel = ctk.CTkFrame(center, fg_color=PANEL, corner_radius=8, width=280)
        right_panel.pack(side="right", fill="both", padx=(10, 20), pady=20, expand=False)
        right_panel.pack_propagate(False)

        ctk.CTkLabel(right_panel,
                     text="◈ CONTROLS",
                     font=ctk.CTkFont("Courier New", 14, "bold"),
                     text_color=RING_BRIGHT).pack(pady=(15, 10))

        # Voice command button
        self.voice_btn = ctk.CTkButton(
            right_panel,
            text="🎤 VOICE COMMAND",
            font=ctk.CTkFont("Courier New", 12, "bold"),
            fg_color="#003A60",
            hover_color=RING_MID,
            text_color=RING_BRIGHT,
            border_width=2,
            border_color=RING_MID,
            corner_radius=6,
            height=38,
            command=self._on_voice,
            state="disabled"
        )
        self.voice_btn.pack(padx=15, pady=(0, 12), fill="x")

        # Greeting button
        self.greeting_btn = ctk.CTkButton(
            right_panel,
            text="👋 GREETING",
            font=ctk.CTkFont("Courier New", 11, "bold"),
            fg_color="#003A60",
            hover_color=RING_MID,
            text_color=RING_BRIGHT,
            border_width=1,
            border_color=RING_DIM,
            corner_radius=4,
            height=32,
            command=self._on_greeting,
            state="disabled"
        )
        self.greeting_btn.pack(padx=15, pady=(0, 8), fill="x")

        # Face auth button
        ctk.CTkButton(
            right_panel,
            text="🔐 RE-AUTHENTICATE",
            font=ctk.CTkFont("Courier New", 11, "bold"),
            fg_color="#003A60",
            hover_color=RING_MID,
            text_color=RING_BRIGHT,
            border_width=1,
            border_color=RING_DIM,
            corner_radius=4,
            height=32,
            command=lambda: threading.Thread(target=self._authenticate, daemon=True).start()
        ).pack(padx=15, pady=(0, 8), fill="x")

        # Clear transcript button
        self.clear_btn = ctk.CTkButton(
            right_panel,
            text="🗑️ CLEAR LOG",
            font=ctk.CTkFont("Courier New", 11, "bold"),
            fg_color="#003A60",
            hover_color=RING_MID,
            text_color=RING_BRIGHT,
            border_width=1,
            border_color=RING_DIM,
            corner_radius=4,
            height=32,
            command=self._clear_transcript,
            state="disabled"
        )
        self.clear_btn.pack(padx=15, pady=(0, 8), fill="x")

        # Info label
        info_text = (
            "Commands:\n"
            "• 'open [app]' - Open Windows apps\n"
            "• 'tell time' - Current time\n"
            "• 'system info' - CPU/RAM/Battery\n"
            "• 'calculate 25 plus 5' - Calculator\n"
            "• 'add task ...' / 'view tasks' / 'remove task ...'\n"
            "• 'hello' / 'hi' - Greeting\n"
            "• 'exit' / 'quit' - Stop listening\n\n"
            "Supported apps:\n"
            "notepad, calculator, paint,\n"
            "cmd, powershell, explorer,\n"
            "settings"
        )
        ctk.CTkLabel(
            right_panel,
            text=info_text,
            font=ctk.CTkFont("Courier New", 9),
            text_color=TEXT_SUB,
            justify="left",
            anchor="w",
            wraplength=245
        ).pack(padx=15, pady=(20, 15), fill="x")

        # ── Floating input — bottom right ─────────────────────────────────
        row = ctk.CTkFrame(self, fg_color="transparent")
        row.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-18)

        ctk.CTkLabel(row, text="▶",
                     font=ctk.CTkFont("Courier New", 15),
                     text_color=ARC_AMBER).pack(side="left", padx=(0, 6))

        self.input_var = tk.StringVar()
        self.entry = ctk.CTkEntry(
            row, textvariable=self.input_var,
            font=ctk.CTkFont("Courier New", 13),
            fg_color="#000F22",
            text_color=ARC_CYAN,
            border_color=RING_MID,
            border_width=1,
            corner_radius=4,
            width=420,
            placeholder_text="Enter directive...",
            placeholder_text_color="#1A4A6A",
            state="disabled"
        )
        self.entry.pack(side="left", padx=(0, 10))
        self.entry.bind("<Return>", self._on_send)

        self.send_btn = ctk.CTkButton(row,
                      text="SEND",
                      font=ctk.CTkFont("Courier New", 12, "bold"),
                      fg_color="#003A60",
                      hover_color=RING_MID,
                      text_color=RING_BRIGHT,
                      border_width=1,
                      border_color=RING_MID,
                      corner_radius=4,
                      width=80,
                      command=self._on_send,
                      state="disabled")
        self.send_btn.pack(side="left")

    def _on_send(self, event=None):
        if not self.authenticated:
            self._add_to_transcript("SYSTEM: Please authenticate first")
            return
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set("")
        self._add_to_transcript(f"YOU: {text}")
        self.orb.set_active(True)
        self.status_lbl.configure(text="● PROCESSING", text_color=TEXT_AMBER)
        threading.Thread(target=self._process, args=(text,), daemon=True).start()

    def _on_voice(self):
        if not self.authenticated:
            self._add_to_transcript("SYSTEM: Please authenticate first")
            return
        self.voice_btn.configure(state="disabled", text="🎤 LISTENING...")
        self.orb.set_active(True)
        self.status_lbl.configure(text="● LISTENING", text_color=TEXT_AMBER)
        threading.Thread(target=self._voice_command, daemon=True).start()

    def _on_greeting(self):
        if not self.authenticated:
            self._add_to_transcript("SYSTEM: Please authenticate first")
            return
        self.orb.set_active(True)
        self.status_lbl.configure(text="● SPEAKING", text_color=TEXT_AMBER)
        threading.Thread(target=self._greeting_thread, daemon=True).start()

    def _greeting_thread(self):
        msg = greeting()
        self._add_to_transcript(f"JARVIS: {msg}")
        speak(msg)
        self.after(0, lambda: (
            self.orb.set_active(False),
            self.status_lbl.configure(text="● ONLINE", text_color=TEXT_GREEN)
        ))

    def _voice_command(self):
        cmd = take_voice_command().strip().lower()
        self.after(0, lambda: self.voice_btn.configure(state="normal", text="🎤 VOICE COMMAND"))
        if cmd:
            self._add_to_transcript(f"YOU: {cmd}")
            self._process(cmd)
        else:
            self.after(0, lambda: (
                self.orb.set_active(False),
                self.status_lbl.configure(text="● ONLINE", text_color=TEXT_GREEN)
            ))

    def _process(self, text):
        cmd = text.strip().lower()
        response = ""

        if cmd in {"exit", "quit", "sleep"}:
            response = "Goodbye."
        elif cmd in {"hello", "hi", "hey"}:
            response = greeting()
        elif cmd.startswith("open "):
            app_name = cmd.replace("open ", "", 1)
            response = open_windows_app(app_name)
        elif cmd in {"tell time", "what time is it", "time"}:
            response = get_current_time_text()
        elif cmd in {"system info", "system information", "pc status"}:
            response = get_system_info_text()
        elif cmd in {"battery", "battery status"}:
            response = get_battery_status_text()
        elif cmd.startswith("calculate "):
            response = calculate_text(cmd.replace("calculate ", "", 1))
        elif cmd.startswith("what is "):
            response = calculate_text(cmd.replace("what is ", "", 1))
        elif cmd.startswith("add task "):
            response = add_task(cmd.replace("add task ", "", 1))
        elif cmd in {"show tasks", "view tasks", "list tasks", "todo list"}:
            response = view_tasks()
        elif cmd.startswith("remove task "):
            response = remove_task(cmd.replace("remove task ", "", 1))
        else:
            response = "Unknown command. Try time, system info, calculate, or todo commands."

        self._add_to_transcript(f"JARVIS: {response}")
        speak(response)
        
        self.after(0, lambda: (
            self.orb.set_active(False),
            self.status_lbl.configure(text="● ONLINE", text_color=TEXT_GREEN)
        ))

    def _authenticate(self):
        self._add_to_transcript("SYSTEM: Starting face authentication...")
        self.after(0, lambda: self.status_lbl.configure(
            text="● AUTHENTICATING", text_color=STATUS_RED))
        
        result = authenticate_face()
        self.authenticated = result
        
        if result:
            self._add_to_transcript("SYSTEM: Authentication successful!")
            # Enable all controls
            self.after(0, lambda: (
                self.voice_btn.configure(state="normal"),
                self.greeting_btn.configure(state="normal"),
                self.clear_btn.configure(state="normal"),
                self.entry.configure(state="normal"),
                self.send_btn.configure(state="normal"),
                self.entry.focus()
            ))
            msg = greeting()
            self._add_to_transcript(f"JARVIS: {msg}")
            speak(msg)
            self.after(0, lambda: self.status_lbl.configure(
                text="● ONLINE", text_color=TEXT_GREEN))
        else:
            self._add_to_transcript("SYSTEM: Authentication failed. Try again.")
            # Keep controls disabled
            self.after(0, lambda: (
                self.voice_btn.configure(state="disabled"),
                self.greeting_btn.configure(state="disabled"),
                self.clear_btn.configure(state="disabled"),
                self.entry.configure(state="disabled"),
                self.send_btn.configure(state="disabled"),
                self.status_lbl.configure(text="● LOCKED", text_color=STATUS_RED)
            ))

    def _add_to_transcript(self, text):
        def update():
            self.transcript.configure(state="normal")
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.transcript.insert("end", f"[{timestamp}] {text}\n")
            self.transcript.see("end")
            self.transcript.configure(state="disabled")
        self.after(0, update)

    def _clear_transcript(self):
        self.transcript.configure(state="normal")
        self.transcript.delete("1.0", "end")
        self.transcript.configure(state="disabled")

    def _start_clock(self):
        self.clock_lbl.configure(
            text=datetime.datetime.now().strftime("SYS  %H:%M:%S  //  %d.%m.%Y"))
        self.after(1000, self._start_clock)

    def _speak_battery_notification(self, message):
        # Keep TTS off the UI thread so center animation can continue rendering.
        self.orb.set_active(True)
        self.status_lbl.configure(text="● SPEAKING", text_color=TEXT_AMBER)

        def worker():
            speak(message)
            self.after(0, lambda: (
                self.orb.set_active(False),
                self.status_lbl.configure(text="● ONLINE", text_color=TEXT_GREEN)
            ))

        threading.Thread(target=worker, daemon=True).start()

    def _check_battery_notifications(self):
        if self.authenticated:
            battery_message = check_battery_notifications(self.battery_state)
            if battery_message:
                self._add_to_transcript(f"JARVIS: {battery_message}")
                self._speak_battery_notification(battery_message)

        # Poll very frequently so charger connect/disconnect is announced quickly.
        self.after(1000, self._check_battery_notifications)


# ─── Entry ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()
