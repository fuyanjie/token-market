# Portable environment and dated validation

**Environment validated 2026-11-15, not the historical Decision A environment.** `ENVIRONMENT.json` records Python 3.13.5, Linux x86_64, the installed distribution versions and observed host hardware. Decision A's run metadata does not record interpreter/package versions. No historical environment is inferred from current pins.

## Portable setup

From a repository checkout with Python ≥3.13:

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q -p no:cacheprovider --basetemp=/tmp/tokenmarket-tests -k 'not test_v01_numbers_unchanged'
```

These setup commands are documented; a fresh installation was **not executed**. L1/L2 actually used the existing interpreter. The core pins suffice for cached-output analysis/tests; model generation needs the optional dependencies documented in `requirements.txt`. Never let a default-output recipe overwrite frozen results or cache.

[requirements-lock.txt](requirements-lock.txt) is a complete installed-distribution inventory (including optional/transitive packages), captured with `importlib.metadata.distributions()`. An attempted `pip freeze` failed with `ModuleNotFoundError: pip._internal.operations.build`; [pip_freeze_2026-11-15.log](pip_freeze_2026-11-15.log) retains the traceback. No pip repair or network installation was attempted. Thus the lock captures versions but is not an independently validated install plan or wheel archive. CPU torch local-version wheels may need their upstream index; platform-specific wheel availability was not tested.

## Execution evidence

[pytest_2026-11-15.log](pytest_2026-11-15.log): **256 passed, 5 deselected in 35.14s**. Command used the existing environment's Python with `PYTHONDONTWRITEBYTECODE=1`, `MPLCONFIGDIR=/tmp/pass17-mpl`, `-p no:cacheprovider`, `--basetemp=/tmp/pass17-pytest`, and `-k 'not test_v01_numbers_unchanged'`. This is a dated executed result alongside the historical collect-only inventory; it is not a full official v1.0 suite pass. The five excluded parametrizations call `sim.prepare()` with the repository cache, which can precompute and append on a cache miss. They were excluded to respect the frozen-cache constraint. Other tests use temporary outputs; no production experiments were run.

[L2_REPORT.json](L2_REPORT.json) and [l2_2026-11-15.log](l2_2026-11-15.log) record each executed frozen-output command, exit status and wall time. Table renderers were copied unmodified to a temporary directory with frozen input symlinks, preserving their inferred root but putting outputs in /tmp. Figures were re-rendered there; official figures were not replaced. Main curve/gate comparisons and T4 result comparisons use parsed exact equality, ignoring output directory provenance fields. All generated table bytes equal the existing official files.

Observed host: Intel Xeon processor, `/proc/meminfo` MemTotal 16386416 kB; this is host-visible memory, not a reserved-resource specification. CPU allocation/quota and available GPU hardware are not recorded. L2 table renderers took 0.122s / 0.027s; figure rendering 3.484s; main frozen-board analysis 5.864s; D3 T4 evaluation 9.526s; PILOT T4 evaluation 11.050s. These are this pass's measurements, not estimates of full simulation or cache regeneration.

Historical metadata (cache-backed, not clean-environment benchmarks): `results/v1.0/main/run_meta.json:elapsed_s=107.17`, D3 `t4_runs` 1.67s, PILOT `t4_pilot` 29.82s. Decision A full-grid wall time and historical hardware are not recorded in its run_meta; no full-regeneration runtime estimate is invented. See [REPRODUCE_v1](REPRODUCE_v1.md) for commands and [STATISTICS](STATISTICS.md) for tolerance scope.
