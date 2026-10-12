"""Bryła 3D z modelu domu: trójkąty pogrupowane wg materiału i wariantu (base / lato / zima).

Współrzędne planu: x – wschód, y – południe, z – w górę.
"""
import math
import random

import shapely
from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely.ops import unary_union

from .geom import polygons, largest
from .dom import SLAB, THICK
from .meble import furnish_level

FACADE = {"tynk": "tynk", "beton": "beton", "drewno": "drewno", "drewno_opal": "drewno_opal", "cegla": "cegla",
          "cegla_biala": "cegla_biala", "kamien": "kamien", "corten": "corten", "miedz": "miedz", "blacha": "blacha",
          "trawertyn": "trawertyn"}
FLOOR_MAT = {"drewno": "podloga_drewno", "drewno_ciemne": "podloga_ciemna", "deska": "deck", "kamien": "podloga_kamien",
             "trawertyn": "podloga_kamien", "plyty": "podloga_kamien", "terakota": "podloga_terakota", "cegla": "podloga_terakota",
             "tatami": "podloga_tatami", "beton": "podloga_beton"}


class Mesh:
    def __init__(self):
        self.g = {}   # (wariant, materiał) → lista trójkątów [(p1,p2,p3)]
        self.lights = []   # (x, y, z, w, d) – panele światła do renderu wieczornego
        self.cams = {}

    def tri(self, var, mat, a, b, c):
        self.g.setdefault((var, mat), []).append((a, b, c))

    def poly_flat(self, poly, z, mat, var="base", up=True):
        for p in polygons(poly):
            if p.area < 1e-5:
                continue
            try:
                tris = shapely.constrained_delaunay_triangles(p)
            except Exception:
                tris = shapely.ops.triangulate(p)
            for t in getattr(tris, "geoms", []):
                cs = list(t.exterior.coords)[:3]
                a, b, c = [(x, y, z) for x, y in cs]
                # normalna do góry: w układzie (x, y-na-południe) odwrotna kolejność
                if _area2(cs) > 0 and up or _area2(cs) < 0 and not up:
                    self.tri(var, mat, a, c, b)
                else:
                    self.tri(var, mat, a, b, c)

    def extrude(self, poly, z0, z1, mat, var="base", top=True, bottom=True, side_mat=None):
        if z1 - z0 < 1e-4:
            return
        for p in polygons(poly):
            if p.area < 1e-5:
                continue
            if top:
                self.poly_flat(p, z1, mat, var, up=True)
            if bottom:
                self.poly_flat(p, z0, mat, var, up=False)
            sm = side_mat or mat
            for ring in [p.exterior] + list(p.interiors):
                cs = list(ring.coords)
                for (x1, y1), (x2, y2) in zip(cs, cs[1:]):
                    if abs(x1 - x2) + abs(y1 - y2) < 1e-6:
                        continue
                    a, b = (x1, y1, z0), (x2, y2, z0)
                    c, d = (x2, y2, z1), (x1, y1, z1)
                    self.tri(var, sm, a, b, c)
                    self.tri(var, sm, a, c, d)

    def box(self, cx, cy, z0, w, d, h, rot, mat, var="base"):
        a = math.radians(rot)
        ca, sa = math.cos(a), math.sin(a)
        pts = []
        for lx, ly in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)):
            pts.append((cx + lx * ca - ly * sa, cy + lx * sa + ly * ca))
        self.extrude(Polygon(pts), z0, z0 + h, mat, var)

    def seg_box(self, a, b, t, z0, z1, mat, var="base"):
        """Płyta wzdłuż odcinka a–b (grubość t)."""
        ln = LineString([a, b])
        if ln.length < 1e-4:
            return
        self.extrude(ln.buffer(t / 2, cap_style="flat"), z0, z1, mat, var)

    def cyl(self, cx, cy, z0, r, h, mat, var="base", n=14):
        self.extrude(Point(cx, cy).buffer(r, max(3, n // 4)), z0, z0 + h, mat, var)

    def cone(self, cx, cy, z0, r, h, mat, var="base", n=12):
        pts = [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
        top = (cx, cy, z0 + h)
        for i in range(n):
            p1, p2 = pts[i], pts[(i + 1) % n]
            self.tri(var, mat, (p1[0], p1[1], z0), (p2[0], p2[1], z0), top)
        self.poly_flat(Polygon(pts), z0, mat, var, up=False)

    def sphere(self, cx, cy, cz, r, mat, var="base", sx=1.0, sy=1.0, sz=1.0, seed=0, jitter=0.0, sub=1):
        rnd = random.Random(seed)
        verts, faces = _icosphere(sub)
        vv = []
        for x, y, z in verts:
            j = 1 + (rnd.uniform(-jitter, jitter) if jitter else 0)
            vv.append((cx + x * r * sx * j, cy + y * r * sy * j, cz + z * r * sz * j))
        for i, j, k in faces:
            self.tri(var, mat, vv[i], vv[j], vv[k])

    def quad(self, p1, p2, p3, p4, mat, var="base"):
        self.tri(var, mat, p1, p2, p3)
        self.tri(var, mat, p1, p3, p4)


def _area2(cs):
    (x1, y1), (x2, y2), (x3, y3) = cs[:3]
    return (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)


_ICO = {}


def _icosphere(sub):
    if sub in _ICO:
        return _ICO[sub]
    t = (1 + 5 ** 0.5) / 2
    v = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
         (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    v = [tuple(c / math.sqrt(sum(q * q for q in p)) for c in p) for p in v]
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
         (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(sub):
        cache = {}
        nf = []

        def mid(i, j):
            key = (min(i, j), max(i, j))
            if key not in cache:
                a, b = v[i], v[j]
                m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2)
                L = math.sqrt(sum(q * q for q in m))
                v.append(tuple(q / L for q in m))
                cache[key] = len(v) - 1
            return cache[key]
        for a, b, c in f:
            ab, bc, ca = mid(a, b), mid(b, c), mid(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        f = nf
    _ICO[sub] = (v, f)
    return v, f


# ------------------------------------------------------------------ budowa bryły
def build_mesh(house, meble=True, rosliny=True, ludzie=True, dach_t=None):
    """meble/rosliny/ludzie=False – pomija uproszczone bryły (film wstawia w ich miejsce realistyczne modele);
    dach_t (0 zamknięty … 1 otwarty) – ruchome części szklanego dachu w stanie pośrednim, wariant "ruch"."""
    M = Mesh()
    fac = FACADE.get(house.style.get("fasada", "tynk"), "tynk")
    base_idx = house.ground
    # teren
    minx, miny, maxx, maxy = house.bbox
    M.extrude(house.footprint.buffer(0.25, join_style="mitre"), -0.32, 0.0, "beton_cokol", top=False)
    for idx in sorted(house.L):
        L = house.L[idx]
        lev = house.levels[idx]
        _walls(M, house, L, fac)
        _openings3d(M, house, L, fac)
        # posadzki
        for r in L["rooms"]:
            if r.kind in ("ogrod", "ogrod_void", "void") or r.parent is not None:
                continue
            if r.outdoor:
                z = r.z0
                mat = "deck" if r.floor in ("deska", "drewno") else FLOOR_MAT.get(r.floor, "deck")
                if r.level > base_idx:
                    # taras na stropie: deski 5 cm nad płytą (bez migotania płaszczyzn)
                    M.extrude(r.net if r.net is not None else r.poly, z + 0.005, z + 0.05, mat)
                else:
                    M.extrude(r.net if r.net is not None else r.poly, z - 0.14, z, mat)
                continue
            net = r.net if r.net is not None else r.poly
            for fp, s in L.get("voids", []):
                net = net.difference(fp)
            M.poly_flat(net, r.z0 + 0.004, FLOOR_MAT.get(r.floor, "podloga_drewno"))
            # sufit / panel światła
            lp = (r.net or r.poly).buffer(-0.8)
            if not lp.is_empty and lp.area > 1.5 and r.kind not in ("garderoba", "spizarnia", "techniczne"):
                M.lights.append((largest(lp), r.top - 0.02, r.kind))
        # meble
        items = L.get("items")
        if items is None:
            items = furnish_level(house, idx)
            L["items"] = items
        if meble:
            for it in items:
                _item3d(M, it)
    # stropy
    for z, poly, kind in house.slabs:
        M.extrude(poly, z - SLAB, z, "strop")
    # podstawa poziomu 0 (płyta)
    base = house.L[base_idx].get("base")
    if base is not None and not base.is_empty:
        M.extrude(base, -0.3, 0.0, "strop", top=False)
    # dachy
    for z, poly, fin, li in house.roofs:
        M.extrude(poly, z - SLAB, z, "strop")
        inner = poly.buffer(-0.25, join_style="mitre")
        M.extrude(poly.difference(inner) if not inner.is_empty else poly, z, z + 0.45, fac)
        if not inner.is_empty:
            M.extrude(inner, z, z + 0.1, "sedum" if fin == "sedum" else "zwir_dach", bottom=False)
    for r, poly in house.patio_roofs:
        lev = house.levels[r.level]
        z = lev.z + lev.h
        M.extrude(poly, z - SLAB, z, fac)
        _posts(M, house, r, poly, r.z0, z - SLAB)
    for r in house.all_rooms:
        if r.outdoor and r.roof == "full" and r.parent is None:
            lev = house.levels[r.level]
            z = lev.z + lev.h
            rp = r.poly.representative_point()
            covered = any(abs(rz - z) < 0.05 and poly.contains(rp) for rz, poly, fin, li in house.roofs) or \
                any(abs(sz - z) < 0.05 and poly.contains(rp) for sz, poly, kind in house.slabs)
            if not covered:
                M.extrude(r.poly, z - SLAB, z, fac)
            _posts(M, house, r, r.poly, r.z0, z - SLAB)
    # ogród
    for g in [r for r in house.all_rooms if r.kind == "ogrod"]:
        _garden3d(M, house, g, rosliny)
        _glass_roof3d(M, house, g, dach_t)
    # teren wokół
    for s_ in house.site:
        if s_["t"] == "path":
            M.extrude(s_["shape"], -0.32, -0.27, "sciezka", bottom=False)
        elif s_["t"] == "tree" and rosliny:
            _tree3d(M, s_["kind"], s_["x"], s_["y"], -0.3, s_.get("h") or 7.5, s_.get("r") or 2.0, seed=int(s_["x"] * 13 + s_["y"]))
    _stairs3d(M, house)
    # ludzie
    if ludzie:
        _people(M, house)
    return M


def _stairs3d(M, house):
    """Schody: biegi z drewnianych stopni (proste, U) albo kręte wokół słupa."""
    for s in house.stairs:
        if s.level not in house.levels or s.to_level not in house.levels:
            continue
        z0 = house.levels[s.level].z
        z1 = house.levels[s.to_level].z
        H = z1 - z0
        if s.kind == "spiral":
            cx, cy = s.p["center"]
            r = s.p.get("r", 1.0)
            a0, sw = s.p.get("start", 90), s.p.get("sweep", 300)
            n = s.p.get("n", 15)
            hr = H / (n + 1)
            for i in range(n):
                a1 = math.radians(a0 + sw * i / n)
                a2 = math.radians(a0 + sw * (i + 1) / n)
                pts = [(cx + 0.1 * math.cos(a1), cy + 0.1 * math.sin(a1))]
                for k in range(5):
                    a = a1 + (a2 - a1) * k / 4
                    pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
                pts.append((cx + 0.1 * math.cos(a2), cy + 0.1 * math.sin(a2)))
                zt = z0 + hr * (i + 1)
                M.extrude(Polygon(pts), zt - 0.06, zt, "podloga_drewno")
            M.cyl(cx, cy, z0, 0.09, H + 1.0, "rama", n=10)
            continue
        fls, landing = s.flights(house)
        if landing is not None:
            lp, zm = landing
            M.extrude(Polygon([(lp[0], lp[1]), (lp[2], lp[1]), (lp[2], lp[3]), (lp[0], lp[3])]), zm - 0.2, zm, "podloga_drewno")
        for (a1, b1, a2, b2), d, za, zb in fls:
            horiz = d in ("E", "W")
            length = (a2 - a1) if horiz else (b2 - b1)
            n = max(2, int(round((zb - za) / 0.175)))
            g = length / n
            hr = (zb - za) / n
            for i in range(n):
                # i-ty stopień licząc od dołu biegu
                if d == "E":
                    q = (a1 + g * i, b1, a1 + g * (i + 1), b2)
                elif d == "W":
                    q = (a2 - g * (i + 1), b1, a2 - g * i, b2)
                elif d == "S":
                    q = (a1, b1 + g * i, a2, b1 + g * (i + 1))
                else:
                    q = (a1, b2 - g * (i + 1), a2, b2 - g * i)
                zt = za + hr * (i + 1)
                M.extrude(Polygon([(q[0], q[1]), (q[2], q[1]), (q[2], q[3]), (q[0], q[3])]), zt - 0.07, zt, "podloga_drewno")


def _wall_mat(cls, fac):
    return {"ext": fac, "int": "tynk_wew", "gwall": fac, "low": fac}.get(cls, fac)


def _walls(M, house, L, fac):
    lev = L["level"]
    groups = {}
    for run in L["walls"]:
        if run.cls in ("ext", "int", "gwall", "low"):
            groups.setdefault((run.cls, round(run.z0, 3), round(run.z1, 3)), []).append(run)
    cuts = {}
    for o in L["openings"]:
        cuts.setdefault(o.cls, []).append(o)
    for (cls, z0, z1), runs in groups.items():
        t = THICK[cls]
        from shapely.ops import linemerge
        from shapely.geometry import MultiLineString
        lines = [r.line for r in runs]
        merged = linemerge(MultiLineString([list(l.coords) for l in lines])) if len(lines) > 1 else lines[0]
        g = merged.buffer(t / 2, cap_style="square" if cls == "ext" else "flat", join_style="mitre", mitre_limit=4.0)
        ops = [o for o in cuts.get(cls, []) if any(o.run is r or (o.run.line.distance(r.line) < 1e-3 and o.run.room is r.room) for r in runs)]
        holes = unary_union([o.footprint() for o in ops]) if ops else None
        solid = g.difference(holes) if holes is not None else g
        mat = _wall_mat(cls, fac)
        M.extrude(solid, z0, z1, mat)
        # wnętrze ścian zewnętrznych w kolorze tynku wewnętrznego – pomijamy (fasada z obu stron)
        for o in ops:
            fp = o.footprint().intersection(g)
            if fp.is_empty:
                continue
            zf = o.z_floor
            if o.sill > 0.02:
                M.extrude(fp, z0, zf + o.sill, mat)
            M.extrude(fp, zf + o.head, z1, mat)


def _openings3d(M, house, L, fac):
    for o in L["openings"]:
        zf = o.z_floor
        ext = o.run.other is None or o.run.other.outdoor
        if o.kind in ("win", "band"):
            _pane(M, o.a, o.b, zf + o.sill, zf + o.head, mullion=1.6)
        elif o.kind == "slide":
            if o.cls in ("glass", "fold"):
                continue
            _pane(M, o.a, o.b, zf + 0.02, zf + o.head, mullion=1.4)
        elif o.kind in ("door", "pivot", "double") and ext:
            M.seg_box(o.a, o.b, 0.06, zf, zf + o.head, "drzwi")
    # przeszklenia ciągłe
    for run in L["walls"]:
        if run.cls in ("glass", "fold"):
            _glass_run(M, run)
        elif run.cls == "railing":
            for a, b in zip(run.pts, run.pts[1:]):
                M.seg_box(a, b, 0.03, run.z0, run.z0 + 1.0, "szklo")
                M.seg_box(a, b, 0.06, run.z0 + 1.0, run.z0 + 1.05, "rama")
        elif run.cls == "columns":
            n = max(2, int(run.length / 2.4) + 1)
            for i in range(n):
                p = run.point_at(run.length * i / (n - 1))
                M.box(p[0], p[1], run.z0, 0.25, 0.25, run.z1 - run.z0, 0, fac)


def _pane(M, a, b, z0, z1, mullion=1.6):
    M.seg_box(a, b, 0.03, z0 + 0.05, z1 - 0.05, "szklo")
    M.seg_box(a, b, 0.07, z0, z0 + 0.06, "rama")
    M.seg_box(a, b, 0.07, z1 - 0.06, z1, "rama")
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, int(L / mullion + 0.5))
    for i in range(n + 1):
        t = i / n
        p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        q1 = (p[0] - ux * 0.03, p[1] - uy * 0.03)
        q2 = (p[0] + ux * 0.03, p[1] + uy * 0.03)
        M.seg_box(q1, q2, 0.08, z0, z1, "rama")


def _glass_run(M, run):
    z0, z1 = run.z0, run.z1 - SLAB + 0.02
    if run.cls == "glass":
        for a, b in zip(run.pts, run.pts[1:]):
            _pane(M, a, b, z0, z1, mullion=1.25)
        return
    # fold: lato – panele złożone przy końcach, zima – zamknięte
    for a, b in zip(run.pts, run.pts[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(2, int(L / 0.8))
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        nx, ny = -uy, ux
        if run.room.kind in ("ogrod", "ogrod_void"):
            nx, ny = -nx, -ny   # pakiety po stronie dziedzińca / patio, nie w ogrodzie
        for i in range(n):
            p1 = (a[0] + ux * L * i / n, a[1] + uy * L * i / n)
            p2 = (a[0] + ux * L * (i + 1) / n, a[1] + uy * L * (i + 1) / n)
            M.seg_box(p1, p2, 0.03, z0 + 0.05, z1 - 0.05, "szklo", var="zima")
            M.seg_box(p1, p2, 0.07, z0 + 0.05, z0 + 0.1, "rama", var="zima")
        # lato: panele złożone w pakiety przy obu końcach, prostopadle do ściany
        half = n // 2
        pw = min(0.8, L / n)
        for side, base in ((0, a), (1, b)):
            cnt = half if side == 0 else n - half
            sgn = 1 if side == 0 else -1
            for k in range(cnt):
                c = (base[0] + ux * sgn * (0.07 + 0.065 * k), base[1] + uy * sgn * (0.07 + 0.065 * k))
                pb = (c[0] + nx * pw, c[1] + ny * pw)
                M.seg_box(c, pb, 0.03, z0 + 0.05, z1 - 0.05, "szklo", var="lato")
        M.seg_box(a, b, 0.07, z1 - 0.08, z1, "rama")


def _posts(M, house, r, poly, z0, z1):
    L = house.L[r.level]
    wu = L["wall_union"]
    for p in list(poly.exterior.coords)[:-1]:
        q = Point(p)
        if wu.is_empty or wu.distance(q) > 0.3:
            M.box(p[0], p[1], z0, 0.22, 0.22, z1 - z0, 0, "rama")


def _item3d(M, it):
    a = math.radians(it.rot)
    ca, sa = math.cos(a), math.sin(a)
    for part in it.parts:
        k = part[0]
        if k == "box":
            _, x, y, z, w, d, h, mat = part
            cx, cy = it.cx + x * ca - y * sa, it.cy + x * sa + y * ca
            M.box(cx, cy, it.z + z, w, d, h, it.rot, mat)
        elif k == "cyl":
            _, x, y, z, r, h, mat = part
            cx, cy = it.cx + x * ca - y * sa, it.cy + x * sa + y * ca
            M.cyl(cx, cy, it.z + z, r, h, mat, n=12)
        elif k == "sph":
            _, x, y, z, r, mat = part
            cx, cy = it.cx + x * ca - y * sa, it.cy + x * sa + y * ca
            M.sphere(cx, cy, it.z + z, r, mat, sz=0.9, seed=int(cx * 31 + cy * 7), jitter=0.12)


# ------------------------------------------------------------------- ogród 3D
ROSLINY = ("mech", "kamien", "klon", "brzoza", "oliwka", "sosna", "palma", "cytrus", "lilia", "paproc", "lawenda",
           "monstera", "donica")


def _garden3d(M, house, g, rosliny=True):
    from .ogrod import garden_layout
    lay = getattr(g, "_layout", None)
    if lay is None:
        lay = garden_layout(g, house.L[g.level], house)
        g._layout = lay
    z = g.z0 - (0.0 if g.style == "jadalnia" else 0.12)   # ogród-jadalnia w poziomie podłogi
    net = lay["net"]
    floors = lay["floor"]
    water = [geom for kind, geom in floors if kind == "woda"]
    wu = unary_union(water) if water else None
    for kind, geom in floors:
        if kind == "woda":
            continue
        gg = geom.difference(wu) if wu is not None else geom
        mat = {"zwir_grabiony": "zwir_grabiony", "plyty": "plyty_ogrod", "trawa_niska": "trawa_ogrod", "mech_runo": "mech",
               "zwir_jasny": "zwir_ogrod", "plyty_jadalnia": "podloga_kamien", "deska_ogrod": "deck"}.get(kind, "zwir_ogrod")
        if kind == "deska_ogrod":                          # pomost 15 cm nad mchem (w poziomie podłogi domu)
            M.extrude(gg, z - 0.1, z + 0.15, mat, bottom=False)
            continue
        M.extrude(gg, z - 0.1, z, mat, bottom=False)
    if wu is not None:
        M.extrude(wu, z - 0.45, z - 0.12, "woda", bottom=False)
        M.extrude(wu.buffer(0.12).difference(wu), z - 0.12, z + 0.03, "kamien_ogrod", bottom=False)
    for ft in lay["features"]:
        t = ft.t
        x, y = ft.x, ft.y
        sd = int(x * 100 + y * 10)
        if not rosliny and t in ROSLINY:
            continue
        if t == "mech":
            M.sphere(x, y, z - 0.05, ft.r, "mech", sx=1.0, sy=0.78, sz=0.18, seed=sd, jitter=0.1)
        elif t == "kamien":
            M.sphere(x, y, z + ft.r * 0.15, ft.r, "kamien_ogrod", sx=1.0, sy=0.75, sz=0.55, seed=sd, jitter=0.18)
        elif t == "krok":
            M.cyl(x, y, z - 0.02, ft.r * 0.85, 0.06, "kamien_ogrod" if ft.kw.get("cls") != "plyta" else "plyty_ogrod", n=10)
        elif t in ("klon", "brzoza", "oliwka", "sosna", "palma"):
            # drzewo nie może przebić szklanego dachu ogrodu
            hmax = g.roof_z - z - 0.45
            _tree3d(M, t, x, y, z, max(1.6, min(ft.kw.get("h", 3.5), hmax)), max(0.6, min(ft.r, hmax * 0.4)), seed=sd)
        elif t == "cytrus":
            if ft.kw.get("grunt"):                         # drzewko posadzone w gruncie, bez donicy
                M.cyl(x, y, z, 0.05, 1.2, "pien", n=6)
                M.sphere(x, y, z + 1.85, 0.75, "lisc_cytrus", sz=0.85, seed=sd, jitter=0.15)
            else:
                M.cyl(x, y, z, 0.38, 0.55, "donica", n=14)
                M.cyl(x, y, z + 0.55, 0.04, 0.7, "pien", n=6)
                M.sphere(x, y, z + 1.6, 0.6, "lisc_cytrus", sz=0.85, seed=sd, jitter=0.15)
        elif t == "jacuzzi" and ft.kw.get("rect"):
            # jacuzzi prostokątne w turkusowej mozaice, obramowanie z trawertynu w poziomie pomostu, lustro wody 7 cm niżej
            pj = ft.kw["poly"]
            M.extrude(pj.buffer(0.15, join_style="mitre").difference(pj), z - 0.1, z + 0.15, "trawertyn")
            M.extrude(pj.difference(pj.buffer(-0.06, join_style="mitre")), z - 0.85, z + 0.15, "mozaika")
            M.extrude(pj, z - 0.9, z - 0.85, "mozaika")
            inner_ = pj.buffer(-0.06, join_style="mitre")
            M.extrude(Polygon([(c[0], c[1]) for c in inner_.exterior.coords]).difference(inner_.buffer(-0.45, join_style="mitre")),
                      z - 0.85, z - 0.45, "mozaika")                         # ławka-siedzisko dookoła
            M.extrude(inner_, z + 0.04, z + 0.08, "woda_basen", bottom=False)
        elif t == "zielona_sciana":
            k = ft.kw
            M.seg_box(k["a"], k["b"], 0.1, z, z + k["h"], "zielona_sciana")
            if rosliny:
                ln = LineString([k["a"], k["b"]])
                nrow = max(2, int(ln.length / 0.45))
                for i in range(nrow):
                    q = ln.interpolate((i + 0.5) / nrow, normalized=True)
                    for hz in (0.5, 1.1, 1.7, 2.3):
                        M.sphere(q.x + k["nx"] * 0.14, q.y + k["ny"] * 0.14, z + hz, 0.26, "lisc_zielony",
                                 sx=1.0, sy=0.6, sz=0.85, seed=sd + i * 7 + int(hz * 10), jitter=0.25)
        elif t == "led":
            for ln in ([ft.kw["geom"]] if ft.kw["geom"].geom_type == "LineString" else list(getattr(ft.kw["geom"], "geoms", []))):
                if ln.length > 0.3:
                    M.extrude(ln.buffer(0.012, cap_style="flat"), z + 0.07, z + 0.1, "lampa")
        elif t == "jacuzzi":
            # misa wpuszczona w grunt: kamienna obudowa 0,3 m nad runem, lustro wody tuż pod krawędzią
            rj = ft.kw.get("rj", 1.0)
            ring = Point(x, y).buffer(ft.r, 16).difference(Point(x, y).buffer(rj, 16))
            M.extrude(ring, z - 0.05, z + 0.3, "kamien_ogrod")
            M.cyl(x, y, z - 0.6, rj, 0.82, "woda", n=32)
            M.cyl(x, y, z - 0.6, rj * 0.55, 0.42, "kamien_ogrod", n=20)     # siedzisko w środku (widać pod wodą)
        elif t == "wodospad" and ft.kw.get("basin") is None:
            # wg zdjęcia: okładzina z ciemnego łupka, półka-wylewka z taśmą LED, tafla wody spada prosto do jacuzzi
            k = ft.kw
            w, h, hl = k["w"], k["h"], k["hl"]
            ux, uy, nx, ny = k["ux"], k["uy"], k["nx"], k["ny"]
            cx, cy = x - nx * 0.08, y - ny * 0.08                              # lico ściany
            rot = math.degrees(math.atan2(uy, ux))
            M.box(cx + nx * 0.07, cy + ny * 0.07, z - 0.85, w + 0.3, 0.14, h + 0.85, rot, "lupek")
            M.box(cx + nx * 0.29, cy + ny * 0.29, z + hl, w, 0.32, 0.1, rot, "lupek")
            M.box(cx + nx * 0.29, cy + ny * 0.29, z + hl - 0.025, w - 0.1, 0.3, 0.025, rot, "lampa")
            M.box(cx + nx * 0.44, cy + ny * 0.44, z + 0.04, w - 0.12, 0.025, hl - 0.04, rot, "wodospad")
        elif t == "wodospad":
            # wodospad na pełnej ścianie: kamienna okładzina, półka-wylewka, tafla spływającej wody i niecka u dołu
            k = ft.kw
            w, d, h = k["w"], k["d"], k["h"]
            ux, uy, nx, ny = k["ux"], k["uy"], k["nx"], k["ny"]
            cx, cy = x - nx * (d / 2), y - ny * (d / 2)                     # lico ściany (0,2 m od osi)
            rot = math.degrees(math.atan2(uy, ux))
            M.box(cx + nx * 0.07, cy + ny * 0.07, z, w + 0.8, 0.14, h + 0.12, rot, "kamien_ogrod")
            M.box(cx + nx * 0.27, cy + ny * 0.27, z + h - 0.12, w, 0.4, 0.12, rot, "kamien_ogrod")
            M.box(cx + nx * 0.42, cy + ny * 0.42, z - 0.1, w - 0.1, 0.03, h - 0.02, rot, "wodospad")
            b = k.get("basin")
            if b is not None:
                M.extrude(b, z - 0.4, z - 0.06, "woda", bottom=False)
                M.extrude(b.buffer(0.14, join_style="mitre").difference(b), z - 0.06, z + 0.22, "kamien_ogrod")
        elif t == "latarnia":
            M.box(x, y, z, 0.4, 0.4, 0.15, 0, "kamien_ogrod")
            M.cyl(x, y, z + 0.15, 0.1, 0.55, "kamien_ogrod", n=8)
            M.box(x, y, z + 0.7, 0.36, 0.36, 0.3, 0, "kamien_ogrod")
            M.cone(x, y, z + 1.0, 0.35, 0.22, "kamien_ogrod", n=4)
        elif t == "misa":
            M.cyl(x, y, z, ft.r, 0.32, "kamien_ogrod", n=12)
            M.cyl(x, y, z + 0.32, ft.r * 0.6, 0.005, "woda", n=12)
        elif t == "fontanna":
            M.extrude(Point(x, y).buffer(ft.r).difference(Point(x, y).buffer(ft.r - 0.15)), z, z + 0.4, "kamien_ogrod")
            M.cyl(x, y, z, ft.r - 0.15, 0.3, "woda", n=20)
            M.cyl(x, y, z, 0.12, 0.9, "kamien_ogrod", n=8)
        elif t == "lawka":
            M.box(x, y, z, ft.r * 2, 0.45, 0.45, ft.rot, "drewno_mebel")
        elif t == "lilia":
            M.cyl(x, y, z - 0.11, ft.r, 0.01, "lisc_zielony", n=8)
        elif t in ("paproc", "lawenda", "monstera", "donica"):
            mat = {"paproc": "lisc_zielony", "lawenda": "lawenda", "monstera": "lisc_palma", "donica": "donica"}[t]
            if t == "donica":
                M.cyl(x, y, z, ft.r, 0.5, "donica", n=12)
                M.sphere(x, y, z + 0.75, ft.r * 0.9, "lisc_zielony", seed=sd, jitter=0.15)
            else:
                M.sphere(x, y, z + ft.r * 0.4, ft.r, mat, sz=0.6, seed=sd, jitter=0.2)


def _limb(M, p, q, r0, r1, mat, n=6, var="base"):
    """Zwężający się pręt (pień, konar) między dwoma punktami 3D."""
    d = (q[0] - p[0], q[1] - p[1], q[2] - p[2])
    L = math.sqrt(sum(c * c for c in d))
    if L < 1e-6:
        return
    ax = tuple(c / L for c in d)
    ref = (0.0, 0.0, 1.0) if abs(ax[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = (ax[1] * ref[2] - ax[2] * ref[1], ax[2] * ref[0] - ax[0] * ref[2], ax[0] * ref[1] - ax[1] * ref[0])
    lu = math.sqrt(sum(c * c for c in u))
    u = tuple(c / lu for c in u)
    v = (ax[1] * u[2] - ax[2] * u[1], ax[2] * u[0] - ax[0] * u[2], ax[0] * u[1] - ax[1] * u[0])
    rings = []
    for c, r in ((p, r0), (q, r1)):
        rings.append([tuple(c[k] + r * (math.cos(2 * math.pi * i / n) * u[k] + math.sin(2 * math.pi * i / n) * v[k])
                            for k in range(3)) for i in range(n)])
    for i in range(n):
        j = (i + 1) % n
        M.quad(rings[0][i], rings[0][j], rings[1][j], rings[1][i], mat, var)


# kształt korony: (spłaszczenie kul, liczba kul, rozrzut poziomy, rozrzut pionowy)
CROWN = {"klon": (0.5, 10, 0.62, 0.55), "brzoza": (1.2, 8, 0.42, 0.9), "lipa": (0.85, 11, 0.5, 0.6),
         "oliwka": (0.65, 9, 0.6, 0.5)}


def _tree3d(M, kind, x, y, z, h, r, seed=0):
    rnd = random.Random(seed)
    if kind == "sosna":
        _limb(M, (x, y, z), (x, y, z + h * 0.85), 0.07 + h * 0.01, 0.04, "pien", n=6)
        for i in range(5):
            zz = z + h * (0.32 + i * 0.13)
            for k in range(3):
                a = rnd.uniform(0, 2 * math.pi)
                d = r * (0.9 - i * 0.15) * rnd.uniform(0.15, 0.45)
                M.sphere(x + math.cos(a) * d, y + math.sin(a) * d, zz, r * (0.85 - i * 0.12) * rnd.uniform(0.55, 0.75),
                         "lisc_sosna", sz=0.32, seed=seed + i * 7 + k, jitter=0.22, sub=2)
        return
    if kind == "palma":
        _limb(M, (x, y, z), (x + 0.3, y, z + h), 0.16, 0.1, "pien", n=8)
        for i in range(8):
            a = 2 * math.pi * i / 8 + rnd.uniform(-0.2, 0.2)
            M.sphere(x + 0.3 + math.cos(a) * r * 0.6, y + math.sin(a) * r * 0.6, z + h - 0.25, r * 0.55, "lisc_palma",
                     sx=1.0, sy=0.35, sz=0.12, seed=seed + i)
        return
    trunk = "pien_brzoza" if kind == "brzoza" else "pien"
    mat = {"klon": "lisc_klon", "brzoza": "lisc_brzoza", "oliwka": "lisc_oliwka", "lipa": "lisc_zielony"}.get(kind, "lisc_zielony")
    flat, nblob, spread, vert = CROWN.get(kind, (0.8, 9, 0.5, 0.6))
    zc = z + h - r * (0.75 if kind != "brzoza" else 1.15)
    rb = 0.05 + h * 0.011
    top = (x + rnd.uniform(-0.12, 0.12) * r, y + rnd.uniform(-0.12, 0.12) * r, zc)
    _limb(M, (x, y, z), top, rb, rb * 0.5, trunk, n=7)
    centers = []
    nb = 2 if kind == "brzoza" else 3
    for i in range(nb):
        a = 2 * math.pi * i / nb + rnd.uniform(-0.5, 0.5)
        reach = r * rnd.uniform(0.4, 0.6)
        zb = z + (zc - z) * rnd.uniform(0.55, 0.75)
        end = (x + math.cos(a) * reach, y + math.sin(a) * reach, zc + rnd.uniform(-0.05, 0.25) * r * flat)
        _limb(M, (x + (top[0] - x) * 0.6, y + (top[1] - y) * 0.6, zb), end, rb * 0.45, rb * 0.2, trunk, n=5)
        centers.append(end)
    while len(centers) < nblob:
        a = rnd.uniform(0, 2 * math.pi)
        d = r * spread * math.sqrt(rnd.uniform(0.0, 1.0))
        centers.append((x + math.cos(a) * d, y + math.sin(a) * d, zc + rnd.uniform(-0.45, 0.55) * r * vert))
    for i, (cx, cy, cz) in enumerate(centers):
        M.sphere(cx, cy, cz, r * rnd.uniform(0.36, 0.52), mat, sz=flat, seed=seed + i, jitter=0.22, sub=2)


def _people(M, house):
    pts = []
    for g in [r for r in house.all_rooms if r.kind == "ogrod"]:
        lay = getattr(g, "_layout", None)
        if lay and lay["paths"]:
            # nie stawiamy postaci w wodzie ani w drzewie
            block = [geom.buffer(0.35) for kind, geom in lay["floor"] if kind == "woda"]
            block += [Point(f.x, f.y).buffer(f.r + 0.25) for f in lay["features"] if f.t not in ("krok", "lilia", "mech")]
            bu = unary_union(block) if block else Polygon()
            for fr in (0.45, 0.35, 0.55, 0.25, 0.65, 0.15, 0.8):
                p = lay["paths"][0].interpolate(fr, normalized=True)
                if bu.is_empty or not bu.contains(p):
                    pts.append((p.x, p.y, g.z0 - 0.12))
                    break
    for r in house.all_rooms:
        if r.outdoor and r.parent is None and r.level == house.ground:
            p = r.poly.representative_point()
            pts.append((p.x + 0.6, p.y + 0.4, r.z0))
            break
    for x, y, z in pts[:2]:
        M.cyl(x, y, z, 0.14, 0.82, "czlowiek", n=8)
        M.cyl(x, y, z + 0.82, 0.19, 0.66, "czlowiek_gora", n=10)
        M.sphere(x, y, z + 1.62, 0.12, "czlowiek", seed=1)


# --------------------------------------------------------------- dach szklany
def _ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def _slat(M, p1, p2, zc, w, th, ang, mat, var="base"):
    """Lamela obrócona o kąt ang (stopnie) wokół osi p1–p2 na wysokości zc."""
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return
    nx, ny = -dy / L, dx / L
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    sec = []
    for u, v in ((-w / 2, -th / 2), (w / 2, -th / 2), (w / 2, th / 2), (-w / 2, th / 2)):
        uu, vv = u * ca - v * sa, u * sa + v * ca
        sec.append((nx * uu, ny * uu, vv))
    A = [(p1[0] + q[0], p1[1] + q[1], zc + q[2]) for q in sec]
    B = [(p2[0] + q[0], p2[1] + q[1], zc + q[2]) for q in sec]
    for i in range(4):
        j = (i + 1) % 4
        M.quad(A[i], A[j], B[j], B[i], mat, var)
    M.quad(A[3], A[2], A[1], A[0], mat, var)
    M.quad(B[0], B[1], B[2], B[3], mat, var)


def _glass_roof3d(M, house, g, stan=None):
    """stan=None: warianty zima (zamknięty) i lato (otwarty); stan∈[0,1]: ruchome części w stanie pośrednim (wariant "ruch")."""
    poly = g.poly
    z = g.roof_z
    t = g.roof_type
    from .meble import frame
    cx, cy, ang, L, W = frame(poly)
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    # obwodowa rama nośna (wieniec)
    ring = poly.buffer(0.15, join_style="mitre").difference(poly.buffer(-0.12, join_style="mitre"))
    M.extrude(ring, z - 0.45, z, "rama")
    if t in ("slide", "fold", "vault", "ridge", "louvre"):
        n = max(2, int(round(L / 1.25)))
        step = L / n
        bars = []
        for i in range(1, n):
            u = -L / 2 + i * step
            p1 = (cx + ux * u - vx * W, cy + uy * u - vy * W)
            p2 = (cx + ux * u + vx * W, cy + uy * u + vy * W)
            seg = LineString([p1, p2]).intersection(poly)
            for s_ in _segs(seg):
                bars.append(s_)
        for s_ in bars:
            cs = list(s_.coords)
            M.seg_box(cs[0], cs[-1], 0.08, z - 0.3, z, "rama")
        if t == "louvre":
            nl = max(4, int(W / 0.32))
            for i in range(nl):
                v = -W / 2 + (i + 0.5) * W / nl
                p1 = (cx + vx * v - ux * L, cy + vy * v - uy * L)
                p2 = (cx + vx * v + ux * L, cy + vy * v + uy * L)
                seg = LineString([p1, p2]).intersection(poly)
                for s_ in _segs(seg):
                    cs = list(s_.coords)
                    if stan is not None:
                        _slat(M, cs[0], cs[-1], z - 0.015, W / nl * 0.98, 0.03, 82 * _ease(stan), "szklo", var="ruch")
                        continue
                    # lato – lamele uchylone (wąskie w rzucie), zima – zamknięte
                    M.seg_box(cs[0], cs[-1], 0.06, z - 0.05, z + 0.22, "szklo", var="lato")
                    M.seg_box(cs[0], cs[-1], W / nl, z - 0.03, z, "szklo", var="zima")
            return
        # połowa stała
        half_fixed = Polygon([(cx + ux * 0 - vx * W, cy + uy * 0 - vy * W), (cx + ux * L - vx * W, cy + uy * L - vy * W),
                              (cx + ux * L + vx * W, cy + uy * L + vy * W), (cx + ux * 0 + vx * W, cy + uy * 0 + vy * W)]).intersection(poly)
        half_move = poly.difference(half_fixed)
        rise = 0.0
        if t == "ridge":
            rise = W * 0.18
        M.extrude(half_fixed, z - 0.02, z, "szklo")
        from shapely import affinity
        if stan is not None:
            # najpierw uniesienie o 16 cm, potem przesuw nad połowę stałą
            lift = 0.16 * _ease(stan / 0.15)
            dist = L / 2 * _ease((stan - 0.15) / 0.85)
            mv = affinity.translate(half_move, ux * dist, uy * dist)
            if dist > L / 2 - 0.05:
                mv = mv.intersection(half_fixed.buffer(0.01))
            M.extrude(mv, z - 0.02 + lift, z + lift, "szklo", var="ruch")
            M.extrude(mv.boundary.buffer(0.04).intersection(mv.buffer(0.05)), z - 0.06 + lift, z + 0.02 + lift, "rama", var="ruch")
            return
        M.extrude(half_move, z - 0.02, z, "szklo", var="zima")
        # lato: ruchoma połowa wsunięta nad stałą
        moved = affinity.translate(half_move, ux * L / 2, uy * L / 2).intersection(half_fixed.buffer(0.01))
        M.extrude(moved, z + 0.14, z + 0.16, "szklo", var="lato")
        M.extrude(moved.boundary.buffer(0.04).intersection(moved.buffer(0.05)), z + 0.1, z + 0.18, "rama", var="lato")
        return
    if t in ("pyramid", "iris"):
        c = poly.centroid
        rr = math.sqrt(poly.area / math.pi)
        top = z + (rr * 0.55 if t == "pyramid" else rr * 0.18)
        cs = list(poly.exterior.coords)[:-1]
        ring_open = 0.33
        for (x1, y1), (x2, y2) in zip(cs, cs[1:] + cs[:1]):
            # do pierścienia otworu
            i1 = (c.x + (x1 - c.x) * ring_open, c.y + (y1 - c.y) * ring_open)
            i2 = (c.x + (x2 - c.x) * ring_open, c.y + (y2 - c.y) * ring_open)
            zt = z + (top - z) * (1 - ring_open)
            M.quad((x1, y1, z), (x2, y2, z), (i2[0], i2[1], zt), (i1[0], i1[1], zt), "szklo")
        # rama promienista
        for (x1, y1) in cs[::max(1, len(cs) // 12)]:
            i1 = (c.x + (x1 - c.x) * ring_open, c.y + (y1 - c.y) * ring_open)
            zt = z + (top - z) * (1 - ring_open)
            _bar3d(M, (x1, y1, z + 0.02), (i1[0], i1[1], zt + 0.02), 0.06, "rama")
        # latarnia / otwór
        zt = z + (top - z) * (1 - ring_open)
        inner = [(c.x + (x - c.x) * ring_open, c.y + (y - c.y) * ring_open) for x, y in cs]
        ip = Polygon(inner)
        M.extrude(ip.buffer(0.06).difference(ip.buffer(-0.06)), zt, zt + 0.08, "rama")
        if stan is not None:
            lift = 0.68 * _ease(stan)
            M.extrude(ip.buffer(0.1), zt + 0.02 + lift, zt + 0.06 + lift, "szklo", var="ruch")
            if lift > 0.02:
                for x, y in inner[::max(1, len(inner) // 4)]:
                    M.box(x, y, zt, 0.06, 0.06, lift + 0.04, 0, "rama", var="ruch")
            return
        # zima – zamknięty kapelusz; lato – uniesiony
        M.extrude(ip.buffer(0.1), zt + 0.02, zt + 0.06, "szklo", var="zima")
        M.extrude(ip.buffer(0.1), zt + 0.7, zt + 0.74, "szklo", var="lato")
        for x, y in inner[::max(1, len(inner) // 4)]:
            M.box(x, y, zt, 0.06, 0.06, 0.72, 0, "rama", var="lato")
        return


def _bar3d(M, p, q, t, mat, var="base"):
    """Pręt między dwoma punktami 3D (przybliżenie płytką)."""
    (x1, y1, z1), (x2, y2, z2) = p, q
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return
    nx, ny = -dy / L * t / 2, dx / L * t / 2
    a1 = (x1 + nx, y1 + ny, z1)
    a2 = (x1 - nx, y1 - ny, z1)
    b1 = (x2 + nx, y2 + ny, z2)
    b2 = (x2 - nx, y2 - ny, z2)
    M.quad(a1, a2, b2, b1, mat, var)
    M.quad((a1[0], a1[1], a1[2] - t), (a2[0], a2[1], a2[2] - t), (b2[0], b2[1], b2[2] - t), (b1[0], b1[1], b1[2] - t), mat, var)


def _segs(g):
    if g.is_empty:
        return []
    if g.geom_type == "LineString":
        return [g]
    out = []
    for x in getattr(g, "geoms", []):
        out.extend(_segs(x))
    return out


# ------------------------------------------------------------------- eksport
def export_json(M, house):
    """JSON dla przeglądarki: wierzchołki indeksowane per (wariant, materiał), cm, base64."""
    import base64
    import struct
    minx, miny, maxx, maxy = house.bbox
    ox, oy = (minx + maxx) / 2, (miny + maxy) / 2
    out = {"center": [0, 0], "size": [maxx - minx, maxy - miny], "groups": []}
    for (var, mat), tris in M.g.items():
        idx = {}
        verts = []
        ind = []
        for tri in tris:
            for (x, y, z) in tri:
                key = (int(round((x - ox) * 100)), int(round(z * 100)), int(round((y - oy) * 100)))
                k = idx.get(key)
                if k is None:
                    k = len(verts)
                    idx[key] = k
                    verts.append(key)
                ind.append(k)
        vb = struct.pack(f"<{len(verts) * 3}h", *[c for v in verts for c in v])
        fmt = "H" if len(verts) < 65536 else "I"
        ib = struct.pack(f"<{len(ind)}{fmt}", *ind)
        out["groups"].append({"var": var, "mat": mat, "v": base64.b64encode(vb).decode(), "i": base64.b64encode(ib).decode(),
                              "i32": fmt == "I", "n": len(ind) // 3})
    return out
