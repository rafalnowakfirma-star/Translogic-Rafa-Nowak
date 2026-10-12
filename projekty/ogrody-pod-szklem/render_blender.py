#!/usr/bin/env python3
"""Rendery Blender (Cycles) lub szybki podgląd (Workbench) z modelu domu.

Uruchom interpreterem z bpy:
  /home/user/tools/bpyenv/bin/python render_blender.py p01 --views lotu,ogrod,zmierzch --q final
  /home/user/tools/bpyenv/bin/python render_blender.py p01 --q podglad       (szybko, mało próbek)
"""
import argparse
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector  # noqa: E402

from podglad import load  # noqa: E402
from silnik.bryla import build_mesh  # noqa: E402
from silnik.geom import polygons  # noqa: E402


def lin(c):
    return tuple(max(0.0, x) ** 2.2 for x in c) + (1.0,)


M = {
    "tynk": dict(c=(0.93, 0.92, 0.89), r=0.85, var=0.03, ns=2),
    "tynk_wew": dict(c=(0.95, 0.94, 0.92), r=0.9),
    "tynk_mebel": dict(c=(0.9, 0.9, 0.88), r=0.8),
    "beton": dict(c=(0.66, 0.65, 0.62), r=0.82, var=0.07, ns=3),
    "beton_cokol": dict(c=(0.42, 0.42, 0.41), r=0.9),
    "strop": dict(c=(0.93, 0.92, 0.9), r=0.9),
    "drewno": dict(c=(0.58, 0.40, 0.24), r=0.6, var=0.12, planks=True),
    "drewno_opal": dict(c=(0.045, 0.04, 0.035), r=0.5, var=0.02, planks=True),
    "cegla": dict(brick=((0.55, 0.26, 0.17), (0.43, 0.2, 0.13)), r=0.85),
    "cegla_biala": dict(brick=((0.9, 0.89, 0.86), (0.8, 0.79, 0.76)), r=0.85),
    "kamien": dict(c=(0.80, 0.75, 0.66), r=0.7, var=0.07, ns=1.5),
    "trawertyn": dict(c=(0.84, 0.78, 0.68), r=0.6, var=0.06, ns=1.2),
    "corten": dict(c=(0.42, 0.18, 0.08), r=0.75, var=0.12, ns=6),
    "miedz": dict(c=(0.36, 0.60, 0.53), r=0.5, metal=0.3, var=0.1, ns=4),
    "blacha": dict(c=(0.17, 0.18, 0.19), r=0.45, metal=0.6),
    "rama": dict(c=(0.11, 0.11, 0.12), r=0.38, metal=0.6),
    "drzwi": dict(c=(0.24, 0.16, 0.10), r=0.5),
    "podloga_drewno": dict(c=(0.74, 0.58, 0.40), r=0.42, var=0.07, planks=True),
    "podloga_ciemna": dict(c=(0.35, 0.24, 0.15), r=0.45, planks=True),
    "podloga_kamien": dict(c=(0.80, 0.78, 0.74), r=0.32),
    "podloga_terakota": dict(c=(0.72, 0.42, 0.28), r=0.6),
    "podloga_tatami": dict(c=(0.78, 0.74, 0.52), r=0.8),
    "podloga_beton": dict(c=(0.62, 0.62, 0.6), r=0.5),
    "deck": dict(c=(0.56, 0.41, 0.28), r=0.7, var=0.1, planks=True),
    "sedum": dict(sedum=True),
    "zwir_dach": dict(c=(0.62, 0.6, 0.57), r=0.95, var=0.1, ns=40),
    "trawa": dict(grass=True),
    "trawa_ogrod": dict(grass=True),
    "sciezka": dict(c=(0.70, 0.68, 0.64), r=0.85, var=0.05, ns=3),
    "zwir_ogrod": dict(c=(0.87, 0.86, 0.82), r=0.95, var=0.06, ns=60),
    "zwir_grabiony": dict(c=(0.74, 0.73, 0.69), r=0.95, var=0.08, rake=True),
    "plyty_ogrod": dict(c=(0.77, 0.74, 0.68), r=0.7, var=0.06, ns=2),
    "mech": dict(c=(0.24, 0.37, 0.12), r=0.95, var=0.15, ns=8),
    "kamien_ogrod": dict(c=(0.42, 0.41, 0.39), r=0.8, var=0.12, ns=4),
    "wodospad": dict(c=(0.80, 0.90, 0.94), r=0.15, var=0.08, ns=30),
    "lupek": dict(c=(0.20, 0.205, 0.215), r=0.75, var=0.12, ns=6),
    "mozaika": dict(c=(0.22, 0.66, 0.62), r=0.25, var=0.1, ns=40),
    "woda_basen": dict(c=(0.55, 0.85, 0.82), r=0.05),
    "zielona_sciana": dict(c=(0.12, 0.22, 0.08), r=0.9, var=0.2, ns=12),
    "lisc_klon": dict(c=(0.62, 0.13, 0.05), r=0.7, var=0.18, ns=10, leaf=True),
    "lisc_zielony": dict(c=(0.18, 0.33, 0.09), r=0.7, var=0.15, ns=10, leaf=True),
    "lisc": dict(c=(0.20, 0.35, 0.11), r=0.7, var=0.15, ns=10, leaf=True),
    "lisc_brzoza": dict(c=(0.36, 0.50, 0.16), r=0.7, var=0.15, ns=10, leaf=True),
    "lisc_oliwka": dict(c=(0.40, 0.45, 0.30), r=0.7, var=0.1, ns=10, leaf=True),
    "lisc_sosna": dict(c=(0.09, 0.21, 0.09), r=0.8, var=0.1, ns=10, leaf=True),
    "lisc_palma": dict(c=(0.15, 0.38, 0.12), r=0.6, var=0.1, ns=10, leaf=True),
    "lisc_cytrus": dict(c=(0.13, 0.30, 0.08), r=0.6, var=0.1, ns=10, leaf=True, fruit=True),
    "lawenda": dict(c=(0.46, 0.39, 0.70), r=0.8, var=0.1, ns=10),
    "pien": dict(c=(0.22, 0.15, 0.10), r=0.9),
    "pien_brzoza": dict(c=(0.88, 0.87, 0.84), r=0.8),
    "donica": dict(c=(0.62, 0.36, 0.24), r=0.8),
    "tkanina": dict(c=(0.78, 0.75, 0.70), r=0.95),
    "tkanina_ciemna": dict(c=(0.16, 0.16, 0.17), r=0.9),
    "drewno_mebel": dict(c=(0.56, 0.40, 0.27), r=0.5),
    "rama_mebel": dict(c=(0.1, 0.1, 0.1), r=0.4),
    "kuchnia": dict(c=(0.88, 0.88, 0.86), r=0.3),
    "ceramika": dict(c=(0.96, 0.96, 0.96), r=0.12),
    "posciel": dict(c=(0.94, 0.93, 0.91), r=0.95),
    "szafa": dict(c=(0.82, 0.78, 0.72), r=0.6),
    "regal": dict(c=(0.56, 0.40, 0.27), r=0.6),
    "dywan": dict(c=(0.70, 0.64, 0.56), r=1.0),
    "czarny_lak": dict(c=(0.03, 0.03, 0.03), r=0.18),
    "kamien_mebel": dict(c=(0.6, 0.58, 0.55), r=0.6),
    "brąz": dict(c=(0.45, 0.30, 0.15), r=0.35, metal=0.8),
    "auto": dict(c=(0.2, 0.25, 0.3), r=0.3, metal=0.5),
    "czlowiek": dict(c=(0.14, 0.14, 0.16), r=0.8),
    "czlowiek_gora": dict(c=(0.55, 0.33, 0.28), r=0.8),
}


def make_mat(name, dusk=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = nodes["Principled BSDF"]
    out = nodes["Material Output"]
    if name in ("szklo", "szklo_mebel"):
        nodes.remove(bsdf)
        glass = nodes.new("ShaderNodeBsdfGlass")
        glass.inputs["Color"].default_value = (0.93, 0.97, 0.98, 1)
        glass.inputs["Roughness"].default_value = 0.0
        glass.inputs["IOR"].default_value = 1.45
        tr = nodes.new("ShaderNodeBsdfTransparent")
        tr.inputs["Color"].default_value = (0.9, 0.95, 0.96, 1)
        lp = nodes.new("ShaderNodeLightPath")
        mix = nodes.new("ShaderNodeMixShader")
        mx = nodes.new("ShaderNodeMath")
        mx.operation = "MAXIMUM"
        links.new(lp.outputs["Is Shadow Ray"], mx.inputs[0])
        links.new(lp.outputs["Is Diffuse Ray"], mx.inputs[1])
        links.new(mx.outputs[0], mix.inputs["Fac"])
        links.new(glass.outputs[0], mix.inputs[1])
        links.new(tr.outputs[0], mix.inputs[2])
        links.new(mix.outputs[0], out.inputs["Surface"])
        return m
    if name == "woda":
        bsdf.inputs["Base Color"].default_value = lin((0.06, 0.13, 0.15))
        bsdf.inputs["Roughness"].default_value = 0.04
        bsdf.inputs["Specular IOR Level"].default_value = 0.8
        return m
    if name == "lampa":
        bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
        return m
    d = M.get(name, dict(c=(0.75, 0.75, 0.73), r=0.8))
    tc = nodes.new("ShaderNodeTexCoord")
    if d.get("brick"):
        br = nodes.new("ShaderNodeTexBrick")
        br.inputs["Color1"].default_value = lin(d["brick"][0])
        br.inputs["Color2"].default_value = lin(d["brick"][1])
        br.inputs["Mortar"].default_value = lin((0.82, 0.8, 0.76))
        br.inputs["Scale"].default_value = 4.0
        br.inputs["Mortar Size"].default_value = 0.012
        br.offset = 0.5
        br.inputs["Brick Width"].default_value = 0.5
        br.inputs["Row Height"].default_value = 0.16
        links.new(tc.outputs["Object"], br.inputs["Vector"])
        links.new(br.outputs["Color"], bsdf.inputs["Base Color"])
    elif d.get("rake"):
        # grabiony żwir: równoległe bruzdy + drobne ziarno
        wv = nodes.new("ShaderNodeTexWave")
        wv.wave_type = "BANDS"
        wv.bands_direction = "X"
        wv.inputs["Scale"].default_value = 6.0
        wv.inputs["Distortion"].default_value = 0.6
        wv.inputs["Detail"].default_value = 1.0
        ns = nodes.new("ShaderNodeTexNoise")
        ns.inputs["Scale"].default_value = 140.0
        mx = nodes.new("ShaderNodeMix")
        mx.data_type = "FLOAT"
        mx.inputs["Factor"].default_value = 0.35
        cr = nodes.new("ShaderNodeValToRGB")
        base, var = d["c"], d.get("var", 0.06)
        cr.color_ramp.elements[0].color = lin(tuple(max(0, c - var * 2.4) for c in base))
        cr.color_ramp.elements[1].color = lin(tuple(min(1, c + var) for c in base))
        links.new(tc.outputs["Object"], wv.inputs["Vector"])
        links.new(tc.outputs["Object"], ns.inputs["Vector"])
        links.new(wv.outputs["Fac"], mx.inputs["A"])
        links.new(ns.outputs["Fac"], mx.inputs["B"])
        links.new(mx.outputs["Result"], cr.inputs["Fac"])
        links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.8
        links.new(mx.outputs["Result"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        bsdf.inputs["Roughness"].default_value = d.get("r", 0.95)
        return m
    elif d.get("sedum") or d.get("grass"):
        # dwie skale szumu: drobna faktura + duże plamy (z daleka trawa nie jest jednolita)
        ns = nodes.new("ShaderNodeTexNoise")
        ns.inputs["Scale"].default_value = 2.2 if d.get("grass") else 7.0
        ns.inputs["Detail"].default_value = 8
        nb = nodes.new("ShaderNodeTexNoise")
        nb.inputs["Scale"].default_value = 0.06 if d.get("grass") else 0.5
        nb.inputs["Detail"].default_value = 3
        mx = nodes.new("ShaderNodeMix")
        mx.data_type = "FLOAT"
        mx.inputs["Factor"].default_value = 0.55
        cr = nodes.new("ShaderNodeValToRGB")
        if d.get("sedum"):
            stops = [(0.0, (0.18, 0.24, 0.08)), (0.38, (0.30, 0.35, 0.13)), (0.55, (0.36, 0.38, 0.15)),
                     (0.72, (0.47, 0.27, 0.15)), (1.0, (0.55, 0.47, 0.22))]
        else:
            stops = [(0.0, (0.19, 0.25, 0.10)), (0.4, (0.26, 0.31, 0.14)), (0.6, (0.30, 0.33, 0.17)),
                     (1.0, (0.38, 0.37, 0.22))]
        cr.color_ramp.elements[0].position = stops[0][0]
        cr.color_ramp.elements[0].color = lin(stops[0][1])
        cr.color_ramp.elements[1].position = stops[-1][0]
        cr.color_ramp.elements[1].color = lin(stops[-1][1])
        for pos, col in stops[1:-1]:
            e = cr.color_ramp.elements.new(pos)
            e.color = lin(col)
        links.new(tc.outputs["Object"], ns.inputs["Vector"])
        links.new(tc.outputs["Object"], nb.inputs["Vector"])
        links.new(ns.outputs["Fac"], mx.inputs["A"])
        links.new(nb.outputs["Fac"], mx.inputs["B"])
        links.new(mx.outputs["Result"], cr.inputs["Fac"])
        links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.35
        nf = nodes.new("ShaderNodeTexNoise")
        nf.inputs["Scale"].default_value = 60.0
        links.new(tc.outputs["Object"], nf.inputs["Vector"])
        links.new(nf.outputs["Fac"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        bsdf.inputs["Roughness"].default_value = 0.95
        return m
    else:
        base = d["c"]
        var = d.get("var", 0)
        if d.get("planks"):
            wv = nodes.new("ShaderNodeTexWave")
            wv.inputs["Scale"].default_value = 3.2
            wv.inputs["Distortion"].default_value = 1.5
            wv.inputs["Detail"].default_value = 2
            ns = nodes.new("ShaderNodeTexNoise")
            ns.inputs["Scale"].default_value = 18
            mixc = nodes.new("ShaderNodeMix")
            mixc.data_type = "RGBA"
            mixc.inputs["Factor"].default_value = 0.5
            cr = nodes.new("ShaderNodeValToRGB")
            cr.color_ramp.elements[0].color = lin(tuple(max(0, c - var - 0.04) for c in base))
            cr.color_ramp.elements[1].color = lin(tuple(min(1, c + var) for c in base))
            links.new(tc.outputs["Object"], wv.inputs["Vector"])
            links.new(wv.outputs["Fac"], cr.inputs["Fac"])
            links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
        elif var > 0:
            ns = nodes.new("ShaderNodeTexNoise")
            ns.inputs["Scale"].default_value = d.get("ns", 3)
            ns.inputs["Detail"].default_value = 4
            cr = nodes.new("ShaderNodeValToRGB")
            cr.color_ramp.elements[0].color = lin(tuple(max(0, c - var) for c in base))
            cr.color_ramp.elements[1].color = lin(tuple(min(1, c + var) for c in base))
            links.new(tc.outputs["Object"], ns.inputs["Vector"])
            links.new(ns.outputs["Fac"], cr.inputs["Fac"])
            links.new(cr.outputs["Color"], bsdf.inputs["Base Color"])
        else:
            bsdf.inputs["Base Color"].default_value = lin(base)
    bsdf.inputs["Roughness"].default_value = d.get("r", 0.8)
    bsdf.inputs["Metallic"].default_value = d.get("metal", 0.0)
    if d.get("leaf"):
        bsdf.inputs["Subsurface Weight"].default_value = 0.15
        # liście: drobna nierówność zamiast gładkich ścianek
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.7
        nf = nodes.new("ShaderNodeTexVoronoi")
        nf.inputs["Scale"].default_value = 14.0
        links.new(tc.outputs["Object"], nf.inputs["Vector"])
        links.new(nf.outputs["Distance"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def build_scene(H, var_extra="lato", dusk=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    Mh = build_mesh(H)
    minx, miny, maxx, maxy = H.bbox
    ox, oy = (minx + maxx) / 2, (miny + maxy) / 2
    mats = {}
    for (var, mat), tris in Mh.g.items():
        if var not in ("base", var_extra):
            continue
        verts, faces, idx = [], [], {}
        for tri in tris:
            f = []
            for (x, y, z) in tri:
                key = (round(x - ox, 4), round(-(y - oy), 4), round(z, 4))
                k = idx.get(key)
                if k is None:
                    k = len(verts)
                    idx[key] = k
                    verts.append(key)
                f.append(k)
            if len(set(f)) == 3:
                faces.append(f)
        me = bpy.data.meshes.new(f"{mat}_{var}")
        me.from_pydata(verts, [], faces)
        me.update()
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        ob = bpy.data.objects.new(f"{mat}_{var}", me)
        sc.collection.objects.link(ob)
        if mat not in mats:
            mats[mat] = make_mat(mat, dusk)
        me.materials.append(mats[mat])
        if mat in ("szklo", "szklo_mebel"):
            ob.visible_shadow = True
    # teren
    bpy.ops.mesh.primitive_circle_add(vertices=96, radius=260, fill_type="NGON", location=(0, 0, -0.31))
    g = bpy.context.object
    g.data.materials.append(make_mat("trawa"))
    return sc, Mh, (ox, oy)


def world(sc, dusk=False):
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    try:
        sky.sky_type = "NISHITA"
    except Exception:
        pass
    sky.sun_disc = False
    sky.sun_elevation = math.radians(2.0 if dusk else 38)
    sky.sun_rotation = math.radians(205 if not dusk else 250)
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.10 if dusk else 0.32
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 0.35 if dusk else 3.2
    sun.color = (1.0, 0.62, 0.38) if dusk else (1.0, 0.96, 0.9)
    sun.angle = math.radians(1.5)
    so = bpy.data.objects.new("sun", sun)
    sc.collection.objects.link(so)
    so.rotation_euler = (math.radians(90 - (4 if dusk else 38)), 0, math.radians(205 if not dusk else 250))


def add_cam(sc, loc, target, lens):
    cam = bpy.data.cameras.new("cam")
    cam.lens = lens
    cam.sensor_width = 36
    co = bpy.data.objects.new("cam", cam)
    sc.collection.objects.link(co)
    co.location = loc
    d = Vector(target) - Vector(loc)
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    return co


def cam_views(H, off):
    ox, oy = off
    minx, miny, maxx, maxy = H.bbox
    R = 0.5 * math.hypot(maxx - minx, maxy - miny)
    ztop = max(L["level"].z + L["level"].h for L in H.L.values())
    views = {}
    # z lotu ptaka – z południowego zachodu
    az = math.radians(225)
    el = math.radians(34)
    dist = (R + 2) / math.sin(math.radians(17)) * 0.9
    tx, ty, tz = 0, 0, ztop * 0.35
    views["lotu"] = ((tx + dist * math.cos(el) * math.cos(az) * 1.0, ty + dist * math.cos(el) * math.sin(az), tz + dist * math.sin(el)), (tx, ty, tz), 40)
    # wnętrze ogrodu
    gs = [r for r in H.all_rooms if r.kind == "ogrod"]
    if gs:
        g = gs[0]
        net = g.net if g.net is not None else g.poly
        c = net.centroid
        best = None
        for p in list(net.exterior.coords)[:-1]:
            d = math.hypot(p[0] - c.x, p[1] - c.y)
            if best is None or d > best[0]:
                best = (d, p)
        vx, vy = best[1]
        px, py = vx + 0.18 * (c.x - vx), vy + 0.18 * (c.y - vy)
        tx_, ty_ = c.x + 0.6 * (c.x - vx), c.y + 0.6 * (c.y - vy)
        views["ogrod"] = ((px - ox, -(py - oy), 1.55 + g.z0), (tx_ - ox, -(ty_ - oy), 2.9 + g.z0), 15)
    # zmierzch – od strony z największym przeszkleniem
    best = None
    for idx, L in H.L.items():
        for run in L["walls"]:
            if run.cls in ("glass", "fold") and (run.other is None or run.other.outdoor):
                ang = run.angle
                score = run.length
                if best is None:
                    best = {}
                k = int(((ang + 22.5) % 360) // 45)
                best[k] = best.get(k, 0) + score
    if best:
        k = max(best, key=best.get)
        ang = math.radians(k * 45)
    else:
        ang = math.radians(90)
    nx, ny = math.cos(ang), math.sin(ang)
    dd = R * 1.75 + 4
    views["zmierzch"] = ((nx * dd, -ny * dd, 1.75), (0, 0, 2.6), 24)
    return views


def render(pid, views, q, outdir):
    H = load(pid).build()
    os.makedirs(outdir, exist_ok=True)
    done = []
    for v in views:
        dusk = v == "zmierzch"
        var = "zima" if dusk else "lato"
        sc, Mh, off = build_scene(H, var_extra=var, dusk=dusk)
        world(sc, dusk)
        vs = cam_views(H, off)
        if v not in vs:
            continue
        loc, tgt, lens = vs[v]
        add_cam(sc, loc, tgt, lens)
        if dusk:
            for poly, z, kind in Mh.lights:
                c = poly.centroid
                minx, miny, maxx, maxy = poly.bounds
                li = bpy.data.lights.new("l", "AREA")
                li.shape = "RECTANGLE"
                li.size = max(0.4, maxx - minx)
                li.size_y = max(0.4, maxy - miny)
                li.energy = min(900, 45 * poly.area)
                li.color = (1.0, 0.78, 0.55)
                lo = bpy.data.objects.new("l", li)
                sc.collection.objects.link(lo)
                lo.location = (c.x - off[0], -(c.y - off[1]), z - 0.05)
            for g in [r for r in H.all_rooms if r.kind == "ogrod"]:
                lay = getattr(g, "_layout", None)
                for ft in (lay["features"] if lay else []):
                    if ft.t in ("klon", "brzoza", "oliwka", "palma", "sosna", "cytrus"):
                        li = bpy.data.lights.new("g", "POINT")
                        li.energy = 120
                        li.color = (1.0, 0.85, 0.65)
                        li.shadow_soft_size = 0.3
                        lo = bpy.data.objects.new("g", li)
                        sc.collection.objects.link(lo)
                        lo.location = (ft.x - off[0], -(ft.y - off[1]), g.z0 + 0.25)
        sc.render.engine = "CYCLES"
        sc.cycles.device = "CPU"
        sc.cycles.samples = {"podglad": 16, "szybki": 40}.get(q, 72 if v == "lotu" else 110)
        sc.cycles.use_adaptive_sampling = True
        sc.cycles.adaptive_threshold = 0.03 if q == "final" else 0.08
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 6 if q == "final" else 3
        sc.cycles.transmission_bounces = 8 if q == "final" else 4
        sc.cycles.transparent_max_bounces = 16
        sc.cycles.caustics_reflective = False
        sc.cycles.caustics_refractive = False
        sc.render.resolution_x, sc.render.resolution_y = {"final": (1600, 1000), "szybki": (1000, 625)}.get(q, (720, 450))
        sc.view_settings.view_transform = "AgX"
        try:
            sc.view_settings.look = "AgX - Medium High Contrast"
        except Exception:
            pass
        sc.view_settings.exposure = 0.6 if dusk else -0.25
        sc.render.image_settings.file_format = "JPEG"
        sc.render.image_settings.quality = 88
        fn = os.path.join(outdir, f"{v}.jpg")
        sc.render.filepath = fn
        t = time.time()
        bpy.ops.render.render(write_still=True)
        done.append((v, round(time.time() - t, 1)))
    print("RENDER", pid, done)


def _slot(n=2):
    """Najwyżej n renderów naraz (wielu projektantów pracuje równolegle – oszczędzamy pamięć)."""
    import fcntl
    d = os.path.join(HERE, "out", ".locks")
    os.makedirs(d, exist_ok=True)
    while True:
        for i in range(n):
            f = open(os.path.join(d, f"render_{i}.lock"), "w")
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return f
            except BlockingIOError:
                f.close()
        time.sleep(2.0)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pid")
    ap.add_argument("--views", default="lotu,ogrod")
    ap.add_argument("--q", default="final", choices=["podglad", "szybki", "final"])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(HERE, "out", a.pid, "render" if a.q != "podglad" else "podglad3d")
    lock = _slot(int(os.environ.get("OGRODY_SLOTY", "2")))
    render(a.pid, a.views.split(","), a.q, out)
