# Pattern e Anti-pattern — flussi DSL ThinkAI WorkForce Studio

> Ricettario operativo derivato SOLO da fatti tracciati: le 4 esportazioni di flusso in vista DSL (F1=`...\Nuova cartella\Flusso.js`; F2/F3/F4=`...\Manuale — ThinkAI WorkForce Studio\Flusso2/3/4.js`), le avvertenze del catalogo manuale (`manuale-clean.md`, rif. `L####`) e un quinto flusso reale, **GAZZA Ordine Cliente v1.4.1** (`GAZZA_Ordine_Cliente__v1.4.1.thinkaiagent.json`), fornito come **export JSON** (non vista DSL): per questo si cita `GAZZA:#N` = numero d'ordine (`Order`) dello step nell'export, non un numero di riga di codice — e i suoi step annidati come `GAZZA:#N→contenitore#M` (es. `GAZZA:#9→itemErrorSteps#2`). Ogni voce cita `Flusso:riga` o `GAZZA:#N` per gli esempi e `L####` per la regola di catalogo.
>
> **Regole di lettura.** I nomi-blocco DSL provengono solo da `references/nomi-blocchi.md` (autorità) e sono ora **tutti confermati** (15 dai flussi, gli altri dal video corso). `⚠️ NON DOCUMENTATO` = presente nei flussi ma non nel manuale. `⚠️ non osservato` = documentato nel manuale ma mai usato nei 4 flussi. Le deduzioni sul comportamento del motore sono marcate *(inferenza)*: la vista a codice è un DSL, non codice eseguito (L8).

---

## PARTE A — Pattern consigliati

Pattern osservati nei flussi o documentati dal corso/manuale. Ognuno: **Quando** applicarlo, **Come** costruirlo, **Esempio** con `Flusso:riga` (o riferimento al corso quando la fonte è il video).

### A1 — Estrai/Classifica con `responseFormat: text|json` PRIMA di un Branch/Switch/CodeJs

- **Quando:** l'output di un `AiAnalysis` (o `ExtractStructured`) deve pilotare una condizione (`if`/`switch`) o essere parsato da `CodeJs`.
- **Come:** imposta `responseFormat: "text"` per una parola/etichetta secca, `"json"` per dati strutturati. **Mai `"report"`**: `report` è destinato a una persona e aggiunge branding/footer che rompe il confronto (L38). Con `json` il motore fa anche strip+parse in `lastAiJson` (L38).
- **Esempio (positivo):** F1:47 e F1:55 estraggono testata/righe con `responseFormat: "json"`; l'output normalizzato da `CodeJs` alimenta poi il Branch `if ($.controllaEsito == true)` (F1:612). `ExtractStructured` produce `lastExtractedJson` (L121) consumato a valle in F4:114.
- **Controesempio:** F4:11 classifica con `responseFormat: "report"` e alimenta `if ($.isOrdine == ordine)` (F4:27) — vedi Anti-pattern B4.
- **Rif:** regola L38; positivi F1:47, F1:55, F4:114.

### A2 — RAG: `lastRagContext` → prompt di `AiAnalysis`

- **Quando:** l'AI deve rispondere/estrarre usando la base di conoscenza (ricerca semantica) invece che a memoria.
- **Come:** esegui prima lo step RAG di ricerca, poi interpola `{lastRagContext}` nel `prompt` dell'`AiAnalysis` seguente. Output disponibili: `lastRagContext` (testo pronto, L77), `lastRagHits` (chunk con score, L76), `lastRagHitCount` (L78).
- **Nome-blocco:** "Cerca nella conoscenza (RAG)" = `RagSearch`; "Indicizza conoscenza (RAG)" = `RagEmbed` — entrambi ✅ CONFERMATI dal video corso (modulo 10).
- **⚠️ non osservato:** nessuno dei 4 flussi usa RAG (dominio unico import-documenti, `sintassi-dsl.md`). Cross-ref documentata ma mai vista in esecuzione.
- **Rif:** regola L61, L76-78.

### A3 — ForEach con cap iterazioni (e pausa per rate-limit)

- **Quando:** si itera su una lista che può crescere (mail, file) e a ogni giro si chiamano AI/API esterne.
- **Come:** anteponi al `for...of` l'annotazione `// @foreach maxIterations=N` per limitare i giri (param `maxIterations`, default 1000, L2712). Per rispettare i rate-limit delle API esterne il manuale prevede sul ForEach `delayBetweenMs` (pausa tra iterazioni, L715), `batchSize` (blocchi con pausa fra blocchi, L713) e `maxConcurrency` (parallelismo max 8, L714).
- **Esempio:** F4:6 `// @foreach maxIterations=20` sopra `for (const item of lastEmails)` (F4:7).
- **⚠️ non osservati:** `delayBetweenMs`, `batchSize`, `maxConcurrency` sono documentati (L713-715) ma **mai usati nei 4 flussi**; nei flussi il throttling non è presente. `// @foreach` è una forma-decoratore **⚠️ NON DOCUMENTATA** come tale nel manuale (solo il concetto/param esiste).
- **Rif:** L2712 (osservato F4:6); L713-715 (non osservati).

### A4 — `CodeJs` per normalizzare / validare / deduplicare

- **Quando:** l'output AI o SQL va ripulito, validato o trasformato con logica reale (parse tollerante, conversione numeri, dedup, controllo quadrature) — cose che il DSL puro non fa.
- **Come:** `CodeJs({ outputKey: "..." }, () => { ... })`. Dentro l'arrow-function gira JS reale: `stepData` (stato mutabile r/w), `$input` (snapshot in sola lettura), lettura difensiva `stepData.X || $input.X || <fallback>`, commit con `Object.assign(stepData, result)`. L'`outputKey` è arbitrario (L3288-3291).
- **Esempio:** F1:159-189 definisce `parseLoose` (JSON tollerante), `toNum` (normalizza `167,280`→167,28), `validate` (righe sospette) e ricalcola la quadratura documento; commit `Object.assign(stepData, result)` (F1:149).
- **Nota:** i blocchi-collezione a catalogo (Sort/Filter/Merge/Aggregate/Remove Duplicates/Rename Keys) esistono ma **non sono osservati**: nei flussi queste operazioni sono fatte a mano in `CodeJs` (`sintassi-dsl.md`).
- **Rif:** L3288-3291; esempi F1:159-189, F1:149.

### A5 — "Catch" dell'output AI prima che lo step AI successivo lo sovrascriva

- **Quando:** due o più `AiAnalysis` in sequenza; ognuno riscrive `lastAiOutput` (L57), quindi l'output del primo va salvato prima di lanciare il secondo.
- **Come:** subito dopo l'`AiAnalysis`, inserisci un `CodeJs` che copia `lastAiOutput` in una chiave applicativa dedicata: `stepData.miaChiaveRaw = (stepData.lastAiOutput || $input.lastAiOutput || '')`.
- **Esempio:** F1:48-53 `catchTestata` salva `stepData.testataJsonRaw` dopo l'agente testata; F1:56-60 `catchRighe` salva `stepData.righeJsonRaw` prima dell'agente footer.
- **Rif:** output `lastAiOutput` L57; esempi F1:48-53, F1:56-60.

### A6 — Cleanup di StepData tra le iterazioni del loop

- **Quando:** un `for...of` rielabora oggetti diversi (un PDF/mail per giro) e le chiavi del giro precedente rischiano di "sanguinare" nel successivo (lette con fallback `|| ''`).
- **Come:** primo step dentro il loop = `CodeJs` che fa `keys.forEach(k => delete stepData[k])` sulle chiavi applicative del giro. **NON** cancellare la chiave che alimenta il loop (`lastFileList`) né `__loopItem` (gestito dall'engine) — vedi commento F1:10-12.
- **Esempio:** F1:13-45 `cleanupOrdine` (azzera testata, righe, esiti, output intermedi a inizio giro); F1:485-493 `cleanupArticoli` (scarta temporanei per-riga e il JSON query già consumato).
- **Rif:** esempi F1:13-45, F1:485-493.

### A7 — Rilettura mirata via coda `[1]`

- **Quando:** un primo passaggio AI produce elementi "sospetti" (es. righe con quadratura incoerente) e serve un secondo giro solo su quelli, senza rileggere tutto.
- **Come:** in un `CodeJs`, popola una chiave-coda con `[]` = nessuna rilettura oppure `[1]` = un passaggio (`rilettureQueue: sospette.length > 0 ? [1] : []`, F1:147). Poi `for (const item of rilettureQueue) { ... }`: il corpo gira 0 o 1 volta. Prima di entrare nel loop di rilettura, cattura i valori dell'outer loop (es. `pdfPath` = `__loopItem`, F1:139) perché il ForEach interno **ombreggia** `__loopItem` dell'esterno (commento F1:138).
- **Esempio:** F1:147 crea `rilettureQueue`; F1:155 `for (const item of rilettureQueue)`; F1:156 rilegge solo `{righeSospetteList}`.
- **Rif:** esempi F1:147, F1:155-156, F1:138-139.

### A-bonus — `@continueOnFail` + Branch di verifica su step esterni

- **Quando:** uno step esterno che può fallire (registrazione ERP) e vuoi gestire l'esito invece di far crashare la run.
- **Come:** annota `// @continueOnFail` sopra lo step (concetto L9: salta l'errore e prosegue), poi verifica l'esito in un `CodeJs`/Branch a valle.
- **Esempio:** F1:613 `// @continueOnFail` sul `GestionaleSend` documento, poi F1:617 `checkDoc` valuta se il documento è stato creato. In F4:167 stesso schema prima del Branch F4:171.
- **⚠️:** la forma-decoratore `// @continueOnFail` è **NON DOCUMENTATA** come tale (esiste il concetto, non la sintassi-commento); assente lo stile `@alias` in F2. Nota inoltre B5/B6: il Branch di verifica di F1 si appoggia a chiavi non a catalogo.
- **Rif:** concetto L9; esempi F1:613, F1:617, F4:167-171.

### A8 — Idempotenza degli effetti esterni (chiave business stabile)

- **Quando:** uno step con **effetto esterno ripetibile** (`SendEmail`, `HttpCall`, `GestionaleSend`, `SqlInsert`/`SqlUpdate`, `FileMove`) in un flusso che può ri-eseguire: retry dopo crash, trigger di polling, o dentro un `for...of`. Senza protezione, un secondo giro crea due volte lo stesso ordine/mail/record.
- **Come:** configura sullo step tre parametri — **`idempotencyKey`** (stringa, identificativo business stabile: es. numero documento + fornitore, o un hash `codCf|numeroOrdine|dataOrdine`), **`idempotencyGroup`** (stringa, raggruppa logicamente più step correlati, es. tutte le notifiche finali di un flusso), **`idempotencyRetryOnFailure`** (sì/no, riprova l'effetto se il tentativo precedente è fallito senza confermare l'esito). Dentro un ForEach includi anche l'elemento corrente (`{__loopItem}` o un suo campo/il correlation id del giro), così ogni item ha la sua chiave. **Non** usare `{timestamp}`, `{now}` o GUID casuali: renderebbero ogni retry un effetto "nuovo" e annullerebbero la protezione.
- **Perché:** il motore tiene un journal degli effetti esterni; dopo un crash marca l'effetto `Started`/`Uncertain` e lo blocca per non ripeterlo alla cieca (in Monitoraggio compaiono fra gli "Effetti da verificare"). Una buona chiave identifica l'**effetto aziendale**, non la run.
- **✅ Nomi-parametro CONFERMATI** (flusso reale esportato **GAZZA Ordine Cliente v1.4.1**, `GAZZA:#N` = numero d'ordine dello step nell'export JSON): `idempotencyKey`/`idempotencyGroup`/`idempotencyRetryOnFailure` compaiono letteralmente su `SqlInsert` (es. `"gazza-log-start-{fileCorrelationId}"`, `GAZZA:#9→itemErrorSteps#2`), `SqlUpdate` (`"gazza-log-final-{fileCorrelationId}"`, `GAZZA:#9→itemErrorSteps#3`), `SendEmail` (`"gazza-email-technical-{fileCorrelationId}"`, `GAZZA:#9→itemErrorSteps#4`) e `FileMove` (`"gazza-move-technical-{fileCorrelationId}"`, `GAZZA:#9→itemErrorSteps#5`) — quindi la cautela precedente ("nome non enumerato, verificare in Studio") è superata per questi 4 blocchi: usa questi nomi esattamente. Restano da riconfermare su altri blocchi (`HttpCall`, `AiAnalysis`) dove il concetto è citato dal corso ma non ancora osservato con questi nomi esatti.
- **Guardia aggiuntiva osservata:** dopo un `SqlInsert`/`SqlUpdate` "di apertura" di un log/claim, verifica `lastInsertRowCount === 1` (o `lastUpdateRowCount === 1`) e fai `throw` se diverso — intercetta corse critiche fra run concorrenti sulla stessa chiave di correlazione (vedi anche A12).
- **Rif:** video corso M7/M20 (concetto); `GAZZA:#9` (nomi-parametro confermati); vedi anche `esempi.md` §5 e §6 (flusso senza duplicazioni).

### A9 — Intake email affidabile con MailPolling durevole + Mail Disposition

- **Quando:** un agente deve elaborare le email in arrivo in modo affidabile, senza doppioni, con archiviazione/marcatura a fine lavorazione (es. bolle/ordini che arrivano via mail).
- **Come:** usa il **trigger MailPolling durevole** (credenziale IMAP cifrata, cartella sorgente, eventuale agente *worker*). Il trigger crea **una run per messaggio**: lavora sul singolo messaggio leggendo `lastEmail`, `inboundEmlPath` e `lastEmailAttachments` (`ForEach` **solo** sugli allegati della mail, **mai** sulle mail). Chiudi il worker con **un unico `MailDisposition` top-level finale** (`action` move/markRead, `outcome` `processed`/`review`). Proteggi gli effetti esterni con una idempotencyKey derivata da `inboundMailId`/identificativo business (vedi A8).
- **Perché:** il trigger tiene un journal e usa un *claim* SQL che impedisce doppie elaborazioni anche con più sorgenti sullo stesso worker; un `ForEach` sulle mail sarebbe ridondante e scorretto (una run = un messaggio). `MailDisposition` chiude il journal (`processed`/`review`) e sposta/marca la mail: il validatore ne richiede **esattamente uno** top-level, **non annidato**.
- **⚠️ Fonte:** video corso M3 «Trigger», M4 (credenziale IMAP + preflight), M15 «Mail Disposition», M7 «Posta in ingresso durevole» (SSOT). Il **blocco** `MailRead` (batch → `lastEmails`, iterabile) è un caso diverso: vedi `blocchi/comunicazione.md`.
- **Rif:** corso M3/M4/M15; `blocchi/comunicazione.md` (Mail Disposition); `modello-esecuzione.md §1.1`.

### A10 — Preflight fail-closed prima di elaborare qualunque item

- **Quando:** un agente in produzione (schedulato/cartella, senza supervisione umana per ogni run) dipende da prerequisiti che possono mancare al primo avvio o dopo una modifica ambientale: configurazione applicativa non compilata, connessione al gestionale non raggiungibile, tabelle/colonne custom del DB non ancora create.
- **Come:** apri il flusso con una sequenza di controlli **bloccanti**, ognuno seguito da un `Branch` che, se il controllo fallisce, esegue `StopAndError` (o l'equivalente `throw new Error(...)` fuori da un loop) e **non** procede oltre: (1) valida con `CodeJs` i valori di configurazione obbligatori (regex su email, stringhe non vuote, non ancora sui valori segnaposto tipo `CONFIGURARE_...`); (2) chiama `GestionaleSend` con `endpoint:"test"` per verificare che l'ERP/WS sia raggiungibile; (3) esegui una `Query` su `INFORMATION_SCHEMA.TABLES`/`INFORMATION_SCHEMA.COLUMNS` per contare che le tabelle e colonne custom richieste esistano davvero (conta esatta, non solo `> 0`), poi un `CodeJs` che confronta i conteggi attesi e produce un flag `...Ready`.
- **Perché:** un agente "fail-open" che parte comunque con prerequisiti mancanti produce risultati silenziosamente sbagliati (es. scrive in una tabella che non esiste ancora, o interpreta un errore di connessione come "nessun dato"). Il fail-closed sposta l'errore a un punto solo, esplicito e presto, con un messaggio operativo diretto (non un errore tecnico generico).
- **Esempio:** `GAZZA:#1-#7` — assignment di configurazione (`#1`) → `CodeJs` di validazione + `Branch`/`StopAndError` (`#2-#3`) → `GestionaleSend endpoint:"test"` (`#4`) → `Query` su `INFORMATION_SCHEMA` che conta 4 tabelle + 6 colonne auto-learning + 2 colonne di audit (`#5`) → `CodeJs` di validazione schema + `Branch`/`StopAndError` (`#6-#7`) → solo dopo, `FileList` dei documenti da elaborare (`#8`).
- **Rif:** `GAZZA:#1-#8`.

### A11 — Recovery per-item nel `ForEach` invece di `throw` (alternativa a B2)
- **Quando:** un `ForEach` elabora un batch (file/righe/messaggi) e vuoi che il fallimento di **un singolo item** non fermi gli altri, ma venga comunque loggato, notificato e "chiuso" in modo pulito (spostamento del file sorgente in una cartella d'errore, riga di audit aggiornata).
- **Come:** sul blocco `ForEach` imposta `continueOnItemError: true` (l'item che fallisce non interrompe la run) e, se vuoi che l'esecuzione del ForEach nel suo complesso risulti "fallita" per il monitoraggio pur avendo processato gli altri item, `failOnItemErrors: true` con `failedItemsKey` (accumula gli item falliti). Popola `itemErrorSteps` con la sequenza di recovery: un `CodeJs` che legge `stepData.__lastItemErrorMessage` e prepara un messaggio/riga di log, uno `SqlInsert`/`SqlUpdate` idempotente per marcare l'errore nel log (vedi A8), un `SendEmail` di notifica, un `FileMove` (con `allowedRoot`) verso una cartella d'errore dedicata.
- **Perché:** è l'esatto opposto, sicuro, dell'Anti-pattern B2 (`throw` dentro un ramo del loop che interrompe l'intera run): qui l'item problematico viene isolato, tracciato e "archiviato", mentre il batch prosegue sugli item successivi.
- **Esempio:** `GAZZA:#9` (il `ForEach` esterno sui PDF) porta `itemsKey:"lastFileList"`, `continueOnItemError:true`, `failOnItemErrors:true`, `failedItemsKey:"failedGazzaOrders"` e un `itemErrorSteps` di 5 step (log tecnico → riapertura idempotente del log se mancante → chiusura idempotente del log in errore → notifica idempotente → `FileMove` idempotente in cartella errore).
- **Rif:** `GAZZA:#9`; vedi `blocchi/flusso.md` (ForEach, parametri `itemErrorSteps` ecc.); contrasta con Anti-pattern B2.

### A12 — Claim atomico anti-race su risorse a file (crash/retry-safe)

- **Quando:** più run dello stesso agente (o run che si sovrappongono per un crash/restart) potrebbero elaborare **due volte lo stesso file** in ingresso, o lasciare un record di log "a metà" (`IN_ELABORAZIONE`) se il processo muore a metà lavorazione.
- **Come:** prima di lavorare un item, (1) sposta/rinomina il file con un `FileMove` **idempotente** (`idempotencyKey` sul path/nome file) verso un'area "in lavorazione" — chi arriva secondo trova il file già spostato e salta l'item; (2) apri una riga di log con `STATO:"IN_ELABORAZIONE"` verificando `lastInsertRowCount === 1` (altrimenti `throw`: qualcun altro ha già aperto quella chiave di correlazione); (3) prima di aprire un nuovo giro, chiudi con un `SqlUpdate` gli eventuali "orfani" `IN_ELABORAZIONE` per lo stesso nome file ma con `CORRELATION_ID` diverso da quello corrente (run precedenti interrotte a metà).
- **Perché:** senza questi tre elementi insieme, un semplice `continueOnFail`/idempotencyKey sul solo step finale non basta: il rischio di doppia-lavorazione si annida nel **primo** step che tocca la risorsa condivisa (il file), non solo nell'ultimo (la creazione del documento).
- **Esempio:** `GAZZA:#9` (subStep di claim, dopo la lettura della provenienza): `FileMove` idempotente verso `processing`, chiusura orfani `IN_ELABORAZIONE`, apertura riga log con controllo `lastInsertRowCount === 1`.
- **Rif:** `GAZZA:#9`.

### A13 — Soglia "percentuale risolta" per accettare un risultato parziale

- **Quando:** un flusso elabora una collezione di sotto-elementi (es. righe di un ordine) di cui alcuni potrebbero non essere risolvibili (articolo non trovato) e vuoi decidere in automatico se il risultato è **comunque accettabile** (crea il documento con quello che si è risolto, segnalando i mancanti) oppure va bloccato per revisione umana.
- **Come:** in un `CodeJs`, calcola `resolvedPct = risolte / totaleRigheRilevanti * 100` **escludendo dal denominatore** le righe che non sono di business (es. righe NOTA/commento) — un errore comune è includerle e abbassare artificialmente la percentuale. Confronta con una soglia **configurabile** (chiave di configurazione tipo `minPercentualeRisoltePerCreare`, non hard-coded): se `resolvedPct >= soglia` prosegui creando il documento e segnala le righe mancanti come warning non bloccante; sotto soglia, tratta l'intero item come da rivedere manualmente (non crearlo).
- **Perché:** una soglia esplicita e configurabile rende il comportamento "quanto è abbastanza per procedere in automatico" un parametro di business (cambia da cliente a cliente), non una scelta implicita nel codice; l'esclusione delle righe non di business dal denominatore evita falsi negativi (un ordine con molte righe di nota risulterebbe erroneamente "poco risolto").
- **Esempio:** `GAZZA:#1` definisce `minPercentualeRisoltePerCreare:"60"` come configurazione; lo step che calcola l'esito finale la confronta con `resolvedPct` per decidere `CREATO` vs `CREATO_PARZIALE` vs "da rivedere", tenendo distinti i "motivi di riga" (non bloccanti) dai "motivi bloccanti d'ordine" — un bug pregresso mescolava le due categorie mandando in revisione anche ordini sopra soglia.
- **Rif:** `GAZZA:#1`; logica di calcolo/branch finale del flusso GAZZA (vedi `esempi.md` §6).

### A14 — Cascata di matching con AI vincolata al catalogo reale + auto-learning

- **Quando:** devi risolvere un'entità esterna incerta (es. un codice articolo cliente) contro l'anagrafica del gestionale, con più fonti di verità in ordine di affidabilità, e vuoi che l'AI **non inventi mai** un codice che non esiste.
- **Come:** costruisci una cascata di step, dal più economico/affidabile al più costoso, fermandoti al primo che trova un match univoco: (1) **memoria/auto-learning** — query su una tabella di corrispondenze già confermate in passato per lo stesso cliente/codice; (2) **match esatto** sul campo primario dell'anagrafica (`GestionaleSend` con `filtro` puntuale); (3) **match su codice secondario/alias** (es. tabella ponte tipo `ART_CODICI`); (4) **query SQL più ampia** (LIKE, storico ordini) che produce una lista di **candidati reali**; (5) **solo se ambiguo**, passa la lista di candidati (mai il catalogo intero, mai "indovina") a un `AiAnalysis`/`ExtractStructured` con un prompt che impone esplicitamente "scegli SOLO tra questi candidati, non inventare codici". Dopo un match riuscito con un metodo diverso dalla memoria, **scrivi/aggiorna** la tabella di auto-learning (nuova riga se assente, rinforzo/`EVIDENCE_COUNT+1` se coerente, stato `CONFLITTO` se in contrasto con una memoria già approvata — non sovrascrivere alla cieca).
- **Perché:** l'AI "vincolata ai candidati" elimina il rischio di codici allucinati (un'AI libera può restituire un codice plausibile ma inesistente); l'auto-learning rende i giri successivi progressivamente più veloci ed economici (meno chiamate AI) e costruisce un audit trail di come/quando ogni corrispondenza è stata stabilita.
- **Esempio:** `GAZZA:#9` (sotto-ForEach articoli): Memoria → Metodo A (match esatto) → Metodo B (SQL + AI vincolata sui soli candidati) → Metodo Offerta (join anti-doppia-evasione) → fallback prezzo da listino; dopo ogni riga risolta, upsert su `THINKAI_GAZZA_ARTICOLI_PROFILO` con `MATCH_METHOD`/`CONFIDENCE`/`EVIDENCE_COUNT`.
- **Rif:** `GAZZA:#9`; vedi `esempi.md` §6 e `../prompt-ordini/template-avanzato.md` per il caso applicato a ordini clienti.

---

## PARTE B — Anti-pattern (quirk reali)

Ognuno: **❌ Non fare / ✅ Fai invece / Perché / rif `Flusso:riga`**.

### B1 — Literal-stringa NON quotato in una condizione (Q1)

- **❌ Non fare:** `if ($.isOrdine == ordine)` (F4:27) — `ordine` è un bareword senza apici.
- **✅ Fai invece:** quota sempre il letterale: `if ($.isOrdine == "ordine")` (cfr. `"ok"` F2:214, `'OK'` F4:171).
- **Perché:** è l'unico literal-stringa non quotato dei 4 flussi (RHS di `==` altrove incoerente ma quotato). *(Inferenza L8)*: se il motore risolve `ordine` come identificatore → `undefined`, l'intero ramo ordine (F4:28-190) è **codice morto**; se coercizza a stringa funziona per caso. Incoerenza sintattica certa, effetto runtime non verificabile.
- **Rif:** F4:27.

### B2 — `throw new Error(...)` dentro un ramo del loop (Q6)

- **❌ Non fare:** nel ramo `else` dentro `for (const item of lastFileList)`, `throw new Error("Non sono riuscito a inserire il documento in target")` (F1:666, idem F3:440).
- **✅ Fai invece:** gestisci l'anomalia con un Branch/`SetFields` che imposta `esito: "anomalia"` e prosegue (come fa F2/F4, che usano Branch senza `throw`), lasciando che gli step email a valle notifichino l'errore.
- **Perché:** `throw` (proiezione di "Stop & Error", L2621) **interrompe l'intera run** *(inferenza L2621)*: rende irraggiungibili gli step email a valle e blocca l'elaborazione dei PDF successivi nel loop.
- **Rif:** F1:666, F3:440.

### B3 — `SendEmail` finale che scarta l'arricchimento e usa chiavi cancellate (Q7)

- **❌ Non fare:** `SendEmail({ bodyFormat: "html", to: [...], subject: "{lastGestionaleCodice}", body: "{lastTargetCrossJson}{lastAiOutput}" })` (F1:711, idem F3:485).
- **✅ Fai invece:** usa le chiavi arricchite già prodotte a monte — `subject: "{mailSubjectFinal}"`, `body: "{lastMarkdownHtml}"` — come fa correttamente F2:259.
- **Perché:** tre difetti sommati. (1) Ignora `mailSubjectFinal`/`mailBodyMarkdown` costruiti da `emailEnrichOutput` (F1:698-699) e l'HTML di `Markdown` `lastMarkdownHtml` (F1:708). (2) `bodyFormat: "html"` ma il body è Markdown grezzo non convertito. (3) `{lastTargetCrossJson}` è stato **cancellato** dallo StepData in `cleanupArticoli` (F1:490, `delete stepData['lastTargetCrossJson']`), quindi interpola vuoto.
- **Rif:** F1:711, F1:490, F1:698-708; corretto F2:259.

### B4 — `responseFormat: "report"` che alimenta un Branch

- **❌ Non fare:** `AiAnalysis({ responseFormat: "report", ... })` (F4:11) il cui output (via `isOrdine`) pilota `if ($.isOrdine == ordine)` (F4:27).
- **✅ Fai invece:** per output che alimenta Branch/Switch/CodeJs usa **sempre** `text` o `json` (vedi Pattern A1).
- **Perché:** viola esplicitamente L38 — `report` aggiunge branding/footer destinato a una persona e **rompe il confronto** del Branch. Qui il danno si somma a B1 (bareword `ordine`).
- **Rif:** F4:11→27; regola L38.

### B5 — Codice morto: lettura di `priceAlertsJson` mai prodotto nel flusso

- **❌ Non fare:** in `emailEnrichOutput` leggere `priceAlertsJson` e costruire un blocco "CONTROLLO PREZZI" (F1:687-695, idem F3:461) quando quella chiave non è mai scritta in F1/F3.
- **✅ Fai invece:** rimuovi il ramo, oppure produci davvero `priceAlertsJson` in uno step a monte dello stesso flusso.
- **Perché:** `priceAlertsJson` è prodotta **solo in F2:171**; in F1/F3 la lettura restituisce sempre vuoto → il blocco alert non si attiva mai (dead-read). È logica inerte che confonde chi legge.
- **Rif:** letto F1:687, F3:461; prodotto F2:171.

### B6 — Chiavi StepData NON a catalogo usate come output standard (Q3)

- **❌ Non fare:** fondare la logica su chiavi che il blocco produttore **non documenta**: `lastQueryJson` (F2:88,110,186 — `Query` non la elenca), `lastTargetCrossStatus` (F1:619), `lastTargetCrossResponseBody` (F1:626 — assenti dagli output di `GestionaleSend`).
- **✅ Fai invece:** usa le chiavi a catalogo del produttore — per `Query`: `lastQueryRows`/`lastQueryRowCount`/`lastQueryColumns` (L375-377); per `GestionaleSend`: `lastGestionaleCodice`/`lastTargetCrossJson`/`lastGestionaleEsito`/`lastGestionalePdf` (L997-1000). Se ti serve lo status HTTP grezzo, verifica in Studio quale chiave lo espone davvero.
- **Perché:** *(inferenza)* se il motore non emette quelle chiavi, la condizione che ci si fonda (es. `checkDoc` su `lastTargetCrossStatus === 200`, F1:620) è rotta e la verifica esito non funziona.
- **Rif:** F2:88, F1:619-620, F1:626; catalogo L375-377, L997-1000.

### B7 — Catena allegati con chiavi mai scritte / tipo sbagliato (Q4+Q5)

- **❌ Non fare (F4):** `SetFields` scrive `currentMailHasAttachments` con la **lista** allegati anziché un booleano (F4:10); il Branch legge `hasAttachments`, chiave **mai scritta** (F4:36); il ForEach itera `attachmentCheck.attachmentList` (F4:39) ma `attachmentCheck` ritorna un **booleano** (F4:30-33), non un oggetto con `attachmentList`; `MailRead` ha `downloadAttachments: false` (F4:3) ma il flusso usa `filePath` degli allegati (F4:43,53).
- **✅ Fai invece:** scrivi il booleano nella stessa chiave che il Branch legge; itera sulla lista effettivamente ritornata (`attachmentCheck` deve ritornare la lista, non `true`); imposta `downloadAttachments: true` se poi ti servono i `filePath`.
- **Perché:** ogni anello legge una chiave con nome o tipo diverso da quello scritto (dead-read): la catena allegati non parte *(inferenza)*.
- **Rif:** F4:3, F4:10, F4:30-33, F4:36, F4:39, F4:43.

### B8 — `{TBD:...}` non risolto usato come valore reale

- **❌ Non fare:** `SendEmail({ to: ["{TBD:email_responsabile_interno}"], ... })` (F4:188).
- **✅ Fai invece:** risolvi il segnaposto con un indirizzo reale (o una chiave StepData valida) prima di pubblicare il flusso.
- **Perché:** `{TBD:nome}` è un placeholder-da-compilare (valore mancante): come destinatario email genera un indirizzo invalido → invio fallito.
- **Rif:** F4:188.

### B9 — `switch` senza `break` trattato come JS reale

- **❌ Non fare:** copiare `switch ($.currentAttachment.ext) { case "pdf": { ... } case "docx": { ... } }` (F4:49-107) in codice JavaScript vero contando sul fallthrough.
- **✅ Fai invece:** nel DSL lascialo così com'è (è corretto): i `case` sono contenitori-ramo isolati (L2665) e il grafo instrada **un solo** caso; l'assenza di `break` è artefatto di proiezione, non fallthrough *(inferenza L8+L2665)*. Se invece porti quella logica in `CodeJs` (JS reale), aggiungi i `break`.
- **Perché:** in JS reale, senza `break` l'esecuzione **cade nei case successivi**; è la trappola copia-incolla DSL→JS. Dentro il DSL, al contrario, aggiungere `break` non serve.
- **Rif:** F4:49-107; regola L2665.
