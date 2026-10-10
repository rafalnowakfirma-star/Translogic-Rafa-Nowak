"""P03 · Pierścień – okrągły dom wokół okrągłego ogrodu z kopułą jak migawka aparatu."""
from silnik import House, sector, circle, union

C = (11.0, 11.0)
R_OUT, R_IN, R_MID = 10.0, 4.5, 7.0


def sec(a1, a2, r1=R_IN, r2=R_OUT):
    return sector(C[0], C[1], r1, r2, a1, a2)


H = House(
    "p03", "Pierścień",
    "Okrągły dom, który obchodzi się dookoła jak krużganek. W środku jest okrągły ogród pod szklaną kopułą, której środek otwiera się jak migawka aparatu.",
    style=dict(fasada="cegla_biala", dach="sedum", akcent="miedz"),
    concept=[
        "Pierścień o średnicy 20 m i okrągły ogród o średnicy 9 m. Każdy pokój ma ścianę od ogrodu, więc ogród jest sercem i przedpokojem domu naraz.",
        "Szklana kopuła nad ogrodem ma ruchome segmenty. Latem rozsuwają się promieniście i zostawiają otwarty okulus o średnicy 3 m.",
        "Biuro od zachodu jest przeszklone od strony ogrodu i od strony pola, a przez przesuwne drzwi łączy się z patio.",
        "Od wejścia prowadzą dwie drogi: przez bibliotekę i przelotową garderobę do sypialni albo przez biuro i patio do salonu.",
        "Salon z kuchnią na dwie kondygnacje zajmuje południowy łuk. Jego zakrzywiona szklana ściana działa jak panorama.",
    ],
    notes=dict(
        lato="Środek kopuły rozsuwa się jak migawka i zostawia okrągły otwór nad stawem. Ciepłe powietrze uchodzi górą, a od wody ciągnie chłodem.",
        zima="Migawka jest zamknięta, a woda w stawie oddaje wieczorem ciepło zebrane za dnia. Pokoje dostają światło z dwóch stron.",
        technologia="Ściany z białej cegły silikatowej układane po łuku krótkimi odcinkami, stropy z prefabrykowanych płyt, kopuła z segmentów szklanych na stalowym ruszcie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

H.ogrod("og", "Ogród", circle(C[0], C[1], R_IN), levels=2, roof_type="iris", style="woda", seed=7)
H.room("wia", "Hol wejściowy", "hol", union(sec(250, 275), sec(275, 290, R_MID, R_OUT)), ext="slits")
H.room("wc", "WC", "wc", sec(275, 290, R_IN, R_MID))
H.room("bib", "Biblioteka", "biblioteka", sec(290, 325), ext="band_high")
H.room("gar", "Garderoba", "garderoba", sec(325, 345), ext="band_high")
H.room("syp", "Sypialnia", "sypialnia_glowna", sec(345, 400), ext="glass_slide")
H.room("laz", "Łazienka", "lazienka", sec(40, 65), ext="band_high")
H.room("pral", "Pralnia", "pralnia", sec(65, 78), ext="band_high")
H.room("sal", "Salon z kuchnią", "salon_kuchnia", sec(78, 170), levels=2, ext="glass_slide", kitchen_at="E")
H.room("pat", "Patio", "patio", sec(170, 205), roof=sec(170, 205, R_IN, R_MID))
H.room("biu", "Biuro", "biuro", sec(205, 250), ext="glass_slide")

H.connect("wia", "bib", "wide")
H.connect("wia", "wc", "door")
H.connect("bib", "gar", "door")
H.connect("gar", "syp", "door")
H.connect("syp", "laz", "slide")
H.connect("pral", "sal", "door")
H.connect("sal", "pat", "slide")
H.connect("pat", "biu", "slide")
H.connect("biu", "wia", "double")
H.entrance("wia", "N")
from silnik import rect  # noqa: E402
H.path(rect(10.3, -6, 11.7, 1.2))
H.tree(24.0, 3.0, "brzoza")
H.tree(-2.0, 22.0, "klon")
H.tree(25.0, 21.0, "lipa")
H.cut("A–A", (11.0, -1.0), (11.0, 23.0))
