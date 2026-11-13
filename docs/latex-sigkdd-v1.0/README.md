# SIGKDD D&B LaTeX — v1.0 text-edit copy (see CHANGES_v1.0.md; supersedes the v0.1 notes below)

This is a format-only conversion of `docs/BENCHMARK_PAPER_DRAFT_v0.1.md` (the source of record, which was not edited) into ACM `acmart` / `sigconf`.
- Scientific claims, numbers, metric names, and contribution wording are unchanged.
- The venue line now names the SIGKDD Datasets & Benchmarks Track.
- §6.1 columns were reordered, as described below.

## Files
- `main.tex` is the paper. It uses `\documentclass[sigconf,review]{acmart}`, which is single-blind, so author names stay visible.
- `refs.bib` is a copy of `docs/refs.bib` with the same keys. The only change is in the line-2 comment, where `[@key]` became `[at-key]`, because BibTeX treats `@` as the start of an entry, even inside a comment.
- `figures/fig1_five_layers.png` and `figures/fig2_pi_star_crossover.png` are used in the paper. The `.svg` copies are included for reference only.
- `main.pdf` is the compiled output.

## Compile
```bash
latexmk -pdf main.tex        # pdflatex + bibtex (ACM-Reference-Format.bst)
# or: pdflatex main && bibtex main && pdflatex main && pdflatex main
```
- Requires TeX Live with `acmart` (v2.21 was tested) and `CJK`/`CJKutf8` with the `bsmi` (arphic) font, which renders the affiliation 橫琴澳門大學高等研究院.
- Also requires `xurl`, `makecell`, `tabularx`, `listings`, and `newunicodechar`.

## Overleaf
1. Choose New Project → Upload Project and upload a zip of this folder (`main.tex`, `refs.bib`, `figures/`).
2. Set the compiler to pdfLaTeX and the main document to `main.tex`. Overleaf's TeX Live already ships `acmart` and `CJK`.
3. Optionally, start from the official "ACM Conference Proceedings Primary Article Template" and replace its `.tex`/`.bib`.

## Class switches
- Submission (current): `[sigconf,review]`. The D&B Track is single-blind, so do **not** add `anonymous`.
- Camera-ready: `[sigconf]`. The camera-ready limit is 12 pages total: up to 9 content pages, plus references and appendix up to 3 pages combined.

## Page budget (submission)
- The compiled PDF is 21 pages in total (Pass 13 build).
- The main body (§1–§8 plus the Ethics statement) ends on **page 8**, within the 8-content-page limit.
- References start on page 8. Appendices follow on pages 9–21.
- Repository and file paths, the one-click commands, and the reproducibility table now live only in Appendix B, "Reproducibility and Artifact Paths" (lettered C before the companion appendix was removed on 2026-11-10). It merges the former §4.3 listing, the former §6.5 one-pager, the layer code map, and the source-path table.

## TODOs (not invented on purpose)
- **CCS concepts:** generate them at https://dl.acm.org/ccs. There is a placeholder comment after the abstract.
- **Conference metadata:** `\acmConference` dates and venue are set to `TBD`. `\acmYear`, DOI, ISBN, and rights (`\setcopyright{none}`) still need to come from the KDD rights form.
- **Author details:** no ORCID or email was added. Please verify the `\country` fields ("Macau SAR, China" and "China").
- **Keywords:** derived from the abstract. Please review them.
- **`refs.bib` notes:** the TODOs and internal notes for `li2026stageroute`, `iosco2009surveillance`, and `aws2024compute_sla` were moved into `%` comments above each entry, so they no longer print. Keys are unchanged.
- **`\nocite`:** `bester2001strategic` and `cumming2019capital` are not cited in the text. They are `\nocite`'d so that the reference list matches the draft's key map.

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
