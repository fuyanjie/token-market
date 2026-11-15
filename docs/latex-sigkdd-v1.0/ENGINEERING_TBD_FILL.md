# Engineering TBD fill-in values for KDD 2027 D&B

Handoff from Coding to Writing. This file only records verified values from the
`v1.1` checkout at `fc67752`. It does **not** edit `main.tex` or the table
inputs. Writing owns any manuscript change.

- Date: 2026-11-15, Asia/Shanghai
- Branch: `v1.1` at `fc67752` (Pass 14), after `git fetch` and fast-forward to `origin/v1.1`
- Scope grepped: `docs/latex-sigkdd-v1.0/KDD2027_DB_CHECK.md` and paper TeX under `docs/latex-sigkdd-v1.0/` (`main.tex`, `tables/*.tex`, `refs.bib`)
- Method: `rg TBD`; `\TBD{...}` parsed from `main.tex`; hashes with `sha256sum` on the actual files (sidecars cross-checked); commands taken from official `run_meta.json` `argv` and confirmed against each script's `--help` (official grids were not rerun). `scripts/pass12_decision_a_tables.py` and `scripts/v1.1/analyze_wp1.py` have no `--help` parser and execute on invocation; they were not used as a source of new results here. `pytest --collect-only -q` was used as a dry inventory (tests were not executed).
- Historical mentions of TBD in `CHANGES_v1.0.md` / briefs are not current placeholders.

## Inventory

| Count | What |
|---:|---|
| 20 | Current `\TBD{...}` invocations in `main.tex` (Pass 14). Macro definition at `main.tex:59` is not an invocation. |
| 0 | TBD in `tables/*.tex` or `refs.bib` |
| 3 of 20 | Owner decisions (傅老师). Left untouched. |
| 17 of 20 | Engineering / result-status items Coding can document from the repo |
| extra | Check-file process items with no paper macro: submission cycle (C3), author line (C13), empty ACM DOI/ISBN/copyright/CCS |

Venue date/location in `\acmConference` are already filled (August 1--5, 2027; San Jose, California). They are not TBDs in this checkout.

## Items left for 傅老师 (do not fill)

1. `main.tex:221` — `傅老师: public repository or archival URL (this checkout's GitHub remote is not publicly accessible)`
2. `main.tex:297` — `傅老师: maintainer, public host, optional artifact-badge pledge`
3. `main.tex:302` — `傅老师: whether additional representativeness evidence will be collected`
4. Check C3 (`KDD2027_DB_CHECK.md`) — submission round: already-submitted vs internal readiness vs the later 2027 cycle; form-side facts. No paper `\TBD` macro.
5. Check C13 — author line: leave unchanged pending 傅老师 (currently Yanjie Fu; single-blind allows a name).
6. ACM DOI, ISBN, copyright (`none`), and CCS — rights-form metadata; already blank/commented. Not engineering facts.

A public T4 submission service, if any, also depends on item 1 and should not be invented.

---

## Coding items (verified values)

### A. Price calibration (four related placeholders plus the sample price)

**Placeholders**

| File:line | Placeholder text |
|---|---|
| `main.tex:179` | `Coding: price sources, snapshot date, and mapping` |
| `main.tex:302` | `Coding: price sources and mapping` |
| `main.tex:429` | `Coding: price sources and mapping` |
| `main.tex:446` | `Coding: price sources, access date, calibration` |
| `main.tex:250` | `Coding: calibrated price` |

**Verified value.** A public-list *snapshot table* exists, but it was **not applied** to the reported simulator prices. The paper's current wording (prices are simulated / uncalibrated; present tables use the simulator's existing ratios) is consistent with the frozen protocol. There is **no calibrated `list_price`** to drop into the sample row.

- Source table (identical in both copies; sha256 `c26293cc3d890c6220491d02c06988372c79d0a5856899d2f165004bd8f9840f`): `configs/v1.0/prices.yaml` and `configs/v1.0/frozen/prices.yaml`.
- Access date recorded in the file: `2026-11-10` (`access_date`, and each provider's `accessed`).
- Named sources actually filled (URLs and dates as written in the YAML, lines 16--44):
  - OpenAI: `https://developers.openai.com/api/docs/pricing`, accessed 2026-11-10
  - Anthropic: `https://claude.com/pricing`, accessed 2026-11-10
  - Google: `https://aistudio.google.com/docs/pricing`, accessed 2026-11-10
- Not filled (recorded as TODO, not invented): DeepSeek (`https://api-docs.deepseek.com/quick_start/pricing`, "price table not retrievable on 2026-11-10"); Alibaba Model Studio (`https://www.alibabacloud.com/help/en/model-studio/models`, "prices not shown…"); `gemini-3.1-flash-lite` prices are null, "verify on source page".
- Mapping to the simulator: **not recorded as applied**. `prices.yaml` lines 6--8 say the table is for "anchor ratios" and that `price_per_1k` values in `configs/v1.0/scale.yaml` "are synthetic market units and are NOT rescaled automatically". The loader `tokenmarket/prices.py` is used in unit tests (`tests/test_v1_infra.py`), not in the official 40-seller or Decision A runners.
- Protocol lock: `docs/PROTOCOL_v1.0.md` 开跑前裁定 4 (line 69): "价格校准保持 TBD，正文不得写已校准。§7 的公开价目表校准作为后续稳健性：须先写死映射规则再跑…不得与主表混为一次结果。"
- Frozen roster prices (`configs/v1.0/frozen/scale.yaml` lines 37--45), synthetic ranges, not public-list values: honest 1.5B `[0.17, 0.24]`, honest 0.5B `[0.08, 0.12]`, `sim-fast-mock` `[0.05, 0.08]`, strategic `[0.15, 0.21]`. File sha256 `780e9b961d89bad6fd520c9cbfd5710055ff2d5d3e0ff3bcfbd745709eb0da6c` (already printed in the paper).
- Sample `list_price` in legacy `docs/DATA_SCHEMA.md` is `0.2` for `seller_cn`. That is the old 3-seller schematic sample, **not** a calibrated public-list price. Do not present it as a calibration.

**Suggested manuscript action (Writing).** Keep the "not calibrated / synthetic ratios" wording. If a citation of the unused snapshot is wanted, point to `configs/v1.0/frozen/prices.yaml`, access date 2026-11-10, and the three filled provider URLs, and state explicitly that the mapping was not applied and is not a reported result. Leave the sample price as a synthetic example or omit a numeric price; do not invent a calibrated value.

---

### B. `main.tex:254` — `Coding: v1.0 hash; final field names`

**Verified value.** There is no single 40-seller `episodes.jsonl` board and no single production `config_hash`. Official 40-seller output is `results/v1.0/main/per_seed.csv` (3420 rows), not `episodes.jsonl`.

`per_seed.csv` columns (exact header):

`method, label, policy, pi, seed, E, E_tok, fraud_share, fraud_share_swap, fraud_share_theft, fraud_share_downgrade, Q, Q_swap, Q_theft, Q_downgrade, tail_trade, tail_trade_sellers, tail_sales, n_strategic, Q_present_rounds, delisted_rounds_tail, q_delisted_mean, J, quality, cost, cost_per_task, audit_cost, n_audits, audit_rate_realised, violation_rate, fill_rate, n_served, seller_learner, audit_rule, compliance_filter, roster_seed, config_hash`

Row-level `config_hash` is a **16-character prefix** of `sha256(json.dumps(per-run cfg, sort_keys=True, default=str))`, implemented at `scripts/run_v1.py:66-67`. It varies by method × π (and related overrides); the 40-seller egreedy main table alone contains many distinct prefixes (example from seed 0, PILOT, π=0: `8480f34cea55114e`). It is not a file hash of `scale.yaml`.

The config *file* hash to cite is already in the paper and in `results/v1.0/main/inference.json` field `scale_yaml_sha256`:

`780e9b961d89bad6fd520c9cbfd5710055ff2d5d3e0ff3bcfbd745709eb0da6c` = `sha256sum configs/v1.0/frozen/scale.yaml` (identical to `configs/v1.0/scale.yaml` in this checkout).

Legacy five-file `episodes.jsonl` (e.g. `exports/production/episodes.jsonl`, older 3-seller boards) still uses `tokenmarket/benchmark_export.py` `EPISODE_FIELDS` (lines 50--53):

`run_id, seed, a, pi, L, reputation_rounds, active_attack_rate, learned_q_swap, learned_q_theft, fraud_share, J, n_audits, config_hash`

That legacy schema still includes `active_attack_rate` and has no `Q` / `Q_downgrade` / suspended-period fields. `docs/DATA_SCHEMA.md` §5 matches this legacy list and is already labelled legacy in the paper. Do not treat those sample hashes (`abc123deadbeef00` in the schema doc) as real.

---

### C. `main.tex:460` — `Coding: v1.0 episodes field names`

**Verified value.** Same as §B. For the 40-seller official board, use the `per_seed.csv` header above. For the older five-file export, use `EPISODE_FIELDS`. The names listed in the appendix sentence (`run_id, seed, a, pi, L, reputation_rounds, fraud_share, Q, per-mode q, suspended rounds, J, n_audits, config_hash`) are a *desired* v1.0 board description; they do not all appear together in one checked-in `episodes.jsonl`. Q-mode and delist fields live on `per_seed.csv` (`Q`, `Q_swap`, `Q_theft`, `Q_downgrade`, `delisted_rounds_tail`, `q_delisted_mean`). The audit rate `a` is encoded in `method` / `audit_rule` on that CSV, not as a column named `a`.

---

### D. `main.tex:268` — `Coding: T4 submission channel and external score-file interface`

**Verified value.**

- Local evaluator (exists): `scripts/run_t4_eval.py`. `--help` accepts `--logs` plus `--config`, or `--export-dir`, and requires `--out`. Optional `--n-boot`, `--drop-latency`, `--train-seeds`.
- Local score-file interface (exists): an export directory with `features_train.csv`, `features_test.csv`, `labels_train.csv`, `labels_test.csv`, and `t4_manifest.json`. Checked paths: `results/v1.0/t4_eval/export/` and `results/v1.0/t4_pilot_eval/export/`.
- Official recorded run + eval (do not rerun):
  - Generate logs: `scripts/run_v1.py --config configs/v1.0/scale.yaml --seeds 0-19 --pi-grid 1.0 --methods fixed_audit_a0.10 --resample-roster --out results/v1.0/t4_runs --log-dir results/v1.0/t4_runs/logs` (`results/v1.0/t4_runs/run_meta.json` `argv`).
  - PILOT supplement: same with `--methods pilot --out results/v1.0/t4_pilot --log-dir results/v1.0/t4_pilot/logs`.
  - Eval JSON records `export_dir` and `n_boot` only (no argv): official D3 `results/v1.0/t4_eval/t4_eval.json` has `n_boot=2000`; the per-run recompute `results/v1.0/t4_eval_per_run/t4_eval.json` has `n_boot=10000`; PILOT `results/v1.0/t4_pilot_eval/t4_eval.json` has `n_boot=2000`.
- Public submission channel / external scoring service: **not recorded**. `scripts/run_leaderboard.py` is an older T1--T3 board helper, not a T4 submission service.

---

### E. `main.tex:297` and `main.tex:513` — pytest count / log path

**Verified value.** There is **no** attributable official "v1.0 full-suite tests passed" log. Do not print a single count as if it were the frozen official pass record.

Existing logs in the checkout (counts only; these are historical snapshots, not a claim that the current tree still matches them):

| Path | Result recorded in the file | File date (Asia/Shanghai, box mtime) |
|---|---|---|
| `results/benchmark/pytest_after_draft.txt` | `76 passed in 1.84s` | 2026-11-10 09:13 |
| `results/v1.1/wp0_repro/pytest_v1_infra.log` | `47 passed in 5.91s` (infra subset) | 2026-11-10 18:59 |
| `results/v1.1/wp1_impl_validation/pytest_initial.log` | `133 passed in 10.75s` | 2026-11-11 02:21 |
| `results/v1.1/wp1_impl_validation/pytest_wp1.log` | `37 passed in 3.64s` | 2026-11-11 02:22 |
| `results/v1.1/wp1_impl_validation/pytest_{full,delivery,final}.log` | `205 passed` (16.44--18.07s) | 2026-11-11 02:22--02:26 |

Current tree inventory only (not a pass log): `python3 -m pytest --collect-only -q` at this checkout collected **261** tests in 13 files under `tests/`. Tests were not executed for this handoff. Top-level `README.md` still quotes stale counts (63 / 76) and should not be treated as current.

Pinned test runner: `pytest==9.2.0` in `requirements.txt` and `pyproject.toml`.

---

### F. `main.tex:476` and `main.tex:511` — final v1.0 / Decision A command lines, and "production config_hash"

**`config_hash` (line 511).** See §B. Print the frozen `scale.yaml` sha256 (already in the paper). Do not invent one production row-hash. If a short explanation is needed: official 40-seller `config_hash` values are 16-character SHA-256 prefixes of each per-run config JSON.

**Commands.** Flags below were checked with `--help` except where noted. Official grids were **not** rerun. `argv` is copied from the corresponding `run_meta.json` when one exists. Use `python3` or the venv `/workspace/tmvenv/bin/python` (the latter is what the help text and older docs name).

40-seller official runs (`scripts/run_v1.py`; defaults: `--config` may be omitted only if the script default is accepted; official argv always passed `--config configs/v1.0/scale.yaml`):

```text
# egreedy main table (results/v1.0/main/run_meta.json)
python3 scripts/run_v1.py --config configs/v1.0/scale.yaml --seeds 0-19 --jobs 8 --out results/v1.0/main

# fictitious play (results/v1.0/main_fp/run_meta.json)
python3 scripts/run_v1.py --config configs/v1.0/scale.yaml --seeds 0-19 --jobs 8 --learner fictitious_play --out results/v1.0/main_fp

# EXP3 (results/v1.0/main_exp3/run_meta.json)
python3 scripts/run_v1.py --config configs/v1.0/scale.yaml --seeds 0-19 --jobs 8 --learner exp3 --out results/v1.0/main_exp3

# A2 filter-off (results/v1.0/a2_filter_off/run_meta.json)
python3 scripts/run_v1.py --config configs/v1.0/scale.yaml --seeds 0-19 --jobs 8 --pi-grid 1.0 --no-compliance-filter --out results/v1.0/a2_filter_off
```

`--help` also documents `--methods`, `--resample-roster`, `--log-dir`, `--backend-override`, `--cache-file`, `--n-tasks`, `--n-rounds`. Official 40-seller mains did not pass those (they used the config `v1:` block). Wall-clock in `run_meta` / `run.log`: main 107.17s, main_fp 105.55s, main_exp3 102.16s, a2_filter_off 6.21s, all `--jobs 8` (cache-backed; not a clean-room measurement).

Inference for the 40-seller egreedy table is already on disk (`results/v1.0/main/inference.json`). The analyzer is `scripts/v1/analyze_scale_v1.py --in INDIR --out OUTDIR [--peer PEER] [--title TITLE]`. No argv for the official inference run is stored in that JSON (only `run_meta.argv` for the simulator). Do not claim a clean-environment rerun.

T4: see §D.

Decision A / v1.2 (PROTOCOL_v1.2, sha256 `daddac6c0dddb22b08701caff5715e77215ae13a588512af176ff4933430b102`):

```text
# Official Decision A grid (2880 runs, 1000 rounds). results/v1.1/v1.2_decision_a/run_meta.json
# git_head of the *run* is 5e848d9 (protocol freeze). The readout was committed later as f759cd6.
python3 scripts/v1.1/run_wp1.py --mode decision_a --protocol docs/v1.1/PROTOCOL_v1.2.md --protocol-sha256 daddac6c0dddb22b08701caff5715e77215ae13a588512af176ff4933430b102 --n-rounds 1000 --out results/v1.1/v1.2_decision_a --jobs 8
# Recorded elapsed_s: 2227.75 (completion.json). Do not rerun.

# Official analysis (required flags from --help; argv not stored in decision_a_eval.json;
# paths and protocol hash taken from the written readout):
python3 scripts/v1.1/analyze_decision_a.py --run results/v1.1/v1.2_decision_a --out results/v1.1/v1.2_decision_a_eval --protocol docs/v1.1/PROTOCOL_v1.2.md --protocol-sha256 daddac6c0dddb22b08701caff5715e77215ae13a588512af176ff4933430b102

# Render frozen tables only (no experiment). The script has no --help and writes
# docs/latex-sigkdd-v1.0/tables/ when invoked:
python3 scripts/pass12_decision_a_tables.py
```

Related official grids (for the reproduction appendix; not Decision A itself):

```text
# v1.1 WP1 48-round egreedy diagnostic (results/v1.1/wp1/run_meta.json)
python3 scripts/v1.1/run_wp1.py --out results/v1.1/wp1 --jobs 8 --log-transactions
# protocol hash in that run_meta: e9c84494…209c179 (PROTOCOL_v1.1)

# v1.2 WP1 rerun (results/v1.1/v1.2_wp1/run_meta.json)
python3 scripts/v1.1/run_wp1.py --protocol docs/v1.1/PROTOCOL_v1.2.md --protocol-sha256 daddac6c0dddb22b08701caff5715e77215ae13a588512af176ff4933430b102 --out results/v1.1/v1.2_wp1 --jobs 8

# WP2 official 48/200/500 (v1.2): results/v1.1/v1.2_wp2/run_meta.json
python3 scripts/v1.1/run_wp2.py --official --protocol docs/v1.1/PROTOCOL_v1.2.md --protocol-sha256 daddac6c0dddb22b08701caff5715e77215ae13a588512af176ff4933430b102 --out results/v1.1/v1.2_wp2 --jobs 8

# WP2 official 1000-round tier: results/v1.1/v1.2_wp2_r1000/run_meta.json
python3 scripts/v1.1/run_wp2.py --official-r1000 --protocol docs/v1.1/PROTOCOL_v1.2.md --protocol-sha256 daddac6c0dddb22b08701caff5715e77215ae13a588512af176ff4933430b102 --out results/v1.1/v1.2_wp2_r1000 --jobs 8

# Combined WP2 analysis (--help). Official files are already at results/v1.1/v1.2_wp2_eval_r1000/
python3 scripts/v1.1/analyze_wp2.py --include-r1000
```

Older recipes already distinguished in Appendix B (`export_benchmark_layers.py --full`, `run_benchmark_tasks.py --full`, `scripts/reproduce_pi_dense.sh --full`) are **not** the 40-seller or Decision A path. Confirmed: `run_benchmark_tasks.py --tasks` only accepts `T1,T2,T3`.

---

### G. `main.tex:598` — `Coding: T1-secondary cost and accuracy per policy, mean [95\% CI]`

**Verified value; official CIs missing.** `results/v1.0/main/inference.json` `curves` entries have `pi, method, label, E, E_tok, Q, Q_swap, Q_theft, Q_downgrade, J, tail_trade_rate, identifiable` only. No `cost`, `quality`, or `accuracy` intervals. That matches the current manuscript note.

Plain *means* (no official bootstrap CI) exist in `results/v1.0/main/summary.md` and per-seed values in `results/v1.0/main/per_seed.csv` columns `quality`, `cost`, `cost_per_task`. Do **not** invent 95% CIs from those files in this pass.

Do not substitute Decision A cell-level `accuracy` / `cost_per_task` CIs from `results/v1.1/v1.2_decision_a_eval/decision_a_eval.md` into the v1.0 T1-secondary table: that is a different experiment (1000-round factorial).

**Suggested action.** Keep "defined but not reported in this manuscript."

---

### H. `main.tex:737` and `main.tex:739` — T3-delist / T3-adaptive tables

**Verified value; v1.0 official tables missing.** No `results/v1.0/` directory contains a 40-seller T3-delist (`reputation_rounds ∈ {0,5,20}`) or T3-adaptive official readout. Official 40-seller mains use default `reputation_rounds=0` (paper already states this).

Older, **out-of-scope** artifacts exist and must not be copied into the v1.0 T3 tables as official numbers:

- `results/v6_delist.md` / `results/v6_adaptive_audit.md`: v6, 3-seller-scale, seeds 0--2, swap/theft only.
- `results/benchmark/production/T3_episodes.jsonl`: 6 rows, legacy episode fields including `active_attack_rate`, hashes `7b60ac28061d2907` and `02e444f6c99cb947`. This is the older production T1--T3 board, not the 40-seller protocol.

**Suggested action.** Keep "defined but not reported in this manuscript."

---

### I. `main.tex:742` and `main.tex:762` — `Coding: T4-5b`

**Verified value; not implemented, no results.** Protocol `docs/PROTOCOL_v1.0.md` §5b (lines 40--42) schedules a simulator change (hidden reasoning tokens vs visible answer) *after* the main table, then a second T4 split. `tokenmarket/t4_export.py` lines 72--76 still say answer length "must not be exported until protocol §5b lands." No post-5b export or eval directory exists under `results/v1.0/`.

**Suggested action.** Keep as future work, defined but not reported.

---

## Official hashes (computed 2026-11-15 with `sha256sum`; sidecars agree where present)

Already printed in the paper, recomputed and confirmed:

| File | sha256 |
|---|---|
| `results/v1.1/v1.2_decision_a_eval/decision_a_eval.md` | `5d3f52292883a73dec8a892e7e64c250eeb7eb62c09b1bb36508e7e3c034dad9` |
| `docs/v1.1/PROTOCOL_v1.2.md` | `daddac6c0dddb22b08701caff5715e77215ae13a588512af176ff4933430b102` |
| `docs/v1.1/PROTOCOL_v1.1.md` | `e9c84494a7031d7023d4861c02a5786a59fbc74541007978a13b9882f209c179` |
| `configs/v1.0/frozen/scale.yaml` | `780e9b961d89bad6fd520c9cbfd5710055ff2d5d3e0ff3bcfbd745709eb0da6c` |

The string ending `…ed83db` is **not** the readout hash. It is the sha256 of the *sidecar file* `decision_a_eval.json.sha256` itself: `bc4b39c9ce566ae171d608501dfc6aa3b6e4e143bfe3c5dca91a873ec6ed83db`. The JSON's content hash is the first column below.

Additional official Decision A eval files (content hashes; each has a matching `*.sha256` sidecar):

| File | sha256 |
|---|---|
| `…/v1.2_decision_a_eval/decision_a_eval.json` | `5c5852e4d5eb70ff83d63ef8a76b63f20b00c375608abe65a6f35c1a7b82d710` |
| `…/v1.2_decision_a_eval/cells.csv` | `51afb33a323efda32ff2e1c94dfa75848886059822056387ceb3ba4355716b5d` |
| `…/v1.2_decision_a_eval/contrasts.csv` | `5eb9a8914621d594c37b61af99ca5d5cab03b5b97f564aae55c7c972129f25a2` |
| `…/v1.2_decision_a_eval/direction_consistency.csv` | `f623eb0c15a730796f3cf8d679f70f8ea0505429b262278d7157daf1de423bc4` |

WP2 1000-round official eval (`results/v1.1/v1.2_wp2_eval_r1000/`; sidecars agree):

| File | sha256 |
|---|---|
| `wp2_eval.json` | `748bc9778d2773ee3ae4312cc359561a80ce9f60463158c1294b34c6dca952e2` |
| `wp2_eval.md` | `a16d0063bb76ada7b39983c78198a1df0d735e971e71810435f302b364ea71fd` |

WP1 official diagnostic (`results/v1.1/wp1_eval/`; no sidecars in tree):

| File | sha256 |
|---|---|
| `wp1_eval.md` | `95f84e6ef716140cfba470c68ab7bd0f9bd1431e7ff73bcc8a4c063d1b7847fc` |
| `wp1_eval.json` | `52294e680e697a9e21340c134546226a14f422c4c9c0b9cff9e2e03dcb27873b` |
| `contrasts.csv` | `14c4e352d8813c85ca69b2cbc8c11d3e1a7f0ea36fd8413a60258aad08ccef8c` |

`docs/PROTOCOL_v1.0.md`: `08077920b302a52b5190f491f536ec92d891c32ff9c844722ce4ecd76c687ee2`.

40-seller official inference (egreedy), optional if the appendix wants them:

| File | sha256 |
|---|---|
| `results/v1.0/main/inference.json` | `70fc9b2ac83825828567b0af16a64a7fb4be49f4091e5859002582fa2752a0dd` |
| `results/v1.0/main/inference.md` | `17c2cbad27b3abaf607dab4152f16d6fccbdf44f27fb507ae8ba303a7918c506` |
| `results/v1.0/main/per_seed.csv` | `d86084ef11c7775f90cae3d3e1d98921c6eaa4b680ef1daf8f666c2c149c322b` |
| `results/v1.0/main/run_meta.json` | `1d24a41df8e37268810925121eccb18e379640f32748ae29590842a2074eb1f0` |

---

## Environment and versions

From `requirements.txt` / `pyproject.toml` (not from official Decision A `run_meta`, which stores no Python/package versions):

- `requires-python`: `>=3.13`
- v0.1 environment documented in `requirements.txt` lines 3--6: **Python 3.13.5** (CPython, GCC 14.2.0), venv `/workspace/tmvenv`. This is recorded for the v0.1 boards; v1.0 / Decision A run metadata do **not** separately record the interpreter.
- Core pins: `PyYAML==6.0.3`, `numpy==2.5.4`, `matplotlib==3.11.2`, `pytest==9.2.0`
- Optional local-HF pins (same files): `torch==2.15.0+cpu` (install incantation in `requirements.txt`), `transformers==5.22.1`, `accelerate==1.15.0`, `huggingface_hub==2.4.0`
- Package version in `pyproject.toml`: `tokenmarket` `0.2.0`

Runtime for official grids is in the command section above. No clean-room runtime is claimed.

---

## Evidence-missing summary (Coding items that cannot be filled with a number or table)

- Calibrated `list_price` / applied mapping rule: snapshot exists, mapping not applied (protocol forbids claiming calibration).
- Single production `config_hash` and a unified v1.0 `episodes.jsonl` field list: official board is `per_seed.csv` with per-run 16-character hashes.
- Public T4 submission channel: not recorded.
- One official v1.0 full-suite pytest pass log: not recorded (only subset/historical logs and a current collect-only count of 261).
- T1-secondary cost/accuracy **95% CIs** in the official 40-seller inference file: absent (means exist in `summary.md` / `per_seed.csv`).
- v1.0 official T3-delist and T3-adaptive tables: absent.
- T4-5b implementation and results: absent.

Python/package versions for the Decision A 1000-round grid itself are also not recorded in that run's metadata; only the documented requirements/v0.1 environment are available.
