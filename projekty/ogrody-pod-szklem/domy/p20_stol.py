"""P20 · Stół pod niebem (wersja 2) – dom na planie trapezu (szerszy od południa), w środku ogród zimowy
z jadalnią w kształcie trapezu pod harmonijkowym szklanym dachem; kuchnia z harmonijką na szerokim boku,
wysoki salon w narożniku południowo-zachodnim, wejście i pomieszczenia gospodarcze od wąskiego, północnego końca.
Tarasy na dachu biblioteki (zachód) i kuchni (południe), moduły piętra nad blokiem północnym i pracownią."""
from silnik import House, rect, poly, union

# ---------------------------------------------------------------- geometria trapezu
X0 = 10.0                 # oś symetrii
HN = 5.1                  # połowa szerokości na północy (y = 0) → 10,2 m
S = 0.21                  # przyrost połowy szerokości na 1 m w stronę południa (boki pod kątem ~12°)
D = 12.4                  # głębokość domu → na południu 2·(HN + S·D) = 15,4 m
YN = 3.4                  # blok północny (wejście, hol, pralnia)
YG1, YG2 = 3.4, 9.4       # ogród: krawędź północna i południowa (6,0 m głębokości)
YB = 6.8                  # koniec biblioteki / początek salonu w skrzydle zachodnim
YO = 7.0                  # koniec biura na piętrze / początek tarasu nad pracownią
GN, GS = 1.85, 2.85       # połowa szerokości ogrodu na północy (3,7 m) i południu (5,7 m)
XK = 8.4                  # ściana salon | kuchnia
XH1, XH2 = 8.0, 13.2      # hol (parter) – między wiatrołapem a pralnią
XG = 8.6                  # ściana sypialnia | galeria (piętro)


def xw(y):
    return X0 - HN - S * y


def xe(y):
    return X0 + HN + S * y


def gw(y):
    return X0 - (GN + (GS - GN) * (y - YG1) / (YG2 - YG1))


def ge(y):
    return X0 + (GN + (GS - GN) * (y - YG1) / (YG2 - YG1))


garden = poly((gw(YG1), YG1), (ge(YG1), YG1), (ge(YG2), YG2), (gw(YG2), YG2))
wia = poly((xw(0), 0), (XH1, 0), (XH1, 1.6), (6.7, 1.6), (6.7, YN), (xw(YN), YN))
wc = rect(6.7, 1.6, XH1, YN)
hol = rect(XH1, 0, XH2, YN)
pral = poly((XH2, 0), (xe(0), 0), (xe(YN), YN), (XH2, YN))
bib = poly((xw(YG1), YG1), (gw(YG1), YG1), (gw(YB), YB), (xw(YB), YB))
sal = poly((xw(YB), YB), (gw(YB), YB), (gw(YG2), YG2), (XK, YG2), (XK, D), (xw(D), D))
kuch = poly((XK, YG2), (xe(YG2), YG2), (xe(D), D), (XK, D))
prac = poly((ge(YG1), YG1), (xe(YG1), YG1), (xe(YG2), YG2), (ge(YG2), YG2))
# piętro
syp = poly((xw(0), 0), (XG, 0), (XG, YN), (xw(YN), YN))
gal = rect(XG, 0, XH2, YN)
laz = poly((XH2, 0), (xe(0), 0), (xe(YN), YN), (XH2, YN))
biu = poly((ge(YG1), YG1), (xe(YG1), YG1), (xe(YO), YO), (ge(YO), YO))
taS = union(poly((ge(YO), YO), (xe(YO), YO), (xe(YG2), YG2), (ge(YG2), YG2)), kuch)
# patio za murem na południe od salonu
PX1, PX2, PY = 3.0, 8.0, D + 3.0
patio = rect(PX1, D, PX2, PY)
canopy = rect(PX1, D, PX2, D + 1.4)

H = House(
    "p20", "Stół pod niebem",
    "Dom na planie trapezu: 15,6 m od południa, 10,4 m od północy. W środku ogród zimowy w kształcie trapezu, "
    "w którym stoi stół jadalny pod harmonijkowym szklanym dachem; kuchnia otwiera się na niego szklaną harmonijką.",
    style=dict(fasada="corten", dach="sedum", akcent="dab"),
    concept=[
        "Plan jest trapezem: 15,6 m na południu, 10,4 m na północy, boki pochylone o 12°. Ogród zimowy z jadalnią powtarza ten kształt w środku domu (3,6 m od północy, 6 m od południa, 25 m²) i ze wszystkich stron dotyka pokoi, więc z zewnątrz go nie widać.",
        "Stół na 8 osób stoi w ogrodzie przy szklanej harmonijce kuchni, która zajmuje cały szeroki, południowy bok. Latem harmonijka jest złożona i kuchnia, stół i rośliny tworzą jedną przestrzeń; w mroźne noce albo gdy dach jest otwarty w deszczu, rozkłada się ją i ogród zimowy jest zamknięty.",
        "Dach ogrodu to szklana harmonijka, która latem składa się nad północnym, węższym końcem – stół stoi wtedy pod gołym niebem.",
        "Salon ma 6,6 m wysokości i zajmuje narożnik południowo-zachodni: szkło do ogrodu na dwóch ścianach narożnika i szkło na patio za murem 2,6 m od południa; na zewnątrz tylko okna, więc przez salon nie widać ogrodu na wylot.",
        "Wejście jest od wąskiego, północnego końca: wiatrołap z WC, hol ze schodami kręconymi i pralnia ze spiżarnią nie mają szkła do ogrodu. Parter obchodzi się dookoła bez korytarzy: wiatrołap, biblioteka, salon, kuchnia, pracownia, hol.",
        "Dachy parteru po bokach szklanego dachu to tarasy: zachodni nad biblioteką przy sypialni i południowy nad kuchnią i końcem pracowni przy biurze. Na piętrze moduły przelotowe: sypialnia ze szklaną ścianą od zachodu, galeria ze schodami nad holem, łazienka i biuro przeszklone na wschód i na taras; najwyższy dach nad nimi jest zielony.",
    ],
    notes=dict(
        lato="Harmonijka dachu składa się nad północnym końcem ogrodu, harmonijka kuchni jest złożona i jada się przy stole pod niebem; z tarasów na dachu biblioteki i kuchni zagląda się do ogrodu z góry, a salon otwiera się na patio za murem.",
        zima="Dach i harmonijka kuchni są zamknięte, ogród z jadalnią jest szklarnią o temperaturze pokojowej, do której wchodzi się drzwiami w harmonijce, z salonu i z biblioteki; cortenowe ściany z małymi oknami chronią dom od wiatru.",
        technologia="Ściany z bloczków keramzytowych na klej (skośne boki trapezu to zwykłe ściany, tylko narożniki cięte pod kątem), stropy i dachy z płyt CLT, tarasy na stropach parteru z warstwą spadkową; elewacja i mur patio z blachy cortenowskiej na ruszcie, dach szklany harmonijkowy na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

H.ogrod("og", "Ogród zimowy z jadalnią", garden, levels=1, roof_type="fold", style="jadalnia", seed=5)

# parter – blok północny bez szkła do ogrodu
H.room("wia", "Wiatrołap", "wiatrolap", wia, ext={"N": "solid", "W": "slits"})
H.room("wc", "WC", "wc", wc)
H.room("hol", "Hol", "hol", hol, garden="solid", ext={"N": "slits"})
H.room("pral", "Pralnia i spiżarnia", "pralnia", pral)
# skrzydła
H.room("bib", "Biblioteka", "biblioteka", bib, ext={"W": "band_high"})
H.room("sal", "Salon", "salon", sal, levels=2,
       ext={"pat": "glass_slide", "taW": "band_high", "taS": "band_high", "N": "glass", "E": "glass", "W": "windows", "S": "band"})
H.room("pat", "Patio za murem", "patio", patio, roof=canopy, enclose="gwall")
H.room("kuch", "Kuchnia", "kuchnia", kuch, garden="fold", kitchen_at="E", ext={"S": "band_high", "E": "windows"})
H.room("prac", "Pracownia", "pracownia", prac, ext={"E": "windows"})
H.stair("spiral", level=0, center=(11.7, 1.85), r=1.0, start=180, sweep=300, n=16)

# piętro – moduły wokół tarasów
H.room("syp", "Sypialnia", "sypialnia_glowna", syp, level=1,
       ext={"W": "glass", "N": "windows", "taW": "glass_slide", "S": "glass"})
H.room("gal", "Galeria nad ogrodem", "galeria", gal, level=1, ext={"N": "windows", "S": "glass"}, floor="drewno")
H.room("laz", "Łazienka", "lazienka", laz, level=1)
H.room("biu", "Biuro", "biuro", biu, level=1, ext={"W": "glass", "E": "glass", "taS": "glass_slide"})
H.room("taW", "Taras zachodni", "taras", bib, level=1)
H.room("taS", "Taras południowy", "taras", taS, level=1)

# połączenia – parter (pętla wokół ogrodu)
H.connect("wia", "hol", "door")
H.connect("wia", "wc", "door")
H.connect("wia", "bib", "door", at=0.3)
H.connect("hol", "prac", "door")
H.connect("hol", "pral", "door", at=0.3)
H.connect("bib", "sal", "door", at=0.2)
H.connect("sal", "kuch", "wide", at=0.35)
H.connect("kuch", "prac", "door", at=0.3)
H.connect("kuch", "og", "door", at=0.88)
# piętro
H.connect("gal", "syp", "door", at=0.3)
H.connect("gal", "laz", "door", at=0.3)
H.connect("gal", "biu", "door")
H.connect("syp", "taW", "slide")
H.connect("biu", "taS", "slide")

H.entrance("wia", "N")
H.exit("pral", "E", kind="door", width=0.9)
H.path(rect(5.7, -6.0, 7.1, -0.2))
H.tree(-1.5, 4.5, "brzoza")
H.tree(21.0, 14.0, "klon")
H.tree(20.0, 1.5, "lipa")
H.tree(0.5, 17.5, "sosna")
H.cut("A–A", (11.7, -3.0), (11.7, 16.5))
H.cut("B–B", (-2.0, 7.6), (22.0, 7.6))
