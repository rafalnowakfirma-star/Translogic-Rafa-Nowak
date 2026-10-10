"""P13 · Kubik – zwarta kostka 12,6 × 12,8 m z atrium 5 × 5 m przez dwie kondygnacje pod lamelowym dachem."""
from silnik import House, rect

# siatka: pasma W | atrium | E = 3,8 | 5,0 | 3,8 m (x), N | atrium | S = 3,4 | 5,0 | 4,4 m (y)
XW, XE, XX = 3.8, 8.8, 12.6
YN, YS, YY = 3.4, 8.4, 12.8

H = House(
    "p13", "Kubik",
    "Najmniejszy dom kolekcji: kostka 12,6 × 12,8 m na dwie kondygnacje z atrium 5 × 5 m w samym środku. "
    "Dwa narożniki kostki są wycięte: na parterze patio sezonowe, nad nim taras sypialni.",
    style=dict(fasada="blacha", dach="sedum", akcent="modrzew"),
    concept=[
        "Atrium 5 × 5 m przechodzi przez obie kondygnacje i ma dach z obrotowych szklanych lameli; wokół niego biegnie pierścień pokoi o głębokości 3,4–4,4 m, więc każdy pokój ma ścianę do ogrodu.",
        "Biuro zajmuje wschodnie pasmo piętra: od zachodu patrzy przez szkło w koronę klonu w atrium, od wschodu przez szklaną ścianę na pola. Wchodzi się do niego przez bibliotekę.",
        "Parter obchodzi się bez korytarzy: z wiatrołapu w lewo do holu ze schodami i pokoju gościnnego, w prawo do pracowni, a z salonu przez spiżarnię-kredens do pralni.",
        "Salon z kuchnią ma 6,1 m wysokości i zajmuje południowe pasmo; na zachodzie otwiera się szklaną ścianą na patio sezonowe wycięte z narożnika bryły – zimą zamknięte szklaną harmonijką, latem całkiem otwarte.",
        "Schody proste biegną w holu wzdłuż północnej ściany i wychodzą na galerię nad holem, która ciągnie się wzdłuż szkła atrium i prowadzi do łazienki, sypialni i biblioteki.",
        "Sypialnia na piętrze ma całą zachodnią ścianę ze szkła i wychodzi na taras nad patio; łóżko stoi pośrodku, między ogrodem w atrium a krajobrazem.",
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
H.room("pod", "Podcień", "loggia", rect(0, 0, 2.4, 1.6), furn=False)
H.room("wc", "WC", "wc", rect(2.4, 0, XW, 1.6))
H.room("wia", "Wiatrołap", "wiatrolap", rect(0, 1.6, XW, YN), ext={"W": "slits", "N": "solid"})
H.room("hol", "Hol", "hol", rect(XW, 0, XE, YN), ext={"N": "slits"})
H.stair("straight", level=0, rect=(3.9, 0.25, 8.6, 1.35), up="W")
H.room("gos", "Pokój gościnny", "gosc", rect(XE, 0, XX, YN), ext={"N": "windows", "E": "windows"})
H.room("pral", "Pralnia", "pralnia", rect(XE, YN, XX, 5.8), ext={"E": "windows_sq"}, garden="band_high")
H.room("spi", "Spiżarnia-kredens", "spizarnia", rect(XE, 5.8, XX, YS), ext={"E": "windows_sq"})
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(XW, YS, XX, YY), levels=2,
       ext={"S": "glass_slide", "E": "windows", "W": "glass_slide"}, kitchen_at="E")
H.room("pat", "Patio sezonowe", "patio_sezonowe", rect(0, YS, XW, YY))
H.room("pra", "Pracownia", "pracownia", rect(0, YN, XW, YS), ext={"W": "windows", "S": "glass_slide"})

H.connect("wia", "hol", "door")
H.connect("wia", "wc", "door")
H.connect("wia", "pra", "door")
H.connect("hol", "gos", "door", at=0.7)
H.connect("sal", "spi", "door")
H.connect("spi", "pral", "door")
H.entrance("wia", "N")

# ---------------------------------------------------------------- piętro
H.room("laz", "Łazienka", "lazienka", rect(0, 0, 2.4, YN), level=1)
H.room("gal", "Galeria", "galeria", rect(2.4, 0, XE, YN), level=1, ext={"N": "slits"}, garden="glass")
H.room("bib", "Biblioteka", "biblioteka", rect(XE, 0, XX, YN), level=1, ext={"N": "windows", "E": "windows"})
H.room("biu", "Biuro", "biuro", rect(XE, YN, XX, YS), level=1, ext={"E": "glass"}, garden="glass")
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(0, YN, XW, YS), level=1,
       ext={"W": "glass_slide", "S": "glass_slide"}, garden="glass")
H.room("tar", "Taras", "taras", rect(0, YS, XW, YY), level=1)

H.connect("gal", "laz", "door", at=0.7)
H.connect("gal", "syp", "door")
H.connect("gal", "bib", "door", at=0.7)
H.connect("bib", "biu", "double")

# ---------------------------------------------------------------- teren
H.path(rect(0.6, -6.0, 1.8, 0.0))
H.path(rect(-3.6, 9.0, -0.2, YY))
H.tree(-4.5, 14.5, "klon")
H.tree(16.0, 2.0, "brzoza")
H.tree(15.5, 15.0, "sosna")
H.cut("A–A", (6.3, -2.0), (6.3, 15.0))
H.cut("B–B", (15.0, 0.8), (-2.0, 0.8))
