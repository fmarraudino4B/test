# Catalogo blocchi — Documenti

> Categoria "Documenti" del manuale ThinkAI Workforce Studio. Ogni scheda cita il riferimento `L####` (riga nell'HTML sorgente del manuale). I nomi DSL provengono da `references/nomi-blocchi.md` (unica autorità): sono tutti confermati (dal video corso per i blocchi non osservati nei flussi). I nomi dei parametri coincidono col manuale.

## Indice
1. [Drive Download](#drive-download--dsl-googledrivedownload--l2161)
2. [Drive List](#drive-list--dsl-googledrivelist--l2181)
3. [Drive Upload](#drive-upload--dsl-googledriveupload--l2205)
4. [OCR Image](#ocr-image--dsl-ocrimage--l2237)
5. [PDF Extract](#pdf-extract--dsl-pdfextract-confermato--l2255)
6. [SharePoint Download](#sharepoint-download--dsl-sharepointdownload--l2277)
7. [SharePoint List](#sharepoint-list--dsl-sharepointlist--l2301)
8. [SharePoint Upload](#sharepoint-upload--dsl-sharepointupload--l2325)
9. [Word Extract](#word-extract--dsl-wordextract-confermato--l2355)
10. [Xlsx Extract](#xlsx-extract--dsl-xlsxextract-confermato--l2369)

---

### Drive Download — DSL `GoogleDriveDownload` ✅ CONFERMATO (corso M12)  `L2161`

Nome DSL `GoogleDriveDownload` ✅ CONFERMATO dal video corso (modulo 12 «Documenti», `node-GoogleDriveDownload`).

- **Scopo:** Scarica un file da Google Drive.
- **Quando usarlo:** Usa questo blocco per scaricare un file specifico da Google Drive (identificato tramite il suo File ID) e salvarlo in un percorso locale. È il passo preliminare per lavorare sui Google Doc nativi: vanno prima scaricati (export automatico in `.docx`) prima di poter essere elaborati da Word Extract.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `credentialName` | credenziale | Sì | — | Credenziale Google. |
| `fileId` | testo | Sì | — | File ID. ID del file su Google Drive. Es. `1AbC2dEf...` |
| `localTargetPath` | testo | Sì | — | Path locale. Percorso locale dove salvare il file scaricato. Es. `download/file.pdf` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastDownloadedFilePath` | testo | Path locale scaricato. |

- **Riferimenti incrociati:** Word Extract (i Google Doc nativi vanno prima scaricati qui, con export automatico in `.docx`); `lastDownloadedFilePath` (alimenta il `filePath` degli extractor). Drive List (per selezionare i `fileId` da scaricare — inferenza, non nel manuale).

---

### Drive List — DSL `GoogleDriveList` ✅ CONFERMATO (corso M12)  `L2181`

Nome DSL `GoogleDriveList` ✅ CONFERMATO dal video corso (modulo 12 «Documenti», `node-GoogleDriveList`).

- **Scopo:** Elenca file da Google Drive.
- **Quando usarlo:** Usa questo blocco per ottenere l'elenco dei file presenti in una cartella di Google Drive, eventualmente filtrando per tipo MIME e limitando il numero di risultati. Utile per iterare o selezionare file prima di scaricarli.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `credentialName` | credenziale | Sì | — | Credenziale Google. |
| `folderId` | testo | — | — | Folder ID. Es. `root` |
| `mimeFilter` | testo | — | — | Filtro MIME. Es. `application/pdf` |
| `maxResults` | intero | — | 100 | Risultati max. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastDriveFiles` | JSON | Elenco file Drive. |

- **Riferimenti incrociati:** Drive Download (scarica i file elencati — inferenza, non nel manuale); ForEach (per iterare su `lastDriveFiles` — inferenza).

---

### Drive Upload — DSL `GoogleDriveUpload` ✅ CONFERMATO (corso M12)  `L2205`

Nome DSL `GoogleDriveUpload` ✅ CONFERMATO dal video corso (modulo 12 «Documenti», `node-GoogleDriveUpload`).

- **Scopo:** Carica un file su Google Drive.
- **Quando usarlo:** Usa questo blocco per caricare un file locale su Google Drive, opzionalmente specificando la cartella padre, il MIME type e la conversione in un formato Google nativo (es. docx → Doc nativo, csv/xlsx → Sheet nativo) al momento del caricamento.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `credentialName` | credenziale | Sì | — | Credenziale Google. |
| `localPath` | testo | Sì | — | Path locale. File locale da caricare. Es. `output/report.pdf` |
| `remoteName` | testo | Sì | — | Nome remoto. Nome del file su Drive. Es. `Report 2026.pdf` |
| `parentFolderId` | testo | — | — | Folder ID padre. `null` = root. |
| `mimeType` | testo | — | — | MIME type. Auto-detect se omesso. |
| `convertTo` | testo | — | — | Converti in formato Google. Opzionale: mimeType google-apps per convertire all'upload (docx → Doc nativo, csv/xlsx → Sheet nativo). Vuoto = carica il file com'è. Es. `application/vnd.google-apps.document` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastUploadedFileId` | testo | ID file caricato. |

- **⚠️ Avvertenze / vincoli:**
  - `parentFolderId`: `null` = root.
  - `mimeType`: auto-detect se omesso.
  - `convertTo`: vuoto = carica il file com'è; se valorizzato con un mimeType google-apps converte all'upload (docx → Doc nativo, csv/xlsx → Sheet nativo).

---

### OCR Image — DSL `OcrImage` ✅ CONFERMATO (corso M12)  `L2237`

Nome DSL `OcrImage` ✅ CONFERMATO dal video corso (modulo 12 «Documenti», `node-OcrImage`).

- **Scopo:** OCR di un'immagine (motore Tesseract).
- **Quando usarlo:** Usa questo blocco per estrarre il testo da un'immagine tramite OCR (motore Tesseract), specificando eventualmente le lingue di riconoscimento. Concatenalo a un passo precedente che produce il path dell'immagine: l'esempio usa la chiave StepData `{lastFilePath}`.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `filePath` | testo | Sì | — | Path immagine. Immagine da cui estrarre il testo (OCR). Es. `{lastFilePath}` |
| `lang` | testo | — | ita+eng | Lingue. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastOcrText` | testo | Testo OCR. |
| `lastOcrConfidence` | numero | Confidenza media. |

- **Riferimenti incrociati:** `{lastFilePath}` (esempio di sorgente del path immagine); PDF Extract (usa lo stesso motore OCR come fallback — inferenza dal parametro `ocrLang`).

---

### PDF Extract — DSL `PdfExtract` ✅ CONFERMATO  `L2255`

DSL `PdfExtract` (confermato, osservato in F4:53).

- **Scopo:** Estrae testo da un PDF (con fallback OCR).
- **Quando usarlo:** Usa questo blocco per estrarre il testo da un file PDF. Se il testo estratto è inferiore alla soglia di caratteri configurata (`fallbackToOcrUnderChars`), interviene automaticamente il fallback OCR con le lingue indicate in `ocrLang`.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `filePath` | testo | Sì | — | Path PDF. Es. `input/fattura.pdf` |
| `fallbackToOcrUnderChars` | intero | — | 100 | Soglia OCR (char). Sotto questa soglia di testo estratto scatta il fallback OCR. |
| `ocrLang` | testo | — | ita+eng | Lingue OCR (usate dal fallback OCR). |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastPdfText` | testo | Testo estratto. |
| `lastPdfPages` | JSON | Testo per pagina. |

- **Riferimenti incrociati:** OCR Image (stesso motore per il fallback OCR — inferenza); Estrai dati (AI) (`{lastPdfText}` è l'esempio di sorgente dell'estrazione strutturata); Indicizza conoscenza (RAG) (`{lastPdfText}` come testo da indicizzare).

---

### SharePoint Download — DSL `SharePointDownload` ✅ CONFERMATO (corso M12)  `L2277`

Nome DSL `SharePointDownload` ✅ CONFERMATO dal video corso (modulo 12 «Documenti», `node-SharePointDownload`).

- **Scopo:** Scarica un file da SharePoint.
- **Quando usarlo:** Usa questo blocco per scaricare un file da SharePoint (tramite credenziale Microsoft 365), indicando il path remoto del file e il percorso locale di destinazione; il Site ID è opzionale.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `credentialName` | credenziale | Sì | — | Credenziale M365. |
| `siteId` | testo | — | — | Site ID. |
| `remotePath` | testo | Sì | — | Path remoto. Es. `/Fatture/2026/file.pdf` |
| `localTargetPath` | testo | Sì | — | Path locale. Percorso locale dove salvare il file scaricato. Es. `download/file.pdf` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastDownloadedFilePath` | testo | Path locale scaricato. |

- **Riferimenti incrociati:** SharePoint List (per individuare i file da scaricare — inferenza); `lastDownloadedFilePath` (alimenta il `filePath` degli extractor); Excel Online Read / Excel Online Append e Outlook (condividono la stessa credenziale Microsoft 365 — inferenza dal manuale).

---

### SharePoint List — DSL `SharePointList` ✅ CONFERMATO (corso M12)  `L2301`

Nome DSL `SharePointList` ✅ CONFERMATO dal video corso (modulo 12 «Documenti», `node-SharePointList`).

- **Scopo:** Elenca file da SharePoint.
- **Quando usarlo:** Usa questo blocco per elencare i file di una cartella SharePoint (tramite credenziale Microsoft 365), eventualmente filtrando per nome. Se `siteId` è `root` o omesso, l'elenco riguarda il OneDrive personale.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `credentialName` | credenziale | Sì | — | Credenziale M365. |
| `siteId` | testo | — | — | Site ID. `root`/omesso = OneDrive personale. |
| `folderPath` | testo | — | — | Cartella. Es. `/Fatture/2026` |
| `filter` | testo | — | — | Filtro nome. Es. `*.pdf` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastSharePointFiles` | JSON | Elenco file SharePoint. |

- **⚠️ Avvertenze / vincoli:**
  - `siteId`: `root`/omesso = OneDrive personale.
- **Riferimenti incrociati:** SharePoint Download (scarica i file elencati — inferenza); ForEach (per iterare su `lastSharePointFiles` — inferenza).

---

### SharePoint Upload — DSL `SharePointUpload` ✅ CONFERMATO (corso M12)  `L2325`

Nome DSL `SharePointUpload` ✅ CONFERMATO dal video corso (modulo 12 «Documenti», `node-SharePointUpload`).

- **Scopo:** Carica un file su SharePoint.
- **Quando usarlo:** Usa questo blocco per caricare un file locale su SharePoint (tramite credenziale Microsoft 365), indicando il path remoto di destinazione e la strategia di gestione dei conflitti (`replace`, `rename` o `fail`); il Site ID è opzionale.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `credentialName` | credenziale | Sì | — | Credenziale M365. |
| `siteId` | testo | — | — | Site ID. |
| `localPath` | testo | Sì | — | Path locale. File locale da caricare. Es. `output/doc.pdf` |
| `remotePath` | testo | Sì | — | Path remoto. Es. `/Esiti/output.pdf` |
| `conflict` | scelta — replace · rename · fail | — | replace | Strategia sui conflitti di nome. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastUploadedFileId` | testo | ID file caricato. |
| `lastUploadedFileUrl` | testo | URL file. |

- **Riferimenti incrociati:** SharePoint Download / SharePoint List (stessa credenziale M365).

---

### Word Extract — DSL `WordExtract` ✅ CONFERMATO  `L2355`

DSL `WordExtract` (confermato, osservato in F4:61).

- **Scopo:** Estrae il testo da documenti Word (`.docx`/`.doc`), OpenOffice Writer (`.odt`) e RTF. I Google Doc arrivano via Drive Download (export automatico).
- **Quando usarlo:** Usa questo blocco per estrarre il testo (completo e per paragrafi) da un documento Word (`.docx`/`.doc`), OpenOffice Writer (`.odt`) o RTF. I placeholder `{chiave}` nel path vengono risolti. Per i Google Doc nativi scaricali prima con Drive Download (export automatico in `.docx`).
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `filePath` | testo | Sì | — | Path documento. Documento Word (`.docx`/`.doc`), OpenOffice Writer (`.odt`) o RTF. Placeholder `{chiave}` risolti. I Google Doc nativi vanno prima scaricati con Drive Download (export automatico in `.docx`). Es. `input/ordine.docx` |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastWordText` | testo | Testo completo del documento. |
| `lastWordParagraphs` | JSON | Paragrafi `{ index, text, charCount }` (vuoti esclusi). |

- **⚠️ Avvertenze / vincoli:**
  - I Google Doc nativi vanno prima scaricati con Drive Download (export automatico in `.docx`).
- **Riferimenti incrociati:** Drive Download (fornisce il `.docx` esportato dai Google Doc); `{lastWordText}` (esempio di testo da indicizzare in Indicizza conoscenza RAG).

---

### Xlsx Extract — DSL `XlsxExtract` ✅ CONFERMATO  `L2369`

DSL `XlsxExtract` (confermato, osservato in F4:77).

- **Scopo:** Estrae dati da un file Excel.
- **Quando usarlo:** Usa questo blocco per estrarre le righe di dati da un file Excel (`.xlsx`/`.xlsm`) o da `.ods` (OpenOffice/LibreOffice Calc) e `.xls` legacy. Indica il foglio (default: primo foglio; `*` = tutti i fogli, con `__sheet` su ogni riga), la riga di header e se il foglio ha intestazioni.
- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `filePath` | testo | Sì | — | Path Excel. File `.xlsx`/`.xlsm`, oppure `.ods` (OpenOffice/LibreOffice Calc) e `.xls` legacy. Es. `input/ordini.xlsx` |
| `sheet` | testo | — | — | Foglio. Default: primo foglio. `*` = tutti i fogli (ogni riga ha `__sheet`). |
| `headerRow` | intero | — | 1 | Riga header. |
| `hasHeaders` | sì/no | — | true | Ha intestazioni. |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastXlsxRows` | JSON | Righe estratte. |

- **⚠️ Avvertenze / vincoli:**
  - `sheet`: `*` = tutti i fogli (ogni riga ha la colonna `__sheet`).
- **Riferimenti incrociati:** Excel Online Read (equivalente su OneDrive/SharePoint, non su file locale — inferenza).
