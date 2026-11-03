#!/usr/bin/env python3
"""
Copertine YouTube 1280x720 nello stile che funziona (vedi ANALISI-COPERTINE.md).

  python3 miniatura.py quiz/cultura-generale-genio.json                 # tutti e due i modelli
  python3 miniatura.py quiz/cultura-generale-genio.json --modello sfida

Modello A "sfida"      -> out/<quiz>-miniatura.jpg    (quella che usa pubblica.py)
Modello B "anteprima"  -> out/<quiz>-miniatura-b.jpg  (da provare col test copertine di YouTube)

Testi da quiz["youtube"]["miniatura"]: riga1, riga2, badge, e per il modello B
"sfida_b" (frase in alto) e "domanda" (indice della domanda da mostrare).
"""
import argparse, json, math, os, re, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H = 1280, 720
EMOJI = os.path.join(ROOT, "assets", "brand", "emoji3d")
sys.path.insert(0, ROOT)
import grafica

NAVY = (11, 20, 55, 255)
GIALLO = ((255, 236, 92), (255, 168, 0))
BIANCO = ((255, 255, 255), (214, 228, 255))
ROSSO = ((255, 92, 80), (214, 24, 24))


def fnt(path, size): return ImageFont.truetype(os.path.join(ROOT, path), size)

def emoji(code, size):
    return Image.open(os.path.join(EMOJI, f"{code}.png")).convert("RGBA").resize((size, size), Image.LANCZOS)

def con_ombra(img, raggio=10, spost=8, opacita=150):
    a = img.split()[3].point(lambda p: opacita if p > 100 else 0)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(raggio))
    out = Image.new("RGBA", (img.width + spost * 2, img.height + spost * 2), (0, 0, 0, 0))
    out.alpha_composite(sh, (spost * 2, spost * 2)); out.alpha_composite(img, (0, 0))
    return out


def raggiera(c1, c2, centro, raggi=22):
    """Sfondo a raggi di sole, con vignetta scura ai bordi."""
    img = Image.new("RGBA", (W, H), c1 + (255,))
    d = ImageDraw.Draw(img)
    cx, cy = centro; R = 2000
    for i in range(raggi):
        a0 = 2 * math.pi * i / raggi; a1 = a0 + math.pi / raggi
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)),
                   (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=c2 + (255,))
    luce = Image.new("L", (W, H), 0)
    ImageDraw.Draw(luce).ellipse([cx - 420, cy - 300, cx + 420, cy + 300], fill=120)
    img.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, 255)),
                        (0, 0)) if False else None
    bianco = Image.new("RGBA", (W, H), (255, 255, 255, 0)); bianco.putalpha(luce.filter(ImageFilter.GaussianBlur(120)))
    img.alpha_composite(bianco)
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).rectangle([0, 0, W, H], fill=150)
    ImageDraw.Draw(vig).ellipse([-200, -160, W + 200, H + 160], fill=0)
    nero = Image.new("RGBA", (W, H), (0, 0, 40, 0)); nero.putalpha(vig.filter(ImageFilter.GaussianBlur(90)))
    img.alpha_composite(nero)
    return img


def testo3d(img, cx, y, parti, size, font_path, larg_max):
    """Una riga di testo 'gonfio': estrusione scura, contorno spesso, riempimento sfumato.
    parti = [(parola, (colore_alto, colore_basso)), ...]. Si restringe da sola se non sta."""
    while True:
        f = fnt(font_path, size)
        spazio = f.getlength(" ")
        larg = sum(f.getlength(p) for p, _ in parti) + spazio * (len(parti) - 1)
        if larg <= larg_max or size < 40: break
        size -= 4
    bordo, prof = max(6, size // 13), max(6, size // 11)
    asc, desc = f.getmetrics(); alt = asc + desc
    lay = Image.new("RGBA", (int(larg) + bordo * 4 + prof, alt + bordo * 4 + prof), (0, 0, 0, 0))
    ox, oy = bordo * 2, bordo * 2
    d = ImageDraw.Draw(lay)
    x = ox
    for p, _ in parti:                                   # estrusione 3D
        for k in range(prof, 0, -1):
            d.text((x + k * 0.6, oy + k), p, font=f, fill=NAVY, stroke_width=bordo, stroke_fill=NAVY)
        x += f.getlength(p) + spazio
    x = ox
    for p, (c1, c2) in parti:
        d.text((x, oy), p, font=f, fill=NAVY, stroke_width=bordo, stroke_fill=NAVY)
        m = Image.new("L", lay.size, 0)
        ImageDraw.Draw(m).text((x, oy), p, font=f, fill=255)
        gr = Image.new("RGBA", lay.size)
        gd = ImageDraw.Draw(gr)
        for yy in range(lay.height):
            t = min(1, max(0, (yy - oy - alt * 0.15) / (alt * 0.75)))
            gd.line([(0, yy), (lay.width, yy)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)) + (255,))
        lay.paste(gr, (0, 0), m)
        hl = Image.new("L", lay.size, 0)                 # riflesso lucido in alto
        ImageDraw.Draw(hl).text((x, oy), p, font=f, fill=70)
        hl = Image.composite(hl, Image.new("L", lay.size, 0),
                             Image.linear_gradient("L").resize(lay.size).point(lambda v: 255 if v < 95 else 0))
        bianco = Image.new("RGBA", lay.size, (255, 255, 255, 0)); bianco.putalpha(hl)
        lay.alpha_composite(bianco)
        x += f.getlength(p) + spazio
    lay = con_ombra(lay, raggio=12, spost=8, opacita=120)
    img.alpha_composite(lay, (int(cx - lay.width / 2), int(y)))
    return size


def colora(riga, base):
    """Le parole con numeri in rosso: e' li' che cade l'occhio."""
    return [(p, ROSSO if re.search(r"\d", p) else base) for p in riga.split()]


def bandiera(img, x, y, w=190, angolo=-12):
    h = int(w * 0.62)
    fl = Image.new("RGBA", (w + 16, h + 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(fl)
    d.rounded_rectangle([0, 0, w + 15, h + 15], 10, fill=(255, 255, 255, 255))
    for i, col in enumerate([(0, 146, 70), (255, 255, 255), (206, 43, 55)]):
        d.rectangle([8 + i * w // 3, 8, 8 + (i + 1) * w // 3, h + 8], fill=col + (255,))
    fl = con_ombra(fl.rotate(angolo, expand=True, resample=Image.BICUBIC), 8, 6, 110)
    img.alpha_composite(fl, (x, y))


def bollino(img, cx, cy, d, numero, sotto, angolo=12):
    b = Image.new("RGBA", (d + 20, d + 20), (0, 0, 0, 0))
    dr = ImageDraw.Draw(b)
    dr.ellipse([0, 0, d + 19, d + 19], fill=(255, 255, 255, 255))
    dr.ellipse([8, 8, d + 11, d + 11], fill=(220, 30, 30, 255))
    luce = Image.new("RGBA", b.size, (0, 0, 0, 0))     # riflesso su livello separato
    ImageDraw.Draw(luce).ellipse([24, 16, d - 4, d * 0.48], fill=(255, 255, 255, 50))
    b.alpha_composite(luce)
    f1 = grafica.adatta(dr, numero, "assets/fonts/Anton-Regular.ttf", int(d * 0.48), d * 0.75)
    dr.text(((d + 20) / 2, (d + 20) * 0.43), numero, font=f1, fill="white", anchor="mm",
            stroke_width=4, stroke_fill=(120, 0, 0))
    f2 = grafica.adatta(dr, sotto, "assets/fonts/BebasNeue-Regular.ttf", int(d * 0.2), d * 0.72)
    dr.text(((d + 20) / 2, (d + 20) * 0.74), sotto, font=f2, fill="white", anchor="mm")
    b = con_ombra(b.rotate(-angolo, expand=True, resample=Image.BICUBIC), 8, 6, 130)
    img.alpha_composite(b, (int(cx - b.width / 2), int(cy - b.height / 2)))


def pillola_emoji(img, cx, cy, codici, size=78):
    pad = 18
    w = len(codici) * size + (len(codici) - 1) * 14 + pad * 2
    p = Image.new("RGBA", (w, size + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(p).rounded_rectangle([0, 0, w - 1, size + pad * 2 - 1], (size + pad * 2) // 2,
                                        fill=(255, 255, 255, 255), outline=NAVY, width=5)
    for i, c in enumerate(codici):
        p.alpha_composite(emoji(c, size), (pad + i * (size + 14), pad))
    p = con_ombra(p, 10, 7, 120)
    img.alpha_composite(p, (int(cx - p.width / 2), int(cy - p.height / 2)))


def mascotte(img, x, y, h):
    m = Image.open(os.path.join(ROOT, "assets", "brand", "mascotte.png")).convert("RGBA")
    m = m.resize((int(m.width * h / m.height), h), Image.LANCZOS)
    img.alpha_composite(con_ombra(m, 10, 8, 120), (x, y))


# ---------- modello A: SFIDA ----------
def modello_sfida(q, out):
    m = q.get("youtube", {}).get("miniatura", {})
    r1, r2 = m.get("riga1", q["titolo"]), m.get("riga2", "")
    n = re.search(r"\d+", m.get("badge", "")) or re.search(r"\d+", q.get("sottotitolo", ""))
    img = raggiera((24, 120, 230), (46, 160, 255), (640, 300))
    bandiera(img, 18, 14)
    usato = testo3d(img, 640, 52, colora(r1, BIANCO), 160, "assets/fonts/Anton-Regular.ttf", 820)
    if r2:
        testo3d(img, 640, 52 + int(usato * 1.18), colora(r2, GIALLO), usato,
                "assets/fonts/Anton-Regular.ttf", 840)
    mascotte(img, -12, 455, 265)
    faccia = con_ombra(emoji("1f631", 285), 12, 9, 130)
    img.alpha_composite(faccia, (W - faccia.width + 4, H - faccia.height + 12))
    pillola_emoji(img, 640, 640, ["1f9e0", "1f914", "1f3c6", "1f525"], size=72)
    if n: bollino(img, W - 115, 112, 170, n.group(), "DOMANDE")
    img.convert("RGB").save(out, quality=92)
    return out


# ---------- modello B: ANTEPRIMA ----------
def modello_anteprima(q, out):
    m = q.get("youtube", {}).get("miniatura", {})
    frase = m.get("sfida_b", "NESSUNO RIESCE A SUPERARE QUESTO TEST!")
    dom = q["domande"]
    if "domanda" in m: d = dom[m["domanda"]]
    else:   # una domanda del livello difficile, corta e con opzioni corte: si legge da lontano
        cand = dom[len(dom) * 2 // 3:] or dom
        d = min(cand, key=lambda x: len(x["q"]) + 2 * max(len(o) for o in x["opzioni"]))
    b = json.load(open(os.path.join(ROOT, "brand.json"), encoding="utf-8"))
    img = raggiera((24, 120, 230), (46, 160, 255), (640, 360))
    # fascia scura con la frase-sfida
    fascia = Image.new("RGBA", (1180, 150), (0, 0, 0, 0))
    ImageDraw.Draw(fascia).rounded_rectangle([0, 0, 1179, 149], 36, fill=(11, 20, 55, 240),
                                             outline=(255, 255, 255, 255), width=6)
    img.alpha_composite(con_ombra(fascia, 10, 7, 120), (50, 22))
    parti = [(p, GIALLO if i % 2 else BIANCO) for i, p in enumerate(frase.split())]
    testo3d(img, 640, 34, parti, 92, "assets/fonts/Anton-Regular.ttf", 1080)
    # riquadro giallo con la domanda vera
    box = Image.new("RGBA", (1180, 480), (0, 0, 0, 0))
    ImageDraw.Draw(box).rounded_rectangle([0, 0, 1179, 479], 40, fill=(255, 210, 60, 255),
                                          outline=NAVY, width=8)
    img.alpha_composite(con_ombra(box, 12, 8, 120), (50, 205))
    dr = ImageDraw.Draw(img)
    fq = grafica.adatta(dr, d["q"], "assets/fonts/Anton-Regular.ttf", 74, 1080)
    dr.text((640, 290), d["q"], font=fq, fill=NAVY, anchor="mm")
    cw, ch = 520, 118
    for i, o in enumerate(d["opzioni"]):
        r, c = divmod(i, 2)
        p = os.path.join(ROOT, ".tmp_card.png")
        _, pad = grafica.card(cw, ch, "ABCD"[i], o, "neutra", b["colori"], b["font"], p)
        img.alpha_composite(Image.open(p).convert("RGBA"), (95 + c * (cw + 50) - pad, 370 + r * (ch + 30) - pad))
        os.remove(p)
    faccia = con_ombra(emoji("1f914", 210), 10, 8, 130)
    img.alpha_composite(faccia, (W - faccia.width + 10, H - faccia.height + 20))
    img.convert("RGB").save(out, quality=92)
    return out


# ---------- modello C: PERSONAGGIO (fasce colorate, stile GK Smart Point) ----------
FASCE = [((230, 40, 40), "white"), ((255, 214, 0), (11, 20, 55)), ((40, 175, 70), "white"),
         ((140, 60, 220), (255, 230, 60)), ((255, 120, 0), "white")]

def personaggio(cartella, chiave):
    """Un personaggio inventato da assets/personaggi (PNG con trasparenza), a rotazione."""
    if not os.path.isdir(cartella): return None
    tutti = sorted(x for x in os.listdir(cartella) if x.lower().endswith(".png"))
    if not tutti: return None
    return os.path.join(cartella, tutti[sum(map(ord, chiave)) % len(tutti)])

def modello_personaggio(q, out, chiave="quiz"):
    m = q.get("youtube", {}).get("miniatura", {})
    righe = m.get("righe_c") or [m.get("riga1", q["titolo"]), m.get("riga2", "")]
    img = raggiera((20, 110, 225), (40, 150, 250), (330, 380))
    # a sinistra il personaggio (o, finche' non c'e', la faccina 3D pensierosa)
    p = personaggio(os.path.join(ROOT, "assets", "personaggi"), chiave)
    if p:
        pers = Image.open(p).convert("RGBA")
        pers = pers.resize((int(pers.width * 700 / pers.height), 700), Image.LANCZOS)
        img.alpha_composite(con_ombra(pers, 14, 10, 120), (-30, H - 700))
    else:
        f = con_ombra(emoji("1f914", 470), 14, 10, 130)
        img.alpha_composite(f, (-10, H - f.height + 20))
    # a destra le fasce colorate, una per riga
    x0, w, y = 500, 750, 40
    hb = min(150, (H - 80) // max(len(righe), 1) - 16)
    for i, r in enumerate(r for r in righe if r):
        col, tcol = FASCE[i % len(FASCE)]
        fascia = Image.new("RGBA", (w, hb), (0, 0, 0, 0))
        dr = ImageDraw.Draw(fascia)
        dr.rounded_rectangle([0, 0, w - 1, hb - 1], hb // 4, fill=col + (255,), outline=NAVY, width=6)
        f = grafica.adatta(dr, r, "assets/fonts/Anton-Regular.ttf", int(hb * 0.78), w - 50)
        dr.text((w / 2, hb / 2), r, font=f, fill=tcol, anchor="mm",
                stroke_width=4 if tcol == "white" else 0, stroke_fill=NAVY)
        fascia = con_ombra(fascia.rotate(-1.5 if i % 2 else 1.5, expand=True, resample=Image.BICUBIC), 8, 6, 120)
        img.alpha_composite(fascia, (x0, y)); y += hb + 16
    img.alpha_composite(con_ombra(emoji("1f9e0", 130), 8, 6, 120), (W - 150, H - 150))
    bandiera(img, 18, 14, w=150)
    img.convert("RGB").save(out, quality=92)
    return out


def main(quiz_path, out=None, modello="tutti"):
    q = json.load(open(quiz_path, encoding="utf-8"))
    base = os.path.join(ROOT, "out", os.path.splitext(os.path.basename(quiz_path))[0])
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    fatti = []
    if modello in ("sfida", "tutti"):
        fatti.append(modello_sfida(q, out or base + "-miniatura.jpg"))
    if modello in ("anteprima", "tutti"):
        fatti.append(modello_anteprima(q, base + "-miniatura-b.jpg"))
    if modello in ("personaggio", "tutti"):
        fatti.append(modello_personaggio(q, base + "-miniatura-c.jpg", os.path.basename(base)))
    for f in fatti: print(f"Miniatura: {f}")
    return fatti[0]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("quiz"); ap.add_argument("out", nargs="?")
    ap.add_argument("--modello", choices=["sfida", "anteprima", "personaggio", "tutti"], default="tutti")
    a = ap.parse_args()
    main(a.quiz, a.out, a.modello)
