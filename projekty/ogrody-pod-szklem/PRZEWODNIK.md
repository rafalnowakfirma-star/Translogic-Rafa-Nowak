# Przewodnik projektanta – „Ogrody pod szkłem”

Każdy dom to jeden plik `domy/pXX_nazwa.py`, który buduje obiekt `H = House(...)`.
Silnik (`silnik/`) sam wylicza ściany, okna, drzwi, stropy, dachy, meble, ogród,
rzuty SVG, przekroje i bryłę 3D. **Nie zmieniaj plików w `silnik/`, `podglad.py`,
`render_blender.py` ani cudzych projektów.** Jeśli silnik czegoś nie umie albo ma błąd,
obejdź to rozsądnie i opisz problem w raporcie (z krótkim przykładem).

Wzory: `domy/p01_kruzganek.py` (kwadrat), `domy/p02_wieza.py` (wieża, schody U, 3 poziomy),
`domy/p03_pierscien.py` (łuki, wycinki koła), `domy/p99_test.py` (patio sezonowe, taras na piętrze, schody proste).

## Polecenia

```bash
cd /home/user/Translogic-Rafa-Nowak/projekty/ogrody-pod-szklem
python3 podglad.py pXX                 # rzuty, dach, przekroje → out/pXX/*.png (+ powierzchnie i UWAGI)
/home/user/tools/bpyenv/bin/python render_blender.py pXX --views lotu,ogrod --q podglad
                                       # szybki render 3D → out/pXX/podglad3d/lotu.jpg, ogrod.jpg (~10–60 s)
```

Obejrzyj PNG-i narzędziem Read (np. `out/pXX/rzut_0.png`). Poprawiaj, aż rzuty są czytelne,
a podgląd 3D wygląda dobrze. Nie rób renderów `--q final` (zrobię je zbiorczo na końcu).

## Układ współrzędnych

Metry. `x` rośnie na **wschód**, `y` rośnie na **południe** (jak na rysunku: północ u góry).
Kierunki: `"N"` (góra rysunku), `"S"` (dół), `"E"`, `"W"`, `"NE"`… Kąty w `sector` liczone od
wschodu zgodnie z ruchem wskazówek zegara na rysunku: 0 = E, 90 = S, 180 = W, 270 = N.

## Kształty (`from silnik import ...`)

| funkcja | co robi |
|---|---|
| `rect(x1, y1, x2, y2)` | prostokąt |
| `poly((x, y), (x, y), ...)` | dowolny wielokąt |
| `circle(cx, cy, r)` / `ellipse(cx, cy, rx, ry)` | koło / elipsa |
| `sector(cx, cy, r1, r2, a1, a2)` | wycinek pierścienia (a1 < a2, można > 360) |
| `ell_sector(cx, cy, rx1, ry1, rx2, ry2, a1, a2)` | wycinek pierścienia eliptycznego |
| `ngon(cx, cy, n, apothem, rot)` / `hexagon(cx, cy, apothem, rot)` | wielokąt foremny |
| `ngon_band(cx, cy, n, a_in, a_out, k, span=1, rot=0)` | pas wielokąta foremnego między apotemami (boki k…k+span−1) |
| `ngon_vertex(cx, cy, n, apothem, k, rot)` | wierzchołek wielokąta foremnego |
| `rotate(g, deg, origin)`, `move(g, dx, dy)`, `union(a, b, ...)` | przekształcenia |
| `pt(cx, cy, r, a)` | punkt na prawdziwym okręgu |
| `arc_pt(cx, cy, r, a)` / `ell_pt(cx, cy, rx, ry, a)` | punkt na wielokącie koła/elipsy (taki jak wierzchołki `sector`/`circle`) – używaj do własnych wielokątów stykających się z łukami |

**Pokoje to wielokąty po osiach ścian.** Sąsiednie pokoje muszą się stykać krawędziami
(wspólne odcinki) i **nie mogą na siebie zachodzić** ani zostawiać szczelin – inaczej silnik
postawi tam ścianę zewnętrzną. Styki typu T (wierzchołek jednego pokoju na krawędzi drugiego)
są obsługiwane. Łuki rób zawsze z `sector`/`circle`/`ell_sector` o **tym samym środku** –
wierzchołki są wtedy wspólne (krok 7,5°; kąty spoza siatki też są dozwolone, bo ich punkty leżą na cięciwach). Pokój może być wielokątem z łuków i prostych
(`union(sector(...), rect(...))`), ale bez dziur.

## API domu

```python
from silnik import House, rect, sector, circle, union

H = House("p04", "Nazwa", "Jedno–dwa zdania: na czym polega dom.",
          style=dict(fasada="drewno_opal", dach="sedum"),
          concept=["4–6 zdań o koncepcji (patrz niżej)"],
          notes=dict(lato="...", zima="...", technologia="..."))
H.level(0, z=0.0, h=3.4)            # poziomy: indeks, rzędna podłogi, wysokość kondygnacji
H.level(1, z=3.4, h=3.4)
H.ogrod("og", "Ogród zimowy", rect(...), levels=1, roof_type="slide", style="japonski", seed=3)
H.room(klucz, nazwa, rodzaj, kształt, **opcje)
H.connect("a", "b", "door")         # drzwi lub przejście między pokojami
H.entrance("wia", "N")              # wejście główne (drzwi obrotowe) w ścianie zewn. pokoju
H.exit("sal", "S", kind="slide")    # dodatkowe wyjście na zewnątrz
H.window("pok", "E", at=0.5, width=1.2, sill=0.9, head=2.4)   # okno dodatkowe
H.stair("U", level=0, rect=(x1, y1, x2, y2), up="E")          # schody
H.path(rect(...))                   # ścieżka / plac na terenie
H.tree(x, y, "klon")                # drzewo na działce: klon, brzoza, lipa, oliwka, sosna, palma
H.cut("A–A", (x1, y1), (x2, y2))    # linia przekroju (patrzymy w lewo od kierunku a→b)
```

### `H.room(...)` – opcje

| opcja | znaczenie |
|---|---|
| `level=0` | kondygnacja |
| `levels=2` | pokój na 2 (lub 3) kondygnacje – silnik robi pustkę nad nim |
| `ext="windows"` | elewacja zewnętrzna: napis albo słownik wg kierunku `{"S": "glass_slide", "N": "slits", "*": "solid"}`; klucz może też być kluczem sąsiedniego patio/loggii, np. `{"log1": "glass_slide", "*": "solid"}` |
| `garden="glass_slide"` | ściana od ogrodu (domyślnie szkło przesuwne z drzwiami do ogrodu) |
| `roof=` | dla patio/tarasu: `None` (otwarte), `"full"` (całe zadaszone) albo wielokąt (zadaszona część) |
| `enclose=` | dla patio: czym zamknąć krawędzie zewnętrzne (`"fold"`, `"railing"`, `"low"`…) |
| `kitchen_at="E"` | po której stronie salonu stoi kuchnia |
| `floor="kamien"` | posadzka: drewno, drewno_ciemne, deska, kamien, trawertyn, plyty, terakota, cegla, tatami, beton |
| `furn=False` | bez mebli |
| `label_at=(x, y)` | ręczne miejsce podpisu (zwykle niepotrzebne) |
| `garden_door=False` | bez drzwi do ogrodu |

**Specyfikacje ścian (`ext`, `garden`, `edge` ogrodu):**
`windows` (okna 1,4 m co 3,2 m), `windows_sq` (kwadratowe), `slits` (wąskie szczeliny),
`band` (wstęga na wysokości oczu), `band_high` (wstęga pod sufitem – łazienki, garderoby),
`solid` (pełna), `glass` (ściana szklana stała), `glass_slide` (szklana z drzwiami przesuwnymi),
`fold` (szklana harmonijka – zimą zamknięta, latem złożona), `railing` (balustrada),
`low` (murek), `columns` (same słupy), `open` (nic).

**Rodzaje pokoi (`rodzaj`, dobiera meble):** `salon_kuchnia`, `salon`, `kuchnia`, `jadalnia`,
`biuro`, `gabinet`, `sypialnia_glowna`, `sypialnia`, `pokoj`, `gosc`, `lazienka`, `wc`, `garderoba`,
`pralnia`, `spizarnia`, `wiatrolap`, `hol`, `korytarz`, `biblioteka`, `pracownia`, `muzyczny`,
`herbaciarnia`, `silownia`, `kino`, `sauna`, `warsztat`, `winiarnia`, `galeria`, `oranzeria`,
`techniczne`, `garaz`, oraz zewnętrzne: `patio`, `patio_sezonowe`, `taras`, `loggia`.

* `patio_sezonowe` – domyślnie zadaszone (`roof="full"`) i zamknięte harmonijką szklaną (`enclose="fold"`)
  na krawędziach zewnętrznych: **zimą zamknięte, latem całkiem otwarte**. Na rzucie i w 3D widać to automatycznie.
* `taras` na piętrze (np. na dachu niższego skrzydła) dostaje balustradę.
* `patio` z `roof=wielokąt` – częściowo zadaszone (daszek na słupach).

**Połączenia `connect(a, b, rodzaj, at=0.5, width=None)`:** drzwi `door` (0,9), `double` (1,6),
`slide` (1,4), `wide` (2,0 – szerokie przejście), `arch` (1,2), `portal` (3,0), `pivot`;
albo zamiast ściany: `open` (bez ściany), `glass`, `glass_slide`, `fold`, `railing`, `columns`.
`at` = położenie na wspólnej ścianie (0–1); kierunek liczenia zależy od obrysu pokoi, więc sprawdź na rzucie – jeśli drzwi są po złej stronie, użyj `1 − at`. Drzwi powstają tylko między podłogami (nie w pustkach).

### Ogród `H.ogrod(klucz, nazwa, kształt, ...)`

| opcja | wartości |
|---|---|
| `levels` | 1 albo 2 (ogród na wysokość dwóch kondygnacji; ściany pięter od ogrodu stają się szklane) |
| `roof_type` | `slide` (połowa dachu przesuwa się nad drugą), `louvre` (obrotowe lamele), `fold` (harmonijka), `iris` (kopuła z otworem jak migawka – do kształtów okrągłych/wypukłych), `pyramid` (szklana piramida z unoszoną latarnią) |
| `style` | `japonski`, `oranzeria`, `woda`, `las`, `srodziemnomorski`, `tropikalny` |
| `edge` | ściana ogrodu tam, gdzie nie ma pokoju (np. `"glass"`, `"fold"` – ogród otwierany latem na krajobraz, `"low"`) |
| `seed` | inna liczba = inny układ roślin i kamieni |
| `roof_z` | wysokość dachu szklanego (domyślnie 0,25 m nad stropem ostatniej kondygnacji ogrodu) |

### Schody

* `H.stair("straight", level=0, rect=(x1, y1, x2, y2), up="E")` – bieg prosty; na 3,4 m potrzeba ok. **5,2 × 1,1 m**.
* `H.stair("U", level=0, rect=(...), up="E", landing=1.1)` – dwa biegi obok siebie + spocznik na końcu;
  ok. **4,3 × 2,3 m** (kierunek `up` = kierunek pierwszego biegu, spocznik po tej stronie).
* `H.stair("spiral", level=0, center=(x, y), r=1.0, start=90, sweep=300, n=15)` – kręcone, Ø 2–2,4 m.
* Schody stoją w pokoju poziomu `level`; pokój piętro wyżej musi przykrywać otwór schodów (silnik wycina go w stropie).
  Kolejne biegi (0→1, 1→2) można postawić w tym samym miejscu (jak w `p02`).

## Zasady architektoniczne (od klienta – obowiązkowe)

1. **Ogród zimowo-letni w środku** domu, pod **otwieranym szklanym dachem**. Dom go obiega lub obejmuje.
2. **Biuro** w jednym z segmentów wokół ogrodu, **przeszklone z obu stron**: od ogrodu (`garden="glass"` lub `"glass_slide"`)
   i od zewnątrz (`ext` z `glass`/`glass_slide` po stronie krajobrazu).
3. Po drugiej stronie i od frontu: **pomieszczenia przelotowe** zamiast korytarzy (amfilada – przechodzi się z pokoju do pokoju).
   Wymyśl im funkcje: biblioteka, galeria, pracownia, herbaciarnia, sala muzyczna, garderoba przelotowa, spiżarnia-kredens,
   pralnia-suszarnia, sauna, winiarnia, warsztat, siłownia, pokój zabaw… Korytarz tylko wyjątkowo i krótki.
4. **Salon z kuchnią wysoki** (`levels=2`) i połączony z **częściowo zadaszonym patio** (albo `patio_sezonowe`).
5. **Sypialnia główna** z **przeszkloną ścianą zewnętrzną** (`glass_slide` w jednym kierunku), może być na piętrze.
6. **Tylko płaskie dachy i płaskie sufity – zero skosów.** (Szklane kopuły/piramidy nad ogrodem są dozwolone, ale to nie pokoje.)
7. Dom ma być **nietuzinkowy, rzeźbiarski** – zaskakujący kształt, gra brył, wysokości, materiałów. Ale funkcjonalny:
   łazienka blisko sypialni, kuchnia przy jadalni, wejście z wiatrołapem i WC, pralnia/techniczne gdzieś po drodze.
8. Wielkość: **150–260 m² powierzchni użytkowej** (bez ogrodu i patio), ogród **30–90 m²**.
9. Każdy dom inny: inny kształt, inny dach szklany i styl ogrodu, inny materiał elewacji.

## Teksty (po polsku, prosto, konkretnie)

* `tagline` – 1–2 zdania: co to za dom.
* `concept` – 4–6 zdań, każde o jednej decyzji projektowej i jej powodzie (gdzie biuro i co z niego widać,
  jak działa dach ogrodu, jak przechodzi się przez dom, co daje kształt). Bez marketingu i przymiotników na wyrost.
* `notes=dict(lato="1 zdanie: jak dom działa latem", zima="1 zdanie: zimą", technologia="1–2 zdania: z czego zbudować")`.
  Technologia – realny system prefabrykowany / „klocki”, pasujący do kształtu, np. CLT (panele z drewna klejonego),
  szkielet drewniany z prefabrykowanych ścian, bloczki ICF (styropian + beton), bloczki drewniane na pióro-wpust
  (np. Brikawood), bloczki keramzytowe lub silikatowe na klej, prefabrykaty betonowe, moduły stalowe, kostka konopna.
* Nazwy pokoi po polsku, krótkie (np. „Biblioteka”, „Galeria”, „Herbaciarnia”).

## Kontrola jakości przed oddaniem

* `podglad.py` bez `UWAGA` (albo z wyjaśnionymi).
* Na rzutach: każdy pokój ma drzwi tam, gdzie trzeba; da się dojść od wejścia do każdego pokoju; podpisy czytelne;
  meble sensowne; okna i szkło tam, gdzie zakłada koncepcja; schody wiodą do pokoju na piętrze.
* Przekrój przechodzi przez ogród i wysoki salon (i wieżę/schody, jeśli są) – to najciekawszy rysunek.
* Podgląd 3D `lotu.jpg` pokazuje ciekawą bryłę, `ogrod.jpg` – wnętrze ogrodu pod szkłem.
* Drzewa na działce (2–4) i ścieżka do wejścia (`H.path`).


## WERSJA 2 – nowe zasady klienta (obowiązkowe, sprawdzane automatycznie)

Klient po obejrzeniu pierwszej wersji napisał: *„170 m² max, ogród wewnętrzny musi być wyizolowany
i nie widać go bezpośrednio z zewnątrz, na przestrzeni dachowej – nie na samej górze, ale na niższych –
tarasy użytkowe, moduły wokół tarasu przelotowe, użytkowe”*. Dlatego:

1. **Najwyżej 170 m² powierzchni użytkowej** (bez ogrodu, patio i tarasów). `podglad.py` ją wypisuje.
2. **Ogród zamknięty ze wszystkich stron domem.** Na parterze każda krawędź ogrodu przylega do pokoju
   (nie do zewnętrza ani do otwartego patio). Ogród jednokondygnacyjny (`levels=1`) z dachem szklanym
   na wysokości dachu parteru jest najprostszy – wokół jego szklanego dachu leżą tarasy piętra.
3. **Z zewnątrz nie widać ogrodu na wylot.** Pokój, który ma szkło od ogrodu, nie może mieć naprzeciw
   szkła ani szklanych drzwi na zewnątrz w linii prostej. Rozwiązania: od zewnątrz okna (`windows`, `slits`,
   `band`), szkło przesunięte za róg, albo szkło na **patio za murem** – pokój rodzaju `patio` z
   `enclose="gwall"` (mur 2,6 m) liczy się jako prywatny. Wiatrołap nie ma szkła do ogrodu.
4. **Tarasy użytkowe na niższych dachach, nie na samej górze.** Pokoje rodzaju `taras` na piętrze
   (`level=1`), położone na dachu parteru, z wyjściem z pokoju piętra (`connect(pokój, taras, "slide")`).
   Najwyższy dach (nad modułami piętra) jest zielony – bez tarasu.
5. **Moduły piętra wokół tarasu, przelotowe i użytkowe**: na piętrze 2–5 pomieszczeń (sypialnia, biuro,
   biblioteka, pracownia, pokój gościnny, łazienka, garderoba…) ustawionych przy tarasach i połączonych
   drzwiami w ciąg (przechodzi się z jednego do drugiego, bez korytarza).

`podglad.py` wypisuje linie `ZASADA OK/NIE`. **Dom jest gotowy dopiero, gdy wszystkie są OK.**

Nadal obowiązują: biuro przeszklone z dwóch stron (najlepiej moduł na piętrze: szkło na krajobraz i na
taras), pokoje przelotowe zamiast korytarzy, wysoki salon z kuchnią (`levels=2`) połączony z częściowo
zadaszonym patio (najlepiej za murem), sypialnia główna ze szklaną ścianą zewnętrzną (na piętrze można
dać szkło stałe), tylko płaskie dachy. Wzór wersji 2: `domy/p01_kruzganek.py`.
Wersje 1 wszystkich domów są w `domy_v1/`.

Przydatne: `ext={"pat": "glass_slide", "S": "solid", "*": "windows"}` – szkło tylko do patio za murem;
`H.room("pat", "Patio za murem", "patio", rect(...), roof=rect(...), enclose="gwall")`;
schody kręcone (`H.stair("spiral", center=(x, y), r=1.0)`) zajmują najmniej miejsca.

## OGRÓD ZIMOWY JAKO CZĘŚĆ JADALNI (domy P17–P20)

Klient: „Zrób też kilka domów, gdzie ogród wewnętrzny zimowy będzie częścią jadalni” – „ale będzie możliwość zamknięcia ogrodu zimowego”.

- Styl ogrodu `style="jadalnia"`: posadzka z płyt kamiennych w poziomie podłogi domu (bez stopnia), stół jadalny
  (6–8 osób, a gdy brak miejsca – okrągły na 4) stawiany automatycznie w ogrodzie przy najdłuższej szklanej ścianie
  od kuchni / jadalni, dookoła rośliny w donicach (cytrusy, oliwka lub palma, monstera, paprocie).
- Ściana między ogrodem a kuchnią (albo salonem z kuchnią) ma być harmonijką: `garden="fold"` w pokoju kuchni.
  Złożona latem – ogród, kuchnia i jadalnia są jedną przestrzenią; rozłożona – ogród zimowy jest zamknięty
  (np. w mroźne noce albo gdy dach jest otwarty w deszczowy dzień). Dach ogrodu nadal otwiera się latem.
- Pokój obok ogrodu nazywaj „Kuchnia” (kind "kuchnia") albo „Salon z kuchnią” (kind "salon"), nie „jadalnia” –
  stół jest w ogrodzie. Ogród nazwij np. „Ogród zimowy z jadalnią”.
- Ogród ma być mniejszy od zwykłego ogrodu (stół + rośliny): 24–36 m², najlepiej prostokąt min. 4,5 m szerokości.
- Wszystkie zasady wersji 2 obowiązują (≤170 m², ogród otoczony domem, brak widoku na wylot, tarasy na niższych
  dachach, moduły piętra wokół tarasu). Pokój z harmonijką do ogrodu nie może mieć naprzeciw szkła na zewnątrz.
- `python3 podglad.py pXX` sprawdza też, czy do każdego pokoju da się dojść od wejścia (UWAGA: „nie da się dojść do”).
