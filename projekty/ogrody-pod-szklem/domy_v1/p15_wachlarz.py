"""P15 · Wachlarz – dom na planie wachlarza otwartego na południe: ogród w zawiasie, pokoje jak pióra."""
from silnik import House, rect, sector, poly, pt

C = (14.0, 4.4)          # zawias wachlarza – środek wszystkich łuków
R_G, R_OUT = 6.0, 12.8   # promień ogrodu i zewnętrzny promień piór
R_PAT = 10.0             # zewnętrzny promień patio (dalej salonik obejmuje patio od południa)


def sec(a1, a2, r1=R_G, r2=R_OUT):
    return sector(C[0], C[1], r1, r2, a1, a2)


def bar(x1, x2, d=3.6):
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
        "Siedem piór między promienistymi ścianami rozchodzi się od półokrągłego ogrodu w zawiasie wachlarza: przy ogrodzie pióro ma 2–5 m "
        "szerokości, przy krajobrazie dwa razy tyle. Ogród jest holem domu – każde pióro ma do niego własne drzwi.",
        "Ogród ma 6 m promienia i wysokość dwóch kondygnacji. Jego szklany dach składa się z dwóch ćwiartek: latem wschodnia wsuwa się nad "
        "zachodnią, jak składany wachlarz.",
        "Biuro w piórze południowo-wschodnim ma szkło od ogrodu i od łąki. Drzwi w promienistych ścianach stoją przy szklanej elewacji, "
        "więc przez galerię, bibliotekę, biuro i salon biegnie jedna oś widokowa.",
        "Salon z kuchnią leży na osi południowej i ma dwie kondygnacje wysokości. Dalej amfilada prowadzi przez patio do herbaciarni i pokoju "
        "gościnnego, a za patio salon ma salonik ze szkłem na zachód. Patio to dziedziniec między ogrodem, salonem i herbaciarnią, zadaszony "
        "tylko pasem przy ogrodzie; od ogrodu zamyka je szklana harmonijka, zimą zamknięta, latem złożona.",
        "Sypialnia jest na piętrze nad galerią, do której prowadzą schody wzdłuż pełnej północnej ściany. Od wschodu ma całą ścianę ze szkła "
        "i wachlarzowy balkon, od ogrodu szkło stałe; obok leży przelotowa garderoba i łazienka nad biblioteką.",
        "Blok wejściowy od północy domyka ogród wzdłuż jego średnicy: łazienka gości, WC, wiatrołap na osi, pralnia z kotłownią i spiżarnia. "
        "Pióra wschodnie i salon mają dwie kondygnacje, biuro, herbaciarnia i pokój gościnny jedną, więc bryła faluje: wysoko, nisko, wysoko, nisko.",
    ],
    notes=dict(
        lato="Wschodnia ćwiartka szklanego dachu wsuwa się nad zachodnią, harmonijka między ogrodem a patio się składa i ogród z patio "
             "stają się jednym przewiewnym dziedzińcem; szklane ściany biura, salonu i herbaciarni rozsuwają się na łąkę.",
        zima="Dach jest zasunięty, harmonijka zamknięta i ogród pracuje jak szklarnia: słońce z południa nagrzewa żwir i oliwkę, a wszystkie "
             "pokoje wychodzą drzwiami na ciepły hol zamiast na mróz; patio zostaje otwartym dziedzińcem oglądanym z salonu i saloniku.",
        technologia="Ściany z bloczków silikatowych na cienką spoinę: promieniste ściany są proste, łuki tylko na elewacjach, murowane z krótkich "
                    "odcinków. Stropy i dachy z prefabrykowanych płyt kanałowych opartych na promienistych ścianach, które skracają rozpiętości "
                    "do 3–7 m (nad salonem 11 m); szklany dach ogrodu na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

# ogród w zawiasie wachlarza
H.ogrod("og", "Ogród", sector(C[0], C[1], 0, R_G, 0, 180), levels=2, roof_type="slide",
        style="srodziemnomorski", seed=4, edge="glass")

# blok wejściowy (północ) – domyka ogród wzdłuż średnicy, od zachodu ku wschodowi
H.room("lazg", "Łazienka", "lazienka", bar(-6.0, -3.9), garden="solid")
H.room("wc", "WC", "wc", bar(-3.9, -2.4))
H.room("wia", "Wiatrołap", "wiatrolap", bar(-2.4, 1.2))
H.room("pral", "Pralnia i kotłownia", "pralnia", bar(1.2, 3.8))
H.room("spi", "Spiżarnia", "spizarnia", bar(3.8, 6.0), garden="solid")

# pióra wachlarza (od wschodu ku zachodowi)
H.room("gal", "Galeria", "galeria", sec(0, 23), ext={"N": "solid", "*": "slits"})
H.room("bib", "Biblioteka", "biblioteka", sec(23, 45), ext="band")
H.room("biu", "Biuro", "biuro", sec(45, 66), ext="glass_slide", garden="glass_slide")
# salon: dwa pióra na wysokość dwóch kondygnacji; za patio salonik (wypoczynek) otwarty do salonu szeroką wnęką
H.room("sal", "Salon z kuchnią", "salon_kuchnia", sec(66, 114), levels=2,
       ext={"NW": "glass", "W": "glass", "*": "glass_slide"}, kitchen_at="E")
H.room("wyp", "Salonik", "salon", sec(114, 136, R_PAT, R_OUT), levels=2, ext="glass")
# patio: dziedziniec między ogrodem, salonem i herbaciarnią; zadaszony tylko pas przy ogrodzie
PAT_ROOF = poly([P(R_G, a) for a in (114, 120, 127.5, 135, 136)] + [P(8.6, 136), P(8.6, 125), P(8.6, 114)])
H.room("pat", "Patio", "patio", sec(114, 136, R_G, R_PAT), roof=PAT_ROOF)
H.room("her", "Herbaciarnia", "herbaciarnia", sec(136, 158), ext={"SE": "glass", "*": "glass_slide"})
H.room("gos", "Pokój gościnny", "gosc", sec(158, 180), ext={"N": "slits", "*": "windows"})

# piętro – apartament właścicieli nad piórami wschodnimi
H.room("syp", "Sypialnia", "sypialnia_glowna", sec(0, 23), level=1,
       ext={"N": "solid", "*": "glass_slide"}, garden="glass", garden_door=False)
H.room("bal", "Balkon", "taras", sec(3, 20, R_OUT, R_OUT + 1.5), level=1)
H.room("gard", "Garderoba", "garderoba", sec(23, 45, R_G, 9.5), level=1)
H.room("laz", "Łazienka", "lazienka", sec(23, 45, 9.5, R_OUT), level=1)
# schody wzdłuż pełnej ściany północnej galerii: start przy elewacji, na górze wychodzi się przy szkle ogrodu
H.stair("straight", level=0, rect=(C[0] + 6.4, C[1] + 0.35, C[0] + 11.6, C[1] + 1.45), up="W")

# drzwi
H.connect("wia", "wc", "door")
H.connect("wia", "pral", "door")
H.connect("spi", "og", "door")
H.connect("lazg", "og", "door")
# amfilada: drzwi przy zewnętrznym końcu ścian promienistych (oś widokowa wzdłuż szklanej elewacji)
H.connect("gal", "bib", "double", at=0.1)
H.connect("bib", "biu", "double", at=0.1)
H.connect("biu", "sal", "double", at=0.1)
H.connect("sal", "wyp", "open")
# salon → patio → herbaciarnia: oboje drzwi na promieniu 7,3 m, pod zadaszonym pasem patio
H.connect("sal", "pat", "slide", at=(R_PAT - 7.3) / (R_PAT - R_G))
H.connect("pat", "her", "slide", at=(R_PAT - 7.3) / (R_PAT - R_G))
H.connect("wyp", "her", "door", at=0.1)
H.connect("her", "gos", "door", at=0.1)
H.connect("og", "pat", "fold")
H.connect("syp", "gard", "door")
H.connect("gard", "laz", "slide")
H.entrance("wia", "N", at=2.4 / 3.6)

# teren
H.path(rect(C[0] - 0.7, C[1] - 10.0, C[0] + 0.7, C[1] - 3.8))
H.path(sector(C[0], C[1], R_OUT + 0.2, R_OUT + 3.0, 79, 101))
H.tree(C[0] + 17.0, C[1] + 9.0, "oliwka")
H.tree(C[0] - 17.0, C[1] + 8.0, "oliwka")
H.tree(C[0] - 10.5, C[1] - 5.0, "sosna")
H.tree(C[0] + 11.0, C[1] - 6.5, "lipa")

H.cut("A–A", (C[0], C[1] - 6.5), (C[0], C[1] + 16.0))
H.cut("B–B", (C[0] + 17.0, C[1] + 1.0), (C[0] - 17.0, C[1] + 1.0))
