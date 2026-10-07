// =====================================================================
//  SILNIK V8 – działający model do wydruku 3D
//
//  Kinematyka jak w prawdziwym silniku OHV (np. Chevrolet small-block):
//   * układ cylindrów V 90°, wał korbowy krzyżowy (cross-plane 0-90-270-180),
//     dwa korbowody na każdym czopie, rzędy przesunięte o grubość korbowodu,
//   * kolejność zapłonu 1-8-4-3-6-5-7-2 (numeracja GM: lewy rząd 1-3-5-7),
//   * wałek rozrządu w „V” napędzany kołami zębatymi 1:2 (znaczniki ustawienia),
//   * 16 popychaczy płaskich -> drążki -> dźwigienki zaworowe (przełożenie 1,25)
//     -> zawory ze sprężynami; dolot od strony V, wydech na zewnątrz,
//   * fazy rozrządu: ssanie maks. 105° po GMP, wydech maks. 105° przed GMP.
//
//  Każda część jest już ułożona do druku bez podpór (czesc = "<nazwa>").
//  Podgląd ruchu: czesc = "zlozenie", View > Animate (FPS 25, Steps 144).
// =====================================================================

czesc = "zlozenie";
kat   = $t * 720;          // kąt wału korbowego (pełny cykl 4-suwu = 720°)
pokaz_osprzet  = true;     // kolektory, gaźnik, filtr, aparat zapłonowy
pokaz_pokrywy  = false;    // pokrywy zaworów (zasłaniają dźwigienki)
przekroj       = true;     // okienka w lewym rzędzie cylindrów

$fn = 48;
s2 = sqrt(0.5);

// --------------------- układ korbowy ---------------------
srednica = 26;     // średnica cylindra
r_k      = 11;     // promień wykorbienia (skok 22)
dl_korb  = 44;     // rozstaw osi korbowodu
podz     = 34;     // odstęp czopów korbowych
przes    = 3.5;    // przesunięcie rzędu L/P względem środka czopu
d_ck     = 10;     // czop korbowy
d_cg     = 12;     // czop główny
dl_ck    = 13;     // długość czopu korbowego (2 korbowody)
gr_ram   = 5;      // grubość ramienia wału
gr_korb  = 6;      // grubość korbowodu
d_sw     = 5;      // sworzeń tłokowy
h_tl     = 22;     // wysokość tłoka
sw_den   = 13;     // oś sworznia od denka
d_tl     = srednica - 0.5;
fi       = [0, 90, 270, 180];   // kąty wykorbień (od przodu)

// --------------------- blok ---------------------
a_tul  = 23;       // dolna krawędź tulei (od osi wału, wzdłuż osi cylindra)
a_deck = 72;       // płaszczyzna przylgowa głowicy
w_bl   = 16;       // pół-szerokość rzędu
r_kom  = 21.5;     // komora korbowa
x_bl0  = -21;  x_bl1 = 123;
z_doliny = 50;     // dno „V”

// --------------------- rozrząd ---------------------
z_cam  = 36;       // oś wałka rozrządu nad osią wału (= rozstaw kół zębatych)
r_tun  = 10.1;     // tunel wałka
d_jr   = 19.6;     // czopy wałka
r_baz  = 7;  r_nos = 5.5;  e_nos = 3.5;   // krzywka: wznios 2 mm
szer_kr = 4;
d_pop  = 7.5;  dl_pop = 14;               // popychacz
r_kul  = 1.8;  r_gn = 1.95;  d_drz = 2.6;  // drążek: kulki, gniazda, trzon
a_gl1  = 88;  w_gl0 = -17;  w_gl1 = 28;  // głowica: góra, boki
d_zaw  = 9;  gr_zaw = 1.2;  d_trz = 3;  a_tip = 96;  a_kiesz = 83;
piv    = [11.7, 99.5];   // oś dźwigienek [w, a]
cup    = [21, 95];       // gniazdo drążka w dźwigience
pad_c  = [0, 99];  r_pad = 3;   // nosek dźwigienki naciska trzonek zaworu

// --------------------- tolerancje ---------------------
luz = 0.2;

// =====================================================================
//  układy współrzędnych
//  rząd b: 0 = lewy (y<0), 1 = prawy; [x, w, a]: a – wzdłuż osi cylindra,
//  w – poprzecznie (dodatnie w stronę „V”)
// =====================================================================
function u(b)  = b == 0 ? [0, -s2, s2] : [0, s2, s2];
function wv(b) = b == 0 ? [0,  s2, s2] : [0, -s2, s2];
module bank(b) {
    multmatrix([[1, 0, 0, 0], [0, wv(b)[1], u(b)[1], 0], [0, wv(b)[2], u(b)[2], 0], [0, 0, 0, 1]]) children();
}
function x_pin(c)   = c * podz;
function x_loz(j)   = (j - 0.5) * podz;            // -17, 17, 51, 85, 119
function x_cyl(b, c) = x_pin(c) + (b == 0 ? -przes : przes);
function x_zaw(b, c, v) = x_cyl(b, c) + (v == 0 ? -6.5 : 6.5);

// pryzmat wzdłuż osi X z profilu 2D w płaszczyźnie (y, z)
module px(x0, dl) { translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(dl) children(); }
// łezka (otwór poziomy bez podpór), szpic w +Y; obc – obcięcie szpica
module lza2d(r, obc = 0) {
    if (obc > 0) intersection() {
        hull() { circle(r = r); translate([0, r * sqrt(2)]) square(0.01, center = true); }
        translate([-2 * r, -2 * r]) square([4 * r, 2 * r + obc]);
    }
    else hull() { circle(r = r); translate([0, r * sqrt(2)]) square(0.01, center = true); }
}
// profil „D” (klin) – spłaszczenie po stronie +X
module d2d(r, plaski) { intersection() { circle(r = r); translate([-2 * r, -2 * r]) square([2 * r + plaski, 4 * r]); } }

// =====================================================================
//  KINEMATYKA
// =====================================================================
function pin_yz(c, t) = r_k * [cos(fi[c] + t), sin(fi[c] + t)];
function pin_bank(b, c, t) = let(p = pin_yz(c, t))
    [p[0] * wv(b)[1] + p[1] * wv(b)[2], p[0] * u(b)[1] + p[1] * u(b)[2]];      // [w, a]
function a_sw(b, c, t) = let(q = pin_bank(b, c, t)) q[1] + sqrt(dl_korb * dl_korb - q[0] * q[0]);

cam_c = [z_cam * s2, z_cam * s2];                 // oś wałka w układzie rzędu [w, a]
dvec  = (cup - cam_c) / norm(cup - cam_c);        // oś popychacza i drążka
delta = atan2(-dvec[0], dvec[1]);
L_drz = norm(cup - cam_c) - (r_baz + dl_pop);     // rozstaw kulek drążka
function alfa_d(b) = let(e = dvec[0] * wv(b) + dvec[1] * u(b)) atan2(e[2], e[1]);

// GMP sprężania (kąt wału) – kolejność 1-8-4-3-6-5-7-2
T   = [[135, 405, 585, 675], [45, 315, 495, 225]];
typ = [[0, 1], [1, 0], [0, 1], [1, 0]];           // 0 = wydech, 1 = ssanie (W-S S-W W-S S-W)
function th_max(b, c, v) = T[b][c] + (typ[c][v] == 1 ? 465 : 255);
function nos0(b, c, v)   = alfa_d(b) + th_max(b, c, v) / 2;
function wznios(b, c, v, t) = let(p = nos0(b, c, v) - t / 2 - alfa_d(b)) max(0, r_nos + e_nos * cos(p) - r_baz);

function rot2(v, g) = [v[0] * cos(g) - v[1] * sin(g), v[0] * sin(g) + v[1] * cos(g)];
function cupg(g) = piv + rot2(cup - piv, g);
function fg(g, B) = norm(cupg(g) - B) - L_drz;
function newton(g, B, n) = n == 0 ? g :
    let(f = fg(g, B), df = (fg(g + 0.01, B) - f) / 0.01) newton(g - f / df, B, n - 1);

// =====================================================================
//  WAŁ KORBOWY (składany z części, klejony)
// =====================================================================
module klucz2d(R) d2d(R - 0.4, R - 1.2);

module ramie2d() {
    difference() {
        union() {
            hull() { circle(r = 10); translate([r_k, 0]) circle(r = 7.5); }
            hull() {
                circle(r = 10);
                intersection() {
                    circle(r = 19);
                    polygon([[0, 0], [-40, 40 * tan(50)], [-40, -40 * tan(50)]]);
                }
            }
        }
        offset(delta = 0.1) klucz2d(d_cg / 2);
        translate([r_k, 0]) offset(delta = 0.1) klucz2d(d_ck / 2);
    }
}
module ramie() linear_extrude(gr_ram) ramie2d();

module czop_korbowy() {
    linear_extrude(4.6) klucz2d(d_ck / 2);
    translate([0, 0, 4.6]) cylinder(d = d_ck, h = dl_ck);
    translate([0, 0, 4.6 + dl_ck]) linear_extrude(4.6) klucz2d(d_ck / 2);
}
dl_cg = podz - dl_ck - 2 * gr_ram;     // 11
module czop_glowny(dfi) {
    linear_extrude(4.6) klucz2d(d_cg / 2);
    translate([0, 0, 4.6]) cylinder(d = d_cg, h = dl_cg);
    translate([0, 0, 4.6 + dl_cg]) rotate(dfi) linear_extrude(4.6) klucz2d(d_cg / 2);
}
dl_nosa = 21.5;
module czop_przedni() {
    linear_extrude(dl_nosa) d2d(5, 4);
    translate([0, 0, dl_nosa]) cylinder(d = d_cg, h = dl_cg);
    translate([0, 0, dl_nosa + dl_cg]) linear_extrude(4.6) klucz2d(d_cg / 2);
}
module czop_tylny() {
    linear_extrude(4.6) klucz2d(d_cg / 2);
    translate([0, 0, 4.6]) cylinder(d = d_cg, h = dl_cg);
    translate([0, 0, 4.6 + dl_cg]) linear_extrude(12.5) d2d(5, 4);
}
x_nosa = x_loz(0) - dl_cg / 2 - dl_nosa;     // -44

module wal_zlozony() {
    for (c = [0 : 3]) rotate([fi[c], 0, 0]) {
        for (x0 = [x_pin(c) - dl_ck / 2 - gr_ram, x_pin(c) + dl_ck / 2]) px(x0, gr_ram) ramie2d();
        translate([x_pin(c) - dl_ck / 2 - 4.6, r_k, 0]) rotate([90, 0, 90]) czop_korbowy();
    }
    translate([x_nosa, 0, 0]) rotate([90, 0, 90]) czop_przedni();
    for (j = [1 : 3]) rotate([fi[j - 1], 0, 0]) translate([x_pin(j - 1) + dl_ck / 2 + gr_ram - 4.6, 0, 0])
        rotate([90, 0, 90]) czop_glowny(fi[j] - fi[j - 1]);
    rotate([fi[3], 0, 0]) translate([x_pin(3) + dl_ck / 2 + gr_ram - 4.6, 0, 0]) rotate([90, 0, 90]) czop_tylny();
}

// =====================================================================
//  KORBOWÓD Z POKRYWĄ (łączone kołkami z filamentu 1,75 mm)
// =====================================================================
R_stopy = 9.2;
module otw_kolka(y0, dl) for (x = [-7.3, 7.3]) translate([x, y0, gr_korb / 2]) rotate([-90, 0, 0])
    linear_extrude(dl) rotate(180) lza2d(0.93);
module korbowod() {
    difference() {
        linear_extrude(gr_korb) difference() {
            union() {
                intersection() { circle(r = R_stopy); translate([-10, 0]) square([20, 10]); }
                intersection() {
                    hull() { circle(r = 5.5); translate([0, dl_korb]) circle(r = d_sw / 2 + 2.3); }
                    translate([-10, 0]) square([20, dl_korb + 10]);
                }
            }
            circle(d = d_ck + 2 * luz);
            translate([0, dl_korb]) circle(d = d_sw + 0.4);
        }
        otw_kolka(-0.01, 3.8);
    }
}
module pokrywa_korbowodu() {
    difference() {
        linear_extrude(gr_korb) difference() {
            intersection() { circle(r = R_stopy); translate([-10, -10]) square([20, 10]); }
            circle(d = d_ck + 2 * luz);
        }
        otw_kolka(-3.8, 3.81);
    }
}

// =====================================================================
//  TŁOK I SWORZEŃ
// =====================================================================
module tlok() {
    sc = 1.6;  denko = 3;
    difference() {
        union() {
            difference() {
                cylinder(d = d_tl, h = h_tl);
                translate([0, 0, denko]) cylinder(d = d_tl - 2 * sc, h = h_tl);
            }
            intersection() {
                cylinder(d = d_tl - 0.1, h = h_tl);
                for (m = [0, 1]) mirror([m, 0, 0])
                    translate([gr_korb / 2 + 1, -5.5, 0]) cube([d_tl, 11, sw_den + d_sw / 2 + 3]);
            }
        }
        translate([0, 0, sw_den]) rotate([0, 90, 0]) linear_extrude(d_tl + 2, center = true) rotate(90) lza2d(d_sw / 2 + 0.15);
        for (z = [2, 4, 6]) translate([0, 0, z]) difference() {
            cylinder(d = d_tl + 1, h = 0.8);
            translate([0, 0, -1]) cylinder(d = d_tl - 1, h = 3);
        }
    }
}
module sworzen() cylinder(d = d_sw, h = d_tl - 1);

// =====================================================================
//  WAŁEK ROZRZĄDU (dwie połówki klejone wzdłuż osi)
// =====================================================================
x_cam0 = x_loz(0) - 3.5 - 12;   // -32.5
x_cam1 = x_loz(4) + 3.5;        // 122.5
module krzywka2d(n0) rotate(n0) hull() { circle(r = r_baz); translate([e_nos, 0]) circle(r = r_nos); }
module walek_rozrzadu() {
    px(x_cam0, 12.01) d2d(4, 3.2);
    px(x_loz(0) - 3.5, x_loz(4) - x_loz(0) + 7) circle(r = 4.5);
    for (j = [0 : 4]) px(x_loz(j) - 3, 6) circle(d = d_jr);
    for (b = [0, 1], c = [0 : 3], v = [0, 1])
        px(x_zaw(b, c, v) - szer_kr / 2, szer_kr) krzywka2d(nos0(b, c, v));
}
module otw_rozrzad() for (j = [0, 2, 4], y = [-6, 6]) translate([x_loz(j), y, -4]) cylinder(d = 1.9, h = 8);
module walek_polowa(gora) {
    difference() {
        intersection() {
            if (gora) walek_rozrzadu(); else rotate([180, 0, 0]) walek_rozrzadu();
            translate([x_cam0 - 1, -20, 0]) cube([x_cam1 - x_cam0 + 2, 40, 20]);
        }
        otw_rozrzad();
    }
}

// =====================================================================
//  KOŁA ROZRZĄDU (m = 1,5; 16 i 32 zęby; rozstaw = z_cam)
// =====================================================================
function inv(a) = tan(a) - a * PI / 180;
module kolo_zebate2d(z, m, faza) {
    rp = m * z / 2;  rb = rp * cos(20);  ra = rp + m;  rf = rp - 1.25 * m;
    r0 = max(rb, rf);
    hp = 90 / z - (0.1 / rp) * 180 / PI;
    pts = [for (i = [0 : 10]) let(r = r0 + (ra - r0) * i / 10, a = acos(rb / r))
           [r, hp + (inv(20) - inv(a)) * 180 / PI]];
    circle(r = rf);
    for (k = [0 : z - 1]) rotate(faza + k * 360 / z)
        polygon(concat([[0, 0]],
            [for (p = pts) [p[0] * cos(-p[1]), p[0] * sin(-p[1])]],
            [for (i = [len(pts) - 1 : -1 : 0]) [pts[i][0] * cos(pts[i][1]), pts[i][0] * sin(pts[i][1])]]));
}
module kolo_rozrzadu_walu() {   // 16 z, na wale korbowym
    difference() {
        union() { linear_extrude(6) kolo_zebate2d(16, 1.5, 90); cylinder(r = 7.5, h = 6); }
        translate([0, 0, -1]) linear_extrude(8) offset(delta = 0.15) d2d(5, 4);
        rotate(90) translate([7.6, 0, 5]) cylinder(d = 1.6, h = 2);     // znacznik
    }
}
module kolo_rozrzadu_walka() {  // 32 z, na wałku rozrządu
    difference() {
        linear_extrude(6) kolo_zebate2d(32, 1.5, 270 + 180 / 32);
        translate([0, 0, -1]) linear_extrude(8) offset(delta = 0.15) d2d(4, 3.2);
        for (a = [45 : 90 : 359]) rotate(a) translate([13, 0, -1]) cylinder(d = 9, h = 8);
        rotate(270) translate([20, 0, 5]) cylinder(d = 1.6, h = 2);     // znacznik
    }
}

// =====================================================================
//  POPYCHACZ, DRĄŻEK, DŹWIGIENKA, ZAWÓR
// =====================================================================
module popychacz() difference() {
    cylinder(d = d_pop, h = dl_pop);
    translate([0, 0, dl_pop]) sphere(r = r_gn);
}
module drazek_z() intersection() {      // wzdłuż Z, spłaszczony w X
    union() {
        cylinder(d = d_drz, h = L_drz);
        sphere(r = r_kul);
        translate([0, 0, L_drz]) sphere(r = r_kul);
    }
    cube([2.4, 10, 3 * L_drz], center = true);
}
module dzw2d() {
    ang = atan2(-dvec[1], -dvec[0]);
    difference() {
        union() {
            hull() { translate(piv) circle(r = 4); translate(pad_c) circle(r = r_pad); }
            hull() { translate(piv) circle(r = 4); translate(cup) circle(r = 3.4); }
        }
        translate(piv) circle(d = 4.4);
        translate(cup) circle(r = r_gn);
        translate(cup) hull() for (k = [-16, 4]) rotate(ang + k) translate([0, -1.45]) square([9, 2.9]);
    }
}
module dzwigienka_3d() translate([-3.8, 0, 0]) rotate([90, 0, 90]) linear_extrude(7.6) dzw2d();
module zawor_3d() {
    translate([0, 0, a_deck]) cylinder(d = d_zaw, h = gr_zaw);
    translate([0, 0, a_deck + gr_zaw - 0.01]) cylinder(d = d_trz, h = a_tip - a_deck - gr_zaw + 0.01);
}
module talerzyk() difference() { cylinder(d = 6, h = 1.5); translate([0, 0, -1]) cylinder(d = 2.9, h = 4); }
module sprezyna() difference() { cylinder(d = 6.4, h = 10); translate([0, 0, -1]) cylinder(d = 3.6, h = 12); }
module os_dzwigienek() intersection() {
    rotate([0, 90, 0]) cylinder(d = 4, h = 130);
    translate([-1, -3, -1.6]) cube([132, 6, 4]);
}

// =====================================================================
//  BLOK SILNIKA
// =====================================================================
module pas_banku(b, a0, a1, w0, w1, x0 = x_bl0, x1 = x_bl1)
    bank(b) translate([x0, w0, a0]) cube([x1 - x0, w1 - w0, a1 - a0]);

module blok() {
    difference() {
        hull() {
            for (b = [0, 1]) pas_banku(b, a_tul, a_deck, -w_bl, w_bl);
            translate([x_bl0, -30, 0]) cube([x_bl1 - x_bl0, 60, 0.01]);
        }
        // „V” – dolina nad wałkiem rozrządu
        px(x_bl0 - 1, x_bl1 - x_bl0 + 2)
            polygon([[-(z_doliny - w_bl / s2), z_doliny], [z_doliny - w_bl / s2, z_doliny],
                     [200 - w_bl / s2, 200], [-(200 - w_bl / s2), 200]]);
        // komory korbowe
        for (c = [0 : 3]) px(x_pin(c) - 13, 26) lza2d(r_kom);
        // gniazda łożysk głównych
        px(x_bl0 - 1, x_bl1 - x_bl0 + 2) lza2d(d_cg / 2 + luz);
        // cylindry
        for (b = [0, 1], c = [0 : 3]) bank(b) {
            translate([x_cyl(b, c), 0, a_tul]) cylinder(d = srednica, h = a_deck - a_tul + 1);
            translate([x_cyl(b, c), 0, a_tul - 0.01]) cylinder(d1 = srednica + 2, d2 = srednica, h = 1);
            intersection() {
                translate([x_cyl(b, c), 0, -5]) cylinder(r = 14, h = a_tul + 5.1);
                translate([x_pin(c) - 13, -20, -10]) cube([26, 40, 50]);
            }
        }
        // tunel wałka rozrządu i prowadnice popychaczy
        translate([0, 0, z_cam]) px(x_bl0 - 1, x_bl1 - x_bl0 + 2) lza2d(r_tun, r_tun * 1.15);
        for (b = [0, 1], c = [0 : 3], v = [0, 1]) bank(b)
            translate([x_zaw(b, c, v), cam_c[0], cam_c[1]]) rotate([delta, 0, 0])
                translate([0, 0, 8]) cylinder(d = d_pop + 0.4, h = 30);
        // okienka przekroju w lewym rzędzie
        if (przekroj) for (c = [0 : 3]) bank(0) translate([x_cyl(0, c) - 7, -w_bl - 1, 36]) cube([14, w_bl + 1, 28]);
        // otwory kołków: głowice, pokrywy łożysk, miska
        for (b = [0, 1], k = [0 : 2]) bank(b) translate([x_cyl(b, k) + 17, 0, a_deck - 5]) cylinder(d = 4.2, h = 6);
        for (j = [0 : 4], y = [-12, 12]) translate([x_loz(j), y, -1]) cylinder(d = 4.2, h = 6);
        for (x = [x_loz(0), x_loz(4)], y = [-26, 26]) translate([x, y, -1]) cylinder(d = 4.2, h = 6);
    }
}

module pokrywa_lozyska() {   // w położeniu pracy: od z=-10 do 0
    difference() {
        translate([-4, -16, -10]) cube([8, 32, 10]);
        rotate([0, 90, 0]) cylinder(r = d_cg / 2 + luz, h = 10, center = true);
        for (y = [-12, 12]) translate([0, y, -5]) cylinder(d = 4.2, h = 6);
    }
}

module miska() {
    difference() {
        union() {
            difference() {
                translate([x_bl0 - 2.5, -30, -30]) cube([x_bl1 - x_bl0 + 5, 60, 30]);
                translate([x_bl0, -27.5, -27]) cube([x_bl1 - x_bl0, 55, 28]);
            }
            for (j = [0 : 4]) translate([x_loz(j) - 3, -14, -27.5]) cube([6, 28, 17.5]);
            for (x = [x_loz(0), x_loz(4)], y = [-26, 26]) translate([x - 4, y - 4, -27.5]) cube([8, 8, 27.5]);
        }
        for (x = [x_bl0 - 3, x_bl1 - 1]) translate([x, 0, 0]) rotate([0, 90, 0]) cylinder(r = 7, h = 4);
        for (x = [x_loz(0), x_loz(4)], y = [-26, 26]) translate([x, y, -5]) cylinder(d = 4.2, h = 6);
    }
}

// =====================================================================
//  GŁOWICA (współrzędne lewego rzędu; prawa = ta sama część)
// =====================================================================
hx0 = x_cyl(0, 0) - 17;  hx1 = x_cyl(0, 3) + 17;
module slupki_dzw() {
    for (c = [0 : 3]) {
        translate([x_cyl(0, c) - 2.5, 0, 0]) slupek(5);
        if (c < 3) translate([x_cyl(0, c) + 10.5, 0, 0]) slupek(13);
    }
    translate([x_cyl(0, 0) - 14.5, 0, 0]) slupek(4);
    translate([x_cyl(0, 3) + 10.5, 0, 0]) slupek(4);
}
module slupek(sz) rotate([90, 0, 90]) linear_extrude(sz) hull() {
    translate([piv[0] - 4, a_gl1 - 0.01]) square([8, 1]);
    translate(piv) circle(r = 4);
}
module glowica() {
    difference() {
        union() {
            translate([hx0, w_gl0, a_deck]) cube([hx1 - hx0, w_gl1 - w_gl0, a_gl1 - a_deck]);
            slupki_dzw();
            // świece zapłonowe (ozdobne)
            for (c = [0 : 3]) translate([x_cyl(0, c), w_gl0 + 0.01, 76.5]) rotate([90, 0, 0]) {
                linear_extrude(3) lza2d(3);
                translate([0, 0, 3]) linear_extrude(3) intersection() { circle(r = 3.4, $fn = 6); lza2d(3.2); }
                translate([0, 0, 6]) linear_extrude(6) lza2d(1.7);
            }
        }
        for (c = [0 : 3], v = [0, 1]) translate([x_zaw(0, c, v), 0, 0]) {
            translate([0, 0, a_deck - 1]) cylinder(d = d_zaw + 0.4, h = gr_zaw + 1);
            translate([0, 0, a_deck - 1]) cylinder(d = d_trz + 0.3, h = 30);
            translate([0, 0, a_kiesz]) cylinder(d = 7, h = 20);
            translate([0, cup[0], cup[1]]) rotate([delta, 0, 0]) translate([0, 0, -40]) cylinder(d = 4.6, h = 60);
            // kanały: wydech na zewnątrz, dolot od strony „V”
            if (typ[c][v] == 0) translate([-3, w_gl0 - 1, 82]) cube([6, 4, 5]);
            else translate([-3, w_gl1 - 3, 78]) cube([6, 4, 6]);
        }
        // oś dźwigienek
        translate([hx0 - 1, piv[0], piv[1]]) rotate([90, 0, 90]) linear_extrude(hx1 - hx0 + 2) lza2d(2.15);
        // kołki: blok, pokrywa zaworów, kolektor wydechowy
        for (k = [0 : 2]) translate([x_cyl(0, k) + 17, 0, a_deck - 1]) cylinder(d = 4.2, h = 6);
        for (x = [hx0 + 5.5, hx1 - 5.5]) translate([x, -11.5, a_gl1 - 5]) cylinder(d = 4.2, h = 6);
        for (k = [0, 2]) translate([x_cyl(0, k) + 17, w_gl0 - 1, 84.5]) rotate([-90, 0, 0]) cylinder(d = 4.2, h = 6);
    }
}

module pokrywa_zaworow() {   // współrzędne lewego rzędu; od a=88 do 108
    difference() {
        union() {
            difference() {
                hull() for (x = [hx0 + 3, hx1 - 3], w = [w_gl0 + 3, w_gl1 - 3]) {
                    translate([x, w, a_gl1]) cylinder(r = 3, h = 18);
                    translate([x, w, a_gl1]) cylinder(r = 1, h = 20);
                }
                hull() for (x = [hx0 + 3, hx1 - 3], w = [w_gl0 + 3, w_gl1 - 3]) {
                    translate([x, w, a_gl1 - 1]) cylinder(r = 1, h = 19);
                }
            }
            for (x = [hx0 + 2, hx1 - 9]) translate([x, w_gl0 + 2, a_gl1]) cube([7, 7, 18]);
        }
        // korek wlewu oleju, odpowietrznik i użebrowanie (grawer na płaskiej górze)
        for (x = [hx0 + 22, hx1 - 22]) translate([x, 1, a_gl1 + 19.4]) difference() {
            cylinder(d = 12, h = 2); translate([0, 0, -1]) cylinder(d = 10, h = 4);
        }
        for (w = [-8, 2, 12]) translate([hx0 + 32, w, a_gl1 + 19.4]) cube([hx1 - hx0 - 64, 1.2, 2]);
        for (x = [hx0 + 5.5, hx1 - 5.5]) translate([x, -11.5, a_gl1 - 1]) cylinder(d = 4.2, h = 6);
    }
}

module kolektor_wydechowy() {   // współrzędne lewego rzędu
    ex = [for (c = [0 : 3], v = [0, 1]) if (typ[c][v] == 0) x_zaw(0, c, v)];
    xw = x_cyl(0, 1) + 17;
    difference() {
        union() {
            translate([hx0 + 4, w_gl0 - 2.5, 81]) cube([hx1 - hx0 - 8, 2.5, 7]);
            hull() {
                translate([ex[0], -26, 84.5]) rotate([0, 90, 0]) cylinder(r = 4.5, h = ex[3] - ex[0]);
                translate([ex[0], w_gl0 - 0.5, 82]) cube([ex[3] - ex[0], 0.5, 5]);
            }
            for (x = ex) hull() {
                translate([x - 3.5, w_gl0 - 2.5, 81.5]) cube([7, 2.5, 6]);
                translate([x, -26, 84.5]) sphere(r = 4.5);
            }
            hull() {
                translate([xw, -26, 84.5]) sphere(r = 4.5);
                translate([xw, -26, 66]) cylinder(r = 4, h = 1);
                translate([xw - 3, w_gl0 - 0.5, 66]) cube([6, 0.5, 18]);
            }
        }
        translate([xw, -26, 65]) cylinder(r = 2.5, h = 10);
        for (k = [0, 2]) translate([x_cyl(0, k) + 17, w_gl0 + 1, 84.5]) rotate([90, 0, 0]) cylinder(d = 4.2, h = 6);
    }
}

// =====================================================================
//  OSPRZĘT (ozdobny): kolektor dolotowy, gaźnik, filtr, aparat zapłonowy
// =====================================================================
kx0 = -12;  kx1 = 114;  kz0 = 60;  kz1 = 92;  x_gaz = 51;  x_apar = 106;
module pas2d(ang, a0, a1) rotate(ang) translate([a0, -150]) square([a1 - a0, 300]);
module kolektor2d() intersection() {
    pas2d(45, w_gl1, a_gl1 - 0.4);
    pas2d(135, w_gl1, a_gl1 - 0.4);
    translate([-100, kz0]) square([200, kz1 - kz0]);
}
module kolektor_ssacy() {
    difference() {
        union() {
            px(kx0, kx1 - kx0) kolektor2d();
            // kanały dolotowe
            for (b = [0, 1], c = [0 : 3], v = [0, 1]) if (typ[c][v] == 1)
                intersection() {
                    px(x_zaw(b, c, v) - 3.5, 7) offset(delta = 1.2) kolektor2d();
                    px(kx0, kx1 - kx0) intersection() {
                        pas2d(45, w_gl1, 200); pas2d(135, w_gl1, 200);
                        translate([b == 0 ? -100 : 3, 70]) square([97, kz1 - 70]);
                    }
                }
        }
        translate([kx0 + 2.5, 0, 0]) px(0, kx1 - kx0 - 5) union() {
            offset(delta = -2.5) kolektor2d();
            translate([0, -4]) offset(delta = -2.5) kolektor2d();
        }
        translate([x_apar, 0, 80]) cylinder(d = 12.4, h = 20);
        for (x = [-1, 1], y = [-1, 1]) translate([x_gaz + 6 * x, 5 * y, kz1 - 5]) cylinder(d = 7, h = 10);
        translate([x_gaz, 0, kz1 - 5]) cylinder(d = 4.2, h = 10);
    }
}
module gaznik() {   // od z = kz1 + 2
    difference() {
        union() {
            translate([-15, -13, 0]) cube([30, 26, 12]);
            translate([-15, -16, 0]) cube([4, 32, 7]);
            translate([11, -16, 0]) cube([4, 32, 7]);
        }
        for (x = [-1, 1], y = [-1, 1]) translate([6 * x, 5 * y, 2]) cylinder(d = 7.5, h = 11);
        translate([0, 0, -1]) cylinder(d = 4.2, h = 20);
    }
}
module filtr_powietrza() {
    difference() {
        union() {
            cylinder(r = 34, h = 3);
            translate([0, 0, 3]) cylinder(r1 = 34, r2 = 32, h = 8);
            translate([0, 0, 11]) cylinder(r1 = 32, r2 = 12, h = 3);
            translate([0, 0, 14]) cylinder(d = 8, h = 3);
            translate([0, 0, 15.5]) cube([16, 3, 3], center = true);
        }
        translate([0, 0, -1]) cylinder(d = 4.2, h = 6);
        translate([0, 0, 13.4]) rotate(90) linear_extrude(1) text("V8", size = 8, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
        for (a = [0 : 15 : 359]) rotate(a) translate([33.6, -0.6, 4]) cube([2, 1.2, 6]);
    }
}
module aparat_zaplonowy() {   // od z = 80
    cylinder(d = 12, h = 12);
    translate([0, 0, 12]) cylinder(d1 = 12, d2 = 18, h = 3);
    translate([0, 0, 15]) cylinder(d = 18, h = 6);
    translate([0, 0, 21]) cylinder(d1 = 18, d2 = 15, h = 7);
    for (a = [0 : 45 : 359]) rotate(a) translate([6, 0, 27]) cylinder(d = 3, h = 4);
    translate([0, 0, 27]) cylinder(d = 4, h = 4);
}

// =====================================================================
//  KOŁO ZAMACHOWE Z KORBKĄ, KOŁO PASOWE, KOŁEK USTALAJĄCY
// =====================================================================
module kolo_zamachowe() {
    R = 26;
    difference() {
        union() {
            cylinder(r = R - 1.5, h = 3);
            difference() { cylinder(r = R - 1.5, h = 6); translate([0, 0, -1]) cylinder(r = R - 4.5, h = 8); }
            linear_extrude(6) for (a = [0 : 5 : 359]) rotate(a) translate([R - 2, 0]) polygon([[0, -0.9], [2, -0.35], [2, 0.35], [0, 0.9]]);
            cylinder(r = 9, h = 9);
            translate([R - 9, 0, 0]) cylinder(d = 7, h = 21);
            translate([R - 9, 0, 21]) cylinder(d1 = 7, d2 = 5, h = 1.5);
        }
        translate([0, 0, -1]) linear_extrude(12) offset(delta = 0.15) d2d(5, 4);
        for (a = [60 : 60 : 300]) rotate(a) translate([15, 0, -1]) cylinder(d = 7, h = 8);
    }
}
module kolo_pasowe() {
    difference() {
        union() {
            cylinder(r = 15, h = 8);
            translate([0, 0, 8]) cylinder(r = 7, h = 2);
        }
        for (z = [2.2, 5.2]) translate([0, 0, z]) rotate_extrude() translate([15, 0]) circle(r = 1.2, $fn = 4);
        translate([0, 0, -1]) linear_extrude(12) offset(delta = 0.15) d2d(5, 4);
        translate([0, 11, 7]) cylinder(d = 2, h = 2);
    }
}
module kolek() cylinder(d = 4, h = 9.4);

// =====================================================================
//  ZŁOŻENIE
// =====================================================================
// macierze przekształceń (te same dla podglądu i dla testu kolizji)
function Tm(v) = [[1, 0, 0, v[0]], [0, 1, 0, v[1]], [0, 0, 1, v[2]], [0, 0, 0, 1]];
function Rx(a) = [[1, 0, 0, 0], [0, cos(a), -sin(a), 0], [0, sin(a), cos(a), 0], [0, 0, 0, 1]];
function Ry(a) = [[cos(a), 0, sin(a), 0], [0, 1, 0, 0], [-sin(a), 0, cos(a), 0], [0, 0, 0, 1]];
function Rz(a) = [[cos(a), -sin(a), 0, 0], [sin(a), cos(a), 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]];
function Sz(k)  = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, k, 0], [0, 0, 0, 1]];
R9090 = Rz(90) * Rx(90);
function MB(b) = [[1, 0, 0, 0], [0, wv(b)[1], u(b)[1], 0], [0, wv(b)[2], u(b)[2], 0], [0, 0, 0, 1]];
function MG(b) = MB(b) * Tm([b == 0 ? 0 : 2 * przes, 0, 0]);

// [nazwa, część, kolor, macierz]
function poz_stale() = concat(
    [["blok", "L_blok", "SlateGray", Tm([0, 0, 0])],
     ["miska", "L_miska", "DimGray", Tm([0, 0, 0])]],
    [for (j = [0 : 4]) [str("pokrywa_lozyska", j), "L_pokrywa_lozyska", "DimGray", Tm([x_loz(j), 0, 0])]],
    [for (b = [0, 1]) [str("glowica", b), "L_glowica", "Gray", MG(b)]],
    [for (b = [0, 1]) [str("os_dzwigienek", b), "L_os_dzwigienek", "Gray", MG(b) * Tm([hx0 + 3, piv[0], piv[1]])]],
    pokaz_osprzet ? concat(
        [for (b = [0, 1]) [str("kolektor_wydechowy", b), "L_kolektor_wydechowy", "Sienna", MG(b)]],
        [["kolektor_ssacy", "L_kolektor_ssacy", "Silver", Tm([0, 0, 0])],
         ["gaznik", "L_gaznik", "DimGray", Tm([x_gaz, 0, kz1])],
         ["filtr_powietrza", "L_filtr_powietrza", "Black", Tm([x_gaz, 0, kz1 + 12])],
         ["aparat_zaplonowy", "L_aparat_zaplonowy", "Black", Tm([x_apar, 0, 80])]]) : [],
    pokaz_pokrywy ? [for (b = [0, 1]) [str("pokrywa_zaworow", b), "L_pokrywa_zaworow", "Crimson", MG(b)]] : []
);

function poz_zaworu(b, c, v, t) =
    let(x  = x_zaw(b, c, v),
        h  = wznios(b, c, v, t),
        B  = cam_c + (r_baz + dl_pop + h) * dvec,
        g  = newton(h * 180 / PI / 9.3, B, 4),
        pc = piv + rot2(pad_c - piv, g),
        hz = a_tip - (pc[1] - r_pad),
        C  = cupg(g),
        n  = str(b, c, v))
    [[str("popychacz", n), "L_popychacz", "LightSlateGray",
         MB(b) * Tm([x, cam_c[0] + (r_baz + h) * dvec[0], cam_c[1] + (r_baz + h) * dvec[1]]) * Rx(delta)],
     [str("drazek", n), "L_drazek", "Orange", MB(b) * Tm([x, B[0], B[1]]) * Rx(atan2(-(C - B)[0], (C - B)[1]))],
     [str("dzwigienka", n), "L_dzwigienka", "OrangeRed", MB(b) * Tm([x, piv[0], piv[1]]) * Rx(g) * Tm([0, -piv[0], -piv[1]])],
     [str("zawor", n), "L_zawor", "WhiteSmoke", MB(b) * Tm([x, 0, -hz])],
     [str("talerzyk", n), "L_talerzyk", "DimGray", MB(b) * Tm([x, 0, a_tip - 4 - hz])],
     [str("sprezyna", n), "L_sprezyna", "Black", MB(b) * Tm([x, 0, a_kiesz]) * Sz((a_tip - 4 - hz - a_kiesz) / 10)]];

function poz_ruchome(t) = concat(
    [["wal", "L_wal", "Goldenrod", Rx(t)],
     ["kolo_rozrzadu_walu", "L_kolo_rozrzadu_walu", "Goldenrod", Rx(t) * Tm([-31, 0, 0]) * R9090],
     ["kolo_pasowe", "L_kolo_pasowe", "Chocolate", Rx(t) * Tm([-43, 0, 0]) * R9090],
     ["kolo_zamachowe", "L_kolo_zamachowe", "DarkRed", Rx(t + fi[3]) * Tm([x_loz(4) + dl_cg / 2 + 1.5, 0, 0]) * R9090],
     ["walek_rozrzadu", "L_walek_rozrzadu", "SteelBlue", Tm([0, 0, z_cam]) * Rx(-t / 2)],
     ["kolo_rozrzadu_walka", "L_kolo_rozrzadu_walka", "SteelBlue", Tm([-31, 0, z_cam]) * Rx(-t / 2) * R9090]],
    [for (b = [0, 1], c = [0 : 3]) let(q = pin_bank(b, c, t))
        [str("korbowod", b, c), "L_korbowod", "Silver",
         MB(b) * Tm([x_cyl(b, c), q[0], q[1]]) * R9090 * Rz(asin(q[0] / dl_korb)) * Tm([0, 0, -gr_korb / 2])]],
    [for (b = [0, 1], c = [0 : 3])
        [str("tlok", b, c), "L_tlok", "Gainsboro", MB(b) * Tm([x_cyl(b, c), 0, a_sw(b, c, t)]) * Rx(180) * Tm([0, 0, -sw_den])]],
    [for (b = [0, 1], c = [0 : 3])
        [str("sworzen", b, c), "L_sworzen", "DimGray", MB(b) * Tm([x_cyl(b, c) - (d_tl - 1) / 2, 0, a_sw(b, c, t)]) * Ry(90)]],
    [for (b = [0, 1], c = [0 : 3], v = [0, 1]) each poz_zaworu(b, c, v, t)]
);

module czesc_lok(id) {
    if      (id == "L_blok")               blok();
    else if (id == "L_miska")              miska();
    else if (id == "L_pokrywa_lozyska")    pokrywa_lozyska();
    else if (id == "L_glowica")            glowica();
    else if (id == "L_os_dzwigienek")      os_dzwigienek();
    else if (id == "L_kolektor_wydechowy") kolektor_wydechowy();
    else if (id == "L_kolektor_ssacy")     kolektor_ssacy();
    else if (id == "L_gaznik")             gaznik();
    else if (id == "L_filtr_powietrza")    filtr_powietrza();
    else if (id == "L_aparat_zaplonowy")   aparat_zaplonowy();
    else if (id == "L_pokrywa_zaworow")    pokrywa_zaworow();
    else if (id == "L_wal")                wal_zlozony();
    else if (id == "L_kolo_rozrzadu_walu") kolo_rozrzadu_walu();
    else if (id == "L_kolo_pasowe")        kolo_pasowe();
    else if (id == "L_kolo_zamachowe")     kolo_zamachowe();
    else if (id == "L_walek_rozrzadu")     walek_rozrzadu();
    else if (id == "L_kolo_rozrzadu_walka") kolo_rozrzadu_walka();
    else if (id == "L_korbowod")           { korbowod(); pokrywa_korbowodu(); }
    else if (id == "L_tlok")               tlok();
    else if (id == "L_sworzen")            sworzen();
    else if (id == "L_popychacz")          popychacz();
    else if (id == "L_drazek")             drazek_z();
    else if (id == "L_dzwigienka")         dzwigienka_3d();
    else if (id == "L_zawor")              zawor_3d();
    else if (id == "L_talerzyk")           talerzyk();
    else if (id == "L_sprezyna")           sprezyna();
}

module zlozenie(t = kat) {
    for (p = concat(poz_stale(), poz_ruchome(t)))
        color(p[2], (p[1] == "L_blok" && przekroj) ? 0.75 : 1) multmatrix(p[3]) render() czesc_lok(p[1]);
}

// =====================================================================
//  CZĘŚCI DO DRUKU
// =====================================================================
if (czesc == "zlozenie") zlozenie();
else if (czesc == "pozycje") for (p = concat(poz_stale(), poz_ruchome(kat))) echo(str("POZ|", p[0], "|", p[1], "|", p[3]));
else if (len(search("L_", czesc)) > 0 && search("L_", czesc)[0] == 0) czesc_lok(czesc);
else if (czesc == "blok")                 blok();
else if (czesc == "pokrywa_lozyska")      translate([0, 0, 10]) pokrywa_lozyska();
else if (czesc == "miska")                translate([0, 0, 30]) miska();
else if (czesc == "ramie_walu")           ramie();
else if (czesc == "czop_korbowy")         czop_korbowy();
else if (czesc == "czop_glowny_1")        czop_przedni();
else if (czesc == "czop_glowny_2")        czop_glowny(fi[1] - fi[0]);
else if (czesc == "czop_glowny_3")        czop_glowny(fi[2] - fi[1]);
else if (czesc == "czop_glowny_4")        czop_glowny(fi[3] - fi[2]);
else if (czesc == "czop_glowny_5")        czop_tylny();
else if (czesc == "korbowod")             korbowod();
else if (czesc == "pokrywa_korbowodu")    translate([0, 0, 0]) rotate([0, 0, 180]) pokrywa_korbowodu();
else if (czesc == "tlok")                 tlok();
else if (czesc == "sworzen")              sworzen();
else if (czesc == "walek_rozrzadu_gora")  walek_polowa(true);
else if (czesc == "walek_rozrzadu_dol")   walek_polowa(false);
else if (czesc == "kolo_rozrzadu_walu")   kolo_rozrzadu_walu();
else if (czesc == "kolo_rozrzadu_walka")  kolo_rozrzadu_walka();
else if (czesc == "popychacz")            popychacz();
else if (czesc == "drazek")               translate([0, 0, 1.2]) rotate([0, 90, 0]) drazek_z();
else if (czesc == "dzwigienka")           linear_extrude(7.6) translate(-piv) dzw2d();
else if (czesc == "os_dzwigienek")        translate([0, 0, 1.6]) os_dzwigienek();
else if (czesc == "zawor")                translate([0, 0, -a_deck]) zawor_3d();
else if (czesc == "talerzyk")             talerzyk();
else if (czesc == "sprezyna_tpu")         sprezyna();
else if (czesc == "glowica")              translate([0, 0, -a_deck]) glowica();
else if (czesc == "pokrywa_zaworow")      translate([0, 0, a_gl1 + 20]) mirror([0, 0, 1]) pokrywa_zaworow();
else if (czesc == "kolektor_wydechowy")   translate([0, 0, 0]) rotate([-90, 0, 0]) translate([0, -w_gl0, 0]) kolektor_wydechowy();
else if (czesc == "kolektor_ssacy")       translate([0, 0, kz1]) mirror([0, 0, 1]) kolektor_ssacy();
else if (czesc == "gaznik")               gaznik();
else if (czesc == "filtr_powietrza")      filtr_powietrza();
else if (czesc == "aparat_zaplonowy")     aparat_zaplonowy();
else if (czesc == "kolo_zamachowe")       kolo_zamachowe();
else if (czesc == "kolo_pasowe")          kolo_pasowe();
else if (czesc == "kolek")                kolek();
