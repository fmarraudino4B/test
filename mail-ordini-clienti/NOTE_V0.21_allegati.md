# DEC Ordini Clienti da mail — V0.21 (allegati testuali + avviso allegati non letti)

Derivata da V0.20 (export JSON). Il DSL completo contiene dati del cliente (P.IVA, email) e sta in `*.privato.dsl.js` (non versionato);
il frammento qui accanto è generico.

## Cosa cambia (5 step su 33; gli altri 28 sono identici a V0.20)
| Step | Modifica |
|---|---|
| CONFIGURAZIONE | `agentVersion` → V0.21.0; nuovo `allegatiNonLettiInRevisione` (`false`) |
| Inizializza chiavi di giro | azzera le chiavi nuove a ogni mail (R5) |
| Seleziona allegati utili | PDF/immagini come prima; **txt/csv → FileRead, doc/docx/odt/rtf → WordExtract, xls/xlsx/xlsm/ods → XlsxExtract** (max 10 file); separa gli allegati davvero non leggibili da loghi/firme/`.p7s`/`.vcf`/`.ics`/`ATT0000x.htm` |
| **Nuovi**: Espone allegati testuali · ForEach "Leggi allegati testuali" · Componi testo degli allegati | per ogni file azzera i `last*`, legge, accoda il testo (max 20.000 caratteri a file, 60.000 totali; Excel: tutti i fogli, max 400 righe a file, colonne separate da ` | `) |
| Componi prompt di estrazione | se c'è testo, aggiunge il blocco `ALLEGATI TESTUALI` (contenuto non attendibile) e una regola |
| Componi email di esito | avviso **rosso** "ALLEGATI NON LETTI", prefisso `[ALLEGATI NON LETTI]` nell'oggetto; con `allegatiNonLettiInRevisione = true` la mail va in Revisione anche se l'ordine è creato |

## Formati
Letti: pdf, immagini (png, jpg, gif, tif, webp, bmp), txt, csv, word (doc, docx, odt, rtf), excel (xls, xlsx, xlsm, ods).
Non letti e segnalati: tutto il resto (zip, heic, xml, p7m, winmail.dat…). Un file letto ma senza testo (vuoto, scansione in Word, foglio vuoto) è segnalato "nessun testo estratto".

## Verificato vs testato
- **Testato** (simulatore dei passi reali con blocchi di lettura simulati, mail `.eml` reale): modalità solo testo, PDF + xlsx + txt + docx + csv illeggibile + zip + firma + logo, prompt con e senza allegati testuali, avvisi. Validatore skill: 0 errori / 0 avvisi; `test_codejs`: 0 errori.
- **Non verificato**: i blocchi `FileRead`/`WordExtract`/`XlsxExtract` su file reali (in particolare che accettino il `filePath` degli allegati della mail), l'estrazione AI sul testo degli allegati, e l'import in Studio.

## Limiti / attenzione
- Word con solo immagini e Excel con celle unite o intestazioni non sulla riga 1 danno testo povero (intestazione = prima riga).
- Il testo degli allegati entra nel prompt: è trattato come contenuto non attendibile (come il corpo della mail).

---

# V0.21.1 — cliente cercato anche per e-mail esatta

**Problema (mail di esito del 20/10).** Una mail inoltrata da `arredamentisettimocielo@gmail.com` è finita in Revisione con "Cliente TargetCross non risolto",
anche se il cliente (009458) ha quella stessa e-mail in anagrafica. Il flusso cercava l'e-mail solo per **dominio** (`E_MAIL_CF LIKE '%dominio%'`) e il dominio
veniva escluso se generico (gmail.com, libero.it, …): un cliente con e-mail personale non era mai trovabile per e-mail.

**Fix.** Nuova ricerca "Cerca/Valuta cliente per e-mail esatta" nella cascata, dopo alias e P.IVA e **prima** del dominio, valida per qualsiasi dominio:
`CF.E_MAIL_CF LIKE '%<indirizzo>%'`, poi verifica che l'indirizzo sia **uno degli indirizzi** del campo (separatori `;`, `,`, spazio; maiuscole indifferenti).
- Una sola anagrafica → `trovato`, metodo `EMAIL` (compare nella mail di esito).
- Più anagrafiche con lo stesso indirizzo → `ambiguo`: sceglie l'AI solo tra i candidati (come per gli altri metodi), altrimenti revisione.
- Se il documento riporta una P.IVA diversa da quella dell'anagrafica → `ambiguo` (non si risolve in automatico), con il motivo nella mail.
- Una semplice somiglianza (`xmail@…` contenuto in `mail@…`) non conta.
- Il metodo `EMAIL` non viene memorizzato in `THINKAI_DECOX_MAIL_CLIENTI` (l'anagrafica basta); `autoApprendiMetodi` resta `PIVA`.

**Provato** (simulatore dei passi reali, risposte TargetCross simulate): e-mail presente → trovato 009458; stessa e-mail con P.IVA diversa → ambiguo; due anagrafiche → ambiguo;
sola sottostringa → non trovato; più indirizzi nel campo e maiuscole → trovato. Sulla V0.20 lo stesso caso restituisce "non risolto", come nella mail di esito.
**Non verificato**: il filtro su `E_MAIL_CF` contro TargetCross reale (stesso campo già usato dalla ricerca per dominio). `agentVersion` → `V0.21.1`.

---

# V0.21.2 — correzioni dai test del 20-21/10

## 1. Ordini "GIA' ELABORATA" ma assenti in TargetCross
- **Refuso:** `modalitaTest` era configurato `True` (maiuscola) e il codice confrontava con `"true"`: la modalità test **non era mai attiva**. In modalità test la chiave del
  journal di idempotenza (`ordcli-mail-create-<chiave>`) è diversa a ogni run; senza, una mail rimandata con lo stesso contenuto veniva "riprodotta" dal journal
  (step verde ma **non eseguito**) anche se l'ordine di prova era stato cancellato in TargetCross o la creazione precedente era finita in errore.
- **Fix:** confronto senza distinzione maiuscole/minuscole; in modalità test anche il **tag** `TK-…` (usato dal controllo duplicati) cambia a ogni run (prima restava uguale,
  perché derivava dai primi caratteri della sola chiave di business). ⚠️ Ora la modalità test è davvero **attiva**: ogni rinvio crea un nuovo ordine. In produzione impostare `modalitaTest = false`.
- **Nuovo esito `JOURNAL_SENZA_DOCUMENTO`:** se il journal dice "già creato" ma in TargetCross non esiste alcun documento col tag, l'esito non è più "già elaborata"
  (mail archiviata in Elaborate): diventa "DA VERIFICARE" (mail in Revisione) con la spiegazione.

## 2. Righe SPNOTE con sconto
Il flusso **non invia sconti** sulle righe segnaposto: il payload aveva solo `COD_ART`, quantità, `FLAG_CALC_PRZ: 1` e descrizione. Quindi gli sconti (50 + 10 nello screenshot) sono
calcolati da TargetCross (condizioni cliente / listino dell'articolo SPNOTE) perché `FLAG_CALC_PRZ = 1` chiede il ricalcolo. Ora le righe segnaposto partono con
`FLAG_CALC_PRZ: 0` e `SCONTO_1..3: 0`. ⚠️ Da verificare sul prossimo ordine; se gli sconti ricompaiono vengono dall'anagrafica di SPNOTE.

## 3. "NON E' UN ORDINE" su mail inoltrata come allegato (Lombardelli)
Il testo letto era solo l'intestazione dell'inoltro (215 caratteri): l'ordine vero stava nell'allegato `Parte allegato al messaggio.tmp` (messaggio inoltrato "come allegato"), ignorato.
**Fix:** nuovo formato `eml` (`.eml` e qualsiasi `.tmp`): `FileRead` + lettura MIME dentro il passo "Accoda testo allegato" (multipart, `message/rfc822` annidati, base64 / quoted-printable,
UTF-8 / Latin-1, intestazioni codificate, HTML → testo, senza usare `String`/`Number`); il testo entra nel prompt con Da / A / Data / Oggetto del messaggio originale. Un `.tmp` non-mail finisce
tra gli allegati "non letti". `.msg` (binario Outlook) resta non supportato e segnalato.

## 4. Mail non spostata in Elaborate / Revisione — NON risolto, serve il log
Il passo `MailDisposition` è l'ultimo top-level e riceve cartella ed esito corretti; senza il log della run non si vede perché non sposti. Ho aggiunto alla "Diagnosi" della mail di esito
casella, cartella sorgente e cartella di destinazione. Richiesti: riga `MailDisposition` del CSV di una run (Success, Error, Summary) e la struttura reale delle cartelle IMAP
(es. `Elaborate` vs `INBOX.Elaborate`). Attenzione: `operatorEmail` coincide con la casella interrogata dal trigger, quindi le mail di esito rientrano nella stessa casella.
