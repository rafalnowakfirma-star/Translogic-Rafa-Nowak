"""P05 · Wiatrak – cztery proste skrzydła ułożone jak łopaty wiatraczka wokół kwadratowego ogrodu."""
from silnik import House, rect, union

# Ogród 8 × 8 m w kwadracie (8,8)–(16,16). Cztery skrzydła (4,2 m, południowe 5,6 m)
# obiegają go zgodnie z ruchem wskazówek zegara i każde wystaje 3,6 m poza obrys sąsiada:
#   północne  x 8–23,8  (wystaje na wschód)      zachodnie x 3,8–8  (wystaje na północ)
#   wschodnie y 8–25,2  (wystaje na południe)    południowe x 0,2–16 (wystaje na zachód)
# Między końcami powstają cztery dziedzińce: wejściowy (N), poranny (E), patio (S), gospodarczy (W).

H = House(
    "p05", "Wiatrak",
    "Cztery proste skrzydła ułożone jak łopaty wiatraczka wokół kwadratowego ogrodu pod przesuwnym szklanym dachem. "
    "Każda łopata wystaje poza obrys domu i kończy się otwartym zadaszeniem, a między łopatami są cztery różne dziedzińce.",
    style=dict(fasada="trawertyn", dach="sedum", akcent="stal"),
    concept=[
        "Ogród 8 × 8 m leży w środku, a cztery prostokątne skrzydła obiegają go zgodnie z ruchem wskazówek zegara. "
        "Każde skrzydło wystaje 3 m poza sąsiednie, dlatego między ich końcami powstają cztery dziedzińce: wejściowy od północy, "
        "poranny przy sypialni od wschodu, patio przy salonie od południa i gospodarczy od zachodu.",
        "Każda łopata kończy się otwartym końcem pod dachem: wiata na samochód i rowery przy wejściu, loggia nad porannym ogrodem, "
        "zadaszona część patio i drewutnia przy podwórzu gospodarczym. Dzięki temu dom ma 250 m² w środku, a wygląda na większy.",
        "Skrzydło północne to amfilada: wiatrołap ze szklaną ścianą do ogrodu, biblioteka z krętymi schodami i pokój muzyczny, "
        "z którego wychodzi się na loggię. Nad biblioteką i pokojem muzycznym jest piętro z dwoma pokojami, łazienką i tarasem nad loggią.",
        "Biuro w skrzydle zachodnim ma szkło od ogrodu i od zachodu, więc po południu widać z biurka zachód słońca nad oliwkami "
        "zachodniego dziedzińca. Wchodzi się do niego z ogrodu, który jest holem domu.",
        "Salon z kuchnią w skrzydle południowym ma 6,5 m wysokości i szkło na całą południową ścianę. Kuchnia stoi przy ścianie "
        "łazienki i spiżarni, a przez przesuwne szkło wychodzi się na patio, którego część pod końcem skrzydła wschodniego ma dach.",
        "Sypialnia od wschodu ma całą ścianę ze szkła na poranny ogród. Przez przelotową garderobę przechodzi się do łazienki. "
        "Dach ogrodu jest z dwóch szklanych tafli: latem jedna zsuwa się nad drugą i ogród z oliwką, lawendą i żwirem stoi pod gołym niebem.",
    ],
    notes=dict(
        lato="Połowa szklanego dachu zjeżdża nad drugą połowę, szklane ściany biura, salonu i sypialni rozsuwają się, a cień dają zadaszone końce skrzydeł: wiata, loggia i daszek patio.",
        zima="Dach jest zamknięty, ogród ze żwirem i kamiennymi murami zbiera ciepło ze słońca, a wszystkie pokoje mają od środka ogród zamiast mrozu; wchodzi się do nich z ogrodu, nie z zewnątrz.",
        technologia="Ściany z bloczków silikatowych na klej, okładzina z płyt trawertynu na ruszcie, stropy i dachy z prefabrykowanych płyt kanałowych; zadaszenia końców skrzydeł na stalowych słupach, dach szklany na stalowej ramie z napędem przesuwnym.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

H.ogrod("og", "Ogród", rect(8, 8, 16, 16), levels=1, roof_type="slide", style="srodziemnomorski", seed=11)

# skrzydło zachodnie (x 3,8–8): wiata, biuro, pralnia
H.room("wiata", "Wiata", "loggia", rect(3.8, 0.2, 8, 8), floor="plyty", furn=False)
H.room("biu", "Biuro", "biuro", rect(3.8, 8, 8, 13.6), ext={"W": "glass_slide", "N": "solid"}, garden="glass_slide")
H.room("pral", "Pralnia", "pralnia", rect(3.8, 13.6, 8, 16), ext={"W": "windows_sq"}, garden="band_high")

# skrzydło północne (y 3,8–8): amfilada wiatrołap – biblioteka – pokój muzyczny – loggia
H.room("wia", "Wiatrołap", "wiatrolap", rect(8, 3.8, 10.6, 8), ext={"N": "slits", "W": "solid"}, garden="glass_slide")
H.room("wc", "WC", "wc", rect(10.6, 3.8, 12.2, 5.8))
H.room("bib", "Biblioteka", "biblioteka", union(rect(10.6, 5.8, 12.2, 8), rect(12.2, 3.8, 17.6, 8)),
       ext={"N": "solid"}, garden="glass_slide")
H.room("muz", "Pokój muzyczny", "muzyczny", rect(17.6, 3.8, 21.2, 8), ext={"N": "windows", "E": "glass", "S": "solid"})
H.room("log", "Loggia", "loggia", rect(21.2, 3.8, 23.8, 8))

# skrzydło wschodnie (x 16–20,2): sypialnia – garderoba – łazienka – spiżarnia, koniec zadaszony nad patio
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(16, 8, 20.2, 13.6), ext={"E": "glass_slide"}, garden="glass_slide")
H.room("gar", "Garderoba", "garderoba", rect(16, 13.6, 20.2, 16), ext={"E": "band_high"})
H.room("laz", "Łazienka", "lazienka", rect(16, 16, 20.2, 19.4), ext={"E": "band_high"})
H.room("spi", "Spiżarnia", "spizarnia", rect(16, 19.4, 20.2, 21.6), ext="solid")
H.room("pat", "Patio", "patio", rect(9.4, 21.6, 20.2, 25.8), roof=rect(16, 21.6, 20.2, 25.2))

# skrzydło południowe (y 16–21,6): salon z kuchnią na 2 kondygnacje, drewutnia i techniczne na końcu
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(3.8, 16, 16, 21.6), levels=2, kitchen_at="E",
       ext={"S": "glass_slide", "E": "windows", "N": "glass", "W": "slits"})
H.room("drew", "Drewutnia", "loggia", rect(0.2, 16, 3.8, 18.6), floor="plyty", furn=False)
H.room("tech", "Techniczne", "techniczne", rect(0.2, 18.6, 3.8, 21.6), ext="solid")

# piętro nad skrzydłem północnym: dwa pokoje, łazienka, hol z krętymi schodami, taras nad loggią
H.room("pok1", "Pokój dziecięcy", "pokoj", rect(8, 3.8, 12.2, 8), level=1, ext={"N": "windows", "W": "windows", "S": "windows"})
H.room("laz1", "Łazienka", "lazienka", rect(12.2, 3.8, 14.6, 6.2), level=1)
H.room("hol1", "Hol", "hol", union(rect(12.2, 6.2, 14.6, 8), rect(14.6, 3.8, 17.6, 8)), level=1,
       ext={"N": "slits", "S": "glass"})
H.room("pok2", "Pokój gościnny", "gosc", rect(17.6, 3.8, 21.2, 8), level=1, ext={"N": "windows", "S": "windows", "E": "glass_slide"})
H.room("tar", "Taras", "taras", rect(21.2, 3.8, 23.8, 8), level=1)
H.stair("spiral", level=0, center=(16.3, 5.25), r=1.0, start=180, sweep=300, n=15)

# połączenia
H.connect("wia", "wc", "door")
H.connect("wia", "bib", "wide")
H.connect("wia", "wiata", "door", at=0.8)
H.connect("bib", "muz", "double", at=0.25)
H.connect("muz", "log", "slide", at=0.8)
H.connect("syp", "gar", "door")
H.connect("gar", "laz", "slide")
H.connect("sal", "spi", "door")
H.connect("sal", "pral", "door", at=0.3)
H.connect("sal", "tech", "door", at=0.7)
H.connect("hol1", "pok1", "door")
H.connect("hol1", "laz1", "door")
H.connect("hol1", "pok2", "door")

H.entrance("wia", "N")
H.window("bib", "N", at=0.84, width=1.4, sill=1.7, head=2.7)   # wysokie okno nad krętymi schodami; reszta ściany pod regały
H.exit("pral", "W", kind="door", width=1.0)
H.exit("tech", "N", kind="door", width=1.0)

# teren: dojście i podjazd od północy, deska przed sypialnią, podwórze przy pralni
H.path(rect(8.6, -4.0, 10.0, 3.6))
H.path(rect(4.0, -4.0, 7.8, 0.2))
H.path(rect(20.5, 9.0, 23.8, 13.6))
H.path(rect(0.0, 13.2, 3.6, 16.0))
H.tree(1.2, 9.6, "oliwka")
H.tree(15.5, -2.5, "brzoza")
H.tree(24.5, 20.0, "lipa")
H.tree(5.5, 26.5, "klon")

H.cut("A–A", (13.4, -2.0), (13.4, 28.0))
H.cut("B–B", (-1.0, 5.0), (27.0, 5.0))
