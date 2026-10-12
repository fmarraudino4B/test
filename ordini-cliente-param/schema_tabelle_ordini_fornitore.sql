/* ============================================================================
   Ordine Cliente PARAM v2.0.0 (ThinkAI WorkForce) - Tabelle di appoggio - SQL Server
   VARIANTE ORDINE FORNITORE: ARTICOLI_PROFILO con colonne CODICE_FORNITORE_NORM/RAW (come la memoria articoli del flusso DDT fornitori,
   con cui la tabella puo' essere condivisa). Derivato dallo script del flusso di riferimento v1.5.6, prefisso parametrico
   <PREFISSO_TABELLE> (compila con: python compila_profilo.py <profilo> --schema).

   Crea le 4 tabelle usate dal flusso, nello schema dbo del database TARGETCROSS
   del cliente (le query fanno join diretto con ART_ANA, quindi devono stare
   nello stesso database):

     <PREFISSO_TABELLE>CLIENTI_PROFILO   causale/serie/deposito/policy destinazione per cliente
     <PREFISSO_TABELLE>ARTICOLI_PROFILO  memoria autonoma codice cliente -> COD_ART
     <PREFISSO_TABELLE>ORDINI_LOG        audit per file elaborato (una riga per PDF)
     <PREFISSO_TABELLE>ORDINI_LOG_RIGHE  audit per riga ordine (dashboard anomalie)

   ATTENZIONE: se la tabella ARTICOLI_PROFILO esiste gia' (es. creata dal flusso DDT) lo script NON la modifica: verifica che abbia
   CODICE_FORNITORE_NORM / CODICE_FORNITORE_RAW e le 6 colonne di auto-learning.

   Caratteristiche
   - Idempotente: si puo' rieseguire; crea solo cio' che manca.
   - Aggiorna le installazioni vecchie: aggiunge le colonne che il preflight del
     flusso verifica (ARTICOLI_PROFILO: 6 colonne auto-learning; LOG_RIGHE: 2).
   - Tutto in una transazione: o si crea tutto o niente.
   - COD_CF e COD_ART copiano tipo e collation delle colonne TargetCross
     (CF_DEST_MERCE.COD_CF, ART_ANA.COD_ART): evita conversioni implicite nel join
     con ART_ANA e conflitti di collation.
   - Solo ASCII nei commenti, per evitare problemi di codifica in SSMS.

   Eseguire prima sul database di TEST, poi su quello di produzione.
   ============================================================================ */

SET NOCOUNT ON;
SET XACT_ABORT ON;
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;   -- richiesto dagli indici filtrati

-- USE [NOME_DB_TARGETCROSS];   -- <<< scegliere il database (prima TEST)

BEGIN TRY
    BEGIN TRANSACTION;

    ------------------------------------------------------------------------
    -- 0. Controlli preliminari: siamo sul database TargetCross?
    ------------------------------------------------------------------------
    IF OBJECT_ID(N'dbo.ART_ANA', N'U') IS NULL OR OBJECT_ID(N'dbo.CF_DEST_MERCE', N'U') IS NULL
        THROW 50001, N'Database errato: tabelle ART_ANA / CF_DEST_MERCE non trovate. Eseguire lo script sul database TargetCross del cliente.', 1;

    DECLARE @tCodCf  nvarchar(200);
    DECLARE @tCodArt nvarchar(200);
    DECLARE @sql     nvarchar(max);

    SELECT @tCodCf = c.DATA_TYPE
         + CASE WHEN c.CHARACTER_MAXIMUM_LENGTH IS NULL THEN N''
                WHEN c.CHARACTER_MAXIMUM_LENGTH = -1    THEN N'(max)'
                ELSE N'(' + CAST(c.CHARACTER_MAXIMUM_LENGTH AS nvarchar(10)) + N')' END
         + ISNULL(N' COLLATE ' + c.COLLATION_NAME, N'')
    FROM INFORMATION_SCHEMA.COLUMNS AS c
    WHERE c.TABLE_SCHEMA = N'dbo' AND c.TABLE_NAME = N'CF_DEST_MERCE' AND c.COLUMN_NAME = N'COD_CF';

    SELECT @tCodArt = c.DATA_TYPE
         + CASE WHEN c.CHARACTER_MAXIMUM_LENGTH IS NULL THEN N''
                WHEN c.CHARACTER_MAXIMUM_LENGTH = -1    THEN N'(max)'
                ELSE N'(' + CAST(c.CHARACTER_MAXIMUM_LENGTH AS nvarchar(10)) + N')' END
         + ISNULL(N' COLLATE ' + c.COLLATION_NAME, N'')
    FROM INFORMATION_SCHEMA.COLUMNS AS c
    WHERE c.TABLE_SCHEMA = N'dbo' AND c.TABLE_NAME = N'ART_ANA' AND c.COLUMN_NAME = N'COD_ART';

    IF @tCodCf IS NULL OR @tCodArt IS NULL
        THROW 50002, N'Colonna CF_DEST_MERCE.COD_CF o ART_ANA.COD_ART non trovata: impossibile derivare i tipi.', 1;

    ------------------------------------------------------------------------
    -- 1. <PREFISSO_TABELLE>CLIENTI_PROFILO
    --    Una riga ATTIVA per cliente. Senza riga il flusso usa i default dello
    --    step "Configurazione parametri" (defaultCausale/Serie/Deposito) e policy REVIEW.
    --    Piu' righe attive per lo stesso COD_CF = "Configurazione cliente duplicata"
    --    (il flusso manda l'ordine in revisione): l'indice univoco filtrato lo impedisce.
    --    DESTINATION_POLICY: 'REVIEW' (default) oppure 'WS_FIELDS' (unico valore che
    --    il flusso distingue: abilita i campi destinazione liberi via web service).
    ------------------------------------------------------------------------
    IF OBJECT_ID(N'dbo.<PREFISSO_TABELLE>CLIENTI_PROFILO', N'U') IS NULL
    BEGIN
        SET @sql = N'
        CREATE TABLE dbo.<PREFISSO_TABELLE>CLIENTI_PROFILO
        (
            ID                  bigint         IDENTITY(1,1) NOT NULL
                                CONSTRAINT PK_<PREFISSO_TABELLE>CLIENTI_PROFILO PRIMARY KEY,
            COD_CF              ' + @tCodCf + N' NOT NULL,
            COD_CAUS_DOC        nvarchar(30)   NULL,
            SERIE_DOC           nvarchar(30)   NULL,
            COD_DEP             nvarchar(30)   NULL,
            DESTINATION_POLICY  nvarchar(30)   NOT NULL
                                CONSTRAINT DF_<PREFISSO_TABELLE>CLIENTI_PROFILO_POLICY DEFAULT (N''REVIEW''),
            ATTIVO              bit            NOT NULL
                                CONSTRAINT DF_<PREFISSO_TABELLE>CLIENTI_PROFILO_ATTIVO DEFAULT (1),
            NOTE                nvarchar(1000) NULL,
            CREATED_AT_UTC      datetime2(3)   NOT NULL
                                CONSTRAINT DF_<PREFISSO_TABELLE>CLIENTI_PROFILO_CREATED DEFAULT (SYSUTCDATETIME())
        );
        CREATE UNIQUE NONCLUSTERED INDEX UX_<PREFISSO_TABELLE>CLIENTI_PROFILO_COD_CF
            ON dbo.<PREFISSO_TABELLE>CLIENTI_PROFILO (COD_CF) WHERE ATTIVO = 1;';
        EXEC sys.sp_executesql @sql;
    END;

    ------------------------------------------------------------------------
    -- 2. <PREFISSO_TABELLE>ARTICOLI_PROFILO  (memoria autonoma / auto-learning)
    --    Chiave logica: (COD_CF, CODICE_FORNITORE_NORM). Il flusso la tratta come
    --    univoca: una riga disattivata blocca il reinserimento e un duplicato e'
    --    "Memoria duplicata" (aggiornamento bloccato). L'unicita' lo rende impossibile.
    --    Il flusso consulta solo righe con ATTIVO = 1 AND APPROVATO = 1.
    --    APPROVATO ha default 0: una riga inserita a mano non e' usata finche' non
    --    viene approvata esplicitamente (il flusso scrive sempre APPROVATO = 1).
    ------------------------------------------------------------------------
    IF OBJECT_ID(N'dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO', N'U') IS NULL
    BEGIN
        SET @sql = N'
        CREATE TABLE dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO
        (
            ID                   bigint         IDENTITY(1,1) NOT NULL
                                 CONSTRAINT PK_<PREFISSO_TABELLE>ARTICOLI_PROFILO PRIMARY KEY,
            COD_CF               ' + @tCodCf + N' NOT NULL,
            CODICE_FORNITORE_NORM  nvarchar(200)  NOT NULL,
            CODICE_FORNITORE_RAW   nvarchar(200)  NULL,
            COD_ART              ' + @tCodArt + N' NOT NULL,
            APPROVATO            bit            NOT NULL
                                 CONSTRAINT DF_<PREFISSO_TABELLE>ARTICOLI_PROFILO_APPROVATO DEFAULT (0),
            ATTIVO               bit            NOT NULL
                                 CONSTRAINT DF_<PREFISSO_TABELLE>ARTICOLI_PROFILO_ATTIVO DEFAULT (1),
            ORIGINE              nvarchar(30)   NULL,
            MATCH_METHOD         nvarchar(50)   NULL,
            VALIDATION_MODE      nvarchar(50)   NULL,
            CONFIDENCE           decimal(9,4)   NULL,
            EVIDENCE_COUNT       int            NOT NULL
                                 CONSTRAINT DF_<PREFISSO_TABELLE>ARTICOLI_PROFILO_EVIDENCE DEFAULT (0),
            LAST_USED_AT_UTC     datetime2(3)   NULL,
            LAST_CORRELATION_ID  nvarchar(64)   NULL,
            NOTE                 nvarchar(1000) NULL,
            CREATED_BY           nvarchar(100)  NULL,
            CREATED_AT_UTC       datetime2(3)   NOT NULL
                                 CONSTRAINT DF_<PREFISSO_TABELLE>ARTICOLI_PROFILO_CREATED DEFAULT (SYSUTCDATETIME()),
            UPDATED_AT_UTC       datetime2(3)   NULL
        );
        CREATE UNIQUE NONCLUSTERED INDEX UX_<PREFISSO_TABELLE>ARTICOLI_PROFILO_CHIAVE
            ON dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO (COD_CF, CODICE_FORNITORE_NORM);';
        EXEC sys.sp_executesql @sql;
    END;

    -- Upgrade installazioni precedenti: colonne auto-learning verificate dal preflight.
    IF COL_LENGTH(N'dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO', N'MATCH_METHOD') IS NULL
        ALTER TABLE dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO ADD MATCH_METHOD nvarchar(50) NULL;
    IF COL_LENGTH(N'dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO', N'VALIDATION_MODE') IS NULL
        ALTER TABLE dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO ADD VALIDATION_MODE nvarchar(50) NULL;
    IF COL_LENGTH(N'dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO', N'CONFIDENCE') IS NULL
        ALTER TABLE dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO ADD CONFIDENCE decimal(9,4) NULL;
    IF COL_LENGTH(N'dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO', N'EVIDENCE_COUNT') IS NULL
        ALTER TABLE dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO ADD EVIDENCE_COUNT int NOT NULL
            CONSTRAINT DF_<PREFISSO_TABELLE>ARTICOLI_PROFILO_EVIDENCE DEFAULT (0);
    IF COL_LENGTH(N'dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO', N'LAST_USED_AT_UTC') IS NULL
        ALTER TABLE dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO ADD LAST_USED_AT_UTC datetime2(3) NULL;
    IF COL_LENGTH(N'dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO', N'LAST_CORRELATION_ID') IS NULL
        ALTER TABLE dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO ADD LAST_CORRELATION_ID nvarchar(64) NULL;

    ------------------------------------------------------------------------
    -- 3. <PREFISSO_TABELLE>ORDINI_LOG  (una riga per file/PDF elaborato)
    --    STATO: IN_ELABORAZIONE, CREATO, CREATO_PARZIALE, DUPLICATO, REVISIONE,
    --           ERRORE_ERP, ERRORE_TECNICO, CREATO_ERRORE_TECNICO
    --    CORRELATION_ID univoco: e' la chiave di tutti gli UPDATE del flusso
    --    (chiusura, esito email, errore tecnico).
    --    ERROR_DETAIL / EMAIL_ERRORE: il flusso li tronca a 3990 caratteri;
    --    il dettaglio completo e' in DETAIL_JSON.
    ------------------------------------------------------------------------
    IF OBJECT_ID(N'dbo.<PREFISSO_TABELLE>ORDINI_LOG', N'U') IS NULL
    BEGIN
        CREATE TABLE dbo.<PREFISSO_TABELLE>ORDINI_LOG
        (
            ID                     bigint         IDENTITY(1,1) NOT NULL
                                   CONSTRAINT PK_<PREFISSO_TABELLE>ORDINI_LOG PRIMARY KEY,
            CORRELATION_ID         nvarchar(64)   NOT NULL,
            AGENT_VERSION          nvarchar(50)   NULL,
            FILE_NAME              nvarchar(400)  NULL,
            FILE_SOURCE            nvarchar(1000) NULL,
            STATO                  nvarchar(30)   NOT NULL,
            DATA_INIZIO_UTC        datetime2(3)   NOT NULL,
            DATA_FINE_UTC          datetime2(3)   NULL,
            ERROR_CODE             nvarchar(100)  NULL,
            ERROR_DETAIL           nvarchar(4000) NULL,
            DETAIL_JSON            nvarchar(max)  NULL,
            PIVA                   nvarchar(32)   NULL,
            COD_CF                 nvarchar(30)   NULL,
            RAG_SOC                nvarchar(200)  NULL,
            NUMERO_ORDINE          nvarchar(100)  NULL,
            DATA_ORDINE            date           NULL,
            DESTINAZIONE_PRESENTE  bit            NULL,
            ERP_DOC_ID             nvarchar(50)   NULL,
            RIGHE_TOTALI           int            NULL,
            RIGHE_RISOLTE          int            NULL,
            RIGHE_ANOMALE          int            NULL,
            EMAIL_STATO            nvarchar(30)   NULL,
            EMAIL_ERRORE           nvarchar(4000) NULL,
            UPDATED_AT_UTC         datetime2(3)   NULL
        );
        CREATE UNIQUE NONCLUSTERED INDEX UX_<PREFISSO_TABELLE>ORDINI_LOG_CORRELATION
            ON dbo.<PREFISSO_TABELLE>ORDINI_LOG (CORRELATION_ID);
        -- "Chiudi log orfani": FILE_NAME + STATO = 'IN_ELABORAZIONE'
        CREATE NONCLUSTERED INDEX IX_<PREFISSO_TABELLE>ORDINI_LOG_FILE_STATO
            ON dbo.<PREFISSO_TABELLE>ORDINI_LOG (FILE_NAME, STATO);
        -- Dashboard/monitoraggio per stato e periodo
        CREATE NONCLUSTERED INDEX IX_<PREFISSO_TABELLE>ORDINI_LOG_STATO_DATA
            ON dbo.<PREFISSO_TABELLE>ORDINI_LOG (STATO, DATA_INIZIO_UTC DESC);
    END;

    ------------------------------------------------------------------------
    -- 4. <PREFISSO_TABELLE>ORDINI_LOG_RIGHE  (una riga per riga ordine, dashboard anomalie)
    --    Nessuna chiave univoca su (CORRELATION_ID, RIGA_NUMERO): le righe di un
    --    kit condividono il numero di riga del PDF.
    --    Nessuna FOREIGN KEY verso ORDINI_LOG: tabelle di audit, volutamente
    --    slegate (un errore sul log testata non deve bloccare le righe).
    --    MOTIVO e' nvarchar(max): per le righe senza motivo proprio il flusso
    --    scrive l'elenco dei motivi dell'intero ordine, che puo' superare 4000 car.
    ------------------------------------------------------------------------
    IF OBJECT_ID(N'dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE', N'U') IS NULL
    BEGIN
        SET @sql = N'
        CREATE TABLE dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE
        (
            ID                   bigint         IDENTITY(1,1) NOT NULL
                                 CONSTRAINT PK_<PREFISSO_TABELLE>ORDINI_LOG_RIGHE PRIMARY KEY,
            CORRELATION_ID       nvarchar(64)   NOT NULL,
            RIGA_NUMERO          int            NOT NULL,
            CODICE_CLIENTE_RAW   nvarchar(200)  NULL,
            CODICE_CLIENTE_NORM  nvarchar(200)  NULL,
            DESCRIZIONE          nvarchar(2000) NULL,
            COD_ART              ' + @tCodArt + N' NULL,
            MATCH_METHOD         nvarchar(50)   NOT NULL
                                 CONSTRAINT DF_<PREFISSO_TABELLE>ORDINI_LOG_RIGHE_METHOD DEFAULT (N''NON_ESEGUITO''),
            MATCH_CONFIDENCE     decimal(9,4)   NOT NULL
                                 CONSTRAINT DF_<PREFISSO_TABELLE>ORDINI_LOG_RIGHE_CONF DEFAULT (0),
            MATCH_EVIDENCE       nvarchar(2000) NULL,
            UM_ORDINE            nvarchar(20)   NULL,
            UM_TARGET            nvarchar(20)   NULL,
            QUANTITA_RAW         nvarchar(100)  NULL,
            QUANTITA_NORM        decimal(18,4)  NULL,
            PREZZO_RAW           nvarchar(100)  NULL,
            PREZZO_NORM          decimal(18,6)  NULL,
            STATO                nvarchar(30)   NOT NULL,
            MOTIVO               nvarchar(max)  NULL,
            CREATED_AT_UTC       datetime2(3)   NOT NULL
                                 CONSTRAINT DF_<PREFISSO_TABELLE>ORDINI_LOG_RIGHE_CREATED DEFAULT (SYSUTCDATETIME())
        );
        CREATE NONCLUSTERED INDEX IX_<PREFISSO_TABELLE>ORDINI_LOG_RIGHE_CORR_RIGA
            ON dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE (CORRELATION_ID, RIGA_NUMERO);
        CREATE NONCLUSTERED INDEX IX_<PREFISSO_TABELLE>ORDINI_LOG_RIGHE_STATO_DATA
            ON dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE (STATO, CREATED_AT_UTC DESC);';
        EXEC sys.sp_executesql @sql;
    END;

    -- Upgrade installazioni precedenti: colonne verificate dal preflight.
    IF COL_LENGTH(N'dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE', N'MATCH_CONFIDENCE') IS NULL
        ALTER TABLE dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE ADD MATCH_CONFIDENCE decimal(9,4) NOT NULL
            CONSTRAINT DF_<PREFISSO_TABELLE>ORDINI_LOG_RIGHE_CONF DEFAULT (0);
    IF COL_LENGTH(N'dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE', N'MATCH_EVIDENCE') IS NULL
        ALTER TABLE dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE ADD MATCH_EVIDENCE nvarchar(2000) NULL;

    COMMIT TRANSACTION;
    PRINT N'OK: tabelle di appoggio <PREFISSO_TABELLE> create/verificate.';
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;
GO

/* ============================================================================
   VERIFICA - stessa query del "Preflight tabelle profilo e log" del flusso.
   Risultato atteso: 1, 1, 1, 1, 6, 2
   ============================================================================ */
SELECT
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='<PREFISSO_TABELLE>CLIENTI_PROFILO')   AS CLIENT_PROFILE,
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='<PREFISSO_TABELLE>ARTICOLI_PROFILO')  AS ARTICLE_PROFILE,
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='<PREFISSO_TABELLE>ORDINI_LOG')        AS ORDER_LOG,
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='<PREFISSO_TABELLE>ORDINI_LOG_RIGHE')  AS ORDER_LOG_LINES,
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='<PREFISSO_TABELLE>ARTICOLI_PROFILO'
      AND COLUMN_NAME IN ('MATCH_METHOD','VALIDATION_MODE','CONFIDENCE','EVIDENCE_COUNT','LAST_USED_AT_UTC','LAST_CORRELATION_ID')) AS ARTICLE_PROFILE_AUTO_COLUMNS,
  (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA='dbo' AND TABLE_NAME='<PREFISSO_TABELLE>ORDINI_LOG_RIGHE'
      AND COLUMN_NAME IN ('MATCH_CONFIDENCE','MATCH_EVIDENCE')) AS ORDER_LOG_MATCH_COLUMNS;
GO

/* ============================================================================
   FACOLTATIVO - PERMESSI per l'utente SQL della credenziale usata dal flusso
   (sostituire <utente_thinkai>). Il flusso scrive solo sulle 4 tabelle e legge
   da ART_ANA, CF_DEST_MERCE, OFF_CLI, OFF_CLI_RIGHE, ORD_CLI_RIGHE,
   ORD_CLI_RIGHE_SPEC e dalle tabelle codici articolo usate dalle query.
   ============================================================================ */
-- GRANT SELECT, INSERT, UPDATE ON dbo.<PREFISSO_TABELLE>CLIENTI_PROFILO   TO [<utente_thinkai>];
-- GRANT SELECT, INSERT, UPDATE ON dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO  TO [<utente_thinkai>];
-- GRANT SELECT, INSERT, UPDATE ON dbo.<PREFISSO_TABELLE>ORDINI_LOG        TO [<utente_thinkai>];
-- GRANT SELECT, INSERT, UPDATE ON dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE  TO [<utente_thinkai>];

/* ============================================================================
   FACOLTATIVO - ESEMPIO di configurazione cliente (valori da sostituire).
   Senza riga il flusso usa i default dello step "Configurazione parametri".
   ============================================================================ */
-- INSERT INTO dbo.<PREFISSO_TABELLE>CLIENTI_PROFILO
--        (COD_CF, COD_CAUS_DOC, SERIE_DOC, COD_DEP, DESTINATION_POLICY, ATTIVO)
-- VALUES (N'<cod_cf>', N'<cod_caus_doc>', N'<serie_doc>', N'<cod_dep>', N'REVIEW', 1);

/* ============================================================================
   FACOLTATIVO - ROLLBACK. ATTENZIONE: cancella anche i dati (audit e memoria).
   ============================================================================ */
-- IF OBJECT_ID(N'dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE', N'U')  IS NOT NULL DROP TABLE dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE;
-- IF OBJECT_ID(N'dbo.<PREFISSO_TABELLE>ORDINI_LOG', N'U')        IS NOT NULL DROP TABLE dbo.<PREFISSO_TABELLE>ORDINI_LOG;
-- IF OBJECT_ID(N'dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO', N'U')  IS NOT NULL DROP TABLE dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO;
-- IF OBJECT_ID(N'dbo.<PREFISSO_TABELLE>CLIENTI_PROFILO', N'U')   IS NOT NULL DROP TABLE dbo.<PREFISSO_TABELLE>CLIENTI_PROFILO;
