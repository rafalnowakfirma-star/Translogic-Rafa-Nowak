"""Materiały PBR do filmów: elewacje, posadzki, teren, szkło, woda, śnieg.

Siatki domu nie mają UV – tekstury liczone są ze współrzędnych obiektu (obiekty mają środek w 0,0,0,
więc to współrzędne świata).  Na ścianach „u” biegnie wzdłuż ściany, „v” w górę; na poziomych powierzchniach (x, y).
"""
import bpy

from .kontekst import zasob


def lin(c):
    return tuple(max(0.0, x) ** 2.2 for x in c[:3]) + (1.0,)


class N:
    """Mały pomocnik do budowy drzewek węzłów."""

    def __init__(self, nt):
        self.nt = nt

    def node(self, kind, inputs=None, **props):
        n = self.nt.nodes.new(kind)
        for k, v in props.items():
            setattr(n, k, v)
        for k, v in (inputs or {}).items():
            self.set(n.inputs[k], v)
        return n

    def set(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            self.nt.links.new(v, sock)
        elif isinstance(v, bpy.types.Node):
            self.nt.links.new(v.outputs[0], sock)
        else:
            sock.default_value = v

    def math(self, op, a, b=0.0, clamp=False):
        n = self.node("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.set(n.inputs[0], a)
        self.set(n.inputs[1], b)
        return n.outputs[0]

    def mixf(self, f, a, b):
        n = self.node("ShaderNodeMix", data_type="FLOAT")
        self.set(n.inputs["Factor"], f)
        self.set(n.inputs["A"], a)
        self.set(n.inputs["B"], b)
        return n.outputs["Result"]

    def mixc(self, f, a, b, blend="MIX"):
        n = self.node("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        self.set(n.inputs["Factor"], f)
        self.set(n.inputs[6], a)
        self.set(n.inputs[7], b)
        return n.outputs[2]

    def ramp(self, fac, stops):
        n = self.node("ShaderNodeValToRGB")
        el = n.color_ramp.elements
        el[0].position, el[0].color = stops[0][0], lin(stops[0][1])
        el[1].position, el[1].color = stops[-1][0], lin(stops[-1][1])
        for p, c in stops[1:-1]:
            e = el.new(p)
            e.color = lin(c)
        self.set(n.inputs["Fac"], fac)
        return n.outputs["Color"]

    def noise(self, vec, scale, detail=4.0, rough=0.5, dist=0.0):
        n = self.node("ShaderNodeTexNoise", {"Scale": scale, "Detail": detail, "Roughness": rough, "Distortion": dist})
        self.set(n.inputs["Vector"], vec)
        return n

    def xyz(self, x, y, z=0.0):
        n = self.node("ShaderNodeCombineXYZ")
        self.set(n.inputs[0], x)
        self.set(n.inputs[1], y)
        self.set(n.inputs[2], z)
        return n.outputs[0]

    def sep(self, v):
        n = self.node("ShaderNodeSeparateXYZ")
        self.set(n.inputs[0], v)
        return n.outputs

    def vscale(self, v, s):
        n = self.node("ShaderNodeVectorMath", operation="MULTIPLY")
        self.set(n.inputs[0], v)
        n.inputs[1].default_value = s if isinstance(s, tuple) else (s, s, s)
        return n.outputs[0]

    def img(self, path, vec, non_color=False, interp="Linear"):
        im = bpy.data.images.load(path, check_existing=True)
        if non_color:
            im.colorspace_settings.name = "Non-Color"
        n = self.node("ShaderNodeTexImage", image=im, interpolation=interp)
        self.set(n.inputs["Vector"], vec)
        return n


def _new(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    return m, N(nt), b, nt.nodes["Material Output"]


def _coords(n):
    tc = n.node("ShaderNodeTexCoord")
    return tc.outputs["Object"]


def _wall_uv(n, su=1.0, sv=1.0):
    """Wektor (u, v): na ścianie u wzdłuż ściany, v = z; na poziomych powierzchniach (x, y)."""
    P = _coords(n)
    geo = n.node("ShaderNodeNewGeometry")
    nx, ny, nz = n.sep(geo.outputs["Normal"])
    px, py, pz = n.sep(P)
    ln = n.math("ADD", n.math("SQRT", n.math("ADD", n.math("MULTIPLY", nx, nx), n.math("MULTIPLY", ny, ny))), 1e-6)
    u = n.math("ADD", n.math("MULTIPLY", n.math("DIVIDE", n.math("MULTIPLY", ny, -1.0), ln), px),
               n.math("MULTIPLY", n.math("DIVIDE", nx, ln), py))
    hor = n.math("GREATER_THAN", n.math("ABSOLUTE", nz), 0.7)
    U = n.mixf(hor, u, px)
    V = n.mixf(hor, pz, py)
    return n.xyz(n.math("MULTIPLY", U, su), n.math("MULTIPLY", V, sv)), U, V


def _bump(n, b, height, strength, dist=0.02, normal=None):
    bp = n.node("ShaderNodeBump", {"Strength": strength, "Distance": dist})
    n.set(bp.inputs["Height"], height)
    if normal is not None:
        n.set(bp.inputs["Normal"], normal)
    n.set(b.inputs["Normal"], bp.outputs["Normal"])
    return bp


def _boards(n, U, V, width, gap, vertical=True):
    """Deski: (id deski, maska szczeliny, współrzędne słojów)."""
    a = U if vertical else V
    q = n.math("DIVIDE", a, width)
    bid = n.math("FLOOR", q)
    fr = n.math("FRACT", q)
    g = gap / width
    mask = n.math("MULTIPLY", n.math("GREATER_THAN", fr, g), n.math("LESS_THAN", fr, 1 - g * 0.3))
    rnd = n.node("ShaderNodeTexWhiteNoise", noise_dimensions="1D")
    n.set(rnd.inputs["W"], bid)
    return bid, mask, rnd.outputs["Value"]


# --------------------------------------------------------------- przepisy
def m_tynk(name, c=(0.86, 0.85, 0.81), var=0.035, r=0.88, bump=0.10):
    m, n, b, _ = _new(name)
    P = _coords(n)
    macro = n.noise(P, 0.35, 3).outputs["Fac"]
    col = n.ramp(macro, [(0.3, tuple(x - var for x in c)), (0.7, tuple(x + var * 0.5 for x in c))])
    n.set(b.inputs["Base Color"], col)
    b.inputs["Roughness"].default_value = r
    fine = n.noise(P, 55, 10, 0.65).outputs["Fac"]
    mid = n.noise(P, 7, 4).outputs["Fac"]
    _bump(n, b, n.math("ADD", fine, n.math("MULTIPLY", mid, 0.4)), bump, 0.004)
    return m


def m_beton(name, c=(0.60, 0.59, 0.56), var=0.07, r=0.82, polished=False):
    m, n, b, _ = _new(name)
    P = _coords(n)
    macro = n.noise(P, 0.6, 5, 0.6).outputs["Fac"]
    spots = n.noise(P, 4.0, 6, 0.7).outputs["Fac"]
    f = n.mixf(0.35, macro, spots)
    col = n.ramp(f, [(0.25, tuple(x - var for x in c)), (0.55, c), (0.8, tuple(x + var * 0.6 for x in c))])
    vor = n.node("ShaderNodeTexVoronoi", {"Scale": 260.0})
    n.set(vor.inputs["Vector"], P)
    pores = n.math("LESS_THAN", vor.outputs["Distance"], 0.06)
    col = n.mixc(n.math("MULTIPLY", pores, 0.35), col, (0.15, 0.15, 0.15, 1))
    n.set(b.inputs["Base Color"], col)
    if polished:
        n.set(b.inputs["Roughness"], n.math("ADD", 0.22, n.math("MULTIPLY", spots, 0.15)))
    else:
        b.inputs["Roughness"].default_value = r
    _bump(n, b, n.math("SUBTRACT", n.noise(P, 30, 8).outputs["Fac"], n.math("MULTIPLY", pores, 0.6)), 0.12, 0.003)
    return m


def m_deski(name, c=(0.55, 0.38, 0.22), var=0.14, width=0.13, gap=0.007, vertical=True, r=0.7,
            charred=False, floor=False):
    """Okładzina / deck z desek: losowy odcień deski, słoje wzdłuż deski, szczeliny."""
    m, n, b, _ = _new(name)
    vec, U, V = _wall_uv(n)
    bid, mask, rnd = _boards(n, U, V, width, gap, vertical)
    along = V if vertical else U
    across = U if vertical else V
    gv = n.xyz(n.math("MULTIPLY", across, 60.0), n.math("MULTIPLY", along, 2.2), n.math("MULTIPLY", rnd, 50.0))
    grain = n.noise(gv, 1.0, 6, 0.6, 2.5).outputs["Fac"]
    if charred:
        vv = n.xyz(n.math("MULTIPLY", across, 18.0), n.math("MULTIPLY", along, 9.0), rnd)
        vor = n.node("ShaderNodeTexVoronoi", {"Scale": 1.0}, feature="DISTANCE_TO_EDGE")
        n.set(vor.inputs["Vector"], vv)
        crack = n.math("LESS_THAN", vor.outputs["Distance"], 0.07)
        col = n.ramp(n.math("ADD", n.math("MULTIPLY", rnd, 0.5), n.math("MULTIPLY", grain, 0.5)),
                     [(0.0, (0.018, 0.017, 0.016)), (1.0, (0.06, 0.055, 0.05))])
        col = n.mixc(n.math("MULTIPLY", n.math("SUBTRACT", 1.0, mask), 0.9), col, (0.0, 0.0, 0.0, 1))
        n.set(b.inputs["Base Color"], col)
        n.set(b.inputs["Roughness"], n.math("ADD", 0.55, n.math("MULTIPLY", crack, 0.3)))
        b.inputs["Coat Weight"].default_value = 0.0
        _bump(n, b, n.math("SUBTRACT", n.math("MULTIPLY", mask, 1.0), n.math("MULTIPLY", crack, 0.7)), 0.6, 0.01)
        return m
    lo = tuple(max(0, x - var) for x in c)
    hi = tuple(min(1, x + var * 0.6) for x in c)
    tone = n.ramp(n.math("ADD", n.math("MULTIPLY", rnd, 0.75), n.math("MULTIPLY", grain, 0.25)), [(0.0, lo), (1.0, hi)])
    dark = n.mixc(n.math("MULTIPLY", n.math("SUBTRACT", 1.0, mask), 0.85), tone, (0.03, 0.025, 0.02, 1))
    streak = n.math("MULTIPLY", n.math("GREATER_THAN", grain, 0.62), 0.25)
    col = n.mixc(streak, dark, tuple(x * 0.7 for x in lin(c)[:3]) + (1,))
    n.set(b.inputs["Base Color"], col)
    n.set(b.inputs["Roughness"], n.math("ADD", r - 0.08, n.math("MULTIPLY", grain, 0.16)))
    _bump(n, b, n.math("ADD", mask, n.math("MULTIPLY", grain, 0.08)), 0.45 if not floor else 0.3, 0.01)
    return m


def m_parkiet(name, tint=(1.0, 0.93, 0.85), val=0.95, sat=0.72, scale=2.6):
    """Posadzka z desek – zdjęcie (three.js hardwood2) na (x, y), plank ~16 cm."""
    m, n, b, _ = _new(name)
    P = _coords(n)
    sx, sy, sz = n.sep(P)
    vec = n.xyz(n.math("DIVIDE", sx, scale), n.math("DIVIDE", sy, scale / 2))
    tx = n.img(zasob("tekstury/hardwood2_diffuse.jpg"), vec)
    hs = n.node("ShaderNodeHueSaturation", {"Saturation": sat, "Value": val})
    n.set(hs.inputs["Color"], tx.outputs["Color"])
    col = n.mixc(1.0, hs.outputs["Color"], tint + (1,), blend="MULTIPLY")
    n.set(b.inputs["Base Color"], col)
    rg = n.img(zasob("tekstury/hardwood2_roughness.jpg"), vec, non_color=True)
    n.set(b.inputs["Roughness"], n.math("ADD", 0.28, n.math("MULTIPLY", rg.outputs["Color"], 0.35)))
    bp = n.img(zasob("tekstury/hardwood2_bump.jpg"), vec, non_color=True)
    _bump(n, b, bp.outputs["Color"], 0.25, 0.004)
    b.inputs["Coat Weight"].default_value = 0.15
    b.inputs["Coat Roughness"].default_value = 0.2
    return m


def m_cegla(name, white=False, scale=1.9):
    m, n, b, _ = _new(name)
    vec, U, V = _wall_uv(n, 1 / scale, 1 / scale)
    if white:
        h = n.img(zasob("tekstury/brick_bump.jpg"), vec, non_color=True).outputs["Color"]
        P = _coords(n)
        nz = n.noise(P, 3.0, 5).outputs["Fac"]
        col = n.ramp(n.math("ADD", n.math("MULTIPLY", h, 0.85), n.math("MULTIPLY", nz, 0.15)),
                     [(0.2, (0.42, 0.41, 0.39)), (0.55, (0.80, 0.79, 0.76)), (1.0, (0.92, 0.91, 0.88))])
        n.set(b.inputs["Base Color"], col)
        b.inputs["Roughness"].default_value = 0.85
        _bump(n, b, h, 0.6, 0.01)
        return m
    tx = n.img(zasob("tekstury/brick_diffuse.jpg"), vec)
    hs = n.node("ShaderNodeHueSaturation", {"Saturation": 0.85, "Value": 0.82})
    n.set(hs.inputs["Color"], tx.outputs["Color"])
    n.set(b.inputs["Base Color"], hs.outputs["Color"])
    rg = n.img(zasob("tekstury/brick_roughness.jpg"), vec, non_color=True)
    n.set(b.inputs["Roughness"], n.math("ADD", 0.55, n.math("MULTIPLY", rg.outputs["Color"], 0.4)))
    h = n.img(zasob("tekstury/brick_bump.jpg"), vec, non_color=True).outputs["Color"]
    _bump(n, b, h, 0.7, 0.012)
    return m


def m_bloki(name, c, var=0.08, bw=0.9, bh=0.45, mortar=0.004, r=0.75, bands=False, pores=False, mortar_c=None,
            offset=0.5):
    """Okładzina z płyt / bloków (kamień, trawertyn, płyty chodnikowe) – tekstura cegły z dużymi elementami."""
    m, n, b, _ = _new(name)
    vec, U, V = _wall_uv(n)
    br = n.node("ShaderNodeTexBrick", {"Scale": 1.0, "Mortar Size": mortar, "Brick Width": bw, "Row Height": bh,
                                        "Mortar Smooth": 0.1, "Bias": 0.0},
                offset=offset, squash=1.0)
    n.set(br.inputs["Vector"], vec)
    br.inputs["Color1"].default_value = (1, 1, 1, 1)
    br.inputs["Color2"].default_value = (0, 0, 0, 1)
    br.inputs["Mortar"].default_value = (0, 0, 0, 1)
    per = br.outputs["Color"]   # losowy odcień płyty (0..1)
    P = _coords(n)
    nz = n.noise(P, 2.5, 6, 0.6).outputs["Fac"]
    f = n.math("ADD", n.math("MULTIPLY", n.sep(per)[0], 0.55), n.math("MULTIPLY", nz, 0.45))
    if bands:
        wv = n.node("ShaderNodeTexWave", {"Scale": 3.0, "Distortion": 6.0, "Detail": 3.0}, wave_type="BANDS",
                    bands_direction="Z")
        n.set(wv.inputs["Vector"], n.xyz(n.math("MULTIPLY", U, 0.15), n.math("MULTIPLY", U, 0.15), n.math("MULTIPLY", V, 1.0)))
        f = n.math("ADD", n.math("MULTIPLY", f, 0.7), n.math("MULTIPLY", wv.outputs["Fac"], 0.3))
    col = n.ramp(f, [(0.0, tuple(x - var for x in c)), (0.5, c), (1.0, tuple(min(1, x + var * 0.7) for x in c))])
    joint = br.outputs["Fac"]   # Fac = 1 w spoinie
    col = n.mixc(joint, col, lin(mortar_c or tuple(x * 0.72 for x in c)))
    if pores:
        vor = n.node("ShaderNodeTexVoronoi", {"Scale": 90.0})
        n.set(vor.inputs["Vector"], n.xyz(n.math("MULTIPLY", U, 1.0), n.math("MULTIPLY", V, 2.2), 0.0))
        pm = n.math("LESS_THAN", vor.outputs["Distance"], 0.08)
        col = n.mixc(n.math("MULTIPLY", pm, 0.55), col, lin(tuple(x * 0.62 for x in c)))
    n.set(b.inputs["Base Color"], col)
    n.set(b.inputs["Roughness"], n.math("ADD", r, n.math("MULTIPLY", joint, 0.15)))
    _bump(n, b, n.math("ADD", n.math("SUBTRACT", 1.0, joint), n.math("MULTIPLY", nz, 0.1)), 0.35, 0.01)
    return m


def m_blacha(name, c=(0.07, 0.072, 0.078), seam=0.45, metal=0.7, r=0.42, patina=False):
    """Blacha na rąbek stojący (pionowe rąbki co 45 cm); patina=True – miedź z zieloną patyną."""
    m, n, b, _ = _new(name)
    vec, U, V = _wall_uv(n)
    fr = n.math("FRACT", n.math("DIVIDE", U, seam))
    ridge = n.math("MULTIPLY", n.math("LESS_THAN", fr, 0.035), 1.0)
    P = _coords(n)
    nz = n.noise(P, 1.5, 5).outputs["Fac"]
    if patina:
        mask = n.ramp(n.math("ADD", nz, n.math("MULTIPLY", n.noise(P, 9, 6).outputs["Fac"], 0.35)),
                      [(0.38, (0, 0, 0)), (0.62, (1, 1, 1))])
        mm = n.sep(mask)[0]
        col = n.mixc(mm, lin((0.48, 0.27, 0.16)), lin((0.36, 0.58, 0.50)))
        n.set(b.inputs["Base Color"], col)
        n.set(b.inputs["Metallic"], n.math("SUBTRACT", 0.85, n.math("MULTIPLY", mm, 0.75)))
        n.set(b.inputs["Roughness"], n.math("ADD", 0.38, n.math("MULTIPLY", mm, 0.4)))
    else:
        col = n.ramp(nz, [(0.3, tuple(x * 0.85 for x in c)), (0.7, tuple(x * 1.15 for x in c))])
        n.set(b.inputs["Base Color"], col)
        b.inputs["Metallic"].default_value = metal
        n.set(b.inputs["Roughness"], n.math("ADD", r - 0.05, n.math("MULTIPLY", nz, 0.12)))
    _bump(n, b, ridge, 0.5, 0.02)
    return m


def m_corten(name):
    m, n, b, _ = _new(name)
    vec, U, V = _wall_uv(n)
    P = _coords(n)
    big = n.noise(P, 0.8, 6, 0.6).outputs["Fac"]
    small = n.noise(P, 14, 8, 0.7).outputs["Fac"]
    streak = n.noise(n.xyz(n.math("MULTIPLY", U, 6.0), n.math("MULTIPLY", V, 0.25)), 1.0, 4).outputs["Fac"]
    f = n.math("ADD", n.math("ADD", n.math("MULTIPLY", big, 0.45), n.math("MULTIPLY", small, 0.3)), n.math("MULTIPLY", streak, 0.25))
    col = n.ramp(f, [(0.2, (0.20, 0.08, 0.035)), (0.45, (0.36, 0.15, 0.06)), (0.65, (0.50, 0.22, 0.08)), (0.85, (0.58, 0.30, 0.12))])
    # spoiny płyt 1,0 × 2,8 m
    br = n.node("ShaderNodeTexBrick", {"Scale": 1.0, "Mortar Size": 0.004, "Brick Width": 1.0, "Row Height": 2.8}, offset=0.0)
    n.set(br.inputs["Vector"], vec)
    col = n.mixc(br.outputs["Fac"], col, lin((0.08, 0.04, 0.02)))
    n.set(b.inputs["Base Color"], col)
    n.set(b.inputs["Roughness"], n.math("ADD", 0.72, n.math("MULTIPLY", small, 0.2)))
    b.inputs["Metallic"].default_value = 0.15
    _bump(n, b, n.math("ADD", n.math("SUBTRACT", 1.0, br.outputs["Fac"]), n.math("MULTIPLY", small, 0.25)), 0.4, 0.01)
    return m


def m_trawa(name, scale=3.2, dry=0.0):
    """Trawnik: zdjęcie trawy w dwóch skalach mieszane szumem (bez widocznego kafelkowania) + plamy koloru."""
    m, n, b, _ = _new(name)
    P = _coords(n)
    px, py, pz = n.sep(P)
    v1 = n.xyz(n.math("DIVIDE", px, scale), n.math("DIVIDE", py, scale))
    v2 = n.xyz(n.math("DIVIDE", n.math("ADD", py, 17.3), scale * 1.37), n.math("DIVIDE", n.math("SUBTRACT", 3.1, px), scale * 1.37))
    t1 = n.img(zasob("tekstury/grasslight-big.jpg"), v1).outputs["Color"]
    t2 = n.img(zasob("tekstury/grasslight-big.jpg"), v2).outputs["Color"]
    mx = n.noise(P, 0.12, 3).outputs["Fac"]
    col = n.mixc(n.math("GREATER_THAN", mx, 0.5), t1, t2)
    col = n.mixc(0.5, col, n.mixc(0.5, t1, t2))
    hs = n.node("ShaderNodeHueSaturation", {"Hue": 0.5 - 0.035 - dry * 0.02, "Saturation": 0.72 - dry * 0.2, "Value": 0.62})
    n.set(hs.inputs["Color"], col)
    patch = n.noise(P, 0.05, 4).outputs["Fac"]
    tintc = n.ramp(patch, [(0.3, (0.82, 0.90, 0.62)), (0.7, (1.0, 0.96, 0.78))])
    col = n.mixc(1.0, hs.outputs["Color"], tintc, blend="MULTIPLY")
    n.set(b.inputs["Base Color"], col)
    b.inputs["Roughness"].default_value = 0.92
    b.inputs["Specular IOR Level"].default_value = 0.3
    _bump(n, b, n.sep(t1)[1], 0.35, 0.02)
    return m


def m_sedum(name):
    m, n, b, _ = _new(name)
    P = _coords(n)
    vor = n.node("ShaderNodeTexVoronoi", {"Scale": 38.0})
    n.set(vor.inputs["Vector"], P)
    cell = vor.outputs["Color"]
    big = n.noise(P, 0.45, 4).outputs["Fac"]
    f = n.math("ADD", n.math("MULTIPLY", n.sep(cell)[0], 0.55), n.math("MULTIPLY", big, 0.45))
    col = n.ramp(f, [(0.0, (0.17, 0.22, 0.08)), (0.35, (0.28, 0.34, 0.12)), (0.55, (0.38, 0.40, 0.15)),
                     (0.75, (0.50, 0.28, 0.16)), (1.0, (0.58, 0.48, 0.22))])
    n.set(b.inputs["Base Color"], col)
    b.inputs["Roughness"].default_value = 0.8
    _bump(n, b, n.math("SUBTRACT", 1.0, vor.outputs["Distance"]), 0.6, 0.01)
    return m


def m_zwir(name, c=(0.66, 0.64, 0.6), var=0.12, scale=70.0, rake=False):
    m, n, b, _ = _new(name)
    P = _coords(n)
    vor = n.node("ShaderNodeTexVoronoi", {"Scale": scale, "Randomness": 1.0})
    n.set(vor.inputs["Vector"], P)
    stone = n.sep(vor.outputs["Color"])[0]
    col = n.ramp(stone, [(0.0, tuple(x - var for x in c)), (0.5, c), (1.0, tuple(min(1, x + var * 0.5) for x in c))])
    h = n.math("SUBTRACT", 1.0, vor.outputs["Distance"])
    if rake:
        wv = n.node("ShaderNodeTexWave", {"Scale": 5.5, "Distortion": 0.4, "Detail": 1.0}, wave_type="BANDS",
                    bands_direction="X")
        n.set(wv.inputs["Vector"], P)
        h = n.math("ADD", n.math("MULTIPLY", h, 0.35), n.math("MULTIPLY", wv.outputs["Fac"], 1.0))
        col = n.mixc(n.math("MULTIPLY", n.math("SUBTRACT", 1.0, wv.outputs["Fac"]), 0.35), col, lin(tuple(x * 0.7 for x in c)))
    n.set(b.inputs["Base Color"], col)
    b.inputs["Roughness"].default_value = 0.9
    _bump(n, b, h, 0.7, 0.015)
    return m


def m_szklo(name, tint=(0.90, 0.96, 0.95)):
    """Szkło architektoniczne: w kamerze i odbiciach szkło (Fresnel), dla cieni i światła rozproszonego przezroczyste."""
    m, n, b, out = _new(name)
    nt = m.node_tree
    nt.nodes.remove(b)
    glass = n.node("ShaderNodeBsdfGlass", {"Color": lin(tint), "Roughness": 0.0, "IOR": 1.5})
    tr = n.node("ShaderNodeBsdfTransparent", {"Color": lin(tint)})
    lp = n.node("ShaderNodeLightPath")
    f = n.math("MAXIMUM", lp.outputs["Is Shadow Ray"], lp.outputs["Is Diffuse Ray"])
    mix = n.node("ShaderNodeMixShader")
    n.set(mix.inputs["Fac"], f)
    n.set(mix.inputs[1], glass.outputs[0])
    n.set(mix.inputs[2], tr.outputs[0])
    n.set(out.inputs["Surface"], mix.outputs[0])
    return m


def m_woda(name):
    m, n, b, _ = _new(name)
    P = _coords(n)
    px, py, pz = n.sep(P)
    vec = n.xyz(n.math("DIVIDE", px, 2.2), n.math("DIVIDE", py, 2.2))
    nm = n.img(zasob("tekstury/waternormals.jpg"), vec, non_color=True)
    nmap = n.node("ShaderNodeNormalMap", {"Strength": 0.25})
    n.set(nmap.inputs["Color"], nm.outputs["Color"])
    n.set(b.inputs["Normal"], nmap.outputs["Normal"])
    b.inputs["Base Color"].default_value = lin((0.035, 0.07, 0.065))
    b.inputs["Roughness"].default_value = 0.03
    b.inputs["IOR"].default_value = 1.33
    b.inputs["Specular IOR Level"].default_value = 0.6
    return m


def m_wodospad(name):
    """Tafla wody spływającej po kamieniu: smugi wydłużone w pionie, jasna piana, częściowa przejrzystość."""
    m, n, b, _ = _new(name)
    P = _coords(n)
    px, py, pz = n.sep(P)
    vec = n.xyz(n.math("MULTIPLY", px, 9.0), n.math("MULTIPLY", py, 9.0), n.math("MULTIPLY", pz, 0.6))
    nz = n.noise(vec, 2.5, 6.0, 0.62).outputs["Fac"]
    smugi = n.ramp(nz, [(0.35, (0.36, 0.48, 0.50)), (0.62, (0.80, 0.88, 0.90)), (0.78, (0.97, 0.98, 0.98))])
    n.set(b.inputs["Base Color"], smugi)
    n.set(b.inputs["Roughness"], n.math("ADD", 0.04, n.math("MULTIPLY", nz, 0.25)))
    b.inputs["Transmission Weight"].default_value = 0.45
    b.inputs["IOR"].default_value = 1.33
    b.inputs["Coat Weight"].default_value = 0.6
    return m


def m_woda_basen(name):
    """Przejrzysta woda jacuzzi: widać mozaikę pod spodem, drobne zmarszczki."""
    m, n, b, _ = _new(name)
    P = _coords(n)
    px, py, pz = n.sep(P)
    vec = n.xyz(n.math("DIVIDE", px, 1.4), n.math("DIVIDE", py, 1.4))
    nm = n.img(zasob("tekstury/waternormals.jpg"), vec, non_color=True)
    nmap = n.node("ShaderNodeNormalMap", {"Strength": 0.18})
    n.set(nmap.inputs["Color"], nm.outputs["Color"])
    n.set(b.inputs["Normal"], nmap.outputs["Normal"])
    b.inputs["Base Color"].default_value = lin((0.80, 0.97, 0.94))
    b.inputs["Roughness"].default_value = 0.02
    b.inputs["IOR"].default_value = 1.33
    b.inputs["Transmission Weight"].default_value = 1.0
    return m


def m_snieg(name):
    m, n, b, _ = _new(name)
    P = _coords(n)
    nz = n.noise(P, 2.0, 8, 0.6).outputs["Fac"]
    b.inputs["Base Color"].default_value = lin((0.93, 0.94, 0.96))
    b.inputs["Subsurface Weight"].default_value = 0.25
    b.inputs["Subsurface Radius"].default_value = (0.6, 0.8, 1.0)
    b.inputs["Subsurface Scale"].default_value = 0.05
    n.set(b.inputs["Roughness"], n.math("ADD", 0.55, n.math("MULTIPLY", nz, 0.2)))
    sp = n.node("ShaderNodeTexVoronoi", {"Scale": 900.0})
    n.set(sp.inputs["Vector"], P)
    _bump(n, b, n.math("ADD", nz, n.math("MULTIPLY", sp.outputs["Distance"], 0.05)), 0.25, 0.03)
    return m


def m_prosty(name, c, r=0.6, metal=0.0, coat=0.0, emis=None):
    m, n, b, _ = _new(name)
    b.inputs["Base Color"].default_value = lin(c)
    b.inputs["Roughness"].default_value = r
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
    if emis:
        b.inputs["Emission Color"].default_value = lin(emis[0])
        b.inputs["Emission Strength"].default_value = emis[1]
    return m


def m_las_daleki(name):
    """Daleki las na horyzoncie: ciemna zieleń z plamami (korony w cieniu), lekko przymglona, bez połysku."""
    m, n, b, _ = _new(name)
    P = _coords(n)
    small = n.noise(P, 0.9, 6, 0.7).outputs["Fac"]
    big = n.noise(P, 0.02, 3).outputs["Fac"]
    f = n.math("ADD", n.math("MULTIPLY", small, 0.6), n.math("MULTIPLY", big, 0.4))
    col = n.ramp(f, [(0.25, (0.10, 0.14, 0.07)), (0.5, (0.15, 0.20, 0.09)), (0.75, (0.22, 0.26, 0.12))])
    n.set(b.inputs["Base Color"], col)
    b.inputs["Roughness"].default_value = 1.0
    b.inputs["Specular IOR Level"].default_value = 0.05
    return m


RECIPES = {
    "tynk": lambda k: m_tynk(k),
    "tynk_wew": lambda k: m_tynk(k, (0.90, 0.89, 0.86), 0.015, 0.92, 0.03),
    "tynk_mebel": lambda k: m_tynk(k, (0.88, 0.87, 0.84), 0.01, 0.8, 0.02),
    "strop": lambda k: m_tynk(k, (0.90, 0.89, 0.87), 0.012, 0.92, 0.03),
    "beton": lambda k: m_beton(k),
    "beton_cokol": lambda k: m_beton(k, (0.40, 0.40, 0.39), 0.05, 0.85),
    "drewno": lambda k: m_deski(k, (0.56, 0.40, 0.25), 0.13, 0.13, 0.007, True, 0.72),
    "drewno_opal": lambda k: m_deski(k, (0.05, 0.045, 0.04), 0.02, 0.14, 0.006, True, 0.6, charred=True),
    "cegla": lambda k: m_cegla(k),
    "cegla_biala": lambda k: m_cegla(k, white=True),
    "kamien": lambda k: m_bloki(k, (0.74, 0.69, 0.60), 0.07, 0.9, 0.45, 0.004, 0.7),
    "trawertyn": lambda k: m_bloki(k, (0.84, 0.79, 0.69), 0.05, 1.2, 0.6, 0.002, 0.55, bands=True, pores=True,
                                   mortar_c=(0.78, 0.74, 0.66)),
    "corten": lambda k: m_corten(k),
    "miedz": lambda k: m_blacha(k, patina=True),
    "blacha": lambda k: m_blacha(k),
    "rama": lambda k: m_prosty(k, (0.07, 0.07, 0.075), 0.35, 0.7),
    "obrobka": lambda k: m_prosty(k, (0.16, 0.165, 0.17), 0.42, 0.65),
    "drzwi": lambda k: m_deski(k, (0.30, 0.19, 0.11), 0.06, 0.16, 0.002, True, 0.5),
    "szklo": lambda k: m_szklo(k),
    "szklo_mebel": lambda k: m_szklo(k, (0.95, 0.98, 0.97)),
    "woda": lambda k: m_woda(k),
    "wodospad": lambda k: m_wodospad(k),
    "woda_basen": lambda k: m_woda_basen(k),
    "lupek": lambda k: m_bloki(k, (0.19, 0.19, 0.20), 0.14, 0.55, 0.12, 0.004, 0.8, mortar_c=(0.07, 0.07, 0.075)),
    "mozaika": lambda k: m_bloki(k, (0.16, 0.62, 0.58), 0.18, 0.05, 0.05, 0.0018, 0.22, mortar_c=(0.78, 0.82, 0.8), offset=0.0),
    "zielona_sciana": lambda k: m_prosty(k, (0.07, 0.13, 0.05), 0.95),
    "podloga_drewno": lambda k: m_parkiet(k),
    "podloga_ciemna": lambda k: m_parkiet(k, (0.62, 0.45, 0.32), 0.62, 0.8),
    "podloga_kamien": lambda k: m_bloki(k, (0.80, 0.78, 0.74), 0.03, 1.2, 0.6, 0.0015, 0.32, mortar_c=(0.66, 0.64, 0.6), offset=0.0),
    "podloga_terakota": lambda k: m_bloki(k, (0.70, 0.40, 0.27), 0.09, 0.3, 0.3, 0.003, 0.65, mortar_c=(0.62, 0.58, 0.52), offset=0.0),
    "podloga_tatami": lambda k: m_bloki(k, (0.76, 0.72, 0.50), 0.04, 0.9, 1.8, 0.012, 0.85, mortar_c=(0.12, 0.14, 0.10), offset=0.5),
    "podloga_beton": lambda k: m_beton(k, (0.58, 0.57, 0.55), 0.05, polished=True),
    "deck": lambda k: m_deski(k, (0.50, 0.38, 0.27), 0.12, 0.14, 0.008, False, 0.75, floor=True),
    "sedum": lambda k: m_sedum(k),
    "zwir_dach": lambda k: m_zwir(k, (0.62, 0.60, 0.56), 0.12, 55),
    "trawa": lambda k: m_trawa(k),
    "trawa_ogrod": lambda k: m_trawa(k, 2.0),
    "sciezka": lambda k: m_bloki(k, (0.68, 0.66, 0.62), 0.05, 0.6, 0.3, 0.004, 0.8, mortar_c=(0.45, 0.44, 0.42)),
    "zwir_ogrod": lambda k: m_zwir(k, (0.84, 0.83, 0.79), 0.08, 90),
    "zwir_grabiony": lambda k: m_zwir(k, (0.76, 0.75, 0.71), 0.08, 110, rake=True),
    "plyty_ogrod": lambda k: m_bloki(k, (0.74, 0.71, 0.65), 0.06, 0.9, 0.6, 0.008, 0.7, mortar_c=(0.35, 0.33, 0.3)),
    "kamien_ogrod": lambda k: m_beton(k, (0.42, 0.41, 0.39), 0.10, 0.8),
    "snieg": lambda k: m_snieg(k),
    "las_daleki": lambda k: m_las_daleki(k),
    "lampa": lambda k: m_prosty(k, (1.0, 0.95, 0.85), 0.5, emis=((1.0, 0.82, 0.6), 6.0)),
    # wnętrza: lamele, farby, płytki, posadzki
    "lamele": lambda k: m_deski(k, (0.62, 0.45, 0.29), 0.07, 0.04, 0.0, True, 0.5),
    "listwa": lambda k: m_prosty(k, (0.88, 0.87, 0.84), 0.45),
    "drzwi_wew": lambda k: m_prosty(k, (0.86, 0.85, 0.82), 0.32),
    "panel_akustyczny": lambda k: m_deski(k, (0.30, 0.21, 0.14), 0.06, 0.04, 0.014, True, 0.62),
    "podloga_plytki": lambda k: m_bloki(k, (0.58, 0.56, 0.53), 0.04, 1.2, 0.6, 0.004, 0.36,
                                        mortar_c=(0.42, 0.40, 0.38), offset=0.0, bands=True),
    "podloga_wykladzina": lambda k: m_tynk(k, (0.16, 0.155, 0.16), 0.02, 1.0, 0.35),
    "plytki_kamien": lambda k: m_bloki(k, (0.84, 0.82, 0.78), 0.045, 0.6, 1.2, 0.0035, 0.24,
                                       mortar_c=(0.62, 0.60, 0.57), offset=0.0, bands=True),
    "plytki_zielone": lambda k: m_bloki(k, (0.15, 0.31, 0.26), 0.12, 0.30, 0.075, 0.003, 0.08,
                                        mortar_c=(0.80, 0.80, 0.77), offset=0.5),
    "plytki_terazzo": lambda k: m_bloki(k, (0.87, 0.85, 0.81), 0.03, 0.6, 0.6, 0.003, 0.3,
                                        mortar_c=(0.66, 0.64, 0.61), offset=0.0, pores=True),
}
# farby ścienne (mat, delikatna faktura wałka)
FARBY = {
    "bialy": (0.90, 0.90, 0.88), "cieply_bialy": (0.89, 0.87, 0.82), "greige": (0.76, 0.72, 0.66),
    "zielen": (0.23, 0.31, 0.27), "glina": (0.72, 0.56, 0.45), "szalwia": (0.62, 0.66, 0.58),
    "szalwia_jasna": (0.78, 0.80, 0.74), "granat": (0.17, 0.21, 0.29), "mieta": (0.74, 0.85, 0.79),
    "brzoskwinia": (0.93, 0.76, 0.64), "grafit": (0.11, 0.11, 0.12),
}
for _k, _c in FARBY.items():
    RECIPES["farba_" + _k] = (lambda c: (lambda k: m_tynk(k, c, 0.008, 0.88, 0.025)))(_c)


def material(name, ctx):
    """Materiał o nazwie z silnika (bryla.py); nieznane nazwy – stary przepis z render_blender.make_mat."""
    cache = ctx.cache.setdefault("mat", {})
    if name in cache:
        return cache[name]
    f = RECIPES.get(name)
    if f is not None:
        m = f(name)
    else:
        from render_blender import make_mat
        m = make_mat(name, ctx.dusk)
    cache[name] = m
    return m
