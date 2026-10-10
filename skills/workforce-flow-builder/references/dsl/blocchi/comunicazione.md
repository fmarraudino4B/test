# Catalogo blocchi — Comunicazione (Mail + Notifiche)

> Categoria trasversale che raccoglie i blocchi di **lettura posta/messaggi**, di **chiusura della posta durevole** (Mail Disposition) e di **invio/notifica** su email e canali di messaggistica (Slack, Teams, Telegram, WhatsApp), più il blocco di **approvazione umana mid-flow** ("Invia e attendi").
>
> **Tracciabilità:** ogni scheda cita il rif `L####` (riga dell'HTML sorgente del manuale) quando disponibile. I nomi DSL provengono da `references/nomi-blocchi.md` (autorità): tutti i nomi sono `✅ CONFERMATI` — dai flussi esportati o dal video corso (palette moduli 15/16). I nomi dei parametri coincidono col manuale; per **Mail Disposition** (documentato solo dal video corso, modulo 15, senza scheda-manuale nell'estrazione) i nomi provengono dalla narrazione del corso.

## Indice
1. [Mail Read](#mail-read--dsl-mailread--l2905) — DSL `MailRead` ✅ — lettura posta (IMAP/Gmail/Graph)
2. [Mail Disposition](#mail-disposition--dsl-maildisposition--corso-m15) — DSL `MailDisposition` ✅ — chiusura della singola email del trigger IMAP durevole
3. [Telegram Read](#telegram-read--dsl-telegramread--l2967) — DSL `TelegramRead` ✅ — lettura messaggi bot Telegram
4. [Email](#email--dsl-sendemail--l2993) — DSL `SendEmail` ✅ — invio email (HTML + allegati)
5. [Invia e attendi](#invia-e-attendi--dsl-sendandwait--l3021) — DSL `SendAndWait` ✅ — approvazione umana mid-flow
6. [Slack](#slack--dsl-sendslack--l3101) — DSL `SendSlack` ✅ — notifica su Slack (webhook)
7. [Teams](#teams--dsl-sendteams--l3117) — DSL `SendTeams` ✅ — notifica su Microsoft Teams (webhook)
8. [Telegram](#telegram--dsl-sendtelegram--l3137) — DSL `SendTelegram` ✅ — invio messaggio Telegram
9. [WhatsApp](#whatsapp--dsl-sendwhatsapp--l3169) — DSL `SendWhatsApp` ✅ — invio messaggio WhatsApp (Twilio)

---

## Lettura (posta / messaggi in arrivo)

### Mail Read — DSL `MailRead` ✅ CONFERMATO — `L2905`

Nome DSL confermato in flusso esportato (evidenza `F4:3`).

- **Scopo:** Legge la posta (IMAP / Gmail / Microsoft Graph) con deduplica dei messaggi.
- **Quando usarlo:** Usalo per leggere la posta in arrivo da IMAP (server classico host/porta/credenziali), Gmail o Microsoft Graph (OAuth via credenziale salvata), con deduplica. Attiva `trackUid` per il tracking incrementale (a ogni esecuzione legge solo le email nuove) e `unreadOnly` per limitarti ai messaggi non letti. Con `downloadAttachments` salvi gli allegati nel sandbox: su ogni email compare `attachments` `[{fileName, contentType, filePath, sizeBytes}]` e i `filePath` sono pronti per gli step Xlsx Extract / PDF Extract / OCR Image / AI Analysis. Gli output `lastEmails` / `lastEmailsSummary` sono quelli del **blocco** MailRead (lettura batch, array iterabile con ForEach): ⚠️ **non** confonderli con le chiavi del **trigger MailPolling durevole** (`inboundMailId`/`lastEmail`/`lastEmailAttachments`, una run per messaggio) — vedi la nota sotto e `modello-esecuzione.md §1.1`.
- **Parametri (input):**

  | Chiave | Tipo | Obbl. | Default | Note |
  | --- | --- | --- | --- | --- |
  | `mode` | scelta — Imap · Gmail · MicrosoftGraph | — | Imap | Imap = server classico (host/porta/credenziali sotto). Gmail/MicrosoftGraph = OAuth via credenziale salvata. |
  | `credentialName` | credenziale | — | — | Solo per Gmail/MicrosoftGraph: credenziale OAuth salvata (Workforce → Credenziali). |
  | `host` | testo | — | — | Solo mode=Imap. — es. `imap.example.com` |
  | `port` | intero | — | 993 | Solo mode=Imap. |
  | `useSsl` | sì/no | — | true | Solo mode=Imap. |
  | `username` | testo | — | — | Solo mode=Imap. |
  | `password` | testo | — | — | Solo mode=Imap (salvata in chiaro nel ConfigJson). |
  | `folder` | testo | — | INBOX | |
  | `since` | testo | — | — | Da data (ISO). — es. `2026-01-01` |
  | `maxEmails` | intero | — | 50 | Email max. |
  | `unreadOnly` | sì/no | — | true | IMAP: UNSEEN · Gmail: is:unread · Graph: isRead eq false. |
  | `trackUid` | sì/no | — | true | Salva un cursore: alla prossima esecuzione legge solo le email nuove. |
  | `downloadAttachments` | sì/no | — | false | Salva gli allegati nel sandbox ed espone su ogni email `attachments` `[{fileName, contentType, filePath, sizeBytes}]`. I filePath sono pronti per Xlsx/Pdf/Ocr/AiAnalysis. (Gmail/IMAP) |

- **Output (variabili StepData prodotte):**

  | Chiave | Tipo | Descrizione |
  | --- | --- | --- |
  | `lastEmails` | JSON | Email lette (array). |
  | `lastEmailsSummary` | testo | Riepilogo testuale. |

- **⚠️ Avvertenze / vincoli:**
  - `password`: valida solo per mode=Imap ed è salvata **in chiaro** nel ConfigJson.
  - `downloadAttachments`: funzione allegati indicata per Gmail/IMAP.
  - `trackUid` attivo = alle esecuzioni successive legge solo le email nuove (cursore salvato).
- **Riferimenti incrociati:** Xlsx Extract / PDF Extract / OCR Image / AI Analysis (i `filePath` degli allegati sono pronti per questi step quando `downloadAttachments`=true).
- **⚠️ Mail Read (blocco) vs trigger MailPolling durevole (course M3/M15):** `MailRead` è una **lettura batch** che popola `lastEmails`/`lastEmailsSummary` (array) — iterabile con ForEach. Il **trigger MailPolling durevole**, invece, crea **una run per messaggio** e popola chiavi diverse (`inboundMailId`, `inboundMailKey`, `inboundEmlPath`, `lastEmail`, `lastEmailAttachments`): NON si itera con ForEach sulle mail e si chiude con **Mail Disposition** (vedi sotto). Non confondere i due contratti. Il manuale (`L1451`) descrive per MailPolling il contratto semplice `lastEmails`/`lastEmailsSummary`; il **corso ha priorità** e documenta il contratto durevole.

---

### Mail Disposition — DSL `MailDisposition` ✅ CONFERMATO (corso M15)

Nome DSL `MailDisposition` ✅ CONFERMATO dal video corso (modulo 15 «Mail»). ⚠️ Documentato **solo dalla narrazione** del corso (nessuna scheda-manuale né immagine `node-`/`campi-` nell'estrazione): i nomi dei parametri provengono dal corso e vanno confermati in Studio per l'ortografia esatta.

- **Scopo:** Conclude in modo affidabile la **singola email** acquisita dal trigger IMAP durevole (MailPolling): sposta la mail e/o la marca come letta e chiude il journal come `processed` (elaborata) o `review` (da revisionare).
- **Quando usarlo:** Come **ultimo step top-level** di un worker alimentato dal trigger MailPolling durevole. Usa `inboundMailId` creato dal trigger (lascialo al default). ⚠️ Il **validatore richiede esattamente UN Mail Disposition top-level finale** nel worker: **non annidarlo** in un ramo (Branch/Switch/ForEach) e **non usarlo dopo un normale Mail Read** (quello è lettura batch, non il flusso durevole). In produzione prepara le cartelle di destinazione nel **preflight** e lascia `createTargetFolder` disattivo.
- **Parametri (input):**

  | Chiave | Tipo | Obbl. | Default | Note |
  | --- | --- | --- | --- | --- |
  | `inboundMailId` | testo | — | (dal trigger) | ID della mail acquisita dal trigger IMAP durevole. Lascialo al default: lo popola il trigger. |
  | `action` | scelta — moveAndMarkRead · move · markRead | — | moveAndMarkRead | Cosa fare della mail: spostarla, marcarla letta, o entrambe. |
  | `targetFolder` | testo | — | — | Cartella di destinazione per le azioni `move`/`moveAndMarkRead` (es. `Elaborate`). |
  | `createTargetFolder` | sì/no | — | false | In produzione **lascialo disattivo**: prepara le cartelle nel preflight IMAP. |
  | `outcome` | scelta — processed · review | — | processed | `processed` = successo business (chiude il journal come elaborata); `review` = manda il messaggio alla **revisione manuale**. |
  | `externalReference` | testo | — | — | Conserva l'identificativo creato dal sistema esterno (es. codice documento gestionale). |

- **Output (variabili StepData prodotte):**

  | Chiave | Tipo | Descrizione |
  | --- | --- | --- |
  | `lastMailDisposition` | JSON | Descrive l'esito della disposizione (senza esporre segreti). |
  | `lastMailDispositionSucceeded` | sì/no | Esito booleano della disposizione. |

- **⚠️ Avvertenze / vincoli:**
  - Deve esistere **esattamente un** Mail Disposition **top-level finale** nel worker (requisito del validatore).
  - **Non annidarlo** in Branch/Switch/ForEach e **non usarlo dopo un Mail Read** normale.
  - Per le azioni `move`/`moveAndMarkRead` prepara le cartelle nel preflight e tieni `createTargetFolder` disattivo in produzione.
  - `outcome=review` instrada il messaggio alla revisione manuale invece di chiuderlo come elaborato.
- **Riferimenti incrociati:** Trigger MailPolling durevole (produce `inboundMailId` e le chiavi `inbound*`/`lastEmail`/`lastEmailAttachments` — vedi `modello-esecuzione.md §1`); Mail Read (lettura batch, contratto diverso `lastEmails`); Monitoraggio → «Posta in ingresso durevole» (corso M7).

---

### Telegram Read — DSL `TelegramRead` ✅ CONFERMATO (corso M15) — `L2967`

Nome DSL `TelegramRead` ✅ CONFERMATO dal video corso (modulo 15 «Mail», `node-TelegramRead`).

- **Scopo:** Riceve i messaggi del bot Telegram (`getUpdates`, polling) con deduplica via offset.
- **Quando usarlo:** Usalo in un agente **schedulato** per ricevere i messaggi del bot Telegram tramite `getUpdates` (polling), con deduplica via offset. Richiede una credenziale HTTP col token del bot (la stessa usata dal blocco di invio Telegram). Attiva `trackOffset` per confermare gli update letti e leggere solo i nuovi alla prossima esecuzione; `onlyText` per limitarti ai messaggi di testo.
- **Parametri (input):**

  | Chiave | Tipo | Obbl. | Default | Note |
  | --- | --- | --- | --- | --- |
  | `botCredentialName` | credenziale | Sì | — | Credenziale HTTP col token del bot (stessa del blocco di invio Telegram). |
  | `maxMessages` | intero | — | 50 | Messaggi max. |
  | `trackOffset` | sì/no | — | true | Conferma gli update letti: alla prossima esecuzione legge solo i nuovi. |
  | `onlyText` | sì/no | — | false | Solo messaggi di testo. |

- **Output (variabili StepData prodotte):**

  | Chiave | Tipo | Descrizione |
  | --- | --- | --- |
  | `lastTelegramMessages` | JSON | Messaggi ricevuti (array: from / chatId / text / date / messageId). |
  | `lastTelegramMessagesSummary` | testo | Riepilogo testuale. |

- **⚠️ Avvertenze / vincoli:**
  - Pensato per un agente **schedulato** (dalla descrizione del blocco).
  - `trackOffset` attivo = deduplica via offset; alla prossima esecuzione legge solo i nuovi update.
- **Riferimenti incrociati:** Telegram (invio, DSL `SendTelegram`) — la credenziale HTTP col token del bot è la stessa.

---

## Invio / Notifiche

### Email — DSL `SendEmail` ✅ CONFERMATO — `L2993`

Nome DSL confermato in flusso esportato (evidenza `F1:711`). Scostamento dall'euristica: verbo "Send" anteposto al display "Email".

- **Scopo:** Invia un'email (HTML + allegati).
- **Quando usarlo:** Quando serve recapitare un'email (HTML / markdown / plain) con eventuali allegati, es. inviare un report `{lastAiOutput}` con oggetto `{agentName}`. Campi obbligatori: `to`, `subject`, `body`.
- **Parametri (input):**

  | Chiave | Tipo | Obbl. | Default | Note |
  | --- | --- | --- | --- | --- |
  | `to` | JSON | Sì | — | Array di indirizzi. — es. `["a@b.it"]` |
  | `cc` | JSON | — | — | ✅ CONFERMATO (flusso GAZZA v1.4.1, esportato). Array di indirizzi in copia conoscenza. — es. `["{operatorEmailCc}"]` |
  | `subject` | testo | Sì | — | Oggetto dell'email. Supporta {placeholder}. — es. `Report {agentName}` |
  | `body` | testo lungo | Sì | — | Supporta {placeholder}. — es. `{lastAiOutput}` |
  | `bodyFormat` | scelta — html · markdown · plain | — | html | |
  | `attachments` | JSON | — | — | Array di path file. — es. `["reports/foo.pdf"]` |
  | `smtpConfigId` | testo | — | — | Vuoto = SMTP predefinito (override del proprietario o default). Seleziona una configurazione SMTP specifica per questo invio. |
  | `idempotencyKey` / `idempotencyGroup` / `idempotencyRetryOnFailure` | testo / testo / sì-no | — | — | ✅ CONFERMATO (GAZZA). Vedi `pattern.md` §A8 — evita l'invio doppio della stessa notifica su retry. Chiave da un identificativo business stabile (es. `"gazza-email-technical-{fileCorrelationId}"`). |

- **Output (variabili StepData prodotte):** nessuno (il blocco non produce chiavi StepData).
- **Riferimenti incrociati:** `{agentName}`; `{lastAiOutput}`; Markdown (per convertire il corpo prima dell'invio con `direction=mdToHtml`); `pattern.md` §A8 (idempotenza).

---

### Invia e attendi — DSL `SendAndWait` ✅ CONFERMATO (corso M16) — `L3021`

Nome DSL `SendAndWait` ✅ CONFERMATO dal video corso (modulo 16 «Notifiche», `node-SendAndWait`).

- **Scopo:** Invia un messaggio col link di risposta (email / Slack / Teams / Telegram / WhatsApp) e mette la run in **pausa** finché il destinatario non sceglie dalla pagina (es. Approva/Rifiuta). Al resume: `resumeChoice` / `resumePayload` pilotano il Branch a valle.
- **Quando usarlo:** Quando serve un'approvazione/decisione umana **mid-flow** su un canale (email / Slack / Teams / Telegram / WhatsApp): il blocco invia un messaggio con link di risposta, sospende la run e la riprende con la scelta del destinatario per pilotare un Branch su `$.resumeChoice`.
- **Parametri (input):**

  | Chiave | Tipo | Obbl. | Default | Note |
  | --- | --- | --- | --- | --- |
  | `channel` | scelta — email · slack · teams · telegram · whatsapp | Sì | — | |
  | `message` | testo lungo | Sì | — | Supporta {placeholder}. Il link di risposta viene aggiunto in coda automaticamente. — es. `Confermi l'ordine {lastQueryRows[0].numero}?` |
  | `choices` | testo | — | Approva, Rifiuta | Scelte CSV = bottoni della pagina di risposta (max 6). La scelta arriva in `resumeChoice` → Branch su `$.resumeChoice`. |
  | `allowNote` | sì/no | — | true | Mostra un campo nota libero nella pagina (arriva in `resumePayload.note`). |
  | `timeoutMinutes` | intero | — | 10080 | Scadenza dell'attesa (default 7 giorni, max 30). |
  | `onTimeout` | scelta — fail · continueWithDefault | — | fail | fail = run fallita; continueWithDefault = riprende con `resumePayload.timedOut=true` (decidi col Branch). |
  | `responseKey` | testo | — | resumePayload | Chiave StepData in cui raccogliere la risposta. |
  | `formFields` | JSON | — | — | Opzionale: la pagina di risposta raccoglie questi campi in `resumePayload` (type: text/textarea/number/email/date/select). I `required` bloccano il submit. — es. `[{"name":"budget","label":"Budget approvato","type":"number","required":true},{"name":"priorita","label":"Priorità","type":"select","options":["Alta","Bassa"]}]` |
  | `to` | testo | — | — | Email: indirizzi CSV. WhatsApp: numero (`whatsapp:+39...`). — es. `capo@azienda.it` |
  | `subject` | testo | — | — | Oggetto (email). Vuoto = "Richiesta di conferma - <nome agente>". |
  | `smtpConfigId` | testo | — | — | Configurazione SMTP (email). Vuoto = SMTP predefinito. |
  | `webhookCredentialName` | credenziale | — | — | Credenziale webhook (slack/teams). |
  | `botCredentialName` | credenziale | — | — | Credenziale bot (telegram). |
  | `chatId` | testo | — | — | Chat ID (telegram). — es. `-100123456 o @canale` |
  | `credentialName` | credenziale | — | — | Credenziale Twilio (whatsapp). |
  | `from` | testo | — | — | Da (whatsapp). — es. `whatsapp:+14155238886` |

- **Output (variabili StepData prodotte):**

  | Chiave | Tipo | Descrizione |
  | --- | --- | --- |
  | `lastWaitResumeUrl` | testo | URL pubblico di risposta (incluso nel messaggio inviato). |
  | `lastWaitKey` | testo | WaitKey monouso della pausa. |
  | `resumeChoice` | testo | Scelta del destinatario (uno dei `choices`) — Branch su `$.resumeChoice`. |
  | `resumePayload` | JSON | Risposta completa (note/campi; `{timedOut:true}` se scaduto con continueWithDefault). |
  | `resumedAt` | testo | Timestamp ISO della ripresa. |

- **⚠️ Avvertenze / vincoli:**
  - Mette la run in **pausa** finché il destinatario non risponde dalla pagina (`L3021`).
  - `timeoutMinutes`: default 7 giorni, max 30 (`L3022`).
  - `onTimeout=fail` interrompe la run alla scadenza; `continueWithDefault` riprende con `resumePayload.timedOut=true` da valutare col Branch (`L3022`).
  - `choices`: massimo 6 bottoni nella pagina di risposta (`L3022`).
  - `formFields`: i campi con `required=true` bloccano il submit della pagina (`L3022`).
  - Il link di risposta viene aggiunto in coda al messaggio **automaticamente** (`L3022`).
- **Riferimenti incrociati:** `{lastQueryRows[0].numero}`; `resumeChoice`; `resumePayload`; `$.resumeChoice`; Branch (a valle, per instradare in base alla scelta).

---

### Slack — DSL `SendSlack` ✅ CONFERMATO (corso M16) — `L3101`

Nome DSL `SendSlack` ✅ CONFERMATO dal video corso (modulo 16 «Notifiche», `node-SendSlack`).

- **Scopo:** Pubblica un messaggio su Slack via Incoming Webhook.
- **Quando usarlo:** Quando serve pubblicare una notifica testuale su un canale Slack tramite Incoming Webhook, es. l'output `{lastAiOutput}`. Richiede la credenziale webhook e il testo.
- **Parametri (input):**

  | Chiave | Tipo | Obbl. | Default | Note |
  | --- | --- | --- | --- | --- |
  | `webhookCredentialName` | credenziale | Sì | — | |
  | `text` | testo lungo | Sì | — | Testo del messaggio. Supporta {placeholder}. — es. `{lastAiOutput}` |

- **Output (variabili StepData prodotte):**

  | Chiave | Tipo | Descrizione |
  | --- | --- | --- |
  | `lastSlackResponse` | testo | Risposta Slack. |

- **Riferimenti incrociati:** `{lastAiOutput}`; Markdown (`direction=htmlToSlack` per convertire in Slack mrkdwn prima dell'invio).

---

### Teams — DSL `SendTeams` ✅ CONFERMATO (corso M16) — `L3117`

Nome DSL `SendTeams` ✅ CONFERMATO dal video corso (modulo 16 «Notifiche», `node-SendTeams`).

- **Scopo:** Pubblica un messaggio su Microsoft Teams via Incoming Webhook.
- **Quando usarlo:** Quando serve pubblicare una notifica (con titolo opzionale) su Microsoft Teams tramite Incoming Webhook, es. l'output `{lastAiOutput}`. Richiede la credenziale webhook e il testo.
- **Parametri (input):**

  | Chiave | Tipo | Obbl. | Default | Note |
  | --- | --- | --- | --- | --- |
  | `webhookCredentialName` | credenziale | Sì | — | |
  | `title` | testo | — | — | Titolo (opzionale). |
  | `text` | testo lungo | Sì | — | Testo del messaggio. Supporta {placeholder}. — es. `{lastAiOutput}` |

- **Output (variabili StepData prodotte):**

  | Chiave | Tipo | Descrizione |
  | --- | --- | --- |
  | `lastTeamsResponse` | testo | Risposta Teams. |

- **Riferimenti incrociati:** `{lastAiOutput}`.

---

### Telegram — DSL `SendTelegram` ✅ CONFERMATO (corso M16) — `L3137`

Nome DSL `SendTelegram` ✅ CONFERMATO dal video corso (modulo 16 «Notifiche», `node-SendTelegram`). Coerente col manuale, che cita "SendTelegram" nelle descrizioni di Telegram Read e Markdown (`htmlToTelegram`).

- **Scopo:** Invia un messaggio Telegram.
- **Quando usarlo:** Quando serve inviare (o modificare in-place via `editMessageId`) un messaggio Telegram, con eventuale allegato o `parseMode` Markdown/HTML, es. l'output `{lastAiOutput}`. Richiede credenziale bot e `chatId`.
- **Parametri (input):**

  | Chiave | Tipo | Obbl. | Default | Note |
  | --- | --- | --- | --- | --- |
  | `botCredentialName` | credenziale | Sì | — | |
  | `chatId` | testo | Sì | — | — es. `-100123456 o @canale` |
  | `text` | testo lungo | Sì | — | Testo del messaggio. Supporta {placeholder}. — es. `{lastAiOutput}` |
  | `parseMode` | scelta — Markdown · HTML | — | — | |
  | `attachmentPath` | testo | — | — | Path relativo a `Workforce:FileBaseDir`; inviato come documento/foto. — es. `reports/report.pdf` |
  | `editMessageId` | testo | — | — | Se valorizzato modifica quel messaggio (`editMessageText`) invece di inviarne uno nuovo. Pattern placeholder ⏳ → risposta in-place. — es. `{lastTelegramMessageId}` |

- **Output (variabili StepData prodotte):**

  | Chiave | Tipo | Descrizione |
  | --- | --- | --- |
  | `lastTelegramMessageId` | testo | ID messaggio Telegram. |

- **Riferimenti incrociati:** `{lastAiOutput}`; `{lastTelegramMessageId}` (per l'edit in-place); Telegram Read (stessa credenziale bot); Markdown (`direction=htmlToTelegram`, richiede `parseMode=HTML`).

---

### WhatsApp — DSL `SendWhatsApp` ✅ CONFERMATO (corso M16) — `L3169`

Nome DSL `SendWhatsApp` ✅ CONFERMATO dal video corso (modulo 16 «Notifiche», `node-SendWhatsApp`).

- **Scopo:** Invia un messaggio WhatsApp (via Twilio).
- **Quando usarlo:** Quando serve inviare un messaggio WhatsApp via Twilio: in **free-form** (dentro la finestra 24h) o con **template pre-approvato** (`contentSid` + `contentVariables`), con eventuale media. Richiede credenziale Twilio, `from` e `to`.
- **Parametri (input):**

  | Chiave | Tipo | Obbl. | Default | Note |
  | --- | --- | --- | --- | --- |
  | `credentialName` | credenziale | Sì | — | Credenziale Twilio. |
  | `from` | testo | Sì | — | — es. `whatsapp:+14155238886` |
  | `to` | testo | Sì | — | — es. `whatsapp:+39...` |
  | `body` | testo lungo | — | — | Corpo (free-form). Richiede finestra 24h. |
  | `contentSid` | testo | — | — | Content SID: template pre-approvato. |
  | `contentVariables` | JSON | — | — | Variabili template. — es. `{"1":"val"}` |
  | `mediaPath` | testo | — | — | Path relativo a `Workforce:FileBaseDir`; pubblicato e passato a Twilio come MediaUrl. — es. `reports/foto.jpg` |
  | `mediaTtlMinutes` | intero | — | 10 | Validità del link media (max 60). |

- **Output (variabili StepData prodotte):**

  | Chiave | Tipo | Descrizione |
  | --- | --- | --- |
  | `lastTwilioMessageSid` | testo | SID messaggio Twilio. |

- **⚠️ Avvertenze / vincoli:**
  - `body` (free-form) richiede la **finestra 24h** di WhatsApp (`L3170`).
  - `mediaTtlMinutes`: validità del link media max 60 minuti (`L3170`).
- **Riferimenti incrociati:** Invia e attendi (canale `whatsapp`, usa la stessa credenziale Twilio e i campi `from`/`to`).
