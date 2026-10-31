# Analisi dei 13 video di riferimento — 31 ottobre 2026

Dati grezzi: `riferimenti-analisi.json` (rigenerabile con `python3 analizza_video.py`).

## Il quadro

| Dato | Valore |
|---|---|
| Video analizzati | 13 su 13 (nessuno privato o rimosso) |
| Canali | 12 da **Quiz Trivia ITA**, 1 da GK Smart Point |
| Durata mediana | **11m 59s** (da 8m 03s a 17m 19s) |
| Viste mediane | 99.597 |
| Capitoli nella descrizione | 0 su 13 |
| Emoji nei titoli | 27 (tutti i 13 titoli ne hanno) |

## Classifica per velocità (viste al giorno)

| Viste/giorno | Durata | Formato |
|---:|---:|---|
| 10.126 | 10m 00s | Cultura generale "SE NE FAI 5 CORRETTE…" (GK Smart Point, 28 giorni) |
| 2.401 | 11m 59s | PREFERIRESTI…? 50 scelte |
| 1.770 | 9m 37s | Brainrot meme dalle emoji |
| 1.497 | 12m 17s | Canzone italiana dalle emoji (40) |
| 1.486 | 15m 23s | 50+ brainrot meme |
| 1.451 | 9m 40s | Storia (40 domande) |
| 999 | 16m 39s | 101 personaggi storici |
| 706 | 17m 19s | 100 loghi in 3 secondi |
| 630 | 8m 08s | Cantante dalla A alla Z |
| 624 | 10m 40s | Cantante dalla canzone (audio) |
| 584 | 11m 59s | Canzone 2020–2026 (audio) |
| 455 | 12m 13s | Scegli un pulsante SÌ/NO |
| 279 | 8m 03s | Calciatore da 3 indizi |

## Cosa ci insegnano

1. **La durata giusta è 10–12 minuti.** I primi sei per velocità stanno tutti tra 9m 37s e 12m 17s.
   I 15–17 minuti non rendono di più.
2. **Il ritmo dipende dal tipo di quiz** (contato dai numeri nei titoli):
   - domanda con 4 opzioni / scelta: **~14 s** (50 scelte in 12m, 40 di storia in 9m 40s)
   - indovina da immagine "in 3 secondi": **~10 s** (100 loghi in 17m, 101 personaggi in 16m 39s)
   - emoji → titolo: **~18 s** (40 canzoni in 12m 17s), serve più tempo per pensare
3. **Il titolo-sfida batte tutto.** "SE NE FAI 5 CORRETTE, LA TUA MEMORIA È INCREDIBILE" fa 10.000 viste
   al giorno: 4 volte il secondo. Ha però lo 0,06% di like (gli altri 0,5–0,8%): è un titolo
   che *aggancia* con l'algoritmo, non che fidelizza. Da usare, ma con contenuto all'altezza.
4. **Formula del titolo:** VERBO IN MAIUSCOLO (INDOVINA / PREFERIRESTI / SCEGLI) + numero
   (40, 50, 100) + soggetto concreto + 2–4 emoji in coda.
5. **Descrizione standard:** 2–3 righe che spiegano la sfida, invito a scrivere il punteggio nei
   commenti, poi il blocco fisso "lascia un like 👍, iscriviti e attiva la campanella 🔔".
   I tag ormai quasi nessuno li usa (solo 4 video su 13).
6. **I commenti li fa la sfida.** Dove il video chiede "scrivi quanti ne hai indovinati" o è un
   tormentone (brainrot), i commenti esplodono (165–242).

## Template per il primo video della fabbrica

- **Formato:** `--formato youtube`, quiz a 4 opzioni, **45 domande** → ~11 minuti
  (con i tempi attuali di `brand.json` è ~14 s a domanda: coerente col riferimento)
- **Titolo modello:** `SE NE FAI 30 CORRETTE SEI UN GENIO! 🧠🇮🇹 | Quiz di Cultura Generale`
- **Seconda scelta:** `PREFERIRESTI…?` — si fa con il motore già pronto (2 opzioni) e non richiede risposte verificate.
- **Da evitare per ora:** quiz audio (canzoni: rischio copyright) e quiz su immagini
  (loghi, personaggi) finché non si sblocca la raccolta immagini.
