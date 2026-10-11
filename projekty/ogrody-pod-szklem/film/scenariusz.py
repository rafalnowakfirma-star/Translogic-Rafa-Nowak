#!/usr/bin/env python3
"""Scenariusz filmu jednego domu: rzuty PNG, pełne klatki animacji dachu, storyboard JSON dla film/montaz.py.

  python3 film/scenariusz.py p01 --wersja 2          → out/film/v2/p01/film.json (+ plany/, anim/lotu_pelne/)
  python3 film/scenariusz.py p01 --wersja 2 --montuj  → od razu składa film
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from PIL import Image, ImageFilter  # noqa: E402

from podglad import load, shot  # noqa: E402
from film.kamery import DACH, STYL  # noqa: E402

POZIOM = {0: "Rzut parteru", 1: "Rzut piętra", 2: "Rzut drugiego piętra", 3: "Rzut wieży"}
NAPISY = [
    "Wizualizacje koncepcyjne – wymiary orientacyjne, to nie jest projekt budowlany.",
    "Meble i dekoracje 3D: Khronos glTF Sample Assets (Eric Chadwick i in.), CC BY 4.0 / CC0.",
    "Tekstury i HDRI: three.js examples (MIT), Poly Haven (CC0).",
]


def _m2(x):
    return f"{x:.0f} m²"


def plany(H, pid, out):
    """Rzuty kondygnacji jako PNG (białe tło) – osobno dla każdej wersji domu."""
    from silnik.rzut import plan_level
    d = os.path.join(out, "plany")
    os.makedirs(d, exist_ok=True)
    res = []
    for idx in sorted(H.L):
        if not any(not r.outdoor and r.kind not in ("void", "ogrod_void") for r in H.L[idx]["rooms"]):
            continue
        svg = os.path.join(d, f"rzut_{idx}.svg")
        png = svg.replace(".svg", ".png")
        if not os.path.exists(png):
            open(svg, "w", encoding="utf-8").write(plan_level(H, idx, f"{pid}f{idx}"))
            shot(svg, png, width=1800)
            _przytnij(png)
        res.append((idx, png))
    return res


def _przytnij(png):
    """Obcina puste białe marginesy zrzutu (Chromium dokłada pasek u dołu)."""
    im = Image.open(png).convert("RGB")
    g = im.convert("L").point(lambda v: 255 if v < 245 else 0)
    bb = g.getbbox()
    if bb:
        x0, y0, x1, y1 = bb
        m = 30
        im = im.crop((max(0, x0 - m), max(0, y0 - m), min(im.width, x1 + m), min(im.height, y1 + m)))
    im.save(png)


def klatki_animacji(out):
    """Wkleja wycinki z dachem w ruchu na pełną klatkę startową (miękka krawędź) → anim/lotu_pelne/%04d.png."""
    src = os.path.join(out, "anim", "lotu")
    meta_fn = os.path.join(src, "gotowe.json")
    if not os.path.exists(meta_fn):
        return None
    meta = json.load(open(meta_fn))
    dst = os.path.join(out, "anim", "lotu_pelne")
    os.makedirs(dst, exist_ok=True)
    base = Image.open(os.path.join(src, "0000.png")).convert("RGB")
    W, H = base.size
    px = meta.get("px")
    n = meta["n"]
    mask = None
    for i in range(n + 1):
        fn = os.path.join(dst, f"{i:04d}.png")
        if os.path.exists(fn):
            continue
        if i == 0 or not px:
            Image.open(os.path.join(src, f"{i:04d}.png")).convert("RGB").save(fn)
            continue
        crop = Image.open(os.path.join(src, f"{i:04d}.png")).convert("RGB")
        x0, y0 = px[0], px[1]
        if mask is None or mask.size != crop.size:
            mask = Image.new("L", crop.size, 0)
            f = max(6, min(crop.size) // 14)
            mask.paste(255, (f, f, crop.size[0] - f, crop.size[1] - f))
            mask = mask.filter(ImageFilter.GaussianBlur(f / 2.5))
            # krawędź kadru – bez wtapiania
            if x0 <= 0 or y0 <= 0 or x0 + crop.size[0] >= W or y0 + crop.size[1] >= H:
                m2 = Image.new("L", crop.size, 0)
                l = f if x0 > 0 else 0
                t = f if y0 > 0 else 0
                rr = crop.size[0] - (f if x0 + crop.size[0] < W else 0)
                bb = crop.size[1] - (f if y0 + crop.size[1] < H else 0)
                m2.paste(255, (l, t, rr, bb))
                mask = m2.filter(ImageFilter.GaussianBlur(f / 2.5))
        fr = base.copy()
        fr.paste(crop, (x0, y0), mask)
        fr.save(fn)
    return dict(klatki="anim/lotu_pelne/%04d.png", n=n + 1, fps_render=meta.get("fps_render", 12.5))


def scenariusz(pid, wersja, out=None):
    kat = "domy" if wersja == 2 else "domy_v1"
    H = load(pid, kat).build()
    out = out or os.path.join(HERE, "out", "film", f"v{wersja}", pid)
    info = json.load(open(os.path.join(out, "kadry.json"), encoding="utf-8"))
    U = {u["id"]: u for u in info["ujecia"]}
    gs = [r for r in H.all_rooms if r.kind == "ogrod"]
    ter = [r for r in H.rooms if r.outdoor and r.level > min(H.L)]
    fakty = [[_m2(H.area["uzytkowa"]), "powierzchnia użytkowa"], [_m2(H.area["ogrod"]), "ogród pod szkłem"]]
    if ter:
        fakty.append([_m2(sum(r.poly.area for r in ter)), "tarasy na dachu"])
    elif H.area.get("zewn", 0) > 1:
        fakty.append([_m2(H.area["zewn"]), "tarasy i patio"])
    nlev = len([i for i in H.L if any(not r.outdoor and r.kind not in ("void", "ogrod_void") for r in H.L[i]["rooms"])])
    fakty.append([str(nlev), "kondygnacje" if nlev in (2, 3, 4) else ("kondygnacja" if nlev == 1 else "kondygnacji")])
    sh = []

    def kadr(uid, czas=6.0):
        u = U.get(uid)
        if not u or not os.path.exists(os.path.join(out, "kadry", uid + ".png")):
            return
        sh.append(dict(typ="kadr", obraz=f"kadry/{uid}.png", czas=czas, ruch=u.get("ruch", "zoom_in"),
                       fokus=u.get("fokus", [0.5, 0.5]), podpis=u.get("podpis", ""), podpis2=u.get("podpis2", "")))

    tlo = "kadry/lotu.png" if os.path.exists(os.path.join(out, "kadry", "lotu.png")) else None
    sh.append(dict(typ="tytul", tlo=tlo, czas=5.0))
    an = klatki_animacji(out)
    if an:
        u = U.get("lotu", {})
        g0 = gs[0] if gs else None
        sh.append(dict(typ="animacja", klatki=an["klatki"], fps=25, fps_render=an["fps_render"],
                       podpis=u.get("podpis", "Z lotu ptaka"),
                       podpis2=(DACH.get(g0.roof_type, "dach") + " ogrodu otwiera się na lato").capitalize() if g0 else ""))
    else:
        kadr("lotu", 6.0)
    for uid in ("ogrod", "salon", "sypialnia", "biuro", "taras", "patio"):
        kadr(uid)
    for idx, png in plany(H, pid, out):
        sh.append(dict(typ="rzut", obraz=os.path.relpath(png, out), czas=5.5, podpis=POZIOM.get(idx, f"Rzut poziomu {idx}")))
    kadr("zmierzch", 6.5)
    kadr("zima", 6.0)
    sh.append(dict(typ="koniec", tlo="kadry/zmierzch.png" if os.path.exists(os.path.join(out, "kadry", "zmierzch.png")) else tlo,
                   czas=7.0))
    sb = dict(pid=pid, wersja=wersja, numer=pid.upper(), nazwa=H.name, tagline=H.tagline,
              seria=f"Ogrody pod szkłem · wersja {wersja}", fakty=fakty, napisy_koncowe=NAPISY,
              ujecia=sh, muzyka=True, wyjscie=f"ogrody_v{wersja}_{pid}.mp4")
    fn = os.path.join(out, "film.json")
    json.dump(sb, open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return fn


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pid")
    ap.add_argument("--wersja", type=int, default=2)
    ap.add_argument("--out", default=None)
    ap.add_argument("--montuj", action="store_true")
    ap.add_argument("--podglad", action="store_true")
    a = ap.parse_args()
    fn = scenariusz(a.pid, a.wersja, a.out)
    print(fn)
    if a.montuj:
        import subprocess
        subprocess.run([sys.executable, os.path.join(HERE, "film", "montaz.py"), fn] + (["--podglad"] if a.podglad else []),
                       check=True)
