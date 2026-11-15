# Cross-Border KDD 2027 D&B manuscript

Current text: **Pass 15**, 2026-11-15 (Asia/Shanghai), starting HEAD `2378793` on `v1.1`. The 17 engineering TBDs are resolved solely from [ENGINEERING_TBD_FILL.md](ENGINEERING_TBD_FILL.md); **3 owner TBDs remain**. This manuscript has evolved beyond the original v0.1 format conversion. See [CHANGES_v1.0.md](CHANGES_v1.0.md), [compliance check](KDD2027_DB_CHECK.md), and [official requirements](KDD2027_DB_REQUIREMENTS.md).

## Current status and files

- `main.tex`: ACM `sigconf,review`, single-blind; Yanjie Fu, both affiliations, and short author line unchanged.
- `main.pdf`: **22 pages**; the body and complete Ethics statement end on **page 8**, References start on **page 8**, Appendix A starts on **page 9**. Verified after Pass 15 source and clean-zip builds: **0 errors, 0 undefined references/citations, 0 overfull boxes**.
- §4 now contains artifact availability, intended licenses, actual checkout paths, dependency/runner/rendering entry points, and generation/coverage limits. Appendix B gives detailed, version-labelled paths and recipes. The v1.0 staging subset is not a complete public release; no public artifact URL is available. C1/C2 remain partial and C3 requires 傅老师's cycle/status decision.
- The manuscript's T4 feature contract governs; `docs/DATA_SCHEMA.md` contains legacy descriptions where they disagree. Two cached Qwen checkpoints and `sim-fast-mock` are distinguished. T3, secondary cost/accuracy intervals, and post-5b T4 are defined but not reported.
- `refs.bib` / `main.bbl`: bibliography; `tables/`: five frozen-result LaTeX inputs. Table numbers/values and locked Decision A wording/statistical conventions are unchanged.
- Figures: layer schematic PNG; PDF+PNG versions of the 40-seller and historical v0.1 Pareto / E–Q-versus-π plots, plus the 40-seller token-weighted-exposure plot. No figures were regenerated.

## Compile

From this directory:

```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

Requires TeX Live with `acmart` (v2.21 in this checkout), CJK/CJKutf8 (`bsmi` for the existing affiliation and `gbsn` for owner TBDs), `xurl`, `makecell`, `tabularx`, `listings`, and `newunicodechar`. Experiments, table generators, and pytest were not run in Pass 15. The handoff reports 261 collected tests, not an executed suite; no official v1.0 full-suite pass log is recorded. Existing font-substitution / ACM metadata warnings are not undefined references or citations.

## Overleaf bundle

Upload `docs/kdd_overleaf_v1.0.zip`, choose pdfLaTeX, and set `main.tex` as the main document. It contains the same **19 compile members as Pass 14**: `main.tex`, `main.bbl`, `refs.bib`, five `tables/*.tex` inputs, and eleven figure files. Every member is byte-identical to the repository source. CHECK, REQUIREMENTS, CHANGES, BRIEF, and other Markdown files are excluded. A clean unzip was compiled with the command above.

## Pending decisions

The check file preserves the original 22-placeholder inventory and Pass 14 dispositions. **3 owner TBDs remain**: public repository/archive URL; maintainer/public host/optional artifact-badge pledge; whether to collect additional representativeness evidence.

Appendix B now gives the official 40-seller and Decision A recipes, per-run hash semantics, local T4 interface, and documented environment provenance. Prices remain synthetic and uncalibrated; the 2026-11-10 public-list snapshot was not applied. No single production config hash, public T4 service, official full-suite pass log, official T1-secondary intervals, official 40-seller T3 tables, or implemented post-5b T4 result is claimed. Decision A metadata records no Python/package versions.

Venue date/location now follow the [official KDD 2027 home](https://kdd2027.kdd.org/): August 1–5, 2027, San Jose, California. DOI/ISBN remain empty, copyright remains `none`, and CCS remains commented out; no author details or funding were added. Submission/cycle eligibility is an owner decision recorded outside the PDF; no target cycle was silently changed.

Submission keeps the full appendix. Later camera-ready preparation must fit **12 total pages**, up to **9 content pages**, with references plus appendix at most **3 pages**; Pass 14 CHANGES records the allocation plan only.

## Historical v0.1 conversion notes (superseded)

The notes below preserve the old conversion history, labels, line numbers, and pending-marker plans. They do not describe the current metric contract, results, page count, artifact status, or outstanding work; use the current manuscript and Pass 15 checklist above.

## §6.1 table change (team decision)
- The column order is now `active_attack_rate`, `fraud_share`, learned q (side), and J (secondary) last.
- The `active_attack_rate` values come from `release/v0.1/results/benchmark/production/T2_episodes.jsonl` at π=1, L=0, seeds {0,1,2}:

| Policy | `active_attack_rate` |
|---|---|
| StageRoute | 0.023±0.022 |
| PILOT | 0.045±0.011 |
| D3 | 0.101±0.023 (also matches `T1_episodes.jsonl`) |

- These values are identical to `fraud_share`.
- The §6.1 "Reading" sentence is kept verbatim and marked `% TODO: wording pending Review ruling`.

## Pending edits after unfreeze
v0.1 was unfrozen by 傅老师 on 2026-11-10 (going to v1.0). Two groups are done (✅); the rest are comment markers only and wait for the v1.0 protocol. "Lcomment → Ltext" refers to `main.tex` as built: the comment sits on the first line and the text it marks follows.

**✅ (0) §6.1 Reading wording (Review ruling, 2026-11-10). DONE 2026-11-10.** The Reading paragraph (L358) now reads: "At π=1, on the primary column `fraud_share` the bandits are lower (StageRoute 0.023, PILOT 0.045, D3 0.101) because they avoid attackers; D3 leads only on the side column learned q (about 0.08 vs. 0.77–0.95 for the bandits)." The range is 0.77–0.95 rather than the ruled 0.80–0.95 because Table 5 lists StageRoute learned q_theft = 0.77. The ruling comment is removed. The old "Primary board therefore favors D3" sentence is gone, so the markers at L356/L357 now sit above text that no longer contains it. They are kept until the v1.0 pass.

**✅ (6) Companion-paper dependency. DONE 2026-11-10.** All 11 markers are resolved and removed. The main body no longer refers to a companion paper:
- Abstract: "(companion paper)" sentence → "We do not propose a new deterrence or routing method; the contribution is the generator, schema, and protocol."
- Front note "Companion paper.": deleted (the contributions list already covers it).
- §1 Scope: "…treated in a companion methods paper" → "it does not propose or claim a new deterrence or routing method, and deterrence theory is out of scope."
- §2 intro: "five nearby literatures and a companion methods paper" → "five nearby literatures".
- §2 "Positioning relative to the companion methods paper" → "Positioning": fixed-a deterrence is posed as an empirical T1 protocol question under the same metrics as every arm, and no novelty is claimed for audit design.
- §3.4: "continuity with the methods paper" → "a scalar summary of accuracy, compliance, and fraud, and T2's regime narrative".
- §7 Limitations item 8: "addressed in the companion paper" → "No deterrence-method novelty is claimed."
- §8 Conclusion: "Deterrence methods stay in the companion paper." → "Designing deterrence or audit methods that improve on this board is left to future methods work." This is the single forward-looking sentence.
- App. B "Companion methods paper" (heading and body): section removed. Appendices are now A Schema, B Reproducibility, C RQ coverage.
- App. B (Reproducibility) closing "(companion paper)" sentence: deleted.

**(1) D3 presented as the paper's method.** Planned relabel: "fixed-audit-rate baseline".
- §5 T1 Baselines: L302 → L303
- §6.1 Table 5, bold D3 row: L339 → L351
- §6.1 Reading: L357 → L358. The target sentence was already removed by (0), so only the marker is left.

**(2) π\* ∈ (0.10, 0.12) statements.** Planned rewrite to a conditional interval with per-seed spread.
- Abstract: L76 → L78
- §1 Contribution 3: L106 → L108
- §5 T2 Summary of findings: L315 → L316
- §6.2 Crossover: L392 → L394
- §6.2 Production T2: L396 → L397
- Figure 2 caption: L399 → L402
- §8 Conclusion: L475 → L477

**(3) §4.2 safe-feature list.** Planned move of `tokens_actual`, `audits.hit/miss/label_correct/fraud_realized`, `slash_amount`, and `delist_rounds` to the label columns.
- L270 → L271

**(4) "D3 insensitive to π" sentences.** Planned deletion.
- Abstract: L77 → L78
- §5 T2 Goal: L310 → L311
- §6.2 Crossover: L393 → L394
- Figure 2 caption: L401 → L402

**(5) Primary metric redefinition (15 markers).** Marker: `% TODO(pending unfreeze): primary metric redefinition`.
- Abstract: L74 → L75
- §1 Contribution 3: L107 → L108
- §3.4: L196 → L197
- §5 T1 Primary metrics: L297 → L298
- §5 T1 fraud_share formula: L299 → L300
- §5 T1 Reading rule: L305 → L306
- §6.1 Table 5: L340 → L341
- §6.1 Reading: L356 → L358. The old "second primary column" clause was removed by (0).
- §6.1 Production export: L360 → L361
- Figure 2 caption: L400 → L402
- §7 Limitations item 8: L467 → L468
- §8 Conclusion: L476 → L477
- App. A minimal row: L501
- App. C (RQ coverage) intro: L601
- App. C RQ table: L603 → L604
