#!/usr/bin/env python3
"""Build a table/figure documentation map from paper labels; write only docs/v1.1/db/."""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PAPER=ROOT/'docs/latex-sigkdd-v1.0'
OUT=ROOT/'docs/v1.1/db'
MAIN='results/v1.0/main/'
DEC='results/v1.1/v1.2_decision_a_eval/'
PROT='docs/PROTOCOL_v1.0.md'
CFG=['configs/v1.0/scale.yaml','configs/benchmark/production.yaml','configs/default.yaml']
A='python scripts/v1/analyze_scale_v1.py --in results/v1.0/main --peer results/v1.0/main_fp --out /tmp/pass17-main-analysis'
D='python scripts/pass12_decision_a_tables.py (no flags; hard-coded paper output, run only in scratch mirror)'
F='python scripts/figures_nature.py (no flags; hard-coded output, run only in scratch mirror)'

def main():
 text=(PAPER/'main.tex').read_text()
 # Resolve inputs in paper order; the facts input defines macros and contains no table labels.
 expanded=re.sub(r'\\input\{([^}]+)\}',lambda m:(PAPER/(m[1] if m[1].endswith('.tex') else m[1]+'.tex')).read_text(),text)
 labels=re.findall(r'\\label\{((?:tab|fig):[^}]+)\}',expanded)
 aux=(PAPER/'main.aux').read_text()
 numbers=dict(re.findall(r'\\newlabel\{((?:tab|fig):[^}]+)\}\{\{([^}]+)\}',aux))
 assert len(labels)==len(set(labels))==32
 rows=[]
 def add(label,inputs,producer,output,protocol=PROT,config=CFG,status='reconstructed command; historical producing argv not recorded',notes=''):
  assert label in labels
  rows.append(dict(label=label,kind='table' if label.startswith('tab') else 'figure',number=numbers.get(label,'not compiled'),
    inputs=inputs,producer_command=producer,output=output,protocol=protocol,config=config,command_provenance=status,
    tolerance='not recorded unless explicitly listed in REPRODUCE_v1.md',notes=notes))
 tex='docs/latex-sigkdd-v1.0/main.tex'
 latex='latexmk -pdf -interaction=nonstopmode main.tex (cwd docs/latex-sigkdd-v1.0)'
 for label,inputs,note in [
  ('tab:layers',['tokenmarket/gateway.py','tokenmarket/compliance.py','tokenmarket/portfolio.py','tokenmarket/sim.py','tokenmarket/feedback.py'],'Conceptual editorial table; no statistical data generator.'),
  ('tab:files',['tokenmarket/benchmark_export.py','docs/DATA_SCHEMA.md'],'Schema descriptions; legacy five-file layout.'),
  ('tab:samples',['docs/DATA_SCHEMA.md','exports/production/orders.jsonl','exports/production/sellers.jsonl','exports/production/buyers.jsonl','exports/production/audits.jsonl','exports/production/episodes.jsonl'],'Schematic/truncated examples; not a new production-number table.'),
  ('tab:labels',['tokenmarket/t4_export.py',PROT],'Whitelist rules, not classifier results.'),
  ('tab:repro',[PROT,'docs/v1.1/PROTOCOL_v1.2.md','release/v1.0/MANIFEST.json','requirements.txt','pyproject.toml','results/v1.0/main/run_meta.json',DEC+'decision_a_eval.json'],'Editorial path/version table; no standalone generator.'),
  ('tab:codemap',['tokenmarket/gateway.py','tokenmarket/matching.py','tokenmarket/portfolio.py','tokenmarket/baselines.py','tokenmarket/audit_v6.py','tokenmarket/strategic.py','tokenmarket/feedback.py','tokenmarket/logging_schema.py'],'Editorial source-to-layer mapping.'),
  ('tab:rq',[PROT,'docs/v1.1/PROTOCOL_v1.2.md',DEC+'decision_a_eval.json',MAIN+'inference.json','results/v1.0/t4_pilot_eval/t4_eval.json'],'Editorial task status table; no standalone generator.')]:
  add(label,inputs,'Manual LaTeX in main.tex; '+latex,tex,status='existing manual table; compile flags recorded in paper README',notes=note)
 add('fig:layers',['docs/latex-sigkdd-v1.0/figures/fig1_five_layers.svg'],
     'SVG source + frozen PNG; original raster-export command not recorded. Reconstructed: inkscape figures/fig1_five_layers.svg --export-type=png --export-filename=/tmp/fig1_five_layers.png',
     'docs/latex-sigkdd-v1.0/figures/fig1_five_layers.png',notes='Conceptual drawing; reconstructed export not executed or byte-equivalence claimed.')
 for label,filename in [('tab:t1','decision_a_main.tex'),('tab:decision-a-pilot','decision_a_deltas.tex'),('tab:decision-a-strongest','decision_a_deltas.tex'),('tab:decision-a-p4','decision_a_lower_penalties.tex'),('tab:decision-a-p16','decision_a_lower_penalties.tex')]:
  add(label,[DEC+'cells.csv',DEC+'contrasts.csv',DEC+'direction_consistency.csv',DEC+'decision_a_eval.json',DEC+'decision_a_eval.md','results/v1.1/v1.2_decision_a/run_meta.json','results/v1.1/v1.2_decision_a/manifest.json','results/v1.1/v1.2_decision_a/factorial/per_seed.csv'],D,
      'docs/latex-sigkdd-v1.0/tables/'+filename,'docs/v1.1/PROTOCOL_v1.2.md',CFG,status='renderer invocation documented; L2 scratch execution verified exact bytes')
 add('tab:wp1-cascade',['results/v1.1/wp1_eval/wp1_eval.json','results/v1.1/wp1_eval/contrasts.csv','results/v1.1/wp1_eval/wp1_eval.md'],D,
     'docs/latex-sigkdd-v1.0/tables/wp1_cascade.tex','docs/v1.1/PROTOCOL_v1.1.md',CFG,status='renderer documented; L2 exact bytes; separate WP1 diagnostic')
 add('tab:price-ratios',['results/v1.1/v1.2_price_representativeness/ratios.csv','results/v1.1/v1.2_price_representativeness/MAPPING_RULE.md','results/v1.1/v1.2_price_representativeness/compute_ratios.py','results/v1.1/v1.2_price_representativeness/FINDINGS.md','configs/v1.0/frozen/prices.yaml','configs/v1.0/frozen/scale.yaml'],
     'python scripts/pass16_price_ratio_tables.py (no flags; scratch mirror only)','docs/latex-sigkdd-v1.0/tables/price_ratios.tex',
     'MAPPING_RULE.md descriptive comparison; not an applied protocol price mapping',['configs/v1.0/frozen/prices.yaml','configs/v1.0/frozen/scale.yaml'],status='renderer documented; L2 exact bytes',notes='Snapshot raw SKU rows and exclusions retained; no price updates.')
 for label in ['tab:t2','tab:t1-v10','tab:j','tab:pistar','tab:qmode','tab:qmodeb']:
  add(label,[MAIN+'per_seed.csv',MAIN+'run_meta.json',MAIN+'inference.json',MAIN+'inference.md'],A+'; manual selection/formatting in main.tex; '+latex,tex,
      notes='No standalone automated LaTeX generator recorded for this table. Analyzer generates inference.json/md and diagnostic plots; paper table is frozen manual LaTeX.')
 add('tab:a2',['results/v1.0/a2_filter_off/A2_paired.json','results/v1.0/a2_filter_off/A2_paired.md','results/v1.0/a2_filter_off/per_seed.csv',MAIN+'per_seed.csv'],
     'Original standalone A2 readout producer/argv not recorded; manual LaTeX + '+latex,tex,
     status='producer gap explicitly recorded',notes='Stored bootstrap metadata exists; do not substitute v0.1-scale D3-only script. L2 verifies frozen bytes/checksums rather than inventing RNG call order.')
 add('tab:exp3',['results/v1.0/main_exp3/inference.json','results/v1.0/main_exp3/per_seed.csv','results/v1.0/main_exp3/run_meta.json'],
     'python scripts/v1/analyze_scale_v1.py --in results/v1.0/main_exp3 --out /tmp/pass17-exp3-analysis; manual LaTeX + '+latex,tex)
 for label,folder in [('tab:t4counts','t4_eval'),('tab:t4pilotcounts','t4_pilot_eval')]:
  add(label,[f'results/v1.0/{folder}/export/labels_train.csv',f'results/v1.0/{folder}/export/labels_test.csv',f'results/v1.0/{folder}/export/t4_manifest.json'],
      'Count nonempty fraud_future and per-type labels by split; manual LaTeX + '+latex,tex,
      notes='Counts use nonempty target labels; feature rows with no target service excluded. Export recipe T4-E in REPRODUCE_v1.md; no original count-table generator recorded.')
 add('tab:t4pilot',['results/v1.0/t4_pilot_eval/export/features_train.csv','results/v1.0/t4_pilot_eval/export/features_test.csv','results/v1.0/t4_pilot_eval/export/labels_train.csv','results/v1.0/t4_pilot_eval/export/labels_test.csv','results/v1.0/t4_pilot_eval/t4_eval.json'],
     'python scripts/run_t4_eval.py --export-dir results/v1.0/t4_pilot_eval/export --out /tmp/pass17-t4-pilot --n-boot 2000; manual LaTeX + '+latex,tex,
     status='reconstructed eval command; L2 parsed result fields exact; historical argv not recorded')
 add('tab:t2v01',['results/v1.0/T2_v01scale_20seed.json','results/v1.0/raw/T2_v01scale_20seed_episodes.jsonl'],
     'Historical scripts/v1/recompute_q_v1.py + scripts/v1/make_report_v1.py (no flags; scratch clone only); manual LaTeX + '+latex,tex,
     config=['configs/benchmark/production.yaml','configs/default.yaml'],notes='Historical v0.1 scale; two Q modes. Scripts hard-code results output; L3 only, never run on frozen checkout.')
 for label,stem in [('fig:t2','fig3_40seller_E_Q_vs_pi'),('fig:pareto','fig2_40seller_pareto_EQ'),('fig:etok','figC_40seller_Etok_vs_pi')]:
  add(label,[MAIN+'inference.json',MAIN+'per_seed.csv',MAIN+'run_meta.json'],F,'docs/latex-sigkdd-v1.0/figures/'+stem+'.pdf',status='renderer documented; L2 scratch run succeeds; no binary-PDF tolerance recorded')
 for label,stem in [('fig:paretov01','fig2_v01scale_pareto_EQ'),('fig:t2v01','fig3_v01scale_E_Q_vs_pi')]:
  add(label,['results/v1.0/T2_v01scale_20seed.json'],F,'docs/latex-sigkdd-v1.0/figures/'+stem+'.pdf',config=['configs/benchmark/production.yaml','configs/default.yaml'],status='renderer documented; L2 scratch run succeeds; no binary-PDF tolerance recorded')
 assert set(x['label'] for x in rows)==set(labels)
 rows.sort(key=lambda x:labels.index(x['label']))
 for row in rows:
  for p in row['inputs']:
   assert (ROOT/p).is_file(),p
 data=dict(documentation_date='2026-11-15',scope='all 26 tables and 6 figures; input dependencies remain repository paths, not staged copies',common_dependencies=['cache/llm_outputs.jsonl','data/long_tasks.jsonl','data/raw/gsm8k_test.jsonl','data/raw/math500_test.jsonl','requirements.txt','pyproject.toml','tokenmarket/','scripts/','docs/latex-sigkdd-v1.0/refs.bib'],items=rows)
 (OUT/'ARTIFACT_MAP.json').write_text(json.dumps(data,indent=2)+'\n')
 lines=['# Artifact map — documentation version 1 (2026-11-15)','',
 'All paper tables and figures are covered below. Detailed arrays, producing commands/flags and provenance are in [ARTIFACT_MAP.json](ARTIFACT_MAP.json). This is a map of the repository, not a claim that release/v1.0 is complete. Source paths are repository-relative. `SHA256SUMS` in this folder and release/v1.0 hash the dependency inventory without copying data.','',
 'Commands are indexed in [REPRODUCE_v1.md](REPRODUCE_v1.md). Each manual table is reproduced by compiling the frozen LaTeX; no missing original converter or argv is invented. Scientific tolerances are not recorded except where the guide cites an existing comparator. Rerendering figures can change PDF metadata/fonts even with identical source values.','',
 '| Paper item / label | Frozen input(s) | Producer + flags / provenance | Output | Protocol / configuration |','|---|---|---|---|---|']
 for r in rows:
  ins='<br>'.join('`'+s+'`' for s in r['inputs'])
  cfg='<br>'.join('`'+s+'`' for s in r['config'])
  lines.append(f"| {r['kind'].title()} {r['number']} `{r['label']}` | {ins} | {r['producer_command']}<br>{r['command_provenance']}<br>{r['notes']} | `{r['output']}` | {r['protocol']}<br>{cfg} |")
 lines += ['', '## Shared lineage and package boundary','',
 'Simulation lineage: scale.yaml → production.yaml → default.yaml; task pool and cache are reused. Official grid argv are recorded in each run_meta.json. Main/peer/EXP3/filter-off have distinct directories. Decision A uses frozen PROTOCOL_v1.2 and its own completed grid, and WP1 cascade uses PROTOCOL_v1.1. The first-batch v0.1-scale readout is separate. Table 10 is descriptive only.','',
 'Joinable logs retained in `results/v1.0/t4_runs/logs/`, `results/v1.0/t4_pilot/logs/` and `logs/` are different representations from aggregate per_seed boards. Decision A completed_runs.jsonl is one row per cell/learner/seed, not per purchase. The main board run_meta has no log-dir argv; no missing per-purchase archive is invented for that grid. See SCHEMA_v1.md for keys and T4 manifests for split/window lineage.', '',
 'The manifest includes code, inherited/frozen configs, protocols, source task/cache assets, the referenced official result directories, available T4 logs/exports, paper inputs, release notices and these documentation files. It excludes itself, temporary scratch outputs, .git, bytecode and LaTeX auxiliary build files; main.pdf is included after the final build. Existing staging MANIFESTs retain their original scope.']
 (OUT/'ARTIFACT_MAP.md').write_text('\n'.join(lines)+'\n')
 print('Mapped',len(rows),'paper tables/figures')
if __name__=='__main__':main()
