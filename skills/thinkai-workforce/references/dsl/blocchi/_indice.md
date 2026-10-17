# Indice catalogo blocchi (63)

> Elenco completo dei 63 blocchi documentati, raggruppati per categoria. Usa questa tabella per **trovare il blocco per scopo**, leggerne il **nome DSL** (Modalità Sviluppatore) e sapere in **quale file di catalogo** sta la scheda di dettaglio (parametri, output, esempi).
>
> Flusso di lavoro consigliato: (1) scegli il blocco qui per categoria/scopo; (2) apri il file di catalogo indicato in colonna **File** e leggi la scheda completa; (3) per il nome DSL vedi anche `../nomi-blocchi.md` (fonte autorevole dei nomi).
>
> **Legenda affidabilità nome DSL:** **tutti i 63 nomi sono ✅ CONFERMATI** — 15 osservati nei flussi esportati, gli altri confermati dal *video corso* (palette dei moduli 9–17: `node-<Tipo>`/`campi-<Tipo>` + narrazione). 62 hanno un'immagine palette (`node-`/`campi-`); **Mail Disposition** è confermato dalla sola narrazione del modulo 15 (senza immagine). Fonte autorevole dei nomi: `../nomi-blocchi.md`.
>
> Colonna **Rif** = riga HTML del manuale (`L####`). Colonne **#param / #out** = numero di parametri e di output della scheda.
>
> **Costrutti di controllo** (Branch, ForEach, Switch, Stop & Error): NON sono funzioni DSL ma proiezioni JavaScript (colonna Nome DSL = proiezione confermata, vedi `../sintassi-dsl.md`).

## Catalogo

| Blocco (display) | Rif | Categoria | Nome DSL | #param | #out | File |
|---|---|---|---|---|---|---|
| AI Analysis | L1481 | AI | `AiAnalysis` | 15 | 2 | ai.md |
| Cerca nella conoscenza (RAG) | L1551 | AI | `RagSearch` | 4 | 3 | ai.md |
| Classifica testo (AI) | L1579 | AI | `ClassifyText` | 5 | 5 | ai.md |
| Estrai dati (AI) | L1615 | AI | `ExtractStructured` | 6 | 2 | ai.md |
| Indicizza conoscenza (RAG) | L1649 | AI | `RagEmbed` | 6 | 3 | ai.md |
| Report PDF/DOCX/XLSX | L1685 | AI | `GenerateReport` | 7 | 4 | ai.md |
| Chiedi alla Chat (sicuro) | L1727 | Dati | `SecureChatQuery` | 5 | 1 | dati.md |
| Delete File | L1755 | Dati | `FileDelete` | 2 | 1 | dati.md |
| Excel Online Append | L1771 | Dati | `ExcelOnlineAppend` | 10 | 2 | dati.md |
| Excel Online Read | L1821 | Dati | `ExcelOnlineRead` | 6 | 2 | dati.md |
| File List | L1855 | Dati | `FileList` | 3 | 1 | dati.md |
| Insert SQL | L1875 | Dati | `SqlInsert` | 4 | 2 | dati.md |
| JSON a file | L1901 | Dati | `JsonToFile` | 5 | 1 | dati.md |
| JSON da file | L1929 | Dati | `JsonFromFile` | 3 | 2 | dati.md |
| JSON Parse | L1951 | Dati | `JsonParse` | 3 | 1 | dati.md |
| Move File | L1971 | Dati | `FileMove` | 4 | 2 | dati.md |
| Query SQL | L1997 | Dati | `Query` | 3 | 3 | dati.md |
| Read File | L2021 | Dati | `FileRead` | 2 | 3 | dati.md |
| Sheets Append | L2041 | Dati | `GoogleSheetsAppend` | 7 | 2 | dati.md |
| Sheets Read | L2079 | Dati | `GoogleSheetsRead` | 4 | 2 | dati.md |
| Update SQL | L2105 | Dati | `SqlUpdate` | 5 | 2 | dati.md |
| Write File | L2135 | Dati | `FileWrite` | 4 | 2 | dati.md |
| Drive Download | L2161 | Documenti | `GoogleDriveDownload` | 3 | 1 | documenti.md |
| Drive List | L2181 | Documenti | `GoogleDriveList` | 4 | 1 | documenti.md |
| Drive Upload | L2205 | Documenti | `GoogleDriveUpload` | 6 | 1 | documenti.md |
| OCR Image | L2237 | Documenti | `OcrImage` | 2 | 2 | documenti.md |
| PDF Extract | L2255 | Documenti | `PdfExtract` | 3 | 2 | documenti.md |
| SharePoint Download | L2277 | Documenti | `SharePointDownload` | 4 | 1 | documenti.md |
| SharePoint List | L2301 | Documenti | `SharePointList` | 4 | 1 | documenti.md |
| SharePoint Upload | L2325 | Documenti | `SharePointUpload` | 5 | 2 | documenti.md |
| Word Extract | L2355 | Documenti | `WordExtract` | 1 | 2 | documenti.md |
| Xlsx Extract | L2369 | Documenti | `XlsxExtract` | 4 | 1 | documenti.md |
| Aggregate | L2393 | Flusso | `Aggregate` | 4 | 1 | flusso.md |
| Branch (IF) | L2417 | Flusso | `if/else` (costrutto, tipo `Branch`) | 1 | 0 | flusso.md |
| Filter | L2426 | Flusso | `Filter` | 3 | 1 | flusso.md |
| ForEach | L2446 | Flusso | `for…of` (costrutto, tipo `ForEach`) | 5 | 0 | flusso.md |
| Inbound Parse | L2471 | Flusso | `InboundParse` | 2 | 6 | flusso.md |
| Limit | L2497 | Flusso | `Limit` | 4 | 1 | flusso.md |
| Merge | L2521 | Flusso | `Merge` | 4 | 1 | flusso.md |
| Remove Duplicates | L2545 | Flusso | `RemoveDuplicates` | 3 | 1 | flusso.md |
| Rename Keys | L2565 | Flusso | `RenameKeys` | 3 | 1 | flusso.md |
| Set Fields | L2585 | Flusso | `SetFields` | 1 | 1 | flusso.md |
| Sort | L2597 | Flusso | `Sort` | 4 | 1 | flusso.md |
| Stop & Error | L2621 | Flusso | `throw new Error()` (costrutto, tipo `StopAndError`) | 2 | 0 | flusso.md |
| Sub-Workflow | L2633 | Flusso | `SubWorkflow` | 3 | 3 | flusso.md |
| Switch | L2658 | Flusso | `switch/case` (costrutto, tipo `Switch`) | 1 | 0 | flusso.md |
| Wait | L2667 | Flusso | `Wait` | 6 | 5 | flusso.md |
| Webhook Respond | L2707 | Flusso | `WebhookRespond` | 4 | 4 | flusso.md |
| HTTP Call | L2737 | Integrazioni | `HttpCall` | 15 | 2 | integrazioni.md |
| TargetCross / TaylorGest | L2807 | Integrazioni | `GestionaleSend` | 19 | 8 | integrazioni.md |
| Mail Read | L2905 | Mail | `MailRead` | 13 | 2 | comunicazione.md |
| Mail Disposition | corso M15 | Mail | `MailDisposition` | 6 | 2 | comunicazione.md |
| Telegram Read | L2967 | Mail | `TelegramRead` | 4 | 2 | comunicazione.md |
| Email | L2993 | Notifiche | `SendEmail` | 6 | 0 | comunicazione.md |
| Invia e attendi | L3021 | Notifiche | `SendAndWait` | 16 | 5 | comunicazione.md |
| Slack | L3101 | Notifiche | `SendSlack` | 2 | 1 | comunicazione.md |
| Teams | L3117 | Notifiche | `SendTeams` | 3 | 1 | comunicazione.md |
| Telegram | L3137 | Notifiche | `SendTelegram` | 6 | 1 | comunicazione.md |
| WhatsApp | L3169 | Notifiche | `SendWhatsApp` | 8 | 1 | comunicazione.md |
| Markdown | L3209 | Output | `Markdown` | 3 | 5 | output-script.md |
| Publish Dashboard | L3237 | Output | `PublishDashboard` | 3 | 1 | output-script.md |
| Code JS | L3257 | Script | `CodeJs` | 7 | 2 | output-script.md |
| Code Python | L3295 | Script | `CodePython` | 6 | 2 | output-script.md |

## Legenda categorie → file di catalogo

| Categoria (digest) | File | Blocchi |
|---|---|---|
| AI | `ai.md` | 6 |
| Dati | `dati.md` | 16 |
| Documenti | `documenti.md` | 10 |
| Flusso | `flusso.md` | 16 |
| Integrazioni (HTTP Call, TargetCross/TaylorGest) | `integrazioni.md` | 2 |
| Comunicazione — Mail (Mail Read, Mail Disposition, Telegram Read) + Notifiche (Email, Invia e attendi, Slack, Teams, Telegram, WhatsApp) | `comunicazione.md` | 9 |
| Output (Markdown, Publish Dashboard) + Script (Code JS, Code Python) | `output-script.md` | 4 |

**Totale: 63 blocchi.**
