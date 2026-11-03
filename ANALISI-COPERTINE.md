# Analisi copertine — GK Smart Point (@GKSmartPoint-m7p) — 3 novembre 2026

Canale da seguire **per le copertine e i titoli**, non per il montaggio (video semplici, da non imitare).
Dati completi: `riferimenti/gk-smart-point.json` (76 video, viste, viste al giorno, link copertina).

## Il canale in numeri

- Nato a giugno 2026, **239 iscritti, 482.000 viste totali**, 76 video.
- I video sono sempre **~10 minuti**. Ci sono anche versioni in spagnolo e inglese
  (quelle in inglese non funzionano: 30–160 viste).
- Pochi video fanno quasi tutto: le viste arrivano dalle **copertine**, non dagli iscritti.

| Viste/giorno | Viste | Titolo |
|---:|---:|---|
| 9.796 | 303.696 | SE NE FAI 5 CORRETTE, LA TUA MEMORIA È INCREDIBILE! |
| 3.065 | 45.981 | SE INDOVINI 18 RISPOSTE, HAI UNA MEMORIA SUPERUMANA! |
| 2.232 | 44.647 | NESSUNO RIESCE A SUPERARE QUESTO TEST! (grammatica) |
| 934 | 6.542 | QUESTO QUIZ È BRUTALMENTE DIFFICILE! RIESCI A FARE 10/10? |
| 755 | 8.308 | QUIZ FOLLEMENTE DIFFICILE! RIESCI A FARE 12 RISPOSTE CORRETTE? |
| 649 | 3.895 | SEI NATO PRIMA DEL 1965? |

## La prova regina: stesso testo, immagine diversa

| | Copertina | Risultato |
|---|---|---|
| Vincente | "SE NE FAI 5 CORRETTE, LA TUA MEMORIA È A POSTO" su **bandiera italiana, Colosseo, paesaggio italiano, libri "ITALIANO"**, fascia verde, etichetta rossa "Conoscenze generali" | **303.696 viste** |
| Perdente | **Stesso identico testo** su fondo verde piatto, niente immagini | **530 viste** |

L'identità italiana e un'immagine ricca hanno fatto la differenza (il resto è il favore
dell'algoritmo, che però si guadagna col clic).

## Cosa hanno in comune le copertine che funzionano

1. **Testo enorme, 3–5 righe, occupa metà copertina**, contorno nero spesso.
2. **Parole a colori diversi**: giallo, bianco, rosso, verde, azzurro. Il colore va sul
   **numero** ("18 ESATTI", "10/10", "5 SU 25") e sulla **parola-sfida** ("BRUTALMENTE",
   "SUPERUMANA", "IMBATTIBILE").
3. **Volto espressivo a destra**: stupore, mano sul mento, occhi sgranati. Spesso
   **persone anziane** (nonna coi capelli grigi, signore con la barba bianca, "Einstein"):
   il pubblico è **over 55–60**, e i titoli lo dicono ("NATO PRIMA DEL 1965", "OVER 72").
4. **Simboli italiani**: tricolore, Colosseo, cartina d'Italia, libri "ITALIANO / STORIA / GEOGRAFIA".
5. **Anteprima della domanda vera** (seconda formula vincente): una domanda con le 4
   opzioni A/B/C/D in pillole bianche e lettere in cerchi colorati. Si capisce subito
   cos'è il video. → 44.647 viste (grammatica) e 7.560 ("parte più sporca del corpo").

## Cosa NON funziona

- **Solo testo su fondo piatto** (verde o nero): 200–850 viste.
- **La stessa foto ripetuta** (la stessa donna sorridente in 4 copertine): 250–850 viste.
  Viso neutro, nessuna emozione, nessuna sorpresa.
- Titoli in inglese per un canale italiano.

## Cosa ne prendiamo per Quiz Divertenti Italia

Le copertine QDI attuali (testo su blu + tessere A/B/C/D) somigliano alla categoria
**che non funziona**. Due modelli nuovi da costruire in `miniatura.py`:

**Modello A — "Sfida"** (per i titoli tipo SE NE FAI 30…):
- testo enorme a 4 righe, parole multicolore, numero in rosso/giallo, contorno nero spesso;
- a destra, al posto della foto di una persona, **la faccina 3D grande e stupita**
  (emoji 3D QDI: 😱 🤯 🤔 🧠) o la mascotte QDI: stessa forza emotiva, zero rischi sui diritti
  di immagine e riconoscibile come marchio;
- **tricolore e un monumento italiano** sullo sfondo, fascia colorata dietro il testo.

**Modello B — "Anteprima"** (per quiz con domande forti):
- in alto la frase-sfida ("NESSUNO RIESCE A SUPERARE QUESTO TEST!");
- sotto, **una domanda vera del quiz con le 4 card A/B/C/D** disegnate da `grafica.py`.

**Titoli**: frase-sfida col numero + emoji 🧠🔥 + "| QUIZ DI CULTURA GENERALE";
provare anche la leva età ("SE SEI NATO PRIMA DEL 1970…"), coerente col pubblico over 55.

**Regola**: ogni video esce con **due copertine** (A e B) da alternare col test copertine
di YouTube Studio, così i dati ci dicono quale vince per il nostro pubblico.
