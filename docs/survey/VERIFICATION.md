# Reference verification (independent check, 2026-11-10, Asia/Shanghai)

Claude Code drafted the survey and bibliography but could not web-check citations in-session (WebSearch/WebFetch/curl were permission-blocked). An independent check was then performed on this box.

## Methods
- DOI / Crossref: `https://doi.org/<doi>` with CSL-JSON content negotiation.
- arXiv: `https://export.arxiv.org/api/query?id_list=...` (HTTPS). Title token overlap required ≥ 0.5 against the bib title.
- Official legal texts: HTTP 200 fetch of EUR-Lex CELEX pages and CAC full-text pages, confirming the instrument title appears in the HTML.
- Additional web-search spot-checks (title, authors, year, venue/arXiv id) for 10+ works, including the 2025 papers most at risk of being invented.

## Result
- **77 entries** in `survey_refs.bib` after adding the independently verified StageRoute paper (`li2026stageroute`, arXiv:2506.17254; also ICLR 2026).
- **77 / 77 verified.** None removed.
- Year notes (venue year vs arXiv first-posting year) were left as venue/publication years where the bib already recorded a later publication year. These are not mismatches of identity.
- `roberts2021chinese`: Crossref issued date 2020 (online), bib year 2021 (journal volume). Kept 2021; identity confirmed by DOI `10.1007/s00146-020-00992-2`.
- Legal-text URLs updated to pages that returned HTTP 200 in this check:
  - EU AI Act: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689
  - GDPR: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R0679
  - EU-US Data Privacy Framework decision: https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023D1795
  - China PIPL: https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm
  - China Data Security Law: https://www.cac.gov.cn/2021-06/11/c_1624994566919140.htm
  - Laffont & Tirole (1993): https://openlibrary.org/isbn/0262121743

## Web-search spot-checks (sample of 10+)
All confirmed real, with matching titles and identifiers:
1. FrugalGPT — Chen et al., arXiv:2305.05176
2. RouteLLM — Ong et al., arXiv:2406.18665 (ICLR 2025)
3. Velasco et al., “Is Your LLM Overcharging You?”, arXiv:2505.21627
4. Cai et al., “Auditing Model Substitution in LLM APIs”, arXiv:2504.04715
5. Gao, Liang, Guestrin, “Model Equality Testing”, arXiv:2410.20247 (ICLR 2025)
6. Backlund & Timbers, Vending-Bench, arXiv:2502.15840
7. Ong et al., TOPLOC, arXiv:2501.16007
8. Li & Li, StageRoute, arXiv:2506.17254 (ICLR 2026)
9. China PIPL (2021) — official CAC full text
10. China Data Security Law (2021) — official CAC full text

Remaining entries were verified via DOI or the arXiv API (titles matched).

## Review checklist pass (2026-11-10, Asia/Shanghai)
Each item checked against Crossref (DOI), PMLR, ACL Anthology DOI, arXiv API, ICLR proceedings, the authors' pages, and official CAC pages; see the parent report for per-item outcomes. New @misc pricing sources: Anthropic Claude pricing page and OpenAI "Reasoning models" guide (accessed 2026-11-10). For page fit, redundant `url` fields were dropped where a DOI or arXiv eprint is already printed.
