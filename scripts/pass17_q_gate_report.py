#!/usr/bin/env python3
"""Read frozen v1.0 boards; write only docs/v1.1/db/Q_GATE_REPORT.{json,md}."""
import csv
import hashlib
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/v1.1/db'
ORDER = ['pilot', 'stageroute', 'cheapest_fixed', 'strongest_fixed',
         'fixed_audit_a0.05', 'fixed_audit_a0.10', 'fixed_audit_a0.20',
         'random_audit', 'risk_adaptive_audit']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(name):
    groups = defaultdict(list)
    with (ROOT / f'results/v1.0/{name}/per_seed.csv').open() as f:
        for r in csv.DictReader(f):
            groups[float(r['pi']), r['method']].append(r)
    return groups

def points(groups, pi):
    out = {}
    for m in ORDER:
        rows = groups.get((pi, m), [])
        if not rows:
            continue
        assert len(rows) == 20 and len({int(r['seed']) for r in rows}) == 20
        out[m] = {k: sum(float(r[k]) for r in rows) / len(rows) for k in ('E', 'Q')}
        out[m]['tail_trade_rate'] = sum(r['tail_trade'].lower() == 'true' for r in rows) / len(rows)
        assert all(math.isfinite(v) for v in out[m].values())
    return out

def front(p, methods):
    return sorted(a for a in methods if not any(
        p[b]['E'] <= p[a]['E'] and p[b]['Q'] <= p[a]['Q'] and
        (p[b]['E'] < p[a]['E'] or p[b]['Q'] < p[a]['Q']) for b in methods))

def main():
    base, peer = load('main'), load('main_fp')
    frozen = json.loads((ROOT / 'results/v1.0/main/inference.json').read_text())['q_gate']
    per = []
    for pi in sorted({k[0] for k in base}):
        a, b = points(base, pi), points(peer, pi)
        ea = [m for m in ORDER if m in a and a[m]['tail_trade_rate'] > 0.5]
        eb = [m for m in ORDER if m in b and b[m]['tail_trade_rate'] > 0.5]
        ms = [m for m in ORDER if m in ea and m in eb]
        # Exactly follow analyzer: stable sorting by Q assigns sequential ranks.
        ra = {m: i for i, m in enumerate(sorted(ms, key=lambda m: a[m]['Q']))}
        rb = {m: i for i, m in enumerate(sorted(ms, key=lambda m: b[m]['Q']))}
        c = d = t = 0
        for i, j in itertools.combinations(ms, 2):
            x, y = ra[i] - ra[j], rb[i] - rb[j]
            if x == 0 or y == 0:
                t += 1
            elif (x > 0) == (y > 0):
                c += 1
            else:
                d += 1
        tau = (c-d)/(len(ms)*(len(ms)-1)/2) if len(ms) > 1 else None
        fa, fb = front(a, ms), front(b, ms)
        row = dict(pi=pi, eligible_main=ea, eligible_peer=eb, common=ms,
                   excluded_main=[m for m in ORDER if m not in ea],
                   excluded_peer=[m for m in ORDER if m not in eb],
                   means_main=a, means_peer=b, ranks_main=ra, ranks_peer=rb,
                   concordant_pairs=c, discordant_pairs=d, tied_pairs=t,
                   kendall_tau_a=tau, tau_ge_0_6=tau is not None and tau >= 0.6,
                   front_main=fa, front_peer=fb, front_unchanged=fa == fb)
        row['pass'] = row['tau_ge_0_6'] and row['front_unchanged']
        old = next(x for x in frozen['per_pi'] if x['pi'] == pi)
        row['matches_frozen_gate'] = (row['pass'] == old['pass'] and fa == old['front_main']
             and fb == old['front_peer'] and tau is not None
             and tau == old['kendall_tau_a'] and ms == old['common'])
        per.append(row)
    paths = ['docs/PROTOCOL_v1.0.md', 'scripts/v1/analyze_scale_v1.py',
             'results/v1.0/main/per_seed.csv', 'results/v1.0/main_fp/per_seed.csv',
             'results/v1.0/main/inference.json']
    result = dict(documentation_date='2026-11-15', scope='formal 40-seller gate; egreedy vs fictitious_play',
        rule_source='docs/PROTOCOL_v1.0.md §1; 口径补正 2026-11-10 and 开跑前裁定 item 2',
        implementation_source='scripts/v1/analyze_scale_v1.py: Q-gate vs peer learner directory',
        rule='At every pi: tau_a >= 0.6 AND unchanged lower-better (E,Q) front on methods with tail_trade_rate > 0.5 under both learners.',
        ties='Analyzer stably sorts equal mean Q in ORDER and assigns distinct sequential ranks; pairwise Kendall uses (C-D)/(n*(n-1)/2). Equal E,Q points do not dominate each other. No epsilon tie threshold.',
        front_evidence='available: derived from frozen main and main_fp per_seed.csv outputs',
        source_sha256={p:sha(ROOT/p) for p in paths}, per_pi=per,
        pass_all_pi=all(r['pass'] for r in per), matches_frozen_gate=all(r['matches_frozen_gate'] for r in per),
        paper_verdict_changed=False, excluded_checks='EXP3 and historical Hedge check are appendix-only, not formal gate members')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'Q_GATE_REPORT.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    lines=['# Q gate audit — documentation 2026-11-15','',result['rule_source'],'',result['rule'],'',result['ties'],'',
        'Formal peer: fictitious play. EXP3 and the earlier Hedge check are excluded. The eligibility screen is reproduced without revising its interpretation or any paper verdict.', '',
        '| π | eligible main / peer / common | τ_a | τ predicate | front main | front peer | front predicate | pass | agrees with frozen gate |',
        '|---|---|---|---|---|---|---|---|---|']
    for r in per:
        lines.append(f"| {r['pi']} | {len(r['eligible_main'])}/{len(r['eligible_peer'])}/{len(r['common'])} | {r['kendall_tau_a']:.15g} | {r['tau_ge_0_6']} | {','.join(r['front_main'])} | {','.join(r['front_peer'])} | {r['front_unchanged']} | {r['pass']} | {r['matches_frozen_gate']} |")
    lines += ['',f"All π pass: **{result['pass_all_pi']}**. All agree with frozen gate: **{result['matches_frozen_gate']}**.", '',
        'The JSON lists each eligible/excluded method, means, ranks, pair counts and source hashes. Rebuild: `python scripts/pass17_q_gate_report.py`. No simulator or bootstrap is run.']
    (OUT/'Q_GATE_REPORT.md').write_text('\n'.join(lines)+'\n')
    print('Q gate:',result['pass_all_pi'],'frozen agreement:',result['matches_frozen_gate'],'pi points:',len(per))

if __name__ == '__main__':
    main()
