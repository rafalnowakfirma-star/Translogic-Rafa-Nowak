"""P04 · Plaster miodu – sześciokątny ogród-las pod szklaną piramidą, pierścień segmentów i doklejone komórki."""
import math

from silnik import House, poly

# ---------------------------------------------------------------- geometria
# Sześciokąt foremny z płaskimi bokami na wschód i zachód (rot = 0).
# Wierzchołki k: 0 → 30°, 1 → 90° (S), 2 → 150°, 3 → 210°, 4 → 270° (N), 5 → 330°.
# Bok k (normalna 60·k°) leży między wierzchołkami k−1 i k: 0 = E, 1 = SE, 2 = SW, 3 = W, 4 = NW, 5 = NE.
CX, CY = 16.0, 16.0
A_IN, A_OUT = 4.0, 8.5        # apotema ogrodu i zewnętrznego obrysu pierścienia (głębokość segmentu 4,5 m)
A_C = 2.75                    # apotema komórek doklejonych z zewnątrz
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


def cell(k, end):
    """Sześciokątna komórka przyklejona do zewnętrznego boku k pierścienia, przy jego końcu
    'lo' (wierzchołek k−1) albo 'hi' (wierzchołek k). Zwraca (wierzchołki, styk_q0, styk_q1)."""
    if end == "lo":
        q0, q1 = VO[(k - 1) % 6], lerp(VO[(k - 1) % 6], VO[k % 6], A_C / A_OUT)
    else:
        q0, q1 = VO[k % 6], lerp(VO[k % 6], VO[(k - 1) % 6], A_C / A_OUT)
    m = ((q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2)
    n = (math.cos(math.radians(60 * k)), math.sin(math.radians(60 * k)))
    c = (m[0] + n[0] * A_C, m[1] + n[1] * A_C)
    pts = [_pt(A_C / COS30, 30 + 60 * i, c) for i in range(6)]
    for i, p in enumerate(pts):          # dokładnie te same współrzędne co na obrysie pierścienia
        for q in (q0, q1):
            if math.hypot(p[0] - q[0], p[1] - q[1]) < 1e-6:
                pts[i] = q
    return pts, q0, q1


TOWER, _, QT = cell(3, "lo")      # komórka-wieża przy zachodnim boku (sypialnia na piętrze)
PATIO, _, QP = cell(2, "hi")      # komórka patio przy boku południowo-zachodnim
# wspólny bok wieży i patio (plaster miodu: trzy sześciokąty w jednym wierzchołku)
for i, p in enumerate(PATIO):
    for q in TOWER:
        if math.hypot(p[0] - q[0], p[1] - q[1]) < 1e-6:
            PATIO[i] = q

# front (bok NE) – podział na pasmo zewnętrzne (WC | wiatrołap | pralnia) i wewnętrzne (hol)
V_SPLIT = 6.2
X4, X5 = R(4, V_SPLIT), R(5, V_SPLIT)
W1, W2 = S(5, -1.4, A_OUT), S(5, -1.4, V_SPLIT)
W3, W4 = S(5, 1.4, A_OUT), S(5, 1.4, V_SPLIT)

# piętro nad galerią: łazienka od ogrodu, garderoba wzdłuż ściany zewnętrznej
RB = R(3, 6.4)
B1, B2 = S(3, -0.9, 6.4), S(3, -0.9, A_IN)

# schody proste w galerii, wzdłuż zachodniej ściany (bieg 5,2 m)
STAIR = (CX - 8.25, CY - 3.2, CX - 7.15, CY + 2.0)

# ------------------------------------------------------------------- dom
H = House(
    "p04", "Plaster miodu",
    "Dom z sześciokątów: wokół sześciokątnego ogrodu-lasu stoi pierścień sześciu pomieszczeń, a do niego przyklejone są komórki – wieża z sypialnią i szklane patio. Nad ogrodem jest szklana piramida z unoszoną latarnią.",
    style=dict(fasada="drewno_opal", dach="sedum", akcent="miedz"),
    concept=[
        "Ogród o boku 4,6 m ma wysokość dwóch kondygnacji i rośnie w nim las: brzozy, paprocie i mech. Szklana piramida ma w szczycie latarnię, którą latem podnosi się o 70 cm, i ciepłe powietrze uchodzi górą.",
        "Biuro zajmuje wschodni segment: od ogrodu ma przesuwną szklaną ścianę, a od wschodu szkło na brzozowy zagajnik. Wchodzi się do niego tylko z holu, więc nikt przez nie nie przechodzi.",
        "Od wejścia nie ma korytarza: hol, biblioteka i galeria ze schodami prowadzą jedna przez drugą do salonu, a każda ma szklane drzwi do ogrodu.",
        "Salon z kuchnią obejmuje dwa boki sześciokąta i ma 6,5 m wysokości. Jego szklane ściany patrzą na południowy wschód i południowy zachód, a przy kuchni stoi szklana komórka patio.",
        "Sypialnia jest na piętrze sześciokątnej wieży i ma szklane ściany na zachód. Wychodzi się z niej na taras na dachu patio, a garderoba i łazienka nad galerią łączą ją ze schodami.",
    ],
    notes=dict(
        lato="Latarnia piramidy jest uniesiona, harmonijki patio złożone, a ogród przewietrza się przez otwarte drzwi wszystkich pokoi jak leśna polana.",
        zima="Piramida jest zamknięta, a ogród grzeje słońce wpadające przez szklany salon; patio zamknięte szkłem służy jako jadalnia z widokiem na śnieg.",
        technologia="Prefabrykowane ściany szkieletowe z drewna w trzech typach (trapez pierścienia, bok komórki, ściana szklana), stropy z płyt CLT, elewacja z opalanych desek, piramida ze stalowych żeber i szkła zespolonego.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

H.ogrod("og", "Ogród-las", poly(VI), levels=2, roof_type="pyramid", style="las", seed=4, edge="glass")

# --- front (NE): wiatrołap, WC, pralnia, hol
H.room("wc", "WC", "wc", poly(VO[4], W1, W2, X4))
H.room("wia", "Wiatrołap", "wiatrolap", poly(W1, W3, W4, W2), ext="slits")
H.room("pral", "Pralnia", "pralnia", poly(W3, VO[5], X5, W4))
H.room("hol", "Hol", "hol", poly(X4, W2, W4, X5, VI[5], VI[4]))
# --- NW: biblioteka (przelotowa)
H.room("bib", "Biblioteka", "biblioteka", poly(VO[3], VO[4], X4, VI[4], VI[3]), ext="slits")
# --- E: biuro przeszklone z obu stron
H.room("biu", "Biuro", "biuro", poly(VO[5], VO[0], VI[0], VI[5], X5), ext="glass_slide", garden="glass_slide")
# --- SE + SW: salon z kuchnią na dwie kondygnacje
H.room("sal", "Salon z kuchnią", "salon_kuchnia", poly(VO[0], VO[1], QP, VO[2], VI[2], VI[1], VI[0]),
       levels=2, ext="glass_slide", kitchen_at="E")
# --- W: galeria ze schodami
H.room("gal", "Galeria", "galeria", poly(VO[2], QT, VO[3], VI[3], B2, VI[2]), ext="band_high")
H.stair("straight", level=0, rect=STAIR, up="S")
# --- komórki: wieża (herbaciarnia / sypialnia) i patio sezonowe z tarasem na dachu
H.room("her", "Herbaciarnia", "herbaciarnia", poly(TOWER),
       ext={"W": "glass", "SW": "glass_slide", "NW": "windows_sq", "N": "solid"})
H.room("ps", "Patio sezonowe", "patio_sezonowe", poly(PATIO))

# --- piętro
H.room("gar", "Garderoba", "garderoba", poly(VO[2], QT, VO[3], RB, B1, B2, VI[2]), level=1)
H.room("laz", "Łazienka", "lazienka", poly(VI[3], RB, B1, B2), level=1, garden="glass")
H.room("syp", "Sypialnia", "sypialnia_glowna", poly(TOWER), level=1,
       ext={"W": "glass_slide", "SW": "glass_slide", "NW": "glass", "N": "solid"})
H.room("tar", "Taras", "taras", poly(PATIO), level=1)

# --- połączenia
H.connect("wia", "hol", "wide")
H.connect("wia", "wc", "door")
H.connect("hol", "pral", "door")
H.connect("hol", "biu", "door")
H.connect("hol", "bib", "wide")
H.connect("bib", "gal", "wide")
H.connect("gal", "sal", "wide")
H.connect("gal", "her", "door")
H.connect("sal", "ps", "slide")
H.connect("her", "ps", "slide")
H.connect("gar", "laz", "door")
H.connect("gar", "syp", "door")
H.connect("syp", "tar", "slide")
H.connect("sal", "tar", "glass")

H.entrance("wia", 300)

# --- teren
H.cut("A–A", (CX + 3.0, CY - 13.0), (CX + 3.0, CY + 12.0))
H.cut("B–B", (CX - 16.0, CY + 1.85), (CX + 11.0, CY + 1.85))
