"""P12 · Oktagon – pierścień ośmiu segmentów wokół oranżerii pod szklaną piramidą."""
from silnik import House, rect, poly, ngon, ngon_band, ngon_vertex

CX, CY = 10.0, 10.0
A_IN, A_MID, A_OUT = 4.5, 7.0, 9.5
# boki ośmiokąta (rot=0): 0 E, 1 SE, 2 S, 3 SW, 4 W, 5 NW, 6 N, 7 NE


def seg(k, a1=A_IN, a2=A_OUT, span=1):
    return ngon_band(CX, CY, 8, a1, a2, k, span)


def V(a, k):
    """Wierzchołek między bokami k i k+1 na apotemie a."""
    return ngon_vertex(CX, CY, 8, a, k)


H = House(
    "p12", "Oktagon",
    "Tagline – do uzupełnienia.",
    style=dict(fasada="miedz", dach="sedum"),
    concept=["Koncepcja – do uzupełnienia."],
    notes=dict(lato="-", zima="-", technologia="-"),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

# --- brama (N): hol ze schodami kręconymi i WC
Y_WC, X_WC = 2.8, 8.6
H.room("wc", "WC", "wc", poly(V(A_OUT, 5), (X_WC, CY - A_OUT), (X_WC, Y_WC), V(CY - Y_WC, 5)))
H.room("hol", "Hol", "hol",
       poly((X_WC, CY - A_OUT), V(A_OUT, 6), V(A_IN, 6), V(A_IN, 5), V(CY - Y_WC, 5), (X_WC, Y_WC)),
       ext="slits")
H.stair("spiral", level=0, center=(12.0, 2.0), r=1.0, start=120, sweep=330, n=18)
# --- NE: biuro przeszklone od ogrodu i od pola
H.room("biu", "Biuro", "biuro", seg(7), ext={315: "glass_slide", "*": "solid"}, garden="glass_slide")
# --- E: spiżarnia przelotowa i pralnia
H.room("spi", "Spiżarnia", "spizarnia", seg(0, A_IN, A_MID), garden="solid", label_at=(16.0, 10.0))
H.room("pral", "Pralnia", "pralnia", seg(0, A_MID, A_OUT), ext="windows_sq")
# --- SE + S: salon z kuchnią na dwie kondygnacje
H.room("sal", "Salon z kuchnią", "salon_kuchnia", seg(1, span=2), levels=2,
       ext={45: "windows", 90: "glass", 202.5: "glass_slide", "*": "solid"},
       garden={225: "glass_slide", 270: "glass"}, kitchen_at="E")
# --- SW: patio – część zadaszona zamykana szkłem, część otwarta
H.room("pz", "Patio zimowe", "patio_sezonowe", seg(3, A_IN, A_MID), label_at=(5.9, 13.75))
H.room("pat", "Patio", "patio", seg(3, A_MID, A_OUT))
# --- W: biblioteka (na dachu taras)
H.room("bib", "Biblioteka", "biblioteka", seg(4), ext={67.5: "glass_slide", "*": "solid"})
# --- NW: sala muzyczna (nad nią sypialnia)
H.room("muz", "Sala muzyczna", "muzyczny", seg(5), ext={225: "windows", "*": "solid"})

# --- piętro
A_GL = 6.6   # granica garderoba / łazienka nad bramą
H.room("gar", "Garderoba", "garderoba", seg(6, A_GL, A_OUT), level=1, ext="solid")
H.room("laz", "Łazienka", "lazienka", seg(6, A_IN, A_GL), level=1, ext="band_high", garden="band")
H.room("syp", "Sypialnia", "sypialnia_glowna", seg(5), level=1,
       ext={225: "glass_slide", 112.5: "glass_slide", "*": "solid"}, garden="glass")
H.room("tar", "Taras", "taras", seg(4), level=1, dz=0.05)  # deska 5 cm nad stropem (patrz raport)

# --- ogród
H.ogrod("og", "Oranżeria", ngon(CX, CY, 8, A_IN), levels=2, roof_type="pyramid", style="oranzeria", seed=4)

# --- połączenia
H.connect("hol", "wc", "door")
H.connect("hol", "biu", "door", at=0.8)
H.connect("hol", "muz", "double")
H.connect("biu", "spi", "door")
H.connect("spi", "sal", "door")
H.connect("spi", "pral", "door")
H.connect("bib", "muz", "double", at=0.75)
H.connect("pz", "pat", "fold")
H.connect("gar", "syp", "door", at=0.8)
H.connect("gar", "laz", "door", at=0.8)

H.entrance("hol", "N", at=(CX - X_WC) / (V(A_OUT, 6)[0] - X_WC))
H.exit("pral", "E", kind="door", width=1.0)

H.path(rect(CX - 0.7, -6.0, CX + 0.7, CY - A_OUT - 0.2))
H.tree(-1.5, 3.0, "brzoza")
H.tree(23.0, 22.0, "klon")
H.tree(22.5, -1.5, "lipa")
H.cut("A–A", (CX + 1.6, -2.0), (CX + 1.6, 22.0))
H.cut("B–B", (CX - 8.5, CY - 8.5), (CX + 8.5, CY + 8.5))
