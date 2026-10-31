#!/usr/bin/env python3
"""
Generatore di musica di sottofondo originale per i video quiz.
Nessun copyright, nessuno strike: le note le calcoliamo noi.
Uso: python3 make_music.py --dur 45 --out assets/audio/bed.wav
"""
import numpy as np, wave, argparse, os, struct

SR  = 44100
BPM = 100.0
BEAT = 60.0 / BPM           # 0.6s
BAR  = 4 * BEAT             # 2.4s

def nt(n):
    """MIDI -> Hz"""
    return 440.0 * (2.0 ** ((n - 69) / 12.0))

def env(n, a, d, s, r, sus=0.7):
    """Inviluppo ADSR su n campioni."""
    a, d, r = int(a*SR), int(d*SR), int(r*SR)
    s = max(0, n - a - d - r)
    return np.concatenate([
        np.linspace(0, 1, a, endpoint=False) if a else np.array([]),
        np.linspace(1, sus, d, endpoint=False) if d else np.array([]),
        np.full(s, sus),
        np.linspace(sus, 0, r) if r else np.array([]),
    ])[:n]

def saw(f, n, detune=0.0):
    t = np.arange(n) / SR
    out = np.zeros(n)
    for h in range(1, 12):                       # saw per armoniche: morbido, non aliasato
        out += np.sin(2*np.pi*f*h*t) / h
    if detune:
        for h in range(1, 12):
            out += np.sin(2*np.pi*f*(1+detune)*h*t) / h * 0.7
    return out / 3.0

def sine(f, n):
    return np.sin(2*np.pi*f*np.arange(n)/SR)

def add(buf, sig, at):
    i = int(at * SR)
    j = min(len(buf), i + len(sig))
    if i < len(buf):
        buf[i:j] += sig[:j-i]

def kick(dur=0.22):
    n = int(dur*SR); t = np.arange(n)/SR
    f = 110 * np.exp(-t*28) + 48                 # pitch drop: il "tump"
    s = np.sin(2*np.pi*np.cumsum(f)/SR)
    return s * np.exp(-t*14) * 0.9

def hat(dur=0.05, lvl=0.18):
    n = int(dur*SR)
    s = np.random.uniform(-1, 1, n)
    s = np.diff(np.concatenate([[0], s]))        # derivata = passa-alto povero
    return s * np.exp(-np.arange(n)/SR*90) * lvl

def clap(dur=0.18, lvl=0.33):
    n = int(dur*SR)
    s = np.random.uniform(-1, 1, n)
    s = np.diff(np.concatenate([[0], s]))
    e = np.exp(-np.arange(n)/SR*22)
    return s * e * lvl

def build(dur):
    total = int(dur*SR) + SR
    bass = np.zeros(total); chords = np.zeros(total)
    arp  = np.zeros(total); drums  = np.zeros(total)

    # Am - F - C - G  (vi-IV-I-V): la progressione che tiene su l'energia
    prog = [(57, [57,60,64]), (53, [57,60,65]), (48, [55,60,64]), (55, [55,59,62])]

    nbars = int(dur / BAR) + 2
    for b in range(nbars):
        t0 = b * BAR
        root, triad = prog[b % 4]

        # BASSO: due note per battuta, pulsa
        for k in (0, 2):
            n = int(BEAT*0.9*SR)
            e = env(n, .005, .05, 0, .12, .85)
            b = (sine(nt(root-12), n)*0.55      # sub: si sente in cuffia
                 + sine(nt(root), n)*0.60       # corpo: si sente sul telefono
                 + saw(nt(root), n)*0.30)       # armoniche: taglia nel mix
            add(bass, b * e * 0.42, t0 + k*BEAT)

        # ACCORDI: pad tenuto, volutamente basso
        n = int(BAR*0.95*SR)
        for m in triad:
            add(chords, saw(nt(m), n, 0.006) * env(n, .12, .25, 0, .5, .55) * 0.14, t0)

        # ARPEGGIO: ottavi, e' lui che da' il senso di "gioco"
        seq = [triad[0], triad[1], triad[2], triad[1], triad[2], triad[1], triad[2], triad[0]]
        for k, m in enumerate(seq):
            n = int(BEAT*0.42*SR)
            e = env(n, .004, .07, 0, .13, .25)
            a2 = saw(nt(m+12), n)*1.0 + saw(nt(m+24), n)*0.45 + sine(nt(m+24), n)*0.30
            add(arp, a2 * e * 0.30, t0 + k*BEAT*0.5)

        # RITMICA
        for k in (0, 2):  add(drums, kick(), t0 + k*BEAT)
        for k in (1, 3):  add(drums, clap(), t0 + k*BEAT)
        for k in range(8): add(drums, hat(), t0 + k*BEAT*0.5)

    mix = bass*0.62 + chords*1.0 + arp*1.15 + drums*0.80

    # high-shelf semplice: alza i medio-alti, cosi' regge sugli altoparlanti piccoli
    hp = mix - np.convolve(mix, np.ones(28)/28, mode="same")
    mix = mix + hp*0.55
    mix = mix[:int(dur*SR)]

    # dissolvenze: entra e esce senza schiaffi
    f = int(1.2*SR)
    if len(mix) > 2*f:
        mix[:f]  *= np.linspace(0, 1, f)
        mix[-f:] *= np.linspace(1, 0, f)

    # limite morbido + normalizzazione a -3 dBFS
    mix = np.tanh(mix * 1.15)
    peak = np.abs(mix).max()
    if peak > 0:
        mix = mix / peak * 0.707
    return mix

def save(mix, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    st = np.stack([mix, mix], axis=1)                 # stereo
    pcm = (st * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes())

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dur", type=float, default=45.0)
    ap.add_argument("--out", default="assets/audio/bed.wav")
    a = ap.parse_args()
    np.random.seed(7)
    save(build(a.dur), a.out)
    print(f"Musica generata: {a.out}  ({a.dur:.1f}s, {BPM:.0f} BPM, Am-F-C-G)")
