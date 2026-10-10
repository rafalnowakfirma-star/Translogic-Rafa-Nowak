#!/usr/bin/env python3
"""Generuje stronę „Ogród w środku” – trzy koncepcje domu wokół ogrodu.

Uruchom:  python3 generuj.py   →  ogrod-w-srodku.html
Rysunki powstają z danych w k1_impluvium.py, k2_latarnia.py i k3_most.py.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from rysunek import pl, stained_rect, stained_rosette, stained_svg  # noqa: E402
import k1_impluvium  # noqa: E402
import k2_latarnia  # noqa: E402
import k3_most  # noqa: E402

OUT = os.path.join(HERE, "ogrod-w-srodku.html")

CONCEPTS = [
    {
        "key": "impluvium", "code": "A", "name": "Impluvium", "mod": k1_impluvium,
        "tag": "Dom-kwadrat wokół ogrodu, jak rzymskie atrium. Wszystkie niskie dachy spadają do środka, a deszcz schodzi łańcuchami do stawu.",
        "size": "14 × 14 m", "levels": "parter + piętro nad skrzydłem północnym", "garden": "23 m², zamknięty ze wszystkich stron",
        "build_m2": 173,
        "sec_title": "Przekrój północ–południe przez ogród",
        "plus": [
            "<b>Dach-lejek.</b> Niskie skrzydła mają spadek do ogrodu, rynny koszowe biegną wzdłuż dziedzińca, a woda schodzi trzema łańcuchami deszczowymi do stawu i kamiennych mis.",
            "<b>Galeria-bufor</b> od północy, wschodu i zachodu oddziela pokoje od zimnych ścian zewnętrznych. Służy też jako wiatrołap, biblioteka i miejsce na szafy.",
            "<b>Każdy pokój patrzy w ogród</b> przez przesuwne przeszklenia. Od ulicy dom jest prawie zamknięty, co daje dużo prywatności.",
            "<b>Łazienka z wanną ofuro</b> otwiera się na zamknięty ogród.",
            "<b>Piętro:</b> dormitorium z futonami na tatami i sypialnia z oknem na dziedziniec. Nad schodami jest witraż w dachu.",
        ],
        "minus": [
            "W koszach leja zbiera się śnieg. Potrzebne są rynny z kablami grzejnymi i przelewy awaryjne, a konstruktor musi policzyć zaspy.",
            "Cała woda z dachu trafia do ogrodu, więc potrzebny jest drenaż i zbiornik na deszczówkę.",
            "Galeria to ok. 30 m² komunikacji, więc dom wychodzi większy niż ten sam układ bez bufora.",
        ],
    },
    {
        "key": "latarnia", "code": "B", "name": "Latarnia", "mod": k2_latarnia,
        "tag": "Ośmiokąt z krętymi schodami w samym środku. Nad schodami latarnia z witrażu rzuca kolorowe światło na całe wnętrze.",
        "size": "12 m (ośmiokąt)", "levels": "parter + piętro", "garden": "patio 11 m², otwarte do nieba",
        "build_m2": 106,
        "sec_title": "Przekrój zachód–wschód przez patio i schody",
        "plus": [
            "<b>Środkowa klatka schodowa:</b> schody kręte pod ośmiokątną latarnią z witrażowymi ścianami i daszkiem.",
            "<b>Dach spada ze wszystkich stron do latarni.</b> Rynna pierścieniowa wylewa wodę miedzianym rzygaczem prosto do patio.",
            "<b>Patio w domu:</b> jeden z ośmiu segmentów jest otwarty do nieba i zamknięty murem z okrągłym oknem księżycowym.",
            "<b>Dormitorium</b> z futonami ułożonymi promieniście jak wskazówki zegara, a na piętrze loggia z widokiem na patio.",
            "<b>Bez korytarzy:</b> z rdzenia ze schodami wchodzi się prosto do każdego pokoju.",
        ],
        "minus": [
            "Ściany pod kątem 135° wymagają bloczków narożnych i wielu docinek, więc budowa trwa dłużej.",
            "W pokojach w kształcie klina trudniej ustawić meble, przyda się zabudowa na wymiar.",
            "Nie ma korytarza-bufora, więc ściany zewnętrzne trzeba bardzo dobrze ocieplić.",
        ],
    },
    {
        "key": "most", "code": "C", "name": "Most", "mod": k3_most,
        "tag": "Dwa skrzydła z opalanego drewna obejmują ogród, a nad wejściem przerzucony jest biały most z sypialnią.",
        "size": "17,2 × 11 m", "levels": "parter + most na piętrze", "garden": "ok. 38 m² z engawą, za murem z bramą",
        "build_m2": 150,
        "sec_title": "Przekrój przez schody, most i ogród",
        "plus": [
            "<b>Zamknięty ogród:</b> skrzydła po bokach, most od północy, a od południa mur z okrągłą bramą księżycową.",
            "<b>Engawa</b> to drewniana weranda pod mostem i wzdłuż skrzydeł. Można przejść z salonu do sypialni „przez ogród”.",
            "<b>Dachy motyle</b> (w kształcie litery V) mają rynnę w osi skrzydła. Woda wypływa rzygaczami do kamiennych mis przy tarasie.",
            "<b>Schody na osi domu</b> pod witrażem w dachu mostu. Sypialnia na moście patrzy na ogród.",
            "<b>Elewacja z opalanego drewna</b> (yakisugi) kontrastuje z białym mostem.",
        ],
        "minus": [
            "Most wysunięty nad ogród (ok. 1,2 m) i rozpiętość 6 m nad holem wymagają żelbetu albo stali i obliczeń konstruktora.",
            "Rynna w środku dachu motylego musi mieć spadek wzdłuż skrzydła, ogrzewanie i przelew awaryjny.",
            "Opalane drewno jest trwałe, ale potrzebuje porządnego rusztu i szczeliny wentylacyjnej.",
        ],
    },
]

WISHES = [
    ("Taras", ["●", "●", "●"], ["taras od ogrodu i loggia", "taras wokół salonu i loggia na piętrze", "taras i engawa"]),
    ("Zamknięty ogród w środku, dom dookoła", ["●", "◐", "●"], ["atrium z 4 stron", "patio w jednym segmencie", "skrzydła, most i mur"]),
    ("Mini ogród japoński", ["●", "●", "●"], ["", "", ""]),
    ("Sypialnia na górze", ["●", "●", "●"], ["", "", "na moście"]),
    ("Patio w domu", ["●", "●", "◐"], ["dziedziniec", "patio do nieba", "engawa pod mostem"]),
    ("Dormitorium", ["●", "●", "●"], ["na piętrze", "promieniste, na piętrze", "w skrzydle nocnym"]),
    ("Korytarz-bufor od zewnątrz", ["●", "—", "●"], ["N, E, W", "rdzeń zamiast korytarzy", "N, E, W"]),
    ("Środkowa klatka schodowa", ["◐", "●", "●"], ["w narożniku", "w samym środku", "na osi domu"]),
    ("Witraż w dachu", ["●", "●", "●"], ["świetlik", "cała latarnia", "świetlik"]),
    ("Dach spadający do środka, rynna środkowa", ["●", "●", "●"], ["lej do ogrodu", "lej do latarni", "dachy motyle"]),
]


def wish_table():
    rows = []
    for name, marks, notes in WISHES:
        lab = {"●": "w pełni", "◐": "częściowo", "—": "brak"}
        cells = "".join(f'<td><span class="mk mk{["●", "◐", "—"].index(m)}" role="img" aria-label="{lab[m]}"></span>{f"<small>{n}</small>" if n else ""}</td>'
                        for m, n in zip(marks, notes))
        rows.append(f"<tr><th scope='row'>{name}</th>{cells}</tr>")
    head = "".join(f"<th>{c['code']} · {c['name']}</th>" for c in CONCEPTS)
    return f"<table class='wish'><thead><tr><th>Twoje życzenie</th>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table>"


def sheet(code, title, body, note="", wide=False):
    return f"""
<figure class="sheet{' wide' if wide else ''}">
  <div class="sheet-draw">{body}</div>
  <figcaption class="tb"><span class="tb-code">{code}</span><span class="tb-title">{title}</span><span class="tb-meta">rysunek poglądowy</span></figcaption>
  {f'<p class="sheet-note">{note}</p>' if note else ''}
</figure>"""


def concept_section(c, data):
    g_area, u_area = data["areas"]
    total = g_area + u_area
    plus = "".join(f"<li>{t}</li>" for t in c["plus"])
    minus = "".join(f"<li>{t}</li>" for t in c["minus"])
    code = c["code"]
    return f"""
<section class="concept" id="{c['key']}">
  <div class="c-head">
    <div class="c-code">{code}</div>
    <div class="c-title"><h2>{c['name']}</h2><p class="lede">{c['tag']}</p></div>
  </div>
  <dl class="spec">
    <div><dt>Pow. użytkowa</dt><dd>ok. {round(total / 5) * 5} <small>m²</small></dd></div>
    <div><dt>Parter / piętro</dt><dd>{round(g_area)} / {round(u_area)} <small>m²</small></dd></div>
    <div><dt>Zabudowa</dt><dd>ok. {c['build_m2']} <small>m²</small></dd></div>
    <div><dt>Bryła</dt><dd class="sm">{c['size']}</dd></div>
    <div><dt>Ogród</dt><dd class="sm">{c['garden']}</dd></div>
  </dl>
  <div class="viewer" data-model="{c['key']}">
    <canvas aria-label="Model 3D – koncepcja {c['name']}. Przeciągnij, aby obrócić."></canvas>
    <div class="vctl" role="group" aria-label="Sterowanie widokiem">
      <button type="button" data-act="left" title="Obróć w lewo" aria-label="Obróć w lewo">⟲</button>
      <button type="button" data-act="right" title="Obróć w prawo" aria-label="Obróć w prawo">⟳</button>
      <button type="button" data-act="in" title="Przybliż" aria-label="Przybliż">+</button>
      <button type="button" data-act="out" title="Oddal" aria-label="Oddal">−</button>
      <button type="button" data-act="top">Z góry</button>
      <button type="button" data-act="eye">Z ziemi</button>
      <button type="button" data-act="home">Start</button>
    </div>
    <p class="vhint">Przeciągnij, aby obrócić model</p>
    <p class="vno">Model 3D nie działa w tej przeglądarce. Rzuty i przekrój są poniżej.</p>
  </div>
  <div class="sheets">
    {sheet(code + "-01", "Rzut parteru", data["plans"][0])}
    {sheet(code + "-02", "Rzut piętra", data["plans"][1])}
    {sheet(code + "-03", c["sec_title"], data["section"], wide=True)}
  </div>
  <div class="pros">
    <div class="panel"><h3>Co tu jest niezwykłego</h3><ul>{plus}</ul></div>
    <div class="panel"><h3>Na co uważać</h3><ul>{minus}</ul></div>
  </div>
</section>"""


CSS = r"""
/* Układ: arkusze rysunkowe na jasnym papierze; każda koncepcja to blok z modelem 3D, rzutami i przekrojem. */
:root{
  --paper:#F1F2EE; --sheet:#FFFFFF; --ink:#1E2124; --ink-2:#4F565C; --ink-3:#8E959A; --rule:#D5D8D3;
  --accent:#9B3B2B; --accent-soft:#F5E6E2;
  --f-wood:#F3E9DA; --f-stone:#E7E6E1; --void:#E9ECEE; --glass-plan:#BFD8E8;
  --lawn:#E4EBDB; --gravel:#EEEBE3; --stone:#B7B2A8; --moss:#9FB57E; --maple:#C9573C; --maple2:#E08A4B;
  --pine:#4E7A55; --pine2:#2F5A3A; --water:#8DB8D2; --waterdk:#2F6E95; --bamboo:#7E9F4E; --copper:#B06E3C;
  --deckc:#C9A57A; --roofplan:#D9DCDD; --tatami:#E6E3BE; --tatami-l:#B9B48A;
  --sky1:#DCE7EF; --sky2:#F1F2EE;
  --display:"Shippori Mincho","Noto Serif",Georgia,serif;
  --body:"Zen Kaku Gothic New","Noto Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#121416; --sheet:#1A1D20; --ink:#E4E6E2; --ink-2:#ABB2B7; --ink-3:#717A80; --rule:#2C3236;
    --accent:#E08D74; --accent-soft:#3A2622;
    --f-wood:#2A2620; --f-stone:#24262A; --void:#22272B; --glass-plan:#2D4A5E;
    --lawn:#1D241B; --gravel:#2A2A27; --stone:#6F6B64; --moss:#56704A; --maple:#B44E37; --maple2:#C97A44;
    --pine:#3E6446; --pine2:#284A31; --water:#3B6E8E; --waterdk:#8FC3E2; --bamboo:#64803F; --copper:#C98450;
    --deckc:#6E5A42; --roofplan:#2C3135; --tatami:#3A3828; --tatami-l:#5A5638;
    --sky1:#1C2632; --sky2:#121416; color-scheme:dark;
  }
}
:root[data-theme="dark"]{
    --paper:#121416; --sheet:#1A1D20; --ink:#E4E6E2; --ink-2:#ABB2B7; --ink-3:#717A80; --rule:#2C3236;
    --accent:#E08D74; --accent-soft:#3A2622;
    --f-wood:#2A2620; --f-stone:#24262A; --void:#22272B; --glass-plan:#2D4A5E;
    --lawn:#1D241B; --gravel:#2A2A27; --stone:#6F6B64; --moss:#56704A; --maple:#B44E37; --maple2:#C97A44;
    --pine:#3E6446; --pine2:#284A31; --water:#3B6E8E; --waterdk:#8FC3E2; --bamboo:#64803F; --copper:#C98450;
    --deckc:#6E5A42; --roofplan:#2C3135; --tatami:#3A3828; --tatami-l:#5A5638;
    --sky1:#1C2632; --sky2:#121416; color-scheme:dark;
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font:15px/1.65 var(--body)}
.wrap{max-width:1180px;margin:0 auto;padding-inline:20px;padding-block:24px 64px}
.text{max-width:68ch}
a{color:var(--accent)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
h1,h2,h3{font-family:var(--display);font-weight:700;line-height:1.1;text-wrap:balance;margin:0;letter-spacing:.01em}
h1{font-size:clamp(42px,7.5vw,80px);font-weight:800}
h2{font-size:clamp(30px,4.4vw,46px)}
h3{font-size:20px;margin-bottom:6px}
p{margin:0 0 12px}
.eyebrow{font:500 12px/1.3 var(--mono);text-transform:uppercase;letter-spacing:.14em;color:var(--ink-2);margin-bottom:14px}
.lede{font-size:17px;color:var(--ink-2);max-width:64ch;margin-top:10px}
section{margin-top:64px}
.hero{display:grid;grid-template-columns:minmax(0,1.2fr) minmax(0,1fr);gap:28px;align-items:end}
@media (max-width:820px){.hero{grid-template-columns:1fr}}
.hero-w{background:var(--sheet);border:1px solid var(--rule);padding:14px}
.hero-w figcaption{font-size:12.5px;color:var(--ink-2);margin-top:8px}

.bar{position:sticky;top:env(safe-area-inset-top,0px);z-index:5;background:var(--paper);border-bottom:1px solid var(--rule);margin-top:26px;
  display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;justify-content:space-between;padding-block:10px}
.bar nav{display:flex;flex-wrap:wrap;gap:4px 16px;font:500 13px var(--mono)}
.bar nav a{color:var(--ink);text-decoration:none}
.bar nav a:hover{color:var(--accent)}
.seg{display:inline-flex;border:1.5px solid var(--ink)}
.seg span{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.08em;color:var(--ink-2);padding:6px 10px;border-right:1.5px solid var(--ink)}
.seg button{font:500 13px var(--body);background:var(--sheet);color:var(--ink);border:0;padding:6px 12px;cursor:pointer}
.seg button+button{border-left:1px solid var(--rule)}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--sheet)}

table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;vertical-align:top;padding:9px 12px;border-bottom:1px solid var(--rule)}
thead th{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.08em;color:var(--ink-2);background:var(--paper);white-space:nowrap}
.tablewrap{overflow-x:auto;margin-top:16px;border:1px solid var(--rule);background:var(--sheet)}
.wish tbody th{font-weight:600;min-width:200px}
.wish td{min-width:150px}
.wish small{display:block;color:var(--ink-2);font-size:12px;line-height:1.35}
.mk{display:inline-block;width:13px;height:13px;border-radius:50%;border:1.5px solid var(--accent);vertical-align:-1px}
.mk0{background:var(--accent)} .mk1{background:linear-gradient(90deg,var(--accent) 50%,transparent 50%)}
.mk2{border:0;border-radius:0;height:2px;width:14px;background:var(--ink-3);vertical-align:4px}
.legend-mk{display:inline-flex;align-items:center;gap:6px;margin-right:14px}
.num{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums;white-space:nowrap}

.concept{border-top:2px solid var(--ink);padding-top:22px}
.c-head{display:flex;gap:18px;align-items:flex-start}
.c-code{font:800 64px/0.9 var(--display);color:var(--accent);min-width:52px}
.c-title{min-width:0}
.spec{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));border:1.5px solid var(--ink);margin:20px 0 0;background:var(--sheet)}
.spec div{padding:10px 14px;border-right:1px solid var(--rule);border-bottom:1px solid var(--rule);min-width:0}
.spec dt{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.08em;color:var(--ink-2)}
.spec dd{margin:2px 0 0;font:700 26px/1.15 var(--display);font-variant-numeric:tabular-nums}
.spec dd.sm{font:500 15px/1.35 var(--body);padding-top:4px}
.spec dd small{font:500 13px var(--body);color:var(--ink-2)}

.viewer{position:relative;margin-top:18px;border:1.5px solid var(--ink);background:linear-gradient(180deg,var(--sky1),var(--sky2));aspect-ratio:16/9;max-height:620px;width:100%}
@media (max-width:640px){.viewer{aspect-ratio:4/3}}
.viewer canvas{display:block;width:100%;height:100%;cursor:grab;touch-action:pan-y}
.viewer canvas:active{cursor:grabbing}
.vctl{position:absolute;right:10px;bottom:10px;display:flex;flex-wrap:wrap;gap:4px;justify-content:flex-end;max-width:calc(100% - 20px)}
.vctl button{font:500 13px var(--body);min-width:34px;height:32px;padding:0 10px;border:1px solid var(--ink);background:var(--sheet);color:var(--ink);cursor:pointer}
.vctl button:hover{background:var(--ink);color:var(--sheet)}
.vhint{position:absolute;left:12px;top:10px;margin:0;font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.08em;color:var(--ink-2)}
.vno{display:none;position:absolute;inset:0;margin:0;align-items:center;justify-content:center;text-align:center;padding:20px;color:var(--ink-2)}
.viewer.no3d .vno{display:flex} .viewer.no3d .vctl,.viewer.no3d .vhint{display:none}

.sheets{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,500px),1fr));gap:20px;margin-top:20px}
.sheet{margin:0;background:var(--sheet);border:1.5px solid var(--ink);display:flex;flex-direction:column;min-width:0}
.sheet.wide{grid-column:1/-1}
.sheet-draw{overflow-x:auto;padding:6px}
.sheet-draw svg{display:block;width:100%;height:auto;min-width:440px}
.tb{display:grid;grid-template-columns:auto 1fr auto;border-top:1.5px solid var(--ink);font:500 12px var(--mono);margin-top:auto}
.tb>span{padding:7px 10px;border-right:1px solid var(--ink);display:flex;align-items:center;min-width:0}
.tb>span:last-child{border-right:0}
.tb-code{font:700 15px var(--mono);background:var(--ink);color:var(--sheet)}
.tb-title{font:700 15px var(--display)}
.tb-meta{color:var(--ink-2)}
@media (max-width:560px){.tb{grid-template-columns:auto 1fr}.tb-meta{display:none}}
.sheet-note{font-size:13px;color:var(--ink-2);padding:8px 12px 12px;margin:0;border-top:1px solid var(--rule)}
.nofurn .furn{display:none}

.pros{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,340px),1fr));gap:18px;margin-top:20px}
.panel{background:var(--sheet);border:1px solid var(--rule);padding:16px 18px;min-width:0}
.panel ul{margin:6px 0 0;padding-left:18px}
.panel li{margin-bottom:7px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,250px),1fr));gap:16px;margin-top:18px}
.card{background:var(--sheet);border:1px solid var(--rule);padding:14px 16px;min-width:0}
.card h3{font-size:18px}
.card p{font-size:14px;color:var(--ink-2);margin:0}
.card .k{font:500 11px var(--mono);text-transform:uppercase;letter-spacing:.08em;color:var(--accent);margin-bottom:6px}
.witraze{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:18px;margin-top:18px;align-items:start}
@media (max-width:700px){.witraze{grid-template-columns:1fr}}
.witraze figure{margin:0;background:var(--sheet);border:1px solid var(--rule);padding:12px}
.witraze figcaption{font-size:12.5px;color:var(--ink-2);margin-top:8px}
svg.illus{display:block;width:100%;height:auto}
.legend{display:flex;flex-wrap:wrap;gap:8px 18px;font-size:13px;color:var(--ink-2);margin-top:12px}
.legend i{display:inline-block;width:22px;height:10px;vertical-align:-1px;margin-right:6px;border:1px solid var(--ink)}
.foot{margin-top:64px;padding-top:16px;border-top:1.5px solid var(--ink);font-size:13px;color:var(--ink-2)}

/* rysunki */
.w-outer,.w-inner,.w-part{fill:none;stroke:var(--ink);stroke-linejoin:miter;stroke-miterlimit:8}
.w-garden{fill:none;stroke:var(--ink-2)}
.w-col{fill:var(--ink)}
.w-glass{fill:none;stroke:var(--glass-plan)} .w-glassline{fill:none;stroke:var(--ink);stroke-width:.8}
.o-cut{fill:var(--sheet)} .o-jamb{stroke:var(--ink);stroke-width:1}
.o-glass{fill:var(--glass-plan);stroke:var(--ink);stroke-width:.6}
.o-pane{stroke:var(--ink);stroke-width:1.5} .o-leaf{stroke:var(--ink);stroke-width:1.6}
.o-swing{fill:none;stroke:var(--ink-2);stroke-width:.6;stroke-dasharray:2 2}
.o-moon{fill:none;stroke:var(--ink-2);stroke-width:.9;stroke-dasharray:3 2}
.f-wood{fill:var(--f-wood)} .f-stone{fill:var(--f-stone)} .f-tatami{fill:url(#tatami)} .f-deck{fill:url(#deckpat)}
.fu{fill:var(--sheet);stroke:var(--ink-3);stroke-width:.7}
.g-lawn{fill:var(--lawn)} .g-deck{fill:url(#deckpat)} .g-path{fill:var(--f-stone);stroke:var(--ink-3);stroke-width:.5}
.g-gravel{fill:url(#rake)} .g-ripple{fill:var(--gravel);stroke:var(--ink-3);stroke-width:.6}
.g-stone{fill:var(--stone);stroke:var(--ink-2);stroke-width:.7}
.g-moss{fill:var(--moss)} .g-maple{fill:var(--maple);opacity:.9} .g-maple2{fill:var(--maple2);opacity:.8} .g-trunk{fill:var(--ink-2)}
.g-pine{fill:var(--pine)} .g-pineline{stroke:var(--pine2);stroke-width:.8}
.g-water{fill:var(--water)} .g-lantern{fill:var(--stone);stroke:var(--ink-2);stroke-width:.7} .g-lanternl{stroke:var(--ink-2);stroke-width:.6}
.g-step{fill:var(--stone);stroke:var(--ink-3);stroke-width:.5} .g-bamboo{fill:var(--bamboo)}
.g-chain{fill:none;stroke:var(--copper);stroke-width:1.8} .g-chaindot{fill:var(--copper)}
.st-box{fill:var(--sheet);stroke:var(--ink);stroke-width:.8} .st-tread{stroke:var(--ink-2);stroke-width:.6}
.st-walk{stroke:var(--ink);stroke-width:.9;fill:none} .st-dot,.st-post{fill:var(--ink)}
.st-void{fill:var(--void);stroke:var(--ink);stroke-width:.6} .st-x{stroke:var(--ink-3);stroke-width:.5}
.st-rail{stroke:var(--ink);stroke-width:2.2} .st-railc{fill:none;stroke:var(--ink);stroke-width:1.6}
.sky-proj{fill:none;stroke:var(--accent);stroke-width:1.1;stroke-dasharray:6 3}
.roof-below{fill:var(--roofplan);stroke:var(--ink-2);stroke-width:.8}
.valley{stroke:var(--waterdk);stroke-width:1.4;stroke-dasharray:8 3}
.flow{stroke:var(--waterdk);stroke-width:1.4}
.d-dim{stroke:var(--accent);stroke-width:.7} .d-tick{stroke:var(--accent);stroke-width:1.3}
.d-t{fill:var(--accent);font:500 10px var(--mono)}
.t-room{fill:var(--ink);font:700 12.5px var(--body)} .t-room-s{fill:var(--ink);font:700 10.5px var(--body)}
.t-area{fill:var(--ink-2);font:400 9.5px var(--mono)}
.t-note{fill:var(--ink-2);font:400 9.5px var(--body)}
.t-garden{fill:var(--ink-2);font:italic 600 12px var(--display);letter-spacing:.06em}
.t-label{fill:var(--ink);font:700 13px var(--body)}
.t-sroom{fill:var(--ink);font:700 11px var(--body)}
.na-c{fill:none;stroke:var(--ink);stroke-width:.8} .na-p{fill:var(--ink)}
.sb-a{fill:var(--ink)} .sb-b{fill:var(--sheet);stroke:var(--ink);stroke-width:.6}
.s-ground{fill:url(#hatch-ground)} .s-line{stroke:var(--ink);stroke-width:1.2}
.s-cut{fill:var(--ink)} .s-glass{fill:var(--glass-plan);stroke:var(--ink);stroke-width:.6}
.s-roof{fill:url(#hatch-wool);stroke:var(--ink);stroke-width:1.2}
.s-gravel{fill:var(--gravel);stroke:var(--ink-3);stroke-width:.5} .s-water{fill:var(--water)}
.s-deck{fill:var(--deckc)} .s-stone{fill:var(--stone);stroke:var(--ink-2);stroke-width:.6}
.s-beyond{fill:none;stroke:var(--ink-3);stroke-width:.8;stroke-dasharray:4 3} .s-beyondf{fill:var(--void)}
.s-chain{stroke:var(--copper);stroke-width:.8} .s-link{fill:none;stroke:var(--copper);stroke-width:1.1}
.s-flow{stroke:var(--waterdk);stroke-width:1.8}
.s-thin{stroke:var(--ink);stroke-width:.6} .s-lvl{fill:var(--sheet);stroke:var(--ink);stroke-width:.8}
.s-person{fill:var(--ink-2)} .s-trunk{stroke:var(--ink-2);stroke-width:2}
.s-tree{fill:var(--pine);opacity:.85} .s-maple{fill:var(--maple);opacity:.9}
.s-leader{fill:none;stroke:var(--ink-2);stroke-width:.6} .s-dot{fill:var(--ink)}
.s-stained{fill:url(#stainedpat);stroke:var(--ink);stroke-width:.8}
.s-post{stroke:var(--ink);stroke-width:2.2} .s-tread{fill:var(--ink-2)}
.p-rake{stroke:var(--ink-3);stroke-width:.5;opacity:.55} .p-base{fill:var(--gravel)}
.p-deckb{fill:var(--deckc)} .p-deckl{stroke:var(--ink-3);stroke-width:.5;opacity:.6}
.p-tat{fill:var(--tatami);stroke:var(--tatami-l);stroke-width:1}
.p-ground{stroke:var(--ink-3);stroke-width:.7} .p-wool{stroke:var(--ink-3);stroke-width:.6;fill:none} .p-woolb{fill:var(--sheet)}
#arrow path{fill:var(--ink)} #arrow-w path{fill:var(--waterdk)}
"""

DEFS = """<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<pattern id="rake" width="8" height="4" patternUnits="userSpaceOnUse"><rect width="8" height="4" class="p-base"/><line x1="0" y1="2" x2="8" y2="2" class="p-rake"/></pattern>
<pattern id="deckpat" width="40" height="6" patternUnits="userSpaceOnUse"><rect width="40" height="6" class="p-deckb"/><line x1="0" y1="5.5" x2="40" y2="5.5" class="p-deckl"/></pattern>
<pattern id="tatami" width="68.4" height="68.4" patternUnits="userSpaceOnUse">
  <rect x="0.5" y="0.5" width="33.2" height="67.4" class="p-tat"/><rect x="34.7" y="0.5" width="33.2" height="33.2" class="p-tat"/><rect x="34.7" y="34.7" width="33.2" height="33.2" class="p-tat"/></pattern>
<pattern id="hatch-ground" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="9" class="p-ground"/></pattern>
<pattern id="hatch-wool" width="10" height="6" patternUnits="userSpaceOnUse"><rect width="10" height="6" class="p-woolb"/><path d="M0,3 C2.5,0 2.5,6 5,3 S7.5,0 10,3" class="p-wool"/></pattern>
<pattern id="stainedpat" width="12" height="12" patternUnits="userSpaceOnUse">
  <rect width="6" height="6" fill="#C1272D"/><rect x="6" width="6" height="6" fill="#2E6FB0"/><rect y="6" width="6" height="6" fill="#E8A317"/><rect x="6" y="6" width="6" height="6" fill="#29A0A2"/></pattern>
<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker>
<marker id="arrow-w" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z"/></marker>
</defs></svg>"""

TOGGLE_JS = r"""
(function(){
  var root=document.getElementById("app");
  var btns=document.querySelectorAll("[data-furn]");
  function set(on){
    root.classList.toggle("nofurn",!on);
    btns.forEach(function(b){b.setAttribute("aria-pressed",String((b.getAttribute("data-furn")==="1")===on));});
    try{localStorage.setItem("ogrod-meble",on?"1":"0");}catch(e){}
  }
  var saved=null; try{saved=localStorage.getItem("ogrod-meble");}catch(e){}
  set(saved!=="0");
  btns.forEach(function(b){b.addEventListener("click",function(){set(b.getAttribute("data-furn")==="1");});});
})();
"""


def build():
    data = {c["key"]: c["mod"].build() for c in CONCEPTS}
    rect_cells = stained_rect(7)
    rose_cells = stained_rosette(11)
    js_data = {
        "models": {k: v["model"] for k, v in data.items()},
        "stained": {"rect": [[[[round(x, 4), round(y, 4)] for x, y in poly], col] for poly, col in rect_cells],
                    "rose": [[[[round(x, 4), round(y, 4)] for x, y in poly], col] for poly, col in rose_cells]},
    }
    viewer_js = open(os.path.join(HERE, "viewer.js"), encoding="utf-8").read()
    w_rect = stained_svg(rect_cells, 600, 300, "Projekt witrażu do świetlika: słońce nad wodą")
    w_rose = stained_svg(rose_cells, 300, 300, "Projekt witrażu do latarni: rozeta ośmiokątna", clip_oct=True)
    concepts_html = "".join(concept_section(c, data[c["key"]]) for c in CONCEPTS)
    cmp_rows = []
    for c in CONCEPTS:
        g, u = data[c["key"]]["areas"]
        cmp_rows.append(f"<tr><th scope='row'>{c['code']} · {c['name']}</th><td class='num'>ok. {round((g + u) / 5) * 5} m²</td>"
                        f"<td class='num'>ok. {c['build_m2']} m²</td><td>{c['size']}</td><td>{c['garden']}</td></tr>")
    html = f"""<title>Ogród w środku</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@600;700;800&family=Zen+Kaku+Gothic+New:wght@400;500;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
{DEFS}
<div class="wrap" id="app">
<header class="hero">
  <div>
    <div class="eyebrow">Trzy koncepcje domu · ogród japoński w środku · rysunki poglądowe</div>
    <h1>Ogród w&nbsp;środku</h1>
    <p class="lede">Trzy różne domy zbudowane wokół Twoich pomysłów: zamknięty ogród japoński w środku, korytarz-bufor po zewnętrznej stronie, schody pod witrażem w dachu, dach spadający do środka z rynną i łańcuchami deszczowymi, sypialnia na piętrze i dormitorium. Każdy ma model 3D do obracania, rzuty z meblami i bez oraz przekrój.</p>
  </div>
  <figure class="hero-w" style="margin:0">
    {w_rect}
    <figcaption>Witraż „słońce nad wodą” do świetlika nad schodami (koncepcje A i C).</figcaption>
  </figure>
</header>

<div class="bar">
  <nav aria-label="Koncepcje"><a href="#zyczenia">Życzenia</a><a href="#impluvium">A · Impluvium</a><a href="#latarnia">B · Latarnia</a><a href="#most">C · Most</a><a href="#dach">Dach do środka</a><a href="#bufor">Bufor</a><a href="#witraz">Witraż</a><a href="#ogrod">Ogród</a></nav>
  <div class="seg" role="group" aria-label="Meble na rzutach"><span>Rzuty</span><button type="button" data-furn="1" aria-pressed="true">Z meblami</button><button type="button" data-furn="0" aria-pressed="false">Bez mebli</button></div>
</div>

<section id="zyczenia" style="margin-top:36px">
  <h2>Twoje życzenia w trzech domach</h2>
  <p class="text"><span class="legend-mk"><span class="mk mk0"></span>w pełni</span><span class="legend-mk"><span class="mk mk1"></span>częściowo</span><span class="legend-mk"><span class="mk mk2"></span>brak</span><br>Każda koncepcja kładzie nacisk na co innego, więc warto wybrać tę, która trafia w najważniejsze dla Ciebie punkty. Elementy można też przenosić między projektami.</p>
  <div class="tablewrap">{wish_table()}</div>
</section>

{concepts_html}

<section id="dach">
  <h2>Czy dach musi być spadzisty na zewnątrz?</h2>
  <p class="text">Nie. Dach może spadać do środka, a woda może trafiać do ogrodu zamiast do rynien na elewacji. W każdej z trzech koncepcji jest inny wariant takiego dachu.</p>
  <div class="cards">
    <div class="card"><div class="k">A · Impluvium</div><h3>Dach lejowy</h3><p>Cztery połacie spadają do dziedzińca, jak w rzymskim atrium. Rynny koszowe przy ogrodzie, łańcuchy w narożnikach.</p></div>
    <div class="card"><div class="k">B · Latarnia</div><h3>Lej do latarni</h3><p>Osiem połaci spada do pierścienia wokół latarni. Rynna pierścieniowa wylewa wodę rzygaczem do patio.</p></div>
    <div class="card"><div class="k">C · Most</div><h3>Dach motyli</h3><p>Dwie połacie w kształcie litery V z rynną w osi skrzydła, z odpływem na końcu skrzydła do kamiennej misy.</p></div>
    <div class="card"><div class="k">Alternatywa</div><h3>Płaski dach zielony</h3><p>Spadek 2–3% do wpustów w środku, na wierzchu rozchodniki. Najprostszy w obróbkach, ale wizualnie spokojniejszy.</p></div>
  </div>
  <div class="panel" style="margin-top:18px"><h3>Żeby działało w polskim klimacie</h3><ul>
    <li>Rynny w koszach i przy ogrodzie powinny być szersze niż zwykle i mieć kable grzejne. Zimą zamarznięta rynna to największe ryzyko.</li>
    <li>Obok każdego odpływu potrzebny jest przelew awaryjny (rzygacz), który wyrzuci wodę, gdy rynna się zatka.</li>
    <li>Śnieg zsuwa się do środka i zalega w koszu, więc konstruktor liczy dodatkowe obciążenie (worek śnieżny).</li>
    <li>Pokrycie: blacha na rąbek albo membrana EPDM z obróbkami w koszu, spadek zgodny z wymaganiami producenta.</li>
    <li>Łańcuch deszczowy zimą obrasta lodem i wygląda pięknie, ale potrzebuje mocnego zaczepu. Pod łańcuchem kładzie się misę albo drenaż z kamieni.</li>
    <li>Wodę warto zbierać do podziemnego zbiornika i używać do podlewania ogrodu, a nadmiar oddawać do skrzynek rozsączających.</li>
  </ul></div>
</section>

<section id="bufor">
  <h2>Korytarz-bufor po zewnętrznej stronie</h2>
  <div class="pros">
    <div class="panel"><h3>Co daje</h3><ul>
      <li>Pokoje nie stykają się z zimną ścianą zewnętrzną. Między nimi jest strefa o temperaturze pośredniej, więc z pokoi ucieka mniej ciepła.</li>
      <li>Bufor wycisza dom od ulicy i od wiatru.</li>
      <li>Korytarz pracuje jako wiatrołap, szafa, biblioteka albo galeria i nie jest pustym przejściem.</li>
    </ul></div>
    <div class="panel"><h3>Jak go dobrze ustawić</h3><ul>
      <li>Najlepiej od północy, wschodu i zachodu, tak jak w koncepcjach A i C. Od południa lepiej otworzyć pokoje na słońce, bo ono ogrzewa za darmo.</li>
      <li>Ściana zewnętrzna bufora nadal musi być w pełni ocieplona. Bufor zmniejsza straty, ale nie zastępuje izolacji.</li>
      <li>Pokoje dostają wtedy światło głównie od ogrodu, dlatego od ogrodu są duże przeszklenia, a w buforze wąskie okna.</li>
    </ul></div>
  </div>
</section>

<section id="witraz">
  <h2>Witraż w dachu</h2>
  <div class="witraze">
    <figure>{w_rect}<figcaption>Świetlik nad schodami: słońce nad wodą (A, C). Kolorowe światło przesuwa się po ścianach klatki schodowej w ciągu dnia.</figcaption></figure>
    <figure>{w_rose}<figcaption>Rozeta do latarni (B): ośmiokrotna symetria jak rzut domu.</figcaption></figure>
  </div>
  <div class="panel" style="margin-top:18px"><ul>
    <li>Prawdziwy witraż ołowiany zamyka się wewnątrz szyby zespolonej albo wiesza tuż pod zwykłym, szczelnym świetlikiem. Dzięki temu nie przecieka i nie traci ciepła.</li>
    <li>Wieczorem podświetlenie LED nad witrażem zamienia go w lampę nad schodami.</li>
    <li>Wzór można zamówić w pracowni witrażu, a te dwa projekty mogą być punktem wyjścia do rozmowy.</li>
  </ul></div>
</section>

<section id="ogrod">
  <h2>Mini ogród japoński</h2>
  <div class="cards">
    <div class="card"><h3>Żwir grabiony</h3><p>Karesansui: żwir grabiony w linie i kręgi wokół kamieni udaje wodę. Potrzebuje mało pielęgnacji.</p></div>
    <div class="card"><h3>Kamienie i mech</h3><p>Trzy większe kamienie w nieparzystym układzie, wyspy mchu (albo karmnika ościstego w cieniu).</p></div>
    <div class="card"><h3>Klon palmowy</h3><p>Acer palmatum jest czerwony jesienią i zimuje w osłoniętym dziedzińcu. Zamiast sosny formowanej może być sosna górska.</p></div>
    <div class="card"><h3>Bambus bez kłopotu</h3><p>Tylko odmiany kępowe (Fargesia), które nie rozrastają się rozłogami pod ścianami domu.</p></div>
    <div class="card"><h3>Woda</h3><p>Staw albo kamienna misa tsukubai pod łańcuchem deszczowym. Deszcz z dachu sam ją napełnia.</p></div>
    <div class="card"><h3>Latarnia i ścieżka</h3><p>Kamienna latarnia tōrō i ścieżka z płaskich kamieni prowadząca od tarasu przez ogród.</p></div>
  </div>
</section>

<section id="porownanie">
  <h2>Porównanie</h2>
  <div class="tablewrap"><table>
    <thead><tr><th>Koncepcja</th><th class="num">Pow. użytkowa</th><th class="num">Zabudowa</th><th>Bryła</th><th>Ogród</th></tr></thead>
    <tbody>{''.join(cmp_rows)}</tbody>
  </table></div>
  <p class="text" style="margin-top:14px">Wszystkie trzy da się postawić z bloczków ICF, o których była mowa wcześniej. Proste ściany A i C pasują do nich najlepiej, a ośmiokąt B wymaga bloczków narożnych. Powierzchnie są orientacyjne: na poddaszach i pod skosami nie odejmowano stref niższych niż 2,2 m.</p>
</section>

<footer class="foot">
  <p>To koncepcje poglądowe, czyli układ, nastrój i pomysły na rozwiązania. Nie są to projekty budowlane. Wymiary są przybliżone. Przed budową architekt dopasuje wybraną koncepcję do działki i planu miejscowego (kąt i kształt dachu bywają tam narzucone), a konstruktor policzy dachy odwrócone, wspornik mostu i duże przeszklenia.</p>
  <p>Rysunki i modele wygenerowano skryptem <code>generuj.py</code>.</p>
</footer>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>window.OGROD = {json.dumps(js_data, separators=(",", ":"))};</script>
<script>{viewer_js}</script>
<script>{TOGGLE_JS}</script>
"""
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)
    for c in CONCEPTS:
        g, u = data[c["key"]]["areas"]
        print(f"{c['name']}: parter {g:.1f} m², piętro {u:.1f} m², razem {g + u:.1f} m²")
    print(f"zapisano {OUT} ({os.path.getsize(OUT) // 1024} kB)")


if __name__ == "__main__":
    build()
