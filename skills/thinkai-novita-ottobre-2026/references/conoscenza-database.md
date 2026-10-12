# Impostazioni Analisi, conoscenza del database, misure nel testo, vocabolario

Fonte: guida ottobre 2026, capp. 2–5.

## 1. Impostazioni Analisi (menu ⋮ del progetto)

Definiscono le **tipologie di analisi** (i contesti che l'utente sceglie in ChatRoom: Vendite,
Crediti, Commesse, Magazzino…). Divisione dei compiti nuova: le informazioni sui dati (legami,
significato dei codici, regole) stanno nella **conoscenza del database** (una per database,
arriva all'AI a ogni domanda); nelle Impostazioni Analisi resta ciò che è proprio della
tipologia: **quali analisi fare e come mostrarle**.

Maschera: a sinistra ricerca (*Cerca tipologia…*), *Aggiungi nuova tipologia*, *Importa da JSON*,
elenco *Tipologie Configurate*; su ogni tipologia: Modifica, Esporta JSON, Attiva/Disattiva,
Elimina (una tipologia disattivata resta salvata ma non compare fra i contesti). A destra 4
schede: **Generale**, **Dashboard**, **Permessi & Avanzate**, **Vista**.

| Campo (scheda Generale) | Contenuto | Quando lo tocchi |
|---|---|---|
| Tipologia Analisi | Nome del contesto visto in chat | Alla creazione |
| Prompt Personalizzato | Istruzioni per la **Dashboard** (cosa leggere, quali analisi, come presentare; qui anche regole di accesso HARD/SOFT) | Per ritoccare il risultato del Configuratore |
| Prompt Personalizzato Relazione | Come sopra, per la **Relazione** | Come sopra |
| Prompt Chat | Cosa l'AI riceve in **Conversazione** e in **Documenti → Conversazione + dati**: significato dei dati del contesto (campi, regole, sinonimi, esempi di query), senza compiti e formato dashboard | Se vuoto e la tipologia è nata dal Configuratore si ricava da solo; **Ricava con AI** lo estrae dal prompt dashboard; **Aggiorna con AI** lo riallinea quando l'avviso giallo dice che è rimasto indietro |
| Escludi System Prompt | Dashboard e Relazione ricevono solo i tuoi prompt | Il Configuratore lo attiva da solo; se scrivi a mano devi indicare formato, librerie, struttura |
| Ricerca web | L'AI può cercare sul web con un prompt dedicato | Solo se serve davvero un dato esterno |

## 2. Il Configuratore in quattro passi

Si apre dal pulsante **Configuratore** delle Impostazioni Analisi (salva la tipologia). Aperto
dalla ChatRoom (*Seleziona contesto → Configura nuova analisi*) vale **solo per la sessione**.
Conoscenza, regole delle misure e vocabolario si salvano con i loro pulsanti, da qualunque punto.

1. **Tabelle** — scegli viste/tabelle (filtro Solo Viste / Tabelle / Tutte); *Note per l'AI*
   (ciò che sai e che i dati non dicono); stato della Conoscenza del database. **Genera Modello
   AI**: misura i legami sui dati (1–2 minuti), usa solo legami provati.
2. **Analisi** — descrizione e tipi di analisi (Temporale, per Cliente, per Articolo…); riquadro
   grigio con i legami provati (es. «27 legami provati sui dati (2 deboli, 48 s)»); **conoscenza
   e domande** (Domande per chi usa il gestionale, testo conoscenza, Misure nel testo,
   Vocabolario, Regole insegnate).
3. **Metriche e Filtri** — metriche (Fatturato Totale, Quantità, Numero Clienti…) e filtri
   predefiniti (Anno, Mese, Periodo, Causale Documento…).
4. **Output** — formato (Relazione o Dashboard), stile, **libreria grafici (una sola)**, tipi di
   grafico e tabella, struttura. **Salva e Applica** salva l'analisi e i tre prompt (Chat,
   Dashboard, Relazione). **Non saltare il passo 4.**

Esporta/Importa Configurazione dal Configuratore; *Importa da file* per la conoscenza.

## 3. La conoscenza del database

Testo in italiano, **una per database** (non di una chat/tipologia). Perché: una correzione vale
ovunque (chat già aperte la vedono entro ~5 min); prompt corti (all'AI arriva solo la parte che
riguarda le **tabelle del contesto scelto** + regole generali); ogni legame ha la sua prova.
Vale per Conversazione, Dashboard, Relazione, correzioni automatiche delle query e agenti Workforce.

Sezioni fisse:

| Sezione | Contiene |
|---|---|
| Concetti chiave | Entità del gestionale in una riga |
| Legami e join | Legame con SQL del join, condizione, prova. **Forti** = provati; **deboli** = marcati e usati solo se confermati |
| Regole | Calcoli, date, cosa unire **solo su richiesta**, regole che cambiano nel tempo |
| Codici | Valore → significato; dove manca: **[da confermare]** |
| Dati nel testo libero | Misure/codici/parametri scritti in descrizioni e note |
| Controlli finali | Errori da non fare, in forma di domanda che l'AI si pone prima di rispondere |

Esempio (illustrativo, dalla guida):

```
## Legami e join
### Legami forti (provati sui dati)
- FATT_CLI_RIGHE → FATT_CLI
  JOIN FATT_CLI F ON F.ANNO = R.ANNO AND F.NUM_DOC = R.NUM_DOC
  Prova: 100% delle righe trova la testata.
### Legami deboli (solo se confermati)
- FATT_CLI_RIGHE → ARTICOLI su COD_ART: 92% (righe descrittive senza articolo).
  Usare LEFT JOIN, mai INNER JOIN: l'INNER perderebbe le righe descrittive.
```

**Cosa trova l'AI da sola** (Genera Modello AI): legami anche senza chiavi esterne, la
condizione del legame («solo per i clienti, non per i fornitori»), legami deboli da confermare
(es. 72%), legami apparenti ma vuoti, colonne che non contengono ciò che il nome promette.
**Cosa controllare**: verso (righe→testata), condizione (clienti o fornitori?), tipo di join per
i deboli. Un legame debole con INNER JOIN fa sparire righe in silenzio.

**Codici**: l'AI non può ricavarli dai dati; li scrive con `[da confermare]` e li mette fra le
*Domande per chi usa il gestionale*.

**Le date nelle query** sono sempre `'YYYYMMDD'` (es. `DATA_DOC >= '20250101'`): regola di
sistema, il SQL Server del cliente può essere in italiano o inglese. Non scriverla nella conoscenza.

### Come si crea, in tre mosse

1. **Genera** (passo 1 → Genera Modello AI).
2. **Correggi e completa** con chi usa il gestionale (passo 2): rispondi alle *Domande per chi usa
   il gestionale* (max dieci) → **Rigenera con le risposte** (le risposte entrano in note e
   conoscenza, le domande chiuse spariscono); sistema i `[da confermare]`; aggiungi regole che
   conosci solo tu; **Espandi** per la finestra grande.
3. **Salva sul database** (Admin e SystemAdmin; autore e data registrati).

### Aggiungere un contesto su altre tabelle

Il Configuratore rilegge la conoscenza e propone **solo ciò che manca**, in coda, sotto
«Aggiunte del …». Il testo già salvato **non viene riscritto**: lo cambia solo chi lo modifica a mano.

### Importare, esportare, lavorare in più persone

- **Importa da file** (`.xml`, `.md`, `.txt`): aggiunto in coda; controllalo prima di salvare
  (ciò che salvi è considerato *confermato*).
- **Esporta** → file `.thinkai.json` con conoscenza, regole delle misure, vocabolario e regole
  insegnate per tutti. Su altra installazione: Configuratore → **Importa da file**: regole,
  vocabolario e regole insegnate si salvano subito (stessa famiglia/termine/regola nello stesso
  contesto: aggiornati; altri: aggiunti); il testo della conoscenza finisce nella casella perché
  lo controlli e lo salvi. **Le misure estratte non viaggiano nel file**: dopo l'importazione
  premi **Estrai su tutta la tabella**.
- **Due persone insieme**: se un altro salva mentre scrivi, il tuo *Salva sul database* mostra un
  avviso con nome e ora; il tuo testo resta nella casella (per ripartire dalla sua versione:
  chiudi e riapri; per sostituirla con la tua: salva di nuovo).
- Percorso tipico: costruire su copia del DB → provare → **Esporta** → **Importa** sul DB del
  cliente. Importa solo su Backend con **stessa versione o successiva**.

## 4. Regole delle misure nel testo

Problema: le misure stanno nella descrizione («CP2021 540 x 1500, 3200 - 40°»); `LIKE '%3000%'`
trova la 3500 e perde la 3200. Le regole leggono i numeri e li salvano come **misure vere**,
confrontabili. Riquadro **Misure nel testo** (passo 2, sotto conoscenza e domande).

### Quattro mosse

1. **Scegli la colonna di testo** (l'elenco propone quelle con numeri, es. `ARTICOLI.DES_ART —
   96.830 righe con numeri`) e la **Colonna chiave** (es. `COD_ART`; serve se la tabella non ha PK).
2. **Proponi le regole con AI**: legge un campione di 2.000 righe, le raggruppa per **famiglia di
   prodotto** (la parola con cui la descrizione comincia: CP, PA, N-CPR…) e propone per ciascuna
   formato in parole, campi con unità, sinonimi, varianti (~1 minuto).
3. **Controlla e conferma**: per ogni regola vedi *come legge gli esempi* e quante righe della
   famiglia legge nel campione; gli **avvisi** segnalano valori zero, copertura bassa, campi senza
   gruppo. Correggi nomi, sinonimi, varianti; spunta **confermata** → **Salva le regole**.
4. **Estrai su tutta la tabella**: le regole confermate leggono tutta la colonna; i numeri vanno
   in una tabella delle misure **nel database di ThinkAI — niente scritture sul gestionale**
   (~mezzo minuto ogni 100.000 righe; es. «115.445 righe lette, 57.767 con misure»).

### Una regola nel dettaglio (famiglia CP, «CP2021 540 x 1500, 3200 - 40°»)

| Elemento | Valore |
|---|---|
| Famiglia | CP |
| Varianti | CP2021, CP 2021, CP21, CPT2021 (entrano anche nel vocabolario) |
| Formato in parole | larghezza x piano inferiore, tratto inclinato - angolo |
| Campi | larghezza (mm), piano_inferiore (mm), tratto_inclinato (mm), angolo (°) |
| Sinonimi | tratto_inclinato: *tratto inclinato, piano inclinato, salita* |
| Espressione regolare | scritta dall'AI; correggibile a mano |

Se una riga è letta male correggi prima **varianti e campi**; la regex solo se sai scriverla. Una
regola che legge bene l'80% della famiglia è già utile: le righe non lette restano fuori dal
confronto numerico ma non sono lette in modo sbagliato.

### Da quel momento: le domande

Se la domanda ha un numero su uno di quei campi, l'AI riceve l'elenco delle righe che soddisfano
**davvero** la condizione (confronto numerico) al posto della ricerca di testo; se c'è il nome
della famiglia («CP21») la condizione vale solo per quella. La risposta lo dice nella riga **Ho
cercato**. Vale in Conversazione, Dashboard, Relazione e nella correzione delle query.

| Domanda | Lettura |
|---|---|
| «commesse CP21 con tratto inclinato oltre 3000» | famiglia CP, tratto_inclinato > 3000 |
| «larghezza tra 500 e 600» | 500 ≤ larghezza ≤ 600 (estremi compresi) |
| «altezza fino a 1000» | altezza ≤ 1000 |
| «oltre 3 metri», «oltre 300 cm» | 3000 (metri e cm → mm) |
| «lunghezza totale oltre 8 metri» (anche sviluppo, totale dei tratti) | somma dei tratti letti dal testo (senza larghezza, altezza, diametro, passo, spessore) > 8000 |
| «velocità oltre 20 m/min» | velocità > 20, in metri al minuto (non diventa 20.000) |

### Una regola per tutte le famiglie: `TUTTE`

Per misure con la stessa forma in ogni famiglia (es. «Velocità fissa ~ 32 m/min» nelle note
tecniche): scrivi **TUTTE** nella casella Famiglia (con *+ regola a mano* se l'AI non l'ha
proposta). Legge tutte le righe della colonna oltre alla regola della famiglia; le misure
trovate restano **della famiglia della riga**. «PA con velocità oltre 20 m/min» = famiglia PA +
velocità > 20. `TUTTE` non va scritto nelle domande. (Richiede Backend ≥ 3.1.)

### Quando si rifà, e chi può

- **Ogni notte alle tre** il sistema conta le righe con numeri di ogni colonna estratta: se il
  numero è cambiato, o l'ultima estrazione ha più di 7 giorni, **riestrae da solo** con le regole
  confermate (lo stato mostra data e se *automatica*).
- Se cambi una regola: salva e **Estrai su tutta la tabella** senza aspettare la notte. Dopo
  un'importazione della conoscenza lancia l'estrazione a mano **una volta**.
- Proporre, confermare, estrarre: **Admin e SystemAdmin**; le misure le usano le domande di tutti.

## 5. Vocabolario del database

Lo stesso concetto è scritto in modi diversi (*diametro* = «diam.» = «Ø»; *sponde laterali* =
«sponde» = «guance»; *CP2021* = «CP 2021» = «CP21»). Il vocabolario raccoglie questi gruppi
**una volta per database**; da lì ogni ricerca di testo li usa tutti.

Costruzione (passo 2, sotto Misure nel testo): **Proponi con AI** (~mezzo minuto; legge le parole
e coppie più frequenti nelle descrizioni, colonne di testo della scoperta e delle misure) → per
ogni gruppo: **termine** (come lo direbbe chi fa le domande), **varianti** (come è scritto nei
dati), **tipo** (*termine* o *modello*), **nota**, colonna **Nei dati** (righe del campione per
variante) → correggi, aggiungi varianti/gruppi a mano, spunta **confermato** → **Salva il
vocabolario** (le chat aperte lo vedono entro ~5 min). Le varianti delle famiglie delle misure
entrano **da sole, già confermate**.

| Tieni | Scarta (rumore) |
|---|---|
| Abbreviazioni/simboli dello stesso concetto (diametro = diam. = ø) | Unità di misura (millimetri = mm) |
| Nomi alternativi dello stesso componente (guance = sponde) | Parole generiche (numero = nr., pezzo = pz) |
| Varianti di un modello (CP2021 = CP21) | Parole simili ma diverse (motore ≠ motoriduttore) |
| Il nome che usano gli utenti anche se nei dati non c'è | Gruppi che uniscono due famiglie di prodotto diverse |

**Uso**: la domanda che tocca un gruppo riceve **tutte** le varianti nei filtri di testo; varianti
dello stesso gruppo in **OR**, concetti diversi della domanda in **AND**. Una variante di più
parole trova anche testi con altre parole in mezzo (`LIKE '%testata%motrice%'`). Anche la ricerca
dei valori reali, quando l'AI non è sicura di come un valore è scritto, prova tutte le varianti.

```
Domanda: "commesse con guance in inox"
WHERE (DES_ART LIKE '%guance%' OR DES_ART LIKE '%sponde%' OR DES_ART LIKE '%laterali%')
  AND (DES_ART LIKE '%inox%' OR DES_ART LIKE '%acciaio%inossidabile%' OR DES_ART LIKE '%AISI 304%')
```

**Vocabolario e misure insieme**: «PA con guance in inox e larghezza oltre 600» → il vocabolario
porta *guance* e *inox* con tutte le varianti, le misure portano *larghezza > 600* sulla famiglia PA.
