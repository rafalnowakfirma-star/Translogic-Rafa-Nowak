#!/usr/bin/env python3
"""Zamienia opowiadanie (Markdown) na audiobook MP3.

Silniki:
  nova  – głos „Nova” z OpenAI (wymaga zmiennej OPENAI_API_KEY, płatne, ok. kilkudziesięciu groszy za opowiadanie)
  edge  – darmowe polskie głosy Microsoftu (pl-PL-MarekNeural, pl-PL-ZofiaNeural)

Przykłady:
  pip install openai
  python narzedzia/czytaj_lektorem.py opowiadania/wielka-niedomownosc.md --silnik nova

  pip install edge-tts
  python narzedzia/czytaj_lektorem.py opowiadania/wielka-niedomownosc.md --silnik edge --glos pl-PL-MarekNeural
"""
import argparse
import asyncio
import re
import sys
from pathlib import Path

MAKS_ZNAKOW = 3500  # limit OpenAI to 4096 znaków na jedno zapytanie

INSTRUKCJE_LEKTORA = (
    "Czytasz po polsku audiobook z prozą fantastycznonaukową w stylu Stanisława Lema. "
    "Mów spokojnie, wyraźnie i z lekką ironią, jak doświadczony lektor. "
    "Rób krótkie pauzy przy tytułach rozdziałów, dialogi czytaj z subtelnym zróżnicowaniem."
)


def markdown_na_tekst(md: str) -> str:
    linie = []
    for linia in md.splitlines():
        linia = linia.strip()
        if linia in ("---", "***"):
            continue
        naglowek = re.match(r"^#+\s*(.*)", linia)
        if naglowek:
            linia = naglowek.group(1).rstrip(".") + "."
        linia = re.sub(r"[*_`]", "", linia)
        linie.append(linia)
    tekst = "\n".join(linie)
    return re.sub(r"\n{3,}", "\n\n", tekst).strip()


def podziel(tekst: str) -> list[str]:
    fragmenty, biezacy = [], ""
    for akapit in tekst.split("\n\n"):
        if biezacy and len(biezacy) + len(akapit) + 2 > MAKS_ZNAKOW:
            fragmenty.append(biezacy)
            biezacy = ""
        biezacy = f"{biezacy}\n\n{akapit}" if biezacy else akapit
    if biezacy:
        fragmenty.append(biezacy)
    return fragmenty


def czytaj_nova(fragmenty: list[str], glos: str) -> list[bytes]:
    from openai import OpenAI

    klient = OpenAI()
    wyniki = []
    for i, fragment in enumerate(fragmenty, 1):
        print(f"  fragment {i}/{len(fragmenty)}", file=sys.stderr)
        odp = klient.audio.speech.create(
            model="gpt-4o-mini-tts",
            voice=glos,
            input=fragment,
            instructions=INSTRUKCJE_LEKTORA,
            response_format="mp3",
        )
        wyniki.append(odp.content)
    return wyniki


async def _czytaj_edge(fragmenty: list[str], glos: str) -> list[bytes]:
    import edge_tts

    wyniki = []
    for i, fragment in enumerate(fragmenty, 1):
        print(f"  fragment {i}/{len(fragmenty)}", file=sys.stderr)
        audio = b""
        async for kawalek in edge_tts.Communicate(fragment, glos, rate="-5%").stream():
            if kawalek["type"] == "audio":
                audio += kawalek["data"]
        wyniki.append(audio)
    return wyniki


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plik", type=Path)
    parser.add_argument("--silnik", choices=["nova", "edge"], default="nova")
    parser.add_argument("--glos", help="domyślnie: nova (OpenAI) lub pl-PL-MarekNeural (edge)")
    parser.add_argument("-o", "--wyjscie", type=Path)
    args = parser.parse_args()

    tekst = markdown_na_tekst(args.plik.read_text(encoding="utf-8"))
    fragmenty = podziel(tekst)
    wyjscie = args.wyjscie or args.plik.with_suffix(".mp3")
    print(f"{len(tekst)} znaków, {len(fragmenty)} fragmentów → {wyjscie}", file=sys.stderr)

    if args.silnik == "nova":
        audio = czytaj_nova(fragmenty, args.glos or "nova")
    else:
        audio = asyncio.run(_czytaj_edge(fragmenty, args.glos or "pl-PL-MarekNeural"))

    # Pliki MP3 można bezpiecznie skleić bajt po bajcie.
    wyjscie.write_bytes(b"".join(audio))
    print(f"Gotowe: {wyjscie}", file=sys.stderr)


if __name__ == "__main__":
    main()
