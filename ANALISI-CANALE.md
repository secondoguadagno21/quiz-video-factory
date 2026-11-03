# Analisi del canale Quiz Divertenti Italia — 3 novembre 2026

Dati: `riferimenti/canale-qdi-2026-11-03.json` (100 video, dati pubblici: viste, like, commenti,
tag, descrizioni). Senza YouTube Analytics (CTR, impressioni, fidelizzazione) il giudizio si basa
sulle viste: per misurare davvero serve l'autorizzazione `yt-analytics.readonly`.

## Il canale
232.520 viste, 2.230 iscritti, 100 video dal dicembre 2024. Lingua e categoria corrette ovunque
(it, 24). 45 video hanno i capitoli. 41 titoli iniziano col pallino 🟡.

## Cosa rende (mediana viste per famiglia)
| Famiglia | Video | Mediana | Massimo |
|---|---:|---:|---:|
| Preferisci / cibo | 6 | 1.931 | 9.120 |
| Grammatica / parole difficili | 18 | 1.150 | 51.133* |
| Emoji | 9 | 551 | 2.827 |
| Cultura generale | 16 | 296 | 12.932 |
| Bandiere / geografia | 9 | 176 | 5.383 |
| Calcoli / matematica | 5 | 194 | 756 |
| Live | 5 | 76 | — |
(*il 51k è "Hai mai?", contato anche qui per la parola "italiano")

**Stile copertina vincente del canale**: fascia gialla in alto e in basso con scritta enorme
nera/rossa, raggiera azzurra al centro, una sola immagine forte (Dante, Einstein, libro, SI/NO).

## Regole per le correzioni
- Mai toccare i video oltre 5.000 viste e quelli usciti da meno di 14 giorni.
- 5–6 video per volta, una sola modifica principale per video (titolo O copertina), poi 14 giorni
  di attesa e misura.
- Prima di ogni modifica si salvano titolo, descrizione, tag e copertina originali (si torna indietro).

## Registro modifiche — giro del 3 novembre 2026 (da misurare il 17 novembre)
Originali (copertine e metadati) in `riferimenti/originali-2026-11-03/`. Nuove copertine in `out/correzioni/`.

| Video | Viste al 3/11 | Modifica | Stato |
|---|---:|---|---|
| bVar4Lvqp8k SE ARRIVI A 30/30 | 293 | copertina modello E Ritratto (presentatrice che indica) | FATTO |
| h151qdMqzFw cultura generale ti farà impazzire | 527 | copertina modello E Ritratto (scienziato stupito) + titolo | copertina FATTA, titolo in attesa del permesso |
| fDxenc6BG5Y grammatica 36 parole | 626 | copertina modello E Ritratto (maestra), `out/correzioni/fDxenc6BG5Y-E.jpg` | RIFIUTATA da YouTube (probabile test copertine attivo): caricarla a mano |
| 7aJlDUGdm4A grammatica 2% | 509 | titolo | in attesa del permesso |
| TZzPRNFwgU8 42 domande cultura generale | 710 | titolo | in attesa del permesso |
| 5YWpZ8faWQo 50 domande animali | 212 | copertina modello E Ritratto (ragazzo col cane) | FATTO |
| 9j1lnmvEoek quiz multilingua | 285 | tag | in attesa del permesso |

Titoli e tag: `python3 correzioni.py --applica` dopo la nuova autorizzazione (`youtube.force-ssl`).
