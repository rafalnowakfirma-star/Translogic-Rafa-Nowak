"""P16 · Owal (wersja 2) – prostokąt z trawertynu wokół eliptycznego ogrodu pod kopułą z przesłoną.
Pierścień pokoi to cztery litery L na przemian wysokie i niskie: moduły piętra (NW) i salon z kuchnią (SE)
po przekątnej, a na dachach parterowych liter L (NE, SW) tarasy wokół kopuły."""
from shapely import set_precision

from silnik import House, rect, ellipse

# prostokąt 14,8 × 12,4 m, elipsa ogrodu 8,4 × 5,8 m (półosie 4,2 × 2,9), przesunięta o 0,3 m na północ,
# żeby pas południowy (salon) miał 3,6 m głębokości, a północny 3,0 m
W, D = 14.8, 12.4
CX, CY, RX, RY = W / 2, 5.9, 4.2, 2.9
E = set_precision(ellipse(CX, CY, RX, RY), 1e-6)   # ta sama siatka współrzędnych co pokoje


def cut(x1, y1, x2, y2):
    """Fragment prostokąta minus elipsa ogrodu (set_precision: wspólna siatka 1e-6 m z elipsą).
    Linie podziału dobrane tak, żeby żaden pokój nie rozpadał się na dwie części przy łuku elipsy."""
    return set_precision(rect(x1, y1, x2, y2).difference(E), 1e-6)


# granice czterech liter L – każda linia przecina pas pierścienia i trafia w elipsę
XA = 9.8    # koniec litery L z modułami (NW) w paśmie północnym
Y3 = 7.2    # koniec litery L z modułami (NW) w paśmie zachodnim
Y1 = 5.2    # koniec tarasu porannego (NE) w paśmie wschodnim
X2 = 5.0    # koniec tarasu wieczornego (SW) w paśmie południowym
# podziały wewnątrz liter L
XB, YB = 3.8, 2.4     # narożnik NW: łazienka/techniczne, sypialnia/sala muzyczna
XG = 6.2              # galeria ze schodami / biuro (piętro)
XW, YW = 12.2, 3.0    # wiatrołap / pralnia, wiatrołap / WC
XK = 10.4             # salon / kuchnia z jadalnią (linia przecina elipsę od dołu)

H = House(
    "p16", "Owal",
    "Prostokątny dom z trawertynu, 167 m² razem z piętrem, z eliptycznym ogrodem w środku, którego nie widać z zewnątrz. "
    "Wokół szklanej kopuły ogrodu na przemian stoją dwie bryły piętrowe i dwa parterowe skrzydła z tarasami na dachach.",
    style=dict(fasada="trawertyn", dach="sedum"),
    concept=[
        "Obrys to prostokąt 14,8 × 12,4 m, a w środku eliptyczny ogród cytrusowy 8,4 × 5,8 m otoczony ze wszystkich stron pokojami. Na parterze szkło mają tylko ściany od ogrodu i od patio za murem, a na zewnątrz są okna, szczeliny i wstęgi, więc ogrodu nie widać z drogi ani od sąsiadów.",
        "Pierścień wokół elipsy składa się z czterech liter L na przemian wysokich i niskich: po przekątnej stoją piętrowe moduły od północnego zachodu i dwukondygnacyjny salon z kuchnią od południowego wschodu, a dachy dwóch parterowych liter L są tarasami, z dwóch stron osłoniętymi wyższymi bryłami i otwartymi na krajobraz z pozostałych dwóch.",
        "Szklana kopuła ogrodu leży na wysokości dachu parteru, więc z obu tarasów patrzy się na nią z góry; jej środek otwiera się jak migawka aparatu.",
        "Parter obchodzi się dookoła ogrodu bez korytarzy: wiatrołap bez szkła do ogrodu, hol z biblioteką i schodami kręconymi, sala muzyczna, herbaciarnia, salon, kuchnia z jadalnią, pralnia ze spiżarnią i z powrotem wiatrołap.",
        "Salon i kuchnia z jadalnią mają 6,6 m wysokości i krzywą szklaną ścianę od ogrodu, a od południa wychodzą na patio schowane za murem wysokości 2,6 m, częściowo zadaszone.",
        "Na piętrze moduły połączone drzwiami w ciąg: biuro przeszklone na krajobraz od północy i na taras poranny, galeria ze schodami i szklaną ścianą od strony kopuły, sypialnia ze szklaną ścianą od zachodu i wyjściem na taras wieczorny oraz łazienka. Najwyższe dachy są zielone.",
    ],
    notes=dict(
        lato="Przesłona kopuły jest otwarta i ciepłe powietrze uchodzi górą, ogród działa jak zacieniony dziedziniec, a życie przenosi się na patio za murem i na tarasy – poranny przy biurze i wieczorny przy sypialni.",
        zima="Kopuła jest zamknięta, ogród z drzewkami cytrusowymi zbiera ciepło słońca i oddaje je pokojom wokół, a pełne ściany z trawertynu i mur patio osłaniają dom od wiatru.",
        technologia="Ściany z bloczków keramzytowych na klej (z drobnych bloczków łatwo wymurować łuki wokół elipsy) z elewacją z płyt trawertynu, stropy z prefabrykowanych płyt kanałowych, tarasy na stropie parteru z warstwą spadkową i deską. Szklane ściany ogrodu to łukowe panele w stalowych ramach pod żelbetowym wieńcem w kształcie elipsy, który niesie ściany piętra i kopułę z segmentów szklanych.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

# ogród jednokondygnacyjny – kopuła na wysokości dachu parteru, wokół niej tarasy i moduły piętra
H.ogrod("og", "Ogród cytrusowy", E, levels=1, roof_type="iris", style="oranzeria", seed=1,
        label_at=(6.38, 4.12))

# --- parter: pierścień pokoi wokół elipsy -------------------------------------
# litera L z modułami nad sobą (NW)
H.room("tech", "Techniczne", "techniczne", rect(0, 0, XB, YB), ext="band_high")
H.room("muz", "Sala muzyczna", "muzyczny", cut(0, YB, XB, Y3), ext="windows", garden="glass")
H.room("hol", "Hol z biblioteką", "biblioteka", cut(XB, 0, XA, Y3), ext="band_high", garden="glass")
H.stair("spiral", level=0, center=(5.0, 1.45), r=1.0, start=90, sweep=300, n=16)
# litera L pod tarasem porannym (NE)
H.room("wia", "Wiatrołap", "wiatrolap", rect(XA, 0, XW, YW), ext={"N": "slits", "*": "solid"},
       label_at=(11.3, 1.55))
H.room("wc", "WC", "wc", cut(XA, YW, XW, Y1))
H.room("pral", "Pralnia i spiżarnia", "pralnia", rect(XW, 0, W, Y1), ext={"N": "band_high", "E": "windows_sq"})
# litera L z salonem (SE) – dwie kondygnacje; szkło na zewnątrz tylko do patio za murem
H.room("kuch", "Kuchnia z jadalnią", "kuchnia", cut(XK, Y1, W, D), levels=2, kitchen_at="N",
       ext={"pat": "glass_slide", "E": "band_high", "taNE": "band", "*": "windows"}, garden="glass")
H.room("sal", "Salon", "salon", cut(X2, Y1, XK, D), levels=2,
       ext={"pat": "glass_slide", "taSW": "band", "*": "windows"}, garden="glass")
H.room("pat", "Patio za murem", "patio", rect(8.0, D, 14.2, D + 4.0), roof=rect(8.0, D, 14.2, D + 2.4), enclose="gwall",
       label_at=(11.1, D + 3.45))
# litera L pod tarasem wieczornym (SW)
H.room("her", "Herbaciarnia", "herbaciarnia", cut(0, Y3, X2, D), ext="windows", garden="glass")

# --- piętro: moduły NW i tarasy na dachach parterowych liter L ----------------
H.room("laz", "Łazienka", "lazienka", rect(0, 0, XB, YB), level=1, ext="band_high")
H.room("syp", "Sypialnia", "sypialnia_glowna", cut(0, YB, XB, Y3), level=1,
       ext={"W": "glass", "taSW": "glass", "*": "windows"})
H.room("gal", "Galeria", "galeria", cut(XB, 0, XG, Y3), level=1, ext={"N": "slits", "*": "glass"},
       label_at=(4.6, 3.05))
H.room("biu", "Biuro", "biuro", cut(XG, 0, XA, Y3), level=1, ext={"N": "glass", "taNE": "glass", "*": "windows"},
       label_at=(9.0, 2.4))
H.room("taNE", "Taras poranny", "taras", cut(XA, 0, W, Y1), level=1)
H.room("taSW", "Taras wieczorny", "taras", cut(0, Y3, X2, D), level=1)

# --- połączenia ---------------------------------------------------------------
H.connect("wia", "hol", "door", at=0.85)
H.connect("wc", "wia", "door")            # drzwi WC otwierane na zewnątrz
H.connect("wia", "pral", "door")
H.connect("pral", "kuch", "door")
H.connect("sal", "kuch", "open")
H.connect("sal", "her", "double", at=0.8)  # przy północnym końcu ściany – reszta ściany na kominek
H.connect("muz", "her", "door", at=0.2)
H.connect("muz", "hol", "door")
H.connect("muz", "tech", "door", at=0.2)
H.connect("hol", "og", "slide", at=0.85)
H.connect("her", "og", "slide")
H.connect("gal", "biu", "door", at=0.85)  # obok spocznika, nie za schodami
H.connect("gal", "syp", "door")
H.connect("syp", "laz", "door", at=0.25)
H.connect("biu", "taNE", "slide")
H.connect("syp", "taSW", "slide")

H.entrance("wia", "N")
H.exit("pral", "E", kind="door", width=0.9)

# --- teren (drzewa poza osią widoku z lotu ptaka od południowego zachodu) -------
H.path(rect(10.3, -6, 11.7, -0.2))
H.tree(-4.0, 1.0, "brzoza")
H.tree(17.5, -2.5, "sosna")
H.tree(18.5, 8.0, "klon")
H.tree(17.0, 16.0, "lipa")
H.cut("A–A", (9.0, -1.5), (9.0, D + 8.1))        # biuro/hol – ogród – salon – patio (koniec cięcia dalej na południe: opis słońca nad rzędnymi)
H.cut("B–B", (-1.5, 10.91), (16.3, 1.2))         # po przekątnej: taras wieczorny – kopuła – taras poranny
