# Preferenze Viste, semantica di tabelle e viste, Reset ChatRoom

Fonte: guida ottobre 2026, capp. 6–7.

## 1. Preferenze Viste

Decidono **su quale contesto** rispondere a ogni domanda. Si aprono da menu ⋮ del progetto →
**Preferenze Viste** (anche dalle azioni rapide). A sinistra: ricerca, **Configura tutte con AI**,
**Aggiungi nuova preferenza**, elenco raggruppato per categoria e ordinato per priorità (regola
AND/OR/PHRASE, priorità *P n*, stato, bollino **Personalizzata** = non sovrascritta dalle
modifiche del progetto master).

| Campo | Contiene | Uso nel sistema |
|---|---|---|
| Keywords di aggancio (virgola) | Poche parole forti o sinonimi | Segnale principale; peso secondo la Regola |
| Viste/tabelle autorizzate | Viste del contesto (pulsante a griglia) | Tabelle su cui l'AI scrive la query; per non-admin anche il loro perimetro dati |
| Tipo Analisi | Tipologia delle Impostazioni Analisi | Lega preferenza e tipologia. **Una sola preferenza per Tipo Analisi** («Aggiungi» con un tipo già usato aggiorna l'esistente) |
| Categoria / area business | Dominio con le parole degli utenti | Raggruppa i contesti nel selettore; ogni parola della domanda che compare vale punti |
| Regola | **AND** tutte le keyword · **OR** almeno una · **PHRASE** frase | Come contano le keyword |
| Priorità | 0–10 | Si **somma sempre** al punteggio (decide la parità, ma può far agganciare da sola) |
| Descrizione semantica | Concetto e termini di dominio | Ogni parola della domanda che compare vale punti; è anche il **titolo** del contesto in barra e selettore |

**Le Preferenze Viste non arrivano all'AI**: keywords/categoria/descrizione servono solo a
scegliere il contesto e mostrarlo. Le istruzioni sui dati vanno nella conoscenza e nel Prompt Chat.

## 2. Come il sistema sceglie il contesto (punteggio, senza AI)

1. La domanda è ridotta a parole (minuscole, senza accenti né parole vuote) e **allargata con gli
   alias** del sistema (*scadenze* vale anche *scadenza*/*scadenzario*; *cliente* anche *clienti*;
   *fatturato* anche *fattura/fatture*).
2. Le keyword si confrontano come **parole intere** (più parole = sequenza): **AND** con tutte
   presenti 45 + 8/keyword; **OR** con almeno una 28 + 8/keyword trovata; **PHRASE** 55 + 10 per
   voce trovata (ne basta una).
3. Ogni parola della domanda trovata nei campi aggiunge: **Tipo Analisi 14**, **Categoria 12**,
   **Descrizione 10**, **nome della vista 5**.
4. La **Priorità** si somma al totale (e un poco al bonus delle keyword).
5. **Vince il punteggio più alto, purché ≥ 12.** A parità decide la priorità. Se nessuno arriva a
   12 si resta sul contesto attuale.

Il calcolo **non ricorda** il contesto corrente (nessun vantaggio): da qui quasi tutti i cambi di
contesto involontari.

> **Regola d'oro: priorità mai oltre 10.** Soglia 12 + priorità sommata sempre ⇒ un contesto con
> priorità ≥12 aggancia qualunque domanda non presa da un altro contesto («e per il 2024?») e
> scavalca il contesto scelto a mano. Il campo della finestra arriva a 10, ma **Configura con AI**
> propone 12 per il «lato di default» delle coppie clienti/fornitori: correggilo sempre a **10 o meno**.

## 3. Contesto scelto a mano e cambi di contesto

Il contesto scelto (*Scegli un contesto di analisi → Scegli ora*) è **un punto di partenza, non un
blocco**; a ogni domanda il sistema rifà il calcolo:

- nessun contesto arriva a 12, oppure vince la stessa vista → si resta;
- **un altro contesto arriva a 12** → la chat toglie la selezione manuale, pulisce la memoria
  locale della conversazione e scrive «Vista preferenziale cambiata - Ho pulito il contesto per
  adattarmi alla nuova vista: …». Senza selezione manuale compare per qualche secondo il bollino **AUTO**.

Il contesto resta **fisso** solo in: *Documenti → Conversazione + dati*, invio con **Costruisci
domanda** (Domanda guidata), aggiornamento di una dashboard salvata.

**Cambiato il 2 ottobre**: prima la MAUI stimava un «cambio di argomento» confrontando le parole
fra domande consecutive e azzerava il contesto («Nuovo argomento rilevato»); sbagliava con le
domande di seguito naturali. Quella stima è **tolta**: oggi il contesto cambia solo quando un
altro contesto vince il punteggio, oppure con il **Reset**.

Un cambio sbagliato pesa: decide il Prompt Chat e **quale parte della conoscenza** arriva all'AI.

## 4. Impostare le preferenze senza cambi involontari

| Fate così | Perché |
|---|---|
| **Priorità 0–10**: contesto più usato di ogni area = 10, gli altri 9, 8… | Sopra 11 aggancia anche domande senza parole utili; priorità diverse rendono prevedibili le parità |
| **Il lato** (clienti/fornitori) scritto **uguale** in Tipo Analisi, Categoria e nome vista di **tutti** i contesti di quel lato, **non** nella Descrizione | Il lato pesa uguale per tutti i contesti del lato; in un solo contesto lo farebbe vincere su tutte le domande con *clienti* |
| **AND** per le coppie speculari: *scadenze + clienti*, *scadenze + fornitori* | La domanda deve nominare concetto **e** lato per agganciare con forza |
| **OR solo per sinonimi stretti** di un concetto unico: *fido, affidamento, castelletto* | In OR basta una parola: se generica aggancia tutto |
| **Descrizione con parole del concetto** (scadenzario, rate, incassi, insoluti, ritardi) | Portano al contesto giusto le domande senza keyword («insoluti di settembre») |
| **Niente parole generiche** (dati, analisi, importi, periodo) e **niente parole-trappola** | *esposizione* è alias di *mostra/visualizza*: in una descrizione aggancia «mostrami…» |
| **Keyword diverse** da un contesto all'altro | Una keyword condivisa fa decidere la priorità, non il significato |

Esempio dalla guida (4 contesti, 3 clienti + 1 fornitori, priorità 10/9/8/8):

| Tipo Analisi · vista | Keywords · Regola | Categoria | P. |
|---|---|---|---|
| Vendite clienti · V_VENDITE_CLIENTI | vendite, clienti · AND | Vendite clienti | 10 |
| Scadenze clienti · V_SCADENZE_CLIENTI | scadenze, clienti · AND | Scadenze clienti | 9 |
| Scadenze fornitori · V_SCADENZE_FORNITORI | scadenze, fornitori · AND | Scadenze fornitori | 8 |
| Fidi clienti · V_FIDI_CLIENTI | fido, affidamento, castelletto · OR | Fidi clienti | 8 |

Esiti calcolati: «scadenze dei clienti di marzo» → Scadenze clienti (152 vs 49); «quanto dobbiamo
pagare ai fornitori a ottobre?» → Scadenze fornitori (49 vs 10); «fido residuo del cliente Rossi» →
Fidi (84 vs 41); «e a novembre?», «e per il 2024?», «solo i primi 10» → nessuno (≤10, sotto
soglia): resta il contesto attuale; «e le scadenze di novembre?» → Scadenze clienti (lato di
default, 50 vs 49: decide la priorità).

**Il caso che la configurazione non può evitare**: una domanda di seguito con **solo la parola
comune** a due contesti speculari va al **lato di default**. Dillo agli utenti: nelle domande di
seguito **nominate il lato** («e le scadenze fornitori di novembre?» → 150 vs 50), oppure usate
**Costruisci domanda** che fissa il contesto. Guardate la barra del contesto dopo ogni risposta.

**Il Configuratore riscrive la preferenza**: ogni **Salva e Applica** dal Configuratore aperto
dalle Impostazioni Analisi rigenera con l'AI la preferenza di quella tipologia (keyword, categoria,
descrizione, regola, priorità). Le modifiche a mano si perdono: dopo ogni salvataggio dal
Configuratore **riapri la preferenza e ricontrollala, priorità compresa**.

**Configura con AI** (nel modulo, con vista e Tipo Analisi compilati): propone keyword, categoria,
regola, descrizione, priorità come *Bozza AI*, **non salva** finché non premi *Aggiungi* o *Salva
modifica*. **Configura tutte con AI** rifà tutte le preferenze (anche disattivate) con anteprima:
**Applica tutte** / **Annulla**; rivedi poi a mano priorità, lato, descrizioni. La **Guida** della
finestra riassume 5 regole.

### Come si collauda

1. Prove con **un utente normale** (Admin/SystemAdmin vedono tutti i contesti e, senza contesto, hanno un percorso diverso).
2. Per ogni contesto: 3 domande tipiche, 2 di seguito («e nel 2024?», «solo i primi 10»), 2 ambigue.
3. Dopo ogni risposta guarda **barra del contesto** e **striscia dei passaggi**: dicono quale contesto ha vinto.
4. Se una domanda di seguito cambia contesto, cerca la parola che ha agganciato (keyword,
   categoria, descrizione, nome vista o suo alias) e toglila, oppure abbassa la priorità.

## 5. Semantica di tabelle e viste (solo SQL Server)

ThinkAI legge le **descrizioni business** scritte come *proprietà estese* di SQL Server: per viste
e tabelle `descrizione`, `descrizione estesa`, `categoria`, `tag`; per le colonne `descrizione`,
`descrizione estesa`, `tipo semantico`, `alias`. Servono a trovare le tabelle giuste quando non c'è
un contesto e a spiegare all'AI cosa contiene ogni colonna (la descrizione arriva come commento
nello schema della query).

| Pulsante | Cosa fa | Scrive sul DB? |
|---|---|---|
| Controlla semantica | Mostra vista per vista descrizione, categoria, tag e quante colonne hanno descrizione/alias/tipo | No |
| Genera semantica DB (SQL) | L'AI propone la semantica (gruppi da 80 colonne) e prepara uno script da rieseguire; tabella o vista lo decide il DB | No (apre il pannello per applicare o copiare) |
| Applica al DB | Esegue lo script dopo aver controllato il permesso ALTER | **Sì, sovrascrive** le proprietà esistenti |
| Completa mancanti | Scrive solo le proprietà che mancano, una vista alla volta | Sì, senza toccare quelle che ci sono |

Dopo ogni scrittura usa **Aggiorna catalogo** del progetto («Ri-indicizza il catalogo semantico
per usarle in chat»). **Alias**: per ogni colonna importante da 3 a 6 alias con le parole degli
utenti (è il segnale più forte contro le colonne inventate); descrizioni brevi e chiare valgono
più di quelle lunghe; se le viste vengono rigenerate, **riapplica la semantica**.

```
Vista V_SCADENZE_FORNITORI
  Descrizione: Scadenze fornitori
  Descrizione estesa: Rate da pagare ai fornitori con data di scadenza, importo e stato; ...
  Categoria: Scadenze fornitori
  Tag: scadenze, pagamenti, debiti, fornitori, rate
Colonna DATA_SCAD
  Descrizione: Data di scadenza della rata · Tipo semantico: data
  Alias: scadenza, data scadenza, data pagamento, entro il
```

## 6. Come lavorano insieme

| Funzione | Risponde a | Se manca/è sbagliata |
|---|---|---|
| Preferenze Viste | Di quale argomento parla l'utente? | Contesto sbagliato o salti di contesto |
| Semantica tabelle/viste | Cosa c'è in questa tabella e colonna? | L'AI indovina il significato dai nomi |
| Conoscenza del database | Come si legano le tabelle, cosa significano i codici, quali regole? | Join sbagliati, codici fraintesi, totali gonfiati |
| Regole delle misure | Quali righe hanno davvero quel numero nel testo? | Ricerche che trovano la 3500 e perdono la 3200 |
| Vocabolario | In quanti modi è scritta questa parola? | Si trovano solo le righe scritte come nella domanda |
| Prompt Chat / Prompt Azienda | Cosa significano i dati? Quali filtri valgono? | Risposte generiche, filtri dimenticati |

## 7. Il Reset della ChatRoom

Pulsante **Reset** (suggerimento «Azzera cache e contesto») nella barra accanto a **Voce** e
**Allega**; disattivato mentre l'AI lavora; **non chiede conferma**. Effetto:

1. **azzera le cache** della conversazione (query già eseguite, tabelle e schemi ricordati, entità);
2. **toglie il contesto scelto** (la barra torna a «Scegli un contesto di analisi»);
3. mostra «Cache e contesto azzerati» e l'avviso «La prossima domanda parte senza i messaggi
   precedenti» con link **annulla**.

La domanda successiva va all'AI **senza la storia della chat** (vale per **una domanda sola**).

| Il Reset toglie | Il Reset lascia |
|---|---|
| Storia della chat (per la domanda successiva) | Messaggi visibili nella conversazione |
| Cache di query, tabelle, schemi | Conoscenza del DB, regole delle misure, vocabolario, regole insegnate |
| Contesto scelto (va riscelto) | Prompt Chat e prompt del contesto, Preferenze Viste, impostazioni |

**Quando usarlo**: risposta sbagliata che, ripetendo la domanda, torna uguale (l'AI ricopia la
query di prima); dopo aver corretto la configurazione (ricorda: conoscenza appena salvata può
impiegare fino a 5 minuti per arrivare alle chat aperte); cambio totale di argomento.
**Dopo il Reset riscegli il contesto** (*Scegli ora*), soprattutto in *Documenti → Conversazione
+ dati* che senza contesto non parte.

**Reset e Documenti**: in Documenti agisce sulla parte dati; le domande precedenti sui documenti
continuano a fare da contesto (si ricostruiscono dai messaggi salvati): per ripartire da zero anche
sui documenti archivia i messaggi o apri una chat nuova. **Nella chat web il Reset non c'è.**
