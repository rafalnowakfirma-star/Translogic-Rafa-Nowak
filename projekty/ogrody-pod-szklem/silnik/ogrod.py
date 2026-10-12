"""Ogród wewnętrzny: układ elementów wg stylu, rysunek 2D i elementy 3D."""
import math
import random

from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union, polylabel

from .geom import largest, polygons

STYLES = ("japonski", "oranzeria", "woda", "las", "srodziemnomorski", "tropikalny", "jadalnia", "jacuzzi")


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
    elif st == "jadalnia":
        # ogród-jadalnia: kamienna posadzka w poziomie podłogi, stół przy ścianie od jadalni, rośliny w donicach dookoła
        floor.append(("plyty_jadalnia", net))
        stol = _miejsce_stolu(g, level, net, inner)
        if stol is not None:
            path_zone = path_zone.union(stol["strefa"])
            stol = {k: v for k, v in stol.items() if k != "strefa"}
        p = spot(0.75)
        if p:
            feats.append(Feature("oliwka" if area < 40 else "palma", p[0], p[1], 0.75, h=3.2))
        for i in range(3 if area < 35 else 4):
            p = spot(0.42)
            if p:
                feats.append(Feature("cytrus", p[0], p[1], 0.42, h=2.0))
        for kind_, rr in (("monstera", 0.45), ("donica", 0.35), ("paproc", 0.32), ("donica", 0.32)):
            p = spot(rr)
            if p:
                feats.append(Feature(kind_, p[0], p[1], rr))
        if g.trees:
            for t in g.trees:
                feats.append(Feature(t[0], t[1], t[2], t[3] if len(t) > 3 else 0.8, h=t[4] if len(t) > 4 else 4.0))
        return dict(floor=floor, paths=paths, features=feats, net=net, stol=stol)
    elif st == "jacuzzi":
        # prawdziwy ogród: runo z mchu, rabaty kwiatów, jedno drzewko owocowe, jacuzzi w kamiennej obudowie
        # i wodospad na pełnej ścianie zewnętrznej (woda spływa po kamieniu do niecki u stóp ściany)
        floor.append(("mech_runo", net))
        wall = _sciana_wodospadu(g, level)
        basin = None
        if wall is not None:
            (ax, ay), (bx, by), nx, ny = wall
            L = math.hypot(bx - ax, by - ay)
            w = min(2.6, L - 1.2)
            mx, my = (ax + bx) / 2, (ay + by) / 2
            ux, uy = (bx - ax) / L, (by - ay) / L
            rot = math.degrees(math.atan2(uy, ux))
            d = 0.72                                                        # głębokość niecki od lica ściany
            feats.append(Feature("wodospad", mx + nx * (0.2 + d / 2), my + ny * (0.2 + d / 2), w / 2, rot=rot,
                                 w=w, d=d, h=2.9, ux=ux, uy=uy, nx=nx, ny=ny))
            basin = Polygon([(mx - ux * w / 2 + nx * 0.2, my - uy * w / 2 + ny * 0.2),
                             (mx + ux * w / 2 + nx * 0.2, my + uy * w / 2 + ny * 0.2),
                             (mx + ux * w / 2 + nx * (0.2 + d), my + uy * w / 2 + ny * (0.2 + d)),
                             (mx - ux * w / 2 + nx * (0.2 + d), my - uy * w / 2 + ny * (0.2 + d))])
            feats[-1].kw["basin"] = basin
            path_zone = path_zone.union(basin.buffer(0.25))
            for sgn in (-1, 1):                                             # paprocie i kamienie po bokach niecki
                px, py = mx + ux * sgn * (w / 2 + 0.45) + nx * 0.95, my + uy * sgn * (w / 2 + 0.45) + ny * 0.95
                if inner.buffer(-0.3).contains(Point(px, py)):
                    feats.append(Feature("paproc", px, py, 0.38))
        # jacuzzi: z dala od niecki wodospadu i od przejść spod drzwi, raczej w głębi ogrodu
        rj = 1.0 if area > 28 else 0.85
        best = None
        zone = inner.buffer(-rj - 0.35)
        door_lines = unary_union(paths) if paths else None
        if not zone.is_empty:
            minx, miny, maxx, maxy = zone.bounds
            for i in range(16):
                for j in range(16):
                    p = Point(minx + (maxx - minx) * (i + 0.5) / 16, miny + (maxy - miny) * (j + 0.5) / 16)
                    if not zone.contains(p):
                        continue
                    db = basin.distance(p) if basin is not None else 9.0
                    if db < rj + 0.45:
                        continue
                    dd = min(1.6, min((d_.distance(p) for d_ in doors), default=9.0))   # nie zastawiaj drzwi
                    sc = 1.2 * dd + 0.35 * min(db, 3.0) - 0.15 * p.distance(hub)
                    if best is None or sc > best[0]:
                        best = (sc, p)
        if best is not None:
            pj = best[1]
            feats.append(Feature("jacuzzi", pj.x, pj.y, rj + 0.3, rj=rj))
            for ln in paths:                                                # ścieżka z płyt od drzwi do jacuzzi
                d0 = Point(ln.coords[0])
                steps_along(_odcinek(d0, pj, rj + 0.4), cls="plyta")
        # drzewko owocowe w gruncie (cytryna – owoce przez cały rok pod szkłem): w narożniku z dala od jacuzzi, niecki i drzwi
        zt = inner.buffer(-0.7)
        bt = None
        if not zt.is_empty:
            minx, miny, maxx, maxy = zt.bounds
            for i in range(14):
                for j in range(14):
                    p = Point(minx + (maxx - minx) * (i + 0.5) / 14, miny + (maxy - miny) * (j + 0.5) / 14)
                    if not zt.contains(p):
                        continue
                    dj = min((math.hypot(f.x - p.x, f.y - p.y) - f.r for f in feats if f.t in ("jacuzzi", "wodospad")), default=9.0)
                    if dj < 0.85 or (basin is not None and basin.distance(p) < 0.9):
                        continue
                    dd = min((d_.distance(p) for d_ in doors), default=9.0)
                    if dd < 1.0:
                        continue
                    sc = min(dj, 2.0) + 0.5 * min(dd, 2.5)
                    if bt is None or sc > bt[0]:
                        bt = (sc, p)
        if bt is not None:
            feats.append(Feature("cytrus", bt[1].x, bt[1].y, 0.75, h=2.6, grunt=True))
        # rabaty kwiatów (lawenda, byliny) i kilka paproci
        for i in range(9 if area > 30 else 7):
            p = spot(0.3)
            if p:
                feats.append(Feature("lawenda", p[0], p[1], 0.3))
        for i in range(2):
            p = spot(0.35)
            if p:
                feats.append(Feature("paproc", p[0], p[1], 0.35))
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


def _odcinek(a, b, cut):
    """Odcinek od punktu a w stronę b, skrócony o cut przy b."""
    L = a.distance(b)
    if L <= cut + 0.3:
        return LineString([(a.x, a.y), (a.x + 1e-3, a.y)])
    t = (L - cut) / L
    return LineString([(a.x, a.y), (a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t)])


def _sciana_wodospadu(g, level):
    """Najdłuższa pełna ściana ogrodu (zewnętrzna, bez okien): ((ax, ay), (bx, by), nx, ny) – n w głąb ogrodu."""
    best = None
    for run in level["runs"]:
        if run.cls != "ext" or run.spec not in ("solid", "wall"):
            continue
        if not (run.room is g or run.other is g):
            continue
        (ax, ay), (bx, by) = run.pts[0], run.pts[-1]
        L = math.hypot(bx - ax, by - ay)
        if L < 2.4:
            continue
        nx, ny = run.normal
        mx, my = (ax + bx) / 2, (ay + by) / 2
        if not g.poly.contains(Point(mx + nx * 0.5, my + ny * 0.5)):
            nx, ny = -nx, -ny
        if best is None or L > best[0]:
            best = (L, ((ax, ay), (bx, by), nx, ny))
    return best[1] if best else None


def _miejsce_stolu(g, level, net, inner):
    """Stół jadalny w ogrodzie: przy najdłuższej szklanej (najlepiej harmonijkowej) ścianie od jadalni / kuchni."""
    from .meble import dining, round_dining
    cand = []
    for run in level["runs"]:
        if run.room is not g or run.other is None or run.other.outdoor or run.cls not in ("fold", "glass"):
            continue
        pri = (2 if run.cls == "fold" else 1) + (1 if run.other.kind in ("jadalnia", "kuchnia", "salon_kuchnia") else 0)
        cand.append((pri, run.length, run))
    if not cand:
        return None
    cand.sort(key=lambda c: (c[0], c[1]), reverse=True)
    run = cand[0][2]
    (ax, ay), (bx, by) = run.pts[0], run.pts[-1]
    L = math.hypot(bx - ax, by - ay) or 1.0
    ux, uy = (bx - ax) / L, (by - ay) / L
    nx, ny = -run.normal[0], -run.normal[1]           # w głąb ogrodu
    rot = math.degrees(math.atan2(uy, ux))
    zone_ok = inner.buffer(-0.05)
    for n, rnd_ in ((8, False), (6, False), (4, False), (4, True)):
        it = round_dining(r=0.55, n=4) if rnd_ else dining(n)
        depth = it.d
        for off in (0.0, 0.6, -0.6, 1.2, -1.2):
            cx = (ax + bx) / 2 + ux * off + nx * (0.32 + depth / 2)
            cy = (ay + by) / 2 + uy * off + ny * (0.32 + depth / 2)
            fp = it.footprint(cx, cy, rot)
            if zone_ok.contains(fp):
                return dict(cx=cx, cy=cy, rot=rot, n=n, okragly=rnd_, strefa=fp.buffer(0.25))
    return None


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
        elif t == "jacuzzi":
            rj = ft.kw.get("rj", 1.0) * s
            out.append(f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" class="g-obrzeze"/><circle cx="{f(x)}" cy="{f(y)}" r="{f(rj)}" class="g-woda"/>'
                       f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(rj * 0.62)}" class="g-linia" fill="none"/>')
        elif t == "wodospad":
            b = ft.kw.get("basin")
            if b is not None:
                pts = " ".join(f"{f(a_)},{f(b_)}" for a_, b_ in (P(*c) for c in list(b.exterior.coords)[:-1]))
                out.append(f'<polygon points="{pts}" class="g-woda"/>')
                c0 = list(b.exterior.coords)
                (x1, y1), (x2, y2) = P(*c0[0]), P(*c0[1])
                out.append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" class="g-obrzeze" style="stroke-width:3"/>')
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
