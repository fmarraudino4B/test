# Server MCP FileSystem 2.1.0.10 («ThinkAI Document»)

Fonte: guida ottobre 2026, cap. 9 (+ §15.1). Servizio **Windows** vicino alle cartelle del
cliente, in **sola lettura** (cerca, legge, scarica; non modifica). Risponde al Backend col
protocollo **MCP**. Novità: trasporto **HTTP nativo** (niente più ponte TCP/Node), vero **RAG**
(estrazione testo, OCR, ricerca per significato e per parole), **due processi** (servitore +
indicizzatore), sincronizzazione che **non perde l'indice** se la rete ha problemi.

```
MAUI/ChatWeb → Backend → MCP servitore (HTTP /mcp, X-Api-Key) → index.db → MCP indicizzatore (figlio) → \\server\documenti
```

## 1. Trasporto Streamable HTTP

Ascolta su `http://localhost:7050/mcp` (porta e percorso configurabili), ospitato come servizio
Windows. Il Backend usa un client HTTP Streamable HTTP con ripiego automatico su SSE.

| | Streamable HTTP (consigliato) | STDIO (legacy) | Ponte TCP Node (deprecato) |
|---|---|---|---|
| Come parla | HTTP su `/mcp`, risposte in streaming | Il Backend avvia l'exe come processo figlio | Backend → script Node → STDIO |
| Processi | Servitore + indicizzatore separati | Uno solo | Come STDIO |
| Salute | `GET /health` | No | No |
| Sicurezza | Host consentiti, API key, HTTPS obbligatorio in rete | Solo locale | — |
| Quando | Sempre nelle installazioni nuove | Solo compatibilità | **Mai: va rimosso** |

**Sicurezza del trasporto**
- **Host consentiti**: ogni richiesta (anche `/health`) deve avere un nome host in `AllowedHosts`,
  altrimenti **400 «Host non consentito.»**
- **API key**: con `EnableAuthentication: true` le chiamate a `/mcp` portano `X-Api-Key` uguale a
  `McpTransport:ApiKey`, altrimenti **401 «API key MCP non valida.»** Il Backend la manda da
  `McpServer:ApiKey`. `/health` non chiede la chiave.
- **Server raggiungibile da altre macchine** (`Host` ≠ localhost, anche `0.0.0.0`): il servizio
  **si rifiuta di partire** senza `EnableAuthentication: true` **e** `Scheme: "https"`.
- **Filtro per utente Windows** (`EnableWindowsImpersonation: true`): serve l'autenticazione del
  trasporto, anche in locale.

## 2. Il sistema RAG, passo per passo

RAG = prima **recupera** i pezzi di documento pertinenti, poi **genera** la risposta citandoli;
il server MCP fa la parte di recupero.

`Scansione (inventario+sync ogni 30 min, watcher) → Estrazione (testo nativo; OCR per le scansioni) → Blocchi (2.500 car., sovrapposti 250) → Embedding (un vettore per blocco) → Indici (vettoriale sqlite-vec + parole FTS5) → Ricerca ibrida (nomi + parole + significato)`

**Estrazione**

| Tipo di file | Lettura |
|---|---|
| PDF con testo | Nativa, parole ricomposte in righe |
| PDF scansionati e immagini (tif, jpg, png, bmp) | **OCR Tesseract** ita+eng a 300 dpi, fino a 200 pagine/doc, raddrizzamento pagine ruotate |
| Word, Excel, PowerPoint (OpenXML) | Nativa |
| .doc, .rtf, .xls | Con licenze **Aspose**; .ppt con lettura euristica |
| OpenDocument (.odt .ods .odp) | Nativa |
| Posta .eml, .msg | Intestazioni e corpo; degli allegati solo i nomi |
| Fatture elettroniche (.xml FatturaPA), .p7m | Campi della fattura; busta firmata aperta |
| .zip | Elenco voci e testo di max 20 voci leggibili (senza OCR) |
| Disegni .dwg, .dxf | Cartiglio, attributi, layer, annotazioni |
| Testo (.txt .csv .json .xml .md…) | Diretta con riconoscimento della codifica |

**«Salita di lettura»**: Tesseract dà a ogni pagina una **confidenza**; sotto **0,65** è «dubbia».
Se il cliente lo decide, le pagine dubbie possono essere **rilette da un modello visivo in cloud**
(tetti di spesa per documento e per giorno); il risultato si scarta se vuoto, rifiuto o con meno
della metà dei caratteri letti da Tesseract.

> **La rilettura in cloud è una decisione del cliente.** Con `OcrRilettura:Abilitata: true` le
> immagini delle pagine scansionate **escono dalla rete del cliente** verso il fornitore del
> modello (Anthropic con `claude-haiku-5-5`, OpenAI con `gpt-5.4-nano`). Serve il **consenso
> esplicito** del cliente. Con la rilettura spenta resta la sola lettura locale con Tesseract. Il
> pacchetto la porta **spenta**: si accende nel file locale del cliente.

**Rilettura con Claude Haiku 5.5** (dall'8 ottobre 2026 il pacchetto porta `claude-haiku-5-5` con
`Sforzo: none` al posto di `gpt-5.4-nano`; misura del 7 ottobre sulle stesse immagini):

| | Haiku 5.5, Sforzo none | gpt-5.4-nano, medium |
|---|---|---|
| Banco 6 documenti, campi giusti | 52/52 | 51/52 |
| 47 pagine native, codici giusti (617) | 97,4% | 75,0% |
| 55 scansioni vere difficili, trascritte | 55 | 31 (23 rifiuti) |
| Secondi a pagina | 3–4,5 | 10–17 |
| Dollari a pagina | 0,0008–0,0011 | 0,0023–0,0040 |

Il nome del modello decide il fornitore: `claude-…` → API Anthropic, altri → OpenAI. Per Haiku:
1. **Configuration Manager** → Configurazioni → config cliente del server documenti
   (`ClientId <Cliente>_Document`): aggiungi **`ClaudeApiKey`** in `FileSystemServer`, accanto a
   `OpenAIApiKey` (che resta per gli embedding). È la chiave API Anthropic (può essere la stessa del Backend).
2. **File locale `appsettings.json`**: accendi la rilettura e indica modello e sforzo.

```json
{ "FileSystemServer": { "OcrRilettura": { "Abilitata": true, "Modello": "claude-haiku-5-5", "Sforzo": "none" } } }
```

Per OpenAI: `"Modello": "gpt-5.4-nano", "Sforzo": "medium"` (basta `OpenAIApiKey`, la stessa degli
embedding; con nano **non** abbassare a none/low: sul manoscritto legge peggio).
Nel log dopo il riavvio: *«Rilettura OCR ATTIVA: modello claude-haiku-5-5 (Anthropic)»*; se manca
la chiave: *«Rilettura OCR richiesta ma NON attiva: manca ClaudeApiKey»* (le pagine restano come
le ha lette Tesseract).

> **Un'installazione con il file vecchio resta su gpt-5.4-nano**: il modello si legge dal file
> locale; se esiste già una sezione `OcrRilettura` con `gpt-5.4-nano`, l'aggiornamento non la
> cambia. Per passare a Haiku cambia Modello e Sforzo nel file locale e aggiungi `ClaudeApiKey`
> nella configurazione cliente. Con `RileggiIncertiGiaIndicizzati` acceso, i documenti incerti già
> indicizzati tornano in coda col modello nuovo.

**Blocchi, embedding, indici**
- **Blocchi** da 2.500 car. (documento fino a `EmbeddingMaxCharsPerFile`), sovrapposti 250, tagliati su punto/a capo.
- **Embedding**: un vettore per blocco; il documento vale quanto il suo blocco più simile alla domanda.
- **Indice vettoriale** in `index.db`; sopra 100.000 blocchi si usa un indice **ANN (sqlite-vec)**; il
  servitore tiene i vettori **in memoria**, compressi a un byte per dimensione (389.000 blocchi ≈ 420 MB;
  ricerche da 4 minuti a 1,5 s sul primo cliente grande).
- **Indice per parole (FTS5)**: parole esatte, ignora gli accenti e, per i codici, prova gli scambi
  tipici dell'OCR (O/0, S/5, I/1, B/8, Z/2).

| `EmbeddingProvider` | Dove gira | Modello e dimensione | Note |
|---|---|---|---|
| `openai` | OpenAI | `text-embedding-3-large`, 1024 | Predefinito |
| `gemini` | Google AI Studio (endpoint globale) | `gemini-embedding-001` | Non vincolato all'UE |
| `gemini-vertex` | Google Vertex AI, `europe-west1` | `gemini-embedding-001` o `text-embedding-005` | Dati in UE; service account JSON |

> **Dimensione dei vettori**: con Gemini/Vertex il server non riduce la dimensione:
> `EmbeddingDimension` deve essere la **nativa** del modello (3072 per `gemini-embedding-001`),
> altrimenti la ricerca in memoria e l'ANN restano vuoti. Cambiando **modello** i vettori si
> rifanno da soli riusando il testo OCR già letto; cambiando **solo la dimensione** con lo stesso
> modello **no**. **Non cancellare `index.db`**: dentro c'è anche il testo OCR, che andrebbe rifatto.

**Ricerca ibrida**: tre ricerche in parallelo (nome file, parole FTS5, significato/vettori) fuse
con **Reciprocal Rank Fusion** (peso delle parole cresce se il termine è raro; il nome vota solo
se il filtro è selettivo).

| `matchSource` | Origine |
|---|---|
| `filename` | Nome del file |
| `lessicale` | Indice per parole (FTS5) |
| `embedding-memoria`, `embedding-ann`, `embedding` | Vettori (memoria / ANN / confronto completo) |
| `content-index` | Indice invertito (modalità `inverted`, senza RAG) |
| `scan`, `scan-budget` | Scansione cartelle mentre l'indice non è pronto |

Le fonti si combinano (`filename+embedding-memoria+lessicale`). Finché l'indice non ha elaborato
tutti i file i risultati portano **`isPartial: true`** e la copertura raggiunta.

## 3. Indicizzatore e servitore

Due processi: il **servitore** risponde e apre `index.db` in sola lettura; l'**indicizzatore**
(processo figlio) scansiona, estrae, fa OCR e calcola i vettori (OCR pesante non rallenta le risposte).
- Tetto di memoria dell'indicizzatore: un quarto della RAM, fra 256 MB e 8 GB; priorità sotto il
  normale; riavvio con attese crescenti (10 s, 30 s, 2 min, 10 min).
- **Lucchetto** `indicizzatore.lock` accanto a `index.db`: un solo indicizzatore per indice.
- Si accorge dei cambiamenti entro un minuto, ricarica solo ciò che è cambiato.
- `EmbeddingExtractors` (0 = automatico): ~1,5 per core fisico, 400–500 MB di RAM ciascuno.

## 4. Sincronizzazione e cartelle di rete

Primo avvio: **scansione completa** + inventario per estensione nel log. Poi sync ogni
`IndexRefreshIntervalMinutes` (30) e **watcher**. Fino a 20 file nuovi per giro letti subito; oltre
passano agli estrattori in parallelo.

**Dal 4 ottobre 2026** una cartella che non risponde **non è più trattata come cancellata**
(prima una caduta di rete durante la sync poteva togliere dall'indice decine di migliaia di file
col loro testo OCR).

| Situazione | Comportamento |
|---|---|
| Errore di rete durante la sync | Nessun file esce dall'indice; si riprova al giro dopo |
| Percorsi non leggibili (permessi, file bloccati) | I file restano nell'indice |
| Tanti file spariti insieme (>100 o >5%) | Escono solo quelli già mancanti al giro prima; gli altri al giro dopo se mancano ancora |
| Cancellazione vista dal watcher con la cartella muta | Ignorata |
| Primo avvio con cartella muta | Aspetta fino a 5 minuti; i vettori dei suoi file restano |
| DB occupato durante l'aggiornamento ANN | Si riprova al giro dopo, senza ricostruire |

Il testo estratto di un file resta in `index.db` per **30 giorni** (se il file torna uguale l'OCR
non si rifà; per questo `index.db` non cala subito dopo aver tolto cartelle).
**Avvio ritardato**: imposta il servizio `start= delayed-auto`; se all'avvio una condivisione non
risponde quella radice viene scartata fino al riavvio del servizio. Se resta irraggiungibile a
lungo, riavvia il servizio quando torna.

## 5. Configurazione

Ordine di lettura: `appsettings.json`, `appsettings.{Ambiente}.json`, variabili d'ambiente, riga
di comando, e per ultimo il **profilo remoto** del Configuration Manager, che **sovrascrive tutto**.

- **Profilo remoto** (ClientId `ThinkAI_Document` o `<Cliente>_Document`): le **chiavi API**
  (`OpenAIApiKey`, `GeminiApiKey`, `VertexProjectId`, service account Vertex, `ClaudeApiKey`).
  Mai nel file locale.
- **File locale**: trasporto, cartelle, percorso indice, impostazioni non segrete. Nel profilo
  remoto **non** vanno `RemoteConfiguration`, `McpTransport`, `AllowedDirectories`, `IndexDbPath`.
- **In produzione** `RemoteConfiguration:Endpoint` (HTTPS) e `ClientId` sono obbligatori (altrimenti
  il servizio non parte). Con indice contenuti attivo e chiave provider mancante il servizio non parte.
- **Primo avvio su macchina nuova**: il servizio si ferma con **codice 2 (EnrollmentPending)** e
  scrive l'impronta in `logs\mcp-bootstrap.log`; un amministratore approva nel Configuration
  Manager, pagina **Accessi configurazione**; poi riavvia. Non si ripete dopo un aggiornamento.

| Chiave | Serve a | Valore tipico |
|---|---|---|
| `McpTransport:Type/Host/Port/Path` | Trasporto e indirizzo | `http` / `localhost` / `7050` / `/mcp` |
| `McpTransport:AllowedHosts` | Host accettati | `localhost`, `127.0.0.1`, `[::1]` |
| `McpTransport:EnableAuthentication` / `ApiKey` | Chiave condivisa col Backend | `true` / chiave lunga |
| `FileSystemServer:AllowedDirectories` | Cartelle consentite: **percorsi UNC** per un servizio | `\\fileserver\documenti` |
| `ReadOnlyMode` | Sola lettura | `true` |
| `EnableFileIndex` / `IndexDbPath` | Indice e percorso (cartella scrivibile dall'account del servizio) | `true` / `D:\ThinkAI\McpIndex\index.db` |
| `IndexRefreshIntervalMinutes` | Intervallo sync | `30` |
| `MaxIndexedFiles` | Tetto; oltre escono i meno recenti | `750000` |
| `EnableContentIndex` / `ContentIndexMode` | Indice contenuti; **`embedding` per il RAG** (`inverted` = solo parole) | `true` / `embedding` |
| `EmbeddingProvider` / `OpenAIEmbeddingModel` / `EmbeddingDimension` | Provider e modello vettori | `openai` / `text-embedding-3-large` / `1024` |
| `EmbeddingExtractors` | Estrattori in parallelo (0 = auto) | `6` |
| `EmbeddingMaxCharsPerFile` | Caratteri letti per file | `1000000` |
| `OcrRilettura:Abilitata` | Rilettura pagine dubbie in cloud | Decisione del cliente |
| `OcrRilettura:Modello` / `Sforzo` | Modello e sforzo; `claude-` richiede `ClaudeApiKey` | `claude-haiku-5-5` / `none` |
| `OcrRilettura:MaxPagineRiletteAlGiorno` / `RileggiPagineConIdentificatori` | Tetto giornaliero (0 = nessuno); rilegge anche pagine con codici letti con alta confidenza | `5000` / `false` |
| `VectorInMemoryMaxMB` | Tetto memoria vettori; oltre, all'avvio la ricerca torna lenta. 1024 ≈ 950.000 blocchi | `1024` |
| `EnableWindowsImpersonation` / `ImpersonationMode` | Risultati filtrati sui permessi dell'utente | `false` / `acl_check` |

### Esempio 1 — stesso server del Backend, cartelle di rete, senza dominio (il più comune)

```json
{
  "RemoteConfiguration": { "Endpoint": "https://thinkaiconfig.runasp.net/api/getsettings", "ClientId": "<Cliente>_Document" },
  "McpTransport": { "Type": "http", "Scheme": "http", "Host": "localhost", "Port": 7050, "Path": "/mcp",
    "AllowedHosts": [ "localhost", "127.0.0.1", "[::1]" ],
    "EnableAuthentication": true, "ApiKey": "<CHIAVE-API-MCP>", "Stateless": true },
  "FileSystemServer": {
    "AllowedDirectories": [ "\\\\fileserver\\documenti" ], "ReadOnlyMode": true,
    "EnableFileIndex": true, "IndexDbPath": "D:\\ThinkAI\\McpIndex\\index.db",
    "IndexRefreshIntervalMinutes": 30, "MaxIndexedFiles": 750000,
    "EnableContentIndex": true, "ContentIndexMode": "embedding",
    "EmbeddingProvider": "openai", "OpenAIEmbeddingModel": "text-embedding-3-large", "EmbeddingDimension": 1024,
    "EmbeddingExtractors": 6, "EmbeddingMaxCharsPerFile": 1000000,
    "OcrRilettura": { "Abilitata": false, "Modello": "claude-haiku-5-5", "Sforzo": "none" },
    "EnableWindowsImpersonation": false } }
```
Servizio MCP con un utente locale che ha accesso alla condivisione; chiave OpenAI dal profilo remoto.

### Esempio 2 — dominio, permessi dell'account del servizio

Cambiano solo cartelle e account: `"AllowedDirectories": ["\\\\fileserver.azienda.local\\documenti"]`,
`"IndexDbPath": "E:\\ThinkAI\\McpIndex\\index.db"`. Ogni utente ThinkAI vede ciò che vede quell'account.

```powershell
# PowerShell amministratore — oppure Scripts\Imposta-AccountServizio.ps1 (non mette la password sulla riga)
sc.exe config ThinkAIFileSystemMcp obj= "AZIENDA\svc_thinkai_mcp" password= "<PASSWORD>"
Restart-Service ThinkAIFileSystemMcp
```

### Esempio 3 — dominio, permessi del singolo utente

Il Backend passa l'identità Windows dell'utente e il server filtra i risultati sui permessi dei
file (`acl_check`); serve l'autenticazione del trasporto.
- MCP: `"EnableWindowsImpersonation": true`, `"ImpersonationMode": "acl_check"` (con
  `EnableAuthentication: true` e `ApiKey` in `McpTransport`).
- Backend: `"McpServer": { "DefaultServerUrl": "http://localhost:7050/mcp", "ApiKey": "<CHIAVE-API-MCP>", "PropagateWindowsIdentity": true, "WindowsAuthMode": "header" }`.

> **Backend e MCP su macchine diverse**: parte **solo con HTTPS e autenticazione** (`Scheme: https`,
> `EnableAuthentication: true`, certificato per il server web, `AllowedHosts` col nome usato dal
> Backend). Con `Scheme: http` il servizio si rifiuta di partire. Concordalo con l'assistenza; dove
> si può, MCP e Backend sulla stessa macchina.

### Configurazione del Backend (sezione `McpServer`, di norma dal profilo remoto)

| Chiave | Significato | Tipico |
|---|---|---|
| `DefaultServerUrl` | Indirizzo MCP con percorso | `http://localhost:7050/mcp` |
| `ApiKey` | Stessa di `McpTransport:ApiKey` (inviata come `X-Api-Key`) | chiave lunga |
| `DefaultSearchPath` | Restringe a una cartella; **vuoto = tutte le cartelle del server MCP** (consigliato) | `""` |
| `SearchMode` | `filename`; `auto`, `hybrid`, `content` = nomi e contenuto | `auto` |
| `SearchTimeoutMs` / `ConnectionTimeoutMs` | Tempo massimo ricerca / connessione | `120000` / `10000` |
| `PropagateWindowsIdentity` / `WindowsAuthMode` | Identità utente verso l'MCP | `false` / `header` |

Con `"DefaultServerType": "filesystem"`. All'avvio il Backend scrive nel log se l'MCP è
raggiungibile e quante cartelle dichiara («MCP documenti: server … raggiungibile, N cartelle
dichiarate»); **non blocca l'avvio**.

## 6. Installazione e verifica

1. **Pubblicazione**: `dotnet publish ThinkAI.FileSystemMcpServer -c Release -r win-x64 --self-contained false`.
   Il pacchetto deve contenere `appsettings.json`, la cartella `tessdata` (modelli di lingua),
   la licenza Aspose e `vec0.dll`.
2. **Servizio**: `Scripts\Install-Http-Service.ps1 -InstallPath "<cartella>"` (opzioni
   `-UseDomainAccount -ServiceAccount "DOMINIO\utente"`, `-RemoveOldService` per togliere il vecchio
   servizio TCP). Crea il servizio **ThinkAIFileSystemMcp**, imposta account, salva e rimette
   `appsettings.json` e `index.db`, prova `/health`, imposta riavvio automatico in caso di errore.
3. **Primo avvio e approvazione** dell'impronta nel Configuration Manager (*Accessi configurazione*),
   poi `Start-Service ThinkAIFileSystemMcp`.
4. **Verifica**: `Invoke-RestMethod http://localhost:7050/health`.

> **Un aggiornamento sovrascrive `appsettings.json`**: il pacchetto porta un file di esempio (con
> `C:\documenti`). Prima di un aggiornamento a mano salva quello dell'installazione e dopo rimetti
> almeno `AllowedDirectories`, `ClientId`, `IndexDbPath`. Lo script di installazione lo fa da solo.

> **Il primo avvio dopo l'aggiornamento del 10 ottobre**: l'indicizzatore crea **tre indici** nel DB
> (log: *Creazione indice SQLite…* e *…pronto*), leggendo tutto il testo OCR e tutti i vettori: su
> 115.000 file e 600.000 vettori servono fino a **15–20 minuti** (stima); il servitore risponde come
> sempre. **Non fermare il servizio** in quel momento (la creazione ripartirebbe da capo). Dal
> secondo avvio l'indicizzatore torna al lavoro in <1 minuto (invece di 8–16) e una cartella
> rinominata non blocca più il database.

| Dove | Cosa leggere |
|---|---|
| `/health` → `index` | `fileCount`, `embeddingVectorFiles` su `embeddingEligibleFiles`, `embeddingCoverage`, `ocrDocumenti`, `ocrIncerti`. `contentReady: false` è normale in modalità `embedding` |
| `/health` → `capabilities.aspose` | `ready` se le licenze sono attive; `degraded` = niente OCR dei PDF e niente .doc/.xls |
| `logs\mcpfilesystem-AAAAMMGG.log` | «Server pronto - in ascolto su…», «Indice vettoriale ANN: componente nativo vec0 presente», «OCR: modelli di lingua presenti (ita+eng)», «Licenza Aspose caricata…», «Inventario archivio…», «Sync completata: +A -R ~U file» |
| `logs\indicizzatore\` | Lavoro dell'indicizzatore: estrazione, OCR, vettori |
| `logs\mcp-bootstrap.log` | Errori di avvio e richiesta di approvazione (EnrollmentPending) |

## 7. Problemi frequenti

| Sintomo | Causa probabile e rimedio |
|---|---|
| 400 «Host non consentito.» | Il nome usato non è in `AllowedHosts`: aggiungilo |
| 401 «API key MCP non valida.» | Chiave diversa fra `McpTransport:ApiKey` e `McpServer:ApiKey` (controlla anche i profili remoti) |
| Servizio si ferma con codice 2 | Impronta da approvare nel Configuration Manager |
| Si ferma con «Configurazione MCP HTTP non sicura» | Host in rete senza HTTPS o senza autenticazione, o filtro per utente senza autenticazione |
| Si ferma con «Configurazione FileSystem non valida» | Provider sconosciuto (giusto: `gemini-vertex`, non `vertex`), chiave del provider mancante, valori fuori intervallo |
| «Nessuna directory consentita valida» | Cartelle inesistenti o non visibili all'account del servizio: usa **percorsi UNC**, non unità mappate |
| Ricerca con zero risultati | Guarda nel log la riga *Ricerca completata* con i conteggi (trovati → dopo filtro cartelle → dopo filtro permessi) |
| Reindicizza sempre gli stessi file | La data del file cambia a ogni giro (antivirus, sincronizzazioni) o `IndexDbPath` non è sempre lo stesso |
| Ricerca oltre due minuti | Il Backend la interrompe dopo `SearchTimeoutMs` con messaggio leggibile |
