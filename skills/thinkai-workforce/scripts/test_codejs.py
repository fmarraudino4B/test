#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_codejs.py — estrae i corpi CodeJs da un flusso DSL (o da un .md con blocchi ```js),
li controlla con `node --check` e, opzionalmente, li ESEGUE con dati sintetici simulando
il sandbox di WorkForce.

Uso:
    python test_codejs.py <flusso.js|file.md>                      # sintassi + costrutti vietati
    python test_codejs.py <flusso.js> --run <stepdata.json>        # esegue in sequenza tutti i CodeJs
    python test_codejs.py <flusso.js> --run <stepdata.json> --only <outputKey[,outputKey...]>

Simulazione del sandbox (evidenza dai run reali, vedi references/conflitti-risolti.md):
  - String() e Number() NON esistono come costruttori  -> nel test valgono undefined
  - $input contiene solo l'output del nodo immediatamente precedente
  - il valore di return finisce in stepData[outputKey] se outputKey e' definito
Richiede node nel PATH. Exit code 1 se un controllo fallisce.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

CODEJS = re.compile(r'^\s*CodeJs\s*\(\s*(\{[^)]*?\})?\s*,?\s*\(\s*\)\s*=>\s*\{\s*$')
OUTKEY = re.compile(r'outputKey\s*:\s*"(\w+)"')
VIETATI = [
    (re.compile(r'(?<![\w.$])String\s*\('), "String() non esiste nel sandbox: usa '' + valore"),
    (re.compile(r'(?<![\w.$])Number\s*[.(]'), "Number()/Number.* non esiste nel sandbox: usa +valore / parseFloat"),
    (re.compile(r'\$input\.(last\w+)'), None),
]

HARNESS = r"""
const fs = require('fs');
const [,, bodiesPath, stepPath, only] = process.argv;
const bodies = JSON.parse(fs.readFileSync(bodiesPath, 'utf8'));
const stepData = JSON.parse(fs.readFileSync(stepPath, 'utf8'));
let input = {};
let failed = 0;
for (const b of bodies) {
  if (only && !only.split(',').includes(b.key)) continue;
  try {
    const fn = new Function('stepData', '$input', 'String', 'Number', b.body);
    const out = fn(stepData, input, undefined, undefined);
    if (b.key) stepData[b.key] = out;
    input = (out && typeof out === 'object') ? out : { value: out };
    console.log(`OK   riga ${b.line} ${b.key || ''}`);
  } catch (e) {
    failed++;
    console.log(`FAIL riga ${b.line} ${b.key || ''}: ${e.message}`);
  }
}
console.log('--- stepData finale ---');
console.log(JSON.stringify(stepData, null, 2));
process.exit(failed ? 1 : 0);
"""


def estrai(testo):
    """Ritorna [(riga, outputKey, corpo)] per ogni CodeJs, anche dentro blocchi ```js di un .md."""
    righe = testo.splitlines()
    out, i = [], 0
    while i < len(righe):
        m = CODEJS.match(righe[i])
        if not m:
            i += 1
            continue
        key = OUTKEY.search(m.group(1) or "")
        corpo, depth, j = [], 1, i + 1
        while j < len(righe):
            r = righe[j]
            depth += r.count("{") - r.count("}")
            if depth <= 0:
                break
            corpo.append(r)
            j += 1
        out.append((i + 1, key.group(1) if key else None, "\n".join(corpo)))
        i = j + 1
    return out


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    testo = open(args[0], encoding="utf-8").read()
    blocchi = estrai(testo)
    print(f"=== {len(blocchi)} CodeJs trovati in {args[0]} ===")
    errori = 0
    tmpdir = tempfile.mkdtemp()
    for n, (riga, key, corpo) in enumerate(blocchi):
        for rx, msg in VIETATI:
            for mm in rx.finditer(corpo):
                if msg:
                    print(f"[ERRORE] riga {riga} {key or ''}: {msg}")
                    errori += 1
        p = os.path.join(tmpdir, f"b{n}.js")
        with open(p, "w", encoding="utf-8") as f:
            f.write("function __codejs(stepData, $input) {\n" + corpo + "\n}\n")
        r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
        if r.returncode:
            errori += 1
            dettaglio = (r.stderr.strip().splitlines() or ["?"])
            print(f"[ERRORE] riga {riga} {key or ''}: sintassi JS non valida -> {dettaglio[-1]}")
    if "--run" in argv:
        idx = argv.index("--run")
        stepfile = argv[idx + 1]
        only = argv[argv.index("--only") + 1] if "--only" in argv else ""
        bp = os.path.join(tmpdir, "bodies.json")
        json.dump([{"line": r, "key": k, "body": b} for r, k, b in blocchi], open(bp, "w"))
        hp = os.path.join(tmpdir, "harness.js")
        open(hp, "w").write(HARNESS)
        r = subprocess.run(["node", hp, bp, stepfile, only], capture_output=True, text=True)
        print(r.stdout + r.stderr)
        if r.returncode:
            errori += 1
    print(f"--- {errori} errori ---")
    return 1 if errori else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
