#!/usr/bin/env python3
"""Zabudowa wokół sofy narożnej z ukrytymi głośnikami tylnymi: trzy warianty i przekrój z głośnikami.

Regały po obu stronach sofy, nad sofą pawlacz łączący regały, na jego końcach wnęki z głośnikami
na uchwytach uchylnych: głośniki pochylone w dół na siedzących, schowane za maskownicą.

  /home/user/tools/bpyenv/bin/python projekty/sofa-glosniki/render.py                      # wszystkie widoki
  /home/user/tools/bpyenv/bin/python projekty/sofa-glosniki/render.py --widoki A --probki 16 --skala 0.5
Widoki: A (biel i dąb), B (lamele dębowe), C (grafit i orzech), X (przekrój: wariant A bez maskownic).
Wyniki: projekty/sofa-glosniki/out/*.jpg oraz punkty.json (położenie opisów na przekroju).
"""
import argparse
import json
import math
import os
import random
import sys
import time
from types import SimpleNamespace

TU = os.path.dirname(os.path.abspath(__file__))
OGRODY = os.path.join(os.path.dirname(TU), "ogrody-pod-szklem")
sys.path.insert(0, OGRODY)
sys.path.insert(0, TU)

import bpy  # noqa: E402
from bpy_extras.object_utils import world_to_camera_view  # noqa: E402
from mathutils import Vector  # noqa: E402

from film import meble3d as M3  # noqa: E402
from film import materialy, wyposazenie  # noqa: E402
from film.kontekst import Ctx  # noqa: E402
from film.meble3d import MB, R, T, lin, rgba  # noqa: E402
from film.scena import niebo  # noqa: E402
import wymiary as W  # noqa: E402

OUT = os.path.join(TU, "out")
F, BK = -W.GL / 2, W.GL / 2          # moduł zabudowy: lico frontów (−Y) i ściana (+Y)
YM = -W.GL / 2                       # położenie modułów w świecie (ściana w Y = 0, pokój w −Y)

BIEL = (0.86, 0.85, 0.82)
GRAFIT = (0.12, 0.12, 0.13)
WARIANTY = {
    "A": dict(nazwa="Biel i dąb", korpus=("lak", BIEL), polka=("drewno", "dab"), front=("lak", BIEL),
              tyl=("lak", BIEL), maskownica="perfo", gora="zamknieta", sofa=(0.62, 0.62, 0.60),
              poduszki=((0.72, 0.40, 0.26), (0.80, 0.63, 0.30), (0.86, 0.83, 0.75)), koc=(0.80, 0.63, 0.30),
              sciana="szalwia_jasna", dywan=((0.86, 0.83, 0.76), (0.66, 0.62, 0.55), "ramka"), stolik="dab",
              drewno="dab"),
    "B": dict(nazwa="Lamele dębowe", korpus=("drewno_z", "dab"), polka=("drewno", "dab"), front=("drewno_z", "dab"),
              tyl=("drewno_z", "dab"), maskownica="lamele", gora="lamele", sofa=(0.70, 0.63, 0.52),
              poduszki=((0.43, 0.48, 0.38), (0.88, 0.85, 0.78), (0.64, 0.36, 0.22)), koc=(0.43, 0.48, 0.38),
              sciana="szalwia", dywan=((0.84, 0.80, 0.71), (0.55, 0.52, 0.44), "melanz"), stolik="dab",
              drewno="dab"),
    "C": dict(nazwa="Grafit i orzech", korpus=("lak", GRAFIT), polka=("drewno", "orzech"), front=("lak", GRAFIT),
              tyl=("drewno_z", "orzech"), maskownica="tkanina", gora="otwarta", sofa=(0.13, 0.25, 0.20), welur=True,
              poduszki=((0.80, 0.60, 0.24), (0.64, 0.33, 0.21), (0.88, 0.85, 0.78)), koc=(0.64, 0.33, 0.21),
              sciana="greige", dywan=((0.78, 0.73, 0.64), (0.40, 0.36, 0.31), "pasy"), stolik="orzech",
              drewno="orzech", led_polki=True, galki=True),
}


# ------------------------------------------------------------------ materiały
def _rejestruj(ctx, key, m):
    """Własny materiał pod kluczem biblioteki meble3d (MB.mesh pobiera materiały przez mat(ctx, key))."""
    ctx.cache.setdefault("m3d_mat", {})[(key, bool(ctx.dusk))] = m
    return m


def _nowy(name):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    return m, nt, nt.nodes["Principled BSDF"]


def m_led(name, sila=10.0, temp=3000.0):
    m, nt, b = _nowy(name)
    b.inputs["Base Color"].default_value = (0.9, 0.9, 0.9, 1.0)
    bb = nt.nodes.new("ShaderNodeBlackbody")
    bb.inputs["Temperature"].default_value = temp
    nt.links.new(bb.outputs[0], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = sila
    return m


def m_perfo(name, col, plaszczyzna, raster=0.005, otwor=0.0015):
    """Płyta perforowana lakierowana jak fronty: otwory 3 mm co 5 mm (ok. 28% otwarcia – przepuszcza dźwięk)."""
    m, nt, b = _nowy(name)
    N, L = nt.nodes, nt.links
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])
    cb = N.new("ShaderNodeCombineXYZ")
    a, c = ("X", "Z") if plaszczyzna == "xz" else ("X", "Y")
    L.new(sep.outputs[a], cb.inputs["X"])
    L.new(sep.outputs[c], cb.inputs["Y"])
    sc = N.new("ShaderNodeVectorMath")
    sc.operation = "SCALE"
    sc.inputs[3].default_value = 1.0 / raster
    L.new(cb.outputs[0], sc.inputs[0])
    fr = N.new("ShaderNodeVectorMath")
    fr.operation = "FRACTION"
    L.new(sc.outputs[0], fr.inputs[0])
    sb = N.new("ShaderNodeVectorMath")
    sb.operation = "SUBTRACT"
    sb.inputs[1].default_value = (0.5, 0.5, 0.0)
    L.new(fr.outputs[0], sb.inputs[0])
    ln = N.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    L.new(sb.outputs[0], ln.inputs[0])
    lt = N.new("ShaderNodeMath")
    lt.operation = "LESS_THAN"
    lt.inputs[1].default_value = otwor / raster
    L.new(ln.outputs["Value"], lt.inputs[0])
    mx = N.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    mx.inputs[6].default_value = rgba(col)
    mx.inputs[7].default_value = rgba((0.56, 0.56, 0.54))     # za otworami biała tkanina akustyczna
    L.new(lt.outputs[0], mx.inputs["Factor"])
    L.new(mx.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.42
    return m


def m_stozek(name, col=(1.0, 0.52, 0.12), k=0.28):
    """Wiązka dźwięku na przekroju: półprzezroczysta, świecąca, bez cieni."""
    m, nt, b = _nowy(name)
    N, L = nt.nodes, nt.links
    out = N["Material Output"]
    tr = N.new("ShaderNodeBsdfTransparent")
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = rgba(col)
    em.inputs["Strength"].default_value = 1.6
    mx = N.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = k
    L.new(tr.outputs[0], mx.inputs[1])
    L.new(em.outputs[0], mx.inputs[2])
    L.new(mx.outputs[0], out.inputs["Surface"])
    return m


def _m_z_opisu(ctx, name, spec, axis="X"):
    kind, v = spec
    if kind == "lak":
        return M3._mk_plain(name, v, rough=0.4, coat=0.1, coat_r=0.3)
    light, dark = M3.DREWNO[v]
    return M3._mk_wood(name, light, dark, "Z" if kind == "drewno_z" else axis, rough=0.5)


def materialy_wariantu(ctx, V):
    reg = lambda k, m: _rejestruj(ctx, k, m)  # noqa: E731
    reg("k_korpus", _m_z_opisu(ctx, "korpus", V["korpus"]))
    reg("k_polka", _m_z_opisu(ctx, "polka", V["polka"]))
    reg("k_front", _m_z_opisu(ctx, "front", V["front"]))
    reg("k_tyl", _m_z_opisu(ctx, "tyl", V["tyl"]))
    light, dark = M3.DREWNO["dab"]
    reg("k_lamela", M3._mk_wood("lamela", light, dark, "Z", rough=0.5))
    reg("k_cokol", M3._mk_plain("cokol_z", (0.06, 0.06, 0.06), rough=0.6))
    fr = V["front"][1] if V["front"][0] == "lak" else BIEL
    reg("k_perfo_xz", m_perfo("perfo_front", fr, "xz"))
    reg("k_perfo_xy", m_perfo("perfo_spod", fr, "xy"))
    reg("k_tkanina", M3._mk_fabric("tkanina_akustyczna", (0.035, 0.035, 0.037), rough=0.95, sheen=0.15,
                                   weave=260.0, bump=0.2, mel=0.02))
    reg("k_filc", M3._mk_fabric("filc_czarny", (0.03, 0.03, 0.03), rough=0.98, sheen=0.05, weave=300.0, bump=0.1))
    reg("k_wata", M3._mk_fabric("wata", (0.78, 0.70, 0.50), rough=1.0, sheen=0.1, weave=40.0, bump=0.8, mel=0.1))
    reg("k_led", m_led("led", 9.0))
    reg("k_profil", M3._mk_plain("profil_alu", (0.78, 0.78, 0.79), rough=0.3, metal=1.0))
    reg("k_glosnik", M3._mk_plain("glosnik", (0.03, 0.03, 0.032), rough=0.35, coat=0.2, coat_r=0.2))
    reg("k_membrana", M3._mk_plain("membrana", (0.09, 0.09, 0.09), rough=0.75))
    reg("k_guma", M3._mk_plain("guma_g", (0.02, 0.02, 0.02), rough=0.6))
    reg("k_kopulka", M3._mk_fabric("kopulka", (0.05, 0.05, 0.05), rough=0.6, sheen=0.3, weave=500.0, bump=0.05))
    reg("k_uchwyt", M3._mk_plain("uchwyt_glosnika", (0.08, 0.08, 0.085), rough=0.4, metal=0.8))
    reg("k_stozek", m_stozek("wiazka"))
    reg("k_noga", M3._mk_plain("noga", (0.03, 0.03, 0.03), rough=0.45))
    reg("k_mosiadz", M3.mat(ctx, "mosiadz"))
    welur = V.get("welur")
    reg("k_sofa", M3._mk_fabric("sofa", V["sofa"], sheen=0.45 if welur else 0.4, weave=300.0 if welur else 120.0,
                                bump=0.1 if welur else 0.3, mel=0.02 if welur else 0.04))
    for i, c in enumerate(V["poduszki"]):
        reg(f"k_pod{i}", M3._mk_fabric(f"poduszka{i}", c, sheen=0.45))
    reg("k_koc", M3._mk_fabric("koc", V["koc"], weave=24.0, bump=0.55, sheen=0.3, mel=0.05))
    light, dark = M3.DREWNO[V["stolik"]]
    reg("k_stolik", M3._mk_wood("stolik", light, dark, "X", rough=0.45))
    reg("kamionka", M3._mk_plain("kamionka", (0.80, 0.77, 0.70), rough=0.55, bump=0.05))
    c1, c2, wz = V["dywan"]
    reg("k_dywan", M3._mk_rug("dywan", c1, c2, wz, 3.0, 2.0))


# ------------------------------------------------------------------ scena: pokój
def plyta(name, x0, y0, z0, x1, y1, z1, m, col):
    me = bpy.data.meshes.new(name)
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(v, [], f)
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    return ob


def pokoj(ctx, V, col):
    """Salon 6 × 6 m, ściana z zabudową w Y = 0, okno od podłogi w lewej ścianie."""
    H = W.SUFIT
    sc_m = materialy.material("farba_" + V["sciana"], ctx)
    bok_m = materialy.material("farba_cieply_bialy", ctx)
    plyta("podloga", -3.0, -6.0, -0.02, 3.0, 0.0, 0.0, materialy.material("podloga_drewno", ctx), col)
    plyta("sufit", -3.0, -6.0, H, 3.0, 0.0, H + 0.02, materialy.material("strop", ctx), col)
    plyta("sciana_sofy", -3.0, 0.0, 0.0, 3.0, 0.15, H, sc_m, col)
    plyta("sciana_prawa", 3.0, -6.0, 0.0, 3.15, 0.0, H, bok_m, col)
    plyta("sciana_przod", -3.0, -6.15, 0.0, 3.0, -6.0, H, bok_m, col)
    y0, y1, zo = -4.2, -1.2, 2.45                     # okno w lewej ścianie
    plyta("sciana_lewa_1", -3.15, -6.0, 0.0, -3.0, y0, H, bok_m, col)
    plyta("sciana_lewa_2", -3.15, y1, 0.0, -3.0, 0.0, H, bok_m, col)
    plyta("nadproze", -3.15, y0, zo, -3.0, y1, H, bok_m, col)
    mb = MB()
    for a, b in ((y0, y0 + 0.05), (y1 - 0.05, y1), ((y0 + y1) / 2 - 0.025, (y0 + y1) / 2 + 0.025)):
        mb.box(-3.12, a, 0.0, -3.05, b, zo, "czarny_metal", r=0.002)
    mb.box(-3.12, y0, zo - 0.05, -3.05, y1, zo, "czarny_metal", r=0.002)
    mb.box(-3.12, y0, 0.0, -3.05, y1, 0.04, "czarny_metal", r=0.002)
    mb.box(-3.09, y0, 0.04, -3.085, y1, zo - 0.05, "szklo_cienkie", r=0)
    ctx.link(bpy.data.objects.new("okno", mb.mesh(ctx, "okno")))
    plyta("trawnik", -80.0, -80.0, -0.08, -3.15, 80.0, -0.06, materialy.material("trawa_ogrod", ctx), col)
    # obraz na prawej ścianie i listwy przypodłogowe
    mb = MB()
    mb.box(2.975, -3.6, 1.05, 3.0, -2.4, 1.85, "drewno", r=0.003)
    mb.box(2.972, -3.56, 1.09, 2.976, -2.44, 1.81, "obraz:3", r=0)
    for x0, y0_, x1, y1_ in ((-3.0, -0.012, 3.0, 0.0), (2.988, -6.0, 3.0, 0.0), (-3.0, -6.0, -2.988, y0),
                             (-3.0, y1, -2.988, 0.0)):
        mb.box(x0, y0_, 0.0, x1, y1_, 0.07, "lak_bialy", r=0.002)
    ctx.link(bpy.data.objects.new("dodatki", mb.mesh(ctx, "dodatki")))


def swiatla(sc, col, V):
    so = niebo(sc, "dzien", az=244.0, el=27.0, strength=0.45)
    so.data.energy = 3.0
    li = bpy.data.lights.new("doswietlenie", "AREA")
    li.shape = "RECTANGLE"
    li.size, li.size_y = 4.0, 2.4
    li.energy = 260.0
    li.use_temperature = True
    li.temperature = 5200.0
    ob = bpy.data.objects.new("doswietlenie", li)
    ob.location = (0.0, -4.4, W.SUFIT - 0.05)
    ob.visible_camera = False
    col.objects.link(ob)


def led_swiatlo(col, name, x0, x1, y, z, energy, temp=3000.0):
    """Taśma LED: źródło prostokątne świecące w dół (spód półki / pawlacza)."""
    li = bpy.data.lights.new(name, "AREA")
    li.shape = "RECTANGLE"
    li.size, li.size_y = x1 - x0, 0.012
    li.energy = energy
    li.use_temperature = True
    li.temperature = temp
    ob = bpy.data.objects.new(name, li)
    ob.location = ((x0 + x1) / 2, y, z)
    ob.visible_camera = False
    col.objects.link(ob)


# ------------------------------------------------------------------ zabudowa
def lamele(mb, x0, x1, z0, z1, y0, y1, krok=0.045, sz=0.03, wzdluz=False):
    """Lamele dębowe 30 × 20 mm co 45 mm (prześwit 15 mm) na jednej siatce dla całej zabudowy:
    środek lameli w x = k · krok, więc rytm nie urywa się na styku regału i pawlacza.
    wzdluz=True – lamele pod spodem pawlacza, biegnące od frontu do ściany (y0..y1, z0..z1)."""
    for k in range(math.ceil((x0 + sz / 2) / krok), math.floor((x1 - sz / 2) / krok) + 1):
        x = k * krok - sz / 2
        mb.box(x, y0, z0, x + sz, y1, z1, "k_lamela", r=0.0015, seg=1)


def ksiazki_i_dekoracje(kmb, rnd, xa, xb, z0, z1, rodzaj):
    hc = z1 - z0
    d = W.GL - 0.04
    if rodzaj == "ksiazki":
        M3._fill_books(kmb, rnd, xa + 0.004, xb - 0.004, z0, hc, d, fill=0.8)
    elif rodzaj == "pol":
        M3._fill_books(kmb, rnd, xa + 0.004, (xa + xb) / 2 + 0.04, z0, hc, d, fill=1.0)
        M3._vase(kmb, xb - 0.12, -0.02, z0, min(hc - 0.05, 0.22), 0.06, "kamionka", kind=rnd.choice((0, 1)))
    else:                                      # dekoracje: stos albumów, wazon, roślinka
        h = M3._book_stack(kmb, rnd, xa + 0.17, -0.02, z0, n=3, big=True)
        if hc - h > 0.14:
            M3._bowl(kmb, xa + 0.17, -0.02, z0 + h, 0.07, 0.04, "kamionka")
        M3._plant_small(kmb, rnd, xb - 0.11, -0.03, z0, r=0.065, h=0.11)


def regal(mb, kmb, rnd, x0, x1, V, strona, zawartosc):
    p = W.PLYTA
    xa, xb = x0 + p, x1 - p
    mb.box(x0, F, 0.0, xa, BK, W.SUFIT, "k_korpus", r=0.0015)
    mb.box(xb, F, 0.0, x1, BK, W.SUFIT, "k_korpus", r=0.0015)
    mb.box(xa, BK - 0.012, 0.0, xb, BK, W.SUFIT, "k_tyl", r=0)
    mb.box(xa, F + 0.05, 0.0, xb, BK - 0.012, W.COKOL, "k_cokol", r=0)
    mb.box(xa, F + W.FRONT, W.COKOL, xb, BK - 0.012, W.COKOL + p, "k_korpus", r=0)
    mb.box(xa, F + W.FRONT, W.SUFIT - p, xb, BK - 0.012, W.SUFIT, "k_korpus", r=0)
    # szafka dolna
    if V["maskownica"] == "lamele":
        mb.box(x0, F - 0.003, W.COKOL, x1, F, W.SZAFKA_Z, "k_filc", r=0)
        lamele(mb, x0, x1, W.COKOL, W.SZAFKA_Z, F - 0.023, F - 0.003)
    else:
        mb.box(xa + 0.0015, F, W.COKOL + 0.002, xb - 0.0015, F + W.FRONT, W.SZAFKA_Z - 0.002, "k_front", r=0.0015)
        if V.get("galki"):
            mb.xf(mb.cyl(0, 0, 0.0, 0.022, 0.011, "k_mosiadz", n=20, r=0.002),
                  T(xa + 0.05 if strona > 0 else xb - 0.05, F, W.SZAFKA_Z - 0.07) @ R("X", 90))
    # półki
    otwarta = V["gora"] == "otwarta"
    polki = [W.SZAFKA_Z] + list(W.POLKI) + [W.MOST_Z] + ([W.POLKA_GORNA] if otwarta else [])
    for z in polki:
        mb.box(xa, F + 0.004, z, xb, BK - 0.012, z + 0.025, "k_polka", r=0.0015)
        if V.get("led_polki") and z > W.SZAFKA_Z:
            mb.box(xa + 0.01, F + 0.014, z - 0.004, xb - 0.01, F + 0.024, z, "k_led", r=0)
    gora = (polki + [W.SUFIT - p])
    for i, z in enumerate(polki):
        if not otwarta and z >= W.MOST_Z:
            break
        ksiazki_i_dekoracje(kmb, rnd, xa, xb, z + 0.025, gora[i + 1], zawartosc[i % len(zawartosc)])
    # strefa górna
    if V["gora"] == "zamknieta":
        mb.box(xa + 0.0015, F, W.MOST_Z + 0.002, xb - 0.0015, F + W.FRONT, W.SUFIT - 0.002, "k_front", r=0.0015)
    elif V["gora"] == "lamele":
        mb.box(x0, F - 0.003, W.MOST_Z - 0.02, x1, F, W.SUFIT, "k_filc", r=0)   # lamele: w pawlacz()


def pawlacz(mb, kmb, rnd, V, col):
    """Pawlacz nad sofą między regałami; na końcach wnęki z głośnikami.
    Zwraca siatkę maskownic osobno (na przekroju są zdjęte)."""
    p = W.PLYTA
    x0, x1 = -W.X_REG, W.X_REG
    z0, z1 = W.MOST_Z, W.SUFIT
    yF = F + W.FRONT
    msk = MB()
    mb.box(x0, yF, z1 - p, x1, BK, z1, "k_korpus", r=0)                         # wieniec
    mb.box(x0, BK - 0.012, z0, x1, BK, z1 - p, "k_tyl", r=0)                    # plecy
    for s in (-1, 1):                                                           # przegrody wnęk
        mb.box(s * W.X_WNEKA - p / 2, yF, z0 + p, s * W.X_WNEKA + p / 2, BK - 0.012, z1 - p, "k_korpus", r=0)
    m = V["maskownica"]
    if m == "tkanina":                                                          # środek: otwarta nisza
        mb.box(-W.X_WNEKA, F + 0.004, z0, W.X_WNEKA, BK - 0.012, z0 + 0.025, "k_polka", r=0.0015)
        mb.box(-W.X_WNEKA + p / 2, F + 0.014, z1 - p - 0.004, W.X_WNEKA - p / 2, F + 0.024, z1 - p, "k_led", r=0)
        led_swiatlo(col, "led_nisza", -W.X_WNEKA + 0.05, W.X_WNEKA - 0.05, YM + F + 0.02, z1 - p - 0.006, 9.0)
        zn = z0 + 0.025
        h = M3._book_stack(kmb, rnd, -0.62, -0.03, zn, n=4, big=True)
        M3._vase(kmb, -0.62, -0.03, zn + h, 0.20, 0.055, "kamionka", kind=1)
        M3._vase(kmb, 0.05, -0.02, zn, 0.36, 0.09, "kamionka", kind=0)
        M3._stems(kmb, 0.05, -0.02, zn + 0.3, 0.32, 7, rnd)
        kmb.sphere(0.32, -0.02, zn + 0.07, 0.07, "braz", n=20)
        M3._fill_books(kmb, rnd, 0.52, 0.95, zn, z1 - p - zn - 0.01, W.GL - 0.04, fill=1.0)
    else:
        mb.box(-W.X_WNEKA, yF, z0, W.X_WNEKA, BK - 0.012, z0 + p, "k_korpus", r=0)   # dno środka
    if m == "perfo":
        for a, b in ((-W.X_WNEKA + 0.0015, -0.0015), (0.0015, W.X_WNEKA - 0.0015)):
            mb.box(a, F, z0, b, F + W.FRONT, z1 - 0.002, "k_front", r=0.0015)
        for s in (-1, 1):
            a, b = sorted((s * (W.X_WNEKA + 0.0015), s * (W.X_REG - 0.0015)))
            msk.box(a, F, z0, b, F + W.FRONT, z1 - 0.002, "k_perfo_xz", r=0.0015)
            msk.box(a, yF, z0, b, BK - 0.012, z0 + p, "k_perfo_xy", r=0)
    elif m == "tkanina":
        for s in (-1, 1):
            a, b = sorted((s * (W.X_WNEKA + 0.0015), s * (W.X_REG - 0.0015)))
            msk.box(a, F, z0, b, F + W.FRONT, z1 - 0.002, "k_tkanina", r=0.002)
            msk.box(a, yF, z0, b, BK - 0.012, z0 + p, "k_tkanina", r=0)
    elif m == "lamele":
        # czarna tkanina za lamelami, lamele na froncie (przez całą szerokość) i pod spodem (w głąb)
        # pas lameli przez całą zabudowę (regały i pawlacz), pod spodem lamele w głąb, za nimi czarna tkanina
        msk.box(x0, F - 0.003, z0 - 0.02, x1, F, z1, "k_filc", r=0)
        msk.box(x0, F, z0 - 0.003, x1, BK - 0.012, z0, "k_filc", r=0)
        lamele(msk, -W.X_ZEW, W.X_ZEW, z0 - 0.02, z1, F - 0.023, F - 0.003)
        lamele(msk, x0, x1, z0 - 0.02, z0 - 0.003, F - 0.003, BK - 0.06)
    # wata akustyczna w wnękach (plecy i wieniec)
    for s in (-1, 1):
        a, b = sorted((s * (W.X_WNEKA + p / 2), s * (W.X_REG - 0.001)))
        mb.box(a, BK - 0.042, z0 + p + 0.02, b, BK - 0.012, z1 - p, "k_wata", r=0.004)
        mb.box(a, yF + 0.04, z1 - p - 0.03, b, BK - 0.042, z1 - p, "k_wata", r=0.004)
    # LED podświetlający ścianę za sofą (przy plecach, pod pawlaczem)
    zl = z0 - (0.003 if m == "lamele" else 0.0)        # przy lamelach: LED w szczelinie za lamelami
    mb.box(x0 + 0.02, BK - 0.05, zl - 0.012, x1 - 0.02, BK - 0.02, zl, "k_profil", r=0.001)
    mb.box(x0 + 0.022, BK - 0.047, zl - 0.0125, x1 - 0.022, BK - 0.023, zl - 0.011, "k_led", r=0)
    led_swiatlo(col, "led_sciana", x0 + 0.05, x1 - 0.05, YM + BK - 0.035, zl - 0.016, 34.0)
    return msk


def glosnik_mb():
    """Monitor półkowy: obudowa, głośnik nisko-średniotonowy, kopułka wysokotonowa (front −Y)."""
    w, h, d = W.GLOSNIK
    mb = MB()
    mb.box(-w / 2, -h / 2, -d, w / 2, h / 2, 0.0, "k_glosnik", r=0.008, seg=3)   # w układzie przegrody: front z = 0
    yw = -h / 2 + 0.085
    mb.torus(0, yw, 0.0, 0.055, 0.006, "k_guma", nu=40, nv=8)
    mb.lathe([(0.049, 0.001), (0.026, -0.022), (0.0, -0.022)], "k_membrana", n=40, x=0, y=yw)
    mb.sphere(0, yw, -0.016, 0.022, "k_membrana", n=20, sz=0.5)
    mb.torus(0, h / 2 - 0.05, 0.0, 0.021, 0.004, "k_glosnik", nu=32, nv=6)
    mb.sphere(0, h / 2 - 0.05, 0.0, 0.014, "k_kopulka", n=16, sz=0.55)
    mb.xf(list(mb.bm.faces), R("X", 90) @ T(0, 0, d / 2))     # oś przegrody → −Y, środek obudowy w (0,0,0)
    return mb


def glosniki(ctx, col):
    """Dwa głośniki tylne na uchwytach uchylnych; zwraca ich macierze (do wiązek i opisów)."""
    w, h, d = W.GLOSNIK
    me = glosnik_mb().mesh(ctx, "glosnik")
    out = []
    mb = MB()
    for s in (-1, 1):
        Mg = T(s * W.G_X, -W.G_Y, W.G_Z) @ R("Z", -s * W.ZBIEZNOSC) @ R("X", W.POCHYLENIE)
        ob = bpy.data.objects.new(f"glosnik_{'L' if s < 0 else 'P'}", me)
        ob.matrix_world = Mg
        ctx.link(ob)
        out.append(Mg)
        tyl = Mg @ Vector((0.0, d / 2, 0.0))
        kotwa = Vector((tyl.x, -0.048, tyl.z))              # płytka uchwytu na wacie przy plecach wnęki
        mb.box(kotwa.x - 0.04, kotwa.y - 0.004, kotwa.z - 0.06, kotwa.x + 0.04, kotwa.y + 0.004, kotwa.z + 0.06,
               "k_uchwyt", r=0.002)
        mb.tube([tuple(kotwa), tuple(tyl)], 0.009, "k_uchwyt", n=12)
        mb.sphere(tyl.x, tyl.y, tyl.z, 0.016, "k_uchwyt", n=12)
    ctx.link(bpy.data.objects.new("uchwyty", mb.mesh(ctx, "uchwyty")))
    return out


def wiazki(ctx, Ms, kat=20.0, n=48):
    """Wiązki dźwięku (stożki) od głośników do wysokości uszu siedzących – tylko na przekroju."""
    d = W.GLOSNIK[2]
    me = bpy.data.meshes.new("wiazki")
    v, f = [], []
    for Mg in Ms:
        a = Mg @ Vector((0.0, -d / 2, 0.0))
        osz = (Mg.to_3x3() @ Vector((0.0, -1.0, 0.0))).normalized()
        L = (a.z - W.CEL_Z) / max(0.2, -osz.z)
        u = osz.orthogonal().normalized()
        w = osz.cross(u)
        r = L * math.tan(math.radians(kat))
        i0 = len(v)
        v.append(tuple(a))
        for k in range(n):
            t = 2 * math.pi * k / n
            v.append(tuple(a + osz * L + (u * math.cos(t) + w * math.sin(t)) * r))
        for k in range(n):
            f.append((i0, i0 + 1 + k, i0 + 1 + (k + 1) % n))
    me.from_pydata(v, [], f)
    me.materials.append(M3.mat(ctx, "k_stozek"))
    ob = bpy.data.objects.new("wiazki", me)
    for attr in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission"):
        setattr(ob, attr, False)
    ctx.link(ob)
    # oś: cienka linia od głośnika do punktu celowania
    mb = MB()
    for Mg in Ms:
        a = Mg @ Vector((0.0, -d / 2, 0.0))
        osz = (Mg.to_3x3() @ Vector((0.0, -1.0, 0.0))).normalized()
        L = (a.z - W.CEL_Z) / max(0.2, -osz.z)
        mb.tube([tuple(a), tuple(a + osz * L)], 0.004, "k_stozek", n=8)
        mb.sphere(*(a + osz * L), 0.025, "k_stozek", n=12)
    o2 = bpy.data.objects.new("osie", mb.mesh(ctx, "osie"))
    for attr in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission"):
        setattr(o2, attr, False)
    ctx.link(o2)


# ------------------------------------------------------------------ sofa, stolik, dywan
def sofa(ctx, rnd):
    mb = MB()
    x0, x1 = -W.SOFA_W / 2, W.SOFA_W / 2
    yb, yf = -W.SOFA_OD_SCIANY, -(W.SOFA_OD_SCIANY + W.SOFA_D)
    xs, ys = x1 - W.SZEZL_W, -W.SZEZL_D
    aw, fab = 0.17, "k_sofa"
    for x, y in ((x0 + 0.1, yb - 0.1), (x0 + 0.1, yf + 0.1), (x1 - 0.1, yb - 0.1), (x1 - 0.1, ys + 0.1),
                 (xs + 0.1, ys + 0.1), (0.0, yb - 0.1), (0.0, yf + 0.1)):
        mb.cyl(x, y, 0.0, 0.03, 0.02, "k_noga", n=12)                         # stopki (sofa nisko, na cokole)
    mb.box(x0 + 0.06, yf + 0.06, 0.02, x1 - 0.06, yb - 0.06, 0.1, "k_noga", r=0.004)
    mb.box(xs + 0.06, ys + 0.06, 0.02, x1 - 0.06, yf, 0.1, "k_noga", r=0.004)
    mb.box(x0 + aw, yf, 0.05, x1 - aw, yb, 0.30, fab, r=0.02, seg=3)
    mb.box(xs, ys, 0.05, x1 - aw, yf, 0.30, fab, r=0.02, seg=3)
    mb.box(x0, yf, 0.05, x0 + aw, yb, 0.62, fab, r=0.03, seg=3)              # boki
    mb.box(x1 - aw, ys, 0.05, x1, yb, 0.62, fab, r=0.03, seg=3)
    mb.box(x0 + aw, yb - 0.16, 0.30, x1 - aw, yb, 0.66, fab, r=0.03, seg=3)  # oparcie
    cw = (xs - x0 - aw) / 2
    yc = (yf + yb - 0.16) / 2
    for k in range(2):
        mb.soft(cw / 2 - 0.008, (yb - 0.16 - yf) / 2 - 0.01, 0.075, fab, M=T(x0 + aw + (k + 0.5) * cw, yc, 0.375),
                e1=0.18, e2=0.08, nu=28, nv=10, puff=0.01, wr=0.004, seed=k)
    sw = x1 - aw - xs
    mb.soft(sw / 2 - 0.008, (yb - 0.16 - ys) / 2 - 0.01, 0.075, fab, M=T(xs + sw / 2, (ys + yb - 0.16) / 2, 0.375),
            e1=0.18, e2=0.08, nu=28, nv=16, puff=0.01, wr=0.004, seed=3)
    bw = (x1 - x0 - 2 * aw) / 3
    for k in range(3):
        mb.soft(bw / 2 - 0.02, 0.09, 0.2, fab, M=T(x0 + aw + (k + 0.5) * bw, yb - 0.22, 0.68) @ R("X", -10),
                e1=0.25, e2=0.12, nu=28, nv=10, puff=0.012, wr=0.004, seed=k + 5)
    for k, (px, key) in enumerate(((-1.02, "k_pod0"), (-0.66, "k_pod1"), (0.74, "k_pod2"), (1.04, "k_pod0"))):
        mb.pillow(0.45, 0.45, 0.14, key, T(px, yb - 0.36, 0.66) @ R("Z", rnd.uniform(-8, 8)) @ R("X", 70.0), seed=k * 3)
    mb.soft(0.30, 0.21, 0.03, "k_koc", M=T(xs + sw / 2, ys + 0.42, 0.47) @ R("Z", 6), e1=0.2, e2=0.1, nu=20, nv=8,
            wr=0.006, seed=9)
    ctx.link(bpy.data.objects.new("sofa", mb.mesh(ctx, "sofa")))


def stolik_i_dywan(ctx, rnd):
    mb = MB()
    mb.rbox(-1.5, -1.0, 0.0, 1.5, 1.0, 0.012, "k_dywan", rc=0.03, r=0.004)
    ob = bpy.data.objects.new("dywan", mb.mesh(ctx, "dywan"))
    ob.location = (-0.2, -1.62, 0.0)
    ctx.link(ob)
    mb = MB()
    x0, x1, y0, y1, h = -1.0, 0.1, -2.05, -1.45, 0.38
    mb.box(x0, y0, h - 0.04, x1, y1, h, "k_stolik", r=0.004)
    for x in (x0 + 0.05, x1 - 0.07):
        mb.box(x, y0 + 0.05, 0.012, x + 0.02, y1 - 0.05, 0.03, "k_noga", r=0.003)
        mb.box(x, (y0 + y1) / 2 - 0.01, 0.03, x + 0.02, (y0 + y1) / 2 + 0.01, h - 0.04, "k_noga", r=0.003)
    hs = M3._book_stack(mb, rnd, -0.72, -1.74, h, n=3, big=True)
    M3._bowl(mb, -0.72, -1.74, h + hs, 0.06, 0.035, "kamionka")
    M3._vase(mb, -0.12, -1.66, h, 0.24, 0.06, "kamionka", kind=0)
    M3._stems(mb, -0.12, -1.66, h + 0.2, 0.3, 6, rnd)
    M3._bowl(mb, -0.38, -1.86, h, 0.12, 0.05, "kamionka")
    ctx.link(bpy.data.objects.new("stolik", mb.mesh(ctx, "stolik")))


def rosliny_i_lampa(ctx):
    pok = SimpleNamespace(kind="salon", top=W.SUFIT)
    it = SimpleNamespace(kind="roslina", cx=2.55, cy=0.45, z=0.0, rot=0.0, w=0.6, d=0.6, room=pok)
    M3._plant_model(M3._B(it, ctx, 0), 0, 0, 0, 1.55, yaw=30.0)
    it = SimpleNamespace(kind="lampa", cx=-2.5, cy=0.4, z=0.0, rot=0.0, w=0.4, d=0.4, room=pok)
    wyposazenie._lampa(M3._B(it, ctx, 0))


# ------------------------------------------------------------------ ujęcia i render
def kamera(sc, loc, cel, lens):
    cam = bpy.data.cameras.new("kamera")
    cam.lens = lens
    cam.sensor_width = 36
    co = bpy.data.objects.new("kamera", cam)
    sc.collection.objects.link(co)
    co.location = loc
    co.rotation_euler = (Vector(cel) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    return co


def render(sc, fn, probki, res, ekspozycja=0.0):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = probki
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.03
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 8
    sc.cycles.diffuse_bounces = 4
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 6
    sc.cycles.transparent_max_bounces = 16
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.cycles.blur_glossy = 1.0
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    sc.view_settings.exposure = ekspozycja
    sc.view_settings.use_white_balance = True             # dzień: ciepłe LED i słońce bez pomarańczowego nalotu
    sc.view_settings.white_balance_temperature = 5600.0
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 92
    sc.render.filepath = fn
    t = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"RENDER {os.path.basename(fn)}: {time.time() - t:.0f} s")


UJECIA = {
    "A": dict(loc=(-0.45, -4.8, 1.2), cel=(0.05, 0.0, 1.42), lens=27.0),
    "B": dict(loc=(-0.45, -4.8, 1.2), cel=(0.05, 0.0, 1.42), lens=27.0),
    "C": dict(loc=(-0.45, -4.8, 1.2), cel=(0.05, 0.0, 1.42), lens=27.0),
    "X": dict(loc=(2.55, -2.75, 1.62), cel=(0.55, -0.25, 1.72), lens=22.0),
}


def scena(widok):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    col = sc.collection
    wk = "A" if widok == "X" else widok
    V = WARIANTY[wk]
    styl = dict(drewno=V["drewno"], metal="mosiadz" if V.get("galki") else "czarny_metal")
    ctx = Ctx(col=col, seed=7, dusk=False, house=SimpleNamespace(styl_wnetrz=styl))
    materialy_wariantu(ctx, V)
    pokoj(ctx, V, col)
    swiatla(sc, col, V)
    rnd = random.Random(f"zabudowa:{wk}")
    mb, kmb = MB(), MB()
    zaw_l = ["ksiazki", "dekor", "ksiazki", "pol", "ksiazki"]
    zaw_p = ["pol", "ksiazki", "dekor", "ksiazki", "ksiazki"]
    regal(mb, kmb, rnd, -W.X_ZEW, -W.X_REG, V, -1, zaw_l)
    regal(mb, kmb, rnd, W.X_REG, W.X_ZEW, V, 1, zaw_p)
    msk = pawlacz(mb, kmb, rnd, V, col)
    for name, m in (("zabudowa", mb), ("ksiazki", kmb), ("maskownice", msk)):
        if name == "maskownice" and widok == "X":
            continue
        if not m.keys:
            continue
        ob = bpy.data.objects.new(name, m.mesh(ctx, name))
        ob.location = (0.0, YM, 0.0)
        ctx.link(ob)
    if V.get("led_polki"):
        for x0, x1 in ((-W.X_ZEW, -W.X_REG), (W.X_REG, W.X_ZEW)):
            for z in list(W.POLKI) + [W.MOST_Z, W.POLKA_GORNA]:
                led_swiatlo(col, "led_polka", x0 + 0.03, x1 - 0.03, YM + F + 0.019, z - 0.006, 2.2)
    Ms = glosniki(ctx, col)
    if widok == "X":
        wiazki(ctx, Ms)
    sofa(ctx, random.Random("sofa"))
    stolik_i_dywan(ctx, random.Random("stolik"))
    rosliny_i_lampa(ctx)
    u = UJECIA[widok]
    co = kamera(sc, u["loc"], u["cel"], u["lens"])
    return sc, co, Ms


def punkty_opisu(sc, co, Ms, res):
    """Położenie opisywanych elementów na obrazie przekroju (piksele) – do podpisów w rysunek.py."""
    d = W.GLOSNIK[2]
    pts = {}
    bpy.context.view_layer.update()          # macierz kamery liczy się dopiero po aktualizacji sceny

    def px(name, p):
        v = world_to_camera_view(sc, co, Vector(p))
        pts[name] = (round(v.x * res[0]), round((1 - v.y) * res[1]))
    for s, Mg in zip(("L", "P"), Ms):
        px("glosnik_" + s, Mg @ Vector((0, 0, 0)))
        px("uchwyt_" + s, Mg @ Vector((0, d / 2 + 0.04, 0)))
        a = Mg @ Vector((0.0, -d / 2, 0.0))
        osz = (Mg.to_3x3() @ Vector((0.0, -1.0, 0.0))).normalized()
        L = (a.z - W.CEL_Z) / max(0.2, -osz.z)
        px("wiazka_" + s, a + osz * L * 0.55)
        px("cel_" + s, a + osz * L)
    px("wata", (W.G_X - 0.05, -0.22, W.SUFIT - W.PLYTA - 0.03))     # spód waty pod wieńcem (widoczny z dołu)
    px("led", (0.0, -0.035, W.MOST_Z - 0.01))
    px("maskownica", (W.G_X, -(W.GL - 0.005), W.MOST_Z + 0.25))
    px("dno_wneki", (W.G_X, -(W.GL - 0.1), W.MOST_Z))
    return pts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--widoki", default="A,B,C,X")
    ap.add_argument("--probki", type=int, default=64)
    ap.add_argument("--skala", type=float, default=1.0)
    ap.add_argument("--ekspozycja", type=float, default=0.0)
    ap.add_argument("--punkty", action="store_true", help="tylko punkty.json do opisów przekroju, bez renderu")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    a = ap.parse_args(argv)
    os.makedirs(OUT, exist_ok=True)
    res = (round(1600 * a.skala), round(1000 * a.skala))
    pj = os.path.join(OUT, "punkty.json")
    for w in a.widoki.split(","):
        sc, co, Ms = scena(w)
        nazwa = {"A": "wariant_A_biel_dab", "B": "wariant_B_lamele", "C": "wariant_C_grafit_orzech",
                 "X": "przekroj_glosniki"}[w]
        if w == "X":
            pts = dict(res=res, **punkty_opisu(sc, co, Ms, res))
            json.dump(pts, open(pj, "w"), indent=1)
        if a.punkty:
            continue
        render(sc, os.path.join(OUT, nazwa + ".jpg"), a.probki, res, a.ekspozycja)


if __name__ == "__main__":
    main()
