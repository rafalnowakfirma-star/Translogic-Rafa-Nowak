"""P01 · Krużganek – kwadrat wokół ogrodu-latarni, salon na dwie kondygnacje."""
from silnik import House, rect, poly

H = House(
    "p01", "Krużganek",
    "Kwadratowy dom wokół ogrodu, który wystaje ponad dachy jak szklana latarnia. Wszystkie pokoje otwierają się na ogród, więc ogród jest głównym holem domu.",
    style=dict(fasada="tynk", dach="sedum", akcent="dab"),
    concept=[
        "Ogród 8 × 8 m pod przesuwnym szklanym dachem na wysokości 7 m. Ściany ponad niskimi skrzydłami też są ze szkła, dlatego światło wpada do ogrodu ze wszystkich stron.",
        "Biuro w skrzydle zachodnim ma szkło od ogrodu i od strony pól. Biurko stoi między dwoma pejzażami.",
        "Od frontu zamiast korytarza jest amfilada: wiatrołap, galeria sztuki wzdłuż ogrodu i pracownia, przez którą przechodzi się do biura.",
        "Salon z kuchnią ma 6,5 m wysokości i przez szklaną ścianę wychodzi na patio. Połowa patio ma daszek, druga połowa jest pod gołym niebem.",
        "Sypialnia od wschodu ma całą ścianę ze szkła na prywatny ogród poranny. Garderoba jest przelotowa i prowadzi do łazienki.",
    ],
    notes=dict(
        lato="Połowa szklanego dachu zsuwa się nad drugą i ogród staje się otwartym dziedzińcem; szklane ściany biura i salonu rozsuwają się na całą szerokość.",
        zima="Dach jest zamknięty, a ogród działa jak bufor: grzeje go słońce wpadające z góry, a pokoje wokół tracą mniej ciepła, bo od środka nie mają mrozu.",
        technologia="Ściany z bloczków silikatowych na cienką spoinę, stropy i dach z prefabrykowanych płyt kanałowych, dach szklany systemowy na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

H.ogrod("og", "Ogród zimowy", rect(6, 6, 14, 14), levels=2, roof_type="slide", style="japonski", seed=3)
# front – amfilada
H.room("pral", "Pralnia", "pralnia", rect(6, 0, 8.5, 2.6))
H.room("wia", "Wiatrołap", "wiatrolap", rect(8.5, 0, 11.5, 2.6))
H.room("wc", "WC", "wc", rect(11.5, 0, 14, 2.6))
H.room("gal", "Galeria", "galeria", rect(6, 2.6, 14, 6), ext="solid")
H.room("pra", "Pracownia", "pracownia", rect(0, 0, 6, 6), ext={"N": "band_high", "W": "windows"})
# zachód – biuro przeszklone z obu stron
H.room("biu", "Biuro", "biuro", rect(0, 6, 6, 14), ext={"W": "glass_slide"}, garden="glass_slide")
# południe – salon z kuchnią na dwie kondygnacje i patio
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(6, 14, 20, 20), levels=2,
       ext={"S": "glass_slide", "E": "windows", "W": "glass_slide"}, kitchen_at="E")
H.room("pat", "Patio", "patio", rect(0, 14, 6, 20), roof=rect(0, 14, 6, 17.4))
# wschód – sypialnia i strefa gościnna
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(14, 9.5, 20, 14), ext={"E": "glass_slide", "S": "solid"})
H.room("gar", "Garderoba", "garderoba", rect(14, 6, 17, 9.5), ext="solid")
H.room("laz", "Łazienka", "lazienka", rect(17, 6, 20, 9.5), ext={"E": "band_high"})
H.room("gos", "Pokój gościnny", "gosc", rect(14, 0, 20, 4))
H.room("hol", "Hol", "hol", rect(14, 4, 17, 6), ext="solid")
H.room("lzg", "Łazienka", "lazienka", rect(17, 4, 20, 6))

H.connect("wia", "gal", "wide")
H.connect("wia", "wc", "door")
H.connect("wia", "pral", "door")
H.connect("gal", "pra", "wide")
H.connect("pra", "biu", "double")
H.connect("biu", "pat", "slide")
H.connect("gal", "hol", "wide")
H.connect("hol", "gos", "door")
H.connect("hol", "lzg", "door")
H.connect("syp", "gar", "door")
H.connect("gar", "laz", "slide")

H.entrance("wia", "N")
H.path(rect(9.3, -6, 10.7, -0.2))
H.path(rect(20.2, 9.6, 24, 14))
H.tree(23.5, 5.0, "brzoza")
H.tree(-3.0, 22.5, "klon")
H.tree(26.0, 20.0, "lipa")
H.cut("A–A", (10.0, -2.0), (10.0, 22.0))
