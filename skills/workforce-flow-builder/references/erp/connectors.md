# Connettori WorkForce — Parametri esatti

## GestionaleSend

Connettore principale per tutte le operazioni TargetCross (ERP via **TcRestAPI
v1.5.3**, doc ufficiale Four Infolab srl del 1 ottobre 2026). Reference completa
del blocco: `../dsl/blocchi/integrazioni.md`. Qui sotto
solo gli usi applicati al caso "ordine cliente".

> **Novità v1.5.0** rilevanti per l'ordine cliente: nuovi endpoint `documento-righe`
> (aggiunge righe a un ORD_CLI esistente), `documento-chiudi` e `documento-righe-chiudi`
> (chiudono l'ordine o la singola riga dopo l'evasione) — vedi sezione dedicata sotto.
> L'endpoint `lookup` è **deprecato** (non più nella doc ufficiale): i flussi legacy
> che lo usano restano operativi, ma per i nuovi preferire le ricerche strutturate.
>
> **Novità v1.5.3** (rispetto a v1.5.0): (1) **numeri JSON** nel body documento invece
> di stringhe, con regole precise sulle stringhe (`"1.000"` = 1!) — vedi
> `gotchas.md` §10; (2) flag di riga `NO_RICALC_PRZ`/`NO_RICALC_SCONTI` per bloccare
> prezzo/sconti concordati; (3) **controlli sui dati** prima della creazione, con
> messaggi `Esito` specifici (causale, cliente/fornitore, pagamento, data, UM, sconto
> > 100); (4) nuovi endpoint REST `PATCH`/`DELETE` su documento e righe e `POST
> /datamining` — vedi la sezione «Variazione, cancellazione e datamining» sotto, con
> la **riserva** che il blocco `GestionaleSend` potrebbe non esporli ancora.

### Parametri comuni

| Parametro | Tipo | Descrizione |
|---|---|---|
| `credentialName` | string | Nome credential TC in WorkForce (es. `targetcross-test`) |
| `endpoint` | string | Operazione TC — vedi tabella endpoint sotto (mappa 1:1 sul path REST TcRestAPI: `test`→`/test`, `documento`→`/documento`, ecc.) |
| `resource` | string | Per `documento`/`documento-righe`/`documenti-stampa`/`documenti`: tipo documento (`ORD_CLI`, `DDT_CLI`, `FATT_CLI`, `ORD_FOR`, `DDT_FOR`, `FATT_FOR`, `MAG_CAR`, `MAG_SCAR` — confermati in TcRestAPI v1.5.0 §4.5). Per `documento-chiudi`/`documento-righe-chiudi`: `ORD_CLI`, `ORD_FOR`, `DDT_ALL`, `APP_FOR`. Per clienti/fornitori/contatti/articoli è automatica (`CF`/`ART_ANA`). |
| `filtro` | string | Clausola WHERE con variabili embedded |
| `filtroRaw` | `"true"` | Passa il filtro grezzo senza escape aggiuntivo (obbligatorio per subquery SQL) |
| `colonne` | string | Colonne da restituire, separate da `;` (es. `COD_ART; DES_ART`) |
| `body` / `payloadFromKey` / `payloadTemplate` | string | JSON del payload per gli endpoint di creazione (`documento`, `cliente`, `fornitore`, `contatto`, `articolo`, `articolo-distinta`, `listino-versione`) |
| `query` / `sql` | string | ⚠️ SQL grezzo (solo SELECT) per endpoint `lookup` — **deprecato in v1.5.0** (solo flussi legacy) |
| `docId` | string | DOC_ID per `documenti-stampa` e (v1.5.0) `documento-righe`/`documento-chiudi` — path REST `{pDocId}` |
| `docRigaId` | string | DOC_RIGA_ID per `documento-righe-chiudi` (v1.5.0) — path REST `{pDocRigaId}` |
| `ricalcolo` | `"0"`/`"1"` | Solo `documento-righe` (v1.5.0): `1` ricalcola i totali a fine inserimento (query `pRicalcolo`) |
| `timeoutSeconds` | number | Timeout in secondi (60 per articoli/documento, 30 per clienti; TcRestAPI accetta fino a 300) |

### Variabili prodotte

| Variabile | Contenuto |
|---|---|
| `lastTargetCrossJson` | Risposta JSON serializzata (usare `JSON.parse()` in CodeJs) |
| `lastTargetCrossDryRun` | `true` se modalità dry-run attiva (nessuna scrittura TC) |
| `lastGestionaleCodice` | Codice/COD_CF/COD_ART creato (endpoint di creazione: `documento`, `cliente`, `fornitore`, `contatto`, `articolo`, `articolo-distinta`, `listino-versione`) |
| `lastGestionalePdf` | Base64 del PDF (solo endpoint `documenti-stampa`) |
| `lastGestionaleStato` / `lastGestionaleEsito` | `"Stato"`/`"Esito"` grezzi della risposta REST TcRestAPI (`"OK"`/`"KO"` + messaggio) |

### Endpoint disponibili

#### `clienti` — lookup anagrafica clienti
```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "clienti",
  filtro: "CF.P_IVA_CF='{piva}'",
  timeoutSeconds: 30
});
// Fallback per nome:
// filtro: "CF.RAG_SOC_CF LIKE '%{nomeMittente}%'"
```

Risposta `lastTargetCrossJson`:
```json
{ "rows": [{ "COD_CF": "CLI001", "RAG_SOC_CF": "Rossi S.r.l." }] }
```

#### `articoli` — ricerca articoli (con subquery ART_CODICI)
```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "articoli",
  filtro: "(ART_ANA.COD_ART='{currentCodArtEscaped}') OR (ART_ANA.COD_ART LIKE '%{currentCodArtEscaped}%') OR ART_ANA.COD_ART IN (SELECT COD_ART FROM ART_CODICI WHERE ART_CODICI.FLAG_COD_CF=1 AND COD_SECONDARIO_ART LIKE '%{currentCodArtEscaped}%' AND (ART_CODICI.TIPO_CODICE='{currentCodCfEscaped}' OR LEN('{currentCodCfEscaped}')=0))",
  colonne: "COD_ART; DES_ART",
  filtroRaw: "true",
  timeoutSeconds: 60
});
```

**Importante**: `filtroRaw: "true"` è obbligatorio per le subquery SQL.
`colonne: "COD_ART; DES_ART"` garantisce che la risposta contenga
sempre il COD_ART della tabella ART_ANA (non il codice secondario).

#### `lookup` — query SQL arbitraria (SELECT di sola lettura) — ⚠️ DEPRECATO in v1.5.0

⚠️ **DEPRECATO in v1.5.0**: la doc ufficiale TcRestAPI non riporta più l'endpoint
`/lookup` (era presente fino a v1.4.5). I flussi legacy (es. CLI-A) che lo usano
restano operativi, ma **non usarlo in nuovi flussi**: preferire le ricerche
strutturate (`articoli`/`documenti` con `filtro`/`filtroRaw`). Se serve una query
grezza, verificare prima con il produttore dell'ERP se `/lookup` resta supportato lato server.
Nota storica: il nome endpoint corretto è `lookup`, non `sql` (il parametro del
blocco che porta la query resta `sql`).
```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "lookup",
  sql: "SELECT TOP 1 ART_ANA.COD_ART FROM ART_ANA INNER JOIN ORD_CLI_RIGHE ON ART_ANA.COD_ART = ORD_CLI_RIGHE.COD_ART AND ART_ANA.FLAG_OBSOLETO = 0 AND ART_ANA.FLAG_INATTIVO = 0 AND ORD_CLI_RIGHE.COD_CF = '{currentCodCfEscaped}' AND ORD_CLI_RIGHE.COD_ART LIKE '%{currentCodArtEscaped}%'",
  timeoutSeconds: 60
});
```

#### `documento` — crea documento ORD_CLI
```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "documento",
  resource: "ORD_CLI",
  body: "{docBody}",   // JSON serializzato da bodyOutput
  timeoutSeconds: 60
});
// produce: lastGestionaleCodice
```

Struttura minima del body, per TcRestAPI v1.5.3 (il `docBody` deve contenere,
in aggiunta ai campi già usati in questa skill, anche `COD_CAUS_DOC` e —
per i campi di riga — `QUANT_RIGA`/`PREZZO_LORDO_VU1`/`SCONTO_1..2` secondo lo
schema ufficiale; vedi `../dsl/blocchi/integrazioni.md`
per lo schema REST completo):
```json
{
  "COD_CF": "CLI001",
  "COD_CAUS_DOC": "ORDCLI",
  "SERIE_DOC": "ORD-C",
  "COD_DEP": "MAG",
  "righe": [
    { "COD_ART": "ART001", "QT_DOC": 10, "UM_DOC": "PZ", "PREZZO_LORDO": 25.00 }
  ]
}
```

**Numeri, date e controlli (v1.5.3).** Prezzi, quantità e sconti vanno nel body come
**numeri JSON** (`25.5`, non `"25,5"`): se li componi in `CodeJs` e serializzi con
`JSON.stringify` lo sono già. Date (`DATA_DOC`) come stringa `GG/MM/AAAA`,
`GG.MM.AAAA`, `GG-MM-AAAA` o `AAAA-MM-GG` con anno a 4 cifre. Se vuoi che il prezzo
concordato nell'ordine del cliente non venga ricalcolato da Target nelle variazioni
successive, aggiungi sulla riga `NO_RICALC_PRZ: 1` (e `NO_RICALC_SCONTI: 1`); se
assenti valgono 0. Il documento **non viene creato** se un controllo fallisce
(causale incoerente col tipo, `COD_CF` assente o non coerente con la causale,
`COD_PAGA` inesistente, `DATA_DOC` non valida, `COD_ART` inesistente, `QUANT_RIGA`
= 0, `UM` non dell'articolo, sconto > 100): il motivo è in `lastGestionaleEsito` —
intercettalo con un Branch su `lastGestionaleStato == "KO"` per distinguere errori
dati da errori di sistema (HTTP 400 = autenticazione, 500 = errore interno).

#### `documenti-stampa` — genera PDF del documento
```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "documenti-stampa",
  resource: "ORD_CLI",
  docId: "{lastGestionaleCodice}",   // DOC_ID del documento appena creato, NON un filtro SQL
  report: "",                        // opzionale: nome report specifico
  timeoutSeconds: 60
});
// produce: lastGestionalePdf (base64)
```
**Correzione rispetto a versioni precedenti di questa pagina**: il body REST di
`/documenti-stampa` è `{"DOC_ID": "...", "REPORT": "..."}` (TcRestAPI v1.5.3 §5),
non un filtro SQL — usa il parametro `docId` del blocco, non `filtro`.

---

#### `documento-righe` / `documento-chiudi` / `documento-righe-chiudi` — gestione ordine post-creazione 🆕 v1.5.0
Utili nel ciclo ordine cliente per aggiungere righe a un ORD_CLI già creato o per
chiuderlo dopo l'evasione. Reference completa: `../dsl/blocchi/integrazioni.md`.
```javascript
// Aggiunge righe a un ORD_CLI esistente (transazione atomica)
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "documento-righe",
  resource: "ORD_CLI",
  docId: "{lastGestionaleCodice}",   // DOC_ID dell'ordine → path {pDocId}
  ricalcolo: "1",                     // ricalcola i totali a fine inserimento
  payloadFromKey: "righeAggiuntiveJson" // { "RIGHE": [ { "COD_ART":"...", "QUANT_RIGA":"..." } ] }
});
// produce: lastGestionaleCodice = DOC_RIGA_ID inseriti, separati da "/"

// Chiude tutte le righe dell'ordine
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "documento-chiudi",
  resource: "ORD_CLI",
  docId: "{lastGestionaleCodice}"     // body vuoto {}, Content-Type: application/json obbligatorio
});

// Chiude una singola riga d'ordine
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "documento-righe-chiudi",
  resource: "ORD_CLI",
  docRigaId: "{docRigaId}"            // DOC_RIGA_ID → path {pDocRigaId}
});
```
Risorse ammesse per le due operazioni di chiusura: `ORD_CLI`, `ORD_FOR`, `DDT_ALL`, `APP_FOR`
(un tipo diverso restituisce HTTP 500 "tipo documento errato").

---

#### Variazione, cancellazione e datamining 🆕 (TcRestAPI v1.5.3)

⚠️ **Stato nel blocco non confermato.** La doc v1.5.3 aggiunge questi endpoint REST, ma
l'elenco `endpoint` di `GestionaleSend` documentato nella skill `thinkai-workforce`
non li include. **Non inventare i nomi DSL**: controlla nell'editor se il blocco li
espone; in alternativa si può usare `HttpCall` (`method: "PATCH"`/`"DELETE"`, `auth`
Basic, header `TcRestApi-Auth-Token` e `TcRestApi-Resource`) tenendo presente la
protezione anti-SSRF e che `HttpCall` non popola `lastGestionale*`. Schemi completi in
`../dsl/blocchi/integrazioni.md`.

| Operazione REST | Uso nel ciclo ordine cliente |
|---|---|
| `PATCH /documento/{pDocId}` (resource `ORD_CLI`) | Correggere la testata di un ordine già creato (pagamento, destinazione merce, data) senza ricrearlo. Solo i campi da variare; `""` azzera; `RIGHE`, `DOC_ID`, `COD_CAUS_DOC` non ammessi. Totali sempre ricalcolati. |
| `PATCH /documento-righe/{pDocId}` | Variare quantità/prezzi/sconti di righe esistenti via `DOC_RIGA_ID`. `COD_ART` non variabile (cancella e reinserisci). **Niente `pRicalcolo`** (errore se passato). Atomico: se una riga fallisce, nessuna è variata. Non applicabile a ordini evasi/chiusi. |
| `DELETE /documento-righe/{pDocId}?pDocRigaId=…` | Eliminare una riga. Vietato su ordini evasi anche parzialmente. |
| `DELETE /documento/{pDocId}` | Eliminare un ordine creato per errore (es. dopo un retry non idempotente — vedi `gotchas.md` §9). Vietato se evaso; ⚠️ **irreversibile**; se è l'ultimo della serie il numero viene riassegnato. Richiedi sempre conferma umana. |
| `POST /datamining` (resource `DM`) | Estrarre statistiche già definite in Target (es. venduto per cliente/articolo) per report o controlli di coerenza. Serve token abilitato al servizio SQL; risposta Base64 con `COLONNE`/`RIGHE`/`TOTALI`. |

#### `fornitori` — lookup anagrafica fornitori (stesso schema di `clienti`)
```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "fornitori",
  filtro: "CF.COD_CF='{codFornitore}'",
  timeoutSeconds: 30
});
```

#### `contatti` — lookup anagrafica contatti (stesso schema di `clienti`)
```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "contatti",
  filtro: "CF.COD_CF='{codContatto}'",
  timeoutSeconds: 30
});
```

#### `cliente` / `fornitore` / `contatto` — crea una nuova anagrafica
Stesso schema per i tre endpoint (resource `CF`, automatica). Obbligatori:
`RAG_SOC_CF`, `PROVINCIA_CF`.
```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "cliente",   // o "fornitore" / "contatto"
  payloadFromKey: "nuovaAnagraficaJson",
  // payload atteso in stepData.nuovaAnagraficaJson:
  // { "RAG_SOC_CF":"...", "INDI_CF":"...", "CAP_CF":"...", "COMUNE_CF":"...",
  //   "PROVINCIA_CF":"...", "P_IVA_CF":"...", "COD_FISC_CF":"..." }
  timeoutSeconds: 30
});
// produce: lastGestionaleCodice = COD_CF generato
```

#### `articolo` — crea un nuovo articolo di magazzino
```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "articolo",
  payloadFromKey: "nuovoArticoloJson",
  // payload atteso: { "COD_CAT":"...", "COD_ART":"...", "DES_ART":"...", "UM_BASE":"..." }
  timeoutSeconds: 60
});
// produce: lastGestionaleCodice = COD_ART creato
```

#### `articolo-distinta` — crea/versiona una distinta base (BOM)
```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "articolo-distinta",
  payloadFromKey: "distintaJson",
  // payload: { "COD_ART":"...", "CICLI":[{...}], "COMPONENTI":[{...}], "STORICIZZA":"1" (opzionale) }
  timeoutSeconds: 60
});
```

#### `listino-versione` — crea una versione di listino + prezzi
```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "listino-versione",
  payloadFromKey: "listinoJson",
  // payload: { "COD_TIPO_LIST":"...", "DATA_INIZIO_VALIDITA":"...", "PREZZI":[{"COD_ART":"...","PREZZO_LISTINO":10,...}] }
  timeoutSeconds: 60
});
```

#### `prezzo` — calcola il prezzo di un articolo (endpoint REST `/articoli-prezzo`)
```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "prezzo",
  codice: "{currentCodArtTc}",     // COD_ART, obbligatorio
  codCf: "{codCf}",                // cliente/fornitore di riferimento
  flagCliOFor: "0",                // 0 = listino clienti, 1 = listino fornitori
  timeoutSeconds: 30
});
// produce: lastTargetCrossPrice ({PREZZO, COD_LIST, ...})
```
Utile come fallback quando il PDF ordine non riporta un prezzo di riga: si
lascia decidere il prezzo al listino TC invece di inserire 0 o bloccare la riga.

#### `lookup` — query SQL SELECT grezza (sola lettura) — ⚠️ DEPRECATO in v1.5.0
⚠️ **Deprecato**: la doc ufficiale TcRestAPI v1.5.0 non riporta più l'endpoint
`/lookup`. Blocco mantenuto per i flussi legacy (es. CLI-A); per i nuovi flussi
preferire le ricerche strutturate. Se indispensabile, verificare con il produttore dell'ERP
il supporto lato server.
```javascript
GestionaleSend({
  credentialName: "targetcross-test",
  endpoint: "lookup",
  sql: "SELECT TOP 1 ART_ANA.COD_ART FROM ART_ANA WHERE ART_ANA.COD_ART LIKE '%{currentCodArtEscaped}%'",
  timeoutSeconds: 60
});
```
Nota storica: fino a v1.4.5 il path REST era `/lookup` (resource `SQL`, body
`{"SQL": "..."}`) — il parametro del blocco resta `sql`. Vietati INSERT/UPDATE/DELETE/DDL/EXEC e statement multipli.

---

## FileList

```javascript
FileList({
  path:      "<CARTELLA_INPUT>",
  pattern:   "*.pdf",
  recursive: false
});
// produce: lastFileList (array di path stringa)
```

---

## FileWrite

**REGOLA CRITICA**: la variabile nel parametro `path` deve sempre essere embedded
in una stringa più lunga. Se è l'intera stringa, la sostituzione non avviene.

> ⚠️ **`FileWrite` scrive SOLO testo** (nessun encoding binario, antepone BOM UTF-8): non usarlo
> MAI per PDF/immagini. La stampa PDF del gestionale è già su disco: si usa `lastGestionalePdfPath`
> (vedi `code-templates.md` § pdfPathOutput). Usi legittimi: log JSON/CSV/HTML, heartbeat.

```javascript
// ✓ CORRETTO — log JSON
FileWrite({
  path:             "<WORK_ROOT>\\log\\{agentName}_{timestamp}.json",
  content:          "{logJsonString}",
  append:           false,
  createDirectories: true
});
// @continueOnFail
```

Variabili prodotte:
- `lastFileWritten`: path del file scritto
- `lastFileBytes`: dimensione in byte

---

## FileMove / FileRename

```javascript
FileMove({
  source:      "{__loopItem}",                       // path originale PDF
  destination: "<WORK_ROOT>\\ELABORATO\\",     // cartella destinazione
  overwrite:   true
});
// @continueOnFail
```

---

## AiAnalysis

```javascript
AiAnalysis({
  attachments: ["{__loopItem}"],   // allegato PDF corrente
  prompt:      "..."               // prompt esatto (vedi ../prompt-ordini/template-*.md)
});
// produce: lastAiOutput (testo/JSON grezzo)
```

---

## Markdown

```javascript
Markdown({
  input: "{mailBodyMarkdown}"
});
// produce: lastMarkdownHtml
```

---

## SendEmail

```javascript
SendEmail({
  to:          ['notifiche@example.com'],
  subject:     "{mailSubjectFinal}",
  body:        "{lastMarkdownHtml}",
  bodyIsHtml:  true,
  attachments: ["{__loopItem}", "{lastGestionalePdfPath}"]
});
```

`{__loopItem}` = PDF ordine originale del cliente.
`{lastGestionalePdfPath}` = PDF documento ORD_CLI creato su TC.

**ATTENZIONE**: `lastGestionalePdfPath` è prodotto dallo step `documenti-stampa` (path relativo
alla working directory del motore, che `SendEmail` risolve così com'è). Non ricalcolarlo, non
convertirlo in assoluto, non spostarlo con `FileMove`. Catturalo in `stampaPdfPath` e, in un
`ForEach`, mettilo nella pulizia anti-bleed di inizio giro.

---

## MailRead (solo trigger email)

```javascript
MailRead({
  credentialName: "gmail-ordini",   // o imap-ordini, microsoft-graph-ordini
  folder:         "INBOX",
  unreadOnly:     true,
  includeAttachments: true
});
// produce: lastEmails (array di email con allegati)
```

---

## SqlInsert

```javascript
SqlInsert({
  credentialName: "db-targetcross",
  table:          "AUDIT_ORDINI_RIGHE",
  rows:           "{righeAudit}"   // array JSON da auditPrep
});
// @continueOnFail
```

Struttura di AUDIT_ORDINI_RIGHE (da definire lato cliente):
```sql
CREATE TABLE AUDIT_ORDINI_RIGHE (
  ID         INT IDENTITY PRIMARY KEY,
  COD_DOC    NVARCHAR(50),
  COD_ART_TC NVARCHAR(30),
  COD_ART_CF NVARCHAR(50),
  QT_DOC     DECIMAL(10,3),
  STATO      INT,           -- 2 = inserito da automazione
  INS_DATA   DATETIME DEFAULT GETDATE()
);
```
