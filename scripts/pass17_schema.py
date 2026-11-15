#!/usr/bin/env python3
"""Generate a documentation dictionary from frozen exports; output only docs/v1.1/db/SCHEMA_v1.md."""
import csv
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/v1.1/db/SCHEMA_v1.md'
STRINGS=set('run_id seller_id buyer_id order_id audit_id task_id portfolio_id config_hash jurisdiction claimed_model actual_model strategy_id state attack_mode jurisdiction_path route_policy mode method label policy seller_learner audit_rule roster_seed router audit cell_id arm penalty_label learner metric baseline_cell_id skip_reason report_family decision_a_family seller_key declared_model seller_jurisdiction'.split())
BOOLS=set('tail_trade compliance_filter trust_feedback audit_efficacy_evidence_allowed Q_identifiable baseline_Q_identifiable testable significant_report significant_decision_a result1_hit report_hit all_supporting_learners_at_or_above_astar correct label_correct'.split())
COUNTS=set('seed capacity banned_until_round round tokens_billed tokens_actual reputation_rounds n_audits tail_trade_sellers tail_sales n_strategic Q_present_rounds delisted_rounds_tail n_served n_runs tail_trade_runs n_attempts n_buyers n_target_served delist_rounds'.split())
COUNTS.update('n_tasks n_rounds tail_rounds billed_tokens_total'.split())
BITS=set('sampled identity_check length_check hit miss label_revealed fraud_realized fraud_future fraud_future_swap fraud_future_theft fraud_future_downgrade'.split())
PRIV=set('actual_model latent_q_swap latent_q_theft attack_mode correct label_correct fraud_realized tokens_actual'.split())
UNITS={
 'n_tasks':'task instances','n_rounds':'rounds','tail_rounds':'rounds in Q tail','strategic_tail_counts':'JSON object: seller ID → allowed tail purchases','audit_checks':'JSON list of check categories','budget_multiplier':'dimensionless budget scaling factor',
 'audit_rate_realised_mean':'mean audits / allowed purchases over runs','served_share_of_run':'seller served purchases / run served purchases in feature window','fraud_order_share_target':'attacked / allowed target purchases','fraud_billed_token_share_target':'attacked billed / all billed target tokens',
 'list_price':'synthetic currency / 1K billed tokens','price':'synthetic currency / 1K billed tokens',
 'quoted_price_mean':'synthetic currency / 1K billed tokens','quoted_price_std':'same price units',
 'budget_total':'synthetic currency','budget_remaining':'synthetic currency','stake':'synthetic currency',
 'stake_remaining':'synthetic currency','amount_escrow':'synthetic currency','amount_paid':'synthetic currency, includes corridor fee',
 'slash_amount':'synthetic currency','auditor_cost':'synthetic currency','penalty':'synthetic currency',
 'cost':'synthetic currency total, excludes audit','audit_cost':'synthetic currency total',
 'cost_per_task':'synthetic currency / task','J':'dimensionless joint objective',
 't_submit':'Unix seconds; shared simulated log timestamp','t_deliver':'Unix seconds; not independent observed delivery',
 't_settle':'Unix seconds; not independent observed settlement','L':'task-step delay; null = never',
 'label_delay_L':'task-step delay; null = never','reputation_rounds':'rounds','round':'zero-based round',
 'delist_rounds':'rounds','banned_until_round':'round watermark','seed':'seed identifier',
 'Q_present_rounds':'seller-rounds','delisted_rounds_tail':'seller-rounds',
 'n_served':'allowed purchases','n_target_served':'target-window allowed purchases',
 'n_attempts':'feature-window attempts','n_buyers':'distinct served buyers',
 'n_runs':'runs','tail_trade_runs':'runs','tail_trade_sellers':'sellers','tail_sales':'allowed purchases',
 'n_strategic':'sellers','capacity':'purchases / round',
 'config_hash':'first 16 SHA256 hex characters of per-run config JSON',
 'seller_key':'first 12 SHA256 hex characters of run_id|seller_id',
 'E':'attacked allowed purchases / allowed purchases',
 'fraud_share':'same per-purchase exposure as E','E_tok':'attacked billed tokens / all billed tokens',
 'Q':'unweighted average of available per-mode intent','quality':'correct final tasks / all tasks',
 'accuracy':'correct final tasks / all tasks','fill_rate':'tasks with service / all tasks',
 'violation_rate':'violating allowed purchases / all tasks','audit_rate_realised':'audits / allowed purchases',
 'active_attack_rate':'legacy realized attacked / allowed purchases; not Q',
 'listed_quality':'difficulty → configured accuracy map','listed_quality_mean':'mean configured accuracy',
 'compliance_profile':'scenario-control JSON object','astar_relation':'JSON object: relation and frozen break-even bounds',
 'per_run_strategic_tail_counts':'JSON list: seed, tail_sales, by_seller counts',
 'report':'JSON direction-consistency object','decision_a':'JSON direction-consistency object',
 'astar_by_learner':'JSON object keyed by learner',
 'n_audits':'allowed audited purchases','n_target_served':'target-window served purchases'}

SPECS=[
 ('Legacy sellers','exports/production/sellers.jsonl','One catalog seller per run; key (run_id, seller_id); join orders on those fields.'),
 ('Legacy buyers','exports/production/buyers.jsonl','One buyer per run; key (run_id, buyer_id); join orders on those fields.'),
 ('Legacy orders','exports/production/orders.jsonl','One purchase attempt or unfilled task line; key order_id (retain run_id when combining files); seller_id nullable for unfilled. portfolio_id = task_id groups task purchases.'),
 ('Legacy audits','exports/production/audits.jsonl','One row per allowed purchase, including unsampled audits; key audit_id; order_id joins orders one-to-one on the served subset.'),
 ('Legacy episodes','exports/production/episodes.jsonl','One run summary; key (run_id, seed); joins other layers on run_id, seed.'),
 ('Official 40-seller board','results/v1.0/main/per_seed.csv','One method × π × seed run; key (method, pi, seed) within one learner/config directory. No run_id or a column. Keep source directory/learner when combining boards.'),
 ('Decision A raw board','results/v1.1/v1.2_decision_a/factorial/per_seed.csv','One cell × learner × seed run; key (cell_id, learner, seed). Join readout cells on (cell_id, learner).'),
 ('Decision A cells','results/v1.1/v1.2_decision_a_eval/cells.csv','One cell × learner summary; key (cell_id, learner). Nested JSON estimates are marginal mean/lo/hi.'),
 ('Decision A contrasts','results/v1.1/v1.2_decision_a_eval/contrasts.csv','One nonreference cell × learner × metric; key (cell_id, learner, metric); join baseline_cell_id, learner to cells.'),
 ('Decision A direction votes','results/v1.1/v1.2_decision_a_eval/direction_consistency.csv','One router × audit × penalty × metric vote summary; key those four fields. Nested objects list participating learners and break-even relations.'),
 ('T4 features','results/v1.0/t4_eval/export/features_train.csv','One run × seller feature window; key (run_id, seller_key); seed is split metadata. Same fields in test/PILOT exports.'),
 ('T4 labels','results/v1.0/t4_eval/export/labels_train.csv','One run × seller target window and private references; key (run_id, seller_key). Join features on both fields. Same fields in test/PILOT exports.')]

def read(path):
 if path.suffix=='.csv':
  with path.open() as f:return list(csv.DictReader(f))
 return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]

def dtype(k,vals):
 if k in STRINGS:return 'string'
 if k in BOOLS:return 'boolean'
 if k in BITS:return 'integer 0/1'
 if k in COUNTS:return 'integer'
 if any(isinstance(v,(dict,list)) for v in vals):return 'object/list'
 if any(isinstance(v,str) and v.startswith(('{','[')) for v in vals):return 'JSON string → object/list'
 if k in ('L','label_delay_L'):return 'integer or null'
 return 'number'

def unit(k):
 if k in UNITS:return UNITS[k]
 if k in STRINGS:return 'identifier / category' if 'id' in k or 'key' in k else 'category / text'
 if k in BOOLS or k in BITS:return 'boolean indicator'
 if k.startswith('latency'):return 'milliseconds'
 if 'billed_tokens' in k or k.startswith('leakref_') or k in ('tokens_billed','tokens_actual'):return 'tokens'
 if k.startswith(('p_raw','p_holm')):return 'adjusted/unadjusted probability as named'
 if k in ('delta_mean','delta_lo','delta_hi'):return 'same units as metric; audit minus baseline'
 if k.startswith(('fraud_share','Q_','q_','learned_q','latent_q')) or k.endswith(('share','rate')) or k in ('pi','a','reveal_pi'):return 'dimensionless fraction/probability'
 if k in COUNTS:return 'count'
 if k in ('E','Q','E_tok','accuracy','cost_per_task'):return UNITS[k]
 return 'dimensionless; see code source below'

def nullable(k,rows):
 observed=any(r.get(k) is None or r.get(k)=='' for r in rows)
 if observed:return 'yes (empty/null observed)'
 if k in ('seller_id','t_deliver','t_settle','correct','label_correct','L','label_delay_L','skip_reason','p_raw','p_holm_report','p_holm_decision_a','decision_a_family','q_delisted_mean') or k.startswith(('Q','q_','learned_q','latency','fraud_future','leakref_')) or k in ('fraud_order_share_target','fraud_billed_token_share_target'):
  return 'conditional; no null in this file'
 return 'none observed; not a general validator'

def visibility(k,title):
 if k in ('run_id','seed','seller_key','order_id','audit_id','buyer_id','seller_id','task_id','portfolio_id'):return 'key/metadata; exclude T4 predictor IDs'
 if title=='T4 labels':return 'evaluation/private; not a predictor'
 if title=='T4 features':return 'buyer feature whitelist'
 if title.startswith('Decision A') or title=='Official 40-seller board' or title=='Legacy episodes':return 'evaluation/config metadata; not T4 input'
 if k in PRIV or k in ('hit','miss'):return 'evaluation/private; not a T4 predictor'
 return 'legacy observable/config; not automatically T4-whitelisted'

def main():
 lines=['# Schema v1 — versioned documentation (2026-11-15)','',
 'Precedence: frozen files and their producing code define each representation; `main.tex` §Feature / Label separation governs T4 admissibility. This dictionary documents coexistence, not a single interchangeable format. `docs/DATA_SCHEMA.md` remains the legacy reference. No legacy five-file export can be losslessly relabeled as the official 40-seller board: it lacks listed-round Q histories and the complete method grid. Decision A has different cells/rounds/audit settings; do not concatenate it as another v1.0 method. T4 is a windowed seller aggregation, not an episode board.','',
 'CSV types below are logical types: parse booleans from True/False, numbers explicitly, and JSON-valued cells with `json.loads`. Empty CSV cells denote missing/undefined values, not zero. JSONL uses JSON null. Nullability combines observed nulls and code-defined conditional cases; “none observed” does not assert a universal validator. Units are synthetic unless explicitly time/tokens. Each section fixes row granularity, primary key and joins; these apply to every field in its table.','',
 'Source implementations: `tokenmarket/benchmark_export.py` (legacy field lists/builders), `scripts/run_v1.py`, `tokenmarket/v1_metrics.py` and `tokenmarket/metrics.py` (board), `tokenmarket/decision_a.py`, `scripts/v1.1/analyze_decision_a.py` (readouts), `tokenmarket/t4_export.py` (T4). Statistical JSON estimates have number-or-null `mean`, `lo`, `hi`; contrast endpoints are paired differences. Rates refer to their named denominator; see METRICS_INTERPRETATION.md.','']
 for title,name,grain in SPECS:
  rows=read(ROOT/name);header=list(rows[0]);lines += ['## '+title,'',f'Frozen example: `{name}`. {grain}', '',
   '| Field | Logical type | Unit / meaning | Nullability | Visibility |','|---|---|---|---|---|']
  for k in header:
   lines.append(f"| `{k}` | {dtype(k,[r.get(k) for r in rows])} | {unit(k)} | {nullable(k,rows)} | {visibility(k,title)} |")
  # Tiny verbatim projection: preserve source values, no new scientific estimate.
  keys=header[:4]+[k for k in ['E','Q','fraud_future','quoted_price_mean','config_hash'] if k in header and k not in header[:4]]
  ex={k:rows[0][k] for k in keys}
  lines += ['', 'Tiny example: first frozen row projected to these fields; CSV strings retained verbatim.', '', '```json',json.dumps(ex,ensure_ascii=False), '```','']
 lines += ['## Conversion and joins','',
 'Legacy `orders.order_id` follows the raw `purchase_id` where present, else an exporter fallback. Audit rows cover served purchases only. Use run_id with seller/buyer IDs; seller catalog values are not chronological seller-state histories. `t_submit/t_deliver/t_settle` reuse log timestamps and are not independent measured events. `episodes.active_attack_rate` describes realized purchase attacks, while `learned_q_*` are separate legacy values; neither is a substitute for official Q.', '',
 'Official CSV `config_hash` is a per-run config JSON SHA256 prefix, not the YAML file hash. The method encodes the audit setting; there is no standalone a or L column. `seller_learner` and input directory disambiguate equivalent method/π/seed keys across learners. Official board has no seller-level join; to recover it use raw transaction logs with matching run metadata, not an invented run_id.', '',
 'Decision A cells join raw run rows on cell_id + learner. Contrasts join twice (cell_id and baseline_cell_id) with learner. Direction votes aggregate learners and join by router, audit, penalty, metric. `decision_a_eval.json` contains the same cell/contrast/vote records plus protocol hashes, input checks, RNG/bootstrap/family metadata and classification; it is not a per-purchase table. JSON-valued CSVs preserve nested data; flattening requires explicit field paths.', '',
 'T4 keys are run_id + seller_key, never seller_key alone. `seller_id` appears in private labels to map back to raw logs. The manifest records run/seed membership, feature/target windows, whitelist and counts. Target labels are empty if no target-window purchase was served. Private `leakref_*` fields summarize feature-window actual tokens for the leakage checker and are not predictors. `n_target_served` distinguishes missing targets from true negatives. Feature activity/window statistics are not full-run board metrics. See T4_FEATURES.md.', '',
 'Raw transaction logs, where retained, use `tokenmarket/logging_schema.py:SCHEMA`: one allowed/blocked attempt or unfilled-task row; `(run_id, task_id, portfolio_step)` locates a line and `purchase_id` supports audit joins. Last task row carries final outcome. Cache joins use `(model_name,prompt_sha256,max_new_tokens)`, not transaction task_id. Long task source IDs and revisions are documented in TASKS_AND_CACHE.md.']
 OUT.write_text('\n'.join(lines)+'\n')
 print('Wrote',OUT,'sections',len(SPECS))

if __name__=='__main__':main()
