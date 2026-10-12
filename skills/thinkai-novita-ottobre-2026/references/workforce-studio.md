# Workforce Studio: palette e funzioni nuove (agosto–ottobre 2026)

Fonte: guida ottobre 2026, cap. 11. Per la sintassi DSL, i nomi dei blocchi e il validatore usa la
skill `thinkai-workforce`. **La guida non riporta i nomi DSL dei blocchi nuovi**: dove serve
scrivere codice, `⚠️ DA VERIFICARE` il nome esatto in Studio (Modalità Sviluppatore) prima di usarlo.

## In breve

| Area | Novità | Dove |
|---|---|---|
| Palette nuove | **PDF → Markdown**, **Controlla documento letto** | Gruppi Documenti e AI |
| GestionaleSend | Chiusura ordini e righe, documenti grandi a blocchi, aggiunta righe, gestionale non raggiungibile, prezzo riletto | Operazioni di GestionaleSend (TcRestAPI 1.5.0) |
| Step AI | Allegati con tutti i provider, Xference e NodeLLM nel menu, avvertenza fonti incerte, campo **Ragionamento** | AiAnalysis e step AI |
| Documenti e OCR | OcrImage apre i PDF, PdfExtract più pulito, qualità OCR misurata | OcrImage, PdfExtract |
| RAG | Ricerca anche per parole, pagina di ogni estratto, copertura dichiarata, memoria per domande di seguito, più veloce | RagSearch, RagEmbed |
| Dati e segnaposto | Date giuste su SQL Server in italiano, `{lista[0].campo}`, `{now}` | Query, SqlInsert, SqlUpdate |
| File e webhook | FileList con `outputKey`, pattern calcolati, dimensione e data dei file; WebhookRespond | FileList, JsonToFile, WebhookRespond |
| Studio | Timeline ad albero, Dispositiva Contabile configurabile dalla pagina, video corso e manuale aggiornati | Studio |
| Affidabilità | Idempotenza per tentativo, palette dei moduli spenti rifiutate al salvataggio | Runtime e salvataggio |

## PDF → Markdown

Converte un PDF in **Markdown strutturato** (ricostruisce tabelle, righe, intestazioni dalla
posizione delle parole). Scelta giusta per ordini, distinte e listini con molte righe: l'AI riceve
la tabella già formata e non perde righe (cosa che col testo semplice di PdfExtract può succedere).

| Campo | Uso |
|---|---|
| `filePath` | PDF da convertire (obbligatorio) |
| `paginaDa` / `paginaA` | Intervallo; `paginaA` = 0 → fino all'ultima |
| `intestazioniPagina` | Inserisce «## Pagina N» prima di ogni pagina (predefinito sì) |

Uscite: `lastPdfMarkdown`, `lastPdfMarkdownPages`, `lastPdfMarkdownTableRows`.
**Non è un OCR**: una scansione senza testo fa **fallire** lo step con messaggio che rimanda a
**OcrImage**. Una tabella incerta esce come testo semplice: il contenuto non viene mai scartato.

## Controlla documento letto

Si mette **dopo la lettura AI** di un DDT o ordine: «questa lettura è affidabile?».
1. **Controlla la lettura**: numero e data presenti, righe presenti, quantità positive (anche all'italiana, «1.250,5»).
2. **Controlla sul gestionale** (se configurate le query): codice articolo esiste in anagrafica, quantità plausibile rispetto allo storico, numero documento non già registrato.
3. **Se qualcosa non torna, rilegge** il documento con Claude passandogli i dubbi, ricontrolla e tiene la lettura con meno problemi.
4. **Dà un esito** per il ramo successivo: `ok`, `riletto`, `anomalia`.

Claude si paga **solo sui documenti dubbi** → lo step si abbina bene a una prima lettura con un
modello economico o locale.

| Campo | Uso |
|---|---|
| `input` | La lettura da controllare (JSON della lettura AI) |
| `attachFilePath` | Il documento da rileggere |
| `sqlCodice` | Query: il codice esiste? Segnaposto `{codice}` |
| `sqlQuantita` | Query: quantità minima e massima dallo storico (colonne `minimo` e `massimo`). Segnaposto `{codice}` |
| `sqlNumero` | Query: il numero è già usato? Segnaposto `{numero}` |
| `fattoreQuantita` | Quanto può scostarsi la quantità dallo storico (predefinito 10 volte) |
| `prompt`, `provider`, `model`, `timeoutSeconds` | La rilettura: predefiniti Claude e 300 secondi |
| `outputKey` | Dove scrivere la lettura scelta (predefinito `documentoControllato`) |

Uscite: `documentoControllato`, `lastControlloEsito`, `lastControlloProblemi`, `lastControlloTesto`
(un problema per riga, pronto per la mail all'operatore), `lastControlloProblemiPrimaLettura`.
**Una query sbagliata ferma lo step** (colonna inesistente, sintassi): fallisce col motivo, non
finisce fra le anomalie. Lo scarto delle quantità è descritto come «da X a Y».

```
Lettura AI → Controlla documento letto → Branch su {lastControlloEsito}
   ok / riletto → carica nel gestionale
   anomalia     → sposta in review e manda {lastControlloTesto} all'operatore
```

## GestionaleSend e TcRestAPI 1.5.0

| Novità | Cosa fa | Uscite |
|---|---|---|
| `chiudi-ordine` | Chiude un documento (`docId`). **Solo ORD_CLI, ORD_FOR, DDT_ALL, APP_FOR** | `lastTargetCrossChiusoId` |
| `chiudi-riga` | Chiude una riga (`docRigaId`) | `lastTargetCrossChiusoId` |
| `documento-righe` | Aggiunge righe a un documento esistente (`docId`, `{"RIGHE":[...]}`), con ricalcolo totali | `lastTargetCrossRigheIds` |
| Documenti grandi | `documento` crea il documento con le prime righe e aggiunge le altre **a blocchi**; totali ricalcolati solo sull'ultimo blocco | `lastTargetCrossRigheInserite` se un blocco fallisce |
| Prezzo | La risposta di `articoli-prezzo` codificata in base64 (TcRestAPI 1.4.3) si legge di nuovo | `lastTargetCrossPrice` |
| Gestionale non raggiungibile | Connessione rifiutata o server irraggiungibile: **3 nuovi tentativi dopo 2, 5, 10 s**, poi lo step lo dice | `lastTargetCrossUnreachable` |

- **Righe per chiamata**: campo `righePerChiamata` per agente, predefinito **50**, `0` = non spezzare
  mai. Le API non fissano un limite, ma oltre 40–50 righe la chiamata rallenta e oltre 200 non va
  a buon fine. Se un blocco fallisce l'errore riporta l'id del documento già creato e quante righe sono entrate.
- **Quando il gestionale è fermo**: `lastTargetCrossUnreachable` distingue un gestionale spento da
  un documento sbagliato. Schema consigliato: **una chiamata di test a inizio giro**, il file
  **rimesso in ingresso** se il gestionale cade a metà, i file successivi saltati e **una sola mail
  all'ora** all'assistenza, non una per documento.
- L'editor di GestionaleSend nello Studio mostra solo i campi che servono all'operazione scelta.
- Gli identificatori sopra (`chiudi-ordine`, `chiudi-riga`, `documento-righe`) sono quelli della
  guida; la loro forma esatta nel DSL `⚠️ DA VERIFICARE`.

## Step AI: allegati con ogni provider

Fino a settembre, con un provider ≠ Claude gli allegati venivano **scartati in silenzio**. Ora:

| Provider | Come riceve il documento |
|---|---|
| Claude | PDF e immagini letti direttamente |
| OpenAI | Il PDF in linea, come file |
| Xference, NodeLLM, vLLM, Ollama | Pagine come **immagini JPEG a 200 dpi**: max **20 pagine** per allegato e **40 MB** per chiamata |

- >20 pagine → lo step lo dice in `lastAiWarning`.
- Le regole sui documenti caricabili valgono anche per gli allegati: file non ammesso ferma lo step col motivo.
- Xference e NodeLLM sono nel menu provider. Con Xference il ragionamento è **spento**, salvo che
  nello step si scelga un livello (acceso, la lettura dei DDT era ~6 volte più lenta senza guadagno misurabile).
- I modelli Claude di quinta generazione sono disponibili negli step AI.
- **Fonti incerte** (OCR di bassa qualità, RAG parziale): lo step lo dice da solo al modello, che
  deve segnalare i codici dubbi (0/O, 5/S, 1/I, 8/B) invece di «correggerli». Con fonte buona non aggiunge niente.

## Step AI: quanto ragiona il modello (campo **Ragionamento**, AiAnalysis)

| Valore | Quando |
|---|---|
| *Predefinito* (vuoto) | Come prima: gli agenti esistenti non cambiano |
| **Minimo** | Leggere documenti ed estrarre dati: più veloce ed economico |
| **Basso / Medio / Alto** | Classificazioni difficili, abbinamenti ambigui, ragionamenti su più dati: più lento, più token |

| Provider | Cosa riceve |
|---|---|
| Claude | Ragionamento adattivo con lo sforzo scelto; sui modelli meno recenti un budget di token |
| OpenAI | `reasoning_effort` |
| Ollama | `reasoning_effort` (tradotto per il modello locale) |
| vLLM, NodeLLM, Xference | `reasoning_effort` + accensione del ragionamento per i modelli Qwen, DeepSeek, Gemma |

- Se un modello **non accetta** il livello, lo step **ripete la chiamata una volta** col predefinito
  del modello e lo scrive in `lastAiWarning`; non si ferma.
- **OpenAI con gli strumenti** (step con query SQL o tool, e Dispositiva): accetta gli strumenti solo
  col ragionamento spento. `gpt-5.5` e `gpt-5.4-nano` lo hanno già spento; `gpt-5.6`, `gpt-6-luna`
  e `gpt-6-sol` lo spengono da soli e il livello dello step non si applica (lo dice `lastAiWarning`).
  **`gpt-6.1-sol` e `gpt-6-astra` non si possono spegnere**: negli step con strumenti e nella
  Dispositiva si fermano con messaggio chiaro → scegli altro modello (es. `gpt-6-sol` o `gpt-5.5`).
- **Prima di usare un modello mai provato** fai girare l'agente su un documento vero con due livelli
  e confronta risultati, tempi, token.
- Prova su un calcolo semplice (risposta giusta 187): Haiku 5.5 sbaglia al Minimo e risponde giusto
  da Basso in su; gpt-5.4-nano sbaglia col predefinito e al Minimo, giusto con Basso e Alto; Opus 5.5
  giusto a ogni livello; **Sonnet 5.5 decide da solo**: sotto Alto spesso non ragiona e scrive il
  ragionamento *dentro* la risposta, rompendo un output JSON → **per le estrazioni lascia il Minimo**.
- *Ragionare di più non vuol dire leggere meglio*: su 10 certificati di collaudo lunghi, Sonnet 5.5
  al Minimo ha fatto meno abbinamenti sbagliati di Haiku 5.5 a ogni livello; Haiku al Minimo era il
  più veloce ma su due dei documenti più lunghi ha letto meno della metà delle righe. Il livello giusto si
  sceglie provando sui documenti veri.

## Documenti, OCR e RAG

- **OcrImage** apre anche i PDF scansionati (il tipo si riconosce dal contenuto, non dall'estensione);
  campi `maxPagine` e `dpi` (300). Nuove uscite: `lastOcrPageCount`, `lastOcrPages`,
  `lastOcrQualita` / `lastOcrIncerto` (dicono se è testo vero). Se non estrae testo lo step **fallisce** invece di proseguire vuoto.
- **PdfExtract** non produce più parole lunghe una pagina sui PDF senza spazi; uscita `lastPdfTextPaginato` con i salti pagina marcati.
- **RagSearch / RagEmbed**: ricerca **per parole** oltre che per significato (codici e numeri d'ordine
  si trovano; anche il nome del file entra); ogni estratto dice **da che pagina** viene; blocchi più
  ampi (2.500 car., sovrapposizione 250); la ricerca dichiara la **copertura** (`lastRagCoverage`,
  `lastRagPartial`, `lastRagAvvertenza`); **memoria** per le domande di seguito (`memoryWindowTurns`,
  `memoryScope`, `memoryScopeKey`, da impostare **uguali anche sull'AiAnalysis che segue**);
  ingestione incrementale (documenti invariati non ricalcolati), ricerca ~2× più veloce.
- > **Le raccolte vanno reindicizzate**: il modello di embedding è cambiato (`text-embedding-3-large`,
  > 1024 dimensioni, lo stesso del server MCP) e i vettori si salvano in un nuovo formato:
  > l'aggiornamento **svuota i blocchi esistenti**. Dopo l'aggiornamento rilancia **RagEmbed** sulle raccolte.

## Dati, date e segnaposto

- **Date giuste sui SQL Server in italiano**: prima si poteva ricevere errore di conversione o,
  peggio, giorno e mese scambiati senza errore (10 settembre letto come 9 ottobre). Ora le date vere
  passate a Query, SqlInsert e SqlUpdate vanno in **ISO 8601** e si leggono uguali con qualunque
  lingua del server. **Le date scritte a mano nelle query vanno sempre come `'YYYYMMDD'`.**
- **Indice tra quadre nei segnaposto**: `{lastQueryRows[0].numero}` funziona come
  `{lastQueryRows.0.numero}` (prima restava scritto così com'era, senza errore).
- **`{now}`**: data e ora del server (in SQL in ISO 8601), proposta dallo Studio fra le chiavi disponibili.

| Palette | Novità |
|---|---|
| FileList | Campo `outputKey` (usarla in un ForEach senza svuotare la lista che si sta scorrendo); `pattern` con segnaposto; uscita `lastFileListInfo` con dimensione e data di ogni file |
| JsonToFile | Flag `raw` per scrivere il testo così com'è; su oggetti o liste rimanda a FileWrite |
| WebhookRespond | Decide davvero status, corpo e header della risposta HTTP; se `bodyFromKey` non esiste lo dice ed elenca le chiavi disponibili |
| CodePython | Lettere accentate intatte su Windows, CSV uguale su ogni macchina |

## Studio, idempotenza e sicurezza

- **Timeline**: dettaglio di un passo con dati ad albero, filtro che nasconde i rami senza la parola
  cercata, liste lunghe a blocchi da 50, JSON grezzo a un clic. Quando lo spazio di un'esecuzione si
  esaurisce, dei passi riusciti si toglie solo il contenuto (la riga resta; i passi falliti conservano sempre i loro dati).
- **Dispositiva Contabile** (solo SystemAdmin): installazione tabelle sul gestionale con un pulsante
  (*Setup DB*), creazione dell'agente dalla pagina, scheda *Configurazione* e *Esecuzioni* (copertura e precisione giorno per giorno).
- **Video corso e manuale**: episodi su Controlla documento, GestionaleSend 1.5.0, idempotenza,
  provider AI e allegati, Dispositiva Contabile; tutte le schede *Campi e output* riallineate. La
  regola delle date è nel manuale e nell'aiuto dei campi, quindi la seguono anche assistente,
  copilota, *Genera flusso* e *Genera codice*.
- **Modalità sviluppatore**: un flusso salvato dai nodi con il costruttore di filtri di
  GestionaleSend torna ai nodi senza errori.
- **Palette dei moduli spenti**: al salvataggio, all'import e alla modifica un flusso che usa palette di
  un modulo **non abilitato per il cliente viene rifiutato**, anche se annidate.

> **Idempotenza per tentativo**: la `idempotencyKey` degli step che spostano file o scrivono nel
> gestionale deve contenere un identificativo del **tentativo** (es. `ddt-move-{correlationId}-{logKey}`).
> Con la sola chiave del documento, un file rimesso in ingresso con lo stesso nome verrebbe
> riconosciuto come «già fatto» e **non verrebbe mai rielaborato**. La protezione contro i doppioni
> resta nel gestionale: il controllo che il documento non esista già.
