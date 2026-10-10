"""P11 · Półksiężyc – ceglany półksiężyc na dwie kondygnacje obejmuje półkolisty ogród pod składanym szklanym dachem."""
import math

from silnik import House, sector, rect, poly, union

# Wspólny środek wszystkich łuków: pokoje w pierścieniu 5,5–12 m, ogród w półkolu w środku.
# Wszystkie granice promieniowe leżą na siatce 7,5° silnika, więc łuki sąsiadów mają te same wierzchołki.
C = (12.0, 12.0)
R_IN, R_OUT = 5.5, 12.0     # pierścień pokoi
R_M = 8.5                   # podział piętra na pas wewnętrzny / zewnętrzny
A0, A1 = 165, 375           # łuk półksiężyca: od rogu SW przez północ do rogu SE (90 = S, 270 = N)


def sec(a1, a2, r1=R_IN, r2=R_OUT):
    return sector(C[0], C[1], r1, r2, a1, a2)


def sec2(a1, a2):
    """Pełny wycinek pierścienia z wierzchołkiem na promieniu R_M – wspólne wierzchołki z pokojami dzielonymi na pasy."""
    return union(sec(a1, a2, R_IN, R_M), sec(a1, a2, R_M, R_OUT))


def P(r, a):
    return (C[0] + r * math.cos(math.radians(a)), C[1] + r * math.sin(math.radians(a)))


H = House(
    "p11", "Półksiężyc",
    "Dom jak półksiężyc z cegły, na dwie kondygnacje, obejmuje półkolisty ogród pod składanym szklanym dachem. "
    "Od południa ogród zamyka szklana harmonijka: zimą jest oranżerią, latem otwartym dziedzińcem, który przechodzi w łąkę.",
    style=dict(fasada="cegla", dach="sedum", akcent="stal"),
    concept=[
        "Pokoje leżą w pierścieniu o promieniach 5,5–12 m na łuku 210°, a ogród wypełnia półkole w środku. Wypukła, północna strona domu jest z cegły z nielicznymi oknami, wklęsła strona od ogrodu jest cała ze szkła.",
        "Biuro zajmuje wschodni róg półksiężyca i ma szkło z trzech stron: od ogrodu, od wschodnich pól i od południa, gdzie przesuwne drzwi wychodzą na kamienny taras przed domem.",
        "Po łuku idzie się z pokoju do pokoju, bez korytarzy: z patio przez salon, hol ze schodami, bibliotekę i herbaciarnię do biura. WC i pralnia to dwie nisze holu od strony ogrodu, więc wejście i schody mają wolną przestrzeń.",
        "Salon z kuchnią przy zachodnim rogu ma dwie kondygnacje i szklaną ścianę do ogrodu na całą wysokość. Za szklaną harmonijką jest zadaszone patio sezonowe na samym końcu rogu: zimą zamknięte szkłem, latem otwarte z trzech stron.",
        "Piętro zajmuje północno-wschodnią część łuku: pracownia nad holem, przelotowa garderoba, łazienka i sypialnia ze szklanymi ścianami od wschodu i w stronę ogrodu, z której wychodzi się na taras na dachu biura.",
        "Dach ogrodu to szklana harmonijka na wysokości 3,75 m, czyli tuż nad podłogą piętra. Z sypialni i pracowni patrzy się ponad nim na południową łąkę, a latem, gdy jest złożony, w dół na drzewa w ogrodzie.",
    ],
    notes=dict(
        lato="Harmonijka od południa i szklany dach ogrodu składają się, patio otwiera się z trzech stron i ogród staje się dziedzińcem przechodzącym w łąkę; ceglana ściana od północy trzyma chłód.",
        zima="Ogród jest zamkniętą oranżerią z oliwką, lawendą i roślinami w donicach; zbiera niskie słońce z południa i ogrzewa wklęsłą, szklaną stronę domu, a cegła od północy osłania od wiatru.",
        technologia="Ściany z ceramicznych pustaków szlifowanych na cienką spoinę, łuk murowany z krótkich prostych odcinków co 7,5°; stropy z prefabrykowanych płyt kanałowych, harmonijki ścian i dach szklany systemowe, na stalowych ramach.",
    ),
)
H.level(0, z=0.0, h=3.5)
H.level(1, z=3.5, h=3.3)

# ogród: półkole z lekkim załamaniem od południa, zamknięte harmonijką
H.ogrod("og", "Ogród", sec(A0, A1, 0.0, R_IN), levels=1, roof_type="fold", style="srodziemnomorski", edge="fold", seed=11)

# ---- parter, po łuku od rogu zachodniego do wschodniego
H.room("pat", "Patio sezonowe", "patio_sezonowe", sec(A0, 195))
H.room("sal", "Salon z kuchnią", "salon_kuchnia", sec2(195, 255), levels=2,
       ext={"SE": "glass", "S": "glass", "*": "windows"}, kitchen_at="N")
# hol: pełna głębokość przy salonie, dalej pas zewnętrzny nad dwiema niszami od strony ogrodu
# (kawałki dobrane tak, by wspólne krawędzie miały identyczne wierzchołki – inaczej union daje MultiPolygon)
HOL = union(sec(255, 270, R_IN, 7.75), sec(255, 270, 7.75, R_OUT), sec(270, 285, 7.75, R_OUT),
            sec(285, 300, 7.25, 7.75), sec(285, 300, 7.75, R_OUT))
assert HOL.geom_type == "Polygon", HOL.geom_type
H.room("hol", "Hol", "hol", HOL, ext="slits")
H.room("pral", "Pralnia", "pralnia", sec(270, 285, R_IN, 7.75), garden="band_high")
H.room("wc", "WC", "wc", sec(285, 300, R_IN, 7.25))
H.room("bib", "Biblioteka", "biblioteka", sec(300, 322.5), ext="band_high")
H.room("her", "Herbaciarnia", "herbaciarnia", sec(322.5, 345), ext="slits")
H.room("biu", "Biuro", "biuro", sec(345, A1), ext={"E": "glass", "S": "glass"}, garden="glass_slide")

# ---- piętro nad północno-wschodnią częścią łuku
H.room("pra", "Pracownia", "pracownia", sec2(255, 292.5), level=1, ext={"N": "windows", "S": "glass"})
H.room("gar", "Garderoba", "garderoba", sec(292.5, 315, R_IN, R_M), level=1)
H.room("laz", "Łazienka", "lazienka", sec(292.5, 315, R_M, R_OUT), level=1)
H.room("syp", "Sypialnia", "sypialnia_glowna", sec2(315, 345), level=1, ext="glass")
H.room("tar", "Taras", "taras", sec2(345, A1), level=1)

# schody dwubiegowe wzdłuż północnej ściany holu; wejście na piętro do pracowni
H.stair("U", level=0, rect=(C[0] - 1.5, C[1] - 11.3, C[0] + 2.3, C[1] - 9.0), up="W")

# ---- połączenia: amfilada parteru
H.connect("sal", "pat", "fold")
H.connect("pat", "og", "slide")
H.connect("sal", "hol", "wide", at=0.78)        # przejście przy szkle ogrodu, kuchnia pod ścianą dalej od ogrodu
H.connect("hol", "og", "slide", width=1.2)
H.connect("hol", "pral", "door")
H.connect("hol", "wc", "door")
H.connect("hol", "bib", "wide")
H.connect("bib", "her", "double")
H.connect("her", "biu", "double")
# ---- piętro
H.connect("pra", "gar", "door")
H.connect("gar", "laz", "door")
H.connect("gar", "syp", "door")
H.connect("syp", "laz", "slide")
H.connect("syp", "tar", "slide")

H.entrance("hol", "N", at=0.78)
H.exit("biu", "S", at=0.7, width=2.4, kind="slide")

# teren: ścieżka do wejścia od północy; od południa kamienny taras 2,6 m wzdłuż całej szklanej linii
# (koniec patio – harmonijka ogrodu – koniec biura to jedna załamana linia od rogu do rogu)
D = 2.6
T15, T165 = P(R_OUT, A1), P(R_OUT, A0)
n15 = (-math.sin(math.radians(15)), math.cos(math.radians(15)))   # normalna na południe do linii pod kątem 15°
n165 = (math.sin(math.radians(15)), math.cos(math.radians(15)))
H.path(rect(15.5, -5.5, 16.9, 0.7))
H.path(poly(T15, C, T165, (T165[0] + D * n165[0], T165[1] + D * n165[1]),
            (C[0], C[1] + D / math.cos(math.radians(15))), (T15[0] + D * n15[0], T15[1] + D * n15[1])))
H.tree(-2.5, 3.5, "brzoza")
H.tree(27.5, 7.0, "lipa")
H.tree(1.5, 20.0, "klon")
H.tree(24.5, 19.5, "sosna")

H.cut("A–A", (C[0] + 1.2, C[1] - 15.0), (C[0] + 1.2, C[1] + 6.0))
H.cut("B–B", (C[0] - 13.5, C[1] - 2.5), (C[0] + 13.5, C[1] - 2.5))
