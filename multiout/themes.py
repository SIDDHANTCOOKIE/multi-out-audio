"""Colour/mascot themes. Add your own by appending to THEMES."""
import json
import os
from pathlib import Path

CONFIG = Path(os.environ.get("APPDATA", Path.home())) / "bt-app-audio-multi" / "settings.json"
CUSTOM_IMAGE = CONFIG.parent / "mascot.png"  # drop any PNG/GIF here for the Custom theme

THEMES = {
    "Sakura": dict(mascot="waifu", bg="#ffe9f3", card="#fff7fb", accent="#ff8fc0", deep="#e0589a", ink="#5a3a62",
                   line="#ffc6e0", trough="#ffd3e8", hair="#ffb3d9", hair_d="#f78fc3", skin="#ffe4d3", gear="#9de3d0",
                   font="Segoe UI", hello="Hi hi~ pick an app that's playing, then choose where it should sing! ♡",
                   start="Start ♡", stop="Stop ♡"),
    "Midnight Idol": dict(mascot="waifu", bg="#171a2e", card="#20254a", accent="#7c6cff", deep="#36e2ff", ink="#e6e8ff",
                          line="#3a4180", trough="#2c3263", hair="#6a7bff", hair_d="#4a56d6", skin="#ffe4d3", gear="#ff5fa8",
                          font="Segoe UI", hello="Late-night session? Pick an app and I'll light up the stage ✦",
                          start="Start ✦", stop="Stop ✦"),
    "Matcha Neko": dict(mascot="cat", bg="#eaf6e4", card="#f7fff2", accent="#7cc576", deep="#3f8f4a", ink="#2f4a33",
                        line="#bfe3b5", trough="#d3efca", hair="#f4e3c1", hair_d="#d9bd88", skin="#fff3dc", gear="#ff9db8",
                        font="Segoe UI", hello="Nya~ choose an app and tick the speakers it should purr through!",
                        start="Start 🐾", stop="Stop 🐾"),
    "Cyber Bot": dict(mascot="robot", bg="#0b0f14", card="#121a22", accent="#00d4aa", deep="#ff2e88", ink="#cfeee8",
                      line="#1f3a40", trough="#16313a", hair="#2a3a48", hair_d="#00d4aa", skin="#1b2733", gear="#ff2e88",
                      font="Consolas", hello="> SELECT SOURCE APP. TICK OUTPUT NODES. PRESS START_",
                      start="> START", stop="> STOP"),
    "Ocean Breeze": dict(mascot="cat", bg="#e3f2fd", card="#f5fbff", accent="#4aa3df", deep="#1b6ca8", ink="#1d3b55",
                         line="#b6dcf5", trough="#cde8fa", hair="#cfe3f3", hair_d="#8dbbe0", skin="#ffffff", gear="#ffd36b",
                         font="Segoe UI", hello="Calm waters. Pick an app, pick your devices, and let it flow ~",
                         start="Start ≈", stop="Stop ≈"),
    "Custom": dict(mascot="custom", bg="#f3eefc", card="#ffffff", accent="#9b7fe6", deep="#6b4bc4", ink="#3b2f5a",
                   line="#d8cdf5", trough="#e4dcf8", hair="#ccc", hair_d="#999", skin="#fff", gear="#999",
                   font="Segoe UI",
                   hello=f"Your own mascot! Put a PNG or GIF at {CUSTOM_IMAGE} (or just switch themes).",
                   start="Start", stop="Stop"),
}


def load_choice():
    try:
        n = json.loads(CONFIG.read_text(encoding="utf-8")).get("theme")
        return n if n in THEMES else "Sakura"
    except (OSError, ValueError):
        return "Sakura"


def save_choice(name):
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps({"theme": name}), encoding="utf-8")
