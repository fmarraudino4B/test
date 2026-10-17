# Catalogo blocchi — Integrazioni

> Categoria "Integrazioni" (fonte manuale: intestazione categoria "Integrazioni+Mail"). Questo file documenta i blocchi di integrazione con sistemi esterni: chiamata HTTP generica e connettore ERP TargetCross/TaylorGest. I nomi DSL provengono da `references/nomi-blocchi.md` (autorità). I nomi dei parametri coincidono col manuale.

---

### HTTP Call  — DSL `HttpCall` ✅ CONFERMATO (corso M14)  `L2737`

Nome DSL `HttpCall` ✅ CONFERMATO dal video corso (modulo 14 «Integrazioni», `node-HttpCall`).

- **Scopo:** Chiama un'API esterna (con credenziali, anti-SSRF).
- **Quando usarlo:** Quando il flusso deve chiamare un'API esterna via HTTP (GET/POST/PUT/DELETE/PATCH) con credenziali e protezione anti-SSRF. Supporta autenticazione Bearer/Basic/ApiKey, body raw o form (x-www-form-urlencoded), query params e placeholder `{chiave}` in URL/body/form. Attivare `neverError` quando si vuole ispezionare status/body con un Branch a valle senza far fallire lo step; l'output `lastHttpResponse` tipicamente viene poi passato a JSON Parse. ⚠️ NON DOCUMENTATO oltre a quanto riportato nella descrizione e nei parametri.

- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `url` | testo | Sì | — | Label "URL". URL dell'endpoint (https). Supporta `{placeholder}`. Es. `https://api.example.com/dati` |
| `method` | scelta — GET · POST · PUT · DELETE · PATCH | — | GET | Label "Metodo". |
| `headers` | lista chiave/valore | — | — | Label "Header". |
| `auth` | JSON | — | — | Label "Autenticazione". `{type:Bearer\|Basic\|ApiKey, value, headerName}` |
| `body` | testo lungo | — | — | Label "Body". Supporta `{placeholder}`. |
| `contentType` | testo | — | application/json | Label "Content-Type". |
| `expectedStatus` | JSON | — | — | Label "Status attesi". Es. `[200,201]` |
| `timeoutSeconds` | intero | — | 30 | Label "Timeout (s)". |
| `maxResponseBytes` | intero | — | 1048576 | Label "Max byte risposta". |
| `queryParams` | lista chiave/valore | — | — | Label "Query params". Parametri query (chiave→valore) appesi all'URL con encoding. Supporta `{placeholder}`. |
| `bodyType` | scelta — raw · form | — | raw | Label "Tipo body". raw = Body+Content-Type. form = campi sotto inviati come x-www-form-urlencoded. |
| `formParams` | lista chiave/valore | — | — | Label "Campi form". Solo `bodyType=form`: campi chiave→valore (x-www-form-urlencoded). Supporta `{placeholder}`. |
| `allowUnauthorizedCerts` | sì/no | — | false | Label "Ignora errori SSL". Accetta certificati TLS non validi/self-signed. Usare solo per servizi on-prem fidati. |
| `followRedirects` | sì/no | — | true | Label "Segui redirect". Se disattivo non segue i redirect HTTP 3xx. |
| `neverError` | sì/no | — | false | Label "Non fallire su errore". Se attivo lo step non fallisce su status non-2xx: registra solo status/body (utile con Branch a valle). |

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastHttpResponse` | testo | Corpo della risposta. |
| `lastHttpStatus` | intero | Status code HTTP. |

- **⚠️ Avvertenze / vincoli:**
  - `allowUnauthorizedCerts`: accetta certificati TLS non validi/self-signed — usare SOLO per servizi on-prem fidati.
  - Protezione anti-SSRF attiva (dalla descrizione del blocco).
  - `neverError`: se attivo lo step NON fallisce su status non-2xx (registra solo status/body).

- **Riferimenti incrociati:** Branch (IF) — output usato a valle con `neverError` attivo; JSON Parse — `lastHttpResponse` è l'esempio di `sourceKey` del blocco JSON Parse (L1951).

---

### TargetCross / TaylorGest  — DSL `GestionaleSend`  `L2807`

Nome DSL ✅ CONFERMATO (osservato in flusso esportato, F1:5; `nomi-blocchi.md` §2). Rinomina totale rispetto al display (brand→generico).

- **Scopo:** Integrazione ERP Target Cross / TaylorGest (TcRestAPI): crea documenti (ordini/DDT/fatture/movimenti magazzino), stampa PDF, cerca documenti/clienti/fornitori/contatti/articoli con filtri e calcola prezzi.
- **Quando usarlo:** Per integrare l'ERP Target Cross / TaylorGest via TcRestAPI (**v1.5.3**, doc ufficiale "Four Infolab srl — Server REST per accesso ai servizi di Target Cross", 1 ottobre 2026 — sostituisce v1.5.0 del 29 settembre 2026 e v1.4.5): verificare la connessione (`test`), creare documenti (testata+RIGHE), aggiungere righe a un documento esistente (`documento-righe`), chiudere un documento o una singola riga di ordine (`documento-chiudi`/`documento-righe-chiudi`), stampare il PDF di un documento, cercare documenti/clienti/fornitori/contatti/articoli con filtro SQL obbligatorio, creare anagrafiche (cliente/fornitore/contatto), creare articoli, distinte base/BOM e versioni listino, o calcolare il prezzo di un articolo (`prezzo`, endpoint REST `/articoli-prezzo`). ⚠️ L'operazione `lookup` (query SQL grezza) è **deprecata** in v1.5.0: la doc ufficiale non la riporta più (vedi nota sul parametro `sql`). Il payload di creazione arriva tipicamente da AI Analysis (`lastAiOutput`) o da SetFields/CodeJs, oppure via template inline (`payloadTemplate` ha precedenza su `payloadFromKey`). Richiede una credenziale TargetCross/TaylorGest configurata (baseUrl, utente, password, auth token).
- **Autenticazione lato TcRestAPI (per configurare correttamente la credenziale):** ogni chiamata REST porta tre header — `Authorization: Basic <UTENTE:PASSWORD in Base64>` (utente/password gestiti in Target Cross, tabella UTENTI di TcRestApi), `TcRestApi-Auth-Token` (token statico generato in Target Cross, sezione Licenza di TcRestApi — non è la password), `TcRestApi-Resource` (codice risorsa, vedi parametro `resource` sotto). Errori tipici lato TcRestAPI: **400** = errore di autenticazione (verificare Authorization/Token), **500** = errore interno del server (contattare assistenza ERP). Il **numero massimo di righe restituite dalle ricerche è impostato lato Target** (default 100, configurabile 0-100 dai "Codici fissi" di TcRestApi) — non è un parametro del blocco. URL base: installazione locale `http://<SERVER>:<PORTA>/api/tcrestapi/v_1`; dietro IIS `https://<sito>/cgi-bin/omnisrestisapi.dll/ws/<PORTA>/api/tcrestapi/v_1`. Le risposte KO riportano anche il campo `Header` con gli header ricevuti (v1.5.3 §99.2): `Authorization` e `TcRestApi-Auth-Token` sono mascherati con `***`, e il log lato server (API_LOG) registra solo utente e primi 8 caratteri del token. `GET /test` restituisce in `Esito` la versione del server TcRestAPI (es. `TcRestAPI 20260522-T1 - 27.05.2026 09:22`): utile per verificare a quale release è allineata l'installazione del cliente.

- **Parametri (input):**

| Chiave | Tipo | Obbl. | Default | Note |
| --- | --- | --- | --- | --- |
| `credentialName` | credenziale | Sì | — | Label "Credenziale TargetCross". Credenziale TargetCross/TaylorGest (Workforce > OAuth & connessioni): baseUrl, utente, password, auth token. |
| `endpoint` | scelta — test · documento · documento-righe · documento-chiudi · documento-righe-chiudi · documenti-stampa · documenti · clienti · fornitori · contatti · cliente · fornitore · contatto · articoli · articolo · articolo-distinta · listino-versione · prezzo · ~~lookup~~ (deprecato) | Sì | — | Label "Operazione". test=verifica connessione (`/test`); documento=crea documento (`/documento`); **documento-righe=aggiunge righe a un documento esistente (`/documento-righe/{pDocId}`, param `docId` + `RIGHE[]`, param `ricalcolo`)**; **documento-chiudi=chiude tutte le righe di un ordine/allestimento/approntamento (`/documento/chiudi/{pDocId}`, param `docId`, body vuoto)**; **documento-righe-chiudi=chiude una singola riga d'ordine (`/documento-righe/chiudi/{pDocRigaId}`, param `docRigaId`, body vuoto)**; documenti-stampa=PDF di un documento (`/documenti-stampa`); documenti/clienti/fornitori/contatti/articoli=ricerca (filtro obbligatorio, endpoint REST `/documenti`, `/clienti`, `/fornitori`, `/contatti`, `/articoli`); cliente/fornitore/contatto=CREA anagrafica (`/cliente`, `/fornitore`, `/contatto`); articolo=CREA articolo (`/articolo`); articolo-distinta=CREA/versiona distinta base/BOM (`/articolo-distinta`, CICLI+COMPONENTI, supporta storicizzazione con `STORICIZZA:"1"`); listino-versione=CREA versione listino+prezzi (`/listino-versione`, PREZZI[]); prezzo=calcola prezzo articolo (`/articoli-prezzo`); ~~lookup=query SQL SELECT grezza (`/lookup`)~~ **DEPRECATO in v1.5.0** (vedi parametro `sql`). API **TcRestAPI v1.5.0** (Four Infolab srl, 29 settembre 2026). ⚠️ I nomi DSL delle 3 nuove operazioni (`documento-righe`, `documento-chiudi`, `documento-righe-chiudi`) sono derivati dai path REST: **allineali all'etichetta esatta esposta dal blocco GestionaleSend** in questa versione di WorkForce. |
| `resource` | scelta — ORD_CLI · OFF_CLI · DDT_CLI · FATT_CLI · ORD_FOR · OFF_FOR · APP_FOR · DDT_FOR · DDT_ALL · FATT_FOR · MAG_CAR · MAG_SCAR | — | — | Label "Risorsa (tipo documento)". Va nell'header REST `TcRestApi-Resource`. Serve per documento/documento-righe/documenti-stampa/documenti (tipo documento) e per documento-chiudi/documento-righe-chiudi (tipo ordine da chiudere). **Confermati nella doc TcRestAPI v1.5.0** (§4.5 "Tipi di documento disponibili"): `ORD_CLI` (ordini cliente), `DDT_CLI` (documenti di trasporto cliente), `FATT_CLI` (fatture cliente), `ORD_FOR` (ordini fornitore), `DDT_FOR` (documenti di trasporto fornitore), `FATT_FOR` (fatture fornitore), `MAG_CAR` (movimenti di carico magazzino), `MAG_SCAR` (movimenti di scarico magazzino). **Solo per le operazioni di chiusura** (documento-chiudi/documento-righe-chiudi, §19.2/§20.2) le risorse ammesse sono `ORD_CLI`, `ORD_FOR`, `DDT_ALL` (allestimento) e `APP_FOR` (approntamento fornitore) — un valore diverso restituisce HTTP 500 "tipo documento errato". `APP_FOR` compare così **ufficialmente** da v1.5.0 (prima solo come estensione), mentre `DDT_ALL` è **nuovo**. `OFF_CLI`/`OFF_FOR` **non compaiono** ancora nella doc ufficiale: trattali come estensione/configurazione specifica dell'installazione cliente e verifica in Target Cross (menu Moduli aggiuntivi → TcRestApi → Codici fissi → Autorizzazioni) prima di usarli. Per clienti/fornitori/contatti/cliente/fornitore/contatto la risorsa è `CF`, per articoli/articolo/prezzo `ART_ANA`, per articolo-distinta `ART_DIST`, per listino-versione `LISTINI` (automatiche, header `TcRestApi-Resource` impostato dal blocco). Per `lookup` (deprecato) la risorsa era `SQL`. |
| `payloadFromKey` | testo | — | — | Label "Chiave payload". Creazione documento/anagrafica/articolo: chiave StepData col body JSON. documento=testata+RIGHE; **documento-righe=solo array `RIGHE[]` (stessa struttura riga di documento, inclusi LOTTI/MATRICOLE/LOCAZIONI e campi USER)**; cliente/fornitore/contatto=campi anagrafica (obbl. RAG_SOC_CF, PROVINCIA_CF); articolo=campi articolo (obbl. COD_CAT, COD_ART, DES_ART, UM_BASE); articolo-distinta=distinta base (COD_ART + CICLI[] + COMPONENTI[]). documento-chiudi/documento-righe-chiudi non richiedono payload (body `{}`). Tipico: output di AI Analysis o SetFields/CodeJs. Es. `lastAiOutput` |
| `payloadTemplate` | testo lungo | — | — | Label "Template payload (JSON)". Solo creazione documento: corpo JSON (testata + RIGHE) composto inline, con placeholder risolti (`{chiave}` / `$.chiave`). HA PRECEDENZA su `payloadFromKey` ("Chiave payload"). Usalo per costruire il body direttamente nello step invece di prenderlo da una chiave StepData. Es. `{"TESTA":{"COD_CF":"{codCliente}"},"RIGHE":[{"COD_ART":"{codArt}","QTA":1}]}` |
| `filtro` | testo | — | — | Label "Filtro (SQL)". Ricerche: condizione SQL TABELLA.COLONNA op valore (es. `CF.COD_CF='00000350'`, `ART_ANA.COD_ART LIKE 'COP%'`). Obbligatorio almeno un filtro o un codice — le ricerche non filtrate sono bloccate. Es. `CF.RAG_SOC_CF LIKE '%rossi%'` |
| `colonne` | testo | — | — | Label "Colonne". Ricerche: colonne da includere, separate da `;` (vuoto = colonne di default). Devono essere colonne standard Target. Es. `COD_CF;RAG_SOC_CF` |
| `codice` | testo | — | — | Label "Codice". Ricerche/prezzo: codice specifico. COD_CF per clienti/fornitori/contatti, COD_ART per articoli/prezzo (obbligatorio per prezzo). |
| `codCf` | testo | — | — | Label "COD_CF (prezzo)". Solo prezzo: cliente/fornitore di riferimento per il calcolo. |
| `flagCliOFor` | scelta — 0 · 1 | — | — | Label "Cliente/Fornitore (prezzo)". Solo prezzo: 0 = listino clienti, 1 = listino fornitori. |
| `codSecondarioArt` | testo | — | — | Label "Codice secondario (articoli)". Solo articoli: codice articolo del fornitore/cliente (dalla bolla). Cerca su ART_CODICI lato gestionale (match codice fornitore→interno, senza SQL). Da usare con `tipoCodice`. Es. `{currentCodArtFornitore}` |
| `tipoCodice` | testo | — | — | Label "Tipo codice (articoli)". Solo articoli con codice secondario: TIPO_CODICE = COD_CF del fornitore/cliente proprietario del codice. Es. `{codCf}` |
| `docId` | testo | — | — | Label "DOC_ID". documenti / documenti-stampa / **documento-righe / documento-chiudi**: identificativo del documento (per documento-righe e documento-chiudi finisce nel path REST `{pDocId}`, con percent-encoding se contiene `/`, spazi o altri caratteri riservati). Es. `2026-OC_MO-0000021` |
| `docRigaId` | testo | — | — | Label "DOC_RIGA_ID". **Solo documento-righe-chiudi**: identificativo della singola riga da chiudere (finisce nel path REST `{pDocRigaId}`, con percent-encoding se serve). È il valore restituito in `lastGestionaleCodice`/`Codice` da `documento-righe` (righe separate da `/`). |
| `ricalcolo` | scelta — 0 · 1 | — | 0 | Label "Ricalcola totali". **Solo documento-righe**: mappa sul query param REST `pRicalcolo`. `1` = a fine inserimento ricalcola i totali del documento; `0`/assente = totali non aggiornati. Con più chiamate successive conviene impostarlo a `1` solo sull'ultima. |
| `dataDocFrom` | testo | — | — | Label "Data da". Ricerca documenti: estremo iniziale del range DATA_DOC (formato gg/mm/aaaa). Es. `01/11/2025` |
| `dataDocTo` | testo | — | — | Label "Data a". Ricerca documenti: estremo finale del range DATA_DOC. Con data+cliente costruisce FILTRO oggetto `{DATA_DOC:{from,to},COD_CF}`. Es. `31/12/2025` |
| `rawBody` | testo lungo | — | — | Label "Body manuale (JSON)". Avanzato: JSON inviato VERBATIM come body, override di tutta la costruzione. Per filtri custom o differenze tra installazioni TcRestAPI. Es. `{"FILTRO":{"DATA_DOC":{"from":"01/11/2025","to":"31/12/2025"},"COD_CF":"016836"}}` |
| `report` | testo | — | — | Label "Report (stampa)". Solo documenti-stampa: nome del report (opzionale). |
| `sql` | codice — sql | — | — | Label "Query SQL (lookup)". ⚠️ **DEPRECATO in v1.5.0** — l'operazione `lookup` (endpoint REST `/lookup`, header `TcRestApi-Resource: SQL`, body `{"SQL":"<query>"}`) **non è più documentata** dalla doc ufficiale TcRestAPI v1.5.0: era presente in v1.4.5 (numerata "98. Endpoint /lookup", con refuso editoriale). Il parametro resta per i **flussi legacy** che già lo usano (es. dedup ordini in CLI-A), ma **non usarlo in nuovi flussi**: dove possibile sostituiscilo con le ricerche strutturate (`documenti`/`clienti`/`fornitori`/`articoli` con `filtro`/`colonne`); se serve davvero una query grezza sul DB, valuta un accesso SQL diretto fuori da TcRestAPI (es. blocco dati SQL / connessione al database) e verifica prima con il produttore dell'ERP se l'endpoint `/lookup` resta supportato lato server. Quando usato: solo SELECT di sola lettura, vietati INSERT/UPDATE/DELETE/DDL/EXEC e statement multipli. Es. `SELECT TOP 10 COD_ART, DES_ART FROM ART_ANA`. |
| `timeoutSeconds` | intero | — | 60 | Label "Timeout (s)". Timeout della chiamata (default 60, max 300). Alza per ERP lenti su payload grandi. |

- **Operazioni REST introdotte dopo v1.5.0 (presenti in v1.5.3) — stato nel blocco ⚠️ NON CONFERMATO:** la doc ufficiale v1.5.3 aggiunge `PATCH /documento/{pDocId}`, `PATCH /documento-righe/{pDocId}`, `DELETE /documento-righe/{pDocId}?pDocRigaId=…`, `DELETE /documento/{pDocId}` e `POST /datamining` (schemi nella sezione «Schema payload» sotto). L'elenco `endpoint` del blocco `GestionaleSend` documentato qui **non le include** e non c'è evidenza che questa versione di WorkForce le esponga: **non inventare nomi DSL**. Verifica nell'editor dei flussi se compaiono tra le operazioni; se non ci sono, l'alternativa è `HttpCall` (supporta `method` PATCH/DELETE e `auth` Basic) con gli header `TcRestApi-Auth-Token` e `TcRestApi-Resource` — da validare perché `HttpCall` ha protezione anti-SSRF (un host TcRestAPI on-prem su rete privata potrebbe essere bloccato) e non popola `lastGestionale*`. Chiedi a Four Infolab/Four AI quando il blocco verrà allineato.

- **Output (variabili StepData prodotte):**

| Chiave | Tipo | Descrizione |
| --- | --- | --- |
| `lastGestionaleResponse` | testo | Risposta grezza. |
| `lastGestionaleEsito` | testo | Esito. |
| `lastGestionaleStato` | testo | Stato. |
| `lastGestionaleCodice` | testo | Codice restituito: DOC_ID per documento; **DOC_RIGA_ID delle righe inserite, separati da `/`, per documento-righe**; **DOC_ID/DOC_RIGA_ID chiuso per documento-chiudi/documento-righe-chiudi**; COD_CF/COD_ART per le creazioni anagrafica/articolo. |
| `lastGestionalePdf` | testo | PDF (base64) — solo documenti-stampa. |
| `lastTargetCrossRows` | JSON | Ricerche: righe decodificate (lista). |
| `lastTargetCrossJson` | testo | Ricerche/prezzo: JSON decodificato grezzo. |
| `lastTargetCrossPrice` | JSON | Prezzo: oggetto `{PREZZO, COD_LIST, ...}`. |

- **⚠️ Avvertenze / vincoli:**
  - Ricerche: obbligatorio almeno un filtro o un codice — le ricerche NON filtrate sono bloccate (parametro `filtro`).
  - ⚠️ `lookup`/`sql`: **DEPRECATO in v1.5.0** (non più nella doc ufficiale) — mantenuto solo per flussi legacy; se usato, SOLO SELECT di sola lettura (vietati INSERT/UPDATE/DELETE/DDL/EXEC e statement multipli).
  - **`documento-righe`**: le righe sono inserite in **un'unica transazione** — se una riga fallisce, non ne viene aggiunta nessuna. Senza `ricalcolo=1` i totali del documento NON vengono aggiornati. Nei documenti che movimentano magazzino valgono gli stessi controlli di `documento`: matricole (n° MATRICOLE = QUANT_RIGA), lotti (somma QTA_LOT = QUANT_RIGA), locazioni (obbligatorie se il deposito è gestito a locazioni).
  - **`documento-chiudi` / `documento-righe-chiudi`**: body JSON **vuoto** (`{}`) ma header `Content-Type: application/json` **obbligatorio** (verificato in fase iniziale anche senza dati). Risorse ammesse: `ORD_CLI`, `ORD_FOR`, `DDT_ALL`, `APP_FOR` — un tipo diverso restituisce HTTP 500 "tipo documento errato".
  - `payloadTemplate` HA PRECEDENZA su `payloadFromKey` ("Chiave payload").
  - `rawBody`: JSON inviato VERBATIM come body, override di tutta la costruzione.
  - `timeoutSeconds`: default 60, MAX 300.
  - Campi obbligatori nei payload di creazione: anagrafica cliente/fornitore/contatto → RAG_SOC_CF, PROVINCIA_CF; articolo → COD_CAT, COD_ART, DES_ART, UM_BASE; codice obbligatorio per l'operazione prezzo (COD_ART).
  - **Numeri e date (TcRestAPI v1.5.3, «Formato di numeri e date»).** Quantità, prezzi, sconti, pesi e flag vanno passati **preferibilmente come numeri JSON** (punto decimale, senza virgolette: `5.5`, `10`, `0`): è l'unico formato indipendente dalle impostazioni del server. ⚠️ *Rettifica rispetto a v1.5.0*, che li mostrava come stringa. Sugli endpoint documenti (`documento`, `documento-righe` in POST e PATCH, PATCH `documento`) le stringhe sono comunque accettate con queste regole: un solo separatore (`"5.50"` / `"5,50"`) = decimale; punto e virgola insieme (`"1.234,50"` / `"1,234.50"`) = decimale è l'ultimo dei due; più separatori uguali (`"1.000.000"`) = migliaia; ⚠️ **`"1.000"` viene registrato come 1, non 1000** → mai il separatore delle migliaia senza decimali. Negli altri endpoint (anagrafiche, articoli, distinte, listini) e nelle quantità dei `LOTTI` le stringhe sono convertite con le impostazioni del server: usare numeri JSON o la virgola decimale (es. `PESO_ART: "75,6"`). **Date**: stringa `GG/MM/AAAA`, `GG.MM.AAAA`, `GG-MM-AAAA` o `AAAA-MM-GG`, anno a 4 cifre; una data inesistente (`31/02/2026`) o con anno a 2 cifre (`04/05/26`) è rifiutata con «Data documento non valida». ⚠️ **RETTIFICA run reali:** con il formato ISO `AAAA-MM-GG` il gestionale registrava sempre il giorno 20: usa solo `gg/mm/aaaa`. Normalizzazione lato flusso: `../../erp/gotchas.md` §10 e template `parseNumeroTC`.
  - Ogni risposta REST di TcRestAPI ha la forma `{"Stato":"OK"|"KO","EndPoint":"...","Messaggio":"...","Esito":"...","Resource":"...","Codice":"..."}` (più `"JSON":"<base64>"` per le ricerche e `"PDF":"<base64>"` per `documenti-stampa`); il blocco `GestionaleSend` la mappa su `lastGestionaleStato`/`lastGestionaleEsito`/`lastGestionaleCodice`/`lastTargetCrossJson`/`lastGestionalePdf`. Codici di errore HTTP lato TcRestAPI: **400** = errore di autenticazione, **500** = errore interno server.
  - Per i documenti, il body JSON supporta anche campi **USER personalizzati** (sia in testata che a livello di riga) purché definiti lato Target Cross, e array `LOTTI`/`MATRICOLE`/`LOCAZIONI` per riga (gestiti automaticamente da `documento` e `documento-righe`). Tutte le colonne indicate in `filtro`/`colonne` devono essere colonne standard di Target Cross.
  - **Note operative su `documento` (v1.5.3 §4.7-4.8):**
    - *Stack limit* — se la creazione evade in automatico ordini/allestimenti/ordini di produzione collegati si può superare il limite di 20 dello stack metodi Omnis (errore di elaborazione). In Target: Aziende → Parametri ed impostazioni → Dati generali, tab Impostazioni → impostare **Stack limit applicazione = 100**.
    - *Destinazione merce* — indicare `DEST_ID` (o `CF_DEST_ID`) in testata con il codice di una destinazione del cliente/fornitore (i dati sono letti dall'anagrafica) oppure gestire la destinazione manuale con le colonne `DES_DEST_MERCE`, `INDI_DEST_MERCE`, `COMUNE_DEST_MERCE`, `CAP_DEST_MERCE`, `PROVINCIA_DEST_MERCE`, `STATO_DEST_MERCE`. Sono accettati anche i vecchi nomi `NOME_DEST`, `INDIR_DEST`, `CITTA_DEST`, `CAP_DEST`, `PROVINCIA_DEST`: se presenti nel body **prevalgono** sui corrispondenti `…_DEST_MERCE`.
    - *Ricalcolo prezzi* — con `FLAG_CALC_PRZ="1"` in testata, prezzi e sconti passati nelle righe vengono **ignorati** e ricalcolati secondo lo standard Target.
    - *Prezzi e sconti bloccati* 🆕 — per ogni riga si possono passare `NO_RICALC_PRZ` e `NO_RICALC_SCONTI` (0/1): con `1` Target non ricalcola rispettivamente prezzo o sconti della riga nelle variazioni successive (es. cambio della sola quantità con PATCH `documento-righe`). I flag li decide il chiamante: se assenti valgono 0, anche quando la riga ha prezzi/sconti espliciti. Per ordini importati con prezzo concordato dal cliente conviene impostarli a `1`.
    - *Controlli sui dati prima della generazione (§4.8)* 🆕 — al primo controllo non superato il documento **non viene creato** e `Esito` riporta il motivo: `COD_CAUS_DOC` obbligatoria, esistente e coerente col tipo in `TcRestApi-Resource` («Causale documento non congrua con risorsa»); `COD_CF` obbligatorio (non per le causali di magazzino `MAG_CAR`/`MAG_SCAR`) e coerente con la causale — con causale clienti un codice solo-fornitore è rifiutato e viceversa («Codice cliente errato (…)» / «Codice fornitore errato (…)» / «Manca codice cliente/fornitore»); `COD_PAGA` facoltativo ma esistente («Codice pagamento errato (…)»); `DATA_DOC` facoltativa ma valida («Data documento non valida (…)»); almeno una riga in `RIGHE`; `COD_ART` esistente; `QUANT_RIGA` ≠ 0; `UM` facoltativa ma base o tra le UM dell'articolo («Unità di misura non valida per l'articolo … (…, riga n)»); `SCONTO_1…SCONTO_5` ≤ 100 («Sconto non valido: SCONTO_1 = 150 (massimo 100) (riga n)»); lotti/matricole/locazioni come sopra. Questi messaggi di `Esito` sono utili da intercettare in un Branch per classificare gli errori dati vs errori di sistema.
  - **Ricerca `documenti` (v1.5.0 §6):** oltre a `FILTRO`/`COLONNE`/`DOC_ID` sono ufficiali anche `SORT` (clausola ORDER BY) e `NUM_RECS` (n° record, default/max 100). Per ottenere **solo le righe** di un documento si usa il suffisso `_RIGHE` sul codice risorsa (es. `DDT_CLI_RIGHE`); il blocco non espone un parametro dedicato → passalo via `rawBody` o, se disponibile, impostando la risorsa con suffisso.

**Schema payload — da TcRestAPI v1.5.3 (§4-25 della doc ufficiale, 1 ottobre 2026).** Gli esempi di documento usano numeri JSON (v1.5.3); in v1.5.0 gli stessi valori erano mostrati come stringhe.

- **`documento`** (endpoint REST `/documento`, header `TcRestApi-Resource` = tipo documento, es. `ORD_CLI`) — testata + array `RIGHE`:
  ```json
  {
    "COD_CAUS_DOC": "DF_MO",
    "SERIE_DOC": "DC_MO",
    "DATA_DOC": "04/05/2026",
    "COD_CF": "00000350",
    "COD_PAGA": "BB30",
    "COD_COMMES": "",
    "COD_DEP": "",
    "DES_DEST_MERCE": "", "INDI_DEST_MERCE": "", "COMUNE_DEST_MERCE": "", "CAP_DEST_MERCE": "", "PROVINCIA_DEST_MERCE": "",
    "RIGHE": [
      { "COD_ART": "KOS", "DES_RIGA": "COSETTA ARTICOLO", "UM": "Pz.", "QUANT_RIGA": 1, "PREZZO_LORDO_VU1": 5.00, "SCONTO_1": 10.00, "SCONTO_2": 5.00 }
    ]
  }
  ```
  Obbligatori: testata `COD_CAUS_DOC`, `COD_CF` (se richiesto dal tipo documento); riga `COD_ART`, `QUANT_RIGA`. Controlli completi nelle note operative sopra. Risposta positiva: `"Codice"` = DOC_ID creato (es. `"2026-OC_MO-0000021"`).
- **`cliente` / `fornitore` / `contatto`** (endpoint `/cliente`, `/fornitore`, `/contatto`, resource `CF`) — stesso schema anagrafica per i tre:
  ```json
  { "RAG_SOC_CF": "FRANCESCO PARISI", "INDI_CF": "VIALE GARIBALDI, 25", "CAP_CF": "65124", "COMUNE_CF": "PESCARA", "PROVINCIA_CF": "PE", "P_IVA_CF": "12345678901", "COD_FISC_CF": "ABCDEFGHILMEND" }
  ```
  Obbligatori: `RAG_SOC_CF`, `PROVINCIA_CF`. Risposta: `"Codice"` = COD_CF generato.
- **`articolo`** (endpoint `/articolo`, resource `ART_ANA`):
  ```json
  { "COD_CAT": "SL", "COD_ART": "FPA_TEST", "DES_ART": "DESCRIZIONE FPA ART", "UM_BASE": "NR", "LARG": "250", "PESO_ART": "75,6" }
  ```
  Obbligatori: `COD_CAT`, `COD_ART`, `DES_ART`, `UM_BASE`. Nota: `PESO_ART` nell'esempio ufficiale usa la **virgola** come separatore decimale.
- **`articolo-distinta`** (endpoint `/articolo-distinta`, resource `ART_DIST`) — distinta base con cicli e componenti:
  ```json
  {
    "COD_ART": "COPOL", "DATA_INIZIO_VALIDITA": "01-06-2026", "DATA_FINE_VALIDITA": "31-12-2026",
    "CICLI": [ { "COD_CICLO": "LAV", "DES_CICLO": "CICLO LAVORAZIONE", "DES_LAV": "Descrizione estesa CICLO 001", "UM_TEMPO_FIX": "1", "UM_TEMPO_VAR": "1", "COD_CENTRO": "MO.02",
      "FASI": [ { "COD_CAUS": "LAV", "DES_FASE": "Lavorazione", "COD_CP": "PS", "TEMPO_FISSO_MACC": "5", "TEMPO_FISSO_OP": "1" } ] } ],
    "COMPONENTI": [ { "COD_ART_COMP": "SL001", "DES_DIST": "Semilavorato SL001", "QUANT_DIST": "2.5", "UM": "NR", "COD_TIPO_COSTO_DIST": "CMP", "TIPO_CALC_PRZ_PREL": "ULT" } ]
  }
  ```
  Obbligatori: `COD_ART`, `COD_CICLO` (almeno 1 riga in `CICLI`), `COD_ART_COMP`/`UM`/`QUANT_DIST` (almeno 1 riga in `COMPONENTI`). Con `"STORICIZZA":"1"` in testata la distinta esistente viene storicizzata invece di sovrascritta (utile per versionare le distinte nel tempo).
- **`listino-versione`** (endpoint `/listino-versione`, resource `LISTINI`) — versione di listino + prezzi:
  ```json
  {
    "COD_TIPO_LIST": "PERS", "DES_AGG_LIST": "Listino da ThinkAi", "DATA_INIZIO_VALIDITA": "01.01.2000", "DATA_FINE_VALIDITA": "31.12.2099",
    "FLAG_ACQ": 0, "FLAG_PERS": 1, "NOTE_LISTINO": "Prova listino",
    "PREZZI": [ { "COD_ART": "PF_001", "PREZZO_LISTINO": 10, "SCONTO1": 0, "SCONTO2": 0, "SCONTO3": 0, "QUANT_MIN": 1, "QUANT_MAX": 20, "UM": "Pz." } ]
  }
  ```
  Obbligatori: `COD_TIPO_LIST`, `DATA_INIZIO_VALIDITA`, `COD_ART`, `PREZZO_LISTINO` (per ogni riga in `PREZZI`). Risposta: `"Codice"` = codice versione listino creata (es. `"PERS_005"`).
- **`prezzo`** (endpoint REST `/articoli-prezzo`, resource `ART_ANA`) — calcolo prezzo secondo le regole Target:
  ```json
  { "COD_ART": "COPOL", "FLAG_CLI_O_FOR": "1", "COD_CF": "00000347" }
  ```
  `COD_ART` obbligatorio; `FLAG_CLI_O_FOR`: 0 = listino clienti, 1 = listino fornitori; `COD_CF` = cliente/fornitore di riferimento (mappa sui parametri `codice`/`flagCliOFor`/`codCf` del blocco).
- **`documento-righe`** 🆕 v1.5.0 (endpoint REST `/documento-righe/{pDocId}`, header `TcRestApi-Resource` = tipo documento) — aggiunge righe a un documento **esistente**. `docId` → path `{pDocId}`; `ricalcolo` → query `pRicalcolo`; body = solo array `RIGHE` (stessa struttura riga di `documento`, inclusi `LOTTI`/`MATRICOLE`/`LOCAZIONI` e campi USER):
  ```json
  { "RIGHE": [ { "COD_ART": "KOS", "DES_RIGA": "COSETTA ARTICOLO", "UM": "Pz.", "QUANT_RIGA": 1, "PREZZO_LORDO_VU1": 5.00, "SCONTO_1": 10.00, "SCONTO_2": 5.00 } ] }
  ```
  Obbligatori: almeno una riga in `RIGHE`, con `COD_ART` (esistente in anagrafica) e `QUANT_RIGA` (≠ 0). Transazione atomica. Risposta: `"Codice"` = DOC_RIGA_ID delle righe inserite separati da `/` (stesso ordine della lista).
- **`documento-chiudi`** 🆕 v1.5.0 (endpoint REST `/documento/chiudi/{pDocId}`, resource `ORD_CLI`/`ORD_FOR`/`DDT_ALL`/`APP_FOR`) — chiude **tutte** le righe del documento. `docId` → path `{pDocId}`; body vuoto `{}`; `Content-Type: application/json` obbligatorio. Risposta: `"Codice"` = DOC_ID chiuso.
- **`documento-righe-chiudi`** 🆕 v1.5.0 (endpoint REST `/documento-righe/chiudi/{pDocRigaId}`, resource `ORD_CLI`/`ORD_FOR`/`DDT_ALL`/`APP_FOR`) — chiude una **singola** riga. `docRigaId` → path `{pDocRigaId}`; body vuoto `{}`; `Content-Type: application/json` obbligatorio. Risposta: `"Codice"` = DOC_RIGA_ID chiuso.
- **`PATCH /documento/{pDocId}`** 🆕 (presente in v1.5.3, assente in v1.5.0; §21; header `TcRestApi-Resource` = tipo documento) — varia la **testata**. Body con i **soli campi da variare** (stessi nomi di `documento`, inclusi campi USER): campi assenti = invariati, campo vuoto `""` = azzera il valore. Esempio: `{ "COD_PAGA": "BB30", "DES_DEST_MERCE": "MAGAZZINO PERIFERICO", "INDI_DEST_MERCE": "VIA DELLE INDUSTRIE, 10", "COMUNE_DEST_MERCE": "PESCARA", "CAP_DEST_MERCE": "65128", "PROVINCIA_DEST_MERCE": "PE" }`. Regole: almeno un campo (altrimenti «Nessun campo da variare»); `RIGHE` non ammesso; `DOC_ID`, `AZIENDA_ID`, `COD_CAUS_DOC` non variabili; `COD_CF` deve esistere come cliente/fornitore secondo il tipo (vuoto solo per `MAG_CAR`/`MAG_SCAR`); `COD_PAGA` non vuoto ed esistente; `DATA_DOC` valida; `COD_TIPO_SPESA` + `SPESE_TRASP` = importo manuale di una spesa **già presente** nel documento. Cambiando `COD_PAGA` Target rilegge sconto pagamento, spese e banca (e riporta il nuovo sconto sulle righe); `COD_CF`/`COD_IVA` sono solo assegnati, senza ricalcolo a cascata di listini, destinazioni o IVA di riga. Transazione unica, totali **sempre** ricalcolati. Risposta: `EndPoint:"/documento-mod"`, `Codice` = DOC_ID del path.
- **`PATCH /documento-righe/{pDocId}`** 🆕 (§22) — varia una o più righe esistenti. Body `{ "RIGHE": [ { "DOC_RIGA_ID": "<id>", "QUANT_RIGA": 5 }, { "DOC_RIGA_ID": "<id>", "PREZZO_LORDO_VU1": 2.30, "SCONTO_1": "", "SCONTO_2": "" } ] }` (solo i campi da variare; `""` azzera). ⚠️ Diversamente dalla POST sullo stesso URI **`pRicalcolo` non è previsto** (una chiamata con `pRicalcolo` restituisce errore): i totali sono sempre ricalcolati, una sola volta dopo l'ultima riga. Regole: `RIGHE` obbligatoria, `DOC_RIGA_ID` obbligatorio e appartenente al documento del path, più almeno un campo da variare; `COD_ART` **non variabile** (chiudere/cancellare la riga e inserirne una nuova); `LOTTI`/`MATRICOLE`/`LOCAZIONI` non variabili; `QUANT_RIGA` ≠ 0; `QUANT_RIGA` e `UM` non variabili su righe con lotti/matricole/locazioni né su righe d'ordine evase/chiuse (su un ordine evaso o chiuso nessuna riga è variabile); `SCONTO_n` ≤ 100; `NO_RICALC_PRZ`/`NO_RICALC_SCONTI` salvati come passati. Se nel body ci sono prezzi/sconti sono usati senza ricalcolo; se varia solo la quantità Target ricalcola prezzo da listino (se la riga non ha `NO_RICALC_PRZ=1`) e sconti (se non `NO_RICALC_SCONTI=1`); variando `QUANT_RIGA`/`UM` sono ricalcolati qtà in UM base, peso e colli (salvo `PESO`/`PESO_NETTO`/`NUM_COLLI` nel body); se cambiano quantità, prezzo o deposito i movimenti di magazzino collegati sono rigenerati. Tutte le righe sono controllate prima di iniziare: se una fallisce **nessuna** è variata (l'`Esito` indica posizione e `DOC_RIGA_ID`). Risposta: `EndPoint:"/documento-righe-mod"`, `Codice` = DOC_ID.
- **`DELETE /documento-righe/{pDocId}?pDocRigaId=<DOC_RIGA_ID>`** 🆕 (§23) — cancella **una** riga; nessun body (eventuale body ignorato); i valori vanno percent-encoded (anche `&`). Risposta: `EndPoint:"/documento-righe-cancella"`, `Codice` = DOC_RIGA_ID. Totali ricalcolati nella stessa transazione. **Non cancellabili:** ordini (`ORD_CLI`, `ORD_FOR`) evasi anche parzialmente; DDT (`DDT_CLI`, `DDT_FOR`) fatturati; fatture (`FATT_CLI`, `FATT_FOR`) registrate in contabilità (messaggi tipo «Riga d'ordine evasa: impossibile cancellare»).
- **`DELETE /documento/{pDocId}`** 🆕 (§24) — cancella testata, righe e tabelle collegate; nessun body. Stesse regole di non cancellabilità di cui sopra. Se il documento è l'**ultimo della serie** il numero torna disponibile e sarà riassegnato al prossimo; altrimenti resta un salto di numerazione. ⚠️ **Irreversibile** (transazione unica, non annullabile): in un flusso conviene sempre un passaggio di conferma umana o un pre-check con `documenti`. Risposta: `EndPoint:"/documento-cancella"`, `Codice` = DOC_ID.
- **`datamining`** 🆕 (`POST /datamining`, §25; `TcRestApi-Resource` valorizzato, es. `DM`; il token deve essere abilitato al **servizio SQL (query)**, stessa abilitazione) — calcola un datamining Target (tabelle REPORTS/COLUMNS_TAB) e restituisce colonne, righe e totali. Body: `{ "COD_REP": "ART.01", "COD_FILTRO": "FATT_DAT", "FILTRI": [ { "TABELLA": "FATT_CLI_RIGHE", "COLONNA": "DATA_DOC", "VALORE": "01.01.2017" }, { "COLONNA": "DATA_DOC", "VALORE": "31.12.2017" } ], "FILTRO": "ART_ANA.COD_CAT LIKE 'MP%'", "NUM_RECS": 100 }`. Solo `COD_REP` è obbligatorio. `COD_FILTRO` assente → filtro del datamining (`REPORTS.FILTRO_RICERCA`), se vuoto nessun filtro standard. `FILTRO` = condizione SQL aggiuntiva in AND (vietati INSERT/UPDATE/DELETE/ALTER/DROP/TRUNCATE). `NUM_RECS` assente → «Numero record» dei codici fissi, altrimenti 100. Ogni voce di `FILTRI` assegna un valore a una riga del filtro standard: `COLONNA` (obbl.), `TABELLA` (se la colonna compare su più tabelle), `VALORE` (vuoto = riga non applicata), `OPERATORE` (sostituisce quello standard; ammessi `= <> < > <= >= LIKE IN IS NULL`); le voci vanno sulla prima riga libera con quella colonna, nell'ordine (una colonna ripetuta, es. `DATA_DOC >=` e `<=`, prende i valori in sequenza); `LIKE` aggiunge `%`, `IN` separa i valori con `;`, `IS NULL` senza valore; date `GG.MM.AAAA`/`AAAA-MM-GG`/`GG/MM/AAAA` (data non valida = errore). Risposta: `Codice` = COD_REP e campo `JSON` in **Base64** che decodificato contiene `COD_REP`, `DES_REP`, `COD_FILTRO`, `NUM_RIGHE` (calcolate), `NUM_RIGHE_RESTITUITE` (≤ `NUM_RECS`), `COLONNE[]` (`COL_NAME`, `COL_DESC`, `COL_TYPE`, `FLAG_TOTAL`), `RIGHE[]` (un oggetto per riga) e `TOTALI` (calcolati su **tutte** le righe, anche oltre `NUM_RECS`). Se `REPORTS.STRINGA_UTENTI_AMMESSI` è valorizzato, l'utente Target impostato sul server REST deve essere nell'elenco («Utente … non abilitato al datamining …»). Altri `Esito` d'errore: «Indicare il codice del datamining (COD_REP)», «Datamining non trovato (…)», «Filtro standard non trovato (…)», «Campo … non presente nel filtro standard o già assegnato (filtro n)», «Operatore non ammesso: … (filtro n)», «Data non valida per …», «Errore SQL datamining …». Colonne con formula calcolate lato server come in Target; colonne `FLAG_NO_DISPLAY` escluse da `COLONNE`/`RIGHE`.
- ⚠️ **`lookup`** — **DEPRECATO in v1.5.0** (endpoint `/lookup`, resource `SQL`, body `{ "SQL": "SELECT ..." }`): non più nella doc ufficiale. Mantenuto solo per i flussi legacy che lo usano; non usarlo in nuovi flussi (vedi parametro `sql`).
- **`documenti` / `clienti` / `fornitori` / `contatti` / `articoli`** (ricerche): body `{"FILTRO": "...", "SORT": "...", "COLONNE": "COL1;COL2", "NUM_RECS": 100, "DOC_ID"/"COD_CF"/"COD_ART": "..."}` — tutti facoltativi ma **almeno un filtro o un codice è richiesto dal blocco** (vedi avvertenza sopra). `SORT` e `NUM_RECS` sono ufficiali da v1.5.0 (§6.5). Per ottenere solo le righe di un documento, v1.5.0 (§6.4) documenta il suffisso risorsa `_RIGHE` (es. `DDT_CLI_RIGHE`) sulla ricerca `documenti` — non esposto come parametro dedicato del blocco: se serve, usa `rawBody` o imposta la risorsa con suffisso. `articoli` accetta anche `COD_SECONDARIO_ART` (§13.4).

- **Riferimenti incrociati:** AI Analysis (`lastAiOutput` come `payloadFromKey`, L1481); Set Fields — citato come fonte tipica del payload (⚠️ NON DOCUMENTATO come blocco separato in questa estrazione); Code JS (`CodeJs`) — citato come fonte tipica del payload; `../../erp/connectors.md` (uso applicato all'ordine cliente).
