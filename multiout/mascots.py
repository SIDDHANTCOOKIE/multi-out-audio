"""Original mascots, rendered with anti-aliasing (4x supersampling) and animated on a tk Canvas.

Every mascot is drawn from code, so there is nothing to license. Frames: eyes open/blink x mouth closed/singing.
"""
import random
import tkinter as tk

from PIL import Image, ImageDraw, ImageTk

from .themes import CUSTOM_IMAGE

W, H, S = 170, 190, 4


def E(t):
    return t.get("eye", t["ink"])


class Pen:
    """Draws in 170x190 logical units onto a 4x canvas."""

    def __init__(self):
        self.img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)

    def _s(self, pts):
        if pts and isinstance(pts[0], (tuple, list)):
            return [(x * S, y * S) for x, y in pts]
        return [v * S for v in pts]

    def oval(self, x0, y0, x1, y1, fill=None, line=None, w=0):
        self.d.ellipse(self._s((x0, y0, x1, y1)), fill=fill, outline=line, width=int(w * S))

    def rrect(self, x0, y0, x1, y1, r, fill=None, line=None, w=0):
        self.d.rounded_rectangle(self._s((x0, y0, x1, y1)), radius=r * S, fill=fill, outline=line, width=int(w * S))

    def poly(self, pts, fill=None, line=None, w=0):
        p = [tuple(self._s(pt)) for pt in pts]
        self.d.polygon(p, fill=fill)
        if line:
            self.d.line(p + [p[0]], fill=line, width=int(w * S), joint="curve")

    def arc(self, x0, y0, x1, y1, a0, a1, color, w):
        self.d.arc(self._s((x0, y0, x1, y1)), a0, a1, fill=color, width=int(w * S))

    def line(self, pts, color, w):
        self.d.line(self._s(pts), fill=color, width=int(w * S), joint="curve")

    def done(self):
        return self.img.resize((W, H), Image.LANCZOS)


def headphones(p, t, y_top=18, y_ear=84, x0=26, x1=144):
    p.arc(x0 + 2, y_top, x1 - 2, 140, 180, 360, t["gear"], 7)
    for x in (x0 - 4, x1 - 8):
        p.rrect(x, y_ear, x + 20, y_ear + 36, 8, fill=t["gear"], line=t["deep"], w=2)
        p.rrect(x + 4, y_ear + 5, x + 9, y_ear + 17, 3, fill="#ffffff90")


def eyes_anime(p, t, blink, cy=104, rx=12, ry=16, xs=(64, 106)):
    for cx in xs:
        if blink:
            p.arc(cx - rx, cy - 2, cx + rx, cy + 12, 200, 340, E(t), 3)
            continue
        p.oval(cx - rx, cy - ry, cx + rx, cy + ry, fill=E(t))
        p.oval(cx - rx + 3, cy - 2, cx + rx - 3, cy + ry - 2, fill=t["deep"])
        p.oval(cx - 7, cy - ry + 4, cx + 1, cy - ry + 13, fill="white")
        p.oval(cx + 3, cy + 3, cx + 8, cy + 8, fill="#ffffffcc")
        p.arc(cx - rx - 1, cy - ry - 3, cx + rx + 1, cy + 2, 190, 350, E(t), 3)


def draw_waifu(t, blink, sing):
    p = Pen()
    p.oval(4, 60, 58, 178, fill=t["hair"], line=t["hair_d"], w=2)
    p.oval(112, 60, 166, 178, fill=t["hair"], line=t["hair_d"], w=2)
    for x in (22, 36, 134, 148):
        p.line([(x, 90), (x - 3, 150)], t["hair_d"], 1.5)
    p.oval(24, 10, 146, 164, fill=t["hair"], line=t["hair_d"], w=2)
    p.poly([(40, 190), (52, 150), (118, 150), (130, 190)], fill="#ffffff", line=t["hair_d"], w=2)
    p.poly([(70, 150), (100, 150), (85, 172)], fill=t["deep"])
    p.poly([(85, 158), (66, 150), (66, 166)], fill=t["accent"], line=t["deep"], w=1.5)
    p.poly([(85, 158), (104, 150), (104, 166)], fill=t["accent"], line=t["deep"], w=1.5)
    p.oval(36, 42, 134, 152, fill=t["skin"], line="#f2c4b0", w=2)
    p.poly([(34, 84), (40, 38), (85, 22), (130, 38), (136, 84), (120, 60), (104, 80), (86, 54), (68, 80), (50, 60)],
           fill=t["hair"], line=t["hair_d"], w=2)
    p.line([(86, 24), (80, 8), (92, 2)], t["hair_d"], 3)
    p.poly([(36, 60), (46, 110), (50, 64)], fill=t["hair"], line=t["hair_d"], w=1.5)
    p.poly([(134, 60), (124, 110), (120, 64)], fill=t["hair"], line=t["hair_d"], w=1.5)
    eyes_anime(p, t, blink)
    p.oval(44, 120, 62, 132, fill="#ffb3c688")
    p.oval(108, 120, 126, 132, fill="#ffb3c688")
    if sing:
        p.oval(77, 122, 93, 138, fill=t["deep"])
        p.oval(80, 130, 90, 137, fill="#ff9db8")
    else:
        p.arc(76, 118, 94, 136, 20, 160, t["deep"], 2.5)
    headphones(p, t)
    p.poly([(60, 26), (40, 14), (40, 38)], fill=t["accent"], line=t["deep"], w=1.5)
    p.poly([(60, 26), (80, 14), (80, 38)], fill=t["accent"], line=t["deep"], w=1.5)
    p.oval(54, 19, 66, 33, fill=t["deep"])
    return p.done()


def draw_cat(t, blink, sing):
    p = Pen()
    p.poly([(34, 74), (36, 8), (82, 44)], fill=t["hair"], line=t["hair_d"], w=2)
    p.poly([(136, 74), (134, 8), (88, 44)], fill=t["hair"], line=t["hair_d"], w=2)
    p.poly([(44, 58), (45, 26), (68, 46)], fill="#ffb3c6")
    p.poly([(126, 58), (125, 26), (102, 46)], fill="#ffb3c6")
    p.poly([(44, 190), (58, 146), (112, 146), (126, 190)], fill=t["hair"], line=t["hair_d"], w=2)
    p.oval(26, 36, 144, 158, fill=t["skin"], line=t["hair_d"], w=2)
    for dx in (-10, 0, 10):
        p.line([(85 + dx, 40), (85 + dx, 54 - abs(dx) * 0.3)], t["hair_d"], 3)
    eyes_anime(p, t, blink, cy=100, rx=10, ry=14, xs=(60, 110))
    p.poly([(79, 114), (91, 114), (85, 122)], fill="#ff8fa8")
    if sing:
        p.oval(76, 124, 94, 142, fill=t["deep"])
        p.oval(80, 134, 90, 141, fill="#ff9db8")
    else:
        p.arc(73, 118, 86, 134, 10, 150, t["deep"], 2.5)
        p.arc(84, 118, 97, 134, 30, 170, t["deep"], 2.5)
    for dy in (-5, 5):
        p.line([(26, 124 + dy), (56, 126)], t["hair_d"], 1.8)
        p.line([(144, 124 + dy), (114, 126)], t["hair_d"], 1.8)
    p.oval(36, 118, 54, 130, fill="#ffb3c670")
    p.oval(116, 118, 134, 130, fill="#ffb3c670")
    headphones(p, t, y_top=30, y_ear=86, x0=24, x1=146)
    return p.done()


def draw_robot(t, blink, sing):
    p = Pen()
    p.line([(85, 34), (85, 12)], t["accent"], 4)
    p.oval(77, 3, 93, 19, fill=t["deep"])
    p.rrect(50, 148, 120, 190, 8, fill=t["hair"], line=t["accent"], w=3)
    p.oval(78, 160, 92, 174, fill=t["accent"])
    p.rrect(30, 32, 140, 152, 20, fill=t["skin"], line=t["accent"], w=4)
    p.rrect(42, 52, 128, 116, 14, fill="#05090d", line=t["line"], w=2)
    for cx in (66, 104):
        if blink:
            p.rrect(cx - 12, 82, cx + 12, 86, 2, fill=t["accent"])
        else:
            p.rrect(cx - 12, 68, cx + 12, 98, 7, fill=t["accent"])
            p.rrect(cx - 7, 72, cx + 1, 80, 3, fill="#ffffffaa")
    if sing:
        for i, hgt in enumerate((8, 16, 22, 16, 8)):
            x = 62 + i * 12
            p.rrect(x, 134 - hgt / 2, x + 7, 134 + hgt / 2, 3, fill=t["deep"])
    else:
        p.rrect(62, 130, 108, 138, 4, fill=t["deep"])
    for x in (22, 138):
        p.rrect(x, 70, x + 12, 114, 5, fill=t["gear"], line=t["deep"], w=2)
    for x, y in ((38, 40), (132, 40), (38, 144), (132, 144)):
        p.oval(x - 2, y - 2, x + 2, y + 2, fill=t["line"])
    return p.done()


def draw_ghost(t, blink, sing):
    p = Pen()
    body = "#fdfcff"
    p.oval(28, 20, 142, 150, fill=body, line=t["deep"], w=3)
    p.rrect(28, 80, 142, 168, 4, fill=body)
    p.line([(28, 85), (28, 168)], t["deep"], 3)
    p.line([(142, 85), (142, 168)], t["deep"], 3)
    for i in range(4):
        x0 = 28 + i * 28.5
        p.oval(x0, 154, x0 + 28.5, 184, fill=body, line=t["deep"], w=3)
    p.rrect(30, 140, 140, 172, 2, fill=body)
    p.oval(14, 100, 36, 126, fill=body, line=t["deep"], w=3)
    p.oval(134, 100, 156, 126, fill=body, line=t["deep"], w=3)
    for cx in (66, 104):
        if blink:
            p.arc(cx - 10, 84, cx + 10, 104, 200, 340, E(t), 3)
        else:
            p.oval(cx - 9, 74, cx + 9, 104, fill=E(t))
            p.oval(cx - 5, 78, cx + 1, 86, fill="white")
    p.oval(44, 104, 60, 114, fill="#ffb3c688")
    p.oval(110, 104, 126, 114, fill="#ffb3c688")
    if sing:
        p.oval(78, 112, 92, 130, fill=E(t))
    else:
        p.arc(76, 106, 94, 122, 20, 160, E(t), 2.5)
    headphones(p, t, y_top=14, y_ear=72, x0=26, x1=144)
    return p.done()


def draw_penguin(t, blink, sing):
    p = Pen()
    dark = "#2d3e50"
    p.oval(40, 20, 130, 175, fill=dark, line="#1c2836", w=2)
    p.oval(54, 70, 116, 172, fill="#ffffff")
    p.oval(30, 90, 56, 150, fill=dark, line="#1c2836", w=2)
    p.oval(114, 90, 140, 150, fill=dark, line="#1c2836", w=2)
    p.oval(52, 168, 82, 186, fill="#ffa63d")
    p.oval(88, 168, 118, 186, fill="#ffa63d")
    p.oval(50, 40, 120, 102, fill="#ffffff")
    for cx in (68, 102):
        if blink:
            p.arc(cx - 8, 58, cx + 8, 76, 200, 340, dark, 3)
        else:
            p.oval(cx - 7, 52, cx + 7, 74, fill=dark)
            p.oval(cx - 4, 55, cx + 1, 61, fill="white")
    p.oval(52, 76, 66, 86, fill="#ff9db888")
    p.oval(104, 76, 118, 86, fill="#ff9db888")
    if sing:
        p.poly([(72, 80), (98, 80), (85, 92)], fill="#ff8a1f")
        p.poly([(74, 88), (96, 88), (85, 100)], fill="#d9531a")
    else:
        p.poly([(72, 80), (98, 80), (85, 94)], fill="#ffa63d", line="#d9531a", w=1.5)
    headphones(p, t, y_top=16, y_ear=48, x0=36, x1=134)
    return p.done()


DRAW = dict(waifu=draw_waifu, cat=draw_cat, robot=draw_robot, ghost=draw_ghost, penguin=draw_penguin)


class Mascot(tk.Canvas):
    W, H = W, H

    def __init__(self, parent, t):
        super().__init__(parent, width=W, height=H, bg=t["bg"], highlightthickness=0)
        self.t = t
        self.singing = False
        self.blinking = False
        self.notes = []
        self.frames = {}
        kind = t["mascot"]
        if kind == "custom":
            self._load_custom()
        else:
            for b in (False, True):
                for s in (False, True):
                    self.frames[(b, s)] = ImageTk.PhotoImage(DRAW[kind](t, b, s))
        first = self.frames.get((False, False))
        self.item = self.create_image(W // 2, H // 2, image=first) if first else None
        self._jobs = [self.after(2500, self.blink), self.after(60, self.animate)]

    def _load_custom(self):
        try:
            im = Image.open(CUSTOM_IMAGE).convert("RGBA")
            im.thumbnail((W, H), Image.LANCZOS)
            self.frames[(False, False)] = ImageTk.PhotoImage(im)
        except OSError:
            self.create_text(W // 2, H // 2, text="your mascot\ngoes here", fill=self.t["deep"],
                             font=(self.t["font"], 12, "bold"), justify="center")

    def destroy(self):
        for j in self._jobs:
            self.after_cancel(j)
        super().destroy()

    def _show(self):
        if self.item and (self.blinking, self.singing) in self.frames:
            self.itemconfig(self.item, image=self.frames[(self.blinking, self.singing)])

    def blink(self):
        self.blinking = True
        self._show()
        self._jobs.append(self.after(130, self._open))

    def _open(self):
        self.blinking = False
        self._show()
        self._jobs.append(self.after(random.randint(2000, 4500), self.blink))

    def sing(self, on):
        self.singing = on
        self._show()

    def animate(self):
        if self.singing and random.random() < 0.25:
            x = random.choice((14, 156))
            self.notes.append(self.create_text(x, 70, text=random.choice("♪♫"), fill=self.t["deep"],
                                               font=("Segoe UI", 16, "bold")))
        for n in self.notes[:]:
            self.move(n, random.choice((-1, 0, 1)), -3)
            if self.coords(n)[1] < 0:
                self.delete(n)
                self.notes.remove(n)
        if self.singing and self.item:  # little bounce
            self.coords(self.item, W // 2, H // 2 + random.choice((-2, 0, 2)))
        elif self.item:
            self.coords(self.item, W // 2, H // 2)
        self._jobs.append(self.after(60, self.animate))
