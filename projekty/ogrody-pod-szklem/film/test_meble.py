#!/usr/bin/env python3
"""Test mebli 3D (film/meble3d.py): salon wystawowy wszystkich rodzajów, wnętrze dzień/wieczór, test obrotów.

Uruchom (interpreter z bpy):
  /home/user/tools/bpyenv/bin/python film/test_meble.py                      # wszystkie ujęcia
  /home/user/tools/bpyenv/bin/python film/test_meble.py --widoki salon,zmierzch --probki 32
Wyniki: out/film/test_meble/*.jpg oraz trojkaty.txt (trójkąty na rodzaj) i obroty.txt (sprawdzenie pleców).
"""
import argparse
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
os.environ.setdefault("MEBLE3D_DEBUG", "1")

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from film import meble3d  # noqa: E402
from film.kontekst import Ctx, zasob  # noqa: E402
from silnik import meble as M  # noqa: E402

OUT = os.path.join(HERE, "out", "film", "test_meble")


class Pokoj:
    def __init__(self, kind="salon", top=2.9, z0=0.0):
        self.kind, self.top, self.z0 = kind, top, z0


def put(it, x, y, rot=0.0, room="salon", top=2.9):
    it.cx, it.cy, it.rot, it.z = x, y, rot, 0.0
    it.room = Pokoj(room, top)
    return it


def item(kind, w, d, parts, h=1.0, shapes=None):
    return M.Item(kind, w, d, shapes or [], parts, h)


# ------------------------------------------------------------------ scena
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def floor_mat():
    m = bpy.data.materials.new("podloga_dab")
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / 2.6, 1 / 1.3, 1)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])
    out = {}
    for k in ("diffuse", "roughness", "bump"):
        im = N.new("ShaderNodeTexImage")
        im.image = bpy.data.images.load(zasob(f"tekstury/hardwood2_{k}.jpg"), check_existing=True)
        if k != "diffuse":
            im.image.colorspace_settings.name = "Non-Color"
        L.new(mp.outputs["Vector"], im.inputs["Vector"])
        out[k] = im
    hs = N.new("ShaderNodeHueSaturation")
    hs.inputs["Saturation"].default_value = 0.55
    hs.inputs["Value"].default_value = 1.12
    hs.inputs["Hue"].default_value = 0.49
    L.new(out["diffuse"].outputs["Color"], hs.inputs["Color"])
    L.new(hs.outputs["Color"], b.inputs["Base Color"])
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.32
    mr.inputs["To Max"].default_value = 0.6
    L.new(out["roughness"].outputs["Color"], mr.inputs["Value"])
    L.new(mr.outputs[0], b.inputs["Roughness"])
    bp = N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.15
    bp.inputs["Distance"].default_value = 0.002
    L.new(out["bump"].outputs["Color"], bp.inputs["Height"])
    L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def plain(name, col, rough=0.9):
    m = bpy.data.materials.new(name)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = meble3d.rgba(col)
    b.inputs["Roughness"].default_value = rough
    return m


def slab(name, x0, y0, z0, x1, y1, z1, m):
    """Prostopadłościan w układzie Blendera (ściany, podłoga, sufit)."""
    me = bpy.data.meshes.new(name)
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(v, [], f)
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def world(sc, dusk=False, sun_el=34.0, sun_az=150.0, strength=None):
    w = bpy.data.worlds.new("niebo")
    sc.world = w
    nt = w.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "SINGLE_SCATTERING"       # model Nishity
    sky.sun_disc = False
    el = 1.5 if dusk else sun_el
    sky.sun_elevation = math.radians(el)
    sky.sun_rotation = math.radians(sun_az)
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength if strength is not None else (0.22 if dusk else 0.35)
    li = bpy.data.lights.new("slonce", "SUN")
    li.energy = 0.25 if dusk else 3.4
    li.color = (1.0, 0.55, 0.32) if dusk else (1.0, 0.96, 0.9)
    li.angle = math.radians(1.2)
    so = bpy.data.objects.new("slonce", li)
    sc.collection.objects.link(so)
    # słońce świeci z kierunku azymutu sun_az (od osi +Y Blendera zgodnie z zegarem, jak w niebie Nishity)
    so.rotation_euler = (math.radians(90 - el), 0, math.radians(sun_az) + math.pi)
    return so


def camera(sc, loc, target, lens=22.0, ortho=None):
    cam = bpy.data.cameras.new("kamera")
    cam.lens = lens
    cam.sensor_width = 36
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    co = bpy.data.objects.new("kamera", cam)
    sc.collection.objects.link(co)
    co.location = loc
    d = Vector(target) - Vector(loc)
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    return co


def render(sc, name, samples=40, res=(960, 540), exposure=0.0, wb=None):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.04
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except TypeError:
        pass
    sc.cycles.max_bounces = 6
    sc.cycles.diffuse_bounces = 3
    sc.cycles.glossy_bounces = 3
    sc.cycles.transmission_bounces = 6
    sc.cycles.transparent_max_bounces = 12
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
    sc.view_settings.exposure = exposure
    if wb:
        # balans bieli aparatu (wieczorem ~3800 K: ciepłe lampy wyglądają ciepło, nie pomarańczowo)
        sc.view_settings.use_white_balance = True
        sc.view_settings.white_balance_temperature = wb
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 90
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, name + ".jpg")
    sc.render.filepath = fn
    from render_blender import _slot
    lock = _slot(2)
    t = time.time()
    try:
        bpy.ops.render.render(write_still=True)
    finally:
        lock.close()
    print(f"RENDER {name}: {time.time() - t:.0f} s -> {fn}")
    return fn


def ground():
    """Teren wokół (żeby za otwartymi bokami nie było czarnego horyzontu)."""
    me = bpy.data.meshes.new("teren")
    R_ = 400.0
    me.from_pydata([(-R_, -R_, -0.06), (R_, -R_, -0.06), (R_, R_, -0.06), (-R_, R_, -0.06)], [], [(0, 1, 2, 3)])
    me.materials.append(plain("teren", (0.42, 0.44, 0.36), 0.95))
    ob = bpy.data.objects.new("teren", me)
    bpy.context.scene.collection.objects.link(ob)


def room_shell(sc, x0, y0, x1, y1, top, walls=("N", "W"), ceiling=True):
    """Podłoga z dębu, białe ściany (plan → Blender: Y = −y)."""
    ground()
    fm = floor_mat()
    wm = plain("tynk_sciana", (0.86, 0.85, 0.82), 0.9)
    slab("podloga", x0, -y1, -0.05, x1, -y0, 0.0, fm)
    t = 0.15
    if "N" in walls:
        slab("sciana_N", x0 - t, -y0, 0, x1, -y0 + t, top, wm)
    if "W" in walls:
        slab("sciana_W", x0 - t, -y1, 0, x0, -y0 + t, top, wm)
    if "E" in walls:
        slab("sciana_E", x1, -y1, 0, x1 + t, -y0 + t, top, wm)
    if "S" in walls:
        slab("sciana_S", x0 - t, -y1 - t, 0, x1 + t, -y1, top, wm)
    if ceiling:
        slab("sufit", x0 - t, -y1 - t, top, x1 + t, -y0 + t, top + 0.2, wm)


# ------------------------------------------------------------------ układy
def arrangement(room_kind="salon_kuchnia", top=2.9):
    """Salon z kuchnią i jadalnią (współrzędne planu: x – wschód, y – południe)."""
    its = []
    its.append(put(M.rug(3.0, 2.2), 1.75, 4.9, -90, room_kind, top))
    its.append(put(M.sofa(2.6), 0.51, 4.9, -90, room_kind, top))
    its.append(put(M.coffee_table(1.1, 0.6), 1.85, 4.9, -90, room_kind, top))
    its.append(put(M.armchair(), 3.05, 3.85, 90 + 30, room_kind, top))
    its.append(put(M.armchair(), 3.05, 5.95, 90 - 30, room_kind, top))
    its.append(put(M.fireplace(), 2.2, 0.33, 0, room_kind, top))
    its.append(put(M.counter(3.6), 6.7, 0.34, 0, room_kind, top))
    its.append(put(M.island(2.2), 6.7, 2.15, 0, room_kind, top))
    its.append(put(M.dining(6), 6.6, 5.0, 0, room_kind, top))
    its.append(put(M.planter(0.4, "zielen"), 0.5, 7.1, 0, room_kind, top))
    return its


def showroom():
    """Wszystkie rodzaje w siatce (z rodzajem pokoju, który wpływa na wyposażenie)."""
    cells = [
        (M.sofa(2.6), "salon"), (M.armchair(), "salon"), (M.coffee_table(1.2, 0.7), "salon"), (M.round_coffee(0.45), "salon"),
        (M.rug(3.0, 2.2), "salon"), (M.tv_unit(), "salon"), (M.fireplace(), "salon"), (M.dining(6), "jadalnia"),
        (M.round_dining(0.65, 6), "jadalnia"), (M.bed(1.8, 2.1), "sypialnia_glowna"), (M.bed(1.2, 2.0, False), "pokoj"),
        (M.wardrobe(2.0), "sypialnia"), (M.shelves(2.4), "biblioteka"), (M.shelves(1.8, 0.45, False), "spizarnia"),
        (M.shelves(1.8, 0.45, False), "jadalnia"), (M.counter(3.6), "kuchnia"), (M.island(2.4), "kuchnia"),
        (M.desk(1.6), "biuro"), (M.desk_pair(1.8), "biuro"), (M.bathtub(1.8, 0.85, True), "lazienka"),
        (M.bathtub(), "lazienka"), (M.shower(), "lazienka"), (M.wc(), "lazienka"), (M.basins(1.4, 0.5, 2), "lazienka"),
        (M.basins(0.9, 0.5, 1), "lazienka"), (M.washer(), "pralnia"), (M.tank(), "pralnia"), (M.piano(), "muzyczny"),
        (M.easel(), "pracownia"), (M.workbench(), "pracownia"), (M.low_table(), "herbaciarnia"), (M.lounger(), "taras"),
        (M.planter(0.4, "cytrus"), "oranzeria"), (M.planter(0.45, "zielen"), "patio"), (M.bench(1.8, 0.45), "galeria"),
        (M.bench(1.4, 0.4), "wiatrolap"), (M.plinth(), "galeria"), (M.sauna_bench(), "sauna"), (M.stove(), "sauna"),
        (M.car(), "garaz"), (M.mat(), "silownia"), (M.wine_rack(1.8), "winiarnia"), (M.dining(6, 2.0, 0.95), "patio"),
        (M.round_dining(0.45, 3), "taras"), (M.counter(1.6, 0.6, True, False), "pralnia"),
    ]
    extra = [
        (M.Item("tokonoma", 1.6, 0.5, [], [("box", 0, 0, 0, 1.6, 0.5, 0.25, "drewno_mebel")], 0.25), "herbaciarnia"),
        (M.Item("stolek", 0.5, 0.5, [], [("cyl", 0, 0, 0, 0.2, 0.6, "tkanina")], 0.6), "pracownia"),
        (M.Item("rower", 0.6, 1.4, [], [("box", 0, 0, 0, 0.5, 1.3, 1.1, "czarny_lak")], 1.1), "silownia"),
        (M.Item("ekran", 2.8, 0.2, [], [("box", 0, 0, 0.6, 2.8, 0.1, 1.6, "czarny_lak")], 2.2), "kino"),
        (M.Item("pompa", 0.8, 0.6, [], [("box", 0, 0, 0, 0.8, 0.6, 1.0, "ceramika")], 1.0), "techniczne"),
        (M.Item("wyspa", 1.4, 0.7, [], [("box", 0, 0, 0, 1.4, 0.7, 0.9, "drewno_mebel")], 0.9), "garderoba"),
    ]
    cells += extra
    its = []
    ncol = 8
    cw, ch = 4.4, 4.4
    for k, (it, rk) in enumerate(cells):
        i, j = k % ncol, k // ncol
        put(it, i * cw, j * ch, 0, rk, 2.9 if rk not in ("salon", "kuchnia") else 3.2)
        its.append(it)
    return its


def tri_table(its, ctx):
    rows = {}
    for it in its:
        obs = meble3d.build_items([it], ctx)
        n = meble3d.tri_count(obs)
        key = it.kind + ("" if it.kind not in ("stol", "regal", "lozko", "wanna", "umywalki", "lawka", "donica", "blat")
                         else f" ({it.room.kind})")
        rows[key] = max(rows.get(key, 0), n)
    return rows


# ------------------------------------------------------------------ ujęcia
def view_salon(dusk, samples, seed, name, res=(960, 540)):
    sc = reset()
    ctx = Ctx(seed=seed, dusk=dusk)
    room_shell(sc, 0, 0, 9.5, 7.6, 2.9, walls=("N", "W"))
    its = arrangement()
    meble3d.build_items(its, ctx)
    world(sc, dusk, sun_el=30, sun_az=140)
    camera(sc, (9.0, -7.3, 1.52), (2.6, -2.6, 0.95), 21)
    return render(sc, name, samples, res, exposure=0.25 if not dusk else 0.3, wb=3800 if dusk else None)


def view_showroom(samples, seed, name, res=(960, 540)):
    sc = reset()
    ctx = Ctx(seed=seed, dusk=False)
    its = showroom()
    t = time.time()
    meble3d.build_items(its, ctx)
    print(f"budowa {len(its)} elementów: {time.time() - t:.1f} s")
    ground()
    fm = floor_mat()
    slab("podloga", -3, -30, -0.05, 34, 3, 0.0, fm)
    world(sc, False, sun_el=40, sun_az=150)
    camera(sc, (15.4, -38.0, 22.0), (15.4, -12.5, 0.0), 28)
    return render(sc, name, samples, res, exposure=0.0)


def view_group(kind, samples, seed, name, res=(960, 540), dusk=False):
    """Zbliżenia grup do oceny detali."""
    sc = reset()
    ctx = Ctx(seed=seed, dusk=dusk)
    g = []
    if kind == "sypialnia":
        room_shell(sc, 0, 0, 7, 6, 2.9, walls=("N", "W"))
        g = [put(M.bed(1.8, 2.1), 2.4, 1.08, 0, "sypialnia_glowna"), put(M.wardrobe(2.0), 0.34, 3.6, -90, "sypialnia_glowna"),
             put(M.bench(1.4, 0.45), 2.4, 2.55, 0, "sypialnia_glowna"), put(M.armchair(), 5.0, 1.0, 200, "sypialnia_glowna"),
             put(M.shelves(1.2), 5.2, 0.22, 0, "pokoj")]
        cam = ((5.6, -5.4, 1.5), (2.0, -1.0, 0.7), 22)
    elif kind == "lazienka":
        room_shell(sc, 0, 0, 6, 5, 2.9, walls=("N", "W"))
        g = [put(M.bathtub(1.8, 0.85, True), 3.4, 1.4, 0, "lazienka"), put(M.basins(1.4, 0.5, 2), 1.2, 0.28, 0, "lazienka"),
             put(M.wc(), 0.37, 1.8, -90, "lazienka"), put(M.shower(), 0.53, 3.4, -90, "lazienka"),
             put(M.washer(), 5.2, 0.34, 0, "lazienka")]
        cam = ((4.8, -4.6, 1.5), (1.6, -1.2, 0.8), 22)
    elif kind == "biuro":
        room_shell(sc, 0, 0, 7, 6, 2.9, walls=("N", "W"))
        g = [put(M.desk_pair(1.8), 3.6, 2.7, 0, "biuro"), put(M.desk(1.6), 1.2, 0.71, 0, "biuro"),
             put(M.shelves(2.4), 0.22, 3.6, -90, "biuro"), put(M.armchair(), 5.6, 1.0, 200, "biuro"),
             put(M.round_coffee(0.3), 5.6, 2.0, 0, "biuro")]
        cam = ((6.4, -5.5, 1.55), (2.4, -1.6, 0.8), 22)
    elif kind == "kuchnia":
        room_shell(sc, 0, 0, 6, 5, 2.9, walls=("N", "W"))
        g = [put(M.counter(3.6), 2.4, 0.34, 0, "kuchnia"), put(M.island(2.2), 2.4, 2.3, 0, "kuchnia")]
        cam = ((4.9, -4.4, 1.6), (1.8, -0.8, 0.9), 24)
    elif kind == "rozne":
        ground()
        fm = floor_mat()
        slab("podloga", -2, -12, -0.05, 22, 3, 0.0, fm)
        g = [put(M.piano(), 1.0, 0.0, 0, "muzyczny"), put(M.easel(), 3.6, 0.0, 0, "pracownia"),
             put(M.workbench(), 6.6, 0.0, 0, "pracownia"), put(M.wine_rack(1.8), 9.8, 0.0, 0, "winiarnia"),
             put(M.plinth(), 12.0, 0.0, 0, "galeria"), put(M.planter(0.4, "cytrus"), 13.4, 0.0, 0, "oranzeria"),
             put(M.planter(0.45, "zielen"), 14.8, 0.0, 0, "patio"), put(M.lounger(), 16.4, 0.4, 0, "taras"),
             put(M.sauna_bench(), 2.0, 3.6, 0, "sauna"), put(M.stove(), 3.8, 3.8, 0, "sauna"),
             put(M.low_table(), 6.4, 4.0, 0, "herbaciarnia"), put(M.mat(), 9.0, 4.0, 0, "silownia"),
             put(M.Item("rower", 0.6, 1.4, [], [("box", 0, 0, 0, 0.5, 1.3, 1.1, "czarny_lak")], 1.1), 10.4, 4.0, 0, "silownia"),
             put(M.car(), 13.8, 4.6, 90, "garaz"), put(M.tv_unit(), 18.0, 3.4, 0, "salon"),
             put(M.tank(), 20.0, 3.4, 0, "pralnia")]
        cam = ((10.0, -14.5, 5.0), (10.0, -1.8, 0.6), 24)
    meble3d.build_items(g, ctx)
    world(sc, dusk, sun_el=32, sun_az=150)
    camera(sc, *cam)
    return render(sc, name, samples, res, exposure=0.25 if kind != "rozne" else 0.0)


STUDIO = {
    "salon": [(M.sofa(2.6), "salon"), (M.armchair(), "salon")],
    "stolik": [(M.round_coffee(0.45), "salon"), (M.coffee_table(1.1, 0.6), "salon"), (M.round_coffee(0.3), "biuro")],
    "stol": [(M.dining(6), "jadalnia")],
    "stolokr": [(M.round_dining(0.65, 6), "jadalnia")],
    "lozko": [(M.bed(1.8, 2.1), "sypialnia_glowna")],
    "lozko1": [(M.bed(1.2, 2.0, False), "pokoj"), (M.wardrobe(1.6), "pokoj")],
    "regal": [(M.shelves(2.4), "biblioteka"), (M.shelves(1.8, 0.45, False), "spizarnia")],
    "regal2": [(M.shelves(1.8, 0.45, False), "jadalnia"), (M.shelves(2.0, 0.4, False), "pracownia")],
    "wc": [(M.wc(), "lazienka"), (M.basins(0.9, 0.5, 1), "lazienka"), (M.washer(), "pralnia"), (M.tank(), "pralnia")],
    "wanna": [(M.bathtub(), "lazienka"), (M.shower(), "lazienka")],
    "fortepian": [(M.piano(), "muzyczny", 180)],
    "rtv": [(M.tv_unit(), "salon"), (M.fireplace(), "salon")],
    "warsztat": [(M.workbench(), "pracownia"), (M.easel(), "pracownia")],
    "wino": [(M.wine_rack(1.8), "winiarnia"), (M.plinth(), "galeria"), (M.planter(0.4, "cytrus"), "oranzeria")],
    "ogrod": [(M.lounger(), "taras"), (M.dining(6, 2.0, 0.95), "patio"), (M.bench(1.8, 0.45), "patio")],
    "sauna": [(M.sauna_bench(), "sauna"), (M.stove(), "sauna"), (M.low_table(), "herbaciarnia")],
    "inne": [(M.mat(), "silownia"), (M.Item("rower", 0.6, 1.4, [], [("box", 0, 0, 0, 0.5, 1.3, 1.1, "czarny_lak")], 1.1), "silownia"),
             (M.Item("stolek", 0.5, 0.5, [], [("cyl", 0, 0, 0, 0.2, 0.6, "tkanina")], 0.6), "pracownia"),
             (M.Item("tokonoma", 1.6, 0.5, [], [("box", 0, 0, 0, 1.6, 0.5, 0.25, "drewno_mebel")], 0.25), "herbaciarnia")],
    "biurko": [(M.desk(1.6), "biuro")],
    "auto": [(M.car(), "garaz")],
}


def view_studio(key, samples, seed, name, res=(800, 450), dusk=False):
    """Zbliżenie kilku elementów w rzędzie pod ścianą (plecy do ściany na północy)."""
    sc = reset()
    ctx = Ctx(seed=seed, dusk=dusk)
    group = [g if len(g) == 3 else g + (0,) for g in STUDIO[key]]
    x = 0.0
    for it, rk, rot in group:
        x += it.w / 2
        put(it, x, it.d / 2 + 0.03, rot, rk, 2.9)
        x += it.w / 2 + 0.6
    span = x - 0.6
    dmax = max(g[0].d for g in group)
    hmax = max(min(g[0].h, 2.4) for g in group)
    room_shell(sc, -3, 0, span + 3, 9, 3.0, walls=("N",), ceiling=False)
    meble3d.build_items([g[0] for g in group], ctx)
    world(sc, dusk, sun_el=35, sun_az=200)
    cx = span / 2
    dist = max(span / 2 + 0.4, hmax * 0.75, dmax * 0.8) / 0.6 * 1.05
    a = math.radians(28)
    camera(sc, (cx + dist * math.sin(a), -(dmax / 2 + dist * math.cos(a)), 1.15 + hmax * 0.3), (cx, -dmax / 2, hmax * 0.36), 30)
    return render(sc, name, samples, res, exposure=0.0 if not dusk else 0.3, wb=3800 if dusk else None)


def view_obroty(samples, seed, name):
    """Plecy przy ścianach: element przy każdej ścianie kwadratowego pokoju z obrotem jak z Placer.against."""
    sc = reset()
    ctx = Ctx(seed=seed)
    room_shell(sc, 0, 0, 7, 7, 1.0, walls=("N", "W", "E", "S"), ceiling=False)
    # obrót z _wall_pose: N → 0, E → 90, S → 180, W → 270 (−90)
    its = [put(M.sofa(2.4), 3.5, 0.51, 0, "salon"), put(M.bed(1.6, 2.0), 6.0 - 0.03 + 1.0 - 0.0 - 0.0, 3.5, 90, "sypialnia"),
           put(M.wardrobe(2.0), 3.5, 7 - 0.34, 180, "sypialnia"), put(M.counter(2.4), 0.34, 3.5, 270, "kuchnia")]
    its[1].cx = 7 - 1.05 - 0.03
    lines = []
    walls = {0: ("N", (None, 0.0)), 90: ("E", (7.0, None)), 180: ("S", (None, 7.0)), 270: ("W", (0.0, None))}
    for it in its:
        obs = meble3d.build_items([it], ctx)
        bpy.context.view_layer.update()
        root = obs[0]
        back = root.matrix_world.to_3x3() @ Vector((0, 1, 0))
        # najdalszy punkt geometrii w kierunku pleców
        far = None
        for ob in obs:
            if ob.type == "MESH":
                for c in ob.bound_box:
                    p = ob.matrix_world @ Vector(c)
                    v = p.dot(back)
                    far = v if far is None else max(far, v)
        wall, (wx, wy) = walls[int(it.rot) % 360]
        # odległość pleców od ściany (Blender: X = x, Y = −y)
        if wx is not None:
            dist = abs(wx - far * (1 if back.x > 0 else -1)) if abs(back.x) > 0.9 else None
        else:
            dist = abs(-wy - far * (1 if back.y > 0 else -1)) if abs(back.y) > 0.9 else None
        ok = dist is not None and dist < 0.08
        lines.append(f"{it.kind:8s} rot={int(it.rot):4d} ściana {wall}: plecy (+Y lokalnie) → świat ({back.x:+.2f}, {back.y:+.2f}),"
                     f" odległość pleców od ściany {dist if dist is None else round(dist, 3)} m  {'OK' if ok else 'BŁĄD'}")
    world(sc, False, sun_el=60, sun_az=160)
    camera(sc, (3.5, -3.5, 20.0), (3.5, -3.5, 0.0), 50, ortho=8.2)
    fn = render(sc, name, samples, (720, 720), exposure=0.0)
    with open(os.path.join(OUT, "obroty.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return fn


def triangles(seed):
    reset()
    ctx = Ctx(seed=seed)
    rows = tri_table(showroom(), ctx)
    house = arrangement()
    reset()
    ctx = Ctx(seed=seed)
    tot = meble3d.tri_count(meble3d.build_items(house, ctx))
    lines = [f"{k:28s} {v:8d}" for k, v in sorted(rows.items(), key=lambda kv: -kv[1])]
    lines.append(f"{'zestaw salon+kuchnia+jadalnia':28s} {tot:8d}")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "trojkaty.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--widoki", default="przeglad,salon,zmierzch,obroty,trojkaty")
    ap.add_argument("--probki", type=int, default=40)
    ap.add_argument("--seed", type=int, default=4)
    ap.add_argument("--res", default="960x540")
    a = ap.parse_args()
    res = tuple(int(v) for v in a.res.split("x"))
    for v in a.widoki.split(","):
        if v == "przeglad":
            view_showroom(a.probki, a.seed, "przeglad", res)
        elif v == "salon":
            view_salon(False, a.probki, a.seed, "salon_dzien", res)
        elif v == "zmierzch":
            view_salon(True, a.probki, a.seed, "salon_zmierzch", res)
        elif v == "obroty":
            view_obroty(min(a.probki, 24), a.seed, "obroty")
        elif v == "trojkaty":
            triangles(a.seed)
        elif v.startswith("studio_"):
            k = v[7:]
            view_studio(k.replace("_noc", ""), a.probki, a.seed, v, res, dusk=k.endswith("_noc"))
        elif v.startswith("grupa_"):
            k = v[6:]
            view_group(k.replace("_noc", ""), a.probki, a.seed, v, res, dusk=k.endswith("_noc"))
