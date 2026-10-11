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

Opublikowana strona (prywatna, do udostępnienia z menu „Share”): https://claude.ai/artifact/2nZooA7H2jdujE3Ec2JgLe

## Polecenia

```bash
python3 podglad.py p04                      # rysunki jednego domu → out/p04/
/home/user/tools/bpyenv/bin/python render_blender.py p04 --views lotu,ogrod,zmierzch --q final
python3 generuj.py                          # strona → strona/index.html
```

Rysunki i modele są koncepcyjne: wymiary i powierzchnie są orientacyjne, to nie jest projekt budowlany.
