#!/usr/bin/env python3
"""
Applica le correzioni a titoli e tag dei video gia' pubblicati (vedi ANALISI-CANALE.md).
Prima salva sempre l'originale in riferimenti/originali-<data>/.

  python3 correzioni.py              # prova: mostra cosa cambierebbe, non tocca niente
  python3 correzioni.py --applica    # applica davvero

Serve l'autorizzazione con il permesso youtube.force-ssl (python autorizza_youtube.py).
"""
import json, sys, urllib.request, urllib.error
import pubblica
from analizza_video import carica_env

API = "https://www.googleapis.com/youtube/v3/videos"
CORREZIONI = {   # giro del 3 novembre 2026
    "h151qdMqzFw": {"title": "QUESTO QUIZ DI CULTURA GENERALE TI FARÀ IMPAZZIRE! 🤯 Solo il 2% le indovina tutte"},
    "7aJlDUGdm4A": {"title": "Quiz di grammatica italiana che solo i veri esperti superano! 🇮🇹 Solo il 2% passa"},
    "TZzPRNFwgU8": {"title": "SE NE FAI 30 SU 42 SEI UN GENIO! 🧠 Quiz di Cultura Generale impossibile"},
    "9j1lnmvEoek": {"tags": ["quiz multilingua", "quiz lingue straniere", "quiz inglese", "quiz spagnolo",
                             "quiz francese", "test di lingue", "indovina la parola", "quiz italiano",
                             "quiz di cultura generale", "quiz divertenti italia"]},
}

def main(applica):
    carica_env(); t = pubblica.access_token()
    ids = ",".join(CORREZIONI)
    rq = pubblica.richiesta(f"{API}?part=snippet&id={ids}", t)
    for v in json.load(urllib.request.urlopen(rq, timeout=30))["items"]:
        sn = v["snippet"]; nuovo = CORREZIONI[v["id"]]
        print(f"\n{v['id']}")
        for k, val in nuovo.items():
            print(f"  {k}: {sn.get(k)!r}\n     -> {val!r}")
        if not applica: continue
        corpo = {"id": v["id"], "snippet": {k: sn[k] for k in ("title", "description", "categoryId") if k in sn}}
        corpo["snippet"]["tags"] = sn.get("tags", [])
        for k in ("defaultLanguage", "defaultAudioLanguage"):
            if k in sn: corpo["snippet"][k] = sn[k]
        corpo["snippet"].update(nuovo)
        rq = pubblica.richiesta(f"{API}?part=snippet", t, json.dumps(corpo).encode(), "PUT",
                                {"Content-Type": "application/json; charset=UTF-8"})
        try:
            urllib.request.urlopen(rq, timeout=30); print("  FATTO")
        except urllib.error.HTTPError as e:
            err = e.read().decode()
            if "insufficient" in err.lower() or "ACCESS_TOKEN_SCOPE" in err:
                sys.exit("  Manca il permesso per modificare i video: rifai l'autorizzazione "
                         "(python autorizza_youtube.py) e aggiorna YT_REFRESH_TOKEN nell'ambiente.")
            print(f"  ERRORE {e.code}: {err[:300]}")
    if not applica: print("\n(prova: niente modificato. Per applicare: --applica)")

if __name__ == "__main__":
    main("--applica" in sys.argv)
