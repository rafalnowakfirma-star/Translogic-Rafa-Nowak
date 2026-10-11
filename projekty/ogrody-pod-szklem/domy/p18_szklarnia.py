"""P18 · Szklarnia (wersja 2, ogród zimowy jako jadalnia) – długi, wąski drewniany pas 22 × 9,6 m jak dawna szklarnia:
w środku ogród zimowy z jadalnią pod przesuwnym szklanym dachem, po bokach wąskie pokoje przelotowe, od zachodu
kuchnia z harmonijką i piętro z modułami, od wschodu wysoki salon i patio za murem."""
from silnik import House, rect

H = House(
    "p18", "Szklarnia",
    "Długi, wąski dom z modrzewia, 22 × 9,6 m, jak dawna szklarnia ogrodnicza. W środku pasa leży ogród zimowy ze stołem jadalnym na osiem osób pod przesuwnym szklanym dachem; od zachodu otwiera się na niego kuchnia szklaną harmonijką, od wschodu wysoki salon.",
    style=dict(fasada="drewno", dach="sedum", akcent="modrzew"),
    concept=[
        "Ogród zimowy 6,6 × 4,8 m (30 m²) jest jadalnią domu: wzdłuż szklanej harmonijki od kuchni stoi stół na osiem osób, dalej oliwka i cytrusy w donicach, posadzka z płyt leży w poziomie podłogi. Złożona harmonijka łączy kuchnię, stół i ogród w jedną przestrzeń o długości 10 m; rozłożona zamyka ogród zimowy na mroźną noc albo wtedy, gdy dach jest otwarty w deszcz.",
        "Ogród z każdej strony domykają pokoje: od zachodu kuchnia, od wschodu salon, od północy pracownia, od południa biblioteka i herbaciarnia. Kuchnia nie ma okien na zewnątrz – światło daje jej ogród pod szkłem – a w pozostałych pokojach od zewnątrz są tylko wstęgi okien pod sufitem i jedno okno herbaciarni, więc ogrodu nie widać ani z drogi, ani od sąsiadów.",
        "Wchodzi się od północy przez wiatrołap w zachodniej głowie domu, obok WC; dalej jest hol ze schodami kręconymi i kuchnia. Dom obchodzi się bez korytarzy dwiema amfiladami wzdłuż ogrodu: kuchnia – spiżarnia – pracownia (6,6 m długa, z warsztatem pod wstęgą okien) – salon po stronie północnej i kuchnia – biblioteka – herbaciarnia – salon po południowej; pralnia jest za biblioteką.",
        "Salon na wschodnim końcu ma 6,6 m wysokości. Do ogrodu jest cały ze szkła, po bokach ma tylko wstęgi okien pod sufitem, a na wschód otwiera się szklaną ścianą na patio za murem 2,6 m, zadaszone na szerokość 2,2 m przy salonie – to otwarty koniec szklarni.",
        "Środkowa część pasa jest parterowa: na dachach pokoi bocznych, po obu stronach szklanego dachu ogrodu, leżą dwa tarasy – północny (15 m²) przy sypialni i południowy (31 m²), który biegnie przez całą długość 13 m aż do zachodniej głowy. Z tarasów patrzy się z góry na stół w ogrodzie przez szkło, a latem przez otwartą połowę dachu.",
        "Na piętrze zachodniej głowy moduły stoją wokół tarasów i przechodzi się przez nie w amfiladzie: czytelnia nad holem, biuro przeszklone na południe na taras i na wschód ponad szklany dach ogrodu, sypialnia ze szklaną ścianą od północy, łóżkiem zwróconym do szkła i wyjściem na taras północny, a za nią łazienka. Najwyższe dachy – nad modułami i nad salonem – są zielone.",
    ],
    notes=dict(
        lato="Zachodnia połowa szklanego dachu zsuwa się nad wschodnią, harmonijka od kuchni jest złożona i je się pod gołym niebem między kuchnią a salonem; z obu tarasów zagląda się do ogrodu z góry, a salon otwiera się na patio za murem.",
        zima="Dach jest zamknięty, harmonijkę rozkłada się na noc i ogród zimowy z roślinami w donicach staje się chłodniejszym buforem między kuchnią a salonem; w dzień otwiera się ją znów i stół stoi w słońcu pod szkłem.",
        technologia="Szkielet drewniany z prefabrykowanych ścian o jednakowej szerokości pasa 9,6 m, stropy i dachy z paneli CLT, elewacja z pionowej deski modrzewiowej; tarasy na stropach CLT z warstwą spadkową i deskami, dach szklany systemowy na stalowej ramie z przesuwną połową na szynach.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

# ogród zimowy z jadalnią: środek pasa, 6,6 × 4,8 m, dach przesuwny
H.ogrod("og", "Ogród zimowy z jadalnią", rect(6.6, 2.4, 13.2, 7.2), roof_type="slide", style="jadalnia", seed=18)

# ---- zachodnia głowa, parter: wiatrołap, WC, spiżarnia, hol ze schodami, kuchnia bez okien na zewnątrz, pralnia
H.room("wia", "Wiatrołap", "wiatrolap", rect(0, 0, 2.6, 2.4), ext={"N": "slits", "W": "solid"})
H.room("wc", "WC", "wc", rect(2.6, 0, 4.0, 2.4))
H.room("spiz", "Spiżarnia", "spizarnia", rect(4.0, 0, 6.6, 2.4), ext={"N": "band_high"})
H.room("kuch", "Kuchnia", "kuchnia", rect(2.6, 2.4, 6.6, 7.2), garden="fold", kitchen_at="S")
H.room("hol", "Hol ze schodami", "hol", rect(0, 2.4, 2.6, 7.2), ext={"W": "slits"})
H.room("pral", "Pralnia", "pralnia", rect(0, 7.2, 2.2, 9.6), ext={"W": "band_high", "S": "band_high"})
H.stair("spiral", level=0, center=(1.3, 6.05), r=1.0, start=180, sweep=300, n=16)

# ---- pokoje boczne wzdłuż ogrodu (przelotowe)
H.room("prac", "Pracownia", "pracownia", rect(6.6, 0, 13.2, 2.4), ext={"N": "band_high"}, garden="glass")
H.room("bib", "Biblioteka", "biblioteka", rect(2.2, 7.2, 8.4, 9.6), ext={"S": "band_high"}, garden="glass")
H.room("her", "Herbaciarnia", "herbaciarnia", rect(8.4, 7.2, 13.2, 9.6), ext={"S": "windows"}, garden="glass")

# ---- wschodni koniec: wysoki salon i patio za murem
H.room("sal", "Salon", "salon", rect(13.2, 0, 17.4, 9.6), levels=2, garden="glass_slide",
       ext={"pat": "glass_slide", "N": "band_high", "S": "band_high", "W": "band", "E": "band"})
H.room("pat", "Patio za murem", "patio", rect(17.4, 0, 22.0, 9.6), roof=rect(17.4, 0, 19.6, 9.6), enclose="gwall")

# ---- piętro zachodniej głowy: moduły w amfiladzie wokół tarasów
H.room("laz", "Łazienka", "lazienka", rect(0, 0, 2.6, 2.4), level=1)
H.room("czyt", "Czytelnia", "biblioteka", rect(0, 2.4, 2.6, 7.2), level=1, ext={"W": "slits", "taS": "glass"})
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(2.6, 0, 6.6, 4.0), level=1,
       ext={"N": "glass", "taN": "glass_slide", "E": "glass"})
H.room("biu", "Biuro", "biuro", rect(2.6, 4.0, 6.6, 7.2), level=1, ext={"E": "glass", "taS": "glass_slide"})
H.room("taN", "Taras północny", "taras", rect(6.6, 0, 13.2, 2.4), level=1)
H.room("taS", "Taras południowy", "taras", rect(0, 7.2, 13.2, 9.6), level=1)

# ---- połączenia parteru (drzwi przy końcach ścian, żeby zostawić miejsce na meble)
H.connect("wia", "hol", "door")
H.connect("wia", "wc", "door", at=0.8)
H.connect("hol", "kuch", "door", at=0.88)
H.connect("kuch", "bib", "door", at=0.12)
H.connect("pral", "bib", "door", at=0.8)
H.connect("kuch", "spiz", "door", at=0.12)
H.connect("spiz", "prac", "door", at=0.8)
H.connect("prac", "sal", "door", at=0.2)
H.connect("bib", "her", "door")
H.connect("her", "sal", "door")
H.connect("sal", "og", "slide", at=0.15, width=1.8)   # drzwi do ogrodu przy północnym końcu szkła salonu
# ---- połączenia piętra (amfilada) i wyjścia na tarasy
H.connect("czyt", "biu", "door", at=0.12)
H.connect("biu", "syp", "door", at=0.88)
H.connect("syp", "laz", "door", at=0.2)
H.connect("syp", "taN", "slide", at=0.15)
H.connect("biu", "taS", "slide", at=0.15, width=0.9)

H.entrance("wia", "N")

# ---- teren
H.path(rect(0.6, -6.0, 2.0, -0.2))
H.tree(-4.0, 3.5, "brzoza")
H.tree(9.5, 14.5, "lipa")
H.tree(25.0, 11.5, "klon")
H.tree(15.5, -4.0, "sosna")

H.cut("A–A", (-2.5, 4.8), (24.5, 4.8))
H.cut("B–B", (9.9, -2.5), (9.9, 12.5))
H.cut("C–C", (1.3, -2.5), (1.3, 12.5))
