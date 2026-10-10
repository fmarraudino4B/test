# Gotcha noti — Cause, Sintomi e Fix verificati

Questa pagina raccoglie tutti i bug e le trappole incontrate nello sviluppo del
flusso WorkForce ordini clienti su TargetCross, con cause esatte e fix testati.

---

## 1. FileWrite — bare variable non sostituita nel path

> ⚠️ **RETTIFICA (collaudo DECOX).** Il sintomo descritto qui è reale, ma il contesto (salvare
> la stampa PDF con `FileWrite`) è un anti-pattern: `FileWrite` scrive solo testo e il PDF
> risultante non si apre. Per la stampa usa `lastGestionalePdfPath` prodotto da
> `documenti-stampa` (vedi `code-templates.md` § pdfPathOutput). La regola "mai l'intera
> variabile come `path`" resta valida per i FileWrite di testo (log, heartbeat).

### Sintomo
```json
"lastFileWritten": "{lastGestionalePdfPath}",
"lastFileBytes": 192068
```
Il connettore `SendEmail` poi fallisce con:
```
allegato 'E:\DOCUMENTI_CLI\Elaborati\OrdCli_2026-ORD-C-0001828.pdf' non trovato
```

### Causa
Il template engine di WorkForce NON sostituisce `{var}` quando è l'intera
stringa del parametro `path`. Il file viene scritto su un path letteralmente
chiamato `{lastGestionalePdfPath}` (probabilmente nella working dir del processo)
e `lastFileBytes` riporta la dimensione del contenuto, non la conferma che il
file sia scritto nel posto giusto.

### Fix
Separare il path completo dal solo filename in `pdfPathOutput`, poi
**embeddare il filename** in una stringa con la directory hardcoded:

```javascript
// pdfPathOutput — produce ENTRAMBI
const fileName = 'OrdCli_' + codice + '.pdf';
const filePath = 'E:\\DOCUMENTI_CLI\\Elaborati\\' + fileName;
return {
  lastGestionalePdfPath:     filePath,   // path completo → allegato SendEmail
  lastGestionalePdfFileName: fileName    // solo filename → embedded in FileWrite
};
```

```javascript
// FileWrite — usa il filename embedded nella stringa del path
FileWrite({
  path: "E:\\DOCUMENTI_CLI\\Elaborati\\{lastGestionalePdfFileName}",  // ✓ embedded
  content: "{lastGestionalePdfBase64}",
  append: false,
  createDirectories: true
});
```

**Regola generale**: ogni volta che `path` in FileWrite è l'intera variabile
(`"{var}"`), la sostituzione non avviene. Metti SEMPRE almeno la directory
hardcoded prima del `{filename}`.

---

## 2. Double-path in FileWrite (variante del bug 1)

### Sintomo
File scritto in un path annidato come:
`E:\DOCUMENTI_CLI\PDF\E:\DOCUMENTI_CLI\Elaborati\OrdCli_....pdf`

### Causa
```javascript
// SBAGLIATO: lastGestionalePdfPath contiene già il path completo
FileWrite({ path: "E:\\DOCUMENTI_CLI\\PDF\\{lastGestionalePdfPath}" })
// → "E:\DOCUMENTI_CLI\PDF\" + "E:\DOCUMENTI_CLI\Elaborati\OrdCli_...pdf"
```

### Fix
Stessa soluzione del gotcha 1: usa solo il filename nella variabile e
la directory hardcoded nel path di FileWrite.

---

## 3. JsonToFile rifiuta path assoluti Windows

### Sintomo
```
JsonToFile: path non valido: Path assoluto non ammesso:
E:\DOCUMENTI_CLI\log\Semplifica GAZZA Ordine Cliente_20260710121906.json
```

### Causa
Il connettore `JsonToFile` di WorkForce blocca qualsiasi path che inizia
con lettera di drive (`C:\`, `E:\`, ecc.).

### Fix
Non usare `JsonToFile` per path assoluti. Pattern sostitutivo:

```javascript
// Step 1 — CodeJs: serializza il JSON in stringa
return { logJsonString: JSON.stringify(logObj, null, 2) };

// Step 2 — FileWrite con @continueOnFail
FileWrite({
  path: "E:\\DOCUMENTI_CLI\\log\\{agentName}_{timestamp}.json",
  content: "{logJsonString}",   // qui content è embedded come valore stringa
  append: false,
  createDirectories: true
});
```

Entrambi i passi con `@continueOnFail` (il log non deve bloccare il flusso).

---

## 4. lastTargetCrossDryRun — TC non esegue nulla

### Sintomo
- Tutti gli articoli risultano `currentArtFound: false`
- Il cliente non viene trovato (`codCf: ''`)
- Nessun documento viene creato
- L'output JSON mostra: `"lastTargetCrossDryRun": true`

### Causa
La credential `targetcross-test` ha il flag `dryRun: true` attivo. In questa
modalità WorkForce simula tutte le chiamate GestionaleSend senza eseguirle
davvero: risponde sempre con payload vuoto.

### Fix
Aprire la configurazione della credential `targetcross-test` in WorkForce e
disabilitare il flag `dryRun` (impostarlo a `false` o rimuoverlo).

---

## 5. GestionaleSend articoli — restituisce COD_SECONDARIO invece di COD_ART

### Sintomo
```json
"currentArtCodTc": "00123456",  // ← codice cliente, non TC!
```
Il documento ORD_CLI viene creato con codici articolo errati.

### Causa
Versioni precedenti del filtro usavano un JOIN diretto su ART_CODICI senza
tornare alla tabella ART_ANA per il COD_ART principale.

### Fix
Usare la subquery che filtra ART_ANA tramite ART_CODICI:

```javascript
GestionaleSend({
  endpoint: "articoli",
  filtro: "(ART_ANA.COD_ART='{currentCodArtEscaped}') OR " +
          "(ART_ANA.COD_ART LIKE '%{currentCodArtEscaped}%') OR " +
          "ART_ANA.COD_ART IN (" +
          "  SELECT COD_ART FROM ART_CODICI " +
          "  WHERE ART_CODICI.FLAG_COD_CF=1 " +
          "  AND COD_SECONDARIO_ART LIKE '%{currentCodArtEscaped}%' " +
          "  AND (ART_CODICI.TIPO_CODICE='{currentCodCfEscaped}' " +
          "       OR LEN('{currentCodCfEscaped}')=0)" +
          ")",
  colonne: "COD_ART; DES_ART",
  filtroRaw: "true",
  timeoutSeconds: 60
});
```

Con `colonne: "COD_ART; DES_ART"` la risposta è su ART_ANA → restituisce
sempre il COD_ART della tabella principale, mai il codice secondario.

---

## 6. Variabili stepData non azzerati tra iterazioni ForEach

### Sintomo
Il secondo PDF del batch eredita dati del primo: il cliente viene trovato
anche se la P.IVA è diversa, o articoli di un ordine compaiono in un altro.

### Causa
WorkForce mantiene le variabili stepData tra iterazioni del ForEach.
Se uno step non scrive una variabile (es. perché il branch non si attiva),
il valore della variabile resta quello dell'iterazione precedente.

### Fix
Inserire uno step `CLEANUP_ordine` come primo step dentro il ForEach.
Vedi `code-templates.md` § CLEANUP_ordine per il codice completo.

---

## 7. Template substitution in filtro GestionaleSend

### Sintomo
La query TC non filtra per il valore corretto, oppure lancia un errore di
sintassi SQL con la stringa `{piva}` letterale.

### Causa
Se il filtro è costruito in modo che la variabile sia ambigua rispetto
al template engine (es. concatenazione in JSON), la sostituzione non avviene.

### Fix
Assicurarsi che le variabili nel filtro siano nel formato `'{varName}'`
(con virgolette singole per i valori stringa SQL) e che il filtro sia
una stringa con la variabile embedded, non l'intera stringa:

```javascript
// CORRETTO
GestionaleSend({ filtro: "CF.P_IVA_CF='{piva}'" })

// ATTENZIONE: se piva contiene apici → SQL injection / errore
// Usare sempre l'escaped version nelle query dinamiche:
GestionaleSend({ filtro: "CF.P_IVA_CF='{pivaEscaped}'" })
// dove pivaEscaped = piva.replace(/'/g, "''")
```

---

## 8. FileWrite con content che è l'intera variabile

### Sintomo
Il file viene scritto vuoto, o il contenuto è il testo letterale `{logJsonString}`.

### Causa
Come per `path`, se `content: "{logJsonString}"` è l'intera stringa del parametro,
potrebbe non essere sostituita in alcuni contesti WorkForce.

### Fix
Verificare che la sostituzione funzioni. In caso di problema, usare il pattern
`contentFromKey` se supportato dal connettore, oppure aggiungere un carattere
neutro (es. uno spazio o un newline finale garantito dal CodeJs) per rendere
il contenuto non-bare. In genere per `content` la sostituzione funziona;
il problema si manifesta quasi esclusivamente con il parametro `path`.

---

## 9. Documento ORD_CLI duplicato dopo un retry/riavvio dell'agente

### Sintomo
Lo stesso ordine cliente compare due volte su TargetCross dopo che l'agente
è stato riavviato, o dopo un trigger di polling che ha rielaborato lo stesso
PDF (es. il file non era ancora stato spostato fuori dalla cartella input
quando l'agente è ripartito).

### Causa
`GestionaleSend endpoint:"documento"` non ha protezione di default contro
l'esecuzione doppia: se il flusso rigira sullo stesso ordine, crea un secondo
documento ORD_CLI identico.

### Fix
Due livelli di protezione, entrambi consigliati in produzione (vedi
`../dsl/pattern.md` §A8/§A12, confermati dal flusso
reale GAZZA Ordine Cliente v1.4.1):
1. **Idempotenza sullo step di creazione**: `idempotencyKey` costruita da un
   identificativo di business stabile, es. `hash(codCf + '|' + numeroOrdine + '|' + dataOrdine)`
   — mai timestamp/GUID.
2. **Pre-check duplicato prima di creare**: una `GestionaleSend endpoint:"documenti"`
   (o `lookup`) che cerca se esiste già un ORD_CLI con lo stesso
   `NUM_ORDINE_CLIENTE`/`DATA_ORDINE_CLIENTE` per quel cliente, e se trovato
   salta la creazione (`esito: "duplicato"`) invece di richiamare `documento`.

```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "documento",
  resource: "ORD_CLI",
  body: "{docBody}",
  idempotencyKey: "gazza-ord-{orderBusinessKey}",
  idempotencyGroup: "gazza-doc-creation",
  timeoutSeconds: 60
});
```

---

## 10. Numeri persi/arrotondati male verso TcRestAPI (formato italiano)

### Sintomo
Prezzi o quantità inviati a TargetCross risultano 10, 100 o **1000 volte** più
piccoli/grandi del previsto (tipico: `1.000` registrato come `1`), oppure il body
viene rifiutato con errore di formato o «Data documento non valida».

### Causa
I valori estratti dal PDF via AI o calcolati in JS arrivano in formati misti
(`2,43/EA`, `1.234,56`, `1.000`, `75.6`). Dalla doc TcRestAPI **v1.5.3** («Formato di
numeri e date») il formato raccomandato è il **numero JSON** con punto decimale e senza
virgolette (`5.5`, `10`, `0`), indipendente dalle impostazioni del server. Le stringhe
sono accettate sugli endpoint dei documenti (`documento`, `documento-righe` POST/PATCH,
PATCH `documento`) con queste regole: un solo separatore = decimale (`"5.50"`/`"5,50"` →
5,5); punto e virgola insieme → decimale è l'ultimo (`"1.234,50"` → 1234,5); più separatori
uguali → migliaia (`"1.000.000"`); ⚠️ **`"1.000"` → 1, non 1000**. Negli altri endpoint
(anagrafiche, articoli, distinte, listini) e nei `LOTTI` le stringhe sono convertite con le
impostazioni del server, quindi un punto può essere letto come migliaia o come decimale a
seconda dell'installazione. (In v1.5.0 gli esempi mostravano le stringhe, `"5.00"`, e
`"75,6"` sull'anagrafica articolo: la raccomandazione è cambiata.)

### Fix
1. Normalizza SEMPRE con un parser tollerante PRIMA di scrivere nel body (template
   `parseNumeroTC` in `code-templates.md`) e restituisci un **Number**, non una stringa.
2. Costruisci il body con `JSON.stringify` così i numeri restano numeri JSON.
3. Non produrre mai separatori delle migliaia (`1.000`) né con punto né con virgola.
4. Se un flusso legacy invia stringhe con la virgola decimale, sui documenti è ancora
   valido; per anagrafiche/articoli/listini verifica in collaudo con l'installazione
   del cliente oppure passa a numeri JSON.
5. Le date solo nei formati `GG/MM/AAAA`, `GG.MM.AAAA`, `GG-MM-AAAA`, `AAAA-MM-GG`, anno a
   4 cifre: `04/05/26` e `31/02/2026` sono rifiutate.
   ⚠️ **RETTIFICA (run reali, handoff 10/10/2026):** nonostante la documentazione, con date ISO
   il gestionale ha registrato sempre il giorno 20. Usa **solo `gg/mm/aaaa`**.

---

## 11. `ERROR_DETAIL` troncato o insert fallito sulla tabella di log/audit

### Sintomo
Un `SqlInsert`/`SqlUpdate` su una tabella di log fallisce con un errore di
troncamento dati, oppure il messaggio d'errore salvato è tagliato a metà
frase.

### Causa
Le colonne di dettaglio errore sono tipicamente `NVARCHAR(4000)` o simili;
un messaggio d'errore lungo (stack trace, risposta JSON di un'API esterna)
supera il limite e SQL Server rifiuta l'INSERT (o lo tronca silenziosamente
a seconda delle impostazioni).

### Fix
Tronca esplicitamente in `CodeJs` PRIMA di scrivere (es. 3990 caratteri per
una colonna `NVARCHAR(4000)`, lasciando margine), e se serve il dettaglio
completo salvalo in una colonna separata `NVARCHAR(MAX)` (es. `DETAIL_JSON`)
non soggetta allo stesso limite:
```javascript
let error = String(stepData.__lastItemErrorMessage || 'Errore non specificato');
if (error.length > 3990) error = error.slice(0, 3987) + '...';
```

---

## 12. `STRING_SPLIT` non disponibile sul DB del gestionale

### Sintomo
Una query SQL che usa `STRING_SPLIT(...)` fallisce con "nome di funzione non
valido" su alcune installazioni del gestionale, ma funziona su altre.

### Causa
`STRING_SPLIT` richiede `COMPATIBILITY_LEVEL >= 130` (SQL Server 2016+); alcune
installazioni TargetCross più datate girano su un database con compatibility
level inferiore.

### Fix
Non dare per scontata la disponibilità di `STRING_SPLIT` in query destinate a
girare su installazioni cliente sconosciute. Alternative portabili: split via
cast a XML (`CAST('<x>' + REPLACE(@lista, ',', '</x><x>') + '</x>' AS XML)`
con `.nodes('/x')`), oppure spostare lo split lato `CodeJs` (array JS) e
costruire il filtro SQL con più condizioni `OR`/`IN (...)` già espanse.

---

## 13. Doppia elaborazione dello stesso file dopo un crash a metà run

### Sintomo
Lo stesso PDF viene elaborato due volte (due documenti ORD_CLI, due mail di
notifica) perché l'agente si è interrotto (crash, riavvio) mentre il file era
ancora nella cartella di input.

### Causa
Un `FileList` + `ForEach` senza "claim" non impedisce a un secondo run
(schedulato o riavviato) di rileggere lo stesso file se non è ancora stato
spostato fuori dalla cartella sorgente.

### Fix
Applica il pattern "claim atomico" prima di iniziare a lavorare un item:
sposta il file (con `FileMove` idempotente) verso un'area "in lavorazione"
come primissimo step del ForEach, e chiudi esplicitamente eventuali righe di
log rimaste `IN_ELABORAZIONE` per lo stesso nome file ma con un
`CORRELATION_ID` diverso da quello del run corrente, prima di aprirne una
nuova. Vedi il template `claimFileClaim` in `code-templates.md` e
`../dsl/pattern.md` §A12.
