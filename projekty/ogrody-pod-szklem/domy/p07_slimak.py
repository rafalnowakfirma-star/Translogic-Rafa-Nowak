"""P07 · Ślimak – bryła wznosi się spiralnie wokół ogrodu: 1, 2 i 3 kondygnacje, dachy są tarasami."""
from silnik import House, rect

# ogród 9 × 9 m w środku; skrzydła: S (1 kond.), W (2 kond.), N (3 kond.), od wschodu patio
GX1, GY1, GX2, GY2 = 6.0, 6.0, 15.0, 15.0
XW, YN, YS, XS = 2.0, 1.0, 19.0, 16.5
DZ = 0.03   # deska tarasów na piętrach 3 cm nad stropem (inaczej w renderze migoczą na czarno)

H = House(
    "p07", "Ślimak",
    "Dom wokół ogrodu japońskiego, którego skrzydła mają kolejno jedną, dwie i trzy kondygnacje. "
    "Dach każdego niższego skrzydła jest tarasem dla wyższego, a schody zewnętrzne łączą tarasy w drogę, która okrąża ogród i kończy się na dachu.",
    style=dict(fasada="beton", dach="sedum"),
    concept=[
        "Skrzydło południowe ma jedną kondygnację, zachodnie dwie, a północne trzy. Dzięki temu zimowe słońce wpada nad niskim skrzydłem prosto do ogrodu, a najwyższa bryła osłania go od północy.",
        "Dachy niższych skrzydeł są tarasami na +3,4 m i +6,8 m, a dach skrzydła północnego na +10,2 m. Trzy biegi schodów zewnętrznych – od patio wzdłuż wschodu, nad biurem wzdłuż południa i nad skrzydłem zachodnim – prowadzą z tarasu na taras dookoła ogrodu, zgodnie z ruchem wskazówek zegara.",
        "Biuro zajmuje całe skrzydło południowe: od północy ma szkło do ogrodu, od południa szkło na trawnik, a od wschodu osobne wejście dla gości.",
        "Od wejścia w elewacji zachodniej idzie się przez kolejne pokoje: wiatrołap, garderobę, herbaciarnię i pracownię aż do biura. W drugą stronę hol ze schodami prowadzi do kuchni.",
        "Salon z kuchnią w skrzydle północnym ma 6,5 m wysokości; górne okno ponad szklanym dachem ogrodu wpuszcza słońce w głąb pokoju, a od wschodu salon wychodzi na patio z daszkiem.",
        "Sypialnia główna na najwyższym piętrze ma szklaną ścianę od południa, z widokiem na ogród i tarasy.",
    ],
    notes=dict(
        lato="Lamele dachu ogrodu stoją pionowo, harmonijka od wschodu jest złożona i ogród łączy się z patio; tarasy na dachach są letnimi pokojami pod niebem.",
        zima="Lamele są zamknięte, ogród grzeje słońce wpadające nad parterowym biurem, a trzykondygnacyjne skrzydło północne zatrzymuje wiatr.",
        technologia="Ściany z bloczków ICF (styropian zalewany betonem) z okładziną z betonu w deskowaniu, więc bryła działa jak monolit; stropy i płyty tarasów żelbetowe, schody zewnętrzne z prefabrykowanych stopni wspornikowych.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)
H.level(2, z=6.8, h=3.4)
H.level(3, z=10.2, h=3.0, name="Dach")

H.ogrod("og", "Ogród zimowy", rect(GX1, GY1, GX2, GY2), levels=1, roof_type="louvre", style="japonski",
        edge="fold", seed=4)

# ---------------------------------------------------------------- parter
# róg NW – hol ze schodami (oś spirali)
H.room("hol0", "Hol", "hol", rect(XW, YN, GX1, GY1), ext={"N": "slits", "W": "slits"}, furn=False)
# skrzydło N – salon z kuchnią na dwie kondygnacje
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(GX1, YN, GX2, GY1), levels=2,
       ext={"N": "solid", "S": "glass", "E": "glass_slide"}, kitchen_at="W")
# skrzydło W – amfilada od frontu: garderoba (z WC), wiatrołap, herbaciarnia, pracownia
WC = rect(4.1, GY1, GX1, 8.0)
H.room("gar0", "Garderoba", "garderoba", rect(XW, GY1, GX1, 8.8).difference(WC), ext={"W": "solid"})
H.room("wc", "WC", "wc", WC)
H.room("wia", "Wiatrołap", "wiatrolap", rect(XW, 8.8, GX1, 10.85), ext={"W": "solid"})
H.room("her", "Herbaciarnia", "herbaciarnia", rect(XW, 10.85, GX1, GY2), ext={"W": "solid"}, garden="glass")
H.room("pra", "Pracownia", "pracownia", rect(XW, GY2, GX1, YS), ext={"W": "solid", "S": "windows"})
# skrzydło S – biuro przeszklone z obu stron, na końcu pralnia z wyjściem na zewnątrz
H.room("biu", "Biuro", "biuro", rect(GX1, GY2, 13.6, YS), ext={"S": "glass_slide"})
H.room("pral", "Pralnia", "pralnia", rect(13.6, GY2, XS, YS), ext={"E": "solid", "N": "solid", "S": "windows_sq"},
       garden="band_high")
# taras na gruncie przed biurem
H.room("tar0", "Taras", "taras", rect(GX1, YS, 13.6, 21.0))
# wschód – patio częściowo zadaszone
H.room("pat", "Patio", "patio", rect(GX2, YN, 19.5, 9.6), roof=rect(GX2, YN, 19.5, 4.6))

# ---------------------------------------------------------------- piętro (+3,4)
H.room("hol1", "Hol", "hol", rect(XW, YN, GX1, GY1), level=1, ext={"N": "slits", "W": "slits"}, furn=False)
H.room("bib", "Biblioteka", "biblioteka", rect(XW, GY1, GX1, 10.4), level=1, ext={"W": "windows", "E": "glass"})
H.room("laz1", "Łazienka", "lazienka", rect(XW, 10.4, 4.2, 13.6), level=1, ext={"W": "band_high"})
H.room("prz", "Przejście", "korytarz", rect(4.2, 10.4, GX1, 13.6), level=1, ext={"E": "glass"}, furn=False)
H.room("syp1", "Sypialnia", "sypialnia", rect(XW, 13.6, GX1, YS), level=1,
       ext={"W": "windows", "S": "glass", "E": "glass"})
T1B = rect(15.25, GY2, 16.35, 16.0)
H.room("t1", "Taras", "taras", rect(GX1, GY2, XS, YS).difference(T1B), level=1, dz=DZ)
H.room("t1b", "Podest", "taras", T1B, level=1, dz=DZ, enclose="open", furn=False)

# ---------------------------------------------------------------- II piętro (+6,8)
H.room("hol2", "Hol", "hol", rect(XW, YN, GX1, GY1), level=2, ext={"N": "slits", "W": "slits", "S": "glass"}, furn=False)
H.room("gar2", "Garderoba", "garderoba", rect(GX1, YN, 9.0, 3.4), level=2, ext={"N": "solid"})
H.room("laz2", "Łazienka", "lazienka", rect(GX1, 3.4, 9.0, GY1), level=2, ext={"S": "band_high"})
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(9.0, YN, GX2, GY1), level=2,
       ext={"S": "glass", "E": "glass_slide", "N": "band"})
T2B = rect(5.0, 15.2, GX1, 16.3)
H.room("t2", "Taras", "taras", rect(XW, GY1, GX1, YS).difference(T2B), level=2, dz=DZ)
H.room("t2b", "Podest", "taras", T2B, level=2, dz=DZ, enclose="open", furn=False)

# ---------------------------------------------------------------- dach (+10,2)
T3B = rect(2.25, 5.0, 3.35, GY1)
H.room("t3", "Taras na dachu", "taras", rect(XW, YN, 8.5, GY1).difference(T3B), level=3, dz=DZ)
H.room("t3b", "Podest", "taras", T3B, level=3, dz=DZ, enclose="open", furn=False)

# ---------------------------------------------------------------- schody
# wewnętrzne: dwa biegi U jeden nad drugim w holu NW
H.stair("U", level=0, rect=(2.25, 1.3, 4.3, 5.6), up="N")
H.stair("U", level=1, rect=(2.25, 1.3, 4.3, 5.6), up="N")
# zewnętrzne: spirala tarasów (wschód → południe → zachód)
H.stair("straight", level=0, rect=(15.25, 9.6, 16.35, 14.8), up="S")
H.stair("straight", level=1, rect=(6.25, 15.2, 11.45, 16.3), up="W")
H.stair("straight", level=2, rect=(2.25, 6.25, 3.35, 11.45), up="N")

# ---------------------------------------------------------------- połączenia
# parter (at dla krawędzi poziomych liczone od wschodu)
H.connect("hol0", "gar0", "open")
H.connect("gar0", "wc", "door")
H.connect("hol0", "sal", "wide", at=0.5)
H.connect("gar0", "wia", "door", at=0.6)
H.connect("wia", "her", "door", at=0.25)
H.connect("her", "pra", "door", at=0.25)
H.connect("pra", "biu", "double")
H.connect("pral", "og", "door")
# piętro
H.connect("hol1", "bib", "open")
H.connect("bib", "prz", "door")
H.connect("prz", "laz1", "door")
H.connect("prz", "syp1", "door")
H.connect("syp1", "t1", "slide", at=0.7)
# II piętro
H.connect("hol2", "gar2", "door", at=0.7)
H.connect("gar2", "syp", "door", at=0.7)
H.connect("laz2", "syp", "door")
H.connect("hol2", "t2", "slide", at=0.3)

H.entrance("wia", "W")
H.window("sal", "N", at=0.78, width=3.2, sill=0.5, head=2.6)
H.window("her", "W", at=0.2, width=1.2, sill=0.3, head=0.9)   # niskie okno przy tatami
H.exit("pral", "E", kind="door", width=1.0)

# ---------------------------------------------------------------- teren
H.path(rect(-6.0, 9.1, 1.8, 10.5))
H.path(rect(16.7, 16.4, 22.0, 17.6))
H.tree(-3.5, 22.5, "klon")
H.tree(23.5, -2.0, "sosna")
H.tree(-4.0, -1.5, "brzoza")
H.cut("A–A", (7.5, -1.5), (7.5, 22.5))
H.cut("B–B", (-0.5, 11.2), (21.0, 11.2))
