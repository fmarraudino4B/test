# Esempi end-to-end — flussi ThinkAI WorkForce Studio

> **Cosa fa questo file.** Presenta i 4 flussi reali esportati (F1–F4) come esempi di riferimento, poi un flusso NUOVO corretto e minimale. Base fattuale: `Flusso.js` (F1), `Flusso2.js` (F2), `Flusso3.js` (F3), `Flusso4.js` (F4); nomi DSL da `nomi-blocchi.md` (autorità); sintassi da `sintassi-dsl.md`.
>
> **Come leggere gli schemi a blocchi.** Ogni riga = `NomeDSL` (L#### = riga scheda nel manuale) · `// @alias` osservato nel flusso · ruolo. La sequenza è numerata nell'ordine di esecuzione. Ogni citazione `Fx:riga` punta alla riga del file di flusso.
>
> **⚠️ I bug NON vanno replicati.** Ogni flusso chiude con "bug da NON replicare" che rimanda a `pattern.md` (quirk Qn) con la `Fx:riga` esatta. I 4 flussi sono materiale reale con difetti noti: si copiano i *pattern buoni*, non i bug.
>
> Legenda: **⚠️ NON DOCUMENTATO** = presente nei flussi ma non nel manuale · **⚠️ DA VERIFICARE** = comportamento/trigger ipotizzato, da confermare in Studio (i **nomi-blocco** sono ora tutti confermati) · *(inferenza)* = deduzione sul motore, non fatto osservato (la vista è un DSL, non codice eseguito — L8).

---

## Indice

1. F1 — Ordini cliente PDF → TargetCross (multi-agente + rilettura)
2. F2 — DDT fornitore PDF → TargetCross (try/catch, controllo prezzi, Query SQL)
3. F3 — Ordini cliente PDF → TargetCross (variante a agente singolo)
4. F4 — Mail → classifica → estrai → registra → risponde
5. Esempio corretto minimale (flusso NUOVO, pulito)
6. CLI-A — Ordini cliente PDF → TargetCross, versione enterprise (fail-closed + auto-learning + audit) — export JSON, non vista DSL

---

## 1. F1 — Ordini cliente PDF → TargetCross (multi-agente testata/righe/footer + rilettura)

**Trigger d'ingresso.** ⚠️ Nessun blocco-trigger è proiettato nel DSL: il file inizia direttamente con il primo step. Ingresso di fatto = i PDF presenti in `<CARTELLA_INPUT>` letti da `FileList` (F1:7). Il trigger reale (manuale/schedulato) va confermato in Studio ⚠️ DA VERIFICARE.

**Scopo di business.** Per ogni PDF di ordine cliente in cartella: estrarne testata + righe + totali, validare i numeri, riconciliare cliente e articoli su TargetCross, creare il documento `ORD_CLI`, salvarne il PDF e notificare via email l'esito (ok / anomalia / errore).

**Schema a blocchi.**

1. `GestionaleSend` (L2807) · *(no @alias — "Verifica WS")* · ping `endpoint:"test"` per verificare la raggiungibilità del WS — F1:5
2. `FileList` (L1855) · `@alias Sfoglia la directory` · elenca i PDF → `lastFileList` — F1:7
3. `for (const item of lastFileList)` (ForEach, L2446) · `@alias ForEach: elabora ogni PDF ordine cliente` — F1:9
4. `CodeJs` (L3257) · `@alias CLEANUP_ordine` · azzera lo stato residuo del PDF precedente (anti-bleed) — F1:13
5. `AiAnalysis` (L1481) · `@alias AGENTE TESTATA` · `responseFormat:"json"`, `attachFilePath:"{__loopItem}"`, estrae SOLO l'header — F1:47
6. `CodeJs` (L3257) · `@alias catchTestata` · salva `lastAiOutput`→`testataJsonRaw` prima che l'agente seguente lo sovrascriva — F1:49
7. `AiAnalysis` (L1481) · `@alias AGENTE RIGHE` · estrae SOLO le righe articolo, tutte le pagine — F1:55
8. `CodeJs` (L3257) · `@alias catchRighe` · salva le righe grezze in `righeJsonRaw` — F1:57
9. `AiAnalysis` (L1481) · `@alias AGENTE FOOTER` · estrae i totali di piè di pagina (checksum) — F1:63
10. `CodeJs` (L3257) · `@alias validateRighe` · validazione numerica deterministica (netto/totale) + checksum footer; produce `rilettureQueue` (`[]`=skip, `[1]`=1 pass) — F1:66
11. `for (const item of rilettureQueue)` (ForEach, L2446) · `@alias RILETTURA` · rilegge SOLO le righe sospette — F1:155
    - `AiAnalysis` (L1481) · rilettura mirata delle righe in `{righeSospetteList}` — F1:156
    - `CodeJs` (L3257) · `@alias mergeValidate` · fonde le correzioni per `codArt` e rivalida — F1:158
12. `CodeJs` (L3257) · `@alias assembleHeader` · fonde testata + righe validate nelle chiavi legacy — F1:234
13. `GestionaleSend` (L2807) · `endpoint:"clienti"`, `filtro:"CF.P_IVA_CF='{piva}'"` · cerca il cliente per P.IVA — F1:303
14. `CodeJs` (L3257) · `@alias clienteOutput` · estrae `codCf`/`ragSoc` dal risultato — F1:304
15. `CodeJs` (L3257) · `@alias righePrep` · prepara `righePerRicerca` (righe + `codCf`) — F1:343
16. `for (const item of righePerRicerca)` (ForEach, L2446) · `@alias Ricerca articoli` — F1:385
    - `CodeJs` (L3257) · `@alias artPrepOutput` · legge `__loopItem` → `currentCodArt*` — F1:387
    - `GestionaleSend` (L2807) · `endpoint:"articoli"` · risolve il codice articolo (diretto / LIKE / codice secondario) — F1:421
    - `CodeJs` (L3257) · `@alias artCheckA` · verifica se l'articolo è stato trovato — F1:423
    - `CodeJs` (L3257) · `@alias artAccumulate` · accumula in `articoliTrovati`/`articoliScartati` — F1:444
17. `CodeJs` (L3257) · `@alias cleanupArticoli` · scarta i temporanei per-riga e `lastTargetCrossJson` — F1:485
18. `CodeJs` (L3257) · `@alias bodyOutput` · determina `esito` (ok/anomalia/errore), costruisce `docBody`/`ordineTarget`, imposta `controllaEsito` — F1:495
19. `if ($.controllaEsito == true) { … } else { … }` (Branch, L2417) · `@alias Branch: crea documento se esito OK` — F1:612
    - **ramo true:**
      - `GestionaleSend` (L2807) · `@continueOnFail` · `endpoint:"documento"`, `resource:"ORD_CLI"`, `payloadFromKey:"ordineTarget"` · crea il documento — F1:614
      - `CodeJs` (L3257) · `@alias checkDoc` · verifica l'esito della creazione senza crashare — F1:617
      - `GestionaleSend` (L2807) · `@continueOnFail` · `endpoint:"documenti-stampa"`, `docId:"{lastGestionaleCodice}"` · stampa PDF — F1:640
      - `CodeJs` (L3257) · `@alias pdfPathOutput` · calcola path e nome file PDF — F1:643
      - `FileWrite` (L2135) · `@continueOnFail` · salva il PDF su disco — F1:661
    - **ramo else:**
      - `SetFields` (L2585) · azzera `lastGestionaleCodice`/`lastGestionalePdfPath` — F1:664
      - `throw new Error("…")` (Stop & Error, L2621) · `@alias Mancato inserimento` — **F1:666 (bug, vedi sotto)**
20. `AiAnalysis` (L1481) · `@alias Genera corpo email Markdown` · `responseFormat:"text"` — F1:669
21. `FileWrite` (L2135) · `@continueOnFail` · `@alias Log` · append su `report.html` — F1:672
22. `CodeJs` (L3257) · `@alias emailEnrichOutput` · arricchisce subject/body (`mailSubjectFinal`, `mailBodyMarkdown`) — F1:674
23. `Markdown` (L3209) · `direction:"mdToHtml"`, `sourceKey:"mailBodyMarkdown"`, `outputKey:"lastMarkdownHtml"` — F1:708
24. `SendEmail` (L2993) · `@continueOnFail` · `@alias invio mail` · `bodyFormat:"html"` — **F1:711 (bug, vedi sotto)**

**Cosa insegna.**
- **Multi-agente per ridurre distrazione:** tre `AiAnalysis` separati (testata / righe / footer) invece di un prompt unico → ogni agente ha un compito ristretto e sbaglia meno.
- **Catch-pattern:** ogni agente scrive in `lastAiOutput`, che il successivo sovrascrive; un `CodeJs` subito dopo salva il valore in una chiave dedicata (`testataJsonRaw`, `righeJsonRaw`) — F1:49, F1:57. *(inferenza: il motore riusa `lastAiOutput`, quindi va catturato subito.)*
- **Validazione deterministica come checksum:** la matematica (netto atteso da lordo/sconti, somma righe vs totale footer) sta in `CodeJs`, non nell'AI — F1:66.
- **Rilettura mirata a coda:** `rilettureQueue = [] | [1]` iterata da un `for` = 0 o 1 passi di ri-lettura solo delle righe sospette — F1:147, F1:155.
- **Anti-bleed:** `cleanupOrdine` cancella le chiavi StepData a inizio giro perché le letture usano `|| ''` e i valori del PDF precedente resterebbero — F1:13.
- **Escape SQL manuale:** gli apici nei filtri sono raddoppiati a mano (`c.replace(/'/g,"''")`) prima di interpolare in `filtro` — F1:263.

**⚠️ Bug da NON replicare.**
- **Q6 — `throw` nel ramo else** (F1:666): interrompe l'intera run dentro `for(lastFileList)`, rende irraggiungibili gli step email a valle e blocca i PDF successivi in coda. → `pattern.md` Q6. *Fix:* usare Branch senza `throw` (come F2/F4).
- **Q7 — `SendEmail` finale scarta l'arricchimento** (F1:711): usa `subject:"{lastGestionaleCodice}"` e `body:"{lastTargetCrossJson}{lastAiOutput}"` con `bodyFormat:"html"` senza conversione, ignorando `mailSubjectFinal`/`lastMarkdownHtml` prodotti apposta ai passi 22–23; peggio, `lastTargetCrossJson` è già stato cancellato da `cleanupArticoli` (F1:490). → `pattern.md` Q7.
- **Q3 — chiavi non a catalogo** in `checkDoc`: `lastTargetCrossStatus` (F1:619) e `lastTargetCrossResponseBody` (F1:626) non sono output documentati di `GestionaleSend`; se il motore non le emette, la verifica del 500 è cieca. → `pattern.md` Q3.
- **Dead-read `priceAlertsJson`** (F1:687): letto in `emailEnrichOutput` ma mai prodotto in F1 (nasce solo in F2:171) → blocco sempre inerte.
- **`colonne:"COD_ART; DES_ART"`** con spazio dopo `;` (F1:421) vs manuale senza spazi (L976) → `pattern.md`.

---

## 2. F2 — DDT fornitore PDF → TargetCross (try/catch, controllo prezzi, Query SQL)

**Trigger d'ingresso.** ⚠️ Trigger non proiettato nel DSL. Ingresso di fatto = i PDF in `<CARTELLA_INPUT>` letti da `FileList` (F2:10).

**Scopo di business.** Per ogni bolla (DDT) fornitore in PDF: estrarre testata + righe, trovare il fornitore per P.IVA, validare gli articoli, collegare le righe all'ordine fornitore già a gestionale (via **Query SQL** dirette), confrontare i prezzi bolla↔ordine e segnalare le differenze, creare il documento `DDT_FOR`, notificare via email con allegati e archiviare il PDF.

**Schema a blocchi.**

1. `try { GestionaleSend(…endpoint:"test") } catch { throw new Error("WebService non operativo") }` (onError, L9 + Stop & Error L2621) · ping WS con gestione errore — F2:4–8
2. `FileList` (L1855) · `pattern:"*.pdf"` → `lastFileList` — F2:10
3. `for (const item of lastFileList)` (ForEach, L2446) — F2:12
4. `AiAnalysis` (L1481) · `responseFormat:"json"`, `attachFilePath:"{__loopItem}"`, `provider:"claude"`, `model:"claude-sonnet-4-6"` · estrae testata+righe del DDT — F2:14
5. `CodeJs` (L3257) · `outputKey:"norm"` · normalizza `piva`, `articoliFiltro`, `numConfQ`, `righe` — F2:18
6. `GestionaleSend` (L2807) · `endpoint:"fornitori"`, `filtro:"CF.P_IVA_CF='{piva}'"` · cerca il fornitore — F2:55
7. `CodeJs` (L3257) · `outputKey:"forn"` · legge `codCf`/`ragSoc` — F2:57
8. `GestionaleSend` (L2807) · `endpoint:"articoli"`, `filtro:"{articoliFiltro}"` · valida i codici articolo — F2:79
9. `Query` (Query SQL, L1997) · `@continueOnFail` · testata ordine fornitore: `ORDINE_ID` con placeholder **bound senza apici** `WHERE COD_CF = {codCf} AND NUMERO_CONFERMA = {numConfQ}` — F2:82
10. `CodeJs` (L3257) · `outputKey:"ordineLink"` · `@continueOnFail` · imposta `ordineId` (tiene quello della bolla se presente) — F2:85
11. `Query` (Query SQL, L1997) · `@continueOnFail` · righe ordine fornitore (`ORD_RIGA_ID`, residuo, prezzi/sconti) filtrate su `{ordineId}` — F2:104
12. `CodeJs` (L3257) · `outputKey:"righeLink"` · `@continueOnFail` · abbina righe bolla↔ordine e produce `priceAlertsJson` (controllo prezzi) — F2:107
13. `CodeJs` (L3257) · `outputItemsKey:"lastQueryRows"` · determina `esito` e compone `docBody` del `DDT_FOR` + dati report — F2:177
14. `if ($.esito == "ok") { … }` (Branch, L2417) · `@continueOnFail` (annotazione sul costrutto) — F2:214
    - `GestionaleSend` (L2807) · `@continueOnFail` · `endpoint:"documento"`, `resource:"DDT_FOR"`, `payloadFromKey:"docBody"` — F2:217
    - `GestionaleSend` (L2807) · `@continueOnFail` · `endpoint:"documenti-stampa"`, `resource:"DDT_FOR"` — F2:220
15. `AiAnalysis` (L1481) · `responseFormat:"text"` · genera il corpo email in markdown — F2:223
16. `CodeJs` (L3257) · `outputKey:"docCreato"` · `@continueOnFail` · antepone al report il codice documento + blocco controllo prezzi — F2:226
17. `Markdown` (L3209) · `sourceKey:"lastAiOutput"`, `outputKey:"lastMarkdownHtml"` — F2:257
18. `SendEmail` (L2993) · `subject:"{mailSubject}"`, `body:"{lastMarkdownHtml}"`, `bodyFormat:"html"`, `attachments:["{__loopItem}","{lastGestionalePdfPath}"]`, `smtpConfigId:"1"` — F2:259
19. `FileMove` (L1971) · `@alias Sposta cartella` · archivia in `…\ddt\elaborati` — F2:261

**Cosa insegna.**
- **onError con `try/catch`:** il ping WS è avvolto in `try { … } catch { throw new Error(...) }` (F2:4). È l'unico uso di `try/catch` osservato come onError; il `catch` è **senza binding** (`catch {`, non `catch (e) {`).
- **Query SQL con placeholder bound:** `Query.sql` usa `{codCf}`/`{numConfQ}` **senza apici** (F2:82, F2:104) — meccanica opposta a `GestionaleSend.filtro`, dove i placeholder vanno dentro apici con escape manuale (F1:303). → vedi `sintassi-dsl.md §5`.
- **Controllo prezzi:** `righeLink` confronta lordo/sconti/netto della bolla con quelli della riga d'ordine collegata e accumula gli scostamenti in `priceAlertsJson` (F2:107) — poi anteposti al report (F2:244).
- **`SendEmail` fatto bene:** usa `mailSubject` + `lastMarkdownHtml` (convertito) + `attachments` (bolla originale + PDF del DDT) — **il modo corretto**, contro il bug Q7 di F1/F3.
- **Archiviazione:** `FileMove` sposta il PDF elaborato per non rielaborarlo al giro dopo (F2:261).

**⚠️ Bug da NON replicare.**
- **Q3 — `lastQueryJson`** (F2:88, F2:110, F2:186): `Query` non documenta questa chiave di output; la logica di `ordineLink`/`righeLink`/composizione doc ci si fonda. Se il motore emette un altro nome, la lettura torna `[]`. → `pattern.md` Q3.
- **Q10 — `@alias` assente in tutto F2** (usa `//` semplice): incoerente con F1/F3/F4; e `@continueOnFail` su un **costrutto** `if` (F2:213) invece che su uno step. → `pattern.md` Q10.
- **`outputItemsKey:"lastQueryRows"`** (F2:177): riusa una chiave dall'aspetto di output standard di `Query` per gli items di un `CodeJs` → collisione semantica. → `pattern.md`.
- **`FileMove` con target dentro il source** (F2:261): `source` = `…\ddt`, `target` = `…\ddt\elaborati` (sottocartella del source) → spostamento della cartella dentro sé stessa, comportamento ambiguo *(inferenza)* ⚠️ DA VERIFICARE.
- **TODO non chiuso** (F2:175): commento `modificare la riga 25 con la causale, serie e magazzino` → causale/serie/deposito del `DDT_FOR` sono hardcoded (F2:202) e segnati come da rivedere.

---

## 3. F3 — Ordini cliente PDF → TargetCross (variante a agente singolo)

**Trigger d'ingresso.** ⚠️ Come F1: nessun trigger proiettato; ingresso = PDF in `<CARTELLA_INPUT>` via `FileList` (F3:7).

**Scopo di business.** Identico a F1 (ordini cliente PDF → documento `ORD_CLI` + email esito), ma è la **versione precedente e più semplice**: un solo `AiAnalysis` estrae tutto il JSON `{testata, righe}`, senza agenti separati, senza footer/checksum, senza rilettura. F1 è l'evoluzione hardened di F3.

**Schema a blocchi.**

1. `GestionaleSend` (L2807) · `@alias Verifica WS` · ping `endpoint:"test"` (nudo, senza `try/catch`) — F3:5
2. `FileList` (L1855) · `@alias Sfoglia la directory` → `lastFileList` — F3:7
3. `for (const item of lastFileList)` (ForEach, L2446) — F3:9
4. `CodeJs` (L3257) · `@alias CLEANUP_ordine` · anti-bleed — F3:13
5. `AiAnalysis` (L1481) · `@alias Estrai dati ordine da PDF` · `responseFormat:"json"` · estrae testata+righe in **un unico** JSON — F3:42
6. `CodeJs` (L3257) · `@alias normOutput` · normalizza la testata e prepara `articoliFiltro`/`righeOrdine` — F3:45
7. `GestionaleSend` (L2807) · `endpoint:"clienti"`, `filtro:"CF.P_IVA_CF='{piva}'"` — F3:109
8. `CodeJs` (L3257) · `@alias clienteOutput` — F3:110
9. `CodeJs` (L3257) · `@alias righePrep` — F3:149
10. `for (const item of righePerRicerca)` (ForEach, L2446) · `@alias Ricerca articoli` — F3:191
    - `CodeJs` (L3257) · `@alias artPrepOutput` — F3:193
    - `GestionaleSend` (L2807) · `endpoint:"articoli"` — **F3:225 (bug, vedi sotto)**
    - `CodeJs` (L3257) · `@alias artCheckA` — F3:227
    - `CodeJs` (L3257) · `@alias artAccumulate` — F3:248
11. `CodeJs` (L3257) · `@alias cleanupArticoli` — F3:289
12. `CodeJs` (L3257) · `@alias bodyOutput` · determina `esito`, costruisce `docBody` — **F3:299 (contiene bug, vedi sotto)**
13. `if ($.controllaEsito == true) { … } else { … }` (Branch, L2417) — F3:412
    - **ramo true:** `GestionaleSend` documento (F3:413) → `GestionaleSend` documenti-stampa (F3:414) → `CodeJs pdfPathOutput` (F3:417) → `FileWrite` (F3:435)
    - **ramo else:** `SetFields` (F3:438) → `throw new Error("…")` — **F3:440 (bug, vedi sotto)**
14. `AiAnalysis` (L1481) · corpo email markdown · `responseFormat:"text"` — F3:443
15. `FileWrite` (L2135) · `@alias Log` · `@continueOnFail` — F3:446
16. `CodeJs` (L3257) · `@alias emailEnrichOutput` — F3:448
17. `Markdown` (L3209) · `mdToHtml` — F3:482
18. `SendEmail` (L2993) · `@continueOnFail` — **F3:485 (bug, vedi sotto)**

**Cosa insegna.**
- **Baseline vs hardened:** confronta 1:1 con F1. F3 mostra la forma "grezza"; F1 aggiunge multi-agente + validazione + rilettura + i fix di Q8/Q9. Utile per capire *perché* servono quelle complicazioni.
- Stessa impalcatura di F1 per cliente/articoli/documento/email → i pattern buoni (cleanup, righePrep, accumulo esito) sono già qui.

**⚠️ Bug da NON replicare.**
- **Q8 — `dataOrdine` copiava `dataConferma`** (F3:66): `const dataOrdine = (testata.dataConferma || '')…` → la data ordine è sempre uguale alla data conferma. Fixato in F1:250 (`testata.dataOrdine`). → `pattern.md` Q8.
- **Q9 — filtro articoli con `TIPO_CODICE`** (F3:225): la sottoquery aggiunge `AND (ART_CODICI.TIPO_CODICE='{currentCodCfEscaped}' …)` mettendo il COD_CF cliente in un campo che è un *tipo*, non il cliente → azzera i match. Rimosso in F1:419–421. → `pattern.md` Q9.
- **Q6 — `throw` nel ramo else** (F3:440): identico a F1, uccide la run e blocca i PDF successivi. → `pattern.md` Q6.
- **Q7 — `SendEmail` scarta l'arricchimento** (F3:485): `subject:"{lastGestionaleCodice}"`, `body:"{lastTargetCrossJson}{lastAiOutput}"`. → `pattern.md` Q7.
- **Dead-read `priceAlertsJson`** (F3:461): mai prodotto in F3.

---

## 4. F4 — Mail → classifica → estrai (allegati via Switch) → registra → risponde

**Trigger d'ingresso.** `MailRead` (L2905) è il primo step/sorgente: legge la casella IMAP `INBOX` → `lastEmails` (F4:3). ⚠️ Il trigger schedulato/polling che avvia la lettura non è proiettato nel DSL.

**Scopo di business.** Per ogni mail in arrivo: classificarla (ordine / altro) con l'AI; se è un ordine, estrarne i dati strutturati (dal corpo e — se presenti — dagli **allegati**, smistati per estensione con uno Switch), cercare il cliente su TargetCross, costruire il payload, registrare l'ordine `ORD_CLI` e rispondere via email (conferma al cliente o notifica di errore + avviso interno).

**Schema a blocchi.**

1. `MailRead` (L2905) · `mode:"Imap"`, `downloadAttachments:false`, `unreadOnly:false` → `lastEmails` — F4:3
2. `for (const item of lastEmails)` (ForEach, L2446) · `// @foreach maxIterations=20` · `@alias ForEach mail in arrivo` — F4:6–7
3. `SetFields` (L2585) · `@alias Estrai campi mail corrente` · copia subject/body/from/attachments nello StepData (`currentMail*`) — F4:10
4. `AiAnalysis` (L1481) · `@alias …classificatore` · `responseFormat:"report"` · risponde `ordine` oppure `altro` — F4:11
5. `CodeJs` (L3257) · `@alias Output Scraping` · `outputKey:"isOrdine"` · normalizza la label (prima riga, lowercase) — F4:14
6. `if ($.isOrdine == ordine) { … }` (Branch, L2417) · `@alias Branch: è un ordine?` — **F4:27 (bug, vedi sotto)**
   1. `CodeJs` (L3257) · `@alias Controlla allegati` · `outputKey:"attachmentCheck"` · ritorna un **booleano** — F4:30
   2. `if ($.hasAttachments == true) { … } else { … }` (Branch, L2417) · `@alias Branch: ha allegati?` — **F4:36 (bug, vedi sotto)**
      - **ramo true:**
        1. `for (const item of attachmentCheck.attachmentList)` (ForEach annidato, L2446) · `@alias ForEach allegato` — **F4:39 (bug, vedi sotto)**
           - `CodeJs` (L3257) · `@alias currentAttachment` · estrae `filePath` + `ext` — F4:42
           - `switch ($.currentAttachment.ext) { … }` (Switch, L2658) · `@alias Switch tipo allegato` — F4:49
             - `case "pdf"`: `PdfExtract` (L2255) F4:53 + `SetFields` (L2585) F4:56
             - `case "docx"`: `WordExtract` (L2355) F4:61 + `SetFields` F4:64
             - `case "doc"`: `WordExtract` (L2355) F4:69 + `SetFields` F4:72
             - `case "xlsx"`: `XlsxExtract` (L2369) F4:77 + `CodeJs xlsxAsText` F4:80 + `SetFields` F4:86
             - `case "xls"`: `XlsxExtract` (L2369) F4:91 + `CodeJs xlsxAsText` F4:94 + `SetFields` F4:100
             - `default`: `SetFields` "[Allegato non supportato]" F4:105
           - `SetFields` (L2585) · `@alias Accumula testo allegati` · concatena in `allAttachmentsText` (accumulatore auto-referenziale) — F4:110
        2. `ExtractStructured` (Estrai dati AI, L1615) · `@alias …(con allegati)` · `input`+`schema`+`instructions` → `lastExtractedJson` — F4:114
      - **ramo else:**
        - `ExtractStructured` (L1615) · `@alias …(solo testo)` · come sopra ma solo dal corpo mail — F4:118
   3. `GestionaleSend` (L2807) · `@continueOnFail` · `endpoint:"clienti"`, `filtro:"CF.P_IVA_CF='{lastExtractedJson.p_iva}'"` — F4:123
   4. `CodeJs` (L3257) · `@alias …Costruisci payload` · `outputKey:"orderPayloadResult"` → `targetPayloadJson` — F4:126
   5. `GestionaleSend` (L2807) · `@continueOnFail` · `endpoint:"documento"`, `resource:"ORD_CLI"`, `payloadFromKey:"orderPayloadResult.targetPayloadJson"` · registra l'ordine — F4:168
   6. `if ($.lastGestionaleEsito == 'OK' || $.lastGestionaleCodice != '') { … } else { … }` (Branch, L2417) · `@alias Branch: esito registrazione ERP` — F4:171
      - **ramo true (successo):**
        - `AiAnalysis` (L1481) · testo mail conferma · `responseFormat:"text"` — F4:174
        - `SendEmail` (L2993) · `to:["{currentMailFrom}"]`, `bodyFormat:"plain"` · conferma al cliente — F4:177
      - **ramo else (fallimento):**
        - `AiAnalysis` (L1481) · testo mail fallimento — F4:181
        - `SendEmail` (L2993) · notifica al cliente — F4:184
        - `SendEmail` (L2993) · `@continueOnFail` · notifica interna a `{TBD:email_responsabile_interno}` — **F4:188 (bug, vedi sotto)**

**Cosa insegna.**
- **Trigger da mail:** `MailRead` come sorgente → `lastEmails` iterato dal ForEach esterno (F4:3→7).
- **Classificazione AI → routing:** un `AiAnalysis` che risponde una sola parola, ripulita da un `CodeJs`, pilota un Branch (F4:11→14→27).
- **ForEach annidato:** loop esterno sulle mail, loop interno sugli allegati; l'inner `__loopItem` ombreggia l'outer, quindi i campi mail vanno catturati prima (pattern SetFields F4:10). Vedi `sintassi-dsl.md §2.1`.
- **Switch per tipo file:** un `switch` sull'estensione instrada l'estrazione al blocco giusto (`PdfExtract`/`WordExtract`/`XlsxExtract`) — F4:49.
- **`ExtractStructured` con schema JSON:** estrazione strutturata guidata da `schema` + `instructions` → `lastExtractedJson`, poi navigabile con `{lastExtractedJson.campo}` (F4:114, F4:123).
- **Risposta condizionale + notifica multipla:** Branch sull'esito ERP → conferma / errore al cliente + avviso interno (F4:171).
- **`@foreach maxIterations=20`:** unico cap iterazioni osservato (F4:6).

**⚠️ Bug da NON replicare (F4 è il flusso con la catena più fragile).**
- **Q4+Q5 — catena allegati rotta:**
  - `downloadAttachments:false` (F4:3) ma più avanti si usa `filePath` degli allegati (F4:43, F4:53) → i file non sono su disco.
  - `SetFields` scrive `currentMailHasAttachments` con la **lista** allegati, non un booleano (F4:10).
  - il Branch legge `$.hasAttachments` (F4:36), chiave **mai scritta** (esiste `currentMailHasAttachments`).
  - il ForEach itera `attachmentCheck.attachmentList` (F4:39) ma `attachmentCheck` ritorna un **booleano**, non un oggetto con `attachmentList`. → `pattern.md` Q4/Q5.
- **Q1 — bareword non quotato** `if ($.isOrdine == ordine)` (F4:27): `ordine` senza apici (cfr `'OK'` F4:171). Se il motore lo risolve come identificatore→undefined, l'intero ramo ordine (F4:28–190) è codice morto. → `pattern.md` Q1.
- **Q2 — `switch` senza `break`** (F4:49–107): artefatto di proiezione; copiato come JS reale cadrebbe nei case successivi (fallthrough). → `pattern.md` Q2.
- **`responseFormat:"report"` che alimenta un Branch** (F4:11→27): viola l'avvertenza L38 (il report non è pensato per essere confrontato in una condizione). → `pattern.md`.
- **`{TBD:email_responsabile_interno}`** (F4:188): destinatario non risolto → la notifica interna parte verso un placeholder. → `pattern.md`.

---

## 5. Esempio corretto minimale (flusso NUOVO, pulito)

> **Scopo.** Un flusso nuovo, non derivato dai 4 esempi, che usa **SOLO blocchi con nome DSL confermato** (`nomi-blocchi.md §2`) e rispetta le regole d'oro. Compito: leggere PDF di fatture da una cartella, estrarne un JSON, decidere ok/anomalia e inviare l'email giusta — **senza** i bug Q6/Q7. Ogni inferenza è marcata.
>
> Blocchi usati (tutti ✅ CONFERMATI): `FileList` (L1855), `CodeJs` (L3257), `AiAnalysis` (L1481), `Markdown` (L3209), `SendEmail` (L2993, ⚠️ nome irregolare: verbo "Send" anteposto) + costrutti `for…of` (L2446) e `if/else` (L2417).

```js
// Flusso in codice (Modalità Sviluppatore). Proiezione fedele del grafo.

// @alias Sfoglia le fatture PDF
// ⚠️ La forma-decoratore "// @alias" NON e' documentata nel manuale (Q10): usala solo
//    come etichetta del nodo, non ha effetti sul motore. *(inferenza)*
// FileList (L1855): elenca i file della cartella -> chiave StepData "lastFileList".
FileList({ directory: "C:\\Fatture\\In", pattern: "*.pdf", recursive: false });

// ForEach (L2446): "item" e' cosmetico -> l'elemento corrente si legge come {__loopItem}.
//    Un solo blocco-trigger a monte alimenta il loop (qui: lastFileList).
for (const item of lastFileList) {

  // @alias CLEANUP: azzera lo stato del PDF precedente (regola d'oro: anti-bleed)
  // Le letture a valle usano "|| ''"/"|| '{}'": senza cleanup i valori del giro
  //    precedente resterebbero. NON tocca lastFileList (alimenta il loop) ne' __loopItem.
  CodeJs({ outputKey: "cleanup" }, () => {
    // stepData = stato mutabile; $input = snapshot in sola lettura *(inferenza, sintassi-dsl §4.3)*
    ['fatturaJson','esito','fornitore','totale','mancanti',
     'mailSubject','mailBodyMd','lastAiOutput','lastMarkdownHtml'
    ].forEach(function (k) { delete stepData[k]; });
    return { ok: true };
  });

  // @alias AGENTE estrazione: PDF -> JSON
  // AiAnalysis (L1481): responseFormat:"json" per output strutturato;
  //    attachFilePath:"{__loopItem}" allega il PDF del giro corrente.
  AiAnalysis({
    prompt: "Analizza la fattura PDF allegata. Restituisci SOLO questo JSON, nessun altro testo:\n{\"fornitore\":\"<ragione sociale>\",\"totale\":\"<totale documento, copia le cifre esatte>\",\"pIva\":\"<solo cifre>\"}\nCampo assente = stringa vuota. Restituisci SOLO il JSON.",
    responseFormat: "json",
    attachFilePath: "{__loopItem}"
  });

  // @alias parse+decidi: cattura l'output PRIMA che un altro agente sovrascriva lastAiOutput
  // Regola d'oro (catch-pattern, cfr F1:49): ogni AiAnalysis scrive in lastAiOutput e il
  //    successivo lo sovrascrive *(inferenza)*, quindi qui lo si legge e si decide l'esito.
  CodeJs({ outputKey: "decidi" }, () => {
    var raw = (stepData.lastAiOutput || $input.lastAiOutput || '{}');
    var j; try { j = JSON.parse(raw); } catch (e) { j = {}; }

    var fornitore = (j.fornitore || '').toString().trim();
    var totale    = (j.totale || '').toString().trim();

    // esito deterministico calcolato in CodeJs, non lasciato all'AI (regola d'oro)
    var mancanti = [];
    if (!fornitore) mancanti.push('fornitore');
    if (!totale)    mancanti.push('totale');
    var esito = mancanti.length ? 'anomalia' : 'ok';

    var subject = (esito === 'ok')
      ? '[OK] Fattura ' + fornitore + ' - Totale ' + totale
      : '[ANOMALIA] Fattura ' + (fornitore || 'sconosciuta') + ' - Dati mancanti';

    var result = {
      fornitore: fornitore,
      totale: totale,
      esito: esito,
      mancanti: mancanti.join(', '),
      mailSubject: subject
    };
    // Object.assign(stepData, result): commit delle chiavi nello stato (cfr F1:149)
    Object.assign(stepData, result);
    return result;   // l'oggetto finisce anche in outputKey "decidi"
  });

  // @alias Branch: fattura valida?
  // Branch/if (L2417): condizione = $.<chiave> <op> <valore>, valutata dal MOTORE (non e' JS).
  //    RHS SEMPRE quotato ("ok"): NON usare bareword non quotati (evita il bug Q1 di F4:27).
  if ($.esito == "ok") {

    // @alias Genera corpo email (markdown)
    AiAnalysis({
      prompt: "Scrivi il corpo email (markdown) che conferma la registrazione della fattura.\nFornitore: {fornitore}\nTotale: {totale}\nTono professionale, italiano, nessuna firma. Rispondi SOLO col markdown.",
      responseFormat: "text"
    });

    // @alias Salva il markdown appena generato (catch-pattern: prima della conversione)
    CodeJs({ outputKey: "catchBody" }, () => {
      stepData.mailBodyMd = (stepData.lastAiOutput || $input.lastAiOutput || '');
      return { len: stepData.mailBodyMd.length };
    });

    // @alias Converti Markdown -> HTML
    // Markdown (L3209): sourceKey/outputKey vogliono il NOME di una chiave (niente graffe).
    Markdown({ direction: "mdToHtml", sourceKey: "mailBodyMd", outputKey: "lastMarkdownHtml" });

    // @alias Invia esito OK
    // SendEmail (L2993): usa le chiavi ARRICCHITE/convertite (mailSubject + lastMarkdownHtml),
    //    NON riscarta il lavoro fatto (evita il bug Q7 di F1:711/F3:485).
    SendEmail({
      to: ["ufficio.acquisti@example.com"],
      subject: "{mailSubject}",
      body: "{lastMarkdownHtml}",
      bodyFormat: "html"
    });

  } else {

    // @alias Invia segnalazione anomalia
    // Regola d'oro: NIENTE throw nel loop (evita il bug Q6 di F1:666/F3:440).
    //    Si invia una notifica e il for prosegue col PDF successivo.
    SendEmail({
      to: ["ufficio.acquisti@example.com"],
      subject: "{mailSubject}",
      body: "Fattura non registrata: dati mancanti ({mancanti}). File: {__loopItem}",
      bodyFormat: "plain"
    });
  }
}
```

**Regole d'oro applicate (e quale bug evitano).**
1. **Cleanup a inizio giro** → niente bleed cross-file (pattern F1:13). Non tocca `lastFileList`/`__loopItem`.
2. **Catch-pattern** → l'output di ogni `AiAnalysis` è salvato prima che il successivo sovrascriva `lastAiOutput` (pattern F1:49; qui `decidi` e `catchBody`).
3. **Esito deterministico in `CodeJs`**, non demandato all'AI.
4. **RHS di `==` quotato** (`"ok"`) → evita **Q1** (bareword non quotato, F4:27).
5. **Nessun `throw` nel loop** → evita **Q6** (F1:666/F3:440): l'anomalia diventa una mail, il giro continua.
6. **`SendEmail` usa `mailSubject` + `lastMarkdownHtml`** → evita **Q7** (F1:711/F3:485): non scarta subject/body arricchiti.

**Inferenze marcate in questo esempio.**
- `stepData` mutabile vs `$input` sola lettura → *(inferenza, `sintassi-dsl.md §4.3`)*.
- Un `AiAnalysis` successivo sovrascrive `lastAiOutput` → *(inferenza)*, base del catch-pattern.
- La forma-decoratore `// @alias` → **⚠️ NON DOCUMENTATA** come costrutto DSL (Q10); usata solo come etichetta.
- `SendEmail` è ✅ confermato come nome, ma **irregolare** (verbo "Send" anteposto, `nomi-blocchi.md §3`): i parametri `to/subject/body/bodyFormat` sono confermati (F1:711, F2:259).

---

## 6. CLI-A — Ordini cliente PDF → TargetCross, versione enterprise (fail-closed + auto-learning + audit)

**Fonte e formato.** Diversamente da F1–F4 (vista DSL "Modalità Sviluppatore", citate `Fx:riga`), questo flusso è fornito come **export JSON** dell'agente (`CLI-A_Ordine_Cliente__v1.4.1.thinkaiagent.json`, formato `thinkai.workforce.agent 1.0`). Non esiste quindi una riga di codice DSL da citare: si cita `CLI-A:#N` (il campo `Order` dello step nell'export) e, per gli step annidati in un contenitore, `CLI-A:#N→contenitore#M`. Tag dell'agente: `fail-closed`, `auto-learning`, `ai-vincolata`, `audit`, `REALE`. Trigger: schedulato (cron `*/30 * * * *`), non manuale.

**Perché è un esempio a parte.** F1/F3 risolvono lo stesso problema di business (ordine cliente PDF → `ORD_CLI` su TargetCross) in modo più semplice e con diversi bug noti (vedi Anti-pattern B1-B9). CLI-A è la stessa famiglia di problema portata a un livello "production-grade": non si limita a creare il documento, ma si rifiuta di partire se i prerequisiti non ci sono (A10), non perde un batch intero per un PDF corrotto (A11), previene le doppie elaborazioni a livello di file e di record (A12), accetta risultati parziali sopra una soglia esplicita (A13) e migliora nel tempo il matching articoli con una memoria propria (A14). Vedi `pattern.md` per il dettaglio di ciascun pattern.

**Schema a blocchi (livello architetturale, non ogni singolo CodeJs).**

1. `SetFields` (Type 18) · `@alias CONFIGURAZIONE CLI-A` · configurazione centralizzata: `workRoot`, `inputDirectory`, `operatorEmail`/`operatorEmailCc`, `ownVat`, `defaultCausale`/`defaultSerie`/`defaultDeposito`, `minPercentualeRisoltePerCreare:"60"`, `agentVersion` — `CLI-A:#1`
2. `CodeJs` · `@alias Valida configurazione obbligatoria` · valida email/serie/percorsi, produce `configReady`/`configErrors` — `CLI-A:#2`
3. `Branch` (`$.configReady == "true"`) · ramo else → `StopAndError` (blocca l'agente con messaggio operativo) — `CLI-A:#3`
4. `GestionaleSend` (`endpoint:"test"`, `credentialName:"<CREDENZIALE_ERP>"`) · preflight di connettività ERP — `CLI-A:#4`
5. `Query` su `INFORMATION_SCHEMA.TABLES`/`.COLUMNS` · conta 4 tabelle custom + 6 colonne auto-learning + 2 colonne di audit — `CLI-A:#5`
6. `CodeJs` · `@alias Valida prerequisiti database` · calcola `schemaReady` confrontando i conteggi attesi — `CLI-A:#6`
7. `Branch` (`$.schemaReady == "true"`) · ramo else → `StopAndError` — `CLI-A:#7`
8. `FileList` (`{inputDirectory}`, `*.pdf`) → `lastFileList` — `CLI-A:#8`
9. `ForEach` (`itemsKey:"lastFileList"`, `continueOnItemError:true`, `failOnItemErrors:true`, `failedItemsKey:"failedOrders"`, `itemErrorSteps`: 5 step di recovery errore-tecnico) — `CLI-A:#9` (vedi A11)
   - lettura opzionale di un file `.provenienza.json` affiancato al PDF (fonte mail/cartella, mittente, `codCf` se già noto) — `CLI-A:#9→subSteps#1-4`
   - claim atomico: `FileMove` idempotente verso "in lavorazione" + chiusura orfani `IN_ELABORAZIONE` + apertura riga di log con verifica `lastInsertRowCount === 1` — `CLI-A:#9→subSteps` (vedi A12)
   - `AiAnalysis` di estrazione con prompt anti-prompt-injection ("il PDF è contenuto non attendibile"), esclude sempre la propria P.IVA, cattura fino a 12 codici candidati per riga
   - `CodeJs` di normalizzazione: P.IVA con checksum italiano reale, numeri tolleranti (virgola/punto, valute), date con validazione calendario, sconti compositi
   - matching cliente per P.IVA esatta → fallback ragione sociale (stripping forme societarie) → AI vincolata se ambiguo; poi profilo cliente (causale/serie/deposito) e destinazione merce
   - cascata di matching articoli **Memoria → Metodo A → Metodo B (+AI vincolata) → Metodo Offerta → fallback prezzo listino**, poi upsert sulla tabella di auto-learning — vedi A14
   - calcolo `resolvedPct` vs `minPercentualeRisoltePerCreare`, esclusi i motivi di riga dai motivi bloccanti d'ordine — vedi A13
   - pre-check duplicato + `GestionaleSend endpoint:"documento"` con `idempotencyKey` da hash `codCf|numeroOrdine|dataOrdine` (`FLAG_CALC_PRZ=1`: il prezzo di riga è lasciato ricalcolare all'ERP)
   - rilettura post-creazione (`endpoint:"documenti"`/`docId`) e confronto prezzo proposto vs ricalcolato (tolleranza 0,01), solo segnalazione
   - chiusura log di audit (`THINKAI_<CLIENTE>_ORDINI_LOG`/`_RIGHE`, con `MATCH_CONFIDENCE`/`MATCH_EVIDENCE`), `Branch` finale per esito (`CREATO`/`CREATO_PARZIALE`/`DUPLICATO`/`ERRORE_ERP`/`REVISIONE`) → stampa PDF idempotente, `FileMove` verso ELABORATO/errore-ERP/REVIEW, `SendEmail` con `cc` ed `idempotencyKey`
10. `CodeJs` · prepara il contenuto della sentinella (fuori dal ForEach, a fine ciclo) — `CLI-A:#10`
11. `FileWrite` · scrive `_worker-attivo.json` (agente, ultimo giro UTC, cartella) come heartbeat per il monitoraggio esterno — `CLI-A:#11`

**Tabelle custom (audit + auto-learning), colonne osservate nelle query del flusso.**
- `THINKAI_<CLIENTE>_CLIENTI_PROFILO`: `COD_CF`, `COD_CAUS_DOC`, `SERIE_DOC`, `COD_DEP`, `DESTINATION_POLICY`, `ATTIVO`.
- `THINKAI_<CLIENTE>_ARTICOLI_PROFILO`: `COD_CF`, `CODICE_CLIENTE_NORM`, `CODICE_CLIENTE_RAW`, `COD_ART`, `APPROVATO`, `ATTIVO`, `ORIGINE`, `MATCH_METHOD`, `VALIDATION_MODE`, `CONFIDENCE`, `EVIDENCE_COUNT`, `LAST_USED_AT_UTC`, `LAST_CORRELATION_ID`, `NOTE`, `CREATED_BY`, `CREATED_AT_UTC`, `UPDATED_AT_UTC`.
- `THINKAI_<CLIENTE>_ORDINI_LOG`: `CORRELATION_ID`, `AGENT_VERSION`, `FILE_NAME`, `FILE_SOURCE`, `STATO`, `DATA_INIZIO_UTC`, `DATA_FINE_UTC`, `ERROR_CODE`, `ERROR_DETAIL` (`nvarchar(4000)`, troncato a 3990 char — dettaglio completo in `DETAIL_JSON`), `DETAIL_JSON`, `PIVA`, `COD_CF`, `RAG_SOC`, `NUMERO_ORDINE`, `DATA_ORDINE`, `DESTINAZIONE_PRESENTE`, `ERP_DOC_ID`, `RIGHE_TOTALI`, `RIGHE_RISOLTE`, `RIGHE_ANOMALE`, `EMAIL_STATO`, `EMAIL_ERRORE`, `UPDATED_AT_UTC`.
- `THINKAI_<CLIENTE>_ORDINI_LOG_RIGHE`: `CORRELATION_ID`, `RIGA_NUMERO`, `CODICE_CLIENTE_RAW`, `CODICE_CLIENTE_NORM`, `DESCRIZIONE`, `COD_ART`, `MATCH_METHOD`, `MATCH_CONFIDENCE`, `MATCH_EVIDENCE`, `UM_ORDINE`, `UM_TARGET`, `QUANTITA_RAW`, `QUANTITA_NORM`, `PREZZO_RAW`, `PREZZO_NORM`, `STATO`, `MOTIVO`, `CREATED_AT_UTC`.

**Gotcha impliciti osservati (da non ignorare se replichi il pattern).**
- `STRING_SPLIT` non disponibile su DB con `COMPATIBILITY_LEVEL` basso: prevedi un fallback (es. split via cast XML) se il gestionale del cliente gira su un SQL Server datato.
- Escape sistematico degli apici (`.replace(/'/g, "''")`) su ogni valore interpolato in un filtro SQL dinamico verso `GestionaleSend`/`Query` — altrimenti SQL injection o errore di sintassi con un solo apice nel nome cliente.
- TcRestAPI (v1.5.3, vedi `blocchi/integrazioni.md`): la doc ufficiale raccomanda **numeri JSON** con il punto decimale (`5.5`, non `"5,5"`) ed è l'unico formato indipendente dalle impostazioni del server; le stringhe sono accettate sugli endpoint documenti (un solo separatore = decimale) ma `"1.000"` diventa **1**. Negli endpoint anagrafica/articolo/distinta/listino le stringhe seguono le impostazioni del server (es. `"75,6"` con la virgola in `articolo`). I flussi più vecchi che convertono in formato italiano con `.replace('.', ',')` restano validi sui documenti, ma per i nuovi preferisci `Number` serializzato da `JSON.stringify`, e normalizza sempre prima, non dopo.
- Verificare sempre `lastInsertRowCount`/`lastUpdateRowCount` dopo un insert/update "di claim" su una chiave di correlazione: un valore diverso da 1 segnala una corsa fra run concorrenti, non un errore da ignorare.

**⚠️ Limiti di questa scheda.** A differenza di F1–F4 non è possibile citare righe di codice DSL esatte (la fonte è un export JSON): i dettagli di dettaglio (prompt AI completi, ogni singolo `CodeJs`) sono nel file originale fornito dall'utente, non riprodotti qui parola per parola. Chi deve replicare questo pattern in un nuovo flusso lo fa componendo i blocchi standard del catalogo secondo l'architettura sopra, non copiando un DSL che qui non esiste.
