# Ogrody pod szkłem

Katalog koncepcji domów jednorodzinnych zbudowanych wokół ogrodu zimowo-letniego pod otwieranym
szklanym dachem. Każdy dom ma biuro przeszklone z dwóch stron, pokoje przelotowe zamiast korytarzy,
wysoki salon z kuchnią połączony z patio, sypialnię ze szklaną ścianą zewnętrzną i wyłącznie płaskie dachy.

## Zawartość

| ścieżka | co to jest |
|---|---|
| `domy/pXX_*.py` | opis każdego domu: pokoje (wielokąty), połączenia, ogród, schody, teksty koncepcji |
| `silnik/` | program, który z opisu wylicza ściany, okna, drzwi, stropy, dachy, meble, ogród, rzuty SVG, przekroje i bryłę 3D |
| `PRZEWODNIK.md` | instrukcja dla projektanta: API silnika i zasady kolekcji |
| `podglad.py` | szybki podgląd rysunków jednego domu (SVG + PNG) |
| `render_blender.py` | rendery Blender Cycles: z lotu ptaka, w ogrodzie, zimowy zmierzch |
| `generuj.py`, `strona_szablon.html` | składanie strony-katalogu w `strona/` |
| `dane/inspiracje.py` | inspiracje i fakty o otwieranych dachach (ze źródłami) |
| `strona/` | gotowa strona: `index.html`, rysunki, modele 3D, zdjęcia |
| `domy_v1/` | pierwsza wersja 16 domów (sprzed zmian klienta) – filmy powstają dla obu wersji |
| `film/` | filmy prezentacyjne: scena fotorealistyczna (materiały, meble, rośliny, teren), kamery, panoramy spaceru, lektor, montaż |
| `film/narracja/` | teksty lektora dla każdego domu (wersja 1 i 2) i szkielety z faktami |

Opublikowana strona (prywatna, do udostępnienia z menu „Share”): https://claude.ai/artifact/2nZooA7H2jdujE3Ec2JgLe

Kino (filmy z lektorem, spacerem i animacją dachu – do oglądania na telewizorze; części filmów w zasobach strony, budowa: `python3 film/kino.py --wersje 2 --out kino --zasoby kino/zasoby.json`): https://claude.ai/artifact/7Lk7FCwkswm9KJtHGCip2C

Archiwum pierwszej wersji katalogu (16 domów sprzed zmian klienta; kopia strony v1 w `strona_v1/` z banerem archiwum): https://claude.ai/artifact/P2izSK4xe3VFVmYYuu4T1B

## Polecenia

```bash
python3 podglad.py p04                      # rysunki jednego domu → out/p04/
/home/user/tools/bpyenv/bin/python render_blender.py p04 --views lotu,ogrod,zmierzch --q final
python3 generuj.py                          # strona → strona/index.html
```

Filmy (po `python3 film/zasoby.py` – pobranie modeli mebli, tekstur, HDRI, fontów i głosu lektora):

```bash
/home/user/tools/bpyenv/bin/python film/render.py p01 --wersja 2 --q final   # kadry, animacja dachu, panoramy spaceru
/home/user/tools/ttsenv/bin/python film/lektor.py p01 --wersja 2             # nagrania lektora z film/narracja/v2/p01.json
python3 film/scenariusz.py p01 --wersja 2 --montuj                          # scenariusz i montaż → out/film/v2/p01/*.mp4
python3 film/kolejka.py                                                     # wszystkie domy po kolei
```

Rysunki i modele są koncepcyjne: wymiary i powierzchnie są orientacyjne, to nie jest projekt budowlany.
