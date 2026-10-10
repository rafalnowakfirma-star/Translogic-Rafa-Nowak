"""P11 · Półksiężyc – ceglany półksiężyc na dwie kondygnacje obejmuje półkolisty ogród pod składanym szklanym dachem."""
from silnik import House, sector, rect, union

# wspólny środek wszystkich łuków: pokoje w pierścieniu 5,5–12 m, ogród w półkolu w środku
C = (12.0, 12.0)
R_IN, R_OUT = 5.5, 12.0     # pierścień pokoi
R_N = 8.0                   # głębokość nisz (WC, pralnia) w holu
R_M = 8.5                   # podział piętra na pas wewnętrzny / zewnętrzny
A0, A1 = 165, 375           # łuk półksiężyca: od rogu SW przez północ do rogu SE (90 = S, 270 = N)


def sec(a1, a2, r1=R_IN, r2=R_OUT):
    return sector(C[0], C[1], r1, r2, a1, a2)


H = House(
    "p11", "Półksiężyc",
    "Dom jak półksiężyc z cegły, na dwie kondygnacje, obejmuje półkolisty ogród pod składanym szklanym dachem. "
    "Od południa ogród zamyka szklana harmonijka: zimą jest oranżerią, latem otwartym dziedzińcem, który przechodzi w łąkę.",
    style=dict(fasada="cegla", dach="sedum", akcent="stal"),
    concept=[
        "Pokoje leżą w pierścieniu o promieniach 5,5–12 m na łuku 210°, a ogród wypełnia półkole w środku. Wypukła, północna strona domu jest z cegły z nielicznymi oknami, wklęsła strona od ogrodu jest cała ze szkła.",
        "Biuro zajmuje wschodni róg półksiężyca i ma szkło z trzech stron: od ogrodu, od wschodnich pól i od południa, gdzie przesuwne drzwi wychodzą na kamienny taras przed domem.",
        "Po łuku idzie się z pokoju do pokoju, bez korytarzy: z patio przez salon, hol ze schodami, bibliotekę i herbaciarnię do biura. WC i pralnia to dwie nisze holu od strony ogrodu, więc hol wzdłuż szkła zostaje wolny.",
        "Salon z kuchnią przy zachodnim rogu ma dwie kondygnacje i szklaną ścianę do ogrodu na całą wysokość. Za szklaną harmonijką jest zadaszone patio sezonowe na samym końcu rogu: zimą zamknięte szkłem, latem otwarte z trzech stron.",
        "Piętro zajmuje północno-wschodnią część łuku: pracownia nad holem, przelotowa garderoba, łazienka i sypialnia ze szklanymi ścianami od wschodu i w stronę ogrodu, z której wychodzi się na taras na dachu biura.",
        "Dach ogrodu to szklana harmonijka na wysokości 3,75 m, czyli tuż nad podłogą piętra. Z sypialni i pracowni patrzy się ponad nim na południową łąkę, a latem, gdy jest złożony, w dół na drzewa w ogrodzie.",
    ],
    notes=dict(
        lato="Harmonijka od południa i szklany dach ogrodu składają się, patio otwiera się z trzech stron i ogród staje się dziedzińcem przechodzącym w łąkę; ceglana ściana od północy trzyma chłód.",
        zima="Ogród jest zamkniętą oranżerią z oliwką i lawendą w donicach; zbiera niskie słońce z południa i ogrzewa wklęsłą, szklaną stronę domu, a cegła od północy osłania od wiatru.",
        technologia="Ściany z ceramicznych pustaków szlifowanych na cienką spoinę, łuk murowany z krótkich prostych odcinków co 7,5°; stropy z prefabrykowanych płyt kanałowych, harmonijki ścian i dach szklany systemowe, na stalowych ramach.",
    ),
)
H.level(0, z=0.0, h=3.5)
H.level(1, z=3.5, h=3.3)

# ogród: półkole z lekkim załamaniem od południa, zamknięte harmonijką
H.ogrod("og", "Ogród", sec(A0, A1, 0.0, R_IN), levels=1, roof_type="fold", style="srodziemnomorski", edge="fold", seed=11)

# ---- parter, po łuku od rogu zachodniego do wschodniego
H.room("pat", "Patio sezonowe", "patio_sezonowe", sec(A0, 195))
H.room("sal", "Salon z kuchnią", "salon_kuchnia", sec(195, 255), levels=2,
       ext={"SE": "glass", "S": "glass", "*": "windows"}, kitchen_at="N")
H.room("hol", "Hol", "hol", union(sec(255, 295, R_N, R_OUT), sec(255, 270, R_IN, R_N)), ext="slits")
H.room("pral", "Pralnia", "pralnia", sec(270, 285, R_IN, R_N), garden="band_high")
H.room("wc", "WC", "wc", sec(285, 295, R_IN, R_N))
H.room("bib", "Biblioteka", "biblioteka", sec(295, 320), ext="band_high")
H.room("her", "Herbaciarnia", "herbaciarnia", sec(320, 342.5), ext="slits")
H.room("biu", "Biuro", "biuro", sec(342.5, A1), ext={"E": "glass", "S": "glass"}, garden="glass_slide")

# ---- piętro nad północno-wschodnią częścią łuku
H.room("pra", "Pracownia", "pracownia", sec(255, 295), level=1, ext={"N": "windows", "S": "glass"})
H.room("gar", "Garderoba", "garderoba", sec(295, 317.5, R_IN, R_M), level=1)
H.room("laz", "Łazienka", "lazienka", sec(295, 317.5, R_M, R_OUT), level=1)
H.room("syp", "Sypialnia", "sypialnia_glowna", sec(317.5, 350), level=1, ext="glass")
H.room("tar", "Taras", "taras", sec(350, A1), level=1)

# schody dwubiegowe wzdłuż północnej ściany holu, wejście na piętro do pracowni
H.stair("U", level=0, rect=(C[0] - 1.9, C[1] - 11.4, C[0] + 1.9, C[1] - 9.1), up="W")

# ---- połączenia: amfilada parteru
H.connect("sal", "pat", "fold")
H.connect("pat", "og", "slide")
H.connect("sal", "hol", "wide", at=0.45)
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

H.entrance("hol", "N", at=0.8)
H.exit("biu", "S", at=0.7, width=2.4, kind="slide")

# teren: ścieżka do wejścia od północy, kamienny taras przed harmonijką od południa
H.path(rect(14.9, -5.5, 16.3, 0.6))
H.path(sec(15, 165, 0.0, 9.0))
H.tree(-2.5, 3.5, "brzoza")
H.tree(27.5, 7.0, "lipa")
H.tree(1.5, 20.0, "klon")
H.tree(24.5, 19.5, "sosna")

H.cut("A–A", (C[0] - 0.6, C[1] - 15.0), (C[0] - 0.6, C[1] + 6.0))
H.cut("B–B", (C[0] - 15.0, C[1] - 2.5), (C[0] + 15.0, C[1] - 2.5))
