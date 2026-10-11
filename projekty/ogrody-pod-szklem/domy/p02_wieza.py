"""P02 · Wieża (wersja 2) – zwarty dom wokół oranżerii, wieża z biurem na szczycie, tarasy na dachu parteru."""
from silnik import House, rect, poly

H = House(
    "p02", "Wieża",
    "Zwarty dom 168 m² wokół oranżerii, z wieżą w narożniku, na której szczycie jest biuro przeszklone z trzech stron. "
    "Na dachu parteru, po obu stronach szklanego dachu oranżerii, leżą dwa tarasy, a przy nich salonik w wieży i sypialnia.",
    style=dict(fasada="beton", dach="sedum", akcent="stal"),
    concept=[
        "Biuro na szczycie wieży, 6,8 m nad ziemią, ma szkło od wschodu, południa i zachodu i widok ponad dachami domu, a od północy, od strony drogi, pełną ścianę, przy której stoją schody kręcone.",
        "Wieża 4,2 × 4,2 m jest wysunięta o 0,8 m przed elewacje i mieści wejście; hol w jej podstawie nie ma szkła do ogrodu, więc oranżeria pokazuje się dopiero za drugimi drzwiami.",
        "Oranżeria 5,8 × 5,6 m jest ze wszystkich stron otoczona pokojami, które na zewnątrz mają tylko okna i pasy okien pod sufitem, a duże szkło wyłącznie od ogrodu i od patio za murem, więc ogrodu nie widać z drogi ani od sąsiadów.",
        "Salon z kuchnią jest wysoki na dwie kondygnacje i od południa otwiera się szklaną ścianą na patio za murem wysokości 2,6 m, w połowie zadaszone.",
        "Lamelowy dach oranżerii leży tuż nad dachem parteru, a po jego obu stronach są tarasy: północny przy saloniku w wieży i południowy przy sypialni.",
        "Na piętrze przechodzi się z saloniku przez garderobę do sypialni ze szklaną ścianą od wschodu i do łazienki, a na parterze z holu jedna droga prowadzi przez bibliotekę do salonu, druga przez pracownię i pralnię do pokoju gościnnego.",
    ],
    notes=dict(
        lato="Lamele dachu oranżerii obracają się do pionu i wypuszczają ciepłe powietrze, salon otwiera się na patio za murem, a z obu tarasów patrzy się do oranżerii z góry.",
        zima="Lamele są zamknięte i oranżeria zbiera ciepło słońca dla otaczających ją pokoi, a od północy dom ma tylko wąskie pasy okien i pełną ścianę wieży, które chronią go przed wiatrem.",
        technologia="Wieża jako sztywny trzon z prefabrykatów żelbetowych, pozostałe ściany z bloczków ICF (styropian zalany betonem), stropy i tarasy na prefabrykowanych płytach kanałowych. Dach oranżerii z systemowych lameli szklanych na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)
H.level(2, z=6.8, h=3.6)

# siatka (oś ścian)
XS, XG1, XE = 4.6, 10.4, 13.8                   # salon | oranżeria | pasmo wschodnie
YN, YG1, YS = 3.4, 9.0, 12.6                    # pasmo północne | oranżeria | pasmo południowe
TX0, TX1, TY0, TY1 = 10.4, 14.6, -0.8, 3.4      # wieża 4,2 × 4,2 m, wysunięta 0,8 m na północ i wschód
SC = (11.7, 0.5)                                # schody kręcone w narożniku NW wieży (na każdym poziomie)

H.ogrod("og", "Oranżeria", rect(XS, YN, XG1, YG1), roof_type="louvre", style="oranzeria", seed=5)

# parter – pierścień pokoi wokół oranżerii
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(0, 0, XS, YG1), levels=2, kitchen_at="N",
       ext={"pat": "glass_slide", "N": "band_high", "*": "windows"})
H.room("bib", "Biblioteka", "biblioteka", rect(XS, 0, XG1, YN), ext="band_high")
H.room("hol", "Hol w wieży", "hol", poly((TX0, TY0), (TX1, TY0), (TX1, 1.7), (13.0, 1.7), (13.0, TY1), (TX0, TY1)),
       ext={"N": "solid", "*": "band_high"})
H.room("wc", "WC", "wc", rect(13.0, 1.7, TX1, TY1), label_at=(13.62, 2.95))
H.room("pra", "Pracownia", "pracownia", rect(XG1, YN, XE, YG1), ext="band_high")
H.room("pral", "Pralnia", "pralnia", rect(XG1, YG1, XE, YS))
H.room("gos", "Pokój gościnny", "gosc", rect(XS, YG1, XG1, YS), ext={"pat": "glass_slide", "*": "band_high"})
H.room("pat", "Patio za murem", "patio", rect(-1.4, YG1, XS, YS), roof=rect(-1.4, YG1, XS, 10.8), enclose="gwall",
       label_at=(2.9, 11.7))
H.stair("spiral", level=0, center=SC, r=1.0, start=90, sweep=300, n=16)

# piętro – salonik w wieży, moduły sypialni od wschodu, tarasy po obu stronach dachu oranżerii
H.room("sln", "Salonik", "salon", rect(TX0, TY0, TX1, TY1), level=1, ext={"E": "band_high", "*": "solid"})
H.stair("spiral", level=1, center=SC, r=1.0, start=90, sweep=300, n=16)
H.room("gar", "Garderoba", "garderoba", rect(XG1, YN, XE, 6.0), level=1)
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(XG1, 6.0, XE, 10.6), level=1, ext={"E": "glass", "*": "solid"})
H.room("laz", "Łazienka", "lazienka", rect(XG1, 10.6, XE, YS), level=1, ext="windows_sq")
H.room("taN", "Taras północny", "taras", rect(XS, 0, XG1, YN), level=1)
H.room("taS", "Taras południowy", "taras", rect(XS, YG1, XG1, YS), level=1)

# szczyt wieży – biuro
H.room("biu", "Biuro", "biuro", rect(TX0, TY0, TX1, TY1), level=2, ext={"N": "solid", "*": "glass"})

H.connect("hol", "bib", "door", at=0.75)
H.connect("bib", "sal", "wide")
H.connect("wc", "hol", "door", at=0.8)
H.connect("hol", "pra", "door", at=0.3)
H.connect("pra", "pral", "door", at=0.85)
H.connect("pral", "gos", "door", at=0.8)
H.connect("gos", "pat", "slide")
H.connect("sal", "pat", "slide")
H.connect("sln", "taN", "slide", at=0.25)
H.connect("sln", "gar", "door", at=0.5)
H.connect("gar", "syp", "door", at=0.15)
H.connect("syp", "laz", "door", at=0.85)
H.connect("syp", "taS", "slide", at=0.0)
H.entrance("hol", "N", at=0.7)
H.exit("pral", "E", kind="door", width=0.9)
H.path(rect(12.6, -6, 14.0, -1.0))
H.tree(-3.5, 3.0, "brzoza")
H.tree(18.0, 12.0, "klon")
H.tree(17.5, -3.5, "lipa")
H.cut("A–A", (-3.0, 6.2), (17.0, 6.2))
H.cut("B–B", (12.0, -3.5), (12.0, 15.0))
