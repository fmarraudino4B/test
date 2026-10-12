# Chat web (ChatWeb 1.2.10, WebProxy, tunnel)

Fonte: guida ottobre 2026, cap. 10. La chat web è ThinkAI nel browser: stesse credenziali di
MAUI, nessuna installazione. Il Backend resta nella rete del cliente e **non si apre verso
Internet**: è lui a collegarsi al **proxy** ThinkAI con un canale sicuro (il *tunnel*); il browser
parla solo col proxy. Con la 3.1 si allinea a MAUI su Documenti, contesti e dashboard.

## Cosa cambia per chi la usa (tutto uguale a MAUI)

| Area | Novità |
|---|---|
| Documenti → Ricerca | Scheda risultati in stile MAUI: nomi leggibili, anteprima, filtro, Mostra altri, Scarica, Analizza con ThinkAI |
| Documenti → Conversazione + dati | Terzo tipo anche in chat web, con stato dei dati e fonti (cap. 8.5) |
| Risposte sui Documenti formattate | Titoli, grassetti, elenchi e tabelle formattati, non più `###` e `**` |
| Contesti | Chi non è admin vede **solo i contesti autorizzati**. Tipologie disattivate non compaiono; l'admin le vede in grigio, non selezionabili |
| Dashboard e relazioni | Grafici e icone ridisegnati con le librerie aggiornate; risposte **Standard** e **Rapida** crescono col contenuto, senza cornice fissa |
| Passaggi del sistema | Striscia chiusa fra domanda e risposta; si apre con un clic |
| Stampa in PDF | Anche sulle risposte dei Documenti (solo quel messaggio) |
| Orari | Progetti, storico e raggruppamento per giorno (Oggi, Ieri) in **ora italiana** (prima indietro di 1–2 ore) |

**Restano solo in MAUI**: il **Reset** (non disponibile in chat web) e le funzioni di
configurazione (Impostazioni Analisi, Configuratore, Preferenze Viste). Si configura in MAUI, si
usa anche dal browser. **Fonti dei Documenti**: nella chat web non mostrano il percorso del file;
**Scarica** e **Analizza** usano un riferimento **firmato**, valido solo per quella risposta e quell'utente.

## Accesso, sessione, licenza

| Situazione | Cosa vede l'utente |
|---|---|
| Sessione scaduta | Login con «La sessione è scaduta: accedi di nuovo.» (prima restava sulla pagina con errori «null») |
| Licenza sospesa o scaduta | Controllata all'apertura e **ogni 5 minuti**, come in MAUI: la sessione si chiude e il login lo spiega |
| Server dell'azienda spento/irraggiungibile | All'accesso «Servizio non raggiungibile» con **Riprova**; in chat «Il server della tua azienda non risponde in questo momento: riprova tra qualche minuto.» |
| File da scaricare troppo grande | Il messaggio del server, non un codice HTTP |

La chat web ora gira **tutta nel browser**: ogni utente ha la sua sessione col proxy (prima la
prima visita passava dal server della chat web e due persone entrate a poca distanza potevano
scollegarsi a vicenda). Il pulsante **Entra** resta su «Un momento…» per un paio di secondi.

## Per chi installa: tunnel con chiave derivata

Ogni Backend si presenta al proxy col suo **identificativo** e la sua **chiave di registrazione**.
Fino all'estate il proxy doveva conoscere una chiave per ogni cliente. Ora:

- il proxy custodisce **un solo segreto**, `Proxy:BackendRegistrationMasterKey`;
- la chiave di ogni Backend è **calcolata** da quel segreto e dal suo identificativo e arriva al
  Backend con la configurazione remota (ConfigurationManager, `ThinkAiProxy:RegistrationMasterKey`,
  lo stesso segreto);
- aggiungere un cliente **non richiede di toccare il proxy**; la chiave di un Backend non vale per
  l'identificativo di un altro e dalla chiave non si risale al segreto.

Il segreto del proxy e quello del ConfigurationManager devono essere **uguali**. Una chiave scritta
a mano per un singolo cliente continua a funzionare e **ha la precedenza** (per cambiarla a un solo cliente).

> **WebProxy e Backend si aggiornano insieme.** Il proxy lascia passare solo le chiamate che
> conosce; la 3.1 ne usa due nuove (contesti autorizzati dell'utente e controllo della licenza):
> con Backend nuovo e proxy vecchio, chi non è amministratore trova **vuota la finestra dei contesti**.

**Verifica** — all'avvio del Backend, log a livello *Information*, entro pochi secondi:

```
Tunnel ChatWeb: connessione al proxy stabilita (...)
Tunnel ChatWeb: backend registrato sul proxy come <identificativo>
```

| Nel log del Backend | Causa probabile |
|---|---|
| «registrazione RIFIUTATA dal proxy. Motivo: Credenziali di registrazione non valida.» | Segreto del proxy ≠ quello del ConfigurationManager, oppure sul proxy il segreto manca (il log distingue i due casi). Spesso un aggiornamento del proxy ha sovrascritto `appsettings.json` con il segreto vuoto |
| «connessione al proxy fallita» | Proxy non raggiungibile dal server del cliente: indirizzo, firewall, certificato |
| Tunnel registrato ma le domande non arrivano | Il Backend non ascolta sulla porta in `ThinkAiProxy:BackendUrl` (devono coincidere) |
| Finestra dei contesti vuota per utenti normali | Proxy più vecchio del Backend: aggiornarli insieme |
