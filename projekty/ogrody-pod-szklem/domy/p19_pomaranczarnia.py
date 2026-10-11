"""P19 · Pomarańczarnia (wersja 2) – trawertynowa willa: wysokie L od północy i zachodu, domknięte w prostokąt
niskimi skrzydłami gospodarczymi; w środku ogród zimowy z jadalnią wśród drzewek pomarańczowych pod obrotowymi lamelami."""
from silnik import House, rect, poly

# osie ścian
XW, XE, XX = 4.4, 10.4, 12.8      # zachodnia i wschodnia krawędź ogrodu, wschodnia ściana domu
YK, YM = 2.2, 3.4                  # pas wejścia na parterze, południowe lico modułów piętra
YN, YS, YY = 5.4, 10.8, 13.2       # północna i południowa krawędź ogrodu, południowa ściana domu

H = House(
    "p19", "Pomarańczarnia",
    "Trawertynowa willa 12,8 × 13,2 m na planie litery L domkniętej w prostokąt: od północy i zachodu wysokie skrzydła, "
    "od wschodu i południa niskie skrzydła gospodarcze. W środku ogród zimowy z jadalnią – stół wśród drzewek "
    "pomarańczowych pod dachem z obrotowych szklanych lamel, oddzielony od kuchni szklaną harmonijką.",
    style=dict(fasada="trawertyn", dach="sedum", akcent="dab"),
    concept=[
        "Dom ma 165 m² powierzchni użytkowej. Wysokie L od północy i zachodu – moduły piętra i dwukondygnacyjny salon – "
        "osłania ogród od wiatru, a niskie skrzydła od wschodu i południa wpuszczają nad sobą do ogrodu poranne "
        "i południowe słońce, którego potrzebują drzewka pomarańczowe.",
        "Ogród 6,0 × 5,4 m jest jadalnią: kamienna posadzka w poziomie podłogi, stół na osiem osób przy kuchni, po jego "
        "bokach dwa drzewka pomarańczowe, a od południa rząd trzech kolejnych i oliwka.",
        "Kuchnię od ogrodu oddziela szklana harmonijka szerokości 6 m. Złożona łączy kuchnię i jadalnię w jedną "
        "przestrzeń, rozłożona zamyka ogród zimowy – w mroźne noce albo gdy przy uchylonych lamelach pada deszcz.",
        "Dach ogrodu to szklane lamele na wysokości dachu parteru: zamknięte dają szczelny szklany strop, uchylone "
        "wietrzą ogród, a ustawione pionowo zamieniają go w otwarty dziedziniec.",
        "Wchodzi się od północy przez wiatrołap do holu ze schodami kręconymi i WC; ogrodu stąd nie widać. Parter "
        "obchodzi się dookoła ogrodu bez korytarzy: hol, kuchnia, pralnia, pracownia, winiarnia, salon. Salon ma "
        "6,3 m wysokości i szkło tylko do ogrodu i na patio za murem wysokości 2,6 m, z pergolą wzdłuż szyby; "
        "pozostałe pokoje mają od zewnątrz wysokie pasma okien, szczeliny albo pełne ściany, więc ogrodu nie widać na wylot.",
        "Dachy niskich skrzydeł to trzy tarasy za trawertynowym murkiem, które obiegają szklany dach z trzech stron. "
        "Na piętrze moduły przechodzą jeden w drugi: z galerii przy schodach do biura przeszklonego na zachód i na taras "
        "oraz do sypialni ze szklaną ścianą przesuwną na taras, a z niej do łazienki. Najwyższy dach jest zielony.",
    ],
    notes=dict(
        lato="Lamele stoją pionowo, harmonijka jest złożona i kuchnia z ogrodem-jadalnią tworzy jedno wnętrze pod "
             "otwartym niebem; z salonu wychodzi się na patio w cieniu pergoli, a wieczorem na tarasy wokół szklanego dachu.",
        zima="Lamele są zamknięte, a rozłożona harmonijka oddziela chłodniejszy, jasny ogród od ciepłej kuchni – drzewka "
             "zimują w nim jak w dawnej oranżerii, a w słoneczne dni stół w ogrodzie nadal służy za jadalnię.",
        technologia="Ściany z prefabrykowanych płyt warstwowych z betonu (beton – izolacja – beton) z okładziną z płyt "
                    "trawertynu na ruszcie, stropy i dachy z prefabrykowanych płyt kanałowych, tarasy na stropie z warstwą "
                    "spadkową i murkiem z trawertynu. Dach ogrodu z systemowych szklanych lamel na aluminiowych osiach, "
                    "obracanych siłownikiem z czujnikiem deszczu, na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

# ogród zimowy z jadalnią – stół stawia silnik przy harmonijce kuchni; dwa drzewka po bokach stołu dokładamy sami
H.ogrod("og", "Ogród zimowy z jadalnią", rect(XW, YN, XE, YS), levels=1, roof_type="louvre", style="jadalnia", seed=37,
        trees=[("cytrus", 5.05, 6.75, 0.4, 2.0), ("cytrus", 9.75, 6.75, 0.4, 2.0)], label_at=(7.4, 8.05))

# ---- parter: wysokie L (północ + zachód)
H.room("hol", "Hol", "hol", poly((0, 0), (XW, 0), (XW, YN), (1.8, YN), (1.8, 3.6), (0, 3.6)),
       ext={"W": "windows", "N": "slits"})
H.room("wc", "WC", "wc", rect(0, 3.6, 1.8, YN))
H.room("wia", "Wiatrołap", "wiatrolap", rect(XW, 0, 7.2, YK), ext="slits", label_at=(5.48, 1.2))
H.room("spi", "Spiżarnia", "spizarnia", rect(7.2, 0, XE, YK))
H.room("kuch", "Kuchnia", "kuchnia", rect(XW, YK, XE, YN), garden="fold", kitchen_at="N")
H.room("sal", "Salon", "salon", rect(0, YN, XW, YY), levels=2,
       ext={"pat": "glass_slide", "W": "glass", "E": "glass", "taS": "windows", "S": "band_high"})
H.room("pat", "Patio za murem", "patio", rect(-4.4, YN, 0, YY), roof=rect(-2.0, YN, 0, YY), enclose="gwall",
       floor="trawertyn", label_at=(-2.75, 9.3))

# ---- parter: niskie skrzydła gospodarcze (wschód + południe)
H.room("tech", "Techniczne", "techniczne", rect(XE, 0, XX, YK))
H.room("pral", "Pralnia", "pralnia", rect(XE, YK, XX, YN), ext={"E": "windows_sq"})
H.room("pra", "Pracownia", "pracownia", rect(XE, YN, XX, YY), ext={"E": "band_high", "S": "windows"}, floor="terakota",
       label_at=(11.53, 7.0))
H.room("win", "Winiarnia", "winiarnia", rect(XW, YS, XE, YY), ext="solid")

H.stair("spiral", level=0, center=(1.35, 1.35), r=1.0, start=0, sweep=300, n=16)

# ---- piętro: moduły w wysokim skrzydle, tarasy na dachach niskich skrzydeł (wokół szklanego dachu)
H.room("gal", "Galeria", "galeria", rect(0, 0, XW, 2.6), level=1, ext={"N": "slits", "W": "glass"})
H.room("biu", "Biuro", "biuro", rect(0, 2.6, XW, YN), level=1, ext={"W": "glass", "taN": "glass_slide"})
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(XW, 0, 9.2, YM), level=1,
       ext={"taN": "glass_slide", "N": "band_high"})
H.room("laz", "Łazienka", "lazienka", rect(9.2, 0, XX, YM), level=1)
H.room("taN", "Taras", "taras", rect(XW, YM, XE, YN), level=1, enclose="low", floor="trawertyn")
H.room("taE", "Taras wschodni", "taras", rect(XE, YM, XX, YY), level=1, enclose="low", floor="trawertyn")
H.room("taS", "Taras południowy", "taras", rect(XW, YS, XE, YY), level=1, enclose="low", floor="trawertyn")

# ---- połączenia parteru (amfilada dookoła ogrodu)
H.connect("wia", "hol", "door")
H.connect("wc", "hol", "door")
H.connect("hol", "kuch", "wide")
H.connect("hol", "sal", "wide")
H.connect("kuch", "spi", "slide", width=1.0)
H.connect("kuch", "pral", "slide", width=1.0)
H.connect("pral", "tech", "slide", width=1.0)
H.connect("pral", "pra", "door")
H.connect("pra", "win", "door", at=0.8)
H.connect("win", "sal", "door", at=0.2)
H.connect("sal", "pat", "slide")
# ---- piętro (moduły przelotowe)
H.connect("gal", "biu", "door")
H.connect("gal", "syp", "door")
H.connect("syp", "laz", "door", at=0.3)
H.connect("biu", "taN", "slide")
H.connect("syp", "taN", "slide")

H.entrance("wia", "N")
H.exit("pral", "E", kind="door", width=0.9, at=0.8)
H.path(rect(5.0, -6.0, 6.4, -0.2))
H.tree(-6.5, 2.0, "oliwka")
H.tree(16.0, 8.0, "oliwka")
H.tree(-2.5, 16.5, "sosna")
H.cut("A–A", (7.4, -2.5), (7.4, 15.0))
H.cut("B–B", (-6.5, 8.1), (15.0, 8.1))
H.cut("C–C", (2.2, -2.5), (2.2, 15.0))
