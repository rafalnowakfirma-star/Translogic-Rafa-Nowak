"""P09 · Pawilony – cztery drewniane pawilony i mały pawilon wejściowy wokół ogrodu leśnego,
połączone szklanym krużgankiem sezonowym (patio_sezonowe) zamiast ogrzewanego korytarza.

Układ krzyża: belki od północy (wejście, salon) i od południa (biuro), ramiona na wschód (nocny)
i zachód (gościnny z sauną). Wysokie są tylko bryły od północy, żeby nie zasłaniały ogrodu.
"""
from silnik import House, rect, union

# ogród 10 × 9 m, krużganek 2,5 m dookoła
GX1, GY1, GX2, GY2 = 10.0, 10.0, 20.0, 19.0
KW = 2.5
X0, Y0, X1, Y1 = GX1 - KW, GY1 - KW, GX2 + KW, GY2 + KW   # 7,5 / 7,5 / 22,5 / 21,5

# krużganek: dwa ramiona w kształcie L (północ+zachód, południe+wschód) – bez dziur w wielokątach,
# a podpisy mieszczą się w szerokich odcinkach
KRU_NW = union(rect(X0, Y0, X1, GY1), rect(X0, GY1, GX1, GY2))
KRU_SE = union(rect(X0, GY2, X1, Y1), rect(GX2, GY1, X1, GY2))

H = House(
    "p09", "Pawilony",
    "Cztery drewniane pawilony – dzienny, nocny, pracy i gościnny z sauną – wokół ogrodu z brzozami pod dachem z lameli szklanych. Łączy je krużganek od strony ogrodu, zimą zamknięty szklaną harmonijką, latem otwarty.",
    style=dict(fasada="drewno", dach="sedum"),
    concept=[
        "Pawilony stoją osobno: dzienny od północy, pracy od południa, a nocny i gościnny z sauną wychodzą jak dwa ramiona na wschód i zachód; między nimi zostają patio kuchni z daszkiem, taras sypialni i taras sauny.",
        "Pawilony łączy krużganek od strony ogrodu, a nie ogrzewany korytarz: ma pełny dach i ściany ze szklanej harmonijki, więc zimą jest zamkniętym buforem jak oranżeria, a latem zadaszoną werandą.",
        "To odpowiedź na pytanie o korytarze od zewnątrz: taki korytarz zabrałby pokojom widok i trzeba by go grzać, a tu każdy pokój ma okna na krajobraz – biuro szkło z obu stron, sypialnia na końcu wschodniego ramienia dwie szklane ściany.",
        "Wejście to osobny mały pawilon z amfiladą: wiatrołap z WC, szatnia i wysoka herbaciarnia, z której wychodzi się na krużganek i ścieżką w głąb ogrodu.",
        "Dwie kondygnacje mają tylko bryły od północy – salon z kuchnią i herbaciarnia – więc od południa, wschodu i zachodu nic wysokiego nie zasłania ogrodowi słońca.",
        "Ogród 10 × 9 m ma 7 m wysokości, żeby zmieściły się brzozy; przykrywają go obrotowe lamele szklane, które latem stają pionowo i wypuszczają ciepłe powietrze.",
    ],
    notes=dict(
        lato="Lamele nad ogrodem stają pionowo, a harmonijki krużganka składają się, więc pawilony wychodzą wprost na ogród i dziedzińce, a krużganek jest zadaszoną werandą.",
        zima="Harmonijki i lamele są zamknięte; nieogrzewany krużganek nagrzewa słońce i ciepło z pawilonów, więc przejście jest chłodne, ale osłonięte od wiatru, a pawilony tracą mniej ciepła, bo od strony ogrodu mają bufor zamiast mrozu.",
        technologia="Pawilony z prefabrykowanych modułów szkieletowych drewnianych – ściany, stropy i dach przyjeżdżają z fabryki jako gotowe skrzynie i stają na płycie fundamentowej w kilka dni. Krużganek ze stalowych słupów i belek ze szklanymi harmonijkami, dach ogrodu z systemowych lameli szklanych na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

H.ogrod("og", "Ogród leśny", rect(GX1, GY1, GX2, GY2), levels=2, roof_type="louvre", style="las",
        edge="glass", seed=4, label_at=(16.4, 14.2))

# krużganek (patio sezonowe): dach pełny, ale podany wielokątem (= obrys) – wtedy jest osobną, niższą płytą,
# a każdy pawilon ma własny dach z attyką (przy roof="full" dachy parterowych pawilonów zlewają się z krużgankiem)
H.room("kn", "Krużganek", "patio_sezonowe", KRU_NW, roof=KRU_NW, furn=False)
H.room("ks", "Krużganek", "patio_sezonowe", KRU_SE, roof=KRU_SE, furn=False)

# pawilon wejściowy – amfilada: wiatrołap → szatnia → herbaciarnia → krużganek
H.room("wia", "Wiatrołap", "wiatrolap", rect(9.0, -0.5, 13.5, 1.7), ext={"N": "slits", "W": "solid", "E": "slits"})
H.room("sza", "Szatnia", "garderoba", rect(9.0, 1.7, 11.8, 4.3), ext="solid")
H.room("wc", "WC", "wc", rect(11.8, 1.7, 13.5, 4.3), label_at=(12.95, 2.95))
H.room("her", "Herbaciarnia", "herbaciarnia", rect(9.0, 4.3, 13.5, Y0), levels=2,
       ext={"S": "glass", "W": "windows", "E": "slits", "N": "solid"})

# pawilon dzienny (belka od północy, 2 kondygnacje)
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(15.5, 1.0, 26.5, Y0), levels=2,
       ext={"S": "glass_slide", "N": "slits", "E": "glass", "W": "band_high"}, kitchen_at="W")
H.room("pat", "Patio", "patio", rect(X1, Y0, 28.0, 11.5), roof=rect(X1, Y0, 26.5, 9.8))

# pawilon nocny (palec na wschód)
H.room("pra", "Pralnia", "pralnia", rect(X1, 11.5, 25.5, 14.0), ext="band_high")
H.room("gar", "Garderoba", "garderoba", rect(X1, 14.0, 25.5, 18.5))
H.room("laz", "Łazienka", "lazienka", rect(25.5, 11.5, 31.5, 14.5), ext={"N": "band_high", "E": "windows"})
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(25.5, 14.5, 31.5, 18.5),
       ext={"E": "glass_slide", "S": "glass_slide"})
H.room("tsy", "Taras sypialni", "taras", rect(25.5, 18.5, 31.5, 21.5))

# pawilon pracy (belka od południa)
H.room("biu", "Biuro", "biuro", rect(GX1, Y1, GX2, 26.5),
       ext={"N": "glass_slide", "S": "glass_slide", "E": "band_high", "W": "band_high"})

# pawilon gościnny z sauną (palec na zachód)
H.room("gos", "Pokój gościnny", "gosc", rect(1.0, 10.5, X0, 14.0),
       ext={"E": "glass_slide", "W": "windows", "N": "band_high"})
H.room("lzg", "Łazienka", "lazienka", rect(4.5, 14.0, X0, 17.5), ext="band_high")
H.room("sau", "Sauna", "sauna", rect(1.0, 14.0, 4.5, 17.5), ext={"W": "band", "S": "solid"})
H.room("tsa", "Taras sauny", "taras", rect(1.0, 17.5, X0, 20.5))

# połączenia
H.connect("wia", "sza", "door", at=0.75)
H.connect("wia", "wc", "door")
H.connect("sza", "her", "door", at=0.75)
H.connect("her", "kn", "door", at=0.88)
H.connect("pat", "kn", "fold")
H.connect("pat", "ks", "fold")
H.connect("ks", "pra", "door")
H.connect("ks", "gar", "door")
H.connect("gar", "syp", "door", at=0.8)
H.connect("syp", "laz", "door", at=0.12)
H.connect("gos", "lzg", "door")
H.connect("kn", "lzg", "door")
H.connect("lzg", "sau", "door")
H.connect("sau", "tsa", "door")
H.connect("tsa", "kn", "fold")
# krużganek – ogród: szklana harmonijka (na piętrze latarnia ma stałe szkło)
H.connect("kn", "og", "fold")
H.connect("ks", "og", "fold")
# główne przejścia do ogrodu w harmonijce (wyznaczają ścieżki)
H.window("og", "N", at=0.25, width=1.4, sill=0.0, head=2.25, kind="slide")
H.window("og", "S", at=0.6, width=1.4, sill=0.0, head=2.25, kind="slide")

H.entrance("wia", "N")
H.exit("pra", "N", kind="door")
H.path(rect(10.55, -6.5, 11.95, -0.7))
# obejście: rzut piętra nie rysuje zadaszeń patio (roof=wielokąt) z parteru – obrys krużganka i daszka
# jako ścieżka pokazuje je na rzucie piętra (na parterze przykrywa je posadzka, w 3D leży pod płytą)
H.path(KRU_NW)
H.path(KRU_SE)
H.path(rect(X1, Y0, 26.5, 9.8))
H.tree(14.5, 3.5, "brzoza", r=1.0)
H.tree(33.0, 6.0, "klon")
H.tree(-2.5, 25.0, "lipa")
H.tree(28.5, 26.5, "sosna")
H.cut("A–A", (16.25, -1.0), (16.25, 27.5))
H.cut("B–B", (0.0, 16.0), (32.5, 16.0))
