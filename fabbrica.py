#!/usr/bin/env python3
"""
Tutta la catena in un comando: video -> miniatura -> YouTube.

  python3 fabbrica.py quiz/x.json --non-in-elenco                 # da controllare
  python3 fabbrica.py quiz/x.json --programma "2026-11-03 18:00"  # esce da solo
  python3 fabbrica.py quiz/x.json --solo-video                    # niente YouTube
"""
import argparse, os, subprocess, sys

ROOT = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("quiz")
    ap.add_argument("--solo-video", action="store_true")
    ap.add_argument("--salta-render", action="store_true", help="usa il video gia' in out/")
    a, resto = ap.parse_known_args()

    if not a.salta_render:
        r = subprocess.run([sys.executable, os.path.join(ROOT, "build.py"), a.quiz, "--formato", "youtube"])
        if r.returncode: sys.exit("Render fallito.")
    import miniatura; miniatura.main(a.quiz)
    if a.solo_video:
        print("Fatto (senza pubblicare)."); sys.exit(0)
    import pubblica; pubblica.main([a.quiz] + resto)
