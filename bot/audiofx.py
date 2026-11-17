"""Sound polish with ffmpeg (free, runs on the GitHub runner, a few seconds per reel).

Voice track:  rumble filter -> warmth (more depth) -> less harsh highs -> de-esser
              -> gentle compression ("radio voice") -> tiny room reverb -> limiter
Each line:    10 ms fade in/out (no clicks between sentences)
Final mix:    loudness normalised to -14 LUFS (Instagram/TikTok level), peaks max -1.5 dB

Variables (optional):  AUDIO_FX=0 switches everything off
                       AUDIO_WARMTH  bass boost in dB (default 3, 0 = none, 5 = very deep)
                       AUDIO_REVERB  room amount 0..0.3 (default 0.08, 0 = dry)
"""
import os, subprocess, tempfile, wave
from pathlib import Path
import numpy as np

ENABLED = (os.getenv("AUDIO_FX") or "1") != "0"
WARMTH = float(os.getenv("AUDIO_WARMTH") or 3)
REVERB = min(max(float(os.getenv("AUDIO_REVERB") or 0.08), 0.0), 0.3)
SR = 44100


def fade(clip, ms=10):
    """Soft start/end of a line so joints never click."""
    n = min(int(SR * ms / 1000), len(clip) // 4)
    if n < 2: return clip
    c = clip.copy(); r = np.linspace(0, 1, n, dtype=np.float32)
    c[:n] *= r; c[-n:] *= r[::-1]
    return c


def _write(path, a):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(a, -1, 1) * 32000).astype(np.int16).tobytes())


def _read(path, n):
    with wave.open(str(path), "rb") as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32000
    return a[:n] if len(a) >= n else np.pad(a, (0, n - len(a)))      # keep exact length = keep timing


def _ffmpeg(a, chain):
    with tempfile.TemporaryDirectory() as d:
        src, dst = Path(d) / "in.wav", Path(d) / "out.wav"
        _write(src, a)
        r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af", chain,
                            "-ar", str(SR), "-ac", "1", "-c:a", "pcm_s16le", str(dst)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip()[-300:])
        return _read(dst, len(a))


def voice_chain(deesser=True):
    f = ["highpass=f=75"]                                                   # remove rumble / pops
    if WARMTH > 0: f.append(f"bass=g={WARMTH:g}:f=140:w=0.7")               # warmth / depth
    f.append("equalizer=f=3200:t=q:w=1.4:g=-2")                             # less shrill
    if deesser: f.append("deesser=i=0.4:m=0.5:f=0.5:s=o")                  # softer "s" sounds
    f.append("acompressor=threshold=-20dB:ratio=3:attack=8:release=150:makeup=2")   # even, "radio" voice
    if REVERB > 0:
        f.append(f"aecho=1.0:1.0:28|47:{REVERB:.3f}|{REVERB * 0.6:.3f}")  # tiny room, not a hall
    f.append("alimiter=limit=0.95:attack=5:release=50:level=disabled:latency=1")
    return ",".join(f)


def polish_voice(voice):
    """Voice-only track (whole reel timeline) -> polished track of the same length."""
    if not ENABLED or not np.any(voice):
        return voice
    for deesser in (True, False):                     # older ffmpeg builds may lack the de-esser
        try:
            out = _ffmpeg(voice, voice_chain(deesser))
            print(f"  audio fx: voice polished (warmth {WARMTH:g} dB, reverb {REVERB:g}"
                  f"{'' if deesser else ', no de-esser'})")
            return out
        except Exception as e:
            err = str(e)
    print(f"WARNING: audio fx skipped ({err[:150]})")
    return voice


def master(mix):
    """Final mix -> broadcast loudness (-14 LUFS) with safe peaks."""
    if not ENABLED:
        return np.clip(mix, -1, 1)
    try:
        out = _ffmpeg(np.clip(mix, -1, 1), "loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100,alimiter=limit=0.82:level=disabled:latency=1")
        print("  audio fx: loudness -14 LUFS")
        return out
    except Exception as e:
        print(f"WARNING: loudness normalisation skipped ({str(e)[:150]})")
        return np.clip(mix, -1, 1)
