"""Test roślinności (film/rosliny.py): cztery ujęcia + statystyki.

  /home/user/tools/bpyenv/bin/python film/test_rosliny.py                 # wszystkie ujęcia
  /home/user/tools/bpyenv/bin/python film/test_rosliny.py --tylko a,c --probki 24 --szer 640

a – drzewa latem (wszystkie gatunki, skrzynka 1,8 m jako człowiek), b – te same zimą,
c – rośliny z bliska na wysokości oczu (dziedziniec japońsko-śródziemnomorski),
d – pierścień drzew w tle z 40 m (+ 30 drzew szczegółowych wokół domu; mierzy czas budowy).
Wyniki: out/film/test_rosliny/*.jpg i statystyki.txt
"""
import argparse
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

from film.kontekst import Ctx  # noqa: E402
from film import rosliny as R  # noqa: E402

OUT = os.path.join(HERE, "out", "film", "test_rosliny")
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    LOG.append(s)


def lin(c):
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c) + (1.0,)


# ------------------------------------------------------------------ scena
def nowa_scena():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def mat_laka():
    """Łąka: dwie skale szumu (plamy + drobna faktura) i wypukłość."""
    m = bpy.data.materials.new("laka")
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 0.08
    n1.inputs["Detail"].default_value = 4
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 3.0
    n2.inputs["Detail"].default_value = 8
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "FLOAT"
    mx.inputs["Factor"].default_value = 0.45
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].position, cr.color_ramp.elements[0].color = 0.3, lin((0.20, 0.27, 0.10))
    cr.color_ramp.elements[1].position, cr.color_ramp.elements[1].color = 0.7, lin((0.36, 0.40, 0.18))
    e = cr.color_ramp.elements.new(0.5)
    e.color = lin((0.27, 0.34, 0.13))
    for a, b in ((tc.outputs["Object"], n1.inputs["Vector"]), (tc.outputs["Object"], n2.inputs["Vector"]),
                 (n1.outputs["Fac"], mx.inputs["A"]), (n2.outputs["Fac"], mx.inputs["B"]),
                 (mx.outputs["Result"], cr.inputs["Fac"]), (cr.outputs["Color"], bs.inputs["Base Color"])):
        nt.links.new(a, b)
    nf = nt.nodes.new("ShaderNodeTexNoise")
    nf.inputs["Scale"].default_value = 80
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    nt.links.new(tc.outputs["Object"], nf.inputs["Vector"])
    nt.links.new(nf.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Roughness"].default_value = 0.95
    return m


def mat_prosty(name, col, rough=0.8, noise=0.0, scale=4.0, metal=0.0):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal
    if noise:
        tc = nt.nodes.new("ShaderNodeTexCoord")
        ns = nt.nodes.new("ShaderNodeTexNoise")
        ns.inputs["Scale"].default_value = scale
        ns.inputs["Detail"].default_value = 8
        cr = nt.nodes.new("ShaderNodeValToRGB")
        cr.color_ramp.elements[0].color = lin(tuple(max(0, c - noise) for c in col))
        cr.color_ramp.elements[1].color = lin(tuple(min(1, c + noise) for c in col))
        nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
        nt.links.new(ns.outputs["Fac"], cr.inputs["Fac"])
        nt.links.new(cr.outputs["Color"], bs.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.3
        nt.links.new(ns.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    else:
        bs.inputs["Base Color"].default_value = lin(col)
    return m


def mat_woda():
    m = bpy.data.materials.new("woda")
    nt = m.node_tree
    bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = lin((0.05, 0.09, 0.08))
    bs.inputs["Roughness"].default_value = 0.03
    bs.inputs["Specular IOR Level"].default_value = 0.8
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ns = nt.nodes.new("ShaderNodeTexNoise")
    ns.inputs["Scale"].default_value = 6.0
    ns.inputs["Detail"].default_value = 4
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.05
    nt.links.new(tc.outputs["Object"], ns.inputs["Vector"])
    nt.links.new(ns.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bs.inputs["Normal"])
    return m


def ziemia(sc, size=600, z=0.0, mat=None):
    me = bpy.data.meshes.new("ziemia")
    h = size / 2
    me.from_pydata([(-h, -h, z), (h, -h, z), (h, h, z), (-h, h, z)], [], [(0, 1, 2, 3)])
    ob = bpy.data.objects.new("ziemia", me)
    me.materials.append(mat or mat_laka())
    sc.collection.objects.link(ob)
    return ob


def skrzynka(sc, x, y, z, w, d, h, mat, name="skrzynka", rot=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + h / 2))
    ob = bpy.context.object
    ob.name = name
    ob.scale = (w, d, h)
    ob.rotation_euler = (0, 0, rot)
    ob.data.materials.append(mat)
    return ob


def czlowiek(sc, x, y, z=0.0):
    """Wzorzec skali: skrzynka 1,8 m (0,45 × 0,25)."""
    return skrzynka(sc, x, y, z, 0.45, 0.25, 1.8, mat_prosty("czlowiek", (0.62, 0.30, 0.24), 0.7), "czlowiek_1_8m")


def niebo(sc, elev=35.0, azim=200.0, strength=0.3, sun=3.2):
    w = bpy.data.worlds.new("niebo")
    sc.world = w
    nt = w.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    for t in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "NISHITA"):
        try:
            sky.sky_type = t
            break
        except TypeError:
            continue
    sky.sun_disc = False
    sky.sun_elevation = math.radians(elev)
    sky.sun_rotation = math.radians(azim)
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = strength
    li = bpy.data.lights.new("slonce", "SUN")
    li.energy = sun
    li.color = (1.0, 0.96, 0.9)
    li.angle = math.radians(1.2)
    so = bpy.data.objects.new("slonce", li)
    sc.collection.objects.link(so)
    # kierunek światła zgodny z położeniem słońca na niebie
    az = math.radians(azim)
    d = Vector((math.sin(az) * math.cos(math.radians(elev)), math.cos(az) * math.cos(math.radians(elev)), math.sin(math.radians(elev))))
    so.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()


def kamera(sc, loc, tgt, lens):
    cam = bpy.data.cameras.new("kamera")
    cam.lens = lens
    cam.sensor_width = 36
    co = bpy.data.objects.new("kamera", cam)
    sc.collection.objects.link(co)
    co.location = loc
    co.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    return co


def render(sc, name, args, exposure=-0.25):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = args.probki
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
    sc.cycles.transparent_max_bounces = 16
    sc.cycles.caustics_reflective = False
    sc.cycles.caustics_refractive = False
    sc.render.resolution_x = args.szer
    sc.render.resolution_y = int(args.szer * 9 / 16)
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    sc.view_settings.exposure = exposure
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 90
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, name + ".jpg")
    sc.render.filepath = fn
    from render_blender import _slot
    lock = _slot(2)   # wspólne gniazda renderu (CPU dzielony z innymi)
    t = time.time()
    bpy.ops.render.render(write_still=True)
    lock.close()
    log(f"render {name}: {time.time() - t:.1f} s → {fn}")


def tris(obs):
    seen, n = set(), 0
    for ob in obs:
        if ob.type == "MESH" and ob.data.name not in seen:
            seen.add(ob.data.name)
            n += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    return n


# ------------------------------------------------------------------ ujęcia
TYLNY = (("lipa", 12.0, 4.5), ("klon_zielony", 10.0, 3.8), ("brzoza", 11.0, 3.0), ("sosna", 13.0, 3.6))
PRZEDNI = (("cytrus", 2.2, 0.45), ("klon", 3.6, 1.4), ("sosna", 2.4, 0.9), ("oliwka", 4.0, 1.6), ("palma", 5.5, 1.4))


def drzewa(args, pora):
    sc = nowa_scena()
    ctx = Ctx(season=pora, seed=1)
    ziemia(sc)
    niebo(sc)
    obs = []
    # tylny rząd: duże drzewa działki; przedni: ogrodowe, ustawione w przerwach tylnego
    xb = (-12.5, -2.6, 6.2, 14.2)
    xf = (-10.4, -7.2, -4.0, 2.0, 10.4)
    for row, xs, y in ((TYLNY, xb, 9.0), (PRZEDNI, xf, -3.5)):
        for i, ((k, h, r), x) in enumerate(zip(row, xs)):
            t = time.time()
            o = R.tree(k, x, y, 0.0, h, r, 11 + i * 7 + (y > 0) * 3, ctx)
            log(f"{pora} {k:12s} h={h:5.1f} r={r:4.2f}  trójkąty={tris(o):7d}  budowa={time.time() - t:5.2f} s")
            obs += o
    for x, y in ((-12.0, -3.2), (-1.0, -2.4), (6.4, -3.0)):
        czlowiek(sc, x, y)
    kamera(sc, (0.0, -21.5, 2.0), (0.0, 1.5, 4.6), 26)
    render(sc, f"drzewa_{pora}", args)


def dziedziniec(args):
    """Dziedziniec: staw z grzybieniami, mech z klonem, kamienie, paprocie, lawendy, trawy, donice, cytrusy, monstery."""
    sc = nowa_scena()
    ctx = Ctx(season="lato", seed=2)
    zwir = mat_prosty("zwir", (0.74, 0.72, 0.68), 0.95, 0.06, 60.0)
    ziemia(sc, 80, 0.0, zwir)
    plyty = mat_prosty("plyty", (0.78, 0.74, 0.67), 0.7, 0.05, 3.0)
    tynk = mat_prosty("tynk", (0.92, 0.91, 0.88), 0.85, 0.03, 2.0)
    kam = mat_prosty("obrzeze", (0.42, 0.41, 0.39), 0.8, 0.08, 6.0)
    niebo(sc, 35, 215)
    # ściany dziedzińca
    skrzynka(sc, 0, 4.2, 0, 12, 0.3, 3.2, tynk, "sciana_n")
    skrzynka(sc, -5.6, 0.5, 0, 0.3, 7.5, 3.2, tynk, "sciana_w")
    # staw: woda 12 cm poniżej, kamienne obrzeże
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=1.0, depth=0.02, location=(1.6, 1.4, 0.01))
    st = bpy.context.object
    st.scale = (1.7, 1.0, 1.0)
    st.data.materials.append(mat_woda())
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.09, location=(1.6, 1.4, 0.03))
    ob = bpy.context.object
    ob.scale = (1.7, 1.0, 1.0)
    ob.data.materials.append(kam)
    # ścieżka z płyt
    for i in range(6):
        skrzynka(sc, -1.2 + 0.25 * i, -2.6 + 0.75 * i, -0.02, 0.6, 0.45, 0.05, plyty, f"plyta{i}", rot=0.3)
    obs = []
    t0 = time.time()
    obs += R.plant("lilia", 1.0, 1.2, 0.02, 0.3, 1, ctx)
    obs += R.plant("lilia", 2.3, 1.7, 0.02, 0.24, 2, ctx)
    obs += R.plant("mech", -2.6, 1.6, 0.0, 1.1, 3, ctx)
    obs += R.tree("klon", -2.7, 1.8, 0.05, 3.4, 1.3, 4, ctx)
    obs += R.plant("kamien", -1.5, 0.9, 0.0, 0.38, 5, ctx, rot=0.6)
    obs += R.plant("kamien", -3.4, 0.5, 0.0, 0.26, 6, ctx, rot=2.0)
    obs += R.plant("kamien", 3.4, 0.4, 0.0, 0.3, 7, ctx, rot=1.1)
    for i, (x, y) in enumerate(((-0.2, 2.8), (-1.0, 3.2), (3.3, 2.7), (-1.9, -0.2))):
        obs += R.plant("paproc", x, y, 0.0, 0.4, 10 + i, ctx)
    for i in range(4):
        obs += R.plant("lawenda", -4.6 + 0.62 * i, -1.7 + 0.18 * i, 0.0, 0.3, 20 + i, ctx)
    obs += R.plant("monstera", 4.3, 2.6, 0.0, 0.55, 30, ctx)
    obs += R.plant("trawa", 3.6, -0.9, 0.0, 0.32, 31, ctx)
    obs += R.plant("trawa", 4.4, -0.2, 0.0, 0.28, 32, ctx)
    obs += R.plant("donica", -4.6, 3.3, 0.0, 0.34, 40, ctx)
    obs += R.plant("donica", 0.9, -1.5, 0.0, 0.3, 41, ctx)
    obs += R.tree("cytrus", 2.4, -1.9, 0.0, 2.2, 0.45, 42, ctx)
    obs += R.tree("cytrus", -0.5, 3.4, 0.0, 2.0, 0.42, 43, ctx)
    obs += R.plant("bambus", 5.0, 3.6, 0.0, 0.5, 44, ctx)
    trawnik = [(-2.6, -4.2), (0.7, -4.2), (0.5, -2.2), (-2.8, -1.9)]
    me = bpy.data.meshes.new("trawnik")
    me.from_pydata([(x, y, 0.004) for x, y in trawnik], [], [(0, 1, 2, 3)])
    tr_ob = bpy.data.objects.new("trawnik", me)
    me.materials.append(mat_laka())
    sc.collection.objects.link(tr_ob)
    obs += R.lawn_tufts(trawnik, 160, 50, ctx, z=0.0, height=0.12)
    log(f"dziedziniec: budowa {time.time() - t0:.2f} s, trójkąty (unikalne siatki) {tris(obs)}")
    czlowiek(sc, -4.9, 2.2)
    kamera(sc, (0.4, -6.4, 1.6), (0.2, 1.2, 0.75), 28)
    render(sc, "rosliny_blisko", args, exposure=-0.15)


def szpaler(args, pora="lato"):
    """Dom (bryła) + 30 drzew szczegółowych na działce + pierścień 100 drzew w tle, widok z 40 m."""
    sc = nowa_scena()
    ctx = Ctx(season=pora, seed=3)
    ziemia(sc, 900)
    niebo(sc, 35, 200)
    skrzynka(sc, 0, 0, 0, 18, 13, 6.5, mat_prosty("dom", (0.9, 0.89, 0.86), 0.8), "dom")
    skrzynka(sc, -3, 0, 6.5, 8, 9, 0.4, mat_prosty("dach", (0.3, 0.32, 0.28), 0.9), "dach")
    import random
    rnd = random.Random(5)
    t0 = time.time()
    obs = []
    kinds = ("lipa", "klon_zielony", "brzoza", "sosna", "klon", "oliwka")
    placed = []
    while len(placed) < 30:
        a = rnd.uniform(0, 2 * math.pi)
        d = rnd.uniform(14, 30)
        x, y = math.cos(a) * d, math.sin(a) * d
        if abs(x) < 13 and abs(y) < 10.5:
            continue
        if any(math.hypot(x - p[0], y - p[1]) < 4.5 for p in placed):
            continue
        placed.append((x, y))
        k = kinds[len(placed) % len(kinds)]
        h = {"lipa": 11, "klon_zielony": 9, "brzoza": 11, "sosna": 13, "klon": 4.5, "oliwka": 4.5}[k] * rnd.uniform(0.85, 1.15)
        r = h * {"lipa": 0.36, "klon_zielony": 0.38, "brzoza": 0.26, "sosna": 0.26, "klon": 0.4, "oliwka": 0.4}[k]
        obs += R.tree(k, x, y, 0.0, h, r, 100 + len(placed), ctx)
    t1 = time.time()
    obs += R.treeline(0, 0, 38, 75, 100, 9, ctx, exclude=lambda x, y: y < -28 and abs(x) < 0.75 * (-y), z=0.0)
    t2 = time.time()
    log(f"szpaler {pora}: 30 drzew szczegółowych {t1 - t0:.2f} s, 100 drzew w tle {t2 - t1:.2f} s, razem {t2 - t0:.2f} s, "
        f"obiektów {len(obs)}, unikalnych siatek {len(set(o.data.name for o in obs))}, trójkąty unikalnych {tris(obs)}")
    kamera(sc, (0.0, -62.0, 40.0), (0.0, 8.0, 2.0), 28)
    render(sc, "szpaler_40m" + ("" if pora == "lato" else "_zima"), args)


def statystyki():
    """Trójkąty wariantów (blisko / daleko) – bez renderu."""
    for k, h, r in (("lipa", 12, 4.5), ("klon_zielony", 10, 3.8), ("brzoza", 11, 3.0), ("sosna", 13, 3.6),
                    ("klon", 3.6, 1.4), ("sosna", 2.4, 0.9), ("oliwka", 4.0, 1.6), ("palma", 5.5, 1.4), ("cytrus", 2.2, 0.45)):
        row = []
        for lod in ("blisko", "daleko"):
            for pora in ("lato", "zima"):
                t = time.time()
                G = R._build_palm(h, r, lod, 0) if k == "palma" else R._build_tree(k, h, r, lod, pora, 0)
                row.append(f"{lod}/{pora} {G.ntris():6d} ({time.time() - t:.2f} s)")
        log(f"{k:12s} h={h:4.1f}: " + "  ".join(row))
    for k, r in (("paproc", 0.38), ("lawenda", 0.3), ("monstera", 0.5), ("mech", 1.0), ("kamien", 0.35), ("lilia", 0.25),
                 ("trawa", 0.3), ("donica", 0.35), ("bambus", 0.5)):
        G = R.PLANTS[k](r, 0, "lato")
        log(f"{k:12s} r={r:4.2f}: {G.ntris():6d} trójkątów")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--tylko", default="a,b,c,d")
    ap.add_argument("--probki", type=int, default=48)
    ap.add_argument("--szer", type=int, default=960)
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    R._ensure_textures()
    statystyki()
    todo = args.tylko.split(",")
    if "a" in todo:
        drzewa(args, "lato")
    if "b" in todo:
        drzewa(args, "zima")
    if "c" in todo:
        dziedziniec(args)
    if "d" in todo:
        szpaler(args)
    if "dz" in todo:
        szpaler(args, "zima")
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "statystyki.txt"), "w") as f:
        f.write("\n".join(LOG) + "\n")
