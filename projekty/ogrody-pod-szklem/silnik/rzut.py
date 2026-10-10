"""Rzuty kondygnacji i rzut dachu jako SVG."""
import math

from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union, polylabel

from .geom import polygons, largest
from .meble import furnish_level, frame
from .ogrod import garden_layout, svg_garden

S = 34.0   # px na metr


def f(v):
    return f"{v:.1f}"


class Canvas:
    def __init__(self, house, uid, pad=56, extra=None):
        self.house, self.uid, self.s = house, uid, S
        minx, miny, maxx, maxy = house.bbox
        if extra is not None:
            ex = extra.bounds
            minx, miny, maxx, maxy = min(minx, ex[0]), min(miny, ex[1]), max(maxx, ex[2]), max(maxy, ex[3])
        m = 2.2
        self.x0, self.y0 = minx - m, miny - m
        self.x1, self.y1 = maxx + m, maxy + m
        self.pad = pad
        self.W = (self.x1 - self.x0) * S + 2 * pad
        self.H = (self.y1 - self.y0) * S + 2 * pad + 18
        self.el = []
        self.defs = {}

    def P(self, x, y):
        return (self.pad + (x - self.x0) * S, self.pad + (y - self.y0) * S)

    def path(self, geom, cls, extra=""):
        for p in polygons(geom):
            if p.area < 1e-4:
                continue
            d = "M" + " L".join(f"{f(a)},{f(b)}" for a, b in (self.P(*c) for c in p.exterior.coords[:-1])) + " Z"
            for h in p.interiors:
                d += " M" + " L".join(f"{f(a)},{f(b)}" for a, b in (self.P(*c) for c in h.coords[:-1])) + " Z"
            self.el.append(f'<path d="{d}" class="{cls}" fill-rule="evenodd" {extra}/>')

    def line(self, a, b, cls):
        (x1, y1), (x2, y2) = self.P(*a), self.P(*b)
        self.el.append(f'<line x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}" class="{cls}"/>')

    def pline(self, pts, cls):
        self.el.append(f'<polyline points="{" ".join(f"{f(a)},{f(b)}" for a, b in (self.P(*p) for p in pts))}" class="{cls}"/>')

    def text(self, x, y, s, cls, anchor="middle", dy=0, rot=None):
        a, b = self.P(x, y)
        b += dy
        tr = f' transform="rotate({rot:.1f} {f(a)} {f(b)})"' if rot is not None else ""
        self.el.append(f'<text x="{f(a)}" y="{f(b)}" text-anchor="{anchor}" class="{cls}"{tr}>{s}</text>')

    def pattern(self, kind, angle=0.0):
        a = int(round(angle)) % 180
        pid = f"{self.uid}-{kind}-{a}"
        if pid not in self.defs:
            self.defs[pid] = _pattern(pid, kind, a)
        return pid

    def render(self, label, cls="plan"):
        defs = "<defs>" + "".join(self.defs.values()) + "</defs>"
        return (f'<svg class="drw {cls}" viewBox="0 0 {self.W:.0f} {self.H:.0f}" role="img" aria-label="{label}" '
                f'xmlns="http://www.w3.org/2000/svg">{defs}' + "".join(self.el) + "</svg>")


def _pattern(pid, kind, a):
    s = S
    tr = f' patternTransform="rotate({a})"' if a else ""
    if kind in ("drewno", "drewno_ciemne", "deska"):
        h = 0.2 * s if kind != "deska" else 0.14 * s
        w = 1.8 * s
        cls = {"drewno": "pt-wood", "drewno_ciemne": "pt-wood2", "deska": "pt-deck"}[kind]
        rows = 4
        body = f'<rect width="{f(w)}" height="{f(h * rows)}" class="{cls}"/>'
        for i in range(rows):
            y = (i + 1) * h - 0.5
            body += f'<line x1="0" y1="{f(y)}" x2="{f(w)}" y2="{f(y)}" class="pt-line"/>'
            jx = [0.3, 1.1, 0.7, 1.5][i] * s
            body += f'<line x1="{f(jx)}" y1="{f(i * h)}" x2="{f(jx)}" y2="{f((i + 1) * h)}" class="pt-line"/>'
        return f'<pattern id="{pid}" width="{f(w)}" height="{f(h * rows)}" patternUnits="userSpaceOnUse"{tr}>{body}</pattern>'
    if kind in ("kamien", "trawertyn", "plyty"):
        w, h = (0.9 * s, 0.45 * s) if kind == "trawertyn" else (0.6 * s, 0.6 * s)
        cls = "pt-stone" if kind != "plyty" else "pt-slab"
        body = (f'<rect width="{f(2 * w)}" height="{f(2 * h)}" class="{cls}"/>'
                f'<path d="M0,{f(h)} H{f(2 * w)} M0,{f(2 * h - 0.5)} H{f(2 * w)} M{f(w)},0 V{f(h)} M{f(w / 2)},{f(h)} V{f(2 * h)} M{f(1.5 * w)},{f(h)} V{f(2 * h)}" class="pt-line"/>')
        return f'<pattern id="{pid}" width="{f(2 * w)}" height="{f(2 * h)}" patternUnits="userSpaceOnUse"{tr}>{body}</pattern>'
    if kind == "terakota":
        w = 0.3 * s
        body = f'<rect width="{f(w)}" height="{f(w)}" class="pt-terra"/><path d="M0,{f(w - 0.5)} H{f(w)} M{f(w - 0.5)},0 V{f(w)}" class="pt-line"/>'
        return f'<pattern id="{pid}" width="{f(w)}" height="{f(w)}" patternUnits="userSpaceOnUse"{tr}>{body}</pattern>'
    if kind == "cegla":
        w, h = 0.25 * s, 0.065 * s * 2
        body = (f'<rect width="{f(2 * w)}" height="{f(2 * h)}" class="pt-brick"/>'
                f'<path d="M0,{f(h)} H{f(2 * w)} M0,{f(2 * h - 0.4)} H{f(2 * w)} M{f(w)},0 V{f(h)} M{f(w / 2)},{f(h)} V{f(2 * h)} M{f(1.5 * w)},{f(h)} V{f(2 * h)}" class="pt-line"/>')
        return f'<pattern id="{pid}" width="{f(2 * w)}" height="{f(2 * h)}" patternUnits="userSpaceOnUse"{tr}>{body}</pattern>'
    if kind == "tatami":
        u = 0.9 * s
        body = (f'<rect x="0.6" y="0.6" width="{f(u - 1.2)}" height="{f(2 * u - 1.2)}" class="pt-tatami"/>'
                f'<rect x="{f(u + 0.6)}" y="0.6" width="{f(u - 1.2)}" height="{f(u - 1.2)}" class="pt-tatami"/>'
                f'<rect x="{f(u + 0.6)}" y="{f(u + 0.6)}" width="{f(u - 1.2)}" height="{f(u - 1.2)}" class="pt-tatami"/>')
        return f'<pattern id="{pid}" width="{f(2 * u)}" height="{f(2 * u)}" patternUnits="userSpaceOnUse"{tr}>{body}</pattern>'
    if kind == "beton":
        w = 1.2 * s
        body = f'<rect width="{f(w)}" height="{f(w)}" class="pt-conc"/><circle cx="{f(w * 0.3)}" cy="{f(w * 0.4)}" r="0.7" class="pt-dot"/><circle cx="{f(w * 0.75)}" cy="{f(w * 0.8)}" r="0.6" class="pt-dot"/>'
        return f'<pattern id="{pid}" width="{f(w)}" height="{f(w)}" patternUnits="userSpaceOnUse"{tr}>{body}</pattern>'
    if kind == "zwir_grabiony":
        h = 0.11 * s
        body = f'<rect width="{f(8)}" height="{f(h)}" class="pt-gravel"/><line x1="0" y1="{f(h / 2)}" x2="8" y2="{f(h / 2)}" class="pt-rake"/>'
        return f'<pattern id="{pid}" width="8" height="{f(h)}" patternUnits="userSpaceOnUse"{tr}>{body}</pattern>'
    if kind == "sedum":
        w = 0.5 * s
        body = (f'<rect width="{f(w)}" height="{f(w)}" class="pt-sedum"/><circle cx="{f(w * 0.25)}" cy="{f(w * 0.3)}" r="1.4" class="pt-sedum2"/>'
                f'<circle cx="{f(w * 0.7)}" cy="{f(w * 0.65)}" r="1.1" class="pt-sedum3"/><circle cx="{f(w * 0.8)}" cy="{f(w * 0.15)}" r="0.9" class="pt-sedum2"/>')
        return f'<pattern id="{pid}" width="{f(w)}" height="{f(w)}" patternUnits="userSpaceOnUse">{body}</pattern>'
    if kind == "zwir":
        w = 0.3 * s
        body = f'<rect width="{f(w)}" height="{f(w)}" class="pt-roofgravel"/><circle cx="{f(w * 0.3)}" cy="{f(w * 0.3)}" r="0.8" class="pt-dot"/><circle cx="{f(w * 0.75)}" cy="{f(w * 0.7)}" r="0.7" class="pt-dot"/>'
        return f'<pattern id="{pid}" width="{f(w)}" height="{f(w)}" patternUnits="userSpaceOnUse">{body}</pattern>'
    if kind == "trawa":
        w = 0.4 * s
        body = f'<rect width="{f(w)}" height="{f(w)}" class="pt-grass"/><path d="M{f(w * 0.2)},{f(w * 0.5)} l1,-2.5 M{f(w * 0.7)},{f(w * 0.9)} l1,-2.5" class="pt-grassl"/>'
        return f'<pattern id="{pid}" width="{f(w)}" height="{f(w)}" patternUnits="userSpaceOnUse">{body}</pattern>'
    return f'<pattern id="{pid}" width="10" height="10" patternUnits="userSpaceOnUse"><rect width="10" height="10" class="pt-wood"/></pattern>'


FLOOR_PATTERN = {"drewno": "drewno", "drewno_ciemne": "drewno_ciemne", "deska": "deska", "kamien": "kamien",
                 "trawertyn": "trawertyn", "plyty": "plyty", "terakota": "terakota", "cegla": "cegla", "tatami": "tatami",
                 "beton": "beton"}


def _room_angle(r):
    try:
        cx, cy, ang, L, W = frame(r.net)
        return ang
    except Exception:
        return 0.0


# ----------------------------------------------------------------- rzut poziomu
def _site_extent(house):
    gs = [s_["shape"] for s_ in house.site if s_["t"] == "path"]
    gs += [Point(s_["x"], s_["y"]).buffer(s_.get("r") or 1.2) for s_ in house.site if s_["t"] == "tree"]
    return unary_union(gs) if gs else None


def _site_trees(C, house):
    from .ogrod import _tree_svg
    for s_ in house.site:
        if s_["t"] == "tree":
            x, y = C.P(s_["x"], s_["y"])
            kind = s_["kind"] if s_["kind"] in ("klon", "brzoza", "oliwka", "sosna", "palma", "cytrus") else "drzewo"
            C.el.append(_tree_svg(kind, x, y, (s_.get("r") or 1.6) * S, f))


def plan_level(house, idx, uid):
    L = house.L[idx]
    lev = house.levels[idx]
    C = Canvas(house, uid, extra=_site_extent(house))
    rooms = L["rooms"]
    # teren
    site = Polygon([(C.x0, C.y0), (C.x1, C.y0), (C.x1, C.y1), (C.x0, C.y1)])
    C.path(site, "", f'fill="url(#{C.pattern("trawa")})"')
    for s_ in house.site:
        if s_["t"] == "path":
            C.path(s_["shape"], "pl-path")
    _site_trees(C, house)
    # dachy niższych poziomów widoczne z góry
    if idx > min(house.L):
        for z, poly, fin, li in house.roofs:
            if li < idx:
                C.path(poly, "", f'fill="url(#{C.pattern(fin if fin in ("sedum", "zwir") else "zwir")})" class="pl-roofbelow"')
                C.path(poly, "pl-roofedge")
        # ogrody z poziomu 0 widziane z góry
    # posadzki
    for r in rooms:
        if r.kind in ("ogrod", "ogrod_void"):
            continue
        if r.kind == "void":
            C.path(r.net, "pl-void")
            continue
        if r.outdoor and r.level == min(house.L) and r.kind == "taras":
            C.path(r.net, "", f'fill="url(#{C.pattern("deska", _room_angle(r))})"')
            continue
        pat = FLOOR_PATTERN.get(r.floor, "drewno")
        C.path(r.net, "", f'fill="url(#{C.pattern(pat, _room_angle(r))})"')
    # ogród
    for r in rooms:
        if r.kind == "ogrod":
            lay = garden_layout(r, L, house)
            r._layout = lay
            g_el = []
            for kind, geom in lay["floor"]:
                if kind == "zwir_grabiony":
                    C.path(geom, "", f'fill="url(#{C.pattern("zwir_grabiony", _room_angle(r))})"')
                elif kind == "plyty":
                    C.path(geom, "", f'fill="url(#{C.pattern("plyty", _room_angle(r))})"')
                else:
                    C.path(geom, f"g-{kind}")
            lay2 = dict(lay)
            lay2["floor"] = []
            C.el.extend(svg_garden(lay2, _PX(C), f))
        elif r.kind == "ogrod_void":
            g = r.parent
            lay = getattr(g, "_layout", None)
            if lay is not None:
                C.path(r.net, "pl-gvoid")
                C.el.append('<g class="pl-below">')
                C.el.extend(svg_garden(dict(floor=[], features=[ft for ft in lay["features"] if ft.t in ("klon", "brzoza", "oliwka", "palma", "sosna", "cytrus")]), _PX(C), f))
                C.el.append("</g>")
    # cienie ścian
    wu = L["wall_union"]
    if not wu.is_empty:
        from shapely import affinity
        sh = affinity.translate(wu, 0.12, 0.16).difference(wu)
        C.path(sh, "pl-shadow")
    # meble
    items = furnish_level(house, idx)
    L["items"] = items
    C.el.append('<g class="furn">')
    for it in items:
        C.el.append(_item_svg(C, it))
    C.el.append("</g>")
    # schody i otwory schodowe
    for fp, s in L.get("voids", []):
        C.path(fp, "pl-stairvoid")
    for s in house.stairs:
        if s.level == idx or s.to_level == idx:
            _stair_svg(C, s, upper=(s.to_level == idx))
    # ściany
    solid = L["wall_solid"]
    for cls in ("low", "gwall"):
        if cls in solid:
            C.path(solid[cls], f"w-{cls}")
    if "glass" in solid:
        C.path(solid["glass"], "w-glass")
    if "fold" in solid:
        C.path(solid["fold"], "w-glass")
    for cls in ("int", "ext"):
        if cls in solid:
            C.path(solid[cls], f"w-{cls}")
    # przeszklenia: linie lic i słupki
    for run in L["walls"]:
        if run.cls in ("glass", "fold"):
            _glass_lines(C, run)
        elif run.cls == "railing":
            _offset_lines(C, run, 0.03, "w-rail")
        elif run.cls == "columns":
            n = max(2, int(run.length / 2.4) + 1)
            for i in range(n):
                p = run.point_at(run.length * i / (n - 1))
                C.path(Point(p).buffer(0.13, cap_style="square"), "w-ext")
    for o in L["openings"]:
        _opening_svg(C, o, house)
    # pustki – krzyż i podpis
    for r in rooms:
        if r.kind == "void":
            b = r.net
            mrr = b.minimum_rotated_rectangle
            cs = list(mrr.exterior.coords)
            C.line(cs[0], cs[2], "pl-voidx")
            C.line(cs[1], cs[3], "pl-voidx")
            p = _label_point(r)
            C.text(p.x, p.y, f"pustka nad: {r.parent.name.lower()}", "t-void")
    # zadaszenia patio
    for r in rooms:
        if r.outdoor and isinstance(r.roof, Polygon) and r.parent is None:
            C.path(r.roof, "pl-patioroof")
            c = r.roof.representative_point()
            C.text(c.x, c.y - 0.6, "zadaszenie", "t-void")
        elif r.outdoor and r.roof == "full" and r.parent is None and r.kind != "patio_sezonowe":
            C.path(r.poly, "pl-patioroof")
    # dach szklany – obrys lub widok z góry
    for g in [r for r in house.all_rooms if r.kind == "ogrod"]:
        top_idx = g.level + g.levels - 1
        if top_idx == idx and idx > min(house.L):
            C.path(g.poly, "pl-glassroof")
        elif idx > top_idx:
            _glass_roof_svg(C, g, label=False)
    # opisy
    for r in rooms:
        if r.kind in ("void", "ogrod_void") or r.parent is not None:
            continue
        _label(C, r, house, L)
    for o in L["openings"]:
        if o.label:
            m = ((o.a[0] + o.b[0]) / 2, (o.a[1] + o.b[1]) / 2)
            n = o.run.normal
            C.text(m[0] + n[0] * 0.95, m[1] + n[1] * 0.95 + 0.1, "wejście", "t-entry")
    _dims(C, house)
    _north(C)
    _scalebar(C)
    C.text(C.x0 + 0.3, C.y1 + 0.35, f"{lev.name.upper()}  ·  poziom {lev.z:+.2f} m".replace(".", ","), "t-sheet", anchor="start")
    return C.render(f"{house.name} – {lev.name}")


class _PX:
    def __init__(self, C):
        self.C, self.s = C, C.s

    def __call__(self, x, y):
        return self.C.P(x, y)


def _label_point(r, items=None):
    net = r.net if r.net is not None else r.poly
    if r.label_at:
        return Point(r.label_at)
    base = net.buffer(-0.1) if net.buffer(-0.1).area > 0.5 else net
    if items is not None:
        occ_l = [it.footprint().buffer(0.12) for it in items if getattr(it, "room", None) is r and it.kind != "dywan"]
        for s in r.house.stairs:
            if s.level == r.level or s.to_level == r.level:
                occ_l.append(s.footprint().buffer(0.15))
        occ = unary_union(occ_l) if occ_l else Polygon()
        free = base.difference(occ) if not occ.is_empty else base
        free = largest(free)
        if free is not None and free.area > 1.2:
            # szerokość pozwala na podpis?
            try:
                p = polylabel(free, 0.05)
                if free.buffer(-0.35).area > 0.2 or free.area > 3:
                    return p
            except Exception:
                pass
    try:
        return polylabel(base, 0.05)
    except Exception:
        return net.representative_point()


ROOF_NOTE = {"slide": "dach szklany przesuwny", "pyramid": "piramida szklana, otwierana latarnia",
             "iris": "kopuła szklana, przesłona jak migawka", "louvre": "obrotowe lamele szklane",
             "fold": "dach szklany harmonijkowy", "ridge": "dach szklany dwuspadowy, uchylny",
             "vault": "szklana kolebka, rozsuwana"}


def _occupied(r, items):
    occ = [it.footprint().buffer(0.1) for it in (items or []) if getattr(it, "room", None) is r and it.kind != "dywan"]
    for s in r.house.stairs:
        if s.level == r.level or s.to_level == r.level:
            occ.append(s.footprint().buffer(0.12))
    lay = getattr(r, "_layout", None)
    if r.kind == "ogrod" and lay:
        for f in lay["features"]:
            if f.t not in ("krok", "lilia", "mech"):
                occ.append(Point(f.x, f.y).buffer(f.r + 0.05))
    return unary_union(occ) if occ else Polygon()


def _place_box(r, items, layouts):
    """Szuka miejsca na ramkę podpisu: w obrysie pokoju, bez mebli, możliwie blisko środka.
    layouts: lista (szerokość_m, góra_m, dół_m) w kolejności preferencji. Zwraca (punkt, nr układu)."""
    from shapely.prepared import prep
    net = r.net if r.net is not None else r.poly
    base = net.buffer(-0.08)
    if base.is_empty or base.area < 0.3:
        base = net
    occ = _occupied(r, items)
    free = largest(base.difference(occ)) if not occ.is_empty else base
    try:
        ctr = polylabel(free if free is not None and free.area > 0.5 else base, 0.05)
    except Exception:
        ctr = base.representative_point()
    pb, po = prep(base), (prep(occ) if not occ.is_empty else None)
    minx, miny, maxx, maxy = base.bounds
    diag = math.hypot(maxx - minx, maxy - miny)
    best = None
    for li, (w, top, bot) in enumerate(layouts):
        step = 0.2 if diag < 25 else 0.35
        ny, nx = int((maxy - miny) / step) + 1, int((maxx - minx) / step) + 1
        for iy in range(ny):
            y = miny + iy * step
            for ix in range(nx):
                x = minx + ix * step
                b = Polygon([(x - w / 2, y - top), (x + w / 2, y - top), (x + w / 2, y + bot), (x - w / 2, y + bot)])
                if not pb.contains(b):
                    continue
                ov = b.intersection(occ).area if (po is not None and po.intersects(b)) else 0.0
                score = ov * 40 + math.hypot(x - ctr.x, y - ctr.y) * 0.25 + li * 0.6
                if best is None or score < best[0]:
                    best = (score, Point(x, y), li, ov)
        if best is not None and best[3] < 1e-6 and best[2] == li:
            return best[1], li
    if best is not None:
        return best[1], best[2]
    return ctr, 0


def _label(C, r, house, L):
    a = r.net.area if r.net is not None else r.poly.area
    for fp, s in L.get("voids", []):
        a -= r.net.intersection(fp).area if r.net is not None else 0
    name = r.name
    note = None
    if r.kind == "ogrod":
        note = ROOF_NOTE.get(r.roof_type, "dach szklany otwierany")
    elif r.kind == "patio_sezonowe":
        note = "zimą zamknięte, latem otwarte"
    nw = (len(note) * 4.3) if note else 0
    words = name.split(" ")
    mid = len(words) // 2 + (len(words) % 2)
    two = [" ".join(words[:mid]), " ".join(words[mid:])] if len(words) > 1 else [name]
    big = 6.6 if r.kind != "ogrod" else 7.0
    cand = [([name], "t-room" if r.kind != "ogrod" else "t-garden", big), ([name], "t-room-s", 5.5)]
    if len(two) == 2:
        cand.append((two, "t-room-s", 5.5))
    layouts = []
    for lines, cls, cw in cand:
        n = len(lines)
        w = max(max(len(x) for x in lines) * cw, 34, nw) / S + 0.1
        top = (13 + (n - 1) * 6) / S
        bot = (12 + (n - 1) * 6 + (12 if note else 0)) / S
        layouts.append((w, top, bot))
    if r.label_at:
        p, li = Point(r.label_at), 0
    else:
        p, li = _place_box(r, L.get("items"), layouts)
    lines, cls, _ = cand[li]
    if r.kind == "ogrod":
        cls = "t-garden"
    for i, ln in enumerate(lines):
        C.text(p.x, p.y, ln, cls, dy=-3 + i * 12 - (len(lines) - 1) * 6)
    C.text(p.x, p.y, f"{a:.1f} m²".replace(".", ","), "t-area", dy=9 + (len(lines) - 1) * 6)
    if note:
        C.text(p.x, p.y, note, "t-void", dy=20 + (len(lines) - 1) * 6)


def _halfwidth(net, p):
    best = 99
    for ang in (0, 90):
        a = math.radians(ang)
        ln = LineString([(p.x - 30 * math.cos(a), p.y - 30 * math.sin(a)), (p.x + 30 * math.cos(a), p.y + 30 * math.sin(a))])
        inter = ln.intersection(net)
        for g in polygons(inter.buffer(0.001)) if False else _segs(inter):
            if g.distance(p) < 1e-6:
                best = min(best, g.length / 2) if ang == 0 else best
    return best if best < 99 else 2.0


def _segs(g):
    if g.is_empty:
        return []
    if g.geom_type == "LineString":
        return [g]
    out = []
    for x in getattr(g, "geoms", []):
        out.extend(_segs(x))
    return out


def _offset_lines(C, run, off, cls):
    try:
        for side in (-off, off):
            ln = run.line.offset_curve(side)
            C.pline(list(ln.coords), cls)
    except Exception:
        C.pline(run.pts, cls)


def _glass_lines(C, run):
    t = 0.12
    _offset_lines(C, run, t / 2, "w-glassface")
    C.pline(run.pts, "w-glassmid")
    L = run.length
    n = max(1, int(L / 1.25))
    for i in range(1, n):
        s_ = L * i / n
        p = run.point_at(s_)
        a = run.point_at(max(0, s_ - 0.01))
        b = run.point_at(min(L, s_ + 0.01))
        ex, ey = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(ex, ey) or 1
        nx, ny = -ey / ln, ex / ln
        C.line((p[0] - nx * t / 2, p[1] - ny * t / 2), (p[0] + nx * t / 2, p[1] + ny * t / 2), "w-mullion")
    if run.cls == "fold":
        pts = []
        n = max(4, int(L / 0.5))
        for i in range(n + 1):
            p = run.point_at(L * i / n)
            off = 0.09 if i % 2 else -0.09
            pts.append((p[0] + run.normal[0] * off, p[1] + run.normal[1] * off))
        C.pline(pts, "w-fold")


def _opening_svg(C, o, house):
    a, b = o.a, o.b
    dx, dy = b[0] - a[0], b[1] - a[1]
    Lw = math.hypot(dx, dy)
    if Lw < 1e-6:
        return
    ux, uy = dx / Lw, dy / Lw
    nx, ny = o.run.normal
    t = o.t
    if o.cls in ("ext", "int", "gwall"):
        for p in (a, b):
            C.line((p[0] - nx * t / 2, p[1] - ny * t / 2), (p[0] + nx * t / 2, p[1] + ny * t / 2), "o-jamb")
    k = o.kind
    if k in ("win", "band"):
        g = 0.045
        C.path(Polygon([(a[0] - nx * g, a[1] - ny * g), (b[0] - nx * g, b[1] - ny * g), (b[0] + nx * g, b[1] + ny * g), (a[0] + nx * g, a[1] + ny * g)]), "o-glass")
        if o.sill < 0.3:
            C.line((a[0] + nx * t / 2, a[1] + ny * t / 2), (b[0] + nx * t / 2, b[1] + ny * t / 2), "o-thin")
    elif k == "slide":
        g = 0.035
        m = 0.5
        C.line((a[0] - nx * g, a[1] - ny * g), (a[0] + ux * Lw * (m + 0.06) - nx * g, a[1] + uy * Lw * (m + 0.06) - ny * g), "o-pane")
        C.line((a[0] + ux * Lw * (m - 0.06) + nx * g, a[1] + uy * Lw * (m - 0.06) + ny * g), (b[0] + nx * g, b[1] + ny * g), "o-pane")
    elif k in ("door", "pivot", "double"):
        # strona otwierania: do pomieszczenia 'into'
        sgn = 1.0
        into = o.into
        if into is not None:
            eff = house._effective(o.run.room).key
            sgn = -1.0 if into == eff else 1.0
        sx, sy = nx * sgn, ny * sgn
        if k == "double":
            half = Lw / 2
            for H, O, d in ((a, (a[0] + ux * half, a[1] + uy * half), 1), (b, (b[0] - ux * half, b[1] - uy * half), -1)):
                tip = (H[0] + sx * half, H[1] + sy * half)
                C.line(H, tip, "o-leaf")
                _arc(C, tip, O, half, H)
        elif k == "pivot":
            piv = (a[0] + ux * Lw * 0.25, a[1] + uy * Lw * 0.25)
            ang = math.radians(60)
            dxp = ux * math.cos(ang) + sx * math.sin(ang)
            dyp = uy * math.cos(ang) + sy * math.sin(ang)
            p1 = (piv[0] - dxp * Lw * 0.25, piv[1] - dyp * Lw * 0.25)
            p2 = (piv[0] + dxp * Lw * 0.75, piv[1] + dyp * Lw * 0.75)
            C.line(p1, p2, "o-leafthick")
            C.el.append(f'<circle cx="{f(C.P(*piv)[0])}" cy="{f(C.P(*piv)[1])}" r="2.2" class="o-pivot"/>')
        else:
            H, O = (a, b) if o.hinge == "a" else (b, a)
            tip = (H[0] + sx * Lw, H[1] + sy * Lw)
            C.line(H, tip, "o-leaf")
            _arc(C, tip, O, Lw, H)
    elif k in ("wide", "arch", "portal"):
        C.line(a, b, "o-head")


def _arc(C, p1, p2, r, center):
    (x1, y1), (x2, y2) = C.P(*p1), C.P(*p2)
    cr = (p1[0] - center[0]) * (p2[1] - center[1]) - (p1[1] - center[1]) * (p2[0] - center[0])
    sweep = 1 if cr > 0 else 0
    C.el.append(f'<path d="M{f(x1)},{f(y1)} A{f(r * S)},{f(r * S)} 0 0 {sweep} {f(x2)},{f(y2)}" class="o-swing"/>')


def _stair_svg(C, s, upper=False):
    cls = "st-up" if upper else "st"
    if s.kind == "spiral":
        cx, cy = s.p["center"]
        r = s.p.get("r", 1.0)
        a0 = s.p.get("start", 90)
        sw = s.p.get("sweep", 300)
        n = s.p.get("n", 15)
        C.path(Point(cx, cy).buffer(r, 64), cls)
        for i in range(n + 1):
            a = math.radians(a0 + sw * i / n)
            C.line((cx + 0.13 * math.cos(a), cy + 0.13 * math.sin(a)), (cx + r * math.cos(a), cy + r * math.sin(a)), "st-tread")
        C.path(Point(cx, cy).buffer(0.13, 24), "st-post")
        rr = r * 0.62
        pts = [(cx + rr * math.cos(math.radians(a0 + sw * i / 30)), cy + rr * math.sin(math.radians(a0 + sw * i / 30))) for i in range(31)]
        C.pline(pts, "st-walk")
        _arrowhead(C, pts[-2], pts[-1])
        C.path(Point(pts[0]).buffer(0.06), "st-dot")
        return
    x1, y1, x2, y2 = s.p["rect"]
    up = s.p.get("up", "E")
    flights = []
    if s.kind == "U":
        # dwa biegi obok siebie wzdłuż kierunku 'up', spocznik na końcu
        land = s.p.get("landing", 1.1)
        if up in ("E", "W"):
            ym = (y1 + y2) / 2
            if up == "E":
                flights = [((x1, y1, x2 - land, ym - 0.05), "E"), ((x1, ym + 0.05, x2 - land, y2), "W")]
                C.path(Polygon([(x2 - land, y1), (x2, y1), (x2, y2), (x2 - land, y2)]), cls)
            else:
                flights = [((x1 + land, y1, x2, ym - 0.05), "W"), ((x1 + land, ym + 0.05, x2, y2), "E")]
                C.path(Polygon([(x1, y1), (x1 + land, y1), (x1 + land, y2), (x1, y2)]), cls)
        else:
            xm = (x1 + x2) / 2
            if up == "S":
                flights = [((x1, y1, xm - 0.05, y2 - land), "S"), ((xm + 0.05, y1, x2, y2 - land), "N")]
                C.path(Polygon([(x1, y2 - land), (x2, y2 - land), (x2, y2), (x1, y2)]), cls)
            else:
                flights = [((x1, y1 + land, xm - 0.05, y2), "N"), ((xm + 0.05, y1 + land, x2, y2), "S")]
                C.path(Polygon([(x1, y1), (x2, y1), (x2, y1 + land), (x1, y1 + land)]), cls)
    else:
        flights = [((x1, y1, x2, y2), up)]
    for (a1, b1, a2, b2), d in flights:
        C.path(Polygon([(a1, b1), (a2, b1), (a2, b2), (a1, b2)]), cls)
        horiz = d in ("E", "W")
        length = (a2 - a1) if horiz else (b2 - b1)
        n = max(2, int(round(length / 0.27)))
        for i in range(1, n):
            if horiz:
                x = a1 + (a2 - a1) * i / n
                C.line((x, b1), (x, b2), "st-tread")
            else:
                y = b1 + (b2 - b1) * i / n
                C.line((a1, y), (a2, y), "st-tread")
        mx, my = (a1 + a2) / 2, (b1 + b2) / 2
        if d == "E":
            p, q = (a1 + 0.12, my), (a2 - 0.08, my)
        elif d == "W":
            p, q = (a2 - 0.12, my), (a1 + 0.08, my)
        elif d == "S":
            p, q = (mx, b1 + 0.12), (mx, b2 - 0.08)
        else:
            p, q = (mx, b2 - 0.12), (mx, b1 + 0.08)
        C.line(p, q, "st-walk")
        _arrowhead(C, p, q)


def _arrowhead(C, p, q):
    (x1, y1), (x2, y2) = C.P(*p), C.P(*q)
    a = math.atan2(y2 - y1, x2 - x1)
    h = 6
    pts = [(x2, y2), (x2 - h * math.cos(a - 0.4), y2 - h * math.sin(a - 0.4)), (x2 - h * math.cos(a + 0.4), y2 - h * math.sin(a + 0.4))]
    C.el.append(f'<polygon points="{" ".join(f"{f(x)},{f(y)}" for x, y in pts)}" class="st-arrow"/>')


def _item_svg(C, it):
    x, y = C.P(it.cx, it.cy)
    s = S
    out = [f'<g transform="translate({f(x)},{f(y)}) rotate({it.rot:.1f})">']
    for sh in it.shapes:
        k = sh[0]
        if k == "r":
            _, a, b, w, h, rx, cls = sh
            out.append(f'<rect x="{f(a * s)}" y="{f(b * s)}" width="{f(w * s)}" height="{f(h * s)}" rx="{f(rx * s)}" class="{cls}"/>')
        elif k == "c":
            _, a, b, r, cls = sh
            out.append(f'<circle cx="{f(a * s)}" cy="{f(b * s)}" r="{f(r * s)}" class="{cls}"/>')
        elif k == "e":
            _, a, b, rx, ry, cls = sh
            out.append(f'<ellipse cx="{f(a * s)}" cy="{f(b * s)}" rx="{f(rx * s)}" ry="{f(ry * s)}" class="{cls}"/>')
        elif k == "l":
            _, a, b, c, d, cls = sh
            out.append(f'<line x1="{f(a * s)}" y1="{f(b * s)}" x2="{f(c * s)}" y2="{f(d * s)}" class="{cls}-l"/>')
        elif k == "p":
            _, pts, cls = sh
            out.append(f'<polygon points="{" ".join(f"{f(px * s)},{f(py * s)}" for px, py in pts)}" class="{cls}"/>')
    out.append("</g>")
    return "".join(out)


def _dims(C, house):
    minx, miny, maxx, maxy = house.bbox
    minx, miny, maxx, maxy = minx - 0.2, miny - 0.2, maxx + 0.2, maxy + 0.2
    off = 1.25
    y = miny - off
    C.line((minx, y), (maxx, y), "d-dim")
    for x in (minx, maxx):
        C.line((x, miny - 0.25), (x, y - 0.15), "d-ext")
        (px, py) = C.P(x, y)
        C.el.append(f'<line x1="{f(px - 3.5)}" y1="{f(py + 3.5)}" x2="{f(px + 3.5)}" y2="{f(py - 3.5)}" class="d-tick"/>')
    C.text((minx + maxx) / 2, y, f"{maxx - minx:.1f} m".replace(".", ","), "d-t", dy=-5)
    x = minx - off
    C.line((x, miny), (x, maxy), "d-dim")
    for yy in (miny, maxy):
        C.line((minx - 0.25, yy), (x - 0.15, yy), "d-ext")
        (px, py) = C.P(x, yy)
        C.el.append(f'<line x1="{f(px - 3.5)}" y1="{f(py + 3.5)}" x2="{f(px + 3.5)}" y2="{f(py - 3.5)}" class="d-tick"/>')
    C.text(x, (miny + maxy) / 2, f"{maxy - miny:.1f} m".replace(".", ","), "d-t", dy=-5, rot=-90)


def _north(C):
    x, y = C.P(C.x1 - 0.9, C.y0 + 1.0)
    C.el.append(f'<g transform="translate({f(x)},{f(y)})"><circle r="13" class="na-c"/><polygon points="0,-11 4.5,5 0,1.5 -4.5,5" class="na-p"/>'
                f'<text y="-17" text-anchor="middle" class="t-label">N</text></g>')


def _scalebar(C):
    x, y = C.P(C.x1 - 5.8, C.y1 - 0.55)
    s = S
    g = [f'<g transform="translate({f(x)},{f(y)})">']
    for i in range(5):
        g.append(f'<rect x="{f(i * s)}" y="0" width="{f(s)}" height="4" class="{"sb-a" if i % 2 == 0 else "sb-b"}"/>')
    for i in (0, 1, 5):
        g.append(f'<text x="{f(i * s)}" y="15" text-anchor="middle" class="d-t">{i}</text>')
    g.append(f'<text x="{f(5 * s + 9)}" y="5" class="d-t">m</text></g>')
    C.el.append("".join(g))


# ----------------------------------------------------------------- rzut dachu
def plan_roof(house, uid):
    C = Canvas(house, uid, extra=_site_extent(house))
    site = Polygon([(C.x0, C.y0), (C.x1, C.y0), (C.x1, C.y1), (C.x0, C.y1)])
    C.path(site, "", f'fill="url(#{C.pattern("trawa")})"')
    for s_ in house.site:
        if s_["t"] == "path":
            C.path(s_["shape"], "pl-path")
    _site_trees(C, house)
    # tarasy na gruncie
    for r in house.all_rooms:
        if r.outdoor and r.level == min(house.L) and r.roof == "none":
            C.path(r.poly, "", f'fill="url(#{C.pattern("deska", _room_angle(r))})"')
    # dachy od najniższego
    for z, poly, fin, li in sorted(house.roofs, key=lambda t: t[0]):
        C.path(poly, "pl-roofshadow", 'transform="translate(5,6)"')
        C.path(poly, "", f'fill="url(#{C.pattern(fin if fin in ("sedum", "zwir") else "zwir")})"')
        C.path(poly, "pl-parapet")
        inner = poly.buffer(-0.25, join_style="mitre")
        if not inner.is_empty:
            C.path(inner, "pl-parapet-in")
        c = poly.representative_point()
        C.text(c.x, c.y, f"+{z:.2f}".replace(".", ","), "t-lvl")
    for r in house.all_rooms:
        if r.outdoor and r.level > min(house.L):
            C.path(r.poly, "", f'fill="url(#{C.pattern("deska", _room_angle(r))})"')
            C.path(r.poly, "pl-parapet")
            p = r.poly.representative_point()
            C.text(p.x, p.y, r.name, "t-room-s")
        if r.outdoor and isinstance(r.roof, Polygon) and r.parent is None:
            C.path(r.roof, "pl-roofpatio")
        if r.outdoor and r.roof == "full":
            rp = r.poly.representative_point()
            above = any(o.level > r.level and o.kind not in ("void", "ogrod_void") and o.poly.contains(rp)
                        for o in house.all_rooms)
            if not above:
                C.path(r.poly, "pl-roofpatio")
    # dach szklany
    for g in [r for r in house.all_rooms if r.kind == "ogrod"]:
        _glass_roof_svg(C, g)
    _north(C)
    _scalebar(C)
    C.text(C.x0 + 0.3, C.y1 + 0.35, "RZUT DACHU", "t-sheet", anchor="start")
    return C.render(f"{house.name} – rzut dachu")


def _glass_roof_svg(C, g, label=True):
    poly = g.poly
    C.path(poly, "gr-glass")
    cx, cy, ang, L, W = frame(poly)
    t = g.roof_type
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    vx, vy = -uy, ux
    if t in ("slide", "fold", "louvre", "ridge", "vault"):
        n = max(3, int(L / 1.2))
        for i in range(1, n):
            u = -L / 2 + L * i / n
            p1 = (cx + ux * u - vx * W, cy + uy * u - vy * W)
            p2 = (cx + ux * u + vx * W, cy + uy * u + vy * W)
            ln = LineString([p1, p2]).intersection(poly)
            for sg in _segs(ln):
                C.pline(list(sg.coords), "gr-mullion")
        if t in ("ridge", "vault"):
            ln = LineString([(cx - ux * L, cy - uy * L), (cx + ux * L, cy + uy * L)]).intersection(poly)
            for sg in _segs(ln):
                C.pline(list(sg.coords), "gr-ridge")
        if t in ("slide", "fold"):
            # połowa otwarta: przesunięte panele
            half = Polygon([(cx - ux * L / 2 - vx * W / 2, cy - uy * L / 2 - vy * W / 2),
                            (cx - vx * W / 2, cy - vy * W / 2), (cx + vx * W / 2, cy + vy * W / 2),
                            (cx - ux * L / 2 + vx * W / 2, cy - uy * L / 2 + vy * W / 2)]).intersection(poly)
            C.path(half, "gr-open")
            p1 = (cx - ux * L * 0.32, cy - uy * L * 0.32)
            p2 = (cx + ux * L * 0.05, cy + uy * L * 0.05)
            C.line(p1, p2, "gr-arrow")
            _arrowhead(C, p1, p2)
        if t == "louvre":
            for i in range(int(W / 0.3)):
                v = -W / 2 + 0.15 + i * 0.3
                p1 = (cx + vx * v - ux * L, cy + vy * v - uy * L)
                p2 = (cx + vx * v + ux * L, cy + vy * v + uy * L)
                ln = LineString([p1, p2]).intersection(poly)
                for sg in _segs(ln):
                    C.pline(list(sg.coords), "gr-lamella")
    elif t in ("pyramid", "iris"):
        c = poly.centroid
        for p in list(poly.exterior.coords)[:-1]:
            C.line((c.x, c.y), p, "gr-mullion")
        rr = math.sqrt(poly.area / math.pi) * 0.33
        C.path(Point(c.x, c.y).buffer(rr, 48 if t == "iris" else 4), "gr-open")
        if t == "iris":
            for i in range(10):
                aa = 2 * math.pi * i / 10
                C.line((c.x + rr * math.cos(aa), c.y + rr * math.sin(aa)), (c.x + rr * 1.7 * math.cos(aa + 0.5), c.y + rr * 1.7 * math.sin(aa + 0.5)), "gr-mullion")
    if label:
        p = poly.representative_point()
        C.text(p.x, p.y + 0.6, "dach szklany otwierany", "t-void")
