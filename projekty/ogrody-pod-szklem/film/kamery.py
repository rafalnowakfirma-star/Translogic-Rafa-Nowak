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
    bnd = space.exterior
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
                score = sc_ * min(1.0, md / 5.0) ** 0.5
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
    eye = h_eye + (0.25 if high else 0.0)
    return dict(loc=(cx, cy, r.z0 + eye), target=(tx, ty, r.z0 + eye), lens=lens,
                shift_y=shift + (0.14 if high else 0.0), poziom=True, score=round(score, 2), glass=round(gfrac, 2))


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
    U = []
    sides = sorted(_side_scores(H), reverse=True)
    phi_a = sides[0][1]
    # lot ptaka: ukos 3/4 względem najlepszej strony
    phi_a += math.radians(25)
    el = math.radians(36)
    d, loc, tgt = _fit_distance(H, phi_a, el, 35.0, fill=0.9)
    gs = [r for r in H.all_rooms if r.kind == "ogrod"]
    area = H.area["uzytkowa"]
    og = sum(g.poly.area for g in gs)
    g0 = gs[0] if gs else None
    sun = _sun_az(phi_a, 1)
    U.append(dict(id="lotu", scena="dzien", sun=sun, cam=dict(loc=loc, target=tgt, lens=35.0, shift_y=0.0, poziom=False),
                  orbit=dict(phi=phi_a, el=el, d=d, tgt=tgt, lens=35.0),
                  podpis="Z lotu ptaka", podpis2=f"{_num(area)} m² użytkowe · ogród pod szkłem {_num(og)} m²",
                  ruch="zoom_in", fokus=(0.5, 0.5), ekspo=0.0))
    if g0 is not None:
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
