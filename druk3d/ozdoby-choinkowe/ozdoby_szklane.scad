// Ozdoby w stylu dawnych szklanych bombek — do druku 3D i malowania.
//
// Bryły obrotowe (kule, kryształ, kropla) drukują się jako DWIE POŁÓWKI
// leżące płasko na przekroju: bez podpór, z gładką powierzchnią.
// Połówki sklejasz, a dwa otwory na kołki z kawałków filamentu 1,75 mm
// pilnują, żeby się nie przesunęły. Sopel i dzwonek drukują się w całości.
//
//   openscad -D 'model="kula_kropki"' -o kula_kropki.stl ozdoby_szklane.scad
//
// Ustaw `podglad = true`, żeby zobaczyć złożoną ozdobę zamiast połówek.

/* [Wybór modelu] */
model = "kula_kropki"; // [kula_kropki, kula_karbowana, krysztal, kropla_vintage, sopel, dzwonek]
podglad = false;       // true: cała ozdoba (do oglądania), false: części do druku

/* [Rozmiar] */
skala = 1.0;           // 1.0 = kula ok. 60 mm średnicy

/* [Kołki ustalające] */
kolek_srednica = 1.95; // otwór na filament 1,75 mm z luzem
kolek_glebokosc = 6;   // w każdą połówkę

/* [Hidden] */
$fn = 96;
DUZO = 200;

// ------------------------------------------------------------- elementy wspólne

module torus(R, r) {
    rotate_extrude($fn = 96) translate([R, 0]) circle(r, $fn = 24);
}

// Prążkowany kapturek jak w szklanej bombce + oczko w płaszczyźnie XZ
// (przy podziale na połówki każda dostaje połowę grubości oczka).
module kapturek(z0, r = 6) {
    translate([0, 0, z0]) {
        cylinder(h = 8, r = r);
        for (i = [0 : 3]) translate([0, 0, 1 + i * 2]) torus(r, 0.6);
        translate([0, 0, 8]) cylinder(h = 1.5, r1 = r, r2 = r * 0.6);
        translate([0, 0, 9.5 + 4])
            rotate([90, 0, 0])
                linear_extrude(4, center = true)
                    difference() { circle(5); circle(3); }
    }
}

// Otwory na kołki wzdłuż osi, prostopadle do płaszczyzny podziału.
module kolki(z_list) {
    for (z = z_list) translate([0, 0, z]) rotate([90, 0, 0])
        cylinder(h = 2 * kolek_glebokosc, d = kolek_srednica, center = true, $fn = 24);
}

// Tnie bryłę płaszczyzną y=0 i kładzie obie połówki przekrojem na stół.
module polowki(odstep) {
    if (podglad) children();
    else {
        translate([-odstep, 0, 0]) rotate([-90, 0, 0])
            intersection() { children(); translate([-DUZO, -DUZO, -DUZO]) cube([2 * DUZO, DUZO, 2 * DUZO]); }
        translate([odstep, 0, 0]) rotate([90, 0, 0])
            intersection() { children(); translate([-DUZO, 0, -DUZO]) cube(2 * DUZO); }
    }
}

// ------------------------------------------------------------- modele

// Klasyczna kula z wypukłymi pasami i perełkami — gotowy „szablon” do malowania.
module kula_kropki() {
    R = 30;
    difference() {
        union() {
            sphere(R, $fn = 128);
            for (z = [-13, 0, 13]) translate([0, 0, z]) torus(sqrt(R * R - z * z), 1.1);
            for (z = [-6.5, 6.5], i = [0 : 17])
                rotate(i * 20 + 10) translate([sqrt(R * R - z * z), 0, z]) sphere(1.9, $fn = 24);
            for (z = [-21, 21], i = [0 : 11])
                rotate(i * 30 + 15) translate([sqrt(R * R - z * z), 0, z]) sphere(1.5, $fn = 24);
            // kropla na dole jak w dmuchanej bombce
            translate([0, 0, -R - 1]) sphere(3, $fn = 32);
            kapturek(R - 2.5);
        }
        kolki([-12, 12]);
    }
}

// Vintage „dynia” — 12 żeber rozdzielonych rowkami (pomaluj rowki innym kolorem).
module kula_karbowana() {
    difference() {
        union() {
            scale([20, 20, 27]) sphere(1, $fn = 64);
            for (i = [0 : 11])
                rotate(i * 30) translate([17, 0, 0]) scale([12, 12, 29]) sphere(1, $fn = 48);
            translate([0, 0, -29]) cylinder(h = 4, r1 = 1.5, r2 = 5);
            kapturek(26);
        }
        kolki([-12, 12]);
    }
}

// Szlifowany kryształ — fasety odbijają światło jak cięte szkło.
module krysztal() {
    difference() {
        union() {
            rotate_extrude($fn = 16)
                polygon([[0, -40], [10, -30], [20, -17], [27, -4], [28, 3],
                         [25, 12], [18, 21], [8, 27], [0, 28]]);
            kapturek(25.5, r = 5.5);
        }
        kolki([-10, 10]);
    }
}

// Kropla z „reflektorami” — wklęsłymi oczkami, które w starych bombkach
// malowano od środka innym kolorem.
module kropla_vintage() {
    difference() {
        union() {
            hull() {
                translate([0, 0, 6]) scale([22, 22, 20]) sphere(1, $fn = 96);
                translate([0, 0, -28]) cylinder(h = 1, r = 3.5);
            }
            for (z = [-29, -33]) translate([0, 0, z]) torus(z == -29 ? 3.8 : 3.0, 1.2);
            translate([0, 0, -50]) cylinder(h = 22.5, r1 = 0.6, r2 = 3.3);
            translate([0, 0, 6]) torus(22, 1.3);
            translate([0, 0, 21]) torus(13.8, 1);
            kapturek(23);
        }
        // reflektory na 45°, 135°, 225°, 315° — żaden nie wypada na linii podziału
        for (i = [0 : 3]) rotate(45 + i * 90) translate([29, 0, 5]) sphere(11);
        kolki([-8, 14]);
    }
}

// Skręcony sopel. Drukowany kapturkiem do stołu, szpicem w górę;
// zawieszka przez poziomy otwór w kapturku (nitka albo haczyk drutowy).
module sopel() {
    kap = 9;
    difference() {
        union() {
            cylinder(h = kap, r = 7);
            for (i = [0 : 2]) translate([0, 0, 1.5 + i * 2.5]) torus(7, 0.7);
            translate([0, 0, kap])
                linear_extrude(95, twist = -540, scale = 0.02, slices = 300)
                    offset(r = 0.6) offset(delta = -0.6)
                        polygon([for (i = [0 : 11])
                            let (a = i * 30, r = i % 2 == 0 ? 10 : 6.5)
                            [r * cos(a), r * sin(a)]]);
        }
        translate([0, 0, 4.5]) rotate([90, 0, 0]) cylinder(h = 20, d = 3, center = true, $fn = 24);
    }
}

// Dzwonek z wywiniętym brzegiem, drukowany w całości otworem do stołu.
// Wnętrze ma ściany nachylone najwyżej 45°, więc nie potrzebuje podpór.
module dzwonek() {
    rotate_extrude($fn = 128)
        polygon(concat(
            [[24, 0], [26, 1.2], [25.5, 3], [21, 9], [18, 16], [16, 24],
             [15, 32], [13.5, 39], [9, 44], [0, 46.5]],
            [[0, 43], [11.5, 31], [12.8, 24], [14.6, 16], [17.5, 9], [22, 2.5], [22, 0]]));
    for (z = [6, 28]) translate([0, 0, z]) torus(z == 6 ? 23 : 15.6, 1.1);
    for (i = [0 : 15]) rotate(i * 22.5) translate([19.4, 0, 14]) sphere(1.6, $fn = 24);
    // kapturek i pionowe oczko
    translate([0, 0, 45]) {
        cylinder(h = 6, r = 5);
        for (i = [0 : 1]) translate([0, 0, 1.5 + i * 2.5]) torus(5, 0.6);
        translate([0, 0, 6 + 4.2]) rotate([90, 0, 0]) torus(4.2, 1.2);
    }
}

scale(skala) {
    if      (model == "kula_kropki")    polowki(36) kula_kropki();
    else if (model == "kula_karbowana") polowki(36) kula_karbowana();
    else if (model == "krysztal")       polowki(34) krysztal();
    else if (model == "kropla_vintage") polowki(30) kropla_vintage();
    else if (model == "sopel")          rotate([podglad ? 180 : 0, 0, 0]) sopel();
    else if (model == "dzwonek")        dzwonek();
}
