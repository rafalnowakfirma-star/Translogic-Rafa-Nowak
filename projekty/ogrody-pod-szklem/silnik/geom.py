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


def sector(cx, cy, r1, r2, a1, a2, step=STEP):
    """Wycinek pierścienia: promienie r1–r2, kąty a1–a2 (a1 < a2)."""
    angs = arc_angles(a1, a2, step)
    outer = [pt(cx, cy, r2, a) for a in angs]
    inner = [pt(cx, cy, r1, a) for a in reversed(angs)] if r1 > 1e-6 else [(cx, cy)]
    return Polygon(outer + inner)


def ell_sector(cx, cy, rx1, ry1, rx2, ry2, a1, a2, step=STEP):
    """Wycinek pierścienia eliptycznego (parametr kąta jak w sector)."""
    angs = arc_angles(a1, a2, step)
    outer = [(cx + rx2 * math.cos(math.radians(a)), cy + ry2 * math.sin(math.radians(a))) for a in angs]
    if rx1 > 1e-6:
        inner = [(cx + rx1 * math.cos(math.radians(a)), cy + ry1 * math.sin(math.radians(a))) for a in reversed(angs)]
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
    return unary_union(list(gs))


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
