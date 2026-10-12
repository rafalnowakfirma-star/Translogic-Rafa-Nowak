#!/usr/bin/env python3
"""Ponowny render wybranych panoram spaceru (np. po przestawieniu punktu w H.spacer) bez renderu całego domu.

  /home/user/tools/bpyenv/bin/python film/render_stacja.py p21 kino,laz [--wersja 2] [--q final]

Panoramy trafiają do out/film/v<wersja>/<pid>/spacer/, wpisy w spacer.json są podmieniane.
"""
import argparse
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from podglad import load  # noqa: E402
from film import scena, kamery  # noqa: E402
from film.render import panoramy, Q  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("pid")
ap.add_argument("stacje")
ap.add_argument("--wersja", type=int, default=2)
ap.add_argument("--q", default="final")
a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
ids = a.stacje.split(",")
H = load(a.pid, "domy" if a.wersja == 2 else "domy_v1").build()
out = os.path.join(HERE, "out", "film", f"v{a.wersja}", a.pid, "spacer")
st = [s for s in kamery.plan_spaceru(H) if s["id"] in ids]
U = kamery.plan_ujec(H, a.wersja)
S = scena.zbuduj(H, "lato", "dzien", snieg=False, dach_t=getattr(H, "dach_dzien", 1.0),
                 seed=int(a.pid[1:]) * 7 + a.wersja, az=U[0]["sun"])
tmp = tempfile.mkdtemp(prefix="stacja_")
panoramy(S, st, Q[a.q], tmp, od_nowa=True)
nowe = {m["id"]: m for m in json.load(open(os.path.join(tmp, "spacer.json"), encoding="utf-8"))}
fn = os.path.join(out, "spacer.json")
meta = json.load(open(fn, encoding="utf-8"))
for i, m in enumerate(meta):
    if m["id"] in nowe:
        os.replace(os.path.join(tmp, m["id"] + ".png"), os.path.join(out, m["id"] + ".png"))
        meta[i] = nowe[m["id"]]
json.dump(meta, open(fn, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("STACJE GOTOWE", ",".join(nowe), flush=True)
