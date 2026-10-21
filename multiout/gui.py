"""Pick an app, tick the devices that should play it, tune per-device delay."""
import tkinter as tk
from tkinter import ttk, messagebox

import psutil
from pycaw.pycaw import AudioUtilities

from .mirror import Mirror, output_devices


def audio_apps():
    """{label: pid} for processes with an audio session (first pid per exe)."""
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
        self.geometry("480x380")
        self.mirror = None
        self.apps = {}
        self.rows = {}  # device index -> (BooleanVar, DoubleVar)

        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")
        ttk.Label(top, text="App").pack(side="left")
        self.app_var = tk.StringVar()
        self.app_cb = ttk.Combobox(top, textvariable=self.app_var, state="readonly")
        self.app_cb.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(top, text="Refresh", command=self.refresh_apps).pack(side="left")

        ttk.Label(self, text="Play on these devices (delay in ms to line them up):",
                  padding=(12, 4)).pack(anchor="w")
        body = ttk.Frame(self, padding=(12, 0))
        body.pack(fill="both", expand=True)
        body.columnconfigure(1, weight=1)
        for i, (idx, name) in enumerate(output_devices()):
            on, ms = tk.BooleanVar(), tk.DoubleVar(value=0)
            ttk.Checkbutton(body, text=name, variable=on, command=self.sync).grid(row=i, column=0, sticky="w", pady=3)
            ttk.Scale(body, from_=0, to=500, variable=ms, command=lambda _v: self.sync()).grid(
                row=i, column=1, sticky="ew", padx=10)
            ttk.Label(body, textvariable=ms, width=4).grid(row=i, column=2)
            self.rows[idx] = (on, ms)

        bottom = ttk.Frame(self, padding=12)
        bottom.pack(fill="x")
        self.btn = ttk.Button(bottom, text="Start", command=self.toggle)
        self.btn.pack(side="right")
        self.status = ttk.Label(bottom, text="Choose an app that is playing audio.", foreground="#666")
        self.status.pack(side="left")
        self.refresh_apps()
        self.protocol("WM_DELETE_WINDOW", self.close)

    def refresh_apps(self):
        self.apps = audio_apps()
        self.app_cb["values"] = sorted(self.apps)
        if self.app_var.get() not in self.apps and self.apps:
            self.app_var.set(sorted(self.apps)[0])

    def wanted(self):
        return {i: int(ms.get()) for i, (on, ms) in self.rows.items() if on.get()}

    def sync(self):
        for i, (_on, ms) in self.rows.items():
            ms.set(round(ms.get()))
        if self.mirror:
            self.mirror.set_sinks(self.wanted())

    def toggle(self):
        if self.mirror:
            self.mirror.stop()
            self.mirror = None
            self.btn.config(text="Start")
            self.status.config(text="Stopped.")
            return
        pid = self.apps.get(self.app_var.get())
        if not pid or not self.wanted():
            messagebox.showinfo("Multi-Out Audio", "Pick an app and at least one device.")
            return
        try:
            self.mirror = Mirror(pid)
            self.mirror.set_sinks(self.wanted())
            self.mirror.start()
        except Exception as e:  # noqa: BLE001
            self.mirror = None
            messagebox.showerror("Multi-Out Audio", str(e))
            return
        self.btn.config(text="Stop")
        self.status.config(text=f"Mirroring {self.app_var.get()}")

    def close(self):
        if self.mirror:
            self.mirror.stop()
        self.destroy()


def main():
    App().mainloop()
