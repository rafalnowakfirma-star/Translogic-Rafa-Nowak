"""P15 · Wachlarz (wersja 2) – pięć krótkich piór wokół półokrągłego, ukrytego ogrodu; blok wejściowy od północy,
tarasy na dachach parteru wokół szklanego dachu ogrodu, trzy moduły piętra (biuro, sypialnia, łazienka) nad galerią
i wschodnim piórem. 164 m² użytkowe."""
import math

from silnik import House, rect, sector, poly, union

C = (12.0, 5.0)              # zawias wachlarza – środek wszystkich łuków
R_G = 5.0                    # promień ogrodu
R_OUT = 9.0                  # zewnętrzny promień piór wschodnich
R_W = 9.4                    # pióro gościnne (dłuższa ściana salonu pod kuchnię)
R_S = 9.8                    # salon – najdłuższe pióro
R_MID = 7.5                  # podział pióra piętra: łazienka / taras
R_PAT = 12.6                 # zewnętrzny promień patio za murem
D = 3.0                      # głębokość bloku wejściowego


def sec(a1, a2, r1=R_G, r2=R_OUT):
    return sector(C[0], C[1], r1, r2, a1, a2)


def bar(x1, x2, y1=-D, y2=0.0):
    """Prostokąt w bloku wejściowym (x względem zawiasu, y na północ od średnicy ogrodu)."""
    return rect(C[0] + x1, C[1] + y1, C[0] + x2, C[1] + y2)


def P(x, y):
    return (C[0] + x, C[1] + y)


H = House(
    "p15", "Wachlarz",
    "Dom na planie wachlarza: pięć krótkich piór wokół półokrągłego ogrodu, którego z zewnątrz nie widać. "
    "Dachy niskich piór to tarasy wokół szklanego dachu ogrodu, a nad galerią i wschodnim piórem stoją trzy moduły piętra: "
    "biuro, sypialnia i łazienka.",
    style=dict(fasada="cegla_biala", dach="sedum", akcent="stal"),
    concept=[
        "Ogród to półkole o promieniu 5 m (37 m²) w zawiasie wachlarza. Ze wszystkich stron otaczają go pokoje: pięć piór "
        "od południa i blok wejściowy wzdłuż średnicy od północy; pióra mają od zewnątrz tylko okna, więc ogrodu nie widać "
        "ani z drogi, ani z łąki.",
        "Wchodzi się przez wiatrołap z pełną ścianą od ogrodu. Ogród pokazuje się dopiero w galerii, za drugimi drzwiami, "
        "a dalej idzie się przez bibliotekę, herbaciarnię i pokój muzyczny do salonu – wszystkie drzwi stoją w narożnikach "
        "przy szkle ogrodu, więc obchodzi się go jak krużganek, bez korytarza.",
        "Salon z kuchnią to najdłuższe pióro, na południowym zachodzie, wysokie na dwie kondygnacje. Od ogrodu jest cały "
        "ze szkła, a od pola otwiera się na patio za murem 2,6 m (26 m²), zadaszone tylko pasem przy salonie; kuchnia stoi "
        "przy ścianie pokoju gościnnego, wypoczynek przy pokoju muzycznym.",
        "Dachy niskich piór to tarasy wokół szklanego dachu ogrodu: wschodni (18 m²) nad herbaciarnią i pokojem muzycznym, "
        "północny (39 m²) nad blokiem wejściowym i pokojem gościnnym. Najwyższy dach, nad modułami piętra i salonem, jest zielony.",
        "Na piętrze trzy moduły w ciągu: biuro nad galerią, do którego prowadzą schody kręcone, ze szkłem na północ, pasmem "
        "okien nad dachem ogrodu i drzwiami na taras północny; sypialnia nad biblioteką ze szklaną ścianą na wschód i wyjściem "
        "na taras wschodni; za nią łazienka. Z jednego pomieszczenia przechodzi się do drugiego drzwiami.",
        "Pióra mają różną długość – salon 9,8 m, pokój gościnny 9,4 m, pióra wschodnie 9 m – więc obrys zachowuje rysunek "
        "wachlarza o nierównych piórach, a dwa wyższe elementy, salon i moduły piętra, stoją po przeciwnych stronach "
        "szklanego dachu. Razem z piętrem dom ma 164 m².",
    ],
    notes=dict(
        lato="Połowa szklanego dachu zsuwa się nad drugą i ogród staje się otwartym dziedzińcem, na który patrzy się z obu "
             "tarasów; szklana ściana salonu rozsuwa się na patio za murem, a drzwi każdego pióra do ogrodu stoją otworem.",
        zima="Dach jest zasunięty i ogród działa jak nasłoneczniona szklarnia między pokojami – wszystkie pióra wychodzą "
             "na niego drzwiami, a pełne ściany z białej cegły od północy i mur patio osłaniają dom od wiatru.",
        technologia="Ściany z bloczków silikatowych na cienką spoinę, z zewnątrz biała cegła klinkierowa murowana po łuku "
                    "z krótkich odcinków; stropy i dachy z prefabrykowanych płyt kanałowych opartych na promienistych ścianach "
                    "(rozpiętości 4–6 m, nad salonem 9 m), tarasy na stropie z warstwą spadkową, szklany dach ogrodu na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

# ogród w zawiasie wachlarza – jedna kondygnacja, szklany dach na wysokości dachu parteru
H.ogrod("og", "Ogród", sector(C[0], C[1], 0, R_G, 0, 180), levels=1, roof_type="slide",
        style="srodziemnomorski", seed=4)

# blok wejściowy (północ), od zachodu ku wschodowi
H.room("laz0", "Łazienka gości", "lazienka", bar(-7.6, -5.0))
H.room("pral", "Pralnia", "pralnia", bar(-5.0, -3.2), garden="band_high")
H.room("wc", "WC", "wc", bar(-3.2, -1.6, -D, -1.0))
H.room("wia", "Wiatrołap", "wiatrolap",
       poly(P(-1.6, -D), P(1.6, -D), P(1.6, 0), P(-3.2, 0), P(-3.2, -1.0), P(-1.6, -1.0)),
       garden="solid", ext="slits")
H.room("gal", "Galeria", "galeria", bar(1.6, 8.2), ext={"N": "slits", "E": "windows_sq"})

# pióra wachlarza (od wschodu ku zachodowi)
H.room("bib", "Biblioteka", "biblioteka", sec(0, 34), ext="windows", label_at=P(7.0, 1.0))
H.room("her", "Herbaciarnia", "herbaciarnia", sec(34, 62), ext="windows")
H.room("muz", "Pokój muzyczny", "muzyczny", sec(62, 92), ext="windows")
H.room("sal", "Salon z kuchnią", "salon_kuchnia", sec(92, 158, R_G, R_S), levels=2, kitchen_at="W",
       ext={"pat": "glass_slide", "t1": "windows", "*": "band"})
H.room("pat", "Patio za murem", "patio", sector(C[0], C[1], R_S, R_PAT, 98, 152),
       roof=sector(C[0], C[1], R_S, R_S + 1.3, 98, 152), enclose="gwall")
H.room("gos", "Pokój gościnny", "gosc", sec(158, 180, R_G, R_W), ext="windows", label_at=P(-7.4, 1.5))

# schody kręcone we wschodnim końcu galerii – na górze wychodzi się w biurze
H.stair("spiral", level=0, center=P(6.85, -1.45), r=1.0, start=90, sweep=300, n=16)

# piętro – trzy moduły w ciągu i dwa tarasy wokół szklanego dachu ogrodu
H.room("biu", "Biuro", "biuro", bar(1.6, 8.2), level=1,
       ext={"N": "glass", "t2": "glass", "E": "windows", "S": "band"})
H.room("syp", "Sypialnia", "sypialnia_glowna", sec(0, 34), level=1,
       ext={"E": "glass", "W": "windows", "t1": "glass", "*": "solid"})
H.room("laz", "Łazienka", "lazienka", sec(34, 62, R_G, R_MID), level=1)
H.room("t1", "Taras wschodni", "taras", union(sec(34, 62, R_MID, R_OUT), sec(62, 92)), level=1)
H.room("t2", "Taras północny", "taras", union(bar(-7.6, 1.6), sec(158, 180, R_G, R_W)), level=1)

# drzwi – parter (drzwi amfilady przy ogrodzie)
H.connect("wia", "wc", "door", at=0.1)
H.connect("wia", "pral", "door")
H.connect("wia", "gal", "door")
H.connect("gal", "bib", "door", at=0.9)
H.connect("bib", "her", "door", at=0.9)
H.connect("her", "muz", "door", at=0.9)
H.connect("muz", "sal", "double", at=0.9)
H.connect("sal", "gos", "door", at=0.9)
H.connect("gos", "laz0", "door", at=0.1)
# drzwi – piętro
H.connect("biu", "syp", "door", at=0.9)
H.connect("syp", "laz", "door", at=0.9)
H.connect("syp", "t1", "slide")
H.connect("biu", "t2", "slide")
H.entrance("wia", "N")
H.exit("pral", "N", kind="door", width=0.9)

# teren
H.path(rect(C[0] - 0.7, C[1] - 9.5, C[0] + 0.7, C[1] - D - 0.2))
H.tree(C[0] + 13.0, C[1] + 9.0, "oliwka")
H.tree(C[0] - 13.5, C[1] + 10.0, "oliwka")
H.tree(C[0] - 11.0, C[1] - 4.5, "sosna")
H.tree(C[0] + 10.5, C[1] - 6.5, "lipa")

# przekrój promienisty pod kątem 100°: wejście, ogród, wysoki salon i patio za murem
_ca, _sa = math.cos(math.radians(100)), math.sin(math.radians(100))
H.cut("A–A", P(-7.0 * _ca, -7.0 * _sa), P(16.0 * _ca, 16.0 * _sa))
H.cut("B–B", (C[0] + 16.0, C[1] + 2.2), (C[0] - 16.0, C[1] + 2.2))
