#!/usr/bin/env python3
"""
Carica un video sul canale YouTube, con titolo, descrizione, capitoli, tag e miniatura
presi dalla banca domande. Funziona sia sul PC sia nel cloud: servono
YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN (vedi autorizza_youtube.py).

  python3 pubblica.py quiz/x.json                                   # privato (da controllare)
  python3 pubblica.py quiz/x.json --programma "2026-11-03 18:00"    # esce da solo, ora italiana
  python3 pubblica.py quiz/x.json --non-in-elenco                   # solo chi ha il link
  python3 pubblica.py quiz/x.json --pubblico                        # subito online
  python3 pubblica.py quiz/x.json --prova                           # mostra i dati, non carica
"""
import argparse, datetime, json, os, sys, time, urllib.parse, urllib.request, urllib.error

from analizza_video import carica_env, ROOT

TOKEN  = "https://oauth2.googleapis.com/token"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3/videos"
THUMB  = "https://www.googleapis.com/upload/youtube/v3/thumbnails/set"
REGISTRO = os.path.join(ROOT, "pubblicati.json")
BLOCCO = 16 * 1024 * 1024          # 16 MB per pezzo: regge anche connessioni lente


def mmss(s):
    s = int(s); return f"{s//3600}:{s%3600//60:02d}:{s%60:02d}" if s >= 3600 else f"{s//60}:{s%60:02d}"


def capitoli(quiz, brand, formato="youtube", timeline=None):
    """Minutaggi veri dal file .json che build.py scrive accanto al video (con intro,
    transizioni e CTA). Se manca, li stima dai tempi di brand.json."""
    if timeline and os.path.exists(timeline):
        caps = json.load(open(timeline, encoding="utf-8")).get("capitoli", [])
        if len(caps) >= 3:
            return "\n".join(f"{mmss(t)} {n}" for t, n in caps)
    cap = quiz.get("capitoli") or []
    if len(cap) < 2: return ""
    t = brand["formati"][formato]["tempi"]
    passo = t["domanda"] + t["risposta"]
    righe = []
    for i, (idx, nome) in enumerate(cap):
        sec = 0 if i == 0 else t["intro"] + idx * passo
        righe.append(f"{mmss(sec)} {nome}")
    fine = t["intro"] + len(quiz["domande"]) * passo
    righe.append(f"{mmss(fine)} Risultato finale")
    return "\n".join(righe)


def metadati(quiz, brand, timeline=None):
    yt = quiz.get("youtube", {})
    titolo = (yt.get("titolo") or quiz["titolo"]).strip()
    if len(titolo) > 100: sys.exit(f"Titolo troppo lungo ({len(titolo)}/100): {titolo}")
    parti = [yt.get("descrizione", "").strip()]
    cap = capitoli(quiz, brand, timeline=timeline)
    if cap: parti.append(cap)
    if brand.get("descrizione_footer"): parti.append(brand["descrizione_footer"].strip())
    if brand.get("hashtag"): parti.append(brand["hashtag"])
    desc = "\n\n".join(p for p in parti if p)
    if len(desc) > 5000: sys.exit("Descrizione oltre 5000 caratteri.")
    for ch in "<>":
        if ch in titolo or ch in desc: sys.exit(f"YouTube rifiuta il carattere {ch} in titolo/descrizione.")
    tag = yt.get("tag", [])
    while len(",".join(tag)) > 480: tag = tag[:-1]
    return dict(title=titolo, description=desc, tags=tag, categoryId=str(yt.get("categoria", 24)),
                defaultLanguage="it", defaultAudioLanguage="it")


def ora_utc(testo):
    """'2026-11-03 18:00' ora italiana -> '2026-11-03T17:00:00Z'."""
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Rome")
    except Exception:
        sys.exit("Manca il fuso orario: esegui  pip install tzdata  e riprova.")
    d = datetime.datetime.fromisoformat(testo.replace("T", " ")).replace(tzinfo=tz)
    if d < datetime.datetime.now(tz) + datetime.timedelta(minutes=15):
        sys.exit("La data di uscita deve essere almeno 15 minuti nel futuro.")
    return d.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def access_token():
    v = {k: os.environ.get(k, "").strip() for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")}
    manca = [k for k, x in v.items() if not x]
    if manca:
        sys.exit("Pubblicazione non ancora autorizzata. Mancano: " + ", ".join(manca) +
                 "\n  Sul PC: python3 autorizza_youtube.py  (una volta sola), poi copia le\n"
                 "  3 righe che stampa nelle variabili dell'ambiente cloud.")
    body = urllib.parse.urlencode(dict(client_id=v["YT_CLIENT_ID"], client_secret=v["YT_CLIENT_SECRET"],
                                       refresh_token=v["YT_REFRESH_TOKEN"],
                                       grant_type="refresh_token")).encode()
    try:
        return json.load(urllib.request.urlopen(TOKEN, body, timeout=30))["access_token"]
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        if "invalid_grant" in err:
            sys.exit("Il token YouTube e' scaduto o revocato.\n"
                     "  Se l'app OAuth e' ancora in modalita' 'Test', scade ogni 7 giorni:\n"
                     "  Google Cloud Console -> Schermata consenso OAuth -> Pubblica app.\n"
                     "  Poi rilancia  python3 autorizza_youtube.py  sul PC.")
        sys.exit("Google ha rifiutato le credenziali: " + err[:300])


def richiesta(url, token, data=None, metodo="GET", headers=None):
    h = {"Authorization": f"Bearer {token}"}; h.update(headers or {})
    return urllib.request.Request(url, data=data, method=metodo, headers=h)


def carica(path, meta, status, token):
    tot = os.path.getsize(path)
    init = richiesta(f"{UPLOAD}?uploadType=resumable&part=snippet,status", token,
                     json.dumps({"snippet": meta, "status": status}).encode(), "POST",
                     {"Content-Type": "application/json; charset=UTF-8",
                      "X-Upload-Content-Length": str(tot), "X-Upload-Content-Type": "video/mp4"})
    try:
        sessione = urllib.request.urlopen(init, timeout=60).headers["Location"]
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        if "quotaExceeded" in err or "uploadLimitExceeded" in err:
            sys.exit("Limite di caricamenti di oggi raggiunto. Riprova domani.")
        sys.exit("YouTube ha rifiutato il caricamento: " + err[:500])

    inviati, tentativi = 0, 0
    with open(path, "rb") as f:
        while True:
            f.seek(inviati); pezzo = f.read(BLOCCO)
            fine = inviati + len(pezzo) - 1
            rq = richiesta(sessione, token, pezzo, "PUT",
                           {"Content-Length": str(len(pezzo)),
                            "Content-Range": f"bytes {inviati}-{fine}/{tot}"})
            try:
                r = urllib.request.urlopen(rq, timeout=300)
                print(f"\r  caricamento 100%      "); return json.load(r)
            except urllib.error.HTTPError as e:
                if e.code == 308:                               # pezzo ricevuto, avanti
                    rng = e.headers.get("Range")
                    inviati = int(rng.split("-")[1]) + 1 if rng else 0
                    tentativi = 0
                    print(f"\r  caricamento {inviati*100//tot:3d}%", end="", flush=True)
                    continue
                if e.code in (500, 502, 503, 504) and tentativi < 6:
                    tentativi += 1; time.sleep(2 ** tentativi); continue
                sys.exit(f"\nCaricamento interrotto ({e.code}): {e.read().decode()[:400]}")
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                if tentativi >= 6: sys.exit(f"\nRete instabile, caricamento fallito: {e}")
                tentativi += 1; time.sleep(2 ** tentativi)
                stato = richiesta(sessione, token, b"", "PUT",
                                  {"Content-Length": "0", "Content-Range": f"bytes */{tot}"})
                try:
                    return json.load(urllib.request.urlopen(stato, timeout=60))
                except urllib.error.HTTPError as e2:
                    if e2.code == 308:
                        rng = e2.headers.get("Range")
                        inviati = int(rng.split("-")[1]) + 1 if rng else 0
                    else: raise


def miniatura(video_id, img, token):
    tipo = "image/png" if img.lower().endswith(".png") else "image/jpeg"
    rq = richiesta(f"{THUMB}?videoId={video_id}", token, open(img, "rb").read(), "POST",
                   {"Content-Type": tipo})
    try:
        urllib.request.urlopen(rq, timeout=120); return True
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        if e.code == 403 and "forbidden" in err and "videoId" in err:
            print("  miniatura NON caricata: YouTube non permette di cambiarla su questo video\n"
                  "  (di solito c'e' un 'Test e confronto' copertine in corso). Va fatto da YouTube Studio.")
        elif e.code == 403:
            print("  miniatura NON caricata: il canale deve essere verificato col telefono\n"
                  "  (youtube.com/verify), oppure manca il permesso. Dettaglio: " + err[:200])
        else:
            print("  miniatura NON caricata: " + err[:200])
        return False


def registra(voce):
    reg = json.load(open(REGISTRO, encoding="utf-8")) if os.path.exists(REGISTRO) else []
    reg.append(voce)
    json.dump(reg, open(REGISTRO, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


def gia_pubblicato(quiz_path):
    if not os.path.exists(REGISTRO): return None
    nome = os.path.basename(quiz_path)
    return next((v for v in json.load(open(REGISTRO, encoding="utf-8")) if v["quiz"] == nome), None)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("quiz")
    ap.add_argument("--video", help="mp4 da caricare (predefinito: out/<quiz>-youtube.mp4)")
    ap.add_argument("--miniatura", help="jpg/png (predefinito: out/<quiz>-miniatura.jpg se esiste)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--programma", help="uscita programmata, ora italiana: '2026-11-03 18:00'")
    g.add_argument("--pubblico", action="store_true")
    g.add_argument("--non-in-elenco", action="store_true",
                   help="visibile solo a chi ha il link: per controllarlo prima di pubblicare")
    ap.add_argument("--prova", action="store_true", help="mostra cosa caricherebbe, senza caricare")
    ap.add_argument("--forza", action="store_true", help="ricarica anche se gia' pubblicato")
    a = ap.parse_args(argv)
    carica_env()

    brand = json.load(open(os.path.join(ROOT, "brand.json"), encoding="utf-8"))
    quiz  = json.load(open(a.quiz, encoding="utf-8"))
    base  = os.path.splitext(os.path.basename(a.quiz))[0]
    video = a.video or os.path.join(ROOT, "out", f"{base}-youtube.mp4")
    img   = a.miniatura or os.path.join(ROOT, "out", f"{base}-miniatura.jpg")
    if not os.path.exists(video): sys.exit(f"Video non trovato: {video}\n  Prima: python3 build.py {a.quiz} --formato youtube")

    meta = metadati(quiz, brand, timeline=os.path.splitext(video)[0] + ".json")
    status = {"privacyStatus": "public" if a.pubblico else "unlisted" if a.non_in_elenco else "private",
              "selfDeclaredMadeForKids": False, "containsSyntheticMedia": False, "embeddable": True}
    if a.programma: status["publishAt"] = ora_utc(a.programma)

    uscita = (f"programmato per {a.programma} (ora italiana)" if a.programma
              else "PUBBLICO subito" if a.pubblico
              else "NON IN ELENCO (solo chi ha il link)" if a.non_in_elenco else "PRIVATO (lo rendi pubblico tu da YouTube Studio)")
    print(f"TITOLO   {meta['title']}\nUSCITA   {uscita}\nVIDEO    {video} "
          f"({os.path.getsize(video)/1e6:.0f} MB)\nMINIATURA {img if os.path.exists(img) else '(nessuna)'}"
          f"\n\n{meta['description']}\n\nTAG      {', '.join(meta['tags'])}\n")
    if a.prova: print("--prova: niente caricato."); return

    prima = gia_pubblicato(a.quiz)
    if prima and not a.forza:
        sys.exit(f"Questo quiz e' gia' stato caricato il {prima['quando']}: {prima['url']}\n"
                 "  Usa --forza se vuoi davvero caricarlo di nuovo.")

    token = access_token()
    v = carica(video, meta, status, token)
    vid = v["id"]; url = f"https://youtu.be/{vid}"
    print(f"CARICATO: {url}")
    if v.get("status", {}).get("privacyStatus") == "private" and (a.pubblico or a.programma or a.non_in_elenco):
        print("  ATTENZIONE: YouTube l'ha tenuto PRIVATO. Succede finche' il progetto Google\n"
              "  non supera la verifica API (audit). Rendilo pubblico a mano da YouTube Studio.")
    if os.path.exists(img): miniatura(vid, img, token) and print("  miniatura caricata")
    registra(dict(quiz=os.path.basename(a.quiz), id=vid, url=url, titolo=meta["title"],
                  uscita=status.get("publishAt") or status["privacyStatus"],
                  quando=datetime.date.today().isoformat()))
    return url


if __name__ == "__main__":
    main()
