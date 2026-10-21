"""Kawaii window: pick an app, tick the devices that should play it, tune per-device delay."""
import random
import tkinter as tk
from tkinter import messagebox

import psutil
import sounddevice as sd
from pycaw.pycaw import AudioUtilities

from .mirror import Mirror, output_devices

BG, CARD, PINK, DEEP, MINT, INK = "#ffe9f3", "#fff7fb", "#ff8fc0", "#e0589a", "#9de3d0", "#5a3a62"
HAIR, HAIR_D, SKIN = "#ffb3d9", "#f78fc3", "#ffe4d3"
FONT = ("Segoe UI", 10)
REFRESH_MS = 3000


def audio_apps():
    """{exe name: pid} for processes with an audio session."""
    apps = {}
    for s in AudioUtilities.GetAllSessions():
        if s.ProcessId:
            try:
                apps.setdefault(psutil.Process(s.ProcessId).name(), s.ProcessId)
            except psutil.Error:
                pass
    return apps


class Mascot(tk.Canvas):
    """Chibi headphone girl drawn from shapes; blinks, and sings while mirroring."""

    def __init__(self, parent):
        super().__init__(parent, width=170, height=190, bg=BG, highlightthickness=0)
        self.singing = False
        self.notes = []
        self.draw()
        self.after(2500, self.blink)
        self.after(60, self.animate)

    def draw(self):
        c = self
        # twin tails + back hair
        c.create_oval(8, 70, 58, 170, fill=HAIR, outline=HAIR_D, width=2)
        c.create_oval(112, 70, 162, 170, fill=HAIR, outline=HAIR_D, width=2)
        c.create_oval(30, 18, 140, 150, fill=HAIR, outline=HAIR_D, width=2)
        # shoulders / outfit
        c.create_polygon(45, 190, 60, 150, 110, 150, 125, 190, fill="#ffffff", outline=HAIR_D, width=2)
        c.create_polygon(75, 150, 95, 150, 85, 172, fill=DEEP, outline="")
        # face
        c.create_oval(40, 48, 130, 150, fill=SKIN, outline="#f2c4b0", width=2)
        # bangs
        c.create_polygon(36, 80, 44, 40, 85, 28, 128, 40, 134, 80, 118, 62, 100, 78, 85, 58, 70, 78, 52, 62,
                         fill=HAIR, outline=HAIR_D, width=2, smooth=True)
        # eyes
        self.eyes = []
        for cx in (65, 105):
            e = c.create_oval(cx - 11, 92, cx + 11, 122, fill=INK, outline="")
            c.create_oval(cx - 6, 96, cx + 2, 106, fill="white", outline="")
            c.create_oval(cx + 2, 110, cx + 7, 116, fill="#ffffff", outline="")
            self.eyes.append((e, cx))
        # blush + mouth
        c.create_oval(46, 120, 62, 130, fill="#ffb3c6", outline="")
        c.create_oval(108, 120, 124, 130, fill="#ffb3c6", outline="")
        self.mouth = c.create_arc(77, 120, 93, 134, start=200, extent=140, style="arc", outline=DEEP, width=2)
        # headphones
        c.create_arc(32, 20, 138, 130, start=0, extent=180, style="arc", outline=MINT, width=7)
        for x in (28, 128):
            c.create_oval(x, 84, x + 16, 118, fill=MINT, outline="#6cc9b3", width=2)
        # bow
        c.create_polygon(75, 30, 52, 20, 52, 42, fill=PINK, outline=DEEP, width=2)
        c.create_polygon(75, 30, 98, 20, 98, 42, fill=PINK, outline=DEEP, width=2)
        c.create_oval(68, 24, 82, 38, fill=DEEP, outline="")

    def blink(self):
        for e, cx in self.eyes:
            self.coords(e, cx - 11, 106, cx + 11, 110)
        self.after(120, self.open_eyes)

    def open_eyes(self):
        for e, cx in self.eyes:
            self.coords(e, cx - 11, 92, cx + 11, 122)
        self.after(random.randint(2000, 4500), self.blink)

    def sing(self, on):
        self.singing = on
        if on:
            self.itemconfig(self.mouth, style="chord", fill="#ff7aa8", start=0, extent=359)
            self.coords(self.mouth, 78, 122, 92, 136)
        else:
            self.itemconfig(self.mouth, style="arc", start=200, extent=140)
            self.coords(self.mouth, 77, 120, 93, 134)

    def animate(self):
        if self.singing and random.random() < 0.25:
            x = random.choice((20, 150))
            self.notes.append([self.create_text(x, 60, text=random.choice("♪♫"), fill=DEEP, font=("Segoe UI", 16, "bold")), x])
        for n in self.notes[:]:
            self.move(n[0], random.choice((-1, 0, 1)), -3)
            if self.coords(n[0])[1] < 0:
                self.delete(n[0])
                self.notes.remove(n)
        self.after(60, self.animate)


def pink_button(parent, text, cmd):
    return tk.Button(parent, text=text, command=cmd, bg=PINK, fg="white", activebackground=DEEP,
                     activeforeground="white", relief="flat", font=("Segoe UI", 11, "bold"),
                     padx=22, pady=6, cursor="hand2", bd=0)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Multi-Out Audio ♡")
        self.geometry("540x680")
        self.minsize(480, 560)
        self.configure(bg=BG)
        self.mirror = None
        self.apps = {}
        self.devs = []
        self.state = {}  # device name -> (BooleanVar, DoubleVar)

        head = tk.Frame(self, bg=BG)
        head.pack(fill="x", padx=14, pady=(10, 0))
        self.mascot = Mascot(head)
        self.mascot.pack(side="left")
        bubble = tk.Frame(head, bg=CARD, highlightbackground=PINK, highlightthickness=2)
        bubble.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=24)
        self.say = tk.Label(bubble, bg=CARD, fg=INK, font=("Segoe UI", 11), wraplength=270, justify="left",
                            padx=14, pady=12, text="Hi hi~ pick an app that's playing, then choose where it should sing! ♡")
        self.say.pack(fill="both", expand=True)

        pick = tk.Frame(self, bg=BG)
        pick.pack(fill="x", padx=18, pady=(10, 4))
        tk.Label(pick, text="✿ App", bg=BG, fg=DEEP, font=("Segoe UI", 11, "bold")).pack(side="left")
        self.app_var = tk.StringVar()
        self.app_menu = tk.OptionMenu(pick, self.app_var, "")
        self.app_menu.config(bg=CARD, fg=INK, activebackground=PINK, relief="flat", font=FONT,
                             highlightthickness=1, highlightbackground=PINK, width=26, anchor="w")
        self.app_menu.pack(side="left", padx=10, fill="x", expand=True)

        tk.Label(self, text="♪ Play on (slide to add delay so they line up)", bg=BG, fg=DEEP,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=18, pady=(8, 2))
        self.list = tk.Frame(self, bg=BG)
        self.list.pack(fill="both", expand=True, padx=18)

        foot = tk.Frame(self, bg=BG)
        foot.pack(fill="x", padx=18, pady=12)
        self.btn = pink_button(foot, "Start ♡", self.toggle)
        self.btn.pack(side="right")
        tk.Label(foot, text="new device not showing? it refreshes by itself ✧", bg=BG, fg="#b987a5",
                 font=("Segoe UI", 8)).pack(side="left")

        self.refresh()
        self.protocol("WM_DELETE_WINDOW", self.close)

    # --- data -----------------------------------------------------------------
    def refresh(self):
        if not self.mirror:  # PortAudio can only re-scan devices while no stream is open
            sd._terminate()
            sd._initialize()
            new = output_devices()
            if [n for _, n in new] != [n for _, n in self.devs]:
                self.devs = new
                self.build_devices()
            self.refresh_apps()
        self.after(REFRESH_MS, self.refresh)

    def refresh_apps(self):
        self.apps = audio_apps()
        names = sorted(self.apps)
        menu = self.app_menu["menu"]
        menu.delete(0, "end")
        for n in names or ["(nothing is playing)"]:
            menu.add_command(label=n, command=lambda v=n: self.app_var.set(v))
        if self.app_var.get() not in self.apps:
            self.app_var.set(names[0] if names else "(nothing is playing)")

    def build_devices(self):
        for w in self.list.winfo_children():
            w.destroy()
        for _idx, name in self.devs:
            on, ms = self.state.setdefault(name, (tk.BooleanVar(), tk.DoubleVar(value=0)))
            card = tk.Frame(self.list, bg=CARD, highlightbackground="#ffc6e0", highlightthickness=1)
            card.pack(fill="x", pady=4)
            tk.Checkbutton(card, text=name, variable=on, command=self.sync, bg=CARD, fg=INK, font=FONT,
                           activebackground=CARD, selectcolor="white", anchor="w").pack(fill="x", padx=8, pady=(6, 0))
            row = tk.Frame(card, bg=CARD)
            row.pack(fill="x", padx=12, pady=(0, 6))
            tk.Scale(row, from_=0, to=500, orient="horizontal", variable=ms, showvalue=False, command=lambda _v: self.sync(),
                     bg=DEEP, troughcolor="#ffd3e8", activebackground=PINK, highlightthickness=0, sliderrelief="flat",
                     sliderlength=22, width=14, bd=0, length=300).pack(side="left", fill="x", expand=True)
            tk.Label(row, textvariable=ms, bg=CARD, fg=DEEP, width=4, font=("Segoe UI", 10, "bold")).pack(side="left")
            tk.Label(row, text="ms", bg=CARD, fg="#b987a5", font=("Segoe UI", 8)).pack(side="left")
        if not self.devs:
            tk.Label(self.list, text="No output devices found...", bg=BG, fg=INK).pack(pady=20)

    def wanted(self):
        return {i: int(self.state[n][1].get()) for i, n in self.devs if self.state[n][0].get()}

    def sync(self):
        if self.mirror:
            self.mirror.set_sinks(self.wanted())

    # --- actions --------------------------------------------------------------
    def toggle(self):
        if self.mirror:
            self.mirror.stop()
            self.mirror = None
            self.btn.config(text="Start ♡")
            self.mascot.sing(False)
            self.say.config(text="Okay, resting now~ ✧")
            return
        pid = self.apps.get(self.app_var.get())
        if not pid or not self.wanted():
            self.say.config(text="Pick an app and at least one device first, okay? (｡•́︿•̀｡)")
            return
        try:
            self.mirror = Mirror(pid)
            self.mirror.set_sinks(self.wanted())
            self.mirror.start()
        except Exception as e:  # noqa: BLE001
            self.mirror = None
            messagebox.showerror("Multi-Out Audio", str(e))
            return
        self.btn.config(text="Stop ♡")
        self.mascot.sing(True)
        self.say.config(text=f"Singing {self.app_var.get()} on {len(self.wanted())} device(s)! ♪\nEcho? Slide the delay on the faster one~")

    def close(self):
        if self.mirror:
            self.mirror.stop()
        self.destroy()


def main():
    App().mainloop()
