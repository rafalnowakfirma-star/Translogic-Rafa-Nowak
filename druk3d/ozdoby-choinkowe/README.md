# Ozdoby choinkowe na drukarkę 3D

![Podgląd modeli](podglad/wszystkie.png)

Pięć ozdób w jednym parametrycznym pliku [`ozdoby.scad`](ozdoby.scad)
oraz gotowe pliki STL w katalogu [`stl/`](stl). Wszystkie modele leżą
płasko na stole, mają oczko do zawieszenia i **drukują się bez podpór**.

| Model | Plik STL | Rozmiar (ok.) | Czas druku (orient.)* |
|---|---|---|---|
| Gwiazda fasetowana | `stl/gwiazda.stl` | 67 × 70 × 9 mm | ~35 min |
| Płatek śniegu | `stl/platek.stl` | 76 × 94 × 2,4 mm | ~30 min |
| Choinka z bombkami | `stl/choinka.stl` | 57 × 89 × 3,6 mm | ~40 min |
| Choinka spiralna 3D | `stl/choinka_spiralna.stl` | 44 × 44 × 77 mm | ~1 h |
| Bombka z napisem | `stl/bombka_napis.stl` | 64 × 77 × 3,6 mm | ~45 min |

\* PLA, dysza 0,4 mm, warstwa 0,2 mm, typowa prędkość — zależy od drukarki.

## Ustawienia druku

- **Materiał:** PLA (najprościej) lub PETG (odporniejszy na ciepło lampek).
  Świetnie wyglądają filamenty „silk” złote/srebrne, brokatowe i
  świecące w ciemności.
- **Warstwa:** 0,2 mm (gwiazda i choinka spiralna ładniej przy 0,12–0,16 mm).
- **Ściany:** 3 obrysy — płaskie ozdoby wyjdą wtedy praktycznie pełne i mocne.
- **Wypełnienie:** 15–20 % (dla płaskich i tak prawie nieistotne).
- **Podpory:** wyłączone. **Brim:** przyda się przy choince spiralnej i gwieździe —
  ostre końce ramion przy stole lubią się odklejać.
- **Prasowanie (ironing)** górnej powierzchni płatka i bombki daje gładki,
  błyszczący wierzch.

## Dwa kolory bez drukarki wielokolorowej

Choinka i bombka mają wypukłe detale (bombki na choince, napis i obwódka
na bombce) o wysokości 1,2 mm nad korpusem 2,4 mm. Wstaw w slicerze
**zmianę filamentu (M600 / „Color change”) na wysokości 2,6 mm** —
korpus wydrukuje się np. na zielono/czerwono, a detale na złoto/biało.

## Własne wersje (OpenSCAD)

1. Zainstaluj [OpenSCAD](https://openscad.org) i otwórz `ozdoby.scad`.
2. Włącz *Window → Customizer* — po prawej pojawią się suwaki i pola.
3. Wybierz `model`, zmień wymiary albo **napis na bombce** (np. imię
   i rok — świetne jako prezent albo zawieszka na prezent).
4. `F6` (Render), potem `F7` (Export STL).

Z linii poleceń:

```bash
openscad -D 'model="bombka_napis"' -D 'napis_1="Dla"' -D 'napis_2="Zosi"' \
         -o bombka_zosia.stl ozdoby.scad
```

Przydatne parametry:

| Parametr | Co robi |
|---|---|
| `gwiazda_ramiona` | liczba ramion gwiazdy (5, 6, 8…) |
| `gwiazda_szczyt` | jak bardzo wypukła jest gwiazda |
| `platek_promien`, `platek_ramie` | wielkość płatka i grubość ramion |
| `spirala_skret` | skręt choinki spiralnej; powyżej ~200° nawisy robią się zbyt strome |
| `spirala_ramiona` | liczba żeber choinki spiralnej |
| `napis_1/2/3`, `czcionka` | tekst na bombce (krótkie słowa — do ~9 liter w linii) |
| `uszko_srednica` | średnica oczka na wstążkę/nitkę |

## Pomysły na wykończenie

- Przewlecz cienką czerwoną wstążkę, sznurek jutowy albo złotą nitkę.
- Płatek wydrukowany z białego PETG lub przezroczystego filamentu
  pięknie łapie światło lampek.
- Gwiazdę ze złotego „silk” PLA można dać na czubek małej choinki —
  wystarczy przykleić od spodu stożek ze zwiniętego kartonu.
- Pomaluj wypukły napis złotym markerem akrylowym, jeśli drukujesz
  w jednym kolorze.
