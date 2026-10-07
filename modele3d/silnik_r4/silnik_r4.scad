// =====================================================================
//  Model silnika rzędowego R4 do wydruku 3D (przekrój, ruchomy)
//  Wał korbowy, 4 korbowody, 4 tłoki, sworznie, koło zamachowe
//  z korbką, blok cylindrów z okienkami i podstawa z łożyskami.
//
//  Wszystkie części drukują się BEZ podpór, każda już ułożona
//  w orientacji do druku. Składa się bez kleju (na zatrzask).
//
//  Użycie w OpenSCAD:
//    czesc = "zlozenie"  -> podgląd całości (View > Animate: FPS 20, Steps 72)
//    czesc = "podstawa" | "blok" | "wal" | "korbowod" | "tlok"
//          | "sworzen" | "kolo" | "male_czesci"
//  Eksport z linii poleceń:  ./eksport.sh
// =====================================================================

czesc = "zlozenie"; // [zlozenie, podstawa, blok, wal, korbowod, tlok, sworzen, kolo, male_czesci]
kat   = $t * 360;   // kąt obrotu wału w złożeniu (animacja)

$fn = 64;

// ---------- parametry główne (mm) ----------
n_cyl     = 4;     // liczba cylindrów (wał płaski: 0-180-180-0)
srednica  = 24;    // średnica cylindra
skok      = 20;    // skok tłoka
dl_korb   = 40;    // rozstaw osi korbowodu
podzialka = 32;    // odstęp między osiami cylindrów

// ---------- tolerancje (dopasuj do swojej drukarki) ----------
luz        = 0.2;  // luz promieniowy łożysk ślizgowych
luz_tloka  = 0.25; // luz promieniowy tłoka w cylindrze
zatrzask   = 7.6;  // szerokość „ust” zatrzasków (czop ma 8 mm na spłaszczeniach)
luz_kolka  = 0.15; // pasowanie koła zamachowego na wałku

// ---------- wymiary pochodne ----------
r_korby   = skok / 2;
d_czopu   = 10;           // średnica czopów (głównych i korbowych)
plaskie   = 4;            // spłaszczenia czopów na ±4 mm -> wał drukuje się na płasko
dl_czopu_k= 10;           // długość czopu korbowego
gr_ramienia = 5;          // grubość ramienia wału
gr_korb   = 7;            // grubość korbowodu
d_sworznia= 4;
h_tloka   = 20;
sw_od_denka = 12;         // odległość osi sworznia od denka tłoka
d_tloka   = srednica - 2 * luz_tloka;

wys_osi   = 28;           // wysokość osi wału nad stołem
gr_plyty  = 4;            // grubość płyty podstawy
wys_kadl  = wys_osi + 24; // wysokość górnej krawędzi skrzyni = spód bloku
h_bloku   = 40;
szer_bloku= srednica + 6;
gr_lozyska= 6;
wysuw_walu= 18;           // przedni koniec wału pod koło zamachowe

function x_cyl(i)  = i * podzialka;
function x_loz(j)  = (j - 0.5) * podzialka;
function znak(i)   = (i == 0 || i == n_cyl - 1) ? 1 : -1;   // 0°,180°,180°,0°

x_pocz  = x_loz(0) - (podzialka - dl_czopu_k - 2 * gr_ramienia) / 2;
x_przod = x_pocz - wysuw_walu;          // koniec wału po stronie koła
x_tyl   = x_loz(n_cyl) + (podzialka - dl_czopu_k - 2 * gr_ramienia) / 2;
x_kola  = x_pocz - 10;                  // wewnętrzna powierzchnia koła zamachowego

// ---------- pomocnicze ----------
module walec_x(d, x0, x1) {
    translate([x0, 0, 0]) rotate([0, 90, 0]) cylinder(d = d, h = x1 - x0);
}

// otwór poziomy wzdłuż osi X, w kształcie łezki (szpic do +Z) – bez podpór
module lezka_x(d, dl) {
    rotate([0, 90, 0]) linear_extrude(height = dl, center = true)
        hull() {
            circle(d = d);
            translate([-d / 2 * 1.414, 0]) square(0.01, center = true);
        }
}

// =====================================================================
//  WAŁ KORBOWY – układ do druku: oś wzdłuż X, wykorbienia w płaszczyźnie XY
// =====================================================================
module wal() {
    intersection() {
        union() {
            for (i = [0 : n_cyl - 1]) {
                xc = x_cyl(i);
                s  = znak(i);
                // ramiona z przeciwwagą
                for (x0 = [xc - dl_czopu_k / 2 - gr_ramienia, xc + dl_czopu_k / 2])
                    translate([x0, 0, 0]) rotate([0, 90, 0])
                        linear_extrude(height = gr_ramienia)
                            hull() {
                                circle(r = 9);
                                translate([0, s * r_korby]) circle(r = 8);
                            }
                // czop korbowy
                translate([0, s * r_korby, 0])
                    walec_x(d_czopu, xc - dl_czopu_k / 2 - 0.01, xc + dl_czopu_k / 2 + 0.01);
            }
            // czopy główne
            for (j = [0 : n_cyl]) {
                x0 = (j == 0)     ? x_przod : x_cyl(j - 1) + dl_czopu_k / 2 + gr_ramienia - 0.01;
                x1 = (j == n_cyl) ? x_tyl   : x_cyl(j)     - dl_czopu_k / 2 - gr_ramienia + 0.01;
                walec_x(d_czopu, x0, x1);
            }
        }
        // spłaszczenie góra/dół – płaskie leżenie na stole i blokada koła zamachowego
        translate([x_przod - 1, -50, -plaskie]) cube([x_tyl - x_przod + 2, 100, 2 * plaskie]);
    }
}

// =====================================================================
//  KORBOWÓD – leży płasko; stopa (zatrzask) w (0,0), oczko w (0,dl_korb)
// =====================================================================
module korbowod() {
    R_stopy = d_czopu / 2 + luz + 2.6;
    linear_extrude(height = gr_korb)
        difference() {
            union() {
                circle(r = R_stopy);
                hull() {
                    circle(r = 5);
                    translate([0, dl_korb]) circle(r = d_sworznia / 2 + 2.4);
                }
            }
            circle(d = d_czopu + 2 * luz);
            translate([0, dl_korb]) circle(d = d_sworznia + 0.4);
            // „usta” zatrzasku z fazką ułatwiającą wciśnięcie
            polygon([[-zatrzask / 2, 0], [zatrzask / 2, 0],
                     [zatrzask / 2, -R_stopy + 1.8], [zatrzask / 2 + 1.6, -R_stopy - 0.5],
                     [-zatrzask / 2 - 1.6, -R_stopy - 0.5], [-zatrzask / 2, -R_stopy + 1.8]]);
            // odciążenie trzonu
            hull() {
                translate([0, R_stopy + 5]) circle(r = 1.3);
                translate([0, dl_korb - 9]) circle(r = 1);
            }
        }
}

// =====================================================================
//  TŁOK – drukowany denkiem do stołu; sworzeń wzdłuż X
// =====================================================================
module tlok() {
    sc = 1.6;             // ścianka
    denko = 3;
    difference() {
        union() {
            difference() {
                cylinder(d = d_tloka, h = h_tloka);
                translate([0, 0, denko]) cylinder(d = d_tloka - 2 * sc, h = h_tloka);
            }
            // piasty sworznia
            intersection() {
                cylinder(d = d_tloka - 0.1, h = h_tloka);
                for (m = [0, 1]) mirror([m, 0, 0])
                    translate([gr_korb / 2 + 1, -5, 0])
                        cube([d_tloka, 10, sw_od_denka + d_sworznia / 2 + 3]);
            }
        }
        translate([0, 0, sw_od_denka]) lezka_x(d_sworznia + 0.3, d_tloka + 2);
        // rowki pierścieni (ozdobne)
        for (z = [2.2, 4.6, 7.0])
            translate([0, 0, z]) difference() {
                cylinder(d = d_tloka + 1, h = 0.8);
                translate([0, 0, -1]) cylinder(d = d_tloka - 1.0, h = 3);
            }
    }
}

// =====================================================================
//  SWORZEŃ TŁOKOWY – leży na stole (spłaszczony)
// =====================================================================
module sworzen() {
    dl = d_tloka - 1;
    translate([0, 0, 1.6]) intersection() {
        rotate([0, 90, 0]) cylinder(d = d_sworznia, h = dl, center = true);
        cube([dl + 1, d_sworznia + 1, 3.2], center = true);
    }
}

// =====================================================================
//  KOŁO ZAMACHOWE z korbką – leży na stole; otwór w kształcie „D-D”
// =====================================================================
module kolo() {
    R = wys_osi - gr_plyty - 2;   // musi minąć płytę podstawy
    difference() {
        union() {
            difference() {
                cylinder(r = R, h = 6);
                translate([0, 0, 3]) cylinder(r = R - 4, h = 10);
            }
            cylinder(r = 9, h = 8);
            // korbka
            translate([R - 8, 0, 0]) cylinder(d = 6, h = 18);
            translate([R - 8, 0, 18]) sphere(d = 6);
        }
        intersection() {
            translate([0, 0, -1]) cylinder(d = d_czopu + 2 * luz_kolka, h = 20);
            cube([30, 2 * (plaskie + luz_kolka), 50], center = true);
        }
        for (a = [36 : 72 : 359])
            rotate(a) translate([(R + 9) / 2 - 2, 0, -1]) cylinder(d = 7, h = 10);
    }
}

// =====================================================================
//  PODSTAWA – płyta, łożyska główne (zatrzaskowe), tylna ściana, słupki
// =====================================================================
x_ram0 = x_loz(0) - 10;
x_ram1 = x_loz(n_cyl) + 10;
y_tyl  = 20;     // tylna ściana (poza zasięgiem wykorbień: 18 mm)
y_przod= -20;

function kolki() = [
    [x_ram0 + 3, y_przod + 3], [x_ram1 - 3, y_przod + 3],
    [x_ram0 + 4, y_tyl + 2.5], [(x_ram0 + x_ram1) / 2, y_tyl + 2.5], [x_ram1 - 4, y_tyl + 2.5]
];

module lozysko() {
    R = d_czopu / 2 + luz + 3.5;
    difference() {
        hull() {
            translate([-gr_lozyska / 2, -11, 0]) cube([gr_lozyska, 22, 1]);
            translate([0, 0, wys_osi]) rotate([0, 90, 0]) cylinder(r = R, h = gr_lozyska, center = true);
        }
        translate([0, 0, wys_osi]) rotate([0, 90, 0]) cylinder(d = d_czopu + 2 * luz, h = gr_lozyska + 2, center = true);
        // usta zatrzasku z fazką
        translate([0, 0, wys_osi]) rotate([90, 0, 90])
            linear_extrude(height = gr_lozyska + 2, center = true)
                polygon([[-zatrzask / 2, 0], [zatrzask / 2, 0], [zatrzask / 2, R - 2.2],
                         [zatrzask / 2 + 1.6, R + 0.5], [-zatrzask / 2 - 1.6, R + 0.5],
                         [-zatrzask / 2, R - 2.2]]);
    }
}

module podstawa() {
    x_p0 = x_przod - 4;
    x_p1 = x_ram1 + 10;
    // płyta
    difference() {
        translate([x_p0, y_przod - 6, 0]) cube([x_p1 - x_p0, y_tyl + 5 - y_przod + 12, gr_plyty]);
        // napis
        translate([(x_ram0 + x_ram1) / 2, y_przod - 3.2, gr_plyty - 0.6])
            linear_extrude(1) text("R4", size = 4, halign = "center", valign = "center",
                                   font = "Liberation Sans:style=Bold");
    }
    // tylna ściana
    translate([x_ram0, y_tyl, 0]) cube([x_ram1 - x_ram0, 5, wys_kadl]);
    // przednie słupki
    for (x = [x_ram0, x_ram1 - 6]) translate([x, y_przod, 0]) cube([6, 6, wys_kadl]);
    // łożyska
    for (j = [0 : n_cyl]) translate([x_loz(j), 0, 0]) lozysko();
    // kołki ustalające
    for (k = kolki()) translate([k[0], k[1], wys_kadl - 0.01]) {
        cylinder(d = 4, h = 2.8);
        translate([0, 0, 2.8]) cylinder(d1 = 4, d2 = 3.2, h = 0.6);
    }
}

// =====================================================================
//  BLOK CYLINDRÓW – drukowany płytą montażową do stołu
// =====================================================================
module blok() {
    gr_pl = 4;
    okno  = 14;
    difference() {
        union() {
            translate([x_ram0, y_przod, 0]) cube([x_ram1 - x_ram0, y_tyl + 5 - y_przod, gr_pl]);
            translate([x_cyl(0) - podzialka / 2, -szer_bloku / 2, 0])
                cube([n_cyl * podzialka, szer_bloku, h_bloku]);
            // pionowe żebra z tyłu (ozdoba, drukują się bez podpór)
            for (x = [x_cyl(0) - podzialka / 2 + 3 : 6 : x_cyl(n_cyl - 1) + podzialka / 2 - 3])
                translate([x - 1, szer_bloku / 2 - 0.01, gr_pl - 0.01]) cube([2, 3, h_bloku - gr_pl - 3]);
        }
        for (i = [0 : n_cyl - 1]) translate([x_cyl(i), 0, 0]) {
            translate([0, 0, -1]) cylinder(d = srednica, h = h_bloku + 2);
            translate([0, 0, -0.01]) cylinder(d1 = srednica + 2.4, d2 = srednica, h = 1.2);   // fazka wejścia tłoka
            translate([0, 0, h_bloku - 1.2 + 0.01]) cylinder(d1 = srednica, d2 = srednica + 2.4, h = 1.2);
            // okienko przekroju
            translate([-okno / 2, -szer_bloku, 9]) cube([okno, szer_bloku, h_bloku - 15]);
        }
        for (k = kolki()) translate([k[0], k[1], -1]) cylinder(d = 4.4, h = gr_pl + 2);
    }
}

// =====================================================================
//  ZŁOŻENIE (podgląd / animacja)
// =====================================================================
// położenia części ruchomych dla kąta wału t
function cz_korb(i, t) = let(a = 90 + t, s = znak(i))
    [s * r_korby * cos(a), wys_osi + s * r_korby * sin(a)];          // [y, z] czopu korbowego
function z_sworznia(i, t) = let(c = cz_korb(i, t)) c[1] + sqrt(dl_korb * dl_korb - c[0] * c[0]);

module na_wale(t)  { translate([0, 0, wys_osi]) rotate([90 + t, 0, 0]) children(); }
module na_kole(t)  { translate([x_kola, 0, wys_osi]) rotate([t, 0, 0]) rotate([0, -90, 0]) children(); }
module na_korb(i, t) {
    c = cz_korb(i, t);
    translate([x_cyl(i), c[0], c[1]]) rotate([90, 0, 90]) rotate([0, 0, asin(c[0] / dl_korb)])
        translate([0, 0, -gr_korb / 2]) children();
}
module na_tloku(i, t) { translate([x_cyl(i), 0, z_sworznia(i, t)]) rotate([180, 0, 0]) translate([0, 0, -sw_od_denka]) children(); }

module zlozenie(t = kat) {
    color("SlateGray")   podstawa();
    color("LightSteelBlue", 0.55) translate([0, 0, wys_kadl]) blok();
    color("Goldenrod")   na_wale(t) wal();
    color("DarkRed")     na_kole(t) kolo();
    for (i = [0 : n_cyl - 1]) {
        color("Silver")    na_korb(i, t) korbowod();
        color("Gainsboro") na_tloku(i, t) tlok();
        color("DimGray")   translate([x_cyl(i), 0, z_sworznia(i, t) - 1.6]) sworzen();
    }
}

// zestaw drobnych części na jeden stół (4 korbowody, 4 tłoki, 4 sworznie)
module male_czesci() {
    for (i = [0 : 3]) translate([i * 22, 0, 0]) korbowod();
    for (i = [0 : 3]) translate([i * 27 + 2, 70, 0]) tlok();
    for (i = [0 : 3]) translate([102, 10 + i * 8, 0]) sworzen();
}

if      (czesc == "zlozenie")    zlozenie();
else if (czesc == "podstawa")    podstawa();
else if (czesc == "blok")        blok();
else if (czesc == "wal")         translate([0, 0, plaskie]) wal();
else if (czesc == "korbowod")    korbowod();
else if (czesc == "tlok")        tlok();
else if (czesc == "sworzen")     sworzen();
else if (czesc == "kolo")        kolo();
else if (czesc == "male_czesci") male_czesci();
