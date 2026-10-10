# -*- coding: utf-8 -*-
"""Lettura/scrittura di un export ThinkAI WorkForce (.thinkaiagent.json).

Gli step annidati stanno dentro `ConfigJson`/`configJson` come stringhe JSON: qui vengono
decodificati, passati a una funzione di trasformazione e ricodificati, a qualunque profondita'.
"""
import json


def _is_step(o):
    return isinstance(o, dict) and ('ConfigJson' in o or 'configJson' in o) and ('Type' in o or 'type' in o)


def _walk_cfg(value, fn):
    if isinstance(value, dict):
        if _is_step(value):
            _walk_step(value, fn)
            return
        for v in value.values():
            _walk_cfg(v, fn)
    elif isinstance(value, list):
        for v in value:
            _walk_cfg(v, fn)


def _walk_step(step, fn):
    key = 'ConfigJson' if 'ConfigJson' in step else 'configJson'
    raw = step[key]
    cfg = json.loads(raw) if isinstance(raw, str) and raw.strip().startswith('{') else None
    if cfg is not None:
        _walk_cfg(cfg, fn)          # prima i figli, poi lo step stesso
    fn(step, cfg)
    if cfg is not None:
        step[key] = json.dumps(cfg, ensure_ascii=False, separators=(',', ':'))


def each_step(doc, fn):
    """Chiama fn(step, cfg) per ogni step (anche annidato). cfg e' modificabile in place."""
    for s in doc['Agent']['Steps']:
        _walk_step(s, fn)


def load(path):
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def save(doc, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write('\n')


def step_id(step):
    return step.get('editorId')


def step_alias(step):
    return step.get('Alias', step.get('alias'))


def set_alias(step, value):
    step['Alias' if 'Alias' in step else 'alias'] = value


def step_note(step):
    return step.get('Note', step.get('note'))


def set_note(step, value):
    step['Note' if 'Type' in step else 'note'] = value
