"""Original vector mascots drawn on a tk Canvas. All animate: blink, and sing while mirroring."""
import random
import tkinter as tk

from .themes import CUSTOM_IMAGE


class Mascot(tk.Canvas):
    W, H = 170, 190

    def __init__(self, parent, t):
        super().__init__(parent, width=self.W, height=self.H, bg=t["bg"], highlightthickness=0)
        self.t = t
        self.eyes = []  # (id, x0, y0, x1, y1) open-eye coords
        self.mouth = None
        self.singing = False
        self.notes = []
        self.img = None
        getattr(self, "draw_" + t["mascot"])()
        self._jobs = [self.after(2500, self.blink), self.after(60, self.animate)]

    def destroy(self):
        for j in self._jobs:
            self.after_cancel(j)
        super().destroy()

    # ---- drawing ------------------------------------------------------------
    def eye(self, cx, cy, rx, ry, color=None, shine=True):
        c = self
        e = c.create_oval(cx - rx, cy - ry, cx + rx, cy + ry, fill=color or self.t["ink"], outline="")
        if shine:
            c.create_oval(cx - rx * .5, cy - ry * .7, cx + rx * .2, cy - ry * .1, fill="white", outline="")
        self.eyes.append((e, cx - rx, cy - ry, cx + rx, cy + ry))

    def headphones(self, y_top=20, y_ear=84):
        t = self.t
        self.create_arc(32, y_top, 138, 130, start=0, extent=180, style="arc", outline=t["gear"], width=7)
        for x in (28, 128):
            self.create_oval(x, y_ear, x + 16, y_ear + 34, fill=t["gear"], outline=t["deep"], width=2)

    def draw_waifu(self):
        c, t = self, self.t
        c.create_oval(8, 70, 58, 170, fill=t["hair"], outline=t["hair_d"], width=2)
        c.create_oval(112, 70, 162, 170, fill=t["hair"], outline=t["hair_d"], width=2)
        c.create_oval(30, 18, 140, 150, fill=t["hair"], outline=t["hair_d"], width=2)
        c.create_polygon(45, 190, 60, 150, 110, 150, 125, 190, fill="#ffffff", outline=t["hair_d"], width=2)
        c.create_polygon(75, 150, 95, 150, 85, 172, fill=t["deep"], outline="")
        c.create_oval(40, 48, 130, 150, fill=t["skin"], outline="#f2c4b0", width=2)
        c.create_polygon(36, 80, 44, 40, 85, 28, 128, 40, 134, 80, 118, 62, 100, 78, 85, 58, 70, 78, 52, 62,
                         fill=t["hair"], outline=t["hair_d"], width=2, smooth=True)
        for cx in (65, 105):
            self.eye(cx, 107, 11, 15)
        c.create_oval(46, 120, 62, 130, fill="#ffb3c6", outline="")
        c.create_oval(108, 120, 124, 130, fill="#ffb3c6", outline="")
        self.mouth = c.create_arc(77, 120, 93, 134, start=200, extent=140, style="arc", outline=t["deep"], width=2)
        self.mouth_closed = (77, 120, 93, 134)
        self.mouth_open = (78, 122, 92, 136)
        self.headphones()
        c.create_polygon(75, 30, 52, 20, 52, 42, fill=t["accent"], outline=t["deep"], width=2)
        c.create_polygon(75, 30, 98, 20, 98, 42, fill=t["accent"], outline=t["deep"], width=2)
        c.create_oval(68, 24, 82, 38, fill=t["deep"], outline="")

    def draw_cat(self):
        c, t = self, self.t
        c.create_polygon(36, 70, 40, 14, 80, 46, fill=t["hair"], outline=t["hair_d"], width=2)
        c.create_polygon(134, 70, 130, 14, 90, 46, fill=t["hair"], outline=t["hair_d"], width=2)
        c.create_polygon(44, 58, 46, 30, 66, 48, fill="#ffb3c6", outline="")
        c.create_polygon(126, 58, 124, 30, 104, 48, fill="#ffb3c6", outline="")
        c.create_polygon(50, 190, 62, 148, 108, 148, 120, 190, fill=t["hair"], outline=t["hair_d"], width=2)
        c.create_oval(30, 40, 140, 156, fill=t["skin"], outline=t["hair_d"], width=2)
        for cx in (62, 108):
            self.eye(cx, 100, 9, 13)
        c.create_polygon(80, 116, 90, 116, 85, 123, fill="#ff8fa8", outline="")
        for dy in (-4, 4):
            c.create_line(30, 120 + dy, 56, 122, fill=t["hair_d"], width=2)
            c.create_line(140, 120 + dy, 114, 122, fill=t["hair_d"], width=2)
        self.mouth = c.create_arc(74, 120, 96, 136, start=200, extent=140, style="arc", outline=t["deep"], width=2)
        self.mouth_closed = (74, 120, 96, 136)
        self.mouth_open = (77, 124, 93, 140)
        self.headphones(y_top=34, y_ear=84)

    def draw_robot(self):
        c, t = self, self.t
        c.create_line(85, 30, 85, 12, fill=t["accent"], width=3)
        c.create_oval(78, 4, 92, 18, fill=t["deep"], outline="")
        c.create_rectangle(52, 150, 118, 190, fill=t["hair"], outline=t["accent"], width=2)
        c.create_rectangle(34, 30, 136, 150, fill=t["skin"], outline=t["accent"], width=3)
        c.create_rectangle(44, 54, 126, 116, fill="#05090d", outline=t["line"], width=2)
        for cx in (65, 105):
            self.eye(cx, 84, 11, 12, color=t["accent"], shine=False)
        self.mouth = c.create_rectangle(65, 128, 105, 134, fill=t["deep"], outline="")
        self.mouth_closed = (65, 128, 105, 134)
        self.mouth_open = (68, 124, 102, 142)
        for x in (28, 130):
            c.create_rectangle(x, 70, x + 12, 110, fill=t["gear"], outline=t["deep"], width=2)
        c.create_line(34, 60, 136, 60, fill=t["gear"], width=0)

    def draw_custom(self):
        try:
            img = tk.PhotoImage(file=str(CUSTOM_IMAGE))
            k = max(1, -(-max(img.width(), img.height()) // self.H))
            self.img = img.subsample(k) if k > 1 else img
            self.item = self.create_image(self.W // 2, self.H // 2, image=self.img)
        except tk.TclError:
            self.create_text(self.W // 2, self.H // 2, text="♡\nyour mascot\ngoes here", fill=self.t["deep"],
                             font=(self.t["font"], 12, "bold"), justify="center")
            self.item = None

    # ---- animation ----------------------------------------------------------
    def blink(self):
        for e, x0, y0, x1, y1 in self.eyes:
            my = (y0 + y1) / 2
            self.coords(e, x0, my - 2, x1, my + 2)
        self._jobs.append(self.after(120, self.open_eyes))

    def open_eyes(self):
        for e, *box in self.eyes:
            self.coords(e, *box)
        self._jobs.append(self.after(random.randint(2000, 4500), self.blink))

    def sing(self, on):
        self.singing = on
        if self.mouth is None:
            return
        if self.type(self.mouth) == "arc":
            self.itemconfig(self.mouth, **(dict(style="chord", fill=self.t["deep"], start=0, extent=359) if on
                                           else dict(style="arc", start=200, extent=140)))
        self.coords(self.mouth, *(self.mouth_open if on else self.mouth_closed))

    def animate(self):
        if self.singing and random.random() < 0.25:
            x = random.choice((18, 152))
            self.notes.append(self.create_text(x, 60, text=random.choice("♪♫"), fill=self.t["deep"],
                                               font=("Segoe UI", 16, "bold")))
        for n in self.notes[:]:
            self.move(n, random.choice((-1, 0, 1)), -3)
            if self.coords(n)[1] < 0:
                self.delete(n)
                self.notes.remove(n)
        if self.singing and getattr(self, "item", None):  # bounce custom image
            self.coords(self.item, self.W // 2, self.H // 2 + random.choice((-3, 0, 3)))
        self._jobs.append(self.after(60, self.animate))
