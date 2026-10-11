#!/usr/bin/env python3
"""Spokojny ambientowy podkład (pad) do filmów prezentacyjnych: WAV 48 kHz stereo, ok. −20 LUFS.

Progresja Cmaj9 – Am9 – Fmaj7(#11) – G6/9 (6–8 s na akord, ostatni zawsze Cmaj9), miękkie głosy
sinus/trójkąt z rozstrojeniem (chorus), bas sinusoidalny, rzadkie ciche dzwonki, łagodny dolnoprzepust,
pogłos splotowy (gasnący szum w pasmach), normalizacja głośności (BS.1770, bramkowana), wejście 2 s, wyjście 3 s.

Użycie:  python3 film/muzyka.py 55.0 wyjscie.wav [--seed 3] [--punkty 4,9.5] [--json]   (generuje i sprawdza)
Import:  from film.muzyka import generuj, sprawdz
"""
import argparse
import math
import sys
import wave

import numpy as np

SR = 48000          # wyjście
SRW = 16000         # synteza i obróbka (treść < 4 kHz), na końcu nadpróbkowanie ×3
CEL_LUFS = -20.0
MAX_SZCZYT_DB = -3.0

# (nazwa, bas, pad, góra) – numery MIDI; wspólne dźwięki sąsiednich akordów brzmią bez przerwy
AKORDY = [
    ("Cmaj9", 36, (55, 59, 62, 64), (74,)),
    ("Am9", 33, (55, 59, 60, 64), (71,)),
    ("Fmaj7(#11)", 41, (57, 60, 64), (71,)),
    ("G6/9", 43, (59, 62, 64, 69), (74,)),
]
# dźwięki dzwonków (oktawa wyżej, tylko składniki akordu)
DZWONKI = [(76, 79, 74, 83), (76, 72, 79, 71), (77, 76, 72, 81), (74, 79, 76, 81)]


def hz(m):
    return 440.0 * 2.0 ** ((m - 69) / 12.0)


# ---------------------------------------------------------------- plan akordów

def plan_akordow(czas, punkty=None, dl=7.0, lo=6.0, hi=8.0):
    """Momenty zmian akordów (s) i indeksy akordów.  `punkty` – preferowane chwile zmian (np. środki przenikań)."""
    zmiany = [0.0]
    punkty = sorted(p for p in (punkty or []) if 0 < p < czas)
    while True:
        t = zmiany[-1]
        if czas - t < hi + lo * 0.5:          # resztę gra ostatni akord
            break
        kand = [p for p in punkty if t + lo - 0.5 <= p <= t + hi + 0.5]
        nast = min(kand, key=lambda p: abs(p - (t + dl))) if kand else t + dl
        zmiany.append(nast)
    idx = [k % len(AKORDY) for k in range(len(zmiany))]
    idx[-1] = 0                                   # koniec na tonice
    if len(idx) > 1 and idx[-2] == 0:            # dwa C pod rząd → jeden dłuższy
        zmiany.pop()
        idx.pop()
    return zmiany, idx


def okna(zmiany, n, x=3.0):
    """Okna akordów: podział jedności z łagodnym (sin²) przenikaniem długości `x` wokół każdej zmiany."""
    t = np.arange(n) / SRW
    w = []
    granice = list(zmiany[1:])
    for k in range(len(zmiany)):
        e = np.ones(n)
        if k > 0:                                  # narastanie wokół zmiany k
            c = granice[k - 1]
            u = np.clip((t - (c - x / 2)) / x, 0, 1)
            e *= np.sin(0.5 * np.pi * u) ** 2
        if k < len(zmiany) - 1:                    # wygaszanie wokół zmiany k+1
            c = granice[k]
            u = np.clip((t - (c - x / 2)) / x, 0, 1)
            e *= np.cos(0.5 * np.pi * u) ** 2
        w.append(e)
    return w


# ---------------------------------------------------------------- głosy

def _faza(f0, i0, i1, rng, detune_c, vib_c, vib_hz):
    t = np.arange(i0, i1) / SRW
    cent = detune_c + vib_c * np.sin(2 * np.pi * vib_hz * t + rng.uniform(0, 2 * np.pi))
    f = f0 * 2.0 ** (cent / 1200.0)
    return 2 * np.pi * np.cumsum(f) / SRW + rng.uniform(0, 2 * np.pi)


def _barwa(faza, f0, harm):
    """Suma harmonicznych (tylko poniżej 3,5 kHz – bez ostrych składowych)."""
    out = np.zeros_like(faza)
    for h, a in enumerate(harm, start=1):
        if a and h * f0 < 3500:
            out += a * np.sin(h * faza)
    return out


def _dodaj(mix, i0, sygnal, pan):
    """Panorama równej mocy, pan ∈ [-1, 1]."""
    th = (pan + 1) * np.pi / 4
    mix[0, i0:i0 + len(sygnal)] += np.cos(th) * sygnal
    mix[1, i0:i0 + len(sygnal)] += np.sin(th) * sygnal


def _zakres(env, prog=1e-6):
    nz = np.flatnonzero(env > prog)
    return (int(nz[0]), int(nz[-1]) + 1) if len(nz) else (0, 0)


def synteza(czas, zmiany, idx, rng):
    n = int(round(czas * SRW))
    mix = np.zeros((2, n))
    w = okna(zmiany, n)
    # obwiednie dźwięków: sqrt(suma okien akordów, w których dźwięk występuje) → wspólne dźwięki = 1
    def obwiednie(wybierz):
        sl = {}
        for k, a in enumerate(idx):
            for m in wybierz(AKORDY[a]):
                sl[m] = sl.get(m, 0) + w[k]
        return {m: np.sqrt(np.clip(v, 0, 1)) for m, v in sl.items()}

    PAD = (1.0, 0.30, 0.16, 0.085, 0.05, 0.03, 0.018, 0.011)     # łagodny „trójkąt”
    for m, env in sorted(obwiednie(lambda a: a[2]).items()):
        i0, i1 = _zakres(env)
        f0 = hz(m)
        g = 0.30 * (1.0 if m < 66 else 0.8)
        oddech = 1.0 + 0.06 * np.sin(2 * np.pi * rng.uniform(0.04, 0.09) * np.arange(i0, i1) / SRW + rng.uniform(0, 6.3))
        e = g * env[i0:i1] * oddech
        # chorus: środek + dwie słabsze, różnie rozstrojone kopie po bokach (płytkie dudnienie)
        for d, a, pan in ((0.0, 1.0, rng.uniform(-0.15, 0.15)),
                          (-rng.uniform(4.0, 7.0), 0.38, -rng.uniform(0.5, 0.75)),
                          (rng.uniform(5.0, 8.0), 0.38, rng.uniform(0.5, 0.75))):
            s = _barwa(_faza(f0, i0, i1, rng, d, 1.5, rng.uniform(0.08, 0.2)), f0, PAD)
            _dodaj(mix, i0, a * e * s, pan)
    GORA = (1.0, 0.12, 0.04)
    for m, env in sorted(obwiednie(lambda a: a[3]).items()):
        i0, i1 = _zakres(env)
        f0 = hz(m)
        for znak in (-1, 1):
            s = _barwa(_faza(f0, i0, i1, rng, znak * rng.uniform(3, 6), 2.0, rng.uniform(0.1, 0.25)), f0, GORA)
            _dodaj(mix, i0, 0.10 * env[i0:i1] * s, znak * 0.6)
        # „powietrze”: ten sam dźwięk o oktawę wyżej, bardzo cicho, z wolnym tremolo
        tt = np.arange(i0, i1) / SRW
        trem = 0.75 + 0.25 * np.sin(2 * np.pi * rng.uniform(0.05, 0.12) * tt + rng.uniform(0, 6.3))
        s = _barwa(_faza(2 * f0, i0, i1, rng, 0.0, 2.5, rng.uniform(0.15, 0.3)), 2 * f0, (1.0,))
        _dodaj(mix, i0, 0.045 * env[i0:i1] * trem * s, rng.uniform(-0.4, 0.4))
    BAS = (1.0, 0.30, 0.07)
    for m, env in sorted(obwiednie(lambda a: (a[1],)).items()):
        i0, i1 = _zakres(env)
        f0 = hz(m)
        s = _barwa(_faza(f0, i0, i1, rng, 0.0, 0.0, 0.1), f0, BAS)
        _dodaj(mix, i0, 0.25 * env[i0:i1] * s, 0.0)
    # rzadkie, miękkie dzwonki (atak 0,25 s – bez perkusyjnego uderzenia)
    granice = list(zmiany) + [czas]
    for k, a in enumerate(idx):
        t0, t1 = granice[k], granice[k + 1]
        chwile = [t0 + rng.uniform(1.0, 2.0)]
        if t1 - t0 > 6.5:
            chwile.append(t0 + rng.uniform(3.8, 4.8))
        for j, tc in enumerate(chwile):
            if tc > czas - 5.0:
                continue
            m = DZWONKI[a][(k + j * 2 + int(rng.integers(0, 2))) % 4]
            f0 = hz(m)
            dl = int(6.0 * SRW)
            i0 = int(tc * SRW)
            i1 = min(n, i0 + dl)
            tt = np.arange(i1 - i0) / SRW
            env = np.exp(-tt / 1.7) * np.sin(0.5 * np.pi * np.clip(tt / 0.25, 0, 1)) ** 2
            env *= np.cos(0.5 * np.pi * np.clip((tt - 5.0) / 1.0, 0, 1)) ** 2
            s = _barwa(_faza(f0, i0, i1, rng, 0.0, 1.0, 0.3), f0, (1.0, 0.12, 0.04))
            _dodaj(mix, i0, 0.13 * env * s, rng.uniform(-0.5, 0.5))
    return mix


# ---------------------------------------------------------------- filtry (zerowa faza, w dziedzinie częstotliwości)

def _nfft(n):
    return 1 << int(math.ceil(math.log2(max(n, 2))))


def filtr(x, odp, sr=SRW):
    """Filtr o zerowej fazie: x (kanały × próbki), odp(f) → mnożnik amplitudy."""
    n = x.shape[-1]
    nf = _nfft(n + sr // 2)
    f = np.fft.rfftfreq(nf, 1 / sr)
    return np.fft.irfft(np.fft.rfft(x, nf) * odp(f), nf)[..., :n]


def dolny(fc, rzad=2):
    return lambda f: 1.0 / np.sqrt(1.0 + (f / fc) ** (2 * rzad))


def gorny(fc, rzad=2):
    return lambda f: (f / fc) ** rzad / np.sqrt(1.0 + (f / fc) ** (2 * rzad))


def nadprobkuj(x, k):
    """Nadpróbkowanie ×k bez aliasingu (dopełnienie widma zerami); sygnał na brzegach jest wyciszony."""
    n = x.shape[-1]
    X = np.fft.rfft(x, n)
    Y = np.zeros(x.shape[:-1] + (n * k // 2 + 1,), complex)
    Y[..., : X.shape[-1]] = X
    return np.fft.irfft(Y, n * k) * k


def poglos(x, rng, sr=SRW, dl=4.2, rt=(3.6, 3.0, 2.1, 1.2), granice=(350.0, 1500.0, 4000.0), predelay=0.028, mokry=0.55):
    """Pogłos splotowy: dla każdego kanału gasnący szum w 4 pasmach (wyższe pasma gasną szybciej)."""
    n_ir = int(dl * sr)
    t = np.arange(n_ir) / sr
    f = np.fft.rfftfreq(n_ir, 1 / sr)
    L = [1.0 / (1.0 + (f / g) ** 4) for g in granice]
    maski = [L[0], L[1] - L[0], L[2] - L[1], 1.0 - L[2]]
    ir = np.zeros((2, n_ir))
    for ch in range(2):
        widmo = np.fft.rfft(rng.standard_normal(n_ir))
        for m, r in zip(maski, rt):
            ir[ch] += np.fft.irfft(widmo * m, n_ir) * np.exp(-6.91 * t / r)
    ir *= np.sin(0.5 * np.pi * np.clip(t / 0.03, 0, 1)) ** 2       # łagodne zagęszczanie na starcie
    ir = np.concatenate([np.zeros((2, int(predelay * sr))), ir], axis=1)
    ir /= np.sqrt((ir ** 2).sum(axis=1, keepdims=True))            # energia jednostkowa
    n = x.shape[1]
    nf = _nfft(n + ir.shape[1])
    X = np.fft.rfft(x.mean(axis=0), nf)
    wet = np.stack([np.fft.irfft(X * np.fft.rfft(ir[c], nf), nf)[:n] for c in range(2)])
    return x + mokry * wet


# ---------------------------------------------------------------- głośność (ITU-R BS.1770, wagi K)

def _waga_k(f):
    """|H| filtra K (półka + górnoprzepust RLB) w funkcji częstotliwości fizycznej (projekt dla 48 kHz)."""
    z = np.exp(-1j * 2 * np.pi * f / 48000.0)
    b1, a1 = (1.53512485958697, -2.69169618940638, 1.19839281085285), (1.0, -1.69065929318241, 0.73248077421585)
    b2, a2 = (1.0, -2.0, 1.0), (1.0, -1.99004745483398, 0.99007225036621)
    h = 1.0
    for b, a in ((b1, a1), (b2, a2)):
        h = h * (b[0] + b[1] * z + b[2] * z * z) / (a[0] + a[1] * z + a[2] * z * z)
    return np.abs(h)


def _bloki(x, sr, blok_s=0.4, krok_s=0.1):
    """Energie bloków ważonych K (suma kanałów) – podstawa głośności chwilowej i zintegrowanej."""
    y = filtr(x, _waga_k, sr)
    blok, krok = int(blok_s * sr), int(krok_s * sr)
    if y.shape[1] < blok:
        return np.zeros(0)
    c = np.cumsum(np.concatenate([np.zeros((y.shape[0], 1)), y ** 2], axis=1), axis=1)
    st = np.arange(0, y.shape[1] - blok + 1, krok)
    return ((c[:, st + blok] - c[:, st]) / blok).sum(axis=0)


def lufs(x, sr=SRW):
    """Zintegrowana głośność (LUFS) z bramkowaniem bezwzględnym −70 i względnym −10 LU."""
    z = _bloki(x, sr)
    z1 = z[-0.691 + 10 * np.log10(np.maximum(z, 1e-20)) > -70]
    if not len(z1):
        return -float("inf")
    prog = -0.691 + 10 * np.log10(z1.mean()) - 10
    z2 = z1[(-0.691 + 10 * np.log10(z1)) > prog]
    return float(-0.691 + 10 * np.log10(z2.mean()))


# ---------------------------------------------------------------- zapis / odczyt

def zapisz_wav(sciezka, x, rng):
    d = (rng.random(x.shape) - rng.random(x.shape)) / 32768.0     # dither TPDF ±1 LSB
    q = np.clip(np.round((x + d) * 32767.0), -32768, 32767).astype("<i2")
    with wave.open(sciezka, "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(q.T.copy().tobytes())


def wczytaj_wav(sciezka):
    with wave.open(sciezka, "rb") as f:
        sr, ch, sw = f.getframerate(), f.getnchannels(), f.getsampwidth()
        raw = f.readframes(f.getnframes())
    assert sw == 2, "oczekiwano 16 bit"
    x = np.frombuffer(raw, "<i2").reshape(-1, ch).T.astype(np.float64) / 32768.0
    return x, sr


# ---------------------------------------------------------------- generowanie

def generuj(czas, sciezka, punkty=None, seed=0, cel_lufs=CEL_LUFS, sprawdzaj=True):
    """Generuje podkład długości `czas` s do pliku WAV; zwraca słownik z wynikami kontroli."""
    rng = np.random.default_rng(seed)
    czas = round(czas * SRW) / SRW
    zmiany, idx = plan_akordow(czas, punkty)
    x = synteza(czas, zmiany, idx, rng)
    x = filtr(x, lambda f: dolny(3500.0)(f) * gorny(40.0)(f))
    x = poglos(x, rng)
    x = filtr(x, dolny(5000.0, 1))                                  # łagodne domknięcie góry po pogłosie
    x -= x.mean(axis=1, keepdims=True)
    t = np.arange(x.shape[1]) / SRW
    x *= np.sin(0.5 * np.pi * np.clip(t / 2.0, 0, 1)) ** 2          # wejście 2 s
    x *= np.cos(0.5 * np.pi * np.clip((t - (czas - 3.0)) / 3.0, 0, 1)) ** 2   # wyjście 3 s
    g = 10 ** ((cel_lufs - lufs(x)) / 20)
    x = nadprobkuj(x, SR // SRW)
    szczyt = np.abs(x).max() * g
    if szczyt > 10 ** (MAX_SZCZYT_DB / 20):
        g *= 10 ** (MAX_SZCZYT_DB / 20) / szczyt
    x *= g
    zapisz_wav(sciezka, x, rng)
    info = {"akordy": [(round(z, 2), AKORDY[a][0]) for z, a in zip(zmiany, idx)]}
    if sprawdzaj:
        info.update(sprawdz(sciezka, zmiany[1:]))
    return info


def sprawdz(sciezka, zmiany=()):
    """Kontrola liczbowa: przesterowanie, DC, głośność, widmo, gładkość obwiedni, trzaski przy zmianach akordów."""
    x, sr = wczytaj_wav(sciezka)
    n = x.shape[1]
    r = {"czas_s": round(n / sr, 3), "sr": sr}
    r["szczyt_dbfs"] = round(20 * math.log10(max(np.abs(x).max(), 1e-12)), 2)
    r["przester_probek"] = int((np.abs(x) >= 32767 / 32768).sum())
    r["dc"] = [float("%.2e" % v) for v in x.mean(axis=1)]
    r["lufs"] = round(lufs(x, sr), 2)
    # widmo
    nf = _nfft(n)
    P = (np.abs(np.fft.rfft(x, nf)) ** 2).sum(axis=0)
    f = np.fft.rfftfreq(nf, 1 / sr)
    r["energia_pow_4kHz_proc"] = round(100 * P[f > 4000].sum() / P.sum(), 4)
    r["srodek_widma_hz"] = round(float((P * f).sum() / P.sum()), 1)
    # obwiednia: głośność chwilowa (bloki 400 ms co 50 ms), największa zmiana między sąsiednimi pomiarami
    z = _bloki(x, sr, 0.4, 0.05)
    gl = -0.691 + 10 * np.log10(np.maximum(z, 1e-20))
    tb = np.arange(len(gl)) * 0.05 + 0.2
    srodek = (tb > 2.5) & (tb < n / sr - 3.5)
    d = np.abs(np.diff(gl))
    r["glosnosc_chwilowa_zakres_lu"] = round(float(gl[srodek].max() - gl[srodek].min()), 2)
    r["obwiednia_max_zmiana_lu_na_50ms"] = round(float(d[srodek[1:]].max()), 3)
    # trzaski: druga różnica (czuła na nieciągłości) przy zmianach akordów na tle otoczenia ±1,5 s
    d2 = np.abs(np.diff(x, 2, axis=1)).max(axis=0)
    r["skok_probek_max"] = round(float(np.abs(np.diff(x, axis=1)).max()), 5)
    stos = []
    w = int(0.05 * sr)
    for zz in zmiany:
        a, b = int((zz - 1.5) * sr), int((zz + 1.5) * sr)
        if 0 < a < b < len(d2):
            lok = d2[a:b]
            c = len(lok) // 2
            tlo = max(lok[: c - w].max(), lok[c + w:].max(), 1e-12)
            stos.append(float(lok[c - w: c + w].max() / tlo))
    r["zmiany_akordow_d2_wzgl"] = round(max(stos), 3) if stos else None
    hf = filtr(x, gorny(8000.0, 4), sr)
    r["resztka_pow_8kHz_dbfs"] = round(20 * math.log10(max(np.abs(hf).max(), 1e-12)), 1)
    r["ok"] = bool(
        r["szczyt_dbfs"] <= MAX_SZCZYT_DB + 0.05 and r["przester_probek"] == 0
        and max(abs(v) for v in r["dc"]) < 1e-4
        and abs(r["lufs"] - CEL_LUFS) < 1.0
        and r["energia_pow_4kHz_proc"] < 1.0
        and r["obwiednia_max_zmiana_lu_na_50ms"] < 1.0
        and (r["zmiany_akordow_d2_wzgl"] or 0) < 1.5
        and r["resztka_pow_8kHz_dbfs"] < -60
    )
    return r


# ---------------------------------------------------------------- lektor i miks końcowy

def lufs_lub_rms(x, sr=SR):
    """Głośność klipu (LUFS); dla bardzo krótkich – przybliżenie z RMS."""
    x = np.atleast_2d(x)
    gl = lufs(x, sr)
    if not np.isfinite(gl):
        gl = 20 * math.log10(max(float(np.sqrt((x ** 2).mean())), 1e-9)) - 0.691
    return gl


def aktywnosc(x, sr=SR, okno=0.02, zakres_db=40.0):
    """Początek i koniec mowy w klipie (s): okna 20 ms głośniejsze niż (szczyt − 40 dB)."""
    o = max(1, int(okno * sr))
    n = len(x) // o
    if n == 0:
        return 0.0, len(x) / sr
    db = 20 * np.log10(np.sqrt((x[: n * o].reshape(n, o) ** 2).mean(axis=1)) + 1e-12)
    idx = np.flatnonzero(db > max(db.max() - zakres_db, -70.0))
    return idx[0] * o / sr, (idx[-1] + 1) * o / sr


def ogranicznik(x, prog_db=-1.0, sr=SR, blok_ms=2.0, zwolnienie_ms=80.0):
    """Ogranicznik szczytów z wyprzedzeniem (blokowy, gładkie wzmocnienie ≤ 1) – bez przesterowania."""
    x = np.atleast_2d(x)
    prog = 10 ** (prog_db / 20)
    a = np.abs(x).max(axis=0)
    if a.max() <= prog:
        return x
    b = max(1, int(blok_ms / 1000 * sr))
    nb = -(-len(a) // b)
    szczyty = np.pad(a, (0, nb * b - len(a))).reshape(nb, b).max(axis=1)
    g = np.minimum(1.0, prog / np.maximum(szczyty, 1e-12))
    gp = np.pad(g, 2, constant_values=1.0)                       # wyprzedzenie ±2 bloki
    g = np.minimum.reduce([gp[i:i + nb] for i in range(5)])
    k = math.exp(-b / (zwolnienie_ms / 1000 * sr))               # łagodny powrót do 1
    for i in range(1, nb):
        g[i] = min(g[i], g[i - 1] * k + (1 - k))
    gs = np.interp(np.arange(len(a)), np.arange(nb) * b + (b - 1) / 2, g)
    return x * gs


def miksuj(sciezka, czas, muzyka=None, klipy=(), glosnosc_db=0.0, lektor_lufs=-16.0, duck_db=-12.0,
           atak=0.3, zwolnienie=0.8, wycisz_koniec=0.0, seed=0, slady=None):
    """Miks końcowy 48 kHz stereo: muzyka (tablica 2×N lub None) przyciszana pod lektorem + klipy lektora.

    klipy: [(chwila_startu_s, próbki mono 48 kHz)].  Każdy klip: górnoprzepust 80 Hz, normalizacja do −16 LUFS;
    muzyka −12 dB, gdy ktokolwiek mówi (narastanie 0,3 s z wyprzedzeniem, powrót 0,8 s).  Zwraca wyniki kontroli."""
    n = int(round(czas * SR))
    t = np.arange(n) / SR
    mus = np.zeros((2, n))
    if muzyka is not None:
        m = np.atleast_2d(np.asarray(muzyka, np.float64))
        if m.shape[0] == 1:
            m = np.repeat(m, 2, axis=0)
        k = min(n, m.shape[1])
        mus[:, :k] = m[:2, :k] * 10 ** (glosnosc_db / 20)
        if wycisz_koniec > 0:
            mus *= np.cos(0.5 * np.pi * np.clip((t - (czas - wycisz_koniec)) / wycisz_koniec, 0, 1)) ** 2
    glos = np.zeros(n)
    env = np.zeros(n)
    odcinki = []
    for t0, x in klipy:
        x = filtr(np.asarray(x, np.float64)[None, :], gorny(80.0, 2), SR)[0]
        x *= 10 ** ((lektor_lufs - 3.01 - lufs_lub_rms(x)) / 20)       # mono w obu kanałach = +3 dB
        i0 = int(round(t0 * SR))
        i1 = min(n, i0 + len(x))
        if i1 <= i0:
            continue
        glos[i0:i1] += x[: i1 - i0]
        a0, a1 = aktywnosc(x)
        on, off = t0 + a0, t0 + a1
        up = np.sin(0.5 * np.pi * np.clip((t - (on - atak)) / atak, 0, 1)) ** 2
        dn = np.cos(0.5 * np.pi * np.clip((t - off) / zwolnienie, 0, 1)) ** 2
        env = np.maximum(env, np.where(t < on, up, np.where(t > off, dn, 1.0)))
        odcinki.append((on, off))
    glos = ogranicznik(glos, -1.5)[0]
    mus_d = mus * 10 ** (duck_db * env / 20)                         # ducking w dB – płynnie
    mix = ogranicznik(mus_d + glos[None, :], -1.0)
    if slady:                                                        # ślady do kontroli (testy)
        np.save(slady + "_glos.npy", glos.astype(np.float32))
        np.save(slady + "_muzyka.npy", mus.astype(np.float32))
    zapisz_wav(sciezka, mix, np.random.default_rng(seed))
    # kontrola: przesterowanie, głośność, przewaga lektora nad muzyką w czasie mowy (ważenie K)
    x, sr = wczytaj_wav(sciezka)
    r = {"szczyt_dbfs": round(20 * math.log10(max(np.abs(x).max(), 1e-12)), 2),
         "przester_probek": int((np.abs(x) >= 32767 / 32768).sum()),
         "lufs_calosc": round(lufs(x, sr), 2)}
    if odcinki:
        kv = filtr(glos[None, :], _waga_k, SR)[0] ** 2
        km = (filtr(mus_d, _waga_k, SR) ** 2).sum(axis=0)
        przewagi, gl_lek = [], []
        for on, off in odcinki:
            i0, i1 = int(on * SR), int(off * SR)
            ev, em = kv[i0:i1].mean() * 2, km[i0:i1].mean()            # lektor w obu kanałach
            przewagi.append(10 * math.log10(ev / max(em, 1e-15)))
            gl_lek.append(-0.691 + 10 * math.log10(max(ev, 1e-15)))
        r["lektor_klipy"] = len(odcinki)
        r["lektor_glosnosc_lufs"] = [round(v, 1) for v in gl_lek]
        r["lektor_nad_muzyka_db_min"] = round(min(przewagi), 1)
    r["ok"] = bool(r["przester_probek"] == 0 and r["szczyt_dbfs"] <= -0.9
                   and (not odcinki or r["lektor_nad_muzyka_db_min"] >= 10.0))
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("czas", type=float, help="długość w sekundach")
    ap.add_argument("wyjscie", help="plik WAV")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--punkty", default="", help="preferowane chwile zmian akordów, np. 4.0,9.5,15")
    ap.add_argument("--json", action="store_true", help="wynik kontroli jako JSON (dla montaz.py)")
    a = ap.parse_args()
    import time
    t = time.time()
    punkty = [float(v) for v in a.punkty.split(",") if v.strip()]
    info = generuj(a.czas, a.wyjscie, punkty=punkty, seed=a.seed)
    info["czas_generowania_s"] = round(time.time() - t, 2)
    if a.json:
        import json
        print(json.dumps(info, ensure_ascii=False))
    else:
        for k, v in info.items():
            print("%-32s %s" % (k, v))
    return 0 if info.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
