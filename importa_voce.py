#!/usr/bin/env python3
"""
Taglia un audio unico con tutto il copione nelle frasi del video. Dopo, build.py usa
quelle frasi al posto delle chiamate a Gemini (zero richieste).

  python3 importa_voce.py quiz/x.json --audio voce.wav --trascrivi     # CONSIGLIATO: trascrive qui
  python3 importa_voce.py quiz/x.json --audio voce.wav --srt voce.srt  # con un SRT fatto altrove
  python3 importa_voce.py quiz/x.json --audio voce.wav                 # senza testo: sulle pause
  python3 importa_voce.py quiz/x.json --gemini                         # Gemini via API, 1 richiesta/livello
  ... --prova                                                          # mostra i tagli, non scrive

Il copione da leggere: python3 voce.py --copione quiz/x.json (una frase per blocco).
--trascrivi ascolta l'audio in locale (faster-whisper, gratis) e trova l'istante di ogni
parola: e' piu' preciso degli SRT automatici, che sbagliano lettere e numeri.
Il testo viene allineato parola per parola al copione e il taglio va sulla pausa vera
dopo l'ultima parola della frase: cosi' non si taglia mai a meta' di una parola.
Senza testo servono pause nette fra le frasi, e il conto deve tornare.
"""
import argparse, difflib, json, os, re, subprocess, sys, unicodedata
import voce

ROOT = os.path.dirname(os.path.abspath(__file__))
VOLUME_FRASE = -17.0      # LUFS di ogni frase tagliata


def durata(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", p], capture_output=True, text=True).stdout.strip())


def silenzi(audio, soglia, minimo):
    """[(inizio, fine)] delle pause dell'audio."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", audio, "-af",
                          f"silencedetect=noise={soglia}dB:d={minimo}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    a = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    z = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    return list(zip(a, z))


def parole(testo):
    t = unicodedata.normalize("NFKD", testo.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", t).split()


def leggi_srt(path):
    """Parole dell'SRT con il loro istante, interpolato dentro il blocco."""
    def sec(s):
        h, m, r = s.strip().replace(".", ",").split(":"); s, ms = r.split(",")
        return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
    fuori = []
    for b in open(path, encoding="utf-8-sig").read().strip().split("\n\n"):
        r = [x for x in b.strip().splitlines() if x.strip()]
        if len(r) < 3 or "-->" not in r[1]: continue
        a, z = (sec(x) for x in r[1].split("-->"))
        w = parole(" ".join(r[2:]))
        fuori += [(p, a + (z - a) * i / max(1, len(w))) for i, p in enumerate(w)]
    return fuori


def trascrivi(audio):
    """Parole con il loro istante, ascoltate in locale. Il modello (~500 MB) si scarica
    la prima volta e resta in cache."""
    try:
        import numpy as np
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("Serve faster-whisper:  pip install faster-whisper")
    os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
    print("  trascrivo l'audio (qualche minuto)...", flush=True)
    # l'audio lo decodifica ffmpeg: il lettore interno di faster-whisper non regge tutti i file
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", audio, "-f", "s16le", "-ac", "1",
                          "-ar", "16000", "-"], capture_output=True).stdout
    segs, _ = WhisperModel("small", device="cpu", compute_type="int8").transcribe(
        np.frombuffer(pcm, np.int16).astype(np.float32) / 32768, language="it",
        word_timestamps=True, condition_on_previous_text=False)
    return [(p, w.start) for s in segs for w in s.words for p in parole(w.word)]


def tagli_da_pause(n, sil, dur):
    """Le n-1 pause piu' lunghe dentro l'audio sono i confini fra le frasi."""
    dentro = [s for s in sil if s[0] > 0.05 and s[1] < dur - 0.05]
    if len(dentro) < n - 1:
        sys.exit(f"Trovate {len(dentro)} pause ma servono {n-1}: le frasi sono attaccate. "
                 "Prova --soglia -30 o --minimo 0.3, oppure passa l'SRT.")
    scelte = sorted(sorted(dentro, key=lambda s: s[1] - s[0], reverse=True)[:n-1])
    corta = min(s[1] - s[0] for s in scelte)
    escluse = [s[1] - s[0] for s in dentro if s not in scelte]
    if escluse and max(escluse) > corta * 0.8:
        print(f"  ATTENZIONE: pausa fra frasi piu' corta {corta:.2f}s, pausa dentro una frase "
              f"piu' lunga {max(escluse):.2f}s: qualche taglio potrebbe essere sbagliato.")
    return [(a + z) / 2 for a, z in scelte]


def tagli_da_testo(righe, sw, sil):
    """Inizio di ogni frase dall'allineamento parola per parola, poi spostato sulla pausa vicina.
    sw = [(parola, istante)] da un SRT o dalla trascrizione locale."""
    cw = [(p, k) for k, r in enumerate(righe) for p in parole(r)]
    m = difflib.SequenceMatcher(None, [p for p, _ in cw], [p for p, _ in sw], autojunk=False)
    tempo = {}
    for a, b, size in m.get_matching_blocks():
        for i in range(size): tempo[a + i] = sw[b + i][1]
    inizio, ultima = [], []
    for k in range(len(righe)):
        idx = [i for i, (_, kk) in enumerate(cw) if kk == k and i in tempo]
        if not idx: sys.exit(f"La frase {k+1} non si trova nell'SRT: {righe[k]}")
        inizio.append(tempo[idx[0]]); ultima.append(tempo[idx[-1]])
    tagli, prima = [], 0.0
    for k in range(1, len(righe)):
        # la pausa di confine comincia dopo l'ultima parola della frase prima (cosi' non si
        # spezza "Risposta B ... Vivaldi"), dopo il taglio precedente, e prima della prima
        # parola di questa: fra le candidate vince la piu' lunga
        vicine = [s for s in sil if max(ultima[k-1] - 0.1, prima + 0.4) <= s[0] <= inizio[k] + 0.6]
        s = max(vicine, key=lambda s: s[1] - s[0]) if vicine else None
        prima = (s[0] + s[1]) / 2 if s else max(inizio[k] - 0.08, prima + 0.4)
        tagli.append(prima)
    return tagli


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("quiz")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--audio"); g.add_argument("--gemini", action="store_true")
    t = ap.add_mutually_exclusive_group()
    t.add_argument("--srt"); t.add_argument("--trascrivi", action="store_true")
    ap.add_argument("--soglia", type=float, default=-40, help="dB sotto cui e' silenzio")
    ap.add_argument("--minimo", type=float, default=0.25, help="secondi minimi di una pausa")
    ap.add_argument("--prova", action="store_true"); ap.add_argument("--forza", action="store_true")
    a = ap.parse_args()

    quiz = json.load(open(a.quiz, encoding="utf-8"))
    righe = voce.copione(quiz)
    if a.gemini:
        base = os.path.splitext(os.path.basename(a.quiz))[0]
        a.audio = os.path.join(ROOT, "out", f"{base}-voce.wav")
        os.makedirs(os.path.dirname(a.audio), exist_ok=True)
        if os.path.exists(a.audio): print(f"  voce: riuso {a.audio}")
        else: voce.audio_unico(quiz, a.audio)
    dur, sil = durata(a.audio), silenzi(a.audio, a.soglia, a.minimo)
    sw = leggi_srt(a.srt) if a.srt else trascrivi(a.audio) if a.trascrivi else None
    tagli = tagli_da_testo(righe, sw, sil) if sw else tagli_da_pause(len(righe), sil, dur)
    confini = [0.0] + tagli + [dur]

    # controllo: ogni frase deve durare piu' o meno quanto il suo testo
    ritmo = sorted((confini[k+1] - confini[k]) / max(8, len(r)) for k, r in enumerate(righe))[len(righe)//2]
    strane = 0
    print(f"{'N':>4} {'INIZIO':>7} {'DUR':>5}  FRASE")
    for k, r in enumerate(righe):
        d = confini[k+1] - confini[k]; atteso = ritmo * max(8, len(r))
        nota = "  <-- ?" if not 0.45 < d / atteso < 2.2 else ""
        strane += bool(nota)
        print(f"{k+1:>4} {confini[k]:7.2f} {d:5.2f}  {r[:60]}{nota}")
    print(f"\n{len(righe)} frasi, {dur:.0f}s di audio, {strane} da controllare")
    if a.prova: sys.exit("--prova: niente scritto.")
    vuote = [k+1 for k in range(len(righe)) if confini[k+1] - confini[k] < 0.5]
    if vuote: sys.exit(f"Frasi quasi vuote (taglio sbagliato): {vuote}. Controlla la tabella.")
    if strane > max(2, len(righe) // 30) and not a.forza:
        sys.exit("Troppe frasi con una durata strana: il taglio e' probabilmente sfasato. "
                 "Controlla la tabella (o usa --forza).")

    os.makedirs(voce.ESTERNA, exist_ok=True)
    # bordi ripuliti dalla mezza pausa che ogni taglio si porta dietro. Soglia bassa: un
    # "Chi" detto piano sta sui -45 dB e con -42 veniva mangiato; i clic sotto 30 ms non contano
    pulisci = "silenceremove=start_periods=1:start_threshold=-52dB:start_duration=0.03"
    for k, r in enumerate(righe):
        out = os.path.join(voce.ESTERNA, f"{voce.firma(r)}.wav")
        # -ss/-to prima di -i: i filtri lavorano solo sul pezzo, non su tutto il file
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-ss", f"{confini[k]:.3f}", "-to", f"{confini[k+1]:.3f}", "-i", a.audio, "-af",
                        f"{pulisci},areverse,{pulisci},areverse,afade=t=in:d=0.02,"
                        "aresample=44100", "-ac", "2", out], check=True)
        # stesso volume per tutte le frasi: nelle letture lunghe la voce sale e scende
        # anche di 7 dB, e le risposte corte finivano sotto la musica
        e = subprocess.run(["ffmpeg", "-hide_banner", "-i", out, "-af", "ebur128", "-f", "null", "-"],
                           capture_output=True, text=True).stderr
        lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", e)
        if lufs:
            gain = max(-6.0, min(6.0, VOLUME_FRASE - float(lufs[-1])))
            tmp = out + ".tmp.wav"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", out, "-af",
                            f"volume={gain:.2f}dB,alimiter=limit=0.89:level=disabled", tmp], check=True)
            os.replace(tmp, out)
    print(f"FATTO: {len(righe)} frasi in {os.path.relpath(voce.ESTERNA, ROOT)}\n"
          f"  ora: python3 build.py {a.quiz} --formato youtube")
