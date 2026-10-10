# Intake requisiti e formato di consegna

> Obiettivo: arrivare al primo flusso valido **senza giri a vuoto**. Ricava dal contesto tutto
> ciò che puoi; chiedi in **un solo messaggio** solo ciò che manca ed è bloccante. Non
> inventare mai valori (cartelle, credenziali, causali, destinatari): usa `<da compilare>` e
> dichiaralo.

## 1. Domande minime (bloccanti)
| # | Domanda | Perché serve | Default proponibile |
|---|---|---|---|
| Q1 | Cosa entra (PDF in cartella, mail, webhook, righe DB) e con che volumi? | Archetipo + trigger | — |
| Q2 | Cosa deve uscire (documento ERP e tipo, tabella, notifica, risposta)? | Moduli di scrittura | — |
| Q3 | Quale ERP/credenziale (`credentialName`)? Ambiente test o produzione? | M01, dry-run | credenziale di test |
| Q4 | Chi riceve notifiche/revisioni? | M13 | — |
| Q5 | Gira supervisionato o da solo? Serve tracciabilità? | Pacchetto produzione P | P se "da solo" |

## 2. Domande di dettaglio (se pertinenti all'archetipo)
- **A1/A2:** causale/serie/deposito (o profilo per cliente); soglia % righe risolte; prezzi da
  documento o ricalcolati ERP; cartelle ELABORATO / REVIEW / ERRORE; P.IVA della propria azienda
  (da escludere in estrazione); tabelle custom ammesse (prefisso).
- **A3:** server/credenziale IMAP, cartelle di destinazione, risposta al mittente.
- **A5:** canale, identità run-as e `chatId`, risposta sincrona o no.
- **A6:** query di sorveglianza o orario, marcatura righe lavorate.

## 3. Specifica di progetto (scrivila prima del DSL, 10-20 righe)
```
Flusso: <nome> v<versione>    Archetipo: <A1..A7> [+P]
Trigger: <tipo> — chiavi iniziali: <...>
Sequenza (moduli): M00 → M01 → ... (indica i contenitori: for / if / switch)
Chiavi StepData prodotte: <chiave> ← <step>   (una riga per chiave usata a valle)
Scritture esterne + idempotencyKey: <step> → <chiave>
Ramo negativo di ogni decisione: <cosa succede>
Passi manuali in Studio: <elenco>
```
Mostrala all'utente solo se il flusso è complesso (≥ 3 contenitori o scritture ERP); altrimenti
procedi direttamente.

## 4. Formato di consegna
1. **File DSL** (`<nome-flusso>.js`): intestazione fissa, solo codice + `// @alias`,
   `// @continueOnFail`, `// @foreach`. Niente commenti esplicativi.
2. **Note manutentori** (`NOTE_MANUTENTORI_<nome-flusso>.md`): scopo, trigger da configurare,
   chiavi di config, tabelle/DDL richieste, passi manuali in Studio, cronistoria bug, test di
   collaudo. Distingui sempre ciò che è **verificato sul sistema reale** da ciò che è **testato
   solo su dati sintetici** (`test_codejs.py --run`).
3. **Esito dei controlli**: `valida_flusso.py` → 0 errori, 0 avvisi (o avvisi giustificati uno
   per uno) e `test_codejs.py` → 0 errori. Nessuno dei due intercetta bug sulla forma dei dati a
   runtime: per quelli servono CSV di run e dump StepData.
4. **Passi manuali** sempre elencati nel messaggio: pannello Gestione errori del ForEach,
   configurazione trigger, credenziale di produzione **letterale** in ogni `GestionaleSend`
   (no dry-run), tabelle da creare, cartelle IMAP/disco da predisporre.
5. **Piano di collaudo** (3-5 casi): caso felice, documento ambiguo, ERP irraggiungibile,
   duplicato, file corrotto. Per ognuno: cosa controllare in Cronologia (step verdi con
   `↺ replay` = NON eseguiti).
