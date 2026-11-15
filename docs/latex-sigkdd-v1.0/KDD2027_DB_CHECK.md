# KDD 2027 Datasets and Benchmarks — Round A compliance review

- **Paper:** `docs/latex-sigkdd-v1.0/main.tex`, its five table inputs, figures, `refs.bib`, and the existing `main.pdf`.
- **Reviewed checkout:** branch `v1.1`, commit **`2616240` (Pass 13b)**; full HEAD `2616240fc69307f853da4fb1c20991f9bb7fbf63`.
- **Target:** **KDD 2027 Datasets and Benchmarks Track, first / August cycle**, single-blind.
- **Review date:** **2026-11-15, Asia/Shanghai**.
- **Checklist authority:** [KDD2027_DB_REQUIREMENTS.md](KDD2027_DB_REQUIREMENTS.md), read in full. Clause names below refer to that file. Official sources checked: [2027 D&B CFP](https://kdd2027.kdd.org/datasets-and-benchmarks-track-call-for-papers/), [conference home](https://kdd2027.kdd.org/), and [FAQs](https://kdd2027.kdd.org/frequently-asked-questions/). No KDD 2026 requirements are substituted.
- **Original Round A scope (historical):** review only. Proposed changes below are for a subsequent authorized round; no paper, table, figure, result, release, frozen protocol, or zip was changed. Public hosting and submission-form facts cannot be certified from this checkout.

## Pass 15 engineering fill update (2026-11-15, Asia/Shanghai)

Starting HEAD `2378793`, branch `v1.1`. Sole authority: [ENGINEERING_TBD_FILL.md](ENGINEERING_TBD_FILL.md), read in full. All **17 engineering TBDs** are resolved with verified values or explicit absence/current-status wording; **3 owner TBDs remain**. Prices are uncalibrated (snapshot not applied); the official board is `per_seed.csv` with per-run prefixes; T4 has a local evaluator/export interface but no recorded public service. No official full-suite pass, secondary CIs, official 40-seller T3 tables, post-5b implementation/results, or Decision A environment record is claimed. Recipes and source-qualified environment details are in Appendix B. No experiment, test suite, or table generator was executed; no commit/push was made.

Source and clean-zip builds: **22 pages, 0 errors, 0 undefined references/citations, 0 overfull boxes**. Ethics, including its final sentence, ends on **page 8**; References begin on **page 8**. The zip has exactly the same **19 compile members as Pass 14**, byte-identical to repository sources. Original issue text, original-placeholder inventory, and Pass 14 disposition table below are preserved as historical records; their engineering-pending counts are superseded by this update. Owner access/representativeness/hosting decisions remain open; this is not a compliance sign-off.

### Current Pass 15 placeholders (3 owner TBDs remain)

| Current source line | Exact placeholder payload |
|---:|---|
| 221 | `傅老师: public repository or archival URL (this checkout's GitHub remote is not publicly accessible)` |
| 297 | `傅老师: maintainer, public host, optional artifact-badge pledge` |
| 302 | `傅老师: whether additional representativeness evidence will be collected` |

## Pass 14 implementation update (2026-11-15, Asia/Shanghai)

Text-only P0/P1 fixes are implemented; this is still **not a compliance sign-off**. C1/C2 remain partial, C3 is an owner process decision, and a complete public pack, hosting/maintenance, operational details, and unreported results remain pending. The unauthenticated 404 was independently verified in this checkout on 2026-11-15 as supplied to Round B; the GitHub remote is not printed as a reviewer download URL. A repeat shell request in this sandbox returned no HTTP response, so it does not establish any change in accessibility. No experiments or table generators were run. Results, release directories, frozen protocols, table numbers, and Result 1 are unchanged.

Source and clean-bundle builds: **21 pages, 0 errors, 0 undefined references/citations, 0 overfull boxes**. The complete Ethics statement ends on **page 8**; References start on **page 8** and Appendix A on **page 9**. The Overleaf zip retains exactly the same **19 compile members**, byte-identical to the edited/rebuilt sources. See [Pass 14 changes](CHANGES_v1.0.md) for actions, evidence, pending work, and the camera-ready plan.

## Original Round A verdict (historical)

**Not ready for a compliance sign-off.** The 21-page PDF meets the submission page allocation: the body and complete Ethics statement end on page 8, references begin on page 8, and the appendix begins on page 9. However, the first eight pages are not yet self-contained for artifact access/use, and the generator lacks the explicitly required quantification of representativeness. D&B review risk is also high: the claimed reference release is marked as staging, cache provenance conflicts with the main text, linked documentation contradicts the feature whitelist, and visible placeholders leave promised capabilities unresolved. The main results, simulation scope, limitations, and ethics statement are already present within eight pages; Result 1 is not reopened. Separately, first-cycle eligibility is a process gate because the published submission deadline predates this review.

**Severity interpretation:** P0 means a must-fix CFP compliance issue or a conditional process blocker, not a prediction that every such omission automatically causes desk rejection. P1 means a serious official evaluation-criterion or reviewer-expectation issue. P2 means a later-stage or optional improvement. Missing GitHub, DOI, CCS, or a separately titled datasheet is not independently declared an automatic desk-reject rule.

## Original Round A verified boundaries and existing strengths (historical)

Read-only checks used source inspection, `pdfinfo`, `pdftotext -layout`, PDF link inspection, and targeted repository comparisons. No experiments, builds, table generators, or tests were run.

| Item | Evidence / outcome |
|---|---|
| Format and identity | English, double-column `acmart`, `sigconf,review` at `main.tex:16`. The PDF displays Yanjie Fu and both supplied affiliations. Single-blind does not require anonymization. |
| Page boundary | A2 Table 7, the remaining Limitations, Conclusion, and the entire Ethics statement are on p.8. Ethics ends with “detection performance.” References follow on p.8; Appendix A starts on p.9. No body spill beyond p.8 was found. |
| Main results within eight pages | T1 Table 5 and its result/caveat on pp.5–6; T2 Table 6 / Figure 2 on p.7 and interpretation on p.6; T4's official non-reporting and qualified PILOT supplement on p.6; A2 interpretation on pp.6–7 and Table 7 on p.8. A reviewer need not read the appendix to learn the principal outcomes. |
| Scope and statistical conventions | `main.tex:318,348–352,433` retain simulator/default-parameter/1000-round/three-rule scope, the pre-run direction rule, EXP3 caveats, and below-break-even qualification. Decision A tables retain raw `p<2×10⁻⁴` and zero-Holm bound `≤0.017`; cascade retains its separate `≤0.009` bound. Preserve all of these. |
| Official result provenance | SHA256 sidecars match the inspected Decision A readout and `cells.csv`, `contrasts.csv`, and `direction_consistency.csv`. The latter records 8 result-1 hits for each router. This is a provenance check, not a new statistical analysis. |
| Artifact content in the main eight pages | File roles, join keys, feature/label rules, named licenses, and simulation/cache distinctions are present on pp.3–5. Thus licenses and documentation are not wholly absent; the gaps concern completeness, consistency, access, and operational instructions. |
| URLs in the PDF | External links inspected are bibliography sources on p.8. No project GitHub, artifact archive, or downloadable release URL was found anywhere in the PDF. Local paths are not public download addresses. |
| Placeholders | **22** explicit `\TBD{...}` invocations: **11** on pp.1–8 and 11 in the appendix. None are in the five table-input files. Literal venue `TBD` fields are additional and counted separately below. |

## Numbered comments — P0

### C1 — First-eight-page artifact access and use are incomplete

- **Severity:** **P0** — first-eight-page self-containedness; the absent GitHub link alone is not an automatic rejection rule.
- **Location:** §4.1, §4.2 “How to submit,” §4.4, `main.tex:222,269,298`, PDF pp.3–4; Appendix B, `main.tex:466–512`, pp.9–10.
- **Issue:** Requirements **Formatting (submission)** / **Key compliance checklist 3** require a self-contained first eight pages. **Accessibility** and **Reproducibility, hosting, licensing, artifacts** also matter. The reader gets `release/v1.0/` without a repository address, no install/run entry point in the body, an appendix-only command pointer, and a TBD submission channel. The repository remote identifies `https://github.com/fuyanjie/token-market.git`, but that address is absent from the PDF. The attempted public web fetch was inconclusive, so this review does not assert that the repository is either public or private. Licenses already appear in §4.3; the operational handoff is what is missing. Appendix reproduction details may legally remain in the appendix.
- **Proposed fix:** Add a compact availability/reproduction paragraph within §4, containing the owner-verified public repository/archive address, reviewed version, exact accessible artifact subset, existing license names, dependency-document path, and a verified entry command for the supported benchmark version. Keep detailed recipes in Appendix B. Check download/read access without a personal request. Use the discovered remote only after Coding verifies public access and appropriate contents; otherwise retain **TBD — Coding/傅老师: public artifact endpoint** in the working draft and keep this issue open. Do not invent a DOI, publish the staging pack, or assume a rebuttal can introduce a missing link: the CFP disallows hyperlinks there. Coordinate with C4 and C6 so the new paragraph does not advertise nonexistent files or the wrong experiment.
- **Status:** `partial` — Pass 14: §4 now states intended licenses, actual checkout paths, pending public access, and Appendix B recipes; owner URL remains TBD (the independently checked remote is not public).

### C2 — Synthetic representativeness is discussed qualitatively but not quantified

- **Severity:** **P0** — explicit generator/environment content requirement; not a separately enumerated automatic desk-reject trigger.
- **Location:** §3.2, §4.5, §6 opening/T1, §7(3),(5),(6), Ethics; `main.tex:178–184,303,341–348,430–433,447`; PDF pp.2–8.
- **Issue:** Requirements **Scope and submission categories, category 3** expressly require quantification and discussion of representativeness in addition to utility. The manuscript supplies simulator scale and useful controlled comparisons, but no quantitative argument about what target workload/market the synthetic data represents. Counts of sellers, seeds, repeated tasks, and policy outcomes are not by themselves evidence of real-market representativeness. Prices remain uncalibrated, jurisdictions are simplified, and latency/theft are acknowledged simulation shortcuts. Existing utility evidence does not fill this separate requirement.
- **Proposed fix:** Add a compact, explicitly bounded representativeness discussion in the first eight pages. Reuse already documented workload composition, task-pool reuse, roster/attack composition, feedback assumptions, and cached-versus-mock provenance, with their existing values unchanged and sources identified. Explain the coverage and exclusions those facts support; distinguish workload coverage from external validation. State that prices/corridors and strategic behavior are not empirically calibrated to production markets. **TBD — 傅老师/Coding:** determine whether existing repository evidence can support the required quantitative representativeness argument. If a defensible target/reference distribution or comparison is absent, text-only disclosure cannot manufacture it or close this item. Do not run a new calibration, add a new dataset, change parameters/results, or broaden Result 1 in Round B; obtain a separate decision about the unresolved evidence requirement.
- **Status:** `partial` — Pass 14: §4 distinguishes roster/pool/cache/mock workload coverage from external representativeness and discloses no production-market quantitative comparison; owner decision on additional evidence remains TBD.

### C3 — First-cycle chronology and submission-side eligibility require confirmation

- **Severity:** **P0, conditional process gate** — not an observed author/profile violation.
- **Location:** Target/cycle decision; `main.tex:19–25,74–83` and PDF p.1 for identification. Most checks belong to OpenReview, not to a PDF line.
- **Issue:** Requirements **First-cycle dates**, **OpenReview / authorship / process**, and the **FAQs** apply. The first-cycle abstract/paper deadlines are July 19/26, 2026, with notification listed as November 14, 2026; this review is dated November 15. A new first-cycle submission cannot be made timely by editing the draft now. No submission receipt/status, complete author profiles, nomination, or eligibility history was supplied. Missing evidence in this checkout is not proof those requirements were violated. Incomplete profiles, excess submissions, and reviewer-duty failures have stated desk-reject consequences; mandatory generative-AI disclosure is form-side.
- **Proposed fix:** **傅老师 decision:** establish whether this is an already-submitted paper, accepted-paper preparation, or an internal readiness review of an expired target. Do not silently switch to KDD 2026 or a later cycle, and do not imply that Round B edits retroactively repair the submitted PDF. Verify the existing submission record and applicable status. Check complete OpenReview profiles (including mandatory profile ORCID and affiliation history), final author list/order, per-author cycle limits, track exclusivity/concurrent-publication and rejection/resubmission/withdrawal history, COIs, qualified-reviewer nomination/duties, and generative-AI disclosure in the form. Do not fabricate those facts or add them as claims to the paper. **Author line: leave unchanged pending 傅老师**; the displayed names/affiliations fit single-blind review, and absent PDF email/ORCID is not established here as a CFP violation.
- **Status:** `tbd-owner` — Pass 14: No PDF eligibility discussion or retargeting; July 19/26, 2026 AoE deadlines and November 14 notification precede this review; 傅老师 must identify already-submitted vs internal readiness vs a later-cycle decision and verify form-side facts.

## Numbered comments — P1

### C4 — The claimed downloadable, self-contained reference release is not the pack in this checkout

- **Severity:** **P1** — official accessibility/documentation/reproducibility criteria and a serious artifact-readiness risk; immediate public release at submission is not invented as an independent automatic desk-reject rule.
- **Location:** Abstract/contribution 2, §4.1, Conclusion, Appendix B; `main.tex:88,114,222,441,466,487–490,507`; PDF pp.1,3,8–10.
- **Issue:** Requirements **Accessibility**, **Quality and Documentation**, and **Reproducibility, hosting, licensing, artifacts** require a truthful artifact description and public code/data upon acceptance. `release/v1.0/REPRODUCE.md` calls itself a staging supplement, says it is not a public release, and instructs against publication. Its `MANIFEST.json` has `staging: true` and `not_a_release: true`; the text manifest still names `release/v0.1.1-supplement/`. The inspected pack lacks the advertised `LICENSE`, `requirements.txt`, data card, `exports/production/`, and main/T4 result directories; its existing result subset is older pi_dense/T2 material. Appendix B's “self-contained” and “all v1.0 results” statements are therefore unsupported by this directory. Top-level files/results existing elsewhere do not make this pack self-contained.
- **Proposed fix:** In the paper, distinguish existing repository code/results, the actual staging subset, and the promised future public artifact. Replace unsupported present-tense pack-completeness assertions with a precise availability/status statement, retaining every experimental value. Describe the separate location of Decision A materials rather than implying the v1.0 staging pack contains them. **Needs Coding/傅老师 outside text-only work:** identify an already complete, verified public artifact if one exists; otherwise a release-completion/publication task remains outstanding. Do not modify, copy into, relicense, regenerate manifests for, or publish `release/` as this review's proposed paper-only fix. A claim or pledge is not proof of a completed pack.
- **Status:** `partial` — Pass 14: Abstract, contribution, §4, conclusion, and Appendix B now describe staging honestly and separate older boards from Decision A; completed public pack/publication remains pending.

### C5 — Cached-model provenance and license coverage remain unresolved

- **Severity:** **P1** — official documentation/accessibility criteria and reviewer confidence in the synthetic/real boundary.
- **Location:** §4.3, §4.5, §7(3), Appendix B; `main.tex:293,303,430,466,507`; PDF pp.4,7,9–10.
- **Issue:** Requirements **Quality and Documentation**, **Licenses/artifacts**, and generator representativeness apply. §4.5 claims real cached outputs of “at least three models,” while the release cache and its manifest identify only the named Qwen checkpoints. The frozen scale config also contains a `sim-fast-mock` backend (`configs/v1.0/frozen/scale.yaml:37–44`); that is not evidence of another cached real model. The main text has unresolved third-model and license placeholders. MIT/CC BY 4.0 are already stated, and `docs/LICENSE_NOTES.md` records the owner's choices and upstream attribution links; this is not a finding that no licenses exist. However, a third-model rights/provenance claim cannot be inferred from them, and the pack-local notice locations claimed in Appendix B are incomplete.
- **Proposed fix:** Have Coding reconcile the actual backend/cache lineage of the frozen runs, using existing configs, run metadata, and cache manifests. Document which outputs are cached generations and which are mock, and map code, source tasks, generated text, and derived fields to their existing notices. A truthful nonnumeric provenance description using the existing backend identities is preferable to an invented third checkpoint/license; approve that wording with 傅老师/Coding without changing any experimental numbers or table values. Keep the third-model question explicitly unresolved until that reconciliation. Do not generate outputs, add a model, assume a model-weight license automatically settles every output right, or alter `release/`/protocols. Any missing redistribution evidence is **TBD — owner/Coding**, not a fabricated license.
- **Status:** `fixed` — Pass 14: Two named cached Qwen checkpoints plus sim-fast-mock are documented; existing MIT/CC BY 4.0/Apache-2.0 attribution and actual notice locations replace the third-model/license placeholders.

### C6 — The advertised one-click commands do not reproduce the current main benchmark

- **Severity:** **P1** — official reproducibility and well-documented-code criteria.
- **Location:** §4.4 and Appendix B; `main.tex:298,468–477,487–512`; PDF pp.4,9–10.
- **Issue:** Requirements **Accessibility** and **reproducibility of results** apply. Beyond being appendix-only, the listed `export_benchmark_layers.py --full` command defaults to the older production config and seeds; the task runner accepts T1–T3, not T4 (`scripts/run_benchmark_tasks.py:213–241`). These are not the current 40-seller main workflow or the separate 1000-round factorial. Appendix B includes a table-generation command, which reads results rather than reproducing runs. T4/leakage command placeholders remain despite existing `scripts/run_t4_eval.py` and `scripts/check_t4_leakage.py`. No test count or run instruction is verified merely because a script exists.
- **Proposed fix:** Replace the generic recipe with version-labelled, existing entry points: export/demo, v1.0 main/T2, official D3 T4, PILOT supplement, and v1.2 Decision A readout/table reproduction. Have Coding extract exact command/config/input/output mappings from existing run metadata and scripts, including the distinction between regenerating experiments and rendering frozen results. Put the minimal supported entry point in the first eight pages and detailed recipes in Appendix B. Mark uncertain flags, prerequisite files, hash fields, and test evidence **TBD — Coding**. Do not execute these recipes, regenerate tables, rerun experiments, write to results/releases, or invent a successful clean-environment run in Round B.
- **Status:** `partial` — Pass 14: §4 gives dependency/runner/rendering entry points and Appendix B distinguishes older recipes, current T4 evaluator and verified leakage script from Decision A rendering; full versioned recipes, hashes, score-file interface, and attributable tests remain Coding TBDs.

### C7 — Generation/curation metadata and the linked schema do not match the paper's contract

- **Severity:** **P1** — official quality/documentation criterion; leakage-control documentation is central to benchmark utility.
- **Location:** §4.1–4.2, §4.5, §6 opening, Appendix A/B; `main.tex:222–269,279–288,303,341,461,508`; PDF pp.3–5,9–10. Supporting discrepancy: `docs/DATA_SCHEMA.md:5–8,171–179,194–206`.
- **Issue:** Requirements **Quality and Documentation** require collection/generation, organization, metadata, and preprocessing descriptions. The body explains file roles and evaluation splits well, but does not sufficiently identify generation/curation lineage: task-pool construction and reuse, source subset selection, cache generation/parsing/correctness, mock sampling, and how those inputs map to each reported experiment. The linked schema still declares `active_attack_rate + fraud_share` primary, treats learned q as secondary, and lists `tokens_actual` and audit-hit/slash fields as safe features, conflicting with the manuscript's blacklist. These are substantive contradictions, not a missing formally titled datasheet. Also, §6's fixed-roster opening needs the already stated T4 resampling exception to avoid implying T4 used the fixed roster.
- **Proposed fix:** Add a short generation/curation lineage paragraph to §4 using verified existing documentation/configs; distinguish cached source pools from the pool actually used by a result and source-task preprocessing from simulated marketplace generation. Include a version-specific schema/feature-contract pointer and explicitly identify the old schema as legacy where it disagrees; the manuscript's whitelist remains authoritative for the reviewed T4 task. Add the existing resampled-roster exception to the §6 overview. Place detailed mappings of existing fields to metrics in an appendix, with unverified fields **TBD — Coding**. A trustworthy linked schema ultimately requires separately authorized documentation reconciliation; do not silently edit frozen protocols/releases or claim that reconciliation has happened. Do not change metric definitions, values, or splits.
- **Status:** `fixed` — Pass 14: §4 adds seeded/reused synthetic-pool and public subset curation lineage, cached versus mock inputs and simulated mechanisms; manuscript T4 contract overrides legacy schema conflicts; §6 adds the T4 resampling exception. Unverified board field names stay TBD.

### C8 — Visible TBDs and promised-but-unfinished capabilities make the benchmark look incomplete

- **Severity:** **P1** — presentation, execution, documentation, and reproducibility criteria; a visible TBD is not by itself a stated automatic desk-reject rule.
- **Location:** Main-body placeholders in `main.tex:133,180,251,255,269,293,298,303,430,447` (pp.2,4–5,7–8); planned 5b statements at `288,332`; appendix placeholders at `461–512,597,736–761`, pp.9–10,15–16; RQ table at `870`, p.21.
- **Issue:** Requirements **Official evaluation criteria** and first-eight-page completeness apply. The inventory below contains 22 unresolved invocations, including 11 visible main-paper placeholders. Some are missing factual evidence rather than cosmetic markers. T3 tables, post-5b T4, and secondary cost/accuracy intervals are not filled; nevertheless the abstract/task description and RQ coverage can be read as a completed T1–T4 release with two T4 simulator versions. The 5b paragraph mixes future planning with present-tense “v1.0 records them separately.” Existing T4 non-reporting and supplemental-result qualifications are appropriately candid and must stay.
- **Proposed fix:** Resolve factual placeholders only from verified existing records; otherwise replace an unsupported completed-work assertion with an explicit pending/not-reported statement and keep its unresolved owner action in the checklist. Describe T3 and post-5b T4 as defined but unevaluated/unreleased where appropriate; do not pretend to fill their tables. State that current prices use the frozen synthetic ratios and public-list calibration is future work, without adding prices or claiming calibration. Remove unsupported “tests passed” wording if no attributable existing log is available; do not invent a count. Keep a concrete pending Coding/傅老师 item for the submission interface. Do not hide missing work by changing the TBD macro's color, add experiments, change any numbers/table values, or weaken locked scope caveats.
- **Status:** `partial` — Pass 14: All 22 original placeholders are dispositioned below; unsupported completion/test claims removed; T3, secondary intervals and post-5b T4 explicitly defined but not reported; 20 current TBD invocations remain, including three new owner decisions.

### C9 — Baseline “faithfulness” needs the already documented adaptation qualifications

- **Severity:** **P1** — reviewer expectation for credible baselines, tied to official execution/reproducibility criteria; not an independent CFP desk-reject rule.
- **Location:** Abstract/contributions, Related Work, protocol baselines; `main.tex:88,116,133,315`; PDF pp.1–2,4. Supporting record: `docs/BASELINES_v1.0.md:53–81,108–135`.
- **Issue:** The paper promises unit tests “against the original settings” and a reproduction-or-gap report, but leaves the gap TBD. The existing baseline report instead describes setting adaptations and says original published-number reproduction is not possible here without additional original benchmark inputs. It records changed contexts/preferences/learning setup for PILOT and deployment/fallback/budget changes for StageRoute. Unit tests for algorithmic components do not establish reproduction of original experiments. Requirements **technical merit, quality of execution, related work, reproducibility** support raising this as a reviewer issue.
- **Proposed fix:** Replace the unfilled reproduction promise with a concise disclosure of the documented market adaptations and the absence of published-setting numerical reproduction. Point to the existing adaptation report and describe only the component checks supported there. Keep the baseline labels, results, and locked Result 1 unchanged; obtain 傅老师 approval for wording around “faithful.” Do not propose downloading new benchmark data or conducting a new replication in this round.
- **Status:** `fixed` — Pass 14: Market-adapted wording and docs/BASELINES_v1.0.md qualification replace faithful/original-setting reproduction prose; original-setting numbers are unavailable without RouterBench/original inputs; table labels and results unchanged.

### C10 — Ethics covers misuse, but bias and source-data privacy/consent need a direct treatment

- **Severity:** **P1** — official Ethics and Fairness content criterion where applicable, not a demand for a new IRB approval or new fairness experiment.
- **Location:** §4.2, §7(3),(5), Ethics; `main.tex:267–288,430–432,444–447`; PDF pp.4–5,7–8.
- **Issue:** Requirements **Ethics and Fairness** / **Ethics** identify privacy, consent, bias, and misuse. The statement already says no real transactions are used, disclaims legal advice, limits use, and warns about leakage. It does not directly address bias from math-only/reused tasks, restricted model/backend coverage, synthetic jurisdiction tags, or the possibility that classifiers learn simulator shortcuts rather than real misconduct. Nor does it explain the privacy/consent provenance of public tasks and retained generated text beyond calling them fixtures. Synthetic transaction fields alone do not establish screening or consent facts about every released text source.
- **Proposed fix:** Add concise body text explaining that jurisdiction tags are scenario controls, not measured country-level fraud tendencies; task/model/latency and pricing assumptions limit fairness and transfer; scores should not support real seller sanctions or national-risk rankings. Describe only verified source provenance and the absence of real marketplace participant logs. Identify any unverified text screening, consent/redistribution, or institutional-review determination as **TBD — 傅老师/Coding**, without asserting screening, consent, IRB approval, or an exemption. Preserve the existing misuse warning and Feature/Label safeguards. No new fairness numbers or broadened claims are needed.
- **Status:** `fixed` — Pass 14: Ethics preserves misuse/leakage safeguards and adds public MIT task/no participant-log provenance, scenario-tag limits, shortcut/transfer risks, and prohibition on real seller sanctions/national-risk rankings; no IRB or consent determination invented.

### C11 — Maintenance, archival hosting, and badge commitments are unspecified

- **Severity:** **P1** — maintenance is a reviewer expectation; public availability upon acceptance is a CFP obligation; a DOI/badge pledge is not mandatory at submission.
- **Location:** §4.1/§4.3–4.4 and Conclusion, `main.tex:222,293–298,441`; PDF pp.3–4,8; Appendix B, pp.9–10.
- **Issue:** Requirements **Reproducibility, hosting, licensing, artifacts** and **Typical D&B reviewer expectations** distinguish these obligations. There is no named hosting/maintenance plan, versioning/issue policy, or statement about whether a badge pledge has been made. Relative paths and the word “release” do not establish long-term availability. Conversely, absence of a DOI in the PDF is not currently a formatting violation or evidence that a mandatory pledge was omitted.
- **Proposed fix:** **傅老师/Coding decision:** specify an actual responsible maintainer/team, supported scope, existing issue channel, version preservation policy, and intended stable host; put a brief accurate plan in §4. Separately decide and record the optional Artifacts Available pledge in the submission form and fulfill public code/data availability upon acceptance. If pursuing the badge, arrange an archival DOI-backed deposit through an authorized later task. Leave host/DOI/maintenance commitments explicitly TBD until chosen; do not invent a DOI, support duration, maintainer identity, or say a pledge was filed. Do not publish or change the existing release in a text-edit round.
- **Status:** `partial` — Pass 14: One candid §4 sentence leaves maintainer, public host, and optional artifact-badge/DOI pledge to 傅老师; no host, DOI, team, or pledge invented.

## Numbered comments — P2

### C12 — Plan for the camera-ready reference/appendix reduction

- **Severity:** **P2** — later camera-ready constraint, not a submission page-limit failure.
- **Location:** References and Appendices A–H; `main.tex:450–879`; PDF pp.8–21, especially the large contrast tables and historical first-batch material.
- **Issue:** Requirements **Camera-ready** allow 12 proceedings pages, up to 9 content pages, with references plus appendix limited to 3 pages combined. The current unlimited submission appendix is legal, but cannot be carried wholesale into that allocation. No submission-stage cut is required just because the PDF has 21 pages.
- **Proposed fix:** Prepare a later allocation plan: keep the self-contained body, locked result qualifications, and essential reproducibility/ethics; prioritize essential supporting explanations within the allowed back matter and plan authorized archival hosting for long contrast listings and historical diagnostics. This is planning only: do not delete, compress, change, or regenerate any table/figure/result now, and do not assume an archive substitutes for the submission's self-contained body.
- **Status:** `fixed` — Pass 14: Planning-only camera-ready allocation paragraph recorded in Pass 14 CHANGES; no submission-stage appendix, table, figure, or result deletion.

### C13 — Venue/CCS/rights metadata needs a later factual cleanup

- **Severity:** **P2** — presentation and later ACM metadata; no demonstrated submission desk-reject rule for blank ISBN/DOI/CCS.
- **Location:** `main.tex:18–27,74–95`; PDF p.1 author block and running headers on pp.2–21.
- **Issue:** `\acmConference` still has literal date/location `TBD` fields, producing “KDD D&B, TBD, TBD” in running headers. CCS is commented out; DOI/ISBN are empty; copyright is `none`. Requirements **What this requirements file does not invent** explicitly prevents treating all these as required fill-in-now fields. The conference home supplies known conference identity/date/location, while rights metadata must come from the proper ACM process. These literal venue TBDs are distinct from the 22 red content placeholders.
- **Proposed fix:** After resolving the actual submission/status decision in C3, use only confirmed official KDD 2027 venue facts for the conference metadata if appropriate. Generate relevant CCS concepts with the official tool when needed. Keep DOI/ISBN/copyright fields pending the applicable rights instructions; do not fabricate them. **Author line: leave unchanged pending 傅老师**; do not replace it with Draft or add real names/emails/ORCIDs. A profile ORCID requirement does not establish a PDF ORCID requirement.
- **Status:** `partial` — Pass 14: Official KDD 2027 date/location filled (August 1–5, 2027; San Jose, California); author/affiliations/shortauthors unchanged; DOI/ISBN/copyright/CCS remain deferred as instructed.

## Original 22-placeholder inventory and Pass 14 disposition

Original line/page numbers and payloads below refer to Pass 13b and are retained for audit. The final column records the Pass 14 disposition; it does not fabricate missing evidence.

| # | Source line | PDF page | Existing placeholder payload | Follow-up | Pass 14 disposition |
|---|---:|---:|---|---|---|
| 1 | 133 | 2 | `Coding: PILOT/StageRoute reproduction gap` | C9; existing adaptation report, no new reproduction | Filled: documented market adaptations and original-input/setting gap (C9). |
| 2 | 180 | 2 | `Coding: price sources, snapshot date, and mapping` | C2/C8; calibration unestablished | Retained Coding TBD; prices explicitly simulated and uncalibrated. |
| 3 | 251 | 5 | `Coding: calibrated price` | C8; no invented sample price | Retained Coding TBD; sample caption explicitly says calibrated price pending. |
| 4 | 255 | 5 | `Coding: v1.0 hash; final field names` | C6/C7; verify exact existing artifact | Retained Coding TBD; fields/hashes not claimed final or published. |
| 5 | 269 | 4 | `Coding: T4 evaluation script and submission process` | C1/C6/C8; interface decision still needed | Verified local scripts/run_t4_eval.py; narrowed TBD to submission channel and external score-file interface. |
| 6 | 293 | 4 | `Coding: third model and its license` | C5; provenance/rights unresolved | Removed: actual two-Qwen cache, attribution and notice paths documented (C5). |
| 7 | 298 | 4 | `Coding: v1.0 pytest count` | C6/C8; no count inferred from source | Retained Coding TBD; removed unsupported tests-passed claim. |
| 8 | 303 | 4 | `Coding: third cached model` | C5; mock is not a real cache checkpoint | Removed: two cached Qwen models plus mock backend (C5). |
| 9 | 303 | 4 | `Coding: price sources and mapping` | C2/C8 | Retained Coding TBD; no calibration or external-market comparison claimed. |
| 10 | 430 | 7 | `Coding: price sources and mapping` | C2/C8 | Retained Coding TBD; limitations now include mock backend. |
| 11 | 447 | 8 | `Coding: price sources, access date, calibration` | C2/C8/C10 | Retained Coding TBD; ethics explicitly says prices uncalibrated. |
| 12 | 461 | 9 | `Coding: v1.0 episodes field names` | C7; schema reconciliation | Retained Coding TBD; legacy schema and incomplete field mapping disclosed. |
| 13 | 477 | 9 | `Coding: final v1.0 command lines` | C6 | Retained Coding TBD for final versioned run recipes; known older/current entry points distinguished; no per-seed pi_dense flag claimed. |
| 14 | 497 | 10 | `Coding: v1.0 config path` | C6; version-specific mapping | Filled: 40-seller grid is in configs/v1.0/frozen/scale.yaml, distinct from older configs/pi_dense.yaml. |
| 15 | 508 | 10 | `Coding: script path` | C6/C7; existing leakage script needs correct input mapping | Filled: scripts/check_t4_leakage.py inspected for whitelist/blacklist and label/token-correlation checks; no success claimed. |
| 16 | 510 | 10 | `Coding: v1.0 config hash` | C6; no invented hash | Retained Coding TBD; no hash invented. |
| 17 | 512 | 10 | `Coding: v1.0 pytest count and log path` | C6/C8 | Retained Coding TBD; no attributable test pass/count claimed. |
| 18 | 597 | 15 | `T1-secondary: cost and accuracy per policy, mean [95\% CI]` | C8; absent from cited official inference; leave not reported | Retained as Coding TBD; explicitly defined but not reported in this manuscript. |
| 19 | 736 | 16 | `T3-delist: table` | C8; pending, no new table/data | Retained as Coding TBD; explicitly defined but not reported in this manuscript. |
| 20 | 738 | 16 | `T3-adaptive: table` | C8; pending, no new table/data | Retained as Coding TBD; explicitly defined but not reported in this manuscript. |
| 21 | 741 | 16 | `T4-5b` | C8; official D3 post-change split remains pending | Retained as Coding TBD; future 5b change/split, defined but not reported. |
| 22 | 761 | 16 | `T4-5b` | C8; supplement post-change split remains pending | Retained as Coding TBD; future 5b split, defined but not reported. |

Original Pass 13b page totals: p.2 = 2, p.4 = 5, p.5 = 2, p.7 = 1, p.8 = 1, p.9 = 2, p.10 = 4, p.15 = 1, p.16 = 4. The macro definition at line 60 is not an invocation. Literal venue TBDs and commented venue/author/CCS TODOs are not counted as red content placeholders.

## Historical Pass 14 placeholders (20 invocations; superseded by Pass 15)

Five original placeholders were filled from evidence (baseline gap, two third-model placeholders, grid config path, leakage script); 17 original entries remain or are narrowed/renamed. Three new owner placeholders concern public URL, representativeness evidence, and maintainer/hosting/optional badge pledge. All remain visibly red; the macro only adds CJK support for 傅老师. Repeated price/test/post-5b entries count separately. The generated list below gives current source lines.

| Current source line | Placeholder payload |
|---:|---|
| 179 | `Coding: price sources, snapshot date, and mapping` |
| 221 | `傅老师: public repository or archival URL (this checkout's GitHub remote is not publicly accessible)` |
| 250 | `Coding: calibrated price` |
| 254 | `Coding: v1.0 hash; final field names` |
| 268 | `Coding: T4 submission channel and external score-file interface` |
| 297 | `Coding: v1.0 pytest count` |
| 297 | `傅老师: maintainer, public host, optional artifact-badge pledge` |
| 302 | `Coding: price sources and mapping` |
| 302 | `傅老师: whether additional representativeness evidence will be collected` |
| 429 | `Coding: price sources and mapping` |
| 446 | `Coding: price sources, access date, calibration` |
| 460 | `Coding: v1.0 episodes field names` |
| 476 | `Coding: final v1.0 command lines` |
| 511 | `Coding: v1.0 config hash` |
| 513 | `Coding: v1.0 pytest count and log path` |
| 598 | `Coding: T1-secondary cost and accuracy per policy, mean [95\% CI]` |
| 737 | `Coding: T3-delist table` |
| 739 | `Coding: T3-adaptive table` |
| 742 | `Coding: T4-5b` |
| 762 | `Coding: T4-5b` |

## Remaining work requiring new evidence / Coding / 傅老师 decision

- **Representativeness:** no text-only claim can supply an absent empirical target/reference comparison. Existing coverage facts may help, but sufficiency remains unresolved (C2). No new evidence collection is authorized here.
- **Submission status and authorship:** first-cycle status/eligibility, profile/form completion, generative-AI disclosure, reviewer nomination, and commitments need the owner's records. Author line **leave unchanged pending 傅老师** (C3/C13).
- **Artifact access and completeness:** public access, a completed downloadable pack, actual maintenance responsibility, stable hosting, and any badge/DOI pledge need verified facts and owner action. The staging release must remain untouched (C1/C4/C11).
- **Backend/license lineage resolved for this text pass (C5):** inspected manifest/cache and frozen scale config establish two named Qwen checkpoints plus mock; owner-confirmed license notes establish the stated attribution/notice paths. No third checkpoint or vendored license is claimed. Public pack completion remains C4.
- **Operational/schema facts:** exact versioned commands, field mappings, hash identifiers, leakage-check scope, scoring interface, and attributable test evidence need Coding verification from existing records (C6/C7). Printed TBDs are not evidence those tasks passed.
- **Absent results:** original-setting baseline reproduction, T1-secondary intervals, T3 tables, and post-5b T4 are not filled by this review. Disclose their status or defer the associated promise; do not run experiments or supply numerical substitutes (C8/C9).

## Original recommended implementation order for Round B (historical; Pass 14 statuses above govern)

1. **Resolve the process gate (C3)** while continuing draft preparation: establish the applicable first-cycle status without implying an expired deadline can be repaired or silently changing the target. Preserve the author line pending 傅老师.
2. **Reconcile artifact facts (C4–C7)** using existing records only. Identify the actual accessible subset, backend lineage, license notices, correct scripts/configs, and authoritative schema. Keep unresolved decisions explicit and leave results/releases/protocols untouched.
3. **Repair the first-eight-page handoff and representativeness discussion (C1/C2).** Add only verified access/use/provenance facts; clearly separate measured coverage, simulation assumptions, and missing external validation. If evidence or public access remains unavailable, keep those P0s open.
4. **Make completion status, baseline qualifications, and ethics candid (C8–C10)**; add only owner-approved maintenance/hosting commitments (C11). Resolve or explicitly scope the full TBD inventory without changing any numbers or table values and without adding experiments.
5. **Address metadata and later length planning (C12/C13).** If an authorized later paper-edit round builds a PDF, recheck that the entire body/Ethics remains within eight pages and that the new artifact paragraph is actually there. Keep all locked Result 1 wording, p-value conventions, caveats, existing tables/figures/results, and frozen protocols intact. Do not rebuild the Overleaf zip, commit, or push as part of this review.
