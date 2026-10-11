"""P09 · Pawilony (wersja 2) – cztery drewniane pawilony wokół ogrodu leśnego, połączone ogrzewanymi łącznikami.

Krzyż pawilonów z wersji 1 zwarty w pierścień bez przerw: wysoki salon od zachodu (patio za murem),
pawilon nocny z piętrem od wschodu, niski pawilon wejściowy z galerią od północy, niska herbaciarnia
z czytelnią od południa. Dachy niskich pawilonów to tarasy po obu stronach szklanego dachu ogrodu,
a moduły piętra (biuro, hol, garderoba z łazienką, sypialnia) łączą je w ciąg.
"""
from silnik import House, rect, union
from silnik.dom import Garden


class OgrodLesny(Garden):
    """Obejście błędu silnika: przekrój rysuje drzewa ogrodu w pełnej wysokości (brzozy stylu „las” mają
    4,5–6,5 m) nawet pod jednokondygnacyjnym dachem szklanym na +3,65, a bryła 3D przycina je pod dachem.
    Tu przycinamy wysokość drzew w układzie ogrodu tak samo jak 3D – rzut, przekrój i 3D się zgadzają."""

    @property
    def _layout(self):
        return self.__dict__.get("_lay")

    @_layout.setter
    def _layout(self, lay):
        if lay:
            top = self.roof_z - (self.z0 - 0.12) - 0.45
            for f in lay["features"]:
                if f.t in ("brzoza", "klon", "sosna", "oliwka", "palma", "cytrus") and f.kw.get("h", 0) > top:
                    f.kw["h"] = top
        self.__dict__["_lay"] = lay


# ogród 6,8 × 6,4 m
GX1, GX2, GY1, GY2 = 4.0, 10.8, 3.6, 10.0
YN = 0.8                       # lico północne salonu, galerii i pawilonu nocnego
XS, XE = -0.4, 14.8            # lico zachodnie salonu / wschodnie pawilonu nocnego
YB = 12.4                      # południowy koniec pawilonu nocnego i czytelni
YH = 13.4                      # lico południowe herbaciarni

H = House(
    "p09", "Pawilony",
    "Cztery drewniane pawilony wokół leśnego ogrodu pod obrotowymi lamelami szklanymi, połączone ogrzewaną "
    "galerią i czytelnią. Wysokie są tylko salon od zachodu i pawilon nocny od wschodu, a dachy niskich pawilonów "
    "od północy i południa to tarasy przy szklanym dachu ogrodu; całość ma 168 m².",
    style=dict(fasada="drewno", dach="sedum"),
    concept=[
        "Ogród leśny 6,8 × 6,4 m ze wszystkich stron otaczają ogrzewane pokoje, a te ze szkłem do ogrodu mają na zewnątrz "
        "tylko szczeliny i okna pod sufitem (salon – szkło na patio za murem), więc ogrodu nie widać z zewnątrz.",
        "Wysokie są tylko pawilony od zachodu i wschodu, a od południa stoi niska herbaciarnia, więc słońce zagląda "
        "do ogrodu ponad jej dachem.",
        "Wchodzi się od północy przez mały wiatrołap bez szkła do ogrodu, a dalej galeria wzdłuż ogrodu prowadzi "
        "na zachód do salonu i na wschód przez pralnię do holu z biblioteką i schodami kręconymi.",
        "Salon z kuchnią ma 6,6 m wysokości i dwie szklane ściany: od wschodu na ogród, od zachodu na częściowo "
        "zadaszone patio za murem wysokości 2,6 m.",
        "Dachy pawilonu wejściowego i herbaciarni to tarasy po obu stronach szklanego dachu ogrodu, a najwyższe dachy "
        "salonu i pawilonu nocnego są zielone.",
        "Na piętrze pawilonu nocnego moduły idą jeden za drugim: biuro przeszklone na las i na taras północny, hol ze "
        "schodami, garderoba przelotowa z łazienką i sypialnia ze szklaną ścianą od wschodu i wyjściem na taras południowy.",
    ],
    notes=dict(
        lato="Lamele nad ogrodem stają pionowo i wypuszczają ciepłe powietrze, salon otwiera się na patio, "
             "a z tarasów patrzy się z góry na korony brzóz.",
        zima="Lamele są zamknięte, ogród jest ciepłym buforem między pawilonami, a z pawilonu do pawilonu "
             "przechodzi się przez ogrzewane pokoje – galerię, czytelnię i hol.",
        technologia="Pawilony z prefabrykowanych modułów szkieletowych drewnianych z elewacją z desek; tarasy "
                    "na stropach z warstwą spadkową i deską, dach ogrodu z systemowych lameli szklanych na stalowej ramie.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

H.rooms.append(OgrodLesny(H, "og", "Ogród leśny", rect(GX1, GY1, GX2, GY2), roof_type="louvre", style="las", seed=4))

# pawilon dzienny (zachód, wysoki) + patio za murem
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(XS, YN, GX1, GY2), levels=2, kitchen_at="N",
       ext={"pat": "glass_slide", "W": "glass", "N": "band_high", "S": "windows", "E": "band"})
H.room("pat", "Patio za murem", "patio", rect(-4.4, YN, XS, GY2), roof=rect(-2.0, 4.6, XS, GY2), enclose="gwall")
# pawilon wejściowy (północ, niski): galeria wzdłuż ogrodu + wiatrołap i WC
H.room("gal", "Galeria", "galeria", rect(GX1, YN, GX2, GY1), ext="slits")
H.room("wia", "Wiatrołap", "wiatrolap", rect(5.8, -1.6, 8.6, YN), ext={"N": "slits", "*": "solid"})
H.room("wc", "WC", "wc", rect(8.6, -1.6, 10.2, YN))
# pawilon nocny (wschód, 2 kondygnacje) – parter
H.room("pra", "Pralnia", "pralnia", rect(GX2, YN, XE, GY1), ext={"N": "band_high", "E": "windows_sq"})
H.room("hol", "Hol z biblioteką", "biblioteka", rect(GX2, GY1, XE, 7.0), ext="band_high")
H.room("gos", "Pokój gościnny", "gosc", rect(GX2, 7.0, XE, GY2), ext="band_high")
H.room("lzg", "Łazienka", "lazienka", rect(GX2, GY2, XE, YB), ext="band_high")
# pawilon herbaciany (południe, niski) i łącznik z czytelnią
H.room("her", "Herbaciarnia", "herbaciarnia", rect(GX1, GY2, GX2, YH), ext={"S": "band_high", "*": "slits"})
H.room("czy", "Czytelnia", "biblioteka", rect(1.2, GY2, GX1, YB), ext="band_high")

H.stair("spiral", level=0, center=(12.4, 4.8), r=1.0, start=0, sweep=300, n=16)

# piętro – moduły nad pawilonem nocnym
H.room("biu", "Biuro", "biuro", rect(GX2, YN, XE, GY1), level=1,
       ext={"E": "glass", "N": "windows", "taN": "glass_slide"})
H.room("hl1", "Hol", "hol", rect(GX2, GY1, XE, 6.0), level=1, ext={"W": "glass", "E": "slits"})
H.room("gar", "Garderoba", "garderoba", rect(GX2, 6.0, 12.8, 8.4), level=1, ext={"W": "band_high"})
H.room("laz", "Łazienka", "lazienka", rect(12.8, 6.0, XE, 8.4), level=1, ext={"E": "band_high"})
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(GX2, 8.4, XE, YB), level=1,
       ext={"E": "glass", "W": "glass", "S": "windows", "taS": "glass_slide"})
H.room("taN", "Taras północny", "taras", union(rect(GX1, YN, GX2, GY1), rect(5.8, -1.6, 10.2, YN)), level=1)
H.room("taS", "Taras południowy", "taras", union(rect(GX1, GY2, GX2, YH), rect(1.2, GY2, GX1, YB)), level=1)

# połączenia – parter
H.connect("wia", "gal", "door")
H.connect("wia", "wc", "door")
H.connect("gal", "sal", "door")
H.connect("gal", "pra", "door")
H.connect("pra", "hol", "door", at=0.15)
H.connect("hol", "gos", "door", at=0.85)
H.connect("gos", "lzg", "door", at=0.85)
H.connect("sal", "czy", "door")
H.connect("czy", "her", "door")
# piętro
H.connect("biu", "hl1", "door", at=0.15)
H.connect("hl1", "gar", "door", width=0.8)
H.connect("gar", "syp", "door", at=0.85, width=0.8)
H.connect("laz", "gar", "door")
H.connect("biu", "taN", "slide")
H.connect("syp", "taS", "slide")

H.entrance("wia", "N")
H.exit("pra", "E", kind="door", width=0.9)
H.path(rect(6.5, -7.5, 7.9, -1.8))
H.tree(18.0, 2.5, "sosna")
H.tree(17.6, 10.5, "brzoza")
H.tree(-3.5, -2.5, "lipa")
H.tree(-2.5, 14.5, "klon")
H.cut("A–A", (-5.0, 5.0), (17.0, 5.0))
H.cut("B–B", (7.4, -3.0), (7.4, 15.0))
