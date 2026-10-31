# Measured local model accuracy (task pool, greedy, CPU fp32)

| model | n | acc overall | acc d1 (n) | acc d2 (n) | acc d3 (n) | reasoning tokens mean ± std | gen time/item (s) mean ± std | total gen time (s) | explicit 'Answer:' rate | truncated rate |
|---|---|---|---|---|---|---|---|---|---|---|
| Qwen/Qwen2.5-0.5B-Instruct | 80 | 0.662 | 0.786 (28) | 0.750 (28) | 0.417 (24) | 149.4 ± 63.7 | 4.40 ± 7.08 | 352.2 | 0.512 | 0.075 |
| Qwen/Qwen2.5-1.5B-Instruct | 80 | 0.925 | 0.929 (28) | 1.000 (28) | 0.833 (24) | 142.3 ± 47.2 | 2.53 ± 0.77 | 202.5 | 0.900 | 0.037 |

Greedy decoding, chat template, max_new_tokens=256, batched (left padding). reasoning tokens = generated tokens excluding EOS/padding; gen time/item = amortised share of batch wall time proportional to generated tokens (8 CPU threads). Correct = parsed answer (last 'Answer:' number, else last number) == gold.
