"""P16 · Owal – prostokąt z trawertynu, w środku eliptyczny ogród pod kopułą z przesłoną."""
from shapely import set_precision

from silnik import House, rect, ellipse

# prostokąt 21 × 17 m, elipsa ogrodu 12 × 9 m (półosie 6 × 4,5) w środku
W, D = 21.0, 17.0
CX, CY, RX, RY = W / 2, D / 2, 6.0, 4.5
E = ellipse(CX, CY, RX, RY)

# linie podziału pierścienia (przecinają elipsę)
XW, XE = 6.5, 14.5      # granice pasm północnego i południowego
YN, YS = 6.2, 10.8      # granice pasm zachodniego i wschodniego


def cut(x1, y1, x2, y2):
    """Fragment prostokąta minus elipsa ogrodu – pokój ze ścianą prostą i krzywą.

    set_precision usuwa zdublowane wierzchołki, gdy linia podziału trafia dokładnie
    w wierzchołek wielokąta elipsy (inaczej silnik rysuje tam ścianę o zerowej długości)."""
    return set_precision(rect(x1, y1, x2, y2).difference(E), 1e-6)


H = House(
    "p16", "Owal",
    "Prostokątny dom z trawertynu, w którego środek wycięto eliptyczny ogród pod szklaną kopułą. Każdy pokój ma jedną ścianę prostą od zewnątrz i jedną krzywą od ogrodu.",
    style=dict(fasada="trawertyn", dach="sedum"),
    concept=[
        "Obrys to prostokąt 21 × 17 m, a w nim elipsa 12 × 9 m. Pokoje wypełniają przestrzeń między prostą elewacją a krzywą szklaną ścianą ogrodu, więc każdy ma inny kształt.",
        "Dom składa się z dwóch zazębionych liter L: niskiej od północy i zachodu oraz piętrowej od wschodu i południa. Nad niskim skrzydłem szklany bęben ogrodu wychodzi ponad dach.",
        "Kopuła nad ogrodem ma przesłonę jak migawka aparatu: latem otwiera okrągły otwór i wypuszcza ciepłe powietrze, zimą jest zamknięta.",
        "Od wejścia prowadzą dwie amfilady: przez galerię i bibliotekę ze schodami do biura oraz przez pracownię, salę muzyczną i patio do salonu.",
        "Biuro od wschodu ma prostą szklaną ścianę na pole i krzywą szklaną ścianę na ogród. Nad nim leży sypialnia z takim samym podwójnym przeszkleniem.",
        "Salon z kuchnią ma dwie kondygnacje wysokości i łączy się z patio w narożniku, które zimą zamyka szklana harmonijka.",
    ],
    notes=dict(
        lato="Przesłona kopuły i harmonijki patio są otwarte, a powietrze przepływa z ogrodu przez patio na zewnątrz.",
        zima="Kopuła i patio są zamknięte; ogród zbiera ciepło słońca i oddaje je pokojom przez szklane ściany.",
        technologia="Żelbetowy szkielet ze ścianami z bloczków, elewacja z płyt trawertynu. Krzywe ściany ogrodu z prefabrykowanych łukowych paneli szklanych.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

H.ogrod("og", "Ogród", E, levels=2, roof_type="iris", style="oranzeria", seed=4, edge="glass")

# --- niska litera L: północ i zachód -------------------------------------
WC = rect(4.7, 0, XW, 3.2)
PRAL = rect(0, 3.4, 2.4, YN)
H.room("pra", "Pracownia", "pracownia", cut(0, 0, XW, YN).difference(WC).difference(PRAL),
       ext={"N": "windows", "W": "slits"})
H.room("wc", "WC", "wc", WC)
H.room("pral", "Pralnia", "pralnia", PRAL, ext="windows_sq")
H.room("wia", "Wiatrołap", "wiatrolap", cut(XW, 0, 9.5, YN), ext="slits")
H.room("gal", "Galeria", "galeria", cut(9.5, 0, XE, YN), ext="slits")
H.room("muz", "Sala muzyczna", "muzyczny", cut(0, YN, XW, YS), ext={"W": "slits", "S": "windows"})
H.room("pat", "Patio sezonowe", "patio_sezonowe", cut(0, YS, 7.5, D))

# --- wysoka litera L: wschód i południe ----------------------------------
H.room("bib", "Biblioteka", "biblioteka", cut(XE, 0, W, YN), ext={"N": "slits", "E": "solid"})
H.stair("spiral", level=0, center=(16.0, 1.5), r=1.1, start=135, sweep=300, n=16)
H.room("biu", "Biuro", "biuro", cut(XE, YN, W, YS), ext={"E": "glass_slide"}, garden="glass_slide")
H.room("sal", "Salon", "salon", cut(7.5, YS, XE, D), levels=2,
       ext={"S": "glass", "W": "glass"}, garden="glass")
H.room("kuch", "Kuchnia z jadalnią", "kuchnia", cut(XE, YS, W, D), levels=2,
       ext={"S": "slits", "E": "solid"}, garden="glass", kitchen_at="E")

# --- piętro ------------------------------------------------------------------
H.room("hol", "Hol", "hol", rect(XE, 0, 17.6, 3.4), level=1, ext={"N": "slits", "W": "windows", "E": "solid"})
H.room("gar", "Garderoba", "garderoba", cut(XE, 3.4, 17.6, YN), level=1, ext="solid", garden="solid")
H.room("log", "Loggia", "loggia", rect(17.6, 0, W, 2.4), level=1, enclose="railing")
H.room("laz", "Łazienka", "lazienka", rect(17.6, 2.4, W, YN), level=1, ext={"E": "band_high", "N": "glass_slide"})
H.room("syp", "Sypialnia", "sypialnia_glowna", cut(XE, YN, W, YS), level=1, ext={"E": "glass_slide"}, garden="glass")

# --- połączenia ---------------------------------------------------------
H.connect("wia", "gal", "wide")
H.connect("wia", "pra", "door")
H.connect("wia", "wc", "door")
H.connect("pra", "pral", "door", at=0.8)
H.connect("pra", "muz", "wide")
H.connect("muz", "pat", "slide")
H.connect("pat", "sal", "slide")
H.connect("pat", "og", "fold")
H.connect("sal", "kuch", "open")
H.connect("gal", "bib", "wide", at=0.8)
H.connect("bib", "biu", "slide", at=0.8)
H.connect("sal", "og", "slide")
H.connect("hol", "gar", "door")
H.connect("gar", "syp", "door")
H.connect("gar", "laz", "door")
H.connect("laz", "log", "slide")

H.entrance("wia", "N")
H.exit("sal", "S", at=0.5, kind="slide")

# --- teren ------------------------------------------------------------------
H.path(rect(7.3, -6, 8.7, -0.2))
H.tree(-3.5, -2.5, "brzoza")
H.tree(25.0, 3.0, "klon")
H.tree(-3.0, 20.0, "lipa")
H.tree(24.5, 20.5, "sosna")
H.cut("A–A", (CX, -2.0), (CX, D + 2.0))
H.cut("B–B", (-2.0, CY), (W + 2.0, CY))
