"""P12 · Oktagon (wersja 2) – miedziany ośmiobok wokół ukrytej oranżerii pod szklaną piramidą,
tarasy na dachu parteru, korona trzech modułów piętra od północy."""
import math

from silnik import House, rect, poly, pt, ngon, ngon_band, ngon_vertex

# Ośmiobok o płaskich bokach na osiach świata (rot=0): bok 0 E, 1 SE, 2 S, 3 SW, 4 W, 5 NW, 6 N, 7 NE.
CX, CY = 10.0, 10.0
A_IN = 3.6       # apotema oranżerii
A_OUT = 7.0      # apotema parteru (pierścień głębokości 3,4 m)
A_UP = 8.4       # apotema modułów piętra – wysunięte 1,4 m poza parter
A_PAT = 11.0     # patio za murem przed salonem


def seg(k, a1=A_IN, a2=A_OUT, span=1):
    """Segment pierścienia na boku k (pas ośmioboku między apotemami a1 i a2)."""
    return ngon_band(CX, CY, 8, a1, a2, k, span)


def V(a, k):
    """Wierzchołek między bokami k i k+1 na apotemie a (punkt na ścianie promienistej)."""
    return ngon_vertex(CX, CY, 8, a, k)


def L(k, u, a):
    """Punkt w układzie boku k: a – odległość od środka wzdłuż normalnej boku,
    u – przesunięcie wzdłuż boku (dodatnie w stronę wierzchołka k)."""
    th = math.radians(45 * k)
    return (CX + a * math.cos(th) - u * math.sin(th), CY + a * math.sin(th) + u * math.cos(th))


H = House(
    "p12", "Oktagon",
    "Ośmiokątny dom w patynowanej miedzi, który chowa w środku oranżerię pod szklaną piramidą. "
    "Na dachu parteru są dwa tarasy, a od północy stoi korona trzech modułów piętra.",
    style=dict(fasada="miedz", dach="sedum"),
    concept=[
        "Osiem segmentów parteru tworzy pierścień szeroki na 14 m i głęboki na 3,4 m, który zamyka oranżerię 41 m² "
        "ze wszystkich stron. Od zewnątrz parter ma pełne miedziane ściany, głównie z oknami pod sufitem, "
        "więc ogrodu nie widać ani z drogi, ani od sąsiadów.",
        "Wejście leży na osi północnej, pod wysuniętą koroną piętra. W sieni stoją kręcone schody przed pełną "
        "ścianą, a ogród otwiera się dopiero w kolejnych pokojach.",
        "Parter obchodzi się dookoła bez korytarzy: sień, pralnia ze spiżarnią, kuchnia, jadalnia, salon, "
        "sala muzyczna, galeria, pracownia i z powrotem sień; WC jest tuż przy wejściu.",
        "Salon w segmencie południowym ma 6,8 m wysokości i łączy się bez ścian z jadalnią i kuchnią. "
        "Szklanymi drzwiami wychodzi na patio za murem wysokości 2,6 m, zadaszone przy domu.",
        "Dachy czterech segmentów parteru, po dwa z obu stron salonu, to tarasy wokół szklanej piramidy. "
        "Trzy segmenty północne niosą moduły piętra wysunięte 1,4 m poza parter, a pod nimi jest podcień nad wejściem.",
        "Moduły łączą się drzwiami w ciąg: biuro przeszklone na północny zachód i na taras zachodni, biblioteka "
        "ze schodami, ścianą książek i szkłem na piramidę, sypialnia ze szklaną ścianą na północny wschód, "
        "wyjściem na taras wschodni i łazienką za wezgłowiem.",
    ],
    notes=dict(
        lato="Latarnia na szczycie piramidy unosi się i wyciąga ciepłe powietrze z oranżerii, a salon, biuro "
             "i sypialnia otwierają się szklanymi drzwiami na patio za murem i na tarasy.",
        zima="Latarnia jest opuszczona, oranżeria zbiera słońce przez piramidę i oddaje ciepło pokojom pierścienia, "
             "a pełne miedziane ściany parteru chronią dom od zewnątrz.",
        technologia="Stalowy szkielet ze słupami w narożnikach ośmioboku i prefabrykowane panele ścienne (rama "
                    "stalowa z wełną mineralną) obłożone patynowaną blachą miedzianą. Stropy i wspornikowe moduły "
                    "piętra z płyt CLT, tarasy z deski na warstwie spadkowej, piramida ze stalowych żeber i szkła "
                    "zespolonego.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

H.ogrod("og", "Oranżeria", ngon(CX, CY, 8, A_IN), roof_type="pyramid", style="oranzeria", seed=15)

# ---------------------------------------------------------------- parter
# N – sień: wejście na osi, kręcone schody przed pełną ścianą, za którą jest ogród
H.room("hol", "Sień", "wiatrolap", seg(6), ext="solid", garden="solid")
H.stair("spiral", level=0, center=(CX, 5.15), r=0.9, start=300, sweep=300, n=17)
# NW – WC przy sieni i pracownia
U_WC, D_WC = 0.6, 1.7
H.room("wc", "WC", "wc", poly(L(5, U_WC, A_OUT), V(A_OUT, 5), V(A_OUT - D_WC, 5), L(5, U_WC, A_OUT - D_WC)))
H.room("pra", "Pracownia", "pracownia",
       poly(V(A_OUT, 4), L(5, U_WC, A_OUT), L(5, U_WC, A_OUT - D_WC), V(A_OUT - D_WC, 5), V(A_IN, 5), V(A_IN, 4)),
       ext="band_high")
# W – galeria, SW – sala muzyczna
H.room("gal", "Galeria", "galeria", seg(4), ext="band_high", garden="windows", label_at=(4.1, 11.45))
H.room("muz", "Sala muzyczna", "muzyczny", seg(3), ext="band_high", garden="glass", label_at=(4.95, 13.07))
# S – salon na dwie kondygnacje, przed nim patio za murem
H.room("sal", "Salon", "salon", seg(2), levels=2,
       ext={"pat": "glass_slide", "N": "glass", "S": "windows", "*": "solid"})
H.room("pat", "Patio za murem", "patio", seg(2, A_OUT, A_PAT), roof=seg(2, A_OUT, A_OUT + 2.4), enclose="gwall",
       label_at=(CX + 2.5, CY + 10.15))
# SE – jadalnia, E – kuchnia (otwarte na salon)
H.room("jad", "Jadalnia", "jadalnia", seg(1), ext="windows")
H.room("kuch", "Kuchnia", "kuchnia", seg(0), ext="band_high", garden="glass_slide", kitchen_at="N")
# NE – pralnia ze spiżarnią i wyjściem gospodarczym
H.room("pral", "Pralnia i spiżarnia", "pralnia", seg(7), ext="band_high", garden="band_high")
# podcień pod wysuniętą koroną piętra (otwarty, z kamienną posadzką) – osłania wejście i wyjście gospodarcze
H.room("pod", "Podcień", "patio", seg(5, A_OUT, A_UP, span=3), floor="kamien", furn=False)

# ---------------------------------------------------------------- piętro: korona modułów od północy
# NE – sypialnia, za wezgłowiem łazienka od strony piramidy; NW – biuro; N – biblioteka nad sienią
A_B = 5.4        # podział modułu NE: łazienka (od piramidy) / sypialnia (od krajobrazu)
H.room("laz", "Łazienka", "lazienka", seg(7, A_IN, A_B), level=1, ext="band_high", label_at=(13.55, 7.15))
H.room("syp", "Sypialnia", "sypialnia_glowna", seg(7, A_B, A_UP), level=1,
       ext={"NE": "glass", "taE": "glass", "*": "solid"})
H.room("bib", "Biblioteka", "biblioteka", seg(6, A_IN, A_UP), level=1, ext={"N": "solid", "S": "glass", "*": "solid"})
H.room("biu", "Biuro", "biuro", seg(5, A_IN, A_UP), level=1, ext={"NW": "glass", "taW": "glass", "*": "solid"})
H.room("taW", "Taras zachodni", "taras", seg(3, span=2), level=1)
H.room("taE", "Taras wschodni", "taras", seg(0, span=2), level=1)

# ---------------------------------------------------------------- połączenia
H.connect("hol", "wc", "door")
H.connect("hol", "pra", "door", at=0.3)
H.connect("pra", "gal", "door")
H.connect("gal", "muz", "door", at=0.25)
H.connect("muz", "sal", "wide")
H.connect("sal", "jad", "open")
H.connect("jad", "kuch", "open")
H.connect("kuch", "pral", "door")
H.connect("pral", "hol", "door", at=0.8)
H.connect("bib", "syp", "door", at=0.85)
H.connect("syp", "laz", "door", at=0.12)
H.connect("bib", "biu", "door", at=0.85)
H.connect("syp", "taE", "slide", at=0.5)
H.connect("biu", "taW", "slide", at=0.5)

H.entrance("hol", "N")
H.window("hol", "N", at=0.12, width=0.45, sill=0.1, head=2.6)
H.window("hol", "N", at=0.88, width=0.45, sill=0.1, head=2.6)
H.exit("pral", "NE", kind="door", width=0.9)

# ---------------------------------------------------------------- teren
H.path(rect(CX - 0.7, -6.0, CX + 0.7, CY - A_UP))
H.tree(13.5, -4.5, "brzoza")
H.tree(24.0, 3.0, "lipa")
H.tree(23.0, 21.0, "klon")
H.tree(-5.0, 7.5, "sosna")
H.cut("A–A", (CX + 0.4, -2.0), (CX + 0.4, 23.0))
H.cut("B–B", pt(CX, CY, A_OUT + 2.0, 135), pt(CX, CY, A_UP + 2.0, 315))
