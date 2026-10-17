# Catalogo blocchi — Flusso

> Categoria "Flusso" (16 blocchi). Fonte manuale: `Manuale — ThinkAI WorkForce Studio.html` (rif. `L####` = riga nell'HTML sorgente). Nomi DSL: `references/nomi-blocchi.md` (unica autorità). Esempi flussi: `Flusso:riga`.
>
> **Legenda affidabilità nome DSL:** tutti i nomi sono ✅ CONFERMATI — `(F…)` dai flussi esportati, `(corso M13)` dal video corso (palette del modulo 13). Per i costrutti di controllo (Branch, ForEach, Switch, Stop & Error) il DSL è una **proiezione JS**, non un nome-funzione (tipi-blocco: `Branch`/`ForEach`/`Switch`/`StopAndError`).

## Indice
1. [Aggregate](#aggregate--dsl-aggregate--confermato-corso-m13--l2393)
2. [Branch (IF)](#branch-if--costrutto-di-controllo--proiezione-js-ifelse--confermato-f1612--l2417)
3. [Filter](#filter--dsl-filter--confermato-corso-m13--l2426)
4. [ForEach](#foreach--costrutto-di-controllo--proiezione-js-forof--confermato-f19-f46--l2446)
5. [Inbound Parse](#inbound-parse--dsl-inboundparse--confermato-corso-m13--l2471)
6. [Limit](#limit--dsl-limit--confermato-corso-m13--l2497)
7. [Merge](#merge--dsl-merge--confermato-corso-m13--l2521)
8. [Remove Duplicates](#remove-duplicates--dsl-removeduplicates--confermato-corso-m13--l2545)
9. [Rename Keys](#rename-keys--dsl-renamekeys--confermato-corso-m13--l2565)
10. [Set Fields](#set-fields--dsl-setfields--confermato-f1664--l2585)
11. [Sort](#sort--dsl-sort--confermato-corso-m13--l2597)
12. [Stop & Error](#stop--error--costrutto-di-controllo--proiezione-js-throw-new-error--confermato-f1666--l2621)
13. [Sub-Workflow](#sub-workflow--dsl-subworkflow--confermato-corso-m13--l2633)
14. [Switch](#switch--costrutto-di-controllo--proiezione-js-switchcase--confermato-f449--l2658)
15. [Wait](#wait--dsl-wait--confermato-corso-m13--l2667)
16. [Webhook Respond](#webhook-respond--dsl-webhookrespond--confermato-corso-m13--l2707)

---

### Aggregate — DSL `Aggregate` ✅ CONFERMATO (corso M13)  `L2393`

- **Scopo:** Aggrega/raggruppa item (somma, conteggio, ecc.).
- **Quando usarlo:** Quando serve ridurre una collezione dello StepData (es. `lastQueryRows`) a un singolo valore aggregato: conteggio, somma, media, min, max, concatenazione di stringhe, primo o ultimo item. Il risultato viene scritto nella chiave StepData indicata in `target`.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `source` | testo | Sì | — | es. `lastQueryRows`. |
| `operation` | scelta — count · sum · avg · min · max · concat · first · last | Sì | — |  |
| `target` | testo | Sì | — | Chiave StepData dove scrivere il risultato aggregato. — es. `totale` |
| `separator` | testo | — | — | Separatore (per `concat`). |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `{target}` | JSON | Dal campo `target` — Risultato aggregazione. |

- **Riferimenti incrociati:** `lastQueryRows`.

---

### Branch (IF) — costrutto di controllo · proiezione JS `if/else` ✅ CONFERMATO (F1:612)  `L2417`

- **Scopo:** Biforcazione condizionale: ramo Vero / ramo Falso.
- **Quando usarlo:** Quando il flusso deve prendere due strade in base a una condizione runtime (espressione con `$.chiave`, es. `$.lastQueryRowCount > 0`). Gli step del ramo Vero vanno nel contenitore `then`, quelli del ramo Falso nel contenitore `else`. Nota generale del manuale: se un output AI alimenta il Branch usare `responseFormat` `text`/`json` (il formato `report` aggiunge un footer e rompe il confronto).
- **Nome DSL:** costrutto di controllo, non funzione. Proiezione JS confermata: `if (<$.cond>) { … } else { … }` (evidenza F1:612).
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `condition` | espressione | Sì | — | es. `$.lastQueryRowCount > 0` |

- **Output (variabili StepData prodotte):** nessuno.
- **Contenitori:** `then` — ramo Vero · `else` — ramo Falso.
- **⚠️ Avvertenze / vincoli:**
  - ⚠️ Il confronto usa l'espressione `$.chiave` valutata dal motore del flusso (non codice eseguito). Un output AI in formato `report` (con footer/branding) rompe il confronto del Branch: usare `text` o `json`.
- **Riferimenti incrociati:** `lastQueryRowCount`.

---

### Filter — DSL `Filter` ✅ CONFERMATO (corso M13)  `L2426`

- **Scopo:** Filtra gli item in base a una condizione.
- **Quando usarlo:** Quando serve tenere solo gli item di una collezione StepData che soddisfano una condizione, valutata per item (`$` = item corrente, es. `$ endsWith '.pdf'`). Gli elementi che superano il filtro finiscono nella chiave `target`.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `source` | testo | Sì | — | Chiave StepData della collezione da filtrare. — es. `lastQueryRows` |
| `condition` | espressione | Sì | — | es. `$ endsWith '.pdf'` |
| `target` | testo | Sì | — | Chiave StepData con gli elementi che superano il filtro. — es. `righeFiltrate` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `{target}` | JSON | Dal campo `target` — Collezione filtrata. |

- **Riferimenti incrociati:** `lastQueryRows`.

---

### ForEach — costrutto di controllo · proiezione JS `for…of` ✅ CONFERMATO (F1:9, F4:6)  `L2446`

- **Scopo:** Cicla sugli item di una collezione eseguendo i sub-step.
- **Quando usarlo:** Quando bisogna eseguire una sequenza di step (contenitore `body`) per ogni item di una collezione (es. `lastFileList`, `lastEmails`). Supporta blocchi (`batchSize`) con pausa tra blocchi per rispettare rate-limit e parallelismo (`maxConcurrency`).
- **Nome DSL:** costrutto di controllo, non funzione. Proiezione JS confermata: `for (const item of <chiave>) { … }` (+ direttiva `// @foreach maxIterations=N`) — evidenza F1:9, F4:6.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `itemsKey` | testo | Sì | — | es. `lastFileList` |
| `maxIterations` | intero | — | 1000 |  |
| `batchSize` | intero | — | 0 | 0 = nessun blocco. >0: processa a blocchi di N item; la Pausa si applica tra un blocco e l'altro (rate-limit verso API esterne). |
| `maxConcurrency` | intero | — | 1 | 1 = sequenziale (default storico). >1 (max 8): iterazioni in parallelo con scope per-iterazione; a fine blocco i risultati sono uniti in ordine di indice (l'ultima iterazione vince, come nel sequenziale). Le iterazioni dello stesso blocco non vedono le scritture l'una dell'altra. |
| `delayBetweenMs` | intero | — | 0 | Pausa tra iterazioni (sequenziale senza blocchi) o tra blocchi. Utile per rispettare i rate-limit di API/AI. |
| `continueOnItemError` | sì/no | — | false | ✅ CONFERMATO (flusso CLI-A v1.4.1, esportato). Se un item lancia un errore, il ForEach non interrompe l'intera run: passa all'item successivo. Distinto da `// @continueOnFail` sul singolo step interno — questo agisce a livello dell'intero ciclo. |
| `failOnItemErrors` | sì/no | — | false | ✅ CONFERMATO (CLI-A). Se `true`, al termine del ciclo lo step ForEach stesso viene marcato fallito qualora almeno un item sia andato in errore (utile per far scattare notifiche/monitoraggio a livello di run, pur avendo lasciato proseguire gli altri item con `continueOnItemError`). |
| `failedItemsKey` | testo | — | — | ✅ CONFERMATO (CLI-A). Chiave StepData in cui viene accumulato l'elenco degli item falliti (per un riepilogo finale o un secondo giro di retry). Es. `failedOrders`. |
| `itemErrorSteps` | contenitore di step | — | — | ✅ CONFERMATO (CLI-A). Sequenza di step di **recovery per-item**, eseguita quando l'item corrente fallisce (in alternativa/aggiunta a `continueOnItemError`). Ha accesso allo StepData dell'iterazione fallita, incluso `stepData.__lastItemErrorMessage` col messaggio d'errore. Tipico contenuto: log tecnico dell'errore (CodeJs), scrittura/aggiornamento di una riga di audit (SqlInsert/SqlUpdate, tipicamente idempotenti), notifica (SendEmail), spostamento del file "incriminato" in una cartella di errore (FileMove). Vedi `pattern.md` §recovery ForEach per il pattern completo. |

- **Output (variabili StepData prodotte):** nessuno.
- **Contenitori:** `body` — Per ogni item. `itemErrorSteps` — Per l'item che fallisce (recovery), se configurato.
- **⚠️ Avvertenze / vincoli:**
  - ⚠️ `maxConcurrency` > 1 ha un massimo di 8 iterazioni parallele.
  - ⚠️ Con iterazioni parallele, le iterazioni dello stesso blocco non vedono le scritture l'una dell'altra; a fine blocco i risultati sono uniti in ordine di indice e l'ultima iterazione vince.
  - ⚠️ `itemErrorSteps`/`continueOnItemError`/`failOnItemErrors`/`failedItemsKey` sono **confermati da un flusso reale esportato** (CLI-A Ordine Cliente v1.4.1) ma non hanno ancora una scheda palette dedicata nel manuale component-per-component: usa questi nomi esattamente, e verifica in Studio l'etichetta esatta del pannello "Gestione errori" del blocco ForEach prima di affidarti a dettagli ulteriori non elencati qui.
- **Riferimenti incrociati:** `lastFileList`; `pattern.md` (recovery per-item vs `throw` che interrompe l'intera run — vedi anti-pattern B2).

---

### Inbound Parse — DSL `InboundParse` ✅ CONFERMATO (corso M13)  `L2471`

- **Scopo:** Estrae mittente/testo/canale dal payload del trigger Webhook (Telegram o Twilio WhatsApp) e li mette in StepData.
- **Quando usarlo:** Come primo step di un agente avviato dal trigger Webhook usato per ricevere messaggi da Telegram, Twilio WhatsApp o Slack: normalizza il payload (`webhookBody`) in chiavi StepData (`inboundText`, `inboundFrom`, `inboundChatId`, ecc.) pronte per rispondere o per isolare la conversazione.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `channel` | scelta — auto · telegram · twilio · slack | — | auto | auto = rileva dal payload. slack = eventi Slack (app_mention / message.im). |
| `sourceKey` | testo | — | webhookBody | Chiave StepData col body del trigger Webhook. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `inboundText` | testo | Testo del messaggio in arrivo (per Slack: senza la @menzione). |
| `inboundFrom` | testo | Mittente (chatId Telegram / numero WhatsApp / userId Slack). |
| `inboundChatId` | testo | Chat/canale per rispondere. |
| `inboundChannel` | testo | Canale rilevato (telegram \| twilio \| slack). |
| `inboundThreadTs` | testo | Slack: thread_ts per rispondere in-thread (solo @menzione). |
| `inboundConvKey` | testo | Slack: chiave conversazione per l'isolamento (thread per @menzione, canale DM per im). |

- **Riferimenti incrociati:** `webhookBody`; Webhook (trigger).

---

### Limit — DSL `Limit` ✅ CONFERMATO (corso M13)  `L2497`

- **Scopo:** Limita una collezione ai primi (o ultimi) N item.
- **Quando usarlo:** Quando serve tenere solo i primi o gli ultimi N item di una collezione StepData (es. top 10). Combinato con Sort per prendere i "migliori" N (`keep=last` dopo un ordinamento crescente, o `keep=first` dopo un decrescente).
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `source` | testo | Sì | — | Chiave StepData della collezione da limitare. — es. `lastQueryRows` |
| `count` | intero | Sì | — | Quanti item tenere (> 0). — es. `10` |
| `keep` | scelta — first · last | — | first | first = i primi N, last = gli ultimi N (utile dopo un Sort). |
| `target` | testo | Sì | — | Chiave StepData con la collezione limitata. — es. `topRows` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `{target}` | JSON | Dal campo `target` — Collezione limitata ai primi/ultimi N item. |

- **⚠️ Avvertenze / vincoli:**
  - ⚠️ `count` deve essere > 0.
- **Riferimenti incrociati:** `lastQueryRows`; Sort.

---

### Merge — DSL `Merge` ✅ CONFERMATO (corso M13)  `L2521`

- **Scopo:** Unisce più insiemi di dati.
- **Quando usarlo:** Quando serve combinare più collezioni StepData (elencate in `sources`) in una sola, con la modalità scelta: append (accoda), byKey (per campo chiave), byPosition (per posizione), union (unione), intersect (intersezione). Per `byKey` specificare `keyField`.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `mode` | scelta — append · byKey · byPosition · union · intersect | Sì | — |  |
| `sources` | JSON | Sì | — | es. `["a","b"]` |
| `target` | testo | Sì | — | Chiave StepData dove scrivere la collezione unita. — es. `uniti` |
| `keyField` | testo | — | — | Campo chiave (per `byKey`). |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `{target}` | JSON | Dal campo `target` — Dati uniti. |

---

### Remove Duplicates — DSL `RemoveDuplicates` ✅ CONFERMATO (corso M13)  `L2545`

- **Scopo:** Rimuove gli item duplicati da una collezione (per campi chiave o per intero item); tiene la prima occorrenza.
- **Quando usarlo:** Quando una collezione StepData contiene duplicati da eliminare, identificandoli per uno o più campi chiave (`keys`) oppure confrontando l'intero item (`keys` vuoto). Viene mantenuta la prima occorrenza.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `source` | testo | Sì | — | Chiave StepData della collezione da deduplicare. — es. `lastQueryRows` |
| `keys` | testo | — | — | Campi (separati da virgola) che identificano un duplicato. Vuoto = confronta l'intero item. — es. `codice, anno` |
| `target` | testo | Sì | — | Chiave StepData con la collezione senza duplicati (resta la prima occorrenza). — es. `uniqueRows` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `{target}` | JSON | Dal campo `target` — Collezione senza duplicati. |

- **⚠️ Avvertenze / vincoli:**
  - ⚠️ Tiene la prima occorrenza di ogni duplicato.
- **Riferimenti incrociati:** `lastQueryRows`.

---

### Rename Keys — DSL `RenameKeys` ✅ CONFERMATO (corso M13)  `L2565`

- **Scopo:** Rinomina le chiavi degli oggetti di una collezione secondo una mappa vecchio→nuovo (es. nomi colonna SQL → nomi parlanti).
- **Quando usarlo:** Quando gli oggetti di una collezione (es. righe SQL con nomi colonna tecnici) devono avere chiavi rinominate in nomi parlanti tramite una mappa `{vecchia:nuova}`. Le chiavi non presenti nella mappa restano invariate e gli item non-oggetto passano invariati.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `source` | testo | Sì | — | Chiave StepData della collezione di oggetti. — es. `lastQueryRows` |
| `mappings` | JSON | Sì | — | Oggetto `{"vecchiaChiave":"nuovaChiave"}` (match esatto, case-sensitive). Le chiavi non in mappa restano invariate; gli item non-oggetto passano invariati. — es. `{"RAG_SOC":"ragioneSociale","P_IVA":"partitaIva"}` |
| `target` | testo | Sì | — | Chiave StepData con la collezione rinominata. — es. `renamedRows` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `{target}` | JSON | Dal campo `target` — Collezione con chiavi rinominate. |

- **⚠️ Avvertenze / vincoli:**
  - ⚠️ Il match delle chiavi è esatto e case-sensitive.
  - ⚠️ Le chiavi non presenti nella mappa restano invariate; gli item non-oggetto passano invariati.
- **Riferimenti incrociati:** `lastQueryRows`.

---

### Set Fields — DSL `SetFields` ✅ CONFERMATO (F1:664)  `L2585`

- **Scopo:** Imposta/trasforma campi nei dati di esecuzione.
- **Quando usarlo:** Quando serve creare o trasformare chiavi dello StepData con un array di assegnazioni `{key,value}`, dove `value` supporta placeholder con path ed eventuale funzione (`{$.path|func}`, es. somma di un campo su tutte le righe).
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `assignments` | JSON | Sì | — | Array di assegnazioni `{ key, value }`. Il value supporta placeholder `{$.path\|func}`. — es. `[{"key":"totale","value":"{$.lastQueryRows[*].importo\|sum}"}]` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `{assignments}` | JSON | Dal campo `assignments` — Chiavi assegnate (dalle `key` delle assignment). |

- **Riferimenti incrociati:** `lastQueryRows`.

---

### Sort — DSL `Sort` ✅ CONFERMATO (corso M13)  `L2597`

- **Scopo:** Ordina una collezione per un campo (o per gli item stessi), crescente o decrescente.
- **Quando usarlo:** Quando serve ordinare una collezione StepData per un campo degli oggetti (`field`) oppure per gli item stessi (`field` vuoto, per liste di stringhe/numeri). Spesso combinato con Limit per prendere i primi/ultimi N.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `source` | testo | Sì | — | Chiave StepData della collezione da ordinare. — es. `lastQueryRows` |
| `field` | testo | — | — | Campo degli oggetti su cui ordinare. Vuoto = ordina gli item stessi (liste di stringhe/numeri). — es. `importo` |
| `order` | scelta — asc · desc | — | asc | asc = crescente, desc = decrescente. Numerico se i valori sono numeri, poi date, altrimenti alfabetico (case-insensitive). |
| `target` | testo | Sì | — | Chiave StepData dove scrivere la collezione ordinata. — es. `sortedRows` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `{target}` | JSON | Dal campo `target` — Collezione ordinata. |

- **Riferimenti incrociati:** `lastQueryRows`; Limit.

---

### Stop & Error — costrutto di controllo · proiezione JS `throw new Error()` ✅ CONFERMATO (F1:666)  `L2621`

- **Scopo:** Interrompe l'esecuzione con un errore esplicito.
- **Quando usarlo:** Quando il flusso deve fermarsi deliberatamente con un errore (es. dopo un Branch che rileva una condizione non valida come "nessun dato trovato"), con messaggio personalizzabile via placeholder e gravità warning o error.
- **Nome DSL:** costrutto di controllo, non funzione. Proiezione JS confermata: `throw new Error("<messaggio>")` (evidenza F1:666).
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `message` | testo | Sì | — | Messaggio d'errore che interrompe il flusso. Supporta `{placeholder}`. — es. `Nessun dato trovato` |
| `severity` | scelta — warning · error | — | error |  |

- **Output (variabili StepData prodotte):** nessuno.
- **⚠️ Avvertenze / vincoli:**
  - ⚠️ Interrompe l'esecuzione del flusso con un errore esplicito.
- **Riferimenti incrociati:** Branch (IF) (tipico predecessore che rileva la condizione di stop).

---

### Sub-Workflow — DSL `SubWorkflow` ✅ CONFERMATO (corso M13)  `L2633`

- **Scopo:** Esegue un sotto-flusso/agente annidato.
- **Quando usarlo:** Quando serve richiamare un altro agente/flusso come sotto-processo (per riuso/modularità), controllando cosa passargli (`inputMapping`) e cosa re-importare al termine (`outputMapping`). Gli step del sotto-flusso stanno nel contenitore `body`.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `agentId` | intero | Sì | — | ID dell'agente (sotto-flusso) da eseguire. — es. `42` |
| `inputMapping` | JSON | — | — | Cosa passare al sotto-flusso: `{ "chiaveSub": "$.chiavePadre" }`. Default (vuoto): passa tutto lo StepData. |
| `outputMapping` | JSON | — | — | Cosa re-importare nel padre al termine: `{ "chiavePadre": "$.chiaveSub" }`. Default (vuoto): non importa nulla. Applicato solo se il sotto-flusso completa. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastSubWorkflowExecutionId` | intero | ID execution del sotto-flusso. |
| `lastSubWorkflowStatus` | testo | Stato. |
| `lastSubWorkflowOutputSummary` | testo | Riepilogo output. |

- **Contenitori:** `body` — Sotto-flusso.
- **⚠️ Avvertenze / vincoli:**
  - ⚠️ `outputMapping` applicato solo se il sotto-flusso completa.
  - ⚠️ `inputMapping` vuoto passa tutto lo StepData; `outputMapping` vuoto non re-importa nulla.
- **Riferimenti incrociati:** StepData.

---

### Switch — costrutto di controllo · proiezione JS `switch/case` ✅ CONFERMATO (F4:49)  `L2658`

- **Scopo:** Smistamento su N casi + default.
- **Quando usarlo:** Quando il flusso deve ramificarsi su più valori (più di due) valutando un'espressione (`$.chiave`, es. `$.docType`): ogni caso ha il suo contenitore in `cases` e c'è un ramo `default` per i valori non gestiti. Adatto a valori prodotti da classificazione/estrazione AI (usare output `text`/`json`, non `report`).
- **Nome DSL:** costrutto di controllo, non funzione. Proiezione JS confermata: `switch (<$.expr>) { case "x": { … } default: { … } }` (evidenza F4:49).
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `value` | espressione | Sì | — | es. `$.docType` |

- **Output (variabili StepData prodotte):** nessuno.
- **Contenitori:** `cases` — Casi · `default` — Default.
- **⚠️ Avvertenze / vincoli:**
  - ⚠️ Il valore è un'espressione `$.chiave` valutata dal motore del flusso; un output AI in formato `report` con footer può rompere il confronto (usare `text`/`json`).
- **Riferimenti incrociati:** Classifica testo (AI); Estrai dati (AI) (sorgenti tipiche del valore da smistare).

---

### Wait — DSL `Wait` ✅ CONFERMATO (corso M13)  `L2667`

- **Scopo:** Attende per un intervallo, fino a un orario, oppure (`untilWebhook`) mette la run in pausa finché non arriva una callback esterna sull'URL di resume.
- **Quando usarlo:** Quando il flusso deve attendere: un intervallo fisso (`mode=delay`), un orario (`mode=untilTime`, HH:mm), o una callback esterna (`mode=untilWebhook`) che mette la run in pausa fino a un POST sull'URL di resume — utile per approvazioni umane / human-in-the-loop, con esito gestibile a valle tramite Branch su `resumePayload`/`resumeChoice`.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `mode` | scelta — delay · untilTime · untilWebhook | Sì | — |  |
| `delaySeconds` | intero | — | 60 | Se `mode=delay`. |
| `seconds` | intero | — | — | Alias legacy di `delaySeconds`. Mantenuto per round-trip di agenti esistenti; nei nuovi flussi usa `delaySeconds`. |
| `untilTime` | testo | — | — | Se `mode=untilTime`. — es. `18:00` |
| `timeoutMinutes` | intero | — | 10080 | Se `mode=untilWebhook`: scadenza dell'attesa (default 7 giorni, max 30). La run si mette in pausa e riprende al POST sull'URL di resume (`lastWaitResumeUrl`). |
| `onTimeout` | scelta — fail · resumeDefault | — | fail | Se `mode=untilWebhook`: fail = run fallita; resumeDefault = riprende con `resumePayload.timedOut=true` (decidi col Branch). |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastWaitResumeUrl` | testo | URL pubblico di resume (solo `mode=untilWebhook`, scritto prima della pausa). |
| `lastWaitKey` | testo | WaitKey monouso della pausa (solo `mode=untilWebhook`). |
| `resumePayload` | JSON | Risposta ricevuta al resume (navigabile: `{resumePayload.campo}`). |
| `resumeChoice` | testo | Scelta dei bottoni della pagina di resume (es. Approva/Rifiuta). |
| `resumedAt` | testo | Timestamp ISO della ripresa. |

- **⚠️ Avvertenze / vincoli:**
  - ⚠️ `mode=untilWebhook`: `timeoutMinutes` default 7 giorni, max 30 (giorni).
  - ⚠️ `mode=untilWebhook`: la WaitKey è monouso; alla scadenza `onTimeout=fail` fa fallire la run, `resumeDefault` riprende con `resumePayload.timedOut=true`.
- **Riferimenti incrociati:** Branch.

---

### Webhook Respond — DSL `WebhookRespond` ✅ CONFERMATO (corso M13)  `L2707`

- **Scopo:** Risponde alla chiamata webhook che ha avviato l'agente.
- **Quando usarlo:** Quando un agente avviato dal trigger Webhook deve restituire una risposta HTTP sincrona al chiamante, con status code, header, body (da una chiave StepData, default `lastAiOutput`) e content-type personalizzabili.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `statusCode` | intero | — | 200 |  |
| `headers` | lista chiave/valore | — | — |  |
| `bodyFromKey` | testo | — | lastAiOutput |  |
| `contentType` | testo | — | application/json |  |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `__webhookResponseStatusCode` | intero | Status code della risposta webhook. |
| `__webhookResponseBody` | testo | Body della risposta webhook. |
| `__webhookResponseContentType` | testo | Content-Type della risposta. |
| `__webhookResponseHeaders` | JSON | Header della risposta. |

- **Riferimenti incrociati:** `lastAiOutput`.
