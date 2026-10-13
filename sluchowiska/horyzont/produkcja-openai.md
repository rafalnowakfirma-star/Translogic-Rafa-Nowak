# Produkcja przez API OpenAI

Narzędzie: `narzedzia/generuj_ujecia.py`. Wyniki trafiają do `sluchowiska/horyzont/produkcja/` (folder poza repozytorium, bo pliki wideo są duże).

## Wymagania środowiska
- zmienna `OPENAI_API_KEY` (ustawiona w ustawieniach środowiska, nigdy wklejana do czatu)
- dostęp sieciowy do `api.openai.com`
- `pip install openai`

## Etap 1 — próba (mały koszt)
```
python narzedzia/generuj_ujecia.py obrazy R1 R2 R6 U07 U10 U36 U37 U38
python narzedzia/generuj_ujecia.py wideo U07 U10 U36 U37 U38
python narzedzia/generuj_ujecia.py lektor
```
Ocena: czy statek, planeta i lądowanie wyglądają tak, jak trzeba. Poprawki → zmiana poleceń w `odc-01-ujecia.md` → `--nadpisz`.

## Etap 2 — całość
```
python narzedzia/generuj_ujecia.py obrazy
python narzedzia/generuj_ujecia.py wideo
```

## Co robi OpenAI, a co nie
| Element | Narzędzie |
|---|---|
| klatki fotorealistyczne | gpt-image-1 |
| klipy wideo z dźwiękiem otoczenia i efektami | Sora 2 (obraz → wideo) |
| roboczy lektor (do sprawdzenia rytmu) | gpt-4o-mini-tts; docelowo głos autora + zmiana barwy |
| muzyka | poza OpenAI (np. Suno) |
