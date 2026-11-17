"""Voice-first timeline: every step lasts as long as its sentence (+ breathing room)."""
import hashlib
import itertools
import math
import re

WORDS_PER_SEC = 2.55          # used only when no real voice clip exists yet (preview / planning)


def fill(text, facts):
    return text.format(**facts) if text else text


def estimate_seconds(text):
    words = len(re.findall(r"[\w'’.-]+", text or ""))
    return words / WORDS_PER_SEC + 0.25 if words else 0.0


def clip_key(text, cfg):
    raw = "|".join([text, cfg.VOICE, cfg.VOICE_MODEL, cfg.VOICE_STYLE.strip(), str(cfg.VOICE_SPEED)])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def narration(episode):
    """All spoken lines: list of (scene_index, step_index, say_text, subtitle_text)."""
    facts = getattr(episode, "FACTS", {})
    out = []
    for si, sc in enumerate(episode.SCENES):
        for ki, st in enumerate(sc.steps):
            say = fill(st.say, facts).strip()
            sub = fill(st.sub, facts).strip() if st.sub else say
            out.append((si, ki, say, sub))
    return out


def _punct_bonus(part):
    return 120 if part[-1] in ".!?;:" else 70 if part[-1] in ",—–" else 0


def _two_lines(text, line_chars=36):
    """One line if it fits, otherwise two lines split near the middle (preferably at punctuation)."""
    if len(text) <= line_chars:
        return text
    words = text.split()
    best = None
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        cost = (len(a) - len(b)) ** 2 - _punct_bonus(a) / 3
        if best is None or cost < best[0]:
            best = (cost, a + "\n" + b)
    return best[1]


def _chunks(text, max_chars=66):
    """Split a sentence into evenly sized subtitle chunks, preferably at punctuation."""
    words = text.split()
    k = min(max(1, math.ceil(len(text) / max_chars)), len(words))
    if k == 1:
        return [_two_lines(text)]
    target = len(text) / k
    best = None
    for cuts in itertools.combinations(range(1, len(words)), k - 1):
        bounds = (0,) + cuts + (len(words),)
        parts = [" ".join(words[a:b]) for a, b in zip(bounds, bounds[1:])]
        if any(len(p) > max_chars + 8 for p in parts):
            continue
        cost = sum((len(p) - target) ** 2 for p in parts) - sum(_punct_bonus(p) for p in parts[:-1])
        if best is None or cost < best[0]:
            best = (cost, parts)
    parts = best[1] if best else [text]
    return [_two_lines(p) for p in parts]


def build(episode, cfg, clip_secs=None):
    """clip_secs: {(scene, step): seconds of real audio}. Missing entries are estimated."""
    clip_secs = clip_secs or {}
    lines = {(si, ki): (say, sub) for si, ki, say, sub in narration(episode)}
    scenes, subs, clips = [], [], []
    g = 0.0
    n = len(episode.SCENES)
    for si, sc in enumerate(episode.SCENES):
        lead = sc.lead if sc.lead is not None else (0.35 if si == 0 else cfg.SCENE_LEAD)
        tail = sc.tail if sc.tail is not None else (1.4 if si == n - 1 else cfg.SCENE_TAIL)
        t = lead
        cues, durs, voice = [], [], []
        for ki, st in enumerate(sc.steps):
            say, sub = lines[(si, ki)]
            if say:
                d = clip_secs.get((si, ki))
                d = estimate_seconds(say) if d is None else d
                length = max(d + cfg.SENTENCE_GAP + st.pause, st.min)
                voice.append([t, t + d])
                clips.append({"scene": si, "step": ki, "start": g + t, "secs": d, "text": say,
                              "key": clip_key(say, cfg)})
                parts = _chunks(sub)
                total_chars = sum(len(p) for p in parts)
                a = g + t
                for p in parts:
                    b = a + d * len(p) / total_chars
                    subs.append([a, b, p])
                    a = b
            else:
                length = max(st.pause, st.min, 0.3)
                voice.append(None)
            cues.append(t)
            durs.append(length)
            t += length
        dur = t + tail
        scenes.append({"start": g, "duration": dur, "cues": cues, "durs": durs, "voice": voice,
                       "header": sc.header})
        g += dur
    # let each subtitle stay a little after the sentence, but never overlap the next one
    for i, s in enumerate(subs):
        nxt = subs[i + 1][0] if i + 1 < len(subs) else g
        s[1] = min(s[1] + 0.35, nxt - 0.02)
    return {"total": g, "scenes": scenes, "subs": subs, "clips": clips}


def srt(timeline):
    def ts(x):
        h, r = divmod(x, 3600)
        m, s = divmod(r, 60)
        return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")
    out = []
    for i, (a, b, text) in enumerate(timeline["subs"], 1):
        out.append(f"{i}\n{ts(a)} --> {ts(b)}\n{text}\n")
    return "\n".join(out)
