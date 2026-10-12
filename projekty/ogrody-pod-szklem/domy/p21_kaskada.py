"""P21 · Kaskada (zamówienie indywidualne, wersja 2) – długi parterowy dom z ogrodem zimowym wzdłuż długiej ściany:
wodospad na pełnej ścianie zewnętrznej, naprzeciw tylko korytarz łączący dwa segmenty. Segment zachodni: długa kuchnia
oddzielona od salonu ścianą z lameli, nad nimi pokój dziecięcy; segment wschodni: sypialnia z łazienką, nad nimi
wieża z dwoma biurami. Dwie klatki schodowe na końcach domu, na piętrze jeden korytarz wzdłuż całego domu,
piwnica z salą kinową (poza powierzchnią użytkową), patio z grillem. Bez łuków i skośnych ścian."""
from silnik import House, rect, poly

# siatka (oś ścian): segment zachodni | ogród | segment wschodni = 8,0 | 9,0 | 7,6 m (x); ogród | korytarz = 5,8 | 1,8 m (y)
XW, XE, XK = 8.0, 17.0, 24.6
YG, YK = 5.8, 7.6
YL = 3.4           # ściana z lameli między kuchnią a salonem
YS = 3.6           # sypialnia | łazienka (parter), biura (piętro)
XB = 20.4          # łazienka | WC
XC = 21.5          # WC | przejście do sypialni
XD = 22.6          # sypialnia | klatka schodowa wschodnia
YD = 2.0           # garderoba | klatka schodowa
SW = (0.9, YL + 0.06, 5.1, YL + 1.06)          # schody proste przy lamelach (salon → hol piętra)
SE = (XD + 0.06, YD + 0.06, XK - 0.2, YG)       # schody dwubiegowe w holu (piwnica → parter → piętro)

H = House(
    "p21", "Kaskada",
    "Dom zamówiony indywidualnie: długi ogród zimowy jak na zdjęciu klienta – wodospad z łupka między zielonymi ścianami "
    "wpada do jacuzzi, obok pomost z sofą, mech, kwiaty i drzewko cytryny – a naprzeciw tylko szklany korytarz. "
    "Długa kuchnia za ścianą z lameli, salon przy ogrodzie, sypialnia z łazienką, pokój dziecięcy, dwa biura w wieży, "
    "kino w piwnicy i patio z grillem.",
    style=dict(fasada="tynk", dach="sedum", akcent="dab"),
    concept=[
        "Ogród zimowy 9,0 × 5,8 m ciągnie się wzdłuż długiej ściany domu. Od północy zamyka go pełna ściana zewnętrzna, "
        "po której spływa wodospad, od południa tylko szklany korytarz łączący oba segmenty – z ulicy ogrodu nie widać.",
        "Jak na zdjęciu klienta: wodospad spływa z podświetlonej półki po ścianie z ciemnego łupka, po obu stronach "
        "rosną zielone ściany z monster i paproci, a woda wpada do jacuzzi w turkusowej mozaice (zamiast basenu). "
        "Od korytarza drewniany pomost z sofą, reszta to prawdziwy ogród: mech, kwiaty, paprocie i cytryna posadzona w gruncie.",
        "Dach ogrodu jest przesuwny: latem rozsuwa się nad całym ogrodem, zimą zamyka.",
        "Segment zachodni: długa kuchnia (8 m) z wyspą i zabudową AGD, oddzielona od salonu ścianą z dębowych lameli "
        "z przejściem – kuchnia i salon są jedną przestrzenią, ale każde ma swoje miejsce. Salon i kuchnia stoją przy samym "
        "ogrodzie, z salonu wychodzi się na patio z grillem.",
        "Segment wschodni: sypialnia z garderobą i łazienka obok niej, obie przeszklone od ogrodu od podłogi do 50 cm pod "
        "sufitem. Do łazienki wchodzi się tylko z sypialni; dla gości jest WC przy holu.",
        "Dwie klatki schodowe na końcach domu: proste schody przy ścianie z lameli prowadzą do pokoju dziecięcego, "
        "schody dwubiegowe w holu – do wieży z biurami i w dół do piwnicy. Na piętrze jeden korytarz wzdłuż całego domu "
        "(nad korytarzem parteru, z widokiem na szklany dach ogrodu) łączy oba segmenty.",
        "Wieża: dwa biura obok siebie, rozdzielone ścianą, każde z własnym wejściem z korytarza, przeszklone do 50 cm "
        "pod sufitem. Na piętrze są tylko toalety, bez łazienki.",
        "Piwnica pod segmentem wschodnim z salą kinową i pomieszczeniem technicznym – poza powierzchnią użytkową. "
        "Bryła prostopadłościenna, wszystkie ściany pod kątem prostym, bez łuków i skosów.",
    ],
    notes=dict(
        lato="Szklany dach ogrodu jest rozsunięty, wodospad szumi pod gołym niebem; grill i stół stoją na patio przy salonie, "
             "a z korytarza piętra wychodzi się na taras nad salonem.",
        zima="Dach jest zamknięty, w ogrodzie zostaje zielony mech i owocująca cytryna, a jacuzzi paruje pod szkłem; "
             "kino w piwnicy czeka na długie wieczory.",
        technologia="Ściany i piwnica z bloczków ICF (styropian zalany betonem); ściana wodospadu żelbetowa z okładziną "
                    "z łupka i hydroizolacją, pompa obiegowa w pomieszczeniu technicznym. Dach ogrodu przesuwny na stalowej "
                    "ramie; ściana z lameli z litego dębu 4 × 6 cm co 12 cm.",
    ),
)
H.max_area = 180.0          # zamówienie: do 180 m² powierzchni użytkowej (piwnica poza limitem)
H.dach_dzien = 0.0          # kadry i spacer: ogród pod zamkniętym szklanym dachem, jak na zdjęciu klienta
H.swiatla_dzien = 1.3       # spacer i panoramy: zapalone oczka w sufitach (jasne wnętrza jak na zdjęciach nieruchomości)
H.kamera_lotu = (-78.0, 44.0)  # z lotu ptaka od północy, wysoko: szklany dach ogrodu między segmentami
H.drzwi_wew = True          # skrzydła drzwi wewnętrznych w modelu 3D (uchylone do pomieszczeń)
H.wyjatki = {
    "private": "otwarte patio przy salonie – z patio widać ogród przez salon, jak w zwykłym domu",
    "modules": "taras nad salonem dostępny z holu piętra – klient nie zamawiał pokoi wokół tarasu",
}

H.level(-1, z=-3.0, h=3.0)
H.level(0, z=0.0, h=3.2)
H.level(1, z=3.2, h=3.0)

# ---------------------------------------------------------------- ogród zimowy
H.ogrod("og", "Ogród zimowy z wodospadem i jacuzzi", rect(XW, 0, XE, YG), roof_type="slide", style="jacuzzi",
        edge="solid", seed=21)

# ---------------------------------------------------------------- parter: segment zachodni
H.room("kuch", "Kuchnia", "kuchnia", rect(0, 0, XW, YL), ext={"N": "solid", "W": "windows"}, garden="glass_slide")
H.room("sal", "Salon", "salon", rect(0, YL, XW, YK), ext={"W": "solid", "S": "windows"}, garden="glass")
H.connect("kuch", "sal", "lamele", width=1.3, near=(6.9, YL))
H.stair("straight", level=0, rect=SW, up="E")
H.exit("sal", "S", at=0.225, width=2.4)          # drzwi przesuwne na patio (x 5,0–7,4)

# ---------------------------------------------------------------- parter: korytarz
H.room("kor", "Korytarz", "korytarz", rect(XW, YG, XE, YK), ext="solid")
H.connect("sal", "kor", "open")
H.exit("kor", "S", at=0.5, width=1.0, kind="door")

# ---------------------------------------------------------------- parter: segment wschodni
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(XE, 0, XD, YS), ext="band_high", garden="glass_50")
H.room("gard", "Garderoba", "garderoba", rect(XD, 0, XK, YD), ext="solid")
H.room("laz", "Łazienka", "lazienka", rect(XE, YS, XB, YG), garden="glass_50")
H.room("wc", "WC", "wc", rect(XB, YS, XC, YG))
H.room("hol", "Hol z wejściem", "hol",
       poly((XE, YG), (XC, YG), (XC, YS), (XD, YS), (XD, YD), (XK, YD), (XK, YK), (XE, YK)), ext="solid")
H.stair("U", level=0, rect=SE, up="N", landing=1.1)
H.connect("kor", "hol", "door", at=0.5)
H.connect("hol", "syp", "door", near=(22.1, YS))
H.connect("syp", "gard", "door", at=0.5)
H.connect("syp", "laz", "door", at=0.6)
H.connect("hol", "wc", "door", near=(21.0, YG))
H.entrance("hol", "E", at=0.82)

# ---------------------------------------------------------------- piętro: pokój dziecięcy, korytarz, wieża z biurami
H.room("dzieci", "Pokój dziecięcy", "pokoj", rect(1.8, 0, 6.2, YL), level=1, ext={"N": "windows", "W": "windows", "E": "windows"})
H.room("wc1", "WC", "wc", rect(6.2, 1.8, XW, YL), level=1)
H.room("hol1", "Hol piętra", "hol", poly((0.9, YL), (XW, YL), (XW, YK), (6.2, YK), (6.2, 4.6), (0.9, 4.6)), level=1,
       ext="solid")
H.room("tar", "Taras nad salonem", "taras", rect(0, 4.6, 6.2, YK), level=1)
H.room("kor1", "Korytarz piętra", "korytarz", rect(XW, YG, XE, YK), level=1, ext={"N": "glass", "S": "windows"})
H.room("biu1", "Biuro 1", "biuro", rect(XE, 1.6, 19.8, YG), level=1, ext="glass_50")
H.room("biu2", "Biuro 2", "biuro", rect(19.8, 1.6, XD, YG), level=1, ext="glass_50")
H.room("hol2", "Hol wieży", "hol", poly((XE, YG), (XD, YG), (XD, YD), (XK, YD), (XK, YK), (XE, YK)), level=1,
       ext={"S": "windows", "*": "solid"})
H.stair("U", level=-1, rect=SE, up="N", landing=1.1)

H.connect("hol1", "dzieci", "door", near=(5.65, YL))
H.connect("wc1", "hol1", "door", at=0.5)          # drzwi WC otwierane na zewnątrz
H.connect("hol1", "tar", "slide", width=0.9, near=(5.65, 4.6))      # przy wyjściu ze schodów, obok otworu
H.connect("hol1", "kor1", "open")
H.connect("kor1", "hol2", "open")
H.connect("hol2", "biu1", "door", near=(18.4, YG))
H.connect("hol2", "biu2", "door", near=(21.2, YG))

# ---------------------------------------------------------------- piwnica pod segmentem wschodnim
H.room("kino", "Sala kinowa", "kino", rect(XE, 0, XD, 5.0), level=-1)
H.room("tech", "Pomieszczenie techniczne", "techniczne", rect(XE, 5.0, 19.4, YK), level=-1)
H.room("holp", "Hol piwnicy", "hol", poly((19.4, 5.0), (XD, 5.0), (XD, YD), (XK, YD), (XK, YK), (19.4, YK)), level=-1,
       ext="solid")
H.connect("holp", "kino", "door", at=0.5)
H.connect("holp", "tech", "door", at=0.5)

H.room("patio", "Patio z grillem", "patio", rect(0, YK, XE, YK + 4.2))

# ---------------------------------------------------------------- zwiedzanie: punkt w każdym pomieszczeniu
# (klucz pokoju albo None – na zewnątrz, x, y, z oka nad podłogą; kierunki patrzenia w stopniach od północy
#  zgodnie z ruchem wskazówek zegara: początek i koniec obrotu kamery w filmie; podpis)
H.spacer = [
    ("przed", None, 29.5, 12.8, 1.65, (-88, -42), "Przed wejściem"),
    ("hol", "hol", 23.35, 6.55, 1.55, (20, -95), "Hol z wejściem"),
    ("kor", "kor", 9.0, 6.62, 1.55, (25, 100), "Korytarz przy ogrodzie"),
    ("og", "og", 14.45, 4.45, 1.55, (-62, 10), "Ogród zimowy"),
    ("sal", "sal", 7.25, 6.85, 1.55, (-115, -45), "Salon"),
    ("kuch", "kuch", 7.3, 2.85, 1.55, (-112, -40), "Kuchnia"),
    ("hol1", "hol1", 6.95, 4.15, 1.55, (-125, -15), "Schody i hol piętra"),
    ("dzieci", "dzieci", 5.35, 2.75, 1.5, (-110, -5), "Pokój dziecięcy"),
    ("wc1", "wc1", 6.85, 3.05, 1.5, (-10, 70), "WC na piętrze"),
    ("tar", "tar", 3.1, 6.85, 1.6, (35, 105), "Taras nad salonem"),
    ("kor1", "kor1", 9.0, 6.6, 1.55, (30, 105), "Korytarz piętra"),
    ("hol2", "hol2", 18.0, 6.7, 1.55, (55, 125), "Hol wieży"),
    ("biu1", "biu1", 19.25, 5.15, 1.5, (-95, -15), "Biuro 1"),
    ("biu2", "biu2", 20.45, 5.15, 1.5, (-15, 70), "Biuro 2"),
    ("syp", "syp", 21.95, 2.95, 1.55, (-120, -20), "Sypialnia"),
    ("laz", "laz", 19.05, 4.3, 1.55, (-165, -65), "Łazienka"),
    ("gard", "gard", 23.45, 1.35, 1.55, (-100, -10), "Garderoba"),
    ("wc", "wc", 21.0, 5.3, 1.5, (-25, 35), "WC dla gości"),
    ("holp", "holp", 20.4, 6.45, 1.55, (-15, 70), "Piwnica – hol"),
    ("kino", "kino", 22.3, 2.55, 1.5, (-118, -62), "Sala kinowa"),
    ("tech", "tech", 18.7, 6.55, 1.55, (-55, -125), "Pomieszczenie techniczne"),
    ("patio", "patio", 9.6, 11.1, 1.6, (-30, 45), "Patio z grillem"),
]

# ---------------------------------------------------------------- wyposażenie i wykończenie (dobrane ręcznie)
H.styl_wnetrz = dict(
    drewno="dab", front=(0.86, 0.85, 0.82), blat="kwarc", metal="czarny_metal", uchwyt="listwa", gorne="szafki",
    szafa="dab", krzeslo="tapicerowane", stol="nogi", lampa="kopula", stolik="dab", sofa=(0.58, 0.60, 0.52),
    sofa2=(0.62, 0.32, 0.21), obicie=(0.65, 0.57, 0.47), posciel=(0.88, 0.88, 0.86), koc=(0.37, 0.45, 0.53),
    akcent=[(0.78, 0.58, 0.22), (0.57, 0.63, 0.51), (0.20, 0.23, 0.31)], dywan=0, wzor="ramka", sofa_ksztalt="prosta",
)
# ściany: farba (kolor), płytki (do wysokości), ściana akcentowa (kierunek, materiał)
H.sciany = {
    "kuch": dict(farba="cieply_bialy"),
    "sal": dict(farba="greige", akcent=("W", "farba_zielen")),
    "kor": dict(farba="cieply_bialy"),
    "hol": dict(farba="cieply_bialy", akcent=("S", "farba_glina")),
    "syp": dict(farba="szalwia", akcent=("N", "farba_granat")),
    "gard": dict(farba="cieply_bialy"),
    "laz": dict(plytki="plytki_kamien", akcent=("E", "plytki_zielone")),
    "wc": dict(plytki="plytki_kamien", do=1.25, farba="cieply_bialy"),
    "dzieci": dict(farba="mieta", akcent=("E", "farba_brzoskwinia")),
    "wc1": dict(plytki="plytki_terazzo", do=1.25, farba="cieply_bialy"),
    "hol1": dict(farba="cieply_bialy"),
    "kor1": dict(farba="cieply_bialy"),
    "biu1": dict(farba="szalwia_jasna"),
    "biu2": dict(farba="greige", akcent=("E", "farba_granat")),
    "hol2": dict(farba="cieply_bialy"),
    "kino": dict(farba="grafit", panele=True, akcent=("W", "farba_grafit")),
    "tech": dict(farba="bialy"),
    "holp": dict(farba="cieply_bialy"),
}
for k, f in (("laz", "plytki_lazienka"), ("wc", "plytki_lazienka"), ("wc1", "plytki_lazienka"), ("hol", "drewno"),
             ("kor", "drewno"), ("kor1", "drewno"), ("hol1", "drewno"), ("hol2", "drewno"), ("kino", "dywan"),
             ("holp", "kamien")):
    H.get(k).floor = f

H.meble("kuch", [
    ("zabudowa", 0.80, 0.51, "S", dict(w=1.2)),                       # lodówka + słupek z piekarnikiem i mikrofalą
    ("blat", 3.10, 0.51, "S", dict(w=3.4, opcje=dict(gorne="szafki"))),  # zlew, płyta, okap, szafki górne
    ("wyspa", 2.90, 2.30, "S", dict(w=2.4, d=0.9, stools=3)),
    ("stol", 6.20, 1.75, "S", dict(n=6, w=1.8, d=0.95)),
    ("obraz", 6.20, 0.22, "S", dict(w=1.3, h=0.85, zc=1.75, seed=3)),
    ("donica", 7.55, 0.55, "S", dict(r=0.3, kind="zielen")),
])
H.meble("sal", [
    ("rtv", 0.43, 5.95, "E", dict(w=2.0)),
    ("dywan", 2.45, 5.95, "E", dict(w=2.6, d=1.9)),
    ("sofa", 3.62, 5.95, "W", dict(w=2.6, d=0.95)),
    ("stolik", 2.35, 5.95, "W", dict(w=1.1, d=0.6)),
    ("fotel", 2.10, 7.00, "N", dict(w=0.85)),
    ("lampa", 4.35, 7.10, "N"),
    ("obraz", 3.70, 7.38, "N", dict(w=1.2, h=0.8, zc=1.65, seed=7)),
    ("donica", 5.55, 3.85, "S", dict(r=0.3, kind="zielen")),
    ("fotel", 7.35, 4.15, 230.0, dict(w=0.85)),
    ("lampa", 7.70, 4.75, "N"),
])
H.meble("kor", [
    ("obraz", 9.60, 7.38, "N", dict(w=1.1, h=0.75, zc=1.55, seed=11)),
    ("obraz", 15.40, 7.38, "N", dict(w=1.1, h=0.75, zc=1.55, seed=12)),
    ("lawka", 10.00, 7.15, "N", dict(w=1.4, d=0.42)),
    ("donica", 8.45, 7.05, "S", dict(r=0.26, kind="zielen")),
    ("donica", 16.55, 7.05, "S", dict(r=0.26, kind="zielen")),
])
H.meble("hol", [
    ("komoda", 18.60, 6.06, "S", dict(w=1.2, d=0.38, h=0.8)),
    ("lustro", 18.60, 5.88, "S", dict(w=0.8, h=1.0, zc=1.55)),
    ("szafa", 20.40, 7.09, "N", dict(w=1.6, d=0.6)),
    ("wieszak", 22.10, 7.19, "N", dict(w=1.4, d=0.4)),
    ("obraz", 17.70, 7.38, "N", dict(w=0.7, h=0.9, zc=1.55, seed=5)),
    ("donica", 17.45, 6.25, "S", dict(r=0.22, kind="zielen")),
])
H.meble("syp", [
    ("dywan", 20.00, 1.95, "S", dict(w=2.6, d=2.2)),
    ("lozko", 20.00, 1.25, "S", dict(w=1.8, l=2.1)),
    ("komoda", 20.30, 3.31, "N", dict(w=1.4, d=0.45, h=0.78)),
    ("obraz", 20.30, 3.52, "N", dict(w=1.0, h=0.7, zc=1.55, seed=21)),
    ("fotel", 17.85, 0.85, -45.0, dict(w=0.85)),
    ("lampa", 17.45, 1.55, "E"),
    ("zaslona", 17.27, 0.55, "E", dict(w=0.6)),
    ("zaslona", 17.27, 3.20, "E", dict(w=0.6)),
])
H.meble("laz", [
    ("wanna", 18.05, 5.33, "N", dict(w=1.7, d=0.8, free=True)),
    ("prysznic", 19.84, 4.16, "W", dict(w=1.0, d=1.0)),
    ("umywalki", 20.09, 5.20, "W", dict(w=0.9, d=0.48, n=1)),
    ("lustro", 20.32, 5.20, "W", dict(w=0.7, h=0.9, zc=1.55)),
    ("wc", 19.35, 5.40, "N"),
])
H.meble("wc", [
    ("wc", 20.95, 4.00, "S"),
    ("umywalki", 21.25, 4.62, "W", dict(w=0.45, d=0.32, n=1)),
    ("lustro", 21.42, 4.62, "W", dict(w=0.4, h=0.6, zc=1.5)),
])
H.meble("dzieci", [
    ("lozko", 5.65, 1.20, "S", dict(w=0.9, l=2.0, nightstands=False, wariant="dziecko")),
    ("biurko", 3.95, 0.50, "S", dict(w=1.2, d=0.6)),
    ("szafa", 4.20, 3.03, "N", dict(w=1.2, d=0.6)),
    ("regal_niski", 2.19, 1.40, "E", dict(w=1.0)),
    ("namiot", 2.62, 2.75, "E", dict(s_=1.0)),
    ("dywan", 3.80, 1.80, "S", dict(w=1.6, d=1.1, wariant="dziecko")),
    ("pufa", 4.45, 2.30, "N", dict(r=0.33)),
    ("obraz", 6.12, 1.20, "W", dict(w=0.6, h=0.8, zc=1.75, seed=31, wariant="dziecko")),
    ("obraz", 2.02, 2.80, "E", dict(w=0.5, h=0.5, zc=1.85, seed=32, wariant="dziecko")),
])
H.meble("wc1", [
    ("wc", 7.46, 2.55, "W"),
    ("umywalki", 6.62, 2.18, "S", dict(w=0.45, d=0.32, n=1)),
    ("lustro", 6.62, 2.02, "S", dict(w=0.4, h=0.6, zc=1.5)),
])
H.meble("hol1", [
    ("obraz", 7.97, 4.55, "W", dict(w=0.9, h=0.6, zc=1.55, seed=41)),
    ("donica", 7.55, 7.00, "S", dict(r=0.25, kind="zielen")),
])
H.meble("tar", [
    ("lezak", 1.00, 6.25, "N"),
    ("lezak", 1.95, 6.25, "N"),
    ("stolik_okragly", 3.30, 6.20, "S", dict(r=0.35)),
    ("donica", 0.45, 7.20, "S", dict(r=0.3, kind="zielen")),
    ("donica", 5.55, 7.20, "S", dict(r=0.3, kind="zielen")),
])
H.meble("kor1", [
    ("lawka", 12.50, 7.15, "N", dict(w=1.6, d=0.42)),
    ("donica", 8.50, 7.05, "S", dict(r=0.26, kind="zielen")),
    ("donica", 16.55, 7.05, "S", dict(r=0.26, kind="zielen")),
])
H.meble("biu1", [
    ("biurko", 17.50, 3.30, "E", dict(w=1.5, d=0.7)),
    ("regal", 19.55, 3.30, "W", dict(w=1.8, d=0.36)),
    ("fotel", 18.70, 2.30, 200.0, dict(w=0.8)),
    ("donica", 17.55, 2.10, "S", dict(r=0.22, kind="zielen")),
    ("dywan", 18.45, 3.30, "S", dict(w=1.6, d=2.2)),
])
H.meble("biu2", [
    ("biurko", 21.20, 2.15, "S", dict(w=1.5, d=0.7)),
    ("regal", 20.05, 3.70, "E", dict(w=1.6, d=0.36)),
    ("sofa", 22.07, 3.90, "W", dict(w=1.7, d=0.85)),
    ("obraz", 22.52, 3.90, "W", dict(w=1.0, h=0.7, zc=1.6, seed=51)),
    ("donica", 22.20, 2.20, "S", dict(r=0.22, kind="zielen")),
])
H.meble("hol2", [
    ("lawka", 18.60, 7.15, "N", dict(w=1.2, d=0.42)),
    ("donica", 21.70, 7.05, "S", dict(r=0.25, kind="zielen")),
])
H.meble("kino", [
    ("ekran", 17.32, 2.55, "E", dict(w=3.2)),
    ("glosnik", 17.42, 0.55, "E"),
    ("glosnik", 17.42, 4.55, "E"),
    ("fotele_kino", 19.80, 2.55, "W", dict(n=3)),
    ("fotele_kino", 21.55, 2.55, "W", dict(n=3)),
    ("projektor", 21.90, 2.55, "W"),
])
H.meble("tech", [
    ("pompa", 17.62, 5.45, "E", dict(w=0.7, d=0.6)),
    ("zbiornik", 18.85, 5.45, "S"),
    ("pralka", 17.55, 6.30, "E"),
    ("pralka", 17.55, 6.95, "E"),
])
H.meble("holp", [
    ("wino", 20.80, 7.20, "N", dict(w=1.8)),
])
H.meble("patio", [
    ("grill", 15.20, 8.17, "S", dict(w=2.4, d=0.7)),
    ("stol", 10.50, 9.80, "S", dict(n=6, w=2.0, d=0.95)),
    ("sofa", 3.00, 11.20, "N", dict(w=2.4, d=0.9)),
    ("stolik", 3.00, 10.25, "N", dict(w=1.0, d=0.6)),
    ("fotel", 1.30, 10.30, "E", dict(w=0.8)),
    ("lezak", 6.80, 10.80, "N"),
    ("lezak", 7.70, 10.80, "N"),
    ("donica", 0.45, 8.30, "S", dict(r=0.35, kind="zielen")),
    ("donica", 8.50, 8.25, "S", dict(r=0.3, kind="zielen")),
    ("donica", 16.55, 11.35, "S", dict(r=0.35, kind="zielen")),
])

# ---------------------------------------------------------------- patio z grillem i teren
H.path(rect(XK + 0.2, 6.2, XK + 6.0, 7.4))
H.tree(-4.0, 2.0, "brzoza")
H.tree(28.5, 1.5, "klon")
H.tree(4.0, 15.0, "lipa")
H.tree(21.0, 13.5, "brzoza")
H.cut("A–A", (12.5, -2.5), (12.5, 12.5))
H.cut("B–B", (-2.0, 4.6), (27.0, 4.6))
