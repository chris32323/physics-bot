"""Entry point.

  python -m bot.main render  --out out            # pick locations, fetch real panoramas, voice, render reel
  python -m bot.main render  --out out --demo     # offline test with synthetic panoramas (no tokens needed)
  python -m bot.main publish --out out --video-url URL
  python -m bot.main refresh-token                # prints a refreshed Instagram token
"""
import argparse, json, random, sys, datetime as dt
from pathlib import Path
import numpy as np
from . import config

HISTORY = config.DATA / "history.json"
LOCATIONS = config.DATA / "locations.json"

def intro_for(slot, n):
    if slot == 0:
        return ("ROUND 1", "WHERE ARE WE?", config.TITLE_EDITION)
    if n >= 3 and slot == n - 1:
        return ("FINAL ROUND", "LAST CHANCE!", "Only the pros get this one")
    return (f"ROUND {slot + 1}", "STILL IN?", "It gets harder now")

SAY_INTRO = ["Where are we?", "Still in?", "Final round!"]
SAY_PAN1 = ["Can you find it?", "This one is tricky.", "Last one!"]   # no location hints
GENERIC_HINTS = ["Watch the road.", "Look at the signs.", "Check the plants.", "Look at the houses.", "Which side do they drive on?"]

# Round 1 is always a well-known sight (more landscapes than city landmarks).
# Later rounds: 50 % sights (landscapes, lesser-known landmarks, border points), 50 % normal streets.
ROUND1_WEIGHTS = {"landscape": 0.6, "landmark": 0.4}
LATER_SIGHT_WEIGHTS = {"landscape": 0.5, "landmark": 0.25, "border": 0.25}


def load_json(p, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def available_locations(history):
    locs = load_json(LOCATIONS, [])
    used = set()
    for post in history.get("posted", [])[-60:]:
        used.update(post.get("location_ids", []))
    dead = set(history.get("no_coverage", []))
    fresh = [l for l in locs if l["id"] not in used and l["id"] not in dead]
    return fresh or [l for l in locs if l["id"] not in dead]


def weighted_order(rng, locs, weights):
    """Random order where higher-weighted types tend to come first; types with weight 0 are dropped."""
    keyed = [(rng.random() ** (1 / weights[l["type"]]), l) for l in locs if weights.get(l.get("type"), 0) > 0]
    return [l for _, l in sorted(keyed, key=lambda t: -t[0])]


def candidates_for(slot, rng, pool):
    if slot == 0:
        easy = [l for l in pool if l.get("difficulty") in ("easy", "medium")]
        first = weighted_order(rng, easy, ROUND1_WEIGHTS)
        return first + weighted_order(rng, pool, ROUND1_WEIGHTS)          # fallbacks: any difficulty
    harder = [l for l in pool if l.get("difficulty") in ("medium", "hard")]
    if rng.random() < 0.5:
        primary = weighted_order(rng, harder, {"street": 1.0})
        backup = weighted_order(rng, harder, LATER_SIGHT_WEIGHTS)
    else:
        primary = weighted_order(rng, harder, LATER_SIGHT_WEIGHTS)
        backup = weighted_order(rng, harder, {"street": 1.0})
    return primary + backup + weighted_order(rng, pool, {"street": 1, "landscape": 1, "landmark": 1, "border": 1})


def build_rounds(n, rng, history, demo=False):
    rounds = []; pool = available_locations(history); tried = set()
    if demo:
        from PIL import Image
        demo_panos = sorted(Path(config.ROOT / "demo").glob("*.jpg"))
    for slot in range(n):
        for loc in candidates_for(slot, rng, pool):
            if loc["id"] in tried: continue
            tried.add(loc["id"])
            kind = loc.get("type", "street")
            print(f"round {slot + 1}: trying {loc['name']}, {loc['country']} ({kind}, {loc['difficulty']})")
            if demo:
                pano = np.array(Image.open(demo_panos[slot % len(demo_panos)]).convert("RGB"))[:, ::-1].copy()
                meta = dict(id="demo", creator="demo", lon=loc["lon"], lat=loc["lat"], url="")
            else:
                from .mapillary import fetch_panorama, NoPanorama
                try:
                    pano, meta = fetch_panorama(loc["lon"], loc["lat"], rng, kind=kind,
                                                place=f"{loc['name']}, {loc['country']}")
                except NoPanorama as e:
                    print(f"  {e}"); history.setdefault("no_coverage", []).append(loc["id"]); continue
            fact = (loc.get("fact") or "").strip()
            reveal = loc.get("reveal") or f"This is {loc.get('say') or loc['name']}."
            if slot == 0: reveal += " Did you get it right?"
            rounds.append(dict(
                pano=pano, lonlat=(loc["lon"], loc["lat"]) if kind != "street" else (meta["lon"], meta["lat"]),
                place=loc["name"] if loc["country"] in loc["name"] else f"{loc['name']}, {loc['country']}",
                fact=fact, loc_id=loc["id"], intro=intro_for(slot, n),
                lines=dict(intro=SAY_INTRO[min(slot, 2)], pan1=SAY_PAN1[min(slot, 2)], reveal=reveal),
                credit="Imagery: Mapillary · CC BY-SA 4.0",
                meta=meta))
            break
        else:
            raise RuntimeError("ran out of locations with usable panoramas")
    return rounds


def make_caption(rounds):
    from .safety import clean_username
    creators = sorted({clean_username(r["meta"].get("creator")) for r in rounds
                       if r["meta"].get("creator") and r["meta"]["creator"] != "demo"} - {""})
    links = " ".join(r["meta"]["url"] for r in rounds if r["meta"].get("url"))
    return (f"Where are we? 🌍 {len(rounds)} rounds – guess before the timer runs out!\n\n"
            f"How many did you get right? Comment your score 👇 New round every day.\n\n"
            f"Street-level imagery: Mapillary contributors{(' (' + ', '.join(creators) + ')') if creators else ''}, "
            f"CC BY-SA 4.0. {links}\nMap data: Natural Earth.\n\n{config.HASHTAGS}")


BOT_VERSION = "2026-11-17m (voice check + ffmpeg sound polish)"


def cmd_render(args):
    print(f"geobot version {BOT_VERSION}")
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    seed = args.seed if args.seed is not None else int(dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d"))
    rng = random.Random(seed)
    history = load_json(HISTORY, {"posted": [], "no_coverage": []})
    rounds = build_rounds(config.ROUNDS_PER_REEL, rng, history, demo=args.demo)
    tts = None
    try:
        if args.fake_voice:
            from .render import SR
            tts = lambda text, mx: (0.15 * np.sin(2 * np.pi * 180 * np.arange(int(len(text) * 0.065 * SR)) / SR)).astype(np.float32)
        else:
            from .voice import Voice
            v = Voice(out / "voice"); tts = v.say
    except Exception as e:
        if config.REQUIRE_VOICE and not args.demo:
            raise
        print(f"WARNING: voice disabled ({e})")
    from .worldmap import WorldMap
    from .render import Reel
    print("rendering world map ..."); world = WorldMap()
    reel = Reel(world, rounds, tts=tts)
    print("rendering video ..."); reel.render(out / "reel.mp4", str(out))
    (out / "caption.txt").write_text(make_caption(rounds), encoding="utf-8")
    meta = dict(date=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), seed=seed,
                location_ids=[r["loc_id"] for r in rounds], places=[r["place"] for r in rounds],
                images=[r["meta"] for r in rounds])
    (out / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    HISTORY.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")   # no_coverage updates
    print("done:", out / "reel.mp4")


def cmd_publish(args):
    from .instagram import publish_reel
    out = Path(args.out)
    caption = (out / "caption.txt").read_text(encoding="utf-8")
    meta = json.loads((out / "meta.json").read_text(encoding="utf-8"))
    mid, link = publish_reel(args.video_url, caption)
    print("published:", mid, link or "")
    history = load_json(HISTORY, {"posted": [], "no_coverage": []})
    history["posted"].append(dict(date=meta["date"], media_id=mid, permalink=link,
                                  location_ids=meta["location_ids"], places=meta["places"]))
    HISTORY.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")


def cmd_refresh(_):
    from .instagram import refresh_token
    tok, exp = refresh_token()
    print(tok)


def main(argv=None):
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render"); r.add_argument("--out", default="out"); r.add_argument("--demo", action="store_true")
    r.add_argument("--fake-voice", action="store_true"); r.add_argument("--seed", type=int)
    p = sub.add_parser("publish"); p.add_argument("--out", default="out"); p.add_argument("--video-url", required=True)
    sub.add_parser("refresh-token")
    a = ap.parse_args(argv)
    {"render": cmd_render, "publish": cmd_publish, "refresh-token": cmd_refresh}[a.cmd](a)


if __name__ == "__main__":
    main()
