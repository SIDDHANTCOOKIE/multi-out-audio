"""Generate multiout/icon.png and assets/icon.ico from the Sakura mascot. Run: python tools/make_icon.py"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root))
from multiout.mascots import draw_waifu  # noqa: E402
from multiout.themes import THEMES  # noqa: E402

t = THEMES["Sakura"]
size = 512
bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
d = ImageDraw.Draw(bg)
d.rounded_rectangle((0, 0, size - 1, size - 1), radius=110, fill=t["accent"])
d.rounded_rectangle((18, 18, size - 19, size - 19), radius=96, fill=t["bg"])
face = draw_waifu(t, False, True).resize((int(170 * 2.7), int(190 * 2.7)), Image.LANCZOS)
bg.alpha_composite(face, ((size - face.width) // 2, size - face.height - 14))
(root / "assets").mkdir(exist_ok=True)
bg.save(root / "assets" / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
bg.resize((128, 128), Image.LANCZOS).save(root / "multiout" / "icon.png")
print("icons written")
