"""P06 · Dwa pasma (wersja 2) – dwa równoległe drewniane pasma, między nimi ukryty ogród wodny; na dachach przewiązek tarasy, nad pasmem północnym moduły piętra."""
from silnik import House, rect, poly

H = House(
    "p06", "Dwa pasma",
    "Dwa równoległe drewniane pasma po 4,2 m głębokości – dzienne od południa i nocne od północy – a między nimi schowany ogród z podłużnym basenem pod przesuwnym szklanym dachem. Oba końce ogrodu domykają parterowe przewiązki, a na ich dachach leżą dwa tarasy piętra.",
    style=dict(fasada="drewno", dach="sedum", akcent="modrzew"),
    concept=[
        "Ogród wodny 7,2 × 4,8 m leży między pasmami i jest ze wszystkich stron obudowany pokojami: od zachodu biblioteką, od wschodu galerią wejściową z kredensem. Pokoje przy ogrodzie mają od zewnątrz tylko okna, szczeliny i wstęgi, więc ogrodu nie widać ani z drogi, ani od sąsiadów.",
        "Wchodzi się od północy przez wiatrołap, który nie dotyka ogrodu. Dopiero galeria wejściowa za drugimi drzwiami otwiera się szkłem na wodę; z niej idzie się do salonu, do kredensu przy kuchni albo do pokoju muzycznego.",
        "Parter obchodzi się dookoła bez korytarzy: galeria wejściowa, pokój muzyczny, galeria ze schodami kręconymi, pracownia z północnym szkłem, biblioteka w zachodniej przewiązce, salon i z powrotem do galerii.",
        "Salon z kuchnią ma 6,6 m wysokości i całą ścianę szklaną do ogrodu. Na południe wychodzi tylko na patio za murem 2,6 m, częściowo zadaszone; dalej na wschód, nad blatem kuchni, biegnie wysoka wstęga okien.",
        "Dachy parterowych części to tarasy z balustradą: zachodni na dachu biblioteki i pralni, przy sypialni, obiega zachodni szczyt salonu; wschodni na dachu galerii wejściowej i wiatrołapu, przy biurze. Między nimi leży szklany dach ogrodu, którego zachodnia połowa latem zsuwa się nad wschodnią.",
        "Na piętrze pasma północnego są moduły w amfiladzie: sypialnia ze szklaną ścianą od zachodu, łazienka z przelotową garderobą, galeria piętra nad schodami i biuro przeszklone na pola od północy, na dach ogrodu od południa i na taras od wschodu.",
    ],
    notes=dict(
        lato="Zachodnia połowa szklanego dachu zjeżdża nad wschodnią i ogród z basenem staje się otwartym dziedzińcem między pasmami; z obu tarasów zagląda się do niego z góry, a salon otwiera się szeroko na patio za murem.",
        zima="Dach jest zamknięty, ogród z wodą zbiera ciepło słońca i oddaje je wieczorem, a oba pasma mają od środka ścianę do ciepłego ogrodu zamiast do mrozu; mur patio osłania salon od wiatru.",
        technologia="Panele CLT (drewno klejone krzyżowo) na ściany i stropy obu pasm i przewiązek – proste elementy do 13,4 m; tarasy na stropach CLT z warstwą spadkową i deskami, dach szklany systemowy na stalowej ramie, elewacja z deski modrzewiowej.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.2)

# ogród między pasmami: 7,2 × 4,8 m, podłużny basen (styl "woda"), dach przesuwny, dwie brzozy w narożnikach
H.ogrod("og", "Ogród wodny", rect(3.4, 4.2, 10.6, 9.0), roof_type="slide", style="woda", seed=11,
        trees=[("brzoza", 4.0, 8.4, 0.5, 3.2), ("brzoza", 10.0, 8.4, 0.45, 3.0)])

# ---- pasmo północne, parter
H.room("pra", "Pracownia", "pracownia", rect(0, 0, 3.4, 4.2), ext={"N": "glass", "W": "band_high"})
H.room("gal", "Galeria ze schodami", "galeria", rect(3.4, 0, 7.8, 4.2), ext={"N": "slits"})
H.room("muz", "Pokój muzyczny", "muzyczny", rect(7.8, 0, 10.6, 4.2), ext={"N": "windows"})
H.room("wia", "Wiatrołap", "wiatrolap", rect(10.6, 0, 13.4, 2.2), ext={"N": "slits", "E": "solid"})
H.room("wc", "WC", "wc", rect(11.8, 2.2, 13.4, 3.8))
H.room("galw", "Galeria wejściowa", "galeria",
       poly((10.6, 2.2), (11.8, 2.2), (11.8, 3.8), (13.4, 3.8), (13.4, 6.6), (11.8, 6.6), (11.8, 9.0), (10.6, 9.0)),
       ext={"E": "slits"})
H.room("kre", "Kredens", "spizarnia", rect(11.8, 6.6, 13.4, 9.0))
H.stair("spiral", level=0, center=(6.6, 1.6), r=1.0, start=180, sweep=300, n=16)

# ---- przewiązka zachodnia
H.room("bib", "Biblioteka", "biblioteka", rect(0, 4.2, 3.4, 9.0), ext={"W": "band_high"})

# ---- pasmo południowe: pralnia, wysoki salon z kuchnią, patio za murem
H.room("pral", "Pralnia", "pralnia", rect(0, 9.0, 2.0, 13.2))
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(2.0, 9.0, 13.4, 13.2), levels=2, kitchen_at="E",
       ext={"pat": "glass_slide", "S": "band_high", "E": "windows", "W": "band", "N": "band"})
H.room("pat", "Patio za murem", "patio", rect(2.0, 13.2, 8.0, 17.0), roof=rect(2.0, 13.2, 8.0, 15.0), enclose="gwall",
       label_at=(5.0, 16.55))

# ---- piętro: moduły w amfiladzie nad pasmem północnym + tarasy na dachach przewiązek
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(0, 0, 3.4, 4.2), level=1,
       ext={"W": "glass", "N": "band_high", "taW": "glass"})
H.room("laz", "Łazienka", "lazienka", rect(3.4, 0, 5.4, 2.2), level=1)
H.room("gard", "Garderoba", "garderoba", rect(3.4, 2.2, 5.4, 4.2), level=1)
H.room("galp", "Galeria piętra", "galeria", rect(5.4, 0, 8.6, 4.2), level=1, ext={"N": "slits", "S": "glass"})
H.room("biu", "Biuro", "biuro", rect(8.6, 0, 11.6, 4.2), level=1, ext={"N": "glass", "S": "glass", "taE": "glass"})
H.room("taW", "Taras zachodni", "taras",
       poly((0, 4.2), (3.4, 4.2), (3.4, 9.0), (2.0, 9.0), (2.0, 13.2), (0, 13.2)), level=1)
H.room("taE", "Taras wschodni", "taras",
       poly((11.6, 0), (13.4, 0), (13.4, 9.0), (10.6, 9.0), (10.6, 4.2), (11.6, 4.2)), level=1)

# ---- połączenia parteru (pętla bez korytarzy)
H.connect("wia", "galw", "door")
H.connect("galw", "wc", "door")
H.connect("galw", "muz", "door", at=0.8)
H.connect("galw", "kre", "door")
H.connect("galw", "sal", "door")
H.connect("kre", "sal", "door")
H.connect("muz", "gal", "double", at=0.8)
H.connect("gal", "pra", "door", at=0.25)
H.connect("pra", "bib", "door")
H.connect("bib", "sal", "double")
H.connect("bib", "pral", "door")
H.connect("pral", "sal", "door", at=0.15)
# ---- połączenia piętra (amfilada) i wyjścia na tarasy
H.connect("syp", "laz", "door", at=0.78)
H.connect("syp", "gard", "door", at=0.28)
H.connect("gard", "galp", "door", at=0.28)
H.connect("galp", "biu", "door", at=0.05)
H.connect("syp", "taW", "slide")
H.connect("biu", "taE", "slide")

H.entrance("wia", "N")
H.exit("pral", "W", kind="door", width=0.9)

# ---- teren
H.path(rect(11.3, -6.0, 12.7, -0.2))
H.tree(-4.0, 2.0, "brzoza")
H.tree(17.5, 11.0, "lipa")
H.tree(6.0, 21.0, "klon")
H.tree(16.5, -3.5, "sosna")

H.cut("A–A", (6.0, -2.5), (6.0, 19.0))
H.cut("B–B", (-2.5, 6.0), (16.0, 6.0))
