"""P17 · Refektarz (wersja 2) – zwarty kwadrat jak klasztorny wirydarz: w środku ogród zimowy z długim stołem
pod szklaną piramidą, kuchnia z harmonijką od wschodu, wysoki salon od południa, moduły piętra od północy."""
from silnik import House, rect, poly

# siatka: pasma W | ogród | E = 3,6 | 5,6 | 4,2 m (x), N | ogród | S = 4,0 | 5,6 | 3,8 m (y) – kwadrat 13,4 × 13,4 m
XW, XE, XX = 3.6, 9.2, 13.4
YN, YS, YY = 4.0, 9.6, 13.4
XS = 11.2    # granica spiżarni i pralni (pas północny)
YK = 4.6     # spiżarnia i pralnia sięgają głębiej niż pas północny – kuchnia (i harmonijka) zaczyna się 0,6 m niżej
XH = 6.1     # koniec holu na piętrze
YL = 2.0     # granica garderoby i łazienki (piętro)

H = House(
    "p17", "Refektarz",
    "Szkic.",
    style=dict(fasada="cegla_biala", dach="sedum", akcent="dab"),
    concept=["Szkic."],
    notes=dict(lato="-", zima="-", technologia="-"),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

H.ogrod("og", "Ogród zimowy z jadalnią", rect(XW, YN, XE, YS), levels=1, roof_type="pyramid", style="jadalnia", seed=13,
        label_at=(6.5, 4.47))

# ---------------------------------------------------------------- parter
H.room("wc", "WC", "wc", rect(0, 2.2, 1.6, YN), ext="band_high", label_at=(1.0, 3.5))
H.room("wia", "Wiatrołap", "wiatrolap", poly((0, 0), (XW, 0), (XW, YN), (1.6, YN), (1.6, 2.2), (0, 2.2)),
       ext={"N": "slits", "W": "solid"})
H.room("bib", "Biblioteka", "biblioteka", rect(XW, 0, XE, YN), ext="band_high", garden="glass", label_at=(7.05, 3.25))
H.stair("spiral", level=0, center=(4.8, 2.7), r=1.0, start=330, sweep=300, n=16)
H.room("spi", "Spiżarnia", "spizarnia", rect(XE, 0, XS, YK), ext="band_high", label_at=(10.2, 3.95))
H.room("pral", "Pralnia", "pralnia", rect(XS, 0, XX, YK), ext={"N": "band_high", "E": "windows_sq"})
H.room("gos", "Pokój gościnny", "gosc", rect(0, YN, XW, YS), ext={"W": "windows", "pat": "glass_slide"}, garden="windows")
H.room("kuch", "Kuchnia", "kuchnia", rect(XE, YK, XX, YS), ext="band_high", garden="fold", kitchen_at="N")
H.room("sal", "Salon", "salon", rect(XW, YS, XX, YY), levels=2,
       ext={"pat": "glass_slide", "taE": "band_high", "S": "slits", "E": "solid", "N": "glass", "W": "glass"})
H.room("pat", "Patio za murem", "patio", rect(0, YS, XW, YY), roof=rect(2.2, YS, XW, YY), enclose="gwall")

H.connect("wia", "bib", "door", at=0.2)
H.connect("wc", "wia", "door", at=0.8)
H.connect("wia", "gos", "door")
H.connect("spi", "bib", "door", at=0.8)
H.connect("spi", "kuch", "door")
H.connect("pral", "kuch", "door", at=0.2)
H.connect("kuch", "sal", "wide", at=0.7)
H.entrance("wia", "N", at=0.6)
H.exit("pral", "E", kind="door", width=0.9)

# ---------------------------------------------------------------- piętro: moduły od północy, tarasy po bokach piramidy
H.room("biu", "Biuro", "biuro", rect(0, 0, XW, YN), level=1, ext={"N": "glass", "W": "glass", "taW": "glass"})
H.room("hol", "Hol", "hol", rect(XW, 0, XH, YN), level=1, ext={"N": "slits", "S": "glass"})
H.room("gar", "Garderoba", "garderoba", rect(XH, 0, XE, YL), level=1, ext="band_high")
H.room("laz", "Łazienka", "lazienka", rect(XH, YL, XE, YN), level=1, ext="band_high")
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(XE, 0, XX, YN), level=1, ext={"E": "glass", "N": "band_high", "taE": "glass"})
H.room("taW", "Taras zachodni", "taras", rect(0, YN, XW, YS), level=1)
H.room("taE", "Taras wschodni", "taras", rect(XE, YN, XX, YS), level=1)

H.connect("hol", "biu", "door", at=0.2)
H.connect("hol", "gar", "door", at=0.9)
H.connect("gar", "laz", "slide", width=0.9)
H.connect("gar", "syp", "door", at=0.9)
H.connect("biu", "taW", "slide")
H.connect("syp", "taE", "slide")

# ---------------------------------------------------------------- teren
H.path(rect(1.5, -6.0, 2.8, -0.2))
H.path(rect(XX + 0.2, 1.65, XX + 1.4, 2.95))
H.tree(-4.0, 6.5, "brzoza")
H.tree(17.5, 12.0, "lipa")
H.tree(17.0, -2.5, "klon")
H.cut("A–A", (5.6, -2.0), (5.6, 16.0))
H.cut("B–B", (-2.0, 6.8), (16.0, 6.8))
