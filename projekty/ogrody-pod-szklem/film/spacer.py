"""Widoki z panoram spaceru: wycinek equirectangular (lon, lat w stopniach) → zwykłe zdjęcie perspektywiczne.

yaw > 0 – obrót w prawo, pitch > 0 – w górę, hfov – poziomy kąt widzenia kadru.
"""
import math

import numpy as np
from PIL import Image


def widok(pano, lon, lat, yaw=0.0, pitch=0.0, hfov=78.0, W=1600, H=900):
    """pano: ścieżka albo PIL.Image; zwraca PIL.Image W×H."""
    im = pano if isinstance(pano, Image.Image) else Image.open(pano).convert("RGB")
    src = np.asarray(im, dtype=np.float32)
    h_e, w_e = src.shape[:2]
    f = (W / 2) / math.tan(math.radians(hfov) / 2)
    xs = (np.arange(W) - (W - 1) / 2) / f
    ys = ((H - 1) / 2 - np.arange(H)) / f
    X, Y = np.meshgrid(xs, ys)
    Z = np.ones_like(X)
    # obrót: pitch wokół osi poziomej, potem yaw wokół pionowej
    p, y_ = math.radians(pitch), math.radians(yaw)
    Y2 = Y * math.cos(p) + Z * math.sin(p)
    Z2 = -Y * math.sin(p) + Z * math.cos(p)
    X3 = X * math.cos(y_) + Z2 * math.sin(y_)
    Z3 = -X * math.sin(y_) + Z2 * math.cos(y_)
    lo = np.degrees(np.arctan2(X3, Z3))
    la = np.degrees(np.arctan2(Y2, np.sqrt(X3 ** 2 + Z3 ** 2)))
    u = (lo - lon[0]) / (lon[1] - lon[0]) * (w_e - 1)
    v = (lat[1] - la) / (lat[1] - lat[0]) * (h_e - 1)
    u = np.clip(u, 0, w_e - 1.001)
    v = np.clip(v, 0, h_e - 1.001)
    u0 = np.floor(u).astype(np.int32)
    v0 = np.floor(v).astype(np.int32)
    du = (u - u0)[..., None]
    dv = (v - v0)[..., None]
    a = src[v0, u0] * (1 - du) + src[v0, u0 + 1] * du
    b = src[v0 + 1, u0] * (1 - du) + src[v0 + 1, u0 + 1] * du
    out = a * (1 - dv) + b * dv
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8))


def kadr_stacji(st, out_dir, W=1600, H=900, t=0.5):
    """Zdjęcie ze stacji spaceru (stan ruchu w chwili t ∈ [0, 1])."""
    import os
    r0, r1 = st["ruch"]
    yaw = r0[0] + (r1[0] - r0[0]) * t
    pitch = r0[1] + (r1[1] - r0[1]) * t
    hfov = r0[2] + (r1[2] - r0[2]) * t
    return widok(os.path.join(out_dir, st["obraz"]), st["lon"], st["lat"], yaw, pitch, hfov, W, H)
