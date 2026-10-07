#!/usr/bin/env python3
"""Generuje dźwięk „ku-ku” w stylu piszczałek zegara z kukułką.

Dwa tony (tercja wielka w dół), każdy z kilkoma alikwotami i lekkim
szumem powietrza, jak w piszczałce zasilanej miechem.

  python generuj_kuku.py                 # zapisuje kuku.wav
  ffmpeg -i kuku.wav -b:a 128k mp3/0001.mp3

Plik 0001.mp3 kopiujesz na kartę microSD do folderu /mp3.
"""
import wave
from pathlib import Path

import numpy as np

FS = 44100
TON_WYSOKI = 740.0   # ok. Fis5
TON_NISKI = 587.0    # ok. D5


def piszczalka(f, dlugosc, glosnosc=1.0, ziarno=0):
    t = np.arange(int(FS * dlugosc)) / FS
    vibrato = 1 + 0.003 * np.sin(2 * np.pi * 5.5 * t)
    faza = 2 * np.pi * f * np.cumsum(vibrato) / FS
    ton = np.sin(faza) + 0.30 * np.sin(2 * faza) + 0.12 * np.sin(3 * faza) + 0.05 * np.sin(4 * faza)

    rng = np.random.default_rng(ziarno)
    szum = rng.standard_normal(len(t))
    szum = np.convolve(szum, np.ones(8) / 8, mode="same")       # łagodny filtr dolnoprzepustowy
    ton += 0.06 * szum

    narastanie = np.clip(t / 0.035, 0, 1) ** 1.5
    wybrzmienie = np.exp(-np.clip(t - dlugosc * 0.55, 0, None) / 0.07)
    return glosnosc * ton * narastanie * wybrzmienie


def kuku():
    przerwa = np.zeros(int(FS * 0.07))
    cisza = np.zeros(int(FS * 0.35))
    s = np.concatenate([piszczalka(TON_WYSOKI, 0.30, 1.0, 1), przerwa,
                        piszczalka(TON_NISKI, 0.42, 0.9, 2), cisza])
    return s / np.max(np.abs(s)) * 0.85


def main():
    probki = (kuku() * 32767).astype(np.int16)
    sciezka = Path(__file__).with_name("kuku.wav")
    with wave.open(str(sciezka), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(FS)
        w.writeframes(probki.tobytes())
    print(f"Zapisano {sciezka} ({len(probki) / FS:.2f} s)")


if __name__ == "__main__":
    main()
