"""Koncepcja 3 – MOST: dwa skrzydła z czarnego drewna i biała sypialnia-most nad wejściem.

Skrzydło dzienne (zachód) i nocne (wschód) obejmują ogród zamknięty murem
z bramą księżycową. Korytarz-bufor biegnie po zewnętrznej stronie skrzydeł.
Skrzydła mają dachy motyle z rynną w środku, most – dach spadający do ogrodu.
"""
from rysunek import *
from model import Model

GW_W, GW_N, GW_E = 1.575, 1.575, 15.625
F1 = 3.4
Z_W_HI, Z_W_LO = 4.0, 3.4        # dach motyli: krawędzie / rynna
Z_B_N, Z_B_S = 6.9, 6.4          # dach mostu: północ / ogród
STAIR = (6.2, 2.55, 10.25, 3.55)


def garden(p):
    deck(p, rect_pts(6.0, 4.5, 12.0, 5.4))
    deck(p, rect_pts(6.0, 5.4, 6.9, 10.8))
    deck(p, rect_pts(11.1, 5.4, 12.0, 10.8))
    gravel(p, rect_pts(6.9, 5.4, 11.1, 10.8))
    pond_ellipse(p, (9.0, 7.25), 1.4, 0.75, rot=-8)
    basin_stone(p, (9.0, 5.85), 0.25)
    chain(p, (9.0, 5.85))
    stone(p, (10.4, 6.2), 0.3)
    stone(p, (10.35, 8.6), 0.22, rot=40)
    moss(p, (10.4, 9.6), 0.8, 0.6, rot=20)
    maple(p, (10.45, 9.45), 0.8)
    pine(p, (7.45, 9.85), 0.55)
    lantern(p, (7.6, 6.0))
    bamboo(p, (7.2, 10.45), 8, 0.3)
    bamboo(p, (10.9, 10.45), 8, 0.3)
    steps(p, [(7.4, 6.6), (7.5, 7.3), (7.7, 8.0), (8.1, 8.65), (8.55, 9.25), (8.9, 9.85), (9.0, 10.45)])


def ground_plan():
    p = Plan("Most – rzut parteru", -1.6, -1.8, 18.8, 13.8)
    lawn(p, rect_pts(-1.6, -1.8, 18.8, 13.8))
    deck(p, rect_pts(0.0, 11.0, 6.0, 13.2))
    p.poly("ground", rect_pts(8.4, -1.8, 9.6, 0.0), "g-path")
    garden(p)
    room(p, [(0.4, 0.4), (16.8, 0.4), (16.8, 10.6), (15.7, 10.6), (15.7, 1.65), (1.5, 1.65), (1.5, 10.6), (0.4, 10.6)],
         "stone", "Galeria – bufor", at=(4.4, 1.0))
    room(p, rect_pts(1.65, 1.65, 3.3, 3.25), "stone", "Spiżarnia", at=(2.47, 2.45), small=True, area=False)
    room(p, [(3.3, 1.65), (5.94, 1.65), (5.94, 10.6), (1.65, 10.6), (1.65, 3.25), (3.3, 3.25)], "wood",
         "Kuchnia, jadalnia, salon", at=(3.8, 6.45))
    a = room(p, rect_pts(5.94, 1.65, 12.06, 4.44), "wood", "Hol ze schodami", at=(9.0, 4.05), small=True)
    room(p, rect_pts(12.06, 1.65, 15.55, 4.2), "stone", "Łazienka", at=(13.4, 3.55))
    room(p, rect_pts(12.06, 4.2, 15.55, 7.4), "wood", "Pokój", at=(13.8, 6.4))
    room(p, rect_pts(12.06, 7.4, 15.55, 10.6), "tatami", "Dormitorium", at=(13.8, 9.85))
    p.text(9.0, 8.55, "ogród", "t-garden")
    p.text(9.0, 4.98, "engawa", "t-garden")
    p.text(3.0, 12.3, "taras", "t-garden")
    # meble
    counter(p, 3.4, 1.65, 5.9, 2.25, sink=(4.0, 1.95), hob=(5.2, 1.95))
    counter(p, 1.65, 3.4, 2.25, 4.8)
    p.item(3.9, 3.7, 0, [("r", -0.9, -0.4, 1.8, 0.8, 0.04)])
    table(p, 3.8, 5.6, 2.2, 0.9, rot=90)
    sofa(p, 2.1, 8.5, 2.6, rot=90)
    low_table(p, 3.4, 8.5, 0.7, 1.1, rot=0)
    armchair(p, 4.9, 9.7, rot=225)
    fireplace(p, 1.9, 10.3, rot=0)
    for y in (2.6, 4.6, 6.6):
        box(p, 0.4, y, 0.75, y + 1.4)
    wardrobe(p, 7.0, 0.7, 2.2)
    wardrobe(p, 11.0, 0.7, 2.2)
    shower(p, 14.6, 1.65, 15.55, 2.6)
    tub(p, 13.0, 2.15, 0.8, 1.7, rot=90)
    wc(p, 15.2, 3.65, rot=-90)
    basin(p, 12.3, 3.5, rot=90, w=0.9)
    desk(p, 12.6, 5.0, 1.2, rot=90)
    bed(p, 14.4, 6.0, 1.2, 2.0, rot=90)
    for y in (8.0, 9.0, 10.0):
        futon(p, 14.4, y, rot=90)
    p.item(12.8, 9.0, 0, [("r", -0.3, -0.5, 0.6, 1.0, 0.05)])
    for y in (5.0, 7.0, 9.0):
        box(p, 16.45, y, 16.8, y + 1.4)
    # ściany
    wall(p, [(5.8, 10.8), (0.2, 10.8), (0.2, 0.2), (17.0, 0.2), (17.0, 10.8), (12.2, 10.8)], 0.4)
    wall(p, [(GW_W, 10.6), (GW_W, GW_N), (GW_E, GW_N), (GW_E, 10.6)], 0.15, cls="w-inner")
    for a_, b_ in (((1.65, 3.25), (3.3, 3.25)), ((3.3, 1.65), (3.3, 3.25)), ((12.06, 1.65), (12.06, 4.44)),
                   ((12.06, 4.2), (15.55, 4.2)), ((12.06, 7.4), (15.55, 7.4))):
        wall(p, [a_, b_], 0.12, cls="w-part")
    glass(p, [(5.94, 10.9), (5.94, 4.44), (12.06, 4.44), (12.06, 10.9)])
    wall(p, [(5.94, 10.9), (12.06, 10.9)], 0.2, cls="w-garden")
    # otwory
    opening(p, (8.5, 0.2), (9.5, 0.2), 0.4, "door", swing=1)
    for a_ in (3.0, 5.4, 12.6, 14.6):
        opening(p, (a_, 0.2), (a_ + 0.6, 0.2), 0.4, "win")
    for a_ in (3.0, 5.6, 7.8):
        opening(p, (0.2, a_), (0.2, a_ + 0.6), 0.4, "win")
        opening(p, (17.0, a_), (17.0, a_ + 0.6), 0.4, "win")
    opening(p, (1.7, 10.8), (5.5, 10.8), 0.4, "slide")
    opening(p, (12.8, 10.8), (15.0, 10.8), 0.4, "win")
    opening(p, (15.8, 10.8), (16.7, 10.8), 0.4, "door", swing=1)
    opening(p, (7.4, GW_N), (10.6, GW_N), 0.15, "gap")
    for a_ in (2.4, 5.2, 8.2):
        opening(p, (GW_E, a_), (GW_E, a_ + 0.8), 0.15, "door", swing=1)
    opening(p, (3.3, 2.0), (3.3, 2.8), 0.12, "door", swing=1)
    opening(p, (5.94, 5.2), (5.94, 10.2), 0.13, "slide")
    opening(p, (12.06, 4.8), (12.06, 7.0), 0.13, "slide")
    opening(p, (12.06, 7.9), (12.06, 10.1), 0.13, "slide")
    opening(p, (6.6, 4.44), (11.4, 4.44), 0.13, "slide")
    opening(p, (8.0, 10.9), (10.0, 10.9), 0.2, "moon")
    stair_straight(p, *STAIR, "E", 15)
    p.text(9.0, -0.25, "wejście", "t-note", dy=-6)
    p.text(9.0, 11.55, "brama księżycowa", "t-note")
    overall_dims(p, 0, 0, 17.2, 11.0)
    north_arrow(p, 18.1, -1.0)
    scale_bar(p, 12.6, 12.9)
    return p


def upper_plan():
    p = Plan("Most – rzut piętra", -1.6, -1.8, 18.8, 13.8)
    lawn(p, rect_pts(-1.6, -1.8, 18.8, 13.8))
    deck(p, rect_pts(0.0, 11.0, 6.0, 13.2))
    garden(p)
    for r in ([(0, 0), (3.6, 0), (3.6, 5.7), (6, 5.7), (6, 11), (0, 11)],
              [(14.4, 0), (17.2, 0), (17.2, 11), (12, 11), (12, 5.7), (14.4, 5.7)]):
        p.poly("ground", r, "roof-below")
    for x in (3.0, 14.6):
        p.line("ground", (x, 0.1), (x, 10.9), "valley")
        for a_, b_ in (((x - 2.2, 8.0), (x - 0.4, 8.0)), ((x + 2.2, 8.0), (x + 0.4, 8.0)), ((x, 6.6), (x, 10.5))):
            if x == 14.6 and a_[0] > 17:
                continue
            (x1, y1), (x2, y2) = p.P(*a_), p.P(*b_)
            p.L["ground"].append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" class="flow" marker-end="url(#arrow-w)"/>')
        chain(p, (x, 11.25))
    p.text(1.5, 5.2, "dach motyli,", "t-note")
    p.text(1.5, 5.2, "rynna w środku", "t-note", dy=11)
    room(p, rect_pts(4.0, 0.4, 14.0, 1.5), "stone", "Korytarz z szafami", at=(10.3, 1.0), small=True)
    room(p, rect_pts(4.0, 1.65, 7.7, 5.3), "wood", "Sypialnia", at=(5.85, 4.55))
    room(p, rect_pts(7.82, 1.65, 11.3, 5.3), "wood", "Hol pod witrażem", at=(9.55, 4.6), small=True)
    p.area -= (10.25 - 7.8) * 1.0
    room(p, rect_pts(11.42, 1.65, 14.0, 5.3), "stone", "Łazienka", at=(12.0, 3.3), small=True)
    void(p, rect_pts(7.8, 2.55, 10.25, 3.55))
    stair_straight(p, 9.0, 2.55, 10.25, 3.55, "E", 5)
    p.poly("sym", rect_pts(7.9, 2.3, 10.3, 3.8), "sky-proj")
    p.text(9.1, 2.2, "witraż w dachu", "t-note")
    for x in (4.3, 6.2, 11.6):
        wardrobe(p, x + 0.8, 0.7, 1.6)
    bed(p, 5.85, 2.7, 1.6, 2.0)
    armchair(p, 7.0, 4.75, rot=200)
    tub(p, 12.85, 4.75, 0.8, 1.7, rot=90)
    shower(p, 13.1, 1.65, 14.0, 2.55)
    wc(p, 11.75, 2.3, rot=-90)
    basin(p, 12.35, 1.9, w=0.8)
    armchair(p, 10.75, 4.65, rot=210)
    wall(p, [(3.8, 0.2), (14.2, 0.2), (14.2, 5.5), (3.8, 5.5)], 0.4, closed=True)
    wall(p, [(4.0, GW_N), (14.0, GW_N)], 0.15, cls="w-inner")
    wall(p, [(7.76, 1.65), (7.76, 5.3)], 0.12, cls="w-part")
    wall(p, [(11.36, 1.65), (11.36, 5.3)], 0.12, cls="w-part")
    opening(p, (5.0, GW_N), (5.9, GW_N), 0.15, "door", swing=1)
    opening(p, (12.4, GW_N), (13.2, GW_N), 0.15, "door", swing=1)
    opening(p, (8.0, GW_N), (11.2, GW_N), 0.15, "gap")
    for a_, b_ in ((4.4, 7.4), (8.2, 11.0), (11.8, 13.6)):
        opening(p, (a_, 5.5), (b_, 5.5), 0.4, "win")
    for a_ in (6.4, 11.4):
        opening(p, (a_, 0.2), (a_ + 0.6, 0.2), 0.4, "win")
    opening(p, (3.8, 2.4), (3.8, 4.4), 0.4, "win")
    opening(p, (14.2, 2.6), (14.2, 3.6), 0.4, "win")
    p.line("sym", (7.8, 2.55), (10.25, 2.55), "st-rail")
    p.line("sym", (7.8, 3.55), (10.25, 3.55), "st-rail")
    overall_dims(p, 0, 0, 17.2, 11.0)
    north_arrow(p, 18.1, -1.0)
    scale_bar(p, 12.6, 12.9)
    return p


def section():
    s = Sec("Most – przekrój północ–południe przez schody i ogród", -1.6, 13.2, -1.0, 7.6, s=36, pad_r=96)
    s.rect(-1.6, -1.0, 13.2, -0.3, "s-ground")
    s.line((-1.6, -0.3), (13.2, -0.3), "s-line")
    # w tle: skrzydło wschodnie
    s.rect(5.7, 0, 11.0, Z_W_HI, "s-beyondf")
    s.rect(0, 0, 11.0, Z_W_HI, "s-beyond")
    s.rect(0, -0.35, 4.44, 0, "s-cut")
    # ściana północna z drzwiami
    s.rect(0, 2.3, 0.4, F1, "s-cut")
    s.rect(0.15, 0, 0.25, 2.3, "s-glass")
    s.rect(0, F1, 0.4, Z_B_N - 0.35, "s-cut")
    # strop / podłoga mostu (wspornik nad engawą), otwór schodów
    s.rect(0.4, 3.1, 2.55, F1, "s-cut")
    s.rect(3.55, 3.1, 5.7, F1, "s-cut")
    s.rect(4.38, 0, 4.5, 2.8, "s-glass")
    s.rect(4.3, 2.8, 4.5, 3.1, "s-cut")
    # schody (przekrój poprzeczny biegu)
    s.poly([(2.55, 1.9), (3.55, 1.9), (3.55, 2.07), (2.55, 2.07)], "s-cut")
    s.poly([(2.55, 1.7), (3.55, 1.7), (3.55, 1.9), (2.55, 1.9)], "s-tread")
    # ściana południowa mostu z oknem
    s.rect(5.3, F1, 5.7, 3.8, "s-cut")
    s.rect(5.45, 3.8, 5.55, 5.9, "s-glass")
    s.rect(5.3, 5.9, 5.7, Z_B_S - 0.35, "s-cut")
    s.poly([(0, Z_B_N), (5.75, Z_B_S), (5.75, Z_B_S - 0.35), (0, Z_B_N - 0.35)], "s-roof")
    zr = lambda y: Z_B_N - (Z_B_N - Z_B_S) * y / 5.75
    s.poly([(2.3, zr(2.3) + 0.02), (3.8, zr(3.8) + 0.02), (3.8, zr(3.8) - 0.33), (2.3, zr(2.3) - 0.33)], "s-stained")
    s.rect(5.75, Z_B_S - 0.2, 6.0, Z_B_S - 0.05, "s-cut")
    s.chain(5.85, Z_B_S - 0.2, 0.15)
    s.flow((0.6, Z_B_N + 0.1), (4.9, Z_B_S + 0.17))
    # ogród
    s.rect(4.5, -0.05, 5.4, 0.05, "s-deck")
    s.rect(5.4, -0.3, 10.8, -0.15, "s-gravel")
    s.rect(6.5, -0.5, 8.0, -0.15, "s-water")
    s.rect(5.6, -0.15, 6.1, 0.15, "s-stone")
    s.tree(9.6, -0.15, 2.2, 0.55, "s-tree")
    # mur z bramą księżycową
    s.rect(10.8, 2.1, 11.0, 2.6, "s-cut")
    s.rect(10.8, -0.3, 11.0, 0.1, "s-cut")
    s.text(2.0, 1.2, "hol", "t-sroom")
    s.text(0.95, 4.6, "korytarz", "t-note")
    s.text(3.0, 4.6, "hol pod witrażem", "t-sroom")
    s.text(8.1, 1.6, "ogród", "t-sroom")
    s.text(4.95, 0.35, "engawa", "t-note")
    s.text(12.2, 0.2, "trawnik", "t-note")
    s.person(1.4, 0)
    s.person(7.4, -0.15)
    s.person(4.4, F1)
    s.note(3.0, zr(3.0) - 0.15, "witraż nad schodami", 6.6, 7.2)
    s.note(5.85, 3.0, "łańcuch deszczowy do misy", 6.6, 4.9)
    s.note(10.9, 1.1, "brama księżycowa w murze", 11.4, 3.4)
    s.note(0.2, 1.1, "drzwi wejściowe", -1.5, 3.6)
    s.note(8.0, 3.0, "w tle: skrzydło nocne, dach motyli", 6.6, 4.35)
    for z, t in ((Z_B_N, "+6,90"), (Z_W_HI, "+4,00"), (F1, "+3,40"), (0, "±0,00"), (-0.3, "−0,30")):
        s.level(12.9, z, t)
    return s.render()


def model():
    m = Model((8.6, 6.0), 15)
    m.box(0, 0, -0.3, 6, 11, Z_W_LO, "char")
    m.box(12, 0, -0.3, 17.2, 11, Z_W_LO, "char")
    m.box(6, 0, -0.3, 12, 4.5, 3.1, "char")
    m.box(3.6, 0, 3.1, 14.4, 5.7, Z_B_S, "plaster")
    m.poly([(3.6, 0, Z_B_N), (14.4, 0, Z_B_N), (14.4, 5.7, Z_B_S), (3.6, 5.7, Z_B_S)], "roof")
    m.fascia([(3.6, 0, Z_B_N), (14.4, 0, Z_B_N)], Z_B_S, "plaster")
    m.poly([(3.6, 0, Z_B_S), (3.6, 5.7, Z_B_S), (3.6, 0, Z_B_N)], "plaster")
    m.poly([(14.4, 0, Z_B_S), (14.4, 0, Z_B_N), (14.4, 5.7, Z_B_S)], "plaster")
    for x0, x1 in ((0, 6), (12, 17.2)):
        xm = (x0 + x1) / 2
        m.poly([(x0, 0, Z_W_HI), (x0, 11, Z_W_HI), (xm, 11, Z_W_LO), (xm, 0, Z_W_LO)], "roof")
        m.poly([(xm, 0, Z_W_LO), (xm, 11, Z_W_LO), (x1, 11, Z_W_HI), (x1, 0, Z_W_HI)], "roof")
        for y in (0, 11):
            m.poly([(x0, y, Z_W_LO), (x0, y, Z_W_HI), (xm, y, Z_W_LO)], "char")
            m.poly([(xm, y, Z_W_LO), (x1, y, Z_W_HI), (x1, y, Z_W_LO)], "char")
        m.fascia([(x0, 0, Z_W_HI), (x0, 11, Z_W_HI)], Z_W_LO, "char")
        m.fascia([(x1, 0, Z_W_HI), (x1, 11, Z_W_HI)], Z_W_LO, "char")
        m.box(xm - 0.1, 11.0, Z_W_LO - 0.15, xm + 0.1, 11.45, Z_W_LO, "copper")
        m.chain(xm, 11.35, -0.15, Z_W_LO - 0.15)
        m.stone(xm, 11.35, 0.3, 0.3)
    zr = lambda y: Z_B_N - (Z_B_N - Z_B_S) * y / 5.7 + 0.04
    m.stained([(7.9, 2.3, zr(2.3)), (10.3, 2.3, zr(2.3)), (10.3, 3.8, zr(3.8)), (7.9, 3.8, zr(3.8))], "rect")
    m.moonwall((6.0, 10.9), (12.0, 10.9), -0.3, 2.6, 0.2, 3.0, 1.1, 1.0, "plaster")
    # przeszklenia
    m.panel((6.02, 4.6), (6.02, 10.8), 0.0, 2.9)
    m.panel((11.98, 10.8), (11.98, 4.6), 0.0, 2.9)
    m.panel((11.8, 4.52), (6.2, 4.52), 0.0, 2.8)
    for a, b in ((4.4, 7.4), (8.2, 11.0), (11.8, 13.6)):
        m.panel((b, 5.72), (a, 5.72), 3.8, 5.9)
    m.panel((3.58, 2.4), (3.58, 4.4), 3.8, 5.9)
    m.panel((1.7, 11.02), (5.5, 11.02), 0.0, 2.9)
    m.panel((12.8, 11.02), (15.0, 11.02), 0.8, 2.5)
    m.panel((9.5, -0.02), (8.5, -0.02), -0.25, 2.3, "door")
    for a in (3.0, 5.4, 12.6, 14.6):
        m.panel((a + 0.6, -0.02), (a, -0.02), 0.6, 2.6, "dark")
    for a in (3.0, 5.6, 7.8):
        m.panel((-0.02, a), (-0.02, a + 0.6), 0.6, 2.6, "dark")
        m.panel((17.22, a + 0.6), (17.22, a), 0.6, 2.6, "dark")
    # ogród
    m.flat([(6.0, 4.5), (12.0, 4.5), (12.0, 5.4), (6.0, 5.4)], 0.02, "deck")
    m.flat([(6.0, 5.4), (6.9, 5.4), (6.9, 10.8), (6.0, 10.8)], 0.02, "deck")
    m.flat([(11.1, 5.4), (12.0, 5.4), (12.0, 10.8), (11.1, 10.8)], 0.02, "deck")
    m.flat([(6.9, 5.4), (11.1, 5.4), (11.1, 10.8), (6.9, 10.8)], -0.2, "gravel")
    m.flat([(0, 11), (6, 11), (6, 13.2), (0, 13.2)], -0.12, "deck")
    m.add(t="ellipse", x=9.0, y=7.25, rx=1.4, ry=0.75, z=-0.17, m="water")
    m.add(t="ellipse", x=10.4, y=9.6, rx=0.8, ry=0.6, z=-0.16, m="moss")
    m.tree(10.45, 9.45, 3.2, 0.95, "maple")
    m.tree(7.45, 9.85, 2.2, 0.6, "pine")
    m.stone(10.4, 6.2, 0.3)
    m.stone(10.35, 8.6, 0.22)
    m.toro(7.6, 6.0)
    m.bamboo(7.2, 10.45, 8, 0.3)
    m.bamboo(10.9, 10.45, 8, 0.3)
    m.stone(9.0, 5.85, 0.28, 0.3)
    m.chain(9.0, 5.82, 0.1, Z_B_S)
    for x, y in ((7.4, 6.6), (7.5, 7.3), (7.7, 8.0), (8.1, 8.65), (8.55, 9.25), (8.9, 9.85)):
        m.add(t="ellipse", x=x, y=y, rx=0.24, ry=0.18, z=-0.15, m="stone")
    m.flat([(8.4, -6), (9.6, -6), (9.6, 0), (8.4, 0)], -0.28, "stone")
    m.tree(-3.0, 3.0, 8, 2.2, "pine")
    m.tree(20.5, 4.0, 7, 2.2, "round")
    m.tree(3.0, 17.0, 5.5, 1.6, "birch")
    m.tree(15.0, 16.0, 6, 1.8, "round")
    m.person(3.0, 12.2, -0.12)
    return m.d


def build():
    g, u = ground_plan(), upper_plan()
    return {"plans": [g.render(), u.render()], "section": section(), "model": model(), "areas": (g.area, u.area)}
