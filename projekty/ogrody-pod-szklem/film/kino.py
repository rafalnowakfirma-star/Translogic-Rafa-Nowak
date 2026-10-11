#!/usr/bin/env python3
"""Kino: strona do oglądania filmów na telewizorze (kolejne części filmu po ≤ 14 MB – limit plików strony).

  python3 film/kino.py --wersje 2,1 --out kino          → kino/index.html + kino/pliki/*
  python3 film/kino.py --wersje 2 --out kino_v2         → tylko wersja 2 (gdy całość nie mieści się w jednej stronie)
"""
import argparse
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

WERSJE = {2: "Wersja 2", 1: "Wersja 1 (pierwsza)"}


def czas(fn):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", fn],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def czesci_web(src, dst_dir, base, part_s=40.0, target_mb=13.6):
    """Film → części MP4 (H.264 1080p, AAC) po ~40 s, każda ≤ ~14 MB, cięte na klatkach kluczowych."""
    os.makedirs(dst_dir, exist_ok=True)
    done = sorted(glob.glob(os.path.join(dst_dir, f"{base}_*.mp4")))
    if done and os.path.getmtime(done[0]) > os.path.getmtime(src):
        return [(os.path.basename(f), czas(f)) for f in done]
    for f in done:
        os.remove(f)
    vbit = int(target_mb * 8e6 / part_s - 128e3)
    tmp = os.path.join(dst_dir, f"_{base}.mp4")
    log = os.path.join(dst_dir, f"_{base}_2pass")
    common = ["-c:v", "libx264", "-preset", "slow", "-b:v", str(vbit), "-maxrate", str(int(vbit * 1.25)),
              "-bufsize", str(int(vbit * 2)), "-g", "50", "-keyint_min", "50", "-sc_threshold", "0",
              "-pix_fmt", "yuv420p", "-profile:v", "high", "-passlogfile", log]
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src] + common + ["-pass", "1", "-an", "-f", "mp4", os.devnull], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src] + common + ["-pass", "2", "-c:a", "aac", "-b:a", "128k",
                                                                         "-movflags", "+faststart", tmp], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp, "-c", "copy", "-f", "segment", "-segment_time", str(part_s),
                    "-reset_timestamps", "1", "-segment_format", "mp4", "-segment_format_options", "movflags=+faststart",
                    os.path.join(dst_dir, f"{base}_%02d.mp4")], check=True)
    for f in glob.glob(log + "*") + [tmp]:
        if os.path.exists(f):
            os.remove(f)
    out = []
    for f in sorted(glob.glob(os.path.join(dst_dir, f"{base}_*.mp4"))):
        mb = os.path.getsize(f) / 1e6
        if mb > 15.0:
            raise SystemExit(f"{f}: {mb:.1f} MB – za duży plik")
        out.append((os.path.basename(f), czas(f)))
    return out


def plakat(src_png, dst):
    from PIL import Image
    im = Image.open(src_png).convert("RGB")
    im.thumbnail((960, 540), Image.LANCZOS)
    im.save(dst, "JPEG", quality=82, optimize=True, progressive=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wersje", default="2,1")
    ap.add_argument("--out", default=os.path.join(HERE, "kino"))
    ap.add_argument("--domy", default=None)
    a = ap.parse_args()
    out = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
    pl = os.path.join(out, "pliki")
    os.makedirs(pl, exist_ok=True)
    filmy = []
    wersje = [int(x) for x in a.wersje.split(",")]
    for w in wersje:
        for d in sorted(glob.glob(os.path.join(HERE, "out", "film", f"v{w}", "p[0-9][0-9]"))):
            pid = os.path.basename(d)
            if a.domy and pid not in a.domy.split(","):
                continue
            mp4 = os.path.join(d, f"ogrody_v{w}_{pid}.mp4")
            sb = os.path.join(d, "film.json")
            if not os.path.exists(mp4) or not os.path.exists(sb):
                continue
            s = json.load(open(sb, encoding="utf-8"))
            base = f"v{w}_{pid}"
            parts = czesci_web(mp4, pl, base)
            pos = os.path.join(d, "kadry", "lotu.png")
            if os.path.exists(pos):
                plakat(pos, os.path.join(pl, f"{base}.jpg"))
            filmy.append(dict(id=base, wersja=w, numer=s["numer"], nazwa=s["nazwa"], opis=s.get("tagline", ""),
                              czas=round(sum(t for _, t in parts), 1), plakat=f"pliki/{base}.jpg",
                              czesci=[dict(src=f"pliki/{f}", czas=round(t, 2)) for f, t in parts]))
            print("FILM", base, len(parts), "części", round(sum(t for _, t in parts)), "s", flush=True)
    tpl = open(os.path.join(HERE, "film", "kino_szablon.html"), encoding="utf-8").read()
    ws = [dict(id=w, nazwa=WERSJE[w]) for w in wersje if any(f["wersja"] == w for f in filmy)]
    rep = {
        "{{TYTUL}}": "Ogrody pod szkłem – kino",
        "{{OPIS}}": "Filmy z lektorem i spacerem po każdym domu. Na telewizorze: wybierz film strzałkami pilota i zatwierdź, "
                    "„Pełny ekran” powiększa obraz.",
        "{{STOPKA}}": "Wizualizacje koncepcyjne, wymiary orientacyjne. Lektor: syntezator mowy Piper (głos pl_PL gosia). "
                      "Meble 3D: Khronos glTF Sample Assets (Eric Chadwick i in.), CC BY 4.0 / CC0. Tekstury i HDRI: three.js (MIT), "
                      "Poly Haven (CC0). Fonty: Archivo, Hanken Grotesk, IBM Plex Mono (SIL OFL).",
        "{{FILMY}}": json.dumps(filmy, ensure_ascii=False),
        "{{WERSJE}}": json.dumps(ws, ensure_ascii=False),
    }
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(tpl)
    tot = sum(os.path.getsize(f) for f in glob.glob(os.path.join(pl, "*")))
    print(f"KINO {len(filmy)} filmów, {tot / 1e6:.0f} MB, plików {len(os.listdir(pl))}")


if __name__ == "__main__":
    main()
