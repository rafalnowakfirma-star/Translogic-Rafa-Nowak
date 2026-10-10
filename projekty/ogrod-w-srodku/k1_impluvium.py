"""Koncepcja 1 – IMPLUVIUM: dom na planie kwadratu wokół japońskiego ogrodu.

Kwadrat 14 × 14 m, dziedziniec 4,8 × 4,8 m. Korytarz-bufor od północy, wschodu
i zachodu. Dachy niskich skrzydeł spadają lejem do ogrodu, a woda schodzi
łańcuchami deszczowymi. Piętro tylko nad skrzydłem północnym.
"""
from rysunek import *
from model import Model

S = 14.0
CY = (4.6, 4.8, 9.4, 9.6)          # dziedziniec x1, y1, x2, y2
GW = 1.575                          # oś ściany galerii
N_SOUTH = 5.15                      # lico pd. ściany piętra (skrzydło północne)
Z_N_HI, Z_N_LO = 7.0, 6.5           # dach skrzydła północnego (północ / ogród)
Z_HI, Z_LO = 3.9, 3.3               # lej niskich skrzydeł: krawędź zewn. / przy ogrodzie
F1 = 3.4                            # posadzka piętra


def garden(p, light=False):
    x1, y1, x2, y2 = CY
    gravel(p, rect_pts(x1 + 0.06, y1 + 0.06, x2 - 0.06, y2 - 0.06))
    pond_ellipse(p, (7.0, 5.6), 0.95, 0.45)
    moss(p, (5.8, 6.5), 1.0, 0.75, rot=-15)
    stone(p, (8.3, 6.6), 0.35)
    stone(p, (7.95, 8.45), 0.27, rot=30)
    stone(p, (6.1, 8.65), 0.22)
    steps(p, [(7.0, 9.25), (6.75, 8.7), (7.05, 8.12), (6.8, 7.55), (7.0, 6.95), (6.85, 6.35)])
    maple(p, (5.9, 6.4), 0.85)
    lantern(p, (8.85, 5.35))
    bamboo(p, (5.0, 5.25))
    basin_stone(p, (4.95, 9.25), 0.22)
    basin_stone(p, (9.05, 9.25), 0.22)
    chain(p, (7.0, 5.05))
    chain(p, (4.75, 9.45))
    chain(p, (9.25, 9.45))


def ground_plan():
    p = Plan("Impluvium – rzut parteru", -1.4, -1.6, 15.2, 16.4)
    lawn(p, rect_pts(-1.4, -1.6, 15.2, 16.4))
    deck(p, rect_pts(0.6, 14.0, 9.4, 16.1))
    deck(p, rect_pts(9.4, 9.9, 14.0, 14.0))
    garden(p)
    # pomieszczenia
    room(p, [(0.4, 0.4), (13.6, 0.4), (13.6, 9.6), (12.5, 9.6), (12.5, 1.65), (1.5, 1.65), (1.5, 9.6), (0.4, 9.6)],
         "stone", "Galeria – bufor", at=(7.0, 1.0))
    room(p, rect_pts(1.65, 1.65, 4.6, 4.8), "wood", "Hol", at=(3.25, 1.98), small=True)
    room(p, rect_pts(4.6, 1.65, 9.4, 4.8), "wood", "Kuchnia z jadalnią", at=(7.0, 2.45))
    room(p, rect_pts(9.4, 1.65, 12.35, 4.8), "stone", "Pralnia", at=(10.9, 3.35))
    room(p, rect_pts(1.65, 4.8, 4.6, 9.6), "wood", "Pokój gościnny", at=(3.1, 6.35))
    room(p, rect_pts(9.4, 4.8, 12.35, 9.6), "stone", "Łazienka ofuro", at=(10.85, 6.45))
    room(p, rect_pts(0.4, 9.6, 9.4, 13.6), "wood", "Salon", at=(6.9, 12.95))
    p.text(7.0, 7.25, "ogród", "t-garden")
    p.text(11.8, 12.1, "loggia", "t-garden")
    p.text(5.0, 15.3, "taras", "t-garden")
    # meble
    wardrobe(p, 1.6, 0.7, 2.2)
    box(p, 0.45, 2.6, 0.85, 4.6)
    for y in (5.0, 6.6, 8.0):
        box(p, 0.4, y, 0.75, y + 1.2)
    counter(p, 4.8, 1.65, 9.3, 2.25, sink=(6.2, 1.95), hob=(8.0, 1.95))
    table(p, 7.0, 3.65, 2.8, 0.9)
    washer(p, 9.85, 1.98)
    washer(p, 10.5, 1.98)
    p.item(11.9, 2.35, 0, [("c", 0, 0, 0.3), ("c", 0, 0, 0.18)])
    box(p, 11.75, 3.0, 12.35, 4.6)
    bed(p, 2.7, 8.1, 1.4, 2.0, rot=-90)
    desk(p, 2.4, 5.35, 1.2, rot=0)
    armchair(p, 4.0, 5.5, rot=-30)
    shower(p, 11.35, 4.8, 12.35, 5.8)
    p.item(11.7, 6.35, 0, [("r", -0.5, -0.18, 1.0, 0.36, 0.05), ("c", -0.7, 0, 0.14)])
    ofuro(p, 10.25, 7.8)
    wc(p, 12.05, 7.6, rot=-90)
    basin(p, 11.6, 9.3, rot=180, w=1.2)
    sofa(p, 3.3, 12.9, 2.6, rot=180)
    sofa(p, 1.55, 11.6, 1.8, rot=90)
    low_table(p, 3.3, 11.4, 1.1, 0.7)
    fireplace(p, 0.65, 11.1, rot=90)
    armchair(p, 5.6, 11.0, rot=200)
    round_table(p, 7.6, 11.6, 0.45, 4)
    p.item(11.8, 11.4, 0, [("r", -0.9, -0.4, 1.8, 0.8, 0.1), ("r", -0.9, -0.4, 1.8, 0.2, 0.05)])
    p.item(11.8, 12.6, 0, [("c", 0, 0, 0.35)])
    # ściany
    wall(p, [(13.8, 9.9), (13.8, 0.2), (0.2, 0.2), (0.2, 13.8), (9.5, 13.8)], 0.4)
    wall(p, [(9.34, 9.75), (14.0, 9.75)], 0.3)
    p.poly("walls", rect_pts(13.6, 13.6, 14.0, 14.0), "w-col")
    wall(p, [(GW, 9.6), (GW, GW), (S - GW, GW), (S - GW, 9.6)], 0.15, cls="w-inner")
    for a, b in (((1.5, 4.8), (4.6, 4.8)), ((9.4, 1.65), (9.4, 4.8)), ((9.4, 4.8), (12.5, 4.8)), ((1.5, 9.6), (4.6, 9.6))):
        wall(p, [a, b], 0.12, cls="w-part")
    x1, y1, x2, y2 = CY
    glass(p, rect_pts(x1, y1, x2, y2), closed=True)
    glass(p, [(9.4, 9.75), (9.4, 13.8)])
    # otwory
    opening(p, (2.6, 0.2), (3.6, 0.2), 0.4, "door", swing=1)
    for a in (6.2, 8.2, 10.8):
        opening(p, (a, 0.2), (a + 0.6, 0.2), 0.4, "win")
    for a in (5.6, 7.6):
        opening(p, (0.2, a), (0.2, a + 0.6), 0.4, "win")
    opening(p, (0.2, 10.6), (0.2, 12.6), 0.4, "win")
    for a in (3.0, 6.6):
        opening(p, (13.8, a), (13.8, a + 0.6), 0.4, "win")
    opening(p, (1.2, 13.8), (8.4, 13.8), 0.4, "slide")
    opening(p, (2.0, GW), (3.4, GW), 0.15, "gap")
    opening(p, (11.0, GW), (11.8, GW), 0.15, "door", swing=1)
    opening(p, (GW, 6.0), (GW, 6.9), 0.15, "door", swing=-1)
    opening(p, (S - GW, 5.6), (S - GW, 6.4), 0.15, "door", swing=1)
    opening(p, (9.4, 3.7), (9.4, 4.5), 0.12, "door", swing=-1)
    opening(p, (12.6, 9.75), (13.5, 9.75), 0.3, "door", swing=1)
    opening(p, (5.2, 4.8), (8.8, 4.8), 0.13, "slide")
    opening(p, (4.6, 5.6), (4.6, 8.8), 0.13, "slide")
    opening(p, (9.4, 5.6), (9.4, 8.8), 0.13, "slide")
    opening(p, (5.2, 9.6), (8.8, 9.6), 0.13, "slide")
    opening(p, (9.4, 10.2), (9.4, 13.2), 0.13, "slide")
    # schody dwubiegowe w holu
    p.poly("sym", rect_pts(1.65, 2.45, 2.65, 4.55), "st-box")
    stair_straight(p, 2.65, 3.55, 4.54, 4.55, "W", 7)
    stair_straight(p, 2.65, 2.45, 4.54, 3.45, "E", 7)
    p.text(3.1, 0.1, "wejście", "t-note", dy=-6)
    overall_dims(p, 0, 0, S, S)
    north_arrow(p, 14.7, -0.9)
    scale_bar(p, 9.8, 15.6)
    return p


def upper_plan():
    p = Plan("Impluvium – rzut piętra", -1.4, -1.6, 15.2, 16.4)
    lawn(p, rect_pts(-1.4, -1.6, 15.2, 16.4))
    deck(p, rect_pts(0.6, 14.0, 9.4, 16.1))
    # dachy niskich skrzydeł (widok z góry) i ogród
    roofs = [[(0, N_SOUTH), (4.6, N_SOUTH), (4.6, 9.6), (0, 14)],
             [(0, 14), (4.6, 9.6), (9.4, 9.6), (14, 14)],
             [(14, N_SOUTH), (14, 14), (9.4, 9.6), (9.4, N_SOUTH)]]
    for r in roofs:
        p.poly("ground", r, "roof-below")
    for a, b in (((1.1, 7.6), (3.9, 7.6)), ((12.9, 7.6), (10.1, 7.6)), ((7.0, 13.2), (7.0, 10.3))):
        (x1, y1), (x2, y2) = p.P(*a), p.P(*b)
        p.L["ground"].append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" class="flow" marker-end="url(#arrow-w)"/>')
    p.text(2.3, 8.2, "dach spada do ogrodu", "t-note")
    garden(p)
    room(p, rect_pts(0.4, 0.4, 10.6, 1.5), "stone", "Korytarz z szafami", at=(7.6, 1.0), small=True)
    a = room(p, rect_pts(0.4, 1.65, 5.6, 4.75), "wood", "Hol", at=(5.05, 3.0), small=True)
    p.area -= (4.54 - 1.65) * (4.55 - 2.45)
    room(p, rect_pts(5.72, 1.65, 8.8, 4.75), "tatami", "Dormitorium", at=(7.26, 4.25))
    room(p, rect_pts(8.92, 1.65, 10.6, 4.75), "stone", "Łazienka", at=(9.76, 3.4), small=True)
    room(p, rect_pts(10.72, 0.4, 13.6, 4.75), "wood", "Sypialnia", at=(12.15, 3.55))
    void(p, rect_pts(1.65, 2.45, 4.54, 4.55))
    stair_straight(p, 2.65, 2.45, 4.54, 3.45, "E", 7)
    p.poly("sym", rect_pts(1.75, 2.0, 4.45, 4.65), "sky-proj")
    p.text(3.1, 4.68, "witraż w dachu", "t-note", dy=-3)
    # meble
    for x in (0.6, 2.4, 6.0, 7.8):
        wardrobe(p, x + 0.8, 0.7, 1.6)
    for x in (6.2, 7.26, 8.32):
        futon(p, x, 2.85)
    p.item(7.26, 4.3, 0, [("r", -0.45, -0.22, 0.9, 0.44, 0.04)])
    shower(p, 8.92, 1.65, 9.82, 2.55)
    wc(p, 10.3, 2.05)
    basin(p, 9.76, 4.48, rot=180, w=0.9)
    bed(p, 12.3, 1.5, 1.6, 2.0)
    wardrobe(p, 11.0, 1.2, 1.6, rot=90)
    armchair(p, 13.05, 4.2, rot=200)
    # ściany
    wall(p, [(0.2, 0.2), (13.8, 0.2), (13.8, 4.95), (0.2, 4.95)], 0.4, closed=True)
    wall(p, [(0.4, GW), (10.66, GW)], 0.15, cls="w-inner")
    for x, y0 in ((5.66, 1.65), (8.86, 1.65), (10.66, 0.4)):
        wall(p, [(x, y0), (x, 4.75)], 0.12, cls="w-part")
    opening(p, (1.7, GW), (5.5, GW), 0.15, "gap")
    opening(p, (6.0, GW), (6.9, GW), 0.15, "door", swing=1)
    opening(p, (9.0, GW), (9.8, GW), 0.15, "door", swing=1)
    opening(p, (10.66, 0.5), (10.66, 1.4), 0.12, "door", swing=-1)
    for a in (3.0, 6.2, 8.2):
        opening(p, (a, 0.2), (a + 0.6, 0.2), 0.4, "win")
    opening(p, (11.6, 0.2), (12.8, 0.2), 0.4, "win")
    opening(p, (13.8, 1.6), (13.8, 3.6), 0.4, "win")
    opening(p, (0.2, 2.6), (0.2, 3.4), 0.4, "win")
    for a, b in ((2.0, 5.3), (6.0, 8.5), (9.1, 10.4), (11.0, 13.3)):
        opening(p, (a, 4.95), (b, 4.95), 0.4, "win")
    p.line("sym", (1.65, 2.45), (2.65, 2.45), "st-rail")
    overall_dims(p, 0, 0, S, S)
    north_arrow(p, 14.7, -0.9)
    scale_bar(p, 9.8, 15.6)
    return p


def section():
    s = Sec("Impluvium – przekrój północ–południe przez ogród", -1.6, 16.6, -1.0, 7.6, s=33, pad_r=96)
    s.rect(-1.6, -1.0, 16.6, -0.3, "s-ground")
    s.line((-1.6, -0.3), (16.6, -0.3), "s-line")
    # płyta
    s.rect(0, -0.35, 4.75, 0, "s-cut")
    s.rect(9.6, -0.35, 14.0, 0, "s-cut")
    # ogród
    s.rect(4.75, -0.3, 9.6, -0.15, "s-gravel")
    s.rect(5.15, -0.45, 6.15, -0.15, "s-water")
    s.text(6.2, 0.1, "staw", "t-note")
    s.tree(8.0, -0.15, 0.6, 0.28, "s-stone")
    s.rect(8.75, -0.15, 8.95, 0.9, "s-beyond")
    s.rect(8.65, 0.9, 9.05, 1.15, "s-beyond")
    # skrzydło północne
    s.rect(0, 0, 0.4, 6.65, "s-cut")
    s.rect(1.5, 0, 1.65, 3.1, "s-cut")
    s.rect(1.5, F1, 1.65, 6.3, "s-cut")
    s.rect(0.4, 3.1, N_SOUTH, F1, "s-cut")
    s.rect(4.75, 0, 4.85, 2.8, "s-glass")
    s.rect(4.75, 2.8, 4.85, 3.1, "s-cut")
    s.rect(4.75, F1, N_SOUTH, 3.6, "s-cut")
    s.rect(4.9, 3.6, 5.0, 5.9, "s-glass")
    s.rect(4.75, 5.9, N_SOUTH, 6.15, "s-cut")
    roof_n = [(0, Z_N_HI), (N_SOUTH + 0.15, Z_N_LO), (N_SOUTH + 0.15, Z_N_LO - 0.35), (0, Z_N_HI - 0.35)]
    s.poly(roof_n, "s-roof")
    s.rect(N_SOUTH, Z_N_LO - 0.2, N_SOUTH + 0.3, Z_N_LO - 0.05, "s-cut")
    s.chain(N_SOUTH + 0.15, Z_N_LO - 0.2, -0.15)
    s.flow((0.8, Z_N_HI + 0.12), (4.4, Z_N_LO + 0.2))
    # skrzydło południowe
    s.rect(9.55, 0, 9.65, 2.7, "s-glass")
    s.rect(9.5, 2.7, 9.7, Z_LO - 0.35, "s-cut")
    s.rect(13.6, 0, 14.0, 0.05, "s-cut")
    s.rect(13.75, 0.05, 13.85, 2.9, "s-glass")
    s.rect(13.6, 2.9, 14.0, Z_HI - 0.35, "s-cut")
    s.poly([(9.4, Z_LO), (14.0, Z_HI), (14.0, Z_HI - 0.35), (9.4, Z_LO - 0.35)], "s-roof")
    s.rect(9.25, Z_LO - 0.2, 9.5, Z_LO - 0.05, "s-cut")
    s.flow((13.4, Z_HI + 0.1), (10.0, Z_LO + 0.12))
    s.rect(14.0, -0.3, 16.1, -0.15, "s-deck")
    # opisy
    s.text(0.95, 1.4, "galeria", "t-note")
    s.text(0.95, 4.7, "korytarz", "t-note")
    s.text(3.2, 1.3, "kuchnia", "t-sroom")
    s.text(3.25, 4.6, "dormitorium", "t-sroom")
    s.text(7.4, 2.4, "ogród", "t-sroom")
    s.text(11.7, 1.3, "salon", "t-sroom")
    s.text(15.1, 0.25, "taras", "t-note")
    s.person(12.4, 0)
    s.person(7.6, -0.15)
    s.person(4.3, F1)
    s.note(N_SOUTH + 0.15, 3.0, "łańcuch deszczowy ok. 6,5 m", 6.6, 4.9)
    s.note(9.38, Z_LO - 0.12, "rynna koszowa przy ogrodzie", 9.9, 5.5)
    s.note(1.0, 5.6, "bufor od zimnej północy", 1.7, 7.25)
    for z, t in ((Z_N_HI, "+7,00"), (Z_HI, "+3,90"), (F1, "+3,40"), (0, "±0,00"), (-0.3, "−0,30")):
        s.level(16.3, z, t)
    return s.render()


def model():
    m = Model((7.0, 7.5), 15)
    # skrzydła
    m.box(0, 0, -0.3, 14, N_SOUTH, Z_N_LO, "wall")
    m.box(0, N_SOUTH, -0.3, 4.6, 9.6, Z_LO, "wall")
    m.box(9.4, N_SOUTH, -0.3, 14, 9.9, Z_LO, "wall")
    m.box(0, 9.6, -0.3, 9.4, 14, Z_LO, "wall")
    m.box(13.6, 13.6, -0.3, 14, 14, Z_HI, "wall")
    m.flat([(9.4, 9.9), (14, 9.9), (14, 14), (9.4, 14)], -0.12, "deck")
    m.flat([(0.6, 14), (9.4, 14), (9.4, 16.1), (0.6, 16.1)], -0.15, "deck")
    # dach północny i obróbki
    m.poly([(0, 0, Z_N_HI), (14, 0, Z_N_HI), (14, N_SOUTH, Z_N_LO), (0, N_SOUTH, Z_N_LO)], "roof")
    m.fascia([(0, 0, Z_N_HI), (14, 0, Z_N_HI)], Z_N_LO, "wall")
    m.poly([(0, 0, Z_N_LO), (0, 0, Z_N_HI), (0, N_SOUTH, Z_N_LO)], "wall")
    m.poly([(14, 0, Z_N_LO), (14, N_SOUTH, Z_N_LO), (14, 0, Z_N_HI)], "wall")
    # lej niskich dachów
    W = [(0, N_SOUTH, Z_HI), (0, 14, Z_HI), (4.6, 9.6, Z_LO), (4.6, N_SOUTH, Z_LO)]
    Sth = [(0, 14, Z_HI), (14, 14, Z_HI), (9.4, 9.6, Z_LO), (4.6, 9.6, Z_LO)]
    E = [(14, N_SOUTH, Z_HI), (9.4, N_SOUTH, Z_LO), (9.4, 9.6, Z_LO), (14, 14, Z_HI)]
    for r in (W, Sth, E):
        m.poly(r, "roof")
    m.fascia([(0, N_SOUTH, Z_HI), (0, 14, Z_HI), (14, 14, Z_HI), (14, N_SOUTH, Z_HI)], Z_LO, "wall")
    # witraż w dachu nad schodami
    def zr(y):
        return Z_N_HI - (Z_N_HI - Z_N_LO) * y / N_SOUTH + 0.04
    m.stained([(1.8, 2.0, zr(2.0)), (4.4, 2.0, zr(2.0)), (4.4, 4.5, zr(4.5)), (1.8, 4.5, zr(4.5))], "rect")
    # przeszklenia od ogrodu
    m.panel((4.75, 9.55), (9.25, 9.55), 0.05, 2.75)
    m.panel((4.65, 5.25), (4.65, 9.45), 0.05, 2.75)
    m.panel((9.35, 9.45), (9.35, 5.25), 0.05, 2.75)
    m.panel((9.25, N_SOUTH + 0.02), (4.75, N_SOUTH + 0.02), 0.05, 2.8)
    for a, b, z0, z1 in ((2.0, 5.3, 4.0, 6.0), (6.0, 8.5, 3.6, 5.9), (9.1, 10.4, 4.6, 5.9), (11.0, 13.3, 4.1, 6.0)):
        m.panel((b, N_SOUTH + 0.02), (a, N_SOUTH + 0.02), z0, z1)
    # okna zewnętrzne
    m.panel((1.2, 14.02), (8.4, 14.02), 0.05, 2.9)
    m.panel((9.42, 10.2), (9.42, 13.2), 0.05, 2.9)
    for a in (2.6,):
        m.panel((a + 1.0, -0.02), (a, -0.02), -0.25, 2.3, "door")
    for a in (6.2, 8.2, 10.8):
        m.panel((a + 0.6, -0.02), (a, -0.02), 0.6, 2.6, "dark")
        m.panel((a + 0.6, -0.02), (a, -0.02), 4.0, 6.2, "dark")
    for a in (5.6, 7.6):
        m.panel((-0.02, a), (-0.02, a + 0.6), 0.6, 2.6, "dark")
    m.panel((-0.02, 10.6), (-0.02, 12.6), 0.5, 2.6)
    m.panel((-0.02, 2.6), (-0.02, 3.4), 4.0, 6.0, "dark")
    for a in (3.0, 6.6):
        m.panel((14.02, a + 0.6), (14.02, a), 0.6, 2.6, "dark")
    m.panel((14.02, 3.6), (14.02, 1.6), 4.0, 6.0)
    # ogród
    m.flat([(4.66, 4.86), (9.34, 4.86), (9.34, 9.54), (4.66, 9.54)], -0.2, "gravel")
    m.add(t="ellipse", x=7.0, y=5.6, rx=0.95, ry=0.45, z=-0.17, m="water")
    m.add(t="ellipse", x=5.8, y=6.5, rx=1.0, ry=0.75, z=-0.16, m="moss")
    m.tree(5.9, 6.4, 3.2, 1.0, "maple")
    m.stone(8.3, 6.6, 0.35)
    m.stone(7.95, 8.45, 0.27)
    m.stone(6.1, 8.65, 0.22)
    m.toro(8.85, 5.35)
    m.bamboo(5.0, 5.25)
    m.chain(7.0, N_SOUTH + 0.12, -0.2, Z_N_LO)
    m.chain(4.75, 9.45, -0.2, Z_LO)
    m.chain(9.25, 9.45, -0.2, Z_LO)
    for x, y in ((7.0, 9.25), (6.75, 8.7), (7.05, 8.12), (6.8, 7.55), (7.0, 6.95)):
        m.add(t="ellipse", x=x, y=y, rx=0.24, ry=0.18, z=-0.15, m="stone")
    # otoczenie
    m.tree(-3.5, 4.0, 7, 2.0, "round")
    m.tree(17.5, 2.0, 8, 2.3, "pine")
    m.tree(16.5, 17.0, 6, 1.8, "round")
    m.tree(-2.0, 16.5, 5, 1.5, "birch")
    m.person(4.5, 15.0, -0.15)
    return m.d


def build():
    g, u = ground_plan(), upper_plan()
    return {
        "plans": [g.render(), u.render()],
        "section": section(),
        "model": model(),
        "areas": (g.area, u.area),
    }
