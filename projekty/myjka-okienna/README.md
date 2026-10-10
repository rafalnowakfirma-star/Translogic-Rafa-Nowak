# Myjka okienna MO-1

### Projekt automatycznej myjki do zewnętrznej strony szyby, zamontowanej na stałe przy oknie

![Schemat konstrukcji](schemat.svg)

---

## 1. Cel i założenia

Urządzenie ma samo myć **zewnętrzną** stronę jednej szyby (jednego skrzydła) okna, bez wychylania się przez okno i bez zdejmowania czegokolwiek. Montuje się je raz, a potem uruchamia przyciskiem w telefonie, z Home Assistanta albo według harmonogramu.

| Wymaganie | Wartość docelowa |
|---|---|
| Wielkość szyby | szerokość 500–1400 mm, wysokość 600–1800 mm |
| Typ okna | PCV / drewno / alu, skrzydło otwierane **do wewnątrz** (rozwierne, rozwierno-uchylne) |
| Pokrycie powierzchni | ≥ 95 % szyby (bez pasków ok. 10 mm przy uszczelkach) |
| Czas mycia | ≤ 6 min (2 cykle szorowanie + ściąganie) |
| Zużycie wody | ok. 0,25 l na mycie, zbiornik 5 l (≈ 20 myć) |
| Zasilanie | 24 V DC (SELV), zasilacz wewnątrz mieszkania |
| Szczelność | elektronika IP65, złącza IP67 |
| Temperatura pracy | +3 … +40 °C (poniżej blokada; zimą płyn zimowy) |
| Montaż | bez wiercenia w szybie i skrzydle; uchwyty na ościeżnicy lub w ościeżu |
| Okno nadal się otwiera | tak — cała mechanika jest na części nieruchomej |
| Koszt części | ok. 1100–1300 zł (prototyp) |

## 2. Koncepcja

Rozważone warianty:

| Wariant | Zalety | Wady | Decyzja |
|---|---|---|---|
| Robot magnetyczny (typu Winbot/Hobot) | gotowy produkt | trzeba go przykładać do szyby, przez szybę zespoloną magnes trzyma słabo, ryzyko upadku | ✗ |
| Wycieraczka wahadłowa (jak w aucie) | prosta | myje wycinek koła, narożniki zostają brudne | ✗ |
| **Bramka liniowa: belka jeżdżąca w pionie po dwóch szynach** | myje cały prostokąt, prosta kinematyka, nic nie wisi na skrzydle | trzeba dopasować do wymiaru okna | ✓ |

**Wybrana koncepcja:** po obu stronach szyby, na ościeżnicy, biegną dwie pionowe szyny. Po nich jeździ pozioma **głowica** na całą szerokość szyby. U góry jest belka z silnikiem, wałkiem synchronizującym i listwą dysz. Na dole, na parapecie zewnętrznym, stoi skrzynka z kanistrem wody i pompą.

Najważniejsze uproszczenie: **głowica jest całkowicie pasywna.** Nie ma na niej żadnych przewodów ani węży. Woda jest natryskiwana z nieruchomych dysz w belce górnej i spływa po szybie, a głowica sama zmienia tryb pracy (szorowanie / ściąganie) w zależności od kierunku ruchu (rozdz. 3.3). Dzięki temu nie trzeba prowadzić ruchomego przewodu ani węża, który na zewnątrz zawodziłby jako pierwszy.

## 3. Budowa mechaniczna

### 3.1. Rama i montaż

- **Szyny pionowe:** profil aluminiowy V-slot 20×20 anodowany (2 szt.), długość = wysokość szyby + 150 mm. Mocowane do lica ościeżnicy po bokach skrzydła albo w ościeżu.
- **Belka górna:** profil 20×40, długość = szerokość ramy. Mieści wałek, łożyska, listwę dysz i puszkę elektroniki. Przykryta daszkiem z blachy alu 0,8 mm (osłona przed deszczem i UV).
- **Mocowanie:**
  - *bez wiercenia:* stalowe uchwyty typu „Z” takie jak do moskitier ramkowych — zaczepiają o ościeżnicę, a zamknięte skrzydło je dociska. Wystarcza na parter i niskie piętra.
  - *na stałe (zalecane wyżej niż na 1. piętrze):* 4 kątowniki nierdzewne przykręcone wkrętami A2 do ościeżnicy (w PCV — w strefę wzmocnienia stalowego). W ociepleniu (styropian/wełna) **nie kotwić** — elewacja nie utrzyma obciążenia.
  - zawsze dodatkowo **linka asekuracyjna** ze stali nierdzewnej Ø2 mm od belki górnej do kotwy w ościeżnicy. Urządzenie wisi nad chodnikiem.
- **Kontrola geometrii:** szyny muszą być równoległe — przekątne ramy równe z dokładnością ±2 mm, inaczej głowica się zaklinuje.

### 3.2. Napęd

- **Jeden silnik**, dwa paski. Motoreduktor ślimakowy 24 V z enkoderem (klasa JGY-370, 40–60 obr/min, ≥ 0,3 Nm) w lewym końcu belki górnej napędza wałek nierdzewny Ø8 mm na całą szerokość. Na obu końcach wałka są koła GT2 20T, a od nich biegną w dół paski do rolek napinających na dole szyn.
- **Wałek synchronizujący** gwarantuje, że oba końce głowicy jadą idealnie równo. Przy dwóch osobnych silnikach głowica przekoszałaby się i zakleszczała.
- **Przekładnia ślimakowa jest samohamowna:** po zaniku zasilania głowica nie zjedzie sama w dół. Nie potrzeba hamulca ani przeciwwagi.
- **Paski:** GT2 6 mm z poliuretanu z kordem stalowym (zwykłe gumowe z włóknem szklanym parcieją od UV i wilgoci).
- **Wózki:** po dwa na każdą stronę, na rolkach z POM (mini V-wheel); łożyska nierdzewne lub uszczelnione 2RS.
- **Krańcówki:** czujniki Halla A3144 w drukowanych obudowach zalanych żywicą, magnesy neodymowe na wózku. Krańcówki są dwie (góra i dół); dodatkowo oprogramowanie pilnuje miękkich limitów z enkodera.

### 3.3. Głowica wahliwa (zmiana trybu bez siłownika)

Głowica to belka aluminiowa z **wahaczem** obracającym się na osi poziomej, równoległej do szyby. Na wahaczu są dwa elementy robocze:

- **u góry** — wymienny pasek mikrofibry na piance (na rzep) — do szorowania,
- **u dołu** — guma ściągaczki (typowa wymienna guma do profesjonalnych ściągaczek) — do zbierania wody.

Oś wahacza jest dociskana do szyby dwiema długimi sprężynami (po jednej na końcach) z siłą łącznie ok. 20 N. Odchylenie wahacza ograniczają zderzaki (±10°).

**Jak to działa.** Tarcie o szybę działa na elementy w odległości `d` od osi wahacza (odległość osi od szyby), a nacisk szyby działa na ramieniu `h` (odległość elementu od osi w pionie). Bilans momentów daje warunek, przy którym ruch sam przechyla wahacz:

> wahacz przechyla się, gdy **μ > h / d**

- **Ruch w dół:** tarcie gumy o mokrą szybę jest duże (μ ≈ 0,6–0,9). Przy `h = 18 mm` i `d = 45 mm` (h/d = 0,4) wahacz przechyla się, guma zostaje dociśnięta, a **mikrofibra odrywa się od szyby**. Szyba za gumą zostaje czysta i sucha, bez smug od mokrej ściereczki.
- **Ruch w górę:** tarcie mikrofibry jest małe (μ ≈ 0,3 < 0,4), więc wahacz zostaje w położeniu neutralnym: **szoruje mikrofibra, a guma lekko ciągnie się za nią**. Tak ma być — guma idąca za ściereczką zbiera część brudnej wody.

W skrócie: **w górę = myje, w dół = ściąga.** Nie ma serwa, przewodów ani elektroniki na ruchomej części. Słaby punkt: rzeczywiste współczynniki tarcia trzeba zmierzyć na prototypie (rozdz. 10). Jeśli warunek nie będzie spełniony, przewidziano **wariant B**: wodoodporne serwo IP67 przechylające wahacz, z przewodem prowadzonym w prowadniku łańcuchowym wzdłuż prawej szyny.

**Dopasowanie do okna:** głowica jest o ok. 20 mm węższa od widocznej szyby. Ramiona łączące ją z wózkami mają kształt „Z” i omijają ramę skrzydła od zewnątrz. Skok sprężyn (≥ 20 mm) kompensuje to, że szyba leży kilka milimetrów głębiej niż lico skrzydła. Gdy skrzydło jest otwarte, głowica opiera się na ograniczniku skoku i nie wpada do środka (a sterownik i tak blokuje pracę — kontaktron).

### 3.4. Układ wodny

- **Zbiornik:** kanister 5 l w skrzynce na parapecie zewnętrznym. Napełnia się go lejkiem przez otwarte okno. Czujnik pływakowy wykrywa brak wody.
- **Pompa:** membranowa 24 V, samozasysająca, 1–2 l/min. Przed nią filtr siatkowy, za nią zawór zwrotny (żeby woda nie cofała się z dysz).
- **Dysze:** 4–6 dysz płaskostrumieniowych (wachlarz 80°, łączny wydatek ok. 0,5 l/min) w belce górnej, skierowanych pod kątem ok. 30° na górną część szyby. Woda spływa po całej szybie.
- **Wąż:** PE 6 mm, poprowadzony wewnątrz rowka prawej szyny (osłonięty przed UV).
- **Co wlewać:**
  - najlepiej **wodę demineralizowaną** (jak w systemach „pure water” myjących witryny) — nie zostawia zacieków z kamienia;
  - opcjonalnie kilka kropel płynu do szyb na 5 l;
  - **zimą:** płyn do spryskiwaczy samochodowych (−20 °C) albo opróżnić układ — patrz rozdz. 7.

## 4. Elektronika

### 4.1. Schemat blokowy

```
 [zasilacz 24 V / 60 W]──(przewód przez przepust okienny)──┐
         (wewnątrz)                                         │
                                                  ┌─────────┴──────────┐
                                                  │ puszka IP65 (góra) │
                                                  │ bezpiecznik 3 A    │
                                                  │ INA219 ── DRV8871 ─┼──► silnik + enkoder
                                                  │ MP1584 24→5 V      │
                                                  │ ESP32 ─────────────┼──► MOSFET ──► pompa
                                                  │   ▲ ▲ ▲ ▲ ▲ ▲      │
                                                  └───┼─┼─┼─┼─┼─┼──────┘
       krańcówka góra/dół (Hall) ─────────────────────┘ │ │ │ │ │
       kontaktron skrzydła (okno zamknięte?) ───────────┘ │ │ │ │
       pływak w zbiorniku ────────────────────────────────┘ │ │ │
       czujnik deszczu ─────────────────────────────────────┘ │ │
       DS18B20 (temperatura) ─────────────────────────────────┘ │
       enkoder silnika (A/B) ───────────────────────────────────┘
```

Przewód zasilający 24 V przechodzi przez **płaski przepust okienny** (taśma przeciskana pod uszczelką) albo przez otwór wywiercony w ościeżnicy tak jak przy roletach zewnętrznych. Napięcie 230 V nigdy nie wychodzi na zewnątrz.

**Wariant solarny (opcja):** zużycie energii na samo mycie to ok. 1 Wh. Panel 10 W na daszku belki, akumulator LiFePO4 12 V 6 Ah i ESP32 w uśpieniu (deep sleep) pozwalają zrezygnować z kabla przez okno. Wymaga wersji silnika i pompy na 12 V.

### 4.2. Przyporządkowanie pinów ESP32

| GPIO | Funkcja | Uwagi |
|---|---|---|
| 25 | DRV8871 IN1 (PWM) | 20 kHz, ruch w górę |
| 26 | DRV8871 IN2 (PWM) | ruch w dół |
| 34 | enkoder A | tylko wejście — zewnętrzny pull-up 10 kΩ do 3,3 V |
| 35 | enkoder B | jw. |
| 32 | krańcówka górna | pull-up wewnętrzny, LOW = magnes |
| 33 | krańcówka dolna | jw. |
| 27 | MOSFET pompy | dioda zwrotna równolegle do pompy |
| 14 | kontaktron skrzydła | LOW = okno zamknięte; przerwany przewód = „otwarte” (bezpieczne) |
| 13 | pływak zbiornika | LOW = jest woda; przerwany przewód = „brak wody” |
| 4 | czujnik deszczu (wyjście cyfrowe) | LOW = mokro |
| 19 | DS18B20 (1-Wire) | pull-up 4,7 kΩ |
| 21 / 22 | I²C SDA / SCL | INA219 (prąd silnika) |

Czujniki bezpieczeństwa są podłączone tak, żeby **przerwany przewód oznaczał stan bezpieczny** (okno „otwarte”, „brak wody” → urządzenie nie ruszy).

## 5. Oprogramowanie

Kod sterownika: [`firmware/myjka/myjka.ino`](firmware/myjka/myjka.ino), konfiguracja: [`firmware/myjka/config.h`](firmware/myjka/config.h). Wymaga Arduino-ESP32 3.x oraz bibliotek *OneWire*, *DallasTemperature* i *Adafruit INA219*.

### 5.1. Cykl mycia (pozycja spoczynkowa: na dole)

1. **Kontrola wstępna:** okno zamknięte, temperatura ≥ 3 °C, brak deszczu, jest woda, działa czujnik prądu.
2. **Bazowanie:** zjazd do dolnej krańcówki, wyzerowanie enkodera.
3. Dla każdego cyklu (domyślnie 2):
   1. natrysk 10 s, odczekanie 15 s (rozmiękczenie brudu),
   2. **jazda w górę** — szorowanie mikrofibrą (prędkość 80 %),
   3. natrysk płuczący 5 s, odczekanie 3 s,
   4. **jazda w dół** — ściąganie gumą (60 %; w ostatnim cyklu 50 % dla lepszego efektu).
4. Koniec na dole — guma zebrała wodę, szyba schnie bez zacieków.

Przy pierwszej jeździe w górę sterownik mierzy skok (liczbę impulsów enkodera między krańcówkami) i potem używa go jako miękkiego limitu.

### 5.2. Zabezpieczenia

| Zdarzenie | Reakcja |
|---|---|
| Otwarcie okna w trakcie pracy | natychmiastowe zatrzymanie silnika i pompy (**awaria**) |
| Prąd silnika > limitu (zakleszczenie, lód, przeszkoda) | natychmiastowe zatrzymanie (**awaria**) |
| Enkoder stoi mimo zasilania silnika > 400 ms | zatrzymanie (**awaria**) |
| Przekroczenie skoku o > 3 % (krańcówka nie zadziałała) | zatrzymanie (**awaria**) |
| Ruch trwa dłużej niż 120 s | zatrzymanie (**awaria**) |
| Deszcz lub brak wody w trakcie mycia | łagodne przerwanie: zjazd gumą w dół i postój (**ostrzeżenie**) |
| Zawieszenie programu | watchdog sprzętowy resetuje ESP32 → wyjścia przechodzą w stan bezpieczny |

Po awarii urządzenie wymaga ręcznego skasowania (`/reset`), żeby nie ponawiało ruchu na ślepo, np. przy przymarzniętej głowicy.

### 5.3. Sterowanie

- Strona WWW pod `http://myjka.local/` (przyciski Start / Stop / Reset).
- API: `/start?cycles=2`, `/stop`, `/reset`, `/status` (JSON).
- Port szeregowy (115200): `s` start, `x` stop, `r` reset, `?` status.

### 5.4. Integracja z Home Assistant

```yaml
rest_command:
  myjka_start:
    url: "http://myjka.local/start?cycles=2"
  myjka_stop:
    url: "http://myjka.local/stop"

sensor:
  - platform: rest
    name: Myjka okienna
    resource: http://myjka.local/status
    value_template: "{{ value_json.mode }}"
    json_attributes: [error, temp_c, water_ok, raining, step]
    scan_interval: 30

automation:
  - alias: "Mycie okna w sobotę rano"
    trigger:
      - platform: time
        at: "09:30:00"
    condition:
      - condition: time
        weekday: [sat]
      - condition: numeric_state
        entity_id: weather.dom
        attribute: temperature
        above: 5
      - condition: state
        entity_id: weather.dom
        state: ["sunny", "partlycloudy", "cloudy"]
    action:
      - service: rest_command.myjka_start
```

Najlepiej myć rano albo przy zachmurzeniu. W pełnym słońcu woda wysycha przed przejściem gumy i zostają smugi.

## 6. Obliczenia

Przykład: szyba 1000 × 1300 mm.

**Siły (najgorszy przypadek — jazda w górę):**

| Składnik | Wartość |
|---|---|
| Ciężar głowicy z wózkami (≈ 0,9 kg) | 8,8 N |
| Tarcie mikrofibry: 0,3 × 20 N | 6,0 N |
| Tarcie gumy ciągnącej się za ściereczką (szacunek) | 3,0 N |
| Opory wózków i pasków | 2,0 N |
| **Razem** | **≈ 20 N** |
| Z zapasem ×2 | 40 N |

**Moment na kole GT2 20T** (promień podziałowy 6,37 mm): 40 N × 0,00637 m ≈ **0,25 Nm** → motoreduktor ≥ 0,3 Nm.

Jazda w dół: tarcie gumy 0,8 × 20 N = 16 N minus ciężar 8,8 N plus opory 2 N ≈ 9 N — mniej niż w górę.

**Prędkość i czas:** 60 obr/min × 40 mm/obr = 40 mm/s bez obciążenia. Szorowanie (80 %) ≈ 30 mm/s → 43 s na przejazd, ściąganie (60 %) ≈ 22 mm/s → 60 s. Pełne mycie (bazowanie + 2 cykle): **≈ 5,5 min**.

**Woda:** 0,5 l/min × (10 s + 5 s) × 2 cykle ≈ **0,25 l**. Kanister 5 l starcza na ok. 20 myć — przy myciu co tydzień to ok. 5 miesięcy.

**Energia:** silnik ≈ 10 W × 4 min + pompa ≈ 12 W × 30 s ≈ **0,8 Wh na mycie**. ESP32 w czuwaniu z Wi-Fi zużywa ok. 0,5 W (12 Wh/dobę) i to on dominuje bilans — stąd deep sleep w wariancie solarnym.

**Sprężyny dociskowe:** długie, o małej sztywności (≈ 0,25 N/mm), wstępnie ściśnięte o 40 mm → 10 N na stronę. Odchyłka położenia szyby ±5 mm zmienia nacisk tylko o ±12 %.

## 7. Bezpieczeństwo i warunki pracy

- **Spadające przedmioty** — największe ryzyko. Linka asekuracyjna, śruby nierdzewne z zabezpieczeniem (nakrętki samokontrujące lub klej do gwintów), przegląd mocowań co pół roku.
- **Elektryka:** na zewnątrz wyłącznie 24 V DC (SELV), zasilacz z atestem wewnątrz, bezpiecznik 3 A w puszce, wszystkie przepusty na dławikach.
- **Mróz:** blokada poniżej +3 °C. Na zimę należy wlać płyn zimowy albo opróżnić kanister i przepompować układ do sucha (pompa pracuje kilka sekund na pusto bez szkody). Guma przymarznięta do szyby zostanie wykryta jako przeciążenie — silnik się zatrzyma, zanim urwie gumę.
- **Wiatr:** głowica jest dociśnięta do szyby, a belka i szyny są przykręcone do ościeżnicy. Profil 20×20 nie ma dużej powierzchni naporu.
- **Owady i pająki:** szczotkowe uszczelki na wlotach szyn, przegląd wiosną.
- **Formalności:** w bloku montaż na elewacji może wymagać zgody wspólnoty lub spółdzielni. Warto to sprawdzić przed montażem, zwłaszcza na budynku po termomodernizacji.

## 8. Lista materiałów (BOM)

Ceny orientacyjne, detaliczne, 2026 r.

| # | Element | Ilość | Cena [zł] |
|---|---|---|---|
| 1 | Profil V-slot 20×20 anodowany, 1,6 m | 2 | 80 |
| 2 | Profil 20×40 na belkę górną, 1,2 m | 1 | 45 |
| 3 | Wózki z rolkami POM (mini V-wheel) | 4 | 60 |
| 4 | Pasek GT2 6 mm PU z kordem stalowym | 4 m | 50 |
| 5 | Koło GT2 20T, otwór 8 mm | 2 | 20 |
| 6 | Rolka napinająca gładka do GT2 | 2 | 20 |
| 7 | Wałek nierdzewny Ø8 + 2 łożyska KFL08 + sprzęgło | kpl. | 70 |
| 8 | Motoreduktor ślimakowy 24 V z enkoderem (np. JGY-370, 40–60 obr/min) | 1 | 80 |
| 9 | Belka głowicy — ceownik aluminiowy, 1 m | 1 | 25 |
| 10 | Części drukowane z **ASA** (wahacz, ramiona Z, obudowy krańcówek, zaślepki) — PLA nie nadaje się na zewnątrz | kpl. | 60 |
| 11 | Sprężyny naciskowe długie, ≈ 0,25 N/mm | 4 | 15 |
| 12 | Guma ściągaczki 1 m + szyna mocująca | 1 | 40 |
| 13 | Pasek mikrofibry na rzep, 1 m | 2 | 30 |
| 14 | Pompa membranowa 24 V, 1–2 l/min, samozasysająca | 1 | 55 |
| 15 | Dysze płaskostrumieniowe, rurka PE 6 mm, złączki, filtr, zawór zwrotny | kpl. | 50 |
| 16 | Kanister 5 l + czujnik pływakowy | 1 | 35 |
| 17 | ESP32 DevKit (WROOM-32E) | 1 | 30 |
| 18 | Moduł DRV8871 | 1 | 20 |
| 19 | Moduł INA219 | 1 | 15 |
| 20 | Moduł MOSFET logic-level + dioda | 1 | 10 |
| 21 | Przetwornica 24→5 V (MP1584) | 1 | 8 |
| 22 | Czujniki: 2× Hall A3144 + magnesy, DS18B20 wodoodporny, kontaktron, czujnik deszczu | kpl. | 50 |
| 23 | Puszki IP65, dławiki, złącza wodoodporne M12 | kpl. | 80 |
| 24 | Zasilacz 24 V 60 W (np. Mean Well) | 1 | 90 |
| 25 | Przewód zewnętrzny, płaski przepust okienny, bezpiecznik | kpl. | 40 |
| 26 | Uchwyty montażowe nierdzewne, śruby A2, linka asekuracyjna | kpl. | 50 |
| | **Razem** | | **≈ 1130** |

Materiały eksploatacyjne: guma ściągaczki (wymiana co ok. 12 mies.), paski mikrofibry (pranie co kilka myć, para na zmianę).

## 9. Montaż i uruchomienie

1. **Pomiar okna:** widoczna szyba (szer. × wys.), szerokość lica ościeżnicy, głębokość osadzenia szyby względem lica skrzydła.
2. **Docięcie:** szyny = wys. szyby + 150 mm; belka górna = szer. ramy; wałek i belka głowicy = szer. szyby − 20 mm.
3. **Montaż na stole:** złożenie ramy, naciągnięcie pasków (oba z identycznym naciągiem), sprawdzenie przekątnych.
4. **Montaż na oknie:** uchwyty, rama, linka asekuracyjna, skrzynka z kanistrem.
5. **Ustawienie krańcówek:** dolna tak, żeby guma zatrzymywała się ok. 5 mm nad dolną uszczelką; górna ok. 5 mm pod górną.
6. **Elektronika:** wgranie programu, ustawienie Wi-Fi w `config.h`, sprawdzenie każdego czujnika w `/status` (otwórz/zamknij okno, wyjmij pływak, zrosz czujnik deszczu).
7. **Próba na sucho:** bez wody, prędkość 30 % — kontrola prądu i płynności ruchu, wahacz musi przechylać się przy jeździe w dół.
8. **Kalibracja prądu:** odczytać prąd w normalnej jeździe (`/status`) i ustawić `CURRENT_LIMIT_MA` ok. 1,5–2× wyżej.
9. **Pierwsze mycie** pod nadzorem.

## 10. Plan prototypowania i ryzyka

**Etap 1 — stanowisko testowe (przed zakupem całości):** stara szyba lub szkło ok. 60 × 60 cm w drewnianej ramce, krótki odcinek głowicy (30 cm), waga hakowa.

- zmierzyć współczynniki tarcia mikrofibry i gumy na mokrej szybie (siła ciągnięcia / docisk),
- sprawdzić warunek przechyłu wahacza μ > h/d i dobrać `h` i `d`,
- dobrać docisk sprężyn i ilość wody dającą szybę bez smug.

**Etap 2 — pełny prototyp na jednym oknie, zwykła woda,** testy przez 2–3 tygodnie, również w deszczu (szczelność puszek).

**Etap 3 — poprawki:** wersja dla okien ze słupkiem (dwie głowice na wspólnym wałku albo dwa urządzenia), ewentualnie wariant solarny.

| Ryzyko | Prawdopodobieństwo | Środek zaradczy |
|---|---|---|
| Wahacz nie przechyla się samoczynnie | średnie | zmiana h/d na prototypie; wariant B z serwem |
| Smugi na szybie | średnie | woda demineralizowana, wolniejsze ściąganie, mycie bez słońca |
| Zakleszczenie na krzywych szynach | średnie | wałek synchronizujący, kontrola przekątnych, luz na wózkach |
| Starzenie gumy i tworzyw od UV | wysokie | ASA zamiast PLA, wymiana gumy co rok, daszek |
| Zamarznięcie | wysokie zimą | blokada temperaturowa, płyn zimowy, wykrywanie przeciążenia |
| Mocne zabrudzenia (ptasie odchody) | średnie | dłuższe namaczanie (`SOAK_MS`), 3 cykle |

## 11. Ograniczenia

- Jedno urządzenie myje **jedną szybę**. Okno dwuskrzydłowe ze słupkiem wymaga dwóch głowic.
- Paski ok. 10 mm przy uszczelkach i w narożnikach zostają nieumyte — tak samo przy ręcznym myciu ściągaczką.
- Nie nadaje się do okien otwieranych na zewnątrz, przesuwnych (HST) i dachowych bez przeróbek.
- Zewnętrzne rolety lub żaluzje w tej samej płaszczyźnie kolidują z belką górną — trzeba wtedy zintegrować belkę z kasetą rolety.
