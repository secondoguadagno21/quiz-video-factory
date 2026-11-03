# Quiz Video Factory — Etna Wellness

Fabbrica di video quiz verticali (1080x1920) che gira **nel cloud**, comandabile dal telefono.
Nessun software da installare. Nessun Mac acceso.

## Dove si lavora: tre modi, un solo repo

Il lavoro vive **qui, su GitHub**, non in un ambiente e non su un computer.
Gli ambienti cloud (Default, SHOP BN) sono solo la configurazione della macchina
che lo esegue: rete consentita, chiavi, programmi. Il codice lo prendono da qui.

| Modo | Da dove comandi | Dove gira | Vede le cartelle del PC | PC acceso |
|---|---|---|---|---|
| **Cloud** | telefono o PC | ambiente **Default** | no | no |
| **PC** | il PC | il tuo computer | sì | sì |
| **Remote Control** | telefono | il tuo computer | sì | sì |

Per i quiz si usa l'ambiente **Default**: lì c'è `YT_API_KEY`.

### Installazione sul PC (una volta sola)

**Windows** (PowerShell):
```
winget install Gyan.FFmpeg
winget install Python.Python.3.12
winget install Git.Git
```
Chiudi e riapri PowerShell, poi:
```
pip install numpy
git clone https://github.com/secondoguadagno21/quiz-video-factory.git
cd quiz-video-factory
copy .env.esempio .env
notepad .env
python build.py quiz\divertenti-italia.json
```

**Mac** (Terminale):
```
brew install ffmpeg python git
pip3 install numpy
git clone https://github.com/secondoguadagno21/quiz-video-factory.git
cd quiz-video-factory
cp .env.esempio .env
open -e .env
python3 build.py quiz/divertenti-italia.json
```

Nel file `.env` incolla la chiave YouTube al posto di `incolla-qui-la-chiave`.
Il file `.env` resta sul tuo PC e non finisce mai su GitHub.

### La regola per non perdere niente

Cloud e PC lavorano sullo stesso repo. Per non pestarsi i piedi:
- **prima di cominciare**: `git pull`
- **quando hai finito**: `git add -A`, `git commit -m "cosa ho fatto"`, `git push`

Le sessioni cloud fanno da sole il pull all'avvio; il push lo fanno quando glielo chiedi.

## Come si comanda dal telefono

1. Apri l'app Claude → Code → nuova sessione su questo repo.
2. Scrivi, a voce o a tastiera, una cosa tipo:
   - "Fammi un nuovo video di Quiz Divertenti Italia sul cibo, 6 domande"
   - "Rifai il video di ieri ma con le domande sul calcio"
   - "Cambia il colore accento in arancione e rigenera"
3. Il video finito ti arriva nella chat. Lo scarichi e lo pubblichi.

## Come si usa a mano

```bash
python3 build.py quiz/divertenti-italia.json
python3 build.py quiz/cibo.json --max 6 --out out/cibo.mp4
```

## Struttura

| File | A cosa serve |
|---|---|
| `brand.json` | Colori, font, tempi, CTA. **Qui si cambia la faccia del canale.** |
| `quiz/*.json` | Le banche domande. Un file = un video. |
| `build.py` | Il motore: JSON → MP4. |
| `make_music.py` | Compone la musica di sottofondo originale. |
| `assets/audio/` | I tuoi MP3. Se è vuota, la musica la genero io. |
| `assets/fonts/` | Anton (titoli) + Bebas Neue (opzioni). |
| `out/` | I video finiti. |

## Grafiche e audio del brand QDI

Tutto in `assets/` (elenco completo in `assets/RISORSE-LEGGIMI.txt`), collegato al motore
da `brand.json` → `"risorse"`:

| Cartella | Cosa | Dove finisce nel video |
|---|---|---|
| `assets/brand/` | intro, transizione, barra, CTA, outro, logo, mascotte | struttura del video YouTube, logo in alto a destra, barra sulle domande |
| `assets/sfx/` | pop, click, brillio, whoosh | domanda, numeri della barra, risposta giusta, cartelli livello |
| `assets/musica/` | 10 brani dalla Libreria audio di YouTube | sottofondo **a rotazione** (registro `musica-usata.json`) |
| `assets/sfondi/` | 4 sfondi animati coi punti interrogativi | sfondo di domande e risposte, uno diverso per quiz; il colore ruota a ogni domanda (`tinte_sfondo`) |

Se un file manca, il motore usa la versione generata: un video esce sempre.

## Formato di una banca domande

```json
{
  "titolo": "QUIZ DIVERTENTI ITALIA",
  "sottotitolo": "QUANTE NE SAI?",
  "domande": [
    { "q": "Testo della domanda?",
      "opzioni": ["A", "B", "C", "D"],
      "giusta": 0 }
  ]
}
```
`giusta` è l'indice da 0: 0=A, 1=B, 2=C, 3=D.

## Tempi e durata

Con i valori in `brand.json` (intro 2s, domanda 5s, risposta 2,2s, outro 3s):

| Domande | Durata | Dove sta bene |
|---|---|---|
| 4 | ~34s | Reels / TikTok |
| 5 | ~41s | Reels / Shorts |
| 8 | ~63s | Shorts / Facebook |

Render: circa **0,9 secondi di macchina per ogni secondo di video**.

## Regole d'oro imparate sul campo

- **I testi vanno su file, mai inline** nei filtri `drawtext`: altrimenti accenti,
  apostrofi e virgole italiane rompono il comando. Il motore lo fa già.
- **Font variabili no.** ffmpeg li renderizza nel peso più leggero e il video esce
  illeggibile. Solo font statici (Anton, Bebas Neue).
- **Sfondo generato una volta sola** e messo in loop: il filtro `gradients` si anima
  e tra uno spezzone e l'altro si vedrebbe lo scatto di luce.
- Domanda max ~26 caratteri per riga, opzioni corte: su telefono si legge a colpo d'occhio.

## Musica

Ogni video esce con musica di sottofondo. Due strade:

**1. Musica generata (predefinita).** Se `assets/audio/` è vuota, il motore compone
la traccia su misura per la durata esatta del video: 100 BPM, giro Am–F–C–G,
basso, accordi, arpeggio e ritmica. È **originale**, quindi nessun rischio di
strike o di audio mutato su TikTok, Reels o Shorts.

```bash
python3 make_music.py --dur 45 --out assets/audio/bed.wav   # per sentirla da sola
```

**2. La tua musica.** Metti un MP3 in `assets/audio/` e viene usato quello
(va in loop e si adatta alla durata). Oppure indicalo al volo:

```bash
python3 build.py quiz/divertenti-italia.json --music ~/mia-traccia.mp3
python3 build.py quiz/divertenti-italia.json --music-vol 0.25   # più discreta
python3 build.py quiz/divertenti-italia.json --no-music
```

Il volume predefinito è `audio.volume_musica` in `brand.json` (ora 0.40).

**Audio di consegna:** stereo 44,1 kHz, −14 LUFS. È il livello con cui i social
normalizzano: il video non viene né abbassato né schiacciato in pubblicazione.
Il mix è pesato sui medi, perché i telefoni i bassi non li riproducono.

## Voce narrante

Voce del canale: **"Kira"** su Google AI Studio, espressione **"promozione"**, stile
**"High energy, elongate vowels"** — femminile, giovane, squillante.
Il piano gratuito di Gemini concede **10 richieste TTS al giorno**, e frase per frase un
quiz da 51 domande ne chiede ~110. Per questo il video si legge in un **audio unico**:

```bash
python3 voce.py --copione quiz/x.json            # il copione: out/x-copione.txt
# -> leggerlo in AI Studio con la voce Kira, scaricare il .wav
python3 importa_voce.py quiz/x.json --audio voce.wav --trascrivi   # taglia nelle frasi
python3 build.py quiz/x.json --formato youtube
```

`importa_voce.py` ascolta l'audio in locale (faster-whisper, `pip install faster-whisper`),
trova l'istante di ogni parola, lo allinea al copione e taglia sulle pause vere; prima
mostra la tabella dei tagli e si ferma se una frase ha una durata strana. Accetta anche
un SRT (`--srt`), ma gli SRT automatici sbagliano lettere e numeri: meglio `--trascrivi`.
Le frasi che mancano le chiede a Gemini, se c'è la chiave: l'API serve solo per i ritocchi.

## Effetti grafici

Card delle risposte che entrano con un rimbalzo, domanda che scivola dall'alto,
risposta giusta che pulsa con un'esplosione di coriandoli QDI, raggi di luce che girano
dietro titolo e cartelli dei livelli. Tutto disegnato da `grafica.py` (Pillow) e montato
da `build.py`: nessun programma esterno.

## Cosa manca ancora (e perché)
- **Filmati stock di sfondo**: Pexels e Pixabay sono bloccati dalla stessa regola.

---

# Il piano completo

## Formati

| Formato | Misure | Dove | Comando |
|---|---|---|---|
| `reel` | 1080x1920 | TikTok, Reels, Shorts | `--formato reel` (predefinito) |
| `youtube` | 1920x1080 | YouTube | `--formato youtube` |

```bash
python3 build.py quiz/cibo.json --formato youtube --max 85   # ~20 minuti
```

### Quante domande servono (formato youtube)

| Domande | Durata |
|---|---|
| 30 | 7m 18s |
| 50 | 11m 58s |
| **85** | **20m 08s** |
| 130 | 30m 38s |
| 170 | 39m 58s |

**Il collo di bottiglia non è il render, è la banca domande.**
Il render gira a 0,68x il tempo reale: 20 minuti di video in ~14 minuti di macchina.
Ma 85 domande vanno scritte, verificate e rese divertenti. È lì che serve il lavoro.

## Cosa serve sbloccare (in ordine di importanza)

### 1. Cartelle del tuo computer — BLOCCATO
Nessuna cartella risulta condivisa. Senza, restano irraggiungibili la libreria
brand Italia, gli audio e i materiali YouTube.
**Come si sblocca:** sul tuo computer, app Claude → Impostazioni → Claude Code →
Remote Control, e scegli le cartelle (quiz video, YouTube).

### 2. Repo GitHub — FATTO
Il codice vive in `secondoguadagno21/quiz-video-factory` (privato).
Ogni sessione nuova su questo repo ritrova la fabbrica intera.

### 2-bis. Chiave YouTube — FATTO
`YT_API_KEY` salvata nelle impostazioni dell'ambiente, limitata alla sola
YouTube Data API v3. Abilita `analizza_video.py` e `scopri_video.py`.
Note per la pubblicazione automatica: il client OAuth `pubblica-quiz` dello
stesso progetto ha il token che scade ogni 7 giorni finché l'app resta in
modalità Test. Va portata In produzione prima di automatizzare.

### 3. Rete chiusa — BLOCCATO
Questa singola impostazione blocca da sola **tre** cose che hai chiesto:

| Serve per | Dominio bloccato |
|---|---|
| Voci narranti | `api.elevenlabs.io`, `api.openai.com` |
| Foto e filmati stock | `pixabay.com`, `api.pexels.com` |
| Ricerca video da emulare | quasi tutto il web |

**Come si sblocca:** menu dell'ambiente cloud nella barra del titolo → Edit →
Network access. Aggiungi i domini, lascia spuntato "Allow package managers".

### 4. Airtable — NON CONNESSO
Il server Airtable non si collega (403 dal proxy). Senza, niente pesca
automatica dei video da emulare.

## Short che promuovono il video lungo

```bash
python build.py quiz/shorts/cultura-generale-genio-short1.json --formato reel --music "assets/musica/Corny Candy - The Soundlings.mp3"
python pubblica.py quiz/shorts/cultura-generale-genio-short1.json --video out/cultura-generale-genio-short1-reel.mp4 --non-in-elenco
```

Nel JSON dello short: `cta_finale`, `cta_sotto`, `cta_immagine` (miniatura del lungo),
`durata_intro`, `durata_cta`, `voce.hook`, `voce.cta`, `voce.solo_registrate`. Il finale
(`invito()` in build.py) mostra "Prova il quiz completo", la miniatura e una freccia che
rimbalza verso il video correlato. Le regole sono in CLAUDE.md.

## Pubblicazione su YouTube

Catena completa in un comando:
```bash
python3 fabbrica.py quiz/cultura-generale-genio.json --non-in-elenco
python3 fabbrica.py quiz/cultura-generale-genio.json --programma "2026-11-03 18:00"
```
`build.py` → `miniatura.py` → `pubblica.py`. Titolo, descrizione, tag, capitoli e testi
della miniatura stanno nel blocco `"youtube"` della banca domande.

### Attivarla (una volta sola, sul PC)
1. Google Cloud Console, stesso progetto della chiave → API e servizi → Credenziali →
   Crea credenziali → **ID client OAuth** → tipo **App desktop**.
2. Copia ID client e secret nel file `.env` (vedi `.env.esempio`).
3. `python autorizza_youtube.py` → si apre il browser → account del canale → Consenti.
   Il token si salva da solo in `.env` e lo script stampa 3 righe.
4. Incolla quelle 3 righe nelle variabili dell'ambiente cloud **Default**.
   Da lì il cloud pubblica senza PC acceso.
5. Schermata consenso OAuth → **Pubblica app** (In produzione): in modalità Test il
   token scade ogni 7 giorni.
6. **Verifica API (audit)**: Google blocca come *privati* i video caricati da progetti
   non verificati. Finché il modulo "YouTube API Services – Audit and Quota Extension"
   non è approvato, ogni video esce privato e va reso pubblico a mano da YouTube Studio
   (un tocco dall'app). Dopo l'audit, la programmazione funziona da sola.
7. Miniature personalizzate: il canale deve essere verificato col telefono (youtube.com/verify).

## Da fare, una volta sbloccato

- [x] Analizzare i 13 video di riferimento → `ANALISI-RIFERIMENTI.md`
- [ ] Leggere la libreria brand e i materiali dalle cartelle locali
- [x] Pipeline di pubblicazione YouTube (`pubblica.py`, `fabbrica.py`) — manca solo l'autorizzazione OAuth
- [ ] Template per tipo di quiz: emoji film, bandiere, immagini, indovinelli
- [ ] Voci narranti sulle domande
- [ ] Raccolta immagini per i quiz visivi
- [ ] Airtable come fonte di ispirazione e come calendario editoriale
- [ ] Comando programmato: 3 video a settimana, generati e pubblicati da soli

## Quello che manca da te

La struttura dei tuoi video quiz. Il quiz **emoji film** di oggi non è
visibile da qui: girava in locale e non è sincronizzato. Serve che tu lo
incolli, o che condivida la cartella (punto 1).
È da lì che nasce l'educazione del sistema: template, ritmo, tono, durate.
