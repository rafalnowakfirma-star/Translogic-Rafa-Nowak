"""P02 · Wieża – dom wokół oranżerii z biurem na szczycie wieży przeszklonym z trzech stron."""
from silnik import House, rect

H = House(
    "p02", "Wieża",
    "Parterowy dom wokół oranżerii, nad którym stoi trzykondygnacyjna wieża. Na jej szczycie jest biuro przeszklone z trzech stron, 7 m nad ogrodem.",
    style=dict(fasada="beton", dach="sedum", akcent="stal"),
    concept=[
        "Biuro na szczycie wieży ma szkło od wschodu, południa i zachodu. Czwarta, północna ściana jest pełna i mieści schody oraz regały, więc biurko stoi w panoramie, ale nie w pełnym słońcu.",
        "Pod biurem, na pierwszym piętrze wieży, jest pokój gościnny z widokiem ponad dachy, a na parterze hol z klatką schodową.",
        "Oranżeria 10 × 6 m ma dach z obrotowych lameli szklanych: zimą zamkniętych, latem uchylonych.",
        "Amfilada od wejścia: wiatrołap, biblioteka, garderoba, sypialnia. Druga droga prowadzi przez hol wieży i pracownię do salonu.",
        "Salon z kuchnią na dwie kondygnacje ciągnie się wzdłuż całej południowej elewacji i kończy patio z daszkiem.",
    ],
    notes=dict(
        lato="Lamele dachu oranżerii obracają się do pionu i wypuszczają ciepłe powietrze, a biuro w wieży przewietrza się przez otwierane skrzydła w narożnikach.",
        zima="Lamele są zamknięte i oranżeria zbiera ciepło od słońca. Pełna północna ściana wieży osłania biuro przed wiatrem.",
        technologia="Wieża jako sztywny żelbetowy trzon ze schodami, reszta z bloczków ICF (styropian zalany betonem), stropy z prefabrykowanych płyt.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)
H.level(2, z=6.8, h=3.4)

H.ogrod("og", "Oranżeria", rect(6, 5, 16, 11), roof_type="louvre", style="oranzeria", seed=5)
# skrzydło nocne (zachód)
H.room("laz", "Łazienka", "lazienka", rect(0, 0, 3.4, 5), ext={"N": "band_high", "W": "band_high"})
H.room("gar", "Garderoba", "garderoba", rect(3.4, 0, 6, 5), ext="band_high")
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(0, 5, 6, 11), ext={"W": "glass_slide"})
# front (północ)
H.room("bib", "Biblioteka", "biblioteka", rect(6, 0, 12, 5), ext="slits")
H.room("wia", "Wiatrołap", "wiatrolap", rect(12, 0, 16, 5), ext="slits")
# wieża
H.room("hol", "Hol wieży", "hol", rect(16, 0, 21, 5), ext={"N": "slits", "E": "windows_sq"})
H.room("gos", "Pokój gościnny", "gosc", rect(16, 0, 21, 5), level=1, ext={"N": "slits", "E": "glass", "S": "windows", "W": "windows"})
H.room("biu", "Biuro w wieży", "biuro", rect(16, 0, 21, 5), level=2, ext={"N": "solid", "E": "glass", "S": "glass", "W": "glass"})
H.stair("U", level=0, rect=(16.35, 0.35, 20.65, 2.6), up="E")
H.stair("U", level=1, rect=(16.35, 0.35, 20.65, 2.6), up="E")
# wschód
H.room("pra", "Pracownia", "pracownia", rect(16, 5, 21, 11), ext={"E": "windows"})
# południe – salon i patio
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(6, 11, 21, 16), levels=2,
       ext={"S": "glass_slide", "E": "windows", "W": "glass_slide", "N": "band"}, kitchen_at="E")
H.room("pat", "Patio", "patio", rect(0, 11, 6, 16), roof=rect(0, 11, 6, 13.6))

H.connect("wia", "bib", "wide")
H.connect("bib", "gar", "door")
H.connect("gar", "laz", "slide")
H.connect("gar", "syp", "door")
H.connect("wia", "hol", "wide")
H.connect("hol", "pra", "double")
H.connect("pra", "sal", "wide")
H.connect("sal", "pat", "slide")
H.entrance("wia", "N")
H.path(rect(13.3, -6, 14.7, -0.2))
H.path(rect(-4, 11.2, 0, 16))
H.tree(-3.5, 3.0, "brzoza")
H.tree(25.0, 13.0, "klon")
H.tree(24.5, -2.5, "lipa")
H.cut("A–A", (18.5, -2.0), (18.5, 18.0))
