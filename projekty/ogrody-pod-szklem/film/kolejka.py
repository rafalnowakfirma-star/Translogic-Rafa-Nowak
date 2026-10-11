#!/usr/bin/env python3
"""Kolejka filmów: render (Blender) → scenariusz → montaż, dom po domu, z dziennikiem i wznawianiem.

  python3 film/kolejka.py                       # wszystkie domy, obie wersje
  python3 film/kolejka.py --wersje 2 --domy p01,p02 --q final
  python3 film/kolejka.py --tylko-montaz         # bez renderów (np. po zmianie montażu)
"""
import argparse
import os
import queue
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BPY = "/home/user/tools/bpyenv/bin/python"
TTS = "/home/user/tools/ttsenv/bin/python"


def log(msg, fn):
    line = time.strftime("%H:%M:%S ") + msg
    print(line, flush=True)
    with open(fn, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def domy_wersji(w):
    """p01…p20 dla wersji 2 (katalog domy/), p01…p16 dla wersji 1 (domy_v1/); bez domu testowego p99."""
    kat = os.path.join(HERE, "domy" if w == 2 else "domy_v1")
    return sorted({f[:3] for f in os.listdir(kat) if f[0] == "p" and f[1:3].isdigit() and f.endswith(".py")} - {"p99"})


def gotowy(out, film):
    """Film nowszy niż rendery i nagrania lektora – dom można pominąć przy wznawianiu kolejki."""
    if not os.path.exists(film):
        return False
    deps = [os.path.join(out, "kadry.json"), os.path.join(out, "lektor", "lektor.json")]
    return all(os.path.getmtime(film) > os.path.getmtime(d) for d in deps if os.path.exists(d))


def obrobka(w, pid, t0, bez_montazu, logdir, main_log):
    """Lektor (gdy tekst nowszy niż nagrania) i montaż – w osobnym wątku, równolegle z renderem następnego domu."""
    out = os.path.join(HERE, "out", "film", f"v{w}", pid)
    film = os.path.join(out, f"ogrody_v{w}_{pid}.mp4")
    nj = os.path.join(HERE, "film", "narracja", f"v{w}", f"{pid}.json")
    lj = os.path.join(out, "lektor", "lektor.json")
    if os.path.exists(nj) and (not os.path.exists(lj) or os.path.getmtime(lj) < os.path.getmtime(nj)):
        with open(os.path.join(logdir, f"v{w}_{pid}_lektor.log"), "a") as lf:
            subprocess.run([TTS, os.path.join(HERE, "film", "lektor.py"), pid, "--wersja", str(w)],
                           cwd=HERE, stdout=lf, stderr=subprocess.STDOUT)
    if bez_montazu:
        log(f"v{w} {pid}: rendery gotowe w {time.time() - t0:.0f} s", main_log)
        return
    t1 = time.time()
    with open(os.path.join(logdir, f"v{w}_{pid}_montaz.log"), "a") as lf:
        r = subprocess.run([sys.executable, os.path.join(HERE, "film", "scenariusz.py"), pid, "--wersja", str(w),
                            "--montuj"], cwd=HERE, stdout=lf, stderr=subprocess.STDOUT)
    ok = r.returncode == 0 and os.path.exists(film)
    log(f"v{w} {pid}: {'film gotowy' if ok else 'BŁĄD montażu'} (montaż {time.time() - t1:.0f} s, "
        f"razem {time.time() - t0:.0f} s)", main_log)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wersje", default="2,1")
    ap.add_argument("--domy", default=None, help="np. p01,p02 (domyślnie wszystkie domy danej wersji)")
    ap.add_argument("--q", default="final")
    ap.add_argument("--tylko-montaz", action="store_true")
    ap.add_argument("--bez-montazu", action="store_true")
    ap.add_argument("--od-nowa", action="store_true", help="montuj także domy z gotowym filmem")
    a = ap.parse_args()
    logdir = os.path.join(HERE, "out", "film", "logi")
    os.makedirs(logdir, exist_ok=True)
    main_log = os.path.join(logdir, "kolejka.log")
    env = dict(os.environ, OGRODY_SLOTY=os.environ.get("OGRODY_SLOTY", "1"))
    zadania = queue.Queue()

    def pracownik():
        while True:
            z = zadania.get()
            if z is None:
                return
            try:
                obrobka(*z)
            except Exception as e:  # noqa: BLE001 – błąd jednego filmu nie zatrzymuje kolejki
                log(f"v{z[0]} {z[1]}: BŁĄD obróbki: {e}", z[5])

    th = threading.Thread(target=pracownik, daemon=True)
    th.start()
    for w in [int(x) for x in a.wersje.split(",")]:
        for pid in (a.domy.split(",") if a.domy else domy_wersji(w)):
            t0 = time.time()
            out = os.path.join(HERE, "out", "film", f"v{w}", pid)
            film = os.path.join(out, f"ogrody_v{w}_{pid}.mp4")
            if not a.od_nowa and not a.tylko_montaz and gotowy(out, film):
                log(f"v{w} {pid}: film już gotowy – pomijam", main_log)
                continue
            if not a.tylko_montaz:
                log(f"v{w} {pid}: render…", main_log)
                with open(os.path.join(logdir, f"v{w}_{pid}_render.log"), "a") as lf:
                    r = subprocess.run([BPY, os.path.join(HERE, "film", "render.py"), pid, "--wersja", str(w), "--q", a.q],
                                       cwd=HERE, env=env, stdout=lf, stderr=subprocess.STDOUT)
                if r.returncode != 0:
                    log(f"v{w} {pid}: BŁĄD renderu (kod {r.returncode})", main_log)
                    continue
                log(f"v{w} {pid}: render gotowy w {time.time() - t0:.0f} s", main_log)
            zadania.put((w, pid, t0, a.bez_montazu, logdir, main_log))
    zadania.put(None)
    th.join()
    log("KONIEC KOLEJKI", main_log)


if __name__ == "__main__":
    main()
