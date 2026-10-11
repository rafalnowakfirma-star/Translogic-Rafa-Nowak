"""P19 · Pomarańczarnia (wersja 2) – trawertynowa willa: wysokie L od północy i zachodu, domknięte w prostokąt
niskimi skrzydłami gospodarczymi; w środku ogród zimowy z jadalnią wśród drzewek pomarańczowych pod lamelami."""
from silnik import House, rect, poly

# osie
XW, XE, XX = 4.4, 10.4, 12.8      # zachodnia i wschodnia krawędź ogrodu, wschodnia ściana domu
YK, YM = 2.2, 3.4                  # pas wejścia (parter), lico modułów piętra
YN, YS, YY = 5.4, 10.4, 12.8       # północna i południowa krawędź ogrodu, południowa ściana domu

H = House(
    "p19", "Pomarańczarnia",
    "Trawertynowa willa.",
    style=dict(fasada="trawertyn", dach="sedum", akcent="dab"),
    concept=["..."],
    notes=dict(lato="...", zima="...", technologia="..."),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

H.ogrod("og", "Ogród zimowy z jadalnią", rect(XW, YN, XE, YS), levels=1, roof_type="louvre", style="jadalnia", seed=19,
        trees=[("cytrus", 5.05, 6.75, 0.4, 2.0), ("cytrus", 9.75, 6.75, 0.4, 2.0), ("cytrus", 9.75, 9.65, 0.4, 2.0)])

# ---- parter: wysokie L (północ + zachód)
H.room("hol", "Hol z biblioteką", "biblioteka", poly((0, 0), (XW, 0), (XW, YN), (1.8, YN), (1.8, 3.6), (0, 3.6)),
       ext={"W": "band_high", "N": "slits"})
H.room("wc", "WC", "wc", rect(0, 3.6, 1.8, YN))
H.room("wia", "Wiatrołap", "wiatrolap", rect(XW, 0, 7.2, YK), ext="slits")
H.room("spi", "Spiżarnia", "spizarnia", rect(7.2, 0, XE, YK))
H.room("kuch", "Kuchnia", "kuchnia", rect(XW, YK, XE, YN), garden="fold", kitchen_at="N")
H.room("sal", "Salon", "salon", rect(0, YN, XW, YY), levels=2,
       ext={"pat": "glass_slide", "W": "glass", "E": "glass", "taS": "windows", "S": "band_high"})
H.room("pat", "Patio za murem", "patio", rect(-4.4, YN, 0, YY), roof=rect(-2.0, YN, 0, YY), enclose="gwall",
       floor="trawertyn")

# ---- parter: niskie skrzydła gospodarcze (wschód + południe)
H.room("tech", "Techniczne", "techniczne", rect(XE, 0, XX, YK))
H.room("pral", "Pralnia", "pralnia", rect(XE, YK, XX, YN), ext={"E": "windows_sq"})
H.room("pra", "Pracownia ogrodnika", "pracownia", rect(XE, YN, XX, YY), ext="windows", floor="terakota")
H.room("win", "Winiarnia", "winiarnia", rect(XW, YS, XE, YY), ext="solid")

H.stair("spiral", level=0, center=(1.35, 1.35), r=1.0, start=0, sweep=300, n=16)

# ---- piętro: moduły w wysokim skrzydle, tarasy na dachach niskich skrzydeł
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
H.connect("hol", "wc", "door")
H.connect("hol", "kuch", "wide")
H.connect("hol", "sal", "wide")
H.connect("kuch", "spi", "door")
H.connect("kuch", "pral", "door")
H.connect("pral", "tech", "door")
H.connect("pral", "pra", "door")
H.connect("pra", "win", "door")
H.connect("win", "sal", "door")
H.connect("sal", "pat", "slide")
# piętro
H.connect("gal", "biu", "door")
H.connect("gal", "syp", "door")
H.connect("syp", "laz", "door", at=0.3)
H.connect("biu", "taN", "slide")
H.connect("syp", "taN", "slide")

H.entrance("wia", "N")
H.exit("pral", "E", kind="door", width=0.9)
H.path(rect(5.0, -6.0, 6.4, -0.2))
H.tree(-6.5, 2.0, "oliwka")
H.tree(16.0, 8.0, "oliwka")
H.tree(-2.5, 16.5, "sosna")
H.cut("A–A", (7.4, -2.5), (7.4, 15.0))
H.cut("B–B", (-6.5, 8.1), (15.0, 8.1))
