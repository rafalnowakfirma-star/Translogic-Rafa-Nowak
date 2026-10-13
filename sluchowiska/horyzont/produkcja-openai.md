# Produkcja przez API OpenAI

Narzędzie: `narzedzia/generuj_ujecia.py`. Wyniki trafiają do `sluchowiska/horyzont/produkcja/` (folder poza repozytorium, bo pliki wideo są duże).

## Wymagania środowiska
- zmienna `OPENAI_API_KEY` (ustawiona w ustawieniach środowiska, nigdy wklejana do czatu)
- dostęp sieciowy do `api.openai.com`
- `pip install openai`

## Etap 1 — PILOTAŻ: wstęp i impuls (U01–U13)
Budżet: ok. 10–12 USD z 30 USD. Reszta zostaje na powtórki i kolejne sceny.

Ujęcia: wstęp lektora (U01–U04), cisza w hali hibernacyjnej (U05–U06), impuls i jego skutki (U07–U13).

```
pip install openai
python narzedzia/generuj_ujecia.py obrazy R1 R2 R3 R5 R6
python narzedzia/generuj_ujecia.py obrazy U01 U02 U03 U04 U05 U06 U07 U08 U09 U10 U11 U12 U13
python narzedzia/generuj_ujecia.py wideo  U01 U02 U03 U04 U05 U06 U07 U08 U09 U10 U11 U12 U13
python narzedzia/generuj_ujecia.py lektor
```
Kolejność: najpierw obrazy i pokazanie ich autorowi. Wideo dopiero po akceptacji obrazów, bo wideo jest najdroższe.

Ocena: czy statek, hala hibernacyjna i impuls wyglądają tak, jak trzeba. Poprawki → zmiana poleceń w `odc-01-ujecia.md` → `--nadpisz` dla wybranych ujęć.

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
