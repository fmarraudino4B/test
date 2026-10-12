# Workforce Console 1.2.10: seguire gli agenti

Fonte: guida ottobre 2026, cap. 12. Pagina web con cui il cliente segue il lavoro degli agenti
Workforce: documenti arrivati, caricati nel gestionale, in attesa di verifica e perché. **Non
esegue i flussi**: legge il log scritto dagli agenti sul database del gestionale e, per l'unica
azione che tocca la piattaforma (**Rielabora**), chiama il Backend. Dalla 3.1 non è più legata a
un solo agente: un cliente con DDT fornitori, ordini clienti ed eventi da mail li segue tutti dallo
stesso indirizzo; **un agente nuovo = una riga di database**.

## Cosa cambia

| Novità | A cosa serve |
|---|---|
| Più agenti nella stessa Console | **Selettore agente** (compare quando gli agenti sono >1); filtri, riquadri e dettaglio sono per agente |
| Registro degli agenti | L'elenco del selettore viene dalla tabella `THINKAI_WF_AGENTI`: aggiungere = `INSERT`, togliere = `ATTIVO = 0` |
| Log uguale per tutti | Le tabelle `THINKAI_WF_*` sono le stesse su ogni DB; gli agenti si distinguono per codice. Niente tabelle nuove per ogni agente |
| Rielabora per agente | Ogni agente ha il suo id Backend nel registro: il documento torna in coda all'agente giusto |
| Vedi PDF dopo lo spostamento | Il PDF si apre anche se l'agente l'ha spostato in `elaborati\`, `review\`, `error\` o l'ha rinominato |

Gli agenti installati **prima della 3.1** che scrivono su tabelle di log dedicate restano dove sono,
**non vanno migrati**: la Console li legge e li mostra nel selettore accanto ai nuovi.

## Chi fa che cosa

| Passo | Chi | Quando |
|---|---|---|
| 1. Tabelle `THINKAI_WF_*` sul DB del gestionale | Chi installa | Una volta per database |
| 2. L'agente scrive il log | Chi costruisce l'agente nello Studio | Una volta per agente |
| 3. Registrazione dell'agente | Chi installa | Una volta per agente |
| 4. Id Backend per Rielabora | Chi installa | Dopo l'import dell'agente |
| 5. Verifica dalla Console | Chi installa, con il cliente | Al collaudo |

## 1. Tabelle sul database (una volta)

Sul **database del gestionale** (stessa connessione dati della chat dell'agente) esegui lo script
**`THINKAI-WF-LOG-SCHEMA.sql`**. Crea: `THINKAI_WF_AGENTI` (registro: un agente per riga, nome,
etichetta del documento, opzioni), `THINKAI_WF_LOG` (una riga per **tentativo** di elaborazione),
`THINKAI_WF_LOG_RIGHE` (righe del documento, facoltative), e le viste che la Console legge.
Lo script è **idempotente** (si rilancia negli aggiornamenti). L'utente SQL dell'agente ha bisogno
di **INSERT e UPDATE** su log e di **INSERT** sulle righe; alla Console basta un utente in **sola lettura**.

## 2. L'agente scrive il log

Ogni elaborazione scrive una riga **all'inizio** e la **chiude alla fine** con l'esito. Bastano 3
step della palette *Dati*, ciascuno preparato da un *Code JS*.

> **LOG_KEY è un tentativo**: ogni giro dell'agente sullo stesso documento è una riga nuova → va
> generata diversa a ogni tentativo (es. hash del percorso + ora).
> **CORRELATION_ID è il documento**: uguale fra i tentativi (per un file l'hash del percorso
> d'ingresso, per una mail la sua chiave). È la chiave che usa **Rielabora**, quindi le chiavi di
> idempotenza degli step che scrivono nel gestionale devono contenerla.

**Apertura** — Code JS + Insert SQL:

```js
// Testata del log: una riga per tentativo, stato iniziale IN_ELABORAZIONE.
stepData.logRows = [{
  LOG_KEY: String(stepData.logKey),
  AGENT_CODE: 'DDT_FORNITORI',                 // lo stesso codice del registro
  CORRELATION_ID: String(stepData.correlationId),
  AGENT_VERSION: 'DDT-FOR-V1.0',
  FILE_NAME: String(stepData.inputFileName),   // nome leggibile: file, oggetto della mail…
  FILE_SOURCE: String(stepData.sourceFilePath),// SOLO il percorso completo del file
  STATO: 'IN_ELABORAZIONE',
  DATA_INIZIO_UTC: DateTime.now()
}];
```

Insert SQL: tabella `dbo.THINKAI_WF_LOG`; chiave righe (array) `logRows`; chiave di idempotenza `ddtfor-log-{logKey}`.

**Chiusura** — sul ramo buono **e** su quelli di revisione ed errore: Code JS + Update SQL:

```js
// Esito del tentativo: la Console mostra stato, soggetto, documento e motivo.
stepData.logUpdateSet = {
  STATO: stepData.esito,                       // uno degli stati del §5
  PIVA: String(stepData.piva || ''),
  COD_CF: String(stepData.codCf || ''),
  RAG_SOC: String(stepData.ragSoc || ''),
  DOC_NUMERO: String(stepData.numeroDoc || ''),
  DOC_DATA: stepData.dataDocIso || null,       // 'YYYY-MM-DD'
  ERP_DOC_TIPO: 'DDT_FOR',
  ERP_DOC_ID: String(stepData.documentoCreatoId || ''),
  RIGHE_TOTALI: righe.length,
  RIGHE_RISOLTE: risolte,
  RIGHE_ANOMALE: righe.length - risolte,
  ESITO_MOTIVO: String(stepData.motivo || ''),
  DATA_FINE_UTC: DateTime.now()
};
```

Update SQL: tabella `dbo.THINKAI_WF_LOG`; chiave SET (oggetto) `logUpdateSet`; WHERE `LOG_KEY = {logKey}`
(senza apici); idempotenza `ddtfor-logclose-{logKey}`.
**Righe (facoltative)**: Insert SQL su `dbo.THINKAI_WF_LOG_RIGHE` con `LOG_KEY`, `RIGA_NUMERO`,
`CODICE_RAW`, `DESCRIZIONE`, `COD_ART`, `MATCH_METHOD`, `STATO` (RISOLTA, ANOMALIA, SALTATA…), `MOTIVO`.

> **Chiudere il log anche quando qualcosa va storto**: la chiusura va messa anche nel ramo di
> errore del ForEach, con stato `ERRORE_TECNICO`. Un tentativo che resta `IN_ELABORAZIONE` per ore
> vuol dire una run interrotta: nella Console si riconosce subito e il Correlation ID porta alla
> Timeline del Backend.

## 3. Gli stati e i riquadri

Stati liberi, ma i **riquadri** in alto (Creati, In revisione, Errori, Duplicati) e i colori riconoscono questi nomi:

| Stato | Riquadro | Quando |
|---|---|---|
| `IN_ELABORAZIONE` | — | All'apertura |
| `CREATO` | Creati | Documento caricato nel gestionale |
| `CREATO_PARZIALE` | Creati | Caricato, con righe da sistemare |
| `REVISIONE` | In revisione | Fermo per verifica dell'operatore |
| `DUPLICATO` | Duplicati | Già presente nel gestionale |
| `ERRORE_ERP` | Errori | Il gestionale ha rifiutato il documento |
| `ERRORE_TECNICO` | Errori | Errore imprevisto del flusso |

Valgono anche `ELABORATO` (Creati), `REVIEW` (In revisione), `ERRORE` (Errori). Uno stato con un
altro nome si filtra dal menu a tendina ma **non entra in nessun riquadro**.

## 4. Il PDF: FILE_SOURCE e cartelle di lavoro

**Vedi PDF** e **Rielabora** usano `FILE_SOURCE` per trovare il file: lì va **solo il percorso
completo** del file d'ingresso (`\\server\condivisione\Ingresso\doc.pdf`). Nome cartella, flusso e
ogni altra informazione vanno in `DETAIL_JSON`. Se l'agente sposta il file a fine lavoro, la Console
lo cerca nelle sottocartelle `processing\`, `elaborati\`, `review\`, `error\` della cartella
d'ingresso, di quella sopra e delle cartelle indicate in `cartelleFile` nel registro. **Mai
nell'intera condivisione.**

- **Se l'agente rinomina il file**: il nuovo nome deve contenere il `CORRELATION_ID`, es.
  `{correlationId}_{nome}.pdf` (è la «firma» con cui la Console riconosce il documento anche con
  più scansioni dello stesso nome, e dopo lo spostamento).
- **Ingresso su un'altra condivisione**: se l'agente legge da una condivisione e sposta in un'altra,
  aggiungi la cartella di lavoro a `cartelleFile`. Se il PDF non si trova, il messaggio elenca le
  cartelle in cui ha cercato.

## 5. Registrare l'agente

Compare nel selettore con `ATTIVO = 1`; lo script si può rilanciare (aggiorna la riga se c'è già).

```sql
DECLARE @AgentCode   varchar(40)   = 'DDT_FORNITORI';       -- lo stesso di AGENT_CODE nel log
DECLARE @Descrizione nvarchar(250) = N'DDT fornitori';      -- il nome nel selettore
DECLARE @DocLabel    nvarchar(40)  = N'DDT';                -- «DDT 123», «N. DDT» nelle colonne
DECLARE @TipoFlusso  varchar(40)   = 'DDT_FORNITORI';
DECLARE @ReprocessAgentId int      = 0;                     -- id Backend, vedi §6

DECLARE @ConfigJson nvarchar(max) = N'{
  "stati": ["IN_ELABORAZIONE","CREATO","CREATO_PARZIALE","REVISIONE","DUPLICATO","ERRORE_ERP","ERRORE_TECNICO"],
  "righe": true,
  "reprocessAgentId": ' + CAST(@ReprocessAgentId AS nvarchar(12)) + N',
  "cartelleFile": []
}';

MERGE dbo.THINKAI_WF_AGENTI AS t
USING (SELECT @AgentCode AS AGENT_CODE) AS s ON t.AGENT_CODE = s.AGENT_CODE
WHEN MATCHED THEN UPDATE SET
    DESCRIZIONE = @Descrizione, TIPO_FLUSSO = @TipoFlusso, DOC_LABEL = @DocLabel,
    ATTIVO = 1, CONFIG_JSON = @ConfigJson, UPDATED_AT_UTC = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT (AGENT_CODE, DESCRIZIONE, TIPO_FLUSSO, DOC_LABEL, ATTIVO, CONFIG_JSON)
    VALUES (@AgentCode, @Descrizione, @TipoFlusso, @DocLabel, 1, @ConfigJson);
```

| Chiave `CONFIG_JSON` | Effetto |
|---|---|
| `stati` | Voci del filtro Stato, nell'ordine scritto (senza: elenco standard) |
| `righe` | `true` = il dettaglio mostra la tabella delle righe |
| `reprocessAgentId` | Id dell'agente sul Backend: mostra **Rielabora**. `0` o assente = nascosto |
| `cartelleFile` | Facoltativo: cartelle di lavoro dove l'agente sposta i file, se non sono vicine alla cartella d'ingresso |

*(Nel testo della guida il commento sull'id rimanda a «10.8»: il riferimento corretto è il §12.8,
cioè Rielabora.)*

## 6. Rielabora

Dopo aver importato l'agente nello Studio, il suo **id** è nell'elenco agenti: rilancia lo script
del §5 con `@ReprocessAgentId` valorizzato e ricarica la Console. Ogni agente ha il suo id: con lo
stesso id su due agenti, Rielabora rimetterebbe il documento a quello sbagliato.
Si usa **dopo aver corretto la causa**, di solito nel gestionale (anagrafica mancante, causale sbagliata):
1. il Backend toglie dal **journal** le operazioni di quel documento e, per gli agenti su mail,
   rimette la mail in coda;
2. per gli agenti su file la Console riporta il PDF nella cartella d'ingresso con il **nome
   originale** (se non lo trova, lo dice e indica dove riportarlo a mano);
3. i controlli nel gestionale restano attivi: un documento già caricato **non si duplica**.
L'azione chiede conferma ed è registrata nel log del Backend con utente, agente e documento.

## 7. Più agenti nella stessa Console

- Il selettore compare da solo se gli agenti sono >1; la scelta resta in un cookie.
- Link diretto a un agente: `https://console.cliente.it/?agent=DDT_FORNITORI`.
- Togliere un agente dal selettore: `UPDATE dbo.THINKAI_WF_AGENTI SET ATTIVO = 0 WHERE AGENT_CODE = '…'` (lo storico resta nel log).
- Login con le credenziali del Backend; ruoli ammessi **Admin** e **SystemAdmin**.

| Chiave `appsettings.json` | Uso |
|---|---|
| `ConnectionStrings:GestionaleDb` | DB del gestionale con le tabelle di log; basta utente sola lettura |
| `Backend:BaseUrl` | Backend ThinkAI: login e Rielabora |
| `Console:Agente` | `Wf` per gli agenti del registro; valore dell'agente per le installazioni precedenti |
| `Wf:AgentCode` | Agente mostrato al primo accesso |
| `Console:AllowedRoles` | Ruoli ammessi; default Admin e SystemAdmin |
| `Console:ReprocessAgentId`, `Console:CartelleFile` | Solo per l'agente storico: per gli altri valgono `reprocessAgentId` e `cartelleFile` del registro |

> **L'account della Console deve leggere le cartelle**: Vedi PDF e Rielabora leggono e spostano
> file con l'account del **pool IIS della Console**: deve poter accedere a tutte le condivisioni
> dell'agente, ingresso e cartelle di lavoro.

## 8. Verifica al collaudo

| Controllo | Fatto quando |
|---|---|
| Selettore | L'agente compare col nome di `DESCRIZIONE` |
| Apertura | Un documento di prova appare subito come **IN ELABORAZIONE** |
| Chiusura | A fine giro passa allo stato finale, nel riquadro giusto |
| Dettaglio | Soggetto, numero, documento ERP e motivo sono valorizzati |
| Vedi PDF | Il PDF si apre anche dopo lo spostamento in `elaborati\` o `review\` |
| Rielabora | Su un documento in revisione risponde «Documento sbloccato» e il file torna in ingresso |

| Sintomo | Causa probabile |
|---|---|
| L'agente non compare nel selettore | `ATTIVO = 0`, oppure codice del registro diverso da quello scritto nel log |
| Dashboard vuota ma l'agente lavora | `AGENT_CODE` nel Code JS diverso dal registro, oppure la Console punta a un altro database |
| Errori a 0 con documenti falliti | Stato con un nome che i riquadri non riconoscono (§3) |
| Manca il bottone Rielabora | `reprocessAgentId` assente o `0` nel registro |
| «PDF non trovato» | Il messaggio elenca dove ha cercato: aggiungere la cartella a `cartelleFile`, controllare che il nome rinominato contenga il `CORRELATION_ID` e che l'account della Console legga la condivisione |
| Documenti fermi su IN ELABORAZIONE | Run interrotta: cercare il Correlation ID nella Timeline del Backend |
