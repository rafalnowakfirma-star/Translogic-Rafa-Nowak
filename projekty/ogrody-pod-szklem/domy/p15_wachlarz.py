"""P15 · Wachlarz – dom na planie wachlarza otwartego na południe: ogród w zawiasie, pokoje jak pióra."""
from silnik import House, rect, sector, poly, pt

C = (14.0, 4.4)          # zawias wachlarza (środek wszystkich łuków)
R_G, R_OUT = 6.0, 12.5   # promień ogrodu i zewnętrzny promień piór


def sec(a1, a2, r1=R_G, r2=R_OUT):
    return sector(C[0], C[1], r1, r2, a1, a2)


def bar(x1, x2, d=3.2):
    """Pokój w bloku wejściowym: pas o głębokości d na północ od średnicy ogrodu."""
    return rect(C[0] + x1, C[1] - d, C[0] + x2, C[1])


def P(r, a):
    return pt(C[0], C[1], r, a)


H = House(
    "p15", "Wachlarz",
    "Dom na planie wachlarza otwartego na południe. W zawiasie wachlarza jest półokrągły ogród pod rozsuwanym szklanym dachem, "
    "a pokoje to promieniste pióra, które rozchodzą się od ogrodu ku krajobrazowi.",
    style=dict(fasada="cegla_biala", dach="sedum", akcent="stal"),
    concept=[
        "Pokoje są wycinkami koła między promienistymi ścianami: przy ogrodzie mają 2–6 m szerokości, przy krajobrazie dwa razy tyle, "
        "więc każde pióro zwęża się ku ogrodowi i rozszerza ku widokowi jak kadr.",
        "Ogród to półkole o promieniu 6 m na wysokość dwóch kondygnacji. Jego szklany dach składa się z dwóch ćwiartek: latem zachodnia "
        "wsuwa się nad wschodnią, jak składany wachlarz.",
        "Biuro w piórze południowo-wschodnim ma szkło od ogrodu i od łąki, a przez drzwi w promienistych ścianach łączy się z biblioteką i salonem.",
        "Pióra tworzą jedną amfiladę wokół ogrodu: galeria ze schodami, biblioteka, biuro, salon, patio i herbaciarnia. Każde pióro ma też "
        "własne drzwi do ogrodu, który jest holem domu.",
        "Salon z kuchnią zajmuje dwa pióra na wysokość dwóch kondygnacji i przez szklaną ścianę przechodzi w patio zadaszone tylko przy ogrodzie; "
        "między ogrodem a patio jest szklana harmonijka, zimą zamknięta, latem złożona.",
        "Sypialnia jest na piętrze nad galerią: od wschodu ma całą ścianę ze szkła i wachlarzowy balkon, od ogrodu szkło stałe, od północy pełny mur; "
        "obok leży przelotowa garderoba i łazienka nad biblioteką. Blok wejściowy od północy domyka ogród: wiatrołap, WC, spiżarnia, pralnia i "
        "pomieszczenie techniczne w jednym rzędzie.",
    ],
    notes=dict(
        lato="Zachodnia ćwiartka szklanego dachu wsuwa się nad wschodnią, harmonijka między ogrodem a patio się składa i ogród staje się "
             "przewiewnym dziedzińcem; szklane ściany biura i salonu rozsuwają się na łąkę.",
        zima="Dach jest zasunięty, harmonijka zamknięta i ogród pracuje jak szklarnia: słońce z południa nagrzewa żwir i oliwkę, "
             "a wszystkie pióra wychodzą drzwiami na ciepły hol zamiast na mróz.",
        technologia="Ściany z bloczków silikatowych na cienką spoinę (promieniste ściany są proste, łuki tylko na elewacjach, z krótkich odcinków); "
                    "stropy i dachy z prefabrykowanych płyt kanałowych opartych na promienistych ścianach, które skracają rozpiętości do 3–7 m "
                    "(tylko nad salonem 12 m); dach szklany na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

# ogród w zawiasie wachlarza
H.ogrod("og", "Ogród", sector(C[0], C[1], 0, R_G, 0, 180), levels=2, roof_type="slide",
        style="srodziemnomorski", seed=4, edge="glass")

# blok wejściowy (północ) – domyka ogród wzdłuż średnicy
H.room("tech", "Techniczne", "techniczne", bar(-6.0, -4.1))
H.room("pral", "Pralnia", "pralnia", bar(-4.1, -2.2))
H.room("spi", "Spiżarnia", "spizarnia", bar(-2.2, -0.4))
H.room("wia", "Wiatrołap", "wiatrolap", bar(-0.4, 4.3))
H.room("wc", "WC", "wc", bar(4.3, 6.0))

# pióra wachlarza (od wschodu ku zachodowi)
H.room("gal", "Galeria", "galeria", sec(0, 30), ext={"N": "solid", "*": "slits"})
H.room("bib", "Biblioteka", "biblioteka", sec(30, 52), ext="band")
H.room("biu", "Biuro", "biuro", sec(52, 80), ext="glass_slide", garden="glass_slide")
H.room("sal", "Salon z kuchnią", "salon_kuchnia", sec(80, 138), levels=2,
       ext={"NW": "glass", "W": "glass", "*": "glass_slide"}, kitchen_at="E")
PAT_ROOF = poly([P(R_G, a) for a in (138, 142.5, 150, 157.5, 158)] + [P(9.6, 158), P(9.6, 148), P(9.6, 138)])
H.room("pat", "Patio", "patio", sec(138, 158), roof=PAT_ROOF)
H.room("her", "Herbaciarnia", "herbaciarnia", sec(158, 180),
       ext={"N": "solid", "NW": "solid", "S": "glass", "SE": "glass", "*": "glass_slide"})

# piętro – apartament właścicieli nad piórami wschodnimi
H.room("syp", "Sypialnia", "sypialnia_glowna", sec(0, 30), level=1,
       ext={"N": "solid", "*": "glass_slide"}, garden="glass", garden_door=False)
H.room("bal", "Balkon", "taras", sec(3, 27, R_OUT, 14.0), level=1)
H.room("gard", "Garderoba", "garderoba", sec(30, 52, R_G, 9.0), level=1)
H.room("laz", "Łazienka", "lazienka", sec(30, 52, 9.0, R_OUT), level=1)
H.stair("straight", level=0, rect=(C[0] + 6.3, C[1] + 0.35, C[0] + 11.5, C[1] + 1.45), up="E")

# drzwi
H.connect("wia", "spi", "door")
H.connect("spi", "pral", "door")
H.connect("pral", "tech", "door")
H.connect("wia", "wc", "door")
H.connect("gal", "bib", "double")
H.connect("bib", "biu", "double")
H.connect("biu", "sal", "wide")
H.connect("sal", "pat", "slide")
H.connect("pat", "her", "slide")
H.connect("og", "pat", "fold")
H.connect("syp", "gard", "door")
H.connect("gard", "laz", "slide")
H.entrance("wia", "N")
H.exit("tech", "N", kind="door", width=1.0)

# teren
H.path(rect(C[0] + 1.25, C[1] - 10.0, C[0] + 2.65, C[1] - 3.4))
H.path(sector(C[0], C[1], 12.7, 15.5, 138, 158))
H.tree(C[0] + 16.5, C[1] + 8.5, "oliwka")
H.tree(C[0] - 16.0, C[1] + 7.0, "oliwka")
H.tree(C[0] - 10.5, C[1] - 4.5, "sosna")
H.tree(C[0] + 11.5, C[1] - 6.5, "lipa")

H.cut("A–A", (C[0] + 1.9, C[1] - 6.0), (C[0] + 1.9, C[1] + 15.0))
H.cut("B–B", (C[0] + 17.0, C[1] + 1.0), (C[0] - 17.0, C[1] + 1.0))
