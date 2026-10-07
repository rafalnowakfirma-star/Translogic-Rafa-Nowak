"""Sprawdza kolizje części silnika V8 dla wielu kątów wału.

Używa tych samych macierzy położeń co podgląd złożenia (czesc="pozycje"),
więc sprawdza dokładnie to, co widać w animacji.
użycie: python3 kolizje.py <silnik_v8.scad> <katalog_stl_lokalnych> kat1 kat2 ...
wymaga: pip install trimesh manifold3d numpy
"""
import sys, os, tempfile, subprocess, itertools, numpy as np, trimesh, manifold3d as m3d

scad, lok = sys.argv[1], sys.argv[2]
katy = [float(a) for a in sys.argv[3:]]
POMIN = {"L_sprezyna"}
# pary dozwolonego wcisku (zamierzony pasowany montaż)
DOZW = {frozenset(["L_talerzyk", "L_zawor"])}

ECHO = os.path.join(tempfile.mkdtemp(), "poz.echo")
cache = {}
def czesc(id):
    if id not in cache:
        t = trimesh.load(f"{lok}/{id}.stl")
        cache[id] = m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(t.vertices, np.float32),
                                          tri_verts=np.asarray(t.faces, np.uint32)))
    return cache[id]

def pozycje(kat):
    subprocess.run(["openscad", "-D", "pokaz_pokrywy=true", "-D", 'czesc="pozycje"', "-D", f"kat={kat}", "-o", ECHO, scad],
                   capture_output=True, text=True)
    out = open(ECHO).read()
    res = []
    for l in out.splitlines():
        if "POZ|" not in l: continue
        _, nazwa, id, mat = l.strip().strip('"').split("|")
        M = np.array(eval(mat))
        res.append((nazwa, id, M))
    return res

def bbox(man):
    b = man.bounding_box()
    return np.array(b[:3]), np.array(b[3:])

for kat in katy:
    poz = [p for p in pozycje(kat) if p[1] not in POMIN]
    obj = []
    for nazwa, id, M in poz:
        man = czesc(id).transform(M[:3, :4].tolist())
        obj.append((nazwa, id, man, bbox(man)))
    kolizje = []
    for (n1, i1, m1, b1), (n2, i2, m2, b2) in itertools.combinations(obj, 2):
        if frozenset([i1, i2]) in DOZW: continue
        if np.any(b1[1] < b2[0]) or np.any(b2[1] < b1[0]): continue
        v = (m1 ^ m2).volume()
        if v > 0.2:
            kolizje.append((round(v, 2), n1, n2))
    kolizje.sort(reverse=True)
    print(f"kat {kat:6.1f}: {len(kolizje)} kolizji", kolizje[:12], flush=True)
