# Regole assolute — Quiz Video Factory (Quiz Divertenti Italia)

Valgono per OGNI video e OGNI sessione. Non si derogano senza un ordine esplicito di Secondo.

## Lingua
- Rispondi sempre in **italiano** (spagnolo solo per contenuti destinati al team spagnolo).

## Identità visiva (brand QDI) — sempre uguale in tutti i video
- Colori, font e tempi stanno in `brand.json`: non si cambiano nel singolo video.
- **Barra del tempo** su ogni domanda: binario scuro (`barra_traccia`) + barra gialla
  accento che si svuota da destra a sinistra in sincronia col countdown. È un elemento
  di brand: non si toglie, non si sposta, non si ricolora.
- Countdown numerico giallo, badge "DOMANDA N" giallo in alto a sinistra.
- Opzioni A/B/C/D in card bianche con etichetta gialla; risposta giusta in verde,
  le altre spente in grigio.
- Font solo statici: Anton (titoli/domande), Bebas Neue (opzioni/CTA).
- Grafiche ufficiali del canale: cartella Drive **QUIZ DIVERTENTI ITALIA**
  (`bar progress quiz italia.mp4`, `CTA SUBSCRIBE.mp4`, `OUTRO ITALIAN.mp4`) e cartella
  **GRAFICA QDI**. Se diventano raggiungibili (rete o cartella locale), vanno integrate
  e hanno la precedenza sulle versioni generate dal motore.

## Audio
- **Voce narrante nei punti strategici** (intro, cambio livello, risultato finale, CTA)
  ogni volta che un servizio di sintesi vocale è disponibile.
- Se la voce non è disponibile: **solo musica di sottofondo** (+ effetti tick/ding già
  nel motore). Mai video muti, mai musica coperta da copyright.
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
