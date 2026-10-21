# Contributing

Thanks for helping! Quick start:

```powershell
git clone https://github.com/SIDDHANTCOOKIE/multi-out-audio
cd multi-out-audio
pip install -r requirements.txt
python run_gui.py
```

- `multiout/capture.py`: per-app capture (Windows process-loopback API)
- `multiout/mirror.py`: playback to several devices, delay, volume
- `multiout/calibrate.py`: acoustic latency measurement for Auto-sync
- `multiout/themes.py`, `multiout/mascots.py`: themes and the drawn mascots
- `multiout/gui.py`: the window

**New theme:** add an entry to `THEMES` in `themes.py`. **New mascot:** write a `draw_xxx(t, blink, sing)` in
`mascots.py` and register it in `DRAW`. Mascots must be original or CC0; please don't submit copyrighted characters.

Bugs and ideas: open an issue. Include your device combination, since Bluetooth behaviour varies a lot.
