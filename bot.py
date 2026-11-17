#!/usr/bin/env python3
"""PHYSICS EVERY DAY – the daily physics explainer bot.

  python bot.py daily                      complete run (steps 1–6), e.g. every morning via cron
  python bot.py make "Topic"               steps 2–5 for one topic, without uploading
  python bot.py render episodes/FILE.py    render an existing episode (voice + 4K video)
        --preview      1080p instead of 4K (faster)
        --no-voice     without narration (subtitles + music only)
  python bot.py check episodes/FILE.py     run the automatic checks only
  python bot.py voice-test "Some text"     listen to VOICE / VOICE_STYLE from config.py
  python bot.py redo "change request"      revise the last video with your feedback
  python bot.py publish build/FOLDER       upload a finished video (after approval)
  python bot.py youtube-login              connect YouTube once

On GitHub the workflows in .github/workflows call these commands.
"""
import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
os.chdir(ROOT)


def load_env(path=os.path.join(ROOT, ".env")):
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env()
import config as cfg                                                    # noqa: E402
from engine import checks, publish, render, sound, timing, topics, voice, writer   # noqa: E402

CACHE = os.path.join(ROOT, "build", "voice_cache")


def log(msg):
    line = f"[{datetime.datetime.now():%H:%M:%S}] {msg}"
    print(line, flush=True)
    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    with open(os.path.join(ROOT, "logs", f"{datetime.date.today()}.log"), "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def prune_cache(days=4):
    if not os.path.isdir(CACHE):
        return
    limit = time.time() - days * 86400
    for f in os.listdir(CACHE):
        p = os.path.join(CACHE, f)
        if os.path.getmtime(p) < limit:
            os.remove(p)


def meta_for(ep, day):
    return {"channel": cfg.CHANNEL_NAME, "day": day, "topic": ep.TOPIC, "subtitles": cfg.SUBTITLES}


# ---------------------------------------------------------------- building blocks
def voice_clips(ep, mode):
    """mode: 'real' | 'fake' | 'none' -> (clips, secs)"""
    if mode == "none":
        return {}, {}
    lines = [(si, ki, say) for si, ki, say, _ in timing.narration(ep) if say]
    keyed = [(timing.clip_key(say, cfg), say) for _, _, say in lines]
    clips = voice.synthesize(keyed, cfg, CACHE, log=log, fake=(mode == "fake"))
    secs = {(si, ki): len(clips[timing.clip_key(say, cfg)]) / voice.SR for si, ki, say in lines}
    return clips, secs


def check_episode(path, day, voice_mode="none"):
    """All automatic checks. Returns (problems, episode, timeline, clips)."""
    with open(path, encoding="utf-8") as fh:
        problems = checks.scan_code(fh.read())
    if problems:
        return problems, None, None, {}
    try:
        ep = render.load_episode(path)
    except Exception:
        return ["The file fails on import:\n" + traceback.format_exc(limit=3)], None, None, {}
    problems = checks.episode_problems(ep, cfg)
    if problems:
        return problems, ep, None, {}
    clips, secs = voice_clips(ep, voice_mode)
    tl = timing.build(ep, cfg, secs)
    problems = checks.duration_problems(tl, cfg)
    try:
        crashes = render.dry_run(ep, tl, meta_for(ep, day))
        problems += crashes or render.layout_check(ep, tl, meta_for(ep, day))
    except Exception:
        problems.append("A draw function crashed:\n" + traceback.format_exc(limit=4))
    return problems, ep, tl, clips


def make_video(ep_path, day, out_dir, voice_mode="real", preview=False):
    """Steps 3 + 5: voice, timing, 4K render, sound, mux. Returns info dict."""
    os.makedirs(out_dir, exist_ok=True)
    ep = render.load_episode(ep_path)
    problems = checks.episode_problems(ep, cfg)
    if problems:
        raise SystemExit("Episode hat Fehler:\n- " + "\n- ".join(problems))
    clips, secs = voice_clips(ep, voice_mode)
    tl = timing.build(ep, cfg, secs)
    meta = meta_for(ep, day)
    tl_path, meta_path = os.path.join(out_dir, "timeline.json"), os.path.join(out_dir, "meta.json")
    with open(tl_path, "w") as fh:
        json.dump(tl, fh, ensure_ascii=False)
    with open(meta_path, "w") as fh:
        json.dump(meta, fh, ensure_ascii=False)
    issues = checks.duration_problems(tl, cfg) + render.layout_check(ep, tl, meta)
    for i in issues:
        log("  ⚠ " + i)
    scale = 1.0 if preview or cfg.RESOLUTION.lower() == "1080p" else 2.0
    log(f"Rendere Video: {int(1080 * scale)}×{int(1920 * scale)}, {cfg.FPS} fps, {tl['total']:.0f} s …")
    silent = os.path.join(out_dir, "video_silent.mp4")
    render.render_video(ep_path, tl_path, meta_path, silent, scale=scale, fps=cfg.FPS, crf=14 if scale > 1 else 16,
                        workers=cfg.WORKERS, log=log)
    log("Mische Ton (Stimme, Musik, Effekte) …")
    audio = sound.build(ep, tl, cfg, clips, os.path.join(out_dir, "audio.wav"), log)
    name = f"day{day:03d}_{checks.slug(ep.TOPIC)}"
    final = os.path.join(out_dir, f"{name}_{'4k' if scale > 1 else '1080p'}.mp4")
    render.mux(silent, audio, final)
    small = final if scale == 1.0 else None
    if scale > 1 and cfg.MAKE_1080P_COPY:
        small = render.downscale(final, os.path.join(out_dir, f"{name}_1080p.mp4"))
    with open(os.path.join(out_dir, "subtitles.srt"), "w", encoding="utf-8") as fh:
        fh.write(timing.srt(tl))
    for f in (silent, audio, os.path.join(out_dir, "audio_raw.wav")):
        if os.path.exists(f):
            os.remove(f)
    shutil.rmtree(os.path.join(out_dir, "chunks"), ignore_errors=True)
    info = {"day": day, "topic": ep.TOPIC, "title": ep.TITLE, "description": ep.DESCRIPTION,
            "tags": list(getattr(ep, "TAGS", [])), "duration": round(tl["total"], 1), "voice": voice_mode,
            "final_4k": final, "final_1080p": small, "issues": issues}
    with open(os.path.join(out_dir, "info.json"), "w", encoding="utf-8") as fh:
        json.dump(info, fh, indent=1, ensure_ascii=False)
    log(f"Fertig: {final}")
    return info


def review_sheets(ep, tl, meta, out_dir):
    times = render.sample_times(tl)
    if len(times) > 24:
        times = [times[round(i * (len(times) - 1) / 23)] for i in range(24)]
    paths = render.stills(ep, tl, meta, times, os.path.join(out_dir, "review"), scale=0.5, labels=True)
    return [render.contact_sheet(paths[i:i + 4], os.path.join(out_dir, "review", f"sheet_{i // 4}.png"), cols=2)
            for i in range(0, len(paths), 4)]


def develop(code, ep_path, day, out_dir):
    """Step 4: technical checks + repairs, real voice, visual review + improvements."""
    for rnd in range(cfg.REVIEW_ROUNDS + 1):
        for attempt in range(cfg.FIX_ATTEMPTS + 1):
            with open(ep_path, "w", encoding="utf-8") as fh:
                fh.write(code)
            problems, ep, tl, _ = check_episode(ep_path, day, "real")
            if not problems:
                break
            log(f"  {len(problems)} Problem(e) gefunden:")
            for p in problems[:8]:
                log("   - " + p.splitlines()[0])
            if attempt == cfg.FIX_ATTEMPTS:
                raise RuntimeError("Episode ist nach mehreren Reparaturversuchen noch fehlerhaft.")
            log("  KI repariert …")
            code = writer.fix_episode(cfg, code, problems)
        if rnd == cfg.REVIEW_ROUNDS:
            break
        log("  Bildprüfung durch die KI …")
        sheets = review_sheets(ep, tl, meta_for(ep, day), out_dir)
        lines = [(c["start"], c["text"]) for c in tl["clips"]]
        verdict = writer.review(cfg, code, sheets, lines, ep.FACTS)
        if verdict.get("ok"):
            log("  Bildprüfung bestanden ✓")
            break
        log(f"  Bildprüfung: {len(verdict['issues'])} Verbesserung(en):")
        for i in verdict["issues"][:8]:
            log("   - " + i)
        code = writer.fix_episode(cfg, code, verdict["issues"], reason="the visual review")
    return code


def approval_mode():
    mode = (os.environ.get("BOT_APPROVAL") or cfg.APPROVAL).lower()
    if mode == "github" and os.environ.get("GITHUB_ACTIONS") != "true":
        return "manual"                     # the GitHub links only exist inside GitHub Actions
    return mode


def out_dir_for(day, slug):
    if os.environ.get("GITHUB_ACTIONS") == "true":
        return os.path.join(ROOT, "build", "out")       # fixed folder -> uploaded as workflow artifact
    return os.path.join(ROOT, "build", f"day{day:03d}_{slug}")


def notify_review(info):
    """GitHub mode: the upload job in the same workflow run now waits for your approval."""
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    run = f"{server}/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    log(f"Video fertig: Tag {info['day']} – {info['title']} ({info['duration']:.0f} s)")
    log(f"Ansehen und freigeben: {run}")


def approve(info, out_dir):
    mode = approval_mode()
    if mode == "auto":
        return "approve", ""
    log(f"Video wartet auf dich: {info['final_4k']}")
    log(f"Veröffentlichen mit: python bot.py publish {os.path.relpath(out_dir, ROOT)}")
    return "manual", ""


# ---------------------------------------------------------------- commands
def cmd_daily(topic=None, upload=True):
    if topic:
        following, day = "", topics.load_state()["day"] + 1
    else:
        topic, following, day = topics.next_topic()
    slug = checks.slug(topic)
    out_dir = out_dir_for(day, slug)
    ep_path = os.path.join(ROOT, "episodes", f"e{day:03d}_{slug}.py")
    log(f"=== Tag {day}: {topic} ===")
    log("Schritt 2: KI schreibt Skript und Animation …")
    code = writer.write_episode(cfg, topic, following, day, topics.history())
    for redo in range(3):
        log("Schritt 4: Selbstkontrolle …")
        code = develop(code, ep_path, day, out_dir)
        log("Schritt 3+5: Stimme, Video und Ton …")
        info = make_video(ep_path, day, out_dir)
        if not upload:
            return info
        if approval_mode() == "github":
            topics.mark_done(topic, day)
            topics.set_pending({"day": day, "topic": topic, "episode": os.path.relpath(ep_path, ROOT),
                                "title": info["title"]})
            notify_review(info)
            return info
        decision, feedback = approve(info, out_dir)
        if decision != "redo":
            break
        log(f"Überarbeitung gewünscht: {feedback}")
        code = writer.revise_episode(cfg, code, feedback)
    topics.mark_done(topic, day)
    if decision == "approve":
        log("Schritt 6: Hochladen …")
        results = publish.publish_all(cfg, info, log)
        log(f"Tag {day} ist online: " + ", ".join(f"{k}: {v}" for k, v in results.items()))
    elif decision == "skip":
        log("Übersprungen – nichts hochgeladen.")
    return info


def cmd_redo(feedback):
    p = topics.get_pending()
    if not p:
        raise SystemExit("Es gibt kein Video, das überarbeitet werden kann.")
    if not (feedback or "").strip():
        raise SystemExit("Bitte einen Änderungswunsch angeben.")
    day, topic = p["day"], p["topic"]
    ep_path = os.path.join(ROOT, p["episode"])
    out_dir = out_dir_for(day, checks.slug(topic))
    log(f"=== Überarbeitung Tag {day}: {feedback} ===")
    with open(ep_path, encoding="utf-8") as fh:
        code = writer.revise_episode(cfg, fh.read(), feedback)
    code = develop(code, ep_path, day, out_dir)
    info = make_video(ep_path, day, out_dir)
    p["revisions"] = p.get("revisions", 0) + 1
    p.pop("published", None)
    topics.set_pending(p)
    if approval_mode() == "github":
        notify_review(info)
    return info


def cmd_publish(folder):
    with open(os.path.join(folder, "info.json"), encoding="utf-8") as fh:
        info = json.load(fh)
    for k in ("final_4k", "final_1080p"):                 # files may come from another machine (artifact)
        if info.get(k):
            local = os.path.join(folder, os.path.basename(info[k]))
            if os.path.exists(local):
                info[k] = local
    done = [e for e in topics.load_state().get("published", []) if e.get("day") == info["day"] and e.get("results")
            and not any(str(v).startswith("FEHLER") for v in e["results"].values())]
    if done:
        log(f"Tag {info['day']} ist schon veröffentlicht – nichts zu tun.")
        return done[-1]["results"]
    if not (cfg.UPLOAD_YOUTUBE or cfg.UPLOAD_INSTAGRAM or cfg.UPLOAD_TIKTOK):
        log("Keine Plattform eingeschaltet – in config.py UPLOAD_YOUTUBE / UPLOAD_INSTAGRAM / UPLOAD_TIKTOK setzen.")
    results = publish.publish_all(cfg, info, log)
    topics.mark_published(info["day"], results)
    for k, v in results.items():
        log(f"  {k}: {v}")
    if any(str(v).startswith("FEHLER") for v in results.values()):
        raise RuntimeError("Mindestens ein Upload ist fehlgeschlagen (Details oben).")
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["daily", "make", "redo", "render", "check", "voice-test", "publish",
                                        "youtube-login"])
    ap.add_argument("arg", nargs="?")
    ap.add_argument("--preview", action="store_true", help="1080p statt 4K")
    ap.add_argument("--no-voice", action="store_true", help="ohne Sprecher (nur Untertitel + Musik)")
    ap.add_argument("--fake-voice", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--day", type=int, default=None)
    a = ap.parse_args()
    try:
        if a.command in ("daily", "redo"):
            prune_cache()
        if a.command == "daily":
            cmd_daily()
        elif a.command == "make":
            cmd_daily(topic=a.arg, upload=False)
        elif a.command in ("render", "check"):
            path = a.arg
            ep = render.load_episode(path)
            stem = os.path.splitext(os.path.basename(path))[0]
            day = a.day or (int(stem[1:4]) if stem[:1] == "e" and stem[1:4].isdigit() else topics.load_state()["day"] + 1)
            mode = "none" if a.no_voice else "fake" if a.fake_voice else "real"
            if a.command == "check":
                problems, *_ = check_episode(path, day, mode)
                log("Keine Probleme ✓" if not problems else "Probleme:\n- " + "\n- ".join(problems))
            else:
                out = os.path.join(ROOT, "build", f"day{day:03d}_{checks.slug(ep.TOPIC)}" + ("_preview" if a.preview else ""))
                make_video(path, day, out, voice_mode=mode, preview=a.preview)
        elif a.command == "voice-test":
            text = a.arg or "Which angle throws a ball the farthest? Let's find out."
            out, transcript, score, secs = voice.voice_test(text, cfg)
            log(f"Gespeichert: {out} ({secs:.1f} s) · Stimme {cfg.VOICE} · {cfg.VOICE_MODEL}")
            log(f"Verstanden als: \"{transcript}\" ({'?' if score is None else f'{score:.0%}'} Übereinstimmung)")
            m4a = out[:-4] + ".m4a"
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", out, "-c:a", "aac", "-b:a", "192k", m4a],
                           check=True)
            log(f"Anhören: {m4a} (auf GitHub unter Artifacts zum Download)")
        elif a.command == "redo":
            cmd_redo(a.arg)
        elif a.command == "publish":
            print(json.dumps(cmd_publish(a.arg), indent=1, ensure_ascii=False))
        elif a.command == "youtube-login":
            publish.youtube_credentials(interactive=True)
            log("YouTube verbunden ✓")
    except Exception as e:
        log("FEHLER: " + "".join(traceback.format_exception_only(type(e), e)).strip())
        log(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
