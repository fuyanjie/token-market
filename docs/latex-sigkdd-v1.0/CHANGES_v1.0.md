# CHANGES v1.0 — SIGKDD LaTeX text edits (no new numbers)

Date: 2026-11-10 (Asia/Shanghai). Working copy of `docs/latex-sigkdd/` (that folder is unchanged and stays the synced v0.1-edited version). Not uploaded to Overleaf.

Sources: `docs/PROTOCOL_v1.0.md` (§0–§8 incl. §5, §5b) and the group decisions of 2026-11-10 (Review, Idea, Coding).

All 30 `TODO(pending unfreeze)` markers are resolved; none remain in `main.tex`. These were 15 primary-metric, 7 π*, 4 "D3 insensitive", 3 "D3 as method", and 1 §4.2 features marker.

Every v1.0 result is a red `\TBD{source: …}` placeholder. v0.1 numbers that v1.0 supersedes were deleted, not kept as claims.

Build: TinyTeX pdfLaTeX + BibTeX, 0 errors, 0 overfull boxes. The PDF has 10 pages, and the main body (§1–§8 + Ethics, with its floats) ends on page 6.

## Changes by section

| Section | Change |
|---|---|
| Preamble | Added `\TBD{}` (red), `\Emet`, `\Qmet`; header comment marks this as the v1.0 text-edit copy. |
| Abstract | Primary metric is now two-dimensional, E = `fraud_share` and Q = learned attack probability over listed rounds, shown as a Pareto plot with no winner; J, cost and quality go to the appendix. It adds T4, the three attack types, the new baselines, the ≥20 seeds / paired bootstrap / Holm statistics, and the leakage-checked feature view. The π* (0.10,0.12) sentence and "fixed-rate audits keep q* near 0.08" are deleted. The one-sentence result headline is TBD. |
| §1 Intro | Selective downgrade is added. RQ (iv) adds T4 seller risk. Contributions 2–4 are rewritten: release pack with MIT/CC BY 4.0, T1–T4 under the pre-fixed protocol, and the full baseline list. D3 is now the "fixed-rate audit reference baseline, not our method". |
| §2 Related | PILOT/StageRoute paragraph: "simplified reimplementations, MIP skipped" becomes **faithful** reimplementations with stage MIP and unit tests, plus a reproduction-gap TBD. Sparse-label behavior is framed as a property of the setting. Positioning now covers T1–T4 and uses Q. |
| §3.1 Layers table | Routing lists the new policies; oversight covers random, fixed-rate and risk-adaptive audit. |
| §3.2 Primitives | Sellers: ≥40 (≥30 honest, ≥3 strategic), roster TBD. Prices are calibrated to ≥3 public API price lists (sources TBD). There are three attack types: swap, theft and selective downgrade. "Default fixed rate a=0.1" moved to the baselines. |
| §3.4 (was "Joint objective (secondary)") | Became **Evaluation metrics**, with these parts: E as a token share; Q only over listed rounds, with suspension rounds and suspended-period q reported separately; per-mode q with Q as their simple average (pass 2: no token weighting); Pareto reading with no winner; the Q-as-primary gate (EXP3 or fictitious play, Kendall τ≥0.6 and same front, else Q demoted, outcome TBD); J, cost and quality moved to Appendix C. `active_attack_rate` is dropped. |
| §4.1 Files / samples | `episodes` row now lists E, Q, per-mode q and suspended rounds. The sample table drops v0.1 numbers (0.100/0.042/0.771) and the v0.1 config hash; the v1.0 hash, price and field names are TBD. |
| §4.2 Feature/Label | Rewritten: the blacklist is stripped from the public view and moved to held-out label files, with an export-time leakage check. The new table holds the **whitelist (7)**, the **blacklist** (now with `actual_model`, `confidence`, `learned_q_*`, `delist_rounds`, `slash_amount`, `audits.*`, `tokens_actual` and its difference, and attack fields) and the **excluded-for-leak** items (answer length, quality score, confidence, with reasons). A paragraph on the 5b simulator change was added. The old "safe features" list that included tokens_actual, hit/miss and slash is deleted. |
| §4.3 Licenses (new) | Code MIT; export, boards and derived cache fields CC BY 4.0; Qwen2.5 Apache-2.0 attributed; third cached model TBD; GSM8K/MATH-500 MIT notices in `release/v1.0/LICENSES/`; v0.1 not relicensed. |
| §4.4 Scripts | T1–T4; the v0.1 test count (76) is replaced by TBD. |
| §4.5 Cache | ≥3 cached models (third TBD); prices are calibrated rather than purely synthetic. |
| §5 Protocol | New preamble saying the protocol was fixed before running. Added: regression gate (§0), scale/statistics, and the baselines list with D3 renamed. T1 is now a Pareto placement with no ranking. T2's headline is now the bandit E/Q degradation vs π on the new grid {0,0.02,…,0.30,0.5,1.0}; "D3 insensitive to π" is stated as by construction, not a finding; π* moves to the appendix with the pre-registered rule. T3 covers adaptive audit plus delist with Q over listed rounds. **T4 is new**: task, AUROC/AP/P@10, whitelist, run split 0–13/14–19, features from rounds 1–32 and labels from 33–48, LR/GBDT/rule, without-latency ablation, pre-/post-5b versions. **A2 filter-off control is new.** The "Reading rule: rank by attack/fraud" line is removed. |
| §6.1 T1 | The table is rebuilt: 9 policies × [E, Q, q_swap/q_theft/q_downgrade, suspended rounds], all TBD, D3 not bolded. The new Fig. 2 (Pareto placeholder) replaces the v0.1 Reading sentence and the "Production export" v0.1 numbers. |
| §6.2 T2 | The v0.1 J-sweep table and the old Fig. 2 (pi* crossover, D3 at 0.08) are removed from the paper, though the files stay in `figures/`. The new Fig. 3 is a placeholder for the degradation curves. The "Crossover" and "Production T2" paragraphs are deleted, and the rule outcome is TBD. |
| §6.3 T4 (new) | Table: {pre-5b, pre-5b −lat, post-5b, post-5b −lat} × {LR, GBDT, Rule} × {AUROC, AP, P@10}, plus a reading TBD. |
| §6.4 A2 (new) | Violation rate with the filter on and off, plus the difference (TBD). |
| §6 v0.1 appendix tables | The delist and adaptive tables and escrow flows (v0.1 numbers) are removed and moved to Appendix C as TBD. |
| §7 Limitations | The "Primary metrics = active_attack_rate+fraud_share" item and the "pipeline-test vs v0.1 board" item are removed. Added: Q depends on the learning rule, and T4 realism before 5b / latency. Feature/Label now points to the v1.0 stripping. Jurisdictions now mention calibrated prices. |
| §8 Conclusion | Rewritten for two-dimensional, Pareto, no-winner evaluation with T2 degradation and T4; no π* claim. |
| Ethics | Prices calibrated to public lists; everything else is unchanged. |
| App. A Schema | v1.0 episodes row (field names TBD); `active_attack_rate` removed. |
| App. B Repro (§6.5) | All paths moved to `release/v1.0/`. pi_dense now points to `release/v1.0/results/pi_dense/`, which fixes the wrong old claim that it was under `release/v0.1/`. Added the protocol path, cache path and per-seed path. Hash, test count, leakage-check path and v1.0 command lines are TBD. The v0.1 "source artifact paths" table is removed; the code map is kept. |
| App. C Secondary (new) | J/cost/quality TBD; ΔJ table at π∈{0.08,0.10,0.12,0.14} with a per-seed crossover column; histogram and rule outcome TBD; delist and adaptive TBD. |
| App. D RQ coverage | Moved to v1.0; T4 row added; A2 row notes the filter-off control; metrics use E and Q. |

## TBD placeholders (113 total) → which result fills them

| Source tag | Count | Filled by |
|---|---|---|
| `T1` | 38 | Experiment: main table at π=1 (9 policies × 4 cells = 36) + Pareto plot + reading |
| `T1-secondary` | 1 | Experiment: J / cost / accuracy table |
| `T1/T2` | 1 | Abstract headline after the main table and T2 |
| `Q-gate` | 3 | Experiment: alternate learning rule (EXP3/FP), Kendall τ, front check, primary/side decision |
| `T2` | 3 | Experiment: degradation curves, reading, rule outcome |
| `T2-pistar` | 10 | Experiment: ΔJ CIs at 4 π values (8 cells) + per-seed histogram + rule outcome |
| `T3-delist` | 1 | Experiment: delist sweep |
| `T3-adaptive` | 1 | Experiment: adaptive vs fixed + escrow flows |
| `T4` | 19 | Experiment/Coding: T4 pre-5b, full and −latency (18 cells) + reading |
| `T4-5b` | 18 | After the 5b simulator change: post-5b, full and −latency |
| `A2` | 3 | Experiment: filter on/off violation rate + paired CI |
| `Coding` | 14 | Coding: PILOT/StageRoute reproduction gap; seller roster; price sources and date; calibrated sample price; v1.0 hash + field names (sample table); episodes field names (App. A); v1.0 config hash (App. B); third cached model (×2, licenses + cache); pytest count (×2, §4.4 + App. B); v1.0 command lines; v1.0 pi grid config path; leakage-check script path |
| `Coding/Experiment` | 1 | Regression gate (seeds 0–2 reproduce v0.1) |

## Protocol ambiguities and how I resolved them (please confirm)

1. **Features before 5b: 6 or 7.** Protocol §5b says T4 runs "before the change (6 features)", but §5 and the later decision put `listed_quality` on the whitelist, making 7. I used 7 everywhere.
2. **Rule baseline.** Protocol §5 says "price low + length anomaly", but answer length is now excluded. I wrote "under-priced quote plus anomalous **billed tokens**", since `tokens_billed` is whitelisted.
3. **Third attack type and Q.** The protocol lists only q_swap and q_theft. With selective downgrade added, I added a q_downgrade column and made Q the token-weighted mean over all three. Its field name is TBD.
4. **E definition.** The protocol defines E by tokens (fraud tokens / total tokens). The v0.1 text defined `fraud_share` as attacked purchases / served purchases. I used the protocol's token definition; Coding should confirm the code matches.
5. **Stripping scope.** The protocol says the blacklist is "stripped before release". I wrote that the **public feature view** is stripped and the labels ship in held-out label files, so the leaderboard can still score. Whether the full five-file export is also stripped is for Coding to decide.
6. **D3 vs the fixed-rate family.** I made D3 the a=0.1 member of the fixed-rate audits a∈{0.05,0.1,0.2} and kept v0.1's "random audit on a simple compliant selector".
7. **Fixed router.** Protocol: "cheapest/strongest", so there are two rows.
8. **T4 split with more seeds.** I kept 0–13 / 14–19 and noted "70/30 rounded when more seeds are run".
9. **precision@10 unit.** Not specified (per test run or pooled); the text doesn't commit. Experiment should decide before running.
10. **π* table rows.** The new grid has 18 points, so the main appendix table shows only 0.08–0.14 and the full grid is in the release.
11. **release/v1.0 contents.** The paper describes the pack per protocol §8 (LICENSE, requirements, REPRODUCE, MANIFEST, data card, exports). Today `release/v1.0/` only has LICENSES, LICENSE_NOTES, MANIFEST(.json), REPRODUCE, cache and partial results; there is no data card, requirements, LICENSE copy or exports yet. Coding needs to add these before submission.


---

# Pass 2: first v1.0 batch filled in (2026-11-10, ~11:00 Asia/Shanghai)

Sources, read directly and not retyped: `results/v1.0/T2_v01scale_20seed.{json,md}` (the recomputed version with unweighted Q and tail-trade fractions, written 10:55–10:56), `A2_compliance_control.{json,md}`, `Q_gate_v01scale.json` and `regression_gate_seed0-2.json`. The tables were generated from the JSON with a script, so no numbers were typed by hand.

The batch is v0.1 scale: 3 sellers, one strategic seller using swap and theft only, the old baselines (PILOT+compliance, StageRoute+compliance, D3), seeds 0–19, an 11-point π grid that includes 0.11, paired bootstrap with 10k resamples, and Holm correction.

Every caption that uses this batch carries `\vzeroonenote` = "v0.1 scale (3 sellers); to be replaced by the 40-seller main table." The abstract and introduction cite no numbers.

## Filled in

| Where | What |
|---|---|
| §5 Regression gate | Passes: 1350 values (90 rows × 15 fields), max \|Δ\| = 0 |
| §6.1 Fig. 2 | Experiment's `T2_v01scale_pareto_EQ.png` (π=1 and π=0.1; StageRoute hollow), caption notes the tail-trade fractions |
| §6.1 text | "First batch" paragraph: the Pareto front is {D3 reference, StageRoute} at every π, no winner, and StageRoute's Q is not identifiable |
| §6.2 Table 6 (new) | For each of the 11 π values: E and Q for StageRoute, PILOT and D3 (mean [CI]) plus the tail-trade run fraction; ° marks Q cells that aren't identifiable |
| §6.2 Fig. 3 | Experiment's `T2_v01scale_E_vs_pi.png` and `T2_v01scale_Q_vs_pi.png`, side by side |
| §6.2 Reading | The headline as approved by Review, Idea and Experiment; E endpoints and Holm significance (PILOT at every π≤0.2, StageRoute at every π≤0.12); StageRoute and PILOT Q statements; D3 at 0.118 / 0.106 by construction; reputation_rounds=0, so no suspension and no rounds excluded; π* not kept |
| §6.4 A2 + Table 8 (new) | Filter on/off violation and fill rates for StageRoute, PILOT and cheapest, plus D3 with the filter on; paired off−on CIs; D3 filter-off left as TBD |
| App. C π* | Table 11 with all 11 π: paired ΔJ [CI] and number of seeds with ΔJ>0; rule outcome (not kept); per-seed crossover distribution (2/20 in (0.10,0.12); non-monotone seeds 3, 8 and 14) |
| App. C Table 12 (new) | Per-mode q_swap and q_theft for the 3 policies × 11 π; q_downgrade marked n/a at v0.1 scale |
| App. C Hedge check | τ=1.0 and the same front at all 11 π, labelled as not the formal gate |
| App. B | First-batch file paths and `scripts/v1/` |

## Text changes from group decisions

- **§3.4 E:** follows the code. `tokenmarket/metrics.py:72` computes `fraud_share = len(attacked)/len(served)`, so E is attacked served **purchases** over served purchases, not a token share.
- **§3.4 Q:**
  - Q is the unweighted mean of the q the seller plays over listed tail rounds (12 of 48), with per-mode columns. The primary Q is the simple average of the three modes, with no token weighting anywhere.
  - Q measures attack intent; E measures attacks that reach buyers.
  - A new "Identifiability" paragraph covers the tail-trade fraction column and hollow points.
- **Q gate:** EXP3 or fictitious play, at every π, at the 40-seller scale. The Hedge check is appendix-only.
- **Baselines (Intro and §5):** D3 is its own row, since it also reroutes by audit-corrected quality. Fixed-rate audits a∈{0.05, 0.1, 0.2} are separate rows. The T1 table now has 10 rows plus a tail-trade column.
- **T4:**
  - Metrics are computed per test run (40 sellers ranked within a run), averaged over runs, with a bootstrap over runs.
  - The full feature set is 7; the no-latency ablation is 6.
- **§4.2 Release:** the blacklist is stripped. Train-run labels are public; test-run labels are withheld and scored by an evaluation script. A new "How to submit" paragraph was added; the script path and submission channel are TBD.
- **Wording:** "Degradation" headers became "Bandit routers under sparse labels", and the contribution bullet says E and Q "change", not "degrade". The Conclusion carries the approved T2 meaning, with no numbers.
- **Limitations:** Q is also not identifiable for sellers a router avoids.
- **Float fix:** the ΔJ table had silently dropped out of the PDF, so it is now `[H]`.

## Remaining TBD: 117

| Source | Count | Notes |
|---|---|---|
| T1 | 52 | 40-seller main table (10 rows × 5 cells), Pareto plot, reading |
| T4 | 19 | |
| T4-5b | 18 | |
| Coding | 15 | Adds the T4 evaluation script and submission process |
| Q-gate | 3 | |
| A2 | 3 | D3 filter-off, policy id `audited_cascade_unfiltered` (implemented by Coding, not yet run) |
| T2 | 2 | 40-seller curves and reading |
| T2-pistar | 1 | 40-seller rule outcome |
| T1/T2 | 1 | Abstract headline |
| T1-secondary | 1 | |
| T3-delist | 1 | |
| T3-adaptive | 1 | |

The regression-gate placeholder is resolved.

## Discrepancies found

1. **E denominator.** Experiment's md says "fraudulent served tokens / served tokens"; the code is per purchase. The paper follows the code. Experiment should fix the md.
2. **Q significance.** Experiment's first summary said no Q change vs π is significant after Holm. The file shows StageRoute ΔQ significant at π=0.06, 0.05 and 0 (Holm p≈0), and the later steering message agrees. PILOT has no significant change anywhere.
3. **Old pre-recompute values.** D3 Q 0.113 became 0.118 after the unweighted recompute, and StageRoute's range "0.67–0.90" is now 0.671–0.934. The paper uses the recomputed file.
4. **ΔJ at 0.12.** The summary's upper bound −0.014 is −0.0135 in the file; the paper prints −0.0135.
5. **Rounding of the approved ranges.** "PILOT Q 0.88–0.94" is 0.881–0.937 in the file; the text prints the exact values.

## Zip

`docs/kdd_overleaf_v1.0.zip` contains `main.tex`, `refs.bib`, `main.bbl` and the 4 figures used. Unzipped, it compiles with 0 errors to 10 pages.


## Pass 4 — Review/Idea wording fixes (2026-11-10, Asia/Shanghai)

Build: 0 errors, 10 pages; main body (through Ethics) ends on page 8; appendices start on page 8. Zip rebuilt (same 7 files) and compiles from a clean unzip with 0 errors. TBD markers now 120 (`grep -o "TBD{"`; new: ethics price sources, E_tok).

- **Abstract / §5 / Intro bullet / App. B:** "protocol written/fixed before any v1.0 run" was untrue. Now: protocol frozen before the 40-seller main table was run; post-first-batch clarifications are in the new **Appendix "Protocol clarifications after the first batch"** (`app:amend`), which lists (1) Q unweighted: mean over present (listed, not suspended) rounds, simple average across attack types; (2) E denominator = purchases (attacked served purchases / served purchases), matching code.
- **§6.1 first batch (Pareto):** dropped "{D3, StageRoute} is the front". Now: the front can only be read along E; StageRoute's Q is not identifiable, so no conclusion is drawn about front membership.
- **§6.2 Reading:** "does not support conclusions about deterrence" restricted to sellers that are avoided and not trading.
- **§6.2 PILOT:** subject fixed — PILOT still buys from attackers; conclusion prefixed "Under this setting's seller learning rule and at v0.1 scale".
- **§6.2 D3:** "by construction" now applies only to invariance in π; the value 0.118 depends on audit rate and slashing. Added the qualifier: D3's lower Q than PILOT's holds only under this setting's audit and slashing parameters (a=0.1) and the current seller learning rule, to be re-checked on the 40-seller main table with EXP3 or fictitious play; not evidence that audits deter attacks in general.
- **§3 metrics + App. C:** primary E stays per purchase; secondary column E_tok (billed-token-weighted E) added to the appendix secondary table as TBD.
- **§6.4 A2:** names the D3 filter-off policy `audited_cascade_unfiltered`; results remain TBD (text + table caption).
- **Ethics:** "list prices are calibrated to public API price lists" → "intended to be calibrated … (TBD: Coding: price sources, access date, calibration)".
- **Not changed:** π* appendix (approved as is). Note: the appendix Hedge-check paragraph still says "the same front {D3 reference, StageRoute}"; it is already caveated (StageRoute Q mostly not identifiable, not the formal gate) but Review may want it aligned with the new §6.1 wording.


## Pass 5 — Hedge / Q-gate / protocol alignments (2026-11-10, Asia/Shanghai)

After Review's request and 傅老师's agreement on the five pre-run rulings:

- **App. C Hedge check:** dropped “the same front {D3 reference, StageRoute}”. Now matches §6.1: the front can only be read along E; StageRoute's Q is not identifiable, so no front-membership conclusion. τ=1.0 is kept; Hedge does not count toward the gate.
- **§3 Q-gate:** formal alternative is fictitious play; front-membership is checked only on points where Q is identifiable. EXP3 is appendix-only (to be reported after the 40-seller run) and does not count toward the gate.
- **§6.2 D3:** re-check is under fictitious play (formal gate); EXP3 is appendix-only.
- **Price calibration:** leftover “are calibrated” claims in §3 Sellers, §4 cache, and Limitations now match Ethics: TBD, present tables use the simulator's existing ratios, not a public-list calibration.
- **T4 split:** main table uses a fixed roster; T4 uses `--resample-roster`.


## Pass 6 — 40-seller main table filled (2026-11-10, Asia/Shanghai)

Sources, read directly (no invented numbers): `results/v1.0/main/{inference.md,inference.json,summary.md}` (authoritative 40-seller egreedy table), `results/v1.0/main_fp/` (fictitious-play gate, already recorded in `inference.json` under `q_gate`), `results/v1.0/a2_filter_off/{A2_paired.md,A2_paired.json}` (Review-locked), and `results/v1.0/main_exp3/inference.md` (appendix only, not part of the Q-gate). Frozen config: `configs/v1.0/frozen/scale.yaml`, sha256 `780e9b961d89bad6fd520c9cbfd5710055ff2d5d3e0ff3bcfbd745709eb0da6c`.

Not uploaded to Overleaf. `docs/latex-sigkdd/` (v0.1 edit copy) was not touched.

Build: TinyTeX pdfLaTeX + BibTeX, 0 errors, 0 overfull boxes. PDF is 13 pages. Body (title through Ethics) ends on page 8; References and Appendix A begin on page 8.

### Filled in the body

| Where | What |
|---|---|
| Abstract | T1/T2 headline: both bandits' E rises significantly as labels vanish; StageRoute Q is identifiable and rises as π falls; PILOT Q does not rise vs π=1 (lower only at 0 and 0.02); audits sit at low E mainly by rarely trading with strategic sellers. No winner, no deterrence claim, no "D3 won". |
| Intro / §5 baselines | Random-intensity audit ($a_t\sim U(0,2a)$, $a=0.1$). D3 and fixed-rate $a=0.1$ merged into one row (9 methods, not 10). Roster filled: 40 sellers (31 honest + 9 strategic: 3 swap / 3 theft / 3 downgrade). Other Coding TBDs left in place. |
| §3 metrics / Q-gate | E includes selective downgrade. E_tok is a T1 side column. Gate outcome filled: 8 identifiable methods, every π, $τ_a=0.643$ (23 vs 5), just over 0.6; Q stays primary; order is not called stable; front membership is not reported as a finding. EXP3 is appendix-only and does not count toward the gate. |
| §6 intro | 40-seller egreedy table is the main result; first batch moved to the appendix. |
| T1 table (tab:t1) | 9 rows at π=1, 20 seeds: E, E_tok, Q, tail-trade runs. Suspended-rounds column dropped (`reputation_rounds=0`). Cheapest Q marked $°$ (0/20). Per-mode $q$ moved to the appendix. |
| fig:pareto | Official `EQ_scatter.png` as `fig2_40seller_pareto_EQ.png` (π=1 and π=0.1; cheapest hollow; front membership not concluded). |
| T1 reading | Review-locked: gate just passes; no stable ranking; no front winner; cheapest along E only; audits just identifiable (12–13/20), low E is avoidance of strategic sellers not deterrence. Do not lean on audit Q "near uniform / 0.52–0.54" as learned intent (averaging over no-trade runs not yet confirmed). Do not write StageRoute Q=0.609 as already deterred. |
| T2 table (tab:t2) | 40-seller selected-π set {1, 0.5, 0.3, 0.2, 0.12, 0.1, 0.08, 0.06, 0.02, 0}: E and Q for PILOT, StageRoute, D3-ref, plus tail-trade fractions. |
| fig:t2 | Official `E_vs_pi.png` and `Q_vs_pi.png`. Caption does not call StageRoute hollow; cheapest Q is hollow; audit flatness is by construction. |
| T2 reading | Review-locked 40-seller wording (both bandits' E worse vs π=1 at every lower π; StageRoute Q identifiable and significantly higher as π falls; PILOT Q as specified; π=0 E gap n.s.; cheapest E=0 / Q not identifiable; audits as in T1). π* is appendix-only; (0.10, 0.12) not kept. |
| T4 | One-sentence body stub: uses `--resample-roster`; results pending. Empty grid moved to the appendix. |
| A2 | Review-locked 40-seller table and reading (filter OFF raises violation from 0; cheapest 0.065, not the highest; fill Holm n.s.; E: PILOT/StageRoute/cheapest n.s., strongest 0.446→0.519; audit E dip significant but Q not identifiable at 1/20 — Q OFF not reported, not read as fewer attacks; StageRoute OFF tail 11/20, no strong reading). D3 OFF is `fixed_audit_a0.10` + `--no-compliance-filter`. No `audited_cascade_unfiltered`, no `\vzeroonenote`. |

### Moved to the appendix

- Entire v0.1-scale first-batch T2 table, Pareto and E/Q figures, and bullet reading (`\vzeroonenote` only here).
- Empty T4 table (still TBD).
- 40-seller π* table and reading (ΔJ>0 at every π; +0.114 [0.104, 0.122] already at π=1; 20/20 seeds with no crossover; (0.10, 0.12) not kept; not written as "D3 won"). Short first-batch π* note kept.
- $J$ at π=1 (CIs from `inference.json`). Cost/quality still TBD (not in the inference file). E_tok curve (`figC_40seller_Etok_vs_pi.png`).
- Per-mode $q$ at selected π, including $q_{downgrade}$; cheapest $°$.
- Hedge check kept as first-batch ($τ=1.0$; StageRoute Q unidentifiable at that scale). Formal 40-seller gate is fictitious play and just passes, as in the body.
- EXP3 appendix table and reading from `results/v1.0/main_exp3/` (Q near 0.501 for all methods/π; E rises as π falls; absolute E must not be compared with the egreedy main table; not part of the gate).
- Repro paths added: `results/v1.0/main/`, `main_fp/`, `a2_filter_off/`, `main_exp3/`, frozen `scale.yaml` sha256.

### Remaining TBD (expected)

T4 and T4-5b cells (36) + T4 script/process; T3-delist; T3-adaptive; T1-secondary cost/accuracy; Coding items (reproduction gap, prices, hash/field names, third model, pytest count, command lines, config path, leakage-check script).

### Confirmations

No sentence says the 40-seller Pareto front is {a=0.20}; no winner; no "D3 won" in the body; no "audits deter"; no 40-seller "StageRoute Q is not identifiable".


## Pass 7 — Data figures redrawn to the Nature figure spec (2026-11-10, Asia/Shanghai)

Per 傅老师's figure spec (89/183 mm widths, Arial-class font 6–7 pt, 8-pt bold lowercase panel labels, 0.5–1 pt lines, 0.5 pt axes, no top/right spines, no grid, no in-figure titles, Okabe-Ito with ≤5 colours and a fixed colour per method, CI bars/bands with n and error meaning in captions, frameless legends / direct labels, vector PDF with Type 42 fonts + 600 dpi PNG). No numbers, claims, or scientific caption content changed. Not uploaded to Overleaf.

- **Script:** `scripts/figures_nature.py` (shared style + fixed method→colour map; reads only `results/v1.0/main/inference.json` and `results/v1.0/T2_v01scale_20seed.json`; asserts B = 10,000, 95% CI).
- **Font:** Liberation Sans (metric-compatible with Arial; Arial not installed). Embedded as TrueType/Type 42 (`pdffonts`: CID TrueType, emb yes). Text 6–7 pt at figure size; 89 mm figures scale ×0.95 into the 84.7 mm acmart column, so the smallest text prints at ≈5.7 pt (≥5 pt).
- **Colour map (all figures):** PILOT vermillion #D55E00; StageRoute blue #0072B2; strongest orange #E69F00; cheapest black #000000 (hollow where Q is not identifiable); all five audit arms bluish green #009E73, told apart by line style / marker (D3-ref a=0.10 dashed ◆, a=0.05 dotted ▼, a=0.20 dash-dot ▲, random-intensity solid ■, risk-adaptive dash-dot-dot ✚). ≤5 colours per figure.
- **Figures:**
  - `fig2_40seller_pareto_EQ.{pdf,png}` (Fig. 2, `figure`, 89 × 42 mm): panels a (π=1) and b (π=0.1); 95% CI bars on E and Q; identifiable solid, cheapest hollow; no point is highlighted as a front. Direct labels; audit arms labelled as one group "audit arms (5)" (they overlap at E≈0.005). A four-panel version with zoomed audit panels was tried and pushed Limitations–Ethics onto page 9, so it was dropped.
  - `fig3_40seller_E_Q_vs_pi.{pdf,png}` (Fig. 3, `figure*`, 183 × 50 mm): merges former `fig3a_40seller_E_vs_pi.png` + `fig3b_40seller_Q_vs_pi.png` into panels a (E) and b (Q), 95% bands, cheapest Q hollow at every π.
  - `figC_40seller_Etok_vs_pi.{pdf,png}` (Fig. 4, appendix, 89 × 55 mm).
  - `fig2_v01scale_pareto_EQ.{pdf,png}` (Fig. 5, appendix, 89 × 46 mm; StageRoute hollow where tail-trade fraction ≤ 0.5).
  - `fig3_v01scale_E_Q_vs_pi.{pdf,png}` (Fig. 6, appendix, 183 × 55 mm): merges former `fig3a/3b_v01scale_*.png`.
- **main.tex:** the six data `\includegraphics` now point to the PDFs (3a/3b pairs → one merged PDF each). Captions: "left/right" → panel letters; added "means over n = 20 seeds; bars/bands are 95% paired-bootstrap CIs (10,000 resamples)" and the audit-arm colour note; Fig. 2 caption adds "values in Table 5" for the overlapping audit arms. Fig. 2 `\Description` no longer refers to a figure title (there is none). All other caption text unchanged.
- **Not redrawn:** `fig1_five_layers.png` (schematic; no generating script in the repo, only a static SVG export). `fig2_pi_star_crossover.png` is not referenced by main.tex.
- **Superseded (left in `figures/`, not in the zip):** `fig3a/3b_40seller_*.png`, `fig3a/3b_v01scale_*.png`.
- **Build:** pdfLaTeX + BibTeX, 0 errors, 0 overfull boxes, no undefined references; 13 pages; body (title through Ethics) ends on page 8; References begin on page 8.
- **Zip:** `docs/kdd_overleaf_v1.0.zip` rebuilt: main.tex, refs.bib, main.bbl, fig1 PNG, and the 5 new figures as PDF + PNG (14 files). Compiles from a clean unzip with 0 errors, 13 pages, Ethics on page 8.


## Pass 8 — Appendix Q averaging / gate robustness note (2026-11-10, Asia/Shanghai)

Per Idea/Chief: main-table numbers unchanged. Added one appendix paragraph under Q-gate checks, and a reproducibility path row for `results/v1.0/main/Q_tail_only_robustness.md`.

- Audit $\mathrm{Q}$ (0.52--0.54) is the unweighted mean over all 20 seeds, including 7--8 no-tail-trade runs (protocol: a sale is not required).
- Tail-trade-runs-only: D3 0.538 → 0.536 (other audit arms similarly); no-tail $\mathrm{Q}$ is not concentrated at 0.5 (about 0.39--0.62).
- Dropping the five low-identifiability audit arms leaves PILOT, StageRoute, and strongest, $\tau_a=1.0$ at every $\pi$; robustness only, pre-registered eight-method gate unchanged.
- Body claims and T1/T2/A2 numbers were not edited.


## Pass 9 — Official T4 (D3, π=1) filled per Review wording (2026-11-10, Asia/Shanghai)

- Body §6 T4 and the conclusion: task is defined; official setting is `fixed_audit_a0.10`, π=1, `--resample-roster`; scores are on sellers who traded in the target window (89 test sellers, not all 40 on each roster); test positives 2/89; only 2/6 test runs have both classes, so detection performance is not reported and the latency ablation is not interpreted. Scarcity matches D3's rare trade with strategic sellers (E=0.0066). No pooled AUROC in the body.
- Protocol §T4: scoring set and the 4/6 non-reporting rule.
- Appendix: counts table; pooled any+logreg AUROC 0.977 / AP 0.417 and ΔAUROC +0.040 [0.011, 0.076] only as a note marked as not following the protocol (per-run then average). Post-5b still TBD. Paths `results/v1.0/t4_eval/` and `t4_eval_per_run/`.
- PILOT supplementary condition not added (not yet run / not yet a locked result).

## Pass 10 — PILOT T4 supplement filled per Review wording (2026-11-10, Asia/Shanghai)

Official D3 T4 body wording from Pass 9 is unchanged: no detection performance, no pooled AUROC 0.977 in the body. PILOT, π=1, current simulator (before 5b) is added as a supplement only, not a new official main result.

- Abstract and conclusion: official T4 (D3) is not scorable; a PILOT, π=1 supplement is reported in §6.3 and is not a new official main result. Abstract wording was tightened slightly so the new clause fits without pushing Ethics off page 8.
- Body §6.3: scorable 6/6; not read as detection already succeeding or as buyers generally detecting fraud. 49 positives / 215 scored sellers come from PILOT still trading with strategic sellers (E=0.158), not from solving scarce positives under D3, and not a general claim that trading with attackers makes detection scorable. any + logistic AUROC 0.970 [0.941, 0.991], 0.895 without latency, above the rule 0.703 in all six test runs under this setting only (not equally strong without latency). Latency contributes on any but not for every attack type; types must not be collapsed into a single 0.97 (downgrade is weaker).
- Appendix: counts table (train 524/105, test 215/49); official per-run mean table for any (logistic / GBDT / rule, 7- vs 6-feature, ΔAUROC); swap and downgrade logistic ΔAUROC intervals contain 0; downgrade logistic 0.826 / 0.458 / 0.167; theft near ceiling; pooled-over-sellers figures in the export are not reported. Path `results/v1.0/t4_pilot_eval/`. Post-5b still TBD. Repro path row added.
- Build: pdfLaTeX, 0 errors, 14 pages (appendix tables added one page). Body including Ethics still ends on page 8. No 0.977 in pages 1–8.


## Pass 11 (2026-11-10, Asia/Shanghai) — Review figure-caption items
- Fig. 3 (and Fig. C, v0.1 Fig.): caption now states the π axis is symlog (linthresh 0.08; v0.1 figure 0.05).
- Q markers in Fig. 2 / Fig. 3: solid = 17–20/20 tail-trade runs; half-filled = audit arms just identifiable (12–13/20); hollow = cheapest (0/20). Captions updated. Marker key added to Fig. 3b.
- No numbers changed. 14 pages, Ethics on page 8.
- \Description of Fig. 2/3 now mention half-filled audit markers.


## Pass 12 — Decision Point A (result 1) written in; T1 → router × audit (2026-11-13, Asia/Shanghai)

Approved by 傅老师 on 2026-11-13. Official source: `results/v1.1/v1.2_decision_a_eval/`, commit `f759cd6`, and frozen `docs/v1.1/PROTOCOL_v1.2.md` §1.1–§1.4. Title, author, conference metadata, ORCID/CCS TODOs, and figure assets unchanged. Committed and pushed as 62b7f9d on v1.1.

- **Body T1:** replaces the v1.0 policy table with the v1.2 router × audit factorial table (`tab:t1`): PILOT and strongest separately, eight audit rows each, six mean columns (E/Q for egreedy, fictitious play, EXP3), 20 seeds, three decimals. Stars use the official merged 84-test Decision-A Holm flags; below-a* rows retain their individual significant cells but are explicitly not counted toward result 1. Both routers have 8/8 qualifying hits at {0.05, 0.10, 0.20, risk-adaptive}. Cascade comparisons are excluded.
- **Generated numbers:** `scripts/pass12_decision_a_tables.py` reads the official CSVs, verifies supplied sha256 files, cross-checks means/deltas/p-values against `decision_a_eval.json`, and checks the direction votes. It writes `tables/decision_a_main.tex`, `decision_a_deltas.tex`, and `decision_a_facts.tex`. The appendix includes all 84 default-parameter paired deltas, 95% CIs, raw and merged-Holm p-values. Lower-penalty cells remain in the readout; P/16 is descriptive only and never evidence of audit efficacy.
- **v1.0 retained:** the old T1 table (`tab:t1-v10`, numeric/tabular content unchanged), Pareto figure, and Reading paragraph move to a separate “v1.0 48-round baseline Pareto view” appendix. Its “not read as deterrence” wording is explicitly scoped to v1.0. Cross-references, the 48-round Q gate/EXP3 check, T2 audit interpretation, and E_tok links now distinguish that baseline from Decision A. T1 explicitly states identity+length checks for all v1.2 routers versus v1.0 identity-only non-cascade checks, `trust_feedback=false`, and no direct numerical comparison with v1.0 audit arms.
- **Protocol / claims:** T1 goal states the pre-run classification, frozen a*(P), three learning rules, and merged 84-test family (§1.2 freezes pooling both routers; additionally pooling all three learners is at least as strict as per-learner 28-test families by the Holm subset property; same verdict (wording corrected in Pass 13)). Abstract, contribution 3, conclusion, and limitations state result 1 only in this simulator under default parameters at 1000 rounds. EXP3 remains in every direction vote (no WP2 exclusion), Q stays near 0.5, PILOT E has no significant change, and its qualifying Q decreases are small (−0.003 to −0.009). “We do not propose a new deterrence or routing method” is retained.
- **Review's three points:** (1) stored zero raw p-values render as `p<2\times10^{-4}` / `<2\times10^{-4}` under labelled p columns; zero Decision-A Holm values render as `≤0.017`, with bound `≤84·2/B` (floor wording corrected in Pass 13); captions explain the two-sided B=10,000 resolution; (2) simulation/default-parameter/1000-round/three-rule scope is explicit, with no inference to real API markets or deployments; (3) both a=0.05 rows carry †, and captions identify the upper edge of frozen a*=[0.044,0.050]. Required p-value and overclaim greps were run; only pre-existing scope qualifications / unrelated substring matches remain in the latter.
- **Reproducibility:** `tab:repro` adds the Decision A readout, commit, protocol, full verified hashes, and generator command. Checksum correction to the brief: the actual readout and its `.sha256` at `f759cd6` agree on `5d3f52292883a73dec8a892e7e64c250eeb7eb62c09b1bb36508e7e3c034dad9` (not the brief's “…ed83db”); protocol is `daddac6c0dddb22b08701caff5715e77215ae13a588512af176ff4933430b102`.
- **TBDs/status filled:** Decision A classification and pending audit-efficacy status are now the official result 1, including router-specific hits, the generated factorial means, paired effects, and EXP3 qualification. There were no literal Decision-A TBD/TODO markers in the incoming LaTeX; all 22 unrelated literal TBD occurrences (Coding, T1-secondary v1.0 cost/accuracy, T3, T4-5b, prices, etc.) are unchanged.
- **Layout / build:** main T1 is a compact `table*` in footnotesize; retained v1.0 T1/Pareto material is appendix-only. A2 may float while the closing body text continues; its table/reading are preserved. A page break before the historical first-batch appendix prevents overfull float pages. `latexmk -pdf -interaction=nonstopmode main.tex` (pdfLaTeX + BibTeX): **0 errors, 0 undefined references/citations, 0 overfull hbox/vbox; 19 pages; Ethics ends on page 8, References start on page 8**, verified with pdftotext page positions. Appendix growth accounts for the added pages.
- **Overleaf zip:** `docs/kdd_overleaf_v1.0.zip` rebuilt with main.tex, refs.bib, main.bbl, all three generated input files, and the figures used by main.tex (PDF + PNG for data figures; existing layer schematic PNG): 17 files. A clean unzip in `/tmp` compiles with **0 errors, 0 undefined references/citations, 0 overfull boxes**, also 19 pages with Ethics ending on page 8. No figures were added or redrawn.

## Pass 13 — Review fixes to Pass 12 (2026-11-13, Asia/Shanghai)

Review source: `/workspace/review_notes/kdd_pass12_review_2026-11-13.md`; Pass 13 was committed and pushed as `9ca0060` on `v1.1`. Official results and protocols are unchanged.

- **P0-1 — Two-sided p-value floor:** `p_value()` now renders stored zero raw values as `$<2\times10^{-4}$`, consistent with resolution `2/B`, B=10,000. Stored zero Decision-A Holm values render as `$\le 0.017$`; main and delta captions state the conservative bound `≤84·2/B = 0.0168`. Nonzero values retain four decimals. Both generated default-parameter tables were regenerated; no obsolete floor remains in the paper or generator. Pass 12's historical floor wording above is corrected explicitly.
- **P0-1 — Holm sensitivity:** the generator reruns Holm on the 84-test Decision-A family with zero raw values floored separately at `1/B` and `2/B`. It asserts all flags equal `contrasts.csv`'s `significant_decision_a`, then reconstructs the direction votes and asserts the same 16 result-1 hits as `direction_consistency.csv`. Output:

  ```text
  Zero floor 1/B: 84/84 flags unchanged; 16 result-1 hits unchanged; max adjusted p among significant = 0.0224.
  Zero floor 2/B: 84/84 flags unchanged; 16 result-1 hits unchanged; max adjusted p among significant = 0.0224.
  ```

- **P0-2 — Learner qualification:** result 1 now states the pre-run rule (significant same-sign decrease under at least two of three learners, none significantly reversed). PILOT E qualifies through egreedy and fictitious play, PILOT Q through all three; strongest qualifies through all three for both metrics. The EXP3 PILOT E nonsignificance caveat remains explicit.
- **P1-1 — Count and scope:** the result paragraph and T1 footer define 8/8 per router as four counted audit levels `{0.05, 0.10, 0.20, risk-adaptive}` × `{E,Q}`. Abstract, contribution 3, and conclusion restrict the claim to rates at/above the frozen break-even and risk-adaptive, and call the criterion the pre-run three-learner direction rule. Simulation/default-parameter/1000-round scope remains explicit.
- **P1-2 — Family definition:** §1.2 freezes pooling PILOT and strongest; the analysis additionally pools three learners into 84 tests. The body and Pass 12 log now say this is at least as strict as per-learner 28-test families by the Holm subset property, with the same verdict, without claiming the protocol froze a per-learner family.
- **P1-3 — Audit effect terminology:** replaced the abstract, introduction, T1 task heading, and RQ/task-table labels with router × audit effect wording. Remaining `deterrence` occurrences in `main.tex` are disclaimers, including the retained v1.0 interpretation and “We do not propose a new deterrence or routing method.”
- **P1-4 — Mechanism verified:** `results/v1.1/v1.2_decision_a/run_meta.json` has `reputation_rounds=0` under both `base_config.market.audited` and `base_config.fraud`; all 48 manifest cells disable trust feedback. All 2,880 `factorial/per_seed.csv` rows have `trust_feedback=False` and `delisted_rounds_tail=0`. The generator asserts these facts. Audits and T1 setting paragraphs explain that the routing rule is identical across audit levels, so these E drops are not v1.0-style avoidance/delisting; the historical reading is preserved.
- **P1-5 — Static break-even caveat:** the result paragraph states that significant learner responses also occur below static break-even at a=0.01–0.03; these levels do not count toward result 1, which does not confirm the a* model.
- **P1-6 — Cascade reported separately:** new `tables/wp1_cascade.tex`, generated from official `results/v1.1/wp1_eval/wp1_eval.json` and `contrasts.csv` (context: `wp1_eval.md`), reports P=0.25, π=1, a=0 E/Q means and all 14 paired E/Q contrasts at nonzero audit levels, 95% CIs, raw p, and the readout's own 42-test report-family Holm values/status. It is labelled 48-round egreedy diagnostic, outside Decision A and never counted toward result 1. All eight Q cells are identifiable as reported (12–14/20 tail-trade runs). Its zero Holm bound uses its own family: `≤42·2/B = 0.0084`, printed `≤0.009`. The appendix gives the frozen v1.1 protocol sha256 and points to `results/v1.1/v1.2_wp1/factorial/{cells.json,per_seed.csv}`; no separate v1.2 WP1 evaluation file exists. Parsed-JSON equality of v1.2 and v1.1 WP1 factorial `cells.json` was verified and is asserted by the generator; no broader equality claim is made.
- **P1-6 — Lower penalties reported:** new `tables/decision_a_lower_penalties.tex`, generated from `results/v1.1/v1.2_decision_a_eval/{cells.csv,contrasts.csv}`, contains both P/4 and P/16 tables: all 192 E/Q means across router × learner × audit × penalty, with official 42-test report-family Holm markers. Stars indicate significant decreases and upward arrows significant increases. Captions state P/4 a*≈0.18–0.20, P/16 a*≈0.71–0.80, descriptive only, never evidence of audit efficacy, and outside the Decision-A family. Reproducibility rows now include the cascade readout, v1.2 WP1 runs, and lower-penalty CSV paths; the body replaces “outside this grid and unused” with the appendix pointer.
- **P1-7 — Documentation:** README now states 21 total pages, body plus Ethics ending on page 8, and References starting on page 8. Pass 12 now records “Committed and pushed as 62b7f9d on v1.1.” Its family and p-floor descriptions are corrected above.
- **Build / checks:** `python3 ../../scripts/pass12_decision_a_tables.py` and `latexmk -pdf -interaction=nonstopmode main.tex`: **0 errors, 0 undefined references/citations, 0 overfull boxes; 21 pages**. PDF text confirms Ethics, including its final sentence, ends on **page 8**; References start on **page 8**. Title/author block and historical v1.0 T1 tabular content compare exactly with the incoming version. Required p-value/family greps pass; `deterrence` remains only in disclaimers. No new TBDs: all **22** existing `\TBD{...}` occurrences are unchanged, covering unrelated Coding, reproduction, prices/config, T1-secondary, T3, and T4-5b work. No requested source numbers were missing. P2 `.gitignore` work was skipped.
- **Overleaf zip:** `docs/kdd_overleaf_v1.0.zip` rebuilt with the same 17 members plus the two new generated tables (**19 files**). Clean unzip in `/tmp` and `latexmk -pdf -interaction=nonstopmode main.tex`: **0 errors, 0 undefined references/citations, 0 overfull boxes; 21 pages**, with Ethics and the start of References on page 8.


## Pass 13b — EXP3 scope, lower-penalty captions, and display rounding (2026-11-13, Asia/Shanghai)

Review source: `/workspace/review_notes/kdd_pass13_review_2026-11-13.md`. Official results and protocols are unchanged.

- **P1-a / default-P scope:** the Limitations sentence now uses Review's wording with explicit default-P scope: “Under EXP3 at default $P=0.25$, $\Qmet$ stays $\approx0.5$, PILOT's $\Emet$ shows no significant change, and PILOT's qualifying $\Qmet$ decreases are small.” The §T1 learning-rule caveat also now begins “Under EXP3 at default $P=0.25$,” scoping Q≈0.5 and the PILOT E / qualifying Q caveat to that setting. The rest of that paragraph and the surrounding Limitations sentences are unchanged.
- **P1-b — Lower-penalty references:** both P/4 and P/16 captions gained: “EXP3's $a=0$ reference differs across $P$ because its epoch reward is normalised by $\max(\text{revenue scale}, P)$; egreedy and fictitious-play references are $P$-invariant.” The caption was changed only in `scripts/pass12_decision_a_tables.py`, then tables were regenerated with `python3 scripts/pass12_decision_a_tables.py` from the repo root; no tables were hand-edited. All other lower-penalty caption/table content is unchanged. `decision_a_main.tex` and `decision_a_facts.tex` remain byte-identical.
- **Cascade scope unchanged:** its caption already states the official WP1 48-round egreedy diagnostic, outside Decision A and not counted toward result 1, so the caption and appendix paragraph remain unchanged. Regeneration only removes signs from five six-decimal zero tokens through the shared `delta_cell()` helper; nonzero values such as `-0.000044` are unchanged.
- **P2-1 — Unsigned display zeros:** `delta_cell()` now removes the sign when a value rounds to zero at the requested precision, retaining signs on nonzero values. All 14 `+0.000` / `-0.000` tokens in `decision_a_deltas.tex` now render as `0.000`; remaining signed-zero token count is **0**. Cascade zeros consistently render as `0.000000`; display precision is unchanged.
- **P2-2 — Pass 13 history:** corrected the Pass 13 header to record that it was committed and pushed as `9ca0060` on `v1.1`; the rest of the Pass 13 log is unchanged.
- **P2-3 — Build artifacts retained:** existing build artifacts remain in the repo; none were removed or untracked. Rebuild updates and newly generated build bookkeeping files are left in place. Untracked `results/` directories were not touched.
- **Source build:** `latexmk -pdf -interaction=nonstopmode main.tex` from `docs/latex-sigkdd-v1.0/`: **21 pages, 0 errors, 0 undefined references/citations, 0 overfull boxes**. PDF text confirms Ethics, including its final sentence, ends on **page 8**, and References start on **page 8**. The longer captions introduce no overfull boxes; no layout changes were needed.
- **Overleaf zip:** `docs/kdd_overleaf_v1.0.zip` rebuilt with exactly the same **19 members**, all byte-identical to their repo sources. A clean unzip in `/tmp` compiled with the same command: **21 pages, 0 errors, 0 undefined references/citations, 0 overfull boxes**; Ethics, including its final sentence, ends on **page 8**, and References start on **page 8**.

## Pass 14 — KDD 2027 D&B P0/P1 text fixes (2026-11-15, Asia/Shanghai)

Starting point: branch `v1.1`, HEAD `2616240` (Pass 13b). Authority: [Round A compliance review](KDD2027_DB_CHECK.md) and [KDD 2027 D&B requirements](KDD2027_DB_REQUIREMENTS.md). All supported text-only P0/P1 fixes are implemented; public access, external representativeness evidence, owner/process decisions, and unverified operational facts remain explicit. This is **not a compliance sign-off**. No experiments, cache generation, table generators, or new result analyses were run. No commit or push was made.

- **C1 — partial:** §4.1 now gives intended MIT / CC BY 4.0 licenses, actual in-checkout artifact paths, the pending public-repository/archival-copy statement, the exact owner URL TBD, and Appendix B recipes. The GitHub remote is not printed as a reviewer download URL: the independent unauthenticated check supplied for this pass returned 404. The repeated shell request here returned no HTTP response and does not supersede that evidence. Local paths are explicitly not public endpoints.
- **C2 — partial:** §4.5 now bounds representativeness using documented roster, synthetic-pool reuse, source-task curation, cached checkpoints versus mock backend, and simulated mechanisms. The existing 40-seller composition is preserved, as is Decision A's repeated 80-task pool. Public GSM8K / MATH-500 long-task sources are distinguished from the pool used for the main results. The text states that prices are uncalibrated, jurisdiction tags are simplified controls, and there is no quantitative comparison to production cross-border inference markets. Workload coverage does not discharge the external representativeness requirement; whether to collect additional evidence remains an owner TBD.
- **C3 — tbd-owner:** no eligibility/deadline discussion was added to the PDF and no cycle was silently changed. The first-cycle abstract/paper deadlines were **July 19/26, 2026 (AoE)** and the listed notification was **November 14, 2026**, before this review. **傅老师 decision:** establish already-submitted status versus internal readiness versus a later-cycle decision, then verify submission/profile/reviewer/disclosure facts from the actual records. Text editing cannot retroactively repair a submitted PDF.
- **C4 — partial:** abstract, contribution 2, §4, conclusion, and Appendix B no longer advertise a completed self-contained/downloadable reference pack. `release/v1.0/MANIFEST.json` is explicitly staging/not-a-release. The actual notes/notices/cache/older pi_dense/T2 subset is described; absent pack-local LICENSE, requirements, data card, and production exports are acknowledged. Root LICENSE/requirements/notes, older five-file boards in `exports/production/` and frozen `release/v0.1/exports/production/`, v1.0 readouts, and Decision A eval paths are distinguished. The older boards are 3-seller / 9 seller-rows, not the 40-seller main table. Completing/publishing a public pack remains pending; `release/` is untouched.
- **C5 — fixed:** the two named Qwen cached checkpoints replace “at least three models” and both third-model/license TBDs. Cache/manifest inspection confirms 250 records, 125 per named checkpoint; this is a provenance count, not a new experimental result. Frozen scale also contains `sim-fast-mock`, `backend: mock`, which is described separately. Code MIT, intended derived data/cache fields CC BY 4.0, attributed Apache-2.0 Qwen checkpoints, public-task MIT notices, and frozen v0.1 non-relicensing are stated accurately. No vendored Qwen license file or third checkpoint is claimed.
- **C6 — partial:** §4.4 identifies root requirements, `scripts/run_v1.py`, frozen Decision A table rendering, and Appendix B for recipes. Appendix B labels the existing three one-click commands as older export/demo/T1–T3 paths, not the 40-seller / 1000-round Decision A workflow or a way to regenerate Table 5. Existing `run_v1.py` and T4 evaluator CLI entry points were inspected; the local evaluator is distinguished from an external score-file service. The leakage script is verified and named, with its heuristic scope and label-dependent correlation checks. `python3 scripts/pass12_decision_a_tables.py` is explicitly rendering from frozen eval files, not experiment reproduction, and was **not executed**. Inline command spaces are rendered explicitly because `\code` uses URL formatting. Versioned run recipes, final hashes/interface details, and attributable pytest evidence remain pending; no clean-environment experiment or test pass is claimed.
- **C7 — fixed:** §4 adds seeded task-type/difficulty pool construction, per-run permutation/reuse, long-task source selection, cached parsed/gold correctness/token fields, mock sampling, and simulated market-generation lineage. Existing source code and notices support this description. The manuscript T4 feature contract explicitly governs over contradictory legacy portions of `docs/DATA_SCHEMA.md`; the schema and frozen protocols are unchanged. §6's fixed-roster overview now explicitly excepts T4's per-run resampling. Final board-field mappings remain marked pending rather than certified.
- **C8 — partial:** the check file retains and dispositions all **22 original TBDs** and lists the **20 current invocations**. Five original placeholders were filled from verified evidence (baseline gap, two third-model entries, grid-config path, leakage-script path); 17 remain or were narrowed/renamed, and three owner TBDs were added. Unsupported tests-passed/release-complete assertions are removed. T3, T1-secondary cost/accuracy intervals, and post-5b T4 are **defined but not reported in this manuscript** in the relevant abstract/body/appendix/RQ statements; 5b is future work, not an already completed second release. All unresolved markers remain red; the macro adds CJK support for 傅老师 without hiding content.
- **C9 — fixed:** abstract/contributions/Related Work/protocol say market-adapted implementations and point to `docs/BASELINES_v1.0.md`. The reproduction-or-gap TBD is replaced by the documented absence of RouterBench/original inputs and the distinction between algorithmic component checks and published-setting reproduction. No original-paper numeric claims were imported. Baseline table labels and result values are unchanged.
- **C10 — fixed:** Ethics retains synthetic-transaction, legal-advice, commercial-API/key, intended-use/misuse, and Feature/Label safeguards. It adds public MIT math-task/no participant-log provenance, scenario tags rather than country fraud tendencies, restricted/reused task and two-model-plus-mock coverage, uncalibrated price/latency transfer limits, possible simulator shortcuts, and a prohibition on real seller sanctions/national-risk rankings. No IRB, consent, or text-screening determination is invented.
- **C11 — partial:** a single §4.4 sentence explicitly leaves long-term host, named maintainer, and optional artifact-badge/DOI pledge unfinalized with the requested owner TBD. No team, host, DOI, support duration, or submitted pledge is invented.
- **C13 — partial, factual scope completed:** `\acmConference` date/location now read **August 1–5, 2027; San Jose, California**, rechecked against the [official conference home](https://kdd2027.kdd.org/). DOI/ISBN remain empty, copyright remains `none`, and CCS remains commented. `\author{Yanjie Fu}`, both affiliations, and `\shortauthors` are byte-identical to Pass 13b. No email, ORCID, coauthor, or funding was added.

**C12 — fixed for planning only:** later camera-ready preparation must allocate at most 9 content pages and 3 pages total for references plus appendix, within 12 proceedings pages. Preserve the self-contained body, locked result qualifications, essential reproducibility and Ethics; prioritize only essential supporting explanations in the small back matter. After owner authorization and actual public archival hosting, move long contrast listings and historical diagnostics to that artifact and select the minimum necessary appendix material for proceedings. No submission-stage appendix, table, figure, or result was deleted or regenerated in this pass, and no unavailable archive is treated as a substitute for the eight-page submission body.

Remaining placeholders/actions (all retained in the check-file inventory):

| Owner | Pending item | Current invocations |
|---|---|---:|
| 傅老师 | Public repository or archival URL (remote not publicly accessible) | 1 |
| 傅老师 | Whether additional representativeness evidence will be collected | 1 |
| 傅老师 | Maintainer, public host, optional artifact-badge pledge | 1 |
| Coding | Price sources/snapshot/mapping/calibration and calibrated sample price | 5 |
| Coding | v1.0 hash/final field names and episodes field names | 2 |
| Coding | T4 submission channel / external score-file interface | 1 |
| Coding | Final versioned command lines | 1 |
| Coding | v1.0 config hash | 1 |
| Coding | pytest count and attributable log path (no pass claimed) | 2 |
| Coding | T1-secondary cost/accuracy intervals | 1 |
| Coding | T3 delist / adaptive tables | 2 |
| Coding | Post-5b T4, official and supplement (future work) | 2 |

Additional owner actions without PDF placeholders: C3 cycle/submission eligibility and form-side facts; completing/publishing the artifact pack; later ACM rights/CCS metadata. No missing fact was replaced with an invented URL, DOI, license, model, price, hash, test count, result, or successful run claim.

**Build and invariants:** `latexmk -pdf -interaction=nonstopmode main.tex` from `docs/latex-sigkdd-v1.0/` and from a clean unzip in `/tmp`: **21 pages, 0 errors, 0 undefined references/citations, 0 overfull hbox/vbox**. `pdftotext -layout` confirms availability on page 3, generation/coverage on page 4, complete Ethics including its final “overstated detection performance.” sentence on **page 8**, References starting on **page 8**, and Appendix A on **page 9**. Visual checks of pages 4 and 8 confirm readable owner markers and the Ethics boundary. Nearby §4 feature/5b prose was compressed; no font-size or margin workaround was introduced. The full Result 1 and learning-rule-caveat paragraphs, scoped headline Result 1 sentences, author block, all 12 numerical `tabular` result tables, all five table-input files, and figures are unchanged. Raw `p<2×10⁻⁴`, Decision A Holm `≤0.017`, cascade's own `≤0.009`, the 8/8 scope, three-learner rule, and default-P EXP3 caveats remain intact. There are no diffs under `results/`, `release/`, either frozen protocol, or the historical `KDD_v1.0_benchmark.pdf`; pre-existing untracked results and build-bookkeeping files are left unstaged/unmodified by source edits. Existing nonfatal ACM/font-substitution warnings are not undefined citations/references.

**Documentation:** the compliance check preserves the original issue text, records all C1–C13 statuses and original-placeholder dispositions, and lists the current 20 markers. README now states current pagination, artifact limitations, metadata, entry points, bundle contents, and pending decisions; original v0.1 conversion notes are labelled historical/superseded.

**Overleaf zip:** `docs/kdd_overleaf_v1.0.zip` has exactly the same **19 compile members as Pass 13b**, each byte-identical to its repository source after rebuild. No CHECK/REQUIREMENTS/CHANGES/BRIEF Markdown, new results, build bookkeeping, or historical benchmark PDF is included. Membership:

```text
figures/fig1_five_layers.png
figures/fig2_40seller_pareto_EQ.pdf
figures/fig2_40seller_pareto_EQ.png
figures/fig2_v01scale_pareto_EQ.pdf
figures/fig2_v01scale_pareto_EQ.png
figures/fig3_40seller_E_Q_vs_pi.pdf
figures/fig3_40seller_E_Q_vs_pi.png
figures/fig3_v01scale_E_Q_vs_pi.pdf
figures/fig3_v01scale_E_Q_vs_pi.png
figures/figC_40seller_Etok_vs_pi.pdf
figures/figC_40seller_Etok_vs_pi.png
main.bbl
main.tex
refs.bib
tables/decision_a_deltas.tex
tables/decision_a_facts.tex
tables/decision_a_main.tex
tables/decision_a_lower_penalties.tex
tables/wp1_cascade.tex
```


## Pass 15 — Engineering TBD fills (2026-11-15, Asia/Shanghai)

Starting point: branch `v1.1`, HEAD `2378793`. Sole authority for values/sources: `ENGINEERING_TBD_FILL.md`, read in full before editing and left unchanged. Brief-and-implement only; no commit or push. No experiment, table generation, pytest execution/collection, or clean-environment experiment rerun was performed in this pass. Handoff collection evidence is attributed to that file.

All **17 engineering TBD invocations** were replaced as follows (line numbers are incoming Pass 14 sites, not final positions):

| # | Incoming site / item | Pass 15 fill and absence wording |
|---:|---|---|
| 1 | 179 — price sources/date/mapping | Retained “the simulator's existing price ratios, not a public-list calibration”; labelled units synthetic. Appendix B records the unused 2026-11-10 snapshot, exact YAML paths/hash, three filled provider URLs/access date, and unapplied mapping. No calibrated prices claimed. |
| 2 | 250 — calibrated sample price | Omitted the numeric value; `list_price` is a “schematic synthetic sample.” Sample caption now says synthetic/legacy and distinguishes the official board. No 0.2 calibration. |
| 3 | 254 — board fields/hash sample | Points to `results/v1.0/main/per_seed.csv` and 16-character per-run prefixes, distinct from the already-cited frozen scale file hash. No single production hash invented. The five-file description also stops attributing Q/delist fields to legacy episodes. |
| 4 | 268 — T4 submission/interface | “No public submission channel or external scoring service is recorded”; public access awaits the owner URL decision. Existing local `scripts/run_t4_eval.py` and train/test feature/label/manifest directory interface are described, with exact files/paths/options in Appendix B. Removed the unsupported submission-service completion implication. |
| 5 | 297 — body pytest count | “No official v1.0 full-suite pass log is recorded; historical snapshots exist. The handoff collected 261 tests without executing them.” Owner hosting marker untouched. No current-tree tests-passed claim. |
| 6 | 302 — coverage price mapping | “Prices are simulated, not public-list calibrated”; removed Coding marker and retained exact owner representativeness marker. |
| 7 | 429 — Limitations price mapping | “prices remain uncalibrated”; simulation scope retained. |
| 8 | 446 — Ethics price source/date/calibration | “prices are uncalibrated (the 2026-11-10 public-list snapshot was not applied; Appendix B).” Exact source path, sha256 and provider URLs are in the appendix to keep Ethics compact. All Ethics protections and final sentence retained. |
| 9 | 460 — episodes field names | Appendix A prints the exact official 3420-row `per_seed.csv` header and exact legacy `EPISODE_FIELDS`. Explicitly states there is no single official 40-seller `episodes.jsonl`; desired names are not one checked-in schema; `a` is encoded in `method`/`audit_rule`, not a CSV column. Legacy `active_attack_rate` remains and Q/delist fields are on the CSV. |
| 10 | 476 — final command lines | Appendix B includes all four official 40-seller run argv and all three Decision A/run-analysis-render recipes from fill §F. Grid argv is distinguished from the analysis recipe (no stored analysis argv) and frozen table rendering; older recipes stay separate. Removed “full experiment recipes remain pending.” No recipe was executed. Cache-backed timing is not a clean-room measurement; official inference argv is not stored. |
| 11 | 511 — production config_hash | Renamed row “Per-run config_hash”: “No single production hash.” Values are 16-character SHA-256 prefixes of per-run config JSON, not the frozen scale file hash already in the table. Appendix gives exact serialization semantics and the verified PILOT example, not a universal hash. |
| 12 | 513 — repro pytest evidence | No official v1.0 full-suite pass log; historical snapshot paths `results/benchmark/pytest_after_draft.txt` and `results/v1.1/wp1_impl_validation/pytest_final.log` only. Handoff collect-only inventory is 261 tests in 13 files, not executed; pinned runner `pytest==9.2.0`. No single frozen official pass count is asserted. |
| 13 | 598 — T1-secondary 95% CIs | “defined but not reported in this manuscript”; intervals absent from official `results/v1.0/main/inference.json`. Means exist in `summary.md`/`per_seed.csv`, without official intervals here. No CI invented or borrowed from Decision A. |
| 14 | 737 — T3-delist | “defined but not reported in this manuscript (no official v1.0 40-seller T3-delist table exists in this checkout).” No legacy readout substituted. |
| 15 | 739 — T3-adaptive | “defined but not reported in this manuscript (no official v1.0 40-seller T3-adaptive table exists in this checkout).” No legacy readout substituted. |
| 16 | 742 — official post-5b T4 | Future work, defined but not reported: “not implemented; no post-5b export or evaluation exists in this checkout.” No completed second release implied. |
| 17 | 762 — supplemental post-5b T4 | Same explicit future/not-implemented/no-export-or-evaluation status; current supplemental results unchanged. |

**Decision A environment honesty:** Appendix B explicitly says its `run_meta` records no Python/package versions. Requirements/pyproject are the stated source for `requires-python >=3.13`, `tokenmarket` 0.2.0 and core pins; Python 3.13.5 (CPython, GCC 14.2.0), `/workspace/tmvenv` are attributed to the documented v0.1 environment, never to official Decision A metadata. No undocumented inference command, public T4 service, hash, interval, price or pass record was invented. T4 JSON bootstrap records (D3 2000, per-run recompute 10000, PILOT 2000) are identified as JSON records without argv.

**Remaining invocations: exactly 3 owner TBDs**, byte-identical to incoming payloads (macro definition excluded):

1. `傅老师: public repository or archival URL (this checkout's GitHub remote is not publicly accessible)`
2. `傅老师: maintainer, public host, optional artifact-badge pledge`
3. `傅老师: whether additional representativeness evidence will be collected`

**Build and pagination:** `latexmk -pdf -interaction=nonstopmode main.tex` from `docs/latex-sigkdd-v1.0/`, and the same command from a clean unzip in `/tmp/kdd-pass15-clean-t1ug9_tq`: both **22 pages, 0 errors, 0 undefined references/citations, 0 overfull hbox/vbox**. `pdftotext -layout` independently confirms the complete Ethics statement, including final “overstated detection performance.” sentence, on **page 8**, References starting on **page 8**, Appendix A on **page 9**. Appendix expansion accounts for the extra total page. Long Decision A command hashes wrap with local listing continuation indentation disabled; no font-size/margin change was made. Existing nonfatal ACM/font warnings remain.

**Invariants:** author/affiliation/shortauthors block and exact three owner payloads compare equal to starting HEAD. The entire Benchmark Protocol through results sections (including Result 1) compare byte-for-byte; all numerical `tabular` blocks and five `tables/*.tex` inputs are unchanged. Locked default-P EXP3 wording, 8/8 scope, pre-run three-learner rule, raw `p<2\times10^{-4}`, Decision A Holm ≤0.017, and cascade family's own ≤0.009 are preserved. Figures, `results/`, `release/`, both named protocols, `ENGINEERING_TBD_FILL.md`, and `KDD_v1.0_benchmark.pdf` have no changes. Submission cycle/front matter are untouched. No outside project was accessed, no other CLI job was interrupted, and pre-existing untracked results/build bookkeeping remain unadded (build bookkeeping restored to incoming contents after compilation).

**Documentation:** README updated to Pass 15, 22 pages and “3 owner TBDs remain,” with engineering absence statuses and recipe/environment provenance. Check file adds the short Pass 15 update and exact current three-marker list; all original issue text and Pass 14 disposition rows are preserved, with the old inventory labelled historical. Earlier CHANGES entries are unchanged.

**Overleaf zip:** rebuilt `docs/kdd_overleaf_v1.0.zip` with exactly the same **19 compile members as Pass 14**, verified byte-identical to repository sources after source and clean builds. No CHECK/REQUIREMENTS/CHANGES/BRIEF/ENGINEERING Markdown, PDF build output, bookkeeping, or results paths were added. Exact membership:

```text
figures/fig1_five_layers.png
figures/fig2_40seller_pareto_EQ.pdf
figures/fig2_40seller_pareto_EQ.png
figures/fig2_v01scale_pareto_EQ.pdf
figures/fig2_v01scale_pareto_EQ.png
figures/fig3_40seller_E_Q_vs_pi.pdf
figures/fig3_40seller_E_Q_vs_pi.png
figures/fig3_v01scale_E_Q_vs_pi.pdf
figures/fig3_v01scale_E_Q_vs_pi.png
figures/figC_40seller_Etok_vs_pi.pdf
figures/figC_40seller_Etok_vs_pi.png
main.bbl
main.tex
refs.bib
tables/decision_a_deltas.tex
tables/decision_a_facts.tex
tables/decision_a_main.tex
tables/decision_a_lower_penalties.tex
tables/wp1_cascade.tex
```
