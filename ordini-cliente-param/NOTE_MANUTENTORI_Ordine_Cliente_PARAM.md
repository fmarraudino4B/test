# Note manutentori — Ordine Cliente PARAM v2.0.0

Flusso A1 (ordine cliente da PDF verso TargetCross) **parametrizzato**: derivato dal flusso di
riferimento Ordine Cliente v1.5.6, con tutto il cliente-specifico spostato in M00 / segnaposto.
Nessun dato reale di cliente in questa cartella (R20): il profilo reale è un file privato.

## File
| File | Scopo |
|---|---|
| `Ordine_Cliente_PARAM_v2.0.0_flusso.js` | DSL "Modalità Sviluppatore" con segnaposto `<…>` |
| `profilo-cliente-ordini.template.json` | Profilo da copiare come `profilo-<cliente>.privato.json` (fuori repo) |
| `compila_profilo.py` | Sostituisce i segnaposto, rifiuta valori mancanti, controlla la sintassi; con `--schema` genera lo SQL delle tabelle |
| `schema_tabelle_ordini.sql` | Script SQL delle 4 tabelle, **derivato dallo script originale del flusso di riferimento** con il solo prefisso parametrico `<PREFISSO_TABELLE>` |
| `schema_tabelle_decox.sql` | Lo stesso script già compilato col prefisso `THINKAI_DECOX_` (prefisso ipotizzato: da confermare) |

Uso: `python compila_profilo.py profilo-<cliente>.privato.json` → `flusso-<cliente>.privato.json.js`
da incollare in Studio. Il file compilato contiene dati reali: non committarlo.

## Versione Decox (parziale)
`Ordine_Cliente_DECOX_v2.0.0_flusso.js` è il DSL già compilato con ciò che è noto (agente `DECOX-V2.0.0`, nome breve, prefisso
tabelle `THINKAI_DECOX_` [ipotesi], interruttori e DMS come nel flusso di riferimento, soglie 60/25). **Restano segnaposto** da
sostituire prima dell'uso, nel primo step "Configurazione parametri": `<RAGIONE_SOCIALE_PROPRIA>`, `<PIVA_PROPRIA>`,
`<WORK_ROOT>`, `<CARTELLA_INPUT>`, `<CARTELLA_DMS>`, `<EMAIL_OPERATORE>`, `<CAUSALE_DOC>`, `<SERIE_DOC>`, `<DEPOSITO>`.
In più `<CREDENZIALE_ERP>` compare **11 volte** come valore letterale di `credentialName` (R19): sostituirla con trova-e-sostituisci
(il preflight M00 non la vede). Finché mancano valori, il flusso si ferma al controllo iniziale elencando cosa manca.
In alternativa compilare un profilo privato e rilanciare `compila_profilo.py` (senza `--parziale`).

## Cosa è stato parametrizzato (rispetto al flusso v1.5.6)
- **Segnaposto non interpolabili dal motore** (R19): `<CREDENZIALE_ERP>` (11 `GestionaleSend`),
  `<PREFISSO_TABELLE>` (4 tabelle `…ORDINI_LOG`, `…ORDINI_LOG_RIGHE`, `…CLIENTI_PROFILO`, `…ARTICOLI_PROFILO`).
- **M00**: identità (`ownName`, `ownShortName`, `ownShortNameUpper`, `ownVat`), cartelle, email, causale/serie/deposito,
  soglie, alias clienti, DMS. Il preflight rifiuta segnaposto non risolti, P.IVA non a 11 cifre, DMS attivo senza classe/chiave.
- **Prompt AI di estrazione**: nome e P.IVA propri via `{ownName}`, `{ownVat}`, `{ownShortName}`,
  `{ownShortNameUpper}` (interpolati dal motore). Rimosso il fallback P.IVA cablato (`|| "<piva>"` ×3).
- **Chiavi/valori rinominati** (neutri): `isOffertaPropria`, `emessoDaNoi`, `codiceClienteInterno`,
  `lookupCodiceInterno`, `pivaPropriaLetta`, `offerta_propria_firmata`, `failedOrders|failedArticleLines|failedLearningMappings`,
  idempotency `ordcli-*`. **Non compatibile 1:1** con log/console che leggono i vecchi nomi.
- **Interruttori** (default = regole del flusso di riferimento): `abilitaOffertaPropria` (offerta propria controfirmata = ordine),
  `abilitaKit` (split `A+B+C`), `dmsAttivo` (descrittore DMS; i 3 step DMS sono sotto `if ($.dmsAttivo == "true")`).
- **R17**: rimossi 439 commenti non funzionali (restano `@alias`, `@continueOnFail`, pannelli ForEach). Logica invariata.

## Passi manuali in Studio dopo l'import
1. Creare la credenziale ERP con **lo stesso nome** usato nel profilo (letterale nel DSL). Verificare che **non sia in dry-run** (`erp/gotchas.md` §4).
2. Eseguire sul DB collegato alla Chat lo **script di schema** (`schema_tabelle_*.sql`, vedi sotto); la SELECT finale deve dare `1, 1, 1, 1, 6, 2` (come il preflight del flusso). Eseguire prima sul database di TEST: lo script controlla che esistano `ART_ANA` e `CF_DEST_MERCE` e copia tipo/collation di `COD_CF` e `COD_ART` da TargetCross.
3. Reimpostare il trigger (cron del flusso di riferimento: `*/30 * * * *`, da confermare).
4. **R3**: configurare a mano la Gestione errori dei 3 ForEach (ordini → `failedOrders`, righe articolo → `failedArticleLines`,
   learning → `failedLearningMappings`; continua su errore item, fallisci a fine ciclo).
5. Creare le cartelle (ingresso, DMS) sotto `workRoot`; collegare la Chat/connessione dati.

## Verificato vs testato
- **Testato su dati sintetici**: sintassi (`node --check`), `valida_flusso.py` → 0 errori; `anonimizza.py verifica` → 0 rilievi;
  `compila_profilo.py` con profilo fittizio (OK) e vuoto (rifiutato); preflight M00 eseguito con stepdata sintetico (ok / ko).
- **NON verificato su sistema reale**: nessuna run su TargetCross, nessuna interpolazione del prompt verificata, nessun PDF.

## Piano di collaudo
1. `dmsAttivo=false`, 1 PDF d'ordine noto → ordine creato, log scritto, nessun descrittore DMS.
2. Controllare in I/O dello step AI che il prompt contenga nome/P.IVA propri (interpolazione) e che la P.IVA propria non finisca come cliente.
3. Un PDF con kit `A+B+C` (con `abilitaKit` true e false), un'offerta propria controfirmata (true e false: con false → revisione).
4. Cliente assente / P.IVA errata → revisione, nessun documento ERP. Ripetere lo stesso PDF → duplicato bloccato.
5. DMS attivo: descrittore depositato e mail senza avvisi.

## Aperti / da decidere
1. **DDL tabelle**: usato lo script originale del flusso di riferimento (v1.5.6) cambiando solo il prefisso; confrontato riga per riga con il sorgente. Non eseguito su SQL Server qui: collaudare su TEST. Dipende da `ART_ANA` e `CF_DEST_MERCE` (stessa struttura TargetCross del cliente di riferimento: da confermare per il nuovo cliente).
2. **R18**: il flusso usa `String()`/`Number()` in ~460 punti (errori di `test_codejs.py`, 0 di `valida_flusso.py`); in produzione sul flusso di riferimento funziona.
   Il codice aggiunto qui non li usa. Da confermare se il sandbox li accetta prima di toccare il resto.
3. `FileWrite` con `{sentinellaSandboxPath}` e un `FileMove` senza `allowedRoot` (avvisi ereditati): non modificati.
4. `aliasClienti` parte vuoto: gli alias del flusso di riferimento sono dati dei *suoi* clienti.
5. Nessun bump di versione del flusso di riferimento: questa è una copia derivata.


---

# Variante ORDINE FORNITORE (`ORD_FOR`) — `Ordine_Fornitore_PARAM_v1.0.0_flusso.js`

Derivata dal template cliente (stessa struttura, stesse tabelle di appoggio e stesso script SQL). Compilazione:
`python compila_profilo.py profilo-<cliente>.privato.json --tipo fornitore` (profilo: `profilo-fornitore-ordini.template.json`).

## Cosa cambia rispetto all'ordine cliente
- **Risorsa e anagrafica**: `ORD_FOR` (crea, duplicati, stampa) e endpoint `fornitori` (`clienti` prima). Testi utente "cliente" → "fornitore".
- **Riferimento ordine**: `NUM_ORDINE_FORNITORE` / `DATA_ORDINE_FORNITORE` (nomi presi da `ORD_FOR_SPEC` del catalogo DB;
  ⚠️ **da verificare nel body TcRestAPI**) al posto di `NUM_ORDINE_CLIENTE` / `DATA_ORDINE_CLIENTE`.
- **Prompt AI riscritto** per documenti del fornitore: P.IVA e codice stampato del fornitore, sconti a cascata `30+5` → due sconti,
  codice a capo ricomposto, sigla modello dalla descrizione, `stabilimentoTesto` = blocco "Destinazione merce".
- **Destinazione merce clienti disattivata** (`hasDestination` sempre falso): la destinazione è lo **stabilimento**.
- **Stabilimento** (parametro `stabilimenti`, step iniziale): dal testo di destinazione si individua lo stabilimento tramite gli `alias`;
  da lì arrivano causale, serie e deposito. Non riconosciuto / ambiguo / senza deposito → **revisione**, nessun documento.
- **Ordine tra filiali**: se il fornitore è una filiale del gruppo (il nome contiene `ownShortName`), la causale è quella "ordine a filiale"
  della matrice `filiali` dello stabilimento di destinazione; il fornitore si risolve **solo** col codice stampato (`Codice:`), verificato in
  anagrafica `fornitori` e con nome coerente con gli alias della filiale; altrimenti revisione.
- **Codice stampato** (`usaCodiceFornitoreStampato`): `Codice:` = `COD_CF`, verificato in anagrafica; per fornitori esterni anche il nome deve essere coerente.
- Nuovi parametri: `numUmRiga` (ex costante `NUM_UM "2"` del flusso cliente, vuoto = non inviato), `prezzoPolicy`
  (`RICALCOLO_ERP` come il flusso cliente, oppure `DA_DOCUMENTO`: prezzo e sconti del PDF, `FLAG_CALC_PRZ 0`).
- Offerta propria (`OFF_CLI`) non usata: `abilitaOffertaPropria` false. DMS: spento finché non si conosce la classe per gli ordini fornitore.

## Formato del parametro `stabilimenti`
`COD|CAUSALE_ORF|SERIE|DEPOSITO|ALIAS1,ALIAS2|STABDEST=CAUSALE_FILIALE,...` con voci separate da `;` (nessun `;` o `|` nei valori).
Esempio generato dal profilo (`opzioni.stabilimenti`: `codice`, `causale`, `serie`, `deposito`, `alias[]`, `filiali{}`).
Gli alias sono confrontati come parole intere sul testo normalizzato (maiuscolo, senza punteggiatura).

## Verificato vs testato
- **Testato su dati sintetici** (runner Node che esegue gli step reali con output AI *simulato* dai 5 PDF di esempio): 9 scenari —
  ordine a filiale (→ causale `…OFL`/`…OFT`), fornitore esterno (→ `…ORF`), stabilimento non riconosciuto/mancante, filiale senza codice,
  stessa filiale, filiale non riconosciuta, P.IVA propria come fornitore; corpo `ORD_FOR` con e senza prezzo da documento.
- **NON verificato**: l'estrazione AI sui PDF (output simulato); la lettura reale dei PDF dei fornitori (gli esempi sono autogenerati);
  nessuna chiamata a TargetCross (`fornitori`, `documenti`, `documento` `ORD_FOR`, campi `NUM_ORDINE_FORNITORE`); matching articoli per codice fornitore.

## Aperti (Decox)
1. **Depositi per stabilimento**: vuoti → tutti gli ordini vanno in revisione ("Deposito non configurato per lo stabilimento X").
2. **Alias**: configurati solo VR=`CEREA`, MB=`LISSONE`, TO=`ORBASSANO` (dai PDF di esempio); mancano CB, NW, TM, PS e il deposito Porcelli (`1NWOFZ`, non mappato).
3. Verificare il nome campi `NUM_ORDINE_FORNITORE`/`DATA_ORDINE_FORNITORE`, `NUM_UM` e la politica prezzi.
4. Credenziale ERP (`<CREDENZIALE_ERP>`, 11 punti) e tabelle `…CLIENTI_PROFILO` (contiene i profili fornitore: nome storico).
5. Righe con data di consegna diverse: il flusso usa la prima in testata (come il flusso cliente).

---

# Correzioni dalla run 97 (collaudo Decox, 0 file in ingresso)

La run ha passato configurazione, preflight TargetCross e controllo tabelle, poi ha mostrato due difetti **introdotti dalla mia
versione parametrizzata** (non presenti nel flusso di riferimento così come era configurato in Studio). Corretti in tutti i template.

1. **Recovery errore tecnico eseguito senza errore** (4 step rossi "idempotencyKey contiene placeholder non risolti": log, mail, spostamento file).
   Causa: nell'import dal DSL i passi "ON ITEM ERROR" diventano normali step dopo il ciclo; avevo inoltre tolto il commento-marcatore
   `// ┌─ ON ITEM ERROR …` insieme agli altri commenti (R17). Con 0 file i passi giravano comunque, e con file avrebbero potuto
   spedire una mail di errore falsa.
   Fix: lo step "Prepara recovery errore tecnico" imposta `recoveryErrore` (vero solo con `__lastItemErrorMessage` o `failedOrders`
   valorizzati) e i 4 passi successivi stanno sotto `if ($.recoveryErrore == "true")` (regola R-23). Il marcatore è stato ripristinato.
   Provato con tre stepdata: nessun errore → falso; con messaggio d'errore → vero; con elemento fallito → vero.
2. **Sentinella `_worker-attivo.json` non depositata** ("Path di mutazione fuori dalla root consentita"). Due cause: il `FileWrite`
   usava come path l'intera variabile `{sentinellaSandboxPath}` (non sostituita: il file veniva scritto con nome letterale, vedi
   `erp/gotchas.md` §1) e il `FileMove` applicava `allowedRoot` anche al sorgente nella sandbox.
   Fix: path letterale `sentinella/_worker-attivo.json`, sorgente `{lastFileWritten}` e nessun `allowedRoot` (come già il deposito
   del descrittore DMS). ⚠️ Da riverificare in Studio: il file deve comparire nella cartella ordini a ogni giro.

**Ancora manuale (R3):** configurare la *Gestione errori* del ForEach in Studio (continua sull'elemento in errore, fallisci a fine ciclo,
`failedOrders`); senza, un file in errore ferma l'intera coda e il recovery non parte. Nell'import la nota del ForEach lo ricorda.

---

# Run 101 (primo PDF reale): memoria articoli condivisa col flusso DDT

La run ha elaborato `…1MBOF-0001894.pdf` (estrazione AI, fornitore dal codice stampato, profilo di default) e si è fermata alla
query "Consulta memoria autonoma articolo": `Il nome di colonna 'CODICE_CLIENTE_NORM' non è valido`.

**Causa.** Nel database Decox `THINKAI_DECOX_ARTICOLI_PROFILO` esisteva già: è la memoria articoli del flusso **DDT fornitori**
e usa `CODICE_FORNITORE_NORM` / `CODICE_FORNITORE_RAW` (più `LAST_LOG_KEY`). Lo script SQL non la ricrea se esiste, e il controllo
iniziale verifica solo 6 colonne di auto-learning, quindi lo schema risultava "pronto". Le altre tre tabelle (`…ORDINI_LOG`,
`…ORDINI_LOG_RIGHE`, `…CLIENTI_PROFILO`) sono quelle dell'ordine e coincidono col flusso.

**Fix.** Il template fornitore ora usa `CODICE_FORNITORE_NORM/RAW` su `ARTICOLI_PROFILO` (lettura memoria, apprendimento, aggiornamento);
il log righe `…ORDINI_LOG_RIGHE` mantiene `CODICE_CLIENTE_*` (struttura già creata). Nuovo `schema_tabelle_ordini_fornitore.sql`
(`compila_profilo.py --schema --tipo fornitore`) con la stessa convenzione per installazioni nuove; `schema_tabelle_decox.sql` rigenerato.
La tabella è **condivisa**: i codici fornitore appresi dal DDT servono anche agli ordini (e viceversa).

**Da tenere d'occhio.**
- Il codice normalizzato (`CODICE_FORNITORE_NORM`) nell'ordine è `MAIUSCOLO senza caratteri non alfanumerici`: verificare che il DDT usi la
  stessa regola, altrimenti non ritrova le memorie (nessun errore, solo meno match).
- L'ordine scrive `ORIGINE='IMPORT'`, `CREATED_BY='WORKFORCE_AUTO'`, `LAST_CORRELATION_ID`; il DDT usa anche `LAST_LOG_KEY` (non valorizzato dall'ordine).
- Lo script non modifica tabelle esistenti: per future installazioni controllare sempre le colonne (non solo l'esistenza).

**Ripetere la prova.** Il PDF è rimasto in `…\processing\<prefisso>_2026-1MBOF-0001894.pdf` (rimetterlo in `ORDINI` col nome originale);
la riga di log `IN_ELABORAZIONE` viene chiusa come orfana al giro successivo. Configurare la Gestione errori del ForEach (R3), altrimenti
un errore ferma tutta la coda.

---

# Pulizia tabelle di appoggio

`pulizia_tabelle_ordini.sql` (generico, `--pulizia` del compilatore; versione Decox: `pulizia_tabelle_decox.sql`). **Anteprima di default**
(`@Conferma = 0`: conta, mostra la composizione della memoria e fa ROLLBACK). Parametri: `@PulisciLog` (log testate e righe, anche righe orfane
in modalità completa), `@PulisciMemoria` (solo righe `ARTICOLI_PROFILO` con `ORIGINE='IMPORT'`, `CREATED_BY='WORKFORCE_AUTO'` e
`LAST_CORRELATION_ID` presente nei log selezionati), `@PulisciProfili` (configurazione fornitori, spento), finestra `@Dal`/`@Fino`.
Non tocca le tabelle del DDT né quelle TargetCross; `ARTICOLI_PROFILO` è condivisa col DDT e non viene mai svuotata in blocco.
Non eseguito su SQL Server reale (solo parsing); provare su TEST e fare un backup in produzione.
