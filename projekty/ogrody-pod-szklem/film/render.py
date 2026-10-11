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
    "podglad": dict(res=(640, 360), spp=(16, 24), noise=0.1, ares=(640, 360), aspp=12, aframes=12),
    "szybki": dict(res=(1280, 720), spp=(48, 80), noise=0.04, ares=(1280, 720), aspp=32, aframes=30),
    "final": dict(res=(2048, 1152), spp=(96, 192), noise=0.015, ares=(2048, 1152), aspp=96, aframes=60),
}
SCENY = {"dzien": ("lato", "dzien", False), "zmierzch": ("zima", "zmierzch", False), "zima": ("zima", "zima", True)}
INTERIOR = ("ogrod", "salon", "sypialnia", "biuro")


def bl(ctx, p):
    return ctx.to_bl(p[0], p[1], p[2])


def auto_ekspozycja(sc, cel=0.18, bias=0.0, tmp="/tmp", chron=True):
    """Pomiar światła małym renderem (EXR liniowy, odszumiony) – ekspozycja tak, by średnia logarytmiczna jasność
    (bez najjaśniejszych okien i nieba) wypadła w szarości `cel`."""
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
    ev = min(math.log2(cel / p50), math.log2(0.85 / p95)) if chron else math.log2(cel / p50)
    ev = max(-2.5, min(3.0, ev + bias))
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


def render_domu(pid, wersja, q, ujecia=None, out=None, od_nowa=False, anim=True):
    kat = "domy" if wersja == 2 else "domy_v1"
    H = load(pid, kat).build()
    out = out or os.path.join(HERE, "out", "film", f"v{wersja}", pid)
    os.makedirs(os.path.join(out, "kadry"), exist_ok=True)
    P = Q[q]
    U = kamery.plan_ujec(H, wersja)
    if ujecia:
        U = [u for u in U if u["id"] in ujecia]
    seed = int(pid[1:]) * 7 + wersja
    czasy = {}
    for sname in ("dzien", "zmierzch", "zima"):
        grp = [u for u in U if u["scena"] == sname]
        if not grp:
            continue
        todo = [u for u in grp if od_nowa or not os.path.exists(os.path.join(out, "kadry", u["id"] + ".png"))]
        want_anim = anim and sname == "dzien" and any(u["id"] == "lotu" for u in grp)
        adir = os.path.join(out, "anim", "lotu")
        if want_anim and not od_nowa and os.path.exists(os.path.join(adir, "gotowe.json")):
            want_anim = False
        if not todo and not want_anim:
            continue
        wariant, pora, snieg = SCENY[sname]
        t0 = time.time()
        minx, miny, maxx, maxy = H.bbox
        ox, oy = (minx + maxx) / 2, (miny + maxy) / 2
        cams = [((u["cam"]["loc"][0] - ox, -(u["cam"]["loc"][1] - oy)), (u["cam"]["target"][0] - ox, -(u["cam"]["target"][1] - oy)))
                for u in grp]
        S = scena.zbuduj(H, wariant, pora, snieg=snieg, dach_t=1.0 if sname == "dzien" else None, kamery=cams,
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
            u = next(u for u in grp if u["id"] == "lotu")
            czasy["anim"] = animacja_dachu(S, u, P, adir)
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
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    render_domu(a.pid, a.wersja, a.q, a.ujecia.split(",") if a.ujecia else None, a.out, a.od_nowa, not a.bez_anim)
