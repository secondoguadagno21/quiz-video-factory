#!/usr/bin/env python3
"""
Voce narrante con Google AI Studio (Gemini TTS). Si attiva da sola se c'e' GEMINI_API_KEY
(cloud: variabili dell'ambiente; PC: file .env). Senza chiave il motore lavora come prima.

  python3 voce.py "Benvenuti a Quiz Divertenti Italia!"     # prova: scrive out/prova-voce.wav

Le frasi gia' generate restano in .cache_voce/ : rigenerare un video non le ripaga.
"""
import base64, hashlib, json, os, subprocess, sys, time, urllib.error, urllib.request

ROOT  = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, ".cache_voce")
API   = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"


def config():
    b = json.load(open(os.path.join(ROOT, "brand.json"), encoding="utf-8"))
    return b.get("voce", {})


def attiva():
    try:
        from analizza_video import carica_env; carica_env()
    except Exception:
        pass
    return bool(os.environ.get("GEMINI_API_KEY", "").strip()) and config().get("attiva", True)


def di(testo, stile=None):
    """Restituisce il percorso (relativo a ROOT) di un wav 44,1 kHz stereo con la frase."""
    cfg = config()
    modello = cfg.get("modello", "gemini-2.5-flash-preview-tts")
    voce = cfg.get("voce", "Puck")
    stile = stile or cfg.get("stile", "")
    prompt = f"{stile}: {testo}" if stile else testo
    h = hashlib.sha1(f"{modello}|{voce}|{prompt}".encode()).hexdigest()[:16]
    os.makedirs(CACHE, exist_ok=True)
    out = os.path.join(CACHE, f"{h}.wav")
    if os.path.exists(out):
        return os.path.relpath(out, ROOT).replace("\\", "/")

    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voce}}},
        },
    }).encode()
    url = API.format(m=modello)
    # chiave nell'intestazione: vale sia per le chiavi classiche (AIza...) sia per le nuove
    head = {"Content-Type": "application/json", "x-goog-api-key": os.environ["GEMINI_API_KEY"].strip()}
    for tent in range(5):
        try:
            rq = urllib.request.Request(url, body, head)
            r = json.load(urllib.request.urlopen(rq, timeout=120))
            parte = r["candidates"][0]["content"]["parts"][0]["inlineData"]
            break
        except urllib.error.HTTPError as e:
            err = e.read().decode()[:400]
            if e.code in (401, 403):
                raise SystemExit("Voce: chiave rifiutata. Controlla che sia di Google AI Studio "
                                 "(aistudio.google.com -> Get API key) e copiata intera.\n  " + err)
            if e.code == 429 or e.code >= 500:            # troppe richieste: aspetta e riprova
                time.sleep(8 * (tent + 1)); continue
            raise SystemExit(f"Voce: Google ha rifiutato la richiesta ({e.code}): {err}")
        except (KeyError, IndexError):
            raise SystemExit(f"Voce: risposta inattesa da Google: {json.dumps(r)[:400]}")
    else:
        raise SystemExit("Voce: limite di richieste raggiunto, riprova tra qualche minuto.")

    pcm = base64.b64decode(parte["data"])
    rate = 24000
    for pezzo in parte.get("mimeType", "").split(";"):
        if pezzo.strip().startswith("rate="): rate = int(pezzo.split("=")[1])
    raw = out + ".raw"
    open(raw, "wb").write(pcm)
    # PCM 16 bit mono -> wav 44,1 kHz stereo, silenzi in testa e in coda tagliati
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "s16le", "-ar", str(rate),
                    "-ac", "1", "-i", raw, "-af",
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                    "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                    "aresample=44100", "-ac", "2", out], check=True)
    os.remove(raw)
    return os.path.relpath(out, ROOT).replace("\\", "/")


if __name__ == "__main__":
    if not attiva(): sys.exit("Manca GEMINI_API_KEY (Google AI Studio -> Get API key).")
    p = di(" ".join(sys.argv[1:]) or "Benvenuti a Quiz Divertenti Italia! Siete pronti?")
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    dest = os.path.join(ROOT, "out", "prova-voce.wav")
    import shutil; shutil.copy(os.path.join(ROOT, p), dest)
    print(f"Voce pronta: {dest}")
