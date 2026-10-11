"""P14 · Zygzak (wersja 2) – krótszy łańcuch przesuniętych modułów z cortenu wokół jednego, ukrytego ogrodu zimowego; letni dziedziniec został jako patio za murem."""
from silnik import House, rect, poly

H = House(
    "p14", "Zygzak",
    "Sześć cortenowych modułów na parterze i cztery na piętrze, każdy przesunięty o metr względem sąsiada, obiega ukryty ogród zimowy pod harmonijkowym szklanym dachem. Letni dziedziniec z pierwszej wersji został jako patio za murem, a na dachach parterowych modułów leżą dwa tarasy: przy sypialni i przy biurze.",
    style=dict(fasada="corten", dach="sedum", akcent="stal"),
    concept=[
        "Dom jest nadal zygzakiem, ale krótszym: sześć modułów parteru i cztery piętra, każdy przesunięty o metr względem sąsiada, więc obie elewacje są ząbkowane, a w załamaniach powstają wnęki na drzwi i ławkę. Ogród zimowy 40 m² leży w środku i każdą krawędzią dotyka pokoju; od zewnątrz dom ma pełne ściany z cortenu, szczeliny i małe okna, więc ogrodu nie widać ani z drogi, ani od sąsiadów.",
        "Wchodzi się od północy przez wiatrołap, który nie ma szkła do ogrodu. Ogród otwiera się dopiero za drugimi drzwiami, w holu z biblioteką i schodami kręconymi, a dalej po parterze chodzi się bez korytarza: hol, herbaciarnia, pracownia, salon, patio, pralnia ze spiżarnią i z powrotem hol.",
        "Letni dziedziniec z pierwszej wersji został jako patio za murem wysokości 2,6 m po wschodniej stronie ogrodu. Od ogrodu dzieli je szklana harmonijka: zimą zamknięta, latem złożona, więc oba ogrody znów są jedną przestrzenią – tyle że schowaną za murem.",
        "Salon z kuchnią ma 6,6 m wysokości i zajmuje całą południową stronę, wysunięty o metr przed zachodnie moduły. Od ogrodu i od patio jest cały ze szkła, a na zewnątrz ma tylko trzy duże okna i wąski pas pod dachem, dlatego przez salon nie widać ogrodu na wylot.",
        "Dachy parterowych modułów to dwa tarasy przy szklanym dachu ogrodu: zachodni na dachu pracowni, z wyjściem z sypialni, i wschodni na dachu pralni, z wyjściem z biura. Najwyższy dach nad modułami piętra jest zielony, bez tarasu.",
        "Na piętrze cztery moduły łączą się drzwiami w ciąg: sypialnia ze szklaną ścianą od zachodu, łazienka, galeria ze schodami i biuro wysunięte o metr przed front domu, przeszklone na pola od północy, na taras od wschodu i na szklany dach ogrodu od południa.",
    ],
    notes=dict(
        lato="Harmonijkowy dach ogrodu i szklana ścianka do patio są złożone: ogród zimowy i patio za murem stają się jednym dziedzińcem pod niebem, salon otwiera się na nie przesuwnymi drzwiami, a z tarasów na dachu patrzy się na brzozy z góry.",
        zima="Dach i harmonijka są zamknięte: ogród zimowy jest ogrzewanym buforem w środku domu, mur patio osłania salon od wschodniego wiatru, a pełne ściany modułów od północy i zachodu trzymają ciepło.",
        technologia="Prefabrykowane moduły stalowe o szerokości 3–4,4 m (rama z profili HEB, strop z blachy trapezowej z nadbetonem, ściany warstwowe z wełną), ustawiane z przesunięciem o metr; biuro na piętrze to moduł wysunięty wspornikowo o metr przed hol. Salon to trzy moduły w rzędzie bez ścian i bez stropu pośredniego. Elewacja i mur patio z blachy cortenowskiej na ruszcie, dach szklany harmonijkowy na stalowej ramie, tarasy z deski na stropach modułów parteru.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

# ogród zimowy w środku, jednokondygnacyjny: każdą krawędzią dotyka pokoju, od wschodu harmonijka do patio za murem
H.ogrod("og", "Ogród zimowy", poly((4.4, 3.0), (9.4, 3.0), (9.4, 4.0), (10.6, 4.0), (10.6, 10.0), (4.4, 10.0)),
        levels=1, roof_type="fold", style="las", edge="fold", seed=14)

# --- parter, moduły północne (front): wiatrołap, hol z biblioteką wysunięty o 1 m, WC i pralnia ze spiżarnią
H.room("wia", "Wiatrołap", "wiatrolap", rect(0, 0, 3.0, 3.0), ext={"N": "slits", "W": "solid"})
H.room("hol", "Hol z biblioteką", "biblioteka", rect(3.0, -1.0, 9.4, 3.0), ext={"N": "band_high", "W": "solid", "E": "solid"})
H.room("wc", "WC", "wc", rect(9.4, 0, 11.0, 1.8))
H.room("pral", "Pralnia i spiżarnia", "pralnia", poly((11.0, 0), (12.4, 0), (12.4, 4.0), (9.4, 4.0), (9.4, 1.8), (11.0, 1.8)),
       ext={"N": "band_high", "E": "windows_sq", "pat": "solid"})
H.stair("spiral", level=0, center=(5.0, 1.3), r=1.05, start=200, sweep=320, n=16)
# --- moduły zachodnie (przelotowe): herbaciarnia i pracownia; na południu wysoki salon wysunięty o 1 m na zachód
H.room("herb", "Herbaciarnia", "herbaciarnia", rect(0, 3.0, 4.4, 7.0), ext={"W": "band"}, garden="glass", label_at=(1.6, 6.1))
H.room("prac", "Pracownia", "pracownia", rect(0, 7.0, 4.4, 10.0), ext={"W": "windows"})
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(-1.0, 10.0, 13.4, 14.0), levels=2, kitchen_at="E",
       ext={"pat": "glass", "S": "band_high", "W": "windows", "E": "windows", "N": "band", "taZ": "windows"})
H.window("sal", "S", at=0.18, width=2.4, sill=0.45, head=2.6)
H.window("sal", "S", at=0.50, width=2.4, sill=0.45, head=2.6)
H.window("sal", "S", at=0.82, width=2.4, sill=0.45, head=2.6)
# --- letnie patio za murem (dawny dziedziniec): między ogrodem, pralnią i salonem, zadaszone przy salonie
H.room("pat", "Patio za murem", "patio", rect(10.6, 4.0, 14.4, 10.0), roof=rect(10.6, 8.2, 14.4, 10.0), enclose="gwall")

# --- piętro: łańcuch czterech modułów wokół dwóch tarasów (biuro wysunięte wspornikowo o 1 m przed hol)
H.room("laz", "Łazienka", "lazienka", rect(0, 0, 3.0, 3.0), level=1, ext={"N": "band_high", "W": "band_high"}, label_at=(1.0, 1.8))
H.room("gal", "Galeria", "galeria", rect(3.0, -1.0, 6.2, 3.0), level=1, ext={"N": "slits", "W": "solid", "S": "glass"})
H.room("biu", "Biuro", "biuro", rect(6.2, -2.0, 9.4, 2.0), level=1,
       ext={"N": "glass", "S": "glass", "E": "solid", "taE": "glass"})
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(0, 3.0, 4.4, 7.0), level=1,
       ext={"W": "glass", "E": "band_high", "taZ": "glass"})
H.room("taE", "Taras wschodni", "taras", rect(9.4, 0, 12.4, 4.0), level=1)
H.room("taZ", "Taras zachodni", "taras", rect(0, 7.0, 4.4, 10.0), level=1)

# --- połączenia: amfilada parteru (pętla wokół ogrodu)
H.connect("wia", "hol", "door", at=0.8)
H.connect("hol", "wc", "door")
H.connect("hol", "pral", "door")
H.connect("hol", "herb", "door")
H.connect("herb", "prac", "door")
H.connect("prac", "sal", "door")
H.connect("sal", "pat", "slide", width=3.0)
H.connect("pral", "pat", "door")
# --- piętro: sypialnia – galeria – biuro, łazienka przy sypialni, wyjścia na tarasy
H.connect("syp", "laz", "door")
H.connect("gal", "syp", "door")
H.connect("gal", "biu", "door", at=0.15)
H.connect("biu", "taE", "slide")
H.connect("syp", "taZ", "slide")

H.entrance("wia", "N")
H.exit("pral", "E", kind="door", width=0.9)
H.path(rect(0.8, -6.0, 2.2, -0.2))
H.tree(-3.5, 5.0, "brzoza")
H.tree(18.0, 2.0, "sosna")
H.tree(18.0, 15.5, "klon")
H.tree(-3.0, 17.0, "lipa")
H.cut("A–A", (5.0, -3.0), (5.0, 16.5))
H.cut("B–B", (-2.5, 5.5), (17.5, 5.5))
