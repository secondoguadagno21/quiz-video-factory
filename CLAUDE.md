# Regole assolute — Quiz Video Factory (Quiz Divertenti Italia)

Valgono per OGNI video e OGNI sessione. Non si derogano senza un ordine esplicito di Secondo.

## Lingua
- Rispondi sempre in **italiano** (spagnolo solo per contenuti destinati al team spagnolo).

## Identità visiva (brand QDI) — sempre uguale in tutti i video
- Le grafiche ufficiali stanno in `assets/` (elenco in `assets/RISORSE-LEGGIMI.txt`) e
  sono collegate al motore da `brand.json` → `"risorse"`. Hanno SEMPRE la precedenza
  sulle versioni generate; il motore usa le generate solo se un file manca.
- Struttura YouTube: intro QDI → titolo del quiz con mascotte → transizione QDI →
  cartello "LIVELLO N" → domande → CTA "Ti sta piacendo?" (al cambio del livello 2) →
  … → outro QDI (schermata finale con 2 riquadri video, 15 s).
- **Barra del tempo ufficiale** (`assets/brand/barra.mov`, numeri 5→1 e faccina QDI)
  negli ultimi 5 secondi di ogni domanda. Sostituisce il countdown numerico: non si
  toglie, non si sposta, non si ricolora.
- **Logo QDI** in alto a destra su domande, risposte e cartelli livello.
- Sfondo: sfumatura blu del brand + sfondo animato coi punti interrogativi
  (`assets/sfondi`, uno diverso a rotazione per ogni quiz).
- Badge "DOMANDA N" giallo in alto a sinistra. Opzioni A/B/C/D in card bianche con
  etichetta gialla; risposta giusta in verde, le altre spente in grigio.
- Font solo statici: Anton (titoli/domande), Bebas Neue (opzioni/CTA).
- Il formato reel (9:16) usa barra, logo, mascotte, sfondi ed effetti QDI; le clip
  intro/CTA/outro sono 16:9 e restano solo nel formato YouTube.
- Nuove grafiche: si mettono in `assets/brand/` e si collegano in `brand.json`.

## Audio
- **Voce narrante nei punti strategici** (intro, cambio livello, risultato finale, CTA)
  ogni volta che un servizio di sintesi vocale è disponibile.
- Se la voce non è disponibile: **solo musica di sottofondo** + effetti QDI
  (`assets/sfx`: pop alla domanda, click a ogni numero della barra, brillio alla
  risposta giusta, whoosh sui cartelli). Mai video muti.
- Musica: solo da `assets/musica` (Libreria audio di YouTube), **a rotazione**: ogni quiz
  nuovo parte dal brano dopo quello del quiz precedente, i brani si susseguono con
  dissolvenza. Registro in `musica-usata.json`. La musica tace sotto le clip QDI che
  hanno il loro audio. Mai musica coperta da copyright.
- Consegna: stereo 44,1 kHz, −14 LUFS.

## Contenuto
- Formato YouTube di riferimento: 10–12 minuti, ~45 domande, 3 livelli di difficoltà
  crescente, capitoli in descrizione (vedi `ANALISI-RIFERIMENTI.md`).
- Ogni risposta va verificata: niente domande ambigue o con risposte contestabili.
- Risposte giuste distribuite tra A, B, C, D (mai prevedibili).

## Pubblicazione
- Default: **non in elenco** (`--non-in-elenco`) finché Secondo non approva, oppure
  **programmato** (`--programma`). Mai `--pubblico` senza ordine esplicito.
- Categoria 24 (Intrattenimento), lingua it, non per bambini.
- Ogni caricamento finisce in `pubblicati.json`; non si ricarica due volte lo stesso quiz.
