"""P10 · Monolit (wersja 2) – zamknięty kamienny blok 13 × 15 m, w środku ukryty staw pod przesuwnym szkłem,
na dachu parteru tarasy za kamiennym murkiem, piętro tylko nad skrzydłem wschodnim."""
from silnik import House, rect, poly

H = House(
    "p10", "Monolit",
    "Zamknięty kamienny blok 13 × 15 m z wąskimi szczelinami okien. W środku staw-lustro pod przesuwnym szklanym dachem, "
    "którego z zewnątrz nie widać; dach parteru to tarasy za kamiennym murkiem, a piętro to rząd czterech modułów nad skrzydłem wschodnim.",
    style=dict(fasada="kamien", dach="zwir", akcent="stal"),
    concept=[
        "Blok ma 13 × 15 m i 165 m² powierzchni użytkowej, o 84 m² mniej niż w pierwszej wersji. Z zewnątrz są tylko "
        "szczeliny i wysokie pasma okien, więc stawu w środku nie widać ani z drogi, ani z ogrodu sąsiada.",
        "Ogród 5,6 × 5,8 m ze stawem-lustrem jest ze wszystkich stron otoczony pokojami: galerią od północy, biblioteką "
        "i herbaciarnią od zachodu, pracownią i jadalnią od wschodu, wysokim salonem od południa. Żaden z nich nie ma "
        "naprzeciw szkła na zewnątrz – jedyne duże przeszklenie poza ogrodem wychodzi z salonu na patio w narożniku, "
        "schowane za murem 2,6 m i w części zadaszone.",
        "Północna ściana to ciepła skorupa pomieszczeń pomocniczych: techniczne, pralnia, wiatrołap i WC. Wchodzi się przez "
        "wiatrołap bez widoku na ogród; staw odsłania się dopiero w galerii, z której idzie się amfiladą dookoła stawu.",
        "Salon ma 6,3 m wysokości i szkło tylko do stawu i do patio; otwiera się bez ściany na niższą kuchnię, "
        "której dach jest tarasem sypialni od południowego wschodu.",
        "Schody kręcone stoją w pracowni i prowadzą do biura przeszklonego na pola od wschodu i na taras od zachodu. "
        "Dalej idzie się przelotowo: biuro, garderoba, sypialnia – a z garderoby do łazienki.",
        "Dach parteru wokół szklanego dachu stawu to taras północny i zachodni za kamiennym murkiem wysokości 1 m; "
        "najwyższy dach nad modułami piętra i salonem jest żwirowy, bez tarasu.",
    ],
    notes=dict(
        lato="Połowa szklanego dachu zsuwa się nad drugą i staw staje się otwartym dziedzińcem; z tarasów za murkiem "
             "patrzy się na niego z góry, a salon otwiera się na patio za murem.",
        zima="Dach jest zamknięty, staw z ogrodem to bufor cieplny między pokojami, od północy chroni skorupa "
             "pomieszczeń pomocniczych, a pełne kamienne ściany z wąskimi szczelinami ograniczają straty ciepła.",
        technologia="Ściany z bloczków keramzytowych na cienką spoinę z okładziną z płyt piaskowca na ruszcie, murki tarasów "
                    "z tych samych płyt, stropy i dachy z prefabrykowanych płyt kanałowych, dach szklany systemowy na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.5)
H.level(1, z=3.5, h=3.1)

# ogród – staw-lustro, jednokondygnacyjny, dach szklany tuż nad dachem parteru
H.ogrod("og", "Ogród ze stawem", rect(3.4, 5.0, 9.0, 10.8), levels=1, roof_type="slide", style="woda", seed=4)

# północna skorupa – pomieszczenia pomocnicze
H.room("tech", "Techniczne", "techniczne", rect(0, 0, 2.4, 2.4), ext="solid")
H.room("pral", "Pralnia", "pralnia", rect(2.4, 0, 4.8, 2.4), ext="band_high")
H.room("wia", "Wiatrołap", "wiatrolap", rect(4.8, 0, 7.4, 2.4), ext="solid")
H.room("wc", "WC", "wc", rect(7.4, 0, 9.0, 2.4), ext="band_high")

# galeria wzdłuż stawu – rozdzielnia domu
H.room("gal", "Galeria", "galeria", rect(3.4, 2.4, 9.0, 5.0))

# zachód – biblioteka i herbaciarnia
H.room("bib", "Biblioteka", "biblioteka", rect(0, 2.4, 3.4, 6.6), ext="slits")
H.room("her", "Herbaciarnia", "herbaciarnia", rect(0, 6.6, 3.4, 12.0), ext={"pat": "band_high", "W": "slits"})

# wschód – pracownia ze schodami (z wnęką przy stawie), łazienka, jadalnia
H.room("pra", "Pracownia", "pracownia", poly((9.0, 0), (12.8, 0), (12.8, 5.0), (10.6, 5.0), (10.6, 7.2), (9.0, 7.2)),
       ext="slits", garden="glass", floor="beton")
H.room("laz", "Łazienka", "lazienka", rect(10.6, 5.0, 12.8, 7.2), ext="band_high", label_at=(11.95, 5.95))
H.room("jad", "Jadalnia", "jadalnia", rect(9.0, 7.2, 12.8, 10.8), ext="slits")
H.stair("spiral", level=0, center=(11.5, 1.5), r=1.0, start=180, sweep=300, n=16)

# południe – wysoki salon, niższa kuchnia, patio za murem w narożniku
H.room("sal", "Salon", "salon", rect(3.4, 10.8, 9.0, 15.0), levels=2,
       ext={"pat": "glass", "taS": "glass", "S": "slits", "W": "slits", "N": "glass", "E": "slits"})
H.room("kuch", "Kuchnia", "kuchnia", rect(9.0, 10.8, 12.8, 15.0), ext={"E": "band_high", "S": "slits"}, kitchen_at="E")
H.room("pat", "Patio", "patio", rect(0, 12.0, 3.4, 15.0), roof=rect(1.9, 12.0, 3.4, 15.0), enclose="gwall",
       floor="kamien", label_at=(2.65, 14.3))

# piętro – moduły nad skrzydłem wschodnim i tarasy na dachu parteru
H.room("biu", "Biuro", "biuro", rect(9.0, 0, 12.8, 4.4), level=1,
       ext={"taN": "glass", "E": "glass", "N": "slits", "W": "solid"})
H.room("laz2", "Łazienka", "lazienka", rect(9.0, 4.4, 11.2, 6.6), level=1, ext="band_high")
H.room("gard", "Garderoba", "garderoba", rect(11.2, 4.4, 12.8, 6.6), level=1, ext="band_high")
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(9.0, 6.6, 12.8, 10.8), level=1,
       ext={"taS": "glass", "E": "band_high", "W": "band_high"})
H.room("taN", "Taras północny", "taras", rect(3.4, 2.4, 9.0, 5.0), level=1, enclose="low", floor="plyty")
H.room("taW", "Taras zachodni", "taras", rect(0, 2.4, 3.4, 12.0), level=1, enclose="low", floor="plyty")
H.room("taS", "Taras sypialni", "taras", rect(9.0, 10.8, 12.8, 15.0), level=1, enclose="low", floor="plyty")

# połączenia – parter (amfilada dookoła stawu)
H.connect("wia", "gal", "wide")
H.connect("wia", "pral", "door")
H.connect("pral", "tech", "door")
H.connect("gal", "wc", "door")
H.connect("gal", "bib", "double")
H.connect("gal", "pra", "double")
H.connect("bib", "her", "door")
H.connect("her", "sal", "door")
H.connect("sal", "kuch", "open")
H.connect("kuch", "jad", "wide")
H.connect("jad", "pra", "door")
H.connect("pra", "laz", "door")
H.connect("sal", "pat", "slide", at=0.15)
# piętro (moduły przelotowe)
H.connect("biu", "gard", "door")
H.connect("gard", "syp", "door")
H.connect("gard", "laz2", "door")
H.connect("biu", "taN", "slide")
H.connect("syp", "taS", "slide")

H.entrance("wia", "N")
H.path(rect(5.4, -6.0, 6.8, -0.2))
H.tree(-3.8, 6.0, "sosna")
H.tree(16.8, 13.0, "klon")
H.tree(16.3, -2.5, "brzoza")
H.tree(4.0, 19.5, "lipa")
H.cut("A–A", (6.2, -2.5), (6.2, 17.5))
H.cut("B–B", (15.5, 8.6), (-2.5, 8.6))
H.cut("C–C", (11.6, 17.5), (11.6, -2.5))
