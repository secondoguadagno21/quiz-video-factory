#!/usr/bin/env python3
"""
Taglia un audio unico con tutto il copione nelle frasi del video. Dopo, build.py usa
quelle frasi al posto delle chiamate a Gemini (zero richieste).

  python3 importa_voce.py quiz/x.json --gemini                    # Gemini Leda, una richiesta per livello
  python3 importa_voce.py quiz/x.json --audio voce.mp3 --srt voce.srt   # audio letto altrove (Fliki, ...)
  python3 importa_voce.py quiz/x.json --audio voce.mp3            # senza SRT: taglia sulle pause
  ... --prova                                                     # mostra i tagli, non scrive

Il copione da leggere: python3 voce.py --copione quiz/x.json (una frase per blocco).
Senza SRT servono pause nette fra le frasi (almeno mezzo secondo), e il conto deve tornare.
Con l'SRT il testo viene allineato parola per parola al copione, e il taglio va sulla pausa
vera piu' vicina: cosi' non si taglia mai a meta' di una parola.
"""
import argparse, difflib, json, os, re, subprocess, sys, unicodedata
import voce

ROOT = os.path.dirname(os.path.abspath(__file__))


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


def tagli_da_srt(righe, srt, sil):
    """Inizio di ogni frase dall'allineamento parola per parola, poi spostato sulla pausa vicina."""
    cw = [(p, k) for k, r in enumerate(righe) for p in parole(r)]
    sw = leggi_srt(srt)
    m = difflib.SequenceMatcher(None, [p for p, _ in cw], [p for p, _ in sw], autojunk=False)
    tempo = {}
    for a, b, size in m.get_matching_blocks():
        for i in range(size): tempo[a + i] = sw[b + i][1]
    inizio = []
    for k in range(len(righe)):
        idx = [i for i, (_, kk) in enumerate(cw) if kk == k and i in tempo]
        if not idx: sys.exit(f"La frase {k+1} non si trova nell'SRT: {righe[k]}")
        inizio.append(tempo[idx[0]])
    tagli = []
    for t in inizio[1:]:
        vicine = [s for s in sil if t - 1.0 <= s[1] <= t + 0.4]
        s = min(vicine, key=lambda s: abs(s[1] - t)) if vicine else None
        tagli.append((s[0] + s[1]) / 2 if s else t - 0.08)
    return tagli


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("quiz")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--audio"); g.add_argument("--gemini", action="store_true")
    ap.add_argument("--srt")
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
    tagli = tagli_da_srt(righe, a.srt, sil) if a.srt else tagli_da_pause(len(righe), sil, dur)
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
    if strane > max(2, len(righe) // 30) and not a.forza:
        sys.exit("Troppe frasi con una durata strana: il taglio e' probabilmente sfasato. "
                 "Controlla la tabella (o usa --forza).")

    os.makedirs(voce.ESTERNA, exist_ok=True)
    for k, r in enumerate(righe):
        out = os.path.join(voce.ESTERNA, f"{voce.firma(r)}.wav")
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", a.audio,
                        "-ss", f"{confini[k]:.3f}", "-to", f"{confini[k+1]:.3f}", "-af",
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                        "silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
                        "aresample=44100", "-ac", "2", out], check=True)
    print(f"FATTO: {len(righe)} frasi in {os.path.relpath(voce.ESTERNA, ROOT)}\n"
          f"  ora: python3 build.py {a.quiz} --formato youtube")
