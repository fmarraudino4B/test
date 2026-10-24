#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_sql_mysql.py - collaudo su DATI SINTETICI del flusso "DOR DDT fornitori v1.2.3 MySQL".

Non sostituisce il collaudo sul database Target Cross di Dorin: verifica che il testo SQL
generato sia MySQL valido, che i valori preparati dai CodeJs siano accettati da MySQL in
modalita' strict e che la logica (anti-duplicato, memoria, staging multi-parte, LIKE con
escape) dia i risultati attesi su tabelle Target Cross minime e sintetiche.

Passi:
  1. statico  : nessun costrutto T-SQL nei nodi SQL, nessun riferimento al cliente sorgente
  2. CodeJs   : `node --check` di tutti i corpi; esecuzione dei CodeJs toccati dall'adattamento
  3. MySQL    : DB di collaudo usa-e-getta, DDL del flusso + tabelle Target Cross sintetiche;
                ogni Query/SqlInsert/SqlUpdate eseguita con parametri bound (come WorkForce),
                con valori tipici e con valori vuoti; scenario con asserzioni sui risultati

Uso:
  python test_sql_mysql.py <DOR_DDT_fornitori_v1.2.3-mysql.thinkaiagent.json>
         [--host 127.0.0.1] [--port 3306] [--user root] [--password ""] [--db collaudo_dorin_ddt]
Richiede: node nel PATH, PyMySQL, un server MySQL di prova (il DB indicato viene ricreato).
"""
import json
import os
import re
import subprocess
import sys
import tempfile

import pymysql

AQUI = os.path.dirname(os.path.abspath(__file__))
DDL = os.path.join(AQUI, "..", "sql", "ddl_mysql_thinkai_dorin.sql")
TSQL = [r"\bTOP\s+\d", r"\bISNULL\s*\(", r"\bLEN\s*\(", r"\bCONVERT\s*\(", r"\bGETDATE\s*\(", r"\bdbo\.",
        r"\bNVARCHAR\b", r"\bDATEADD\s*\(", r"ESCAPE\s+'\\'", r"\[\w+\]"]
PH = re.compile(r"\{(\w+)\}")

# Tabelle Target Cross minime e SINTETICHE: solo le colonne lette dal flusso, tipi plausibili.
# Collation NO PAD (default MySQL 8.0) = caso peggiore per gli spazi finali.
TC_DDL = """
CREATE TABLE CF (COD_CF VARCHAR(20) PRIMARY KEY, RAG_SOC_CF VARCHAR(100), P_IVA_CF VARCHAR(20), FLAG_FOR TINYINT);
CREATE TABLE ORD_FOR (AZIENDA_ID INT, DOC_ID VARCHAR(30), NUM_DOC INT, ANNO_DOC INT, COD_CF VARCHAR(20), PRIMARY KEY (AZIENDA_ID, DOC_ID));
CREATE TABLE ORD_FOR_SPEC (AZIENDA_ID INT, DOC_ID VARCHAR(30), NUMERO_CONFERMA VARCHAR(50), PRIMARY KEY (AZIENDA_ID, DOC_ID));
CREATE TABLE ORD_FOR_RIGHE (AZIENDA_ID INT, DOC_ID VARCHAR(30), DOC_RIGA_ID VARCHAR(40), COD_CF VARCHAR(20), COD_ART VARCHAR(30),
  UM VARCHAR(5), PREZZO_LORDO_VU1 DECIMAL(18,6), SCONTO_1 DECIMAL(9,4), SCONTO_2 DECIMAL(9,4), DES_RIGA TEXT, PRIMARY KEY (AZIENDA_ID, DOC_RIGA_ID));
CREATE TABLE ORD_FOR_RIGHE_SPEC (AZIENDA_ID INT, DOC_ID VARCHAR(30), DOC_RIGA_ID VARCHAR(40), QUANT_DA_CONS_RIGA_UM_BASE DECIMAL(18,6));
CREATE TABLE ART_ANA (COD_ART VARCHAR(30) PRIMARY KEY, DES_ART VARCHAR(100));
CREATE TABLE DDT_FOR (DOC_ID VARCHAR(30) PRIMARY KEY, COD_CF VARCHAR(20), COD_CAUS_DOC VARCHAR(10), DATA_DOC DATETIME);
CREATE TABLE DDT_FOR_RIGHE (DOC_ID VARCHAR(30), DOC_RIGA_ID VARCHAR(40) PRIMARY KEY, COD_ART VARCHAR(30), DES_RIGA TEXT);
CREATE TABLE CAUS_DOC_SERIE (COD_CAUS_DOC VARCHAR(10), SERIE VARCHAR(10));
"""
TC_DATI = """
INSERT INTO CF VALUES ('F0001','FORNITORE SINTETICO SRL','01234567890',1),('C0001','FORNITORE SINTETICO SRL','01234567890',0);
INSERT INTO ORD_FOR VALUES (1,'2026-OF-000123',123,2026,'F0001'),(1,'2025-OF-000777',777,2025,'F0001');
INSERT INTO ORD_FOR_SPEC VALUES (1,'2026-OF-000123','CONF ABCDEF  '),(1,'2025-OF-000777',NULL);
INSERT INTO ORD_FOR_RIGHE VALUES
  (1,'2026-OF-000123','2026-OF-000123-0001','F0001','ART001','PZ',12.5,10,0,'PIASTRELLA 60X60'),
  (1,'2026-OF-000123','2026-OF-000123-0002','F0001','ART002','PZ',3,0,0,'COLLA'),
  (1,'2025-OF-000777','2025-OF-000777-0001','F0001','ART001','PZ',11,0,0,'PIASTRELLA 60X60');
INSERT INTO ORD_FOR_RIGHE_SPEC VALUES
  (1,'2026-OF-000123','2026-OF-000123-0001',4),(1,'2026-OF-000123','2026-OF-000123-0001',2),
  (1,'2026-OF-000123','2026-OF-000123-0002',0),(1,'2025-OF-000777','2025-OF-000777-0001',5);
INSERT INTO ART_ANA VALUES ('ART001','PIASTRELLA GRES 60X60'),('ART002','COLLA CEMENTIZIA'),('AB-123X','ARTICOLO CON CODICE FORNITORE');
INSERT INTO DDT_FOR VALUES ('2026-DF-000001','F0001','DTR','2026-10-24 15:30:00'),('2026-DF-000002','F0001','DTR','2026-10-23 09:00:00');
INSERT INTO DDT_FOR_RIGHE VALUES ('2026-DF-000002','R1','ART001','PIASTRELLA GRES 60X60 LOTTO 7');
INSERT INTO CAUS_DOC_SERIE VALUES ('DTR','DF');
"""


def figli_step(v):
    return isinstance(v, list) and v and all(isinstance(x, dict) and ("Type" in x or "type" in x) for x in v)


def steps(lista, out):
    for s in lista:
        raw = s.get("ConfigJson", s.get("configJson"))
        c = json.loads(raw) if isinstance(raw, str) and raw else (raw or {})
        out.append((s.get("Type", s.get("type")), s.get("Alias") or s.get("alias") or "", c))
        for v in list(c.values()) + list(s.values()):
            if figli_step(v):
                steps(v, out)
            elif isinstance(v, dict):
                for vv in v.values():
                    if figli_step(vv):
                        steps(vv, out)
    return out


class Esito:
    def __init__(self):
        self.ok, self.ko = 0, []

    def check(self, cond, msg):
        if cond:
            self.ok += 1
        else:
            self.ko.append(msg)
            print("  [KO] " + msg)


def esegui_js(code, stepdata):
    prog = ("const stepData = " + json.dumps(stepdata) + "; const $input = {};\n"
            "const __r = (() => {\n" + code + "\n})();\n"
            "console.log(JSON.stringify({ r: __r === undefined ? null : __r, s: stepData }));")
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write(prog)
    try:
        out = subprocess.run(["node", f.name], capture_output=True, text=True, timeout=30)
    finally:
        os.unlink(f.name)
    if out.returncode:
        raise RuntimeError(out.stderr.strip())
    return json.loads(out.stdout)


def node_check(code):
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
        f.write("(() => {\n" + code + "\n});\n")
    try:
        return subprocess.run(["node", "--check", f.name], capture_output=True, text=True).returncode == 0
    finally:
        os.unlink(f.name)


def bind(testo, sd):
    """{chiave} -> parametro bound. Chiave mai scritta -> resta letterale (comportamento WorkForce, R8)."""
    params = []

    def r(m):
        if m.group(1) not in sd:
            return m.group(0).replace("%", "%%")
        params.append(sd[m.group(1)])
        return "%s"
    return PH.sub(r, testo.replace("%", "%%")), params


def valore(v, sd):
    if isinstance(v, str):
        m = PH.fullmatch(v)
        if m and m.group(1) in sd:
            return sd[m.group(1)]
        return PH.sub(lambda m: "" + str(sd.get(m.group(1), m.group(0))), v)
    return v


def sql_insert(cur, c, sd):
    vals = {k: valore(v, sd) for k, v in c["values"].items()}
    cols = ", ".join(vals)
    cur.execute(f"INSERT INTO {c['table']} ({cols}) VALUES ({', '.join(['%s'] * len(vals))})", list(vals.values()))
    return cur.rowcount


def sql_update(cur, c, sd):
    sets = {k: valore(v, sd) for k, v in c["set"].items()}
    where, wp = bind(c["where"], sd)
    cur.execute(f"UPDATE {c['table']} SET {', '.join(k + ' = %s' for k in sets)} WHERE {where}", list(sets.values()) + wp)
    return cur.rowcount


def query(cur, sql, sd):
    q, p = bind(sql, sd)
    cur.execute(q, p)
    return list(cur.fetchall())


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
    with open(args[0], encoding="utf-8") as f:
        flusso = json.load(f)
    tutti = steps(flusso["Agent"]["Steps"], [])
    queries = [(a, c) for t, a, c in tutti if t == 1]
    inserts = [(a, c) for t, a, c in tutti if t == 62]
    updates = [(a, c) for t, a, c in tutti if t == 63]
    codejs = [(a, c) for t, a, c in tutti if t == 23 and isinstance(c.get("code"), str)]
    E = Esito()

    print(f"== 1. Controlli statici ({len(queries)} query, {len(inserts)} insert, {len(updates)} update)")
    for a, c in queries + updates + inserts:
        testo = " ".join(str(c.get(k, "")) for k in ("sql", "where", "table"))
        for p in TSQL:
            E.check(not re.search(p, testo, re.I), f"T-SQL '{p}' residuo in '{a}': {testo[:120]}")
    E.check(not re.search("decox", json.dumps(flusso), re.I), "riferimenti al cliente sorgente nel flusso")

    print(f"== 2. CodeJs ({len(codejs)} corpi)")
    for a, c in codejs:
        E.check(node_check(c["code"]), f"sintassi JS non valida in '{a}'")
    js = {a: c["code"] for a, c in codejs}

    def corpo(frammento):
        trovati = [c for c in js.values() if frammento in c]
        E.check(len(trovati) >= 1, f"CodeJs con '{frammento}' non trovato")
        return trovati[0] if trovati else "return null;"

    now = esegui_js(corpo("toISOString().replace"), {})["r"]
    E.check(re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}", now or ""), f"nowIso in formato inatteso: {now}")
    grp = esegui_js(corpo("stepData.gruppoLikeLog ="), {"docGroupId": "DDT_ACME_123", "parteTot": 2})
    like_gruppo = grp["s"]["gruppoLikeLog"]
    E.check(like_gruppo == "DDT!_ACME!_123!_!_p%", f"gruppoLikeLog inatteso: {like_gruppo}")
    E.check(grp["r"] == [{"nome": "DDT_ACME_123__p01of02.pdf"}], f"parti da spostare inattese: {grp['r']}")
    rs = esegui_js(corpo("stepData.fornitoreRagSocLike ="), {"fornitoreCodCf": "", "ragioneSocialeMittente": "L'Arte\\Ceramica S.r.l."})["s"]
    E.check("\\" not in rs["fornitoreRagSocLike"] and "''" in rs["fornitoreRagSocLike"],
            f"ragione sociale non sicura per il filtro TcRestAPI: {rs['fornitoreRagSocLike']}")
    for righe, atteso in (([{"TABELLE_TROVATE": 5}], True), ([{"TABELLE_TROVATE": "5"}], True), ([{"TABELLE_TROVATE": 3}], False)):
        r = esegui_js(corpo("const ok = trovate"), {"lastQueryRows": righe})["s"]
        E.check(r["schemaCheckOk"] is atteso, f"controllo schema con {righe}: atteso {atteso}")
    piva_line = [ln for c in js.values() for ln in c.split("\n") if ln.startswith("stepData.pivaMittenteRicerca = pivaMittente")]
    E.check(len(piva_line) == 1, "riga di normalizzazione P.IVA non trovata")
    if piva_line:
        r = esegui_js("const pivaMittente = \"IT 01234567890'--\";\n" + piva_line[0] + "\nreturn stepData.pivaMittenteRicerca;", {})["r"]
        E.check(r == "01234567890", f"P.IVA normalizzata inattesa: {r}")

    print("== 3. MySQL")
    db = opz.get("--db", "collaudo_dorin_ddt")
    cn = pymysql.connect(host=opz.get("--host", "127.0.0.1"), port=int(opz.get("--port", "3306")),
                         user=opz.get("--user", "root"), password=opz.get("--password", ""), autocommit=True,
                         cursorclass=pymysql.cursors.DictCursor, charset="utf8mb4")
    cur = cn.cursor()
    cur.execute("SELECT VERSION() AS v, @@sql_mode AS m")
    info = cur.fetchone()
    print(f"  server {info['v']}  sql_mode={info['m']}")
    cur.execute(f"DROP DATABASE IF EXISTS `{db}`")
    cur.execute(f"CREATE DATABASE `{db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci")
    cur.execute(f"USE `{db}`")
    cur.execute("SET SESSION sql_mode = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'")
    with open(DDL, encoding="utf-8") as f:
        ddl = re.sub(r"/\*.*?\*/", "", f.read(), flags=re.S)
    for st in [s for s in ddl.split(";") if s.strip()] * 2:   # due volte: lo script deve essere idempotente
        cur.execute(st)
    for st in [s for s in (TC_DDL + TC_DATI).split(";") if s.strip()]:
        cur.execute(st)

    config = {a["key"]: a["value"] for a in json.loads(flusso["Agent"]["Steps"][0]["ConfigJson"])["assignments"]}
    sd = dict(config)
    sd.update({
        "nowIso": now, "nowIsoFine": now, "fileCorrelationId": "DDT_ACME_123__p02of02.pdf", "docGroupId": "DDT_ACME_123",
        "currentFileName": "DDT_ACME_123__p02of02.pdf", "workRoot": "C:\\WF\\DDT", "agentVersion": config["agentVersion"],
        "pivaMittente": "IT01234567890", "docNumero": "123/A", "docDataSql": "20261020", "fornitoreCodCf": "F0001",
        "rigaRiferimentoOrdineLike": "%2026-OF-000123%", "rigaRiferimentoNumDoc": "-1", "docAnno": "2026", "docAnnoPrec": "2025",
        "rigaRiferimentoConfermaLike": "%ABCDEF%", "rigaCodiceFornitoreNorm": "AB123", "rigaCodiceFornitoreRawLike": "AB-123%",
        "rigaDescrizioneLike": "%PIASTRELLA%", "rigaCodArtRisolto": "ART001", "arrOrdDocId": "2026-OF-000123",
        "arrOrdRigaId": "2026-OF-000123-0001", "causaleBolla": "DTR", "dataRegistrazione": "2026-10-24",
        "codiceDocCreato": "2026-DF-000001", "gruppoLikeLog": like_gruppo,
        "daImpararCodCf": "F0001", "daImpararCodiceFornitoreNorm": "AB123", "daImpararCodiceFornitoreRaw": "AB-123",
        "daImpararCodArt": "ART001", "daImpararMetodo": "METODO_A", "daImpararConfidence": "0.9000",
        "logRigaLogKey": "DDT_ACME_123__p02of02.pdf", "logRigaNumero": "1", "logRigaCodiceFornitore": "AB-123",
        "logRigaDescrizione": "Piastrella gres 60x60 'grigio'", "logRigaCodArt": "ART001", "logRigaMatchMethod": "METODO_A",
        "logRigaStato": "RISOLTA", "logRigaUm": "PZ", "logRigaQuantita": "1,5", "logRigaPrezzoUnitario": "12.50",
        "stgTestaTipoDoc": "RICEVUTO", "stgTestaCausale": "DTR", "stgTestaSerie": "DF", "stgTestaDataDoc": "24/10/2026",
        "stgTestaCodCf": "F0001", "stgTestaCodDep": "01", "stgTestaNumDdt": "123/A", "stgTestaDataDdt": "20/10/2026",
        "stgTestaNote": "", "stgTestaOrdineId": "2026-OF-000123", "stgTestaPartiTot": 2,
        "stgRigaLogKey": "DDT_ACME_123", "stgRigaNumero": 200001, "stgRigaCodArt": "ART001", "stgRigaDes": "Piastrella",
        "stgRigaUm": "Pz.", "stgRigaQuant": 1.5, "stgRigaPrezzo": 12.5, "stgRigaSconto1": 10, "stgRigaSconto2": 0,
        "stgRigaOrdRigaId": "2026-OF-000123-0001", "stgRigaOrdDocId": "2026-OF-000123", "stgRigaFlagRaggr": 0,
        "stgRigaMatch": "ORDINE_FOR", "stgRigaStato": "RISOLTA", "stgRigaParte": 2,
        "logStatoFinale": "CREATO", "logCodCf": "F0001", "ragioneSocialeMittente": "FORNITORE SINTETICO SRL",
        "logConfidenza": "0.9500", "logEsitoValidazione": "OK", "esitoMotivo": "", "logErpDdtId": "2026-DF-000001",
        "logCreazioneParziale": "0", "logRigheTotali": "1", "logRigheRisolte": "1", "logRigheScartate": "0",
        "logErrorCode": "", "logErrorDetail": "", "logDetailJson": "{\"causale\":\"DTR\"}",
    })

    print("  3a. ogni nodo SQL eseguito una volta (transazione annullata)")
    for gruppo, fn in (("query", lambda c: query(cur, c["sql"], sd)), ("insert", lambda c: sql_insert(cur, c, sd)),
                       ("update", lambda c: sql_update(cur, c, sd))):
        for a, c in {"query": queries, "insert": inserts, "update": updates}[gruppo]:
            cur.execute("START TRANSACTION")
            try:
                fn(c)
                E.check(True, "")
            except pymysql.MySQLError as e:
                E.check(False, f"{gruppo} '{a or c.get('table')}': {e}")
            cur.execute("ROLLBACK")

    print("  3b. insert/update con valori vuoti dove il flusso puo' passare stringa vuota")
    sempre_valorizzate = {"nowIso", "nowIsoFine", "fileCorrelationId", "docGroupId", "logRigaLogKey", "logRigaNumero",
                          "stgRigaLogKey", "stgRigaNumero", "stgRigaQuant", "stgRigaPrezzo", "stgRigaSconto1",
                          "stgRigaSconto2", "stgRigaFlagRaggr", "stgRigaParte", "stgTestaPartiTot", "logConfidenza",
                          "daImpararConfidence", "logRigheTotali", "logRigheRisolte", "logRigheScartate",
                          "logCreazioneParziale", "daImpararCodCf", "daImpararCodiceFornitoreNorm", "logStatoFinale"}
    vuoto = {k: ("" if k not in sempre_valorizzate and isinstance(v, str) else v) for k, v in sd.items()}
    vuoto["logStatoFinale"] = "REVISIONE"
    for gruppo, fn in (("insert", sql_insert), ("update", sql_update)):
        for a, c in {"insert": inserts, "update": updates}[gruppo]:
            cur.execute("START TRANSACTION")
            try:
                fn(cur, c, vuoto)
                E.check(True, "")
            except pymysql.MySQLError as e:
                E.check(False, f"{gruppo} con valori vuoti '{a or c.get('table')}': {e}")
            cur.execute("ROLLBACK")

    print("  3c. scenario con asserzioni")
    Q = {re.sub(r"\s+", " ", c["sql"]): c["sql"] for _, c in queries}

    def q(frammento, dati=None):
        k = [s for s in Q if frammento in s]
        E.check(len(k) == 1, f"query con '{frammento}' non univoca ({len(k)})")
        return query(cur, Q[k[0]], dati or sd) if k else []

    def nodo(lista, tabella, chiave):
        n = [c for _, c in lista if c["table"] == tabella and chiave in json.dumps(c)]
        E.check(len(n) >= 1, f"nodo su {tabella} con '{chiave}' non trovato")
        return n[0]

    r = q("INFORMATION_SCHEMA.TABLES")
    E.check(r and int(r[0]["TABELLE_TROVATE"]) == 5, f"tabelle di appoggio trovate: {r}")
    E.check(q("FROM CAUS_DOC_SERIE") == [{"SERIE": "DF"}], "serie della causale")

    log, log_r, prof = "THINKAI_DORIN_DDT_LOG", "THINKAI_DORIN_DDT_LOG_RIGHE", "THINKAI_DORIN_ARTICOLI_PROFILO"
    stg_t, stg_r = "THINKAI_DORIN_DDT_STAGING_TESTA", "THINKAI_DORIN_DDT_STAGING_RIGHE"
    claim_ins = nodo(inserts, log, "IN_ELABORAZIONE")
    p1 = dict(sd, fileCorrelationId="DDT_ACME_123__p01of02.pdf", currentFileName="DDT_ACME_123__p01of02.pdf")
    trappola = dict(sd, fileCorrelationId="DDT_ACMEX123__p01of02.pdf", currentFileName="DDT_ACMEX123__p01of02.pdf")
    for dati in (p1, trappola, sd):
        E.check(sql_insert(cur, claim_ins, dati) == 1, "claim: insert riga di log")
    E.check(len(q("SELECT STATO, DATA_INIZIO_UTC")) == 1, "lettura riga di log per LOG_KEY")
    cur.execute(f"UPDATE {log} SET ERP_DDT_ID = ' 0 ' WHERE LOG_KEY = %s", [p1["fileCorrelationId"]])
    bonifica = [c for _, c in updates if c["table"] == log and "'0'" in c["where"]][0]
    E.check(sql_update(cur, bonifica, sd) == 1, "bonifica sentinella ERP_DDT_ID '0'")

    E.check(q("FROM THINKAI_DORIN_DDT_LOG WHERE PIVA") == [], "anti-duplicato: nessun DDT registrato prima")
    r = q("R.COD_CF = {fornitoreCodCf} AND (R.DOC_ID LIKE {rigaRiferimentoOrdineLike} OR (O.NUM_DOC = CAST({rigaRiferimentoNumDoc} AS SIGNED) AND O.ANNO_DOC IN (CAST({docAnno} AS SIGNED), CAST({docAnnoPrec} AS SIGNED)))) AND EXISTS")
    E.check([x["RIGA_ID"] for x in r] == ["2026-OF-000123-0001"], f"ordine per riferimento (righe con residuo): {r}")
    r = q("R.COD_ART, R.DOC_ID AS ORD_DOC_ID FROM ORD_FOR_RIGHE R INNER JOIN", dict(sd, rigaRiferimentoOrdineLike="~~NOMATCH~~", rigaRiferimentoNumDoc="777"))
    E.check([x["RIGA_ID"] for x in r] == ["2025-OF-000777-0001"], f"ordine per numero e anno precedente: {r}")
    r = q("RTRIM(SP.NUMERO_CONFERMA) LIKE")
    E.check([x["RIGA_ID"] for x in r] == ["2026-OF-000123-0001"], f"ordine per numero conferma: {r}")
    r = q("R.COD_ART = {rigaCodArtRisolto}")
    E.check([x["RIGA_ID"] for x in r] == ["2026-OF-000123-0001"], f"aggancio riga d'ordine per COD_ART: {r}")

    learn_ins, learn_upd = nodo(inserts, prof, "IMPORT"), nodo(updates, prof, "LAST_USED_AT_UTC")
    E.check(sql_update(cur, learn_upd, sd) == 0, "auto-learning: update a vuoto prima dell'insert")
    E.check(sql_insert(cur, learn_ins, sd) == 1, "auto-learning: insert")
    E.check(q("FROM THINKAI_DORIN_ARTICOLI_PROFILO WHERE COD_CF") == [{"COD_ART": "ART001"}], "memoria: corrispondenza trovata")
    E.check(q("FROM THINKAI_DORIN_ARTICOLI_PROFILO WHERE COD_CF", dict(sd, rigaCodiceFornitoreNorm="")) == [], "memoria: codice vuoto escluso")
    cur.execute(f"UPDATE {prof} SET MATCH_METHOD = 'ORDINE_FOR'")
    E.check(q("FROM THINKAI_DORIN_ARTICOLI_PROFILO WHERE COD_CF") == [], "memoria: voci ORDINE_FOR ignorate")
    try:
        sql_insert(cur, learn_ins, sd)
        E.check(False, "il vincolo UNIQUE (COD_CF, CODICE_FORNITORE_NORM) non ha bloccato il duplicato")
    except pymysql.err.IntegrityError:
        E.check(True, "")

    E.check([x["COD_ART"] for x in q("FROM ART_ANA WHERE COD_ART LIKE")] == ["AB-123X", "ART001"], "metodo B su ART_ANA")
    E.check(q("SELECT DISTINCT R.COD_ART FROM DDT_FOR_RIGHE") == [{"COD_ART": "ART001"}], "metodo C su DDT_FOR_RIGHE")
    r = q("FROM ORD_FOR_RIGHE WHERE DOC_ID = {arrOrdDocId}")
    E.check(len(r) == 1 and float(r[0]["PREZZO_LORDO_VU1"]) == 12.5 and r[0]["UM"] == "PZ", f"prezzo dalla riga d'ordine: {r}")

    E.check(sql_update(cur, nodo(updates, log_r, "CODICE_FORNITORE"), sd) == 0, "audit righe: update a vuoto")
    E.check(sql_insert(cur, nodo(inserts, log_r, "CODICE_FORNITORE"), sd) == 1, "audit righe: insert con quantita' '1,5'")
    E.check(sql_update(cur, nodo(updates, stg_t, "TIPO_DOCUMENTO"), sd) == 0, "staging testa: update a vuoto")
    E.check(sql_insert(cur, nodo(inserts, stg_t, "TIPO_DOCUMENTO"), sd) == 1, "staging testa: insert (data gg/mm/aaaa)")
    stg_ins, stg_upd = nodo(inserts, stg_r, "COD_ART"), nodo(updates, stg_r, "COD_ART")
    for dati in (dict(sd, stgRigaNumero=100001, stgRigaParte=1), sd):
        E.check(sql_update(cur, stg_upd, dati) == 0 and sql_insert(cur, stg_ins, dati) == 1, "staging righe: insert per parte")
    E.check(sql_update(cur, stg_upd, dict(sd, stgRigaQuant=2)) == 1, "staging righe: upsert idempotente")
    r = q("COUNT(DISTINCT PARTE_NUMERO)")
    E.check(r and int(r[0]["PARTI_PRONTE"]) == 2, f"parti pronte: {r}")
    r = q("FROM THINKAI_DORIN_DDT_STAGING_RIGHE WHERE LOG_KEY = {docGroupId} ORDER BY RIGA_NUMERO")
    E.check([x["RIGA_NUMERO"] for x in r] == [100001, 200001] and float(r[1]["QUANT_RIGA"]) == 2, f"righe complete da staging: {r}")

    r = q("FROM DDT_FOR D WHERE D.COD_CF")
    E.check([x["DOC_ID"] for x in r] == ["2026-DF-000001"], f"recupero post-timeout per data (DATA_DOC con ora): {r}")
    E.check(sql_update(cur, nodo(updates, log, "codiceDocCreato"), sd) == 1, "fissa codice documento sul log")
    E.check(sql_update(cur, [c for _, c in updates if c["table"] == log and "LIKE" in c["where"]][0], sd) == 1,
            "propagazione CREATO alla sola parte 1 del gruppo")
    cur.execute(f"SELECT LOG_KEY, STATO FROM {log} ORDER BY LOG_KEY")
    stati = {x["LOG_KEY"]: x["STATO"] for x in cur.fetchall()}
    E.check(stati.get("DDT_ACMEX123__p01of02.pdf") == "IN_ELABORAZIONE", f"LIKE: '_' trattato come jolly, toccato un altro gruppo: {stati}")
    E.check(stati.get("DDT_ACME_123__p01of02.pdf") == "CREATO", f"parte 1 non propagata: {stati}")
    E.check(sql_update(cur, nodo(updates, log, "logStatoFinale"), sd) == 1, "chiusura log finale")
    r = q("FROM THINKAI_DORIN_DDT_LOG WHERE PIVA")
    E.check(r == [{"ERP_DDT_ID": "2026-DF-000001", "STATO": "CREATO"}], f"anti-duplicato dopo la registrazione: {r}")
    try:
        sql_update(cur, nodo(updates, log, "logStatoFinale"), dict(sd, logStatoFinale="IN_ATTESA_PARTI"))
        E.check(info["v"] < "8.0.16", "il CHECK sullo STATO non ha bloccato 'IN_ATTESA_PARTI'")
    except pymysql.err.OperationalError:
        E.check(True, "")

    cur.execute(f"DROP DATABASE `{db}`")
    print(f"\nEsito: {E.ok} controlli superati, {len(E.ko)} falliti")
    return 1 if E.ko else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
