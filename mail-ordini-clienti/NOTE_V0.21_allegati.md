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
