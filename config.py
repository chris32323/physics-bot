# =====================================================================
#  PHYSICS EVERY DAY – Einstellungen
#  Alles, was du anpassen willst, steht in dieser Datei.
#  API-Schlüssel gehören NICHT hierher, sondern in die Datei ".env".
# =====================================================================

# ── Kanal ────────────────────────────────────────────────────────────
CHANNEL_NAME = "PHYSICS EVERY DAY"   # steht oben links im Video
LANGUAGE = "English"                 # Sprache von Sprecher, Text und Untertiteln

# ── Stimme ───────────────────────────────────────────────────────────
# Stimme einfach eintippen (OpenAI-Stimmen, z. B. "cedar", "marin", "coral", ...).
VOICE = "cedar"

# Sprachmodell von OpenAI. Günstiger und schneller: "gpt-realtime-2.1-mini"
VOICE_MODEL = "gpt-realtime-2.1"

# Wie der Sprecher klingen soll – frei formulierbar.
# Leer lassen (VOICE_STYLE = "") = keine Vorgaben, die Stimme spricht ganz neutral.
VOICE_STYLE = """
Calm, confident science explainer. Warm and friendly, like a good teacher
talking to one curious person. Natural, unhurried pace with clear articulation.
Let questions sound genuinely curious, and leave a short pause before key results.
Never theatrical, never salesy.
"""

VOICE_SPEED = 1.4                   # 1.0 = normal, 0.9 = etwas langsamer

# ── Tempo / genug Zeit für die Erklärung ─────────────────────────────
# Die Länge jeder Szene richtet sich nach der Sprecherstimme. Diese Werte
# geben zusätzlich Luft, damit man Bild und Erklärung in Ruhe aufnehmen kann.
SENTENCE_GAP = 0.30                  # Pause nach jedem Satz (Sekunden)
SCENE_LEAD = 0.35                    # Ruhe am Anfang jeder Szene
SCENE_TAIL = 0.50 
TARGET_DURATION = 60
MAX_DURATION = 75              # längere Videos werden als Problem gemeldet (Sekunden)
SUBTITLES = True                     # Untertitel einblenden (empfohlen – viele schauen ohne Ton)

# ── Bild ─────────────────────────────────────────────────────────────
RESOLUTION = "4k"                    # "4k" (2160×3840) oder "1080p" (1080×1920)
FPS = 60
MAKE_1080P_COPY = True               # zusätzlich eine 1080p-Datei für Instagram/TikTok
WORKERS = 0                          # 0 = automatisch (alle CPU-Kerne)

# ── Ton ──────────────────────────────────────────────────────────────
MUSIC = True                         # Hintergrundmusik (wird unter der Stimme automatisch leiser)
MUSIC_LEVEL = 1.0                    # 1.0 = Standard, 0.7 = leiser, 1.3 = lauter
SFX = True                           # Soundeffekte (Whoosh, Landung, Gong ...)
TARGET_LUFS = -14                    # Gesamtlautstärke (Standard für Social Media)

# ── KI für Skript, Animation und Bildprüfung (Schritt 2 und 4) ──────
WRITER_PROVIDER = "openai"           # "openai" (Standard) – alternativ "anthropic"
WRITER_MODEL = "gpt-6.1-sol"         # GPT-6.1 Sol; bei "anthropic" z. B. "claude-sonnet-5-5"
WRITER_EFFORT = "medium"             # Denkaufwand der KI: "low", "medium" oder "high"
FIX_ATTEMPTS = 5                     # wie oft die KI technische Fehler selbst reparieren darf
REVIEW_ROUNDS = 2                    # wie oft sie nach der Bildprüfung nachbessern darf

# ── Freigabe ─────────────────────────────────────────────────────────
# "github" = auf GitHub: wird nach den automatischen Prüfungen direkt hochgeladen
#            (ohne Freigabe; wer doch freigeben will: in daily.yml beim Job "publish"
#             die Zeile "environment: release" ergänzen und das Environment anlegen)
# "manual" = Video bleibt liegen, veröffentlichen mit: python bot.py publish ORDNER
# "auto"   = wird ohne Rückfrage hochgeladen
APPROVAL = "github"

# ── Hochladen (Schritt 6) ────────────────────────────────────────────
UPLOAD_YOUTUBE = False               # auf True setzen, sobald die Zugänge eingerichtet sind
UPLOAD_INSTAGRAM = True
UPLOAD_TIKTOK = False

YOUTUBE_PRIVACY = "public"           # "public", "unlisted" oder "private"
INSTAGRAM_API_VERSION = "v25.0"
INSTAGRAM_HOST = "graph.facebook.com"   # bei "Instagram Login" statt Facebook-Login: "graph.instagram.com"
TIKTOK_MODE = "inbox"                # "inbox" = landet als Entwurf in deiner TikTok-App (ohne TikTok-Prüfung möglich)
                                     # "direct" = direkt veröffentlichen (erst nach TikTok-Audit öffentlich)
TIKTOK_PRIVACY = "SELF_ONLY"         # nur für "direct": PUBLIC_TO_EVERYONE, FOLLOWER_OF_CREATOR, SELF_ONLY ...

HASHTAGS = ["#physics", "#science", "#learnontiktok", "#STEM", "#shorts"]
