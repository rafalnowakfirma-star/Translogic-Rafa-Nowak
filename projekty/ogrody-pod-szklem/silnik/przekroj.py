"""Przekrój pionowy wzdłuż linii cięcia – generowany z modelu domu."""
import math

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

from .geom import polygons
from .dom import SLAB, THICK


def f(v):
    return f"{v:.1f}"


class SecCanvas:
    def __init__(self, hmin, hmax, zmin, zmax, s=30, pad_l=46, pad_r=96, pad_t=22, pad_b=26):
        self.s, self.hmin, self.zmax, self.pl, self.pt = s, hmin, zmax, pad_l, pad_t
        self.W = pad_l + pad_r + (hmax - hmin) * s
        self.H = pad_t + pad_b + (zmax - zmin) * s
        self.el = []

    def P(self, h, z):
        return (self.pl + (h - self.hmin) * self.s, self.pt + (self.zmax - z) * self.s)

    def rect(self, h1, z1, h2, z2, cls):
        if abs(h2 - h1) < 1e-4 or abs(z2 - z1) < 1e-4:
            return
        (x1, y1), (x2, y2) = self.P(min(h1, h2), max(z1, z2)), self.P(max(h1, h2), min(z1, z2))
        self.el.append(f'<rect x="{f(x1)}" y="{f(y1)}" width="{f(x2 - x1)}" height="{f(y2 - y1)}" class="{cls}"/>')

    def poly(self, pts, cls):
        self.el.append(f'<polygon points="{" ".join(f"{f(a)},{f(b)}" for a, b in (self.P(*p) for p in pts))}" class="{cls}"/>')

    def line(self, a, b, cls):
        (x1, y1), (x2, y2) = self.P(*a), self.P(*b)
        self.el.append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" class="{cls}"/>')

    def text(self, h, z, s, cls, anchor="middle", dy=0):
        a, b = self.P(h, z)
        self.el.append(f'<text x="{f(a)}" y="{f(b + dy)}" text-anchor="{anchor}" class="{cls}">{s}</text>')


def _intervals(line, geom):
    out = []
    if geom is None or geom.is_empty:
        return out
    inter = line.intersection(geom)
    for g in _lines(inter):
        cs = list(g.coords)
        h1 = line.project(Point(cs[0]))
        h2 = line.project(Point(cs[-1]))
        if abs(h2 - h1) > 1e-3:
            out.append((min(h1, h2), max(h1, h2)))
    return sorted(out)


def _lines(g):
    if g.is_empty:
        return []
    if g.geom_type == "LineString":
        return [g]
    out = []
    for x in getattr(g, "geoms", []):
        out.extend(_lines(x))
    return out


def section(house, name, a, b, uid):
    line = LineString([a, b])
    Ltot = line.length
    dx, dy = (b[0] - a[0]) / Ltot, (b[1] - a[1]) / Ltot
    look = (-dy, dx)
    zmax = 0.0
    for idx, L in house.L.items():
        lev = house.levels[idx]
        zmax = max(zmax, lev.z + lev.h)
    for r in house.all_rooms:
        if r.kind == "ogrod":
            rr = math.sqrt(r.poly.area / math.pi)
            rise = {"pyramid": rr * 0.55, "iris": rr * 0.18}.get(r.roof_type, 0.0)
            zmax = max(zmax, r.roof_z + rise + 1.3)
    C = SecCanvas(-1.5, Ltot + 1.5, -1.2, zmax + 1.6)
    # niebo / tło ogrodów
    C.rect(-1.5, -0.3, Ltot + 1.5, zmax + 1.6, "s-sky")
    # grunt
    C.el.append('<defs><pattern id="s-hatch" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                '<line x1="0" y1="0" x2="0" y2="9" style="stroke:var(--r-ink3);stroke-width:.7"/></pattern></defs>')
    C.rect(-1.5, -1.2, Ltot + 1.5, -0.3, "s-ground")
    C.line((-1.5, -0.3), (Ltot + 1.5, -0.3), "s-line")
    base_idx = min(house.L)
    # elementy ogrodu za linią cięcia (sylwetki)
    for r in house.all_rooms:
        if r.kind != "ogrod":
            continue
        for h1, h2 in _intervals(line, r.poly):
            C.rect(h1, -0.3, h2, -0.12, "s-gravel")
        lay = getattr(r, "_layout", None)
        if lay is None:
            from .ogrod import garden_layout
            lay = garden_layout(r, house.L[r.level], house)
            r._layout = lay
        for kind, geom in lay["floor"]:
            if kind == "woda":
                for h1, h2 in _intervals(line, geom):
                    C.rect(h1, -0.55, h2, -0.15, "s-water")
        for ft in lay["features"]:
            p = Point(ft.x, ft.y)
            d = (ft.x - a[0]) * look[0] + (ft.y - a[1]) * look[1]
            h = line.project(p)
            if -0.8 < d < 6.0 and 0 < h < Ltot:
                hgt = ft.kw.get("h", 1.0)
                if ft.t in ("klon", "brzoza", "oliwka", "sosna", "palma", "cytrus"):
                    cls = {"klon": "s-maple", "brzoza": "s-birch", "oliwka": "s-olive"}.get(ft.t, "s-tree")
                    _tree(C, h, -0.15, hgt, max(0.6, ft.r * 1.1), cls)
                elif ft.t in ("kamien", "misa", "latarnia"):
                    C.rect(h - ft.r, -0.15, h + ft.r, -0.15 + (0.45 if ft.t != "latarnia" else 1.0), "s-beyond")
    # pomieszczenia: tło i opisy
    labels = []
    for idx, L in house.L.items():
        for r in L["rooms"]:
            if r.kind in ("ogrod", "ogrod_void"):
                continue
            for h1, h2 in _intervals(line, r.poly):
                if r.parent is None:
                    labels.append((r, h1, h2))
    for r, h1, h2 in labels:
        if r.outdoor:
            continue
        C.rect(h1, r.z0, h2, r.top, "s-room")
    for idx, L in house.L.items():
        for r in L["rooms"]:
            if r.kind == "void":
                for h1, h2 in _intervals(line, r.poly):
                    C.rect(h1, r.z0 - SLAB, h2, r.top, "s-room")
    # stropy, płyta, dachy
    if base_idx in house.L:
        base = house.L[base_idx].get("base")
        for h1, h2 in _intervals(line, base.buffer(0.2) if base is not None else None):
            C.rect(h1, -0.35, h2, 0.0, "s-slab")
    for z, poly, kind in house.slabs:
        for h1, h2 in _intervals(line, poly):
            C.rect(h1, z - SLAB, h2, z, "s-slab")
    for z, poly, fin, li in house.roofs:
        for h1, h2 in _intervals(line, poly.buffer(0.2)):
            C.rect(h1, z - SLAB, h2, z, "s-slab")
            C.rect(h1 + 0.25, z, h2 - 0.25, z + 0.12, "s-green" if fin == "sedum" else "s-gravel")
            C.rect(h1, z, h1 + 0.25, z + 0.45, "s-slab")
            C.rect(h2 - 0.25, z, h2, z + 0.45, "s-slab")
            zmax = max(zmax, z)
    for r, poly in house.patio_roofs:
        lev = house.levels[r.level]
        z = lev.z + lev.h
        for h1, h2 in _intervals(line, poly):
            C.rect(h1, z - SLAB, h2, z, "s-slab")
    for r in house.all_rooms:
        if r.outdoor and r.roof == "full" and r.parent is None:
            lev = house.levels[r.level]
            z = lev.z + lev.h
            for h1, h2 in _intervals(line, r.poly):
                C.rect(h1, z - SLAB, h2, z, "s-slab")
        if r.outdoor and r.parent is None:
            for h1, h2 in _intervals(line, r.poly):
                C.rect(h1, r.z0 - 0.12, h2, r.z0, "s-deck")
    # ściany
    for idx, L in house.L.items():
        geoms = L.get("wall_geoms", {})
        for cls, g in geoms.items():
            for h1, h2 in _intervals(line, g):
                hm = (h1 + h2) / 2
                pm = line.interpolate(hm)
                run = _nearest_run(L, cls, pm)
                z0 = run.z0 if run is not None else house.levels[idx].z
                z1 = run.z1 if run is not None else house.levels[idx].z + house.levels[idx].h
                op = None
                for o in L["openings"]:
                    if o.footprint(0.02).contains(pm):
                        op = o
                        break
                if cls in ("glass", "fold"):
                    C.rect(h1, z0, h2, z0 + 0.06, "s-cut")
                    C.rect(h1 + 0.02, z0 + 0.06, h2 - 0.02, z1 - SLAB - 0.05, "s-glass")
                    continue
                if cls == "railing":
                    C.rect(h1, z0, h2, z0 + 1.05, "s-glass")
                    continue
                if op is None:
                    C.rect(h1, z0, h2, z1, "s-cut")
                else:
                    zf = op.z_floor
                    if op.sill > 0.02:
                        C.rect(h1, z0, h2, zf + op.sill, "s-cut")
                    C.rect(h1, zf + op.head, h2, z1, "s-cut")
                    if op.kind in ("win", "band", "slide"):
                        C.rect(h1 + 0.03, zf + op.sill, h2 - 0.03, zf + op.head, "s-glass")
    # schody przecięte linią
    for s in house.stairs:
        if s.kind == "spiral":
            iv = _intervals(line, s.footprint())
            if not iv:
                continue
            z0 = house.levels[s.level].z
            z1 = house.levels[s.to_level].z if s.to_level in house.levels else z0 + 3.0
            _flight(C, iv[0][0], iv[-1][1], z0, z1, max(6, int(round((z1 - z0) / 0.18))))
            continue
        fls, landing = s.flights(house)
        for (x1, y1, x2, y2), d, za, zb in fls:
            iv = _intervals(line, Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)]))
            if not iv:
                continue
            h1, h2 = iv[0][0], iv[-1][1]
            fv = {"E": (1, 0), "W": (-1, 0), "S": (0, 1), "N": (0, -1)}[d]
            length = (x2 - x1) if d in ("E", "W") else (y2 - y1)
            n = max(2, int(round((zb - za) / 0.175)))

            def zat(p, d=d, x1=x1, y1=y1, x2=x2, y2=y2, length=length, za=za, zb=zb):
                t = {"E": (p.x - x1), "W": (x2 - p.x), "S": (p.y - y1), "N": (y2 - p.y)}[d] / length
                return za + (zb - za) * min(1.0, max(0.0, t))

            pa, pb = line.interpolate(h1), line.interpolate(h2)
            if abs(fv[0] * dx + fv[1] * dy) > 0.7:
                z_a, z_b = zat(pa), zat(pb)
                k = max(1, int(round(abs(z_b - z_a) / ((zb - za) / n))))
                if z_a <= z_b:
                    _flight(C, h1, h2, z_a, z_b, k)
                else:
                    _flight(C, h2, h1, z_b, z_a, k)
            else:
                # bieg prostopadły do przekroju: widok stopni za płaszczyzną cięcia + przecięty stopień
                zc = zat(line.interpolate((h1 + h2) / 2))
                ahead = fv[0] * look[0] + fv[1] * look[1] > 0
                zlo, zhi = (zc - 0.22, zb) if ahead else (za, zc)
                if zhi - zlo > 0.05:
                    C.rect(h1, zlo, h2, zhi, "s-stairv")
                    rz = (zb - za) / n
                    k = za + rz
                    while k < zhi - 0.02:
                        if k > zlo + 0.02:
                            C.line((h1, k), (h2, k), "s-stairl")
                        k += rz
                C.rect(h1, zc - 0.22, h2, zc, "s-stair")
        if landing is not None:
            lp, zm = landing
            for h1, h2 in _intervals(line, Polygon([(lp[0], lp[1]), (lp[2], lp[1]), (lp[2], lp[3]), (lp[0], lp[3])])):
                C.rect(h1, zm - 0.22, h2, zm, "s-stair")
    # dach szklany nad ogrodem
    for g in [r for r in house.all_rooms if r.kind == "ogrod"]:
        for h1, h2 in _intervals(line, g.poly):
            _glass_roof(C, g, h1, h2)
    # opisy pomieszczeń
    stair_iv = []
    for s in house.stairs:
        for a_, b_ in _intervals(line, s.footprint()):
            stair_iv.append((a_ - 0.15, b_ + 0.15, s.level, s.to_level))
    for r, h1, h2 in labels:
        if h2 - h1 < 1.4:
            continue
        z = r.z0 + 2.05
        top = r.top
        if r.levels > 1:
            z = r.z0 + (top - r.z0) * 0.5
        # wolny odcinek bez schodów
        segs = [(h1, h2)]
        for a_, b_, l0, l1 in stair_iv:
            if r.level != l0 and not (r.levels > 1 and l0 >= r.level and l0 < r.level + r.levels):
                continue
            nxt = []
            for u, v in segs:
                if b_ <= u or a_ >= v:
                    nxt.append((u, v))
                    continue
                if a_ > u:
                    nxt.append((u, a_))
                if b_ < v:
                    nxt.append((b_, v))
            segs = nxt
        u, v = max(segs, key=lambda t: t[1] - t[0]) if segs else (h1, h2)
        if v - u < 1.2 or ((v - u) * C.s < len(r.name) * 6.2 <= (h2 - h1) * C.s and not segs):
            u, v = h1, h2
        nm = r.name if (v - u) * C.s > len(r.name) * 6.2 else r.name.split(" ")[0]
        C.text((u + v) / 2, z, nm, "t-sroom")
    for r in house.all_rooms:
        if r.kind == "ogrod":
            for h1, h2 in _intervals(line, r.poly):
                # podpis tuż pod szklanym dachem, nad koronami drzew
                C.text((h1 + h2) / 2, max(2.6, r.roof_z - 0.75), r.name.lower(), "t-garden")
    # ludzie dla skali
    done = 0
    for r, h1, h2 in sorted(labels, key=lambda t: -(t[2] - t[1])):
        if done >= 2 or r.outdoor or h2 - h1 < 3:
            continue
        _person(C, h1 + (h2 - h1) * 0.7, r.z0)
        done += 1
    for r in house.all_rooms:
        if r.kind == "ogrod":
            for h1, h2 in _intervals(line, r.poly):
                _person(C, h1 + (h2 - h1) * 0.3, -0.12)
                break
    # słońce zimą i latem (cięcie mniej więcej północ–południe)
    if abs(dy) > 0.7:
        gl = [r for r in house.all_rooms if r.kind == "ogrod"]
        if gl:
            g = gl[0]
            iv = _intervals(line, g.poly)
            if iv:
                h1, h2 = iv[0]
                hm = (h1 + h2) / 2
                sgn = 1 if dy > 0 else -1
                for alt, lab in ((15, "słońce w grudniu 15°"), (61, "słońce w czerwcu 61°")):
                    t = math.radians(alt)
                    ztop = zmax + 0.9
                    hs = hm + sgn * (ztop / math.tan(t))
                    if hs < -1.3 or hs > Ltot + 1.3:
                        hs = max(-1.3, min(Ltot + 1.3, hs))
                        ztop = abs(hs - hm) * math.tan(t)
                    C.line((hs, ztop), (hm, 0.0), "s-sun")
                    C.text(hs, ztop + 0.2, lab, "t-snote", anchor="end" if hs > hm else "start")
    # poziomy
    lv = set()
    for idx, L in house.L.items():
        lv.add(round(house.levels[idx].z, 2))
    for z, poly, fin, li in house.roofs:
        lv.add(round(z, 2))
    for g in [r for r in house.all_rooms if r.kind == "ogrod"]:
        lv.add(round(g.roof_z, 2))
    hx = Ltot + 0.9
    prev = None
    for z in sorted(lv):
        (x, y) = C.P(hx, z)
        if prev is not None and abs(z - prev) < 0.45:
            x += 44
        prev = z
        C.el.append(f'<polygon points="{f(x)},{f(y)} {f(x - 4.5)},{f(y - 7)} {f(x + 4.5)},{f(y - 7)}" class="s-lvl"/>'
                    f'<line x1="{f(x - 7)}" y1="{f(y)}" x2="{f(x + 34)}" y2="{f(y)}" class="s-thin"/>'
                    f'<text x="{f(x + 7)}" y="{f(y - 3)}" class="d-t">{"±0,00" if abs(z) < 1e-3 else f"{z:+.2f}".replace(".", ",")}</text>')
    C.text(-1.3, zmax + 1.2, f"PRZEKRÓJ {name}", "t-sheet", anchor="start")
    return (f'<svg class="drw sec" viewBox="0 0 {C.W:.0f} {C.H:.0f}" role="img" aria-label="{house.name} – przekrój {name}" '
            f'xmlns="http://www.w3.org/2000/svg">' + "".join(C.el) + "</svg>")


def _flight(C, ha, hb, za, zb, n):
    """Bieg schodów jako schodkowa linia od (ha, za) do (hb, zb)."""
    pts = [(ha, za)]
    for i in range(n):
        h = ha + (hb - ha) * (i / n)
        z = za + (zb - za) * ((i + 1) / n)
        pts.append((h, z))
        pts.append((ha + (hb - ha) * ((i + 1) / n), z))
    pts.append((hb, zb - 0.25))
    pts.append((ha, za - 0.25))
    C.poly(pts, "s-stair")


def _nearest_run(L, cls, p):
    best, bd = None, 1e9
    for run in L["walls"]:
        if run.cls != cls:
            continue
        d = run.line.distance(p)
        if d < bd:
            best, bd = run, d
    return best


def _tree(C, h, z, ht, r, cls):
    (x, y) = C.P(h, z)
    s = C.s
    C.el.append(f'<line x1="{f(x)}" y1="{f(y)}" x2="{f(x)}" y2="{f(y - (ht - r) * s)}" class="s-trunk"/>'
                f'<ellipse cx="{f(x)}" cy="{f(y - (ht - r) * s)}" rx="{f(r * s)}" ry="{f(r * 0.85 * s)}" class="{cls}"/>')


def _person(C, h, z):
    x, y = C.P(h, z)
    s = C.s
    C.el.append(f'<g class="s-person"><circle cx="{f(x)}" cy="{f(y - 1.62 * s)}" r="{f(0.12 * s)}"/>'
                f'<rect x="{f(x - 0.18 * s)}" y="{f(y - 1.48 * s)}" width="{f(0.36 * s)}" height="{f(0.7 * s)}" rx="{f(0.1 * s)}"/>'
                f'<rect x="{f(x - 0.13 * s)}" y="{f(y - 0.85 * s)}" width="{f(0.11 * s)}" height="{f(0.85 * s)}"/>'
                f'<rect x="{f(x + 0.02 * s)}" y="{f(y - 0.85 * s)}" width="{f(0.11 * s)}" height="{f(0.85 * s)}"/></g>')


def _glass_roof(C, g, h1, h2):
    z = g.roof_z
    t = g.roof_type
    w = h2 - h1
    if t in ("slide", "fold", "louvre"):
        C.rect(h1, z - 0.18, h2, z - 0.06, "s-gframe")
        if t == "louvre":
            n = max(3, int(w / 0.4))
            for i in range(n):
                hc = h1 + (i + 0.5) * w / n
                C.line((hc - 0.17, z + 0.1), (hc + 0.17, z + 0.3), "s-arrow")
            return
        mid = (h1 + h2) / 2
        C.rect(h1, z - 0.06, mid, z, "s-glass")
        C.rect(mid - w * 0.35, z + 0.06, mid + w * 0.15 - w * 0.35 + w * 0.35, z + 0.12, "s-glass")
        C.line((mid - w * 0.3, z + 0.32), (mid + w * 0.1, z + 0.32), "s-arrow")
    elif t in ("ridge",):
        hm = (h1 + h2) / 2
        C.poly([(h1, z - 0.1), (hm, z + w * 0.18), (h2, z - 0.1), (h2, z), (hm, z + w * 0.18 + 0.1), (h1, z)], "s-glass")
    elif t in ("pyramid", "iris"):
        hm = (h1 + h2) / 2
        top = z + w * (0.32 if t == "pyramid" else 0.12)
        C.poly([(h1, z - 0.1), (hm - w * 0.14, top - 0.1), (hm + w * 0.14, top - 0.1), (h2, z - 0.1), (h2, z), (hm + w * 0.14, top), (hm - w * 0.14, top), (h1, z)], "s-glass")
        C.rect(hm - w * 0.14, top + 0.25, hm + w * 0.14, top + 0.35, "s-glass")
        C.line((hm - w * 0.1, top + 0.55), (hm + w * 0.1, top + 0.55), "s-arrow")
    elif t == "vault":
        pts = []
        n = 16
        for i in range(n + 1):
            u = i / n
            pts.append((h1 + w * u, z + math.sin(math.pi * u) * w * 0.25))
        C.poly(pts + [(p[0], p[1] + 0.1) for p in reversed(pts)], "s-glass")
