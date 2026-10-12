# Configurare un cliente nuovo, chiavi di configurazione, glossario

Fonte: guida ottobre 2026, cap. 15. L'ordine conta: ogni passo usa il lavoro del precedente.

## Sequenza per un'installazione nuova (12 passi)

| # | Passo | Dove | Fatto quando |
|---|---|---|---|
| 1 | **Server MCP FileSystem** installato, cartelle UNC raggiungibili dall'account del servizio, indicizzazione avviata (solo se servono i documenti) | Server dei file · `mcp-filesystem.md` | L'health risponde e il log dice quanti file sono da indicizzare |
| 2 | **Progetto e connessione dati**, azienda abilitata | Dashboard → progetto | La ChatRoom si apre sul database giusto |
| 3 | **Conoscenza del database**: tabelle, Genera Modello AI, domande per chi usa il gestionale, `[da confermare]` risolti, salvataggio | Configuratore, passi 1 e 2 · `conoscenza-database.md` | Nessun `[da confermare]` sulle tabelle usate |
| 4 | **Misure nel testo**: colonne con numeri, regole proposte e confermate, estrazione | Configuratore, passo 2 | Lo stato dice quante righe hanno misure |
| 5 | **Vocabolario**: gruppi proposti, rumore scartato, gruppi a mano | Configuratore, passo 2 | Gruppi confermati e salvati |
| 6 | **Tipologie di analisi**: metriche, filtri, output; Salva e Applica; controllo del Prompt Chat | Configuratore e Impostazioni Analisi | Le tre risposte (Chat, Dashboard, Relazione) escono coerenti |
| 7 | **Preferenze Viste e semantica**: keyword senza sovrapposizioni, categoria, descrizione semantica, descrizioni di tabelle e viste | Menu ⋮ → Preferenze Viste · `contesti-e-reset.md` | Le domande di prova vanno tutte al contesto giusto |
| 8 | **Prova con domande vere**, scritte da chi usa il gestionale; stile **Standard**. Le correzioni che devono valere sempre si insegnano in chat e si confermano | ChatRoom · `regole-insegnate.md` | Risposte giuste e ripetibili |
| 9 | **Esporta il pacchetto della conoscenza** | Configuratore → Esporta | File `.thinkai.json` conservato |
| 10 | **Workforce Console** (solo se il cliente ha agenti Workforce): tabelle `THINKAI_WF_*`, agenti registrati, Rielabora abilitata | DB del gestionale e Console · `workforce-console.md` | Ogni agente compare nel selettore e il collaudo del §8 della Console è passato |
| 11 | **Chat web** (se il cliente la usa): Backend e WebProxy alla stessa versione, tunnel registrato | Proxy e log del Backend · `chat-web.md` | Nel log *backend registrato sul proxy*; un utente normale vede i suoi contesti |
| 12 | **NodeLLM** (se il cliente usa modelli sui suoi server): chiavi del gateway, sezione `NodeLlm` del Backend, modelli importati, connessione dati sul modello scelto | Gateway, Configuration Manager e Gestione modelli AI · `nodellm.md` | Una domanda di prova risponde dal modello in azienda; nessun avviso di cluster aperto nel log del gateway |

**Il banco di prova**: prima di consegnare, fatevi dare dal cliente **10–20 domande vere** con la
risposta attesa; ripetetele dopo ogni modifica importante (è il modo più rapido per capire se una
correzione ne ha rotta un'altra). Per domande con elenco di casi e dubbi lo stile **Standard**
mostra tutto; **Rapida** riassume in 2–3 paragrafi.

Percorso tipico per passare dal DB di prova a quello del cliente: costruisci la conoscenza su una
copia, prova con domande vere, **Esporta** il pacchetto, **Importa** sul DB del cliente (stessa
versione di Backend o successiva; poi lancia **Estrai su tutta la tabella** una volta).

## Chiavi nuove nei file di configurazione (rispetto ai pacchetti del 18 settembre: Backend 3.0.0.20, MCP 2.0.0.20)

Le funzioni nuove non elencate qui (conoscenza, misure, vocabolario, regole insegnate, indici del
server MCP) **non hanno chiavi: si attivano da sole**. Il **profilo remoto** del Configuration
Manager vince sul file: se il profilo di un cliente ha una sua sezione `Xference` o `NodeLlm`, la
voce va scritta lì.

**Backend** (`appsettings.json`)

| Chiave | A cosa serve | Nel pacchetto |
|---|---|---|
| `Xference:ReasoningByModel` (nuova, 3.1.0.9) | Ragionamento per singolo modello: `none` lo spegne nelle query SQL e nelle risposte in chat, `model` lo lascia al modello. Vince su `Xference:Reasoning`. Vale anche per NodeLLM (`NodeLlm:ReasoningByModel`) | Qwen3.6-35B-A3B spento, con e senza prefisso `vllm/` |
| `Xference:ReasoningForAnalysis`, `NodeLlm:ReasoningForAnalysis` (**tolte**) | Nelle relazioni e dashboard il ragionamento è sempre spento: non c'è più niente da impostare | — |

**Server MCP FileSystem** (sezione `FileSystemServer`)

| Chiave | A cosa serve | Nel pacchetto |
|---|---|---|
| `EmbeddingExtractors` | Estrattori in parallelo, 0 = automatico; regola pratica ~1,5 per core fisico | 6 (dalla 2.0.0.29) |
| `OcrRilettura:RileggiPagineConIdentificatori` | Rilegge anche le pagine con codici (lettere e cifre) che Tesseract ha letto con confidenza alta; acceso, su fatture e schede tecniche sale quasi ogni pagina | false (dalla 2.0.0.29) |
| `OcrRilettura:MaxPagineRiletteAlGiorno` | Tetto pagine rilette in un giorno; 0 = nessun tetto; fissa in anticipo la spesa massima | 5000 (dalla 2.0.0.29) |
| `OcrRilettura:Endpoint` (2.1.0.9) | Indirizzo dell'API di rilettura, per passare da un gateway europeo. Con modello Claude non va scritto: col valore predefinito si usa l'API di Anthropic | assente: vale il predefinito |
| `VectorInMemory`, `VectorInMemoryMaxMB` (2.0.0.22) | Il servitore tiene i vettori in memoria (ricerche in decimi di secondo). All'avvio, oltre il tetto (1024 MB, ~950.000 blocchi) non li carica e la ricerca torna lenta: per archivi più grandi alza il tetto | assenti: valgono `true` e 1024 |
| `ClaudeApiKey` (2.1.0.9) | Chiave per rileggere con un modello Claude; **solo nel profilo remoto** | — |

**Tolte dal pacchetto del server MCP (5 ottobre)**: `RequireConfirmationForDestructiveOps`,
`McpTransport:ConnectionTimeoutSeconds`, `McpTransport:EnableTransportLogging` (non avevano effetto)
e `RipassaDocumentiDaFile` (un ripasso fatto una volta per cliente). Se restano nel file di
un'installazione non fanno danni; per `RipassaDocumentiDaFile` il log avvisa che il file non c'è.

Il primo avvio del server MCP dopo l'aggiornamento crea tre indici e dura di più, una volta sola
(`mcp-filesystem.md` §6).

## Modelli OpenAI di nuova generazione (da §1.1 della guida)

`gpt-5.5`, `gpt-5.6`, `gpt-6` e `gpt-6.1` sono disponibili in chat, negli step AI e nella
Dispositiva; costi del listino nei report; nelle relazioni i numeri in formato italiano e i totali
non contati due volte. Aggiornamento da *Gestione modelli AI → Aggiorna da Provider*. Per i
limiti con gli strumenti (`gpt-6.1-sol`, `gpt-6-astra`) vedi `workforce-studio.md`, sezione
«quanto ragiona il modello». *Dettagli oltre quanto scritto in guida: `⚠️ DA VERIFICARE`.*

## Glossario

| Termine | Significato |
|---|---|
| Contesto / tipologia di analisi | Area di analisi su cui risponde la chat (Vendite, Crediti…): tabelle, prompt, presentazione |
| Preferenza vista | Regola che dice quando usare un contesto: viste collegate, keyword, categoria, descrizione semantica |
| Conoscenza del database | Testo unico per database con legami, codici, regole, testo libero, controlli |
| Legame forte / debole | Join provato sui dati (forte) o con corrispondenza parziale, da usare solo se confermato (debole) |
| `[da confermare]` | Segno lasciato dall'AI dove manca un significato che solo chi usa il gestionale conosce |
| Regola delle misure | Regola che legge i numeri da un testo per una famiglia di prodotti; `TUTTE` vale per ogni famiglia |
| Famiglia / variante | Gruppo di prodotti riconosciuto dall'inizio della descrizione / modo in cui è scritto |
| Vocabolario | Gruppi di parole che nei dati indicano la stessa cosa; in OR fra loro |
| Pacchetto della conoscenza | File `.thinkai.json` con conoscenza, regole delle misure, vocabolario e regole insegnate per tutti |
| Regola insegnata | Correzione data in chat («impara…», «d'ora in poi…») che ThinkAI ricorda per le domande successive sullo stesso DB |
| Reset | Comando della ChatRoom: la domanda dopo parte senza la storia della chat |
| RAG | Retrieval-Augmented Generation: l'AI risponde dopo aver recuperato i pezzi di documento pertinenti |
| Embedding | Vettore numerico che rappresenta il significato di un pezzo di testo; serve a cercare per significato |
| OCR | Lettura del testo dalle immagini e dalle scansioni |
| MCP | Model Context Protocol: il protocollo con cui il Backend usa il server dei documenti |
| Streamable HTTP | Trasporto MCP su HTTP con risposte in streaming; sostituisce STDIO e il ponte TCP |
| Chat web / proxy / tunnel | ThinkAI nel browser; il proxy è il servizio pubblico a cui parla il browser; il tunnel è il canale che il Backend del cliente apre verso il proxy |
| Workforce Console | Pagina web con cui il cliente segue i documenti elaborati dagli agenti Workforce |
| Registro degli agenti | Tabella `THINKAI_WF_AGENTI`: gli agenti visibili nella Console, con nome e opzioni |
| LOG_KEY / CORRELATION_ID | Il singolo tentativo di elaborazione / il documento, uguale fra i tentativi |
| Rielabora | Azione della Console che sblocca un documento fermo e lo rimette in coda all'agente |
| NodeLLM / gateway / nodo | Cluster dei modelli AI sui server dell'azienda; il gateway è l'indirizzo unico a cui parla ThinkAI; un nodo è una macchina del cluster con il suo agent |
| Motore (vLLM, ds4, Ollama) | Il programma che esegue davvero il modello sul nodo |
| Percorso UNC | Percorso di rete `\\server\condivisione`, l'unico visibile a un servizio Windows |
