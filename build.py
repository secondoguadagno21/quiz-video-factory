#!/usr/bin/env python3
"""
Quiz Video Factory - motore di render
  python3 build.py quiz/divertenti-italia.json                  # reel verticale
  python3 build.py quiz/cibo.json --formato youtube             # 16:9 lungo
  python3 build.py quiz/cibo.json --formato youtube --max 85    # ~20 minuti
"""
import json, os, subprocess, sys, textwrap, shutil, argparse, time

ROOT = os.path.dirname(os.path.abspath(__file__))
TMP  = os.path.join(ROOT, ".tmp")
REL  = ".tmp"          # i filtri ffmpeg vedono solo percorsi relativi: su Windows
                       # "C:/..." ha i due punti, che per ffmpeg separano le opzioni

def sh(args):
    r = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        print("FFMPEG ERRORE:\n" + r.stderr[-2500:], file=sys.stderr)
        sys.exit(1)
    return r

def txtfile(name, content):
    """Testi su file: cosi' accenti, apostrofi e virgole italiane non rompono drawtext."""
    p = os.path.join(TMP, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return f"{REL}/{name}"

def wrap(s, width):
    return textwrap.wrap(s, width=width) or [""]


class Factory:
    def __init__(self, brand, formato):
        self.b = brand
        fm = brand["formati"][formato]
        self.nome_formato = formato
        self.W, self.H, self.FPS = fm["w"], fm["h"], fm["fps"]
        self.layout = fm["layout"]
        self.tempi  = fm["tempi"]
        self.crf    = brand["video"]["crf"]
        self.preset = brand["video"]["preset"]
        self.c = brand["colori"]
        self.f = {k: p.replace("\\", "/") for k, p in brand["font"].items()}
        for k, p in self.f.items():
            if not os.path.exists(os.path.join(ROOT, p)):
                sys.exit(f"Font mancante per '{k}': {p}")
        self.G = self._geometria()

    def _geometria(self):
        """Misure calcolate sul formato: niente numeri magici copiati a mano."""
        W, H = self.W, self.H
        if self.layout == "griglia":                 # 16:9 YouTube, opzioni 2x2
            cw, ch = int(W*0.435), int(H*0.125)
            gx, gy = int(W*0.021), int(H*0.037)
            x0 = (W - (cw*2 + gx)) // 2
            return dict(
                badge=(int(W*0.042), int(H*0.055), int(W*0.20), int(H*0.065)),
                badge_fs=int(H*0.042), q_y=int(H*0.185), q_fs=int(H*0.062), q_wrap=46,
                q_lh=int(H*0.078), card=(cw, ch), gap=(gx, gy), opt_x0=x0,
                opt_y0=int(H*0.42), lab_w=int(cw*0.115), opt_fs=int(H*0.058),
                lab_fs=int(H*0.068), cd_y=int(H*0.80), cd_fs=int(H*0.145),
                ok_y=int(H*0.855), ok_fs=int(H*0.072),
                tit_fs=int(H*0.105), sub_fs=int(H*0.072), tit_wrap=22,
            )
        cw, ch = W - int(W*0.13), int(H*0.068)       # 9:16 reel, opzioni in colonna
        return dict(
            badge=(int(W*0.055), int(H*0.104), int(W*0.333), int(H*0.047)),
            badge_fs=int(H*0.032), q_y=int(H*0.198), q_fs=int(H*0.034), q_wrap=26,
            q_lh=int(H*0.043), card=(cw, ch), gap=(0, int(H*0.013)),
            opt_x0=int(W*0.065), opt_y0=int(H*0.396), lab_w=int(W*0.102),
            opt_fs=int(H*0.034), lab_fs=int(H*0.040), cd_y=int(H*0.828),
            cd_fs=int(H*0.088), ok_y=int(H*0.833), ok_fs=int(H*0.040),
            tit_fs=int(H*0.056), sub_fs=int(H*0.043), tit_wrap=16,
        )

    # ---------- utilita' di disegno ----------
    def righe(self, tag, lines, font, size, color, y0, lh):
        """Un drawtext per riga: solo cosi' ogni riga e' davvero centrata."""
        out = []
        for i, ln in enumerate(lines):
            tf = txtfile(f"{tag}_{i}.txt", ln)
            out.append(f"drawtext=fontfile='{font}':textfile='{tf}':fontsize={size}"
                       f":fontcolor={color}:x=(w-tw)/2:y={y0 + i*lh}")
        return out

    def opzioni(self, tag, opzioni, giusta=None):
        """Le card delle risposte. giusta=None -> tutte neutre."""
        G, c, f = self.G, self.c, self.f
        cw, ch = G["card"]; gx, gy = G["gap"]
        cols = 2 if self.layout == "griglia" else 1
        vf = []
        for i, op in enumerate(opzioni):
            r, col = divmod(i, cols)
            x = G["opt_x0"] + col*(cw + gx)
            y = G["opt_y0"] + r*(ch + gy)
            if giusta is None:
                box, tcol, lcol = f"{c['card']}@0.96", c["card_testo"], c["sfondo_top"]
            elif i == giusta:
                box, tcol, lcol = c["giusta"], c["testo"], c["testo"]
            else:
                box, tcol, lcol = f"{c['card']}@0.28", f"{c['testo']}@0.45", f"{c['testo']}@0.45"
            vf.append(f"drawbox=x={x}:y={y}:w={cw}:h={ch}:color={box}:t=fill")
            if giusta is None:
                vf.append(f"drawbox=x={x}:y={y}:w={G['lab_w']}:h={ch}:color={c['accento']}:t=fill")
            tl = txtfile(f"{tag}L{i}.txt", "ABCD"[i])
            to = txtfile(f"{tag}T{i}.txt", op)
            vf.append(f"drawtext=fontfile='{f['opzioni']}':textfile='{tl}'"
                      f":fontsize={G['lab_fs']}:fontcolor={lcol}"
                      f":x={x + G['lab_w']//2}-tw/2:y={y + (ch-G['lab_fs'])//2 - int(ch*0.06)}")
            vf.append(f"drawtext=fontfile='{f['opzioni']}':textfile='{to}'"
                      f":fontsize={G['opt_fs']}:fontcolor={tcol}"
                      f":x={x + G['lab_w'] + int(cw*0.04)}:y={y + (ch-G['opt_fs'])//2 - int(ch*0.06)}")
        return vf

    def make_bg(self):
        """Sfondo generato una volta: il filtro gradients si anima e si vedrebbe lo scatto."""
        self.bgpng = f"{REL}/bg.png"
        # sfumatura lineare calcolata riga per riga: chiaro in alto, scuro in basso.
        # (il filtro "gradients" sui formati verticali arriva al colore finale a meta')
        a = int(self.c["sfondo_bottom"], 16); b = int(self.c["sfondo_top"], 16)
        ch = lambda v, sh: (v >> sh) & 255
        expr = lambda sh: f"{ch(a,sh)}+({ch(b,sh)}-{ch(a,sh)})*Y/(H-1)"
        sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
            f"color=c=black:s={self.W}x{self.H}:d=1,format=rgb24,"
            f"geq=r='{expr(16)}':g='{expr(8)}':b='{expr(0)}'",
            "-frames:v", "1", self.bgpng])
        return self.bgpng

    def render(self, name, dur, vfilters, afilter=None):
        out = f"{REL}/{name}"
        chain = ",".join(vfilters) if vfilters else "null"
        a_in = afilter or f"anullsrc=r=44100:cl=stereo:d={dur}"
        sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-loop", "1", "-t", str(dur), "-i", self.bgpng,
            "-f", "lavfi", "-i", a_in,
            "-filter_complex", f"[0:v]{chain},format=yuv420p[v]",
            "-map", "[v]", "-map", "1:a", "-t", str(dur), "-r", str(self.FPS),
            "-c:v", "libx264", "-preset", self.preset, "-crf", str(self.crf),
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", out])
        return out

    # ---------- segmenti ----------
    def intro(self, titolo, sottotitolo, dur):
        G, c, f = self.G, self.c, self.f
        y = int(self.H*0.30)
        vf  = [f"drawbox=x=0:y={y-int(self.H*0.04)}:w={self.W}:h={max(6,int(self.H*0.005))}"
               f":color={c['accento']}:t=fill"]
        vf += self.righe("itit", wrap(titolo, G["tit_wrap"]), f["titolo"],
                         G["tit_fs"], c["testo"], y, int(G["tit_fs"]*1.12))
        y2 = y + int(self.H*0.20)
        vf += self.righe("isub", wrap(sottotitolo, G["tit_wrap"]+6), f["opzioni"],
                         G["sub_fs"], c["accento"], y2, int(G["sub_fs"]*1.12))
        vf += [f"drawbox=x=0:y={y2+int(self.H*0.10)}:w={self.W}"
               f":h={max(6,int(self.H*0.005))}:color={c['accento']}:t=fill"]
        return self.render("00_intro.mp4", dur, vf,
                           afilter=f"sine=frequency=520:duration=0.18,apad=whole_dur={dur}")

    def domanda(self, idx, q, opzioni, dur):
        G, c, f = self.G, self.c, self.f
        bx, by, bw, bh = G["badge"]
        tf = txtfile(f"qn{idx}.txt", f"DOMANDA {idx+1}")
        vf  = [f"drawbox=x={bx}:y={by}:w={bw}:h={bh}:color={c['accento']}:t=fill"]
        vf += [f"drawtext=fontfile='{f['opzioni']}':textfile='{tf}':fontsize={G['badge_fs']}"
               f":fontcolor={c['sfondo_top']}:x={bx+int(bw*0.08)}:y={by+(bh-G['badge_fs'])//2-int(bh*0.08)}"]
        vf += self.righe(f"qt{idx}", wrap(q, G["q_wrap"]), f["domanda"],
                         G["q_fs"], c["testo"], G["q_y"], G["q_lh"])
        vf += self.opzioni(f"o{idx}", opzioni)
        n = int(dur)
        vf += [f"drawtext=fontfile='{f['titolo']}':text='%{{eif\\:max(0\\,{n}-t)\\:d}}'"
               f":fontsize={G['cd_fs']}:fontcolor={c['countdown']}:x=(w-tw)/2:y={G['cd_y']}"]
        ticks = "".join(f"sine=frequency=880:duration=0.06,adelay={i*1000}|{i*1000}[t{i}];"
                        for i in range(n))
        a = f"{ticks}{''.join(f'[t{i}]' for i in range(n))}amix=inputs={n}:duration=longest,apad=whole_dur={dur}"
        return self.render(f"10_q{idx:04d}.mp4", dur, vf, afilter=a)

    def risposta(self, idx, q, opzioni, giusta, dur, spiega=None):
        G, c, f = self.G, self.c, self.f
        vf  = self.righe(f"rt{idx}", wrap(q, G["q_wrap"]), f["domanda"],
                         int(G["q_fs"]*0.88), f"{c['testo']}@0.75", G["q_y"], G["q_lh"])
        vf += self.opzioni(f"r{idx}", opzioni, giusta)
        testo = spiega or "RISPOSTA GIUSTA"
        vf += self.righe(f"rok{idx}", wrap(testo, G["q_wrap"]+8), f["titolo"],
                         G["ok_fs"], c["giusta"], G["ok_y"], int(G["ok_fs"]*1.12))
        return self.render(f"20_r{idx:04d}.mp4", dur, vf,
                           afilter=f"sine=frequency=1180:duration=0.35,apad=whole_dur={dur}")

    def outro(self, cta, brand, dur):
        G, c, f = self.G, self.c, self.f
        y = int(self.H*0.33)
        vf  = self.righe("octa", wrap(cta, G["tit_wrap"]), f["titolo"],
                         int(G["tit_fs"]*0.9), c["testo"], y, int(G["tit_fs"]*1.05))
        vf += [f"drawbox=x=0:y={int(self.H*0.62)}:w={self.W}"
               f":h={max(6,int(self.H*0.005))}:color={c['accento']}:t=fill"]
        vf += self.righe("obr", wrap(brand, G["tit_wrap"]+6), f["cta"],
                         G["sub_fs"], c["accento"], int(self.H*0.68), int(G["sub_fs"]*1.1))
        return self.render("90_outro.mp4", dur, vf,
                           afilter=f"sine=frequency=660:duration=0.3,apad=whole_dur={dur}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("quiz")
    ap.add_argument("--formato", default="reel", choices=["reel", "youtube"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--music", default=None)
    ap.add_argument("--music-vol", type=float, default=None)
    ap.add_argument("--no-music", action="store_true")
    a = ap.parse_args()

    brand = json.load(open(os.path.join(ROOT, "brand.json"), encoding="utf-8"))
    data  = json.load(open(a.quiz, encoding="utf-8"))
    if a.music: a.music = os.path.abspath(a.music)
    dom   = data["domande"][:a.max] if a.max else data["domande"]

    shutil.rmtree(TMP, ignore_errors=True); os.makedirs(TMP, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)

    fac = Factory(brand, a.formato); fac.make_bg()
    t = fac.tempi
    attesa = t["intro"] + t["outro"] + len(dom)*(t["domanda"] + t["risposta"])
    print(f"formato {a.formato} {fac.W}x{fac.H} · {len(dom)} domande · "
          f"durata prevista {int(attesa)//60}m {int(attesa)%60:02d}s")

    t0 = time.time(); segs = [fac.intro(data["titolo"], data.get("sottotitolo",""), t["intro"])]
    for i, d in enumerate(dom):
        if i % 10 == 0 or len(dom) <= 10:
            print(f"  domanda {i+1}/{len(dom)}", flush=True)
        segs.append(fac.domanda(i, d["q"], d["opzioni"], t["domanda"]))
        segs.append(fac.risposta(i, d["q"], d["opzioni"], d["giusta"],
                                 t["risposta"], d.get("spiegazione")))
    segs.append(fac.outro(brand["cta_finale"], brand["brand"], t["outro"]))

    lst = os.path.join(TMP, "lista.txt")
    with open(lst, "w") as f:
        for s in segs: f.write(f"file '{os.path.basename(s)}'\n")   # relativi alla lista
    out = os.path.abspath(a.out) if a.out else os.path.join(ROOT, "out",
            f"{os.path.splitext(os.path.basename(a.quiz))[0]}-{a.formato}.mp4")

    print("  montaggio")
    muto = f"{REL}/montato.mp4"
    sh(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0",
        "-i",f"{REL}/lista.txt","-c","copy",muto])

    if a.no_music:
        shutil.move(os.path.join(ROOT, muto), out)
    else:
        dur = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                                    "-of","csv=p=0",muto],capture_output=True,text=True,cwd=ROOT).stdout.strip())
        bed = a.music
        if not bed:
            cart = os.path.join(ROOT,"assets","audio")
            tuoi = [f for f in sorted(os.listdir(cart))
                    if f.lower().endswith((".mp3",".m4a",".wav",".aac"))] if os.path.isdir(cart) else []
            if tuoi:
                bed = os.path.join(cart, tuoi[0]); print(f"  musica: {tuoi[0]} (tua)")
            else:
                bed = f"{REL}/bed_auto.wav"; print(f"  musica: generata ({dur:.0f}s)")
                sh([sys.executable, os.path.join(ROOT,"make_music.py"),
                    "--dur", f"{min(dur,180):.2f}", "--out", bed])
        vol = a.music_vol if a.music_vol is not None else brand.get("audio",{}).get("volume_musica",0.40)
        print(f"  mix finale (musica al {int(vol*100)}%)")
        sh(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",muto,
            "-stream_loop","-1","-i",bed,"-filter_complex",
            f"[1:a]volume={vol},afade=t=in:st=0:d=1.2,"
            f"afade=t=out:st={max(0,dur-1.5):.2f}:d=1.5[m];"
            f"[0:a]aformat=channel_layouts=stereo[v0];"
            f"[v0][m]amix=inputs=2:duration=first:normalize=0,"
            f"aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,"
            f"alimiter=limit=0.97[a]",
            "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k",
            "-ac","2","-ar","44100","-t",f"{dur:.2f}","-movflags","+faststart",out])

    d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                              "-of","csv=p=0",out],capture_output=True,text=True).stdout.strip())
    el = time.time()-t0
    print(f"\nFATTO: {out}\n  {int(d)//60}m {int(d)%60:02d}s · {os.path.getsize(out)/1e6:.1f} MB "
          f"· {len(dom)} domande\n  render in {int(el)//60}m {int(el)%60:02d}s "
          f"({el/d:.2f}x il tempo reale)")

if __name__ == "__main__":
    main()
