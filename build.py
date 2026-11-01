#!/usr/bin/env python3
"""
Quiz Video Factory - motore di render (brand Quiz Divertenti Italia)
  python3 build.py quiz/divertenti-italia.json                  # reel verticale
  python3 build.py quiz/cibo.json --formato youtube             # 16:9 lungo
  python3 build.py quiz/cibo.json --formato youtube --max 85    # ~20 minuti

Le grafiche ufficiali (intro, transizione, barra, CTA, outro, logo, effetti, musica,
sfondi) sono elencate in brand.json -> "risorse". Se un file manca, il motore usa
la versione generata, cosi' un video esce sempre.
"""
import json, os, re, subprocess, sys, textwrap, shutil, argparse, time
import grafica, voce

ROOT = os.path.dirname(os.path.abspath(__file__))
TMP  = os.path.join(ROOT, ".tmp")
REL  = ".tmp"          # i filtri ffmpeg vedono solo percorsi relativi: su Windows
                       # "C:/..." ha i due punti, che per ffmpeg separano le opzioni
AUDIO_EXT = (".mp3", ".m4a", ".wav", ".aac", ".ogg")
REG_MUSICA = os.path.join(ROOT, "musica-usata.json")


def sh(args):
    r = subprocess.run(args, capture_output=True, text=True, cwd=ROOT)
    if r.returncode != 0:
        print("FFMPEG ERRORE:\n" + r.stderr[-2500:], file=sys.stderr)
        sys.exit(1)
    return r

def ffmpeg(*args):
    return sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args])

def durata(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True, cwd=ROOT).stdout
    try: return float(out.strip())
    except ValueError: return 0.0

def ha_audio(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                          "stream=index", "-of", "csv=p=0", path], capture_output=True, text=True, cwd=ROOT).stdout
    return bool(out.strip())

def txtfile(name, content):
    """Testi su file: cosi' accenti, apostrofi e virgole italiane non rompono drawtext."""
    p = os.path.join(TMP, name)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)
    return f"{REL}/{name}"

def wrap(s, width):
    return textwrap.wrap(s, width=width) or [""]

def mmss(s):
    s = int(round(s)); return f"{s//60}:{s%60:02d}"


class Factory:
    def __init__(self, brand, formato, rotazione=0):
        self.b = brand
        fm = brand["formati"][formato]
        self.nome_formato = formato
        self.W, self.H, self.FPS = fm["w"], fm["h"], fm["fps"]
        self.layout = fm["layout"]
        self.tempi  = fm["tempi"]
        self.clip_brand = fm.get("clip_brand", False)
        self.crf    = brand["video"]["crf"]
        self.preset = brand["video"]["preset"]
        self.c = brand["colori"]
        self.f = {k: p.replace("\\", "/") for k, p in brand["font"].items()}
        for k, p in self.f.items():
            if not os.path.exists(os.path.join(ROOT, p)):
                sys.exit(f"Font mancante per '{k}': {p}")
        self.G = self._geometria()
        self.rot = rotazione
        # risorse ufficiali: solo quelle che esistono davvero
        R = brand.get("risorse", {})
        ok = lambda p: p if p and os.path.exists(os.path.join(ROOT, p)) else None
        self.R = {k: ok(R.get(k)) for k in ("intro", "transizione", "cta", "outro",
                                             "barra", "logo", "mascotte")}
        self.logo_crop = R.get("logo_ritaglio")
        self.sfx = {k: ok(v) for k, v in R.get("sfx", {}).items()}
        self.sfondi_dir = ok(R.get("sfondi"))
        self.barra_len = durata(self.R["barra"]) if self.R["barra"] else 0
        # linea del tempo: serve per i capitoli e per abbassare la musica sulle clip
        self.clock, self.capitoli, self.silenzio, self.attenua = 0.0, [], [], []
        self.voce = voce.attiva()

    def _geometria(self):
        """Misure calcolate sul formato: niente numeri magici copiati a mano."""
        W, H = self.W, self.H
        if self.layout == "griglia":                 # 16:9 YouTube, opzioni 2x2
            cw, ch = int(W*0.435), int(H*0.125)
            gx, gy = int(W*0.021), int(H*0.037)
            x0 = (W - (cw*2 + gx)) // 2
            bw = int(W*0.62)
            return dict(
                badge=(int(W*0.042), int(H*0.055), int(W*0.20), int(H*0.065)),
                badge_fs=int(H*0.042), q_y=int(H*0.185), q_fs=int(H*0.062), q_wrap=46,
                q_lh=int(H*0.078), card=(cw, ch), gap=(gx, gy), opt_x0=x0,
                opt_y0=int(H*0.42), lab_w=int(cw*0.115), opt_fs=int(H*0.058),
                lab_fs=int(H*0.068), cd_y=int(H*0.80), cd_fs=int(H*0.145),
                ok_y=int(H*0.855), ok_fs=int(H*0.072),
                tit_fs=int(H*0.105), sub_fs=int(H*0.072), tit_wrap=22,
                barra=(x0, int(H*0.735), cw*2 + gx, int(H*0.024)),     # barra generata
                barra_qdi=((W-bw)//2, int(H*0.725), bw),                # barra ufficiale
                logo=(int(H*0.15), int(H*0.025)), masc_h=int(H*0.26),
                badge_d=int(H*0.13), badge_xy=(int(W*0.025), int(H*0.03)),
            )
        cw, ch = W - int(W*0.13), int(H*0.068)       # 9:16 reel, opzioni in colonna
        bw = int(W*0.93)
        return dict(
            badge=(int(W*0.055), int(H*0.104), int(W*0.333), int(H*0.047)),
            badge_fs=int(H*0.032), q_y=int(H*0.198), q_fs=int(H*0.034), q_wrap=26,
            q_lh=int(H*0.043), card=(cw, ch), gap=(0, int(H*0.013)),
            opt_x0=int(W*0.065), opt_y0=int(H*0.396), lab_w=int(W*0.102),
            opt_fs=int(H*0.034), lab_fs=int(H*0.040), cd_y=int(H*0.828),
            cd_fs=int(H*0.088), ok_y=int(H*0.833), ok_fs=int(H*0.040),
            tit_fs=int(H*0.056), sub_fs=int(H*0.043), tit_wrap=16,
            barra=(int(W*0.065), int(H*0.745), cw, int(H*0.014)),
            barra_qdi=((W-bw)//2, int(H*0.725), bw),
            logo=(int(H*0.085), int(H*0.02)), masc_h=int(H*0.14),
            badge_d=int(H*0.07), badge_xy=(int(W*0.05), int(H*0.085)),
        )

    # ---------- utilita' di disegno ----------
    def righe(self, tag, lines, font, size, color, y0, lh, bordo=0):
        """Un drawtext per riga: solo cosi' ogni riga e' davvero centrata."""
        out = []
        b = f":borderw={bordo}:bordercolor=black@0.6" if bordo else ""
        for i, ln in enumerate(lines):
            tf = txtfile(f"{tag}_{i}.txt", ln)
            # expansion=none: un "78%" nel testo e' testo, non un comando di drawtext
            out.append(f"drawtext=fontfile='{font}':textfile='{tf}':expansion=none:fontsize={size}"
                       f":fontcolor={color}{b}:x=(w-tw)/2:y={y0 + i*lh}")
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
                box, tcol, lcol = f"{c['card']}@0.97", c["card_testo"], c["card_testo"]
            elif i == giusta:
                box, tcol, lcol = c["giusta"], c["testo"], c["testo"]
            else:
                box, tcol, lcol = f"{c['card']}@0.28", f"{c['testo']}@0.5", f"{c['testo']}@0.5"
            sh_ = max(4, ch//14)                       # ombra: stacca le card dallo sfondo
            vf.append(f"drawbox=x={x+sh_}:y={y+sh_}:w={cw}:h={ch}:color=black@0.25:t=fill")
            vf.append(f"drawbox=x={x}:y={y}:w={cw}:h={ch}:color={box}:t=fill")
            if giusta is None:
                vf.append(f"drawbox=x={x}:y={y}:w={G['lab_w']}:h={ch}:color={c['accento']}:t=fill")
            tl = txtfile(f"{tag}L{i}.txt", "ABCD"[i])
            to = txtfile(f"{tag}T{i}.txt", op)
            vf.append(f"drawtext=fontfile='{f['opzioni']}':textfile='{tl}':expansion=none"
                      f":fontsize={G['lab_fs']}:fontcolor={lcol}"
                      f":x={x + G['lab_w']//2}-tw/2:y={y + (ch-G['lab_fs'])//2 - int(ch*0.06)}")
            vf.append(f"drawtext=fontfile='{f['opzioni']}':textfile='{to}':expansion=none"
                      f":fontsize={G['opt_fs']}:fontcolor={tcol}"
                      f":x={x + G['lab_w'] + int(cw*0.04)}:y={y + (ch-G['opt_fs'])//2 - int(ch*0.06)}")
        return vf

    def parla(self, testo):
        """(percorso_wav, durata) oppure (None, 0) se la voce non e' attiva."""
        if not self.voce: return None, 0.0
        p = voce.di(testo)
        return p, durata(p)

    def png_badge(self, n):
        d = self.G["badge_d"]
        out = os.path.join(TMP, f"badge{n}.png")
        if not os.path.exists(out): grafica.badge(n, d, self.c, self.f, out)
        pad = d // 8
        return (f"{REL}/badge{n}.png", self.G["badge_xy"][0] - pad, self.G["badge_xy"][1] - pad)

    def png_card(self, tag, i, testo, stato):
        G = self.G
        cw, ch = G["card"]; gx, gy = G["gap"]
        cols = 2 if self.layout == "griglia" else 1
        r, col = divmod(i, cols)
        x = G["opt_x0"] + col*(cw + gx); y = G["opt_y0"] + r*(ch + gy)
        nome = f"card_{tag}_{i}_{stato}.png"
        _, pad = grafica.card(cw, ch, "ABCD"[i], testo, stato, self.c, self.f, os.path.join(TMP, nome))
        return (f"{REL}/{nome}", x - pad, y - pad)

    # ---------- sfondo ----------
    def make_bg(self):
        """Sfumatura blu del brand; se c'e' uno sfondo animato QDI (punti interrogativi)
        lo stampa sopra in trasparenza e lo mette in loop continuo tra uno spezzone e l'altro."""
        self.bgpng = f"{REL}/bg.png"
        a = int(self.c["sfondo_bottom"], 16); b = int(self.c["sfondo_top"], 16)
        ch = lambda v, sh: (v >> sh) & 255
        expr = lambda sh: f"{ch(a,sh)}+({ch(b,sh)}-{ch(a,sh)})*Y/(H-1)"
        ffmpeg("-f", "lavfi", "-i",
               f"color=c=black:s={self.W}x{self.H}:d=1,format=rgb24,"
               f"geq=r='{expr(16)}':g='{expr(8)}':b='{expr(0)}'", "-frames:v", "1", self.bgpng)
        self.bgvid, self.bglen = None, 0
        sf = sorted(x for x in os.listdir(os.path.join(ROOT, self.sfondi_dir))
                    if x.lower().endswith((".mp4", ".mov"))) if self.sfondi_dir else []
        if sf:
            src = f"{self.sfondi_dir}/{sf[self.rot % len(sf)]}"
            self.bgvid = f"{REL}/bg.mp4"
            ffmpeg("-loop", "1", "-i", self.bgpng, "-i", src, "-filter_complex",
                   f"[1:v]scale={self.W}:{self.H}:force_original_aspect_ratio=increase,"
                   f"crop={self.W}:{self.H},fps={self.FPS},format=gbrp[s];"
                   f"[0:v]fps={self.FPS},format=gbrp[g];"
                   f"[g][s]blend=all_mode=multiply:shortest=1,format=yuv420p",
                   "-an", "-c:v", "libx264", "-preset", self.preset, "-crf", "18",
                   "-g", str(self.FPS), self.bgvid)
            self.bglen = durata(self.bgvid)
            print(f"  sfondo: {sf[self.rot % len(sf)]}")
        return self.bgpng

    # ---------- audio degli spezzoni ----------
    def suoni(self, nome, dur, eventi):
        """eventi = [(tipo_sfx, secondo)]. Usa gli effetti QDI; se mancano, un bip sintetico."""
        bip = {"domanda": 700, "tick": 880, "giusta": 1180, "livello": 520}
        args, parti = [], []
        for i, (tipo, t) in enumerate(eventi):
            if tipo.startswith("voce:"):                     # frase della voce narrante
                args += ["-i", tipo[5:]]; vol = 1.6
            else:
                f = self.sfx.get(tipo)
                if f: args += ["-i", f]
                else: args += ["-f", "lavfi", "-i", f"sine=frequency={bip[tipo]}:duration=0.12"]
                vol = 0.55 if tipo == "tick" else 0.9
            ms = int(t*1000)
            parti.append(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo,"
                         f"volume={vol},adelay={ms}|{ms}[e{i}]")
        out = f"{REL}/{nome}.wav"
        if not eventi:
            ffmpeg("-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={dur}", out); return out
        mix = "".join(f"[e{i}]" for i in range(len(eventi)))
        ffmpeg(*args, "-filter_complex",
               ";".join(parti) + f";{mix}amix=inputs={len(eventi)}:duration=longest:normalize=0,"
               f"apad=whole_dur={dur},atrim=0:{dur}", "-ar", "44100", "-ac", "2", out)
        return out

    # ---------- render di uno spezzone grafico ----------
    def png_raggi(self):
        out = os.path.join(TMP, "raggi.png")
        if not os.path.exists(out): grafica.raggi(int(self.H*1.5), grafica.rgb(self.c["accento"]), out)
        return f"{REL}/raggi.png"

    def seq_coriandoli(self):
        """Sequenza unica per tutto il video: si riusa a ogni risposta giusta."""
        w, h = int(self.W*0.5), int(self.H*0.62)
        pat = os.path.join(TMP, "cor_%02d.png")
        if not os.path.exists(pat % 0):
            col = [grafica.rgb(self.c[k]) for k in ("accento", "giusta", "card")] + [grafica.rgb("4FC3FF")]
            grafica.coriandoli(w, h, col, 36, pat)
        return f"{REL}/cor_%02d.png", w, h

    def anima(self, livello, curva, tag):
        """(png, x, y) -> (sequenza, x, y): la grafica entra con un rimbalzo."""
        path, x, y = livello
        pat = os.path.join(TMP, f"{tag}_%02d.png")
        dx, dy = grafica.sequenza_scala(os.path.join(ROOT, path), curva, pat)
        return (f"{REL}/{tag}_%02d.png", x - dx, y - dy)

    def render(self, name, dur, vfilters, audio=None, barra=False, logo=True, mascotte=None, livelli=(),
               raggi=False):
        out = f"{REL}/{name}"
        chain = ",".join(vfilters) if vfilters else "null"
        args = []
        if self.bgvid:      # lo sfondo animato riparte da dove era arrivato: nessuno scatto
            args += ["-stream_loop", "-1", "-ss", f"{self.clock % self.bglen:.3f}",
                     "-t", f"{dur}", "-i", self.bgvid]
        else:
            args += ["-loop", "1", "-t", f"{dur}", "-i", self.bgpng]
        args += ["-i", audio] if audio else ["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={dur}"]
        n = 2
        if raggi:           # raggi di luce che girano lenti, sotto i testi
            args += ["-loop", "1", "-t", f"{dur}", "-i", self.png_raggi()]
            fc = [f"[{n}:v]format=rgba,rotate=a='t*0.35':c=none:ow=iw:oh=ih[rg];"
                  f"[0:v][rg]overlay=(W-w)/2:(H-h)/2[b0];[b0]{chain}[v0]"]
            n += 1
        else:
            fc = [f"[0:v]{chain}[v0]"]
        cur = "v0"
        for path, x, y, comparsa in livelli:               # grafiche PNG (badge, card)
            if "%" in path:                                # sequenza animata (rimbalzo, coriandoli)
                args += ["-framerate", str(self.FPS), "-i", path]
                fc.append(f"[{n}:v]format=rgba,setpts=PTS+{comparsa or 0:.3f}/TB[g{n}];"
                          f"[{cur}][g{n}]overlay={x}:{y}:eof_action=repeat[v{n}]")
            else:
                args += ["-loop", "1", "-t", f"{dur}", "-i", path]
                fade = f"format=rgba,fade=t=in:st={comparsa:.2f}:d=0.18:alpha=1," if comparsa else ""
                fc.append(f"[{n}:v]{fade}null[g{n}];[{cur}][g{n}]overlay={x}:{y}[v{n}]")
            cur, n = f"v{n}", n+1
        if logo and self.R["logo"]:                         # icona QDI in alto a destra
            lh, ly = self.G["logo"]
            cr = self.logo_crop
            crop = f"crop={cr[0]}:{cr[1]}:{cr[2]}:{cr[3]}," if cr else ""
            args += ["-loop", "1", "-t", f"{dur}", "-i", self.R["logo"]]
            fc.append(f"[{n}:v]{crop}scale=-1:{lh}[lg];[{cur}][lg]overlay=W-w-{int(self.W*0.025)}:{ly}[v{n}]")
            cur, n = f"v{n}", n+1
        if mascotte and self.R["mascotte"]:
            mh, my = mascotte
            args += ["-loop", "1", "-t", f"{dur}", "-i", self.R["mascotte"]]
            fc.append(f"[{n}:v]scale=-1:{mh}[ms];[{cur}][ms]overlay=(W-w)/2:{my}[v{n}]")
            cur, n = f"v{n}", n+1
        if barra and self.R["barra"]:                       # barra ufficiale QDI, ultimi 5 s
            bx, by, bw = self.G["barra_qdi"]
            start = max(0.0, dur - self.barra_len)
            vel = min(1.0, dur / self.barra_len)              # se la domanda e' piu' corta
            args += ["-i", self.R["barra"]]
            fc.append(f"[{n}:v]scale={bw}:-1,setpts=PTS*{vel:.4f}+{start:.3f}/TB[br];"
                      f"[{cur}][br]overlay={bx}:{by}:eof_action=pass[v{n}]")
            cur, n = f"v{n}", n+1
        elif barra:                                         # ripiego: barra generata
            bx, by, bw, bh = self.G["barra"]
            trk = self.c.get("barra_traccia", "0x2A3A80")
            fc.append(f"color=c={trk}:s={bw}x{bh}:r={self.FPS}:d={dur}[trk];"
                      f"color=c={self.c['accento']}:s={bw}x{bh}:r={self.FPS}:d={dur}[pie];"
                      f"[trk][pie]overlay=x='-{bw}*t/{dur}':y=0:eval=frame[bar];"
                      f"[{cur}][bar]overlay={bx}:{by}:shortest=1[vb]")
            cur = "vb"
        fc.append(f"[{cur}]format=yuv420p[v]")
        ffmpeg(*args, "-filter_complex", ";".join(fc),
               "-map", "[v]", "-map", "1:a", "-t", f"{dur}", "-r", str(self.FPS),
               "-c:v", "libx264", "-preset", self.preset, "-crf", str(self.crf),
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2", out)
        self.clock += dur
        return out

    # ---------- clip ufficiali (intro, transizione, CTA, outro) ----------
    def clip(self, name, chiave, musica="silenzio"):
        """Ricodifica la clip QDI nello stesso formato degli spezzoni, cosi' si montano
        senza ricodificare tutto. musica: 'silenzio' | 'attenua' | 'normale'."""
        src = self.R[chiave]
        d = durata(src)
        out = f"{REL}/{name}"
        a = ["-i", src] if ha_audio(src) else ["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo:d={d}"]
        amap = "0:a" if ha_audio(src) else "1:a"
        ffmpeg("-i", src, *(a[2:] if ha_audio(src) else a),
               "-vf", f"scale={self.W}:{self.H}:force_original_aspect_ratio=decrease,"
                      f"pad={self.W}:{self.H}:(ow-iw)/2:(oh-ih)/2,fps={self.FPS},format=yuv420p",
               "-map", "0:v", "-map", amap, "-t", f"{d}", "-r", str(self.FPS),
               "-c:v", "libx264", "-preset", self.preset, "-crf", str(self.crf), "-pix_fmt", "yuv420p",
               "-af", "aresample=44100,aformat=channel_layouts=stereo",
               "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2", out)
        d = durata(out)
        if musica == "silenzio": self.silenzio.append((self.clock, self.clock + d))
        if musica == "attenua":  self.attenua.append((self.clock, self.clock + d))
        self.clock += d
        return out

    # ---------- spezzoni ----------
    def intro(self, titolo, sottotitolo, dur, hook):
        G, c, f = self.G, self.c, self.f
        y = int(self.H*0.22)
        vf  = [f"drawbox=x=0:y={y-int(self.H*0.04)}:w={self.W}:h={max(6,int(self.H*0.005))}"
               f":color={c['accento']}:t=fill"]
        tit = wrap(titolo, G["tit_wrap"]); lh = int(G["tit_fs"]*1.12)
        vf += self.righe("itit", tit, f["titolo"], G["tit_fs"], c["testo"], y, lh, bordo=5)
        y2  = y + len(tit)*lh + int(self.H*0.03)
        sub = wrap(sottotitolo, G["tit_wrap"]+6); slh = int(G["sub_fs"]*1.12)
        vf += self.righe("isub", sub, f["opzioni"], G["sub_fs"], c["accento"], y2, slh, bordo=3)
        yl  = y2 + len(sub)*slh + int(self.H*0.03)
        vf += [f"drawbox=x=0:y={yl}:w={self.W}:h={max(6,int(self.H*0.005))}:color={c['accento']}:t=fill"]
        # gancio: entro pochi secondi, con le parole chiave di titolo, descrizione e tag
        v, vd = self.parla(hook)
        if v: dur = max(dur, vd + 1.2)
        a = self.suoni("a_intro", dur, [("livello", 0)] + ([("voce:" + v, 0.5)] if v else []))
        return self.render("05_titolo.mp4", dur, vf, audio=a, logo=False, raggi=True,
                           mascotte=(G["masc_h"], yl + int(self.H*0.04)))

    def livello(self, idx, nome, dur):
        """Cartello di cambio livello: 'LIVELLO 2' grande + 'MEDIO' sotto."""
        G, c, f = self.G, self.c, self.f
        parti = [p.strip() for p in nome.split(" - ", 1)]
        y = int(self.H*0.30)
        vf  = self.righe(f"lv{idx}", [parti[0].upper()], f["titolo"], int(G["tit_fs"]*1.5),
                         c["accento"], y, 0, bordo=6)
        if len(parti) > 1:
            vf += self.righe(f"lvs{idx}", [parti[1].upper()], f["opzioni"], int(G["sub_fs"]*1.3),
                             c["testo"], y + int(G["tit_fs"]*1.75), 0, bordo=3)
        self.capitoli.append((self.clock, nome))
        v, vd = self.parla(voce.frase_livello(nome))
        if v: dur = max(dur, vd + 0.8)
        a = self.suoni(f"a_lv{idx}", dur, [("livello", 0)] + ([("voce:" + v, 0.3)] if v else []))
        return self.render(f"07_lv{idx}.mp4", dur, vf, audio=a, logo=True, raggi=True)

    def domanda(self, idx, q, opzioni, dur):
        G, c, f = self.G, self.c, self.f
        vf = self.righe(f"qt{idx}", wrap(q, G["q_wrap"]), f["domanda"],
                        G["q_fs"], c["testo"], G["q_y"], G["q_lh"], bordo=3)
        # la domanda entra in dissolvenza scivolando dall'alto
        vf = [re.sub(r":y=(\d+)$", r":y='\1-40*pow(max(0,1-t/0.35),2)'", v) + ":alpha='min(1,t/0.3)'"
              for v in vf]
        # le card entrano una alla volta: piu' ritmo, l'occhio segue le opzioni
        entra = [0.35 + 0.18*i for i in range(len(opzioni))]
        v, vd = self.parla(q)
        if v and self.R["barra"]:          # tempo di lettura = durata della frase, niente buchi
            dur = round(max(dur - self.barra_len, vd + 0.6) + self.barra_len, 2)
        liv = [self.png_badge(idx + 1) + (None,)]
        # ogni card entra con un rimbalzo (piccola -> 112% -> 100%)
        liv += [self.anima(self.png_card(f"q{idx}", i, op, "neutra"), grafica.POP, f"pq{idx}_{i}")
                + (entra[i],) for i, op in enumerate(opzioni)]
        ev = [("domanda", 0)] + [("tick", t) for t in entra] + ([("voce:" + v, 0.25)] if v else [])
        if self.R["barra"]:
            # la barra QDI ha gia' i numeri 5-4-3-2-1: tick a ogni numero
            start = max(0.0, dur - self.barra_len)
            passo = min(1.0, dur / max(self.barra_len, 1))
            ev += [("tick", start + i*passo) for i in range(int(round(self.barra_len)))]
        else:
            n = int(dur)
            vf += [f"drawtext=fontfile='{f['titolo']}':text='%{{eif\\:max(0\\,{n}-t)\\:d}}'"
                   f":fontsize={G['cd_fs']}:fontcolor={c['countdown']}:x=(w-tw)/2:y={G['cd_y']}"]
            ev += [("tick", i) for i in range(1, n)]
        a = self.suoni(f"a_q{idx}", dur, ev)
        return self.render(f"10_q{idx:04d}.mp4", dur, vf, audio=a, barra=True, livelli=liv)

    def risposta(self, idx, q, opzioni, giusta, dur, spiega=None):
        G, c, f = self.G, self.c, self.f
        vf  = self.righe(f"rt{idx}", wrap(q, G["q_wrap"]), f["domanda"],
                         int(G["q_fs"]*0.88), f"{c['testo']}@0.8", G["q_y"], G["q_lh"], bordo=3)
        testo = spiega or "RISPOSTA GIUSTA"
        vf += self.righe(f"rok{idx}", wrap(testo, G["q_wrap"]+8), f["titolo"],
                         G["ok_fs"], c["accento"], G["ok_y"], int(G["ok_fs"]*1.12), bordo=4)
        liv = [self.png_badge(idx + 1) + (None,)]
        for i, op in enumerate(opzioni):
            card = self.png_card(f"r{idx}", i, op, "giusta" if i == giusta else "spenta")
            if i == giusta: card = self.anima(card, grafica.PULSA, f"pr{idx}")   # la giusta pulsa
            liv.append(card + (0.0 if i == giusta else None,))
        # coriandoli QDI che esplodono dal centro della risposta giusta
        cw, ch = self.G["card"]; gx, gy = self.G["gap"]
        cols = 2 if self.layout == "griglia" else 1
        r_, c_ = divmod(giusta, cols)
        cx = self.G["opt_x0"] + c_*(cw + gx) + cw//2; cy = self.G["opt_y0"] + r_*(ch + gy) + ch//2
        pat, w_, h_ = self.seq_coriandoli()
        liv.append((pat, cx - w_//2, cy - h_//2, 0.05))
        v, vd = self.parla(voce.frase_risposta(opzioni, giusta))
        if v: dur = max(dur, vd + 0.9)
        a = self.suoni(f"a_r{idx}", dur, [("giusta", 0)] + ([("voce:" + v, 0.35)] if v else []))
        return self.render(f"20_r{idx:04d}.mp4", dur, vf, audio=a, livelli=liv)

    def outro(self, cta, brand, dur):
        G, c, f = self.G, self.c, self.f
        y = int(self.H*0.33)
        vf  = self.righe("octa", wrap(cta, G["tit_wrap"]), f["titolo"],
                         int(G["tit_fs"]*0.9), c["testo"], y, int(G["tit_fs"]*1.05), bordo=5)
        vf += [f"drawbox=x=0:y={int(self.H*0.62)}:w={self.W}"
               f":h={max(6,int(self.H*0.005))}:color={c['accento']}:t=fill"]
        vf += self.righe("obr", wrap(brand, G["tit_wrap"]+6), f["cta"],
                         G["sub_fs"], c["accento"], int(self.H*0.68), int(G["sub_fs"]*1.1), bordo=3)
        a = self.suoni("a_outro", dur, [("livello", 0)])
        return self.render("90_outro.mp4", dur, vf, audio=a, logo=False,
                           mascotte=(G["masc_h"], int(self.H*0.10)))


# ---------- musica a rotazione ----------
def scegli_musica(cartella, chiave):
    """Ogni quiz nuovo parte dal brano successivo a quello usato dal quiz precedente.
    Lo stesso quiz rigenerato tiene il suo brano. Registro: musica-usata.json."""
    brani = sorted(x for x in os.listdir(os.path.join(ROOT, cartella)) if x.lower().endswith(AUDIO_EXT))
    if not brani: return []
    reg = json.load(open(REG_MUSICA, encoding="utf-8")) if os.path.exists(REG_MUSICA) else {}
    if chiave in reg and reg[chiave] in brani:
        i = brani.index(reg[chiave])
    elif reg:
        ultimo = list(reg.values())[-1]
        i = (brani.index(ultimo) + 1) % len(brani) if ultimo in brani else len(reg) % len(brani)
    else:
        i = 0
    reg.pop(chiave, None); reg[chiave] = brani[i]
    json.dump(reg, open(REG_MUSICA, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return [f"{cartella}/{b}" for b in brani[i:] + brani[:i]]


def letto_musicale(playlist, dur, out):
    """Brani in fila con dissolvenza incrociata di 3 s fino a coprire tutto il video."""
    scelti, tot = [], 0.0
    for p in playlist * 10:
        scelti.append(p); tot += durata(p) - 3
        if tot >= dur: break
    args = sum((["-i", p] for p in scelti), [])
    norm = ";".join(f"[{i}:a]aresample=44100,aformat=channel_layouts=stereo[m{i}]" for i in range(len(scelti)))
    if len(scelti) == 1:
        fc = norm + ";[m0]anull[out]"
    else:
        cat, prev = [], "m0"
        for i in range(1, len(scelti)):
            cat.append(f"[{prev}][m{i}]acrossfade=d=3[x{i}]"); prev = f"x{i}"
        fc = norm + ";" + ";".join(cat) + f";[{prev}]anull[out]"
    ffmpeg(*args, "-filter_complex", fc, "-map", "[out]", "-t", f"{dur:.2f}", "-ar", "44100", "-ac", "2", out)
    return [os.path.basename(p) for p in scelti]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("quiz")
    ap.add_argument("--formato", default="reel", choices=["reel", "youtube"])
    ap.add_argument("--out", default=None)
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--music", default=None, help="un brano preciso al posto della rotazione")
    ap.add_argument("--music-vol", type=float, default=None)
    ap.add_argument("--no-music", action="store_true")
    a = ap.parse_args()

    brand = json.load(open(os.path.join(ROOT, "brand.json"), encoding="utf-8"))
    data  = json.load(open(a.quiz, encoding="utf-8"))
    if a.music: a.music = os.path.abspath(a.music)
    dom   = data["domande"][:a.max] if a.max else data["domande"]
    base  = os.path.splitext(os.path.basename(a.quiz))[0]

    shutil.rmtree(TMP, ignore_errors=True); os.makedirs(TMP, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)

    # la rotazione (musica e sfondo) avanza di un passo per ogni quiz nuovo
    musica_dir = brand.get("risorse", {}).get("musica")
    playlist = []
    if not a.music and not a.no_music and musica_dir and os.path.isdir(os.path.join(ROOT, musica_dir)):
        playlist = scegli_musica(musica_dir, base)
    rot = len(json.load(open(REG_MUSICA, encoding="utf-8"))) - 1 if os.path.exists(REG_MUSICA) else 0

    fac = Factory(brand, a.formato, rotazione=max(rot, 0)); fac.make_bg()
    t = fac.tempi
    yt = fac.clip_brand
    print(f"formato {a.formato} {fac.W}x{fac.H} · {len(dom)} domande · voce: "
          f"{'SI (Gemini)' if fac.voce else 'no (manca GEMINI_API_KEY)'} · grafiche QDI: "
          + ", ".join(k for k, v in fac.R.items() if v))

    # dove cadono i cambi livello (indice domanda -> nome)
    cap = {int(i): n for i, n in data.get("capitoli", [])} if len(data.get("capitoli", [])) > 1 else {}
    if cap: cap = {i: n for i, n in cap.items() if i < len(dom)}
    cta_dopo = sorted(cap)[1] if len(cap) > 1 else (len(dom)//2 if yt and len(dom) >= 10 else -1)

    t0 = time.time(); segs = []
    if yt and fac.R["intro"]: segs.append(fac.clip("00_intro.mp4", "intro"))
    segs.append(fac.intro(data["titolo"], data.get("sottotitolo", ""), t["intro"],
                          voce.frase_hook(data)))
    for i, d in enumerate(dom):
        if i == cta_dopo and yt and fac.R["cta"]:
            segs.append(fac.clip(f"06_cta{i}.mp4", "cta"))
        if i in cap:
            if yt and fac.R["transizione"]:
                segs.append(fac.clip(f"06_tr{i}.mp4", "transizione", musica="attenua"))
            segs.append(fac.livello(i, cap[i], t.get("livello", 2.5)))
        elif i == 0 and yt and fac.R["transizione"]:
            segs.append(fac.clip("06_tr0.mp4", "transizione", musica="attenua"))
        if i == 0 and not cap: fac.capitoli.append((0.0, "Inizio quiz"))
        if i % 10 == 0 or len(dom) <= 10:
            print(f"  domanda {i+1}/{len(dom)}", flush=True)
        segs.append(fac.domanda(i, d["q"], d["opzioni"], t["domanda"]))
        segs.append(fac.risposta(i, d["q"], d["opzioni"], d["giusta"],
                                 t["risposta"], d.get("spiegazione")))
    fine = fac.clock
    if yt and fac.R["outro"]:
        segs.append(fac.clip("90_outro.mp4", "outro"))
    else:
        segs.append(fac.outro(brand["cta_finale"], brand["brand"], t["outro"]))

    lst = os.path.join(TMP, "lista.txt")
    with open(lst, "w") as f:
        for s in segs: f.write(f"file '{os.path.basename(s)}'\n")   # relativi alla lista
    out = os.path.abspath(a.out) if a.out else os.path.join(ROOT, "out", f"{base}-{a.formato}.mp4")

    print("  montaggio")
    muto = f"{REL}/montato.mp4"
    ffmpeg("-f", "concat", "-safe", "0", "-i", f"{REL}/lista.txt", "-c", "copy", muto)
    dur = durata(muto)

    brani = []
    if a.no_music:
        shutil.move(os.path.join(ROOT, muto), out)
    else:
        bed = f"{REL}/bed.wav"
        if a.music:
            ffmpeg("-stream_loop", "-1", "-i", a.music, "-t", f"{dur:.2f}", "-ar", "44100", "-ac", "2", bed)
            brani = [os.path.basename(a.music)]
        elif playlist:
            brani = letto_musicale(playlist, dur, bed)
        else:
            sh([sys.executable, os.path.join(ROOT, "make_music.py"), "--dur", f"{min(dur,180):.2f}", "--out", bed])
            brani = ["generata"]
        print(f"  musica: {', '.join(brani)}")
        vol = a.music_vol if a.music_vol is not None else brand.get("audio", {}).get("volume_musica", 0.40)
        # musica zitta sotto le clip QDI che hanno il loro audio, piu' bassa sulle transizioni
        z = "+".join(f"between(t,{s:.2f},{e:.2f})" for s, e in fac.silenzio) or "0"
        at = "+".join(f"between(t,{s:.2f},{e:.2f})" for s, e in fac.attenua) or "0"
        env = f"volume='{vol}*(1-min(1,{z}))*(1-0.65*min(1,{at}))':eval=frame"
        ffmpeg("-i", muto, "-stream_loop", "-1", "-i", bed, "-filter_complex",
               f"[1:a]{env},afade=t=out:st={max(0,dur-1.5):.2f}:d=1.5[m];"
               f"[0:a]aformat=channel_layouts=stereo[v0];"
               f"[v0][m]amix=inputs=2:duration=first:normalize=0,"
               f"aformat=channel_layouts=stereo,loudnorm=I=-14:TP=-1.5:LRA=11,"
               f"alimiter=limit=0.97[a]",
               "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
               "-ac", "2", "-ar", "44100", "-t", f"{dur:.2f}", "-movflags", "+faststart", out)

    if not a.no_music:     # seconda passata: loudnorm a passo singolo sbaglia di 1 dB
        r = subprocess.run(["ffmpeg", "-hide_banner", "-i", out, "-af", "ebur128", "-f", "null", "-"],
                           capture_output=True, text=True, cwd=ROOT).stderr
        righe = [l for l in r.splitlines() if l.strip().startswith("I:")]
        if righe:
            lufs = float(righe[-1].split()[1])
            if abs(lufs + 14) > 0.4:
                tmp2 = out + ".tmp.mp4"
                # tetto a -1,5 dB: con 0.97 la ricodifica AAC portava i picchi sopra 0 dBFS
                ffmpeg("-i", out, "-c:v", "copy", "-af",
                       f"volume={-14 - lufs:.2f}dB,alimiter=limit=0.84:level=disabled",
                       "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2",
                       "-movflags", "+faststart", "-f", "mp4", tmp2)
                os.replace(tmp2, out)
                print(f"  volume corretto da {lufs:.1f} a -14 LUFS")

    # linea del tempo per i capitoli di YouTube (letta da pubblica.py)
    caps = [(round(s, 2), n) for s, n in fac.capitoli]
    if caps: caps[0] = (0.0, caps[0][1])          # YouTube vuole il primo capitolo a 0:00
    caps.append((round(fine, 2), "Risultato finale"))
    json.dump({"durata": round(durata(out), 2), "capitoli": caps, "musica": brani},
              open(os.path.splitext(out)[0] + ".json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    d = durata(out); el = time.time()-t0
    print(f"\nFATTO: {out}\n  {int(d)//60}m {int(d)%60:02d}s · {os.path.getsize(out)/1e6:.1f} MB "
          f"· {len(dom)} domande\n  capitoli: " + " | ".join(f"{mmss(s)} {n}" for s, n in caps) +
          f"\n  render in {int(el)//60}m {int(el)%60:02d}s ({el/d:.2f}x il tempo reale)")

if __name__ == "__main__":
    main()
