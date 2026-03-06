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
from datetime import datetime

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
        self._build_ui()
        self._start_clock()

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

        self.orb = JarvisOrb(center, size=486)
        self.orb.place(relx=0.5, rely=0.5, anchor="center")

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
            placeholder_text_color="#1A4A6A"
        )
        self.entry.pack(side="left", padx=(0, 10))
        self.entry.bind("<Return>", self._on_send)
        self.entry.focus()

        ctk.CTkButton(row,
                      text="SEND",
                      font=ctk.CTkFont("Courier New", 12, "bold"),
                      fg_color="#003A60",
                      hover_color=RING_MID,
                      text_color=RING_BRIGHT,
                      border_width=1,
                      border_color=RING_MID,
                      corner_radius=4,
                      width=80,
                      command=self._on_send).pack(side="left")

    def _on_send(self, event=None):
        text = self.input_var.get().strip()
        if not text:
            return
        self.input_var.set("")
        self.orb.set_active(True)
        self.status_lbl.configure(text="● PROCESSING", text_color=TEXT_AMBER)
        threading.Thread(target=self._process, args=(text,), daemon=True).start()

    def _process(self, text):
        time.sleep(0.8 + random.random() * 0.7)
        self.after(0, lambda: (
            self.orb.set_active(False),
            self.status_lbl.configure(text="● ONLINE", text_color=TEXT_GREEN)
        ))

    def _start_clock(self):
        self.clock_lbl.configure(
            text=datetime.now().strftime("SYS  %H:%M:%S  //  %d.%m.%Y"))
        self.after(1000, self._start_clock)


# ─── Entry ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = JarvisApp()
    app.mainloop()
