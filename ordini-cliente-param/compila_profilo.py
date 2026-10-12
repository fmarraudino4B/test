#!/usr/bin/env python3
"""Compila il flusso ordini cliente parametrico con un profilo cliente PRIVATO.

Uso:  python compila_profilo.py profilo-<cliente>.privato.json [--flusso F.js] [--out OUT.js]
      python compila_profilo.py profilo-<cliente>.privato.json --schema   # solo lo script SQL delle tabelle

Sostituisce i <SEGNAPOSTO> del flusso con i valori del profilo (escape JS incluso), rifiuta
valori mancanti o segnaposto residui e controlla la sintassi con `node --check` se disponibile.
Il file generato contiene dati reali del cliente: tienilo FUORI dal repository (*.privato.js).
"""
import argparse, json, os, re, shutil, subprocess, sys

QUI = os.path.dirname(os.path.abspath(__file__))
FLUSSO = os.path.join(QUI, "Ordine_Cliente_PARAM_v2.0.0_flusso.js")

def b(v):
    return "true" if v else "false"

def mappa(p):
    i, c, n, d, s, o = (p.get(k, {}) for k in ("identita", "cartelle", "notifiche", "documentoErp", "soglie", "opzioni"))
    dms = o.get("dms", {})
    short = i.get("ownShortName", "")
    return {
        "NOME_AGENTE": (i.get("agentVersion", ""), True),
        "RAGIONE_SOCIALE_PROPRIA": (i.get("ownName", ""), True),
        "NOME_BREVE_PROPRIO": (short, True),
        "NOME_BREVE_PROPRIO_MAIUSC": (short.upper(), True),
        "PIVA_PROPRIA": (i.get("ownVat", ""), True),
        "CREDENZIALE_ERP": (i.get("credenzialeErp", ""), True),
        "PREFISSO_TABELLE": (i.get("prefissoTabelle", ""), True),
        "WORK_ROOT": (c.get("workRoot", ""), True),
        "CARTELLA_INPUT": (c.get("inputDirectory", ""), True),
        "CARTELLA_DMS": (c.get("dmsDirectory", ""), bool(dms.get("attivo"))),
        "EMAIL_OPERATORE": (n.get("operatorEmail", ""), True),
        "EMAIL_CC": (n.get("operatorEmailCc", ""), False),
        "CAUSALE_DOC": (d.get("defaultCausale", ""), True),
        "SERIE_DOC": (d.get("defaultSerie", ""), True),
        "DEPOSITO": (d.get("defaultDeposito", ""), True),
        "DEST_WS_READY": (b(d.get("destinationWsReady", False)), True),
        "ABILITA_OFFERTA_PROPRIA": (b(o.get("abilitaOffertaPropria", True)), True),
        "ABILITA_KIT": (b(o.get("abilitaKit", True)), True),
        "DMS_ATTIVO": (b(dms.get("attivo", True)), True),
        "DMS_CLASSE_DOC": (dms.get("classeDocumento", ""), bool(dms.get("attivo"))),
        "DMS_ATTRIBUTO_CHIAVE": (dms.get("chiaveEsterna", ""), bool(dms.get("attivo"))),
        "DMS_ATTRIBUTI_EXTRA": (dms.get("attributiExtra", ""), False),
        "SOGLIA_PERCENTUALE": (str(s.get("minPercentualeRisoltePerCreare", "")), True),
        "SOGLIA_ASSOLUTA": (str(s.get("minPercentualeAssolutaPerCreare", "")), True),
        "ALIAS_CLIENTI": (o.get("aliasClienti", ""), False),
    }

def schema(profilo, out):
    prefisso = str(profilo.get("identita", {}).get("prefissoTabelle", "")).strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{2,40}_", prefisso):
        sys.exit("ERRORE: identita.prefissoTabelle deve essere un identificatore SQL che finisce con '_' (es. THINKAI_CLIENTE_)")
    src = open(os.path.join(QUI, "schema_tabelle_ordini.sql"), encoding="utf-8").read()
    src = src.replace("<PREFISSO_TABELLE>", prefisso)
    residui = sorted(set(re.findall(r"<[A-Z][A-Z0-9_]{3,}>", src)))
    if residui:
        sys.exit("segnaposto non risolti: " + ", ".join(residui))
    out = out or "schema-tabelle-" + prefisso.strip("_").lower() + ".privato.sql"
    open(out, "w", encoding="utf-8").write(src)
    print("OK ->", out)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profilo")
    ap.add_argument("--flusso", default=FLUSSO)
    ap.add_argument("--out")
    ap.add_argument("--schema", action="store_true", help="genera solo lo script SQL delle tabelle (serve solo il prefisso)")
    a = ap.parse_args()
    profilo = json.load(open(a.profilo, encoding="utf-8"))
    if a.schema:
        return schema(profilo, a.out)
    src = open(a.flusso, encoding="utf-8").read()
    errori = []
    for k, (v, obbligatorio) in mappa(profilo).items():
        if obbligatorio and not str(v).strip():
            errori.append(f"valore mancante per <{k}>")
            continue
        if "<" in str(v) and re.search(r"<[A-Z0-9_]+>", str(v)):
            errori.append(f"<{k}>: il valore contiene un segnaposto")
            continue
        src = src.replace(f"<{k}>", json.dumps(str(v), ensure_ascii=False)[1:-1])
    if not re.fullmatch(r"\d{11}", str(profilo.get("identita", {}).get("ownVat", ""))):
        errori.append("ownVat: servono 11 cifre")
    residui = sorted(set(re.findall(r"<[A-Z][A-Z0-9_]{3,}>", src)))
    if residui:
        errori.append("segnaposto non risolti: " + ", ".join(residui))
    if errori:
        sys.exit("ERRORE:\n  " + "\n  ".join(errori))
    out = a.out or os.path.splitext(a.profilo)[0].replace("profilo-", "flusso-") + ".privato.js"
    open(out, "w", encoding="utf-8").write(src)
    if shutil.which("node"):
        r = subprocess.run(["node", "--check", out], capture_output=True, text=True)
        if r.returncode:
            sys.exit("SINTASSI NON VALIDA:\n" + r.stderr)
    print("OK ->", out)

if __name__ == "__main__":
    main()
