// Ozdoby choinkowe do druku 3D — parametryczny projekt OpenSCAD.
//
// Wybierz model zmienną `model` (lub w Customizerze OpenSCAD), potem
// F6 (Render) i F7 (Export STL). Z linii poleceń:
//   openscad -D 'model="gwiazda"' -o gwiazda.stl ozdoby.scad
//
// Wszystkie wymiary w milimetrach. Modele leżą płasko na stole
// i drukują się bez podpór.

/* [Wybór modelu] */
model = "gwiazda"; // [gwiazda, platek, choinka, choinka_spiralna, bombka_napis]

/* [Uszko do zawieszenia] */
uszko_srednica = 8;   // zewnętrzna średnica oczka
uszko_scianka  = 2;   // grubość ścianki oczka

/* [Gwiazda] */
gwiazda_ramiona  = 5;
gwiazda_promien  = 35;  // promień do czubka ramienia
gwiazda_wciecie  = 0.45; // promień wewnętrzny jako ułamek promienia
gwiazda_podstawa = 1.6; // grubość płaskiej podstawy
gwiazda_szczyt   = 7;   // wysokość fasetowanego szczytu

/* [Płatek śniegu] */
platek_promien  = 40;
platek_ramie    = 3.2;  // szerokość ramion
platek_grubosc  = 2.4;

/* [Choinka płaska] */
choinka_wysokosc = 75;
choinka_grubosc  = 2.4;
choinka_ozdoby   = 1.2; // wysokość wypukłych bombek (zmiana koloru!)

/* [Choinka spiralna] */
spirala_wysokosc = 70;
spirala_promien  = 22;
spirala_ramiona  = 8;
spirala_skret    = 180; // stopnie skrętu; >200 daje nawisy ponad 45°

/* [Bombka z napisem] */
bombka_promien = 32;
bombka_grubosc = 2.4;
napis_1 = "Wesołych";
napis_2 = "Świąt";
napis_3 = "2026";
napis_wysokosc = 1.2;   // wypukłość napisu i obwódki (zmiana koloru!)
czcionka = "Liberation Sans:style=Bold";

/* [Hidden] */
$fn = 64;

// ---------------------------------------------------------------- pomocnicze

module gwiazda2d(n, r_out, r_in) {
    polygon([for (i = [0 : 2 * n - 1])
        let (a = 90 + i * 180 / n, r = i % 2 == 0 ? r_out : r_in)
        [r * cos(a), r * sin(a)]]);
}

module pasek(p1, p2, w) {
    hull() {
        translate(p1) circle(d = w);
        translate(p2) circle(d = w);
    }
}

// Płaskie oczko; `y` to punkt na brzegu ozdoby, do którego się doczepia.
module uszko_plaskie(y, h) {
    r = uszko_srednica / 2;
    linear_extrude(h)
        translate([0, y + r - uszko_scianka / 2])
            difference() {
                circle(r);
                circle(r - uszko_scianka);
            }
}

// ---------------------------------------------------------------- modele

module gwiazda() {
    r_in = gwiazda_promien * gwiazda_wciecie;
    linear_extrude(gwiazda_podstawa)
        gwiazda2d(gwiazda_ramiona, gwiazda_promien, r_in);
    translate([0, 0, gwiazda_podstawa])
        linear_extrude(gwiazda_szczyt, scale = 0)
            gwiazda2d(gwiazda_ramiona, gwiazda_promien, r_in);
    // czubek ramienia jest ostry — pogrubiamy miejsce styku z oczkiem
    linear_extrude(gwiazda_podstawa)
        pasek([0, gwiazda_promien - 6], [0, gwiazda_promien], 3);
    uszko_plaskie(gwiazda_promien, gwiazda_podstawa);
}

module platek2d() {
    L = platek_promien;
    w = platek_ramie;
    for (k = [0 : 5]) rotate(k * 60) {
        pasek([0, 0], [0, L], w);
        // gałązki: dłuższe bliżej środka, krótsze przy czubku
        for (f = [0.38, 0.62, 0.84]) {
            y = f * L;
            b = (1 - f) * L * 0.75 + 3;
            for (s = [-1, 1])
                pasek([0, y], [s * b * sin(55), y + b * cos(55)], w * 0.85);
        }
        // romb na końcu ramienia
        translate([0, L]) rotate(45) square(w * 1.8, center = true);
    }
    difference() {
        circle(r = L * 0.24, $fn = 6);
        circle(r = L * 0.13, $fn = 6);
    }
}

module platek() {
    linear_extrude(platek_grubosc) platek2d();
    uszko_plaskie(platek_promien + platek_ramie, platek_grubosc);
}

module choinka2d() {
    H = choinka_wysokosc;
    pien_h = H * 0.12;
    pietra = 4;
    korona_h = H - pien_h;
    // pień
    translate([-H * 0.07, 0]) square([H * 0.14, pien_h + 1]);
    // piętra korony — każde to trapez z lekko zadartymi rogami
    for (i = [0 : pietra - 1]) {
        y0 = pien_h + i * korona_h * 0.21;
        szer = H * 0.38 * (1 - i * 0.2);
        gora = i == pietra - 1 ? H : y0 + korona_h * 0.42;
        polygon([[-szer, y0], [szer, y0], [szer * 0.92, y0 + 2],
                 [0, gora], [-szer * 0.92, y0 + 2]]);
    }
}

module choinka() {
    H = choinka_wysokosc;
    linear_extrude(choinka_grubosc) choinka2d();
    // gwiazdka na czubku
    linear_extrude(choinka_grubosc)
        translate([0, H]) gwiazda2d(5, H * 0.09, H * 0.04);
    // wypukłe bombki — od tej warstwy można zmienić filament
    linear_extrude(choinka_grubosc + choinka_ozdoby)
        for (p = [[-0.22, 0.22], [0.18, 0.27], [-0.12, 0.42],
                  [0.14, 0.50], [-0.05, 0.64], [0.07, 0.76]])
            translate([p[0] * H, p[1] * H]) circle(d = H * 0.065);
    uszko_plaskie(H + H * 0.09, choinka_grubosc);
}

module choinka_spiralna() {
    H = spirala_wysokosc;
    linear_extrude(H, twist = -spirala_skret, scale = 0.06, slices = 160)
        gwiazda2d(spirala_ramiona, spirala_promien, spirala_promien * 0.72);
    // pionowe oczko na czubku (małe łuki drukują się bez podpór)
    r = uszko_srednica / 2;
    translate([0, 0, H - 0.6 + r])
        rotate([90, 0, 0])
            rotate_extrude($fn = 48)
                translate([r - uszko_scianka / 2, 0])
                    circle(d = uszko_scianka, $fn = 24);
}

module bombka_napis() {
    R = bombka_promien;
    t = bombka_grubosc;
    nasadka_w = R * 0.42;
    nasadka_h = R * 0.2;
    // korpus bombki z nasadką
    linear_extrude(t) {
        circle(R, $fn = 128);
        translate([-nasadka_w / 2, R - 2]) square([nasadka_w, nasadka_h + 2]);
    }
    // wypukła obwódka, prążki nasadki i napis
    linear_extrude(t + napis_wysokosc) {
        difference() {
            circle(R, $fn = 128);
            circle(R - 2, $fn = 128);
        }
        for (i = [0 : 2])
            translate([-nasadka_w / 2, R + 1 + i * nasadka_h * 0.33])
                square([nasadka_w, 1.2]);
        translate([0, R * 0.30])
            text(napis_1, size = R * 0.24, font = czcionka,
                 halign = "center", valign = "center");
        translate([0, -R * 0.05])
            text(napis_2, size = R * 0.30, font = czcionka,
                 halign = "center", valign = "center");
        translate([0, -R * 0.45])
            text(napis_3, size = R * 0.20, font = czcionka,
                 halign = "center", valign = "center");
    }
    uszko_plaskie(R + nasadka_h, t);
}

if      (model == "gwiazda")          gwiazda();
else if (model == "platek")           platek();
else if (model == "choinka")          choinka();
else if (model == "choinka_spiralna") choinka_spiralna();
else if (model == "bombka_napis")     bombka_napis();
