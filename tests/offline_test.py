"""Offline test of the complete daily pipeline – no API keys needed.

The AI writer, the image review and the voice are simulated; everything else
(checks, repair loop, timing, rendering, sound, approval flow) runs for real.
    python tests/offline_test.py
"""
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import numpy as np                     # noqa: E402
from scipy.signal import resample_poly  # noqa: E402

import bot                             # noqa: E402
from engine import topics, voice, writer   # noqa: E402

EXAMPLE = open(os.path.join(ROOT, "episodes", "e012_projectile_motion.py"), encoding="utf-8").read()
calls = {"write": 0, "fix": 0, "review": 0, "tts": 0}
_misread = set()


def fake_ask(cfg, system, content, **kw):
    text = content if isinstance(content, str) else content[-1]["text"]
    if system == writer.REVIEW_SYSTEM:
        calls["review"] += 1
        if calls["review"] == 1:
            return '{"ok": false, "issues": ["Test: make the hook heading a little larger"]}'
        return '{"ok": true, "issues": []}'
    if text.startswith("Write episode"):
        calls["write"] += 1
        broken = EXAMPLE.replace("    c.ground(SGY)\n", "    c.ground(SGY)\n    if c.t > 2.0: undefined_name\n", 1)
        return "<plan>test</plan>\n```python\n" + broken + "```"
    calls["fix"] += 1
    return "```python\n" + EXAMPLE + "```"


def fake_tts(text, cfg, timeout=120):
    calls["tts"] += 1
    clip = voice.fake_clip(text, seed=len(text))
    pcm = (resample_poly(clip, 1, 2) * 32767 * 0.8).astype("<i2").tobytes()
    if text.startswith("We can split") and text not in _misread:   # one wrong reading -> must be retried
        _misread.add(text)
        return pcm, "Sure! Here is the line you asked for."
    return pcm, text


def main():
    writer.ask = fake_ask
    voice.realtime_tts = fake_tts
    bot.cfg.RESOLUTION, bot.cfg.FPS, bot.cfg.APPROVAL = "1080p", 30, "auto"
    state = open(topics.STATE, encoding="utf-8").read()
    topic, _, day = topics.next_topic()
    slug = bot.checks.slug(topic)
    cache = bot.CACHE
    bot.CACHE = os.path.join(ROOT, "build", "test_voice_cache")
    try:
        info = bot.cmd_daily()
        print(json.dumps(info, indent=1, ensure_ascii=False))
        print("calls:", calls)
        assert calls["fix"] >= 2, "repair loop + review fix should have run"
        assert calls["tts"] == 29, "the misread sentence should have been re-recorded once"
        assert os.path.exists(info["final_1080p"])
        print("OFFLINE TEST OK")
    finally:
        with open(topics.STATE, "w", encoding="utf-8") as fh:
            fh.write(state)
        bot.CACHE = cache
        ep = os.path.join(ROOT, "episodes", f"e{day:03d}_{slug}.py")
        if os.path.exists(ep):
            os.remove(ep)


if __name__ == "__main__":
    main()
