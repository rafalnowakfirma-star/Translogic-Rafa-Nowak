// Zegar ścienny do druku 3D — model parametryczny (OpenSCAD)
//
// Pod standardowy mechanizm kwarcowy (np. cichy „sweep” 56×56 mm, gwint M8,
// zasilanie AA). Tarcza drukuje się licem do stołu — gładki front bez podpór.
//
// Eksport pojedynczej części z linii poleceń:
//   openscad -D 'czesc="tarcza"' -o tarcza.stl zegar.scad
//
// czesc: "zlozenie" (podgląd), "tarcza", "wskazowki", "wklady",
//        "wklady_mmu" (wkładki bez luzu, do drukarek wielokolorowych), "test_otworow"

/* [Wybór części] */
czesc = "zlozenie"; // [zlozenie, tarcza, wskazowki, wklady, wklady_mmu, test_otworow]

/* [Tarcza] */
srednica = 200;          // średnica zewnętrzna [mm] — musi zmieścić się na stole
grubosc_tarczy = 3;      // grubość płyty frontowej (gwint mechanizmu zwykle do ~5 mm)
glebokosc = 22;          // całkowita głębokość: front → ściana (mechanizm ma ~16 mm)
scianka = 2.4;           // grubość obrzeża
faza = 1;                // faza na przedniej krawędzi
otwor_walka = 8.2;       // otwór na gwintowaną tuleję mechanizmu
mechanizm = 58;          // wolne pole na korpus mechanizmu (kwadrat)

/* [Tarcza — wygląd] */
styl = "arabskie";       // [arabskie, rzymskie, kreski]
minutnik = true;         // 60 kresek minutowych
glebokosc_grawer = 0.8;  // głębokość grawerunku = grubość wkładek
luz_wkladu = 0.12;       // luz wkładki na stronę
font_arabski = "Liberation Sans:style=Bold";
font_rzymski = "Liberation Serif:style=Bold";

/* [Wskazówki] */
grubosc_wsk = 1.2;       // grubsze mogą nie zmieścić się na wałku mechanizmu
otwor_godz = 5.2;        // okrągły otwór wskazówki godzinowej
otwor_min_d = 3.3;       // otwór minutowy: średnica…
otwor_min_plaska = 2.4;  // …i rozstaw dwóch ścięć (kształt „double-D”)

$fn = 120;

// ---------------------------------------------------------------------------
R = srednica / 2;
r_kreski = R - scianka - 3;            // zewnętrzny promień podziałki
dl_kreski_h = srednica * 0.045;        // kreska godzinowa
dl_kreski_m = srednica * 0.02;         // kreska minutowa
rozm_arab = srednica * 0.075;
rozm_rzym = srednica * 0.06;
r_cyfr = r_kreski - dl_kreski_h - 4 - (styl == "rzymskie" ? rozm_rzym / 2 : rozm_arab * 0.65);

dl_min = r_kreski - 2;
dl_godz = r_cyfr - (styl == "kreski" ? 0 : rozm_arab * 0.45);
ogon = 18;

rzymskie = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"];

// ---------------------------------------------------------------------------
// Front tarczy w 2D, tak jak widzi go patrzący (12 na górze, +Y).

module kreski_godzinowe_2d() {
    sz = srednica * 0.015;
    for (h = [0:11]) rotate(-h * 30) {
        if (styl == "kreski" && h == 0) {
            // podwójna kreska na dwunastce
            for (dx = [-sz, sz])
                translate([dx - sz / 2, r_kreski - dl_kreski_h * 1.4]) square([sz, dl_kreski_h * 1.4]);
        } else {
            k = (styl == "kreski" && h % 3 == 0) ? 1.4 : 1;
            translate([-sz * k / 2, r_kreski - dl_kreski_h * k]) square([sz * k, dl_kreski_h * k]);
        }
    }
}

module cyfry_2d() {
    if (styl == "arabskie")
        for (h = [0:11]) {
            a = h * 30;
            translate([r_cyfr * sin(a), r_cyfr * cos(a)])
                text(str(h == 0 ? 12 : h), size = rozm_arab, font = font_arabski,
                     halign = "center", valign = "center");
        }
    else if (styl == "rzymskie")
        for (h = [0:11]) rotate(-h * 30) translate([0, r_cyfr])
            text(rzymskie[h], size = rozm_rzym, font = font_rzymski,
                 halign = "center", valign = "center");
}

module kreski_minutowe_2d() {
    sz = srednica * 0.006;
    for (m = [0:59]) if (m % 5 != 0) rotate(-m * 6)
        translate([-sz / 2, r_kreski - dl_kreski_m]) square([sz, dl_kreski_m]);
}

// elementy, które dostają kolorową wkładkę
module wzor_wkladek_2d() {
    kreski_godzinowe_2d();
    cyfry_2d();
}

// ---------------------------------------------------------------------------
// Tarcza w orientacji do druku: front na z=0 (stół), obrzeże rośnie w górę,
// czyli w stronę ściany. Wzór frontu jest lustrzany, bo oglądamy go od spodu.

module tarcza() {
    difference() {
        union() {
            rotate_extrude($fn = 240) polygon([
                [0, 0], [R - faza, 0], [R, faza], [R, glebokosc],
                [R - scianka, glebokosc], [R - scianka, grubosc_tarczy], [0, grubosc_tarczy]
            ]);
            zebra();
            wieszak();
        }
        translate([0, 0, -1]) cylinder(d = otwor_walka, h = grubosc_tarczy + 2, $fn = 48);
        translate([0, 0, -0.01]) linear_extrude(glebokosc_grawer + 0.01) mirror([1, 0, 0]) {
            wzor_wkladek_2d();
            if (minutnik) kreski_minutowe_2d();
        }
        otwor_wieszaka();
    }
}

// usztywnienia promieniowe — omijają mechanizm i wieszak (12 i 6 godzina)
module zebra() {
    r0 = mechanizm / 2 * sqrt(2) + 2;
    for (a = [0:60:300]) rotate(a)
        translate([r0, -1, grubosc_tarczy - 0.01]) cube([R - scianka - r0 + 0.5, 2, 8]);
}

wieszak_szer = 30;
wieszak_gl = 20;
wieszak_y = R - scianka - wieszak_gl;

module wieszak() {
    translate([-wieszak_szer / 2, wieszak_y, grubosc_tarczy - 0.01])
        cube([wieszak_szer, wieszak_gl + scianka / 2, glebokosc - grubosc_tarczy + 0.01]);
}

// otwór typu „dziurka od klucza”: łeb wkrętu wchodzi w duży otwór,
// po opuszczeniu zegara trzon wsuwa się w szczelinę ku górze
module otwor_wieszaka() {
    y_otw = wieszak_y + 7;
    y_konc = wieszak_y + wieszak_gl - 6;
    plyta = 2;
    komora = 3.5;
    translate([0, 0, glebokosc - plyta - 0.01]) {
        translate([0, y_otw, 0]) cylinder(d = 9.5, h = plyta + 1, $fn = 40);
        hull() for (y = [y_otw, y_konc]) translate([0, y, 0]) cylinder(d = 4.5, h = plyta + 1, $fn = 30);
    }
    translate([0, 0, glebokosc - plyta - komora])
        hull() for (y = [y_otw, y_konc]) translate([0, y, 0]) cylinder(d = 10, h = komora, $fn = 40);
}

// ---------------------------------------------------------------------------
// Wkładki w kontrastowym kolorze, ułożone dokładnie tak, jak w tarczy.
// Drukuje się je spodem do stołu; spód to widoczna strona.

module wklady(luz) {
    linear_extrude(glebokosc_grawer) mirror([1, 0, 0])
        offset(delta = -luz) wzor_wkladek_2d();
}

// ---------------------------------------------------------------------------
// Wskazówki — płaskie, skierowane wzdłuż +Y.

module otwor_min_2d() {
    intersection() {
        circle(d = otwor_min_d, $fn = 40);
        square([otwor_min_plaska, otwor_min_d + 1], center = true);
    }
}

module wskazowka_2d(dl, w0, w1, piasta, ogon_w) {
    hull() { circle(d = w0); translate([0, dl]) circle(d = w1); }
    hull() { circle(d = w0); translate([0, -ogon]) circle(d = ogon_w); }
    circle(d = piasta);
}

module wskazowka_minutowa() {
    linear_extrude(grubosc_wsk) difference() {
        wskazowka_2d(dl_min, 6, 2, 10, 5);
        otwor_min_2d();
    }
}

module wskazowka_godzinowa() {
    linear_extrude(grubosc_wsk) difference() {
        wskazowka_2d(dl_godz, 9, 3, 12, 6);
        circle(d = otwor_godz, $fn = 40);
    }
}

module wskazowki() {
    translate([-10, 0, 0]) wskazowka_minutowa();
    translate([12, -dl_godz / 2, 0]) wskazowka_godzinowa();
}

// mały wydruk do sprawdzenia pasowania na mechanizmie przed drukiem całości
module test_otworow() {
    linear_extrude(grubosc_wsk) difference() {
        circle(d = 12); otwor_min_2d();
    }
    translate([16, 0, 0]) linear_extrude(grubosc_wsk) difference() {
        circle(d = 14); circle(d = otwor_godz, $fn = 40);
    }
    translate([36, 0, 0]) linear_extrude(grubosc_tarczy) difference() {
        circle(d = 20); circle(d = otwor_walka, $fn = 48);
    }
}

// ---------------------------------------------------------------------------
// Podgląd złożonego zegara (front do góry), godzina 10:10.

module zlozenie() {
    rotate([0, 180, 0]) {
        color("WhiteSmoke") tarcza();
        color("DimGray") translate([0, 0, -0.02]) wklady(0);
        if (minutnik) color("DarkGray") translate([0, 0, -0.02])
            linear_extrude(glebokosc_grawer) mirror([1, 0, 0]) kreski_minutowe_2d();
    }
    color("Black") translate([0, 0, 1]) rotate(-305) wskazowka_godzinowa();
    color("FireBrick") translate([0, 0, 1 + grubosc_wsk + 0.5]) rotate(-60) wskazowka_minutowa();
}

if (czesc == "zlozenie") zlozenie();
else if (czesc == "tarcza") tarcza();
else if (czesc == "wskazowki") wskazowki();
else if (czesc == "wklady") wklady(luz_wkladu);
else if (czesc == "wklady_mmu") wklady(0);
else if (czesc == "test_otworow") test_otworow();
