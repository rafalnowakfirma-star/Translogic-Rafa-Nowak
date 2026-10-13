#!/usr/bin/env python3
"""Generuje materiały do „Horyzontu” przez API OpenAI na podstawie listy ujęć.

Czyta polecenia OBRAZ / RUCH z pliku ujęć i lektora ze scenariusza, a wyniki zapisuje w
sluchowiska/horyzont/produkcja/. Pliki, które już istnieją, są pomijane (żeby nie płacić dwa razy);
--nadpisz wymusza ponowne wygenerowanie.

Polecenia:
  obrazy [ID ...]   klatki fotorealistyczne (domyślnie wszystkie R* i U*)
  wideo  [ID ...]   klipy wideo z klatek (obraz → wideo), z dźwiękiem
  lektor            robocza ścieżka lektora (głos syntetyczny, do sprawdzenia rytmu)

Przykłady:
  pip install openai
  python narzedzia/generuj_ujecia.py obrazy R1 R2 U07
  python narzedzia/generuj_ujecia.py wideo U07 --model-wideo sora-2-pro
  python narzedzia/generuj_ujecia.py lektor

Wymaga zmiennej OPENAI_API_KEY.
"""
import argparse
import base64
import re
import subprocess
import sys
import time
from pathlib import Path

KATALOG = Path(__file__).resolve().parent.parent / "sluchowiska" / "horyzont"
UJECIA = KATALOG / "odc-01-ujecia.md"
SCENARIUSZ = KATALOG / "odc-01-scenariusz.md"
WYJSCIE = KATALOG / "produkcja"

INSTRUKCJE_LEKTORA = (
    "Jesteś lektorem zwiastuna filmu science fiction. Mów po polsku, nisko, wolno i spokojnie, "
    "z powagą dokumentu o kosmosie. Rób wyraźne pauzy między zdaniami. Nie dramatyzuj."
)


def wczytaj_ujecia() -> dict[str, dict[str, str]]:
    """Zwraca {ID: {"obraz": ..., "ruch": ..., "czas": ...}} z pliku ujęć."""
    ujecia = {}
    for blok in re.split(r"^### ", UJECIA.read_text(encoding="utf-8"), flags=re.M)[1:]:
        naglowek = blok.splitlines()[0]
        uid = re.match(r"(R\d+|U\d+)", naglowek).group(1)
        czas = re.search(r"·\s*(\d+)\s*s", naglowek)
        kody = re.findall(r"```\n(.*?)\n```", blok, flags=re.S)
        ujecia[uid] = {
            "obraz": kody[0].strip(),
            "ruch": kody[1].strip() if len(kody) > 1 else "",
            "czas": int(czas.group(1)) if czas else 5,
        }
    return ujecia


def wybierz(ujecia: dict, ids: list[str], tylko_u: bool = False) -> list[str]:
    if ids:
        brak = [i for i in ids if i not in ujecia]
        if brak:
            sys.exit(f"Nie ma takich ujęć: {', '.join(brak)}")
        return ids
    return [i for i in ujecia if not tylko_u or i.startswith("U")]


def generuj_obrazy(klient, ujecia: dict, ids: list[str], args) -> None:
    katalog = WYJSCIE / "obrazy"
    katalog.mkdir(parents=True, exist_ok=True)
    for uid in wybierz(ujecia, ids):
        plik = katalog / f"{uid}.png"
        if plik.exists() and not args.nadpisz:
            print(f"  {uid}: już jest, pomijam", file=sys.stderr)
            continue
        print(f"  {uid}: generuję obraz…", file=sys.stderr)
        odp = klient.images.generate(
            model=args.model_obrazu,
            prompt=ujecia[uid]["obraz"],
            size="1536x1024",
            quality=args.jakosc,
        )
        plik.write_bytes(base64.b64decode(odp.data[0].b64_json))
        print(f"  {uid}: zapisano {plik.relative_to(KATALOG)}", file=sys.stderr)


def dopasuj_klatke(zrodlo: Path, cel: Path, rozmiar: str) -> None:
    """Generator wideo wymaga klatki startowej dokładnie w rozdzielczości filmu."""
    szer, wys = rozmiar.split("x")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(zrodlo),
         "-vf", f"scale={szer}:{wys}:force_original_aspect_ratio=increase,crop={szer}:{wys}", str(cel)],
        check=True,
    )


def generuj_wideo(klient, ujecia: dict, ids: list[str], args) -> None:
    katalog = WYJSCIE / "wideo"
    katalog.mkdir(parents=True, exist_ok=True)
    for uid in wybierz(ujecia, ids, tylko_u=True):
        plik = katalog / f"{uid}.mp4"
        if plik.exists() and not args.nadpisz:
            print(f"  {uid}: już jest, pomijam", file=sys.stderr)
            continue
        klatka = WYJSCIE / "obrazy" / f"{uid}.png"
        if not klatka.exists():
            print(f"  {uid}: brak obrazu {klatka.name}, najpierw: obrazy {uid}", file=sys.stderr)
            continue
        dopasowana = katalog / f"{uid}_klatka.png"
        dopasuj_klatke(klatka, dopasowana, args.rozmiar)
        sekundy = "4" if ujecia[uid]["czas"] <= 4 else "8" if ujecia[uid]["czas"] <= 8 else "12"
        opis = f"{ujecia[uid]['obraz']}\n\nMotion and camera: {ujecia[uid]['ruch']}"
        print(f"  {uid}: zlecam wideo {sekundy} s…", file=sys.stderr)
        with dopasowana.open("rb") as f:
            zadanie = klient.videos.create(
                model=args.model_wideo, prompt=opis, seconds=sekundy, size=args.rozmiar, input_reference=f,
            )
        while zadanie.status in ("queued", "in_progress"):
            time.sleep(10)
            zadanie = klient.videos.retrieve(zadanie.id)
            print(f"  {uid}: {zadanie.status} {getattr(zadanie, 'progress', '')}", file=sys.stderr)
        dopasowana.unlink(missing_ok=True)
        if zadanie.status != "completed":
            print(f"  {uid}: NIEUDANE: {getattr(zadanie, 'error', zadanie.status)}", file=sys.stderr)
            continue
        klient.videos.download_content(zadanie.id, variant="video").write_to_file(plik)
        print(f"  {uid}: zapisano {plik.relative_to(KATALOG)}", file=sys.stderr)


def generuj_lektora(klient, args) -> None:
    """Każda kwestia LEKTORA osobno: lektor_U01.mp3, lektor_U02.mp3…"""
    katalog = WYJSCIE / "audio"
    katalog.mkdir(parents=True, exist_ok=True)
    kwestie: dict[str, list[str]] = {}
    ujecie = "U00"
    for linia in SCENARIUSZ.read_text(encoding="utf-8").splitlines():
        if m := re.match(r"\*\*▶ (U\d+)\*\*", linia):
            ujecie = m.group(1)
        elif linia.startswith("**LEKTOR:**"):
            tekst = re.sub(r"\*\([^)]*\)\*", " ", linia.removeprefix("**LEKTOR:**"))
            kwestie.setdefault(ujecie, []).append(re.sub(r"\s+", " ", tekst.replace("*", "")).strip())
    for uid, teksty in kwestie.items():
        plik = katalog / f"lektor_{uid}.mp3"
        if plik.exists() and not args.nadpisz:
            continue
        print(f"  lektor {uid}…", file=sys.stderr)
        odp = klient.audio.speech.create(
            model="gpt-4o-mini-tts", voice=args.glos, input="\n\n".join(teksty),
            instructions=INSTRUKCJE_LEKTORA, response_format="mp3",
        )
        plik.write_bytes(odp.content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("co", choices=["obrazy", "wideo", "lektor"])
    parser.add_argument("ids", nargs="*", help="np. R1 U07 U10; puste = wszystkie")
    parser.add_argument("--model-obrazu", default="gpt-image-1")
    parser.add_argument("--jakosc", default="high", choices=["low", "medium", "high"])
    parser.add_argument("--model-wideo", default="sora-2", help="sora-2 (taniej) lub sora-2-pro (lepiej)")
    parser.add_argument("--rozmiar", default="1280x720")
    parser.add_argument("--glos", default="onyx", help="głos roboczego lektora")
    parser.add_argument("--nadpisz", action="store_true")
    args = parser.parse_args()

    from openai import OpenAI

    klient = OpenAI()
    ujecia = wczytaj_ujecia()
    if args.co == "obrazy":
        generuj_obrazy(klient, ujecia, args.ids, args)
    elif args.co == "wideo":
        generuj_wideo(klient, ujecia, args.ids, args)
    else:
        generuj_lektora(klient, args)


if __name__ == "__main__":
    main()
