"""P04 · Plaster miodu (wersja 2) – sześciokątny ogród-las pod szklaną piramidą, pierścień sześciu segmentów,
na dachu parteru dwa tarasy i trzy moduły piętra."""
import math

from shapely.geometry import Polygon

from silnik import House, poly

# ---------------------------------------------------------------- geometria
# Sześciokąt foremny z płaskimi bokami na północ i południe (obrót 30°).
# Segment k ma normalną 30 + 60·k: 0 = ESE, 1 = S, 2 = WSW, 3 = WNW, 4 = N, 5 = ENE.
# Lokalny układ segmentu: v – odległość od środka (apotema), u – przesunięcie wzdłuż boku
# (u < 0 w stronę wierzchołka pod kątem normalna − 30°, u > 0 – normalna + 30°).
CX, CY = 10.0, 10.0
ROT = 30.0
A_IN = 3.2          # apotema ogrodu
A_OUT = 6.6         # apotema pierścienia (głębokość segmentu 3,4 m)
A_SAL = 8.4         # salon wysunięty na południe
A_P = 3.3           # apotema sześciokątnego patio
A_G = 1.6           # apotema ganku
T30 = math.tan(math.radians(30))
ESE, S_, WSW, WNW, N_, ENE = range(6)

_REG = []


def _snap(p):
    for q in _REG:
        if abs(p[0] - q[0]) < 1e-6 and abs(p[1] - q[1]) < 1e-6:
            return q
    _REG.append(p)
    return p


def P(k, u, v):
    """Punkt segmentu k (wspólne punkty sąsiadów mają identyczne współrzędne)."""
    n = math.radians(ROT + 60 * k)
    t = n + math.pi / 2
    return _snap((CX + v * math.cos(n) + u * math.cos(t), CY + v * math.sin(n) + u * math.sin(t)))


def lo(k, v):
    return P(k, -v * T30, v)


def hi(k, v):
    return P(k, v * T30, v)


def seg(k, v1, v2, u1=None, u2=None):
    """Część segmentu k między apotemami v1–v2 i liniami prostopadłymi do boku u1–u2 (None = krawędź promienista)."""
    a = P(k, u1, v1) if u1 is not None else lo(k, v1)
    b = P(k, u2, v1) if u2 is not None else hi(k, v1)
    c = P(k, u2, v2) if u2 is not None else hi(k, v2)
    d = P(k, u1, v2) if u1 is not None else lo(k, v2)
    return [a, b, c, d]


def hexcell(c, a):
    R = a / math.cos(math.radians(30))
    return [_snap((c[0] + R * math.cos(math.radians(ROT + 30 + 60 * i)), c[1] + R * math.sin(math.radians(ROT + 30 + 60 * i))))
            for i in range(6)]


GARDEN = [hi(k, A_IN) for k in range(6)]

# patio – sześciokąt przyklejony do południowej ściany salonu, przesunięty na zachód
U_PAT = 2.6
PC = P(S_, U_PAT, A_SAL + A_P)
PATIO = hexcell(PC, A_P)
PP_E, PP_W = PATIO[4], PATIO[3]            # wierzchołki na ścianie salonu (300° i 240° od środka komórki)

# segment ENE: wiatrołap | pralnia ze spiżarnią (pasy na całą głębokość)
U_W = -0.4
GU = (-A_OUT * T30 + U_W) / 2              # ganek na środku zewnętrznej ściany wiatrołapu
GC = P(ENE, GU, A_OUT + A_G)
PORCH = hexcell(GC, A_G)


def _u(k, p):
    t = math.radians(ROT + 60 * k + 90)
    return (p[0] - CX) * math.cos(t) + (p[1] - CY) * math.sin(t)


# wierzchołki ganku na ścianie wiatrołapu (bok ganku o normalnej 150°), od strony U_W ku północy
G0, G1 = sorted([PORCH[1], PORCH[2]], key=lambda p: -_u(ENE, p))

# schody kręcone przy północnej ścianie holu (wschodnia część)
ST = P(N_, 1.7, 5.35)
# WC parteru – północno-zachodni narożnik holu
U_WC, V_WC = -1.2, 4.7
# moduł N piętra (biblioteka + łazienka) wysunięty 0,4 m nad północną ścianę parteru;
# łazienka w jego północno-zachodnim narożniku (przy sypialni)
A_N1 = 7.0
U_LZ, V_LZ = 0.5, 5.1
# salon / kuchnia – podział segmentu S
U_K = -0.3

# ------------------------------------------------------------------- dom
H = House(
    "p04", "Plaster miodu",
    "Dom z sześciokątów, 167 m²: pierścień sześciu segmentów szczelnie otacza ogród-las pod szklaną piramidą. Na dachu parteru są dwa tarasy, a nad północną połową stoją trzy moduły piętra – sypialnia, biblioteka i biuro.",
    style=dict(fasada="drewno_opal", dach="sedum"),
    concept=[
        "Ogród-las ma 34 m² i z każdej z sześciu stron przylega do pokoju. Od zewnątrz parter ma tylko okna, szczeliny i wysokie pasma, a jedyna szklana ściana salonu wychodzi na patio za murem, więc przez żaden pokój nie widać ogrodu na wylot.",
        "Wchodzi się przez sześciokątny ganek do wiatrołapu, który od ogrodu ma pełną ścianę; ogród pokazuje się dopiero w holu przy kręconych schodach.",
        "Parter obchodzi się dookoła ogrodu bez korytarzy: hol, pracownia, herbaciarnia, salon, kuchnia, jadalnia, pralnia ze spiżarnią i z powrotem wiatrołap.",
        "Salon z kuchnią zajmuje południowy segment wysunięty o 1,8 m i ma 6,3 m wysokości: na dole otwiera się na ogród, u góry na piramidę i oba tarasy, a od południa szklaną ścianą na sześciokątne patio za murem wysokości 2,6 m.",
        "Ogród ma jedną kondygnację, więc jego szklana piramida stoi na dachu parteru, a po obu jej stronach leżą tarasy po 19 m²; najwyższy dach, nad modułami i salonem, jest zielony.",
        "Na piętrze trzy moduły w ciągu, bez korytarza: biuro przeszklone na brzozowy zagajnik i taras wschodni, biblioteka ze schodami oraz sypialnia ze szklaną ścianą na zachód i wyjściem na taras zachodni. Moduł biblioteki jest wysunięty 0,4 m na północ i mieści też łazienkę sypialni.",
    ],
    notes=dict(
        lato="Latarnia piramidy jest uniesiona o 70 cm i ciepłe powietrze uchodzi z ogrodu górą, salon otwiera się na patio za murem, a z tarasów przez szkło piramidy widać korony brzóz w ogrodzie.",
        zima="Piramida jest zamknięta i ogród działa jak ciepły bufor w środku domu, a pełne ściany od północy i mur patio osłaniają przed wiatrem.",
        technologia="Prefabrykowane ściany szkieletowe z drewna: ściany zewnętrzne schodzą się zawsze pod kątem 60° albo 120°, więc pierścień i komórki składa się z kilku powtarzalnych typów płyt. Stropy i dachy z płyt CLT z warstwą spadkową pod tarasy i sedum, elewacja z opalanych desek, piramida na stalowych żebrach.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

# --- parter
hol = [lo(N_, A_IN), hi(N_, A_IN), hi(N_, A_OUT), P(N_, U_WC, A_OUT), P(N_, U_WC, V_WC), lo(N_, V_WC)]
H.room("hol", "Hol ze schodami", "hol", poly(hol), ext="slits", garden="glass_slide")
H.room("wc", "WC", "wc", poly(seg(N_, V_WC, A_OUT, None, U_WC)))
wia = seg(ENE, A_IN, A_OUT, None, U_W)
H.room("wia", "Wiatrołap", "wiatrolap", poly(wia[0], wia[1], wia[2], G0, G1, wia[3]), ext="slits", garden="solid")
H.room("pral", "Pralnia ze spiżarnią", "pralnia", poly(seg(ENE, A_IN, A_OUT, U_W, None)), ext="windows_sq", garden="band_high")
H.room("jad", "Jadalnia", "jadalnia", poly(seg(ESE, A_IN, A_OUT)), ext="windows")
# kuchnia (wschodnia część segmentu S) i salon (zachodnia, przy patio) – razem jedna wysoka przestrzeń
k0, k1, k2, k3 = seg(S_, A_IN, A_SAL, None, U_K)
H.room("kuch", "Kuchnia", "kuchnia", poly(k0, k1, k2, k3, lo(S_, A_OUT)), levels=2, kitchen_at="E",
       ext={"taE": "glass", "N": "glass", "S": "band_high", "*": "solid"}, floor="drewno")
s0, s1, s2, s3 = seg(S_, A_IN, A_SAL, U_K, None)
H.room("sal", "Salon", "salon", poly(s0, s1, hi(S_, A_OUT), s2, PP_W, PP_E, s3), levels=2,
       ext={"pat": "glass_slide", "taW": "glass", "N": "glass", "S": "band_high", "*": "solid"})
H.room("her", "Herbaciarnia", "herbaciarnia", poly(seg(WSW, A_IN, A_OUT)), ext="windows")
H.room("pra", "Pracownia", "pracownia", poly(seg(WNW, A_IN, A_OUT)), ext="band_high")
_roof_cut = Polygon([(PC[0] - 9, PP_E[1]), (PC[0] + 9, PP_E[1]), (PC[0] + 9, PP_E[1] + 2.2), (PC[0] - 9, PP_E[1] + 2.2)])
H.room("pat", "Patio za murem", "patio", poly(PATIO), enclose="gwall", roof=Polygon(PATIO).intersection(_roof_cut),
       label_at=(PC[0] + 0.9, PC[1] - 0.2))
H.room("gan", "Ganek", "loggia", poly(PORCH), furn=False)
H.stair("spiral", level=0, center=ST, r=1.0, start=180, sweep=300, n=16)

# --- piętro: moduły od północy, tarasy na dachu parteru
H.room("syp", "Sypialnia", "sypialnia_glowna", poly(seg(WNW, A_IN, A_OUT)), level=1,
       ext={"taW": "glass_slide", 210: "glass", "*": "solid"})
H.room("laz", "Łazienka", "lazienka", poly(lo(N_, V_LZ), P(N_, U_LZ, V_LZ), P(N_, U_LZ, A_N1), lo(N_, A_N1), lo(N_, A_OUT)),
       level=1, ext="band_high")
bib = [lo(N_, A_IN), hi(N_, A_IN), hi(N_, A_OUT), hi(N_, A_N1), P(N_, U_LZ, A_N1), P(N_, U_LZ, V_LZ), lo(N_, V_LZ)]
H.room("bib", "Biblioteka", "biblioteka", poly(bib), level=1, ext={"S": "glass", "*": "solid"})
H.room("biu", "Biuro", "biuro", poly(seg(ENE, A_IN, A_OUT)), level=1,
       ext={"taE": "glass_slide", 330: "glass", "*": "windows"})
H.room("taW", "Taras zachodni", "taras", poly(seg(WSW, A_IN, A_OUT)), level=1)
H.room("taE", "Taras wschodni", "taras", poly(seg(ESE, A_IN, A_OUT)), level=1)

# --- ogród (po pokojach)
H.ogrod("og", "Ogród-las", poly(GARDEN), levels=1, roof_type="pyramid", style="las", seed=2)

# --- połączenia
H.connect("wia", "hol", "door", at=0.8)
H.connect("wia", "pral", "door")
H.connect("hol", "wc", "door")
H.connect("hol", "pra", "door", at=0.2)
H.connect("pra", "her", "door", at=0.2)
H.connect("her", "sal", "arch", at=0.85)
H.connect("sal", "kuch", "open")
H.connect("kuch", "jad", "wide")
H.connect("jad", "pral", "door")
H.connect("bib", "syp", "door", at=1.0)
H.connect("laz", "syp", "door")
H.connect("bib", "biu", "door", at=0.85)
H.connect("syp", "taW", "slide")
H.connect("biu", "taE", "slide")
H.entrance("wia", 330)

# --- teren: ścieżka do ganku od północnego wschodu
H.path(poly(P(ENE, GU - 0.75, A_OUT + 2 * A_G), P(ENE, GU + 0.75, A_OUT + 2 * A_G),
            P(ENE, GU + 0.75, A_OUT + 2 * A_G + 6.0), P(ENE, GU - 0.75, A_OUT + 2 * A_G + 6.0)))
H.tree(CX + 11.5, CY - 3.5, "brzoza")      # zagajnik przed biurem
H.tree(CX + 13.0, CY + 1.0, "brzoza")
H.tree(CX + 10.5, CY + 6.0, "sosna")
H.tree(CX - 12.0, CY + 11.5, "klon")
# A–A: skraj schodów, ogród, wysoki salon, patio
_a, _b = (ST[0] - 0.8, ST[1]), (PC[0] + 1.6, PC[1])
_d = (_b[0] - _a[0], _b[1] - _a[1])
H.cut("A–A", (_a[0] - 0.33 * _d[0], _a[1] - 0.33 * _d[1]), (_b[0] + 0.3 * _d[0], _b[1] + 0.3 * _d[1]))
H.cut("B–B", P(WSW, 0.9, 10.0), P(ENE, -0.9, 10.0))
