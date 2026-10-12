# KANAŁ 19

Słuchowisko sci-fi horror z obrazem w formie filmu komiksowego.

> Rok 2189. Kosmiczni kierowcy rozmawiają ze sobą na kanale 19. Na Martwym Odcinku odzywają się na nim ci, którzy zaginęli. I wołają po imieniu.

## Pliki

| Plik | Co zawiera |
|---|---|
| [biblia-serii.md](biblia-serii.md) | świat, postacie, styl obrazu i dźwięku, głosy, plan sezonu, tajemnica |
| [odc-01-skrot-scenariusz.md](odc-01-skrot-scenariusz.md) | scenariusz pilota do nagrania (ok. 6 min) |
| [odc-01-skrot-storyboard.md](odc-01-skrot-storyboard.md) | 27 kadrów z poleceniami do grafik + 7 kadrów wzorcowych |

## Plan produkcji pilota

1. **Przeczytaj i popraw.** Biblię i scenariusz, wszystko można zmienić: imiona, dialogi, zakończenie.
2. **Próbne czytanie.** Przeczytaj cały scenariusz na głos ze stoperem. Sprawdzisz rytm i długość.
3. **Kadry wzorcowe R1–R7** w ChatGPT: postacie, kabina, statek. To najważniejszy etap dla spójności.
4. **Kadry K01–K27.**
5. **Nagranie głosów.** Wszystkie role czytasz sam, każda kwestia w osobnym pliku. Potem zmiana barwy w ElevenLabs Voice Changer (szczegóły w biblii, rozdział „Głosy”).
6. **Efekty i muzyka.** Radio, interkom, reaktor, pukanie, motyw przewodni.
7. **Montaż.** Kadry + ruch kamery + dźwięk + dymki/napisy (DaVinci Resolve albo CapCut).

## Struktura folderów na materiały (propozycja)

```
kanal-19/
  grafika/odc-01/      K01.png ... K27.png, R1.png ... R7.png
  glosy/odc-01/        K03_KUBA_1.wav, K03_HANKA_1.wav, ...
  efekty/              reaktor.wav, pip.wav, klik.wav, pukanie.wav, ...
  muzyka/              motyw.wav, dron.wav
```

Przy takim nazewnictwie plików montaż da się w dużej części zautomatyzować.
