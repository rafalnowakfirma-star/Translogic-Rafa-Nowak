#!/usr/bin/env python3
"""Strona „Ogrody pod szkłem”: zbiera domy z domy/pXX_*.py i składa katalog w strona/.

  python3 generuj.py            → strona/index.html + strona/pXX/* (rysunki SVG, modele 3D, zdjęcia)

Zdjęcia brane są z out/pXX/render/ (rendery końcowe), a gdy ich nie ma – z out/pXX/podglad3d/.
"""
import glob
import html
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from podglad import load  # noqa: E402
from silnik.rzut import plan_level, plan_roof, ROOF_NOTE  # noqa: E402
from silnik.przekroj import section  # noqa: E402
from silnik.bryla import build_mesh, export_json  # noqa: E402
from silnik.geom import polygons  # noqa: E402
from shapely.ops import unary_union  # noqa: E402
from dane.inspiracje import REFS, DACH_FAKTY  # noqa: E402

OUT = os.path.join(HERE, "strona")
E = html.escape

GARDEN = {"japonski": "japoński", "oranzeria": "oranżeria", "woda": "wodny", "las": "leśny",
          "srodziemnomorski": "śródziemnomorski", "tropikalny": "tropikalny"}
ROOF_SHORT = {"slide": "przesuwny", "louvre": "lamelowy", "fold": "harmonijkowy", "iris": "kopuła-migawka",
              "pyramid": "piramida z latarnią", "ridge": "dwuspadowy", "vault": "kolebka"}
FACADE = {"tynk": "biały tynk", "beton": "beton architektoniczny", "drewno": "drewno (modrzew)",
          "drewno_opal": "drewno opalane", "cegla": "cegła", "cegla_biala": "biała cegła", "kamien": "kamień",
          "corten": "stal corten", "miedz": "miedź", "blacha": "blacha na rąbek", "trawertyn": "trawertyn"}
VIEWS = [("lotu", "Z lotu ptaka, lato – dach ogrodu otwarty"), ("ogrod", "W ogrodzie pod szklanym dachem"),
         ("zmierzch", "Zimowy zmierzch – dach zamknięty, światła w domu")]


def nice(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


# ------------------------------------------------------------------ materiały do przeglądarki 3D
def viewer_materials():
    src = open(os.path.join(HERE, "render_blender.py"), encoding="utf-8").read()
    i = src.index("M = {")
    j = src.index("\n}\n", i) + 2
    ns = {}
    exec(src[i:j], {}, ns)
    out = {}
    for k, d in ns["M"].items():
        if "c" in d:
            c = d["c"]
        elif "brick" in d:
            a, b = d["brick"]
            c = tuple((x + y) / 2 for x, y in zip(a, b))
        elif d.get("sedum"):
            c = (0.42, 0.47, 0.27)
        elif d.get("grass"):
            c = (0.42, 0.50, 0.30)
        else:
            c = (0.75, 0.75, 0.73)
        hx = "#" + "".join(f"{int(max(0, min(1, v)) * 255):02x}" for v in c)
        out[k] = [hx, round(d.get("r", 0.8), 2), round(d.get("metal", 0.0), 2)]
    out["szklo"] = ["#a9cfe0", 0.05, 0.1, 0.32]
    out["szklo_mebel"] = ["#a9cfe0", 0.05, 0.1, 0.4]
    out["woda"] = ["#29505c", 0.08, 0.1, 0.92]
    out["lampa"] = ["#fff4dc", 0.5, 0.0]
    return out


# ------------------------------------------------------------------ rzut-sygnet (mały plan bryły)
def keyplan(H, size=132):
    rooms0 = [r for r in H.all_rooms if r.level == min(H.L) and r.parent is None]
    base = unary_union([r.poly for r in rooms0 if r.kind not in ("ogrod",) and not r.outdoor])
    outdoor = unary_union([r.poly for r in rooms0 if r.outdoor]) if any(r.outdoor for r in rooms0) else None
    garden = unary_union([r.poly for r in H.rooms if r.kind == "ogrod"])
    upper = [r.poly for r in H.all_rooms if r.level > min(H.L) and r.kind not in ("void", "ogrod_void") and not r.outdoor]
    up = unary_union(upper) if upper else None
    allg = unary_union([g for g in (base, outdoor, garden, up) if g is not None and not g.is_empty])
    minx, miny, maxx, maxy = allg.bounds
    pad = 6
    s = (size - 2 * pad) / max(maxx - minx, maxy - miny)
    ox = pad + ((size - 2 * pad) - (maxx - minx) * s) / 2
    oy = pad + ((size - 2 * pad) - (maxy - miny) * s) / 2

    def path(g, cls):
        out = []
        for p in polygons(g):
            for ring in [p.exterior] + list(p.interiors):
                cs = list(ring.coords)
                out.append("M" + " L".join(f"{ox + (x - minx) * s:.1f},{oy + (y - miny) * s:.1f}" for x, y in cs) + "Z")
        return f'<path class="{cls}" d="{" ".join(out)}" fill-rule="evenodd"/>' if out else ""

    parts = []
    if outdoor is not None and not outdoor.is_empty:
        parts.append(path(outdoor, "kp-out"))
    parts.append(path(base, "kp-base"))
    if up is not None and not up.is_empty:
        parts.append(path(up, "kp-up"))
    parts.append(path(garden, "kp-gar"))
    return (f'<svg class="keyplan" viewBox="0 0 {size} {size}" role="img" aria-label="Sygnet planu: {E(H.name)}">'
            + "".join(parts) + "</svg>")


# ------------------------------------------------------------------ zdjęcia
def images(pid, dst):
    try:
        from PIL import Image
    except Exception:
        Image = None
    got = {}
    for v, cap in VIEWS:
        src = None
        for d in ("render", "podglad3d"):
            f = os.path.join(HERE, "out", pid, d, f"{v}.jpg")
            if os.path.exists(f):
                src = f
                break
        if src is None:
            continue
        big, small = os.path.join(dst, f"{v}.jpg"), os.path.join(dst, f"{v}_s.jpg")
        if Image is None:
            shutil.copy(src, big)
            shutil.copy(src, small)
        else:
            im = Image.open(src).convert("RGB")
            w, h = im.size
            if w > 1600:
                im = im.resize((1600, int(h * 1600 / w)), Image.LANCZOS)
            im.save(big, "JPEG", quality=82, optimize=True, progressive=True)
            sm = im.resize((720, int(im.size[1] * 720 / im.size[0])), Image.LANCZOS)
            sm.save(small, "JPEG", quality=80, optimize=True, progressive=True)
        got[v] = (f"{pid}/{v}.jpg", f"{pid}/{v}_s.jpg", cap, src.split(os.sep)[-2] == "render")
    return got


# ------------------------------------------------------------------ dane jednego domu
def project(pid):
    H = load(pid).build()
    dst = os.path.join(OUT, pid)
    os.makedirs(dst, exist_ok=True)
    sheets = []
    for idx in sorted(H.L):
        svg = plan_level(H, idx, f"{pid}l{idx}")
        fn = f"rzut_{idx}.svg"
        open(os.path.join(dst, fn), "w", encoding="utf-8").write(svg)
        sheets.append((f"{pid}/{fn}", H.levels[idx].name, svg))
    svg = plan_roof(H, f"{pid}d")
    open(os.path.join(dst, "dach.svg"), "w", encoding="utf-8").write(svg)
    sheets.append((f"{pid}/dach.svg", "Dach", svg))
    for i, (name, a, b) in enumerate(H.cuts):
        svg = section(H, name, a, b, f"{pid}s{i}")
        fn = f"przekroj_{i}.svg"
        open(os.path.join(dst, fn), "w", encoding="utf-8").write(svg)
        sheets.append((f"{pid}/{fn}", f"Przekrój {name}", svg))
    M = build_mesh(H)
    json.dump(export_json(M, H), open(os.path.join(dst, "model.json"), "w"), separators=(",", ":"))
    gardens = [r for r in H.rooms if r.kind == "ogrod"]
    g = gardens[0] if gardens else None
    top = max(H.levels[i].z + H.levels[i].h for i in H.L)
    nlev = len(H.L)
    rooms = []
    for idx, r, a in H.room_areas:
        rooms.append((H.levels[idx].name, r.name, a, r.kind))
    sezon = H.area["sezon"] > 0.5
    return dict(
        pid=pid, num=pid.upper(), name=H.name, tagline=H.tagline, concept=H.concept, notes=H.notes,
        area=H.area, rooms=rooms, sheets=sheets, keyplan=keyplan(H), imgs=images(pid, dst),
        roof=(g.roof_type if g else ""), roof_note=ROOF_NOTE.get(g.roof_type, "") if g else "",
        garden=GARDEN.get(g.style, g.style) if g else "", facade=FACADE.get(H.style.get("fasada"), H.style.get("fasada")),
        levels=nlev, top=top, sezon=sezon, bbox=H.bbox,
        size=(H.bbox[2] - H.bbox[0], H.bbox[3] - H.bbox[1]),
    )


# ------------------------------------------------------------------ HTML
def h_project(p):
    a = p["area"]
    stats = [("Powierzchnia użytkowa", f"{nice(a['uzytkowa'])} m²"), ("Ogród pod szkłem", f"{nice(a['ogrod'])} m²")]
    if a["sezon"] > 0.5:
        stats.append(("Patio sezonowe", f"{nice(a['sezon'])} m²"))
    if a["zewn"] > 0.5:
        stats.append(("Patio i tarasy", f"{nice(a['zewn'])} m²"))
    stats += [("Kondygnacje", str(p["levels"])), ("Wymiary", f"{nice(p['size'][0])} × {nice(p['size'][1])} m"),
              ("Dach ogrodu", ROOF_SHORT.get(p["roof"], p["roof"])), ("Ogród", p["garden"]), ("Elewacja", p["facade"])]
    st = "".join(f"<div><dt>{E(k)}</dt><dd>{E(v)}</dd></div>" for k, v in stats)
    imgs = p["imgs"]
    gal = ""
    order = [v for v, _ in VIEWS if v in imgs]
    if order:
        cells = []
        for k, v in enumerate(order):
            big, small, cap, final = imgs[v]
            sizes = "(min-width: 821px) 30vw, 100vw" if v == "ogrod" else "(min-width: 821px) 62vw, 100vw"
            cells.append(f'<figure class="shot shot-{v}{" shot-main" if k == 0 else ""}">'
                         f'<button type="button" class="shot-btn" data-full="{big}" data-cap="{E(p["name"])} · {E(cap)}" '
                         f'aria-label="Powiększ: {E(cap)}"><img src="{small}" srcset="{small} 720w, {big} 1600w" sizes="{sizes}" '
                         f'alt="{E(p["name"])}: {E(cap)}" loading="lazy" decoding="async"></button><figcaption>{E(cap)}</figcaption></figure>')
        gal = f'<div class="gallery">{"".join(cells)}</div>'
    tabs, panes = [], []
    for k, (url, label, svg) in enumerate(p["sheets"]):
        tid = f"{p['pid']}-t{k}"
        tabs.append(f'<button type="button" role="tab" id="{tid}" aria-selected="{"true" if k == 0 else "false"}" '
                    f'data-src="{url}" data-pane="{p["pid"]}-pane">{E(label)}</button>')
    first_svg = p["sheets"][0][2]
    concept = "".join(f"<li>{E(c)}</li>" for c in p["concept"])
    notes = p["notes"] or {}
    seasons = ""
    if notes.get("lato") or notes.get("zima"):
        seasons = (f'<div class="seasons"><div class="season season-lato"><h4>Lato</h4><p>{E(notes.get("lato", ""))}</p></div>'
                   f'<div class="season season-zima"><h4>Zima</h4><p>{E(notes.get("zima", ""))}</p></div></div>')
    tech = f'<p class="tech"><span>Technologia</span>{E(notes["technologia"])}</p>' if notes.get("technologia") else ""
    rows = "".join(f"<tr><td>{E(lv)}</td><td>{E(n)}</td><td class='num'>{nice(ar)} m²</td></tr>" for lv, n, ar, k in p["rooms"])
    return f'''
<section class="house" id="{p['pid']}" aria-labelledby="{p['pid']}-h">
  <header class="house-head">
    <div class="house-title">
      <p class="house-num">{p['num']}</p>
      <h2 id="{p['pid']}-h">{E(p['name'])}</h2>
      <p class="house-tag">{E(p['tagline'])}</p>
    </div>
    <div class="house-key">{p['keyplan']}</div>
  </header>
  {gal}
  <div class="house-body">
    <div class="house-text">
      <ul class="concept">{concept}</ul>
      {seasons}
      {tech}
      <div class="actions">
        <button type="button" class="btn btn-3d" data-model="{p['pid']}/model.json" data-name="{E(p['name'])}" data-top="{p['top']:.1f}">Obejrzyj model 3D</button>
      </div>
    </div>
    <dl class="stats">{st}</dl>
  </div>
  <div class="drawings">
    <div class="drw-bar">
      <div class="tabs" role="tablist" aria-label="Rysunki: {E(p['name'])}">{"".join(tabs)}</div>
      <label class="furn-toggle"><input type="checkbox" id="{p['pid']}-meble" checked> meble</label>
    </div>
    <div class="drw-pane" id="{p['pid']}-pane" role="tabpanel" aria-labelledby="{p['pid']}-t0">{first_svg}</div>
  </div>
  <details class="rooms"><summary>Zestawienie pomieszczeń</summary>
    <div class="table-wrap"><table><thead><tr><th>Poziom</th><th>Pomieszczenie</th><th class="num">Powierzchnia</th></tr></thead><tbody>{rows}</tbody></table></div>
  </details>
</section>'''


def h_card(p):
    imgs = p["imgs"]
    lato = imgs.get("lotu", (None, None))[1]
    zima = imgs.get("zmierzch", imgs.get("lotu", (None, None)))[1]
    img = (f'<span class="card-img"><img src="{lato}" data-lato="{lato}" data-zima="{zima}" alt="" loading="lazy" decoding="async"></span>'
           if lato else f'<span class="card-key">{p["keyplan"]}</span>')
    return (f'<li class="card"><a href="#{p["pid"]}">{img}<span class="card-num">{p["num"]}</span>'
            f'<span class="card-name">{E(p["name"])}</span>'
            f'<span class="card-meta">{nice(p["area"]["uzytkowa"], 0)} m² · ogród {nice(p["area"]["ogrod"], 0)} m² · dach {E(ROOF_SHORT.get(p["roof"], ""))}</span></a></li>')


def h_compare(ps):
    rows = []
    for p in ps:
        a = p["area"]
        patio = f"{nice(a['sezon'], 0)} m² sezonowe" if a["sezon"] > 0.5 else (f"{nice(a['zewn'], 0)} m²" if a["zewn"] > 0.5 else "–")
        rows.append(f"<tr><td><a href='#{p['pid']}'>{p['num']} · {E(p['name'])}</a></td>"
                    f"<td class='num' data-v='{a['uzytkowa']:.1f}'>{nice(a['uzytkowa'])}</td>"
                    f"<td class='num' data-v='{a['ogrod']:.1f}'>{nice(a['ogrod'])}</td>"
                    f"<td data-v='{a['sezon'] + a['zewn']:.1f}'>{patio}</td>"
                    f"<td class='num' data-v='{p['levels']}'>{p['levels']}</td>"
                    f"<td class='num' data-v='{p['top']:.1f}'>{nice(p['top'])}</td>"
                    f"<td>{E(ROOF_SHORT.get(p['roof'], p['roof']))}</td><td>{E(p['garden'])}</td><td>{E(p['facade'])}</td></tr>")
    return ("<div class='table-wrap'><table class='compare'><thead><tr>"
            "<th data-sort='t'>Dom</th><th data-sort='n' class='num'>Pow. użytkowa [m²]</th><th data-sort='n' class='num'>Ogród [m²]</th>"
            "<th data-sort='n'>Patio</th><th data-sort='n' class='num'>Kondygnacje</th><th data-sort='n' class='num'>Wysokość [m]</th>"
            "<th data-sort='t'>Dach ogrodu</th><th data-sort='t'>Styl ogrodu</th><th data-sort='t'>Elewacja</th>"
            f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>")


def h_refs():
    cats = {}
    for name, author, year, place, cat, lesson, url in REFS:
        cats.setdefault(cat, []).append((name, author, year, place, lesson, url))
    label = {"atrium": "Dom wokół dziedzińca", "sezonowe": "Ogrody zimowe i pokoje sezonowe", "dach szklany": "Otwierany dach",
             "szkło i wieża": "Szkło i wieża", "amfilada": "Amfilada i promenada", "polskie": "Polskie realizacje"}
    out = []
    for cat, items in cats.items():
        lis = "".join(f'<li><a href="{E(u)}" target="_blank" rel="noopener">{E(n)}</a> <span class="ref-meta">{E(a)}, {E(y)}, {E(pl)}</span><p>{E(ls)}</p></li>'
                      for n, a, y, pl, ls, u in items)
        out.append(f'<div class="ref-group"><h3>{E(label.get(cat, cat))}</h3><ul>{lis}</ul></div>')
    return "".join(out)


def h_facts():
    return "".join(f'<li><strong>{E(t)}.</strong> {E(x)} <a href="{E(u)}" target="_blank" rel="noopener">źródło</a></li>'
                   for t, x, u in DACH_FAKTY)


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    pids = []
    for f in sorted(glob.glob(os.path.join(HERE, "domy", "p[0-9][0-9]_*.py"))):
        pid = os.path.basename(f).split("_")[0]
        if pid != "p99":
            pids.append(pid)
    ps = []
    for pid in pids:
        try:
            ps.append(project(pid))
            print("OK", pid, ps[-1]["name"], f"{ps[-1]['area']['uzytkowa']:.0f} m²", sorted(ps[-1]["imgs"]))
        except Exception as e:  # dom w trakcie prac – pomijamy
            print("POMINIĘTO", pid, type(e).__name__, e)
    css = open(os.path.join(HERE, "silnik", "rysunki.css"), encoding="utf-8").read()
    tpl = open(os.path.join(HERE, "strona_szablon.html"), encoding="utf-8").read()
    hero = next((p for p in ps if p["pid"] == HERO), ps[0])
    hl = hero["imgs"].get("lotu", ("", "", "", False))[0]
    hz = hero["imgs"].get("zmierzch", hero["imgs"].get("lotu", ("", "", "", False)))[0]
    areas = [p["area"]["uzytkowa"] for p in ps]
    rep = {
        "{{DRAWING_CSS}}": css,
        "{{COUNT}}": str(len(ps)),
        "{{AREA_MIN}}": nice(min(areas), 0) if areas else "",
        "{{AREA_MAX}}": nice(max(areas), 0) if areas else "",
        "{{HERO_LATO}}": hl, "{{HERO_ZIMA}}": hz, "{{HERO_NAME}}": E(hero["name"]), "{{HERO_PID}}": hero["pid"],
        "{{HERO_NUM}}": hero["num"],
        "{{CARDS}}": "".join(h_card(p) for p in ps),
        "{{HOUSES}}": "".join(h_project(p) for p in ps),
        "{{COMPARE}}": h_compare(ps),
        "{{FACTS}}": h_facts(),
        "{{REFS}}": h_refs(),
        "{{MATS}}": json.dumps(viewer_materials(), separators=(",", ":")),
    }
    for k, v in rep.items():
        tpl = tpl.replace(k, v)
    open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(tpl)
    tot = 0
    n = 0
    for root, _, files in os.walk(OUT):
        for f in files:
            tot += os.path.getsize(os.path.join(root, f))
            n += 1
    print(f"strona: {n} plików, {tot / 1e6:.1f} MB")


HERO = os.environ.get("HERO", "p01")

if __name__ == "__main__":
    main()
