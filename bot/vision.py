"""AI image check (OpenAI vision): is the sight really visible, does a sign give the answer away, is the photo usable?

Only used when OPENAI_API_KEY is set (and VISION_CHECK is not "0"). If the API fails, the bot simply
continues without the check, so a post is never lost because of it.
"""
import base64, io, json, os
import numpy as np
import requests
from PIL import Image
from .safety import redact

VISION_MODEL = os.getenv("VISION_MODEL", "gpt-5-mini")
ENABLED = bool(os.getenv("OPENAI_API_KEY")) and os.getenv("VISION_CHECK", "1") != "0"
MAX_CHECKS = int(os.getenv("VISION_MAX_CHECKS", "4"))      # panoramas checked per location at most


def _views(pano):
    """Four 90° views (front/right/back/left) from the middle band of the equirectangular panorama."""
    h, w = pano.shape[:2]
    band = pano[int(h * 0.22): int(h * 0.72)]
    out = []
    for k in range(4):
        x0 = int((k * 0.25 - 0.125) * w)
        cols = np.arange(x0, x0 + w // 4) % w
        im = Image.fromarray(band[:, cols]).convert("RGB")
        im.thumbnail((768, 768))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=80)
        out.append(base64.b64encode(buf.getvalue()).decode())
    return out


def check(pano, place, kind):
    """Return dict(usable, sight_visible, spoiler, reason) or None if the check could not run."""
    if not ENABLED:
        return None
    sight = kind in ("landmark", "landscape", "border")
    task = (f"These are four views (front, right, back, left) from one 360° street-level photo taken near: {place}.\n"
            "Answer ONLY with JSON: "
            '{"usable": true/false, "sight_visible": true/false/null, "spoiler": true/false, "reason": "max 12 words"}\n'
            "- usable = false if the photo is indoors, very dark, blurry, mostly blocked (car interior, wall, tunnel) or broken.\n"
            "- spoiler = true if readable text (signs, shop names) clearly reveals the city or exact place.\n"
            + (f"- sight_visible = true if {place} itself is clearly visible in at least one view, otherwise false.\n" if sight
               else "- sight_visible = null.\n"))
    content = [{"type": "text", "text": task}] + [
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b}", "detail": "low"}} for b in _views(pano)]
    try:
        r = requests.post("https://api.openai.com/v1/chat/completions",
                          headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"},
                          json=dict(model=VISION_MODEL, messages=[{"role": "user", "content": content}],
                                    response_format={"type": "json_object"}, max_completion_tokens=2000),
                          timeout=120)
        if r.status_code != 200:
            print(redact(f"  AI check unavailable (HTTP {r.status_code}: {r.text[:200]}) - continuing without it"))
            return None
        txt = r.json()["choices"][0]["message"]["content"] or "{}"
        res = json.loads(txt)
        return dict(usable=bool(res.get("usable", True)), sight_visible=res.get("sight_visible"),
                    spoiler=bool(res.get("spoiler", False)), reason=str(res.get("reason", ""))[:120])
    except Exception as e:
        print(redact(f"  AI check failed ({e}) - continuing without it"))
        return None
