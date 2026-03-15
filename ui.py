"""
JARVIS - Just A Rather Very Intelligent System
Colorful cinematic HUD theme
Install: pip install customtkinter
"""

import customtkinter as ctk
import tkinter as tk
import threading
import time
import math
import random
import datetime
import calendar
import os
import queue
import subprocess
import cv2
import speech_recognition as sr

from features.calculator import calculate_text
from features.command_normalizer import normalize_command
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
    NetworkNotificationState,
    check_network_notifications,
)
from features.system_info import (
    BatteryNotificationState,
    check_battery_notifications,
    get_battery_status_text,
    get_system_info_text,
)
from features.news_headlines import get_news_text
from features.stock_market import get_crypto_text, get_stock_text
from features.tell_time import get_current_time_text
from features.todo_list import add_task, remove_task, view_tasks, get_tasks_for_date, update_task
from features.weather import get_weather_text
from features.wikipedia_search import search_wikipedia

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ─── CINEMATIC JARVIS PALETTE (SINGLE BLUE FAMILY) ──────────────────────────
BG           = "#070B1A"       # deep night blue
PANEL        = "#101A36"       # elevated panel base
PANEL_SOFT   = "#162248"       # panel accents
RING_BRIGHT  = "#37E7FF"       # electric cyan
RING_MID     = "#2A9FD6"       # mid cyan blue
RING_DIM     = "#1D4F75"       # dim ring / borders
RING_GLOW    = "#00C2FF"       # glow accent
ARC_CYAN     = "#4AF7FF"       # fast-spin cyan arc
ARC_AMBER    = "#2B7CC2"       # unified accent blue
ARC_GOLD     = "#5CB5F0"       # unified highlight blue
TEXT_WHITE   = "#EEF5FF"       # center label
TEXT_SUB     = "#8DB6E8"       # subtitle / dim text
TEXT_GREEN   = "#71D7FF"       # online / status cyan
TEXT_AMBER   = "#64BFFF"       # active/listening blue
STATUS_RED   = "#4C93D6"       # auth/alert blue tone
TICK_MAJOR   = "#5AB9E6"       # major tick marks
TICK_MINOR   = "#204D72"       # minor tick marks
SCAN_LINE    = "#2D79AD"       # hud scan line
INNER_FILL   = "#0D1735"       # inner orb fill
BORDER       = "#2A5E8A"       # frame borders

BTN_PRIMARY  = "#1E5C9A"
BTN_PRIMARY_HOVER = "#2772BC"
BTN_SECONDARY = "#16577A"
BTN_SECONDARY_HOVER = "#1F6E98"
BTN_WARN = "#1B5D93"
BTN_WARN_HOVER = "#2675B4"
BTN_DANGER = "#164F80"
BTN_DANGER_HOVER = "#1F699F"
BTN_DANGER_BORDER = "#4A9AD8"
INPUT_BG = "#0C1633"
LOG_BG = "#0A1630"
ORB_SCALE = 0.60


# ─── JARVIS Core Functions ────────────────────────────────────────────────────
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
                 bg=BG, highlightthickness=0, **kwargs)
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
            c  = f"#{2:02x}{lv+3:02x}{lv*2+8:02x}"
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
                             fill="#0A4A72")

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
        frame_delay = 40 if self.active else 72
        self.after(frame_delay, self._animate)

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

    def resize_orb(self, size: int):
        self.orb_size = size
        self.size = size
        self.cx = size / 2
        self.cy = size / 2
        self.configure(width=size, height=size)


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
        width = int(sw * 0.94)
        height = int(sh * 0.92)
        self.geometry(f"{width}x{height}+0+0")
        self._min_width = 1180
        self._min_height = 700
        self.minsize(self._min_width, self._min_height)
        self.resizable(True, True)
        self.configure(fg_color=BG)
        self.authenticated = False
        self.battery_state = BatteryNotificationState()
        self.network_state = NetworkNotificationState()
        self._resize_job = None
        self._build_ui()
        self._start_clock()
        self._check_battery_notifications()
        self._check_network_notifications()
        self.bind("<Configure>", self._on_window_resize)
        self.after(150, self._apply_responsive_layout)
        # Start authentication in background
        threading.Thread(target=self._authenticate, daemon=True).start()

    @staticmethod
    def _clamp(value: int, low: int, high: int) -> int:
        return max(low, min(value, high))

    def _build_ui(self):
        # ── Header ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=56)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Left: logo
        ctk.CTkLabel(header,
                     text="◈  JARVIS",
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

        # Top scanline removed to reduce render overhead and UI jitter.

        # ── Center area with orb ──────────────────────────────────────────
        center = ctk.CTkFrame(self, fg_color=BG)
        center.pack(fill="both", expand=True)

        # Left side: Transcript
        self.left_panel = ctk.CTkFrame(
            center,
            fg_color=PANEL,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
            width=390,
        )
        self.left_panel.pack(side="left", fill="both", padx=(20, 10), pady=20, expand=False)
        self.left_panel.pack_propagate(False)

        ctk.CTkLabel(self.left_panel,
                     text="◈ COMMAND LINE",
                     font=ctk.CTkFont("Courier New", 14, "bold"),
                     text_color=RING_BRIGHT).pack(pady=(15, 10))

        # Transcript text area
        self.transcript = ctk.CTkTextbox(
            self.left_panel,
            font=ctk.CTkFont("Courier New", 11),
            fg_color=LOG_BG,
            text_color="#BBD5F8",
            border_color=BORDER,
            border_width=1,
            corner_radius=8,
            wrap="word"
        )
        self.transcript.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.transcript.configure(state="disabled")

        # Center: Orb
        self.orb_frame = ctk.CTkFrame(center, fg_color=BG)
        self.orb_frame.pack(side="left", fill="both", expand=True)

        self.orb = JarvisOrb(self.orb_frame, size=int(486 * ORB_SCALE))
        self.orb.place(relx=0.5, rely=0.5, anchor="center")

        # Right side: Controls
        self.right_panel = ctk.CTkFrame(
            center,
            fg_color=PANEL_SOFT,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
            width=270,
            height=620,
        )
        self.right_panel.pack(side="right", fill="y", padx=(10, 20), pady=20, expand=False)
        self.right_panel.pack_propagate(False)

        ctk.CTkLabel(self.right_panel,
                     text="◈ CONTROLS",
                     font=ctk.CTkFont("Courier New", 14, "bold"),
                     text_color=RING_BRIGHT).pack(pady=(15, 10))

        # Voice command button
        self.voice_btn = ctk.CTkButton(
            self.right_panel,
            text="🎤 VOICE COMMAND",
            font=ctk.CTkFont("Courier New", 12, "bold"),
            fg_color=BTN_PRIMARY,
            hover_color=BTN_PRIMARY_HOVER,
            text_color="#EAF6FF",
            border_width=2,
            border_color="#4AB4F2",
            corner_radius=8,
            height=40,
            command=self._on_voice,
            state="disabled"
        )
        self.voice_btn.pack(padx=15, pady=(0, 12), fill="x")

        # Greeting button
        self.greeting_btn = ctk.CTkButton(
            self.right_panel,
            text="👋 GREETING",
            font=ctk.CTkFont("Courier New", 11, "bold"),
            fg_color=BTN_SECONDARY,
            hover_color=BTN_SECONDARY_HOVER,
            text_color="#EAF6FF",
            border_width=1,
            border_color="#4AAEE0",
            corner_radius=8,
            height=32,
            command=self._on_greeting,
            state="disabled"
        )
        self.greeting_btn.pack(padx=15, pady=(0, 8), fill="x")

        # Face auth button
        ctk.CTkButton(
            self.right_panel,
            text="🔐 RE-AUTHENTICATE",
            font=ctk.CTkFont("Courier New", 11, "bold"),
            fg_color=BTN_WARN,
            hover_color=BTN_WARN_HOVER,
            text_color="#FFF7EE",
            border_width=1,
            border_color="#F6B066",
            corner_radius=8,
            height=32,
            command=lambda: threading.Thread(target=self._authenticate, daemon=True).start()
        ).pack(padx=15, pady=(0, 8), fill="x")

        # Clear transcript button
        self.clear_btn = ctk.CTkButton(
            self.right_panel,
            text="🗑️ CLEAR LOG",
            font=ctk.CTkFont("Courier New", 11, "bold"),
            fg_color=BTN_DANGER,
            hover_color=BTN_DANGER_HOVER,
            text_color="#EAF6FF",
            border_width=1,
            border_color=BTN_DANGER_BORDER,
            corner_radius=8,
            height=32,
            command=self._clear_transcript,
            state="disabled"
        )
        self.clear_btn.pack(padx=15, pady=(0, 15), fill="x")

        # Todo calendar controls
        self.todo_panel = ctk.CTkFrame(
            self.right_panel,
            fg_color=INPUT_BG,
            corner_radius=10,
            border_width=1,
            border_color=BORDER,
        )
        self.todo_panel.pack(padx=15, pady=(0, 15), fill="both", expand=True)

        ctk.CTkLabel(
            self.todo_panel,
            text="TASK CALENDAR",
            font=ctk.CTkFont("Courier New", 11, "bold"),
            text_color=RING_BRIGHT,
        ).pack(pady=(8, 6))

        today = datetime.date.today()
        self.todo_selected_date = today
        self.todo_visible_year = today.year
        self.todo_visible_month = today.month
        self._calendar_enabled = False
        self.todo_task_var = tk.StringVar()
        self._todo_task_rows = []

        month_row = ctk.CTkFrame(self.todo_panel, fg_color="transparent")
        month_row.pack(fill="x", padx=8, pady=(0, 2))

        self.cal_prev_btn = ctk.CTkButton(
            month_row,
            text="<",
            width=28,
            height=24,
            fg_color=BTN_SECONDARY,
            hover_color=BTN_SECONDARY_HOVER,
            command=lambda: self._shift_calendar_month(-1),
            state="disabled",
        )
        self.cal_prev_btn.pack(side="left")

        self.cal_month_label = ctk.CTkLabel(
            month_row,
            text="",
            font=ctk.CTkFont("Courier New", 10, "bold"),
            text_color="#D7ECFF",
        )
        self.cal_month_label.pack(side="left", expand=True)

        self.cal_next_btn = ctk.CTkButton(
            month_row,
            text=">",
            width=28,
            height=24,
            fg_color=BTN_SECONDARY,
            hover_color=BTN_SECONDARY_HOVER,
            command=lambda: self._shift_calendar_month(1),
            state="disabled",
        )
        self.cal_next_btn.pack(side="right")

        weekday_row = ctk.CTkFrame(self.todo_panel, fg_color="transparent")
        weekday_row.pack(fill="x", padx=8)
        for weekday in ["M", "T", "W", "T", "F", "S", "S"]:
            ctk.CTkLabel(
                weekday_row,
                text=weekday,
                width=26,
                font=ctk.CTkFont("Courier New", 9, "bold"),
                text_color="#7FA8D3",
            ).pack(side="left", expand=True)

        self.cal_grid = ctk.CTkFrame(self.todo_panel, fg_color="transparent")
        self.cal_grid.pack(fill="x", padx=8, pady=(0, 4))

        self.cal_day_buttons = []
        self.cal_day_dates = []
        for row in range(6):
            for col in range(7):
                btn = ctk.CTkButton(
                    self.cal_grid,
                    text="",
                    width=26,
                    height=22,
                    corner_radius=6,
                    font=ctk.CTkFont("Courier New", 9),
                    fg_color="#0E2140",
                    hover_color="#17406D",
                    text_color="#A8C9EA",
                    border_width=0,
                    command=lambda idx=len(self.cal_day_buttons): self._on_calendar_day_click(idx),
                    state="disabled",
                )
                btn.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
                self.cal_day_buttons.append(btn)
                self.cal_day_dates.append(today)

        for idx in range(7):
            self.cal_grid.grid_columnconfigure(idx, weight=1)

        self.todo_task_entry = ctk.CTkEntry(
            self.todo_panel,
            textvariable=self.todo_task_var,
            font=ctk.CTkFont("Courier New", 10),
            fg_color=LOG_BG,
            text_color="#D3E7FF",
            border_color="#4FAEE6",
            border_width=1,
            corner_radius=6,
            placeholder_text="Task details...",
            state="disabled",
        )
        self.todo_task_entry.pack(fill="x", padx=8, pady=(8, 6))

        actions_row = ctk.CTkFrame(self.todo_panel, fg_color="transparent")
        actions_row.pack(fill="x", padx=8)

        self.todo_add_btn = ctk.CTkButton(
            actions_row,
            text="ADD",
            width=80,
            height=28,
            font=ctk.CTkFont("Courier New", 10, "bold"),
            fg_color=BTN_PRIMARY,
            hover_color=BTN_PRIMARY_HOVER,
            command=self._on_add_task_from_calendar,
            state="disabled",
        )
        self.todo_add_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.todo_update_btn = ctk.CTkButton(
            actions_row,
            text="UPDATE",
            width=80,
            height=28,
            font=ctk.CTkFont("Courier New", 10, "bold"),
            fg_color=BTN_WARN,
            hover_color=BTN_WARN_HOVER,
            command=self._on_update_selected_task,
            state="disabled",
        )
        self.todo_update_btn.pack(side="left", fill="x", expand=True, padx=(4, 0))

        list_wrap = ctk.CTkFrame(
            self.todo_panel,
            fg_color=LOG_BG,
            corner_radius=8,
            border_width=1,
            border_color=BORDER,
            height=110,
        )
        list_wrap.pack(fill="both", expand=True, padx=8, pady=(8, 8))
        list_wrap.pack_propagate(False)

        self.todo_listbox = tk.Listbox(
            list_wrap,
            height=8,
            bg=LOG_BG,
            fg="#BBD5F8",
            selectbackground="#1E5C9A",
            selectforeground="#EEF7FF",
            borderwidth=0,
            highlightthickness=0,
            activestyle="none",
            font=("Courier New", 9),
            state="disabled",
        )
        self.todo_listbox.pack(side="left", fill="both", expand=True, padx=(6, 0), pady=6)
        self.todo_listbox.bind("<<ListboxSelect>>", self._on_task_list_select)

        self.todo_scroll = ctk.CTkScrollbar(list_wrap, command=self.todo_listbox.yview)
        self.todo_scroll.pack(side="right", fill="y", padx=6, pady=6)
        self.todo_listbox.configure(yscrollcommand=self.todo_scroll.set)

        self._rebuild_calendar_grid()

        # ── Floating input — bottom right ─────────────────────────────────
        self.input_row = ctk.CTkFrame(self, fg_color="transparent")
        self.input_row.place(relx=1.0, rely=1.0, anchor="se", x=-20, y=-18)

        ctk.CTkLabel(self.input_row, text="▶",
                     font=ctk.CTkFont("Courier New", 15),
                     text_color=ARC_AMBER).pack(side="left", padx=(0, 6))

        self.input_var = tk.StringVar()
        self.entry = ctk.CTkEntry(
            self.input_row, textvariable=self.input_var,
            font=ctk.CTkFont("Courier New", 13),
            fg_color=INPUT_BG,
            text_color="#D3E7FF",
            border_color="#4FAEE6",
            border_width=1,
            corner_radius=8,
            width=420,
            placeholder_text="Enter directive...",
            placeholder_text_color="#6C90B8",
            state="disabled"
        )
        self.entry.pack(side="left", padx=(0, 10))
        self.entry.bind("<Return>", self._on_send)

        self.send_btn = ctk.CTkButton(self.input_row,
                      text="SEND",
                      font=ctk.CTkFont("Courier New", 12, "bold"),
                      fg_color=BTN_PRIMARY,
                      hover_color=BTN_PRIMARY_HOVER,
                      text_color="#EEF7FF",
                      border_width=1,
                      border_color="#4AB4F2",
                      corner_radius=8,
                      width=80,
                      command=self._on_send,
                      state="disabled")
        self.send_btn.pack(side="left")

    def _on_window_resize(self, event=None):
        if self._resize_job is not None:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(120, self._apply_responsive_layout)

    def _apply_responsive_layout(self):
        self._resize_job = None
        w = max(self.winfo_width(), self._min_width)
        h = max(self.winfo_height(), self._min_height)

        # Keep the orb centered while making the right panel intentionally slimmer.
        side_width = self._clamp(int(w * 0.24), 280, 430)
        left_width = side_width
        right_width = self._clamp(int(side_width * 0.82), 220, 350)

        available_center = w - (left_width + right_width) - 140
        if available_center < 340:
            side_width = self._clamp(int((w - 500) / 2), 240, 400)
            left_width = side_width
            right_width = self._clamp(int(side_width * 0.82), 210, 330)
            available_center = w - (left_width + right_width) - 140

        target_orb = self._clamp(
            int(min(int(h * 0.68), int(available_center * 0.95)) * ORB_SCALE),
            204,
            336,
        )

        input_width = self._clamp(int(available_center * 0.70), 320, 640)
        right_height = self._clamp(int(h - 130), 520, 760)
        self.left_panel.configure(width=left_width)
        self.right_panel.configure(width=right_width, height=right_height)
        self.entry.configure(width=input_width)

        if abs(self.orb.orb_size - target_orb) > 8:
            self.orb.resize_orb(target_orb)

    def _get_selected_date_key(self) -> str:
        return self.todo_selected_date.strftime("%Y-%m-%d")

    def _shift_calendar_month(self, step: int):
        month = self.todo_visible_month + step
        year = self.todo_visible_year
        while month < 1:
            month += 12
            year -= 1
        while month > 12:
            month -= 12
            year += 1
        self.todo_visible_year = year
        self.todo_visible_month = month
        self._rebuild_calendar_grid()

    def _on_calendar_day_click(self, button_index: int):
        if button_index < 0 or button_index >= len(self.cal_day_dates):
            return
        chosen_date = self.cal_day_dates[button_index]
        self.todo_selected_date = chosen_date
        self.todo_visible_year = chosen_date.year
        self.todo_visible_month = chosen_date.month
        self._rebuild_calendar_grid()

    def _rebuild_calendar_grid(self):
        self.cal_month_label.configure(
            text=f"{calendar.month_name[self.todo_visible_month]} {self.todo_visible_year}"
        )

        calendar_builder = calendar.Calendar(firstweekday=0)
        weeks = calendar_builder.monthdatescalendar(self.todo_visible_year, self.todo_visible_month)
        while len(weeks) < 6:
            last_week = weeks[-1]
            next_week_start = last_week[-1] + datetime.timedelta(days=1)
            weeks.append([next_week_start + datetime.timedelta(days=i) for i in range(7)])

        flat_dates = [day for week in weeks[:6] for day in week]
        self.cal_day_dates = flat_dates

        for idx, day in enumerate(flat_dates):
            btn = self.cal_day_buttons[idx]
            is_current_month = day.month == self.todo_visible_month
            is_selected = day == self.todo_selected_date
            is_today = day == datetime.date.today()

            fg_color = "#0E2140"
            hover_color = "#17406D"
            text_color = "#A8C9EA"
            border_width = 0
            border_color = BORDER

            if not is_current_month:
                fg_color = "#0A1630"
                text_color = "#4F6C8E"
            if is_today:
                fg_color = "#153A62"
                text_color = "#DDF0FF"
            if is_selected:
                fg_color = BTN_PRIMARY
                hover_color = BTN_PRIMARY_HOVER
                text_color = "#EEF7FF"
                border_width = 1
                border_color = "#6EC7FF"

            btn.configure(
                text=str(day.day),
                fg_color=fg_color,
                hover_color=hover_color,
                text_color=text_color,
                border_width=border_width,
                border_color=border_color,
                state="normal" if self._calendar_enabled else "disabled",
            )

        self._refresh_task_list()

    def _refresh_task_list(self):
        date_key = self._get_selected_date_key()
        self._todo_task_rows = get_tasks_for_date(date_key)

        self.todo_listbox.configure(state="normal")
        self.todo_listbox.delete(0, "end")

        if not self._todo_task_rows:
            self.todo_listbox.insert("end", "No tasks for selected date.")
            self.todo_listbox.configure(state="disabled")
            return

        for task in self._todo_task_rows:
            status = "DONE" if task.get("status") == "completed" else "PENDING"
            self.todo_listbox.insert(
                "end",
                f"{task['id']}. [{status}] {task['task']} ({task['added_time']})",
            )
        if not self.authenticated:
            self.todo_listbox.configure(state="disabled")

    def _set_calendar_enabled(self, enabled: bool):
        self._calendar_enabled = enabled
        state = "normal" if enabled else "disabled"
        self.cal_prev_btn.configure(state=state)
        self.cal_next_btn.configure(state=state)
        for btn in self.cal_day_buttons:
            btn.configure(state=state)
        self.todo_task_entry.configure(state=state)
        self.todo_add_btn.configure(state=state)
        self.todo_update_btn.configure(state=state)
        self.todo_listbox.configure(state=state)
        self._rebuild_calendar_grid()

    def _on_task_list_select(self, _event=None):
        if not self.authenticated:
            return
        selected = self.todo_listbox.curselection()
        if not selected:
            return
        idx = selected[0]
        if idx >= len(self._todo_task_rows):
            return
        self.todo_task_var.set(self._todo_task_rows[idx].get("task", ""))

    def _selected_task_id(self):
        selected = self.todo_listbox.curselection()
        if not selected:
            return None
        idx = selected[0]
        if idx >= len(self._todo_task_rows):
            return None
        return self._todo_task_rows[idx].get("id")

    def _on_add_task_from_calendar(self):
        if not self.authenticated:
            self._add_to_transcript("SYSTEM: Please authenticate first")
            return

        task_text = self.todo_task_var.get().strip()
        date_key = self._get_selected_date_key()
        response = add_task(task_text, date_key)
        self._add_to_transcript(f"JARVIS: {response}")
        speak(response)

        if task_text:
            self.todo_task_var.set("")
        self._refresh_task_list()

    def _on_update_selected_task(self):
        if not self.authenticated:
            self._add_to_transcript("SYSTEM: Please authenticate first")
            return

        task_id = self._selected_task_id()
        if task_id is None:
            self._add_to_transcript("JARVIS: Select a task from the calendar list to update.")
            return

        new_text = self.todo_task_var.get().strip()
        date_key = self._get_selected_date_key()
        response = update_task(str(task_id), new_text, date_key)
        self._add_to_transcript(f"JARVIS: {response}")
        speak(response)
        self._refresh_task_list()

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
        cmd = normalize_command(text).strip().lower()
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
        # ---- Network features ----
        elif cmd in {"wifi", "wifi status", "wi-fi", "wi-fi status", "wireless"}:
            response = get_wifi_status_text()
        elif cmd in {"turn on wifi", "enable wifi", "wifi on"}:
            response = toggle_wifi(True)
        elif cmd in {"turn off wifi", "disable wifi", "wifi off"}:
            response = toggle_wifi(False)
        elif cmd in {"bluetooth", "bluetooth status", "bt status"}:
            response = get_bluetooth_status_text()
        elif cmd in {"turn on bluetooth", "enable bluetooth", "bluetooth on"}:
            response = toggle_bluetooth(True)
        elif cmd in {"turn off bluetooth", "disable bluetooth", "bluetooth off"}:
            response = toggle_bluetooth(False)
        elif cmd in {"ip address", "my ip", "local ip", "ip"}:
            response = get_ip_address_text()
        elif cmd in {"public ip", "external ip", "my public ip", "wan ip"}:
            response = get_public_ip_text()
        elif cmd in {"network interfaces", "network adapters", "interfaces"}:
            response = get_network_interfaces_text()
        elif cmd in {"network usage", "data usage", "bandwidth usage", "network stats"}:
            response = get_network_usage_text()
        elif cmd in {"active connections", "connections", "network connections"}:
            response = get_active_connections_text()
        elif cmd.startswith("ping "):
            response = get_ping_text(cmd.replace("ping ", "", 1))
        elif cmd.startswith("search wikipedia "):
            response = search_wikipedia(cmd.replace("search wikipedia ", "", 1))
        elif cmd.startswith("wikipedia "):
            response = search_wikipedia(cmd.replace("wikipedia ", "", 1))
        # ---- Information features ----
        elif cmd in {"news", "latest news", "headlines", "top news"}:
            response = get_news_text()
        elif cmd in {"weather", "weather report", "temperature", "forecast"}:
            response = get_weather_text()
        elif cmd.startswith("weather in "):
            response = get_weather_text(cmd.replace("weather in ", "", 1).strip())
        elif cmd in {"stock", "stock market", "stocks", "share market", "share price", "market"}:
            response = get_stock_text()
        elif cmd in {"crypto", "cryptocurrency", "bitcoin", "bitcoin price", "crypto price", "crypto update"}:
            response = get_crypto_text()
        else:
            response = "Unknown command. Try: tell time, system info, wifi, bluetooth, news, weather, stock, crypto, wikipedia, or todo commands."

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
                self._set_calendar_enabled(True),
                self._refresh_task_list(),
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
                self._set_calendar_enabled(False),
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

    def _check_network_notifications(self):
        if self.authenticated:
            net_message = check_network_notifications(self.network_state)
            if net_message:
                self._add_to_transcript(f"JARVIS: {net_message}")
                self._speak_battery_notification(net_message)  # reuse same async-speak helper

        # Poll every 3 seconds — fast enough for instant feel, light on resources.
        self.after(3000, self._check_network_notifications)


# ─── Entry ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()
