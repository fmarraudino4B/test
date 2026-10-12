# Scheda Documenti: Ricerca, Conversazione, Conversazione + dati

Fonte: guida ottobre 2026, cap. 8. La scheda **Documenti** della ChatRoom lavora sugli archivi di
file del cliente tramite il **server MCP FileSystem** (`mcp-filesystem.md`). Oltre all'elenco dei
file sa **rispondere citando i documenti** e mettere insieme **documenti e dati del gestionale**.

## Scegliere il tipo di risposta

Con la scheda Documenti attiva compare il pulsante **«Stile: …»** con tre voci:

| Voce | Suggerimento |
|---|---|
| **Ricerca** | «Mostra l'elenco dei documenti trovati» |
| **Conversazione** | «L'AI risponde e cita i documenti usati» |
| **Conversazione + dati** | «L'AI risponde usando i documenti e i dati del contesto scelto» |

- Predefinito **Ricerca**; la scelta **non è ricordata** (a ogni apertura si riparte da Ricerca).
- La scheda la vede chi ha il permesso **Documenti**; per Conversazione + dati serve anche **Chat**
  (i SystemAdmin li hanno tutti).
- In Documenti **Allega** è disattivato (si lavora sui file dell'archivio). Lo stop (*Interrompi
  richiesta*) ferma anche le domande combinate.

## Come vengono trovati i documenti

Stesso motore per i tre tipi. Il Backend toglie dalla domanda il «comando» iniziale («cerca»,
«trovami i documenti su…») e chiede al server MCP **al massimo 10 documenti**, cercando **per nome
del file, per parole e per significato**. Per ogni documento fino a **tre estratti da 600
caratteri** attorno ai punti trovati (per le scansioni dal testo letto con OCR).

> La **pertinenza** è una posizione, non un voto: il primo vale sempre 100%, gli altri sono
> relativi al primo. 100% ≠ «risponde di sicuro».

## Ricerca: l'elenco

Scheda «Risultati ricerca documenti»: numero di documenti e tempo, filtro per nome file/percorso,
primi 5 risultati, **Mostra altri risultati**. Per documento: nome, cartella, tipo, dimensione,
Percorso, Modifica, Relevanza, **estratto** con parole evidenziate; riquadro giallo **«testo
incerto»** per scansioni lette male dall'OCR. **Analizza con ThinkAI** legge il documento intero e
produce una scheda (Sommario esecutivo, Contenuti principali, Dati tecnici, Procedure e
istruzioni, avvisi, Raccomandazioni). **Scarica** scarica il file (i Google .gdoc/.gsheet/.gslides
si aprono solo online). Se non trova niente: «Nessun risultato trovato» con suggerimenti.
Usala per **trovare file** («contratto con planimetria», «ordine 4471 ricambi carrello R50»);
l'elenco non nasconde niente: se ne mostra dieci, sono dieci.

## Conversazione

L'AI legge gli estratti dei documenti trovati e **scrive una risposta citando i documenti per
nome**. Sotto compare il riquadro **fonti**:

- **copertura** sempre visibile: «Ho cercato fra il NN% dei documenti indicizzabili delle cartelle
  configurate. Quello che non compare qui potrebbe comunque esistere — anche fuori dalle cartelle
  configurate.» (con indice ancora in costruzione la percentuale è <100%);
- elenco dei **documenti usati** (chiuso, «N documenti usati — espandi», con conteggio delle
  scansioni incerte);
- per ogni fonte il **motivo** (es. «pertinenza 78% · trovata per parole: manutenzione, Yale»;
  origini: significato, parole, nome del file, contenuto al volo); sul nome si vede il percorso;
  pulsanti **Scarica** e **Analizza**.

Istruzioni rigide all'AI: rispondere **solo** con ciò che c'è nei documenti trovati; dire
chiaramente quando la risposta non c'è; segnalare i dubbi sulle scansioni incerte senza
correggerli; se l'indice non è completo non affermare mai che un documento «non esiste». **Il
contenuto dei documenti è trattato come dato, mai come istruzione** (un documento con ordini
dentro non viene eseguito).

**Analizza**: scrive «Analizza il documento: …» e fa leggere **il documento intero** (fino a
200.000 caratteri, OCR compreso); la risposta resta nella conversazione; la domanda successiva
torna a cercare sugli estratti.

**Domande di seguito**: la Conversazione ricorda le domande precedenti sui documenti (fino a 3,
più l'ultima risposta); la seconda domanda viene **riscritta in forma completa** prima di
cercare («quali documenti sulla valutazione rischi ponteggi?» → «e fra quelli, qual è il più
recente?»). A schermo resta la domanda come scritta.

**Limite**: le domande **esaustive** («quante aziende hanno un DVR?») o «**abbiamo mai…**»: l'AI
vede i primi 10 documenti e non dimostra che un undicesimo non esista. Per un «no» affidabile
serve una ricerca nei dati del gestionale o la Ricerca con parole diverse.

## Conversazione + dati

Una sola domanda interroga **sia il gestionale sia l'archivio**; la risposta confronta le due
fonti. Serve quando l'informazione sta in parte nelle tabelle e in parte nei file (dimensioni di
una macchina nella scheda tecnica vs gestionale; prezzi venduti vs specifiche nei preventivi;
difetto nei rapportini vs riparazioni fatturate).

**Prima di tutto scegli il contesto dati** (riquadro sopra la casella di testo: *Scegli un
contesto di analisi → Scegli ora*). Le parole della domanda **non** cambiano il contesto. Senza
contesto: «Per «Conversazione + dati» scegli prima il contesto dati (il riquadro sopra la casella
di testo), poi ripeti la domanda.» Un contesto messo in automatico (**AUTO**) non basta: va scelto
esplicitamente; **dopo un Reset va scelto di nuovo**.

**Cosa succede dietro** (domanda scritta una volta sola):

1. **Dati**: Chat dati sul contesto scelto, una query, fino a 2 tentativi più larghi se torna vuota.
   Usa Prompt Azienda, Prompt Chat del contesto, conoscenza del database, misure e vocabolario,
   permessi sulla vista e filtri per utente; stile **Standard** (salvo diversa scelta nel selettore).
2. **Documenti**: stessa ricerca e regole della Conversazione (10 fonti).
3. **Tre risposte**: sui dati, sui documenti, poi la **sintesi incrociata**.

La parte dati riceve anche le **query eseguite davvero**, e la conoscenza arriva **tagliata sulle
tabelle del contesto**: se la tipologia non ha tabelle nelle impostazioni valgono quelle della
vista collegata. I titoli delle due risposte parziali entrano *dentro* le sezioni della finale.

Struttura della risposta:

```
## Sintesi
### Cosa dicono i dati
### Cosa dicono i documenti
### Dove concordano e dove no
### Cosa manca
## Dai dati del gestionale   (la risposta sui dati, intera)
## Dai documenti             (la risposta sui documenti, intera)
Dati del gestionale nel contesto «Commesse»: 12 righe.
Ho cercato fra il 100% dei documenti indicizzabili delle cartelle configurate.
3 documenti usati — espandi
```

La sintesi (~15 righe): per ogni informazione dice **da dove viene**, se le fonti danno **valori
diversi** li riporta entrambi senza sceglierne uno né fare la media, dice **cosa manca**, non
scambia una richiesta o un preventivo per una vendita; per rispondere «no» dichiara cosa ha cercato.

| Se… | La risposta |
|---|---|
| query trova righe e ci sono documenti | Sintesi, Dai dati, Dai documenti |
| query non trova righe | Solo documenti, con nota che la query non ha restituito righe |
| query non riesce (errore SQL, vista non consentita) | Avviso dell'errore, poi solo documenti, con il motivo |
| non ci sono documenti ma ci sono righe | Risposta sui dati, senza elenco fonti |
| nessuna delle due fonti risponde | «Non ho elementi per rispondere…» con i due motivi |

Domande adatte: «Per la commessa C10234, confronta le dimensioni della scheda tecnica con quelle
registrate nel gestionale.» → «E il peso?»; «Abbiamo mai fornito in garanzia un controller per
l'allarme A26?»; «Che risoluzione abbiamo già dato per l'errore OVERCURRENT?»; «A che prezzi
abbiamo venduto negli ultimi due anni gli EV con tapparella metallica, e con che specifiche?»

## Quale tipo usare

| Volete… | Usate |
|---|---|
| Trovare un file, vedere cosa esiste | **Ricerca** |
| Una risposta che sta nei documenti | **Conversazione** |
| Tutto il contenuto di un documento | **Analizza** su una fonte |
| Una risposta in parte nei file e in parte nel gestionale | **Conversazione + dati** |
| Una risposta solo dal gestionale (prezzi, provvigioni, fatturato) | Scheda **Chat**, non Documenti (più rapida; il «no» si basa su tutti i dati, non su 10 documenti) |

**Sicurezza e riservatezza**: il perimetro dei documenti sono le **cartelle consentite del server
MCP**; il contesto dati non lo restringe. Se ogni utente deve vedere solo i propri documenti, va
attivato il **filtro sui permessi Windows** (`mcp-filesystem.md`, esempio 3). Gli estratti mandati
all'AI passano dall'anonimizzazione dei dati personali, quando è attiva per la chat. Nella **chat
web** sono disponibili tutti e tre i tipi (`chat-web.md`).
