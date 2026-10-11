"""Scena filmowa w Blenderze: dom z bryla.py + realistyczne materiały, meble, rośliny, teren, niebo i światło.

Uruchamiane interpreterem z bpy (patrz film/render.py).
"""
import math
import random

import bpy
import bmesh
from mathutils import Vector

from silnik.bryla import build_mesh, Mesh, _glass_roof3d, ROSLINY, _item3d
from .kontekst import Ctx, zasob
from .materialy import material, lin



def _modul(name, funcs):
    """Moduł mebli / roślin, jeśli gotowy; OGRODY_FILM_PROSTE=1 wymusza proste bryły z bryla.py."""
    import importlib
    import os
    if os.environ.get("OGRODY_FILM_PROSTE"):
        return None
    try:
        m = importlib.import_module(f"film.{name}")
    except Exception:
        return None
    return m if all(hasattr(m, f) for f in funcs) else None


meble3d = _modul("meble3d", ("build_items",))
rosliny = _modul("rosliny", ("tree", "plant", "treeline"))

TREES = ("klon", "brzoza", "oliwka", "sosna", "palma", "lipa")


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


def _col(name, parent=None):
    c = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(c)
    return c


def mesh_from_tris(name, tris, ctx):
    """Siatka z listy trójkątów w układzie planu (scalanie wierzchołków, normalne na zewnątrz)."""
    verts, faces, idx = [], [], {}
    for tri in tris:
        f = []
        for (x, y, z) in tri:
            key = (round(x - ctx.ox, 4), round(-(y - ctx.oy), 4), round(z, 4))
            k = idx.get(key)
            if k is None:
                k = len(verts)
                idx[key] = k
                verts.append(key)
            f.append(k)
        if len(set(f)) == 3:
            faces.append(f)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    return me


def _objects(Mh, ctx, keep, col):
    obs = {}
    for (var, mat), tris in Mh.g.items():
        if var not in keep:
            continue
        me = mesh_from_tris(f"{mat}_{var}", tris, ctx)
        ob = bpy.data.objects.new(f"{mat}_{var}", me)
        col.objects.link(ob)
        me.materials.append(material(mat, ctx))
        obs[(var, mat)] = ob
    return obs


# --------------------------------------------------------------- dach w ruchu
def dach_ruch(H, t):
    """Trójkąty ruchomych części szklanych dachów w stanie t (0 zamknięty … 1 otwarty)."""
    M = Mesh()
    for g in [r for r in H.all_rooms if r.kind == "ogrod"]:
        _glass_roof3d(M, H, g, t)
    return {k: v for k, v in M.g.items() if k[0] == "ruch"}


def ustaw_dach(S, t):
    """Podmienia siatki ruchomego dachu (animacja klatka po klatce)."""
    ctx = S["ctx"]
    groups = dach_ruch(S["H"], t)
    for key, ob in list(S["ruch"].items()):
        old = ob.data
        tris = groups.get(key, [])
        ob.data = mesh_from_tris(old.name, tris, ctx)
        ob.data.materials.append(material(key[1], ctx))
        bpy.data.meshes.remove(old)


# --------------------------------------------------------------- detale architektury
def detale(H, ctx, col, snieg=False):
    """Obróbki attyk, parapety zewnętrzne pod oknami, opaska żwirowa wokół domu."""
    from shapely.geometry import LineString
    M = Mesh()
    for z, poly, fin, li in H.roofs:
        ring = poly.buffer(0.025, join_style="mitre").difference(poly.buffer(-0.275, join_style="mitre"))
        M.extrude(ring, z + 0.45, z + 0.475, "obrobka")
    for idx, L in H.L.items():
        for o in L["openings"]:
            if o.kind not in ("win", "band") or o.run.other is not None or o.sill < 0.2:
                continue
            nx, ny = o.run.normal
            ax, ay = o.a
            bx, by = o.b
            ln = math.hypot(bx - ax, by - ay)
            if ln < 0.2:
                continue
            ux, uy = (bx - ax) / ln, (by - ay) / ln
            a2 = (ax - ux * 0.03, ay - uy * 0.03)
            b2 = (bx + ux * 0.03, by + uy * 0.03)
            off0, off1 = o.t / 2 - 0.03, o.t / 2 + 0.05
            pts = [(a2[0] + nx * off0, a2[1] + ny * off0), (b2[0] + nx * off0, b2[1] + ny * off0),
                   (b2[0] + nx * off1, b2[1] + ny * off1), (a2[0] + nx * off1, a2[1] + ny * off1)]
            from shapely.geometry import Polygon
            zf = o.z_floor + o.sill
            M.extrude(Polygon(pts), zf - 0.035, zf - 0.005, "obrobka")
    fp = H.footprint
    strip = fp.buffer(0.55, join_style="mitre").difference(fp.buffer(0.25, join_style="mitre"))
    paths = [s_["shape"] for s_ in H.site if s_["t"] == "path"]
    if paths:
        from shapely.ops import unary_union
        strip = strip.difference(unary_union(paths).buffer(0.05))
    M.extrude(strip, -0.32, -0.285, "snieg" if snieg else "zwir_dach", bottom=False)
    for (var, mat), tris in M.g.items():
        me = mesh_from_tris(f"detal_{mat}", tris, ctx)
        ob = bpy.data.objects.new(f"detal_{mat}", me)
        col.objects.link(ob)
        me.materials.append(material(mat, ctx))


# --------------------------------------------------------------- teren i horyzont
def teren(ctx, col, snow=False):
    bpy.ops.mesh.primitive_circle_add(vertices=128, radius=420, fill_type="NGON", location=(0, 0, -0.31))
    g = bpy.context.object
    for c in g.users_collection:
        c.objects.unlink(g)
    col.objects.link(g)
    g.name = "teren"
    g.data.materials.append(material("snieg" if snow else "trawa", ctx))
    # daleki las na horyzoncie: sylweta z pojedynczych koron drzew na łagodnych wzgórzach
    rnd = random.Random(ctx.seed * 7 + 3)
    n = 2400
    r0, r1, r2 = 150.0, 175.0, 900.0
    base = [rnd.uniform(2.5, 8.0) for _ in range(48)]
    for _ in range(2):
        base = [(base[i - 1] + 2 * base[i] + base[(i + 1) % 48]) / 4 for i in range(48)]
    hs = []
    for i in range(n):
        f = 48 * i / n
        k = int(f)
        t = f - k
        t = t * t * (3 - 2 * t)
        hs.append(base[k] * (1 - t) + base[(k + 1) % 48] * t)
    crown = [0.0] * n
    j = 0
    while j < n:
        w = rnd.randint(5, 14)            # szerokość korony w wierzchołkach (~0,4 m każdy)
        hc = rnd.uniform(1.0, 4.0) * (1.6 if rnd.random() < 0.12 else 1.0)
        sharp = rnd.uniform(0.35, 1.0)    # świerki ostrzejsze, liściaste okrągłe
        for q in range(w):
            u = (q + 0.5) / w * 2 - 1
            v = max(0.0, 1 - abs(u) ** (1.0 + sharp)) ** (0.5 + 0.5 * sharp)
            crown[(j + q) % n] = max(crown[(j + q) % n], hc * v + rnd.uniform(-0.15, 0.15))
        j += max(2, int(w * rnd.uniform(0.35, 0.8)))
    verts, faces = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        h = hs[i] + crown[i]
        hb = hs[i] * 0.8
        verts += [(ca * r0, sa * r0, -0.35), (ca * (r0 + 6), sa * (r0 + 6), hb * 0.55), (ca * r1, sa * r1, h),
                  (ca * r2, sa * r2, h * 1.5 + 30)]
    for i in range(n):
        j2 = (i + 1) % n
        for k in range(3):
            faces.append((i * 4 + k, j2 * 4 + k, j2 * 4 + k + 1, i * 4 + k + 1))
    me = bpy.data.meshes.new("horyzont")
    me.from_pydata(verts, [], faces)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.update()
    ob = bpy.data.objects.new("horyzont", me)
    col.objects.link(ob)
    me.materials.append(material("las_daleki", ctx))
    return g


# --------------------------------------------------------------- niebo i słońce
def niebo(sc, pora="dzien", az=205.0, el=None, hdri="rooitou_park_1k.hdr", strength=None):
    """az – azymut słońca w stopniach od północy (+Y Blendera) zgodnie z ruchem wskazówek zegara."""
    w = bpy.data.worlds.new("swiat")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    if el is None:
        el = {"dzien": 36.0, "zmierzch": -1.5, "zima": 14.0}[pora]
    sky.sun_disc = False
    sky.sun_elevation = math.radians(max(el, -4.0))
    sky.sun_rotation = math.radians(az)
    sky.aerosol_density = 1.6 if pora != "zima" else 3.0
    sky.air_density = 1.0
    s = strength if strength is not None else {"dzien": 0.30, "zmierzch": 0.55, "zima": 0.42}[pora]
    # odbicia w szkle: zdjęcie HDRI (prawdziwe drzewa i chmury), w kamerze i oświetleniu – niebo Nishita
    out = sky.outputs["Color"]
    if hdri and pora == "dzien":
        env = nt.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(zasob("hdri/" + hdri), check_existing=True)
        mp = nt.nodes.new("ShaderNodeMapping")
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp.inputs["Rotation"].default_value = (0, 0, math.radians(90 - az))
        nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
        nt.links.new(mp.outputs[0], env.inputs["Vector"])
        lp = nt.nodes.new("ShaderNodeLightPath")
        mul = nt.nodes.new("ShaderNodeMix")
        mul.data_type = "RGBA"
        mul.blend_type = "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        nt.links.new(env.outputs["Color"], mul.inputs[6])
        mul.inputs[7].default_value = (0.55, 0.55, 0.55, 1.0)
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        nt.links.new(lp.outputs["Is Glossy Ray"], mx.inputs["Factor"])
        nt.links.new(sky.outputs["Color"], mx.inputs[6])
        nt.links.new(mul.outputs[2], mx.inputs[7])
        out = mx.outputs[2]
    nt.links.new(out, bg.inputs["Color"])
    bg.inputs["Strength"].default_value = s
    sun = bpy.data.lights.new("slonce", "SUN")
    if pora == "dzien":
        sun.energy, sun.color = 3.4, (1.0, 0.95, 0.88)
    elif pora == "zima":
        sun.energy, sun.color = 2.2, (1.0, 0.9, 0.78)
    else:
        sun.energy, sun.color = 0.0, (1.0, 0.6, 0.35)
    sun.angle = math.radians(1.2)
    so = bpy.data.objects.new("slonce", sun)
    sc.collection.objects.link(so)
    # az – azymut słońca od północy zgodnie z ruchem wskazówek (jak w niebie); lampa ma odwrotną konwencję
    so.rotation_euler = (math.radians(90 - max(el, 1.0)), 0, math.radians(180 - az))
    return so


# --------------------------------------------------------------- światła wieczorne
def swiatla_wieczor(H, Mh, ctx, col):
    """Wpuszczane oczka w sufitach (ciepłe 2700 K), podświetlenie drzew w ogrodzie."""
    warm = (1.0, 0.72, 0.46)
    me_disc = None
    discs = []
    for poly, z, kind in Mh.lights:
        minx, miny, maxx, maxy = poly.bounds
        nx = max(1, int((maxx - minx) / 1.7 + 0.5))
        ny = max(1, int((maxy - miny) / 1.7 + 0.5))
        for i in range(nx):
            for j in range(ny):
                x = minx + (maxx - minx) * (i + 0.5) / nx
                y = miny + (maxy - miny) * (j + 0.5) / ny
                from shapely.geometry import Point
                if not poly.buffer(0.3).contains(Point(x, y)):
                    continue
                li = bpy.data.lights.new("oczko", "SPOT")
                li.energy = 34.0
                li.color = warm
                li.spot_size = math.radians(115)
                li.spot_blend = 0.7
                li.shadow_soft_size = 0.04
                lo = bpy.data.objects.new("oczko", li)
                col.objects.link(lo)
                lo.location = ctx.to_bl(x, y, z - 0.03)
                discs.append(ctx.to_bl(x, y, z - 0.012))
    if discs:
        verts, faces = [], []
        for (X, Y, Z) in discs:
            k = len(verts)
            for i in range(8):
                a = 2 * math.pi * i / 8
                verts.append((X + 0.045 * math.cos(a), Y + 0.045 * math.sin(a), Z))
            faces.append(tuple(range(k, k + 8))[::-1])
        me_disc = bpy.data.meshes.new("oczka")
        me_disc.from_pydata(verts, [], faces)
        ob = bpy.data.objects.new("oczka", me_disc)
        col.objects.link(ob)
        me_disc.materials.append(material("lampa", ctx))
    # ogród: podświetlenie drzew od dołu
    for g in [r for r in H.all_rooms if r.kind == "ogrod"]:
        lay = getattr(g, "_layout", None)
        for ft in (lay["features"] if lay else []):
            if ft.t in TREES + ("cytrus",):
                li = bpy.data.lights.new("drzewo", "SPOT")
                li.energy = 90.0
                li.color = (1.0, 0.82, 0.6)
                li.spot_size = math.radians(60)
                li.spot_blend = 0.8
                li.shadow_soft_size = 0.05
                lo = bpy.data.objects.new("drzewo", li)
                col.objects.link(lo)
                lo.location = ctx.to_bl(ft.x + 0.45, ft.y + 0.45, g.z0 - 0.05)
                lo.rotation_euler = (math.radians(-12), math.radians(-12), 0)


# --------------------------------------------------------------- rośliny
def _rosliny(H, ctx, col):
    if rosliny is None:
        return
    for s_ in H.site:
        if s_["t"] == "tree":
            X, Y, Z = ctx.to_bl(s_["x"], s_["y"], -0.31)
            rosliny.tree(s_["kind"], X, Y, Z, s_.get("h") or 7.5, s_.get("r") or 2.0, int(s_["x"] * 13 + s_["y"]), ctx)
    gctx = Ctx(ctx.ox, ctx.oy, ctx.col, ctx.seed, ctx.dusk, "lato", H)   # pod szkłem zawsze lato
    gctx.cache = ctx.cache
    for g in [r for r in H.all_rooms if r.kind == "ogrod"]:
        lay = getattr(g, "_layout", None)
        if not lay:
            continue
        z = g.z0 - 0.12
        for ft in lay["features"]:
            if ft.t not in ROSLINY:
                continue
            sd = int(ft.x * 100 + ft.y * 10)
            X, Y, Z = ctx.to_bl(ft.x, ft.y, z)
            if ft.t in TREES:
                hmax = g.roof_z - z - 0.45
                h = max(1.6, min(ft.kw.get("h", 3.5), hmax))
                rosliny.tree(ft.t, X, Y, Z, h, max(0.6, min(ft.r, hmax * 0.4)), sd, gctx)
            elif ft.t == "cytrus":
                rosliny.tree("cytrus", X, Y, Z, 2.2, 0.6, sd, gctx)
            else:
                Zp = Z - 0.11 if ft.t == "lilia" else Z
                rosliny.plant(ft.t, X, Y, Zp, ft.r, sd, gctx, rot=getattr(ft, "rot", 0.0) or 0.0)


def _treeline(H, ctx, col, cams):
    if rosliny is None:
        return
    minx, miny, maxx, maxy = H.bbox
    R = 0.5 * math.hypot(maxx - minx, maxy - miny)

    def exclude(X, Y):
        p = Vector((X, Y))
        for (loc, tgt) in cams:
            a = Vector(loc[:2])
            b = Vector(tgt[:2])
            ab = b - a
            t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.length_squared, 1e-6)))
            if (a + ab * t - p).length < 9.0:
                return True
        return False
    rosliny.treeline(0.0, 0.0, R + 26.0, R + 95.0, 110, ctx.seed + 11, ctx, exclude=exclude)


# --------------------------------------------------------------- scena
def zbuduj(H, wariant="lato", pora="dzien", snieg=False, dach_t=None, kamery=(), seed=0, az=205.0):
    """wariant: lato (dach otwarty, harmonijki złożone) | zima (zamknięte); pora: dzien | zmierzch | zima;
    dach_t – dach w ruchu (animacja; zwraca obiekty "ruch" do podmiany)."""
    reset()
    sc = bpy.context.scene
    minx, miny, maxx, maxy = H.bbox
    ox, oy = (minx + maxx) / 2, (miny + maxy) / 2
    root = _col("dom")
    ctx = Ctx(ox, oy, root, seed=seed, dusk=(pora == "zmierzch"), season="zima" if snieg else "lato", house=H)
    Mh = build_mesh(H, meble=meble3d is None, rosliny=rosliny is None, ludzie=False, dach_t=dach_t)
    keep = {"base", wariant}
    if dach_t is not None:
        keep.add("ruch")
    if snieg:
        for k in list(Mh.g):
            if k[1] in ("sedum", "zwir_dach", "deck", "sciezka"):
                Mh.g.setdefault((k[0], "snieg"), []).extend(Mh.g.pop(k))
    obs = _objects(Mh, ctx, keep, root)
    if meble3d is not None:
        items = []
        for idx, L in H.L.items():
            items += L.get("items") or []
        mc = _col("meble")
        mctx = Ctx(ox, oy, mc, seed=seed, dusk=ctx.dusk, season=ctx.season, house=H)
        mctx.cache = ctx.cache
        meble3d.build_items(items, mctx)
    vc = _col("rosliny")
    vctx = Ctx(ox, oy, vc, seed=seed, dusk=ctx.dusk, season=ctx.season, house=H)
    vctx.cache = ctx.cache
    _rosliny(H, vctx, vc)
    _treeline(H, vctx, vc, kamery)
    detale(H, ctx, _col("detale"), snieg)
    teren(ctx, _col("teren"), snow=snieg)
    sun = niebo(sc, pora, az=az)
    if pora == "zmierzch":
        swiatla_wieczor(H, Mh, ctx, _col("swiatla"))
    S = dict(H=H, ctx=ctx, Mh=Mh, sc=sc, obs=obs, sun=sun,
             ruch={k: o for k, o in obs.items() if k[0] == "ruch"})
    return S


# --------------------------------------------------------------- kamera i render
def kamera(sc, loc, target, lens=24.0, shift_y=0.0, poziom=False, name="kam"):
    """poziom=True – kamera pozioma (pionowe krawędzie pionowe), kadr przesuwany shiftem jak w aparacie architektonicznym."""
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.sensor_width = 36
    cam.clip_start = 0.05
    cam.clip_end = 2000
    co = bpy.data.objects.new(name, cam)
    sc.collection.objects.link(co)
    co.location = loc
    d = Vector(target) - Vector(loc)
    if poziom:
        d.z = 0
        cam.shift_y = shift_y
    co.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    return co


def ustaw_render(sc, res=(1920, 1080), samples=96, ekspozycja=0.0, look="AgX - Medium High Contrast",
                 noise=0.02, persistent=False):
    sc.render.engine = "CYCLES"
    cy = sc.cycles
    cy.device = "CPU"
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = noise
    cy.adaptive_min_samples = min(16, samples)
    cy.use_denoising = True
    try:
        cy.denoiser = "OPENIMAGEDENOISE"
        cy.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        cy.denoising_prefilter = "ACCURATE"
    except Exception:
        pass
    cy.max_bounces = 8
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 3
    cy.transmission_bounces = 8
    cy.transparent_max_bounces = 24
    cy.volume_bounces = 0
    cy.sample_clamp_indirect = 6.0
    cy.blur_glossy = 1.0
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    try:
        cy.use_light_tree = True
    except Exception:
        pass
    sc.render.use_persistent_data = persistent
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.view_settings.view_transform = "AgX"
    try:
        sc.view_settings.look = look
    except Exception:
        pass
    sc.view_settings.exposure = ekspozycja
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.color_depth = "8"
    sc.render.film_transparent = False
