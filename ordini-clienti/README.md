# Ordini Clienti – template multi-azienda (base V1.34)

Flusso ThinkAI WorkForce per gli ordini cliente da cartella condivisa (XML SdDataSlice, PDF, PDF + Excel,
programmazioni di consegna) verso Target Cross (TcRestAPI, risorsa `ORD_CLI`), reso **parametrico**:
tutti i valori dell'azienda stanno nello step **CONFIGURAZIONE AZIENDA - parametri** (step 1). Uno step
**Valida parametri azienda** (step 2) ferma la run con un messaggio esplicito se manca qualcosa,
prima di toccare file o gestionale.

```
template/Ordini_Clienti_-_Multi-azienda_-_V1.34.thinkaiagent.json   template da importare/compilare
profili/esempio.profilo.json                                         profilo di esempio (valori fittizi)
tools/applica_profilo.py                                             template + profilo -> flusso pronto
```

## Due modi per configurare una nuova azienda

**A. Da profilo (consigliato).** Copia `profili/esempio.profilo.json` in `profili/<azienda>.privato.json`
(ignorato da git), compilalo e lancia:

```
python tools/applica_profilo.py template/Ordini_Clienti_-_Multi-azienda_-_V1.34.thinkaiagent.json \
       profili/<azienda>.privato.json out/Ordini_Clienti_<azienda>.thinkaiagent.json
```

Lo script compila lo step di configurazione, rinomina l'agente, imposta credenziale Target Cross e
prefisso dei gruppi di idempotenza; esce con errore su chiavi sconosciute o segnaposto `<...>` rimasti.

**B. A mano in Studio.** Importa il template e compila lo step 1. Credenziale (`TCRESTAPI`) e gruppi di
idempotenza (`ordcli-create`, `ordcli-chiudi`) vanno cambiati negli step relativi, se diversi.

## Parametri (step 1)

| Parametro | Default template | Significato |
|---|---|---|
| `ragioneSocialeAzienda` | `<RAGIONE_SOCIALE_AZIENDA>` | Azienda che **riceve** gli ordini. Usata nel prompt AI, nei messaggi, e per non agganciarla mai come cliente nella ricerca per ragione sociale. Forma breve come compare sui documenti. |
| `pivaAzienda` | `<PIVA_AZIENDA>` | P.IVA dell'azienda (il prefisso `IT` viene tolto). Esclusa sempre come P.IVA cliente. |
| `workRoot` | `<WORK_ROOT>` | Radice di lavoro: contiene le cartelle d'ingresso e `processing/ elaborati/ review/ error/`. |
| `operatorEmail` | `workforce@think-ai.it` | Destinatario di esiti e avvisi (un indirizzo). |
| `operatorEmailCc` | `workforce@think-ai.it` | Copia conoscenza (un indirizzo). Vuoto = uguale a `operatorEmail`. |
| `prefissoOggettoMail` | `[Ordini Clienti]` | Prefisso dell'oggetto di tutte le mail. |
| `agentCode` / `agentVersion` | `ORD_CLI` / `ORDCLI-V1.34` | Codice registrato in `dbo.THINKAI_WF_AGENTI` (attivo) e versione nel log. |
| `cartelleJson` | `Ordine_Diretto`, `Ordine_Aperto` | Cartelle d'ingresso; `chiusura: true` = i precedenti con lo stesso numero si chiudono. |
| `depositiJson` | `[]` | Tabella **deposito → reparto / causale / serie / campi di testata**, vedi sotto. |
| `causaleDefault` / `depositoDefault` | vuoti | Ripiego quando il deposito dell'articolo non è in tabella o manca. Vuoti = revisione (comportamento V1.34). |
| `serieDocRiserva` | vuoto | Ultima riserva per `SERIE_DOC`. |
| `campiTestataJson` | `{}` | Campi di testata aggiuntivi per Target Cross (es. **magazzino**), vedi sotto. |
| `likeSuPivaEstera` | `true` | Ricerca LIKE sulle sole cifre per le P.IVA estere. |
| `classeDocDms` | vuoto | Classe documentale DMS; vuota = descrittore non scritto. |
| `pivaClientiMatricolaExcel` | vuoto | P.IVA (separate da virgola) dei clienti PDF + Excel: MATRICOLA dal PDF, CAUSALE di riga dall'Excel. Vuoto = regola spenta. |
| `programmazioniJson` | `[]` | Programmazioni di consegna lette senza AI. |

### Causali, depositi, serie, magazzino

```json
[
  { "deposito": "01", "nome": "Produzione", "causale": "OC01" },
  { "deposito": "02", "nome": "Ricambi",    "causale": "OC02", "serie": "R",
    "campiTestata": { "<CAMPO_TC>": "<valore>" } }
]
```

- **Deposito / causale**: si leggono da `ART_ANA.COD_DEP` del primo articolo risolto e si traducono con
  la tabella. Righe su depositi diversi → revisione (invariato).
- **Serie** (`SERIE_DOC`), in quest'ordine: `serie` della voce → `CAUS_DOC_SERIE` se univoca → ultimo
  `ORD_CLI` con la stessa causale → `serieDocRiserva` → nessuna (la sceglie Target Cross).
- **Magazzino e altri campi di testata**: `campiTestataJson` (tutte le righe) e `campiTestata` della voce
  (prevale) vengono aggiunti al body subito dopo `COD_DEP`. I campi base (`COD_CAUS_DOC`, `SERIE_DOC`,
  `COD_DEP`, `COD_CF`, `NUM_ORDINE_CLIENTE`, `DATA_ORDINE_CLIENTE`, `RIGHE`) non si sovrascrivono.
  ⚠️ DA VERIFICARE: il nome del campo magazzino su TcRestAPI `ORD_CLI` va confermato su Target Cross.
- Il reparto, la causale, il deposito, la serie e l'eventuale uso dei valori predefiniti compaiono
  nella mail di esito.

## Differenze rispetto alla V1.34 TR

- Valori dell'azienda tolti da prompt AI, parser XML, messaggi, ricerca per ragione sociale e commenti;
  `pivaTr` → `pivaAzienda`, `pivaDaikin` → `pivaClientiMatricolaExcel` (elenco).
- Nuovi: `ragioneSocialeAzienda`, `prefissoOggettoMail`, `causaleDefault`, `depositoDefault`,
  `campiTestataJson`, `serie` / `campiTestata` per deposito, step **Valida parametri azienda**.
- Fix R5: la pulizia di inizio file azzera anche deposito, causale, reparto e serie (prima un file
  fermato prima della determinazione del reparto poteva mostrare in mail quello del file precedente).
- Un profilo con i valori V1.34 genera un flusso identico all'originale, salvo le voci sopra.

## Passi manuali in Studio dopo l'import

1. Creare la credenziale Target Cross con lo stesso nome usato nel flusso (default `TCRESTAPI`).
2. Configurare la **Gestione errori** dei due ForEach (cartelle e file), non garantita dall'import.
3. Eseguire `THINKAI-WF-LOG-SCHEMA.sql` e `SETUP-LOG-ORDINI-CLIENTI.sql` e registrare `agentCode`
   in `THINKAI_WF_AGENTI`.
4. Ricollegare l'eventuale Chat (il collegamento non viene esportato).

## Collaudo

Testato su dati sintetici: compilazione di tutti i 44 step CodeJs con Node, 20 casi sugli step
modificati (validazione, deposito/causale con e senza valori predefiniti, serie, regola
matricola/Excel, ordine e fusione dei campi di testata, pulizia), round-trip del profilo V1.34.
**Non ancora verificato su sistema reale**: prima esecuzione su un'azienda nuova con un ordine di prova
per cartella, controllando body inviato a Target Cross, mail e log.

Note: il parser XML è generato da `tools/parse-ordine-toyota-xml.mjs` (repository originale): riportare
lì le modifiche `pivaNostra` / `nomeNostro`. Il prompt AI contiene esempi di ordini reali (nomi dei
clienti di altri progetti), utili come casi guida; valutare se anonimizzarli prima di distribuirlo.
