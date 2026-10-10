# Mappa nomi: DISPLAY (manuale) → DSL (Modalità Sviluppatore)

> **Riferimento autorevole dei nomi-funzione.** Il manuale usa etichette umane (es. "Write File"); il codice DSL usa identificatori engine (es. `FileWrite`). Chi cerca il nome DSL nel manuale spesso non lo trova. Questo file è l'UNICA fonte dei nomi. I nomi dei **parametri**, invece, coincidono col manuale (nessuna divergenza osservata).
>
> **Tutti i 63 nomi sono ora CONFERMATI.** Il *Video corso ThinkAI WorkForce Studio* (cartella `video-corso/`, moduli 9–17 "Le palette in dettaglio") mostra 62 palette con il proprio identificatore-tipo nelle immagini (`media/palette/node-<Tipo>.png`, `campi-<Tipo>.png`) e nella narrazione; il 63° blocco, **Mail Disposition** (`MailDisposition`), è documentato dalla sola narrazione del modulo 15 (senza immagine palette). Questi identificatori-tipo **coincidono al 100%** con i 15 nomi-funzione già osservati nei flussi esportati (inclusi i 5 irregolari: `Query`, `FileWrite`, `FileMove`, `ExtractStructured`, `GestionaleSend`), quindi il nome-tipo palette = il nome-funzione DSL.
>
> Legenda affidabilità:
> - **✅ CONFERMATO (flusso)** = nome-funzione osservato in un flusso DSL esportato (`Fx:riga`). Prova più forte: attesta anche la *forma di chiamata* `Nome({...})`.
> - **✅ CONFERMATO (corso)** = nome-tipo palette confermato dal video-corso (`node-<Tipo>`/`campi-<Tipo>` + narrazione, modulo indicato). La forma di chiamata `Nome({...})` segue la convenzione verificata sui 15 osservati in flusso (rischio residuo trascurabile).

## Indice
1. Come usare questa mappa
2. Tabella completa dei 63 nomi (per categoria)
3. Convenzione di naming e trappole
4. Costrutti di controllo (non sono funzioni)
5. Correzioni rispetto alla versione precedente

---

## 1. Come usare questa mappa
Per ogni step che generi:
1. Scegli il blocco per scopo (vedi `blocchi/_indice.md`).
2. Cerca qui il suo **nome DSL** e usalo così: tutti sono confermati.
3. I parametri (chiavi dentro `{ ... }`) prendili sempre dalla scheda del blocco nel catalogo (coincidono col manuale).
4. I 5 nomi **irregolari** (§3) non sono deducibili "a naso": leggili sempre da qui.

---

## 2. Tabella completa dei 63 nomi (per categoria)

> Colonna **Regolare?** = segue l'euristica "spazi rimossi + PascalCase inglese" (§3). Colonna **Evidenza**: `Fx:riga` = flusso esportato; `corso Mn` = modulo del video corso in cui la palette è documentata (`node-`/`campi-<Tipo>`).

### Script (2)
| DISPLAY | DSL | Regolare? | Evidenza |
|---|---|---|---|
| Code JS | `CodeJs` | ✅ sì | flusso F1:13 |
| Code Python | `CodePython` | ✅ sì | corso M9 (`node-CodePython`) |

### AI (6)
| DISPLAY | DSL | Regolare? | Evidenza |
|---|---|---|---|
| AI Analysis | `AiAnalysis` | ✅ sì | flusso F1:47 |
| Cerca nella conoscenza (RAG) | `RagSearch` | ✅ sì | corso M10 (`node-RagSearch`) |
| Classifica testo (AI) | `ClassifyText` | ✅ sì | corso M10 (`node-ClassifyText`) |
| Estrai dati (AI) | `ExtractStructured` | ⚠️ NO — display IT tradotto/rinominato | flusso F4:114 |
| Indicizza conoscenza (RAG) | `RagEmbed` | ⚠️ NO — display IT, "Embed" non "Index" | corso M10 (`node-RagEmbed`) |
| Report PDF/DOCX/XLSX | `GenerateReport` | ⚠️ NO — display IT rinominato | corso M10 (`node-GenerateReport`) |

### Dati (16)
| DISPLAY | DSL | Regolare? | Evidenza |
|---|---|---|---|
| Chiedi alla Chat (sicuro) | `SecureChatQuery` | ⚠️ NO — display IT rinominato | corso M11 (`node-SecureChatQuery`) |
| Delete File | `FileDelete` | ⚠️ NO — ordine invertito (nome+verbo) | corso M11 (`node-FileDelete`) |
| Excel Online Append | `ExcelOnlineAppend` | ✅ sì | corso M11 (`node-ExcelOnlineAppend`) |
| Excel Online Read | `ExcelOnlineRead` | ✅ sì | corso M11 (`node-ExcelOnlineRead`) |
| File List | `FileList` | ✅ sì | flusso F1:7 |
| Insert SQL | `SqlInsert` | ⚠️ NO — ordine invertito (`Sql`+verbo) | corso M11 (`node-SqlInsert`) |
| JSON a file | `JsonToFile` | ⚠️ NO — display IT misto | corso M11 (`node-JsonToFile`) |
| JSON da file | `JsonFromFile` | ⚠️ NO — display IT misto | corso M11 (`node-JsonFromFile`) |
| JSON Parse | `JsonParse` | ✅ sì | corso M11 (`node-JsonParse`) |
| Move File | `FileMove` | ⚠️ NO — ordine invertito (nome+verbo) | flusso F2:261 |
| Query SQL | `Query` | ⚠️ NO — suffisso "SQL" caduto | flusso F2:82 |
| Read File | `FileRead` | ⚠️ NO — ordine invertito (nome+verbo) | corso M11 (`node-FileRead`) |
| Sheets Append | `GoogleSheetsAppend` | ⚠️ NO — prefisso "Google" (display "Sheets") | corso M11 (`node-GoogleSheetsAppend`) |
| Sheets Read | `GoogleSheetsRead` | ⚠️ NO — prefisso "Google" (display "Sheets") | corso M11 (`node-GoogleSheetsRead`) |
| Update SQL | `SqlUpdate` | ⚠️ NO — ordine invertito (`Sql`+verbo) | corso M11 (`node-SqlUpdate`) |
| Write File | `FileWrite` | ⚠️ NO — ordine invertito (nome+verbo) | flusso F1:661 |

### Documenti (10)
| DISPLAY | DSL | Regolare? | Evidenza |
|---|---|---|---|
| Drive Download | `GoogleDriveDownload` | ⚠️ NO — prefisso "Google" (display "Drive") | corso M12 (`node-GoogleDriveDownload`) |
| Drive List | `GoogleDriveList` | ⚠️ NO — prefisso "Google" (display "Drive") | corso M12 (`node-GoogleDriveList`) |
| Drive Upload | `GoogleDriveUpload` | ⚠️ NO — prefisso "Google" (display "Drive") | corso M12 (`node-GoogleDriveUpload`) |
| OCR Image | `OcrImage` | ✅ sì | corso M12 (`node-OcrImage`) |
| PDF Extract | `PdfExtract` | ✅ sì | flusso F4:53 |
| SharePoint Download | `SharePointDownload` | ✅ sì | corso M12 (`node-SharePointDownload`) |
| SharePoint List | `SharePointList` | ✅ sì | corso M12 (`node-SharePointList`) |
| SharePoint Upload | `SharePointUpload` | ✅ sì | corso M12 (`node-SharePointUpload`) |
| Word Extract | `WordExtract` | ✅ sì | flusso F4:61 |
| Xlsx Extract | `XlsxExtract` | ✅ sì | flusso F4:77 |

### Flusso (16) — 4 sono costrutti di controllo (vedi §4)
| DISPLAY | DSL | Regolare? | Evidenza |
|---|---|---|---|
| Aggregate | `Aggregate` | ✅ sì | corso M13 (`node-Aggregate`) |
| Branch (IF) | costrutto → `if/else` (tipo `Branch`) | — | flusso F1:612 / corso M13 |
| Filter | `Filter` | ✅ sì | corso M13 (`node-Filter`) |
| ForEach | costrutto → `for…of` (tipo `ForEach`) | — | flusso F1:9 / corso M13 |
| Inbound Parse | `InboundParse` | ✅ sì | corso M13 (`node-InboundParse`) |
| Limit | `Limit` | ✅ sì | corso M13 (`node-Limit`) |
| Merge | `Merge` | ✅ sì | corso M13 (`node-Merge`) |
| Remove Duplicates | `RemoveDuplicates` | ✅ sì | corso M13 (`node-RemoveDuplicates`) |
| Rename Keys | `RenameKeys` | ✅ sì | corso M13 (`node-RenameKeys`) |
| Set Fields | `SetFields` | ✅ sì | flusso F1:664 |
| Sort | `Sort` | ✅ sì | corso M13 (`node-Sort`) |
| Stop & Error | costrutto → `throw new Error()` (tipo `StopAndError`) | — | flusso F1:666 / corso M13 |
| Sub-Workflow | `SubWorkflow` | ✅ sì | corso M13 (`node-SubWorkflow`) |
| Switch | costrutto → `switch/case` (tipo `Switch`) | — | flusso F4:49 / corso M13 |
| Wait | `Wait` | ✅ sì | corso M13 (`node-Wait`) |
| Webhook Respond | `WebhookRespond` | ✅ sì | corso M13 (`node-WebhookRespond`) |

### Integrazioni (2)
| DISPLAY | DSL | Regolare? | Evidenza |
|---|---|---|---|
| HTTP Call | `HttpCall` | ✅ sì | corso M14 (`node-HttpCall`) |
| TargetCross / TaylorGest | `GestionaleSend` | ⚠️ NO — rinomina totale (brand→generico) | flusso F1:5 |

### Mail (3)
| DISPLAY | DSL | Regolare? | Evidenza |
|---|---|---|---|
| Mail Read | `MailRead` | ✅ sì | flusso F4:3 |
| Mail Disposition | `MailDisposition` | ✅ sì | corso M15 (narrazione, senza immagine palette) |
| Telegram Read | `TelegramRead` | ✅ sì | corso M15 (`node-TelegramRead`) |

### Notifiche (6)
| DISPLAY | DSL | Regolare? | Evidenza |
|---|---|---|---|
| Email | `SendEmail` | ⚠️ NO — verbo "Send" anteposto | flusso F1:711 |
| Invia e attendi | `SendAndWait` | ⚠️ NO — display IT rinominato | corso M16 (`node-SendAndWait`) |
| Slack | `SendSlack` | ⚠️ NO — verbo "Send" anteposto | corso M16 (`node-SendSlack`) |
| Teams | `SendTeams` | ⚠️ NO — verbo "Send" anteposto | corso M16 (`node-SendTeams`) |
| Telegram | `SendTelegram` | ⚠️ NO — verbo "Send" anteposto | corso M16 (`node-SendTelegram`) |
| WhatsApp | `SendWhatsApp` | ⚠️ NO — verbo "Send" anteposto | corso M16 (`node-SendWhatsApp`) |

### Output (2)
| DISPLAY | DSL | Regolare? | Evidenza |
|---|---|---|---|
| Markdown | `Markdown` | ✅ sì | flusso F1:708 |
| Publish Dashboard | `PublishDashboard` | ✅ sì | corso M17 (`node-PublishDashboard`) |

---

## 3. Convenzione di naming e trappole
**Euristica sui regolari:** rimuovi gli spazi e usa PascalCase mantenendo le parole inglesi (`File List`→`FileList`, `AI Analysis`→`AiAnalysis`, `Mail Read`→`MailRead`).

**Le 5 famiglie irregolari CONFERMATE (memorizzale — non deducibili a naso):**
- **Verbo↔nome invertito** per i file: `Write File`→`FileWrite`, `Move File`→`FileMove`, `Read File`→`FileRead`, `Delete File`→`FileDelete`.
- **Prefisso di dominio** anteposto: `Sheets Read/Append`→`GoogleSheetsRead`/`GoogleSheetsAppend`; `Drive …`→`GoogleDrive…`. Il display nasconde il "Google". (`Excel Online …`→`ExcelOnlineRead`/`ExcelOnlineAppend`, coerente col display.)
- **Verbo/prefisso `Sql`** per le scritture SQL: `Insert SQL`→`SqlInsert`, `Update SQL`→`SqlUpdate`; mentre `Query SQL`→`Query` (suffisso caduto).
- **Verbo "Send" anteposto** all'invio: `Email`→`SendEmail`, `Slack`→`SendSlack`, `Teams`→`SendTeams`, `Telegram`→`SendTelegram`, `WhatsApp`→`SendWhatsApp`.
- **Rinomina totale / traduzione** dei display italiani: `Estrai dati (AI)`→`ExtractStructured`, `Indicizza conoscenza (RAG)`→`RagEmbed`, `Report …`→`GenerateReport`, `Chiedi alla Chat (sicuro)`→`SecureChatQuery`, `Invia e attendi`→`SendAndWait`, `TargetCross / TaylorGest`→`GestionaleSend`. (`Cerca nella conoscenza (RAG)`→`RagSearch` e `Classifica testo (AI)`→`ClassifyText` sono invece regolari nonostante il display IT.)

---

## 4. Costrutti di controllo (proiettati come JS, NON funzioni)
Vedi `sintassi-dsl.md` per sintassi completa ed esempi. I 4 costrutti hanno anche un **tipo-blocco** (utile per palette/manuale) ma nel DSL si proiettano come JavaScript, non come chiamata `Nome({...})`.

| DISPLAY | Tipo-blocco | Proiezione DSL | Evidenza |
|---|---|---|---|
| ForEach | `ForEach` | `for (const item of <chiave>) { … }` (+ `// @foreach maxIterations=N`) | flusso F1:9, F4:6 |
| Branch (IF) | `Branch` | `if (<$.cond>) { … } else { … }` | flusso F1:612 |
| Switch | `Switch` | `switch (<$.expr>) { case "x": { … } default: { … } }` | flusso F4:49 |
| Stop & Error | `StopAndError` | `throw new Error("<messaggio>")` | flusso F1:666 |
| onError (concetto) | — | `try { … } catch { … }` | flusso F2:4 |

⚠️ `Sub-Workflow` (`SubWorkflow`) e `Wait` (`Wait`) NON sono costrutti: sono blocchi-funzione con contenitore/pausa. Si scrivono come chiamata `SubWorkflow({...})` / `Wait({...})`.

---

## 5. Correzioni rispetto alla versione precedente
La versione precedente marcava 43 nomi come `⚠️ DA VERIFICARE` (ipotesi per convenzione). Il video corso li ha **tutti confermati**. Nove ipotesi erano **sbagliate** — usarle avrebbe prodotto flussi invalidi:

| DISPLAY | Ipotesi vecchia (errata) | Nome reale (corso) |
|---|---|---|
| Chiedi alla Chat (sicuro) | `AskChat` / `ChatQuery` | `SecureChatQuery` |
| Insert SQL | `Insert` / `InsertSql` | `SqlInsert` |
| Update SQL | `Update` / `UpdateSql` | `SqlUpdate` |
| Sheets Read | `SheetsRead` | `GoogleSheetsRead` |
| Sheets Append | `SheetsAppend` | `GoogleSheetsAppend` |
| Drive Download | `DriveDownload` | `GoogleDriveDownload` |
| Drive List | `DriveList` | `GoogleDriveList` |
| Drive Upload | `DriveUpload` | `GoogleDriveUpload` |
| Indicizza conoscenza (RAG) | `RagIndex` / `KnowledgeIndex` | `RagEmbed` |

**Blocco aggiunto (62 → 63):** una revisione contro il video corso (SSOT) ha rilevato che **Mail Disposition** (`MailDisposition`, categoria Mail, modulo 15) era **assente** dal catalogo. È stato aggiunto: è la chiusura obbligatoria (un solo step top-level finale) dei worker alimentati dal trigger MailPolling durevole. Vedi `blocchi/comunicazione.md`.

---

## 6. Appendice — mappa `Type` numerico (solo per leggere export `.thinkaiagent.json`, NON per il DSL)

⚠️ **Questa mappa serve solo se ricevi un agente esportato come JSON** (es.
per adattarlo a un nuovo cliente) e devi capire cosa fa ogni step senza avere
la vista DSL. **Non usarla per scrivere/generare DSL**: nel DSL si scrive
sempre il nome-funzione (`GestionaleSend({...})`), mai un numero. Il campo
`Type` è un intero interno del formato di export `thinkai.workforce.agent`
(non il DSL "Modalità Sviluppatore").

Ricostruita per osservazione diretta su un solo export reale (**GAZZA Ordine
Cliente v1.4.1**, formato `thinkai.workforce.agent 1.0`): copre solo i valori
di `Type` effettivamente incontrati in quel file, **non tutti i 63 blocchi**.
Non estrapolare valori mancanti per analogia.

| `Type` | Blocco DSL corrispondente | Evidenza |
|---|---|---|
| 1 | `Query` (Query SQL) | `GAZZA:#5` |
| 2 | `AiAnalysis` / `ExtractStructured` (schema step estrazione AI) | osservato nei sub-step del `GAZZA:#9` |
| 4 | `SendEmail` | `GAZZA:#9→itemErrorSteps#4` |
| 8 | `Branch` (if/else) | `GAZZA:#3`, `#7` |
| 10 | `FileRead` | `GAZZA:#9→subSteps` |
| 11 | `FileWrite` | `GAZZA:#11` |
| 15 | `ForEach` | `GAZZA:#9` |
| 17 | `FileList` | `GAZZA:#8` |
| 18 | `SetFields` | `GAZZA:#1` |
| 22 | `StopAndError` (Stop & Error) | `GAZZA:#3→elseSteps#1` |
| 23 | `CodeJs` | `GAZZA:#2` |
| 28 | `GestionaleSend` | `GAZZA:#4` |
| 37 | `FileMove` | `GAZZA:#9→itemErrorSteps#5` |
| 62 | `SqlInsert` | `GAZZA:#9→itemErrorSteps#2` |
| 63 | `SqlUpdate` | `GAZZA:#9→itemErrorSteps#3` |

⚠️ **NON DOCUMENTATO** oltre questa tabella: i `Type` dei restanti ~48 blocchi
del catalogo non sono stati osservati in nessun export e non vanno indovinati.
