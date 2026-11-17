"""Steps 2 + 4: the AI (OpenAI GPT by default) writes script + animation code, repairs problems
and reviews the stills."""
import base64
import json
import os
import re
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.anthropic.com/v1/messages"
EXAMPLE = os.path.join(ROOT, "episodes", "e012_projectile_motion.py")

REVIEW_SYSTEM = """You are the strict quality reviewer of a physics explainer channel (vertical video).
You get a contact sheet of stills in time order (each labelled with its time), the narration with
timestamps, the FACTS and the episode code. Check:
1. Physics: is every statement and number correct? Are assumptions stated where needed?
2. Visual ↔ narration: does the picture show what is being said at that moment?
3. Legibility: overlapping or cut-off text, cramped areas, text too small, anything inside the
   subtitle band (y 392–548) or the bottom app zone (y < 380), important text at the far right.
4. Pacing: does each idea get enough time? Is anything rushed?
5. Hook and clarity: would a curious 15-year-old follow it?
Reply ONLY with JSON: {"ok": true|false, "issues": ["concrete, actionable fix", ...]}.
Set ok=false only for problems a viewer would notice or for physics errors."""


def _openai_key():
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise SystemExit("OPENAI_API_KEY fehlt (Datei .env bzw. GitHub-Secret).")
    return key


def _anthropic_key():
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY fehlt (Datei .env bzw. GitHub-Secret).")
    return key


def _post(url, headers, body, retries=4):
    for attempt in range(retries):
        try:
            r = requests.post(url, headers=headers, json=body, timeout=900)
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise RuntimeError(f"KI nicht erreichbar: {e}")
            time.sleep(15 * (attempt + 1))
            continue
        if r.status_code in (429, 500, 502, 503, 529):
            time.sleep(15 * (attempt + 1))
            continue
        if r.status_code != 200:
            raise RuntimeError(f"KI-API {r.status_code}: {r.text[:500]}")
        return r.json()
    raise RuntimeError("KI-API nicht erreichbar (mehrere Versuche)")


def _openai_content(content):
    """Internal message blocks -> OpenAI Responses API input parts."""
    if isinstance(content, str):
        return [{"type": "input_text", "text": content}]
    parts = []
    for b in content:
        if b["type"] == "text":
            parts.append({"type": "input_text", "text": b["text"]})
        elif b["type"] == "image":
            src = b["source"]
            parts.append({"type": "input_image", "detail": "high",
                          "image_url": f"data:{src['media_type']};base64,{src['data']}"})
    return parts


def ask(cfg, system, content, max_tokens=None):
    """One request to the configured AI (OpenAI GPT by default, optionally Anthropic Claude)."""
    provider = getattr(cfg, "WRITER_PROVIDER", "openai").lower()
    if provider == "openai":
        body = {"model": cfg.WRITER_MODEL, "instructions": system,
                "input": [{"role": "user", "content": _openai_content(content)}],
                "max_output_tokens": max_tokens or 48000,          # includes the model's reasoning
                "reasoning": {"effort": getattr(cfg, "WRITER_EFFORT", "medium")}}
        data = _post("https://api.openai.com/v1/responses",
                     {"Authorization": f"Bearer {_openai_key()}", "Content-Type": "application/json"}, body)
        if data.get("status") == "incomplete":
            raise RuntimeError(f"OpenAI-Antwort unvollständig: {data.get('incomplete_details')}")
        text = "".join(part.get("text", "") for item in data.get("output", []) if item.get("type") == "message"
                       for part in item.get("content", []) if part.get("type") == "output_text")
        return text or data.get("output_text", "")
    body = {"model": cfg.WRITER_MODEL, "max_tokens": max_tokens or 16000, "system": system,
            "messages": [{"role": "user", "content": content}]}
    data = _post(API, {"x-api-key": _anthropic_key(), "anthropic-version": "2023-06-01",
                       "content-type": "application/json"}, body)
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


def _code(text):
    blocks = re.findall(r"```python\s*\n(.*?)```", text, flags=re.S)
    if not blocks:
        raise RuntimeError("Die KI hat keinen Python-Code geliefert")
    return blocks[-1].strip() + "\n"


def _system(cfg):
    with open(os.path.join(ROOT, "prompts", "writer_guide.md"), encoding="utf-8") as fh:
        guide = fh.read().replace("{LANGUAGE}", cfg.LANGUAGE)
    with open(EXAMPLE, encoding="utf-8") as fh:
        example = fh.read()
    return (guide + "\n\n# Reference episode\n\nA complete, finished episode. Match its quality, pacing, "
            "structure and code style – but invent visuals that fit the new topic.\n\n```python\n" + example + "```\n")


def write_episode(cfg, topic, teaser_topic, day, done):
    prompt = (f"Write episode {day}.\n\nTopic of today: {topic}\n"
              f"Tomorrow's topic (turn it into the TEASER question): {teaser_topic or 'choose a fitting next topic'}\n"
              f"Already covered (don't repeat them): {', '.join(done[-20:]) or 'none'}\n")
    return _code(ask(cfg, _system(cfg), prompt))


def fix_episode(cfg, code, problems, reason="automatic checks", history=None):
    prompt = (f"The episode below has problems found by {reason}. Fix all of them and keep everything "
              f"else as it is. Reply with the complete corrected file in one ```python block.\n\n"
              "Problems:\n" + "\n".join(f"- {p}" for p in problems))
    if history:
        prompt += ("\n\nIMPORTANT – earlier fix attempts did not solve this; texts were only moved onto other "
                   "texts. Earlier reports:\n" + "\n".join(f"- {p}" for p in history[-12:]) +
                   "\nMake a structural fix instead of nudging: give every text item its own row with at least "
                   "25 units of empty space to its neighbours (check all items of that scene together, also the "
                   "ones from earlier steps that are still visible), fade out an old item before a new one "
                   "appears in the same place, or use smaller fonts / fewer items on screen.")
    prompt += "\n\nCurrent file:\n```python\n" + code + "```"
    return _code(ask(cfg, _system(cfg), prompt))


def revise_episode(cfg, code, feedback):
    return fix_episode(cfg, code, [f"Feedback from the channel owner: {feedback}"], reason="the channel owner")


def review(cfg, code, sheets, narration_lines, facts):
    content = []
    for path in sheets:
        with open(path, "rb") as fh:
            content.append({"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                                        "data": base64.b64encode(fh.read()).decode()}})
    text = ("Narration (start time, sentence):\n" + "\n".join(f"{t:6.1f}s  {s}" for t, s in narration_lines)
            + f"\n\nFACTS: {json.dumps(facts, ensure_ascii=False)}\n\nEpisode code:\n```python\n{code}```")
    content.append({"type": "text", "text": text})
    reply = ask(cfg, REVIEW_SYSTEM, content, max_tokens=20000)
    m = re.search(r"\{.*\}", reply, flags=re.S)
    if not m:
        return {"ok": True, "issues": [], "raw": reply}
    try:
        verdict = json.loads(m.group(0))
    except json.JSONDecodeError:
        return {"ok": True, "issues": [], "raw": reply}
    verdict.setdefault("issues", [])
    return verdict
