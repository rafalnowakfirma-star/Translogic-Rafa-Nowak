#!/usr/bin/env python3
"""Ogrody pod szkłem TV: jedna strona na telewizor – wszystkie domy: film, zdjęcia, rzuty, liczby, zalety i wady, opis.

  python3 film/portal.py --wersja 2 --out portal --zasoby kino/zasoby.json
        → portal/index.html + portal/pliki/<dom>/*  (zdjęcia i rzuty publikowane jako pliki strony)
          części filmów → kino/pliki/*.mp4 (wysyłane do zasobów strony; mapa nazwa → url w kino/zasoby.json)
          portal/do_wyslania.json – części filmów, których jeszcze nie ma w zasobach (film pokazany jako „w przygotowaniu”)

Zdjęcia: kadry z filmu (out/film/v<w>/<dom>/kadry), widoki ze spaceru (panoramy), a gdy domu jeszcze nie wyrenderowano –
podglądy 3D tej samej wersji projektu.
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from PIL import Image  # noqa: E402

from podglad import load  # noqa: E402
from film.scenariusz import fakty_domu, POZIOM  # noqa: E402
from film.kino import czesci  # noqa: E402

KADRY = (("lotu", "Z lotu ptaka"), ("zmierzch", "Wieczorem"), ("zima", "Zimą"))
NAZWY_WERSJI = {2: "Wersja 2", 1: "Wersja 1 – archiwum"}


def _jpg(im, dst, szer=1600, q=82):
    im = im.convert("RGB")
    if im.width > szer:
        im = im.resize((szer, round(im.height * szer / im.width)), Image.LANCZOS)
    im.save(dst, "JPEG", quality=q, optimize=True, progressive=True)


def _png(src, dst, maks=1500):
    im = Image.open(src).convert("RGB")
    s = min(1.0, maks / max(im.size))
    if s < 1.0:
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    im = im.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    im.save(dst, "PNG", optimize=True)


def _aktualne(src, dst):
    return os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src)


def zdjecia(w, pid, film_dir, dst, rel):
    """Lista {src, podpis} – kadry z filmu, widoki ze spaceru; brak renderów → podglądy 3D tej wersji."""
    out = []

    def dodaj(src_png, nazwa, podpis, im=None):
        fn = os.path.join(dst, nazwa + ".jpg")
        if im is not None or not _aktualne(src_png, fn):
            _jpg(im if im is not None else Image.open(src_png), fn)
        out.append(dict(src=f"{rel}/{nazwa}.jpg", podpis=podpis))

    p = os.path.join(film_dir, "kadry", "lotu.png")
    if os.path.exists(p):
        dodaj(p, "lotu", KADRY[0][1])
    sj = os.path.join(film_dir, "spacer", "spacer.json")
    if os.path.exists(sj):
        from film.spacer import kadr_stacji
        for st in json.load(open(sj, encoding="utf-8")):
            src = os.path.join(film_dir, st["obraz"])
            if not os.path.exists(src):
                continue
            fn = os.path.join(dst, f"spacer_{st['id']}.jpg")
            podpis = "Przed wejściem" if st.get("room") is None else st.get("podpis", "")
            if _aktualne(src, fn):
                out.append(dict(src=f"{rel}/spacer_{st['id']}.jpg", podpis=podpis))
            else:
                dodaj(src, f"spacer_{st['id']}", podpis, kadr_stacji(st, film_dir, 1600, 900, 0.5))
    for k, podpis in KADRY[1:]:
        p = os.path.join(film_dir, "kadry", f"{k}.png")
        if os.path.exists(p):
            dodaj(p, k, podpis)
    if out:
        return out, True
    # bez renderów filmowych: rendery/podglądy tej samej wersji projektu
    v1 = glob.glob(os.path.join(HERE, "domy_v1", f"{pid}_*.py"))
    t_v2 = os.path.getmtime(v1[0]) if v1 else 0
    for d in ("render", "podglad3d"):
        for k, podpis in (("lotu", "Z lotu ptaka"), ("ogrod", "Ogród"), ("zmierzch", "Wieczorem")):
            f = os.path.join(HERE, "out", pid, d, f"{k}.jpg")
            if not os.path.exists(f):
                continue
            nowszy = os.path.getmtime(f) > t_v2
            if (w == 2) != nowszy:            # v2: tylko z czasów v2; v1: tylko sprzed zmian
                continue
            if not any(z["src"].endswith(f"/{k}.jpg") for z in out):
                dodaj(f, k, podpis + (" (podgląd)" if d == "podglad3d" else ""))
    return out, False


def rzuty(H, pid, film_dir, dst, rel):
    out = []
    for f in sorted(glob.glob(os.path.join(film_dir, "plany", "rzut_*.png"))):
        idx = int(os.path.basename(f)[5:-4])
        fn = os.path.join(dst, f"rzut_{idx}.png")
        if not _aktualne(f, fn):
            _png(f, fn)
        out.append(dict(src=f"{rel}/rzut_{idx}.png", podpis=POZIOM.get(idx, f"Rzut poziomu {idx}")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wersja", type=int, default=2)
    ap.add_argument("--out", default="portal")
    ap.add_argument("--zasoby", default=os.path.join(HERE, "kino", "zasoby.json"))
    ap.add_argument("--czesci", default=os.path.join(HERE, "kino", "pliki"), help="katalog części filmów")
    ap.add_argument("--linki", default=None, help='JSON: [{"nazwa": …, "url": …}] – odnośniki w nagłówku')
    a = ap.parse_args()
    w = a.wersja
    out = a.out if os.path.isabs(a.out) else os.path.join(HERE, a.out)
    os.makedirs(os.path.join(out, "pliki"), exist_ok=True)
    zasoby = json.load(open(a.zasoby, encoding="utf-8")) if os.path.exists(a.zasoby) else {}
    kat = "domy" if w == 2 else "domy_v1"
    pids = sorted({os.path.basename(f)[:3] for f in glob.glob(os.path.join(HERE, kat, "p[0-9][0-9]_*.py"))} - {"p99"})
    domy, do_wyslania, pliki = [], [], []
    for pid in pids:
        H = load(pid, kat).build()
        film_dir = os.path.join(HERE, "out", "film", f"v{w}", pid)
        rel = f"pliki/v{w}_{pid}"
        dst = os.path.join(out, rel)
        os.makedirs(dst, exist_ok=True)
        zd, final = zdjecia(w, pid, film_dir, dst, rel)
        rz = rzuty(H, pid, film_dir, dst, rel)
        plakat = None
        if zd:
            src0 = os.path.join(out, zd[0]["src"])
            pf = os.path.join(dst, "plakat.jpg")
            if not _aktualne(src0, pf):
                _jpg(Image.open(src0), pf, szer=640, q=80)
            plakat = f"{rel}/plakat.jpg"
        nj = os.path.join(HERE, "film", "narracja", f"v{w}", f"{pid}.json")
        nar = json.load(open(nj, encoding="utf-8")) if os.path.exists(nj) else {}
        film = None
        mp4 = os.path.join(film_dir, f"ogrody_v{w}_{pid}.mp4")
        if os.path.exists(mp4):
            parts = czesci(mp4, a.czesci, f"v{w}_{pid}")
            brak = [f for f, _ in parts if f not in zasoby]
            if brak:
                do_wyslania += [os.path.join(a.czesci, f) for f in brak]
            else:
                film = dict(czas=round(sum(t for _, t in parts), 1),
                            czesci=[dict(src=zasoby[f], czas=round(t, 2)) for f, t in parts])
        opis = " ".join(x for x in (nar.get("lotu", ""), nar.get("rzuty", "")) if x)
        domy.append(dict(id=f"v{w}_{pid}", numer=pid.upper(), nazwa=H.name, haslo=getattr(H, "tagline", ""),
                         fakty=fakty_domu(H), zalety=nar.get("zalety", []), wady=nar.get("wady", []), opis=opis,
                         zdjecia=zd, rzuty=rz, plakat=plakat, fotorealistyczne=final, film=film))
        for z in zd + rz + ([dict(src=plakat)] if plakat else []):
            pliki.append(z["src"])
        print(f"DOM {pid} {H.name}: zdjęć {len(zd)}{'' if final else ' (podglądy)'}, rzutów {len(rz)}, "
              f"film {'tak' if film else ('do wysłania' if os.path.exists(mp4) else 'nie')}", flush=True)
    linki = json.loads(a.linki) if a.linki else []
    tpl = open(os.path.join(HERE, "film", "portal_szablon.html"), encoding="utf-8").read()
    n_film = sum(1 for d in domy if d["film"])
    info = dict(wersja=w, nazwa_wersji=NAZWY_WERSJI.get(w, f"Wersja {w}"), liczba=len(domy), filmy=n_film, linki=linki)
    rep = {
        "{{TYTUL}}": "Ogrody pod szkłem TV" if w == 2 else "Ogrody pod szkłem TV · wersja 1",
        "{{DOMY}}": json.dumps(domy, ensure_ascii=False).replace("</", "<\\/"),
        "{{INFO}}": json.dumps(info, ensure_ascii=False).replace("</", "<\\/"),
    }
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(tpl)
    json.dump(do_wyslania, open(os.path.join(out, "do_wyslania.json"), "w"), indent=0)
    json.dump(sorted(set(pliki)), open(os.path.join(out, "pliki.json"), "w"), indent=0)
    tot = sum(os.path.getsize(os.path.join(out, f)) for f in set(pliki))
    print(f"PORTAL v{w}: {len(domy)} domów, filmów {n_film}, plików {len(set(pliki))} ({tot / 1e6:.1f} MB), "
          f"części filmów do wysłania: {len(do_wyslania)}")


if __name__ == "__main__":
    main()
