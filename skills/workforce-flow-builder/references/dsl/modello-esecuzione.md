# Modello di esecuzione, dati ed errori — ThinkAI Workforce Studio

> **Scopo.** Documentare come un agente parte, come i dati fluiscono tra gli step, come si annidano i contenitori, come il motore controlla l'esecuzione (iterazione, attesa, human-in-the-loop, sync/async), come gestisce gli errori e come si comporta in debug/dry-run.
>
> **Fonti.** `manuale-clean.md` (guida sviluppatore, blocco HTML `L1436`; "Trigger e StepData iniziale" `L1451`) e l'inventario trasversale FASE 1. **Tracciabilità:** ogni affermazione cita il `L####` = riga del manuale HTML sorgente già presente nelle fonti. Ciò che il manuale non copre è marcato **⚠️ NON DOCUMENTATO**; i nomi DSL sono **tutti confermati** (15 dai flussi, gli altri dal video corso).
>
> **Nomi DSL.** I nomi-funzione DSL citati provengono esclusivamente da `references/nomi-blocchi.md` (autorità). I nomi dei parametri coincidono col manuale e sono riportati esatti, senza omissioni. I nomi dei trigger (`Manual`, `Schedule`, …) sono quelli usati dal manuale stesso (`L1451`).

---

## 1. Trigger e punti d'ingresso

Un agente parte **sempre** da un trigger. Il trigger non decide solo *quando* parte l'agente: in alcuni scenari prepara già le prime variabili che il flusso può leggere nel primo step (`L1451`). Alcuni trigger popolano lo StepData **prima** del primo step (`webhookBody`, `formData`, `lastEmail`/`inboundMailId` per MailPolling durevole, `lastFileList`, `lastEventRows`), così il primo nodo può partire subito da quelle chiavi (`L1436`; contratto MailPolling da corso M3, vedi §1.1).

### 1.1 Gli 8 trigger — tabella verbatim (`L1451`)

| Trigger | Quando parte | Chiavi StepData disponibili |
| --- | --- | --- |
| `Manual` | Avvio manuale da Studio, debug o API. | Nessuna chiave automatica. |
| `Schedule` | Pianificazione oraria o periodica. | Nessuna chiave automatica specifica. |
| `EventDb` | Nuove righe rilevate dalla query di sorveglianza. | `lastEventRows`, `lastQueryRows`, `lastQueryRowCount`, `lastQueryColumns` |
| `Webhook` | POST pubblico sul token dell'agente. | `webhookBody`, `webhookContentType` |
| `MailPolling` | Polling IMAP **durevole**: una run **per messaggio** (vedi ⚠️ nota corso sotto). | `inboundMailId`, `inboundMailKey`, `inboundEmlPath`, `lastEmail`, `lastEmailAttachments` |
| `FilePolling` | Nuovi file nella directory configurata. | `lastFileList`, `lastFileListCount` |
| `Form` | Invio della form pubblica ospitata dal Backend. | `formData`, `formSubmittedAt` |
| `ErrorTrigger` | Fallimento di un altro agente monitorato. | `failedAgentId`, `failedAgentName`, `failedExecutionId`, `failedAt`, `errorMessage` |

> ⚠️ **MailPolling — il corso (SSOT) ha priorità sul manuale.** Il manuale (`L1451`) descrive per `MailPolling` un contratto semplice (`lastEmails`/`lastEmailsSummary`, come una lettura batch). Il **video corso** (M3 «Trigger», M4, M15) documenta il **polling IMAP durevole** effettivo: acquisisce EML + allegati, registra la mail in un journal e crea **una sola run per messaggio**, esponendo `inboundMailId`, `inboundMailKey`, `inboundEmlPath`, `lastEmail` (singolare) e `lastEmailAttachments`. **NON creare un `ForEach` sulle mail** — usa un ciclo solo per gli allegati della singola email. Il worker deve terminare con **un unico `MailDisposition` top-level** (sposta/marca letta + chiude il journal `processed`/`review`). Le chiavi `lastEmails`/`lastEmailsSummary` restano invece l'output del **blocco `MailRead`** (lettura batch), non del trigger durevole.

Esempi rapidi (verbatim, `L1451`): *"`{formData.email}` in un prompt, `ForEach` su `lastEmails` o `lastFileList`, `InboundParse` su `webhookBody`."* — ⚠️ nel caso `lastEmails` la citazione del manuale vale per il **blocco** `MailRead` (batch), non per il trigger MailPolling durevole (vedi nota sopra).

**Note per trigger (dalla colonna "Quando parte", `L1451`):**
- `Manual` — tre modi d'avvio: da Studio, in debug, o via API. Nessuna chiave StepData automatica.
- `Schedule` — avvio pianificato (orario o periodico). Nessuna chiave automatica specifica.
- `EventDb` — scatta quando la "query di sorveglianza" rileva nuove righe; espone sia `lastEventRows` sia le chiavi standard di query (`lastQueryRows`, `lastQueryRowCount`, `lastQueryColumns`). È di fatto un controllo di flusso inter-dato: parte al comparire di nuove righe.
- `Webhook` — attivato da un POST pubblico sul token dell'agente; popola `webhookBody` (payload) e `webhookContentType`. È la base per Inbound Parse (`L2471`) e per la risposta via Webhook Respond (`L2707`).
- `MailPolling` — polling IMAP **durevole** (corso M3/M4/M15): credenziale IMAP cifrata, cartella sorgente, prima sincronizzazione, limite per messaggio ed eventuale agente *worker*; il *claim* SQL impedisce doppie elaborazioni quando più sorgenti alimentano lo stesso worker. Crea **una run per messaggio** ed espone `inboundMailId`, `inboundMailKey`, `inboundEmlPath`, `lastEmail`, `lastEmailAttachments` (EML e allegati finiscono in `WorkforceFiles` del Backend). Non iterare le mail con `ForEach`; chiudi con un unico `MailDisposition` top-level. Il manuale (`L1451`) riporta invece il contratto semplice `lastEmails`/`lastEmailsSummary`: il corso ha priorità.
- `FilePolling` — scatta su nuovi file nella directory configurata; espone `lastFileList` e `lastFileListCount`.
- `Form` — invio della form pubblica ospitata dal Backend; espone `formData` (navigabile, es. `{formData.email}`) e `formSubmittedAt`.
- `ErrorTrigger` — meccanismo di controllo di flusso **inter-agente**: parte quando un altro agente monitorato fallisce, popolando i metadati del fallimento (`failedAgentId`, `failedAgentName`, `failedExecutionId`, `failedAt`, `errorMessage`). Vedi §5.6.

> ⚠️ **Il trigger NON è serializzato nel DSL** (`⚠️ NON DOCUMENTATO`). Il codice "Modalità Sviluppatore" inizia dal primo step: né il tipo di trigger né la sua configurazione (cron di `Schedule`, campi della `Form`, token del `Webhook`, query di sorveglianza di `EventDb`, config MailRead di `MailPolling`, directory di `FilePolling`) compaiono nel file DSL. Anche **come importare/incollare il DSL in Studio** non è documentato. Trigger e import si impostano nell'interfaccia di Studio; nel DSL puoi solo **assumere** che le chiavi iniziali del trigger (tabella §1.1) siano già presenti in StepData e partire da quelle.

### 1.2 Punti d'ingresso HTTP legati a blocchi (non trigger d'avvio)

Oltre agli 8 trigger, quattro blocchi aprono/gestiscono un ingresso HTTP a run già avviata: **non** avviano l'agente.

| Punto d'ingresso | Nome DSL | Ruolo | Avvia la run? | Ref |
| --- | --- | --- | --- | --- |
| Inbound Parse | `InboundParse` | Estrae mittente/testo/canale dal `webhookBody` del trigger Webhook (Telegram/Twilio/Slack) → chiavi `inbound*`. | No (consuma il payload) | `L2471` |
| Wait `mode=untilWebhook` | `Wait` | Mette la run in pausa e apre un URL pubblico di resume (`lastWaitResumeUrl`); un POST esterno la riprende. | No, riprende una run in pausa | `L2667` |
| Webhook Respond | `WebhookRespond` | Chiude in modo sincrono la richiesta HTTP che ha avviato l'agente (status/body/header scelti). | No | `L2707` |
| Invia e attendi | `SendAndWait` | Invia un messaggio col link di risposta e mette la run in pausa fino alla scelta del destinatario. | No, riprende una run in pausa | `L3021` |

Dettaglio di Wait e Invia e attendi in §4; di Webhook Respond in §4.5.

### 1.3 ⚠️ NON DOCUMENTATO (trigger)
- La configurazione dei trigger stessi non compare nella sezione "Trigger e StepData iniziale": pianificazione cron di `Schedule`, configurazione MailRead di `MailPolling`, directory di `FilePolling`, schema della form di `Form`, token dell'endpoint di `Webhook`, e come si associa l'agente monitorato di `ErrorTrigger`. Sono citati solo nella colonna "Quando parte".

---

## 2. StepData — il contesto dati condiviso

### 2.1 Concetto (`L1436`)
StepData è il **contesto dati condiviso** di un'esecuzione. Verbatim (`L1436`): *"StepData — ogni step legge/scrive dati con chiavi standard (es. `lastQueryRows`, `lastAiOutput`); gli step successivi le usano. I dati nascono dal trigger iniziale o dagli output degli step, **non da variabili globali**."*

Regole conseguenti:
- **Nessuna variabile globale.** Tutto transita per StepData, alimentato da trigger (§1) + output degli step.
- **Provenienza dei dati:** o dal trigger iniziale (§1.1), o dalla tabella "Output (variabili prodotte)" di ogni blocco che gira. Chi scrive una chiave e chi la legge si "collegano" solo tramite **il nome della chiave** (vedi §3).
- **Naming prevalente:** gli step di lettura/elaborazione producono chiavi `last*` fisse (es. `lastQueryRows`, `lastAiOutput`, `lastPdfText`).

### 2.2 Placeholder vs espressioni (`L1436`)
Verbatim (`L1436`): *"Placeholder vs espressioni — `{chiave}` interpola testo (prompt/body/subject); `$.chiave` è un'espressione runtime per condizioni Branch/Switch (`\"$.lastQueryRowCount > 0\"`). `$` da solo = item corrente in Filter/ForEach."*

| Sintassi | Uso | Chi la valuta |
| --- | --- | --- |
| `{chiave}` / `{oggetto.proprieta}` / `{array[N].proprieta}` | Interpola testo nei campi (prompt/body/subject/content/message/url/where/values…). | Il motore, sostituzione testuale (`L1436`) |
| `$.chiave` | Espressione runtime per condizioni Branch/Switch/Filter, mapping Sub-Workflow, `value` di Set Fields. | Il motore del flusso / DSL (`L1436`) |
| `$` (da solo) | Item corrente dentro Filter/ForEach. | Il motore del flusso (`L1436`) |

⚠️ Natura DSL (`L1436`): *"La vista a codice è un DSL, non codice eseguito — `if/for/switch` e le espressioni tra virgolette le valuta il motore del flusso. L'unico codice realmente eseguito è dentro `CodeJs.code` / `CodePython.code`."* Quindi i costrutti di controllo e le espressioni `$.chiave` sono **valutati dal motore**, non compilati come linguaggio generale.

### 2.3 Chiavi a nome dinamico: convenzione `{target}` / `{outputKey}` / `{assignments}`
Diversi blocchi non scrivono su un nome fisso ma su una chiave **decisa da un parametro**. Il manuale la indica nella tabella output come `{nomeParametro} — dal campo nomeParametro`.

- **`{target}`** (parametro "Chiave output") — i blocchi di trasformazione collezioni: Aggregate, Filter, Limit, Merge, Remove Duplicates, Rename Keys, Sort scrivono il risultato sulla chiave indicata in `target`.
- **`{outputKey}`** (parametro "Chiave output") — JSON da file (+ `lastJsonRead`), JSON Parse, Code JS (`CodeJs`), Code Python scrivono il risultato sulla chiave indicata in `outputKey`; Code JS/Python producono anche `{outputItemsKey}` (default `lastItems`). Markdown usa `outputKey` opzionale (altrimenti default per direzione).
- **`{assignments}`** (Set Fields) — scrive tante chiavi quante sono le `key` dell'array `assignments`; il `value` supporta il mini-linguaggio `{$.path|func}` (es. `{$.lastQueryRows[*].importo|sum}`).

### 2.4 Prefisso `__` (chiavi di sistema)
Il prefisso `__` è riservato a chiavi di sistema/interne: `__webhookResponseStatusCode`/`__webhookResponseBody`/`__webhookResponseContentType`/`__webhookResponseHeaders` (Webhook Respond, `L2726`), `__sheet` (Xlsx Extract con `sheet='*'`), `__loopItem` (item corrente ForEach in forma placeholder). ⚠️ `__loopItem` compare solo negli esempi (es. `sourceName` di Indicizza conoscenza, `L1649`); non è formalizzato in una tabella output (vedi §3.3).

### 2.5 ⚠️ NON DOCUMENTATO (dati)
- Semantica formale delle variabili built-in citate solo negli esempi: `{now}` (`L2105`), `{timestamp}` (`L1901`), `{agentName}` (`L1685`, `L1901`, Email). Quale blocco/motore le produca e il loro formato non sono dichiarati.
- Placeholder citati negli esempi ma senza blocco produttore documentato: `{slackText}`, `{slackUser}` (Inbound Parse produce `inboundText`/`inboundConvKey`, non `slackText`/`slackUser`).
- Grammatica completa degli operatori delle espressioni: attestati solo `>` (`$.lastQueryRowCount > 0`, `L1436`) e `endsWith` (`$ endsWith '.pdf'`, Filter). Ogni altro operatore (`<`, `>=`, `==`, `!=`, `startsWith`, `contains`, AND/OR/NOT…) non è documentato.

---

## 3. Connessioni e contenitori — modello ad albero annidato

### 3.1 Non è un grafo di wire tra porte
Il manuale **non** descrive collegamenti espliciti (wire) tra porte di uscita e ingresso dei nodi. Il modello documentato è: **step in sequenza che scrivono/leggono StepData**, con **contenitori annidati** per il controllo di flusso (`L1436`). Il termine "grafo" compare una sola volta, come argomento su cui la chat agentica sa rispondere (`L1436`), non come modello a wire/porte.

⚠️ NON DOCUMENTATO: un modello a grafo con porte/archi collegabili. Anche l'ordinamento lineare preciso degli step non è enunciato esplicitamente: è implicito nel linguaggio *"gli step successivi le usano"* (`L1436`) e *"eseguendo i sub-step"* (ForEach, `L2446`). Vedi §4.1.

### 3.2 I dati passano via StepData, non via connessioni
Il canale di passaggio dati è lo StepData (§2), non collegamenti punto-a-punto. Ogni step produce chiavi di output che alimentano gli step a valle; il "collegamento" reale è **il nome della chiave** condiviso tra scrittore e lettore (`L1436`).

### 3.3 I quattro (e soli quattro) blocchi con contenitori
Nel manuale **esattamente quattro** blocchi dichiarano una sezione "Contenitori" con slot annidati. Gli altri step sono foglie non annidanti.

| Blocco | Nome DSL / proiezione | Slot (etichetta → chiave interna) | Ref blocco / contenitori |
| --- | --- | --- | --- |
| Branch (IF) | `if (<$.cond>) { … } else { … }` | Vero → `then` ; Falso → `else` | `L2417` / `L2424` |
| ForEach | `for (const item of <chiave>) { … }` (+ `// @foreach maxIterations=N`) | Per ogni item → `body` | `L2446` / `L2469` |
| Switch | `switch (<$.expr>) { case … default … }` | Casi → `cases` ; Default → `default` | `L2658` / `L2665` |
| Sub-Workflow | `SubWorkflow` | Sotto-flusso → `body` | `L2633` / `L2656` |

**Branch (IF)** (`L2417`) — "Biforcazione condizionale: ramo Vero / ramo Falso". Parametro `condition` — espressione, **Sì**, es. `$.lastQueryRowCount > 0` (`L2418`). Slot `then` (Vero) / `else` (Falso) (`L2424`).

**Switch** (`L2658`) — "Smistamento su N casi + default". Parametro `value` — espressione, **Sì**, es. `$.docType` (`L2659`). Slot `cases` (N rami) / `default` (`L2665`).

**ForEach** (`L2446`) — vedi §4.2 per parametri e semantica.

**Sub-Workflow** (`L2633`) — "Esegue un sotto-flusso/agente annidato". È l'**unico** blocco che passa dati con mapping esplicito padre↔figlio; tutti gli altri contenitori condividono lo StepData ambientale.

Parametri (`L2634`):

| Parametro | Tipo | Obbl. | Default | Comportamento (verbatim) |
| --- | --- | --- | --- | --- |
| `agentId` — Agente da eseguire | intero | Sì | — | ID dell'agente (sotto-flusso) da eseguire (es. `42`). |
| `inputMapping` — Mapping input | JSON | — | — | Cosa passare al sotto-flusso: `{ "chiaveSub": "$.chiavePadre" }`. **Default (vuoto): passa tutto lo StepData.** |
| `outputMapping` — Mapping output | JSON | — | — | Cosa re-importare nel padre al termine: `{ "chiavePadre": "$.chiaveSub" }`. **Default (vuoto): non importa nulla. Applicato solo se il sotto-flusso completa.** |

Output nel padre (`L2648`): `lastSubWorkflowExecutionId` (intero), `lastSubWorkflowStatus` (testo), `lastSubWorkflowOutputSummary` (testo). Slot `body` (`L2656`).

### 3.4 Blocchi di controllo flusso SENZA contenitori
Questi influenzano il flusso ma non hanno slot annidati: passano dati solo via StepData.

| Blocco | Nome DSL | Meccanismo (non contenitore) | Ref |
| --- | --- | --- | --- |
| Filter | `Filter` | Filtra la collezione `source` in `target` via `condition` (usa `$` come item corrente). | `L2426` |
| Stop & Error | `throw new Error("<messaggio>")` | Interrompe la run con errore esplicito (`message`, `severity`). | `L2621` |
| Wait | `Wait` | Attesa/pausa; con `untilWebhook` pausa+resume via `lastWaitResumeUrl`. | `L2667` |
| Invia e attendi | `SendAndWait` | Invia link e mette in pausa fino alla scelta del destinatario. | `L3021` |
| Webhook Respond | `WebhookRespond` | Risponde alla chiamata webhook che ha avviato l'agente. | `L2707` |

Anche `onError` / `continueOnFail` (`L1436`) sono controllo di flusso ma **non** sono documentati come contenitori con slot (§5).

---

## 4. Controllo dell'esecuzione

### 4.1 Ordine sequenziale
Il manuale non ha una sezione dedicata all'ordinamento: lo definisce tramite la semantica StepData. Uno step legge le chiavi prodotte da quelli precedenti — *"gli step successivi le usano"* (`L1436`) — da cui discende l'esecuzione sequenziale. I trigger che pre-popolano StepData permettono al primo nodo di partire subito da quelle chiavi (`L1436`, dettaglio `L1451`).

⚠️ NON DOCUMENTATO: una formulazione esplicita "il motore esegue dall'alto verso il basso" oltre a quanto implicito nella semantica StepData; l'ordine di valutazione tra rami paralleli non-ForEach.

### 4.2 ForEach — iterazione, parallelismo, batch, scope
"Cicla sugli item di una collezione eseguendo i sub-step." (`L2446`). Contenitore: "Per ogni item `body`" (`L2469`).

Parametri (verbatim, `L2447`):

| Campo | Tipo | Obbl. | Default | Descrizione / esempio |
| --- | --- | --- | --- | --- |
| `itemsKey` — Chiave collezione | testo | Sì | — | es. `lastFileList` |
| `maxIterations` — Iterazioni max | intero | — | 1000 | — |
| `batchSize` — Dimensione blocco | intero | — | 0 | 0 = nessun blocco. >0: processa a blocchi di N item; la Pausa si applica tra un blocco e l'altro (rate-limit verso API esterne). |
| `maxConcurrency` — Iterazioni parallele | intero | — | 1 | 1 = sequenziale (default storico). >1 (max 8): iterazioni in parallelo con scope per-iterazione; a fine blocco i risultati sono uniti in ordine di indice (l'ultima iterazione vince, come nel sequenziale). Le iterazioni dello stesso blocco non vedono le scritture l'una dell'altra. |
| `delayBetweenMs` — Pausa (ms) | intero | — | 0 | Pausa tra iterazioni (sequenziale senza blocchi) o tra blocchi. Utile per rispettare i rate-limit di API/AI. |

Semantica di esecuzione (`L2447`):
- **Sequenziale vs parallelo:** `maxConcurrency = 1` → sequenziale (default storico); `> 1` (massimo **8**) → iterazioni in parallelo.
- **Scope per-iterazione:** in parallelo ogni iterazione ha uno scope proprio e *"le iterazioni dello stesso blocco non vedono le scritture l'una dell'altra"*.
- **Merge per indice:** *"a fine blocco i risultati sono uniti in ordine di indice (l'ultima iterazione vince, come nel sequenziale)"*.
- **Batch:** `batchSize > 0` processa a blocchi di N item; con `batchSize = 0` (nessun blocco) `delayBetweenMs` è tra iterazioni.
- **Guardia:** `maxIterations` default 1000.

Item corrente dentro il body: `$` (`L1436`) o il placeholder `{__loopItem}` (`L1649`).

⚠️ NON DOCUMENTATO: comportamento del merge oltre alla regola "l'ultima iterazione vince per indice"; ordine di scheduling interno delle iterazioni parallele; interazione precisa tra `maxConcurrency > 1` e `batchSize` (descritti separatamente, senza esempio combinato).

### 4.3 Wait — attesa, pausa e resume
"Attende per un intervallo, fino a un orario, oppure (untilWebhook) mette la run in pausa finché non arriva una callback esterna sull'URL di resume." (`L2667`).

Parametri (verbatim, `L2668`):

| Campo | Tipo | Obbl. | Default | Descrizione / esempio |
| --- | --- | --- | --- | --- |
| `mode` — Modalità | scelta — delay · untilTime · untilWebhook | Sì | — | — |
| `delaySeconds` — Secondi attesa | intero | — | 60 | Se mode=delay. |
| `seconds` — Secondi attesa (legacy) | intero | — | — | Alias legacy di delaySeconds. Mantenuto per round-trip di agenti esistenti; nei nuovi flussi usa delaySeconds. |
| `untilTime` — Fino alle (HH:mm) | testo | — | — | Se mode=untilTime. — es. `18:00` |
| `timeoutMinutes` — Timeout pausa (min) | intero | — | 10080 | Se mode=untilWebhook: scadenza dell'attesa (default 7 giorni, max 30). La run si mette in pausa e riprende al POST sull'URL di resume (lastWaitResumeUrl). |
| `onTimeout` — Alla scadenza | scelta — fail · resumeDefault | — | fail | Se mode=untilWebhook: fail = run fallita; resumeDefault = riprende con resumePayload.timedOut=true (decidi col Branch). |

Output (verbatim, `L2694`):

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastWaitResumeUrl` | testo | URL pubblico di resume (solo mode=untilWebhook, scritto prima della pausa). |
| `lastWaitKey` | testo | WaitKey monouso della pausa (solo mode=untilWebhook). |
| `resumePayload` | JSON | Risposta ricevuta al resume (navigabile: {resumePayload.campo}). |
| `resumeChoice` | testo | Scelta dei bottoni della pagina di resume (es. Approva/Rifiuta). |
| `resumedAt` | testo | Timestamp ISO della ripresa. |

I tre modi (`L2668`): `delay` (attesa a tempo), `untilTime` (fino a un orario HH:mm), `untilWebhook` (**pausa + resume**: run sospesa che riparte al POST sull'URL di resume). Default `timeoutMinutes = 10080` = 7 giorni, massimo 30 giorni. Gestione scadenza `onTimeout` in §5.4.

### 4.4 "Invia e attendi" — human-in-the-loop
"Invia un messaggio col link di risposta (email/Slack/Teams/Telegram/WhatsApp) e mette la run in pausa finché il destinatario non sceglie dalla pagina (es. Approva/Rifiuta). Al resume: resumeChoice/resumePayload per il Branch a valle." (`L3021`). È il pattern human-in-the-loop: pausa in attesa di una decisione umana, poi ripresa.

Parametri (verbatim, `L3022` — tabella completa, nessun parametro omesso):

| Campo | Tipo | Obbl. | Default | Descrizione / esempio |
| --- | --- | --- | --- | --- |
| `channel` — Canale | scelta — email · slack · teams · telegram · whatsapp | Sì | — | — |
| `message` — Messaggio | testo lungo | Sì | — | Supporta {placeholder}. Il link di risposta viene aggiunto in coda automaticamente. — es. `Confermi l'ordine {lastQueryRows[0].numero}?` |
| `choices` — Scelte (CSV) | testo | — | Approva, Rifiuta | Bottoni della pagina di risposta (max 6). La scelta arriva in resumeChoice → Branch su $.resumeChoice. |
| `allowNote` — Campo nota | sì/no | — | true | Mostra un campo nota libero nella pagina (arriva in resumePayload.note). |
| `timeoutMinutes` — Timeout attesa (min) | intero | — | 10080 | Scadenza dell'attesa (default 7 giorni, max 30). |
| `onTimeout` — Alla scadenza | scelta — fail · continueWithDefault | — | fail | fail = run fallita; continueWithDefault = riprende con resumePayload.timedOut=true (decidi col Branch). |
| `responseKey` — Chiave risposta | testo | — | resumePayload | — |
| `formFields` — Campi form (mid-flow) | JSON | — | — | Opzionale: la pagina di risposta raccoglie questi campi in resumePayload (type: text/textarea/number/email/date/select). I required bloccano il submit. — es. `[{"name":"budget","label":"Budget approvato","type":"number","required":true},{"name":"priorita","label":"Priorità","type":"select","options":["Alta","Bassa"]}]` |
| `to` — Destinatari | testo | — | — | Email: indirizzi CSV. WhatsApp: numero (whatsapp:+39...). — es. `capo@azienda.it` |
| `subject` — Oggetto (email) | testo | — | — | Vuoto = "Richiesta di conferma - <nome agente>". |
| `smtpConfigId` — Configurazione SMTP (email) | testo | — | — | Vuoto = SMTP predefinito. |
| `webhookCredentialName` — Credenziale webhook (slack/teams) | credenziale | — | — | — |
| `botCredentialName` — Credenziale bot (telegram) | credenziale | — | — | — |
| `chatId` — Chat ID (telegram) | testo | — | — | — es. `-100123456 o @canale` |
| `credentialName` — Credenziale Twilio (whatsapp) | credenziale | — | — | — |
| `from` — Da (whatsapp) | testo | — | — | — es. `whatsapp:+14155238886` |

Output (verbatim, `L3088`):

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastWaitResumeUrl` | testo | URL pubblico di risposta (incluso nel messaggio inviato). |
| `lastWaitKey` | testo | WaitKey monouso della pausa. |
| `resumeChoice` | testo | Scelta del destinatario (uno dei choices) — Branch su $.resumeChoice. |
| `resumePayload` | JSON | Risposta completa (note/campi; {timedOut:true} se scaduto con continueWithDefault). |
| `resumedAt` | testo | Timestamp ISO della ripresa. |

**Wait `untilWebhook` vs Invia e attendi (documentato):** condividono la meccanica di pausa/resume (`lastWaitResumeUrl` / `lastWaitKey` / `resumePayload` / `resumeChoice` / `resumedAt`). Differenze: "Invia e attendi" **spedisce attivamente** il messaggio col link e raccoglie scelta/nota/form dal destinatario umano; il valore di timeout che riprende è `continueWithDefault` (`L3022`), mentre in Wait è `resumeDefault` (`L2668`).

### 4.5 Webhook Respond — uscita sincrona del trigger Webhook
"Risponde alla chiamata webhook che ha avviato l'agente." (`L2707`). Chiude la richiesta HTTP con status/body/header scelti.

Parametri (verbatim, `L2708`): `statusCode` (intero, default 200), `headers` (lista chiave/valore), `bodyFromKey` (testo, default `lastAiOutput`), `contentType` (testo, default `application/json`). Output (`L2726`): `__webhookResponseStatusCode`, `__webhookResponseBody`, `__webhookResponseContentType`, `__webhookResponseHeaders`.

### 4.6 Sync vs async
Il manuale **non usa** le etichette "sincrono/asincrono" (⚠️ NON DOCUMENTATO come terminologia). Il comportamento si ricava dalle descrizioni:
- **Sincrono (in-run):** gli step normali girano dentro una singola esecuzione, con StepData che passa da uno all'altro (`L1436`). Sub-Workflow è bloccante rispetto al padre: re-importa gli output "solo se il sotto-flusso completa" (`L2633`).
- **Asincrono (pausa/resume):** gli unici punti documentati in cui "la run si mette in pausa" sono **Wait `untilWebhook`** (`L2667`) e **Invia e attendi** (`L3021`); la ripresa avviene via POST sull'URL di resume con `lastWaitKey` monouso.
- **Parallelismo intra-step:** solo `ForEach` con `maxConcurrency > 1` (max 8) (`L2447`).
- **Timeout della singola chiamata (natura bloccante):** AI Analysis `timeoutSeconds` (`L1482`), HTTP Call `timeoutSeconds` default 30 (`L2738`), Code JS `timeoutMs` default 5000 (`L3258`), Code Python `timeoutMs` default 30000 (`L3296`), TargetCross `timeoutSeconds` default 60 max 300 (`L2808`).

⚠️ NON DOCUMENTATO: se durante la pausa il worker sia liberato dalla coda; persistenza/ripresa dopo riavvio del motore; limiti di run in pausa concorrenti.

---

## 5. Gestione errori e interruzione

### 5.1 Panoramica (`L1436`)
La guida dichiara due meccanismi d'errore a livello di step. Verbatim (`L1436`): *"Errori — `onError` (try/catch) esegue step di recupero; `continueOnFail` salta e prosegue."*

### 5.2 `onError` (try/catch)
Proiezione DSL del concetto: `try { … } catch { … }` (nomi-blocchi.md, evidenza F2:4). Il manuale afferma solo che `onError` implementa una logica try/catch che esegue uno "step di recupero" (`L1436`).

⚠️ NON DOCUMENTATO: non esiste un blocco/componente dedicato `onError` con tabella parametri. Dove si imposta, come si definisce lo "step di recupero" e quali chiavi StepData espone **non** sono documentati.

### 5.3 `continueOnFail` (salta e prosegue)
Concetto generale "salta e prosegue" (`L1436`). Come **parametro concreto** compare esclusivamente nel blocco **Code JS** (`CodeJs`) in modalità RunForEach (`L3258`):

| Campo | Tipo | Obbl. | Default | Descrizione |
| --- | --- | --- | --- | --- |
| `continueOnFail` — Continua su errore (RunForEach) | sì/no | — | false | (nessuna nota aggiuntiva) |

⚠️ `continueOnFail` **non** è documentato in Code Python (`L3296`) né in ForEach (`L2447`): non assumere che esista lì.

### 5.4 Stop & Error (interruzione esplicita)
Blocco Stop & Error, proiezione DSL `throw new Error("<messaggio>")` (nomi-blocchi.md, F1:666). "Interrompe l'esecuzione con un errore esplicito." (`L2621`).

Parametri (verbatim, `L2622`):

| Campo | Tipo | Obbl. | Default | Descrizione / esempio |
| --- | --- | --- | --- | --- |
| `message` — Messaggio | testo | Sì | — | Messaggio d'errore che interrompe il flusso. Supporta {placeholder}. — es. `Nessun dato trovato` |
| `severity` — Gravità | scelta — warning · error | — | error | (nessuna nota aggiuntiva) |

Il blocco **non** dichiara alcuna tabella "Output" (assente dopo `L2622`).

### 5.5 Timeout sulle attese (Wait / Invia e attendi)
Entrambi i blocchi di pausa espongono `timeoutMinutes` (default 10080 = 7 giorni, max 30) e `onTimeout`, ma con etichette di valore **diverse**:

| Blocco | `onTimeout` valori | Comportamento alla scadenza | Ref |
| --- | --- | --- | --- |
| Wait (`untilWebhook`) | `fail` · `resumeDefault` | `fail` = run fallita; `resumeDefault` = riprende con `resumePayload.timedOut=true` (decidi col Branch). | `L2668` |
| Invia e attendi | `fail` · `continueWithDefault` | `fail` = run fallita; `continueWithDefault` = riprende con `resumePayload.timedOut=true` (decidi col Branch). | `L3022` |

⚠️ Attenzione: sono **due parametri distinti in due componenti diversi** — il valore di ripresa è `resumeDefault` in Wait (`L2668`) e `continueWithDefault` in Invia e attendi (`L3022`).

### 5.6 ErrorTrigger (trigger su fallimento altrui)
`ErrorTrigger` avvia l'agente quando un altro agente monitorato fallisce, popolando lo StepData con `failedAgentId`, `failedAgentName`, `failedExecutionId`, `failedAt`, `errorMessage` (`L1451`). È il meccanismo documentato per reagire ai fallimenti a livello inter-agente. ⚠️ NON DOCUMENTATO: come si associa/configura l'agente monitorato e gli eventuali filtri sul tipo di errore.

### 5.7 Parametri per-step di robustezza
**HTTP Call — parametri rilevanti per gli errori (sottoinsieme del blocco, `L2738`):**

| Campo | Tipo | Obbl. | Default | Descrizione / esempio |
| --- | --- | --- | --- | --- |
| `expectedStatus` — Status attesi | JSON | — | — | — es. `[200,201]` |
| `timeoutSeconds` — Timeout (s) | intero | — | 30 | (nessuna nota) |
| `allowUnauthorizedCerts` — Ignora errori SSL | sì/no | — | false | Accetta certificati TLS non validi/self-signed. Usare solo per servizi on-prem fidati. |
| `followRedirects` — Segui redirect | sì/no | — | true | Se disattivo non segue i redirect HTTP 3xx. |
| `neverError` — Non fallire su errore | sì/no | — | false | Se attivo lo step non fallisce su status non-2xx: registra solo status/body (utile con Branch a valle). |

**Altri flag "errore se…":** Delete File `failIfMissing` (sì/no, default false, `L1756`); JSON da file `failOnInvalid` (sì/no, default true, `L1929`); JSON Parse `failOnInvalid` (sì/no, default true, `L1951`).

**Sub-Workflow:** il re-import degli output è condizionato al completamento — `outputMapping` "Applicato solo se il sotto-flusso completa" (`L2634`); `lastSubWorkflowStatus` (`L2648`) permette di rilevare esiti/fallimenti del sotto-flusso.

### 5.8 Retry / Fallback
⚠️ **NON DOCUMENTATO.** Nel manuale non esiste alcun meccanismo di **retry** (ritentativi automatici) né di **fallback** d'errore: nessun numero di tentativi, backoff o delay tra retry, nessun ramo di fallback per step falliti. Le uniche occorrenze di "fallback" sono estranee alla gestione errori: "fallback legacy" della Chat (`L1727`) e "fallback OCR" / `fallbackToOcrUnderChars` di PDF Extract (`L2255`).

### 5.9 Riepilogo meccanismi

| Meccanismo | Dove | Stato | Ref |
| --- | --- | --- | --- |
| `onError` (try/catch + step di recupero) | concetto generale (nessun blocco dedicato) | Solo concettuale; dettagli ⚠️ NON DOCUMENTATO | `L1436` |
| `continueOnFail` (salta e prosegue) | concetto + param Code JS RunForEach | Documentato (param solo in Code JS) | `L1436`, `L3258` |
| Stop & Error (`message`, `severity`) | blocco Flusso | Documentato | `L2621` / `L2622` |
| Wait `onTimeout` (fail / resumeDefault) | blocco Flusso | Documentato | `L2668` |
| Invia e attendi `onTimeout` (fail / continueWithDefault) | blocco Notifiche | Documentato | `L3022` |
| ErrorTrigger | trigger | Documentato (config ⚠️ NON DOCUMENTATO) | `L1451` |
| HTTP `neverError` / `expectedStatus` | blocco Integrazioni | Documentato | `L2738` |
| `failIfMissing` / `failOnInvalid` | Delete File, JSON da file, JSON Parse | Documentato | `L1756`, `L1929`, `L1951` |
| Timeout per-step (AI, Code, ERP, HTTP) | vari blocchi | Documentato | `L1482`, `L1580`, `L1616`, `L2738`, `L2808`, `L3258`, `L3296` |
| Retry / Fallback d'errore | — | ⚠️ NON DOCUMENTATO | — |

---

## 6. Debug / dry-run

Verbatim (`L1436`): *"Debug — il dry-run non invia nulla (email/file/telegram). ⚠️ `AiAnalysis`/`ExtractStructured` girano davvero e consumano token: usa \"Non chiamare AI/API esterne\" per simularli."*

- **Cosa NON viene inviato in dry-run:** le azioni con effetti esterni citate esplicitamente — **email, file, telegram** — non vengono eseguite (`L1436`).
- **Cosa gira davvero (e consuma token):** **AI Analysis** (`AiAnalysis`, `L1481`) e **Estrai dati (AI)** (`ExtractStructured`, `L1615`) girano realmente anche in dry-run; per simularle attiva l'opzione **"Non chiamare AI/API esterne"** (`L1436`).
- **Supporto al debug:** AI Analysis `timeoutSeconds` è "Utile per non far attendere a lungo il debug/dry-run su prompt o allegati pesanti" (`L1482`).
- **Chiarimento dal video corso (M6 «Debug nel grafo»):** il **"Debug sicuro" è ATTIVO per default** e simula le azioni esterne — **AI, HTTP, email, file, notifiche e subprocess Python** — mentre il JavaScript locale continua a trasformare lo StepData per rendere utile l'anteprima. In pratica il default del corso corrisponde all'opzione "Non chiamare AI/API esterne" attiva (quindi AI/Extract NON consumano token). Disattiva i mock solo per un collaudo consapevole (può generare costi o modificare sistemi esterni). Prima esecuzione sempre con Debug sicuro attivo.

⚠️ Il manuale (`L1436`) cita esplicitamente solo email/file/telegram come "non inviati" e dichiara AI/Extract come eseguiti per default; il **video corso** estende la lista simulata (AI, HTTP, email, file, notifiche, Python) col Debug sicuro attivo. Per DB/Sheets/Excel/Drive/SharePoint non assumere il comportamento senza verificarlo in Studio.

---

## Appendice — nomi DSL dei costrutti/blocchi citati

> Fonte: `references/nomi-blocchi.md` (autorità). ✅ (Fx) = confermato in un flusso esportato; ✅ (corso Mn) = confermato dal video corso (palette modulo n). Tutti i nomi sono ora confermati.

| Elemento (display) | Nome / proiezione DSL | Stato |
| --- | --- | --- |
| Branch (IF) | `if (<$.cond>) { … } else { … }` | ✅ (F1:612) |
| Switch | `switch (<$.expr>) { case … default … }` | ✅ (F4:49) |
| ForEach | `for (const item of <chiave>) { … }` + `// @foreach maxIterations=N` | ✅ (F1:9, F4:6) |
| Stop & Error | `throw new Error("<messaggio>")` | ✅ (F1:666) |
| onError (concetto) | `try { … } catch { … }` | ✅ (F2:4) |
| Code JS | `CodeJs` | ✅ (F1:13) |
| Filter | `Filter` | ✅ CONFERMATO (corso M13) |
| Wait | `Wait` | ✅ CONFERMATO (corso M13) |
| Sub-Workflow | `SubWorkflow` | ✅ CONFERMATO (corso M13) |
| Webhook Respond | `WebhookRespond` | ✅ CONFERMATO (corso M13) |
| Inbound Parse | `InboundParse` | ✅ CONFERMATO (corso M13) |
| Code Python | `CodePython` | ✅ CONFERMATO (corso M9) |
| Invia e attendi | `SendAndWait` | ✅ CONFERMATO (corso M16) |
| Mail Disposition | `MailDisposition` | ✅ CONFERMATO (corso M15) |

I nomi dei trigger (`Manual`, `Schedule`, `EventDb`, `Webhook`, `MailPolling`, `FilePolling`, `Form`, `ErrorTrigger`) sono quelli usati dal manuale stesso nella tabella "Trigger e StepData iniziale" (`L1451`).
