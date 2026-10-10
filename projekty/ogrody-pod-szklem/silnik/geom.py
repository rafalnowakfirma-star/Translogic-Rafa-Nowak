"""Pomocnicze kształty. Układ: x na wschód, y na południe (jak na rysunku), metry.

Kąty w stopniach liczone od wschodu zgodnie z ruchem wskazówek zegara na rysunku
(0 = wschód, 90 = południe, 180 = zachód, 270 = północ).
"""
import math

from shapely import affinity
from shapely.geometry import Polygon, Point, LineString, MultiPolygon, GeometryCollection, box
from shapely.ops import unary_union, linemerge

STEP = 7.5  # krok podziału łuków (stopnie), wspólny dla wszystkich – łuki sąsiednich pokoi mają te same wierzchołki

DIRS = {"E": 0, "SE": 45, "S": 90, "SW": 135, "W": 180, "NW": 225, "N": 270, "NE": 315}


def rect(x1, y1, x2, y2):
    """Prostokąt (oś ścian) od (x1, y1) do (x2, y2)."""
    x1, x2 = min(x1, x2), max(x1, x2)
    y1, y2 = min(y1, y2), max(y1, y2)
    return Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)])


def poly(*pts):
    """Wielokąt z listy punktów: poly((0,0),(4,0),(4,3)) albo poly([(0,0),...])."""
    if len(pts) == 1:
        pts = pts[0]
    return Polygon(pts)


def pt(cx, cy, r, a):
    a = math.radians(a)
    return (cx + r * math.cos(a), cy + r * math.sin(a))


def arc_angles(a1, a2, step=STEP):
    """Kąty od a1 do a2 z pośrednimi wielokrotnościami kroku (globalnie wyrównane)."""
    out = [a1]
    k = math.floor(a1 / step + 1e-9) + 1
    while k * step < a2 - 1e-6:
        out.append(k * step)
        k += 1
    out.append(a2)
    return out


def arc_pt(cx, cy, r, a, step=STEP):
    """Punkt pod kątem a na wielokącie okręgu (wierzchołki co `step`).
    Dla kątów spoza siatki leży na cięciwie, więc pokrywa się z bokiem koła/wycinka sąsiada."""
    k = a / step
    if abs(k - round(k)) < 1e-9:
        return pt(cx, cy, r, a)
    a0 = math.floor(k) * step
    mid = a0 + step / 2
    return pt(cx, cy, r * math.cos(math.radians(step / 2)) / math.cos(math.radians(a - mid)), a)


def ell_pt(cx, cy, rx, ry, a, step=STEP):
    """Punkt elipsy dla parametru a; poza siatką – na cięciwie między sąsiednimi wierzchołkami."""
    k = a / step
    if abs(k - round(k)) < 1e-9:
        return (cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)))
    a0 = math.floor(k) * step
    t = (a - a0) / step
    p0 = (cx + rx * math.cos(math.radians(a0)), cy + ry * math.sin(math.radians(a0)))
    p1 = (cx + rx * math.cos(math.radians(a0 + step)), cy + ry * math.sin(math.radians(a0 + step)))
    return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)


def sector(cx, cy, r1, r2, a1, a2, step=STEP):
    """Wycinek pierścienia: promienie r1–r2, kąty a1–a2 (a1 < a2).
    Kąty mogą być dowolne – punkty spoza siatki 7,5° leżą na cięciwach, więc łuki sąsiadów się pokrywają."""
    angs = arc_angles(a1, a2, step)
    outer = [arc_pt(cx, cy, r2, a, step) for a in angs]
    inner = [arc_pt(cx, cy, r1, a, step) for a in reversed(angs)] if r1 > 1e-6 else [(cx, cy)]
    return Polygon(outer + inner)


def ell_sector(cx, cy, rx1, ry1, rx2, ry2, a1, a2, step=STEP):
    """Wycinek pierścienia eliptycznego (parametr kąta jak w sector)."""
    angs = arc_angles(a1, a2, step)
    outer = [ell_pt(cx, cy, rx2, ry2, a, step) for a in angs]
    if rx1 > 1e-6:
        inner = [ell_pt(cx, cy, rx1, ry1, a, step) for a in reversed(angs)]
    else:
        inner = [(cx, cy)]
    return Polygon(outer + inner)


def circle(cx, cy, r, step=STEP):
    return Polygon([pt(cx, cy, r, a) for a in arc_angles(0, 360, step)[:-1]])


def ellipse(cx, cy, rx, ry, step=STEP):
    return Polygon([(cx + rx * math.cos(math.radians(a)), cy + ry * math.sin(math.radians(a)))
                    for a in arc_angles(0, 360, step)[:-1]])


def ngon(cx, cy, n, apothem, rot=0.0):
    """Wielokąt foremny: apothem = odległość środka od boku; rot = kąt normalnej pierwszego boku."""
    R = apothem / math.cos(math.pi / n)
    return Polygon([pt(cx, cy, R, rot + 180.0 / n + 360.0 * k / n) for k in range(n)])


def ngon_vertex(cx, cy, n, apothem, k, rot=0.0):
    """Wierzchołek k wielokąta foremnego (między bokiem k a k+1)."""
    R = apothem / math.cos(math.pi / n)
    return pt(cx, cy, R, rot + 180.0 / n + 360.0 * k / n)


def ngon_band(cx, cy, n, a_in, a_out, k, span=1, rot=0.0):
    """Pas wielokąta foremnego między apotemami a_in i a_out dla boków k..k+span-1."""
    outer = [ngon_vertex(cx, cy, n, a_out, k - 1 + i, rot) for i in range(span + 1)]
    if a_in > 1e-6:
        inner = [ngon_vertex(cx, cy, n, a_in, k - 1 + i, rot) for i in range(span, -1, -1)]
    else:
        inner = [(cx, cy)]
    return Polygon(outer + inner)


def hexagon(cx, cy, apothem, rot=0.0):
    """Sześciokąt; rot=0 → płaski bok skierowany na wschód."""
    return ngon(cx, cy, 6, apothem, rot)


def rotate(g, deg, origin=(0, 0)):
    return affinity.rotate(g, deg, origin=origin)


def move(g, dx, dy):
    return affinity.translate(g, dx, dy)


def union(*gs):
    """Suma kształtów; drobne szczeliny z zaokrągleń są domykane, żeby wyszedł jeden wielokąt."""
    import shapely
    g = unary_union([shapely.set_precision(x, 1e-6) for x in gs])
    if isinstance(g, MultiPolygon):
        h = g.buffer(2e-4, join_style="mitre").buffer(-2e-4, join_style="mitre")
        if isinstance(h, Polygon):
            g = h
    return g


def largest(g):
    """Największy wielokąt z geometrii złożonej."""
    if g is None or g.is_empty:
        return None
    if isinstance(g, Polygon):
        return g
    polys = [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]
    if not polys:
        sub = []
        for p in getattr(g, "geoms", []):
            if isinstance(p, MultiPolygon):
                sub.extend(p.geoms)
        polys = sub
    return max(polys, key=lambda p: p.area) if polys else None


def polygons(g):
    """Lista wielokątów z dowolnej geometrii."""
    if g is None or g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g]
    out = []
    for p in getattr(g, "geoms", []):
        out.extend(polygons(p))
    return out


def norm_angle(a):
    return a % 360.0


def ang_diff(a, b):
    d = abs(norm_angle(a) - norm_angle(b)) % 360.0
    return min(d, 360.0 - d)


def dir_angle(d):
    """'N'/'E'/... albo liczba → kąt."""
    if isinstance(d, (int, float)):
        return float(d)
    return float(DIRS[d.upper()])
