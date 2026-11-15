# Codex Round A — KDD 2027 D&B compliance review ONLY (no paper edits)

You are reviewing the Cross-Border Reasoning-Token Market KDD paper for submission to the **KDD 2027 Datasets and Benchmarks Track (first / August cycle)**.

Work only in `/workspace/token-market` (already this repo; branch `v1.1`, HEAD should be `2616240`). Do **not** edit `main.tex`, tables, figures, results, release, protocols, the Overleaf zip, or any other paper/source file in this round. The only file you should create/overwrite is:

`docs/latex-sigkdd-v1.0/KDD2027_DB_CHECK.md`

## Authority for requirements

Read in full, then treat as the official checklist:

`docs/latex-sigkdd-v1.0/KDD2027_DB_REQUIREMENTS.md`

That file was written from the official KDD 2027 D&B CFP (retrieved 2026-11-15, Asia/Shanghai):

- https://kdd2027.kdd.org/datasets-and-benchmarks-track-call-for-papers/
- https://kdd2027.kdd.org/
- https://kdd2027.kdd.org/frequently-asked-questions/

Use **KDD 2027**, not 2026. Do not invent extra desk-reject rules that are not in the requirements file or the CFP. You MAY also apply typical D&B reviewer criteria (dataset/benchmark value, documentation, accessibility & license, maintenance, reproducibility, baselines, limitations, claim scope), but mark those as reviewer-expectation items, not automatic CFP desk-rejects, unless the CFP actually says so.

## Paper to review

- LaTeX root: `docs/latex-sigkdd-v1.0/main.tex`
- Tables: `docs/latex-sigkdd-v1.0/tables/`
- Figures: `docs/latex-sigkdd-v1.0/figures/`
- Bib: `docs/latex-sigkdd-v1.0/refs.bib`
- Change log (for context only): `docs/latex-sigkdd-v1.0/CHANGES_v1.0.md`
- Built PDF (Pass 13b): `docs/latex-sigkdd-v1.0/main.pdf` (21 pages; body + Ethics end on p.8; this already meets the submission 8-content-page + unlimited appendix rule, but you must still check that the first 8 pages are self-contained).
- Official results (read-only): `results/v1.1/v1.2_decision_a_eval/`
- Do not modify `results/`, `release/`, or any frozen protocol.

Read the paper (main.tex + inputs + relevant appendix) carefully. Check PDF page breaks if useful (`pdftotext -layout`). Confirm page 8 ending, whether first 8 pages can stand alone for a reviewer who does not read the appendix, whether GitHub/release/license/access instructions are actually in those 8 pages, ethics, synthetic representativeness, TBDs, claim scope, etc.

## Hard constraints (for the comments' proposed fixes; you are not applying them yet)

- Do **NOT** propose changing any numbers or table values, or touching `results/`, `release/`, or the frozen protocol.
- Do **NOT** propose broadening claims. Claims stay limited to the simulator setting, default parameters, 1000 rounds, three learning rules; Result 1 wording stays as reviewed (Pass 13/13b).
- Author line: standing project policy is that author lines stay `Draft` unless anonymization is required; the D&B track is **single-blind**, so anonymization is **not** required, and names may be listed. The current PDF has `\author{Yanjie Fu}` with University of Macau / 橫琴澳門大學高等研究院 affiliations. **Do not propose silently changing the author line either to Draft or to additional real names/emails/ORCIDs.** If you comment on it, mark it as a 傅老师 decision and keep the proposed fix as "leave unchanged pending 傅老师".
- Keep p-value conventions: `p<2×10⁻⁴`, Holm `≤0.017` (and the cascade family's own bound as already written).
- Do not invent facts, URLs, DOIs, licenses, model names, price sources, config hashes, or test counts. If something required by the CFP is missing and cannot be filled from the repo as it stands, the proposed fix is a clearly marked TBD or a 傅老师/Coding decision, not a fabricated value.
- Existing `\TBD{...}` placeholders (Coding / T1-secondary / T3 / T4-5b, etc.) should be inventoried. Do not pretend they are filled.

## Output format for `docs/latex-sigkdd-v1.0/KDD2027_DB_CHECK.md`

Write in English (Chinese quotes of existing paper wording are fine if needed). Structure:

1. Header: paper path, commit `2616240` (Pass 13b), CFP source/year (KDD 2027 first cycle), date of this review (2026-11-15, Asia/Shanghai).
2. Short verdict paragraph (compliance risk + D&B review risk).
3. Numbered comments. Each comment MUST have:
   - ID (C1, C2, …)
   - Severity: **P0** = must-fix for CFP compliance / realistic desk-reject risk; **P1** = should-fix before submission (reviewer / CFP content criteria that will hurt badly if left); **P2** = nice-to-have
   - Location: section, approx. line in `main.tex` or table file, and PDF page if known
   - Issue: what is wrong or missing, citing the CFP/requirements clause
   - Proposed fix: concrete, implementable in the next round, without new experiments or invented facts. If it cannot be fixed in text alone, say so and mark TBD / needs 傅老师 or Coding.
   - Status: `open` (this is a review-only round)

Group or order by severity (P0 first, then P1, then P2).

Be specific and evidence-based. Do not flood the list with nitpicks, but do not miss real CFP gaps, especially:

- 8-page self-containedness (artifact access, licenses, how to run, main results, ethics, limitations/scope, synthetic representativeness) for a reviewer who skips the appendix
- Accessibility without personal requests; open-source code; documented licenses; a GitHub/archival URL in the PDF (highly recommended; no post-deadline hyperlinks in rebuttal)
- Documentation / metadata / generation & curation
- Synthetic-data representativeness quantification + utility (explicit CFP requirement for generators/environments)
- Ethics / fairness / misuse
- Maintenance / hosting / DOI pledge (submission-form vs PDF)
- Camera-ready 9+3 page crunch (flag, not a submission P0)
- CCS / acmConference TBD / copyright (do not treat missing ISBN/DOI/CCS as desk-reject unless you can show the CFP requires them now; still may be P2 or a later rights-form item)
- Claim scope already locked by Review (do not reopen Result 1)
- Visible red `\TBD{}` in the main 8 pages (reviewers will see them; judge severity honestly)

Also include a short "cannot fix without new data / 傅老师 decision" list at the end, and a recommended implementation order for Round B.

Do not commit, push, rebuild the zip, or edit the paper in this round.
