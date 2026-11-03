#!/usr/bin/env python3
"""
Genera personaggi INVENTATI per le copertine (Google AI Studio, modello immagini Gemini)
e li salva scontornati in assets/personaggi/, dove li prende il modello C di miniatura.py.

  python3 personaggi.py                 # genera tutta la lista PERSONAGGI che manca
  python3 personaggi.py nonna-stupita   # solo uno

Serve GEMINI_API_KEY e la FATTURAZIONE attiva sul progetto di AI Studio: nel piano
gratuito la generazione di immagini ha limite zero. Costo indicativo: pochi centesimi
a immagine. Mai persone reali o famose: solo volti inventati.
"""
import base64, io, json, os, sys, urllib.error, urllib.request
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(ROOT, "assets", "personaggi")
MODELLO = "gemini-2.5-flash-image"

BASE = ("Fotografia ritratto realistica e nitida di una persona INVENTATA (non una persona reale), "
        "mezzo busto, guarda verso l'obiettivo, luce da studio morbida, "
        "sfondo verde uniforme da green screen (#00FF00) senza ombre, nessun testo, formato verticale. ")
# pubblico over 55: volti maturi ed emozioni forti funzionano meglio (ANALISI-COPERTINE.md)
PERSONAGGI = {
    "nonna-stupita":     "Signora italiana di circa 68 anni, capelli grigi ricci, occhiali, bocca aperta per lo stupore, mani sulle guance, cardigan colorato.",
    "nonno-pensieroso":  "Signore italiano di circa 70 anni, barba bianca curata, occhiali, mano sul mento, sguardo furbo e pensieroso, giacca e camicia.",
    "signora-sfida":     "Donna italiana di circa 55 anni, capelli castani corti, sorriso di sfida, un sopracciglio alzato, braccia conserte, giacca blu.",
    "professore-shock":  "Anziano professore con capelli bianchi spettinati e baffi, occhi sgranati e bocca aperta, mani alzate per lo stupore, maglione verde.",
    "signore-ride":      "Uomo italiano di circa 60 anni, calvo, ride di gusto indicando l'obiettivo, camicia a quadri.",
}


def genera(nome, descr):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key: sys.exit("Manca GEMINI_API_KEY.")
    body = json.dumps({"contents": [{"parts": [{"text": BASE + descr}]}],
                       "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}}).encode()
    rq = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{MODELLO}:generateContent", body,
        {"Content-Type": "application/json", "x-goog-api-key": key})
    try:
        r = json.load(urllib.request.urlopen(rq, timeout=180))
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        if e.code == 429 and "free_tier" in err:
            sys.exit("Google: le immagini non sono incluse nel piano gratuito. Attiva la fatturazione "
                     "su aistudio.google.com (Settings -> Billing) e riprova.")
        sys.exit(f"Google ha rifiutato ({e.code}): {err[:300]}")
    parti = r["candidates"][0]["content"]["parts"]
    dati = next((p["inlineData"]["data"] for p in parti if "inlineData" in p), None)
    if not dati: sys.exit(f"Nessuna immagine per {nome}: {json.dumps(r)[:300]}")
    img = Image.open(io.BytesIO(base64.b64decode(dati))).convert("RGBA")
    return scontorna(img)


def scontorna(img):
    """Toglie il verde del green screen e smorza i riflessi verdi sui bordi."""
    px = img.load()
    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            verde = g - max(r, b)
            if verde > 60 and g > 120:
                px[x, y] = (r, g, b, 0)
            elif verde > 20:
                px[x, y] = (r, max(r, b), b, int(a * max(0, 1 - (verde - 20) / 60)))
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


if __name__ == "__main__":
    try:
        from analizza_video import carica_env; carica_env()
    except Exception:
        pass
    os.makedirs(DEST, exist_ok=True)
    scelti = sys.argv[1:] or [n for n in PERSONAGGI if not os.path.exists(os.path.join(DEST, f"{n}.png"))]
    for n in scelti:
        if n not in PERSONAGGI: sys.exit(f"Non conosco '{n}'. Disponibili: {', '.join(PERSONAGGI)}")
        out = os.path.join(DEST, f"{n}.png")
        genera(n, PERSONAGGI[n]).save(out)
        print(f"Personaggio pronto: {out}")
