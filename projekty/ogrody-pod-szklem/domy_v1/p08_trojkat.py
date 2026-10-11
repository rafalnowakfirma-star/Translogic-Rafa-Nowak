"""P08 · Trójkąt – trójkątny dom o ściętych narożnikach wokół sześciokątnego ogrodu pod szklaną harmonijką."""
import math

from silnik import House, poly, rect

# ---------------------------------------------------------------- geometria
# Trójkąt równoboczny (oś ścian zewnętrznych) o promieniu wpisanym RT → bok 27,7 m.
# Każdy punkt liczymy jedną funkcją P(bok, t, d): d = odległość od środka wzdłuż normalnej boku,
# t = przesunięcie wzdłuż boku. Punkty wspólne sąsiadów są liczone raz i wstawiane do obu wielokątów
# (także tam, gdzie wierzchołek jednego pokoju leży na krawędzi drugiego), więc unia pokoi jest czysta.
SQ3 = math.sqrt(3)
O = (14.0, 16.6)
RT = 8.0                 # linia zewnętrzna
D = 4.3                  # głębokość skrzydeł
RI = RT - D              # linia wewnętrzna (ogród)
SIDE = {"S": 90.0, "NE": 330.0, "NW": 210.0}          # kąty normalnych boków
CORNER = {"N": ("NW", "NE"), "SE": ("NE", "S"), "SW": ("S", "NW")}   # (bok z narożnikiem przy +t, bok przy -t)
_NORM = {s: (round(math.cos(math.radians(a)), 12), round(math.sin(math.radians(a)), 12)) for s, a in SIDE.items()}


def P(side, t, d):
    nx, ny = _NORM[side]
    return (O[0] + nx * d - ny * t, O[1] + ny * d + nx * t)


def tcut(d, r):
    """Parametr t, w którym prosta ścinająca narożnik (odl. d od środka) przecina linię o promieniu r."""
    return r * SQ3 - 2 * (2 * r - d) / SQ3


def between(p, q, y):
    """Punkt odcinka p–q o rzędnej y."""
    return (p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1]), y)


G = 4.6                  # ścięcie narożników ogrodu → sześciokąt (boki 6,4 m i 3,2 m)
TP = tcut(G, RI)         # wierzchołek ogrodu na linii wewnętrznej (±3,18 od środka boku)
E_N, E_SE = 2.1, 1.6     # o ile skrzydła wchodzą w narożniki N i SE
D_S = 9.4                # szklana ściana salon/patio (odległość od środka)
TS = tcut(D_S, RT)       # jej przecięcie z bokami zewnętrznymi
DC_N, DC_SE, DC_SW = 10.0, 10.5, 13.0   # ścięcia narożników domu


def corner(c, e, dc):
    sA, sB = CORNER[c]
    tT = tcut(dc, RT)
    return dict(PA=P(sA, TP, RI), QA=P(sA, TP + e, RI), FA=P(sA, TP + e, RT), TA=P(sA, tT, RT),
                TB=P(sB, -tT, RT), FB=P(sB, -(TP + e), RT), QB=P(sB, -(TP + e), RI), PB=P(sB, -TP, RI))


N, SE, SW = corner("N", E_N, DC_N), corner("SE", E_SE, DC_SE), corner("SW", 0, DC_SW)

# --- narożnik N: pas wejściowy (wiatrołap, WC) + hol
Y_STRIP = 8.5
Y_TIP = N["TA"][1]
L1, L2 = between(N["QA"], N["FA"], Y_STRIP), between(N["QB"], N["FB"], Y_STRIP)
X_WC = 15.0
W1, W2 = (X_WC, Y_TIP), (X_WC, Y_STRIP)
hol = poly(N["PA"], N["QA"], L1, W2, L2, N["QB"], N["PB"])
wia = poly(L1, N["FA"], N["TA"], W1, W2)
wc = poly(W1, N["TB"], N["FB"], L2, W2)

# --- skrzydło NW: spiżarnia i pokój muzyczny (między salonem a holem)
T_K, T_M = -0.2, 1.4
K_in, K_out = P("NW", T_K, RI), P("NW", T_K, RT)
M_in, M_out = P("NW", T_M, RI), P("NW", T_M, RT)
spi = poly(K_in, M_in, M_out, K_out)
muz = poly(M_in, N["PA"], N["QA"], L1, N["FA"], M_out)

# --- skrzydło NE: biuro i garderoba przelotowa (między holem a sypialnią)
T_G = 2.0
G_in, G_out = P("NE", T_G, RI), P("NE", T_G, RT)
biu = poly(N["QB"], N["PB"], G_in, G_out, N["FB"], L2)
gar = poly(G_in, SE["PA"], SE["QA"], SE["FA"], G_out)

# --- skrzydło S (poziome): biblioteka, pralnia, łazienka.  x maleje z t.
X_E, X_H = SE["QB"][0], SW["PA"][0]           # 19,18 (ściana sypialni), 10,82 (ściana salonu)
Y_IN, Y_OUT = SW["PA"][1], SE["FB"][1]        # 20,3 (linia ogrodu), 24,6 (elewacja południowa)
X_LIB, X_PRA = 14.5, 16.5
bib = rect(X_H, Y_IN, X_LIB, Y_OUT)
pra = rect(X_LIB, Y_IN, X_PRA, Y_OUT)
laz = poly((X_PRA, Y_IN), SE["PB"], SE["QB"], SE["FB"], (X_PRA, Y_OUT))

# --- narożnik SW: salon (razem z końcem skrzydła NW) i patio na samym cyplu
SA, SB = P("S", TS, RT), P("NW", -TS, RT)
salon = poly(SW["PA"], (X_H, Y_OUT), SA, SB, K_out, K_in, SW["PB"])
patio = poly(SA, SW["TA"], SW["TB"], SB)
D_R = 11.2               # zadaszona część patio (od szkła do linii D_R)
canopy = poly(SA, P("S", tcut(D_R, RT), RT), P("NW", -tcut(D_R, RT), RT), SB)

# --- narożnik SE: sypialnia (parter); na piętrze pokój gościnny i taras na cyplu
syp = poly(SE["PA"], SE["QA"], SE["FA"], SE["TA"], SE["TB"], SE["FB"], SE["QB"], SE["PB"])
D_T = 8.4                # linia podziału piętra nad sypialnią: pokój / taras
S1, S2 = P("NE", tcut(D_T, RT), RT), P("S", -tcut(D_T, RT), RT)

# --- ogród: sześciokąt z wierzchołkami pośrednimi tam, gdzie kończą się pokoje skrzydeł
garden = poly(N["PA"], N["PB"], G_in, SE["PA"], SE["PB"], (X_PRA, Y_IN), (X_LIB, Y_IN), SW["PA"], SW["PB"], K_in, M_in)

# --- piętro nad skrzydłem południowym (nadwieszone 1,8 m na południe) i nad sypialnią
Y_CANT = Y_OUT + 1.8
X_G, X_B = 13.2, 15.0    # koniec galerii ze schodami, koniec łazienki
Y_COR = Y_IN + 1.4
hol1 = poly((X_H, Y_IN), (X_G, Y_IN), (X_G, Y_COR), (X_G, Y_CANT), (X_H, Y_CANT), (X_H, Y_OUT))
kor = poly((X_G, Y_IN), SE["PB"], SE["QB"], (X_E, Y_COR), (X_B, Y_COR), (X_G, Y_COR))
laz1 = rect(X_G, Y_COR, X_B, Y_CANT)
pok1 = poly((X_B, Y_COR), (X_E, Y_COR), SE["FB"], (X_E, Y_CANT), (X_B, Y_CANT))
gosc = poly(SE["PA"], SE["QA"], SE["FA"], S1, S2, SE["FB"], (X_E, Y_COR), SE["QB"], SE["PB"])
taras = poly(S1, SE["TA"], SE["TB"], S2)

# ---------------------------------------------------------------- dom
H = House(
    "p08", "Trójkąt",
    "Trójkątny dom o ściętych narożnikach. W środku sześciokątny ogród tropikalny pod szklaną harmonijką, a każdy z trzech narożników ma inną funkcję: wejście, salon na dwie kondygnacje z patio na cyplu i sypialnię z widokiem.",
    style=dict(fasada="tynk", dach="zwir", akcent="dab"),
    concept=[
        "Plan to trójkąt równoboczny o boku 27,7 m ze ściętymi narożnikami. Trzy skrzydła o głębokości 4,3 m otaczają sześciokątny ogród, a narożniki są większe od skrzydeł, więc mieszczą główne pokoje: wejście, salon i sypialnię.",
        "Ogród ma 55 m² i 7 m wysokości. Jego dach to szklana harmonijka: zimą zamknięta, latem złożona w pakiet nad jednym bokiem. Ponad niskimi skrzydłami ściany ogrodu są szklane, więc z zewnątrz widać palmy ponad dachami.",
        "Biuro zajmuje skrzydło północno-wschodnie i jest przeszklone od ogrodu i od łąki. Wchodzi się do niego prosto z holu przy wejściu, więc klienci nie przechodzą przez dom.",
        "Zamiast korytarzy są amfilady: od holu przez pokój muzyczny i spiżarnię do kuchni, a od salonu przez bibliotekę, pralnię i łazienkę do sypialni. Trzecia droga prowadzi przez ogród, na który każdy pokój ma drzwi.",
        "Salon z kuchnią ma 6,5 m wysokości i zajmuje narożnik południowo-zachodni. Jego szklana ściana otwiera się na patio wycięte w cyplu trójkąta: połowa patio ma daszek, połowa jest pod niebem.",
        "Nad skrzydłem południowym jest piętro: kręcone schody z biblioteki prowadzą na galerię z balustradą nad salonem, dalej szklana galeria nad ogrodem, łazienka, pokój dziecięcy i pokój gościnny na dachu sypialni z tarasem na cyplu. Piętro nadwiesza się 1,8 m nad elewacją południową i zacienia szkło parteru.",
    ],
    notes=dict(
        lato="Harmonijka dachu składa się w pakiet nad jednym bokiem sześciokąta, szkło salonu i biura rozsuwa się, a nadwieszone piętro zacienia południowe okna parteru.",
        zima="Dach jest zamknięty, ogród działa jak szklarnia buforowa między skrzydłami, a niskie zimowe słońce wchodzi pod nadwieszenie do biblioteki i łazienki.",
        technologia="Szkielet drewniany z prefabrykowanych paneli ściennych: trójkątny plan składa się z prostych paneli ciętych pod kątem 60° tylko w narożnikach. Nadwieszenie piętra na belkach z drewna klejonego, dach szklany na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

H.ogrod("og", "Ogród tropikalny", garden, levels=2, roof_type="fold", style="tropikalny", seed=11)

# narożnik N – wejście
H.room("wia", "Wiatrołap", "wiatrolap", wia, ext="solid")
H.room("wc", "WC", "wc", wc)
H.room("hol", "Hol", "hol", hol)
# skrzydło NW – pokój muzyczny i spiżarnia (przelotowe) do kuchni
H.room("muz", "Pokój muzyczny", "muzyczny", muz, ext="windows")
H.room("spi", "Spiżarnia", "spizarnia", spi)
# narożnik SW – salon na dwie kondygnacje i patio na cyplu
H.room("sal", "Salon z kuchnią", "salon_kuchnia", salon, levels=2,
       ext={"SW": "glass_slide", "S": "glass_slide", "NW": "band_high"}, kitchen_at=300)
H.room("pat", "Patio", "patio", patio, roof=canopy, ext={"S": "low", "NW": "low", "SW": "open"})
# skrzydło S – biblioteka ze schodami, pralnia, łazienka (amfilada do sypialni)
H.room("bib", "Biblioteka", "biblioteka", bib, ext="windows")
H.room("pra", "Pralnia i kotłownia", "pralnia", pra)
H.room("laz", "Łazienka", "lazienka", laz, garden="solid")
# narożnik SE – sypialnia z przeszkloną ścianą na krajobraz
H.room("syp", "Sypialnia", "sypialnia_glowna", syp, ext={"SE": "glass_slide", "S": "windows", "NE": "solid"})
# skrzydło NE – garderoba przelotowa i biuro przeszklone z obu stron
H.room("gar", "Garderoba", "garderoba", gar)
H.room("biu", "Biuro", "biuro", biu, ext={"NE": "glass_slide"}, garden="glass_slide")

# piętro
H.room("hol1", "Galeria", "hol", hol1, level=1, ext="glass", garden="glass", floor="drewno")
H.room("kor", "Galeria nad ogrodem", "korytarz", kor, level=1, ext="glass", garden="glass", floor="drewno")
H.room("laz1", "Łazienka", "lazienka", laz1, level=1)
H.room("pok1", "Pokój", "pokoj", pok1, level=1, ext={"S": "band", "*": "solid"})
H.room("gos", "Pokój gościnny", "gosc", gosc, level=1, ext={"SE": "glass_slide", "*": "solid"})
H.room("tar", "Taras", "taras", taras, level=1)
H.stair("spiral", level=0, center=(12.0, 21.5), r=1.0, start=200, sweep=330, n=16)

# połączenia
H.connect("wia", "hol", "wide")
H.connect("hol", "wc", "door")
H.connect("hol", "muz", "wide")
H.connect("muz", "spi", "door")
H.connect("spi", "sal", "door", at=0.2)
H.connect("sal", "bib", "wide", at=0.85)
H.connect("bib", "pra", "door", at=0.3)
H.connect("pra", "laz", "door", at=0.3)
H.connect("laz", "syp", "slide")
H.connect("syp", "gar", "door")
H.connect("gar", "biu", "door")
H.connect("biu", "hol", "double")
H.connect("hol1", "sal", "railing")
H.connect("hol1", "kor", "open")
H.connect("kor", "laz1", "door")
H.connect("kor", "pok1", "door")
H.connect("kor", "gos", "door")

H.entrance("wia", "N")
H.path(rect(13.3, 0.0, 14.7, Y_TIP - 0.1))
H.tree(25.5, 6.5, "lipa")
H.tree(0.5, 29.0, "klon")
H.tree(28.0, 27.5, "brzoza")
H.tree(2.5, 8.0, "sosna")
H.cut("A–A", (1.5, 23.8), (23.0, 11.4))
H.cut("B–B", (29.0, 22.0), (-1.0, 22.0))
