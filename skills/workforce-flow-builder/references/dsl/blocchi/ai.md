# Catalogo blocchi — AI

> Categoria "AI" del manuale ThinkAI Workforce Studio. Ogni scheda cita il rif `L####` (riga HTML del manuale) e i nomi DSL provengono da `references/nomi-blocchi.md` (autorità). I nomi dei parametri coincidono col manuale.

## Indice
1. [AI Analysis — `AiAnalysis` `L1481`](#ai-analysis--dsl-aianalysis-l1481)
2. [Cerca nella conoscenza (RAG) — `RagSearch` `L1551`](#cerca-nella-conoscenza-rag--dsl-ragsearch-l1551)
3. [Classifica testo (AI) — `ClassifyText` `L1579`](#classifica-testo-ai--dsl-classifytext-l1579)
4. [Estrai dati (AI) — `ExtractStructured` `L1615`](#estrai-dati-ai--dsl-extractstructured-l1615)
5. [Indicizza conoscenza (RAG) — `RagEmbed` `L1649`](#indicizza-conoscenza-rag--dsl-ragembed-l1649)
6. [Report PDF/DOCX/XLSX — `GenerateReport` `L1685`](#report-pdfdocxxlsx--dsl-generatereport-l1685)

---

### AI Analysis  — DSL `AiAnalysis`  `L1481`

*(nome DSL ✅ CONFERMATO, evidenza F1:47)*

- **Scopo:** L'AI analizza i dati e produce testo/report. Può usare tool (DB, HTTP, web search, MCP) e memoria.
- **Quando usarlo:** Quando serve far analizzare dati dall'AI e produrre testo o un report. Se il risultato è destinato a una persona usa `responseFormat` `report` (con branding/stile/footer); se invece l'output alimenta un Branch/Switch/CodeJs (es. una categoria o un booleano) usa SEMPRE `text` o `json` perché `report` aggiunge un footer e rompe il confronto del Branch. Può usare tool (`sqlQuery`, `httpRequest`, `mcp__server__tool`), web search, memoria conversazionale opt-in e allegati (anche multipli via `attachFilePathsKey`). Il contesto RAG `{lastRagContext}` prodotto da "Cerca nella conoscenza (RAG)" è pronto per essere inserito nel prompt.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `prompt` | testo lungo | Sì | — | Istruzione per l'AI. |
| `responseFormat` | scelta — report · text · json | — | report | report = output destinato a una persona (con branding/stile/footer). text/json = estrazione/classificazione M2M (NIENTE branding/footer); json fa anche strip+parse del risultato in `lastAiJson`. ⚠️ Se l'output alimenta un Branch/Switch/CodeJs (es. una categoria o un booleano) usa SEMPRE text o json: 'report' aggiunge un footer e rompe il confronto del Branch. |
| `provider` | scelta — claude · openai · ollama · vllm | — | — | Lascia vuoto per ereditare dalla chat dell'agente (poi Claude di default). |
| `model` | modello AI | — | — | Modello del provider. Vuoto = modello della chat / default. Per Ollama/vLLM scrivi il nome del modello del tuo deployment. — es. claude-sonnet-4-6 |
| `maxRowsToAi` | intero | — | 500 | Righe dati all'AI. |
| `tools` | JSON | — | — | Array di nomi tool (`sqlQuery`, `httpRequest`, `mcp__server__tool`). — es. `["sqlQuery"]` |
| `maxToolTurns` | intero | — | 5 | Iterazioni tool max. |
| `timeoutSeconds` | intero | — | 0 | Limite massimo per la singola chiamata AI. 0 o vuoto = nessun limite di step (vale il timeout client 20min). Utile per non far attendere a lungo il debug/dry-run su prompt o allegati pesanti. |
| `enableWebSearch` | sì/no | — | false | Web search. |
| `memoryScope` | scelta — agent · chat | — | — | Memoria conversazionale opt-in. |
| `memoryWindowTurns` | intero | — | — | Finestra memoria (turni). 0 = memoria disattiva. |
| `memoryScopeKey` | testo | — | — | Suffisso dinamico per isolare la memoria per utente/conversazione, es. `{inboundChatId}` (Telegram) o `{slackUser}` (Slack). Vuoto = memoria condivisa nello scope. |
| `promptPrefix` | testo lungo | — | — | Override del prefisso globale. |
| `attachFilePath` | testo | — | — | Allegato per l'AI. |
| `attachFilePathsKey` | testo | — | — | Nome di una chiave StepData che contiene una LISTA di path (es. `imagePaths`): l'AI riceve tutti gli allegati in una sola chiamata e sceglie quello giusto (utile per più immagini: scarta logo/firma). Alimentala da uno step CodeJs con `JSON.stringify(paths)`. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastAiOutput` | testo | Testo prodotto dall'AI. |
| `lastAiToolCalls` | JSON | Chiamate tool eseguite (audit). |
| `lastAiJson` | JSON | Prodotto SOLO con `responseFormat=json` (strip+parse del risultato). Non elencato tra gli output base del manuale ma citato nelle note. |

- **⚠️ Avvertenze / vincoli:**
  - ⚠️ (`responseFormat`) Se l'output alimenta un Branch/Switch/CodeJs (es. una categoria o un booleano) usa SEMPRE text o json: 'report' aggiunge un footer e rompe il confronto del Branch.
  - ⚠️ (Debug, guida `L1436`) AiAnalysis/ExtractStructured girano davvero e consumano token anche in debug/dry-run: usa "Non chiamare AI/API esterne" per simularli.
- **Riferimenti incrociati:** `lastAiJson` (da `responseFormat=json`); `lastRagContext` / `{lastRagContext}` (da "Cerca nella conoscenza (RAG)"); tool `sqlQuery`, `httpRequest`, `mcp__server__tool`; Branch; Switch; CodeJs (per alimentare `attachFilePathsKey` con `JSON.stringify(paths)`); `{inboundChatId}` (Telegram); `{slackUser}` (Slack); `imagePaths` (esempio chiave lista path).

---

### Cerca nella conoscenza (RAG)  — DSL `RagSearch` ✅ CONFERMATO (corso M10)  `L1551`

*(nome DSL ✅ CONFERMATO dal video corso — palette del modulo 10 «Le palette in dettaglio — AI» (`node-RagSearch`/`campi-RagSearch`).)*

- **Scopo:** Recupera dalla base di conoscenza i passaggi più pertinenti a una domanda (ricerca semantica). `lastRagContext` è pronto da inserire nel prompt di AI Analysis.
- **Quando usarlo:** Quando serve recuperare dalla base di conoscenza i passaggi più pertinenti a una domanda tramite ricerca semantica (trova i passaggi pertinenti anche senza parole identiche). Da usare a valle di "Indicizza conoscenza (RAG)" (stessa raccolta usata in fase di indicizzazione). L'output `lastRagContext` è pronto per essere inserito come `{lastRagContext}` nel prompt di AI Analysis.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `query` | testo lungo | Sì | — | La domanda da cercare nella base di conoscenza (placeholder `{chiave}` risolti, es. `{lastMailBody}`). Ricerca semantica: trova i passaggi pertinenti anche senza parole identiche. — es. `{lastMailBody}` |
| `collection` | testo | — | default | La raccolta in cui cercare (stessa usata in fase di indicizzazione). |
| `topK` | intero | — | 5 | Quanti chunk pertinenti recuperare (1-50). |
| `minScore` | numero | — | 0 | 0..1: scarta i chunk sotto questa similarità (0 = nessuna soglia). |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastRagHits` | JSON | Chunk pertinenti `{ text, source, chunkIndex, score }`. |
| `lastRagContext` | testo | Contesto testuale pronto per il prompt (`{lastRagContext}` in AI Analysis). |
| `lastRagHitCount` | intero | Numero di chunk trovati. |

- **Riferimenti incrociati:** AI Analysis (destinazione di `{lastRagContext}`); Indicizza conoscenza (RAG) (stessa raccolta usata in fase di indicizzazione); `{lastMailBody}` (esempio query).

---

### Classifica testo (AI)  — DSL `ClassifyText` ✅ CONFERMATO (corso M10)  `L1579`

*(nome DSL ✅ CONFERMATO dal video corso — palette del modulo 10 «Le palette in dettaglio — AI».)*

- **Scopo:** L'AI classifica un testo in UNA tra le etichette indicate (con confidenza e motivazione). Copre anche sentiment (es. positivo/negativo/neutro). Output pronto per Switch/Branch.
- **Quando usarlo:** Quando serve classificare un testo (es. il corpo di un'email) in UNA sola tra un elenco di etichette (minimo 2), ottenendo anche confidenza e motivazione. Copre anche l'analisi del sentiment (es. positivo/negativo/neutro). L'output `lastClassifyLabel` è normalizzato sull'elenco ed è pronto per pilotare uno Switch/Branch.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `input` | testo lungo | Sì | — | Testo (o placeholder `{chiave}`) da classificare, es. il corpo di un'email. — es. `{lastMailBody}` |
| `labels` | testo | Sì | — | Etichette ammesse separate da virgola (minimo 2). L'AI ne sceglie UNA. Per il sentiment usa es. 'positivo, negativo, neutro'. — es. `ordine, reclamo, richiesta info` |
| `provider` | scelta — claude · openai · ollama · vllm | — | — | Vuoto = eredita dalla chat dell'agente (o Claude). |
| `model` | modello AI | — | — | Vuoto = modello di default del provider. |
| `timeoutSeconds` | intero | — | 0 | 0 = nessun limite per-step. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastClassifyLabel` | testo | Etichetta scelta (normalizzata sull'elenco). |
| `lastClassifyConfidence` | testo | Confidenza 0..1 dichiarata dall'AI. |
| `lastClassifyReason` | testo | Breve motivazione. |
| `lastClassifyJson` | JSON | Risposta JSON completa (label/confidence/reason). |
| `lastClassifyWarning` | testo | Avviso (es. etichetta fuori elenco). |

- **⚠️ Avvertenze / vincoli:**
  - Vincolo: `labels` richiede minimo 2 etichette separate da virgola; l'AI ne sceglie UNA.
  - `lastClassifyWarning` segnala i casi anomali (es. etichetta fuori elenco).
- **Riferimenti incrociati:** Switch; Branch; `{lastMailBody}` (esempio input).

---

### Estrai dati (AI)  — DSL `ExtractStructured`  `L1615`

*(nome DSL ✅ CONFERMATO, evidenza F4:114. ⚠️ NON regolare: display italiano tradotto/rinominato in inglese — non deducibile per convenzione, ma osservato.)*

- **Scopo:** L'AI estrae dati strutturati da un testo secondo uno schema JSON d'esempio (null per i campi assenti), con parse e validazione. Output navigabile via placeholder.
- **Quando usarlo:** Quando serve estrarre dati strutturati da un testo (es. corpo di un'email o testo di un PDF) secondo uno schema JSON d'esempio che definisce campi e tipi attesi. L'AI usa `null` per i dati assenti e i campi top-level mancanti generano `lastExtractWarning`; con parse e validazione. Il risultato `lastExtractedJson` è navigabile via placeholder.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `input` | testo lungo | Sì | — | Testo (o placeholder `{chiave}`) da cui estrarre i dati, es. il corpo di un'email o il testo di un PDF. — es. `{lastPdfText}` |
| `schema` | JSON | Sì | — | Esempio della struttura attesa: stessi campi e tipi della risposta. L'AI usa `null` per i dati assenti; i campi top-level mancanti generano `lastExtractWarning`. — es. `{"cliente":"","articoli":[{"codice":"","qta":0}]}` |
| `instructions` | testo lungo | — | — | Indicazioni aggiuntive per l'estrazione (unità di misura, formati data, ecc.). |
| `provider` | scelta — claude · openai · ollama · vllm | — | — | Vuoto = eredita dalla chat dell'agente (o Claude). |
| `model` | modello AI | — | — | Vuoto = modello di default del provider. |
| `timeoutSeconds` | intero | — | 0 | 0 = nessun limite per-step. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastExtractedJson` | JSON | Dati estratti conformi allo schema (navigabili via placeholder). |
| `lastExtractWarning` | testo | Avviso (es. campi dello schema assenti nella risposta). |

- **⚠️ Avvertenze / vincoli:**
  - Vincolo: i campi top-level dello schema mancanti nella risposta generano `lastExtractWarning`; l'AI usa `null` per i dati assenti.
  - ⚠️ (Debug, guida `L1436`) AiAnalysis/ExtractStructured girano davvero e consumano token anche in debug/dry-run: usa "Non chiamare AI/API esterne" per simularli.
- **Riferimenti incrociati:** `{lastPdfText}` (esempio input); PDF Extract / Word Extract (sorgenti tipiche del testo); AI Analysis (condivide la guida Debug `L1436`).

---

### Indicizza conoscenza (RAG)  — DSL `RagEmbed` ✅ CONFERMATO (corso M10)  `L1649`

*(nome DSL ✅ CONFERMATO dal video corso — palette del modulo 10 «Le palette in dettaglio — AI».)*

- **Scopo:** Indicizza testo nella base di conoscenza (chunking + embedding): i documenti diventano interrogabili semanticamente. Re-indicizzare la stessa origine sostituisce i chunk precedenti.
- **Quando usarlo:** Quando serve aggiungere testo (es. `{lastPdfText}` o `{lastWordText}`) alla base di conoscenza per renderlo interrogabile semanticamente: il testo viene spezzato in chunk e vettorizzato (embedding). Re-indicizzare la stessa origine SOSTITUISCE i suoi chunk (operazione idempotente, salvo `replaceSource` disattivato che accoda). Da usare a monte di "Cerca nella conoscenza (RAG)" sulla stessa raccolta. Più agenti dello stesso owner possono condividere la raccolta.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `input` | testo lungo | Sì | — | Testo (o placeholder `{chiave}`) da aggiungere alla base di conoscenza, es. `{lastPdfText}` o `{lastWordText}`. Viene spezzato in chunk e vettorizzato. — es. `{lastPdfText}` |
| `sourceName` | testo | Sì | — | Etichetta della sorgente (es. nome file). Re-indicizzare la stessa origine SOSTITUISCE i suoi chunk (idempotente). Placeholder supportati. — es. `{__loopItem}` |
| `collection` | testo | — | default | Raccolta logica della conoscenza (es. 'listini', 'manuali'). Più agenti dello stesso owner possono condividerla. |
| `chunkSize` | intero | — | 1000 | Lunghezza massima dei blocchi di testo indicizzati (char). |
| `overlap` | intero | — | 100 | Coda del chunk precedente ripetuta nel successivo (continuità di contesto, char). |
| `replaceSource` | sì/no | — | true | Se attivo (default) i chunk esistenti della stessa origine vengono sostituiti; disattivato = accoda. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastRagStored` | intero | Numero di chunk indicizzati. |
| `lastRagSource` | testo | Nome origine indicizzata (risolto). |
| `lastRagCollection` | testo | Raccolta usata. |

- **⚠️ Avvertenze / vincoli:**
  - Vincolo: re-indicizzare la stessa origine (`sourceName`) SOSTITUISCE i suoi chunk precedenti (idempotente) quando `replaceSource` è attivo (default); disattivandolo si accoda invece di sostituire.
- **Riferimenti incrociati:** Cerca nella conoscenza (RAG) (interroga la stessa raccolta); `{lastPdfText}`; `{lastWordText}`; `{__loopItem}` (esempio `sourceName`).

---

### Report PDF/DOCX/XLSX  — DSL `GenerateReport` ✅ CONFERMATO (corso M10)  `L1685`

*(nome DSL ✅ CONFERMATO dal video corso — palette del modulo 10 «Le palette in dettaglio — AI».)*

- **Scopo:** Genera un documento XLSX/PDF/DOCX (anche PPTX) con grafici sfruttando le Skills Anthropic.
- **Quando usarlo:** Quando serve generare un documento (pdf/docx/xlsx/pptx) con grafici a partire da un prompt che compone il report, sfruttando le Skills Anthropic. Il prompt supporta `{placeholder}` per iniettare i dati da includere (es. `{lastQueryRows}`); opzionalmente si possono allegare le righe query come CSV.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `prompt` | testo lungo | Sì | — | Istruzione per comporre il report. Supporta `{placeholder}` (es. i dati da includere). — es. `Crea un report del fatturato: {lastQueryRows}` |
| `format` | scelta — pdf · docx · xlsx · pptx | Sì | — | Formato del file generato. |
| `outputPath` | testo | — | — | Path di output. — es. `reports/{agentName}.pdf` |
| `model` | testo | — | — | Modello. |
| `attachLastQueryRows` | sì/no | — | — | Allega righe query (CSV). |
| `csvFileName` | testo | — | data.csv | Nome CSV. |
| `promptPrefix` | testo lungo | — | — | Prefisso prompt. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastReportPath` | testo | Path relativo del documento. |
| `lastReportFullPath` | testo | Path assoluto. |
| `lastReportFormat` | testo | Formato (pdf/docx/xlsx/pptx). |
| `lastReportBytes` | intero | Dimensione in byte. |

- **Riferimenti incrociati:** `{lastQueryRows}` (esempio prompt / `attachLastQueryRows`); `{agentName}` (esempio `outputPath`); Query SQL (sorgente tipica di `lastQueryRows`).
