"""Meble: symbole 2D (rzut) i proste bryły 3D oraz automatyczne rozmieszczanie w pokojach.

Element ma lokalny układ: x – szerokość, y – głębokość; plecy przy y = -d/2, front przy y = +d/2.
"""
import math
import random

from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union

from .geom import largest, polygons


class Item:
    def __init__(self, kind, w, d, shapes, parts, h=0.8):
        self.kind, self.w, self.d = kind, w, d
        self.shapes = shapes      # 2D: ('r', x, y, w, h, rx, cls) | ('c', x, y, r, cls) | ('l', x1, y1, x2, y2, cls) | ('p', [(x,y)], cls)
        self.parts = parts        # 3D: ('box', x, y, z, w, d, h, mat) | ('cyl', x, y, z, r, h, mat) | ('sph', x, y, z, r, mat)
        self.h = h
        self.cx = self.cy = 0.0
        self.rot = 0.0
        self.z = 0.0

    def footprint(self, cx=None, cy=None, rot=None, pad=0.0):
        cx = self.cx if cx is None else cx
        cy = self.cy if cy is None else cy
        rot = self.rot if rot is None else rot
        p = box(-self.w / 2 - pad, -self.d / 2 - pad, self.w / 2 + pad, self.d / 2 + pad)
        p = affinity.rotate(p, rot, origin=(0, 0))
        return affinity.translate(p, cx, cy)

    def world(self, x, y):
        a = math.radians(self.rot)
        return (self.cx + x * math.cos(a) - y * math.sin(a), self.cy + x * math.sin(a) + y * math.cos(a))


# ------------------------------------------------------------ biblioteka
F, W, D, T, P = "fu", "fu-w", "fu-d", "fu-t", "fu-p"   # klasy rysunkowe: tkanina, drewno, ciemne, tekstylia jasne, rośliny


def r_(x, y, w, h, rx=0.0, cls=F):
    return ("r", x, y, w, h, rx, cls)


def sofa(w=2.6, d=0.95):
    s = [r_(-w / 2, -d / 2, w, d, 0.1, F), r_(-w / 2, -d / 2, w, 0.24, 0.06, D),
         r_(-w / 2, -d / 2, 0.22, d, 0.06, D), r_(w / 2 - 0.22, -d / 2, 0.22, d, 0.06, D)]
    n = max(2, int(round((w - 0.44) / 0.75)))
    cw = (w - 0.44) / n
    for i in range(n):
        s.append(r_(-w / 2 + 0.22 + i * cw + 0.03, -d / 2 + 0.27, cw - 0.06, d - 0.33, 0.06, T))
    parts = [("box", 0, 0, 0, w, d, 0.42, "tkanina"), ("box", 0, -d / 2 + 0.12, 0.42, w, 0.24, 0.38, "tkanina"),
             ("box", -w / 2 + 0.11, 0, 0.42, 0.22, d, 0.2, "tkanina"), ("box", w / 2 - 0.11, 0, 0.42, 0.22, d, 0.2, "tkanina")]
    return Item("sofa", w, d, s, parts, 0.8)


def armchair(w=0.85):
    s = [r_(-w / 2, -w / 2, w, w, 0.14, F), r_(-w / 2, -w / 2, w, 0.2, 0.08, D), r_(-w / 2 + 0.16, -w / 2 + 0.22, w - 0.32, w - 0.3, 0.08, T)]
    return Item("fotel", w, w, s, [("box", 0, 0, 0, w, w, 0.42, "tkanina"), ("box", 0, -w / 2 + 0.1, 0.42, w, 0.2, 0.4, "tkanina")], 0.8)


def coffee_table(w=1.2, d=0.7):
    return Item("stolik", w, d, [r_(-w / 2, -d / 2, w, d, 0.05, W)], [("box", 0, 0, 0, w, d, 0.4, "drewno_mebel")], 0.4)


def round_coffee(r=0.45):
    return Item("stolik", 2 * r, 2 * r, [("c", 0, 0, r, W)], [("cyl", 0, 0, 0, r, 0.4, "drewno_mebel")], 0.4)


def rug(w=3.0, d=2.2):
    return Item("dywan", w, d, [r_(-w / 2, -d / 2, w, d, 0.04, "fu-rug")], [("box", 0, 0, 0, w, d, 0.01, "dywan")], 0.01)


def dining(n=6, w=None, d=1.0):
    ends = n % 2 == 1 or n >= 8          # krzesła u szczytów stołu liczą się do n
    per = max(1, (n - (2 if ends else 0)) // 2)
    w = w or max(1.4, per * 0.65 + 0.3)
    s = [r_(-w / 2, -d / 2, w, d, 0.05, W)]
    parts = [("box", 0, 0, 0.72, w, d, 0.04, "drewno_mebel"), ("box", 0, 0, 0, 0.16, d * 0.6, 0.72, "drewno_mebel")]
    for i in range(per):
        x = -w / 2 + (i + 0.5) * w / per
        for sy in (-1, 1):
            y = sy * (d / 2 + 0.22)
            s.append(r_(x - 0.21, y - 0.2, 0.42, 0.4, 0.07, F))
            parts.append(("box", x, y, 0, 0.42, 0.4, 0.46, "tkanina"))
    if ends:
        for sx in (-1, 1):
            s.append(r_(sx * (w / 2 + 0.22) - 0.2, -0.21, 0.4, 0.42, 0.07, F))
            parts.append(("box", sx * (w / 2 + 0.22), 0, 0, 0.4, 0.42, 0.46, "tkanina"))
    return Item("stol", w + 0.9, d + 0.9, s, parts, 0.75)


def round_dining(r=0.65, n=6):
    s = [("c", 0, 0, r, W)]
    parts = [("cyl", 0, 0, 0.72, r, 0.04, "drewno_mebel"), ("cyl", 0, 0, 0, 0.1, 0.72, "drewno_mebel")]
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = (r + 0.25) * math.cos(a), (r + 0.25) * math.sin(a)
        s.append(("c", x, y, 0.2, F))
        parts.append(("cyl", x, y, 0, 0.2, 0.46, "tkanina"))
    R = r + 0.5
    return Item("stol", 2 * R, 2 * R, s, parts, 0.75)


def bed(w=1.8, l=2.1, nightstands=True):
    tw = w + (1.0 if nightstands else 0)
    s = [r_(-w / 2, -l / 2, w, l, 0.06, F), r_(-w / 2, -l / 2, w, 0.1, 0.02, D)]
    pw = (w - 0.3) / (2 if w > 1.2 else 1)
    for i in range(2 if w > 1.2 else 1):
        s.append(r_(-w / 2 + 0.12 + i * (pw + 0.06), -l / 2 + 0.16, pw, 0.36, 0.08, T))
    s.append(r_(-w / 2, -l / 2 + 0.75, w, l - 0.75, 0.04, "fu-blanket"))
    s.append(("l", -w / 2, -l / 2 + 1.45, w / 2, -l / 2 + 1.45, F))
    parts = [("box", 0, 0, 0, w, l, 0.5, "posciel"), ("box", 0, -l / 2 + 0.05, 0, w + 0.1, 0.1, 1.0, "drewno_mebel")]
    if nightstands:
        for sx in (-1, 1):
            x = sx * (w / 2 + 0.27)
            s.append(r_(x - 0.22, -l / 2, 0.44, 0.4, 0.04, W))
            s.append(("c", x, -l / 2 + 0.2, 0.09, "fu-lamp"))
            parts.append(("box", x, -l / 2 + 0.2, 0, 0.44, 0.4, 0.5, "drewno_mebel"))
    return Item("lozko", tw, l, s, parts, 0.6)


def wardrobe(w=2.0, d=0.62):
    s = [r_(-w / 2, -d / 2, w, d, 0.0, W), ("l", -w / 2, d / 2 - 0.03, w / 2, d / 2 - 0.03, D)]
    n = max(1, int(round(w / 0.6)))
    for i in range(1, n):
        x = -w / 2 + i * w / n
        s.append(("l", x, -d / 2, x, d / 2, D))
    return Item("szafa", w, d, s, [("box", 0, 0, 0, w, d, 2.3, "szafa")], 2.3)


def shelves(w=2.0, d=0.38, books=True):
    s = [r_(-w / 2, -d / 2, w, d, 0.0, W)]
    if books:
        rnd = random.Random(int(w * 100))
        x = -w / 2 + 0.03
        while x < w / 2 - 0.08:
            bw = rnd.uniform(0.03, 0.08)
            s.append(r_(x, -d / 2 + 0.04, bw, d - 0.12, 0.0, rnd.choice(["fu-b1", "fu-b2", "fu-b3"])))
            x += bw + 0.01
    return Item("regal", w, d, s, [("box", 0, 0, 0, w, d, 2.4, "regal")], 2.4)


def counter(w=3.6, d=0.62, sink=True, hob=True):
    s = [r_(-w / 2, -d / 2, w, d, 0.0, "fu-c")]
    if sink:
        s.append(r_(-w / 4 - 0.35, -0.2, 0.7, 0.42, 0.06, F))
    if hob:
        for dx in (-0.16, 0.16):
            for dy in (-0.12, 0.12):
                s.append(("c", w / 4 + dx, dy, 0.09, D))
    return Item("blat", w, d, s, [("box", 0, 0, 0, w, d, 0.9, "kuchnia"), ("box", 0, -d / 2 + 0.18, 1.5, w, 0.35, 0.75, "kuchnia")], 0.9)


def island(w=2.4, d=1.0, stools=3):
    s = [r_(-w / 2, -d / 2, w, d, 0.04, "fu-c")]
    parts = [("box", 0, 0, 0, w, d, 0.92, "kuchnia")]
    for i in range(stools):
        x = -w / 2 + (i + 0.5) * w / stools
        s.append(("c", x, d / 2 + 0.3, 0.19, F))
        parts.append(("cyl", x, d / 2 + 0.3, 0, 0.18, 0.75, "tkanina"))
    return Item("wyspa", w, d + 0.6, s, parts, 0.92)


def desk(w=1.6, d=0.75, chair=True):
    s = [r_(-w / 2, -d / 2, w, d, 0.03, W), r_(-0.28, -d / 2 + 0.06, 0.56, 0.32, 0.02, "fu-screen")]
    parts = [("box", 0, 0, 0.72, w, d, 0.04, "drewno_mebel"), ("box", -w / 2 + 0.05, 0, 0, 0.06, d, 0.72, "rama_mebel"),
             ("box", w / 2 - 0.05, 0, 0, 0.06, d, 0.72, "rama_mebel")]
    dd = d
    if chair:
        s.append(("c", 0, d / 2 + 0.32, 0.26, F))
        parts.append(("cyl", 0, d / 2 + 0.32, 0, 0.26, 0.9, "tkanina_ciemna"))
        dd = d + 0.6
    return Item("biurko", w, dd, s, parts, 0.75)


def desk_pair(w=1.6, d=1.5):
    s = [r_(-w / 2, -d / 4 - 0.37, w, 0.74, 0.02, W), r_(-w / 2, d / 4 - 0.37, w, 0.74, 0.02, W),
         r_(-0.3, -0.06, 0.6, 0.12, 0.0, "fu-screen")]
    parts = [("box", 0, 0, 0.72, w, 1.48, 0.04, "drewno_mebel"), ("box", 0, 0, 0, 0.1, 1.2, 0.72, "rama_mebel")]
    for sy in (-1, 1):
        s.append(("c", 0, sy * (d / 2 + 0.25), 0.26, F))
        parts.append(("cyl", 0, sy * (d / 2 + 0.25), 0, 0.26, 0.9, "tkanina_ciemna"))
    return Item("biurko2", w, d + 1.1, s, parts, 0.75)


def bathtub(w=1.75, d=0.8, free=False):
    s = [r_(-w / 2, -d / 2, w, d, 0.35 if free else 0.08, "fu-bath"), r_(-w / 2 + 0.1, -d / 2 + 0.1, w - 0.2, d - 0.2, 0.3, "fu-water")]
    return Item("wanna", w, d, s, [("box", 0, 0, 0, w, d, 0.55, "ceramika")], 0.55)


def shower(w=1.0, d=1.0):
    s = [r_(-w / 2, -d / 2, w, d, 0.0, "fu-bath"), ("l", -w / 2, -d / 2, w / 2, d / 2, F), ("l", w / 2, -d / 2, -w / 2, d / 2, F),
         ("c", 0, 0, 0.05, D)]
    return Item("prysznic", w, d, s, [("box", 0, 0, 0, w, d, 0.03, "ceramika"), ("box", 0, d / 2 - 0.02, 0, w, 0.02, 2.0, "szklo_mebel")], 0.03)


def wc():
    s = [r_(-0.2, -0.33, 0.4, 0.16, 0.03, "fu-bath"), ("p", [(-0.18, -0.17), (0.18, -0.17), (0.17, 0.12), (0.08, 0.3), (-0.08, 0.3), (-0.17, 0.12)], "fu-bath")]
    return Item("wc", 0.45, 0.68, s, [("box", 0, 0, 0, 0.38, 0.6, 0.42, "ceramika")], 0.42)


def basins(w=1.4, d=0.5, n=2):
    s = [r_(-w / 2, -d / 2, w, d, 0.02, "fu-c")]
    for i in range(n):
        x = -w / 2 + (i + 0.5) * w / n
        s.append(("e", x, 0.02, 0.22, 0.15, "fu-bath"))
    return Item("umywalki", w, d, s, [("box", 0, 0, 0.0, w, d, 0.85, "kuchnia")], 0.85)


def washer():
    return Item("pralka", 0.62, 0.62, [r_(-0.31, -0.31, 0.62, 0.62, 0.04, "fu-bath"), ("c", 0, 0.03, 0.2, F)], [("box", 0, 0, 0, 0.6, 0.6, 0.85, "ceramika")], 0.85)


def piano():
    s = [("p", [(-0.75, -0.75), (0.75, -0.75), (0.75, 0.2), (0.4, 0.75), (0.0, 0.95), (-0.5, 0.9), (-0.75, 0.6)], D),
         r_(-0.7, -0.75, 1.4, 0.18, 0.0, T), r_(-0.3, -1.15, 0.6, 0.3, 0.05, F)]
    return Item("fortepian", 1.6, 2.3, s, [("box", 0, 0.1, 0.65, 1.5, 1.6, 0.35, "czarny_lak"), ("box", 0, -1.0, 0, 0.6, 0.3, 0.48, "tkanina_ciemna")], 1.0)


def easel():
    s = [("p", [(-0.4, 0.2), (0.4, 0.2), (0, -0.35)], W), ("l", -0.5, 0.2, 0.5, 0.2, D)]
    return Item("sztaluga", 1.0, 0.6, s, [("box", 0, 0, 0, 0.8, 0.05, 1.6, "drewno_mebel")], 1.6)


def workbench(w=2.4, d=0.8):
    s = [r_(-w / 2, -d / 2, w, d, 0.0, W), ("l", -w / 2, -d / 2 + 0.15, w / 2, -d / 2 + 0.15, D)]
    return Item("warsztat", w, d, s, [("box", 0, 0, 0, w, d, 0.9, "drewno_mebel")], 0.9)


def low_table(w=1.2, d=0.8):
    s = [r_(-w / 2, -d / 2, w, d, 0.04, W)]
    for sx, sy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        x, y = sx * (w / 2 + 0.3), sy * (d / 2 + 0.3)
        s.append(r_(x - 0.25, y - 0.25, 0.5, 0.5, 0.12, T))
    return Item("czajnik", w + 1.1, d + 1.1, s, [("box", 0, 0, 0, w, d, 0.32, "drewno_mebel")], 0.32)


def lounger():
    s = [r_(-0.35, -1.0, 0.7, 2.0, 0.12, F), r_(-0.35, -1.0, 0.7, 0.6, 0.1, T)]
    return Item("lezak", 0.7, 2.0, s, [("box", 0, 0, 0, 0.7, 2.0, 0.35, "tkanina")], 0.35)


def planter(r=0.4, kind="cytrus"):
    s = [("c", 0, 0, r, "fu-pot"), ("c", 0, 0, r * 0.82, P)]
    for i in range(6):
        a = i * math.pi / 3
        s.append(("c", r * 0.45 * math.cos(a), r * 0.45 * math.sin(a), r * 0.32, P))
    if kind == "cytrus":
        for i in range(4):
            a = 0.6 + i * math.pi / 2
            s.append(("c", r * 0.5 * math.cos(a), r * 0.5 * math.sin(a), 0.05, "fu-fruit"))
    parts = [("cyl", 0, 0, 0, r, 0.55, "donica"), ("sph", 0, 0, 1.6, r * 1.6, "lisc_cytrus" if kind == "cytrus" else "lisc")]
    return Item("donica", 2 * r, 2 * r, s, parts, 1.8)


def bench(w=1.8, d=0.45):
    return Item("lawka", w, d, [r_(-w / 2, -d / 2, w, d, 0.04, W)], [("box", 0, 0, 0, w, d, 0.45, "drewno_mebel")], 0.45)


def plinth(s=0.5):
    return Item("cokol", s, s, [r_(-s / 2, -s / 2, s, s, 0.0, F), ("c", 0, 0, s * 0.25, D)], [("box", 0, 0, 0, s, s, 1.0, "tynk_mebel"), ("sph", 0, 0, 1.2, 0.2, "brąz")], 1.2)


def sauna_bench(w=2.0, d=0.6):
    s = [r_(-w / 2, -d / 2, w, d, 0.0, W)]
    for i in range(1, int(w / 0.12)):
        x = -w / 2 + i * 0.12
        s.append(("l", x, -d / 2, x, d / 2, D))
    return Item("lawa", w, d, s, [("box", 0, 0, 0, w, d, 0.9, "drewno_mebel")], 0.9)


def stove():
    return Item("piec", 0.5, 0.5, [r_(-0.25, -0.25, 0.5, 0.5, 0.05, D), ("c", 0, 0, 0.12, F)], [("box", 0, 0, 0, 0.5, 0.5, 0.8, "czarny_lak")], 0.8)


def fireplace(w=1.6):
    s = [r_(-w / 2, -0.3, w, 0.6, 0.0, "fu-stone"), r_(-0.45, -0.1, 0.9, 0.3, 0.02, D)]
    return Item("kominek", w, 0.6, s, [("box", 0, 0, 0, w, 0.6, 1.1, "kamien_mebel")], 1.1)


def tv_unit(w=2.2):
    s = [r_(-w / 2, -0.22, w, 0.44, 0.0, W), r_(-0.7, -0.22, 1.4, 0.06, 0.0, D)]
    return Item("rtv", w, 0.44, s, [("box", 0, 0, 0, w, 0.44, 0.5, "drewno_mebel")], 0.5)


def car():
    s = [r_(-0.9, -2.3, 1.8, 4.6, 0.5, "fu-car"), r_(-0.75, -0.9, 1.5, 1.6, 0.3, D)]
    return Item("auto", 1.8, 4.6, s, [("box", 0, 0, 0.2, 1.8, 4.6, 0.8, "auto"), ("box", 0, -0.1, 1.0, 1.5, 2.2, 0.45, "auto")], 1.45)


def tank():
    return Item("zbiornik", 0.7, 0.7, [("c", 0, 0, 0.32, "fu-bath"), ("c", 0, 0, 0.12, F)], [("cyl", 0, 0, 0, 0.32, 1.9, "ceramika")], 1.9)


def mat():
    return Item("mata", 0.7, 1.9, [r_(-0.35, -0.95, 0.7, 1.9, 0.05, "fu-mat")], [("box", 0, 0, 0, 0.7, 1.9, 0.01, "dywan")], 0.01)


def wine_rack(w=2.0):
    s = [r_(-w / 2, -0.2, w, 0.4, 0.0, W)]
    for i in range(int(w / 0.12)):
        s.append(("c", -w / 2 + 0.06 + i * 0.12, 0, 0.04, "fu-wine"))
    return Item("wino", w, 0.4, s, [("box", 0, 0, 0, w, 0.4, 2.2, "regal")], 2.2)


# --------------------------------------------------------------- rozmieszczanie
class Placer:
    def __init__(self, room, net, segs, blocked):
        self.room = room
        self.free = net.buffer(-0.02)
        self.segs = segs          # lista (LineString odcinka ściany pełnej, długość)
        self.blocked = blocked
        self.items = []
        self.occ = []

    def fits(self, it, cx, cy, rot, pad=0.05):
        fp = it.footprint(cx, cy, rot)
        if not self.free.contains(fp):
            return False
        if self.blocked is not None and not self.blocked.is_empty and fp.intersects(self.blocked):
            return False
        fpp = it.footprint(cx, cy, rot, pad)
        return all(not fpp.intersects(o) for o in self.occ)

    def put(self, it, cx, cy, rot):
        it.cx, it.cy, it.rot = cx, cy, rot
        self.items.append(it)
        self.occ.append(it.footprint())
        return True

    def try_at(self, it, cx, cy, rot):
        if self.fits(it, cx, cy, rot):
            return self.put(it, cx, cy, rot)
        return False

    def against(self, it, prefer="long", gap=0.03, along=0.5, exclude=None, segs=None):
        """Plecami do pełnej ściany. Próbuje kolejne odcinki i pozycje wzdłuż nich."""
        cand = list(segs if segs is not None else self.segs)
        if prefer == "long":
            cand.sort(key=lambda s: -s[1])
        elif prefer == "short":
            cand.sort(key=lambda s: s[1])
        for seg, L in cand:
            if exclude is not None and seg.distance(exclude) < 0.3:
                continue
            if L < it.w + 0.05:
                continue
            for f in _fracs(along):
                s = (L - it.w) * f + it.w / 2
                pos = self._wall_pose(seg, s, it.d / 2 + gap)
                if pos and self.try_at(it, *pos):
                    return seg
        return None

    def _wall_pose(self, seg, s, off):
        p = seg.interpolate(s)
        a = seg.interpolate(max(0, s - 0.05))
        b = seg.interpolate(min(seg.length, s + 0.05))
        ex, ey = b.x - a.x, b.y - a.y
        L = math.hypot(ex, ey)
        if L < 1e-9:
            return None
        ex, ey = ex / L, ey / L
        # normalna do wnętrza: sprawdź, która strona jest w pokoju
        for nx, ny in ((-ey, ex), (ey, -ex)):
            q = Point(p.x + nx * (off + 0.05), p.y + ny * (off + 0.05))
            if self.free.contains(q):
                cx, cy = p.x + nx * off, p.y + ny * off
                rot = math.degrees(math.atan2(-nx, ny))
                return cx, cy, rot
        return None

    def center(self, it, rot=None, shifts=((0, 0),)):
        c = self.free.representative_point() if self.free.area < 1 else _pole(self.free)
        r = self.axis() if rot is None else rot
        for dx, dy in shifts:
            a = math.radians(r)
            cx = c.x + dx * math.cos(a) - dy * math.sin(a)
            cy = c.y + dx * math.sin(a) + dy * math.cos(a)
            for rr in (r, r + 90):
                if self.try_at(it, cx, cy, rr):
                    return True
        # zapas: siatka po wolnej powierzchni, najpierw miejsca najbliżej środka
        minx, miny, maxx, maxy = self.free.bounds
        step = 0.2
        cand = []
        nx, ny = int((maxx - minx) / step) + 1, int((maxy - miny) / step) + 1
        for i in range(nx):
            for j in range(ny):
                x, y = minx + i * step, miny + j * step
                cand.append((math.hypot(x - c.x, y - c.y), x, y))
        cand.sort()
        for d, x, y in cand[:500]:
            for rr in (r, r + 90):
                if self.try_at(it, x, y, rr):
                    return True
        return False

    def near(self, it, x, y, rots, radius=3.0, step=0.2):
        """Najbliższe (x, y) miejsce, w którym mebel się mieści (siatka w promieniu radius)."""
        cand = []
        n = int(radius / step)
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                d = math.hypot(i * step, j * step)
                if d <= radius:
                    cand.append((d, x + i * step, y + j * step))
        cand.sort()
        for d, px, py in cand:
            if not self.free.contains(Point(px, py)):
                continue
            for rr in rots:
                if self.try_at(it, px, py, rr):
                    return True
        return False

    def axis(self):
        mrr = self.free.minimum_rotated_rectangle
        cs = list(mrr.exterior.coords)
        e1 = (cs[1][0] - cs[0][0], cs[1][1] - cs[0][1])
        e2 = (cs[2][0] - cs[1][0], cs[2][1] - cs[1][1])
        e = e1 if math.hypot(*e1) >= math.hypot(*e2) else e2
        return math.degrees(math.atan2(e[1], e[0]))


def _fracs(along):
    base = [along, 0.5, 0.2, 0.8, 0.0, 1.0, 0.35, 0.65]
    out = []
    for f in base:
        if f not in out:
            out.append(f)
    return out


def _pole(poly):
    from shapely.ops import polylabel
    try:
        return polylabel(poly, 0.05)
    except Exception:
        return poly.representative_point()


def frame(net):
    """Prostokąt obrócony: środek, kąt osi długiej, długość, szerokość."""
    mrr = net.minimum_rotated_rectangle
    cs = list(mrr.exterior.coords)
    e1 = (cs[1][0] - cs[0][0], cs[1][1] - cs[0][1])
    e2 = (cs[2][0] - cs[1][0], cs[2][1] - cs[1][1])
    l1, l2 = math.hypot(*e1), math.hypot(*e2)
    if l1 >= l2:
        ang, L, Wd = math.degrees(math.atan2(e1[1], e1[0])), l1, l2
    else:
        ang, L, Wd = math.degrees(math.atan2(e2[1], e2[0])), l2, l1
    c = mrr.centroid
    return c.x, c.y, ang, L, Wd


def local(cx, cy, ang, u, v):
    a = math.radians(ang)
    return cx + u * math.cos(a) - v * math.sin(a), cy + u * math.sin(a) + v * math.cos(a)


# ---------------------------------------------------------------- przepisy
def furnish(room, P):
    k = room.kind
    fn = RECIPES.get(k)
    if fn is None:
        return []
    try:
        fn(room, P)
    except Exception as e:  # meble nigdy nie blokują rysunku
        room.house.warnings.append(f"meble {room.key}: {e}")
    return P.items


def _kitchen_living(room, P, with_k=True, with_d=True, with_l=True):
    cx, cy, ang, L, Wd = frame(P.free)
    # wybór końca kuchennego
    sign = 1
    if room.kitchen_at:
        from .geom import dir_angle
        ka = dir_angle(room.kitchen_at)
        ax = (math.cos(math.radians(ang)), math.sin(math.radians(ang)))
        kv = (math.cos(math.radians(ka)), math.sin(math.radians(ka)))
        sign = 1 if ax[0] * kv[0] + ax[1] * kv[1] >= 0 else -1
    else:
        # więcej pełnej ściany po stronie kuchni
        best = None
        for sg in (1, -1):
            ex, ey = local(cx, cy, ang, sg * L / 2, 0)
            score = sum(seg.length for seg, l in P.segs if seg.distance(Point(ex, ey)) < max(1.6, Wd * 0.5))
            if best is None or score > best[0]:
                best = (score, sg)
        sign = best[1]
    kl = min(4.6, max(3.4, L * 0.3)) if with_k else 0
    dl = 3.6 if with_d else 0
    if with_k:
        kx, ky = local(cx, cy, ang, sign * (L / 2 - kl / 2), 0)
        zone = Point(kx, ky).buffer(max(kl, Wd) * 0.75)
        segs = [s for s in P.segs if s[0].intersects(zone)]
        cw = min(4.2, max(2.4, Wd - 0.8))
        placed = P.against(counter(cw), prefer="long", segs=segs) if segs else None
        if not placed:
            P.against(counter(min(cw, 3.0)), prefer="long", segs=segs or None)
        isl = island(min(2.6, max(1.6, Wd * 0.45)))
        ix, iy = local(cx, cy, ang, sign * (L / 2 - kl / 2), 0)
        for du in (0, 0.4, -0.4, 0.8):
            for rot in (ang, ang + 90):
                jx, jy = local(cx, cy, ang, sign * (L / 2 - kl / 2) + du, 0)
                if P.try_at(isl, jx, jy, rot):
                    break
            else:
                continue
            break
        else:
            P.near(isl, ix, iy, (ang, ang + 90), radius=2.6)
    if with_d:
        n = 8 if Wd > 4.4 and L > 9 else 6
        dt = dining(n)
        u = sign * (L / 2 - kl - dl / 2) if with_k else 0
        for du in (0, -0.5 * sign, 0.5 * sign, -1.0 * sign):
            done = False
            for rot in (ang, ang + 90):
                jx, jy = local(cx, cy, ang, u + du, 0)
                if P.try_at(dt, jx, jy, rot):
                    done = True
                    break
            if done:
                break
        else:
            jx, jy = local(cx, cy, ang, u, 0)
            if not P.near(dt, jx, jy, (ang, ang + 90), radius=2.4):
                rd = round_dining(0.6, 5)
                P.try_at(rd, jx, jy, 0) or P.near(rd, jx, jy, (0,), radius=2.4)
    if with_l:
        lu = -sign * (L / 2 - max(2.4, (L - kl - dl) / 2)) if (with_k or with_d) else 0
        lx, ly = local(cx, cy, ang, lu, 0)
        _lounge_set(P, lx, ly, ang, min(Wd - 0.6, 4.2))


def _lounge_set(P, lx, ly, ang, span):
    s = sofa(min(2.8, max(2.0, span - 1.2)))
    ok = False
    # kotwica zestawu: podany punkt, a gdy wypada przy ścianie lub poza pokojem – najbliższe dobre miejsce
    anchors = [(lx, ly)]
    for d in (0.4, 0.8, 1.2, 1.6, 2.0, 2.5, 3.0):
        for k in range(8):
            a = math.radians(45 * k)
            anchors.append((lx + d * math.cos(a), ly + d * math.sin(a)))
    for lx, ly in anchors:
        if _lounge_try(P, s, lx, ly, ang):
            ok = True
            break
    if not ok:
        P.center(sofa(2.0))
    # kominek lub rtv na najbliższej pełnej ścianie
    near = sorted(P.segs, key=lambda sg: sg[0].distance(Point(lx, ly)))
    if near:
        P.against(fireplace(), segs=near[:2]) or P.against(tv_unit(), segs=near[:3])


def _lounge_try(P, s, lx, ly, ang):
    ok = False
    for rot in (ang + 90, ang - 90, ang, ang + 180):
        # sofa przodem w stronę stolika
        a = math.radians(rot)
        for off in (0.9, 0.6, 1.2):
            sx, sy = lx - off * (-math.sin(a)), ly - off * math.cos(a)
            if P.fits(s, sx, sy, rot):
                rg = rug(min(3.0, s.w + 0.4), 2.2)
                rg.cx, rg.cy, rg.rot = lx + 0.1 * (-math.sin(a)), ly + 0.1 * math.cos(a), rot
                if P.free.contains(rg.footprint()):
                    P.items.insert(0, rg)
                P.put(s, sx, sy, rot)
                ct = coffee_table(1.1, 0.6)
                P.try_at(ct, lx + 0.35 * (-math.sin(a)), ly + 0.35 * math.cos(a), rot)
                for sd in (-1, 1):
                    fx = lx + sd * (s.w / 2 + 0.2) * math.cos(a) + 0.75 * (-math.sin(a))
                    fy = ly + sd * (s.w / 2 + 0.2) * math.sin(a) + 0.75 * math.cos(a)
                    P.try_at(armchair(), fx, fy, rot + 180 - sd * 35)
                ok = True
                break
        if ok:
            break
    return ok


def r_salon_kuchnia(room, P):
    _kitchen_living(room, P)


def r_salon(room, P):
    _kitchen_living(room, P, with_k=False, with_d=False, with_l=True)
    P.against(shelves(2.4), prefer="long")


def r_kuchnia(room, P):
    # kuchnia przy ogrodzie-jadalni: stół stoi w ogrodzie, w kuchni go nie dublujemy
    jad = any(run.room is room and run.other is not None and run.other.kind == "ogrod"
              and getattr(run.other, "style", None) == "jadalnia" for run in room.house.L[room.level]["runs"])
    _kitchen_living(room, P, with_k=True, with_d=not jad, with_l=False)


def r_jadalnia(room, P):
    cx, cy, ang, L, Wd = frame(P.free)
    n = 8 if L > 4.5 and Wd > 3.4 else 6
    if not P.center(dining(n), rot=ang, shifts=((0, 0), (0.4, 0), (-0.4, 0))):
        P.center(round_dining(0.6, 5))
    P.against(shelves(1.8, 0.45, books=False), prefer="long")


def r_biuro(room, P):
    cx, cy, ang, L, Wd = frame(P.free)
    placed = P.center(desk_pair(1.8), rot=ang + 90, shifts=((0, 0), (0.8, 0), (-0.8, 0), (1.5, 0)))
    if not placed:
        P.center(desk(1.6), rot=ang)
    for _ in range(2):
        P.against(shelves(min(2.4, Wd - 0.4)), prefer="short")
    u = L / 2 - 1.0
    for sg in (1, -1):
        x, y = local(cx, cy, ang, sg * u, 0)
        if P.try_at(armchair(), x, y, ang + 90 * sg):
            P.try_at(round_coffee(0.3), *local(cx, cy, ang, sg * (u - 0.75), 0.5), 0)
            break
    if L > 6:
        P.center(round_dining(0.55, 4), shifts=((-L / 2 + 1.6, 0), (L / 2 - 1.6, 0)))


def r_sypialnia_glowna(room, P):
    b = bed(1.8, 2.1)
    # wezgłowie do pełnej ściany, najlepiej naprzeciw szkła
    if not P.against(b, prefer="short"):
        b = bed(1.6, 2.0)
        if not P.against(b, prefer="long"):
            b = bed(1.6, 2.0)
            cx, cy, ang, L, Wd = frame(P.free)
            if not P.center(b, rot=ang + 90, shifts=((0, 0), (0.8, 0), (-0.8, 0), (0, 0.5), (0, -0.5))):
                P.center(b, rot=ang, shifts=((0, 0), (0.8, 0), (-0.8, 0)))
    cx, cy, ang, L, Wd = frame(P.free)
    P.against(wardrobe(min(2.4, max(1.2, L / 3))), prefer="long")
    for f in (0.85, 0.15):
        x, y = local(cx, cy, ang, (f - 0.5) * L, Wd * 0.25)
        if P.try_at(armchair(), x, y, ang + 200):
            break
    bb = bench(1.4, 0.45)
    if b in P.items:
        x, y = b.world(0, b.d / 2 + 0.35)
        P.try_at(bb, x, y, b.rot)


def r_sypialnia(room, P, w=1.6):
    if not P.against(bed(w, 2.05), prefer="short"):
        P.against(bed(1.4, 2.0, nightstands=False), prefer="long")
    P.against(wardrobe(1.8), prefer="long")
    P.against(desk(1.3), prefer="long")


def r_pokoj(room, P):
    if not P.against(bed(1.2, 2.0, nightstands=False), prefer="long"):
        P.center(bed(0.9, 2.0, nightstands=False))
    P.against(desk(1.4), prefer="long")
    P.against(wardrobe(1.6), prefer="short")
    P.against(shelves(1.2), prefer="short")


def r_gosc(room, P):
    r_sypialnia(room, P, w=1.4)


def r_lazienka(room, P):
    cx, cy, ang, L, Wd = frame(P.free)
    big = L * Wd > 8
    if big and P.free.area > 9:
        if not P.center(bathtub(1.8, 0.85, free=True), rot=ang, shifts=((0, 0), (0.6, 0), (-0.6, 0), (0, 0.4))):
            P.against(bathtub(), prefer="long")
    else:
        P.against(bathtub(), prefer="long")
    P.against(basins(1.4 if big else 0.9, 0.5, 2 if big else 1), prefer="long")
    P.against(wc(), prefer="short")
    P.against(shower(1.0, 1.0), prefer="short", along=0.0) or P.against(shower(0.9, 0.9), prefer="long", along=1.0)


def r_wc(room, P):
    P.against(wc(), prefer="short")
    P.against(basins(0.6, 0.4, 1), prefer="long")


def r_garderoba(room, P):
    for _ in range(4):
        cx, cy, ang, L, Wd = frame(P.free)
        if not P.against(wardrobe(min(2.4, max(1.0, L - 0.4)), 0.6), prefer="long"):
            break
    cx, cy, ang, L, Wd = frame(P.free)
    if Wd > 2.6:
        P.center(Item("wyspa", 1.4, 0.7, [r_(-0.7, -0.35, 1.4, 0.7, 0.04, W)], [("box", 0, 0, 0, 1.4, 0.7, 0.9, "drewno_mebel")], 0.9))


def r_pralnia(room, P):
    for it in (washer(), washer(), counter(1.6, 0.6, sink=True, hob=False), tank()):
        P.against(it, prefer="long")


def r_spizarnia(room, P):
    for _ in range(3):
        if not P.against(shelves(1.8, 0.45, books=False), prefer="long"):
            break


def r_wiatrolap(room, P):
    P.against(wardrobe(min(2.4, 1.8), 0.6), prefer="long")
    P.against(bench(1.4, 0.4), prefer="long")


def r_biblioteka(room, P):
    n = 0
    for _ in range(6):
        cx, cy, ang, L, Wd = frame(P.free)
        if not P.against(shelves(min(3.0, max(1.2, L * 0.45))), prefer="long"):
            break
        n += 1
    cx, cy, ang, L, Wd = frame(P.free)
    for sg in (-1, 1):
        x, y = local(cx, cy, ang, sg * 0.55, 0)
        P.try_at(armchair(0.8), x, y, ang + 90 * sg)
    P.try_at(round_coffee(0.28), cx, cy, 0)
    if L > 5:
        P.center(dining(4, 1.8, 0.9), shifts=((L / 4, 0), (-L / 4, 0)))


def r_pracownia(room, P):
    P.against(workbench(min(3.0, 2.4)), prefer="long")
    P.against(shelves(2.0, 0.4, books=False), prefer="long")
    cx, cy, ang, L, Wd = frame(P.free)
    P.center(easel(), shifts=((0, 0), (1.0, 0), (-1.0, 0)))
    P.center(Item("stolek", 0.5, 0.5, [("c", 0, 0, 0.22, F)], [("cyl", 0, 0, 0, 0.2, 0.6, "tkanina")], 0.6), shifts=((0.8, 0.6), (-0.8, 0.6), (0, 1.0)))


def r_muzyczny(room, P):
    P.center(piano(), shifts=((0, 0), (0.6, 0), (-0.6, 0)))
    P.against(shelves(2.0), prefer="long")
    cx, cy, ang, L, Wd = frame(P.free)
    for sg in (-1, 1):
        P.try_at(armchair(0.75), *local(cx, cy, ang, sg * (L / 2 - 0.8), Wd / 4), ang + 90 * sg)


def r_herbaciarnia(room, P):
    P.center(low_table())
    P.against(Item("tokonoma", 1.6, 0.5, [r_(-0.8, -0.25, 1.6, 0.5, 0.0, W), ("c", 0.4, 0, 0.12, P)], [("box", 0, 0, 0, 1.6, 0.5, 0.25, "drewno_mebel")], 0.25), prefer="short")


def r_silownia(room, P):
    cx, cy, ang, L, Wd = frame(P.free)
    for du in (-0.8, 0.0, 0.8):
        P.try_at(mat(), *local(cx, cy, ang, du, 0), ang + 90)
    P.against(Item("rower", 0.6, 1.4, [r_(-0.3, -0.7, 0.6, 1.4, 0.2, D)], [("box", 0, 0, 0, 0.5, 1.3, 1.1, "czarny_lak")], 1.1), prefer="short")


def r_kino(room, P):
    P.against(Item("ekran", 2.8, 0.2, [r_(-1.4, -0.1, 2.8, 0.2, 0.0, D)], [("box", 0, 0, 0.6, 2.8, 0.1, 1.6, "czarny_lak")], 2.2), prefer="short")
    cx, cy, ang, L, Wd = frame(P.free)
    P.center(sofa(min(3.2, Wd - 0.6), 1.0), shifts=((L * 0.15, 0), (L * 0.25, 0), (0, 0)))


def r_sauna(room, P):
    P.against(sauna_bench(min(2.4, 2.0)), prefer="long")
    P.against(sauna_bench(1.4), prefer="short")
    P.center(stove(), shifts=((0.8, 0.6), (-0.8, 0.6), (0, 0.8)))


def r_warsztat(room, P):
    P.against(workbench(3.0), prefer="long")
    P.against(shelves(2.4, 0.5, books=False), prefer="long")


def r_winiarnia(room, P):
    for _ in range(3):
        if not P.against(wine_rack(1.8), prefer="long"):
            break
    P.center(round_dining(0.45, 4))


def r_galeria(room, P):
    cx, cy, ang, L, Wd = frame(P.free)
    n = max(1, int(L // 3))
    for i in range(n):
        u = -L / 2 + (i + 0.5) * L / n
        P.try_at(plinth(), *local(cx, cy, ang, u, Wd * 0.18), 0)
    P.center(bench(1.8, 0.45), rot=ang, shifts=((0, -Wd * 0.15), (0, 0)))


def r_oranzeria(room, P):
    cx, cy, ang, L, Wd = frame(P.free)
    n = max(2, int(L // 1.6))
    for i in range(n):
        u = -L / 2 + 0.8 + i * (L - 1.6) / max(1, n - 1)
        P.try_at(planter(0.42), *local(cx, cy, ang, u, Wd / 2 - 0.65), 0)
    P.center(bench(1.8), rot=ang, shifts=((0, -0.4), (0, 0)))


def r_korytarz(room, P):
    P.against(shelves(2.0, 0.35), prefer="long")
    P.against(bench(1.6, 0.4), prefer="long")


def r_hol(room, P):
    P.against(wardrobe(2.0, 0.6), prefer="long")
    P.against(bench(1.4, 0.4), prefer="long")


def r_patio(room, P):
    cx, cy, ang, L, Wd = frame(P.free)
    if not P.center(dining(6, 2.0, 0.95), rot=ang, shifts=((L / 4, 0), (0, 0), (-L / 4, 0))):
        P.center(round_dining(0.55, 4))
    for du in (-L / 4, -L / 4 - 0.9):
        P.try_at(lounger(), *local(cx, cy, ang, du, 0), ang)
    P.try_at(planter(0.45, "zielen"), *local(cx, cy, ang, L / 2 - 0.7, Wd / 2 - 0.7), 0)


def r_patio_sezonowe(room, P):
    cx, cy, ang, L, Wd = frame(P.free)
    _lounge_set(P, *local(cx, cy, ang, -L / 4, 0), ang, min(Wd - 0.6, 3.6))
    P.center(dining(6, 2.0, 0.95), rot=ang, shifts=((L / 4, 0), (L / 3, 0)))
    P.try_at(planter(0.4, "cytrus"), *local(cx, cy, ang, L / 2 - 0.6, Wd / 2 - 0.6), 0)


def r_taras(room, P):
    cx, cy, ang, L, Wd = frame(P.free)
    for du in (-0.5, 0.4):
        P.try_at(lounger(), *local(cx, cy, ang, du, 0), ang + 90)
    P.center(round_dining(0.45, 3), shifts=((L / 3, 0), (-L / 3, 0)))
    P.try_at(planter(0.35, "zielen"), *local(cx, cy, ang, L / 2 - 0.5, -Wd / 2 + 0.5), 0)


def r_techniczne(room, P):
    P.against(tank(), prefer="long")
    P.against(Item("pompa", 0.8, 0.6, [r_(-0.4, -0.3, 0.8, 0.6, 0.03, D)], [("box", 0, 0, 0, 0.8, 0.6, 1.0, "ceramika")], 1.0), prefer="long")


def r_garaz(room, P):
    P.center(car())


def r_gabinet(room, P):
    P.against(desk(1.6), prefer="long")
    P.against(shelves(2.4), prefer="long")
    P.center(armchair(), shifts=((0.8, 0.6), (-0.8, 0.6)))


RECIPES = {
    "salon_kuchnia": r_salon_kuchnia, "salon": r_salon, "kuchnia": r_kuchnia, "jadalnia": r_jadalnia,
    "biuro": r_biuro, "sypialnia_glowna": r_sypialnia_glowna, "sypialnia": r_sypialnia, "pokoj": r_pokoj,
    "gosc": r_gosc, "lazienka": r_lazienka, "wc": r_wc, "garderoba": r_garderoba, "pralnia": r_pralnia,
    "spizarnia": r_spizarnia, "wiatrolap": r_wiatrolap, "hol": r_hol, "biblioteka": r_biblioteka,
    "pracownia": r_pracownia, "muzyczny": r_muzyczny, "herbaciarnia": r_herbaciarnia, "silownia": r_silownia,
    "kino": r_kino, "sauna": r_sauna, "warsztat": r_warsztat, "winiarnia": r_winiarnia, "galeria": r_galeria,
    "oranzeria": r_oranzeria, "korytarz": r_korytarz, "patio": r_patio, "patio_sezonowe": r_patio_sezonowe,
    "taras": r_taras, "loggia": r_taras, "techniczne": r_techniczne, "garaz": r_garaz, "gabinet": r_gabinet,
}


# ------------------------------------------------------------ dane o ścianach
def wall_segments(room, level, min_len=0.6):
    """Odcinki obwodu pomieszczenia (netto), przy których stoi ściana pełna bez otworów."""
    net = room.net
    if net is None:
        return []
    # ściany bez wycięć – wysokie okna i pasma pod sufitem nie przeszkadzają meblom, zwykłe otwory odejmujemy niżej
    solid = level.get("wall_geoms") or level["wall_solid"]
    full = unary_union([g for c, g in solid.items() if c in ("ext", "int", "gwall")]) if solid else None
    if full is None or full.is_empty:
        return []
    holes = [o.footprint(extra=0.45) for o in level["openings"] if not (o.kind in ("win", "band") and o.sill >= 1.5)]
    hole = unary_union(holes) if holes else None
    ring = LineString(net.exterior.coords)
    near = full.buffer(0.06)
    good = ring.intersection(near)
    if hole is not None and not hole.is_empty:
        good = good.difference(hole)
    out = []
    for g in _lines(good):
        for part in _straight_parts(g):
            if part.length >= min_len:
                out.append((part, part.length))
    return out


def _lines(g):
    if g.is_empty:
        return []
    if g.geom_type == "LineString":
        return [g]
    if g.geom_type == "MultiLineString":
        from shapely.ops import linemerge
        m = linemerge(g)
        return list(m.geoms) if m.geom_type == "MultiLineString" else [m]
    out = []
    for p in getattr(g, "geoms", []):
        out.extend(_lines(p))
    return out


def _straight_parts(line):
    cs = list(line.coords)
    parts, cur = [], [cs[0]]
    for i in range(1, len(cs)):
        if len(cur) >= 2:
            a, b, c = cur[-2], cur[-1], cs[i]
            a1 = math.atan2(b[1] - a[1], b[0] - a[0])
            a2 = math.atan2(c[1] - b[1], c[0] - b[0])
            d = abs((a2 - a1 + math.pi) % (2 * math.pi) - math.pi)
            if d > math.radians(4):
                parts.append(LineString(cur))
                cur = [b]
        cur.append(cs[i])
    if len(cur) >= 2:
        parts.append(LineString(cur))
    return parts


def door_clearance(room, level):
    zones = []
    for o in level["openings"]:
        if o.kind in ("win", "band"):
            continue
        ln = LineString([o.a, o.b])
        w = max(o.width, 0.8)
        zones.append(ln.buffer(min(0.85, w) + 0.1, cap_style="flat"))
    for fp, s in level.get("voids", []):
        zones.append(fp.buffer(0.15))
    for s in level.get("stairs_here", []):
        fp = s.footprint()
        # strefa przy schodach tylko w pokoju, w którym schody stoją (nie przez ścianę do sąsiada)
        if room.net is not None and fp.intersects(room.net):
            zones.append(fp.buffer(0.6).intersection(room.net.buffer(0.05)))
    return unary_union(zones) if zones else None


def furnish_level(house, idx):
    level = house.L[idx]
    out = []
    # ogród-jadalnia: stół pod szklanym dachem
    for g in level["rooms"]:
        if g.kind == "ogrod" and g.parent is None and getattr(g, "style", None) == "jadalnia":
            lay = getattr(g, "_layout", None)
            if lay is None:
                from .ogrod import garden_layout
                lay = garden_layout(g, level, house)
                g._layout = lay
            st = lay.get("stol")
            if st:
                it = round_dining(r=0.55, n=4) if st["okragly"] else dining(st["n"])
                it.cx, it.cy, it.rot, it.z, it.room = st["cx"], st["cy"], st["rot"], g.z0, g
                out.append(it)
    # ogród z jacuzzi: sofa i stolik na pomoście przodem do wodospadu
    for g in level["rooms"]:
        if g.kind == "ogrod" and g.parent is None and getattr(g, "style", None) == "jacuzzi":
            lay = getattr(g, "_layout", None)
            if lay is None:
                from .ogrod import garden_layout
                lay = garden_layout(g, level, house)
                g._layout = lay
            sl = lay.get("salon")
            if sl:
                sx, sy, rot, w = sl["sofa"]
                it = sofa(w, 0.95)
                it.cx, it.cy, it.rot, it.z, it.room = sx, sy, rot, g.z0 + 0.03, g
                out.append(it)
                tx, ty, trot = sl["stolik"]
                ct = coffee_table(1.2, 0.6)
                ct.cx, ct.cy, ct.rot, ct.z, ct.room = tx, ty, trot, g.z0 + 0.03, g
                out.append(ct)
    for r in level["rooms"]:
        if not r.furn or r.parent is not None or r.kind in ("ogrod", "ogrod_void", "void"):
            continue
        segs = wall_segments(r, level)
        P = Placer(r, r.net, segs, door_clearance(r, level))
        items = furnish(r, P)
        for it in items:
            it.z = r.z0
            it.room = r
        out.extend(items)
    return out
