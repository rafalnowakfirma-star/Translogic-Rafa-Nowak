#!/usr/bin/env python3
"""Folder „domy” do skopiowania na pendrive (odtwarzacz multimediów telewizora): dom po domu – film MP4 1080p,
zdjęcia i rzuty JPG, opis TXT. Nazwy plików bez polskich znaków (część telewizorów ich nie wyświetla).

  python3 film/pendrive.py --out /home/user/pendrive/domy
      domy/00_SPIS_DOMOW.txt
      domy/wersja_2/P01_Kruzganek/P01_Kruzganek_film.mp4, 01_Z_lotu_ptaka.jpg, …, Rzut_parteru.jpg, opis.txt
      domy/wersja_1_archiwum/P01_Kruzganek/…
"""
import argparse
import glob
import json
import os
import shutil
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from PIL import Image  # noqa: E402

from podglad import load  # noqa: E402
from film.scenariusz import fakty_domu  # noqa: E402
from film.portal import zdjecia, rzuty  # noqa: E402
from kosztorys import kosztorys, tekst, zl, POZIOM_CEN  # noqa: E402

WERSJE = {2: "wersja_2", 1: "wersja_1_archiwum"}
PL = str.maketrans("ąćęłńóśźżĄĆĘŁŃÓŚŹŻ", "acelnoszzACELNOSZZ")


def ascii_(t):
    t = t.translate(PL)
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    out = "".join(c if c.isalnum() else "_" for c in t)
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")


def mmss(s):
    s = int(round(s))
    return f"{s // 60}:{s % 60:02d}"


def czas(fn):
    import subprocess
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", fn],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def podlinkuj(src, dst):
    """Twarde dowiązanie (bez kopiowania gigabajtów), a gdy się nie da – kopia."""
    if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return
    if os.path.exists(dst):
        os.remove(dst)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def dom(w, pid, out_root, spis):
    kat = "domy" if w == 2 else "domy_v1"
    H = load(pid, kat).build()
    nazwa = f"{pid.upper()}_{ascii_(H.name)}"
    d = os.path.join(out_root, WERSJE[w], nazwa)
    os.makedirs(d, exist_ok=True)
    film_dir = os.path.join(HERE, "out", "film", f"v{w}", pid)
    mp4 = os.path.join(film_dir, f"ogrody_v{w}_{pid}.mp4")
    film = None
    if os.path.exists(mp4):
        film = os.path.join(d, f"{nazwa}_film.mp4")
        podlinkuj(mp4, film)
    with tempfile.TemporaryDirectory() as tmp:
        zd, final = zdjecia(w, pid, film_dir, tmp, ".")
        rz = rzuty(H, pid, film_dir, tmp, ".")
        nowe = set()
        for i, z in enumerate(zd, 1):
            fn = f"{i:02d}_{ascii_(z['podpis'])}.jpg"
            shutil.copy2(os.path.join(tmp, z["src"]), os.path.join(d, fn))
            nowe.add(fn)
        for z in rz:                                            # rzuty: PNG → JPG na białym tle
            fn = f"{ascii_(z['podpis'])}.jpg"
            Image.open(os.path.join(tmp, z["src"])).convert("RGB").save(os.path.join(d, fn), "JPEG", quality=90)
            nowe.add(fn)
    for f in os.listdir(d):                                     # stare zdjęcia (np. podglądy zastąpione renderami)
        if f.endswith(".jpg") and f not in nowe:
            os.remove(os.path.join(d, f))
    nj = os.path.join(HERE, "film", "narracja", f"v{w}", f"{pid}.json")
    nar = json.load(open(nj, encoding="utf-8")) if os.path.exists(nj) else {}
    fakty = fakty_domu(H)
    tl = [f"{pid.upper()} {H.name}", getattr(H, "tagline", ""), ""]
    tl += [f"{v} – {t}" for v, t in fakty]
    if nar.get("zalety"):
        tl += ["", "Zalety:"] + [f"  + {z}" for z in nar["zalety"]]
    if nar.get("wady"):
        tl += ["", "Minusy:"] + [f"  - {z}" for z in nar["wady"]]
    opis = " ".join(x for x in (nar.get("lotu", ""), nar.get("rzuty", "")) if x)
    if opis:
        tl += ["", opis]
    k = kosztorys(H)
    n = k["narastajaco"]
    tl += ["", f"Koszt budowy (szacunek, {POZIOM_CEN.lower()}): stan surowy zamknięty {zl(n['SSZ'])}, deweloperski {zl(n['DEW'])}, "
           f"pod klucz {zl(n['PK'])} ({zl(k['za_m2']['PK'])}/m²); z projektem, nadzorem i rezerwą {zl(n['RAZEM'])}. "
           "Szczegóły: kosztorys.txt."]
    open(os.path.join(d, "kosztorys.txt"), "w", encoding="utf-8-sig").write(
        tekst(dict(wersja=w, pid=pid, numer=pid.upper(), nazwa=H.name, **k)) + "\n")
    tl += ["", f"Film: {mmss(czas(film))}" if film else "Film: w przygotowaniu"]
    if not final:
        tl += ["Zdjęcia: podglądy 3D (rendery fotorealistyczne w przygotowaniu)."]
    open(os.path.join(d, "opis.txt"), "w", encoding="utf-8-sig").write("\n".join(tl) + "\n")
    spis.append((w, pid.upper(), H.name, fakty[0][0], mmss(czas(film)) if film else "w przygotowaniu",
                 f"{WERSJE[w]}/{nazwa}", k))
    return film


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/home/user/pendrive/domy")
    ap.add_argument("--wersje", default="2,1")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    spis, filmy = [], []
    for w in [int(x) for x in a.wersje.split(",")]:
        kat = "domy" if w == 2 else "domy_v1"
        pids = sorted({os.path.basename(f)[:3] for f in glob.glob(os.path.join(HERE, kat, "p[0-9][0-9]_*.py"))} - {"p99"})
        for pid in pids:
            f = dom(w, pid, a.out, spis)
            if f:
                filmy.append(f)
            print("DOM", w, pid, "film" if f else "bez filmu", flush=True)
    tl = ["OGRODY POD SZKŁEM – domy wokół prywatnego ogrodu pod otwieranym szklanym dachem", "",
          "Na telewizorze: włóż pendrive, otwórz odtwarzacz multimediów (USB) i wejdź do folderu „domy”.",
          "W folderze każdego domu: film (MP4, 1080p, z lektorem), zdjęcia i rzuty (JPG), opis (opis.txt) i kosztorys (kosztorys.txt).",
          "Porównanie kosztów wszystkich domów: 00_KOSZTORYS_ZESTAWIENIE.txt.", ""]
    for w in sorted({s[0] for s in spis}, reverse=True):
        tl += ["", "WERSJA 2 (aktualna)" if w == 2 else "WERSJA 1 (archiwum – przed zmianami)", ""]
        tl += [f"  {nr}  {nazwa:<22} {m2:>7}   film {f:<16} {kat}" for ww, nr, nazwa, m2, f, kat, _ in spis if ww == w]
    tl += ["", "Wizualizacje koncepcyjne – wymiary orientacyjne, to nie jest projekt budowlany."]
    open(os.path.join(a.out, "00_SPIS_DOMOW.txt"), "w", encoding="utf-8-sig").write("\n".join(tl) + "\n")
    zestawienie(a.out, spis)
    tot = sum(os.path.getsize(f) for f in filmy) / 1e6
    readme(os.path.dirname(a.out), spis, filmy)
    print(f"PENDRIVE: {len(spis)} domów, filmów {len(filmy)} ({tot:.0f} MB) → {a.out}")


def zestawienie(out, spis):
    """00_KOSZTORYS_ZESTAWIENIE.txt: koszt etapów wszystkich domów obok siebie (szczegóły w kosztorys.txt domu)."""
    mln = lambda x: f"{x / 1e6:5.2f}".replace(".", ",")   # noqa: E731
    tl = ["OGRODY POD SZKŁEM – KOSZTORYS SZACUNKOWY (porównanie domów)",
          f"Ceny brutto (VAT 8%), {POZIOM_CEN.lower()}, średni standard; dokładność ±15–20%. Kwoty w mln zł.",
          "SSZ – stan surowy zamknięty, DEW – deweloperski, PK – pod klucz, RAZEM – z projektem, nadzorem i rezerwą.", ""]
    for w in sorted({x[0] for x in spis}, reverse=True):
        tl += ["WERSJA 2 (aktualna)" if w == 2 else "WERSJA 1 (archiwum – przed zmianami)", "",
               f"  {'dom':<27} {'pow.':>7}   {'SSZ':>5}  {'DEW':>5}  {'PK':>5}  {'RAZEM':>5}   zł/m² pod klucz"]
        for ww, nr, nazwa, m2, f, kat, k in spis:
            if ww == w:
                n = k["narastajaco"]
                tl.append(f"  {nr} {nazwa:<23} {m2:>7}   {mln(n['SSZ'])}  {mln(n['DEW'])}  {mln(n['PK'])}  {mln(n['RAZEM'])}   "
                          + f"{k['za_m2']['PK']:>8,}".replace(",", " "))
        tl.append("")
    tl += ["Poza kosztorysem: działka, przyłącza, ogrodzenie i zagospodarowanie działki, meble ruchome.",
           "Największy rozrzut cen: otwierany dach szklany ogrodu i stolarka aluminiowa – przed budową zapytania ofertowe."]
    open(os.path.join(out, "00_KOSZTORYS_ZESTAWIENIE.txt"), "w", encoding="utf-8-sig").write("\n".join(tl) + "\n")


REPO = "rafalnowakfirma-star/Translogic-Rafa-Nowak"
GALAZ = "ogrody-pendrive"


def readme(katalog, spis, filmy):
    """README gałęzi z folderem „domy”: jak pobrać i skopiować na pendrive, lista filmów z linkami do pobrania."""
    zip_url = f"https://github.com/{REPO}/archive/refs/heads/{GALAZ}.zip"
    tl = ["# Ogrody pod szkłem – folder „domy” na pendrive", "",
          "Filmy (MP4 1080p z lektorem), zdjęcia i rzuty (JPG) oraz opisy wszystkich domów – do oglądania na telewizorze z pendrive'a.", "",
          "## Jak przenieść na telewizor", "",
          f"1. Pobierz całość: **[Download ZIP]({zip_url})** (albo pojedyncze filmy z listy poniżej).",
          "2. Rozpakuj i skopiuj folder **`domy`** na pendrive (FAT32 lub exFAT).",
          "3. Włóż pendrive do telewizora → odtwarzacz multimediów / USB → folder `domy` → wybierz dom.",
          "", "W folderze każdego domu: film `…_film.mp4`, zdjęcia `01_…jpg`, rzuty `Rzut_…jpg`, `opis.txt` i `kosztorys.txt`.",
          "Porównanie kosztów budowy wszystkich domów: `domy/00_KOSZTORYS_ZESTAWIENIE.txt`.",
          "Filmy kolejnych domów dochodzą na bieżąco – lista poniżej pokazuje, które już są.", ""]
    for w in sorted({x[0] for x in spis}, reverse=True):
        tl += ["## " + ("Wersja 2 (aktualna)" if w == 2 else "Wersja 1 – archiwum (przed zmianami)"), "",
               "| Dom | Powierzchnia | Film |", "|---|---|---|"]
        for ww, nr, nazwa, m2, f, kat, _ in spis:
            if ww != w:
                continue
            plik = os.path.basename(kat) + "_film.mp4"
            link = f"[pobierz ({f})](https://github.com/{REPO}/raw/{GALAZ}/domy/{kat}/{plik})" if f != "w przygotowaniu" else "w przygotowaniu"
            tl.append(f"| {nr} {nazwa} | {m2} | {link} |")
        tl.append("")
    tl += ["Wizualizacje koncepcyjne – wymiary orientacyjne, to nie jest projekt budowlany."]
    open(os.path.join(katalog, "README.md"), "w", encoding="utf-8").write("\n".join(tl) + "\n")


if __name__ == "__main__":
    main()
