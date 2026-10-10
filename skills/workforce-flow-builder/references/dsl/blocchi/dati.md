# Catalogo blocchi — Dati

> Categoria "Dati" del manuale ThinkAI Workforce Studio. Una scheda per blocco (16 blocchi).
> `L####` = riga nell'HTML sorgente del manuale. I nomi DSL provengono da `references/nomi-blocchi.md` (unica autorità); sono tutti confermati (15 dai flussi, gli altri dal video corso).
> I nomi dei parametri coincidono col manuale e sono riportati esatti e completi.

## Indice
1. [Chiedi alla Chat (sicuro)](#chiedi-alla-chat-sicuro--dsl-securechatquery--dati) — `L1727`
2. [Delete File](#delete-file--dsl-filedelete--dati) — `L1755`
3. [Excel Online Append](#excel-online-append--dsl-excelonlineappend--dati) — `L1771`
4. [Excel Online Read](#excel-online-read--dsl-excelonlineread--dati) — `L1821`
5. [File List](#file-list--dsl-filelist--dati) — `L1855`
6. [Insert SQL](#insert-sql--dsl-sqlinsert--dati) — `L1875`
7. [JSON a file](#json-a-file--dsl-jsontofile--dati) — `L1901`
8. [JSON da file](#json-da-file--dsl-jsonfromfile--dati) — `L1929`
9. [JSON Parse](#json-parse--dsl-jsonparse--dati) — `L1951`
10. [Move File](#move-file--dsl-filemove--dati) — `L1971`
11. [Query SQL](#query-sql--dsl-query--dati) — `L1997`
12. [Read File](#read-file--dsl-fileread--dati) — `L2021`
13. [Sheets Append](#sheets-append--dsl-googlesheetsappend--dati) — `L2041`
14. [Sheets Read](#sheets-read--dsl-googlesheetsread--dati) — `L2079`
15. [Update SQL](#update-sql--dsl-sqlupdate--dati) — `L2105`
16. [Write File](#write-file--dsl-filewrite--dati) — `L2135`

---

### Chiedi alla Chat (sicuro)  — DSL `SecureChatQuery` ✅ CONFERMATO (corso M11)  `L1727`

- **Scopo:** Interroga il gestionale RESTANDO nel perimetro dell'utente: inoltra la domanda alla pipeline chat sicura agendo come un'identità configurata (viste collegate + permesso categoria + isolamento azienda). Risposta in `StepData["lastChatAnswer"]`.
- **Quando usarlo:** Quando serve interrogare il gestionale in linguaggio naturale restando dentro il perimetro di sicurezza di uno specifico utente (viste collegate, permesso categoria, isolamento azienda), agendo come identità configurata. Utile per esporre risposte in chat sicura da input come `{inboundText}`/`{slackText}`, opzionalmente isolando la conversazione per utente finale con `userKey`.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `userMessage` | testo lungo | Sì | — | Testo della domanda (placeholder ammessi, es. `{inboundText}` / `{slackText}`). — es. `{inboundText}` |
| `runAsUserName` | testo | Sì | — | Username/email dell'utente che definisce il perimetro sicurezza. Admin e SystemAdmin sono consentiti per costruire/collaudare agenti; la Chat selezionata deve appartenere a questo utente. — es. `admin@azienda.it` |
| `chatId` | intero | — | — | ID della Chat dell'utente run-as con viste/connessione/permessi. Configuralo nei nuovi flussi; vuoto resta solo fallback legacy alla Chat dell'agente. — es. `9` |
| `context` | testo | — | — | Opzionale: TipologiaAnalisi da forzare (es. Vendite, Clienti) saltando il riconoscimento automatico per keyword. Il permesso vista resta comunque verificato. Vuoto = argomento dedotto dalla domanda. — es. `Vendite` |
| `userKey` | testo | — | — | Opzionale: isola la conversazione per utente finale. Ogni valore distinto (es. `{inboundChatId}` Telegram, `{slackUser}`) ottiene una Chat dedicata clonata dal template (stesso perimetro, storia/memoria separate). Vuoto = conversazione condivisa. — es. `{inboundChatId}` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastChatAnswer` | testo | Risposta in linguaggio naturale entro il perimetro dell'utente run-as. |

- **⚠️ Avvertenze / vincoli:**
  - La Chat selezionata deve appartenere all'utente run-as (`runAsUserName`).
  - Solo Admin e SystemAdmin sono consentiti per costruire/collaudare agenti.
  - `chatId`: configuralo nei nuovi flussi; vuoto resta solo fallback legacy alla Chat dell'agente.
  - Il permesso vista resta comunque verificato anche forzando il contesto (`context`).
- **Riferimenti incrociati:** `lastChatAnswer`; `{inboundText}`; `{slackText}`; `{inboundChatId}`; `{slackUser}`; TipologiaAnalisi.

---

### Delete File  — DSL `FileDelete` ✅ CONFERMATO (corso M11)  `L1755`

- **Scopo:** Elimina un file.
- **Quando usarlo:** Quando serve eliminare un file (percorso relativo alla sandbox); opzionalmente si può fare fallire lo step se il file è assente.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `filePath` | testo | Sì | — | Percorso del file da eliminare (relativo alla sandbox). — es. `output/vecchio.txt` |
| `failIfMissing` | sì/no | — | false |  |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastDeletedPath` | testo | Path eliminato. |

- **⚠️ Avvertenze / vincoli:**
  - `filePath` è relativo alla sandbox.
- **Riferimenti incrociati:** Move File; Read File; Write File (gestione file nella sandbox).

---

### Excel Online Append  — DSL `ExcelOnlineAppend` ✅ CONFERMATO (corso M11)  `L1771`

- **Scopo:** Appende righe a un Excel su OneDrive/SharePoint: su tabella (consigliato, atomico) o in coda al foglio.
- **Quando usarlo:** Quando serve accodare righe (da una collezione StepData, es. `lastQueryRows`) a un file Excel su OneDrive/SharePoint tramite credenziale Microsoft 365, preferibilmente su una tabella Excel (append atomico) oppure in coda al foglio. Supporta modalità `append`/`appendNew` (deduplicazione per Colonne chiave)/`overwrite`.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `credentialName` | credenziale | Sì | — | Credenziale OAuth Microsoft 365 salvata (la stessa di SharePoint/Outlook). |
| `filePath` | testo | — | — | Path del file .xlsx nel drive (alternativa a ID file). — es. `Documenti/ordini.xlsx` |
| `itemId` | testo | — | — | ID Graph del file (vince sul percorso). Opzionale se usi il percorso. |
| `siteId` | testo | — | — | Vuoto = OneDrive personale. Valorizzato = drive del sito SharePoint indicato. |
| `table` | testo | — | — | Nome della tabella Excel a cui accodare (append atomico). Vuoto = accoda in coda al foglio (usedRange). — es. `Tabella1` |
| `worksheet` | testo | — | — | Usato solo SENZA tabella. Vuoto = primo foglio. — es. `Foglio1` |
| `source` | testo | Sì | — | Chiave StepData con la collezione di righe da accodare (oggetti o array). — es. `lastQueryRows` |
| `columns` | testo | — | — | Ordine delle colonne per righe-oggetto. Vuoto = chiavi del primo oggetto. — es. `codice, importo` |
| `writeMode` | scelta — append · appendNew · overwrite | — | append | append = accoda sempre (storico); appendNew = accoda SOLO le righe con chiave nuova (vedi Colonne chiave) — niente duplicati; overwrite = svuota le righe dati (preserva l'intestazione) e riscrive solo quelle correnti. |
| `keyColumns` | testo | — | — | Solo per appendNew: colonne che identificano univocamente una riga (es. 'codice'). Le righe la cui chiave è già nel foglio NON vengono riscritte. — es. `codice` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastSheetAppended` | intero | Numero righe accodate. |
| `lastSheetUpdatedRange` | testo | Range scritto (null per append su tabella Excel). |

- **⚠️ Avvertenze / vincoli:**
  - Append su tabella è consigliato perché atomico.
  - `itemId` vince sul percorso (`filePath`).
  - `worksheet` è usato solo SENZA tabella.
  - `keyColumns` è usato solo per `writeMode=appendNew`.
  - `writeMode=overwrite` svuota le righe dati (preserva l'intestazione) e riscrive solo quelle correnti.
- **Riferimenti incrociati:** Sheets Append / `GoogleSheetsAppend` (stesse chiavi output/logica su Google Sheet); Excel Online Read; SharePoint; Outlook; `lastQueryRows`.

---

### Excel Online Read  — DSL `ExcelOnlineRead` ✅ CONFERMATO (corso M11)  `L1821`

- **Scopo:** Legge righe da un Excel su OneDrive/SharePoint (credenziale Microsoft 365). Stesse chiavi output di Sheets Read.
- **Quando usarlo:** Quando serve leggere righe da un file Excel su OneDrive/SharePoint tramite credenziale Microsoft 365, con la prima riga opzionalmente usata come intestazioni per ottenere oggetti navigabili. Condivide le chiavi output con Sheets Read.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `credentialName` | credenziale | Sì | — | Credenziale OAuth Microsoft 365 salvata (la stessa di SharePoint/Outlook). |
| `filePath` | testo | — | — | Path del file .xlsx nel drive (alternativa a ID file). — es. `Documenti/ordini.xlsx` |
| `itemId` | testo | — | — | ID Graph del file (vince sul percorso). Opzionale se usi il percorso. |
| `siteId` | testo | — | — | Vuoto = OneDrive personale. Valorizzato = drive del sito SharePoint indicato. |
| `worksheet` | testo | — | — | Nome del worksheet. Vuoto = primo foglio del workbook. — es. `Foglio1` |
| `hasHeaders` | sì/no | — | true | Se attivo le righe diventano oggetti con i nomi delle intestazioni; altrimenti col1..colN. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastSheetRows` | JSON | Righe lette (oggetti per intestazione o col1..colN). |
| `lastSheetRowCount` | intero | Numero righe lette. |

- **⚠️ Avvertenze / vincoli:**
  - `itemId` vince sul percorso (`filePath`).
  - Stesse chiavi output di Sheets Read.
- **Riferimenti incrociati:** Sheets Read; Excel Online Append; SharePoint; Outlook.

---

### File List  — DSL `FileList`  `L1855`

- **Scopo:** Elenca i file di una directory (con pattern).
- **Quando usarlo:** Quando serve elencare i file presenti in una directory, eventualmente filtrando per pattern e/o cercando in modo ricorsivo.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `directory` | testo | Sì | — | — es. `input/` |
| `pattern` | testo | — | * | — es. `*.pdf` |
| `recursive` | sì/no | — | false |  |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastFileList` | JSON | Elenco file trovati. |

- **Riferimenti incrociati:** Read File; Move File; Delete File; `lastFileList` (iterabile con ForEach).

---

### Insert SQL  — DSL `SqlInsert` ✅ CONFERMATO (corso M11)  `L1875`

- **Scopo:** Inserisce una o più righe in una tabella del DB cliente con INSERT parametrizzato (valori bound, schema validato: solo colonne reali). Per tabelle d'appoggio/frontiera. La Query resta read-only.
- **Quando usarlo:** Quando serve inserire una o più righe in una tabella d'appoggio/frontiera del DB cliente con INSERT parametrizzato (valori bound, schema validato). Usare `rowsKey` per un array di oggetti (tipicamente da un Code JS) oppure `values` per una riga singola; opzionalmente su una connessione dati specifica. Operazione di scrittura, distinta dalla Query SQL che resta read-only.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `table` | testo | Sì | — | Nome tabella di destinazione (ammesso schema.tabella). Deve esistere: lo schema viene letto e si accettano solo colonne reali. — es. `ORDINI_FRONTIERA` |
| `rowsKey` | testo | — | — | Chiave StepData con un ARRAY di oggetti {colonna: valore} (tipicamente da un Code JS). Ha precedenza su 'values'. Le chiavi non presenti nello schema tabella vengono ignorate. — es. `righeFrontiera` |
| `values` | JSON | — | — | Alternativa a 'rowsKey': oggetto JSON {colonna: valore} per UNA riga; i valori stringa supportano placeholder {chiave} risolti dallo StepData. Valori sempre passati come parametri bound. — es. `{"COD_CF":"{codCf}","STATO":1}` |
| `dataConnectionId` | intero | — | — | Vuoto = connessione della Chat dell'agente. Valorizzato = quella connessione (deve appartenere all'owner). È un'operazione di SCRITTURA: usa un account DB con permessi di INSERT sulla tabella. |
| `idempotencyKey` / `idempotencyGroup` / `idempotencyRetryOnFailure` | testo / testo / sì-no | — | — | ✅ CONFERMATO (flusso GAZZA v1.4.1, esportato — es. `"gazza-log-start-{fileCorrelationId}"`). Vedi `pattern.md` §A8: rende l'INSERT sicuro da ripetere su retry/crash/ForEach senza duplicare la riga. Chiave da un identificativo business stabile, mai timestamp/GUID. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastInsertRowCount` | intero | Righe inserite. |
| `lastInsertInfo` | JSON | Dettaglio insert (tabella, colonne, colonne ignorate, dataConnection). |

- **⚠️ Avvertenze / vincoli:**
  - Operazione di SCRITTURA: usa un account DB con permessi di INSERT sulla tabella.
  - La tabella deve esistere: lo schema viene letto e si accettano solo colonne reali.
  - Le chiavi non presenti nello schema tabella vengono ignorate.
  - `rowsKey` ha precedenza su `values`.
  - `dataConnectionId` valorizzato deve appartenere all'owner.
  - La Query resta read-only (solo Insert/Update/Delete scrivono).
  - Pattern di guardia osservato in produzione (GAZZA): dopo l'insert, controllare `lastInsertRowCount === 1` e fare `throw` se diverso, per intercettare race-condition su chiavi di correlazione concorrenti.
- **Riferimenti incrociati:** Code JS (alimenta `rowsKey`); Query SQL; Update SQL; `lastQueryRows`; `pattern.md` §A8 (idempotenza).

---

### JSON a file  — DSL `JsonToFile` ✅ CONFERMATO (corso M11)  `L1901`

- **Scopo:** Serializza dati in un file .json.
- **Quando usarlo:** Quando serve serializzare un oggetto/array presente nello StepData in un file .json su path target (con placeholder), scegliendo indentazione, sovrascrittura e creazione automatica della cartella.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `sourceKey` | testo | Sì | — | Chiave StepData con l'oggetto/array da serializzare nel file. — es. `lastAiJson` |
| `target` | testo | Sì | — | — es. `audit/{agentName}/{timestamp}.json` |
| `indented` | sì/no | — | true |  |
| `overwrite` | sì/no | — | false |  |
| `createTargetDir` | sì/no | — | true |  |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastJsonWritten` | testo | Path del file scritto. |

- **Riferimenti incrociati:** JSON da file (operazione inversa); `lastAiJson`; `{agentName}`; `{timestamp}`.

---

### JSON da file  — DSL `JsonFromFile` ✅ CONFERMATO (corso M11)  `L1929`

- **Scopo:** Legge e parse un file .json.
- **Quando usarlo:** Quando serve leggere e fare il parse di un file .json e mettere l'oggetto risultante in una chiave StepData indicata; opzionalmente fallire se il JSON non è valido.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `filePath` | testo | Sì | — | Percorso del file JSON da leggere. — es. `input/dati.json` |
| `outputKey` | testo | Sì | — | Chiave StepData dove mettere il JSON letto. — es. `datiFile` |
| `failOnInvalid` | sì/no | — | true |  |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `{outputKey}` | JSON | Chiave dinamica dal campo `outputKey`: oggetto JSON letto dal file. |
| `lastJsonRead` | JSON | Ultimo JSON letto. |

- **Riferimenti incrociati:** JSON a file (operazione inversa); JSON Parse (per parse di una stringa già in StepData).

---

### JSON Parse  — DSL `JsonParse` ✅ CONFERMATO (corso M11)  `L1951`

- **Scopo:** Converte una stringa JSON in oggetto usabile via placeholder.
- **Quando usarlo:** Quando serve convertire una stringa JSON già presente in una chiave StepData (es. `lastHttpResponse`) in un oggetto navigabile via placeholder, salvato in una chiave output; opzionalmente fallire se non valido.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `sourceKey` | testo | Sì | — | — es. `lastHttpResponse` |
| `outputKey` | testo | Sì | — | — es. `parsed` |
| `failOnInvalid` | sì/no | — | true |  |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `{outputKey}` | JSON | Chiave dinamica dal campo `outputKey`: oggetto JSON parsato. |

- **Riferimenti incrociati:** JSON da file (parse da file invece che da stringa); `lastHttpResponse` (sorgente tipica).

---

### Move File  — DSL `FileMove`  `L1971`

- **Scopo:** Sposta/rinomina un file.
- **Quando usarlo:** Quando serve spostare o rinominare un file da una sorgente a una destinazione, opzionalmente sovrascrivendo l'eventuale file esistente e creando la cartella di destinazione.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `source` | testo | Sì | — | File di origine da spostare. — es. `input/a.pdf` |
| `target` | testo | Sì | — | Percorso di destinazione. — es. `archivio/a.pdf` |
| `overwrite` | sì/no | — | false |  |
| `createTargetDir` | sì/no | — | true |  |
| `allowedRoot` | testo | — | — | ✅ CONFERMATO (flusso GAZZA v1.4.1, esportato). Fence di sicurezza: la destinazione (`target`) viene rifiutata se non ricade sotto questa cartella radice (tipicamente `{workRoot}`). Da impostare sempre quando `target` è (anche in parte) costruito da dati derivati da AI o da file esterni, per evitare che un percorso malformato/malevolo scriva fuori dall'area di lavoro dell'agente. |
| `idempotencyKey` / `idempotencyGroup` / `idempotencyRetryOnFailure` | testo / testo / sì-no | — | — | ✅ CONFERMATO (GAZZA). Vedi `pattern.md` §A8 — protegge lo spostamento da doppia esecuzione su retry/crash. Usare una chiave di business stabile (es. include l'item corrente del ForEach), mai timestamp/GUID. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastMovedFrom` | testo | Path sorgente. |
| `lastMovedTo` | testo | Path destinazione. |

- **⚠️ Avvertenze / vincoli:**
  - ⚠️ `allowedRoot` è confermato da un flusso reale esportato ma non ha ancora una scheda palette dedicata nel manuale: verifica in Studio l'etichetta esatta prima di assumere altri dettagli non elencati qui.
- **Riferimenti incrociati:** File List; Read File; Write File; Delete File; `pattern.md` §A8 (idempotenza), §claim atomico anti-race.

---

### Query SQL  — DSL `Query`  `L1997`

- **Scopo:** Esegue una query SQL sul database del cliente; le righe sono disponibili agli step successivi.
- **Quando usarlo:** Quando serve leggere dati dal database del cliente con una query SELECT (sola lettura); le righe restituite (`lastQueryRows`) sono disponibili agli step successivi. Opzionalmente si sceglie il limite righe e una connessione dati specifica per agenti multi-DB.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `sql` | codice — sql | Sì | — | Query SELECT (sola lettura). |
| `maxRows` | intero | — | 1000 | Limite righe restituite. |
| `dataConnectionId` | intero | — | — | Vuoto = connessione della Chat dell'agente (default storico). Valorizzato = esegue su quella connessione dati (deve appartenere all'owner dell'agente) — abilita agenti multi-DB. Consiglio: per le origini extra usa un account DB in sola lettura. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastQueryRows` | JSON | Righe restituite (array). |
| `lastQueryRowCount` | intero | Numero righe. |
| `lastQueryColumns` | JSON | Nomi colonne. |

- **⚠️ Avvertenze / vincoli:**
  - Solo query SELECT (sola lettura).
  - `dataConnectionId` valorizzato deve appartenere all'owner dell'agente.
  - Consiglio: per le origini extra usa un account DB in sola lettura.
- **Riferimenti incrociati:** Insert SQL; Update SQL (operazioni di scrittura); `lastQueryRows` (consumato da Sheets Append / Excel Online Append / Report).

---

### Read File  — DSL `FileRead` ✅ CONFERMATO (corso M11)  `L2021`

- **Scopo:** Legge un file dalla base dati Workforce.
- **Quando usarlo:** Quando serve leggere il contenuto di un file dalla base dati Workforce, opzionalmente limitando i byte letti.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `path` | testo | Sì | — | — es. `input/data.txt` |
| `maxBytes` | intero | — | 1048576 |  |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastFileContent` | testo | Contenuto del file. |
| `lastFilePath` | testo | Path del file letto. |
| `lastFileBytes` | intero | Byte letti. |

- **Riferimenti incrociati:** Write File (operazione inversa); File List; Move File; Delete File.

---

### Sheets Append  — DSL `GoogleSheetsAppend` ✅ CONFERMATO (corso M11)  `L2041`

- **Scopo:** Appende righe in coda a un Google Sheet da una collezione dello StepData (es. `lastQueryRows`).
- **Quando usarlo:** Quando serve accodare righe a un Google Sheet (credenziale Google OAuth) da una collezione dello StepData (es. `lastQueryRows`). Supporta modalità `append`/`appendNew` (deduplicazione per Colonne chiave)/`overwrite` e ordine colonne personalizzato.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `credentialName` | credenziale | Sì | — | Credenziale OAuth Google salvata (la stessa di Gmail/Drive). |
| `spreadsheetId` | testo | Sì | — | — es. `1AbC2dEf...` |
| `range` | testo | — | A1 | Il foglio (o range) a cui accodare: l'API trova da sola la prima riga libera. — es. `Foglio1!A1` |
| `source` | testo | Sì | — | Chiave StepData con la collezione di righe da accodare (oggetti o array). — es. `lastQueryRows` |
| `columns` | testo | — | — | Ordine delle colonne per righe-oggetto (es. 'codice, importo'). Vuoto = chiavi del primo oggetto. — es. `codice, importo` |
| `writeMode` | scelta — append · appendNew · overwrite | — | append | append = accoda sempre (storico); appendNew = accoda SOLO le righe con chiave nuova (vedi Colonne chiave) — niente duplicati; overwrite = svuota le righe dati (preserva l'intestazione) e riscrive solo quelle correnti. |
| `keyColumns` | testo | — | — | Solo per appendNew: colonne che identificano univocamente una riga (es. 'codice' o 'codice, cliente'). Le righe la cui chiave è già nel foglio NON vengono riscritte. — es. `codice` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastSheetAppended` | intero | Numero righe accodate. |
| `lastSheetUpdatedRange` | testo | Range scritto (null per append su tabella Excel). |

- **⚠️ Avvertenze / vincoli:**
  - `keyColumns` è usato solo per `writeMode=appendNew`.
  - `writeMode=overwrite` svuota le righe dati (preserva l'intestazione) e riscrive solo quelle correnti.
- **Riferimenti incrociati:** Excel Online Append (equivalente su Microsoft 365); Sheets Read; Gmail; Drive; `lastQueryRows`.

---

### Sheets Read  — DSL `GoogleSheetsRead` ✅ CONFERMATO (corso M11)  `L2079`

- **Scopo:** Legge righe da un Google Sheet (credenziale Google OAuth). Prima riga = intestazioni → oggetti navigabili. Stesse chiavi output di Excel Online Read.
- **Quando usarlo:** Quando serve leggere righe da un Google Sheet (credenziale Google OAuth), con la prima riga opzionalmente usata come intestazioni per ottenere oggetti navigabili. Condivide le chiavi output con Excel Online Read.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `credentialName` | credenziale | Sì | — | Credenziale OAuth Google salvata (la stessa di Gmail/Drive). Le credenziali collegate prima dell'introduzione dello scope Fogli vanno ricollegate. |
| `spreadsheetId` | testo | Sì | — | L'ID nell'URL del foglio: docs.google.com/spreadsheets/d/QUESTO/edit. — es. `1AbC2dEf...` |
| `range` | testo | — | A1:Z1000 | Range A1, opzionalmente con foglio: 'Foglio1!A1:F100'. Vuoto = A1:Z1000 del primo foglio. CONSIGLIO: indica le colonne reali (es. A1:F1000) — i range larghi su 26 colonne possono rendere l'API Google lentissima (timeout/500). — es. `Foglio1!A1:F100` |
| `hasHeaders` | sì/no | — | true | Se attivo le righe diventano oggetti con i nomi delle intestazioni; altrimenti col1..colN. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastSheetRows` | JSON | Righe lette (oggetti per intestazione o col1..colN). |
| `lastSheetRowCount` | intero | Numero righe lette. |

- **⚠️ Avvertenze / vincoli:**
  - Le credenziali collegate prima dell'introduzione dello scope Fogli vanno ricollegate.
  - CONSIGLIO: indica le colonne reali (es. A1:F1000) — i range larghi su 26 colonne possono rendere l'API Google lentissima (timeout/500).
  - Stesse chiavi output di Excel Online Read.
- **Riferimenti incrociati:** Excel Online Read (equivalente su Microsoft 365); Sheets Append; Gmail; Drive.

---

### Update SQL  — DSL `SqlUpdate` ✅ CONFERMATO (corso M11)  `L2105`

- **Scopo:** Aggiorna righe di una tabella del DB cliente con UPDATE parametrizzato (SET schema-validato, valori e WHERE bound). La WHERE è obbligatoria (no update intera tabella). Write controllato; la Query resta read-only.
- **Quando usarlo:** Quando serve aggiornare righe di una tabella del DB cliente con UPDATE parametrizzato (SET schema-validato, valori e WHERE bound). La WHERE è obbligatoria per evitare l'update dell'intera tabella. Usare `set` o `setKey` per le colonne da aggiornare; opzionalmente una connessione dati specifica. Write controllato, distinto dalla Query SQL read-only.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `table` | testo | Sì | — | Nome tabella (ammesso schema.tabella). Deve esistere: lo schema viene letto e si accettano solo colonne reali nel SET. — es. `ORDINI_FRONTIERA` |
| `set` | JSON | — | — | Oggetto {colonna: valore} delle colonne da aggiornare; i valori stringa supportano placeholder {chiave}. Valori sempre bound. Alternativa: 'setKey'. — es. `{"STATO":2,"DATA_ORA_IMPORT":"{now}"}` |
| `setKey` | testo | — | — | Alternativa a 'set': chiave StepData con l'oggetto {colonna: valore} (es. da Code JS). — es. `valoriUpdate` |
| `where` | testo | Sì | — | OBBLIGATORIA (no update intera tabella). Condizione SQL con placeholder {chiave} → parametri bound. Niente ';'. — es. `ID_ORDINE = {idOrdine}` |
| `dataConnectionId` | intero | — | — | Vuoto = connessione della Chat. Valorizzato = quella connessione (owner). SCRITTURA: usa un account DB con permessi di UPDATE. |
| `idempotencyKey` / `idempotencyGroup` / `idempotencyRetryOnFailure` | testo / testo / sì-no | — | — | ✅ CONFERMATO (flusso GAZZA v1.4.1, esportato — es. `"gazza-log-final-{fileCorrelationId}"`). Vedi `pattern.md` §A8. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastUpdateRowCount` | intero | Righe aggiornate. |
| `lastUpdateInfo` | JSON | Dettaglio update (tabella, colonne SET, where, dataConnection). |

- **⚠️ Avvertenze / vincoli:**
  - La WHERE è OBBLIGATORIA (no update intera tabella).
  - Operazione di SCRITTURA: usa un account DB con permessi di UPDATE.
  - Niente ';' nella condizione WHERE.
  - La tabella deve esistere: lo schema viene letto e si accettano solo colonne reali nel SET.
  - `dataConnectionId` valorizzato deve appartenere all'owner.
  - La Query resta read-only.
- **Riferimenti incrociati:** Code JS (alimenta `setKey`); Query SQL; Insert SQL; `{now}`.

---

### Write File  — DSL `FileWrite`  `L2135`

- **Scopo:** Scrive un file nella base dati Workforce.
- **Quando usarlo:** Quando serve scrivere un file nella base dati Workforce con contenuto testuale (supporta `{placeholder}`), in sovrascrittura o append, creando opzionalmente le cartelle mancanti.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `path` | testo | Sì | — | — es. `output/report.html` |
| `content` | testo lungo | Sì | — | Supporta {placeholder}. |
| `append` | sì/no | — | false |  |
| `createDirectories` | sì/no | — | true |  |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastFileWritten` | testo | Path del file scritto. |
| `lastFileBytes` | intero | Byte scritti. |

- **Riferimenti incrociati:** Read File (operazione inversa); Move File; Delete File; File List; JSON a file (per output strutturato).
