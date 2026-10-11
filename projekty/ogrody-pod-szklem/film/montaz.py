#!/usr/bin/env python3
"""Montaż filmu prezentacyjnego jednego domu: storyboard JSON → MP4 1920×1080, 25 kl/s (+ wersja web).

  python3 film/montaz.py storyboard.json [--podglad] [--bez-web] [--klatki 2,9.5,31]
  from film.montaz import montuj;  montuj(storyboard_dict, katalog=None) -> ścieżka MP4

Klatki liczone w Pythonie (numpy/PIL, kilka wątków), surowe RGB24 idą rurą równolegle do dwóch
koderów ffmpeg: główny (libx264 High, slow, CRF 19) i web (CRF z limitem VBV wyliczonym z długości,
tak by plik ≤ 14 MB na minutę razem z dźwiękiem).  Muzyka: film/muzyka.py (osobny proces).

Pola storyboardu (ścieżki względne liczone od katalogu pliku JSON):
  pid, wersja, numer, nazwa, tagline, seria, fakty [[wartość, opis], ...], napisy_koncowe [...],
  muzyka (true | false | ścieżka do gotowego pliku audio), wyjscie (MP4), ujecia [...],
  opcjonalnie: web (true/false), web_mb_na_minute (14), muzyka_seed (int), muzyka_glosnosc (dB, 0).
Ujęcia (wspólne: czas [s], przejscie: "przenikanie" | "ciecie" | "krok" | liczba sekund przenikania,
        lektor: {"plik": "lektor/03.wav", "start": 0.5} – klip od początku ujęcia (początku przenikania) + start;
        ujęcie wydłuża się do start + długość + 0,7 s, animacja stoi wtedy na ostatniej klatce):
  tytul    – tlo (obraz, opcjonalnie), czas
  animacja – klatki ("anim/%04d.png" lub wzorzec glob), fps (25), fps_render (np. 12.5 → minterpolate),
             podpis, podpis2
  kadr     – obraz, czas, ruch (zoom_in | zoom_out | pan_lewo | pan_prawo | pan_gora | pan_dol | statyczny),
             fokus [x, y] (0..1), zoom (siła, domyślnie 1.10; pan 1.08; statyczny 1.025), podpis, podpis2
  rzut     – obraz, czas, podpis, podpis2, zoom (≤ 1.04)
  panorama – obraz (wycinek równoprostokątny), lon [l0, l1], lat [b0, b1], ruch [[yaw, pitch, hfov], [...]],
             czas, podpis, podpis2; przejscie "krok" między dwiema panoramami = krok naprzód
  zalety_wady – tlo, zalety [...], wady [...] (2–5 punktów), czas
  koniec   – tlo, czas
"""
import argparse
import fractions
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import threading
import time
import zlib
from collections import deque
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

try:                                    # opcjonalnie: szybkie remapowanie panoram
    import cv2
    cv2.setNumThreads(2)
except ImportError:
    cv2 = None
try:
    from . import muzyka
except ImportError:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import muzyka

TU = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.dirname(TU)
FONTY = os.path.join(PROJ, "zasoby", "fonty")
FFMPEG = shutil.which("ffmpeg") or "/usr/bin/ffmpeg"
FFPROBE = shutil.which("ffprobe") or "/usr/bin/ffprobe"

FPS = 25
PRZENIKANIE = 1.0           # s
WEJSCIE_Z_CZERNI = 1.4      # s
WYJSCIE_W_CZERN = 1.6       # s
LIMIT_POWIEKSZENIA = 1.15   # maks. powiększenie względem natywnej rozdzielczości źródła
WEB_MB_NA_MINUTE = 14.0
KROK = 1.1                  # s, przejście „krok” między panoramami
LEKTOR_ZAPAS = 0.7          # s ciszy po klipie lektora do końca ujęcia
SR_AUDIO = 48000

TEKST = (244, 241, 234)     # #f4f1ea
MOSIADZ = (201, 169, 110)   # #c9a96e
ZIELEN = (127, 163, 122)    # #7fa37a
PAPIER = (243, 240, 232)    # #f3f0e8
GRAFIT = (38, 37, 33)
CIEN = (8, 8, 7)

MI_FILTR = "minterpolate=fps={fps}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1:scd=none"
WERSJA_CACHE = 1


# ---------------------------------------------------------------- drobne narzędzia

def ease_io(u):
    """Sinusoidalne wejście-wyjście 0→1."""
    u = min(max(u, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * u)


def ease_out(u):
    u = min(max(u, 0.0), 1.0)
    return 1.0 - (1.0 - u) ** 3


def smooth(a, b, x):
    """smoothstep na tablicach numpy."""
    u = np.clip((x - a) / (b - a), 0.0, 1.0)
    return u * u * (3 - 2 * u)


def dither_u8(arr):
    """float (0..255) → uint8 z ditherem TPDF (bez pasm w gładkich, ciemnych gradientach)."""
    rng = np.random.default_rng(7)
    n = rng.random(arr.shape, np.float32) - rng.random(arr.shape, np.float32)
    return np.clip(arr + n + 0.5, 0, 255).astype(np.uint8)


def miks(a, b, alfa):
    """Przenikanie a→b (alfa 0..1) w arytmetyce całkowitej."""
    q = int(round(alfa * 256))
    if q <= 0:
        return a
    if q >= 256:
        return b
    o = a.astype(np.uint16)
    o *= 256 - q
    o += b.astype(np.uint16) * np.uint16(q)
    o += 128
    o >>= 8
    return o.astype(np.uint8)


def przyciemnij(kl, f):
    q = int(round(f * 256))
    if q >= 256:
        return kl
    o = kl.astype(np.uint16)
    o *= q
    o += 128
    o >>= 8
    return o.astype(np.uint8)


def sciezka(p, katalog):
    p = os.path.expanduser(p)
    return p if os.path.isabs(p) else os.path.normpath(os.path.join(katalog, p))


def wczytaj_rgb(p):
    im = Image.open(p)
    im.load()
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        tlo = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(tlo, im)
    return im.convert("RGB")


def okno(box, W, H):
    """Prostokąt źródła przycięty do obrazu W×H (błędy zaokrągleń dają np. x0 = −1e−13, czego PIL nie przyjmuje)."""
    x0, y0, x1, y1 = box
    x0, y0 = min(max(0.0, x0), W - 1.0), min(max(0.0, y0), H - 1.0)
    return x0, y0, min(max(x0 + 1.0, x1), float(W)), min(max(y0 + 1.0, y1), float(H))


def kadruj_pokrycie(im, w, h, filtr=Image.LANCZOS):
    """Skalowanie z przycięciem do środka (pokrycie całego kadru w×h)."""
    s = max(w / im.width, h / im.height)
    bw, bh = w / s, h / s
    x0, y0 = (im.width - bw) / 2, (im.height - bh) / 2
    return im.resize((w, h), filtr, box=okno((x0, y0, x0 + bw, y0 + bh), im.width, im.height))


def wczytaj_audio(p, kanaly=1, sr=SR_AUDIO):
    """Dowolny plik audio → float32 (kanały × próbki) 48 kHz (ffmpeg, resampler soxr)."""
    r = subprocess.run([FFMPEG, "-v", "error", "-nostdin", "-i", p, "-vn", "-ac", str(kanaly),
                        "-af", "aresample=%d:resampler=soxr" % sr, "-f", "f32le", "-"], capture_output=True)
    if r.returncode:
        raise RuntimeError("audio %s: %s" % (p, r.stderr.decode(errors="replace")[-500:]))
    return np.frombuffer(r.stdout, np.float32).reshape(-1, kanaly).T.copy()


# ---------------------------------------------------------------- typografia

class Typo:
    """Fonty (z instancjami osi zmiennych) w skali kadru: rozmiary podawane dla 1080p."""

    def __init__(self, skala):
        self.s = skala
        self._c = {}

    def font(self, plik, px, wght=None, wdth=None):
        px = max(6, int(round(px * self.s)))
        k = (plik, px, wght, wdth)
        f = self._c.get(k)
        if f is None:
            f = ImageFont.truetype(os.path.join(FONTY, plik), px, layout_engine=ImageFont.Layout.RAQM)
            try:
                osie = [a["name"] for a in f.get_variation_axes()]
            except OSError:
                osie = []
            if osie:                      # Archivo: [Weight, Width], Hanken: [Weight]
                wart = {b"Weight": wght or 400, b"Width": wdth or 100}
                f.set_variation_by_axes([wart.get(n, 100) for n in osie])
            self._c[k] = f
        return f


class Napis:
    """Maska tekstu (float32 0..1) i położenie początku linii bazowej (bx, by) w masce."""

    def __init__(self, tekst, font, tracking=0.0):
        pad = self.pad = 3
        self.tekst = tekst
        if not tracking:
            x0, y0, x1, y1 = font.getbbox(tekst, anchor="ls")
            w, h = int(math.ceil(x1 - x0)) + 2 * pad, int(math.ceil(y1 - y0)) + 2 * pad
            im = Image.new("L", (max(w, 1), max(h, 1)), 0)
            ImageDraw.Draw(im).text((pad - x0, pad - y0), tekst, font=font, fill=255, anchor="ls")
            self.bx, self.by = pad - x0, pad - y0
            self.szer = font.getlength(tekst)
        else:                              # rozstrzelenie: znak po znaku
            poz, x = [], 0.0
            for ch in tekst:
                poz.append(x)
                x += font.getlength(ch) + tracking
            self.szer = x - tracking
            bb = [font.getbbox(ch, anchor="ls") for ch in tekst]
            x0 = min(p + b[0] for p, b in zip(poz, bb))
            x1 = max(p + b[2] for p, b in zip(poz, bb))
            y0 = min(b[1] for b in bb)
            y1 = max(b[3] for b in bb)
            w, h = int(math.ceil(x1 - x0)) + 2 * pad, int(math.ceil(y1 - y0)) + 2 * pad
            im = Image.new("L", (max(w, 1), max(h, 1)), 0)
            d = ImageDraw.Draw(im)
            for p, ch in zip(poz, tekst):
                d.text((pad - x0 + p, pad - y0), ch, font=font, fill=255, anchor="ls")
            self.bx, self.by = pad - x0, pad - y0
        self.im = im
        self.m = np.asarray(im, np.float32) / 255.0


def dopasuj_font(typo, plik, px, tekst, szer, **osie):
    """Font o stopniu ≤ px, w którym tekst mieści się w szerokości `szer` (px kadru)."""
    f = typo.font(plik, px, **osie)
    while tekst and px > 12 and f.getlength(tekst) > szer:
        px *= 0.94
        f = typo.font(plik, px, **osie)
    return f


def zawijaj(tekst, font, szer):
    """Łamanie wierszy; jednoliterowe wyrazy i liczby z jednostkami nie zostają na końcu linii."""
    sl = tekst.split()
    grupy, i = [], 0
    while i < len(sl):
        g = [sl[i]]
        while i + 1 < len(sl) and (
            len(g[-1]) == 1                                         # „w ogrodzie”, „×”
            or (g[-1].replace(",", "").isdigit() and len(sl[i + 1]) <= 3)   # „13 ×”, „14 m”
        ):
            i += 1
            g.append(sl[i])
        if sl[i + 1:i + 2] and sl[i + 1] in ("–", "—", "-"):        # myślnik zostaje na końcu linii
            i += 1
            g.append(sl[i])
        grupy.append(" ".join(g))
        i += 1
    linie, akt = [], ""
    for g in grupy:
        kand = (akt + " " + g).strip()
        if akt and font.getlength(kand) > szer:
            linie.append(akt)
            akt = g
        else:
            akt = kand
    if akt:
        linie.append(akt)
    return linie


# ---------------------------------------------------------------- warstwy tekstu i kształtów

def naloz(kl, m, kolor, x, y, a):
    """Nakłada maskę m (float32) w kolorze na klatkę uint8; y może być ułamkowe (ruch sub-pikselowy)."""
    if a <= 0.002:
        return
    h, w = m.shape
    iy = int(math.floor(y))
    fy = y - iy
    if fy > 0.004:
        mm = np.zeros((h + 1, w), np.float32)
        mm[:h] = m * (1.0 - fy)
        mm[1:] += m * fy
        m, h = mm, h + 1
    x = int(round(x))
    H, W = kl.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(iy, 0), min(x + w, W), min(iy + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    mm = m[y0 - iy:y1 - iy, x0 - x:x1 - x]
    if a < 0.999:
        mm = mm * np.float32(a)
    reg = kl[y0:y1, x0:x1].astype(np.float32)
    reg += (np.asarray(kolor, np.float32) - reg) * mm[..., None]
    reg += 0.5
    kl[y0:y1, x0:x1] = reg.astype(np.uint8)


class Element:
    """Tekst lub kreska: pojawia się (krycie + wysunięcie w górę) od t_in, znika od t_out."""

    def __init__(self, maska, kolor, x, y, t_in=0.0, dl_in=0.8, t_out=None, dl_out=0.6,
                 wysuw=0.0, krycie=1.0, cien=None, rosnie=False):
        self.m, self.kolor = maska, kolor
        self.x, self.y = x, y
        self.t_in, self.dl_in, self.t_out, self.dl_out = t_in, dl_in, t_out, dl_out
        self.wysuw, self.krycie, self.rosnie = wysuw, krycie, rosnie
        self.cien = cien            # (maska, dx, dy, krycie)

    @classmethod
    def z_napisu(cls, napis, kolor, x, y_bazy, **kw):
        """x – lewa krawędź liter (wyrównanie optyczne, niezależne od stopnia pisma), y_bazy – linia bazowa."""
        return cls(napis.m, kolor, x - napis.pad, y_bazy - napis.by, **kw)

    def dodaj_cien(self, promien, dy, krycie):
        r = max(1, int(round(promien)))
        pad = 3 * r
        im = Image.fromarray((self.m * 255).astype(np.uint8))
        big = Image.new("L", (im.width + 2 * pad, im.height + 2 * pad), 0)
        big.paste(im, (pad, pad))
        big = big.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(r))
        self.cien = (np.asarray(big, np.float32) / 255.0, -pad, dy - pad, krycie)
        return self

    def postep(self, t):
        a = (t - self.t_in) / self.dl_in if self.dl_in > 0 else (1.0 if t >= self.t_in else 0.0)
        return min(max(a, 0.0), 1.0)

    def alfa(self, t):
        a = ease_out(self.postep(t))
        if self.t_out is not None and t > self.t_out:
            a *= 1.0 - ease_io((t - self.t_out) / self.dl_out)
        return a * self.krycie

    def rysuj(self, kl, t):
        a = self.alfa(t)
        if a <= 0.002:
            return
        p = ease_out(self.postep(t))
        y = self.y + self.wysuw * (1.0 - p)
        m = self.m
        if self.rosnie:                      # kreska wysuwa się od lewej
            w = int(round(m.shape[1] * p))
            if w <= 0:
                return
            m = m[:, :w]
        if self.cien is not None:
            cm, dx, dy, ck = self.cien
            naloz(kl, cm, CIEN, self.x + dx, y + dy, a * ck)
        naloz(kl, m, self.kolor, self.x, y, a)


def kreska(w, h):
    return np.ones((max(1, int(round(h))), max(1, int(round(w)))), np.float32)


class Pasek:
    """Łagodne przyciemnienie dołu kadru pod podpisem (mocniejsze z lewej)."""

    def __init__(self, W, H, moc=0.6):
        self.y0 = int(H * 0.45)
        yy = np.arange(self.y0, H, dtype=np.float32)
        xx = np.arange(W, dtype=np.float32)
        fy = smooth(self.y0, H * 1.02, yy) ** 0.85
        fx = 1.0 - 0.55 * smooth(0.0, W * 0.95, xx)
        self.a = (moc * fy[:, None] * fx[None, :]).astype(np.float32)

    def rysuj(self, kl, op):
        if op <= 0.002:
            return
        k = (self.a * np.float32(op * 256.0)).astype(np.uint16)
        reg = kl[self.y0:].astype(np.uint16)
        reg *= (256 - k)[..., None]
        reg += 128
        reg >>= 8
        kl[self.y0:] = reg.astype(np.uint8)


class Podpis:
    """Podpis ujęcia: kreska akcentu, tytuł (Archivo, ≤ 2 wiersze) i opcjonalny podtytuł (Hanken, łamany).

    ciagly / ciagly2 = (wejście, wyjście): tytuł / podtytuł widoczny bez zanikania na styku z sąsiednim
    ujęciem o tym samym podpisie (panoramy); linie2_min – wspólna liczba wierszy podtytułu w takim łańcuchu."""

    @staticmethod
    def linie(ctx, tekst, tekst2, ciemny=False):
        """Łamanie tytułu i podtytułu: (linie1, px1, linie2, px2)."""
        s = ctx.s
        szer1 = ((ctx.kolumna_rzutu + 60) if ciemny else 1560) * s
        szer2 = (ctx.kolumna_rzutu if ciemny else 1150) * s
        px1 = 46                                     # tytuł: ≤ 2 wiersze (min. 34 px)
        while True:
            f1 = ctx.typo.font("Archivo.ttf", px1, wght=600, wdth=106)
            linie1 = zawijaj(tekst, f1, szer1)
            if len(linie1) <= 2 or px1 <= 34:
                break
            px1 -= 2
        px2, maks2, linie2 = 30, (4 if ciemny else 2), []   # podtytuł bez obcinania tekstu (min. 24 px)
        while tekst2:
            f2 = ctx.typo.font("HankenGrotesk.ttf", px2, wght=400 if ciemny else 380)
            linie2 = zawijaj(tekst2, f2, szer2)
            if len(linie2) <= maks2 or px2 <= 24:
                break
            px2 -= 2
        if len(linie2) > maks2:
            print("  [podpis] uwaga: podtytuł „%s…” zajmuje %d wierszy" % (tekst2[:30], len(linie2)))
        return linie1, px1, linie2, px2

    def __init__(self, ctx, tekst, tekst2, t_in, t_out, ciemny=False, ciagly=(False, False),
                 ciagly2=(False, False), linie2_min=0):
        s = ctx.s
        self.elementy = []
        self.pasek = None if ciemny else ctx.pasek()
        self.t_in, self.t_out, self.ciagly = t_in, t_out, ciagly
        if not tekst:
            self.pasek = None
            self.ramka = (0, 0, 0, 0)
            return
        kol = GRAFIT if ciemny else TEKST
        akc = ZIELEN if ciemny else MOSIADZ
        linie1, px1, linie2, px2 = self.linie(ctx, tekst, tekst2, ciemny)
        f1 = ctx.typo.font("Archivo.ttf", px1, wght=600, wdth=106)
        f2 = ctx.typo.font("HankenGrotesk.ttf", px2, wght=400 if ciemny else 380)
        n1 = [Napis(ln, f1) for ln in linie1]
        n2 = [Napis(ln, f2) for ln in linie2]
        n2u = max(len(n2), linie2_min)               # wiersze przyjęte do układu
        lh1, lh2 = px1 * 1.16 * s, px2 * 1.37 * s
        x = ctx.margines_x
        if ciemny:                                   # u góry po lewej (rzuty)
            y1 = 168 * s
            y2 = y1 + lh1 * (len(n1) - 1) + (20 + px2) * s
        else:                                        # na dole po lewej, tekst rośnie w górę
            dol = ctx.H - 112 * s
            y2 = dol - lh2 * max(0, n2u - 1)
            y1 = (y2 - (20 + px2) * s if n2u else dol) - lh1 * (len(n1) - 1)
        yk = y1 - px1 * s * 0.74 - 24 * s
        wys = 16 * s
        ZAWSZE = -1e3
        t1, k1 = (ZAWSZE if ciagly[0] else t_in), (None if ciagly[1] else t_out)
        t2, k2 = (ZAWSZE if ciagly2[0] else t_in + 0.24), (None if ciagly2[1] else t_out)
        self.elementy.append(Element(kreska(44 * s, 3 * s), akc, x, yk, t_in=t1, dl_in=0.7, rosnie=True,
                                     t_out=k1, dl_out=0.6))
        prawa = x
        for i, n in enumerate(n1):
            e = Element.z_napisu(n, kol, x, y1 + i * lh1, t_in=t1 + 0.08 + 0.05 * i, dl_in=0.8, wysuw=wys,
                                 t_out=k1, dl_out=0.6)
            if not ciemny:
                e.dodaj_cien(7 * s, 2 * s, 0.45)
            self.elementy.append(e)
            prawa = max(prawa, x + n.szer)
        for i, n in enumerate(n2):
            e = Element.z_napisu(n, kol, x, y2 + i * lh2, t_in=t2 + 0.06 * i, dl_in=0.8, wysuw=wys,
                                 krycie=0.86 if not ciemny else 0.78, t_out=k2, dl_out=0.6)
            if not ciemny:
                e.dodaj_cien(6 * s, 2 * s, 0.45)
            self.elementy.append(e)
            prawa = max(prawa, x + n.szer)
        dol = (y2 + lh2 * max(0, len(n2) - 1)) if n2 else (y1 + lh1 * (len(n1) - 1))
        self.ramka = (x, yk - 6 * s, prawa, dol + 10 * s)   # obszar podpisu

    def rysuj(self, kl, t):
        if self.pasek is not None:
            op = 1.0 if self.ciagly[0] else ease_io((t - (self.t_in - 0.35)) / 1.0)
            if t > self.t_out and not self.ciagly[1]:
                op *= 1.0 - ease_io((t - self.t_out) / 0.9)
            self.pasek.rysuj(kl, op)
        for e in self.elementy:
            e.rysuj(kl, t)


# ---------------------------------------------------------------- tło rozmyte (tytuł, koniec)

def tlo_rozmyte(p, W, H, zmax, jasnosc=0.42, lewa=0.55, dol=0.25):
    """Rozmyty, przyciemniony i stonowany obraz (lub ciemny gradient) w rozmiarze kadru × zmax."""
    Wb, Hb = int(math.ceil(W * zmax)), int(math.ceil(H * zmax))
    if p and os.path.exists(p):
        im = wczytaj_rgb(p)
        male = kadruj_pokrycie(im, max(8, Wb // 4), max(8, Hb // 4))
        male = male.filter(ImageFilter.GaussianBlur(max(1.0, Wb / 260.0)))
        a = np.asarray(male.resize((Wb, Hb), Image.BICUBIC), np.float32)
        lum = a @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        a = lum[..., None] + (a - lum[..., None]) * 0.72              # stonowanie barw
        a *= jasnosc
    else:
        a = np.zeros((Hb, Wb, 3), np.float32) + np.array([30, 29, 26], np.float32)
    xx = np.linspace(0, 1, Wb, dtype=np.float32)[None, :]
    yy = np.linspace(0, 1, Hb, dtype=np.float32)[:, None]
    g = (1.0 - lewa * (1.0 - smooth(0.0, 0.8, xx))) * (1.0 - dol * smooth(0.45, 1.0, yy))
    r2 = ((xx - 0.5) / 0.72) ** 2 + ((yy - 0.5) / 0.72) ** 2
    g = g * (1.0 - 0.38 * np.clip(r2, 0, 1.6) / 1.6)                  # winieta
    a *= g[..., None]
    a *= np.array([1.0, 0.975, 0.93], np.float32)                     # ciepłe cienie
    a += np.array([5.0, 4.6, 4.0], np.float32)                        # czerń nie całkiem czarna
    return Image.fromarray(dither_u8(a))


# ---------------------------------------------------------------- ujęcia

class Ujecie:
    rodzaj = "?"

    def __init__(self, u, ctx):
        self.u, self.ctx = u, ctx
        self.o_in = self.o_out = 0          # długość przenikania (klatki) na wejściu / wyjściu
        self.start = 0
        self.L = max(2, int(float(u.get("czas", 5.0)) * FPS + 0.5))
        self.krok_in = self.krok_out = False    # przejście „krok” (panoramy)
        self.lektor = None                      # (start s, próbki mono 48 kHz, ścieżka)
        self.opcje_podpisu = {}                 # ciągłość podpisu między panoramami

    def czasy_podpisu(self):
        """Podpis pojawia się po ustaleniu obrazu i znika przed przenikaniem do następnego ujęcia."""
        t_in = max(0.6, self.o_in / FPS * 0.5 + 0.4)
        t_kon = self.L / FPS - max(0.6, self.o_out / FPS * 0.5 + 0.4)
        return t_in, t_kon - 0.6

    def przygotuj(self):
        pass

    def rozgrzej(self):
        pass

    def zwolnij(self):
        pass

    def klatka(self, k):
        raise NotImplementedError


class UjecieKadr(Ujecie):
    """Nieruchomy obraz z płynnym ruchem kamery (Ken Burns), próbkowanie sub-pikselowe z pełnej rozdzielczości."""
    rodzaj = "kadr"

    def przygotuj(self):
        c, u = self.ctx, self.u
        W, H = c.W, c.H
        p = sciezka(u["obraz"], c.katalog)
        im = wczytaj_rgb(p)
        iw, ih = im.size
        s0 = max(W / iw, H / ih)                       # px kadru na px źródła przy pokryciu
        ruch = u.get("ruch", "zoom_in")
        domyslny = {"statyczny": 1.025, "pan_lewo": 1.08, "pan_prawo": 1.08, "pan_gora": 1.10, "pan_dol": 1.10}
        z = float(u.get("zoom", domyslny.get(ruch, 1.10)))
        # limit powiększenia względem natywnej rozdzielczości (w 1080p; podgląd liczy się jak pełna wersja)
        s0_pelne = s0 / c.s
        z_lim = max(1.0, LIMIT_POWIEKSZENIA / s0_pelne)
        if z > z_lim:
            z_new = max(z_lim, min(z, 1.025))
            print("  [kadr] %s: źródło %d×%d za małe na zoom %.3f – ograniczam do %.3f"
                  % (os.path.basename(p), iw, ih, z, z_new))
            z = z_new
        self.zmax = max(z, 1.0)
        # zmniejszenie roboczego obrazu, gdy źródło jest dużo większe niż potrzeba (szybkość)
        potrzeba = s0 * self.zmax
        if potrzeba < 0.62:
            f = potrzeba / 0.8
            im = im.resize((max(1, round(iw * f)), max(1, round(ih * f))), Image.LANCZOS)
            iw, ih = im.size
            s0 = max(W / iw, H / ih)
        im.load()
        self.im, self.iw, self.ih, self.s0 = im, iw, ih, s0
        self.ruch = ruch
        fx, fy = u.get("fokus", [0.5, 0.5])
        self.P = (fx * iw, fy * ih)
        t_in, t_out = self.czasy_podpisu()
        self.podpis = (Podpis(c, u.get("podpis"), u.get("podpis2"), t_in, t_out, **self.opcje_podpisu)
                       if u.get("podpis") else None)

    def _okno(self, e):
        """Środek okna (px źródła) i powiększenie dla postępu ruchu e ∈ [0,1]."""
        iw, ih, s0 = self.iw, self.ih, self.s0
        W, H = self.ctx.W, self.ctx.H

        def wym(z):
            return W / (s0 * z), H / (s0 * z)

        def przytnij(cx, cy, z):
            ww, wh = wym(z)
            return min(max(cx, ww / 2), iw - ww / 2), min(max(cy, wh / 2), ih - wh / 2)

        r, zm = self.ruch, self.zmax
        if r in ("zoom_in", "zoom_out", "statyczny"):
            z = 1.0 + (zm - 1.0) * (e if r != "zoom_out" else 1.0 - e)
            c1 = przytnij(iw / 2, ih / 2, 1.0)
            ww, wh = wym(1.0)
            # biegun przybliżenia w obrębie okna startowego – okno zawsze mieści się w obrazie
            px = min(max(self.P[0], c1[0] - ww / 2), c1[0] + ww / 2)
            py = min(max(self.P[1], c1[1] - wh / 2), c1[1] + wh / 2)
            return px + (c1[0] - px) / z, py + (c1[1] - py) / z, z
        z = zm
        ww, wh = wym(z)
        maks = 0.10 * W / (s0 * z)                     # przesuw ≤ 10% szerokości kadru
        def zakres(lo, hi, p):                       # przesuw ≤ maks, wokół fokusu
            if hi - lo > maks:
                c = min(max(p, lo + maks / 2), hi - maks / 2)
                lo, hi = c - maks / 2, c + maks / 2
            return lo, hi

        if r in ("pan_lewo", "pan_prawo"):           # pan_lewo: kamera jedzie w lewo (obraz płynie w prawo)
            lo, hi = zakres(ww / 2, iw - ww / 2, self.P[0])
            cx = hi - (hi - lo) * e if r == "pan_lewo" else lo + (hi - lo) * e
            return przytnij(cx, self.P[1], z) + (z,)
        lo, hi = zakres(wh / 2, ih - wh / 2, self.P[1])   # pan_gora / pan_dol
        cy = hi - (hi - lo) * e if r == "pan_gora" else lo + (hi - lo) * e
        return przytnij(self.P[0], cy, z) + (z,)

    def okno_box(self, k):
        e = ease_io(k / max(1, self.L - 1))
        cx, cy, z = self._okno(e)
        ww, wh = self.ctx.W / (self.s0 * z), self.ctx.H / (self.s0 * z)
        x0 = min(max(cx - ww / 2, 0.0), self.iw - ww)
        y0 = min(max(cy - wh / 2, 0.0), self.ih - wh)
        return (max(0.0, x0), max(0.0, y0), min(float(self.iw), x0 + ww), min(float(self.ih), y0 + wh))

    def klatka(self, k):
        c = self.ctx
        kl = np.array(self.im.resize((c.W, c.H), c.filtr, box=okno(self.okno_box(k), self.im.width, self.im.height)))
        if self.podpis:
            self.podpis.rysuj(kl, k / FPS)
        return kl


class Strumien:
    """Klatki RGB24 z procesu ffmpeg czytane w tle; klatka(k) czeka na k-tą klatkę."""

    def __init__(self, cmd, W, H, zapas=12):
        self.cmd, self.W, self.H = cmd, W, H
        self.fs = W * H * 3
        self.buf = {}
        self.cv = threading.Condition()
        self.nast = 0
        self.koniec = False
        self.stop = False
        self.ostatnia = None
        self.zapas = zapas
        self.p = None
        self.min_k = 0              # klatki o mniejszych numerach nie będą już potrzebne

    def start(self):
        with self.cv:
            if self.p is not None:
                return
            self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        threading.Thread(target=self._czytaj, daemon=True).start()
        threading.Thread(target=self._stderr, daemon=True).start()

    def _stderr(self):
        self.log = self.p.stderr.read()

    def _czytaj(self):
        while True:
            with self.cv:
                while len(self.buf) >= self.zapas and not self.stop:
                    self.cv.wait()
                if self.stop:
                    return
            b = bytearray(self.fs)
            mv = memoryview(b)
            got = 0
            while got < self.fs:
                r = self.p.stdout.readinto(mv[got:])
                if not r:
                    break
                got += r
            with self.cv:
                if got < self.fs:
                    self.koniec = True
                    self.cv.notify_all()
                    return
                if self.nast >= self.min_k:
                    self.buf[self.nast] = b
                self.ostatnia = b
                self.nast += 1
                self.cv.notify_all()

    def klatka(self, k):
        if self.p is None:
            self.start()
        with self.cv:
            if k >= self.nast + self.zapas:          # duży skok (tryb --klatki): pomiń klatki po drodze
                self.min_k = max(self.min_k, k - self.zapas // 2)
            while k >= self.nast and not self.koniec:
                self.cv.wait()
            b = self.buf.pop(k, None)
            for j in [j for j in self.buf if j < self.min_k or j < k - 2 * self.zapas]:   # pominięte – zwolnij
                del self.buf[j]
            self.cv.notify_all()
            if b is None:
                if self.ostatnia is None:
                    raise RuntimeError("brak klatek z ffmpeg: %s" % " ".join(self.cmd[:12]))
                b = bytearray(self.ostatnia)
            elif b is self.ostatnia:
                b = bytearray(b)
        return np.frombuffer(b, np.uint8).reshape(self.H, self.W, 3)

    def zamknij(self):
        with self.cv:
            self.stop = True
            self.buf.clear()
            self.cv.notify_all()
        if self.p is not None and self.p.poll() is None:
            self.p.kill()
            self.p.wait()


def lista_klatek(wzorzec, katalog):
    """Pliki sekwencji: wzorzec printf (%04d) – kolejne numery od pierwszego istniejącego – albo glob."""
    w = sciezka(wzorzec, katalog)
    if "%" in w:
        start = next((i for i in range(0, 10) if os.path.exists(w % i)), None)
        if start is None:
            raise FileNotFoundError("brak klatek: " + w)
        pliki, i = [], start
        while os.path.exists(w % i):
            pliki.append(w % i)
            i += 1
        return pliki, w, start
    import glob
    pliki = sorted(glob.glob(w))
    if not pliki:
        raise FileNotFoundError("brak klatek: " + w)
    return pliki, None, 0


class UjecieAnimacja(Ujecie):
    """Sekwencja klatek renderu; przy fps_render < 25 – interpolacja ruchu (minterpolate, wynik w pamięci podręcznej)."""
    rodzaj = "animacja"

    def __init__(self, u, ctx):
        super().__init__(u, ctx)
        self.pliki, self.wzorzec, self.nr0 = lista_klatek(u["klatki"], ctx.katalog)
        self.fps_zr = float(u.get("fps_render") or u.get("fps") or FPS)
        self.r = fractions.Fraction(FPS / self.fps_zr).limit_denominator(100)
        n = len(self.pliki)
        self.L = max(2, int(math.floor((n - 1) * self.r)) + 1 if self.r != 1 else n)
        self.strumien = None
        self._zamek = threading.Lock()

    def _skala(self, wej=""):
        """Skalowanie (lanczos) z przycięciem do środka; konwersja do RGB w tym samym filtrze."""
        W, H = self.ctx.W, self.ctx.H
        return ("scale=w=%d:h=%d:force_original_aspect_ratio=increase:flags=lanczos+accurate_rnd+full_chroma_int%s,"
                "format=rgb24,crop=%d:%d" % (W, H, wej, W, H))

    def _wejscie_obrazow(self, od=0, do=None):
        """Argumenty wejścia ffmpeg dla klatek [od, do] sekwencji."""
        do = len(self.pliki) - 1 if do is None else do
        if self.wzorzec:
            return ["-framerate", "%g" % self.fps_zr, "-start_number", str(self.nr0 + od), "-i", self.wzorzec]
        lst = os.path.join(self.ctx.cache, "lista_%08x_%d_%d.txt" % (zlib.crc32("|".join(self.pliki).encode()), od, do))
        with open(lst, "w") as f:
            f.write("ffconcat version 1.0\n")
            for p in self.pliki[od:do + 1]:
                f.write("file '%s'\nduration %.6f\n" % (p.replace("'", "'\\''"), 1.0 / self.fps_zr))
        return ["-f", "concat", "-safe", "0", "-i", lst]

    def _klucz(self):
        h = hashlib.sha1()
        for p in self.pliki:
            st = os.stat(p)
            h.update(("%s|%d|%d;" % (os.path.realpath(p), st.st_size, st.st_mtime_ns)).encode())
        h.update(("%s|%s|%s|%d" % (self.fps_zr, FPS, MI_FILTR, WERSJA_CACHE)).encode())
        return h.hexdigest()[:16]

    def interpoluj(self):
        """Interpolacja do 25 kl/s równolegle w kawałkach (z zakładkami), wynik FFV1 w pamięci podręcznej."""
        if self.r == 1:
            return None
        kat = os.path.join(self.ctx.cache, "anim_" + self._klucz())
        meta = os.path.join(kat, "gotowe.json")
        if os.path.exists(meta):
            return meta
        os.makedirs(kat, exist_ok=True)
        n = len(self.pliki)
        den = self.r.denominator
        P = max(1, min(os.cpu_count() or 2, 4, n // 12))
        granice = sorted(set([0] + [int(round(n * i / P / den)) * den for i in range(1, P)] + [n - 1]))
        t0 = time.time()
        procesy = []
        for i in range(len(granice) - 1):
            a, b = granice[i], granice[i + 1]
            ostatni = i == len(granice) - 2
            s = max(0, a - 2 * den)
            e = min(n - 1, b + 2 * den)
            pomin = int((a - s) * self.r)
            ile = int((b - a) * self.r) + (1 if ostatni else 0)
            vf = ("trim=end_frame=%d,setpts=PTS-STARTPTS,%s"
                  "scale=out_color_matrix=bt709:out_range=full,format=yuv444p,%s,"
                  "trim=start_frame=%d:end_frame=%d,setpts=N/(%d*TB)"
                  % (e - s + 1, "tpad=stop_mode=clone:stop=%d," % (4 * den) if ostatni else "",
                     MI_FILTR.format(fps=FPS), pomin, pomin + ile, FPS))
            wyj = os.path.join(kat, "kawalek_%02d.mkv" % i)
            cmd = [FFMPEG, "-v", "error", "-y", "-nostdin"] + self._wejscie_obrazow(s, e) + [
                "-vf", vf, "-fps_mode", "passthrough", "-c:v", "ffv1", "-level", "3", "-g", "1",
                "-slices", "4", wyj]
            procesy.append((subprocess.Popen(cmd, stderr=subprocess.PIPE), wyj, ile))
        for p, wyj, ile in procesy:
            _, err = p.communicate()
            if p.returncode:
                raise RuntimeError("minterpolate: " + err.decode(errors="replace")[-2000:])
        with open(os.path.join(kat, "lista.txt"), "w") as f:
            f.write("ffconcat version 1.0\n")
            for _, wyj, _ in procesy:
                f.write("file '%s'\n" % os.path.basename(wyj))
        with open(meta + ".tmp", "w") as f:
            json.dump({"klatki": self.L, "zrodlo": n, "kawalki": len(procesy)}, f)
        os.replace(meta + ".tmp", meta)
        print("  [animacja] interpolacja %d → %d klatek (%d procesy): %.1f s"
              % (n, self.L, len(procesy), time.time() - t0))
        return meta

    def przygotuj(self):
        c = self.ctx
        meta = None
        if self.r != 1:
            kat = os.path.join(c.cache, "anim_" + self._klucz())
            meta = os.path.join(kat, "gotowe.json")
            if not os.path.exists(meta) and not c.podglad:
                meta = self.interpoluj()
        if meta and os.path.exists(meta):
            lst = os.path.join(os.path.dirname(meta), "lista.txt")
            wej = ["-f", "concat", "-safe", "0", "-i", lst]
            vf = self._skala(":in_color_matrix=bt709:in_range=full")
        elif self.r != 1:                                  # podgląd bez gotowej interpolacji: powielanie klatek
            wej = self._wejscie_obrazow()
            vf = "fps=%d," % FPS + self._skala()
        else:
            wej = self._wejscie_obrazow()
            vf = self._skala()
        self.cmd = [FFMPEG, "-v", "error", "-nostdin"] + wej + [
            "-vf", vf, "-fps_mode", "passthrough", "-frames:v", str(self.L),
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        t_in, t_out = self.czasy_podpisu()
        self.podpis = (Podpis(c, self.u.get("podpis"), self.u.get("podpis2"), t_in, t_out, **self.opcje_podpisu)
                       if self.u.get("podpis") else None)

    def rozgrzej(self):
        with self._zamek:
            if self.strumien is None:
                self.strumien = Strumien(self.cmd, self.ctx.W, self.ctx.H)
                self.strumien.start()
            return self.strumien

    def klatka(self, k):
        kl = (self.strumien or self.rozgrzej()).klatka(k)
        if self.podpis:
            self.podpis.rysuj(kl, k / FPS)
        return kl

    def zwolnij(self):
        with self._zamek:
            if self.strumien is not None:
                self.strumien.zamknij()
                self.strumien = None


class UjecieRzut(Ujecie):
    """Rzut na papierowym tle (mnożenie: biel rysunku = kolor papieru), bardzo wolne przybliżenie.

    Układ nie zależy od długości podpisu: kolumna podpisu po lewej, rzut w polu po prawej – kolejne
    rzuty tego samego formatu (np. parter → piętro z cięciem) leżą dokładnie w tym samym miejscu."""
    rodzaj = "rzut"

    @staticmethod
    def ramka_tresci(im):
        a = np.asarray(im)
        tresc = np.argwhere(a.min(axis=2) < 246)            # przycięcie białych marginesów
        if not len(tresc):
            return (0, 0, im.width, im.height)
        (y0, x0), (y1, x1) = tresc.min(0), tresc.max(0) + 1
        return (int(x0), int(y0), int(x1), int(y1))

    def przygotuj(self):
        c, u = self.ctx, self.u
        W, H, s = c.W, c.H, c.s
        im = wczytaj_rgb(sciezka(u["obraz"], c.katalog))
        x0, y0, x1, y1 = c.ramki_rzutow.get(im.size) or self.ramka_tresci(im)
        pad = int(0.012 * max(im.size))
        im = im.crop((max(0, x0 - pad), max(0, y0 - pad), min(im.width, x1 + pad), min(im.height, y1 + pad)))
        t_in, t_out = self.czasy_podpisu()
        self.podpis = Podpis(c, u.get("podpis"), u.get("podpis2"), t_in, t_out, ciemny=True)
        self.zr = min(1.04, max(1.0, float(u.get("zoom", 1.035))))
        pw, ph = im.size
        T, B, R = 80 * s, H - 80 * s, W - c.margines_x

        def dopasuj(l, t, r, b):
            sc = min((r - l) / pw, (b - t) / ph) / self.zr
            w, h = pw * sc, ph * sc
            return sc, (l + r - w) / 2, (t + b - h) / 2, w, h

        # pole na prawo od kolumny podpisu albo (dla bardzo szerokich rzutów) pod podpisem
        L = c.margines_x + (c.kolumna_rzutu + 70) * s
        kand = [dopasuj(L, T, R, B)]
        if self.podpis.ramka[3] > 0:
            kand.append(dopasuj(c.margines_x, self.podpis.ramka[3] + 50 * s, R, B))
        sc, x, y, w, h = max(kand, key=lambda k: k[0] * (1.0 if k is kand[0] else 0.9))
        # arkusz w rozdzielczości maks. przybliżenia
        Ws, Hs = int(math.ceil(W * self.zr)), int(math.ceil(H * self.zr))
        xx = np.linspace(-1, 1, Ws, dtype=np.float32)[None, :]
        yy = np.linspace(-1, 1, Hs, dtype=np.float32)[:, None]
        win = 1.0 - 0.045 * (xx ** 2 + yy ** 2) / 2
        arkusz = np.array(PAPIER, np.float32)[None, None, :] * win[..., None]
        rw, rh = max(1, int(round(w * self.zr))), max(1, int(round(h * self.zr)))
        rx, ry = int(round(x * self.zr)), int(round(y * self.zr))
        plan = np.asarray(im.resize((rw, rh), Image.LANCZOS), np.float32) / 255.0
        arkusz[ry:ry + rh, rx:rx + rw] *= plan
        self.arkusz = Image.fromarray(dither_u8(arkusz))
        self.arkusz.load()
        self.Ws, self.Hs = Ws, Hs
        self.biegun = (rx + rw / 2, ry + rh / 2)

    def klatka(self, k):
        c = self.ctx
        z = 1.0 + (self.zr - 1.0) * ease_io(k / max(1, self.L - 1))
        ww, wh = self.Ws / z, self.Hs / z
        px, py = self.biegun
        x0 = min(max(px - px / z, 0.0), self.Ws - ww)
        y0 = min(max(py - py / z, 0.0), self.Hs - wh)
        kl = np.array(self.arkusz.resize((c.W, c.H), c.filtr,
                                         box=okno((x0, y0, x0 + ww, y0 + wh), self.arkusz.width, self.arkusz.height)))
        self.podpis.rysuj(kl, k / FPS)
        return kl


class UjecieTlo(Ujecie):
    """Wspólne dla tytułu i końca: rozmyte tło z wolnym przybliżeniem i warstwy tekstu."""
    ZMAX = 1.06

    def tlo(self, **kw):
        c = self.ctx
        p = sciezka(self.u["tlo"], c.katalog) if self.u.get("tlo") else None
        self.bg = tlo_rozmyte(p, c.W, c.H, self.ZMAX, **kw)
        self.bg.load()
        self.elementy = []

    def klatka(self, k):
        c = self.ctx
        z = 1.0 + (self.ZMAX - 1.0) * ease_io(k / max(1, self.L - 1))
        bw, bh = self.bg.size
        ww, wh = bw / z, bh / z
        x0, y0 = (bw - ww) / 2, (bh - wh) / 2
        kl = np.array(self.bg.resize((c.W, c.H), Image.BILINEAR, box=okno((x0, y0, x0 + ww, y0 + wh), bw, bh)))
        t = k / FPS
        for e in self.elementy:
            e.rysuj(kl, t)
        return kl


class UjecieTytul(UjecieTlo):
    rodzaj = "tytul"

    def przygotuj(self):
        c, sb, s = self.ctx, self.ctx.sb, self.ctx.s
        self.tlo(jasnosc=0.56, lewa=0.55, dol=0.3)
        x = c.margines_x
        typo = c.typo
        f_seria = typo.font("IBMPlexMono-Regular.ttf", 23)
        f_nr = typo.font("Archivo.ttf", 66, wght=300, wdth=125)
        f_nazwa = dopasuj_font(typo, "Archivo.ttf", 172, sb.get("nazwa", ""), 1560 * s, wght=640, wdth=112)
        rozm = 40
        f_tag = typo.font("HankenGrotesk.ttf", rozm, wght=340)
        tag = sb.get("tagline", "")
        linie = zawijaj(tag, f_tag, 1060 * s) if tag else []
        while len(linie) > 3 and rozm > 26:                       # tagline ≤ 3 wiersze
            rozm -= 2
            f_tag = typo.font("HankenGrotesk.ttf", rozm, wght=340)
            linie = zawijaj(tag, f_tag, 1060 * s)
        lh = rozm * 1.42 * s
        # układ od dołu, odstępy z metryk pisma (akcenty Ż, ogonki ą)
        gora_naz = -f_nazwa.getbbox("ŻÓŚĆK", anchor="ls")[1]
        dol_naz = f_nazwa.getbbox("gąjpy", anchor="ls")[3]
        gora_tag = -f_tag.getbbox("KŻ", anchor="ls")[1]
        gora_nr = -f_nr.getbbox("P0", anchor="ls")[1]
        y_tag = c.H - 156 * s - lh * (len(linie) - 1)
        y_kr = y_tag - gora_tag - 40 * s
        y_naz = y_kr - dol_naz - 30 * s
        y_nr = y_naz - gora_naz - 44 * s
        y_ser = y_nr - gora_nr - 38 * s
        # tekst gaśnie w pierwszej części przenikania do kolejnego ujęcia
        t_out = (self.L - self.o_out) / FPS - 0.05
        kw = dict(t_out=t_out, dl_out=max(0.4, 0.6 * self.o_out / FPS))
        el = self.elementy
        t0 = 0.35
        if sb.get("seria"):
            n = Napis(sb["seria"].upper(), f_seria, tracking=0.22 * 23 * s)
            el.append(Element.z_napisu(n, MOSIADZ, x, y_ser, t_in=t0, dl_in=0.9, wysuw=12 * s, **kw))
        if sb.get("numer"):
            n = Napis(sb["numer"], f_nr, tracking=0.06 * 66 * s)
            el.append(Element.z_napisu(n, TEKST, x, y_nr, t_in=t0 + 0.15, dl_in=1.0, wysuw=16 * s, krycie=0.8, **kw))
        el.append(Element.z_napisu(Napis(sb.get("nazwa", ""), f_nazwa), TEKST, x, y_naz, t_in=t0 + 0.3, dl_in=1.1,
                                   wysuw=22 * s, **kw).dodaj_cien(14 * s, 3 * s, 0.35))
        el.append(Element(kreska(84 * s, 3 * s), MOSIADZ, x, y_kr, t_in=t0 + 0.6, dl_in=0.9, rosnie=True, **kw))
        for i, ln in enumerate(linie):
            el.append(Element.z_napisu(Napis(ln, f_tag), TEKST, x, y_tag + i * lh, t_in=t0 + 0.7 + 0.1 * i,
                                       dl_in=1.0, wysuw=12 * s, krycie=0.9, **kw))


class UjecieKoniec(UjecieTlo):
    rodzaj = "koniec"

    def przygotuj(self):
        c, sb, s = self.ctx, self.ctx.sb, self.ctx.s
        self.tlo(jasnosc=0.36, lewa=0.35, dol=0.3)
        x, W, H = c.margines_x, c.W, c.H
        typo = c.typo
        el = self.elementy
        t0 = self.o_in / FPS * 0.4 + 0.1
        # linia serii + nazwa
        ser = " · ".join(v for v in (sb.get("numer"), sb.get("seria")) if v)
        nrz = 0 if not sb.get("fakty") else (1 if len(sb["fakty"]) <= 4 else 2)
        wys_bloku = (140 + (104 + 152 + 36) + 230 * max(0, nrz - 1)) * s if nrz else 140 * s
        y = max(150 * s, (H - 150 * s - wys_bloku) / 2 + 20 * s)
        if ser:
            n = Napis(ser.upper(), typo.font("IBMPlexMono-Regular.ttf", 22), tracking=0.22 * 22 * s)
            el.append(Element.z_napisu(n, MOSIADZ, x, y, t_in=t0, dl_in=0.8, wysuw=10 * s))
        f_naz = dopasuj_font(typo, "Archivo.ttf", 116, sb.get("nazwa", ""), 1560 * s, wght=620, wdth=112)
        y_naz = y + 140 * s
        el.append(Element.z_napisu(Napis(sb.get("nazwa", ""), f_naz), TEKST, x, y_naz, t_in=t0 + 0.12,
                                   dl_in=0.9, wysuw=16 * s).dodaj_cien(12 * s, 3 * s, 0.3))
        # fakty: siatka (≤ 4 kolumny), duża wartość + mały opis
        fakty = sb.get("fakty", [])
        if fakty:
            nk = len(fakty) if len(fakty) <= 4 else (3 if len(fakty) in (5, 6) else 4)
            szer = (W - 2 * x) / nk
            f_w = typo.font("Archivo.ttf", 84, wght=560, wdth=104)
            f_o = typo.font("HankenGrotesk.ttf", 28, wght=400)
            y_r = y_naz + 104 * s
            for i, (wart, opis) in enumerate(fakty):
                kol, rz = i % nk, i // nk
                xc = x + kol * szer
                yr = y_r + rz * 230 * s
                ti = t0 + 0.3 + 0.08 * i
                el.append(Element(kreska(szer - 48 * s, max(1.0, 1.5 * s)), TEKST, xc, yr, t_in=ti, dl_in=0.9,
                                  rosnie=True, krycie=0.32))
                el.append(Element.z_napisu(Napis(str(wart), f_w), TEKST, xc, yr + 104 * s, t_in=ti + 0.08,
                                           dl_in=0.9, wysuw=14 * s))
                for j, ln in enumerate(zawijaj(str(opis), f_o, szer - 56 * s)[:2]):
                    el.append(Element.z_napisu(Napis(ln, f_o), TEKST, xc, yr + (152 + 36 * j) * s, t_in=ti + 0.16,
                                               dl_in=0.9, wysuw=10 * s, krycie=0.74))
        # napisy końcowe – małe, u dołu
        f_n = typo.font("HankenGrotesk.ttf", 24, wght=400)
        linie = []
        for t in sb.get("napisy_koncowe", []):
            linie += zawijaj(t, f_n, W - 2 * x)
        lh = 36 * s
        y0 = H - 100 * s - lh * (len(linie) - 1)
        for i, ln in enumerate(linie):
            el.append(Element.z_napisu(Napis(ln, f_n), TEKST, x, y0 + i * lh, t_in=t0 + 0.7 + 0.08 * i, dl_in=0.9,
                                       wysuw=8 * s, krycie=0.62))


class UjeciePanorama(Ujecie):
    """Stanowisko spaceru: prostoliniowy widok perspektywiczny z wycinka panoramy równoprostokątnej.

    x obrazu: lon[0] (lewa krawędź) → lon[1] (prawa), y: lat[1] (góra) → lat[0] (dół), stopnie.
    Kamera: yaw 0 = lon 0, yaw > 0 – obrót w prawo; pitch > 0 – w górę; hfov – poziome pole widzenia kadru 16:9.
    Mapowanie odwrotne: piksel → promień → (lon, lat) → próbka (cv2.remap bicubic, bez OpenCV: PIL MESH)."""
    rodzaj = "panorama"

    def przygotuj(self):
        c, u = self.ctx, self.u
        im = wczytaj_rgb(sciezka(u["obraz"], c.katalog))
        self.Wp, self.Hp = im.size
        self.lon = [float(v) for v in u.get("lon", [-180, 180])]
        self.lat = [float(v) for v in u.get("lat", [-90, 90])]
        r = [[float(v) for v in q] for q in (u.get("ruch") or [[0, 0, 80]])]
        self.ruch = (r[0], r[-1])
        if cv2 is not None:
            self.arr = np.ascontiguousarray(np.asarray(im))
        else:
            im.load()
            self.im = im
        self._sprawdz_zasieg()
        t_in, t_out = self.czasy_podpisu()
        self.podpis = (Podpis(c, u.get("podpis"), u.get("podpis2"), t_in, t_out, **self.opcje_podpisu)
                       if u.get("podpis") else None)

    def kamera(self, k):
        """(yaw, pitch, hfov) w klatce k; przy przejściu „krok” – zwężanie / rozszerzanie pola widzenia."""
        (y0, p0, h0), (y1, p1, h1) = self.ruch
        a = self.o_in if self.krok_in else 0
        b = self.L - self.o_out if self.krok_out else self.L
        if k < a:                                   # wejście: pole widzenia 0,8 → 1,0 (zatrzymanie po kroku)
            return y0, p0, h0 * (0.8 + 0.2 * ease_out((k + 0.5) / a))
        if k >= b:                                  # wyjście: ostatni kierunek, pole widzenia −25% (krok naprzód)
            return y1, p1, h1 * (1.0 - 0.25 * ease_io((k - b + 0.5) / self.o_out))
        e = ease_io((k - a) / max(1, b - a - 1))
        return y0 + (y1 - y0) * e, p0 + (p1 - p0) * e, h0 + (h1 - h0) * e

    def _mapa(self, xs, ys, yaw, pitch, hfov):
        """Piksele kadru (xs, ys) → współrzędne pikseli panoramy (px, py)."""
        W, H = self.ctx.W, self.ctx.H
        f = (W / 2) / math.tan(math.radians(hfov) / 2)
        x = (xs + 0.5 - W / 2) / f
        y = -(ys + 0.5 - H / 2) / f
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        cq, sq = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        y2 = y * cp + sp                             # pochylenie (oś x)
        z2 = cp - y * sp
        x3 = x * cq + z2 * sq                        # odchylenie (oś y), w prawo = rosnąca długość
        z3 = z2 * cq - x * sq
        lon = np.degrees(np.arctan2(x3, z3))
        lat = np.degrees(np.arctan2(y2, np.hypot(x3, z3)))
        if self.lon[1] - self.lon[0] >= 359.9:       # pełne 360°: zawinięcie
            lon = (lon - self.lon[0]) % 360.0 + self.lon[0]
        px = (lon - self.lon[0]) / (self.lon[1] - self.lon[0]) * self.Wp - 0.5
        py = (self.lat[1] - lat) / (self.lat[1] - self.lat[0]) * self.Hp - 0.5
        return px.astype(np.float32), py.astype(np.float32)

    def _sprawdz_zasieg(self):
        W, H = self.ctx.W, self.ctx.H
        bx = np.concatenate([np.arange(0, W, 32), np.full(H // 32, W - 1), np.arange(0, W, 32), np.zeros(H // 32)])
        by = np.concatenate([np.zeros(W // 32), np.arange(0, H, 32), np.full(W // 32, H - 1), np.arange(0, H, 32)])
        bx, by = bx[:min(len(bx), len(by))].astype(np.float64), by[:min(len(bx), len(by))].astype(np.float64)
        poza = 0.0
        for k in sorted(set([0, self.L // 2, self.L - 1, max(0, self.o_in - 1)])):
            px, py = self._mapa(bx, by, *self.kamera(k))
            poza = max(poza, -0.5 - px.min(), px.max() - (self.Wp - 0.5), -0.5 - py.min(), py.max() - (self.Hp - 0.5))
        if poza > 1.0:
            print("  [panorama] %s: kadr wychodzi poza zakres panoramy o ~%.0f px (brzeg powielony)"
                  % (os.path.basename(self.u["obraz"]), poza))

    def widok(self, yaw, pitch, hfov):
        c = self.ctx
        W, H = c.W, c.H
        if cv2 is not None:                          # mapy na rzadkiej siatce (co 4 px) + dokładne powiększenie
            xs, ys = c.siatka_panoramy()
            px, py = self._mapa(xs, ys, yaw, pitch, hfov)
            px = cv2.resize(px, (W + 8, H + 8), interpolation=cv2.INTER_LINEAR)[4:4 + H, 4:4 + W]
            py = cv2.resize(py, (W + 8, H + 8), interpolation=cv2.INTER_LINEAR)[4:4 + H, 4:4 + W]
            return cv2.remap(self.arr, px, py, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        gx, gy = c.siatka_mesh()                     # bez OpenCV: siatka 16 px, odwzorowanie w węzłach
        GX, GY = np.meshgrid(gx, gy)
        px, py = self._mapa(GX - 0.5, GY - 0.5, yaw, pitch, hfov)
        px, py = px + 0.5, py + 0.5
        mesh = [((int(gx[i]), int(gy[j]), int(gx[i + 1]), int(gy[j + 1])),
                 (px[j, i], py[j, i], px[j + 1, i], py[j + 1, i], px[j + 1, i + 1], py[j + 1, i + 1],
                  px[j, i + 1], py[j, i + 1]))
                for j in range(len(gy) - 1) for i in range(len(gx) - 1)]
        return np.array(self.im.transform((W, H), Image.MESH, mesh, resample=Image.BICUBIC))

    def klatka(self, k):
        kl = self.widok(*self.kamera(k))
        if not kl.flags.writeable:
            kl = kl.copy()
        if self.podpis:
            self.podpis.rysuj(kl, k / FPS)
        return kl


class UjecieZaletyWady(UjecieTlo):
    """Plansza „Zalety / Minusy”: dwie kolumny punktów pojawiających się kolejno w pierwszych ~70% ujęcia."""
    rodzaj = "zalety_wady"

    def przygotuj(self):
        c, sb, s, u = self.ctx, self.ctx.sb, self.ctx.s, self.u
        self.tlo(jasnosc=0.34, lewa=0.25, dol=0.25)
        W, H, x0 = c.W, c.H, c.margines_x
        typo = c.typo
        el = self.elementy
        listy = [[str(v) for v in u.get("zalety", [])], [str(v) for v in u.get("wady", [])]]
        for lst, nazwa in zip(listy, ("zalety", "wady")):
            if not 2 <= len(lst) <= 5:
                print("  [zalety_wady] uwaga: %d punktów w „%s” (zalecane 2–5)" % (len(lst), nazwa))
        przerwa = 96 * s
        kol_w = (W - 2 * x0 - przerwa) / 2
        xs = [x0, x0 + kol_w + przerwa]
        wciecie = 50 * s
        px = 38                                      # punkty: każdy ≤ 2 wiersze (38 → 30 px)
        while True:
            f = typo.font("HankenGrotesk.ttf", px, wght=400)
            linie = [[zawijaj(t, f, kol_w - wciecie - 10 * s) for t in lst] for lst in listy]
            if all(len(l) <= 2 for lst in linie for l in lst) or px <= 30:
                break
            px -= 2
        lh, odst = px * 1.3 * s, px * 0.7 * s
        f_t = typo.font("Archivo.ttf", 64, wght=600, wdth=106)
        f_z = typo.font("Archivo.ttf", px * 1.1, wght=500, wdth=100)
        cap_t = -f_t.getbbox("ZM", anchor="ls")[1]
        cap_p = -f.getbbox("Hk", anchor="ls")[1]

        def wys(lst):
            return sum(len(l) * lh for l in lst) + odst * max(0, len(lst) - 1)

        h_blok = cap_t + 34 * s + 3 * s + 42 * s + cap_p + max(wys(linie[0]), wys(linie[1])) - lh
        y_t = max(250 * s, (H - 60 * s - h_blok) / 2 + cap_t)          # linia bazowa tytułów kolumn
        y_kr = y_t + 30 * s
        y_p0 = y_kr + 3 * s + 42 * s + cap_p
        # czasy: tytuły na początku, punkty kolejno do ~70% ujęcia (najpierw zalety, potem minusy)
        t0 = self.o_in / FPS * 0.4 + 0.1
        n = sum(len(l) for l in listy)
        t_a, t_b = t0 + 0.7, max(t0 + 0.8, 0.7 * self.L / FPS)
        chwile = [t_a + (t_b - t_a) * i / max(1, n - 1) for i in range(n)]
        ser = " · ".join(v for v in (sb.get("numer"), sb.get("nazwa")) if v)
        if ser:
            el.append(Element.z_napisu(Napis(ser.upper(), typo.font("IBMPlexMono-Regular.ttf", 22), tracking=0.22 * 22 * s),
                                       MOSIADZ, x0, y_t - cap_t - 52 * s, t_in=t0, dl_in=0.8, wysuw=10 * s))
        el.append(Element(kreska(max(1.0, 1.5 * s), y_p0 + wys(max(linie, key=wys)) - y_t + cap_t),
                          TEKST, xs[1] - przerwa / 2, y_t - cap_t, t_in=t0 + 0.2, dl_in=1.0, krycie=0.18))
        i = 0
        for kol, (lst, tytul, akc, znak) in enumerate(zip(linie, ("Zalety", "Minusy"), (ZIELEN, MOSIADZ), ("+", "–"))):
            x = xs[kol]
            tt = t0 + 0.1 if kol == 0 else max(t0 + 0.1, (chwile[i] if i < n else t_b) - 0.4)
            el.append(Element.z_napisu(Napis(tytul, f_t), TEKST, x, y_t, t_in=tt, dl_in=0.9, wysuw=14 * s)
                      .dodaj_cien(10 * s, 3 * s, 0.3))
            el.append(Element(kreska(64 * s, 3 * s), akc, x, y_kr, t_in=tt + 0.15, dl_in=0.8, rosnie=True))
            y = y_p0
            for wiersze in lst:
                ti = chwile[i]
                el.append(Element.z_napisu(Napis(znak, f_z), akc, x, y, t_in=ti, dl_in=0.7, wysuw=12 * s))
                for j, ln in enumerate(wiersze):
                    el.append(Element.z_napisu(Napis(ln, f), TEKST, x + wciecie, y + j * lh, t_in=ti + 0.04 * j,
                                               dl_in=0.8, wysuw=12 * s, krycie=0.92).dodaj_cien(6 * s, 2 * s, 0.3))
                y += len(wiersze) * lh + odst
                i += 1


RODZAJE = {"tytul": UjecieTytul, "animacja": UjecieAnimacja, "kadr": UjecieKadr, "rzut": UjecieRzut,
           "panorama": UjeciePanorama, "zalety_wady": UjecieZaletyWady, "koniec": UjecieKoniec}


# ---------------------------------------------------------------- montaż

class Montaz:
    def __init__(self, sb, katalog, podglad=False, watki=3):
        self.sb, self.katalog, self.podglad = sb, os.path.abspath(katalog), podglad
        self.W, self.H = (960, 540) if podglad else (1920, 1080)
        self.s = self.W / 1920.0
        self.margines_x = 150 * self.s          # 7,8% – wewnątrz obszaru bezpiecznego (90%)
        self.kolumna_rzutu = 540                # szerokość kolumny podpisu rzutu (px przy 1080p)
        self.typo = Typo(self.s)
        self.filtr = Image.BICUBIC if podglad else Image.LANCZOS
        self.watki = watki
        wyj = sb.get("wyjscie") or "%s_film.mp4" % sb.get("pid", "film")
        self.wyjscie = sciezka(wyj, katalog)
        if podglad:
            r, e = os.path.splitext(self.wyjscie)
            self.wyjscie = r + "_podglad" + e
        self.cache = os.path.join(os.path.dirname(self.wyjscie), "_montaz_cache")
        os.makedirs(self.cache, exist_ok=True)
        self._pasek = None
        self.ujecia = []
        for u in sb["ujecia"]:
            if u.get("typ") not in RODZAJE:
                raise ValueError("nieznany typ ujęcia: %r" % u.get("typ"))
            self.ujecia.append(RODZAJE[u["typ"]](u, self))
        for uj in self.ujecia:                  # lektor: ujęcie trwa co najmniej start + klip + 0,7 s
            lek = uj.u.get("lektor")
            if lek:
                p = sciezka(lek["plik"], self.katalog)
                x = wczytaj_audio(p)[0]
                st = float(lek.get("start", 0.0))
                uj.lektor = (st, x, p)
                potrzeba = int(math.ceil((st + len(x) / SR_AUDIO + LEKTOR_ZAPAS) * FPS))
                if uj.L < potrzeba:
                    print("  [lektor] %s (%.2f s): ujęcie %s wydłużone %.2f → %.2f s"
                          % (os.path.basename(p), len(x) / SR_AUDIO, uj.rodzaj, uj.L / FPS, potrzeba / FPS))
                    uj.L = potrzeba
        self._siatki = {}
        self.os_czasu()
        self.ciaglosc_podpisow()

    def pasek(self):
        if self._pasek is None:
            self._pasek = Pasek(self.W, self.H)
        return self._pasek

    def os_czasu(self):
        for _ in range(len(self.ujecia) + 1):
            for i, uj in enumerate(self.ujecia):
                uj.krok_in = uj.krok_out = False
                if i:
                    pop = self.ujecia[i - 1]
                    p = uj.u.get("przejscie", "przenikanie")
                    krok = p == "krok" and pop.rodzaj == uj.rodzaj == "panorama"
                    if p in ("ciecie", "cięcie", "cut"):
                        o = 0
                    elif krok:
                        o = int(round(KROK * FPS))
                    elif isinstance(p, (int, float)):
                        o = int(round(float(p) * FPS))
                    else:                                  # przenikanie (także „krok” poza parą panoram)
                        o = int(round(PRZENIKANIE * FPS))
                    o = max(0, min(o, uj.L // 2, pop.L // 2))
                    uj.o_in = pop.o_out = o
                    uj.krok_in = pop.krok_out = krok and o > 0
                    uj.start = pop.start + pop.L - o
                else:
                    uj.start = 0
            # wypowiedzi lektora nie mogą na siebie nachodzić (min. 0,3 s przerwy) – wydłuż wcześniejsze ujęcie
            kl = [uj for uj in self.ujecia if uj.lektor]
            kolizja = False
            for a, b in zip(kl, kl[1:]):
                brak = (a.start / FPS + a.lektor[0] + len(a.lektor[1]) / SR_AUDIO + 0.3) - (b.start / FPS + b.lektor[0])
                if brak > 0:
                    a.L += int(math.ceil(brak * FPS))
                    print("  [lektor] %s nachodzi na %s – ujęcie %s wydłużone o %.2f s"
                          % (os.path.basename(a.lektor[2]), os.path.basename(b.lektor[2]), a.rodzaj, brak))
                    kolizja = True
                    break
            if not kolizja:
                break
        self.ujecia[-1].o_out = 0
        self.N = self.ujecia[-1].start + self.ujecia[-1].L
        self.fi = int(round(WEJSCIE_Z_CZERNI * FPS))
        self.fo = int(round(WYJSCIE_W_CZERN * FPS))

    def ciaglosc_podpisow(self):
        """Kolejne panoramy z tym samym podpisem: podpis zostaje (bez zanikania), tytuł w stałym miejscu."""
        lancuch = []
        for i, uj in enumerate(self.ujecia + [None]):
            pop = self.ujecia[i - 1] if i else None
            ten_sam = (uj is not None and pop is not None and uj.rodzaj == pop.rodzaj == "panorama"
                       and uj.u.get("podpis") and uj.u.get("podpis") == pop.u.get("podpis"))
            if ten_sam:
                sam2 = (uj.u.get("podpis2") or "") == (pop.u.get("podpis2") or "")
                pop.opcje_podpisu["ciagly"] = (pop.opcje_podpisu.get("ciagly", (False, False))[0], True)
                uj.opcje_podpisu["ciagly"] = (True, False)
                pop.opcje_podpisu["ciagly2"] = (pop.opcje_podpisu.get("ciagly2", (False, False))[0], sam2)
                uj.opcje_podpisu["ciagly2"] = (sam2, False)
                lancuch.append(uj)
                continue
            if len(lancuch) > 1:
                n2 = max(len(Podpis.linie(self, q.u.get("podpis"), q.u.get("podpis2"))[2]) for q in lancuch)
                for q in lancuch:
                    q.opcje_podpisu["linie2_min"] = n2
            lancuch = [uj] if uj is not None else []

    def siatka_panoramy(self):
        """Rzadka siatka (co 4 px, z zapasem 1 węzła) we współrzędnych pikseli kadru – do map cv2."""
        k = ("p", self.W, self.H)
        if k not in self._siatki:
            xs = np.arange(self.W // 4 + 2, dtype=np.float32) * 4 - 2.5
            ys = np.arange(self.H // 4 + 2, dtype=np.float32) * 4 - 2.5
            self._siatki[k] = np.meshgrid(xs, ys)
        return self._siatki[k]

    def siatka_mesh(self, krok=16):
        k = ("m", self.W, self.H, krok)
        if k not in self._siatki:
            gx = np.unique(np.append(np.arange(0, self.W, krok), self.W)).astype(np.float64)
            gy = np.unique(np.append(np.arange(0, self.H, krok), self.H)).astype(np.float64)
            self._siatki[k] = (gx, gy)
        return self._siatki[k]

    def punkty_zmian(self):
        return [(uj.start + uj.o_in / 2) / FPS for uj in self.ujecia[1:]]

    def aktywne(self, n):
        return [(uj, n - uj.start) for uj in self.ujecia if uj.start <= n < uj.start + uj.L]

    def klatka(self, n):
        akt = self.aktywne(n)
        t0 = time.perf_counter()
        if len(akt) == 1:
            uj, k = akt[0]
            kl = uj.klatka(k)
        else:
            (ua, ka), (ub, kb) = akt[-2], akt[-1]
            a = ua.klatka(ka)
            b = ub.klatka(kb)
            kl = miks(a, b, ease_io((kb + 0.5) / max(1, ub.o_in)))
        f = 1.0
        if n < self.fi:
            f = ease_io((n + 0.5) / self.fi)
        if n >= self.N - self.fo:
            f *= ease_io((self.N - n - 0.5) / self.fo)
        if f < 1.0:
            kl = przyciemnij(kl, f)
        dt = time.perf_counter() - t0
        with self._lock:
            for uj, _ in akt:
                self.czas_rodzaj[uj.rodzaj] = self.czas_rodzaj.get(uj.rodzaj, 0.0) + dt / len(akt)
        return np.ascontiguousarray(kl)

    def przygotuj(self):
        t = time.time()
        self._lock = threading.Lock()
        self.czas_rodzaj = {}
        # wspólne przycięcie rzutów tego samego formatu → identyczna skala i położenie
        self.ramki_rzutow = {}
        for uj in self.ujecia:
            if isinstance(uj, UjecieRzut):
                im = wczytaj_rgb(sciezka(uj.u["obraz"], self.katalog))
                r = UjecieRzut.ramka_tresci(im)
                q = self.ramki_rzutow.get(im.size)
                self.ramki_rzutow[im.size] = r if q is None else (min(q[0], r[0]), min(q[1], r[1]),
                                                                   max(q[2], r[2]), max(q[3], r[3]))
        for uj in self.ujecia:                               # najpierw interpolacje (procesy równoległe)
            if isinstance(uj, UjecieAnimacja) and not self.podglad:
                uj.interpoluj()
        for uj in self.ujecia:
            uj.przygotuj()
        print("przygotowanie ujęć: %.1f s" % (time.time() - t))

    def klatki_png(self, czasy):
        """Pojedyncze klatki do PNG (kontrola wyglądu), bez kodowania."""
        self.przygotuj()
        wyn = []
        for t in sorted(czasy):
            n = min(self.N - 1, max(0, int(round(t * FPS))))
            kl = self.klatka(n)
            p = os.path.splitext(self.wyjscie)[0] + "_klatka_%06.2f.png" % (n / FPS)
            Image.fromarray(kl).save(p)
            wyn.append(p)
            print(p)
        for uj in self.ujecia:
            uj.zwolnij()
        return wyn


def _koder(sciezka_wy, W, H, opcje, log):
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", "%dx%d" % (W, H), "-framerate", str(FPS), "-i", "-", "-an",
           "-vf", "scale=out_color_matrix=bt709:out_range=tv:flags=bicubic+accurate_rnd,format=yuv420p",
           "-c:v", "libx264"] + opcje + [
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv",
           sciezka_wy]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=log)


def _pisarz(proc, q, bledy):
    try:
        while True:
            f = q.get()
            if f is None:
                break
            proc.stdin.write(f)
    except Exception as e:                       # np. BrokenPipe – ffmpeg padł
        bledy.append(e)
        while q.get() is not None:
            pass
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass


def _sonda(p):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration,bit_rate", "-of", "json", p],
                       capture_output=True, text=True)
    try:
        f = json.loads(r.stdout)["format"]
        return float(f["duration"]), int(f.get("bit_rate", 0))
    except Exception:
        return 0.0, 0


def _mux(wideo, audio, wyj, ab, czas):
    cmd = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", wideo]
    if audio:
        cmd += ["-i", audio, "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", ab, "-ar", "48000",
                "-af", "apad", "-t", "%.3f" % czas]
    cmd += ["-c:v", "copy", "-movflags", "+faststart", wyj]
    subprocess.run(cmd, check=True)


def montuj(sb, katalog=None, podglad=False, web=None, watki=3, klatki=None):
    """Składa film ze storyboardu (słownik); zwraca ścieżkę MP4.  `katalog` – baza ścieżek względnych."""
    t_start = time.time()
    katalog = os.path.abspath(katalog or sb.get("_katalog") or os.getcwd())
    m = Montaz(sb, katalog, podglad=podglad, watki=watki)
    czas = m.N / FPS
    print("%s %s „%s”: %d ujęć, %d klatek = %.2f s%s" % (sb.get("numer", ""), sb.get("pid", ""), sb.get("nazwa", ""),
          len(m.ujecia), m.N, czas, " (podgląd 960×540)" if podglad else ""))
    for i, uj in enumerate(m.ujecia):
        print("  %2d %-11s %6.2f – %6.2f s%s%s" % (i + 1, uj.rodzaj, uj.start / FPS, (uj.start + uj.L) / FPS,
              "  (cięcie)" if i and not uj.o_in else ("  (krok)" if uj.krok_in else ""),
              "  lektor %.2f–%.2f s" % (uj.start / FPS + uj.lektor[0], uj.start / FPS + uj.lektor[0]
                                        + len(uj.lektor[1]) / SR_AUDIO) if uj.lektor else ""))
    if klatki:
        return m.klatki_png(klatki)
    os.makedirs(os.path.dirname(m.wyjscie), exist_ok=True)
    web = (not podglad) and (sb.get("web", True) if web is None else web)

    # muzyka – osobny proces, równolegle z przygotowaniem i renderem
    muz = sb.get("muzyka", False)
    wav, proc_muz = None, None
    if isinstance(muz, str) and muz:
        wav = sciezka(muz, katalog)
    elif muz:
        wav = os.path.join(m.cache, "muzyka_%s.wav" % os.path.splitext(os.path.basename(m.wyjscie))[0])
        seed = int(sb.get("muzyka_seed", zlib.crc32(str(sb.get("pid", "")).encode()) % 1000))
        proc_muz = subprocess.Popen(
            [sys.executable, os.path.join(TU, "muzyka.py"), "%.4f" % czas, wav, "--seed", str(seed), "--json",
             "--punkty", ",".join("%.3f" % p for p in m.punkty_zmian())],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    m.przygotuj()

    # kodery: główny + (równolegle) web z limitem przepływności
    rdzen = os.path.splitext(os.path.basename(m.wyjscie))[0]
    tmp_v = os.path.join(m.cache, "wideo_%s.mp4" % rdzen)
    tmp_w = os.path.join(m.cache, "wideo_%s_web.mp4" % rdzen)
    log_path = os.path.join(m.cache, "ffmpeg_%s.log" % rdzen)
    log = open(log_path, "wb")
    if podglad:
        opcje = ["-preset", "veryfast", "-crf", "23", "-profile:v", "high", "-g", "50"]
    else:
        # CRF z storyboardu (domyślnie 19); limit szczytów przepływności ułatwia podział filmu na części ≤ 20 MB
        opcje = ["-preset", "slow", "-crf", str(sb.get("crf", 19)), "-maxrate", "8M", "-bufsize", "16M",
                 "-profile:v", "high", "-level:v", "4.1", "-g", "100", "-x264-params", "aq-mode=3"]
    kodery = [(_koder(tmp_v, m.W, m.H, opcje, log), tmp_v)]
    web_mb = float(sb.get("web_mb_na_minute", WEB_MB_NA_MINUTE)) * czas / 60.0
    ab_web = "128k"
    if web:
        z_dzwiekiem = bool(wav or muz or any(uj.lektor for uj in m.ujecia))
        budzet = web_mb * 1e6 * 8 * 0.985 - (136000 if z_dzwiekiem else 0) * czas   # bity na obraz
        maxrate = int(budzet / (czas + 1.8))                                     # VBV: ≤ maxrate·T + 0,9·bufsize
        opcje_w = ["-preset", "medium", "-crf", "21", "-maxrate", str(maxrate), "-bufsize", str(2 * maxrate),
                   "-profile:v", "high", "-level:v", "4.1", "-g", "100", "-x264-params", "aq-mode=3"]
        kodery.append((_koder(tmp_w, m.W, m.H, opcje_w, log), tmp_w))
        print("web: budżet %.2f MB, limit obrazu %d kb/s" % (web_mb, maxrate // 1000))

    import queue
    kolejki, watki_pis, bledy = [], [], []
    for proc, _ in kodery:
        q = queue.Queue(maxsize=6)
        th = threading.Thread(target=_pisarz, args=(proc, q, bledy), daemon=True)
        th.start()
        kolejki.append(q)
        watki_pis.append(th)

    t_r = time.time()
    ostatni_druk = t_r
    nastepne = {i: uj.start for i, uj in enumerate(m.ujecia)}
    try:
        with ThreadPoolExecutor(max_workers=watki) as ex:
            w_toku = deque()
            n_nast = 0
            for n in range(m.N):
                while len(w_toku) < 2 * watki + 2 and n_nast < m.N:
                    for uj in m.ujecia:                         # strumień animacji startuje z wyprzedzeniem
                        if uj.start - 2 * FPS <= n_nast < uj.start:
                            uj.rozgrzej()
                    w_toku.append(ex.submit(m.klatka, n_nast))
                    n_nast += 1
                kl = w_toku.popleft().result()
                for q in kolejki:
                    q.put(kl)
                if bledy:
                    raise RuntimeError("koder ffmpeg przerwał pracę – zob. %s" % log_path)
                for i, uj in enumerate(m.ujecia):              # zwolnij zakończone ujęcia
                    if nastepne.get(i) is not None and n >= uj.start + uj.L + 2 * watki + 2:
                        uj.zwolnij()
                        nastepne[i] = None
                if time.time() - ostatni_druk > 10:
                    ostatni_druk = time.time()
                    v = (n + 1) / (time.time() - t_r)
                    print("  klatka %d/%d  %.1f kl/s  pozostało ~%.0f s" % (n + 1, m.N, v, (m.N - n - 1) / v), flush=True)
    finally:
        for q in kolejki:
            q.put(None)
        for th in watki_pis:
            th.join()
        for proc, _ in kodery:
            proc.wait()
        for uj in m.ujecia:
            uj.zwolnij()
        log.close()
    for proc, p in kodery:
        if proc.returncode:
            raise RuntimeError("ffmpeg zakończył się błędem (%s): %s" % (p, open(log_path, errors="replace").read()[-3000:]))
    t_render = time.time() - t_r

    # muzyka gotowa?
    info_muz = None
    if proc_muz is not None:
        out, err = proc_muz.communicate()
        try:
            info_muz = json.loads(out.strip().splitlines()[-1])
        except Exception:
            raise RuntimeError("muzyka.py: " + err[-2000:])
    if wav and not os.path.exists(wav):
        raise FileNotFoundError(wav)
    # miks: lektor + przyciszanie muzyki, głośność muzyki (muzyka_glosnosc)
    klipy = [(uj.start / FPS + uj.lektor[0], uj.lektor[1]) for uj in m.ujecia if uj.lektor]
    glosnosc = float(sb.get("muzyka_glosnosc", 0.0))
    info_mix = None
    if klipy or abs(glosnosc) > 1e-6 or (isinstance(muz, str) and muz):
        mus = wczytaj_audio(wav, kanaly=2) if wav else None
        wav = os.path.join(m.cache, "audio_%s.wav" % os.path.splitext(os.path.basename(m.wyjscie))[0])
        info_mix = muzyka.miksuj(wav, czas, muzyka=mus, klipy=klipy, glosnosc_db=glosnosc,
                                 wycisz_koniec=3.0 if isinstance(muz, str) and muz else 0.0)

    _mux(tmp_v, wav, m.wyjscie, "160k", czas)
    wyniki = [m.wyjscie]
    if web:
        wyj_w = os.path.splitext(m.wyjscie)[0].replace("_podglad", "") + "_web.mp4"
        _mux(tmp_w, wav, wyj_w, ab_web, czas)
        if os.path.getsize(wyj_w) > web_mb * 1e6:            # awaryjnie: 2 przebiegi z pliku głównego
            print("web: %.2f MB > %.2f MB – kodowanie dwuprzebiegowe" % (os.path.getsize(wyj_w) / 1e6, web_mb))
            _web_2pass(tmp_v, wav, wyj_w, web_mb, czas, ab_web, m.cache)
        wyniki.append(wyj_w)
    for p in (tmp_v, tmp_w):
        if os.path.exists(p):
            os.remove(p)

    # podsumowanie
    print("render + kodowanie: %.1f s (%.1f kl/s); czas renderu wg rodzaju ujęć (suma wątków): %s"
          % (t_render, m.N / t_render, ", ".join("%s %.1f s" % kv for kv in sorted(m.czas_rodzaj.items()))))
    if info_muz:
        print("muzyka: %.1f LUFS, szczyt %.1f dBFS, >4 kHz %.3f%%, skok obwiedni %.2f LU/50 ms, trzaski %.2f, %s (%.1f s)"
              % (info_muz["lufs"], info_muz["szczyt_dbfs"], info_muz["energia_pow_4kHz_proc"],
                 info_muz["obwiednia_max_zmiana_lu_na_50ms"], info_muz["zmiany_akordow_d2_wzgl"],
                 "OK" if info_muz["ok"] else "UWAGA", info_muz["czas_generowania_s"]))
    if info_mix:
        print("miks audio: szczyt %.1f dBFS, %.1f LUFS%s, %s" % (
            info_mix["szczyt_dbfs"], info_mix["lufs_calosc"],
            ("; lektor %d klip(y) %s LUFS, min. %.1f dB nad muzyką" % (
                info_mix["lektor_klipy"], "/".join("%.1f" % v for v in info_mix["lektor_glosnosc_lufs"]),
                info_mix["lektor_nad_muzyka_db_min"])) if info_mix.get("lektor_klipy") else "",
            "OK" if info_mix["ok"] else "UWAGA"))
    for p in wyniki:
        d, br = _sonda(p)
        print("%-60s %7.2f s  %7.2f MB  %5d kb/s" % (p, d, os.path.getsize(p) / 1e6, br // 1000))
    print("razem: %.1f s" % (time.time() - t_start))
    return m.wyjscie


def _web_2pass(src, wav, wyj, mb, czas, ab, cache):
    budzet = mb * 1e6 * 8 * 0.97 - (136000 * czas if wav else 0)
    br = int(budzet / czas)
    log = os.path.join(cache, "x264_2pass")
    base = [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", src]
    v = ["-c:v", "libx264", "-preset", "medium", "-b:v", str(br), "-maxrate", str(int(br * 1.5)),
         "-bufsize", str(3 * br), "-profile:v", "high", "-g", "100", "-passlogfile", log]
    subprocess.run(base + v + ["-pass", "1", "-an", "-f", "null", os.devnull], check=True)
    tmp = os.path.join(cache, "web_2pass.mp4")
    subprocess.run(base + v + ["-pass", "2", "-an", tmp], check=True)
    _mux(tmp, wav, wyj, ab, czas)
    os.remove(tmp)


def main():
    ap = argparse.ArgumentParser(description="Montaż filmu prezentacyjnego ze storyboardu JSON.")
    ap.add_argument("storyboard")
    ap.add_argument("--podglad", action="store_true", help="szybki podgląd 960×540 (bez wersji web)")
    ap.add_argument("--bez-web", action="store_true", help="bez wersji _web.mp4")
    ap.add_argument("--klatki", default="", help="tylko wybrane klatki do PNG, np. 2,9.5,31 (sekundy)")
    ap.add_argument("--watki", type=int, default=3, help="wątki renderu (domyślnie 3)")
    a = ap.parse_args()
    with open(a.storyboard, encoding="utf-8") as f:
        sb = json.load(f)
    katalog = os.path.dirname(os.path.abspath(a.storyboard))
    klatki = [float(v) for v in a.klatki.split(",") if v.strip()]
    montuj(sb, katalog=katalog, podglad=a.podglad, web=False if a.bez_web else None, watki=a.watki,
           klatki=klatki or None)
    return 0


if __name__ == "__main__":
    sys.exit(main())
