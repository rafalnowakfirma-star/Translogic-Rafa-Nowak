#!/usr/bin/env python3
"""Generuje stronę projektu koncepcyjnego „Dom Klocek”.

Parterowa stodoła ok. 150 m² z bloczków ICF, z przeszklonym szczytem salonu
i dużymi oknami w sypialni. Wszystkie rysunki (rzut, przekrój, elewacje,
aksonometrie) powstają z jednego zestawu wymiarów zapisanego poniżej.

Uruchom:  python3 generuj.py   →  dom-klocek.html
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "dom-klocek.html")

# ---------------------------------------------------------------- geometria [m]
L, B = 19.0, 9.0            # wymiary zewnętrzne: długość (W–E) × szerokość (N–S)
TW = 0.35                   # ściana ICF: 15 EPS + 15 beton + 5 EPS
LAYERS = [(0.0, 0.15, "d-eps"), (0.15, 0.30, "d-conc"), (0.30, 0.35, "d-eps")]
PITCH = 40.0
T40 = math.tan(math.radians(PITCH))
ROOF_T = 0.35               # grubość warstw dachu (prostopadle do połaci)
ROOF_V = ROOF_T / math.cos(math.radians(PITCH))
IN_OUTER = 3.15             # korona ścian: 13 warstw bloczków od płyty (−0,10)
EAVE = IN_OUTER + ROOF_V    # okap (wierzch pokrycia)
RIDGE = EAVE + B / 2 * T40  # kalenica
IN_APEX = IN_OUTER + B / 2 * T40
CEIL = 2.80                 # sufit w pokojach (salon i sypialnia otwarte do kalenicy)
TERRAIN = -0.30
SLAB_TOP = -0.10

WA = (7.20, 7.32)           # ściana między salonem a holem

# otwory w ścianach zewnętrznych na rzucie: (od, do, typ) – współrzędne wzdłuż ściany
OPEN_0 = {
    "N": [(4.20, 6.40, "win"), (8.30, 9.30, "door"), (10.36, 10.96, "win"), (12.50, 13.30, "win"),
          (17.10, 17.90, "win")],
    "S": [(1.00, 6.00, "hs"), (8.05, 9.65, "win"), (11.25, 12.85, "win"), (14.40, 17.80, "hs")],
    "W": [(1.75, 7.25, "hs")],
    "E": [(1.40, 2.20, "win"), (3.60, 5.40, "win")],
}
# okna na elewacjach: (ściana, od, do, z_dół, z_góra[, "door"])
WINDOWS_ELEV = [
    ("N", 4.20, 6.40, 1.05, 2.30), ("N", 8.30, 9.30, 0.0, 2.25, "door"), ("N", 10.36, 10.96, 1.50, 2.30),
    ("N", 12.50, 13.30, 1.50, 2.30), ("N", 17.10, 17.90, 1.50, 2.30),
    ("S", 1.00, 6.00, 0.0, 2.60), ("S", 8.05, 9.65, 0.50, 2.50), ("S", 11.25, 12.85, 0.50, 2.50),
    ("S", 14.40, 17.80, 0.0, 2.60),
    ("W", 1.75, 7.25, 0.0, 2.60),
    ("E", 1.40, 2.20, 1.50, 2.30), ("E", 3.60, 5.40, 0.0, 5.60),
]


def gable_top(v):
    """Spód połaci na licu zewnętrznym szczytu w odległości v od okapu."""
    return IN_OUTER + T40 * min(v, B - v)


# przeszklony trójkąt szczytu zachodniego, nad oknem HS (współrzędna wzdłuż szczytu, z)
GLASS_GABLE = [(2.25, 2.85), (6.75, 2.85), (6.75, gable_top(6.75) - 0.35),
               (B / 2, IN_APEX - 0.35), (2.25, gable_top(2.25) - 0.35)]
GLASS_GABLE_MULL = [3.75, 5.25]


def pl(v, d=2):
    return f"{v:.{d}f}".replace(".", ",").replace("-", "−")


def lvl(v):
    if abs(v) < 1e-6:
        return "±0,00"
    return ("+" if v > 0 else "−") + pl(abs(v))


def cm(v):
    return f"{round(v * 100):d}"


# ------------------------------------------------------------- powierzchnie
ROOMS = [
    ("01", "Salon z kuchnią", (0.35, 0.35, 7.20, 8.65), (2.0, 1.75)),
    ("02", "Hol", (7.32, 0.35, 9.70, 4.42), (8.75, 2.85)),
    ("03", "Korytarz", (9.70, 3.22, 13.60, 4.42), (11.65, 3.72)),
    ("04", "Pralnia", (9.82, 0.35, 11.50, 3.10), (10.66, 1.55)),
    ("05", "Łazienka", (11.62, 0.35, 14.20, 3.10), (12.95, 1.75)),
    ("06", "Pokój", (7.32, 4.54, 10.40, 8.65), (8.95, 7.10)),
    ("07", "Pokój", (10.52, 4.54, 13.60, 8.65), (11.85, 7.10)),
    ("08", "Sypialnia", (13.72, 3.22, 18.65, 8.65), (16.20, 4.75)),
    ("09", "Garderoba", (14.32, 0.35, 16.20, 3.10), (15.26, 1.90)),
    ("10", "Łazienka", (16.32, 0.35, 18.65, 3.10), (17.50, 1.95)),
]


def area(r):
    x1, y1, x2, y2 = r
    return (x2 - x1) * (y2 - y1)


AREAS = [(n, nm, area(r)) for n, nm, r, _ in ROOMS]
TOTAL = sum(a[2] for a in AREAS)

# ------------------------------------------------------------- narzędzia SVG


class Svg:
    def __init__(self, w, h, label):
        self.w, self.h, self.label, self.el = w, h, label, []

    def add(self, s):
        self.el.append(s)

    def render(self, cls="drw"):
        return (f'<svg class="{cls}" viewBox="0 0 {self.w:.0f} {self.h:.0f}" role="img" '
                f'aria-label="{self.label}" xmlns="http://www.w3.org/2000/svg">' + "".join(self.el) + "</svg>")


def f(v):
    return f"{v:.1f}"


def pts(points):
    return " ".join(f"{f(x)},{f(y)}" for x, y in points)


class Plan:
    """Rzut: współrzędne w metrach, północ u góry, y rośnie na południe."""

    def __init__(self, label, s=52, ox=96, oy=100, extra_h=0):
        self.S, self.ox, self.oy = s, ox, oy
        self.svg = Svg(ox * 2 + L * s, oy * 2 + B * s + extra_h, label)

    def P(self, x, y):
        return self.ox + x * self.S, self.oy + y * self.S

    def rect(self, x1, y1, x2, y2, cls, extra=""):
        (a, b), (c, d) = self.P(x1, y1), self.P(x2, y2)
        self.svg.add(f'<rect x="{f(min(a, c))}" y="{f(min(b, d))}" width="{f(abs(c - a))}" '
                     f'height="{f(abs(d - b))}" class="{cls}" {extra}/>')

    def line(self, x1, y1, x2, y2, cls="d-line", extra=""):
        (a, b), (c, d) = self.P(x1, y1), self.P(x2, y2)
        self.svg.add(f'<line x1="{f(a)}" y1="{f(b)}" x2="{f(c)}" y2="{f(d)}" class="{cls}" {extra}/>')

    def poly(self, points, cls):
        self.svg.add(f'<polygon points="{pts([self.P(*p) for p in points])}" class="{cls}"/>')

    def path(self, d, cls):
        self.svg.add(f'<path d="{d}" class="{cls}"/>')

    def text(self, x, y, s, cls, anchor="middle", rot=None, dx=0, dy=0):
        a, b = self.P(x, y)
        a += dx
        b += dy
        tr = f' transform="rotate({rot} {f(a)} {f(b)})"' if rot is not None else ""
        self.svg.add(f'<text x="{f(a)}" y="{f(b)}" text-anchor="{anchor}" class="{cls}"{tr}>{s}</text>')

    def circle(self, x, y, r, cls):
        a, b = self.P(x, y)
        self.svg.add(f'<circle cx="{f(a)}" cy="{f(b)}" r="{f(r * self.S)}" class="{cls}"/>')


def split(a, b, gaps):
    segs, cur = [], a
    for g1, g2 in sorted(gaps):
        if g1 > cur:
            segs.append((cur, g1))
        cur = max(cur, g2)
    if cur < b:
        segs.append((cur, b))
    return segs


def outer_walls(p, openings):
    """Ściany zewnętrzne ICF z warstwami: EPS / beton / EPS."""
    for a, b, cls in LAYERS:
        for side, ops in openings.items():
            gaps = [(o[0], o[1]) for o in ops]
            if side in "NS":
                for s1, s2 in split(a, L - a, gaps):
                    if side == "N":
                        p.rect(s1, a, s2, b, cls)
                    else:
                        p.rect(s1, B - b, s2, B - a, cls)
            else:
                for s1, s2 in split(a, B - a, gaps):
                    if side == "W":
                        p.rect(a, s1, b, s2, cls)
                    else:
                        p.rect(L - b, s1, L - a, s2, cls)
    # krawędzie: lico zewnętrzne, wewnętrzne, ościeża
    for side, ops in openings.items():
        gaps = [(o[0], o[1]) for o in ops]
        if side in "NS":
            yo, yi = (0, TW) if side == "N" else (B, B - TW)
            for s1, s2 in split(0, L, gaps):
                p.line(s1, yo, s2, yo, "d-cut")
            for s1, s2 in split(TW, L - TW, gaps):
                p.line(s1, yi, s2, yi, "d-cut")
            for g1, g2 in gaps:
                p.line(g1, yo, g1, yi, "d-cut")
                p.line(g2, yo, g2, yi, "d-cut")
        else:
            xo, xi = (0, TW) if side == "W" else (L, L - TW)
            for s1, s2 in split(0, B, gaps):
                p.line(xo, s1, xo, s2, "d-cut")
            for s1, s2 in split(TW, B - TW, gaps):
                p.line(xi, s1, xi, s2, "d-cut")
            for g1, g2 in gaps:
                p.line(xo, g1, xi, g1, "d-cut")
                p.line(xo, g2, xi, g2, "d-cut")
    # stolarka
    for side, ops in openings.items():
        for g1, g2, kind in ops:
            if kind == "door":
                continue
            if side in "NS":
                yo, yi = (0, TW) if side == "N" else (B, B - TW)
                sgn = 1 if side == "N" else -1
                p.line(g1, yo, g2, yo, "d-thin")
                p.line(g1, yi, g2, yi, "d-thin")
                p.rect(g1, yo + sgn * 0.12, g2, yo + sgn * 0.24, "d-win")
                if kind == "hs":
                    m = (g1 + g2) / 2
                    p.line(g1, yo + sgn * 0.16, m + 0.1, yo + sgn * 0.16, "d-thin")
                    p.line(m - 0.1, yo + sgn * 0.20, g2, yo + sgn * 0.20, "d-thin")
                else:
                    p.line(g1, yo + sgn * 0.18, g2, yo + sgn * 0.18, "d-thin")
            else:
                xo, xi = (0, TW) if side == "W" else (L, L - TW)
                sgn = 1 if side == "W" else -1
                p.line(xo, g1, xo, g2, "d-thin")
                p.line(xi, g1, xi, g2, "d-thin")
                p.rect(xo + sgn * 0.12, g1, xo + sgn * 0.24, g2, "d-win")
                if kind == "hs":
                    m = (g1 + g2) / 2
                    p.line(xo + sgn * 0.16, g1, xo + sgn * 0.16, m + 0.1, "d-thin")
                    p.line(xo + sgn * 0.20, m - 0.1, xo + sgn * 0.20, g2, "d-thin")
                else:
                    p.line(xo + sgn * 0.18, g1, xo + sgn * 0.18, g2, "d-thin")


def wall_v(p, x1, x2, y1, y2, gaps=()):
    for s1, s2 in split(y1, y2, gaps):
        p.rect(x1, s1, x2, s2, "d-part")
        p.line(x1, s1, x1, s2, "d-cut")
        p.line(x2, s1, x2, s2, "d-cut")
        if s1 > y1:
            p.line(x1, s1, x2, s1, "d-cut")
        if s2 < y2:
            p.line(x1, s2, x2, s2, "d-cut")


def wall_h(p, y1, y2, x1, x2, gaps=()):
    for s1, s2 in split(x1, x2, gaps):
        p.rect(s1, y1, s2, y2, "d-part")
        p.line(s1, y1, s2, y1, "d-cut")
        p.line(s1, y2, s2, y2, "d-cut")
        if s1 > x1:
            p.line(s1, y1, s1, y2, "d-cut")
        if s2 < x2:
            p.line(s2, y1, s2, y2, "d-cut")


def door_v(p, xa, xb, y1, y2, swing, hinge):
    """Drzwi w ścianie pionowej (x od xa do xb). swing +1 = na wschód. hinge 'top'/'bottom'."""
    w = y2 - y1
    xf = xb if swing > 0 else xa
    yh, yo = (y1, y2) if hinge == "top" else (y2, y1)
    s = 1 if yo > yh else -1
    p.line(xf, yh, xf + swing * w, yh, "d-leaf")
    a, b = p.P(xf + swing * w, yh)
    c, d = p.P(xf, yo)
    sweep = 1 if swing * s > 0 else 0
    p.path(f"M{f(a)},{f(b)} A{f(w * p.S)},{f(w * p.S)} 0 0 {sweep} {f(c)},{f(d)}", "d-swing")


def door_h(p, ya, yb, x1, x2, swing, hinge):
    """Drzwi w ścianie poziomej (y od ya do yb). swing +1 = na południe. hinge 'left'/'right'."""
    w = x2 - x1
    yf = yb if swing > 0 else ya
    xh, xo = (x1, x2) if hinge == "left" else (x2, x1)
    s = 1 if xo > xh else -1
    p.line(xh, yf, xh, yf + swing * w, "d-leaf")
    a, b = p.P(xh, yf + swing * w)
    c, d = p.P(xo, yf)
    sweep = 1 if -swing * s > 0 else 0
    p.path(f"M{f(a)},{f(b)} A{f(w * p.S)},{f(w * p.S)} 0 0 {sweep} {f(c)},{f(d)}", "d-swing")


def tick(p, x, y):
    a, b = p.P(x, y)
    p.svg.add(f'<line x1="{f(a - 3.5)}" y1="{f(b + 3.5)}" x2="{f(a + 3.5)}" y2="{f(b - 3.5)}" class="d-dimtick"/>')


def dim_h(p, xs, y, y_from=None, min_label=0.3, above=True):
    p.line(xs[0] - 0.12, y, xs[-1] + 0.12, y, "d-dim")
    for x in xs:
        tick(p, x, y)
        if y_from is not None:
            p.line(x, y_from, x, y, "d-dimext")
    for x1, x2 in zip(xs, xs[1:]):
        if x2 - x1 >= min_label:
            p.text((x1 + x2) / 2, y, cm(x2 - x1), "d-dimt", dy=-4 if above else 11)


def dim_v(p, ys, x, x_from=None, min_label=0.3, left=True):
    p.line(x, ys[0] - 0.12, x, ys[-1] + 0.12, "d-dim")
    for y in ys:
        a, b = p.P(x, y)
        p.svg.add(f'<line x1="{f(a - 3.5)}" y1="{f(b + 3.5)}" x2="{f(a + 3.5)}" y2="{f(b - 3.5)}" class="d-dimtick"/>')
        if x_from is not None:
            p.line(x_from, y, x, y, "d-dimext")
    for y1, y2 in zip(ys, ys[1:]):
        if y2 - y1 >= min_label:
            p.text(x, (y1 + y2) / 2, cm(y2 - y1), "d-dimt", rot=-90, dx=-4 if left else 11)


def room_label(p, num, name, a_floor, a_eff, cx, cy, eff=False):
    p.text(cx, cy, name, "d-room", dy=-2)
    if eff:
        p.text(cx, cy, f"{num} · {pl(a_floor)} m² · użytk. {pl(a_eff)} m²", "d-area", dy=11)
    else:
        p.text(cx, cy, f"{num} · {pl(a_floor)} m²", "d-area", dy=11)


def north_arrow(p, x, y):
    a, b = p.P(x, y)
    p.svg.add(f'<g transform="translate({f(a)},{f(b)})"><circle r="15" class="d-thin"/>'
              f'<polygon points="0,-13 5,6 0,2 -5,6" class="d-solid"/>'
              f'<text y="-19" text-anchor="middle" class="d-label">N</text></g>')


def scale_bar(p, x, y):
    a, b = p.P(x, y)
    s = p.S
    g = [f'<g transform="translate({f(a)},{f(b)})">']
    for i in range(5):
        cls = "d-solid" if i % 2 == 0 else "d-hollow"
        g.append(f'<rect x="{f(i * s)}" y="0" width="{f(s)}" height="5" class="{cls}"/>')
    for i in (0, 1, 2, 5):
        g.append(f'<text x="{f(i * s)}" y="17" text-anchor="middle" class="d-dimt">{i}</text>')
    g.append(f'<text x="{f(5 * s + 10)}" y="6" class="d-dimt">m</text></g>')
    p.svg.add("".join(g))


def furniture(p):
    F = "d-furn"

    def box(x1, y1, x2, y2, cross=False):
        p.rect(x1, y1, x2, y2, F)
        if cross:
            p.line(x1, y1, x2, y2, F)
            p.line(x2, y1, x1, y2, F)

    # kuchnia: zabudowa pod oknem, słupek z lodówką, wyspa z płytą
    box(3.40, 0.35, 7.20, 0.95)
    box(6.60, 0.35, 7.20, 0.95, cross=True)
    box(5.00, 0.45, 5.60, 0.85)
    box(3.80, 2.10, 6.20, 3.00)
    for cx in (4.45, 4.85):
        for cy in (2.35, 2.75):
            p.circle(cx, cy, 0.11, F)
    for cx in (4.40, 5.00, 5.60):
        p.circle(cx, 3.28, 0.17, F)
    # jadalnia
    box(4.20, 5.00, 6.40, 6.00)
    for cx in (4.65, 5.30, 5.95):
        box(cx - 0.2, 4.68, cx + 0.2, 4.95)
        box(cx - 0.2, 6.05, cx + 0.2, 6.32)
    # salon zwrócony do przeszklonego szczytu
    box(2.20, 2.90, 3.05, 6.30)
    box(2.20, 2.90, 3.05, 3.15)
    box(2.20, 6.05, 3.05, 6.30)
    box(1.05, 3.90, 1.75, 5.30)
    p.circle(0.95, 7.85, 0.28, F)
    # hol: szafa
    box(7.32, 0.35, 7.92, 2.20, cross=True)
    # pralnia: pralka, suszarka, zasobnik pompy ciepła
    p.circle(10.20, 2.75, 0.24, F)
    box(9.90, 2.45, 10.50, 3.05)
    p.circle(11.05, 0.80, 0.30, F)
    p.circle(11.05, 0.80, 0.18, F)
    # łazienka
    box(11.62, 0.35, 12.42, 2.05)
    box(11.62, 2.20, 12.52, 3.10, cross=True)
    box(13.55, 0.35, 14.15, 0.80)
    p.circle(13.85, 2.30, 0.18, F)
    box(14.02, 2.10, 14.20, 2.50)
    # pokój 06
    box(7.32, 5.60, 8.22, 7.60)
    box(7.32, 5.60, 8.22, 5.90)
    box(8.30, 8.05, 9.50, 8.65)
    box(9.80, 4.54, 10.40, 6.20, cross=True)
    # pokój 07
    box(12.70, 5.90, 13.60, 7.90)
    box(12.70, 7.60, 13.60, 7.90)
    box(11.40, 8.05, 12.60, 8.65)
    box(10.52, 4.54, 11.12, 6.20, cross=True)
    # sypialnia: łóżko 160, fotel przy wysokim oknie
    box(13.72, 5.40, 15.72, 7.00)
    box(13.72, 5.40, 14.05, 7.00)
    box(13.72, 4.90, 14.12, 5.30)
    box(13.72, 7.10, 14.12, 7.50)
    box(17.55, 5.90, 18.30, 6.65)
    # garderoba
    box(14.32, 0.35, 16.20, 0.95)
    box(14.32, 0.95, 14.92, 2.60)
    # łazienka przy sypialni
    box(16.32, 0.35, 17.52, 1.25, cross=True)
    box(18.10, 2.20, 18.65, 3.00)
    p.circle(18.30, 0.80, 0.18, F)
    box(18.47, 0.60, 18.65, 1.00)


def plan_parter():
    p = Plan("Rzut parteru – rysunek poglądowy", s=46, ox=86, oy=90, extra_h=6)
    for _, _, r, _ in ROOMS:
        p.rect(*r, "d-floor")
    # strefy z sufitem otwartym do kalenicy
    p.rect(0.35, 0.35, WA[0], B - TW, "d-open")
    p.rect(13.72, 3.22, L - TW, B - TW, "d-open")
    p.line(0.35, B / 2, WA[0], B / 2, "d-ridge")
    p.line(13.72, B / 2, L - TW, B / 2, "d-ridge")
    p.text(0.55, B / 2 - 0.10, "kalenica – sufit otwarty", "d-note", anchor="start")
    furniture(p)
    outer_walls(p, OPEN_0)
    wall_v(p, *WA, TW, B - TW, gaps=[(2.40, 4.20)])
    wall_v(p, 9.70, 9.82, TW, 3.10)
    wall_v(p, 11.50, 11.62, TW, 3.10)
    wall_v(p, 14.20, 14.32, TW, 3.10)
    wall_v(p, 16.20, 16.32, TW, 3.10)
    wall_v(p, 10.40, 10.52, 4.54, B - TW)
    wall_v(p, 13.60, 13.72, 3.22, B - TW, gaps=[(3.32, 4.22)])
    wall_h(p, 3.10, 3.22, 9.70, L - TW, gaps=[(10.30, 11.10), (12.70, 13.50), (14.60, 15.40), (16.60, 17.40)])
    wall_h(p, 4.42, 4.54, 7.32, 13.60, gaps=[(8.70, 9.60), (12.60, 13.50)])
    door_h(p, 0, TW, 8.30, 9.30, +1, "right")
    door_h(p, 3.10, 3.22, 10.30, 11.10, -1, "left")
    door_h(p, 3.10, 3.22, 12.70, 13.50, -1, "left")
    door_h(p, 3.10, 3.22, 14.60, 15.40, -1, "left")
    door_h(p, 3.10, 3.22, 16.60, 17.40, -1, "right")
    door_h(p, 4.42, 4.54, 8.70, 9.60, +1, "right")
    door_h(p, 4.42, 4.54, 12.60, 13.50, +1, "right")
    door_v(p, 13.60, 13.72, 3.32, 4.22, +1, "top")
    p.text(8.80, -0.22, "wejście", "d-note")
    p.text(3.50, B + 0.42, "taras", "d-note")
    p.text(16.10, B + 0.42, "taras przy sypialni", "d-note")
    for n, nm, r, (cx, cy) in ROOMS:
        room_label(p, n, nm, area(r), area(r), cx, cy)
    # wymiary orientacyjne: tylko gabaryty
    dim_h(p, [0, L], -0.75, y_from=-0.08)
    dim_v(p, [0, B], -0.75, x_from=-0.08)
    # linia przekroju A–A (patrzymy na zachód, na przeszklony szczyt)
    for y0, y1 in ((-1.25, -0.55), (B + 0.55, B + 1.25)):
        p.line(3.50, y0, 3.50, y1, "d-section")
    for yy in (-1.25, B + 1.25):
        a, b = p.P(3.50, yy)
        p.svg.add(f'<line x1="{f(a)}" y1="{f(b)}" x2="{f(a - 16)}" y2="{f(b)}" class="d-section" marker-end="url(#arrow)"/>')
        p.svg.add(f'<text x="{f(a + 6)}" y="{f(b + 5)}" class="d-label">A</text>')
    north_arrow(p, L + 0.95, -1.05)
    scale_bar(p, L - 5.4, B + 1.10)
    return p.svg.render()


# ------------------------------------------------------- przekrój i elewacje
class Elev:
    """Widok pionowy: poziomo h [m], pionowo z [m]."""

    def __init__(self, label, h_min, h_max, z_min=-1.0, z_max=8.2, s=46, pad_l=60, pad_r=70):
        self.S, self.hmin, self.zmax = s, h_min, z_max
        self.pad_l = pad_l
        self.svg = Svg(pad_l + pad_r + (h_max - h_min) * s, 24 + (z_max - z_min) * s, label)

    def P(self, h, z):
        return self.pad_l + (h - self.hmin) * self.S, 12 + (self.zmax - z) * self.S

    def poly(self, points, cls, extra=""):
        self.svg.add(f'<polygon points="{pts([self.P(*q) for q in points])}" class="{cls}" {extra}/>')

    def rect(self, h1, z1, h2, z2, cls):
        self.poly([(h1, z1), (h2, z1), (h2, z2), (h1, z2)], cls)

    def line(self, h1, z1, h2, z2, cls="d-line"):
        (a, b), (c, d) = self.P(h1, z1), self.P(h2, z2)
        self.svg.add(f'<line x1="{f(a)}" y1="{f(b)}" x2="{f(c)}" y2="{f(d)}" class="{cls}"/>')

    def text(self, h, z, s, cls, anchor="middle", dx=0, dy=0, rot=None):
        a, b = self.P(h, z)
        a += dx
        b += dy
        tr = f' transform="rotate({rot} {f(a)} {f(b)})"' if rot is not None else ""
        self.svg.add(f'<text x="{f(a)}" y="{f(b)}" text-anchor="{anchor}" class="{cls}"{tr}>{s}</text>')

    def level(self, h, z, label, side="right"):
        a, b = self.P(h, z)
        self.svg.add(f'<polygon points="{f(a)},{f(b)} {f(a - 5)},{f(b - 8)} {f(a + 5)},{f(b - 8)}" class="d-hollow"/>')
        self.svg.add(f'<line x1="{f(a - 8)}" y1="{f(b)}" x2="{f(a + 34)}" y2="{f(b)}" class="d-thin"/>')
        self.svg.add(f'<text x="{f(a + 8)}" y="{f(b - 3)}" class="d-dimt">{label}</text>')

    def vdim(self, h, zs, left=True):
        self.line(h, zs[0], h, zs[-1], "d-dim")
        for z in zs:
            a, b = self.P(h, z)
            self.svg.add(f'<line x1="{f(a - 3.5)}" y1="{f(b + 3.5)}" x2="{f(a + 3.5)}" y2="{f(b - 3.5)}" class="d-dimtick"/>')
        for z1, z2 in zip(zs, zs[1:]):
            self.text(h, (z1 + z2) / 2, cm(z2 - z1), "d-dimt", rot=-90, dx=-4 if left else 11)


def panes(e, h1, h2, z1, z2, cls="e-frame", step=1.9):
    """Słupki i ślemię dzielące duże przeszklenie."""
    n = max(1, round((h2 - h1) / step))
    for i in range(1, n):
        m = h1 + (h2 - h1) * i / n
        e.rect(m - 0.04, z1, m + 0.04, z2, cls)
    if z2 - z1 > 3.2:
        e.rect(h1, 2.56, h2, 2.64, cls)


def section_aa():
    """Przekrój przez salon w osi x = 3,50, widok na zachód (na przeszklony szczyt).
    Północ po prawej: h = B − y."""
    e = Elev("Przekrój A–A przez salon – widok na przeszklony szczyt", -1.6, B + 1.6,
             z_min=-1.1, z_max=7.9, s=44, pad_l=200, pad_r=86)

    def H(y):
        return B - y

    # grunt, podsypka, XPS, płyta
    e.rect(-1.6, -1.1, B + 1.6, TERRAIN, "d-ground")
    e.line(-1.6, TERRAIN, B + 1.6, TERRAIN, "d-line")
    e.rect(-0.45, -0.85, B + 0.45, -0.55, "d-gravel")
    e.rect(-0.15, -0.55, B + 0.15, -0.35, "d-eps")
    e.rect(-0.15, -0.35, 0, SLAB_TOP, "d-eps")
    e.rect(B, -0.35, B + 0.15, SLAB_TOP, "d-eps")
    e.rect(0, -0.35, B, SLAB_TOP, "d-concx")
    e.rect(TW, SLAB_TOP, B - TW, 0, "d-screed")
    # w tle: szczyt zachodni od środka (lico wewnętrzne) z oknem HS i przeszklonym trójkątem
    e.poly([(TW, 0), (B - TW, 0), (B - TW, gable_top(TW)), (B / 2, IN_APEX), (TW, gable_top(TW))], "d-beyond")
    s_ = [w for w in WINDOWS_ELEV if w[0] == "W"][0]
    h1, h2 = sorted((H(s_[1]), H(s_[2])))
    e.rect(h1, s_[3], h2, s_[4], "d-glassb")
    panes(e, h1, h2, s_[3], s_[4], "d-mull")
    e.poly([(H(y), z) for y, z in GLASS_GABLE], "d-glassb")
    for y in GLASS_GABLE_MULL:
        e.rect(H(y) - 0.04, 2.85, H(y) + 0.04, gable_top(y) - 0.35, "d-mull")
    e.text(B / 2, 1.30, "okno przesuwne HS 550 × 260", "d-note")
    e.text(B / 2, 3.55, "przeszklenie stałe", "d-note")
    # ściana północna (pełna) i południowa (otwór HS 0–2,60)
    for a, b, cls in LAYERS:
        c = "d-concx" if cls == "d-conc" else cls
        e.rect(B - b, SLAB_TOP, B - a, IN_OUTER, c)       # północ (po prawej)
        e.rect(a, 2.60, b, IN_OUTER, c)                   # południe, nadproże
        e.rect(a, SLAB_TOP, b, 0, c)
    e.rect(0.12, 0, 0.24, 2.60, "d-win")
    e.line(0.18, 0, 0.18, 2.60, "d-thin")
    for h1_, h2_ in ((0, TW), (B - TW, B)):
        e.line(h1_, SLAB_TOP, h1_, IN_OUTER, "d-cut")
        e.line(h2_, SLAB_TOP, h2_, IN_OUTER, "d-cut")
    # dach
    outer = [(0, EAVE), (B / 2, RIDGE), (B, EAVE)]
    inner = [(B, IN_OUTER), (B / 2, IN_APEX), (0, IN_OUTER)]
    e.poly(outer + inner, "d-roofcut")
    for a_, b_ in ((outer[0], outer[1]), (outer[1], outer[2]), (inner[0], inner[1]), (inner[1], inner[2]),
                   ((0, IN_OUTER), (0, EAVE)), ((B, IN_OUTER), (B, EAVE))):
        e.line(*a_, *b_, "d-cut")
    # stalowe ściągi zamiast jętek – nie zasłaniają szczytu
    zt = 4.60
    dy = (zt - IN_OUTER) / T40
    e.line(dy, zt, B - dy, zt, "d-tie")
    e.text(B / 2 - 1.3, zt + 0.12, "ściąg stalowy", "d-note")
    e.text(B / 2, 0.45, "01 Salon z kuchnią", "d-room")
    # wymiary wysokości
    e.vdim(1.55, [0, 2.60])
    e.vdim(B / 2, [0, IN_APEX], left=False)
    # poziomy
    hx = B + 0.75
    for z, t in ((RIDGE, lvl(RIDGE) + " kalenica"), (EAVE, lvl(EAVE) + " okap"),
                 (0, "±0,00"), (TERRAIN, lvl(TERRAIN) + " teren")):
        e.level(hx, z, t)
    e.text(B - 1.25, EAVE + 0.18, "40°", "d-dimt")
    e.line(B - 1.6, EAVE, B, EAVE, "d-thin")
    # opisy warstw
    notes = [
        (6.2, (1.6, EAVE + 1.6 * T40 - 0.22), "Dach: blacha na rąbek, membrana,"),
        (6.2, None, "krokwie + wełna 25 cm, płyta g-k"),
        (2.0, (0.18, 2.95), "Nadproże żelbetowe w bloczkach ICF"),
        (1.0, (0.08, 1.0), "Okno HS w warstwie ocieplenia"),
        (-0.45, (0.4, -0.22), "Płyta fundamentowa 25 cm"),
        (-0.45, None, "na XPS 20 cm i podsypce"),
    ]
    for z, target, t in notes:
        dy_ = 11 if target is None else 0
        e.text(-1.55, z, t, "d-note", anchor="start", dx=-140, dy=dy_)
        if target is not None:
            a, b = e.P(-1.55, z)
            c, d = e.P(*target)
            e.svg.add(f'<polyline points="{f(a - 140 + 2)},{f(b + 3)} {f(a + 30)},{f(b + 3)} {f(c)},{f(d)}" class="d-leader"/>')
            e.svg.add(f'<circle cx="{f(c)}" cy="{f(d)}" r="1.8" class="d-solid"/>')
    return e.svg.render()


def elevation(side):
    """Elewacje. N: patrzymy na południe (wschód po lewej). S: zachód po lewej.
    W: północ po lewej. E: południe po lewej."""
    long_side = side in "NS"
    width = L if long_side else B
    e = Elev(f"Elewacja {side}", -0.8, width + 0.8, z_min=-0.8, z_max=7.9, s=34, pad_l=24, pad_r=80)

    def h_of(t):
        if side == "N":
            return L - t
        if side == "E":
            return B - t
        return t

    e.rect(-0.8, -0.8, width + 0.8, TERRAIN, "d-groundl")
    e.line(-0.8, TERRAIN, width + 0.8, TERRAIN, "d-line")
    if long_side:
        e.rect(0, TERRAIN, L, 0, "e-plinth")
        e.rect(0, 0, L, IN_OUTER, "e-wall")
        e.rect(0, IN_OUTER, L, RIDGE, "e-roof")
        for i in range(1, int(L / 0.5)):
            e.line(i * 0.5, IN_OUTER + 0.1, i * 0.5, RIDGE, "e-seam")
        if side == "S":
            s0, s1 = 1.55, 4.40
            sn = math.sin(math.radians(PITCH))
            e.rect(h_of(8.0), EAVE + s0 * sn, h_of(13.5), EAVE + s1 * sn, "e-pv")
            for i in range(1, 6):
                x = 8.0 + i * 5.5 / 6
                e.line(x, EAVE + s0 * sn, x, EAVE + s1 * sn, "e-pvline")
        e.rect(0, IN_OUTER, L, EAVE, "e-fascia")
        e.line(0, RIDGE, L, RIDGE, "d-line")
        e.poly([(0, TERRAIN), (L, TERRAIN), (L, RIDGE), (0, RIDGE)], "d-outline")
    else:
        gable = [(0, TERRAIN), (B, TERRAIN), (B, IN_OUTER), (B / 2, IN_APEX), (0, IN_OUTER)]
        e.poly(gable, "e-wood")
        n = int(B / 0.15)
        for i in range(1, n + 1):
            h = i * 0.15
            e.line(h, 0.0, h, gable_top(h), "e-board")
        e.rect(0, TERRAIN, B, 0, "e-plinth")
        e.poly([(0, IN_OUTER), (B / 2, IN_APEX), (B, IN_OUTER), (B, EAVE), (B / 2, RIDGE), (0, EAVE)], "e-roofedge")
        e.poly(gable[:2] + [(B, EAVE), (B / 2, RIDGE), (0, EAVE)], "d-outline")
        if side == "W":
            pts_ = [(h_of(y), z) for y, z in GLASS_GABLE]
            e.poly(pts_, "e-frame")
            g = [(h_of(y), z) for y, z in GLASS_GABLE]
            # szyba odsunięta od ramy o 7 cm
            cx = B / 2
            inset = [(x + (0.07 if x < cx else -0.07), z + (0.07 if z < 3 else -0.09)) for x, z in g]
            inset[3] = (cx, g[3][1] - 0.1)
            e.poly(inset, "e-glass")
            for y in GLASS_GABLE_MULL:
                e.rect(h_of(y) - 0.04, 2.85, h_of(y) + 0.04, gable_top(y) - 0.35, "e-frame")
    for w in WINDOWS_ELEV:
        s_, t1, t2, z1, z2 = w[:5]
        if s_ != side:
            continue
        h1, h2 = sorted((h_of(t1), h_of(t2)))
        door = len(w) > 5
        e.rect(h1, z1, h2, z2, "e-frame")
        if door:
            e.rect(h1 + 0.08, z1, h2 - 0.08, z2 - 0.08, "e-door")
            e.rect(h2 - 0.30, z1 + 0.3, h2 - 0.16, z2 - 0.35, "e-glass")
        else:
            e.rect(h1 + 0.07, z1 + 0.07, h2 - 0.07, z2 - 0.07, "e-glass")
            if h2 - h1 > 1.7 or z2 - z1 > 3.2:
                panes(e, h1, h2, z1, z2)
    hx = width + 0.35
    e.level(hx, RIDGE, lvl(RIDGE))
    e.level(hx, EAVE if long_side else IN_OUTER, lvl(EAVE))
    e.level(hx, 0, "±0,00")
    e.level(hx, TERRAIN, lvl(TERRAIN))
    return e.svg.render()


# --------------------------------------------------------------- aksonometria
class Axo:
    """u = x (wschód), v = 7 − y (od elewacji południowej na północ), z w górę."""

    def __init__(self, label, w, h, k, cx, cy):
        self.k, self.cx, self.cy = k, cx, cy
        self.svg = Svg(w, h, label)

    def P(self, u, v, z):
        return (self.cx + self.k * (u * 0.94 - v * 0.57),
                self.cy - self.k * (z + u * 0.20 + v * 0.45))

    def poly(self, points, cls, extra=""):
        self.svg.add(f'<polygon points="{pts([self.P(*q) for q in points])}" class="{cls}" {extra}/>')

    def line(self, a, b, cls):
        (x1, y1), (x2, y2) = self.P(*a), self.P(*b)
        self.svg.add(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" class="{cls}"/>')

    def box(self, u1, v1, z1, u2, v2, z2, top, front, side):
        self.poly([(u1, v1, z1), (u1, v2, z1), (u1, v2, z2), (u1, v1, z2)], side)
        self.poly([(u1, v1, z1), (u2, v1, z1), (u2, v1, z2), (u1, v1, z2)], front)
        self.poly([(u1, v1, z2), (u2, v1, z2), (u2, v2, z2), (u1, v2, z2)], top)



def house_illustration():
    a = Axo("Wizualizacja domu Klocek od strony ogrodu (południowy zachód)", 860, 480, 29, 215, 425)
    S = a.svg
    c, sn = math.cos(math.radians(PITCH)), math.sin(math.radians(PITCH))
    S.add('<rect x="0" y="0" width="860" height="480" class="i-sky"/>')
    a.poly([(-14, -9, -0.3), (34, -9, -0.3), (34, 20, -0.3), (-14, 20, -0.3)], "i-grass")

    def tree(u, v, r, hgt):
        x, y = a.P(u, v, -0.3)
        xt, yt = a.P(u, v, hgt)
        S.add(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(xt)}" y2="{f(yt + r * a.k * 0.6)}" class="i-trunk"/>')
        S.add(f'<ellipse cx="{f(xt)}" cy="{f(yt)}" rx="{f(r * a.k)}" ry="{f(r * a.k * 1.15)}" class="i-tree"/>')
        S.add(f'<ellipse cx="{f(xt - r * a.k * 0.3)}" cy="{f(yt - r * a.k * 0.35)}" rx="{f(r * a.k * 0.45)}" '
              f'ry="{f(r * a.k * 0.5)}" class="i-tree-hi"/>')

    tree(-3.5, 3.0, 1.6, 5.8)
    tree(22.0, 8.0, 1.9, 6.8)
    # tarasy
    for u1, u2 in ((0.0, 6.6), (13.9, 18.4)):
        a.poly([(u1, -3.0, -0.18), (u2, -3.0, -0.18), (u2, 0, -0.18), (u1, 0, -0.18)], "i-deck")
        u = u1 + 0.3
        while u < u2 - 0.05:
            a.line((u, -3.0, -0.18), (u, 0, -0.18), "i-deckline")
            u += 0.3
        a.poly([(u1, -3.0, -0.3), (u2, -3.0, -0.3), (u2, -3.0, -0.18), (u1, -3.0, -0.18)], "i-deckedge")
    # szczyt zachodni w desce z przeszkleniem
    a.poly([(0, 0, TERRAIN), (0, B, TERRAIN), (0, B, IN_OUTER), (0, B / 2, IN_APEX), (0, 0, IN_OUTER)], "i-wood")
    for i in range(1, int(B / 0.18)):
        v = i * 0.18
        a.line((0, v, 0), (0, v, gable_top(v)), "i-board")
    a.poly([(0, 0, TERRAIN), (0, B, TERRAIN), (0, B, 0), (0, 0, 0)], "i-plinth")

    def glass_w(points_vz, mull_v=(), mull_z=None):
        a.poly([(0, v, z) for v, z in points_vz], "i-frame")
        cx = sum(v for v, _ in points_vz) / len(points_vz)
        cz = sum(z for _, z in points_vz) / len(points_vz)
        inset = [(v + 0.08 * (1 if v < cx else -1), z + 0.08 * (1 if z < cz else -1)) for v, z in points_vz]
        a.poly([(0, v, z) for v, z in inset], "i-glass")

    # okno HS w szczycie (v = 9 − y)
    hs = [w for w in WINDOWS_ELEV if w[0] == "W"][0]
    v1, v2 = B - hs[2], B - hs[1]
    glass_w([(v1, 0), (v2, 0), (v2, 2.60), (v1, 2.60)])
    for i in (1, 2):
        m = v1 + (v2 - v1) * i / 3
        a.poly([(0, m - .04, 0), (0, m + .04, 0), (0, m + .04, 2.6), (0, m - .04, 2.6)], "i-frame")
    gg = [(B - y, z) for y, z in GLASS_GABLE]
    glass_w(gg)
    for y in GLASS_GABLE_MULL:
        v = B - y
        a.poly([(0, v - .04, 2.85), (0, v + .04, 2.85), (0, v + .04, gable_top(v) - 0.35),
                (0, v - .04, gable_top(v) - 0.35)], "i-frame")
    # ściana południowa
    a.poly([(0, 0, TERRAIN), (L, 0, TERRAIN), (L, 0, IN_OUTER), (0, 0, IN_OUTER)], "i-wall")
    a.poly([(0, 0, TERRAIN), (L, 0, TERRAIN), (L, 0, 0), (0, 0, 0)], "i-plinth")
    for w in WINDOWS_ELEV:
        s_, u1, u2, z1, z2 = w[:5]
        if s_ != "S":
            continue
        a.poly([(u1, 0, z1), (u2, 0, z1), (u2, 0, z2), (u1, 0, z2)], "i-frame")
        a.poly([(u1 + .07, 0, z1 + .07), (u2 - .07, 0, z1 + .07), (u2 - .07, 0, z2 - .07), (u1 + .07, 0, z2 - .07)], "i-glass")
        n = max(1, round((u2 - u1) / 1.8))
        for i in range(1, n):
            m = u1 + (u2 - u1) * i / n
            a.poly([(m - .04, 0, z1), (m + .04, 0, z1), (m + .04, 0, z2), (m - .04, 0, z2)], "i-frame")
    # dach
    a.poly([(0, 0, EAVE), (L, 0, EAVE), (L, B / 2, RIDGE), (0, B / 2, RIDGE)], "i-roof")
    for i in range(1, int(L / 0.5)):
        u = i * 0.5
        a.line((u, 0.03, EAVE + 0.02), (u, B / 2, RIDGE), "i-seam")
    s0, s1 = 1.55, 4.40
    a.poly([(8.0, s0 * c, EAVE + s0 * sn), (13.5, s0 * c, EAVE + s0 * sn),
            (13.5, s1 * c, EAVE + s1 * sn), (8.0, s1 * c, EAVE + s1 * sn)], "i-pv")
    for i in range(1, 6):
        u = 8.0 + i * 5.5 / 6
        a.line((u, s0 * c, EAVE + s0 * sn), (u, s1 * c, EAVE + s1 * sn), "i-pvline")
    sm = (s0 + s1) / 2
    a.line((8.0, sm * c, EAVE + sm * sn), (13.5, sm * c, EAVE + sm * sn), "i-pvline")
    a.poly([(0, 0, IN_OUTER), (0, B / 2, IN_APEX), (0, B, IN_OUTER), (0, B, EAVE), (0, B / 2, RIDGE), (0, 0, EAVE)], "i-roofedge")
    a.poly([(0, 0, IN_OUTER), (L, 0, IN_OUTER), (L, 0, EAVE), (0, 0, EAVE)], "i-roofedge")
    a.line((0, B / 2, RIDGE), (L, B / 2, RIDGE), "i-ridge")
    # postać na tarasie (skala 1,75 m)
    x, y = a.P(4.6, -1.5, -0.18)
    k = a.k
    S.add(f'<g class="i-person"><circle cx="{f(x)}" cy="{f(y - 1.62 * k)}" r="{f(0.12 * k)}"/>'
          f'<rect x="{f(x - 0.2 * k)}" y="{f(y - 1.47 * k)}" width="{f(0.4 * k)}" height="{f(0.7 * k)}" rx="{f(0.12 * k)}"/>'
          f'<rect x="{f(x - 0.15 * k)}" y="{f(y - 0.85 * k)}" width="{f(0.12 * k)}" height="{f(0.85 * k)}"/>'
          f'<rect x="{f(x + 0.03 * k)}" y="{f(y - 0.85 * k)}" width="{f(0.12 * k)}" height="{f(0.85 * k)}"/></g>')
    tree(22.5, -3.5, 1.3, 4.2)
    return S.render("illus")


def icf_rim(a, u1, v1, u2, v2, z):
    """Korona ściany ICF widziana z góry: EPS / rdzeń betonowy / EPS (wypełnienie evenodd)."""
    def ring(o, i_, cls):
        P = a.P
        outer = [P(u1 + o, v1 + o, z), P(u2 - o, v1 + o, z), P(u2 - o, v2 - o, z), P(u1 + o, v2 - o, z)]
        inner = [P(u1 + i_, v1 + i_, z), P(u1 + i_, v2 - i_, z), P(u2 - i_, v2 - i_, z), P(u2 - i_, v1 + i_, z)]
        d = "M" + " L".join(f"{f(x)},{f(y)}" for x, y in outer) + " Z M" + " L".join(f"{f(x)},{f(y)}" for x, y in inner) + " Z"
        a.svg.add(f'<path d="{d}" fill-rule="evenodd" class="{cls}"/>')
    ring(0, 0.15, "x-eps-top")
    ring(0.15, 0.30, "x-core")
    ring(0.30, 0.35, "x-eps-top")


def block_courses_face(a, face, z1, z2, length, top_fn=None):
    """Spoiny bloczków ICF (100 × 25 cm, przesunięcie o pół bloczka) na licu ściany."""
    n = int(round((z2 - z1) / 0.25))
    for c in range(n + 1):
        z = z1 + c * 0.25
        if face == "S":
            a.line((0, 0, z), (length, 0, z), "x-joint")
        else:
            a.line((0, 0, z), (0, length, z), "x-joint")
    for c in range(n):
        za, zb = z1 + c * 0.25, z1 + (c + 1) * 0.25
        off = 0.5 if c % 2 else 0.0
        t = off if off else 1.0
        while t < length - 0.01:
            if face == "S":
                a.line((t, 0, za), (t, 0, zb), "x-joint")
            else:
                a.line((0, t, za), (0, t, zb), "x-joint")
            t += 1.0


def assembly():
    a = Axo("Kolejność montażu – rozstrzelona aksonometria", 880, 600, 19, 120, 560)
    S = a.svg
    gap = 2.6
    # 1. płyta fundamentowa
    a.box(0, 0, -0.55, L, B, -0.10, "x-slab-top", "x-slab", "x-slab-side")
    a.poly([(0, 0, -0.55), (L, 0, -0.55), (L, 0, -0.35), (0, 0, -0.35)], "x-xps")
    a.poly([(0, 0, -0.55), (0, B, -0.55), (0, B, -0.35), (0, 0, -0.35)], "x-xps")
    # 2. ściany z bloczków ICF (13 warstw)
    z1 = gap
    zb, zt = SLAB_TOP + z1, IN_OUTER + z1
    a.poly([(TW, TW, zb), (L - TW, TW, zb), (L - TW, B - TW, zb), (TW, B - TW, zb)], "x-floor")
    a.poly([(TW, B - TW, zb), (L - TW, B - TW, zb), (L - TW, B - TW, zt), (TW, B - TW, zt)], "x-eps-in")
    a.poly([(L - TW, TW, zb), (L - TW, B - TW, zb), (L - TW, B - TW, zt), (L - TW, TW, zt)], "x-eps-in2")
    a.poly([(0, 0, zb), (0, B, zb), (0, B, zt), (0, 0, zt)], "x-eps-side")
    a.poly([(0, 0, zb), (L, 0, zb), (L, 0, zt), (0, 0, zt)], "x-eps-front")
    block_courses_face(a, "S", zb, zt, L)
    block_courses_face(a, "W", zb, zt, B)
    # otwory okienne zostawione w ścianach
    for w in WINDOWS_ELEV:
        s_, t1, t2, q1, q2 = w[:5]
        if s_ == "S":
            a.poly([(t1, 0, q1 + z1), (t2, 0, q1 + z1), (t2, 0, q2 + z1), (t1, 0, q2 + z1)], "x-hole")
        elif s_ == "W":
            a.poly([(0, B - t2, q1 + z1), (0, B - t1, q1 + z1), (0, B - t1, q2 + z1), (0, B - t2, q2 + z1)], "x-hole")
    a.poly([(0, B - 6.75, 2.85 + z1), (0, B - 2.25, 2.85 + z1), (0, B - 2.25, zt), (0, B - 6.75, zt)], "x-hole")
    icf_rim(a, 0, 0, L, B, zt)
    # 3. szczyty ICF: zachodni z otworem na przeszklenie, wschodni pełny
    z2 = 2 * gap
    base = IN_OUTER + z2
    a.poly([(L - TW, 0, base), (L - TW, B / 2, IN_APEX + z2), (L - TW, B, base)], "x-eps-in2")
    a.line((0, 0, base), (L, 0, base), "x-edge")
    a.line((0, B, base), (L - TW, B, base), "x-edge")
    a.poly([(0, 0, base), (0, B / 2, IN_APEX + z2), (0, B, base)], "x-eps-side")
    for cc in range(1, int((IN_APEX - IN_OUTER) / 0.25) + 1):
        z = base + cc * 0.25
        dv = (z - base) / T40
        if dv < B / 2:
            a.line((0, dv, z), (0, B - dv, z), "x-joint")
    a.poly([(0, B - y, max(z, IN_OUTER) + z2) for y, z in GLASS_GABLE], "x-hole")
    a.line((0, 0, base), (0, B / 2, IN_APEX + z2), "x-edge")
    a.line((0, B / 2, IN_APEX + z2), (0, B, base), "x-edge")
    a.line((0, 0, base), (0, B, base), "x-edge")
    # 4. dach
    z3 = 3 * gap + 2.2
    a.poly([(0, 0, IN_OUTER + z3), (0, B / 2, IN_APEX + z3), (0, B, IN_OUTER + z3), (0, B, EAVE + z3),
            (0, B / 2, RIDGE + z3), (0, 0, EAVE + z3)], "x-roof-edge")
    a.poly([(0, 0, EAVE + z3), (L, 0, EAVE + z3), (L, B / 2, RIDGE + z3), (0, B / 2, RIDGE + z3)], "x-roof")
    for i in range(1, int(L / 0.5)):
        a.line((i * 0.5, 0.02, EAVE + z3 + 0.02), (i * 0.5, B / 2, RIDGE + z3), "x-seam")
    a.poly([(0, 0, IN_OUTER + z3), (L, 0, IN_OUTER + z3), (L, 0, EAVE + z3), (0, 0, EAVE + z3)], "x-roof-edge")
    labels = [
        (-0.3, "1", "Izolowana płyta fundamentowa", "XPS 20 cm, beton 25 cm, instalacje w gruncie"),
        (z1 + 1.4, "2", "Ściany z bloczków ICF", "13 warstw na sucho → zbrojenie → beton"),
        (z2 + IN_OUTER + 0.4, "3", "Szczyty i wieniec", "bloczki docięte pod 40°, otwór na szklany szczyt"),
        (z3 + EAVE + 0.4, "4", "Dach", "krokwie lub płyty SIP, blacha na rąbek, PV"),
    ]
    for z, n, t1, t2 in labels:
        x, y = a.P(L, 0, z)
        S.add(f'<line x1="{f(x + 8)}" y1="{f(y)}" x2="{f(x + 40)}" y2="{f(y)}" class="d-leader"/>')
        S.add(f'<circle cx="{f(x + 52)}" cy="{f(y)}" r="11" class="x-badge"/>'
              f'<text x="{f(x + 52)}" y="{f(y + 4)}" text-anchor="middle" class="x-badge-t">{n}</text>')
        S.add(f'<text x="{f(x + 70)}" y="{f(y - 2)}" class="x-lt">{t1}</text>'
              f'<text x="{f(x + 70)}" y="{f(y + 12)}" class="x-ls">{t2}</text>')
    for zf, zt_ in ((-0.1, z1 - 0.4), (IN_OUTER + z1, z2 + IN_OUTER - 0.3), (IN_APEX + z2 - 0.6, z3 + IN_OUTER + 0.3)):
        x1, y1 = a.P(-1.6, -1.2, zf + 0.3)
        x2, y2 = a.P(-1.6, -1.2, zt_)
        S.add(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" class="x-arrow" marker-end="url(#arrow)"/>')
    return S.render("illus")


def block_figure():
    """Bloczek ICF i układanie „na zakładkę” jak klocki."""
    a = Axo("Bloczki ICF układane na sucho z przesunięciem o pół bloczka", 640, 230, 92, 70, 212)
    S = a.svg
    D = 0.35

    def block(u1, u2, z, top=True, left=True, studs=False, ghost=False):
        z2 = z + 0.25
        pre = "g-" if ghost else ""
        if left:
            a.poly([(u1, 0, z), (u1, D, z), (u1, D, z2), (u1, 0, z2)], pre + "b-side")
        a.poly([(u1, 0, z), (u2, 0, z), (u2, 0, z2), (u1, 0, z2)], pre + "b-front")
        if top:
            a.poly([(u1, 0, z2), (u2, 0, z2), (u2, 0.15, z2), (u1, 0.15, z2)], pre + "b-top")
            a.poly([(u1, 0.15, z2), (u2, 0.15, z2), (u2, 0.30, z2), (u1, 0.30, z2)], pre + "b-core")
            a.poly([(u1, 0.30, z2), (u2, 0.30, z2), (u2, D, z2), (u1, D, z2)], pre + "b-top")
            # łączniki w rdzeniu
            t = u1 + 0.125
            while t < u2 - 0.05:
                a.line((t, 0.15, z2), (t, 0.30, z2), pre + "b-tie")
                t += 0.25
            if studs:
                t = u1 + 0.0625
                while t < u2 - 0.05:
                    for v1, v2 in ((0.04, 0.11), (0.31, 0.34)):
                        a.poly([(t, v1, z2), (t + 0.06, v1, z2), (t + 0.06, v1, z2 + 0.025), (t, v1, z2 + 0.025)], pre + "b-stud")
                        a.poly([(t, v1, z2 + 0.025), (t + 0.06, v1, z2 + 0.025), (t + 0.06, v2, z2 + 0.025), (t, v2, z2 + 0.025)], pre + "b-studtop")
                    t += 0.125
    # trzy warstwy, 3 m ściany
    for c in range(3):
        z = c * 0.25
        if c % 2 == 0:
            spans = [(0, 1), (1, 2), (2, 3)]
        else:
            spans = [(0, 0.5), (0.5, 1.5), (1.5, 2.5), (2.5, 3)]
        for i, (u1, u2) in enumerate(spans):
            block(u1, u2, z, top=(c == 2), left=(i == 0), studs=(c == 2))
    # klocek opuszczany z góry
    block(0.5, 1.5, 1.20, top=True, left=True, studs=True, ghost=False)
    x1, y1 = a.P(1.0, 0.0, 1.17)
    x2, y2 = a.P(1.0, 0.0, 0.80)
    S.add(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" class="x-arrow" marker-end="url(#arrow)"/>')
    # opisy po prawej stronie ściany
    xr = a.P(3.0, 0, 0)[0] + 16
    x, y = a.P(1.5, 0, 1.45)
    S.add(f'<text x="{f(x + 8)}" y="{f(y - 6)}" class="x-ls">bloczek ok. 100 × 25 × 35 cm, kilka kg</text>')
    _, y = a.P(3.0, 0.35, 0.75)
    S.add(f'<text x="{f(xr)}" y="{f(y + 22)}" class="x-ls">rdzeń 15 cm na beton i zbrojenie</text>')
    _, y = a.P(3.0, 0, 0.30)
    S.add(f'<text x="{f(xr)}" y="{f(y + 4)}" class="x-ls">spoiny przesunięte o pół bloczka</text>')
    return S.render("illus")


def wall_detail():
    """Przekrój poziomy ściany zewnętrznej (od środka do zewnątrz)."""
    layers = [
        ("Tynk gipsowy na siatce", 0.015, "w-plaster"),
        ("EPS 5 cm (wewn. ścianka bloczka)", 0.05, "w-eps"),
        ("Beton C20/25 + zbrojenie 15 cm", 0.15, "w-conc"),
        ("EPS grafitowy 15 cm (zewn. ścianka)", 0.15, "w-eps2"),
        ("Klej, siatka, tynk silikonowy / deska", 0.008, "w-render"),
    ]
    s = 900  # px na metr
    W = 640
    x0 = 30
    svg = Svg(W, 252, "Przekrój poziomy ściany ICF, skala 1:10")
    x = x0
    svg.add(f'<text x="{x0}" y="22" class="x-ls">wnętrze (+20 °C)</text>')
    svg.add(f'<text x="{f(x0 + 0.373 * s)}" y="22" text-anchor="end" class="x-ls">zewnątrz (−20 °C)</text>')
    for i, (name, t, cls) in enumerate(layers):
        w = max(t * s, 4)
        svg.add(f'<rect x="{f(x)}" y="34" width="{f(w)}" height="120" class="{cls}"/>')
        if cls == "w-conc":
            for ry in (64, 124):
                svg.add(f'<circle cx="{f(x + w / 2)}" cy="{ry}" r="4.5" class="w-rebar"/>')
            for k in range(4):
                svg.add(f'<rect x="{f(x - 0.05 * s + 2)}" y="{40 + k * 30}" width="{f(w + 0.10 * s - 4)}" height="2" class="w-tie"/>')
        cx = x + w / 2
        ly = 172 + (len(layers) - 1 - i) * 17
        svg.add(f'<polyline points="{f(cx)},154 {f(cx)},{ly} 404,{ly}" class="d-leader"/>')
        svg.add(f'<text x="410" y="{ly + 4}" class="x-ls">{name}</text>')
        x += w
    # wymiar całkowity
    svg.add(f'<line x1="{x0}" y1="44" x2="{f(x)}" y2="44" class="d-dim" opacity="0"/>')
    tot = sum(l[1] for l in layers)
    svg.add(f'<text x="{f(x + 12)}" y="98" class="d-dimt">≈ {pl(tot * 100, 1)} cm</text>')
    return svg.render("illus")


# ------------------------------------------------------------------- treść
U_ROWS = [
    ("Opór przejmowania wewn. R<sub>si</sub>", None, None, 0.13),
    ("Tynk gipsowy", 0.015, 0.40, None),
    ("EPS 0,031 (wewn.)", 0.05, 0.031, None),
    ("Beton zbrojony", 0.15, 1.70, None),
    ("EPS grafitowy 0,031 (zewn.)", 0.15, 0.031, None),
    ("Tynk cienkowarstwowy", 0.008, 0.70, None),
    ("Opór przejmowania zewn. R<sub>se</sub>", None, None, 0.04),
]


def u_table():
    rows, total = [], 0.0
    for name, d, lam, r in U_ROWS:
        rr = r if r is not None else d / lam
        total += rr
        rows.append(f"<tr><td>{name}</td><td class='num'>{'' if d is None else pl(d * 100, 1)}</td>"
                    f"<td class='num'>{'' if lam is None else pl(lam, 3)}</td><td class='num'>{pl(rr, 3)}</td></tr>")
    u = 1 / total
    rows.append(f"<tr class='sum'><td>Suma oporów R<sub>T</sub></td><td></td><td></td><td class='num'>{pl(total, 2)}</td></tr>")
    return "\n".join(rows), u


TECH = [
    ("ICF – bloczki styropianowe zalewane betonem",
     "Lekkie kształtki z EPS z „zamkami” stawiasz na sucho jak klocki, wkładasz zbrojenie i zalewasz betonem. Styropian zostaje jako ocieplenie (szalunek tracony).",
     5, 4, 5, "ściany parteru: 1–2 tyg.",
     "Ciepła i masywna ściana jednym ruchem. Wymaga starannego betonowania i wentylacji mechanicznej. Producenci w Polsce, np. Izodom."),
    ("Drewniane bloczki izolowane",
     "Prefabrykowane klocki z drewna i ocieplenia skręcane śrubami, bez kleju i betonu. Przykłady: Gablok (Belgia), Brikawood (Francja).",
     5, 5, 2, "producenci deklarują kilka dni",
     "Najbliżej prawdziwego Lego i pełna sucha zabudowa. Import, mało wykonawców; sprawdź dopuszczenie do obrotu i ocenę techniczną w Polsce."),
    ("Panele SIP",
     "Gotowe płyty: dwie płyty OSB z rdzeniem z twardej pianki. Ściany i dach składa się z paneli dociętych w fabryce.",
     3, 3, 4, "1–2 tyg.",
     "Bardzo ciepłe i szybkie. Panele są ciężkie (HDS lub mały dźwig) i nie lubią wilgoci podczas budowy."),
    ("Prefabrykowane ściany szkieletowe",
     "Ściany z oknami i instalacjami przyjeżdżają z fabryki, ekipa producenta stawia stan surowy.",
     2, 1, 5, "montaż 2–5 dni",
     "Przewidywalny koszt i termin. Mało pracy własnej, za to wybór producenta decyduje o wszystkim."),
    ("Moduły 3D z fabryki",
     "Całe „pudełka” z wykończeniem, łazienkami i instalacjami stawiane dźwigiem. Dom 7 m szerokości to 2–3 moduły.",
     4, 1, 4, "1–2 dni na działce",
     "Najszybciej pod klucz. Szerokość modułu ogranicza transport, potrzebny dojazd dla dźwigu."),
    ("Płyty CLT (drewno klejone krzyżowo)",
     "Masywne płyty drewniane na ściany, stropy i dach, wycinane z otworami w fabryce.",
     3, 1, 3, "kilka dni",
     "Piękne drewno widoczne wewnątrz, dobra akustyka. Najdroższa z opcji drewnianych."),
    ("Bloczki z plastiku z recyklingu",
     "Klocki z przetworzonych odpadów plastikowych, np. ByBlock (ByFusion, USA) lub Conceptos Plásticos (Kolumbia).",
     5, 4, 1, "kilka dni",
     "Ciekawostka. W Polsce brak dopuszczeń do budynków mieszkalnych, trudności z ochroną przeciwpożarową."),
    ("Druk 3D z betonu",
     "Drukarka wylewa ściany warstwa po warstwie na budowie.",
     1, 1, 1, "kilka dni druku",
     "Pierwsze realizacje w Polsce, drogi sprzęt i wykonawca. To nie jest technologia do samodzielnej budowy."),
]


def dots(n):
    return '<span class="dots" aria-label="' + f"{n} na 5" + '">' + "".join(
        f'<i class="{"on" if i < n else ""}"></i>' for i in range(5)) + "</span>"


def tech_rows():
    out = []
    for i, (name, how, lego, diy, pl_, time, note) in enumerate(TECH):
        cls = ' class="pick"' if i == 0 else ""
        out.append(f"<tr{cls}><th scope='row'>{name}{'<span class=\"tag\">wybrana</span>' if i == 0 else ''}</th>"
                   f"<td>{how}</td><td>{dots(lego)}</td><td>{dots(diy)}</td><td>{dots(pl_)}</td>"
                   f"<td>{time}</td><td>{note}</td></tr>")
    return "\n".join(out)


def area_rows():
    out = []
    for n, nm, a in AREAS:
        out.append(f"<tr><td>{n}</td><td>{nm}</td><td class='num'>{pl(a, 1)}</td></tr>")
    out.append(f"<tr class='sum'><td></td><td>Razem (orientacyjnie)</td><td class='num'>{pl(TOTAL, 1)}</td></tr>")
    return "\n".join(out)


def sheet(code, title, scale, body, note=""):
    return f"""
<figure class="sheet" id="{code.lower()}">
  <div class="sheet-draw">{body}</div>
  <figcaption class="tb">
    <span class="tb-code">{code}</span>
    <span class="tb-title">{title}</span>
    <span class="tb-meta">{scale}</span>
    <span class="tb-meta">Dom Klocek</span>
  </figcaption>
  {f'<p class="sheet-note">{note}</p>' if note else ''}
</figure>"""


CSS = r"""
/* Układ: arkusz rysunkowy – wąska kolumna tekstu, szerokie arkusze rysunków z tabelką. */
:root{
  --paper:#F2F4F1; --open:#EEF3F8; --sheet:#FFFFFF; --ink:#1C2024; --ink-2:#4B535A; --ink-3:#8C949A; --rule:#D3D8D4;
  --accent:#1E58B4; --accent-soft:#E3EBF8; --mark:#E2A72E;
  --eps:#F2E6A8; --conc:#7D868D; --part:#C3C8CB; --floor:#FFFFFF; --void:#E8ECEF; --glass-plan:#CFE0EE;
  --sky:#DCE7EF; --grass:#BDCDA8; --wall:#FBFBF8; --wall-sh:#E4E6E1; --wood:#B98252; --wood-line:#9A673C;
  --roof:#3B4148; --roof-hi:#4B525A; --glass:#8DB0CA; --frame:#2A2E33; --deck:#C9A67C; --tree:#77955F; --tree-hi:#93AF79;
  --shadow:rgba(40,52,40,.18); --person:#2A2E33;
  --display:"Barlow Condensed","Arial Narrow",sans-serif;
  --body:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",Menlo,monospace;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#111417; --open:#1A2129; --sheet:#171B1F; --ink:#E3E6E2; --ink-2:#AAB2B8; --ink-3:#6F7880; --rule:#2B3136;
    --accent:#86AEF2; --accent-soft:#1D2A3F; --mark:#E8B54A;
    --eps:#5E5530; --conc:#5B646B; --part:#3C4349; --floor:#171B1F; --void:#20262B; --glass-plan:#2C4256;
    --sky:#1A2531; --grass:#29372A; --wall:#C7CBC6; --wall-sh:#A2A7A2; --wood:#8E5F38; --wood-line:#6E4728;
    --roof:#2A2F35; --roof-hi:#363C43; --glass:#E9C46F; --frame:#14171A; --deck:#6E5A43; --tree:#3B5235; --tree-hi:#4B6544;
    --shadow:rgba(0,0,0,.35); --person:#0E1012; color-scheme:dark;
  }
}
:root[data-theme="dark"]{
    --paper:#111417; --open:#1A2129; --sheet:#171B1F; --ink:#E3E6E2; --ink-2:#AAB2B8; --ink-3:#6F7880; --rule:#2B3136;
    --accent:#86AEF2; --accent-soft:#1D2A3F; --mark:#E8B54A;
    --eps:#5E5530; --conc:#5B646B; --part:#3C4349; --floor:#171B1F; --void:#20262B; --glass-plan:#2C4256;
    --sky:#1A2531; --grass:#29372A; --wall:#C7CBC6; --wall-sh:#A2A7A2; --wood:#8E5F38; --wood-line:#6E4728;
    --roof:#2A2F35; --roof-hi:#363C43; --glass:#E9C46F; --frame:#14171A; --deck:#6E5A43; --tree:#3B5235; --tree-hi:#4B6544;
    --shadow:rgba(0,0,0,.35); --person:#0E1012; color-scheme:dark;
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font:15px/1.6 var(--body);}
.wrap{max-width:1120px;margin:0 auto;padding-inline:20px;padding-block:28px 64px}
.text{max-width:68ch}
a{color:var(--accent)}
a:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
h1,h2,h3{font-family:var(--display);font-weight:700;letter-spacing:.01em;line-height:1.05;text-wrap:balance;margin:0}
h1{font-size:clamp(44px,8vw,84px);text-transform:uppercase}
h2{font-size:clamp(28px,4vw,40px);text-transform:uppercase;margin-bottom:10px}
h3{font-size:22px;margin-bottom:6px}
p{margin:0 0 12px}
.eyebrow{font:500 12px/1.3 var(--mono);text-transform:uppercase;letter-spacing:.12em;color:var(--ink-2);margin-bottom:12px}
.lede{font-size:18px;color:var(--ink-2);max-width:62ch;margin-top:14px}
nav.toc{display:flex;flex-wrap:wrap;gap:6px 18px;margin:22px 0 0;padding:10px 0;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);font:500 13px var(--mono)}
nav.toc a{text-decoration:none;color:var(--ink)}
nav.toc a:hover{color:var(--accent)}
section{margin-top:56px}

/* tabelka parametrów */
.spec{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));border:1.5px solid var(--ink);margin-top:26px;background:var(--sheet)}
.spec div{padding:10px 14px;border-right:1px solid var(--rule);border-bottom:1px solid var(--rule);min-width:0}
.spec dt{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.08em;color:var(--ink-2)}
.spec dd{margin:2px 0 0;font:700 28px/1.1 var(--display);font-variant-numeric:tabular-nums}
.spec dd small{font:500 13px var(--body);color:var(--ink-2)}

.hero-fig{margin:26px 0 0;background:var(--sheet);border:1px solid var(--rule)}
.hero-fig figcaption{padding:10px 16px;font-size:13px;color:var(--ink-2);border-top:1px solid var(--rule)}
svg{display:block;width:100%;height:auto}
.illus text{font-family:var(--body)}

/* arkusze rysunków */
.sheets{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,520px),1fr));gap:22px;margin-top:18px}
.sheet{margin:0;background:var(--sheet);border:1.5px solid var(--ink);display:flex;flex-direction:column;min-width:0}
.sheet.wide{grid-column:1/-1}
.sheet-draw{overflow-x:auto;padding:8px}
.sheet-draw svg{min-width:460px}
.tb{display:grid;grid-template-columns:auto 1fr auto auto;border-top:1.5px solid var(--ink);font:500 12px var(--mono)}
.tb>span{padding:7px 10px;border-right:1px solid var(--ink);display:flex;align-items:center;min-width:0}
.tb>span:last-child{border-right:0}
.tb-code{font:700 16px var(--display);background:var(--ink);color:var(--sheet)}
.tb-title{font:600 15px var(--display);text-transform:uppercase;letter-spacing:.04em}
.tb-meta{color:var(--ink-2)}
@media (max-width:560px){.tb{grid-template-columns:auto 1fr}.tb-meta{border-top:1px solid var(--ink)}}
.sheet-note{font-size:13px;color:var(--ink-2);padding:8px 12px 12px;margin:0;border-top:1px solid var(--rule)}
.legend{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:13px;color:var(--ink-2);margin-top:10px}
.legend i{display:inline-block;width:22px;height:10px;vertical-align:-1px;margin-right:6px;border:1px solid var(--ink)}

/* style rysunków */
.d-eps{fill:var(--eps)} .d-conc{fill:var(--conc)} .d-concx{fill:url(#hatch-conc)} .d-part{fill:var(--part)}
.d-floor{fill:var(--floor)} .d-open{fill:var(--open)}
.d-ridge{stroke:var(--accent);stroke-width:.8;stroke-dasharray:14 4 2 4;opacity:.8}
.d-beyond{fill:none;stroke:var(--ink-3);stroke-width:.8}
.d-glassb{fill:var(--glass-plan);stroke:var(--ink-2);stroke-width:.7;opacity:.85}
.d-mull{fill:var(--ink-2)}
.d-tie{stroke:var(--ink);stroke-width:1.6}
.x-hole{fill:var(--glass);opacity:.75;stroke:var(--ink);stroke-width:.6}
.e-pv{fill:#1F2E45;stroke:var(--frame);stroke-width:.8} .e-pvline{stroke:#46607F;stroke-width:.8} .d-void{fill:var(--void)}
.d-cut{stroke:var(--ink);stroke-width:1.3;fill:none;stroke-linecap:square}
.d-line{stroke:var(--ink);stroke-width:1.1;fill:none}
.d-thin{stroke:var(--ink);stroke-width:.6;fill:none}
.d-win{fill:var(--glass-plan);stroke:var(--ink);stroke-width:.6}
.d-leaf{stroke:var(--ink);stroke-width:1.4}
.d-swing{stroke:var(--ink-2);stroke-width:.6;fill:none;stroke-dasharray:2 2}
.d-furn{stroke:var(--ink-3);stroke-width:.7;fill:none}
.d-stair,.d-stair-up{fill:var(--floor);stroke:var(--ink);stroke-width:.8}
.d-stair-up{fill:none;stroke:var(--ink-2)}
.d-tread{stroke:var(--ink-2);stroke-width:.6}
.d-walkline{stroke:var(--ink);stroke-width:.8;fill:none}
.d-rail{stroke:var(--ink);stroke-width:2}
.d-hline{stroke:var(--ink-3);stroke-width:.7;stroke-dasharray:6 3 1 3}
.d-roofwin{fill:none;stroke:var(--ink-2);stroke-width:.8;stroke-dasharray:4 2}
.d-dim{stroke:var(--accent);stroke-width:.7}
.d-dimext{stroke:var(--accent);stroke-width:.4;opacity:.7}
.d-dimtick{stroke:var(--accent);stroke-width:1.3}
.d-dimt{fill:var(--accent);font:500 10px var(--mono)}
.d-room{fill:var(--ink);font:600 12.5px var(--display);letter-spacing:.02em}
.d-area{fill:var(--ink-2);font:400 9.5px var(--mono)}
.d-note{fill:var(--ink-2);font:italic 400 9.5px var(--body)}
.d-label{fill:var(--ink);font:700 14px var(--display)}
.d-solid{fill:var(--ink)} .d-hollow{fill:var(--sheet);stroke:var(--ink);stroke-width:.8}
.d-section{stroke:var(--ink);stroke-width:2.4;stroke-dasharray:10 3 2 3}
.d-leader{stroke:var(--ink-2);stroke-width:.6;fill:none}
.d-ground{fill:url(#hatch-ground)} .d-groundl{fill:url(#hatch-ground);opacity:.6}
.d-gravel{fill:url(#dots-gravel)}
.d-screed{fill:var(--part)}
.d-roofcut{fill:url(#hatch-wool)}
.d-ceil{fill:var(--part);stroke:var(--ink);stroke-width:.6}
.d-outline{fill:none;stroke:var(--ink);stroke-width:1.3}
#arrow path{fill:var(--ink)}
.p-line{stroke:var(--ink-3);stroke-width:.7}
.p-fill{fill:var(--ink-3)}
.p-ground{stroke:var(--ink-3);stroke-width:.7}
.p-dot{fill:var(--ink-3)}
.p-wool{stroke:var(--ink-3);stroke-width:.6;fill:none}

.e-wall{fill:var(--wall);stroke:none} .e-plinth{fill:var(--conc)}
.e-roof{fill:var(--roof)} .e-seam{stroke:var(--roof-hi);stroke-width:1}
.e-fascia{fill:var(--frame)}
.e-wood{fill:var(--wood)} .e-board{stroke:var(--wood-line);stroke-width:.6}
.e-roofedge{fill:var(--frame)}
.e-frame{fill:var(--frame)} .e-glass{fill:var(--glass)} .e-door{fill:var(--wood-line)}

.i-sky{fill:var(--sky)} .i-grass{fill:var(--grass)} .i-shadow{fill:var(--shadow)}
.i-wall{fill:var(--wall);stroke:var(--frame);stroke-width:.6}
.i-wood{fill:var(--wood);stroke:var(--frame);stroke-width:.6} .i-board{stroke:var(--wood-line);stroke-width:.7}
.i-plinth{fill:var(--conc)}
.i-roof{fill:var(--roof)} .i-seam{stroke:var(--roof-hi);stroke-width:1.1}
.i-roofedge{fill:var(--frame)} .i-ridge{stroke:var(--frame);stroke-width:2}
.i-frame{fill:var(--frame)} .i-glass{fill:var(--glass)}
.i-pv{fill:#1F2E45;stroke:var(--frame);stroke-width:.8} .i-pvline{stroke:#46607F;stroke-width:.8}
.i-deck{fill:var(--deck)} .i-deckline{stroke:var(--wood-line);stroke-width:.5;opacity:.7} .i-deckedge{fill:var(--wood-line)}
.i-tree{fill:var(--tree)} .i-tree-hi{fill:var(--tree-hi)} .i-trunk{stroke:var(--wood-line);stroke-width:4}
.i-person{fill:var(--person)}

.x-slab{fill:var(--conc)} .x-slab-side{fill:var(--conc);opacity:.85} .x-slab-top{fill:var(--part)}
.x-xps{fill:#9FC3DE}
.x-floor{fill:var(--part)}
.x-eps-front{fill:var(--eps);stroke:var(--ink);stroke-width:.7}
.x-eps-side{fill:var(--eps);stroke:var(--ink);stroke-width:.7;filter:brightness(.9)}
.x-eps-in{fill:var(--eps);filter:brightness(.82)} .x-eps-in2{fill:var(--eps);filter:brightness(.72)}
.x-eps-top{fill:var(--eps);stroke:var(--ink);stroke-width:.5} .x-core{fill:var(--conc)}
.x-joint{stroke:var(--ink);stroke-width:.45;opacity:.55}
.x-edge{stroke:var(--ink);stroke-width:.8}
.x-roof{fill:var(--roof)} .x-seam{stroke:var(--roof-hi);stroke-width:1} .x-roof-edge{fill:var(--frame)}
.x-arrow{stroke:var(--ink);stroke-width:1.2;stroke-dasharray:5 3;fill:none}
.x-badge{fill:var(--ink)} .x-badge-t{fill:var(--sheet);font:700 13px var(--display)}
.x-lt{fill:var(--ink);font:600 15px var(--display);text-transform:uppercase;letter-spacing:.03em}
.x-ls{fill:var(--ink-2);font:400 12px var(--body)}
.b-front{fill:var(--eps);stroke:var(--ink);stroke-width:.8}
.b-side{fill:var(--eps);stroke:var(--ink);stroke-width:.8;filter:brightness(.88)}
.b-top{fill:var(--eps);stroke:var(--ink);stroke-width:.6;filter:brightness(1.04)}
.b-core{fill:var(--conc);stroke:var(--ink);stroke-width:.6}
.b-tie{stroke:var(--mark);stroke-width:2.2}
.b-stud{fill:var(--eps);stroke:var(--ink);stroke-width:.5;filter:brightness(.9)}
.b-studtop{fill:var(--eps);stroke:var(--ink);stroke-width:.5}
.w-plaster{fill:var(--part)} .w-eps{fill:var(--eps);stroke:var(--ink);stroke-width:.6}
.w-eps2{fill:var(--eps);stroke:var(--ink);stroke-width:.6;filter:brightness(.93)}
.w-conc{fill:url(#hatch-conc);stroke:var(--ink);stroke-width:.8} .w-render{fill:var(--ink-2)}
.w-rebar{fill:var(--ink)} .w-tie{fill:var(--mark)}

/* tabele */
.tablewrap{overflow-x:auto;margin-top:16px;border:1px solid var(--rule);background:var(--sheet)}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:10px 12px;border-bottom:1px solid var(--rule)}
thead th{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.08em;color:var(--ink-2);background:var(--paper);white-space:nowrap}
tbody th{font:600 17px/1.15 var(--display);min-width:170px}
.tech td:nth-child(2){min-width:240px} .tech td:last-child{min-width:240px}
.tech td:nth-child(6){white-space:nowrap;font:13px var(--mono)}
tr.pick{background:var(--accent-soft)}
.tag{display:inline-block;margin-left:8px;padding:1px 7px;font:500 10px var(--mono);text-transform:uppercase;letter-spacing:.08em;border:1px solid var(--accent);color:var(--accent);vertical-align:2px}
.dots{display:inline-flex;gap:3px;white-space:nowrap}
.dots i{width:9px;height:9px;border:1.2px solid var(--ink);border-radius:50%;display:inline-block}
.dots i.on{background:var(--ink)}
.num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}
tr.sub td{font-weight:600;background:var(--paper)}
tr.sum td{font-weight:700;border-top:1.5px solid var(--ink)}
.compact th,.compact td{padding:6px 10px}

.two{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr));gap:22px;margin-top:18px;align-items:start}
.panel{background:var(--sheet);border:1px solid var(--rule);padding:16px 18px;min-width:0}
.callout{border-left:4px solid var(--accent);background:var(--sheet);padding:14px 18px;margin-top:18px}
.callout h3{margin-bottom:4px}
.pros{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:18px;margin-top:14px}
.pros ul{margin:6px 0 0;padding-left:18px}
.pros li{margin-bottom:5px}
.big-u{font:700 46px/1 var(--display);color:var(--accent)}

ol.steps{list-style:none;counter-reset:s;padding:0;margin:18px 0 0;display:grid;gap:0}
ol.steps li{counter-increment:s;display:grid;grid-template-columns:52px 1fr auto;gap:4px 14px;padding:14px 0;border-top:1px solid var(--rule)}
ol.steps li::before{content:counter(s,decimal-leading-zero);font:700 26px/1 var(--display);color:var(--accent)}
ol.steps h3{font-size:20px}
ol.steps p{margin:0;color:var(--ink-2);grid-column:2/3}
ol.steps .t{font:500 12px var(--mono);color:var(--ink-2);white-space:nowrap;grid-column:3;grid-row:1}
@media (max-width:560px){ol.steps li{grid-template-columns:40px 1fr}ol.steps .t{grid-column:2;grid-row:auto}}
.foot{margin-top:56px;padding-top:16px;border-top:1.5px solid var(--ink);font-size:13px;color:var(--ink-2)}
.foot ul{padding-left:18px}
"""

DEFS = """<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<pattern id="hatch-conc" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <rect width="6" height="6" style="fill:var(--conc)"/><line x1="0" y1="0" x2="0" y2="6" style="stroke:var(--sheet);stroke-width:.8;opacity:.55"/></pattern>
<pattern id="hatch-ground" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
  <line x1="0" y1="0" x2="0" y2="9" class="p-ground"/></pattern>
<pattern id="dots-gravel" width="7" height="7" patternUnits="userSpaceOnUse">
  <circle cx="2" cy="2" r="1" class="p-dot"/><circle cx="5.5" cy="5" r=".8" class="p-dot"/></pattern>
<pattern id="hatch-wool" width="10" height="6" patternUnits="userSpaceOnUse">
  <rect width="10" height="6" style="fill:var(--sheet)"/><path d="M0,3 C2.5,0 2.5,6 5,3 S7.5,0 10,3" class="p-wool"/></pattern>
<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
  <path d="M0,0 L10,5 L0,10 z"/></marker>
</defs></svg>"""


def build():
    u_rows, u_val = u_table()
    height_total = RIDGE - TERRAIN
    html = f"""<title>Dom Klocek</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap">
<style>{CSS}</style>
{DEFS}
<div class="wrap">
<header>
  <div class="eyebrow">Koncepcja poglądowa · dom parterowy ok. 150 m² · technologia ICF</div>
  <h1>Dom Klocek</h1>
  <p class="lede">Parterowa nowoczesna stodoła dla rodziny 2+2, stawiana z lekkich bloczków styropianowych, które składa się na sucho jak klocki i zalewa betonem. Salon z kuchnią i sypialnia mają sufit otwarty aż do kalenicy i duże przeszklenia od strony ogrodu.</p>
  <dl class="spec">
    <div><dt>Pow. użytkowa</dt><dd>ok. 150 <small>m²</small></dd></div>
    <div><dt>Zabudowa</dt><dd>ok. 170 <small>m²</small></dd></div>
    <div><dt>Pokoje</dt><dd>3 <small>sypialnie + salon</small></dd></div>
    <div><dt>Bryła</dt><dd>ok. 19 × 9 <small>m</small></dd></div>
    <div><dt>Dach</dt><dd>40° <small>wys. ok. {pl(height_total, 1)} m</small></dd></div>
    <div><dt>Ściana U</dt><dd>{pl(u_val, 2)} <small>W/m²K</small></dd></div>
  </dl>
  <nav class="toc" aria-label="Spis treści">
    <a href="#technologie">Technologie</a><a href="#icf">Jak działa ICF</a><a href="#przeszklenia">Przeszklenia</a>
    <a href="#rysunki">Rysunki</a><a href="#powierzchnie">Pomieszczenia</a><a href="#budowa">Kolejność budowy</a>
  </nav>
</header>

<figure class="hero-fig">
  {house_illustration()}
  <figcaption>Widok od ogrodu (południowy zachód). Po lewej przeszklony szczyt salonu, po prawej sypialnia z oknem tarasowym. Szczyt w desce, ściany w białym tynku, dach z blachy na rąbek bez okapów, fotowoltaika na połaci południowej.</figcaption>
</figure>

<section id="technologie">
  <h2>Z czego zbudować – technologie „klockowe”</h2>
  <div class="text">
    <p>Filmy, w których dom rośnie z klocków w kilka dni, pokazują zwykle jedną z ośmiu technologii poniżej. Oceniłem, jak bardzo każda przypomina składanie klocków, ile da się zrobić samemu i jak łatwo kupić ją w Polsce. Oceny są orientacyjne, czasy dotyczą stanu surowego, bez wykończenia.</p>
  </div>
  <div class="tablewrap">
  <table class="tech">
    <thead><tr><th>Technologia</th><th>Na czym polega</th><th>Jak klocki</th><th>Samemu</th><th>Dostępność w PL</th><th>Stan surowy</th><th>Plusy i minusy</th></tr></thead>
    <tbody>
{tech_rows()}
    </tbody>
  </table>
  </div>
  <div class="callout">
    <h3>Propozycja: ICF na izolowanej płycie fundamentowej</h3>
    <p class="text">ICF najlepiej łączy efekt „klocków” z tym, co da się kupić, zaprojektować i odebrać w Polsce. Bloczki są lekkie, łączą się na zamki, a po zalaniu powstaje żelbetowa ściana, która od razu jest ocieplona. Żelbet dobrze znosi też duże otwory: nad przeszkleniami robi się nadproża i słupy w tych samych bloczkach.</p>
  </div>
  <div class="pros">
    <div class="panel"><h3>Dlaczego ICF</h3><ul>
      <li>Jedna operacja daje konstrukcję i ocieplenie, bez osobnego docieplania.</li>
      <li>Bloczki ważą kilka kilogramów, więc ściany parterowego domu postawi 3–4 osoby bez dźwigu.</li>
      <li>Beton w środku zapewnia akustykę, masę cieplną (latem mniej się nagrzewa) i odporność na wiatr.</li>
      <li>Ściana o U ≈ {pl(u_val, 2)} W/m²K spełnia wymóg 0,20 z zapasem.</li>
    </ul></div>
    <div class="panel"><h3>Na co uważać</h3><ul>
      <li>Betonowanie warstwami po ok. 1 m i podpory pionujące, bo inaczej szalunek może się rozeprzeć.</li>
      <li>Ściana jest szczelna, więc wentylacja mechaniczna z odzyskiem ciepła jest konieczna.</li>
      <li>Styropian po obu stronach trzeba osłonić tynkiem lub płytą (ochrona ppoż. i UV).</li>
      <li>Późniejsze przebicia w betonie są trudniejsze, dlatego instalacje trzeba zaplanować przed zalaniem.</li>
    </ul></div>
  </div>
  <p class="text" style="margin-top:14px">Jeśli wolisz budowę zupełnie „na sucho”, tę samą bryłę da się zrobić z drewnianych bloczków izolowanych albo z paneli SIP. Prostokąt z dwuspadowym dachem pasuje do każdego z tych systemów.</p>
</section>

<section id="icf">
  <h2>Jak działa ściana z klocków ICF</h2>
  <div class="two">
    <figure class="panel" style="margin:0">
      {block_figure()}
      <figcaption class="legend" style="margin-top:6px">Kolejne warstwy kładzie się z przesunięciem o pół bloczka. Wypustki na górze wchodzą w gniazda warstwy wyżej, a żółte łączniki trzymają obie ścianki styropianu w stałym odstępie.</figcaption>
    </figure>
    <div class="panel">
      <h3>Przekrój ściany zewnętrznej</h3>
      {wall_detail()}
      <div class="tablewrap" style="margin-top:10px">
        <table class="compact">
          <thead><tr><th>Warstwa</th><th class="num">d [cm]</th><th class="num">λ [W/mK]</th><th class="num">R [m²K/W]</th></tr></thead>
          <tbody>{u_rows}</tbody>
        </table>
      </div>
      <p style="margin-top:12px"><span class="big-u">U = {pl(u_val, 3)}</span> W/m²K</p>
      <p class="text" style="font-size:13px;color:var(--ink-2)">Wynik bez mostków od łączników i ościeży. Realnie wyjdzie ok. 0,16 W/m²K, czyli nadal poniżej wymaganego 0,20 W/m²K (WT 2021).</p>
    </div>
  </div>
</section>

<section id="przeszklenia">
  <h2>Duże przeszklenia w salonie i sypialni</h2>
  <div class="text"><p>Obie strefy dzienne mają sufit otwarty do kalenicy, więc szkło może sięgać wysoko. Salon dostaje cały przeszklony szczyt na zachód i okno tarasowe na południe, a sypialnia okno tarasowe na południe i wysokie okno w szczycie wschodnim na poranne słońce.</p></div>
  <div class="pros">
    <div class="panel"><h3>Salon z kuchnią</h3><ul>
      <li>Szczyt zachodni: okno przesuwne HS ok. 5,5 × 2,6 m i nad nim stałe przeszklenie w trójkącie, prawie do kalenicy.</li>
      <li>Ściana południowa: drugie okno HS ok. 5 × 2,6 m z wyjściem na taras.</li>
      <li>Kuchnia: szerokie okno nad blatem od północy, czyli równe światło do pracy.</li>
    </ul></div>
    <div class="panel"><h3>Sypialnia</h3><ul>
      <li>Okno HS ok. 3,4 × 2,6 m na prywatny taras od południa.</li>
      <li>Wysokie okno w szczycie wschodnim (ok. 1,8 × 5,6 m) pod skosem dachu.</li>
      <li>Garderoba i łazienka od północy, więc łóżko stoi z dala od okien.</li>
    </ul></div>
    <div class="panel"><h3>Żeby nie było za gorąco ani za zimno</h3><ul>
      <li>Rolety lub żaluzje zewnętrzne na oknach od zachodu i południa. Rolety wewnętrzne nie zatrzymują ciepła.</li>
      <li>Pakiet trzyszybowy z powłoką przeciwsłoneczną na szczycie zachodnim.</li>
      <li>Ciepły montaż okien w warstwie styropianu oraz słupy i nadproża żelbetowe w ICF według obliczeń konstruktora.</li>
    </ul></div>
  </div>
</section>

<section id="rysunki">
  <h2>Rysunki poglądowe</h2>
  <div class="text"><p>Rysunki pokazują układ i proporcje, a wymiary są orientacyjne. Dokładne wymiary ustali architekt w projekcie budowlanym, po dopasowaniu do działki. Ściany zewnętrzne narysowano warstwami: żółty to styropian bloczka, szary to rdzeń betonowy.</p></div>
  <div class="legend">
    <span><i style="background:var(--eps)"></i>EPS (bloczek ICF)</span>
    <span><i style="background:var(--conc)"></i>beton</span>
    <span><i style="background:var(--part)"></i>ścianka działowa</span>
    <span><i style="background:var(--glass-plan)"></i>okno</span>
    <span><i style="background:var(--open)"></i>sufit otwarty do kalenicy</span>
  </div>
  <div class="sheets">
    {sheet("A-01", "Rzut parteru", "poglądowy", plan_parter(),
           "Strefa dzienna od zachodu, sypialnie od południa (ogród), łazienki, pralnia i garderoba od północy. Z holu wchodzi się prosto do salonu albo korytarzem do pokoi. Pralnia mieści zasobnik i jednostkę pompy ciepła.").replace('class="sheet"', 'class="sheet wide"')}
    {sheet("A-02", "Przekrój A–A przez salon", "poglądowy", section_aa(),
           "Salon ma sufit otwarty do kalenicy, ok. 6,9 m w najwyższym miejscu. Stalowe ściągi zamiast drewnianych jętek nie zasłaniają przeszklonego szczytu.")}
    {sheet("A-03", "Elewacja zachodnia – szklany szczyt", "poglądowa", elevation("W"))}
    {sheet("A-04", "Elewacja południowa – ogród", "poglądowa", elevation("S")).replace('class="sheet"', 'class="sheet wide"')}
    {sheet("A-05", "Elewacja północna – wejście", "poglądowa", elevation("N")).replace('class="sheet"', 'class="sheet wide"')}
    {sheet("A-06", "Elewacja wschodnia – sypialnia", "poglądowa", elevation("E"))}
    {sheet("A-07", "Kolejność montażu", "aksonometria", assembly(),
           "Stan surowy powstaje z czterech „warstw klocków”. Szczyty to te same bloczki ICF docięte pod kąt 40°, a w szczycie zachodnim zostaje otwór na przeszklenie.").replace('class="sheet"', 'class="sheet wide"')}
  </div>
</section>

<section id="powierzchnie">
  <h2>Pomieszczenia</h2>
  <div class="two">
    <div class="tablewrap" style="margin-top:0">
      <table>
        <thead><tr><th>Nr</th><th>Pomieszczenie</th><th class="num">ok. m²</th></tr></thead>
        <tbody>{area_rows()}</tbody>
      </table>
    </div>
    <div class="panel">
      <h3>Wykończenie i instalacje</h3>
      <p><b>Fundament:</b> izolowana płyta fundamentowa 25 cm na XPS 20 cm. Ogrzewanie podłogowe można zatopić bezpośrednio w płycie.</p>
      <p><b>Ściany:</b> bloczki ICF 35 cm. Na zewnątrz tynk silikonowy, szczyty w desce modrzewiowej lub termowanej na ruszcie.</p>
      <p><b>Sufity:</b> w pokojach, łazienkach i holu płaski sufit na wysokości ok. 2,8 m. Salon i sypialnia otwarte do kalenicy.</p>
      <p><b>Dach:</b> więźba krokwiowa ze stalowymi ściągami i wełną 25 cm albo płyty SIP, pokrycie blachą na rąbek stojący bez okapów.</p>
      <p><b>Ogrzewanie:</b> pompa ciepła powietrze–woda z podłogówką, wentylacja mechaniczna z rekuperacją, ok. 6–8 kWp fotowoltaiki na połaci południowej.</p>
    </div>
  </div>
</section>

<section id="budowa">
  <h2>Kolejność budowy</h2>
  <ol class="steps">
    <li><h3>Formalności i projekt budowlany</h3><span class="t">2–4 mies.</span>
      <p>Wypis z MPZP albo decyzja o warunkach zabudowy, mapa do celów projektowych, badanie gruntu. Architekt i konstruktor z uprawnieniami robią projekt budowlany na podstawie tej koncepcji. Dom jednorodzinny, którego obszar oddziaływania mieści się na działce, można budować na zgłoszenie z projektem. Potrzebny jest wtedy kierownik budowy i dziennik budowy.</p></li>
    <li><h3>Izolowana płyta fundamentowa</h3><span class="t">2–3 tyg.</span>
      <p>Zagęszczona podsypka, kanalizacja podposadzkowa i przepusty, XPS 20 cm, zbrojenie, beton. Pierwsza warstwa bloczków wymaga idealnie poziomej płyty, więc ten etap nie może być „mniej więcej”.</p></li>
    <li><h3>Ściany z bloczków ICF</h3><span class="t">2–3 tyg.</span>
      <p>Pierwsza warstwa na poziomicy, kolejne na sucho z przesunięciem o pół bloczka. Zbrojenie według konstruktora, słupy przy dużych oknach, ościeża, rury elektryczne, podpory pionujące. Betonowanie pompą warstwami po ok. 1 m.</p></li>
    <li><h3>Szczyty i wieniec</h3><span class="t">1 tyg.</span>
      <p>Bloczki na szczytach docinane pod kąt 40° piłą albo nożem do styropianu. W szczycie zachodnim zostaje otwór na przeszklenie z żelbetową ramą. Wieniec skośny pod krokwie.</p></li>
    <li><h3>Dach i okna – stan surowy zamknięty</h3><span class="t">3–4 tyg.</span>
      <p>Więźba albo płyty SIP, membrana, blacha na rąbek. Okna i drzwi w ciepłym montażu. Duże okna HS montuje zwykle ekipa producenta.</p></li>
    <li><h3>Instalacje i wykończenie</h3><span class="t">3–5 mies.</span>
      <p>Rekuperacja, pompa ciepła, elektryka, fotowoltaika. Wewnątrz tynk gipsowy na siatce albo płyty g-k na kleju, na zewnątrz tynk i deska elewacyjna.</p></li>
  </ol>
  <div class="callout">
    <h3>Czym jest ta strona, a czym nie</h3>
    <p class="text">To przykładowa koncepcja: układ, technologia i wygląd, z którymi można pójść do architekta i producenta bloczków. Nie jest to projekt budowlany. Do budowy potrzebny jest projekt wykonany przez osoby z uprawnieniami: z obliczeniami konstrukcji (zwłaszcza nad dużymi przeszkleniami), charakterystyką energetyczną i dopasowaniem do działki, gruntu i zapisów planu miejscowego (kąt dachu, wysokość, kolor pokrycia).</p>
  </div>
</section>

<footer class="foot">
  <p>Źródła i dalsza lektura:</p>
  <ul>
    <li><a href="https://muratordom.pl/budowa/inne-technologie-budowlane/z-jakiego-materialu-warto-zbudowac-dom-energooszczedny-w-2023-roku-aa-wEzh-oohr-6Ump.html">muratordom.pl – technologia ICF (Izodom)</a> · <a href="https://materialdistrict.com/material/izodom-icf-solutions/">MaterialDistrict – Izodom ICF</a></li>
    <li><a href="https://constructiondigital.com/built-environment/gablok-revolutionising-housebuilding">Construction Digital – Gablok, drewniane bloczki izolowane</a></li>
  </ul>
  <p>Rysunki wygenerowano skryptem <code>generuj.py</code> z jednego zestawu wymiarów.</p>
</footer>
</div>
"""
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    print(f"zapisano {OUT}")
    print(f"powierzchnia {TOTAL:.2f} m², zabudowa {L * B:.1f} m²")
    print(f"okap {EAVE:.3f}, kalenica {RIDGE:.3f}, wnętrze pod kalenicą {IN_APEX:.3f}, U={u_val:.3f}")


if __name__ == "__main__":
    build()
