"""P16 · Owal – prostokąt z trawertynu, w środku eliptyczny ogród pod kopułą z przesłoną."""
from silnik import House, rect, ellipse

# prostokąt 21 × 17 m, elipsa ogrodu 12 × 9 m (półosie 6 × 4,5) w środku
W, D = 21.0, 17.0
CX, CY, RX, RY = W / 2, D / 2, 6.0, 4.5
E = ellipse(CX, CY, RX, RY)

# linie podziału pierścienia (przecinają elipsę)
XW, XE = 6.5, 14.5      # granice pasm północnego i południowego
YN, YS = 6.2, 10.8      # granice pasm zachodniego i wschodniego


def cut(x1, y1, x2, y2):
    """Fragment prostokąta minus elipsa ogrodu – pokój ze ścianą prostą i krzywą."""
    return rect(x1, y1, x2, y2).difference(E)


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
WC = rect(4.8, 0, XW, 2.2)
PRAL = rect(0, 3.4, 2.4, YN)
H.room("pra", "Pracownia", "pracownia", cut(0, 0, XW, YN).difference(WC).difference(PRAL),
       ext={"N": "windows", "W": "windows"})
H.room("wc", "WC", "wc", WC)
H.room("pral", "Pralnia", "pralnia", PRAL, ext="windows_sq")
H.room("wia", "Wiatrołap", "wiatrolap", cut(XW, 0, 9.5, YN), ext="slits")
H.room("gal", "Galeria", "galeria", cut(9.5, 0, XE, YN), ext="slits")
H.room("muz", "Sala muzyczna", "muzyczny", cut(0, YN, XW, YS), ext={"W": "windows"})
H.room("pat", "Patio sezonowe", "patio_sezonowe", cut(0, YS, XW, D))

# --- wysoka litera L: wschód i południe ----------------------------------
H.room("bib", "Biblioteka", "biblioteka", cut(XE, 0, W, YN), ext={"N": "slits", "E": "windows"})
H.stair("U", level=0, rect=(16.35, 0.35, 20.65, 2.65), up="E")
H.room("biu", "Biuro", "biuro", cut(XE, YN, W, YS), ext={"E": "glass_slide"}, garden="glass_slide")
H.room("sal", "Salon z kuchnią", "salon_kuchnia", cut(XW, YS, W, D), levels=2,
       ext={"S": "glass", "W": "glass", "E": "windows"}, garden="glass", kitchen_at="E")

# --- piętro ------------------------------------------------------------------
H.room("hol", "Hol", "hol", rect(XE, 0, W, 3.0), level=1, ext={"N": "slits", "W": "windows", "E": "slits"})
H.room("gar", "Garderoba", "garderoba", cut(XE, 3.0, 17.6, YN), level=1, ext="band_high", garden="band_high")
H.room("laz", "Łazienka", "lazienka", rect(17.6, 3.0, W, YN), level=1, ext="band_high")
H.room("syp", "Sypialnia", "sypialnia_glowna", cut(XE, YN, W, YS), level=1, ext={"E": "glass_slide"}, garden="glass")

# --- połączenia ---------------------------------------------------------
H.connect("wia", "gal", "wide")
H.connect("wia", "pra", "door")
H.connect("wia", "wc", "door")
H.connect("pra", "pral", "door")
H.connect("pra", "muz", "wide")
H.connect("muz", "pat", "slide")
H.connect("pat", "sal", "slide")
H.connect("gal", "bib", "wide")
H.connect("bib", "biu", "double")
H.connect("sal", "og", "slide")
H.connect("hol", "gar", "door")
H.connect("gar", "syp", "door")
H.connect("syp", "laz", "door")

H.entrance("wia", "N")
H.exit("sal", "S", at=0.35, kind="slide")

# --- teren ------------------------------------------------------------------
H.path(rect(7.3, -6, 8.7, -0.2))
H.tree(-3.5, -2.5, "brzoza")
H.tree(25.0, 3.0, "klon")
H.tree(-3.0, 20.0, "lipa")
H.tree(24.5, 20.5, "sosna")
H.cut("A–A", (CX, -2.0), (CX, D + 2.0))
H.cut("B–B", (-2.0, CY), (W + 2.0, CY))
