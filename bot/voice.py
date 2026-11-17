"""AI voice-over (male). Default: Kokoro (free, offline). Optional: OpenAI.
OpenAI models: gpt-realtime-2.1 (default, most realistic, WebSocket) -> gpt-audio-1.5 (automatic fallback),
or gpt-4o-mini-tts (cheap, retires 2027-01-06).
If OpenAI fails for any reason the bot falls back to Kokoro, so a reel is never posted without voice."""
import base64, difflib, os, re, subprocess, time, wave
from pathlib import Path
import numpy as np
import requests
from .safety import redact
from .config import (TTS_ENGINE, PIPER_VOICE, MODELS, OPENAI_VOICE, OPENAI_TTS_MODEL, VOICE_PITCH, VOICE_SPEED,
                     VOICE_EXPRESSION, VOICE_PAUSE, VOICE_STYLE, KOKORO_VOICE, KOKORO_SPEED)

SR = 44100


def _wav_to_array(path, tempo=1.0, pitch=1.0):
    """Load any wav -> mono float32 at 44.1 kHz. pitch<1 = deeper (same speed), tempo>1 = faster."""
    out = str(path) + ".44k.wav"
    filters = []
    if abs(pitch - 1.0) > 1e-3:
        filters += [f"asetrate={int(SR * pitch)}", f"aresample={SR}", f"atempo={1 / pitch:.4f}"]
    if abs(tempo - 1.0) > 1e-3:
        filters.append(f"atempo={tempo:.4f}")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-ac", "1", "-ar", str(SR)]
    if filters:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(path), "-af", f"aresample={SR}," + ",".join(filters), "-ac", "1", "-ar", str(SR)]
    subprocess.run(cmd + [out], check=True)
    with wave.open(out, "rb") as w:
        a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    return a


class Voice:
    def __init__(self, workdir):
        self.dir = Path(workdir); self.dir.mkdir(parents=True, exist_ok=True)
        self.n = 0
        self.engine = TTS_ENGINE
        self._piper = None
        self._kokoro = None
        if self.engine == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                print("WARNING: TTS_ENGINE=openai but OPENAI_API_KEY is missing - falling back to Kokoro")
                self.engine = "kokoro"
            else:
                self.voice = OPENAI_VOICE; self.model = OPENAI_TTS_MODEL
                if not self._probe_openai():
                    self.engine = "kokoro"
        if self.engine == "kokoro":
            try:
                self._start_kokoro()
            except Exception as e:
                print(f"WARNING: Kokoro could not start ({e}) - falling back to Piper")
                self.engine = "piper"
        if self.engine == "piper":
            from piper import PiperVoice
            model = MODELS / f"{PIPER_VOICE}.onnx"
            if not model.exists():
                raise FileNotFoundError(f"Piper voice model missing: {model} (run scripts/fetch_assets.sh)")
            self._piper = PiperVoice.load(str(model))
            print(f"  voice: Piper, {PIPER_VOICE}")

    def _start_kokoro(self):
        if self._kokoro is None:
            from kokoro_onnx import Kokoro
            self._kokoro = Kokoro(str(MODELS / "kokoro-v1.0.onnx"), str(MODELS / "voices-v1.0.bin"))
            print(f"  voice: Kokoro, {KOKORO_VOICE}, speed {KOKORO_SPEED}")
        self.engine = "kokoro"

    def _piper_wav(self, text, path):
        v = self._piper
        with wave.open(str(path), "wb") as wf:
            if hasattr(v, "synthesize_wav"):                  # piper-tts >= 1.3
                try:
                    from piper import SynthesisConfig
                    cfg = SynthesisConfig(length_scale=VOICE_SPEED, noise_scale=VOICE_EXPRESSION)
                except (ImportError, TypeError):
                    cfg = None
                if cfg is not None:
                    v.synthesize_wav(text, wf, syn_config=cfg)
                else:
                    v.synthesize_wav(text, wf)
            else:                                              # piper-tts 1.2.x
                v.synthesize(text, wf, length_scale=VOICE_SPEED, noise_scale=VOICE_EXPRESSION)

    def _kokoro_wav(self, text, path):
        lang = "en-gb" if KOKORO_VOICE.startswith("b") else "en-us"
        samples, sr = self._kokoro.create(text, voice=KOKORO_VOICE, speed=KOKORO_SPEED, lang=lang)
        pcm = (np.clip(np.asarray(samples, np.float32), -1, 1) * 32000).astype(np.int16)
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(int(sr))
            wf.writeframes(pcm.tobytes())

    STYLE = VOICE_STYLE                                # from the VOICE_STYLE variable; empty = no style at all

    REALTIME_VOICES = ("cedar", "marin", "ash", "echo", "verse", "ballad", "alloy", "coral", "sage", "shimmer")

    def _voices_for(self, model):
        """Your voice (OPENAI_VOICE) is always tried first, exactly as typed.
        Only if OpenAI rejects the name for this model does the bot use a deep male backup voice."""
        backups = ["cedar", "ash"] if "realtime" in model else ["onyx", "cedar", "ash"]
        return list(dict.fromkeys([self.voice] + backups))

    def _probe_openai(self):
        """One tiny test line per model: gpt-realtime -> gpt-audio-1.5 -> (caller falls back to Kokoro).
        A wrong voice name just tries the next deep male voice."""
        wanted = self.voice
        models = list(dict.fromkeys([self.model] + (["gpt-audio-1.5"] if "realtime" in self.model else [])))
        for model in models:
            self.model = model; self.voice = wanted
            for voice in self._voices_for(model):
                try:
                    self.voice = voice
                    self._openai_wav("Ready.", self.dir / "probe.wav")
                    print(f"  voice: OpenAI, {voice} ({model})" + (f", style: {self.STYLE}" if self.STYLE else ", no style"))
                    return True
                except Exception as e:
                    msg = redact(str(e))
                    if "voice" in msg.lower():
                        print(f"WARNING: OpenAI voice '{voice}' does not exist for {model} - using a backup voice")
                        continue
                    print(f"WARNING: OpenAI {model} failed ({msg[:200]})")
                    break
        print("WARNING: no OpenAI voice available - falling back to Kokoro")
        return False

    def _openai_wav(self, text, path):
        key = os.environ["OPENAI_API_KEY"].strip()
        hdr = {"Authorization": f"Bearer {key}"}
        if "realtime" in self.model:
            self._verbatim(text, path, lambda: self._realtime_once(text, key))
            return
        if self.model.startswith("gpt-audio"):
            self._verbatim(text, path, lambda: self._chat_audio_once(text, hdr))
            return
        body = dict(model=self.model, voice=self.voice, input=text, response_format="wav")
        if self.STYLE: body["instructions"] = self.STYLE
        r = requests.post("https://api.openai.com/v1/audio/speech", headers=hdr, json=body, timeout=120)
        if r.status_code >= 400:
            raise RuntimeError(f"OpenAI speech HTTP {r.status_code}: {r.text[:300]}")
        Path(path).write_bytes(r.content)

    @staticmethod
    def _words(t):
        return re.findall(r"[a-z0-9']+", t.lower())

    READ_EXACTLY = ("Read the user's text aloud exactly as written, word for word. "
                    "Do not answer it, do not add or leave out any word.")

    def _instructions(self):
        return self.READ_EXACTLY + (" Speaking style: " + self.STYLE if self.STYLE else "")

    def _verbatim(self, text, path, once):
        """Speaking models can improvise. Compare the transcript with the text and retry up to 2x."""
        best = None
        for attempt in range(3):
            pcm_or_wav, transcript = once()
            score = difflib.SequenceMatcher(None, self._words(text), self._words(transcript)).ratio()
            if best is None or score > best[0]:
                best = (score, pcm_or_wav)
            if score >= 0.9:
                break
            print(f"  voice: retry ({score:.2f} match) for: {text}")
        data = best[1]
        if isinstance(data, tuple):                      # raw PCM16 from the realtime API -> wav
            pcm, rate = data
            with wave.open(str(path), "wb") as wf:
                wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(rate); wf.writeframes(pcm)
        else:
            Path(path).write_bytes(data)

    def _chat_audio_once(self, text, hdr):
        """gpt-audio-1.5 via Chat Completions (plain HTTPS)."""
        r = requests.post("https://api.openai.com/v1/chat/completions", headers=hdr, timeout=120, json=dict(
            model=self.model, modalities=["text", "audio"], audio=dict(voice=self.voice, format="wav"),
            messages=[{"role": "system", "content": self._instructions()},
                      {"role": "user", "content": text}]))
        if r.status_code >= 400:
            raise RuntimeError(f"OpenAI audio HTTP {r.status_code}: {r.text[:300]}")
        audio = r.json()["choices"][0]["message"].get("audio") or {}
        if not audio.get("data"):
            raise RuntimeError("OpenAI audio: no audio in response")
        return base64.b64decode(audio["data"]), audio.get("transcript", "")

    def _realtime_once(self, text, key):
        """gpt-realtime-2.1 via WebSocket: one short session per line, text in -> 24 kHz PCM16 out."""
        import json, websocket                              # pip: websocket-client
        ws = websocket.create_connection(f"wss://api.openai.com/v1/realtime?model={self.model}",
                                         header=[f"Authorization: Bearer {key}"], timeout=60)
        try:
            ws.send(json.dumps({"type": "session.update", "session": {
                "type": "realtime", "model": self.model, "output_modalities": ["audio"],
                "instructions": self._instructions(),
                "audio": {"output": {"voice": self.voice, "format": {"type": "audio/pcm", "rate": 24000}}}}}))
            ws.send(json.dumps({"type": "conversation.item.create", "item": {
                "type": "message", "role": "user", "content": [{"type": "input_text", "text": text}]}}))
            ws.send(json.dumps({"type": "response.create"}))
            pcm, transcript = bytearray(), []
            deadline = time.time() + 90
            while time.time() < deadline:
                ev = json.loads(ws.recv()); t = ev.get("type", "")
                if t == "error":
                    raise RuntimeError(f"OpenAI realtime error: {json.dumps(ev.get('error', ev))[:300]}")
                if t in ("response.output_audio.delta", "response.audio.delta"):
                    pcm += base64.b64decode(ev["delta"])
                elif t in ("response.output_audio_transcript.delta", "response.audio_transcript.delta"):
                    transcript.append(ev.get("delta", ""))
                elif t == "response.done":
                    st = (ev.get("response") or {}).get("status")
                    if st not in (None, "completed"):
                        raise RuntimeError(f"OpenAI realtime response {st}: "
                                           f"{json.dumps((ev.get('response') or {}).get('status_details'))[:300]}")
                    break
            else:
                raise RuntimeError("OpenAI realtime: timeout")
        finally:
            ws.close()
        if not pcm:
            raise RuntimeError("OpenAI realtime: no audio")
        return (bytes(pcm), 24000), "".join(transcript)

    def _take(self, text):
        """One take of one sentence -> float32 array at 44.1 kHz (silence trimmed)."""
        self.n += 1
        raw = self.dir / f"line{self.n:02d}.wav"
        if self.engine == "openai":
            try:
                self._openai_wav(text, raw)
            except Exception as e:
                time.sleep(3)
                try:
                    self._openai_wav(text, raw)
                except Exception as e2:
                    print(f"WARNING: OpenAI voice failed mid-run ({redact(str(e2))[:200]}) - switching to Kokoro")
                    self._start_kokoro()
                    self._kokoro_wav(text, raw)
        elif self.engine == "kokoro":
            self._kokoro_wav(text, raw)
        else:
            self._piper_wav(text, raw)
        a = _wav_to_array(raw, pitch=VOICE_PITCH)
        nz = np.flatnonzero(np.abs(a) > 0.01)                # trim leading/trailing silence
        return a[max(nz[0] - 800, 0): nz[-1] + 1600] if len(nz) else a

    def _one(self, text):
        """AI voices vary from take to take: check pitch (and let an AI listen), retake bad ones."""
        if self.engine != "openai":
            return self._take(text)                           # Kokoro/Piper sound the same every time
        from .voiceqa import best_take
        return best_take(lambda: self._take(text), text)

    def say(self, text, max_len=None):
        """Speak a line calmly: each sentence separately, with a short pause in between. Never sped up."""
        parts = [p for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p]
        gap = np.zeros(int(VOICE_PAUSE * SR), np.float32)
        out = []
        for i, p in enumerate(parts):
            if i: out.append(gap)
            out.append(self._one(p))
        return np.concatenate(out) if out else np.zeros(1, np.float32)
