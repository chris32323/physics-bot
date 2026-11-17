"""Step 6: uploads to YouTube, Instagram and TikTok (approval happens on GitHub)."""
import base64
import json
import math
import os
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRETS = os.path.join(ROOT, "secrets")


def _env(name):
    v = os.environ.get(name, "").strip()
    if not v:
        raise SystemExit(f"{name} fehlt in der Datei .env")
    return v


# ---------------------------------------------------------------- GitHub secrets (rotating tokens)
def update_github_secret(name, value, log=print):
    """Stores a renewed token as GitHub secret (needs GH_SECRETS_TOKEN, a token with 'Secrets: write')."""
    token, repo = os.environ.get("GH_SECRETS_TOKEN", "").strip(), os.environ.get("GITHUB_REPOSITORY", "")
    if not (token and repo):
        return False
    try:
        from nacl import encoding, public
        h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        key = requests.get(f"https://api.github.com/repos/{repo}/actions/secrets/public-key", headers=h,
                           timeout=30).json()
        box = public.SealedBox(public.PublicKey(key["key"].encode(), encoding.Base64Encoder()))
        enc = base64.b64encode(box.encrypt(value.encode())).decode()
        r = requests.put(f"https://api.github.com/repos/{repo}/actions/secrets/{name}", headers=h, timeout=30,
                         json={"encrypted_value": enc, "key_id": key["key_id"]})
        ok = r.status_code in (201, 204)
        log(f"  GitHub-Secret {name} {'aktualisiert' if ok else f'NICHT aktualisiert ({r.status_code})'}")
        return ok
    except Exception as e:
        log(f"  GitHub-Secret {name} konnte nicht aktualisiert werden: {e}")
        return False


# ---------------------------------------------------------------- YouTube
YT_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def youtube_credentials(interactive=False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    token = os.path.join(SECRETS, "youtube_token.json")
    if not os.path.exists(token) and os.environ.get("YOUTUBE_TOKEN_JSON", "").strip():
        os.makedirs(SECRETS, exist_ok=True)                       # GitHub: token comes from a secret
        with open(token, "w") as fh:
            fh.write(os.environ["YOUTUBE_TOKEN_JSON"])
    creds = Credentials.from_authorized_user_file(token, YT_SCOPES) if os.path.exists(token) else None
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif interactive:
        from google_auth_oauthlib.flow import InstalledAppFlow
        flow = InstalledAppFlow.from_client_secrets_file(os.path.join(SECRETS, "client_secret.json"), YT_SCOPES)
        creds = flow.run_local_server(port=0)
    else:
        raise SystemExit("YouTube ist noch nicht verbunden: einmal 'python bot.py youtube-login' ausführen.")
    os.makedirs(SECRETS, exist_ok=True)
    with open(token, "w") as fh:
        fh.write(creds.to_json())
    return creds


def upload_youtube(cfg, video, title, description, tags, log=print):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    yt = build("youtube", "v3", credentials=youtube_credentials())
    body = {"snippet": {"title": title[:100], "description": description[:4900], "tags": tags[:30],
                        "categoryId": "27"},                       # 27 = Education
            "status": {"privacyStatus": cfg.YOUTUBE_PRIVACY, "selfDeclaredMadeForKids": False}}
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(video, mimetype="video/mp4", chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    url = f"https://youtube.com/shorts/{resp['id']}"
    log(f"  YouTube: {url}")
    return url


# ---------------------------------------------------------------- Instagram Reels (resumable upload)
def instagram_token(cfg, log=print):
    token = _env("IG_ACCESS_TOKEN")
    if cfg.INSTAGRAM_HOST == "graph.instagram.com":            # Instagram Login: renew the 60-day token
        try:
            r = requests.get("https://graph.instagram.com/refresh_access_token", timeout=30,
                             params={"grant_type": "ig_refresh_token", "access_token": token}).json()
            if r.get("access_token") and r["access_token"] != token:
                update_github_secret("IG_ACCESS_TOKEN", r["access_token"], log)
                return r["access_token"]
        except Exception as e:
            log(f"  Instagram: Token-Erneuerung übersprungen ({e})")
    return token


def upload_instagram(cfg, video, caption, log=print):
    token, user = instagram_token(cfg, log), _env("IG_USER_ID")
    base = f"https://{cfg.INSTAGRAM_HOST}/{cfg.INSTAGRAM_API_VERSION}"
    r = requests.post(f"{base}/{user}/media", data={"media_type": "REELS", "upload_type": "resumable",
                                                    "caption": caption[:2200], "share_to_feed": "true",
                                                    "access_token": token}, timeout=60).json()
    if "id" not in r:
        raise RuntimeError(f"Instagram: {r}")
    cid = r["id"]
    uri = r.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{cfg.INSTAGRAM_API_VERSION}/{cid}"
    size = os.path.getsize(video)
    with open(video, "rb") as fh:
        up = requests.post(uri, headers={"Authorization": f"OAuth {token}", "offset": "0", "file_size": str(size)},
                           data=fh, timeout=1800)
    if up.status_code != 200:
        raise RuntimeError(f"Instagram Upload {up.status_code}: {up.text[:300]}")
    for _ in range(120):                                          # up to ~10 minutes processing
        st = requests.get(f"{base}/{cid}", params={"fields": "status_code,status", "access_token": token},
                          timeout=60).json()
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram Verarbeitung fehlgeschlagen: {st}")
        time.sleep(5)
    pub = requests.post(f"{base}/{user}/media_publish", data={"creation_id": cid, "access_token": token},
                        timeout=60).json()
    if "id" not in pub:
        raise RuntimeError(f"Instagram publish: {pub}")
    log(f"  Instagram: veröffentlicht (ID {pub['id']})")
    return pub["id"]


# ---------------------------------------------------------------- TikTok (Content Posting API)
TT = "https://open.tiktokapis.com/v2/post/publish"


def tiktok_token(log=print):
    """TikTok access tokens expire after 24 h. With client key/secret + refresh token the bot renews them itself."""
    store = os.path.join(SECRETS, "tiktok_token.json")
    refresh = os.environ.get("TIKTOK_REFRESH_TOKEN", "").strip()
    if os.path.exists(store):
        with open(store) as fh:
            refresh = json.load(fh).get("refresh_token", refresh)
    key, secret = os.environ.get("TIKTOK_CLIENT_KEY", "").strip(), os.environ.get("TIKTOK_CLIENT_SECRET", "").strip()
    if refresh and key and secret:
        r = requests.post("https://open.tiktokapis.com/v2/oauth/token/", timeout=60,
                          headers={"Content-Type": "application/x-www-form-urlencoded"},
                          data={"client_key": key, "client_secret": secret, "grant_type": "refresh_token",
                                "refresh_token": refresh}).json()
        if "access_token" in r:
            new_refresh = r.get("refresh_token", refresh)
            os.makedirs(SECRETS, exist_ok=True)
            with open(store, "w") as fh:
                json.dump({"refresh_token": new_refresh}, fh)
            if new_refresh != refresh:
                update_github_secret("TIKTOK_REFRESH_TOKEN", new_refresh, log)
            return r["access_token"]
        log(f"  TikTok: Token-Erneuerung fehlgeschlagen ({r}) – nutze TIKTOK_ACCESS_TOKEN")
    return _env("TIKTOK_ACCESS_TOKEN")


def upload_tiktok(cfg, video, caption, log=print):
    headers = {"Authorization": f"Bearer {tiktok_token(log)}", "Content-Type": "application/json; charset=UTF-8"}
    size = os.path.getsize(video)
    if size <= 64 * 1024 * 1024:
        chunk, count = size, 1
    else:
        chunk = 10 * 1024 * 1024
        count = size // chunk                                     # last chunk takes the remainder
    source = {"source": "FILE_UPLOAD", "video_size": size, "chunk_size": chunk, "total_chunk_count": count}
    if cfg.TIKTOK_MODE == "direct":
        info = requests.post(f"{TT}/creator_info/query/", headers=headers, timeout=60).json()
        options = info.get("data", {}).get("privacy_level_options", [])
        if cfg.TIKTOK_PRIVACY not in options:
            raise RuntimeError(f"TikTok erlaubt nur {options} – bitte TIKTOK_PRIVACY in config.py anpassen")
        body = {"post_info": {"title": caption[:2200], "privacy_level": cfg.TIKTOK_PRIVACY, "disable_duet": False,
                              "disable_comment": False, "disable_stitch": False, "video_cover_timestamp_ms": 1000},
                "source_info": source}
        init = requests.post(f"{TT}/video/init/", headers=headers, json=body, timeout=60).json()
    else:
        init = requests.post(f"{TT}/inbox/video/init/", headers=headers, json={"source_info": source},
                             timeout=60).json()
    data = init.get("data", {})
    if "upload_url" not in data:
        raise RuntimeError(f"TikTok init: {init}")
    with open(video, "rb") as fh:
        for i in range(count):
            start = i * chunk
            end = size - 1 if i == count - 1 else start + chunk - 1
            fh.seek(start)
            part = fh.read(end - start + 1)
            r = requests.put(data["upload_url"], data=part, timeout=1800,
                             headers={"Content-Type": "video/mp4", "Content-Length": str(len(part)),
                                      "Content-Range": f"bytes {start}-{end}/{size}"})
            if r.status_code not in (200, 201, 206):
                raise RuntimeError(f"TikTok Upload {r.status_code}: {r.text[:300]}")
    for _ in range(120):
        st = requests.post(f"{TT}/status/fetch/", headers=headers, json={"publish_id": data["publish_id"]},
                           timeout=60).json().get("data", {})
        status = st.get("status", "")
        if status in ("PUBLISH_COMPLETE", "SEND_TO_USER_INBOX"):
            log("  TikTok: " + ("veröffentlicht" if status == "PUBLISH_COMPLETE" else "als Entwurf in deiner App"))
            return status
        if status == "FAILED":
            raise RuntimeError(f"TikTok: {st.get('fail_reason')}")
        time.sleep(5)
    return "PROCESSING"


def publish_all(cfg, info, log=print):
    """info: dict with final_4k, final_1080p, title, description, tags."""
    tags = " ".join(cfg.HASHTAGS)
    caption = f"{info['title']}\n\n{info['description']}\n\n{tags}"
    small = info.get("final_1080p") or info["final_4k"]
    results = {}
    for flag, name, fn in ((cfg.UPLOAD_YOUTUBE, "youtube",
                            lambda: upload_youtube(cfg, info["final_4k"], info["title"],
                                                   info["description"] + "\n\n" + tags, info["tags"], log)),
                           (cfg.UPLOAD_INSTAGRAM, "instagram", lambda: upload_instagram(cfg, small, caption, log)),
                           (cfg.UPLOAD_TIKTOK, "tiktok", lambda: upload_tiktok(cfg, small, caption, log))):
        if not flag:
            continue
        try:
            results[name] = fn()
        except Exception as e:                                       # one platform failing must not stop the others
            results[name] = f"FEHLER: {e}"
            log(f"  {name}: FEHLER {e}")
    return results
