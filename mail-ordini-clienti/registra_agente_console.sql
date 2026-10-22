-- Registra l'agente "Ordini Clienti da mail" nella Workforce Console (ThinkAI 3.1.0.10, cap. 12.7).
-- Prerequisito: script THINKAI-WF-LOG-SCHEMA.sql di ThinkAI gia' eseguito sul database del gestionale.
-- Rilanciabile: aggiorna la riga se esiste.
DECLARE @AgentCode   varchar(40)   = 'DEC_ORD_CLI_MAIL';      -- uguale a logAgentCode nella CONFIGURAZIONE del flusso
DECLARE @Descrizione nvarchar(250) = N'Ordini clienti da mail';
DECLARE @DocLabel    nvarchar(40)  = N'Ordine';
DECLARE @TipoFlusso  varchar(40)   = 'ORDINI_CLIENTI_MAIL';
DECLARE @ReprocessAgentId int      = 0;                         -- id Backend dell'agente dopo l'import: abilita "Rielabora"

DECLARE @ConfigJson nvarchar(max) = N'{
  "stati": ["IN_ELABORAZIONE","CREATO","CREATO_PARZIALE","REVISIONE","DUPLICATO","ERRORE_ERP","ERRORE_TECNICO"],
  "righe": true,
  "reprocessAgentId": ' + CAST(@ReprocessAgentId AS nvarchar(12)) + N',
  "cartelleFile": []
}';

MERGE dbo.THINKAI_WF_AGENTI AS t
USING (SELECT @AgentCode AS AGENT_CODE) AS s ON t.AGENT_CODE = s.AGENT_CODE
WHEN MATCHED THEN UPDATE SET
    DESCRIZIONE = @Descrizione, TIPO_FLUSSO = @TipoFlusso, DOC_LABEL = @DocLabel,
    ATTIVO = 1, CONFIG_JSON = @ConfigJson, UPDATED_AT_UTC = SYSUTCDATETIME()
WHEN NOT MATCHED THEN INSERT (AGENT_CODE, DESCRIZIONE, TIPO_FLUSSO, DOC_LABEL, ATTIVO, CONFIG_JSON)
    VALUES (@AgentCode, @Descrizione, @TipoFlusso, @DocLabel, 1, @ConfigJson);
