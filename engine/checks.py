"""Checks for AI-written episodes: code safety net, structure and narration rules."""
import ast
import re
import string

ALLOWED_FROM = {"engine.style", "math", "textwrap"}
ALLOWED_IMPORT = {"math", "numpy", "textwrap"}
FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "globals", "locals", "vars", "input",
                   "breakpoint", "getattr", "setattr", "delattr", "help", "exit", "quit", "memoryview"}
FORBIDDEN_ATTRS = {"system", "popen", "remove", "unlink", "rmtree", "savefig", "save", "savez", "savez_compressed",
                   "load", "fromfile", "tofile", "loadtxt", "savetxt", "genfromtxt", "memmap", "ctypeslib", "f2py",
                   "DataSource", "lib", "testing"}
SYMBOLS_NOT_SPOKEN = "₀₁₂²³αβγθωπΔ√=≈≤≥·×÷→∞°"


def scan_code(src):
    """Static safety net: episode files may only compute and draw."""
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [f"SyntaxError in line {e.lineno}: {e.msg}"]
    problems = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORT:
                    problems.append(f"line {node.lineno}: import of '{a.name}' is not allowed")
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "") not in ALLOWED_FROM:
                problems.append(f"line {node.lineno}: import from '{node.module}' is not allowed")
        elif isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            problems.append(f"line {node.lineno}: use of '{node.id}' is not allowed")
        elif isinstance(node, ast.Attribute) and (node.attr in FORBIDDEN_ATTRS or node.attr.startswith("__")):
            problems.append(f"line {node.lineno}: attribute '.{node.attr}' is not allowed")
    return problems


def episode_problems(ep, cfg):
    """Structure + narration rules (after the module was imported)."""
    from .style import Scene, Step
    p = []
    for name in ("TOPIC", "TITLE", "DESCRIPTION", "TEASER", "FACTS", "SCENES"):
        if not hasattr(ep, name):
            p.append(f"missing module variable {name}")
    if p:
        return p
    if not isinstance(ep.FACTS, dict):
        p.append("FACTS must be a dict of strings")
    if not ep.SCENES or not all(isinstance(s, Scene) for s in ep.SCENES):
        return p + ["SCENES must be a non-empty list of Scene(...)"]
    fields = set()
    for si, sc in enumerate(ep.SCENES):
        if not callable(sc.draw):
            p.append(f"scene {si + 1}: draw is not a function")
        if not sc.steps or not all(isinstance(s, Step) for s in sc.steps):
            p.append(f"scene {si + 1}: steps must be a non-empty list of Step(...)")
            continue
        for ki, st in enumerate(sc.steps):
            for label, text in (("say", st.say), ("sub", st.sub)):
                if not text:
                    continue
                names = {f[1] for f in string.Formatter().parse(text) if f[1]}
                fields |= names
                missing = [n for n in names if n not in ep.FACTS]
                if missing:
                    p.append(f"scene {si + 1} step {ki + 1}: {label} uses unknown FACTS {missing}")
            say = st.say or ""
            bad = [ch for ch in SYMBOLS_NOT_SPOKEN if ch in say]
            if bad:
                p.append(f"scene {si + 1} step {ki + 1}: say contains symbols {bad} – write them out in words in "
                         f"`say` (e.g. 'v zero', 'alpha', 'squared') and put symbols into `sub`")
            if len(say.split()) > 26:
                p.append(f"scene {si + 1} step {ki + 1}: sentence too long ({len(say.split())} words, max 26)")
            for e in st.sfx:
                if not (isinstance(e, tuple) and len(e) >= 2 and isinstance(e[0], str)):
                    p.append(f"scene {si + 1} step {ki + 1}: sfx entries must look like ('whoosh', 0.2)")
    if not str(ep.TEASER).strip():
        p.append("TEASER is empty")
    return p


def duration_problems(tl, cfg):
    if tl["total"] > cfg.MAX_DURATION:
        return [f"video is {tl['total']:.0f}s long, limit is {cfg.MAX_DURATION}s – shorten the narration"]
    return []


def slug(text):
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40] or "episode"
