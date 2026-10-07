// Zegar z kukułką w stylu zakopiańskim — model parametryczny (OpenSCAD)
//
// Domek z bali, stromy dach z gontu, śparogi na szczycie, słoneczko
// (rozeta) nad drzwiczkami. Godzinę pokazuje zwykły mechanizm kwarcowy,
// a kukułkę wysuwa serwo SG90 sterowane przez ESP32 (patrz ../kukulka_esp32).
//
// Wszystkie części drukują się płasko, ozdobną stroną do góry, bez podpór.
// Eksport jednej części:
//   openscad -D 'czesc="sciana_przednia"' -o sciana_przednia.stl kukulka.scad
//
// Układ współrzędnych złożenia: X w prawo, Y w głąb (front na Y=0,
// ściana pokoju za Y=D), Z w górę.

/* [Wybór części] */
czesc = "zlozenie"; // [zlozenie, przekroj, podloga, sciana_przednia, sciana_boczna, sciana_tylna, strop, szczyt_przedni, szczyt_tylny, dach, kalenica, sparogi, tarcza, wskazowki, drzwiczki, kukulka, ramie, uchwyt_serwa, kostka, szyszka, test_otworow]

/* [Bryła] */
W = 170;            // szerokość domku
D = 100;            // głębokość domku
Hs = 180;           // wysokość od spodu podłogi do górnej krawędzi ścian
spad = 55;          // kąt nachylenia dachu (styl zakopiański: stromy)
t = 4;              // grubość ścian i szczytów (bez płaskorzeźby)
tf = 4;             // grubość podłogi
ts = 3;             // grubość stropu
bal = 2;            // wypukłość bali
bal_h = 14;         // przybliżona wysokość jednego bala
okap = 16;          // wysunięcie dachu poza ściany boczne
nawis = 15;         // wysunięcie dachu z przodu i z tyłu
tr = 3;             // grubość połaci dachu (bez gontu)

/* [Tarcza i wskazówki] */
tarcza_d = 120;
tarcza_g = 2.5;        // gwint mechanizmu musi to objąć
otwor_walka = 8.2;
otwor_mech = 82;       // otwór w ścianie na korpus mechanizmu 56×56
grubosc_wsk = 1.2;
otwor_godz = 5.2;
otwor_min_d = 3.3;
otwor_min_plaska = 2.4;
font = "Liberation Serif:style=Bold";

/* [Kukułka i serwo SG90] */
drzwi_szer = 34;       // otwór drzwiczek w szczycie
drzwi_wys = 45;
ramie_L = 58;          // od osi serwa do środka ptaka
serwo_Y = 24;          // położenie osi serwa (w głąb)
serwo_pod_stropem = 26;
kat_ptaka = 18;        // ptak przechylony do tyłu względem ramienia
// SG90 (sprawdź suwmiarką — wymiary różnią się między producentami)
sg_dl = 22.5;          // długość korpusu
sg_szer = 12.2;        // szerokość korpusu
sg_rozstaw = 27.8;     // rozstaw otworów w uszach
sg_wal = 5.9;          // oś wałka od krawędzi korpusu
sg_ucho_do_orczyka = 13; // od spodu uszu do zewnętrznej powierzchni orczyka

/* [Głośnik] */
glosnik_d = 40;

$fn = 64;

// ---------------------------------------------------------------------------
Hw = Hs - tf;                    // wysokość ścian
z0g = Hs + ts;                   // spód szczytów = wierzch stropu
Hg = W / 2 * tan(spad);          // wysokość szczytu
Lr = W / 2 / cos(spad) + okap;   // długość połaci (od kalenicy do okapu)
Ld = D + 2 * nawis;              // długość dachu wzdłuż kalenicy
v_tarczy = Hw - tarcza_d / 2 - 14;
Za = Hs - serwo_pod_stropem;     // wysokość osi serwa
v_zawiasu = drzwi_wys + 4;
os_zawiasu = 5;                  // oś zawiasu przed licem szczytu
h_tulei = 7 * cos(30) / 2;       // oś tulei drzwiczek nad stołem
y_glosnika = D / 2 + 10;

// kąty ramienia: do przodu dodatnie; środek ptaka ma wyjść do Y=-5, schować się do Y=25
kat_wysuniety = asin((serwo_Y + 5) / ramie_L);
kat_schowany = asin((serwo_Y - 25) / ramie_L);

echo(str("Wysokość całkowita ok. ", round(z0g + Hg + 30), " mm"));
echo(str("Wychylenie ramienia: ", round(kat_schowany), "° … ", round(kat_wysuniety), "° (różnica ",
         round(kat_wysuniety - kat_schowany), "°)"));

function kier(a) = [sin(a), cos(a)];

// ---------------------------------------------------------------------------
// Bale: wypukłe walce na płycie leżącej w XY, grubość t, ozdoby rosną w +Z.

module bale(dl, wys, x0 = 0) {
    n = max(1, round(wys / bal_h));
    lh = wys / n;
    c = lh / 2 - 0.6;
    r = (c * c + bal * bal) / (2 * bal);
    intersection() {
        for (i = [0:n - 1])
            translate([x0, (i + 0.5) * lh, t + bal - r]) rotate([0, 90, 0]) cylinder(r = r, h = dl, $fn = 120);
        translate([x0, 0, t]) cube([dl, wys, bal]);
    }
}

// ---------------------------------------------------------------------------
// Ściany (współrzędne druku: u = szerokość, v = wysokość, w = grubość)

module sciana_przednia() {
    difference() {
        union() {
            translate([-W / 2, 0, 0]) cube([W, Hw, t]);
            difference() {
                bale(W, Hw, -W / 2);
                translate([0, v_tarczy, 0]) cylinder(d = tarcza_d + 6, h = 20, $fn = 160);
            }
        }
        translate([0, v_tarczy, -1]) cylinder(d = otwor_mech, h = t + 2, $fn = 120);
    }
}

module sciana_boczna() {
    cube([D - 2 * t, Hw, t]);
    bale(D - 2 * t, Hw);
}

// zdejmowana — dostęp do baterii mechanizmu i elektroniki
module sciana_tylna() {
    difference() {
        translate([-W / 2, 0, 0]) cube([W, Hw, t]);
        for (s = [-1, 1], v = [5, Hw - 5]) translate([s * (W / 2 - t - 5), v, 0]) {
            translate([0, 0, -1]) cylinder(d = 3.4, h = t + 2);
            translate([0, 0, t - 1.8]) cylinder(d1 = 3.4, d2 = 7, h = 1.81);   // łeb stożkowy
        }
        translate([-8, -1, -1]) cube([16, 9, t + 2]);                          // przepust kabla USB
    }
}

// ---------------------------------------------------------------------------
// Podłoga i strop (drukowane tak, jak leżą)

module podloga() {
    difference() {
        union() {
            hull() {
                translate([-W / 2 - 4, -4, 0]) cube([W + 8, D + 4, tf - 1]);
                translate([-W / 2 - 3, -3, 0]) cube([W + 6, D + 3, tf]);
            }
            // listwa ustalająca ściany
            difference() {
                translate([-W / 2 + t, t, tf - 0.01]) cube([W - 2 * t, D - 2 * t, 1.5]);
                translate([-W / 2 + t + 1.2, t + 1.2, tf - 1]) cube([W - 2 * t - 2.4, D - 2 * t - 2.4, 4]);
            }
            // kostki pod wkręty ściany tylnej
            for (s = [-1, 1]) translate([s * (W / 2 - t - 5) - 5, D - t - 12, tf - 0.01]) cube([10, 12, 10]);
            // gniazdo głośnika
            translate([0, y_glosnika, tf - 0.01]) difference() {
                cylinder(d = glosnik_d + 4, h = 4, $fn = 96);
                translate([0, 0, -1]) cylinder(d = glosnik_d + 0.6, h = 6, $fn = 96);
            }
        }
        for (s = [-1, 1]) translate([s * (W / 2 - t - 5), D - t - 13, tf + 5]) rotate([-90, 0, 0]) cylinder(d = 2.5, h = 14);
        // kratka głośnika
        for (r = [0:4:glosnik_d / 2 - 5]) for (a = [0:360 / max(1, round(r * 1.4)):359.9])
            translate([r * sin(a), y_glosnika + r * cos(a), -1]) cylinder(d = 2.4, h = tf + 2, $fn = 16);
        // otwory na sznurki szyszek
        for (s = [-1, 1]) translate([s * 40, 30, -1]) cylinder(d = 4, h = tf + 2);
    }
}

module strop() {
    difference() {
        translate([-W / 2, -4, 0]) cube([W, D + 4, ts]);
        translate([-3, 0, -1]) cube([6, 32, ts + 2]);   // szczelina ramienia kukułki
    }
}

// kostka przyklejana pod stropem w tylnych narożnikach (2 szt.)
module kostka() {
    difference() {
        cube([10, 10, 12]);
        translate([5, 5, -1]) cylinder(d = 2.5, h = 14);
    }
}

// ---------------------------------------------------------------------------
// Szczyty

module trojkat_2d() { polygon([[-W / 2, 0], [W / 2, 0], [0, Hg]]); }

module otwor_drzwi_2d() {
    hull() {
        translate([-drzwi_szer / 2, -1]) square([drzwi_szer, 1]);
        translate([0, drzwi_wys - drzwi_szer / 2]) circle(d = drzwi_szer);
    }
}

// słoneczko — sześciopłatkowa rozeta
module rozeta(R = 20) {
    rp = R - 4;
    linear_extrude(0.6) circle(R, $fn = 120);
    translate([0, 0, 0.59]) linear_extrude(1) {
        difference() { circle(R - 0.4, $fn = 120); circle(R - 2.4, $fn = 120); }
        for (a = [0:60:300]) offset(delta = -0.6) intersection() {
            translate(rp * kier(a + 60)) circle(rp, $fn = 90);
            translate(rp * kier(a - 60)) circle(rp, $fn = 90);
        }
        for (a = [30:60:330]) translate((rp - 2) * kier(a)) circle(1.4, $fn = 24);
    }
}

module szczyt_przedni() {
    union() {
        difference() {
            linear_extrude(t) trojkat_2d();
            // pionowe deski szalunku
            translate([0, 0, t - 0.8]) linear_extrude(1) difference() {
                for (u = [-W / 2 + 11:11:W / 2]) translate([u - 0.4, -1]) square([0.8, Hg + 2]);
                offset(r = 3.5) otwor_drzwi_2d();
            }
            translate([0, 0, -1]) linear_extrude(t + 2) otwor_drzwi_2d();
        }
        // obramienie drzwiczek
        translate([0, 0, t - 0.01]) linear_extrude(1.2) difference() {
            offset(r = 3) otwor_drzwi_2d();
            offset(delta = 0.4) otwor_drzwi_2d();
            translate([-W / 2, -10]) square([W, 10]);
        }
        translate([0, Hg * 0.63, t - 0.01]) rozeta(20);
        // ucha zawiasu drzwiczek (oś = kawałek filamentu 1,75 mm)
        for (s = [-1, 1]) translate([s * 11.75, 0, 0]) difference() {
            hull() {
                translate([-2.75, v_zawiasu - 4, t - 0.01]) cube([5.5, 8, 1]);
                translate([-2.75, v_zawiasu, t + os_zawiasu]) rotate([0, 90, 0]) cylinder(r = 3.5, h = 5.5, $fn = 32);
            }
            translate([-4, v_zawiasu, t + os_zawiasu]) rotate([0, 90, 0]) cylinder(d = 1.95, h = 8, $fn = 16);
        }
    }
}

// drukowany zewnętrzną stroną do stołu; wieszak od środka
module szczyt_tylny() {
    vk = 50;
    difference() {
        union() {
            linear_extrude(t) trojkat_2d();
            translate([-12, vk - 10, t - 0.01]) cube([24, 30, 6]);
        }
        translate([0, vk, -1]) cylinder(d = 10, h = 20);
        hull() for (v = [vk, vk + 10]) translate([0, v, -1]) cylinder(d = 5, h = 20);
        hull() for (v = [vk, vk + 10]) translate([0, v, 2.5]) cylinder(d = 11, h = 20);
    }
}

// ---------------------------------------------------------------------------
// Dach: połać z gontem (współrzędne druku: x = od kalenicy w dół, y = wzdłuż kalenicy)

module dach() {
    rz = 12;            // wysokość rzędu gontów
    sz = 9;             // szerokość gonta
    gr = 1.6;           // pogrubienie dolnej krawędzi rzędu
    n = ceil(Lr / rz);
    translate([0, -nawis, 0]) {
        cube([Lr, Ld, tr]);
        difference() {
            for (k = [0:n - 1]) {
                x0 = k * rz;
                x1 = min(Lr, x0 + rz);
                translate([0, Ld, tr - 0.01]) rotate([90, 0, 0])
                    linear_extrude(Ld) polygon([[x0, 0], [x1, 0], [x1, gr * (x1 - x0) / rz]]);
            }
            for (k = [0:n - 1]) for (y = [((k % 2) * sz / 2):sz:Ld])
                translate([k * rz - 0.01, y - 0.4, tr + 0.2]) cube([rz + 0.02, 0.8, 3]);
        }
    }
}

// przykrycie kalenicy, drukowane na nóżkach (nawisy ok. 35° od pionu)
kal_zi = tr / cos(spad);   // wewnętrzny wierzchołek nad wierzchołkiem szczytu
kal_dz = 12;               // wysokość nóżek

module kalenica_2d() {
    zi = kal_zi;
    zo = zi + 2.5 / cos(spad);
    xi = kal_dz / tan(spad);
    xo = (zo - zi + kal_dz) / tan(spad);
    polygon([[0, zo], [xo, zi - kal_dz], [xi, zi - kal_dz], [0, zi], [-xi, zi - kal_dz], [-xo, zi - kal_dz]]);
}

module kalenica() {
    rotate([90, 0, 0]) translate([0, kal_dz - kal_zi, -Ld]) linear_extrude(Ld) kalenica_2d();
}

// śparogi: skrzyżowane deski nad szczytem i pazdur, przyklejane do czoła połaci
function P(s, n) = [s * cos(spad) + n * sin(spad), -s * sin(spad) + n * cos(spad)];

module deska_2d() {
    difference() {
        polygon([P(55, 0), P(51, 4.5), P(55, 9), P(-24, 9), P(-34, 4.5), P(-24, 0)]);
        translate(P(-24, 4.5)) circle(d = 3, $fn = 20);
    }
}

module sparogi_2d() {
    deska_2d();
    mirror([1, 0]) deska_2d();
    zc = 4.5 / cos(spad);
    polygon([[-3, zc], [3, zc], [1.5, zc + 22], [0, zc + 26], [-1.5, zc + 22]]);
    translate([0, zc + 14]) circle(d = 6, $fn = 6);
}

module sparogi() { linear_extrude(3) sparogi_2d(); }

// ---------------------------------------------------------------------------
// Tarcza z rzymskimi cyframi i wzorem „wilcze zęby”; drukowana licem do góry,
// zmiana koloru na wysokości tarcza_g.

rzymskie = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"];

module tarcza_wzor_2d() {
    R = tarcza_d / 2;
    difference() { circle(R - 0.4, $fn = 180); circle(R - 2.4, $fn = 180); }
    for (m = [0:59]) translate((R - 5) * kier(m * 6)) circle(d = m % 5 == 0 ? 2.8 : 1.4, $fn = 16);
    for (h = [0:11]) rotate(-h * 30) translate([0, R - 15])
        text(rzymskie[h], size = 8, font = font, halign = "center", valign = "center");
    difference() { circle(R - 26, $fn = 160); circle(R - 27.2, $fn = 160); }
    for (k = [0:35]) rotate(-k * 10) polygon([[-2.6, R - 27], [2.6, R - 27], [0, R - 22.5]]);
    difference() { circle(9); circle(7.5); }
}

module tarcza_baza() {
    difference() {
        cylinder(r = tarcza_d / 2, h = tarcza_g, $fn = 180);
        translate([0, 0, -1]) cylinder(d = otwor_walka, h = tarcza_g + 2, $fn = 48);
    }
}

module tarcza() {
    tarcza_baza();
    translate([0, 0, tarcza_g - 0.01]) linear_extrude(0.8) tarcza_wzor_2d();
}

// ---------------------------------------------------------------------------
// Wskazówki — ażurowe kółko w stylu zegarów szwarcwaldzkich/góralskich

module otwor_min_2d() {
    intersection() {
        circle(d = otwor_min_d, $fn = 40);
        square([otwor_min_plaska, otwor_min_d + 1], center = true);
    }
}

module wskazowka_2d(dl, w0, w1, piasta, oczko, ogon) {
    difference() {
        union() {
            hull() { circle(d = w0); translate([0, dl]) circle(d = w1); }
            hull() { circle(d = w0); translate([0, -ogon]) circle(d = w0 * 0.8); }
            circle(d = piasta);
            translate([0, dl * 0.72]) circle(d = oczko);
            translate([0, dl]) rotate(45) square(w1 * 1.6, center = true);
        }
        translate([0, dl * 0.72]) circle(d = oczko - 3);
    }
}

module wskazowka_godzinowa() {
    linear_extrude(grubosc_wsk) difference() {
        wskazowka_2d(tarcza_d / 2 - 24, 4, 2, 12, 10, 10);
        circle(d = otwor_godz, $fn = 40);
    }
}

module wskazowka_minutowa() {
    linear_extrude(grubosc_wsk) difference() {
        wskazowka_2d(tarcza_d / 2 - 7, 3.4, 1.6, 10, 8, 12);
        otwor_min_2d();
    }
}

module wskazowki() {
    wskazowka_minutowa();
    translate([16, 0, 0]) wskazowka_godzinowa();
}

module test_otworow() {
    linear_extrude(grubosc_wsk) difference() { circle(d = 12); otwor_min_2d(); }
    translate([16, 0, 0]) linear_extrude(grubosc_wsk) difference() { circle(d = 14); circle(d = otwor_godz, $fn = 40); }
    translate([36, 0, 0]) linear_extrude(tarcza_g) difference() { circle(d = 20); circle(d = otwor_walka, $fn = 48); }
    // ucho zawiasu + otwór na filament 1,75
    translate([56, 0, 0]) difference() {
        cylinder(d = 8, h = 4);
        translate([0, 0, -1]) cylinder(d = 1.95, h = 6, $fn = 16);
    }
}

// ---------------------------------------------------------------------------
// Drzwiczki — zawieszone u góry, ptak je wypycha, opadają same.
// Drukowane płasko, frontem do góry (x = szerokość, y = od dołu do osi zawiasu).

module drzwiczki() {
    sz = drzwi_szer + 6;
    difference() {
        union() {
            hull() {
                translate([-sz / 2, 0, 0]) cube([sz, v_zawiasu - 6, 2]);
                translate([0, v_zawiasu - sz / 2 - 2, 0]) cylinder(d = sz, h = 2, $fn = 90);
            }
            // tuleja zawiasu (sześciokąt, płaski spód)
            translate([-8.25, v_zawiasu, h_tulei]) rotate([0, 90, 0]) rotate(30) cylinder(d = 7, h = 16.5, $fn = 6);
            translate([-8.25, v_zawiasu - 6, 0]) cube([16.5, 6, 2]);
        }
        translate([-10, v_zawiasu, h_tulei]) rotate([0, 90, 0]) cylinder(d = 2.2, h = 20, $fn = 16);
        // deski
        for (x = [-sz / 2 + 8:8:sz / 2 - 1]) translate([x - 0.4, -1, 1.4]) cube([0.8, v_zawiasu - 6, 1]);
    }
    // gałka
    translate([0, v_zawiasu * 0.45, 1.99]) cylinder(d1 = 5, d2 = 3.5, h = 3, $fn = 24);
}

// ---------------------------------------------------------------------------
// Kukułka: profil z boku, drukowany na boku (x = do przodu, y = w górę, z = szerokość)

module kukulka_2d() {
    translate([-2, 0]) scale([1, 0.6]) circle(13, $fn = 80);
    translate([9, 6]) circle(6.5, $fn = 48);
    polygon([[13, 8.5], [21, 6], [13, 4]]);
    polygon([[-10, 3], [-19, 8], [-20, 3], [-18, -1], [-10, -4]]);
}

module kukulka() {
    sz = 12;
    difference() {
        linear_extrude(sz) kukulka_2d();
        translate([10.5, 7.5, -1]) cylinder(d = 2, h = sz + 2, $fn = 16);           // oko
        for (z = [-0.01, sz - 0.6]) translate([0, 0, z]) linear_extrude(0.61) {   // skrzydło
            translate([-4, 0]) difference() { scale([1, 0.45]) circle(9, $fn = 60); translate([2, 0]) scale([1, 0.45]) circle(9, $fn = 60); }
            for (i = [0:2]) translate([-6 - i * 3, -2 + i]) square([2.4, 0.6]);
        }
        // gniazdo na końcówkę ramienia (wciskane od spodu)
        translate([0, 0, sz / 2 - 1.65]) linear_extrude(3.3)
            rotate(-kat_ptaka) translate([-3.7, -25]) square([7.4, 26]);
    }
}

// ---------------------------------------------------------------------------
// Ramię: przykręcane/przyklejane do pojedynczego orczyka SG90

module ramie_2d() {
    hull() { circle(d = 13); translate([0, 12]) circle(d = 7); }
    translate([-3.5, 12]) square([7, ramie_L + 1 - 12]);
}

module ramie() {
    difference() {
        linear_extrude(3) ramie_2d();
        translate([0, 0, 3 - 1.7]) linear_extrude(2) hull() { circle(d = 7.4); translate([0, 15]) circle(d = 4.4); }
        translate([0, 0, -1]) cylinder(d = 5.5, h = 5, $fn = 32);
    }
}

// ---------------------------------------------------------------------------
// Uchwyt serwa (L): płyta pionowa z wycięciem, półka przyklejana pod stropem.
// Współrzędne druku: p = wzdłuż Y, q = w górę, r = grubość (płyta na stole).

uchwyt_H = serwo_pod_stropem + 14;

module uchwyt_serwa() {
    qa = uchwyt_H - serwo_pod_stropem;   // oś serwa w układzie uchwytu
    difference() {
        union() {
            cube([36, uchwyt_H, 3]);
            translate([0, uchwyt_H - 3, 0]) cube([36, 3, 17]);
            for (p = [0, 33]) translate([p, uchwyt_H - 12, 0]) cube([3, 12, 15]);   // żebra
        }
        translate([18 - sg_szer / 2 - 0.2, qa - sg_wal - 0.3, -1]) cube([sg_szer + 0.4, sg_dl + 0.6, 5]);
        for (dq = [-sg_rozstaw / 2, sg_rozstaw / 2])
            translate([18, qa - sg_wal + sg_dl / 2 + dq, -1]) cylinder(d = 2, h = 5, $fn = 16);
    }
}

// ---------------------------------------------------------------------------
// Szyszka-obciążnik (ozdoba). Drukowana do góry nogami: szeroki koniec na stole.

module szyszka() {
    H = 72;
    n = 11;
    th = H / n;
    difference() {
        union() for (i = [0:n - 1]) {
            R = 4 + 9.5 * (1 - pow((i + 0.5) / n, 2.2));
            translate([0, 0, i * th]) rotate(i * 15) cylinder(r1 = 0.8 * R, r2 = R, h = th, $fn = 12);
        }
        translate([0, 0, -1]) cylinder(d = 3.5, h = H + 2, $fn = 20);
    }
}

// ---------------------------------------------------------------------------
// Złożenie

module M(m) { multmatrix(m) render(convexity = 6) children(); }
m_przod   = [[1, 0, 0, 0], [0, 0, -1, t], [0, 1, 0, tf], [0, 0, 0, 1]];
m_prawa   = [[0, 0, 1, W / 2 - t], [1, 0, 0, t], [0, 1, 0, tf], [0, 0, 0, 1]];
m_lewa    = [[0, 0, -1, -W / 2 + t], [-1, 0, 0, D - t], [0, 1, 0, tf], [0, 0, 0, 1]];
m_tyl     = [[-1, 0, 0, 0], [0, 0, 1, D - t], [0, 1, 0, tf], [0, 0, 0, 1]];
m_szczyt  = [[1, 0, 0, 0], [0, 0, -1, t], [0, 1, 0, z0g], [0, 0, 0, 1]];
m_szczyt_t = [[1, 0, 0, 0], [0, 0, -1, D], [0, 1, 0, z0g], [0, 0, 0, 1]];
m_dach    = [[cos(spad), 0, sin(spad), 0], [0, 1, 0, 0], [-sin(spad), 0, cos(spad), z0g + Hg], [0, 0, 0, 1]];
m_uchwyt  = [[0, 0, -1, -13], [-1, 0, 0, serwo_Y + 18], [0, 1, 0, Hs - uchwyt_H], [0, 0, 0, 1]];

module mechanizm_ptaka(kat) {
    translate([0, serwo_Y, Za]) rotate([kat, 0, 0]) {
        color("Peru") multmatrix([[0, 0, -1, 1.5], [-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]]) render() ramie();
        translate([0, 0, ramie_L]) rotate([-kat_ptaka, 0, 0])
            color("SlateGray") multmatrix([[0, 0, -1, 6], [-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]]) render() kukulka();
    }
}

module serwo_atrapa() {
    color("RoyalBlue") translate([-13 - 15.9, serwo_Y - sg_szer / 2, Za - sg_wal]) cube([22.7, sg_szer, sg_dl]);
}

module drzwiczki_zlozone(kat = 0) {
    translate([0, -os_zawiasu, z0g + v_zawiasu]) rotate([-kat, 0, 0]) translate([0, 0, -v_zawiasu])
        multmatrix([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]) translate([0, 0, -h_tulei]) render() drzwiczki();
}

module zlozenie(kat_ramienia = kat_schowany, kat_drzwi = 0) {
    drewno = "Burlywood";
    ciemne = "SaddleBrown";
    color(drewno) render() podloga();
    color(drewno) M(m_przod) sciana_przednia();
    color(drewno) M(m_prawa) sciana_boczna();
    color(drewno) M(m_lewa) sciana_boczna();
    color(drewno) M(m_tyl) sciana_tylna();
    color(ciemne) translate([0, 0, Hs]) render() strop();
    color(drewno) M(m_szczyt) szczyt_przedni();
    color(drewno) M(m_szczyt_t) szczyt_tylny();
    {
        color(ciemne) M(m_dach) dach();
        color(ciemne) translate([0, D / 2, 0]) rotate(180) translate([0, -D / 2, 0]) M(m_dach) dach();
        color(ciemne) translate([0, D + nawis, z0g + Hg]) rotate([90, 0, 0]) linear_extrude(Ld) kalenica_2d();
        color(ciemne) translate([0, -nawis, z0g + Hg]) rotate([90, 0, 0]) linear_extrude(3) sparogi_2d();
    }
    // tarcza i wskazówki (10:10)
    translate([0, 0, tf + v_tarczy]) rotate([90, 0, 0]) {
        color("Ivory") render() tarcza_baza();
        color("Black") translate([0, 0, tarcza_g - 0.01]) linear_extrude(0.8) tarcza_wzor_2d();
        color("Black") translate([0, 0, tarcza_g + 1]) rotate(-305) wskazowka_godzinowa();
        color("Black") translate([0, 0, tarcza_g + 1 + grubosc_wsk + 0.5]) rotate(-60) wskazowka_minutowa();
    }
    color(ciemne) drzwiczki_zlozone(kat_drzwi);
    color("DimGray") M(m_uchwyt) uchwyt_serwa();
    for (s = [-1, 1]) color("DimGray") translate([s * (W / 2 - t - 5) - 5, D - t, Hs - 10]) rotate([90, 0, 0]) kostka();
    serwo_atrapa();
    mechanizm_ptaka(kat_ramienia);
    for (s = [-1, 1]) {
        color("Black") translate([s * 40, 30, -60]) cylinder(d = 1, h = 60);
        color(ciemne) translate([s * 40, 30, -60]) rotate([180, 0, 0]) render() szyszka();
    }
}

// widok z boku bez prawej ściany i dachu: ramię i ptak wysunięte, drzwiczki otwarte,
// półprzezroczyście — ptak schowany
module polowa() { children(); }

module przekroj() {
    drewno = "Burlywood";
    polowa() color(drewno) render() podloga();
    polowa() color(drewno) M(m_przod) sciana_przednia();
    color(drewno) M(m_lewa) sciana_boczna();
    polowa() color(drewno) M(m_tyl) sciana_tylna();
    polowa() color("SaddleBrown") translate([0, 0, Hs]) render() strop();
    polowa() color(drewno) M(m_szczyt) szczyt_przedni();
    polowa() color(drewno) M(m_szczyt_t) szczyt_tylny();
    polowa() translate([0, 0, tf + v_tarczy]) rotate([90, 0, 0]) color("Ivory") render() tarcza();
    color(drewno) drzwiczki_zlozone(62);
    color("DimGray") M(m_uchwyt) uchwyt_serwa();
    serwo_atrapa();
    mechanizm_ptaka(kat_wysuniety);
    %mechanizm_ptaka(kat_schowany);
}

if (czesc == "zlozenie") zlozenie();
else if (czesc == "przekroj") przekroj();
else if (czesc == "podloga") podloga();
else if (czesc == "sciana_przednia") sciana_przednia();
else if (czesc == "sciana_boczna") sciana_boczna();
else if (czesc == "sciana_tylna") sciana_tylna();
else if (czesc == "strop") strop();
else if (czesc == "szczyt_przedni") szczyt_przedni();
else if (czesc == "szczyt_tylny") szczyt_tylny();
else if (czesc == "dach") dach();
else if (czesc == "kalenica") kalenica();
else if (czesc == "sparogi") sparogi();
else if (czesc == "tarcza") tarcza();
else if (czesc == "wskazowki") wskazowki();
else if (czesc == "drzwiczki") drzwiczki();
else if (czesc == "kukulka") kukulka();
else if (czesc == "ramie") ramie();
else if (czesc == "uchwyt_serwa") uchwyt_serwa();
else if (czesc == "kostka") kostka();
else if (czesc == "szyszka") szyszka();
else if (czesc == "test_otworow") test_otworow();
