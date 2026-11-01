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
