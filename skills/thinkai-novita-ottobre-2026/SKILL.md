---
name: thinkai-novita-ottobre-2026
description: "Riferimento operativo sulle novità ThinkAI di ottobre 2026 (Backend e MAUI 3.1.0.10, server MCP FileSystem 2.1.0.10, ChatWeb e Workforce Console 1.2.10): conoscenza del database, regole delle misure nel testo, vocabolario, Preferenze Viste e semantica, Reset ChatRoom, Documenti (Ricerca / Conversazione / Conversazione + dati), server MCP FileSystem con RAG e OCR, chat web e tunnel, palette nuove di Workforce Studio (PDF→Markdown, Controlla documento letto, GestionaleSend/TcRestAPI 1.5.0, ragionamento dei modelli), Workforce Console multi-agente (THINKAI_WF_*), regole insegnate in chat, NodeLLM, configurazione di un cliente nuovo. USA QUESTA SKILL ogni volta che si parla di Impostazioni Analisi, Configuratore, conoscenza del database, [da confermare], misure nel testo, vocabolario, Preferenze Viste, cambio di contesto involontario, Reset, scheda Documenti, server MCP / RAG / index.db / OcrRilettura / appsettings del server documenti, chat web / WebProxy / tunnel, Workforce Console / Rielabora / LOG_KEY / CORRELATION_ID / FILE_SOURCE, regole insegnate (\"impara…\", \"d'ora in poi…\"), NodeLLM / gateway / cluster, chiavi di configurazione nuove, oppure serve il checklist per configurare/collaudare un cliente nuovo. Per costruire o validare il codice DSL dei flussi usa insieme la skill thinkai-workforce."
---

# ThinkAI — Novità di ottobre 2026 (3.1.0.10)

Sintesi operativa della guida *«Le novità di ThinkAI — ottobre 2026»* (Four AI Srl, edizione
ottobre 2026). Serve a rispondere a domande di configurazione, collaudo e diagnosi su queste
funzioni **senza reinventare**: ogni dettaglio qui dentro viene dalla guida.

**Versioni coperte:** ThinkAI Backend e MAUI **3.1.0.10** · server MCP FileSystem **2.1.0.10** ·
ChatWeb e Workforce Console **1.2.10** · confronto con i pacchetti del 18 settembre
(Backend 3.0.0.20, MCP 2.0.0.20).

**Pubblico:** Admin e SystemAdmin, chi installa; i capitoli su ChatRoom/Reset/regole insegnate
anche per gli utenti.

## Regole di ingaggio

- **Non inventare**: se un nome di campo, di chiave, di blocco DSL o un valore non è in questi
  file, scrivi `⚠️ DA VERIFICARE` e chiedi (versione del Backend, schermata, log). Gli esempi
  della guida usano un gestionale tipo con prodotti inventati: i nomi nel database del cliente
  possono essere diversi.
- **Controlla la versione**: tutto vale da 3.1.0.10 in su. Un pacchetto della conoscenza che usa
  funzioni nuove (es. famiglia `TUTTE` delle misure) su un Backend vecchio viene salvato ma
  non letto.
- **Dati del cliente**: nessun nome, chiave API, password o percorso reale nei file condivisi;
  usa segnaposto (`<Cliente>`, `<CHIAVE-API-MCP>`, `\\server\condivisione`).
- Per il **DSL dei flussi Workforce** (blocchi, `CodeJs`, validatore) la fonte è la skill
  `thinkai-workforce`; qui ci sono solo le novità di palette/parametri di ottobre. I nomi DSL
  dei blocchi nuovi **non sono nella guida**: verificali nel Workforce Studio.

## Il filo conduttore

Una risposta giusta nasce da **tre scelte giuste**: *di quale argomento parla la domanda*
(contesto), *come sono fatti i dati* (conoscenza, regole, vocabolario), *dove sta la risposta*
(tabella o documento).

```
Domanda → Contesto (Preferenze Viste) → Viste e tabelle (semantica) → Conoscenza → Query SQL → Risposta
```

Se il contesto è sbagliato, anche la conoscenza migliore lavora sulle tabelle sbagliate. Se il
contesto è giusto ma la conoscenza manca, l'AI indovina legami e significato dei codici.

## Indice dei riferimenti (carica solo ciò che serve)

| Tema / sintomo | File |
|---|---|
| Impostazioni Analisi, Configuratore a 4 passi, conoscenza del DB, `[da confermare]`, misure nel testo (`CP2021 540 x 1500`), vocabolario (guance=sponde), pacchetto `.thinkai.json` | `references/conoscenza-database.md` |
| Domande che cambiano contesto da sole, priorità, Preferenze Viste, semantica SQL Server (proprietà estese), Reset della ChatRoom | `references/contesti-e-reset.md` |
| Regole insegnate in chat («impara…», «d'ora in poi…»), segnalibro +, «Regole insegnate» nel Configuratore | `references/regole-insegnate.md` |
| Scheda Documenti: Ricerca / Conversazione / Conversazione + dati | `references/documenti.md` |
| Server MCP FileSystem: HTTP streaming, RAG, OCR, embedding, indici, `appsettings.json`, installazione, problemi | `references/mcp-filesystem.md` |
| Chat web, sessione/licenza, WebProxy, tunnel con chiave derivata | `references/chat-web.md` |
| Workforce Studio: PDF→Markdown, Controlla documento letto, GestionaleSend 1.5.0, step AI (allegati, Ragionamento), OCR/RAG, date, idempotenza | `references/workforce-studio.md` |
| Workforce Console: `THINKAI_WF_*`, log, stati, Rielabora, più agenti | `references/workforce-console.md` |
| NodeLLM: cluster, gateway, nodi, motori, chiavi, tempi | `references/nodellm.md` |
| Cliente nuovo (12 passi), chiavi nuove nei file di configurazione, glossario | `references/cliente-nuovo-e-config.md` |

## Cosa va dove (decisione rapida)

| Informazione | Dove | Vale per |
|---|---|---|
| Legami fra tabelle, significato dei codici, regole di calcolo, testo libero, controlli | **Conoscenza del database** | Tutte le chat/contesti/agenti su quel DB |
| Come leggere i numeri nelle descrizioni; parole equivalenti | **Regole delle misure** e **Vocabolario** | Tutte le chat su quel DB |
| Filtri/istruzioni di una sola chat (es. «escludi le S.p.A.») | **Prompt Azienda** (menu ⋮) | Quella chat |
| Cosa significano i dati di un contesto | **Prompt Chat** della tipologia | Quella tipologia |
| Quando usare un contesto | **Preferenze Viste** | Scelta del contesto |
| Correzioni ricorrenti degli utenti (colonne da mostrare, ordinamenti, filtri) | **Regole insegnate** | DB (tutti o solo l'autore) |

**Un'informazione, un posto solo:** se i legami fra tabelle stanno anche in Prompt Azienda o nei
prompt delle tipologie, dopo aver salvato la conoscenza vanno tolti da lì (due copie divergono).
Per ripulire una tipologia creata prima: riaprila dal Configuratore → **Salva e Applica**.

## Regole d'oro (dalla guida)

1. **Priorità delle Preferenze Viste mai oltre 10**: la soglia di aggancio è 12 e la priorità si
   somma sempre; ≥12 aggancia qualunque domanda di seguito (§ `contesti-e-reset.md`).
2. **Il lato** (clienti/fornitori) scritto uguale in Tipo Analisi, Categoria e nome vista di
   tutti i contesti di quel lato, **non** nella Descrizione.
3. **Date nelle query sempre `'YYYYMMDD'`** (regola di sistema, non va scritta nella conoscenza).
4. **Non saltare il passo 4 del Configuratore** (Output): senza stile/libreria/struttura l'AI
   improvvisa e il risultato cambia a ogni volta.
5. **I legami deboli** (<100%) si usano solo se confermati, con `LEFT JOIN`, mai `INNER JOIN`.
6. **Il vocabolario**: le varianti di un gruppo valgono in OR fra loro; nel dubbio, due gruppi
   separati. Un gruppo sbagliato allarga le ricerche.
7. **Dopo ogni modifica alla conoscenza**: le chat già aperte la vedono entro ~5 minuti; per
   riprovare subito → Reset + nuova scelta del contesto.
8. **Idempotenza per tentativo** negli step Workforce che spostano file o scrivono sul
   gestionale: la `idempotencyKey` contiene l'id del tentativo (`ddt-move-{correlationId}-{logKey}`).
9. **WebProxy e Backend si aggiornano insieme** (chat web), altrimenti la finestra dei contesti
   è vuota per gli utenti normali.
10. **Un aggiornamento del server MCP sovrascrive `appsettings.json`**: salva quello
    dell'installazione e rimetti almeno `AllowedDirectories`, `ClientId`, `IndexDbPath`.

## Collaudo (banco di prova)

Fatevi dare dal cliente 10–20 domande vere con la risposta attesa; ripetetele dopo ogni modifica
importante. Provate con **un utente normale** (Admin/SystemAdmin vedono tutti i contesti).
Per domande con elenco di casi e dubbi lo stile **Standard** mostra tutto; **Rapida** riassume
in 2–3 paragrafi.
