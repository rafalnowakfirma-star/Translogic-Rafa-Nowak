#!/usr/bin/env python3
"""Szkielet narracji filmu: fakty o domu, kolejność ujęć i stacje spaceru → plik dla autora tekstu lektora.

  python3 film/szkielet.py p01 --wersja 2      → film/narracja/szkielet/v2_p01.md
  python3 film/szkielet.py --wszystkie          → szkielety wszystkich domów (v1, v2)
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from podglad import load  # noqa: E402
from film.kamery import plan_spaceru, DACH, STYL, _graf  # noqa: E402
from silnik.zasady import check  # noqa: E402

FASADA = {"tynk": "biały tynk", "beton": "beton architektoniczny", "drewno": "drewno (modrzew)",
          "drewno_opal": "drewno opalane", "cegla": "cegła", "cegla_biala": "biała cegła", "kamien": "kamień",
          "corten": "stal corten", "miedz": "miedź", "blacha": "ciemna blacha na rąbek", "trawertyn": "trawertyn"}

SZABLON = {
    "tytul": "1–2 zdania (12–22 słowa): jaki to dom, jedna myśl przewodnia.",
    "lotu": "2–3 zdania (30–45 słów) nad ujęciem z lotu ptaka: kształt bryły, powierzchnia, ogród w środku, tarasy.",
    "dach": "1 zdanie (10–16 słów) w trakcie animacji otwierania szklanego dachu ogrodu: jak się otwiera.",
    "spacer": "dla KAŻDEJ stacji spaceru osobny tekst 18–35 słów, jak przewodnik idący z widzem: co widzimy, do czego służy, jak się z tego korzysta na co dzień; przejścia typu „Z wiatrołapu przechodzimy…”.",
    "rzuty": "2–3 zdania (25–45 słów) nad rzutami: podział na strefy, ciąg pokoi przelotowych zamiast korytarzy, ile sypialni, gdzie schody.",
    "zmierzch": "1–2 zdania (12–22 słowa): wieczór, światło, prywatność.",
    "zima": "1–2 zdania (12–22 słowa): zima – dach zamknięty, ogród jako bufor ciepła, co się dzieje z tarasami.",
    "zalety": "lista 3–4 krótkich punktów (≤ 7 słów każdy) – na planszę",
    "wady": "lista 2–4 krótkich punktów (≤ 7 słów każdy) – na planszę; uczciwe minusy TEGO domu",
    "zalety_wady": "tekst lektora 35–60 słów czytany nad planszą: najpierw zalety, potem minusy i jak je złagodzić.",
    "koniec": "1 zdanie (8–16 słów) na zakończenie.",
}


def _m(x):
    return f"{x:.1f}".replace(".", ",")


def fakty(H, wersja):
    gs = [r for r in H.rooms if r.kind == "ogrod"]
    base = H.ground
    ter = [r for r in H.rooms if r.outdoor and r.level > base]
    pat = [r for r in H.rooms if r.outdoor and r.level == base]
    out = [f"# {H.pid.upper()} · {H.name} (wersja {wersja})", "", f"Hasło: {H.tagline}", ""]
    out.append("## Liczby")
    out.append(f"- powierzchnia użytkowa: {_m(H.area['uzytkowa'])} m²; ogród pod szkłem: {_m(H.area['ogrod'])} m²")
    if ter:
        out.append(f"- tarasy na dachu: {', '.join(f'{r.name} {_m(r.poly.area)} m²' for r in ter)}")
    if pat:
        out.append(f"- tarasy i patio na gruncie: {', '.join(f'{r.name} {_m(r.poly.area)} m²' for r in pat)}")
    nlev = len([i for i in H.L if any(not r.outdoor and r.kind not in ('void', 'ogrod_void') for r in H.L[i]['rooms'])])
    top = max(H.levels[i].z + H.levels[i].h for i in H.L)
    out.append(f"- kondygnacje: {nlev}; najwyższy dach: {_m(top)} m nad parterem")
    out.append(f"- elewacja: {FASADA.get(H.style.get('fasada'), H.style.get('fasada'))}")
    for g in gs:
        out.append(f"- ogród: {STYL.get(g.style, g.style)}, {DACH.get(g.roof_type, g.roof_type)}")
    out += ["", "## Pomieszczenia"]
    for idx, r, a in H.room_areas:
        out.append(f"- {H.levels[idx].name}: {r.name} ({r.kind}) {_m(a)} m²")
    out += ["", "## Przejścia między pomieszczeniami (drzwi, otwarte przejścia, schody)"]
    G = _graf(H)
    names = {r.key: r.name for r in H.all_rooms}
    seen = set()
    for a, lst in G.items():
        for (b, p, lvl) in lst:
            k = tuple(sorted((a, b)))
            if k in seen:
                continue
            seen.add(k)
            out.append(f"- {names.get(a, a)} ↔ {names.get(b, b)}" + (" (schody)" if lvl == "schody" else ""))
    out += ["", "## Koncepcja (opis autora domu)"]
    out += [f"- {c}" for c in H.concept]
    for k in ("lato", "zima", "technologia"):
        if H.notes.get(k):
            out.append(f"- {k}: {H.notes[k]}")
    if wersja == 2:
        out += ["", "## Zasady klienta (wersja 2)"]
        out += [f"- {'spełniona' if z['ok'] else 'NIE'}: {z['label']}" for z in check(H)]
    return out


def szkielet(pid, wersja):
    kat = "domy" if wersja == 2 else "domy_v1"
    H = load(pid, kat).build()
    st = plan_spaceru(H)
    out = fakty(H, wersja)
    out += ["", "## Kolejność filmu", "1. plansza tytułowa → `tytul`", "2. ujęcie z lotu ptaka (lato) → `lotu`",
            "3. animacja otwierania szklanego dachu ogrodu → `dach`", "4. spacer z perspektywy pierwszej osoby – stacje:"]
    for s in st:
        out.append(f"   - `{s['id']}`: {s['podpis']}" + (" (stoimy przed drzwiami wejściowymi, na zewnątrz)" if s["room"] is None else ""))
    out += ["5. rzuty kondygnacji → `rzuty`", "6. wieczór, dom świeci od środka → `zmierzch`",
            "7. zima, śnieg na dachach, dach ogrodu zamknięty → `zima`", "8. plansza zalet i minusów → `zalety`, `wady`, `zalety_wady`",
            "9. zakończenie → `koniec`", "", "## Do napisania (JSON)"]
    for k, v in SZABLON.items():
        out.append(f"- `{k}`: {v}")
    tpl = {"tytul": "", "lotu": "", "dach": "", "spacer": {s["id"]: "" for s in st}, "rzuty": "", "zmierzch": "", "zima": "",
           "zalety": [], "wady": [], "zalety_wady": "", "koniec": ""}
    out += ["", "```json", json.dumps(tpl, ensure_ascii=False, indent=1), "```"]
    d = os.path.join(HERE, "film", "narracja", "szkielet")
    os.makedirs(d, exist_ok=True)
    fn = os.path.join(d, f"v{wersja}_{pid}.md")
    open(fn, "w", encoding="utf-8").write("\n".join(out) + "\n")
    return fn


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", nargs="?")
    ap.add_argument("--wersja", type=int, default=2)
    ap.add_argument("--wszystkie", action="store_true")
    a = ap.parse_args()
    if a.wszystkie:
        for w, kat in ((2, "domy"), (1, "domy_v1")):
            for f in sorted(glob.glob(os.path.join(HERE, kat, "p[0-9][0-9]_*.py"))):
                pid = os.path.basename(f).split("_")[0]
                if pid in ("p98", "p99"):
                    continue
                try:
                    print(szkielet(pid, w))
                except Exception as e:
                    print("BŁĄD", w, pid, e)
    else:
        print(szkielet(a.pid, a.wersja))
