# Template CodeJs — Tutti gli step di codice del flusso

## CLEANUP_ordine

Primo step nel ForEach esterno. Azzera tutte le variabili del ciclo precedente
per evitare che dati di un PDF "contaminino" l'elaborazione di quello successivo.

```javascript
// @alias CLEANUP_ordine — azzeramento variabili tra PDF
const keysToClean = [
  'isOrdineClienteFlag', 'lastAiOutput', 'piva', 'stato', 'numConferma',
  'dataConferma', 'ordineId', 'destDesc', 'destIndi', 'destComune',
  'destCap', 'destProv', 'righeOrdine', 'nomeMittente',
  'codCf', 'ragSoc', 'clienteFiltro',
  'profiloCliente', 'codiciAppresi',
  'righePerRicerca', 'articoliTrovati', 'articoliScartati',
  'currentCodArt', 'currentCodArtEscaped', 'currentCodCfEscaped',
  'currentArtFound', 'currentArtCodTc', 'currentArtDes',
  'esito', 'motivoErrore', 'docBody', 'riepilogoOrdine',
  'codCfDoc', 'ragSocDoc',
  'lastGestionaleCodice', 'lastGestionalePdf',
  'lastGestionalePdfPath', 'stampaPdfPath', 'stampaDisponibile',
  'lastTargetCrossJson', 'lastTargetCrossDryRun',
  'mailSubjectFinal', 'mailBodyMarkdown', 'lastMarkdownHtml',
  'logJsonString'
];
const result = {};
for (const key of keysToClean) {
  result[key] = null;
}
return result;
```

---

## classifyOutput

Parsa il JSON di classificazione dall'AI e imposta il flag stringa.

```javascript
// @alias classifyOutput — parsa classificazione AI
let raw = stepData.lastAiOutput || '';
// rimuove eventuali marcatori markdown
raw = raw.replace(/```json/g, '').replace(/```/g, '').trim();
let parsed;
try {
  parsed = JSON.parse(raw);
} catch(e) {
  parsed = { isOrdineCliente: false, motivo: 'JSON non valido: ' + e.message };
}
return {
  isOrdineClienteFlag: parsed.isOrdineCliente === true ? "true" : "false",
  classificazionMotivo: parsed.motivo || ''
};
```

---

## normOutput

Normalizza i dati estratti dall'AI (step 4→5).

```javascript
// @alias normOutput — normalizza dati estratti dal PDF
let raw = stepData.lastAiOutput || '';
raw = raw.replace(/```json/g, '').replace(/```/g, '').trim();
let parsed;
try {
  parsed = JSON.parse(raw);
} catch(e) {
  return { normError: 'JSON non valido: ' + e.message, piva: '', righeOrdine: [] };
}
const t = parsed.testata || {};
const righe = (parsed.righe || []).filter(r => r.codArt && r.codArt.trim() !== '');
return {
  piva:         (t.pIva || '').replace(/[^0-9A-Za-z]/g, '').trim(),
  stato:        t.stato || '',
  nomeMittente: t.nomeMittente || t.ragSoc || '',
  numConferma:  t.numConferma || '',
  dataConferma: t.dataConferma || '',
  ordineId:     t.ordineId || '',
  destDesc:     t.destDesc || '',
  destIndi:     t.destIndi || '',
  destComune:   t.destComune || '',
  destCap:      t.destCap || '',
  destProv:     t.destProv || '',
  righeOrdine:  righe
};
```

---

## clienteOutput

Parsa la risposta TC dopo lookup clienti e salva COD_CF + ragione sociale.

```javascript
// @alias clienteOutput — estrae COD_CF dalla risposta TC
let tcJson;
try {
  tcJson = JSON.parse(stepData.lastTargetCrossJson || '{}');
} catch(e) {
  return { codCf: '', ragSoc: '', clienteErrore: 'JSON TC non valido' };
}
const rows = tcJson.rows || tcJson.Rows || [];
if (!rows.length) {
  return { codCf: '', ragSoc: '', clienteErrore: 'Cliente non trovato per P.IVA: ' + stepData.piva };
}
const r = rows[0];
return {
  codCf:        r.COD_CF || r.cod_cf || '',
  ragSoc:       r.RAG_SOC_CF || r.rag_soc_cf || '',
  clienteErrore: ''
};
```

---

## profiloOutput

Carica la mappa codici-appresa dal profilo JSON del cliente (se esiste).

```javascript
// @alias profiloOutput — carica mappa codici appresa
let profilo;
try {
  profilo = JSON.parse(stepData.lastJsonFile || '{}');
} catch(e) {
  profilo = {};
}
return {
  codiciAppresi: profilo.codiciAppresi || {},   // { "COD_CLIENTE": "COD_ART_TC", ... }
  profiloCliente: profilo
};
```

---

## righePrep

Prepara `righePerRicerca` aggiungendo il codCf e il SQL-escape ad ogni riga.

```javascript
// @alias righePrep — prepara righe per il loop di ricerca articoli
const righe = stepData.righeOrdine || [];
const codCf = stepData.codCf || '';
const righePerRicerca = righe.map(r => ({
  ...r,
  codCf:                codCf,
  currentCodArtEscaped: (r.codArt || '').replace(/'/g, "''"),
  currentCodCfEscaped:  codCf.replace(/'/g, "''")
}));
return {
  righePerRicerca,
  articoliTrovati:  [],
  articoliScartati: [],
  codCfDoc:  codCf,
  ragSocDoc: stepData.ragSoc || ''
};
```

---

## artCheckA (dopo Metodo A)

```javascript
// @alias artCheckA — verifica esito ricerca articolo Metodo A
let tcJson;
try {
  tcJson = JSON.parse(stepData.lastTargetCrossJson || '{}');
} catch(e) {
  tcJson = {};
}
const rows = tcJson.rows || tcJson.Rows || [];
if (rows.length && rows[0].COD_ART) {
  return {
    currentArtFound:  "true",
    currentArtCodTc:  rows[0].COD_ART,
    currentArtDes:    rows[0].DES_ART || stepData.currentArtDesOrig || ''
  };
}
return { currentArtFound: "false", currentArtCodTc: '', currentArtDes: '' };
```

---

## artCheckB (dopo Metodo B — SQL ART_CODICI o ORD_CLI_RIGHE)

```javascript
// @alias artCheckB — verifica esito ricerca articolo Metodo B
let tcJson;
try {
  tcJson = JSON.parse(stepData.lastTargetCrossJson || '{}');
} catch(e) {
  tcJson = {};
}
const rows = tcJson.rows || tcJson.Rows || [];
if (rows.length && rows[0].COD_ART) {
  return {
    currentArtFound:  "true",
    currentArtCodTc:  rows[0].COD_ART,
    currentArtDes:    rows[0].DES_ART || stepData.currentArtDesOrig || ''
  };
}
return { currentArtFound: "false", currentArtCodTc: '', currentArtDes: '' };
```

---

## artAccumulate

Aggiorna `articoliTrovati` / `articoliScartati` dopo ogni riga del ForEach interno.

```javascript
// @alias artAccumulate — accumula risultati ricerca articoli
const trovati   = stepData.articoliTrovati  || [];
const scartati  = stepData.articoliScartati || [];
const loopItem  = stepData.__loopItem || {};   // riga corrente dal ForEach
const found     = stepData.currentArtFound === "true";
const riga = {
  codArtCliente: loopItem.codArt || stepData.currentCodArt || '',
  des:           loopItem.des    || '',
  quant:         loopItem.quant  || 0,
  prezzoLordo:   loopItem.prezzoLordo || 0,
  um:            loopItem.um || '',
  codArtTc:      stepData.currentArtCodTc || '',
  desTc:         stepData.currentArtDes   || ''
};
if (found) {
  trovati.push(riga);
} else {
  scartati.push({ ...riga, motivo: 'Articolo non trovato nel gestionale' });
}
// reset variabili per prossima iterazione
return {
  articoliTrovati:   trovati,
  articoliScartati:  scartati,
  currentArtFound:   null,
  currentArtCodTc:   null,
  currentArtDes:     null,
  lastTargetCrossJson: null
};
```

---

## bodyOutput

Costruisce il body JSON per la chiamata `GestionaleSend documento` e determina
l'esito (ok / anomalia / errore).

```javascript
// @alias bodyOutput — costruisce docBody e determina esito
const trovati  = stepData.articoliTrovati  || [];
const scartati = stepData.articoliScartati || [];
const codCf    = stepData.codCfDoc || stepData.codCf || '';

// Determina esito
let esito, motivoErrore = '', controllaEsito = false;
if (!codCf) {
  esito = 'errore';
  motivoErrore = 'Cliente non trovato (COD_CF mancante)';
} else if (!trovati.length) {
  esito = 'errore';
  motivoErrore = 'Nessun articolo trovato nel gestionale';
} else if (scartati.length > 0) {
  esito = 'anomalia';
  motivoErrore = `${scartati.length} articoli non trovati: ` +
    scartati.map(a => a.codArtCliente).join(', ');
  controllaEsito = true;   // anomalia: creiamo comunque il documento
} else {
  esito = 'ok';
  controllaEsito = true;
}

// Riepilogo per email
const righeRiepilogo = trovati.map(a =>
  `${a.codArtTc} (${a.des}) — q.tà ${a.quant} ${a.um} @ ${a.prezzoLordo}`
).join('\n');

// Costruzione righe documento
const righeDoc = trovati.map(a => ({
  COD_ART:      a.codArtTc,
  DES_ART:      a.desTc || a.des,
  QT_DOC:       a.quant,
  UM_DOC:       a.um,
  PREZZO_LORDO: a.prezzoLordo,
  SC1_DOC:      a.sconto1 || 0,
  SC2_DOC:      a.sconto2 || 0
}));

const docObj = {
  COD_CF:       codCf,
  COD_CAUS_DOC: 'ORDCLI',
  SERIE_DOC:    'ORD-C',
  COD_DEP:      'MAG',
  NUM_CONFERMA: stepData.numConferma || '',
  DATA_CONF:    stepData.dataConferma || '',
  NOTE_DOC:     stepData.ordineId || '',
  DEST_DESC:    stepData.destDesc || '',
  DEST_INDI:    stepData.destIndi || '',
  DEST_COMUNE:  stepData.destComune || '',
  DEST_CAP:     stepData.destCap || '',
  DEST_PROV:    stepData.destProv || '',
  righe:        righeDoc
};

return {
  esito,
  motivoErrore,
  controllaEsito,
  docBody:        JSON.stringify(docObj),
  riepilogoOrdine: righeRiepilogo
};
```

---

## auditPrep

Prepara le righe di audit da inserire con SqlInsert.

```javascript
// @alias auditPrep — prepara righe audit STATO=2
const trovati = stepData.articoliTrovati || [];
const codice  = stepData.lastGestionaleCodice || '';
const righeAudit = trovati.map(r => ({
  COD_DOC:    codice,
  COD_ART_TC: r.codArtTc,
  COD_ART_CF: r.codArtCliente,
  QT_DOC:     r.quant,
  STATO:      2
}));
return { righeAudit };
```

---

## profiloUpdate

Aggiorna la mappa codici appresa e prepara il JSON del profilo da salvare su file.

```javascript
// @alias profiloUpdate — aggiorna profilo cliente con corrispondenze apprese
const trovati      = stepData.articoliTrovati || [];
const profiloOld   = stepData.profiloCliente  || {};
const codiciOld    = profiloOld.codiciAppresi || {};
const codiciNuovi  = { ...codiciOld };

for (const a of trovati) {
  if (a.codArtCliente && a.codArtTc) {
    codiciNuovi[a.codArtCliente] = a.codArtTc;
  }
}

const profiloNew = {
  ...profiloOld,
  codCf:         stepData.codCfDoc || stepData.codCf,
  ragSoc:        stepData.ragSocDoc || stepData.ragSoc,
  aggiornatoIl:  new Date().toISOString(),
  codiciAppresi: codiciNuovi
};

return {
  profiloCliente:    profiloNew,
  profiloJsonString: JSON.stringify(profiloNew, null, 2)
};
```

---

## pdfPathOutput

> ⚠️ **RETTIFICA.** La versione precedente di questo template ricalcolava
> `lastGestionalePdfPath` e preparava il base64 per un `FileWrite`: è l'anti-pattern che ha
> prodotto per giorni allegati illeggibili (FileWrite scrive solo testo; le chiavi `last*` sono
> output del motore e non vanno sovrascritte). Lo step `documenti-stampa` **scrive già il PDF in
> binario** e ne espone il percorso (relativo alla working directory del motore) in
> `lastGestionalePdfPath`. Qui lo si **cattura**, non lo si ricostruisce.

```javascript
// @alias pdfPathOutput — cattura il path della stampa prodotta dal gestionale
const path = ('' + (stepData.lastGestionalePdfPath || $input.lastGestionalePdfPath || ''));
stepData.stampaPdfPath = path;
stepData.stampaDisponibile = path ? 'true' : 'false';
return { path: path, hasPdf: !!path };
```

Allegato email: `attachments: ["{__loopItem}", "{stampaPdfPath}"]`, solo nel ramo
`stampaDisponibile == "true"` (altrimenti un `SendEmail` distinto senza allegato).

---

## logPrep

Serializza lo stato completo per il log JSON.

```javascript
// @alias logPrep — prepara JSON di log
const logObj = {
  timestamp:        new Date().toISOString(),
  pdfFile:          stepData.__loopItem || '',
  esito:            stepData.esito || '',
  motivoErrore:     stepData.motivoErrore || '',
  codCf:            stepData.codCfDoc || '',
  ragSoc:           stepData.ragSocDoc || '',
  lastGestionaleCodice: stepData.lastGestionaleCodice || '',
  articoliTrovati:  stepData.articoliTrovati  || [],
  articoliScartati: stepData.articoliScartati || []
};
return { logJsonString: JSON.stringify(logObj, null, 2) };
```

---

## emailEnrichOutput

Arricchisce l'oggetto email con il codice documento e antepone il blocco esito.

```javascript
// @alias emailEnrichOutput — arricchisce oggetto email
const esito   = stepData.esito || 'errore';
const codice  = stepData.lastGestionaleCodice || '';
const esitoUp = esito.toUpperCase();
const subject = `[${esitoUp}] Ordine ${stepData.numConferma || 'N/D'} — ` +
                `${stepData.ragSocDoc || 'Cliente'} — TC: ${codice || 'N/D'}`;

let intestazione = '';
if (esito === 'ok')      intestazione = `✅ **DOCUMENTO CREATO: ${codice}**\n\n`;
if (esito === 'anomalia') intestazione = `⚠️ **ANOMALIA — documento NON creato**\n\n`;
if (esito === 'errore')   intestazione = `❌ **ERRORE — documento NON creato**\n\n`;

const bodyConIntestazione = intestazione + (stepData.lastAiOutput || '');

return {
  mailSubjectFinal:  subject,
  mailBodyMarkdown:  bodyConIntestazione
};
```

---

## filtroEmailPdf (solo trigger email)

Filtra le email e raccoglie solo gli allegati PDF.

```javascript
// @alias filtroEmailPdf — filtra email con allegati PDF
const emails = stepData.lastEmails || [];
const pdfDaSalvare = [];

for (const email of emails) {
  const allegati = email.attachments || email.allegati || [];
  for (const all of allegati) {
    const nome = all.filename || all.name || '';
    if (nome.toLowerCase().endsWith('.pdf')) {
      pdfDaSalvare.push({
        filename: nome,
        content:  all.content || all.data || ''  // base64
      });
    }
  }
}

return {
  pdfDaSalvare,
  emailConPdf: pdfDaSalvare.length
};
```

---

## sogliaOutput (variante avanzata di bodyOutput con soglia % risolta)

Pattern ricavato dal flusso reale CLI-A Ordine Cliente v1.4.1 (vedi
`../dsl/pattern.md` §A13 e `esempi.md` §6): invece di
bloccare il documento non appena manca un articolo, calcola la percentuale di
righe risolte ed **accetta un ordine parziale** sopra una soglia configurabile.
Usare al posto di `bodyOutput` quando è impostato `usaSogliaPercentuale = sì`.

```javascript
// @alias sogliaOutput — calcola % risolta e decide se creare comunque il documento
const trovati  = stepData.articoliTrovati  || [];
const scartati = stepData.articoliScartati || [];
// Esclude dal conteggio le righe non di business (es. righe NOTA/commento):
// altrimenti abbassano artificialmente la percentuale risolta.
const righeRilevanti = trovati.length + scartati.filter(r => !/^Riga\b|^NOTA\b/i.test(r.motivo || '')).length;
const soglia = (+(stepData.minPercentualeRisoltePerCreare || 60));
const resolvedPct = righeRilevanti > 0 ? Math.round((trovati.length / righeRilevanti) * 100) : 0;

let esito, motivoErrore = '', controllaEsito = false;
if (!stepData.codCfDoc) {
  esito = 'errore';
  motivoErrore = 'Cliente non trovato (COD_CF mancante)';
} else if (!trovati.length) {
  esito = 'errore';
  motivoErrore = 'Nessun articolo trovato nel gestionale';
} else if (resolvedPct >= soglia) {
  esito = scartati.length > 0 ? 'anomalia' : 'ok';   // 'anomalia' = creato PARZIALE
  controllaEsito = true;
  if (scartati.length > 0) {
    motivoErrore = `Ordine parziale (${resolvedPct}% risolto, soglia ${soglia}%): ` +
      `${scartati.length} articoli non trovati: ` + scartati.map(a => a.codArtCliente).join(', ');
  }
} else {
  esito = 'errore';
  motivoErrore = `Percentuale risolta insufficiente: ${resolvedPct}% (soglia ${soglia}%). ` +
    `Articoli non trovati: ` + scartati.map(a => a.codArtCliente).join(', ');
}

return { esito, motivoErrore, controllaEsito, resolvedPct, sogliaUsata: soglia };
```

---

## escSql (helper di escape apici riusabile)

Da richiamare prima di comporre QUALSIASI filtro SQL dinamico verso
`GestionaleSend`/Query — un apice non escapato nella ragione sociale o nel
codice articolo genera un errore di sintassi o, peggio, un filtro sbagliato.

```javascript
// @alias escSql — escape apici per filtro SQL dinamico
function escSql(v) {
  return ('' + (v == null ? '' : v)).replace(/'/g, "''");
}
return {
  currentCodArtEscaped: escSql(stepData.currentCodArt),
  currentCodCfEscaped:  escSql(stepData.codCf),
  ragSocEscaped:        escSql(stepData.nomeMittente)
};
```

---

## parseNumeroTC (numeri verso TcRestAPI come numeri JSON)

TcRestAPI (v1.5.3) raccomanda **numeri JSON** con punto decimale e senza virgolette per
quantità, prezzi, sconti, pesi e flag; le stringhe sono convertite con regole che
dipendono dall'endpoint (`"1.000"` diventa 1 sui documenti). I PDF ordine arrivano spesso
con formati misti (punto, virgola, valuta, migliaia). Normalizza SEMPRE prima di scrivere
nel body verso TargetCross e lascia che sia `JSON.stringify` a serializzare il numero.

```javascript
// @alias parseNumeroTC — normalizza numero PDF -> Number per il body TC
function parseNumeroLoose(raw) {
  let s = ('' + (raw ?? '')).trim().replace(/[^\d,.\-]/g, ''); // via valuta/unità (es. "2,43/EA")
  if (!s) return 0;
  const hasComma = s.includes(','), hasDot = s.includes('.');
  if (hasComma && hasDot) {
    // entrambi: l'ultimo separatore incontrato è il decimale
    s = s.lastIndexOf(',') > s.lastIndexOf('.')
      ? s.replace(/\./g, '').replace(',', '.')
      : s.replace(/,/g, '');
  } else if (hasComma) {
    s = s.replace(',', '.');
  } else if (hasDot) {
    // solo punti: "1.000" / "1.000.000" = migliaia (gruppi da 3 cifre), "75.6" = decimale
    if (/^\-?\d{1,3}(\.\d{3})+$/.test(s)) s = s.replace(/\./g, '');
  }
  const n = (+(s));
  return ((n) === (n) && (n) !== Infinity && (n) !== -Infinity) ? n : 0;
}
function toTcNum(n, decimals = 4) {
  return (+((+(n)).toFixed(decimals)));   // Number, NON stringa: JSON.stringify -> 5.5
}
// Uso: riga = { COD_ART, QUANT_RIGA: toTcNum(parseNumeroLoose(q)), PREZZO_LORDO_VU1: toTcNum(parseNumeroLoose(p)) }
return { esempioParsed: parseNumeroLoose('2,43/EA'), esempioMigliaia: parseNumeroLoose('1.000'), esempioTc: toTcNum(2.43) };
```

⚠️ Euristica sul solo punto: `"1.000"` è letto come mille, ma un prezzo `1.000` con tre
decimali reali sarebbe ambiguo. Se i PDF del cliente usano tre decimali, decidi per
cliente (parametro) invece di affidarti all'euristica.

---

## claimFileClaim (claim atomico anti-doppia-elaborazione)

Da usare come primi step del ForEach quando l'agente gira su schedulazione e
può sovrapporsi a run precedenti non ancora terminate (crash, agente lento).
Vedi `../dsl/pattern.md` §A12.

```javascript
// @alias claimPrep — prepara correlationId e path "in lavorazione"
const pdfPath = ('' + (stepData.__loopItem || ''));
const fileName = pdfPath.split(/[\\/]/).pop();
return {
  fileCorrelationId: fileName + '-' + stepData.agentVersion,  // stabile, NON timestamp/GUID
  inputFileName: fileName,
  processingPath: '{cartellaProcessing}\\' + fileName          // sostituire {cartellaProcessing}
};
```

Poi: `FileMove` con `idempotencyKey: "ordcli-claim-{fileCorrelationId}"` verso
`processingPath`; `SqlUpdate` che chiude gli eventuali orfani
`STATO='IN_ELABORAZIONE'` con lo stesso `FILE_NAME` ma `CORRELATION_ID`
diverso da quello corrente; `SqlInsert` di apertura log con verifica
`lastInsertRowCount === 1` (altrimenti `throw new Error('Claim concorrente su ' + fileCorrelationId)`,
fuori da un ForEach esterno o gestito con `itemErrorSteps` se dentro).
