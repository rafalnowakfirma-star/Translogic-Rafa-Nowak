#!/usr/bin/env python3
"""Lektor filmów: tekst → WAV polskim głosem (Piper przez sherpa-onnx, offline) + kontrola zrozumiałości (Whisper).

Uruchamiaj interpreterem z sherpa-onnx:
  /home/user/tools/ttsenv/bin/python film/lektor.py p01 --wersja 2        → out/film/v2/p01/lektor/*.wav + lektor.json
Teksty: film/narracja/v<wersja>/<pid>.json (segmenty jak w scenariuszu: tytul, lotu, dach, spacer{stacja: tekst}, …).
"""
import argparse
import json
import os
import re
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLOS = os.path.join(HERE, "zasoby", "glos")
ASR = "/home/user/tools/asr/sherpa-onnx-whisper-small"

_tts = {}
_asr = None

JEDN = ["", "jeden", "dwa", "trzy", "cztery", "pięć", "sześć", "siedem", "osiem", "dziewięć", "dziesięć", "jedenaście",
        "dwanaście", "trzynaście", "czternaście", "piętnaście", "szesnaście", "siedemnaście", "osiemnaście", "dziewiętnaście"]
DZIES = ["", "", "dwadzieścia", "trzydzieści", "czterdzieści", "pięćdziesiąt", "sześćdziesiąt", "siedemdziesiąt",
         "osiemdziesiąt", "dziewięćdziesiąt"]
SETKI = ["", "sto", "dwieście", "trzysta", "czterysta", "pięćset", "sześćset", "siedemset", "osiemset", "dziewięćset"]


def slownie(n):
    n = int(n)
    if n == 0:
        return "zero"
    out = []
    if n >= 1000:
        k = n // 1000
        out.append("tysiąc" if k == 1 else slownie(k) + (" tysiące" if k % 10 in (2, 3, 4) and k % 100 not in (12, 13, 14) else " tysięcy"))
        n %= 1000
    if n >= 100:
        out.append(SETKI[n // 100])
        n %= 100
    if n >= 20:
        out.append(DZIES[n // 10])
        n %= 10
    if n:
        out.append(JEDN[n])
    return " ".join(w for w in out if w)


def _m2(n):
    n = int(n)
    if n == 1:
        return "metr kwadratowy"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return "metry kwadratowe"
    return "metrów kwadratowych"


def _m(n):
    n = int(n)
    if n == 1:
        return "metr"
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return "metry"
    return "metrów"


def normalizuj(t):
    """Symbole i skróty na słowa – syntezator czyta wtedy poprawnie."""
    t = t.replace("–", ",").replace("—", ",").replace("…", ".").replace("„", "").replace("”", "").replace('"', "")
    t = re.sub(r"(\d+)\s*m²", lambda m: f"{slownie(m.group(1))} {_m2(m.group(1))}", t)
    t = re.sub(r"(\d+),(\d)\s*m\b", lambda m: f"{slownie(m.group(1))} i {slownie(m.group(2))} dziesiątych metra", t)
    t = re.sub(r"(\d+)\s*×\s*(\d+)\s*m\b", lambda m: f"{slownie(m.group(1))} na {slownie(m.group(2))} {_m(m.group(2))}", t)
    t = re.sub(r"(\d+)\s*×\s*(\d+)", lambda m: f"{slownie(m.group(1))} na {slownie(m.group(2))}", t)
    t = re.sub(r"(\d+)\s*m\b", lambda m: f"{slownie(m.group(1))} {_m(m.group(1))}", t)
    t = re.sub(r"(\d+)\s*%", lambda m: f"{slownie(m.group(1))} procent", t)
    t = re.sub(r"\bnp\.", "na przykład", t)
    t = re.sub(r"\bm\.in\.", "między innymi", t)
    t = re.sub(r"\bok\.", "około", t)
    t = re.sub(r"\d+", lambda m: slownie(m.group(0)), t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def tts(glos="gosia"):
    if glos not in _tts:
        import sherpa_onnx
        d = os.path.join(GLOS, f"vits-piper-pl_PL-{glos}-medium")
        onnx = [f for f in os.listdir(d) if f.endswith(".onnx")][0]
        cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=os.path.join(d, onnx), tokens=os.path.join(d, "tokens.txt"),
                                                       data_dir=os.path.join(d, "espeak-ng-data"),
                                                       noise_scale=0.6, noise_scale_w=0.75, length_scale=1.0),
            num_threads=2, provider="cpu"), max_num_sentences=2)
        _tts[glos] = sherpa_onnx.OfflineTts(cfg)
    return _tts[glos]


def mow(tekst, plik, glos="gosia", tempo=0.94):
    """Syntetyzuje tekst do WAV (mono), wyrównuje głośność; zwraca długość w sekundach."""
    a = tts(glos).generate(normalizuj(tekst), sid=0, speed=tempo)
    s = np.asarray(a.samples, dtype=np.float32)
    sr = a.sample_rate
    # cisza na początku i końcu przycięta, 0,15 s marginesu
    thr = 0.01 * np.abs(s).max()
    nz = np.nonzero(np.abs(s) > thr)[0]
    if len(nz):
        s = s[max(0, nz[0] - int(0.05 * sr)): nz[-1] + int(0.15 * sr)]
    rms = np.sqrt(np.mean(s ** 2)) or 1.0
    s = s * (0.08 / rms)
    s = np.clip(s, -0.95, 0.95)
    os.makedirs(os.path.dirname(plik), exist_ok=True)
    sf.write(plik, s, sr)
    return len(s) / sr


def asr(plik):
    """Transkrypcja Whisperem – do sprawdzenia, czy syntezator przeczytał tekst zrozumiale."""
    global _asr
    import sherpa_onnx
    if _asr is None:
        _asr = sherpa_onnx.OfflineRecognizer.from_whisper(
            encoder=f"{ASR}/small-encoder.int8.onnx", decoder=f"{ASR}/small-decoder.int8.onnx",
            tokens=f"{ASR}/small-tokens.txt", language="pl", task="transcribe", num_threads=4)
    s, sr = sf.read(plik, dtype="float32")
    if sr != 16000:
        n = int(len(s) * 16000 / sr)
        s = np.interp(np.linspace(0, len(s) - 1, n), np.arange(len(s)), s).astype(np.float32)
    out = []
    for k in range(0, len(s), 16000 * 28):
        st = _asr.create_stream()
        st.accept_waveform(16000, s[k:k + 16000 * 28])
        _asr.decode_stream(st)
        out.append(st.result.text.strip())
    return " ".join(out)


def _slowa(t):
    return re.findall(r"[a-ząćęłńóśźż]+", t.lower())


def zgodnosc(a, b):
    """Udział słów tekstu a odnalezionych (w kolejności) w transkrypcji b – prosta miara zrozumiałości."""
    wa, wb = _slowa(a), _slowa(b)
    if not wa:
        return 1.0
    # najdłuższy wspólny podciąg słów
    n, m = len(wa), len(wb)
    dp = [0] * (m + 1)
    for i in range(1, n + 1):
        prev = 0
        for j in range(1, m + 1):
            cur = dp[j]
            dp[j] = prev + 1 if wa[i - 1] == wb[j - 1] else max(dp[j], dp[j - 1])
            prev = cur
    return dp[m] / n


def zgodnosc_tekstu(tekst, transkrypcja):
    """Zgodność po sprowadzeniu obu tekstów do słów (Whisper zapisuje liczby cyframi)."""
    return zgodnosc(normalizuj(tekst), normalizuj(transkrypcja.replace("x", " × ")))


def segmenty(nar):
    """Płaska lista (id, tekst) z pliku narracji."""
    out = []
    for k, v in nar.items():
        if k in ("zalety", "wady"):
            continue
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if v2:
                    out.append((f"{k}__{k2}", v2))
        elif isinstance(v, str) and v.strip():
            out.append((k, v))
    return out


def lektor_domu(pid, wersja, glos="gosia", sprawdz=True):
    src = os.path.join(HERE, "film", "narracja", f"v{wersja}", f"{pid}.json")
    nar = json.load(open(src, encoding="utf-8"))
    out = os.path.join(HERE, "out", "film", f"v{wersja}", pid, "lektor")
    os.makedirs(out, exist_ok=True)
    res = {}
    for sid, tekst in segmenty(nar):
        fn = os.path.join(out, f"{sid}.wav")
        dur = mow(tekst, fn, glos)
        r = dict(plik=f"lektor/{sid}.wav", czas=round(dur, 2), tekst=tekst)
        if sprawdz:
            tr = asr(fn)
            r["asr"] = tr
            r["zgodnosc"] = round(zgodnosc_tekstu(tekst, tr), 2)
        res[sid] = r
    json.dump(res, open(os.path.join(out, "lektor.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    slabe = {k: v for k, v in res.items() if v.get("zgodnosc", 1) < 0.8}
    tot = sum(v["czas"] for v in res.values())
    print(f"LEKTOR {pid} v{wersja}: {len(res)} nagrań, {tot:.0f} s" + (f", do poprawy: {list(slabe)}" if slabe else ""))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pid")
    ap.add_argument("--wersja", type=int, default=2)
    ap.add_argument("--glos", default="gosia")
    ap.add_argument("--bez-sprawdzania", action="store_true")
    a = ap.parse_args()
    lektor_domu(a.pid, a.wersja, a.glos, not a.bez_sprawdzania)
