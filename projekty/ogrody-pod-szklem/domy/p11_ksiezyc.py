"""P11 · Półksiężyc (wersja 2) – ceglany półksiężyc domknięty od południa prostym pasmem pokoi; półkolisty ogród pod składanym szklanym dachem schowany w środku, tarasy na dachach rogów, moduły piętra na szczycie łuku."""
import math

from silnik import House, sector, rect, union

# Jeden wspólny środek wszystkich łuków. Pierścień pokoi 4,8–8,2 m na łuku 180° (zachód → północ → wschód),
# ogród to półkole w środku, a cięciwę (od południa) zamyka proste pasmo pokoi o głębokości 4,2 m.
C = (10.0, 10.0)
R_IN, R_M, R_OUT = 4.8, 6.0, 8.2      # ogród | podział pasa sypialni i łazienki na piętrze | elewacja
D = 4.2                               # głębokość pasma wzdłuż cięciwy


def sec(a1, a2, r1=R_IN, r2=R_OUT):
    return sector(C[0], C[1], r1, r2, a1, a2)


def rc(x1, y1, x2, y2):
    """Prostokąt we współrzędnych względem środka łuków."""
    return rect(C[0] + x1, C[1] + y1, C[0] + x2, C[1] + y2)


def P(r, a):
    return (C[0] + r * math.cos(math.radians(a)), C[1] + r * math.sin(math.radians(a)))


H = House(
    "p11", "Półksiężyc",
    "Ceglany półksiężyc domknięty od południa prostym pasmem z wysokim salonem. Półkolisty ogród pod składanym "
    "szklanym dachem jest schowany w środku domu, a na dachach rogów półksiężyca leżą dwa tarasy.",
    style=dict(fasada="cegla", dach="sedum", akcent="stal"),
    concept=[
        "Pokoje parteru stoją w pierścieniu o promieniach 4,8–8,2 m na łuku 180°, a cięciwę od południa zamyka proste pasmo: wiatrołap z łazienką, wysoki salon z kuchnią i biblioteka – półkolisty ogród o średnicy 9,6 m ma dzięki temu pokoje ze wszystkich stron.",
        "Od zewnątrz dom jest ceglany, z oknami i szczelinami; szkło mają tylko ściany od ogrodu, więc ogrodu nie widać ani z drogi, ani z łąki, a wiatrołap nie ma do niego szkła – ogród otwiera się dopiero z sali muzycznej.",
        "Parter obchodzi się dookoła bez korytarza, drzwiami ustawionymi w jednej linii przy szkle ogrodu: sala muzyczna, pracownia, hol ze schodami kręconymi, herbaciarnia, spiżarnia z pralnią, biblioteka i salon; sala muzyczna, pracownia, hol i herbaciarnia mają własne drzwi do ogrodu.",
        "Salon z kuchnią ma 6,6 m wysokości: od północy jest cały ze szkła do ogrodu, a od południa wychodzi na patio za murem 2,6 m, zadaszone w pasie przy domu; kuchnia stoi przy pełnym, wschodnim końcu południowej ściany, obok biblioteki, przez którą przechodzi się do spiżarni.",
        "Dachy parterowych rogów półksiężyca to dwa tarasy z balustradą po obu stronach szklanego dachu ogrodu: zachodni nad salą muzyczną i wiatrołapem z wyjściem z biura, wschodni nad spiżarnią i biblioteką z wyjściem z sypialni; najwyższy dach, nad modułami piętra, jest zielony.",
        "Na szczycie łuku stoją cztery moduły piętra połączone przelotowo: biuro przeszklone na północny zachód i na taras, galeria ze schodami, łazienka i sypialnia z przedsionkiem wzdłuż szklanego dachu oraz szklaną ścianą od północnego wschodu.",
    ],
    notes=dict(
        lato="Harmonijka szklanego dachu składa się i półkolisty ogród staje się otwartym dziedzińcem, do którego zagląda się z obu tarasów; patio za murem jest letnim przedłużeniem salonu, a cegła od północy trzyma chłód.",
        zima="Dach jest zamknięty, ogród działa jak oranżeria i bufor cieplny między pokojami, a mur patio i ceglane ściany z małymi oknami osłaniają dom od wiatru.",
        technologia="Ściany z ceramicznych pustaków szlifowanych na cienką spoinę z okładziną z cegły, łuk murowany z krótkich prostych odcinków co 7,5°; stropy z prefabrykowanych płyt kanałowych z warstwą spadkową pod tarasami, składany dach szklany i balustrady systemowe na stalowych ramach.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

# ogród: półkole w środku łuku, dach szklany harmonijkowy nad parterem
H.ogrod("og", "Ogród", sec(180, 360, 0.0, R_IN), levels=1, roof_type="fold", style="srodziemnomorski", seed=11)

# ---- parter: pasmo wzdłuż cięciwy (od zachodu do wschodu)
H.room("wia", "Wiatrołap", "wiatrolap", rc(-R_OUT, 0, -R_IN, 2.4), ext={"W": "solid"})
H.room("laz0", "Łazienka", "lazienka", rc(-R_OUT, 2.4, -R_IN, D))
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rc(-R_IN, 0, R_IN, D), levels=2, kitchen_at="E",
       ext={"pat": "glass_slide", "taW": "windows", "taE": "windows", "N": "glass", "S": "band_high", "*": "solid"})
H.room("pat", "Patio za murem", "patio", rc(-4.2, D, 1.2, D + 3.6), roof=rc(-4.2, D, 1.2, D + 1.6), enclose="gwall")
H.room("bib", "Biblioteka", "biblioteka", rc(R_IN, 0, R_OUT, D), ext={"E": "band_high", "S": "windows"},
       label_at=(C[0] + 6.4, C[1] + 3.45))
# ---- parter: pierścień po łuku (od rogu zachodniego przez północ do rogu wschodniego)
H.room("muz", "Sala muzyczna", "muzyczny", sec(180, 217.5), ext="slits")
H.room("pra", "Pracownia", "pracownia", sec(217.5, 247.5), ext="windows")
H.room("hol", "Hol", "hol", sec(247.5, 277.5), ext="slits")
H.room("her", "Herbaciarnia", "herbaciarnia", sec(277.5, 322.5), ext="windows")
H.room("spi", "Spiżarnia i pralnia", "pralnia", sec(322.5, 360), ext="windows_sq", garden="band_high")
H.stair("spiral", level=0, center=P(6.9, 262.5), r=1.0, start=180, sweep=300, n=16)

# ---- piętro: cztery moduły na szczycie łuku + tarasy na dachach rogów
H.room("biu", "Biuro", "biuro", sec(217.5, 247.5), level=1, ext={"taW": "glass", "*": "glass"})
H.room("gal", "Galeria", "galeria", sec(247.5, 277.5), level=1, ext={"N": "slits", "S": "glass"}, furn=False)
# sypialnia: przedsionek wzdłuż szklanego dachu ogrodu (za nim łazienka od strony elewacji) + pełny wycinek przy tarasie
H.room("syp", "Sypialnia", "sypialnia_glowna", union(sec(277.5, 307.5, R_IN, R_M), sec(307.5, 345)), level=1,
       ext={"taE": "glass", "S": "band", "SE": "band", "*": "glass"})
H.room("laz", "Łazienka", "lazienka", sec(277.5, 307.5, R_M, R_OUT), level=1)
H.room("taW", "Taras zachodni", "taras", union(sec(180, 217.5), rc(-R_OUT, 0, -R_IN, D)), level=1)
H.room("taE", "Taras wschodni", "taras", union(sec(345, 360), rc(R_IN, 0, R_OUT, D)), level=1)

# ---- połączenia: pętla parteru wokół ogrodu, drzwi przy szkle ogrodu (amfilada wzdłuż ogrodu)
H.connect("wia", "muz", "door", at=0.85)
H.connect("wia", "sal", "door", at=0.4)
H.connect("wia", "laz0", "door", at=0.5)
H.connect("muz", "pra", "door", at=0.76)
H.connect("pra", "hol", "door", at=0.76)
H.connect("hol", "her", "door", at=0.76)
H.connect("her", "spi", "door", at=0.76)
H.connect("spi", "bib", "door", at=0.3)
H.connect("sal", "bib", "door", at=0.17)
H.connect("hol", "og", "slide", width=1.2)
# ---- piętro: ciąg biuro – galeria – sypialnia (z łazienką), wyjścia na tarasy
H.connect("biu", "gal", "door", at=0.76)
H.connect("gal", "syp", "door")
H.connect("syp", "laz", "door")           # drzwi w łukowej ścianie przedsionka sypialni
H.connect("biu", "taW", "slide")
H.connect("syp", "taE", "slide")

H.entrance("wia", "W")
H.exit("spi", "E", kind="door", width=0.9)

# teren
H.path(rc(-14.0, 0.6, -R_OUT - 0.2, 1.8))
H.tree(-2.5, 4.0, "brzoza")
H.tree(23.0, 7.5, "lipa")
H.tree(21.5, 20.5, "klon")
H.tree(-1.0, 20.0, "sosna")

H.cut("A–A", (C[0] - 0.8, C[1] - 11.5), (C[0] - 0.8, C[1] + 9.5))
H.cut("B–B", (C[0] - 11.0, C[1] - 2.5), (C[0] + 11.0, C[1] - 2.5))
