#!/usr/bin/env python3
"""Podgląd projektu: buduje dom, zapisuje SVG rzutów i robi z nich PNG (Chromium).

Użycie:  python3 podglad.py p01            → out/p01/*.svg i *.png
         python3 podglad.py p01 --bez-png  → tylko SVG
"""
import importlib
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def load(pid):
    files = glob.glob(os.path.join(HERE, "domy", f"{pid}_*.py"))
    if not files:
        raise SystemExit(f"brak pliku domy/{pid}_*.py")
    name = os.path.splitext(os.path.basename(files[0]))[0]
    mod = importlib.import_module(f"domy.{name}")
    importlib.reload(mod)
    return mod.H


def shot(svg_path, png_path, width=1400):
    css = open(os.path.join(HERE, "silnik", "rysunki.css"), encoding="utf-8").read()
    svg = open(svg_path, encoding="utf-8").read()
    html = f"<!doctype html><html><head><meta charset='utf-8'><style>body{{margin:0;background:#fff}}{css}</style></head><body>{svg}</body></html>"
    tmp = png_path.replace(".png", ".html")
    open(tmp, "w", encoding="utf-8").write(html)
    import re
    m = re.search(r'viewBox="0 0 (\d+) (\d+)"', svg)
    w, h = (int(m.group(1)), int(m.group(2))) if m else (1200, 900)
    W = width
    H = int(h * W / w) + 4
    subprocess.run([CHROME, "--headless", "--no-sandbox", "--hide-scrollbars", f"--window-size={W},{H}",
                    f"--screenshot={png_path}", "file://" + tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    os.remove(tmp)


def main():
    pid = sys.argv[1]
    nopng = "--bez-png" in sys.argv
    from silnik.rzut import plan_level, plan_roof
    from silnik.przekroj import section
    H = load(pid).build()
    out = os.path.join(HERE, "out", pid)
    os.makedirs(out, exist_ok=True)
    files = []
    for idx in sorted(H.L):
        svg = plan_level(H, idx, f"{pid}l{idx}")
        fn = os.path.join(out, f"rzut_{idx}.svg")
        open(fn, "w", encoding="utf-8").write(svg)
        files.append(fn)
    fn = os.path.join(out, "dach.svg")
    open(fn, "w", encoding="utf-8").write(plan_roof(H, f"{pid}d"))
    files.append(fn)
    for i, (name, a, b) in enumerate(H.cuts):
        fn = os.path.join(out, f"przekroj_{i}.svg")
        open(fn, "w", encoding="utf-8").write(section(H, name, a, b, f"{pid}s{i}"))
        files.append(fn)
    print(f"{H.pid} {H.name}: pow. użytkowa {H.area['uzytkowa']:.1f} m², ogród {H.area['ogrod']:.1f} m², "
          f"patio sezonowe {H.area['sezon']:.1f} m², tarasy/patio {H.area['zewn']:.1f} m²")
    for idx, r, a in H.room_areas:
        print(f"  L{idx} {r.key:6s} {r.name:28s} {a:6.1f} m²")
    for w in H.warnings:
        print("  UWAGA:", w)
    if not nopng:
        for fn in files:
            shot(fn, fn.replace(".svg", ".png"))
        print("PNG:", ", ".join(os.path.basename(f).replace(".svg", ".png") for f in files))


if __name__ == "__main__":
    main()
