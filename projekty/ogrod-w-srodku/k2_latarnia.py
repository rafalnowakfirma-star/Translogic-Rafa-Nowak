"""Koncepcja 2 – LATARNIA: ośmiokąt z krętymi schodami w środku pod witrażową latarnią.

Ośmiokąt 12 m (bok do boku). Osiem segmentów wokół rdzenia ze schodami,
jeden segment to otwarte patio z ogrodem. Dach spada do latarni, rynna
pierścieniowa wylewa wodę rzygaczem do patio.
"""
import math

from rysunek import *
from model import Model

C = 6.0
K = math.cos(math.radians(22.5))
T = math.tan(math.radians(22.5))
A_OUT, A_IN = 5.6, 2.1          # lica: wewn. ściany zewnętrznej, zewn. ściany rdzenia
Z_HI, Z_LO = 6.8, 6.2           # lej dachu: krawędź zewnętrzna / pierścień latarni
F1 = 3.3


def V(apo, ang):
    r = apo / K
    a = math.radians(ang)
    return (C + r * math.cos(a), C + r * math.sin(a))


def N(r, ang, t=0.0):
    """Punkt na promieniu kierunku normalnej ang (odległość r), przesunięty t wzdłuż stycznej."""
    a = math.radians(ang)
    return (C + r * math.cos(a) - t * math.sin(a), C + r * math.sin(a) + t * math.cos(a))


def sector(theta, a_in=A_IN, a_out=A_OUT, span=1):
    lo, hi = theta - 22.5, theta - 22.5 + 45 * span
    outer = [V(a_out, lo + 45 * i) for i in range(span + 1)]
    inner = [V(a_in, hi - 45 * i) for i in range(span + 1)]
    return outer + inner


def side(apo, theta, w):
    """Odcinek szerokości w na boku o normalnej theta (od kąta mniejszego do większego)."""
    return N(apo, theta, -w / 2), N(apo, theta, w / 2)


def oct_pts(apo):
    return [V(apo, 22.5 + 45 * k) for k in range(8)]


def patio_garden(p):
    gravel(p, sector(180, A_IN + 0.05, A_OUT - 0.05))
    moss(p, N(4.3, 172), 0.7, 0.5, rot=80)
    maple(p, N(4.1, 194), 0.75)
    stone(p, N(3.4, 166), 0.3)
    stone(p, N(4.7, 186), 0.2)
    basin_stone(p, N(2.55, 180), 0.28)
    chain(p, N(2.55, 180))
    steps(p, [N(3.0, 157), N(3.6, 160), N(4.3, 159)])
    lantern(p, N(5.0, 200))


def ground_plan():
    p = Plan("Latarnia – rzut parteru", -2.6, -2.6, 14.6, 14.6)
    lawn(p, rect_pts(-2.6, -2.6, 14.6, 14.6))
    deck(p, [V(8.4, 22.5), V(8.4, 67.5), V(8.4, 112.5), V(8.4, 157.5), V(6.0, 157.5), V(6.0, 112.5), V(6.0, 67.5), V(6.0, 22.5)])
    p.poly("ground", [N(6.0, 270, -0.8), N(6.0, 270, 0.8), N(8.6, 270, 0.8), N(8.6, 270, -0.8)], "g-path")
    patio_garden(p)
    room(p, sector(270), "stone", "Wejście", at=N(3.9, 270))
    room(p, sector(315), "wood", "Kuchnia", at=N(4.25, 307))
    room(p, sector(0), "wood", "Jadalnia", at=N(2.75, 0))
    room(p, sector(45, span=2), "wood", "Salon", at=N(3.0, 72))
    room(p, sector(135), "wood", "Gabinet", at=N(3.65, 135))
    room(p, sector(225), "stone", "Łazienka", at=N(3.9, 228))
    room(p, oct_pts(1.9), "stone", "Hol", at=N(1.45, 300), area=False, small=True)
    p.text(*N(4.6, 180), "patio", "t-garden", dy=-16)
    p.text(*N(7.3, 90), "taras", "t-garden")
    p.poly("sym", oct_pts(2.0), "sky-proj")
    # meble
    for t in (-1.45, 1.45):
        cx, cy = N(5.25, 270, t)
        wardrobe(p, cx, cy, 1.1, rot=0)
    cx, cy = N(5.3, 315)
    p.item(cx, cy, 315 + 90, [("r", -1.7, -0.3, 3.4, 0.6), ("r", -0.3, -0.2, 0.6, 0.4, 0.05)])
    cx, cy = N(3.75, 315)
    p.item(cx, cy, 315 + 90, [("r", -0.9, -0.4, 1.8, 0.8, 0.04), ("c", -0.3, 0, 0.1), ("c", 0.3, 0, 0.1)])
    round_table(p, *N(3.95, 0), 0.65, 6)
    sofa(p, *N(4.45, 67.5), 2.6, rot=67.5 + 90)
    p.item(*N(3.25, 67.5), 67.5 + 90, [("r", -0.55, -0.35, 1.1, 0.7, 0.05)])
    armchair(p, *N(3.8, 30), rot=30 + 90)
    armchair(p, *N(3.5, 104), rot=104 + 90)
    plant(p, *N(5.0, 22.5), 0.28)
    desk(p, *N(4.9, 135), 1.4, rot=135 + 90)
    sofa(p, *N(3.0, 135), 1.8, rot=135 + 90, d=0.8)
    cx, cy = N(4.85, 212)
    p.item(cx, cy, 212 + 90, [("r", -0.45, -0.45, 0.9, 0.9), ("l", -0.45, -0.45, 0.45, 0.45), ("l", 0.45, -0.45, -0.45, 0.45)])
    wc(p, *N(5.0, 240), rot=240 + 90)
    basin(p, *N(2.75, 226), rot=226 - 90, w=0.7)
    washer(p, *N(4.1, 243), rot=243 + 90)
    # ściany
    wall(p, oct_pts(5.8), 0.4, closed=True)
    for th in (135, 225):
        wall(p, [V(2.0, th - 22.5), V(2.0, th + 22.5)], 0.2, cls="w-inner")
    wall(p, [V(2.0, 247.5), V(2.0, 292.5)], 0.2, cls="w-inner")
    glass(p, [V(2.0, 157.5), V(2.0, 202.5)])
    for ang in (112.5, 247.5, 292.5):
        wall(p, [V(2.0, ang), V(5.8, ang)], 0.15, cls="w-inner")
    for ang in (157.5, 202.5):
        glass(p, [V(2.0, ang), V(5.8, ang)])
    # otwory
    for th, w, kind in ((270, 1.0, "door"), (315, 2.0, "win"), (0, 3.2, "slide"), (45, 3.6, "slide"), (90, 3.6, "slide"),
                        (135, 1.6, "win"), (180, 1.8, "moon"), (225, 0.8, "win")):
        a, b = side(5.8, th, w)
        opening(p, a, b, 0.4, kind, swing=1)
    a, b = side(2.0, 270, 1.2)
    opening(p, a, b, 0.2, "gap")
    for th in (135, 225):
        a, b = side(2.0, th, 0.8)
        opening(p, a, b, 0.2, "door", swing=-1)
    a, b = V(2.0, 157.5), V(5.8, 157.5)
    opening(p, (a[0] + (b[0] - a[0]) * 0.3, a[1] + (b[1] - a[1]) * 0.3),
            (a[0] + (b[0] - a[0]) * 0.75, a[1] + (b[1] - a[1]) * 0.75), 0.13, "slide")
    stair_spiral(p, (C, C), 1.0, 90, 300, 15)
    p.text(*N(6.3, 270), "wejście", "t-note", dy=-14)
    overall_dims(p, 0, 0, 12, 12, off=1.4)
    north_arrow(p, 13.6, -1.6)
    scale_bar(p, 8.8, 13.6)
    return p


def upper_plan():
    p = Plan("Latarnia – rzut piętra", -2.6, -2.6, 14.6, 14.6)
    lawn(p, rect_pts(-2.6, -2.6, 14.6, 14.6))
    deck(p, [V(8.4, 22.5), V(8.4, 67.5), V(8.4, 112.5), V(8.4, 157.5), V(6.0, 157.5), V(6.0, 112.5), V(6.0, 67.5), V(6.0, 22.5)])
    patio_garden(p)
    room(p, sector(270), "stone", "Łazienka", at=N(3.95, 270))
    room(p, sector(315, span=2), "wood", "Sypialnia", at=N(3.35, 340))
    room(p, sector(45, span=2), "tatami", "Dormitorium", at=N(2.85, 67.5))
    room(p, sector(225), "wood", "Garderoba", at=N(3.0, 225), small=True)
    room(p, oct_pts(1.9), "wood", "Galeria", at=N(1.5, 315), area=False, small=True)
    p.area -= math.pi * 1.05 ** 2
    p.poly("floor", sector(135), "f-deck")
    p.text(*N(3.9, 135), "loggia", "t-garden")
    p.text(*N(4.6, 180), "patio", "t-garden", dy=-16)
    p.circle("sym", (C, C), 1.05, "st-void")
    stair_spiral(p, (C, C), 1.0, 90, 300, 15)
    p.circle("sym", (C, C), 1.08, "st-railc")
    p.poly("sym", oct_pts(2.0), "sky-proj")
    p.text(C, C + 1.6, "latarnia z witrażem nad schodami", "t-note")
    # meble
    bed(p, *N(4.55, 318), 1.6, 2.0, rot=318 + 90)
    for th in (306, 330):
        cx, cy = N(5.15, th)
        p.item(cx, cy, th + 90, [("r", -0.25, -0.2, 0.5, 0.4, 0.05)])
    armchair(p, *N(4.4, 6), rot=6 + 90)
    p.item(*N(4.0, 14), 22.5, [("r", -1.0, -0.3, 2.0, 0.6), ("l", -1.0, -0.3, 1.0, 0.3)])
    for th in (32, 54, 77, 100):
        futon(p, *N(4.35, th), rot=th + 90)
    p.item(*N(2.75, 67.5), 67.5 + 90, [("c", 0, 0, 0.35)])
    tub(p, *N(5.05, 270), 0.8, 1.7, rot=270)
    wc(p, *N(5.0, 292), rot=292 + 90)
    basin(p, *N(2.8, 262), rot=262 - 90, w=0.8)
    cx, cy = N(4.6, 248)
    p.item(cx, cy, 248 + 90, [("r", -0.45, -0.45, 0.9, 0.9), ("l", -0.45, -0.45, 0.45, 0.45), ("l", 0.45, -0.45, -0.45, 0.45)])
    wardrobe(p, *N(5.3, 225), 3.2, rot=225 + 90)
    p.item(*N(3.4, 225), 225 + 90, [("r", -0.6, -0.3, 1.2, 0.6, 0.05)])
    armchair(p, *N(4.4, 125), rot=125 + 90)
    armchair(p, *N(4.4, 147), rot=147 + 90)
    plant(p, *N(3.0, 135), 0.25)
    # ściany
    wall(p, [V(5.8, 202.5 + 45 * k) for k in range(7)], 0.4)
    a, b = V(5.8, 112.5), V(5.8, 157.5)
    p.line("walls", a, b, "st-rail")
    wall(p, [V(2.0, 202.5 + 45 * k) for k in range(8)], 0.2, cls="w-inner")
    glass(p, [V(2.0, 157.5), V(2.0, 202.5)])
    for ang in (22.5, 247.5, 292.5):
        wall(p, [V(2.0, ang), V(5.8, ang)], 0.15, cls="w-inner")
    glass(p, [V(2.0, 112.5), V(5.8, 112.5)])
    glass(p, [V(2.0, 202.5), V(5.8, 202.5)])
    p.line("walls", V(2.0, 157.5), V(5.8, 157.5), "st-rail")
    for th, w in ((270, 0.8), (315, 2.4), (0, 1.6), (45, 2.4), (90, 2.4), (225, 0.8)):
        a, b = side(5.8, th, w)
        opening(p, a, b, 0.4, "win")
    for th in (270, 315, 45, 225):
        a, b = side(2.0, th, 0.8)
        opening(p, a, b, 0.2, "door", swing=-1)
    a, b = V(2.0, 112.5), V(5.8, 112.5)
    opening(p, (a[0] + (b[0] - a[0]) * 0.45, a[1] + (b[1] - a[1]) * 0.45),
            (a[0] + (b[0] - a[0]) * 0.8, a[1] + (b[1] - a[1]) * 0.8), 0.13, "slide")
    overall_dims(p, 0, 0, 12, 12, off=1.4)
    north_arrow(p, 13.6, -1.6)
    scale_bar(p, 8.8, 13.6)
    return p


def section():
    s = Sec("Latarnia – przekrój zachód–wschód przez patio i schody", -1.8, 13.8, -1.0, 9.0, s=34, pad_r=100)
    s.rect(-1.8, -1.0, 13.8, -0.3, "s-ground")
    s.line((-1.8, -0.3), (13.8, -0.3), "s-line")
    # patio
    s.rect(0, -0.3, 0.4, 0.6, "s-cut")
    s.rect(0, 2.4, 0.4, 3.0, "s-cut")
    s.rect(0.4, -0.3, 3.9, -0.15, "s-gravel")
    s.tree(2.1, -0.15, 3.6, 1.1, "s-maple")
    s.rect(3.25, -0.15, 3.85, 0.25, "s-stone")
    s.rect(3.35, 0.12, 3.75, 0.25, "s-water")
    s.text(2.0, 0.55, "patio", "t-sroom")
    # płyta
    s.rect(3.9, -0.35, 12.0, 0, "s-cut")
    # rdzeń
    s.rect(3.92, 0, 4.08, 2.9, "s-glass")
    s.rect(3.9, 2.9, 4.1, F1 + 0.3, "s-cut")
    s.rect(3.92, F1 + 0.3, 4.08, Z_LO - 0.15, "s-glass")
    s.rect(3.9, Z_LO - 0.15, 4.1, Z_LO, "s-cut")
    s.rect(7.9, F1, 8.1, Z_LO, "s-cut")
    # schody kręte
    s.line((6.0, 0), (6.0, F1 + 1.0), "s-post")
    for i in range(16):
        z = (i + 1) * F1 / 16
        x0 = 6.0 + 0.95 * math.sin(i * 2 * math.pi * 300 / 360 / 15 + 0.6)
        s.rect(min(6.0, x0), z - 0.05, max(6.0, x0), z, "s-tread")
    s.rect(4.1, F1 - 0.3, 4.95, F1, "s-cut")
    s.rect(7.05, F1 - 0.3, 11.6, F1, "s-cut")
    s.line((4.95, F1 + 1.0), (4.95, F1), "s-thin")
    s.line((7.05, F1 + 1.0), (7.05, F1), "s-thin")
    # skrzydło wschodnie
    s.rect(11.6, -0.35, 12.0, 0.0, "s-cut")
    s.rect(11.75, 0, 11.85, 2.8, "s-glass")
    s.rect(11.6, 2.8, 12.0, 3.9, "s-cut")
    s.rect(11.75, 3.9, 11.85, 5.8, "s-glass")
    s.rect(11.6, 5.8, 12.0, Z_HI - 0.4, "s-cut")
    s.poly([(12.0, Z_HI), (8.1, Z_LO), (8.1, Z_LO - 0.35), (12.0, Z_HI - 0.35)], "s-roof")
    s.flow((11.6, Z_HI + 0.1), (8.6, Z_LO + 0.18))
    # latarnia
    s.rect(3.9, Z_LO, 4.1, 7.4, "s-stained")
    s.rect(7.9, Z_LO, 8.1, 7.4, "s-stained")
    s.poly([(3.85, 7.4), (8.15, 7.4), (6.0, 8.5)], "s-stained")
    s.rect(8.1, Z_LO - 0.15, 8.4, Z_LO, "s-cut")
    s.rect(3.6, Z_LO - 0.15, 3.9, Z_LO, "s-cut")
    s.rect(3.2, Z_LO - 0.12, 3.6, Z_LO - 0.02, "s-cut")
    s.chain(3.55, Z_LO - 0.12, 0.25)
    s.text(9.9, 1.4, "jadalnia", "t-sroom")
    s.text(9.9, 4.6, "sypialnia", "t-sroom")
    s.text(6.0, 4.9, "galeria", "t-note")
    s.person(9.0, 0)
    s.person(2.9, -0.15)
    s.person(11.1, F1)
    s.note(6.0, 7.8, "latarnia z witrażem", 9.0, 8.55)
    s.note(8.25, Z_LO - 0.07, "rynna pierścieniowa", 9.6, 7.55)
    s.note(3.3, Z_LO - 0.07, "rzygacz – woda spada do patio", -1.4, 7.6)
    s.note(6.0, 1.5, "schody kręte", 7.2, 2.5)
    s.note(0.2, 1.5, "okno księżycowe w murze patio", -1.6, 3.6)
    for z, t in ((8.5, "+8,50"), (Z_HI, "+6,80"), (F1, "+3,30"), (0, "±0,00"), (-0.3, "−0,30")):
        s.level(13.4, z, t)
    return s.render()


def panel_side(m, apo, theta, w, z0, z1, kind="glass"):
    a, b = side(apo, theta, w)
    m.panel(a, b, z0, z1, kind)


def model():
    m = Model((C, C), 13)
    main = [V(6.0, 202.5 + 45 * k) for k in range(7)] + [V(2.1, 112.5), V(2.1, 157.5), V(2.1, 202.5)]
    m.prism(main, -0.3, Z_LO, "plaster")
    m.prism(sector(135, 2.1, 6.0), -0.3, F1, "plaster")
    m.flat(sector(135, 2.1, 5.8), F1 + 0.02, "deck")
    cx, cy = V(5.85, 157.5)
    m.box(cx - 0.18, cy - 0.18, F1, cx + 0.18, cy + 0.18, Z_HI, "plaster")
    a, b = side(6.02, 135, 4.6)
    m.panel(a, b, F1, F1 + 1.0, "glass")
    for k in range(8):
        th = 45 * k
        if th == 180:
            continue
        q = sector(th, 2.1, 6.0)
        m.poly([(q[0][0], q[0][1], Z_HI), (q[1][0], q[1][1], Z_HI), (q[2][0], q[2][1], Z_LO), (q[3][0], q[3][1], Z_LO)], "roofcopper")
        m.poly([(q[0][0], q[0][1], Z_LO), (q[1][0], q[1][1], Z_LO), (q[1][0], q[1][1], Z_HI), (q[0][0], q[0][1], Z_HI)], "plaster")
    p1, p2 = V(6.0, 202.5), V(2.1, 202.5)
    m.poly([(p1[0], p1[1], Z_LO), (p1[0], p1[1], Z_HI), (p2[0], p2[1], Z_LO)], "plaster")
    m.lantern(C, C, 2.0, Z_LO, 7.4, 8.5)
    # patio
    a, b = V(5.8, 157.5), V(5.8, 202.5)
    m.moonwall(a, b, -0.3, 3.0, 0.4, 2.4, 1.5, 0.9, "plaster")
    m.flat(sector(180, 2.1, 5.6), -0.2, "gravel")
    m.panel(V(2.12, 157.5), V(5.6, 157.5), 0.0, 2.9)
    m.panel(V(2.12, 202.5), V(5.6, 202.5), 0.0, Z_LO - 0.1)
    m.panel(V(2.12, 157.5), V(2.12, 202.5), 0.0, Z_LO - 0.1)
    m.tree(*N(4.1, 194), 3.6, 1.0, "maple")
    m.add(t="ellipse", x=N(4.3, 172)[0], y=N(4.3, 172)[1], rx=0.7, ry=0.5, z=-0.17, m="moss")
    m.stone(*N(3.4, 166), 0.3)
    m.stone(*N(4.7, 186), 0.2)
    m.toro(*N(5.0, 200))
    bx, by = N(2.55, 180)
    m.stone(bx, by, 0.3, 0.35)
    m.box(C - 2.6, C - 0.1, Z_LO - 0.15, C - 2.1, C + 0.1, Z_LO - 0.02, "copper")
    m.chain(C - 2.5, C, 0.15, Z_LO - 0.15)
    # okna
    for th, w, z0, z1, kind in ((270, 1.0, -0.25, 2.3, "door"), (315, 2.0, 0.9, 2.4, "glass"), (0, 3.2, 0.05, 2.8, "glass"),
                                (45, 3.6, 0.05, 2.8, "glass"), (90, 3.6, 0.05, 2.8, "glass"), (135, 1.6, 0.8, 2.4, "glass"),
                                (225, 0.8, 1.4, 2.4, "dark"), (270, 0.8, 4.4, 5.6, "dark"), (315, 2.4, 3.8, 5.8, "glass"),
                                (0, 1.6, 3.8, 5.8, "glass"), (45, 2.4, 3.8, 5.8, "glass"), (90, 2.4, 3.8, 5.8, "glass"),
                                (225, 0.8, 4.4, 5.6, "dark")):
        panel_side(m, 6.02, th, w, z0, z1, kind)
    m.flat([V(8.4, 22.5), V(8.4, 67.5), V(8.4, 112.5), V(8.4, 157.5), V(6.0, 157.5), V(6.0, 112.5), V(6.0, 67.5), V(6.0, 22.5)], -0.12, "deck")
    m.flat([N(6.0, 270, -0.8), N(6.0, 270, 0.8), N(9.5, 270, 0.8), N(9.5, 270, -0.8)], -0.28, "stone")
    m.tree(-2.5, 1.0, 8, 2.0, "pine")
    m.tree(15.0, 3.0, 6.5, 2.0, "round")
    m.tree(-1.5, 13.5, 5, 1.4, "birch")
    m.tree(14.0, 14.0, 4.5, 1.4, "maple")
    m.person(*N(7.2, 70), -0.12)
    return m.d


def build():
    g, u = ground_plan(), upper_plan()
    return {"plans": [g.render(), u.render()], "section": section(), "model": model(), "areas": (g.area, u.area)}
