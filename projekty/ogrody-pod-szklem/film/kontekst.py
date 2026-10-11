"""Wspólny kontekst sceny filmowej: przeliczanie współrzędnych planu na Blendera i ustawienia ujęcia.

Plan: x – wschód, y – południe, z – w górę, obrót elementu `rot` w stopniach (jak w silnik/meble.py).
Blender: X = x - ox, Y = -(y - oy), Z = z.  Element o obrocie `rot` ma w Blenderze rotation_euler.z = -radians(rot),
a w lokalnym układzie Blendera jego plecy (y = -d/2 w planie) leżą po stronie +Y, front po stronie -Y.
"""
import math
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZASOBY = os.path.join(HERE, "zasoby")


class Ctx:
    def __init__(self, ox=0.0, oy=0.0, col=None, seed=0, dusk=False, season="lato", house=None):
        self.ox, self.oy = ox, oy
        self.col = col            # kolekcja bpy, do której trafiają nowe obiekty
        self.seed = seed          # różnorodność między domami (kolory tkanin, gatunki)
        self.dusk = dusk          # wieczór: lampy świecą
        self.season = season      # "lato" | "zima" (zima: drzewa liściaste bez liści, śnieg na zewnątrz)
        self.house = house
        self.cache = {}           # zaimportowane modele, materiały, warianty drzew

    def to_bl(self, x, y, z=0.0):
        return (x - self.ox, -(y - self.oy), z)

    def rot_bl(self, rot_deg):
        return -math.radians(rot_deg)

    def link(self, ob):
        (self.col or __import__("bpy").context.scene.collection).objects.link(ob)
        return ob


def zasob(rel):
    """Ścieżka do pobranego zasobu (python3 film/zasoby.py)."""
    return os.path.join(ZASOBY, rel)
