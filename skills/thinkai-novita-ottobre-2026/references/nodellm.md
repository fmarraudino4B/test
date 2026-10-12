# ThinkAI NodeLLM: i modelli AI sui server dell'azienda

Fonte: guida ottobre 2026, cap. 14. NodeLLM fa girare modelli AI sulle macchine dell'azienda
(server con GPU, workstation, in futuro anche Mac). Un **gateway** raccoglie i modelli di tutte le
macchine e li offre a ThinkAI da un solo indirizzo, come un provider cloud. Domande, dati e risposte
restano nella rete aziendale. Per l'utente è un provider come gli altri: nella ChatRoom e negli
agenti cambia solo la voce **NodeLLM (Cluster aziendale)**. Con la 3.1 il cluster è passato dalla
prova a un'installazione reale su due macchine, collaudata su chat, query, dashboard, allegati e agenti.

## Novità

| Novità | A cosa serve |
|---|---|
| Cluster a più macchine | Un gateway e un agent su ogni macchina: i modelli di tutte compaiono in un solo catalogo |
| Più motori di esecuzione | vLLM (anche su Windows Server, in WSL2), ds4 per DeepSeek V4, Ollama, llama-server |
| Repliche e failover | Stesso modello su più macchine: il gateway manda la richiesta alla meno occupata; se una non risponde passa alla successiva |
| Avvio automatico | Dopo un riavvio i nodi ripartono da soli e ripubblicano i loro modelli |
| Dashboard e relazioni dal JSON | Con i modelli in azienda la pagina è costruita da un **modello fisso**: grafici sempre presenti, totali calcolati dal Backend, niente pagine troncate |
| Allegati e CSV | Gli allegati finiscono nella domanda; un CSV diventa una tabella con totali già calcolati |
| Ragionamento per modello | Si accende/spegne modello per modello; in dashboard e relazioni è **sempre spento** |
| Agenti Workforce | Gli step AI girano su NodeLLM, anche con PDF e immagini allegati (`workforce-studio.md`) |

## Usarlo da ThinkAI

1. **Importare i modelli**: Gestione modelli AI, provider **NodeLLM**, pulsante di aggiornamento: legge il catalogo del gateway; per ogni modello arrivano contesto massimo, uso degli strumenti (*tool*) e visione. I modelli che il cluster non pubblica più vengono disattivati.
2. **Collegare la chat**: nella connessione dati del progetto scegli provider **NodeLLM (Cluster aziendale)** e il modello.
3. **Negli agenti**: step AI di Workforce Studio (AiAnalysis, ClassifyText, ExtractStructured) → provider **NodeLLM (cluster)**. Per gli step con strumenti serve un modello che li gestisca.

> **Cosa non c'è con i modelli in azienda**: la ricerca web e i file caricati sul provider cloud sono
> funzioni dei provider cloud: con NodeLLM la richiesta viene servita senza, con un avviso nel log.
> I PDF degli agenti arrivano al modello come immagini delle pagine.

## Cosa fa ThinkAI con i modelli in azienda (vale per NodeLLM, Ollama, vLLM, Xference)

I modelli open scrivono più lentamente dei cloud e hanno contesti più piccoli. ThinkAI si adatta:
- **Il budget dei dati segue il modello**: righe e testo da mandare si calcolano dal contesto del modello letto dal catalogo.
- **Dashboard e relazioni dal JSON**: il modello restituisce un JSON corto (titolo, sintesi, indicatori, grafici, tabelle, conclusioni) e il **Backend costruisce la pagina** da un modello fisso. 2.000–4.000 token invece di 16.000–24.000. Vale per Dashboard completa, Dashboard personalizzata e Relazione testuale.
- **I numeri li calcola il Backend**: totali e somme per categoria/mese entrano già calcolati; il modello li riporta, non li stima.
- **Gli allegati entrano nella domanda**: testo dei file in richiesta; un **CSV** → tabella di dati coi totali già calcolati.
- **Ragionamento solo dove serve**: per le query SQL lo decide la configurazione; in dashboard e relazioni **sempre spento** (i modelli locali consumavano tutto lo spazio ragionando, senza scrivere la pagina).

> Se il modello non risponde con un JSON, il testo ricevuto viene mostrato comunque in una pagina.
> Per tornare alla pagina scritta dal modello: `LocalProviders:DashboardDaJson = false`.

## Il cluster: gateway, nodi, motori

| Componente | Dove gira | Cosa fa |
|---|---|---|
| **Gateway** | Una macchina sempre accesa, raggiungibile da nodi e Backend | Tiene il catalogo dei modelli, sceglie il nodo per ogni richiesta, controlla le chiavi; dashboard web su `/admin/ui/` |
| **Agent** | Ogni macchina del cluster | Registra il nodo, manda lo stato ogni **15 s** (GPU, memoria, temperatura), avvia/sorveglia il motore, pubblica il modello |
| **Motore** | Sulla macchina del nodo | vLLM, ds4, Ollama o llama-server: esegue davvero il modello |

**A ogni richiesta il gateway**: controlla che il modello esista e sia pubblicato (altrimenti errore
chiaro); con lo **stesso modello su più nodi** sceglie prima i nodi attivi, poi quello con meno
richieste in corso (se il motore non accetta la connessione passa al successivo); **rifiuta le
immagini** dirette a un modello senza visione; traduce **accensione/spegnimento del ragionamento**
nel linguaggio di ogni motore; pubblica per ogni modello contesto, strumenti, visione e **stato**
(attivo se almeno un suo nodo è attivo).

**Quando qualcosa si ferma**: se il **gateway si riavvia** i nodi se ne accorgono al primo segnale e si
registrano di nuovo (i modelli mancano dal catalogo una quindicina di secondi); un errore verso il
gateway **non ferma l'agent** (motore acceso, modello ripubblicato appena il gateway torna); dopo un
**riavvio della macchina** l'agent riparte da solo (attività pianificate su Windows Server, servizio
utente su Linux) e riavvia il motore.

> **Le chiavi del cluster**: il gateway ha due serrature: le **chiavi API** per le richieste ai modelli
> (vanno anche nel Backend ThinkAI) e i **token di amministrazione** per agent e dashboard. Se sono
> vuote il cluster è aperto e all'avvio compare un avviso: va bene solo per una prova, **mai in produzione**.

## Configurazione del Backend (sezione `NodeLlm`, meglio nel profilo remoto del Configuration Manager, che vince sul file)

```json
"NodeLlm": {
  "BaseUrl": "http://server-del-gateway:5000",
  "ApiKey": "una delle chiavi API del gateway",
  "EnableTools": true,
  "MaxOutputTokens": 24000,
  "Reasoning": "model",
  "ReasoningByModel": { "qwen3.8-27b": "none", "deepseek-v4-flash": "none" }
}
```

| Chiave | Serve a | Consigliato |
|---|---|---|
| `BaseUrl` | Indirizzo del gateway | `http://server-del-gateway:5000` |
| `ApiKey` | Una delle chiavi API del gateway; vuota solo se il cluster è aperto | Sempre valorizzata in produzione |
| `EnableTools` | I modelli possono usare gli strumenti | `true` |
| `MaxOutputTokens` | Tetto della risposta; 0 = nessuno, decide il motore | `24000` (spazio alla dashboard completa) |
| `Reasoning` | `model` lascia il ragionamento come lo vuole il modello, `none` lo spegne | `model` |
| `ReasoningByModel` | Idem, modello per modello; **vince su `Reasoning`** | `none` per i modelli che sulle query impiegano troppo |
| `AiProviders:TimeoutMinutes` | Attesa massima del Backend verso un provider | `45` (una dashboard completa in locale può richiedere 12–20 min) |

Le stesse chiavi valgono per **Xference** nella sezione `Xference` (per ThinkAI è un provider con
modelli open in un data center italiano e si comporta come NodeLLM).

## Tempi e capacità (misure di collaudo, dipendono da macchina e modello)

| Nodo | Modello e motore | Cosa regge |
|---|---|---|
| Server x86 con GPU da 48 GB | Qwen da 27 miliardi di parametri, vLLM | Più richieste insieme (continuous batching), ~23 token/s per risposta, contesto fino a 131.072 token; pronto ~7 min dopo il riavvio |
| Nodo ARM con 128 GB di memoria unificata | DeepSeek V4 Flash, ds4 | ~21 token/s; due richieste insieme con contesto fino a 270.000 token (~200.000 domanda + 64.000 risposta); la terza attende; pronto in ~1 minuto |

- **Prima parola**: con sessioni in batch poco più di 1 s; una domanda da 200.000 token richiede ~2 min prima di cominciare.
- **Dashboard**: una completa costa **minuti, non secondi** (prezzo di scrivere in locale). Il JSON ha tolto i troncamenti, non il tempo di calcolo.
- **Ragionamento**: acceso, la prima parola tarda qualche secondo e il ragionamento consuma parte di `MaxOutputTokens`; su un modello medio una query SQL poteva richiedere 7–12 min, per questo il pacchetto lo spegne per modello.

## Problemi frequenti

| Sintomo | Causa probabile | Cosa fare |
|---|---|---|
| Chat: *modello non trovato* per qualche secondo | Gateway appena riavviato: i nodi si registrano al segnale successivo | Aspetta; se dura >1 min controlla nei log degli agent *registrato* e *pubblicato* |
| *Runtime del nodo non raggiungibile* | Modello nel catalogo ma motore fermo o macchina in riavvio | Aspetta il rientro del nodo o riavvia il motore; dopo 30 s senza segnali il nodo risulta spento |
| *Chiave API non valida* | `NodeLlm:ApiKey` vuota o diversa da quelle del gateway | Copia nel Backend una delle chiavi API del gateway |
| *Modello senza visione* | Immagine o PDF a un modello che non vede | Scegli un modello con visione nel catalogo |
| La risposta è il ragionamento, non la risposta | Spazio di risposta troppo piccolo per un modello che ragiona | Alza `MaxOutputTokens` o spegni il ragionamento per quel modello |
| Dashboard in timeout | Output lungo su modello locale | Controlla `AiProviders:TimeoutMinutes` (45) e `MaxOutputTokens` (24000) |
| Nodo nella dashboard senza GPU e temperatura | Macchina senza lo strumento delle metriche (es. `nvidia-smi` non nel PATH dell'agent) | Su scheda NVIDIA verifica `nvidia-smi`; su Mac è normale |
