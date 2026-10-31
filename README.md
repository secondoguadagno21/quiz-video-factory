# Quiz Video Factory — Etna Wellness

Fabbrica di video quiz verticali (1080x1920) che gira **nel cloud**, comandabile dal telefono.
Nessun software da installare. Nessun Mac acceso.

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

## Cosa manca ancora (e perché)

- **Voce narrante**: la rete di questo ambiente blocca ElevenLabs e OpenAI.
  Si sblocca aggiungendo i domini in Network access delle impostazioni dell'ambiente.
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

### 2. Repo GitHub — BLOCCATO
Il token è scaduto, e da qui un repo nuovo non si crea.
**Come si sblocca:** riconnetti su https://claude.ai/connect-github, poi crea
un repo privato vuoto `quiz-video-factory`. Il commit qui è già pronto a partire.

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

## Da fare, una volta sbloccato

- [ ] Leggere la libreria brand e i materiali dalle cartelle locali
- [ ] Agganciare la pipeline YouTube già esistente (`pubblica.py`, canale
      Benessere Network Etna Wellness, categoria 24 Intrattenimento)
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
