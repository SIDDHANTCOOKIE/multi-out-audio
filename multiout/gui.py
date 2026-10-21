"""Themed window: pick an app, tick the devices that should play it, tune per-device delay."""
import tkinter as tk
from tkinter import messagebox

import psutil
import sounddevice as sd
from pycaw.pycaw import AudioUtilities

from . import themes
from .mascots import Mascot
from .mirror import Mirror, output_devices

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


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Multi-Out Audio")
        self.geometry("540x700")
        self.minsize(480, 580)
        self.mirror = None
        self.apps = {}
        self.devs = []
        self.state = {}  # device name -> (BooleanVar, DoubleVar), survives theme changes
        self.app_var = tk.StringVar()
        self.theme_var = tk.StringVar(value=themes.load_choice())
        self.build_ui()
        self.refresh()
        self.protocol("WM_DELETE_WINDOW", self.close)

    # ---- layout -------------------------------------------------------------
    def build_ui(self):
        for w in self.winfo_children():
            w.destroy()
        t = self.t = themes.THEMES[self.theme_var.get()]
        F = t["font"]
        self.configure(bg=t["bg"])

        head = tk.Frame(self, bg=t["bg"])
        head.pack(fill="x", padx=14, pady=(10, 0))
        self.mascot = Mascot(head, t)
        self.mascot.pack(side="left")
        self.mascot.sing(bool(self.mirror))
        bubble = tk.Frame(head, bg=t["card"], highlightbackground=t["accent"], highlightthickness=2)
        bubble.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=24)
        self.say = tk.Label(bubble, bg=t["card"], fg=t["ink"], font=(F, 11), wraplength=270, justify="left",
                            padx=14, pady=12, text=t["hello"])
        self.say.pack(fill="both", expand=True)

        pick = tk.Frame(self, bg=t["bg"])
        pick.pack(fill="x", padx=18, pady=(10, 4))
        tk.Label(pick, text="App", bg=t["bg"], fg=t["deep"], font=(F, 11, "bold")).pack(side="left")
        self.app_menu = tk.OptionMenu(pick, self.app_var, "")
        self.app_menu.config(bg=t["card"], fg=t["ink"], activebackground=t["accent"], activeforeground="white",
                             relief="flat", font=(F, 10), highlightthickness=1, highlightbackground=t["accent"],
                             width=26, anchor="w")
        self.app_menu["menu"].config(bg=t["card"], fg=t["ink"], font=(F, 10))
        self.app_menu.pack(side="left", padx=10, fill="x", expand=True)

        tk.Label(self, text="Play on (slide to add delay so they line up)", bg=t["bg"], fg=t["deep"],
                 font=(F, 10, "bold")).pack(anchor="w", padx=18, pady=(8, 2))
        self.list = tk.Frame(self, bg=t["bg"])
        self.list.pack(fill="both", expand=True, padx=18)

        foot = tk.Frame(self, bg=t["bg"])
        foot.pack(fill="x", padx=18, pady=12)
        self.btn = tk.Button(foot, text=t["stop"] if self.mirror else t["start"], command=self.toggle, bg=t["accent"],
                             fg="white", activebackground=t["deep"], activeforeground="white", relief="flat",
                             font=(F, 11, "bold"), padx=22, pady=6, cursor="hand2", bd=0)
        self.btn.pack(side="right")
        tk.Label(foot, text="Theme", bg=t["bg"], fg=t["deep"], font=(F, 10, "bold")).pack(side="left")
        tm = tk.OptionMenu(foot, self.theme_var, *themes.THEMES, command=self.change_theme)
        tm.config(bg=t["card"], fg=t["ink"], activebackground=t["accent"], activeforeground="white", relief="flat",
                  font=(F, 10), highlightthickness=1, highlightbackground=t["accent"], width=14)
        tm["menu"].config(bg=t["card"], fg=t["ink"], font=(F, 10))
        tm.pack(side="left", padx=8)

        self.build_devices()
        self.refresh_apps()

    def build_devices(self):
        t, F = self.t, self.t["font"]
        for w in self.list.winfo_children():
            w.destroy()
        for _idx, name in self.devs:
            on, ms = self.state.setdefault(name, (tk.BooleanVar(), tk.DoubleVar(value=0)))
            card = tk.Frame(self.list, bg=t["card"], highlightbackground=t["line"], highlightthickness=1)
            card.pack(fill="x", pady=4)
            tk.Checkbutton(card, text=name, variable=on, command=self.sync, bg=t["card"], fg=t["ink"], font=(F, 10),
                           activebackground=t["card"], activeforeground=t["ink"], selectcolor=t["card"],
                           anchor="w").pack(fill="x", padx=8, pady=(6, 0))
            row = tk.Frame(card, bg=t["card"])
            row.pack(fill="x", padx=12, pady=(0, 6))
            tk.Scale(row, from_=0, to=500, orient="horizontal", variable=ms, showvalue=False,
                     command=lambda _v: self.sync(), bg=t["deep"], troughcolor=t["trough"], activebackground=t["accent"],
                     highlightthickness=0, sliderrelief="flat", sliderlength=22, width=14, bd=0,
                     length=300).pack(side="left", fill="x", expand=True)
            tk.Label(row, textvariable=ms, bg=t["card"], fg=t["deep"], width=4, font=(F, 10, "bold")).pack(side="left")
            tk.Label(row, text="ms", bg=t["card"], fg=t["ink"], font=(F, 8)).pack(side="left")
        if not self.devs:
            tk.Label(self.list, text="No output devices found...", bg=t["bg"], fg=t["ink"]).pack(pady=20)

    def change_theme(self, name):
        themes.save_choice(name)
        self.build_ui()

    # ---- data ---------------------------------------------------------------
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

    def wanted(self):
        return {i: int(self.state[n][1].get()) for i, n in self.devs if self.state[n][0].get()}

    def sync(self):
        if self.mirror:
            self.mirror.set_sinks(self.wanted())

    # ---- actions ------------------------------------------------------------
    def toggle(self):
        t = self.t
        if self.mirror:
            self.mirror.stop()
            self.mirror = None
            self.btn.config(text=t["start"])
            self.mascot.sing(False)
            self.say.config(text="Stopped. Pick something else whenever you like.")
            return
        pid = self.apps.get(self.app_var.get())
        if not pid or not self.wanted():
            self.say.config(text="Pick an app and at least one device first.")
            return
        try:
            self.mirror = Mirror(pid)
            self.mirror.set_sinks(self.wanted())
            self.mirror.start()
        except Exception as e:  # noqa: BLE001
            self.mirror = None
            messagebox.showerror("Multi-Out Audio", str(e))
            return
        self.btn.config(text=t["stop"])
        self.mascot.sing(True)
        self.say.config(text=f"Playing {self.app_var.get()} on {len(self.wanted())} device(s) ♪\n"
                             "Hear an echo? Slide the delay on the faster device.")

    def close(self):
        if self.mirror:
            self.mirror.stop()
        self.destroy()


def main():
    App().mainloop()
