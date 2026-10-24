/* =====================================================================
   VERIFICA PREREQUISITI MySQL - flusso "DOR DDT fornitori v1.2.3 MySQL"
   SOLA LETTURA: solo SELECT / SHOW. Nessuna scrittura.

   Esecuzione (con lo stesso utente della connessione dati WorkForce):
     mysql -h <HOST> -u <UTENTE_WORKFORCE> -p <DB_TARGET_CROSS> < verifica_prerequisiti_mysql.sql > esito_verifica.txt

   Restituire esito_verifica.txt: serve a chiudere i punti "DA VERIFICARE"
   di NOTE_MANUTENTORI_DOR_DDT.md (tipi, lunghezze, collation, spazi finali).
   ===================================================================== */

-- 1. Server e sessione: versione, sql_mode (strict?), sensibilita' maiuscole dei nomi tabella
SELECT VERSION() AS versione, DATABASE() AS db, @@sql_mode AS sql_mode,
       @@lower_case_table_names AS lower_case_table_names,
       @@character_set_database AS charset_db, @@collation_database AS collation_db,
       @@time_zone AS time_zone, @@system_time_zone AS system_time_zone;

-- 2. Permessi dell'utente WorkForce (servono SELECT su Target Cross, SELECT/INSERT/UPDATE sulle THINKAI_DORIN_*)
SHOW GRANTS FOR CURRENT_USER();

-- 3. Tabelle Target Cross lette dal flusso: nome reale (maiuscole!), engine, collation
SELECT TABLE_NAME, ENGINE, TABLE_COLLATION, TABLE_ROWS
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = DATABASE()
  AND UPPER(TABLE_NAME) IN ('CF', 'ORD_FOR', 'ORD_FOR_SPEC', 'ORD_FOR_RIGHE', 'ORD_FOR_RIGHE_SPEC',
                            'ART_ANA', 'DDT_FOR', 'DDT_FOR_RIGHE', 'CAUS_DOC_SERIE')
ORDER BY TABLE_NAME;

-- 4. Tabelle di appoggio del flusso (attese 5 dopo ddl_mysql_thinkai_dorin.sql)
SELECT TABLE_NAME, ENGINE, TABLE_COLLATION
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA = DATABASE() AND UPPER(TABLE_NAME) LIKE 'THINKAI!_DORIN!_%' ESCAPE '!'
ORDER BY TABLE_NAME;

-- 5. Colonne usate dal flusso: tipo, lunghezza, collation
SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, CHARACTER_MAXIMUM_LENGTH, COLLATION_NAME, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
  AND (   (UPPER(TABLE_NAME) = 'CF'                 AND COLUMN_NAME IN ('COD_CF', 'RAG_SOC_CF', 'P_IVA_CF', 'FLAG_FOR'))
       OR (UPPER(TABLE_NAME) = 'ORD_FOR'            AND COLUMN_NAME IN ('AZIENDA_ID', 'DOC_ID', 'NUM_DOC', 'ANNO_DOC'))
       OR (UPPER(TABLE_NAME) = 'ORD_FOR_SPEC'       AND COLUMN_NAME IN ('AZIENDA_ID', 'DOC_ID', 'NUMERO_CONFERMA'))
       OR (UPPER(TABLE_NAME) = 'ORD_FOR_RIGHE'      AND COLUMN_NAME IN ('AZIENDA_ID', 'DOC_ID', 'DOC_RIGA_ID', 'COD_CF', 'COD_ART', 'UM', 'PREZZO_LORDO_VU1', 'SCONTO_1', 'SCONTO_2'))
       OR (UPPER(TABLE_NAME) = 'ORD_FOR_RIGHE_SPEC' AND COLUMN_NAME IN ('AZIENDA_ID', 'DOC_ID', 'DOC_RIGA_ID', 'QUANT_DA_CONS_RIGA_UM_BASE'))
       OR (UPPER(TABLE_NAME) = 'ART_ANA'            AND COLUMN_NAME IN ('COD_ART', 'DES_ART'))
       OR (UPPER(TABLE_NAME) = 'DDT_FOR'            AND COLUMN_NAME IN ('DOC_ID', 'COD_CF', 'COD_CAUS_DOC', 'DATA_DOC'))
       OR (UPPER(TABLE_NAME) = 'DDT_FOR_RIGHE'      AND COLUMN_NAME IN ('DOC_ID', 'COD_ART', 'DES_RIGA'))
       OR (UPPER(TABLE_NAME) = 'CAUS_DOC_SERIE'     AND COLUMN_NAME IN ('COD_CAUS_DOC', 'SERIE')))
ORDER BY TABLE_NAME, COLUMN_NAME;

-- 6. Collation NO PAD (MySQL 8.0, es. utf8mb4_0900_ai_ci): 'ABC  ' <> 'ABC'.
--    Su MySQL 5.7 questa query fallisce (PAD_ATTRIBUTE non esiste): in quel caso tutte le collation sono PAD SPACE.
SELECT c.TABLE_NAME, c.COLUMN_NAME, c.COLLATION_NAME, k.PAD_ATTRIBUTE
FROM INFORMATION_SCHEMA.COLUMNS c
JOIN INFORMATION_SCHEMA.COLLATIONS k ON k.COLLATION_NAME = c.COLLATION_NAME
WHERE c.TABLE_SCHEMA = DATABASE()
  AND k.PAD_ATTRIBUTE = 'NO PAD'
  AND UPPER(c.TABLE_NAME) IN ('CF', 'ORD_FOR_RIGHE', 'ORD_FOR_SPEC', 'ART_ANA', 'DDT_FOR', 'CAUS_DOC_SERIE')
  AND c.COLUMN_NAME IN ('COD_CF', 'COD_ART', 'P_IVA_CF', 'COD_CAUS_DOC', 'NUMERO_CONFERMA');

-- 7. Spazi finali nelle chiavi confrontate con '=' (rilevanti solo con collation NO PAD)
SELECT 'ORD_FOR_RIGHE.COD_CF' AS colonna, COUNT(*) AS valori_con_spazi_finali FROM ORD_FOR_RIGHE WHERE CHAR_LENGTH(COD_CF) <> CHAR_LENGTH(RTRIM(COD_CF))
UNION ALL SELECT 'ORD_FOR_RIGHE.COD_ART', COUNT(*) FROM ORD_FOR_RIGHE WHERE CHAR_LENGTH(COD_ART) <> CHAR_LENGTH(RTRIM(COD_ART))
UNION ALL SELECT 'DDT_FOR.COD_CF', COUNT(*) FROM DDT_FOR WHERE CHAR_LENGTH(COD_CF) <> CHAR_LENGTH(RTRIM(COD_CF))
UNION ALL SELECT 'DDT_FOR.COD_CAUS_DOC', COUNT(*) FROM DDT_FOR WHERE CHAR_LENGTH(COD_CAUS_DOC) <> CHAR_LENGTH(RTRIM(COD_CAUS_DOC))
UNION ALL SELECT 'CAUS_DOC_SERIE.COD_CAUS_DOC', COUNT(*) FROM CAUS_DOC_SERIE WHERE CHAR_LENGTH(COD_CAUS_DOC) <> CHAR_LENGTH(RTRIM(COD_CAUS_DOC))
UNION ALL SELECT 'ART_ANA.COD_ART', COUNT(*) FROM ART_ANA WHERE CHAR_LENGTH(COD_ART) <> CHAR_LENGTH(RTRIM(COD_ART))
UNION ALL SELECT 'CF.P_IVA_CF', COUNT(*) FROM CF WHERE CHAR_LENGTH(P_IVA_CF) <> CHAR_LENGTH(RTRIM(P_IVA_CF));

-- 8. Valori di FLAG_FOR (il flusso riconosce il fornitore con FLAG_FOR = 1)
SELECT FLAG_FOR, COUNT(*) AS anagrafiche FROM CF GROUP BY FLAG_FOR;

-- 9. Causali DDT fornitore con serie (per compilare catalogoCausaliDestinazioneDdt)
SELECT COD_CAUS_DOC, SERIE FROM CAUS_DOC_SERIE ORDER BY COD_CAUS_DOC;

-- 10. Formato di DDT_FOR.DATA_DOC e ultimi documenti (recupero post-timeout per data)
SELECT DOC_ID, COD_CF, COD_CAUS_DOC, DATA_DOC FROM DDT_FOR ORDER BY DOC_ID DESC LIMIT 5;

-- 11. Formato di DOC_ID / NUM_DOC / ANNO_DOC degli ordini fornitore (riferimento ordine sui DDT)
SELECT o.DOC_ID, o.NUM_DOC, o.ANNO_DOC, s.NUMERO_CONFERMA
FROM ORD_FOR o LEFT JOIN ORD_FOR_SPEC s ON s.AZIENDA_ID = o.AZIENDA_ID AND s.DOC_ID = o.DOC_ID
ORDER BY o.DOC_ID DESC LIMIT 5;
