"""P04 · Plaster miodu – sześciokątny ogród-las pod szklaną piramidą, pierścień segmentów i doklejone komórki."""
import math

from silnik import House, poly

# ---------------------------------------------------------------- geometria
# Sześciokąt foremny z płaskimi bokami na wschód i zachód (rot = 0).
# Wierzchołki k: 0 → 30°, 1 → 90° (S), 2 → 150°, 3 → 210°, 4 → 270° (N), 5 → 330°.
# Bok k (normalna 60·k°) leży między wierzchołkami k−1 i k: 0 = E, 1 = SE, 2 = SW, 3 = W, 4 = NW, 5 = NE.
CX, CY = 16.0, 16.0
A_IN, A_OUT = 4.0, 8.5        # apotema ogrodu i obrysu pierścienia (głębokość segmentu 4,5 m)
A_T = 3.25                    # apotema komórek: wieża i patio (mają wspólny bok)
A_G = 2.0                     # apotema ganku przed wejściem
COS30 = math.cos(math.radians(30))
T30 = math.tan(math.radians(30))


def _pt(r, ang, c=(CX, CY)):
    a = math.radians(ang)
    return (c[0] + r * math.cos(a), c[1] + r * math.sin(a))


def lerp(p, q, t):
    if t <= 0:
        return p
    if t >= 1:
        return q
    return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


VI = [_pt(A_IN / COS30, 30 + 60 * k) for k in range(6)]     # wierzchołki ogrodu
VO = [_pt(A_OUT / COS30, 30 + 60 * k) for k in range(6)]    # wierzchołki obrysu pierścienia


def R(k, v):
    """Punkt na promieniu wierzchołka k w odległości v (apotema) od środka."""
    return lerp(VI[k % 6], VO[k % 6], (v - A_IN) / (A_OUT - A_IN))


def S(k, u, v):
    """Punkt segmentu k: v – odległość od środka (A_IN…A_OUT), u – przesunięcie wzdłuż boku
    (ujemne w stronę wierzchołka k−1, dodatnie w stronę wierzchołka k)."""
    return lerp(R(k - 1, v), R(k, v), (u + v * T30) / (2 * v * T30))


def snap(pts, ref):
    """Wierzchołki leżące w tym samym miejscu dostają identyczne współrzędne (wspólne krawędzie)."""
    for i, p in enumerate(pts):
        for q in ref:
            if math.hypot(p[0] - q[0], p[1] - q[1]) < 1e-6:
                pts[i] = q
    return pts


def cell(k, a, q0, q1):
    """Sześciokąt o apotemie a przyklejony bokiem q0–q1 do zewnętrznego boku k pierścienia.
    Zwraca (wierzchołki pod kątami 30 + 60·m od środka komórki, środek)."""
    m = ((q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2)
    n = (math.cos(math.radians(60 * k)), math.sin(math.radians(60 * k)))
    c = (m[0] + n[0] * a, m[1] + n[1] * a)
    return snap([_pt(a / COS30, 30 + 60 * i, c) for i in range(6)], (q0, q1)), c


# wieża przy boku W i patio przy boku SW stykają się w wierzchołku 150° pierścienia:
# trzy sześciokąty w jednym punkcie, jak w plastrze miodu
QT = lerp(VO[2], VO[3], A_T / A_OUT)
QP = lerp(VO[2], VO[1], A_T / A_OUT)
TOWER, TC = cell(3, A_T, VO[2], QT)
PATIO, PC = cell(2, A_T, VO[2], QP)
PATIO = snap(PATIO, TOWER)
t0, t1, t2, t3, t4, t5 = TOWER          # t0 = VO[2], t5 = QT; ściany: t5–t0 E, t0–t1 SE, t1–t2 SW, t2–t3 W, t3–t4 NW, t4–t5 NE

# podział wieży: pas wzdłuż dwóch północnych ścian – łazienka (piętro) nad pralnią (parter);
# schody kręcone w narożniku przy ścianie E
_s = 0.745 / (t2[1] - t3[1])
WS, ES = lerp(t3, t2, _s), lerp(t5, t0, _s)
SPIRAL = (TC[0] + 1.65, TC[1] + 1.27)

# ganek przed wejściem (bok NE, pośrodku)
G0, G1 = S(5, -A_G * T30, A_OUT), S(5, A_G * T30, A_OUT)
PORCH, _ = cell(5, A_G, G0, G1)

# front (bok NE) – pasmo zewnętrzne (WC | wiatrołap | techniczne) i wewnętrzne (hol)
V_SPLIT = 5.8
X4, X5 = R(4, V_SPLIT), R(5, V_SPLIT)
W1, W2 = S(5, -1.5, A_OUT), S(5, -1.5, V_SPLIT)
W3, W4 = S(5, 1.5, A_OUT), S(5, 1.5, V_SPLIT)

# ------------------------------------------------------------------- dom
H = House(
    "p04", "Plaster miodu",
    "Dom z sześciokątów: wokół sześciokątnego ogrodu-lasu stoi niski pierścień sześciu pomieszczeń, a do niego przyklejone są komórki – wieża z sypialnią, szklane patio i ganek. Nad ogrodem jest szklana piramida z unoszoną latarnią.",
    style=dict(fasada="drewno_opal", dach="sedum"),
    concept=[
        "Ogród ma wysokość dwóch kondygnacji i rośnie w nim las: brzozy, paprocie i mech. Szklana piramida ma w szczycie latarnię, którą latem podnosi się o 70 cm, i ciepłe powietrze uchodzi górą.",
        "Biuro zajmuje wschodni segment: od ogrodu ma przesuwną szklaną ścianę, a od wschodu szkło na brzozowy zagajnik. Wchodzi się do niego tylko z holu, więc nikt przez nie nie przechodzi.",
        "Od wejścia nie ma korytarza: hol, biblioteka i herbaciarnia prowadzą jedna przez drugą do salonu i kuchni, a z każdej widać ogród.",
        "Salon i kuchnia zajmują dwa boki sześciokąta i mają 6,5 m wysokości. Szkło od południowego wschodu i południowego zachodu wpuszcza słońce przez salon aż do ogrodu.",
        "Sypialnia z łazienką jest na piętrze sześciokątnej wieży i ma szklane ściany na zachód. Na dole wieży są garderoba i pralnia, a z sypialni wychodzi się na taras na dachu patio.",
    ],
    notes=dict(
        lato="Latarnia piramidy jest uniesiona, harmonijki patio złożone, a ogród przewietrza się przez otwarte drzwi pokoi jak leśna polana.",
        zima="Piramida jest zamknięta, a ogród grzeje słońce wpadające przez szklany salon; patio zamknięte szkłem służy jako jadalnia z widokiem na śnieg.",
        technologia="Prefabrykowane ściany szkieletowe z drewna w kilku powtarzalnych typach (trapez pierścienia, bok komórki, ściana szklana), stropy z płyt CLT, elewacja z opalanych desek, piramida ze stalowych żeber i szkła zespolonego.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

H.ogrod("og", "Ogród-las", poly(VI), levels=2, roof_type="pyramid", style="las", seed=4, edge="glass")

# --- front (NE): wiatrołap, WC, techniczne, hol; przed wiatrołapem ganek
H.room("wc", "WC", "wc", poly(VO[4], W1, W2, X4))
H.room("wia", "Wiatrołap", "wiatrolap", poly(W1, G0, G1, W3, W4, W2), ext="slits")
H.room("tech", "Techniczne", "techniczne", poly(W3, VO[5], X5, W4))
H.room("hol", "Hol", "hol", poly(X4, W2, W4, X5, VI[5], VI[4]))
H.room("gan", "Ganek", "loggia", poly(PORCH), furn=False)
# --- NW: biblioteka, ściana zewnętrzna w regałach
H.room("bib", "Biblioteka", "biblioteka", poly(VO[3], VO[4], X4, VI[4], VI[3]), ext="solid", garden="glass")
H.window("bib", "NW", at=0.5, width=1.2, sill=0.45, head=2.6)
# --- W: herbaciarnia (przelotowa, prowadzi do wieży i do salonu)
H.room("her", "Herbaciarnia", "herbaciarnia", poly(VO[2], ES, QT, VO[3], VI[3], VI[2]), ext="band")
# --- E: biuro przeszklone z obu stron
H.room("biu", "Biuro", "biuro", poly(VO[5], VO[0], VI[0], VI[5], X5), ext="glass_slide", garden="glass_slide")
# --- SE + SW: kuchnia z jadalnią i salon, razem, na dwie kondygnacje
H.room("kuch", "Kuchnia z jadalnią", "kuchnia", poly(VO[0], VO[1], VI[1], VI[0]), levels=2,
       ext="glass_slide", garden="glass", kitchen_at="E")
H.room("sal", "Salon", "salon", poly(VO[1], QP, VO[2], VI[2], VI[1]), levels=2, ext="glass_slide")
# --- komórki: patio sezonowe z tarasem na dachu; wieża: garderoba i pralnia / sypialnia i łazienka
H.room("ps", "Patio sezonowe", "patio_sezonowe", poly(PATIO))
H.room("gar", "Garderoba", "garderoba", poly(ES, t0, t1, t2, WS), ext={"W": "windows_sq", "*": "solid"})
H.room("pral", "Pralnia", "pralnia", poly(WS, t3, t4, t5, ES), ext={"NW": "solid", "NE": "windows_sq"})
H.stair("spiral", level=0, center=SPIRAL, r=1.0, start=270, sweep=270, n=16)
H.room("syp", "Sypialnia", "sypialnia_glowna", poly(ES, t0, t1, t2, WS), level=1,
       ext={"SE": "glass_slide", "SW": "glass_slide", "W": "glass", "E": "windows"})
H.room("laz", "Łazienka", "lazienka", poly(WS, t3, t4, t5, ES), level=1, ext={"NW": "solid", "NE": "band_high"})
H.room("tar", "Taras", "taras", poly(PATIO), level=1, dz=0.03)   # dz: posadzka tarasu nad stropem patio

# --- połączenia (szklane ściany przesuwne same dają drzwi: salon–patio, sypialnia–taras, pokoje–ogród)
H.connect("wia", "hol", "double")
H.connect("hol", "wc", "door")
H.connect("hol", "tech", "door")
H.connect("hol", "biu", "door")
H.connect("hol", "bib", "wide")
H.connect("bib", "her", "wide", at=0.3)
H.connect("her", "sal", "wide", at=0.5)
H.connect("sal", "kuch", "open")
H.connect("her", "gar", "door", at=0.75)
H.connect("gar", "pral", "door", at=0.8)
H.connect("syp", "laz", "door", at=0.8)
H.connect("sal", "tar", "glass")
H.connect("sal", "og", "glass", width=1.0)

H.entrance("wia", 300)

# --- teren
_n = (math.cos(math.radians(300)), math.sin(math.radians(300)))
_t = (-_n[1], _n[0])
_d = S(5, 0.0, A_OUT)
H.path(poly(*[(_d[0] + _t[0] * a + _n[0] * b, _d[1] + _t[1] * a + _n[1] * b)
              for a, b in ((-0.75, 2 * A_G), (0.75, 2 * A_G), (0.75, 8.5), (-0.75, 8.5))]))
H.tree(CX + 12.0, CY - 1.5, "brzoza")      # zagajnik przed biurem
H.tree(CX + 13.5, CY + 2.5, "brzoza")
H.tree(CX + 11.2, CY + 5.0, "sosna")
H.tree(CX - 15.0, CY + 11.5, "klon")
H.cut("A–A", (CX + 3.0, CY - 13.5), (CX + 3.0, CY + 12.0))
H.cut("B–B", (CX - 17.0, CY + 17.0 * 0.4257), (CX + 12.0, CY - 12.0 * 0.4257))
