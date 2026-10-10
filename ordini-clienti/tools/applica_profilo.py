#!/usr/bin/env python3
"""Genera il flusso "Ordini Clienti" di un'azienda dal template multi-azienda e da un profilo JSON.

Uso:
    python applica_profilo.py <template.thinkaiagent.json> <profilo.json> <output.thinkaiagent.json>

Il profilo ha due sezioni (vedi profili/esempio.profilo.json):
  "agente"    -> valori che il motore NON interpola e vanno scritti nel file prima dell'import:
                 nome dell'agente, tag, credenziale Target Cross, prefisso dei gruppi di idempotenza;
  "parametri" -> valori dello step CONFIGURAZIONE AZIENDA (chiave = nome della variabile).
                 Gli elenchi JSON (depositiJson, cartelleJson, ...) si possono scrivere come
                 oggetti/array veri: lo script li serializza.
Esce con codice 1 se il profilo contiene chiavi sconosciute o lascia segnaposto <...> obbligatori.
"""
import json
import re
import sys

CREDENZIALE_TEMPLATE = "TCRESTAPI"
PREFISSO_IDEMPOTENZA_TEMPLATE = "ordcli"


def carica(percorso):
    with open(percorso, encoding="utf-8") as f:
        return json.load(f)


def sostituisci_letterali(o, credenziale, prefisso):
    """Aggiorna credentialName e idempotencyGroup in tutti gli step, annidati compresi."""
    conta = {"credentialName": 0, "idempotencyGroup": 0}

    def visita(x):
        if isinstance(x, dict):
            for k, v in list(x.items()):
                if k in ("ConfigJson", "configJson") and isinstance(v, str) and v:
                    x[k] = json.dumps(visita(json.loads(v)), ensure_ascii=False, separators=(",", ":"))
                elif k == "credentialName" and v == CREDENZIALE_TEMPLATE:
                    x[k] = credenziale
                    conta[k] += 1
                elif k == "idempotencyGroup" and isinstance(v, str) and v.startswith(PREFISSO_IDEMPOTENZA_TEMPLATE + "-"):
                    x[k] = prefisso + v[len(PREFISSO_IDEMPOTENZA_TEMPLATE):]
                    conta[k] += 1
                else:
                    x[k] = visita(v)
            return x
        if isinstance(x, list):
            return [visita(e) for e in x]
        return x

    visita(o)
    return conta


def main(template_path, profilo_path, out_path):
    flusso = carica(template_path)
    profilo = carica(profilo_path)
    agente = flusso["Agent"]
    m00 = next(s for s in agente["Steps"] if s.get("Alias", "").startswith("CONFIGURAZIONE AZIENDA"))
    cfg = json.loads(m00["ConfigJson"])
    voci = {a["key"]: a for a in cfg["assignments"]}

    errori = []
    for chiave, valore in (profilo.get("parametri") or {}).items():
        if chiave not in voci:
            errori.append("parametro sconosciuto: %s (validi: %s)" % (chiave, ", ".join(voci)))
            continue
        if not isinstance(valore, str):
            valore = json.dumps(valore, ensure_ascii=False, separators=(",", ":"))
        voci[chiave]["value"] = valore
    for chiave, voce in voci.items():
        if re.fullmatch(r"<[^>]*>", voce["value"].strip()):
            errori.append("parametro obbligatorio non compilato: %s" % chiave)
    if errori:
        for e in errori:
            print("ERRORE:", e)
        sys.exit(1)
    m00["ConfigJson"] = json.dumps(cfg, ensure_ascii=False, separators=(",", ":"))

    meta = profilo.get("agente") or {}
    ragione = voci["ragioneSocialeAzienda"]["value"]
    agente["Name"] = meta.get("nome") or agente["Name"].replace("<RAGIONE_SOCIALE_AZIENDA>", ragione)
    tag = meta.get("tag") or ragione
    if tag and tag not in agente["Tags"]:
        agente["Tags"].append(tag)
    conta = sostituisci_letterali(agente["Steps"],
                                  meta.get("credenzialeErp") or CREDENZIALE_TEMPLATE,
                                  meta.get("prefissoIdempotenza") or PREFISSO_IDEMPOTENZA_TEMPLATE)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(flusso, f, ensure_ascii=False, indent=2)
    print("Creato %s per '%s': %d parametri, %d step Target Cross, %d gruppi di idempotenza."
          % (out_path, ragione, len(voci), conta["credentialName"], conta["idempotencyGroup"]))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    main(*sys.argv[1:])
