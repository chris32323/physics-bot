# PHYSICS EVERY DAY – der tägliche Physik-Bot

Jeden Morgen ein neues Physik-Erklärvideo im Hochformat (YouTube Shorts, Instagram Reels, TikTok):
Animationen, Formeln, Sprecherstimme, Untertitel, Musik und Soundeffekte – in 4K mit 60 Bildern pro Sekunde.
Er läuft komplett auf **GitHub** und nutzt nur **OpenAI**: kein eigener PC, kein Abo.

| Schritt | Was passiert |
|---|---|
| 1. Thema | nimmt das nächste offene Thema aus `topics.txt` |
| 2. Skript + Animation | **GPT-6.1** schreibt Erzähltext und Animationscode – nach den Regeln in `prompts/writer_guide.md`, mit `episodes/e012_projectile_motion.py` als Vorbild |
| 3. Rendern | 4K/60 fps auf GitHubs Servern, plus eine 1080p-Kopie |
| 4. Selbstkontrolle | Code-Sicherheitscheck · Absturztest über das ganze Video · Layout-Prüfung (überlappende Texte, Untertitel-Bereich, App-Buttons) · alle Zahlen kommen aus dem Code · jede Sprachaufnahme wird mit dem Skript verglichen und bei Abweichung neu aufgenommen · danach prüft GPT-6.1 Standbilder und bessert nach |
| 5. Stimme + Ton | Stimme **cedar** über **gpt-realtime-2.1**; Musik wird unter der Stimme automatisch leiser; Soundeffekte zur Animation; Lautstärke −14 LUFS |
| 6. Upload | automatisch zu Instagram (und YouTube/TikTok, falls eingeschaltet) – ohne Freigabe |

**Genug Zeit für die Erklärung:** Die Stimme wird zuerst erzeugt. Jede Szene dauert genau so lange wie
ihre Sätze – plus Pausen, damit man Animation und Erklärung in Ruhe aufnehmen kann.

---

## Einrichtung auf GitHub (einmalig, ca. 20 Minuten)

Die ausführliche Schritt-für-Schritt-Anleitung bekommst du separat. Kurzfassung:

1. **Repository anlegen** – öffentlich empfohlen (GitHub Actions dann kostenlos und unbegrenzt; deine
   Schlüssel bleiben trotzdem geheim). Privat geht genauso (2.000 Gratis-Minuten im Monat).
2. **Dateien hochladen** – Inhalt der ZIP, inklusive des oft unsichtbaren Ordners `.github`.
3. **Secrets** (Settings → Secrets and variables → Actions): `OPENAI_API_KEY`, für Instagram
   `IG_ACCESS_TOKEN` und `IG_USER_ID`.
4. **Schreibrechte**: Settings → Actions → General → Workflow permissions → „Read and write permissions“.
5. **Stimme testen**: Actions → Voice test → Run workflow → Aufnahme unter „Artifacts“ herunterladen.
6. **Erstes Video**: Actions → Daily video → Run workflow (Feld leer lassen).

## Jeden Tag: vollautomatisch

Jeden Morgen (05:17 Uhr Winterzeit / 06:17 Uhr Sommerzeit) erstellt GitHub das Video, prüft es automatisch
und lädt es direkt hoch – ohne Freigabe. Das Video liegt zusätzlich 14 Tage im Lauf unter **Artifacts**.
Schlägt eine Prüfung oder ein Upload fehl, wird nichts veröffentlicht und GitHub schickt dir eine E-Mail.

Wer doch freigeben möchte: Settings → Environments → `release` mit „Required reviewers“ anlegen und in
`.github/workflows/daily.yml` beim Job `publish` die Zeile `environment: release` ergänzen.

## Einstellungen ändern

Alles steht in `config.py` – auf GitHub einfach die Datei öffnen, auf den Stift klicken, ändern, **Commit changes**.

```python
VOICE = "cedar"                    # Stimme (z. B. "cedar", "marin", "coral")
VOICE_MODEL = "gpt-realtime-2.1"   # günstiger: "gpt-realtime-2.1-mini"
VOICE_STYLE = """..."""            # wie gesprochen wird – leer lassen ("") = keine Vorgaben
WRITER_MODEL = "gpt-6.1-sol"       # das Modell, das Skript und Animation schreibt
RESOLUTION = "4k"                  # oder "1080p" (schneller)
```

Themen stehen in `topics.txt` (eins pro Zeile, beliebig ergänzen). Das jeweils nächste Thema wird zum
„Tomorrow: …“-Teaser am Ende des Videos.

## Hochladen einrichten (wenn du so weit bist)

Erst in `config.py` einschalten, wenn der Zugang steht (`UPLOAD_YOUTUBE = True` usw.).

**YouTube**

1. In der Google Cloud Console ein Projekt anlegen, die **YouTube Data API v3** aktivieren.
2. OAuth-Zustimmungsbildschirm einrichten und auf **„In Produktion“** stellen – im Testmodus läuft die
   Anmeldung nach 7 Tagen ab.
3. OAuth-Client vom Typ „Desktop-App“ erstellen, JSON herunterladen.
4. Einmalig auf einem PC (braucht einen Browser): Python installieren, dann im Projektordner
   `pip install -r requirements.txt`, die JSON als `secrets/client_secret.json` speichern und
   `python bot.py youtube-login` ausführen.
5. Den Inhalt der entstandenen Datei `secrets/youtube_token.json` als Secret `YOUTUBE_TOKEN_JSON` eintragen.

Hinweis: Neue Google-Projekte dürfen per API oft nur **privat** hochladen, bis Google das Projekt geprüft hat.

**Instagram (Reels)** – Business- oder Creator-Konto und eine Meta-App mit `instagram_business_content_publish`.
Secrets: `IG_USER_ID`, `IG_ACCESS_TOKEN`. Bei „Instagram Login“ zusätzlich in `config.py`
`INSTAGRAM_HOST = "graph.instagram.com"` – dann erneuert der Bot den Token selbst (siehe `GH_SECRETS_TOKEN`).

**TikTok** – TikTok-Developer-App mit der Content Posting API.
Secrets: `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REFRESH_TOKEN` (der Bot holt sich damit
selbst einen frischen Zugang).

- `TIKTOK_MODE = "inbox"` (Standard): Video landet als **Entwurf in deiner TikTok-App**, du tippst dort auf
  Posten – funktioniert ohne TikTok-Prüfung.
- `TIKTOK_MODE = "direct"`: direkt veröffentlichen; ohne TikTok-Audit sind solche Posts nur privat sichtbar.

**`GH_SECRETS_TOKEN`** (optional, empfohlen für TikTok/Instagram): Manche Plattformen geben bei jeder
Erneuerung einen neuen Schlüssel aus. Damit der Bot ihn speichern kann: github.com → Settings → Developer
settings → **Fine-grained personal access token** → nur dieses Repository → Berechtigung
**Secrets: Read and write** → als Secret `GH_SECRETS_TOKEN` eintragen.

## Kosten (grobe Schätzung)

| Posten | pro Video | pro Monat (täglich) |
|---|---|---|
| GPT-6.1 Sol (Skript, Animation, Prüfung) | ca. 0,20–1,50 $, meist ~0,50 $ | ~15 $ |
| Stimme cedar (gpt-realtime-2.1) | ca. 0,10–0,25 $ | ~5 $ |
| GitHub Actions | öffentliches Repo: 0 $ | 0 $ |

Die echten Zahlen siehst du nach den ersten Läufen in deiner OpenAI-Abrechnung. Tipp: Lege dort ein
Ausgabenlimit fest.

## Ohne GitHub auf dem eigenen PC (optional)

Python 3.10+, ffmpeg und die Schrift Inter installieren (Linux: `sudo apt install ffmpeg fonts-inter`), dann:

```bash
pip install -r requirements.txt
cp .env.example .env                                   # Schlüssel eintragen
python bot.py voice-test "Hello there"                 # Stimme anhören
python bot.py render episodes/e012_projectile_motion.py   # Beispiel-Video in 4K
python bot.py daily                                    # kompletter Tageslauf
```

In `config.py` dafür `APPROVAL = "manual"` setzen; veröffentlicht wird dann mit `python bot.py publish build/ORDNER`.
`python tests/offline_test.py` testet alles ohne Schlüssel (KI und Stimme werden simuliert).

## Ordner

```
config.py                 alle Einstellungen
topics.txt                Themenliste
state.json                welche Folge dran ist, was veröffentlicht wurde (pflegt der Bot)
episodes/                 eine Datei pro Folge (Skript + Animation, schreibt die KI)
prompts/writer_guide.md   Regeln für die KI: Stil, Layout, Sprache, Tempo
engine/                   der Bot selbst
.github/workflows/        die drei GitHub-Abläufe: Daily video, Publish video, Voice test
```

## Wenn etwas nicht klappt

- **Lauf rot / Fehler:** Actions → den Lauf anklicken → den roten Schritt aufklappen. GitHub schickt dir bei
  Fehlern eine E-Mail.
- **„OPENAI_API_KEY fehlt“:** Secret-Name genau so schreiben, ohne Leerzeichen.
- **Fehler bei der Stimme:** zuerst den Workflow **Voice test** laufen lassen. Betrifft die Meldung `speed`,
  in `config.py` `VOICE_SPEED = 1.0` lassen.
- **Ein Satz klingt anders als im Skript:** Der Bot vergleicht jede Aufnahme mit dem Text und nimmt sie bis
  zu dreimal neu auf. Sonst: **Nochmal** mit einem Hinweis.
- **Der tägliche Lauf startet nicht mehr:** GitHub pausiert zeitgesteuerte Abläufe manchmal, wenn lange
  nichts im Repository passiert ist – unter Actions → Daily video wieder aktivieren.
- **Sicherheit:** Die Episoden-Dateien sind Python-Code, den die KI schreibt. Der Bot prüft vor dem Ausführen,
  dass dieser nur rechnet und zeichnet (keine Dateien, kein Netzwerk).
