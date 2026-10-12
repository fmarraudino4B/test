# Regole insegnate in chat

Fonte: guida ottobre 2026, cap. 13. Una correzione data in chat diventa una **regola del
database**, ricordata e applicata alle domande successive in **tutte** le chat collegate a quel
database, in MAUI e nella chat web.

## Come si insegna

Sotto il messaggio dell'utente compare il riquadro **«Vuoi che lo ricordi per le prossime domande?»**:

- **da solo**, se il messaggio contiene *impara, ricorda, memorizza, tieni presente, d'ora in poi,
  da adesso in poi*, oppure un'istruzione con *sempre* o *mai* («mostra sempre…», «non usare mai…»);
- **a richiesta**, con l'icona **segnalibro +** accanto a ogni messaggio dell'utente (chat
  collegate a un database): serve quando la correzione non contiene quelle parole.

La domanda intanto prosegue: la risposta arriva comunque, anche se la regola non si salva.

## Cosa propone il riquadro

- **Raccoglie le correzioni di prima** sulla stessa domanda (risale fino alla domanda di partenza,
  con l'ora); si ferma a un **Reset**, a mezz'ora di pausa o a otto messaggi. Ogni correzione ha la
  sua spunta; «già ricordata» indica quelle salvate prima.
- **Le riscrive in regole che si capiscono da sole** (1–3 regole, in pochi secondi): «fai sempre
  così» → «ogni volta che la risposta riguarda ordini di acquisto, mostra anche il fornitore e
  ordina per data di consegna prevista». I dati inviati all'AI sono protetti come nelle domande.
- **Si correggono a mano**; ogni regola ha la spunta; **Riscrivi** chiede una proposta nuova.
- **Vale per:** *tutti i contesti del database* (default proposto) oppure *solo il contesto in uso*.
- **Per:** *tutti gli utenti* oppure *solo per me*. Se chi insegna non è amministratore e sceglie
  *tutti*, la regola vale subito per lui e diventa di tutti quando un amministratore la conferma.
- **Ricorda** salva le regole spuntate; **Non ora** chiude.

## Da quel momento

- Ogni domanda sui dati di quel DB riceve le regole **del suo contesto + quelle per tutti + quelle
  dell'utente** che fa la domanda; se sono molte entrano quelle che riguardano la domanda. L'AI le
  segue nella query e nella risposta.
- Le regole stanno **sul database, non nella conversazione**: **Reset** e **Svuota chat** non le cancellano.
- Le istruzioni «impara…» date **prima** di questa versione vivevano solo nella storia della chat
  e **non sono diventate regole**: vanno ripetute.

**Scrivere una buona regola**: dice **su quali dati** vale e **cosa fare**, con le parole che si
useranno nelle domande. ✔ «Nei prezzi di vendita di un codice mostra sempre se il materiale è
teorico o definitivo»; ✘ «fai come prima». Una regola che *mostra* dati in più vale negli elenchi;
una che *filtra* («escludi sempre le righe con importo zero») vale in ogni domanda.

## Nel Configuratore (Admin/SystemAdmin)

Riquadro **Regole insegnate** (passo 2, sotto Vocabolario). Accanto al titolo il conteggio:
*attive, da confermare, spente o nella conoscenza*.

| Colonna / comando | Serve a |
|---|---|
| Regola | Testo, correggibile |
| Contesto | Vuoto = tutti i contesti del DB; altrimenti solo quello |
| Per | *tutti* oppure *solo l'autore* |
| Stato | *attiva*; *da confermare* (ancora solo per chi l'ha insegnata); *spenta* (resta in elenco ma non entra nelle domande); *nella conoscenza* |
| Conferma per tutti | Su una regola *da confermare*: la rende valida per tutti dalla domanda successiva (spunta *solo da confermare*) |
| Sposta nella conoscenza | Copia la regola in fondo alla conoscenza (sezione *Regole insegnate dagli utenti*); controlla e premi **Salva sul database**: al salvataggio passa a *nella conoscenza* e non entra due volte |
| + regola a mano, ✕, Salva le regole | Aggiungono, tolgono, salvano |

Sotto ogni regola: chi l'ha insegnata, quando, in quale chat e il messaggio da cui è nata.
**Nel pacchetto**: **Esporta** porta con sé le regole *per tutti*; quelle *solo per me* restano
all'utente su quell'installazione. All'importazione la stessa regola nello stesso contesto si
aggiorna, le altre si aggiungono. Ogni utente insegna regole per sé, o per tutti con la conferma
di un amministratore.

## Lo spazio di una domanda

In ogni domanda le regole occupano **max 40 regole e 6.000 caratteri**. Se le attive per tutti sono
di più compare un avviso giallo, ed entrano solo quelle con **parole in comune con la domanda**
(finché c'è spazio); quelle nate dallo stesso messaggio entrano insieme. In MAUI le regole che
riguardano di più la domanda vengono ripetute **in fondo** alla domanda.

Per verificare: scrivi una domanda in **Prova una domanda** → **Quali entrano**: sotto ogni regola
compare *entra nella domanda di prova* oppure *resta fuori*. Se una regola importante resta fuori:
riscrivila con le parole delle domande, accorcia/spegni le inutili, oppure spostala nella conoscenza.

## Regola, conoscenza o prompt?

| Dove | Cosa ci va | Chi lo scrive |
|---|---|---|
| Regola insegnata | Correzioni scoperte usando la chat: colonne da mostrare, ordinamenti, filtri ricorrenti, come presentare un dato | Utenti in chat; admin confermano |
| Conoscenza del database | Legami, codici, significati: ciò che è stabile e verificato | Admin nel Configuratore |
| Prompt Azienda (menu ⋮) | Istruzioni di una sola chat | Admin |

Una regola che descrive i **dati** più che il **modo di rispondere** sta meglio nella conoscenza:
**Sposta nella conoscenza** la porta lì senza riscriverla.
