"""P08 · Trójkąt (wersja 2) – mały trójkąt o ściętych narożnikach wokół ukrytego sześciokątnego ogrodu;
tarasy na dachach dwóch skrzydeł, moduły piętra nad trzecim skrzydłem i dwoma narożnikami."""
import math

from silnik import House, poly, rect

# ---------------------------------------------------------------- geometria
# Trójkąt równoboczny (oś ścian zewnętrznych) o promieniu wpisanym RT = 6,2 m → bok 21,5 m.
# Każdy punkt liczymy jedną funkcją P(bok, t, d): d = odległość od środka wzdłuż normalnej boku,
# t = przesunięcie wzdłuż boku. Punkty wspólne sąsiadów są liczone raz i wstawiane do obu wielokątów.
SQ3 = math.sqrt(3)
O = (12.0, 10.0)
RT = 6.2                 # linia zewnętrzna
D = 3.2                  # głębokość skrzydeł
RI = RT - D              # linia wewnętrzna (ogród)
SIDE = {"S": 90.0, "NE": 330.0, "NW": 210.0}          # kąty normalnych boków
CORNER = {"N": ("NW", "NE"), "SE": ("NE", "S"), "SW": ("S", "NW")}   # (bok z narożnikiem przy +t, bok przy -t)
_NORM = {s: (round(math.cos(math.radians(a)), 12), round(math.sin(math.radians(a)), 12)) for s, a in SIDE.items()}


def P(side, t, d):
    nx, ny = _NORM[side]
    return (O[0] + nx * d - ny * t, O[1] + ny * d + nx * t)


def tcut(d, r):
    """Parametr t, w którym prosta ścinająca narożnik (odl. d od środka) przecina linię o promieniu r."""
    return (2 * d - r) / SQ3


def between(p, q, y):
    """Punkt odcinka p–q o rzędnej y."""
    return (p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1]), y)


def at_y(chain, y):
    for a, b in zip(chain, chain[1:]):
        if (a[1] - y) * (b[1] - y) <= 0 and abs(a[1] - b[1]) > 1e-9:
            return between(a, b, y)
    raise ValueError("linia nie przecina łańcucha")


G = 3.6                  # ścięcie narożników ogrodu → sześciokąt (boki 4,85 m i 2,77 m)
TP = tcut(G, RI)         # wierzchołek ogrodu na linii wewnętrznej (±2,42 od środka boku)
E_N, E_SE, E_SW = 1.3, 1.3, (-1.2, -2.6)   # o ile skrzydła wchodzą w narożniki (SW ujemne: salon wchodzi w skrzydła S i NW)
DC_N, DC_SE, DC_SW = 8.1, 7.5, 7.5   # ścięcia narożników domu (SW = szklana ściana salon/patio)
DP, DR = 10.8, 9.1       # koniec patio (mur) i zasięg daszku nad patio


def corner(c, e, dc):
    """Narożnik c: e = (eA, eB) – o ile skrzydła wchodzą w narożnik (ujemne: narożnik wchodzi w skrzydła)."""
    sA, sB = CORNER[c]
    eA, eB = e if isinstance(e, tuple) else (e, e)
    tT = tcut(dc, RT)
    return dict(PA=P(sA, TP, RI), QA=P(sA, TP + eA, RI), FA=P(sA, TP + eA, RT), TA=P(sA, tT, RT),
                TB=P(sB, -tT, RT), FB=P(sB, -(TP + eB), RT), QB=P(sB, -(TP + eB), RI), PB=P(sB, -TP, RI))


def cpoly(c):
    return poly(c["PA"], c["QA"], c["FA"], c["TA"], c["TB"], c["FB"], c["QB"], c["PB"])


N, SE, SW = corner("N", E_N, DC_N), corner("SE", E_SE, DC_SE), corner("SW", E_SW, DC_SW)

# --- ogród: sześciokąt między trzema skrzydłami
garden = poly(N["PA"], N["PB"], SE["PA"], SE["PB"], SW["PA"], SW["PB"])

# --- narożnik N: pas wejściowy (wiatrołap, łazienka gości) + hol przy ogrodzie; nad nim biuro
Y_TIP = N["TA"][1]
Y_STRIP = Y_TIP + 2.0
X_SPLIT = O[0] + 0.3
west = [N["TA"], N["FA"], N["QA"], N["PA"]]
east = [N["TB"], N["FB"], N["QB"], N["PB"]]
L1, L2 = at_y(west, Y_STRIP), at_y(east, Y_STRIP)
W1, W2 = (X_SPLIT, Y_TIP), (X_SPLIT, Y_STRIP)
wia = poly(W1, W2, L1, *[p for p in reversed(west[:-1]) if p[1] < Y_STRIP - 1e-6])
laz0 = poly(W1, *[p for p in east[:-1] if p[1] < Y_STRIP - 1e-6], L2, W2)
hol = poly(L1, W2, L2, *[p for p in east[1:] if p[1] > Y_STRIP + 1e-6], *[p for p in reversed(west[1:]) if p[1] > Y_STRIP + 1e-6])
biu = cpoly(N)

# --- skrzydło NE (parter: biblioteka ze schodami; piętro: galeria, garderoba, łazienka)
T0, T1 = -(TP + E_N), TP + E_SE
L_GAL, L_GAR = 3.2, 1.85
D_STRIP = RI + 1.2       # szklany pasaż galerii wzdłuż dachu ogrodu
bib = poly(P("NE", T0, RI), P("NE", T0, RT), P("NE", T1, RT), P("NE", T1, RI))
gal = poly(P("NE", T0, RI), P("NE", T0, RT), P("NE", T0 + L_GAL, RT), P("NE", T0 + L_GAL, D_STRIP),
           P("NE", T1, D_STRIP), P("NE", T1, RI))
gar = poly(P("NE", T0 + L_GAL, D_STRIP), P("NE", T0 + L_GAL, RT), P("NE", T0 + L_GAL + L_GAR, RT),
           P("NE", T0 + L_GAL + L_GAR, D_STRIP))
laz1 = poly(P("NE", T0 + L_GAL + L_GAR, D_STRIP), P("NE", T0 + L_GAL + L_GAR, RT), P("NE", T1, RT), P("NE", T1, D_STRIP))
STAIR_C = P("NE", T0 + 1.9, RI + 1.3)   # schody kręcone przy szkle ogrodu, regały wzdłuż ściany zewnętrznej

# --- narożnik SE: parter pokój gościnny, piętro sypialnia
gosc = cpoly(SE)
syp = cpoly(SE)

# --- skrzydło S: herbaciarnia (parter), taras południowy (dach)
her = poly(SE["QB"], SE["FB"], SW["FA"], SW["QA"])
# --- skrzydło NW: pralnia ze spiżarnią (parter), taras zachodni (dach)
pral = poly(SW["QB"], SW["FB"], N["FA"], N["QA"])

# --- narożnik SW: salon na dwie kondygnacje z końcami skrzydeł; patio za murem na cyplu
salon = cpoly(SW)
tP, tR = tcut(DP, RT), tcut(DR, RT)
patio = poly(SW["TA"], P("S", tP, RT), P("NW", -tP, RT), SW["TB"])
canopy = poly(SW["TA"], P("S", tR, RT), P("NW", -tR, RT), SW["TB"])

# ---------------------------------------------------------------- dom
H = House(
    "p08", "Trójkąt",
    "Trójkątny dom o boku 21,5 m ze ściętymi narożnikami. W środku ukryty sześciokątny ogród tropikalny pod szklaną harmonijką, "
    "na dachach dwóch niskich skrzydeł tarasy, a nad trzecim skrzydłem i dwoma narożnikami ciąg modułów piętra.",
    style=dict(fasada="tynk", dach="sedum", akcent="dab"),
    concept=[
        "Plan to trójkąt równoboczny o boku 21,5 m ze ściętymi narożnikami. Trzy skrzydła głębokości 3,2 m i trzy narożniki szczelnie otaczają sześciokątny ogród o powierzchni 35 m² i wysokości jednej kondygnacji; cały dom ma 160 m² powierzchni użytkowej.",
        "Od zewnątrz ogrodu nie widać: elewacje z białego tynku mają tylko okna, szczeliny i wysokie pasma, salon ma szkło wyłącznie do patio za murem wysokości 2,6 m na południowo-zachodnim cyplu, a przy wejściu stoją wiatrołap i łazienka gości bez szkła do ogrodu.",
        "Parter obchodzi się dookoła bez korytarzy: hol, biblioteka ze schodami kręconymi, pokój gościnny w narożniku, herbaciarnia, salon z kuchnią, pralnia ze spiżarnią i z powrotem hol. Hol, biblioteka, pokój gościnny i salon mają drzwi do ogrodu, herbaciarnia patrzy na niego przez stałe szkło.",
        "Salon z kuchnią ma 6,6 m wysokości i zajmuje narożnik południowo-zachodni z końcami obu skrzydeł: kuchnia w ramieniu przy pralni, stół w środku, wypoczynek przy szklanej ścianie patio. Część patio przy szkle ma daszek, reszta jest pod niebem.",
        "Dachy skrzydeł południowego i północno-zachodniego to tarasy z balustradą po obu stronach szklanego dachu ogrodu: południowy (15 m²) z wyjściem z sypialni, zachodni (10 m²) z wyjściem z biura. Dach ogrodu to harmonijka, która latem składa się nad jednym bokiem sześciokąta.",
        "Piętro to ciąg modułów nad narożnikiem północnym, skrzydłem wschodnim i narożnikiem południowo-wschodnim: biuro ze szkłem na północ i drzwiami na taras, galeria ze szklanym pasażem wzdłuż dachu ogrodu, przy niej garderoba i łazienka, na końcu sypialnia ze szklaną ścianą na południowy wschód. Najwyższy dach nad modułami jest zielony.",
    ],
    notes=dict(
        lato="Harmonijka dachu składa się nad jednym bokiem ogrodu, drzwi pokoi parteru do ogrodu stoją otworem, a życie przenosi się na patio za murem i na oba tarasy na dachach skrzydeł.",
        zima="Dach jest zamknięty, ogród działa jak szklarnia buforowa między skrzydłami, a pełne ściany, mur patio i małe okna od zewnątrz chronią dom przed wiatrem.",
        technologia="Szkielet drewniany z prefabrykowanych paneli ściennych, ciętych pod kątem 60° tylko w narożnikach; stropy i dachy z płyt CLT, tarasy na stropach skrzydeł z warstwą spadkową, dach szklany składany na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

H.ogrod("og", "Ogród tropikalny", garden, levels=1, roof_type="fold", style="tropikalny", seed=11)

# parter – narożnik N: wejście
H.room("wia", "Wiatrołap", "wiatrolap", wia, ext="solid")
H.room("laz0", "Łazienka gości", "lazienka", laz0)
H.room("hol", "Hol", "hol", hol)
# skrzydło NE – biblioteka ze schodami (przelotowa między holem a pokojem gościnnym)
H.room("bib", "Biblioteka", "biblioteka", bib, ext="band_high")
# narożnik SE – pokój gościnny
H.room("gosc", "Pokój gościnny", "gosc", gosc, ext={"SE": "band_high", "*": "windows"},
       label_at=(O[0] + 4.9 * math.cos(math.radians(30)), O[1] + 4.9 * math.sin(math.radians(30))))
# skrzydło S – herbaciarnia (przelotowa między pokojem gościnnym a salonem)
H.room("her", "Herbaciarnia", "herbaciarnia", her, ext="windows", garden="glass")
# narożnik SW – salon na dwie kondygnacje i patio za murem na cyplu
H.room("sal", "Salon z kuchnią", "salon_kuchnia", salon, levels=2, kitchen_at=300,
       ext={"pat": "glass_slide", "S": "windows", "NW": "band_high", "*": "band"})
H.room("pat", "Patio za murem", "patio", patio, roof=canopy, enclose="gwall")
# skrzydło NW – pralnia ze spiżarnią (przelotowa między kuchnią a holem)
H.room("pral", "Pralnia i spiżarnia", "pralnia", pral, ext="windows_sq", garden="band_high")

# piętro – moduły: biuro (N) → galeria → sypialnia (SE); garderoba i łazienka przy pasażu galerii
H.room("biu", "Biuro", "biuro", biu, level=1,
       ext={"taW": "glass_slide", "N": "glass", "NW": "windows", "NE": "windows", "*": "glass"})
H.room("gal", "Galeria", "hol", gal, level=1, ext={"NE": "slits", "*": "glass"}, floor="drewno")
H.room("gar", "Garderoba", "garderoba", gar, level=1)
H.room("laz1", "Łazienka", "lazienka", laz1, level=1)
H.room("syp", "Sypialnia", "sypialnia_glowna", syp, level=1,
       ext={"SE": "glass", "S": "windows", "taS": "glass_slide", "NW": "band", "*": "windows"})
H.room("taW", "Taras zachodni", "taras", pral, level=1)
H.room("taS", "Taras południowy", "taras", her, level=1)
H.stair("spiral", level=0, center=STAIR_C, r=1.0, start=150, sweep=300, n=16)

# połączenia
H.connect("wia", "hol", "door", at=0.7)
H.connect("hol", "laz0", "door")
H.connect("hol", "bib", "door", at=0.8)
H.connect("bib", "gosc", "door", at=0.2)
H.connect("gosc", "her", "door", at=0.8)
H.connect("her", "sal", "wide")
H.connect("sal", "pral", "door", at=0.3)
H.connect("pral", "hol", "door", at=0.7)
H.connect("biu", "gal", "door", at=0.8)
H.connect("gal", "gar", "door")
H.connect("gal", "laz1", "door")
H.connect("gal", "syp", "door")
H.connect("biu", "taW", "slide")
H.connect("syp", "taS", "slide")

H.entrance("wia", "N", at=0.7)
H.path(rect((W1[0] + N["TA"][0]) / 2 - 0.7, Y_TIP - 6.0, (W1[0] + N["TA"][0]) / 2 + 0.7, Y_TIP - 0.1))
H.tree(23.0, 6.0, "lipa")
H.tree(1.5, 17.5, "klon")
H.tree(22.5, 17.0, "brzoza")
H.tree(2.5, 4.5, "sosna")
CA, SA = math.cos(math.radians(30)), math.sin(math.radians(30))
H.cut("A–A", (O[0] - 11.0 * CA, O[1] + 11.0 * SA), (O[0] + 8.5 * CA, O[1] - 8.5 * SA))
H.cut("B–B", (O[0] + 0.8, Y_TIP - 2.0), (O[0] + 0.8, O[1] + RT + 2.0))
