#!/usr/bin/env python3
"""
Autorizza la fabbrica a pubblicare sul TUO canale YouTube. Si fa UNA volta, sul PC
(serve il browser per dire "Consenti").

  python3 autorizza_youtube.py                    # apre il browser, scrive il token in .env
  python3 autorizza_youtube.py --da-token token.json   # riusa il token della vecchia pubblica.py

Prima, nel file .env, servono:
  YT_CLIENT_ID=....apps.googleusercontent.com
  YT_CLIENT_SECRET=....
(Google Cloud Console -> API e servizi -> Credenziali -> client OAuth di tipo "App desktop")

Alla fine stampa le tre righe da incollare nelle impostazioni dell'ambiente cloud.
"""
import argparse, base64, hashlib, http.server, json, os, secrets, sys, threading
import urllib.parse, urllib.request, urllib.error, webbrowser

from analizza_video import carica_env, ROOT

AUTH  = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
SCOPE = " ".join([
    "https://www.googleapis.com/auth/youtube.upload",     # caricare video e miniature
    "https://www.googleapis.com/auth/youtube.readonly",   # sapere su che canale siamo
])


def salva_env(chiavi):
    """Aggiorna (o crea) .env senza toccare le altre righe."""
    p = os.path.join(ROOT, ".env")
    righe = open(p, encoding="utf-8-sig").read().splitlines() if os.path.exists(p) else []
    fatte = set()
    for i, r in enumerate(righe):
        k = r.split("=", 1)[0].strip().removeprefix("export ").strip()
        if k in chiavi:
            righe[i] = f"{k}={chiavi[k]}"; fatte.add(k)
    righe += [f"{k}={v}" for k, v in chiavi.items() if k not in fatte]
    open(p, "w", encoding="utf-8").write("\n".join(righe) + "\n")


def canale(access):
    q = urllib.parse.urlencode({"part": "snippet", "mine": "true"})
    rq = urllib.request.Request(f"https://www.googleapis.com/youtube/v3/channels?{q}",
                                headers={"Authorization": f"Bearer {access}"})
    try:
        it = json.load(urllib.request.urlopen(rq, timeout=30)).get("items", [])
        return it[0]["snippet"]["title"] if it else "(nessun canale su questo account)"
    except urllib.error.HTTPError:
        return "(non verificabile)"


def flusso_browser(cid, secret):
    verifier  = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    stato     = secrets.token_urlsafe(16)
    preso     = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == stato:
                preso.update({k: v[0] for k, v in q.items()})
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            msg = "Fatto! Puoi chiudere questa scheda." if "code" in preso else "Autorizzazione non riuscita."
            self.wfile.write(f"<h2 style='font-family:sans-serif'>{msg}</h2>".encode())
        def log_message(self, *a): pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    redirect = f"http://127.0.0.1:{srv.server_port}"
    url = AUTH + "?" + urllib.parse.urlencode(dict(
        client_id=cid, redirect_uri=redirect, response_type="code", scope=SCOPE,
        access_type="offline", prompt="consent", state=stato,
        code_challenge=challenge, code_challenge_method="S256"))

    print("Si apre il browser. Scegli l'account del canale e premi Consenti.")
    print("Se non si apre da solo, copia questo indirizzo nel browser:\n\n" + url + "\n")
    webbrowser.open(url)
    t = threading.Thread(target=lambda: [srv.handle_request() for _ in range(3) if "code" not in preso])
    t.start(); t.join(timeout=300); srv.server_close()
    if "code" not in preso:
        sys.exit("Nessuna risposta dal browser entro 5 minuti. " + preso.get("error", ""))

    body = urllib.parse.urlencode(dict(code=preso["code"], client_id=cid, client_secret=secret,
                                       redirect_uri=redirect, grant_type="authorization_code",
                                       code_verifier=verifier)).encode()
    try:
        tok = json.load(urllib.request.urlopen(TOKEN, body, timeout=30))
    except urllib.error.HTTPError as e:
        sys.exit("Google ha rifiutato lo scambio: " + e.read().decode()[:400])
    if "refresh_token" not in tok:
        sys.exit("Google non ha dato il refresh token. Revoca l'accesso su "
                 "myaccount.google.com/permissions e rilancia.")
    return tok["refresh_token"], tok["access_token"]


def cerca_file_client(indicato=None):
    """Il file JSON scaricato da Google Cloud (client_secret_....json): lo cerca da solo
    nella cartella del progetto, in Download e sul Desktop."""
    import glob
    casa = os.path.expanduser("~")
    posti = [indicato] if indicato else [
        p for d in (ROOT, os.path.join(casa, "Downloads"), os.path.join(casa, "Download"),
                    os.path.join(casa, "Desktop"), casa)
        for p in sorted(glob.glob(os.path.join(d, "client_secret*.json")), key=os.path.getmtime, reverse=True)]
    for p in posti:
        try:
            j = json.load(open(p, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        dati = j.get("installed") or j.get("web") or {}
        if dati.get("client_id") and dati.get("client_secret"):
            if "web" in j:
                print("ATTENZIONE: questo client e' di tipo 'Applicazione web'. Se Google da' errore\n"
                      "  redirect_uri_mismatch, creane uno di tipo 'App desktop'.")
            print(f"Uso il file client: {p}")
            return dati["client_id"], dati["client_secret"]
    # nessun file: li chiediamo a mano (incolla con il tasto destro del mouse)
    print("\nNon trovo il file del client: li incolli tu, uno alla volta.")
    print("Li trovi in Google Cloud Console -> API e servizi -> Credenziali -> il client 'App desktop'.")
    print("Per incollare nella finestra nera: tasto DESTRO del mouse, poi Invio.\n")
    cid = input("ID client (finisce con .apps.googleusercontent.com): ").strip().strip('"')
    secret = input("Client secret (di solito inizia con GOCSPX-): ").strip().strip('"')
    if not cid.endswith(".apps.googleusercontent.com"):
        sys.exit("Questo non sembra un ID client: deve finire con .apps.googleusercontent.com")
    if len(secret) < 10:
        sys.exit("Il secret sembra incompleto: ricopialo intero.")
    return cid, secret


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--da-token", help="token.json salvato dalla libreria google-auth")
    ap.add_argument("--client", help="file client_secret_....json scaricato da Google")
    ap.add_argument("--verifica", action="store_true",
                    help="controlla le credenziali gia' salvate e dice su che canale pubblica")
    a = ap.parse_args()
    carica_env()

    if a.verifica:
        v = {k: os.environ.get(k, "").strip() for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")}
        manca = [k for k, x in v.items() if not x]
        if manca: sys.exit("NON PRONTO. Mancano: " + ", ".join(manca))
        body = urllib.parse.urlencode(dict(client_id=v["YT_CLIENT_ID"], client_secret=v["YT_CLIENT_SECRET"],
                                           refresh_token=v["YT_REFRESH_TOKEN"], grant_type="refresh_token")).encode()
        try:
            access = json.load(urllib.request.urlopen(TOKEN, body, timeout=30))["access_token"]
        except urllib.error.HTTPError as e:
            sys.exit("NON PRONTO. Google rifiuta le credenziali: " + e.read().decode()[:300])
        print(f"PRONTO. Pubblico sul canale: {canale(access)}")
        sys.exit(0)

    if a.da_token:
        t = json.load(open(a.da_token, encoding="utf-8"))
        cid, secret, refresh = t.get("client_id"), t.get("client_secret"), t.get("refresh_token")
        if not (cid and secret and refresh):
            sys.exit("Nel token mancano client_id, client_secret o refresh_token.")
        body = urllib.parse.urlencode(dict(client_id=cid, client_secret=secret,
                                           refresh_token=refresh, grant_type="refresh_token")).encode()
        try:
            access = json.load(urllib.request.urlopen(TOKEN, body, timeout=30))["access_token"]
        except urllib.error.HTTPError:
            sys.exit("Quel token e' scaduto o revocato: rilancia senza --da-token.")
    else:
        cid    = os.environ.get("YT_CLIENT_ID", "").strip()
        secret = os.environ.get("YT_CLIENT_SECRET", "").strip()
        if not (cid and secret) or "incolla" in cid:
            cid, secret = cerca_file_client(a.client)
        refresh, access = flusso_browser(cid, secret)

    salva_env({"YT_CLIENT_ID": cid, "YT_CLIENT_SECRET": secret, "YT_REFRESH_TOKEN": refresh})
    print(f"\nAutorizzato sul canale: {canale(access)}")
    print("Salvato nel file .env (che resta sul PC).\n")
    print("Per pubblicare anche dal cloud, incolla queste 3 righe nelle variabili")
    print("dell'ambiente Default (accanto a YT_API_KEY):\n")
    print(f"YT_CLIENT_ID={cid}\nYT_CLIENT_SECRET={secret}\nYT_REFRESH_TOKEN={refresh}")
