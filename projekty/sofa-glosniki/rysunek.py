#!/usr/bin/env python3
"""Rysunek wymiarowy zabudowy (widok z przodu, przekrój przez wnękę głośnika, rzut z góry)
oraz opisy na renderze przekroju.

  python3 projekty/sofa-glosniki/rysunek.py
Wyniki: out/rysunek_wymiarowy.png, out/przekroj_glosniki_opis.jpg (gdy jest render przekroju i punkty.json).
"""
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

TU = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TU)
import wymiary as W  # noqa: E402

OUT = os.path.join(TU, "out")
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

PAPIER = (250, 248, 243)
TUSZ = (38, 40, 44)
SZARY = (150, 150, 150)
JASNY = (226, 222, 214)
AKCENT = (214, 106, 34)          # głośniki i wiązka dźwięku
WNEKA = (252, 228, 205)
SOFA = (205, 210, 214)


def f(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def cm(v):
    """Wymiar w centymetrach do opisu (bez zbędnych zer)."""
    c = round(v * 100, 1)
    return f"{c:g}"


class Rys:
    """Rzutnia: metry → piksele (oś pozioma w prawo, pionowa w górę)."""

    def __init__(self, d, ox, oy, s):
        self.d, self.ox, self.oy, self.s = d, ox, oy, s

    def p(self, x, z):
        return (self.ox + x * self.s, self.oy - z * self.s)

    def rect(self, x0, z0, x1, z1, fill=None, outline=TUSZ, w=3):
        (a, b), (c, e) = self.p(x0, z1), self.p(x1, z0)
        self.d.rectangle((min(a, c), min(b, e), max(a, c), max(b, e)), fill=fill, outline=outline, width=w)

    def line(self, pts, fill=TUSZ, w=3, dash=None):
        P = [self.p(*q) for q in pts]
        if not dash:
            self.d.line(P, fill=fill, width=w)
            return
        for (ax, ay), (bx, by) in zip(P, P[1:]):
            L = math.hypot(bx - ax, by - ay)
            n = max(1, int(L / dash))
            for i in range(0, n, 2):
                t0, t1 = i / n, min(1.0, (i + 1) / n)
                self.d.line((ax + (bx - ax) * t0, ay + (by - ay) * t0, ax + (bx - ax) * t1, ay + (by - ay) * t1),
                            fill=fill, width=w)

    def poly(self, pts, fill=None, outline=TUSZ, w=3):
        P = [self.p(*q) for q in pts]
        self.d.polygon(P, fill=fill, outline=outline, width=w)

    def text(self, x, z, t, size=26, fill=TUSZ, anchor="mm", bold=False):
        self.d.text(self.p(x, z), t, font=f(size, bold), fill=fill, anchor=anchor)

    def wymiar_poziomy(self, x0, x1, z, txt=None, size=24, tick=10):
        """Linia wymiarowa z kreskami ukośnymi, opis nad linią."""
        (a, y), (b, _) = self.p(x0, z), self.p(x1, z)
        self.d.line((a, y, b, y), fill=TUSZ, width=2)
        for x in (a, b):
            self.d.line((x - tick, y + tick, x + tick, y - tick), fill=TUSZ, width=3)
            self.d.line((x, y - 16, x, y + 16), fill=SZARY, width=1)
        self.d.text(((a + b) / 2, y - 6), txt or cm(x1 - x0), font=f(size), fill=TUSZ, anchor="mb")

    def wymiar_pionowy(self, z0, z1, x, txt=None, size=24, tick=10, strona=-1):
        (xx, a), (_, b) = self.p(x, z0), self.p(x, z1)
        self.d.line((xx, a, xx, b), fill=TUSZ, width=2)
        for y in (a, b):
            self.d.line((xx - tick, y + tick, xx + tick, y - tick), fill=TUSZ, width=3)
            self.d.line((xx - 16, y, xx + 16, y), fill=SZARY, width=1)
        t = txt or cm(z1 - z0)
        im = Image.new("RGBA", (int(f(size).getlength(t)) + 8, size + 10), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((4, 2), t, font=f(size), fill=TUSZ)
        im = im.rotate(90, expand=True)
        cx = xx + strona * (im.width / 2 + 6)
        self.d._image.paste(im, (int(cx - im.width / 2), int((a + b) / 2 - im.height / 2)), im)


def kreskowanie(d, box, krok=14, fill=SZARY):
    x0, y0, x1, y1 = box
    for k in range(int(x0 - (y1 - y0)), int(x1), krok):
        a = (max(x0, k), y1 - (max(x0, k) - k))
        b = (min(x1, k + (y1 - y0)), y1 - (min(x1, k + (y1 - y0)) - k))
        if a[0] <= b[0]:
            d.line((a, b), fill=fill, width=1)


def glosnik_obrys(x, z, kat, w, h):
    """Prostokąt głośnika w przekroju (oś y–z): środek (x, z), front pochylony o kat w dół, w – głębokość."""
    t = math.radians(kat)
    fwd = (math.cos(t), -math.sin(t))          # oś głośnika: w głąb pokoju i w dół
    up = (math.sin(t), math.cos(t))
    pts = []
    for a, b in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        pts.append((x + fwd[0] * a + up[0] * b, z + fwd[1] * a + up[1] * b))
    return pts, fwd, up


def widok_z_przodu(d, ox, oy, s):
    r = Rys(d, ox, oy, s)
    H = W.SUFIT
    d.text(r.p(-W.X_ZEW, H + 0.36), "WIDOK Z PRZODU", font=f(34, True), fill=TUSZ, anchor="ls")
    r.line([(-W.X_ZEW - 0.35, 0), (W.X_ZEW + 0.35, 0)], w=4)
    r.line([(-W.X_ZEW - 0.35, H), (W.X_ZEW + 0.35, H)], w=4)
    # sofa (sylwetka)
    x0, x1 = -W.SOFA_W / 2, W.SOFA_W / 2
    r.poly([(x0, 0.03), (x1, 0.03), (x1, 0.62), (x1 - 0.17, 0.62), (x1 - 0.17, W.OPARCIE_Z), (x0 + 0.17, W.OPARCIE_Z),
            (x0 + 0.17, 0.62), (x0, 0.62)], fill=SOFA, outline=SZARY, w=2)
    r.line([(x0 + 0.17, W.SIEDZISKO_Z), (x1 - 0.17, W.SIEDZISKO_Z)], fill=SZARY, w=2)
    r.text(0, 0.24, "sofa narożna prawostronna 280 cm", 22, fill=(90, 96, 104))
    # regały
    for a, b in ((-W.X_ZEW, -W.X_REG), (W.X_REG, W.X_ZEW)):
        r.rect(a, 0, b, H, fill=(255, 255, 255))
        r.rect(a, 0, b, W.COKOL, fill=JASNY, w=2)
        r.rect(a + W.PLYTA, W.COKOL, b - W.PLYTA, W.SZAFKA_Z, fill=(240, 238, 232), w=2)
        for z in list(W.POLKI) + [W.SZAFKA_Z, W.MOST_Z]:
            r.rect(a + W.PLYTA, z, b - W.PLYTA, z + 0.025, fill=(205, 170, 120), w=1)
        r.line([(a + W.PLYTA, W.POLKA_GORNA), (b - W.PLYTA, W.POLKA_GORNA)], fill=SZARY, w=2, dash=10)
        r.text((a + b) / 2, (W.SZAFKA_Z + W.COKOL) / 2, "szafka", 20, fill=(110, 110, 110))
        r.text((a + b) / 2, (W.SZAFKA_Z + W.MOST_Z) / 2, "półki", 20, fill=(110, 110, 110))
        r.text((a + b) / 2, (W.MOST_Z + H) / 2 + 0.06, "pawlacz", 20, fill=(110, 110, 110))
        r.text((a + b) / 2, (W.MOST_Z + H) / 2 - 0.08, "lub półka", 18, fill=SZARY)
    # pawlacz nad sofą z wnękami
    r.rect(-W.X_REG, W.MOST_Z, W.X_REG, H, fill=(255, 255, 255))
    for sgn in (-1, 1):
        a, b = sorted((sgn * W.X_WNEKA, sgn * W.X_REG))
        r.rect(a, W.MOST_Z, b, H, fill=WNEKA, outline=AKCENT, w=3)
        gw, gh = W.GLOSNIK[0], W.GLOSNIK[1] * math.cos(math.radians(W.POCHYLENIE)) + W.GLOSNIK[2] * math.sin(
            math.radians(W.POCHYLENIE))
        r.rect(sgn * W.G_X - gw / 2, W.G_Z - gh / 2, sgn * W.G_X + gw / 2, W.G_Z + gh / 2, fill=AKCENT, outline=TUSZ,
               w=2)
        r.text(sgn * W.G_X, W.G_Z + gh / 2 + 0.1, "głośnik " + ("L" if sgn < 0 else "P"), 22, bold=True, fill=AKCENT)
    r.text(0, (W.MOST_Z + H) / 2, "pawlacz nad sofą (fronty / półka otwarta)", 22, fill=(90, 90, 90))
    r.line([(-W.X_REG + 0.03, W.MOST_Z - 0.015), (W.X_REG - 0.03, W.MOST_Z - 0.015)], fill=(240, 180, 60), w=5)
    r.text(0, W.MOST_Z - 0.08, "LED 3000 K pod pawlaczem, przy ścianie", 20, fill=(170, 120, 30))
    # wymiary poziome
    zt = H + 0.14
    xs = [-W.X_ZEW, -W.X_REG, -W.X_WNEKA, W.X_WNEKA, W.X_REG, W.X_ZEW]
    for a, b in zip(xs, xs[1:]):
        r.wymiar_poziomy(a, b, zt)
    r.wymiar_poziomy(-W.X_ZEW, W.X_ZEW, H + 0.27)
    r.wymiar_poziomy(-W.SOFA_W / 2, W.SOFA_W / 2, -0.12, txt=f"sofa {cm(W.SOFA_W)}")
    r.wymiar_poziomy(-W.X_REG, -W.SOFA_W / 2, -0.12, txt=cm(W.SZCZELINA), size=20)
    # wymiary pionowe (lewa strona: regał, prawa: sofa i pawlacz)
    zs = [0, W.COKOL, W.SZAFKA_Z, W.POLKI[0], W.POLKI[1], W.MOST_Z, W.SUFIT]
    for a, b in zip(zs, zs[1:]):
        r.wymiar_pionowy(a, b, -W.X_ZEW - 0.14, size=20)
    r.wymiar_pionowy(0, W.SUFIT, -W.X_ZEW - 0.32, size=22)
    r.wymiar_pionowy(0, W.MOST_Z, W.X_ZEW + 0.16, txt=f"spód pawlacza {cm(W.MOST_Z)}", size=20, strona=1)
    r.wymiar_pionowy(W.MOST_Z, W.SUFIT, W.X_ZEW + 0.16, size=20, strona=1)
    r.wymiar_pionowy(0, W.OPARCIE_Z, W.SOFA_W / 2 - 0.3, txt=cm(W.OPARCIE_Z), size=20, strona=1)
    r.wymiar_pionowy(W.OPARCIE_Z, W.MOST_Z, W.SOFA_W / 2 - 0.3, txt=f"{cm(W.MOST_Z - W.OPARCIE_Z)} nad oparciem",
                     size=20, strona=1)


def przekroj(d, ox, oy, s):
    """Przekrój przez wnękę głośnika: ściana po lewej, pokój w prawo."""
    r = Rys(d, ox, oy, s)
    H = W.SUFIT
    t = math.radians(W.POCHYLENIE)
    d.text(r.p(-0.2, H + 0.36), "PRZEKRÓJ PRZEZ WNĘKĘ GŁOŚNIKA", font=f(34, True), fill=TUSZ, anchor="ls")
    a, b = r.p(-0.18, H), r.p(0, 0)
    d.rectangle((a[0], a[1], b[0], b[1]), fill=(235, 233, 228), outline=TUSZ, width=3)
    kreskowanie(d, (a[0], a[1], b[0], b[1]))
    r.line([(-0.18, 0), (2.0, 0)], w=4)
    r.line([(-0.18, H), (2.0, H)], w=4)
    # sofa w przekroju
    y0, y1 = W.SOFA_OD_SCIANY, W.SOFA_OD_SCIANY + W.SOFA_D
    r.poly([(y0, 0.03), (y1, 0.03), (y1, W.SIEDZISKO_Z), (y0 + 0.22, W.SIEDZISKO_Z), (y0 + 0.2, W.OPARCIE_Z),
            (y0, W.OPARCIE_Z)], fill=SOFA, outline=SZARY, w=2)
    # siedzący: głowa i tułów
    hx, hz = W.UCHO_Y, W.UCHO_Z
    r.line([(hx - 0.2, W.SIEDZISKO_Z + 0.03), (hx - 0.06, hz - 0.14)], fill=(120, 126, 134), w=18)
    r.line([(hx - 0.2, W.SIEDZISKO_Z + 0.03), (hx + 0.25, W.SIEDZISKO_Z + 0.04)], fill=(120, 126, 134), w=18)
    (cx, cz), rr = r.p(hx, hz + 0.02), 0.1 * s
    d.ellipse((cx - rr, cz - rr * 1.15, cx + rr, cz + rr * 1.15), fill=(255, 255, 255), outline=(120, 126, 134), width=3)
    (ex, ez) = r.p(hx + 0.01, hz)
    d.ellipse((ex - 7, ez - 7, ex + 7, ez + 7), fill=AKCENT)
    # pawlacz: wnęka, wata, dno i front
    r.rect(0, W.MOST_Z, W.GL, H, fill=WNEKA, outline=TUSZ, w=3)
    r.rect(0, W.MOST_Z, 0.012, H, fill=JASNY, w=1)
    r.rect(0.012, W.MOST_Z + W.PLYTA + 0.02, 0.042, H - W.PLYTA, fill=(232, 210, 150), outline=SZARY, w=1)
    r.rect(0.012, H - W.PLYTA - 0.03, W.GL - W.FRONT - 0.04, H - W.PLYTA, fill=(232, 210, 150), outline=SZARY, w=1)
    r.rect(0, H - W.PLYTA, W.GL, H, fill=JASNY, w=2)
    r.rect(W.GL - W.FRONT, W.MOST_Z, W.GL, H, fill=None, outline=AKCENT, w=4)
    r.rect(0.012, W.MOST_Z, W.GL - W.FRONT, W.MOST_Z + W.PLYTA, fill=None, outline=AKCENT, w=4)
    # głośnik i uchwyt
    pts, fwd, up = glosnik_obrys(W.G_Y, W.G_Z, W.POCHYLENIE, W.GLOSNIK[2], W.GLOSNIK[1])
    r.poly(pts, fill=(60, 60, 64), outline=TUSZ, w=2)
    tyl = (W.G_Y - fwd[0] * W.GLOSNIK[2] / 2, W.G_Z - fwd[1] * W.GLOSNIK[2] / 2)
    r.line([(0.045, tyl[1]), tyl], fill=(70, 70, 74), w=7)
    r.rect(0.042, tyl[1] - 0.06, 0.05, tyl[1] + 0.06, fill=(70, 70, 74), w=1)
    # oś i wiązka
    front = (W.G_Y + fwd[0] * W.GLOSNIK[2] / 2, W.G_Z + fwd[1] * W.GLOSNIK[2] / 2)
    L = (front[1] - W.CEL_Z) / math.sin(t)
    for da, wd in ((0.0, 4), (-20.0, 2), (20.0, 2)):
        tt = t + math.radians(da)
        k = (front[1] - W.CEL_Z) / math.sin(tt) if da else L
        r.line([front, (front[0] + math.cos(tt) * k, front[1] - math.sin(tt) * k)], fill=AKCENT, w=wd,
               dash=None if da == 0 else 14)
    cel = (front[0] + fwd[0] * L, front[1] + fwd[1] * L)
    (px, pz) = r.p(*cel)
    d.ellipse((px - 9, pz - 9, px + 9, pz + 9), outline=AKCENT, width=4)
    # kąt pochylenia: łuk od poziomu do osi
    (fx, fz) = r.p(*front)
    R_ = 120
    d.line((fx, fz, fx + R_ + 30, fz), fill=SZARY, width=2)
    d.arc((fx - R_, fz - R_, fx + R_, fz + R_), start=0, end=W.POCHYLENIE, fill=AKCENT, width=3)
    d.text((fx + (R_ + 48) * math.cos(math.radians(28)), fz + (R_ + 48) * math.sin(math.radians(28))),
           f"{W.POCHYLENIE:.0f}°", font=f(32, True), fill=AKCENT, anchor="mm")
    # wymiary
    r.wymiar_poziomy(0, W.GL, H + 0.12)
    r.wymiar_poziomy(0, W.G_Y, W.MOST_Z - 0.16, size=20)
    r.wymiar_poziomy(0, W.CEL_Y, 0.95, txt=f"cel osi {cm(W.CEL_Y)}", size=20)
    r.wymiar_poziomy(0, W.SOFA_OD_SCIANY + W.SOFA_D, -0.12, txt=f"sofa {cm(W.SOFA_D)} + {cm(W.SOFA_OD_SCIANY)}",
                     size=20)
    r.wymiar_pionowy(0, W.MOST_Z, 1.36, size=22, strona=1)
    r.wymiar_pionowy(W.MOST_Z, H, 1.36, size=22, strona=1)
    r.wymiar_pionowy(0, W.G_Z, 1.6, txt=f"środek głośnika {cm(W.G_Z)}", size=20, strona=1)
    r.wymiar_pionowy(0, W.UCHO_Z, 1.15, txt=cm(W.UCHO_Z), size=20, strona=1)
    r.wymiar_pionowy(W.UCHO_Z, W.G_Z, 1.86, txt=f"{cm(W.NAD_USZAMI)} nad uszami", size=20, strona=1)
    # oznaczenia elementów (numery) i legenda pod przekrojem
    znaczniki = [
        ((0.22, H - W.PLYTA - 0.015), "wata / pianka akustyczna 3 cm na plecach i pod wieńcem"),
        ((0.06, tyl[1] + 0.05), "uchwyt uchylny przykręcony do pleców wnęki"),
        ((W.GL - W.FRONT / 2, W.MOST_Z + 0.5), "front wnęki: maskownica przepuszczająca dźwięk"),
        ((W.GL * 0.55, W.MOST_Z + W.PLYTA / 2), "dno wnęki: maskownica, zdejmowana na magnesach"),
        ((W.UCHO_Y + 0.01, W.UCHO_Z), f"uszy siedzącego (ok. {cm(W.UCHO_Z)} cm nad podłogą)"),
        (cel, f"cel osi głośnika: {cm(W.CEL_Y)} cm od ściany, lekko przed głową"),
    ]
    off = [(0.3, 0.13), (0.13, 0.16), (0.14, 0.0), (0.12, -0.12), (-0.16, 0.14), (0.12, -0.12)]
    for i, ((x, z), _), (dx, dz) in zip(range(len(znaczniki)), znaczniki, off):
        (ax, az), (bx, bz) = r.p(x, z), r.p(x + dx, z + dz)
        d.line((ax, az, bx, bz), fill=TUSZ, width=2)
        d.ellipse((bx - 17, bz - 17, bx + 17, bz + 17), fill=(255, 255, 255), outline=TUSZ, width=2)
        d.text((bx, bz), str(i + 1), font=f(20, True), fill=TUSZ, anchor="mm")
    lx, ly = r.p(-0.18, -0.32)
    for i, (_, txt) in enumerate(znaczniki):
        y = ly + i * 36
        d.ellipse((lx, y - 15, lx + 30, y + 15), fill=(255, 255, 255), outline=TUSZ, width=2)
        d.text((lx + 15, y), str(i + 1), font=f(18, True), fill=TUSZ, anchor="mm")
        d.text((lx + 44, y), txt, font=f(22), fill=TUSZ, anchor="lm")


def rzut(d, ox, oy, s):
    """Rzut z góry: ściana u góry, pokój w dół rysunku."""
    def P(x, y):
        return (ox + x * s, oy + y * s)
    d.text(P(-W.X_ZEW, -0.42), "RZUT Z GÓRY", font=f(34, True), fill=TUSZ, anchor="ls")
    a, b = P(-W.X_ZEW - 0.35, -0.15), P(W.X_ZEW + 0.35, 0)
    d.rectangle((a, b), fill=(235, 233, 228), outline=TUSZ, width=3)
    kreskowanie(d, (a[0], a[1], b[0], b[1]))
    for x0, x1 in ((-W.X_ZEW, -W.X_REG), (W.X_REG, W.X_ZEW)):
        d.rectangle((P(x0, 0), P(x1, W.GL)), fill=(255, 255, 255), outline=TUSZ, width=3)
        d.text(P((x0 + x1) / 2, W.GL / 2), "regał", font=f(20), fill=TUSZ, anchor="mm")
    # sofa L
    x0, x1 = -W.SOFA_W / 2, W.SOFA_W / 2
    y0, y1, ys = W.SOFA_OD_SCIANY, W.SOFA_OD_SCIANY + W.SOFA_D, W.SZEZL_D
    xs = x1 - W.SZEZL_W
    d.polygon([P(x0, y0), P(x1, y0), P(x1, ys), P(xs, ys), P(xs, y1), P(x0, y1)], fill=SOFA, outline=SZARY, width=3)
    d.text(P(-0.5, y1 - 0.12), "sofa narożna prawostronna", font=f(22), fill=(90, 96, 104), anchor="mm")
    # pawlacz nad sofą – linia przerywana
    pa, pb = P(-W.X_REG, 0), P(W.X_REG, W.GL)
    for x in range(int(pa[0]), int(pb[0]), 24):
        d.line((x, pb[1], min(x + 12, pb[0]), pb[1]), fill=TUSZ, width=3)
    d.text(P(0, W.GL / 2), "pawlacz nad sofą (spód 190 cm)", font=f(20), fill=TUSZ, anchor="mm")
    # głowy siedzących
    for hx, hy in ((-0.9, W.UCHO_Y), (-0.15, W.UCHO_Y), (0.88, W.UCHO_Y + 0.1)):
        (cx, cy) = P(hx, hy)
        d.ellipse((cx - 22, cy - 26, cx + 22, cy + 26), fill=(255, 255, 255), outline=(120, 126, 134), width=3)
    # głośniki z kierunkiem osi i zasięgiem (±35°)
    for sgn in (-1, 1):
        th = math.radians(-sgn * W.ZBIEZNOSC)        # oś: w głąb pokoju, skręcona do środka sofy
        fw, rt = (math.sin(th), math.cos(th)), (math.cos(th), -math.sin(th))
        gw = W.GLOSNIK[0]
        gd = W.GLOSNIK[2] * math.cos(math.radians(W.POCHYLENIE)) + W.GLOSNIK[1] * math.sin(math.radians(W.POCHYLENIE))
        c = P(sgn * W.G_X, W.G_Y)
        d.polygon([(c[0] + (a_ * rt[0] + b_ * fw[0]) * s, c[1] + (a_ * rt[1] + b_ * fw[1]) * s)
                   for a_, b_ in ((-gw / 2, -gd / 2), (gw / 2, -gd / 2), (gw / 2, gd / 2), (-gw / 2, gd / 2))],
                  fill=AKCENT, outline=TUSZ, width=2)
        L = W.CEL_Y - W.G_Y + 0.2
        for da, wd in ((0, 4), (-35, 2), (35, 2)):
            ang = th + math.radians(da)
            d.line((c[0], c[1], c[0] + math.sin(ang) * L * s, c[1] + math.cos(ang) * L * s), fill=AKCENT, width=wd)
    # wymiary
    def wym(x0_, x1_, y, txt):
        (a_, yy), (b_, _) = P(x0_, y), P(x1_, y)
        d.line((a_, yy, b_, yy), fill=TUSZ, width=2)
        for x in (a_, b_):
            d.line((x - 10, yy + 10, x + 10, yy - 10), fill=TUSZ, width=3)
        d.text(((a_ + b_) / 2, yy - 6), txt, font=f(22), fill=TUSZ, anchor="mb")
    wym(xs, x1, ys + 0.18, cm(W.SZEZL_W))
    (xa, ya), (_, yb) = P(x0 - 0.2, y0), P(x0 - 0.2, y1)
    d.line((xa, ya, xa, yb), fill=TUSZ, width=2)
    for y in (ya, yb):
        d.line((xa - 10, y + 10, xa + 10, y - 10), fill=TUSZ, width=3)
    d.text((xa - 12, (ya + yb) / 2), cm(W.SOFA_D), font=f(22), fill=TUSZ, anchor="rm")
    wym(-W.X_ZEW, W.X_ZEW, ys + 0.38, f"cała zabudowa {cm(2 * W.X_ZEW)}")
    (xa, ya), (_, yb) = P(x1 + 0.85, 0), P(x1 + 0.85, ys)
    d.line((xa, ya, xa, yb), fill=TUSZ, width=2)
    for y in (ya, yb):
        d.line((xa - 10, y + 10, xa + 10, y - 10), fill=TUSZ, width=3)
    d.text((xa + 10, (ya + yb) / 2), f"{cm(W.SZEZL_D)}", font=f(22), fill=TUSZ, anchor="lm")
    d.text(P(W.G_X + 0.45, W.G_Y + 0.25), f"skręt {W.ZBIEZNOSC:.0f}° do środka", font=f(20), fill=AKCENT,
           anchor="lm")


UWAGI = [
    ("Głośniki", "małe monitory półkowe do ok. 18 × 28 × 20 cm (szer. × wys. × gł.), obudowa zamknięta "
                 "albo z otworem bas-refleks z przodu (z tyłu wnęki nie ma miejsca)."),
    ("Mocowanie", f"uchwyt uchylny na plecach wnęki, pochylenie ok. {W.POCHYLENIE:.0f}° w dół, skręt "
                  f"{W.ZBIEZNOSC:.0f}° do środka sofy; podkładki gumowe, żeby korpus nie drgał."),
    ("Wnęka", f"{cm(W.WNEKA_W)} × {cm(W.SUFIT - W.MOST_Z)} × {cm(W.GL)} cm, plecy i góra wyłożone wełną "
              "lub pianką akustyczną 3 cm."),
    ("Maskownica", "front i dno wnęki przepuszczają dźwięk: płyta perforowana, otwory 3 mm co 5 mm, od środka "
                   "biała tkanina akustyczna (A); lamele z czarną tkaniną (B); rama z tkaniną akustyczną (C). "
                   "Dno na magnesach – dostęp do głośnika."),
    ("Kabel", "kanał w boku regału do cokołu, dalej pod podłogą albo w listwie do amplitunera."),
    ("Wysokość", f"głośnik {cm(W.NAD_USZAMI)} cm nad uszami (zwykle zaleca się 60–90 cm); przy chęci "
                 "obniżenia: spód pawlacza 180 cm."),
    ("Kalibracja", "po montażu automatyczna kalibracja amplitunera (odległości i poziomy głośników)."),
]


def uwagi(d, x, y, w):
    d.text((x, y), "UWAGI DLA STOLARZA I MONTAŻU", font=f(30, True), fill=TUSZ, anchor="ls")
    y += 26
    for k, txt in UWAGI:
        words = txt.split()
        line, lines = "", []
        for wd in words:
            t = (line + " " + wd).strip()
            if f(22).getlength(k + ": " + t if not lines else t) > w:
                lines.append(line)
                line = wd
            else:
                line = t
        lines.append(line)
        d.text((x, y), k + ":", font=f(22, True), fill=AKCENT, anchor="lt")
        kw = f(22, True).getlength(k + ": ")
        for i, ln in enumerate(lines):
            d.text((x + (kw if i == 0 else 0), y), ln, font=f(22), fill=TUSZ, anchor="lt")
            y += 32
        y += 10


def rysunek():
    im = Image.new("RGB", (3300, 2350), PAPIER)
    d = ImageDraw.Draw(im)
    d.text((110, 110), "Zabudowa wokół sofy z ukrytymi głośnikami tylnymi", font=f(52, True), fill=TUSZ, anchor="ls")
    d.text((110, 160), "Regały po bokach sofy, pawlacz nad sofą, głośniki we wnękach na końcach pawlacza "
                       "skierowane w dół na siedzących. Wymiary w cm.", font=f(26), fill=(90, 90, 90), anchor="ls")
    widok_z_przodu(d, 900, 1180, 300)
    przekroj(d, 2160, 1180, 300)
    rzut(d, 900, 1580, 300)
    uwagi(d, 1950, 1560, 1250)
    d.rectangle((40, 40, im.width - 40, im.height - 40), outline=TUSZ, width=3)
    fn = os.path.join(OUT, "rysunek_wymiarowy.png")
    im.save(fn, optimize=True)
    return fn


# ------------------------------------------------------------------ opisy na renderze przekroju
OPISY = [
    ("glosnik_P", "Głośnik tylny prawy", (0.38, 0.06)),
    ("wata", "Wełna / pianka akustyczna 3 cm", (0.70, 0.13)),
    ("uchwyt_P", f"Uchwyt uchylny, pochylenie {W.POCHYLENIE:.0f}°", (0.70, 0.22)),
    ("dno_wneki", "Maskownica zdjęta (front i dno wnęki)", (0.645, 0.45)),
    ("led", "LED 3000 K podświetla ścianę nad sofą", (0.14, 0.38)),
    ("wiazka_P", "Główna wiązka dźwięku na głowy siedzących", (0.58, 0.68)),
    ("wiazka_L", "Wiązka lewego głośnika (druga wnęka)", (0.02, 0.62)),
]


def opisz_przekroj():
    src = os.path.join(OUT, "przekroj_glosniki.jpg")
    pj = os.path.join(OUT, "punkty.json")
    if not (os.path.exists(src) and os.path.exists(pj)):
        return None
    P = json.load(open(pj))
    im = Image.open(src).convert("RGB")
    k = im.width / P["res"][0]
    d = ImageDraw.Draw(im)
    fs = max(18, int(im.width / 62))
    for key, txt, (lx, ly) in OPISY:
        if key not in P:
            continue
        px, py = P[key][0] * k, P[key][1] * k
        tx, ty = lx * im.width, ly * im.height
        tw = f(fs, True).getlength(txt)
        box = (tx - 12, ty - fs * 0.75, tx + tw + 12, ty + fs * 0.75)
        kx = min(max(px, box[0]), box[2])
        ky = box[3] if py > box[3] else box[1] if py < box[1] else py
        d.line((px, py, kx, ky), fill=(255, 255, 255), width=5)
        d.line((px, py, kx, ky), fill=AKCENT, width=3)
        d.ellipse((px - 8, py - 8, px + 8, py + 8), fill=AKCENT, outline=(255, 255, 255), width=3)
        d.rounded_rectangle(box, radius=8, fill=(255, 255, 255), outline=AKCENT, width=2)
        d.text((tx, ty), txt, font=f(fs, True), fill=TUSZ, anchor="lm")
    fn = os.path.join(OUT, "przekroj_glosniki_opis.jpg")
    im.save(fn, quality=92)
    return fn


def zestawienie():
    """Trzy warianty obok siebie z podpisami (do szybkiego porównania)."""
    pliki = [("wariant_A_biel_dab.jpg", "A · Biel i dąb", "głośniki za białą płytą perforowaną"),
             ("wariant_B_lamele.jpg", "B · Lamele dębowe", "głośniki za lamelami i czarną tkaniną"),
             ("wariant_C_grafit_orzech.jpg", "C · Grafit i orzech", "głośniki za czarną tkaniną, nisza z LED")]
    if not all(os.path.exists(os.path.join(OUT, p)) for p, _, _ in pliki):
        return None
    w = 1000
    ims = [Image.open(os.path.join(OUT, p)).convert("RGB") for p, _, _ in pliki]
    h = round(ims[0].height * w / ims[0].width)
    out = Image.new("RGB", (3 * w + 4 * 30, h + 150), PAPIER)
    d = ImageDraw.Draw(out)
    for i, (im, (_, t1, t2)) in enumerate(zip(ims, pliki)):
        x = 30 + i * (w + 30)
        out.paste(im.resize((w, h), Image.LANCZOS), (x, 30))
        d.text((x, h + 75), t1, font=f(34, True), fill=TUSZ, anchor="ls")
        d.text((x, h + 118), t2, font=f(24), fill=(90, 90, 90), anchor="ls")
    fn = os.path.join(OUT, "porownanie_wariantow.jpg")
    out.save(fn, quality=90)
    return fn


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(rysunek())
    print(opisz_przekroj())
    print(zestawienie())
