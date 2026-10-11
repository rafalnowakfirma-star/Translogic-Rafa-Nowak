"""P13 · Kubik (wersja 2) – zwarta kostka 13,6 × 14,3 m z ukrytym atrium 5,6 × 5,6 m; zachodni pas parterowy z tarasem na dachu, moduły piętra w kształcie L."""
from silnik import House, rect, poly

# siatka: pasma W | atrium | E = 3,6 | 5,6 | 4,0 m (x), N | atrium | S = 3,5 | 5,6 | 4,8 m (y)
XW, XE, XX = 3.6, 9.2, 13.2
YN, YS, YY = 3.5, 9.1, 13.9
YB = 10.4   # koniec biblioteki / początek patio za murem (pas zachodni)
YT = 6.7    # koniec łazienki i garderoby / początek tarasu wschodniego (pas wschodni, piętro)
YP = 6.3    # koniec pralni / początek herbaciarni (pas wschodni, parter)
YK = 9.5    # koniec herbaciarni – salon ma tu uskok 0,4 m, dzięki czemu taras wschodni ma 2,8 m głębokości

H = House(
    "p13", "Kubik",
    "Zwarta kostka 13,6 × 14,3 m (168 m²) z atrium 5,6 × 5,6 m w środku, którego z zewnątrz nie widać. "
    "Zachodni pas domu jest parterowy – na jego dachu leży taras przy szklanym dachu atrium, a moduły piętra ustawione w L stoją wokół niego i drugiego, mniejszego tarasu od wschodu.",
    style=dict(fasada="blacha", dach="sedum", akcent="modrzew"),
    concept=[
        "Atrium 5,6 × 5,6 m stoi w samym środku kostki i ze wszystkich stron otaczają je pokoje parteru: hol, biblioteka, pralnia, herbaciarnia i salon. Ma szklany dach z obrotowych lameli na wysokości dachu parteru.",
        "Z zewnątrz ogrodu nie widać: dom ma od ulicy i od sąsiadów tylko okna i szczeliny w ciemnej blasze, a wiatrołap nie ma szkła do atrium – ogród otwiera się dopiero z holu, biblioteki, herbaciarni i salonu.",
        "Salon z kuchnią (9,6 × 4,8 m, 6,3 m wysokości) zajmuje południowy pas. Szkło ma do atrium i do patio za murem wysokości 2,6 m, wyciętego z południowo-zachodniego narożnika; od południa ma zwykłe okna, od wschodu wysoki pas nad blatem kuchni.",
        "Parter obchodzi się bez korytarzy: z wiatrołapu do holu ze schodami i pokoju gościnnego albo przez bibliotekę do salonu, dalej przez herbaciarnię do pralni ze spiżarnią i wyjściem gospodarczym.",
        "Zachodni pas jest parterowy – na dachu biblioteki leży taras 24 m² przy szklanym dachu atrium, z widokiem w dół na patio. Drugi taras, 10 m², leży na dachu herbaciarni przy garderobie i łazience, od południa osłonięty wysoką ścianą salonu.",
        "Moduły piętra stoją w L wokół tarasów i przechodzi się przez nie po kolei: biuro przeszklone na zachód i na taras, galeria nad atrium ze schodami, sypialnia ze szklaną ścianą od wschodu, a z niej łazienka i garderoba przelotowa z wyjściem na taras wschodni. Dach nad modułami jest zielony.",
    ],
    notes=dict(
        lato="Lamele nad atrium stają pionowo, salon otwiera się na patio za murem, a życie przenosi się na tarasy na dachu parteru – zachodni przy biurze i wschodni przy garderobie i łazience sypialni.",
        zima="Lamele są zamknięte i atrium działa jak nasłoneczniony bufor między holem a salonem; pełne ściany z blachy i mur patio osłaniają dom od wiatru.",
        technologia="Szkielet stalowy z prefabrykowanych modułów przestrzennych (ściany z płyt warstwowych) ustawionych wokół atrium, stropy z płyt kanałowych, tarasy na stropie parteru z warstwą spadkową. Elewacja z ciemnej blachy na rąbek stojący, dach szklany systemowy na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

H.ogrod("og", "Atrium", rect(XW, YN, XE, YS), levels=1, roof_type="louvre", style="japonski", seed=13)

# ---------------------------------------------------------------- parter
H.room("wc", "WC", "wc", rect(2.4, 0, XW, 2.0), ext={"N": "solid", "W": "band_high"})
H.room("wia", "Wiatrołap", "wiatrolap", poly((0, 1.3), (2.4, 1.3), (2.4, 2.0), (XW, 2.0), (XW, YN), (0, YN)),
       ext={"W": "slits", "N": "solid"})
H.room("hol", "Hol", "hol", rect(XW, 0, XE, YN), ext={"N": "slits"})
H.stair("straight", level=0, rect=(3.7, 0.25, 8.7, 1.35), up="W")
H.room("gos", "Pokój gościnny", "gosc", rect(XE, 0, XX, YN), ext={"N": "solid", "E": "windows"})
H.room("pral", "Pralnia i spiżarnia", "pralnia", rect(XE, YN, XX, YP), ext={"E": "windows_sq"}, garden="band_high")
H.room("her", "Herbaciarnia", "herbaciarnia", rect(XE, YP, XX, YK), ext={"E": "windows"})
H.room("sal", "Salon z kuchnią", "salon_kuchnia",
       poly((XW, YS), (XE, YS), (XE, YK), (XX, YK), (XX, YY), (XW, YY)), levels=2, kitchen_at="E",
       ext={"pat": "glass_slide", "taW": "band", "taE": "band", "S": "windows", "E": "band_high", "N": "band", "W": "band"})
H.room("pat", "Patio za murem", "patio", rect(0, YB, XW, YY), roof=rect(1.8, YB, XW, YY), enclose="gwall")
H.room("bib", "Biblioteka", "biblioteka", rect(0, YN, XW, YB), ext={"W": "band_high", "pat": "glass_slide"})

H.connect("wia", "hol", "door")
H.connect("wia", "wc", "door")
H.connect("wia", "bib", "door", at=0.15)
H.connect("hol", "gos", "door", at=0.7)
H.connect("bib", "sal", "door")
H.connect("sal", "her", "door", at=0.8)
H.connect("her", "pral", "door")
H.entrance("wia", "N", at=0.7)
H.exit("pral", "E", kind="door", width=0.9)

# ---------------------------------------------------------------- piętro: moduły w L wokół tarasów
H.room("biu", "Biuro", "biuro", rect(0, 0, XW, YN), level=1, ext={"W": "glass", "N": "band_high", "taW": "glass"})
H.room("gal", "Galeria nad atrium", "galeria", rect(XW, 0, XE, YN), level=1, ext={"N": "slits", "S": "glass"})
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(XE, 0, XX, YN), level=1, ext={"N": "band_high", "E": "glass"})
H.room("gar", "Garderoba", "garderoba", rect(XE, YN, 11.2, YT), level=1, ext={"W": "band_high", "taE": "glass"}, label_at=(9.95, 5.45))
H.room("laz", "Łazienka", "lazienka", rect(11.2, YN, XX, YT), level=1, ext={"E": "band_high", "taE": "band_high"}, label_at=(12.25, 4.35))
H.room("taW", "Taras zachodni", "taras", rect(0, YN, XW, YB), level=1)
H.room("taE", "Taras wschodni", "taras", rect(XE, YT, XX, YK), level=1)

H.connect("biu", "gal", "door", at=0.75)
H.connect("gal", "syp", "door", at=0.85)
H.connect("syp", "gar", "door", at=0.85)
H.connect("syp", "laz", "door")
H.connect("biu", "taW", "slide")
H.connect("gar", "taE", "slide", at=0.9, width=1.1)

# ---------------------------------------------------------------- teren
H.path(rect(0, 0, 2.4, 1.3))        # posadzka podcienia wejściowego (wnęka pod biurem)
H.path(rect(0.6, -6.0, 1.8, 0.0))
H.path(rect(XX, 4.2, XX + 1.2, 5.6))  # dojście do wyjścia gospodarczego z pralni
H.tree(-4.5, 15.5, "klon")
H.tree(16.8, 2.0, "brzoza")
H.tree(16.2, 16.0, "sosna")
H.cut("A–A", (6.4, -2.0), (6.4, 16.5))
H.cut("B–B", (-2.0, 8.0), (16.0, 8.0))
