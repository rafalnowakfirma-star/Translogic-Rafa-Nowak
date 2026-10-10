"""P06 · Dwa pasma – dwa równoległe drewniane pasma, między nimi ogród wodny pod przesuwnym szklanym dachem."""
from silnik import House, rect, poly

H = House(
    "p06", "Dwa pasma",
    "Dwa równoległe drewniane pasma – dzienne od południa i nocne od północy – a między nimi ogród z podłużnym basenem pod przesuwnym szklanym dachem. Pasma spinają dwa niskie szklane mosty: biuro i biblioteka z wejściem.",
    style=dict(fasada="drewno", dach="sedum", akcent="modrzew"),
    concept=[
        "Ogród ma 10 × 7 m, a pośrodku podłużny basen 7 × 4 m z brzozami wokół; od drzwi biura prowadzi w głąb wody kładka z kamieni. Przykrywa go płaski szklany dach jak hala dworca: zachodnia połowa latem zsuwa się nad wschodnią.",
        "Biuro jest zachodnim mostem między pasmami: od wschodu szkło na wodę, od zachodu szkło na pole. Oś widoku biegnie przez cały dom – od drzwi wejściowych przez bibliotekę, nad wodą i przez biuro aż na łąkę.",
        "Wschodni most to wejście: wiatrołap z WC i biblioteka przeszklona od ogrodu i od strony podjazdu. Z biblioteki idzie się przez kredens do kuchni albo wprost do ogrodu.",
        "Pasmo nocne ma dwie kondygnacje, ale parter jest zabudowany tylko na zachodnim odcinku: pracownia wysoka na dwie kondygnacje z północnym światłem i galeria ze schodami. Dalej piętro stoi na słupach nad otwartym podcieniem, na który latem składa się szklana harmonijka ogrodu.",
        "Na piętrze pokoje dzieci i łazienki leżą od północy, a wzdłuż ogrodu biegnie przeszklona galeria. Sypialnia na końcu pasma ma szklaną ścianę od wschodu z balkonem.",
        "Pasmo dzienne to wysoki na dwie kondygnacje salon z kuchnią, otwarty szkłem na ogród i na południe. Na zachodnim końcu jest patio w połowie pod daszkiem, na wschodnim kredens i pralnia.",
    ],
    notes=dict(
        lato="Zachodnia połowa szklanego dachu zjeżdża nad wschodnią, harmonijka od podcienia się składa i ogród z basenem staje się przewiewnym dziedzińcem między pasmami; chłód znad wody ciągnie pod piętro na słupach.",
        zima="Dach i harmonijka są zamknięte; ogród z wodą zbiera ciepło słońca i oddaje je wieczorem, a oba pasma mają od środka ścianę do ciepłego ogrodu zamiast do mrozu.",
        technologia="Panele CLT (drewno klejone krzyżowo) na ściany i stropy obu pasm – długie, proste elementy do 16 m. Piętro nad podcieniem to sztywne pudło z CLT na słupach z drewna klejonego, ze stropem ocieplonym od spodu; mosty i dach ogrodu na stalowych ramach, elewacja z deski modrzewiowej.",
    ),
)
H.level(0, z=0.0, h=3.4)
H.level(1, z=3.4, h=3.4)

# ogród między pasmami: 10 × 7 m, podłużny basen (styl "woda"), dach przesuwny; od północy harmonijka na podcień
# (wierzchołki od krawędzi zachodniej: kładka z kamieni zaczyna się wtedy od drzwi biura, na osi widokowej)
H.ogrod("og", "Ogród wodny", poly((4.5, 13.0), (4.5, 6.0), (14.5, 6.0), (14.5, 13.0)), levels=2,
        roof_type="slide", style="woda", edge={"N": "fold", "*": "glass"}, seed=11)

# ---- most zachodni: biuro przeszklone od ogrodu i od pola
H.room("biu", "Biuro", "biuro", rect(0.5, 6.0, 4.5, 13.0), ext={"W": "glass_slide", "S": "windows"})

# ---- most wschodni: wejście, WC, biblioteka
H.room("wc", "WC", "wc", rect(14.5, 6.0, 16.1, 8.4))
H.room("wia", "Wiatrołap", "wiatrolap", rect(16.1, 6.0, 18.5, 8.4), ext={"E": "solid", "N": "band_high"})
H.room("bib", "Biblioteka", "biblioteka", rect(14.5, 8.4, 18.5, 13.0), ext={"E": "glass"})

# ---- pasmo nocne, parter: pracownia (2 kondygnacje), galeria ze schodami, podcień pod piętrem
H.room("pra", "Pracownia", "pracownia", rect(0.5, 0, 4.5, 6.0), levels=2, ext={"N": "glass", "W": "band_high", "S": "windows"})
H.room("gal", "Galeria", "galeria", rect(4.5, 0, 8.0, 6.0), ext={"N": "slits", "E": "solid"})
H.stair("straight", level=0, rect=(4.85, 0.3, 5.95, 5.3), up="S")
H.room("pod", "Podcień", "loggia", rect(8.0, 0, 21.5, 6.0), dz=0.2, roof="none", enclose="columns")

# ---- pasmo nocne, piętro: galeria wzdłuż ogrodu, pokoje od północy, sypialnia nad podcieniem
H.room("gp", "Galeria piętra", "galeria",
       poly((4.5, 0), (6.9, 0), (6.9, 4.4), (15.5, 4.4), (15.5, 6.0), (4.5, 6.0)),
       level=1, ext={"N": "band"}, garden="glass")
H.room("lazd", "Łazienka", "lazienka", rect(6.9, 0, 8.9, 4.4), level=1)
H.room("dz1", "Pokój dziecka", "pokoj", rect(8.9, 0, 12.2, 4.4), level=1, ext={"N": "band"})
H.room("dz2", "Pokój dziecka", "pokoj", rect(12.2, 0, 15.5, 4.4), level=1, ext={"N": "band"})
H.room("laz", "Łazienka", "lazienka", rect(15.5, 0, 17.5, 3.4), level=1)
H.room("gar", "Garderoba", "garderoba", rect(15.5, 3.4, 17.5, 6.0), level=1)
H.room("syp", "Sypialnia", "sypialnia_glowna", rect(17.5, 0, 21.5, 6.0), level=1,
       ext={"E": "glass_slide", "N": "band", "S": "solid"})
H.room("bal", "Balkon", "taras", rect(21.5, 0.5, 23.0, 5.5), level=1)

# ---- pasmo dzienne: patio, wysoki salon z kuchnią, kredens, pralnia
H.room("pat", "Patio", "patio", rect(-1.5, 13.0, 4.5, 18.4), roof=rect(1.0, 13.0, 4.5, 18.4))
H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(4.5, 13.0, 14.5, 18.4), levels=2, kitchen_at="E",
       ext={"S": "glass_slide", "W": "glass_slide", "E": "slits"})
H.room("kre", "Kredens", "spizarnia", rect(14.5, 13.0, 16.5, 18.4), ext={"S": "slits"})
H.room("pral", "Pralnia", "pralnia", rect(16.5, 13.0, 18.5, 18.4))

# ---- połączenia
H.connect("pra", "biu", "double")
H.connect("pra", "gal", "double", at=0.82)
H.connect("wia", "bib", "double")
H.connect("wia", "wc", "door")
H.connect("bib", "kre", "door")
H.connect("kre", "sal", "door", at=0.85)
H.connect("kre", "pral", "door")
H.connect("gp", "lazd", "door")
H.connect("gp", "dz1", "door")
H.connect("gp", "dz2", "door")
H.connect("gp", "gar", "door")
H.connect("gar", "syp", "door")
H.connect("syp", "laz", "door", at=0.2)
H.connect("gp", "pra", "glass")

H.entrance("wia", "E")
H.exit("gal", "E", kind="door")
H.exit("pral", "S", kind="door")

# ---- teren
H.path(rect(18.7, 6.6, 26.0, 7.8))
H.path(rect(4.5, 18.6, 14.5, 21.0))
H.tree(-6.0, 3.5, "brzoza")
H.tree(27.0, 17.0, "lipa")
H.tree(9.0, 25.0, "klon")
H.tree(24.5, -3.5, "sosna")

H.cut("A–A", (5.5, -3.0), (5.5, 22.5))
H.cut("B–B", (-4.0, 9.5), (27.0, 9.5))
