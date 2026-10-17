# Template: Trigger Manuale / Schedulato (FileList esplicito)

Versione più evoluta del flusso. Differenze rispetto al template cartella:
- Usa FileList esplicito invece del trigger "su nuovo file"
- CLEANUP_ordine tra ogni PDF per evitare bleed tra iterazioni
- Gestione NON_ELAB (sposta PDF non elaborabili)
- Fallback ricerca cliente per nome se P.IVA mancante
- Ricerca articoli con subquery ART_CODICI più robusta (2 metodi invece di 3)
- FileMove ELABORATO dopo creazione documento
- Log JSON per ogni esecuzione

Sostituire tutti i segnaposto `{{...}}` con i valori raccolti.

---

## Testo del prompt da generare

```
Crea un agente WorkForce che registra automaticamente nel gestionale TargetCross gli ordini di acquisto dei clienti ricevuti come PDF.

TRIGGER: avvio MANUALE (a richiesta). NON usare il trigger "su nuovo file": i PDF li recupera lo step FileList qui sotto. In produzione puoi sostituire il manuale con uno SCHEDULATO (es. ogni mattina alle 8, oppure ogni 5 minuti) senza toccare il resto del flusso.

PASSO INIZIALE - Step "File List" (categoria Dati): elenca i file della cartella {{CARTELLA_INPUT}}, pattern *.pdf, non ricorsivo. Lo step scrive la lista dei PDF nella variabile lastFileList.

Poi, per OGNI file in lastFileList (ForEach con itemsKey = lastFileList), esegui questo flusso:

1) Filtra con uno step AI di analisi che classifica il documento. Prompt esatto dello step: "Analizza il PDF allegato e determina se è un ORDINE DI ACQUISTO emesso da un cliente verso un fornitore (documento con righe di articoli, quantità e prezzi che un cliente invia per ordinare merce). Rispondi SOLO con questo JSON: {"isOrdineCliente": true|false, "motivo": "<breve motivo>"}. false se è una fattura, un DDT, un preventivo/offerta, una mail generica, un sollecito o altro tipo di documento."

2) Trasforma l'esito AI in un flag isOrdineClienteFlag ("true"/"false") con uno step di codice.

3) Branch con condizione $.isOrdineClienteFlag == "true". Se è un ordine cliente esegui tutta la pipeline sotto; nel ramo else ignora il documento (nessuna azione) e segnala via mail che non è stato possibile inserire. Sposta il file nella cartella {{CARTELLA_NON_ELAB}} e vai all'analisi del file successivo.

RAMO "è un ordine cliente":

4) Step AI di estrazione dati dal PDF. Prompt esatto dello step: "Analizza il PDF allegato: è l'ordine di acquisto di un CLIENTE verso la NOSTRA azienda ({{NOME_AZIENDA_FORNITORE}}, P.IVA {{PIVA_FORNITORE}}). Estrai SOLO un oggetto JSON con questa struttura esatta, senza testo aggiuntivo, senza markdown:
{"testata":{"pIva":"<P.IVA del CLIENTE che emette l'ordine: è il mittente/intestatario dell'ordine, di solito in alto; può trovarsi nei dati mittente OPPURE nel logo/intestazione. NON usare MAI la P.IVA della nostra azienda {{PIVA_FORNITORE}}, che sul documento compare come Fornitore. Il cliente usa la parte solo la parte numerica senza lo stato. Se non trovi la partita iva cerca di individuare il cliente tramite una similitudine del nome cliente>","stato":"<indica lo stato, nazione del mittente>","numConferma":"<numero ordine del cliente se presente, oppure numero conferma altrimenti vuoto>","dataConferma":"<data ordine gg/mm/aaaa, oppure data conferma ordine altrimenti vuoto>","ordineId":"<identificativo/commessa ordine se presente>","destDesc":"<descrizione destinazione merce se presente>","destIndi":"<indirizzo destinazione>","destComune":"<comune destinazione>","destCap":"<CAP destinazione>","destProv":"<provincia 2 lettere>"},"righe":[{"codArt":"<codice articolo: può essere il codice del CLIENTE, o quello indicato come codice fornitore>","des":"<descrizione articolo>","um":"<unità di misura>","quant":0,"prezzoLordo":0,"sconto1":0,"sconto2":0,"sconto3":0,"sconto4":0,"sconto5":0,"offRigaId":"<riferimento riga offerta se indicato in riga, altrimenti vuoto>"}]}
Regole: il CLIENTE è chi ordina (NON {{NOME_AZIENDA_FORNITORE}}). Importi in EURO. Se un dato manca usa stringa vuota o 0."

5) Step di codice: normalizza il JSON estratto e salva piva, numConferma, dataConferma e le righe dell'ordine.

6) Step gestionale (TargetCross): operazione clienti con filtro CF.P_IVA_CF='{piva}' per ricavare il COD_CF del cliente dalla P.IVA estratta. Se la partita iva {piva} è vuota o non è stato trovata cerca in CF.RAG_SOC_CF il nome del mittente. Se non trovi neanche in questo caso una corrispondenza invia una mail di errore. Sposta il file nella cartella {{CARTELLA_NON_ELAB}} e vai all'analisi del file successivo.

7) Step di codice: parsa la risposta e salva codCf, ragSoc e il filtro cliente.

8) Step "carica JSON da file": profiles-clienti/{codCf}.json se esiste (failOnInvalid=false: al primo ordine del cliente non esiste ancora).

9) Step di codice: esponi la mappa appresa codice-cliente -> COD_ART.

10) Step di codice: prepara la lista righePerRicerca e gli accumulatori articoli.

11) ForEach su righePerRicerca (ogni riga dell'ordine): cerca l'articolo con una CASCATA DI 2 METODI:
   - Pre-check profilo: se il codice è già appreso per questo cliente, salta A/B.
   - Metodo A - step gestionale: operazione articoli con filtro cercando prima in articolo, poi nell'articolo secondario: (ART_ANA.COD_ART='{currentCodArtEscaped}') OR (ART_ANA.COD_ART LIKE '%{currentCodArtEscaped}%') OR ART_ANA.COD_ART IN (SELECT COD_ART FROM ART_CODICI WHERE ART_CODICI.FLAG_COD_CF=1 AND COD_SECONDARIO_ART LIKE '%{currentCodArtEscaped}%' AND (ART_CODICI.TIPO_CODICE='{currentCodCfEscaped}' OR LEN('{currentCodCfEscaped}')=0)) (codice diretto su TargetCross). Poi step di codice che imposta currentArtFound true/false.
   - Branch $.currentArtFound == "false" -> Metodo B - step Query SQL sullo storico ordini (ORD_CLI_RIGHE, LIKE sul codice):
     SELECT TOP 1 ART_ANA.COD_ART FROM ART_ANA INNER JOIN ORD_CLI_RIGHE ON ART_ANA.COD_ART = ORD_CLI_RIGHE.COD_ART AND ART_ANA.FLAG_OBSOLETO = 0 AND ART_ANA.FLAG_INATTIVO = 0 AND ORD_CLI_RIGHE.COD_CF = '{currentCodCfEscaped}' AND ORD_CLI_RIGHE.COD_ART LIKE '%{currentCodArtEscaped}%'. Poi step di codice che imposta currentArtFound true/false.
   - Step di codice: aggiorna articoliTrovati e articoliScartati dopo ogni riga.

12) Step di codice: costruisci il body JSON per ORD_CLI e determina l'esito (ok/anomalia/errore).

13) Branch con condizione $.esito == "ok". Se ok ed è stato trovato almeno 1 articolo, crea il documento, altrimenti (else) azzera i campi documento senza crearlo. Per la creazione del documento ordini clienti utilizza:
COD_CAUS_DOC = 'ORDCLI', SERIE_DOC: 'ORD-C', COD_DEP: 'MAG'.
Sposta il file nella cartella {{CARTELLA_NON_ELAB}} e vai all'analisi del file successivo.

RAMO "esito ok":
   - Step gestionale: operazione documento per creare il documento ORD_CLI su TargetCross (produce il codice documento).
   - Step di codice: prepara le righe di audit (STATO=2).
   - Step SqlInsert: scrivi le righe di audit su una tabella d'appoggio (nome e colonne da definire lato cliente).
   - Step di codice: costruisci il profilo cliente aggiornato con le corrispondenze articolo apprese.
   - Step "scrivi JSON su file": profiles-clienti/{codCf}.json (overwrite).
   - Step gestionale: operazione documenti-stampa (docId = codice del documento creato, continueOnFail). Il gestionale SCRIVE GIÀ il PDF su disco e ne espone il percorso in lastGestionalePdfPath: NON salvarlo con uno step "scrivi file" (FileWrite scrive solo testo e produrrebbe un PDF illeggibile).
   - Step di codice: copia lastGestionalePdfPath in una chiave dedicata (stampaPdfPath) e imposta stampaDisponibile = "true"/"false", senza ricalcolare né sovrascrivere lastGestionalePdfPath.
   - Step sposta il file pdf nella cartella {{CARTELLA_ELABORATO}}

14) Step AI per generare il corpo email in Markdown con l'esito. Prompt esatto dello step: "Genera un corpo email professionale in Markdown per notificare l'esito del caricamento di un Ordine Cliente.

Dati disponibili:
- Esito: {esito}
- Motivo errore/anomalia: {motivoErrore}
- Cliente: {ragSocDoc} (COD_CF: {codCfDoc})
- P.IVA fornitore: {piva}
- Numero conferma: {numConferma}
- Data conferma: {dataConferma}
- Codice documento creato: {lastGestionaleCodice}
- Riepilogo ordine: {riepilogoOrdine}

Regole:
- Se esito è 'ok': dichiara che il documento ORD_CLI è stato creato con successo in Target Cross con il codice {lastGestionaleCodice}. Elenca gli articoli caricati.
- Se esito è 'anomalia': dichiara che il documento NON è stato creato perché alcuni articoli non sono stati trovati nel gestionale. Elenca gli articoli trovati e quelli scartati con il motivo.
- Se esito è 'errore': dichiara che il documento NON è stato creato e spiega il motivo (es. cliente non trovato, nessuna riga valida). Indica i campi obbligatori mancanti.
- Includi sempre: esito, cliente/documento, articoli trovati, articoli scartati, campi obbligatori mancanti se presenti.
- Usa un tono professionale e chiaro. Usa tabelle Markdown per gli articoli se ci sono più di 2 righe.
- Non aggiungere firme o footer aziendali."

15) Step di codice: arricchisci l'oggetto con il codice documento e anteponi il blocco esito.

16) Step "Markdown": converti il corpo email da Markdown a HTML.

17) Step SendEmail: invia il riepilogo a [{{EMAIL_NOTIFICA}}] allegando il PDF originale dell'ordine e, solo se stampaDisponibile == "true", il PDF del documento ORD_CLI creato (stampaPdfPath). Se la stampa non è disponibile usa un SendEmail distinto senza quell'allegato.
```

---

## Segnaposto disponibili

| Segnaposto | Valore da sostituire |
|---|---|
| `{{CARTELLA_INPUT}}` | Es. `<WORK_ROOT>\in` |
| `{{CARTELLA_ELABORATO}}` | Es. `<WORK_ROOT>\ELABORATO` |
| `{{CARTELLA_NON_ELAB}}` | Es. `<WORK_ROOT>\NON_ELAB` |
| `{{NOME_AZIENDA_FORNITORE}}` | Es. `Azienda Esempio s.r.l.` |
| `{{PIVA_FORNITORE}}` | Es. `<PIVA_PROPRIA>` |
| `{{EMAIL_NOTIFICA}}` | Es. `'notifiche@example.com'` |

## Note rispetto al template cartella

- Il Metodo A in questa versione usa una subquery ART_CODICI più potente che
  cerca sia in COD_ART diretto che nei codici secondari con LIKE, restituendo
  sempre il COD_ART della tabella ART_ANA (non il codice secondario).
- Il Metodo C è assorbito nel Metodo A tramite la subquery, quindi questa
  versione ha solo 2 metodi invece di 3.
- Il documento ORD_CLI richiede i parametri fissi: COD_CAUS_DOC='ORDCLI',
  SERIE_DOC='ORD-C', COD_DEP='MAG'.
