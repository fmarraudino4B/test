/* =====================================================================
   SCOPERTA SCHEMA PER CONTROLLO FATTIBILITA' E SLOT SPEDIZIONE
   SOLA LETTURA: solo SELECT / WITH. Nessuna scrittura, nessun #tmp, nessun EXEC.

   Obiettivo: individuare sul DB del gestionale dove stanno
     - giacenze, impegnato, disponibilita' per deposito
     - ordini fornitore in arrivo (residuo + data consegna)
     - cicli di lavorazione e fasi con tempi di attraversamento
     - calendario festivi/chiusure e tempi di transito/vettori
   NON presuppone nomi di tabelle oltre a ART_ANA, ORD_CLI_RIGHE, ORD_FOR_RIGHE
   (gia' verificate in altre analisi). Tutto il resto e' cercato per pattern sul catalogo.

   Esecuzione (dal PC che vede il server; adattare server e database):
     sqlcmd -S <SERVER> -E -C -d <DATABASE> -i 01_scoperta_schema.sql -o output_scoperta.txt -s"|" -W

   Inviare l'output (anche anonimizzato) per la fase di specifica finale.
   Nessun dato di riga viene letto: solo struttura e conteggi.
   ===================================================================== */

-- ===== PASSO 0: verifica connessione ==================================
SELECT DB_NAME() AS db, @@SERVERNAME AS server;
GO

-- ===== PASSO 1: tabelle e viste candidate per pattern =================
SELECT t.TABLE_TYPE, t.TABLE_NAME
FROM INFORMATION_SCHEMA.TABLES t
WHERE t.TABLE_NAME LIKE '%CICL%'
   OR t.TABLE_NAME LIKE '%FASE%'
   OR t.TABLE_NAME LIKE '%FASI%'
   OR t.TABLE_NAME LIKE '%LAV%'
   OR t.TABLE_NAME LIKE '%PROD%'
   OR t.TABLE_NAME LIKE '%DIST%'
   OR t.TABLE_NAME LIKE '%GIAC%'
   OR t.TABLE_NAME LIKE '%MAGAZ%'
   OR t.TABLE_NAME LIKE '%DEP%'
   OR t.TABLE_NAME LIKE '%IMPEG%'
   OR t.TABLE_NAME LIKE '%DISP%'
   OR t.TABLE_NAME LIKE '%PROGR%'
   OR t.TABLE_NAME LIKE '%CAL%'
   OR t.TABLE_NAME LIKE '%FEST%'
   OR t.TABLE_NAME LIKE '%VETT%'
   OR t.TABLE_NAME LIKE '%TRANS%'
   OR t.TABLE_NAME LIKE '%SPED%'
   OR t.TABLE_NAME LIKE '%LEAD%'
   OR t.TABLE_NAME LIKE '%ORD_FOR%'
   OR t.TABLE_NAME LIKE '%ORD_CLI%'
   OR t.TABLE_NAME LIKE 'ART[_]%'
ORDER BY t.TABLE_NAME;
GO

-- ===== PASSO 2: conteggio righe per tabella candidata (metadati) ======
SELECT s.name AS schema_name, o.name AS table_name, SUM(p.row_count) AS righe
FROM sys.dm_db_partition_stats p
JOIN sys.objects o ON o.object_id = p.object_id AND o.type = 'U'
JOIN sys.schemas s ON s.schema_id = o.schema_id
WHERE p.index_id IN (0, 1)
  AND (o.name LIKE '%CICL%' OR o.name LIKE '%FASE%' OR o.name LIKE '%FASI%' OR o.name LIKE '%LAV%'
    OR o.name LIKE '%GIAC%' OR o.name LIKE '%MAGAZ%' OR o.name LIKE '%DEP%' OR o.name LIKE '%IMPEG%'
    OR o.name LIKE '%DISP%' OR o.name LIKE '%PROGR%' OR o.name LIKE '%CAL%' OR o.name LIKE '%FEST%'
    OR o.name LIKE '%VETT%' OR o.name LIKE '%TRANS%' OR o.name LIKE '%SPED%' OR o.name LIKE '%LEAD%'
    OR o.name LIKE 'ORD_FOR%' OR o.name LIKE 'ORD_CLI%' OR o.name LIKE 'ART[_]%')
GROUP BY s.name, o.name
ORDER BY o.name;
GO

-- ===== PASSO 3: colonne delle tabelle candidate ========================
SELECT c.TABLE_NAME, c.ORDINAL_POSITION, c.COLUMN_NAME, c.DATA_TYPE,
       c.CHARACTER_MAXIMUM_LENGTH AS lung, c.NUMERIC_PRECISION AS prec, c.NUMERIC_SCALE AS scala,
       c.IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS c
JOIN INFORMATION_SCHEMA.TABLES t ON t.TABLE_NAME = c.TABLE_NAME AND t.TABLE_TYPE = 'BASE TABLE'
WHERE t.TABLE_NAME LIKE '%CICL%' OR t.TABLE_NAME LIKE '%FASE%' OR t.TABLE_NAME LIKE '%FASI%'
   OR t.TABLE_NAME LIKE '%LAV%' OR t.TABLE_NAME LIKE '%GIAC%' OR t.TABLE_NAME LIKE '%MAGAZ%'
   OR t.TABLE_NAME LIKE '%DEP%' OR t.TABLE_NAME LIKE '%IMPEG%' OR t.TABLE_NAME LIKE '%DISP%'
   OR t.TABLE_NAME LIKE '%PROGR%' OR t.TABLE_NAME LIKE '%FEST%' OR t.TABLE_NAME LIKE '%VETT%'
   OR t.TABLE_NAME LIKE '%TRANS%' OR t.TABLE_NAME LIKE '%SPED%' OR t.TABLE_NAME LIKE '%LEAD%'
ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION;
GO

-- ===== PASSO 4: colonne note per quantita'/date nelle tabelle gia' note =
SELECT c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE, c.CHARACTER_MAXIMUM_LENGTH AS lung, c.NUMERIC_PRECISION AS prec, c.NUMERIC_SCALE AS scala
FROM INFORMATION_SCHEMA.COLUMNS c
WHERE c.TABLE_NAME IN ('ART_ANA', 'ORD_CLI_RIGHE', 'ORD_FOR_RIGHE')
  AND (c.COLUMN_NAME LIKE '%QT%' OR c.COLUMN_NAME LIKE '%QUANT%' OR c.COLUMN_NAME LIKE '%DATA%'
    OR c.COLUMN_NAME LIKE '%DT_%' OR c.COLUMN_NAME LIKE '%CONS%' OR c.COLUMN_NAME LIKE '%EVAS%'
    OR c.COLUMN_NAME LIKE '%RES%' OR c.COLUMN_NAME LIKE '%DEP%' OR c.COLUMN_NAME LIKE '%FLAG%'
    OR c.COLUMN_NAME LIKE '%LEAD%' OR c.COLUMN_NAME LIKE '%GG%' OR c.COLUMN_NAME LIKE '%CICL%'
    OR c.COLUMN_NAME LIKE '%PROD%' OR c.COLUMN_NAME LIKE '%ACQ%')
ORDER BY c.TABLE_NAME, c.COLUMN_NAME;
GO

-- ===== PASSO 5: colonne con nome indicativo in QUALSIASI tabella ======
SELECT c.TABLE_NAME, c.COLUMN_NAME, c.DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS c
JOIN INFORMATION_SCHEMA.TABLES t ON t.TABLE_NAME = c.TABLE_NAME AND t.TABLE_TYPE = 'BASE TABLE'
WHERE c.COLUMN_NAME LIKE '%GIAC%' OR c.COLUMN_NAME LIKE '%IMPEG%' OR c.COLUMN_NAME LIKE '%DISPON%'
   OR c.COLUMN_NAME LIKE '%LEAD%' OR c.COLUMN_NAME LIKE '%ATTRAV%' OR c.COLUMN_NAME LIKE '%TEMPO%'
   OR c.COLUMN_NAME LIKE '%DT_CONS%' OR c.COLUMN_NAME LIKE '%DATA_CONS%' OR c.COLUMN_NAME LIKE '%DATA_PREV%'
   OR c.COLUMN_NAME LIKE '%GG_TRANS%' OR c.COLUMN_NAME LIKE '%TRANSITO%'
ORDER BY c.TABLE_NAME, c.COLUMN_NAME;
GO

-- ===== PASSO 6: chiavi esterne delle tabelle candidate (relazioni) ====
SELECT fk.name AS fk, OBJECT_NAME(fk.parent_object_id) AS tabella_figlia,
       COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS colonna_figlia,
       OBJECT_NAME(fk.referenced_object_id) AS tabella_padre,
       COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS colonna_padre
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id = fk.object_id
WHERE OBJECT_NAME(fk.parent_object_id) LIKE '%CICL%' OR OBJECT_NAME(fk.parent_object_id) LIKE '%FASE%'
   OR OBJECT_NAME(fk.parent_object_id) LIKE '%GIAC%' OR OBJECT_NAME(fk.parent_object_id) LIKE '%IMPEG%'
   OR OBJECT_NAME(fk.parent_object_id) LIKE 'ORD_FOR%' OR OBJECT_NAME(fk.parent_object_id) LIKE 'ORD_CLI%'
ORDER BY tabella_figlia, fk;
GO

-- ===== PASSO 7: viste candidate (nomi) ================================
SELECT s.name AS schema_name, v.name AS vista
FROM sys.views v
JOIN sys.schemas s ON s.schema_id = v.schema_id
WHERE v.name LIKE '%GIAC%' OR v.name LIKE '%DISP%' OR v.name LIKE '%IMPEG%' OR v.name LIKE '%CICL%'
   OR v.name LIKE '%PROGR%' OR v.name LIKE '%PREV%'
ORDER BY v.name;
GO
