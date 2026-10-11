"""P03 · Pierścień (wersja 2) – zamknięty pierścień parteru wokół okrągłego ogrodu z kopułą-migawką,
tarasy-wycinki pierścienia na dachu parteru i łuk modułów piętra od północnego zachodu."""
import math

from silnik import House, sector, circle, poly, pt, arc_pt, arc_angles

CX, CY = 10.0, 10.0
R_IN, R_OUT, R_PAT = 3.6, 7.45, 11.0      # ogród Ø 7,2 m, dom Ø 14,9 m, mur patio
RC0, RC1 = 5.4, 5.7                       # cięciwy dzielące wycinki na część od ogrodu i od zewnątrz
ROT = -22.5                               # obrót całego układu: salon na SSE, taras zachodni na SW


def P(r, a):
    """Punkt na promieniu r pod kątem a (kąty układu, obrócone o ROT)."""
    return pt(CX, CY, r, a + ROT)


def sec(a1, a2, r1=R_IN, r2=R_OUT):
    """Wycinek pierścienia – wszystkie łuki z jednego środka."""
    return sector(CX, CY, r1, r2, a1 + ROT, a2 + ROT)


def arc(r, a1, a2):
    """Punkty łuku (te same wierzchołki co w sector/circle) od kąta a1 do a2."""
    a1, a2 = a1 + ROT, a2 + ROT
    pts = [arc_pt(CX, CY, r, a) for a in arc_angles(min(a1, a2), max(a1, a2))]
    return pts if a1 <= a2 else pts[::-1]


def inner_part(a1, a2, rc, splits=()):
    """Część wycinka od ogrodu, odcięta prostą ścianką (cięciwą) na promieniu rc – daje prostą ścianę na meble."""
    return poly(arc(R_IN, a1, a2) + [P(rc, a) for a in [a2, *reversed(splits), a1]])


def outer_part(a1, a2, rc, splits=()):
    """Część wycinka od zewnątrz – od cięciwy (lub łamanej przez kąty splits) do łuku zewnętrznego."""
    return poly([P(rc, a) for a in [a1, *splits, a2]] + arc(R_OUT, a2, a1))


def D(a):
    """Kierunek elewacji (klucz w ext) w kątach układu."""
    return (a + ROT) % 360


def strip(a, r1, r2, w):
    """Prosta ścieżka wzdłuż promienia a."""
    c1, c2 = P(r1, a), P(r2, a)
    ux, uy = (c2[0] - c1[0]) / (r2 - r1), (c2[1] - c1[1]) / (r2 - r1)
    nx, ny = -uy * w / 2, ux * w / 2
    return poly((c1[0] + nx, c1[1] + ny), (c2[0] + nx, c2[1] + ny), (c2[0] - nx, c2[1] - ny), (c1[0] - nx, c1[1] - ny))


H = House(
    "p03", "Pierścień",
    "Okrągły dom o średnicy 15 m wokół okrągłego ogrodu, którego z zewnątrz nie widać. Na dachu parteru, "
    "po obu stronach szklanej kopuły, leżą dwa tarasy, a od północnego zachodu stoi łuk modułów piętra z sypialnią i biurem.",
    style=dict(fasada="cegla_biala", dach="sedum", akcent="miedz"),
    concept=[
        "Parter to zamknięty pierścień pokoi wokół ogrodu o średnicy 7 m. Od ogrodu pokoje są przeszklone, a od "
        "zewnątrz mają tylko okna i szczeliny, więc ogrodu nie widać ani z drogi, ani od sąsiadów.",
        "Wiatrołap od północnego zachodu nie dotyka ogrodu – oddzielają go od niego WC i pralnia. Ogród widać dopiero "
        "za drugimi drzwiami: w jedną stronę przez bibliotekę i herbaciarnię do salonu, w drugą przez hol ze "
        "schodami do pokoju gościnnego.",
        "Salon z kuchnią zajmuje łuk od wschodu po południowy zachód i ma 6,5 m wysokości: kuchnia z wyspą stoi przy "
        "pełnej ścianie od wschodu, dalej w łuku kanapa i stół. Od ogrodu salon jest ze szkła, a od południa "
        "wychodzi na częściowo zadaszone patio schowane za łukowym murem wysokości 2,6 m.",
        "Na dachu parteru, po obu stronach kopuły, leżą dwa tarasy – wycinki pierścienia: zachodni przy sypialni, "
        "wschodni przy biurze. Najwyższy dach, nad salonem i modułami piętra, jest zielony.",
        "Moduły piętra stoją w łuku od zachodu po północny wschód i łączą się drzwiami w ciąg: sypialnia ze szklaną "
        "ścianą i łazienką, garderoba, galeria ze schodami i biuro przeszklone na pola i na taras.",
        "Kopuła nad ogrodem otwiera się w środku jak migawka aparatu, a z tarasów i z galerii patrzy się na ogród z góry.",
    ],
    notes=dict(
        lato="Środek kopuły rozsuwa się i zostawia okrągły otwór nad stawem, a dom przedłużają patio za murem "
             "i dwa tarasy: wschodni na poranek, zachodni na wieczór.",
        zima="Migawka jest zamknięta, ogród zbiera ciepło słońca i oddaje je pokojom pierścienia, a pełne ściany "
             "zewnętrzne i mur patio osłaniają dom od wiatru.",
        technologia="Ściany z białych bloczków silikatowych na klej, murowane po łuku krótkimi odcinkami; stropy "
                    "i dach z płyt CLT ciętych na wycinki pierścienia, kopuła z segmentów szklanych na stalowym "
                    "ruszcie z otwieraną przesłoną w środku.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

H.ogrod("og", "Ogród", circle(CX, CY, R_IN), roof_type="iris", style="woda", seed=7)

# parter – zamknięty pierścień pokoi wokół ogrodu (ściana kuchni bez drzwi, za nią pokój gościnny)
H.room("sal", "Salon z kuchnią", "salon_kuchnia", sec(30, 150), levels=2, kitchen_at="E",
       ext={"pat": "glass_slide", D(270): "glass", "taE": "windows", "taW": "windows", "*": "windows"})
H.room("pat", "Patio za murem", "patio", sec(50, 130, R_OUT, R_PAT), roof=sec(50, 130, R_OUT, R_OUT + 1.6),
       enclose="gwall", label_at=P(10.15, 90))
H.room("her", "Herbaciarnia", "herbaciarnia", sec(150, 195), ext="windows")
H.room("bib", "Biblioteka", "biblioteka", sec(195, 225), ext="slits")
H.room("wia", "Wiatrołap", "wiatrolap", outer_part(225, 277.5, RC0, splits=(251.25,)), ext="slits")
H.room("wc", "WC", "wc", inner_part(225, 251.25, RC0))
H.room("pral", "Pralnia", "pralnia", inner_part(251.25, 277.5, RC0))
H.room("hol", "Hol ze schodami", "hol", sec(277.5, 330), ext="slits")
H.room("gos", "Pokój gościnny", "gosc", sec(330, 390), ext="windows")
H.stair("spiral", level=0, center=P(6.05, 296.25), r=1.0, start=180 + ROT, sweep=300, n=16)

# piętro – łuk modułów od zachodu po północny wschód, tarasy na dachu parteru po obu stronach kopuły
H.room("taW", "Taras zachodni", "taras", sec(150, 195), level=1)
H.room("syp", "Sypialnia", "sypialnia_glowna", sec(195, 240), level=1,
       ext={"taW": "glass", D(217.5): "glass", "*": "windows"})
H.room("gar", "Garderoba", "garderoba", inner_part(240, 281.25, RC1), level=1, ext="windows")
H.room("laz", "Łazienka", "lazienka", outer_part(240, 281.25, RC1), level=1)
H.room("gal", "Galeria", "galeria", sec(281.25, 311.25), level=1, ext={D(270): "slits", D(90): "glass", "*": "windows"})
H.room("biu", "Biuro", "biuro", sec(311.25, 345), level=1,
       ext={"taE": "glass", D(315): "glass", "*": "windows"})
H.room("taE", "Taras wschodni", "taras", sec(345, 390), level=1)

H.connect("sal", "her", "wide")
H.connect("her", "bib", "door", at=0.85)
H.connect("bib", "wia", "door")
H.connect("wia", "wc", "door", at=0.2)
H.connect("hol", "wia", "door")
H.connect("hol", "pral", "door")
H.connect("hol", "gos", "door", at=0.85)
H.connect("gal", "gar", "door", at=0.85, width=0.8)
H.connect("gar", "syp", "door", at=0.85, width=0.8)
H.connect("syp", "laz", "door")
H.connect("gal", "biu", "door", at=0.85)
H.connect("syp", "taW", "slide", at=0.8)
H.connect("biu", "taE", "slide", at=0.8)
H.entrance("wia", D(250), at=0.78)       # kierunek liczbowo: długi łuk wiatrołapu

ENTRY_A = 267.6                           # oś drzwi wejściowych (kąt układu)
H.path(strip(ENTRY_A, R_OUT - 0.3, R_OUT + 7.0, 1.4))
H.tree(-0.5, 2.0, "brzoza")
H.tree(22.5, 4.5, "lipa")
H.tree(-0.5, 19.0, "klon")
H.cut("A–A", P(R_OUT + 2.0, 296.25), P(R_PAT + 2.0, 116.25))
H.cut("B–B", P(R_OUT + 2.0, 172.5), P(R_OUT + 2.0, 352.5))
