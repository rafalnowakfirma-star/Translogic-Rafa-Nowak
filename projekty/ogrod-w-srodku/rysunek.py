"""Narzędzia rysunkowe: rzuty SVG (ściany, otwory, meble, ogród), przekroje i witraże.

Współrzędne w metrach: x na wschód, y na południe (północ u góry rysunku).
"""
import math
import random


def pl(v, d=1):
    return f"{v:.{d}f}".replace(".", ",").replace("-", "−")


def f(v):
    return f"{v:.1f}"


def shoelace(ps):
    a = 0.0
    for (x1, y1), (x2, y2) in zip(ps, ps[1:] + ps[:1]):
        a += x1 * y2 - x2 * y1
    return abs(a) / 2


def centroid(ps):
    return (sum(p[0] for p in ps) / len(ps), sum(p[1] for p in ps) / len(ps))


def rect_pts(x1, y1, x2, y2):
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


# ------------------------------------------------------------------ rzut
class Plan:
    LAYERS = ("ground", "floor", "garden", "furn", "walls", "open", "sym", "text")

    def __init__(self, label, xmin, ymin, xmax, ymax, s=38, pad=48):
        self.s, self.x0, self.y0, self.pad = s, xmin, ymin, pad
        self.W = (xmax - xmin) * s + 2 * pad
        self.H = (ymax - ymin) * s + 2 * pad
        self.label = label
        self.L = {k: [] for k in self.LAYERS}
        self.area = 0.0

    def P(self, x, y):
        return (self.pad + (x - self.x0) * self.s, self.pad + (y - self.y0) * self.s)

    def _pts(self, ps):
        return " ".join(f"{f(a)},{f(b)}" for a, b in (self.P(*q) for q in ps))

    def poly(self, layer, ps, cls, extra=""):
        self.L[layer].append(f'<polygon points="{self._pts(ps)}" class="{cls}" {extra}/>')

    def pline(self, layer, ps, cls, w=None, closed=False):
        d = "M" + " L".join(f"{f(a)},{f(b)}" for a, b in (self.P(*q) for q in ps)) + (" Z" if closed else "")
        st = f' style="stroke-width:{w * self.s:.1f}px"' if w else ""
        self.L[layer].append(f'<path d="{d}" class="{cls}"{st}/>')

    def line(self, layer, a, b, cls):
        (x1, y1), (x2, y2) = self.P(*a), self.P(*b)
        self.L[layer].append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" class="{cls}"/>')

    def circle(self, layer, c, r, cls):
        x, y = self.P(*c)
        self.L[layer].append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r * self.s)}" class="{cls}"/>')

    def ellipse(self, layer, c, rx, ry, cls, rot=0):
        x, y = self.P(*c)
        tr = f' transform="rotate({rot} {f(x)} {f(y)})"' if rot else ""
        self.L[layer].append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(rx * self.s)}" ry="{f(ry * self.s)}" class="{cls}"{tr}/>')

    def text(self, x, y, s, cls, anchor="middle", dy=0, rot=None):
        a, b = self.P(x, y)
        b += dy
        tr = f' transform="rotate({rot} {f(a)} {f(b)})"' if rot is not None else ""
        self.L["text"].append(f'<text x="{f(a)}" y="{f(b)}" text-anchor="{anchor}" class="{cls}"{tr}>{s}</text>')

    def item(self, cx, cy, rot, shapes, layer="furn"):
        """Element w układzie lokalnym (metry, środek w 0,0), obrócony o rot stopni."""
        x, y = self.P(cx, cy)
        s = self.s
        out = [f'<g transform="translate({f(x)},{f(y)}) rotate({rot:.1f})">']
        for sh in shapes:
            k = sh[0]
            cls = sh[-1] if isinstance(sh[-1], str) and sh[-1].startswith(("fu", "g-", "o-")) else "fu"
            if k == "r":
                _, a, b, w, h = sh[:5]
                rx = sh[5] if len(sh) > 5 and not isinstance(sh[5], str) else 0
                out.append(f'<rect x="{f(a * s)}" y="{f(b * s)}" width="{f(w * s)}" height="{f(h * s)}" rx="{f(rx * s)}" class="{cls}"/>')
            elif k == "c":
                _, a, b, r = sh[:4]
                out.append(f'<circle cx="{f(a * s)}" cy="{f(b * s)}" r="{f(r * s)}" class="{cls}"/>')
            elif k == "e":
                _, a, b, rx, ry = sh[:5]
                out.append(f'<ellipse cx="{f(a * s)}" cy="{f(b * s)}" rx="{f(rx * s)}" ry="{f(ry * s)}" class="{cls}"/>')
            elif k == "l":
                _, a, b, c, d = sh[:5]
                out.append(f'<line x1="{f(a * s)}" y1="{f(b * s)}" x2="{f(c * s)}" y2="{f(d * s)}" class="{cls}"/>')
        out.append("</g>")
        self.L[layer].append("".join(out))

    def render(self, extra_cls=""):
        body = []
        for k in self.LAYERS:
            if k == "furn":
                body.append('<g class="furn">' + "".join(self.L[k]) + "</g>")
            else:
                body.append("".join(self.L[k]))
        return (f'<svg class="drw {extra_cls}" viewBox="0 0 {self.W:.0f} {self.H:.0f}" role="img" '
                f'aria-label="{self.label}" xmlns="http://www.w3.org/2000/svg">' + "".join(body) + "</svg>")


# ------------------------------------------------------------ ściany i otwory
def wall(p, ps, t, closed=False, cls="w-outer"):
    p.pline("walls", ps, cls, w=t, closed=closed)


def glass(p, ps, closed=False):
    p.pline("walls", ps, "w-glass", w=0.13, closed=closed)
    p.pline("walls", ps, "w-glassline", closed=closed)


def opening(p, A, B, t, kind, swing=1, hinge="A"):
    ax, ay = A
    bx, by = B
    L = math.hypot(bx - ax, by - ay)
    dx, dy = (bx - ax) / L, (by - ay) / L
    nx, ny = -dy, dx
    h = t / 2 + 0.03
    p.poly("open", [(ax - nx * h, ay - ny * h), (bx - nx * h, by - ny * h),
                    (bx + nx * h, by + ny * h), (ax + nx * h, ay + ny * h)], "o-cut")
    if kind != "gap":
        for x, y in (A, B):
            p.line("sym", (x - nx * t / 2, y - ny * t / 2), (x + nx * t / 2, y + ny * t / 2), "o-jamb")
    if kind == "win":
        g = 0.045
        p.poly("sym", [(ax - nx * g, ay - ny * g), (bx - nx * g, by - ny * g),
                       (bx + nx * g, by + ny * g), (ax + nx * g, ay + ny * g)], "o-glass")
    elif kind == "slide":
        m = 0.5
        g = 0.035
        p.line("sym", (ax - nx * g, ay - ny * g), (ax + dx * L * (m + 0.06) - nx * g, ay + dy * L * (m + 0.06) - ny * g), "o-pane")
        p.line("sym", (ax + dx * L * (m - 0.06) + nx * g, ay + dy * L * (m - 0.06) + ny * g), (bx + nx * g, by + ny * g), "o-pane")
    elif kind == "door":
        H, O = (A, B) if hinge == "A" else (B, A)
        tip = (H[0] + nx * swing * L, H[1] + ny * swing * L)
        p.line("sym", H, tip, "o-leaf")
        cr = (tip[0] - H[0]) * (O[1] - H[1]) - (tip[1] - H[1]) * (O[0] - H[0])
        sweep = 1 if cr > 0 else 0
        (x1, y1), (x2, y2) = p.P(*tip), p.P(*O)
        p.L["sym"].append(f'<path d="M{f(x1)},{f(y1)} A{f(L * p.s)},{f(L * p.s)} 0 0 {sweep} {f(x2)},{f(y2)}" class="o-swing"/>')
    elif kind == "moon":
        mx, my = (ax + bx) / 2, (ay + by) / 2
        p.circle("sym", (mx, my), L / 2, "o-moon")


def room(p, ps, mat, name, at=None, area=True, count=True, small=False):
    p.poly("floor", ps, f"f-{mat}")
    a = shoelace(ps)
    if count:
        p.area += a
    cx, cy = at if at else centroid(ps)
    p.text(cx, cy, name, "t-room-s" if small else "t-room", dy=-2)
    if area:
        p.text(cx, cy, f"{pl(a)} m²", "t-area", dy=10)
    return a


def stair_straight(p, x1, y1, x2, y2, direction, n):
    p.poly("sym", rect_pts(x1, y1, x2, y2), "st-box")
    horiz = direction in "EW"
    for i in range(1, n):
        if horiz:
            x = x1 + (x2 - x1) * i / n
            p.line("sym", (x, y1), (x, y2), "st-tread")
        else:
            y = y1 + (y2 - y1) * i / n
            p.line("sym", (x1, y), (x2, y), "st-tread")
    my, mx = (y1 + y2) / 2, (x1 + x2) / 2
    if direction == "E":
        a, b = (x1 + 0.1, my), (x2 - 0.05, my)
    elif direction == "W":
        a, b = (x2 - 0.1, my), (x1 + 0.05, my)
    elif direction == "S":
        a, b = (mx, y1 + 0.1), (mx, y2 - 0.05)
    else:
        a, b = (mx, y2 - 0.1), (mx, y1 + 0.05)
    (ax_, ay_), (bx_, by_) = p.P(*a), p.P(*b)
    p.L["sym"].append(f'<circle cx="{f(ax_)}" cy="{f(ay_)}" r="2.4" class="st-dot"/>'
                      f'<line x1="{f(ax_)}" y1="{f(ay_)}" x2="{f(bx_)}" y2="{f(by_)}" class="st-walk" marker-end="url(#arrow)"/>')


def stair_spiral(p, c, r, a0, sweep, n):
    p.circle("sym", c, r, "st-box")
    for i in range(n + 1):
        a = math.radians(a0 + sweep * i / n)
        p.line("sym", (c[0] + 0.13 * math.cos(a), c[1] + 0.13 * math.sin(a)),
               (c[0] + r * math.cos(a), c[1] + r * math.sin(a)), "st-tread")
    p.circle("sym", c, 0.13, "st-post")
    rr = r * 0.62
    a1, a2 = math.radians(a0 + 6), math.radians(a0 + sweep - 4)
    (x1, y1) = p.P(c[0] + rr * math.cos(a1), c[1] + rr * math.sin(a1))
    (x2, y2) = p.P(c[0] + rr * math.cos(a2), c[1] + rr * math.sin(a2))
    large = 1 if sweep > 180 else 0
    p.L["sym"].append(f'<circle cx="{f(x1)}" cy="{f(y1)}" r="2.4" class="st-dot"/>'
                      f'<path d="M{f(x1)},{f(y1)} A{f(rr * p.s)},{f(rr * p.s)} 0 {large} 1 {f(x2)},{f(y2)}" class="st-walk" marker-end="url(#arrow)"/>')


def void(p, ps, label=None):
    p.poly("sym", ps, "st-void")
    a, b = ps[0], ps[2]
    p.line("sym", a, b, "st-x")
    p.line("sym", ps[1], ps[3], "st-x")
    if label:
        cx, cy = centroid(ps)
        p.text(cx, cy, label, "t-note", dy=4)


def overall_dims(p, x1, y1, x2, y2, off=0.9):
    """Wymiary orientacyjne: tylko gabaryty, w metrach."""
    for (a, b, c, d, txt, vert) in ((x1, y1 - off, x2, y1 - off, f"{pl(x2 - x1)} m", False),
                                    (x1 - off, y1, x1 - off, y2, f"{pl(y2 - y1)} m", True)):
        p.line("text", (a, b), (c, d), "d-dim")
        for q in ((a, b), (c, d)):
            x, y = p.P(*q)
            p.L["text"].append(f'<line x1="{f(x - 3.5)}" y1="{f(y + 3.5)}" x2="{f(x + 3.5)}" y2="{f(y - 3.5)}" class="d-tick"/>')
        if vert:
            p.text(a, (b + d) / 2, txt, "d-t", rot=-90, dy=-5)
        else:
            p.text((a + c) / 2, b, txt, "d-t", dy=-5)


def north_arrow(p, x, y):
    a, b = p.P(x, y)
    p.L["text"].append(f'<g transform="translate({f(a)},{f(b)})"><circle r="13" class="na-c"/>'
                       f'<polygon points="0,-11 4.5,5 0,1.5 -4.5,5" class="na-p"/>'
                       f'<text y="-17" text-anchor="middle" class="t-label">N</text></g>')


def scale_bar(p, x, y):
    a, b = p.P(x, y)
    s = p.s
    g = [f'<g transform="translate({f(a)},{f(b)})">']
    for i in range(5):
        g.append(f'<rect x="{f(i * s)}" y="0" width="{f(s)}" height="4" class="{"sb-a" if i % 2 == 0 else "sb-b"}"/>')
    for i in (0, 1, 5):
        g.append(f'<text x="{f(i * s)}" y="15" text-anchor="middle" class="d-t">{i}</text>')
    g.append(f'<text x="{f(5 * s + 9)}" y="5" class="d-t">m</text></g>')
    p.L["text"].append("".join(g))


# ------------------------------------------------------------------ meble
def box(p, x1, y1, x2, y2, cross=False):
    cx, cy, w, h = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
    sh = [("r", -w / 2, -h / 2, w, h)]
    if cross:
        sh += [("l", -w / 2, -h / 2, w / 2, h / 2), ("l", w / 2, -h / 2, -w / 2, h / 2)]
    p.item(cx, cy, 0, sh)


def bed(p, cx, cy, w, l, rot=0):
    """Łóżko: wezgłowie po stronie −y w układzie lokalnym."""
    p.item(cx, cy, rot, [("r", -w / 2, -l / 2, w, l, 0.05), ("r", -w / 2 + 0.08, -l / 2 + 0.08, w - 0.16, 0.38, 0.06),
                         ("l", -w / 2, -l / 2 + 0.75, w / 2, -l / 2 + 0.75)])


def futon(p, cx, cy, rot=0):
    p.item(cx, cy, rot, [("r", -0.45, -1.0, 0.9, 2.0, 0.08), ("r", -0.3, -0.92, 0.6, 0.3, 0.1),
                         ("l", -0.45, -0.4, 0.45, -0.4)])


def sofa(p, cx, cy, w, rot=0, d=0.9):
    p.item(cx, cy, rot, [("r", -w / 2, -d / 2, w, d, 0.08), ("r", -w / 2, -d / 2, w, 0.25, 0.05),
                         ("r", -w / 2, -d / 2, 0.22, d, 0.05), ("r", w / 2 - 0.22, -d / 2, 0.22, d, 0.05)])


def armchair(p, cx, cy, rot=0):
    p.item(cx, cy, rot, [("r", -0.4, -0.4, 0.8, 0.8, 0.12), ("r", -0.4, -0.4, 0.8, 0.2, 0.06)])


def table(p, cx, cy, w, h, rot=0, chairs=True):
    sh = [("r", -w / 2, -h / 2, w, h, 0.04)]
    if chairs:
        n = max(1, int(w / 0.65))
        for i in range(n):
            x = -w / 2 + w * (i + 0.5) / n
            sh += [("r", x - 0.2, -h / 2 - 0.42, 0.4, 0.36, 0.06), ("r", x - 0.2, h / 2 + 0.06, 0.4, 0.36, 0.06)]
    p.item(cx, cy, rot, sh)


def round_table(p, cx, cy, r, n=6):
    sh = [("c", 0, 0, r)]
    for i in range(n):
        a = 2 * math.pi * i / n
        sh.append(("c", (r + 0.28) * math.cos(a), (r + 0.28) * math.sin(a), 0.2))
    p.item(cx, cy, 0, sh)


def low_table(p, cx, cy, w, h, rot=0):
    """Niski stolik z poduszkami zabuton."""
    sh = [("r", -w / 2, -h / 2, w, h, 0.05)]
    for sx in (-1, 1):
        sh.append(("r", sx * (w / 2 + 0.1) - 0.25 + sx * 0.25, -0.25, 0.5, 0.5, 0.1))
    p.item(cx, cy, rot, sh)


def counter(p, x1, y1, x2, y2, sink=None, hob=None):
    box(p, x1, y1, x2, y2)
    if sink:
        p.item(sink[0], sink[1], 0, [("r", -0.3, -0.2, 0.6, 0.4, 0.05)])
    if hob:
        p.item(hob[0], hob[1], 0, [("c", -0.15, -0.12, 0.09), ("c", 0.15, -0.12, 0.09), ("c", -0.15, 0.12, 0.09), ("c", 0.15, 0.12, 0.09)])


def wc(p, cx, cy, rot=0):
    p.item(cx, cy, rot, [("r", -0.2, -0.36, 0.4, 0.18, 0.03), ("e", 0, 0.05, 0.18, 0.25)])


def basin(p, cx, cy, rot=0, w=0.6):
    p.item(cx, cy, rot, [("r", -w / 2, -0.23, w, 0.46, 0.04), ("e", 0, 0.02, w / 2 - 0.1, 0.14)])


def shower(p, x1, y1, x2, y2):
    box(p, x1, y1, x2, y2, cross=True)


def tub(p, cx, cy, w, l, rot=0):
    p.item(cx, cy, rot, [("r", -w / 2, -l / 2, w, l, 0.08), ("r", -w / 2 + 0.08, -l / 2 + 0.08, w - 0.16, l - 0.16, 0.25)])


def ofuro(p, cx, cy, s=1.3, rot=0):
    p.item(cx, cy, rot, [("r", -s / 2, -s / 2, s, s, 0.06), ("r", -s / 2 + 0.1, -s / 2 + 0.1, s - 0.2, s - 0.2, 0.08),
                         ("l", -s / 2, s / 2 + 0.25, s / 2, s / 2 + 0.25)])


def wardrobe(p, cx, cy, w, d=0.6, rot=0):
    p.item(cx, cy, rot, [("r", -w / 2, -d / 2, w, d), ("l", -w / 2, -d / 2, w / 2, d / 2)])


def desk(p, cx, cy, w=1.4, rot=0):
    p.item(cx, cy, rot, [("r", -w / 2, -0.35, w, 0.7, 0.03), ("c", 0, 0.6, 0.24)])


def fireplace(p, cx, cy, rot=0):
    p.item(cx, cy, rot, [("r", -0.6, -0.25, 1.2, 0.5, 0.05), ("r", -0.35, -0.12, 0.7, 0.25, 0.03)])


def washer(p, cx, cy, rot=0):
    p.item(cx, cy, rot, [("r", -0.3, -0.3, 0.6, 0.6, 0.04), ("c", 0, 0.03, 0.2)])


def plant(p, cx, cy, r=0.3):
    p.item(cx, cy, 0, [("c", 0, 0, r), ("c", 0, 0, r * 0.45)])


# ------------------------------------------------------------------ ogród
def gravel(p, ps):
    p.poly("garden", ps, "g-gravel")


def deck(p, ps):
    p.poly("ground", ps, "g-deck")


def lawn(p, ps):
    p.poly("ground", ps, "g-lawn")


def stone(p, c, rx, ry=None, rings=2, rot=0):
    ry = ry or rx * 0.75
    for k in range(rings, 0, -1):
        p.ellipse("garden", c, rx + 0.18 * k, ry + 0.18 * k, "g-ripple", rot)
    p.ellipse("garden", c, rx, ry, "g-stone", rot)


def moss(p, c, rx, ry=None, rot=0):
    p.ellipse("garden", c, rx, ry or rx * 0.8, "g-moss", rot)


def maple(p, c, r=0.9):
    p.circle("garden", c, r, "g-maple")
    for i in range(7):
        a = 2 * math.pi * i / 7 + 0.3
        p.circle("garden", (c[0] + r * 0.55 * math.cos(a), c[1] + r * 0.55 * math.sin(a)), r * 0.38, "g-maple2")
    p.circle("garden", c, 0.07, "g-trunk")


def pine(p, c, r=0.8):
    p.circle("garden", c, r, "g-pine")
    for i in range(9):
        a = 2 * math.pi * i / 9
        p.line("garden", c, (c[0] + r * math.cos(a), c[1] + r * math.sin(a)), "g-pineline")


def pond(p, ps):
    p.poly("garden", ps, "g-water")


def pond_ellipse(p, c, rx, ry, rot=0):
    p.ellipse("garden", c, rx, ry, "g-water", rot)


def basin_stone(p, c, r=0.3):
    p.circle("garden", c, r, "g-stone")
    p.circle("garden", c, r * 0.5, "g-water")


def lantern(p, c):
    x, y = c
    p.poly("garden", rect_pts(x - 0.2, y - 0.2, x + 0.2, y + 0.2), "g-lantern")
    p.line("garden", (x - 0.2, y - 0.2), (x + 0.2, y + 0.2), "g-lanternl")
    p.line("garden", (x + 0.2, y - 0.2), (x - 0.2, y + 0.2), "g-lanternl")


def steps(p, pts):
    for i, c in enumerate(pts):
        p.ellipse("garden", c, 0.24, 0.18, "g-step", rot=(i * 37) % 180)


def bamboo(p, c, n=9, r=0.45):
    rnd = random.Random(int(c[0] * 100 + c[1] * 7))
    for _ in range(n):
        a, rr = rnd.random() * 6.28, rnd.random() * r
        p.circle("garden", (c[0] + rr * math.cos(a), c[1] + rr * math.sin(a)), 0.05, "g-bamboo")


def chain(p, c, label=None):
    p.circle("garden", c, 0.14, "g-chain")
    p.circle("garden", c, 0.05, "g-chaindot")
    if label:
        p.text(c[0] + 0.25, c[1] + 0.05, label, "t-note", anchor="start")


# --------------------------------------------------------------- przekrój
class Sec:
    def __init__(self, label, hmin, hmax, zmin, zmax, s=34, pad_l=40, pad_r=110, pad_t=16, pad_b=16):
        self.s, self.hmin, self.zmax, self.pl, self.pt = s, hmin, zmax, pad_l, pad_t
        self.W = pad_l + pad_r + (hmax - hmin) * s
        self.H = pad_t + pad_b + (zmax - zmin) * s
        self.label = label
        self.el = []

    def P(self, h, z):
        return (self.pl + (h - self.hmin) * self.s, self.pt + (self.zmax - z) * self.s)

    def poly(self, ps, cls):
        self.el.append(f'<polygon points="{" ".join(f"{f(a)},{f(b)}" for a, b in (self.P(*q) for q in ps))}" class="{cls}"/>')

    def rect(self, h1, z1, h2, z2, cls):
        self.poly([(h1, z1), (h2, z1), (h2, z2), (h1, z2)], cls)

    def line(self, a, b, cls):
        (x1, y1), (x2, y2) = self.P(*a), self.P(*b)
        self.el.append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" class="{cls}"/>')

    def pline(self, ps, cls):
        self.el.append(f'<polyline points="{" ".join(f"{f(a)},{f(b)}" for a, b in (self.P(*q) for q in ps))}" class="{cls}"/>')

    def text(self, h, z, s, cls, anchor="middle", dx=0, dy=0):
        a, b = self.P(h, z)
        self.el.append(f'<text x="{f(a + dx)}" y="{f(b + dy)}" text-anchor="{anchor}" class="{cls}">{s}</text>')

    def flow(self, a, b):
        (x1, y1), (x2, y2) = self.P(*a), self.P(*b)
        self.el.append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" class="s-flow" marker-end="url(#arrow-w)"/>')

    def chain(self, h, z1, z2):
        self.line((h, z1), (h, z2), "s-chain")
        z = z2
        while z < z1 - 0.1:
            x, y = self.P(h, z)
            self.el.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="2" ry="3.2" class="s-link"/>')
            z += 0.22

    def level(self, h, z, label):
        a, b = self.P(h, z)
        self.el.append(f'<polygon points="{f(a)},{f(b)} {f(a - 4.5)},{f(b - 7)} {f(a + 4.5)},{f(b - 7)}" class="s-lvl"/>'
                       f'<line x1="{f(a - 7)}" y1="{f(b)}" x2="{f(a + 30)}" y2="{f(b)}" class="s-thin"/>'
                       f'<text x="{f(a + 7)}" y="{f(b - 3)}" class="d-t">{label}</text>')

    def person(self, h, z):
        x, y = self.P(h, z)
        s = self.s
        self.el.append(f'<g class="s-person"><circle cx="{f(x)}" cy="{f(y - 1.62 * s)}" r="{f(0.12 * s)}"/>'
                       f'<rect x="{f(x - 0.18 * s)}" y="{f(y - 1.48 * s)}" width="{f(0.36 * s)}" height="{f(0.7 * s)}" rx="{f(0.1 * s)}"/>'
                       f'<rect x="{f(x - 0.13 * s)}" y="{f(y - 0.85 * s)}" width="{f(0.11 * s)}" height="{f(0.85 * s)}"/>'
                       f'<rect x="{f(x + 0.02 * s)}" y="{f(y - 0.85 * s)}" width="{f(0.11 * s)}" height="{f(0.85 * s)}"/></g>')

    def tree(self, h, z, ht, r, cls="s-tree"):
        x, y = self.P(h, z)
        s = self.s
        self.el.append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x)}" y2="{f(y - (ht - r) * s)}" class="s-trunk"/>'
                       f'<ellipse cx="{f(x)}" cy="{f(y - (ht - r) * s)}" rx="{f(r * s)}" ry="{f(r * 0.8 * s)}" class="{cls}"/>')

    def note(self, h, z, txt, th, tz, anchor="start"):
        """Opis z odnośnikiem: tekst w (th, tz), kropka w (h, z)."""
        a, b = self.P(h, z)
        c, d = self.P(th, tz)
        self.el.append(f'<polyline points="{f(a)},{f(b)} {f(c)},{f(d + 3)} {f(c + (60 if anchor == "start" else -60))},{f(d + 3)}" class="s-leader"/>'
                       f'<circle cx="{f(a)}" cy="{f(b)}" r="1.8" class="s-dot"/>')
        self.el.append(f'<text x="{f(c + (2 if anchor == "start" else -2))}" y="{f(d)}" text-anchor="{anchor}" class="t-note">{txt}</text>')

    def render(self):
        return (f'<svg class="drw" viewBox="0 0 {self.W:.0f} {self.H:.0f}" role="img" aria-label="{self.label}" '
                f'xmlns="http://www.w3.org/2000/svg">' + "".join(self.el) + "</svg>")


# ------------------------------------------------------------------ witraż
PALETTE = {
    "gold": ["#E8A317", "#F2C14E", "#D98E04", "#F6D27A"],
    "ruby": ["#A4161A", "#C1272D", "#7F0F14", "#D9483B"],
    "blue": ["#1D4E89", "#2E6FB0", "#163A66", "#3E86C6"],
    "teal": ["#167D7F", "#29A0A2", "#0F5F61", "#5BC0BE"],
    "green": ["#3A7D44", "#5B9A4B", "#2C5F34", "#8CB369"],
    "sky": ["#D8E2F0", "#C9D6EA", "#E9EEF6", "#B9C9E2"],
    "violet": ["#5B3E8C", "#7A5BA6", "#45306B", "#9A7FC2"],
}


def stained_rect(seed=7, nx=14, ny=7):
    """Witraż prostokątny 2:1 „słońce nad wodą”: lista (wielokąt w [0,1]×[0,0.5], kolor)."""
    rnd = random.Random(seed)
    W, H = 1.0, 0.5
    pts = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x, y = W * i / nx, H * j / ny
            if 0 < i < nx:
                x += (rnd.random() - 0.5) * W / nx * 0.7
            if 0 < j < ny:
                y += (rnd.random() - 0.5) * H / ny * 0.7
            pts[i, j] = (x, y)
    cells = []
    for i in range(nx):
        for j in range(ny):
            a, b, c, d = pts[i, j], pts[i + 1, j], pts[i + 1, j + 1], pts[i, j + 1]
            tris = [(a, b, c), (a, c, d)] if (i + j) % 2 == 0 else [(a, b, d), (b, c, d)]
            for t in tris:
                cx = sum(q[0] for q in t) / 3
                cy = sum(q[1] for q in t) / 3
                wave = 0.31 + 0.035 * math.sin(cx * 13) + 0.02 * math.sin(cx * 31 + 1)
                if math.hypot(cx - 0.68, cy - 0.17) < 0.1:
                    fam = "gold"
                elif math.hypot(cx - 0.68, cy - 0.17) < 0.15:
                    fam = "ruby" if rnd.random() < 0.6 else "gold"
                elif cy > wave + 0.07:
                    fam = "blue"
                elif cy > wave:
                    fam = "teal"
                elif cx < 0.25 and cy > 0.12 and rnd.random() < 0.7:
                    fam = "green"
                else:
                    fam = "sky" if rnd.random() < 0.75 else "violet"
                cells.append((list(t), rnd.choice(PALETTE[fam])))
    return cells


def stained_rosette(seed=11):
    """Witraż ośmiokątny (rozeta 8-krotna) w kwadracie [0,1]²."""
    rnd = random.Random(seed)
    cells = []
    rings = [0.0, 0.07, 0.17, 0.28, 0.39, 0.5]
    fams = ["gold", "ruby", "teal", "blue", "green"]
    for k in range(len(rings) - 1):
        n = 8 * (k + 1) if k < 3 else 32
        r1, r2 = rings[k], rings[k + 1]
        for i in range(n):
            a1 = 2 * math.pi * i / n + math.pi / 8
            a2 = 2 * math.pi * (i + 1) / n + math.pi / 8
            steps = 3
            poly = []
            for s in range(steps + 1):
                a = a1 + (a2 - a1) * s / steps
                poly.append((0.5 + r2 * math.cos(a), 0.5 + r2 * math.sin(a)))
            for s in range(steps, -1, -1):
                a = a1 + (a2 - a1) * s / steps
                poly.append((0.5 + r1 * math.cos(a), 0.5 + r1 * math.sin(a)))
            if k == 0:
                fam = "gold"
            elif k == 4:
                fam = "blue" if i % 4 in (0, 1) else "teal"
            else:
                fam = fams[k] if i % 2 == 0 else fams[(k + 2) % 5]
            cells.append((poly, rnd.choice(PALETTE[fam])))
    return cells


def stained_svg(cells, w, h, label, clip_oct=False):
    out = [f'<svg class="illus witraz" viewBox="0 0 {w} {h}" role="img" aria-label="{label}" xmlns="http://www.w3.org/2000/svg">']
    sc = w
    cid = "oct" + str(abs(hash(label)) % 10000)
    if clip_oct:
        r = 0.5 * sc
        pts = " ".join(f"{f(w / 2 + r / math.cos(math.pi / 8) * math.cos(math.pi / 8 + k * math.pi / 4))},"
                       f"{f(h / 2 + r / math.cos(math.pi / 8) * math.sin(math.pi / 8 + k * math.pi / 4))}" for k in range(8))
        out.append(f'<defs><clipPath id="{cid}"><polygon points="{pts}"/></clipPath></defs><g clip-path="url(#{cid})">')
        out.append(f'<rect width="{w}" height="{h}" fill="#1a1a1a"/>')
    else:
        out.append('<g>')
    for poly, col in cells:
        out.append(f'<polygon points="{" ".join(f"{f(x * sc)},{f(y * sc)}" for x, y in poly)}" fill="{col}" stroke="#141414" stroke-width="2.2" stroke-linejoin="round"/>')
    out.append("</g>")
    if clip_oct:
        out.append(f'<polygon points="{pts}" fill="none" stroke="#141414" stroke-width="6"/>')
    else:
        out.append(f'<rect x="1.5" y="1.5" width="{w - 3}" height="{h - 3}" fill="none" stroke="#141414" stroke-width="5"/>')
    out.append("</svg>")
    return "".join(out)
