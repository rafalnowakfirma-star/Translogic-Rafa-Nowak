"""P14 · Zygzak – łańcuch stalowych modułów przesuniętych schodkowo wokół dwóch ogrodów: zimowego pod szkłem i letniego pod niebem."""
from silnik import House, rect, poly

H = House(
    "p14", "Zygzak",
    "Dziesięć prostokątnych modułów ustawionych w łańcuch, każdy przesunięty o 1,5 m względem sąsiada, obiega dwa ogrody: zimowy pod harmonijkowym szklanym dachem i letni dziedziniec bez dachu. Latem szklana harmonijka między nimi składa się i oba ogrody stają się jednym.",
    style=dict(fasada="corten", dach="zwir", akcent="stal"),
    concept=[
        "Dom to zygzak: kolejne moduły o szerokości 4 m są przesunięte na przemian do środka i na zewnątrz o 1,5 m, więc obie elewacje – zewnętrzna i od ogrodu – są ząbkowane, a w każdym załamaniu powstaje nisza na drzwi, ławkę albo drzewo.",
        "W środku są dwa ogrody obok siebie. Zachodni, zimowy, ma 55 m² i szklany dach harmonijkowy 7 m nad posadzką, pod którym rosną palmy. Wschodni, letni dziedziniec z drewnianym pokładem, nie ma dachu. Dzieli je 8 m szklanej harmonijki: zimą zamknięta, latem złożona przy słupach.",
        "Biuro stoi w module wschodnim i jest przeszklone z obu stron: od letniego dziedzińca (szkło przesuwne) i od pól na wschodzie (szkło stałe). Nad biurem, w tym samym module, jest sypialnia główna z całą wschodnią ścianą ze szkła.",
        "Od wejścia idzie się przez kolejne moduły bez korytarza: wiatrołap, biblioteka na dwie kondygnacje, pokój muzyczny otwierany na dziedziniec i hol ze schodami kręconymi – albo w drugą stronę: herbaciarnia przy palmach, wysoka pracownia i patio sezonowe aż do salonu. Pętla zamyka się wokół ogrodów.",
        "Salon z kuchnią ma 6,5 m wysokości i trzy szklane ściany: na ogród zimowy, na letni dziedziniec i na południe. Od zachodu przylega patio sezonowe – szklany moduł, który zimą jest zamkniętą werandą, a latem całkiem otwartym tarasem.",
        "Moduły mają różne wysokości: wieża biblioteki, pracownia, część wschodnia i salon są dwukondygnacyjne, reszta parterowa, dlatego bryła schodkuje się także w pionie. Na dachu pokoju muzycznego jest taras dostępny z górnej galerii.",
    ],
    notes=dict(
        lato="Harmonijka między ogrodami i połowa szklanego dachu są złożone, więc palmy stoją pod otwartym niebem razem z dziedzińcem; patio sezonowe i szklane ściany salonu rozsuwają się na całą szerokość.",
        zima="Harmonijka i dach są zamknięte: ogród zimowy jest ogrzewaną halą z palmami, a dziedziniec letni zostaje na zewnątrz i chroni wschodnie pokoje przed wiatrem; patio sezonowe działa jak zamknięta weranda.",
        technologia="Prefabrykowane moduły stalowe 4 × 4,5–7 m (rama z profili HEB, strop z blachy trapezowej z nadbetonem, ściany warstwowe), ustawiane z przesunięciem jak klocki; elewacja z blachy cortenowskiej na ruszcie. Salon to jedyna przestrzeń poza modułem: stalowe kratownice rozpięte między sąsiednimi modułami. Dach szklany na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

# dwa ogrody w środku: zimowy pod szkłem (zachód) i letni dziedziniec (wschód)
H.ogrod("og", "Ogród zimowy",
        poly((5.5, 5.5), (6, 5.5), (6, 4), (11, 4), (11, 13.5), (4.5, 13.5), (4.5, 10), (5.5, 10)),
        levels=2, roof_type="fold", style="tropikalny", edge="fold", seed=14)
H.room("dz", "Dziedziniec letni", "patio",
       poly((11, 5.5), (15.5, 5.5), (15.5, 6.5), (17, 6.5), (17, 13.5), (11, 13.5)), roof=None)

# --- północ: front, amfilada (moduły 1–3)
H.room("pral", "Pralnia", "pralnia", rect(0, 1.5, 2, 5.5))
H.room("wia", "Wiatrołap", "wiatrolap", poly((2, 1.5), (6, 1.5), (6, 5.5), (3.6, 5.5), (3.6, 3.5), (2, 3.5)), ext="slits")
H.room("wc", "WC", "wc", rect(2, 3.5, 3.6, 5.5))
H.room("bib", "Biblioteka", "biblioteka", rect(6, 0, 11, 4), levels=2, ext={"N": "band_high", "W": "solid", "E": "solid"})
H.room("muz", "Pokój muzyczny", "muzyczny", rect(11, 1.5, 15.5, 5.5), ext={"N": "band_high", "S": "glass_slide"}, garden="glass")
# --- wschód: hol ze schodami, biuro, spiżarnia (moduły 4–6)
H.room("hol", "Hol", "hol", rect(15.5, 0, 19.5, 6.5), ext={"N": "solid", "E": "windows_sq", "W": "slits", "S": "glass"})
H.stair("spiral", level=0, center=(17.85, 4.55), r=1.15, start=180, sweep=320, n=16)
H.room("biu", "Biuro", "biuro", rect(17, 6.5, 21, 13.5), ext={"E": "glass", "W": "glass_slide", "N": "solid", "S": "solid"})
H.room("spiz", "Spiżarnia", "spizarnia", rect(15.5, 13.5, 19.5, 16))
# --- południe: wysoki salon i patio sezonowe (moduły 7–8)
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(4.5, 13.5, 15.5, 19), levels=2,
       ext={"S": "glass_slide", "W": "glass_slide", "E": "solid", "N": "glass_slide"}, kitchen_at="E")
H.room("ps", "Patio sezonowe", "patio_sezonowe", rect(0.5, 15, 4.5, 20))
# --- zachód: wysoka pracownia i herbaciarnia przy palmach (moduły 9–10)
H.room("prac", "Pracownia", "pracownia", rect(0, 10, 4.5, 15), levels=2, ext={"W": "windows", "N": "solid", "S": "glass_slide"})
H.room("herb", "Herbaciarnia", "herbaciarnia", rect(1.5, 5.5, 5.5, 10), ext={"W": "band"}, garden="glass")

# --- piętro: galeria nad holem, garderoba, sypialnia, łazienka, taras na dachu pokoju muzycznego
H.room("gal", "Galeria", "galeria", rect(15.5, 0, 19.5, 6.5), level=1, ext={"N": "solid", "E": "windows_sq", "W": "glass", "S": "glass"})
H.room("gard", "Garderoba", "garderoba", rect(17, 6.5, 21, 8.5), level=1)
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(17, 8.5, 21, 13.5), level=1, ext={"E": "glass_slide", "W": "glass", "S": "solid"})
H.room("laz", "Łazienka", "lazienka", rect(15.5, 13.5, 19.5, 16), level=1)
H.room("tar", "Taras", "taras", rect(11, 1.5, 15.5, 5.5), level=1)

# --- połączenia: amfilada parteru (pętla wokół ogrodów)
H.connect("wia", "pral", "door")
H.connect("wia", "wc", "door")
H.connect("wia", "bib", "wide")
H.connect("bib", "muz", "wide")
H.connect("muz", "hol", "double")
H.connect("hol", "biu", "double")
H.connect("biu", "spiz", "door", at=0.2)
H.connect("spiz", "sal", "door")
H.connect("wia", "herb", "door")
H.connect("herb", "prac", "door")
# --- piętro
H.connect("gal", "gard", "door")
H.connect("gard", "syp", "door")
H.connect("syp", "laz", "door")
H.connect("gal", "tar", "slide")

H.entrance("wia", "N")
H.path(rect(3.3, -5.5, 4.7, 1.3))
H.path(rect(5.0, 19.2, 15.0, 22.0))
H.tree(-3.0, 3.0, "brzoza")
H.tree(24.5, 16.5, "klon")
H.tree(-2.5, 22.0, "lipa")
H.tree(19.0, -4.0, "sosna")
H.cut("A–A", (8.5, -2.0), (8.5, 23.0))
H.cut("B–B", (-2.0, 10.0), (24.0, 10.0))
