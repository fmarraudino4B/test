#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adatta_mysql.py - deriva il flusso "DDT fornitori" per DORIN (Target Cross su MySQL)
dall'export ThinkAI WorkForce del flusso DECOX (Target Cross su SQL Server).

Sorgente (unica fonte di verita'): Flussi_Workforce/DECOX/DDT_fornitori/DEC_DDT_fornitori_v1.2.3.thinkaiagent.json
Il flusso Dorin e' un artefatto GENERATO: non si modifica a mano, si rigenera.

Ogni modifica e' chirurgica: cerca il testo originale esatto e verifica il numero di
occorrenze. Se l'export Decox cambia (nuova versione), lo script si ferma con un errore
invece di produrre un flusso a meta' convertito.

Uso:
  python adatta_mysql.py <DEC_DDT_fornitori_v1.2.3.thinkaiagent.json>
         [--profilo profilo-dorin.privato.json] [--out DOR_DDT_fornitori_v1.2.3-mysql.thinkaiagent.json]

Senza --profilo i valori cliente restano segnaposto "DA_CONFIGURARE_*": il passo
"Valida configurazione" del flusso blocca la run finche' non vengono compilati.
"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
VERSIONE_SORGENTE = "DEC DDT fornitori  v1.2.3"
VERSIONE_DERIVATA = "MY1"

# ---------------------------------------------------------------------------
# 1. Conversioni SQL Server -> MySQL dei nodi Query / SqlUpdate (testo esatto)
#    (campo, testo originale, testo MySQL, occorrenze attese)
# ---------------------------------------------------------------------------
SUB_MSSQL = "SELECT 1 FROM dbo.ORD_FOR_RIGHE_SPEC S WHERE S.AZIENDA_ID = R.AZIENDA_ID AND S.DOC_ID = R.DOC_ID AND S.DOC_RIGA_ID = R.DOC_RIGA_ID GROUP BY S.AZIENDA_ID, S.DOC_ID, S.DOC_RIGA_ID HAVING SUM(ISNULL(S.QUANT_DA_CONS_RIGA_UM_BASE, 0)) > 0"
SUB_MYSQL = "SELECT 1 FROM ORD_FOR_RIGHE_SPEC S WHERE S.AZIENDA_ID = R.AZIENDA_ID AND S.DOC_ID = R.DOC_ID AND S.DOC_RIGA_ID = R.DOC_RIGA_ID GROUP BY S.AZIENDA_ID, S.DOC_ID, S.DOC_RIGA_ID HAVING SUM(COALESCE(S.QUANT_DA_CONS_RIGA_UM_BASE, 0)) > 0"
RIF_MSSQL = "(R.DOC_ID LIKE {rigaRiferimentoOrdineLike} OR (O.NUM_DOC = CONVERT(int, {rigaRiferimentoNumDoc}) AND O.ANNO_DOC IN (CONVERT(int, {docAnno}), CONVERT(int, {docAnnoPrec}))))"
RIF_MYSQL = "(R.DOC_ID LIKE {rigaRiferimentoOrdineLike} OR (O.NUM_DOC = CAST({rigaRiferimentoNumDoc} AS SIGNED) AND O.ANNO_DOC IN (CAST({docAnno} AS SIGNED), CAST({docAnnoPrec} AS SIGNED))))"

SQL = [
    ("sql",
     "SELECT (SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME IN ({tabellaLog},{tabellaLogRighe},{tabellaArticoliProfilo})) AS TABELLE_TROVATE",
     "SELECT COUNT(*) AS TABELLE_TROVATE FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = DATABASE() AND UPPER(TABLE_NAME) IN ({tabellaLog},{tabellaLogRighe},{tabellaArticoliProfilo},{tabellaStagingTesta},{tabellaStagingRighe})",
     1),
    ("sql",
     "SELECT TOP 1 ISNULL(ERP_DDT_ID, '') AS ERP_DDT_ID, STATO FROM dbo.THINKAI_DECOX_DDT_LOG WHERE PIVA = {pivaMittente} AND NUMERO_DDT = {docNumero} AND DATA_DDT = {docDataSql} AND (STATO = 'CREATO' OR (ERP_DDT_ID IS NOT NULL AND LTRIM(RTRIM(ERP_DDT_ID)) NOT IN ('', '0'))) ORDER BY CREATED_AT_UTC DESC",
     "SELECT COALESCE(ERP_DDT_ID, '') AS ERP_DDT_ID, STATO FROM THINKAI_DORIN_DDT_LOG WHERE PIVA = {pivaMittente} AND NUMERO_DDT = {docNumero} AND DATA_DDT = {docDataSql} AND (STATO = 'CREATO' OR (ERP_DDT_ID IS NOT NULL AND TRIM(ERP_DDT_ID) NOT IN ('', '0'))) ORDER BY CREATED_AT_UTC DESC LIMIT 1",
     1),
    ("sql",
     "SELECT TOP 5 R.DOC_RIGA_ID AS RIGA_ID, R.COD_ART, R.DOC_ID AS ORD_DOC_ID FROM dbo.ORD_FOR_RIGHE R INNER JOIN dbo.ORD_FOR O ON O.AZIENDA_ID = R.AZIENDA_ID AND O.DOC_ID = R.DOC_ID WHERE R.COD_CF = {fornitoreCodCf} AND " + RIF_MSSQL + " AND EXISTS (" + SUB_MSSQL + ") ORDER BY R.DOC_ID DESC, R.DOC_RIGA_ID",
     "SELECT R.DOC_RIGA_ID AS RIGA_ID, R.COD_ART, R.DOC_ID AS ORD_DOC_ID FROM ORD_FOR_RIGHE R INNER JOIN ORD_FOR O ON O.AZIENDA_ID = R.AZIENDA_ID AND O.DOC_ID = R.DOC_ID WHERE R.COD_CF = {fornitoreCodCf} AND " + RIF_MYSQL + " AND EXISTS (" + SUB_MYSQL + ") ORDER BY R.DOC_ID DESC, R.DOC_RIGA_ID LIMIT 5",
     1),
    ("sql",
     "SELECT TOP 5 R.DOC_RIGA_ID AS RIGA_ID, R.COD_ART, R.DOC_ID AS ORD_DOC_ID FROM dbo.ORD_FOR_RIGHE R WHERE R.COD_CF = {fornitoreCodCf} AND EXISTS (SELECT 1 FROM dbo.ORD_FOR_SPEC SP WHERE SP.AZIENDA_ID = R.AZIENDA_ID AND SP.DOC_ID = R.DOC_ID AND RTRIM(SP.NUMERO_CONFERMA) LIKE {rigaRiferimentoConfermaLike}) AND EXISTS (" + SUB_MSSQL + ") ORDER BY R.DOC_ID DESC, R.DOC_RIGA_ID",
     "SELECT R.DOC_RIGA_ID AS RIGA_ID, R.COD_ART, R.DOC_ID AS ORD_DOC_ID FROM ORD_FOR_RIGHE R WHERE R.COD_CF = {fornitoreCodCf} AND EXISTS (SELECT 1 FROM ORD_FOR_SPEC SP WHERE SP.AZIENDA_ID = R.AZIENDA_ID AND SP.DOC_ID = R.DOC_ID AND RTRIM(SP.NUMERO_CONFERMA) LIKE {rigaRiferimentoConfermaLike}) AND EXISTS (" + SUB_MYSQL + ") ORDER BY R.DOC_ID DESC, R.DOC_RIGA_ID LIMIT 5",
     1),
    ("sql",
     "SELECT TOP 1 COD_ART FROM dbo.THINKAI_DECOX_ARTICOLI_PROFILO WHERE COD_CF = {fornitoreCodCf} AND CODICE_FORNITORE_NORM = {rigaCodiceFornitoreNorm} AND LEN({rigaCodiceFornitoreNorm}) > 0 AND ATTIVO = 1 AND ISNULL(MATCH_METHOD, '') NOT IN ('ORDINE_FOR', 'ORDINE_FOR_CONFERMA')",
     "SELECT COD_ART FROM THINKAI_DORIN_ARTICOLI_PROFILO WHERE COD_CF = {fornitoreCodCf} AND CODICE_FORNITORE_NORM = {rigaCodiceFornitoreNorm} AND CHAR_LENGTH({rigaCodiceFornitoreNorm}) > 0 AND ATTIVO = 1 AND COALESCE(MATCH_METHOD, '') NOT IN ('ORDINE_FOR', 'ORDINE_FOR_CONFERMA') LIMIT 1",
     1),
    ("sql",
     "SELECT TOP 5 COD_ART, DES_ART FROM ART_ANA WHERE COD_ART LIKE {rigaCodiceFornitoreRawLike} OR DES_ART LIKE {rigaDescrizioneLike}",
     "SELECT COD_ART, DES_ART FROM ART_ANA WHERE COD_ART LIKE {rigaCodiceFornitoreRawLike} OR DES_ART LIKE {rigaDescrizioneLike} LIMIT 5",
     1),
    ("sql",
     "SELECT DISTINCT TOP 3 R.COD_ART FROM DDT_FOR_RIGHE R INNER JOIN DDT_FOR D ON D.DOC_ID = R.DOC_ID WHERE D.COD_CF = {fornitoreCodCf} AND R.DES_RIGA LIKE {rigaDescrizioneLike}",
     "SELECT DISTINCT R.COD_ART FROM DDT_FOR_RIGHE R INNER JOIN DDT_FOR D ON D.DOC_ID = R.DOC_ID WHERE D.COD_CF = {fornitoreCodCf} AND R.DES_RIGA LIKE {rigaDescrizioneLike} LIMIT 3",
     1),
    ("sql",
     "SELECT TOP 2 R.DOC_RIGA_ID AS RIGA_ID, R.DOC_ID AS ORD_DOC_ID FROM dbo.ORD_FOR_RIGHE R INNER JOIN dbo.ORD_FOR O ON O.AZIENDA_ID = R.AZIENDA_ID AND O.DOC_ID = R.DOC_ID WHERE R.COD_CF = {fornitoreCodCf} AND " + RIF_MSSQL + " AND R.COD_ART = {rigaCodArtRisolto} AND EXISTS (" + SUB_MSSQL + ") ORDER BY R.DOC_RIGA_ID",
     "SELECT R.DOC_RIGA_ID AS RIGA_ID, R.DOC_ID AS ORD_DOC_ID FROM ORD_FOR_RIGHE R INNER JOIN ORD_FOR O ON O.AZIENDA_ID = R.AZIENDA_ID AND O.DOC_ID = R.DOC_ID WHERE R.COD_CF = {fornitoreCodCf} AND " + RIF_MYSQL + " AND R.COD_ART = {rigaCodArtRisolto} AND EXISTS (" + SUB_MYSQL + ") ORDER BY R.DOC_RIGA_ID LIMIT 2",
     1),
    ("sql",
     "SELECT TOP 1 * FROM dbo.ORD_FOR_RIGHE WHERE DOC_ID = {arrOrdDocId} AND DOC_RIGA_ID = {arrOrdRigaId}",
     "SELECT * FROM ORD_FOR_RIGHE WHERE DOC_ID = {arrOrdDocId} AND DOC_RIGA_ID = {arrOrdRigaId} LIMIT 1",
     1),
    ("sql",
     "SELECT TOP 3 D.DOC_ID FROM dbo.DDT_FOR D WHERE D.COD_CF = {fornitoreCodCf} AND D.COD_CAUS_DOC = {causaleBolla} AND CONVERT(date, D.DATA_DOC) = CONVERT(date, {dataRegistrazione}) ORDER BY D.DOC_ID DESC",
     "SELECT D.DOC_ID FROM DDT_FOR D WHERE D.COD_CF = {fornitoreCodCf} AND D.COD_CAUS_DOC = {causaleBolla} AND D.DATA_DOC >= CAST({dataRegistrazione} AS DATE) AND D.DATA_DOC < CAST({dataRegistrazione} AS DATE) + INTERVAL 1 DAY ORDER BY D.DOC_ID DESC LIMIT 3",
     1),
    ("where",
     "LOG_KEY LIKE {gruppoLikeLog} ESCAPE '\\' AND LOG_KEY <> {fileCorrelationId} AND STATO <> 'CREATO'",
     "LOG_KEY LIKE {gruppoLikeLog} ESCAPE '!' AND LOG_KEY <> {fileCorrelationId} AND STATO <> 'CREATO'",
     1),
    ("where",
     "LTRIM(RTRIM(ERP_DDT_ID)) = '0' AND STATO <> 'CREATO'",
     "TRIM(ERP_DDT_ID) = '0' AND STATO <> 'CREATO'",
     1),
]

# ---------------------------------------------------------------------------
# 2. CodeJs: valori preparati per SQL / filtri TcRestAPI (testo esatto)
# ---------------------------------------------------------------------------
CODE = [
    # MySQL rifiuta 'AAAA-MM-GGTHH:MM:SS.mmmZ' su DATETIME (errore 1292); il formato
    # 'AAAA-MM-GG HH:MM:SS.mmm' (UTC) e' accettato sia da MySQL sia da datetime2.
    ("return new Date().toISOString();  ",
     "return new Date().toISOString().replace(\"T\", \" \").replace(\"Z\", \"\");",
     2),
    # Pattern LIKE del gruppo multi-parte: carattere di escape '!' invece di '\'
    # (in MySQL '\' e' anche escape delle stringhe: ESCAPE '\' e' un errore di sintassi).
    ("const esc = g.replace(/([\\\\%_\\[])/g, \"\\\\$1\");   // escape per LIKE (underscore letterali)\nstepData.gruppoLikeLog = esc + \"\\\\_\\\\_p%\";",
     "const esc = g.replace(/([!%_\\[])/g, \"!$1\");\nstepData.gruppoLikeLog = esc + \"!_!_p%\";",
     1),
    # Filtri TcRestAPI interpolati come testo (non bound): in MySQL anche '\' e' un
    # carattere di escape, quindi P.IVA ridotta ad alfanumerici e '\' tolto dalla ragione sociale.
    ("stepData.pivaMittenteRicerca = pivaMittente.replace(/^[A-Za-z]{2}/, \"\");",
     "stepData.pivaMittenteRicerca = pivaMittente.replace(/[^A-Za-z0-9]/g, \"\").replace(/^[A-Za-z]{2}/, \"\");",
     1),
    ("stepData.pivaMittenteRicerca = (\"\" + pivaErp).replace(/^[A-Za-z]{2}/, \"\");",
     "stepData.pivaMittenteRicerca = (\"\" + pivaErp).replace(/[^A-Za-z0-9]/g, \"\").replace(/^[A-Za-z]{2}/, \"\");",
     1),
    ("  .replace(/[.,;:&]/g, \" \")\n",
     "  .replace(/[.,;:&\\\\]/g, \" \")\n",
     1),
    # Controllo schema: 5 tabelle di appoggio (anche lo staging), non 3.
    ("const ok = trovate === 3;", "const ok = trovate === 5;", 1),
    ("return { ok: ok, trovate: trovate, attese: 3 };", "return { ok: ok, trovate: trovate, attese: 5 };", 1),
    # Le mappe che determinano causale e deposito sono obbligatorie per il nuovo cliente.
    ("const richiesti = [\"workRoot\", \"workRootO\", \"operatorEmail\", \"destinatarioPiva\", \"destinatarioRagioneSociale\"];",
     "const richiesti = [\"workRoot\", \"workRootO\", \"operatorEmail\", \"destinatarioPiva\", \"destinatarioRagioneSociale\", \"mappaDestinazioni\", \"mappaDepositiDestinazione\", \"catalogoCausaliDestinazioneDdt\"];",
     1),
]

# ---------------------------------------------------------------------------
# 3. Prompt AI: riferimenti al cliente sorgente resi parametrici
# ---------------------------------------------------------------------------
PROMPT = [
    ("a quale filiale Decox è indirizzato il documento",
     "a quale filiale/sede di '{destinatarioRagioneSociale}' è indirizzato il documento", 1),
    ("reso di merce da Decox verso il fornitore",
     "reso di merce da '{destinatarioRagioneSociale}' verso il fornitore", 1),
]

# Esempi con dati reali del cliente sorgente (indirizzo di filiale, P.IVA di un fornitore, numeri
# d'ordine, riferimento cliente): riconosciuti per forma, non per contenuto, e resi fittizi.
PROMPT_REGEX = [
    (r"'P\.I \d{11} - Cod Id\. Nr\. IT \d{11} - Cap\. Soc\. € [\d.]+ i\.v\.'",
     "'P.I 01234567890 - Cod Id. Nr. IT 01234567890 - Cap. Soc. € 100.000 i.v.'", 1),
    (r"'ns\.rif\.: \d+ / \d+ / vs ordine (\d{4})-1[A-Z]{2}OF-\d{7}'",
     r"'ns.rif.: 1234567890 / 000001 / vs ordine \1-1XXOF-0000123'", 1),
    (r"'Ord:\d+ del (\d{2}/\d{2}/\d{4}) vs rif: (\d{4})-1[A-Z]{2}OF-\d{7}'",
     r"'Ord:0001234567 del \1 vs rif: \2-1XXOF-0000456'", 1),
    (r"Vostro rif\. [A-Z]+-[A-Z]+'", "Vostro rif. CANTIERE-NORD'", 1),
    (r"es\. etichetta '[^']*' seguita dalle righe '[^']*' / '[^']*': l'etichetta cita '[^']*' ma il comune REALE che identifica la filiale è '[^']*'",
     "es. etichetta 'RAGIONE SOCIALE - MILANO' seguita dalle righe 'VIA ESEMPIO 1' / 'I-20090 SEGRATE MI': l'etichetta cita 'MILANO' ma il comune REALE che identifica la filiale è 'SEGRATE'", 1),
]

MESSAGGI = [
    ("Tabelle di appoggio DECOX mancanti (THINKAI_DECOX_DDT_LOG / _RIGHE / _ARTICOLI_PROFILO). Creare le tabelle (vedi DDL suggerita in fondo al file) prima di avviare l'agente.",
     "Tabelle di appoggio DORIN mancanti (THINKAI_DORIN_DDT_LOG / _DDT_LOG_RIGHE / _ARTICOLI_PROFILO / _DDT_STAGING_TESTA / _DDT_STAGING_RIGHE). Creare le tabelle con sql/ddl_mysql_thinkai_dorin.sql prima di avviare l'agente.",
     1),
]

# Testi rivolti all'operatore (oggetti mail, messaggi, alias, commenti): nome cliente.
RINOMINA_TESTI = [(r"\bTHINKAI_DECOX_", "THINKAI_DORIN_"), (r"\bCK_DECOX_", "CK_DORIN_"), (r"\bDECOX\b", "DORIN")]
CAMPI_TESTO = ("subject", "message", "code", "body")

# ---------------------------------------------------------------------------
# 4. Profilo cliente (M00). Senza profilo privato: segnaposto bloccanti.
# ---------------------------------------------------------------------------
CONFIG_DORIN = {
    "workRoot": "DA_CONFIGURARE_WORK_ROOT",
    "workRootO": "DA_CONFIGURARE_WORK_ROOT_SCANSIONE",
    "operatorEmail": "DA_CONFIGURARE_EMAIL_OPERATORE",
    "operatorEmailCc": "",
    "agentVersion": "DORIN-DDT-v1.2.3-" + VERSIONE_DERIVATA,
    "destinatarioPiva": "DA_CONFIGURARE_PIVA_DORIN",
    "destinatarioRagioneSociale": "DA_CONFIGURARE_RAGIONE_SOCIALE_DORIN",
    "tabellaLog": "THINKAI_DORIN_DDT_LOG",
    "tabellaLogRighe": "THINKAI_DORIN_DDT_LOG_RIGHE",
    "tabellaArticoliProfilo": "THINKAI_DORIN_ARTICOLI_PROFILO",
    "tabellaStagingTesta": "THINKAI_DORIN_DDT_STAGING_TESTA",
    "tabellaStagingRighe": "THINKAI_DORIN_DDT_STAGING_RIGHE",
    "dmsAbilitato": "false",
    "dmsCartellaImport": "",
    "mappaDestinazioni": "DA_CONFIGURARE_MAPPA_DESTINAZIONI",
    "mappaDepositiDestinazione": "DA_CONFIGURARE_MAPPA_DEPOSITI",
    "mappaBrandArticolo": "",
    "catalogoCausaliDestinazioneDdt": "DA_CONFIGURARE_CATALOGO_CAUSALI",
    "catalogoCausaliRiferimento": "",
}
CREDENZIALE_SORGENTE = "TEST_TCDecox"
CREDENZIALE_DORIN = "DA_CONFIGURARE_CREDENZIALE_TC_DORIN"
TABELLE = ["DDT_LOG_RIGHE", "DDT_LOG", "ARTICOLI_PROFILO", "DDT_STAGING_TESTA", "DDT_STAGING_RIGHE"]
TSQL_VIETATI = [r"\bTOP\s+\d", r"\bISNULL\s*\(", r"\bLEN\s*\(", r"\bCONVERT\s*\(", r"\bGETDATE\s*\(",
                r"\bdbo\.", r"\bNVARCHAR\b", r"\bDATEADD\s*\(", r"ESCAPE\s+'\\\\'", r"\bTHINKAI_DECOX_"]


def figli_step(v):
    return isinstance(v, list) and v and all(isinstance(x, dict) and ("Type" in x or "type" in x) for x in v)


class Flusso:
    """Visita tutti gli step (anche annidati in subSteps/thenSteps/elseSteps/cases)."""

    def __init__(self, dati):
        self.dati = dati
        self.cfg = []  # (step, nome_campo_config, dict_config)
        self._visita(dati["Agent"]["Steps"])

    def _visita(self, steps):
        for s in steps:
            campo = "ConfigJson" if "ConfigJson" in s else "configJson"
            raw = s.get(campo)
            c = json.loads(raw) if isinstance(raw, str) and raw else (raw or {})
            self.cfg.append((s, campo, c))
            for v in list(c.values()) + list(s.values()):
                if figli_step(v):
                    self._visita(v)
                elif isinstance(v, dict):
                    for vv in v.values():
                        if figli_step(vv):
                            self._visita(vv)

    def campi(self, nome):
        for s, _, c in self.cfg:
            if isinstance(c, dict) and isinstance(c.get(nome), str):
                yield s, c

    def sostituisci(self, nome, da, a, attese):
        trovate = 0
        for _, c in self.campi(nome):
            n = c[nome].count(da)
            if n:
                c[nome] = c[nome].replace(da, a)
                trovate += n
        if trovate != attese:
            raise SystemExit(f"[ERRORE] campo '{nome}': attese {attese} occorrenze, trovate {trovate}:\n  {da[:160]}")
        return trovate

    def serializza(self):
        # Riserializza tutti i ConfigJson, dal piu' interno al piu' esterno.
        for s, campo, c in reversed(self.cfg):
            s[campo] = json.dumps(c, ensure_ascii=False, separators=(",", ":"))


def carica_profilo(percorso):
    if not percorso:
        return {}
    with open(percorso, encoding="utf-8") as f:
        p = json.load(f)
    return {k: v for k, v in p.items() if not k.startswith("_")}


def adatta(sorgente, profilo):
    with open(sorgente, encoding="utf-8") as f:
        dati = json.load(f)
    agente = dati["Agent"]
    if agente["Name"] != VERSIONE_SORGENTE:
        raise SystemExit(f"[ERRORE] sorgente inattesa: '{agente['Name']}' (attesa '{VERSIONE_SORGENTE}')")
    fl = Flusso(dati)

    for campo, da, a, n in SQL:
        fl.sostituisci(campo, da, a, n)
    for da, a, n in CODE:
        fl.sostituisci("code", da, a, n)
    for da, a, n in PROMPT:
        fl.sostituisci("prompt", da, a, n)
    for da, a, n in PROMPT_REGEX:
        trovate = 0
        for _, c in fl.campi("prompt"):
            c["prompt"], k = re.subn(da, a, c["prompt"])
            trovate += k
        if trovate != n:
            raise SystemExit(f"[ERRORE] prompt: attese {n} occorrenze di {da[:60]}, trovate {trovate}")
    for da, a, n in MESSAGGI:
        fl.sostituisci("message", da, a, n)
    for nome in CAMPI_TESTO:
        for _, c in fl.campi(nome):
            for da, a in RINOMINA_TESTI:
                c[nome] = re.sub(da, a, c[nome])
    for s, _, _ in fl.cfg:
        for k in ("Alias", "alias"):
            if isinstance(s.get(k), str):
                for da, a in RINOMINA_TESTI:
                    s[k] = re.sub(da, a, s[k])

    # Nomi tabella: niente schema dbo (in MySQL sarebbe un database), prefisso cliente.
    for nome in ("table", "sql", "where"):
        for _, c in fl.campi(nome):
            c[nome] = c[nome].replace("dbo.", "")
            for t in TABELLE:
                c[nome] = c[nome].replace("THINKAI_DECOX_" + t, "THINKAI_DORIN_" + t)
    for _, c in fl.campi("idempotencyKey"):
        c["idempotencyKey"] = re.sub(r"^decox-", "dorin-", c["idempotencyKey"])

    credenziale = profilo.get("credentialName", CREDENZIALE_DORIN)
    n = 0
    for _, c in fl.campi("credentialName"):
        if c["credentialName"] == CREDENZIALE_SORGENTE:
            c["credentialName"] = credenziale
            n += 1
    if n == 0:
        raise SystemExit("[ERRORE] credenziale sorgente non trovata")

    config = dict(CONFIG_DORIN)
    config.update(profilo.get("config", {}))
    passo = agente["Steps"][0]
    c0 = next(c for s, _, c in fl.cfg if s is passo)
    chiavi = {a["key"] for a in c0["assignments"]}
    ignote = set(config) - chiavi
    if ignote:
        raise SystemExit(f"[ERRORE] chiavi di configurazione inesistenti nel flusso: {sorted(ignote)}")
    for a in c0["assignments"]:
        if a["key"] in config:
            a["value"] = config[a["key"]]

    fl.serializza()
    dati["Warnings"] = [w.replace(CREDENZIALE_SORGENTE, credenziale) for w in dati.get("Warnings", [])]

    testo = json.dumps(dati, ensure_ascii=False)
    residui = [p for nome in ("sql", "where", "table") for _, c in fl.campi(nome)
               for p in TSQL_VIETATI if re.search(p, c[nome], re.I)]
    if residui:
        raise SystemExit(f"[ERRORE] costrutti T-SQL residui: {sorted(set(residui))}")
    if re.search(r"decox", testo, re.I):
        righe = sorted(set(m.group(0) for m in re.finditer(r".{0,40}decox.{0,40}", testo, re.I)))
        raise SystemExit("[ERRORE] riferimenti al cliente sorgente residui:\n  " + "\n  ".join(righe[:10]))

    agente["Name"] = profilo.get("nomeAgente", "DOR DDT fornitori v1.2.3 MySQL")
    agente["Description"] = "Import DDT fornitori - Target Cross su MySQL (derivato da DEC v1.2.3)"
    agente["Tags"] = ["Test", "DDT", "4B", "DOR", "MySQL"]
    return dati


def main(argv):
    args, opz, i = [], {}, 1
    while i < len(argv):
        if argv[i].startswith("--") and i + 1 < len(argv):
            opz[argv[i]] = argv[i + 1]
            i += 2
        else:
            args.append(argv[i])
            i += 1
    if not args:
        print(__doc__)
        return 2
    profilo = carica_profilo(opz.get("--profilo"))
    out = opz.get("--out") or os.path.join(AQUI, "DOR_DDT_fornitori_v1.2.3-mysql.thinkaiagent.json")
    dati = adatta(args[0], profilo)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(dati, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[OK] flusso MySQL scritto in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
