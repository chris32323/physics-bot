"""Soundtrack: voice + music bed (ducked under the voice) + synced sound effects, loudness-normalised."""
import json
import math
import re
import subprocess

import numpy as np
from scipy.io import wavfile
from scipy.ndimage import maximum_filter1d
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

from .style import Timing

SR = 48000
SCALE = [440.0, 523.25, 587.33, 659.25, 783.99, 880.0, 1046.5, 1174.66, 1318.51, 1567.98]  # A minor pentatonic
BEAT = 0.625             # 96 bpm
EIGHTH = BEAT / 2
CH = 5.0                 # one chord = 2 bars
CHORDS = [([220.00, 261.63, 329.63, 440.00], 110.00),   # Am
          ([174.61, 220.00, 261.63, 349.23], 87.31),    # F
          ([196.00, 261.63, 329.63, 392.00], 130.81),   # C
          ([196.00, 246.94, 293.66, 392.00], 98.00)]    # G


def _t(n):
    return np.arange(n) / SR


# ---------------------------------------------------------------- instruments
def soft_saw(f, n, det, rng):
    x, s = _t(n), np.zeros(n)
    for h in range(1, 9):
        s += np.sin(2 * np.pi * f * h * (1 + det) * x + rng.uniform(0, 2 * np.pi)) / h ** 1.5
    return s


def pluck(f, dur=1.0):
    n = int(dur * SR); x = _t(n)
    s = (np.sin(2 * np.pi * f * x) + 0.28 * np.sin(4 * np.pi * f * x) * np.exp(-x * 7)
         + 0.10 * np.sin(6 * np.pi * f * x) * np.exp(-x * 11))
    return s * np.minimum(x / 0.003, 1) * np.exp(-x * 5.0)


def marimba(f, dur=1.2):
    n = int(dur * SR); x = _t(n)
    s = (np.sin(2 * np.pi * f * x) * np.exp(-x * 4.5) + 0.25 * np.sin(8 * np.pi * f * x) * np.exp(-x * 14)
         + 0.06 * np.sin(20 * np.pi * f * x) * np.exp(-x * 30))
    return s * np.minimum(x / 0.0015, 1)


def bell(f, dur=2.6):
    n = int(dur * SR); x = _t(n); s = np.zeros(n)
    for r, a, d in [(1, 1.0, 1.6), (2.0, 0.35, 1.1), (3.0, 0.16, 0.7), (4.2, 0.07, 0.45), (5.4, 0.04, 0.3)]:
        s += a * np.sin(2 * np.pi * f * r * x) * np.exp(-x / d)
    return s * np.minimum(x / 0.002, 1)


def bass_note(f, dur=1.2):
    n = int(dur * SR); x = _t(n)
    return (np.sin(2 * np.pi * f * x) + 0.25 * np.sin(4 * np.pi * f * x)) * np.minimum(x / 0.01, 1) * np.exp(-x * 2.2)


def kick():
    n = int(0.4 * SR); x = _t(n)
    f = 48 + 90 * np.exp(-x * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 8) * np.minimum(x / 0.001, 1)


def hat(rng):
    n = int(0.06 * SR); x = _t(n)
    return sosfilt(butter(2, 7000, "high", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-x * 70)


def thud(rng):
    n = int(0.3 * SR); x = _t(n)
    f = 70 + 60 * np.exp(-x * 40)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-x * 14)
    click = sosfilt(butter(2, [800, 4000], "band", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-x * 120)
    return body + 0.3 * click


def tick(rng):
    n = int(0.05 * SR); x = _t(n)
    return sosfilt(butter(2, [2500, 6000], "band", fs=SR, output="sos"), rng.standard_normal(n)) * np.exp(-x * 90)


def whoosh(dur=1.0, seed=1):
    n = int(dur * SR); x = _t(n) / dur
    noise = np.random.default_rng(seed).standard_normal(n)
    out = np.zeros(n)
    bands = np.geomspace(300, 3200, 10)
    for k, fc in enumerate(bands):
        sos = butter(2, [fc / 1.25, min(fc * 1.25, SR / 2 - 100)], btype="band", fs=SR, output="sos")
        out += sosfilt(sos, noise) * np.exp(-((x - (0.15 + 0.6 * k / (len(bands) - 1))) / 0.2) ** 2)
    out *= np.sin(np.pi * x) ** 1.2
    out /= np.abs(out).max()
    a = (-0.7 + 1.4 * x + 1) / 4 * np.pi                 # sweeps left -> right with the throw
    return out * np.cos(a), out * np.sin(a)


# ---------------------------------------------------------------- placement helpers
def _put(bus, sig, t, pan=0.0, gain=1.0):
    i = int(round(t * SR))
    if i < 0 or i >= bus.shape[1]:
        return
    n = min(len(sig), bus.shape[1] - i)
    a = (pan + 1) / 4 * math.pi
    bus[0, i:i + n] += sig[:n] * gain * math.cos(a)
    bus[1, i:i + n] += sig[:n] * gain * math.sin(a)


def _put2(bus, l, r, t, gain=1.0):
    i = int(round(t * SR))
    if i < 0 or i >= bus.shape[1]:
        return
    n = min(len(l), bus.shape[1] - i)
    bus[0, i:i + n] += l[:n] * gain
    bus[1, i:i + n] += r[:n] * gain


def _reverb(bus, wet, seed=3, sec=2.4, rt=1.9):
    n = int(sec * SR); x = _t(n)
    rng = np.random.default_rng(seed)
    lp = butter(2, 4500, "low", fs=SR, output="sos")
    out = bus.copy()
    for c in range(2):
        ir = sosfilt(lp, rng.standard_normal(n) * np.exp(-6.9 * x / rt))
        ir = np.concatenate([np.zeros(int(0.02 * SR)), ir])
        ir /= np.sqrt((ir ** 2).sum())
        out[c] += wet * fftconvolve(bus[c], ir)[:bus.shape[1]]
    return out


def _rms(x):
    return math.sqrt(float(np.mean(x ** 2))) + 1e-12


# ---------------------------------------------------------------- music
def music(total, level=1.0, seed=7):
    rng = np.random.default_rng(seed)
    N = int(math.ceil(total * SR))
    pad, mus = np.zeros((2, N)), np.zeros((2, N))
    for k in range(int(math.ceil(total / CH))):
        notes, _ = CHORDS[k % 4]
        n = int((CH + 1.6) * SR); x = _t(n)
        env = np.minimum(x / 1.4, 1) * np.clip((CH + 1.6 - x) / 1.6, 0, 1)
        for f in notes:
            l, r = soft_saw(f, n, -0.003, rng) * env, soft_saw(f, n, 0.003, rng) * env
            _put2(pad, l, r, k * CH, gain=0.045)
    pad = sosfilt(butter(2, 1700, "low", fs=SR, output="sos"), pad, axis=1)
    pattern = [0, 1, 2, 3, 2, 1, 2, 1]
    step, t = 0, 0.0
    while t < total - 1.0:
        notes, _ = CHORDS[int(t // CH) % 4]
        _put(mus, pluck(notes[pattern[step % 8]] * 2), t, pan=0.3 if step % 2 else -0.3, gain=0.035)
        step += 1
        t += EIGHTH
    t = 0.0
    while t < total - 2.0:
        _, b = CHORDS[int(t // CH) % 4]
        _put(mus, bass_note(b), t, gain=0.12)
        _put(mus, kick(), t, gain=0.15)
        for e in (EIGHTH, BEAT + EIGHTH):
            _put(mus, hat(rng), t + e, pan=0.25, gain=0.022)
        t += 2 * BEAT
    bed = _reverb(pad + mus, 0.28)
    bed *= 10 ** (-31 / 20) / _rms(bed) * level          # bed sits ~11 dB under the voice
    return bed


# ---------------------------------------------------------------- sound effects
def events(episode, tl):
    out = []
    for sc, info in zip(episode.SCENES, tl["scenes"]):
        base = info["start"]
        for ki, st in enumerate(sc.steps):
            for e in st.sfx:
                out.append((e[0], base + info["cues"][ki] + e[1], e[2] if len(e) > 2 else {}))
        if sc.sounds:
            for e in sc.sounds(Timing(0.0, info)):
                out.append((e[0], base + e[1], e[2] if len(e) > 2 else {}))
    return out


def sfx_bus(evts, N, log=print):
    rng = np.random.default_rng(11)
    bus = np.zeros((2, N))
    for i, (name, t, opts) in enumerate(evts):
        n = opts.get("n")
        pan = opts.get("pan", 0.0)
        if name == "whoosh":
            l, r = whoosh(seed=i + 1)
            _put2(bus, l, r, t, gain=0.16)
        elif name == "pop":
            _put(bus, pluck(SCALE[5 if n is None else n], 0.7), t, pan, 0.07)
        elif name == "note":
            _put(bus, marimba(SCALE[0 if n is None else n]), t, pan, 0.07)
        elif name == "chime":
            k = 2 if n is None else n
            _put(bus, bell(SCALE[k]), t, pan - 0.15, 0.08)
            _put(bus, bell(SCALE[min(k + 2, len(SCALE) - 1)]), t + 0.12, pan + 0.15, 0.08)
        elif name == "land":
            _put(bus, thud(rng), t, pan, 0.15)
            if n is not None:
                _put(bus, marimba(SCALE[n]), t, pan, 0.07)
        elif name == "tick":
            _put(bus, tick(rng), t, pan, 0.05)
        else:
            log(f"  Hinweis: unbekannter Soundeffekt '{name}' ignoriert")
    return _reverb(bus, 0.38, seed=5)


# ---------------------------------------------------------------- mix
def _duck(voice, depth=0.55):
    a = math.exp(-1 / (0.04 * SR))
    db = 10 * np.log10(lfilter([1 - a], [1, -a], voice * voice) + 1e-12)
    on = np.clip((db + 45) / 15, 0, 1)
    on = maximum_filter1d(on, size=int(0.25 * SR))
    r = math.exp(-1 / (0.12 * SR))
    on = lfilter([1 - r], [1, -r], on)
    return 1 - depth * on


def loudnorm(src, dst, target):
    af = f"loudnorm=I={target}:TP=-1.0:LRA=11"
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af", af + ":print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(re.findall(r"\{[^{}]*\}", p.stderr)[-1])
    af2 = (f"{af}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
           f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", af2, "-ar", str(SR), "-c:a", "pcm_s24le",
                    dst], check=True)
    return float(m["input_i"])


def build(episode, tl, cfg, clips, out_wav, log=print):
    """clips: {key: float32 voice clip at 48 kHz} (empty dict = no voice, e.g. preview)."""
    total = tl["total"]
    N = int(math.ceil(total * SR))
    voice = np.zeros(N)
    for c in tl["clips"]:
        clip = clips.get(c["key"])
        if clip is None:
            continue
        i = int(round(c["start"] * SR))
        n = min(len(clip), N - i)
        voice[i:i + n] += clip[:n]
    has_voice = bool(np.any(voice))
    mix = np.vstack([voice, voice])
    if cfg.MUSIC:
        bed = music(total, cfg.MUSIC_LEVEL)
        mix += bed * (_duck(voice) if has_voice else 1.0)
    if cfg.SFX:
        mix += sfx_bus(events(episode, tl), N, log)
    mix = sosfilt(butter(2, 30, "high", fs=SR, output="sos"), mix, axis=1)
    x = _t(N)
    mix *= np.minimum(x / 0.15, 1) * np.clip((total - x) / 1.5, 0, 1)
    mix *= 0.5 / (np.abs(mix).max() + 1e-9)
    raw = out_wav[:-4] + "_raw.wav"
    wavfile.write(raw, SR, mix.T.astype(np.float32))
    target = cfg.TARGET_LUFS if has_voice else -20
    loudnorm(raw, out_wav, target)
    return out_wav
