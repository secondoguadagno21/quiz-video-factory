#!/usr/bin/env python3
"""
Voce narrante con Google AI Studio (Gemini TTS). Si attiva da sola se c'e' GEMINI_API_KEY
(cloud: variabili dell'ambiente; PC: file .env). Senza chiave il motore lavora come prima.

  python3 voce.py "Benvenuti a Quiz Divertenti Italia!"     # prova: scrive out/prova-voce.wav
  python3 voce.py --copione quiz/x.json                      # tutte le frasi: out/x-copione.txt

Il video intero si puo' leggere anche in un audio unico (Gemini in poche richieste,
oppure registrato altrove con il suo SRT): lo taglia importa_voce.py.

Le frasi gia' generate restano in .cache_voce/ : rigenerare un video non le ripaga.
"""
import base64, hashlib, json, os, subprocess, sys, time, urllib.error, urllib.request

ROOT  = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, ".cache_voce")
ESTERNA = os.path.join(CACHE, "esterna")   # frasi tagliate da un audio unico (importa_voce.py)
API   = "https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent"


def config():
    b = json.load(open(os.path.join(ROOT, "brand.json"), encoding="utf-8"))
    return b.get("voce", {})


def chiave():
    try:
        from analizza_video import carica_env; carica_env()
    except Exception:
        pass
    k = os.environ.get("GEMINI_API_KEY", "").strip()
    if not k and sys.platform == "win32":     # setx la scrive qui: i processi gia' aperti non la vedono
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as h:
                k = winreg.QueryValueEx(h, "GEMINI_API_KEY")[0].strip()
            os.environ["GEMINI_API_KEY"] = k
        except OSError:
            pass
    return k


def attiva():
    """Voce accesa se c'e' la chiave Gemini oppure un audio esterno gia' importato."""
    esterne = os.path.isdir(ESTERNA) and any(f.endswith(".wav") for f in os.listdir(ESTERNA))
    return (bool(chiave()) or esterne) and config().get("attiva", True)


def firma(testo):
    """Chiave di una frase importata: non dipende da modello, voce o stile."""
    return hashlib.sha1(" ".join(testo.split()).encode()).hexdigest()[:16]


def registrata(testo):
    """La frase c'e' gia' nell'audio esterno importato (la voce scelta, Kira)?"""
    return os.path.exists(os.path.join(ESTERNA, f"{firma(testo)}.wav"))


def di(testo, stile=None):
    """Restituisce il percorso (relativo a ROOT) di un wav 44,1 kHz stereo con la frase.
    Prima cerca l'audio esterno importato (importa_voce.py), poi chiede a Gemini."""
    est = os.path.join(ESTERNA, f"{firma(testo)}.wav")
    if os.path.exists(est):
        return os.path.relpath(est, ROOT).replace("\\", "/")
    if not chiave():
        raise SystemExit(f"Voce: manca l'audio di questa frase e non c'e' GEMINI_API_KEY:\n  {testo}")
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
    pcm, rate = gemini(prompt, modello, voce)
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


def gemini(prompt, modello, voce):
    """Una richiesta TTS: (pcm 16 bit mono, frequenza)."""
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
            if "PerDay" in err:                           # quota del giorno finita: inutile insistere
                raise SystemExit("Voce: finite le richieste gratuite di oggi (10 al giorno). "
                                 "Riprova domani.\n  " + err)
            if e.code == 429 or e.code >= 500:            # troppe richieste: aspetta e riprova
                time.sleep(8 * (tent + 1)); continue
            raise SystemExit(f"Voce: Google ha rifiutato la richiesta ({e.code}): {err}")
        except (KeyError, IndexError):
            raise SystemExit(f"Voce: risposta inattesa da Google: {json.dumps(r)[:400]}")
    else:
        raise SystemExit("Voce: limite di richieste raggiunto, riprova tra qualche minuto.")
    rate = 24000
    for pezzo in parte.get("mimeType", "").split(";"):
        if pezzo.strip().startswith("rate="): rate = int(pezzo.split("=")[1])
    return base64.b64decode(parte["data"]), rate


def audio_unico(quiz, dest):
    """Tutto il copione in poche richieste (una per livello) invece di una per frase:
    il piano gratuito ne concede 10 al giorno. Le frasi vanno poi tagliate da importa_voce.py."""
    cfg = config()
    modello = cfg.get("modello", "gemini-2.5-flash-preview-tts")
    righe, liv = copione(quiz), {frase_livello(n) for _, n in quiz.get("capitoli") or []}
    blocchi = [[]]
    for r in righe:
        if r in liv and len(blocchi[-1]) > 1:      # un blocco per livello (il gancio va col primo)
            blocchi.append([])
        blocchi[-1].append(r)
    if not chiave(): raise SystemExit("Manca GEMINI_API_KEY.")
    pezzi = []
    for i, b in enumerate(blocchi):
        print(f"  voce: blocco {i+1}/{len(blocchi)} ({len(b)} frasi)", flush=True)
        prompt = (f"{cfg.get('stile', '')}. Leggi le frasi seguenti una dopo l'altra, esattamente "
                  "come sono scritte, con una pausa di un secondo e mezzo fra una frase e l'altra:\n\n"
                  + "\n\n".join(b))
        pcm, rate = gemini(prompt, modello, cfg.get("voce", "Leda"))
        raw = f"{dest}.{i}.raw"; open(raw, "wb").write(pcm)
        pezzi.append((raw, rate))
    # i blocchi si uniscono con 1,5 s di silenzio: lo stesso segnale di taglio fra le frasi
    ins, fc = [], ""
    for j, (raw, rate) in enumerate(pezzi):
        ins += ["-f", "s16le", "-ar", str(rate), "-ac", "1", "-i", raw]
        fc += f"[{j}:a]aresample=44100,apad=pad_dur=1.5[p{j}];"
    fc += "".join(f"[p{j}]" for j in range(len(pezzi))) + f"concat=n={len(pezzi)}:v=0:a=1[a]"
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *ins, "-filter_complex", fc,
                    "-map", "[a]", "-ac", "2", dest], check=True)
    for raw, _ in pezzi: os.remove(raw)
    return dest


# ---------- le frasi del video: le usano sia build.py sia il copione ----------
def mancanti_o_tutte(files, mancanti):
    """Frasi di uno o piu' quiz, senza doppioni; con mancanti=True solo quelle senza audio."""
    righe = []
    for f in files:
        for r in copione(json.load(open(f, encoding="utf-8"))):
            if r not in righe and not (mancanti and registrata(r)): righe.append(r)
    return righe



def frase_hook(quiz):
    v = quiz.get("voce", {})
    if "hook" in v: return v["hook"]
    return (v.get("hook") or
            f"{quiz['titolo']} {quiz.get('sottotitolo', '')}. Tieni il conto e scrivi il punteggio nei commenti. Via!")


def frase_livello(nome):
    parti = [p.strip() for p in nome.split(" - ", 1)]
    frase = {"facile": "Si comincia col riscaldamento!", "medio": "Adesso si fa sul serio!",
             "difficile": "Solo per veri geni!"}.get(parti[-1].lower(), "")
    return f"{parti[0]}! {parti[1] if len(parti) > 1 else ''}. {frase}"


def frase_cta(quiz):
    """Frase finale degli short (rimando al video completo); None nei video lunghi."""
    return quiz.get("voce", {}).get("cta")


def frase_risposta(opzioni, giusta):
    return f"Risposta {'ABCD'[giusta]}: {opzioni[giusta]}!"


def copione(quiz):
    """Tutte le frasi, nell'ordine in cui le dice il video."""
    cap = {i: nome for i, nome in quiz.get("capitoli") or []}
    righe = [frase_hook(quiz)]
    for i, d in enumerate(quiz["domande"]):
        if i in cap: righe.append(frase_livello(cap[i]))
        righe += [d["q"], frase_risposta(d["opzioni"], d["giusta"])]
    if frase_cta(quiz): righe.append(frase_cta(quiz))
    return [r for r in righe if r]


if __name__ == "__main__":
    if sys.argv[1:2] == ["--copione"]:
        # una frase per riga, riga vuota in mezzo: chi legge (o il TTS) fa la pausa.
        # Piu' quiz insieme (es. gli short) danno un copione solo; --mancanti tiene solo
        # le frasi non ancora registrate (negli short le domande ci sono gia')
        mancanti = "--mancanti" in sys.argv
        files = [f for f in sys.argv[2:] if f != "--mancanti"]
        righe = mancanti_o_tutte(files, mancanti)
        base = os.path.splitext(os.path.basename(files[0]))[0] + ("-mancanti" if mancanti else "")
        dest = os.path.join(ROOT, "out", f"{base}-copione.txt")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        open(dest, "w", encoding="utf-8").write("\n\n".join(righe) + "\n")
        print(f"Copione: {dest}\n  {len(righe)} frasi, {sum(len(r) for r in righe)} caratteri")
        sys.exit(0)
    if not attiva(): sys.exit("Manca GEMINI_API_KEY (Google AI Studio -> Get API key).")
    p = di(" ".join(sys.argv[1:]) or "Benvenuti a Quiz Divertenti Italia! Siete pronti?")
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    dest = os.path.join(ROOT, "out", "prova-voce.wav")
    import shutil; shutil.copy(os.path.join(ROOT, p), dest)
    print(f"Voce pronta: {dest}")
