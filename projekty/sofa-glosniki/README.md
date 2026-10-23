# Zabudowa wokół sofy z ukrytymi głośnikami tylnymi

Regały po obu stronach sofy narożnej (prawostronnej), nad sofą pawlacz łączący regały.
Na końcach pawlacza są wnęki z głośnikami tylnymi na uchwytach uchylnych: głośniki są
pochylone w dół na siedzących i schowane za maskownicą przepuszczającą dźwięk.

Warianty:

- **A – biel i dąb**: białe fronty bez uchwytów, dębowe półki, wnęki za białą płytą perforowaną.
- **B – lamele dębowe**: pas lameli przez całą zabudowę, głośniki za lamelami i czarną tkaniną.
- **C – grafit i orzech**: grafitowy korpus, orzechowe półki z LED, wnęki za czarną tkaniną, otwarta nisza nad sofą.

Wymiary są w `wymiary.py` (wspólne dla renderów i rysunku).

```
/home/user/tools/bpyenv/bin/python projekty/sofa-glosniki/render.py      # rendery: out/wariant_*.jpg, out/przekroj_glosniki.jpg
python3 projekty/sofa-glosniki/rysunek.py                                 # rysunek wymiarowy, opisy na przekroju, porównanie
```

Scena korzysta z biblioteki mebli i materiałów z `projekty/ogrody-pod-szklem/film`.
