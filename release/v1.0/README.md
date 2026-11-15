# v1.0 staging scaffold — 2026-11-15

**Staging remains staging.** This directory is not self-contained and is not a public release. Existing `MANIFEST` / `MANIFEST.json` describe the historical staged subset and were not rewritten. The new SHA256 manifest is explicitly of repository-relative paths, not an inventory claiming those files have been copied into this directory.

Present staging: prior reproduction/license notes and task notices; cache and cache manifest; older dense-π outputs; older production T2 episodes. New scaffolding: this README, NOTICE, LICENSE_TBD, component matrix, artifact map pointer and repository-path checksums. The repository's `docs/v1.1/db/` now contains versioned data dictionaries, data card, task/cache and T4 construction details, statistics/metric interpretation, coverage matrix, portable environment inventory, three-level reproduction instructions and dated validation evidence.

A complete package will need the corresponding source snapshot, frozen protocols and inherited configs, data/cache, per-seed boards for every reported experiment, analysis/rendering scripts, T4 exports and joinable transaction logs, paper assets, dependency inventory and checksums with a table/figure map. Those inputs remain at the repository paths in [ARTIFACT_MAP.md](ARTIFACT_MAP.md); this pass did not copy them or regenerate experiments. Some producing argv, source revisions and environment records are not recorded; the map and reproduction guide distinguish those gaps from reconstructed recipes.

Project's own code/data license: **TBD (傅老师 to choose/confirm)**. Factually, the current top-level repository LICENSE is MIT, and `docs/LICENSE_NOTES.md` records a 2026-11-10 owner note of CC BY 4.0 for derived data. No final choice is asserted here. [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) preserves separate upstream terms and flags unverified provenance. A final package must include owner-approved project license text and applicable upstream licenses/notices; `LICENSE_TBD.md` is not a substitute license grant.

Access: **TBD (傅老师): public repository or archival URL**.
Maintenance: **TBD (傅老师): maintainer / public host / DOI / badge pledge**.
No hosting, publication, DOI or badge commitment was made in this pass.

From repository root, verify the final repository-path inventory with `sha256sum -c release/v1.0/SHA256SUMS`. See `docs/v1.1/db/REPRODUCE_v1.md` for L1 smoke checks, L2 frozen-output verification/re-rendering, and unexecuted L3 full regeneration recipes. The new environment evidence is validated 2026-11-15, not the historical Decision A environment.
