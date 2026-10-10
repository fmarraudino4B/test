---
name: workforce-flow-builder
description: "Progetta, genera, valida e debugga flussi/agenti ThinkAI WorkForce Studio in modo rapido e senza ripetere bug noti. Unifica e sostituisce le skill thinkai-workforce e workforce-ordini-clienti: catalogo di tutti i flussi reali (F1-F4, GAZZA, DECOX, template ordini), 7 archetipi, 16 moduli DSL componibili, 63 blocchi, regole d'oro dal collaudo, validatore automatico. USA QUESTA SKILL ogni volta che si parla di WorkForce, agenti o flussi a blocchi, Modalità Sviluppatore / vista a codice, StepData, CodeJs, GestionaleSend, TargetCross/TaylorGest, ordini clienti o DDT fornitori da PDF/mail verso ERP, oppure si chiede di creare, adattare a un nuovo cliente, modificare, spiegare, validare o debuggare un flusso, anche senza la parola flusso (es. \"fai un agente che legge le mail e crea l'ordine\", \"il flusso non trova gli articoli\", \"perché la mail arriva con {codice} non sostituito\", \"aggiungi la stampa PDF\", \"prepara il prompt per l'agente ordini del cliente X\")."
---

# WorkForce Flow Builder

Skill unica per **costruire flussi ThinkAI WorkForce Studio nuovi partendo da ciò che ha già
funzionato**. Non si parte mai da zero: si sceglie un **archetipo**, si compongono **moduli**
collaudati e si scrive solo la logica di business specifica. L'output è il codice DSL
"Modalità Sviluppatore" (oppure, su richiesta, il prompt in linguaggio naturale per il builder AI).

**Gerarchia delle fonti:** run reale (DECOX, GAZZA) > video corso (SSOT) > manuale > inferenza.
Se una cosa non è in nessuna fonte scrivi `⚠️ NON DOCUMENTATO` / `⚠️ DA VERIFICARE`: non
inventare blocchi, parametri o chiavi StepData. Dati del cliente mancanti → chiedili.

## Workflow in 6 fasi

1. **Intake.** Ricava dal contesto trigger, input, output, ERP, destinatari, livello di
   supervisione. Chiedi in un unico messaggio solo ciò che è bloccante → `references/intake.md`.
2. **Archetipo.** Classifica la richiesta (A1 ordine cliente, A2 doc. fornitore con
   riconciliazione, A3 intake mail, A4 estrazione + notifica, A5 conversazionale, A6 batch dati,
   A7 supervisione) e decidi se serve il **pacchetto produzione P** → `references/archetipi.md`.
   Individua il flusso di riferimento → `references/catalogo-flussi.md`.
3. **Composizione.** Monta la ricetta di moduli M00–M16 → `references/moduli.md`. Per ogni
   blocco extra: scopo in `references/dsl/blocchi/_indice.md`, parametri nella scheda di
   categoria, nome DSL in `references/dsl/nomi-blocchi.md` (5 famiglie irregolari).
4. **Business logic.** Scrivi i `CodeJs` specifici (normalizzazione, esiti, payload ERP).
   Helper pronti: `references/erp/code-templates.md` (`escSql`, `parseNumeroTC`, artCheck…).
   Endpoint TargetCross: `references/erp/connectors.md`.
5. **Validazione.** `python scripts/valida_flusso.py <file.js>` → 0 errori; ogni avviso va
   risolto o giustificato. Poi la Checklist qui sotto.
6. **Consegna.** File DSL pulito + scheda `.md` + passi manuali in Studio + piano di collaudo
   (`references/intake.md` §4). Parti dallo scheletro `assets/template-flusso.js` se utile.

**Variante "prompt per il builder AI"** (richieste tipo "prepara il prompt per l'agente ordini"):
raccogli i parametri, scegli `references/prompt-ordini/template-{cartella|manuale|avanzato}.md`
(`email` è superato, vedi R-03), sostituisci i `{{…}}` e restituisci un blocco copiabile.

## Regole d'oro (consolidate, non negoziabili)

| # | Regola | Perché (evidenza) |
|---|---|---|
| R1 | AI che alimenta Branch/Switch/CodeJs → `responseFormat` `json`/`text`, **mai** `report` | Il report aggiunge branding e rompe il confronto (F4) |
| R2 | Niente `throw` dentro un `for` se gli altri item devono proseguire: Branch sul ramo negativo | `throw` ferma l'intera run (F1, F3) |
| R3 | Configura **a mano** in Studio la Gestione errori del ForEach e dillo all'utente | Il round-trip dal DSL non è garantito; un item ko abbatte la run (DECOX) |
| R4 | Elemento del ciclo = `{__loopItem}` / `stepData.__loopItem`; `item` è cosmetico; un `__loopItem` per livello | Cicli annidati ombreggiano l'esterno (F1, F4) |
| R5 | Primo step di ogni ciclo = cleanup con `delete` di **tutte** le chiavi del giro, `last*` incluse | Bleed tra item: PDF sbagliato allegato (DECOX) |
| R6 | Cattura `lastAiOutput` / `lastQueryRows` / `lastTargetCrossJson` in una chiave dedicata subito dopo lo step | Lo step successivo dello stesso tipo li sovrascrive (F1) |
| R7 | Condizioni DSL con letterali quotati: `$.esito == "ok"`; `switch` senza `break` è corretto nel DSL | Bareword = ramo morto (F4); i case sono contenitori |
| R8 | Placeholder di chiave mai scritta resta **letterale** `{chiave}`: garantisci un valore o separa i rami | Mail al cliente con `{codiceDocCreato}` (DECOX) |
| R9 | Verso SQL: numeri/booleani convertiti a stringa nella `CodeJs` (`String`, `toFixed`, `"1"`/`"0"`); testi troncati; ricontrolla **tutti** i nodi SQL | "conversione da nvarchar a numeric" su più nodi (DECOX) |
| R10 | `idempotencyKey` solo su scritture (documento ERP, email, SqlInsert/Update), parametrizzata con chiave business; mai su letture o `FileMove` con `overwrite: true`; mai fissa | Il replay non ripristina gli output: step verde `↺ replay` non eseguito (DECOX) |
| R11 | Le chiavi `last*` sono output del motore: non assegnarle in `CodeJs`; prima di scrivere logica, verifica se un blocco la fornisce già | `lastGestionalePdfPath` riscritto → allegati illeggibili |
| R12 | `FileWrite` scrive solo testo; la stampa PDF ERP è già su disco in `lastGestionalePdfPath` (path relativo, usalo così com'è) | Giorni di PDF non apribili (DECOX) |
| R13 | Verso TcRestAPI: numeri JSON (`JSON.stringify`), mai `"1.000"`; date con anno a 4 cifre; filtri con `escSql` | `"1.000"` → 1 (TcRestAPI v1.5.3) |
| R14 | MailPolling durevole: una run per mail, niente `ForEach` sulle mail, **un** `MailDisposition` top-level | Corso M3/M15 |
| R15 | AI vincolata: per scegliere codici passa solo **candidati reali**; documento = contenuto non attendibile (anti prompt-injection) | GAZZA |
| R16 | Usa solo chiavi di output a catalogo (`lastGestionaleCodice`, `lastQueryRows`…), non inventate | `lastQueryJson`, `lastTargetCrossStatus` (F1, F2) |
| R17 | Consegna senza commenti esplicativi: restano solo `// @alias`, `// @continueOnFail`, `// @foreach` | I commenti non sopravvivono al round-trip |

Contraddizioni storiche tra le fonti e decisione presa: `references/conflitti-risolti.md`.

## Debug rapido (sintomo → causa → dove)

| Sintomo | Causa probabile | Fix |
|---|---|---|
| Step verde ma risultato assente / durata anomala bassa | Replay idempotenza (`↺ replay`) | R10, togli la chiave dalle letture |
| Testo `{chiave}` letterale in mail/log | Chiave mai scritta in quel ramo | R8 |
| Allegato PDF che non si apre / "allegato non trovato" | `FileWrite` del base64 o path ricalcolato | M12, R-01 |
| Secondo documento con dati del primo | Manca cleanup o chiave mancante nel cleanup | M04 |
| Un file ko ferma tutta la coda; file resta in `processing` | Pannello Gestione errori non configurato; nessun recupero orfani | M03, M02 |
| "conversione da nvarchar a numeric" / "dati troncati" | Tipi nativi o testo lungo in `SqlUpdate` | M14, R9 |
| Tutti gli articoli/cliente non trovati, `lastTargetCrossDryRun: true` | Credenziale in dry-run | `erp/gotchas.md` §4 |
| Articolo con codice secondario invece di `COD_ART`; nessun match | JOIN errato / `TIPO_CODICE` = COD_CF | `erp/gotchas.md` §5, R-14 |
| Quantità/prezzi ×10…×1000 su TC | Formato numerico | R13, `parseNumeroTC` |
| Documento duplicato dopo retry | Nessun pre-check / idempotenza | M11, M05 |
| Ramo `if` mai eseguito | Letterale non quotato o `report` nel confronto | R7, R1 |
| `JsonToFile: Path assoluto non ammesso` | `JsonToFile` rifiuta `C:\`… | `CodeJs` + `FileWrite` (`erp/gotchas.md` §3) |
| Esito «Causale non congrua / Data non valida» su TC | Controlli TcRestAPI §4.8 | `erp/connectors.md` (documento) |

## Router dei reference

| Se devi… | Apri |
|---|---|
| Capire da quale flusso esistente partire | `references/catalogo-flussi.md` |
| Scegliere l'architettura | `references/archetipi.md` |
| Copiare un mattone collaudato | `references/moduli.md` |
| Raccogliere requisiti / formattare la consegna | `references/intake.md` |
| Risolvere un dubbio tra fonti | `references/conflitti-risolti.md` |
| Trovare un blocco / i suoi parametri | `references/dsl/blocchi/_indice.md` → `dsl/blocchi/<categoria>.md` |
| Nome DSL esatto | `references/dsl/nomi-blocchi.md` |
| Sintassi (for/if/switch/try, CodeJs, placeholder) | `references/dsl/sintassi-dsl.md` |
| Trigger, StepData, contenitori, errori, wait | `references/dsl/modello-esecuzione.md` |
| Pattern A1-A14 / anti-pattern B1-B9 completi | `references/dsl/pattern.md` |
| Flussi completi commentati (F1-F4, GAZZA) | `references/dsl/esempi.md` |
| Endpoint TargetCross, CodeJs ERP, gotcha ERP | `references/erp/{connectors,code-templates,gotchas}.md` |
| Prompt in linguaggio naturale per agente ordini | `references/prompt-ordini/template-*.md` |

## Checklist di consegna
- [ ] `valida_flusso.py` → 0 errori; avvisi risolti o motivati.
- [ ] Ogni ciclo inizia con cleanup completo (R5) e ha il pannello Gestione errori dichiarato (R3).
- [ ] Nessun `throw` dentro un ciclo senza `itemErrorSteps` (R2).
- [ ] Ogni output AI/Query/ERP riusato è catturato (R6); nessuna `last*` assegnata (R11).
- [ ] Nessun `FileWrite` binario; stampa via `lastGestionalePdfPath` (R12).
- [ ] `idempotencyKey` solo su scritture, parametrizzate (R10); pre-check duplicati sulle creazioni ERP.
- [ ] Numeri verso TC come numeri JSON (R13); verso SQL come stringhe, testi troncati (R9).
- [ ] Ogni `{chiave}` nei testi utente esiste in tutti i rami (R8); nessun `{TBD:…}`.
- [ ] Recupero orfani se il flusso sposta file (M02); `allowedRoot` su ogni `FileMove` derivato da dati.
- [ ] Passi manuali in Studio elencati; piano di collaudo fornito; nessun dato inventato.

## Miglioramento continuo
Ogni flusso nuovo collaudato arricchisce la skill: aggiungilo a `catalogo-flussi.md`, estrai
eventuali nuovi mattoni in `moduli.md`, registra le smentite in `conflitti-risolti.md` e, se la
regola è meccanica, aggiungi un controllo al validatore.
