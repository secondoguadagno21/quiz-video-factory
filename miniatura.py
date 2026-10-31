#!/usr/bin/env python3
"""
Miniatura YouTube 1280x720 coi colori del brand.
I testi vengono da quiz["youtube"]["miniatura"]: riga1, riga2, badge.

  python3 miniatura.py quiz/cultura-generale-genio.json
"""
import json, os, subprocess, sys, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
TMP, REL = os.path.join(ROOT, ".tmp_mini"), ".tmp_mini"     # separata da .tmp di build.py

def main(quiz_path, out=None):
    b = json.load(open(os.path.join(ROOT, "brand.json"), encoding="utf-8"))
    q = json.load(open(quiz_path, encoding="utf-8"))
    m = q.get("youtube", {}).get("miniatura") or {}
    r1, r2 = m.get("riga1", q["titolo"]), m.get("riga2", "")
    badge = m.get("badge", q.get("sottotitolo", ""))
    c, f = b["colori"], {k: v.replace("\\", "/") for k, v in b["font"].items()}
    W, H = 1280, 720
    out = out or os.path.join(ROOT, "out",
                              os.path.splitext(os.path.basename(quiz_path))[0] + "-miniatura.jpg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    shutil.rmtree(TMP, ignore_errors=True); os.makedirs(TMP)

    def t(nome, testo):
        open(os.path.join(TMP, nome), "w", encoding="utf-8").write(testo); return f"{REL}/{nome}"

    vf = [
        # fascia accento in alto con badge
        f"drawbox=x=0:y=0:w={W}:h=16:color={c['accento']}:t=fill",
        f"drawbox=x=60:y=60:w=420:h=92:color={c['sbagliata']}:t=fill",
        f"drawtext=fontfile='{f['opzioni']}':textfile='{t('b.txt', badge)}':fontsize=70"
        f":fontcolor=white:x=60+(420-tw)/2:y=60+(92-th)/2",
        # due righe enormi, la seconda in giallo
        f"drawtext=fontfile='{f['titolo']}':textfile='{t('r1.txt', r1)}':fontsize=150"
        f":fontcolor={c['testo']}:borderw=6:bordercolor=black@0.55:x=(w-tw)/2:y=215",
        f"drawtext=fontfile='{f['titolo']}':textfile='{t('r2.txt', r2)}':fontsize=150"
        f":fontcolor={c['accento']}:borderw=6:bordercolor=black@0.55:x=(w-tw)/2:y=405",
        # quattro tessere A B C D in basso: si capisce subito che e' un quiz
    ]
    for i, L in enumerate("ABCD"):
        x = 140 + i*265
        col = c["giusta"] if i == 2 else c["card"]
        vf += [f"drawbox=x={x}:y=600:w=220:h=80:color={col}:t=fill",
               f"drawtext=fontfile='{f['opzioni']}':textfile='{t(f'l{L}.txt', L)}':fontsize=66"
               f":fontcolor={c['card_testo']}:x={x}+(220-tw)/2:y=600+(80-th)/2"]
    r = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                        f"gradients=s={W}x{H}:c0={c['sfondo_top']}:c1={c['sfondo_bottom']}"
                        f":x0=0:y0=0:x1=0:y1={H}:d=1", "-frames:v", "1",
                        "-vf", ",".join(vf), "-q:v", "3", out], capture_output=True, text=True, cwd=ROOT)
    shutil.rmtree(TMP, ignore_errors=True)
    if r.returncode: sys.exit("ffmpeg: " + r.stderr[-1500:])
    print(f"Miniatura: {out}")
    return out

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
