#!/usr/bin/env python3
"""Reproducible descriptive price-ratio comparison. Not a calibration."""
from __future__ import annotations

import csv
import hashlib
import statistics
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

ROOT = Path("/workspace/token-market")
OUT = ROOT / "results/v1.1/v1.2_price_representativeness"
PRICES = ROOT / "configs/v1.0/frozen/prices.yaml"
SCALE = ROOT / "configs/v1.0/frozen/scale.yaml"
EXPECTED = {
    PRICES: "c26293cc3d890c6220491d02c06988372c79d0a5856899d2f165004bd8f9840f",
    SCALE: "780e9b961d89bad6fd520c9cbfd5710055ff2d5d3e0ff3bcfbd745709eb0da6c",
}

MAPPING_RULE = """# Frozen comparison rule (written before ratios were computed)

Date: 2026-11-15 Asia/Shanghai (UTC+8)
Repo: `/workspace/token-market`, branch `v1.1`
Inputs:
- `configs/v1.0/frozen/prices.yaml` (public list snapshot, access_date 2026-11-10)
- `configs/v1.0/frozen/scale.yaml` (simulator roster; `price_per_1k` ranges are synthetic market units)

This is a descriptive ratio comparison, not a calibration. Simulator prices are not rescaled. The text must not say “calibrated” or “已校准”. Simulator models are not paired to named public SKUs (Qwen 0.5B/1.5B are not GPT/Claude/Gemini). Simulator `price_per_1k` is a single synthetic unit with no input/output split, so input/output mix cannot be compared to the public lists.

1. Public snapshot: include a model row only if both `input` and `output` are non-null numbers. Exclude TODO/null/empty providers (DeepSeek, Alibaba) and unverified null rows (`gemini-3.1-flash-lite`). For `gemini-4-argon`, the primary table uses the access-date price (the through-2026-11-30 values). The `from_2026_12_01` schedule is reported only as a clearly labeled footnote/sensitivity row and is not mixed into primary max/min ratios.
2. For each filled provider, and for the pool of all filled primary rows across OpenAI+Anthropic+Google: report `output_max/output_min` and `input_max/input_min`. Also, for each included model, `output/input`, then min/median/max of those ratios within each provider and in the pool. Median is the ordinary mid-value of the sorted list (average of the two central values if even count).
3. Simulator roster bands are summarized by the midpoint of the configured range, midpoint = (lo+hi)/2, fixed a priori:
   - honest 1.5B: (0.17+0.24)/2
   - honest 0.5B: (0.08+0.12)/2
   - honest mock: (0.05+0.08)/2
   - strategic: (0.15+0.21)/2
   Primary roster ratios (midpoint): 1.5B/0.5B, 1.5B/mock, 0.5B/mock. Also report strategic mid / 1.5B mid as an overlap note, not as a representativeness claim. Sensitivity (clearly labeled, not primary): the same three honest ratios using range lows and using range highs.
4. Do not invent missing market evidence. There are no real marketplace transaction logs, and therefore no quantitative comparison of latency, volume, jurisdictions, or executed trades. Incomplete providers stay incomplete.
5. Record source paths, access date, URLs as written in prices.yaml, and sha256 of both yaml files. If a hash differs from the expected values, stop.
"""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_hashes() -> None:
    for path, expected in EXPECTED.items():
        got = sha256(path)
        if got != expected:
            raise SystemExit(f"HASH MISMATCH {path}: got {got}, expected {expected}")


def mid(lo: float, hi: float) -> float:
    return (lo + hi) / 2.0


def fmt(x: float) -> str:
    return f"{x:.10g}"


def ratio(a: float, b: float) -> float:
    if b == 0:
        raise SystemExit("zero denominator")
    return a / b


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "MAPPING_RULE.md").write_text(MAPPING_RULE)
    check_hashes()

    prices = yaml.safe_load(PRICES.read_text())
    access_date = prices.get("access_date")
    rows = []  # primary filled models
    footnotes = []
    excluded = []

    for prov_key, prov in (prices.get("providers") or {}).items():
        source_url = prov.get("source_url", "")
        accessed = prov.get("accessed", "")
        models = prov.get("models") or {}
        if prov.get("todo") and not models:
            excluded.append({"provider": prov_key, "model": "", "reason": prov.get("todo"), "source_url": source_url})
            continue
        for name, spec in models.items():
            if not isinstance(spec, dict):
                excluded.append({"provider": prov_key, "model": name, "reason": "not a mapping", "source_url": source_url})
                continue
            inp, out = spec.get("input"), spec.get("output")
            if inp is None or out is None or spec.get("todo"):
                excluded.append({
                    "provider": prov_key,
                    "model": name,
                    "reason": spec.get("todo") or "null input/output",
                    "source_url": source_url,
                })
                continue
            rec = {
                "provider": prov_key,
                "model": name,
                "input": float(inp),
                "output": float(out),
                "cached_input": spec.get("cached_input"),
                "source_url": source_url,
                "accessed": accessed,
            }
            rows.append(rec)
            if "from_2026_12_01" in spec and isinstance(spec["from_2026_12_01"], dict):
                alt = spec["from_2026_12_01"]
                if alt.get("input") is not None and alt.get("output") is not None:
                    footnotes.append({
                        "provider": prov_key,
                        "model": f"{name}@from_2026_12_01",
                        "input": float(alt["input"]),
                        "output": float(alt["output"]),
                        "cached_input": alt.get("cached_input"),
                        "source_url": source_url,
                        "accessed": accessed,
                    })

    # roster midpoints / endpoints, fixed a priori in the rule
    bands = {
        "honest_1.5B": (0.17, 0.24),
        "honest_0.5B": (0.08, 0.12),
        "honest_mock": (0.05, 0.08),
        "strategic": (0.15, 0.21),
    }
    mids = {k: mid(*v) for k, v in bands.items()}

    records = []  # list of dicts for csv

    def add(scope, metric, numer, denom, value, notes, numerator=None, denominator=None):
        records.append({
            "scope": scope,
            "metric": metric,
            "numerator": numer,
            "denominator": denom,
            "numerator_value": "" if numerator is None else fmt(numerator),
            "denominator_value": "" if denominator is None else fmt(denominator),
            "value": fmt(value) if value is not None else "",
            "notes": notes,
        })

    # source metadata rows (not ratios)
    records.append({
        "scope": "source",
        "metric": "prices_yaml_sha256",
        "numerator": str(PRICES.relative_to(ROOT)),
        "denominator": "",
        "numerator_value": "",
        "denominator_value": "",
        "value": sha256(PRICES),
        "notes": f"access_date={access_date}",
    })
    records.append({
        "scope": "source",
        "metric": "scale_yaml_sha256",
        "numerator": str(SCALE.relative_to(ROOT)),
        "denominator": "",
        "numerator_value": "",
        "denominator_value": "",
        "value": sha256(SCALE),
        "notes": "synthetic market units, not rescaled",
    })

    by_prov: dict[str, list] = {}
    for r in rows:
        by_prov.setdefault(r["provider"], []).append(r)

    def spread_and_oi(scope: str, group: list, notes: str) -> None:
        outs = [r["output"] for r in group]
        inps = [r["input"] for r in group]
        ois = [ratio(r["output"], r["input"]) for r in group]
        add(scope, "output_max/output_min", "output_max", "output_min", ratio(max(outs), min(outs)), notes, max(outs), min(outs))
        add(scope, "input_max/input_min", "input_max", "input_min", ratio(max(inps), min(inps)), notes, max(inps), min(inps))
        add(scope, "output/input_min", "output/input", "min of group", min(ois), notes, min(ois), None)
        add(scope, "output/input_median", "output/input", "median of group", statistics.median(ois), notes, statistics.median(ois), None)
        add(scope, "output/input_max", "output/input", "max of group", max(ois), notes, max(ois), None)
        for r, oi in zip(group, ois):
            add(scope, "output/input", r["model"], "input", oi,
                f"output={fmt(r['output'])}; input={fmt(r['input'])}; source={r['source_url']}",
                r["output"], r["input"])

    for prov, group in by_prov.items():
        url = group[0]["source_url"]
        acc = group[0]["accessed"]
        spread_and_oi(f"public:{prov}", group, f"primary; accessed={acc}; {url}; n={len(group)}")
    spread_and_oi("public:pool", rows, f"primary pool OpenAI+Anthropic+Google; n={len(rows)}; from_2026_12_01 not included")

    if footnotes:
        for r in footnotes:
            oi = ratio(r["output"], r["input"])
            add("sensitivity:gemini-4-argon@from_2026_12_01", "output/input", r["model"], "input", oi,
                "footnote only; not mixed into primary max/min", r["output"], r["input"])

    # roster primary
    add("roster:midpoint", "1.5B/0.5B", "honest_1.5B mid", "honest_0.5B mid",
        ratio(mids["honest_1.5B"], mids["honest_0.5B"]), "primary; midpoint=(lo+hi)/2",
        mids["honest_1.5B"], mids["honest_0.5B"])
    add("roster:midpoint", "1.5B/mock", "honest_1.5B mid", "honest_mock mid",
        ratio(mids["honest_1.5B"], mids["honest_mock"]), "primary; midpoint=(lo+hi)/2",
        mids["honest_1.5B"], mids["honest_mock"])
    add("roster:midpoint", "0.5B/mock", "honest_0.5B mid", "honest_mock mid",
        ratio(mids["honest_0.5B"], mids["honest_mock"]), "primary; midpoint=(lo+hi)/2",
        mids["honest_0.5B"], mids["honest_mock"])
    add("roster:midpoint", "strategic/1.5B", "strategic mid", "honest_1.5B mid",
        ratio(mids["strategic"], mids["honest_1.5B"]), "overlap note only, not a representativeness claim",
        mids["strategic"], mids["honest_1.5B"])

    lows = {k: v[0] for k, v in bands.items()}
    highs = {k: v[1] for k, v in bands.items()}
    for label, vals, note in (
        ("roster:sensitivity_lows", lows, "sensitivity; uses range lows, not primary"),
        ("roster:sensitivity_highs", highs, "sensitivity; uses range highs, not primary"),
    ):
        add(label, "1.5B/0.5B", "honest_1.5B", "honest_0.5B", ratio(vals["honest_1.5B"], vals["honest_0.5B"]), note, vals["honest_1.5B"], vals["honest_0.5B"])
        add(label, "1.5B/mock", "honest_1.5B", "honest_mock", ratio(vals["honest_1.5B"], vals["honest_mock"]), note, vals["honest_1.5B"], vals["honest_mock"])
        add(label, "0.5B/mock", "honest_0.5B", "honest_mock", ratio(vals["honest_0.5B"], vals["honest_mock"]), note, vals["honest_0.5B"], vals["honest_mock"])

    for e in excluded:
        records.append({
            "scope": "excluded",
            "metric": "not_in_primary",
            "numerator": e["provider"],
            "denominator": e["model"],
            "numerator_value": "",
            "denominator_value": "",
            "value": "",
            "notes": f"{e['reason']}; source={e['source_url']}",
        })

    fields = ["scope", "metric", "numerator", "denominator", "numerator_value", "denominator_value", "value", "notes"]
    csv_path = OUT / "ratios.csv"
    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(records)

    def md_escape(s: str) -> str:
        return s.replace("|", "\\|")

    lines = [
        "# Descriptive price-ratio comparison",
        "",
        "Not a calibration. Simulator `price_per_1k` values were not rescaled. Models are not paired by name to public SKUs.",
        "",
        f"- Rule: `MAPPING_RULE.md`",
        f"- Snapshot: `{PRICES.relative_to(ROOT)}` sha256 `{sha256(PRICES)}`, access_date {access_date}",
        f"- Roster: `{SCALE.relative_to(ROOT)}` sha256 `{sha256(SCALE)}`",
        f"- Regenerated by: `python3 results/v1.1/v1.2_price_representativeness/compute_ratios.py`",
        "",
        "| scope | metric | numerator | denominator | numerator_value | denominator_value | value | notes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in records:
        lines.append("| " + " | ".join(md_escape(str(r[c])) for c in fields) + " |")
    (OUT / "ratios.md").write_text("\n".join(lines) + "\n")

    def val(scope, metric) -> str:
        hits = [r for r in records if r["scope"] == scope and r["metric"] == metric]
        if not hits:
            return "NA"
        return hits[0]["value"]

    findings = f"""# Findings (descriptive only; not a calibration)

Computed 2026-11-15 Asia/Shanghai from frozen inputs. See `MAPPING_RULE.md` and `ratios.md`.

## Simulator roster (synthetic units, midpoint of configured range)

- honest 1.5B mid = (0.17+0.24)/2 = {fmt(mids['honest_1.5B'])}
- honest 0.5B mid = (0.08+0.12)/2 = {fmt(mids['honest_0.5B'])}
- honest mock mid = (0.05+0.08)/2 = {fmt(mids['honest_mock'])}
- strategic mid = (0.15+0.21)/2 = {fmt(mids['strategic'])}
- primary ratios: 1.5B/0.5B = {val('roster:midpoint','1.5B/0.5B')}; 1.5B/mock = {val('roster:midpoint','1.5B/mock')}; 0.5B/mock = {val('roster:midpoint','0.5B/mock')}
- overlap note (not a representativeness claim): strategic/1.5B = {val('roster:midpoint','strategic/1.5B')}
- sensitivity using range lows: 1.5B/0.5B = {val('roster:sensitivity_lows','1.5B/0.5B')}; 1.5B/mock = {val('roster:sensitivity_lows','1.5B/mock')}; 0.5B/mock = {val('roster:sensitivity_lows','0.5B/mock')}
- sensitivity using range highs: 1.5B/0.5B = {val('roster:sensitivity_highs','1.5B/0.5B')}; 1.5B/mock = {val('roster:sensitivity_highs','1.5B/mock')}; 0.5B/mock = {val('roster:sensitivity_highs','0.5B/mock')}

The primary honest max/min midpoint ratio is 1.5B/mock = {val('roster:midpoint','1.5B/mock')}.

## Public list snapshot (USD per 1K tokens, access_date {access_date})

Primary filled rows: n={len(rows)} ({", ".join(f"{p} {len(g)}" for p, g in by_prov.items())}).

- OpenAI output_max/output_min = {val('public:openai','output_max/output_min')}; input_max/input_min = {val('public:openai','input_max/input_min')}
- Anthropic output_max/output_min = {val('public:anthropic','output_max/output_min')}; input_max/input_min = {val('public:anthropic','input_max/input_min')}
- Google output_max/output_min = {val('public:google','output_max/output_min')}; input_max/input_min = {val('public:google','input_max/input_min')}
- Pool (OpenAI+Anthropic+Google) output_max/output_min = {val('public:pool','output_max/output_min')}; input_max/input_min = {val('public:pool','input_max/input_min')}
- Pool output/input min/median/max = {val('public:pool','output/input_min')} / {val('public:pool','output/input_median')} / {val('public:pool','output/input_max')}

Compared with each provider's primary output_max/output_min, the roster 1.5B/mock midpoint ratio ({val('roster:midpoint','1.5B/mock')}) is smaller than OpenAI ({val('public:openai','output_max/output_min')}), Anthropic ({val('public:anthropic','output_max/output_min')}), and the three-provider pool ({val('public:pool','output_max/output_min')}), and larger than Google ({val('public:google','output_max/output_min')}). The Google primary set has only two filled models; gemini-3.1-flash-lite is excluded as unverified, so 1.2 is not a full-catalog spread. These are internal spreads in different units; they do not say the simulator is cheaper or more expensive in USD.

## What this is not

- Not a calibration, and not a claim that prices are 已校准. The snapshot was not applied to `scale.yaml`.
- Not evidence that the simulator represents real API-market transactions. There are no real marketplace transaction logs, so latency, volume, jurisdictions, and executed trades cannot be compared quantitatively.
- Simulator `price_per_1k` has no input/output split, so public output/input ratios have no roster counterpart.
- DeepSeek and Alibaba Model Studio were empty TODOs on 2026-11-10; `gemini-3.1-flash-lite` was unverified/null and is excluded. `gemini-4-argon`'s 2026-12-01 schedule is a footnote only and is not in the primary ratios.
- Qwen 0.5B/1.5B are not mapped to named GPT/Claude/Gemini SKUs.

## Later protocol §7 robustness (not done here)

A calibrated robustness rerun still requires a mapping that rescales synthetic units, written down before any rerun, then a separate results table. That table must not be mixed with Decision A / Result 1. This file is only the descriptive ratio comparison.
"""
    (OUT / "FINDINGS.md").write_text(findings)

    out_hashes = {p.name: sha256(p) for p in sorted(OUT.iterdir()) if p.is_file()}
    tz = timezone(timedelta(hours=8))
    done = f"""# DONE

time: {datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S %Z")}
command: python3 results/v1.1/v1.2_price_representativeness/compute_ratios.py
cwd: /workspace/token-market
branch: v1.1

CLI note: Antigravity (`agy`) required a Google login and was not used; Codex exec returned 403 on this machine's egress (known); Claude Code was not logged in; Warp is available only as an interactive TUI and was already running an unrelated session. The frozen rule was executed with this script so the numbers are computed from the yaml files, not typed by hand.

Hashes of inputs matched the expected values.
Output sha256:
""" + "\n".join(f"- {k}: `{v}`" for k, v in out_hashes.items()) + "\n\nREPORT_READY\n"
    (OUT / "DONE.md").write_text(done)
    print("wrote", OUT)
    for k, v in out_hashes.items():
        print(k, v)


if __name__ == "__main__":
    main()
