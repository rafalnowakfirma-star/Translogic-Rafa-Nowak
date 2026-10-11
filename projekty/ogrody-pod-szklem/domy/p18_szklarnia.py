"""P18 · Szklarnia (wersja 2, ogród zimowy jako jadalnia) – długi, wąski drewniany pas 22 × 9,6 m jak dawna szklarnia:
w środku ogród zimowy z jadalnią pod przesuwnym szklanym dachem, po bokach wąskie pokoje przelotowe, od zachodu
kuchnia z harmonijką i piętro z modułami, od wschodu wysoki salon i patio za murem."""
from silnik import House, rect, poly

H = House(
    "p18", "Szklarnia",
    "Długi, wąski dom z modrzewia, 22 × 9,6 m, jak dawna szklarnia ogrodnicza. W środku pasa leży ogród zimowy ze stołem jadalnym pod przesuwnym szklanym dachem; otwiera się na niego kuchnia szklaną harmonijką, a z drugiej strony wysoki salon.",
    style=dict(fasada="drewno", dach="sedum", akcent="modrzew"),
    concept=[
        "Ogród zimowy 6,0 × 4,8 m jest jadalnią domu: przy szklanej harmonijce od kuchni stoi stół na osiem osób, dookoła rośliny w donicach, posadzka z płyt w poziomie podłogi. Złożona harmonijka łączy kuchnię, stół i ogród w jedną przestrzeń o długości 10 m; rozłożona zamyka ogród zimowy, gdy noc jest mroźna albo dach jest otwarty w deszcz.",
        "Ogród z każdej strony domykają pokoje: od zachodu kuchnia, od wschodu salon, od północy spiżarnia-kredens i pracownia, od południa biblioteka i herbaciarnia. Od zewnątrz w tych pokojach są tylko okna i szczeliny, więc ogrodu nie widać ani z drogi, ani od sąsiadów.",
        "Wchodzi się od północy przez wiatrołap w zachodniej głowie domu, obok WC; dalej jest hol ze schodami kręconymi i kuchnia. Dom obchodzi się bez korytarzy dwiema amfiladami wzdłuż ogrodu: kuchnia – spiżarnia-kredens – pracownia – salon po północnej stronie i kuchnia – biblioteka – herbaciarnia – salon po południowej.",
        "Salon na wschodnim końcu ma 6,6 m wysokości. Do ogrodu jest cały ze szkła, na północ i południe ma tylko okna, a na wschód otwiera się szklaną ścianą na patio za murem 2,6 m, częściowo zadaszone – to otwarty koniec szklarni.",
        "Środkowa część pasa jest parterowa: na dachach pokoi bocznych, po obu stronach szklanego dachu ogrodu, leżą dwa tarasy – północny przy sypialni i południowy, który biegnie przez całą długość 12,6 m aż do zachodniej głowy. Z tarasów patrzy się z góry na stół w ogrodzie przez szkło, a latem przez otwartą połowę dachu.",
        "Na piętrze zachodniej głowy moduły stoją wokół tarasów i przechodzi się przez nie w pętli: czytelnia nad holem, łazienka, sypialnia ze szklaną ścianą od północy i wyjściem na taras północny, biuro przeszklone na wschód ponad szklany dach ogrodu i na południe na taras. Najwyższe dachy – nad modułami i nad salonem – są zielone.",
    ],
    notes=dict(
        lato="Zachodnia połowa szklanego dachu zsuwa się nad wschodnią, harmonijka od kuchni jest złożona i je się pod gołym niebem między kuchnią a salonem; z tarasów po obu stronach zagląda się do ogrodu z góry, a salon otwiera się na patio za murem.",
        zima="Dach jest zamknięty, harmonijkę rozkłada się na noc i ogród zimowy z roślinami w donicach staje się chłodniejszym buforem między kuchnią a salonem; w dzień otwiera się ją znów i stół stoi w słońcu pod szkłem.",
        technologia="Szkielet drewniany z prefabrykowanych ścian o jednakowej szerokości pasa 9,6 m, stropy i dachy z paneli CLT, elewacja z pionowej deski modrzewiowej; tarasy na stropach CLT z warstwą spadkową i deskami, dach szklany systemowy na stalowej ramie z przesuwną połową na szynach.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

# ogród zimowy z jadalnią: środek pasa, 6,0 × 4,8 m, dach przesuwny
H.ogrod("og", "Ogród zimowy z jadalnią", rect(6.6, 2.4, 12.6, 7.2), roof_type="slide", style="jadalnia", seed=5)

# ---- zachodnia głowa, parter: wiatrołap, WC, hol ze schodami, kuchnia (L z oknem na północ), pralnia
H.room("wia", "Wiatrołap", "wiatrolap", rect(0, 0, 2.6, 2.4), ext={"N": "slits", "W": "solid"})
H.room("wc", "WC", "wc", rect(2.6, 0, 4.0, 2.4))
H.room("kuch", "Kuchnia", "kuchnia", poly((4.0, 0), (6.6, 0), (6.6, 7.2), (2.6, 7.2), (2.6, 2.4), (4.0, 2.4)),
       garden="fold", ext={"N": "windows"}, kitchen_at="N")
H.room("hol", "Hol ze schodami", "hol", rect(0, 2.4, 2.6, 7.2), ext={"W": "slits"})
H.room("pral", "Pralnia", "pralnia", rect(0, 7.2, 2.2, 9.6))
H.stair("spiral", level=0, center=(1.3, 5.2), r=1.0, start=180, sweep=300, n=16)

# ---- pokoje boczne wzdłuż ogrodu (przelotowe)
H.room("spiz", "Spiżarnia-kredens", "spizarnia", rect(6.6, 0, 8.6, 2.4), ext={"N": "slits"})
H.room("prac", "Pracownia", "pracownia", rect(8.6, 0, 12.6, 2.4), ext={"N": "windows"}, garden="glass_slide")
H.room("bib", "Biblioteka", "biblioteka", rect(2.2, 7.2, 8.4, 9.6), ext={"S": "windows"}, garden="glass")
H.room("her", "Herbaciarnia", "herbaciarnia", rect(8.4, 7.2, 12.6, 9.6), ext={"S": "windows"}, garden="glass_slide")

# ---- wschodni koniec: wysoki salon i patio za murem
H.room("sal", "Salon", "salon", rect(12.6, 0, 16.8, 9.6), levels=2, garden="glass_slide",
       ext={"pat": "glass_slide", "N": "windows", "S": "windows", "W": "band", "E": "band"})
H.room("pat", "Patio za murem", "patio", rect(16.8, 0, 22.0, 9.6), roof=rect(16.8, 0, 19.0, 9.6), enclose="gwall")

# ---- piętro zachodniej głowy: moduły w pętli wokół tarasów
H.room("laz", "Łazienka", "lazienka", rect(0, 0, 2.6, 2.4), level=1)
H.room("czyt", "Czytelnia", "biblioteka", rect(0, 2.4, 2.6, 7.2), level=1, ext={"W": "slits", "taS": "glass_slide"})
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(2.6, 0, 6.6, 3.6), level=1,
       ext={"N": "glass", "taN": "glass_slide", "E": "glass"})
H.room("biu", "Biuro", "biuro", rect(2.6, 3.6, 6.6, 7.2), level=1, ext={"E": "glass", "taS": "glass_slide"})
H.room("taN", "Taras północny", "taras", rect(6.6, 0, 12.6, 2.4), level=1)
H.room("taS", "Taras południowy", "taras", rect(0, 7.2, 12.6, 9.6), level=1)

# ---- połączenia parteru
H.connect("wia", "hol", "door")
H.connect("wia", "wc", "door")
H.connect("hol", "kuch", "door", at=0.15)
H.connect("hol", "pral", "door")
H.connect("pral", "bib", "door")
H.connect("kuch", "bib", "door", at=0.3)
H.connect("kuch", "spiz", "door")
H.connect("spiz", "prac", "door")
H.connect("prac", "sal", "door")
H.connect("bib", "her", "door")
H.connect("her", "sal", "door")
# ---- połączenia piętra (pętla) i wyjścia na tarasy
H.connect("czyt", "laz", "door")
H.connect("laz", "syp", "door")
H.connect("syp", "biu", "door", at=0.8)
H.connect("biu", "czyt", "door", at=0.2)
H.connect("syp", "taN", "slide")
H.connect("biu", "taS", "slide")
H.connect("czyt", "taS", "slide")

H.entrance("wia", "N")
H.exit("pral", "W", kind="door", width=0.9)

# ---- teren
H.path(rect(0.6, -6.0, 2.0, -0.2))
H.tree(-4.0, 3.5, "brzoza")
H.tree(9.5, 14.5, "lipa")
H.tree(25.0, 11.5, "klon")
H.tree(15.5, -4.0, "sosna")

H.cut("A–A", (-2.5, 4.8), (24.5, 4.8))
H.cut("B–B", (9.6, -2.5), (9.6, 12.5))
H.cut("C–C", (1.3, -2.5), (1.3, 12.5))
