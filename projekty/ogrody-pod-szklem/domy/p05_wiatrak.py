"""P05 · Wiatrak (wersja 2) – cztery proste skrzydła jak łopaty wiatraczka wokół ukrytego ogrodu 6 × 6 m;
dwie łopaty parterowe z tarasami na dachu, dwie z modułami piętra ustawionymi w literę L."""
from silnik import House, rect, union

# Ogród 6 × 6 m w kwadracie (6,6)–(12,12). Cztery skrzydła obiegają go zgodnie z ruchem wskazówek zegara
# i każde wystaje 2,8 m poza obrys sąsiada:
#   zachodnie  x 2,8–6   y 0–12     (wystaje na północ: wiatrołap i WC, nad nimi łazienka)
#   północne   y 2,8–6   x 6–19,2   (wystaje na wschód: loggia, nad nią koniec tarasu)
#   wschodnie  x 12–16,4 y 6–18     (wystaje na południe: zadaszona część patio za murem)
#   południowe y 12–15   x 0–12     (wystaje na zachód: drewutnia)
# Piętro: moduły w literę L nad skrzydłem zachodnim i początkiem północnego; tarasy na dachach
# skrzydła południowego i wschodniej części północnego.

H = House(
    "p05", "Wiatrak",
    "Cztery proste skrzydła ułożone jak łopaty wiatraczka wokół kwadratowego ogrodu, którego z zewnątrz nie widać. "
    "Na dachach niskich skrzydeł są dwa tarasy, nad skrzydłem zachodnim i początkiem północnego stoją moduły piętra w literę L, "
    "a skrzydło wschodnie to wysoki salon.",
    style=dict(fasada="trawertyn", dach="sedum", akcent="stal"),
    concept=[
        "Ogród 6 × 6 m leży w środku, a cztery skrzydła szerokości 3,0–4,4 m obiegają go zgodnie z ruchem wskazówek zegara. "
        "Każde wystaje około 3 m poza sąsiednie, więc między końcami łopat są cztery dziedzińce: wejściowy od północy, poranny od wschodu, "
        "patio za murem od południa i gospodarczy od zachodu.",
        "Z zewnątrz ogrodu nie widać: pokoje przy ogrodzie mają od strony krajobrazu tylko okna i szczeliny, a szkło przesuwne "
        "wychodzi wyłącznie na patio schowane za murem wysokości 2,6 m. Wiatrołap na końcu zachodniej łopaty nie styka się z ogrodem.",
        "Parter obchodzi się bez korytarzy: z holu ze schodami kręconymi przez bibliotekę i pokój muzyczny z loggią na końcu łopaty "
        "do wysokiego salonu, z salonu do herbaciarni i pralni; przy holu są WC i pokój gościnny przy ogrodzie.",
        "Salon z kuchnią we wschodniej łopacie ma 6,6 m wysokości, szkło od ogrodu i szkło na patio, nad którym daszek tworzy "
        "wystający koniec skrzydła.",
        "Dachy skrzydła południowego i wschodniej części północnego to tarasy z balustradą; wychodzi się na nie z sypialni i z biura. "
        "Najwyższy dach nad modułami piętra jest zielony.",
        "Na piętrze cztery moduły w literę L połączone drzwiami: łazienka nad wiatrołapem, galeria ze schodami, sypialnia ze szklaną "
        "ścianą od zachodu i biuro przeszklone na pola od północy i na taras od wschodu.",
    ],
    notes=dict(
        lato="Połowa szklanego dachu zsuwa się nad drugą i ogród z oliwką stoi pod gołym niebem, szkło salonu i herbaciarni rozsuwa się na patio za murem, a z dwóch tarasów zagląda się do ogrodu z góry.",
        zima="Dach jest zamknięty, ogród ze żwirem i kamieniem zbiera ciepło ze słońca i ociepla cztery pokoje wokół, a mur patio i pełne ściany końców łopat osłaniają dom od wiatru.",
        technologia="Ściany z bloczków silikatowych na cienką spoinę z okładziną z płyt trawertynu na ruszcie, stropy i dachy z prefabrykowanych płyt kanałowych, tarasy na stropach z warstwą spadkową; daszki końców łopat na stalowych słupach, dach szklany na stalowej ramie z napędem przesuwnym.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

H.ogrod("og", "Ogród", rect(6, 6, 12, 12), levels=1, roof_type="slide", style="srodziemnomorski", seed=11)

# skrzydło zachodnie (x 2,8–6): wiatrołap na końcu, hol ze schodami, pokój gościnny przy ogrodzie
H.room("wia", "Wiatrołap", "wiatrolap", rect(2.8, 0, 6, 2.8), ext={"N": "slits", "E": "solid", "W": "solid"})
H.room("hol", "Hol", "hol", rect(2.8, 2.8, 6, 6), ext={"W": "windows"})
H.room("gos", "Pokój gościnny", "gosc", rect(2.8, 6, 6, 12), ext={"W": "windows"})

# skrzydło północne (y 2,8–6): WC przy holu, biblioteka – pokój muzyczny – loggia na końcu
H.room("wc", "WC", "wc", rect(6, 2.8, 7.8, 4.7))
H.room("bib", "Biblioteka", "biblioteka", union(rect(7.8, 2.8, 12, 6), rect(6, 4.7, 7.8, 6)), ext={"N": "slits"})
H.room("muz", "Pokój muzyczny", "muzyczny", rect(12, 2.8, 16.4, 6), ext={"N": "windows", "log": "glass_slide", "*": "windows"})
H.room("log", "Loggia", "loggia", rect(16.4, 2.8, 19.2, 6))

# skrzydło wschodnie (x 12–16,4): wysoki salon z kuchnią, na końcu patio za murem z daszkiem
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(12, 6, 16.4, 15), levels=2, kitchen_at="S",
       ext={"pat": "glass_slide", "taN": "windows", "taS": "glass", "*": "windows"})
H.room("pat", "Patio za murem", "patio", rect(6, 15, 16.4, 18), roof=rect(12, 15, 16.4, 18), enclose="gwall")

# skrzydło południowe (y 12–15): herbaciarnia przy ogrodzie, pralnia, drewutnia na końcu
H.room("her", "Herbaciarnia", "herbaciarnia", rect(6, 12, 12, 15), ext={"pat": "glass_slide", "*": "windows"})
H.room("pra", "Pralnia i techniczne", "pralnia", rect(2.8, 12, 6, 15), ext={"S": "windows_sq", "*": "solid"})
H.room("dre", "Drewutnia", "loggia", rect(0, 12, 2.8, 15), floor="plyty", furn=False)

H.stair("spiral", level=0, center=(4.0, 4.35), r=0.95, start=30, sweep=300, n=15)

# piętro: moduły w literę L (łazienka – galeria – sypialnia, galeria – biuro) i dwa tarasy
H.room("laz", "Łazienka", "lazienka", rect(2.8, 0, 6, 2.8), level=1)
H.room("gal", "Galeria", "galeria", rect(2.8, 2.8, 6, 6), level=1, ext={"W": "windows"})
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(2.8, 6, 6, 12), level=1,
       ext={"W": "glass", "E": "windows", "taS": "glass_slide"})
H.room("biu", "Biuro", "biuro", rect(6, 2.8, 9.6, 6), level=1, ext={"N": "glass", "S": "windows", "taN": "glass_slide"})
H.room("taS", "Taras południowy", "taras", rect(2.8, 12, 12, 15), level=1)
H.room("taN", "Taras północny", "taras", rect(9.6, 2.8, 19.2, 6), level=1)

# połączenia parteru
H.connect("hol", "wia", "door", at=0.2)
H.connect("hol", "wc", "door")
H.connect("hol", "bib", "door")
H.connect("hol", "gos", "door", at=0.15)
H.connect("bib", "muz", "double")
H.connect("muz", "sal", "double")
H.connect("muz", "log", "slide")
H.connect("sal", "her", "door", at=0.5)
H.connect("her", "pra", "door", at=0.3)
# połączenia piętra
H.connect("gal", "laz", "door", at=0.2)
H.connect("gal", "syp", "door", at=0.15)
H.connect("gal", "biu", "door", at=0.2)
H.connect("syp", "taS", "slide")
H.connect("biu", "taN", "slide")

H.entrance("wia", "E")
H.exit("pra", "W", kind="door", width=1.0)

# teren: dojście od północy wzdłuż wiatrołapa do dziedzińca wejściowego, podwórze gospodarcze przy drewutni
H.path(rect(6.4, -5.5, 7.8, 2.8))
H.path(rect(6.0, 0.0, 9.6, 2.8))
H.path(rect(-2.6, 12.4, 0.0, 15.0))
H.tree(1.0, 3.5, "oliwka")
H.tree(14.0, -2.6, "brzoza")
H.tree(20.5, 11.0, "lipa")
H.tree(6.0, 21.5, "klon")

H.cut("A–A", (9.0, -2.0), (9.0, 20.5))
H.cut("B–B", (-2.0, 9.0), (21.5, 9.0))
