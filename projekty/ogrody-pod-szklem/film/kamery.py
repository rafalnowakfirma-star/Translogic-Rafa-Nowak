"""Plan ujęć filmu: kamery dobierane automatycznie z modelu domu (współrzędne planu: x – wschód, y – południe).

Każde ujęcie: dict(id, scena, cam=dict(loc, target, lens, shift_y, poziom), podpis, podpis2, ruch, fokus, ekspo).
"scena" mówi, w której wersji sceny renderować: dzien (lato, dach otwarty), zmierzch, zima (śnieg).
"""
import math

from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union

from silnik.geom import largest

GLASS = ("glass", "fold")
STYL = {"japonski": "ogród japoński", "oranzeria": "oranżeria z cytrusami", "woda": "ogród wodny",
        "las": "leśny ogród z brzozami", "srodziemnomorski": "ogród śródziemnomorski", "tropikalny": "ogród tropikalny"}
DACH = {"slide": "dach przesuwny", "fold": "dach harmonijkowy", "louvre": "dach z obrotowych lameli",
        "pyramid": "szklana piramida z unoszoną latarnią", "iris": "szklana kopuła z unoszonym środkiem",
        "vault": "dach przesuwny", "ridge": "dach przesuwny"}


def _num(x):
    return f"{x:.0f}"


def _net(r):
    return r.net if r.net is not None else r.poly


def _items(H, r):
    out = []
    for L in H.L.values():
        for it in L.get("items") or []:
            if getattr(it, "room", None) is r:
                out.append(it)
    return out


def _blocked(H, r, pad=0.18, tall=None):
    fps = []
    for it in _items(H, r):
        if tall is not None and it.h < tall:
            continue
        if it.kind == "dywan":
            continue
        fps.append(it.footprint(pad=pad))
    return unary_union(fps) if fps else Polygon()


def _runs(H, r):
    L = H.L[r.level]
    return [run for run in L["runs"] if run.room is r]


def _seg_samples(run, n=9):
    return [run.point_at(run.length * (0.06 + 0.88 * i / (n - 1))) for i in range(n)]


def _hfov(lens):
    return 2 * math.atan(18.0 / lens)


def _best_view(space, free, targets, lens, min_d=2.2, block=None, step=0.22, prefer_wall=True, need=None):
    """Najlepsza para (punkt kamery w `free`, kierunek) widząca jak najwięcej celów (x, y, waga, grupa).
    need – minimalny udział wagi grupy "szklo" w kadrze (żeby okno/ogród był w ujęciu)."""
    if free.is_empty or not targets:
        return None
    minx, miny, maxx, maxy = free.bounds
    half = _hfov(lens) / 2 * 0.88
    nx = max(1, int((maxx - minx) / step))
    ny = max(1, int((maxy - miny) / step))
    bnd = space.boundary            # także MultiPolygon (rozłączne tarasy) i dziury (ogród w pierścieniu)
    sp = space.buffer(0.08)
    tot_glass = sum(t[2] for t in targets if t[3] == "szklo") or 1.0
    best = None
    for i in range(nx + 1):
        for j in range(ny + 1):
            x, y = minx + (maxx - minx) * i / nx, miny + (maxy - miny) * j / ny
            P = Point(x, y)
            if not free.contains(P):
                continue
            vis = []
            for (qx, qy, w, grp) in targets:
                d = math.hypot(qx - x, qy - y)
                if d < 0.8:
                    continue
                ln = LineString([(x, y), (qx, qy)])
                if not ln.within(sp):
                    continue
                if block is not None and not block.is_empty and grp == "szklo" and ln.intersects(block):
                    continue
                vis.append((math.atan2(qy - y, qx - x), w, grp, d))
            if not vis:
                continue
            for k in range(72):
                aim = 2 * math.pi * k / 72
                sc_, g_, dsum, wsum = 0.0, 0.0, 0.0, 0.0
                for (ang, w, grp, d) in vis:
                    da = (ang - aim + math.pi) % (2 * math.pi) - math.pi
                    if abs(da) <= half:
                        sc_ += w
                        dsum += d * w
                        wsum += w
                        if grp == "szklo":
                            g_ += w
                if wsum == 0:
                    continue
                if need is not None and g_ / tot_glass < need:
                    continue
                md = dsum / wsum
                if md < min_d:
                    continue
                # głębia kadru: jak daleko widać na wprost (unikamy patrzenia w bliską ścianę)
                ray = LineString([(x, y), (x + math.cos(aim) * 40, y + math.sin(aim) * 40)])
                hit = ray.intersection(bnd)
                depth = 40.0 if hit.is_empty else P.distance(hit)
                score = sc_ * min(1.6, md / 5.0) ** 0.6 * min(1.5, depth / 4.0) ** 0.5
                if prefer_wall:
                    score *= 1.0 + 0.3 * max(0.0, 1.0 - bnd.distance(P) / 1.2)
                if best is None or score > best[0]:
                    best = (score, (x, y), aim, g_ / tot_glass, md)
    return best


GLOWNE = {"sofa": 3.0, "stol": 3.0, "wyspa": 3.0, "lozko": 4.0, "biurko": 3.0, "biurko2": 3.0, "fotel": 1.5,
          "regal": 1.5, "fortepian": 3.0, "blat": 2.0, "kominek": 2.0, "wanna": 2.0, "czajnik": 2.0, "stolik": 1.0}


# --------------------------------------------------------------- ujęcia wnętrz
def ujecie_wnetrza(H, r, kind_cel, lens=17.0, h_eye=1.3, shift=0.06):
    """Kamera w pokoju r: w kadrze przeszklenie (kind_cel 'ogrod' – do ogrodu, 'zewn' – na zewnątrz) i główne meble."""
    space = _net(r)
    targets = []
    for run in _runs(H, r):
        o = run.other
        if run.cls not in GLASS:
            continue
        is_g = o is not None and o.kind in ("ogrod", "ogrod_void")
        if kind_cel == "ogrod" and not is_g:
            continue
        if kind_cel == "zewn" and is_g:
            continue
        for (x, y) in _seg_samples(run):
            targets.append((x, y, 1.0, "szklo"))
    if not targets:
        for run in _runs(H, r):
            if run.cls in GLASS:
                for (x, y) in _seg_samples(run):
                    targets.append((x, y, 1.0, "szklo"))
    if not targets:
        return None
    for it in _items(H, r):
        w = GLOWNE.get(it.kind)
        if w:
            targets.append((it.cx, it.cy, w, "mebel"))
    free = space.buffer(-0.35, join_style="mitre").difference(_blocked(H, r, pad=0.22))
    tall = _blocked(H, r, pad=0.0, tall=1.25)
    best = None
    for md in (2.6, 2.0, 1.4):
        for ln_ in (lens, lens + 3):
            b = _best_view(space, free, targets, ln_, min_d=md, block=tall, need=0.25)
            if b is not None and (best is None or b[0] > best[0][0] * 1.1):
                best = (b, ln_)
        if best is not None:
            break
    if best is None:
        return None
    (score, (cx, cy), aim, gfrac, md), lens = best
    hz = r.top - r.z0
    high = hz > 4.5
    tx, ty = cx + math.cos(aim) * 5, cy + math.sin(aim) * 5
    eye = h_eye + (0.15 if high else 0.0)
    return dict(loc=(cx, cy, r.z0 + eye), target=(tx, ty, r.z0 + eye), lens=lens,
                shift_y=shift + (0.06 if high else 0.0), poziom=True, score=round(score, 2), glass=round(gfrac, 2))


def ujecie_ogrodu(H, g, lens=17.0):
    space = _net(g)
    lay = getattr(g, "_layout", None) or {}
    feats = lay.get("features", [])
    obst = [Point(f.x, f.y).buffer(f.r + 0.3) for f in feats if f.t not in ("krok", "lilia", "mech")]
    water = [geom.buffer(0.1) for kind, geom in lay.get("floor", []) if kind == "woda"]
    free = space.buffer(-0.45, join_style="mitre").difference(unary_union(obst + water) if obst or water else Polygon())
    if free.is_empty:
        free = space.buffer(-0.3)
    targets = []
    for run in [r for r in H.L[g.level]["runs"] if r.room is g or getattr(r.room, "parent", None) is g]:
        for (x, y) in _seg_samples(run, 7):
            targets.append((x, y, 1.0, "szklo"))
    for f in feats:
        if f.t in ("klon", "brzoza", "oliwka", "sosna", "palma", "cytrus", "latarnia", "fontanna", "misa"):
            targets.append((f.x, f.y, 2.5, "mebel"))
    best = _best_view(space.buffer(0.3), free, targets, lens, min_d=1.8, prefer_wall=True)
    if best is None:
        c = space.centroid
        return dict(loc=(c.x, c.y, g.z0 + 1.5), target=(c.x + 1, c.y, g.z0 + 1.5), lens=lens, shift_y=0.16, poziom=True)
    _, (cx, cy), aim, gfrac, md = best
    # pień drzewa nie w samym środku kadru
    for f in feats:
        if f.t in ("klon", "brzoza", "oliwka", "sosna", "palma"):
            a = math.atan2(f.y - cy, f.x - cx)
            da = (a - aim + math.pi) % (2 * math.pi) - math.pi
            if abs(da) < math.radians(7):
                aim += math.radians(10) * (-1 if da > 0 else 1)
    tx, ty = cx + math.cos(aim) * 5, cy + math.sin(aim) * 5
    return dict(loc=(cx, cy, g.z0 + 1.5), target=(tx, ty, g.z0 + 1.5), lens=lens, shift_y=0.16, poziom=True)


def ujecie_tarasu(H, t, lens=20.0):
    space = _net(t)
    gs = [r for r in H.all_rooms if r.kind == "ogrod"]
    targets = []
    for g in gs:
        for (x, y) in list(g.poly.exterior.coords)[:-1]:
            targets.append((x, y, 1.0, "szklo"))
        c = g.poly.centroid
        targets.append((c.x, c.y, 3.0, "szklo"))
    for r in H.L[t.level]["rooms"]:
        if not r.outdoor and r.kind not in ("void", "ogrod_void"):
            c = _net(r).centroid
            targets.append((c.x, c.y, 1.5, "mebel"))
    if not targets:
        return None
    free = space.buffer(-0.35, join_style="mitre").difference(_blocked(H, t, pad=0.2))
    if free.is_empty:
        return None
    vis = unary_union([space] + [g.poly for g in gs] + [r.poly for r in H.L[t.level]["rooms"] if r.outdoor]).buffer(0.6)
    best = _best_view(vis, free, targets, lens, min_d=2.0, prefer_wall=False, need=0.3)
    if best is None:
        return None
    _, (cx, cy), aim, gfrac, md = best
    tx, ty = cx + math.cos(aim) * 5, cy + math.sin(aim) * 5
    return dict(loc=(cx, cy, t.z0 + 1.6), target=(tx, ty, t.z0 + 1.35), lens=lens, shift_y=0.02, poziom=True)


def ujecie_patio(H, p, lens=18.0):
    space = _net(p)
    targets = []
    for run in _runs(H, p):
        o = run.other
        if o is not None and not o.outdoor and run.cls in GLASS:
            for (x, y) in _seg_samples(run):
                targets.append((x, y, 1.0, "szklo"))
    if not targets:
        return None
    for it in _items(H, p):
        targets.append((it.cx, it.cy, 1.5, "mebel"))
    free = space.buffer(-0.4, join_style="mitre").difference(_blocked(H, p, pad=0.2))
    best = _best_view(space.buffer(0.2), free, targets, lens, min_d=2.5, need=0.3)
    if best is None:
        return None
    _, (cx, cy), aim, gfrac, md = best
    tx, ty = cx + math.cos(aim) * 5, cy + math.sin(aim) * 5
    return dict(loc=(cx, cy, p.z0 + 1.5), target=(tx, ty, p.z0 + 1.5), lens=lens, shift_y=0.1, poziom=True)


# --------------------------------------------------------------- ujęcia z zewnątrz
def _bryla_bbox(H):
    polys = [r.poly for r in H.all_rooms if r.kind not in ("void",)]
    u = unary_union(polys)
    return u.bounds


def _corners(H):
    minx, miny, maxx, maxy = _bryla_bbox(H)
    ztop = max(L["level"].z + L["level"].h for L in H.L.values()) + 0.5
    return [(x, y, z) for x in (minx, maxx) for y in (miny, maxy) for z in (-0.3, ztop)], ztop


def _fit_distance(H, phi, el, lens, fill=0.8, aspect=16 / 9, tz=None):
    """Odległość kamery (azymut phi w układzie planu, elewacja el), przy której bryła wypełnia kadr."""
    pts, ztop = _corners(H)
    minx, miny, maxx, maxy = _bryla_bbox(H)
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    tz = ztop * 0.32 if tz is None else tz
    fx = math.tan(_hfov(lens) / 2)
    fy = fx / aspect
    for d in [x * 0.5 for x in range(8, 400)]:
        ex = cx + d * math.cos(el) * math.cos(phi)
        ey = cy + d * math.cos(el) * math.sin(phi)
        ez = tz + d * math.sin(el)
        # baza kamery
        fwd = (cx - ex, cy - ey, tz - ez)
        L = math.sqrt(sum(c * c for c in fwd))
        fwd = tuple(c / L for c in fwd)
        right = (fwd[1], -fwd[0], 0.0)
        Lr = math.hypot(right[0], right[1])
        right = (right[0] / Lr, right[1] / Lr, 0.0)
        up = (right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2], right[0] * fwd[1] - right[1] * fwd[0])
        ok = True
        for (px, py, pz) in pts:
            v = (px - ex, py - ey, pz - ez)
            zc = sum(a * b for a, b in zip(v, fwd))
            if zc <= 0.1:
                ok = False
                break
            xc = sum(a * b for a, b in zip(v, right)) / zc
            yc = sum(a * b for a, b in zip(v, up)) / zc
            if abs(xc) > fx * fill or abs(yc) > fy * fill:
                ok = False
                break
        if ok:
            return d, (ex, ey, ez), (cx, cy, tz)
    return d, (ex, ey, ez), (cx, cy, tz)


def _bryly(H):
    """Bryły zasłaniające: (wielokąt, wysokość wierzchu) – pokoje z dachem/stropem i mury patio."""
    out = []
    for r in H.all_rooms:
        if r.parent is not None or r.kind in ("ogrod", "void", "ogrod_void"):
            continue
        if r.outdoor:
            if r.enclose in ("gwall", "solid", "wall"):
                out.append((r.poly.boundary.buffer(0.15), r.z0 + 2.6))
            continue
        out.append((r.poly, r.top + 0.75))
    return out


def widocznosc(H, cam, pts, bryly=None):
    """Udział punktów 3D widocznych z kamery (prosty test 2,5D: odcinek nie może przejść pod wierzchem bryły)."""
    bryly = bryly or _bryly(H)
    cx, cy, cz = cam
    ok = 0
    for (px, py, pz) in pts:
        seg = LineString([(px, py), (cx, cy)])
        L = seg.length or 1e-6
        vis = True
        for poly, zt in bryly:
            if zt <= pz + 0.05:
                continue
            inter = seg.intersection(poly)
            if inter.is_empty:
                continue
            # najniższy punkt odcinka nad bryłą to jego wejście nad bryłę (najbliżej celu)
            d = min(Point(px, py).distance(g) for g in getattr(inter, "geoms", [inter]))
            z = pz + (cz - pz) * d / L
            if z < zt:
                vis = False
                break
        ok += vis
    return ok / max(1, len(pts))


def ujecie_dachu(H, phi_pref, lens=35.0):
    """Kamera z góry, z której widać szklany dach ogrodu (animacja otwierania)."""
    gs = [r for r in H.all_rooms if r.kind == "ogrod"]
    if not gs:
        return None
    g = gs[0]
    pts = []
    for q in [g.poly.buffer(-0.4)] if not g.poly.buffer(-0.4).is_empty else [g.poly]:
        minx, miny, maxx, maxy = q.bounds
        for i in range(5):
            for j in range(5):
                P = Point(minx + (maxx - minx) * (i + 0.5) / 5, miny + (maxy - miny) * (j + 0.5) / 5)
                if q.contains(P):
                    pts.append((P.x, P.y, g.roof_z + 0.1))
    br = _bryly(H)
    best = None
    for el_d in (52, 60, 68):
        for k in range(24):
            phi = 2 * math.pi * k / 24
            d, loc, tgt = _fit_distance(H, phi, math.radians(el_d), lens, fill=0.82, tz=g.roof_z)
            v = widocznosc(H, loc, pts, br)
            dphi = abs((phi - phi_pref + math.pi) % (2 * math.pi) - math.pi)
            score = v - 0.08 * dphi - 0.002 * (el_d - 52)
            if best is None or score > best[0]:
                best = (score, v, loc, tgt, phi, el_d)
    _, v, loc, tgt, phi, el_d = best
    return dict(loc=loc, target=tgt, lens=lens, shift_y=0.0, poziom=False, widac=round(v, 2))


def _side_scores(H):
    """Atrakcyjność stron domu (szkło, tarasy, patio) dla 24 kierunków (kąt w układzie planu)."""
    minx, miny, maxx, maxy = H.bbox
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    out = []
    for k in range(24):
        phi = 2 * math.pi * k / 24
        dx, dy = math.cos(phi), math.sin(phi)
        s = 0.0
        for idx, L in H.L.items():
            for run in L["walls"]:
                if run.cls in GLASS and (run.other is None or run.other.outdoor):
                    nx, ny = run.normal
                    s += run.length * max(0.0, nx * dx + ny * dy) * (1.3 if idx > min(H.L) else 1.0)
        for r in H.all_rooms:
            if r.outdoor and r.parent is None:
                c = r.poly.centroid
                v = (c.x - cx, c.y - cy)
                Lv = math.hypot(*v) or 1.0
                s += 0.25 * r.poly.area * max(0.0, (v[0] * dx + v[1] * dy) / Lv) * (1.6 if r.level > min(H.L) else 1.0)
        out.append((s, phi))
    return out


def _sun_az(phi_cam, side=1):
    """Azymut słońca (od północy, zgodnie z zegarem) ~65° obok kierunku kamery – światło z boku, z przodu."""
    ps = phi_cam + side * math.radians(65)
    # wektor (cos ps, sin ps) w planie → Blender (x, -y); azymut od +Y Blendera zgodnie z zegarem
    bx, by = math.cos(ps), -math.sin(ps)
    return math.degrees(math.atan2(bx, by)) % 360


def plan_ujec(H, wersja=2):
    """Lista ujęć filmu dla domu H."""
    from silnik.meble import furnish_level
    for idx, L in H.L.items():
        if L.get("items") is None:
            L["items"] = furnish_level(H, idx)   # meble potrzebne, żeby kamera nie stanęła w szafie
    U = []
    sides = sorted(_side_scores(H), reverse=True)
    phi_a = sides[0][1]
    # lot ptaka: ukos 3/4 względem najlepszej strony
    phi_a += math.radians(25)
    el = math.radians(36)
    d, loc, tgt = _fit_distance(H, phi_a, el, 35.0, fill=0.9)
    gs = [r for r in H.all_rooms if r.kind == "ogrod"]
    area = H.area["uzytkowa"]
    og = H.area["ogrod"]
    g0 = gs[0] if gs else None
    sun = _sun_az(phi_a, 1)
    U.append(dict(id="lotu", scena="dzien", sun=sun, cam=dict(loc=loc, target=tgt, lens=35.0, shift_y=0.0, poziom=False),
                  orbit=dict(phi=phi_a, el=el, d=d, tgt=tgt, lens=35.0),
                  podpis="Z lotu ptaka", podpis2=f"{_num(area)} m² użytkowe · ogród pod szkłem {_num(og)} m²",
                  ruch="zoom_in", fokus=(0.5, 0.5), ekspo=0.0))
    if g0 is not None:
        cd = ujecie_dachu(H, phi_a)
        if cd is not None:
            U.append(dict(id="dach", scena="dzien", sun=sun, cam=cd, podpis="Dach ogrodu", podpis2=DACH.get(g0.roof_type, ""),
                          ruch="statyczny", fokus=(0.5, 0.5), ekspo=0.0, tylko_anim=True))
        c = ujecie_ogrodu(H, g0)
        U.append(dict(id="ogrod", scena="dzien", sun=sun, cam=c, podpis="Ogród pod szkłem",
                      podpis2=f"{STYL.get(g0.style, 'ogród')} · {DACH.get(g0.roof_type, 'dach otwierany')}",
                      ruch="pan_prawo", fokus=(0.5, 0.5), ekspo=0.6))
    rooms = [r for r in H.rooms if not r.outdoor and r.parent is None]
    sal = [r for r in rooms if r.kind == "salon_kuchnia"] or [r for r in rooms if r.kind in ("salon", "jadalnia")]
    if sal:
        r = max(sal, key=lambda r: r.poly.area)
        c = ujecie_wnetrza(H, r, "ogrod") or ujecie_wnetrza(H, r, "zewn")
        if c:
            hz = r.top - r.z0
            U.append(dict(id="salon", scena="dzien", sun=sun, cam=c, podpis=r.name,
                          podpis2=(f"wysokość {hz:.1f} m · ".replace(".", ",") if hz > 4.5 else "") + "widok na ogród",
                          ruch="zoom_in", fokus=(0.5, 0.52), ekspo=0.9))
    syp = [r for r in rooms if r.kind == "sypialnia_glowna"] or [r for r in rooms if r.kind == "sypialnia"]
    if syp:
        r = max(syp, key=lambda r: r.poly.area)
        c = ujecie_wnetrza(H, r, "zewn", lens=18.0, h_eye=1.3)
        if c:
            U.append(dict(id="sypialnia", scena="dzien", sun=sun, cam=c, podpis=r.name,
                          podpis2="szklana ściana na krajobraz", ruch="pan_lewo", fokus=(0.5, 0.5), ekspo=0.8))
    biu = [r for r in rooms if r.kind == "biuro"]
    if biu:
        r = max(biu, key=lambda r: r.poly.area)
        c = ujecie_wnetrza(H, r, "zewn", lens=18.0, h_eye=1.35)
        if c:
            U.append(dict(id="biuro", scena="dzien", sun=sun, cam=c, podpis=r.name,
                          podpis2="przeszklone z dwóch stron", ruch="zoom_in", fokus=(0.5, 0.5), ekspo=0.7))
    ter = [r for r in H.rooms if r.outdoor and r.level > min(H.L)]
    if ter:
        t = max(ter, key=lambda r: r.poly.area)
        c = ujecie_tarasu(H, t)
        if c:
            tot = sum(r.poly.area for r in ter)
            U.append(dict(id="taras", scena="dzien", sun=sun, cam=c, podpis="Taras na dachu parteru",
                          podpis2=f"tarasy razem {_num(tot)} m² · przy modułach piętra", ruch="pan_prawo",
                          fokus=(0.5, 0.5), ekspo=0.1))
    pat = [r for r in H.rooms if r.outdoor and r.level == min(H.L) and r.kind in ("patio", "patio_sezonowe")]
    if pat:
        p = max(pat, key=lambda r: r.poly.area)
        c = ujecie_patio(H, p)
        if c:
            U.append(dict(id="patio", scena="dzien", sun=sun, cam=c, podpis=p.name,
                          podpis2="przedłużenie salonu na zewnątrz", ruch="zoom_out", fokus=(0.5, 0.5), ekspo=0.3))
    # wieczór: strona z największym przeszkleniem (świeci), nieco z góry – widać też świecący dach ogrodu
    phi_z = sides[0][1] - math.radians(20)
    if abs((phi_z - phi_a + math.pi) % (2 * math.pi) - math.pi) < math.radians(35):
        phi_z = phi_a + math.radians(60)
    dz, locz, tgz = _fit_distance(H, phi_z, math.radians(24), 30.0, fill=0.86)
    U.append(dict(id="zmierzch", scena="zmierzch", sun=_sun_az(phi_z + math.pi, 1),
                  cam=dict(loc=locz, target=tgz, lens=30.0, shift_y=0.0, poziom=False),
                  podpis="Wieczorem", podpis2="ogród świeci w środku domu jak latarnia", ruch="zoom_in",
                  fokus=(0.5, 0.45), ekspo=0.0))
    # zima: lot ptaka z drugiej strony
    phi_w = phi_a - math.radians(100)
    dw, locw, tgw = _fit_distance(H, phi_w, math.radians(40), 35.0, fill=0.9)
    U.append(dict(id="zima", scena="zima", sun=_sun_az(phi_w, -1),
                  cam=dict(loc=locw, target=tgw, lens=35.0, shift_y=0.0, poziom=False),
                  podpis="Zimą", podpis2="dach zamknięty – pod szkłem trwa lato", ruch="zoom_in", fokus=(0.5, 0.5),
                  ekspo=-0.2))
    return U


# --------------------------------------------------------------- wirtualny spacer (pierwsza osoba)
DOOR_KINDS = ("door", "slide", "double", "pivot", "wide", "portal", "arch")
SALON = ("salon_kuchnia", "salon", "kuchnia", "jadalnia")


def _graf(H):
    """Graf przejść: klucz pokoju → [(sąsiad, punkt przejścia (x, y), poziom)]."""
    def key(r):
        return r.parent.key if r.parent is not None else r.key
    G = {}

    def link(a, b, p, lvl):
        if a == b:
            return
        G.setdefault(a, []).append((b, p, lvl))
        G.setdefault(b, []).append((a, p, lvl))
    for idx, L in H.L.items():
        for o in L["openings"]:
            if o.kind in DOOR_KINDS and o.run.other is not None:
                link(key(o.run.room), key(o.run.other), ((o.a[0] + o.b[0]) / 2, (o.a[1] + o.b[1]) / 2), idx)
        for run in L["runs"]:
            if run.other is not None and run.cls in (None, "open") and run.length > 0.8:
                p = run.point_at(run.length / 2)
                link(key(run.room), key(run.other), p, idx)
    for s in H.stairs:
        fp = s.footprint()
        c = fp.centroid
        ends = []
        for lvl in (s.level, s.to_level):
            best = None
            for r in H.all_rooms:
                if r.level <= lvl < r.level + r.levels and r.poly.buffer(0.05).intersects(fp):
                    a = r.poly.intersection(fp).area
                    if best is None or a > best[0]:
                        best = (a, key(r))
            if best:
                ends.append(best[1])
        if len(ends) == 2:
            link(ends[0], ends[1], (c.x, c.y), "schody")
    return G


def _sciezka(G, a, b):
    """Najkrótsza droga (liczba przejść) z a do b: lista (pokój, punkt wejścia, poziom przejścia)."""
    from collections import deque
    prev = {a: None}
    dq = deque([a])
    while dq:
        k = dq.popleft()
        if k == b:
            break
        for (n, p, lvl) in G.get(k, []):
            if n not in prev:
                prev[n] = (k, p, lvl)
                dq.append(n)
    if b not in prev:
        return None
    out = []
    k = b
    while prev[k] is not None:
        pk, p, lvl = prev[k]
        out.append((k, p, lvl))
        k = pk
    return out[::-1]


def _kat(dx, dy):
    """Kąt kierunku planu (x – wschód, y – południe) w układzie Blendera (stopnie, przeciwnie do zegara od +X)."""
    return math.degrees(math.atan2(-dy, dx))


def _stoisko(H, r, entry, lvl_z, back=None):
    """Punkt kamery ~1,1 m za progiem wejścia do pokoju r, w wolnym miejscu."""
    net = _net(r)
    free = net.buffer(-0.3, join_style="mitre")
    if r.kind != "ogrod":
        free = free.difference(_blocked(H, r, pad=0.15))
    else:
        lay = getattr(r, "_layout", None) or {}
        obst = [Point(f.x, f.y).buffer(f.r + 0.2) for f in lay.get("features", []) if f.t not in ("krok", "lilia", "mech")]
        water = [geom.buffer(0.05) for kind, geom in lay.get("floor", []) if kind == "woda"]
        if obst or water:
            free = free.difference(unary_union(obst + water))
        free = free.difference(_blocked(H, r, pad=0.15))
    if free.is_empty:
        free = net.buffer(-0.2)
    ex, ey = entry
    c = largest(free).representative_point() if not free.is_empty else net.representative_point()
    vx, vy = c.x - ex, c.y - ey
    L = math.hypot(vx, vy) or 1.0
    vx, vy = vx / L, vy / L
    best = None
    for d in (1.1, 0.8, 1.5, 2.0, 0.6, 2.6):
        for side in (0.0, 0.4, -0.4, 0.8, -0.8):
            px = ex + vx * d - vy * side
            py = ey + vy * d + vx * side
            if free.contains(Point(px, py)):
                best = (px, py)
                break
        if best:
            break
    if best is None:
        best = (c.x, c.y)
    return best


def _cel_pokoju(H, r, pos):
    """Na co patrzeć w pokoju: przeszklenie (ogród / krajobraz) albo główne meble."""
    pts = []
    for run in _runs(H, r):
        if run.cls in GLASS:
            for (x, y) in _seg_samples(run, 5):
                pts.append((x, y, 1.0))
    for it in _items(H, r):
        w = GLOWNE.get(it.kind)
        if w:
            pts.append((it.cx, it.cy, w))
    if r.kind == "ogrod":
        lay = getattr(r, "_layout", None) or {}
        for f in lay.get("features", []):
            if f.t in ("klon", "brzoza", "oliwka", "sosna", "palma", "cytrus", "fontanna", "latarnia"):
                pts.append((f.x, f.y, 2.0))
        c = r.poly.centroid
        pts.append((c.x, c.y, 3.0))
    if not pts:
        c = _net(r).centroid
        return (c.x, c.y)
    # najdalsze skupisko celów od kamery (ważone)
    sx = sum(p[0] * p[2] for p in pts) / sum(p[2] for p in pts)
    sy = sum(p[1] * p[2] for p in pts) / sum(p[2] for p in pts)
    if math.hypot(sx - pos[0], sy - pos[1]) < 0.6:
        c = _net(r).centroid
        return (c.x, c.y)
    return (sx, sy)


def zasieg_widoku(ruch, margines=2.5, kroki=9, aspekt=16 / 9):
    """Najmniejszy wycinek panoramy (lon, lat w stopniach) pokrywający kadry 16:9 dla ruchu kamery
    [[yaw, pitch, hfov] na początku, [..] na końcu] – to samo odwzorowanie co montaż (UjeciePanorama._mapa)."""
    n = 24
    t = [i / n for i in range(n + 1)]
    brzeg = [(u, 0.0) for u in t] + [(1.0, v) for v in t] + [(u, 1.0) for u in t] + [(0.0, v) for v in t]
    (y0, p0, h0), (y1, p1, h1) = ruch[0], ruch[-1]
    lo, la = [], []
    for i in range(kroki):
        e = i / (kroki - 1)
        yaw, pitch, hfov = y0 + (y1 - y0) * e, p0 + (p1 - p0) * e, h0 + (h1 - h0) * e
        tx = math.tan(math.radians(hfov) / 2)
        ty = tx / aspekt
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        cq, sq = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        for u, v in brzeg:
            x, y = (2 * u - 1) * tx, (1 - 2 * v) * ty
            y2, z2 = y * cp + sp, cp - y * sp
            x3, z3 = x * cq + z2 * sq, z2 * cq - x * sq
            lo.append(math.degrees(math.atan2(x3, z3)))
            la.append(math.degrees(math.atan2(y2, math.hypot(x3, z3))))
    return ([round(min(lo) - margines, 2), round(max(lo) + margines, 2)],
            [round(min(la) - margines, 2), round(max(la) + margines, 2)])


def plan_spaceru(H, max_stacji=6):
    """Stacje spaceru z perspektywy pierwszej osoby: przed wejściem → wnętrza → ogród → salon → piętro → taras."""
    from silnik.meble import furnish_level
    for idx, L in H.L.items():
        if L.get("items") is None:
            L["items"] = furnish_level(H, idx)
    G = _graf(H)
    rooms = {r.key: r for r in H.rooms}
    if not H.entrances:
        return []
    start = H.entrances[0]["room"]
    base = min(H.L)
    # drzwi wejściowe
    L0 = H.L[base]
    door = None
    for o in L0["openings"]:
        if o.label == "wejście" and (o.run.room.key == start or (o.run.other is not None and o.run.other.key == start)):
            door = o
            break
    targets = [start]
    gs = [r for r in H.rooms if r.kind == "ogrod"]
    if gs and gs[0].key in G:
        targets.append(gs[0].key)
    sal = [r for r in H.rooms if r.kind in SALON and not r.outdoor]
    if sal:
        targets.append(max(sal, key=lambda r: r.poly.area).key)
    upper = [r for r in H.rooms if r.level > base and not r.outdoor and r.kind not in ("void",)]
    rest = []
    for kinds in (("sypialnia_glowna", "sypialnia"), ("biuro",)):
        c = [r for r in upper if r.kind in kinds] or [r for r in H.rooms if r.kind in kinds and not r.outdoor]
        if c:
            rest.append(max(c, key=lambda r: r.poly.area).key)
    cur0 = targets[-1]
    while rest:
        # najpierw pokój najbliższy w liczbie przejść
        dist = [(len(_sciezka(G, cur0, k) or [0] * 99), k) for k in rest]
        dist.sort()
        cur0 = dist[0][1]
        targets.append(cur0)
        rest.remove(cur0)
    ter = [r for r in H.rooms if r.outdoor and r.level > base and r.key in G]
    if ter:
        # taras najbliżej ostatniego pokoju
        best = min(ter, key=lambda r: (len(_sciezka(G, cur0, r.key) or [0] * 99), -r.poly.area))
        targets.append(best.key)
    order = []
    for t in targets:
        if t not in order:
            order.append(t)
    stations = []
    # 0: przed wejściem
    if door is not None:
        mx, my = (door.a[0] + door.b[0]) / 2, (door.a[1] + door.b[1]) / 2
        nx, ny = door.run.normal
        if door.run.room.key != start:
            nx, ny = -nx, -ny
        px, py = mx + nx * 6.0, my + ny * 6.0
        stations.append(dict(id="przed", room=None, pos=(px, py, -0.3 + 1.6), look=(mx, my), next=(mx, my), lvl=base,
                             podpis="Przed wejściem"))
    cur = start
    visited = set()
    seq = [(start, (door.a[0] + door.b[0]) / 2 if door else None, (door.a[1] + door.b[1]) / 2 if door else None, base)]
    for t in order[1:]:
        p = _sciezka(G, cur, t)
        if not p:
            continue
        for (k, pt, lvl) in p:
            seq.append((k, pt[0], pt[1], lvl))
        cur = t
    # stacje: cele + pokój po schodach (przyjście na piętro)
    keyset = set(order)
    chosen = []
    for i, (k, x, y, lvl) in enumerate(seq):
        if k in visited:
            continue
        if k in keyset or (lvl == "schody"):
            chosen.append((k, x, y, lvl, i))
            visited.add(k)
    # za dużo stacji: najpierw odpada pokój po schodach, potem wiatrołap (cele klienta zostają)
    budget = max_stacji
    while len(chosen) > budget:
        extra = [c for c in chosen if c[0] not in keyset]
        if extra:
            chosen.remove(extra[0])
        elif len(chosen) > 1 and chosen[0][0] == start:
            chosen.pop(0)
        else:
            chosen.pop()
    for n_, (k, x, y, lvl, i) in enumerate(chosen):
        r = rooms.get(k)
        if r is None:
            continue
        entry = (x, y) if x is not None else _net(r).representative_point().coords[0]
        # najpierw dobry kadr jak w ujęciach wnętrz (kamera w głębi pokoju), w razie porażki – tuż za progiem
        c = None
        try:
            if r.kind == "ogrod":
                c = ujecie_ogrodu(H, r)
            elif r.outdoor:
                c = ujecie_tarasu(H, r)
            elif k != start:
                adj_g = any(run.other is not None and run.other.kind in ("ogrod", "ogrod_void") and run.cls in GLASS
                            for run in _runs(H, r))
                c = ujecie_wnetrza(H, r, "ogrod" if adj_g else "zewn")
        except Exception:
            c = None
        if c is not None:
            pos = c["loc"][:2]
            look = c["target"][:2]
        else:
            pos = _stoisko(H, r, entry, r.z0)
            look = _cel_pokoju(H, r, pos)
        # kierunek dalej: punkt wejścia do kolejnej stacji (jeśli w tym pokoju)
        nxt = None
        if n_ + 1 < len(chosen):
            j = chosen[n_ + 1][4]
            # przejście z tego pokoju w stronę następnej stacji
            for (k2, x2, y2, l2) in seq[i + 1:j + 1]:
                nxt = (x2, y2)
                break
        stations.append(dict(id=f"s{n_ + 1}_{k}", room=k, pos=(pos[0], pos[1], r.z0 + 1.5), look=look,
                             next=nxt, lvl=r.level, podpis=r.name))
    # kąty i zakres panoram
    out = []
    for st in stations:
        x, y, z = st["pos"]
        a1 = _kat(st["look"][0] - x, st["look"][1] - y)
        a2 = _kat(st["next"][0] - x, st["next"][1] - y) if st.get("next") else a1 - 40
        d = (a2 - a1 + 180) % 360 - 180
        if abs(d) < 30:
            a1 -= math.copysign(18, d if d else 1)
            a2 += math.copysign(18, d if d else 1)
            d = (a2 - a1 + 180) % 360 - 180
        if abs(d) > 50:
            # rozglądanie się w granicach ±25° – panorama nie może być za szeroka (czas renderu)
            a1 = a1 + (d - math.copysign(50, d)) / 2
            d = math.copysign(50, d)
            a2 = a1 + d
        mid = a1 + d / 2
        r = rooms.get(st["room"]) if st["room"] else None
        small = r is not None and r.poly.area < 12
        hfov = 70.0 if r is None else (84.0 if small else 78.0)
        pitch = 0.0
        if r is not None and r.kind == "ogrod":
            pitch = 6.0
        elif r is not None and (r.top - r.z0) > 4.5:
            pitch = 4.0
        yaw0, yaw1 = d / 2, -d / 2                # dodatni yaw = obrót w prawo (zgodnie z zegarem)
        if r is None:
            ruch = [[yaw0, 1.0, hfov], [yaw1, 0.0, hfov * 0.86]]
        else:
            ruch = [[yaw0, pitch, hfov], [yaw1, pitch * 0.5, hfov]]
        # panorama tylko tak duża, jak wymagają kadry (czas renderu ∝ liczbie pikseli)
        lon, lat = zasieg_widoku(ruch)
        out.append(dict(id=st["id"], room=st["room"], pos=st["pos"], kierunek=mid, lon=lon,
                        lat=lat, ruch=ruch, podpis=st["podpis"]))
    return out
