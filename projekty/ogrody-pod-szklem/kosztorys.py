#!/usr/bin/env python3
"""Kosztorys szacunkowy (wskaźnikowy) domów: ilości z modelu domu × ceny jednostkowe (Polska, poziom 2026,
ceny brutto z VAT 8%, wykonawstwo z materiałem, średni standard). To nie jest kosztorys ofertowy – rozrzut ±15–20%.

  python3 kosztorys.py                    → out/kosztorys/kosztorys.json (wszystkie domy v2 i v1)
  python3 kosztorys.py p05 --wersja 2     → wypisuje kosztorys jednego domu

Etapy: SSZ – stan surowy zamknięty, DEW – stan deweloperski (dopłata do SSZ), PK – pod klucz (dopłata do DEW).
Poza kosztorysem: działka, przyłącza do sieci, ogrodzenie i zagospodarowanie działki, meble ruchome.
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from podglad import load  # noqa: E402

# ------------------------------------------------------------------ ceny jednostkowe (zł brutto, VAT 8%)
# Poziom cen 2026, średnia krajowa, średni standard; skalibrowane na cennikach portali budowlanych (ZRODLA niżej).
CENY = {
    # stan surowy zamknięty
    "fundament": 760,          # zł/m² rzutu: płyta ok. 25 cm (śr. ok. 690) + roboty ziemne, XPS, podsypki
    "strop": 520,              # zł/m² stropu żelbetowego monolitycznego (z płytą pod tarasami)
    "sciana_zewn": 520,        # zł/m² ściany: mur 24–25 cm + ocieplenie 20 cm + tynk cienkowarstwowy
    "sciana_dzialowa": 160,    # zł/m² ściany działowej 12 cm (bez tynku – tynki w etapie deweloperskim)
    "dach": 950,               # zł/m² stropodachu: płyta żelbetowa + paroizolacja + 25–30 cm w spadku + membrana + attyki
    "dach_sedum": 330,         # zł/m² dopłaty – dach zielony ekstensywny
    "dach_zwir": 90,           # zł/m² dopłaty – balast żwirowy
    "okno": 1500,              # zł/m² okna aluminiowego 3-szybowego z ciepłym montażem
    "fasada_szklana": 2300,    # zł/m² fasady słupowo-ryglowej (przeszklenie stałe) z montażem
    "hs": 2900,                # zł/m² drzwi przesuwnych HS aluminiowych z montażem i dźwigiem
    "harmonijka": 2700,        # zł/m² ściany szklanej składanej (harmonijka) z montażem
    "drzwi_wejsciowe": 9000,   # zł/szt
    "drzwi_pivot": 18000,      # zł/szt (aluminiowe drzwi obrotowe na osi)
    "drzwi_boczne": 5500,      # zł/szt (drzwi zewnętrzne gospodarcze / boczne)
    # dopłaty do elewacji ponad tynk (zł/m² ściany)
    "elewacja": {"tynk": 0, "beton": 400, "cegla_biala": 380, "cegla": 370, "drewno": 380, "drewno_opal": 480,
                 "trawertyn": 650, "kamien": 600, "miedz": 950, "blacha": 350, "corten": 650},
    # dach szklany ogrodu (zł/m² rzutu ogrodu, z konstrukcją, napędami, sterowaniem i czujnikami deszczu/wiatru)
    "dach_ogrodu": {"slide": 9500, "louvre": 8500, "pyramid": 7500, "iris": 12000, "fold": 9000},
    # stan deweloperski
    "tynki_wylewki": 270,      # zł/m² p.u.: tynki wewnętrzne, wylewki, izolacje podłóg
    "elektryka": 280,          # zł/m² p.u.
    "wodkan": 150,             # zł/m² p.u. (podejścia, kanalizacja podposadzkowa, bez białego montażu)
    "podlogowka": 300,         # zł/m² podłogi
    "pompa_ciepla": 42000,     # kpl. powietrze–woda 8–10 kW z montażem i zasobnikiem CWU
    "rekuperacja": 28000,      # kpl. wentylacja mechaniczna z odzyskiem ciepła
    "schody": {"spiral": 18000, "straight": 16000, "U": 22000},
    "taras": 900,              # zł/m² tarasu na stropie: ocieplenie w spadku, hydroizolacja, wsporniki, deska
    "patio": 420,              # zł/m² patio na gruncie (podbudowa, płyty kamienne)
    "balustrada": 1900,        # zł/mb balustrady szklanej
    # pod klucz
    "wykonczenie": 1050,       # zł/m² p.u.: podłogi (deska/gres), malowanie, sufity, listwy, parapety, oświetlenie
    "drzwi_wewn": 1800,        # zł/szt z ościeżnicą i montażem
    "lazienka": 32000,         # zł/kpl (płytki, ceramika, armatura, kabina/wanna)
    "wc": 12000,               # zł/kpl
    "sauna": 30000,            # zł/kpl
    "kuchnia": 50000,          # zł/kpl (zabudowa na wymiar + AGD + montaż)
    "ogrod_zielen": 600,       # zł/m² ogrodu: podłoże, drenaż, nawadnianie, rośliny, nawierzchnie
    "ogrod_styl": {"woda": 25000, "tropikalny": 16000, "jadalnia": 12000},   # dopłaty: woda, mgła, posadzka
    # koszty dodatkowe
    "projekt": 40000,          # projekt indywidualny z branżami + adaptacja + pozwolenia
    "kierownik": 12000,        # kierownik budowy + geodeta
    "rezerwa": 0.15,           # rezerwa na nieprzewidziane (otwierany dach szklany: zalecane 15–20%)
}
POZIOM_CEN = "Poziom cen: 2026, średnia krajowa"

# Podstawy cen (portale cenowe; strony cytowane przez wyniki wyszukiwania, nie oferty wykonawców)
_KB = "kb.pl"
ZRODLA = [
    ("Płyta fundamentowa z robotami ziemnymi", "m² rzutu", "fundament", [(_KB, "https://kb.pl/cenniki/plyta-fundamentowa/")],
     "płyta śr. ok. 690 zł/m², + XPS i roboty ziemne"),
    ("Strop żelbetowy monolityczny", "m²", "strop", [(_KB, "https://kb.pl/cenniki/uslugi/cennik-stropow-monolitycznych-zelbetowych/")], "480–750"),
    ("Ściana zewnętrzna z ociepleniem 20 cm i tynkiem", "m²", "sciana_zewn",
     [(_KB, "https://kb.pl/aktualnosci/budowa-domu/koszty-ocieplenia-domu-i-elewacji-2026/"),
      ("Castorama", "https://www.castorama.pl/ile-kosztuje-ocieplenie-domu-ins-11545881.html")], "mur + bloczki + ocieplenie, 400–650"),
    ("Ściana działowa 12 cm", "m²", "sciana_dzialowa", [(_KB, "https://kb.pl/cenniki/sciany-dzialowe")], "130–220"),
    ("Stropodach kompletny", "m²", "dach", [("cenauslug.pl", "https://cenauslug.pl/poradniki/krycie-dachu-plaskiego-epdm-papa-czy-pvc"),
                                            (_KB, "https://kb.pl/cenniki/uslugi/papa-dachowa/")], "płyta + warstwy, 750–1 350"),
    ("Dach zielony ekstensywny – dopłata", "m²", "dach_sedum", [("scianyidachy.pl", "https://scianyidachy.pl/dach-zielony-cena")], "200–550"),
    ("Okna aluminiowe 3-szybowe z montażem", "m²", "okno", [(_KB, "https://kb.pl/cenniki/produkty/okna-aluminiowe/")], "1 000–1 900"),
    ("Fasada słupowo-ryglowa", "m²", "fasada_szklana", [("nowe-fasady.pl", "https://nowe-fasady.pl/fasada-aluminiowa-cena-za-m2")],
     "1 600–3 200 z montażem"),
    ("Drzwi przesuwne HS", "m²", "hs", [(_KB, "https://kb.pl/cenniki/produkty/ceny-przesuwnych-drzwi-tarasowych-ile-trzeba-zaplacic/")],
     "1 800–4 500, systemy slim drożej"),
    ("Ściana szklana harmonijkowa", "m²", "harmonijka",
     [("omnisklep.pl", "https://omnisklep.pl/drzwi/drzwi-tarasowe/drzwi-balkonowe-harmonijkowe/drzwi-harmonijkowe-aluminiowe-2400-x-2200")],
     "Aluprof MB-86 Fold Line + montaż"),
    ("Drzwi wejściowe / pivot", "szt.", ("drzwi_wejsciowe", "drzwi_pivot"), [(_KB, "https://kb.pl/cenniki/drzwi-wejsciowe-antywlamaniowe")],
     "aluminiowe z panelem 10–20 tys."),
    ("Elewacja drewniana / klinkier – dopłata do tynku", "m²", ("elewacja", "drewno"),
     [("Murator", "https://muratordom.pl/budowa/elewacja/ile-zaplacisz-za-elewacje-w-2026-pelny-cennik-tynkow-drewna-klinkieru-i-sidingu-aa-W6H6-jpmp-59KB.html")],
     "deska 300–650, klinkier 320–700"),
    ("Otwierany dach szklany ogrodu (przesuwny)", "m²", ("dach_ogrodu", "slide"),
     [("Roofglaze", "https://roofglaze.co.uk/product/skyway-electric-sliding-flat-glass-rooflights/"),
      ("Sterling Build", "https://www.sterlingbuild.co.uk/signature-electric-sliding-flat-rooflight/")],
     "brak polskich cenników – szacunek 7–18 tys., potrzebne oferty producentów"),
    ("Instalacja elektryczna", "m² p.u.", "elektryka",
     [("Murator", "https://muratordom.pl/instalacje/instalacja-elektryczna/ile-kosztuje-instalacja-elektryczna-we-wrzesniu-2026-roku-aktualny-cennik-robocizny-aa-UXtk-Yo6M-r7k1.html")],
     "200–450"),
    ("Instalacja wod-kan", "m² p.u.", "wodkan", [(_KB, "https://kb.pl/aktualnosci/budowa-domu/cennik-uslug-hydraulicznych-2026/")],
     "punkt ok. 840 zł"),
    ("Ogrzewanie podłogowe", "m²", "podlogowka", [(_KB, "https://kb.pl/cenniki/uslugi/ogrzewanie-podlogowe/")], "260–400"),
    ("Pompa ciepła 8–10 kW z montażem", "kpl.", "pompa_ciepla",
     [("cenauslug.pl", "https://cenauslug.pl/poradniki/ile-kosztuje-pompa-ciepla-z-montazem-cennik-urzadzen-i-robocizny")], "30–60 tys."),
    ("Rekuperacja", "kpl.", "rekuperacja",
     [("Murator", "https://muratordom.pl/instalacje/wentylacja-i-klimatyzacja/rekuperacja-ile-kosztuje-kompletny-system-z-montazem-aktualne-ceny-2026-aa-cJbZ-3mcb-Ecwc.html")],
     "20–38 tys."),
    ("Schody kręcone stalowe", "kpl.", ("schody", "spiral"),
     [(_KB, "https://kb.pl/remont-i-wykonczenie/schody/schody-spiralne-rodzaje-zalety-wady-opinie-ceny-porady/")], "8–35 tys."),
    ("Taras na stropie", "m²", "taras", [(_KB, "https://kb.pl/ogrody/budowa-tarasu/ile-kosztuje-taras-kompozytowy-aktualne-ceny-budowy/")],
     "deska 400–900 + warstwy dachu"),
    ("Balustrada szklana", "mb", "balustrada", [(_KB, "https://kb.pl/cenniki/uslugi/cennik-balustrad-roznego-typu-z-montazem/")], "1 200–2 500"),
    ("Wykończenie wnętrz", "m² p.u.", "wykonczenie",
     [("Leroy Merlin", "https://www.leroymerlin.pl/uslugi/podlogi/ukladanie-deski-warstwowej.html"),
      (_KB, "https://kb.pl/cenniki/uslugi/ile-kosztuje-malowanie-pokoju/")], "deska dębowa ok. 330/m² + malowanie"),
    ("Drzwi wewnętrzne", "szt.", "drzwi_wewn", [(_KB, "https://kb.pl/aktualnosci/wnetrza/ile-kosztuja-drzwi-wewnetrzne-z-montazem/")], "1 100–3 500"),
    ("Łazienka 6–8 m²", "kpl.", "lazienka", [("cenauslug.pl", "https://cenauslug.pl/poradniki/remont-lazienki-ile-kosztuje-i-jak-nie-przeplacic")],
     "25–40 tys. standard"),
    ("Kuchnia z AGD", "kpl.", "kuchnia",
     [("Murator", "https://muratordom.pl/wnetrza/kuchnia/remont-kuchni-2026-ktore-decyzje-sa-najdrozsze-ceny-materialow-i-robocizny-aa-vhNj-2EEK-AGTL.html")],
     "ok. 57 tys. dla 8 m²"),
    ("Ogród wewnętrzny", "m²", "ogrod_zielen",
     [("Murator", "https://muratordom.pl/ogrod/aranzacja-ogrodu/zalozenie-ogrodu-500-1000-m2-w-2026-ile-kosztuje-usluga-zalozenia-ogrodu-aa-YDVf-TjuY-DGeL.html")],
     "ogród 150–350, w atrium ×2–3"),
    ("Woda w ogrodzie (oczko z filtracją)", "kpl.", ("ogrod_styl", "woda"),
     [("Murator", "https://muratordom.pl/ogrod/wyposazenie-ogrodu/koszt-budowy-oczka-wodnego-2026-ceny-materialow-i-robocizny-aa-3qqw-KjCw-Rfz1.html")],
     "5–25 tys."),
    ("Projekt indywidualny z branżami", "kpl.", "projekt", [("Rankomat", "https://rankomat.pl/nieruchomosci/ile-kosztuje-projekt-domu")], "25–65 tys."),
    ("Kierownik budowy, geodeta", "kpl.", "kierownik", [("Oferteo", "https://www.oferteo.pl/kierownicy-budowy")], "kierownik śr. 7,7 tys. netto"),
    ("Rezerwa", "%", "rezerwa", [(_KB, "https://kb.pl/aktualnosci/budowa-domu/niespodziewane-wydatki-przy-budowie-domu/")],
     "zalecane 10–20%, przy dachu otwieranym górna połowa"),
]
ETAPY = {"SSZ": "Stan surowy zamknięty", "DEW": "Stan deweloperski", "PK": "Pod klucz", "DOD": "Koszty dodatkowe"}
ELEWACJA_NAZWA = {"tynk": "tynk", "beton": "beton architektoniczny", "cegla_biala": "cegła biała", "cegla": "cegła",
                  "drewno": "deska drewniana", "drewno_opal": "drewno opalane", "trawertyn": "trawertyn",
                  "kamien": "kamień", "miedz": "blacha miedziana", "blacha": "blacha na rąbek", "corten": "stal corten"}
DACH_OGRODU = {"slide": "przesuwny dach szklany z napędem", "louvre": "dach z obrotowych lamel szklanych",
               "pyramid": "szklana piramida z podnoszoną latarnią", "iris": "szklana kopuła otwierana przesłonowo",
               "fold": "składany (harmonijkowy) dach szklany"}
LAZIENKI = {"lazienka": "lazienka", "wc": "wc", "sauna": "sauna"}


def ilosci(H):
    """Przedmiar z modelu: powierzchnie, ściany, przeszklenia, otwory, dachy, tarasy, schody, pomieszczenia mokre."""
    q = dict(pu=H.area["uzytkowa"], ogrod=H.area["ogrod"], rzut=H.footprint.area)
    gs = [r for r in H.rooms if r.kind == "ogrod"]
    q["ogrod_rzut"] = sum(g.poly.area for g in gs)
    q["dach_ogrodu"] = gs[0].roof_type if gs else None
    q["ogrod_styl"] = gs[0].style if gs else None
    base = min(H.L)
    q.update(sciana_zewn=0.0, okna=0.0, fasada=0.0, hs=0.0, harmonijka=0.0, dzialowe=0.0, balustrada=0.0,
             drzwi_wej=0, drzwi_pivot=0, drzwi_wewn=0)
    for L in H.L.values():
        otw_zewn = 0.0
        for o in L["openings"]:
            a = o.width * max(0.3, (o.head or 2.2) - (o.sill or 0.0))
            if o.cls in ("ext", "gwall", "low"):
                if o.kind in ("win", "band"):
                    q["okna"] += a
                elif o.kind == "slide":
                    q["hs"] += a
                elif o.kind == "pivot":
                    q["drzwi_pivot"] += 1
                elif o.kind == "door":
                    q["drzwi_wej"] += 1
                otw_zewn += a
            elif o.cls == "glass" and o.kind == "slide":
                q["hs"] += a
            elif o.cls == "int" and o.kind in ("door", "double", "slide"):
                q["drzwi_wewn"] += 2 if o.kind == "double" else 1
        for w in L["walls"]:
            h = max(0.0, w.z1 - w.z0)
            if w.cls in ("ext", "gwall", "low"):
                q["sciana_zewn"] += w.length * h
            elif w.cls == "glass":
                q["fasada"] += w.length * h
            elif w.cls == "fold":
                q["harmonijka"] += w.length * h
            elif w.cls == "int":
                q["dzialowe"] += w.length * h
            elif w.cls == "railing":
                q["balustrada"] += w.length
        q["sciana_zewn"] -= otw_zewn
    q["fasada"] = max(0.0, q["fasada"] - q["hs"] + sum(  # przesuwne skrzydła w fasadach liczone jako HS
        o.width * max(0.3, (o.head or 2.2) - (o.sill or 0.0)) for L in H.L.values() for o in L["openings"]
        if o.cls in ("ext", "gwall", "low") and o.kind == "slide"))
    q["sciana_zewn"] = max(0.0, q["sciana_zewn"])
    q["stropy"] = sum(s[1].area for s in H.slabs)
    q["dach_sedum"] = sum(r[1].area for r in H.roofs if r[2] == "sedum")
    q["dach_zwir"] = sum(r[1].area for r in H.roofs if r[2] != "sedum")
    q["tarasy"] = sum(r.poly.area for r in H.rooms if r.outdoor and r.level > base)
    q["patio"] = sum(r.poly.area for r in H.rooms if r.outdoor and r.level == base)
    q["schody"] = [s.kind for s in H.stairs]
    q["mokre"] = {k: sum(1 for r in H.rooms if r.kind == k) for k in LAZIENKI}
    q["kuchnie"] = max(1, sum(1 for r in H.rooms if r.kind in ("salon_kuchnia", "kuchnia")))
    q["elewacja"] = H.style.get("fasada", "tynk")
    q["poziomy"] = len([i for i in H.L if any(not r.outdoor and r.kind not in ("void", "ogrod_void")
                                              for r in H.L[i]["rooms"])])
    return q


def kosztorys(H):
    q = ilosci(H)
    C = CENY
    poz = []

    def dodaj(etap, nazwa, ilosc, jm, cena, szklo=False):
        if ilosc and cena:
            poz.append(dict(etap=etap, nazwa=nazwa, ilosc=round(ilosc, 1), jm=jm, cena=round(cena), wartosc=round(ilosc * cena),
                            szklo=szklo))

    el = q["elewacja"]
    dodaj("SSZ", "Fundamenty i płyta parteru (bez ogrodu)", q["rzut"] - q["ogrod_rzut"], "m²", C["fundament"])
    dodaj("SSZ", "Ściany zewnętrzne z ociepleniem i tynkiem", q["sciana_zewn"], "m²", C["sciana_zewn"])
    dodaj("SSZ", f"Elewacja: {ELEWACJA_NAZWA.get(el, el)} (dopłata do tynku)", q["sciana_zewn"], "m²", C["elewacja"].get(el, 0))
    dodaj("SSZ", "Ściany działowe", q["dzialowe"], "m²", C["sciana_dzialowa"])
    dodaj("SSZ", "Stropy żelbetowe", q["stropy"], "m²", C["strop"])
    dodaj("SSZ", "Dachy płaskie (konstrukcja, ocieplenie, hydroizolacja)", q["dach_sedum"] + q["dach_zwir"], "m²", C["dach"])
    dodaj("SSZ", "Dach zielony (sedum)", q["dach_sedum"], "m²", C["dach_sedum"])
    dodaj("SSZ", "Dach żwirowy", q["dach_zwir"], "m²", C["dach_zwir"])
    dodaj("SSZ", "Okna aluminiowe 3-szybowe", q["okna"], "m²", C["okno"], True)
    dodaj("SSZ", "Przeszklenia stałe (fasady słupowo-ryglowe)", q["fasada"], "m²", C["fasada_szklana"], True)
    dodaj("SSZ", "Drzwi przesuwne HS", q["hs"], "m²", C["hs"], True)
    dodaj("SSZ", "Ściana szklana składana (zamykanie ogrodu)", q["harmonijka"], "m²", C["harmonijka"], True)
    dodaj("SSZ", "Drzwi wejściowe obrotowe (pivot)", q["drzwi_pivot"], "szt.", C["drzwi_pivot"])
    gl = 0 if q["drzwi_pivot"] else min(1, q["drzwi_wej"])          # bez pivota pierwsze drzwi są wejściowymi
    dodaj("SSZ", "Drzwi wejściowe", gl, "szt.", C["drzwi_wejsciowe"])
    dodaj("SSZ", "Drzwi zewnętrzne boczne / gospodarcze", q["drzwi_wej"] - gl, "szt.", C["drzwi_boczne"])
    if q["dach_ogrodu"]:
        dodaj("SSZ", f"Dach ogrodu: {DACH_OGRODU.get(q['dach_ogrodu'], q['dach_ogrodu'])}", q["ogrod_rzut"] * 1.08, "m²",
              C["dach_ogrodu"].get(q["dach_ogrodu"], 9000), True)
    dodaj("DEW", "Tynki wewnętrzne, wylewki, izolacje podłóg", q["pu"], "m²", C["tynki_wylewki"])
    dodaj("DEW", "Instalacja elektryczna", q["pu"], "m²", C["elektryka"])
    dodaj("DEW", "Instalacje wodno-kanalizacyjne", q["pu"], "m²", C["wodkan"])
    dodaj("DEW", "Ogrzewanie podłogowe", q["pu"] + q["ogrod_rzut"] * 0.5, "m²", C["podlogowka"])
    dodaj("DEW", "Pompa ciepła powietrze–woda", 1, "kpl.", C["pompa_ciepla"])
    dodaj("DEW", "Wentylacja z rekuperacją", 1, "kpl.", C["rekuperacja"])
    for k in q["schody"]:
        dodaj("DEW", {"spiral": "Schody kręcone stalowe", "straight": "Schody proste", "U": "Schody dwubiegowe"}.get(k, "Schody"),
              1, "kpl.", C["schody"].get(k, 24000))
    dodaj("DEW", "Tarasy na stropie (ocieplenie, hydroizolacja, deska)", q["tarasy"], "m²", C["taras"])
    dodaj("DEW", "Patio", q["patio"], "m²", C["patio"])
    dodaj("DEW", "Balustrady szklane", q["balustrada"], "mb", C["balustrada"])
    dodaj("PK", "Wykończenie wnętrz (podłogi, malowanie, sufity)", q["pu"], "m²", C["wykonczenie"])
    dodaj("PK", "Drzwi wewnętrzne", q["drzwi_wewn"], "szt.", C["drzwi_wewn"])
    for k, n in q["mokre"].items():
        dodaj("PK", {"lazienka": "Łazienki", "wc": "WC", "sauna": "Sauna"}[k], n, "kpl.", C[k])
    dodaj("PK", "Kuchnia (zabudowa i AGD)", q["kuchnie"], "kpl.", C["kuchnia"])
    dodaj("PK", "Ogród wewnętrzny (podłoże, drenaż, nawadnianie, rośliny)", q["ogrod_rzut"], "m²", C["ogrod_zielen"])
    if q["ogrod_styl"] in C["ogrod_styl"]:
        dodaj("PK", {"woda": "Ogród: woda (oczko / basen, filtracja)", "tropikalny": "Ogród: zamgławianie i nawilżanie",
                     "jadalnia": "Ogród-jadalnia: posadzka kamienna, oświetlenie"}[q["ogrod_styl"]], 1, "kpl.",
              C["ogrod_styl"][q["ogrod_styl"]])
    suma = {e: sum(p["wartosc"] for p in poz if p["etap"] == e) for e in ("SSZ", "DEW", "PK")}
    netto_budowa = suma["SSZ"] + suma["DEW"] + suma["PK"]
    dodaj("DOD", "Projekt, adaptacja, pozwolenia", 1, "kpl.", C["projekt"])
    dodaj("DOD", "Kierownik budowy, geodeta", 1, "kpl.", C["kierownik"])
    dodaj("DOD", f"Rezerwa na nieprzewidziane ({C['rezerwa'] * 100:.0f}%)", 1, "kpl.", netto_budowa * C["rezerwa"])
    suma["DOD"] = sum(p["wartosc"] for p in poz if p["etap"] == "DOD")
    narast = dict(SSZ=suma["SSZ"], DEW=suma["SSZ"] + suma["DEW"], PK=netto_budowa, RAZEM=netto_budowa + suma["DOD"])
    return dict(pozycje=poz, sumy=suma, narastajaco=narast, ilosci={k: v for k, v in q.items()},
                za_m2={k: round(v / q["pu"]) for k, v in narast.items()})


def wszystkie():
    out = []
    for w, kat in ((2, "domy"), (1, "domy_v1")):
        pids = sorted({os.path.basename(f)[:3] for f in glob.glob(os.path.join(HERE, kat, "p[0-9][0-9]_*.py"))} - {"p99"})
        for pid in pids:
            H = load(pid, kat).build()
            k = kosztorys(H)
            out.append(dict(wersja=w, pid=pid, numer=pid.upper(), nazwa=H.name, **k))
    return out


def zl(x):
    return f"{x:,.0f} zł".replace(",", "\u00a0")


def _l(x, w):
    return f"{x:>{w},}".replace(",", " ")


def tekst(d):
    """Kosztorys jednego domu jako tekst (opis na pendrive, podgląd w konsoli)."""
    q = d["ilosci"]
    tl = [f"KOSZTORYS SZACUNKOWY – {d['numer']} {d['nazwa']} (wersja {d['wersja']})",
          f"Powierzchnia użytkowa {q['pu']:.0f} m², ogród pod szkłem {q['ogrod_rzut']:.0f} m², tarasy {q['tarasy']:.0f} m²",
          f"Ceny brutto (VAT 8%), {POZIOM_CEN.lower()}, średni standard; dokładność ±15–20%.", ""]
    for e in ("SSZ", "DEW", "PK", "DOD"):
        tl.append(ETAPY[e].upper())
        for p in d["pozycje"]:
            if p["etap"] == e:
                tl.append(f"  {p['nazwa']:<62} {p['ilosc']:>8.1f} {p['jm']:<4} × {_l(p['cena'], 7)} = {_l(p['wartosc'], 11)} zł")
        tl.append(f"  {'razem':<62} {'':>8} {'':<4}   {'':>7}   {_l(d['sumy'][e], 11)} zł")
        tl.append("")
    n = d["narastajaco"]
    tl += [f"Stan surowy zamknięty:   {zl(n['SSZ'])}  ({zl(d['za_m2']['SSZ'])}/m²)",
           f"Stan deweloperski:       {zl(n['DEW'])}  ({zl(d['za_m2']['DEW'])}/m²)",
           f"Pod klucz:               {zl(n['PK'])}  ({zl(d['za_m2']['PK'])}/m²)",
           f"Razem z kosztami dodatkowymi: {zl(n['RAZEM'])}",
           "", "Poza kosztorysem: działka, przyłącza, ogrodzenie i zagospodarowanie działki, meble ruchome."]
    return "\n".join(tl)


def _cena_txt(klucz):
    if isinstance(klucz, tuple) and klucz[0] in CENY and isinstance(CENY[klucz[0]], dict):
        v = CENY[klucz[0]][klucz[1]]
    elif isinstance(klucz, tuple):
        return " / ".join(_cena_txt(k) for k in klucz)
    else:
        v = CENY[klucz]
    return f"{v * 100:.0f}%" if klucz == "rezerwa" else zl(v)


def strona(dane, out):
    """Strona porównania kosztów (HTML z danymi w środku) + miniatury domów w out/img."""
    from PIL import Image
    os.makedirs(os.path.join(out, "img"), exist_ok=True)
    domy, pliki = [], []
    for d in dane:
        w, pid = d["wersja"], d["pid"]
        img = None
        for src in (os.path.join(HERE, "portal", "pliki", f"v{w}_{pid}", "plakat.jpg"),
                    *glob.glob(os.path.join(HERE, "tv", "v*", "pliki", f"v{w}_{pid}", "plakat.jpg"))):
            if os.path.exists(src):
                img = f"img/v{w}_{pid}.jpg"
                dst = os.path.join(out, img)
                if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
                    im = Image.open(src).convert("RGB")
                    im.thumbnail((400, 225))
                    im.save(dst, "JPEG", quality=76, optimize=True, progressive=True)
                pliki.append(img)
                break
        q = d["ilosci"]
        domy.append(dict(w=w, pid=pid, nr=d["numer"], nazwa=d["nazwa"], pu=round(q["pu"], 1), ogrod=round(q["ogrod_rzut"], 1),
                         tarasy=round(q["tarasy"], 1), dach=DACH_OGRODU.get(q["dach_ogrodu"], ""), n=d["narastajaco"], s=d["sumy"],
                         poz=[[p["etap"], p["nazwa"], p["ilosc"], p["jm"], p["cena"], p["wartosc"], p["szklo"]] for p in d["pozycje"]],
                         img=img))
    v2 = [d for d in dane if d["wersja"] == 2]
    sr = lambda xs: sum(xs) / len(xs)   # noqa: E731
    pk_m2 = sr([d["za_m2"]["PK"] for d in v2])
    szklo = sr([sum(p["wartosc"] for p in d["pozycje"] if p["szklo"]) / d["narastajaco"]["PK"] for d in v2])
    bez = sr([(d["narastajaco"]["PK"] - sum(p["wartosc"] for p in d["pozycje"] if p["szklo"])) / d["ilosci"]["pu"] for d in v2])
    m2_szkla = sr([d["ilosci"]["okna"] + d["ilosci"]["fasada"] + d["ilosci"]["hs"] + d["ilosci"]["harmonijka"] for d in v2])
    m2_dachu = sr([d["ilosci"]["ogrod_rzut"] * 1.08 for d in v2])
    od, do = min(d["narastajaco"]["PK"] for d in v2), max(d["narastajaco"]["PK"] for d in v2)
    f = lambda x: f"{x:,.0f}".replace(",", "\u00a0")   # noqa: E731
    info = dict(
        opis=(f"Kosztorys {len(dane)} domów liczony z modeli projektów: {len(v2)} domów wersji 2 (do 170 m², ogród ukryty, "
              f"tarasy na niższych dachach) i {len(dane) - len(v2)} domów archiwalnej wersji 1. Dom z wersji 2 pod klucz to "
              + f"{od / 1e6:.2f}".replace(".", ",") + " – " + f"{do / 1e6:.2f}".replace(".", ",")
              + " mln zł; kliknij dom, żeby zobaczyć wszystkie pozycje."),
        poziom=POZIOM_CEN,
        drozej=(f"Typowy nowoczesny dom 160–170 m² z płaskim dachem kosztuje dziś ok. 6 500–9 500 zł/m² pod klucz. Tu średnio "
                f"{f(pk_m2)} zł/m², bo każdy dom ma średnio {m2_szkla:.0f} m² stolarki aluminiowej (okna, fasady, drzwi HS) "
                f"i {m2_dachu:.0f} m² otwieranego dachu szklanego nad ogrodem – to {szklo * 100:.0f}% kosztu pod klucz. "
                f"Po odjęciu szkła zostaje ok. {f(bez)} zł/m², czyli koszt zwykłego domu. Otwierany dach to też największa "
                "niewiadoma: w Polsce nie ma cenników, ceny bywają do dwóch razy wyższe lub niższe – przed budową trzeba "
                "zebrać oferty producentów."),
        stopka=("Kosztorys wskaźnikowy do porównania domów i rozmowy z wykonawcą – nie jest ofertą ani kosztorysem budowlanym. "
                "Ceny jednostkowe z portali cenowych (kb.pl, Murator, cenauslug.pl, Oferteo i inne – linki w tabeli), "
                "ilości z modeli domów. Region zmienia wszystkie kwoty o podany procent."),
        ceny=[dict(nazwa=n, jm=jm, cena=_cena_txt(k), zrodla=[dict(nazwa=a, url=u) for a, u in zr], uwaga=uw)
              for n, jm, k, zr, uw in ZRODLA],
        domy=domy)
    tpl = open(os.path.join(HERE, "kosztorys_szablon.html"), encoding="utf-8").read()
    tpl = tpl.replace("{{DANE}}", json.dumps(info, ensure_ascii=False).replace("</", "<\\/"))
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(tpl)
    return pliki


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pid", nargs="?")
    ap.add_argument("--wersja", type=int, default=2)
    ap.add_argument("--strona", default=os.path.join(HERE, "out", "kosztorys", "strona"), help="katalog strony porównania")
    a = ap.parse_args()
    if a.pid:
        H = load(a.pid, "domy" if a.wersja == 2 else "domy_v1").build()
        print(tekst(dict(wersja=a.wersja, pid=a.pid, numer=a.pid.upper(), nazwa=H.name, **kosztorys(H))))
    else:
        dane = wszystkie()
        os.makedirs(os.path.join(HERE, "out", "kosztorys"), exist_ok=True)
        json.dump(dane, open(os.path.join(HERE, "out", "kosztorys", "kosztorys.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1, default=str)
        pliki = strona(dane, a.strona)
        json.dump(pliki, open(os.path.join(a.strona, "pliki.json"), "w"), indent=0)
        for d in dane:
            n = d["narastajaco"]
            print(f"v{d['wersja']} {d['numer']} {d['nazwa']:<18} {d['ilosci']['pu']:6.0f} m²  SSZ {n['SSZ'] / 1e6:5.2f}  "
                  f"DEW {n['DEW'] / 1e6:5.2f}  PK {n['PK'] / 1e6:5.2f}  razem {n['RAZEM'] / 1e6:5.2f} mln zł  "
                  f"({d['za_m2']['PK']} zł/m² pod klucz)")
