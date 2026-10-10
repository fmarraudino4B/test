# Regole per cliente (knowledge base di progetto)

> Regole di business e vincoli tecnici emersi per ogni cliente. **Prima di toccare un flusso di un
> cliente, rileggi la sua sezione.** Fonte: handoff del 10/10/2026 (conversazioni dal 15/09 al
> 07/10/2026). Le voci [DA VERIFICARE] richiedono evidenza prima dell'uso.

## Convenzioni di consegna comuni
- Solo DSL "Modalità Sviluppatore" senza commenti (ammesse `// @alias`, `// @continueOnFail`,
  `// @foreach`); cronistoria bug e note in `NOTE_MANUTENTORI_<flusso>.md` a parte.
- File lunghi (> 50 righe) scritti a blocchi; flussi complessi generati da script Python
  (`gen_flusso.py` / `build.py`) con modifiche chirurgiche, mai rigenerazioni complete.
- In consegna distingui sempre **verificato sul sistema reale** da **testato su dati sintetici**.
- Dopo l'import in Studio vanno sempre reimpostati a mano: trigger, pannello Gestione errori dei
  ForEach, credenziali.

## Gazza (DB `Gazza_TC`)
- **Versioni GAZZA Ordine Cliente:** nessun bump di versione senza autorizzazione esplicita
  (etichetta congelata in passato a "1.5.5"). Base attuale nota: 1.5.7A.
- P.IVA cliente dall'intestazione, **mai `00426440343`** (P.IVA Gazza).
- UM = **UM BASE dell'articolo Target**, non quella letta dal documento.
- Ordine creato anche con **una sola riga** risolta (con revisione). Email minimale
  "Ordine creato" oppure "ORDINE CREATO CON REVISIONE" se ci sono warning.
- Confronto prezzo documento vs listino **senza alterare** il prezzo ricalcolato dall'ERP.
- Logica DMS rimossa dal prompt operativo.
- `FileMove` entro `allowedRoot` `e:\DispositiveAI` (sentinella fuori root → falsi errori, run #3918).
- Tabella `THINKAI_GAZZA_ARTICOLI_PROFILO`: PK `(COD_CF, CODICE_CLIENTE_NORM)`; rename legacy
  `CODICE_FORNITORE_*` → `CODICE_CLIENTE_*`, `LAST_LOG_KEY` → `LAST_CORRELATION_ID`; FK log riga →
  testata; 4 viste `VW_THINKAI_GAZZA_*`. Script SQLCMD idempotente con `:setvar NomeCliente`.
  Altri DB cliente possono avere naming diverso.
- Riconciliazione Mustweb e Verifica fatture: **solo SELECT**. Tolleranze 0,01 per riga e 0,02
  sui totali, finestra DDT ±90 giorni; `COD_ART` proposto da Mustweb mai fidato senza verifica su
  `ART_ANA`; `ART_ANA.AZIENDA_ID = 0` = condiviso tra aziende (non escluderlo); attenzione a
  collation nelle join e a "&" vs "e" nei nomi fornitore.
- Conversione campioni: causale ordine campione `OCCD` (la vista usava `OCCA`); DB `Gazza_TC`
  (non REIRE); periodo di default dal 01/10/2025 a oggi.

## DECOX (TaylorGest / Target Cross via TcRestAPI)
- Cartelle `F:\DispositiveAI\DDT\`: `Scansione`, `processing`, `elaborati`, `review`, `attesa`,
  `error-erp`, `error-tecnico`.
- Causale "conto riparazioni" → non è DDT fornitore (DDT_CLI) → **review**.
- Più anagrafiche fornitore: prendi la **prima** (le altre obsolete), filtro `FLAG_FOR=1`.
- Data registrazione = oggi; `DATA_DDT_FOR` dal PDF.
- Riferimento ordine variabile per fornitore: Franke dopo `vs ordine`, European Appliances dopo
  `Ns.rif.`, GM TOP spesso in `ORD_FOR_SPEC.NUMERO_CONFERMA` (match testuale).
- Prezzi ereditati da `ORD_FOR_RIGHE` (`PREZZO_LORDO_VU1`, `SCONTO_1`, `SCONTO_2`), non `0.00`.
- Documenti a blocchi da 30 righe, ricalcolo solo sull'ultimo (M18). **Retry disabilitato** su
  `documento`.
- Import DMS: `COD_CLASSE_DOC=DDT_FOR`, chiave esterna `DOC_ID`; valorizzare `COD_CF_C` e
  `COD_CF_F` nel JSON dei descrittori; cartella di import = `elaborati` se non definita.
- Fatture Franke in XML FatturaPA: scartare la notifica SDI `_ZD_001.xml`.
- P.IVA spesso nel piè di pagina o come `VAT NO.` / `UID` (Hisense, BORA Holding GmbH); EAN come
  codice alternativo in anagrafica.
- Non produrre l'export raw di Studio (`Agent.Steps[]`).

## CMRISTO
- Lettura AI: MailPolling + corpo email e PDF (fornitore, righe, date consegna), confidence per
  campo, date multilingua it/en/de e relative, `MailDisposition` finale.
- Flusso 5: input `righeConfermaFornitore` `{codArt, nuovaData, verificato,
  docIdOrdineFornitore, numRigaOrdineFornitore, docIdOrdineClienteOrigine}`; aggiornamento
  `data_consegna_confermata` via `SqlUpdate` (nessun endpoint di update in TcRestAPI v1.4.5);
  controllo ordini cliente collegati (ordine origine oppure tutti gli aperti sull'articolo).
- Credenziale reale da sostituire a `targetcross-cmristo`.

## DAICOM
- Fatture estere → staging XOFT (testata, IVA, pagamenti, righe), **senza** XML né SDI. Ordine
  di scrittura: righe → IVA → pagamenti → testata.
- Tipi documento: TD17 servizi, TD18 beni UE da estero, TD19 beni già in Italia; conversione in euro.
- Ordini cliente multi-formato (TESISQUARE posizionale, Excel MW, PDF ASPIAG/DESPAR, mail) → CSV `;`.

## Farpro
- Modello fattura canonico con due adapter (XML deterministico Italia, AI da PDF Estero); agenti
  collegati via EventDb su tabella stato/audit; regole in tabella di configurazione multi-cliente.
- Limiti API: nessun endpoint per prima nota, ritenute, autofattura reverse charge, modifica
  anagrafica, cespiti → decisione con Four Infolab prima della terza ondata.

## Profilazione lead (interno)
- Skip dei lead invariati via hash rispetto allo storico; scrittura **solo** su `CF.NOTE_CF`;
  fallback categoria se il codice proposto dall'AI non è a catalogo; preflight fail-closed.
