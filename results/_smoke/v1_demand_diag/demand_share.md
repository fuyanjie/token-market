# Smoke: demand landing on strategic sellers (2 seeds, π∈{0.1,1.0})

Demand share = served purchases from the 9 strategic roster sellers / all served purchases.
Tail trade = runs with ≥1 sale to a strategic seller in the last 12 rounds.

| method | π | demand share | tail trade | E | Q |
|---|---:|---:|---:|---:|---:|
| cheapest_fixed | 0.1 | 0.000 (0/960) | 0/2 | 0.000 | 0.520 |
| cheapest_fixed | 1 | 0.000 (0/960) | 0/2 | 0.000 | 0.520 |
| fixed_audit_a0.05 | 0.1 | 0.009 (16/1824) | 1/2 | 0.006 | 0.576 |
| fixed_audit_a0.05 | 1 | 0.009 (16/1824) | 1/2 | 0.006 | 0.576 |
| fixed_audit_a0.10 | 0.1 | 0.009 (17/1828) | 2/2 | 0.007 | 0.576 |
| fixed_audit_a0.10 | 1 | 0.009 (17/1828) | 2/2 | 0.007 | 0.576 |
| fixed_audit_a0.20 | 0.1 | 0.009 (17/1818) | 2/2 | 0.005 | 0.521 |
| fixed_audit_a0.20 | 1 | 0.009 (17/1818) | 2/2 | 0.005 | 0.521 |
| pilot | 0.1 | 0.355 (336/947) | 2/2 | 0.230 | 0.825 |
| pilot | 1 | 0.288 (271/942) | 2/2 | 0.170 | 0.943 |
| random_audit | 0.1 | 0.009 (16/1825) | 1/2 | 0.004 | 0.521 |
| random_audit | 1 | 0.009 (16/1825) | 1/2 | 0.004 | 0.521 |
| risk_adaptive_audit | 0.1 | 0.009 (16/1821) | 1/2 | 0.006 | 0.576 |
| risk_adaptive_audit | 1 | 0.009 (16/1821) | 1/2 | 0.006 | 0.576 |
| stageroute | 0.1 | 0.202 (180/890) | 2/2 | 0.099 | 0.629 |
| stageroute | 1 | 0.093 (82/885) | 2/2 | 0.036 | 0.565 |
| strongest_fixed | 0.1 | 0.792 (699/883) | 2/2 | 0.455 | 0.793 |
| strongest_fixed | 1 | 0.792 (699/883) | 2/2 | 0.455 | 0.793 |
