"""Meble 3D do wnętrz rozstawianych ręcznie (H.meble): zabudowa AGD, komody, obrazy, lustra, zasłony,
pokój dziecięcy, kino domowe, lampy, kuchnia ogrodowa z grillem, garderoba w holu.

Układ lokalny jak w meble3d: x – szerokość, tył mebla przy +d/2, front przy −d/2, z od podłogi.
Rejestrowane w meble3d.BUILDERS.
"""
import math

from .meble3d import MB, T, R, Sc, _vase, _stems, _book_stack, _bowl, _plant_small, _table_lamp, _ns, _fill_books

KOLORY_DZ = ("tk_akcent0", "tk_akcent1", "tk_akcent2", "tk_kolor")


def _art(it):
    return getattr(it, "art", None) or {}


# ------------------------------------------------------------------ kuchnia: zabudowa wysoka z AGD
def _zabudowa(B):
    it, st = B.it, B.st
    w, d = it.w, it.d
    H = min(2.32, (B.ceil or 2.6) - 0.04)
    mb = MB()
    yf = -d / 2 + 0.02
    mb.box(-w / 2 + 0.005, yf + 0.06, 0.0, w / 2 - 0.005, d / 2, 0.10, "cokol", r=0.002)
    mb.box(-w / 2, yf + 0.019, 0.10, w / 2, d / 2, H, "lak_front", r=0.002)
    g = 0.003
    ncol = max(2, int(round(w / 0.6)))
    cw = (w - g * (ncol + 1)) / ncol
    hm = "akcent"

    def front(x0, x1, z0, z1, hz=None, hx=None):
        mb.box(x0, -d / 2, z0, x1, -d / 2 + 0.021, z1, "lak_front", r=0.002)
        if hz is not None:      # uchwyt poziomy (szuflady) albo pionowy przy krawędzi (drzwi)
            cx = (x0 + x1) / 2
            mb.box(cx - 0.12, -d / 2 - 0.026, hz - 0.006, cx + 0.12, -d / 2 - 0.014, hz + 0.006, hm, r=0.003)
        elif hx is not None:
            mb.box(hx - 0.006, -d / 2 - 0.026, z0 + 0.15, hx + 0.006, -d / 2 - 0.014, z0 + 0.15 + min(0.6, z1 - z0 - 0.3),
                   hm, r=0.003)
    for c in range(ncol):
        x0 = -w / 2 + g + c * (cw + g)
        x1 = x0 + cw
        if c == 0:
            # lodówka z zamrażarką w zabudowie: dwa fronty
            front(x0, x1, 0.10 + g, 0.86, hx=x1 - 0.05)
            front(x0, x1, 0.86 + g, H - g, hx=x1 - 0.05)
            continue
        # słupek: szuflada, piekarnik, mikrofala, szafka u góry
        front(x0, x1, 0.10 + g, 0.46, hz=0.40)
        zo0, zo1 = 0.47, 1.06
        mb.box(x0, -d / 2 - 0.002, zo0, x1, -d / 2 + 0.02, zo1, "stal", r=0.003)                     # rama piekarnika
        mb.box(x0 + 0.02, -d / 2 - 0.006, zo0 + 0.02, x1 - 0.02, -d / 2, zo1 - 0.11, "szklo_czarne", r=0.003)
        mb.box(x0 + 0.02, -d / 2 - 0.006, zo1 - 0.09, x1 - 0.02, -d / 2, zo1 - 0.01, "szklo_czarne", r=0.002)
        mb.box((x0 + x1) / 2 - 0.04, -d / 2 - 0.008, zo1 - 0.065, (x0 + x1) / 2 + 0.04, -d / 2 - 0.005, zo1 - 0.035,
               "led", r=0.0)                                                                         # wyświetlacz
        mb.tube([(x0 + 0.05, -d / 2 - 0.006, zo1 - 0.14), (x0 + 0.05, -d / 2 - 0.05, zo1 - 0.14),
                 (x1 - 0.05, -d / 2 - 0.05, zo1 - 0.14), (x1 - 0.05, -d / 2 - 0.006, zo1 - 0.14)], 0.009, "stal", n=10)
        zm0, zm1 = 1.08, 1.46
        mb.box(x0, -d / 2 - 0.002, zm0, x1, -d / 2 + 0.02, zm1, "stal", r=0.003)                     # mikrofala
        mb.box(x0 + 0.02, -d / 2 - 0.006, zm0 + 0.03, x1 - 0.14, -d / 2, zm1 - 0.03, "szklo_czarne", r=0.003)
        mb.box(x1 - 0.12, -d / 2 - 0.006, zm0 + 0.03, x1 - 0.02, -d / 2, zm1 - 0.03, "szklo_czarne", r=0.002)
        front(x0, x1, zm1 + g, H - g, hx=x0 + 0.05)
    B.mesh(mb, "zabudowa")


# ------------------------------------------------------------------ komoda / konsola z dekoracjami
def _komoda(B):
    it, r = B.it, B.rnd
    w, d, h = it.w, it.d, it.h
    mb = MB()
    n = max(2, int(round(w / 0.45)))
    _ns(mb, -w / 2, -d / 2, w / 2, d / 2, h, "drewno", drawers=1 if B.rk == "hol" else 2, handle=None, legs=True)
    # pionowe podziały frontów (szczeliny) i uchwyty-wpusty
    for k in range(1, n):
        x = -w / 2 + k * w / n
        mb.box(x - 0.0015, -d / 2 - 0.0005, 0.13, x + 0.0015, -d / 2 + 0.002, h - 0.01, "czarny_mat", r=0.0)
    dec = MB()
    if B.rk in ("sypialnia_glowna", "sypialnia"):
        _book_stack(dec, r, -w / 2 + 0.25, 0.02, h, n=2, big=True)
        _vase(dec, w / 2 - 0.22, 0.05, h, 0.28, 0.07, "kamionka", kind=0)
        _stems(dec, w / 2 - 0.22, 0.05, h + 0.2, 0.4, 6, r)
        _bowl(dec, 0.0, 0.0, h, 0.12, 0.05, "kamionka")
    else:
        _vase(dec, -w / 2 + 0.2, 0.04, h, 0.36, 0.08, "kamionka", kind=1)
        _stems(dec, -w / 2 + 0.2, 0.04, h + 0.25, 0.45, 7, r)
        _bowl(dec, w / 2 - 0.25, 0.0, h, 0.13, 0.05, "ceramika")
        _plant_small(dec, r, 0.05, 0.05, h, r=0.06, h=0.1)
    B.mesh(mb, "komoda")
    B.mesh(dec, "komoda_dekoracje")
    if B.rk in ("sypialnia_glowna", "hol"):
        _table_lamp(B, 0.0 if B.rk == "hol" else -w / 2 + 0.55, 0.06, h, 0.8)


# ------------------------------------------------------------------ obraz, lustro
def _obraz(B):
    it, r = B.it, B.rnd
    a = _art(it)
    w, h, zc = it.w, a.get("h", 0.7), a.get("zc", 1.5)
    dz = getattr(it, "wariant", None) == "dziecko"
    mb = MB()
    yb = it.d / 2
    t = 0.032
    fr = "lak_bialy" if dz else ("drewno" if r.random() < 0.5 else "czarny_mat")
    fw = 0.025
    z0, z1 = zc - h / 2, zc + h / 2
    # rama z czterech listew i płótno w głębi (passe-partout przy zdjęciach)
    for x0, x1, za, zb in ((-w / 2, w / 2, z0, z0 + fw), (-w / 2, w / 2, z1 - fw, z1),
                           (-w / 2, -w / 2 + fw, z0, z1), (w / 2 - fw, w / 2, z0, z1)):
        mb.box(x0, yb - t, za, x1, yb, zb, fr, r=0.002)
    pp = 0.05 if (dz or r.random() < 0.4) else 0.0
    if pp:
        mb.box(-w / 2 + fw, yb - t + 0.008, z0 + fw, w / 2 - fw, yb - 0.004, z1 - fw, "papier", r=0.0)
    mb.box(-w / 2 + fw + pp, yb - t + 0.006, z0 + fw + pp, w / 2 - fw - pp, yb - 0.004, z1 - fw - pp,
           f"obraz:{a.get('seed', 0)}", r=0.0)
    B.mesh(mb, "obraz")


def _lustro(B):
    it = B.it
    a = _art(it)
    w, h, zc = it.w, a.get("h", 1.0), a.get("zc", 1.45)
    mb = MB()
    yb = it.d / 2
    z0, z1 = zc - h / 2, zc + h / 2
    mb.box(-w / 2, yb - 0.022, z0, w / 2, yb, z1, "czarny_metal", r=0.004)
    mb.box(-w / 2 + 0.012, yb - 0.026, z0 + 0.012, w / 2 - 0.012, yb - 0.02, z1 - 0.012, "lustro", r=0.0)
    if B.rk in ("lazienka", "wc"):
        mb.box(-w / 2 + 0.03, yb - 0.03, z1 + 0.02, w / 2 - 0.03, yb, z1 + 0.05, "czarny_metal", r=0.004)
        mb.box(-w / 2 + 0.05, yb - 0.032, z1 + 0.02, w / 2 - 0.05, yb - 0.029, z1 + 0.024, "led", r=0.0)
        B.light(None, 15.0, kind="AREA", M=T(0, yb - 0.04, z1 + 0.02) @ R("X", 180), area=(w - 0.1, 0.03), name="kinkiet")
    B.mesh(mb, "lustro")


def _zaslona(B):
    """Zasłona lniana zebrana przy oknie: fale od szyny pod sufitem do podłogi."""
    it, r = B.it, B.rnd
    w = it.w
    top = (B.ceil or 2.8) - 0.04
    mb = MB()
    amp = 0.035
    nw = max(3, int(w / 0.11))

    def f(u, v):
        x = -w / 2 + u * w
        y = amp * math.sin(u * nw * 2 * math.pi) * (0.8 + 0.2 * v) + 0.01
        z = 0.012 + v * (top - 0.05)
        return (x, y, z)
    mb.surf(f, nw * 8, 6, "plotno", smooth=True)
    mb.box(-w / 2 - 0.05, -0.02, top - 0.02, w / 2 + 0.05, 0.04, top + 0.02, "czarny_metal", r=0.004)
    B.mesh(mb, "zaslona")


# ------------------------------------------------------------------ pokój dziecięcy
def _regal_niski(B):
    it, r = B.it, B.rnd
    w, d, h = it.w, it.d, it.h
    mb = MB()
    t = 0.022
    ncol = max(2, int(round(w / 0.33)))
    cw = (w - t * (ncol + 1)) / ncol
    mb.box(-w / 2, -d / 2, 0.0, w / 2, d / 2, 0.06, "lak_bialy", r=0.002)
    for z in (0.06, h / 2, h - t):
        mb.box(-w / 2, -d / 2, z, w / 2, d / 2, z + t, "lak_bialy", r=0.002)
    for k in range(ncol + 1):
        x = -w / 2 + k * (cw + t)
        mb.box(x, -d / 2, 0.0, x + t, d / 2, h, "lak_bialy", r=0.002)
    toys = MB()
    for k in range(ncol):
        x0 = -w / 2 + t + k * (cw + t)
        # dolna półka: kosze z filcu, górna: książeczki i zabawki
        toys.rbox(x0 + 0.015, -d / 2 + 0.03, 0.06 + t, x0 + cw - 0.015, d / 2 - 0.02, h / 2 - 0.02, KOLORY_DZ[k % 4],
                  rc=0.02, r=0.006)
        if k % 2 == 0:
            _fill_books(toys, r, x0, x0 + cw, h / 2 + t, h / 2 - 2 * t, d, 0.7)
        else:
            for j in range(3):
                toys.box(x0 + 0.03 + j * 0.07, -0.05, h / 2 + t, x0 + 0.09 + j * 0.07, 0.01, h / 2 + t + 0.06,
                         KOLORY_DZ[(j + k) % 4], r=0.006)
    # na blacie: klocki i piłka
    for j in range(4):
        toys.box(-w / 2 + 0.1 + j * 0.065, -0.04, h, -w / 2 + 0.155 + j * 0.065, 0.015, h + 0.055 * (1 + j % 2),
                 KOLORY_DZ[j % 4], r=0.006)
    toys.sphere(w / 2 - 0.15, 0.0, h + 0.1, 0.1, "tk_akcent0", n=20)
    B.mesh(mb, "regal_niski")
    B.mesh(toys, "zabawki")


def _namiot(B):
    """Namiot do zabawy: dwie skośne płachty na drewnianym stelażu A, mata i poduchy w środku."""
    it = B.it
    s = it.w
    hgt = 1.35
    mb = MB()
    half = s / 2
    # płachty: od kalenicy (v=0) do podłogi (v=1), lekko wybrzuszone
    for sx in (-1, 1):
        mb.surf(lambda u, v, sx=sx: (sx * (half * v + 0.03 * math.sin(math.pi * v)), -half + u * s, hgt * (1 - v)), 6, 8,
                "plotno" if sx < 0 else "tk_akcent1")
    for sy in (-half, half):
        for sx in (-1, 1):
            mb.tube([(sx * (half + 0.04), sy, 0.0), (-sx * 0.06, sy, hgt + 0.12)], 0.016, "buk", n=8)
    mb.tube([(0, -half - 0.08, hgt + 0.02), (0, half + 0.08, hgt + 0.02)], 0.015, "buk", n=8)
    mb.box(-half + 0.08, -half + 0.05, 0.0, half - 0.08, half - 0.05, 0.03, "tk_akcent2", r=0.01)
    mb.soft(0.2, 0.2, 0.07, "tk_akcent0", M=T(-0.15, 0.15, 0.1), e1=0.3, e2=0.3, nu=20, nv=8)
    mb.soft(0.18, 0.18, 0.06, "tk_kolor", M=T(0.18, 0.05, 0.09), e1=0.3, e2=0.3, nu=20, nv=8)
    B.mesh(mb, "namiot")


def _pufa(B):
    it = B.it
    rr = it.w / 2
    mb = MB()
    mb.soft(rr, rr, 0.3, "tk_akcent1" if B.rk == "pokoj" else "boucle", M=T(0, 0, 0.3), e1=0.55, e2=0.9, nu=36, nv=16,
            puff=0.04, wr=0.01, seed=3)
    B.mesh(mb, "pufa")


# ------------------------------------------------------------------ lampa stojąca
def _lampa(B):
    mb = MB()
    mb.cyl(0, 0, 0.0, 0.02, 0.15, "czarny_metal", n=32, r=0.004)
    mb.cyl(0, 0, 0.02, 1.38, 0.012, "czarny_metal", n=12)
    mb.lathe([(0.0, 1.62), (0.07, 1.62), (0.21, 1.36), (0.215, 1.355), (0.205, 1.355), (0.065, 1.61), (0.0, 1.61)],
             "abazur", n=40)
    mb.sphere(0, 0, 1.45, 0.04, "zarowka", n=12)
    B.mesh(mb, "lampa")
    B.light((0, 0, 1.45), 40.0, size=0.08, name="lampa_stojaca")


# ------------------------------------------------------------------ patio: kuchnia ogrodowa z grillem
def _grill(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    mb = MB()
    zt = 0.9
    mb.box(-w / 2, -d / 2 + 0.03, 0.0, w / 2, d / 2, zt - 0.04, "beton_ciemny", r=0.01)
    mb.box(-w / 2 - 0.02, -d / 2 - 0.02, zt - 0.04, w / 2 + 0.02, d / 2 + 0.01, zt, "ciemny", r=0.004)
    # drzwiczki i szuflady ze stali
    for x0, x1 in ((-w / 2 + 0.08, -0.45), (0.45, w / 2 - 0.08)):
        mb.box(x0, -d / 2 + 0.01, 0.12, x1, -d / 2 + 0.035, zt - 0.12, "stal", r=0.003)
        mb.box((x0 + x1) / 2 - 0.15, -d / 2 - 0.02, zt - 0.2, (x0 + x1) / 2 + 0.15, -d / 2 + 0.01, zt - 0.185, "stal", r=0.004)
    # grill gazowy: korpus, pokrywa, uchwyt, pokrętła
    gw = 0.86
    mb.box(-gw / 2, -d / 2 + 0.03, 0.12, gw / 2, d / 2 - 0.05, zt - 0.01, "stal", r=0.004)
    for k in range(4):
        mb.cyl(-0.27 + k * 0.18, -d / 2 + 0.01, 0.62, 0.66, 0.025, "czarny_metal", n=16)
    lid = mb.prism([(-gw / 2, -d / 2 + 0.06), (gw / 2, -d / 2 + 0.06), (gw / 2, d / 2 - 0.06), (-gw / 2, d / 2 - 0.06)],
                   zt, zt + 0.28, "stal", r=0.01,
                   top=[(-gw / 2 + 0.03, -d / 2 + 0.2), (gw / 2 - 0.03, -d / 2 + 0.2), (gw / 2 - 0.03, d / 2 - 0.08),
                        (-gw / 2 + 0.03, d / 2 - 0.08)])
    mb.tube([(-0.3, -d / 2 + 0.05, zt + 0.12), (-0.3, -d / 2 - 0.02, zt + 0.14), (0.3, -d / 2 - 0.02, zt + 0.14),
             (0.3, -d / 2 + 0.05, zt + 0.12)], 0.012, "stal", n=10)
    # na blacie: deska, przyprawy, szczypce
    mb.box(0.55, -0.12, zt, 0.95, 0.12, zt + 0.025, "drewno_z", r=0.004)
    for k in range(3):
        mb.cyl(-0.9 + k * 0.08, 0.15, zt, zt + 0.12 + 0.02 * k, 0.025, "szklo_butelka" if k == 1 else "ceramika", n=16)
    B.mesh(mb, "grill")


# ------------------------------------------------------------------ kino domowe
def _fotele_kino(B):
    it = B.it
    w, d = it.w, it.d
    n = max(1, int(round((w - 0.16) / 0.82)))
    mb = MB()
    sw = 0.82
    x0 = -w / 2 + 0.08
    for k in range(n + 1):
        x = x0 + k * sw
        # podłokietniki z uchwytem na kubek
        mb.rbox(x - 0.08, -d / 2 + 0.08, 0.0, x + 0.08, d / 2, 0.62, "skora", rc=0.03, r=0.012)
        mb.cyl(x, -d / 2 + 0.22, 0.58, 0.625, 0.04, "czarny_mat", n=20)
    for k in range(n):
        x = x0 + (k + 0.5) * sw
        mb.rbox(x - 0.33, -d / 2 + 0.05, 0.0, x + 0.33, d / 2 - 0.12, 0.42, "skora", rc=0.04, r=0.02, seg=3)  # podstawa
        mb.soft(0.31, 0.3, 0.07, "skora", M=T(x, -0.02, 0.47), e1=0.25, e2=0.12, nu=28, nv=10, puff=0.015)       # siedzisko
        mb.soft(0.31, 0.11, 0.36, "skora", M=T(x, d / 2 - 0.13, 0.82) @ R("X", -12), e1=0.25, e2=0.15, nu=28, nv=12)  # oparcie
        mb.soft(0.27, 0.05, 0.09, "skora", M=T(x, d / 2 - 0.18, 1.06) @ R("X", -12), e1=0.4, e2=0.3, nu=24, nv=8)     # zagłówek
    B.mesh(mb, "fotele_kino")
    B.light(None, 6.0 * n, kind="AREA", M=T(0, -d / 2 + 0.03, 0.03), area=(w - 0.1, 0.02), temp=4000.0, name="led_fotele")


def _glosnik(B):
    it = B.it
    w, d, h = it.w, it.d, it.h
    mb = MB()
    mb.box(-w / 2, -d / 2, 0.06, w / 2, d / 2, h, "lak_czarny", r=0.01)
    mb.box(-w / 2 + 0.02, -d / 2 + 0.02, 0.0, w / 2 - 0.02, d / 2 - 0.02, 0.06, "czarny_mat", r=0.004)
    for zz, rr in ((h - 0.12, 0.025), (h - 0.3, 0.075), (h - 0.52, 0.075), (0.35, 0.09)):
        drv = mb.cyl(0, 0, 0, 0.012, rr, "czarny_mat", n=28)
        mb.xf(drv, T(0, -d / 2, zz) @ R("X", 90))
        ring = mb.torus(0, 0, 0, rr, 0.006, "aluminium", nu=28, nv=6)
        mb.xf(ring, T(0, -d / 2 - 0.003, zz) @ R("X", 90))
    B.mesh(mb, "glosnik")


def _projektor(B):
    mb = MB()
    ceil = B.ceil or 2.7
    z = ceil - 0.4
    mb.box(-0.2, -0.16, z, 0.2, 0.16, z + 0.14, "lak_bialy", r=0.015)
    lens = mb.cyl(0, 0, 0, 0.04, 0.045, "szklo_czarne", n=24)
    mb.xf(lens, T(0.08, -0.16, z + 0.07) @ R("X", 90))
    mb.cyl(0, 0.0, z + 0.14, ceil, 0.02, "czarny_metal", n=12)
    mb.cyl(0, 0.0, ceil - 0.01, ceil, 0.07, "czarny_metal", n=20)
    B.mesh(mb, "projektor")


# ------------------------------------------------------------------ hol: ławka z wieszakiem
def _wieszak(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    mb = MB()
    _ns(mb, -w / 2, -d / 2, w / 2, d / 2, 0.42, "drewno", drawers=1, handle=None, legs=False)
    mb.soft(w / 2 - 0.04, d / 2 - 0.04, 0.035, "tk_akcent2", M=T(0, 0.0, 0.46), e1=0.2, e2=0.1, nu=32, nv=8)
    # listwa z haczykami i płaszcze
    yb = d / 2
    mb.box(-w / 2, yb - 0.025, 1.68, w / 2, yb, 1.78, "drewno", r=0.004)
    cols = ("tk_ciemna", "tk_akcent0", "koc", "tk_obicie")
    nh = max(3, int(w / 0.3))
    for k in range(nh):
        x = -w / 2 + (k + 0.5) * w / nh
        mb.tube([(x, yb - 0.02, 1.73), (x, yb - 0.08, 1.72), (x, yb - 0.09, 1.66)], 0.008, "czarny_metal", n=8)
        if k % 2 == 0:
            mb.soft(0.2, 0.07, 0.42, cols[(k // 2) % len(cols)], M=T(x, yb - 0.1, 1.24), e1=0.6, e2=0.4, nu=20, nv=10,
                    wr=0.01, seed=k)
    B.mesh(mb, "wieszak")


# ------------------------------------------------------------------ sofa o prostej, kanciastej bryle
def _sofa_prosta(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    out = B.outdoor
    fab = "tk_ogrod" if out else "tk_sofa"
    mb = MB()
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(sx * (w / 2 - 0.08) - 0.02, sy * (d / 2 - 0.08) - 0.02, 0.0, sx * (w / 2 - 0.08) + 0.02,
                   sy * (d / 2 - 0.08) + 0.02, 0.09, "czarny_metal" if not out else "tik", r=0.004)
    mb.box(-w / 2, -d / 2, 0.09, w / 2, d / 2, 0.30, fab, r=0.02, seg=3)                      # rama
    aw = 0.17
    for sx in (-1, 1):                                                                   # boki
        mb.box(sx * w / 2 - (aw if sx > 0 else 0), -d / 2, 0.09, sx * w / 2 + (aw if sx < 0 else 0), d / 2, 0.62, fab,
               r=0.03, seg=3)
    mb.box(-w / 2 + aw, d / 2 - 0.16, 0.30, w / 2 - aw, d / 2, 0.66, fab, r=0.03, seg=3)      # oparcie
    n = max(1, int(round((w - 2 * aw) / 0.78)))
    cw = (w - 2 * aw) / n
    for k in range(n):
        x = -w / 2 + aw + (k + 0.5) * cw
        mb.soft(cw / 2 - 0.008, (d - 0.2) / 2 - 0.01, 0.075, fab, M=T(x, -0.08, 0.38), e1=0.18, e2=0.08, nu=28, nv=10,
                puff=0.01, wr=0.004, seed=k)                                              # siedziska
        mb.soft(cw / 2 - 0.02, 0.09, 0.2, fab, M=T(x, d / 2 - 0.22, 0.68) @ R("X", -10), e1=0.25, e2=0.12, nu=28, nv=10,
                puff=0.012, wr=0.004, seed=k + 5)                                         # poduchy oparcia
    for k, (px, key) in enumerate(((-w / 2 + aw + 0.28, "tk_akcent0"), (w / 2 - aw - 0.3, "tk_akcent1"),
                                    (-w / 2 + aw + 0.6, "tk_akcent2"))):
        if k == 2 and w < 2.3:
            continue
        mb.pillow(0.44, 0.44, 0.14, key, T(px, d / 2 - 0.34, 0.66) @ R("Z", r.uniform(-8, 8)) @ R("X", 70.0), seed=k * 3)
    B.mesh(mb, "sofa")


BUILDERS = {
    "zabudowa": _zabudowa, "komoda": _komoda, "obraz": _obraz, "lustro": _lustro, "zaslona": _zaslona,
    "regal_niski": _regal_niski, "namiot": _namiot, "pufa": _pufa, "lampa": _lampa, "grill": _grill,
    "fotele_kino": _fotele_kino, "glosnik": _glosnik, "projektor": _projektor, "wieszak": _wieszak,
    "sofa_prosta": _sofa_prosta,
}
