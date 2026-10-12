"""P21 · Kaskada (zamówienie indywidualne) – ogród zimowy z wodospadem na pełnej ścianie zewnętrznej i jacuzzi,
po drugiej stronie korytarz łączący dwa skrzydła; salon z kuchnią przy ogrodzie, sypialnia z łazienką na parterze,
wieża z dwoma biurami, piwnica z salą kinową, otwarty taras na dachu. Do 180 m² razem z piwnicą."""
from silnik import House, rect, poly

# siatka (oś ścian): salon | ogród | skrzydło wschodnie = 5,8 | 5,6 | 6,2 m (x); ogród | korytarz = 6,4 | 1,6 m (y)
XS, XG, XE = 5.8, 11.4, 17.6
YG, YK = 6.4, 8.0
XB = 14.8          # granica łazienki / holu (parter), biur / holu (piętro), techniki / holu (piwnica)
YS = 3.6           # granica sypialni (parter), biur (piętro), sali kinowej (piwnica)
YH = 9.6           # południowa ściana holu z wejściem
YT = 7.2           # południowa ściana wieży (piętro)
YP = 7.4           # południowa ściana piwnicy
SC = (16.2, 5.9)   # schody kręcone: piwnica – parter – piętro w jednym trzonie

H = House(
    "p21", "Kaskada",
    "Dom zamówiony indywidualnie: ogród zimowy jak na zdjęciu klienta – wodospad z łupka między zielonymi ścianami wpada do jacuzzi, obok pomost z sofą, mech i drzewko cytryny, "
    "po drugiej stronie szklany korytarz łączący dwa skrzydła. Przy ogrodzie salon z kuchnią, sypialnia z łazienką, w wieży dwa biura, "
    "pod spodem piwnica z salą kinową, a na dachu otwarty taras.",
    style=dict(fasada="tynk", dach="sedum", akcent="dab"),
    concept=[
        "Ogród zimowy 5,6 × 6,4 m leży między dwoma skrzydłami domu. Od północy zamyka go pełna ściana zewnętrzna bez okien, "
        "po której spływa wodospad do kamiennej niecki, a od południa szklany korytarz łączący oba skrzydła – z ulicy ogrodu nie widać.",
        "Jak na zdjęciu klienta: wodospad spływa z podświetlonej półki po ścianie z ciemnego łupka, a po obu jego stronach "
        "rosną zielone ściany z monster i paproci. Woda wpada wprost do jacuzzi w turkusowej mozaice – mniejszego od basenu ze zdjęcia – "
        "obramowanego trawertynem i drewnianym pomostem.",
        "Od strony korytarza leży drewniany pomost z dużą sofą i stolikiem, przodem do wodospadu, z taśmą LED pod krawędzią. "
        "Reszta to prawdziwy ogród: miękkie runo z mchu, kwiaty, paprocie i jedno drzewko owocowe – cytryna, która pod szkłem "
        "owocuje przez cały rok; od salonu do pomostu prowadzą płyty z trawertynu.",
        "Dach ogrodu jest przesuwny: latem rozsuwa się nad całym ogrodem, zimą zamyka i ogród zbiera ciepło słońca.",
        "Salon z kuchnią (zachodnie skrzydło) przylega do ogrodu szklaną ścianą z drzwiami przesuwnymi, kuchnia stoi od północy.",
        "We wschodnim skrzydle sypialnia i łazienka mają szkło od ogrodu od podłogi do 50 cm pod sufitem – górny pas ściany jest pełny. "
        "Do łazienki wchodzi się tylko z sypialni; na parterze dla gości jest osobne WC przy holu.",
        "Wieża nad sypialnią mieści dwa biura obok siebie, oddzielone ścianą i każde z własnym wejściem z holu, przeszklone tak samo "
        "do 50 cm pod sufitem – na dach ogrodu i wodospad. Na piętrze jest tylko WC, bez łazienki.",
        "Schody kręcone w trzonie holu prowadzą w dół do piwnicy z salą kinową i pomieszczeniem technicznym, a w górę do biur. "
        "Z drugiego biura wychodzi się na otwarty taras na dachu korytarza i holu, z widokiem na szklany dach ogrodu.",
    ],
    notes=dict(
        lato="Szklany dach ogrodu jest rozsunięty, wodospad szumi pod gołym niebem, a z korytarza wychodzi się na pomost z sofą i do jacuzzi. "
             "Wieczorem siedzi się na otwartym tarasie nad korytarzem.",
        zima="Dach jest zamknięty, w ogrodzie zostaje zielony mech i owocująca cytryna, a jacuzzi paruje pod szkłem; "
             "pełna ściana z wodospadem chroni ogród od północy, a kino w piwnicy czeka na długie wieczory.",
        technologia="Ściany i piwnica z bloczków ICF (styropian zalany betonem) – szczelna, ciepła piwnica pod kinem; ściana wodospadu "
                    "żelbetowa z okładziną kamienną i hydroizolacją od strony ogrodu, pompa obiegowa w pomieszczeniu technicznym. "
                    "Dach ogrodu przesuwny na stalowej ramie, taras na stropie z warstwą spadkową i balustradą szklaną.",
    ),
)
H.max_area = 180.0          # zamówienie: do 180 m² razem z piwnicą
H.dach_dzien = 0.0          # kadry i spacer: ogród pod zamkniętym szklanym dachem, jak na zdjęciu klienta (animacja pokazuje otwieranie)

H.level(-1, z=-3.0, h=3.0)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

# ---------------------------------------------------------------- ogród zimowy
H.ogrod("og", "Ogród zimowy z jacuzzi", rect(XS, 0, XG, YG), roof_type="slide", style="jacuzzi", edge="solid", seed=21)

# ---------------------------------------------------------------- parter
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(0, 0, XS, YK), kitchen_at="N",
       ext={"N": "band_high", "W": "windows", "S": "windows"})
H.room("kor", "Korytarz", "korytarz", rect(XS, YG, XG, YK), ext="solid")
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(XG, 0, XE, YS), ext="band_high", garden="glass_50")
H.room("laz", "Łazienka", "lazienka", rect(XG, YS, XB, YG), garden="glass_50")
H.room("hol", "Hol z wejściem", "hol",
       poly((XB, YS), (XE, YS), (XE, YH), (13.4, YH), (13.4, YK), (XG, YK), (XG, YG), (XB, YG)),
       ext={"E": "windows_sq", "S": "band_high"})
H.room("wc", "WC", "wc", rect(XG, YK, 13.4, YH))
H.stair("spiral", level=0, center=SC, r=1.0, start=200, sweep=300, n=16)

H.connect("sal", "kor", "open")
H.connect("kor", "hol", "door", at=0.5)
H.connect("hol", "syp", "door", at=0.5)
H.connect("syp", "laz", "door", at=0.25)
H.connect("hol", "wc", "door", at=0.5)
H.entrance("hol", "S", at=0.55)

# ---------------------------------------------------------------- piętro: wieża z dwoma biurami, WC, taras na dachu
H.room("biu1", "Biuro 1", "biuro", rect(XG, 0, XB, YS), level=1, ext="glass_50")
H.room("biu2", "Biuro 2", "biuro", rect(XG, YS, XB, YT), level=1, ext={"tar": "glass_slide", "*": "glass_50"})
H.room("hol1", "Hol piętra", "hol", rect(XB, 1.8, XE, YT), level=1, ext={"E": "windows_sq", "*": "solid"})
H.room("wc1", "WC", "wc", rect(XB, 0, XE, 1.8), level=1)
H.room("tar", "Taras otwarty", "taras",
       poly((XS, YG), (XG, YG), (XG, YT), (XE, YT), (XE, YH), (XG, YH), (XG, YK), (XS, YK)), level=1)
H.stair("spiral", level=-1, center=SC, r=1.0, start=200, sweep=300, n=16)

H.connect("hol1", "biu1", "door", at=0.5)
H.connect("hol1", "biu2", "door", at=0.17)
H.connect("hol1", "wc1", "door", at=0.5)
H.connect("biu2", "tar", "slide", at=0.5)

# ---------------------------------------------------------------- piwnica
H.room("kino", "Sala kinowa", "kino", rect(XG, 0, XE, YS), level=-1)
H.room("tech", "Pomieszczenie techniczne", "techniczne", rect(XG, YS, XB, YP), level=-1)
H.room("holp", "Hol piwnicy", "hol", rect(XB, YS, XE, YP), level=-1, ext="solid")

H.connect("holp", "kino", "door", at=0.5)
H.connect("holp", "tech", "door", at=0.2)

# ---------------------------------------------------------------- teren
H.path(rect(14.6, YH + 0.2, 16.0, YH + 6.0))
H.tree(-3.5, 2.0, "brzoza")
H.tree(20.5, 2.5, "klon")
H.tree(3.0, 12.0, "lipa")
H.cut("A–A", (8.6, -2.5), (8.6, 12.0))
H.cut("B–B", (-2.0, 3.0), (20.0, 3.0))
