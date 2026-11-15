# Pass 17 validation — 2026-11-15

Scope: documentation, release scaffolding and appendix additions only. No production simulator grid or experiment/cache regeneration was executed. See `PROTECTION_AUDIT.json` for hashes compared against the pre-edit inventory, and `L2_REPORT.json` for scratch-output command status, wall times and exact comparisons.

- L1: 256 passed, five deselected in 35.14s. The five deselected golden-number cases call cache preparation on the frozen cache; no full historical suite-pass claim is made. Existing collect-only sentences were retained.
- L2: six frozen table renderings are byte-identical; main analysis curves and Q gate match parsed frozen JSON exactly; D3 per-run and PILOT T4 result/notes arrays match exactly. Five paper plots re-render successfully in /tmp; PDF binary equivalence or image tolerance is not recorded or claimed.
- Q gate: both predicates pass at all 19 π values, matching the frozen formal gate. Eligibility and front members are recorded per π. No verdict was changed.
- Build command executed from `docs/latex-sigkdd-v1.0`: `latexmk -pdf -interaction=nonstopmode main.tex`. Exit 0, no errors, **23 pages; Ethics ends on page 8**. See `latexmk_2026-11-15.log`. Warnings include float placement adjustments, ACM reference/CCS requirements, font substitution and balance; no overfull boxes were reported in the final log. Administrative metadata was outside scope.
- Body preservation: pre-appendix source is byte-identical to HEAD; every original nonblank main.tex source line is retained verbatim. Extracted PDF text of pages 1–8 is identical to the original HEAD PDF. Both owner TBD lines are unchanged. Only five appendix paragraphs were added; official tables are unchanged.
- Environment: installed metadata inventory captured; pip freeze failed because its internal build module is missing. The traceback is retained. No package repair/installation was attempted. The dated validation is not the historical Decision A environment.
- `git diff --check` passed. No git add/commit/push or network write was performed. Protected license/protocol/result/config/cache/export/source paths and existing script files remain unchanged. Frozen release/v0.1 and existing release/v1.0 MANIFESTs remain unchanged.

## Paper paragraph additions

1. Appendix A, “Versioned dictionaries.” First words: `docs/v1.1/db/SCHEMA_v1.md records field types`.
2. Appendix B, “Dated documentation supplement.” First words: `Added 2026-11-15`.
3. Appendix B, “Statistical conventions.” First words: `docs/v1.1/db/STATISTICS.md consolidates`.
4. Appendix C, “Inspectable source rows.” First words: `The raw SKU/date/input/output rows`.
5. Appendix F, “Gate audit trail.” First words: `docs/v1.1/db/Q_GATE_REPORT.json and its Markdown companion`.

## Unexecuted or unresolved subparts

L3 full regeneration is documented and deliberately unexecuted. Original producing argv/code for the 40-seller A2 standalone paired readout and several manual LaTeX conversions are not recorded; the artifact map exposes these gaps instead of inventing them. T4 re-export/leakage-check and conceptual SVG re-export recipes are reconstructed but unexecuted; frozen local T4 evaluation was executed. Complete upstream revisions, mirror-specific MATH-500 licensing, generated-text rights, and the full transitive wheel license audit remain unverified where stated in the component matrix. Project license, public access and maintenance/host/DOI/badge choices remain owner TBD. No complete distribution was assembled, no public upload made and no upstream terms replaced. The optional raw-row appendix table and optional legacy-schema pointer were unnecessary because direct paths/dictionaries were supplied.

## Discrepancies for Research

No derived result contradicting a paper number or verdict was found. Documentation distinguishes 80 pool IDs from 77 unique question texts (the paper calls it an 80-task pool, not 80 unique question strings). Cache counts are consistent with 77 short prompt hashes plus 48 long prompts per model. T4 feature-unit counts include empty target labels and therefore differ in scope from the paper's target-trading counts; they are not substituted for those counts. Q tau_a=0.6428571428571429 rounds to the paper's 0.643 and both gate predicates agree. The PDF page count changes with appendix layout, while body/Ethics pages remain unchanged.
