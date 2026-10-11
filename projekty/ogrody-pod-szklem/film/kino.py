#!/usr/bin/env python3
"""Kino: strona do oglądania filmów na telewizorze (film w częściach po ≤ 19 MB, odtwarzanych jedna po drugiej).

  python3 film/kino.py --wersje 2,1 --out kino          → kino/index.html + kino/pliki/* (plakaty i części filmów)
  python3 film/kino.py --wersje 2,1 --out kino --zasoby kino/zasoby.json
        → części filmów wskazują na zasoby strony (asset store, mapa: nazwa pliku → url zwrócony przy wysyłce)
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


def czesci_kopia(src, dst_dir, base, limit_mb=18.5):
    """Film → części MP4 bez ponownego kodowania (jakość oryginału): cięcia na klatkach kluczowych dobrane tak,
    by każda część miała ≤ limit_mb (zasoby strony przyjmują pliki do 20 MiB)."""
    os.makedirs(dst_dir, exist_ok=True)
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "packet=pts_time,size,flags",
                        "-of", "csv=p=0", src], capture_output=True, text=True, check=True)
    gopy = []                                   # [czas początku, bajty] kolejnych grup klatek
    for line in r.stdout.split():
        t, sz, fl = line.split(",")[:3]
        if "K" in fl or not gopy:
            gopy.append([float(t), 0])
        gopy[-1][1] += int(sz)
    gopy.sort()
    dur = czas(src)
    audio_bps = 170e3 / 8                       # AAC ~164 kb/s + narzut kontenera
    limit = limit_mb * 1e6
    ciecia, acc, t0 = [], 0.0, gopy[0][0]
    for i, (t, b) in enumerate(gopy):
        t_nast = gopy[i + 1][0] if i + 1 < len(gopy) else dur
        dodatek = b + audio_bps * (t_nast - t)
        if acc > 0 and acc + dodatek > limit:
            ciecia.append(t)
            acc, t0 = 0.0, t
        acc += dodatek
    for f in glob.glob(os.path.join(dst_dir, f"{base}_*.mp4")):
        os.remove(f)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", src, "-map", "0", "-c", "copy", "-f", "segment",
           "-reset_timestamps", "1", "-segment_format", "mp4", "-segment_format_options", "movflags=+faststart"]
    if ciecia:
        cmd += ["-segment_times", ",".join(f"{t:.3f}" for t in ciecia)]
    else:
        cmd += ["-segment_time", "100000"]
    subprocess.run(cmd + [os.path.join(dst_dir, f"{base}_%02d.mp4")], check=True)
    out = []
    for f in sorted(glob.glob(os.path.join(dst_dir, f"{base}_*.mp4"))):
        if os.path.getsize(f) / 1e6 > max(19.8, limit_mb + 1.3):
            return None                         # wyjątkowo gęsty fragment – lepiej przekodować
        out.append((os.path.basename(f), czas(f)))
    return out


def wersja_tv(src, dst_dir, base, vbit=1150e3, abit="80k", limit_mb=13.5):
    """Lżejsza wersja filmu do stron publicznych (720p, ~1,2 Mb/s, 2 przebiegi) pocięta na części ≤ limit_mb
    (pliki strony mogą mieć do 15 MB). Gotowe części nowsze niż film – bez zmian."""
    os.makedirs(dst_dir, exist_ok=True)
    done = sorted(glob.glob(os.path.join(dst_dir, f"{base}_*.mp4")))
    if done and all(os.path.getmtime(f) > os.path.getmtime(src) for f in done):
        return [(os.path.basename(f), czas(f)) for f in done]
    tmp = os.path.join(dst_dir, f"_{base}_720p.mp4")
    log = os.path.join(dst_dir, f"_{base}_2pass")
    v = ["-vf", "scale=1280:720:flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-b:v", str(int(vbit)),
         "-maxrate", str(int(vbit * 1.5)), "-bufsize", str(int(vbit * 3)), "-g", "50", "-keyint_min", "25",
         "-pix_fmt", "yuv420p", "-profile:v", "high", "-level:v", "3.1", "-passlogfile", log]
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src] + v + ["-pass", "1", "-an", "-f", "mp4", os.devnull], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src] + v + ["-pass", "2", "-c:a", "aac", "-b:a", abit,
                                                                    "-movflags", "+faststart", tmp], check=True)
    out = czesci_kopia(tmp, dst_dir, base, limit_mb=limit_mb)
    for f in glob.glob(log + "*") + [tmp]:
        if os.path.exists(f):
            os.remove(f)
    if out is None or any(os.path.getsize(os.path.join(dst_dir, f)) > 14.9e6 for f, _ in out):
        raise SystemExit(f"{base}: część wersji TV za duża")
    return out


def czesci(src, dst_dir, base):
    """Części gotowe i nowsze niż film – bez zmian; inaczej kopia strumienia, a gdy część za duża – przekodowanie."""
    done = sorted(glob.glob(os.path.join(dst_dir, f"{base}_*.mp4")))
    if done and all(os.path.getmtime(f) > os.path.getmtime(src) for f in done):
        return [(os.path.basename(f), czas(f)) for f in done]
    return czesci_kopia(src, dst_dir, base) or czesci_web(src, dst_dir, base)


def czesci_web(src, dst_dir, base, part_s=40.0, target_mb=16.0, limit_mb=19.8):
    """Film → części MP4 (H.264 1080p, AAC) po ~45 s, każda ≤ 19,5 MB, cięte na klatkach kluczowych."""
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
        if mb > limit_mb:
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
    ap.add_argument("--zasoby", default=None, help="JSON: nazwa pliku części → url zasobu strony")
    a = ap.parse_args()
    zasoby = json.load(open(a.zasoby, encoding="utf-8")) if a.zasoby and os.path.exists(a.zasoby) else {}
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
            parts = czesci(mp4, pl, base)
            pos = os.path.join(d, "kadry", "lotu.png")
            if os.path.exists(pos):
                plakat(pos, os.path.join(pl, f"{base}.jpg"))
            filmy.append(dict(id=base, wersja=w, numer=s["numer"], nazwa=s["nazwa"], opis=s.get("tagline", ""),
                              czas=round(sum(t for _, t in parts), 1), plakat=f"pliki/{base}.jpg",
                              czesci=[dict(src=zasoby.get(f, f"pliki/{f}"), czas=round(t, 2)) for f, t in parts]))
            print("FILM", base, len(parts), "części", round(sum(t for _, t in parts)), "s", flush=True)
    tpl = open(os.path.join(HERE, "film", "kino_szablon.html"), encoding="utf-8").read()
    ws = [dict(id=w, nazwa=WERSJE[w]) for w in wersje if any(f["wersja"] == w for f in filmy)]
    rep = {
        "{{TYTUL}}": "Kino ogrodów pod szkłem",
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
    brak = [c["src"] for f in filmy for c in f["czesci"] if c["src"].startswith("pliki/")]
    print(f"KINO {len(filmy)} filmów, {tot / 1e6:.0f} MB, plików {len(os.listdir(pl))}, części bez zasobu: {len(brak)}")
    json.dump(brak, open(os.path.join(out, "do_wyslania.json"), "w"), indent=0)


if __name__ == "__main__":
    main()
