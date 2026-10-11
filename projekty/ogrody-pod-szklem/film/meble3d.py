"""Meble 3D do filmów: realistyczne meble (Cycles) w miejsce prostych brył z silnik/meble.py.

    from film.meble3d import build_items
    obiekty = build_items(items, ctx)      # lista utworzonych obiektów bpy

Każdy element budujemy w układzie lokalnym: początek w środku na podłodze, szerokość wzdłuż X
(−w/2…w/2), głębokość wzdłuż Y, plecy (od ściany) po stronie +Y, front po stronie −Y.
Pusty obiekt-korzeń dostaje położenie i obrót z planu, części są jego dziećmi.  Stara część
z `parts` w punkcie planu (x, y) leży w Blenderze w (x, −y).
Modele glTF z zasoby/modele importujemy raz na scenę (ctx.cache) i wstawiamy jako kopie
dzielące siatki; resztę modelujemy proceduralnie (bmesh) z fazowanymi krawędziami.
Wieczorem (ctx.dusk) lampy świecą ciepło (2700 K), ogień w kominku i piecu migocze.
"""
import math
import os
import random

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector, noise

try:
    from .kontekst import zasob
except ImportError:  # moduł uruchomiony spoza pakietu film
    from kontekst import zasob

OUTDOOR = {"patio", "patio_sezonowe", "taras", "loggia"}
WARM = 2700.0          # barwa lamp wieczorem [K]
DEBUG = bool(os.environ.get("MEBLE3D_DEBUG"))

# ------------------------------------------------------------------ palety (sRGB 0–1)
SOFA = [("granat", (0.13, 0.18, 0.32)), ("oliwka", (0.36, 0.37, 0.21)), ("piasek", (0.68, 0.61, 0.50)),
        ("terakota", (0.62, 0.32, 0.21)), ("grafit", (0.22, 0.22, 0.23)), ("roz", (0.74, 0.56, 0.54))]
AKCENT = [(0.78, 0.58, 0.22), (0.64, 0.33, 0.21), (0.57, 0.63, 0.51), (0.42, 0.49, 0.57), (0.87, 0.83, 0.75),
          (0.71, 0.43, 0.33), (0.45, 0.45, 0.27), (0.80, 0.63, 0.60), (0.20, 0.23, 0.31)]
OBICIE = [(0.74, 0.69, 0.60), (0.56, 0.56, 0.54), (0.57, 0.60, 0.50), (0.26, 0.26, 0.27), (0.58, 0.35, 0.24),
          (0.65, 0.57, 0.47)]
POSCIEL = [(0.88, 0.88, 0.86), (0.82, 0.78, 0.70), (0.74, 0.75, 0.76), (0.70, 0.73, 0.65), (0.80, 0.68, 0.60)]
KOC = [(0.62, 0.33, 0.22), (0.76, 0.57, 0.22), (0.27, 0.28, 0.29), (0.45, 0.46, 0.28), (0.71, 0.45, 0.35),
       (0.37, 0.45, 0.53)]
DYWAN = [((0.79, 0.74, 0.65), (0.62, 0.56, 0.47)), ((0.72, 0.72, 0.70), (0.38, 0.38, 0.39)),
         ((0.85, 0.81, 0.73), (0.66, 0.44, 0.32)), ((0.64, 0.68, 0.60), (0.85, 0.83, 0.76)),
         ((0.36, 0.36, 0.37), (0.50, 0.49, 0.47)), ((0.57, 0.62, 0.68), (0.82, 0.81, 0.79))]
DREWNO = {"dab": ((0.80, 0.65, 0.47), (0.58, 0.43, 0.28)), "dab_miod": ((0.75, 0.56, 0.35), (0.50, 0.34, 0.19)),
          "dab_wedz": ((0.47, 0.36, 0.27), (0.27, 0.19, 0.13)), "orzech": ((0.49, 0.35, 0.25), (0.27, 0.17, 0.11)),
          "tik": ((0.62, 0.46, 0.32), (0.42, 0.30, 0.20)), "sauna": ((0.88, 0.76, 0.60), (0.74, 0.60, 0.44)),
          "buk": ((0.83, 0.67, 0.51), (0.69, 0.53, 0.39)), "swierk": ((0.90, 0.79, 0.60), (0.78, 0.64, 0.45))}
FRONTY = [(0.87, 0.86, 0.83), (0.56, 0.61, 0.53), (0.67, 0.63, 0.58), (0.22, 0.23, 0.24), None]  # None = fornir dębowy
KSIAZKI = [(0.55, 0.16, 0.13), (0.14, 0.22, 0.38), (0.20, 0.35, 0.27), (0.80, 0.76, 0.66), (0.12, 0.12, 0.13),
           (0.76, 0.56, 0.24), (0.47, 0.50, 0.53), (0.66, 0.36, 0.25), (0.32, 0.25, 0.36), (0.40, 0.30, 0.22),
           (0.30, 0.42, 0.50), (0.60, 0.20, 0.25), (0.86, 0.66, 0.50), (0.20, 0.28, 0.24), (0.62, 0.58, 0.50),
           (0.24, 0.20, 0.17), (0.72, 0.30, 0.18), (0.50, 0.55, 0.40)]
KAMIONKA = [(0.62, 0.58, 0.52), (0.30, 0.30, 0.30), (0.80, 0.76, 0.68), (0.57, 0.38, 0.28), (0.48, 0.53, 0.48)]


def lin(c):
    """sRGB 0–1 → liniowy RGB (Blender)."""
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c[:3])


def rgba(c):
    return lin(c) + (1.0,)


def shade(c, k):
    return tuple(min(1.0, max(0.0, x * k)) for x in c)


def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def R(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def Sc(x, y=None, z=None):
    return Matrix.Diagonal((x, x if y is None else y, x if z is None else z, 1.0))


# ------------------------------------------------------------------ styl domu (z ctx.seed)
def _styl(ctx):
    s = ctx.cache.get("m3d_styl")
    if s is None:
        r = random.Random(f"styl:{ctx.seed}")
        si = r.randrange(len(SOFA))
        akc = list(AKCENT)
        r.shuffle(akc)
        s = dict(
            sofa=SOFA[si][1], sofa2=SOFA[(si + 3) % len(SOFA)][1], akcent=akc[:3],
            obicie=r.choice(OBICIE), posciel=r.choice(POSCIEL), koc=r.choice(KOC),
            dywan=r.randrange(len(DYWAN)), wzor=r.choice(["gladki", "pasy", "ramka", "melanz"]),
            drewno=r.choice(["dab", "dab", "dab_miod", "dab_wedz", "orzech"]),
            front=r.choice(FRONTY), blat=r.choice(["kwarc", "kwarc_szary", "ciemny", "trawertyn"]),
            metal=r.choice(["czarny_metal", "czarny_metal", "mosiadz", "stal"]),
            uchwyt=r.choice(["listwa", "listwa", "bez", "galka"]), gorne=r.choice(["szafki", "polki"]),
            szafa=r.choice(["dab", "bialy", "greige"]), krzeslo=r.choice(["drewno", "drewno", "tapicerowane"]),
            stol=r.choice(["nogi", "plozy", "kozly"]), lampa=r.choice(["kopula", "stozek", "kula", "len"]),
            kominek=r.choice(["beton", "kamien"]), stolik=r.choice(["dab", "kamien", "czarny"]),
            mata=r.choice([(0.50, 0.57, 0.49), (0.45, 0.32, 0.40), (0.28, 0.29, 0.31), (0.64, 0.52, 0.42)]),
            ogrod=r.choice([(0.84, 0.81, 0.74), (0.58, 0.58, 0.56), (0.38, 0.42, 0.40)]),
        )
        ctx.cache["m3d_styl"] = s
    return s


# ------------------------------------------------------------------ węzły materiałów
def _sock(nd, name):
    for s in nd.inputs:
        if s.name == name and s.enabled:
            return s
    for s in nd.inputs:
        if s.name == name:
            return s
    return None


class _NT:
    """Zwięzła budowa drzewa węzłów materiału."""

    def __init__(self, m):
        self.nt = m.node_tree
        self.N, self.L = self.nt.nodes, self.nt.links
        self.b = self.N.get("Principled BSDF")
        self.out = self.N.get("Material Output")
        self._tc = None

    def n(self, typ, **kw):
        nd = self.N.new(typ)
        for k, v in kw.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
        for k, v in kw.items():
            if not hasattr(nd, k):
                _sock(nd, k.replace("_", " ")).default_value = v
        return nd

    def l(self, a, b):
        if isinstance(a, (int, float, tuple)):
            b.default_value = a
        else:
            self.L.new(a, b)

    def co(self, kind="Object"):
        if self._tc is None:
            self._tc = self.N.new("ShaderNodeTexCoord")
        return self._tc.outputs[kind]

    def map(self, vec, scale=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0)):
        nd = self.N.new("ShaderNodeMapping")
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Location"].default_value = loc
        nd.inputs["Rotation"].default_value = rot
        self.L.new(vec, nd.inputs["Vector"])
        return nd.outputs["Vector"]

    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.N.new("ShaderNodeMath")
        nd.operation = op
        nd.use_clamp = clamp
        for i, v in enumerate((a, b, c)):
            if v is not None:
                self.l(v, nd.inputs[i])
        return nd.outputs[0]

    def ramp(self, fac, stops, interp="LINEAR"):
        nd = self.N.new("ShaderNodeValToRGB")
        cr = nd.color_ramp
        cr.interpolation = interp
        e = cr.elements
        e[0].position, e[0].color = stops[0][0], stops[0][1]
        e[1].position, e[1].color = stops[-1][0], stops[-1][1]
        for p, c in stops[1:-1]:
            e.new(p).color = c
        self.l(fac, nd.inputs["Fac"])
        return nd.outputs["Color"]

    def mixc(self, fac, a, b, blend="MIX"):
        nd = self.N.new("ShaderNodeMixRGB")
        nd.blend_type = blend
        self.l(fac, nd.inputs[0])
        self.l(a, nd.inputs[1])
        self.l(b, nd.inputs[2])
        return nd.outputs[0]

    def bump(self, h, strength=0.2, dist=0.002, normal=None):
        nd = self.N.new("ShaderNodeBump")
        nd.inputs["Strength"].default_value = strength
        nd.inputs["Distance"].default_value = dist
        self.L.new(h, nd.inputs["Height"])
        if normal is not None:
            self.L.new(normal, nd.inputs["Normal"])
        return nd.outputs["Normal"]

    def noise(self, vec, scale, detail=3.0, rough=0.5, dist=0.0):
        nd = self.N.new("ShaderNodeTexNoise")
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Detail"].default_value = detail
        nd.inputs["Roughness"].default_value = rough
        nd.inputs["Distortion"].default_value = dist
        if vec is not None:
            self.L.new(vec, nd.inputs["Vector"])
        return nd

    def wave(self, vec, scale, direction="X", dist=0.0, detail=2.0, kind="BANDS"):
        nd = self.N.new("ShaderNodeTexWave")
        nd.wave_type = kind
        nd.bands_direction = direction
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Distortion"].default_value = dist
        nd.inputs["Detail"].default_value = detail
        self.L.new(vec, nd.inputs["Vector"])
        return nd

    def shader_out(self, sock):
        self.L.new(sock, self.out.inputs["Surface"])


_PK = {"col": "Base Color", "rough": "Roughness", "metal": "Metallic", "coat": "Coat Weight", "coat_r": "Coat Roughness",
       "sheen": "Sheen Weight", "sheen_r": "Sheen Roughness", "sheen_tint": "Sheen Tint", "trans": "Transmission Weight",
       "ior": "IOR", "sss": "Subsurface Weight", "aniso": "Anisotropic", "spec": "Specular IOR Level",
       "emis": "Emission Color", "emis_s": "Emission Strength", "alpha": "Alpha"}


def _p(t, **kw):
    for k, v in kw.items():
        if k in ("col", "sheen_tint", "emis"):
            v = rgba(v)
        t.b.inputs[_PK[k]].default_value = v


def _m_new(name):
    m = bpy.data.materials.new(name)
    return m, _NT(m)


def _mk_plain(name, col, bump=0.0, bscale=200.0, **kw):
    m, t = _m_new(name)
    _p(t, col=col, **kw)
    if bump:
        nz = t.noise(t.co(), bscale, 4.0, 0.6)
        t.l(t.bump(nz.outputs["Fac"], bump, 0.001), t.b.inputs["Normal"])
    return m


def _mk_wood(name, light, dark, axis="X", rough=0.5, coat=0.0, ring=45.0, board=0.15):
    """Drewno proceduralne: słoje (fala + szum), pory, odcień deski, losowo na obiekt."""
    m, t = _m_new(name)
    co = t.co()
    k = 0.10
    v1 = t.map(co, scale={"X": (k, 1, 1), "Y": (1, k, 1), "Z": (1, 1, k)}[axis])
    wv = t.wave(v1, ring, "DIAGONAL", dist=6.0, detail=2.5)
    _sock(wv, "Detail Scale").default_value = 0.7
    f = 110.0
    v2 = t.map(co, scale={"X": (2.0, f, f), "Y": (f, 2.0, f), "Z": (f, f, 2.0)}[axis])
    nz = t.noise(v2, 1.0, 5.0, 0.6)
    sep = t.n("ShaderNodeSeparateXYZ")
    t.l(co, sep.inputs[0])
    idx = t.math("FLOOR", t.math("DIVIDE", sep.outputs["Y" if axis == "X" else "X"], board))
    wn = t.n("ShaderNodeTexWhiteNoise", noise_dimensions="1D")
    t.l(idx, wn.inputs["W"])
    oi = t.n("ShaderNodeObjectInfo")
    fac = t.math("MULTIPLY", wv.outputs["Fac"], 0.26)
    fac = t.math("MULTIPLY_ADD", nz.outputs["Fac"], 0.62, fac)
    fac = t.math("MULTIPLY_ADD", wn.outputs["Value"], 0.20, fac)
    fac = t.math("MULTIPLY_ADD", oi.outputs["Random"], 0.10, fac)
    t.l(t.ramp(fac, [(0.22, rgba(dark)), (0.55, rgba(mix3(dark, light, 0.55))), (0.88, rgba(light))]),
        t.b.inputs["Base Color"])
    t.l(t.math("MULTIPLY_ADD", nz.outputs["Fac"], 0.18, rough - 0.09), t.b.inputs["Roughness"])
    t.l(t.bump(nz.outputs["Fac"], 0.06, 0.0008), t.b.inputs["Normal"])
    if coat:
        _p(t, coat=coat, coat_r=0.12)
    return m


def mix3(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def _mk_fabric(name, col, rough=0.92, sheen=0.35, weave=140.0, bump=0.25, mel=0.06, sheen_tint=None):
    """Tkanina: splot (fale w trzech osiach), melanż, połysk aksamitny (sheen)."""
    m, t = _m_new(name)
    co = t.co()
    wx = t.wave(co, weave, "X")
    wy = t.wave(co, weave, "Y")
    wz = t.wave(co, weave, "Z")
    h = t.math("ADD", t.math("ADD", wx.outputs["Fac"], wy.outputs["Fac"]), wz.outputs["Fac"])
    nf = t.noise(co, weave * 1.7, 2.0, 0.5)
    h = t.math("MULTIPLY_ADD", nf.outputs["Fac"], 1.2, h)
    nm = t.noise(co, 9.0, 3.0, 0.55)
    t.l(t.ramp(nm.outputs["Fac"], [(0.3, rgba(shade(col, 1 - mel))), (0.7, rgba(shade(col, 1 + mel)))]),
        t.b.inputs["Base Color"])
    _p(t, rough=rough, sheen=sheen, sheen_r=0.45, sheen_tint=sheen_tint or (1.0, 1.0, 1.0))
    t.l(t.bump(h, bump, 0.0006), t.b.inputs["Normal"])
    return m


def _mk_stone(name, base, vein, rough=0.25, vein_k=0.55, vscale=1.3, coat=0.0, speck=0.05, stretch=(1, 1, 1)):
    """Kamień/konglomerat: żyłki (wąskie pasmo szumu), drobne ziarno."""
    m, t = _m_new(name)
    co = t.co()
    v = t.map(co, scale=stretch)
    nz = t.noise(v, vscale, 7.0, 0.62, 1.2)
    d = t.math("ABSOLUTE", t.math("SUBTRACT", nz.outputs["Fac"], 0.5))
    mr = t.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
    t.l(d, _sock(mr, "Value"))
    _sock(mr, "From Min").default_value = 0.0
    _sock(mr, "From Max").default_value = 0.018
    _sock(mr, "To Min").default_value = vein_k
    _sock(mr, "To Max").default_value = 0.0
    vo = t.n("ShaderNodeTexVoronoi", Scale=260.0)
    t.l(co, vo.inputs["Vector"])
    nb = t.noise(co, 4.0, 3.0, 0.5)
    c = t.ramp(nb.outputs["Fac"], [(0.3, rgba(shade(base, 0.97))), (0.7, rgba(shade(base, 1.03)))])
    c = t.mixc(vo.outputs["Distance"], rgba(shade(base, 1 - speck)), c, "MIX")
    c = t.mixc(mr.outputs[0], c, rgba(vein), "MIX")
    t.l(c, t.b.inputs["Base Color"])
    _p(t, rough=rough)
    if coat:
        _p(t, coat=coat, coat_r=0.05)
    t.l(t.bump(nb.outputs["Fac"], 0.03, 0.002), t.b.inputs["Normal"])
    return m


def _mk_concrete(name, base, rough=0.78):
    m, t = _m_new(name)
    co = t.co()
    n1 = t.noise(co, 2.2, 6.0, 0.6)
    n2 = t.noise(co, 45.0, 4.0, 0.6)
    f = t.math("MULTIPLY_ADD", n2.outputs["Fac"], 0.35, n1.outputs["Fac"])
    t.l(t.ramp(f, [(0.45, rgba(shade(base, 0.9))), (1.0, rgba(shade(base, 1.08)))]), t.b.inputs["Base Color"])
    vo = t.n("ShaderNodeTexVoronoi", Scale=90.0)
    t.l(co, vo.inputs["Vector"])
    t.l(t.math("MULTIPLY_ADD", n2.outputs["Fac"], 0.12, rough - 0.06), t.b.inputs["Roughness"])
    h = t.math("ADD", n2.outputs["Fac"], t.math("LESS_THAN", vo.outputs["Distance"], 0.08))
    t.l(t.bump(h, 0.12, 0.002), t.b.inputs["Normal"])
    return m


def _mk_glass(name, col=(1, 1, 1), rough=0.0, ior=1.5):
    """Szkło prawdziwe; promienie cienia przechodzą (bez kaustyk szkło nie rzuca czarnego cienia)."""
    m, t = _m_new(name)
    _p(t, col=col, trans=1.0, rough=rough, ior=ior)
    lp = t.n("ShaderNodeLightPath")
    tr = t.n("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = rgba(col)
    mx = t.n("ShaderNodeMixShader")
    t.l(lp.outputs["Is Shadow Ray"], mx.inputs[0])
    t.l(t.b.outputs[0], mx.inputs[1])
    t.l(tr.outputs[0], mx.inputs[2])
    t.shader_out(mx.outputs[0])
    return m


def _mk_thin_glass(name, col=(1, 1, 1), refl=0.08, rough=0.02):
    """Cienkie szkło (słoiki, szklanki, panele): przezroczyste z odbiciem Fresnela – tanie w renderze."""
    m, t = _m_new(name)
    tr = t.n("ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = rgba(col)
    gl = t.n("ShaderNodeBsdfGlossy")
    gl.inputs["Color"].default_value = (1, 1, 1, 1)
    gl.inputs["Roughness"].default_value = rough
    lw = t.n("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.25
    f = t.math("MULTIPLY_ADD", lw.outputs["Fresnel"], 1.0 - refl, refl, clamp=True)
    mx = t.n("ShaderNodeMixShader")
    t.l(f, mx.inputs[0])
    t.l(tr.outputs[0], mx.inputs[1])
    t.l(gl.outputs[0], mx.inputs[2])
    t.shader_out(mx.outputs[0])
    return m


def _mk_attr(name, rough=0.5, metal=0.0, books=False, leaf=False):
    """Kolor z atrybutu 'kolor' (książki, nakrętki, liście, pudełka) – jedna siatka, wiele barw."""
    m, t = _m_new(name)
    vc = t.n("ShaderNodeVertexColor", layer_name="kolor")
    col = vc.outputs["Color"]
    if books:
        uv = t.n("ShaderNodeUVMap", uv_map="UVMap")
        sep = t.n("ShaderNodeSeparateXYZ")
        t.l(uv.outputs["UV"], sep.inputs[0])
        u, v = sep.outputs["X"], sep.outputs["Y"]
        fl = vc.outputs["Alpha"]

        def band(x, a, b):
            return t.math("MULTIPLY", t.math("GREATER_THAN", x, a), t.math("LESS_THAN", x, b))

        lab = t.math("MULTIPLY", band(v, 0.60, 0.80), band(u, 0.16, 0.84))
        lab = t.math("MULTIPLY", lab, t.math("GREATER_THAN", fl, 0.5))
        gold = t.math("ADD", band(v, 0.06, 0.085), band(v, 0.905, 0.93))
        gold = t.math("MULTIPLY", gold, band(fl, 0.2, 0.5))
        col = t.mixc(lab, col, rgba((0.86, 0.83, 0.75)))
        col = t.mixc(gold, col, rgba((0.72, 0.57, 0.30)))
        nz = t.noise(t.co(), 300.0, 2.0, 0.5)
        t.l(t.bump(nz.outputs["Fac"], 0.08, 0.0005), t.b.inputs["Normal"])
    if leaf:
        oi = t.n("ShaderNodeObjectInfo")
        col = t.mixc(t.math("MULTIPLY", oi.outputs["Random"], 0.3), col, rgba((0.25, 0.32, 0.10)))
        _p(t, sss=0.12)
    t.l(col, t.b.inputs["Base Color"])
    _p(t, rough=rough, metal=metal)
    return m


def _mk_emit(name, dusk, day_col, strength, temp=WARM, rough=0.25, glow_base=None):
    """Świecące elementy (żarówki, klosze, LED): wieczorem emisja ciała doskonale czarnego."""
    m, t = _m_new(name)
    _p(t, col=day_col, rough=rough)
    if dusk:
        bb = t.n("ShaderNodeBlackbody")
        bb.inputs["Temperature"].default_value = temp
        t.l(bb.outputs[0], t.b.inputs["Emission Color"])
        _p(t, emis_s=strength)
    return m


def _mk_rug(name, c1, c2, wzor, w, d):
    m, t = _m_new(name)
    co = t.co()
    sep = t.n("ShaderNodeSeparateXYZ")
    t.l(co, sep.inputs[0])
    x, y = sep.outputs["X"], sep.outputs["Y"]
    nm = t.noise(co, 14.0, 4.0, 0.6)
    base = t.ramp(nm.outputs["Fac"], [(0.3, rgba(shade(c1, 0.95))), (0.7, rgba(shade(c1, 1.04)))])
    if wzor == "ramka":
        ax = t.math("SUBTRACT", t.math("ABSOLUTE", x), w / 2 - 0.20)
        ay = t.math("SUBTRACT", t.math("ABSOLUTE", y), d / 2 - 0.20)
        mm = t.math("MAXIMUM", ax, ay)
        k = t.math("MULTIPLY", t.math("GREATER_THAN", mm, 0.0), t.math("LESS_THAN", mm, 0.06))
        k2 = t.math("MULTIPLY", t.math("GREATER_THAN", mm, 0.10), t.math("LESS_THAN", mm, 0.115))
        col = t.mixc(t.math("ADD", k, k2), base, rgba(c2))
    elif wzor == "pasy":
        wv = t.wave(co, 2.2, "Y", dist=0.6, detail=1.0)
        k = t.math("GREATER_THAN", wv.outputs["Fac"], 0.86)
        col = t.mixc(t.math("MULTIPLY", k, 0.85), base, rgba(c2))
    elif wzor == "melanz":
        n2 = t.noise(co, 55.0, 2.0, 0.5)
        col = t.mixc(t.math("MULTIPLY", t.math("GREATER_THAN", n2.outputs["Fac"], 0.56), 0.6), base, rgba(c2))
    else:
        col = base
    t.l(col, t.b.inputs["Base Color"])
    vo = t.n("ShaderNodeTexVoronoi", Scale=420.0)
    t.l(co, vo.inputs["Vector"])
    nf = t.noise(co, 380.0, 2.0, 0.5)
    h = t.math("ADD", vo.outputs["Distance"], nf.outputs["Fac"])
    t.l(t.bump(h, 0.45, 0.002), t.b.inputs["Normal"])
    _p(t, rough=0.97, sheen=0.4, sheen_r=0.5)
    return m


def _mk_painting(name, seed):
    m, t = _m_new(name)
    r = random.Random(f"obraz:{seed}")
    pal = [(0.11, 0.12, 0.14), (0.78, 0.60, 0.30), (0.90, 0.87, 0.80), (0.70, 0.38, 0.26), (0.34, 0.43, 0.52),
           (0.85, 0.80, 0.70), (0.45, 0.50, 0.40)]
    r.shuffle(pal)
    co = t.co()
    nz = t.noise(co, r.uniform(1.2, 2.4), 2.0, 0.45, r.uniform(0.6, 1.8))
    st = [(i / 5.0, rgba(pal[i])) for i in range(6)]
    c = t.ramp(nz.outputs["Fac"], st, "EASE")
    t.l(c, t.b.inputs["Base Color"])
    v = t.map(co, scale=(30, 4, 30))
    ns = t.noise(v, 1.0, 3.0, 0.6)
    t.l(t.bump(ns.outputs["Fac"], 0.25, 0.001), t.b.inputs["Normal"])
    _p(t, rough=0.62)
    return m


def _mk_screen(name, dusk):
    m, t = _m_new(name)
    _p(t, col=(0.012, 0.012, 0.014), rough=0.05)
    if dusk:
        nz = t.noise(t.co(), 1.4, 2.0, 0.5)
        c = t.ramp(nz.outputs["Fac"], [(0.25, rgba((0.20, 0.24, 0.30))), (0.55, rgba((0.55, 0.58, 0.62))),
                                       (0.8, rgba((0.80, 0.74, 0.66)))])
        t.l(c, t.b.inputs["Emission Color"])
        _p(t, emis_s=0.45)
    return m


def _mk_fire(name, z0=0.35, h=0.36):
    """Płomienie na płaszczyznach: maska z szumu 4D (W sterowane klatką – ogień faluje w filmie),
    jasna żółć u podstawy, pomarańcz i przezroczystość ku górze i na bokach."""
    m, t = _m_new(name)
    co = t.co()
    sep = t.n("ShaderNodeSeparateXYZ")
    t.l(co, sep.inputs[0])
    zr = t.math("DIVIDE", t.math("SUBTRACT", sep.outputs["Z"], z0), h)
    v = t.map(co, scale=(9.0, 9.0, 2.6))
    nz = t.n("ShaderNodeTexNoise", noise_dimensions="4D", Scale=1.0, Detail=3.0, Roughness=0.55, Distortion=0.5)
    t.l(v, nz.inputs["Vector"])
    fc = nz.inputs["W"].driver_add("default_value")
    fc.driver.type = "SCRIPTED"
    fc.driver.expression = "frame*0.07"
    m1 = t.math("MULTIPLY_ADD", t.math("SUBTRACT", nz.outputs["Fac"], 0.5), 1.3, t.math("MULTIPLY_ADD", zr, -1.3, 1.12))
    fx = t.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
    t.l(t.math("ABSOLUTE", sep.outputs["X"]), _sock(fx, "Value"))
    _sock(fx, "From Min").default_value = 0.16
    _sock(fx, "From Max").default_value = 0.34
    _sock(fx, "To Min").default_value = 1.0
    _sock(fx, "To Max").default_value = 0.0
    base = t.math("MINIMUM", t.math("MULTIPLY", zr, 8.0), 1.0, clamp=True)
    mask = t.math("MULTIPLY", t.math("MULTIPLY", m1, fx.outputs[0]), base, clamp=True)
    c = t.ramp(mask, [(0.0, rgba((0.80, 0.10, 0.01))), (0.45, rgba((1.0, 0.36, 0.04))), (0.85, rgba((1.0, 0.70, 0.25)))])
    em = t.n("ShaderNodeEmission")
    t.l(c, em.inputs["Color"])
    t.l(t.math("MULTIPLY", mask, 9.0), em.inputs["Strength"])
    tr = t.n("ShaderNodeBsdfTransparent")
    mx = t.n("ShaderNodeMixShader")
    t.l(t.math("POWER", mask, 0.6), mx.inputs[0])
    t.l(tr.outputs[0], mx.inputs[1])
    t.l(em.outputs[0], mx.inputs[2])
    t.shader_out(mx.outputs[0])
    return m


def _mk_embers(name, dusk):
    m, t = _m_new(name)
    co = t.co()
    vo = t.n("ShaderNodeTexVoronoi", Scale=140.0, feature="DISTANCE_TO_EDGE")
    t.l(co, vo.inputs["Vector"])
    nz = t.noise(co, 12.0, 3.0, 0.5)
    t.l(t.ramp(nz.outputs["Fac"], [(0.3, rgba((0.03, 0.025, 0.02))), (0.8, rgba((0.12, 0.10, 0.09)))]),
        t.b.inputs["Base Color"])
    _p(t, rough=0.95)
    if dusk:
        k = t.math("LESS_THAN", vo.outputs["Distance"], 0.05)
        k = t.math("MULTIPLY", k, t.math("GREATER_THAN", nz.outputs["Fac"], 0.5))
        t.l(rgba((1.0, 0.25, 0.03)), t.b.inputs["Emission Color"])
        t.l(t.math("MULTIPLY", k, 3.0), t.b.inputs["Emission Strength"])
    return m


def _mk_pegboard(name):
    """Płyta perforowana (otwory co 25 mm w płaszczyźnie XZ)."""
    m, t = _m_new(name)
    sep = t.n("ShaderNodeSeparateXYZ")
    t.l(t.co(), sep.inputs[0])
    fx = t.math("SUBTRACT", t.math("FRACT", t.math("DIVIDE", sep.outputs["X"], 0.025)), 0.5)
    fz = t.math("SUBTRACT", t.math("FRACT", t.math("DIVIDE", sep.outputs["Z"], 0.025)), 0.5)
    dd = t.math("SQRT", t.math("ADD", t.math("MULTIPLY", fx, fx), t.math("MULTIPLY", fz, fz)))
    hole = t.math("LESS_THAN", dd, 0.16)
    t.l(t.mixc(hole, rgba((0.66, 0.54, 0.40)), rgba((0.05, 0.04, 0.035))), t.b.inputs["Base Color"])
    _p(t, rough=0.8)
    return m


def _mk_bronze(name):
    m, t = _m_new(name)
    nz = t.noise(t.co(), 5.0, 4.0, 0.6)
    t.l(t.ramp(nz.outputs["Fac"], [(0.35, rgba((0.22, 0.15, 0.09))), (0.7, rgba((0.58, 0.40, 0.23)))]),
        t.b.inputs["Base Color"])
    t.l(t.math("MULTIPLY_ADD", nz.outputs["Fac"], -0.25, 0.48), t.b.inputs["Roughness"])
    _p(t, metal=1.0)
    return m


def _mk_velvet(name, src, col, dark=0.55):
    """Kopia tkaniny modelu glTF w innym kolorze (aksamit: ciemniejsza baza + barwny połysk)."""
    m = src.copy()
    m.name = name
    b = m.node_tree.nodes.get("Principled BSDF")
    lc = lin(col)
    if b.inputs["Base Color"].is_linked:
        for lk in list(b.inputs["Base Color"].links):
            m.node_tree.links.remove(lk)
    b.inputs["Base Color"].default_value = tuple(x * dark for x in lc) + (1.0,)
    b.inputs["Sheen Tint"].default_value = tuple(min(1.0, x * 1.3 + 0.03) for x in lc) + (1.0,)
    b.inputs["Sheen Weight"].default_value = 0.8
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = 0.75
    return m


def mat(ctx, key):
    """Materiał z biblioteki (tworzony raz na scenę, trzymany w ctx.cache)."""
    lib = ctx.cache.setdefault("m3d_mat", {})
    ck = (key, bool(ctx.dusk))
    m = lib.get(ck)
    if m is None:
        m = _make_mat(ctx, key)
        lib[ck] = m
    return m


_WOODS = ("drewno", "dab", "orzech", "tik", "sauna", "buk", "swierk")


def _make_mat(ctx, key):
    s = _styl(ctx)
    b, *a = key.split(":")
    nm = "m3d_" + key
    dusk = bool(ctx.dusk)
    root = b[:-2] if b.endswith(("_y", "_z")) else b
    if root in _WOODS:
        light, dark = DREWNO[s["drewno"] if root == "drewno" else root]
        ax = "Y" if b.endswith("_y") else "Z" if b.endswith("_z") else "X"
        return _mk_wood(nm, light, dark, ax, rough=0.62 if root == "tik" else 0.48)
    if b == "lak_front":
        if s["front"] is None:
            light, dark = DREWNO["dab"]
            return _mk_wood(nm, light, dark, "X", rough=0.45)
        return _mk_plain(nm, s["front"], rough=0.38, coat=0.15, coat_r=0.3)
    if b == "lak_szafa":
        if s["szafa"] == "dab":
            light, dark = DREWNO[s["drewno"]]
            return _mk_wood(nm, light, dark, "Z", rough=0.45)
        return _mk_plain(nm, (0.86, 0.85, 0.82) if s["szafa"] == "bialy" else (0.66, 0.62, 0.57), rough=0.4)
    plain = {
        "lak_bialy": ((0.86, 0.85, 0.82), dict(rough=0.35)),
        "lak_czarny": ((0.018, 0.018, 0.019), dict(rough=0.13)),
        "czarny_mat": ((0.025, 0.025, 0.025), dict(rough=0.6)),
        "cokol": ((0.07, 0.07, 0.07), dict(rough=0.6)),
        "emalia": ((0.87, 0.87, 0.86), dict(rough=0.22, coat=0.4, coat_r=0.1)),
        "plastik_czarny": ((0.035, 0.035, 0.037), dict(rough=0.42)),
        "plastik_szary": ((0.30, 0.30, 0.31), dict(rough=0.45)),
        "guma": ((0.03, 0.03, 0.03), dict(rough=0.85)),
        "papier": ((0.88, 0.85, 0.78), dict(rough=0.9)),
        "ekran_proj": ((0.86, 0.86, 0.85), dict(rough=0.95)),
        "nadruk": ((0.30, 0.30, 0.30), dict(rough=0.3)),
        "porcelana": ((0.89, 0.88, 0.85), dict(rough=0.1)),
        "ceramika": ((0.88, 0.88, 0.86), dict(rough=0.07)),
        "stal": ((0.74, 0.74, 0.74), dict(rough=0.28, metal=1.0, aniso=0.5)),
        "chrom": ((0.92, 0.92, 0.92), dict(rough=0.05, metal=1.0)),
        "czarny_metal": ((0.035, 0.035, 0.036), dict(rough=0.45)),
        "mosiadz": ((0.86, 0.68, 0.42), dict(rough=0.24, metal=1.0)),
        "miedz": ((0.88, 0.56, 0.42), dict(rough=0.26, metal=1.0)),
        "aluminium": ((0.80, 0.80, 0.81), dict(rough=0.32, metal=1.0)),
        "zloto": ((0.80, 0.64, 0.36), dict(rough=0.38, metal=1.0)),
        "lustro": ((0.93, 0.93, 0.93), dict(rough=0.015, metal=1.0)),
        "szklo_czarne": ((0.012, 0.012, 0.013), dict(rough=0.05)),
        "palenisko": ((0.06, 0.055, 0.05), dict(rough=0.9)),
        "materac": ((0.86, 0.86, 0.84), dict(rough=0.9, sheen=0.3)),
        "pomarancza": ((0.95, 0.47, 0.06), dict(rough=0.42)),
        "pien": ((0.33, 0.27, 0.21), dict(rough=0.9)),
        "kora": ((0.20, 0.14, 0.10), dict(rough=0.95)),
        "ziemia": ((0.13, 0.10, 0.08), dict(rough=1.0)),
        "terakota": ((0.70, 0.42, 0.29), dict(rough=0.85)),
        "tynk": ((0.88, 0.87, 0.84), dict(rough=0.9)),
        "kamienie": ((0.40, 0.40, 0.39), dict(rough=0.85)),
        "skora": ((0.47, 0.27, 0.15), dict(rough=0.45, coat=0.25, coat_r=0.3)),
        "mata": (s["mata"], dict(rough=0.85)),
    }
    if b in plain:
        col, kw = plain[b]
        bump = {"tynk": 0.15, "kora": 0.6, "ziemia": 0.5, "kamienie": 0.3, "terakota": 0.12, "mata": 0.1,
                "skora": 0.08, "pomarancza": 0.15, "pien": 0.4}.get(b, 0.0)
        return _mk_plain(nm, col, bump=bump, bscale={"pomarancza": 900.0, "kora": 60.0}.get(b, 200.0), **kw)
    if b == "akcent":
        return mat(ctx, s["metal"])
    fab = {
        "tk_obicie": (s["obicie"], dict(sheen=0.35)),
        "tk_akcent0": (s["akcent"][0], dict(sheen=0.45)),
        "tk_akcent1": (s["akcent"][1], dict(sheen=0.45)),
        "tk_akcent2": (s["akcent"][2], dict(sheen=0.45)),
        "posciel": (s["posciel"], dict(rough=0.95, sheen=0.25, weave=170.0, bump=0.12, mel=0.03)),
        "koc": (s["koc"], dict(weave=24.0, bump=0.55, sheen=0.3, mel=0.05)),
        "tk_ciemna": ((0.12, 0.12, 0.13), dict(sheen=0.3, weave=90.0, bump=0.35)),
        "tk_ogrod": (s["ogrod"], dict(sheen=0.15, weave=110.0, bump=0.3)),
        "lina": ((0.80, 0.74, 0.62), dict(sheen=0.1, weave=38.0, bump=0.8, mel=0.05)),
        "boucle": ((0.87, 0.85, 0.80), dict(sheen=0.2, weave=60.0, bump=0.9, mel=0.03)),
        "filc": ((0.43, 0.46, 0.44), dict(sheen=0.2, weave=400.0, bump=0.1, mel=0.05)),
        "plotno": ((0.88, 0.86, 0.80), dict(sheen=0.05, weave=160.0, bump=0.2, mel=0.02)),
        "tk_kolor": (s["sofa2"], dict(sheen=0.5)),
    }
    if b in fab:
        col, kw = fab[b]
        return _mk_fabric(nm, col, **kw)
    if b == "blat":
        return mat(ctx, s["blat"])
    stones = {
        "kwarc": ((0.88, 0.87, 0.85), (0.60, 0.60, 0.60), dict(rough=0.18, vein_k=0.45, coat=0.2)),
        "kwarc_szary": ((0.62, 0.62, 0.61), (0.82, 0.82, 0.80), dict(rough=0.25, vein_k=0.3)),
        "ciemny": ((0.10, 0.10, 0.10), (0.30, 0.30, 0.30), dict(rough=0.32, vein_k=0.3, speck=0.3)),
        "trawertyn": ((0.83, 0.77, 0.67), (0.68, 0.60, 0.50), dict(rough=0.45, vein_k=0.5, stretch=(1, 1, 7))),
        "marmur": ((0.90, 0.89, 0.87), (0.45, 0.45, 0.47), dict(rough=0.12, vein_k=0.6, coat=0.3, vscale=0.9)),
        "lupek": ((0.16, 0.16, 0.17), (0.24, 0.24, 0.25), dict(rough=0.6, vein_k=0.2, stretch=(1, 1, 5))),
    }
    if b in stones:
        base, vein, kw = stones[b]
        return _mk_stone(nm, base, vein, **kw)
    if b == "beton":
        return _mk_concrete(nm, (0.64, 0.63, 0.60))
    if b == "beton_ciemny":
        return _mk_concrete(nm, (0.40, 0.40, 0.39))
    if b == "kamien_kominek":
        return mat(ctx, "beton_ciemny" if s["kominek"] == "beton" else "lupek")
    if b == "szklo":
        return _mk_glass(nm)
    if b == "szklo_cienkie":
        return _mk_thin_glass(nm)
    if b == "szklo_dymione":
        return _mk_thin_glass(nm, (0.55, 0.55, 0.56), 0.04)
    if b == "szklo_butelka":
        return _mk_thin_glass(nm, (0.10, 0.22, 0.12), 0.12)
    if b == "ksiazki":
        return _mk_attr(nm, 0.55, books=True)
    if b == "kolor":
        return _mk_attr(nm, 0.5)
    if b == "folia":
        return _mk_attr(nm, 0.3, metal=0.7)
    if b == "lisc":
        return _mk_attr(nm, 0.38, leaf=True)
    if b == "dywan":
        c1, c2 = DYWAN[s["dywan"]]
        return _mk_rug(nm, c1, c2, s["wzor"], float(a[0]), float(a[1]))
    if b == "obraz":
        return _mk_painting(nm, f"{ctx.seed}:{a[0] if a else 0}")
    if b == "ekran":
        return _mk_screen(nm, False)
    if b == "monitor":
        return _mk_screen(nm, dusk)
    if b == "zarowka":
        return _mk_emit(nm, dusk, (0.88, 0.87, 0.84), 30.0)
    if b == "abazur":
        return _mk_emit(nm, dusk, (0.86, 0.83, 0.77), 1.1, rough=0.9)
    if b == "opal":
        return _mk_emit(nm, dusk, (0.90, 0.90, 0.88), 7.0, rough=0.3)
    if b == "led":
        return _mk_emit(nm, dusk, (0.80, 0.80, 0.80), 14.0, temp=3000.0)
    if b == "ogien":
        return _mk_fire(nm, float(a[0]), float(a[1])) if a else _mk_fire(nm)
    if b == "zar":
        return _mk_embers(nm, dusk)
    if b == "braz":
        return _mk_bronze(nm)
    if b == "perforowana":
        return _mk_pegboard(nm)
    return _mk_plain(nm, (0.6, 0.6, 0.58), rough=0.6)


# ------------------------------------------------------------------ geometria
def _spow(x, e):
    return math.copysign(abs(x) ** e, x)


def _rrect(x0, y0, x1, y1, rc, n=6):
    """Prostokąt o zaokrąglonych narożnikach (CCW)."""
    rc = min(rc, (x1 - x0) / 2 - 1e-4, (y1 - y0) / 2 - 1e-4)
    if rc <= 1e-4:
        return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    pts = []
    for cx, cy, a0 in ((x1 - rc, y0 + rc, -90), (x1 - rc, y1 - rc, 0), (x0 + rc, y1 - rc, 90), (x0 + rc, y0 + rc, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + rc * math.cos(a), cy + rc * math.sin(a)))
    return pts


def _sel(cx, cy, rx, ry, n=32, p=2.0):
    """Superelipsa (p=2 elipsa, większe p – bardziej kwadratowa), CCW."""
    out = []
    for i in range(n):
        a = 2 * math.pi * i / n
        out.append((cx + rx * _spow(math.cos(a), 2 / p), cy + ry * _spow(math.sin(a), 2 / p)))
    return out


def _circle(cx, cy, r, n=24):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _catmull(pts, n=6, closed=True):
    """Gładka krzywa Catmulla-Roma przez punkty."""
    P = [Vector((p[0], p[1])) for p in pts]
    m = len(P)
    out = []
    rng = range(m) if closed else range(m - 1)
    for i in rng:
        p0, p1 = P[(i - 1) % m] if closed else P[max(i - 1, 0)], P[i]
        p2 = P[(i + 1) % m]
        p3 = P[(i + 2) % m] if closed else P[min(i + 2, m - 1)]
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            out.append((q.x, q.y))
    if not closed:
        out.append((P[-1].x, P[-1].y))
    return out


def _island(faces):
    """Wszystkie ściany spójnej bryły (fazowanie przebudowuje ściany – zbieramy je od nowa)."""
    seen = set(faces)
    stack = list(faces)
    while stack:
        f = stack.pop()
        for e in f.edges:
            for g in e.link_faces:
                if g not in seen:
                    seen.add(g)
                    stack.append(g)
    return list(seen)


class MB:
    """Budowa jednej siatki z wielu prymitywów; materiały jako klucze biblioteki `mat`."""

    def __init__(self):
        self.bm = bmesh.new()
        self.keys = []
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self._col = None

    def mi(self, key):
        if key not in self.keys:
            self.keys.append(key)
        return self.keys.index(key)

    def tag(self, faces, key, smooth=False):
        i = self.mi(key)
        for f in faces:
            f.material_index = i
            f.smooth = smooth
        return faces

    def xf(self, faces, M):
        """Przekształca wierzchołki podanych ścian macierzą M."""
        vs = list({v for f in faces for v in f.verts})
        bmesh.ops.transform(self.bm, matrix=M, verts=vs)
        return faces

    def _bevel(self, edges, r, seg, key):
        res = bmesh.ops.bevel(self.bm, geom=edges, offset=r, offset_type="OFFSET", segments=seg, profile=0.5,
                              affect="EDGES", clamp_overlap=True)
        return self.tag(res["faces"], key, smooth=True)

    def box(self, x0, y0, z0, x1, y1, z1, key, r=0.003, seg=2):
        """Prostopadłościan z fazowanymi (zaokrąglonymi) krawędziami."""
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        if min(sx, sy, sz) < 1e-5:
            return []
        M = Matrix.LocRotScale(Vector(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)), None, Vector((sx, sy, sz)))
        vs = bmesh.ops.create_cube(self.bm, size=1.0, matrix=M)["verts"]
        fs = self.tag(list({f for v in vs for f in v.link_faces}), key)
        r = min(r, 0.45 * min(sx, sy, sz))
        if seg and r > 0.0003:
            fs = _island(self._bevel(list({e for v in vs for e in v.link_edges}), r, seg, key))
        return fs

    def box_hole(self, x0, y0, z0, x1, y1, z1, key, hole, depth, key_in, r=0.004):
        """Prostopadłościan z prostokątną wnęką we froncie (−Y); hole = (xa, za, xb, zb)."""
        bm = self.bm
        fs = self.box(x0, y0, z0, x1, y1, z1, key, r=r, seg=2)
        bm.normal_update()
        front = max((f for f in fs if f.normal.y < -0.999), key=lambda f: f.calc_area())
        ring = bmesh.ops.inset_region(bm, faces=[front], thickness=0.03, depth=0.0)["faces"]
        xa, za, xb, zb = hole
        for v in front.verts:
            v.co.x = xa if v.co.x < (x0 + x1) / 2 else xb
            v.co.z = za if v.co.z < (z0 + z1) / 2 else zb
        ex = bmesh.ops.extrude_face_region(bm, geom=[front])
        nv = [g for g in ex["geom"] if isinstance(g, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0.0, depth, 0.0), verts=nv)
        if front.is_valid:                      # oryginalna ściana zostaje w otworze – usuwamy ją
            bmesh.ops.delete(bm, geom=[front], context="FACES_ONLY")
        cav = list({f for v in nv for f in v.link_faces})
        allf = _island(cav)
        bmesh.ops.recalc_face_normals(bm, faces=allf)
        self.tag(cav, key_in)
        return allf

    def prism(self, pts, z0, z1, key, r=0.0, seg=2, smooth=False, top=None, cap=(True, True)):
        """Graniastosłup (lub ścięty ostrosłup, gdy `top`) z wielokąta CCW; faza krawędzi den."""
        bm = self.bm
        top = top or pts
        n = len(pts)
        vb = [bm.verts.new((x, y, z0)) for x, y in pts]
        vt = [bm.verts.new((x, y, z1)) for x, y in top]
        side = [bm.faces.new((vb[i], vb[(i + 1) % n], vt[(i + 1) % n], vt[i])) for i in range(n)]
        self.tag(side, key, smooth)
        caps = []
        if cap[0]:
            caps.append(bm.faces.new(list(reversed(vb))))
        if cap[1]:
            caps.append(bm.faces.new(vt))
        self.tag(caps, key)
        fs = side + caps
        if seg and r > 0.0003 and caps:
            es = list({e for f in caps for e in f.edges})
            fs = _island(self._bevel(es, min(r, 0.45 * abs(z1 - z0)), seg, key))
        return fs

    def rbox(self, x0, y0, z0, x1, y1, z1, key, rc=0.03, r=0.003, seg=2, n=6):
        """Płyta o zaokrąglonych narożnikach w rzucie (rc) i fazowanych krawędziach (r)."""
        return self.prism(_rrect(x0, y0, x1, y1, rc, n), z0, z1, key, r=r, seg=seg, smooth=rc > 0.004)

    def cyl(self, x, y, z0, z1, rad, key, n=24, r=0.0, seg=2, rad2=None):
        pts = _circle(x, y, rad, n)
        top = None if rad2 is None else _circle(x, y, rad2, n)
        return self.prism(pts, z0, z1, key, r=r, seg=seg, smooth=True, top=top)

    def lathe(self, prof, key, n=32, x=0.0, y=0.0, z=0.0, smooth=True, keys=None):
        """Bryła obrotowa; prof = [(r, z)] obchodzony tak, by materiał był po lewej (normalne na prawo)."""
        bm = self.bm
        ang = [2 * math.pi * i / n for i in range(n)]
        rings = []
        for rr, zz in prof:
            if rr < 1e-6:
                rings.append([bm.verts.new((x, y, z + zz))])
            else:
                rings.append([bm.verts.new((x + rr * math.cos(t), y + rr * math.sin(t), z + zz)) for t in ang])
        fs = []
        for k in range(len(rings) - 1):
            A, B = rings[k], rings[k + 1]
            cur = []
            if len(A) == 1 and len(B) == 1:
                continue
            for i in range(n):
                j = (i + 1) % n
                if len(A) == 1:
                    cur.append(bm.faces.new((A[0], B[j], B[i])))
                elif len(B) == 1:
                    cur.append(bm.faces.new((A[i], A[j], B[0])))
                else:
                    cur.append(bm.faces.new((A[i], A[j], B[j], B[i])))
            self.tag(cur, keys[k] if keys else key, smooth)
            fs += cur
        return fs

    def surf(self, fn, nu, nv, key, cu=False, cv=False, smooth=True, flip=False):
        """Powierzchnia parametryczna fn(u, v) -> (x, y, z), u, v w [0, 1]; cu/cv – zamknięta."""
        bm = self.bm
        U = nu if cu else nu + 1
        V = nv if cv else nv + 1
        vs = [[bm.verts.new(fn(i / nu, j / nv)) for j in range(V)] for i in range(U)]
        fs = []
        for i in range(nu):
            i2 = (i + 1) % U
            for j in range(nv):
                j2 = (j + 1) % V
                q = (vs[i][j], vs[i2][j], vs[i2][j2], vs[i][j2])
                fs.append(bm.faces.new(q[::-1] if flip else q))
        return self.tag(fs, key, smooth)

    def tube(self, pts, rad, key, n=10, cap=True, smooth=True):
        """Rurka wzdłuż łamanej (ramy, kable, wylewki); rad – liczba albo promień w każdym punkcie."""
        P = [Vector(p) for p in pts]
        m = len(P)
        Rr = list(rad) if isinstance(rad, (list, tuple)) else [rad] * m
        Tg = [(P[min(i + 1, m - 1)] - P[max(i - 1, 0)]).normalized() for i in range(m)]
        up = Vector((0, 0, 1)) if abs(Tg[0].z) < 0.9 else Vector((1, 0, 0))
        Ns = [Tg[0].cross(up).normalized()]
        for i in range(1, m):
            q = Ns[-1] - Tg[i] * Ns[-1].dot(Tg[i])
            Ns.append(q.normalized() if q.length > 1e-9 else Ns[-1])
        bm = self.bm
        rings = []
        for i in range(m):
            Bv = Tg[i].cross(Ns[i])
            rings.append([bm.verts.new(P[i] + (Ns[i] * math.cos(2 * math.pi * k / n) + Bv * math.sin(2 * math.pi * k / n)) * Rr[i])
                          for k in range(n)])
        fs = []
        for i in range(m - 1):
            A, Bq = rings[i], rings[i + 1]
            for k in range(n):
                fs.append(bm.faces.new((A[k], A[(k + 1) % n], Bq[(k + 1) % n], Bq[k])))
        self.tag(fs, key, smooth)
        if cap:
            fs += self.tag([bm.faces.new(list(reversed(rings[0]))), bm.faces.new(rings[-1])], key)
        return fs

    def soft(self, hx, hy, hz, key, M=None, e1=0.3, e2=0.15, nu=32, nv=14, puff=0.0, wr=0.0, seed=0):
        """Miękka bryła (superelipsoida): poduchy, materace, siedziska; e1 – profil pionowy, e2 – rzut."""
        bm = self.bm
        rings = []
        for j in range(1, nv):
            ph = -math.pi / 2 + math.pi * j / nv
            cp, sp = _spow(math.cos(ph), e1), _spow(math.sin(ph), e1)
            ring = []
            for i in range(nu):
                th = 2 * math.pi * i / nu + 0.5 * math.pi / nu
                x = hx * cp * _spow(math.cos(th), e2)
                y = hy * cp * _spow(math.sin(th), e2)
                z = hz * sp
                if puff:
                    k = max(0.0, 1 - (x / hx) ** 2) * max(0.0, 1 - (y / hy) ** 2)
                    z += (puff if z > 0 else -0.35 * puff) * k * abs(sp) ** 0.5
                if wr:
                    z += wr * noise.noise(Vector((x * 7 + seed, y * 7, 0.3)))
                ring.append(bm.verts.new((x, y, z)))
            rings.append(ring)
        bot = bm.verts.new((0, 0, -hz - 0.35 * puff))
        top = bm.verts.new((0, 0, hz + puff))
        fs = []
        for k in range(len(rings) - 1):
            A, Bq = rings[k], rings[k + 1]
            for i in range(nu):
                fs.append(bm.faces.new((A[i], A[(i + 1) % nu], Bq[(i + 1) % nu], Bq[i])))
        for i in range(nu):
            fs.append(bm.faces.new((bot, rings[0][(i + 1) % nu], rings[0][i])))
            fs.append(bm.faces.new((rings[-1][i], rings[-1][(i + 1) % nu], top)))
        self.tag(fs, key, True)
        if M is not None:
            self.xf(fs, M)
        return fs

    def pillow(self, w, d, h, key, M, n=12, pinch=0.08, p=2.6, wr=0.004, seed=0.0):
        """Poduszka: wypukłe ściany, ostrzejsze rogi; w płaszczyźnie XY, grubość h (oś Z)."""
        bm = self.bm
        top, bot = {}, {}
        for i in range(n + 1):
            u = -1 + 2 * i / n
            for j in range(n + 1):
                v = -1 + 2 * j / n
                x = u * w / 2 * (1 - pinch * (1 - v * v))
                y = v * d / 2 * (1 - pinch * (1 - u * u))
                f = max(0.0, (1 - abs(u) ** p) * (1 - abs(v) ** p)) ** 0.55
                dz = wr * noise.noise(Vector((x * 9 + seed, y * 9, 1.7)))
                if i in (0, n) or j in (0, n):
                    top[i, j] = bot[i, j] = bm.verts.new((x, y, dz))
                else:
                    top[i, j] = bm.verts.new((x, y, h / 2 * f + dz))
                    bot[i, j] = bm.verts.new((x, y, -h / 2 * f + dz))
        fs = []
        for i in range(n):
            for j in range(n):
                fs.append(bm.faces.new((top[i, j], top[i + 1, j], top[i + 1, j + 1], top[i, j + 1])))
                fs.append(bm.faces.new((bot[i, j + 1], bot[i + 1, j + 1], bot[i + 1, j], bot[i, j])))
        self.tag(fs, key, True)
        self.xf(fs, M)
        return fs

    def torus(self, x, y, z, Rr, r, key, nu=32, nv=8):
        def f(u, v):
            a, b = 2 * math.pi * u, 2 * math.pi * v
            return (x + (Rr + r * math.cos(b)) * math.cos(a), y + (Rr + r * math.cos(b)) * math.sin(a), z + r * math.sin(b))
        return self.surf(f, nu, nv, key, cu=True, cv=True)

    def sphere(self, x, y, z, r, key, n=16, sz=1.0):
        prof = [(0.0, -r * sz)] + [(r * math.cos(a), r * sz * math.sin(a))
                                   for a in [-math.pi / 2 + math.pi * k / (n // 2) for k in range(1, n // 2)]] + [(0.0, r * sz)]
        return self.lathe(prof, key, n=n, x=x, y=y, z=z)

    def basin(self, pts, z0, z1, key, r=0.0):
        """Misa/zlew: dno i ściany widoczne od środka (bez góry)."""
        bm = self.bm
        n = len(pts)
        vb = [bm.verts.new((x, y, z0)) for x, y in pts]
        vt = [bm.verts.new((x, y, z1)) for x, y in pts]
        side = [bm.faces.new((vt[i], vt[(i + 1) % n], vb[(i + 1) % n], vb[i])) for i in range(n)]
        bot = bm.faces.new(vb)
        self.tag(side, key, True)
        self.tag([bot], key)
        fs = side + [bot]
        if r > 0.0003:
            fs = _island(self._bevel(list(bot.edges), r, 2, key))
        return fs

    def colbox(self, x0, y0, z0, x1, y1, z1, key, cols, M=None, uv_front=False):
        """Szybki prostopadłościan bez fazy; kolory ścian w atrybucie 'kolor'.
        cols: kolor (RGBA liniowe) albo słownik {'-y': ..., '+z': ..., 'reszta': ...}."""
        bm = self.bm
        if self._col is None:
            self._col = bm.loops.layers.float_color.get("kolor") or bm.loops.layers.float_color.new("kolor")
        v = [bm.verts.new(c) for c in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                                       (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1))]
        quads = {"-z": (0, 3, 2, 1), "+z": (4, 5, 6, 7), "-y": (0, 1, 5, 4), "+y": (2, 3, 7, 6),
                 "-x": (3, 0, 4, 7), "+x": (1, 2, 6, 5)}
        fs = []
        i = self.mi(key)
        for k, q in quads.items():
            f = bm.faces.new([v[j] for j in q])
            f.material_index = i
            c = cols.get(k, cols.get("reszta")) if isinstance(cols, dict) else cols
            for lp in f.loops:
                lp[self._col] = c
            if uv_front and k == "-y":
                for lp, uvv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                    lp[self.uv].uv = uvv
            fs.append(f)
        if M is not None:
            self.xf(fs, M)
        return fs

    def setcol(self, faces, col):
        if self._col is None:
            self._col = self.bm.loops.layers.float_color.get("kolor") or self.bm.loops.layers.float_color.new("kolor")
        for f in faces:
            for lp in f.loops:
                lp[self._col] = col
        return faces

    def mesh(self, ctx, name):
        me = bpy.data.meshes.new(name)
        self.bm.normal_update()
        self.bm.to_mesh(me)
        self.bm.free()
        for k in self.keys:
            me.materials.append(mat(ctx, k))
        return me


def _lin(a, b, n, end=True):
    return [a + (b - a) * k / n for k in range(n + (1 if end else 0))]


def _drape(mb, key, x0, x1, y0, y1, ztop, zlow, r=0.05, th=0.03, sides=True, foot=True, nf=26, wr=0.012, seed=0.0,
           flare=0.04, puff=0.0):
    """Kołdra/koc: płaska góra (ztop) nad x0..x1, y0..y1 (y1 – strona głowy), zaokrąglona krawędź (r),
    zwis po bokach i w nogach (y0) do zlow; w narożnikach materiał układa się w fałdę.  Grubość th."""
    q = math.pi * r / 2
    hv = max(0.0, (ztop - r) - zlow)
    fx0, fx1 = (x0 + r, x1 - r) if sides else (x0, x1)
    fy0, fy1 = (y0 + r) if foot else y0, y1
    xs = []
    if sides:
        xs += _lin(fx0 - q - hv, fx0 - q, 5, False) + _lin(fx0 - q, fx0, 7, False)
    xs += _lin(fx0, fx1, nf, not sides)
    if sides:
        xs += _lin(fx1, fx1 + q, 7, False) + _lin(fx1 + q, fx1 + q + hv, 5, True)
    ys = []
    if foot:
        ys += _lin(fy0 - q - hv, fy0 - q, 5, False) + _lin(fy0 - q, fy0, 7, False)
    ys += _lin(fy0, fy1, max(4, int(nf * (fy1 - fy0) / max(0.1, fx1 - fx0))), True)

    def f(px, py):
        qx, qy = min(max(px, fx0), fx1), min(max(py, fy0), fy1)
        dx, dy = px - qx, py - qy
        dd = math.hypot(dx, dy)
        ux = uy = 0.0
        if dd < 1e-9:
            x, y, z, hk = px, py, ztop, 0.0
        else:
            ux, uy = dx / dd, dy / dd
            if dd <= q:
                off, z = r * math.sin(dd / r), ztop - r + r * math.cos(dd / r)
            else:
                off, z = r + flare * (dd - q), ztop - r - (dd - q)
            x, y = qx + ux * off, qy + uy * off
            hk = min(1.0, dd / (q + 0.05))
        if hk == 0.0 and puff:
            # góra lekko wypukła (wypełnienie kołdry)
            ux_ = (px - (fx0 + fx1) / 2) / max(1e-6, (fx1 - fx0) / 2)
            uy_ = (py - fy0) / max(1e-6, fy1 - fy0)
            z += puff * max(0.0, 1 - ux_ ** 4) * max(0.0, 1 - (2 * uy_ - 1) ** 4)
        z = max(z, zlow)
        n1 = noise.noise_vector(Vector((x * 2.6 + seed, y * 2.6, z * 2.6)))
        n2 = noise.noise_vector(Vector((x * 7.5 + seed, y * 7.5, z * 7.5 + 3.0)))
        a = wr * (0.3 + 0.7 * hk)
        k2 = 0.35
        if hk > 0.0:
            # fałdy zwisu: tylko na zewnątrz (nie wchodzą w materac) i wzdłuż krawędzi
            out_ = (0.5 + 0.5 * n1.x) * a * hk
            tan_ = (n1.y + k2 * n2.y) * a * hk
            x += ux * out_ - uy * tan_
            y += uy * out_ + ux * tan_
        return Vector((x, y, z + (n1.z + k2 * n2.z) * a * (0.5 + 0.5 * hk)))

    bm = mb.bm
    V = [[bm.verts.new(f(px, py)) for py in ys] for px in xs]
    fs = []
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            fs.append(bm.faces.new((V[i][j], V[i + 1][j], V[i + 1][j + 1], V[i][j + 1])))
    mb.tag(fs, key, True)
    res = bmesh.ops.solidify(bm, geom=fs, thickness=th)
    new = [g for g in res["geom"] if isinstance(g, bmesh.types.BMFace)]
    mb.tag(new, key, True)
    return fs + new


# ------------------------------------------------------------------ modele glTF
def _glb(ctx, fn):
    """Importuje model raz na scenę; zwraca (części [(nazwa, siatka, macierz)], (min, max))."""
    key = ("m3d_glb", fn)
    got = ctx.cache.get(key)
    if got is not None:
        return got
    sc = bpy.context.scene
    keep = (sc.frame_start, sc.frame_end, sc.frame_current, sc.render.fps, sc.render.fps_base, sc.camera)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=zasob("modele/" + fn))
    bpy.context.view_layer.update()
    new = [o for o in bpy.data.objects if o not in before]
    parts = []
    mn, mx = Vector((1e9, 1e9, 1e9)), Vector((-1e9, -1e9, -1e9))
    for o in new:
        if o.type != "MESH" or "firefly" in o.name:
            continue
        me = o.data
        me.use_fake_user = True
        mw = o.matrix_world.copy()
        parts.append((o.name, me, mw))
        a = np.empty(len(me.vertices) * 3, dtype=np.float64)
        me.vertices.foreach_get("co", a)
        a = a.reshape(-1, 3) @ np.array(mw)[:3, :3].T + np.array(mw)[:3, 3]
        if len(a):
            mn = Vector(np.minimum(mn, a.min(0)))
            mx = Vector(np.maximum(mx, a.max(0)))
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    sc.frame_start, sc.frame_end, sc.frame_current, sc.render.fps, sc.render.fps_base, sc.camera = keep
    got = (parts, (mn, mx))
    ctx.cache[key] = got
    if fn == "CarConcept.glb":
        _car_paint(ctx, parts)
    return got


def _car_paint(ctx, parts):
    """Samochód: spokojny grafitowy metalik zamiast czerwieni."""
    paint = bpy.data.materials.new("m3d_lakier_auto")
    t = _NT(paint)
    _p(t, col=(0.20, 0.21, 0.22), metal=0.75, rough=0.32, coat=1.0, coat_r=0.03)
    nz = t.noise(t.co(), 2600.0, 2.0, 0.5)
    t.l(t.math("MULTIPLY_ADD", nz.outputs["Fac"], 0.08, 0.28), t.b.inputs["Roughness"])
    trim = _mk_plain("m3d_lakier_auto2", (0.05, 0.05, 0.055), rough=0.25, coat=1.0, coat_r=0.03, metal=0.3)
    inner = _mk_plain("m3d_auto_wnetrze", (0.16, 0.15, 0.14), rough=0.6)
    for _, me, _ in parts:
        for i, m in enumerate(me.materials):
            if m is None:
                continue
            if m.name.startswith("Paint 1"):
                me.materials[i] = paint
            elif m.name.startswith("Paint 2"):
                me.materials[i] = trim
            elif m.name.startswith("Interior 3"):
                me.materials[i] = inner


def _model_mat(ctx, fn, sub):
    parts, _ = _glb(ctx, fn)
    for _, me, _ in parts:
        for m in me.materials:
            if m is not None and sub in m.name:
                return m
    return None


# ------------------------------------------------------------------ budowa elementu
class _B:
    """Kontekst budowy jednego elementu: korzeń, losowość, dodawanie części."""

    def __init__(self, it, ctx, idx):
        self.it, self.ctx, self.idx = it, ctx, idx
        self.st = _styl(ctx)
        self.rnd = random.Random(f"{ctx.seed}:{it.kind}:{idx}:{round(it.cx, 2)}:{round(it.cy, 2)}")
        self.dusk = bool(ctx.dusk)
        room = getattr(it, "room", None)
        self.rk = getattr(room, "kind", "") or ""
        top = getattr(room, "top", None)
        self.ceil = (top - it.z) if top is not None else None
        self.outdoor = self.rk in OUTDOOR
        self.obs = []
        root = bpy.data.objects.new(f"mebel_{it.kind}", None)
        root.empty_display_size = 0.25
        root.location = ctx.to_bl(it.cx, it.cy, it.z)
        root.rotation_euler = (0.0, 0.0, ctx.rot_bl(it.rot))
        ctx.link(root)
        self.root = root
        self.obs.append(root)

    def add(self, ob, M=None):
        ob.parent = self.root
        if M is not None:
            ob.matrix_basis = M
        self.ctx.link(ob)
        self.obs.append(ob)
        return ob

    def mesh(self, mb, name, M=None):
        return self.add(bpy.data.objects.new(name, mb.mesh(self.ctx, "m3d_" + name)), M)

    def inst(self, key, make, M=None, name=None):
        """Kopia siatki proceduralnej wspólnej dla wielu obiektów (krzesła, stołki, lampy)."""
        c = self.ctx.cache.setdefault("m3d_siatki", {})
        k = (key, bool(self.ctx.dusk))
        me = c.get(k)
        if me is None:
            me = make().mesh(self.ctx, "m3d_" + str(key[0] if isinstance(key, tuple) else key))
            c[k] = me
        return self.add(bpy.data.objects.new(name or str(key[0] if isinstance(key, tuple) else key), me), M)

    def model(self, fn, M, skip=(), over=None):
        parts, _ = _glb(self.ctx, fn)
        out = []
        for name, me, mw in parts:
            if any(s in name for s in skip):
                continue
            ob = self.add(bpy.data.objects.new(name, me), M @ mw)
            if over:
                for sl in ob.material_slots:
                    for sub, m in over.items():
                        if sl.material is not None and sub in sl.material.name:
                            sl.link = "OBJECT"
                            sl.material = m
            out.append(ob)
        return out

    def light(self, loc, energy, size=0.04, kind="POINT", temp=WARM, M=None, name="lampa", spot=None, area=None):
        """Światło lampy – tylko wieczorem."""
        if not self.dusk:
            return None
        li = bpy.data.lights.new(name, kind)
        li.energy = energy
        li.use_temperature = True
        li.temperature = temp
        if kind in ("POINT", "SPOT"):
            li.shadow_soft_size = size
        if kind == "SPOT" and spot:
            li.spot_size, li.spot_blend = math.radians(spot[0]), spot[1]
        if kind == "AREA" and area:
            li.shape = "RECTANGLE"
            li.size, li.size_y = area
        ob = bpy.data.objects.new(name, li)
        ob.visible_camera = False          # źródło niewidoczne wprost – świeci klosz/żarówka
        return self.add(ob, M if M is not None else T(*loc))

    def flicker(self, li, k=0.3):
        """Migotanie ognia: sterownik z sum sinusów (bez skryptów Pythona)."""
        if li is None:
            return
        base = li.data.energy
        r = self.rnd
        a, b, c = r.uniform(0.9, 1.4), r.uniform(2.1, 2.9), r.uniform(5.5, 7.5)
        fc = li.data.driver_add("energy")
        fc.driver.type = "SCRIPTED"
        fc.driver.expression = (f"{base:.2f}*(1+{0.5 * k:.3f}*sin(frame*{a:.3f})+{0.3 * k:.3f}*sin(frame*{b:.3f}+1.7)"
                                f"+{0.2 * k:.3f}*sin(frame*{c:.3f}+0.4))")


def _local(p):
    """Punkt starej części (plan, lokalnie) → lokalny układ Blendera."""
    return p[1], -p[2]


# ------------------------------------------------------------------ elementy wspólne
def _book_flat(mb, x, y, z, w, d, t, col, yaw=0.0):
    """Książka leżąca (album): okładka w kolorze, kartki od strony grzbietu przeciwnej."""
    page = lin((0.88, 0.85, 0.78)) + (0.0,)
    c = lin(col) + (0.0,)
    M = T(x, y, z) @ R("Z", yaw)
    mb.colbox(-w / 2, -d / 2, 0, w / 2, d / 2, 0.003, "ksiazki", c, M=M)
    mb.colbox(-w / 2, -d / 2, t - 0.003, w / 2, d / 2, t, "ksiazki", c, M=M)
    mb.colbox(-w / 2, -d / 2, 0.003, -w / 2 + 0.004, d / 2, t - 0.003, "ksiazki", c, M=M)
    mb.colbox(-w / 2 + 0.004, -d / 2 + 0.003, 0.003, w / 2 - 0.003, d / 2 - 0.003, t - 0.003, "ksiazki", page, M=M)


def _book_stack(mb, rnd, x, y, z, n=3, big=True):
    h = 0.0
    for i in range(n):
        w = rnd.uniform(0.26, 0.33) if big else rnd.uniform(0.15, 0.22)
        d = w * rnd.uniform(0.72, 0.85)
        t = rnd.uniform(0.018, 0.035)
        _book_flat(mb, x + rnd.uniform(-0.01, 0.01), y + rnd.uniform(-0.01, 0.01), z + h, w, d, t,
                   rnd.choice(KSIAZKI), rnd.uniform(-8, 8))
        h += t
    return h


def _vase(mb, x, y, z, h, r, key, kind=0):
    """Wazon / dzbanek z toczenia (ścianka 4 mm)."""
    if kind == 0:   # bańka z szyjką
        o = [(0.0, 0.0), (r * 0.62, 0.0), (r * 0.95, h * 0.18), (r, h * 0.42), (r * 0.70, h * 0.72), (r * 0.40, h * 0.88),
             (r * 0.42, h)]
    elif kind == 1:  # walec lekko zwężony
        o = [(0.0, 0.0), (r * 0.85, 0.0), (r, h * 0.12), (r * 0.94, h * 0.85), (r * 0.88, h)]
    else:            # czarka
        o = [(0.0, 0.0), (r * 0.45, 0.0), (r * 0.8, h * 0.35), (r, h)]
    th = 0.004
    inner = [(max(rr - th, 0.0), zz) for rr, zz in reversed(o[2:])] + [(0.0, h * 0.3 if kind != 2 else th)]
    prof = o + [(o[-1][0] - th * 0.5, h + 0.001)] + inner
    return mb.lathe(prof, key, n=28, x=x, y=y, z=z)


def _bowl(mb, x, y, z, r, h, key):
    prof = [(0.0, 0.0), (r * 0.45, 0.0), (r * 0.82, h * 0.45), (r, h), (r - 0.005, h + 0.002), (r * 0.78, h * 0.45 + 0.004),
            (r * 0.4, 0.006), (0.0, 0.006)]
    return mb.lathe(prof, key, n=32, x=x, y=y, z=z)


def _stems(mb, x, y, z, h, n, rnd, key="pien"):
    """Gałązki suszu w wazonie."""
    for i in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        lean = rnd.uniform(0.05, 0.22)
        top = (x + math.cos(a) * lean * h, y + math.sin(a) * lean * h, z + h * rnd.uniform(0.8, 1.1))
        mid = (x + math.cos(a) * lean * h * 0.4, y + math.sin(a) * lean * h * 0.4, z + h * 0.5)
        mb.tube([(x, y, z), mid, top], 0.0025, key, n=5, cap=False)


def _plant_small(mb, rnd, x, y, z, r=0.07, h=0.12):
    """Mała roślina w doniczce (sukulent/zioło) z liści-elips."""
    mb.lathe([(0.0, 0.0), (r * 0.8, 0.0), (r, h * 0.9), (r * 1.05, h), (r * 0.95, h), (0.0, h - 0.01)],
             "terakota" if rnd.random() < 0.5 else "kamionka", n=20, x=x, y=y, z=z)
    for i in range(int(14 * r / 0.07)):
        a = rnd.uniform(0, 2 * math.pi)
        tilt = rnd.uniform(15, 60)
        L = rnd.uniform(0.5, 1.0) * r * 1.4
        fs = mb.soft(L / 2, L / 7, L / 25, "lisc", M=T(x, y, z + h) @ R("Z", math.degrees(a)) @ R("Y", -tilt) @ T(L / 2, 0, 0),
                     e1=0.6, e2=0.7, nu=10, nv=5)
        mb.setcol(fs, lin((0.20 + rnd.uniform(-0.04, 0.04), 0.36 + rnd.uniform(-0.05, 0.05), 0.12)) + (1.0,))


def _pendant(B, x, y, zb, style=None):
    """Lampa wisząca: klosz z dolną krawędzią na wysokości zb, kabel do sufitu, rozeta."""
    style = style or B.st["lampa"]
    ceil = B.ceil
    key = ("lampa_wiszaca", style)

    def make():
        mb = MB()
        m_out = "akcent" if style in ("kopula", "stozek") else "czarny_metal"
        if style == "kopula":
            R_, H = 0.20, 0.17
            prof = [(R_, 0.0)] + [(R_ * math.cos(a) + 0.0, H * math.sin(a)) for a in [math.radians(t) for t in (15, 35, 55, 75)]]
            prof += [(0.03, H + 0.005), (0.03, H + 0.04), (0.0, H + 0.045)]
            inner = [(0.0, H - 0.005), (R_ * 0.25, H - 0.006)] + [(R_ * math.cos(a) - 0.003, H * math.sin(a) - 0.003)
                                                                 for a in [math.radians(t) for t in (75, 55, 35, 15)]] + [(R_ - 0.003, 0.0)]
            mb.lathe(prof + [(0.0, H + 0.045)], m_out, n=40)
            mb.lathe(list(reversed(inner)), "lak_bialy", n=40)
            mb.sphere(0, 0, 0.06, 0.045, "zarowka", n=16)
        elif style == "stozek":
            prof = [(0.17, 0.0), (0.03, 0.26), (0.018, 0.30), (0.0, 0.30)]
            mb.lathe(prof, m_out, n=40)
            mb.lathe([(0.0, 0.258), (0.028, 0.255), (0.167, 0.0)], "lak_bialy", n=40)
            mb.sphere(0, 0, 0.07, 0.035, "zarowka", n=14)
        elif style == "kula":
            mb.sphere(0, 0, 0.16, 0.16, "opal", n=28)
            mb.cyl(0, 0, 0.31, 0.36, 0.025, "akcent", n=16)
        else:   # len: walec lniany
            mb.lathe([(0.19, 0.0), (0.19, 0.25), (0.0, 0.25)], "abazur", n=40)
            mb.lathe([(0.0, 0.245), (0.185, 0.245), (0.185, 0.003)], "abazur", n=40)
            mb.sphere(0, 0, 0.11, 0.04, "zarowka", n=14)
        return mb

    B.inst(key, make, T(x, y, zb), "lampa_wiszaca")
    top = {"kopula": 0.215, "stozek": 0.30, "kula": 0.36, "len": 0.25}[style]
    if ceil is not None and ceil > zb + top + 0.05:
        mb = MB()
        mb.cyl(x, y, zb + top, ceil - 0.02, 0.0022, "czarny_metal", n=6)
        mb.cyl(x, y, ceil - 0.025, ceil, 0.055, "akcent" if style != "len" else "lak_bialy", n=24, r=0.003)
        B.mesh(mb, "kabel")
    zl = zb + {"kopula": 0.06, "stozek": 0.07, "kula": 0.16, "len": 0.11}[style]
    B.light((x, y, zl), 45.0 if style != "kula" else 55.0, size=0.05, name="lampa_wiszaca")


def _ns(mb, x0, y0, x1, y1, h, key, drawers=2, handle="akcent", legs=True):
    """Szafka nocna/komoda z szufladami (szczeliny 3 mm)."""
    zl = 0.12 if legs else 0.0
    if legs:
        for sx in (x0 + 0.03, x1 - 0.03):
            for sy in (y0 + 0.03, y1 - 0.03):
                mb.tube([(sx, sy, 0.0), (sx, sy, zl + 0.01)], [0.011, 0.014], "drewno_z", n=10)
    mb.box(x0, y0 + 0.018, zl, x1, y1, h, key, r=0.003)
    g = 0.003
    hh = (h - zl - g * (drawers + 1)) / drawers
    for i in range(drawers):
        z0 = zl + g + i * (hh + g)
        mb.box(x0 + g, y0, z0, x1 - g, y0 + 0.019, z0 + hh, key, r=0.002)
        if handle:
            cx = (x0 + x1) / 2
            mb.box(cx - 0.05, y0 - 0.012, z0 + hh * 0.62, cx + 0.05, y0 + 0.002, z0 + hh * 0.62 + 0.012, handle, r=0.003)


def _table_lamp(B, x, y, z, s=0.85):
    """Lampka nocna (IridescenceLamp) z żarówką wieczorem."""
    B.model("IridescenceLamp.glb", T(x, y, z) @ Sc(s))
    B.light((x, y, z + 0.34 * s), 22.0, size=0.05, name="lampka")


def _plant_model(B, x, y, z, height, yaw=0.0, pot=True):
    parts, (mn, mx) = _glb(B.ctx, "DiffuseTransmissionPlant.glb")
    s = height / (mx.z - mn.z)
    M = T(x, y, z) @ R("Z", yaw) @ Sc(s)
    if pot:
        return B.model("DiffuseTransmissionPlant.glb", M)
    return B.model("DiffuseTransmissionPlant.glb", T(0, 0, -0.30 * s) @ M, skip=("pot", "dirt"))


# ------------------------------------------------------------------ salon
def _sofa(B):
    it = B.it
    parts, (mn, mx) = _glb(B.ctx, "GlamVelvetSofa.glb")
    W0, D0 = mx.x - mn.x, mx.y - mn.y
    sx, sy = min(1.4, it.w / W0), min(1.12, it.d / D0)
    M = Sc(sx, sy, 1.0) @ T(-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z)
    n = B.ctx.cache.get("m3d_nsofa", 0)
    B.ctx.cache["m3d_nsofa"] = n + 1
    col = B.st["sofa"] if n == 0 else B.st["sofa2"]
    tint = B.ctx.cache.get(("m3d_welur", col))
    if tint is None:
        src = _model_mat(B.ctx, "GlamVelvetSofa.glb", "fabric")
        tint = _mk_velvet(f"m3d_welur_{len(B.ctx.cache)}", src, col)
        B.ctx.cache[("m3d_welur", col)] = tint
    B.model("GlamVelvetSofa.glb", M, over={"fabric": tint})
    # poduszki oparte o oparcie (pozycje zmierzone na modelu)
    mb = MB()
    for (px, py, yaw), key, sz in (((0.56, 0.21, -26.0), "tk_akcent0", 0.46), ((-0.40, 0.35, 5.0), "tk_akcent1", 0.43),
                                   ((-0.78, 0.30, -4.0), "tk_akcent0", 0.40)):
        if key == "tk_akcent0" and px < 0 and it.w < 2.4:
            continue
        p = M @ Vector((px, py, 0.0))
        yaw2 = math.degrees(math.atan2(math.sin(math.radians(yaw)) * sy, math.cos(math.radians(yaw)) * sx))
        mb.pillow(sz, sz, 0.15, key, T(p.x, p.y, 0.445 + sz * 0.45) @ R("Z", yaw2) @ R("X", 72.0), seed=px * 10)
    B.mesh(mb, "poduszki")


def _fotel(B):
    it = B.it
    parts, (mn, mx) = _glb(B.ctx, "SheenChair.glb")
    s = min(1.05, it.w / (mx.x - mn.x), it.d / (mx.y - mn.y))
    M = Sc(s) @ T(-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z)
    col = B.st["akcent"][2] if B.rk in ("salon", "salon_kuchnia") else B.st["obicie"]
    tint = B.ctx.cache.get(("m3d_fotel", col))
    if tint is None:
        src = _model_mat(B.ctx, "SheenChair.glb", "fabric Mystere Mango")
        tint = _mk_velvet(f"m3d_fotel_{len(B.ctx.cache)}", src, col, dark=0.7)
        B.ctx.cache[("m3d_fotel", col)] = tint
    B.model("SheenChair.glb", M, skip=("label",), over={"fabric": tint})


def _stolik(B):
    it, r = B.it, B.rnd
    rnd_ = it.parts[0][0] == "cyl"
    style = B.st["stolik"]
    H = 0.40 if it.w > 0.7 else 0.48
    mb = MB()
    wood = "drewno"
    if rnd_:
        Rr = it.w / 2 - 0.01
        if style == "kamien":
            mb.cyl(0, 0, H - 0.025, H, Rr, "trawertyn", n=56, r=0.004)
            mb.cyl(0, 0, 0.0, H - 0.025, Rr * 0.42, "trawertyn", n=40, r=0.003)
        else:
            top = "czarny_metal" if style == "czarny" else wood
            mb.cyl(0, 0, H - 0.028, H, Rr, top, n=56, r=0.004)
            for k in range(3):
                a = math.radians(90 + 120 * k)
                mb.tube([(math.cos(a) * Rr * 0.62, math.sin(a) * Rr * 0.62, 0.0),
                         (math.cos(a) * Rr * 0.5, math.sin(a) * Rr * 0.5, H - 0.028)],
                        [0.012, 0.018] if style != "czarny" else 0.009, "drewno_z" if style != "czarny" else "czarny_metal", n=10)
            if style == "czarny":
                mb.cyl(0, 0, 0.12, 0.135, Rr * 0.6, wood, n=40, r=0.003)
        zt = H
        sx, sy = Rr * 0.6, Rr * 0.6
    else:
        W, D = it.w - 0.02, it.d - 0.02
        if style == "kamien":
            mb.rbox(-W / 2, -D / 2, H - 0.03, W / 2, D / 2, H, "trawertyn", rc=0.05, r=0.005)
            for sxn in (-1, 1):
                mb.box(sxn * W * 0.30 - 0.07, -D / 2 + 0.06, 0, sxn * W * 0.30 + 0.07, D / 2 - 0.06, H - 0.03, "trawertyn", r=0.004)
        elif style == "czarny":
            mb.rbox(-W / 2, -D / 2, H - 0.02, W / 2, D / 2, H, wood, rc=0.02, r=0.004)
            t_ = 0.018
            for sxn in (-1, 1):
                for syn in (-1, 1):
                    x, y = sxn * (W / 2 - 0.03), syn * (D / 2 - 0.03)
                    mb.box(x - t_ / 2, y - t_ / 2, 0, x + t_ / 2, y + t_ / 2, H - 0.02, "czarny_metal", r=0.002)
            for z in (0.12, H - 0.04):
                for syn in (-1, 1):
                    y = syn * (D / 2 - 0.03)
                    mb.box(-W / 2 + 0.03, y - t_ / 2, z, W / 2 - 0.03, y + t_ / 2, z + 0.02, "czarny_metal", r=0.002)
                for sxn in (-1, 1):
                    x = sxn * (W / 2 - 0.03)
                    mb.box(x - t_ / 2, -D / 2 + 0.03, z, x + t_ / 2, D / 2 - 0.03, z + 0.02, "czarny_metal", r=0.002)
            mb.box(-W / 2 + 0.04, -D / 2 + 0.04, 0.14, W / 2 - 0.04, D / 2 - 0.04, 0.152, "szklo_dymione", r=0.002)
        else:
            mb.rbox(-W / 2, -D / 2, H - 0.032, W / 2, D / 2, H, wood, rc=0.035, r=0.005)
            for sxn in (-1, 1):
                for syn in (-1, 1):
                    x, y = sxn * (W / 2 - 0.08), syn * (D / 2 - 0.07)
                    mb.tube([(x * 1.03, y * 1.04, 0.0), (x, y, H - 0.032)], [0.015, 0.021], "drewno_z", n=12)
            mb.rbox(-W / 2 + 0.1, -D / 2 + 0.09, 0.13, W / 2 - 0.1, D / 2 - 0.09, 0.15, wood, rc=0.02, r=0.003)
        zt = H
        sx, sy = W / 2 - 0.2, D / 2 - 0.15
    # na blacie: albumy i miska / wazon
    if it.w > 0.7:
        _book_stack(mb, r, -sx * 0.45, -sy * 0.15, zt, n=r.choice((2, 3)), big=True)
        if r.random() < 0.5:
            _bowl(mb, sx * 0.55, sy * 0.2, zt, 0.11, 0.07, "kamionka")
        else:
            _vase(mb, sx * 0.55, sy * 0.25, zt, 0.24, 0.07, "kamionka", kind=r.choice((0, 1)))
            _stems(mb, sx * 0.55, sy * 0.25, zt + 0.12, 0.35, 6, r)
    else:
        _book_stack(mb, r, 0, 0, zt, n=2, big=False)
    B.mesh(mb, "stolik")


def _dywan(B):
    it = B.it
    w, d = it.w, it.d
    mb = MB()
    mb.rbox(-w / 2, -d / 2, 0.0, w / 2, d / 2, 0.012, f"dywan:{w:.2f}:{d:.2f}", rc=0.03, r=0.004, seg=2)
    B.mesh(mb, "dywan")


def _rtv(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    mb = MB()
    H = 0.42
    wood = "drewno"
    # szafka wisząca nisko: korpus + fronty z frezowanymi listwami
    mb.box(-w / 2, -d / 2 + 0.02, 0.10, w / 2, d / 2, H, wood, r=0.004)
    n = max(2, round(w / 0.55))
    fw = (w - 0.003 * (n + 1)) / n
    for i in range(n):
        x0 = -w / 2 + 0.003 + i * (fw + 0.003)
        nl = int(fw / 0.032)
        for k in range(nl):
            xa = x0 + k * fw / nl
            mb.box(xa + 0.0015, -d / 2, 0.103, xa + fw / nl - 0.0015, -d / 2 + 0.021, H - 0.003, "drewno_z", r=0.004, seg=2)
    for sxn in (-1, 1):
        mb.box(sxn * (w / 2 - 0.12) - 0.03, -d / 2 + 0.08, 0.0, sxn * (w / 2 - 0.12) + 0.03, d / 2 - 0.08, 0.10, "czarny_metal", r=0.002)
    # telewizor 65"
    tw = min(1.45, w - 0.3)
    th = tw * 9 / 16
    ty = d / 2 - 0.08
    zt = H + 0.25
    mb.box(-tw / 2, ty - 0.012, zt, tw / 2, ty + 0.012, zt + th, "plastik_czarny", r=0.003)
    mb.box(-tw / 2 + 0.006, ty - 0.0135, zt + 0.006, tw / 2 - 0.006, ty - 0.012, zt + th - 0.006, "ekran", r=0.0)
    mb.box(-0.15, ty - 0.01, H, 0.15, ty + 0.08, H + 0.012, "plastik_czarny", r=0.003)
    mb.box(-0.025, ty + 0.0, H, 0.025, ty + 0.03, zt + 0.1, "plastik_czarny", r=0.003)
    # soundbar i dekoracje
    mb.rbox(-0.45, -d / 2 + 0.08, H, 0.45, -d / 2 + 0.17, H + 0.06, "tk_ciemna", rc=0.03, r=0.01)
    _vase(mb, w / 2 - 0.25, 0.0, H, 0.30, 0.08, "kamionka", kind=0)
    _stems(mb, w / 2 - 0.25, 0.0, H + 0.2, 0.45, 7, r)
    _book_stack(mb, r, -w / 2 + 0.3, 0.0, H, n=2, big=True)
    B.mesh(mb, "rtv")


def _flames(mb, y0, z0, w, h, rnd, key="ogien"):
    """Kilka skrzyżowanych płaszczyzn z teksturą płomieni (maska w materiale)."""
    bm = mb.bm
    fs = []
    for k, (dy, yaw) in enumerate(((0.13, 8.0), (0.19, -6.0), (0.25, 4.0), (0.19, 70.0))):
        L = w if k < 3 else w * 0.35
        a = math.radians(yaw)
        cx, cy = (rnd.uniform(-0.05, 0.05) if k == 3 else 0.0), y0 + dy
        pts = [(cx - L / 2 * math.cos(a), cy - L / 2 * math.sin(a)), (cx + L / 2 * math.cos(a), cy + L / 2 * math.sin(a))]
        v = [bm.verts.new((pts[0][0], pts[0][1], z0)), bm.verts.new((pts[1][0], pts[1][1], z0)),
             bm.verts.new((pts[1][0], pts[1][1], z0 + h)), bm.verts.new((pts[0][0], pts[0][1], z0 + h))]
        fs.append(bm.faces.new(v))
    return mb.tag(fs, key)


def _kominek(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    mb = MB()
    st = "kamien_kominek"
    H = 1.1
    fw, fz0, fz1, fd = min(0.9, w - 0.4), 0.32, 0.76, 0.34
    y0 = -d / 2
    mb.box_hole(-w / 2, y0, 0.0, w / 2, d / 2, H, st, (-fw / 2, fz0, fw / 2, fz1), fd, "palenisko", r=0.006)
    # komin do sufitu (węższy)
    if B.ceil and B.ceil > H + 0.3:
        mb.box(-w / 2 + 0.2, y0 + 0.12, H, w / 2 - 0.2, d / 2, B.ceil, st, r=0.004)
    # rama z czarnej stali i szyba
    t = 0.025
    for (a, b, c, e) in ((-fw / 2 - t, fz0 - t, fw / 2 + t, fz0), (-fw / 2 - t, fz1, fw / 2 + t, fz1 + t),
                         (-fw / 2 - t, fz0, -fw / 2, fz1), (fw / 2, fz0, fw / 2 + t, fz1)):
        mb.box(a, y0 - 0.006, b, c, y0 + 0.004, e, "czarny_metal", r=0.002)
    mb.box(-fw / 2, y0 - 0.002, fz0, fw / 2, y0 + 0.002, fz1, "szklo_dymione", r=0)
    # polana na ruszcie
    mb.box(-fw * 0.32, y0 + 0.12, fz0, fw * 0.32, y0 + 0.26, fz0 + 0.02, "czarny_metal", r=0.003)
    for k, (dx, dy, yaw, dz) in enumerate(((-0.10, 0.17, 6, 0.0), (0.11, 0.21, -5, 0.0), (0.0, 0.19, 82, 0.07))):
        a = math.radians(yaw)
        L = 0.2 if k < 2 else 0.1
        lz = fz0 + 0.02 + 0.042 + dz
        mb.tube([(dx - L * math.cos(a), y0 + dy - L * math.sin(a), lz), (dx + L * math.cos(a), y0 + dy + L * math.sin(a), lz)],
                0.042, "zar" if B.dusk else "kora", n=12)
    if B.dusk:
        _flames(mb, y0, fz0 + 0.03, min(0.7, fw - 0.1), 0.38, r, key=f"ogien:{fz0 + 0.03:.2f}:0.36")
        li = B.light((0, y0 - 0.25, fz0 + 0.2), 90.0, size=0.2, temp=1900.0, name="ogien")
        li.visible_glossy = False          # bez odbicia źródła w szybie
        B.flicker(li, 0.35)
    B.mesh(mb, "kominek")


# ------------------------------------------------------------------ jadalnia
def _chair_mesh(style, outdoor=False):
    """Krzesło do stołu: front −Y, siedzisko 0,47 m."""
    mb = MB()
    if outdoor:
        wood, wz = "tik", "tik_z"
    else:
        wood, wz = "drewno", "drewno_z"
    if style == "tapicerowane" and not outdoor:
        for sx in (-1, 1):
            mb.tube([(sx * 0.205, -0.20, 0.0), (sx * 0.19, -0.18, 0.43)], [0.012, 0.016], "czarny_metal", n=10)
            mb.tube([(sx * 0.205, 0.22, 0.0), (sx * 0.19, 0.18, 0.43)], [0.012, 0.016], "czarny_metal", n=10)
        mb.soft(0.235, 0.23, 0.035, "tk_obicie", M=T(0, -0.01, 0.462), e1=0.3, e2=0.12, puff=0.008)
        mb.soft(0.225, 0.04, 0.17, "tk_obicie", M=T(0, 0.205, 0.66) @ R("X", -10), e1=0.25, e2=0.25, puff=0.0)
        mb.box(-0.2, -0.19, 0.415, 0.2, 0.19, 0.43, "czarny_metal", r=0.002)
        return mb
    # nogi z drewna, tylne przechodzą w słupki oparcia
    for sx in (-1, 1):
        mb.tube([(sx * 0.205, -0.205, 0.0), (sx * 0.19, -0.18, 0.43)], [0.013, 0.018], wz, n=10)
        mb.tube([(sx * 0.20, 0.225, 0.0), (sx * 0.19, 0.185, 0.43), (sx * 0.185, 0.215, 0.79)], [0.013, 0.018, 0.014], wz, n=10)
        mb.tube([(sx * 0.198, -0.19, 0.17), (sx * 0.197, 0.20, 0.17)], 0.008, wz, n=8)
    # oparcie: wygięta listwa
    Rr = 0.55
    pts_o, pts_i = [], []
    for k in range(13):
        x = -0.2 + 0.4 * k / 12
        y = 0.215 + (math.sqrt(Rr * Rr - x * x) - math.sqrt(Rr * Rr - 0.2 * 0.2)) * 1.0
        pts_o.append((x, y + 0.009))
        pts_i.append((x, y - 0.009))
    poly = pts_i + list(reversed(pts_o))
    mb.prism(poly, 0.69, 0.785, wood, r=0.004, seg=2, smooth=True)
    # rama i siedzisko
    mb.box(-0.195, -0.185, 0.395, 0.195, 0.19, 0.43, wood, r=0.003)
    if outdoor:
        for k in range(6):
            y = -0.2 + k * 0.075
            mb.box(-0.215, y, 0.43, 0.215, y + 0.065, 0.45, wood, r=0.004)
    else:
        mb.soft(0.228, 0.225, 0.028, "tk_obicie", M=T(0, -0.005, 0.457), e1=0.3, e2=0.14, puff=0.007)
    return mb


def _chairs_from(it):
    """Środki krzeseł (lokalnie, Blender) z rysunku 2D – razem z krzesłami u szczytu stołu."""
    out = []
    for sh in it.shapes[1:]:
        if sh[0] == "r" and sh[-1] == "fu":
            out.append((sh[1] + sh[3] / 2, -(sh[2] + sh[4] / 2)))
        elif sh[0] == "c" and sh[-1] == "fu":
            out.append((sh[1], -sh[2]))
    return out


def _stol(B):
    it, r, st = B.it, B.rnd, B.st
    p0 = it.parts[0]
    rnd_ = p0[0] == "cyl"
    out = B.outdoor
    zt = 0.755
    mb = MB()
    wood = "tik" if out else "drewno"
    wz = "tik_z" if out else "drewno_z"
    if rnd_:
        Rr = p0[4]
        mb.cyl(0, 0, zt - 0.032, zt, Rr, wood, n=72, r=0.005)
        if out:
            for k in range(4):
                a = math.radians(45 + 90 * k)
                mb.box(math.cos(a) * Rr * 0.55 - 0.025, math.sin(a) * Rr * 0.55 - 0.025, 0, math.cos(a) * Rr * 0.55 + 0.025,
                       math.sin(a) * Rr * 0.55 + 0.025, zt - 0.032, wz, r=0.004)
            mb.cyl(0, 0, 0.3, 0.32, Rr * 0.58, wood, n=40, r=0.003)
        else:
            base = "czarny_metal" if st["stol"] == "plozy" else wood
            mb.lathe([(0.0, 0.0), (Rr * 0.48, 0.0), (Rr * 0.48, 0.012), (Rr * 0.30, 0.03), (0.075, 0.10), (0.06, 0.30),
                      (0.065, zt - 0.20), (0.16, zt - 0.06), (0.18, zt - 0.032), (0.0, zt - 0.032)], base if base != wood else "drewno_z", n=48)
        hx = 0.0
    else:
        TW, TD = p0[4], p0[5]
        hx = TW
        if out:
            mb.box(-TW / 2, -TD / 2, zt - 0.05, TW / 2, TD / 2, zt - 0.03, wood, r=0.003)
            ns = int(TD / 0.1)
            for k in range(ns):
                y0 = -TD / 2 + k * TD / ns
                mb.box(-TW / 2, y0 + 0.004, zt - 0.03, TW / 2, y0 + TD / ns - 0.004, zt, wood, r=0.004)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    mb.box(sx * (TW / 2 - 0.1) - 0.03, sy * (TD / 2 - 0.08) - 0.03, 0, sx * (TW / 2 - 0.1) + 0.03,
                           sy * (TD / 2 - 0.08) + 0.03, zt - 0.05, wz, r=0.005)
        else:
            mb.rbox(-TW / 2, -TD / 2, zt - 0.036, TW / 2, TD / 2, zt, wood, rc=0.012, r=0.006)
            kind = st["stol"]
            if kind == "nogi":
                for sx in (-1, 1):
                    for sy in (-1, 1):
                        x, y = sx * (TW / 2 - 0.09), sy * (TD / 2 - 0.08)
                        mb.prism(_rrect(x - 0.022, y - 0.022, x + 0.022, y + 0.022, 0.008, 3), 0.0, zt - 0.036, wz,
                                 top=_rrect(x - 0.032, y - 0.032, x + 0.032, y + 0.032, 0.01, 3), smooth=True)
                for sy in (-1, 1):
                    y = sy * (TD / 2 - 0.085)
                    mb.box(-TW / 2 + 0.12, y - 0.011, zt - 0.11, TW / 2 - 0.12, y + 0.011, zt - 0.036, wood, r=0.003)
                for sx in (-1, 1):
                    x = sx * (TW / 2 - 0.095)
                    mb.box(x - 0.011, -TD / 2 + 0.11, zt - 0.11, x + 0.011, TD / 2 - 0.11, zt - 0.036, wood, r=0.003)
            elif kind == "plozy":
                for sx in (-1, 1):
                    x = sx * (TW / 2 - 0.22)
                    yy = TD / 2 - 0.1
                    mb.box(x - 0.02, -yy, 0.0, x + 0.02, yy, 0.04, "czarny_metal", r=0.003)
                    mb.box(x - 0.02, -yy + 0.05, zt - 0.076, x + 0.02, yy - 0.05, zt - 0.036, "czarny_metal", r=0.003)
                    for sy in (-1, 1):
                        y = sy * (yy - 0.03)
                        mb.box(x - 0.02, y - 0.02, 0.04, x + 0.02, y + 0.02, zt - 0.036, "czarny_metal", r=0.003)
            else:   # kozły: dwie lite nogi płytowe + belka
                for sx in (-1, 1):
                    x = sx * (TW / 2 - 0.22)
                    mb.box(x - 0.03, -TD / 2 + 0.12, 0.0, x + 0.03, TD / 2 - 0.12, zt - 0.036, wz, r=0.004)
                mb.box(-TW / 2 + 0.25, -0.03, zt - 0.14, TW / 2 - 0.25, 0.03, zt - 0.08, wood, r=0.003)
    # krzesła
    chairs = _chairs_from(it)
    cst = "drewno" if out else st["krzeslo"]
    half_w, half_d = it.w / 2, it.d / 2
    for (x, y) in chairs:
        ang = math.atan2(y, x)
        dist = math.hypot(x, y)
        # krzesło w obrysie: oparcie najdalej 0,25 m za środkiem siedziska
        if rnd_:
            dist = min(dist, min(half_w, half_d) - 0.26)
        elif abs(y) > abs(x) * 0.6 and abs(y) > 0.1:
            dist = min(dist, (half_d - 0.26) / max(1e-6, abs(math.sin(ang))))
        else:
            dist = min(dist, (half_w - 0.26) / max(1e-6, abs(math.cos(ang))))
        if rnd_:
            px, py = dist * math.cos(ang), dist * math.sin(ang)
            yaw = math.degrees(ang) - 90.0
        else:
            px, py = dist * math.cos(ang), dist * math.sin(ang)
            if abs(y) > 0.1 and abs(y) >= abs(x) * 0.6:
                yaw = 0.0 if y > 0 else 180.0
            else:
                yaw = -90.0 if x > 0 else 90.0
        yaw += r.uniform(-4, 4)
        px += r.uniform(-0.015, 0.015)
        B.inst(("krzeslo", cst, out), lambda: _chair_mesh(cst, out), T(px, py, 0) @ R("Z", yaw), "krzeslo")
    # na stole: wazon z kwiatami
    _, (mn, mx) = _glb(B.ctx, "GlassVaseFlowers.glb")
    s = 1.35
    B.model("GlassVaseFlowers.glb", T(-(mn.x + mx.x) / 2 * s, -(mn.y + mx.y) / 2 * s, zt) @ Sc(s))
    if not rnd_ and hx > 1.6:
        _bowl(mb, hx * 0.28, 0.02, zt, 0.12, 0.07, "kamionka")
        for k in range(5):
            a = k * 2.1
            mb.sphere(hx * 0.28 + 0.045 * math.cos(a), 0.02 + 0.045 * math.sin(a), zt + 0.04 + 0.01 * (k % 2), 0.036,
                      "pomarancza", n=12)
    B.mesh(mb, "stol")
    # lampy wiszące nad stołem
    if not out and B.ceil and B.ceil > 2.3:
        zb = zt + 0.80
        if rnd_ or hx < 1.7:
            xs = [0.0]
        elif hx < 2.4:
            xs = [-hx * 0.22, hx * 0.22]
        else:
            xs = [-hx * 0.3, 0.0, hx * 0.3]
        for x in xs:
            _pendant(B, x, 0.0, zb)


# ------------------------------------------------------------------ sypialnia
def _lozko(B):
    it, r = B.it, B.rnd
    p0 = it.parts[0]
    bw, L = p0[4], p0[5]
    st = B.st
    mb = MB()
    hb = 0.085              # grubość wezgłowia
    yb = L / 2 - hb         # tył ramy
    fz = 0.27               # góra ramy
    # rama tapicerowana na niskich nóżkach (kołdra zwisa poza nią, więc rama jest o kilka cm mniejsza od obrysu)
    fw2 = bw / 2 - 0.03
    yf = -L / 2 + 0.04
    mb.rbox(-fw2, yf, 0.07, fw2, yb, fz, "tk_obicie", rc=0.025, r=0.018, seg=3)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (fw2 - 0.1), (yf + 0.12) if sy < 0 else (yb - 0.12)
            mb.cyl(x, y, 0.0, 0.075, 0.022, "drewno_z", n=12, rad2=0.026)
    # wezgłowie: pionowe przeszycia
    nch = max(3, round(bw / 0.3))
    cw = bw / nch
    for k in range(nch):
        x = -bw / 2 + (k + 0.5) * cw
        mb.soft(cw / 2 + 0.004, hb / 2, 0.47, "tk_obicie", M=T(x, L / 2 - hb / 2, 0.58), e1=0.12, e2=0.55, nu=20, nv=10)
    # materac
    mw, ml = bw - 0.09, yb - yf - 0.015
    mb.soft(mw / 2, ml / 2, 0.11, "materac", M=T(0, (yb + yf + 0.015) / 2, fz + 0.11), e1=0.22, e2=0.06, nu=40, nv=12)
    zt = fz + 0.22
    # kołdra z odwinięciem
    yh = yb - 0.58
    _drape(mb, "posciel", -bw / 2 + 0.012, bw / 2 - 0.012, -L / 2 + 0.015, yh, zt + 0.03, fz + 0.07, r=0.07, th=0.035,
           wr=0.016, seed=r.uniform(0, 50), nf=34, puff=0.035)
    mb.soft(bw / 2 - 0.02, 0.17, 0.035, "posciel", M=T(0, yh - 0.14, zt + 0.085), e1=0.45, e2=0.1, nu=48, nv=10,
            wr=0.008, seed=r.uniform(0, 9), puff=0.01)
    # koc w nogach
    _drape(mb, "koc", -bw / 2 + 0.006, bw / 2 - 0.006, -L / 2 + 0.16, -L / 2 + 0.64, zt + 0.085, zt - 0.12, r=0.05,
           th=0.016, foot=False, nf=30, wr=0.012, seed=r.uniform(0, 50))
    # poduszki
    npl = 2 if bw > 1.25 else 1
    pw = min(0.72, (bw - 0.12) / npl - 0.03)
    for k in range(npl):
        x = (k - (npl - 1) / 2) * (pw + 0.04)
        mb.pillow(pw, 0.5, 0.17, "posciel", T(x, yb - 0.21, zt + 0.17) @ R("Z", r.uniform(-3, 3)) @ R("X", 58.0),
                  seed=x * 7 + 1)
    if bw >= 1.55:
        for k, key in enumerate(("tk_akcent0", "tk_akcent1")):
            x = (k - 0.5) * 0.5
            mb.pillow(0.45, 0.45, 0.15, key, T(x, yb - 0.40, zt + 0.18) @ R("Z", r.uniform(-6, 6)) @ R("X", 66.0),
                      seed=x * 5 + 3)
    B.mesh(mb, "lozko")
    # szafki nocne z lampkami
    ns = [p for p in it.parts[2:] if p[0] == "box"]
    for p in ns:
        x, y = _local(p)
        w_, d_ = p[4], p[5]
        y = min(y, L / 2 - d_ / 2 - 0.005)

        def make(w_=w_, d_=d_):
            m2 = MB()
            _ns(m2, -w_ / 2, -d_ / 2, w_ / 2, d_ / 2, 0.5, "drewno", 2)
            return m2
        B.inst(("szafka_nocna", round(w_, 2), round(d_, 2)), make, T(x, y, 0), "szafka_nocna")
        _table_lamp(B, x + (0.06 if x > 0 else -0.06), y + 0.03, 0.5)
        mb2 = MB()
        _book_stack(mb2, r, x - (0.08 if x > 0 else -0.08), y - 0.06, 0.5, n=1, big=False)
        B.mesh(mb2, "ksiazka")


def _szafa(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    H = 2.3
    if B.ceil:
        H = min(2.4, B.ceil - 0.02) if B.ceil < 2.7 else 2.3
    mb = MB()
    key = "lak_szafa"
    mb.box(-w / 2 + 0.005, -d / 2 + 0.06, 0, w / 2 - 0.005, d / 2 - 0.01, 0.08, "cokol", r=0.002)
    mb.box(-w / 2, -d / 2 + 0.021, 0.08, w / 2, d / 2, H, key, r=0.003)
    n = max(1, int(round(w / 0.6)))
    g = 0.003
    fw = (w - g * (n + 1)) / n
    hstyle = B.st["uchwyt"]
    for i in range(n):
        x0 = -w / 2 + g + i * (fw + g)
        mb.box(x0, -d / 2, 0.08 + g, x0 + fw, -d / 2 + 0.021, H - g, key, r=0.0025)
        # uchwyty: przy krawędzi otwierania (pary drzwi – w środku pary)
        if hstyle != "bez":
            right = (i % 2 == 0)
            hx = x0 + fw - 0.05 if right else x0 + 0.05
            if n == 1:
                hx = x0 + fw - 0.05
            if hstyle == "galka":
                mb.xf(mb.cyl(0, 0, 0, 0.026, 0.016, "akcent", n=16, r=0.004), T(hx, -d / 2, 1.06) @ R("X", 90))
            else:
                mb.box(hx - 0.006, -d / 2 - 0.028, 0.75, hx + 0.006, -d / 2 - 0.016, 1.55, "akcent", r=0.004)
                for zz in (0.79, 1.51):
                    mb.box(hx - 0.004, -d / 2 - 0.018, zz - 0.006, hx + 0.004, -d / 2 + 0.001, zz + 0.006, "akcent", r=0.002)
    B.mesh(mb, "szafa")


def _regal(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    H = it.h if not B.ceil else min(it.h, B.ceil - 0.05)
    books = any(sh[-1] in ("fu-b1", "fu-b2", "fu-b3") for sh in it.shapes)
    mb = MB()
    frame = "drewno" if B.st["drewno"] != "orzech" or r.random() < 0.5 else "lak_bialy"
    if B.rk in ("spizarnia", "warsztat", "pracownia"):
        frame = "dab" if B.rk == "spizarnia" else "buk"
    t = 0.025
    nseg = max(1, int(round(w / 0.85)))
    sw = (w - t * (nseg + 1)) / nseg
    nshelf = max(3, int(round((H - 0.1) / 0.38)))
    zs = [0.08 + k * (H - 0.08 - t) / nshelf for k in range(nshelf + 1)]
    mb.box(-w / 2 + t, -d / 2 + 0.03, 0, w / 2 - t, d / 2, 0.08, "cokol" if frame == "lak_bialy" else frame, r=0.002)
    for k in range(nseg + 1):
        x = -w / 2 + k * (sw + t)
        mb.box(x, -d / 2, 0, x + t, d / 2, H, frame + ("_z" if frame not in ("lak_bialy",) else ""), r=0.002)
    for z in zs:
        mb.box(-w / 2 + t, -d / 2, z, w / 2 - t, d / 2, z + t, frame, r=0.002)
    # zawartość półek
    bk = MB()
    for k in range(nseg):
        xa = -w / 2 + t + k * (sw + t)
        for j in range(nshelf):
            z = zs[j] + t
            hc = zs[j + 1] - z
            if B.rk == "spizarnia":
                _fill_pantry(bk, r, xa, xa + sw, z, hc, d)
            elif B.rk == "jadalnia" or (not books and B.rk not in ("pracownia", "warsztat")):
                if r.random() < 0.7:
                    _fill_dishes(bk, r, xa, xa + sw, z, hc, d)
                else:
                    _fill_books(bk, r, xa, xa + sw, z, hc, d, 0.5)
            elif B.rk in ("pracownia", "warsztat"):
                _fill_boxes(bk, r, xa, xa + sw, z, hc, d)
            else:
                _fill_books(bk, r, xa, xa + sw, z, hc, d, 0.88 if j not in (0,) else 0.6)
    B.mesh(mb, "regal")
    B.mesh(bk, "regal_zawartosc")


def _book_upright(mb, rnd, x, z, t, h, depth, d, col, lean=0.0):
    """Książka stojąca grzbietem do −Y; lean – przechył w lewo (opiera się o poprzednią), obrót wokół lewej krawędzi."""
    y0 = -d / 2 + 0.012 + rnd.uniform(0, 0.012)
    page = lin((0.86, 0.83, 0.76)) + (0.0,)
    fl = rnd.choice((0.0, 0.0, 0.35, 0.7, 0.7, 0.95))
    c = lin(col) + (fl,)
    M = T(x, 0, z) @ R("Y", -lean) @ T(-x, 0, -z) if lean else None
    mb.colbox(x, y0, z, x + t, y0 + depth, z + h, "ksiazki", {"-y": c, "-x": c, "+x": c, "reszta": page}, M=M, uv_front=True)


def _decor(mb, rnd, cx, z, hc, d):
    """Drobiazg na półce: wazon, miska albo ramka ze zdjęciem."""
    k = rnd.random()
    if k < 0.4:
        hh = min(hc - 0.04, rnd.uniform(0.13, 0.24))
        _vase(mb, cx, -0.01, z, hh, rnd.uniform(0.045, 0.065), "kamionka", kind=rnd.choice((0, 1)))
    elif k < 0.65:
        _bowl(mb, cx, -0.01, z, 0.07, 0.045, "kamionka")
    elif k < 0.85:
        hh = min(hc - 0.04, 0.2)
        fs = mb.box(-0.075, -0.008, 0, 0.075, 0.008, hh, "drewno_z", r=0.002)
        fs += mb.box(-0.06, -0.0085, 0.015, 0.06, -0.008, hh - 0.015, f"obraz:{rnd.randint(1, 5)}", r=0)
        mb.xf(fs, T(cx, d / 2 - 0.06, z) @ R("X", 8))
    else:
        mb.sphere(cx, 0.0, z + 0.05, 0.05, "braz", n=16)


def _fill_books(mb, rnd, xa, xb, z, hc, d, fill=0.85):
    """Półka z książkami: rzędy grzbietów w seriach, czasem stos leżących, drobiazg, przechylona książka."""
    W = xb - xa
    obst = []
    if rnd.random() > fill:
        dw = rnd.uniform(0.17, 0.26)
        dx = xa + rnd.choice((0.02, W - dw - 0.02, rnd.uniform(0.1, max(0.11, W - dw - 0.1))))
        obst.append(("deco", dx, dx + dw))
    if rnd.random() < 0.3 and W > 0.5:
        sw = rnd.uniform(0.17, 0.23)
        sx = xa + rnd.choice((0.01, W - sw - 0.01))
        if all(sx + sw < o[1] - (o[2] - o[1]) or sx > o[2] for o in obst):
            obst.append(("stos", sx, sx + sw))
    obst.sort(key=lambda o: o[1])
    page = lin((0.86, 0.83, 0.76)) + (0.0,)
    x = xa + 0.006
    run_col, run_n = None, 0
    while x < xb - 0.014:
        hit = next((o for o in obst if o[1] <= x < o[2]), None)
        if hit:
            kind, a, b = hit
            if kind == "deco":
                _decor(mb, rnd, (a + b) / 2, z, hc, d)
            else:
                hs = 0.0
                for i in range(rnd.randint(2, 5)):
                    tt = rnd.uniform(0.02, 0.045)
                    if hs + tt > hc - 0.03:
                        break
                    cc = lin(rnd.choice(KSIAZKI)) + (0.0,)
                    dd = min(d - 0.05, rnd.uniform(0.15, 0.22))
                    ww = (b - a) * rnd.uniform(0.85, 1.0)
                    y0 = -d / 2 + 0.02
                    mb.colbox(a, y0, z + hs, a + ww, y0 + dd, z + hs + tt, "ksiazki",
                              {"-x": cc, "+z": cc, "-z": cc, "-y": page, "reszta": page})
                    hs += tt
            x = b + 0.008
            continue
        limit = min([o[1] for o in obst if o[1] > x] + [xb - 0.006])
        if run_n <= 0:
            run_col = rnd.choice(KSIAZKI)
            run_n = rnd.choice((1, 1, 1, 2, 2, 3, 5))
            hrun = min(hc - 0.02, max(0.15, rnd.gauss(0.23, 0.04)))
        run_n -= 1
        col = run_col if rnd.random() < 0.8 else rnd.choice(KSIAZKI)
        g = sum(col) / 3
        col = shade(mix3(col, (g, g, g), rnd.uniform(0.15, 0.4)), rnd.uniform(0.78, 1.05))
        t = rnd.uniform(0.014, 0.05) if rnd.random() < 0.85 else rnd.uniform(0.05, 0.07)
        h = min(hc - 0.02, hrun * rnd.uniform(0.92, 1.06))
        depth = min(d - 0.03, rnd.uniform(0.15, 0.23))
        room = limit - x
        if room < 0.016:
            x = limit + 0.0005
            continue
        if t > room:
            t = room - 0.0005
        if room < 0.09 and room > 0.03 and h > 0.15 and rnd.random() < 0.5:
            # ostatnia przed przeszkodą/końcem – przechylona
            lean = rnd.uniform(9, 20)
            bx = x + math.sin(math.radians(lean)) * h + 0.002
            if bx + t * math.cos(math.radians(lean)) < limit:
                _book_upright(mb, rnd, bx, z, t, h, depth, d, col, lean)
            x = limit + 0.0005
            continue
        _book_upright(mb, rnd, x, z, t, h, depth, d, col)
        x += t + rnd.uniform(0.0, 0.0015)


def _fill_dishes(mb, rnd, xa, xb, z, hc, d):
    x = xa + 0.03
    while x < xb - 0.12:
        k = rnd.random()
        if k < 0.35:      # stos talerzy
            r_ = rnd.choice((0.11, 0.13))
            for i in range(rnd.randint(3, 7)):
                mb.lathe([(0.0, 0.0), (r_ * 0.6, 0.0), (r_, 0.012), (r_ - 0.004, 0.014), (r_ * 0.58, 0.004), (0.0, 0.004)],
                         "porcelana", n=28, x=x + r_, y=0.0, z=z + i * 0.014)
            x += 2 * r_ + 0.04
        elif k < 0.6:     # miski
            r_ = 0.07
            for i in range(rnd.randint(1, 3)):
                _bowl(mb, x + r_, -0.02, z + i * 0.03, r_ - i * 0.003, 0.055, "kamionka")
            x += 2 * r_ + 0.04
        elif k < 0.8:     # szklanki
            for i in range(rnd.randint(2, 4)):
                mb.lathe([(0.0, 0.0), (0.035, 0.0), (0.038, 0.11), (0.0345, 0.11), (0.032, 0.004), (0.0, 0.004)],
                         "szklo_cienkie", n=20, x=x + 0.04 + i * 0.08, y=-0.03 + (i % 2) * 0.06, z=z)
            x += 0.32
        else:             # dzbanek / wazon
            hh = min(hc - 0.04, 0.24)
            _vase(mb, x + 0.07, 0.0, z, hh, 0.065, "ceramika" if rnd.random() < 0.5 else "kamionka", kind=rnd.choice((0, 1)))
            x += 0.18


def _fill_pantry(mb, rnd, xa, xb, z, hc, d):
    x = xa + 0.02
    cont = [(0.85, 0.72, 0.42), (0.55, 0.30, 0.18), (0.92, 0.90, 0.84), (0.60, 0.45, 0.22), (0.30, 0.18, 0.12),
            (0.80, 0.55, 0.15), (0.45, 0.50, 0.25)]
    while x < xb - 0.1:
        k = rnd.random()
        if k < 0.55:      # słoik: zawartość + szkło + pokrywka
            rr = rnd.choice((0.045, 0.055, 0.065))
            hh = min(hc - 0.05, rnd.choice((0.12, 0.16, 0.22)))
            c = lin(rnd.choice(cont)) + (0.0,)
            fs = mb.lathe([(0.0, 0.0), (rr - 0.003, 0.0), (rr - 0.003, hh * rnd.uniform(0.5, 0.9)), (0.0, hh * 0.7)], "kolor",
                          n=18, x=x + rr, y=-0.02, z=z + 0.003)
            mb.setcol(fs, c)
            mb.lathe([(0.0, 0.0), (rr, 0.0), (rr, hh), (rr - 0.001, hh), (0.0, hh)], "szklo_cienkie", n=20, x=x + rr, y=-0.02, z=z)
            mb.cyl(x + rr, -0.02, z + hh, z + hh + 0.02, rr * 0.92, "akcent" if rnd.random() < 0.5 else "drewno_z", n=20, r=0.003)
            x += 2 * rr + 0.02
        elif k < 0.8:     # pudełko
            bw_, bh = rnd.uniform(0.08, 0.16), min(hc - 0.04, rnd.uniform(0.15, 0.26))
            c = lin(rnd.choice(KSIAZKI)) + (0.0,)
            mb.colbox(x, -d / 2 + 0.04, z, x + bw_, -d / 2 + 0.04 + rnd.uniform(0.12, 0.2), z + bh, "kolor", c)
            x += bw_ + 0.015
        else:             # butelka
            rr, hh = 0.035, min(hc - 0.03, 0.28)
            mb.lathe([(0.0, 0.0), (rr, 0.0), (rr, hh * 0.62), (0.012, hh * 0.85), (0.012, hh), (0.0, hh)], "szklo_butelka", n=16,
                     x=x + rr, y=0.0, z=z)
            x += 2 * rr + 0.02


def _fill_boxes(mb, rnd, xa, xb, z, hc, d):
    x = xa + 0.02
    cols = [(0.35, 0.40, 0.45), (0.78, 0.74, 0.66), (0.15, 0.15, 0.16), (0.55, 0.30, 0.20), (0.62, 0.62, 0.60)]
    while x < xb - 0.12:
        k = rnd.random()
        if k < 0.5:
            bw_ = rnd.uniform(0.2, 0.36)
            bh = min(hc - 0.03, rnd.uniform(0.14, 0.25))
            c = lin(rnd.choice(cols)) + (0.0,)
            mb.colbox(x, -d / 2 + 0.03, z, x + bw_, d / 2 - 0.03, z + bh, "kolor", c)
            x += bw_ + 0.02
        elif k < 0.8:
            for i in range(rnd.randint(1, 3)):
                rr = 0.06
                mb.cyl(x + rr, -0.02, z, z + 0.12, rr, "aluminium", n=20, r=0.002)
                c = lin(rnd.choice(KSIAZKI)) + (0.0,)
                mb.setcol(mb.cyl(x + rr, -0.02, z + 0.12, z + 0.128, rr - 0.002, "kolor", n=20), c)
                x += 2 * rr + 0.01
            x += 0.02
        else:
            _vase(mb, x + 0.05, 0.0, z, 0.12, 0.045, "kamionka", kind=1)
            _stems(mb, x + 0.05, 0.0, z + 0.08, 0.16, 6, rnd, "drewno_z")
            x += 0.14


# ------------------------------------------------------------------ kuchnia
def _handle(mb, B, x0, x1, z0, z1, y, kind, vertical=False, right=True, low=False):
    """Uchwyt na froncie (y – lico frontu); low – przy dolnej krawędzi (szafki wiszące)."""
    hs = B.st["uchwyt"]
    if hs == "bez":
        return
    if hs == "galka":
        cx = ((x1 - 0.04) if right else (x0 + 0.04)) if vertical else (x0 + x1) / 2
        cz = ((z0 + 0.06) if low else (z1 - 0.07)) if vertical else (z0 + z1) / 2
        mb.xf(mb.cyl(0, 0, 0, 0.024, 0.013, "akcent", n=14, r=0.004), T(cx, y, cz) @ R("X", 90))
        return
    if vertical:
        cx = (x1 - 0.035) if right else (x0 + 0.035)
        za, zb = z1 - 0.06 - min(0.25, (z1 - z0) * 0.45), z1 - 0.06
        if low:
            za, zb = z0 + 0.06, z0 + 0.06 + min(0.25, (z1 - z0) * 0.45)
        mb.box(cx - 0.006, y - 0.03, za, cx + 0.006, y - 0.018, zb, "akcent", r=0.004)
        for zz in (za + 0.03, zb - 0.03):
            mb.box(cx - 0.004, y - 0.02, zz - 0.005, cx + 0.004, y + 0.001, zz + 0.005, "akcent", r=0.002)
    else:
        L = min(0.32, (x1 - x0) * 0.55)
        cx, cz = (x0 + x1) / 2, z1 - 0.045
        mb.box(cx - L / 2, y - 0.03, cz - 0.006, cx + L / 2, y - 0.018, cz + 0.006, "akcent", r=0.004)
        for xx in (cx - L / 2 + 0.025, cx + L / 2 - 0.025):
            mb.box(xx - 0.005, y - 0.02, cz - 0.004, xx + 0.005, y + 0.001, cz + 0.004, "akcent", r=0.002)


def _fronts(mb, B, x0, x1, z0, z1, y, plan, key="lak_front", low=False):
    """Fronty szafek: plan = lista modułów ('d' drzwi, 's3' trzy szuflady, 's2', 'z' zmywarka)."""
    n = len(plan)
    g = 0.003
    mw = (x1 - x0) / n
    for i, kind in enumerate(plan):
        a, b = x0 + i * mw + g / 2, x0 + (i + 1) * mw - g / 2
        if kind.startswith("s"):
            k = int(kind[1])
            hs = [0.18, 0.28, 0.28] if k == 3 else [0.36, 0.38]
            tot = sum(hs)
            zc = z0
            for j, hh in enumerate(hs):
                h2 = (z1 - z0) * hh / tot
                mb.box(a, y, zc + g / 2, b, y + 0.019, zc + h2 - g / 2, key, r=0.0018)
                _handle(mb, B, a, b, zc, zc + h2, y, "s")
                zc += h2
        else:
            mb.box(a, y, z0 + g / 2, b, y + 0.019, z1 - g / 2, key, r=0.0018)
            _handle(mb, B, a, b, z0, z1, y, "d", vertical=(kind == "d"), right=(i % 2 == 0), low=low)


def _blat(B):
    it, r, st = B.it, B.rnd, B.st
    w, d = it.w, it.d
    shapes = it.shapes
    sink = any(sh[0] == "r" and sh[-1] == "fu" for sh in shapes[1:])
    hob = any(sh[0] == "c" and sh[-1] == "fu-d" for sh in shapes)
    mb = MB()
    zt, tt = 0.90, 0.035
    zf = zt - tt
    yf = -d / 2 + 0.02            # lico frontów (blat wystaje 2 cm)
    mb.box(-w / 2 + 0.005, yf + 0.06, 0, w / 2 - 0.005, d / 2 - 0.02, 0.10, "cokol", r=0.002)
    mb.box(-w / 2, yf + 0.019, 0.10, w / 2, d / 2 - 0.005, zf, "lak_front", r=0.002)
    n = max(1, int(round(w / 0.6)))
    mw = w / n
    sx = -w / 4 if sink else None
    hx = w / 4 if hob else None
    plan = []
    for i in range(n):
        cx = -w / 2 + (i + 0.5) * mw
        if sink and abs(cx - sx) <= mw / 2 + 1e-6:
            plan.append("dd")
        elif hob and abs(cx - hx) <= mw / 2 + 1e-6:
            plan.append("s3")
        elif sink and abs(cx - sx - mw) <= mw / 2 + 1e-6 and n > 3:
            plan.append("z")
        else:
            plan.append(r.choice(("d", "s2", "d", "s3")))
    _fronts(mb, B, -w / 2, w / 2, 0.10, zf - 0.002, yf, [p if p != "dd" else "d" for p in plan])
    # blat z otworem na zlew
    top = "blat"
    if sink:
        sw_, sd_ = min(0.52, mw - 0.1), 0.40
        cy = yf + 0.07 + sd_ / 2
        a, b = sx - sw_ / 2, sx + sw_ / 2
        c, e = cy - sd_ / 2, cy + sd_ / 2
        mb.box(-w / 2, -d / 2, zf, a, d / 2, zt, top, r=0.002)
        mb.box(b, -d / 2, zf, w / 2, d / 2, zt, top, r=0.002)
        mb.box(a, -d / 2, zf, b, c, zt, top, r=0.0015)
        mb.box(a, e, zf, b, d / 2, zt, top, r=0.0015)
        mb.basin(_rrect(a + 0.002, c + 0.002, b - 0.002, e - 0.002, 0.03, 4), zf - 0.19, zf, "stal", r=0.02)
        mb.cyl(sx, cy, zf - 0.188, zf - 0.186, 0.035, "chrom", n=20)
        # bateria
        fy = e + 0.06
        fm = "akcent" if st["metal"] != "czarny_metal" else "czarny_metal"
        mb.cyl(sx, fy, zt, zt + 0.06, 0.026, fm, n=20, r=0.003)
        arc = [(sx, fy, zt + 0.05)] + [(sx, fy - 0.11 + 0.11 * math.cos(math.radians(a_)), zt + 0.32 + 0.11 * math.sin(math.radians(a_)))
                                        for a_ in range(0, 181, 20)] + [(sx, fy - 0.22, zt + 0.26)]
        mb.tube(arc, 0.011, fm, n=12)
        mb.box(sx + 0.026, fy - 0.008, zt + 0.03, sx + 0.07, fy + 0.008, zt + 0.042, fm, r=0.004)
    else:
        mb.box(-w / 2, -d / 2, zf, w / 2, d / 2, zt, top, r=0.002)
    # płyta indukcyjna
    if hob:
        pw, pd = min(0.6, mw - 0.04), 0.51
        cy = yf + 0.04 + pd / 2
        mb.box(hx - pw / 2, cy - pd / 2, zt, hx + pw / 2, cy + pd / 2, zt + 0.005, "szklo_czarne", r=0.002)
        for dx, dy, rr in ((-0.14, -0.11, 0.09), (0.15, -0.11, 0.075), (-0.14, 0.12, 0.075), (0.15, 0.12, 0.1)):
            ring = [(rr * math.cos(2 * math.pi * k / 40), rr * math.sin(2 * math.pi * k / 40)) for k in range(40)]
            inner = [(p[0] * 0.95, p[1] * 0.95) for p in ring]
            bm = mb.bm
            vo = [bm.verts.new((hx + dx + p[0], cy + dy + p[1], zt + 0.0053)) for p in ring]
            vi = [bm.verts.new((hx + dx + p[0], cy + dy + p[1], zt + 0.0053)) for p in inner]
            mb.tag([bm.faces.new((vi[k], vo[k], vo[(k + 1) % 40], vi[(k + 1) % 40])) for k in range(40)], "nadruk")
        for k in range(6):
            mb.box(hx - 0.1 + k * 0.04, cy - pd / 2 + 0.02, zt + 0.005, hx - 0.085 + k * 0.04, cy - pd / 2 + 0.035, zt + 0.0055, "nadruk", r=0)
    # zabudowa górna (z części: 1,5–2,25 m, głębokość 0,35 przy ścianie)
    wall = [p for p in it.parts[1:] if p[0] == "box" and p[3] >= 1.2]
    if wall:
        p = wall[0]
        z0, z1 = p[3], p[3] + p[6]
        dd = p[5]
        yb = d / 2
        mb.box(-w / 2, yb - 0.012, zt, w / 2, yb, z0, top, r=0.002)       # panel za blatem
        if st["gorne"] == "szafki" or B.rk == "pralnia":
            mb.box(-w / 2, yb - dd + 0.02, z0, w / 2, yb, z1, "lak_front", r=0.002)
            nn = max(1, int(round(w / 0.6)))
            plan2 = ["d"] * nn
            _fronts(mb, B, -w / 2, w / 2, z0, z1, yb - dd, plan2, low=True)
            # listwa LED pod szafkami
            mb.box(-w / 2 + 0.05, yb - dd + 0.05, z0 - 0.008, w / 2 - 0.05, yb - dd + 0.07, z0, "led", r=0)
            B.light(None, 40.0 * w / 3.6, kind="AREA", M=T(0, yb - dd + 0.06, z0 - 0.01), area=(w - 0.1, 0.03),
                    temp=3000.0, name="led_kuchnia")
            if hob:
                mb.box(hx - 0.3, yb - dd - 0.03, z0 - 0.04, hx + 0.3, yb - 0.02, z0, "stal", r=0.003)
        else:
            sh_w = [(-w / 2, (hx - 0.4) if hob else w / 2)]
            if hob:
                sh_w.append((hx + 0.4, w / 2))
            for (a, b) in sh_w:
                if b - a < 0.3:
                    continue
                for zz in (z0 + 0.05, z0 + 0.45):
                    mb.box(a, yb - 0.26, zz, b, yb, zz + 0.035, "drewno", r=0.003)
                    _shelf_props(mb, r, a, b, zz + 0.035, yb - 0.13)
            if hob:
                hz = z0 + 0.1
                mb.box(hx - 0.3, yb - 0.48, hz, hx + 0.3, yb, hz + 0.06, "stal", r=0.004)
                cz = B.ceil if B.ceil else z1 + 0.6
                mb.prism([(hx - 0.28, yb - 0.46), (hx + 0.28, yb - 0.46), (hx + 0.28, yb), (hx - 0.28, yb)], hz + 0.06, hz + 0.32,
                         "stal", top=[(hx - 0.13, yb - 0.27), (hx + 0.13, yb - 0.27), (hx + 0.13, yb), (hx - 0.13, yb)])
                mb.box(hx - 0.13, yb - 0.27, hz + 0.32, hx + 0.13, yb, cz, "stal", r=0.002)
    # drobiazgi na blacie
    if w > 1.2:
        bx = (-w / 2 + 0.25) if not sink or sx > -w / 2 + 0.6 else (w / 2 - 0.35)
        fs = mb.box(bx - 0.2, -0.01, 0.0, bx + 0.2, 0.01, 0.34, "drewno_z", r=0.004)
        mb.xf(fs, T(0, d / 2 - 0.03, zt) @ R("X", -10) @ T(0, -0.012, 0))
        for k in range(3):
            hh = (0.2, 0.16, 0.13)[k]
            mb.cyl(bx - 0.12 + k * 0.11, d / 2 - 0.13, zt, zt + hh, 0.05, "ceramika" if k != 1 else "kamionka", n=24, r=0.004)
            mb.cyl(bx - 0.12 + k * 0.11, d / 2 - 0.13, zt + hh, zt + hh + 0.015, 0.048, "drewno_z", n=24, r=0.003)
    B.mesh(mb, "blat")


def _shelf_props(mb, rnd, a, b, z, y):
    x = a + 0.08
    while x < b - 0.12:
        k = rnd.random()
        if k < 0.35:
            for i in range(rnd.randint(3, 6)):
                mb.lathe([(0.0, 0.0), (0.06, 0.0), (0.1, 0.012), (0.096, 0.014), (0.058, 0.004), (0.0, 0.004)], "porcelana", n=28,
                         x=x + 0.1, y=y, z=z + i * 0.014)
            x += 0.24
        elif k < 0.6:
            for i in range(2):
                _bowl(mb, x + 0.07, y, z + i * 0.035, 0.07 - i * 0.004, 0.06, "kamionka")
            x += 0.18
        elif k < 0.8:
            mb.cyl(x + 0.05, y, z, z + 0.15, 0.05, "szklo_cienkie", n=20)
            mb.cyl(x + 0.05, y, z + 0.15, z + 0.17, 0.048, "drewno_z", n=20, r=0.003)
            x += 0.14
        else:
            _plant_small(mb, rnd, x + 0.08, y, z)
            x += 0.2


def _stool_mesh(seat_key, leg_key, back=False):
    mb = MB()
    H = 0.655
    for k in range(4):
        a = math.radians(45 + 90 * k)
        mb.tube([(0.205 * math.cos(a), 0.205 * math.sin(a), 0.0), (0.15 * math.cos(a), 0.15 * math.sin(a), H - 0.035)],
                [0.011, 0.013], leg_key, n=10)
    mb.torus(0, 0, 0.26, 0.178, 0.008, leg_key, nu=40, nv=8)
    mb.cyl(0, 0, H - 0.04, H - 0.03, 0.15, leg_key, n=28)
    mb.soft(0.19, 0.19, 0.03, seat_key, M=T(0, 0, H), e1=0.35, e2=1.0, nu=32, nv=10, puff=0.006)
    if back:
        mb.tube([(-0.1, 0.12, H), (-0.11, 0.15, H + 0.2)], 0.008, leg_key, n=8)
        mb.tube([(0.1, 0.12, H), (0.11, 0.15, H + 0.2)], 0.008, leg_key, n=8)
        mb.soft(0.16, 0.025, 0.05, seat_key, M=T(0, 0.155, H + 0.2) @ R("X", -12), e1=0.4, e2=0.3, nu=24, nv=8)
    return mb


def _wyspa(B):
    it, r, st = B.it, B.rnd, B.st
    p0 = it.parts[0]
    if p0[-1] != "kuchnia":
        return _wyspa_garderoba(B)
    w = p0[4]
    d = p0[5]
    mb = MB()
    zt, tt = 0.92, 0.04
    top = "blat"
    # blat „wodospad”
    mb.box(-w / 2, -d / 2, zt - tt, w / 2, d / 2, zt, top, r=0.003)
    for sx in (-1, 1):
        mb.box(sx * w / 2 - (tt if sx > 0 else 0), -d / 2, 0, sx * w / 2 + (tt if sx < 0 else 0), d / 2, zt - tt, top, r=0.003)
    # korpus z frontami po stronie kuchni (+Y), nawis 0,3 m po stronie stołków (−Y)
    yb0 = -d / 2 + 0.30
    xa, xb = -w / 2 + tt + 0.005, w / 2 - tt - 0.005
    mb.box(xa, yb0 + 0.04, 0, xb, d / 2 - 0.06, 0.10, "cokol", r=0.002)
    mb.box(xa, yb0, 0.10, xb, d / 2 - 0.02, zt - tt, "lak_front", r=0.002)
    n = max(1, int(round((xb - xa) / 0.6)))
    plan = [("s3" if i % 2 == 0 else "s2") for i in range(n)]
    # fronty od +Y: budujemy jak dla −Y i obracamy o 180°
    m2 = MB()
    _fronts(m2, B, xa, xb, 0.10, zt - tt - 0.002, -(d / 2 - 0.02) - 0.019, plan)
    me = m2
    fs = list(me.bm.faces)
    me.xf(fs, R("Z", 180))
    B.mesh(me, "wyspa_fronty")
    # stołki
    stools = [p for p in it.parts[1:] if p[0] == "cyl"]
    seat = "skora" if st["krzeslo"] == "tapicerowane" else "tk_obicie"
    legk = "czarny_metal" if st["metal"] != "mosiadz" else "mosiadz"
    for p in stools:
        x, _y = _local(p)
        y = -(d / 2 + 0.10)
        B.inst(("stolek_barowy", seat, legk), lambda: _stool_mesh(seat, legk, back=True),
               T(x + r.uniform(-0.02, 0.02), y, 0) @ R("Z", 180 + r.uniform(-8, 8)), "stolek")
    # na blacie: patera z oliwkami, deska
    parts, (mn, mx) = _glb(B.ctx, "IridescentDishWithOlives.glb")
    s = 0.62
    B.model("IridescentDishWithOlives.glb", T(w * 0.22, 0.05, zt) @ Sc(s))
    mb.rbox(-w * 0.3 - 0.2, -0.12, zt, -w * 0.3 + 0.2, 0.14, zt + 0.025, "drewno", rc=0.04, r=0.005)
    _bowl(mb, -w * 0.3 + 0.05, 0.0, zt + 0.025, 0.1, 0.06, "kamionka")
    for k in range(4):
        a = k * 1.7
        mb.sphere(-w * 0.3 + 0.05 + 0.04 * math.cos(a), 0.04 * math.sin(a), zt + 0.025 + 0.045 + 0.01 * (k % 2), 0.034,
                  "pomarancza", n=12)
    B.mesh(mb, "wyspa")
    if B.ceil and B.ceil > 2.4:
        n = 2 if w < 2.0 else 3
        for k in range(n):
            _pendant(B, -w / 2 + (k + 0.5) * w / n, 0.0, zt + 0.78, "kula" if st["lampa"] == "len" else st["lampa"])


def _wyspa_garderoba(B):
    it, r = B.it, B.rnd
    w, d = it.parts[0][4], it.parts[0][5]
    mb = MB()
    m2 = MB()
    _ns(mb, -w / 2, -d / 2, w / 2, 0.0, 0.88, "drewno", 3, handle="akcent", legs=False)
    _ns(m2, -w / 2, -d / 2, w / 2, 0.0, 0.88, "drewno", 3, handle="akcent", legs=False)
    m2.xf(list(m2.bm.faces), R("Z", 180))
    mb.box(-w / 2 - 0.01, -d / 2 - 0.01, 0.88, w / 2 + 0.01, d / 2 + 0.01, 0.9, "skora", r=0.004)
    _book_stack(mb, r, -w * 0.25, 0, 0.9, 2)
    _bowl(mb, w * 0.25, 0.0, 0.9, 0.09, 0.05, "mosiadz")
    B.mesh(mb, "garderoba_wyspa")
    B.mesh(m2, "garderoba_wyspa2")


# ------------------------------------------------------------------ biuro
def _office_chair_mesh():
    mb = MB()
    for k in range(5):
        a = math.radians(90 + 72 * k)
        c, s = math.cos(a), math.sin(a)
        mb.tube([(0.03 * c, 0.03 * s, 0.11), (0.30 * c, 0.30 * s, 0.075)], [0.022, 0.014], "aluminium", n=8)
        mb.cyl(0.3 * c, 0.3 * s, 0.05, 0.08, 0.012, "plastik_czarny", n=8)
        wheel = mb.cyl(0, 0, -0.012, 0.012, 0.025, "plastik_czarny", n=14)
        mb.xf(wheel, T(0.3 * c, 0.3 * s, 0.026) @ R("Z", math.degrees(a)) @ R("X", 90))
    mb.cyl(0, 0, 0.09, 0.14, 0.04, "plastik_czarny", n=16, r=0.004)
    mb.cyl(0, 0, 0.14, 0.40, 0.022, "chrom", n=16)
    mb.box(-0.12, -0.12, 0.39, 0.12, 0.12, 0.43, "plastik_czarny", r=0.006)
    mb.soft(0.25, 0.245, 0.04, "tk_ciemna", M=T(0, -0.02, 0.47), e1=0.35, e2=0.18, puff=0.01)
    # oparcie: wygięta siatka w ramie
    def back(u, v):
        x = (u - 0.5) * 0.46 * (1 - 0.12 * v)
        y = 0.04 * ((u - 0.5) * 2) ** 2 * 2.0 - 0.03 * math.sin(math.pi * v)
        return (x, 0.24 + y + v * 0.08, 0.56 + v * 0.55)
    fs = mb.surf(back, 16, 14, "tk_ciemna")
    res = bmesh.ops.solidify(mb.bm, geom=fs, thickness=0.02)
    mb.tag([g for g in res["geom"] if isinstance(g, bmesh.types.BMFace)], "tk_ciemna", True)
    edge = [back(u / 10, 0) for u in range(11)] + [back(1, v / 10) for v in range(1, 11)] + \
        [back(1 - u / 10, 1) for u in range(1, 11)] + [back(0, 1 - v / 10) for v in range(1, 11)]
    mb.tube(edge, 0.012, "plastik_czarny", n=8, cap=False)
    mb.tube([(0, 0.12, 0.42), (0, 0.24, 0.45), (0, 0.27, 0.62)], 0.018, "plastik_czarny", n=10)
    for sx in (-1, 1):
        mb.tube([(sx * 0.2, 0.0, 0.43), (sx * 0.26, 0.0, 0.47), (sx * 0.26, 0.02, 0.64)], 0.012, "plastik_czarny", n=8)
        mb.soft(0.035, 0.12, 0.014, "plastik_czarny", M=T(sx * 0.26, 0.0, 0.655), e1=0.4, e2=0.3, nu=16, nv=6)
    return mb


def _monitor(mb, x, y, z, w=0.62):
    h = w * 9 / 16
    mb.box(x - 0.11, y - 0.09, z, x + 0.11, y + 0.08, z + 0.01, "aluminium", r=0.003)
    mb.box(x - 0.025, y + 0.04, z, x + 0.025, y + 0.06, z + 0.3, "aluminium", r=0.004)
    mb.box(x - w / 2, y + 0.005, z + 0.1, x + w / 2, y + 0.02, z + 0.1 + h, "plastik_czarny", r=0.003)
    mb.box(x - w / 2 + 0.006, y + 0.0035, z + 0.106, x + w / 2 - 0.006, y + 0.005, z + 0.094 + h, "monitor", r=0)


def _desk_lamp(B, mb, x, y, z, yaw=0.0):
    M = T(x, y, z) @ R("Z", yaw)
    fs = []
    fs += mb.cyl(0, 0, 0, 0.018, 0.075, "czarny_metal", n=24, r=0.003)
    fs += mb.tube([(0, 0, 0.018), (0.04, 0.02, 0.38)], 0.007, "czarny_metal", n=8)
    fs += mb.tube([(0.04, 0.02, 0.38), (0.0, -0.22, 0.48)], 0.006, "czarny_metal", n=8)
    head = mb.lathe([(0.075, 0.0), (0.05, 0.08), (0.02, 0.11), (0.0, 0.115)], "czarny_metal", n=24)
    head += mb.lathe([(0.0, 0.112), (0.019, 0.107), (0.048, 0.078), (0.072, 0.0)], "lak_bialy", n=24)
    head += mb.sphere(0, 0, 0.05, 0.022, "zarowka", n=10)
    mb.xf(head, T(0.0, -0.24, 0.47) @ R("X", 155))
    fs += head
    mb.xf(fs, M)
    lp = M @ Vector((0.0, -0.24, 0.42))
    B.light(lp, 12.0, size=0.03, name="lampka_biurko")


def _biurko(B):
    it, r = B.it, B.rnd
    p0 = it.parts[0]
    w, dd = p0[4], p0[5]
    pair = it.kind == "biurko2"
    mb = MB()
    zt = 0.75
    if pair:
        D = dd
        y0, y1 = -D / 2, D / 2
    else:
        y1 = it.d / 2 - 0.01
        y0 = y1 - dd
    mb.rbox(-w / 2, y0, zt - 0.026, w / 2, y1, zt, "drewno", rc=0.01, r=0.004)
    # nogi: rama stalowa
    for sx in (-1, 1):
        x = sx * (w / 2 - 0.06)
        mb.box(x - 0.015, y0 + 0.04, 0, x + 0.015, y1 - 0.04, 0.03, "czarny_metal", r=0.003)
        mb.box(x - 0.015, (y0 + y1) / 2 - 0.02, 0.03, x + 0.015, (y0 + y1) / 2 + 0.02, zt - 0.026, "czarny_metal", r=0.003)
        mb.box(x - 0.015, y0 + 0.06, zt - 0.06, x + 0.015, y1 - 0.06, zt - 0.026, "czarny_metal", r=0.003)
    mb.box(-w / 2 + 0.07, (y0 + y1) / 2 - 0.015, zt - 0.09, w / 2 - 0.07, (y0 + y1) / 2 + 0.015, zt - 0.06, "czarny_metal", r=0.003)
    places = []
    if pair:
        mb.rbox(-w / 2 + 0.1, -0.012, zt, w / 2 - 0.1, 0.012, zt + 0.38, "filc", rc=0.01, r=0.006)
        places = [(0.0, -D / 4, 0.0), (0.0, D / 4, 180.0)]
    else:
        places = [(0.0, (y0 + y1) / 2, 0.0)]
    for k, (px, py, yaw) in enumerate(places):
        sub = MB()
        _monitor(sub, 0.0, 0.10, zt, 0.6 if w > 1.3 else 0.5)
        sub.rbox(-0.22, -0.16, zt, 0.22, -0.03, zt + 0.012, "aluminium", rc=0.008, r=0.002)
        sub.rbox(-0.21, -0.153, zt + 0.012, 0.21, -0.037, zt + 0.016, "plastik_szary", rc=0.006, r=0.001)
        sub.soft(0.03, 0.055, 0.016, "plastik_czarny", M=T(0.33, -0.1, zt + 0.012), e1=0.5, e2=0.5, nu=16, nv=8)
        if k == 0:
            _book_stack(sub, r, -w / 2 + 0.25, -0.05, zt, 2, big=False)
            _plant_small(sub, r, w / 2 - 0.18, 0.15, zt, 0.07, 0.11)
        sub.xf(list(sub.bm.faces), T(px, py, 0) @ R("Z", yaw))
        B.mesh(sub, "biurko_sprzet")
        if k == 0:
            dl = MB()
            _desk_lamp(B, dl, -w / 2 + 0.22 if w > 1.2 else w / 2 - 0.15, py + (0.12 if not pair else -0.12),
                       zt, -150 if not pair else -30)
            B.mesh(dl, "lampka")
    # krzesła obrotowe
    chairs = [p for p in it.parts[1:] if p[0] == "cyl"]
    for p in chairs:
        x, y = _local(p)
        if pair:
            yy = max(-it.d / 2 + 0.33, min(it.d / 2 - 0.33, y))
            yy = (abs(yy) - 0.1) * (1 if yy > 0 else -1)
            yaw = 0.0 if y > 0 else 180.0
        else:
            yy = y0 - 0.12
            yy = max(yy, -it.d / 2 + 0.34)
            yaw = 180.0
        B.inst(("krzeslo_biurowe",), _office_chair_mesh, T(x, yy, 0) @ R("Z", yaw + r.uniform(-14, 14)), "krzeslo_biurowe")
    B.mesh(mb, "biurko")


# ------------------------------------------------------------------ łazienka
def _wanna(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    free = it.shapes[0][5] > 0.2
    mb = MB()
    H = 0.58
    p = 2.4 if free else 5.0
    nring = 64

    def ring(rx, ry, z, pp=p):
        return [(x, y, z) for x, y in _sel(0, 0, rx, ry, nring, pp)]
    rings = []
    if free:
        rings = [ring(w / 2 * 0.86, d / 2 * 0.82, 0.0), ring(w / 2 * 0.90, d / 2 * 0.86, 0.04), ring(w / 2 * 0.97, d / 2 * 0.95, H * 0.6),
                 ring(w / 2, d / 2, H - 0.012), ring(w / 2 - 0.006, d / 2 - 0.006, H), ring(w / 2 - 0.03, d / 2 - 0.03, H),
                 ring(w / 2 - 0.045, d / 2 - 0.045, H - 0.02), ring(w / 2 - 0.07, d / 2 - 0.07, 0.25),
                 ring(w / 2 - 0.12, d / 2 - 0.12, 0.09), ring(w / 2 - 0.2, d / 2 - 0.17, 0.06)]
    else:
        rings = [ring(w / 2, d / 2, 0.0), ring(w / 2, d / 2, H - 0.01), ring(w / 2 - 0.006, d / 2 - 0.006, H),
                 ring(w / 2 - 0.05, d / 2 - 0.05, H), ring(w / 2 - 0.065, d / 2 - 0.065, H - 0.02),
                 ring(w / 2 - 0.09, d / 2 - 0.09, 0.22, 3.2), ring(w / 2 - 0.14, d / 2 - 0.14, 0.09, 3.0),
                 ring(w / 2 - 0.22, d / 2 - 0.2, 0.06, 2.8)]
    bm = mb.bm
    vr = [[bm.verts.new(p_) for p_ in rg] for rg in rings]
    fs = []
    for k in range(len(vr) - 1):
        A, Bq = vr[k], vr[k + 1]
        for i in range(nring):
            j = (i + 1) % nring
            fs.append(bm.faces.new((A[i], A[j], Bq[j], Bq[i])))
    fs.append(bm.faces.new(list(reversed(vr[0]))))
    fs.append(bm.faces.new(vr[-1]))
    mb.tag(fs, "ceramika", True)
    mb.tag(fs[-2:], "ceramika", False)
    mb.cyl(-w / 2 + 0.25, 0, 0.061, 0.064, 0.035, "chrom", n=20)
    # bateria
    if free:
        px, py = -w / 2 + 0.09, d / 2 - 0.09
        mb.cyl(px, py, 0, 0.015, 0.06, "chrom", n=24, r=0.003)
        top = 0.98
        pts = [(px, py, 0.0), (px, py, top - 0.08)]
        for k in range(1, 7):
            a = math.pi * k / 6
            e = 0.09 * (1 - math.cos(a))
            pts.append((px + 0.7 * e, py - 0.7 * e, top - 0.08 + 0.09 * math.sin(a)))
        pts.append((pts[-1][0], pts[-1][1], pts[-1][2] - 0.04))
        mb.tube(pts, 0.014, "chrom", n=12)
        mb.cyl(px, py, 0.70, 0.75, 0.024, "chrom", n=16, r=0.003)
    else:
        mb.tube([(0, d / 2 - 0.005, 0.72), (0, d / 2 - 0.12, 0.72), (0, d / 2 - 0.16, 0.70)], 0.012, "chrom", n=12)
        mb.cyl(0.1, d / 2 - 0.02, 0.69, 0.75, 0.022, "chrom", n=16)
    B.mesh(mb, "wanna")


def _prysznic(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    mb = MB()
    mb.rbox(-w / 2, -d / 2, 0, w / 2, d / 2, 0.03, "kwarc_szary" if B.st["blat"] != "kwarc_szary" else "kwarc", rc=0.005, r=0.003)
    mb.box(-0.3, d / 2 - 0.12, 0.0305, 0.3, d / 2 - 0.08, 0.031, "stal", r=0)
    gl = 0.008
    pw = max(0.6, w - 0.28)
    x0 = -w / 2 + 0.005
    mb.box(x0, -d / 2 + 0.01, 0.03, x0 + pw, -d / 2 + 0.01 + gl, 2.0, "szklo", r=0.001)
    mb.box(x0, -d / 2 + 0.0, 1.98, x0 + pw, -d / 2 + 0.02 + gl, 2.0, "czarny_metal", r=0.002)
    mb.box(x0, -d / 2 + 0.0, 0.03, x0 + 0.02, -d / 2 + 0.02 + gl, 2.0, "czarny_metal", r=0.002)
    mb.box(x0 + 0.01, -d / 2 + 0.01, 0.03, x0 + pw, -d / 2 + 0.024, 0.045, "czarny_metal", r=0.002)
    mb.tube([(x0 + pw - 0.03, -d / 2 + 0.014, 1.97), (x0 + pw - 0.03, d / 2 - 0.005, 1.97)], 0.008, "czarny_metal", n=8)
    # deszczownica + termostat
    hx = 0.0
    mb.tube([(hx, d / 2 - 0.005, 2.12), (hx, d / 2 - 0.3, 2.12)], 0.01, "czarny_metal", n=10)
    mb.cyl(hx, d / 2 - 0.32, 2.09, 2.11, 0.15, "czarny_metal", n=40, r=0.004)
    mb.cyl(hx, d / 2 - 0.32, 2.088, 2.09, 0.135, "plastik_szary", n=40)
    mb.box(hx - 0.14, d / 2 - 0.035, 1.05, hx + 0.14, d / 2 - 0.005, 1.13, "czarny_metal", r=0.006)
    for sx in (-1, 1):
        mb.xf(mb.cyl(0, 0, 0, 0.03, 0.025, "czarny_metal", n=16, r=0.003), T(hx + sx * 0.1, d / 2 - 0.035, 1.09) @ R("X", 90))
    mb.tube([(hx + 0.12, d / 2 - 0.02, 1.1), (hx + 0.16, d / 2 - 0.03, 0.95), (hx + 0.18, d / 2 - 0.03, 1.25)], 0.006, "czarny_metal", n=8)
    B.mesh(mb, "prysznic")


def _taper(faces, yc, ylen, k=0.24, p=1.6):
    """Zwęża bryłę ku przodowi (−Y): x *= 1 − k·((yc − y)/ylen)^p dla części przedniej."""
    for v in {v for f in faces for v in f.verts}:
        t = max(0.0, (yc - v.co.y) / ylen)
        v.co.x *= 1 - k * t ** p


def _wc(B):
    it = B.it
    d = it.d
    mb = MB()
    yb = d / 2
    L = 0.55
    yc = yb - L / 2
    bowl = mb.soft(0.18, L / 2, 0.095, "ceramika", M=T(0, yc, 0.315), e1=0.42, e2=0.45, nu=40, nv=16)
    _taper(bowl, yc, L / 2, 0.3)
    for v in {v for f in bowl for v in f.verts}:           # spód wznosi się ku przodowi
        if v.co.z < 0.315:
            v.co.z += 0.05 * max(0.0, (yc - v.co.y) / (L / 2)) * (0.315 - v.co.z) / 0.095
    seat = mb.soft(0.178, L / 2 - 0.01, 0.009, "ceramika", M=T(0, yc - 0.005, 0.418), e1=0.5, e2=0.45, nu=40, nv=8)
    _taper(seat, yc - 0.005, L / 2 - 0.01, 0.3)
    lid = mb.soft(0.174, L / 2 - 0.02, 0.012, "ceramika", M=T(0, yc - 0.008, 0.437), e1=0.5, e2=0.45, nu=40, nv=8, puff=0.006)
    _taper(lid, yc - 0.008, L / 2 - 0.02, 0.3)
    mb.box(-0.09, yb - 0.04, 0.33, 0.09, yb, 0.40, "ceramika", r=0.01)
    # przycisk spłukiwania na ścianie
    mb.rbox(-0.12, yb - 0.012, 0.98, 0.12, yb, 1.14, "czarny_metal" if B.st["metal"] == "czarny_metal" else "chrom",
            rc=0.01, r=0.002)
    mb.box(-0.002, yb - 0.0125, 1.0, 0.002, yb - 0.012, 1.12, "plastik_szary", r=0)
    B.mesh(mb, "wc")


def _umywalki(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    mb = MB()
    zt = 0.85
    basins = [sh for sh in it.shapes if sh[0] == "e"]
    xs = [sh[1] for sh in basins] or [0.0]
    small = w < 0.8
    # szafka podwieszana + blat
    body = "drewno" if B.st["front"] is None or r.random() < 0.6 else "lak_front"
    if not small:
        mb.box(-w / 2 + 0.01, -d / 2 + 0.03, 0.40, w / 2 - 0.01, d / 2, zt - 0.03, body, r=0.003)
        n = max(1, int(round(w / 0.6)))
        g = 0.003
        fw = (w - 0.02 - g * (n + 1)) / n
        for i in range(n):
            x0 = -w / 2 + 0.01 + g + i * (fw + g)
            mb.box(x0, -d / 2 + 0.012, 0.40 + g, x0 + fw, -d / 2 + 0.031, zt - 0.03 - g, body, r=0.002)
            mb.box(x0 + fw * 0.3, -d / 2 + 0.008, zt - 0.03 - 0.05, x0 + fw * 0.7, -d / 2 + 0.013, zt - 0.03 - 0.045, "akcent", r=0.001)
    mb.box(-w / 2, -d / 2, zt - 0.03, w / 2, d / 2, zt, "marmur", r=0.003)
    for x in xs:
        rx, ry = (0.2, 0.15) if not small else (0.16, 0.12)
        y = -0.02
        o = _sel(0, 0, rx, ry, 48, 2.6)
        bm = mb.bm
        rings = [[(x + px * k, y + py * k, zt + zz) for px, py in o] for k, zz in
                 ((0.80, 0.0), (0.96, 0.05), (1.0, 0.13), (0.97, 0.135), (0.90, 0.12), (0.7, 0.04), (0.35, 0.02))]
        vr = [[bm.verts.new(p) for p in rg] for rg in rings]
        fs = []
        for k in range(len(vr) - 1):
            A, Bq = vr[k], vr[k + 1]
            for i in range(48):
                j = (i + 1) % 48
                fs.append(bm.faces.new((A[i], A[j], Bq[j], Bq[i])))
        fs.append(bm.faces.new(list(reversed(vr[0]))))
        fs.append(bm.faces.new(vr[-1]))
        mb.tag(fs, "ceramika", True)
        mb.cyl(x, y, zt + 0.021, zt + 0.023, 0.02, "chrom", n=16)
        # bateria ścienna
        fm = "czarny_metal" if B.st["metal"] == "czarny_metal" else "chrom"
        mb.rbox(x - 0.03, d / 2 - 0.006, zt + 0.25, x + 0.03, d / 2, zt + 0.33, fm, rc=0.008, r=0.002)
        mb.tube([(x, d / 2 - 0.005, zt + 0.27), (x, y + ry * 0.55, zt + 0.27)], 0.009, fm, n=10)
        mb.xf(mb.cyl(0, 0, 0, 0.05, 0.007, fm, n=10), T(x + 0.05, d / 2 - 0.005, zt + 0.29) @ R("X", 90))
    # lustro (na ścianie) z podświetleniem
    mw = min(w - 0.1, 1.2)
    if len(xs) > 1 and w > 1.2:
        for x in xs:
            mirror = mb.cyl(0, 0, 0, 0.012, 0.29, "lustro", n=48, r=0.002)
            mb.xf(mirror, T(x, d / 2, zt + 0.75) @ R("X", 90))
            ring = mb.torus(0, 0, 0, 0.292, 0.007, "akcent", nu=48, nv=6)
            mb.xf(ring, T(x, d / 2 - 0.012, zt + 0.75) @ R("X", 90))
    else:
        fs = mb.rbox(-mw / 2, -0.32, 0.0, mw / 2, 0.32, 0.012, "lustro", rc=0.05, r=0.002)
        mb.xf(fs, T(0, d / 2, zt + 0.70) @ R("X", 90))
    mb.box(-mw / 2 + 0.05, d / 2 - 0.03, zt + 0.355, mw / 2 - 0.05, d / 2 - 0.012, zt + 0.362, "led", r=0)
    B.light(None, 12.0 * max(1, len(xs)), kind="AREA", M=T(0, d / 2 - 0.05, zt + 0.75) @ R("X", -90), area=(mw, 0.5),
            temp=3000.0, name="led_lustro")
    # dozownik, ręcznik
    mb.cyl(w / 2 - 0.08, d / 2 - 0.08, zt, zt + 0.14, 0.032, "kamionka", n=20, r=0.004)
    mb.tube([(w / 2 - 0.08, d / 2 - 0.08, zt + 0.14), (w / 2 - 0.08, d / 2 - 0.08, zt + 0.17), (w / 2 - 0.08, d / 2 - 0.12, zt + 0.17)],
            0.005, "chrom", n=6)
    if not small:
        mb.soft(0.12, 0.09, 0.025, "tk_akcent1", M=T(-w / 2 + 0.15, 0.02, zt + 0.025), e1=0.3, e2=0.12, nu=20, nv=8)
    B.mesh(mb, "umywalki")


def _pralka(B):
    it = B.it
    mb = MB()
    W, D, H = 0.598, 0.58, 0.85
    mb.box(-W / 2, -D / 2, 0.015, W / 2, D / 2, H, "emalia", r=0.012, seg=3)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.cyl(sx * 0.25, sy * 0.22, 0, 0.016, 0.02, "plastik_szary", n=10)
    mb.box(-W / 2 + 0.01, -D / 2 - 0.004, H - 0.11, W / 2 - 0.01, -D / 2 + 0.01, H - 0.012, "emalia", r=0.004)
    mb.box(-W / 2 + 0.02, -D / 2 - 0.005, H - 0.1, -W / 2 + 0.2, -D / 2, H - 0.025, "emalia", r=0.003)
    mb.box(0.02, -D / 2 - 0.006, H - 0.085, 0.16, -D / 2, H - 0.04, "szklo_czarne", r=0.003)
    knob = mb.cyl(0, 0, 0, 0.028, 0.032, "chrom", n=24, r=0.004)
    mb.xf(knob, T(0.21, -D / 2, H - 0.062) @ R("X", 90))
    # drzwi: pierścień, szyba, środek
    cz = 0.42
    ring = mb.torus(0, 0, 0, 0.215, 0.028, "chrom", nu=48, nv=10)
    mb.xf(ring, T(0, -D / 2 - 0.02, cz) @ R("X", 90))
    glass = mb.lathe([(0.0, 0.065), (0.12, 0.058), (0.2, 0.02)], "szklo_dymione", n=48)
    mb.xf(glass, T(0, -D / 2, cz) @ R("X", 90))
    drum = mb.lathe([(0.0, 0.002), (0.15, 0.004), (0.19, 0.03)], "stal", n=40)
    mb.xf(drum, T(0, -D / 2, cz) @ R("X", 90))
    B.mesh(mb, "pralka")


def _zbiornik(B):
    mb = MB()
    Rr, H = 0.3, 1.86
    mb.lathe([(0.0, 0.03), (Rr - 0.02, 0.03), (Rr, 0.06), (Rr, H - 0.12), (Rr * 0.85, H - 0.03), (Rr * 0.4, H), (0.0, H)], "emalia", n=48)
    mb.cyl(0, 0, H - 0.05, H - 0.02, Rr * 0.95, "plastik_szary", n=48)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        mb.cyl(Rr * 0.7 * math.cos(a), Rr * 0.7 * math.sin(a), 0, 0.035, 0.025, "plastik_szary", n=10)
    mb.rbox(-0.09, -Rr - 0.004, 1.15, 0.09, -Rr + 0.03, 1.32, "plastik_szary", rc=0.015, r=0.003)
    mb.box(-0.06, -Rr - 0.006, 1.22, 0.06, -Rr, 1.28, "szklo_czarne", r=0.002)
    for k, x in enumerate((-0.12, 0.0, 0.12)):
        mb.tube([(x, Rr - 0.05, 0.5 + k * 0.25), (x, Rr + 0.02, 0.5 + k * 0.25), (x, Rr + 0.03, 0.5 + k * 0.25 + 0.05),
                 (x, Rr + 0.03, 2.05 + k * 0.08), (x, Rr + 0.06, 2.12 + k * 0.08)], 0.02, "czarny_mat" if k != 1 else "miedz", n=10)
    B.mesh(mb, "zbiornik")


def _pompa(B):
    it = B.it
    mb = MB()
    w, d = min(0.6, it.w - 0.05), min(0.55, it.d - 0.03)
    mb.box(-w / 2, -d / 2, 0, w / 2, d / 2, 1.0, "emalia", r=0.015, seg=3)
    mb.box(-w / 2 + 0.01, -d / 2 - 0.003, 0.0, w / 2 - 0.01, -d / 2 + 0.01, 0.1, "plastik_szary", r=0.003)
    mb.box(-0.08, -d / 2 - 0.004, 0.78, 0.08, -d / 2, 0.86, "szklo_czarne", r=0.003)
    for k in range(3):
        mb.tube([(-0.15 + k * 0.15, 0.0, 1.0), (-0.15 + k * 0.15, 0.0, 1.06), (-0.15 + k * 0.15, d / 2 + 0.02, 1.1),
                 (-0.15 + k * 0.15, d / 2 + 0.03, 2.4)], 0.018, "czarny_mat" if k != 1 else "miedz", n=10)
    B.mesh(mb, "pompa")


# ------------------------------------------------------------------ pokoje specjalne
def _poly_ymin(poly, x):
    """Najniższe y wielokąta na pionowej prostej x (do długości strun)."""
    best = None
    n = len(poly)
    for i in range(n):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
        if (ax - x) * (bx - x) <= 0 and abs(bx - ax) > 1e-9:
            y = ay + (by - ay) * (x - ax) / (bx - ax)
            best = y if best is None else min(best, y)
    return best


def _fortepian(B):
    it, r = B.it, B.rnd
    mb = MB()
    lak = "lak_czarny"
    # obrys: klawiatura po stronie +Y, prosta ściana basowa po lewej pianisty (+X), ogon w stronę −Y
    yk = 0.50
    tail = [(0.74, -0.20), (0.71, -0.62), (0.55, -0.92), (0.28, -1.06), (0.0, -1.06), (-0.22, -0.92), (-0.36, -0.58),
            (-0.50, -0.26), (-0.68, 0.02), (-0.74, 0.30)]
    poly = [(0.74, yk)] + _catmull(tail, 5, closed=False) + [(-0.74, yk)]
    area = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    if area < 0:
        poly = list(reversed(poly))
    z0, z1 = 0.66, 0.96
    mb.prism(poly, z0, z1, lak, r=0.006, seg=2, smooth=True)
    inner = [(x * 0.95, y * 0.96 - 0.01) for x, y in poly]
    mb.prism(inner, z1 - 0.12, z1 - 0.115, "swierk_y")
    plate = [(x * 0.88, y * 0.9 - 0.02) for x, y in poly]
    mb.prism(plate, z1 - 0.10, z1 - 0.075, "zloto", r=0.004, smooth=True)
    for k in range(44):
        x = -0.58 + k * 0.027
        ye = _poly_ymin(plate, x)
        if ye is None:
            continue
        mb.box(x, ye + 0.04, z1 - 0.074, x + 0.0018, yk - 0.14, z1 - 0.072, "stal", r=0)
    # pokrywa otwarta na podpórce (zawias po stronie basowej +X)
    fs = mb.prism(poly, 0.0, 0.018, lak, r=0.004, seg=2, smooth=True)
    mb.xf(fs, T(0.74, 0, z1 + 0.004) @ R("Y", 38) @ T(-0.74, 0, 0))
    mb.tube([(-0.30, -0.30, z1), (-0.30, -0.30, z1 + 0.80)], 0.009, lak, n=8)
    # klawiatura
    kb0, kb1 = yk, yk + 0.30
    mb.box(-0.74, kb0 - 0.02, 0.66, 0.74, kb1, 0.74, lak, r=0.004)
    for sx in (-1, 1):
        mb.box(sx * 0.74 - (0.06 if sx > 0 else 0), kb0, 0.74, sx * 0.74 + (0.06 if sx < 0 else 0), kb1, 0.80, lak, r=0.006)
    nw = 52
    kw = 1.36 / nw
    xk0 = -0.68
    for i in range(nw):
        x = xk0 + i * kw
        mb.box(x + 0.0006, kb0 + 0.12, 0.745, x + kw - 0.0006, kb1 - 0.012, 0.767, "porcelana", r=0.001, seg=1)
    pat = [1, 1, 0, 1, 1, 1, 0]
    for i in range(nw - 1):
        if pat[(i + 5) % 7]:
            x = xk0 + (i + 1) * kw
            mb.box(x - kw * 0.29, kb0 + 0.12, 0.767, x + kw * 0.29, kb0 + 0.215, 0.781, lak, r=0.0015, seg=1)
    mb.box(-0.68, kb0 + 0.02, 0.745, 0.68, kb0 + 0.12, 0.83, lak, r=0.004)
    mb.box(-0.68, kb1 - 0.012, 0.70, 0.68, kb1, 0.755, lak, r=0.003)
    # pulpit z nutami (pochylony od pianisty)
    desk = mb.box(-0.32, -0.012, 0, 0.32, 0.012, 0.28, lak, r=0.004)
    paper = mb.box(-0.28, 0.0122, 0.05, -0.003, 0.0125, 0.27, "papier", r=0)
    paper += mb.box(0.003, 0.0122, 0.05, 0.28, 0.0125, 0.27, "papier", r=0)
    mb.xf(desk + paper, T(0, kb0 + 0.03, 0.83) @ R("X", 16))
    # nogi i lira z pedałami
    for (x, y) in ((0.62, kb0 + 0.10), (-0.62, kb0 + 0.10), (0.06, -0.92)):
        mb.prism(_rrect(x - 0.045, y - 0.045, x + 0.045, y + 0.045, 0.01, 3), 0.04, z0, lak, smooth=True,
                 top=_rrect(x - 0.06, y - 0.06, x + 0.06, y + 0.06, 0.012, 3))
        mb.cyl(x, y, 0.0, 0.04, 0.025, "mosiadz", n=12)
    mb.box(-0.12, kb0 + 0.10, 0.08, 0.12, kb0 + 0.13, z0, lak, r=0.004)
    for k in range(3):
        mb.box(-0.06 + k * 0.05 - 0.012, kb0 + 0.13, 0.085, -0.06 + k * 0.05 + 0.012, kb0 + 0.24, 0.095, "mosiadz", r=0.003)
    # ława
    by = min(it.d / 2 - 0.17, kb1 + 0.19)
    mb.rbox(-0.32, by - 0.16, 0.44, 0.32, by + 0.16, 0.5, "skora", rc=0.02, r=0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(sx * 0.28 - 0.02, by + sy * 0.12 - 0.02, 0, sx * 0.28 + 0.02, by + sy * 0.12 + 0.02, 0.44, lak, r=0.004)
    B.mesh(mb, "fortepian")


def _sztaluga(B):
    it, r = B.it, B.rnd
    mb = MB()
    wz = "buk_z"
    mb.tube([(-0.32, -0.22, 0.0), (-0.03, -0.02, 1.72)], 0.018, wz, n=8)
    mb.tube([(0.32, -0.22, 0.0), (0.03, -0.02, 1.72)], 0.018, wz, n=8)
    mb.tube([(0.0, 0.26, 0.0), (0.0, 0.0, 1.62)], 0.016, wz, n=8)
    mb.box(-0.30, -0.24, 0.62, 0.30, -0.15, 0.645, "buk", r=0.003)
    mb.box(-0.30, -0.25, 0.645, 0.30, -0.235, 0.665, "buk", r=0.003)
    cw, ch = 0.6, 0.78
    canvas = mb.box(-cw / 2, -0.03, 0.0, cw / 2, 0.0, ch, "plotno", r=0.002)
    face = mb.box(-cw / 2 + 0.002, -0.0305, 0.002, cw / 2 - 0.002, -0.03, ch - 0.002, f"obraz:{B.idx}", r=0)
    mb.xf(canvas + face, T(0, -0.17, 0.665) @ R("X", -8))
    mb.box(-0.06, -0.08, 0.665 + ch + 0.02, 0.06, -0.05, 0.665 + ch + 0.06, "buk", r=0.003)
    # paleta i pędzle w słoiku obok
    mb.cyl(0.38, 0.1, 0, 0.0, 0.0, "buk", n=3)
    B.mesh(mb, "sztaluga")


def _warsztat(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    mb = MB()
    zt = 0.9
    mb.box(-w / 2, -d / 2, zt - 0.06, w / 2, d / 2, zt, "buk", r=0.004)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (w / 2 - 0.08), sy * (d / 2 - 0.08)
            mb.box(x - 0.04, y - 0.04, 0, x + 0.04, y + 0.04, zt - 0.06, "buk_z", r=0.004)
    for sy in (-1, 1):
        mb.box(-w / 2 + 0.12, sy * (d / 2 - 0.08) - 0.02, 0.15, w / 2 - 0.12, sy * (d / 2 - 0.08) + 0.02, 0.23, "buk", r=0.003)
    mb.box(-w / 2 + 0.12, -d / 2 + 0.06, 0.23, w / 2 - 0.12, d / 2 - 0.06, 0.25, "buk", r=0.003)
    # imadło
    vx = w / 2 - 0.25
    mb.box(vx - 0.1, -d / 2 - 0.03, zt - 0.12, vx + 0.1, -d / 2 + 0.01, zt + 0.02, "buk", r=0.004)
    mb.tube([(vx, -d / 2 - 0.03, zt - 0.06), (vx, -d / 2 - 0.12, zt - 0.06)], 0.012, "stal", n=8)
    mb.tube([(vx - 0.1, -d / 2 - 0.12, zt - 0.06), (vx + 0.1, -d / 2 - 0.12, zt - 0.06)], 0.008, "stal", n=8)
    # tablica narzędziowa na ścianie
    pw = min(w - 0.2, 1.6)
    mb.box(-pw / 2, d / 2 - 0.02, 1.05, pw / 2, d / 2, 1.85, "perforowana", r=0.003)
    tools = MB()
    y = d / 2 - 0.035
    x = -pw / 2 + 0.1
    seq = ["mlotek", "srubokrety", "klucze", "pila", "scisk", "mlotek", "obcegi", "scisk", "srubokrety"]
    for tool in seq:
        if x > pw / 2 - 0.15:
            break
        if tool == "mlotek":
            tools.box(x - 0.012, y - 0.012, 1.25, x + 0.012, y + 0.012, 1.55, "buk_z", r=0.004)
            tools.box(x - 0.06, y - 0.016, 1.55, x + 0.06, y + 0.016, 1.585, "stal", r=0.004)
            x += 0.17
        elif tool == "srubokrety":
            for j in range(4):
                xx = x + j * 0.04
                tools.cyl(xx, y, 1.42, 1.53, 0.012, "kolor", n=10, r=0.003)
                tools.setcol(tools.cyl(xx, y, 1.42, 1.53, 0.0125, "kolor", n=10), lin(((0.7, 0.1, 0.08), (0.95, 0.75, 0.1), (0.1, 0.25, 0.6), (0.1, 0.1, 0.1))[j]) + (1.0,))
                tools.cyl(xx, y, 1.30, 1.42, 0.003, "chrom", n=6)
            x += 0.2
        elif tool == "klucze":
            for j in range(5):
                tools.box(x + j * 0.032, y - 0.004, 1.32 - j * 0.025, x + j * 0.032 + 0.016, y + 0.004, 1.56, "chrom", r=0.002)
            x += 0.2
        elif tool == "pila":
            tools.box(x, y - 0.001, 1.42, x + 0.3, y + 0.001, 1.53, "stal", r=0)
            tools.box(x + 0.3, y - 0.015, 1.40, x + 0.4, y + 0.015, 1.56, "buk", r=0.008)
            x += 0.45
        elif tool == "scisk":
            tools.box(x - 0.01, y - 0.008, 1.2, x + 0.01, y + 0.008, 1.6, "stal", r=0.002)
            tools.box(x - 0.01, y - 0.02, 1.58, x + 0.12, y + 0.02, 1.6, "czarny_metal", r=0.003)
            tools.box(x - 0.01, y - 0.02, 1.35, x + 0.12, y + 0.02, 1.37, "czarny_metal", r=0.003)
            tools.box(x + 0.09, y - 0.012, 1.27, x + 0.11, y + 0.012, 1.35, "kolor", r=0.004)
            x += 0.2
        else:   # obcęgi
            tools.tube([(x, y, 1.3), (x + 0.02, y, 1.45), (x + 0.03, y, 1.5)], 0.008, "czarny_metal", n=6)
            tools.tube([(x + 0.06, y, 1.3), (x + 0.04, y, 1.45), (x + 0.03, y, 1.5)], 0.008, "czarny_metal", n=6)
            x += 0.12
    # na blacie: strug, pudełko, deski
    tools.box(-0.2, -0.1, zt, 0.08, -0.04, zt + 0.06, "buk", r=0.006)
    tools.box(-0.15, -0.095, zt + 0.06, -0.12, -0.045, zt + 0.12, "stal", r=0.003)
    tools.box(0.3, 0.05, zt, 1.0 if w > 2.0 else 0.6, 0.2, zt + 0.02, "dab", r=0.002)
    B.mesh(tools, "narzedzia")
    B.mesh(mb, "warsztat")
    B.model("AnisotropyBarnLamp.glb", T(-pw / 2 - 0.12 if w > 1.8 else 0.0, d / 2, 1.95) @ Sc(1.2))
    B.light((-pw / 2 - 0.12 if w > 1.8 else 0.0, d / 2 - 0.16, 1.78), 18.0, size=0.03, name="kinkiet")


def _czajnik(B):
    it, r = B.it, B.rnd
    p0 = it.parts[0]
    w, d = p0[4], p0[5]
    mb = MB()
    zt = 0.33
    mb.rbox(-w / 2, -d / 2, zt - 0.035, w / 2, d / 2, zt, "orzech", rc=0.02, r=0.005)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(sx * (w / 2 - 0.08) - 0.03, sy * (d / 2 - 0.07) - 0.03, 0, sx * (w / 2 - 0.08) + 0.03,
                   sy * (d / 2 - 0.07) + 0.03, zt - 0.035, "orzech_z", r=0.004)
    for sh in it.shapes[1:]:
        if sh[0] == "r":
            cx, cy = sh[1] + sh[3] / 2, -(sh[2] + sh[4] / 2)
            mb.soft(0.25, 0.25, 0.045, "tk_akcent0" if (cx > 0) == (cy > 0) else "tk_obicie",
                    M=T(cx, cy, 0.045) @ R("Z", r.uniform(-6, 6)), e1=0.35, e2=0.15, puff=0.012)
    # czajniczek żeliwny i tacka
    mb.rbox(-0.2, -0.14, zt, 0.2, 0.14, zt + 0.015, "drewno", rc=0.02, r=0.003)
    tp = [(0.0, 0.0), (0.06, 0.0), (0.085, 0.04), (0.08, 0.08), (0.04, 0.1), (0.03, 0.11), (0.0, 0.11)]
    mb.lathe(tp, "czarny_metal", n=28, x=-0.08, y=0.0, z=zt + 0.015)
    mb.tube([(-0.08 - 0.07, 0.0, zt + 0.07), (-0.08 - 0.13, 0.0, zt + 0.1)], [0.012, 0.007], "czarny_metal", n=8)
    mb.tube([(-0.14, 0.0, zt + 0.11), (-0.08, 0.0, zt + 0.19), (-0.02, 0.0, zt + 0.11)], 0.004, "czarny_metal", n=6, cap=False)
    B.mesh(mb, "czajnik")
    for k, (x, y) in enumerate(((0.07, -0.06), (0.1, 0.07))):
        B.model("DiffuseTransmissionTeacup.glb", T(x, y, zt + 0.015) @ R("Z", 30 + 100 * k))


def _tokonoma(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    mb = MB()
    mb.box(-w / 2, -d / 2, 0, w / 2, d / 2, 0.22, "orzech", r=0.004)
    mb.box(-w / 2 + 0.02, -d / 2 + 0.02, 0, w / 2 - 0.02, d / 2, 0.02, "cokol", r=0.001)
    # zwój na ścianie
    mb.box(-0.22, d / 2 - 0.006, 0.9, 0.22, d / 2 - 0.002, 2.0, "papier", r=0)
    mb.box(-0.18, d / 2 - 0.0065, 1.15, 0.18, d / 2 - 0.006, 1.8, "obraz:7", r=0)
    for z in (0.9, 2.0):
        mb.cyl(0, 0, -0.25, 0.25, 0.012, "orzech", n=10)
        mb.xf(mb.bm.faces[-12:], T(0, d / 2 - 0.015, z) @ R("Y", 90))
    _vase(mb, 0.35, 0.0, 0.22, 0.2, 0.07, "kamionka", kind=1)
    _stems(mb, 0.35, 0.0, 0.36, 0.5, 5, r)
    B.mesh(mb, "tokonoma")
    _, (mn, mx) = _glb(B.ctx, "GlassVaseFlowers.glb")
    B.model("GlassVaseFlowers.glb", T(-0.4, 0.0, 0.22) @ Sc(1.2))


def _lezak(B):
    it, r = B.it, B.rnd

    def make():
        mb = MB()
        L, W = 1.95, 0.66
        for sx in (-1, 1):
            x = sx * (W / 2 - 0.03)
            mb.box(x - 0.025, -L / 2, 0.2, x + 0.025, L / 2 - 0.02, 0.29, "tik", r=0.005)
            for y in (-L / 2 + 0.08, L / 2 - 0.12):
                mb.box(x - 0.025, y - 0.03, 0.0, x + 0.025, y + 0.03, 0.2, "tik_z", r=0.005)
        mb.box(-W / 2 + 0.055, -L / 2 + 0.03, 0.24, W / 2 - 0.055, -L / 2 + 0.07, 0.28, "tik", r=0.004)
        ns = 18
        for k in range(ns):
            y = -L / 2 + 0.05 + k * (L * 0.68) / ns
            mb.box(-W / 2 + 0.055, y, 0.27, W / 2 - 0.055, y + 0.055, 0.29, "tik", r=0.004)
        # oparcie uniesione (głowa po +Y)
        back = []
        for k in range(8):
            y = k * 0.075
            back += mb.box(-W / 2 + 0.06, y, 0.0, W / 2 - 0.06, y + 0.055, 0.02, "tik", r=0.004)
        for sx in (-1, 1):
            back += mb.box(sx * (W / 2 - 0.08) - 0.02, 0, -0.03, sx * (W / 2 - 0.08) + 0.02, 0.6, 0.0, "tik", r=0.004)
        mb.xf(back, T(0, L / 2 - 0.62, 0.29) @ R("X", 38))
        cush = mb.soft(W / 2 - 0.05, 0.62, 0.035, "tk_ogrod", M=T(0, -L / 2 + 0.68, 0.33), e1=0.3, e2=0.1, nu=36, nv=10, puff=0.008)
        cb = mb.soft(W / 2 - 0.05, 0.3, 0.035, "tk_ogrod", M=T(0, 0.3, 0.035), e1=0.3, e2=0.1, nu=36, nv=10, puff=0.008)
        mb.xf(cb, T(0, L / 2 - 0.62, 0.29) @ R("X", 38))
        mb.pillow(0.4, 0.25, 0.1, "tk_akcent0", T(0, L / 2 - 0.3, 0.62) @ R("X", 60))
        return mb
    B.inst(("lezak",), make, R("Z", 0), "lezak")


def _lawka(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    out = B.outdoor or B.rk in ("oranzeria",)
    mb = MB()
    H = 0.45
    if out:
        ns = max(3, int(d / 0.09))
        for k in range(ns):
            y = -d / 2 + k * d / ns
            mb.box(-w / 2, y + 0.004, H - 0.03, w / 2, y + d / ns - 0.004, H, "tik", r=0.004)
        for sx in (-1, 1):
            x = sx * (w / 2 - 0.12)
            mb.box(x - 0.03, -d / 2 + 0.03, 0, x + 0.03, d / 2 - 0.03, H - 0.03, "tik_z", r=0.005)
    elif B.rk == "galeria":
        mb.box(-w / 2, -d / 2, H - 0.06, w / 2, d / 2, H, "drewno", r=0.006)
        for sx in (-1, 1):
            x = sx * (w / 2 - 0.25)
            mb.box(x - 0.06, -d / 2 + 0.05, 0, x + 0.06, d / 2 - 0.05, H - 0.06, "trawertyn", r=0.004)
    else:
        mb.box(-w / 2, -d / 2, H - 0.1, w / 2, d / 2, H - 0.06, "drewno", r=0.005)
        for sx in (-1, 1):
            for sy in (-1, 1):
                x, y = sx * (w / 2 - 0.07), sy * (d / 2 - 0.06)
                mb.tube([(x * 1.02, y * 1.06, 0), (x, y, H - 0.1)], [0.016, 0.02], "drewno_z", n=10)
        mb.soft(w / 2 - 0.01, d / 2 - 0.01, 0.03, "tk_obicie" if B.rk != "sypialnia_glowna" else "boucle",
                M=T(0, 0, H - 0.03), e1=0.3, e2=0.08, nu=40, nv=10, puff=0.006)
        if B.rk in ("wiatrolap", "hol", "korytarz"):
            mb.box(-w / 2 + 0.1, -d / 2 + 0.05, 0.0, -w / 2 + 0.45, d / 2 - 0.08, 0.012, "lina", r=0.002)
    B.mesh(mb, "lawka")


def _lawa(B):
    it = B.it
    w, d = it.w, it.d
    mb = MB()
    # górna ława (przy ścianie) i stopień przed nią, na słupkach
    for (y0, y1, z) in ((d / 2 - 0.44, d / 2, 0.9), (-d / 2, -d / 2 + 0.2, 0.45)):
        ns = max(2, int((y1 - y0) / 0.095))
        for k in range(ns):
            ya = y0 + k * (y1 - y0) / ns
            mb.box(-w / 2, ya + 0.005, z - 0.026, w / 2, ya + (y1 - y0) / ns - 0.005, z, "sauna", r=0.004)
        npost = max(2, int(w / 0.7) + 1)
        for j in range(npost):
            x = -w / 2 + 0.04 + j * (w - 0.08) / (npost - 1)
            for yy in (y0 + 0.04, y1 - 0.04):
                mb.box(x - 0.022, yy - 0.022, 0, x + 0.022, yy + 0.022, z - 0.026, "sauna_z", r=0.003)
            mb.box(x - 0.02, y0 + 0.02, z - 0.07, x + 0.02, y1 - 0.02, z - 0.026, "sauna", r=0.003)
    # oparcie z listew na ścianie
    for k in range(4):
        zz = 1.05 + k * 0.13
        mb.box(-w / 2 + 0.05, d / 2 - 0.03, zz, w / 2 - 0.05, d / 2 - 0.005, zz + 0.085, "sauna", r=0.004)
    for x in (-w / 2 + 0.1, w / 2 - 0.1):
        mb.box(x - 0.02, d / 2 - 0.01, 1.0, x + 0.02, d / 2, 1.6, "sauna_z", r=0.002)
    B.mesh(mb, "lawa")


def _piec(B):
    it, r = B.it, B.rnd
    mb = MB()
    W, D, H = 0.44, 0.42, 0.62
    mb.box(-W / 2, -D / 2, 0.06, W / 2, D / 2, H, "czarny_metal", r=0.008)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(sx * (W / 2 - 0.04) - 0.015, sy * (D / 2 - 0.04) - 0.015, 0, sx * (W / 2 - 0.04) + 0.015,
                   sy * (D / 2 - 0.04) + 0.015, 0.06, "czarny_metal", r=0.003)
    mb.box(-0.14, -D / 2 - 0.012, 0.16, 0.14, -D / 2 + 0.002, 0.42, "czarny_metal", r=0.006)
    mb.box(-0.11, -D / 2 - 0.014, 0.19, 0.11, -D / 2 - 0.01, 0.39, "szklo_dymione", r=0.002)
    mb.box(-0.11, -D / 2 + 0.003, 0.19, 0.11, -D / 2 + 0.006, 0.39, "zar", r=0)
    mb.tube([(0.12, -D / 2 - 0.02, 0.3), (0.12, -D / 2 - 0.05, 0.3), (0.12, -D / 2 - 0.05, 0.36)], 0.008, "drewno_z", n=8)
    # kosz z kamieniami
    for sx in (-1, 1):
        mb.box(sx * (W / 2 - 0.01) - 0.01, -D / 2, H, sx * (W / 2 - 0.01) + 0.01, D / 2, H + 0.2, "czarny_metal", r=0.002)
    for k in range(28):
        x, y = r.uniform(-W / 2 + 0.06, W / 2 - 0.06), r.uniform(-D / 2 + 0.06, D / 2 - 0.06)
        z = H + 0.04 + r.uniform(0, 0.14)
        rr = r.uniform(0.035, 0.055)
        mb.soft(rr, rr * r.uniform(0.7, 1.0), rr * r.uniform(0.55, 0.8), "kamienie",
                M=T(x, y, z) @ R("Z", r.uniform(0, 180)) @ R("X", r.uniform(-20, 20)), e1=0.8, e2=0.8, nu=10, nv=6)
    B.mesh(mb, "piec")
    li = B.light((0, -D / 2 - 0.15, 0.3), 25.0, size=0.1, temp=1900.0, name="piec")
    B.flicker(li, 0.3)


def _mata(B):
    it, r = B.it, B.rnd
    mb = MB()
    w, L = 0.61, 1.83
    mb.rbox(-w / 2, -L / 2, 0, w / 2, L / 2 - 0.25, 0.006, "mata", rc=0.02, r=0.002, seg=1)

    def roll(u, v):
        a = 2 * math.pi * 1.6 * u
        rr = 0.05 - 0.012 * u
        return ((v - 0.5) * w, L / 2 - 0.25 + 0.0 + rr * math.sin(a), 0.05 - rr * math.cos(a) + 0.001)
    mb.surf(roll, 40, 4, "mata", flip=True)
    B.mesh(mb, "mata", R("Z", r.uniform(-3, 3)))


def _wino(B):
    it, r = B.it, B.rnd
    w, d = it.w, it.d
    H = min(2.2, (B.ceil or 2.4) - 0.05)
    mb = MB()
    wood = "orzech"
    mb.box(-w / 2, -d / 2, 0, -w / 2 + 0.025, d / 2, H, wood + "_z", r=0.003)
    mb.box(w / 2 - 0.025, -d / 2, 0, w / 2, d / 2, H, wood + "_z", r=0.003)
    mb.box(-w / 2, -d / 2, H - 0.025, w / 2, d / 2, H, wood, r=0.003)
    mb.box(-w / 2 + 0.02, -d / 2 + 0.03, 0, w / 2 - 0.02, d / 2, 0.08, "cokol", r=0.002)
    bt = MB()
    rows = int((H - 0.45) / 0.105)
    cols = int((w - 0.06) / 0.11)
    caps = [(0.40, 0.05, 0.08), (0.08, 0.08, 0.08), (0.75, 0.62, 0.30), (0.55, 0.10, 0.15), (0.85, 0.83, 0.78)]
    for j in range(rows):
        z = 0.08 + j * 0.105
        mb.box(-w / 2 + 0.025, -d / 2 + 0.02, z, w / 2 - 0.025, -d / 2 + 0.04, z + 0.018, wood, r=0.002)
        mb.box(-w / 2 + 0.025, d / 2 - 0.12, z, w / 2 - 0.025, d / 2 - 0.1, z + 0.018, wood, r=0.002)
        for i in range(cols):
            if r.random() < 0.14:
                continue
            x = -w / 2 + 0.03 + (i + 0.5) * (w - 0.06) / cols
            zc = z + 0.018 + 0.037
            fs = bt.lathe([(0.0, -0.17), (0.037, -0.165), (0.037, 0.05), (0.014, 0.11), (0.014, 0.16), (0.0, 0.165)],
                          "szklo_butelka", n=14)
            capf = bt.lathe([(0.0, 0.11), (0.0152, 0.112), (0.0152, 0.163), (0.0, 0.166)], "folia", n=14)
            bt.setcol(capf, lin(r.choice(caps)) + (1.0,))
            bt.xf(fs + capf, T(x, -d / 2 + 0.17, zc) @ R("X", 90))
    top = H - 0.3
    mb.box(-w / 2 + 0.025, -d / 2, top, w / 2 - 0.025, d / 2, top + 0.025, wood, r=0.003)
    for k in range(4):
        bt.lathe([(0.0, 0.0), (0.038, 0.0), (0.04, 0.003), (0.04, 0.03), (0.003, 0.11), (0.003, 0.17), (0.035, 0.175),
                  (0.042, 0.23), (0.0, 0.232)], "szklo_cienkie", n=18, x=-w / 2 + 0.2 + k * 0.1, y=0, z=top + 0.025)
    B.mesh(mb, "wino")
    B.mesh(bt, "butelki")


def _cokol(B):
    it, r = B.it, B.rnd
    s = it.w
    mb = MB()
    a = s * 0.42
    mb.box(-a, -a, 0, a, a, 1.0, "tynk", r=0.003)
    sc_ = MB()
    kind = (B.idx + B.ctx.seed) % 3
    if kind == 0:   # skręcona pętla
        def f(u, v):
            t = 2 * math.pi * u
            ph = 2 * math.pi * v
            Rr = 0.15 + 0.03 * math.sin(2 * t)
            rr = 0.045 + 0.02 * math.cos(t)
            tw = t * 0.5
            cx, cz = Rr * math.cos(t), Rr * math.sin(t)
            ox, oy = rr * math.cos(ph + tw) * 1.6, rr * math.sin(ph + tw) * 0.7
            return ((cx + ox * math.cos(t)), oy, 1.0 + 0.19 + cz + ox * math.sin(t))
        sc_.surf(f, 64, 16, "braz", cu=True, cv=True, flip=True)
        sc_.box(-0.05, -0.04, 1.0, 0.05, 0.04, 1.04, "braz", r=0.004)
    elif kind == 1:  # kamienie ułożone w stos
        z = 1.0
        for k, (rx, rz) in enumerate(((0.13, 0.05), (0.10, 0.045), (0.075, 0.04), (0.05, 0.035))):
            sc_.soft(rx, rx * 0.8, rz, "braz", M=T(r.uniform(-0.01, 0.01), 0, z + rz * 0.95) @ R("Z", r.uniform(0, 90)) @ R("X", r.uniform(-6, 6)),
                     e1=0.8, e2=0.8, nu=24, nv=12)
            z += rz * 1.85
    else:           # smukły owal z otworem
        def f(u, v):
            t = 2 * math.pi * u
            ph = 2 * math.pi * v
            Rr = 0.09
            rr = 0.055 * (1 + 0.5 * math.sin(t) ** 2)
            cx, cz = Rr * math.cos(t), 1.5 * Rr * math.sin(t)
            return (cx + rr * math.cos(ph) * math.cos(t), rr * math.sin(ph) * 0.6, 1.0 + 0.2 + cz + rr * math.cos(ph) * math.sin(t) * 1.3)
        sc_.surf(f, 56, 14, "braz", cu=True, cv=True, flip=True)
        sc_.box(-0.04, -0.035, 1.0, 0.04, 0.035, 1.07, "braz", r=0.004)
    B.mesh(mb, "cokol")
    B.mesh(sc_, "rzezba", R("Z", r.uniform(-40, 40)))


def _citrus_mesh(r):
    mb = MB()
    mb.tube([(0, 0, 0.5), (0.01, 0.0, 0.85), (-0.01, 0.01, 1.15)], [0.03, 0.024, 0.018], "pien", n=10)
    for k in range(5):
        a = k * 2 * math.pi / 5 + 0.3
        mb.tube([(0, 0, 1.0 + k * 0.04), (0.18 * math.cos(a), 0.18 * math.sin(a), 1.2 + k * 0.04)], [0.012, 0.006], "pien", n=6)
    cz, Rx, Rz = 1.38, 0.42, 0.36
    rng = random.Random(7)
    for k in range(900):
        while True:
            v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
            if 0.55 < v.length <= 1.0:
                break
        p = Vector((v.x * Rx, v.y * Rx, v.z * Rz + cz))
        out = v.normalized()
        L = rng.uniform(0.05, 0.08)
        yaw = math.degrees(math.atan2(out.y, out.x)) + rng.uniform(-50, 50)
        pitch = -math.degrees(math.asin(max(-1, min(1, out.z)))) * 0.6 + rng.uniform(-30, 30)
        fs = _leaf(mb, L)
        mb.xf(fs, T(*p) @ R("Z", yaw) @ R("Y", pitch) @ R("X", rng.uniform(-40, 40)))
        mb.setcol(fs, lin((0.11 + rng.uniform(-0.03, 0.04), 0.27 + rng.uniform(-0.05, 0.06), 0.07)) + (1.0,))
    for k in range(16):
        while True:
            v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 0.6)))
            if 0.75 < v.length <= 1.0:
                break
        mb.sphere(v.x * Rx * 1.02, v.y * Rx * 1.02, v.z * Rz + cz, 0.036, "pomarancza", n=12)
    return mb


def _leaf(mb, L):
    bm = mb.bm
    W = L * 0.38
    pts = [(0.0, 0.0, 0.0), (L * 0.3, W * 0.5, 0.004), (L * 0.65, W * 0.42, 0.002), (L, 0.0, -0.003),
           (L * 0.65, -W * 0.42, 0.002), (L * 0.3, -W * 0.5, 0.004), (L * 0.5, 0.0, -0.002)]
    v = [bm.verts.new(p) for p in pts]
    fs = [bm.faces.new((v[6], v[i], v[i + 1])) for i in range(5)] + [bm.faces.new((v[6], v[5], v[0]))]
    return mb.tag(fs, "lisc", True)


def _donica(B):
    it, r = B.it, B.rnd
    Rr = it.w / 2 - 0.02
    cyt = any(p[-1] == "lisc_cytrus" for p in it.parts)
    mb = MB()
    key = "terakota" if cyt else "beton"
    H = 0.55
    mb.lathe([(0.0, 0.0), (Rr * 0.82, 0.0), (Rr * 0.86, 0.02), (Rr, H - 0.02), (Rr - 0.005, H), (Rr - 0.03, H), (Rr - 0.035, H - 0.04),
              (Rr - 0.04, H - 0.05), (0.0, H - 0.05)], key, n=48)
    mb.cyl(0, 0, H - 0.07, H - 0.05, Rr - 0.04, "ziemia", n=40)
    B.mesh(mb, "donica")
    if cyt:
        s = min(1.0, Rr / 0.38)
        B.inst(("cytrus",), lambda: _citrus_mesh(r), Sc(s, s, 1.0) @ R("Z", r.uniform(0, 360)), "drzewko")
    else:
        parts, (mn, mx) = _glb(B.ctx, "DiffuseTransmissionPlant.glb")
        s = 1.55 * min(1.0, Rr / 0.38)
        B.model("DiffuseTransmissionPlant.glb", T(0, 0, H - 0.07 - 0.30 * s) @ R("Z", r.uniform(0, 360)) @ Sc(s), skip=("pot", "dirt"))


def _auto(B):
    it = B.it
    parts, (mn, mx) = _glb(B.ctx, "CarConcept.glb")
    L = mx.y - mn.y
    s = it.d / L * 0.98
    M = Sc(s) @ T(-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z)
    B.model("CarConcept.glb", M)


def _stolek(B):
    r = B.rnd

    def make():
        mb = MB()
        mb.cyl(0, 0, 0.58, 0.62, 0.17, "buk", n=36, r=0.006)
        for k in range(3):
            a = math.radians(90 + 120 * k)
            mb.tube([(0.2 * math.cos(a), 0.2 * math.sin(a), 0.0), (0.12 * math.cos(a), 0.12 * math.sin(a), 0.58)], [0.014, 0.017], "buk_z", n=10)
        mb.torus(0, 0, 0.2, 0.165, 0.008, "buk", nu=36, nv=6)
        return mb
    B.inst(("stolek",), make, R("Z", r.uniform(0, 120)), "stolek")


def _rower(B):
    mb = MB()
    mb.tube([(0, -0.55, 0.0), (0, 0.55, 0.0)], 0.03, "czarny_metal", n=10)
    mb.tube([(-0.25, -0.5, 0.02), (0.25, -0.5, 0.02)], 0.03, "czarny_metal", n=10)
    mb.tube([(-0.25, 0.5, 0.02), (0.25, 0.5, 0.02)], 0.03, "czarny_metal", n=10)
    mb.tube([(0, 0.45, 0.02), (0, 0.1, 0.55), (0, 0.08, 0.82)], 0.03, "czarny_metal", n=10)
    mb.tube([(0, 0.2, 0.42), (0, -0.4, 0.75), (0, -0.42, 1.0)], 0.03, "czarny_metal", n=10)
    wheel = mb.cyl(0, 0, -0.025, 0.025, 0.24, "chrom", n=40, r=0.01)
    mb.xf(wheel, T(0, -0.38, 0.32) @ R("Y", 90))
    cover = mb.cyl(0, 0, -0.03, 0.03, 0.16, "czarny_metal", n=32, r=0.01)
    mb.xf(cover, T(0, -0.38, 0.32) @ R("Y", 90))
    mb.soft(0.09, 0.14, 0.035, "plastik_czarny", M=T(0, 0.08, 0.86), e1=0.5, e2=0.5, nu=20, nv=8)
    mb.tube([(-0.24, -0.45, 1.05), (-0.1, -0.42, 1.0), (0.1, -0.42, 1.0), (0.24, -0.45, 1.05)], 0.014, "guma", n=8)
    for sx in (-1, 1):
        mb.tube([(sx * 0.05, 0.12, 0.3), (sx * 0.14, 0.12, 0.3)], 0.01, "aluminium", n=6)
        mb.box(sx * 0.14 - 0.05 * (sx < 0), 0.07, 0.29, sx * 0.14 + 0.05 * (sx > 0), 0.17, 0.31, "plastik_czarny", r=0.004)
    B.mesh(mb, "rower")


def _ekran(B):
    it = B.it
    w = it.w
    mb = MB()
    z0, z1 = 0.6, 2.2
    y = it.d / 2 - 0.02
    mb.box(-w / 2, y - 0.03, z0, w / 2, y + 0.02, z1, "czarny_mat", r=0.004)
    mb.box(-w / 2 + 0.06, y - 0.031, z0 + 0.06, w / 2 - 0.06, y - 0.03, z1 - 0.06, "ekran_proj" if not B.dusk else "ekran", r=0)
    B.mesh(mb, "ekran")


def _ogolny(B):
    """Nieznany rodzaj: fazowane bryły ze starych części z sensownymi materiałami."""
    it = B.it
    mb = MB()
    MAP = {"tkanina": "tk_obicie", "tkanina_ciemna": "tk_ciemna", "drewno_mebel": "drewno", "rama_mebel": "czarny_metal",
           "kuchnia": "lak_front", "ceramika": "emalia", "posciel": "posciel", "szafa": "lak_szafa", "regal": "drewno",
           "dywan": "dywan:1:1", "czarny_lak": "czarny_metal", "kamien_mebel": "kamien_kominek", "tynk_mebel": "tynk",
           "brąz": "braz", "szklo_mebel": "szklo", "donica": "terakota", "auto": "plastik_szary"}
    for p in it.parts:
        key = MAP.get(p[-1], "plastik_szary")
        if p[0] == "box":
            _, x, y, z, w, d, h, _m = p
            mb.box(x - w / 2, -y - d / 2, z, x + w / 2, -y + d / 2, z + h, key, r=0.006)
        elif p[0] == "cyl":
            _, x, y, z, rr, h, _m = p
            mb.cyl(x, -y, z, z + h, rr, key, n=32, r=0.006)
        elif p[0] == "sph":
            _, x, y, z, rr, _m = p
            mb.sphere(x, -y, z, rr, key, n=20)
    B.mesh(mb, it.kind or "mebel")


BUILDERS = {
    "sofa": _sofa, "fotel": _fotel, "stolik": _stolik, "dywan": _dywan, "rtv": _rtv, "kominek": _kominek,
    "stol": _stol, "lozko": _lozko, "szafa": _szafa, "regal": _regal, "blat": _blat, "wyspa": _wyspa,
    "biurko": _biurko, "biurko2": _biurko, "wanna": _wanna, "prysznic": _prysznic, "wc": _wc, "umywalki": _umywalki,
    "pralka": _pralka, "zbiornik": _zbiornik, "pompa": _pompa, "fortepian": _fortepian, "sztaluga": _sztaluga,
    "warsztat": _warsztat, "czajnik": _czajnik, "tokonoma": _tokonoma, "lezak": _lezak, "lawka": _lawka,
    "lawa": _lawa, "piec": _piec, "mata": _mata, "wino": _wino, "cokol": _cokol, "donica": _donica, "auto": _auto,
    "stolek": _stolek, "rower": _rower, "ekran": _ekran,
}


def build_items(items, ctx):
    """Buduje meble 3D dla elementów silnik.meble.Item (z cx, cy, rot, z, room); zwraca obiekty bpy."""
    out = []
    for i, it in enumerate(items):
        fn = BUILDERS.get(it.kind, _ogolny)
        B = _B(it, ctx, i)
        try:
            fn(B)
        except Exception as e:   # mebel nigdy nie blokuje sceny: zastępczo proste bryły
            if DEBUG:
                raise
            for ob in B.obs[1:]:
                bpy.data.objects.remove(ob, do_unlink=True)
            B.obs = B.obs[:1]
            ctx.cache.setdefault("m3d_bledy", []).append(f"{it.kind}: {e}")
            try:
                _ogolny(B)
            except Exception:
                pass
        out.extend(B.obs)
    return out


def tri_count(obs):
    """Liczba trójkątów (po modyfikatorach) w podanych obiektach – do testów i budżetu sceny."""
    dg = bpy.context.evaluated_depsgraph_get()
    n = 0
    for ob in obs:
        if ob.type != "MESH":
            continue
        me = ob.evaluated_get(dg).data
        me.calc_loop_triangles()
        n += len(me.loop_triangles)
    return n
