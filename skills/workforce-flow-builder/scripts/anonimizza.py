#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anonimizza.py — anonimizza flussi WorkForce, note e reference prima di condividerli o versionarli.

Comandi:
    python anonimizza.py applica  <mappa.json> <file|cartella> [...] [--dry-run]
    python anonimizza.py verifica <file|cartella> [...] [--denylist <lista.txt>]

`applica`  sostituisce in ordine le coppie [regex, sostituzione] della mappa.
           ⚠️ La mappa contiene i nomi REALI: tienila fuori dal repository (es. cartella privata,
           file *.privato.json, ignorato da git). Mai pubblicarla.
`verifica` cerca dati identificativi con rilevatori generici (nessun nome reale nel codice):
           email non di esempio, P.IVA/codici fiscali, IBAN, telefoni, percorsi Windows cablati,
           numeri di documento ERP, nomi di istanza SQL; con --denylist cerca anche termini
           privati (uno per riga, la lista resta fuori dal repository).
Exit code 1 se `verifica` trova qualcosa.
"""
import json
import os
import re
import sys

ESTENSIONI = {".md", ".js", ".json", ".txt", ".py", ".sql", ".csv"}
ESCLUSI = {".git", "__pycache__", "dist", "node_modules"}

RILEVATORI = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@(?!example\.(?:com|it)\b)(?!cliente\.it\b)"
                         r"(?!azienda\.it\b)(?!b\.it\b)[A-Za-z0-9.-]+\.[a-z]{2,}\b")),
    ("P.IVA / codice 11 cifre", re.compile(r"(?<![\w.])(?:IT)?(?!01234567890|12345678901|14155238886)"
                                            r"[0-9]{11}(?![0-9])")),
    ("codice fiscale", re.compile(r"\b[A-Z]{6}[0-9]{2}[A-EHLMPRST][0-9]{2}[A-Z][0-9]{3}[A-Z]\b")),
    ("IBAN", re.compile(r"\bIT[0-9]{2}[A-Z][0-9]{10}[0-9A-Z]{12}\b")),
    ("telefono", re.compile(r"(?<![\w.])\+?39[ ]?3[0-9]{2}[ ]?[0-9]{6,7}\b")),
    ("percorso Windows cablato", re.compile(r"(?<![<\w])[A-Za-z]:\\{1,2}(?!\.\.\.)(?!Fatture\\{1,2}In)"
                                             r"(?!WF\b)(?!WorkForce\b)[A-Za-z_][\w .-]*")),
    ("percorso UNC", re.compile(r"\\\\\\\\?[A-Za-z0-9-]+\\{1,2}[A-Za-z0-9$_-]+")),
    ("numero documento ERP", re.compile(r"\b20[0-9]{2}-[0-9A-Z]{3,6}-[0-9]{6,}\b")),
    ("istanza SQL", re.compile(r"\b[a-z0-9-]{3,}\\{1,2}sql[0-9]{2,4}\b", re.I)),
]


def file_da(percorsi):
    for p in percorsi:
        if os.path.isfile(p):
            yield p
            continue
        for radice, cartelle, files in os.walk(p):
            cartelle[:] = [c for c in cartelle if c not in ESCLUSI]
            for f in files:
                if os.path.splitext(f)[1].lower() in ESTENSIONI and ".privato." not in f:
                    yield os.path.join(radice, f)


def applica(mappa_path, percorsi, dry=False):
    regole = [(re.compile(a), b) for a, b in json.load(open(mappa_path, encoding="utf-8"))]
    totale = 0
    for f in file_da(percorsi):
        testo = open(f, encoding="utf-8").read()
        nuovo, n_file = testo, 0
        for rx, sost in regole:
            nuovo, n = rx.subn(lambda m, s=sost: s, nuovo)
            n_file += n
        if n_file:
            totale += n_file
            print(f"{'[dry] ' if dry else ''}{f}: {n_file} sostituzioni")
            if not dry:
                open(f, "w", encoding="utf-8").write(nuovo)
    print(f"--- {totale} sostituzioni ---")
    return 0


def verifica(percorsi, denylist=None):
    termini = []
    if denylist:
        termini = [t.strip() for t in open(denylist, encoding="utf-8") if t.strip() and not t.startswith("#")]
    trovati = 0
    for f in file_da(percorsi):
        for i, riga in enumerate(open(f, encoding="utf-8", errors="replace"), 1):
            for nome, rx in RILEVATORI:
                for m in rx.finditer(riga):
                    trovati += 1
                    print(f"{f}:{i}: [{nome}] {m.group(0)[:60]}")
            low = riga.lower()
            for t in termini:
                if re.search(r"(?<![a-z0-9])" + re.escape(t.lower()) + r"(?![a-z0-9])", low):
                    trovati += 1
                    print(f"{f}:{i}: [denylist] termine privato n.{termini.index(t) + 1}")
    print(f"--- {trovati} possibili dati identificativi ---")
    return 1 if trovati else 0


def main(argv):
    if len(argv) < 3 or argv[1] not in ("applica", "verifica"):
        print(__doc__)
        return 2
    if argv[1] == "applica":
        args = [a for a in argv[3:] if not a.startswith("--")]
        return applica(argv[2], args, dry="--dry-run" in argv)
    deny = argv[argv.index("--denylist") + 1] if "--denylist" in argv else None
    args = [a for a in argv[2:] if not a.startswith("--") and a != deny]
    return verifica(args, deny)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
