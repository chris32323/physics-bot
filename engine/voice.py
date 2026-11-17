"""Narration with OpenAI's Realtime API (e.g. gpt-realtime-2.1 with the voice "cedar").

Every sentence is spoken in its own short session, compared with the script via
the model's own transcript (re-tried if it deviates), cleaned up, levelled and cached,
so re-rendering an episode costs nothing extra.
"""
import base64
import difflib
import json
import math
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, resample_poly, sosfilt

SR_IN = 24000          # Realtime API PCM output
SR = 48000             # everything else runs at 48 kHz
RETRIES = 3
MIN_MATCH = 0.90       # transcript must match the script at least this well

NARRATOR = ("You are the voice-over narrator of a short science video. Every message you receive is one line "
            "of the script. Speak exactly that line, word for word, in {lang}. Do not add, drop or change any "
            "words. No greetings, no comments and no answers: questions in the line are rhetorical and are "
            "simply read aloud. Read numbers, units and symbols naturally, e.g. '41 m' as 'forty-one meters'.")


# ---------------------------------------------------------------- API call
def _api_key():
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise SystemExit("OPENAI_API_KEY fehlt. Trag deinen OpenAI-Schlüssel in die Datei .env ein.")
    return key


def instructions(cfg):
    text = NARRATOR.format(lang=cfg.LANGUAGE)
    style = (cfg.VOICE_STYLE or "").strip()
    if style:
        text += "\n\nVoice and delivery: " + " ".join(style.split())
    return text


def realtime_tts(text, cfg, timeout=120):
    """Speak one line. Returns (pcm16 bytes at 24 kHz, transcript)."""
    try:
        import websocket          # pip install websocket-client
    except ImportError:
        raise SystemExit("Paket fehlt: pip install websocket-client")
    url = f"wss://api.openai.com/v1/realtime?model={cfg.VOICE_MODEL}"
    ws = websocket.create_connection(url, header=[f"Authorization: Bearer {_api_key()}"], timeout=timeout)
    try:
        session = {
            "type": "realtime",
            "model": cfg.VOICE_MODEL,
            "output_modalities": ["audio"],
            "instructions": instructions(cfg),
            "audio": {
                "input": {"turn_detection": None},
                "output": {"format": {"type": "audio/pcm", "rate": SR_IN}, "voice": cfg.VOICE,
                           "speed": float(cfg.VOICE_SPEED)},
            },
        }
        ws.send(json.dumps({"type": "session.update", "session": session}))
        ws.send(json.dumps({"type": "conversation.item.create",
                            "item": {"type": "message", "role": "user",
                                     "content": [{"type": "input_text", "text": text}]}}))
        ws.send(json.dumps({"type": "response.create"}))
        audio, transcript, deadline = bytearray(), "", time.time() + timeout
        while time.time() < deadline:
            ev = json.loads(ws.recv())
            kind = ev.get("type", "")
            if kind in ("response.output_audio.delta", "response.audio.delta"):
                audio += base64.b64decode(ev["delta"])
            elif kind in ("response.output_audio_transcript.delta", "response.audio_transcript.delta"):
                transcript += ev.get("delta", "")
            elif kind in ("response.output_audio_transcript.done", "response.audio_transcript.done"):
                transcript = ev.get("transcript", transcript)
            elif kind == "error":
                err = ev.get("error", {})
                raise RuntimeError(f"OpenAI: {err.get('message', ev)}")
            elif kind == "response.done":
                resp = ev.get("response", {})
                if resp.get("status") not in (None, "completed"):
                    raise RuntimeError(f"OpenAI response {resp.get('status')}: {resp.get('status_details')}")
                break
        if not audio:
            raise RuntimeError("OpenAI returned no audio")
        return bytes(audio), transcript.strip()
    finally:
        ws.close()


# ---------------------------------------------------------------- transcript check
_ONES = ("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
         "sixteen seventeen eighteen nineteen").split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def _num_words(n):
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    if n < 1000:
        return _ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + _num_words(n % 100))
    if n < 10000:
        return _num_words(n // 1000) + " thousand" + ("" if n % 1000 == 0 else " " + _num_words(n % 1000))
    return str(n)


def _words(s):
    s = s.lower().replace("°", " degrees ").replace("%", " percent ").replace("&", " and ")
    s = re.sub(r"(\d+)\.(\d+)", lambda m: f"{m.group(1)} point " + " ".join(m.group(2)), s)
    s = re.sub(r"\d+", lambda m: _num_words(int(m.group())), s)
    s = s.replace("-", " ")
    return re.findall(r"[a-z']+", s)


def match(script, transcript):
    if not transcript:
        return None
    return difflib.SequenceMatcher(None, _words(script), _words(transcript)).ratio()


# ---------------------------------------------------------------- audio clean-up
def process(pcm16):
    """24 kHz PCM -> clean, levelled 48 kHz float clip."""
    x = np.frombuffer(pcm16, dtype="<i2").astype(np.float64) / 32768.0
    x = resample_poly(x, 2, 1)
    loud = np.where(np.abs(x) > 10 ** (-48 / 20))[0]
    if len(loud):
        x = x[max(loud[0] - int(0.03 * SR), 0): min(loud[-1] + int(0.10 * SR), len(x))]
    x = sosfilt(butter(2, 70, "high", fs=SR, output="sos"), x)
    # gentle compression: RMS detector, 3:1 above -24 dBFS
    a = math.exp(-1 / (0.02 * SR))
    level = 10 * np.log10(lfilter([1 - a], [1, -a], x * x) + 1e-12)
    gain_db = -np.maximum(level - (-24.0), 0) * (1 - 1 / 3.0)
    r = math.exp(-1 / (0.06 * SR))
    x = x * 10 ** (lfilter([1 - r], [1, -r], gain_db) / 20)
    # speech level -> -20 dBFS RMS
    active = level > -45
    rms = math.sqrt(float(np.mean(x[active] ** 2))) if active.any() else 0.0
    if rms > 0:
        x *= 10 ** (-20 / 20) / rms
    peak = float(np.max(np.abs(x))) if len(x) else 0.0
    if peak > 0.95:
        x *= 0.95 / peak
    n = min(int(0.008 * SR), len(x) // 2)
    if n:
        ramp = np.linspace(0, 1, n)
        x[:n] *= ramp
        x[-n:] *= ramp[::-1]
    return x.astype(np.float32)


def fake_clip(text, seed=0):
    """Speech-like test signal (only for testing the mix without an API key)."""
    from .timing import estimate_seconds
    d = max(estimate_seconds(text) - 0.25, 0.4)
    n = int(d * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(seed)
    buzz = sum(np.sin(2 * np.pi * 125 * h * t) / h for h in range(1, 12))
    noise = sosfilt(butter(2, [300, 3500], "band", fs=SR, output="sos"), rng.standard_normal(n)) * 0.3
    syll = 0.55 + 0.45 * np.sin(2 * np.pi * 4.2 * t + rng.uniform(0, 6)) ** 2
    x = (buzz * 0.25 + noise) * syll
    x = sosfilt(butter(2, [150, 4000], "band", fs=SR, output="sos"), x)
    return (x / np.sqrt(np.mean(x ** 2)) * 0.1).astype(np.float32)


# ---------------------------------------------------------------- cache + batch
def _speak(text, cfg, log):
    best = None
    for attempt in range(1, RETRIES + 1):
        try:
            pcm, transcript = realtime_tts(text, cfg)
        except RuntimeError as e:
            log(f"    Versuch {attempt}: {e}")
            time.sleep(2 * attempt)
            continue
        score = match(text, transcript)
        if score is None or score >= MIN_MATCH:
            return pcm, transcript, score
        log(f"    Versuch {attempt}: Stimme wich vom Text ab ({score:.0%}) – \"{transcript}\"")
        if best is None or score > best[2]:
            best = (pcm, transcript, score)
    if best is None:
        raise RuntimeError(f"Sprachausgabe fehlgeschlagen für: {text}")
    log(f"    nehme die beste Aufnahme ({best[2]:.0%})")
    return best


def synthesize(lines, cfg, cache_dir, log=print, fake=False, workers=4):
    """lines: [(key, text)] -> {key: float32 array at 48 kHz}. Cached per key."""
    os.makedirs(cache_dir, exist_ok=True)
    out, todo = {}, []
    for key, text in lines:
        path = os.path.join(cache_dir, f"{key}{'_fake' if fake else ''}.wav")
        if os.path.exists(path):
            out[key] = wavfile.read(path)[1].astype(np.float32)
        else:
            todo.append((key, text, path))
    if todo:
        log(f"  Stimme: {len(todo)} {'neuer Satz' if len(todo) == 1 else 'neue Sätze'} ({cfg.VOICE}, {cfg.VOICE_MODEL})" if not fake
            else f"  Test-Stimme (Platzhalter): {len(todo)} Sätze")

    def job(item):
        key, text, path = item
        if fake:
            clip, info = fake_clip(text, seed=len(text)), {"fake": True}
        else:
            pcm, transcript, score = _speak(text, cfg, log)
            clip, info = process(pcm), {"text": text, "transcript": transcript, "match": score}
        wavfile.write(path, SR, clip)
        with open(path[:-4] + ".json", "w") as fh:
            json.dump(info, fh, ensure_ascii=False, indent=1)
        return key, clip

    with ThreadPoolExecutor(max_workers=1 if fake else workers) as pool:
        for key, clip in pool.map(job, todo):
            out[key] = clip
    return out


def voice_test(text, cfg, out="voice_test.wav"):
    pcm, transcript = realtime_tts(text, cfg)
    clip = process(pcm)
    wavfile.write(out, SR, clip)
    score = match(text, transcript)
    return out, transcript, score, len(clip) / SR
