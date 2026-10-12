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
| `schema_tabelle_ordini.sql` | Script SQL idempotente delle 4 tabelle (segnaposto `<PREFISSO_TABELLE>`) |
| `schema_tabelle_decox.sql` | Lo stesso script già compilato col prefisso `THINKAI_DECOX_` (prefisso ipotizzato: da confermare) |

Uso: `python compila_profilo.py profilo-<cliente>.privato.json` → `flusso-<cliente>.privato.json.js`
da incollare in Studio. Il file compilato contiene dati reali: non committarlo.

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
2. Eseguire sul DB collegato alla Chat lo **script di schema** (`schema_tabelle_*.sql`, vedi sotto); l'ultima SELECT deve dare 4 / 6 / 2.
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
1. **DDL tabelle**: ricostruito dalle colonne che il flusso legge/scrive, non è lo script originale del flusso di riferimento (non fornito). Rispetto al DDL di esempio della skill ho allargato `EMAIL_ERRORE` (4000, il flusso tronca a 3990), `NOTE` (1000) e `NUMERO_ORDINE` (100): con le lunghezze dell'esempio le scritture sarebbero fallite. Da far rivedere al DBA; non eseguito su SQL Server reale (solo parsing T-SQL e confronto colonne flusso/DDL).
2. **R18**: il flusso usa `String()`/`Number()` in ~460 punti (errori di `test_codejs.py`, 0 di `valida_flusso.py`); in produzione sul flusso di riferimento funziona.
   Il codice aggiunto qui non li usa. Da confermare se il sandbox li accetta prima di toccare il resto.
3. `FileWrite` con `{sentinellaSandboxPath}` e un `FileMove` senza `allowedRoot` (avvisi ereditati): non modificati.
4. `aliasClienti` parte vuoto: gli alias del flusso di riferimento sono dati dei *suoi* clienti.
5. Nessun bump di versione del flusso di riferimento: questa è una copia derivata.
