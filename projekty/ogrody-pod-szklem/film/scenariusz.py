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
    "Lektor: syntezator mowy Piper (głos pl_PL gosia), sherpa-onnx.",
    "Meble i dekoracje 3D: Khronos glTF Sample Assets (Eric Chadwick i in.), CC BY 4.0 / CC0.",
    "Tekstury i HDRI: three.js examples (MIT), Poly Haven (CC0).",
]


def _m2(x):
    return f"{x:.0f} m²"


def fakty_domu(H):
    """Najważniejsze liczby domu: [wartość, opis] – powierzchnia, ogród, tarasy, kondygnacje."""
    ter = [r for r in H.rooms if r.outdoor and r.level > H.ground]
    fakty = [[_m2(H.area["uzytkowa"]), "powierzchnia użytkowa"], [_m2(H.area["ogrod"]), "ogród pod szkłem"]]
    if ter:
        fakty.append([_m2(sum(r.poly.area for r in ter)), "tarasy na dachu"])
    elif H.area.get("zewn", 0) > 1:
        fakty.append([_m2(H.area["zewn"]), "tarasy i patio"])
    nlev = len([i for i in H.L if any(not r.outdoor and r.kind not in ("void", "ogrod_void") for r in H.L[i]["rooms"])])
    fakty.append([str(nlev), "kondygnacje" if nlev in (2, 3, 4) else ("kondygnacja" if nlev == 1 else "kondygnacji")])
    return fakty


def plany(H, pid, out):
    """Rzuty kondygnacji jako PNG (białe tło) – osobno dla każdej wersji domu."""
    from silnik.rzut import plan_level
    d = os.path.abspath(os.path.join(out, "plany"))     # Chromium potrzebuje bezwzględnej ścieżki file://
    os.makedirs(d, exist_ok=True)
    res = []
    for idx in sorted(H.L):
        if not any(not r.outdoor and r.kind not in ("void", "ogrod_void") for r in H.L[idx]["rooms"]):
            continue
        svg = os.path.join(d, f"rzut_{idx}.svg")
        png = svg.replace(".svg", ".png")
        if not os.path.exists(png) or _zly_zrzut(png):
            open(svg, "w", encoding="utf-8").write(plan_level(H, idx, f"{pid}f{idx}"))
            shot(svg, png, width=1800)
            _przytnij(png)
            if _zly_zrzut(png):
                raise RuntimeError(f"nieudany zrzut rzutu {png}")
        res.append((idx, png))
    return res


def _zly_zrzut(png):
    """Strona błędu Chromium zamiast rysunku: prawie brak zieleni terenu i ciemnych ścian."""
    im = Image.open(png).convert("RGB").resize((90, 120))
    px = list(im.getdata())
    dark = sum(1 for r, g, b in px if r + g + b < 150)
    green = sum(1 for r, g, b in px if g > r + 12 and g > b + 8)
    return dark < 20 and green < 40


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
    lj = os.path.join(out, "lektor", "lektor.json")
    L = json.load(open(lj, encoding="utf-8")) if os.path.exists(lj) else {}
    nj = os.path.join(HERE, "film", "narracja", f"v{wersja}", f"{pid}.json")
    N = json.load(open(nj, encoding="utf-8")) if os.path.exists(nj) else {}
    sj = os.path.join(out, "spacer", "spacer.json")
    SP = json.load(open(sj, encoding="utf-8")) if os.path.exists(sj) else []
    gs = [r for r in H.rooms if r.kind == "ogrod"]
    fakty = fakty_domu(H)
    sh = []

    def lek(key, start=0.6):
        v = L.get(key)
        return dict(plik=v["plik"], start=start) if v else None

    def add(d, key=None, start=0.6):
        if key:
            lk = lek(key, start)
            if lk:
                d["lektor"] = lk
        sh.append(d)

    def kadr(uid, czas=6.0, key=None):
        u = U.get(uid)
        if not u or not os.path.exists(os.path.join(out, "kadry", uid + ".png")):
            return False
        add(dict(typ="kadr", obraz=f"kadry/{uid}.png", czas=czas, ruch=u.get("ruch", "zoom_in"),
                 fokus=u.get("fokus", [0.5, 0.5]), podpis=u.get("podpis", ""), podpis2=u.get("podpis2", "")), key)
        return True

    tlo = "kadry/lotu.png" if os.path.exists(os.path.join(out, "kadry", "lotu.png")) else None
    add(dict(typ="tytul", tlo=tlo, czas=5.0), "tytul", 1.3)
    kadr("lotu", 7.0, "lotu")
    an = klatki_animacji(out)
    g0 = gs[0] if gs else None
    if an:
        add(dict(typ="animacja", klatki=an["klatki"], fps=25, fps_render=an["fps_render"],
                 podpis="Dach ogrodu", podpis2=(DACH.get(g0.roof_type, "dach") + " – latem otwarty") if g0 else ""), "dach", 0.4)
    if SP:
        for i, st in enumerate(SP):
            if not os.path.exists(os.path.join(out, st["obraz"])):
                continue
            add(dict(typ="panorama", obraz=st["obraz"], lon=st["lon"], lat=st["lat"], ruch=st["ruch"], czas=6.0,
                     przejscie="krok", podpis="Spacer po domu" if st["room"] is None else st["podpis"],
                     podpis2="przed wejściem" if st["room"] is None else ""), f"spacer__{st['id']}", 0.5)
    else:
        for uid in ("ogrod", "salon", "sypialnia", "biuro", "taras", "patio"):
            kadr(uid)
    for k, (idx, png) in enumerate(plany(H, pid, out)):
        add(dict(typ="rzut", obraz=os.path.relpath(png, out), czas=5.5 if k else 6.0,
                 podpis=POZIOM.get(idx, f"Rzut poziomu {idx}")), "rzuty" if k == 0 else None)
    kadr("zmierzch", 6.5, "zmierzch")
    kadr("zima", 6.0, "zima")
    tz = "kadry/zmierzch.png" if os.path.exists(os.path.join(out, "kadry", "zmierzch.png")) else tlo
    if N.get("zalety") or N.get("wady"):
        add(dict(typ="zalety_wady", tlo=tz, zalety=N.get("zalety", []), wady=N.get("wady", []), czas=12.0), "zalety_wady", 0.8)
    add(dict(typ="koniec", tlo=tz, czas=7.0), "koniec", 0.8)
    sb = dict(pid=pid, wersja=wersja, numer=pid.upper(), nazwa=H.name, tagline=H.tagline,
              seria=f"Ogrody pod szkłem · wersja {wersja}", fakty=fakty, napisy_koncowe=NAPISY,
              ujecia=sh, muzyka=True, muzyka_glosnosc=-2, web=False, crf=21, wyjscie=f"ogrody_v{wersja}_{pid}.mp4")
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
