# Catalogo dei flussi WorkForce raccolti

> Inventario unico di **tutti i flussi noti**: quelli documentati nelle skill di origine
> (`thinkai-workforce`, `workforce-ordini-clienti`) e quelli realizzati nelle conversazioni dal
> 15/09/2026 al 07/10/2026 (handoff del 10/10/2026). Serve a rispondere in 30 secondi alla domanda
> *"da quale flusso parto?"*. Regole specifiche per cliente: `profili-cliente.md`. Dettaglio blocco per
> blocco dei flussi storici: `dsl/esempi.md`. Prompt pronti: `prompt-ordini/`.
>
> ⚠️ Il codice DSL dei flussi dell'handoff **non è incluso**: qui c'è l'indice e la specifica.
> Per lavorare su uno di essi chiedi il file (`.js` / `.thinkaiagent.json`) da mettere in
> `flussi/<cliente>/`. Le voci **[DA VERIFICARE]** non vanno assunte: serve evidenza (CSV di run,
> dump StepData, export Studio).

## 1. Flussi di produzione e collaudo (handoff 10/10/2026)

| ID | Flusso / file | Cliente | Archetipo | Stato | Punti aperti principali |
|---|---|---|---|---|---|
| CLI-A-OC | `CLI-A_Ordine_Cliente_-_v1_5_7A_dsl.js` (+ `.thinkaiagent.json`), 142 step, ~4.047 righe | CLI-A | A1+P | Produzione, validatore 0/0 | Run #3918: 5 falsi errori tecnici (recovery senza errore reale, chiavi idempotenza da variabili di loop; `FileMove` sentinella fuori `allowedRoot`); 3 ForEach da riconfigurare; codice articolo su due righe (cliente finale Y1); cliente finale Y2 righe 2-7 senza codici; readback righe `ORD_CLI_RIGHE` non confermato; lineage versioni [DA VERIFICARE] |
| CLI-B-DDT | `DDT_Fornitore_CLI-B_v1.1.thinkaiagent.json` → base v1.2.1 → "DDT fornitori DEC Blocchi v1.0" → v1.1 con split `CodePython` | CLI-B | A2+P | Collaudo | Split PDF "Nessuna risposta JSON"; timeout AI su PDF 34 pagine; disabilitare retry su `documento`; `TRUNCATE` profilo articoli sporco |
| CLI-B-FATT | `Fattura_Fornitore_CLI-B_v1.0` | CLI-B | A2 (fattura→DDT→ordini) | Sviluppo | Fatture Fornitore X1 XML FatturaPA: scartare notifica SDI `_ZD_001.xml` |
| CLI-A-FV | `Fattura_Fornitore_Verifica_v1.0.js` + note | CLI-A | A8 + M19 | Fermo a Fase 0 (atteso), validatore 0/0 | 5 parametri vuoti: `cfgArticoloConai`, `cfgUmConai`, `cfgArticoliVietati`, `cfgTolleranzaPrezzo`, `cfgEmailOperatore`; colonne `FATT_FOR_*` dedotte |
| CLI-A-MW | Riconciliazione fatture XML PortaleXML (32 step) | CLI-A | A8 | Collaudo (run 3650-3657+) | Codice fornitore in descrizione `ART_ANA` senza `ART_CODICI`: CONFERMATO o PROPOSTO? |
| CLI-A-CC | `flusso_conversione_campioni.js` ("Indici conversione") | CLI-A | A6 (report/dashboard) | Bloccato | `ALTER VIEW` errore 208 su `<DB_ERP>` (sospetta `PBI_PARAMETRI`); `VENDITA_SUCCESSIVA` senza date campione; media giorni troncata; PublishDashboard da verificare |
| CLI-C-AI | Lettura AI mail (Flusso 1 esistente, Flusso 2 sostitutivo) | CLI-C | A3 | Sviluppo | Flusso 2 deve replicare chiavi StepData e step finali del Flusso 1 |
| CLI-C-F5 | `Flusso5_OrdineFornitoreTarget.js` + `NOTE_MANUTENTORI_…md` | CLI-C | A6 (aggiornamento dati) | Pre-collaudo, validatore 0/0 | Suffisso riga `ORD_FOR` in TcRestAPI; colonne reali `ORD_CLI`/`RIGHE_CLI`; tabella `THINKAI_<CLIENTE>_ORDFOR_LOG`; credenziale reale; `continueOnItemError` sui 2 ForEach |
| LEAD | `profilazione-lead-targetcross.js` + note (DDL storico) | Interno / Target Cross | A6 (arricchimento AI) | Validatore 0 errori / 3 avvisi (credenziale) | Scrittura SQL diretta su `CF.NOTE_CF` accettabile? limite 100 lead/run; nota in sostituzione o in testa |
| CLI-D-STAGING | Fatture estere PDF → 4 tabelle staging STAGING (nome file [DA VERIFICARE]) | CLI-D | A9 (staging) | Testato su 12 casi sintetici | Mancano paese, divisa/cambio, ID IVA estero; `STATO = 0`; `TARGET_*`, `HEAD_CONT_ID`; `REVERSE_CHARGE`; aliquota 22% assunta; PDF esteri reali |
| CLI-E | Ciclo passivo: piano 12 agenti FPR-A…FPR-L, 3 ondate | CLI-E | A10 (pipeline EventDb) | Solo piano | Capacità API (prima nota, ritenute, autofattura RC, cespiti) dal produttore dell'ERP; volumi e alert da CLI-E |

### Progetti senza flusso consegnato verificabile
| Progetto | Cosa risulta | Archetipo |
|---|---|---|
| CLI-F — "DDT Fornitori 6 casi" | Flusso collaudato per DDT conto lavoro; richiesto template generalizzato in DSL [DA VERIFICARE] | A2 |
| CLI-D — ordini cliente | Formati eterogenei (tracciato EDI posizionale, Excel da portale, PDF catene GDO, mail) → CSV `;` verso ORD_CLI | A1 multi-formato (solo analisi) |
| Tracking spedizioni | Tracking da `DDT_CLI_SPEC.TRACK`, DHL e GLS, console solleciti [DA VERIFICARE] | A6 + A5 |

## 2. Flussi storici di riferimento (skill di origine)

| ID | Flusso | Archetipo | Maturità | Usalo come base? |
|---|---|---|---|---|
| F3 | Ordini cliente PDF, agente singolo | A1 | ⭐ baseline (bug Q6-Q9) | No: solo per capire F1 |
| F1 | Ordini cliente PDF, multi-agente + rilettura | A1 | ⭐⭐ (bug Q6, Q7, Q3) | Sì, per estrazione multi-agente |
| F2 | DDT fornitore PDF + controllo prezzi | A2 | ⭐⭐ (bug Q3, Q10) | Sì, per riconciliazione e price check |
| F4 | Mail → classifica → estrai → registra | A3 | ⭐ fragile | Solo per lo Switch sugli allegati |
| EX | Fatture PDF minimale corretto | A4 | ⭐⭐ didattico | Sì, scheletro minimo |
| CLI-A v1.4.1 | Ordine cliente enterprise (export JSON) | A1+P | ⭐⭐⭐ | Riferimento architetturale (oggi superato da CLI-A-OC 1.5.7A) |
| T-cart / T-man / T-adv | Prompt ordini cartella / manuale / avanzato | A1 | ⭐⭐–⭐⭐⭐ | Sì, per prompt in linguaggio naturale |
| T-mail | Prompt ordini via email | A3 | ⚠️ superato (R-03, R-04) | No: usa M16 |

## 3. Lezioni trasversali

| Tema | Evidenza | Regola / modulo |
|---|---|---|
| Sandbox CodeJs | Più flussi: `String()`/`Number()` inesistenti, `$input` solo dal nodo precedente | R18, M17 |
| Righe query | PortaleXML: `lastQueryRows` non Array o stringa | M17 |
| Credenziali | Placeholder non interpolato in `GestionaleSend` | R19 |
| Documenti lunghi | CLI-B: timeout oltre ~24 righe; retry su timeout = duplicato | M18, R19 |
| Date ERP | Date ISO registrate sempre al giorno 20; date un giorno indietro per UTC | R13, M17 |
| File | `FileWrite` scrive nella sandbox interna; `FileMove` silenzioso sotto `@continueOnFail` | R12, M15 |
| Idempotenza | CLI-A #3918: chiavi da variabili di loop → recovery spurio | R10 |
| Placeholder | CLI-B: `{codiceDocCreato}` letterale nella mail al cliente | R8 |
| SQL | CLI-B: "conversione da nvarchar a numeric" su più nodi; PortaleXML: collation nelle join, `AZIENDA_ID = 0` condiviso | R9, `profili-cliente.md` |
| Stampa PDF | CLI-B: allegati illeggibili da `FileWrite` | R12, M12 |
| Matching | F3 Q9; CLI-A cascata; CLI-B EAN; PortaleXML `COD_ART` proposto mai fidato | M09 |
| Errori nei cicli | F1/F3 `throw`; CLI-B timeout AI; CLI-A 3 ForEach da riconfigurare | R2, R3, M03 |
| Sola lettura | PortaleXML, Fattura Verifica: SELECT soltanto, verdetto + report | A8 |
| Sviluppo | Flussi da 100+ step: DSL generato da script Python, modifiche chirurgiche | SKILL.md fase 4 |

## 4. Come aggiungere un flusso
Quando ricevi un nuovo flusso (DSL o `.thinkaiagent.json`): aggiungi una riga in §1 (ID, file,
cliente, archetipo, stato, punti aperti), le regole cliente in `profili-cliente.md`, i mattoni nuovi in
`moduli.md`, le smentite in `conflitti-risolti.md`. Un run reale vince sulle fonti documentali.
