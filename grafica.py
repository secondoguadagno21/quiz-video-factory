"""
Grafiche QDI disegnate come immagini (angoli arrotondati, bordi, ombre, sfumature):
badge "DOMANDA N" e card delle risposte. Le usa build.py come livelli sopra il video.
"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))

def rgb(hexstr, a=255):
    v = int(str(hexstr).replace("0x", "").replace("#", ""), 16)
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255, a)

def font(path, size):
    return ImageFont.truetype(os.path.join(ROOT, path), size)

def ombra(img, raggio, spost, opacita=110):
    """Ombra morbida sotto la sagoma (usa l'alfa dell'immagine)."""
    a = img.split()[3].point(lambda p: opacita if p > 160 else 0)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(raggio))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (spost, spost)); out.alpha_composite(img)
    return out

def adatta(draw, testo, path, size, larghezza):
    """Riduce il carattere finche' il testo sta nella larghezza."""
    while size > 12:
        f = font(path, size)
        if draw.textlength(testo, font=f) <= larghezza: return f
        size -= 2
    return font(path, size)

def gradiente(w, h, c1, c2, r):
    g = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(g)
    for y in range(h):
        t = y / max(h - 1, 1)
        d.line([(0, y), (w, y)], fill=tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)) + (255,))
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=255)
    g.putalpha(m)
    return g


def livello_sopra(img, disegna):
    """Disegna su un livello separato e lo fonde: ImageDraw da solo sostituisce i pixel
    invece di sfumarli, e i riflessi semitrasparenti uscirebbero 'bucati'."""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    disegna(ImageDraw.Draw(lay))
    img.alpha_composite(lay)


def badge(n, d, c, fonts, out):
    """Grande cerchio giallo col numero scuro in contrasto (niente scritta)."""
    navy, bordo = rgb(c["card_testo"]), max(4, d // 15)
    pad = d // 8
    img = Image.new("RGBA", (d + pad * 2, d + pad * 2), (0, 0, 0, 0))
    disco = gradiente(d, d, rgb("FFE36B"), rgb("FFB300"), d // 2)
    m = Image.new("L", (d, d), 0); ImageDraw.Draw(m).ellipse([0, 0, d - 1, d - 1], fill=255)
    disco.putalpha(m)
    img.alpha_composite(disco, (pad, pad))
    box = [pad, pad, pad + d - 1, pad + d - 1]
    livello_sopra(img, lambda dr: dr.ellipse([box[0] + bordo * 2, box[1] + bordo * 1.5,
                                              box[2] - bordo * 2, box[1] + d * 0.45], fill=(255, 255, 255, 70)))
    dr = ImageDraw.Draw(img)
    dr.ellipse(box, outline=navy, width=bordo)
    dr.ellipse([box[0] + bordo + 2, box[1] + bordo + 2, box[2] - bordo - 2, box[3] - bordo - 2],
               outline=(255, 255, 255, 255), width=max(2, bordo // 2))
    fn = adatta(dr, str(n), fonts["titolo"], int(d * 0.62), d * 0.70)
    dr.text((pad + d / 2, pad + d / 2 + d * 0.02), str(n), font=fn, fill=navy, anchor="mm")
    ombra(img, d // 18, max(3, d // 22)).save(out)
    return out


def sequenza_scala(png, scale, out_pattern):
    """Fotogrammi di un rimbalzo: la stessa grafica a scale diverse, centrata su una tela
    fissa. ffmpeg non sa animare una scala senza cambiare misura al flusso, quindi il
    rimbalzo si prepara qui e si sovrappone come sequenza di immagini."""
    src = Image.open(png).convert("RGBA")
    top = max(scale)
    W, H = int(src.width * top) + 2, int(src.height * top) + 2
    for i, s in enumerate(scale):
        tela = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if s > 0.02:
            im = src.resize((max(1, int(src.width * s)), max(1, int(src.height * s))), Image.LANCZOS)
            tela.alpha_composite(im, ((W - im.width) // 2, (H - im.height) // 2))
        tela.save(out_pattern % i)
    return (W - src.width) // 2, (H - src.height) // 2      # di quanto spostare in alto a sinistra


# curve dei rimbalzi, un valore per fotogramma a 30 fps
POP   = [0.35, 0.62, 0.86, 1.04, 1.12, 1.10, 1.04, 0.99, 0.98, 1.0]
PULSA = [1.0, 1.05, 1.10, 1.13, 1.12, 1.08, 1.03, 0.99, 0.98, 1.0, 1.02, 1.03, 1.02, 1.0]


def coriandoli(w, h, colori, n, out_pattern, seme=7):
    """Esplosione di coriandoli dal centro: rettangolini che ruotano e ricadono."""
    import math, random
    rnd = random.Random(seme)
    pezzi = []
    for _ in range(160):
        ang = rnd.uniform(0, 2 * math.pi); v = rnd.uniform(0.4, 1.0) * min(w, h) * 0.065
        pezzi.append(dict(vx=math.cos(ang) * v * 1.4, vy=math.sin(ang) * v - min(w, h) * 0.025,
                          col=rnd.choice(colori), lw=rnd.randint(12, 26), lh=rnd.randint(7, 14),
                          rot=rnd.uniform(0, 360), vr=rnd.uniform(-25, 25)))
    for f in range(n):
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        alfa = 255 if f < n * 0.6 else int(255 * (n - 1 - f) / (n * 0.4))   # l'ultimo e' vuoto
        for p in pezzi:
            x = w / 2 + p["vx"] * f * 0.92 ** f * 1.6
            y = h / 2 + p["vy"] * f + 0.9 * f * f
            q = Image.new("RGBA", (p["lw"], p["lh"]), p["col"][:3] + (alfa,))
            q = q.rotate(p["rot"] + p["vr"] * f, expand=True)
            if 0 <= x < w and 0 <= y < h: img.alpha_composite(q, (int(x), int(y)))
        img.save(out_pattern % f)


def raggi(d, colore, out, n=18):
    """Raggi di luce che partono dal centro e sfumano verso i bordi: girano dietro i titoli."""
    import math
    img = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    cx = cy = d / 2
    for i in range(n):
        a0 = 2 * math.pi * i / n; a1 = a0 + math.pi / n * 0.9
        dr.polygon([(cx, cy), (cx + d * math.cos(a0), cy + d * math.sin(a0)),
                    (cx + d * math.cos(a1), cy + d * math.sin(a1))], fill=colore[:3] + (60,))
    m = Image.new("L", (d, d), 0)
    for r in range(d // 2, 0, -4):                         # sfumatura radiale verso il bordo
        ImageDraw.Draw(m).ellipse([cx - r, cy - r, cx + r, cy + r], fill=int(255 * (1 - r / (d / 2)) ** 0.6))
    img.putalpha(Image.composite(img.split()[3], Image.new("L", (d, d), 0), m))
    img.filter(ImageFilter.GaussianBlur(3)).save(out)
    return out


def card(w, h, lettera, testo, stato, c, fonts, out):
    """stato: 'neutra' | 'giusta' | 'spenta'."""
    pad = max(10, h // 8)
    img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    r, bordo = max(14, h // 5), max(3, h // 30)
    lab = int(h * 0.82)
    x0, y0, x1, y1 = pad, pad, pad + w - 1, pad + h - 1
    navy = rgb(c["card_testo"])
    if stato == "giusta":
        glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle([x0 - 4, y0 - 4, x1 + 4, y1 + 4], r + 4, fill=rgb("7CFFB2", 200))
        img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(pad // 2)))
        dr.rounded_rectangle([x0, y0, x1, y1], r, fill=rgb(c["giusta"]), outline=(255, 255, 255, 255), width=bordo + 2)
        dr.rounded_rectangle([x0 + bordo + 2, y0 + bordo + 2, x0 + lab, y1 - bordo - 2], r - 4, fill=rgb("1E9E58"))
        col_l, col_t = (255, 255, 255, 255), (255, 255, 255, 255)
    elif stato == "spenta":
        dr.rounded_rectangle([x0, y0, x1, y1], r, fill=(255, 255, 255, 70), outline=(255, 255, 255, 90), width=bordo)
        col_l, col_t = (255, 255, 255, 140), (255, 255, 255, 150)
    else:
        dr.rounded_rectangle([x0, y0, x1, y1], r, fill=(255, 255, 255, 255), outline=navy, width=bordo)
        lab_img = gradiente(lab, h - bordo * 2, rgb("FFE36B"), rgb("FFB800"), r - 2)
        img.alpha_composite(lab_img, (x0 + bordo, y0 + bordo))
        dr = ImageDraw.Draw(img)
        dr.line([(x0 + bordo + lab, y0 + bordo), (x0 + bordo + lab, y1 - bordo)], fill=navy, width=bordo)
        dr.rounded_rectangle([x0, y0, x1, y1], r, outline=navy, width=bordo)
        col_l, col_t = navy, navy
    fl = font(fonts["titolo"], int(h * 0.56))
    dr.text((x0 + bordo + lab / 2, y0 + h / 2), lettera, font=fl, fill=col_l, anchor="mm")
    ft = adatta(dr, testo.upper(), fonts["opzioni"], int(h * 0.50), w - lab - h * 0.45)
    dr.text((x0 + bordo + lab + h * 0.22, y0 + h / 2 + h * 0.02), testo.upper(), font=ft, fill=col_t, anchor="lm")
    img = ombra(img, pad // 2, max(3, h // 20), 90) if stato == "neutra" else img
    img.save(out)
    return out, pad
