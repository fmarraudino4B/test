# Sintassi DSL — come si SCRIVE un flusso in "Modalità Sviluppatore"

> Guida operativa alla grammatica del DSL di ThinkAI WorkForce Studio. Serve a **generare** flussi validi, non solo a leggerli.
>
> **Base fattuale:** spec consolidata + 4 flussi esportati — F1=`...\Nuova cartella\Flusso.js`, F2/F3/F4=`...\Manuale — ThinkAI WorkForce Studio\Flusso2/3/4.js` — e catalogo manuale (rif. `L####` = riga HTML del manuale). Ogni forma è tracciata a `Flusso:riga` o `L####`.
>
> **Convenzioni di questa guida:**
> - `⚠️ NON DOCUMENTATO` = presente nei flussi ma assente dal manuale.
> - `⚠️ DA VERIFICARE` = ipotesi non confermata; apri lo step in Studio prima di usarla.
> - *(inferenza)* = deduzione sul comportamento del motore; la vista è un DSL, NON codice eseguito (L8), quindi il runtime non è osservabile dal solo file.
>
> **I nomi DSL dei blocchi NON stanno qui.** L'unica fonte autorevole dei nomi-funzione è `nomi-blocchi.md` (nella stessa cartella `references/`). Qui si descrive solo la *grammatica* (come si scrive uno step), non *quale* nome usare.

## Indice
1. Struttura del file
2. Costrutti di controllo (ForEach, Branch, Switch, Stop&Error, onError)
3. Annotazioni-commento (`// @alias`, `// @continueOnFail`, `// @foreach`)
4. CodeJs — API completa
5. Placeholder ed espressioni

---

## 1. Struttura del file

### 1.1 Intestazione fissa
Apri SEMPRE il file con questa riga esatta (F1:1, F2:1, F3:1, F4:1):
```js
// Flusso in codice (Modalità Sviluppatore). Proiezione fedele del grafo.
```

### 1.2 La vista a codice è un DSL, NON codice eseguito
Fatto centrale (L8, L1212): `if`/`for`/`switch`/`throw`/`try-catch` e le espressioni fra virgolette **le valuta il motore del flusso**, non un runtime JS. L'unico codice realmente eseguito è quello dentro `CodeJs` (§4) / `CodePython`.

Ne conseguono **due grammatiche sovrapposte**, da tenere distinte (F1:135, F4:130):
- **(a) grammatica DSL** — costrutti di controllo, placeholder `{}`, espressioni `$.`, annotazioni `// @…`: valutata dal motore.
- **(b) JS reale** — solo dentro l'arrow-function di `CodeJs` (operatori `&&`, `>`, ternari, regex, `try/catch(e)`): NON fa parte della grammatica del flusso.

### 1.3 Sequenza di chiamate-blocco
Il corpo del file è una **sequenza di chiamate-blocco** intervallate da costrutti di controllo e annotazioni. Ogni chiamata-blocco ha la forma:
```js
NomeBlocco({ ...config });
```
- `NomeBlocco` = identificatore DSL preso da `nomi-blocchi.md` (NON inventarlo).
- L'argomento è un **singolo oggetto di config** con i parametri del blocco. I nomi dei parametri **coincidono col manuale** (nessuna divergenza osservata): riportali esatti e non ometterne.
- Eccezione di firma: `CodeJs` prende **due** argomenti (config + arrow-function) — vedi §4.

Esempio di step nudo (F1:5):
```js
GestionaleSend({ timeoutSeconds: 60, credentialName: "targetcross-test", endpoint: "test" });
```

### 1.4 StepData (lo stato del flusso)
Lo stato scorre in un dizionario chiamato **StepData** (L5-L6):
- Ogni blocco **legge** chiavi prodotte da trigger/step precedenti (via placeholder `{chiave}`, §5) e **scrive** il proprio output.
- L'output di un blocco è la sua chiave di catalogo (es. `FileList` → `lastFileList`, L2711; `MailRead` → `lastEmails`) oppure la chiave scelta con `outputKey`/`outputItemsKey` in `CodeJs` (§4).
- Gli step a valle si concatenano leggendo quelle chiavi. Esempio: `FileList` scrive `lastFileList` (F1:7), il `for` a riga 9 lo itera.
- Il catalogo delle chiavi StepData osservate (con produttore e quirk) sta nella `modello-esecuzione.md` §2; qui interessa solo che **il collegamento fra step passa per i nomi di chiave**, non per variabili locali.

---

## 2. Costrutti di controllo

Sono costrutti nativi JS **in cui il DSL proietta i blocchi di flusso** (L8). **NON sono funzioni.** La loro tabella-nomi (DISPLAY → proiezione) sta in `nomi-blocchi.md` §5.

### 2.1 ForEach — `for (const item of <chiave>) { … }`  (L2446)
Sintassi:
```js
// @foreach maxIterations=20            // opzionale: cap iterazioni (default 1000, L2712)
for (const item of lastFileList) {
  // corpo: uno o più step
}
```
Regole:
- L'**iterabile è una chiave StepData** prodotta a monte: `lastFileList` da FileList (F1:7→9), `lastEmails` da MailRead (F4:7), o un output di `CodeJs` (`righePerRicerca` F1:385).
- **`item` è cosmetico e inerte**: il corpo NON lo usa mai. L'elemento corrente si legge come placeholder `{__loopItem}` (§5) o, dentro `CodeJs`, come `stepData.__loopItem` / `$input.__loopItem` (F1:388, F4:43).
- È ammesso un **path puntato** sull'iterabile: `for (const item of attachmentCheck.attachmentList)` (F4:39). Il manuale documenta però solo la forma piatta (L2711).
- **Annidamento**: esempio outer `lastEmails` (F4:7) con inner `attachmentCheck.attachmentList` (F4:39). Il motore ha **un solo `__loopItem`**, ri-associato per livello: l'inner "ombreggia" l'outer (commento F1:138-139). Cattura i valori dell'outer PRIMA di entrare nel loop interno.
- ⚠️ non osservati (documentati L713-715): `batchSize`, `maxConcurrency`, `delayBetweenMs`.

Esempio completo (F4:6-9):
```js
// @foreach maxIterations=20
for (const item of lastEmails) {
  SetFields({ assignments: [{"key":"currentMailSubject","value":"{__loopItem.subject}"}, /* … */] });
  // …
}
```

### 2.2 Branch (IF) — `if (<cond>) { … } else { … }`  (L2417)
Sintassi:
```js
if ($.controllaEsito == true) {
  // ramo vero
} else {
  // ramo falso (opzionale)
}
```
Regole:
- La condizione è **sempre** nella forma `$.<chiave> <op> <valore>` (§5): la valuta il motore, non è JS.
- Il ramo `else` è **opzionale**: con else F1:612/662, F4:36; senza else F2:214, F4:27.
- Operatori osservati in condizione DSL: `==` (F1:612), `!=` (F4:171), `||` (F4:171). ⚠️ non osservati qui: `>` (solo esempio L2682), `&&` (compare solo dentro il JS di `CodeJs`).

Esempio con else (F1:612-667, condensato):
```js
// @alias Branch: crea documento se esito OK
if ($.controllaEsito == true) {
  // @continueOnFail
  GestionaleSend({ credentialName: "targetcross-test", endpoint: "documento", resource: "ORD_CLI", payloadFromKey: "ordineTarget", timeoutSeconds: 120 });
} else {
  SetFields({ assignments: [{"key":"lastGestionaleCodice","value":""}] });
  throw new Error("Non sono riuscito a inserire il documento in target");
}
```
Esempio con `||` e `!=` (F4:171):
```js
if ($.lastGestionaleEsito == 'OK' || $.lastGestionaleCodice != '') { … } else { … }
```

### 2.3 Switch — `switch (<$.expr>) { case "x": { … } … default: { … } }`  (L2658)
Sintassi:
```js
switch ($.currentAttachment.ext) {
  case "pdf": { /* ramo pdf */ }
  case "docx": { /* ramo docx */ }
  default: { /* ramo di default */ }
}
```
Regole:
- Lo **scrutinee** è un'espressione `$.` puntata (F4:49). Le **etichette case** sono stringhe fra doppi apici; ogni ramo ha il proprio blocco `{ … }`.
- **NESSUN `break`** (F4:50-102). I `case` sono **contenitori-ramo isolati** (L2665): il grafo instrada un solo caso, quindi il `break` non serve. Il break mancante è un **artefatto della proiezione**, NON un fallthrough runtime *(inferenza da L8 + L2665)*.
- **⚠️ Trappola copia-incolla:** se copi questo switch in JS reale, l'assenza di `break` fa **cadere nei case successivi**. Vale solo dentro il DSL.

### 2.4 Stop & Error — `throw new Error("<messaggio>")`  (L2621)
Sintassi:
```js
throw new Error("Non sono riuscito a inserire il documento in target");
```
Regole:
- Messaggio **letterale**. Nessun placeholder `{…}` osservato nel messaggio (F1:666, F2:7, F3:440); ⚠️ `severity` (L852) e i `{placeholder}` nel messaggio (L851) **non sono proiettati**.
- **Interrompe la run** *(inferenza L2621)*. ⚠️ Avvertenza: dentro un `for`, un `throw` nel ramo else rende irraggiungibili gli step a valle e blocca le iterazioni successive (quirk osservato F1:666/F3:440). Se serve solo segnalare un'anomalia senza fermare tutto, usa un Branch senza `throw` (come F2/F4).

### 2.5 onError — `try { … } catch { … }`  (L9)
Sintassi:
```js
try {
  GestionaleSend({ timeoutSeconds: 60, credentialName: "targetcross-test", endpoint: "test" });
} catch {
  throw new Error("WebService non operativo");
}
```
Regole:
- È la **proiezione del concetto `onError`**, NON un blocco a catalogo.
- Il `catch` è **senza binding**: si scrive `catch {`, non `catch (e) {` (F2:6).
- Va tenuto distinto dal `try/catch(e)` che compare **dentro** `CodeJs`, che è JS reale (es. F1:69, F1:627).
- Osservato **una sola volta** (F2:4-8, attorno al `GestionaleSend` di test); lo stesso step altrove è nudo, senza try (F1:5, F3:5).

---

## 3. Annotazioni-commento `// @…`

> ⚠️ **NON DOCUMENTATE come decoratori DSL nel manuale.** I *concetti* `alias` e `continueOnFail` esistono nel manuale (L9), e `maxIterations` esiste come parametro del ForEach (L2712); ma la **forma-decoratore-commento** `// @…` NON è documentata. Sono osservate solo nei flussi esportati. Usale come le usa l'export, ma sappi che non c'è una spec.

Ogni annotazione sta su una riga di commento **immediatamente sopra** lo step/costrutto a cui si applica.

| Annotazione | Significato | Si applica a | Esempi |
|---|---|---|---|
| `// @alias <nome>` | etichetta/nome del nodo | lo step successivo | ovunque in F1/F3/F4; **ASSENTE in F2** (che usa `//` semplice) |
| `// @continueOnFail` | lo step salta l'errore e prosegue (concetto L9) | lo step successivo | F1:613,639,660,671; F2:81,103,213; F3:416,434,445; F4:122,167,187 |
| `// @foreach maxIterations=N` | cap iterazioni del ForEach seguente (param `maxIterations` L2712) | il `for` successivo | **solo F4:6** (`=20`) |
| `// <testo libero>` | descrizione/nota del nodo (proiezione del campo descrittivo) | — | F1:4, F2:16-17, F1:419 |

Esempio combinato (F1:659-661):
```js
// @alias Salva PDF documento su file
// @continueOnFail
FileWrite({ path: "{lastGestionalePdfPath}", content: "{lastGestionalePdfBase64}", append: false, createDirectories: true });
```

---

## 4. CodeJs — API completa

`CodeJs` è l'unico posto dove gira **JS reale**. Mappa su "Code JS Script" del manuale (L1211).

### 4.1 Firma
```js
CodeJs({ <config> }, () => { <corpo JS> });
```
- **Due argomenti:** (1) l'oggetto di config, (2) l'**arrow-function** col corpo. Il campo manuale `code` (L1218) NON si scrive come chiave: È il secondo argomento arrow-function.

### 4.2 Config (chiavi del primo argomento)
| Config | Stato | Esempio |
|---|---|---|
| `outputKey` (L1221) | ✅ osservato | F1:13 `{ outputKey: "cleanupOrdine" }` |
| `mode: "RunOnce"` (L1219) | ✅ osservato | F2:18 (è il default se omesso ⇒ RunOnce) |
| `mode: "RunForEach"` | ⚠️ non osservato | — |
| `outputItemsKey` (L1222) | ✅ osservato | F2:177 `"lastQueryRows"`; F4:14 `"lastItems"` |
| `timeoutMs` (L1220) | ✅ osservato | F4:14 `5000` |
| `continueOnFail` (L1224) | ✅ osservato | F4:14 `false` |
| `inputItemsKey` (L1223) | ⚠️ non osservato | — |

Config più completa osservata (F4:14):
```js
CodeJs({ mode: "RunOnce", timeoutMs: 5000, outputItemsKey: "lastItems", continueOnFail: false, outputKey: "isOrdine" }, () => { … });
```

### 4.3 API interna (dentro l'arrow-function)
| Costrutto | Stato | Esempio |
|---|---|---|
| `stepData` — stato **mutabile** (read/write) | ✅ | F1:43 `delete stepData[k]`; F1:51 `stepData.testataJsonRaw = raw` |
| `$input` — snapshot d'ingresso (**sola lettura**) | ✅ | F1:50 `$input.lastAiOutput`; F4:43 `$input.__loopItem.filePath` |
| `$json` — API alternativa (L1212) | ⚠️ non osservato | — |
| `Object.assign(stepData, result)` — commit di più chiavi in StepData | ✅ | F1:636, F1:655 |
| `stepData.__loopItem` / `$input.__loopItem` — item del ForEach | ✅ | F1:388, F4:43 |
| Lettura difensiva `stepData.X \|\| $input.X \|\| <fallback>` | ✅ | F1:50, F1:618 |

*(inferenza)* `stepData` è lo stato scrivibile, `$input` lo snapshot d'ingresso in sola lettura; il pattern `stepData.X || $input.X || <fallback>` copre la chiave assente. Scrivere in `stepData` (diretto o via `Object.assign`) è ciò che rende una chiave visibile agli step successivi.

Esempio (F4:42-46):
```js
CodeJs({ outputKey: "currentAttachment" }, () => {
  const filePath = $input.__loopItem.filePath || '';
  const ext = filePath.split('.').pop().toLowerCase();
  return { filePath: filePath, ext: ext };
});
```

### 4.4 Forme di `return`
| Forma | Effetto | Esempio |
|---|---|---|
| `return '<stringa>'` | `outputKey` riceve la stringa | F2:52 `return 'ok'`; F4:23 `return label` |
| `return { … }` | `outputKey` riceve l'oggetto (navigabile con `.` nei placeholder) | F1:44 `return { removed }`; F4:45 `return { filePath, ext }` |
| `return [{ json: { … } }]` | popola `outputItemsKey` (items normalizzati L1231) | F2:210 (con `outputItemsKey:"lastQueryRows"` a F2:177) |

---

## 5. Placeholder ed espressioni

Due sistemi distinti: **placeholder `{…}`** nei valori dei parametri (interpolazione di StepData) e **espressioni `$.`** nelle condizioni dei costrutti.

### 5.1 Placeholder `{…}` (nei valori dei parametri)
| Forma | Semantica | Esempio |
|---|---|---|
| `{chiave}` | interpola il **testo** della chiave StepData (L7) | F1:640 `docId: "{lastGestionaleCodice}"` |
| `{oggetto.prop}` / `{chiaveOutput.sotto}` | naviga una sotto-proprietà | F4:53 `"{currentAttachment.filePath}"`; F4:86 `"{xlsxAsText.text}"` |
| `{__loopItem}` | l'item corrente del ForEach (intero) | F1:47 `attachFilePath: "{__loopItem}"` |
| `{__loopItem.campo}` | un campo dell'item corrente | F4:10 `"{__loopItem.subject}"` |
| `{TBD:nome}` | segnaposto da compilare (valore ancora mancante) | F4:188 `["{TBD:email_responsabile_interno}"]` |

**⚠️ Distinzione critica — nome-chiave SENZA graffe.** Alcuni parametri vogliono il **nome** di una chiave, NON la sua interpolazione. Si scrivono come stringa **senza** `{}`:
```js
payloadFromKey: "ordineTarget"                       // F1:614  (nome della chiave da leggere)
payloadFromKey: "orderPayloadResult.targetPayloadJson" // F4:168 (path di chiave)
Markdown({ direction: "mdToHtml", sourceKey: "mailBodyMarkdown", outputKey: "lastMarkdownHtml" }) // F1:708
```
Regola pratica: `payloadFromKey`, `sourceKey`, `outputKey`, `outputItemsKey` e simili prendono un **nome di chiave nudo**; tutti gli altri valori-testo usano `{…}` per interpolare.

**Forme composite osservate:**
- Concatenazione di placeholder: `body: "{lastTargetCrossJson}{lastAiOutput}"` (F1:711); `content: "{timestamp} - {bodyOutput}"` (F1:672).
- Accumulatore auto-referenziale (un SetFields che rilegge la propria chiave): F4:110 `value: "{allAttachmentsText}\n\n--- Allegato: {currentAttachment.filePath} ---\n{currentAttachmentText}"`.
- **SQL — due meccaniche opposte da NON confondere:**
  - `Query.sql` usa placeholder **bound, senza apici**: `WHERE COD_CF = {codCf} AND NUMERO_CONFERMA = {numConfQ}` (F2:82, commento F2:80).
  - `GestionaleSend.filtro` usa placeholder **interpolato dentro apici, con escape manuale** nel `CodeJs` che lo costruisce: `"CF.P_IVA_CF='{piva}'"` (F1:303; escape `c.replace(/'/g,"''")` F1:263-265).

⚠️ non osservate (documentate): pipe-funzione/wildcard nei placeholder `{$.lastQueryRows[*].importo|sum}` (L818); `$` da solo = item corrente in Filter/ForEach (L7).

### 5.2 Espressioni `$.` (nelle condizioni di Branch/Switch)
Nelle **condizioni** dei costrutti si usa `$.<espr>` (L7), valutata a runtime dal motore:
```js
if ($.controllaEsito == true) { … }        // F1:612
switch ($.currentAttachment.ext) { … }      // F4:49  (path puntato ammesso)
if ($.lastGestionaleEsito == 'OK' || $.lastGestionaleCodice != '') { … }  // F4:171
```
- Operatori osservati: `==`, `!=`, `||` (§2.2).
- **⚠️ RHS di `==` non normalizzato.** Il letterale a destra appare in stili incoerenti nei flussi: boolean nudo `true` (F1:612), doppi apici `"ok"` (F2:214), apici singoli `'OK'`/`''` (F4:171), e **bareword NON quotato** `ordine` (F4:27, `if ($.isOrdine == ordine)` — unico caso). Quando **generi** una condizione con stringa a destra, **quotala** (preferisci apici doppi come F2:214); il bareword è un'anomalia sintattica dall'effetto runtime non verificabile *(inferenza)*.

### 5.3 L'`item` del `for` è inerte
Ribadito perché è la trappola più facile: la variabile `item` dichiarata da `for (const item of …)` **non si usa mai** nel corpo. Per accedere all'elemento corrente usa `{__loopItem}` / `{__loopItem.campo}` nei parametri (F1:47, F4:10) oppure `stepData.__loopItem` / `$input.__loopItem` dentro `CodeJs` (F1:388, F4:43). Scrivere `item.qualcosa` non è una forma osservata.

---

> **Per i nomi dei blocchi** (`FileList`, `CodeJs`, `GestionaleSend`, `FileWrite`, `SendEmail`, ecc.) e per la mappa DISPLAY→DSL — ora **tutti confermati** (15 dai flussi, gli altri dal video corso) — consulta l'unica fonte autorevole: `nomi-blocchi.md` (stessa cartella `references/`). Questa guida NON duplica quella tabella.
