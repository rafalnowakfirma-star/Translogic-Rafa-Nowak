#!/usr/bin/env python3
"""Pliki strony zmienione od ostatniej publikacji (publikacja przyjmuje do 64 MB naraz – wysyłamy tylko nowości).

  python3 film/zmienione.py tv/v2a              → JSON {ścieżka: ścieżka} plików nowych/zmienionych (wg pliki.json)
  python3 film/zmienione.py tv/v2a --zapisz     → zapamiętuje stan po udanej publikacji (tv/v2a/opublikowane.json)
"""
import argparse
import hashlib
import json
import os


def skrot(fn):
    h = hashlib.sha1()
    with open(fn, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("katalog")
    ap.add_argument("--zapisz", action="store_true")
    a = ap.parse_args()
    pliki = json.load(open(os.path.join(a.katalog, "pliki.json"), encoding="utf-8"))
    stan_fn = os.path.join(a.katalog, "opublikowane.json")
    stan = json.load(open(stan_fn, encoding="utf-8")) if os.path.exists(stan_fn) else {}
    teraz = {f: skrot(os.path.join(a.katalog, f)) for f in pliki}
    if a.zapisz:
        json.dump(teraz, open(stan_fn, "w", encoding="utf-8"), indent=0)
        print(f"zapisano stan {len(teraz)} plików")
        return
    zm = {f: f for f, h in teraz.items() if stan.get(f) != h}
    for f in stan:
        if f not in teraz:
            zm[f] = None                 # usunięty ze strony
    mb = sum(os.path.getsize(os.path.join(a.katalog, f)) for f, v in zm.items() if v) / 1e6
    print(json.dumps(zm, ensure_ascii=False))
    print(f"# {len(zm)} plików, {mb:.1f} MB", flush=True)


if __name__ == "__main__":
    main()
