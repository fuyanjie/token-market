# License notes (confirmed by owner 2026-11-10, for v1.0)

This file records the license decisions the owner confirmed on 2026-11-10
for the v1.0 release. It does not itself grant or change any license. `LICENSES/DATA_LICENSES.md`
is left untouched (it only documents the MIT-licensed GSM8K / MATH-500 sources).

## Code

The repository code is offered under the MIT License in the top-level `LICENSE`
file (copyright holder: Yanjie Fu, year 2026).

## Data export (confirmed: CC BY 4.0)

The publishable five-file JSONL export (`sellers`, `buyers`, `orders`,
`audits`, `labels` / episodes) and the derived benchmark boards are released
under **CC BY 4.0** (https://creativecommons.org/licenses/by/4.0/), starting
with v1.0. `release/v0.1` is frozen and is not relicensed retroactively.

## Qwen cached-output redistribution (confirmed: released with v1.0)

Reproduction of the v0.1 boards uses an on-disk cache of model generations:

- Path: `cache/llm_outputs.jsonl` (copied into `release/v0.1.1-supplement/cache/`
  in the staging supplement).
- Models recorded in the cache (125 lines each, 250 lines total):
  - `Qwen/Qwen2.5-0.5B-Instruct`
  - `Qwen/Qwen2.5-1.5B-Instruct`
- The cache stores `raw_text` (model output), parsed answers, correctness
  flags, and token counts for the 80-task synthetic pool and a GSM8K / MATH-500
  long-task subset. No model weights are included.

**License name is not stated anywhere in this repository** (no model card,
LICENSE, or attribution file for Qwen is vendored here). Official Hugging Face
model cards / LICENSE files for both checkpoints name the **Apache License 2.0**:

- https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct/blob/main/LICENSE
- https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/blob/main/LICENSE

The owner confirmed on 2026-11-10 that the cached generations (`raw_text` and
derived fields) ship with the v1.0 release pack, under CC BY 4.0 for our
derived fields, with attribution to the Qwen2.5 checkpoints (Apache-2.0)
above. The v1.0 staging directory is `release/v1.0/`; the old
`release/v0.1.1-supplement/` is superseded and kept only for history.
