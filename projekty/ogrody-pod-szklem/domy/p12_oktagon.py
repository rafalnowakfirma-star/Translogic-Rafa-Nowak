"""P12 · Oktagon – pierścień ośmiu segmentów wokół oranżerii pod szklaną piramidą."""
from shapely.geometry import LineString

from silnik import House, rect, poly, pt, ngon, ngon_band, ngon_vertex

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
    "Ośmiokątny dom w patynowanej miedzi wokół oranżerii pod szklaną piramidą. "
    "Pokoje w segmentach pierścienia łączą się drzwiami w pętlę wokół ogrodu.",
    style=dict(fasada="miedz", dach="sedum"),
    concept=[
        "Pierścień ośmiu segmentów (19 m szerokości, 5 m głębokości) otacza ośmioboczną oranżerię 65 m² "
        "z cytrusami w donicach i fontanną. Z każdego segmentu parteru widać ogród przez szkło, "
        "więc ogród jest głównym holem domu.",
        "Wejście leży na osi północnej: w miedzianej ścianie z wąskimi szczelinami są drzwi, "
        "a z sieni na wprost widać przez szkło fontannę. W sieni stoją kręcone schody na piętro.",
        "Parter obchodzi się dookoła bez korytarzy: sień, biblioteka, sala muzyczna, patio zimowe, "
        "salon z kuchnią, spiżarnia, biuro i z powrotem sień.",
        "Biuro od północnego wschodu ma szkło od ogrodu i od pola oraz własne przesuwne drzwi na zewnątrz, "
        "więc klient nie przechodzi przez dom.",
        "Salon z kuchnią na dwie kondygnacje zajmuje dwa segmenty od południa. Obok jest patio zimowe pod dachem: "
        "zimą zamyka je szklana harmonijka, latem harmonijka się składa i patio zimowe łączy się z odkrytym "
        "patio z desek przed domem.",
        "Piętro stoi tylko nad sienią i biblioteką, a salon ma podwójną wysokość, więc nad pierścieniem "
        "wznoszą się dwie wysokie pary segmentów naprzeciw siebie, a ponad nimi szklana piramida. "
        "Sypialnia ma szklaną ścianę na północny zachód i wyjście na taras na dachu sali muzycznej; "
        "garderoba i łazienka są nad sienią.",
    ],
    notes=dict(
        lato="Latarnia na szczycie piramidy unosi się i wyciąga ciepłe powietrze z oranżerii, harmonijka patio "
             "zimowego składa się, a szklane drzwi salonu, biura i sypialni stoją otworem.",
        zima="Latarnia jest opuszczona, oranżeria zbiera ciepło słońca i osłania pokoje od środka, a patio zimowe "
             "działa jak zamknięta weranda między salonem a salą muzyczną.",
        technologia="Stalowy szkielet ze słupami w narożnikach ośmioboku i prefabrykowane panele ścienne "
                    "(rama stalowa z wełną mineralną) obłożone patynowaną blachą miedzianą; stropy z płyt "
                    "prefabrykowanych, piramida ze stalowych żeber i szkła zespolonego.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)
H.level(2, z=6.8, h=1.3)

# --- brama (N): hol ze schodami kręconymi i WC
Y_WC, X_WC = 2.8, 9.3
H.room("wc", "WC", "wc", poly(V(A_OUT, 5), (X_WC, CY - A_OUT), (X_WC, Y_WC), V(CY - Y_WC, 5)))
H.room("hol", "Sień", "hol",
       poly((X_WC, CY - A_OUT), V(A_OUT, 6), V(A_IN, 6), V(A_IN, 5), V(CY - Y_WC, 5), (X_WC, Y_WC)),
       ext="slits")
H.stair("spiral", level=0, center=(12.0, 2.0), r=1.0, start=120, sweep=330, n=18)
# --- NE: biuro przeszklone od ogrodu i od pola
H.room("biu", "Biuro", "biuro", seg(7), ext={315: "glass_slide", "*": "solid"}, garden="glass_slide")
# --- E: spiżarnia przelotowa i pralnia
H.room("spi", "Spiżarnia", "spizarnia", seg(0, A_MID, A_OUT), ext="solid")
H.room("pral", "Pralnia", "pralnia", seg(0, A_IN, A_MID), garden="windows")
# --- SE + S: salon z kuchnią na dwie kondygnacje
H.room("sal", "Salon z kuchnią", "salon_kuchnia", seg(1, span=2), levels=2,
       ext={45: "windows", 90: "glass", 202.5: "glass_slide", "*": "solid"},
       garden={225: "glass_slide", 270: "glass"}, kitchen_at="E")
# --- SW: patio zimowe (zadaszone, harmonijka szklana) i taras drewniany przed nim
A_DECK = 12.0
H.room("pz", "Patio zimowe", "patio_sezonowe", seg(3), furn=False)
H.room("pat", "Patio", "patio", seg(3, A_OUT, A_DECK))
# --- W: sala muzyczna (na dachu taras), otwiera się na patio zimowe
H.room("muz", "Sala muzyczna", "muzyczny", seg(4), ext={67.5: "glass_slide", "*": "solid"})
# --- NW: biblioteka (nad nią sypialnia)
H.room("bib", "Biblioteka", "biblioteka", seg(5), ext={225: "windows", "*": "solid"})

# --- piętro
A_GL = 6.6   # granica garderoba / łazienka nad bramą
H.room("gar", "Garderoba", "garderoba", seg(6, A_GL, A_OUT), level=1, ext="slits")
H.room("laz", "Łazienka", "lazienka", seg(6, A_IN, A_GL), level=1, ext="solid", garden="band")
H.room("syp", "Sypialnia", "sypialnia_glowna", seg(5), level=1,
       ext={225: "glass", 112.5: "glass_slide", "*": "solid"}, garden="solid")
H.room("tar", "Taras", "taras", seg(4), level=1, dz=0.05)  # deska 5 cm nad stropem (patrz raport)

# --- ogród
H.ogrod("og", "Oranżeria", ngon(CX, CY, 8, A_IN), levels=3, roof_type="pyramid", style="oranzeria", seed=4)  # podstawa piramidy na wysokości attyk

# --- połączenia
H.connect("hol", "wc", "door", at=0.2)
H.connect("hol", "biu", "door", at=0.8)
H.connect("hol", "bib", "door", at=0.3)
H.connect("biu", "spi", "door")
H.connect("spi", "sal", "door")
H.connect("spi", "pral", "door")
H.connect("bib", "muz", "double", at=0.75)
H.connect("pz", "pat", "fold")
H.connect("gar", "syp", "door", at=0.8)
H.connect("syp", "laz", "door", at=0.75)

H.entrance("hol", "N", at=(CX - X_WC) / (V(A_OUT, 6)[0] - X_WC))
H.exit("spi", "E", kind="door", width=1.0)
H.window("muz", "W", at=0.85, width=1.2, sill=0.4, head=2.7)

H.path(rect(CX - 0.7, -6.0, CX + 0.7, CY - A_OUT - 0.2))
DOOR_BIU = pt(CX, CY, A_OUT + 0.2, 315)   # przesuwne drzwi biura (NE)
H.path(LineString([DOOR_BIU, pt(CX, CY, A_OUT + 2.4, 315), (18.3, -1.4), (CX + 0.7, -1.4)])
       .buffer(0.6, cap_style=2, join_style=2))
H.tree(13.0, -5.5, "brzoza")
H.tree(24.5, 2.5, "lipa")
H.tree(23.0, 22.0, "klon")
H.tree(-6.0, 7.5, "sosna")
H.cut("A–A", (CX + 1.6, -2.0), (CX + 1.6, 22.0))
H.cut("B–B", pt(CX, CY, A_DECK + 0.5, 135), pt(CX, CY, A_OUT + 1.0, 315))
