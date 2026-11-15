#!/usr/bin/env python3
"""Document frozen task/cache and schema evidence; write only docs/v1.1/db/."""
import csv
import hashlib
import importlib.metadata
import json
import sys
from collections import Counter
from pathlib import Path
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tokenmarket.config import load_config
from tokenmarket.tasks import build_task_pool
OUT=ROOT/'docs/v1.1/db'

def read_jsonl(p):
    return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    evidence={'date':'2026-11-15','kind':'documentation counts, not revised paper results','files':{},'pools':{}}
    for name in ['data/raw/gsm8k_test.jsonl','data/raw/math500_test.jsonl','data/long_tasks.jsonl','cache/llm_outputs.jsonl']:
        p=ROOT/name;rows=read_jsonl(p)
        d={'rows':len(rows),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
        if 'cache/' in name:
            d.update(unique_cache_keys=len({(r['model_name'],r['prompt_sha256'],r['max_new_tokens']) for r in rows}),
                     unique_prompt_hashes=len({r['prompt_sha256'] for r in rows}),
                     unique_pool_task_ids=len({r['pool_task_id'] for r in rows}),
                     by_model=dict(Counter(r['model_name'] for r in rows)),
                     by_model_limit={str(k):v for k,v in Counter((r['model_name'],r['max_new_tokens']) for r in rows).items()})
        else:
            question='problem' if 'math500_test' in name else 'question'
            d['unique_question_texts']=len({r[question] for r in rows})
            if 'long_tasks' in name:
                d['unique_ids']=len({r['id'] for r in rows});d['by_source']=dict(Counter(r['source'] for r in rows))
        evidence['files'][name]=d
    for name in ['configs/default.yaml','configs/benchmark/production.yaml','configs/v1.0/scale.yaml']:
        pool=build_task_pool(load_config(ROOT/name))
        evidence['pools'][name]={'rows':len(pool),'unique_ids':len({r.task_id for r in pool}),'unique_questions':len({r.question for r in pool}),
             'by_source':dict(Counter(r.source for r in pool)),'task_seed':load_config(ROOT/name)['task_pool'].get('task_seed')}
    (OUT/'TASK_COUNTS.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(evidence,indent=2))

if __name__=='__main__':main()
