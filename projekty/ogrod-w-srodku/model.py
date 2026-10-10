"""Opis brył 3D przekazywany do przeglądarki (three.js) jako JSON."""


class Model:
    def __init__(self, center, radius):
        self.d = {"center": list(center), "radius": radius, "items": []}

    def add(self, **kw):
        self.d["items"].append(kw)

    def prism(self, pts, z0, z1, m="wall", holes=None):
        self.add(t="prism", pts=[list(p) for p in pts], z0=z0, z1=z1, m=m, holes=holes or [])

    def box(self, x1, y1, z1, x2, y2, z2, m="wall"):
        self.prism([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], z1, z2, m)

    def poly(self, pts3, m="roof"):
        self.add(t="poly", pts=[list(p) for p in pts3], m=m)

    def panel(self, a, b, z0, z1, m="glass", d=0.06):
        self.add(t="panel", a=list(a), b=list(b), z0=z0, z1=z1, m=m, d=d)

    def flat(self, pts, z, m):
        self.add(t="flat", pts=[list(p) for p in pts], z=z, m=m)

    def tree(self, x, y, h, r, kind="round"):
        self.add(t="tree", x=x, y=y, h=h, r=r, kind=kind)

    def stone(self, x, y, r, h=None):
        self.add(t="stone", x=x, y=y, r=r, h=h or r * 0.6)

    def chain(self, x, y, z0, z1):
        self.add(t="chain", x=x, y=y, z0=z0, z1=z1)

    def person(self, x, y, z=0):
        self.add(t="person", x=x, y=y, z=z)

    def toro(self, x, y):
        self.add(t="toro", x=x, y=y)

    def bamboo(self, x, y, n=9, r=0.4):
        self.add(t="bamboo", x=x, y=y, n=n, r=r)

    def stained(self, pts3, design="rect"):
        self.add(t="stained", pts=[list(p) for p in pts3], design=design)

    def lantern(self, cx, cy, a, z0, z1, z2):
        self.add(t="lantern", cx=cx, cy=cy, a=a, z0=z0, z1=z1, z2=z2)

    def moonwall(self, a, b, z0, z1, th, hu, hz, hr, m="wall"):
        """Ściana z okrągłym otworem: hu – położenie środka wzdłuż ściany, hz – wysokość, hr – promień."""
        self.add(t="moonwall", a=list(a), b=list(b), z0=z0, z1=z1, th=th, hu=hu, hz=hz, hr=hr, m=m)

    def fascia(self, pts_top, z_base, m="wall"):
        """Pionowe pasy między płaską koroną ścian (z_base) a krawędzią dachu (pts_top z wysokościami)."""
        for (x1, y1, z1), (x2, y2, z2) in zip(pts_top, pts_top[1:]):
            q = [(x1, y1, z_base), (x2, y2, z_base)]
            if z2 > z_base + 1e-3:
                q.append((x2, y2, z2))
            if z1 > z_base + 1e-3:
                q.append((x1, y1, z1))
            if len(q) >= 3:
                self.poly(q, m)
