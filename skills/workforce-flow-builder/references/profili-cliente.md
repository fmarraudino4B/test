# Profili cliente: opzioni di comportamento parametrizzabili

> Le regole di business emerse nei progetti reali sono qui **trasformate in opzioni**: un flusso
> nuovo non ha logica cablata per un cliente, ma legge il profilo (`opzioni` in
> `assets/profilo-cliente.template.json`). I clienti sono **pseudonimizzati** (`CLI-A` … `CLI-F`,
> fornitori `Fornitore X1` …, clienti finali `Y1` …); la corrispondenza con i nomi reali non è
> conservata nella skill. Valori, cartelle e codici sono parametri: vedi `parametri.md`.
>
> Quando lavori per un cliente: (1) compila il profilo privato, (2) scegli le opzioni qui sotto,
> (3) dichiara in consegna quali opzioni sono attive e quali sono default non confermati.

## 1. Opzioni di comportamento

| Opzione | Valori | Default | Effetto sul flusso | Emersa in |
|---|---|---|---|---|
| `umPolicy` | `BASE_ARTICOLO` · `DOCUMENTO` | `BASE_ARTICOLO` | UM della riga ERP presa dall'anagrafica articolo, non dal PDF | CLI-A |
| `creaConRigheMinime` | intero ≥ 1 | `1` | Crea il documento anche con poche righe risolte, marcandolo "con revisione" (si combina con `minPercentualeRisoltePerCreare`) | CLI-A |
| `prezzoPolicy` | `RICALCOLO_ERP` · `DA_DOCUMENTO` · `DA_ORDINE` | `RICALCOLO_ERP` | `RICALCOLO_ERP`: prezzo lasciato all'ERP; `DA_ORDINE`: prezzo e sconti ereditati dalla riga d'ordine (`PREZZO_LORDO_VU1`, `SCONTO_1`, `SCONTO_2`), mai `0.00` | CLI-A, CLI-B |
| `confrontoListino` | `NO` · `SOLO_SEGNALAZIONE` · `BLOCCANTE` | `SOLO_SEGNALAZIONE` | Confronto prezzo documento vs listino senza alterare il prezzo ERP | CLI-A |
| `anagraficaMultipla` | `REVISIONE` · `PRIMA_ATTIVA` | `REVISIONE` | Con più anagrafiche per la stessa P.IVA: revisione, oppure la prima attiva (es. filtro `FLAG_FOR=1`, le altre obsolete) | CLI-B |
| `fallbackRagioneSociale` | sì / no | sì | Ricerca per ragione sociale ripulita quando manca la P.IVA (M08) | CLI-B |
| `cascataArticoli` | lista ordinata | `MEMORIA, COD_ART, CODICE_SECONDARIO, EAN, CANDIDATI_AI` | Ordine dei metodi di matching (M09) | CLI-A, CLI-B |
| `autoLearning` | sì / no | sì | Upsert su `THINKAI_<CLIENTE>_ARTICOLI_PROFILO` | CLI-A |
| `dataRegistrazione` | `OGGI` · `DATA_DOCUMENTO` | `OGGI` | Data di registrazione; la data del documento resta quella del PDF | CLI-B |
| `riferimentoOrdinePerFornitore` | lista `{codFornitore, etichetta, fonte}` | vuota | Dove trovare il riferimento all'ordine per ciascun fornitore: dopo un'etichetta nel testo, oppure in `NUMERO_CONFERMA` con match testuale | CLI-B |
| `causaliDaRevisione` | lista di testi | vuota | Documenti con queste causali (es. "conto riparazioni", che non è un DDT fornitore) vanno in revisione | CLI-B |
| `fileDaScartare` | lista di suffissi | vuota | File da ignorare in ingresso (es. notifiche SDI `_ZD_001.xml` accanto alle fatture XML) | CLI-B |
| `emailEsito` | `MINIMALE` · `DETTAGLIATA` | `MINIMALE` | Oggetto "Documento creato" / "DOCUMENTO CREATO CON REVISIONE" se ci sono warning | CLI-A |
| `modalitaScrittura` | `API` · `SQL_DIRETTO` · `STAGING` | `API` | `SQL_DIRETTO` solo dove l'API non ha l'operazione (es. update date consegna, note anagrafica), dichiarandolo; `STAGING`: tabelle di frontiera in ordine di dipendenza | CLI-C, CLI-D, interno |
| `soloLettura` | sì / no | no | Flussi di verifica/riconciliazione: solo `SELECT`/`WITH` (A8) | CLI-A |
| `dms` | `{attivo, classeDocumento, chiaveEsterna}` | non attivo | Import DMS: classe documento, chiave esterna `DOC_ID`, valorizzare `COD_CF_C`/`COD_CF_F` nei descrittori, cartella di import = elaborati se non definita | CLI-B |
| `retrySuCreazione` | sì / no | **no** | Il retry dopo un timeout crea duplicati (R19) | CLI-B |
| `righePerBlocco` | intero | `24` | Creazione documento a blocchi (M18) | CLI-B |

## 2. Accortezze di dominio riusabili (valgono per qualsiasi cliente)
- **P.IVA nei documenti:** spesso nel piè di pagina o sotto `VAT NO.`, `UID`, `USt-IdNr.`, `MwSt`,
  `Tax ID`; un campo `PIVA` vuoto non significa assenza; più P.IVA → solo quella del mittente;
  escludere sempre `ownVat` (P.IVA propria). Osservato su fornitori italiani ed esteri (CLI-B).
- **Codice articolo spezzato su due righe del PDF** o righe senza codice: prevedi la
  ricomposizione o la revisione, non lo scarto silenzioso (CLI-A, clienti finali Y1 e Y2).
- **EAN** come codice alternativo in anagrafica (CLI-B).
- **Riconciliazione in sola lettura** (CLI-A): tolleranze da `soglie`; `COD_ART` proposto da un
  portale esterno mai fidato senza verifica su `ART_ANA`; `ART_ANA.AZIENDA_ID = 0` significa
  condiviso tra aziende (non escluderlo); collation esplicita nelle join tra DB; normalizza
  "&"/"e" nei nomi fornitore; attenzione alle date un giorno indietro (UTC).
- **Fatture estere** (CLI-D): tipi documento TD17 servizi, TD18 beni UE, TD19 beni già in Italia;
  conversione in euro; tracciato di staging spesso privo di paese, divisa/cambio e ID IVA estero:
  chiedili prima di partire.
- **Ordini multi-formato** (CLI-D): tracciato EDI posizionale, Excel da portale, PDF di catene
  GDO, mail testuali → un modello canonico unico, un adapter per formato.
- **Pipeline multi-agente** (CLI-E): modello canonico + adapter (XML deterministico / PDF con AI),
  agenti collegati via EventDb su tabella stato/audit, regole in tabella di configurazione;
  prima mappa i limiti dell'API (prima nota, ritenute, autofattura reverse charge, modifica
  anagrafica, cespiti).
- **Lettura AI mail** (CLI-C): confidence per campo; date multilingua it/en/de e relative.
- **Arricchimento anagrafiche** (interno): salta i record invariati via hash rispetto allo
  storico; scrivi solo nel campo concordato; fallback se il codice proposto dall'AI non è a
  catalogo; limite per run.
- **Schema tabelle custom:** script SQLCMD idempotente con `:setvar NomeCliente`; PK composta
  `(COD_CF, CODICE_CLIENTE_NORM)` sulla tabella profilo articoli; FK log riga → testata; viste
  `VW_THINKAI_<CLIENTE>_*`. Il naming legacy può variare tra DB cliente: verifica prima.

## 3. Profili pseudonimizzati (valori scelti nei progetti)
| Profilo | Archetipi | Opzioni non di default |
|---|---|---|
| CLI-A | A1+P, A8, A6 | `creaConRigheMinime=1`, `emailEsito=MINIMALE`, `soloLettura` sui flussi di verifica; versioni: nessun bump senza autorizzazione |
| CLI-B | A2+P | `anagraficaMultipla=PRIMA_ATTIVA`, `prezzoPolicy=DA_ORDINE`, `riferimentoOrdinePerFornitore` (3 fornitori), `causaliDaRevisione`, `fileDaScartare`, `dms.attivo`, `righePerBlocco=30` |
| CLI-C | A3, A6 | `modalitaScrittura=SQL_DIRETTO` per le date di consegna |
| CLI-D | A9, A1 multi-formato | `modalitaScrittura=STAGING` |
| CLI-E | A10 | solo piano |
| CLI-F | A2 (conto lavoro) | template generalizzato richiesto [DA VERIFICARE] |

## 4. Convenzioni di consegna comuni
- Solo DSL "Modalità Sviluppatore" senza commenti (ammesse `// @alias`, `// @continueOnFail`,
  `// @foreach`); cronistoria in `NOTE_MANUTENTORI_<flusso>.md`.
- Flussi complessi generati da script Python con modifiche chirurgiche.
- In consegna distingui **verificato su sistema reale** da **testato su dati sintetici**.
- Dopo l'import in Studio: trigger, Gestione errori dei ForEach e credenziali vanno reimpostati.
- **Privacy:** nei file condivisi solo pseudonimi e segnaposto; la copia con i dati reali resta
  privata (`*.privato.*`). Verifica con `scripts/anonimizza.py verifica` prima di ogni invio.
