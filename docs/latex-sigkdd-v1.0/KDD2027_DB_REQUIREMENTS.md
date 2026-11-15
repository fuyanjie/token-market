# KDD 2027 Datasets and Benchmarks Track — submission requirements

Retrieved: 2026-11-15 (Asia/Shanghai).

**Official source used: KDD 2027 (first / August cycle), not KDD 2026.** The 2027 Datasets and Benchmarks Track CFP is published and is the authority for this check. KDD 2026 was consulted only as background and is not used to override 2027 text.

## Source URLs

- Primary CFP: https://kdd2027.kdd.org/datasets-and-benchmarks-track-call-for-papers/
- Conference home (dates/location): https://kdd2027.kdd.org/
- FAQs: https://kdd2027.kdd.org/frequently-asked-questions/
- OpenReview (KDD 2027): https://openreview.net/group?id=KDD.org/2027
- The CFP links submissions to “KDD 2027 Datasets and Benchmarks Track (Cycle 1) | OpenReview” (exact forum URL should be taken from the live CFP at submission time).
- Track chairs: KDD27-benchmark-chairs@acm.org — Yan Liu (USC), Sayan Ranu (Indian Institute of Technology Delhi), Evgeniy Gabrilovich (Microsoft).

Related ACM policies named by the CFP (not KDD-specific page limits):

- ACM authorship policy, including generative-AI disclosure: https://www.acm.org/publications/policies/new-acm-policy-on-authorship
- ACM Publications Policy on Research Involving Human Participants and Subjects: https://www.acm.org/publications/policies/research-involving-human-participants-and-subjects
- ACM Conflict of Interest Policy: https://www.acm.org/publications/policies/conflict-of-interest
- ACM Code of Ethics and Professional Conduct: https://www.acm.org/code-of-ethics
- ACM Open / APC (2027 subsidized rates are stated on the CFP): https://www.acm.org/publications/openaccess

## Venue and cycle

- Conference: KDD 2027, San Jose, California, August 1–5, 2027 (dates from the conference home page; the D&B CFP page itself lists the city but had a blank “from , in San Jose” date string when retrieved).
- KDD has two submission cycles per year. This CFP is for the **first (August) cycle**.
- A paper may be submitted to only one of the KDD tracks. The D&B CFP names three tracks in the “one of the three” sentence (Research, Applied Data Science, Datasets and Benchmarks). The conference home also lists an AI for Sciences track; track choice is a submission-form decision, not something this paper should invent.

### First-cycle dates (AoE)

- Abstract deadline: July 19, 2026
- Paper deadline: July 26, 2026
- Author rebuttal: September 29–October 13, 2026
- Notification: November 14, 2026

Deadlines are strict; no extensions. Placeholder or dummy abstracts are forbidden and are grounds for desk rejection.

## Anonymity / review model

- **Single-blind.** Author names and affiliations **should be listed**.
- This is different from the Research track, which is double-blind.
- Submissions are not made public on OpenReview during reviewing.
- For accepted papers, the authors agree that the original submission, reviews, meta-reviews, and discussions will be made public in OpenReview.

Implication for this draft: anonymization is **not** required. Do not strip names for D&B compliance. Do not invent additional authors, emails, ORCIDs, or funding. Any change to the current author line is a decision for 傅老师, not a silent edit.

## Formatting (submission)

- Language: English.
- Format: double-column ACM template (also available in Overleaf).
- Recommended LaTeX class: `\documentclass[sigconf,review]{acmart}`
- One PDF file.
- **Main paper: exactly the first 8 content pages must contain the paper body.** References and an optional Appendix follow and have **no page limit at submission**.
- The first 8 pages must be **self-contained**; reviewers are not required to read past that.
- The Appendix may hold reproducibility details, proofs, pseudo-code, etc.
- Submissions that do not follow these guidelines, or that do not view or print properly, will be desk-rejected.

### Camera-ready (accepted papers; not the current deadline, but constrains later cuts)

- Same maximum proceedings length for all accepted papers: **12 pages, of which up to 9 are content pages**.
- That is one extra content page versus submission, and **references + Appendix combined are limited to 3 pages**.
- Camera-ready must meet ACM camera-ready format, identify authors, and acknowledge funding that directly supported the work.
- Implication: a long submission appendix is legal now, but would have to be cut hard after acceptance.

## OpenReview / authorship / process (desk-reject risks; mostly form-side)

- Every listed author must have an up-to-date, **complete** OpenReview profile (incomplete profiles are sufficient ground for desk rejection). Mandatory fields: current and past institutional affiliation (at least 5 years), homepage, DBLP (if prior publication), ORCID, Advisors, and Recent Publications (if any). Other fields (Google Scholar, LinkedIn, Semantic Scholar, Advisees, Other Relations) should be entered where applicable.
- New OpenReview profiles without an institutional email can take up to two weeks to moderate; the deadline will not be extended.
- ACM authorship policy applies. Every named author must have contributed substantially and must take responsibility for the entire content.
- **Generative AI use must be disclosed and elaborated in the submission form.**
- Author list and order must be finalized by the submission deadline; after that, only spelling or new affiliation may change.
- **Maximum two D&B submissions per author per cycle.** Further papers (by submission id) are desk-rejected.
- Papers rejected in the last cycle of the KDD D&B track are not eligible for submission. FAQs also state that a manuscript cannot be submitted twice to the same KDD 2027 track, and only “Resubmit” (not “Reject”) August-cycle papers may go to the February cycle.
- Serving as reviewer: every submission must nominate at least one qualified reviewer (authors with at least three papers in KDD or related conferences); otherwise nominate the best-qualified author. Authors on two or more papers may be drafted as reviewers. Failure to provide a qualified reviewer when one exists, or failure to review properly, is grounds for desk rejection of all coauthored submissions.
- Withdrawal: OpenReview withdrawal button until the end of rebuttal; later withdrawal needs PC Chairs. Withdrawal after reviews are revealed triggers a 12-month waiting period before resubmission to KDD.

These process items are not all fixable in the PDF; flag them as submission-form / 傅老师 actions where relevant.

## Scope and submission categories

The track wants novel datasets, new benchmarks, or tools/methodologies for dataset creation, curation, and evaluation, including open-source libraries and tools.

Welcomed categories (a paper may fit more than one):

1. **New Datasets.** Original datasets, or thoughtfully designed collections based on previously available data, that fill gaps or offer unique characteristics. Original datasets should ideally come with some empirical evaluation proving the value of the data. Collections of previously available data should be submitted only if they provide bona fide new value not attainable from the original data (e.g., new human annotations).
2. **Benchmarks and Benchmarking Tools.** New benchmarks, evaluation methodologies or frameworks, and tools for benchmarking across datasets or domains.
3. **Data Generators and Environments.** Tools, libraries, or platforms that create synthetic data or offer new training environments. **Synthetic data must be accompanied with a quantification and a discussion of its representativeness, in addition to proving its utility.**
4. **Advanced Data Collection and Curation Practices.**
5. **Responsible Dataset Development.** Frameworks or methodologies for auditing datasets, identifying significant biases, and developing datasets responsibly.

This paper is primarily a simulator / generator + benchmark protocol (categories 2 and 3). The synthetic-data representativeness requirement is therefore first-class.

## Official evaluation criteria (reviewers will use these)

Reviewed with the same rigor as the other tracks, tailored to datasets and benchmarks:

- **Accessibility.** Datasets should be easily accessible to the research community **without requiring personal requests**. Associated code or tools **must be open source and well-documented**.
- **Quality and Documentation.** Clear, detailed descriptions of how data was collected, curated, and organized. Documentation should include metadata, data collection methods, and any preprocessing steps.
- **Impact.** Potential to advance research by addressing gaps, enabling new studies, or enhancing reproducibility and generalizability. Submissions should clearly outline how they can influence future work.
- **Ethics and Fairness.** If applicable, submissions must address ethical considerations, including data privacy, consent, bias, and potential misuse.

The CFP does **not** mandate a formal “Datasheet for Datasets” or NeurIPS-style checklist by name. Those remain useful reviewer expectations, but missing a separately titled datasheet is not, by itself, a stated desk-reject rule. Documentation, accessibility, licensing, and ethics content still need to appear in the self-contained first 8 pages or be clearly pointed from them.

Area chairs also consider: technical merit, originality, potential impact, quality of execution, quality of presentation, related work, **reproducibility of results**, and ethics.

## Ethics

- Authors are encouraged to include a section on the ethical use of data and/or informed consent of research subjects, when appropriate.
- Authors are subject to all ACM Publications Policies, including the policy on research involving human participants and subjects.
- IRB approval, when obtained, may not be sufficient; the PC may still raise ethics concerns.
- This work uses a synthetic market plus cached model outputs and standard public math-task subsets, not human-subject marketplace logs. An ethics / synthetic-data statement is still appropriate (privacy, consent, bias, misuse, and the CFP’s synthetic-data representativeness requirement).

## Reproducibility, hosting, licensing, artifacts

- In the submission, authors **may refer to a GitHub repository**. This is **not strictly required, but highly recommended**.
- After the submission deadline there is **no further opportunity to share this with reviewers**; rebuttals and discussions **will not allow hyperlinks**. Any review-time URL must already be in the submitted PDF (and preferably an archival / immutable pointer).
- **Upon acceptance, authors are required to make their code and data publicly available.**
- ACM “Artifacts Available” badge: release code, dataset, or similar in a publicly available **archival** repository that provides a **DOI**, then apply for the badge.
- Two badge rounds: (1) at submission, authors can **pledge** to make artifacts available upon publication (revealed to reviewers; reneging may retract acceptance); (2) after acceptance, authors who did not pledge may still apply.
- An artifact evaluation committee will check artifacts of accepted papers for availability and relatedness.
- The CFP does not name a required license, but accessibility + “must be open source” for associated code/tools implies a clear, standard OSS license for code and a clear data license, documented in the paper, with artifacts reachable without a personal request.

## Typical D&B reviewer expectations (not all are explicit CFP desk-reject rules)

Use these when writing the review comments, and mark severity honestly:

- Clear statement of what is released (generator, schema, boards, caches, scripts) versus what is not yet public.
- Working public URL or a candid TBD if the archival host/DOI/license text is not yet finalized.
- License, maintenance plan, and long-term hosting.
- Documentation of collection/generation, preprocessing, splits, intended uses, and limitations.
- For synthetic / simulated data: representativeness relative to the claimed real-world setting, and evidence of utility (this **is** in the CFP).
- Baselines, evaluation protocol frozen before results, leakage controls, uncertainty, and multiple seeds.
- Limitations and claim scope that do not overgeneralize beyond the simulator.
- Ethics, dual-use / misuse, and bias.

## What this requirements file does not invent

- ACM ISBN, DOI, copyright form, and CCS concept XML are not specified in the CFP as fill-in-now fields; they are typically completed from the ACM rights form / CCS tool and should not be fabricated.
- Word-template wording appears on some related CFPs; the 2027 D&B CFP text retrieved here specifies the LaTeX `sigconf,review` class and does not discuss Word in the formatting paragraph that was captured.

## Key compliance checklist for the PDF

Submission desk-reject / formatting:

1. English, ACM `acmart` `sigconf,review`, double column, prints/views correctly.
2. Main-paper body occupies at most 8 content pages; references and appendix may follow.
3. First 8 pages are self-contained (core contribution, release description, how to access artifacts, main results, ethics if applicable, limitations / scope).
4. Single-blind: names and affiliations are allowed and expected; do not anonymize for this track.
5. No concurrent / previously published archival submission (process, not text).

Content the CFP and reviewers will look for:

6. Open-source, well-documented code/tools; datasets accessible without personal requests; GitHub or other URL in the PDF if one exists (highly recommended).
7. Documentation of how data/benchmark artifacts were generated, curated, organized; metadata; preprocessing; feature/label separation if relevant.
8. For this synthetic generator: quantification and discussion of representativeness, plus evidence of utility.
9. Ethics and fairness discussion where applicable (privacy, consent, bias, misuse).
10. Impact / how others can use the benchmark, stated without broadening empirical claims beyond the frozen protocol.

Camera-ready later (flag, do not treat as a current page-limit violation): 9 content + 3 pages of references and appendix (12 total).
