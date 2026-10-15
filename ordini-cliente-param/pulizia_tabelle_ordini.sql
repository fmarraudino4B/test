/* ============================================================================
   PULIZIA TABELLE DI APPOGGIO - Agente Ordine (prefisso <PREFISSO_TABELLE>)
   SQL Server, schema dbo, database TargetCross.

   SICUREZZA
   - Di default e' un'ANTEPRIMA: conta e mostra cosa verrebbe cancellato, poi fa ROLLBACK.
     Per cancellare davvero: @Conferma = 1.
   - Tutto in una transazione: o si cancella tutto o niente.
   - Non tocca MAI le tabelle del flusso DDT (DDT_LOG, DDT_STAGING_*), ne' ART_ANA / tabelle TargetCross.
   - <PREFISSO_TABELLE>ARTICOLI_PROFILO e' CONDIVISA col flusso DDT: non viene svuotata. Con @PulisciMemoria = 1
     si cancellano SOLO le righe la cui ultima scrittura e' un'elaborazione di questo flusso
     (LAST_CORRELATION_ID presente in ORDINI_LOG, ORIGINE = 'IMPORT', CREATED_BY = 'WORKFORCE_AUTO').
   - CLIENTI_PROFILO e' configurazione (causale/serie/deposito per fornitore): non si tocca salvo @PulisciProfili = 1.
   - Eseguire prima sul database di TEST. Fare un backup prima di una pulizia in produzione.

   PARAMETRI (modificare solo questo blocco)
   ============================================================================ */
SET NOCOUNT ON;
SET XACT_ABORT ON;

-- USE [NOME_DB_TARGETCROSS];            -- <<< scegliere il database (prima TEST)

DECLARE @Conferma         bit       = 0;      -- 0 = solo anteprima (rollback) | 1 = cancella davvero
DECLARE @PulisciLog       bit       = 1;      -- ORDINI_LOG + ORDINI_LOG_RIGHE
DECLARE @PulisciMemoria   bit       = 0;      -- righe ARTICOLI_PROFILO create da questo flusso (vedi sopra)
DECLARE @PulisciProfili   bit       = 0;      -- CLIENTI_PROFILO (configurazione!)
DECLARE @Dal              datetime2 = NULL;   -- solo log con DATA_INIZIO_UTC >= @Dal   (NULL = nessun limite)
DECLARE @Fino             datetime2 = NULL;   -- solo log con DATA_INIZIO_UTC <  @Fino  (NULL = nessun limite)

/* ============================================================================ */
IF OBJECT_ID(N'dbo.<PREFISSO_TABELLE>ORDINI_LOG', N'U') IS NULL
   OR OBJECT_ID(N'dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE', N'U') IS NULL
   OR OBJECT_ID(N'dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO', N'U') IS NULL
   OR OBJECT_ID(N'dbo.<PREFISSO_TABELLE>CLIENTI_PROFILO', N'U') IS NULL
    THROW 50001, N'Tabelle <PREFISSO_TABELLE>* non trovate: database o prefisso errati.', 1;

DECLARE @tutto bit = CASE WHEN @Dal IS NULL AND @Fino IS NULL THEN 1 ELSE 0 END;

-- log selezionati dalla finestra temporale
IF OBJECT_ID(N'tempdb..#log') IS NOT NULL DROP TABLE #log;
SELECT CORRELATION_ID INTO #log
FROM dbo.<PREFISSO_TABELLE>ORDINI_LOG
WHERE (@Dal  IS NULL OR DATA_INIZIO_UTC >= @Dal)
  AND (@Fino IS NULL OR DATA_INIZIO_UTC <  @Fino);

-- ===== ANTEPRIMA ============================================================
SELECT 'ORDINI_LOG (da cancellare)'        AS tabella, COUNT(*) AS righe FROM #log WHERE @PulisciLog = 1
UNION ALL
SELECT 'ORDINI_LOG_RIGHE (da cancellare)',
       (SELECT COUNT(*) FROM dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE r
         WHERE @PulisciLog = 1
           AND (r.CORRELATION_ID IN (SELECT CORRELATION_ID FROM #log)
                OR (@tutto = 1 AND r.CORRELATION_ID NOT IN (SELECT CORRELATION_ID FROM dbo.<PREFISSO_TABELLE>ORDINI_LOG))))
UNION ALL
SELECT 'ARTICOLI_PROFILO create dal flusso ordini (da cancellare)',
       (SELECT COUNT(*) FROM dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO p
         WHERE @PulisciMemoria = 1 AND p.ORIGINE = 'IMPORT' AND p.CREATED_BY = 'WORKFORCE_AUTO'
           AND p.LAST_CORRELATION_ID IN (SELECT CORRELATION_ID FROM #log))
UNION ALL
SELECT 'CLIENTI_PROFILO (da cancellare)',
       (SELECT COUNT(*) FROM dbo.<PREFISSO_TABELLE>CLIENTI_PROFILO WHERE @PulisciProfili = 1)
UNION ALL
SELECT 'ARTICOLI_PROFILO totali (NON toccate in blocco)', (SELECT COUNT(*) FROM dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO);

-- come e' composta la memoria, per capire chi l'ha scritta (ordine / DDT)
SELECT ORIGINE, CREATED_BY, COUNT(*) AS righe,
       SUM(CASE WHEN LAST_CORRELATION_ID IN (SELECT CORRELATION_ID FROM dbo.<PREFISSO_TABELLE>ORDINI_LOG) THEN 1 ELSE 0 END) AS ultima_scrittura_da_ordini
FROM dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO
GROUP BY ORIGINE, CREATED_BY
ORDER BY righe DESC;

-- ===== ESECUZIONE (in transazione) ==========================================
BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @nMem int = 0, @nRighe int = 0, @nLog int = 0, @nProf int = 0;

    -- 1) memoria articoli (prima del log: serve la correlazione)
    IF @PulisciMemoria = 1
    BEGIN
        DELETE p
        FROM dbo.<PREFISSO_TABELLE>ARTICOLI_PROFILO p
        WHERE p.ORIGINE = 'IMPORT' AND p.CREATED_BY = 'WORKFORCE_AUTO'
          AND p.LAST_CORRELATION_ID IN (SELECT CORRELATION_ID FROM #log);
        SET @nMem = @@ROWCOUNT;
    END;

    -- 2) log righe, 3) log testate
    IF @PulisciLog = 1
    BEGIN
        DELETE r
        FROM dbo.<PREFISSO_TABELLE>ORDINI_LOG_RIGHE r
        WHERE r.CORRELATION_ID IN (SELECT CORRELATION_ID FROM #log)
           OR (@tutto = 1 AND r.CORRELATION_ID NOT IN (SELECT CORRELATION_ID FROM dbo.<PREFISSO_TABELLE>ORDINI_LOG));
        SET @nRighe = @@ROWCOUNT;

        DELETE l
        FROM dbo.<PREFISSO_TABELLE>ORDINI_LOG l
        WHERE l.CORRELATION_ID IN (SELECT CORRELATION_ID FROM #log);
        SET @nLog = @@ROWCOUNT;
    END;

    -- 4) profili fornitore (configurazione)
    IF @PulisciProfili = 1
    BEGIN
        DELETE FROM dbo.<PREFISSO_TABELLE>CLIENTI_PROFILO;
        SET @nProf = @@ROWCOUNT;
    END;

    SELECT @nLog AS ordini_log_cancellati, @nRighe AS ordini_log_righe_cancellate,
           @nMem AS memoria_articoli_cancellata, @nProf AS profili_cancellati,
           CASE WHEN @Conferma = 1 THEN 'COMMIT' ELSE 'ROLLBACK (anteprima)' END AS esito;

    IF @Conferma = 1
    BEGIN
        COMMIT TRANSACTION;
        PRINT N'OK: pulizia eseguita.';
    END
    ELSE
    BEGIN
        ROLLBACK TRANSACTION;
        PRINT N'ANTEPRIMA: nessuna modifica. Impostare @Conferma = 1 per cancellare.';
    END;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
    THROW;
END CATCH;

IF OBJECT_ID(N'tempdb..#log') IS NOT NULL DROP TABLE #log;
