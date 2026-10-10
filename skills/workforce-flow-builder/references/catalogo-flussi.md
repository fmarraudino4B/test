# Catalogo dei flussi WorkForce raccolti

> Inventario unico di **tutti i flussi** noti alle skill `thinkai-workforce` e
> `workforce-ordini-clienti`, classificati per archetipo, maturità e riusabilità. Serve a
> rispondere in 30 secondi alla domanda: *"da quale flusso parto?"*.
> Dettaglio blocco per blocco: `dsl/esempi.md`. Prompt pronti: `prompt-ordini/`.

## Matrice riassuntiva

| ID | Flusso | Archetipo | Ingresso | ERP / output | Maturità | Usalo come base? |
|---|---|---|---|---|---|---|
| F3 | Ordini cliente PDF, agente singolo | A1 | FileList cartella | `ORD_CLI` + email | ⭐ baseline (bug Q6, Q7, Q8, Q9) | No: solo per capire il "perché" di F1 |
| F1 | Ordini cliente PDF, multi-agente + rilettura | A1 | FileList cartella | `ORD_CLI` + PDF + email | ⭐⭐ hardened (bug Q6, Q7, Q3) | Sì, per estrazione multi-agente e validazione numerica |
| F2 | DDT fornitore PDF + controllo prezzi | A2 | FileList cartella | `DDT_FOR` + email + archivio | ⭐⭐ (bug Q3, Q10, FileMove annidato) | Sì, per riconciliazione ordine e price check |
| F4 | Mail → classifica → estrai → registra → risponde | A3 | `MailRead` batch | `ORD_CLI` + risposta cliente | ⭐ fragile (Q1, Q2, Q4, Q5, report→Branch) | Solo per Switch per tipo allegato |
| EX | Fatture PDF minimale corretto | A4 | FileList | email ok/anomalia | ⭐⭐ didattico pulito | Sì, come scheletro minimo |
| GAZZA | Ordine Cliente v1.4.x enterprise | A1+ | Schedule `*/30` + FileList | `ORD_CLI` + audit + auto-learning | ⭐⭐⭐ produzione | **Sì: riferimento architetturale** |
| DECOX | Collaudo DDT fornitore (set. 2026) | A2+ | cartella + processing | documento ERP + log SQL + email | ⭐⭐⭐ oltre 40 bug reali corretti | **Sì: fonte delle Regole d'oro R8-R12** |
| T-cart | Prompt ordini: trigger cartella | A1 | FilePolling | `ORD_CLI` | ⭐⭐ validato | Sì, per prompt in linguaggio naturale |
| T-mail | Prompt ordini: trigger email | A3 | `MailRead` + FileWrite | `ORD_CLI` | ⚠️ superato (vedi R-03, R-04) | No: usa MailPolling durevole (M16) |
| T-man | Prompt ordini: manuale/schedulato | A1 | Manual/Schedule + FileList | `ORD_CLI` + NON_ELAB | ⭐⭐ | Sì |
| T-adv | Prompt ordini: avanzato | A1+ | Schedule + FileList | come GAZZA | ⭐⭐⭐ | Sì, per clienti ad alto volume/compliance |

Archetipi: vedi `archetipi.md`. Rettifiche R-xx: vedi `conflitti-risolti.md`.

## Lezioni trasversali (cosa hanno insegnato tutti insieme)

| Tema | Evidenza | Regola risultante |
|---|---|---|
| Estrazione AI | F3 → F1: un prompt unico sbaglia di più di tre agenti mirati | Multi-agente + checksum deterministico per documenti con molte righe |
| Output AI e logica | F4: `report` dentro un Branch | `json`/`text` sempre (R1) |
| Errori nei cicli | F1/F3: `throw` nel ciclo; DECOX: timeout AI ferma la coda | Branch sul ramo negativo + pannello Gestione errori del ForEach (M03) |
| Stato tra iterazioni | F1 cleanup; DECOX: PDF dell'item precedente allegato | Cleanup di TUTTE le chiavi del giro, incluse le `last*` (M04) |
| Email | F1/F3 Q7 vs F2 corretto | Usa le chiavi arricchite e convertite (M13) |
| Placeholder | DECOX: mail al cliente con `{codiceDocCreato}` letterale | Chiave non scritta = testo letterale (R8) |
| SQL | DECOX: "conversione da nvarchar a numeric" su più nodi | Stringhe esplicite per numeri/booleani; ricontrolla tutti i nodi (R9) |
| Idempotenza | GAZZA conferma i parametri; DECOX: 3 bug da replay | Solo sulle scritture, chiave parametrizzata, mai su letture (R10) |
| Stampa PDF | DECOX: giorni di allegati illeggibili da `FileWrite` | Usa `lastGestionalePdfPath` (R11, R12, M12) |
| Duplicati | gotcha 9, 13; GAZZA claim | Pre-check + `idempotencyKey` business + claim file (M05, M11) |
| Matching | F3 Q9; GAZZA cascata; DECOX EAN | Cascata deterministica, AI solo sui candidati (M09) |
| Anagrafiche | DECOX: P.IVA nel piè di pagina, `VAT NO.` | Prompt mirato + fallback ragione sociale (M06, M08) |
| Robustezza run | DECOX: file orfani in `processing` | Recupero orfani prima del FileList (M02) |
| Produzione | GAZZA preflight | Fail-closed: config → ERP → schema (M01) |

## Flussi non ancora in catalogo
Se l'utente cita un flusso esportato che non compare qui (DSL o JSON `.thinkaiagent.json`),
chiedi il file e aggiungilo a questa tabella: ID, archetipo, ingresso, output, maturità,
bug osservati, pattern buoni. Un flusso nuovo collaudato diventa una fonte: se contraddice una
voce documentale **vince il run reale**, e la rettifica va registrata in `conflitti-risolti.md`.
