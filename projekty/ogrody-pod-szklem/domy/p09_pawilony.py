"""P09 · Pawilony – cztery drewniane pawilony wokół ogrodu leśnego, połączone szklanym krużgankiem sezonowym."""
from silnik import House, rect, union

# ogród 10 × 9 m, krużganek 2,5 m dookoła
GX1, GY1, GX2, GY2 = 10.0, 10.0, 20.0, 19.0
KW = 2.5
X0, Y0, X1, Y1 = GX1 - KW, GY1 - KW, GX2 + KW, GY2 + KW   # 7,5 / 7,5 / 22,5 / 21,5

# krużganek: dwa ramiona w kształcie L (północ+zachód, południe+wschód)
KRU_NW = union(rect(X0, Y0, X1, GY1), rect(X0, GY1, GX1, GY2))
KRU_SE = union(rect(X0, GY2, X1, Y1), rect(GX2, GY1, X1, GY2))

H = House(
    "p09", "Pawilony",
    "Cztery drewniane pawilony – dzienny, nocny, pracy i gościnny z sauną – stoją wokół ogrodu leśnego przesunięte jak skrzydła wiatraka. Łączy je szklany krużganek od strony ogrodu, zimą zamknięty, latem otwarty.",
    style=dict(fasada="drewno", dach="sedum"),
    concept=["(szkic)"],
    notes=dict(lato="(szkic)", zima="(szkic)", technologia="(szkic)"),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

H.ogrod("og", "Ogród leśny", rect(GX1, GY1, GX2, GY2), levels=2, roof_type="louvre", style="las",
        edge="glass", seed=4, label_at=(16.6, 18.0))

# krużganek (patio sezonowe): pełne zadaszenie jako osobna płyta, harmonijka szklana
H.room("kn", "Krużganek", "patio_sezonowe", KRU_NW, roof=KRU_NW)
H.room("ks", "Krużganek", "patio_sezonowe", KRU_SE, roof=KRU_SE)

# pawilon wejściowy – amfilada: wiatrołap → szatnia → herbaciarnia → krużganek
H.room("wia", "Wiatrołap", "wiatrolap", rect(9.0, -0.5, 13.5, 1.7), ext={"N": "slits", "W": "solid", "E": "slits"})
H.room("sza", "Szatnia", "garderoba", rect(9.0, 1.7, 11.8, 4.3), ext="solid")
H.room("wc", "WC", "wc", rect(11.8, 1.7, 13.5, 4.3))
H.room("her", "Herbaciarnia", "herbaciarnia", rect(9.0, 4.3, 13.5, Y0),
       ext={"S": "glass", "W": "windows", "E": "slits"})

# pawilon dzienny (2 kondygnacje)
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(15.5, 1.0, 26.5, Y0), levels=2,
       ext={"S": "glass_slide", "N": "slits", "E": "glass", "W": "solid"}, kitchen_at="W")
H.room("pat", "Patio", "patio", rect(X1, Y0, 28.0, 12.0), roof=rect(X1, Y0, 26.5, 10.0))

# pawilon nocny
H.room("pra", "Pralnia", "pralnia", rect(X1, 12.0, 28.0, 14.2), ext="band_high")
H.room("laz", "Łazienka", "lazienka", rect(X1, 14.2, 28.0, 17.2), ext="band_high")
H.room("gar", "Garderoba", "garderoba", rect(X1, 17.2, 28.0, 19.0))
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(X1, 19.0, 28.0, 24.0),
       ext={"E": "glass_slide", "W": "solid", "S": "windows"})
H.room("tsy", "Taras", "taras", rect(17.0, Y1, X1, 24.0))

# pawilon pracy
H.room("biu", "Biuro", "biuro", rect(X0, Y1, 17.0, 26.5),
       ext={"N": "glass_slide", "S": "glass_slide", "E": "solid"})
H.room("prc", "Pracownia", "pracownia", rect(4.0, Y1, X0, 26.5), levels=2,
       ext={"W": "windows", "S": "windows", "N": "solid", "E": "band_high"})

# pawilon gościnny z sauną
H.room("gos", "Pokój gościnny", "gosc", rect(2.0, GY1, X0, 14.5),
       ext={"E": "glass_slide", "W": "windows", "N": "windows"})
H.room("lzg", "Łazienka", "lazienka", rect(2.0, 14.5, X0, 16.5), ext="band_high")
H.room("sau", "Sauna", "sauna", rect(2.0, 16.5, X0, 18.5), ext={"E": "glass", "W": "band", "S": "solid"})
H.room("tsa", "Taras sauny", "taras", rect(2.0, 18.5, X0, Y1), label_at=(3.2, 19.15))

# połączenia
H.connect("wia", "sza", "door", at=0.75)
H.connect("wia", "wc", "door")
H.connect("sza", "her", "door", at=0.75)
H.connect("her", "kn", "door", at=0.88)
H.connect("pat", "kn", "fold")
H.connect("pat", "ks", "fold")
H.connect("ks", "pra", "door")
H.connect("ks", "gar", "door")
H.connect("gar", "laz", "slide")
H.connect("gar", "syp", "door")
H.connect("syp", "tsy", "slide")
H.connect("tsy", "ks", "fold")
H.connect("biu", "prc", "wide")
H.connect("gos", "lzg", "door")
H.connect("kn", "lzg", "door")
H.connect("lzg", "sau", "door")
H.connect("sau", "tsa", "door")
H.connect("tsa", "kn", "fold")
H.connect("tsa", "ks", "fold")
# krużganek – ogród: szklana harmonijka (na piętrze latarnia ma stałe szkło)
H.connect("kn", "og", "fold")
H.connect("ks", "og", "fold")
# główne przejścia do ogrodu w harmonijce (wyznaczają ścieżki)
H.window("og", "N", at=0.25, width=1.4, sill=0.0, head=2.25, kind="slide")
H.window("og", "S", at=0.8, width=1.4, sill=0.0, head=2.25, kind="slide")

H.entrance("wia", "N")
H.exit("pra", "E", kind="door")
# obrys krużganka na rzucie dachu (silnik nie rysuje tam zadaszeń patio)
H.path(KRU_NW)
H.path(KRU_SE)
H.path(rect(10.55, -6.5, 11.95, -0.7))
H.tree(14.5, 3.5, "brzoza", r=1.0)
H.tree(32.0, 3.0, "klon")
H.tree(-2.0, 27.0, "lipa")
H.tree(31.0, 29.0, "sosna")
H.cut("A–A", (16.25, -1.0), (16.25, 27.5))
H.cut("B–B", (0.5, 12.5), (29.5, 12.5))
