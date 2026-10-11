# Controllo Fattibilità e Slot Spedizione — Specifica di progetto

Stato: **bozza v0.1** — analisi conclusa, in attesa dell'esito dello script di scoperta schema.
Marcatori: `✅ CONFERMATO` (deciso con il cliente) · `⚠️ DA VERIFICARE` (serve evidenza dal sistema reale) · `📐 PROPOSTA` (ipotesi mia, da validare).

## 1. Obiettivo

Per ogni ordine cliente ricevuto in PDF, l'agente calcola in sola lettura se l'ordine è evadibile e **quando** (data prevista di consegna), poi invia **una mail** con verdetto e dettaglio per riga.

## 2. Decisioni confermate

| Tema | Decisione | Stato |
|---|---|---|
| Ingresso | PDF in cartella, percorso parametrico (M00) | ✅ |
| ERP | TargetCross (`GestionaleSend`, credenziale letterale) | ✅ |
| Slot | = **data prevista di consegna** (non prenotazione di capacità) | ✅ |
| Tempi | **cicli di lavorazione** (tempi di attraversamento per fase) + giorni di transito | ✅ (cicli) / ⚠️ (transito) |
| Formula data | `partenza = max(data disponibilità merce, data ordine + lavorazione)`; `consegna = partenza + transito`; se festivo → primo giorno lavorativo utile | ✅ |
| Data richiesta | Di norma presente nel PDF → confronto con la prevista e scarto in mail | ✅ |
| Deposito | Di norma uno, ma lista **ordinata per priorità** parametrica | ✅ |
| Output | Una sola mail | ✅ |
| Scritture ERP | **Nessuna** nella v1 (solo lettura) | 📐 |
| Dati reali di collaudo | Non disponibili: test su dati sintetici | ✅ |

## 3. Archetipo e sequenza

Archetipo **A1 (front) → A8 (verifica in sola lettura)** + pacchetto produzione **P** se gira senza supervisione.

```
M00 config → M01 preflight → M02 orfani → M03 elenco/ciclo con cap
  └─ per ogni PDF:
      M04 cleanup (tutte le chiavi del giro, last* incluse)
      → M05 claim file
      → M06 estrazione AI (JSON, mai "report")        [catch → cartella ERRORE]
      → M07 normalizzazione (numeri, date gg/mm/aaaa)
      → M08 cliente (P.IVA → ragione sociale)
      → M09 cascata articoli (AI solo su candidati reali)
      → LETTURA disponibilità per deposito (priorità)    ⚠️ tabelle da scoprire
      → LETTURA arrivi da fornitore (residuo ordini)     ⚠️ tabelle da scoprire
      → LETTURA ciclo di lavorazione per articolo        ⚠️ tabelle da scoprire
      → CodeJs deterministico: fattibilità + data prevista per riga
      → CodeJs: verdetto d'ordine e scarto vs data richiesta
      → M13 SendEmail unica (riepilogo)
      → M15 chiusura file + heartbeat
```

Niente `GestionaleSend` con `endpoint: documento` e niente `idempotencyKey` (nessuna scrittura). `lookup` è deprecato dalla v1.5.0: si usano `articoli`/`documenti` con `filtro`/`filtroRaw`, oppure `Query` SELECT sul DB se la connessione dati è disponibile ⚠️ (da decidere dopo la scoperta schema).

## 4. Dati estratti dal PDF (JSON)

`numeroOrdineCliente`, `dataOrdine`, `dataConsegnaRichiesta` (può mancare), `mittente` (ragione sociale, P.IVA — esclusa `ownVat`), `righe[]`: `codiceCliente`, `codiceArticolo`, `descrizione`, `quantita`, `um`, `dataConsegnaRiga` (se presente). Il contenuto del PDF è **non attendibile** (anti prompt-injection, R15).

## 5. Logica di calcolo (📐 PROPOSTA — da validare con i dati reali)

Per ogni riga, nell'ordine:

1. **Disponibilità**: `disp = Σ_depositi (giacenza − impegnato)` scorrendo `depositiPriorita`. Se `disp ≥ quantità` → `dataMerce = dataBase`.
2. **Residuo** `= quantità − disp`. Copertura da **arrivi fornitore** (residuo ordini aperti con data consegna, cumulati per data). Se coperto → `dataMerce = data dell'ultimo arrivo necessario`.
3. **Produzione** (se l'articolo ha un ciclo): `dataLavorazione = dataOrdine + Σ tempi di attraversamento delle fasi` (in giorni lavorativi).
4. `partenza = max(dataMerce, dataLavorazione)` → `consegna = partenza + giorniTransito`, poi aggiustamento festivi/chiusure.
5. **Esito riga**: `NEI_TEMPI` (`consegna ≤ richiesta`) · `IN_RITARDO` (con giorni di scarto) · `NON_DETERMINABILE` (articolo non risolto, ciclo/dati mancanti).
6. **Verdetto ordine**: `FATTIBILE` (tutte NEI_TEMPI) · `PARZIALE` (mix) · `NON FATTIBILE` (nessuna nei tempi) · `DA REVISIONARE` (almeno una NON_DETERMINABILE).

Se la data richiesta manca nel PDF: nessun confronto, si riporta solo la data prevista (default parametrico `giorniConsegnaDefault` ⚠️ da concordare).

## 6. Parametri (profilo privato → M00)

Vedi `profilo-fattibilita-slot.template.json`. Nuovi rispetto al profilo standard: `depositiPriorita`, `giorniTransitoDefault`, `calendarioLavorativo` (giorni e festivi), `giorniConsegnaDefault`, `modalitaLettura`. Tutti i valori sono stringhe in M00 (R9/R18).

## 7. Mail (un solo `SendEmail`, Markdown → HTML)

Oggetto: `[Fattibilità] Ordine {numeroOrdineCliente} – {verdetto}`.
Corpo: verdetto in testa; tabella righe (articolo, richiesta, disponibile, data prevista, scarto, motivo); note su righe non determinabili; allegato: PDF originale.
R8: ogni `{chiave}` deve esistere in tutti i rami → garantire valori di default prima dell'invio.

## 8. Punti aperti (bloccanti per il DSL finale)

| # | Domanda | Come si chiude |
|---|---|---|
| O1 | Dove stanno giacenza, impegnato, ordini fornitore in arrivo? | Script `01_scoperta_schema.sql` |
| O2 | Dove stanno cicli e fasi con tempi di attraversamento? Unità (ore/giorni)? | Idem |
| O3 | Fonte dei giorni di transito (tabella, per zona, default unico)? | Risposta del cliente |
| O4 | Calendario festivi/chiusure: tabella ERP o config? | Risposta + scoperta schema |
| O5 | Articoli solo prodotti, solo acquistati o misti? | Risposta del cliente |
| O6 | Lettura via endpoint TcRestAPI o via `Query` SQL diretta? | Esito scoperta + accordo col produttore ERP |
| O7 | Destinatari/e della mail | Risposta del cliente |
| O8 | Lingua e formato date dei PDF (verso TC: solo `gg/mm/aaaa`, R13) | Esempi di PDF |

## 9. Piano di collaudo (dati sintetici, poi PDF reali)

1. Caso felice: tutte le righe disponibili → `FATTIBILE`.
2. Parziale: una riga con arrivo fornitore oltre la data richiesta.
3. Produzione: articolo con ciclo; verifica somma fasi e giorni lavorativi.
4. Articolo non risolto → `DA REVISIONARE`, nessun errore bloccante.
5. Data richiesta assente nel PDF.
6. Più depositi: la quantità si spezza secondo priorità.
7. ERP irraggiungibile: il file va in `ERRORE`, gli altri proseguono (R2/R3).
8. PDF corrotto o vuoto.

Si distinguerà sempre **verificato su sistema reale** da **testato su dati sintetici** (`test_codejs.py --run`).

## 10. Passi manuali in Studio (a consegna)

Pannello Gestione errori del ForEach (R3) · trigger/cartella · credenziale ERP letterale in ogni `GestionaleSend` · cartelle ELABORATO/REVIEW/ERRORE sotto `workRoot` · eventuale DDL se si adottano tabelle di audit.

## 11. Evoluzioni previste

- Sub-workflow condiviso "calcolo fattibilità" riusabile da un agente schedulato sul portafoglio ordini (A6).
- Passaggio dal verdetto FATTIBILE alla creazione ordine (A1) con data già calcolata.
- Dashboard di scostamento tra data prevista e data effettiva.
