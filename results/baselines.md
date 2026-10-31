# D — baselines vs the STRATEGIC model-swap seller

All policies face the same learning swap seller (seller_sg; penalty P=0.25, d=0.9). Only D3 audits (rate 0.1, audit cost 0.004 per audit charged to the buyer budget), so for every other policy the seller faces a = 0. Mean ± std over seeds [0, 1, 2].

| policy | task accuracy | total cost incl. audit | of which audit | cost/task | budget violations | compliance violations | fraud-seller share (swapped purchases) | sg learned q | swaps detected / served | stake slashed | buyer surplus |
|---|---|---|---|---|---|---|---|---|---|---|---|
| single_cheapest_compliant | 0.665 ± 0.019 | 5.562 ± 0.292 | 0.000 | 0.0116 ± 0.0006 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.061 ± 0.019 | 0.922 ± 0.081 | 0.0 / 29.3 | 0.00 | 19.221 ± 0.441 |
| single_best_compliant | 0.634 ± 0.008 | 11.606 ± 0.227 | 0.000 | 0.0242 ± 0.0005 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.766 ± 0.016 | 0.950 ± 0.044 | 0.0 / 335.7 | 0.00 | 12.431 ± 0.333 |
| cascade_compliant | 0.768 ± 0.011 | 13.940 ± 0.054 | 0.000 | 0.0290 ± 0.0001 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.302 ± 0.014 | 0.950 ± 0.044 | 0.0 / 222.7 | 0.00 | 14.897 ± 0.476 |
| vote_k_compliant | 0.690 ± 0.014 | 20.669 ± 0.161 | 0.000 | 0.0431 ± 0.0003 | 0.7 ± 0.6 | 0.0 ± 0.0 | 0.323 ± 0.004 | 0.950 ± 0.044 | 0.0 / 311.7 | 0.00 | 5.555 ± 0.581 |
| compliance_unaware_cheapest | 0.627 ± 0.044 | 3.486 ± 0.028 | 0.000 | 0.0073 ± 0.0001 | 0.0 ± 0.0 | 103.3 ± 6.4 | 0.000 ± 0.000 | 0.539 ± 0.028 | 0.0 / 0.0 | 0.00 | 19.594 ± 1.671 |
| PILOT-style (our simplified reimpl. of Panda et al. 2025), no compliance filter | 0.883 ± 0.019 | 11.433 ± 0.093 | 0.000 | 0.0238 ± 0.0002 | 0.0 ± 0.0 | 77.7 ± 9.3 | 0.235 ± 0.066 | 0.950 ± 0.044 | 0.0 / 112.7 | 0.00 | 21.420 ± 0.660 |
| PILOT-style + compliance filter | 0.856 ± 0.013 | 11.183 ± 0.319 | 0.000 | 0.0233 ± 0.0007 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.215 ± 0.049 | 0.950 ± 0.044 | 0.0 / 103.0 | 0.00 | 20.667 ± 0.634 |
| StageRoute-style (our simplified reimpl. of Li & Li 2025), no compliance filter | 0.837 ± 0.037 | 12.551 ± 0.154 | 0.000 | 0.0261 ± 0.0003 | 0.0 ± 0.0 | 61.3 ± 8.0 | 0.085 ± 0.038 | 0.950 ± 0.044 | 0.0 / 37.7 | 0.00 | 18.819 ± 1.071 |
| StageRoute-style + compliance filter | 0.797 ± 0.030 | 11.507 ± 0.565 | 0.000 | 0.0240 ± 0.0012 | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.116 ± 0.086 | 0.950 ± 0.044 | 0.0 / 51.7 | 0.00 | 18.453 ± 1.455 |
| **D3 audited_compliance_cascade (ours)** | 0.811 ± 0.010 | 11.979 ± 0.364 | 0.233 | 0.0250 ± 0.0008 | 0.3 ± 0.6 | 0.0 ± 0.0 | 0.042 ± 0.017 | 0.131 ± 0.108 | 3.3 / 28.0 | 0.83 | 18.418 ± 0.687 |

## Accuracy at equal cost (from the A curves)

| family | c=0.0100 | c=0.0203 | c=0.0246 | c=0.0272 |
|---|---|---|---|---|
| audited_compliance_cascade | 0.317 | 0.646 | 0.786 | 0.877 |
| audited_compliance_cascade (audit rate) | – | – | – | 0.880 |
| cascade_compliant | 0.265 | 0.537 | 0.646 | 0.710 |
| cascade_compliant (threshold) | – | 0.769 | 0.798 | 0.808 |
| pilot | 0.546 | 0.788 | 0.890 | 0.896 |
| pilot_compliant | 0.465 | 0.761 | 0.875 | 0.876 |
| single_best_compliant | 0.275 | 0.538 | 0.644 | 0.693 |
| single_cheapest_compliant | 0.588 | 0.665 | 0.665 | 0.665 |
| stageroute | 0.305 | 0.644 | 0.786 | 0.865 |
| stageroute_compliant | 0.342 | 0.681 | 0.819 | 0.832 |
| vote_k_compliant (k) | – | – | – | 0.693 |
| vote_k_compliant k=1 | 0.275 | 0.538 | 0.644 | 0.693 |
| vote_k_compliant k=2 | 0.173 | 0.335 | 0.401 | 0.440 |
| vote_k_compliant k=3 | 0.174 | 0.340 | 0.405 | 0.447 |

Differences from the papers (all baselines are OUR SIMPLIFIED REIMPLEMENTATIONS):
- PILOT: hand-made task features instead of query embeddings; the preference prior is the CLAIMED model's public reputation (so a swap seller inherits a good prior); reward = observed correctness; ON-MCKP ZCL threshold with budget bins + spillover and the B_left/Q_left fallback; one LinUCB shared by all buyers, budgets per buyer.
- StageRoute: only the per-query routing LP with UCB rewards / LCB costs and throughput caps (alpha = capacity share); the stage-wise deployment MIP is skipped (3 fixed sellers); LP solved exactly by vertex enumeration.
- Neither baseline accounts for audit cost, models a strategic seller, or filters on compliance (the `_compliant` variants add the hard compliance filter); non-filtered variants run through the audit_only gateway so their breaches are counted.
- D3 routes on audit-adjusted quality: once an audit reveals the served model, the seller's quality is (1 − q̂)·rep(claimed) + q̂·rep(revealed), q̂ = detected / (audits·d) (smoothed).
