"""P13 · Kubik – zwarta kostka 12,8 × 13,1 m z atrium 5,6 × 5,6 m przez dwie kondygnacje pod lamelowym dachem."""
from silnik import House, rect, poly

# siatka: pasma W | atrium | E = 3,6 | 5,6 | 3,6 m (x), N | atrium | S = 3,3 | 5,6 | 4,2 m (y)
XW, XE, XX = 3.6, 9.2, 12.8
YN, YS, YY = 3.3, 8.9, 13.1

H = House(
    "p13", "Kubik",
    "Najmniejszy dom kolekcji: kostka 12,8 × 13,1 m na dwie kondygnacje z atrium 5,6 × 5,6 m w samym środku. "
    "Z kostki wycięto trzy kawałki: podcień przy wejściu, patio sezonowe w narożniku i taras nad nim.",
    style=dict(fasada="blacha", dach="sedum", akcent="modrzew"),
    concept=[
        "Atrium 5,6 × 5,6 m przechodzi przez obie kondygnacje i ma dach z obrotowych szklanych lameli; wokół niego biegnie pierścień pokoi o głębokości 3,3–4,2 m, więc dom nie potrzebuje korytarzy.",
        "Biuro zajmuje zachodnie pasmo piętra: od wschodu patrzy przez szkło w koronę klonu w atrium, od zachodu przez szklaną ścianę na pola, a na południu wychodzi na taras nad patio.",
        "Parter obchodzi się amfiladą: z wiatrołapu w jedną stronę do holu ze schodami i pokoju gościnnego, w drugą przez bibliotekę na patio i do salonu, a z kuchni przez spiżarnię-kredens do pralni. Zimą z holu do salonu przechodzi się przez atrium.",
        "Salon z kuchnią ma 6,1 m wysokości i zajmuje południowe pasmo; na zachodzie otwiera się szklaną ścianą na patio sezonowe wycięte z narożnika bryły – zimą zamknięte szklaną harmonijką, latem całkiem otwarte.",
        "Schody proste biegną w holu wzdłuż północnej ściany i wychodzą na galerię, która ciągnie się przez całą szerokość domu wzdłuż szkła atrium; z niej wchodzi się do biura i – przez przelotową garderobę – do sypialni.",
        "Sypialnia na piętrze ma całą wschodnią ścianę ze szkła, a od atrium tylko wysokie pasmo okien, żeby biuro po drugiej stronie ogrodu nie zaglądało do łóżka; wezgłowie stoi przy ścianie wysokiego salonu.",
    ],
    notes=dict(
        lato="Lamele nad atrium stają pionowo, harmonijka patio się składa i dom przewietrza się na przestrzał: od patio przez salon i atrium do holu.",
        zima="Lamele są zamknięte, patio zamknięte szkłem działa jak oranżeria, a atrium jako nasłoneczniony bufor, przez który przechodzi się z holu do salonu.",
        technologia="Cztery moduły przestrzenne z fabryki (szkielet stalowy, ściany z płyt warstwowych) ustawione wokół atrium i skręcone na budowie; alternatywnie bloczki ICF ze stropami z płyt kanałowych. Elewacja z ciemnej blachy na rąbek stojący.",
    ),
)
H.level(0, z=0.0, h=3.2)
H.level(1, z=3.2, h=3.2)

H.ogrod("og", "Atrium", rect(XW, YN, XE, YS), levels=2, roof_type="louvre", style="japonski", seed=13)

# ---------------------------------------------------------------- parter
H.room("pod", "Podcień", "loggia", rect(0, 0, 2.4, 1.3), furn=False, label_at=(1.2, 1.0))
H.room("wc", "WC", "wc", rect(2.4, 0, XW, 1.9))
H.room("wia", "Wiatrołap", "wiatrolap", poly((0, 1.3), (2.4, 1.3), (2.4, 1.9), (XW, 1.9), (XW, YN), (0, YN)),
       ext={"W": "slits", "N": "solid"})
H.room("hol", "Hol", "hol", rect(XW, 0, XE, YN), ext={"N": "slits"})
H.stair("straight", level=0, rect=(3.7, 0.25, 8.7, 1.35), up="W")
H.room("gos", "Pokój gościnny", "gosc", rect(XE, 0, XX, YN), ext={"N": "solid", "E": "windows"})
H.room("pral", "Pralnia", "pralnia", rect(XE, YN, XX, 6.1), ext={"E": "windows_sq"}, garden="band_high")
H.room("spi", "Spiżarnia-kredens", "spizarnia", rect(XE, 6.1, XX, YS), ext={"E": "windows_sq"})
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(XW, YS, XX, YY), levels=2,
       ext={"S": "glass", "E": "solid", "W": "glass_slide"}, garden="glass", kitchen_at="E")
H.room("pat", "Patio sezonowe", "patio_sezonowe", rect(0, YS, XW, YY))
H.room("bib", "Biblioteka", "biblioteka", rect(0, YN, XW, YS), ext={"W": "solid", "S": "glass_slide"})

H.connect("wia", "hol", "door")
H.connect("wia", "wc", "door")
H.connect("wia", "bib", "door", at=0.85)
H.connect("hol", "gos", "door", at=0.7)
H.connect("sal", "og", "slide", at=0.85)
H.connect("sal", "spi", "door", at=0.2)
H.connect("spi", "pral", "door")
H.entrance("wia", "N")
H.exit("sal", "S", kind="slide", at=0.6)
H.window("bib", "W", at=0.85, width=1.2, sill=0.6, head=2.5)

# ---------------------------------------------------------------- piętro
H.room("gal", "Galeria", "galeria", rect(0, 0, XE, YN), level=1, ext={"N": "slits", "W": "solid"}, garden="glass")
H.room("gar", "Garderoba", "garderoba", rect(XE, 0, 11.0, YN), level=1)
H.room("laz", "Łazienka", "lazienka", rect(11.0, 0, XX, YN), level=1, ext={"N": "band_high", "E": "solid"})
H.room("biu", "Biuro", "biuro", rect(0, YN, XW, YS), level=1, ext={"W": "glass", "S": "glass_slide"}, garden="glass")
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(XE, YN, XX, YS), level=1,
       ext={"E": "glass"}, garden="band_high")
H.room("tar", "Taras", "taras", rect(0, YS, XW, YY), level=1)

H.connect("gal", "biu", "door", at=0.3)
H.connect("gal", "gar", "door", at=0.7)
H.connect("gar", "syp", "door")
H.connect("syp", "laz", "door")

# ---------------------------------------------------------------- teren
H.path(rect(0.6, -6.0, 1.8, 0.0))
H.path(rect(-3.6, 9.4, -0.2, YY))
H.tree(-4.5, 15.0, "klon")
H.tree(16.0, 2.0, "brzoza")
H.tree(15.5, 15.0, "sosna")
H.cut("A–A", (6.4, -2.0), (6.4, 15.0))
H.cut("B–B", (-2.0, 6.0), (15.0, 6.0))
