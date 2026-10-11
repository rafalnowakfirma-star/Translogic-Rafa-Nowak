# Myjka okienna MO-1 — kosztorys, plan prototypu, wykonawcy i konkurencja

Uzupełnienie do [README](README.md). Ceny części są orientacyjne, detaliczne, z 2026 r. Stawki za usługi i robociznę to moje szacunki rynkowe — przed zamówieniem trzeba je potwierdzić wycenami.

---

## 1. Kosztorys

### 1.1. Etap 1 — stanowisko testowe (szyba 60 × 60 cm, krótka głowica)

Cel: sprawdzić szczotkę, gumę, docisk i wodę, zanim kupi się całość.

| Pozycja | Koszt [zł] |
|---|---|
| Szyba: stare okno z demontażu (OLX, Allegro Lokalnie) albo szkło float 4 mm 60 × 60 cm | 0–80 |
| Rama/stojak z drewna, śruby | 40 |
| Szczotka 30 cm (szczotka paskowa na rurze lub odcinek szczotki do fotowoltaiki) | 60 |
| Silnik szczotki 24 V z przekładnią | 80 |
| Serwo IP67 25 kg·cm | 120 |
| Guma ściągaczki 35 cm + szyna | 20 |
| Pompa membranowa 24 V + dysze + wąż | 80 |
| ESP32, DRV8871/MOSFET, INA219, przetwornice | 90 |
| Zasilacz 24 V 100 W (docelowy, przejdzie do prototypu) | 120 |
| Filament ASA 1 kg (przy własnej drukarce) | 100 |
| Waga hakowa (pomiar sił), menzurka | 40 |
| **Razem** | **≈ 750–830** |

### 1.2. Etap 2–4 — pełny prototyp na jednym oknie

| Pozycja | Koszt [zł] |
|---|---|
| Części wg BOM z README (rozdz. 8) | 1855 |
| Opcja: podłączenie do kranu | 135 |
| Części ze stanowiska testowego, które przechodzą do prototypu | −300 |
| Zapas na pomyłki, drugą sztukę drobnych części, wysyłki (≈ 15 %) | 280 |
| Druk 3D zlecony na zewnątrz (jeśli brak własnej drukarki) | 200–400 |
| Szczotka walcowa na zamówienie zamiast samodzielnej | 0–250 |
| Płytka PCB (opcjonalnie, zamiast płytki uniwersalnej): 5 szt. z Chin z wysyłką | 100–200 |
| Okno testowe z demontażu (do prób w garażu przed montażem na domu) | 50–150 |
| **Razem materiały** | **≈ 2300–3000** |
| Narzędzia, jeśli ich nie masz (lutownica, multimetr, gwintowniki, piła do alu) | 300–600 |

**Czas własny:** ok. 100–150 h (konstrukcja CAD, montaż, programowanie, testy), rozłożone na 4–6 miesięcy po godzinach.

### 1.3. Jeśli zlecasz pracę (szacunki stawek)

| Usługa | Zakres | Szacunek [zł netto] |
|---|---|---|
| Konstruktor mechanik (CAD, rysunki) | 40–80 h × 100–180 zł/h | 4 000–14 000 |
| Programista systemów wbudowanych (ESP32) | dopracowanie i testy kodu: 20–40 h × 120–220 zł/h | 2 400–8 800 |
| Projekt PCB (KiCad) | 15–30 h | 1 500–5 000 |
| Montaż prototypu w warsztacie | 20–40 h | 1 500–4 000 |
| **Razem z materiałami** | | **ok. 12 000–35 000** |

Najtańsza ścieżka: samodzielny montaż z gotowej dokumentacji i zlecenie tylko tego, czego nie umiesz (np. elektronika albo gięcie blach).

### 1.4. Mała seria (10–50 szt.) — koszt jednostkowy

| Pozycja | Za sztukę [zł] |
|---|---|
| Materiały przy zakupach hurtowych (profile od producenta, szczotki hurtowo, PCB zmontowane w fabryce) | 900–1 300 |
| Montaż i test końcowy (3–5 h) | 200–400 |
| Opakowanie, instrukcja, gwarancja (rezerwa) | 100–200 |
| **Razem** | **≈ 1 200–1 900** |

Koszty jednorazowe przy sprzedaży (nie przy budowie na własny użytek):

- **Oznakowanie CE.** Urządzenie podlega przepisom o maszynach — dyrektywa 2006/42/WE, od 20 stycznia 2027 r. rozporządzenie (UE) 2023/1230. Do tego dochodzi kompatybilność elektromagnetyczna (2014/30/UE) i urządzenia radiowe (RED 2014/53/UE — przez Wi-Fi w ESP32) oraz RoHS. Zasilacz 230 V musi być gotowy i certyfikowany. Badania EMC/RED w laboratorium kosztują szacunkowo 5–20 tys. zł.
- **Ogólne bezpieczeństwo produktów** — rozporządzenie (UE) 2023/988 (GPSR): analiza ryzyka, instrukcja, oznaczenia.
- **Formy wtryskowe** opłacają się dopiero od setek–tysięcy sztuk (szacunkowo 20–80 tys. zł za formę). Dla małej serii: druk 3D (ASA, PA12) albo odlewy z poliuretanu w formach silikonowych.
- **Ubezpieczenie OC produktu.** Urządzenie wisi nad chodnikiem.

## 2. Plan prototypowania

| Etap | Czas | Co powstaje | Kryterium „zaliczone” |
|---|---|---|---|
| 0. Model CAD | 2–3 tyg. | model 3D w FreeCAD / Onshape / Fusion 360, rysunki części do druku i cięcia | wszystkie części mieszczą się na wymiarach konkretnego okna |
| 1. Stanowisko testowe | 2–4 tyg. | szyba 60 × 60 cm, krótka głowica ze szczotką, gumą, serwem i dyszami | 4 na 5 prób bez smug po 1 cyklu; brak rys po 50 cyklach z piaskiem na szybie; zmierzone siły i prądy |
| 2. Rama i napęd | 3–4 tyg. | pełna rama na oknie z demontażu ustawionym w garażu | 500 cykli na sucho bez zakleszczenia; powtarzalność krańcówek ±2 mm |
| 3. Woda i elektronika | 3–4 tyg. | skrzynka wodna, dozowanie, dolewanie z kranu, puszka IP65, firmware na ESP32 | dozowanie ±20 %; 24 h próby szczelności; dolewanie zatrzymuje się na górnym pływaku i po limicie czasu |
| 4. Próba na domu | 4–8 tyg. | montaż na oknie na parterze, mycie co tydzień | działa w deszczu, słońcu i wietrze; brak wycieków i zawilgocenia puszek; szyba czysta „jak po ręcznym myciu” |
| 5. Wersja 2 | 4–6 tyg. | poprawki, obniżka kosztów, dokumentacja montażu | decyzja: zostaje do własnego użytku czy mała seria |

**Razem: ok. 4–6 miesięcy** przy pracy po godzinach.

Najważniejsze pytania do rozstrzygnięcia na etapie 1, bo od nich zależy reszta:

1. Czy szczotka z miękkiego nylonu nie rysuje szkła, gdy na szybie jest piasek?
2. Jaki docisk gumy i jaka prędkość dają szybę bez smug?
3. Ile wody i płynu naprawdę potrzeba?
4. Jak bardzo chlapie szczotka przy 250–300 obr/min?

## 3. Gdzie to wykonać

| Co | Gdzie | Uwagi |
|---|---|---|
| Profile aluminiowe V-slot cięte na wymiar | sklepy z profilami konstrukcyjnymi (polskie sklepy internetowe, np. dla hasła „profil V-slot cięcie na wymiar”; także Motedis z Niemiec, wysyła do Polski) | cięcie zwykle w cenie lub za kilka zł za cięcie; zamawiaj z gwintowaniem końców |
| Części z tworzywa | własna drukarka 3D (ASA) albo usługi druku: lokalne firmy z Oferteo, wykonawcy na Useme, Allegro Lokalnie; online PA12 MJF (np. JLC3DP, PCBWay) | **nie PLA** — mięknie w słońcu; ASA lub PA12 są odporne na UV |
| Osłona szczotki, daszek, kątowniki | lokalna firma od cięcia laserem i gięcia blach (aluminium 0,8–1,5 mm, stal nierdzewna) | wystarczy rysunek DXF z wymiarami gięć |
| Szczotka walcowa | gotowe szczotki walcowe do mycia paneli fotowoltaicznych (części zamienne, długości ok. 0,6–1,1 m); producenci szczotek technicznych na zamówienie; DIY: szczotka paskowa nawinięta na rurę | przy zamówieniu podaj: średnicę, długość, rodzaj włosia (miękki nylon rozszczepiony 0,10–0,15 mm), średnicę i zakończenie wałka |
| Elektronika | prototyp na płytce uniwersalnej; potem PCB w KiCad, produkcja w JLCPCB/PCBWay (Chiny, 1–2 tyg.) lub w polskiej firmie robiącej prototypowe PCB (szybciej, drożej) | moduł ESP32 z certyfikatem radiowym ułatwia późniejszy RED |
| Silniki, pompy, serwo, czujniki | sklepy z elektroniką i robotyką (polskie i AliExpress) | kupuj po 2 sztuki kluczowych podzespołów — jedna zapasowa na testy niszczące |
| Pomoc, sprzęt i miejsce do pracy | hackerspace / makerspace / FabLab w większych miastach; koła naukowe robotyki na politechnikach; centra transferu technologii na uczelniach; parki technologiczne | często mają drukarki, frezarki CNC, lasery i ludzi, którzy pomogą |
| Konstruktor / programista na zlecenie | Useme, Oferteo, lokalne biura konstrukcyjne | wyślij README i rysunki — to gotowa specyfikacja do wyceny |
| Okno do testów | OLX / Allegro: „okno PCV z demontażu” | testy w garażu zamiast na elewacji |
| Ochrona prawna | rzecznik patentowy, uczelniane centrum transferu technologii, Urząd Patentowy RP | patrz rozdz. 4.4 |
| Finansowanie | programy dla startupów i innowacji (PARP, inkubatory przy uczelniach i parkach technologicznych) | sprawdź aktualne nabory |

## 4. Czy ktoś to już robi?

### 4.1. Produkty na rynku

Nie znalazłem gotowego produktu dla domu, który montuje się na stałe przy oknie i sam myje zewnętrzną stronę szyby. Szukałem po angielsku i po polsku. Rynek wygląda tak:

| Kategoria | Przykłady | Różnica względem MO-1 |
|---|---|---|
| Roboty przyssawkowe | Ecovacs Winbot (np. W2 Pro Omni, W3 Omni), Hobot, Mamibot, Kärcher | przenośne — trzeba je za każdym razem przyłożyć do szyby (na zewnątrz: wychylając się, z linką asekuracyjną) |
| Szkło samoczyszczące | Pilkington Activ, SGG Bioclean | tylko przy zakupie nowych szyb; potrzebuje słońca i deszczu; nie usuwa mocnego brudu |
| Roboty do wieżowców | Skyline Robotics Ozmo, gondole BMU | duże budynki komercyjne, inna skala i cena |
| Roboty do paneli fotowoltaicznych | Ecoppia (szyny, mikrofibra bez wody), SolarCleano (szczotki spiralne), roboty szynowe ze szczotkami | **technicznie najbliższe** — szyna + szczotka walcowa; dobre źródło części i rozwiązań |

### 4.2. Patenty — pomysł jest stary

Koncepcja „prowadnice przy oknie + szczotka + wycieraczka” jest opatentowana od dziesięcioleci:

| Dokument | Rok | Treść (w skrócie) |
|---|---|---|
| US3080592 „Automatic window washer” | lata 60. | automatyczna myjka okienna |
| US3694847 „Device for automatically cleaning a window sash” | lata 70. | urządzenie myjące skrzydło okna |
| US4257138 „Automatic device for washing windows” | 1981 | urządzenie montowane na zewnątrz nad oknem, szczotka, wycieraczka, detergent |
| US6851156B1 „Window sky scraper” | 2005 | automatyczne mycie zewnętrznej strony okien sterowane z wnętrza budynku |
| US7503091B2 „Automatic window cleaning apparatus” | 2009 | wózek ze szczotką i wycieraczką na pionowych prowadnicach przy oknie, napęd ciśnieniem wody, wariant ze szczotką obrotową |
| DE19543595A1 | lata 90. | wycieraczka na szynach U przy ramie, przesuwana ręcznie linkami |
| WO2021048576A1 (Genima Innovations Marketing GmbH) | zgł. 2019 | moduł na ramie okna, listwa zębata, ściągaczka i gąbka; według Google Patents wygasłe |
| US20230407655A1 (S. Kamyshniy) | zgł. 2020 | prowadnice mocowane do ramy okna, pasek zębaty w prowadnicach; według Google Patents w toku (USA) |

Statusy prawne pochodzą z wyników wyszukiwania (Google Patents) — samych dokumentów nie udało mi się otworzyć. Przed decyzjami biznesowymi trzeba je zweryfikować.

### 4.3. Co z tego wynika

- **Wolność działania jest raczej dobra.** Patenty z lat 60.–2000. wygasły (patent działa maks. 20 lat), więc ogólna koncepcja jest w domenie publicznej. Warto sprawdzić tylko nowsze zgłoszenia, np. US20230407655A1: czy ma odpowiedniki europejskie lub polskie i co dokładnie zastrzega.
- **Szerokiego patentu na „myjkę na szynach przy oknie” nie da się uzyskać** — brak nowości. Ochrona jest możliwa najwyżej dla konkretnych, nowych rozwiązań szczegółowych (np. konstrukcja głowicy). Często wystarczy tańszy wzór użytkowy.
- **Dlaczego nikt tego nie sprzedaje domom** (mój wniosek, nie badanie rynku):
  - koszt urządzenia wobec ręcznego mycia 2–4 razy w roku albo firmy sprzątającej,
  - szyny i głowica są widoczne na oknie, a każde okno ma inny wymiar,
  - eksploatacja (guma, szczotka, woda, zima) i odpowiedzialność za urządzenie na wysokości.
- **Gdzie ma to największy sens:**
  - okna trudno dostępne: fixy (okna nieotwierane), wysokie przeszklenia w domach, klatki schodowe, ogrody zimowe, świetliki,
  - **witryny sklepów i biur na parterze** — brudzą się szybko i są myte często,
  - domy osób starszych i domy letniskowe.
- **Najmocniejsza droga na rynek:** współpraca z producentem okien albo rolet. Myjka montowana fabrycznie razem z kasetą rolety rozwiązuje problem dopasowania i wyglądu. Polska jest jednym z największych producentów okien w Europie.

### 4.4. Ochrona pomysłu — ważne

- **Ujawnienie publiczne niszczy nowość.** Patent i wzór użytkowy można uzyskać tylko na rozwiązanie, które nie zostało wcześniej publicznie ujawnione, również przez samego twórcę. **To repozytorium jest publiczne.** Jeśli rozważasz ochronę, ustaw repozytorium jako prywatne i nie publikuj kolejnych szczegółów przed zgłoszeniem. Opisane tu rozwiązania i tak w większości nie są nowe (rozdz. 4.2).
- Zgłoszenie wzoru użytkowego lub wynalazku w UPRP kosztuje ok. 500–550 zł opłaty podstawowej (sprawdź aktualny cennik UPRP). Do tego dochodzą opłaty okresowe i zwykle rzecznik patentowy (szacunkowo kilka tys. zł).
- Przed wydawaniem pieniędzy zleć **badanie stanu techniki** rzecznikowi patentowemu albo uczelnianemu centrum transferu technologii.

## Źródła

- [WO2021048576A1 — Automatic cleaning system for window surfaces](https://patents.google.com/patent/WO2021048576A1/en)
- [US20230407655A1 — Automated window-cleaning device](https://patents.google.com/patent/US20230407655A1/en)
- [US7503091B2 — Automatic window cleaning apparatus](https://patents.google.com/patent/US7503091B2/en)
- [US6851156B1 — Window sky scraper](https://patents.google.com/patent/US6851156)
- [US4257138A — Automatic device for washing windows](https://patents.google.com/patent/US4257138)
- [US3080592A — Automatic window washer](https://patents.google.com/patent/US3080592)
- [US3694847A — Device for automatically cleaning a window sash](https://patents.google.com/patent/US3694847A/Direct)
- [DE19543595A1 — Window cleaning device esp. for fixed built-in windows](https://patents.google.com/patent/DE19543595A1/en)
- [Ecovacs Winbot](https://www.ecovacs.com/us/winbot-window-cleaning-robot), [Winbot W3 Omni — recenzja 9to5Google](https://9to5google.com/2026/04/24/hands-on-ecovacs-w3-omni-winbot/), [Hobot](https://hobot.us/blogs/news/the-ultimate-guide-to-choosing-a-window-cleaning-robot-in-2025-and-why-hobot-leads-the-market), [Mamibot](https://www.mamibot.com/robot-window-cleaner), [Kärcher](https://www.kaercher.com/int/home-garden/window-cleaning-robot.html)
- [Ranking robotów do mycia okien 2026 — benchmark.pl](https://www.benchmark.pl/ranking-robotow-do-mycia-okien-2026-top-5-7300605485410336a)
- [Pilkington — szkło samoczyszczące, FAQ](https://www.pilkington.com/en/global/knowledge-base/types-of-glass/self-cleaning-glass/faqs/general-faqs)
- [Skyline Robotics Ozmo](https://www.skylinerobotics.com/meet-ozmo)
- [Ecoppia — technologia](https://www.ecoppia.com/technology), [TaiyangNews — SolarCleano i roboty szynowe](https://taiyangnews.info/technology/haala-energy-introduces-robotic-cleaning-to-utility-pv)
- [Opłaty za wzór użytkowy — Rzeczpospolita](https://pro.rp.pl/prawo-w-firmie/art6851621-za-wzor-uzytkowy-trzeba-zaplacic), [Opłaty dla Urzędu Patentowego — automatykaonline.pl](https://automatykaonline.pl/en/Articles/Prawo-i-normy/Oplaty-dla-Urzedu-Patentowego)
- [Oferteo — druk 3D](https://www.oferteo.pl/druk-3d/katowice), [Useme](https://useme.com/pl/roles/contractor/pandaprint3d,388436/)
