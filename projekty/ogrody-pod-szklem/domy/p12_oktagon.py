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
Y_WC = 2.8
X_WC = 11.4
H.room("wc", "WC", "wc", poly((X_WC, CY - A_OUT), V(A_OUT, 6), V(CY - Y_WC, 6), (X_WC, Y_WC)))
H.room("hol", "Hol", "hol",
       poly(V(A_OUT, 5), (X_WC, CY - A_OUT), (X_WC, Y_WC), V(CY - Y_WC, 6), V(A_IN, 6), V(A_IN, 5)),
       ext="slits")
H.stair("spiral", level=0, center=(8.0, 2.0), r=1.0, start=90, sweep=330, n=18)
# --- NE: biuro przeszklone od ogrodu i od pola
H.room("biu", "Biuro", "biuro", seg(7), ext={315: "glass_slide", "*": "solid"}, garden="glass_slide")
# --- E: spiżarnia przelotowa i pralnia
H.room("spi", "Spiżarnia", "spizarnia", seg(0, A_IN, A_MID))
H.room("pral", "Pralnia", "pralnia", seg(0, A_MID, A_OUT), ext="windows_sq")
# --- SE + S: salon z kuchnią na dwie kondygnacje
H.room("sal", "Salon z kuchnią", "salon_kuchnia", seg(1, span=2), levels=2,
       ext={45: "windows", 90: "glass_slide", 202.5: "glass_slide", "*": "solid"}, kitchen_at="E")
# --- SW: patio – część zadaszona zamykana szkłem, część otwarta
H.room("pz", "Patio zimowe", "patio_sezonowe", seg(3, A_IN, A_MID))
H.room("pat", "Patio", "patio", seg(3, A_MID, A_OUT))
# --- W: biblioteka (na dachu taras)
H.room("bib", "Biblioteka", "biblioteka", seg(4), ext={67.5: "glass_slide", 180: "slits", "*": "solid"})
# --- NW: sala muzyczna (nad nią sypialnia)
H.room("muz", "Sala muzyczna", "muzyczny", seg(5), ext={225: "windows", "*": "solid"})

# --- piętro
H.room("gar", "Garderoba", "garderoba", poly(V(A_OUT, 5), (CX, CY - A_OUT), (CX, CY - A_IN), V(A_IN, 5)), level=1)
H.room("laz", "Łazienka", "lazienka", poly((CX, CY - A_OUT), V(A_OUT, 6), V(A_IN, 6), (CX, CY - A_IN)), level=1,
       ext="band_high", garden="band")
H.room("syp", "Sypialnia", "sypialnia_glowna", seg(5), level=1,
       ext={225: "glass_slide", 112.5: "glass_slide", "*": "solid"}, garden="glass")
H.room("tar", "Taras", "taras", seg(4), level=1)

# --- ogród
H.ogrod("og", "Oranżeria", ngon(CX, CY, 8, A_IN), levels=2, roof_type="pyramid", style="oranzeria", seed=4)

# --- połączenia
H.connect("hol", "wc", "door")
H.connect("hol", "biu", "door")
H.connect("hol", "muz", "double", at=0.7)
H.connect("biu", "spi", "door")
H.connect("spi", "sal", "door")
H.connect("spi", "pral", "door")
H.connect("bib", "muz", "double")
H.connect("pz", "pat", "fold")
H.connect("gar", "syp", "door")
H.connect("gar", "laz", "door")

H.entrance("hol", "N", at=(CX - V(A_OUT, 5)[0]) / (X_WC - V(A_OUT, 5)[0]))
H.exit("pral", "E", kind="door", width=1.0)

H.path(rect(CX - 0.7, -6.0, CX + 0.7, CY - A_OUT - 0.2))
H.tree(-1.5, 3.0, "brzoza")
H.tree(23.0, 22.0, "klon")
H.tree(22.5, -1.5, "lipa")
H.cut("A–A", (CX, -2.0), (CX, 22.0))
H.cut("B–B", (CX - 12.0, CY - 12.0), (CX + 12.0, CY + 12.0))
