# Catalogo blocchi — Output + Script

> Categoria "Output + Script" (4 blocchi). Ogni scheda cita il rif `L####` (riga dell'HTML sorgente del manuale) e, dove disponibile, l'evidenza `Flusso:riga` dai flussi esportati.
> Fonte parametri/output: `scratchpad/inventario-fase1.md`. Fonte nomi DSL: `references/nomi-blocchi.md` (autorità).
> Tutti i nomi DSL sono confermati (dai flussi o dal video corso).

---

### Markdown  — DSL `Markdown`  `L3209`
(✅ nome DSL CONFERMATO — evidenza Flusso F1:708; identico al DISPLAY)

- **Scopo:** Converte una chiave dello StepData tra Markdown / HTML / testo semplice / Telegram / Slack (es. corpo email, contenuto dashboard, messaggio di messaggistica).
- **Quando usarlo:** Prima di inviare un testo via email, dashboard o messaggistica, quando serve trasformarne il formato. Tipicamente si converte `lastAiOutput` o `lastChatAnswer` da Markdown a HTML (per email/dashboard) oppure da HTML alla resa specifica del canale (Telegram/Slack/testo semplice).
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `direction` | scelta — mdToHtml · htmlToMd · htmlToText · htmlToTelegram · htmlToSlack | — | mdToHtml | (Direzione) mdToHtml=Markdown→HTML (email/dashboard). htmlToMd=HTML→Markdown. htmlToText=testo semplice. htmlToTelegram=HTML→Telegram (richiede parseMode=HTML nel SendTelegram). htmlToSlack=HTML→Slack mrkdwn. Tabelle→righe leggibili in tutte le varianti htmlTo*. |
| `sourceKey` | testo | — | lastAiOutput | (Chiave sorgente) Chiave StepData sorgente (es. lastAiOutput o lastChatAnswer). |
| `outputKey` | testo | — | — | (Chiave output) Chiave StepData destinazione. Vuoto = lastMarkdownHtml / lastMarkdownText / lastPlainText / lastTelegramText / lastSlackText secondo la direzione. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastMarkdownHtml` | testo | HTML risultante (direzione mdToHtml). |
| `lastMarkdownText` | testo | Markdown risultante (direzione htmlToMd). |
| `lastPlainText` | testo | Testo semplice risultante (direzione htmlToText). |
| `lastTelegramText` | testo | Testo Telegram (HTML subset) risultante (direzione htmlToTelegram). |
| `lastSlackText` | testo | Testo Slack (mrkdwn) risultante (direzione htmlToSlack). |

- **⚠️ Avvertenze / vincoli:**
  - ⚠️ `direction=htmlToTelegram` richiede `parseMode=HTML` nel blocco SendTelegram per rendere correttamente (L3210).
  - Se `outputKey` è vuoto, la chiave di destinazione dipende dalla direzione (vedi Note del parametro): non assumere `lastMarkdownHtml` a prescindere.
- **Riferimenti incrociati:** `lastAiOutput`; `lastChatAnswer`; SendTelegram (`parseMode=HTML`); Publish Dashboard / Email (consumatori tipici dell'HTML prodotto).

---

### Publish Dashboard  — DSL `PublishDashboard` ✅ CONFERMATO (corso M17)  `L3237`
(✅ nome DSL CONFERMATO dal video corso — modulo 17 «Output», `node-PublishDashboard`.)

- **Scopo:** Aggiorna il contenuto di una dashboard personalizzata.
- **Quando usarlo:** Quando serve pubblicare/aggiornare (in sostituzione o in coda) il contenuto di una dashboard personalizzata con l'output di uno step, tipicamente `{lastAiOutput}`.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `dashboardName` | testo | Sì | — | (Nome dashboard) Nome della dashboard da pubblicare/aggiornare. — es. `Vendite 2026` |
| `content` | testo lungo | — | {lastAiOutput} | (Contenuto) |
| `mode` | scelta — replace · append | — | replace | (Modalità) |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastDashboardPublished` | testo | Nome dashboard aggiornata. |

- **Riferimenti incrociati:** `{lastAiOutput}`; Markdown (per convertire il contenuto in HTML prima della pubblicazione).

---

### Code JS  — DSL `CodeJs`  `L3257`
(✅ nome DSL CONFERMATO — evidenza Flusso F1:13; spazi rimossi rispetto al DISPLAY)

- **Scopo:** Esegue codice JavaScript in sandbox, con API a oggetti `$input`/`$json` più `return`.
- **Quando usarlo:** Quando serve logica custom non coperta dai blocchi (trasformazioni, calcoli, preparazione di payload/array — es. per Insert SQL). Insieme a `CodePython.code` è l'unico codice realmente eseguito. Due modalità: RunOnce (esecuzione singola) o RunForEach (per item).
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `code` | codice — js | Sì | — | (Codice JS) |
| `mode` | scelta — RunOnce · RunForEach | — | RunOnce | (Modalità) |
| `timeoutMs` | intero | — | 5000 | (Timeout (ms)) |
| `outputKey` | testo | — | — | (Chiave output) |
| `outputItemsKey` | testo | — | lastItems | (Chiave items output) |
| `inputItemsKey` | testo | — | — | (Chiave items input) |
| `continueOnFail` | sì/no | — | false | (Continua su errore (RunForEach)) |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `{outputKey}` (dal campo `outputKey`) | JSON | Valore di `return` dello script. |
| `{outputItemsKey}` (dal campo `outputItemsKey`) | JSON | Items normalizzati (default `lastItems`). |

- **⚠️ Avvertenze / vincoli:**
  - ⚠️ È l'unico codice realmente eseguito, insieme a `CodePython.code`; la vista a codice del flusso è un DSL NON eseguito (L8).
  - `continueOnFail` ha effetto solo in modalità RunForEach.
- **Riferimenti incrociati:** `CodeJs.code` (L8); `$input` / `$json`; `lastItems`; Insert SQL (destinatario tipico dell'array preparato via `rowsKey`); Code Python.

---

### Code Python  — DSL `CodePython` ✅ CONFERMATO (corso M9)  `L3295`
(✅ nome DSL CONFERMATO dal video corso — modulo 9 «Script», `node-CodePython`.)

- **Scopo:** Esegue codice Python in un subprocess sandboxato.
- **Quando usarlo:** Quando serve logica custom in Python (trasformazioni/calcoli non coperti dai blocchi). Insieme a `CodeJs.code` è l'unico codice realmente eseguito.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `code` | codice — python | Sì | — | (Codice Python) |
| `pythonPath` | testo | — | — | (Interprete Python) Override per-step (path assoluto). |
| `timeoutMs` | intero | — | 30000 | (Timeout (ms)) |
| `outputKey` | testo | — | — | (Chiave output) |
| `outputItemsKey` | testo | — | lastItems | (Chiave items output) |
| `inputItemsKey` | testo | — | — | (Chiave items input) |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `{outputKey}` (dal campo `outputKey`) | JSON | stdout JSON dello script. |
| `{outputItemsKey}` (dal campo `outputItemsKey`) | JSON | Items normalizzati (default `lastItems`). |

- **⚠️ Avvertenze / vincoli:**
  - ⚠️ È l'unico codice realmente eseguito, insieme a `CodeJs.code`; la vista a codice del flusso è un DSL NON eseguito (L8).
- **Riferimenti incrociati:** `CodePython.code` (L8); `lastItems`; Code JS.
