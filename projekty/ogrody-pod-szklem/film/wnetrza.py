"""Wykończenie ścian wnętrz: farba w kolorze pokoju, ściana akcentowa, płytki (do wysokości albo po sufit),
listwy przypodłogowe, panele akustyczne. Cienka „skóra” 4 mm przed licem ściany, z otworami okien i drzwi.

Opis w projekcie domu: H.sciany = {klucz_pokoju: dict(farba=…, plytki=…, do=…, akcent=(kierunek, materiał), panele=…)}.
Pokoje bez opisu dostają ciepłą biel (tylko gdy dom ma H.sciany).
"""
import math

import bpy
from shapely.geometry import Point

from .materialy import material

WALLS = ("ext", "int", "gwall")
DIRV = {"N": (0.0, -1.0), "S": (0.0, 1.0), "E": (1.0, 0.0), "W": (-1.0, 0.0)}   # plan: y rośnie na południe


def _mat_key(name):
    if name.startswith(("farba_", "plytki_", "panel_")):
        return name
    return "farba_" + name


def _sub(za, zb, cuts):
    """Przedział [za, zb] minus lista przedziałów."""
    out = [(za, zb)]
    for a, b in cuts:
        nxt = []
        for c, d in out:
            if b <= c or a >= d:
                nxt.append((c, d))
                continue
            if a > c:
                nxt.append((c, a))
            if b < d:
                nxt.append((b, d))
        out = nxt
    return [(c, d) for c, d in out if d - c > 0.004]


def _rects(s0, s1, za, zb, holes):
    """Prostokąty (s0, s1, z0, z1) pokrywające strefę bez otworów (otwory: (sa, sb, za, zb))."""
    hs = [h for h in holes if h[1] > s0 and h[0] < s1 and h[3] > za and h[2] < zb]
    xs = sorted({s0, s1} | {min(max(h[0], s0), s1) for h in hs} | {min(max(h[1], s0), s1) for h in hs})
    out = []
    prev = None
    for a, b in zip(xs, xs[1:]):
        if b - a < 1e-4:
            continue
        m = (a + b) / 2
        zs = tuple(_sub(za, zb, [(h[2], h[3]) for h in hs if h[0] < m < h[1]]))
        if prev is not None and prev[1] == zs and abs(prev[0][1] - a) < 1e-6:
            prev[0][1] = b
            continue
        prev = ([a, b], zs)
        out.append(prev)
    res = []
    for (a, b), zs in out:
        for c, d in zs:
            res.append((a, b, c, d))
    return res


class _Acc:
    """Zbiera czworokąty i bryłki według materiału."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.g = {}

    def quad(self, mat, pts):
        v, f = self.g.setdefault(mat, ([], []))
        k = len(v)
        v.extend(self.ctx.to_bl(*p) for p in pts)
        f.append((k, k + 1, k + 2, k + 3))

    def box(self, mat, p, u, n, s0, s1, off0, off1, z0, z1):
        """Prostopadłościan wzdłuż ściany: od s0 do s1 (wzdłuż u), od off0 do off1 (wzdłuż n), od z0 do z1."""
        def P(s, o, z):
            return (p[0] + u[0] * s + n[0] * o, p[1] + u[1] * s + n[1] * o, z)
        c = [P(s0, off0, z0), P(s1, off0, z0), P(s1, off1, z0), P(s0, off1, z0),
             P(s0, off0, z1), P(s1, off0, z1), P(s1, off1, z1), P(s0, off1, z1)]
        for q in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7)):
            self.quad(mat, [c[i] for i in q])

    def build(self, col, prefix):
        for mat, (v, f) in self.g.items():
            me = bpy.data.meshes.new(f"{prefix}_{mat}")
            me.from_pydata(v, [], f)
            me.update()
            ob = bpy.data.objects.new(f"{prefix}_{mat}", me)
            col.objects.link(ob)
            me.materials.append(material(mat, self.ctx))


def _edges(net):
    cs = list(net.exterior.coords)
    for a, b in zip(cs, cs[1:]):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L > 0.05:
            yield a, b, L


def wykonczenia(H, ctx, col):
    spec_all = getattr(H, "sciany", None)
    if not spec_all:
        return
    acc = _Acc(ctx)
    for idx, L in H.L.items():
        geoms = L.get("wall_geoms") or {}
        wall = None
        for c in WALLS:
            g = geoms.get(c)
            if g is not None:
                wall = g if wall is None else wall.union(g)
        if wall is None:
            continue
        for r in L["rooms"]:
            if r.parent is not None or r.outdoor or r.kind in ("ogrod", "ogrod_void", "void") or r.net is None:
                continue
            sp = spec_all.get(r.key, dict(farba="cieply_bialy"))
            z0, z1 = r.z0, r.top - 0.003
            net = r.net
            for a, b, Ln in _edges(net):
                u = ((b[0] - a[0]) / Ln, (b[1] - a[1]) / Ln)
                n = (-u[1], u[0])
                mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                if not net.buffer(1e-4).contains(Point(mid[0] + n[0] * 0.02, mid[1] + n[1] * 0.02)):
                    n = (-n[0], -n[1])             # n – do wnętrza pokoju
                out = (-n[0], -n[1])
                # odcinki z pełną ścianą za licem
                pres, cur = [], None
                k = max(2, int(Ln / 0.05))
                for i in range(k + 1):
                    s = Ln * i / k
                    q = Point(a[0] + u[0] * s + out[0] * 0.04, a[1] + u[1] * s + out[1] * 0.04)
                    on = wall.contains(q)
                    if on and cur is None:
                        cur = s
                    if not on and cur is not None:
                        pres.append((cur, s))
                        cur = None
                if cur is not None:
                    pres.append((cur, Ln))
                pres = [(s0, s1) for s0, s1 in pres if s1 - s0 > 0.08]
                if not pres:
                    continue
                # otwory w tej ścianie
                holes = []
                for o in L["openings"]:
                    if o.cls not in WALLS:
                        continue
                    pa = ((o.a[0] - a[0]) * u[0] + (o.a[1] - a[1]) * u[1])
                    pb = ((o.b[0] - a[0]) * u[0] + (o.b[1] - a[1]) * u[1])
                    da = abs((o.a[0] - a[0]) * n[0] + (o.a[1] - a[1]) * n[1])
                    if da > o.t / 2 + 0.1:
                        continue
                    sa, sb = min(pa, pb), max(pa, pb)
                    if sb < 0 or sa > Ln:
                        continue
                    holes.append((sa, sb, o.z_floor + o.sill, o.z_floor + o.head))
                # strefy materiałów
                ang = math.degrees(math.atan2(out[1], out[0]))
                akc = sp.get("akcent")
                is_acc = False
                if akc:
                    dv = DIRV[akc[0]]
                    is_acc = out[0] * dv[0] + out[1] * dv[1] > 0.9
                zones = []
                if is_acc:
                    zones.append((z0, z1, _mat_key(akc[1])))
                elif sp.get("plytki"):
                    zt = min(z1, z0 + sp["do"]) if sp.get("do") else z1
                    zones.append((z0, zt, sp["plytki"]))
                    if zt < z1:
                        zones.append((zt, z1, _mat_key(sp.get("farba", "cieply_bialy"))))
                else:
                    zones.append((z0, z1, _mat_key(sp.get("farba", "cieply_bialy"))))
                tiled = bool(sp.get("plytki")) or (is_acc and akc[1].startswith("plytki"))
                for s0, s1 in pres:
                    for za, zb, mat in zones:
                        for (ra, rb, rc, rd) in _rects(s0, s1, za, zb, holes):
                            P = [(a[0] + u[0] * s + n[0] * 0.004, a[1] + u[1] * s + n[1] * 0.004, z)
                                 for s, z in ((ra, rc), (rb, rc), (rb, rd), (ra, rd))]
                            acc.quad(mat, P)
                    # listwa przypodłogowa (bez płytek i poza drzwiami)
                    if not tiled:
                        doors = [(h[0], h[1], h[2], h[3]) for h in holes if h[2] - z0 < 0.05]
                        for (ra, rb, rc, rd) in _rects(s0, s1, z0, z0 + 0.08, doors):
                            acc.box("listwa", a, u, n, ra, rb, 0.004, 0.016, rc, rd)
                    # kino: panele akustyczne z listew na ścianach bocznych i tylnej
                    if sp.get("panele") and not is_acc and Ln > 1.0:
                        for (ra, rb, rc, rd) in _rects(s0 + 0.15, s1 - 0.15, z0 + 0.35, z0 + 2.35, holes):
                            acc.box("panel_akustyczny", a, u, n, ra, rb, 0.005, 0.04, rc, rd)
    acc.build(col, "sciana")
