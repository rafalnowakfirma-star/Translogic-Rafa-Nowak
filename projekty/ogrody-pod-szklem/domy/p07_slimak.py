"""P07 · Ślimak (wersja 2) – bryła wznosi się spiralnie wokół ukrytego ogrodu: 1, 2 i 3 kondygnacje.
Dachy niższych skrzydeł są tarasami połączonymi schodami zewnętrznymi, najwyższy dach (nad biurem) jest zielony."""
from silnik import House, rect

# osie: zachód 0 | ogród XA–XB | wschód XC ;  północ 0 | ogród YA–YB | południe YC
XA, XB, XC = 3.4, 9.2, 12.0
YA, YB, YC = 4.6, 10.2, 13.4
YH = 2.6     # wiatrołap i WC / hol
YT = 7.0     # koniec holu (parter) i biblioteki (piętro)
YS = 11.6    # sypialnia / łazienka na piętrze
YO = 6.0     # koniec biura na II piętrze
SC = (1.3, 4.7)   # oś schodów kręconych (parter → piętro → II piętro)
DZ = 0.03    # deska tarasów na piętrach 3 cm nad stropem (inaczej w renderze migoczą)

H = House(
    "p07", "Ślimak",
    "Dom o powierzchni 165 m² wokół ogrodu, którego nie widać z zewnątrz. Bryła wznosi się spiralnie – jedna, "
    "dwie i trzy kondygnacje – a dachy niższych skrzydeł są tarasami połączonymi schodami zewnętrznymi.",
    style=dict(fasada="beton", dach="sedum"),
    concept=[
        "Ogród 5,8 × 5,6 m jest ze wszystkich stron otoczony pokojami, a parter od zewnątrz ma tylko szczeliny, "
        "wysokie pasma i pojedyncze okna, więc ogrodu nie widać ani z drogi, ani od sąsiadów.",
        "Skrzydła południowe i wschodnie mają jedną kondygnację, zachodnie dwie, a narożnik północno-zachodni trzy, "
        "dzięki czemu zimowe słońce wpada nad niskimi skrzydłami do ogrodu, a najwyższa część osłania go od północy.",
        "Dachy niższych skrzydeł są tarasami: na +3,4 m od południa i wschodu oraz na +6,6 m nad skrzydłem zachodnim; "
        "schody zewnętrzne prowadzą z patio na taras wschodni i z tarasu południowego na zachodni, a najwyższy dach nad biurem jest zielony.",
        "Na piętrze moduły stoją w ciągu przy tarasie: biblioteka przy schodach ze szklaną ścianą do salonu, sypialnia "
        "z przeszkloną ścianą od zachodu i wyjściem na taras oraz łazienka; poziom wyżej jest biuro przeszklone na zachód i na taras.",
        "Wiatrołap w narożniku nie styka się z ogrodem, który widać dopiero z holu ze schodami kręconymi; dalej parter "
        "obchodzi się przez galerię, herbaciarnię i pralnię albo przez salon do pokoju gościnnego.",
        "Salon z kuchnią ma 6,3 m wysokości i górne przeszklenie nad szklanym dachem ogrodu, a od wschodu wychodzi "
        "na częściowo zadaszone patio za murem wysokości 2,6 m.",
    ],
    notes=dict(
        lato="Lamele nad ogrodem obracają się do pionu i ogród staje się otwartym dziedzińcem, tarasy na dachach służą jako letnie pokoje, a patio za murem przedłuża salon.",
        zima="Lamele są zamknięte, ogród zbiera słońce wpadające nad niskim skrzydłem południowym i ogrzewa sąsiednie pokoje, a trzykondygnacyjny narożnik osłania dom od północnego zachodu.",
        technologia="Ściany z bloczków ICF (styropian zalewany betonem) obłożone od zewnątrz płytami z betonu architektonicznego, stropy i płyty tarasów z prefabrykowanych płyt kanałowych z warstwą spadkową. Schody zewnętrzne to drewniane stopnie na stalowej belce, a dach ogrodu to systemowe lamele szklane na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)
H.level(2, z=6.6, h=3.2)

H.ogrod("og", "Ogród", rect(XA, YA, XB, YB), roof_type="louvre", style="japonski", seed=4)

# ---------------------------------------------------------------- parter
H.room("wia", "Wiatrołap", "wiatrolap", rect(0, 0, 2.1, YH), ext="solid")
H.room("wc", "WC", "wc", rect(2.1, 0, XA, YH), ext="band_high")
H.room("hol", "Hol", "hol", rect(0, YH, XA, YT), ext="slits", furn=False)
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(XA, 0, XC, YA), levels=2, kitchen_at="W",
       ext={"pat": "glass_slide", "N": "band", "S": "glass", "E": "windows"})
H.room("gos", "Pokój gościnny", "gosc", rect(XB, YA, XC, YB), ext="windows")
H.room("pral", "Pralnia", "pralnia", rect(XB, YB, XC, YC), ext={"E": "windows_sq", "S": "solid"})
H.room("her", "Herbaciarnia", "herbaciarnia", rect(XA, YB, XB, YC), ext="band_high", garden="glass")
H.room("gal", "Galeria", "galeria", rect(0, YT, XA, YC), ext={"W": "slits", "S": "windows"})
# patio za murem od wschodu; wzdłuż jego południowego muru schody na taras wschodni
PX = XC + 6.6
H.room("pat", "Patio za murem", "patio", rect(XC, 0, PX, 6.6), roof=rect(XC, 0, XC + 4.2, 2.6), enclose="gwall")

# ---------------------------------------------------------------- piętro (+3,4)
H.room("bib", "Biblioteka", "biblioteka", rect(0, 0, XA, YT), level=1, ext={"W": "band_high", "N": "band_high", "E": "windows"})
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(0, YT, XA, YS), level=1,
       ext={"W": "glass", "E": "band_high", "taS": "glass"})
H.room("laz", "Łazienka", "lazienka", rect(0, YS, XA, YC), level=1, ext="band_high")
H.room("taS", "Taras południowy", "taras", rect(XA, YB, XC, YC), level=1, dz=DZ)
T1B = rect(XC - 1.0, 5.25, XC, 6.35)
H.room("taE", "Taras wschodni", "taras", rect(XB, YA, XC, YB).difference(T1B), level=1, dz=DZ)
H.room("t1b", "Podest", "taras", T1B, level=1, dz=DZ, enclose="open", furn=False)

# ---------------------------------------------------------------- II piętro (+6,6)
H.room("biu", "Biuro", "biuro", rect(0, 0, XA, YO), level=2,
       ext={"W": "glass", "N": "windows", "E": "windows", "taW": "glass_slide"})
T2B = rect(2.3, YC - 1.3, XA, YC - 0.2)
H.room("taW", "Taras zachodni", "taras", rect(0, YO, XA, YC).difference(T2B), level=2, dz=DZ)
H.room("t2b", "Podest", "taras", T2B, level=2, dz=DZ, enclose="open", furn=False)

# ---------------------------------------------------------------- schody
H.stair("spiral", level=0, center=SC, r=1.0, start=120, sweep=300, n=16)
H.stair("spiral", level=1, center=SC, r=1.0, start=120, sweep=300, n=16)
H.stair("straight", level=0, rect=(XC + 0.25, 5.25, XC + 5.45, 6.35), up="W")
H.stair("straight", level=1, rect=(XA + 0.25, YC - 1.3, XA + 5.25, YC - 0.2), up="W")

# ---------------------------------------------------------------- połączenia
H.connect("wia", "hol", "door", at=0.8)
H.connect("hol", "wc", "door")
H.connect("hol", "sal", "double")
H.connect("sal", "gos", "door", at=0.85)
H.connect("hol", "gal", "door")
H.connect("gal", "her", "wide")
H.connect("her", "pral", "door")
H.connect("her", "og", "slide", at=0.2)
H.connect("sal", "pat", "slide")
H.connect("bib", "syp", "door", at=0.85)
H.connect("syp", "laz", "slide", at=0.15, width=0.9)
H.connect("syp", "taS", "slide")
H.connect("biu", "taW", "slide")

H.entrance("wia", "W")
H.exit("pral", "E", kind="door", width=1.0)

# ---------------------------------------------------------------- teren
H.path(rect(-6.0, 0.5, -0.2, 1.9))
H.path(rect(XC + 0.2, 11.2, XC + 5.0, 12.4))
H.tree(-4.0, -2.5, "brzoza")
H.tree(21.5, -2.5, "sosna")
H.tree(17.5, 16.5, "klon")
H.cut("A–A", (6.3, -1.5), (6.3, YC + 1.5))
H.cut("B–B", (-1.5, 5.0), (PX + 1.0, 5.0))
