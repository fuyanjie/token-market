# Codex Round B — implement KDD 2027 D&B P0/P1 fixes (Pass 14)

You are editing the Cross-Border KDD paper in `/workspace/token-market` (branch `v1.1`, starting HEAD `2616240`, Pass 13b). Follow the review in `docs/latex-sigkdd-v1.0/KDD2027_DB_CHECK.md` and the official requirements in `docs/latex-sigkdd-v1.0/KDD2027_DB_REQUIREMENTS.md`.

## Goal

Implement **all P0 and P1 items that can be done without new experiments or invented facts**. Items that need new data, a real public URL/DOI/license that does not already exist, or 傅老师's decision: leave as clearly marked `\TBD{...}` (or an explicit pending sentence) and list them in CHANGES and in the check file.

Also do the factual, low-risk parts of P2 C13 (venue date/location only). Do **not** cut the appendix for camera-ready (C12 is planning only; record a one-paragraph plan in CHANGES, not a submission-stage deletion).

After edits: rebuild the PDF with 0 errors and 0 undefined refs/citations; keep the **main text + Ethics within the first 8 content pages** (Ethics, including its final sentence, must still end on page 8; References may start on page 8). Then update the check-file statuses, write a Pass 14 entry in `CHANGES_v1.0.md`, update `docs/latex-sigkdd-v1.0/README.md` if it states page/status facts, and rebuild `docs/kdd_overleaf_v1.0.zip`.

You may edit paper/docs listed below. You may **not** modify `results/`, `release/`, frozen protocols (`docs/PROTOCOL_v1.0.md`, `docs/v1.1/PROTOCOL_v1.2.md`), table *values*, or any official readout. Do not run new experiments, regenerate Decision A tables unless a caption/wording-only generator change is required (values must stay identical), or force-push / commit / push (the parent agent will commit).

## Hard constraints

- Do not change any numbers or table values.
- Do not broaden claims. Claims stay limited to the simulator setting, default parameters, 1000 rounds, three learning rules. **Result 1 wording stays as reviewed in Pass 13/13b**, including “Under EXP3 at default $P=0.25$”, 8/8 scope, pre-run three-learner rule, p-value conventions (`p<2\times10^{-4}`, Holm `≤0.017`; cascade family’s own `≤0.009`).
- **Author line: leave `\author{Yanjie Fu}` and affiliations / `\shortauthors` unchanged.** Do not switch to Draft, and do not add emails, ORCIDs, coauthors, or funding.
- Do not invent facts, URLs, DOIs, licenses, model names, price sources, config hashes, pytest counts, or commands you have not verified against this checkout.
- Space is tight: adding paragraphs in the body requires compressing nearby prose, not spilling onto page 9. Do not drop locked result qualifications, ethics’ existing protections, or the self-contained main results.

## Verified facts you MAY use (re-check if you rely on them)

These were independently verified in this checkout on 2026-11-15. Use them; do not go beyond them.

1. **Public URL.** `git remote` is `https://github.com/fuyanjie/token-market.git`, but an unauthenticated HTTP GET of that GitHub URL returns **404** (`logged_in=no`). It is **not** a publicly accessible artifact URL. **Do not print this URL in the paper as if reviewers could download the data without a request.** In §4 (within the first 8 pages) add a compact availability paragraph that: (a) states intended licenses (see fact 5); (b) states that a public repository / archival copy will be provided and is not yet publicly downloadable without request; (c) uses `\TBD{傅老师: public repository or archival URL (this checkout's GitHub remote is not publicly accessible)}`; (d) points to in-repo paths that actually exist, honestly labelled; (e) points to Appendix B for detailed recipes. That is the honest C1 fix; C1 remains partly TBD until 傅老师 publishes a URL.

2. **`release/v1.0/` is a staging pack, not a complete public release.** `release/v1.0/MANIFEST.json` has `"staging": true` and `"not_a_release": true`. Present files: `REPRODUCE.md`, `LICENSE_NOTES.md`, `LICENSES/DATA_LICENSES.md`, `cache/llm_outputs.jsonl` + `CACHE_MANIFEST.json`, and some `results/pi_dense/` plus `results/benchmark/production/T2_episodes.jsonl`. It does **not** contain a top-level `LICENSE`, `requirements.txt`, a data card, or `release/v1.0/exports/production/*`. Appendix B currently over-claims (“self-contained… LICENSE, requirements.txt, a data card… and all v1.0 results”; “Production board & `release/v1.0/exports/production/…`”). Correct this language. Do **not** invent or copy files into `release/`. The five-file JSONL boards that exist in this checkout are `exports/production/` and `release/v0.1/exports/production/` (3-seller / 9 seller-rows, not the 40-seller main table). Decision A materials live under `results/v1.1/v1.2_decision_a_eval/` (already cited). Be precise about what is where.

3. **Cached models.** `release/v1.0/cache/CACHE_MANIFEST.json` and the cache file record **250** lines: only `Qwen/Qwen2.5-0.5B-Instruct` and `Qwen/Qwen2.5-1.5B-Instruct` (125 each). `configs/v1.0/frozen/scale.yaml` also includes `sim-fast-mock` with `backend: mock`, weight 0.25, plus the two Qwen models (`local_hf`, weights 0.5 and 0.25). There is **no third cached real LLM** in this checkout. Replace “at least three models (Qwen… and TBD third cached model)” with the two named Qwen cached checkpoints plus the `sim-fast-mock` mock backend used in the frozen scale config. Do not invent another checkpoint or license. You may drop the third-model `\TBD` once the text is truthful.

4. **Licenses (owner-confirmed 2026-11-10, `docs/LICENSE_NOTES.md` and `release/v1.0/LICENSE_NOTES.md`).** Code: MIT, top-level `LICENSE`, copyright Yanjie Fu 2026. Five-file export, derived boards, and derived cache fields: CC BY 4.0, starting v1.0. Qwen2.5 cached generations: attributed, checkpoints Apache-2.0 (HF LICENSE URLs are recorded in LICENSE_NOTES; do not claim a vendored Qwen LICENSE file if it is not in the pack). GSM8K and MATH-500 subsets: MIT, notices in `LICENSES/DATA_LICENSES.md` and `release/v1.0/LICENSES/DATA_LICENSES.md`. Frozen `release/v0.1` is not relicensed. Keep these names; fix pack-local path claims that do not match the staging directory.

5. **Baselines.** `docs/BASELINES_v1.0.md` documents market-setting adaptations for PILOT and StageRoute, and states that reproducing the original published numbers is not possible in this repository without RouterBench / the original inputs; the gap is one of setting, not of the isolated algorithmic unit checks. Replace the unfilled “reproduction-or-gap” `\TBD` with this documented qualification. Do not add original-paper numeric claims from that file if the file itself says they must be checked against a PDF. Keep baseline labels and all result numbers unchanged. Soften “faithful reimplementations” to a wording that includes these adaptations, without touching Result 1.

6. **Schema mismatch.** `docs/DATA_SCHEMA.md` still treats `active_attack_rate` + `fraud_share` as primary and lists some audit/`tokens_actual` fields as example “safe” features. The manuscript’s T4 whitelist/blacklist (§4.2, Table of labels) is authoritative for the reviewed task. The paper already says `active_attack_rate` is removed (same formula as `fraud_share`). Add a short pointer that the manuscript’s feature contract governs T4, and that parts of `docs/DATA_SCHEMA.md` are legacy where they disagree. Do not rewrite the schema file in this pass unless a one-line warning at the top is clearly helpful and does not touch `release/`. Prefer fixing the paper’s pointer.

7. **Leakage-check script path (exists):** `scripts/check_t4_leakage.py`. You may fill that TBD only if you confirm the script is the leakage check described. Do not invent T4 “submission channel” or config hashes or pytest counts — leave those `\TBD{Coding: ...}` if still unverified.

8. **Existing one-click commands in Appendix B** (`scripts/export_benchmark_layers.py --full --use-cache --out exports/production`, `scripts/run_benchmark_tasks.py --full --use-cache`, `scripts/reproduce_pi_dense.sh --full`) exist as scripts, but they are **not** the 40-seller / 1000-round / Decision A path. Do not imply they regenerate Table 5 / official Decision A. Decision A table *rendering* is `python3 scripts/pass12_decision_a_tables.py` from frozen eval files (already stated). Keep that distinction.

9. **Venue metadata (C13, factual only).** Official conference home: KDD 2027, San Jose, California, August 1–5, 2027. You may fill `\acmConference` date/location from these official facts (so running headers stop saying “TBD, TBD”). Leave DOI, ISBN, copyright (`none`), and CCS empty/commented — do not invent them. Do not change the author line.

10. **Cycle eligibility (C3).** First-cycle abstract/paper deadlines were July 19/26, 2026 (AoE); this review is 2026-11-15, after the listed notification date. **Do not put deadline/eligibility discussion into the PDF.** Record in CHANGES and the check file: this is a **傅老师 decision** (already submitted vs internal readiness vs later cycle). Do not silently retarget the paper to KDD 2026 or to a February cycle.

11. **Maintenance / DOI / badge (C11).** No public host or DOI exists. Add at most one candid sentence that long-term public hosting, a named maintainer, and any Artifacts Available / DOI pledge are not yet finalized, with `\TBD{傅老师: maintainer, public host, optional artifact-badge pledge}`. Do not invent a maintenance team or Zenodo DOI.

## Per-comment implementation guidance

- **C1 P0 (partial):** availability paragraph in §4 as in fact 1; honest paths; no fake public URL. Status: `partial` (text fixed; public URL TBD).
- **C2 P0 (partial):** add a compact, explicitly bounded representativeness discussion in the first 8 pages using already documented facts only: 40-seller roster (31 honest / 9 strategic: 3 swap / 3 theft / 3 downgrade) as already stated; task pool / cache coverage (80-task synthetic pool and the GSM8K / MATH-500 long-task subset documented in LICENSE notes and REPRODUCE.md — re-verify counts before quoting); two cached Qwen models + mock backend; simulated prices, not public-list calibrated; CN/SG/BR tags are simplified devices, not real legal regimes; strategic learning and audit/feedback are simulated. Distinguish **workload coverage inside the simulator** from **external representativeness vs real markets**. State clearly that no quantitative comparison to production cross-border inference markets is available. That honest disclosure is required; it does **not** fully discharge the CFP’s “quantification of representativeness” if no external reference exists — leave a `\TBD{傅老师: whether additional representativeness evidence will be collected}` and mark C2 `partial`. Do not add new numbers, calibrations, or datasets. Do not broaden Result 1.
- **C3 P0:** PDF unchanged on this point. Status `tbd-owner`.
- **C4 P1:** rewrite over-claims about `release/v1.0/` as in fact 2 (body + Appendix B + any abstract/contribution sentence that asserts a completed downloadable reference pack). Status: `partial` or `fixed` for the wording; remaining public pack is TBD.
- **C5 P1:** two Qwen caches + mock; licenses as in facts 3–4. Status `fixed` if wording is truthful; no third-model TBD needed.
- **C6 P1:** put a minimal, accurate entry-point + “appendix for recipes” sentence in the first 8 pages; correct Appendix B so commands are not over-sold as reproducing Decision A / 40-seller official tables. Fill only verified script paths (including leakage script if confirmed). Leave unverified command/hash/pytest TBDs. Status `partial`.
- **C7 P1:** short generation/curation lineage in §4 (synthetic pool + GSM8K/MATH-500 subset construction as documented; cache vs mock; marketplace mechanism simulated). Schema-legacy pointer. Add the already-stated T4 resampling exception to §6’s fixed-roster opening if that opening currently omits it. Status `fixed` if done from existing docs only.
- **C8 P1:** inventory all 22 `\TBD`s. Fill only from verified facts (third model, possibly leakage script, baseline gap). For prices, config hash, pytest, T4 submission channel, episodes field names if still unknown: keep `\TBD{Coding: ...}` but make surrounding sentences say “not yet published / not claimed as complete” rather than “tests passed” / “reference release” if those claims are unsupported. Describe T3 tables, T1-secondary cost/accuracy, and post-5b T4 as **defined but not reported in this manuscript** (do not invent tables or numbers). Planned 5b simulator change should read as future work, not a completed second T4 release. Status `partial`.
- **C9 P1:** baseline qualification as in fact 5. Status `fixed`.
- **C10 P1:** concise ethics/limitations additions: jurisdiction tags are scenario controls, not measured country-level fraud rates; math-only/reused tasks, two cached models + mock, and uncalibrated prices limit transfer; classifiers may learn simulator shortcuts; scores must not support real seller sanctions or national-risk rankings; no real marketplace participant logs; GSM8K/MATH-500 are public MIT-licensed task subsets (not human-subject market data). Do not invent an IRB determination; if none is documented, do not claim one. Status `fixed` for the text that can be written; IRB/consent screening remains TBD only if you would otherwise have to invent it (better: state no human-subject market logs are used, and do not mention IRB unless documented).
- **C11 P1:** short TBD sentence as in fact 11. Status `partial`/`tbd-owner`.
- **C12 P2:** CHANGES-only planning note. No appendix deletion.
- **C13 P2:** venue date/location only, as in fact 9.

## Files you should update

- `docs/latex-sigkdd-v1.0/main.tex` (primary)
- `docs/latex-sigkdd-v1.0/KDD2027_DB_CHECK.md`: set each comment **Status** to `fixed`, `partial`, or `tbd-owner`/`tbd-coding` with a one-line what-changed / what-remains note. Do not delete the original issue text.
- `docs/latex-sigkdd-v1.0/CHANGES_v1.0.md`: append a **Pass 14** section dated 2026-11-15, Asia/Shanghai, listing each C# action, remaining TBDs, build result (page count, where Ethics ends, error counts), and zip membership.
- `docs/latex-sigkdd-v1.0/README.md` if it states page counts or release status.
- Rebuild `docs/kdd_overleaf_v1.0.zip` with the **same 19 compile members as Pass 13b** (figures used by main.tex, `main.tex`, `main.bbl`, `refs.bib`, the five `tables/*.tex`). Do not add the CHECK/REQUIREMENTS/CHANGES/BRIEF markdown files to the zip. Members must be byte-identical to the repo sources after the edit/rebuild.
- Latex build artifacts already tracked (`main.pdf`, `.aux`, `.bbl`, `.log`, etc.) may be updated by the build. Do not add untracked `main.fdb_latexmk` / `main.fls` or any `results/` paths. Do not edit `KDD_v1.0_benchmark.pdf` unless you intentionally refresh it; prefer leaving that historical file alone.

## Build and verify

From `docs/latex-sigkdd-v1.0/`:

```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

Confirm: 0 errors, 0 undefined references/citations, body+Ethics end on page 8 (pdftotext), Result 1 wording and p-value conventions unchanged, author line unchanged, no new invented URLs/numbers, no `results/` or `release/` diffs. If page 8 overflows, compress (do not drop locked claims) and rebuild until it fits.

Do not `git commit` or `git push`.
