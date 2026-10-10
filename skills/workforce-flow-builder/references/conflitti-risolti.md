# Rettifiche: contraddizioni risolte tra le fonti

> Le due skill di origine sono cresciute in tempi diversi: alcune indicazioni della skill ordini
> sono state smentite dal collaudo DECOX e dal flusso GAZZA. Qui la decisione vincolante per
> ogni conflitto. Gerarchia: **run reale > video corso (SSOT) > manuale > inferenza**.
> Le copie in `erp/` e `prompt-ordini/` sono già state allineate (banner "RETTIFICA").

| ID | Tema | Indicazione superata | Decisione vincolante | Fonte |
|---|---|---|---|---|
| R-01 | Stampa PDF | `pdfPathOutput` ricalcola `lastGestionalePdfPath` e salva il base64 con `FileWrite` | Il gestionale scrive già il PDF: si **cattura** `lastGestionalePdfPath` in `stampaPdfPath` (M12) | DECOX, R11, R12 |
| R-02 | `FileWrite` | Usabile per qualsiasi contenuto | Solo **testo** (BOM UTF-8, nessun binario): log, JSON, heartbeat | DECOX |
| R-03 | Intake mail | `MailRead` batch + `ForEach` sulle mail | Trigger **MailPolling durevole**: una run per mail, `MailDisposition` unico top-level | Corso M3/M15 |
| R-04 | Allegati mail | Salvarli da base64 con "Scrivi file" | Usare i path esposti dal trigger (`lastEmailAttachments`) | R-02 + corso |
| R-05 | Placeholder assente | Diventa stringa vuota | Resta **testo letterale** `{chiave}` | DECOX (mail reale) |
| R-06 | Cleanup | `return { chiave: null }` | `delete stepData[k]` + valori espliciti dove servono | R-05 |
| R-07 | Idempotenza | "Mettila sugli effetti esterni" (incluso FileMove di claim con chiave = nome file) | Solo su **scritture**, chiave parametrizzata; no su letture, test, `FileMove` con `overwrite: true`; attenzione alle chiavi stabili in collaudo | DECOX (3 bug da replay) |
| R-08 | Placeholder in `CodeJs` | `'{cartellaProcessing}\\' + nome` nel template `claimFileClaim` | Dentro `CodeJs` è JS reale: si legge `stepData.cartellaProcessing` | `sintassi-dsl.md` §4 |
| R-09 | Numeri verso TC | Stringhe in formato italiano (`.replace('.', ',')`) | **Numeri JSON** con `JSON.stringify`; mai separatore migliaia | TcRestAPI v1.5.3 |
| R-10 | Numeri verso SQL | Valori nativi nel `set`/`values` | Stringhe convertite in `CodeJs` (`'' + n`, `n.toFixed(k)`, `"1"`/`"0"`) | DECOX |
| R-11 | Endpoint `lookup` | SQL libera via `GestionaleSend` | Deprecato in v1.5.0: ricerche strutturate o blocco `Query` | TcRestAPI |
| R-12 | Errori nel ForEach | `throw` nel ramo else | Branch sul ramo negativo + `itemErrorSteps` configurati **a mano** in Studio | F1/F3, GAZZA, DECOX |
| R-13 | Commenti nel DSL | Documentazione in testa al file | Non sopravvivono al round-trip: documentazione in un `.md` a fianco; nel DSL solo `// @…` | Studio |
| R-14 | `TIPO_CODICE` | Filtro con `COD_CF` cliente | Mai: è un tipo, non il cliente (azzera i match). Per EAN niente `tipoCodice` | F3 Q9, DECOX |
| R-15 | `lastQueryJson`, `lastTargetCrossStatus` | Usate come output | Non a catalogo: usa `lastQueryRows`, `lastGestionaleCodice`, `lastGestionaleEsito`, `lastTargetCrossJson` | B6 |
| R-16 | `String()` / `Number()` in CodeJs | Usati liberamente (anche nella vecchia ricetta stampa PDF) | Non esistono come costruttori nel sandbox: `'' + v` e `+v`; niente `Number.isFinite` | Handoff 10/10, run reali |
| R-17 | `$input` | Snapshot generico in sola lettura | Contiene solo l'output del nodo **immediatamente precedente**: leggi `stepData.x` con fallback `$input.x` | Handoff 10/10 |
| R-18 | `lastQueryRows` | Sempre un array | Può essere oggetto host non Array o stringa: normalizza (M17) | Mustweb run 3650+ |
| R-19 | `credentialName` | Configurabile con `{credentialName}` | Solo stringa **letterale** | Handoff 10/10 |
| R-20 | Date verso TcRestAPI | `AAAA-MM-GG` accettato (doc v1.5.3) | Solo `gg/mm/aaaa`: con ISO il gestionale registrava sempre il giorno 20 | Run reali |
| R-21 | `FileWrite` su `E:\…` | Scrive sul disco del cliente | Scrive nella sandbox interna; un `FileMove` successivo fallisce in silenzio | Run reale |
| R-22 | Creazione documento | Un'unica chiamata `documento`, retry ammesso | Oltre ~24 righe → blocchi `documento-righe`; timeout max 300 s; retry disabilitato (duplicati) | DECOX |
| R-23 | Recovery `itemErrorSteps` | Chiavi di idempotenza con variabili di loop | Recovery attivato solo da un flag di errore reale; chiavi stabili per item | GAZZA run #3918 |

## Come registrare una nuova rettifica
1. Annota run/flusso/data che la prova (es. "DECOX 9/9/2026, step X, messaggio Y").
2. Aggiungi una riga qui con ID progressivo.
3. Correggi la voce nel reference interessato con un banner `⚠️ RETTIFICA` (non cancellare la
   storia: chi legge un flusso vecchio deve capire perché è diverso).
4. Se la regola è verificabile meccanicamente, aggiungi un controllo a `scripts/valida_flusso.py`.
