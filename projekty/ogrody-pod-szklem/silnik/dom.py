"""Model domu: pokoje jako wielokąty (oś ścian), z których silnik sam wylicza ściany,
okna, drzwi, stropy i dachy.

Szybki przykład::

    H = House("p00", "Przykład", "Dom testowy")
    H.level(0, z=0.0, h=3.3)
    H.ogrod("og", "Ogród zimowy", rect(6, 6, 14, 14), roof="slide")
    H.room("sal", "Salon z kuchnią", "salon_kuchnia", rect(0, 14, 20, 20), levels=2, ext={"S": "glass_slide"})
    H.connect("sal", "bib", "wide")
    H.entrance("hol", "N")
    H.build()
"""
import math

from shapely.geometry import Polygon, LineString, Point, MultiLineString
from shapely.geometry.polygon import orient
from shapely.ops import unary_union, linemerge

from .geom import ang_diff, dir_angle, largest, polygons, circle, rect

# grubości ścian [m]
THICK = {"ext": 0.40, "int": 0.12, "glass": 0.12, "fold": 0.12, "gwall": 0.30,
         "railing": 0.05, "low": 0.25, "columns": 0.0}
SLAB = 0.30

OUTDOOR = {"patio", "patio_sezonowe", "taras", "loggia"}
SPECIAL = {"ogrod", "void", "ogrod_void"}

# domyślne wykończenia podłóg
FLOOR = {
    "lazienka": "kamien", "wc": "kamien", "pralnia": "kamien", "spizarnia": "kamien", "wiatrolap": "kamien",
    "techniczne": "beton", "garaz": "beton", "sauna": "drewno_ciemne", "warsztat": "beton",
    "oranzeria": "terakota", "patio": "deska", "patio_sezonowe": "deska", "taras": "deska", "loggia": "deska",
    "herbaciarnia": "tatami", "galeria": "kamien", "korytarz": "kamien", "hol": "kamien", "winiarnia": "cegla",
}

# domyślna elewacja zewnętrzna i strona ogrodowa wg typu pokoju
EXT_DEFAULT = {"lazienka": "band_high", "wc": "band_high", "garderoba": "band_high", "pralnia": "windows_sq",
               "spizarnia": "solid", "techniczne": "solid", "sauna": "windows_sq", "winiarnia": "solid",
               "kino": "solid", "garaz": "solid"}
GARDEN_DEFAULT = {"lazienka": "glass", "wc": "band_high", "garderoba": "band_high", "pralnia": "windows",
                  "spizarnia": "band_high", "techniczne": "solid", "kino": "solid", "sauna": "glass",
                  "winiarnia": "glass"}

# okna: (szerokość, parapet, nadproże, rozstaw)
WIN = {
    "windows": (1.4, 0.9, 2.4, 3.2),
    "windows_sq": (1.0, 1.2, 2.2, 2.6),
    "slits": (0.45, 0.1, 2.6, 1.4),
    "band": (None, 1.0, 2.2, None),
    "band_high": (None, 1.8, 2.45, None),
}
DOOR_W = {"door": 0.9, "double": 1.6, "slide": 1.4, "wide": 2.0, "arch": 1.2, "portal": 3.0, "pivot": 1.2}


class Level:
    def __init__(self, idx, z, h, name):
        self.idx, self.z, self.h, self.name = idx, z, h, name


class Room:
    def __init__(self, house, key, name, kind, shape, level=0, levels=1, dz=0.0, ext=None, garden=None,
                 floor=None, label_at=None, furn=True, roof=None, enclose=None, garden_door=None, area=True,
                 height=None, note=None, parent=None, kitchen_at=None, focus=None, seed=0):
        self.house = house
        self.key, self.name, self.kind = key, name, kind
        self.poly = orient(shape.buffer(0) if not shape.is_valid else shape, 1.0)
        self.level, self.levels, self.dz = level, levels, dz
        self.outdoor = kind in OUTDOOR
        self.ext = ext if ext is not None else EXT_DEFAULT.get(kind, "open" if self.outdoor else "windows")
        self.garden = garden if garden is not None else GARDEN_DEFAULT.get(kind, "glass_slide")
        self.floor = floor or FLOOR.get(kind, "drewno")
        self.label_at = label_at
        self.furn = furn
        self.roof = roof if roof is not None else ("full" if kind in ("patio_sezonowe", "loggia") else "none")
        self.enclose = enclose if enclose is not None else ("fold" if kind == "patio_sezonowe" else None)
        self.garden_door = garden_door if garden_door is not None else kind not in (
            "lazienka", "wc", "garderoba", "pralnia", "spizarnia", "techniczne", "kino", "sauna")
        self.count_area = area and kind not in SPECIAL
        self.height = height
        self.note = note
        self.parent = parent
        self.kitchen_at = kitchen_at
        self.focus = focus
        self.seed = seed
        self.net = None

    # wysokości bezwzględne
    @property
    def z0(self):
        return self.house.levels[self.level].z + self.dz

    @property
    def top(self):
        """Spód stropu / dachu nad pokojem."""
        if self.height is not None:
            return self.z0 + self.height
        last = self.house.levels[self.level + self.levels - 1] if (self.level + self.levels - 1) in self.house.levels else None
        if last is None:
            L = self.house.levels[self.level]
            return L.z + L.h * self.levels - SLAB
        return last.z + last.h - SLAB

    def ext_for(self, angle):
        return _spec_for(self.ext, angle)

    def garden_for(self, angle):
        return _spec_for(self.garden, angle)

    def __repr__(self):
        return f"<Room {self.key} {self.kind} L{self.level}>"


def _spec_for(spec, angle):
    if isinstance(spec, str):
        return spec
    best, bd = spec.get("*", "windows"), 999
    for k, v in spec.items():
        if k == "*":
            continue
        d = ang_diff(angle, dir_angle(k))
        if d < bd and d <= 50:
            best, bd = v, d
    return best


class Garden(Room):
    def __init__(self, house, key, name, shape, level=0, levels=1, roof_type="slide", roof_z=None, style="japonski",
                 edge="glass", seed=1, trees=None, label_at=None, open_frac=0.5, plants=None):
        super().__init__(house, key, name, "ogrod", shape, level=level, levels=levels, ext=edge, floor="ogrod",
                         label_at=label_at, furn=True)
        self.roof_type, self._roof_z, self.style = roof_type, roof_z, style
        self.edge = edge
        self.seed = seed
        self.trees = trees
        self.open_frac = open_frac
        self.plants = plants

    @property
    def roof_z(self):
        if self._roof_z is not None:
            return self._roof_z
        last = self.house.levels[self.level + self.levels - 1]
        return last.z + last.h + 0.25


class Run:
    """Odcinek granicy pokoju o jednym sąsiedzie (prosty lub łukowy)."""

    def __init__(self, room, other, pts):
        self.room, self.other, self.pts = room, other, pts
        self.line = LineString(pts)
        self.length = self.line.length
        a, b = pts[0], pts[-1]
        dx, dy = b[0] - a[0], b[1] - a[1]
        if math.hypot(dx, dy) < 1e-9:
            dx, dy = pts[1][0] - a[0], pts[1][1] - a[1]
        L = math.hypot(dx, dy)
        # pierścień CCW (w liczbach) → wnętrze po lewej, na zewnątrz po prawej: (dy, -dx)
        self.normal = (dy / L, -dx / L)
        self.angle = math.degrees(math.atan2(self.normal[1], self.normal[0])) % 360
        self.straight = len(pts) == 2
        self.cls = None
        self.spec = None
        self.owner = None
        self.z0 = self.z1 = 0.0

    def point_at(self, s):
        p = self.line.interpolate(max(0.0, min(self.length, s)))
        return (p.x, p.y)

    def key(self):
        a = tuple(round(c, 3) for c in self.pts[0])
        b = tuple(round(c, 3) for c in self.pts[-1])
        ids = sorted([id(self.room), id(self.other) if self.other else 0])
        return (tuple(ids), tuple(sorted([a, b])), round(self.length, 3))


class Opening:
    def __init__(self, kind, level, a, b, t, z_floor, sill, head, run, into=None, hinge="a", cls="ext", label=None):
        self.kind, self.level, self.a, self.b, self.t = kind, level, a, b, t
        self.z_floor, self.sill, self.head = z_floor, sill, head
        self.run, self.into, self.hinge, self.cls = run, into, hinge, cls
        self.label = label

    @property
    def width(self):
        return math.hypot(self.b[0] - self.a[0], self.b[1] - self.a[1])

    def footprint(self, extra=0.012):
        return LineString([self.a, self.b]).buffer(self.t / 2 + extra, cap_style="flat")


class Stair:
    def __init__(self, kind, level, to_level, **p):
        self.kind, self.level, self.to_level, self.p = kind, level, to_level, p

    def flights(self, house):
        """Biegi schodów prostych i U: ([(prostokąt, kierunek, z_dół, z_góra)], (prostokąt spocznika, z) | None)."""
        z0 = house.levels[self.level].z
        z1 = house.levels[self.to_level].z if self.to_level in house.levels else z0 + 3.0
        x1, y1, x2, y2 = self.p["rect"]
        up = self.p.get("up", "E")
        land = self.p.get("landing", 1.1)
        if self.kind != "U":
            return [((x1, y1, x2, y2), up, z0, z1)], None
        zm = (z0 + z1) / 2
        if up in ("E", "W"):
            ym = (y1 + y2) / 2
            if up == "E":
                fl = [((x1, y1, x2 - land, ym - 0.05), "E"), ((x1, ym + 0.05, x2 - land, y2), "W")]
                lp = (x2 - land, y1, x2, y2)
            else:
                fl = [((x1 + land, y1, x2, ym - 0.05), "W"), ((x1 + land, ym + 0.05, x2, y2), "E")]
                lp = (x1, y1, x1 + land, y2)
        else:
            xm = (x1 + x2) / 2
            if up == "S":
                fl = [((x1, y1, xm - 0.05, y2 - land), "S"), ((xm + 0.05, y1, x2, y2 - land), "N")]
                lp = (x1, y2 - land, x2, y2)
            else:
                fl = [((x1, y1 + land, xm - 0.05, y2), "N"), ((xm + 0.05, y1 + land, x2, y2), "S")]
                lp = (x1, y1, x2, y1 + land)
        return [(fl[0][0], fl[0][1], z0, zm), (fl[1][0], fl[1][1], zm, z1)], (lp, zm)

    def footprint(self):
        if self.kind == "spiral":
            cx, cy = self.p["center"]
            return circle(cx, cy, self.p.get("r", 1.0) + 0.05)
        x1, y1, x2, y2 = self.p["rect"]
        return rect(x1, y1, x2, y2)


class House:
    def __init__(self, pid, name, tagline, style=None, concept=None, notes=None):
        self.pid, self.name, self.tagline = pid, name, tagline
        self.style = dict(fasada="tynk", rama="ciemna", dach="sedum", akcent=None)
        self.style.update(style or {})
        self.concept = concept or []
        self.notes = notes or {}
        self.levels = {}
        self.rooms = []
        self.connects, self.entrances, self.exits, self.windows, self.stairs = [], [], [], [], []
        self.site = []          # elementy terenu: ścieżki, tarasy na gruncie, drzewa
        self.cuts = []          # przekroje: (nazwa, (x1,y1), (x2,y2))
        self.built = False

    # ------------------------------------------------------------- definicja
    def level(self, idx, z, h=3.3, name=None):
        names = {0: "Parter", 1: "Piętro", 2: "II piętro", 3: "III piętro", -1: "Piwnica"}
        self.levels[idx] = Level(idx, z, h, name or names.get(idx, f"Poziom {idx}"))
        return self.levels[idx]

    def room(self, key, name, kind, shape, **kw):
        r = Room(self, key, name, kind, shape, **kw)
        self.rooms.append(r)
        return r

    def ogrod(self, key, name, shape, **kw):
        g = Garden(self, key, name, shape, **kw)
        self.rooms.append(g)
        return g

    def connect(self, a, b, kind="door", at=0.5, width=None):
        self.connects.append(dict(a=a, b=b, kind=kind, at=at, width=width))

    def entrance(self, room, direction, at=0.5, width=1.1, kind="pivot"):
        self.entrances.append(dict(room=room, dir=direction, at=at, width=width, kind=kind))

    def exit(self, room, direction, at=0.5, width=None, kind="slide"):
        self.exits.append(dict(room=room, dir=direction, at=at, width=width, kind=kind))

    def window(self, room, direction, at=0.5, width=1.2, sill=0.9, head=2.4, kind="win"):
        self.windows.append(dict(room=room, dir=direction, at=at, width=width, sill=sill, head=head, kind=kind))

    def stair(self, kind, level=0, to_level=None, **p):
        s = Stair(kind, level, level + 1 if to_level is None else to_level, **p)
        self.stairs.append(s)
        return s

    def path(self, shape, kind="kamien"):
        """Ścieżka / taras na gruncie poza budynkiem."""
        self.site.append(dict(t="path", shape=shape, kind=kind))

    def tree(self, x, y, kind="klon", r=None, h=None):
        self.site.append(dict(t="tree", x=x, y=y, kind=kind, r=r, h=h))

    def cut(self, name, a, b):
        """Linia przekroju (patrzymy w lewo od kierunku a→b)."""
        self.cuts.append((name, a, b))

    def get(self, key):
        for r in self.rooms:
            if r.key == key:
                return r
        raise KeyError(f"{self.pid}: brak pomieszczenia '{key}'")

    # ----------------------------------------------------------------- budowa
    def build(self):
        self.all_rooms = list(self.rooms)
        self.warnings = []
        # pustki nad pomieszczeniami wielokondygnacyjnymi
        for r in list(self.rooms):
            for i in range(1, r.levels):
                if r.level + i not in self.levels:
                    self.warnings.append(f"{r.key}: brak poziomu {r.level + i}")
                    continue
                kind = "ogrod_void" if r.kind == "ogrod" else "void"
                v = Room(self, f"{r.key}~{i}", r.name, kind, r.poly, level=r.level + i, ext=r.ext, garden=r.garden,
                         furn=False, parent=r, area=False)
                v.enclose = r.enclose
                self.all_rooms.append(v)
        self.L = {}
        for idx in sorted(self.levels):
            rooms = [r for r in self.all_rooms if r.level == idx]
            if rooms:
                self.L[idx] = self._build_level(idx, rooms)
        self._stairs()
        self._slabs()
        self._areas()
        self.built = True
        return self

    def _effective(self, r):
        return r.parent if r.parent is not None else r

    def _build_level(self, idx, rooms):
        lev = self.levels[idx]
        rings = _densify(rooms)
        emap = {}
        for r in rooms:
            ring = rings[r.key]
            n = len(ring)
            for i in range(n):
                a, b = ring[i], ring[(i + 1) % n]
                k = _ekey(a, b)
                emap.setdefault(k, []).append(r)
        # przebiegi (runs) dla każdego pokoju
        runs = []
        for r in rooms:
            ring = rings[r.key]
            n = len(ring)
            seg = []
            for i in range(n):
                a, b = ring[i], ring[(i + 1) % n]
                owners = emap[_ekey(a, b)]
                others = [o for o in owners if o is not r]
                if len(others) > 1:
                    self.warnings.append(f"L{idx}: krawędź wspólna dla >2 pomieszczeń przy {r.key}")
                seg.append((a, b, others[0] if others else None))
            runs.extend(_merge_runs(r, seg))
        # klasyfikacja przebiegów
        conn = {}
        for c in self.connects:
            conn[(c["a"], c["b"])] = c
            conn[(c["b"], c["a"])] = c
        walls = []
        seen = set()
        for run in runs:
            A, B = run.room, run.other
            key = run.key()
            twin = key in seen
            seen.add(key)
            cls, spec, owner = self._classify(A, B, run, conn)
            run.cls, run.spec, run.owner = cls, spec, owner
            run.twin = twin
            floors = [A.z0] + ([B.z0] if B is not None else [])
            tops = [A.top if not A.outdoor else A.z0 + 2.6] + ([B.top if not B.outdoor else B.z0 + 2.6] if B is not None else [])
            run.z0 = min(floors)
            cap = lev.z + lev.h
            for rr in (A, B):
                if rr is not None and rr.height is not None:
                    cap = max(cap, rr.z0 + rr.height + SLAB)
            run.z1 = min(max(tops) + SLAB, cap) if cls not in ("railing", "low", "gwall") else run.z0 + (1.05 if cls == "railing" else 1.0)
            if cls == "gwall":
                run.z1 = run.z0 + 2.6
            if not twin and cls is not None:
                walls.append(run)
        out = dict(level=lev, rooms=rooms, runs=runs, walls=walls, openings=[], rings=rings)
        self._openings(idx, out, conn)
        self._wall_geometry(out)
        for r in rooms:
            net = r.poly.difference(out["wall_union"]) if not out["wall_union"].is_empty else r.poly
            r.net = largest(net.buffer(0)) or r.poly
        return out

    def _classify(self, A, B, run, conn):
        """Zwraca (klasa ściany, specyfikacja, właściciel specyfikacji)."""
        EA, EB = self._effective(A), self._effective(B) if B is not None else None
        kA = A.kind
        kB = B.kind if B is not None else None

        def is_garden(r):
            return r is not None and r.kind in ("ogrod", "ogrod_void")

        def indoor(r):
            return r is not None and not r.outdoor and r.kind not in ("ogrod", "ogrod_void")

        # jawne połączenie ma pierwszeństwo
        c = None
        if B is not None:
            c = conn.get((EA.key, EB.key))
        if c is not None:
            k = c["kind"]
            if k == "open":
                return None, "open", EA
            if k in ("glass", "glass_slide"):
                return "glass", "glass_slide" if k == "glass_slide" else "glass", EA
            if k == "fold":
                return "fold", "fold", EA
            if k == "railing":
                return "railing", "railing", EA
            if k == "columns":
                return "columns", "columns", EA
            if indoor(A) and indoor(B):
                return "int", "wall", EA
            # połączenia z ogrodem / zewnętrzem – ściana wg specyfikacji pomieszczenia
        # wnętrze ↔ ogród
        if indoor(A) and is_garden(B) or indoor(B) and is_garden(A):
            r = EA if indoor(A) else EB
            ang = run.angle if indoor(A) else (run.angle + 180) % 360
            return _cls_of(r.garden_for(ang)), r.garden_for(ang), r
        # wnętrze ↔ wnętrze
        if indoor(A) and indoor(B):
            if EA is EB:
                return None, "open", EA
            if A.kind == "void" and B.kind == "void":
                return "int", "wall", EA
            return "int", "wall", EA
        # wnętrze ↔ zewnątrz lub pomieszczenie otwarte (patio, taras)
        if indoor(A) and (B is None or B.outdoor) or indoor(B) and A.outdoor:
            r = EA if indoor(A) else EB
            ang = run.angle if indoor(A) else (run.angle + 180) % 360
            sp = r.ext_for(ang)
            if B is not None and B.outdoor and indoor(A) and sp in ("windows", "windows_sq", "slits", "band", "band_high", "solid"):
                sp = sp  # zostaw wybór projektanta
            return _cls_of(sp), sp, r
        # ogród ↔ zewnątrz / patio
        if is_garden(A) and (B is None or B.outdoor) or is_garden(B) and A.outdoor:
            g = EA if is_garden(A) else EB
            sp = g.ext if isinstance(g.ext, str) else _spec_for(g.ext, run.angle)
            return _cls_of(sp), sp, g
        if is_garden(A) and is_garden(B):
            return None, "open", EA
        # pomieszczenia otwarte
        if A.outdoor and (B is None or B.outdoor):
            if B is not None:
                return None, "open", EA
            sp = A.enclose
            if sp is None and A.level > 0:
                sp = "railing"
            if sp is None:
                return None, "open", EA
            return _cls_of(sp), sp, EA
        return None, "open", EA

    def _openings(self, idx, out, conn):
        lev = out["level"]
        ops = out["openings"]
        runs = [r for r in out["runs"] if not r.twin and r.cls is not None]
        allruns = out["runs"]

        def add(kind, run, s1, s2, sill=0.0, head=2.25, into=None, cls=None, label=None):
            s1, s2 = max(0.0, s1), min(run.length, s2)
            if s2 - s1 < 0.3:
                return
            # na łukach długie otwory dzielimy na krótkie cięciwy
            if not run.straight and kind in ("win", "band", "slide") and s2 - s1 > 1.1:
                k = int(math.ceil((s2 - s1) / 0.9))
                for i in range(k):
                    add(kind if kind != "slide" else "slide", run, s1 + (s2 - s1) * i / k, s1 + (s2 - s1) * (i + 1) / k,
                        sill, head, into, cls, label if i == 0 else None)
                return
            a, b = run.point_at(s1), run.point_at(s2)
            t = THICK.get(run.cls, 0.12)
            hinge = "a" if (s1 + s2) / 2 < run.length / 2 else "b"
            zf = max(run.room.z0, run.other.z0) if run.other is not None else run.room.z0
            ops.append(Opening(kind, idx, a, b, t, zf, sill, head, run, into=into, hinge=hinge, cls=cls or run.cls, label=label))

        # okna wg specyfikacji elewacji
        for run in runs:
            sp = run.spec
            if run.cls != "ext" and not (run.cls == "int" and False):
                if run.cls in ("glass", "fold"):
                    if sp in ("glass_slide",) and run.length >= 2.0:
                        if run.owner is not None and run.owner.kind in ("ogrod", "ogrod_void"):
                            continue
                        owner_room = run.owner
                        if owner_room is not None and owner_room.kind == "void":
                            continue
                        if run.other is not None and run.other.kind in ("ogrod", "ogrod_void") and not run.owner.garden_door:
                            continue
                        # piętro: drzwi tylko na taras/patio albo do ogrodu, nie w powietrze
                        if run.other is None and idx > min(self.levels):
                            continue
                        if run.other is not None and run.other.kind == "ogrod_void":
                            continue
                        w = min(3.0, max(1.6, 0.45 * run.length))
                        m = run.length / 2
                        add("slide", run, m - w / 2, m + w / 2, 0, 2.6)
                continue
            if sp in WIN:
                w, sill, head, spacing = WIN[sp]
                L = run.length
                if w is None:  # wstęga
                    if L >= 1.8:
                        add("band", run, 0.5, L - 0.5, sill, head)
                    continue
                if L < w + 0.6:
                    continue
                n = max(1, int((L + 0.4) // spacing))
                for i in range(n):
                    c = L * (i + 0.5) / n
                    add("win", run, c - w / 2, c + w / 2, sill, head)
        # połączenia drzwiowe
        for c in self.connects:
            k = c["kind"]
            if k in ("open", "glass", "railing", "fold", "columns"):
                if k == "glass":
                    cand = [r for r in _runs_between(allruns, c["a"], c["b"], self)
                            if r.room.kind not in ("void", "ogrod_void") and r.other.kind not in ("void", "ogrod_void")]
                    if cand:
                        run = max(cand, key=lambda r: r.length)
                        w = c["width"] or 0.9
                        m = run.length * c["at"]
                        add("door", run, m - w / 2, m + w / 2, 0, 2.25, into=c["b"], cls="glass")
                continue
            cand = _runs_between(allruns, c["a"], c["b"], self)
            # drzwi tylko między prawdziwymi podłogami (nie w pustkach nad salonem / ogrodem)
            cand = [r for r in cand if r.cls is not None and r.room.kind not in ("void", "ogrod_void")
                    and r.other.kind not in ("void", "ogrod_void")]
            if not cand:
                continue
            run = max(cand, key=lambda r: r.length)
            w = c["width"] or DOOR_W.get(k, 0.9)
            w = min(w, run.length - 0.3)
            m = run.length * c["at"] if c["at"] <= 1 else c["at"]
            m = max(w / 2 + 0.12, min(run.length - w / 2 - 0.12, m))
            into = c["b"]
            add(k, run, m - w / 2, m + w / 2, 0, 2.25 if k not in ("wide", "portal", "arch") else 2.6, into=into)
        # wejścia i wyjścia
        for e in self.entrances + self.exits:
            r = self.get(e["room"])
            if r.level != idx:
                continue
            run = _pick_ext_run(allruns, r, e["dir"])
            if run is None:
                self.warnings.append(f"{e['room']}: brak ściany zewnętrznej w kierunku {e['dir']}")
                continue
            w = e["width"] or (2.4 if e["kind"] == "slide" else 1.0)
            w = min(w, run.length - 0.3)
            m = run.length * e["at"]
            m = max(w / 2 + 0.12, min(run.length - w / 2 - 0.12, m))
            # usuń kolidujące okna
            ops[:] = [o for o in ops if not (o.run is run and _overlap(o, run, m - w / 2 - 0.3, m + w / 2 + 0.3))]
            add(e["kind"], run, m - w / 2, m + w / 2, 0, 2.6 if e["kind"] == "slide" else 2.4, into=r.key,
                label="wejście" if e in self.entrances else None)
        # okna jawne
        for wspec in self.windows:
            r = self.get(wspec["room"])
            if r.level != idx:
                continue
            run = _pick_ext_run(allruns, r, wspec["dir"])
            if run is None:
                continue
            m = run.length * wspec["at"]
            w = wspec["width"]
            ops[:] = [o for o in ops if not (o.run is run and o.kind in ("win", "band") and _overlap(o, run, m - w / 2 - 0.2, m + w / 2 + 0.2))]
            add(wspec["kind"], run, m - w / 2, m + w / 2, wspec["sill"], wspec["head"])

    def _wall_geometry(self, out):
        by = {}
        for run in out["walls"]:
            by.setdefault(run.cls, []).append(run.line)
        geoms = {}
        for cls, lines in by.items():
            t = THICK.get(cls, 0.12)
            if t <= 0:
                continue
            merged = linemerge(MultiLineString([list(l.coords) for l in lines])) if len(lines) > 1 else lines[0]
            cap = "square" if cls == "ext" else "flat"
            g = merged.buffer(t / 2, cap_style=cap, join_style="mitre", mitre_limit=4.0)
            geoms[cls] = g
        # wycięcia otworów w ścianach pełnych
        cut = {}
        for o in out["openings"]:
            if o.cls in ("ext", "int", "gwall", "low"):
                cut.setdefault(o.cls, []).append(o.footprint())
        solid = {}
        for cls, g in geoms.items():
            if cls in cut:
                g = g.difference(unary_union(cut[cls]))
            solid[cls] = g
        # pełne ściany przykrywają szkło (słupki w narożnikach)
        if "glass" in solid and "ext" in solid:
            solid["glass"] = solid["glass"].difference(geoms["ext"])
        if "glass" in solid and "int" in solid:
            solid["glass"] = solid["glass"].difference(geoms["int"])
        out["wall_geoms"] = geoms
        out["wall_solid"] = solid
        out["wall_union"] = unary_union([g for c, g in geoms.items() if c not in ("railing",)]) if geoms else Polygon()

    def _stairs(self):
        self.voids = {}
        for s in self.stairs:
            fp = s.footprint()
            self.voids.setdefault(s.to_level, []).append((fp, s))
        for idx, L in self.L.items():
            L["stairs_here"] = [s for s in self.stairs if s.level == idx]
            L["voids"] = self.voids.get(idx, [])

    def _slabs(self):
        """Stropy, dachy i podstawa."""
        idxs = sorted(self.L)
        self.slabs = []   # (z_top, polygon, kind)
        self.roofs = []   # (z, polygon, finish)
        self.patio_roofs = []
        for i, idx in enumerate(idxs):
            L = self.L[idx]
            lev = self.levels[idx]
            indoor = [r for r in L["rooms"] if not r.outdoor and r.kind not in ("ogrod", "ogrod_void")]
            floor_rooms = [r for r in indoor if r.kind != "void"]
            terr = [r for r in L["rooms"] if r.outdoor]
            if idx == idxs[0]:
                base = unary_union([r.poly for r in floor_rooms + terr]) if floor_rooms else Polygon()
                L["base"] = base
            else:
                fl = unary_union([r.poly for r in floor_rooms + terr]) if floor_rooms + terr else Polygon()
                for fp, s in L["voids"]:
                    fl = fl.difference(fp)
                L["floor_slab"] = fl
                self.slabs.append((lev.z, fl, "strop"))
            # dach nad poziomem
            cover = unary_union([r.poly for r in indoor] + [r.poly for r in terr if r.roof == "full"]) if indoor else Polygon()
            nxt = self.L.get(idxs[i + 1]) if i + 1 < len(idxs) else None
            if nxt is not None:
                above = unary_union([r.poly for r in nxt["rooms"] if r.kind not in ("ogrod_void",)])
                cover = cover.difference(above)
            cover = cover.buffer(0)
            for p in polygons(cover):
                if p.area < 0.3:
                    continue
                self.roofs.append((lev.z + lev.h, p, self.style.get("dach", "sedum"), idx))
            for r in terr:
                if isinstance(r.roof, Polygon):
                    self.patio_roofs.append((r, r.roof))
        self.footprint = unary_union([r.poly for r in self.all_rooms if r.level == idxs[0]])

    def _areas(self):
        self.area = {"uzytkowa": 0.0, "ogrod": 0.0, "zewn": 0.0, "sezon": 0.0}
        self.room_areas = []
        for idx, L in self.L.items():
            for r in L["rooms"]:
                if r.parent is not None:
                    continue
                a = r.net.area if r.net is not None else r.poly.area
                if r.kind == "ogrod":
                    self.area["ogrod"] += a
                elif r.kind == "patio_sezonowe":
                    self.area["sezon"] += a
                elif r.outdoor:
                    self.area["zewn"] += a
                elif r.count_area:
                    # minus otwory schodowe nad pokojem
                    for fp, s in L.get("voids", []):
                        a -= r.net.intersection(fp).area if r.net is not None else 0
                    self.area["uzytkowa"] += a
                self.room_areas.append((idx, r, a))
        minx, miny, maxx, maxy = self.footprint.bounds
        self.bbox = (minx, miny, maxx, maxy)


# ------------------------------------------------------------------ pomocnicze
def _ekey(a, b):
    ka = (round(a[0], 4), round(a[1], 4))
    kb = (round(b[0], 4), round(b[1], 4))
    return (ka, kb) if ka <= kb else (kb, ka)


def _densify(rooms):
    """Wstawia w krawędzie wierzchołki innych pomieszczeń leżące na nich (styki typu T)."""
    allpts = []
    for r in rooms:
        allpts.extend(r.poly.exterior.coords[:-1])
    uniq = {}
    for p in allpts:
        uniq[(round(p[0], 5), round(p[1], 5))] = p
    pts = list(uniq.values())
    rings = {}
    for r in rooms:
        coords = list(r.poly.exterior.coords)[:-1]
        n = len(coords)
        new = []
        for i in range(n):
            a, b = coords[i], coords[(i + 1) % n]
            new.append(a)
            abx, aby = b[0] - a[0], b[1] - a[1]
            L2 = abx * abx + aby * aby
            if L2 < 1e-12:
                continue
            L = math.sqrt(L2)
            minx, maxx = min(a[0], b[0]) - 1e-3, max(a[0], b[0]) + 1e-3
            miny, maxy = min(a[1], b[1]) - 1e-3, max(a[1], b[1]) + 1e-3
            cand = []
            for p in pts:
                if p[0] < minx or p[0] > maxx or p[1] < miny or p[1] > maxy:
                    continue
                apx, apy = p[0] - a[0], p[1] - a[1]
                t = (apx * abx + apy * aby) / L2
                if 1e-6 < t < 1 - 1e-6 and abs(apx * aby - apy * abx) / L < 2e-3:
                    cand.append((t, p))
            cand.sort()
            for t, p in cand:
                if math.hypot(p[0] - new[-1][0], p[1] - new[-1][1]) > 1e-4:
                    new.append((a[0] + t * abx, a[1] + t * aby))
        rings[r.key] = new
    return rings


def _merge_runs(room, seg):
    """Łączy kolejne krawędzie o tym samym sąsiedzie i podobnym kierunku (łuki do 16°)."""
    n = len(seg)
    if n == 0:
        return []

    def ang(s):
        a, b, _ = s
        return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))

    def same(s1, s2):
        return s1[2] is s2[2] and ang_diff(ang(s1), ang(s2)) < 16.5

    start = 0
    for i in range(n):
        if not same(seg[i - 1], seg[i]):
            start = i
            break
    else:
        # cały obwód jednym ciągiem (np. okrąg) – podziel na ćwiartki
        start = 0
    order = seg[start:] + seg[:start]
    runs = []
    cur = [order[0]]
    for s in order[1:]:
        # nie łącz zbyt długich łuków (max 90°) – lepsze rozmieszczenie okien
        if same(cur[-1], s) and ang_diff(ang(cur[0]), ang(s)) < 80:
            cur.append(s)
        else:
            runs.append(cur)
            cur = [s]
    runs.append(cur)
    out = []
    for group in runs:
        pts = [group[0][0]] + [g[1] for g in group]
        out.append(Run(room, group[0][2], pts))
    return out


def _cls_of(spec):
    if spec in ("solid", "windows", "windows_sq", "slits", "band", "band_high", "wall"):
        return "ext"
    if spec in ("glass", "glass_slide"):
        return "glass"
    if spec == "fold":
        return "fold"
    if spec == "railing":
        return "railing"
    if spec == "low":
        return "low"
    if spec == "gwall":
        return "gwall"
    if spec == "columns":
        return "columns"
    return None


def _runs_between(runs, a, b, house):
    out = []
    for r in runs:
        if r.other is None or r.twin:
            continue
        ka = house._effective(r.room).key
        kb = house._effective(r.other).key
        if {ka, kb} == {a, b}:
            out.append(r)
    return out


def _pick_ext_run(runs, room, direction):
    ang = dir_angle(direction)
    best, bscore = None, None
    for r in runs:
        if r.room is not room or r.cls is None:
            continue
        if r.other is not None and not r.other.outdoor:
            continue
        d = ang_diff(r.angle, ang)
        if d > 60:
            continue
        score = (round(d / 10), -r.length)
        if bscore is None or score < bscore:
            best, bscore = r, score
    return best


def _overlap(o, run, s1, s2):
    pa = run.line.project(Point(o.a))
    pb = run.line.project(Point(o.b))
    lo, hi = min(pa, pb), max(pa, pb)
    return not (hi < s1 or lo > s2)
