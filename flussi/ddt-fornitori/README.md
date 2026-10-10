# DDT Fornitori 6 casi — versione parametrica V2.0

Flusso ThinkAI WorkForce per l'acquisizione dei DDT fornitore da cartella (OCR + AI), la
classificazione nei 6 flussi e la registrazione `DDT_FOR` su Target Cross. Deriva dalla V1.51
collaudata per il primo cliente: la logica è la stessa, ma tutti i valori legati all'azienda
stanno ora in **un solo step**, `CONFIGURAZIONE CLIENTE`, oppure in un profilo JSON.

| File | Cosa contiene |
|---|---|
| `DDT_Fornitori_6_casi_PARAMETRICO_V2.0.thinkaiagent.json` | Template con segnaposto `<...>`: **non si importa così com'è** |
| `profili/profilo-cliente.template.json` | Profilo d'esempio (valori fittizi) da copiare per ogni azienda |
| `strumenti/applica_profilo.py` | Template + profilo → flusso pronto da importare |
| `strumenti/wfjson.py` | Lettura e scrittura dell'export WorkForce, step annidati compresi |

## Come si configura una nuova azienda

```bash
cp profili/profilo-cliente.template.json profilo-acme.privato.json   # fuori dal repository
# compilare il profilo, poi:
python strumenti/applica_profilo.py DDT_Fornitori_6_casi_PARAMETRICO_V2.0.thinkaiagent.json \
       profilo-acme.privato.json DDT_Fornitori_ACME_V2.0.thinkaiagent.json
```

Lo script si ferma se resta un segnaposto non compilato, se una mappa per flusso non è JSON
valido o usa chiavi diverse da `"1"`..`"6"`/`"*"`, se la P.IVA non ha 11 cifre o se l'email
non è valida. I profili reali (`*.privato.json`) restano fuori dal repository.

## Parametri

### Profilo (valori letterali, non interpolabili a runtime)
| Chiave | Uso | Esempio |
|---|---|---|
| `cliente.nome` | Nome nel titolo e nei tag dell'agente | `Azienda Esempio` |
| `cliente.sigla` | Tabelle `dbo.THINKAI_<SIGLA>_DDT_LOG`, `_DDT_LOG_RIGHE`, `_ARTICOLI_PROFILO`; prefisso idempotenza in minuscolo | `ACME` |
| `erp.credenziale` | `credentialName` di tutti gli step Target Cross | `TCRESTAPI` |

### Step CONFIGURAZIONE CLIENTE (modificabili anche da Studio)
| Chiave | Default template | Significato |
|---|---|---|
| `workRoot` | `<WORK_ROOT>` | Cartella di ingresso dei PDF (sotto: processing, elaborati, review, error, profiles) |
| `flusso5Root` | vuoto | Cartella i cui PDF sono sempre flusso 5. Vuoto = spenta |
| `operatorEmail` | `workforce@think-ai.it` | Destinatario di esiti, eccezioni ed errori |
| `operatorEmailCc` | vuoto | Copie, separate da virgola |
| `ownName` | `<RAGIONE_SOCIALE_AZIENDA>` | Ragione sociale del **destinatario** dei DDT (usata nel prompt AI) |
| `ownShortName` | `<SIGLA_AZIENDA>` | Nome breve usato nel prompt e nelle email |
| `ownVat` | `<PIVA_AZIENDA>` | P.IVA del destinatario, esclusa dalla ricerca del fornitore |
| `causaliPerFlussoJson` | `{}` | Causale per flusso, vedi sotto |
| `seriePerFlussoJson` | `{}` | Serie fissa per flusso (`"*"` = tutti) |
| `depositiPerFlussoJson` | `{}` | `COD_DEP` per flusso (`"*"` = tutti) |
| `magazziniPerFlussoJson` | `{}` | Codice magazzino per flusso (`"*"` = tutti) |
| `campoMagazzino` | vuoto | Nome del campo di testata in cui inviare il magazzino (vedi ⚠️) |
| `codiciCausaleContoLavoroCliente` | vuoto | Codici causale **stampati dal mittente** che indicano conto lavoro cliente, separati da virgola |
| `prefissiArticoliJson` | `[]` | Prefissi dei codici articolo interni (`pesoKg`, `tolleranzaPerc`) |
| `tolleranzaEccedenzaC00Perc` | `0` | Tolleranza % di ripiego per i prefissi senza `tolleranzaPerc` |
| `tolleranzaPesoNettoPerc` | `2` | Riscontro peso netto/righe (solo avviso); 0 = spento |
| `lunghezzaMinimaPrefissoD` | `4` | Lettere minime per l'aggancio automatico del Metodo D |
| `istruzioniExtraEstrazione` | vuoto | Regole del prompt specifiche dell'azienda (testo libero) |
| `agentVersion` | `DDTFOR6-V2.0` | Versione scritta nel log |

### Causali, serie, depositi, magazzino
```json
"causaliPerFlussoJson":   {"5": {"codice": "600.009", "descrizione": "Conto lavorazione cliente"},
                           "6": {"codice": "600.013", "descrizione": "Reso da cliente"}},
"seriePerFlussoJson":     {},
"depositiPerFlussoJson":  {"6": "007"},
"magazziniPerFlussoJson": {}
```

| Flusso | Causale | Serie | Deposito / magazzino |
|---|---|---|---|
| 1, 2, 4 (con ordine/approntamento) | `CAUS_DOC_SUCC` della causale dell'ordine; se c'è una voce in `causaliPerFlussoJson` vince quella | `seriePerFlussoJson`, altrimenti `CAUS_DOC_SERIE` se univoca | Inviati solo se configurati, altrimenti li calcola Target Cross |
| 3 (senza ordine) | Nessuna: va sempre in revisione (regola invariata) | — | — |
| 5 (c/lavoro cliente) | Obbligatoria in `causaliPerFlussoJson["5"]`, altrimenti revisione | `seriePerFlussoJson`, altrimenti la calcola Target Cross | Come sopra |
| 6 (reso da cliente) | Obbligatoria in `causaliPerFlussoJson["6"]`, altrimenti revisione | `seriePerFlussoJson`, altrimenti `CAUS_DOC_SERIE` | Come sopra |

> ⚠️ **Magazzino — DA VERIFICARE.** Sul `DDT_FOR` di TcRestAPI è documentato solo `COD_DEP`
> (deposito). Il magazzino si invia solo se `campoMagazzino` contiene il nome del campo di testata
> confermato su Target Cross; con il campo vuoto non parte niente.

## Cosa è cambiato rispetto alla V1.51
- P.IVA, ragione sociale e sigla del destinatario non sono più cablate nel prompt AI e nel codice.
- Causali 5/6, il codice causale «16» e il deposito `007` del flusso 6 non sono più cablati: arrivano
  dalla configurazione. Novità: causale forzabile su 1/2/4, serie fissa per flusso, deposito e
  magazzino per flusso con la voce jolly `"*"`.
- Email operatore preimpostata a `workforce@think-ai.it`.
- Tabelle di log, credenziale ERP e prefisso delle chiavi di idempotenza si generano dalla sigla.
- `prefissiArticoliJson = []` significa davvero «nessun prefisso». Il ripiego su `C00` resta solo
  se la chiave manca, per compatibilità con i flussi V1.x.
- Il campo `deposito` nel log (`DETAIL_JSON`) riporta il `COD_DEP` effettivamente inviato
  (vuoto = calcolato da Target Cross). In V1.51 conteneva un `01` solo informativo.
- **Correzione di un bug della V1.51:** in «Costruisci body DDT_FOR» la funzione `escMail` era
  usata prima di essere definita. Con un avviso sull'anagrafica (più P.IVA, flag ruolo, posizioni
  dismesse) lo step falliva con `escMail is not a function` e il PDF finiva in errore tecnico.

## Passi manuali in Studio dopo l'import
1. Creare la credenziale TcRestAPI con lo stesso nome di `erp.credenziale`.
2. Eseguire il DDL delle tabelle `THINKAI_<SIGLA>_DDT_LOG`, `_DDT_LOG_RIGHE` (e, se usata,
   `_ARTICOLI_PROFILO`) e concedere INSERT/UPDATE alla DataConnection.
3. Configurare **a mano** la Gestione errori del ForEach sui PDF: continua sugli errori dell'item,
   con gli step di recupero esistenti. Il round-trip dal JSON non è garantito.
4. Controllare lo step CONFIGURAZIONE CLIENTE e la schedulazione (`*/30 */1 * * *`).
5. Rivedere gli step di codice prima di abilitare l'agente, come chiede l'avviso di import.

## Piano di collaudo
| # | Caso | Atteso |
|---|---|---|
| 1 | DDT con ordine (flusso 2) | Causale da `CAUS_DOC_SUCC`, nessun `COD_DEP` se non configurato |
| 2 | Stesso DDT con `seriePerFlussoJson = {"2":"<serie>"}` | `SERIE_DOC` = serie configurata |
| 3 | Conto lavoro cliente (flusso 5) | Causale `causaliPerFlussoJson["5"]` |
| 4 | Flusso 5 senza causale configurata | Revisione con motivo «Causale della bolla per il flusso 5 non configurata» |
| 5 | Reso da cliente (flusso 6) | Causale e deposito da configurazione |
| 6 | Bolla che riporta solo la P.IVA del destinatario | Esito errore «P.IVA destinatario usata come fornitore» |
| 7 | Fornitore trovato con una P.IVA diversa da quella principale | DDT creato, nota P.IVA in email, **nessun errore tecnico** (bug corretto) |
| 8 | `campoMagazzino` + `magazziniPerFlussoJson` valorizzati | Campo presente nel body (verificare l'accettazione di TcRestAPI) |
| 9 | Email | Esiti a `operatorEmail`, nessun `{chiave}` letterale |

Verifiche già eseguite **su dati sintetici**, non ancora su sistema reale: sintassi di tutti i 47
CodeJs; 37 test funzionali su normalizzazione, causale/serie e body. Il flusso del primo cliente
rigenerato dal template coincide con la V1.51, salvo il deposito informativo del log.

## Limiti noti e possibili evoluzioni
- Il prompt di estrazione contiene ancora esempi reali di fornitori (nomi e numeri di documento) e
  descrive la numerazione ordini `anno-OF-numero` / `anno-OC-numero`. È lo standard Target Cross,
  ma va verificato per ogni nuova azienda; le sigle si potrebbero rendere parametriche.
- I tipi causale `TIPO_CAUS_DOC = 11/12` nelle query sono costanti dello schema Target Cross.
- Le decisioni di business del primo cliente restano quelle validate in collaudo: flusso 3 sempre
  in revisione, regola approntamento allegato, tolleranze.
