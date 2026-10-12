"""Zasady kolekcji (wersja 2) sprawdzane automatycznie.

Klient: dom do 170 m², ogród wewnętrzny wyizolowany i niewidoczny bezpośrednio z zewnątrz,
tarasy użytkowe na niższych dachach (nie na samej górze), wokół tarasu przelotowe moduły użytkowe.
"""
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

MAX_AREA = 170.0
GLASS = ("glass", "fold")
WALLED = ("gwall", "solid", "wall")


def _indoor(r):
    return r is not None and not r.outdoor and r.kind not in ("ogrod", "ogrod_void")


def _garden(r):
    return r is not None and r.kind in ("ogrod", "ogrod_void")


def _exterior(r):
    """Sąsiad, przez którego można patrzeć z zewnątrz: brak sąsiada albo otwarte patio/taras bez muru."""
    if r is None:
        return True
    return r.outdoor and r.level == r.house.ground and r.enclose not in WALLED


def _segments(run, ops):
    """Przeszklone fragmenty przebiegu: cały przebieg szklany albo drzwi przesuwne / wejście w ścianie pełnej."""
    if run.cls in GLASS:
        return [LineString(run.pts)]
    out = []
    for o in ops:
        if o.run is run and o.kind in ("slide", "pivot", "door", "double", "portal"):
            out.append(LineString([o.a, o.b]))
    return out


def _samples(seg, n=7):
    L = seg.length
    return [seg.interpolate(L * (0.08 + 0.84 * i / (n - 1))) for i in range(n)]


def _space(H, room, level_rooms):
    """Pomieszczenie razem z sąsiadami połączonymi bez ściany (connect "open")."""
    keys = {room.key}
    changed = True
    while changed:
        changed = False
        for c in H.connects:
            if c["kind"] != "open":
                continue
            if c["a"] in keys and c["b"] not in keys or c["b"] in keys and c["a"] not in keys:
                keys |= {c["a"], c["b"]}
                changed = True
    polys = [r.poly for r in level_rooms if r.key in keys and _indoor(r)]
    return unary_union(polys).buffer(0.05) if polys else room.poly.buffer(0.05)


def check(H):
    """Lista wyników: dict(key, label, ok, detail)."""
    res = []
    base = H.ground
    a = H.area["uzytkowa"]
    lim = getattr(H, "max_area", MAX_AREA)          # dom zamówiony z innym limitem (np. P21: 180 m² z piwnicą)
    res.append(dict(key="area", label=f"{a:.0f} m² użytkowe (limit {lim:.0f} m²)".replace(".", ","),
                    ok=a <= lim + 0.05, detail="" if a <= lim + 0.05 else f"za dużo o {a - lim:.1f} m²"))

    # 1. ogród otoczony pokojami
    bad = []
    gardens = [r for r in H.rooms if r.kind == "ogrod"]
    for g in gardens:
        for li in range(g.level, g.level + g.levels):
            L = H.L.get(li)
            if L is None:
                continue
            for run in L["runs"]:
                me = run.room
                if not (me is g or getattr(me, "parent", None) is g):
                    continue
                o = run.other
                if li == base:
                    if o is None and run.cls == "ext" and run.spec in ("solid", "wall"):
                        continue                    # pełna ściana zewnętrzna bez okien (np. z wodospadem) – ogród zasłonięty
                    if not _indoor(o) and not (o is not None and o.outdoor and o.enclose in WALLED):
                        bad.append(f"{run.length:.1f} m krawędzi ogrodu na parterze graniczy z "
                                   + ("zewnętrzem" if o is None else f"„{o.name}”"))
                elif o is None:
                    bad.append(f"{run.length:.1f} m krawędzi ogrodu na poziomie {li} wychodzi na zewnątrz")
    res.append(dict(key="enclosed", label="ogród ze wszystkich stron otoczony domem", ok=not bad and bool(gardens),
                    detail="; ".join(bad) if bad else ("" if gardens else "brak ogrodu")))

    # 2. brak widoku na przestrzał przez pokój (szkło od ogrodu + szkło / drzwi na zewnątrz)
    L0 = H.L[base]
    ops = L0["openings"]
    rooms0 = L0["rooms"]
    seen = []
    entry_keys = {e["room"] for e in H.entrances}
    entry_seen = []
    for r in rooms0:
        if not _indoor(r):
            continue
        g_segs, e_segs = [], []
        for run in L0["runs"]:
            if run.room is not r:
                continue
            if _garden(run.other):
                g_segs += _segments(run, ops) if run.cls in GLASS else []
            elif _exterior(run.other):
                e_segs += [(s, run) for s in _segments(run, ops)]
        if not g_segs or not e_segs:
            continue
        space = _space(H, r, rooms0)
        hit = None
        for gs in g_segs:
            gp = _samples(gs)
            for es, erun in e_segs:
                for p in _samples(es):
                    for q in gp:
                        if LineString([p, q]).within(space):
                            hit = es
                            break
                    if hit is not None:
                        break
                if hit is not None:
                    break
            if hit is not None:
                break
        if hit is not None:
            if r.key in entry_keys:
                entry_seen.append(r.name)
            else:
                seen.append(r.name)
    res.append(dict(key="private", label="z zewnątrz nie widać ogrodu na wylot przez pokoje", ok=not seen,
                    detail=("przez: " + ", ".join(seen)) if seen else ""))
    ent_bad = list(entry_seen)
    for e in H.entrances:
        try:
            r = H.get(e["room"])
        except KeyError:
            continue
        for run in L0["runs"]:
            if run.room is r and _garden(run.other) and run.cls in GLASS and r.name not in ent_bad:
                ent_bad.append(r.name)
    res.append(dict(key="entry", label="od wejścia nie widać ogrodu", ok=not ent_bad,
                    detail=("szkło do ogrodu w: " + ", ".join(ent_bad)) if ent_bad else ""))

    # 3. tarasy użytkowe na niższych dachach (nie na samej górze)
    terr = [r for r in H.rooms if r.outdoor and r.level > base]
    top_bad, usable = [], []
    for t in terr:
        same = [r for r in H.all_rooms if r.level == t.level and _indoor(r) and r.kind != "void"]
        if not same:
            top_bad.append(t.name)
        for c in H.connects:
            if t.key in (c["a"], c["b"]):
                other = c["b"] if c["a"] == t.key else c["a"]
                try:
                    o = H.get(other)
                except KeyError:
                    continue
                if _indoor(o) and o.level == t.level and c["kind"] not in ("railing",):
                    usable.append(t)
                    break
    ok3 = bool(usable) and not top_bad
    det = []
    if not usable:
        det.append("brak tarasu na dachu z wyjściem z pokoju piętra")
    if top_bad:
        det.append("taras na najwyższym dachu: " + ", ".join(top_bad))
    res.append(dict(key="terraces", label="tarasy użytkowe na niższych dachach", ok=ok3, detail="; ".join(det)))

    # 4. moduły piętra wokół tarasu, przelotowe
    upper = [r for r in H.rooms if r.level > base and _indoor(r)]
    around = []
    for r in upper:
        for t in usable:
            if t.level == r.level and r.poly.buffer(0.05).intersection(t.poly.buffer(0.05)).length > 0 or \
                    t.level == r.level and r.poly.buffer(0.02).intersects(t.poly.buffer(0.02)):
                around.append(r)
                break
    ok4 = len(around) >= 2
    res.append(dict(key="modules", label="moduły piętra wokół tarasu", ok=ok4,
                    detail="" if ok4 else f"przy tarasie stoi {len(around)} pomieszczeń piętra (potrzeba co najmniej 2)"))
    return res


def problems(H):
    return [f"{r['label']}: {r['detail']}" if r["detail"] else r["label"] for r in check(H) if not r["ok"]]


def nieosiagalne(H):
    """Pomieszczenia, do których nie da się dojść od wejścia (drzwi z połączeń, przejścia otwarte, schody)."""
    from shapely.geometry import Point
    adj = {}

    def link(a, b):
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    def key(r):
        return r.parent.key if r.parent is not None else r.key
    for c in H.connects:
        if c["kind"] == "open":
            link(c["a"], c["b"])
    for L in H.L.values():
        for run in L["runs"]:
            if run.other is not None and run.cls in (None, "open", "fold", "columns") and run.length > 0.8:
                link(key(run.room), key(run.other))
        for o in L["openings"]:
            if o.kind in ("door", "slide", "double", "pivot", "wide", "portal", "arch") and o.run.other is not None:
                link(key(o.run.room), key(o.run.other))
    for r in H.all_rooms:
        if r.parent is not None:
            link(r.key, r.parent.key)
    for s in H.stairs:
        try:
            fp = s.footprint()
        except Exception:
            continue
        p = fp.representative_point() if not fp.is_empty else None
        if p is None:
            continue
        ends = []
        for lvl in (s.level, s.to_level):
            best = None
            for r in H.all_rooms:
                if r.level <= lvl < r.level + r.levels and r.poly.buffer(0.05).intersects(fp):
                    a = r.poly.intersection(fp).area
                    if best is None or a > best[0]:
                        best = (a, r.parent.key if r.parent is not None else r.key)
            if best:
                ends.append(best[1])
        if len(ends) == 2:
            link(*ends)
    start = [e["room"] for e in H.entrances]
    seen = set(start)
    todo = list(start)
    while todo:
        k = todo.pop()
        for n in adj.get(k, ()):
            if n not in seen:
                seen.add(n)
                todo.append(n)
    out = []
    for r in H.rooms:
        if r.kind in ("ogrod", "void") or r.parent is not None:
            continue
        if r.key not in seen:
            out.append(r.name)
    return out
