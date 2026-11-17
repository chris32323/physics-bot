"""Step 1: pick the topic of the day from topics.txt (and remember what was done)."""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOPICS = os.path.join(ROOT, "topics.txt")
STATE = os.path.join(ROOT, "state.json")


def load_state():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    return {"day": 0, "done": []}


def save_state(state):
    with open(STATE, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=1, ensure_ascii=False)


def all_topics():
    with open(TOPICS, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip() and not ln.lstrip().startswith("#")]


def next_topic():
    """Returns (topic, following_topic, day)."""
    state = load_state()
    open_ = [t for t in all_topics() if t not in state["done"]]
    if not open_:
        raise SystemExit("topics.txt ist leer bzw. alles erledigt – bitte neue Themen eintragen.")
    following = open_[1] if len(open_) > 1 else ""
    return open_[0], following, state["day"] + 1


def mark_done(topic, day):
    state = load_state()
    if topic not in state["done"]:
        state["done"].append(topic)
    state["day"] = max(state["day"], day)
    save_state(state)


def history(n=30):
    return load_state()["done"][-n:]


def set_pending(entry):
    """The video that waits for approval (GitHub mode)."""
    state = load_state()
    state["pending"] = entry
    save_state(state)


def get_pending():
    return load_state().get("pending")


def mark_published(day, results):
    state = load_state()
    p = state.get("pending") or {}
    if p.get("day") == day:
        p["published"] = results
        state["pending"] = p
    state.setdefault("published", []).append({"day": day, "results": results})
    save_state(state)
