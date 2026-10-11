"""P01 · Krużganek (wersja 2) – zwarty kwadrat wokół ukrytego ogrodu, tarasy na dachu parteru, moduły piętra od północy."""
from silnik import House, rect, circle

H = House(
    "p01", "Krużganek",
    "Kwadratowy dom 13 × 14 m, który z zewnątrz nie zdradza ogrodu w środku. Na dachu parteru wokół szklanego dachu ogrodu są dwa tarasy, a od północy stoją moduły piętra z sypialnią i biurem.",
    style=dict(fasada="tynk", dach="sedum", akcent="dab"),
    concept=[
        "Ogród 5,8 × 5,8 m jest ze wszystkich stron otoczony pokojami. Od zewnątrz dom ma tylko okna i szczeliny, więc ogrodu nie widać ani z drogi, ani od sąsiadów.",
        "Wchodzi się przez wiatrołap w narożniku, który nie ma szkła do ogrodu. Ogród otwiera się dopiero za drugimi drzwiami, w holu z biblioteką i schodami kręconymi.",
        "Parter obchodzi się dookoła bez korytarzy: hol z biblioteką, pralnia ze spiżarnią, herbaciarnia, salon z kuchnią, pokój gościnny i z powrotem wiatrołap.",
        "Salon z kuchnią ma 6,6 m wysokości. Od ogrodu jest cały ze szkła, a od południa wychodzi na patio za murem: częściowo zadaszone, schowane za ścianą wysokości 2,6 m.",
        "Dach parteru po obu stronach szklanego dachu ogrodu to tarasy z balustradą: zachodni przy sypialni, wschodni przy biurze. Najwyższy dach nad modułami piętra jest zielony.",
        "Na piętrze trzy moduły wokół tarasów: sypialnia ze szklaną ścianą od zachodu, galeria nad ogrodem i biuro przeszklone na pola od północy i na taras od południa.",
    ],
    notes=dict(
        lato="Połowa szklanego dachu zsuwa się nad drugą, ogród staje się otwartym dziedzińcem, a z tarasów zagląda się do niego z góry; patio za murem jest przedłużeniem salonu.",
        zima="Dach jest zamknięty, ogród działa jak bufor między pokojami, a mur patio i pełne ściany zewnętrzne chronią dom przed wiatrem.",
        technologia="Ściany z bloczków silikatowych na cienką spoinę, stropy i dach z prefabrykowanych płyt kanałowych, tarasy na stropie z warstwą spadkową, dach szklany systemowy na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

H.ogrod("og", "Ogród", rect(3.6, 3.6, 9.4, 9.4), roof_type="slide", style="japonski", seed=3)
# parter – pierścień pokoi wokół ogrodu
H.room("wia", "Wiatrołap", "wiatrolap", rect(0, 0, 3.0, 3.6), ext={"N": "slits", "W": "solid"})
H.room("hol", "Hol z biblioteką", "biblioteka", rect(3.0, 0, 10.0, 3.6), ext="slits")
H.room("pral", "Pralnia i spiżarnia", "pralnia", rect(10.0, 0, 12.8, 3.6), ext={"N": "band_high", "E": "windows_sq"})
H.room("gos", "Pokój gościnny", "gosc", rect(0, 3.6, 3.6, 9.4), ext="windows")
H.room("her", "Herbaciarnia", "herbaciarnia", rect(9.4, 3.6, 12.8, 9.4), ext="windows")
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(0, 9.4, 12.8, 13.8), levels=2, kitchen_at="E",
       ext={"pat": "glass_slide", "S": "solid", "W": "windows", "E": "windows", "N": "band"})
H.room("pat", "Patio za murem", "patio", rect(2.0, 13.8, 11.0, 17.6), roof=rect(2.0, 13.8, 11.0, 15.3), enclose="gwall")
H.stair("spiral", level=0, center=(8.3, 1.8), r=1.0, start=180, sweep=300, n=16)
# piętro – moduły od północy wokół tarasów
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(0, 0, 5.2, 3.6), level=1,
       ext={"W": "glass", "N": "windows", "taW": "glass_slide", "S": "glass"})
H.room("laz", "Łazienka", "lazienka", rect(5.2, 0, 7.0, 3.6), level=1, ext={"N": "band_high", "S": "band_high"})
H.room("gal", "Galeria nad ogrodem", "galeria", rect(7.0, 0, 9.6, 3.6), level=1, ext={"N": "slits", "S": "glass"})
H.room("biu", "Biuro", "biuro", rect(9.6, 0, 12.8, 3.6), level=1, ext={"N": "glass", "E": "windows", "taE": "glass_slide"})
H.room("taW", "Taras zachodni", "taras", rect(0, 3.6, 3.6, 9.4), level=1)
H.room("taE", "Taras wschodni", "taras", rect(9.4, 3.6, 12.8, 9.4), level=1)

H.connect("wia", "hol", "door", at=0.7)
H.connect("wia", "gos", "door")
H.connect("hol", "pral", "door")
H.connect("pral", "her", "door")
H.connect("her", "sal", "wide")
H.connect("sal", "gos", "door")
H.connect("syp", "laz", "door")
H.connect("syp", "gal", "door")
H.connect("gal", "biu", "door")
H.connect("syp", "taW", "slide")
H.connect("biu", "taE", "slide")
H.entrance("wia", "N")
H.exit("pral", "E", kind="door", width=0.9)
H.path(rect(0.8, -6, 2.2, -0.2))
H.tree(-3.5, 5.0, "brzoza")
H.tree(16.5, 15.0, "klon")
H.tree(17.0, 2.0, "lipa")
H.cut("A–A", (6.5, -2.0), (6.5, 19.5))
H.cut("B–B", (-2.0, 6.5), (15.0, 6.5))
