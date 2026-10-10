# Dizionario dei parametri cliente

> **Regola:** nei flussi, nei prompt e nei reference **non compare mai un dato reale del cliente**.
> Ogni valore che cambia da cliente a cliente è un parametro di questo dizionario e si compila in
> uno solo dei tre punti indicati in colonna **Dove**. Il profilo completo del cliente si scrive in
> `assets/profilo-cliente.template.json` (copia privata, fuori dal repository), e da lì si
> generano i valori di M00. Gli esempi sono **fittizi**.
>
> Tre forme dello stesso parametro:
> - `chiave` = chiave StepData scritta da M00 (`SetFields`) e letta con `{chiave}` / `stepData.chiave`;
> - `<SEGNAPOSTO>` = da sostituire nel file DSL **prima dell'import** (valori che il motore non
>   interpola: credenziale, risorsa, nomi tabella);
> - `{{SEGNAPOSTO}}` = da sostituire nei prompt in linguaggio naturale (`prompt-ordini/`).

## 1. Identità e ambiente
| Parametro | Chiave M00 | DSL | Prompt | Dove | Esempio fittizio |
|---|---|---|---|---|---|
| Nome agente/versione | `agentVersion` | `<NOME_AGENTE>` | `{{NOME_AGENTE}}` | M00 | `ORDCLI-V1` |
| Ragione sociale propria | `ownName` | — | `{{NOME_AZIENDA_FORNITORE}}` | M00 | `Azienda Esempio s.r.l.` |
| P.IVA propria (da escludere in estrazione) | `ownVat` | `<PIVA_PROPRIA>` | `{{PIVA_FORNITORE}}` | M00 | `01234567890` |
| Credenziale ERP | — | `<CREDENZIALE_ERP>` | `credentialName` | **letterale in ogni `GestionaleSend`** (R19) | `tc-produzione` |
| Database ERP | — | `<DB_ERP>` | — | connessione dati / `dataConnectionId` | `ERP_DB` |
| Prefisso tabelle custom | — | `THINKAI_<CLIENTE>_` | `{{PREFISSO_TABELLE}}` | DSL + DDL | `THINKAI_CLIENTE_` |
| Credenziale IMAP | — | — | `{{CREDENTIAL_EMAIL}}` | trigger MailPolling in Studio | `imap-ordini` |

## 2. Cartelle
| Parametro | Chiave M00 | DSL | Prompt | Esempio fittizio |
|---|---|---|---|---|
| Radice di lavoro (`allowedRoot`) | `workRoot` | `<WORK_ROOT>` | `{{CARTELLA_ROOT}}` | `D:\WorkForce\Agente` |
| Ingresso | `inputDirectory`, `workRootIngresso` | `<CARTELLA_INPUT>` | `{{CARTELLA_INPUT}}` | `<WORK_ROOT>\in` |
| In lavorazione | `processingDirectory` | — | `{{CARTELLA_PROCESSING}}` | `<WORK_ROOT>\processing` |
| Elaborati | `cartellaElaborato` | — | `{{CARTELLA_ELABORATO}}` | `<WORK_ROOT>\ELABORATO` |
| Revisione | `cartellaReview` | — | `{{CARTELLA_REVIEW}}` | `<WORK_ROOT>\REVIEW` |
| Errore (tecnico / ERP) | `cartellaErrore` | — | `{{CARTELLA_ERRORE}}`, `{{CARTELLA_NON_ELAB}}` | `<WORK_ROOT>\ERRORE` |

Tutte le cartelle devono stare sotto `workRoot`, altrimenti `FileMove` le rifiuta e lo step fallisce
in silenzio sotto `@continueOnFail` (run reale).

## 3. Notifiche
| Parametro | Chiave M00 | Prompt | Esempio fittizio |
|---|---|---|---|
| Operatore / destinatario esiti | `operatorEmail` (DSL: `<EMAIL_OPERATORE>`) | `{{EMAIL_OPERATORE}}`, `{{EMAIL_NOTIFICA}}` | `ufficio@example.com` |
| Copia conoscenza | `operatorEmailCc` | `{{EMAIL_CC}}` | `responsabile@example.com` |

## 4. Documento ERP
| Parametro | Chiave M00 | DSL | Prompt | Esempio fittizio |
|---|---|---|---|---|
| Tipo documento (risorsa) | — | `<TIPO_DOC>` / `<ORD_CLI>` | — | `ORD_CLI`, `DDT_FOR` |
| Causale | `defaultCausale` | — | `{{CAUSALE_DOC}}` | `OC01` |
| Serie | `defaultSerie` | — | `{{SERIE_DOC}}` | `A` |
| Deposito | `defaultDeposito` | — | `{{DEPOSITO}}` | `01` |
| Causale campione (report) | `causaleCampione` | `<CAUSALE_CAMPIONE>` | — | `CMP1` |
| Righe per blocco (M18) | `righePerBlocco` | — | — | `24` |

## 5. Regole di business (soglie)
| Parametro | Chiave M00 | Prompt | Default |
|---|---|---|---|
| % minima righe risolte per creare | `minPercentualeRisoltePerCreare` | `{{SOGLIA_PERCENTUALE}}` | `60` |
| Tolleranza prezzo per riga | `tolleranzaRiga` | — | `0.01` |
| Tolleranza totali | `tolleranzaTotali` | — | `0.02` |
| Finestra ricerca DDT (giorni) | `finestraDdtGiorni` | — | `90` |
| Massimo elementi per run | `maxPerRun` | — | `50` |
| Intervallo schedulazione (min) | — | `{{INTERVALLO_MINUTI}}` | `30` |

Le opzioni di comportamento (UM, multi-anagrafica, prezzi, revisione…) sono in
`profili-cliente.md`.

## Come si usa
1. Copia `assets/profilo-cliente.template.json` in una cartella privata come
   `profilo-<cliente>.privato.json` e compilalo.
2. Genera M00 con i valori di §1-§5 e sostituisci i `<SEGNAPOSTO>` del DSL (credenziale,
   risorsa, prefisso tabelle) nella copia privata del flusso.
3. Nei file versionati o condivisi restano **solo segnaposto**: verifica con
   `python scripts/anonimizza.py verifica <cartella>` prima di ogni commit o invio.
