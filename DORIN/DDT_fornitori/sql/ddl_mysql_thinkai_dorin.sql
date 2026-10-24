/* =====================================================================
   DDL tabelle di appoggio del flusso "DOR DDT fornitori v1.2.3 MySQL"
   Database: quello della connessione dati WorkForce (database Target Cross di Dorin)
   Requisiti: MySQL 5.7+ (CHECK applicato solo da 8.0.16), InnoDB, utf8mb4.

   Colonne ricavate dal flusso (insert/update/select): il DDL originale Decox
   non e' nell'export. Tipi scelti per MySQL in modalita' strict, che rifiuta
   '' su INT/DECIMAL/DATE (SQL Server invece converte in 0 / 1900-01-01):
     - VARCHAR dove il flusso puo' passare stringa vuota o testo grezzo dell'AI
       (DATA_DDT 'AAAAMMGG', date ERP 'gg/mm/aaaa', QUANTITA/PREZZO del log righe);
     - numerici solo dove il flusso garantisce sempre un numero;
     - DATETIME(3) per i timestamp scritti da {nowIso} ('AAAA-MM-GG HH:MM:SS.mmm' UTC).
   Script idempotente: CREATE TABLE IF NOT EXISTS, nessun DROP.
   ===================================================================== */

CREATE TABLE IF NOT EXISTS THINKAI_DORIN_DDT_LOG (
  LOG_KEY              VARCHAR(255)  NOT NULL,
  FILE_CORRELATION_ID  VARCHAR(255)  NULL,
  AGENT_VERSION        VARCHAR(50)   NULL,
  FILE_NAME            VARCHAR(400)  NULL,
  FILE_SOURCE          VARCHAR(400)  NULL,
  STATO                VARCHAR(20)   NOT NULL,
  DATA_INIZIO_UTC      DATETIME(3)   NULL,
  DATA_FINE_UTC        DATETIME(3)   NULL,
  PIVA                 VARCHAR(30)   NULL,
  COD_CF               VARCHAR(30)   NULL,
  RAG_SOC              VARCHAR(250)  NULL,
  NUMERO_DDT           VARCHAR(100)  NULL,
  DATA_DDT             VARCHAR(8)    NULL COMMENT 'AAAAMMGG, vuota se la data non e'' stata estratta',
  CONFIDENZA           DECIMAL(6,4)  NULL,
  ESITO_VALIDAZIONE    VARCHAR(20)   NULL,
  ESITO_MOTIVO         TEXT          NULL,
  ERP_DDT_ID           VARCHAR(100)  NULL,
  CREAZIONE_PARZIALE   TINYINT       NULL,
  RIGHE_TOTALI         INT           NULL,
  RIGHE_RISOLTE        INT           NULL,
  RIGHE_SCARTATE       INT           NULL,
  ERROR_CODE           VARCHAR(80)   NULL,
  ERROR_DETAIL         TEXT          NULL,
  DETAIL_JSON          MEDIUMTEXT    NULL,
  CREATED_AT_UTC       DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3) COMMENT 'ora del server: usata solo per ordinare',
  UPDATED_AT_UTC       DATETIME(3)   NULL,
  PRIMARY KEY (LOG_KEY),
  KEY IX_DORIN_DDT_LOG_DUP (PIVA, NUMERO_DDT, DATA_DDT),
  CONSTRAINT CK_DORIN_DDT_LOG_STATO CHECK (STATO IN ('IN_ELABORAZIONE', 'CREATO', 'REVISIONE', 'ERRORE_ERP'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS THINKAI_DORIN_DDT_LOG_RIGHE (
  LOG_KEY              VARCHAR(255)  NOT NULL,
  RIGA_NUMERO          INT           NOT NULL,
  CODICE_FORNITORE     VARCHAR(255)  NULL,
  DESCRIZIONE          TEXT          NULL,
  COD_ART              VARCHAR(50)   NULL,
  MATCH_METHOD         VARCHAR(30)   NULL,
  STATO                VARCHAR(20)   NULL,
  UM                   VARCHAR(50)   NULL,
  QUANTITA             VARCHAR(50)   NULL COMMENT 'valore estratto, non normalizzato',
  PREZZO_UNITARIO      VARCHAR(50)   NULL COMMENT 'valore estratto, non normalizzato',
  PRIMARY KEY (LOG_KEY, RIGA_NUMERO)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS THINKAI_DORIN_ARTICOLI_PROFILO (
  ID                     INT           NOT NULL AUTO_INCREMENT,
  COD_CF                 VARCHAR(30)   NOT NULL,
  CODICE_FORNITORE_NORM  VARCHAR(100)  NOT NULL,
  CODICE_FORNITORE_RAW   VARCHAR(255)  NULL,
  COD_ART                VARCHAR(50)   NULL,
  MATCH_METHOD           VARCHAR(30)   NULL,
  CONFIDENCE             DECIMAL(6,4)  NULL,
  ORIGINE                VARCHAR(20)   NULL,
  VALIDATION_MODE        VARCHAR(20)   NULL,
  ATTIVO                 TINYINT       NOT NULL DEFAULT 1,
  LAST_USED_AT_UTC       DATETIME(3)   NULL,
  LAST_LOG_KEY           VARCHAR(255)  NULL,
  CREATED_BY             VARCHAR(50)   NULL,
  CREATED_AT_UTC         DATETIME(3)   NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  UPDATED_AT_UTC         DATETIME(3)   NULL,
  PRIMARY KEY (ID),
  UNIQUE KEY UX_DORIN_ART_PROF (COD_CF, CODICE_FORNITORE_NORM)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS THINKAI_DORIN_DDT_STAGING_TESTA (
  LOG_KEY              VARCHAR(255)  NOT NULL COMMENT 'docGroupId: nome file senza suffisso __pNNofMM',
  TIPO_DOCUMENTO       VARCHAR(20)   NULL,
  COD_CAUS_DOC         VARCHAR(20)   NULL,
  SERIE_DOC            VARCHAR(20)   NULL,
  DATA_DOC             VARCHAR(10)   NULL COMMENT 'gg/mm/aaaa (formato TcRestAPI)',
  COD_CF               VARCHAR(30)   NULL,
  COD_DEP              VARCHAR(20)   NULL,
  NUM_DDT_FOR          VARCHAR(100)  NULL,
  DATA_DDT_FOR         VARCHAR(10)   NULL COMMENT 'gg/mm/aaaa (formato TcRestAPI)',
  NOTE_STAMPA          TEXT          NULL,
  ORDINE_ID            VARCHAR(50)   NULL,
  STATO_SCRITTURA      VARCHAR(20)   NULL,
  DATA_PREP_UTC        DATETIME(3)   NULL,
  ULTIMA_RIGA_SCRITTA  INT           NOT NULL DEFAULT 0,
  TENTATIVI_SCRITTURA  INT           NOT NULL DEFAULT 0,
  PARTI_TOTALI         INT           NOT NULL DEFAULT 1,
  PRIMARY KEY (LOG_KEY)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS THINKAI_DORIN_DDT_STAGING_RIGHE (
  LOG_KEY              VARCHAR(255)  NOT NULL,
  RIGA_NUMERO          INT           NOT NULL,
  PARTE_NUMERO         INT           NOT NULL DEFAULT 1,
  COD_ART              VARCHAR(50)   NULL,
  DES_RIGA             TEXT          NULL,
  UM                   VARCHAR(20)   NULL,
  QUANT_RIGA           DECIMAL(18,6) NULL,
  PREZZO_LORDO_VU1     DECIMAL(18,6) NULL,
  SCONTO_1             DECIMAL(9,4)  NULL,
  SCONTO_2             DECIMAL(9,4)  NULL,
  ORD_RIGA_ID          VARCHAR(50)   NULL,
  ORD_DOC_ID           VARCHAR(50)   NULL,
  FLAG_RAGGRUPPATA     TINYINT       NULL,
  MATCH_METHOD         VARCHAR(30)   NULL,
  STATO_RIGA           VARCHAR(20)   NULL,
  SCRITTA              TINYINT       NOT NULL DEFAULT 0,
  PRIMARY KEY (LOG_KEY, RIGA_NUMERO)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
