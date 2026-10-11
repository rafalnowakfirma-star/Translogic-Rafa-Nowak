"""P17 · Refektarz (wersja 2) – zwarty kwadrat z białej cegły jak klasztorny wirydarz: w środku ogród zimowy z długim stołem
pod szklaną piramidą, od kuchni szklana harmonijka, wysoki salon od południa, moduły piętra od północy, tarasy po bokach piramidy."""
from silnik import House, rect, poly

# siatka: pasma W | ogród | E = 3,6 | 5,6 | 4,2 m (x), N | ogród | S = 4,0 | 5,6 | 3,8 m (y) – kwadrat 13,4 × 13,4 m po osiach ścian
XW, XE, XX = 3.6, 9.2, 13.4
YN, YS, YY = 4.0, 9.6, 13.4
XS = 11.2    # granica spiżarni i pralni (pas północny)
YK = 4.6     # spiżarnia i pralnia sięgają 0,6 m głębiej – harmonijka kuchni ma 5 m, a stół przesuwa się na południe
XH = 6.1     # koniec holu ze schodami na piętrze
YL = 2.0     # granica garderoby i łazienki (piętro)

H = House(
    "p17", "Refektarz",
    "Zwarty kwadrat z białej cegły zbudowany jak klasztorny wirydarz: w środku ogród zimowy z długim stołem pod szklaną piramidą, "
    "oddzielony od kuchni szklaną harmonijką. Na dachu parteru po obu stronach piramidy są tarasy, a od północy moduły piętra z biurem i sypialnią.",
    style=dict(fasada="cegla_biala", dach="sedum", akcent="dab"),
    concept=[
        "Dom to kwadrat 13,8 × 13,8 m (164 m²) ułożony jak klasztor wokół wirydarza: ogród zimowy 5,6 × 5,6 m w środku "
        "ze wszystkich stron otaczają pokoje, które na zewnątrz mają tylko okna-szczeliny, wysokie pasma i zwykłe okna, "
        "a jedyne szklane drzwi parteru wychodzą na patio za murem – dlatego ogrodu nie widać ani z drogi, ani od sąsiadów.",
        "Ogród jest jadalnią: na kamiennej posadzce w poziomie podłogi stoi długi stół na 8–10 osób, wzdłuż pięciometrowej "
        "szklanej harmonijki od kuchni – złożona łączy kuchnię i ogród w jedną salę, rozłożona zamyka ogród zimowy w mroźne noce "
        "albo wtedy, gdy w deszczowy dzień dach jest otwarty.",
        "Nad stołem stoi szklana piramida z latarnią, którą latem unosi się o 0,7 m, żeby ciepłe powietrze uchodziło górą, "
        "a wysoki salon od południa daje stołowi cień w letnie południe.",
        "Wchodzi się od północy przez wiatrołap z WC bez szkła do ogrodu i dalej idzie się bez korytarzy, z pokoju do pokoju: "
        "biblioteka ze schodami kręconymi i szklaną ścianą na ogród, spiżarnia, kuchnia i salon, a z wiatrołapu także pokój gościnny "
        "z wyjściem na patio.",
        "Salon ma 6,6 m wysokości i szkło tylko do ogrodu oraz do patio za murem 2,6 m w południowo-zachodnim narożniku, "
        "częściowo zadaszonego; na zewnątrz ma dwa rzędy wąskich, wysokich okien jak refektarz.",
        "Moduły piętra od północy łączą się przelotowo – biuro przeszklone na krajobraz od północy i zachodu i na taras zachodni, "
        "hol ze schodami, garderoba z łazienką, sypialnia ze szklaną ścianą od wschodu i wyjściem na taras wschodni – a dach nad nimi jest zielony.",
    ],
    notes=dict(
        lato="Harmonijka jest złożona, a latarnia piramidy uniesiona: kuchnia, ogród ze stołem i salon są jedną salą, "
             "salon otwiera się na patio za murem, a wieczorem siedzi się na tarasach po obu stronach piramidy.",
        zima="Harmonijka jest rozłożona, a piramida zamknięta, więc ogród z cytrusami i stołem jest osobną, jasną salą pod szkłem, "
             "do której wchodzi się z salonu, a pełne ściany z białej cegły z wąskimi oknami chronią dom przed wiatrem.",
        technologia="Ściany z bloczków ICF (styropian + beton) z licówką z białej cegły na kotwach, stropy z prefabrykowanych płyt kanałowych, "
                    "tarasy na stropie parteru z warstwą spadkową. Piramida ze szkła zespolonego na stalowej ramie z latarnią na siłownikach, "
                    "harmonijka kuchni w systemowej ramie aluminiowej.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

H.ogrod("og", "Ogród zimowy z jadalnią", rect(XW, YN, XE, YS), levels=1, roof_type="pyramid", style="jadalnia", seed=13,
        label_at=(6.5, 4.47))

# ---------------------------------------------------------------- parter
H.room("wc", "WC", "wc", rect(0, 2.2, 1.6, YN), ext="band_high", label_at=(1.0, 3.5))
H.room("wia", "Wiatrołap", "wiatrolap", poly((0, 0), (XW, 0), (XW, YN), (1.6, YN), (1.6, 2.2), (0, 2.2)),
       ext={"N": "slits", "W": "solid"})
H.room("bib", "Biblioteka", "biblioteka", rect(XW, 0, XE, YN), ext="band_high", garden="glass", label_at=(7.05, 3.25))
H.stair("spiral", level=0, center=(4.8, 2.7), r=1.0, start=330, sweep=300, n=16)
H.room("spi", "Spiżarnia", "spizarnia", rect(XE, 0, XS, YK), ext="band_high", label_at=(10.2, 3.95))
H.room("pral", "Pralnia", "pralnia", rect(XS, 0, XX, YK), ext={"N": "band_high", "E": "windows_sq"})
H.room("gos", "Pokój gościnny", "gosc", rect(0, YN, XW, YS), ext={"W": "windows", "pat": "glass_slide"}, garden="windows")
H.room("kuch", "Kuchnia", "kuchnia", rect(XE, YK, XX, YS), ext="band_high", garden="fold", kitchen_at="N")
H.room("sal", "Salon", "salon", rect(XW, YS, XX, YY), levels=2,
       ext={"pat": "glass_slide", "taE": "band_high", "S": "slits", "W": "slits", "E": "solid", "N": "glass"})
H.room("pat", "Patio za murem", "patio", rect(0, YS, XW, YY), roof=rect(2.2, YS, XW, YY), enclose="gwall")

H.connect("wia", "bib", "door", at=0.2)
H.connect("wc", "wia", "door", at=0.8)
H.connect("wia", "gos", "door")
H.connect("spi", "bib", "door", at=0.8)
H.connect("spi", "kuch", "door")
H.connect("pral", "kuch", "door", at=0.2)
H.connect("kuch", "sal", "wide", at=0.7)
H.entrance("wia", "N", at=0.6)
H.exit("pral", "E", kind="door", width=0.9)

# ---------------------------------------------------------------- piętro: moduły od północy, tarasy po bokach piramidy
H.room("biu", "Biuro", "biuro", rect(0, 0, XW, YN), level=1, ext={"N": "glass", "W": "glass", "taW": "glass"})
H.room("hol", "Hol", "hol", rect(XW, 0, XH, YN), level=1, ext={"N": "slits", "S": "glass"})
H.room("gar", "Garderoba", "garderoba", rect(XH, 0, XE, YL), level=1, ext="band_high")
H.room("laz", "Łazienka", "lazienka", rect(XH, YL, XE, YN), level=1, ext="band_high")
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(XE, 0, XX, YN), level=1, ext={"E": "glass", "N": "band_high", "taE": "glass"})
H.room("taW", "Taras zachodni", "taras", rect(0, YN, XW, YS), level=1)
H.room("taE", "Taras wschodni", "taras", rect(XE, YN, XX, YS), level=1)

H.connect("hol", "biu", "door", at=0.2)
H.connect("hol", "gar", "door", at=0.9)
H.connect("gar", "laz", "slide", width=0.9)
H.connect("gar", "syp", "door", at=0.9)
H.connect("biu", "taW", "slide")
H.connect("syp", "taE", "slide")

# ---------------------------------------------------------------- teren
H.path(rect(1.5, -6.0, 2.8, -0.2))
H.path(rect(XX + 0.2, 1.65, XX + 1.4, 2.95))
H.tree(-3.6, -2.8, "brzoza")
H.tree(17.6, 10.5, "lipa")
H.tree(17.2, -2.5, "klon")
H.cut("A–A", (5.6, -2.0), (5.6, 16.0))
H.cut("B–B", (-2.0, 6.8), (16.0, 6.8))
