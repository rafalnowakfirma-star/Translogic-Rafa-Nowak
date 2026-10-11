#!/usr/bin/env python3
"""Po każdym nowym filmie: odświeża wszystkie miejsca, w których filmy są do obejrzenia.

  python3 film/aktualizuj.py            → etap 1: strona TV (prywatna) – lista części do wysłania do zasobów;
                                          strony publiczne tv/* – zmienione pliki (tv/<sekcja>/zmiany.json);
                                          folder „domy” (pendrive) – commit i push gałęzi ogrody-pendrive;
                                          pojedyncze pliki 720p do wysłania w rozmowie (pendrive/720p)
  python3 film/aktualizuj.py --portal   → etap 2 (po dopisaniu zasobów do kino/zasoby.json): przebudowa strony TV
                                          i lista zmienionych plików (portal/zmiany.json)
Publikację (Artifact) wykonuje się osobno – skrypt tylko przygotowuje pliki i listy.
"""
import argparse
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
SEKCJE = {"v2a": (2, "p01-p10", "domy 1–10"), "v2b": (2, "p11-p20", "domy 11–20"),
          "v1a": (1, "p01-p08", "archiwum 1–8"), "v1b": (1, "p09-p16", "archiwum 9–16")}


def run(cmd, **kw):
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-3000:])
        raise SystemExit(f"błąd: {' '.join(cmd[:3])}…")
    return r.stdout


def zmiany(katalog):
    out = run([PY, "film/zmienione.py", katalog]).strip().splitlines()
    m = json.loads(out[0])
    json.dump(m, open(os.path.join(HERE, katalog, "zmiany.json"), "w", encoding="utf-8"), ensure_ascii=False)
    return m, out[-1]


def portal():
    linki = open(os.path.join(HERE, "portal", "linki.json"), encoding="utf-8").read()
    print(run([PY, "film/portal.py", "--wersja", "2", "--out", "portal", "--linki", linki]).strip().splitlines()[-1])
    wys = json.load(open(os.path.join(HERE, "portal", "do_wyslania.json")))
    return wys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--portal", action="store_true", help="tylko etap 2: strona TV po dopisaniu zasobów")
    ap.add_argument("--bez-gita", action="store_true")
    a = ap.parse_args()
    if a.portal:
        portal()
        m, opis = zmiany("portal")
        print("PORTAL zmiany:", opis)
        return
    wys = portal()
    print("ZASOBY DO WYSŁANIA:", json.dumps(wys))
    linki = open(os.path.join(HERE, "tv", "linki.json"), encoding="utf-8").read()
    for s, (w, domy, tyt) in SEKCJE.items():
        print(run([PY, "film/portal.py", "--wersja", str(w), "--domy", domy, "--publiczny", "--out", f"tv/{s}",
                   "--tytul", f"Ogrody pod szkłem TV · {tyt}", "--linki", linki, "--sekcje", "tv/sekcje.json",
                   "--sekcja", s]).strip().splitlines()[-1])
        m, opis = zmiany(f"tv/{s}")
        print(f"TV {s} zmiany:", opis)
    # pendrive: folder „domy” + gałąź ogrody-pendrive
    print(run([PY, "film/pendrive.py", "--out", os.path.join(HERE, "pendrive", "domy")]).strip().splitlines()[-1])
    pd = os.path.join(HERE, "pendrive")
    if not a.bez_gita:
        subprocess.run(["git", "add", "-A", "README.md", "domy"], cwd=pd, check=True)
        st = subprocess.run(["git", "status", "--porcelain"], cwd=pd, capture_output=True, text=True).stdout.strip()
        if st:
            filmy = sorted({os.path.basename(f).split("_film")[0] for f in glob.glob(os.path.join(pd, "domy", "*", "*", "*_film.mp4"))})
            msg = (f"Folder „domy”: {len(filmy)} filmów ({', '.join(f.split('_')[0] for f in filmy)})\n\n"
                   "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
                   "Claude-Session: https://claude.ai/code/session_01UWecZLqboZ3MmxhQRX6os1")
            subprocess.run(["git", "commit", "-q", "-m", msg], cwd=pd, check=True)
            for proba in range(4):
                r = subprocess.run(["git", "push", "-q", "origin", "ogrody-pendrive"], cwd=pd, capture_output=True, text=True)
                if r.returncode == 0:
                    print("PENDRIVE: wysłano na GitHub")
                    break
                import time
                time.sleep(2 ** (proba + 1))
            else:
                print("PENDRIVE: push nieudany:", r.stderr[-500:])
        else:
            print("PENDRIVE: bez zmian")
    # pojedyncze pliki 720p (≤ 30 MB) do wysłania w rozmowie
    os.makedirs(os.path.join(pd, "720p"), exist_ok=True)
    nowe = []
    for s in SEKCJE:
        for pierwsza in sorted(glob.glob(os.path.join(HERE, "tv", s, "pliki", "filmy", "v*_p??_00.mp4"))):
            baza = os.path.basename(pierwsza)[:-7]                        # v2_p01
            w, pid = baza.split("_")
            kat = glob.glob(os.path.join(pd, "domy", "wersja_2" if w == "v2" else "wersja_1_archiwum", f"{pid.upper()}_*"))
            nazwa = os.path.basename(kat[0]) if kat else pid.upper()
            dst = os.path.join(pd, "720p", f"{nazwa}{'' if w == 'v2' else '_archiwum'}_film_720p.mp4")
            czesci = sorted(glob.glob(os.path.join(HERE, "tv", s, "pliki", "filmy", f"{baza}_*.mp4")))
            if os.path.exists(dst) and os.path.getmtime(dst) >= max(os.path.getmtime(c) for c in czesci):
                continue
            lst = os.path.join(pd, "720p", "_lista.txt")
            open(lst, "w").write("".join(f"file '{c}'\n" for c in czesci))
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                            "-movflags", "+faststart", dst], check=True)
            os.remove(lst)
            nowe.append(dst)
    print("NOWE 720p:", json.dumps(nowe))


if __name__ == "__main__":
    main()
