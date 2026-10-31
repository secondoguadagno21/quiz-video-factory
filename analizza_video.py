#!/usr/bin/env python3
"""
Legge i video di riferimento dall'API ufficiale di YouTube e ne estrae lo schema.
YouTube.com e' bloccato dalla rete di questo ambiente, ma googleapis.com no:
percio' passiamo dall'API.

  export YT_API_KEY="la-tua-chiave"
  python3 analizza_video.py                      # usa la lista in riferimenti.json
  python3 analizza_video.py --id ABC123 DEF456
"""
import json, os, re, sys, urllib.request, urllib.error, urllib.parse, argparse

ROOT = os.path.dirname(os.path.abspath(__file__))
API  = "https://www.googleapis.com/youtube/v3/videos"

def api(ids, key):
    out = []
    for i in range(0, len(ids), 50):                  # l'API ne accetta 50 per volta
        q = urllib.parse.urlencode({
            "part": "snippet,contentDetails,statistics",
            "id": ",".join(ids[i:i+50]), "key": key})
        try:
            with urllib.request.urlopen(f"{API}?{q}", timeout=30) as r:
                out += json.load(r).get("items", [])
        except urllib.error.HTTPError as e:
            err = json.load(e).get("error", {})
            motivi = {x.get("reason") for x in err.get("errors", [])}
            if "quotaExceeded" in motivi:
                sys.exit("QUOTA ESAURITA per oggi. Si azzera a mezzanotte ora del Pacifico.")
            if e.code == 400 or "keyInvalid" in motivi:
                sys.exit("Chiave non valida: controlla di averla copiata intera, "
                         "senza spazi ne' virgolette.")
            if e.code == 403:
                sys.exit("Chiave rifiutata: verifica che sia abilitata per "
                         "YouTube Data API v3.\n  Dettaglio: " + err.get("message", ""))
            sys.exit(f"API YouTube: {err.get('message', e)}")
    return out

def carica_env():
    """Sul PC la chiave sta nel file .env (mai su GitHub); nel cloud nelle
    impostazioni dell'ambiente. Una variabile gia' impostata vince sempre."""
    p = os.path.join(ROOT, ".env")
    if not os.path.exists(p): return
    for riga in open(p, encoding="utf-8-sig"):
        riga = riga.strip()
        if not riga or riga.startswith("#") or "=" not in riga: continue
        k, v = riga.split("=", 1)
        k = k.strip().removeprefix("export ").strip()
        os.environ.setdefault(k, v.strip().strip('"').strip("'"))

def durata(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m: return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h*3600 + mi*60 + s

def hms(s):
    return f"{s//3600}h {s%3600//60:02d}m" if s >= 3600 else f"{s//60}m {s%60:02d}s"

def capitoli(desc):
    """I capitoli stanno nella descrizione come 0:00 Titolo."""
    return re.findall(r"^\s*((?:\d+:)?\d{1,2}:\d{2})\s+(.{2,80})$", desc or "", re.M)

def analizza(v):
    s, c, st = v["snippet"], v.get("contentDetails", {}), v.get("statistics", {})
    d = durata(c.get("duration"))
    desc = s.get("description", "")
    cap = capitoli(desc)
    return dict(
        id=v["id"], titolo=s["title"], canale=s["channelTitle"],
        pubblicato=s["publishedAt"][:10], secondi=d, durata=hms(d),
        viste=int(st.get("viewCount", 0)), like=int(st.get("likeCount", 0)),
        commenti=int(st.get("commentCount", 0)),
        tag=s.get("tags", [])[:15], n_capitoli=len(cap), capitoli=cap[:8],
        descrizione=desc[:600],
        domande_stimate=round(d/14) if d else 0,   # 10s domanda + 4s risposta
    )

def schema(a):
    """Cosa hanno in comune: e' da qui che nasce il template."""
    if not a: return {}
    sec = sorted(x["secondi"] for x in a)
    vis = sorted(x["viste"] for x in a)
    tutte = " ".join(x["titolo"].lower() for x in a)
    parole = re.findall(r"[a-zàèéìòù]{4,}", tutte)
    freq = {}
    for p in parole: freq[p] = freq.get(p, 0) + 1
    emoji = len(re.findall(r"[\U0001F300-\U0001FAFF]", " ".join(x["titolo"] for x in a)))
    return dict(
        n=len(a),
        durata_mediana=hms(sec[len(sec)//2]),
        durata_min=hms(sec[0]), durata_max=hms(sec[-1]),
        viste_mediane=f"{vis[len(vis)//2]:,}".replace(",", "."),
        domande_mediane=round(sec[len(sec)//2]/14),
        canali=sorted({x["canale"] for x in a}),
        parole_ricorrenti=sorted(freq.items(), key=lambda t: -t[1])[:12],
        emoji_nei_titoli=emoji,
        con_capitoli=sum(1 for x in a if x["n_capitoli"] > 2),
    )

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", nargs="*", default=None)
    ap.add_argument("--out", default=os.path.join(ROOT, "riferimenti-analisi.json"))
    a = ap.parse_args()

    carica_env()
    key = os.environ.get("YT_API_KEY", "").strip()
    if not key:
        sys.exit("Manca YT_API_KEY.\n"
                 "  Chiave da console.cloud.google.com -> API e servizi -> Credenziali\n"
                 "  (abilita 'YouTube Data API v3').\n"
                 "  Cloud: impostazioni dell'ambiente.  PC: copia .env.esempio in .env.")

    ids = a.id
    if not ids:
        rif = os.path.join(ROOT, "riferimenti.json")
        if not os.path.exists(rif): sys.exit(f"Manca {rif}")
        ids = [v["id"] for v in json.load(open(rif))["video"]]

    print(f"Interrogo l'API per {len(ids)} video...\n")
    dati = [analizza(v) for v in api(ids, key)]
    dati.sort(key=lambda x: -x["viste"])
    sc = schema(dati)

    print(f"{'DURATA':>9}  {'VISTE':>12}  {'DOM.':>5}  CANALE / TITOLO")
    print("-"*96)
    for x in dati:
        print(f"{x['durata']:>9}  {x['viste']:>12,}  {x['domande_stimate']:>5}  "
              f"{x['canale'][:22]:22} {x['titolo'][:44]}".replace(",", "."))
    mancanti = set(ids) - {x["id"] for x in dati}
    if mancanti: print(f"\nnon trovati (privati o rimossi): {', '.join(mancanti)}")

    print(f"\n{'='*96}\nLO SCHEMA CHE EMERGE\n{'='*96}")
    print(f"  video analizzati   {sc['n']}")
    print(f"  durata mediana     {sc['durata_mediana']}   (da {sc['durata_min']} a {sc['durata_max']})")
    print(f"  domande mediane    {sc['domande_mediane']}")
    print(f"  viste mediane      {sc['viste_mediane']}")
    print(f"  con capitoli       {sc['con_capitoli']} su {sc['n']}")
    print(f"  emoji nei titoli   {sc['emoji_nei_titoli']}")
    print(f"  canali             {', '.join(sc['canali'][:6])}")
    print(f"\n  parole che tornano nei titoli:")
    for p, n in sc["parole_ricorrenti"]:
        print(f"    {n}x  {p}")

    json.dump({"video": dati, "schema": sc}, open(a.out, "w"),
              ensure_ascii=False, indent=2)
    print(f"\nSalvato: {a.out}")
