#!/usr/bin/env python3
"""
Pesca i video quiz che funzionano, dall'API di YouTube.

  export YT_API_KEY="..."
  python3 scopri_video.py --cerca "quiz emoji film" "indovina il film"
  python3 scopri_video.py --canale UCxxxxxxxx          # 100 volte piu' economico
  python3 scopri_video.py --cerca "quiz italia" --salva

QUOTA (10.000 punti al giorno, gratuiti):
  search.list ......... 100 punti   <- cara: usala per scoprire canali nuovi
  playlistItems.list .... 1 punto   <- per sorvegliare un canale che gia' conosci
  videos.list ........... 1 punto   (fino a 50 video per chiamata)
  channels.list ......... 1 punto
"""
import json, os, re, sys, urllib.request, urllib.parse, argparse, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = "https://www.googleapis.com/youtube/v3"
COSTO = {"search": 100, "videos": 1, "channels": 1, "playlistItems": 1}
spesa = {"punti": 0, "chiamate": []}

def get(endpoint, **params):
    params["key"] = KEY
    url = f"{BASE}/{endpoint}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        msg = json.load(e).get("error", {})
        rs = [x.get("reason") for x in msg.get("errors", [])]
        if "quotaExceeded" in rs:
            sys.exit(f"\nQUOTA ESAURITA per oggi (spesi {spesa['punti']} punti).\n"
                     "  Si azzera a mezzanotte ora del Pacifico.")
        sys.exit(f"\nAPI: {msg.get('message','errore')} [{','.join(filter(None,rs))}]")
    spesa["punti"] += COSTO.get(endpoint, 1)
    spesa["chiamate"].append(endpoint)
    return d

def durata(iso):
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso or "")
    if not m: return 0
    h, mi, s = (int(x) if x else 0 for x in m.groups())
    return h*3600 + mi*60 + s

def hms(s):
    return f"{s//3600}h{s%3600//60:02d}m" if s >= 3600 else f"{s//60}m{s%60:02d}s"

def arricchisci(ids):
    """search e playlistItems NON danno durata ne' viste: vanno chieste a parte."""
    out = []
    for i in range(0, len(ids), 50):
        d = get("videos", part="snippet,contentDetails,statistics",
                id=",".join(ids[i:i+50]))
        for v in d.get("items", []):
            s, c, st = v["snippet"], v.get("contentDetails", {}), v.get("statistics", {})
            sec = durata(c.get("duration"))
            vis = int(st.get("viewCount", 0))
            gg = max(1, (datetime.datetime.now(datetime.timezone.utc) -
                  datetime.datetime.fromisoformat(s["publishedAt"].replace("Z","+00:00"))).days)
            out.append(dict(
                id=v["id"], titolo=s["title"], canale=s["channelTitle"],
                canale_id=s["channelId"], pubblicato=s["publishedAt"][:10],
                secondi=sec, durata=hms(sec), viste=vis,
                like=int(st.get("likeCount", 0)),
                viste_al_giorno=round(vis/gg),
                domande_stimate=round(sec/14) if sec else 0,
                tag=s.get("tags", [])[:10],
                url=f"https://www.youtube.com/watch?v={v['id']}"))
    return out

def cerca(termini, n, ordine, giorni, lunghezza):
    ids, visti = [], set()
    dopo = (datetime.datetime.now(datetime.timezone.utc) -
            datetime.timedelta(days=giorni)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for t in termini:
        print(f"  cerco: \"{t}\"   (-100 punti)")
        p = dict(part="snippet", q=t, type="video", maxResults=min(n, 50),
                 order=ordine, regionCode="IT", relevanceLanguage="it",
                 publishedAfter=dopo)
        if lunghezza != "any": p["videoDuration"] = lunghezza
        for it in get("search", **p).get("items", []):
            vid = it["id"].get("videoId")
            if vid and vid not in visti:
                visti.add(vid); ids.append(vid)
    return ids

def da_canale(canale_id, n):
    """Il trucco: la playlist dei caricamenti costa 1 punto invece di 100."""
    ch = get("channels", part="contentDetails,snippet", id=canale_id).get("items", [])
    if not ch: sys.exit(f"Canale non trovato: {canale_id}")
    nome = ch[0]["snippet"]["title"]
    pl = ch[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    print(f"  canale: {nome}   (-2 punti invece di 100)")
    ids, tok = [], None
    while len(ids) < n:
        d = get("playlistItems", part="contentDetails", playlistId=pl,
                maxResults=50, **({"pageToken": tok} if tok else {}))
        ids += [i["contentDetails"]["videoId"] for i in d.get("items", [])]
        tok = d.get("nextPageToken")
        if not tok: break
    return ids[:n]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cerca", nargs="*", default=[])
    ap.add_argument("--canale", nargs="*", default=[])
    ap.add_argument("--n", type=int, default=25)
    ap.add_argument("--ordine", default="viewCount",
                    choices=["viewCount", "date", "relevance", "rating"])
    ap.add_argument("--giorni", type=int, default=365)
    ap.add_argument("--lunghezza", default="any", choices=["any","short","medium","long"],
                    help="long = oltre 20 minuti")
    ap.add_argument("--min-viste", type=int, default=0)
    ap.add_argument("--salva", action="store_true", help="aggiunge a riferimenti.json")
    a = ap.parse_args()

    KEY = os.environ.get("YT_API_KEY", "").strip()
    if not KEY:
        sys.exit("Manca YT_API_KEY.  export YT_API_KEY=...")
    if not a.cerca and not a.canale:
        sys.exit("Serve almeno --cerca \"...\" oppure --canale UCxxxx")

    ids = []
    if a.canale:
        for c in a.canale: ids += da_canale(c, a.n)
    if a.cerca:
        ids += cerca(a.cerca, a.n, a.ordine, a.giorni, a.lunghezza)

    print(f"\n  {len(ids)} video trovati, chiedo i dettagli...\n")
    v = [x for x in arricchisci(list(dict.fromkeys(ids))) if x["viste"] >= a.min_viste]
    v.sort(key=lambda x: -x["viste_al_giorno"])

    print(f"{'VISTE':>11} {'/GIORNO':>9} {'DURATA':>7} {'DOM':>4}  CANALE / TITOLO")
    print("-"*100)
    for x in v[:40]:
        print(f"{x['viste']:>11,} {x['viste_al_giorno']:>9,} {x['durata']:>7} "
              f"{x['domande_stimate']:>4}  {x['canale'][:20]:20} {x['titolo'][:40]}"
              .replace(",", "."))

    if v:
        lunghi = [x for x in v if x["secondi"] >= 480]
        print(f"\n  oltre 8 minuti: {len(lunghi)} su {len(v)}")
        if lunghi:
            md = sorted(x["secondi"] for x in lunghi)[len(lunghi)//2]
            print(f"  durata mediana dei lunghi: {hms(md)}  (~{round(md/14)} domande)")
        canali = {}
        for x in v: canali[x["canale"]] = canali.get(x["canale"], 0) + x["viste_al_giorno"]
        print(f"\n  canali che spingono di piu' (viste al giorno):")
        for c, n in sorted(canali.items(), key=lambda t: -t[1])[:6]:
            print(f"    {n:>9,}".replace(",", ".") + f"  {c}")

    print(f"\n  quota spesa: {spesa['punti']} punti su 10.000 "
          f"({', '.join(sorted(set(spesa['chiamate'])))})")

    if a.salva:
        rif = os.path.join(ROOT, "riferimenti.json")
        d = json.load(open(rif)) if os.path.exists(rif) else {"video": []}
        noti = {x["id"] for x in d["video"]}
        nuovi = [{"id": x["id"], "url": x["url"],
                  "note": f"{x['canale']} · {x['durata']} · {x['viste']:,} viste".replace(",",".")}
                 for x in v if x["id"] not in noti]
        d["video"] += nuovi
        json.dump(d, open(rif, "w"), ensure_ascii=False, indent=2)
        print(f"  aggiunti a riferimenti.json: {len(nuovi)} nuovi")
