# Messaggio da incollare nella sessione LOCALE di Claude

Copia tutto il blocco qui sotto e incollalo come primo messaggio.

```
Ciao, ti passo un compito dalla sessione cloud del progetto quiz-video-factory.
Rispondimi sempre in italiano, passo per passo: sono su Windows e non sono un tecnico.

OBIETTIVO: autorizzare la pubblicazione sul canale YouTube "Quiz Divertenti Italia".

1. Se non esiste, clona il repo sul Desktop:
   git clone -b claude/wonderful-shannon-1c1wuv https://github.com/secondoguadagno21/quiz-video-factory.git %USERPROFILE%\Desktop\quiz-video-factory
   Se esiste già: entra nella cartella, fai git fetch, git checkout claude/wonderful-shannon-1c1wuv, git pull.
   Se manca git: winget install Git.Git. Se manca python: winget install Python.Python.3.12.

2. Lo script autorizza_youtube.py chiede dati da incollare, quindi NON lanciarlo
   tu dentro la chat: aprimi una finestra separata con
   start cmd /k "cd /d %USERPROFILE%\Desktop\quiz-video-factory && python autorizza_youtube.py"
   Lì incollo ID client e secret (tasto destro + Invio) e premo Consenti nel browser
   con l'account del canale Quiz Divertenti Italia (NON Benessere Network).
   Se il client non mostra più il secret, guidami a crearne uno nuovo ("Aggiungi secret")
   nella pagina del client su Google Cloud Console.

3. Quando ho finito, verifica tu:
   python autorizza_youtube.py --verifica
   Deve dire "PRONTO. Pubblico sul canale: Quiz Divertenti Italia".
   Se dice un altro canale, rifacciamo il punto 2 con l'account giusto.

4. Guidami a copiare le 3 righe YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN
   (le trovi nel file .env della cartella) nelle variabili dell'ambiente cloud "Default"
   (claude.ai/code → ambiente Default → Edit → Environment variables).
   Non mostrarmi né ripetermi i valori in chat: dimmi solo dove sono e come copiarli.

5. Ultimo passo, porta l'app OAuth "In produzione" (Google Cloud Console →
   Schermata consenso OAuth → Pubblica app), così il token non scade dopo 7 giorni.

Non modificare altri file del progetto e non fare push su GitHub.
```

Finito tutto, torna nella sessione cloud e scrivi **fatto**.
