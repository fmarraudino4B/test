#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera il flusso DDT Fornitori configurato per un'azienda.

Uso:
    python applica_profilo.py <template.thinkaiagent.json> <profilo.json> <uscita.thinkaiagent.json>

Il profilo (vedi profili/profilo-cliente.template.json) contiene:
  - cliente.nome / cliente.sigla : nome visibile e sigla tecnica (tabelle THINKAI_<SIGLA>_*,
                                   prefisso delle chiavi di idempotenza in minuscolo);
  - erp.credenziale              : nome della credenziale TcRestAPI in Studio (letterale, R19);
  - configurazione               : valori dello step CONFIGURAZIONE CLIENTE (stesse chiavi).
I valori *Json possono essere scritti come oggetti/array JSON: vengono serializzati qui.
Il comando si ferma se resta un segnaposto <...> non compilato o se un valore non e' valido.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wfjson as W  # noqa: E402

SEGNAPOSTO = re.compile(r'<(?:CLIENTE|cliente|CREDENZIALE_ERP|NOME_CLIENTE|WORK_ROOT|RAGIONE_SOCIALE_AZIENDA|SIGLA_AZIENDA|PIVA_AZIENDA)>')
MAPPE_FLUSSO = ('causaliPerFlussoJson', 'seriePerFlussoJson', 'depositiPerFlussoJson', 'magazziniPerFlussoJson')


def errore(msg):
    raise SystemExit('ERRORE: ' + msg)


def normalizza_configurazione(conf):
    out = {}
    for k, v in conf.items():
        if k.endswith('Json') and not isinstance(v, str):
            v = json.dumps(v, ensure_ascii=False, separators=(',', ':'))
        elif isinstance(v, bool):
            v = 'true' if v else 'false'
        elif v is None:
            v = ''
        elif not isinstance(v, str):
            v = str(v)
        out[k] = v
    for k in MAPPE_FLUSSO:
        if k in out:
            try:
                m = json.loads(out[k] or '{}')
            except ValueError as e:
                errore('%s non e\' JSON valido: %s' % (k, e))
            if not isinstance(m, dict):
                errore('%s deve essere un oggetto {"1":..,"6":..,"*":..}' % k)
            extra = [x for x in m if x not in ('1', '2', '3', '4', '5', '6', '*')]
            if extra:
                errore('%s: chiavi non riconosciute %s (ammesse "1".."6" e "*")' % (k, extra))
            if k == 'causaliPerFlussoJson' and '*' in m:
                errore('causaliPerFlussoJson non ammette "*": la causale si imposta flusso per flusso')
    if 'prefissiArticoliJson' in out:
        try:
            if not isinstance(json.loads(out['prefissiArticoliJson'] or '[]'), list):
                errore('prefissiArticoliJson deve essere un array')
        except ValueError as e:
            errore('prefissiArticoliJson non e\' JSON valido: %s' % e)
    if 'ownVat' in out:
        out['ownVat'] = re.sub(r'\D', '', out['ownVat'])
        if len(out['ownVat']) != 11:
            errore('ownVat deve avere 11 cifre')
    if out.get('campoMagazzino') and not re.match(r'^[A-Za-z][A-Za-z0-9_]*$', out['campoMagazzino']):
        errore('campoMagazzino deve essere un nome di campo (lettere, cifre, _)')
    for k in ('operatorEmail',):
        if k in out and not re.match(r'^[^@\s,;]+@[^@\s,;]+\.[^@\s,;]+$', out[k]):
            errore('%s non e\' un indirizzo email valido' % k)
    return out


def main(argv):
    if len(argv) != 4:
        print(__doc__)
        return 2
    doc = W.load(argv[1])
    with open(argv[2], encoding='utf-8-sig') as f:
        prof = json.load(f)
    nome = (prof.get('cliente') or {}).get('nome', '').strip()
    sigla = (prof.get('cliente') or {}).get('sigla', '').strip().upper()
    cred = (prof.get('erp') or {}).get('credenziale', '').strip()
    if not nome:
        errore('cliente.nome mancante')
    if not re.match(r'^[A-Z][A-Z0-9_]{1,19}$', sigla):
        errore('cliente.sigla: solo lettere maiuscole, cifre e _ (max 20), es. ACME')
    if not re.match(r'^[A-Za-z0-9_.-]+$', cred):
        errore('erp.credenziale mancante o non valida')
    conf = normalizza_configurazione(prof.get('configurazione') or {})

    sconosciute = []
    trovato_m00 = []

    def letterali(text):
        return (text.replace('<CLIENTE>', sigla).replace('<cliente>', sigla.lower())
                    .replace('<CREDENZIALE_ERP>', cred).replace('<NOME_CLIENTE>', nome))

    def fix(value):
        if isinstance(value, str):
            return letterali(value)
        if isinstance(value, list):
            return [fix(x) for x in value]
        if isinstance(value, dict):
            return {k: fix(v) for k, v in value.items()}
        return value

    def step(s, cfg):
        for k in ('Alias', 'alias', 'Note', 'note'):
            if isinstance(s.get(k), str):
                s[k] = letterali(s[k])
        if cfg is None:
            return
        if 'assignments' in cfg:
            trovato_m00.append(True)
            chiavi = [a['key'] for a in cfg['assignments']]
            for k in conf:
                if k not in chiavi:
                    sconosciute.append(k)
            for a in cfg['assignments']:
                if a['key'] in conf:
                    a['value'] = conf[a['key']]
        for k in list(cfg.keys()):
            if k in ('thenSteps', 'elseSteps', 'subSteps', 'itemErrorSteps', 'cases', 'onErrorSteps'):
                continue
            cfg[k] = fix(cfg[k])

    W.each_step(doc, step)
    if len(trovato_m00) != 1:
        errore('il template deve contenere un solo step di configurazione (SetFields)')
    if sconosciute:
        errore('chiavi di configurazione non presenti nel template: %s' % sconosciute)

    a = doc['Agent']
    a['Name'] = letterali(a['Name']).replace(' - V2.0 parametrico', ' - V2.0')
    a['Description'] = letterali(a['Description'])
    a['Tags'] = [letterali(t) for t in a.get('Tags', []) if t != 'parametrico']
    doc['Warnings'] = [letterali(w) for w in doc.get('Warnings', [])]

    testo = json.dumps(doc, ensure_ascii=False)
    resti = sorted(set(SEGNAPOSTO.findall(testo)))
    if resti:
        errore('segnaposto non compilati: %s (compilali nel profilo)' % ', '.join(resti))
    W.save(doc, argv[3])
    print('OK: %s' % argv[3])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
