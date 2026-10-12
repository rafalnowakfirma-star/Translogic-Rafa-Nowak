#!/usr/bin/env python3
"""Rendery do filmu jednego domu: kadry (stillsy), animacja otwierania dachu, scenariusz montażu.

  /home/user/tools/bpyenv/bin/python film/render.py p01 --wersja 2 --q final
  /home/user/tools/bpyenv/bin/python film/render.py p05 --wersja 1 --q podglad --ujecia lotu,salon

Wyniki: out/film/v<wersja>/<pid>/kadry/*.png, anim/lotu/*.png, kadry.json (plan ujęć z podpisami).
Rendery wznawiają się: istniejące pliki są pomijane (--od-nowa wymusza ponowny render).
"""
import argparse
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

from podglad import load  # noqa: E402
from render_blender import _slot  # noqa: E402
from film import scena, kamery  # noqa: E402

Q = {
    # rozdzielczość kadrów, próbki (zewn., wnętrza), próg szumu, rozdzielczość i próbki animacji, klatki animacji
    "podglad": dict(res=(640, 360), spp=(16, 24), noise=0.1, ares=(640, 360), aspp=12, aframes=12, ppd=6, pspp=16),
    "szybki": dict(res=(1280, 720), spp=(48, 80), noise=0.04, ares=(1280, 720), aspp=32, aframes=30, ppd=12, pspp=48),
    # docelowa: 1080p; próbki dobrane testami (z odszumianiem OIDN 24–48 próbek ≈ 96 wizualnie, 2–3× szybciej);
    # panoramy spaceru 14 px/° (kadr 78° ma ~20 px/° w środku – lekkie zmiękczenie, ale 2× krótszy render)
    "final": dict(res=(1920, 1080), spp=(32, 48), noise=0.05, ares=(1920, 1080), aspp=32, aframes=40, ppd=14, pspp=24,
                  pnoise=0.06),
}
SCENY = {"dzien": ("lato", "dzien", False), "zmierzch": ("zima", "zmierzch", False), "zima": ("zima", "zima", True)}
INTERIOR = ("ogrod", "salon", "sypialnia", "biuro")
KADRY_FILMU = ("lotu", "dach", "zmierzch", "zima")


def bl(ctx, p):
    return ctx.to_bl(p[0], p[1], p[2])


def auto_ekspozycja(sc, cel=0.18, bias=0.0, tmp="/tmp", chron=True, zapas=0.0, maks=3.0):
    """Pomiar światła małym renderem (EXR liniowy, odszumiony) – ekspozycja tak, by średnia logarytmiczna jasność
    (bez najjaśniejszych okien i nieba) wypadła w szarości `cel`.
    zapas – o ile EV wolno prześwietlić najjaśniejsze 5% (niebo, okna), żeby ciemna fasada / wnętrze nie wyszły czarne."""
    r = sc.render
    keep = (r.resolution_x, r.resolution_y, sc.cycles.samples, r.image_settings.file_format, r.filepath,
            sc.cycles.use_adaptive_sampling)
    r.resolution_x, r.resolution_y = 320, 180
    sc.cycles.samples = 16
    sc.cycles.use_adaptive_sampling = False
    r.image_settings.file_format = "OPEN_EXR"
    fn = os.path.join(tmp, f"pomiar_{os.getpid()}.exr")
    r.filepath = fn
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(fn)
    px = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)[..., :3]
    bpy.data.images.remove(im)
    os.remove(fn)
    Y = 0.2126 * px[..., 0] + 0.7152 * px[..., 1] + 0.0722 * px[..., 2]
    h, w = Y.shape
    b = 8
    Y = Y[:h // b * b, :w // b * b].reshape(h // b, b, w // b, b).mean(axis=(1, 3))   # bloki 8×8 – bez szumu
    Yc = np.clip(Y, 1e-4, None)
    p50, p95 = float(np.percentile(Yc, 50)), float(np.percentile(Yc, 95))
    # jak fotograf: średnie tony do szarości, ale jasne (oświetlone słońcem) płaszczyzny nie mogą się przepalić
    ev = min(math.log2(cel / p50), math.log2(0.85 / p95) + zapas) if chron else math.log2(cel / p50)
    ev = max(-2.5, min(maks, ev + bias))
    (r.resolution_x, r.resolution_y, sc.cycles.samples, r.image_settings.file_format, r.filepath,
     sc.cycles.use_adaptive_sampling) = keep
    sc.view_settings.exposure = ev
    return ev


def _projekcja(sc, cam, pts):
    """Prostokąt (0..1, początek w lewym dolnym rogu) obejmujący punkty 3D w kadrze kamery."""
    from bpy_extras.object_utils import world_to_camera_view
    xs, ys = [], []
    for p in pts:
        v = world_to_camera_view(sc, cam, Vector(p))
        if v.z <= 0:
            continue
        xs.append(v.x)
        ys.append(v.y)
    if not xs:
        return None
    return max(0.0, min(xs)), max(0.0, min(ys)), min(1.0, max(xs)), min(1.0, max(ys))


def render_domu(pid, wersja, q, ujecia=None, out=None, od_nowa=False, anim=True, spacer=True):
    kat = "domy" if wersja == 2 else "domy_v1"
    H = load(pid, kat).build()
    out = out or os.path.join(HERE, "out", "film", f"v{wersja}", pid)
    os.makedirs(os.path.join(out, "kadry"), exist_ok=True)
    P = Q[q]
    U = kamery.plan_ujec(H, wersja)
    if ujecia:
        U = [u for u in U if u["id"] in ujecia]
    else:
        # wnętrza pokazuje spacer z panoram – osobne kadry tylko z zewnątrz
        U = [u for u in U if u["id"] in KADRY_FILMU]
    seed = int(pid[1:]) * 7 + wersja
    czasy = {}
    for sname in ("dzien", "zmierzch", "zima"):
        grp = [u for u in U if u["scena"] == sname]
        if not grp:
            continue
        todo = [u for u in grp if not u.get("tylko_anim")
                and (od_nowa or not os.path.exists(os.path.join(out, "kadry", u["id"] + ".png")))]
        sp_done = os.path.exists(os.path.join(out, "spacer", "spacer.json")) and not od_nowa
        want_anim = anim and sname == "dzien" and any(u["id"] == "dach" for u in grp)
        adir = os.path.join(out, "anim", "lotu")
        if want_anim and not od_nowa and os.path.exists(os.path.join(adir, "gotowe.json")):
            want_anim = False
        if not todo and not want_anim and not (sname == "dzien" and spacer and not sp_done):
            continue
        wariant, pora, snieg = SCENY[sname]
        t0 = time.time()
        minx, miny, maxx, maxy = H.bbox
        ox, oy = (minx + maxx) / 2, (miny + maxy) / 2
        cams = [((u["cam"]["loc"][0] - ox, -(u["cam"]["loc"][1] - oy)), (u["cam"]["target"][0] - ox, -(u["cam"]["target"][1] - oy)))
                for u in grp]
        S = scena.zbuduj(H, wariant, pora, snieg=snieg, dach_t=getattr(H, "dach_dzien", 1.0) if sname == "dzien" else None, kamery=cams,
                         seed=seed, az=grp[0]["sun"])
        sc, ctx = S["sc"], S["ctx"]
        czasy[f"budowa_{sname}"] = round(time.time() - t0, 1)
        lock = _slot(int(os.environ.get("OGRODY_SLOTY", "2")))
        for u in todo:
            c = u["cam"]
            inside = u["id"] in INTERIOR
            scena.ustaw_render(sc, P["res"], P["spp"][1 if inside else 0], 0.0, noise=P["noise"], persistent=True)
            cam = scena.kamera(sc, bl(ctx, c["loc"]), bl(ctx, c["target"]), c["lens"], c.get("shift_y", 0.0),
                               c.get("poziom", False), name="kam_" + u["id"])
            t1 = time.time()
            cel = {"zmierzch": 0.07, "zima": 0.34}.get(sname, 0.19 if inside else 0.18)
            ev = auto_ekspozycja(sc, cel, u.get("ekspo", 0.0), chron=sname != "zmierzch")
            sc.render.filepath = os.path.join(out, "kadry", u["id"] + ".png")
            bpy.ops.render.render(write_still=True)
            czasy[u["id"]] = round(time.time() - t1, 1)
            u["ev"] = round(ev, 2)
            print(f"KADR {pid} v{wersja} {u['id']}: {czasy[u['id']]} s, ekspozycja {ev:+.2f}", flush=True)
        if want_anim:
            u = next(u for u in grp if u["id"] == "dach")
            czasy["anim"] = animacja_dachu(S, u, P, adir)
            scena.ustaw_dach(S, getattr(H, "dach_dzien", 1.0))   # spacer w stanie dachu jak w kadrach dnia
        if sname == "dzien" and spacer and not sp_done:
            czasy["spacer"] = panoramy(S, kamery.plan_spaceru(H), P, os.path.join(out, "spacer"), od_nowa)
        del lock
    # plan ujęć dla montażu
    info = dict(pid=pid, wersja=wersja, nazwa=H.name, tagline=H.tagline if hasattr(H, "tagline") else "",
                ujecia=[{k: v for k, v in u.items() if k not in ("orbit",)} for u in U], czasy=czasy)
    old = os.path.join(out, "kadry.json")
    if os.path.exists(old) and ujecia:
        prev = json.load(open(old, encoding="utf-8"))
        ids = {u["id"] for u in info["ujecia"]}
        info["ujecia"] = [u for u in prev.get("ujecia", []) if u["id"] not in ids] + info["ujecia"]
        prev.get("czasy", {}).update(czasy)
        info["czasy"] = prev.get("czasy", czasy)
    json.dump(info, open(old, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print("CZASY", pid, czasy, flush=True)


def kierunek_widoku(sc, ctx, st, zakres=120, krok=5):
    """Szybki rzut 360° z punktu stacji (bardzo niska rozdzielczość): o ile stopni (+ w prawo) przesunąć kadry spaceru,
    żeby patrzyły w najjaśniejszą i najbardziej otwartą stronę (okna, przejścia), a nie w ciemną ścianę czy szafę."""
    r, cy = sc.render, sc.cycles
    co = bpy.data.objects.get("sonda_360")
    if co is None:                     # jedna kamera pomocnicza na scenę (usuwanie obiektów przy trwałych danych
        cam = bpy.data.cameras.new("sonda_360")                       # renderu wywracało Blendera)
        cam.type = "PANO"
        cam.panorama_type = "EQUIRECTANGULAR"
        cam.longitude_min, cam.longitude_max = -math.pi, math.pi
        cam.latitude_min, cam.latitude_max = math.radians(-22), math.radians(22)
        cam.clip_start = 0.05
        co = bpy.data.objects.new("sonda_360", cam)
        sc.collection.objects.link(co)
    co.location = bl(ctx, st["pos"])
    co.rotation_euler = (math.radians(90), 0, math.radians(st["kierunek"] - 90))
    keep = (sc.camera, r.resolution_x, r.resolution_y, cy.samples, cy.use_adaptive_sampling, r.image_settings.file_format,
            r.filepath)
    sc.camera = co
    r.engine = "CYCLES"                # przed pierwszym renderem sceny może być jeszcze silnik podglądu (wymaga GPU)
    cy.device = "CPU"
    r.resolution_x, r.resolution_y = 360, 44
    cy.samples = 8
    cy.use_adaptive_sampling = False
    r.image_settings.file_format = "OPEN_EXR"
    fn = f"/tmp/sonda_{os.getpid()}.exr"
    r.filepath = fn
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(fn)
    px = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)[..., :3]
    bpy.data.images.remove(im)
    os.remove(fn)
    (sc.camera, r.resolution_x, r.resolution_y, cy.samples, cy.use_adaptive_sampling, r.image_settings.file_format,
     r.filepath) = keep
    Y = 0.2126 * px[..., 0] + 0.7152 * px[..., 1] + 0.0722 * px[..., 2]
    kol = np.log(np.clip(np.median(Y, axis=0), 1e-5, None))        # 360 kolumn: długość −180…180 (lewo → prawo)
    W = len(kol)
    hf = max(u[2] for u in st["ruch"])
    y0, y1 = st["ruch"][0][0], st["ruch"][-1][0]
    sr, amp = (y0 + y1) / 2, (y0 - y1) / 2                          # środek i połowa obrotu (ze znakiem)
    ciemno = np.median(kol) - 1.6                                   # kolumny wyraźnie ciemniejsze niż typowe w pokoju

    def kadr(c):                                                    # ocena jednego kadru o środku c (stopnie)
        idx = (np.arange(int(round(c - hf / 2)), int(round(c + hf / 2)) + 1) + W // 2) % W
        w = kol[idx]
        return float(np.median(w) - 2.0 * np.mean(w < ciemno))

    def ocena(c, f):                                                # przesunięcie c, obrót zmniejszony do f
        return min(kadr(sr + c + amp * f), kadr(sr + c - amp * f)) + 0.15 * f - 0.003 * abs(c)

    best = max(((c, f) for c in range(-zakres, zakres + 1, krok) for f in (1.0, 0.6, 0.3)), key=lambda x: ocena(*x))
    return best[0], best[1], ocena(*best) - ocena(0, 1.0)


def panoramy(S, stations, P, sdir, od_nowa=False):
    """Panoramy (wycinek walcowo-kulisty, equirectangular) do spaceru z perspektywy pierwszej osoby."""
    sc, ctx = S["sc"], S["ctx"]
    os.makedirs(sdir, exist_ok=True)
    t0 = time.time()
    meta = []
    pokoje = {r.key: r for r in S["H"].rooms}
    prev_ev, prev_inside = None, None
    for st in stations:
        fn = os.path.join(sdir, st["id"] + ".png")
        cam = bpy.data.cameras.new("pano_" + st["id"])
        cam.type = "PANO"
        cam.panorama_type = "EQUIRECTANGULAR"
        cam.longitude_min, cam.longitude_max = (math.radians(v) for v in st["lon"])
        cam.latitude_min, cam.latitude_max = (math.radians(v) for v in st["lat"])
        cam.clip_start = 0.05
        co = bpy.data.objects.new("pano_" + st["id"], cam)
        sc.collection.objects.link(co)
        co.location = bl(ctx, st["pos"])
        co.rotation_euler = (math.radians(90), 0, math.radians(st["kierunek"] - 90))
        sc.camera = co
        W = int(round((st["lon"][1] - st["lon"][0]) * P["ppd"] / 2)) * 2
        Hh = int(round((st["lat"][1] - st["lat"][0]) * P["ppd"] / 2)) * 2
        r = pokoje.get(st["room"])
        inside = r is not None and not r.outdoor          # taras liczy się jako „na dworze”
        scena.ustaw_render(sc, (W, Hh), P["pspp"], 0.0, noise=P.get("pnoise", P["noise"]), persistent=True)
        # spacer: jak fotograf wnętrz – ekspozycja na pokój / fasadę, okna i niebo mogą się lekko przepalić (AgX łagodnie)
        ev = ev_zmierzone = auto_ekspozycja(sc, 0.19 if inside else 0.18, 0.0, zapas=1.0 if inside else 1.5, maks=4.5)
        if prev_ev is not None and prev_inside == inside:
            # między pokojami oko adaptuje się, ale bez skoków; wejście z dworu do środka (i wyjście) – pełna ekspozycja
            ev = max(prev_ev - 2.0, min(prev_ev + 2.0, ev))
            sc.view_settings.exposure = ev
        prev_ev, prev_inside = ev, inside
        if od_nowa or not os.path.exists(fn):
            sc.render.filepath = fn
            bpy.ops.render.render(write_still=True)
            print(f"PANORAMA {st['id']} {W}×{Hh} {time.time() - t0:.0f} s, ekspozycja {ev:+.2f}"
                  f" (zmierzona {ev_zmierzone:+.2f})", flush=True)
        meta.append(dict(st, obraz=f"spacer/{st['id']}.png", ev=round(ev, 2)))
    json.dump(meta, open(os.path.join(sdir, "spacer.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return round(time.time() - t0, 1)


def animacja_dachu(S, u, P, adir):
    """Otwieranie szklanego dachu z nieruchomej kamery: pełna klatka startowa + co klatkę tylko obszar dachu (border)."""
    sc, ctx, H = S["sc"], S["ctx"], S["H"]
    os.makedirs(adir, exist_ok=True)
    c = u["cam"]
    cam = scena.kamera(sc, bl(ctx, c["loc"]), bl(ctx, c["target"]), c["lens"], 0.0, False, name="kam_anim")
    scena.ustaw_render(sc, P["ares"], P["aspp"], 0.0, noise=P["noise"], persistent=True)
    ev = auto_ekspozycja(sc, 0.2, u.get("ekspo", 0.0))
    # obszar dachu w kadrze (z zapasem): obrys ogrodu na wysokości dachu i nad nim
    pts = []
    for g in [r for r in H.all_rooms if r.kind == "ogrod"]:
        for (x, y) in list(g.poly.buffer(1.2).exterior.coords):
            for dz in (-0.6, 1.0):
                pts.append(bl(ctx, (x, y, g.roof_z + dz)))
    box = _projekcja(sc, cam, pts)
    t0 = time.time()
    n = P["aframes"]
    meta = dict(n=n, fps_render=12.5, ev=ev, box=box, res=list(P["ares"]))
    r = sc.render
    W, Hh = P["ares"]
    for i in range(n + 1):
        fn = os.path.join(adir, f"{i:04d}.png")
        if os.path.exists(fn):
            continue
        t = i / n
        scena.ustaw_dach(S, t)
        if i == 0 or box is None:
            r.use_border = False
        else:
            r.use_border = True
            r.use_crop_to_border = True
            r.border_min_x, r.border_min_y, r.border_max_x, r.border_max_y = box
        r.filepath = fn
        bpy.ops.render.render(write_still=True)
        print(f"ANIM {i}/{n} {time.time() - t0:.0f} s", flush=True)
    r.use_border = False
    if box is not None:
        meta["px"] = [int(round(box[0] * W)), int(round((1 - box[3]) * Hh)), int(round(box[2] * W)), int(round((1 - box[1]) * Hh))]
    json.dump(meta, open(os.path.join(adir, "gotowe.json"), "w"), indent=1)
    return round(time.time() - t0, 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pid")
    ap.add_argument("--wersja", type=int, default=2)
    ap.add_argument("--q", default="final", choices=list(Q))
    ap.add_argument("--ujecia", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--od-nowa", action="store_true")
    ap.add_argument("--bez-anim", action="store_true")
    ap.add_argument("--bez-spaceru", action="store_true")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    render_domu(a.pid, a.wersja, a.q, a.ujecia.split(",") if a.ujecia else None, a.out, a.od_nowa, not a.bez_anim,
                not a.bez_spaceru)
