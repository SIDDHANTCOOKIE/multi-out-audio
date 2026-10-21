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
        self.geometry("560x800")
        self.minsize(500, 700)
        self.mirror = None
        self.apps = {}
        self.devs = []
        self.state = {}  # device name -> (BooleanVar, DoubleVar), survives theme changes
        self.app_var = tk.StringVar()
        self.theme_var = tk.StringVar(value=themes.load_choice())
        saved = themes.load_settings()
        self.latency = saved.get("latency", {})  # device name -> measured seconds
        self.auto_var = tk.BooleanVar(value=True)
        self.meters = {}
        self.build_ui()
        self.refresh()
        self.poll()
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
        self.sync_btn = tk.Button(foot, text="Auto-sync", command=self.autosync, bg=t["card"], fg=t["deep"],
                                  activebackground=t["accent"], relief="flat", font=(F, 10, "bold"), padx=12, pady=5,
                                  highlightthickness=1, highlightbackground=t["accent"], cursor="hand2")
        self.sync_btn.pack(side="right", padx=8)
        tm = tk.OptionMenu(foot, self.theme_var, *themes.THEMES, command=self.change_theme)
        tm.config(bg=t["card"], fg=t["ink"], activebackground=t["accent"], activeforeground="white", relief="flat",
                  font=(F, 10), highlightthickness=1, highlightbackground=t["accent"], width=12)
        tm["menu"].config(bg=t["card"], fg=t["ink"], font=(F, 10))
        tm.pack(side="left")
        tk.Checkbutton(foot, text="auto delay", variable=self.auto_var, command=self.sync, bg=t["bg"], fg=t["ink"],
                       font=(F, 9), activebackground=t["bg"], selectcolor=t["card"]).pack(side="left", padx=8)

        self.build_devices()
        self.refresh_apps()

    def build_devices(self):
        t, F = self.t, self.t["font"]
        for w in self.list.winfo_children():
            w.destroy()
        self.meters = {}
        for _idx, name in self.devs:
            on, vol, ms = self.state.setdefault(
                name, (tk.BooleanVar(), tk.DoubleVar(value=100), tk.DoubleVar(value=0)))
            card = tk.Frame(self.list, bg=t["card"], highlightbackground=t["line"], highlightthickness=1)
            card.pack(fill="x", pady=3)
            top = tk.Frame(card, bg=t["card"])
            top.pack(fill="x", padx=8, pady=(5, 0))
            tk.Checkbutton(top, text=name, variable=on, command=self.sync, bg=t["card"], fg=t["ink"], font=(F, 10),
                           activebackground=t["card"], activeforeground=t["ink"], selectcolor=t["card"],
                           anchor="w").pack(side="left", fill="x", expand=True)
            meter = tk.Canvas(top, width=60, height=8, bg=t["trough"], highlightthickness=0)
            meter.pack(side="right", padx=4)
            bar = meter.create_rectangle(0, 0, 0, 8, fill=t["accent"], outline="")
            self.meters[name] = (meter, bar)
            for label, var, hi, unit in (("Volume", vol, 100, "%"), ("Fine-tune delay", ms, 300, "ms")):
                row = tk.Frame(card, bg=t["card"])
                row.pack(fill="x", padx=12, pady=(0, 3))
                tk.Label(row, text=label, bg=t["card"], fg=t["ink"], font=(F, 8), width=14, anchor="w").pack(side="left")
                tk.Scale(row, from_=0, to=hi, orient="horizontal", variable=var, showvalue=False,
                         command=lambda _v: self.sync(), bg=t["deep"], troughcolor=t["trough"],
                         activebackground=t["accent"], highlightthickness=0, sliderrelief="flat", sliderlength=18,
                         width=10, bd=0).pack(side="left", fill="x", expand=True)
                tk.Label(row, textvariable=var, bg=t["card"], fg=t["deep"], width=4, font=(F, 9, "bold")).pack(side="left")
                tk.Label(row, text=unit, bg=t["card"], fg=t["ink"], font=(F, 8)).pack(side="left")
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

    def auto_delays(self, names):
        """Delay (ms) that equalises saved acoustic latencies; {} if any device is uncalibrated."""
        lat = self.latency
        if not self.auto_var.get() or not names or any(n not in lat for n in names):
            return {}
        top = max(lat[n] for n in names)
        return {n: (top - lat[n]) * 1000 for n in names}

    def wanted(self):
        ticked = [(i, n) for i, n in self.devs if self.state[n][0].get()]
        auto = self.auto_delays([n for _, n in ticked])
        return {i: (int(auto.get(n, 0) + self.state[n][2].get()), self.state[n][1].get() / 100)
                for i, n in ticked}

    def poll(self):
        """Update level meters and surface playback errors."""
        m = self.mirror
        for i, n in self.devs:
            meter, bar = self.meters.get(n, (None, None))
            if meter:
                lvl = m.sinks[i].level if m and i in m.sinks else 0
                meter.coords(bar, 0, 0, min(1, lvl * 3) * 60, 8)
        if m and m.error:
            self.say.config(text=m.error)
            self.toggle()
        self.after(150, self.poll)

    def autosync(self):
        """Measure each ticked device with the mic, save, and apply."""
        from .calibrate import measure
        ticked = [(i, n) for i, n in self.devs if self.state[n][0].get()]
        if len(ticked) < 2 or self.mirror:
            self.say.config(text="Tick at least two devices (and press Stop first), then Auto-sync.")
            return
        self.sync_btn.config(state="disabled")
        self.say.config(text="Listening... keep each device near the mic. Clicks incoming!")

        def work():
            out, errs = {}, []
            for i, n in ticked:
                try:
                    lat, conf = measure(i)
                except Exception as e:  # noqa: BLE001
                    errs.append(f"{n}: {e}")
                    continue
                if lat is None or conf < 0.3:
                    errs.append(f"{n}: couldn't hear it")
                else:
                    out[n] = lat
            self.after(0, lambda: self.autosync_done(out, errs))
        import threading
        threading.Thread(target=work, daemon=True).start()

    def autosync_done(self, out, errs):
        self.sync_btn.config(state="normal")
        self.latency.update(out)
        themes.save_settings(latency=self.latency)
        if errs:
            self.say.config(text="Auto-sync problem: " + "; ".join(errs)[:200] +
                                 "\nMove the device closer to your mic and retry.")
        else:
            shown = ", ".join(f"{n.split('(')[-1].rstrip(')')} {v * 1000:.0f}ms" for n, v in out.items())
            self.say.config(text=f"Synced! Measured: {shown}.\nSaved. It's applied automatically on Start.")

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
