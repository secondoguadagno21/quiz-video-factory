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
