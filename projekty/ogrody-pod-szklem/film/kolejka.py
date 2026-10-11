#!/usr/bin/env python3
"""Kolejka filmów: render (Blender) → scenariusz → montaż, dom po domu, z dziennikiem i wznawianiem.

  python3 film/kolejka.py                       # wszystkie domy, obie wersje
  python3 film/kolejka.py --wersje 2 --domy p01,p02 --q final
  python3 film/kolejka.py --tylko-montaz         # bez renderów (np. po zmianie montażu)
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BPY = "/home/user/tools/bpyenv/bin/python"
TTS = "/home/user/tools/ttsenv/bin/python"


def log(msg, fn):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    with open(fn, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wersje", default="2,1")
    ap.add_argument("--domy", default=",".join(f"p{i:02d}" for i in range(1, 17)))
    ap.add_argument("--q", default="final")
    ap.add_argument("--tylko-montaz", action="store_true")
    ap.add_argument("--bez-montazu", action="store_true")
    a = ap.parse_args()
    logdir = os.path.join(HERE, "out", "film", "logi")
    os.makedirs(logdir, exist_ok=True)
    main_log = os.path.join(logdir, "kolejka.log")
    env = dict(os.environ, OGRODY_SLOTY=os.environ.get("OGRODY_SLOTY", "1"))
    for w in [int(x) for x in a.wersje.split(",")]:
        for pid in a.domy.split(","):
            t0 = time.time()
            out = os.path.join(HERE, "out", "film", f"v{w}", pid)
            film = os.path.join(out, f"ogrody_v{w}_{pid}.mp4")
            if not a.tylko_montaz:
                with open(os.path.join(logdir, f"v{w}_{pid}_render.log"), "a") as lf:
                    r = subprocess.run([BPY, os.path.join(HERE, "film", "render.py"), pid, "--wersja", str(w), "--q", a.q],
                                       cwd=HERE, env=env, stdout=lf, stderr=subprocess.STDOUT)
                if r.returncode != 0:
                    log(f"v{w} {pid}: BŁĄD renderu (kod {r.returncode})", main_log)
                    continue
            # lektor: nagrania z tekstu narracji (gdy tekst nowszy niż nagrania)
            nj = os.path.join(HERE, "film", "narracja", f"v{w}", f"{pid}.json")
            lj = os.path.join(out, "lektor", "lektor.json")
            if os.path.exists(nj) and (not os.path.exists(lj) or os.path.getmtime(lj) < os.path.getmtime(nj)):
                with open(os.path.join(logdir, f"v{w}_{pid}_lektor.log"), "a") as lf:
                    subprocess.run([TTS, os.path.join(HERE, "film", "lektor.py"), pid, "--wersja", str(w)],
                                   cwd=HERE, stdout=lf, stderr=subprocess.STDOUT)
            if a.bez_montazu:
                log(f"v{w} {pid}: rendery gotowe w {time.time() - t0:.0f} s", main_log)
                continue
            with open(os.path.join(logdir, f"v{w}_{pid}_montaz.log"), "a") as lf:
                r = subprocess.run([sys.executable, os.path.join(HERE, "film", "scenariusz.py"), pid, "--wersja", str(w),
                                    "--montuj"], cwd=HERE, stdout=lf, stderr=subprocess.STDOUT)
            ok = r.returncode == 0 and os.path.exists(film)
            log(f"v{w} {pid}: {'film gotowy' if ok else 'BŁĄD montażu'} w {time.time() - t0:.0f} s", main_log)


if __name__ == "__main__":
    main()
