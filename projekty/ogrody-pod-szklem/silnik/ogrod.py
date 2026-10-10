"""Ogród wewnętrzny: układ elementów wg stylu, rysunek 2D i elementy 3D."""
import math
import random

from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union, polylabel

from .geom import largest, polygons

STYLES = ("japonski", "oranzeria", "woda", "las", "srodziemnomorski", "tropikalny")


class Feature:
    def __init__(self, t, x, y, r=0.3, rot=0.0, **kw):
        self.t, self.x, self.y, self.r, self.rot = t, x, y, r, rot
        self.kw = kw


def garden_layout(g, level, house):
    """Zwraca dict: floor (wielokąty nawierzchni), paths, features."""
    net = g.net if g.net is not None else g.poly
    inner = net.buffer(-0.15)
    if inner.is_empty:
        inner = net
    rnd = random.Random(g.seed * 7919 + len(house.pid))
    # drzwi do ogrodu
    doors = []
    for o in level["openings"]:
        if o.kind in ("slide", "door", "double", "wide", "portal", "pivot", "arch"):
            ln = LineString([o.a, o.b])
            if ln.distance(net) < 0.4:
                m = ln.interpolate(0.5, normalized=True)
                # punkt 0,7 m w głąb ogrodu
                c = net.centroid
                v = (c.x - m.x, c.y - m.y)
                L = math.hypot(*v) or 1
                p = Point(m.x + v[0] / L * 0.7, m.y + v[1] / L * 0.7)
                if net.contains(p):
                    doors.append(p)
    try:
        hub = polylabel(inner, 0.05)
    except Exception:
        hub = inner.representative_point()
    paths = []
    for d in doors:
        paths.append(LineString([(d.x, d.y), (hub.x, hub.y)]))
    path_zone = unary_union([p.buffer(0.45) for p in paths]) if paths else Polygon()
    feats = []
    floor = []
    st = g.style
    area = net.area
    R = math.sqrt(area / math.pi)

    def spot(rad, tries=60, avoid=None, near=None, spread=1.0):
        zone = inner.buffer(-rad - 0.1)
        if zone.is_empty:
            return None
        minx, miny, maxx, maxy = zone.bounds
        best = None
        for _ in range(tries):
            if near is not None:
                x = near.x + rnd.uniform(-1, 1) * R * 0.5 * spread
                y = near.y + rnd.uniform(-1, 1) * R * 0.5 * spread
            else:
                x, y = rnd.uniform(minx, maxx), rnd.uniform(miny, maxy)
            p = Point(x, y)
            if not zone.contains(p):
                continue
            if p.distance(path_zone) < rad + 0.1 if not path_zone.is_empty else False:
                continue
            clash = False
            for f in feats:
                if math.hypot(f.x - x, f.y - y) < f.r + rad + 0.25:
                    clash = True
                    break
            if clash:
                continue
            if avoid is not None and p.distance(avoid) < rad:
                continue
            return (x, y)
        return best

    def steps_along(line, cls="kamien"):
        n = max(1, int(line.length / 0.62))
        for i in range(n):
            p = line.interpolate((i + 0.5) / n, normalized=True)
            feats.append(Feature("krok", p.x, p.y, 0.24, rot=rnd.uniform(0, 180), cls=cls))

    if st == "japonski":
        floor.append(("zwir_grabiony", net))
        main = spot(min(1.1, R * 0.35), near=hub, spread=0.8) or (hub.x, hub.y)
        feats.append(Feature("mech", main[0], main[1], min(1.4, R * 0.42)))
        feats.append(Feature("klon", main[0] + 0.2, main[1] - 0.1, min(1.1, R * 0.33), h=3.6))
        for rr in (0.38, 0.3, 0.24):
            p = spot(rr + 0.5)
            if p:
                feats.append(Feature("kamien", p[0], p[1], rr, rot=rnd.uniform(0, 180)))
        p = spot(0.5)
        if p:
            feats.append(Feature("latarnia", p[0], p[1], 0.22))
        p = spot(0.4)
        if p:
            feats.append(Feature("misa", p[0], p[1], 0.3))
        p = spot(0.6)
        if p and area > 30:
            feats.append(Feature("sosna", p[0], p[1], 0.6, h=2.4))
        for ln in paths:
            steps_along(ln)
    elif st == "oranzeria":
        floor.append(("plyty", net))
        feats.append(Feature("fontanna", hub.x, hub.y, min(1.0, R * 0.3)))
        n = 4 if area < 50 else 6
        for i in range(n):
            a = 2 * math.pi * i / n + 0.4
            x = hub.x + math.cos(a) * R * 0.62
            y = hub.y + math.sin(a) * R * 0.62
            if inner.buffer(-0.5).contains(Point(x, y)) and Point(x, y).distance(path_zone) > 0.3:
                feats.append(Feature("cytrus", x, y, 0.45, h=2.2))
        p = spot(0.6)
        if p:
            feats.append(Feature("oliwka", p[0], p[1], 0.7, h=3.2))
        p = spot(0.9)
        if p:
            feats.append(Feature("lawka", p[0], p[1], 0.9, rot=rnd.uniform(0, 180)))
    elif st == "woda":
        floor.append(("trawa_niska", net))
        pool = inner.buffer(-max(0.9, R * 0.28))
        pool = largest(pool) if not pool.is_empty else None
        if pool is not None and pool.area > 2:
            pool = pool.simplify(0.05)
            floor.append(("woda", pool))
            # kładka z kamieni przez wodę
            if doors:
                ln = LineString([(doors[0].x, doors[0].y), (hub.x, hub.y)])
                steps_along(ln, cls="plyta")
        for i in range(3):
            p = spot(0.6)
            if p and (pool is None or not pool.buffer(0.3).contains(Point(p))):
                feats.append(Feature("brzoza", p[0], p[1], 0.55, h=5.0))
        for i in range(4):
            if pool is not None:
                q = pool.representative_point()
                x = q.x + rnd.uniform(-1, 1) * R * 0.3
                y = q.y + rnd.uniform(-1, 1) * R * 0.3
                if pool.buffer(-0.3).contains(Point(x, y)):
                    feats.append(Feature("lilia", x, y, 0.22))
    elif st == "las":
        floor.append(("mech_runo", net))
        for i in range(5):
            p = spot(0.5)
            if p:
                feats.append(Feature("brzoza", p[0], p[1], 0.5, h=5.5 + rnd.uniform(-1, 1)))
        for i in range(6):
            p = spot(0.35)
            if p:
                feats.append(Feature("paproc", p[0], p[1], 0.35))
        for ln in paths:
            steps_along(ln, cls="plyta")
    elif st == "srodziemnomorski":
        floor.append(("zwir_jasny", net))
        feats.append(Feature("oliwka", hub.x, hub.y, min(1.2, R * 0.35), h=3.6))
        for i in range(8):
            p = spot(0.3)
            if p:
                feats.append(Feature("lawenda", p[0], p[1], 0.3))
        for i in range(3):
            p = spot(0.4)
            if p:
                feats.append(Feature("donica", p[0], p[1], 0.35))
        for ln in paths:
            steps_along(ln, cls="plyta")
    else:  # tropikalny
        floor.append(("plyty", net))
        pool = inner.buffer(-max(1.0, R * 0.45))
        pool = largest(pool) if not pool.is_empty else None
        if pool is not None and pool.area > 2:
            floor.append(("woda", pool.simplify(0.05)))
        for i in range(4):
            p = spot(0.8)
            if p and (pool is None or pool.distance(Point(p)) > 0.4):
                feats.append(Feature("palma", p[0], p[1], 0.9, h=4.5 + rnd.uniform(-0.6, 0.8)))
        for i in range(4):
            p = spot(0.45)
            if p:
                feats.append(Feature("monstera", p[0], p[1], 0.45))
    if g.trees:
        for t in g.trees:
            feats.append(Feature(t[0], t[1], t[2], t[3] if len(t) > 3 else 0.8, h=t[4] if len(t) > 4 else 4.0))
    return dict(floor=floor, paths=paths, features=feats, net=net)


# ------------------------------------------------------------------- rysunek 2D
def svg_garden(lay, P, f):
    """P(x, y) → px; f – formatowanie liczb. Zwraca listę elementów SVG."""
    out = []
    s = P.s

    def poly(geom, cls):
        for p in polygons(geom):
            d = "M" + " L".join(f"{f(a)},{f(b)}" for a, b in (P(*c) for c in p.exterior.coords)) + " Z"
            for h in p.interiors:
                d += " M" + " L".join(f"{f(a)},{f(b)}" for a, b in (P(*c) for c in h.coords)) + " Z"
            out.append(f'<path d="{d}" class="{cls}" fill-rule="evenodd"/>')

    for kind, geom in lay["floor"]:
        poly(geom, f"g-{kind}")
    for ft in lay["features"]:
        x, y = P(ft.x, ft.y)
        r = ft.r * s
        t = ft.t
        if t == "mech":
            out.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r)}" ry="{f(r * 0.78)}" class="g-mech"/>')
        elif t == "kamien":
            for k in (2, 1):
                out.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r + 0.17 * s * k)}" ry="{f(r * 0.75 + 0.17 * s * k)}" class="g-krag" transform="rotate({ft.rot:.0f} {f(x)} {f(y)})"/>')
            out.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r)}" ry="{f(r * 0.75)}" class="g-kamien" transform="rotate({ft.rot:.0f} {f(x)} {f(y)})"/>')
        elif t == "krok":
            cls = "g-plyta" if ft.kw.get("cls") == "plyta" else "g-krok"
            if cls == "g-plyta":
                out.append(f'<rect x="{f(x - r)}" y="{f(y - r * 0.6)}" width="{f(2 * r)}" height="{f(1.2 * r)}" rx="2" class="{cls}" transform="rotate({ft.rot:.0f} {f(x)} {f(y)})"/>')
            else:
                out.append(f'<ellipse cx="{f(x)}" cy="{f(y)}" rx="{f(r)}" ry="{f(r * 0.72)}" class="{cls}" transform="rotate({ft.rot:.0f} {f(x)} {f(y)})"/>')
        elif t in ("klon", "brzoza", "oliwka", "sosna", "palma", "cytrus"):
            out.append(_tree_svg(t, x, y, r, f))
        elif t == "latarnia":
            out.append(f'<rect x="{f(x - r)}" y="{f(y - r)}" width="{f(2 * r)}" height="{f(2 * r)}" class="g-latarnia"/>'
                       f'<path d="M{f(x - r)},{f(y - r)} L{f(x + r)},{f(y + r)} M{f(x + r)},{f(y - r)} L{f(x - r)},{f(y + r)}" class="g-linia"/>')
        elif t == "misa":
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" class="g-kamien"/><circle cx="{f(x)}" cy="{f(y)}" r="{f(r * 0.5)}" class="g-woda"/>')
        elif t == "fontanna":
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" class="g-obrzeze"/><circle cx="{f(x)}" cy="{f(y)}" r="{f(r - 0.15 * s)}" class="g-woda"/>'
                       f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(0.12 * s)}" class="g-obrzeze"/>')
        elif t == "lawka":
            out.append(f'<rect x="{f(x - r)}" y="{f(y - 0.22 * s)}" width="{f(2 * r)}" height="{f(0.44 * s)}" rx="2" class="g-lawka" transform="rotate({ft.rot:.0f} {f(x)} {f(y)})"/>')
        elif t == "lilia":
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" class="g-lilia"/>')
        elif t in ("paproc", "lawenda", "monstera", "donica"):
            cls = {"paproc": "g-paproc", "lawenda": "g-lawenda", "monstera": "g-monstera", "donica": "g-donica"}[t]
            n = 7
            pts = []
            for i in range(n * 2):
                a = math.pi * i / n
                rr = r if i % 2 == 0 else r * 0.55
                pts.append(f"{f(x + rr * math.cos(a))},{f(y + rr * math.sin(a))}")
            out.append(f'<polygon points="{" ".join(pts)}" class="{cls}"/>')
    return out


def _tree_svg(t, x, y, r, f):
    cls = {"klon": "g-klon", "brzoza": "g-brzoza", "oliwka": "g-oliwka", "sosna": "g-sosna", "palma": "g-palma", "cytrus": "g-cytrus", "drzewo": "g-drzewo"}[t]
    parts = [f'<circle cx="{f(x + r * 0.18)}" cy="{f(y + r * 0.22)}" r="{f(r)}" class="g-cien"/>']
    if t == "palma":
        for i in range(9):
            a = 2 * math.pi * i / 9
            parts.append(f'<path d="M{f(x)},{f(y)} Q{f(x + r * 0.6 * math.cos(a + 0.3))},{f(y + r * 0.6 * math.sin(a + 0.3))} {f(x + r * math.cos(a))},{f(y + r * math.sin(a))}" class="{cls}-l"/>')
    else:
        lobes = 7 if t != "sosna" else 11
        for i in range(lobes):
            a = 2 * math.pi * i / lobes
            parts.append(f'<circle cx="{f(x + r * 0.5 * math.cos(a))}" cy="{f(y + r * 0.5 * math.sin(a))}" r="{f(r * 0.52)}" class="{cls}"/>')
        parts.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r * 0.55)}" class="{cls}"/>')
        if t == "cytrus":
            for i in range(5):
                a = 1.0 + 2 * math.pi * i / 5
                parts.append(f'<circle cx="{f(x + r * 0.6 * math.cos(a))}" cy="{f(y + r * 0.6 * math.sin(a))}" r="{f(max(1.6, r * 0.1))}" class="g-owoc"/>')
    parts.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(max(1.2, r * 0.07))}" class="g-pien"/>')
    return "".join(parts)
