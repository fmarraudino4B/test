# Archetipi di flusso — scegli, componi, adatta

> Ogni richiesta nuova ricade (quasi sempre) in uno di questi archetipi. Per ciascuno: quando si
> applica, flusso di riferimento, **ricetta di moduli** (`moduli.md`) e decisioni da prendere
> con l'utente. Componi i moduli nell'ordine indicato e scrivi a mano solo la logica di business.

## Albero di scelta rapido
```
Da dove arriva il lavoro?
├─ File in una cartella ───────────── documento → ERP?
│    ├─ ordine cliente / doc. vendita ─────────────────► A1
│    ├─ DDT/fattura fornitore da riconciliare ─────────► A2
│    └─ altro documento (solo estrazione/notifica) ────► A4
├─ Casella email ──────────────────────────────────────► A3 (+ ricetta A1/A2 sugli allegati)
├─ Webhook / Form / Telegram / Slack (domanda-risposta) ► A5
├─ Nuove righe DB (EventDb) o orario (Schedule) ───────► A6
├─ Fallimento di un altro agente (ErrorTrigger) ───────► A7
├─ Verifica / riconciliazione SENZA scrivere sull'ERP ───► A8
├─ Caricamento su tabelle di staging / frontiera ────────► A9
└─ Processo con più agenti in sequenza ──────────────────► A10
Livello: senza supervisione, volumi alti o audit → aggiungi il "pacchetto produzione" (P).
```

**Pacchetto produzione (P)** = M00 config + M01 preflight + M02 orfani + M05 claim +
pannello Gestione errori del ForEach + M11 idempotente + M14 audit + M15 heartbeat.

---

## A1 — Documento di vendita PDF → ERP (ordine cliente)
- **Riferimento:** CLI-A-OC 1.5.7A (produzione), F1 (estrazione), prompt `prompt-ordini/template-*.md`.
- **Ricetta:** M00 → [P: M01, M02] → M03 → { M04 → [P: M05] → classificazione (opzionale) →
  M06 → M07 → M08 → M09 → M10 → M11 → M12 → M14 → M13 → M15 } → [P: heartbeat].
- **Decisioni:** trigger (cartella / mail / schedulato); soglia % (`minPercentualeRisoltePerCreare`);
  causale/serie/deposito (profilo per cliente o default); prezzi forzati o ricalcolati dall'ERP
  (`FLAG_CALC_PRZ`); auto-learning sì/no; destinatari notifiche.
- **Variante prompt (linguaggio naturale per il builder AI di WorkForce):** genera dal template
  `prompt-ordini/` scelto (`template-avanzato.md` se serve il livello P), sostituendo i `{{…}}`.

## A2 — Documento fornitore PDF → ERP con riconciliazione (DDT/fattura)
- **Riferimento:** CLI-B-DDT (blocchi + split), CLI-B-FATT, F2, CLI-F (conto lavoro).
- **Documenti lunghi:** M18 a blocchi, M20 per lo split; retry disabilitato su `documento`.
- **Ricetta:** come A1 con `endpoint: "fornitori"` in M08 e, dopo M09, uno stadio di
  **aggancio riga d'ordine** (residuo `> 0`, risultato univoco) + **controllo prezzi**
  bolla↔ordine (`priceAlertsJson`, solo segnalazione).
- **Specifiche CLI-B da non dimenticare:** righe di riferimento ordine su riga separata da
  propagare e rimuovere; EAN come codice alternativo; P.IVA estera (`VAT NO.`, `UID`); testi di
  esito troncati prima dell'`SqlUpdate`.

## A3 — Intake email → (classifica) → A1/A2 sugli allegati
- **Riferimento:** F4 (solo per lo Switch sugli allegati), M16 (contratto corretto).
- **Ricetta:** trigger MailPolling durevole → classificazione (`ClassifyText` o `AiAnalysis`
  `text`) → `for` su `lastEmailAttachments` con `switch` sull'estensione (`PdfExtract`,
  `WordExtract`, `XlsxExtract`, `OcrImage`) → ricetta A1/A2 → **un** `MailDisposition` finale.
- **Decisioni:** cartelle IMAP (Elaborate / Revisione); risposta al mittente sì/no; allegati
  non supportati → `review`.

## A4 — Estrazione documentale + notifica (senza ERP)
- **Riferimento:** esempio minimale (`dsl/esempi.md` §5), `assets/template-flusso.js`.
- **Ricetta:** M03 → { M04 → M06 → esito deterministico in `CodeJs` → M13 } (+ `GenerateReport`,
  `GoogleSheetsAppend`/`ExcelOnlineAppend`/`SqlInsert` se serve persistere).

## A5 — Conversazionale / webhook (domanda → risposta)
- **Blocchi:** trigger Webhook/Form, `InboundParse` (Telegram/Twilio/Slack), `RagSearch` →
  `AiAnalysis` con `{lastRagContext}` (A2 pattern) oppure `SecureChatQuery` (perimetro utente),
  risposta con `SendTelegram`/`SendSlack`/`SendWhatsApp` o `WebhookRespond` (sincrono).
- **Decisioni:** identità run-as e `chatId`; isolamento conversazioni (`userKey`); risposta
  sincrona vs asincrona. ⚠️ Nessun flusso reale di questo tipo in catalogo: marca le inferenze.

## A6 — Batch su dati (EventDb / Schedule), arricchimento e reportistica
- **Riferimento:** CLI-A-CC (dashboard HTML: Query → 8 blocchi dati → CodeJs insight → AiAnalysis
  narrativo **solo su dati aggregati** → HTML → `PublishDashboard` + email), CLI-C-F5
  (aggiornamento date consegna via `SqlUpdate`), LEAD (hash per saltare l'invariato, AI web,
  `SqlUpdate` mirato, limite per run).
- **Blocchi:** trigger EventDb (`lastEventRows`) o Schedule + `Query`; trasformazioni con
  `Filter`/`Sort`/`Aggregate`/`RemoveDuplicates` o `CodeJs`; output `GenerateReport`,
  `PublishDashboard`, `SqlUpdate` di stato (marcatura righe lavorate per non riprenderle).
- **Regola:** marca le righe elaborate (STATO) con `SqlUpdate` idempotente; R9 sui tipi.

## A7 — Supervisione (ErrorTrigger) e human-in-the-loop
- **Blocchi:** trigger ErrorTrigger (`failedAgentName`, `errorMessage`) → notifica;
  `SendAndWait` per approvazioni a metà flusso (timeout + `continueWithDefault`).
- **Uso tipico:** affiancare ad A1/A2 in produzione un agente che avvisa sui fallimenti, e
  `SendAndWait` al posto della revisione via cartella quando l'operatore risponde da mobile.

## A8 — Verifica / riconciliazione in sola lettura
- **Riferimento:** CLI-A-MW (PortaleXML XML ↔ DDT ↔ ordini), CLI-A-FV (fattura fornitore, 7 controlli).
- **Ricetta:** M00 → M01 (anche schema) → acquisizione (XML deterministico o M06 su PDF) →
  controlli SQL deterministici con M17 → **una** AI solo dove serve giudizio (es. catena DDT/ordini,
  output JSON) → step verdetto (COMPLETA / PARZIALE / NON POSSIBILE, declassamento automatico con
  anomalie bloccanti) → report markdown via email, oppure M19 per la conferma operatore →
  rilettura post-inserimento.
- **Vincolo:** solo `SELECT`/`WITH`; tolleranze esplicite in configurazione; mai fidarsi di un
  codice proposto senza verifica in anagrafica. Due modalità utili: `PREPARAZIONE` e
  `VERIFICA_A_POSTERIORI`.

## A9 — Caricamento su tabelle di staging / frontiera
- **Riferimento:** CLI-D-STAGING.
- **Ricetta:** M01 (config, ERP, schema staging) → polling cartella → M06 → normalizzazione
  (tipo documento, valuta, IVA) → `SqlInsert` in ordine di dipendenza (righe → IVA → pagamenti →
  testata) con idempotenza per documento → archiviazione PDF → audit → email.
- **Decisioni:** significato degli stati della staging, chi la consuma, gestione cambio valuta.

## A10 — Pipeline multi-agente (EventDb)
- **Riferimento:** piano CLI-E (12 agenti, 3 ondate con decision gate).
- **Ricetta:** modello dati canonico; ogni agente esegue una fase e scrive lo stato in una tabella
  stato/audit; l'agente successivo parte con trigger EventDb su quella tabella; regole di business
  in tabella di configurazione (riuso multi-cliente); adapter separati per formato (XML
  deterministico vs PDF con AI).
- **Prima di partire:** mappa dei limiti API (cosa non ha endpoint) e decisione sulle scritture SQL
  dirette.

---

## Proposte evolutive (da offrire all'utente quando pertinenti)
- **Sub-workflow condivisi:** estrarre M08 (anagrafica) e M09 (cascata articoli) in un
  `SubWorkflow` riusato da A1 e A2, così un fix vale per tutti i flussi (`lastSubWorkflowStatus`).
- **Agente sentinella:** un A7 unico per tutti gli agenti del cliente + lettura dell'heartbeat.
- **Dashboard anomalie:** `PublishDashboard` sulle tabelle di audit (`MATCH_METHOD`, `CONFIDENCE`,
  esiti) per misurare il tasso di automazione nel tempo.
- **Revisione da mobile:** `SendAndWait` sulle righe sotto soglia invece della cartella REVIEW.
