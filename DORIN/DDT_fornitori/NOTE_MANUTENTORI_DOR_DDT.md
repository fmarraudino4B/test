# DOR DDT fornitori v1.2.3 MySQL: note per i manutentori

Flusso ThinkAI WorkForce per registrare i DDT fornitori su Target Cross. Deriva dal flusso
Decox `DEC DDT fornitori v1.2.3`, che gira su SQL Server, ed è adattato a Dorin, che usa
**Target Cross su MySQL**.

**Stato: testato su dati sintetici, NON ancora verificato sul sistema reale di Dorin.**

| File | Contenuto |
|---|---|
| `adatta_mysql.py` | Generatore. Legge l'export Decox (unica fonte) e applica modifiche chirurgiche con il controllo delle occorrenze. |
| `DOR_DDT_fornitori_v1.2.3-mysql.thinkaiagent.json` | Artefatto generato da importare in Studio. Contiene solo segnaposto `DA_CONFIGURARE_*`. |
| `profilo-dorin.template.json` | Dati cliente da compilare nella copia privata `profilo-dorin.privato.json`, esclusa da git. |
| `sql/ddl_mysql_thinkai_dorin.sql` | DDL MySQL delle 5 tabelle di appoggio. |
| `sql/verifica_prerequisiti_mysql.sql` | Controlli in sola lettura da eseguire sul database di Dorin. |
| `collaudo/test_sql_mysql.py` | Collaudo automatico su MySQL con dati sintetici. |

## 1. Verifica del flusso Decox

Ho censito i 200 step del flusso, inclusi quelli annidati in cicli, rami e switch. Gli elementi che dipendono dal
database sono:

| Tipo | Numero | Dipende dal dialetto SQL? |
|---|---|---|
| Query SQL (`Query`) | 14 | **Sì.** 11 su 14 usano T-SQL: `TOP`, `ISNULL`, `LEN`, `CONVERT`, `dbo.`. |
| Insert SQL (`SqlInsert`) | 5 | Sì, per lo schema `dbo.` e per i tipi dei valori. |
| Update SQL (`SqlUpdate`) | 9 | Sì: `dbo.`, `ESCAPE '\'` e tipi dei valori. |
| Chiamate TcRestAPI | 9 | Solo per i filtri `fornitori`, che sono testo SQL eseguito dal server TcRestAPI. |
| CodeJs | 84 | Solo quelli che preparano valori per SQL: timestamp, pattern LIKE, filtri. |

I placeholder `{chiave}` nei nodi SQL sono **parametri bound**: l'escape dei valori non
dipende dal dialetto. Restano invece da convertire il testo SQL e i formati dei valori.

### Problemi verificati su MySQL 8.0.46 (sql_mode strict di default)

| # | Costrutto Decox | Comportamento su MySQL | Evidenza |
|---|---|---|---|
| P1 | `TOP n`, `DISTINCT TOP n` | Errore di sintassi 1064 | Collaudo; Target Cross 4BPatch_NM06541 |
| P2 | `ISNULL(a, b)` | Errore 1582: `ISNULL` accetta un solo argomento | Collaudo |
| P3 | `LEN(x)` | Errore 1064 | Collaudo; Target Cross 4BPatch_LR06835 |
| P4 | `CONVERT(int, x)`, `CONVERT(date, x)` | Errore 1064, perché in MySQL l'ordine degli argomenti è invertito | Collaudo |
| P5 | `dbo.TABELLA` | In MySQL `dbo` sarebbe il nome di un database | Analisi |
| P6 | `ESCAPE '\'` | Errore 1064: in MySQL `\` fa da escape anche dentro la stringa | Collaudo |
| P7 | `{nowIso}` = `toISOString()` (`...T..Z`) | Errore 1292 su DATETIME: il suffisso `Z` viene rifiutato | Collaudo |
| P8 | `''` su colonne INT/DECIMAL/DATE | Errori 1366/1292 in strict. SQL Server invece converte in 0 o 1900-01-01 | Collaudo |
| P9 | `INFORMATION_SCHEMA.TABLES` senza schema | Conta le tabelle di **tutti** i database del server | Analisi |
| P10 | Data `gg/mm/aaaa` su una colonna DATE | Errore 1292 | Collaudo |
| P11 | Confronto `=` con spazi finali | Con collation NO PAD (default 8.0) `'ABC  ' <> 'ABC'` | Collaudo; da verificare su Dorin (§4) |

## 2. Modifiche (generate da `adatta_mysql.py`)

| Step (alias) | Modifica | Problema |
|---|---|---|
| Verifica esistenza tabelle di appoggio | `TABLE_SCHEMA = DATABASE()`, `UPPER(TABLE_NAME)`, **5** tabelle (prima 3, staging escluso) | P9 |
| Valuta schema DB | Attese 5 tabelle | P9 |
| Anti-duplicato su mittente+numero+data | `COALESCE`, `TRIM`, `LIMIT 1` | P1, P2 |
| Flusso 1 / Flusso 1-bis / Aggancia riga d'ordine | `LIMIT n`, `CAST(x AS SIGNED)`, `COALESCE` | P1, P2, P4 |
| Memoria: cerca corrispondenza | `CHAR_LENGTH`, `COALESCE`, `LIMIT 1` | P1, P2, P3 |
| Metodo B / Metodo C | `LIMIT 5` / `DISTINCT … LIMIT 3` | P1 |
| Leggi prezzo e sconti | `LIMIT 1` | P1 |
| Recupero post-timeout su DDT_FOR | Intervallo `[data, data + 1 giorno)` con `CAST(... AS DATE)`; usa l'indice | P1, P4 |
| Bonifica sentinella `'0'` | `TRIM` (forma equivalente) | — |
| Propaga CREATO alle parti del gruppo | `ESCAPE '!'` e pattern costruito con `!` (nel CodeJs "Chiudi orfani") | P6 |
| Timestamp ISO 8601 (apertura e chiusura) | Formato `AAAA-MM-GG HH:MM:SS.mmm` UTC, accettato anche da `datetime2` | P7 |
| Interpreta esito estrazione / ricerca fornitore | P.IVA ridotta ad alfanumerici prima del filtro TcRestAPI | Sicurezza del filtro testuale |
| Serve il fallback per ragione sociale? | Rimosso `\` dalla ragione sociale prima del filtro `LIKE` | `\` è un escape in MySQL |
| Valida configurazione | Rese obbligatorie anche `mappaDestinazioni`, `mappaDepositiDestinazione` e `catalogoCausaliDestinazioneDdt` | Nuovo cliente: fail-closed |
| Tutti i nodi SQL, messaggi, oggetti mail, alias | `dbo.` rimosso; `THINKAI_DECOX_*` → `THINKAI_DORIN_*`; `DECOX` → `DORIN`; chiavi di idempotenza `dorin-*` | P5 |
| Estrai dati dal DDT (AI) | Nome cliente reso parametrico. Esempi con dati reali (indirizzo di filiale, P.IVA di un fornitore, numeri d'ordine, riferimento cliente) sostituiti da valori fittizi con lo stesso formato | Repository pubblico, riuso multi-cliente |
| Configurazione (M00) | Valori Decox sostituiti con i segnaposto `DA_CONFIGURARE_*` (vedi sotto) | Privacy |

Le tabelle di appoggio sono state progettate per MySQL strict (P8, P10):

- **VARCHAR** dove il flusso può passare `''` o testo grezzo:
  - `DATA_DDT` (`AAAAMMGG`);
  - date di staging in formato `gg/mm/aaaa`;
  - `QUANTITA` e `PREZZO_UNITARIO` del log righe;
  - ID d'ordine.
- **Tipi numerici** solo dove il flusso garantisce un numero.
- Mantenuto il vincolo `CK_*_STATO`, che esisteva in Decox: valori ammessi `IN_ELABORAZIONE`, `CREATO`, `REVISIONE`, `ERRORE_ERP`.
- `UNIQUE (COD_CF, CODICE_FORNITORE_NORM)` sul profilo articoli rende sicuro l'auto-learning
  in caso di run concorrenti.

**Non cambiano** la logica di matching (cascata Memoria → EAN → Brand → A → B → C), gli
endpoint TcRestAPI, la gestione multi-parte e quella di errori e notifiche.

## 3. Collaudo eseguito (dati sintetici)

```
python adatta_mysql.py <Flussi_Workforce>/DECOX/DDT_fornitori/DEC_DDT_fornitori_v1.2.3.thinkaiagent.json
python collaudo/test_sql_mysql.py DOR_DDT_fornitori_v1.2.3-mysql.thinkaiagent.json --user <u> --password <p>
```

Esito su MySQL 8.0.46 (strict, collation `utf8mb4_0900_ai_ci` NO PAD): **490 controlli
superati, 0 falliti**.

- **Controlli statici**: nessun T-SQL residuo e nessun riferimento al cliente sorgente.
- **CodeJs**: `node --check` sugli 84 corpi; i CodeJs modificati sono stati eseguiti
  (timestamp, pattern di gruppo, P.IVA, ragione sociale con `'` e `\`, controllo schema).
- **Nodi SQL**: tutti i 28 nodi eseguiti con parametri bound, con valori tipici e con valori
  vuoti. Il DDL è stato applicato due volte per verificarne l'idempotenza.
- **Scenario**, con asserzioni su:
  - claim;
  - bonifica della sentinella;
  - ordine trovato per riferimento, numero più anno precedente, numero conferma con spazi finali;
  - esclusione delle righe d'ordine già evase;
  - memoria articoli (esclusione di `ORDINE_FOR` e del codice vuoto, vincolo UNIQUE);
  - metodi B e C;
  - prezzo dall'ordine;
  - staging multi-parte con upsert;
  - recupero post-timeout con `DATA_DOC` comprensiva di ora;
  - propagazione CREATO con **trappola sull'underscore**: `DDT_ACMEX123` non viene toccato;
  - anti-duplicato dopo la registrazione;
  - CHECK sullo STATO.

**Controprova**: la stessa variante con le sole tabelle rinominate (nessuna conversione)
produce 36 rilievi, tra cui gli errori 1064 su `TOP`, `ISNULL`, `LEN`, `CONVERT` ed
`ESCAPE '\'`.

Il validatore DSL della skill (`valida_flusso.py`) lavora sul formato `.js` e non su
`.thinkaiagent.json`, quindi non è stato eseguito.

## 4. Da verificare prima del collaudo reale

1. ⚠️ **NON DOCUMENTATO: connessione dati MySQL in WorkForce.** La documentazione dei
   blocchi `Query`, `SqlInsert` e `SqlUpdate` non cita MySQL. Va verificato in Studio che:
   - la connessione dati dell'agente sia MySQL;
   - `SqlInsert`/`SqlUpdate` leggano lo schema delle tabelle MySQL;
   - un valore `null` venga passato come NULL o `''` e non come testo letterale.
2. **TcRestAPI su MySQL.** Il filtro `CF.P_IVA_CF='…'` e la creazione di `DDT_FOR` passano
   dal server TcRestAPI di Dorin, che deve essere configurato sul database MySQL. Si collauda
   con lo step "Test connessione ERP".
3. **Esito di `sql/verifica_prerequisiti_mysql.sql`** sul database di Dorin:
   - versione e `sql_mode`;
   - `lower_case_table_names` (con 0 i nomi tabella devono essere maiuscoli come nel flusso);
   - collation NO PAD e spazi finali sui codici (P11);
   - tipo di `DDT_FOR.DATA_DOC`;
   - lunghezze di `COD_ART` e `COD_CF` rispetto al DDL (50 e 30).
4. **Dati di Dorin** (segnaposto in M00):
   - cartelle di lavoro e mail dell'operatore;
   - P.IVA e ragione sociale;
   - mappe destinazione → codice → deposito;
   - catalogo delle causali `COD:DTR` / `COD:RSC`;
   - nome della credenziale TcRestAPI.

   Con una sola sede basta una voce per ciascuna mappa.
5. **Prompt AI.** Restano i nomi dei fornitori del parco Decox citati come esempi (Franke,
   Candy/Haier, GM TOP, Campra Marmi). Gli ID d'ordine d'esempio sono ora fittizi
   (`2026-1XXOF-0000123`): vanno sostituiti con il formato reale di Dorin e i pattern vanno
   rivisti sui DDT reali dei fornitori di Dorin. `anonimizza.py verifica` segnala solo questi
   due ID fittizi.
6. **MySQL 5.7.** I `CHECK` non vengono applicati (servono 8.0.16+); il resto del DDL è
   compatibile.

## 5. Rilievi preesistenti nel flusso Decox (non modificati, da valutare anche per Decox)

- Le `idempotencyKey` di mail e chiusura log contengono `{nowIso}`. La chiave cambia a ogni
  run, quindi l'idempotenza non protegge da un replay (regola R10).
- `String()`/`Number()` compaiono 92 volte nei CodeJs. Se il flusso Decox è in
  esercizio, questo smentisce la regola R18 della skill, che va aggiornata in
  `conflitti-risolti.md`.
- I parametri `claimStaleMinutes` e `riscritturaStaleMinutes` sono configurati ma non letti
  da nessuno step.
- Metodo C (`DDT_FOR_RIGHE` ⨝ `DDT_FOR`) e "Leggi prezzo e sconti" non filtrano per
  `AZIENDA_ID`. È rilevante solo con più aziende nello stesso database.
- `RIGA_NUMERO` dello staging viene da `Number(r.pos)`. Con un valore `pos` non numerico
  estratto dall'AI diventa `NaN` e l'insert fallisce, su entrambi i database.
- Nel flusso Decox il controllo schema verificava 3 tabelle su 5 e la P.IVA entrava nel filtro
  TcRestAPI senza pulizia. Entrambi i punti sono corretti nella versione Dorin.

## 6. Passi manuali in Studio

1. Creare le tabelle con `sql/ddl_mysql_thinkai_dorin.sql`. L'utente WorkForce deve avere
   SELECT su Target Cross e SELECT/INSERT/UPDATE sulle tabelle `THINKAI_DORIN_*`.
2. Creare la credenziale TcRestAPI e la connessione dati MySQL; collegare la Chat dell'agente
   alla connessione MySQL.
3. Compilare `profilo-dorin.privato.json`, rigenerare con `--profilo` e importare il JSON
   generato.
4. Configurare a mano la **Gestione errori dei ForEach** (R3): il round-trip dall'export non
   è garantito.
5. Prima run su una copia della cartella di scansione con 3-5 DDT già noti.

## 7. Piano di collaudo sul sistema reale

| # | Caso | Esito atteso |
|---|---|---|
| 1 | DDT con riferimento d'ordine sulla riga | `CREATO`; righe agganciate all'ordine; prezzo e sconti dall'ordine |
| 2 | DDT senza riferimento, articoli già appresi | `CREATO` tramite memoria |
| 3 | Stesso DDT rielaborato | Nessun nuovo documento (anti-duplicato) |
| 4 | DDT diviso in 2 parti (`__p01of02`, `__p02of02`) | Un solo documento; entrambe le parti in `elaborati`; log CREATO su entrambe |
| 5 | Reso (causale RSC) di una destinazione senza RSC configurata | `REVISIONE` |
| 6 | Documento "conto riparazione" | `NON_ACQUISTO`, poi `REVISIONE` |
| 7 | Fornitore assente in anagrafica | `REVISIONE` con il motivo nella mail |
| 8 | Run interrotta a metà | Alla run successiva gli orfani tornano in Scansione e vengono rielaborati |

## 8. Rigenerazione

Il JSON non si modifica a mano. Quando esce una nuova versione Decox:

1. aggiornare `VERSIONE_SORGENTE` in `adatta_mysql.py`;
2. rilanciare il generatore, che si ferma se una query Decox è cambiata, così la conversione
   va riallineata in modo consapevole;
3. rilanciare il collaudo.
