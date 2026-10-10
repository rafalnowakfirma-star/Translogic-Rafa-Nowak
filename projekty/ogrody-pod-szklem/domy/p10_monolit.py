"""P10 · Monolit – zamknięty kamienny blok z głębokimi wcięciami, w środku staw pod przesuwnym szkłem."""
from silnik import House, rect

H = House(
    "p10", "Monolit",
    "Z zewnątrz zamknięty kamienny blok 20 × 17 m z wąskimi szczelinami okien i głębokimi wcięciami-loggiami. "
    "W środku wszystko otwiera się na ogród ze stawem-lustrem pod przesuwnym szklanym dachem.",
    style=dict(fasada="kamien", dach="zwir", akcent="stal"),
    concept=[
        "Z zewnątrz dom jest jednym wyciosanym blokiem z kamienia: okna to wąskie szczeliny, a duże szkło pojawia się tylko w głębokich wcięciach – w loggii biura od zachodu, w dwukondygnacyjnej loggii od wschodu i w patio wciętym w południową ścianę. Tam szkło ma cień i prywatność.",
        "Północna ściana to gruba ciepła skorupa z pomieszczeń pomocniczych: techniczne, pralnia, wiatrołap, WC, szatnia i schody. To poprawiona wersja pomysłu z korytarzem po obwodzie: bufor jest tylko tam, gdzie jest zimno, i nie zabiera okien pokojom, bo pokoje za nim patrzą na ogród.",
        "Ogród 7,4 × 6,9 m to płytki staw-lustro z kamieniami i brzozami pod przesuwnym szklanym dachem. Od wschodu ogród przechodzi w werandę pod sypialnią, którą zimą zamyka szklana harmonijka, a latem otwiera się przez loggię na krajobraz.",
        "Biuro od zachodu ma szkło od ogrodu i od loggii głębokiej na 2,6 m; biurko stoi między stawem a cieniem kamiennej niszy.",
        "Od wejścia idzie się amfiladą: wiatrołap, galeria wzdłuż stawu, potem biblioteka i biuro na zachód albo pracownia i weranda na wschód. Salon z kuchnią ma 6,9 m wysokości, od południa tylko szczeliny, a światło bierze z ogrodu i z patio, które w połowie jest pod dachem; przy patio są sauna i łazienka.",
        "Piętro to wyłącznie sypialnia nad werandą: przeszklona do wschodniej loggii z kamiennym murkiem i nad szklany dach ogrodu, z przelotową garderobą i łazienką nad pracownią. Schody do niej biegną w północnej skorupie.",
    ],
    notes=dict(
        lato="Połowa szklanego dachu zsuwa się nad drugą, harmonijka werandy składa się i ogród przewietrza się na przestrzał od wschodniej loggii po patio; głębokie wcięcia dają szkłu cień.",
        zima="Dach i harmonijka są zamknięte: ogród z werandą to bufor między pokojami a mrozem, a od północy chroni gruba skorupa pomieszczeń pomocniczych; staw oddaje wieczorem ciepło zebrane za dnia.",
        technologia="Ściany z bloczków keramzytowych na cienką spoinę z okładziną z płyt piaskowca na ruszcie, stropy i dach z prefabrykowanych płyt kanałowych, dach szklany systemowy na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=4.2)
H.level(1, z=4.2, h=3.1)

# ogród – staw-lustro; ściany ogrodu podciągnięte 0,5 m ponad dach parteru, żeby brzozy mieściły się pod szkłem
og = H.ogrod("og", "Ogród ze stawem", rect(7.0, 5.6, 14.4, 12.5), levels=1, roof_type="slide", style="woda",
             seed=4, roof_z=4.95)
og.height = 4.4

# północna skorupa (pomieszczenia pomocnicze)
H.room("tech", "Techniczne", "techniczne", rect(0, 0, 3.4, 2.6), ext="solid")
H.room("pral", "Pralnia", "pralnia", rect(3.4, 0, 7.0, 2.6), ext="slits")
H.room("wia", "Wiatrołap", "wiatrolap", rect(7.0, 0, 9.8, 2.6), ext="solid")
H.room("wc", "WC", "wc", rect(9.8, 0, 11.4, 2.6), ext="slits")
H.room("szat", "Szatnia", "garderoba", rect(11.4, 0, 13.0, 2.6), ext="solid")
H.room("sch", "Schody", "hol", rect(13.0, 0, 20.4, 2.6), ext="slits", furn=False)
H.stair("straight", level=0, rect=(13.3, 0.3, 19.6, 1.4), up="E")

# amfilada od frontu – za skorupą, oknami na staw
H.room("bib", "Biblioteka", "biblioteka", rect(0, 2.6, 7.0, 5.6), ext="slits")
H.room("gal", "Galeria", "galeria", rect(7.0, 2.6, 14.4, 5.6))
H.room("pra", "Pracownia", "pracownia", rect(14.4, 2.6, 20.4, 5.6), ext={"E": "slits", "S": "glass"}, floor="beton")

# zachód – biuro za głęboką loggią
H.room("logw", "Loggia biura", "loggia", rect(0, 5.6, 2.6, 12.5), floor="kamien")
H.room("biu", "Biuro", "biuro", rect(2.6, 5.6, 7.0, 12.5), ext={"W": "glass_slide", "S": "solid"}, garden="glass_slide")

# wschód – weranda pod sypialnią i dwukondygnacyjna loggia
H.room("ver", "Weranda", "loggia", rect(14.4, 5.6, 18.4, 12.5), roof="none", floor="kamien")
H.room("loge", "Loggia wschodnia", "loggia", rect(18.4, 5.6, 20.4, 12.5), roof="none", floor="kamien", furn=False)

# południe – sauna i łazienka przy patio, patio wcięte w ścianę, wysoki salon, zimne pomieszczenia przy kuchni
H.room("sau", "Sauna", "sauna", rect(0, 12.5, 2.6, 15.0), ext={"W": "slits", "E": "solid"})
H.room("laz2", "Łazienka", "lazienka", rect(0, 15.0, 2.6, 17.4), ext={"W": "slits", "S": "solid", "E": "solid"})
H.room("pat", "Patio", "patio", rect(2.6, 12.5, 7.0, 17.4), roof=rect(2.6, 12.5, 7.0, 14.9), floor="kamien")
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(7.0, 12.5, 17.4, 17.4), levels=2,
       ext={"S": "slits", "W": "glass_slide", "N": "glass", "E": "slits"}, kitchen_at="E")
H.room("win", "Winiarnia", "winiarnia", rect(17.4, 12.5, 20.4, 14.9), ext="solid")
H.room("spi", "Spiżarnia", "spizarnia", rect(17.4, 14.9, 20.4, 17.4), ext="solid")

# piętro – tylko sypialnia nad werandą
H.room("holg", "Hol górny", "hol", rect(13.0, 0, 20.4, 2.6), level=1, ext={"N": "slits", "E": "slits", "*": "solid"}, furn=False)
H.room("lazm", "Łazienka", "lazienka", rect(14.4, 2.6, 16.6, 5.6), level=1, ext={"W": "band_high", "*": "solid"})
H.room("garm", "Garderoba", "garderoba", rect(16.6, 2.6, 20.4, 5.6), level=1, ext={"E": "slits", "*": "solid"})
H.room("sypm", "Sypialnia", "sypialnia_glowna", rect(14.4, 5.6, 18.4, 12.5), level=1,
       ext={"W": "glass", "E": "glass_slide", "S": "solid"})
H.room("logu", "Loggia sypialni", "loggia", rect(18.4, 5.6, 20.4, 12.5), level=1, enclose="low", floor="kamien")

# połączenia – parter
H.connect("wia", "gal", "wide")
H.connect("wia", "pral", "door")
H.connect("pral", "tech", "door")
H.connect("gal", "wc", "door")
H.connect("gal", "szat", "door")
H.connect("gal", "sch", "door")
H.connect("gal", "bib", "wide")
H.connect("gal", "pra", "wide")
H.connect("bib", "biu", "double")
H.connect("biu", "pat", "door")
H.connect("pat", "laz2", "door")
H.connect("laz2", "sau", "door")
H.connect("pra", "ver", "slide")
H.connect("og", "ver", "open")
H.connect("ver", "loge", "fold")
H.connect("sal", "win", "door")
H.connect("sal", "spi", "door")
# piętro
H.connect("holg", "garm", "door")
H.connect("garm", "sypm", "door")
H.connect("sypm", "lazm", "door")

H.entrance("wia", "N")
H.path(rect(7.7, -7, 9.1, -0.2))
H.path(rect(2.6, 17.6, 7.0, 20.6))
H.tree(-4.0, 9.5, "sosna")
H.tree(24.5, 13.5, "klon")
H.tree(23.5, -3.0, "brzoza")
H.tree(3.0, 24.0, "lipa")
H.cut("A–A", (10.8, -2.0), (10.8, 20.0))
H.cut("B–B", (-2.0, 9.0), (23.0, 9.0))
H.cut("C–C", (16.4, -2.0), (16.4, 20.0))
