#!/usr/bin/env python3
"""Wirtualne zwiedzanie domu: pełne panoramy 360° ze spaceru (film/render.py) → strona do samodzielnego zwiedzania
(przeglądarka Pannellum, przejścia do sąsiednich pomieszczeń, rzut kondygnacji z punktami, opisy pomieszczeń).

  python3 film/zwiedzanie.py p21          → out/zwiedzanie/p21/index.html + pano/*.jpg + mini/*.jpg
  python3 film/zwiedzanie.py p21 --lokalnie  → wersja do sprawdzenia bez sieci (Pannellum wklejony w stronę)
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from PIL import Image  # noqa: E402

from podglad import load  # noqa: E402
from film import kamery  # noqa: E402
from film.spacer import widok  # noqa: E402

PANNELLUM = "https://cdnjs.cloudflare.com/ajax/libs/pannellum/2.5.6/pannellum.js"
POZIOMY = {-1: "Piwnica", 0: "Parter", 1: "Piętro", 2: "II piętro"}


def _bearing(x, y, px, py):
    """Kierunek od północy zgodnie z ruchem wskazówek zegara (plan: y rośnie na południe)."""
    return math.degrees(math.atan2(px - x, -(py - y)))


def _r(v, n=2):
    return round(float(v), n)


def zwiedzanie(pid, wersja=2, lokalnie=False, szer=4096):
    H = load(pid, "domy" if wersja == 2 else "domy_v1").build()
    src = os.path.join(HERE, "out", "film", f"v{wersja}", pid)
    SP = json.load(open(os.path.join(src, "spacer", "spacer.json"), encoding="utf-8"))
    nar = {}
    nj = os.path.join(HERE, "film", "narracja", f"v{wersja}", f"{pid}.json")
    if os.path.exists(nj):
        nar = json.load(open(nj, encoding="utf-8")).get("spacer", {})
    out = os.path.join(HERE, "out", "zwiedzanie", pid)
    for d in ("pano", "mini"):
        os.makedirs(os.path.join(out, d), exist_ok=True)
    rooms = {r.key: r for r in H.rooms}
    area = {r.key: a for _, r, a in H.room_areas}
    by_room = {st["room"]: st for st in SP if st["room"]}
    G = kamery._graf(H)
    przed = [st for st in SP if st["room"] is None]
    wejscie = None
    for o in H.L[H.ground]["openings"]:
        if o.label == "wejście":
            wejscie = (o.run.room.key, ((o.a[0] + o.b[0]) / 2, (o.a[1] + o.b[1]) / 2))
    stacje = []
    for st in SP:
        sid, rk = st["id"], st["room"]
        r = rooms.get(rk)
        x, y, z = st["pos"]
        lvl = r.level if r is not None else H.ground
        z_fl = r.z0 if r is not None else -0.3
        # obraz: JPEG do 4096 px szerokości, miniatura z kierunku startowego
        pano = os.path.join(src, st["obraz"])
        im = Image.open(pano).convert("RGB")
        if im.width > szer:
            im = im.resize((szer, round(im.height * szer / im.width)), Image.LANCZOS)
        im.save(os.path.join(out, "pano", sid + ".jpg"), quality=84, optimize=True, progressive=True)
        (y0, p0, h0), (y1, p1, h1) = st["ruch"]
        th = widok(im, st["lon"], st["lat"], (y0 + y1) / 2, 0.0, 84.0, 480, 270)
        th.save(os.path.join(out, "mini", sid + ".jpg"), quality=80, optimize=True)
        # przejścia: drzwi / otwarcia / schody do pomieszczeń, które mają swój punkt
        hs = {}

        def dodaj(tgt, px, py, pz, opis):
            t = by_room.get(tgt) if tgt != "__przed" else (przed[0] if przed else None)
            if t is None or t["id"] == sid:
                return
            d = math.hypot(px - x, py - y)
            yaw = _bearing(x, y, px, py)
            pitch = math.degrees(math.atan2(pz - z, max(d, 0.3)))
            prev = hs.get(t["id"])
            if prev is None or d < prev["_d"]:
                hs[t["id"]] = dict(do=t["id"], yaw=_r(yaw, 1), pitch=_r(max(-55, min(55, pitch)), 1), opis=opis, _d=d)
        if rk is not None:
            for (nb, p, l) in G.get(rk, []):
                rn = rooms.get(nb)
                if rn is None:
                    continue
                if l == "schody":
                    up = rn.level > lvl
                    dodaj(nb, p[0], p[1], z_fl + (1.6 if up else -0.6),
                          ("Schody w górę: " if up else "Schody w dół: ") + (by_room.get(nb) or {}).get("podpis", rn.name))
                else:
                    dodaj(nb, p[0], p[1], z_fl + 1.0, (by_room.get(nb) or {}).get("podpis", rn.name))
            if wejscie and wejscie[0] == rk:
                dodaj("__przed", wejscie[1][0], wejscie[1][1], z_fl + 1.0, "Wyjście przed dom")
        elif wejscie:
            hk = wejscie[0]
            dodaj(hk, wejscie[1][0], wejscie[1][1], z_fl + 1.3, (by_room.get(hk) or {}).get("podpis", "Wejście"))
        for v in hs.values():
            v.pop("_d", None)
        stacje.append(dict(
            id=sid, room=rk, nazwa=st["podpis"], poziom=lvl, x=_r(x), y=_r(y), yaw=_r((y0 + y1) / 2, 1),
            obraz=f"pano/{sid}.jpg", mini=f"mini/{sid}.jpg", haov=_r(st["lon"][1] - st["lon"][0], 1),
            vaov=_r(st["lat"][1] - st["lat"][0], 1), voff=_r((st["lat"][1] + st["lat"][0]) / 2, 1),
            opis=nar.get(sid, ""), m2=_r(area.get(rk, 0.0), 1) if rk else None, przejscia=list(hs.values())))
    # rzuty: obrysy pomieszczeń netto każdej kondygnacji
    plany = {}
    for idx, L in sorted(H.L.items()):
        rr = []
        for r in L["rooms"]:
            if r.parent is not None or r.kind in ("void", "ogrod_void"):
                continue
            g = r.net if r.net is not None else r.poly
            rr.append(dict(key=r.key, nazwa=r.name, rodzaj=("ogrod" if r.kind == "ogrod" else
                                                            "zewn" if r.outdoor else "wn"),
                           pts=[[_r(a), _r(b)] for a, b in list(g.exterior.coords)[:-1]],
                           c=[_r(g.representative_point().x), _r(g.representative_point().y)]))
        if rr:
            plany[str(idx)] = dict(nazwa=POZIOMY.get(idx, f"Poziom {idx}"), pokoje=rr)
    minx, miny, maxx, maxy = H.bbox
    for st in stacje:
        minx, miny = min(minx, st["x"] - 1), min(miny, st["y"] - 1)
        maxx, maxy = max(maxx, st["x"] + 1), max(maxy, st["y"] + 1)
    for p in plany.values():
        for r in p["pokoje"]:
            for a, b in r["pts"]:
                minx, miny, maxx, maxy = min(minx, a), min(miny, b), max(maxx, a), max(maxy, b)
    dane = dict(pid=pid.upper(), nazwa=H.name, opis=H.tagline, m2=_r(H.area["uzytkowa"], 0),
                piwnica=_r(H.area.get("piwnica", 0.0), 0), stacje=stacje, plany=plany,
                bbox=[_r(minx - 0.6), _r(miny - 0.6), _r(maxx + 0.6), _r(maxy + 0.6)])
    tpl = open(os.path.join(HERE, "film", "zwiedzanie_szablon.html"), encoding="utf-8").read()
    css = open(os.path.join(HERE, "film", "pannellum.css"), encoding="utf-8").read()
    if lokalnie:
        js = open(os.path.join(HERE, "film", "pannellum.js"), encoding="utf-8").read()
        skrypt = "<script>" + js + "</script>"
    else:
        skrypt = f'<script src="{PANNELLUM}"></script>'
    html = (tpl.replace("/*PANNELLUM_CSS*/", css).replace("<!--PANNELLUM_JS-->", skrypt)
            .replace("/*DANE*/null", json.dumps(dane, ensure_ascii=False)))
    fn = os.path.join(out, "index_lokalnie.html" if lokalnie else "index.html")
    open(fn, "w", encoding="utf-8").write(html)
    return fn


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pid")
    ap.add_argument("--wersja", type=int, default=2)
    ap.add_argument("--lokalnie", action="store_true")
    a = ap.parse_args()
    print(zwiedzanie(a.pid, a.wersja, a.lokalnie))
