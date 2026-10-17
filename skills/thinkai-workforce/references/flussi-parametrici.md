# Flussi parametrici (template multi-azienda) — stato al 15/10/2026

> Dal 10/10/2026 i flussi di produzione sono stati trasformati in **template parametrici**: tutto ciò
> che è dell'azienda sta in M00 o in un `<SEGNAPOSTO>`, e un profilo privato (`profilo-<cliente>.privato.json`,
> fuori repository) genera il flusso pronto da importare. Questo file riassume **cosa è stato fatto,
> cosa è stato corretto dopo le run reali e come si lavora con questi template**. Clienti pseudonimizzati
> (R20): CLI-F, CLI-G, CLI-H; i nomi reali non vanno copiati nella skill.
>
> Fonti: cartelle `ordini-cliente-param/`, `flussi/ddt-fornitori/`, `ordini-clienti/`, `fattibilita-slot/` del
> repository dei flussi e relative `NOTE_MANUTENTORI`. Distinzione sempre esplicita: **verificato su sistema
> reale** vs **testato su dati sintetici**.

## 1. I quattro filoni

| ID | Template | Base | Archetipo | Come si compila | Verificato |
|---|---|---|---|---|---|
| ORD-PARAM | `Ordine_Cliente_PARAM_v2.0.0_flusso.js` (DSL, 107 blocchi, ~3.700 righe) | CLI-A-OC v1.5.6, 439 commenti rimossi (R17) | A1+P (`ORD_CLI` da PDF) | `compila_profilo.py profilo.json` (opz. `--parziale`, `--schema`, `--pulizia`) | Sintetico: `node --check`, validatore 0 errori, preflight M00 con stepdata finto |
| ORD-FOR | `Ordine_Fornitore_PARAM_v1.0.0_flusso.js` | ORD-PARAM | A1 variante `ORD_FOR` (ordine **a** fornitore, multi-stabilimento) | `compila_profilo.py … --tipo fornitore` | Sintetico: 9 scenari con output AI *simulato*; run 101 reale su un PDF (vedi §4) |
| ORD-CLI-MA | `Ordini Clienti – Multi-azienda – V1.34` (`.thinkaiagent.json`, 44 CodeJs) | CLI-H V1.34 | A1 multi-formato (XML, PDF, PDF+Excel, programmazioni) | `applica_profilo.py template profilo out` | Sintetico: 20 casi sugli step modificati; **non** su sistema reale |
| DDT-FOR6 | `DDT Fornitori 6 casi PARAMETRICO V2.0` (`.thinkaiagent.json`, 47 CodeJs) | CLI-F V1.51 | A2+P (DDT conto lavoro, 6 flussi) | `applica_profilo.py template profilo out` | Sintetico: 37 test funzionali; rigenerato = V1.51 salvo deposito informativo del log |
| FATT-SLOT | solo **specifica** + profilo + script di scoperta schema | — | A1 (front) → A8 (sola lettura) | — | Nessun DSL: attesa dell'output di `01_scoperta_schema.sql` |

Due modalità di compilazione, scegli in base al formato: **DSL** (`.js`, segnaposto `<NOME>` sostituiti da
`compila_profilo.py`) oppure **export `.thinkaiagent.json`** (step di configurazione compilato da
`applica_profilo.py` + `wfjson.py`, che legge e scrive anche gli step annidati). Il compilatore **rifiuta**
valori mancanti, segnaposto residui, P.IVA ≠ 11 cifre, e controlla la sintassi con `node --check`; con
`--parziale` lascia i mancanti come `<SEGNAPOSTO>` e li elenca (il preflight M00 del flusso blocca comunque
l'esecuzione, elencando cosa manca).

## 2. Cosa si parametrizza, e dove (regola per scegliere)

| Tipo di valore | Dove va | Perché |
|---|---|---|
| Identità (`ownName`, `ownVat`, `ownShortName[Upper]`), cartelle, email, causale/serie/deposito, soglie, interruttori | **M00** (primo step) | Interpolati dal motore: modificabili da Studio senza rigenerare |
| `credentialName` degli step `GestionaleSend` | **Segnaposto letterale** (`<CREDENZIALE_ERP>`) sostituito dal compilatore | Non interpolabile (R19): 11 occorrenze nel flusso ordini; il preflight M00 **non** le vede |
| Prefisso tabelle di appoggio (`<PREFISSO_TABELLE>`) | **Segnaposto letterale** | Il nome tabella negli step SQL non è interpolabile (R24) |
| Prefisso idempotenza, nome agente, tag | Compilatore | Derivati dalla sigla |
| Mappe per flusso/stabilimento/deposito | M00 come **stringa** (JSON o formato a separatori) | Tutti i valori M00 sono stringhe (R9/R18) |

Un profilo con i valori del flusso di origine deve **riprodurre il flusso originale** salvo le voci
dichiarate in `NOTE_MANUTENTORI` (test di regressione del template).

### Interruttori e parametri nuovi (non erano nei profili della skill v2)

| Parametro | Flusso | Significato / default |
|---|---|---|
| `abilitaOffertaPropria` | ORD | Offerta propria controfirmata = ordine (default come il flusso di origine); con `false` → revisione |
| `abilitaKit` | ORD | Split di codici `A+B+C` in più righe |
| `dmsAttivo` (+ classe, chiave) | ORD, ORD-FOR | I 3 step DMS stanno sotto `if ($.dmsAttivo == "true")`; il preflight rifiuta DMS attivo senza classe/chiave |
| `aliasClienti` | ORD | Parte **vuoto**: gli alias sono dati dei clienti del flusso di origine |
| `prezzoPolicy` | ORD-FOR | `RICALCOLO_ERP` (come ORD) o `DA_DOCUMENTO` (prezzo e sconti del PDF, `FLAG_CALC_PRZ 0`) |
| `numUmRiga` | ORD-FOR | Ex costante `NUM_UM "2"`; vuoto = non inviato |
| `usaCodiceFornitoreStampato` | ORD-FOR | `Codice:` stampato = `COD_CF`, verificato in anagrafica `fornitori` |
| `stabilimenti` | ORD-FOR | `COD\|CAUSALE_ORF\|SERIE\|DEPOSITO\|ALIAS1,ALIAS2\|STABDEST=CAUSALE_FILIALE,…` voci separate da `;` (vietati `;` e `\|` nei valori); dal profilo: `opzioni.stabilimenti[{codice,causale,serie,deposito,alias[],filiali{}}]` |
| `depositiJson`, `causaleDefault`, `depositoDefault`, `serieDocRiserva`, `campiTestataJson` | ORD-CLI-MA | Tabella deposito → reparto/causale/serie/campi di testata; ripiego vuoto = revisione; `campiTestata` della voce prevale su `campiTestataJson`; i campi base non si sovrascrivono |
| `causaliPerFlussoJson`, `seriePerFlussoJson`, `depositiPerFlussoJson`, `magazziniPerFlussoJson`, `campoMagazzino`, `codiciCausaleContoLavoroCliente`, `prefissiArticoliJson`, `tolleranzaPesoNettoPerc`, `istruzioniExtraEstrazione` | DDT-FOR6 | Causale/serie/deposito per flusso con jolly `"*"`; `[]` in `prefissiArticoliJson` = davvero nessun prefisso (il ripiego `C00` resta solo se la chiave **manca**) |
| `pivaClientiMatricolaExcel` | ORD-CLI-MA | Clienti PDF+Excel: MATRICOLA dal PDF, CAUSALE di riga dall'Excel (vuoto = regola spenta) |
| `agentCode` | ORD-CLI-MA | Codice registrato in `THINKAI_WF_AGENTI` (Console, vedi la skill `thinkai-novita-ottobre-2026`) |

⚠️ **Campo magazzino** su TcRestAPI (`DDT_FOR`/`ORD_CLI`) e campi `NUM_ORDINE_FORNITORE`/`DATA_ORDINE_FORNITORE`
su `ORD_FOR`: nomi presi dal catalogo DB (`ORD_FOR_SPEC`) o dal solo `COD_DEP` documentato → **DA VERIFICARE**
nel body TcRestAPI prima di mandarli.

## 3. Logiche di dominio emerse (riusabili)

- **Stabilimento di destinazione** (ORD-FOR): dal blocco «Destinazione merce» si individua lo stabilimento via
  `alias` confrontati come **parole intere** sul testo normalizzato (maiuscolo, senza punteggiatura); da lì
  causale/serie/deposito. Non riconosciuto, ambiguo o senza deposito → **revisione**, nessun documento.
- **Ordine tra filiali**: se il fornitore è una filiale del gruppo (il nome contiene `ownShortName`) la causale
  è quella «ordine a filiale» dello stabilimento di destinazione; il fornitore si risolve **solo** col codice
  stampato verificato in anagrafica e con nome coerente con gli alias della filiale; altrimenti revisione.
- **Sconti a cascata** `30+5` → due sconti separati; **codice a capo** ricomposto; sigla modello dalla descrizione.
- **P.IVA propria come fornitore/cliente** → errore esplicito (testato anche nel DDT).
- **Fornitore con P.IVA diversa dalla principale** (DDT): documento creato, nota P.IVA in mail, **nessun** errore tecnico.
- **Serie** (ORD-CLI-MA), in ordine: serie della voce deposito → `CAUS_DOC_SERIE` se univoca → ultimo documento con
  la stessa causale → `serieDocRiserva` → nessuna (la sceglie Target Cross).
- **Righe con date di consegna diverse**: si usa la prima in testata (come il flusso cliente) — punto aperto.
- **Flusso senza causale configurata** (DDT flussi 5/6, ORD-FOR con stabilimento senza deposito): revisione con
  motivo esplicito, mai un default silenzioso.

## 4. Correzioni dalle run reali (valgono per ogni flusso, non solo per questi)

| Run | Sintomo | Causa | Fix / regola |
|---|---|---|---|
| ORD-PARAM run 97 (0 file in ingresso) | 4 step rossi «idempotencyKey contiene placeholder non risolti» (log, mail, move) | Nell'import dal DSL i passi **ON ITEM ERROR** diventano **step normali dopo il ciclo**; il commento-marcatore `// ┌─ ON ITEM ERROR …` era stato tolto con gli altri commenti (R17) | Step «Prepara recovery» che imposta `recoveryErrore` (vero solo con `__lastItemErrorMessage` o `failedOrders` valorizzati) e i passi successivi sotto `if ($.recoveryErrore == "true")`; marcatore **ripristinato** → **R21**, M21 |
| ORD-PARAM run 97 | «Path di mutazione fuori dalla root consentita» sulla sentinella `_worker-attivo.json` | `FileWrite` con `path = {sentinellaSandboxPath}` (variabile intera non sostituita → file con nome letterale) e `FileMove` con `allowedRoot` applicato anche al sorgente nella sandbox | Path letterale `sentinella/_worker-attivo.json`, sorgente `{lastFileWritten}`, **nessun** `allowedRoot` → **R-25**, M15 |
| ORD-FOR run 101 (primo PDF reale) | `Il nome di colonna 'CODICE_CLIENTE_NORM' non è valido` alla query «memoria autonoma articolo» | `…ARTICOLI_PROFILO` **esisteva già**: è la memoria articoli del flusso DDT (colonne `CODICE_FORNITORE_NORM/RAW` + `LAST_LOG_KEY`); lo script SQL non ricrea tabelle esistenti e il preflight controllava solo 6 colonne di auto-learning | Il template fornitore usa `CODICE_FORNITORE_*` su `ARTICOLI_PROFILO` (log righe resta `CODICE_CLIENTE_*`); schema dedicato `schema_tabelle_ordini_fornitore.sql` → **R22** |
| DDT V1.51 → V2.0 | `escMail is not a function` con avviso anagrafica (più P.IVA, flag ruolo, posizioni dismesse) → PDF in errore tecnico | Funzione usata **prima** di essere definita dentro lo step «Costruisci body DDT_FOR» | Definire gli helper in testa al `CodeJs`; testare i rami di avviso, non solo il percorso felice |
| ORD-CLI-MA (fix R5) | Mail con il reparto del file **precedente** | La pulizia di inizio file non azzerava deposito, causale, reparto, serie | Il cleanup (M04) deve elencare **ogni** chiave scritta nel giro |

## 5. Tabelle di appoggio condivise

- Le 4 tabelle dell'ordine: `…ORDINI_LOG`, `…ORDINI_LOG_RIGHE`, `…CLIENTI_PROFILO` (contiene anche i profili
  fornitore: nome storico), `…ARTICOLI_PROFILO`. Script SQL **derivato riga per riga dallo script originale**
  cambiando solo il prefisso (`<PREFISSO_TABELLE>`); controlla che esistano `ART_ANA` e `CF_DEST_MERCE` e copia tipo/
  collation di `COD_CF` e `COD_ART` da TargetCross. **Atteso:** la SELECT finale restituisce `1, 1, 1, 1, 6, 2`.
  Eseguire prima su TEST.
- `ARTICOLI_PROFILO` è **condivisa col flusso DDT**: i codici fornitore appresi dal DDT servono anche agli ordini e
  viceversa. Verifica che la normalizzazione del codice sia la stessa (`MAIUSCOLO senza caratteri non
  alfanumerici`), altrimenti nessun errore ma meno match. L'ordine scrive `ORIGINE='IMPORT'`,
  `CREATED_BY='WORKFORCE_AUTO'`, `LAST_CORRELATION_ID`; il DDT usa anche `LAST_LOG_KEY` (non valorizzato dall'ordine).
- **Pulizia** (`pulizia_tabelle_*.sql`, `compila_profilo.py --pulizia`): **anteprima di default** (`@Conferma = 0`: conta,
  mostra la composizione della memoria, ROLLBACK). Parametri `@PulisciLog` (testate e righe, anche orfane in modalità
  completa), `@PulisciMemoria` (solo righe `ORIGINE='IMPORT'`, `CREATED_BY='WORKFORCE_AUTO'` e
  `LAST_CORRELATION_ID` presente nei log selezionati), `@PulisciProfili` (spento), finestra `@Dal`/`@Fino`. Non tocca
  le tabelle del DDT né TargetCross; `ARTICOLI_PROFILO` non si svuota mai in blocco. Non eseguito su SQL Server reale
  (solo parsing): provare su TEST, backup in produzione.
- Un tentativo rimasto `IN_ELABORAZIONE` viene chiuso come **orfano** al giro successivo (M02).

## 6. Passi manuali in Studio (comuni a tutti i template)

1. Creare la credenziale ERP con **lo stesso nome** usato nel profilo (letterale nel DSL); verificare che non sia in dry-run (`erp/gotchas.md` §4).
2. Eseguire lo script di schema sul DB collegato alla Chat (prima su TEST) e dare INSERT/UPDATE alla connessione dati.
3. Reimpostare il trigger (cron del flusso di origine, es. `*/30 * * * *`, da confermare).
4. **R3**: Gestione errori dei ForEach (continua sull'item, fallisci a fine ciclo, `failedItemsKey`); senza, un file in errore ferma tutta la coda **e il recovery non parte**.
5. Creare le cartelle (ingresso, DMS) sotto `workRoot`; ricollegare la Chat (il collegamento non viene esportato).
6. Registrare l'agente in `THINKAI_WF_AGENTI` se si usa la Console (skill `thinkai-novita-ottobre-2026`).
7. Se il flusso è compilato con `--parziale`: sostituire i segnaposto residui (`<CREDENZIALE_ERP>` con trova-e-sostituisci).

## 7. Piano di collaudo minimo (template ordini)

1. `dmsAttivo=false`, 1 PDF noto → ordine creato, log scritto, nessun descrittore DMS.
2. Nell'I/O dello step AI il prompt contiene nome/P.IVA propri (interpolazione) e la P.IVA propria **non** finisce come cliente.
3. PDF con kit `A+B+C` (`abilitaKit` true/false); offerta propria controfirmata (true/false: con false → revisione).
4. Cliente assente / P.IVA errata → revisione, nessun documento ERP; stesso PDF due volte → duplicato bloccato.
5. DMS attivo: descrittore depositato, mail senza avvisi.
6. **Run con 0 file** (caso run 97): nessuno step di recovery eseguito, nessuna mail di errore, sentinella depositata a ogni giro.
7. ORD-FOR: ordine a filiale, fornitore esterno, stabilimento non riconosciuto/mancante, filiale senza codice, P.IVA propria come fornitore, corpo con e senza prezzo da documento.

## 8. Punti ancora aperti (registrati dalle NOTE_MANUTENTORI)

- **DDL** tabelle non eseguito su SQL Server dalla skill; dipendenza da `ART_ANA` e `CF_DEST_MERCE` da confermare per il cliente nuovo.
- **R18**: nei template ordini `String()`/`Number()` compaiono in ~460 punti (0 errori di `valida_flusso.py`, errori di `test_codejs.py`); in produzione sul flusso di origine funzionano. Il codice nuovo non li usa: **confermare** se il sandbox li accetta prima di toccare il resto (smentita possibile di R18).
- `FileWrite` con `{sentinellaSandboxPath}` (corretto in run 97, da **riverificare in Studio**: la sentinella deve comparire a ogni giro).
- Depositi per stabilimento vuoti → tutti gli ordini in revisione («Deposito non configurato per lo stabilimento X»); alias degli stabilimenti incompleti.
- Campi `NUM_ORDINE_FORNITORE`/`DATA_ORDINE_FORNITORE`, `NUM_UM`, campo magazzino, politica prezzi: **da verificare**.
- Il prompt di estrazione dei template contiene ancora **esempi reali** di fornitori/clienti (nomi e numeri di documento) e la numerazione ordini `anno-OF-numero`/`anno-OC-numero` (standard Target Cross, da verificare per ogni azienda): anonimizzare prima di distribuire (R20).
- Il parser XML di ORD-CLI-MA è generato da uno script del repository originale: riportare lì le modifiche a `pivaNostra`/`nomeNostro`.
- Chiavi di idempotenza dei template: usano la chiave **documento** (`ordcli-log-start-{fileCorrelationId}`); la guida ThinkAI 3.1 raccomanda per gli step che spostano file o scrivono nel gestionale un id **del tentativo** nella chiave (vedi skill `thinkai-novita-ottobre-2026`, `workforce-studio.md`): da valutare per i flussi che rimettono in ingresso lo stesso file.
- Nessun bump di versione del flusso di origine: i template sono **copie derivate**.

## 9. FATT-SLOT — Controllo fattibilità e slot spedizione (specifica v0.1)

Per ogni ordine cliente PDF l'agente calcola **in sola lettura** se è evadibile e **quando** (data prevista di
consegna), poi invia **una mail**. Archetipo A1 (front, M00→M09) → A8 (verifica) + P. Decisioni **confermate**:
ingresso PDF da cartella (M00); ERP Target Cross; slot = data prevista di consegna (non prenotazione capacità);
tempi da **cicli di lavorazione** + giorni di transito (transito ⚠️); `partenza = max(data disponibilità merce,
data ordine + lavorazione)`, `consegna = partenza + transito`, festivo → primo giorno lavorativo; depositi in
**lista ordinata per priorità**; nessuna scrittura ERP nella v1.

📐 **Proposta** (da validare): `disp = Σ(giacenza − impegnato)` per deposito in priorità; residuo coperto dagli
arrivi fornitore (cumulati per data); esiti riga `NEI_TEMPI` / `IN_RITARDO` / `NON_DETERMINABILE`; verdetto
`FATTIBILE` / `PARZIALE` / `NON FATTIBILE` / `DA REVISIONARE`. Senza data richiesta nel PDF: nessun confronto,
solo data prevista (`giorniConsegnaDefault` ⚠️). Niente `idempotencyKey` (nessuna scrittura); `lookup` è
deprecato → `articoli`/`documenti` con `filtro`/`filtroRaw` o `Query` SELECT.

Parametri nuovi del profilo: `modalitaLettura` (API|SQL), `depositiPriorita[]`, `giorniTransitoDefault`,
`giorniConsegnaDefault`, `calendarioLavorativo{giorniLavorativi,festivi}`, `unitaTempoCicli` (ore|giorni ⚠️),
`tolleranzaGiorni`; opzioni `soloLettura`, `emailEsito`, `allegaPdfOriginale`.

**Punti aperti bloccanti (O1–O8)**: dove stanno giacenza/impegnato/ordini fornitore (O1) e cicli/fasi con unità
(O2) → `01_scoperta_schema.sql` (solo `SELECT`/`WITH`, struttura e conteggi, nessun dato di riga; cerca per pattern
`%CICL%`, `%FASE%`, `%GIAC%`, `%IMPEG%`, `%FEST%`… tranne `ART_ANA`, `ORD_CLI_RIGHE`, `ORD_FOR_RIGHE` già verificate);
fonte dei giorni di transito (O3); calendario festivi (O4); articoli prodotti/acquistati/misti (O5); lettura via
API o SQL (O6, accordo col produttore ERP); destinatari mail (O7); lingua/formato date dei PDF (O8). Non scrivere
il DSL finale prima dell'esito della scoperta schema.
