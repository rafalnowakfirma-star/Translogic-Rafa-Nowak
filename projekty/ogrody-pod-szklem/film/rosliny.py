"""Roślinność do filmów (Blender 5.1, Cycles): drzewa, krzewy i rośliny ogrodowe.

API (współrzędne Blendera, już przeliczone):
  tree(kind, X, Y, Z, h, r, seed, ctx, lod="blisko")   – drzewo o wysokości h i promieniu korony r
  plant(kind, X, Y, Z, r, seed, ctx, rot=0.0)          – mała roślina / kamień (rot – obrót wokół Z, radiany)
  treeline(cx, cy, r_in, r_out, n, seed, ctx, exclude=None) – pierścień drzew w tle
  lawn_tufts(poly_xy, density, seed, ctx, z=0.0, height=0.12) – kępki trawy 3D (instancje)

Drzewa: szkielet rośnie warstwami (pień → konary → gałęzie → gałązki) z tropizmami i obwiednią korony,
grubość z modelu rurek (da Vinci), liście to karty z kanałem alfa (tekstury z PIL w zasoby/generowane/).
Każdy (gatunek, lod, pora roku, przedział rozmiaru, wariant) budujemy raz (ctx.cache) i stawiamy kopie dzielące siatkę.
"""
import math
import os
import random
import subprocess
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(HERE, "zasoby", "generowane")
TEX_VER = 2


def _tex_path(name):
    return os.path.join(GEN, f"{name}_v{TEX_VER}.png")


# =====================================================================================================
#  TEKSTURY (PIL) – liczone raz, zapisywane w zasoby/generowane/.  W Blenderze bez PIL → podproces python3.
# =====================================================================================================

# atlasy: nazwa → (kolumny, wiersze, piksele komórki w, h).  Komórka: nasada liścia w środku dolnej krawędzi.
ATLAS = {
    "liscie_klon": (2, 2, 512, 512),
    "liscie_klon_zielony": (2, 2, 512, 512),
    "liscie_brzoza": (2, 2, 384, 512),
    "liscie_lipa": (2, 2, 512, 512),
    "liscie_oliwka": (4, 1, 160, 512),
    "liscie_cytrus": (2, 2, 288, 512),
    "liscie_bukszpan": (2, 2, 320, 512),
    "liscie_bambus": (4, 1, 128, 512),
    "spray_klon": (2, 1, 512, 640),
    "spray_klon_zielony": (2, 1, 512, 640),
    "spray_brzoza": (2, 1, 512, 640),
    "spray_lipa": (2, 1, 512, 640),
    "spray_oliwka": (2, 1, 448, 640),
    "spray_cytrus": (2, 1, 512, 640),
    "spray_bukszpan": (2, 1, 512, 640),
    "spray_bambus": (2, 1, 512, 640),
    "kepa_klon": (2, 1, 512, 512),
    "kepa_klon_zielony": (2, 1, 512, 512),
    "kepa_brzoza": (2, 1, 512, 512),
    "kepa_lipa": (2, 1, 512, 512),
    "kepa_oliwka": (2, 1, 512, 512),
    "igly": (2, 2, 512, 512),
    "galazki": (2, 1, 512, 512),
    "paproc": (2, 1, 320, 768),
    "monstera": (2, 1, 640, 640),
    "lawenda": (2, 1, 128, 512),
    "lawenda_lisc": (1, 1, 512, 512),
    "lilia": (1, 1, 512, 512),
}

# kolory liści (sRGB 0–255): wierzch, nerw, końcówki, rozrzut
LEAF_COL = {
    "klon": ((150, 30, 24), (176, 66, 42), (192, 66, 30), 0.10),
    "klon_zielony": ((78, 110, 38), (112, 140, 64), (92, 120, 40), 0.08),
    "brzoza": ((108, 140, 48), (140, 166, 82), (120, 148, 50), 0.08),
    "lipa": ((70, 104, 34), (104, 132, 60), (80, 110, 36), 0.08),
    "oliwka": ((100, 110, 76), (136, 142, 108), (106, 116, 80), 0.06),
    "cytrus": ((40, 76, 26), (88, 116, 50), (46, 82, 28), 0.07),
    "bukszpan": ((58, 94, 30), (90, 118, 50), (68, 102, 34), 0.08),
    "bambus": ((78, 114, 38), (110, 142, 64), (92, 122, 42), 0.08),
}


def _pil():
    from PIL import Image, ImageDraw, ImageFilter
    return Image, ImageDraw, ImageFilter


def _noise(rng, w, h, cells, octaves=3):
    """Gładki szum wartości 0..1 (kilka oktaw, skalowanie dwusześcienne)."""
    Image, _, _ = _pil()
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        c = max(2, int(cells * 2 ** o))
        small = Image.fromarray(rng.random((c, c)).astype(np.float32), "F")
        out += amp * np.asarray(small.resize((w, h), Image.BICUBIC), np.float32)
        tot += amp
        amp *= 0.5
    return np.clip(out / tot, 0, 1)


def _serrate(pts, period, amp):
    """Ząbkowanie brzegu: przesunięcie punktów obrysu wzdłuż normalnej piłą o okresie `period`."""
    d = np.roll(pts, -1, 0) - np.roll(pts, 1, 0)
    n = np.stack([d[:, 1], -d[:, 0]], 1)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    seg = np.linalg.norm(np.diff(pts, axis=0, append=pts[:1]), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)[:-1]])
    saw = (s / period) % 1.0
    return pts + n * (amp * (saw ** 1.6 - 0.45))[:, None]


def _polar(c, phi, r, sx=1.0):
    return np.stack([c[0] + sx * r * np.sin(phi), c[1] + r * np.cos(phi)], 1)


def _outline(sp, rng):
    """Obrys blaszki w jednostkach liścia (nasada ogonka (0,0), czubek ~(0,1)).
    Zwraca (punkty obrysu, środek blaszki, nerwy jako listy punktów)."""
    j = lambda s: 1.0 + rng.uniform(-s, s)
    veins = []
    phi = np.linspace(-math.pi, math.pi, 1400, endpoint=False)
    if sp in ("klon", "klon_zielony"):
        # liść dłoniasty: płaty jako szczyty funkcji biegunowej wokół nasady blaszki
        if sp == "klon":
            c = (0.0, 0.30)
            lobes = [(0, 0.66), (31, 0.62), (62, 0.52), (96, 0.34)]
            w, p, q, rmin = 0.44, 2.2, 2.8, 0.07
        else:
            c = (0.0, 0.27)
            lobes = [(0, 0.60), (54, 0.58), (108, 0.38)]
            w, p, q, rmin = 0.62, 1.8, 1.5, 0.16
        r = np.full_like(phi, rmin)
        for ang, L in lobes:
            for sgn in ((1,) if ang == 0 else (1, -1)):
                th = math.radians(ang) * sgn + rng.uniform(-0.04, 0.04)
                LL = L * j(0.05)
                u = np.abs(np.angle(np.exp(1j * (phi - th)))) / w
                g = np.where(u < 1, (1 - np.clip(u, 0, 1) ** p) ** q, 0)
                if sp == "klon_zielony":   # duże boczne zęby płata
                    for off in (0.42, -0.42):
                        u2 = np.abs(np.angle(np.exp(1j * (phi - th - off * w)))) / (w * 0.22)
                        g = np.maximum(g, np.where(u2 < 1, 0.74 * (1 - np.clip(u2, 0, 1) ** 1.3) ** 1.2, 0))
                r = np.maximum(r, LL * g)
                veins.append([(c[0], c[1]), (c[0] + math.sin(th) * LL * 0.92, c[1] + math.cos(th) * LL * 0.92)])
        pts = _polar(c, phi, r)
        pts = _serrate(pts, 0.022 if sp == "klon" else 0.05, 0.010 if sp == "klon" else 0.012)
        return pts, c, veins
    if sp == "lipa":
        c = (0.0, 0.24)
        r = 0.40 * (1 + np.cos(phi)) ** 0.85 + 0.035
        r *= 1 + 0.30 * np.exp(-(phi / 0.12) ** 2)          # zaostrzony czubek
        r *= np.where(phi < 0, 0.93, 1.0)                    # asymetria nasady
        pts = _serrate(_polar(c, phi, r, 1.08), 0.03, 0.012)
        for a in (-0.9, -0.45, 0.45, 0.9):
            L = 0.55 - abs(a) * 0.15
            veins.append([c, (c[0] + math.sin(a) * L, c[1] + math.cos(a) * L)])
        veins.insert(0, [c, (0.0, c[1] + 0.86)])
        for t in (0.25, 0.45, 0.62):
            y = c[1] + t * 0.8
            for s_ in (1, -1):
                veins.append([(0, y), (s_ * 0.28 * (1 - t * 0.6), y + 0.18)])
        return pts, c, veins
    # liście pierzastonerwowe: połowa szerokości w(t) wzdłuż blaszki
    spec = {
        "brzoza": (0.26, 0.29, lambda t: (np.sin(math.pi * t ** 0.62)) ** 0.85 * (1 - 0.1 * t), 0.035, 0.012),
        "oliwka": (0.05, 0.105, lambda t: (np.sin(math.pi * t ** 0.95)) ** 0.75, 0, 0.0),
        "cytrus": (0.10, 0.235, lambda t: (np.sin(math.pi * t ** 0.88)) ** 0.62, 0, 0.0),
        "bukszpan": (0.04, 0.27, lambda t: (np.sin(math.pi * t ** 0.92)) ** 0.55, 0, 0.0),
        "bambus": (0.05, 0.085, lambda t: (np.sin(math.pi * t ** 0.55)) ** 0.7, 0, 0.0),
    }[sp]
    p0, W, fw, per, amp = spec
    W *= j(0.06)
    t = np.linspace(0, 1, 500)
    w = W * fw(t)
    bend = rng.uniform(-0.03, 0.03) if sp in ("oliwka", "bambus") else rng.uniform(-0.01, 0.01)
    y = p0 + t * (0.99 - p0)
    xm = bend * np.sin(math.pi * t)
    right = np.stack([xm + w, y], 1)
    left = np.stack([xm - w, y], 1)[::-1]
    pts = np.concatenate([right, left[1:-1]], 0)
    if per:
        pts = _serrate(pts, per, amp)
    c = (0.0, p0)
    veins.append([(float(xm[k]), float(y[k])) for k in range(0, 500, 25)] + [(float(xm[-1]), float(y[-1]))])
    nsec = {"brzoza": 8, "oliwka": 0, "cytrus": 9, "bukszpan": 0, "bambus": 0}[sp]
    for k in range(1, nsec + 1):
        tt = k / (nsec + 1.5)
        i = int(tt * 499)
        for s_ in (1, -1):
            i2 = min(499, int((tt + 0.12) * 499))
            veins.append([(float(xm[i]), float(y[i])), (float(xm[i2] + s_ * w[i2] * 0.92), float(y[i2]))])
    return pts, c, veins


def _leaf_rgba(sp, rng, W, H, scale=1.0, col=None):
    """Pojedynczy liść w komórce W×H (nasada w środku dołu). Zwraca tablice RGB (float 0..1) i alfa."""
    Image, ImageDraw, ImageFilter = _pil()
    S = 2  # nadpróbkowanie
    w2, h2 = W * S, H * S
    pts, c, veins = _outline(sp, rng)
    base, vein, tipc, var = col or LEAF_COL[sp]
    # dopasowanie do komórki: skala wspólna, nasada w (w2/2, h2-1)
    sx = h2 * 0.97 * scale
    maxx = np.abs(pts[:, 0]).max()
    if maxx * sx > w2 * 0.48:
        sx = w2 * 0.48 / maxx
    P = lambda x, y: (w2 / 2 + x * sx, h2 - 1 - y * sx)
    m = Image.new("L", (w2, h2), 0)
    d = ImageDraw.Draw(m)
    d.polygon([P(x, y) for x, y in pts], fill=255)
    # ogonek
    d.line([P(0, 0), P(c[0], c[1])], fill=255, width=max(2, int(sx * 0.018)))
    vm = Image.new("L", (w2, h2), 0)
    dv = ImageDraw.Draw(vm)
    for k, vn in enumerate(veins):
        wv = max(1, int(sx * (0.012 if k == 0 or sp.startswith("klon") else 0.006)))
        dv.line([P(x, y) for x, y in vn], fill=255 if k == 0 else 170, width=wv)
    vm = vm.filter(ImageFilter.GaussianBlur(S * 0.8))
    a = np.asarray(m, np.float32) / 255
    v = np.asarray(vm, np.float32) / 255
    # odległość od nasady blaszki → przejście kolorów ku końcówkom
    yy, xx = np.mgrid[0:h2, 0:w2].astype(np.float32)
    cx, cy = P(c[0], c[1])
    dist = np.hypot(xx - cx, yy - cy) / (sx * 0.75)
    n1 = _noise(rng, w2, h2, 3, 3)
    n2 = _noise(rng, w2, h2, 18, 2)
    b = np.array(base, np.float32) / 255
    tc = np.array(tipc, np.float32) / 255
    vc = np.array(vein, np.float32) / 255
    k = np.clip(dist, 0, 1)[..., None] ** 1.5
    rgb = b * (1 - k) + tc * k
    rgb = rgb * (1 + var * 2.0 * (n1[..., None] - 0.5) + 0.06 * (n2[..., None] - 0.5))
    rgb = rgb * (1 - v[..., None] * 0.55) + vc * v[..., None] * 0.55
    # brzeg odrobinę ciemniejszy (grubość blaszki)
    edge = np.asarray(m.filter(ImageFilter.GaussianBlur(S * 1.5)), np.float32) / 255
    rgb = rgb * (0.9 + 0.1 * np.clip((edge - 0.5) * 2, 0, 1))[..., None]
    return np.clip(rgb, 0, 1), a


def _down(rgb, a, W, H):
    """Zmniejszenie z nadpróbkowania, tło wypełnione średnim kolorem (bez obwódek przy filtrowaniu)."""
    Image, _, _ = _pil()
    m = a > 0.02
    mean = rgb[m].mean(0) if m.any() else np.array([0.2, 0.3, 0.1])
    rgb = np.where(a[..., None] > 0.02, rgb, mean)
    im = Image.fromarray((rgb * 255).astype(np.uint8), "RGB").resize((W, H), Image.LANCZOS)
    al = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L").resize((W, H), Image.LANCZOS)
    im.putalpha(al)
    return im


def _paste(canvas, leaf, x, y, ang, sc, squash=1.0, tint=1.0):
    """Wkleja obraz liścia (nasada w środku dołu) obrócony o ang (rad, 0 = w górę) w punkt (x, y) płótna."""
    Image, _, _ = _pil()
    lw, lh = leaf.size
    w2, h2 = max(2, int(lw * sc * squash)), max(2, int(lh * sc))
    im = leaf.resize((w2, h2), Image.BICUBIC)
    if tint != 1.0:
        r, g, b, al = im.split()
        r = r.point(lambda q: min(255, int(q * tint)))
        g = g.point(lambda q: min(255, int(q * tint)))
        b = b.point(lambda q: min(255, int(q * tint)))
        im = Image.merge("RGBA", (r, g, b, al))
    # obrót wokół nasady: powiększone płótno z nasadą w środku
    big = Image.new("RGBA", (h2 * 2 + 4, h2 * 2 + 4), (0, 0, 0, 0))
    big.paste(im, (h2 + 2 - w2 // 2, 2))
    big = big.rotate(-math.degrees(ang), resample=Image.BICUBIC, center=(h2 + 2, h2 + 2))
    canvas.alpha_composite(big, (int(x - h2 - 2), int(y - h2 - 2)))


def _cell_canvas(W, H):
    Image, _, _ = _pil()
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def _twig_line(d, pts, col, w0, w1):
    n = len(pts) - 1
    for i in range(n):
        wi = w0 + (w1 - w0) * i / max(1, n)
        d.line([pts[i], pts[i + 1]], fill=col, width=max(1, int(round(wi))))


def _spray(sp, rng, W, H, nleaf, leaf_imgs, twig_col=(92, 70, 50)):
    """Gałązka z kilkoma liśćmi (karta „spray”) – nasada gałązki w środku dołu."""
    Image, ImageDraw, _ = _pil()
    cv = _cell_canvas(W, H)
    d = ImageDraw.Draw(cv)
    L = H * 0.62
    bend = rng.uniform(-0.15, 0.15)
    pts = [(W / 2 + bend * W * 0.2 * math.sin(math.pi * t) , H - 1 - t * L) for t in np.linspace(0, 1, 12)]
    _twig_line(d, pts, twig_col + (255,), max(2, W * 0.012), max(1, W * 0.005))
    lw = leaf_imgs[0].size[1]
    for i in range(nleaf):
        t = 0.25 + 0.75 * (i + 0.5) / nleaf if nleaf > 1 else 1.0
        k = min(11, int(t * 11))
        x, y = pts[k]
        side = 1 if i % 2 else -1
        ang = side * rng.uniform(0.45, 0.95) * (1.1 - 0.5 * t)
        if i == nleaf - 1:
            ang = rng.uniform(-0.15, 0.15)
        sc = (H * {'oliwka': 0.42, 'bambus': 0.45, 'cytrus': 0.36, 'bukszpan': 0.26, 'brzoza': 0.36}.get(sp, 0.30)) / lw * rng.uniform(0.75, 1.0) * (0.85 + 0.15 * t)
        _paste(cv, leaf_imgs[rng.integers(len(leaf_imgs))], x, y, ang, sc, rng.uniform(0.75, 1.0), rng.uniform(0.82, 1.1))
    return cv


def _cluster(sp, rng, W, H, leaf_imgs, nleaf=34, twig_col=(80, 64, 50), leaf_frac=0.2):
    """Kępa liści na rozgałęzionej gałązce (karty dalekiego planu)."""
    Image, ImageDraw, _ = _pil()
    cv = _cell_canvas(W, H)
    d = ImageDraw.Draw(cv)
    tips = []

    def br(x, y, ang, L, wd, depth):
        n = 6
        pts = [(x, y)]
        for i in range(n):
            ang += rng.uniform(-0.12, 0.12)
            x += math.sin(ang) * L / n
            y -= math.cos(ang) * L / n
            pts.append((x, y))
        _twig_line(d, pts, twig_col + (255,), wd, wd * 0.6)
        tips.extend(pts[2:])
        if depth > 0:
            for k in range(3):
                t = 0.3 + 0.22 * k
                px, py = pts[int(t * n)]
                br(px, py, ang + (1 if k % 2 else -1) * rng.uniform(0.5, 0.9), L * rng.uniform(0.45, 0.6), wd * 0.6, depth - 1)

    br(W / 2, H - 1, rng.uniform(-0.1, 0.1), H * 0.6, max(2, W * 0.012), 3)
    lw = leaf_imgs[0].size[1]
    order = rng.permutation(len(tips))
    for i in range(nleaf):
        x, y = tips[order[i % len(tips)]]
        x += rng.normal(0, W * 0.02)
        y += rng.normal(0, W * 0.02)
        ang = rng.uniform(-math.pi, math.pi) * 0.75
        sc = (H * leaf_frac) / lw * rng.uniform(0.7, 1.05)
        _paste(cv, leaf_imgs[rng.integers(len(leaf_imgs))], x, y, ang, sc, rng.uniform(0.45, 1.0), rng.uniform(0.7, 1.12))
    return cv


def _needles(rng, W, H, kind):
    """Pęczki igieł sosny: 0 – pęd z boku, 1 – rozeta z góry, 2 – gałązka z pędami, 3 – duża kępa."""
    Image, ImageDraw, ImageFilter = _pil()
    S = 2
    cv = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    base = np.array((52, 84, 48), np.float32)

    def ncol(front, t):
        k = rng.uniform(0.75, 1.2) * (1.12 if front else 0.78) * (0.85 + 0.3 * t)
        c = np.clip(base * k + np.array((6, 8, 10)) * rng.uniform(-1, 1), 0, 255)
        return tuple(int(q) for q in c) + (255,)

    def shoot(x0, y0, ang, L, nn=110, spread=1.0, radial=False):
        # pęd: oś z igłami w parach skierowanymi ku czubkowi
        ax, ay = math.sin(ang), -math.cos(ang)
        if not radial:
            d.line([(x0, y0), (x0 + ax * L * 0.7, y0 + ay * L * 0.7)], fill=(96, 70, 48, 255), width=max(2, int(W * S * 0.008)))
        items = []
        for i in range(nn):
            t = rng.uniform(0.0, 0.75) if not radial else 0.0
            psi = rng.uniform(0, 2 * math.pi)
            if radial:
                a = psi
                ln = L * rng.uniform(0.7, 1.0)
                sx, sy = x0 + math.cos(a) * L * 0.05, y0 + math.sin(a) * L * 0.05
                ex, ey = sx + math.cos(a) * ln, sy + math.sin(a) * ln
                items.append((1.0, (sx, sy, ex, ey), True, 0.5))
                continue
            alpha = rng.uniform(0.45, 0.95) * spread
            ln = L * rng.uniform(0.38, 0.52) * (1.0 - 0.3 * t)
            sx, sy = x0 + ax * L * 0.7 * t, y0 + ay * L * 0.7 * t
            lat = math.sin(alpha) * math.cos(psi)
            fwd = math.cos(alpha)
            dx = ax * fwd + (-ay) * lat
            dy = ay * fwd + ax * lat
            items.append((math.sin(psi), (sx, sy, sx + dx * ln, sy + dy * ln), math.sin(psi) > 0, t))
        items.sort(key=lambda q: q[0])
        for _, (sx, sy, ex, ey), front, t in items:
            mx, my = (sx + ex) / 2 + rng.normal(0, 1.5), (sy + ey) / 2 + rng.normal(0, 1.5)
            d.line([(sx, sy), (mx, my), (ex, ey)], fill=ncol(front, t), width=max(2, int(W * S * 0.0055)))
        # pąk szczytowy
        bx, by = x0 + ax * L * 0.72, y0 + ay * L * 0.72
        rr = W * S * 0.012
        d.ellipse([bx - rr, by - rr * 1.6, bx + rr, by + rr * 1.6], fill=(120, 88, 60, 255))

    Wp, Hp = W * S, H * S
    if kind == 0:
        shoot(Wp / 2, Hp - 2, 0.0, Hp * 0.95)
    elif kind == 1:
        shoot(Wp / 2, Hp / 2, 0.0, Wp * 0.46, nn=160, radial=True)
    elif kind == 2:
        d.line([(Wp / 2, Hp - 2), (Wp / 2, Hp * 0.45)], fill=(100, 72, 50, 255), width=int(Wp * 0.014))
        for k, (y, a) in enumerate(((0.62, -0.75), (0.55, 0.7), (0.47, -0.25), (0.45, 0.3), (0.42, 0.0))):
            shoot(Wp / 2, Hp * y, a, Hp * 0.55, nn=80)
    else:
        for k in range(9):
            a = rng.uniform(-1.1, 1.1)
            shoot(Wp / 2 + rng.normal(0, Wp * 0.08), Hp * rng.uniform(0.55, 0.95), a, Hp * rng.uniform(0.4, 0.55), nn=60)
    rgba = np.asarray(cv, np.float32) / 255
    return _down(rgba[..., :3], rgba[..., 3], W, H)


def _twigs(rng, W, H, birch=False):
    """Drobne bezlistne gałązki (zima) – karta z rozgałęzieniem."""
    Image, ImageDraw, _ = _pil()
    S = 2
    cv = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    col = np.array((70, 52, 44) if birch else (92, 82, 72), np.float32)

    def br(x, y, ang, L, wd, depth):
        n = 5
        pts = [(x, y)]
        for i in range(n):
            ang += rng.uniform(-0.18, 0.18)
            if birch and depth < 3:
                ang += 0.12 * math.copysign(1, ang) if abs(ang) > 0.2 else 0  # zwisające
            x += math.sin(ang) * L / n
            y -= math.cos(ang) * L / n
            pts.append((x, y))
        c = tuple(int(q) for q in np.clip(col * rng.uniform(0.85, 1.15), 0, 255)) + (255,)
        _twig_line(d, pts, c, wd, wd * 0.7)
        if depth > 0:
            nk = 3 if depth > 1 else 2
            for k in range(nk):
                t = 0.25 + 0.7 * (k + rng.uniform(0, 0.6)) / nk
                px, py = pts[min(n, int(t * n))]
                sgn = 1 if (k + depth) % 2 else -1
                br(px, py, ang + sgn * rng.uniform(0.4, 0.85), L * rng.uniform(0.55, 0.72), max(1.0, wd * 0.66), depth - 1)
        else:
            d.ellipse([x - 1.5, y - 1.5, x + 1.5, y + 1.5], fill=c)

    br(W * S / 2, H * S - 2, rng.uniform(-0.1, 0.1), H * S * 0.62, W * S * 0.018, 5)
    rgba = np.asarray(cv, np.float32) / 255
    return _down(rgba[..., :3], rgba[..., 3], W, H)


def _fern(rng, W, H):
    """Liść paproci (podwójnie pierzasty), nasada w środku dołu."""
    Image, ImageDraw, ImageFilter = _pil()
    S = 2
    Wp, Hp = W * S, H * S
    cv = Image.new("RGBA", (Wp, Hp), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    base = np.array((70, 112, 34), np.float32)
    bend = rng.uniform(-0.05, 0.05)
    rach = lambda t: (Wp / 2 + bend * Wp * math.sin(math.pi * t), Hp - 2 - t * (Hp - 6))
    npair = 28
    for i in range(npair):
        t = 0.10 + 0.88 * i / (npair - 1)
        Lp = 0.47 * Wp * (math.sin(math.pi * ((t - 0.06) / 0.96) ** 0.85)) ** 0.9
        x0, y0 = rach(t)
        for s in (1, -1):
            ang = s * (math.radians(68) - 0.25 * t) + rng.uniform(-0.05, 0.05)
            dxp, dyp = math.sin(ang), -math.cos(ang)
            npin = max(3, int(Lp / (Wp * 0.026)))
            for k in range(npin):
                u = (k + 0.5) / npin
                px, py = x0 + dxp * Lp * u, y0 + dyp * Lp * u
                pl = Wp * 0.05 * (1.15 - 0.75 * u) * (0.55 + 0.45 * math.sin(math.pi * min(1, t * 1.15)))
                for s2 in (1, -1):
                    a2 = ang + s2 * 0.95 + 0.25 * (1 if s > 0 else -1)
                    qx, qy = px + math.sin(a2) * pl, py - math.cos(a2) * pl
                    nx, ny = -(qy - py) * 0.42, (qx - px) * 0.42
                    c = base * rng.uniform(0.85, 1.12) * (0.92 + 0.2 * u)
                    d.polygon([(px - nx * 0.4, py - ny * 0.4), ((px + qx) / 2 + nx, (py + qy) / 2 + ny), (qx, qy),
                               ((px + qx) / 2 - nx, (py + qy) / 2 - ny)], fill=tuple(int(q) for q in np.clip(c, 0, 255)) + (255,))
            d.line([(x0, y0), (x0 + dxp * Lp, y0 + dyp * Lp)], fill=(88, 120, 50, 255), width=2)
    pts = [rach(t) for t in np.linspace(0, 1, 30)]
    _twig_line(d, pts, (86, 104, 46, 255), Wp * 0.012, Wp * 0.004)
    rgba = np.asarray(cv, np.float32) / 255
    return _down(rgba[..., :3], rgba[..., 3], W, H)


def _monstera(rng, W, H):
    """Liść monstery: sercowaty z wcięciami od brzegu i otworami przy nerwie głównym."""
    Image, ImageDraw, ImageFilter = _pil()
    S = 2
    Wp, Hp = W * S, H * S
    phi = np.linspace(-math.pi, math.pi, 900, endpoint=False)
    c = (0.0, 0.17)
    r = 0.42 * (1 + np.cos(phi)) ** 0.78 + 0.06
    r *= (1 + 0.12 * np.exp(-(phi / 0.2) ** 2)) * (1 + 0.04 * np.cos(2 * phi))
    pts = _polar(c, phi, r, 0.8)
    tipy = c[1] + r[450]
    y0 = pts[:, 1].min()
    sc = min((Hp - 6) / (pts[:, 1].max() - min(0.0, y0) + 0.01), (Wp * 0.48) / np.abs(pts[:, 0]).max())
    P = lambda x, y: (Wp / 2 + x * sc, Hp - 3 - (y - min(0.0, y0)) * sc)
    m = Image.new("L", (Wp, Hp), 0)
    d = ImageDraw.Draw(m)
    d.polygon([P(x, y) for x, y in pts], fill=255)
    vm = Image.new("L", (Wp, Hp), 0)
    dv = ImageDraw.Draw(vm)
    dv.line([P(*c), P(0, tipy)], fill=255, width=max(2, int(sc * 0.016)))
    nv = 8
    for s_ in (1, -1):
        for k in range(nv):
            t = 0.06 + 0.86 * k / nv
            y0 = c[1] + (tipy - c[1]) * t
            ang = s_ * (math.radians(70) - 0.55 * t)
            L = 0.75
            dv.line([P(0, y0), P(math.sin(ang) * L, y0 + math.cos(ang) * L)], fill=190, width=max(1, int(sc * 0.007)))
            if 0 < k < nv - 1:
                # wcięcie od brzegu między nerwami
                t2 = t + 0.5 / nv
                y2 = c[1] + (tipy - c[1]) * t2
                a2 = s_ * (math.radians(70) - 0.55 * t2)
                depth = rng.uniform(0.08, 0.2) * (0.6 + 0.6 * t)
                wd = rng.uniform(0.03, 0.05)
                A = (math.sin(a2) * depth, y2 + math.cos(a2) * depth)
                B = (math.sin(a2) * 1.2, y2 + math.cos(a2) * 1.2)
                nx, ny = math.cos(a2) * wd, -math.sin(a2) * wd
                d.polygon([P(*A), P(B[0] + nx, B[1] + ny), P(B[0] - nx, B[1] - ny)], fill=0)
                if rng.random() < 0.6:
                    hd = depth * rng.uniform(0.3, 0.5)
                    hx, hy = math.sin(a2) * hd, y2 + math.cos(a2) * hd
                    hr = rng.uniform(0.014, 0.024)
                    X, Y = P(hx, hy)
                    d.ellipse([X - hr * sc * 1.7, Y - hr * sc, X + hr * sc * 1.7, Y + hr * sc], fill=0)
    a = np.asarray(m, np.float32) / 255
    v = np.asarray(vm.filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 255
    n1 = _noise(rng, Wp, Hp, 4, 3)
    b = np.array((40, 82, 28), np.float32) / 255
    vc = np.array((92, 132, 54), np.float32) / 255
    rgb = b * (1 + 0.16 * (n1[..., None] - 0.5))
    rgb = rgb * (1 - v[..., None] * 0.55) + vc * v[..., None] * 0.55
    return _down(rgb, a, W, H)


def _lavender(rng, W, H):
    """Kłos lawendy: łodyżka + okółki kwiatów w górnej części."""
    Image, ImageDraw, _ = _pil()
    S = 2
    Wp, Hp = W * S, H * S
    cv = Image.new("RGBA", (Wp, Hp), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    d.line([(Wp / 2, Hp - 2), (Wp / 2, Hp * 0.04)], fill=(104, 116, 84, 255), width=max(2, int(Wp * 0.05)))
    nw = 12
    for k in range(nw):
        t = k / (nw - 1)
        y = Hp * (0.05 + 0.45 * t ** 1.3)
        rw = Wp * (0.13 + 0.09 * t) * (0.6 if k == 0 else 1)
        for i in range(14):
            ang = rng.uniform(0, 2 * math.pi)
            x = Wp / 2 + math.cos(ang) * rw * 0.75
            yy = y + rng.normal(0, Hp * 0.008)
            c = np.array((104, 76, 166), np.float32) * rng.uniform(0.7, 1.08) * (0.8 if math.sin(ang) < 0 else 1.05)
            rr = Wp * rng.uniform(0.045, 0.07)
            d.ellipse([x - rr, yy - rr * 1.25, x + rr, yy + rr * 1.25], fill=tuple(int(q) for q in np.clip(c, 0, 255)) + (255,))
    rgba = np.asarray(cv, np.float32) / 255
    return _down(rgba[..., :3], rgba[..., 3], W, H)


def _lavender_leaves(rng, W, H):
    """Kępka wąskich, szarozielonych liści lawendy (wachlarz)."""
    Image, ImageDraw, _ = _pil()
    S = 2
    Wp, Hp = W * S, H * S
    cv = Image.new("RGBA", (Wp, Hp), (0, 0, 0, 0))
    d = ImageDraw.Draw(cv)
    for i in range(140):
        x0 = Wp / 2 + rng.normal(0, Wp * 0.04)
        ang = rng.normal(0, 0.55)
        L = Hp * rng.uniform(0.35, 0.95)
        pts = []
        for t in np.linspace(0, 1, 6):
            a = ang * (1 + 0.6 * t)
            pts.append((x0 + math.sin(a) * L * t, Hp - 2 - math.cos(a) * L * t))
        c = np.array((112, 128, 100), np.float32) * rng.uniform(0.75, 1.15)
        _twig_line(d, pts, tuple(int(q) for q in np.clip(c, 0, 255)) + (255,), Wp * 0.011, Wp * 0.004)
    rgba = np.asarray(cv, np.float32) / 255
    return _down(rgba[..., :3], rgba[..., 3], W, H)


def _lily_pad(rng, W, H):
    """Liść grzybieni: zieleń z promienistymi nerwami i czerwonawym brzegiem (mapowany planarnie)."""
    Image, ImageDraw, ImageFilter = _pil()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = (xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)
    rr = np.hypot(u, v)
    ang = np.arctan2(v, u)
    n1 = _noise(rng, W, H, 5, 3)
    b = np.array((58, 96, 34), np.float32) / 255
    rgb = b * (0.85 + 0.3 * n1[..., None])
    veins = np.clip(1 - np.abs(np.sin(ang * 13)) * 9, 0, 1) * np.clip(rr * 1.5, 0, 1) * (rr < 0.97)
    rgb = rgb * (1 - 0.25 * veins[..., None]) + np.array((100, 130, 60)) / 255 * 0.25 * veins[..., None]
    edge = np.clip((rr - 0.93) / 0.06, 0, 1)[..., None] * 0.8
    rgb = rgb * (1 - edge) + np.array((110, 52, 36)) / 255 * edge
    a = (rr < 1.0).astype(np.float32)
    return _down(rgb, a, W, H)


def tekstury(force=False):
    """Generuje brakujące tekstury roślin (wymaga PIL)."""
    Image, _, _ = _pil()
    os.makedirs(GEN, exist_ok=True)
    rng0 = np.random.default_rng(1234)

    def save(name, cells):
        cols, rows, W, H = ATLAS[name]
        atlas = Image.new("RGBA", (cols * W, rows * H), (0, 0, 0, 0))
        # tło atlasu = średni kolor (bez obwódek)
        for k, im in enumerate(cells):
            cx, cy = k % cols, k // cols
            atlas.paste(im, (cx * W, cy * H))
        p = _tex_path(name)
        atlas.save(p + ".tmp.png")
        os.replace(p + ".tmp.png", p)

    def need(name):
        return force or not os.path.exists(_tex_path(name))

    for sp in LEAF_COL:
        cols, rows, W, H = ATLAS["liscie_" + sp]
        rng = np.random.default_rng(zlib.crc32(sp.encode()))
        singles = []
        for k in range(4):
            rgb, a = _leaf_rgba(sp, rng, W, H)
            singles.append(_down(rgb, a, W, H))
        if need("liscie_" + sp):
            save("liscie_" + sp, singles)
        # „spray” i kępa składane z pojedynczych liści
        tw = (110, 40, 30) if sp == "klon" else (88, 70, 52)
        if need("spray_" + sp):
            cols, rows, W, H = ATLAS["spray_" + sp]
            nl = {"oliwka": 9, "bukszpan": 11, "brzoza": 7, "bambus": 6}.get(sp, 5)
            save("spray_" + sp, [_spray(sp, rng, W, H, nl, singles, tw), _spray(sp, rng, W, H, nl + 2, singles, tw)])
        if "kepa_" + sp in ATLAS and need("kepa_" + sp):
            cols, rows, W, H = ATLAS["kepa_" + sp]
            nl = {"oliwka": 150, "brzoza": 140, "klon": 110}.get(sp, 100)
            lf = {"oliwka": 0.13, "brzoza": 0.1, "klon": 0.12}.get(sp, 0.125)
            save("kepa_" + sp, [_cluster(sp, rng, W, H, singles, nl, tw, lf), _cluster(sp, rng, W, H, singles, nl, tw, lf)])
    if need("igly"):
        cols, rows, W, H = ATLAS["igly"]
        save("igly", [_needles(rng0, W, H, k) for k in range(4)])
    if need("galazki"):
        cols, rows, W, H = ATLAS["galazki"]
        save("galazki", [_twigs(rng0, W, H), _twigs(rng0, W, H, birch=True)])
    if need("paproc"):
        cols, rows, W, H = ATLAS["paproc"]
        save("paproc", [_fern(rng0, W, H), _fern(rng0, W, H)])
    if need("monstera"):
        cols, rows, W, H = ATLAS["monstera"]
        save("monstera", [_monstera(rng0, W, H), _monstera(rng0, W, H)])
    if need("lawenda"):
        cols, rows, W, H = ATLAS["lawenda"]
        save("lawenda", [_lavender(rng0, W, H), _lavender(rng0, W, H)])
    if need("lawenda_lisc"):
        cols, rows, W, H = ATLAS["lawenda_lisc"]
        save("lawenda_lisc", [_lavender_leaves(rng0, W, H)])
    if need("lilia"):
        cols, rows, W, H = ATLAS["lilia"]
        save("lilia", [_lily_pad(rng0, W, H)])


def _ensure_textures():
    if all(os.path.exists(_tex_path(n)) for n in ATLAS):
        return
    try:
        import PIL  # noqa: F401
        tekstury()
        return
    except ImportError:
        pass
    import fcntl
    os.makedirs(GEN, exist_ok=True)
    with open(os.path.join(GEN, ".lock"), "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        if all(os.path.exists(_tex_path(n)) for n in ATLAS):
            return
        for py in ("/usr/bin/python3", "/bin/python3", "python3"):
            try:
                subprocess.run([py, os.path.abspath(__file__), "--tekstury"], check=True, cwd=HERE)
                return
            except Exception as e:  # następny interpreter
                err = e
        raise RuntimeError(f"nie udało się wygenerować tekstur roślin: {err}")



# =====================================================================================================
#  GEOMETRIA (numpy): części siatki zbierane w Geo, na końcu jedna siatka Blendera
# =====================================================================================================

def _nz(v, eps=1e-9):
    return v / (np.linalg.norm(v, axis=-1, keepdims=True) + eps)


class Geo:
    """Zbiera wierzchołki, ściany (czworokąty/trójkąty), UV, materiały i atrybuty kilku części."""

    def __init__(self):
        self.parts = []
        self.mats = []

    def mat(self, key):
        if key not in self.mats:
            self.mats.append(key)
        return self.mats.index(key)

    def add(self, verts, faces, uv=None, mat="kora", pattr=None, fattr=None):
        v = np.asarray(verts, np.float32).reshape(-1, 3)
        f = np.asarray(faces, np.int32)
        if len(f) == 0:
            return
        if uv is not None:
            uv = np.asarray(uv, np.float32).reshape(len(f), f.shape[1], 2)
        self.parts.append((v, f, uv, self.mat(mat), pattr or {}, fattr or {}))

    def ntris(self):
        return int(sum(len(f) * (f.shape[1] - 2) for _, f, *_ in self.parts))

    def bounds(self):
        V = np.concatenate([p[0] for p in self.parts])
        return float(np.hypot(V[:, 0], V[:, 1]).max()), float(V[:, 2].min()), float(V[:, 2].max())

    def arrays(self):
        """Scalone tablice (do budowy siatki i do pamięci podręcznej na dysku)."""
        pn, fn = {}, {}
        for v, f, uv, mi, pa, fa in self.parts:
            for k, a in pa.items():
                pn[k] = 1 if np.ndim(a) == 1 else 3
            for k, a in fa.items():
                fn[k] = 1 if np.ndim(a) == 1 else 3
        V, L, S, UV, MI = [], [], [], [], []
        PA = {k: [] for k in pn}
        FA = {k: [] for k in fn}
        off = loff = 0
        for v, f, uv, mi, pa, fa in self.parts:
            m, k = f.shape
            V.append(v)
            L.append((f + off).ravel())
            S.append(loff + np.arange(m, dtype=np.int32) * k)
            UV.append(uv.reshape(-1, 2) if uv is not None else np.zeros((m * k, 2), np.float32))
            MI.append(np.full(m, mi, np.int32))
            for name, dim in pn.items():
                a = pa.get(name)
                PA[name].append(np.asarray(a, np.float32) if a is not None else np.zeros((len(v),) if dim == 1 else (len(v), 3), np.float32))
            for name, dim in fn.items():
                a = fa.get(name)
                FA[name].append(np.asarray(a, np.float32) if a is not None else np.zeros((m,) if dim == 1 else (m, 3), np.float32))
            off += len(v)
            loff += m * k
        out = dict(V=np.concatenate(V), L=np.concatenate(L), S=np.concatenate(S), UV=np.concatenate(UV),
                   MI=np.concatenate(MI))
        for k in pn:
            out["p_" + k] = np.concatenate(PA[k])
        for k in fn:
            out["f_" + k] = np.concatenate(FA[k])
        return out


def _mesh_from_arrays(name, A):
    import bpy
    me = bpy.data.meshes.new(name)
    V, L, S = A["V"], A["L"], A["S"]
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.astype(np.float32).ravel())
    me.loops.add(len(L))
    me.loops.foreach_set("vertex_index", L.astype(np.int32))
    me.polygons.add(len(S))
    me.polygons.foreach_set("loop_start", S.astype(np.int32))
    tot = np.diff(np.append(S, len(L))).astype(np.int32)
    me.polygons.foreach_set("loop_total", tot)
    me.update(calc_edges=True)
    uv = me.uv_layers.new(name="UVMap")
    uv.data.foreach_set("uv", A["UV"].astype(np.float32).ravel())
    me.polygons.foreach_set("material_index", A["MI"].astype(np.int32))
    for k, a in A.items():
        if k.startswith("p_") or k.startswith("f_"):
            dom = "POINT" if k[0] == "p" else "FACE"
            if a.ndim == 1:
                at = me.attributes.new(k[2:], "FLOAT", dom)
                at.data.foreach_set("value", a.astype(np.float32))
            else:
                at = me.attributes.new(k[2:], "FLOAT_VECTOR", dom)
                at.data.foreach_set("vector", a.astype(np.float32).ravel())
    me.shade_smooth()
    return me


def _frames(P):
    """Styczne i ramki (transport równoległy) wzdłuż gałęzi P (M, n+1, 3)."""
    T = np.empty_like(P)
    T[:, 1:-1] = P[:, 2:] - P[:, :-2]
    T[:, 0] = P[:, 1] - P[:, 0]
    T[:, -1] = P[:, -1] - P[:, -2]
    T = _nz(T)
    ref = np.where(np.abs(T[:, 0, 2:3]) < 0.9, np.array([[0, 0, 1.0]]), np.array([[1.0, 0, 0]]))
    N = np.empty_like(P)
    N[:, 0] = _nz(np.cross(T[:, 0], ref))
    for i in range(1, P.shape[1]):
        n = N[:, i - 1] - (N[:, i - 1] * T[:, i]).sum(1, keepdims=True) * T[:, i]
        N[:, i] = _nz(n)
    B = np.cross(T, N)
    return T, N, B


def _tubes(G, P, R, sides, mat="kora", lobes=None, kofs=None, h0=1.0):
    """Rurki wzdłuż gałęzi: P (M, n+1, 3), R (M, n+1). lobes(θ, i) → mnożnik promienia (pień)."""
    M, n1, _ = P.shape
    if M == 0:
        return
    T, N, B = _frames(P)
    th = np.linspace(0, 2 * math.pi, sides, endpoint=False)
    ct, st = np.cos(th), np.sin(th)
    Rr = R[:, :, None] * np.ones(sides)
    if lobes is not None:
        Rr = Rr * lobes(th, P)
    ring = (P[:, :, None, :] + Rr[..., None] * (ct[None, None, :, None] * N[:, :, None, :] + st[None, None, :, None] * B[:, :, None, :]))
    V = ring.reshape(-1, 3)
    base = (np.arange(M) * n1 * sides)[:, None, None]
    i = np.arange(n1 - 1)[None, :, None] * sides
    j = np.arange(sides)[None, None, :]
    j1 = (j + 1) % sides
    q = np.stack([base + i + j, base + i + j1, base + i + sides + j1, base + i + sides + j], -1).reshape(-1, 4)
    # współrzędne kory: obwód (cos, sin)·r, długość łuku; przesunięcie losowe na gałąź
    seg = np.linalg.norm(np.diff(P, axis=1), axis=2)
    sarc = np.concatenate([np.zeros((M, 1)), np.cumsum(seg, 1)], 1)
    off = kofs if kofs is not None else np.zeros((M, 3))
    kora = np.stack([ct[None, None, :] * Rr, st[None, None, :] * Rr, np.broadcast_to(sarc[:, :, None], Rr.shape)], -1) + off[:, None, None, :]
    grub = np.broadcast_to(R[:, :, None], Rr.shape)
    wys = np.broadcast_to((P[:, :, 2] / h0)[:, :, None], Rr.shape)
    G.add(V, q, None, mat, pattr=dict(kora=kora.reshape(-1, 3), grub=grub.reshape(-1), wys=wys.reshape(-1)))


def _cards(G, A, U, Nn, length, width, cell, atlas, mat, cols=3, rows=2, fold=0.0, curl=0.0, rnd=None):
    """Karty liści: nasada w A, oś U (do czubka), normalna Nn. cell – indeks komórki atlasu."""
    K = len(A)
    if K == 0:
        return
    U = _nz(U)
    Nn = _nz(Nn - (Nn * U).sum(1, keepdims=True) * U)
    W = np.cross(U, Nn)
    x = np.linspace(-0.5, 0.5, cols)
    y = np.linspace(0, 1, rows)
    X, Y = np.meshgrid(x, y)                     # (rows, cols)
    L = length[:, None, None]
    Wd = width[:, None, None]
    fo = np.broadcast_to(np.asarray(fold, float), (K,))[:, None, None]
    cu = np.broadcast_to(np.asarray(curl, float), (K,))[:, None, None]
    off_n = np.abs(X)[None] * fo * Wd - (Y[None] ** 2) * cu * L
    V = (A[:, None, None, :] + U[:, None, None, :] * (Y[None] * L)[..., None] + W[:, None, None, :] * (X[None] * Wd)[..., None]
         + Nn[:, None, None, :] * off_n[..., None])
    base = (np.arange(K) * rows * cols)[:, None, None]
    ii = np.arange(rows - 1)[None, :, None] * cols
    jj = np.arange(cols - 1)[None, None, :]
    q = np.stack([base + ii + jj, base + ii + jj + 1, base + ii + cols + jj + 1, base + ii + cols + jj], -1).reshape(-1, 4)
    ac, ar, cw, chh = ATLAS[atlas]
    cx = cell % ac
    cy = cell // ac
    u0, du = cx / ac, 1.0 / ac
    v0, dv = 1.0 - (cy + 1) / ar, 1.0 / ar
    uu = u0[:, None, None] + (X[None] + 0.5) * du
    vv = v0[:, None, None] + Y[None] * dv
    UVv = np.stack([np.broadcast_to(uu, (K, rows, cols)), np.broadcast_to(vv, (K, rows, cols))], -1)   # (K, rows, cols, 2)
    # UV na rogach ścian
    fi = np.stack([ii + jj, ii + jj + 1, ii + cols + jj + 1, ii + cols + jj], -1).reshape(-1, 4)  # lokalne indeksy
    UVf = UVv.reshape(K, -1, 2)[:, fi.ravel()].reshape(-1, 4, 2)
    nf = (rows - 1) * (cols - 1)
    r = rnd if rnd is not None else np.random.default_rng(K).random(K)
    G.add(V.reshape(-1, 3), q, UVf, mat, fattr=dict(rnd=np.repeat(r, nf)))


# ----------------------------------------------------------------------------------- obwiednia korony
class Env:
    """Obwiednia korony: promień R(z) od podstawy korony zb do szczytu h (oś pionowa przez nasadę)."""

    def __init__(self, h, r, zb, peak=0.45, base=0.3, a=2.0, b=2.0, core=0.12, drop=0.18):
        self.h, self.r, self.zb = h, r, zb
        self.peak, self.base, self.a, self.b, self.core, self.drop = peak, base, a, b, core, drop

    def R(self, z):
        t = (z - self.zb) / max(1e-6, self.h - self.zb)
        tc = np.clip(t, 0, 1)
        lo = tc < self.peak
        u = np.where(lo, (self.peak - tc) / self.peak, (tc - self.peak) / (1 - self.peak))
        e = np.where(lo, self.a, self.b)
        sh = np.clip(1 - np.clip(u, 0, 1) ** e, 0, 1) ** (1 / e)
        sh = np.where(lo, self.base + (1 - self.base) * sh, sh)
        # poniżej podstawy korony gałęzie mogą lekko opaść
        sh = np.where(t < 0, self.base * np.clip(1 + t / self.drop, 0, 1), sh)
        out = self.r * sh
        core = np.where((t > -0.3) & (t < 1.0), self.r * np.maximum(self.core, 0.3 * (t < 0)), 0.0)
        return np.where(t > 1.0, 0.0, np.maximum(out, core))

    def excess(self, P):
        rho = np.hypot(P[..., 0], P[..., 1])
        R = self.R(P[..., 2])
        return np.where(R > 1e-6, rho / np.maximum(R, 1e-6), 9.0)

    def pull(self, P, k):
        """Wektor ściągający do środka przy brzegu obwiedni."""
        e = self.excess(P)
        w = np.clip((e - 0.8) / 0.2, 0, 2.0)[:, None] * k
        rho = np.hypot(P[:, 0], P[:, 1])[:, None] + 1e-6
        inward = np.concatenate([-P[:, :2] / rho, np.zeros((len(P), 1))], 1)
        top = np.clip((P[:, 2] - self.h * 0.95) / (self.h * 0.05), 0, 1.5)[:, None] * k * np.array([[0, 0, -1.0]])
        return inward * w + top

    def raylen(self, S, D, Lmax, K=28):
        """Długość promienia do wyjścia z obwiedni (liczy się wyjście po wejściu – gałąź może startować poza nią)."""
        f = np.linspace(1.0 / K, 1.0, K)
        Q = S[:, None, :] + D[:, None, :] * (f[None, :, None] * Lmax[:, None, None])
        e = self.excess(Q)
        seen = np.maximum.accumulate(e <= 1.0, axis=1) | (self.excess(S) <= 1.0)[:, None]
        out = (e > 1.0) & seen
        first = np.where(out.any(1), out.argmax(1), np.where(seen[:, -1], K, K // 3))
        return np.maximum(Lmax * first / K, Lmax * 0.12)


# ----------------------------------------------------------------------------------- szkielet
class Lv:
    """Wszystkie gałęzie jednego poziomu: P (M, n+1, 3), długości L, rodzic par i miejsce t na rodzicu."""

    def __init__(self, P, L, par, t, lvl):
        self.P, self.L, self.par, self.t, self.lvl = P, L, par, t, lvl
        self.R = None
        self.T = self.N = self.B = None

    @property
    def M(self):
        return len(self.P)

    def frames(self):
        if self.T is None and self.M:
            self.T, self.N, self.B = _frames(self.P)
        return self.T, self.N, self.B

    def at(self, idx, t):
        """Pozycja, styczna i ramka w punkcie t (0..1) gałęzi idx."""
        n = self.P.shape[1] - 1
        f = np.clip(t, 0, 1) * n
        i0 = np.minimum(np.floor(f).astype(int), n - 1)
        w = (f - i0)[:, None]
        T, N, B = self.frames()
        pos = self.P[idx, i0] * (1 - w) + self.P[idx, i0 + 1] * w
        tt = _nz(T[idx, i0] * (1 - w) + T[idx, i0 + 1] * w)
        nn = _nz(N[idx, i0] * (1 - w) + N[idx, i0 + 1] * w)
        nn = _nz(nn - (nn * tt).sum(1, keepdims=True) * tt)
        return pos, tt, nn, np.cross(tt, nn)


def _grow(S0, D0, L, nseg, rng, env, wander, up, grav, gpow=1.3, flat=0.0, envk=0.9, clip=True, curl=0.0):
    """Rośnięcie wielu gałęzi naraz krokami: losowe zgięcia, fototropizm, grawitacja, obwiednia."""
    M = len(S0)
    P = np.empty((M, nseg + 1, 3))
    P[:, 0] = S0
    d = _nz(np.array(D0, float))
    step = (L / nseg)[:, None]
    gl = np.clip(L / (np.mean(L) + 1e-6), 0.4, 1.8)[:, None]   # dłuższe gałęzie bardziej się uginają
    side = _nz(np.cross(d, rng.normal(0, 1, (M, 3))))
    for i in range(nseg):
        t = (i + 0.5) / nseg
        d = d + rng.normal(0, wander, (M, 3)) + side * curl * 0.5 * math.sin(t * 6.3)
        d[:, 2] += up - grav * gl[:, 0] * t ** gpow
        if flat:
            d[:, 2] *= 1 - flat
        if env is not None:
            d = d + env.pull(P[:, i] + d * step, envk)
        d = _nz(d)
        P[:, i + 1] = P[:, i] + d * step
    if clip and env is not None:
        e = env.excess(P[:, 1:])
        seen = np.maximum.accumulate(e <= 1.0, axis=1) | (env.excess(P[:, 0]) <= 1.0)[:, None]
        out = (e > 1.1) & seen
        bad = out.any(1)
        if bad.any():
            first = out.argmax(1)
            seg = np.linalg.norm(np.diff(P, axis=1), axis=2)
            cum = np.concatenate([np.zeros((M, 1)), np.cumsum(seg, 1)], 1)
            s_cut = np.where(bad, cum[np.arange(M), first] + 0.3 * seg[np.arange(M), first], cum[:, -1])
            s_cut = np.maximum(s_cut, cum[:, -1] * 0.08)
            P = _resample(P, s_cut, cum)
            L = s_cut
    return P, L


def _resample(P, s_new, cum=None):
    M, n1, _ = P.shape
    if cum is None:
        seg = np.linalg.norm(np.diff(P, axis=1), axis=2)
        cum = np.concatenate([np.zeros((M, 1)), np.cumsum(seg, 1)], 1)
    tgt = s_new[:, None] * np.linspace(0, 1, n1)[None]
    idx = (cum[:, None, :] <= tgt[:, :, None]).sum(-1) - 1
    idx = np.clip(idx, 0, n1 - 2)
    s0 = np.take_along_axis(cum, idx, 1)
    s1 = np.take_along_axis(cum, idx + 1, 1)
    f = np.clip((tgt - s0) / np.maximum(s1 - s0, 1e-9), 0, 1)[..., None]
    P0 = np.take_along_axis(P, idx[..., None].repeat(3, -1), 1)
    P1 = np.take_along_axis(P, (idx + 1)[..., None].repeat(3, -1), 1)
    return P0 + (P1 - P0) * f


def _spawn(par, counts, t0, t1, rng, ang, rot="spiral", flat_bias=0.0, up_bias=0.0, tjit=0.5, tpow=1.0, outward=0.0):
    """Miejsca i kierunki gałęzi potomnych. ang – (kąt u dołu, kąt u góry) w stopniach."""
    counts = np.asarray(counts, int)
    idx = np.repeat(np.arange(par.M), counts)
    if len(idx) == 0:
        return idx, np.zeros(0), np.zeros((0, 3)), np.zeros((0, 3))
    starts = np.repeat(np.cumsum(counts) - counts, counts)
    k = np.arange(len(idx)) - starts
    cnt = counts[idx]
    tt0 = t0[idx] if np.ndim(t0) else np.full(len(idx), t0)
    u = (k + 0.5 + rng.uniform(-tjit, tjit, len(idx)) * 0.9) / cnt
    t = tt0 + (t1 - tt0) * np.clip(u, 0.0, 1.0) ** tpow
    pos, T, N, B = par.at(idx, t)
    psi0 = rng.uniform(0, 2 * math.pi, par.M)[idx]
    if rot == "spiral":
        psi = psi0 + k * 2.39996 + rng.normal(0, 0.25, len(idx))
    elif rot == "opposite":
        psi = psi0 + (k // 2) * (math.pi / 2) + (k % 2) * math.pi + rng.normal(0, 0.2, len(idx))
    elif rot == "whorl":
        psi = psi0 + k * 2 * math.pi / np.maximum(cnt, 1) + rng.normal(0, 0.3, len(idx))
    else:  # "flat": na boki w płaszczyźnie poziomej
        psi = None
    if psi is not None:
        side = np.cos(psi)[:, None] * N + np.sin(psi)[:, None] * B
    else:
        hz = np.cross(np.array([0, 0, 1.0]), T)
        hz = np.where(np.linalg.norm(hz, axis=1, keepdims=True) < 1e-3, N, hz)
        sgn = np.where(k % 2 == 0, 1.0, -1.0)[:, None]
        side = _nz(_nz(hz) * sgn + np.array([0, 0, 1.0]) * rng.normal(0.15, 0.25, (len(idx), 1)))
        side = _nz(side - (side * T).sum(1, keepdims=True) * T)
    a = np.radians(ang[0] + (ang[1] - ang[0]) * t + rng.normal(0, 6, len(idx)))
    D = np.cos(a)[:, None] * T + np.sin(a)[:, None] * side
    if flat_bias:
        D[:, 2] *= 1 - flat_bias
    if up_bias:
        D[:, 2] += up_bias
    if outward:
        # gałęzie rosnące do wnętrza korony zamierają – kierunek odchylony na zewnątrz
        rad = np.concatenate([pos[:, :2], np.zeros((len(pos), 1))], 1)
        rad = _nz(rad + 1e-5)
        D = _nz(D) + rad * outward
    return idx, t, pos, _nz(D)


def _pipe(levels, r_tip, e=2.2, k_len=1.5e-5):
    """Grubości z modelu rurek: przekrój gałęzi = suma przekrojów gałęzi wyżej + przyrost na długości."""
    for li in range(len(levels) - 1, -1, -1):
        lv = levels[li]
        if lv.M == 0:
            lv.R = np.zeros((0, lv.P.shape[1]))
            continue
        n1 = lv.P.shape[1]
        rem = (1 - np.linspace(0, 1, n1))[None, :] * lv.L[:, None]
        A = np.full((lv.M, n1), r_tip ** e) + k_len * rem
        if li + 1 < len(levels) and levels[li + 1].M:
            ch = levels[li + 1]
            node = np.clip(np.ceil(ch.t * (n1 - 1)).astype(int), 0, n1 - 1)
            inc = np.zeros((lv.M, n1))
            np.add.at(inc, (ch.par, node), ch.R[:, 0] ** e)
            A += np.cumsum(inc[:, ::-1], 1)[:, ::-1]
        lv.R = A ** (1.0 / e)
    # dziecko nie grubsze niż rodzic w miejscu wyrastania
    for li in range(1, len(levels)):
        ch, pa = levels[li], levels[li - 1]
        if ch.M == 0:
            continue
        n1 = pa.P.shape[1]
        node = np.clip(np.round(ch.t * (n1 - 1)).astype(int), 0, n1 - 1)
        lim = pa.R[ch.par, node] * 0.82
        ch.R = np.minimum(ch.R, lim[:, None])


def _rescale_radii(levels, r_tip, target):
    """Pień dociągnięty do docelowego promienia, cienkie gałązki bez zmian (interpolacja w skali log)."""
    r0 = math.sqrt(float((levels[0].R[:, 0] ** 2).sum()))
    if r0 <= r_tip * 1.01 or target <= 0:
        return
    k = math.log(target / r0)
    lr0 = math.log(r0 / r_tip)
    for lv in levels:
        if lv.M:
            f = np.clip(np.log(np.maximum(lv.R, r_tip) / r_tip) / lr0, 0, 1.5)
            lv.R = lv.R * np.exp(k * f)



# =====================================================================================================
#  MATERIAŁY (Cycles)
# =====================================================================================================

def _lin(c):
    """sRGB (0–1) → liniowy RGBA."""
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)


class _NT:
    """Mały pomocnik do budowy węzłów materiału."""

    def __init__(self, mat):
        self.nt = mat.node_tree
        self.nt.nodes.clear()

    def n(self, typ, **kw):
        nd = self.nt.nodes.new(typ)
        for k, v in kw.items():
            if k.startswith("_"):
                setattr(nd, k[1:], v)
            else:
                self.set(nd.inputs[k], v)
        return nd

    def set(self, sock, v):
        if hasattr(v, "is_output") or hasattr(v, "links"):
            self.nt.links.new(v, sock)
        else:
            sock.default_value = v

    def link(self, a, b):
        self.nt.links.new(a, b)

    def math(self, op, a, b=0.0, c=None):
        nd = self.nt.nodes.new("ShaderNodeMath")
        nd.operation = op
        self.set(nd.inputs[0], a)
        self.set(nd.inputs[1], b)
        if c is not None:
            self.set(nd.inputs[2], c)
        return nd.outputs[0]

    def mix(self, fac, a, b, blend="MIX"):
        nd = self.nt.nodes.new("ShaderNodeMix")
        nd.data_type = "RGBA"
        nd.blend_type = blend
        self.set(nd.inputs["Factor"], fac)
        self.set(nd.inputs["A"], a)
        self.set(nd.inputs["B"], b)
        return nd.outputs["Result"]

    def ramp(self, fac, stops, interp="LINEAR"):
        nd = self.nt.nodes.new("ShaderNodeValToRGB")
        cr = nd.color_ramp
        cr.interpolation = interp
        cr.elements[0].position, cr.elements[0].color = stops[0][0], stops[0][1]
        cr.elements[1].position, cr.elements[1].color = stops[-1][0], stops[-1][1]
        for pos, col in stops[1:-1]:
            e = cr.elements.new(pos)
            e.color = col
        self.set(nd.inputs[0], fac)
        return nd.outputs[0]

    def out(self, shader):
        o = self.nt.nodes.new("ShaderNodeOutputMaterial")
        o.target = "ALL"
        self.link(shader, o.inputs["Surface"])
        return o


def _new_mat(name):
    import bpy
    import warnings
    m = bpy.data.materials.new(name)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m.use_nodes = True
    return m


def _image(name):
    import bpy
    p = _tex_path(name)
    im = bpy.data.images.load(p, check_existing=True)
    im.alpha_mode = "CHANNEL_PACKED"
    return im


# parametry liści: (zmienność odcienia, nasycenia, jasności, przeświecanie, odcień spodu, szorstkość, mnożnik koloru)
LEAF_SH = {
    "klon": (0.035, 0.18, 0.30, 0.38, (1.05, 0.80, 0.75), 0.48, (1.0, 1.0, 1.0)),
    "klon_zielony": (0.03, 0.15, 0.28, 0.30, (1.15, 1.18, 1.0), 0.5, (1.0, 1.0, 1.0)),
    "brzoza": (0.03, 0.15, 0.28, 0.32, (1.2, 1.2, 1.05), 0.5, (1.0, 1.0, 1.0)),
    "lipa": (0.03, 0.15, 0.28, 0.30, (1.25, 1.25, 1.05), 0.5, (1.0, 1.0, 1.0)),
    "oliwka": (0.02, 0.10, 0.22, 0.18, (1.9, 1.85, 1.75), 0.55, (1.0, 1.0, 1.0)),
    "cytrus": (0.02, 0.12, 0.22, 0.22, (1.35, 1.35, 1.15), 0.28, (1.0, 1.0, 1.0)),
    "bukszpan": (0.025, 0.12, 0.25, 0.25, (1.25, 1.25, 1.05), 0.42, (1.0, 1.0, 1.0)),
    "bambus": (0.03, 0.12, 0.25, 0.32, (1.2, 1.2, 1.05), 0.45, (1.0, 1.0, 1.0)),
    "igly": (0.025, 0.12, 0.22, 0.18, (1.15, 1.15, 1.1), 0.55, (1.0, 1.0, 1.0)),
    "galazki": (0.02, 0.05, 0.25, 0.0, (1.0, 1.0, 1.0), 0.8, (1.0, 1.0, 1.0)),
    "paproc": (0.03, 0.12, 0.25, 0.35, (1.2, 1.2, 1.05), 0.5, (1.0, 1.0, 1.0)),
    "monstera": (0.02, 0.10, 0.18, 0.22, (1.3, 1.3, 1.1), 0.42, (1.0, 1.0, 1.0)),
    "lawenda": (0.03, 0.12, 0.25, 0.25, (1.1, 1.1, 1.1), 0.6, (1.0, 1.0, 1.0)),
    "lawenda_lisc": (0.02, 0.10, 0.22, 0.15, (1.2, 1.2, 1.2), 0.65, (1.0, 1.0, 1.0)),
    "lilia": (0.02, 0.10, 0.18, 0.0, (1.0, 1.0, 1.0), 0.3, (0.85, 0.9, 0.8)),
}


def _mat_leaf(ctx, atlas, sh_key):
    """Liść: tekstura z alfą, zmienność koloru na liść (atrybut rnd) i na drzewo, przeświecanie, jaśniejszy spód."""
    key = "rosliny:mat:lisc:" + atlas
    if key in ctx.cache:
        return ctx.cache[key]
    hv, sv, vv, tr, under, rough, mul = LEAF_SH.get(sh_key, LEAF_SH["lipa"])
    m = _new_mat("lisc_" + atlas)
    N = _NT(m)
    uv = N.n("ShaderNodeUVMap", _uv_map="UVMap")
    tex = N.n("ShaderNodeTexImage", _image=_image(atlas), _interpolation="Linear", _extension="CLIP")
    N.link(uv.outputs[0], tex.inputs[0])
    at = N.n("ShaderNodeAttribute", _attribute_name="rnd")
    oi = N.n("ShaderNodeObjectInfo")
    r1 = at.outputs["Fac"]
    r2 = N.math("FRACT", N.math("MULTIPLY", r1, 7.31))
    r3 = N.math("FRACT", N.math("MULTIPLY", r1, 13.7))
    hue = N.math("ADD", N.math("MULTIPLY_ADD", r1, hv, 0.5 - hv / 2), N.math("MULTIPLY", N.math("SUBTRACT", oi.outputs["Random"], 0.5), hv * 0.6))
    sat = N.math("MULTIPLY_ADD", r3, sv, 1.0 - sv / 2)
    val = N.math("MULTIPLY_ADD", r2, vv, 1.0 - vv / 2)
    hsv = N.n("ShaderNodeHueSaturation", Hue=hue, Saturation=sat, Value=val, Fac=1.0, Color=tex.outputs["Color"])
    col = hsv.outputs[0]
    if mul != (1.0, 1.0, 1.0):
        col = N.mix(1.0, col, mul + (1.0,), "MULTIPLY")
    geo = N.n("ShaderNodeNewGeometry")
    under_col = N.mix(1.0, col, under + (1.0,), "MULTIPLY")
    col2 = N.mix(geo.outputs["Backfacing"], col, under_col)
    bs = N.n("ShaderNodeBsdfPrincipled", **{"Base Color": col2, "Roughness": rough, "Specular IOR Level": 0.45})
    sh = bs.outputs[0]
    if tr > 0:
        tcol = N.mix(1.0, col, (1.25, 1.35, 0.6, 1.0), "MULTIPLY")
        tl = N.n("ShaderNodeBsdfTranslucent", Color=tcol)
        mx = N.n("ShaderNodeMixShader", Fac=tr)
        N.link(bs.outputs[0], mx.inputs[1])
        N.link(tl.outputs[0], mx.inputs[2])
        sh = mx.outputs[0]
    tp = N.n("ShaderNodeBsdfTransparent")
    ma = N.n("ShaderNodeMixShader", Fac=tex.outputs["Alpha"])
    N.link(tp.outputs[0], ma.inputs[1])
    N.link(sh, ma.inputs[2])
    N.out(ma.outputs[0])
    ctx.cache[key] = m
    return m


# kora: (kolor płytek, kolor szczelin, kolor gałązek, skala wokół, skala wzdłuż, siła rys, wypukłość, szorstkość)
BARK = {
    "lipa": ((0.36, 0.31, 0.26), (0.12, 0.10, 0.08), (0.33, 0.26, 0.20), 30.0, 3.0, 0.6, 1.0, 0.85),
    "klon_zielony": ((0.36, 0.33, 0.29), (0.13, 0.11, 0.09), (0.36, 0.30, 0.22), 26.0, 3.5, 0.55, 0.9, 0.85),
    "klon": ((0.40, 0.36, 0.33), (0.27, 0.24, 0.21), (0.42, 0.20, 0.15), 30.0, 2.0, 0.2, 0.3, 0.7),
    "oliwka": ((0.47, 0.45, 0.40), (0.14, 0.13, 0.11), (0.45, 0.43, 0.36), 16.0, 3.0, 0.7, 1.4, 0.9),
    "sosna": ((0.40, 0.31, 0.25), (0.10, 0.08, 0.07), (0.62, 0.38, 0.22), 15.0, 2.4, 0.7, 1.3, 0.9),
    "cytrus": ((0.40, 0.38, 0.32), (0.26, 0.24, 0.21), (0.35, 0.40, 0.25), 30.0, 3.0, 0.2, 0.25, 0.75),
    "bukszpan": ((0.42, 0.37, 0.30), (0.22, 0.19, 0.15), (0.40, 0.36, 0.26), 9.0, 2.0, 0.3, 0.3, 0.8),
    "palma": ((0.47, 0.43, 0.37), (0.20, 0.18, 0.15), (0.40, 0.33, 0.24), 4.0, 1.0, 0.0, 0.8, 0.85),
    "bambus": ((0.38, 0.52, 0.18), (0.30, 0.42, 0.14), (0.38, 0.52, 0.18), 4.0, 1.0, 0.0, 0.1, 0.4),
}


def _mat_bark(ctx, sp):
    key = "rosliny:mat:kora:" + sp
    if key in ctx.cache:
        return ctx.cache[key]
    m = _new_mat("kora_" + sp)
    N = _NT(m)
    kor = N.n("ShaderNodeAttribute", _attribute_name="kora")
    grub = N.n("ShaderNodeAttribute", _attribute_name="grub").outputs["Fac"]
    wys = N.n("ShaderNodeAttribute", _attribute_name="wys").outputs["Fac"]
    vec = kor.outputs["Vector"]
    oi = N.n("ShaderNodeObjectInfo")
    bs = N.n("ShaderNodeBsdfPrincipled")
    if sp == "brzoza":
        # biała kora z czarnymi przetchlinkami, ciemna spękana nasada, ciemne cienkie gałązki
        mp = N.n("ShaderNodeMapping", Vector=vec, Scale=(5.0, 5.0, 26.0))
        ns = N.n("ShaderNodeTexNoise", Vector=mp.outputs[0], Scale=1.6, Detail=3.0, Roughness=0.55)
        lent = N.ramp(ns.outputs["Fac"], [(0.0, (0, 0, 0, 1)), (0.60, (0, 0, 0, 1)), (0.66, (1, 1, 1, 1)), (1.0, (1, 1, 1, 1))])
        mp2 = N.n("ShaderNodeMapping", Vector=vec, Scale=(2.0, 2.0, 3.0))
        ns2 = N.n("ShaderNodeTexNoise", Vector=mp2.outputs[0], Scale=2.0, Detail=5.0)
        white = N.ramp(ns2.outputs["Fac"], [(0.3, _lin((0.70, 0.69, 0.65))), (0.55, _lin((0.86, 0.85, 0.81))), (0.75, _lin((0.80, 0.78, 0.72)))])
        dark = _lin((0.07, 0.065, 0.06))
        c = N.mix(N.math("MULTIPLY", N.n("ShaderNodeSeparateColor", Color=lent).outputs[0], 0.92), white, dark)
        # nasada: ciemna, spękana kora (wys – wysokość względna; tu wysokość bezwzględna z kora.z nie wystarcza)
        tc = N.n("ShaderNodeTexCoord")
        sep = N.n("ShaderNodeSeparateXYZ", Vector=tc.outputs["Object"])
        nb = N.n("ShaderNodeTexNoise", Vector=vec, Scale=3.0, Detail=4.0)
        zb = N.math("ADD", sep.outputs["Z"], N.math("MULTIPLY", nb.outputs["Fac"], 0.5))
        base = N.n("ShaderNodeMapRange", Value=zb, **{"From Min": 0.8, "From Max": 1.5, "To Min": 1.0, "To Max": 0.0}).outputs[0]
        vor = N.n("ShaderNodeTexVoronoi", Vector=N.n("ShaderNodeMapping", Vector=vec, Scale=(9.0, 9.0, 2.5)).outputs[0], _feature="DISTANCE_TO_EDGE")
        crack = N.ramp(vor.outputs["Distance"], [(0.0, (0, 0, 0, 1)), (0.06, (1, 1, 1, 1))])
        basec = N.mix(crack, _lin((0.05, 0.045, 0.04)), _lin((0.26, 0.25, 0.23)))
        c = N.mix(base, c, basec)
        twig = N.n("ShaderNodeMapRange", Value=grub, **{"From Min": 0.018, "From Max": 0.055, "To Min": 1.0, "To Max": 0.0}).outputs[0]
        c = N.mix(twig, c, _lin((0.22, 0.13, 0.10)))
        N.link(c, bs.inputs["Base Color"])
        bump_h = N.math("ADD", N.math("MULTIPLY", N.n("ShaderNodeSeparateColor", Color=lent).outputs[0], 0.3), N.math("MULTIPLY", N.math("SUBTRACT", 1.0, N.n("ShaderNodeSeparateColor", Color=crack).outputs[0]), N.math("MULTIPLY", base, -1.0)))
        bump = N.n("ShaderNodeBump", Strength=0.35, Height=bump_h)
        N.link(bump.outputs[0], bs.inputs["Normal"])
        N.set(bs.inputs["Roughness"], 0.6)
    else:
        cp, cc, ct, s_ar, s_al, crk, bmp, rough = BARK.get(sp, BARK["lipa"])
        # współrzędne kory zaburzone szumem: rysy meandrują zamiast tworzyć regularne komórki
        nw = N.n("ShaderNodeTexNoise", Vector=vec, Scale=4.0, Detail=3.0)
        dv = N.n("ShaderNodeVectorMath", _operation="MULTIPLY_ADD", Vector=nw.outputs["Color"])
        N.set(dv.inputs[1], (0.06, 0.06, 0.12))
        N.set(dv.inputs[2], vec)
        mp = N.n("ShaderNodeMapping", Vector=dv.outputs[0], Scale=(s_ar, s_ar, s_al))
        vor = N.n("ShaderNodeTexVoronoi", Vector=mp.outputs[0], _feature="DISTANCE_TO_EDGE", Scale=1.0, Randomness=1.0)
        nd = N.n("ShaderNodeTexNoise", Vector=mp.outputs[0], Scale=2.5, Detail=6.0, Roughness=0.6)
        # rysy: odległość od krawędzi komórki Voronoi zaburzona szumem
        dist = N.math("ADD", vor.outputs["Distance"], N.math("MULTIPLY", N.math("SUBTRACT", nd.outputs["Fac"], 0.5), 0.12))
        crack = N.ramp(dist, [(0.0, (0, 0, 0, 1)), (0.05 + 0.07 * crk, (1, 1, 1, 1))])
        nc = N.n("ShaderNodeTexNoise", Vector=vec, Scale=1.3, Detail=4.0)
        plate = N.ramp(nc.outputs["Fac"], [(0.25, _lin(tuple(x * 0.82 for x in cp))), (0.5, _lin(cp)), (0.75, _lin(tuple(min(1, x * 1.12) for x in cp)))])
        crack_f = N.math("MULTIPLY", N.math("SUBTRACT", 1.0, N.n("ShaderNodeSeparateColor", Color=crack).outputs[0]), crk)
        c = N.mix(crack_f, plate, _lin(cc))
        if sp == "sosna":
            # sosna: wyżej pomarańczowa, łuszcząca się kora
            up = N.n("ShaderNodeMapRange", Value=N.math("ADD", wys, N.math("MULTIPLY", nd.outputs["Fac"], 0.15)),
                     **{"From Min": 0.42, "From Max": 0.62, "To Min": 0.0, "To Max": 1.0}).outputs[0]
            orange = N.ramp(nc.outputs["Fac"], [(0.3, _lin((0.52, 0.30, 0.18))), (0.6, _lin((0.66, 0.40, 0.24))), (0.8, _lin((0.58, 0.36, 0.24)))])
            c = N.mix(up, c, orange)
        twig = N.n("ShaderNodeMapRange", Value=grub, **{"From Min": 0.004, "From Max": 0.025, "To Min": 1.0, "To Max": 0.0}).outputs[0]
        c = N.mix(twig, c, _lin(ct))
        if sp == "palma":
            # pierścienie po liściach
            wv = N.n("ShaderNodeTexWave", Vector=vec, _wave_type="BANDS", _bands_direction="Z", Scale=7.0, Distortion=1.5, Detail=2.0)
            rings = N.ramp(wv.outputs["Fac"], [(0.0, (0, 0, 0, 1)), (0.18, (1, 1, 1, 1))])
            c = N.mix(N.math("MULTIPLY", N.math("SUBTRACT", 1.0, N.n("ShaderNodeSeparateColor", Color=rings).outputs[0]), 0.6), c, _lin(cc))
            crack = rings
        N.link(c, bs.inputs["Base Color"])
        hb = N.math("ADD", N.n("ShaderNodeSeparateColor", Color=crack).outputs[0], N.math("MULTIPLY", nd.outputs["Fac"], 0.35))
        bump = N.n("ShaderNodeBump", Strength=min(1.0, 0.4 * bmp), Distance=0.02, Height=hb)
        N.link(bump.outputs[0], bs.inputs["Normal"])
        N.set(bs.inputs["Roughness"], rough)
    N.out(bs.outputs[0])
    ctx.cache[key] = m
    return m


def _mat_simple(ctx, name):
    """Materiały proste: owoce, donice, ziemia, kamień, mech, kwiaty, trawa, liście palmy."""
    key = "rosliny:mat:" + name
    if key in ctx.cache:
        return ctx.cache[key]
    m = _new_mat(name)
    N = _NT(m)
    bs = N.n("ShaderNodeBsdfPrincipled")
    tc = N.n("ShaderNodeTexCoord")
    sh = bs.outputs[0]
    if name in ("pomarancza", "cytryna"):
        base = (0.86, 0.40, 0.04) if name == "pomarancza" else (0.88, 0.74, 0.12)
        vor = N.n("ShaderNodeTexVoronoi", Vector=tc.outputs["Object"], Scale=260.0)
        ns = N.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=18.0)
        c = N.ramp(ns.outputs["Fac"], [(0.3, _lin(tuple(x * 0.85 for x in base))), (0.7, _lin(base))])
        N.link(c, bs.inputs["Base Color"])
        N.link(N.n("ShaderNodeBump", Strength=0.25, Height=vor.outputs["Distance"]).outputs[0], bs.inputs["Normal"])
        N.set(bs.inputs["Roughness"], 0.38)
        N.set(bs.inputs["Subsurface Weight"], 0.15)
    elif name in ("donica", "donica_ciemna", "ziemia"):
        if name == "donica":
            stops = [(0.3, _lin((0.52, 0.28, 0.18))), (0.55, _lin((0.62, 0.35, 0.23))), (0.8, _lin((0.66, 0.44, 0.33)))]
            rough = 0.85
        elif name == "donica_ciemna":
            stops = [(0.3, _lin((0.16, 0.16, 0.16))), (0.6, _lin((0.22, 0.22, 0.21))), (0.9, _lin((0.28, 0.27, 0.26)))]
            rough = 0.6
        else:
            stops = [(0.3, _lin((0.08, 0.06, 0.045))), (0.7, _lin((0.16, 0.12, 0.09)))]
            rough = 0.95
        ns = N.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=6.0, Detail=8.0)
        N.link(N.ramp(ns.outputs["Fac"], stops), bs.inputs["Base Color"])
        nf = N.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=60.0, Detail=4.0)
        N.link(N.n("ShaderNodeBump", Strength=0.3 if name != "ziemia" else 0.8, Height=nf.outputs["Fac"]).outputs[0], bs.inputs["Normal"])
        N.set(bs.inputs["Roughness"], rough)
    elif name == "kamien":
        # wygładzony głaz: plamy, drobne ziarno, mech w zagłębieniach od góry
        ns = N.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=2.2, Detail=8.0, Roughness=0.6)
        nf = N.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=40.0, Detail=6.0)
        c = N.ramp(ns.outputs["Fac"], [(0.25, _lin((0.30, 0.30, 0.29))), (0.5, _lin((0.44, 0.43, 0.41))), (0.7, _lin((0.52, 0.51, 0.48))), (0.85, _lin((0.40, 0.39, 0.37)))])
        c = N.mix(N.math("MULTIPLY", nf.outputs["Fac"], 0.25), c, _lin((0.62, 0.61, 0.58)))
        geo = N.n("ShaderNodeNewGeometry")
        nz = N.n("ShaderNodeSeparateXYZ", Vector=geo.outputs["Normal"]).outputs["Z"]
        nm = N.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=5.0, Detail=6.0)
        moss = N.math("MULTIPLY", N.n("ShaderNodeMapRange", Value=nz, **{"From Min": 0.55, "From Max": 0.95}).outputs[0],
                      N.n("ShaderNodeMapRange", Value=nm.outputs["Fac"], **{"From Min": 0.5, "From Max": 0.62}).outputs[0])
        c = N.mix(N.math("MULTIPLY", moss, 0.85), c, _lin((0.22, 0.30, 0.08)))
        N.link(c, bs.inputs["Base Color"])
        hb = N.math("ADD", N.math("MULTIPLY", ns.outputs["Fac"], 0.6), N.math("MULTIPLY", nf.outputs["Fac"], 0.25))
        N.link(N.n("ShaderNodeBump", Strength=0.35, Distance=0.05, Height=hb).outputs[0], bs.inputs["Normal"])
        N.set(bs.inputs["Roughness"], 0.78)
    elif name == "mech":
        ns = N.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=3.0, Detail=6.0)
        nf = N.n("ShaderNodeTexVoronoi", Vector=tc.outputs["Object"], Scale=90.0)
        nn = N.n("ShaderNodeTexNoise", Vector=tc.outputs["Object"], Scale=160.0, Detail=3.0)
        c = N.ramp(ns.outputs["Fac"], [(0.3, _lin((0.16, 0.26, 0.05))), (0.5, _lin((0.24, 0.34, 0.07))), (0.7, _lin((0.33, 0.40, 0.10))), (0.85, _lin((0.28, 0.33, 0.09)))])
        c = N.mix(N.math("MULTIPLY", nf.outputs["Distance"], 0.6), c, _lin((0.10, 0.16, 0.04)))
        N.link(c, bs.inputs["Base Color"])
        hb = N.math("ADD", N.math("MULTIPLY", nf.outputs["Distance"], -1.0), N.math("MULTIPLY", nn.outputs["Fac"], 0.5))
        N.link(N.n("ShaderNodeBump", Strength=0.6, Distance=0.01, Height=hb).outputs[0], bs.inputs["Normal"])
        N.set(bs.inputs["Roughness"], 0.95)
        N.set(bs.inputs["Sheen Weight"], 0.6)
        N.set(bs.inputs["Sheen Tint"], _lin((0.75, 0.9, 0.5)))
    elif name in ("platek", "platek_rozowy"):
        uv = N.n("ShaderNodeUVMap", _uv_map="UVMap")
        sep = N.n("ShaderNodeSeparateXYZ", Vector=uv.outputs[0])
        tip = (0.97, 0.80, 0.86) if name == "platek_rozowy" else (0.98, 0.96, 0.95)
        c = N.ramp(sep.outputs["Y"], [(0.0, _lin((0.95, 0.90, 0.62))), (0.25, _lin((0.98, 0.96, 0.93))), (1.0, _lin(tip))])
        N.link(c, bs.inputs["Base Color"])
        N.set(bs.inputs["Roughness"], 0.45)
        N.set(bs.inputs["Subsurface Weight"], 0.35)
        tl = N.n("ShaderNodeBsdfTranslucent", Color=c)
        mx = N.n("ShaderNodeMixShader", Fac=0.25)
        N.link(bs.outputs[0], mx.inputs[1])
        N.link(tl.outputs[0], mx.inputs[2])
        sh = mx.outputs[0]
    elif name == "precik":
        N.set(bs.inputs["Base Color"], _lin((0.95, 0.72, 0.10)))
        N.set(bs.inputs["Roughness"], 0.6)
    elif name in ("trawa_zdzblo", "trawa_ozdobna", "trawa_sucha", "palma_lisc", "palma_sucha", "bambus_lisc", "lodyga"):
        # źdźbła / listki z geometrii: przejście kolorów wzdłuż (UV v), zmienność na źdźbło (rnd), przeświecanie
        uv = N.n("ShaderNodeUVMap", _uv_map="UVMap")
        sep = N.n("ShaderNodeSeparateXYZ", Vector=uv.outputs[0])
        at = N.n("ShaderNodeAttribute", _attribute_name="rnd").outputs["Fac"]
        cols = {
            "trawa_zdzblo": ((0.10, 0.18, 0.04), (0.22, 0.34, 0.07), (0.34, 0.42, 0.12)),
            "trawa_ozdobna": ((0.18, 0.26, 0.07), (0.38, 0.48, 0.14), (0.62, 0.58, 0.30)),
            "trawa_sucha": ((0.36, 0.30, 0.17), (0.62, 0.52, 0.32), (0.74, 0.66, 0.46)),
            "palma_lisc": ((0.12, 0.24, 0.06), (0.16, 0.32, 0.07), (0.20, 0.36, 0.09)),
            "palma_sucha": ((0.38, 0.30, 0.16), (0.52, 0.42, 0.24), (0.60, 0.50, 0.30)),
            "bambus_lisc": ((0.18, 0.30, 0.07), (0.24, 0.38, 0.09), (0.30, 0.42, 0.12)),
            "lodyga": ((0.30, 0.36, 0.22), (0.38, 0.42, 0.28), (0.42, 0.46, 0.30)),
        }[name]
        c = N.ramp(sep.outputs["Y"], [(0.0, _lin(cols[0])), (0.45, _lin(cols[1])), (1.0, _lin(cols[2]))])
        hsv = N.n("ShaderNodeHueSaturation", Hue=N.math("MULTIPLY_ADD", at, 0.05, 0.475), Saturation=N.math("MULTIPLY_ADD", at, 0.3, 0.85),
                  Value=N.math("MULTIPLY_ADD", N.math("FRACT", N.math("MULTIPLY", at, 7.3)), 0.4, 0.8), Fac=1.0, Color=c)
        c = hsv.outputs[0]
        if name in ("palma_lisc", "bambus_lisc"):
            # nerw środkowy listka (UV u = 0.5)
            mid = N.n("ShaderNodeMapRange", Value=N.math("ABSOLUTE", N.math("SUBTRACT", sep.outputs["X"], 0.5)), **{"From Min": 0.0, "From Max": 0.06, "To Min": 1.0, "To Max": 0.0}).outputs[0]
            c = N.mix(N.math("MULTIPLY", mid, 0.5), c, _lin((0.42, 0.50, 0.20)))
        N.link(c, bs.inputs["Base Color"])
        N.set(bs.inputs["Roughness"], 0.45 if name.startswith("palma") else 0.62)
        N.set(bs.inputs["Specular IOR Level"], 0.3 if name.startswith("trawa") else 0.45)
        tl = N.n("ShaderNodeBsdfTranslucent", Color=N.mix(1.0, c, (1.2, 1.3, 0.6, 1.0), "MULTIPLY"))
        mx = N.n("ShaderNodeMixShader", Fac=0.3 if name != "lodyga" else 0.1)
        N.link(bs.outputs[0], mx.inputs[1])
        N.link(tl.outputs[0], mx.inputs[2])
        sh = mx.outputs[0]
    elif name == "wlokna":
        # włókniste nasady liści palmy
        ns = N.n("ShaderNodeTexNoise", Vector=N.n("ShaderNodeMapping", Vector=tc.outputs["Object"], Scale=(30.0, 30.0, 3.0)).outputs[0], Scale=4.0, Detail=8.0)
        N.link(N.ramp(ns.outputs["Fac"], [(0.3, _lin((0.18, 0.13, 0.08))), (0.7, _lin((0.42, 0.32, 0.20)))]), bs.inputs["Base Color"])
        N.link(N.n("ShaderNodeBump", Strength=0.8, Height=ns.outputs["Fac"]).outputs[0], bs.inputs["Normal"])
        N.set(bs.inputs["Roughness"], 0.95)
    else:
        N.set(bs.inputs["Base Color"], _lin((0.5, 0.5, 0.5)))
    N.out(sh)
    ctx.cache[key] = m
    return m


def _material(ctx, key):
    """Klucz materiału z Geo → materiał Blendera."""
    kind, _, arg = key.partition(":")
    if kind == "kora":
        return _mat_bark(ctx, arg)
    if kind == "lisc":
        atlas, _, sh = arg.partition("/")
        return _mat_leaf(ctx, atlas, sh or atlas)
    return _mat_simple(ctx, key)



# =====================================================================================================
#  GATUNKI DRZEW
# =====================================================================================================

UP = np.array([0.0, 0.0, 1.0])

# wartości domyślne (opis w komentarzach); gatunki nadpisują wybrane
_D = dict(
    cb=0.25, env=(0.45, 0.3, 2.0, 2.0), core=0.12,     # podstawa korony (ułamek h), obwiednia (szczyt, podstawa, wykł. dołu, góry)
    stems=(1, 1), sang=(8, 18), tl=0.9,                # liczba pni, ich rozchylenie (°), długość pnia (ułamek h)
    lean=3.0, tw=0.03, tup=0.06, tr=0.02,              # pochylenie (°), falowanie, prostowanie, promień pnia (ułamek h)
    lobes=0.06, flare=0.35, twist=0.0,                 # nieregularny przekrój, rozszerzenie nasady, skręcenie pnia
    n1=(10, 14), t1=1.0, a1=(65, 30), rot1="spiral", w1=0.08, up1=0.05, g1=0.04, f1=0.0, len1=(0.85, 1.0), c1=0.0,
    d2=4.0, t2=0.15, a2=(50, 45), rot2="spiral", w2=0.12, up2=0.04, g2=0.05, f2=0.0, r2=0.65, m2=3.0,
    d3=8.0, t3=0.12, a3=(48, 40), rot3="flat", w3=0.14, up3=0.03, g3=0.05, f3=0.0, r3=0.5, m3=0.5,
    d4=14.0, a4=(45, 40), m4=0.16,
    seg=(24, 12, 6, 3, 3), sides=(14, 8, 5, 3, 3),
    leaf="lipa", ls=0.08, sl=0.25, single_h=5.0, ldens=14.0, lmax=24000, lpet=(60, 15), ldroop=0.15,
    lup=1.0, lout=0.5, lrnd=0.6, fold=0.12, curl=0.06, lphyl="flat", l2=0.25, ldens2=6.0,
    kepa=0.8, kfar=5.0, kmax_far=3600,                 # karty kęp dalekiego planu: rozmiar, warstwy, limit
    bark="lipa", decid=True, rtip=0.0016,
    href=10.0, o2=0.35, o3=0.25, kleaf=3.0,           # wysokość odniesienia gęstości, odchylenie na zewnątrz, warstwy liści
)

SP = {
    # lipa drobnolistna: gęsta, szeroko jajowata korona
    "lipa": dict(
        cb=0.22, env=(0.40, 0.45, 2.0, 2.3), tl=0.78, tr=0.021, href=10.0,
        n1=(16, 22), a1=(72, 20), w1=0.09, up1=0.07, g1=0.05,
        d2=4.5, a2=(55, 45), r2=0.7, m2=3.2, d3=9.0, a3=(50, 42), m3=0.55,
        leaf="lipa", ls=0.10, sl=0.30, single_h=6.0, lmax=15000, bark="lipa"),
    # klon zwyczajny (zieleń działki): kulista, gęsta korona, rozgałęzienia naprzeciwległe
    "klon_zielony": dict(
        cb=0.22, env=(0.45, 0.5, 2.2, 2.0), tl=0.55, tr=0.02, href=9.0, kleaf=3.6,
        n1=(16, 22), a1=(66, 15), rot1="spiral", w1=0.1, up1=0.05, g1=0.04,
        d2=5.0, a2=(52, 42), rot2="opposite", r2=0.75, m2=3.0, d3=9.0, rot3="opposite",
        leaf="klon_zielony", ls=0.13, sl=0.34, single_h=5.0, lmax=20000, bark="klon_zielony"),
    # klon palmowy: niski, wielopniowy, parasolowata korona, warstwy liści
    "klon": dict(
        cb=0.14, env=(0.62, 0.35, 1.6, 2.6), core=0.2, stems=(1, 3), sang=(10, 26), tl=0.5, lean=8, tw=0.07, tup=0.03,
        tr=0.017, href=4.5, o2=0.45, o3=0.3, rtip=0.0013,
        n1=(6, 9), a1=(66, 16), w1=0.13, up1=0.03, g1=0.02, c1=0.2,
        d2=6.0, t2=0.12, a2=(58, 50), rot2="opposite", w2=0.15, up2=0.0, g2=0.03, f2=0.6, r2=0.75, m2=1.8,
        d3=12.0, a3=(55, 50), rot3="opposite", w3=0.16, up3=0.0, g3=0.04, f3=0.35, m3=0.35,
        leaf="klon", ls=0.085, sl=0.24, single_h=7.0, lmax=13000, lpet=(70, 12), ldroop=0.05, lup=1.6, lout=0.3,
        lrnd=0.45, fold=0.08, l2=0.5, bark="klon"),
    # brzoza brodawkowata: smukła, ażurowa, zwisające gałązki
    "brzoza": dict(
        cb=0.32, env=(0.36, 0.3, 1.8, 1.5), core=0.15, tl=0.93, lean=4, tw=0.025, tup=0.1, tr=0.012, href=10.0,
        rtip=0.0011, kepa=0.6, kfar=3.0,
        n1=(18, 26), a1=(52, 25), w1=0.08, up1=0.10, g1=0.07, len1=(0.6, 1.0),
        d2=5.0, t2=0.2, a2=(48, 38), w2=0.10, up2=0.0, g2=0.32, r2=0.7, m2=2.2,
        d3=8.0, t3=0.15, a3=(38, 30), rot3="spiral", w3=0.06, up3=-0.1, g3=0.65, gp3=0.8, r3=0.75, m3=0.85,
        leaf="brzoza", ls=0.065, sl=0.24, single_h=4.5, lmax=20000, lpet=(45, 15), ldroop=0.6, lup=0.4, lout=0.6,
        lrnd=1.0, fold=0.06, l2=0.12, bark="brzoza", kleaf=1.9),
    # oliwka: krępy, skręcony pień, szeroka nieregularna korona, srebrzyste wąskie liście
    "oliwka": dict(
        cb=0.4, env=(0.45, 0.55, 2.0, 2.0), core=0.2, stems=(1, 3), sang=(10, 22), tl=0.42, lean=10, tw=0.09,
        tup=0.02, tr=0.04, lobes=0.16, flare=0.35, twist=2.5, href=4.5, o2=0.5, o3=0.3, rtip=0.0013, kepa=0.6,
        n1=(6, 9), a1=(64, 24), w1=0.14, up1=0.02, g1=0.02, c1=0.2,
        d2=6.0, a2=(50, 40), w2=0.18, up2=0.03, g2=0.06, r2=0.7, m2=1.6,
        d3=12.0, a3=(50, 40), rot3="spiral", w3=0.15, g3=0.08, m3=0.3,
        leaf="oliwka", ls=0.075, sl=0.20, single_h=2.5, lmax=16000, lpet=(50, 15), ldroop=0.25, lup=0.7, lout=0.5,
        lrnd=0.9, fold=0.04, lphyl="spiral", l2=0.45, bark="oliwka", decid=False),
    # sosna: zwyczajna (wysoka, korona w górze) albo japońska (niska, poziome piętra) – patrz _pine_params
    "sosna": dict(
        cb=0.55, env=(0.45, 0.4, 1.6, 2.6), core=0.15, tl=0.92, lean=4, tw=0.03, tup=0.08, tr=0.016, href=10.0,
        rtip=0.003, kepa=1.0,
        n1=(14, 20), rot1="whorl", a1=(84, 50), w1=0.10, up1=0.06, g1=0.03, c1=0.15,
        d2=3.5, t2=0.2, a2=(55, 50), rot2="flat", w2=0.12, up2=0.06, g2=0.03, f2=0.4, r2=0.6, m2=1.6,
        d3=14.0, t3=0.25, a3=(40, 35), rot3="spiral", w3=0.1, up3=0.10, g3=0.0, r3=0.5, m3=0.35,
        leaf="igly", bark="sosna", decid=False),
    # cytrus w donicy: pień jak lizak, kulista gęsta korona
    "cytrus": dict(
        cb=0.5, env=(0.5, 0.3, 2.0, 2.0), core=0.2, tl=0.8, lean=2, tw=0.012, tup=0.12, tr=0.014, flare=0.1, href=2.0,
        o2=0.5, o3=0.4, rtip=0.0015, seg=(10, 8, 6, 4, 3), sides=(9, 6, 4, 3, 3),
        n1=(6, 9), a1=(65, 35), w1=0.12, up1=0.06, g1=0.02, c1=0.2,
        d2=20.0, a2=(50, 45), w2=0.15, r2=0.7, m2=0.5, d3=30.0, a3=(50, 45), m3=0.15, rot3="spiral",
        leaf="cytrus", ls=0.10, single_h=9.0, lmax=4000, lpet=(55, 15), ldroop=0.1, lup=0.8, lout=0.8, lrnd=0.7,
        fold=0.10, lphyl="spiral", l2=0.5, bark="cytrus", decid=False),
    # krzew w donicy (bukszpan / mirt): wiele pędów, kulisty
    "krzew": dict(
        cb=0.0, env=(0.45, 0.5, 1.8, 2.0), core=0.3, stems=(5, 8), sang=(18, 38), tl=0.45, lean=4, tw=0.08, tr=0.02,
        flare=0.0, lobes=0.0, href=0.8, o2=0.5, o3=0.4, rtip=0.0012, seg=(6, 5, 4, 3, 3), sides=(5, 4, 3, 3, 3),
        n1=(3, 5), a1=(40, 25), w1=0.15, up1=0.08, d2=10.0, a2=(45, 40), m2=0.35, d3=18.0, m3=0.14, rot3="spiral",
        leaf="bukszpan", ls=0.035, sl=0.12, single_h=0.5, lmax=7000, lpet=(50, 15), ldroop=0.05, lup=0.7, lout=0.9,
        lrnd=0.8, fold=0.1, lphyl="spiral", l2=0.6, bark="bukszpan", decid=False),
}
DECID = ("klon", "klon_zielony", "brzoza", "lipa")


def _pine_params(h):
    """Sosna japońska (niska, ogród) albo zwyczajna (wysoka, działka)."""
    P = dict(_D)
    P.update(SP["sosna"])
    if h < 5.0:
        P.update(cb=0.3, env=(0.4, 0.75, 1.6, 1.6), core=0.3, tl=0.88, lean=14, tw=0.07, tup=0.02, tr=0.026, n1=(6, 8),
                 href=3.0, rot1="spiral", a1=(96, 70), w1=0.06, up1=0.0, g1=0.01, c1=0.35, len1=(0.85, 1.0),
                 d2=10.0, t2=0.45, a2=(62, 55), f2=0.85, up2=0.0, g2=0.0, r2=0.6, m2=0.35,
                 d3=18.0, t3=0.1, m3=0.12, f3=0.4, up3=0.1, lobes=0.08, flare=0.25)
    return P


def _params(kind, h):
    if kind == "sosna":
        return _pine_params(h)
    P = dict(_D)
    P.update(SP[kind])
    return P


def _skeleton(P, h, r, env, rng, lvls):
    """Szkielet: lvls poziomów (pień + konary + gałęzie + gałązki …)."""
    # małe drzewo ≈ pomniejszone duże: gęstość rozgałęzień na metr rośnie odwrotnie do wielkości
    ds = float(np.clip((P["href"] / max(h, 0.3)) ** 0.75, 0.6, 3.0))
    ns = int(rng.integers(P["stems"][0], P["stems"][1] + 1))
    az = rng.uniform(0, 2 * math.pi) + np.arange(ns) * 2 * math.pi / ns + rng.normal(0, 0.3, ns)
    spread = np.radians(rng.uniform(*P["sang"], ns)) if ns > 1 else np.zeros(1)
    la = rng.uniform(0, 2 * math.pi)
    lean = math.radians(rng.uniform(0.3, 1.0) * P["lean"])
    D0 = np.stack([np.sin(spread) * np.cos(az), np.sin(spread) * np.sin(az), np.cos(spread)], 1)
    D0 += np.array([math.sin(lean) * math.cos(la), math.sin(lean) * math.sin(la), 0])
    off = 0.025 * h * min(1.0, 0.5 + 0.2 * ns) if ns > 1 else 0.0
    S0 = np.stack([np.cos(az) * off, np.sin(az) * off, np.full(ns, -0.12)], 1)
    L0 = P["tl"] * h * rng.uniform(0.9, 1.04, ns) * (np.where(np.arange(ns) == 0, 1.0, rng.uniform(0.75, 0.95, ns)) if ns > 1 else 1)
    P0, L0 = _grow(S0, D0, L0, P["seg"][0], rng, None, P["tw"], P["tup"], 0.0, clip=False)
    # wierzchołek pnia nie dalej niż ~0,35 r od osi (inaczej korona wypada z obwiedni)
    off = np.hypot(P0[:, -1, 0], P0[:, -1, 1])
    f = np.minimum(1.0, 0.35 * r / np.maximum(off, 1e-6))
    P0[:, :, :2] = P0[:, :1, :2] + (P0[:, :, :2] - P0[:, :1, :2]) * f[:, None, None]
    L0 = np.linalg.norm(np.diff(P0, axis=1), axis=2).sum(1)
    levels = [Lv(P0, L0, np.full(ns, -1), np.zeros(ns), 0)]
    if lvls < 2:
        return levels
    # konary
    n1 = rng.integers(P["n1"][0], P["n1"][1] + 1, ns)
    if ns > 1:
        n1 = np.maximum(2, (n1 * (0.65 + 0.35 / ns)).astype(int))
    t0 = np.clip((P["cb"] * h + 0.12) / np.maximum(L0, 1e-3), 0.03, 0.9)
    idx, t, pos, D = _spawn(levels[0], n1, t0, P["t1"], rng, P["a1"], P["rot1"], flat_bias=P["f1"])
    # przewodnik: najwyżej osadzona gałąź każdego pnia rośnie ku szczytowi korony
    order = np.lexsort((t, idx))
    last = order[np.r_[np.diff(idx[order]) != 0, True]]
    if P["tl"] < 0.85 and len(last):
        tip_t = levels[0].T[idx[last], -1] if levels[0].T is not None else _frames(levels[0].P)[0][idx[last], -1]
        top = np.array([0.0, 0.0, env.h]) - pos[last]
        D[last] = _nz(_nz(top) * 1.2 + tip_t * 0.5 + rng.normal(0, 0.08, (len(last), 3)))
    L1 = env.raylen(pos, D, np.full(len(idx), 2.4 * r + 0.3 * h)) * rng.uniform(*P["len1"], len(idx))
    if P["tl"] < 0.85 and len(last):
        L1[last] = env.raylen(pos[last], D[last], np.full(len(last), 1.2 * h)) * 0.97
    P1, L1 = _grow(pos, D, L1, P["seg"][1], rng, env, P["w1"], P["up1"], P["g1"], flat=P["f1"], curl=P["c1"])
    levels.append(Lv(P1, L1, idx, t, 1))
    # gałęzie i gałązki
    for li in range(2, lvls):
        pa = levels[-1]
        k = str(li) if li < 4 else "4"
        if li < 4:
            d, tt, a, rot = P["d" + k], P["t" + k], P["a" + k], P["rot" + k]
            w, up, g, f, rr, mm = P["w" + k], P["up" + k], P["g" + k], P["f" + k], P["r" + k], P["m" + k]
            ob = P["o" + k]
        else:
            d, tt, a, rot, w, up, g, f, rr, mm, ob = P["d4"], 0.15, P["a4"], "spiral", 0.15, 0.0, 0.05, 0.0, 0.5, P["m4"], 0.2
        cnt = rng.poisson(d * ds * pa.L)
        if li == 2:
            cnt = np.maximum(cnt, 1)
        mm = mm * min(1.0, h / P["href"]) ** 0.5
        idx, t, pos, D = _spawn(pa, cnt, tt, 1.0, rng, a, rot, flat_bias=f, outward=ob)
        if len(idx) == 0:
            levels.append(Lv(np.zeros((0, P["seg"][li] + 1, 3)), np.zeros(0), idx, t, li))
            continue
        rem = pa.L[idx] * (1 - t)
        Lr = np.minimum(rr * rem + 0.12 * mm, mm) * rng.uniform(0.7, 1.1, len(idx))
        Lr = np.minimum(Lr, env.raylen(pos, D, np.maximum(Lr, 0.05)) * 1.05)
        Pn, Ln = _grow(pos, D, Lr, P["seg"][li], rng, env, w, up, g, gpow=P.get("gp" + k, 1.3), flat=f)
        levels.append(Lv(Pn, Ln, idx, t, li))
    return levels


def _trunk_lobes(P, h0, rng):
    amp, flare, tw = P["lobes"], P["flare"], P["twist"]
    ph = rng.uniform(0, 2 * math.pi, 4)

    def f(th, Pp):
        z = np.maximum(Pp[:, :, 2:3], 0.0)
        zr = z / max(h0, 1e-3)
        a = amp * (0.4 + 0.6 * np.exp(-z / 0.6)) + 0.18 * np.exp(-z / 0.25) * (flare > 0.2)
        tt = th[None, None, :] + tw * zr
        m = 1 + a * (0.6 * np.sin(3 * tt + ph[0]) + 0.4 * np.sin(5 * tt + ph[1]) + 0.3 * np.sin(2 * tt + ph[2]))
        return m * (1 + flare * np.exp(-z / 0.22))
    return f


def _foliage_cards(G, lv, P, rng, atlas, mat, size, dens, budget, t0=0.15, tip=True, cols=3, rows=2,
                   phyl=None, pet=None, droop=None, up=None, out=None, rnd=None, fold=None, curl=None, cells=None, sel=None,
                   center=False):
    """Karty liści rozłożone wzdłuż gałązek poziomu lv."""
    if lv.M == 0:
        return 0
    L = lv.L if sel is None else np.where(sel, lv.L, 0.0)
    Ltot = float(L.sum())
    if Ltot <= 0:
        return 0
    d = min(dens, budget / Ltot)
    cnt = rng.poisson(d * L)
    if tip:
        cnt = np.where(L > 0, np.maximum(cnt, 1), 0)
    idx = np.repeat(np.arange(lv.M), cnt)
    n = len(idx)
    if n == 0:
        return 0
    k = np.arange(n) - np.repeat(np.cumsum(cnt) - cnt, cnt)
    c = cnt[idx]
    t = t0 + (1 - t0) * (k + rng.uniform(0.15, 0.85, n)) / c
    last = (k == c - 1) & tip
    t = np.where(last, 1.0, t)
    pos, T, N, B = lv.at(idx, t)
    phyl = phyl or P["lphyl"]
    if phyl == "flat":
        hz = np.cross(UP, T)
        hz = np.where(np.linalg.norm(hz, axis=1, keepdims=True) < 1e-3, N, hz)
        sgn = np.where(k % 2 == 0, 1.0, -1.0)[:, None]
        side = _nz(_nz(hz) * sgn + rng.normal(0, 0.35, (n, 3)))
    else:
        psi = rng.uniform(0, 2 * math.pi, lv.M)[idx] + k * 2.4
        side = np.cos(psi)[:, None] * N + np.sin(psi)[:, None] * B
    side = _nz(side - (side * T).sum(1, keepdims=True) * T)
    pm, ps = pet or P["lpet"]
    beta = np.radians(rng.normal(pm, ps, n))
    beta = np.where(last, np.radians(rng.uniform(0, 25, n)), beta)
    U = np.cos(beta)[:, None] * T + np.sin(beta)[:, None] * side
    U[:, 2] -= (P["ldroop"] if droop is None else droop) * rng.uniform(0.4, 1.6, n)
    U = _nz(U)
    radial = np.concatenate([pos[:, :2], np.zeros((n, 1))], 1)
    radial = _nz(radial + 1e-4)
    pref = (UP * (P["lup"] if up is None else up) + radial * (P["lout"] if out is None else out)
            + rng.normal(0, 1, (n, 3)) * (P["lrnd"] if rnd is None else rnd))
    ac, ar, cw, chh = ATLAS[atlas]
    Ls = size * rng.uniform(0.78, 1.15, n)
    W = Ls * cw / chh
    cl = rng.choice(cells if cells is not None else np.arange(ac * ar), n)
    fo = (P["fold"] if fold is None else fold) * rng.uniform(0.4, 1.5, n)
    cu = (P["curl"] if curl is None else curl) * rng.uniform(0.0, 1.5, n)
    if center:
        pos = pos - U * Ls[:, None] * 0.5
    _cards(G, pos, U, pref, Ls, W, cl, atlas, mat, cols, rows, fold=fo, curl=cu, rnd=rng.random(n))
    return n


def _sphere_tpl(sub=1):
    """Ikosfera (wierzchołki, trójkąty) – szablon do owoców."""
    t = (1 + 5 ** 0.5) / 2
    V = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
         (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
         (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    V = [np.array(v, float) / np.linalg.norm(v) for v in V]
    for _ in range(sub):
        cache, F2 = {}, []

        def mid(a, b):
            k = (min(a, b), max(a, b))
            if k not in cache:
                m = V[a] + V[b]
                V.append(m / np.linalg.norm(m))
                cache[k] = len(V) - 1
            return cache[k]
        for a, b, c in F:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            F2 += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        F = F2
    return np.array(V), np.array(F, np.int32)


def _spheres(G, C, R, mat, sub=1, scale=(1, 1, 1), jitter=0.0, rng=None):
    V0, F0 = _sphere_tpl(sub)
    K = len(C)
    if K == 0:
        return
    V = V0[None] * np.asarray(scale)[None, None]
    if jitter and rng is not None:
        V = V * (1 + rng.normal(0, jitter, (K, len(V0), 1)))
    V = C[:, None, :] + V * R[:, None, None]
    F = (F0[None] + (np.arange(K) * len(V0))[:, None, None]).reshape(-1, 3)
    G.add(V.reshape(-1, 3), F, None, mat)


def _lathe(G, prof, sides, mat, center=(0, 0, 0), rot=0.0, close_top=False):
    """Bryła obrotowa z profilu [(r, z), ...] (od dołu do góry)."""
    prof = np.asarray(prof, float)
    th = np.linspace(0, 2 * math.pi, sides, endpoint=False) + rot
    V = np.stack([np.cos(th)[None] * prof[:, :1], np.sin(th)[None] * prof[:, :1], np.broadcast_to(prof[:, 1:2], (len(prof), sides))], -1)
    V = V.reshape(-1, 3) + np.asarray(center)
    i = np.arange(len(prof) - 1)[:, None] * sides
    j = np.arange(sides)[None]
    j1 = (j + 1) % sides
    q = np.stack([i + j, i + j1, i + sides + j1, i + sides + j], -1).reshape(-1, 4)
    G.add(V, q, None, mat)


def _disc(G, r, z, sides, mat, center=(0, 0), bump=0.0, rng=None, rings=3):
    """Płaski (lekko wypukły) krążek – ziemia w donicy."""
    rr = np.linspace(0, r, rings + 1)[1:]
    th = np.linspace(0, 2 * math.pi, sides, endpoint=False)
    V = [(center[0], center[1], z + bump)]
    for k, ra in enumerate(rr):
        zz = z + bump * (1 - (ra / r) ** 2)
        for a in th:
            V.append((center[0] + ra * math.cos(a), center[1] + ra * math.sin(a), zz))
    V = np.array(V)
    F = [(0, 1 + (j + 1) % sides, 1 + j) for j in range(sides)]
    Q = []
    for k in range(rings - 1):
        b0, b1 = 1 + k * sides, 1 + (k + 1) * sides
        for j in range(sides):
            j1 = (j + 1) % sides
            Q.append((b0 + j, b0 + j1, b1 + j1, b1 + j))
    G.add(V, np.array([(a, c, b) for a, b, c in F]), None, mat)
    if Q:
        G.add(V, np.array(Q)[:, ::-1], None, mat)



def _build_tree(kind, h, r, lod, season, var):
    """Geometria jednego wariantu drzewa (w układzie lokalnym, nasada w (0,0,0))."""
    far = lod == "daleko"
    P = _params(kind, h)
    rng = np.random.default_rng(zlib.crc32(f"{kind}|{lod}|{h:.3f}|{r:.3f}|{var}".encode()))
    G = Geo()
    winter = season == "zima" and kind in DECID
    z0 = 0.0
    if kind == "cytrus":
        z0 = _pot(G, r, rng, h)            # donica, drzewko rośnie z ziemi w donicy
    elif kind == "krzew":
        z0 = 0.0
    single = (h <= P["single_h"]) and not far
    if kind == "sosna":
        lsize = 0.22 if not far else P["kepa"]
    else:
        lsize = (P["ls"] if single else P["sl"]) if not far else P["kepa"]
    hh = h - z0
    margin = lsize * (0.55 if not far else 0.45)
    env = Env(hh - margin, max(0.15, r - margin), P["cb"] * hh, *P["env"], core=P["core"])
    lvls = 3 if far else 4
    if winter and not far:
        P = dict(P, d3=P["d3"] * 1.5)
    if far:
        P = dict(P, d2=P["d2"] * 0.6, seg=(12, 8, 4, 3, 3))
    elif not winter and kind != "sosna":
        # latem gałązki schowane w liściach: krótsze rurki
        sg = P["seg"]
        P = dict(P, seg=(sg[0], sg[1], sg[2], min(sg[3], 2), sg[4]))
    levels = _skeleton(P, hh, r, env, rng, lvls)
    _pipe(levels, P["rtip"])
    _rescale_radii(levels, P["rtip"], P["tr"] * hh)
    sides = P["sides"] if not far else (max(6, P["sides"][0] // 2), 4, 3, 3, 3)
    if h > 8 and not far:
        sides = sides[:2] + (min(sides[2], 4),) + sides[3:]
    if winter and not far:
        sides = sides[:2] + (max(4, sides[2]), 3, 3)
    bark = "kora:" + P["bark"]
    for li, lv in enumerate(levels):
        if lv.M == 0:
            continue
        Pp = lv.P.copy()
        Pp[:, :, 2] += z0
        kofs = rng.uniform(0, 50, (lv.M, 3))
        lob = _trunk_lobes(P, hh, rng) if li == 0 else None
        R = np.maximum(lv.R, P["rtip"] * 0.8)
        if far and li == 2:
            R = R * 1.4          # z daleka cienkie gałązki znikają – lekko pogrubione
        _tubes(G, Pp, R, sides[min(li, 4)], bark, lobes=lob, kofs=kofs, h0=hh)
    shift = np.array([0, 0, z0])
    for lv in levels:
        lv.P = lv.P + shift
        lv.T = None
    if kind == "sosna":
        _pine_foliage(G, levels, P, rng, far, h)
    elif not winter:
        sp = P["leaf"]
        if far:
            ka = "kepa_" + sp if "kepa_" + sp in ATLAS else "spray_" + sp
            mat = f"lisc:{ka}/{sp}"
            ksz = P["kepa"] * min(1.6, max(0.7, h / 11))
            area = 2 * math.pi * r * hh * (1 - P["cb"]) * 0.75
            target = min(P["kmax_far"], P["kfar"] * area / (ksz * ksz * 0.5))
            _foliage_cards(G, levels[2], P, rng, ka, mat, ksz, 1e9, target * 0.85, t0=0.25, cols=2, rows=2,
                           pet=(40, 20), droop=0.1, up=0.6, out=0.9, rnd=1.0, fold=0.0, curl=0.1)
            _foliage_cards(G, levels[1], P, rng, ka, mat, ksz * 0.9, 1e9, target * 0.15, t0=0.45, tip=False, cols=2,
                           rows=2, pet=(50, 20), up=0.6, out=0.9, rnd=1.0, fold=0.0)
        else:
            atlas = ("liscie_" if single else "spray_") + sp
            mat = f"lisc:{atlas}/{sp}"
            size = P["ls"] if single else P["sl"]
            ac, ar, cw, chh = ATLAS[atlas]
            # liczba kart z powierzchni korony: kleaf warstw liści
            area = 2 * math.pi * r * hh * (1 - P["cb"]) * 0.75
            target = min(P["lmax"], P["kleaf"] * area / (size * size * cw / chh * 0.45))
            cr, rw = (3, 2) if single else (2, 3)
            _foliage_cards(G, levels[3], P, rng, atlas, mat, size, 1e9, target * (1 - P["l2"]) * 0.95, cols=cr, rows=rw)
            _foliage_cards(G, levels[2], P, rng, atlas, mat, size, 1e9, target * P["l2"], t0=0.3, cols=cr, rows=rw)
            _foliage_cards(G, levels[1], P, rng, atlas, mat, size, 1e9, target * 0.05, t0=0.85, cols=cr, rows=rw)
    elif far:
        # zima z daleka: nieliczne rzadkie karty drobnych gałązek (mgiełka korony); z bliska tylko geometria
        cell = np.array([1 if kind == "brzoza" else 0])
        sz = min(1.6, max(0.7, h / 9)) * 0.9
        _foliage_cards(G, levels[-1], P, rng, "galazki", "lisc:galazki/galazki", sz, 1e9, 260, t0=0.6, cols=2, rows=2,
                       pet=(25, 15), droop=0.3 if kind == "brzoza" else 0.0, up=0.2, out=1.0, rnd=0.8, fold=0.0,
                       curl=0.0, cells=cell)
    if kind == "cytrus":
        _fruits(G, levels, rng, r, h, z0)
    return G


def _pine_foliage(G, levels, P, rng, far, h):
    """Igły sosny: pędy-szczotki na gałązkach, rozety na końcach (płaskie „poduszki”), kępy z daleka."""
    mat = "lisc:igly/igly"
    jap = h < 5.0
    if far:
        lv = levels[2]
        sz = 1.0 * min(1.4, h / 14 + 0.4)
        _foliage_cards(G, lv, P, rng, "igly", mat, sz, 1e9, 1100, t0=0.3, cols=2, rows=2, phyl="spiral", pet=(30, 20),
                       droop=0.0, up=0.9, out=0.6, rnd=0.8, fold=0.0, curl=0.0, cells=np.array([3]))
        _foliage_cards(G, lv, P, rng, "igly", mat, sz * 0.8, 1e9, 400, t0=0.85, cols=2, rows=2, phyl="spiral",
                       pet=(85, 5), droop=0.0, up=3.0, out=0.0, rnd=0.3, fold=0.0, curl=0.0, cells=np.array([1]), center=True)
        return
    lv3, lv2 = levels[3], levels[2]
    s = float(np.clip(0.12 + 0.012 * h, 0.14, 0.26))
    n3 = max(lv3.M, 1)
    if jap:
        _pine_pads(G, levels, rng, h, mat)
        _foliage_cards(G, lv3, P, rng, "igly", mat, s, 1e9, min(3000, n3 * 4), t0=0.0, cols=2, rows=3,
                       phyl="spiral", pet=(35, 14), droop=-0.1, up=0.8, out=0.4, rnd=1.0, fold=0.0, curl=-0.06, cells=np.array([0]))
        return
    # szczotki igieł wzdłuż pędów
    _foliage_cards(G, lv3, P, rng, "igly", mat, s, 1e9, min(9000, n3 * 7), t0=0.0, cols=2, rows=3,
                   phyl="spiral", pet=(32, 14), droop=-0.1, up=0.5, out=0.4, rnd=1.2, fold=0.0, curl=-0.06, cells=np.array([0]))
    # rozety na końcach – płaskie piętra igieł od góry
    _foliage_cards(G, lv3, P, rng, "igly", mat, s * 1.3, 1e9, min(4000, n3 * 1.2), t0=0.92, cols=2, rows=2, phyl="spiral",
                   pet=(85, 5), droop=0.0, up=4.0 if jap else 2.5, out=0.2, rnd=0.35, fold=0.0, curl=0.0,
                   cells=np.array([1]), center=True)
    # gałązki z pędami (wypełnienie wnętrza poduszek)
    _foliage_cards(G, lv2, P, rng, "igly", mat, s * 1.7, 1e9, min(3000, lv2.M * 3), t0=0.35, tip=False, cols=2, rows=3,
                   phyl="spiral", pet=(40, 15), droop=0.0, up=1.5 if jap else 0.8, out=0.5, rnd=0.8, fold=0.0, curl=0.08,
                   cells=np.array([2]))


def _pine_pads(G, levels, rng, h, mat):
    """Płaskie „chmury” igieł na końcach konarów (niwaki): rozety od góry + szczotki na obwodzie."""
    lv1, lv0 = levels[1], levels[0]
    C, PR = [], []
    for m in range(lv1.M):
        L = lv1.L[m]
        for t in (1.0, 0.62):
            if t < 1.0 and L < 0.35:
                continue
            p, _, _, _ = lv1.at(np.array([m]), np.array([t]))
            C.append(p[0])
            PR.append(max(0.16, min(0.5, 0.45 * L + 0.1)) * (1.0 if t == 1.0 else 0.75))
    top = lv0.P[:, -1]
    for p in top:
        C.append(p + np.array([0, 0, 0.04]))
        PR.append(0.22 * h / 2.4)
    C, PR = np.array(C), np.array(PR)
    A, U, N, S, cell = [], [], [], [], []
    for c, pr in zip(C, PR):
        nr = int(14 + 60 * pr)
        a = rng.uniform(0, 2 * math.pi, nr)
        d = pr * np.sqrt(rng.uniform(0, 1, nr))
        pos = c + np.stack([np.cos(a) * d, np.sin(a) * d * 0.85, rng.normal(0, 0.035, nr) + 0.05 * (1 - d / pr)], 1)
        u = np.stack([np.cos(a + 1.3), np.sin(a + 1.3), np.zeros(nr)], 1)
        n = _nz(UP + rng.normal(0, 0.22, (nr, 3)))
        sz = rng.uniform(0.15, 0.22, nr) * min(1.3, max(0.8, h / 2.4))
        A.append(pos - u * sz[:, None] * 0.5)
        U.append(u)
        N.append(n)
        S.append(sz)
        cell.append(np.ones(nr, int))
        # szczotki na obwodzie, skierowane na zewnątrz i lekko w górę
        nb = int(10 + 40 * pr)
        a = rng.uniform(0, 2 * math.pi, nb)
        pos = c + np.stack([np.cos(a) * pr * 0.55, np.sin(a) * pr * 0.5, rng.normal(0, 0.03, nb)], 1)
        u = _nz(np.stack([np.cos(a), np.sin(a), rng.uniform(0.2, 0.6, nb)], 1))
        n = _nz(rng.normal(0, 1, (nb, 3)))
        sz = rng.uniform(0.14, 0.2, nb) * min(1.3, max(0.8, h / 2.4))
        A.append(pos)
        U.append(u)
        N.append(n)
        S.append(sz)
        cell.append(np.zeros(nb, int))
        # kępy igieł sterczące w górę – grubość poduszki
        nu = int(10 + 50 * pr)
        a = rng.uniform(0, 2 * math.pi, nu)
        d = pr * 0.8 * np.sqrt(rng.uniform(0, 1, nu))
        pos = c + np.stack([np.cos(a) * d, np.sin(a) * d * 0.85, rng.normal(-0.02, 0.025, nu)], 1)
        u = _nz(UP * 1.0 + np.stack([np.cos(a), np.sin(a), np.zeros(nu)], 1) * (d / pr)[:, None] * 0.8 + rng.normal(0, 0.15, (nu, 3)))
        n = _nz(rng.normal(0, 1, (nu, 3)))
        sz = rng.uniform(0.16, 0.24, nu) * min(1.3, max(0.8, h / 2.4))
        A.append(pos)
        U.append(u)
        N.append(n)
        S.append(sz)
        cell.append(np.full(nu, 3))
    A, U, N, S, cell = (np.concatenate(x) for x in (A, U, N, S, cell))
    rows = np.where(cell == 0, 3, 2)
    for rw in (2, 3):
        k = rows == rw
        _cards(G, A[k], U[k], N[k], S[k], S[k], cell[k], "igly", mat, cols=2, rows=rw, rnd=rng.random(int(k.sum())))


def _pot(G, r, rng, h):
    """Donica terakotowa z ziemią; zwraca wysokość ziemi."""
    pr = max(0.22, min(0.42, r * 0.75))
    ph = pr * 1.25
    prof = [(pr * 0.72, 0.0), (pr * 0.95, ph * 0.88), (pr * 1.06, ph * 0.9), (pr * 1.06, ph), (pr * 0.97, ph),
            (pr * 0.95, ph * 0.94), (pr * 0.70, ph * 0.1)]
    _lathe(G, prof, 32, "donica")
    _disc(G, pr * 0.95, ph * 0.9, 32, "ziemia", bump=0.01)
    return ph * 0.9


def _fruits(G, levels, rng, r, h, z0):
    """Pomarańcze albo cytryny wiszące przy końcach gałązek."""
    lv = levels[-1]
    if lv.M == 0:
        return
    n = int(rng.integers(12, 22))
    pick = rng.choice(lv.M, min(n, lv.M), replace=False)
    pos, T, N, B = lv.at(pick, np.full(len(pick), 0.85))
    lemon = rng.random() < 0.4
    rad = rng.uniform(0.032, 0.042, len(pick)) * (0.85 if lemon else 1.0)
    C = pos - np.array([0, 0, 1.0]) * rad[:, None] * 1.1
    _spheres(G, C, rad, "cytryna" if lemon else "pomarancza", sub=2, scale=(1, 1, 1.25) if lemon else (1, 1, 0.95))


def _build_palm(h, r, lod, var):
    """Palma pierzasta (jak kencja): smukły pierścieniowany pień, łukowate liście z listkami z geometrii."""
    rng = np.random.default_rng(zlib.crc32(f"palma|{lod}|{h:.3f}|{r:.3f}|{var}".encode()))
    G = Geo()
    far = lod == "daleko"
    nf = int(rng.integers(10, 15)) if not far else 9
    frond = min(r * 1.25, h * 0.45)
    th = h - frond * 0.42                      # wysokość szczytu pnia
    rt = max(0.06, 0.022 * h)
    # pień lekko wygięty
    n = 18
    la = rng.uniform(0, 2 * math.pi)
    lean = rng.uniform(0.02, 0.08)
    t = np.linspace(0, 1, n + 1)
    Pt = np.stack([np.cos(la) * lean * th * t ** 1.6, np.sin(la) * lean * th * t ** 1.6, -0.1 + t * (th + 0.1)], 1)[None]
    R = (rt * (1.25 - 0.3 * t + 0.25 * np.exp(-t * 20)))[None]
    _tubes(G, Pt, R, 12 if not far else 7, "kora:palma", kofs=rng.uniform(0, 9, (1, 3)), h0=h)
    top = Pt[0, -1]
    # nasady liści (włókniste)
    _lathe(G, [(rt * 0.95, -0.05), (rt * 1.25, frond * 0.06), (rt * 1.1, frond * 0.14), (rt * 0.5, frond * 0.2)], 10, "wlokna", center=top)
    # liście
    LP, LW, LU, LN, RR, RF, MATS = [], [], [], [], [], [], []
    for k in range(nf):
        age = k / max(1, nf - 1)                  # 0 – młody (stromy), 1 – stary (opadający)
        az = k * 2.39996 + rng.normal(0, 0.15)
        el = math.radians(70 - 75 * age + rng.normal(0, 6))
        L = frond * rng.uniform(0.82, 1.0) * (0.9 + 0.15 * (1 - abs(age - 0.5) * 2))
        droop = 1.2 + 1.6 * age
        hd = np.array([math.cos(az), math.sin(az), 0.0])
        ns = 14
        s_ = np.linspace(0, 1, ns + 1)
        ang = el - droop * s_ ** 1.6
        ds = L / ns
        pts = [top + np.array([0, 0, frond * 0.12])]
        for i in range(ns):
            a = 0.5 * (ang[i] + ang[i + 1])
            pts.append(pts[-1] + (hd * math.cos(a) + np.array([0, 0, 1.0]) * math.sin(a)) * ds)
        pts = np.array(pts)
        rr = np.linspace(0.016, 0.004, ns + 1) * min(1.5, frond / 1.3 + 0.4)
        _tubes(G, pts[None], rr[None], 4, "lodyga")
        # listki: pary wzdłuż osi (od 12% długości)
        Tg = _nz(np.gradient(pts, axis=0))
        side = _nz(np.cross(Tg, UP))
        nl = 30 if not far else 16
        for j in range(nl):
            u = 0.12 + 0.86 * j / (nl - 1)
            fi = u * ns
            i0 = min(int(fi), ns - 1)
            w = fi - i0
            base = pts[i0] * (1 - w) + pts[i0 + 1] * w
            tg = _nz(Tg[i0] * (1 - w) + Tg[i0 + 1] * w)
            sd = _nz(side[i0] * (1 - w) + side[i0 + 1] * w)
            ll = L * 0.36 * math.sin(math.pi * (0.08 + 0.9 * u)) ** 0.7 * rng.uniform(0.9, 1.08)
            for sgn in (1, -1):
                dvec = _nz(sd * sgn * 0.85 + tg * 0.45 + UP * 0.35)
                LP.append(base)
                LU.append(dvec)
                LN.append(_nz(np.cross(dvec, tg) * sgn + UP * 0.3))
                LW.append(ll)
                RR.append(age)
                RF.append(rng.random())
    if LP:
        LP, LU, LN, LW = np.array(LP), np.array(LU), np.array(LN), np.array(LW)
        _leaflets(G, LP, LU, LN, LW, np.array(RF), rng, far)
    return G


def _leaflets(G, A, U, Nn, L, rnd, rng, far, mat="palma_lisc", wfrac=0.065, droop=0.55, rows=5):
    """Wąskie listki z geometrii (bez alfy): pasek zwężony do ostrza, opadający ku końcowi."""
    K = len(A)
    rows = 3 if far else rows
    Nn = _nz(Nn - (Nn * U).sum(1, keepdims=True) * U)
    W = np.cross(U, Nn)
    y = np.linspace(0, 1, rows)
    wd = (L * wfrac)[:, None] * (np.sin(np.pi * np.clip(y * 0.92 + 0.08, 0, 1)) ** 0.6)[None] * (1 - y[None] ** 3)
    dz = -(droop * rng.uniform(0.6, 1.3, K))[:, None] * (y[None] ** 2) * L[:, None]
    C = A[:, None, :] + U[:, None, :] * (y[None, :, None] * L[:, None, None]) + Nn[:, None, :] * dz[..., None] * 0 + np.array([0, 0, 1.0]) * dz[..., None]
    left = C - W[:, None, :] * wd[..., None] + Nn[:, None, :] * (wd * 0.35)[..., None]
    right = C + W[:, None, :] * wd[..., None] + Nn[:, None, :] * (wd * 0.35)[..., None]
    V = np.stack([left, C, right], 2)                  # (K, rows, 3, 3) – złożone w V wzdłuż nerwu
    base = (np.arange(K) * rows * 3)[:, None, None]
    ii = np.arange(rows - 1)[None, :, None] * 3
    jj = np.arange(2)[None, None, :]
    q = np.stack([base + ii + jj, base + ii + jj + 1, base + ii + 3 + jj + 1, base + ii + 3 + jj], -1).reshape(-1, 4)
    uu = np.array([0.0, 0.5, 1.0])
    UVv = np.stack([np.broadcast_to(uu[None, :], (rows, 3)), np.broadcast_to(y[:, None], (rows, 3))], -1)
    fi = np.stack([ii + jj, ii + jj + 1, ii + 3 + jj + 1, ii + 3 + jj], -1).reshape(-1, 4)
    UVf = np.broadcast_to(UVv.reshape(-1, 2)[fi.ravel()].reshape(-1, 4, 2)[None], (K, fi.shape[0], 4, 2)).reshape(-1, 4, 2)
    G.add(V.reshape(-1, 3), q, UVf, mat, fattr=dict(rnd=np.repeat(rnd, 2 * (rows - 1))))



# =====================================================================================================
#  MAŁE ROŚLINY
# =====================================================================================================

def _bent_cards(G, A, D, L, wid, droop, cell, atlas, mat, rows=6, fold=0.15, twist=0.0, rnd=None, wdir=None, rng=None):
    """Wygięte karty (liście paproci, monstery): oś startuje w A w kierunku D i opada (droop – kąt na całej długości)."""
    K = len(A)
    D = _nz(D)
    hz = _nz(np.concatenate([D[:, :2], np.zeros((K, 1))], 1) + 1e-6)
    W = _nz(np.cross(UP, hz)) if wdir is None else _nz(wdir)
    y = np.linspace(0, 1, rows)
    el0 = np.arcsin(np.clip(D[:, 2], -1, 1))
    ang = el0[:, None] - droop[:, None] * y[None] ** 1.4
    ds = (L / (rows - 1))[:, None]
    Tv = np.cos(ang)[..., None] * hz[:, None, :] + np.sin(ang)[..., None] * UP
    C = np.zeros((K, rows, 3))
    C[:, 0] = A
    for i in range(1, rows):
        C[:, i] = C[:, i - 1] + 0.5 * (Tv[:, i - 1] + Tv[:, i]) * ds
    # skręt wokół osi wzdłuż długości
    tw = twist[:, None] * y[None] if np.ndim(twist) else twist * y[None]
    Wt = np.cos(tw)[..., None] * W[:, None, :] + np.sin(tw)[..., None] * np.cross(Tv, W[:, None, :])
    Nv = _nz(np.cross(Wt, Tv))
    x = np.array([-0.5, 0.0, 0.5])
    hw = wid[:, None, None] * x[None, None, :]
    fo = (np.abs(x)[None, None, :] * 2) * (fold * wid)[:, None, None] * 0.5
    V = C[:, :, None, :] + Wt[:, :, None, :] * hw[..., None] + Nv[:, :, None, :] * fo[..., None]
    cols = 3
    base = (np.arange(K) * rows * cols)[:, None, None]
    ii = np.arange(rows - 1)[None, :, None] * cols
    jj = np.arange(cols - 1)[None, None, :]
    q = np.stack([base + ii + jj, base + ii + jj + 1, base + ii + cols + jj + 1, base + ii + cols + jj], -1).reshape(-1, 4)
    ac, ar, cw, chh = ATLAS[atlas]
    cell = np.asarray(cell)
    u0 = (cell % ac) / ac
    v0 = 1.0 - (cell // ac + 1) / ar
    uu = u0[:, None, None] + (x[None, None, :] + 0.5) / ac
    vv = v0[:, None, None] + y[None, :, None] / ar
    UVv = np.stack([np.broadcast_to(uu, (K, rows, cols)), np.broadcast_to(vv, (K, rows, cols))], -1)
    fi = np.stack([ii + jj, ii + jj + 1, ii + cols + jj + 1, ii + cols + jj], -1).reshape(-1, 4)
    UVf = UVv.reshape(K, -1, 2)[:, fi.ravel()].reshape(-1, 4, 2)
    r = rnd if rnd is not None else np.random.default_rng(K).random(K)
    G.add(V.reshape(-1, 3), q, UVf, mat, fattr=dict(rnd=np.repeat(r, (rows - 1) * (cols - 1))))
    return C, Tv


def _blades(G, A, D, L, wid, droop, mat, rng, rows=5, twist=None):
    """Źdźbła z geometrii (trawa): pasek zwężony do ostrza, łukowato opadający."""
    K = len(A)
    D = _nz(D)
    hz = _nz(np.concatenate([D[:, :2], np.zeros((K, 1))], 1) + 1e-6)
    y = np.linspace(0, 1, rows)
    el0 = np.arcsin(np.clip(D[:, 2], -1, 1))
    ang = el0[:, None] - droop[:, None] * y[None] ** 1.6
    ds = (L / (rows - 1))[:, None]
    Tv = np.cos(ang)[..., None] * hz[:, None, :] + np.sin(ang)[..., None] * UP
    C = np.zeros((K, rows, 3))
    C[:, 0] = A
    for i in range(1, rows):
        C[:, i] = C[:, i - 1] + 0.5 * (Tv[:, i - 1] + Tv[:, i]) * ds
    tw = (twist if twist is not None else rng.uniform(-1.2, 1.2, K))[:, None] * y[None]
    W0 = _nz(np.cross(UP, hz))
    Wt = np.cos(tw)[..., None] * W0[:, None, :] + np.sin(tw)[..., None] * np.cross(Tv, W0[:, None, :])
    hw = wid[:, None] * (1 - y[None] ** 1.5) * 0.5 + 0.0004
    V = np.stack([C - Wt * hw[..., None], C + Wt * hw[..., None]], 2)
    base = (np.arange(K) * rows * 2)[:, None]
    ii = np.arange(rows - 1)[None, :] * 2
    q = np.stack([base + ii, base + ii + 1, base + ii + 3, base + ii + 2], -1).reshape(-1, 4)
    UVv = np.stack([np.broadcast_to(np.array([0.0, 1.0])[None, :], (rows, 2)), np.broadcast_to(y[:, None], (rows, 2))], -1)
    fi = np.stack([ii[0], ii[0] + 1, ii[0] + 3, ii[0] + 2], -1)
    UVf = np.broadcast_to(UVv.reshape(-1, 2)[fi.ravel()].reshape(-1, 4, 2)[None], (K, rows - 1, 4, 2)).reshape(-1, 4, 2)
    G.add(V.reshape(-1, 3), q, UVf, mat, fattr=dict(rnd=np.repeat(rng.random(K), rows - 1)))


def _build_paproc(r, var, season):
    rng = np.random.default_rng(zlib.crc32(f"paproc|{r:.3f}|{var}".encode()))
    G = Geo()
    n = int(rng.integers(11, 17))
    az = rng.uniform(0, 2 * math.pi) + np.arange(n) * 2.39996 + rng.normal(0, 0.2, n)
    young = rng.random(n) < 0.3
    el = np.radians(np.where(young, rng.uniform(62, 80, n), rng.uniform(38, 62, n)))
    D = np.stack([np.cos(az) * np.cos(el), np.sin(az) * np.cos(el), np.sin(el)], 1)
    L = r / 0.78 * rng.uniform(0.75, 1.0, n) * np.where(young, 0.85, 1.0)
    A = np.stack([np.cos(az) * r * 0.06, np.sin(az) * r * 0.06, np.full(n, -0.01)], 1)
    ac, ar, cw, chh = ATLAS["paproc"]
    _bent_cards(G, A, D, L, L * cw / chh, np.radians(rng.uniform(60, 110, n)), rng.integers(0, 2, n), "paproc",
                "lisc:paproc/paproc", rows=7, fold=0.25, twist=rng.normal(0, 0.25, n), rnd=rng.random(n), rng=rng)
    return G


def _build_monstera(r, var, season):
    rng = np.random.default_rng(zlib.crc32(f"monstera|{r:.3f}|{var}".encode()))
    G = Geo()
    n = int(rng.integers(6, 10))
    az = rng.uniform(0, 2 * math.pi) + np.arange(n) * 2.39996 + rng.normal(0, 0.25, n)
    el = np.radians(rng.uniform(58, 82, n))
    pl = r * rng.uniform(0.6, 1.25, n)                     # ogonki
    Ll = r * rng.uniform(0.85, 1.15, n)                    # blaszki
    ac, ar, cw, chh = ATLAS["monstera"]
    tips, dirs = [], []
    for k in range(n):
        d = np.array([math.cos(az[k]) * math.cos(el[k]), math.sin(az[k]) * math.cos(el[k]), math.sin(el[k])])
        pts = [np.array([0, 0, -0.02])]
        for i in range(8):
            t = (i + 1) / 8
            d2 = _nz(d + np.array([0, 0, -0.9]) * t ** 2 * 0.6 + np.array([math.cos(az[k]), math.sin(az[k]), 0]) * 0.25 * t)
            pts.append(pts[-1] + d2 * pl[k] / 8)
        pts = np.array(pts)
        _tubes(G, pts[None], np.linspace(0.011, 0.006, 9)[None] * (r / 0.45) ** 0.5, 5, "lodyga")
        tips.append(pts[-1])
        dirs.append(_nz(pts[-1] - pts[-2]))
    tips, dirs = np.array(tips), np.array(dirs)
    # blaszka: od końca ogonka, odchylona w dół i na zewnątrz
    hz = _nz(np.concatenate([dirs[:, :2], np.zeros((n, 1))], 1) + 1e-6)
    D = _nz(hz * 1.0 + UP * rng.uniform(-0.7, 0.05, (n, 1)))
    _bent_cards(G, tips - D * Ll[:, None] * 0.06, D, Ll, Ll * cw / chh, np.radians(rng.uniform(15, 40, n)),
                rng.integers(0, 2, n), "monstera", "lisc:monstera/monstera", rows=5, fold=0.22,
                twist=rng.normal(0, 0.25, n), rnd=rng.random(n), rng=rng)
    return G


def _build_lawenda(r, var, season):
    rng = np.random.default_rng(zlib.crc32(f"lawenda|{r:.3f}|{var}".encode()))
    G = Geo()
    # kopułka liści
    n = int(rng.integers(36, 50))
    az = rng.uniform(0, 2 * math.pi, n)
    rr = r * 0.45 * np.sqrt(rng.random(n))
    A = np.stack([np.cos(az) * rr, np.sin(az) * rr, np.full(n, -0.02)], 1)
    el = np.radians(rng.uniform(55, 85, n))
    U = np.stack([np.cos(az) * np.cos(el), np.sin(az) * np.cos(el), np.sin(el)], 1)
    Nn = _nz(rng.normal(0, 1, (n, 3)))
    sz = r * rng.uniform(0.8, 1.15, n)
    _cards(G, A, U, Nn, sz, sz, np.zeros(n, int), "lawenda_lisc", "lisc:lawenda_lisc/lawenda_lisc", cols=2, rows=2, rnd=rng.random(n))
    if season == "zima":
        return G
    # łodyżki z kłosami
    m = int(rng.integers(190, 260) * min(1.6, max(0.6, (r / 0.3) ** 2)))
    az = rng.uniform(0, 2 * math.pi, m)
    rr = r * 0.5 * np.sqrt(rng.random(m))
    A = np.stack([np.cos(az) * rr, np.sin(az) * rr, np.full(m, r * 0.4)], 1)
    tilt = np.radians(8 + 40 * rr / (r * 0.5) + rng.normal(0, 6, m))
    D = np.stack([np.cos(az) * np.sin(tilt), np.sin(az) * np.sin(tilt), np.cos(tilt)], 1)
    Ls = r * rng.uniform(0.75, 1.05, m)
    seg = 3
    t = np.linspace(0, 1, seg + 1)
    Pp = A[:, None, :] + D[:, None, :] * (Ls[:, None, None] * t[None, :, None])
    Pp[:, :, :2] += (D[:, None, :2] * (t[None, :, None] ** 2) * Ls[:, None, None] * 0.25)
    _tubes(G, Pp, np.full((m, seg + 1), 0.0016), 3, "lodyga")
    tip = Pp[:, -1]
    tdir = _nz(Pp[:, -1] - Pp[:, -2])
    sl = rng.uniform(0.08, 0.11, m) * min(1.3, max(0.8, r / 0.3))
    ac, ar, cw, chh = ATLAS["lawenda"]
    cell = rng.integers(0, 2, m)
    for rot in (0.0, math.pi / 2):
        ref = _nz(np.cross(tdir, np.array([math.cos(rot), math.sin(rot), 0.0])))
        _cards(G, tip - tdir * sl[:, None] * 0.15, tdir, ref, sl, sl * cw / chh, cell, "lawenda", "lisc:lawenda/lawenda",
               cols=2, rows=2, rnd=rng.random(m))
    return G


def _build_mech(r, var, season):
    """Poduszka mchu: nieregularny, lekko wypukły placek."""
    rng = np.random.default_rng(zlib.crc32(f"mech|{r:.3f}|{var}".encode()))
    G = Geo()
    H = float(np.clip(0.06 + 0.07 * r, 0.08, 0.18))
    nr, na = 14, 64
    phi = np.linspace(0, 2 * math.pi, na, endpoint=False)
    ph = rng.uniform(0, 2 * math.pi, 4)
    edge = 1 + 0.07 * np.sin(3 * phi + ph[0]) + 0.05 * np.sin(5 * phi + ph[1]) + 0.04 * np.sin(8 * phi + ph[2])
    Rx, Ry = r, r * 0.8
    rho = np.linspace(0, 1, nr + 1)[1:]
    X = np.cos(phi)[None] * Rx * edge[None] * rho[:, None]
    Y = np.sin(phi)[None] * Ry * edge[None] * rho[:, None]
    prof = (1 - rho ** 2.2) ** 0.55
    bump = 0.25 * (np.sin(X * 7 + ph[3]) * np.sin(Y * 6) + 0.6 * np.sin(X * 15 + 1.3) * np.sin(Y * 13 + 0.4))
    Z = H * prof[:, None] * (1 + bump) - 0.025 * (rho[:, None] > 0.9)
    V = np.concatenate([[[0, 0, H * 1.02]], np.stack([X, Y, Z], -1).reshape(-1, 3)])
    j = np.arange(na)
    j1 = (j + 1) % na
    tri = np.stack([np.zeros(na, int), 1 + j, 1 + j1], 1)
    G.add(V, tri, None, "mech")
    i = np.arange(nr - 1)[:, None] * na + 1
    q = np.stack([i + j[None], i + na + j[None], i + na + j1[None], i + j1[None]], -1).reshape(-1, 4)
    G.add(V, q, None, "mech")
    return G


def _build_kamien(r, var, season):
    """Naturalny, wygładzony głaz (nie kula): szum niskiej częstotliwości + ścięte płaszczyzny."""
    rng = np.random.default_rng(zlib.crc32(f"kamien|{r:.3f}|{var}".encode()))
    G = Geo()
    V0, F0 = _sphere_tpl(4)
    V = V0 * np.array([1.0, 0.76, 0.6])
    n = np.zeros(len(V))
    for k in range(5):
        d = _nz(rng.normal(0, 1, 3))
        f = rng.uniform(1.2, 3.5)
        n += rng.uniform(0.03, 0.08) * np.sin(V @ d * f * 2 + rng.uniform(0, 6.3))
    V = V * (1 + n)[:, None]
    for k in range(int(rng.integers(3, 6))):
        nrm = _nz(rng.normal(0, 1, 3) * np.array([1, 1, 0.6]) + np.array([0, 0, 0.35 if k == 0 else 0.0]))
        dd = (V @ nrm).max() * rng.uniform(0.72, 0.9)
        ex = V @ nrm - dd
        # miękkie ścięcie
        cut = np.where(ex > 0, ex * 0.85, 0.0) + np.where((ex > -0.08) & (ex <= 0), 0.0, 0.0)
        V = V - nrm[None] * cut[:, None]
    V *= r
    zmin = V[:, 2].min()
    V[:, 2] -= zmin + (V[:, 2].max() - zmin) * 0.28          # częściowo zagłębiony
    G.add(V, F0, None, "kamien")
    return G


def _build_lilia(r, var, season):
    """Grzybienie: liście pływające na wodzie (Z) i kilka kwiatów."""
    rng = np.random.default_rng(zlib.crc32(f"lilia|{r:.3f}|{var}".encode()))
    G = Geo()
    npad = int(rng.integers(5, 9))
    pts = []
    for _ in range(npad * 6):
        if len(pts) >= npad:
            break
        a = rng.uniform(0, 2 * math.pi)
        d = r * 0.85 * math.sqrt(rng.random())
        pr = rng.uniform(0.09, 0.17) * min(1.4, max(0.7, r / 0.22) ** 0.5)
        x, y = math.cos(a) * d, math.sin(a) * d
        if all(math.hypot(x - q[0], y - q[1]) > (pr + q[2]) * 0.8 for q in pts):
            pts.append((x, y, pr))
    seg = 28
    for x, y, pr in pts:
        notch = rng.uniform(0, 2 * math.pi)
        th = notch + np.linspace(0.18, 2 * math.pi - 0.18, seg)
        rim = np.stack([x + np.cos(th) * pr, y + np.sin(th) * pr, np.full(seg, 0.004)], 1)
        rim2 = np.stack([x + np.cos(th) * pr * 0.92, y + np.sin(th) * pr * 0.92, np.full(seg, 0.002)], 1)
        c = np.array([[x, y, 0.001]])
        V = np.concatenate([c, rim2, rim])
        tri = np.stack([np.zeros(seg - 1, int), 1 + np.arange(seg - 1), 2 + np.arange(seg - 1)], 1)
        q = np.stack([1 + np.arange(seg - 1), 1 + seg + np.arange(seg - 1), 2 + seg + np.arange(seg - 1), 2 + np.arange(seg - 1)], 1)
        uvp = lambda P: np.stack([0.5 + (P[:, 0] - x) / (2 * pr), 0.5 + (P[:, 1] - y) / (2 * pr)], 1)
        uv = uvp(V)
        G.add(V, tri, uv[tri], "lisc:lilia/lilia", fattr=dict(rnd=np.full(len(tri), rng.random())))
        G.add(V, q[:, ::-1], uv[q[:, ::-1]], "lisc:lilia/lilia", fattr=dict(rnd=np.full(len(q), rng.random())))
    # kwiaty
    nfl = int(rng.integers(1, 3))
    pink = rng.random() < 0.5
    for k in range(nfl):
        x, y, pr = pts[k] if k < len(pts) else (0, 0, 0.1)
        cx, cy = x + rng.uniform(-0.3, 0.3) * pr, y + rng.uniform(-0.3, 0.3) * pr
        for ring, (npet, el, ln) in enumerate(((10, 28, 0.055), (8, 52, 0.048), (6, 70, 0.038))):
            az = np.arange(npet) * 2 * math.pi / npet + ring * 0.3 + rng.normal(0, 0.08, npet)
            D = np.stack([np.cos(az) * math.cos(math.radians(el)), np.sin(az) * math.cos(math.radians(el)),
                          np.full(npet, math.sin(math.radians(el)))], 1)
            A = np.stack([cx + np.cos(az) * 0.008, cy + np.sin(az) * 0.008, np.full(npet, 0.012)], 1)
            L = ln * rng.uniform(0.85, 1.1, npet)
            _petals(G, A, D, L, L * 0.36, "platek_rozowy" if pink else "platek", rng)
        _lathe(G, [(0.0, 0.01), (0.012, 0.012), (0.014, 0.026), (0.0, 0.03)], 10, "precik", center=(cx, cy, 0))
    return G


def _petals(G, A, D, L, W, mat, rng, rows=4):
    """Płatki z geometrii: łódeczkowate, zaostrzone, wygięte do góry."""
    K = len(A)
    D = _nz(D)
    side = _nz(np.cross(UP, D) + 1e-6)
    Nn = _nz(np.cross(D, side))
    y = np.linspace(0, 1, rows)
    wd = W[:, None] * np.sin(np.pi * np.clip(y * 0.85 + 0.12, 0, 1)) ** 0.8 * (1 - y ** 4)
    C = A[:, None, :] + D[:, None, :] * (y[None, :, None] * L[:, None, None]) + Nn[:, None, :] * (y[None, :, None] ** 2 * L[:, None, None] * 0.25)
    cup = wd * 0.35
    V = np.stack([C - side[:, None, :] * wd[..., None] + Nn[:, None, :] * cup[..., None], C,
                  C + side[:, None, :] * wd[..., None] + Nn[:, None, :] * cup[..., None]], 2)
    base = (np.arange(K) * rows * 3)[:, None, None]
    ii = np.arange(rows - 1)[None, :, None] * 3
    jj = np.arange(2)[None, None, :]
    q = np.stack([base + ii + jj, base + ii + jj + 1, base + ii + 3 + jj + 1, base + ii + 3 + jj], -1).reshape(-1, 4)
    uu = np.array([0.0, 0.5, 1.0])
    UVv = np.stack([np.broadcast_to(uu[None, :], (rows, 3)), np.broadcast_to(y[:, None], (rows, 3))], -1)
    fi = np.stack([ii + jj, ii + jj + 1, ii + 3 + jj + 1, ii + 3 + jj], -1).reshape(-1, 4)
    UVf = np.broadcast_to(UVv.reshape(-1, 2)[fi.ravel()].reshape(-1, 4, 2)[None], (K, fi.shape[0], 4, 2)).reshape(-1, 4, 2)
    G.add(V.reshape(-1, 3), q, UVf, mat)


def _build_trawa(r, var, season):
    """Kępa trawy ozdobnej: łukowato przewieszone źdźbła (zimą słomkowe)."""
    rng = np.random.default_rng(zlib.crc32(f"trawa|{r:.3f}|{var}".encode()))
    G = Geo()
    n = int(140 * min(2.0, max(0.6, (r / 0.3) ** 1.5)))
    az = rng.uniform(0, 2 * math.pi, n)
    rr = r * 0.22 * np.sqrt(rng.random(n))
    A = np.stack([np.cos(az) * rr, np.sin(az) * rr, np.full(n, -0.01)], 1)
    el = np.radians(rng.uniform(48, 86, n))
    D = np.stack([np.cos(az) * np.cos(el), np.sin(az) * np.cos(el), np.sin(el)], 1)
    L = r * rng.uniform(1.3, 2.3, n)
    droop = np.radians(rng.uniform(25, 85, n)) * (L / (2.3 * r))
    mat = "trawa_sucha" if season == "zima" else "trawa_ozdobna"
    _blades(G, A, D, L, rng.uniform(0.006, 0.011, n) * min(1.5, max(0.7, r / 0.3)), droop, mat, rng)
    return G


def _build_bambus(r, var, season):
    """Kępa bambusa: zielone źdźbła z kolankami, liście na krótkich gałązkach w górnej części."""
    rng = np.random.default_rng(zlib.crc32(f"bambus|{r:.3f}|{var}".encode()))
    G = Geo()
    H = float(np.clip(r * 7, 2.5, 5.5))
    n = int(rng.integers(9, 16))
    az = rng.uniform(0, 2 * math.pi, n)
    rr = r * 0.45 * np.sqrt(rng.random(n))
    S = np.stack([np.cos(az) * rr, np.sin(az) * rr, np.full(n, -0.05)], 1)
    tilt = np.radians(rng.uniform(2, 12, n))
    D = np.stack([np.cos(az) * np.sin(tilt), np.sin(az) * np.sin(tilt), np.cos(tilt)], 1)
    L = H * rng.uniform(0.7, 1.0, n)
    P = dict(_D)
    P.update(lpet=(55, 15), ldroop=0.4, lup=0.5, lout=0.8, lrnd=0.8, fold=0.05, curl=0.1, lphyl="spiral")
    Pc, Lc = _grow(S, D, L, 14, rng, None, 0.01, 0.0, 0.25, gpow=2.0)
    lv0 = Lv(Pc, Lc, np.full(n, -1), np.zeros(n), 0)
    R0 = rng.uniform(0.012, 0.022, n)[:, None] * np.linspace(1.0, 0.55, 15)[None]
    _tubes(G, Pc, R0, 8, "kora:bambus", kofs=rng.uniform(0, 9, (n, 3)), h0=H)
    cnt = rng.poisson(9 * Lc / H) + 2
    idx, t, pos, Dd = _spawn(lv0, cnt, 0.45, 1.0, rng, (55, 45), "spiral")
    Lb = rng.uniform(0.25, 0.6, len(idx))
    Pb, Lb = _grow(pos, Dd, Lb, 4, rng, None, 0.08, 0.0, 0.2)
    lv1 = Lv(Pb, Lb, idx, t, 1)
    _tubes(G, Pb, np.full((len(idx), 5), 0.003), 3, "kora:bambus")
    _foliage_cards(G, lv1, P, rng, "spray_bambus", "lisc:spray_bambus/bambus", 0.32, 1e9, len(idx) * 7, t0=0.1,
                   cols=2, rows=3)
    return G


def _build_donica(r, var, season):
    """Donica z krzewem liściastym."""
    rng = np.random.default_rng(zlib.crc32(f"donica|{r:.3f}|{var}".encode()))
    G = Geo()
    pr = r
    ph = r * 1.3
    dark = var % 2 == 1
    if dark:   # gładka, ciemna ceramika – walec z zaokrągleniem
        prof = [(pr * 0.82, 0.0), (pr * 0.98, ph * 0.12), (pr, ph * 0.5), (pr * 0.97, ph), (pr * 0.9, ph), (pr * 0.9, ph * 0.9), (pr * 0.7, ph * 0.1)]
        _lathe(G, prof, 32, "donica_ciemna")
    else:
        prof = [(pr * 0.72, 0.0), (pr * 0.95, ph * 0.88), (pr * 1.06, ph * 0.9), (pr * 1.06, ph), (pr * 0.97, ph),
                (pr * 0.95, ph * 0.94), (pr * 0.70, ph * 0.1)]
        _lathe(G, prof, 32, "donica")
    zs = ph * 0.9
    _disc(G, pr * 0.92, zs, 32, "ziemia", bump=0.01)
    hs = r * 2.0
    T = _build_tree("krzew", hs, r * 1.05, "blisko", "lato", var)
    for v, f, uv, mi, pa, fa in T.parts:
        G.add(v + np.array([0, 0, zs]), f, uv, T.mats[mi], pa, fa)
    return G


PLANTS = {"paproc": _build_paproc, "monstera": _build_monstera, "lawenda": _build_lawenda, "mech": _build_mech,
          "kamien": _build_kamien, "lilia": _build_lilia, "trawa": _build_trawa, "bambus": _build_bambus,
          "donica": _build_donica}


# =====================================================================================================
#  API
# =====================================================================================================

KINDS_TREE = ("klon", "klon_zielony", "brzoza", "lipa", "oliwka", "sosna", "palma", "cytrus")
_GEO_CACHE = {}       # w procesie: geometria wariantów (niezależna od sceny Blendera)


def _bucket(h, r):
    """Przedziały rozmiaru (±10%): wariant budowany raz, potem skalowany do dokładnego h i r."""
    hb = int(round(math.log(max(h, 0.3)) / math.log(1.2)))
    ab = int(round(math.log(max(r, 0.1) / max(h, 0.3)) / math.log(1.22)))
    h0 = 1.2 ** hb
    return hb, ab, h0, h0 * 1.22 ** ab


def _variant(kind, h, r, lod, season, var, ctx):
    """Siatka wariantu (z ctx.cache) i jej zasięg (promień, wysokość)."""
    hb, ab, h0, r0 = _bucket(h, r)
    deciduous_bare = season == "zima" and kind in DECID
    skey = "zima" if deciduous_bare else "lato"
    key = ("rosliny", "drzewo", kind, lod, skey, hb, ab, var)
    if key in ctx.cache:
        return ctx.cache[key]
    gk = key
    A = _GEO_CACHE.get(gk)
    if A is None:
        _ensure_textures()
        G = _build_palm(h0, r0, lod, var) if kind == "palma" else _build_tree(kind, h0, r0, lod, skey, var)
        A = G.arrays()
        A["mats"] = list(G.mats)
        _GEO_CACHE[gk] = A
    me = _mesh_from_arrays(f"{kind}_{lod}_{skey}_{hb}_{ab}_{var}", A)
    for mk in A["mats"]:
        me.materials.append(_material(ctx, mk))
    V = A["V"]
    rho = float(np.hypot(V[:, 0], V[:, 1]).max())
    zt = float(V[:, 2].max())
    out = (me, rho, zt, len(A["S"]), int((np.diff(np.append(A["S"], len(A["L"]))) - 2).sum()))
    ctx.cache[key] = out
    return out


def tree(kind, X, Y, Z, h, r, seed, ctx, lod="blisko"):
    """Drzewo gatunku kind w (X, Y, Z) – korona mieści się w promieniu r i wysokości h. Zwraca [obiekt]."""
    import bpy
    kind = {"drzewo": "lipa", "klon_czerwony": "klon", "klon_palmowy": "klon"}.get(kind, kind)
    if kind not in KINDS_TREE and kind != "krzew":
        print(f"rosliny.tree: nieznany gatunek {kind!r} – stawiam lipę", file=sys.stderr)
        kind = "lipa"
    rnd = random.Random(seed * 7919 + 13)
    var = rnd.randrange(3)
    me, rho, zt, nf, ntri = _variant(kind, h, r, lod, ctx.season, var, ctx)
    ob = bpy.data.objects.new(f"{kind}_{seed}", me)
    ob.location = (X, Y, Z)
    ob.rotation_euler = (0, 0, rnd.uniform(0, 2 * math.pi))
    hb, ab, h0, r0 = _bucket(h, r)
    # przedział → dokładny rozmiar; korona nigdy nie wychodzi poza r i h
    sxy = min(r / max(rho, 1e-3), (r / r0) * 1.15)
    sz = min(h / max(zt, 1e-3), (h / h0) * 1.12)
    ob.scale = (sxy, sxy, sz)
    ctx.link(ob)
    return [ob]



def _plant_mesh(kind, r, var, season, ctx):
    rb = int(round(math.log(max(r, 0.03)) / math.log(1.18)))
    r0 = 1.18 ** rb
    sk = season if kind in ("trawa", "lawenda") else "lato"
    key = ("rosliny", "roslina", kind, rb, var, sk)
    if key in ctx.cache:
        return ctx.cache[key]
    A = _GEO_CACHE.get(key)
    if A is None:
        _ensure_textures()
        G = PLANTS[kind](r0, var, sk)
        A = G.arrays()
        A["mats"] = list(G.mats)
        _GEO_CACHE[key] = A
    me = _mesh_from_arrays(f"{kind}_{rb}_{var}", A)
    for mk in A["mats"]:
        me.materials.append(_material(ctx, mk))
    out = (me, r0, int((np.diff(np.append(A["S"], len(A["L"]))) - 2).sum()))
    ctx.cache[key] = out
    return out


def plant(kind, X, Y, Z, r, seed, ctx, rot=0.0):
    """Mała roślina / element ogrodu o promieniu r w (X, Y, Z). rot – obrót wokół Z (radiany, np. ctx.rot_bl(ft.rot))."""
    import bpy
    kind = {"kamień": "kamien", "paproć": "paproc", "lilie": "lilia", "grzybienie": "lilia", "trawy": "trawa",
            "bambusy": "bambus", "krzew": "donica"}.get(kind, kind)
    if kind == "cytrus":
        return tree("cytrus", X, Y, Z, 2.2 * max(0.8, min(1.3, (r / 0.45) ** 0.5)), max(0.35, r), seed, ctx)
    if kind not in PLANTS:
        print(f"rosliny.plant: nieznana roślina {kind!r} – stawiam paproć", file=sys.stderr)
        kind = "paproc"
    rnd = random.Random(seed * 7919 + 101)
    var = rnd.randrange(3)
    me, r0, ntri = _plant_mesh(kind, r, var, ctx.season, ctx)
    ob = bpy.data.objects.new(f"{kind}_{seed}", me)
    ob.location = (X, Y, Z)
    if kind == "kamien":
        ob.rotation_euler = (0, 0, rot)
        sc = r / r0
        ob.scale = (sc, sc, sc * rnd.uniform(0.85, 1.15))
    else:
        ob.rotation_euler = (0, 0, rot + rnd.uniform(0, 2 * math.pi))
        sc = r / r0 * rnd.uniform(0.94, 1.06)
        ob.scale = (sc, sc, sc)
    ctx.link(ob)
    return [ob]


# drzewa w tle: gatunek, udział, wysokość (min, max), stosunek r/h
TREELINE = (("lipa", 0.26, (10, 17), (0.32, 0.4)), ("klon_zielony", 0.18, (9, 14), (0.33, 0.42)),
            ("brzoza", 0.2, (10, 16), (0.2, 0.27)), ("sosna", 0.26, (13, 21), (0.2, 0.28)),
            ("oliwka", 0.0, (4, 6), (0.4, 0.5)))


def _excluded(exclude, x, y):
    if exclude is None:
        return False
    if callable(exclude):
        return bool(exclude(x, y))
    if hasattr(exclude, "contains"):
        from shapely.geometry import Point
        return exclude.contains(Point(x, y))
    for c in exclude:
        if math.hypot(x - c[0], y - c[1]) < c[2]:
            return True
    return False


def treeline(cx, cy, r_in, r_out, n, seed, ctx, exclude=None, z=-0.3, kinds=None):
    """Pierścień n drzew w tle (lod „daleko”) między promieniami r_in i r_out wokół (cx, cy).
    exclude: geometria shapely (XY Blendera), funkcja (x, y) → bool albo lista kół (x, y, r)."""
    import bpy
    rnd = random.Random(seed * 104729 + 7)
    spec = kinds or TREELINE
    tot = sum(w for _, w, _, _ in spec)
    area = math.pi * (r_out ** 2 - r_in ** 2)
    dmin = math.sqrt(area / max(n, 1)) * 0.55
    pts = []
    tries = 0
    while len(pts) < n and tries < n * 60:
        tries += 1
        a = rnd.uniform(0, 2 * math.pi)
        d = math.sqrt(rnd.uniform(r_in ** 2, r_out ** 2))
        x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
        if _excluded(exclude, x, y):
            continue
        if any((x - p[0]) ** 2 + (y - p[1]) ** 2 < dmin * dmin for p in pts):
            continue
        pts.append((x, y))
    out = []
    # skupiska gatunków: gatunek zależy od położenia (wolny szum kątowy) + losowość
    ph = rnd.uniform(0, 6.3)
    for k, (x, y) in enumerate(pts):
        a = math.atan2(y - cy, x - cx)
        u = (0.5 + 0.35 * math.sin(3 * a + ph) + 0.15 * math.sin(7 * a + 2 * ph) + rnd.uniform(-0.25, 0.25)) % 1.0
        acc = 0.0
        kind = spec[0][0]
        for kd, w, _, _ in spec:
            acc += w / tot
            if u <= acc:
                kind = kd
                break
        _, _, (h0, h1), (q0, q1) = next(t for t in spec if t[0] == kind)
        hc, rc = (h0 + h1) / 2, (h0 + h1) / 2 * (q0 + q1) / 2
        var = rnd.randrange(3)
        me, rho, zt, nf, ntri = _variant(kind, hc, rc, "daleko", ctx.season, var, ctx)
        ob = bpy.data.objects.new(f"tlo_{kind}_{k}", me)
        sc = rnd.uniform(h0, h1) / max(zt, 1e-3)
        sxy = sc * rnd.uniform(0.88, 1.12)
        ob.location = (x, y, z)
        ob.rotation_euler = (0, 0, rnd.uniform(0, 2 * math.pi))
        ob.scale = (sxy, sxy * rnd.uniform(0.92, 1.08), sc)
        ctx.link(ob)
        out.append(ob)
    return out


def _tuft_geo(height, var, season):
    """Kępka trawy (~30 źdźbeł) do rozsiewania instancjami."""
    rng = np.random.default_rng(zlib.crc32(f"kepka|{height:.3f}|{var}".encode()))
    G = Geo()
    n = int(rng.integers(26, 40))
    az = rng.uniform(0, 2 * math.pi, n)
    rr = 0.035 * np.sqrt(rng.random(n))
    A = np.stack([np.cos(az) * rr, np.sin(az) * rr, np.full(n, -0.005)], 1)
    el = np.radians(rng.uniform(58, 88, n))
    D = np.stack([np.cos(az) * np.cos(el), np.sin(az) * np.cos(el), np.sin(el)], 1)
    L = height * rng.uniform(0.55, 1.25, n)
    _blades(G, A, D, L, rng.uniform(0.004, 0.007, n), np.radians(rng.uniform(10, 50, n)),
            "trawa_sucha" if season == "zima" else "trawa_zdzblo", rng, rows=4)
    return G


def lawn_tufts(poly_xy, density, seed, ctx, z=0.0, height=0.12):
    """Kępki trawy 3D na małym obszarze (zbliżenia): punkty w wielokącie + instancje (Geometry Nodes).
    poly_xy – lista (x, y) w układzie Blendera albo wielokąt shapely; density – kępek na m²."""
    import bpy
    import shapely
    from shapely.geometry import Polygon
    poly = poly_xy if hasattr(poly_xy, "area") else Polygon(poly_xy)
    rng = np.random.default_rng(seed)
    n = int(poly.area * density)
    if n <= 0:
        return []
    minx, miny, maxx, maxy = poly.bounds
    pts = np.zeros((0, 2))
    while len(pts) < n:
        c = rng.uniform((minx, miny), (maxx, maxy), (n * 2, 2))
        c = c[shapely.contains_xy(poly, c[:, 0], c[:, 1])]
        pts = np.concatenate([pts, c])
    pts = pts[:n]
    key = ("rosliny", "kepki", round(height, 3), ctx.season)
    coll = ctx.cache.get(key)
    if coll is None:
        coll = bpy.data.collections.new(f"kepki_trawy_{height:.2f}")
        for v in range(4):
            G = _tuft_geo(height, v, ctx.season)
            A = G.arrays()
            me = _mesh_from_arrays(f"kepka_{v}", A)
            for mk in G.mats:
                me.materials.append(_material(ctx, mk))
            coll.objects.link(bpy.data.objects.new(f"kepka_{v}", me))
        ctx.cache[key] = coll
    me = bpy.data.meshes.new("kepki_punkty")
    V = np.concatenate([pts, np.full((n, 1), z)], 1).astype(np.float32)
    me.vertices.add(n)
    me.vertices.foreach_set("co", V.ravel())
    me.update()
    ob = bpy.data.objects.new("kepki_trawy", me)
    ng = ctx.cache.get("rosliny:gn_kepki")
    if ng is None:
        ng = bpy.data.node_groups.new("kepki_trawy", "GeometryNodeTree")
        ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
        ng.interface.new_socket("Kolekcja", in_out="INPUT", socket_type="NodeSocketCollection")
        ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        N, L = ng.nodes, ng.links
        gi, go = N.new("NodeGroupInput"), N.new("NodeGroupOutput")
        m2p = N.new("GeometryNodeMeshToPoints")
        ci = N.new("GeometryNodeCollectionInfo")
        ci.transform_space = "ORIGINAL"
        ci.inputs["Separate Children"].default_value = True
        ci.inputs["Reset Children"].default_value = True
        iop = N.new("GeometryNodeInstanceOnPoints")
        iop.inputs["Pick Instance"].default_value = True
        ri = N.new("FunctionNodeRandomValue")
        ri.data_type = "INT"
        ri.inputs[4].default_value, ri.inputs[5].default_value = 0, 3
        rr_ = N.new("FunctionNodeRandomValue")
        rr_.data_type = "FLOAT_VECTOR"
        rr_.inputs[0].default_value = (-0.12, -0.12, 0.0)
        rr_.inputs[1].default_value = (0.12, 0.12, 6.2832)
        rr_.inputs[8].default_value = 7
        e2r = N.new("FunctionNodeEulerToRotation")
        rs = N.new("FunctionNodeRandomValue")
        rs.data_type = "FLOAT"
        rs.inputs[2].default_value, rs.inputs[3].default_value = 0.7, 1.3
        rs.inputs[8].default_value = 13
        L.new(gi.outputs[0], m2p.inputs["Mesh"])
        L.new(gi.outputs[1], ci.inputs["Collection"])
        L.new(m2p.outputs[0], iop.inputs["Points"])
        L.new(ci.outputs[0], iop.inputs["Instance"])
        L.new(ri.outputs[2], iop.inputs["Instance Index"])
        L.new(rr_.outputs[0], e2r.inputs[0])
        L.new(e2r.outputs[0], iop.inputs["Rotation"])
        L.new(rs.outputs[1], iop.inputs["Scale"])
        L.new(iop.outputs[0], go.inputs[0])
        ctx.cache["rosliny:gn_kepki"] = ng
    mod = ob.modifiers.new("kepki", "NODES")
    mod.node_group = ng
    ident = [it.identifier for it in ng.interface.items_tree if getattr(it, "in_out", "") == "INPUT"][1]
    mod[ident] = coll
    ctx.link(ob)
    return [ob]


if __name__ == "__main__" and "--tekstury" in sys.argv:
    tekstury(force="--force" in sys.argv)
