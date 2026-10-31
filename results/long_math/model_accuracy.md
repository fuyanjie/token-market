# Measured local model accuracy (task pool, greedy, CPU fp32)

| model | n | acc overall | acc d4 (n) | acc d5 (n) | reasoning tokens mean ± std | gen time/item (s) mean ± std | total gen time (s) | explicit 'Answer:' rate | truncated rate |
|---|---|---|---|---|---|---|---|---|---|
| Qwen/Qwen2.5-0.5B-Instruct | 48 | 0.146 | 0.214 (28) | 0.050 (20) | 425.3 ± 90.7 | 3.02 ± 0.61 | 145.0 | 0.000 | 0.417 |
| Qwen/Qwen2.5-1.5B-Instruct | 48 | 0.438 | 0.536 (28) | 0.300 (20) | 414.3 ± 90.4 | 13.90 ± 9.86 | 667.0 | 0.312 | 0.292 |

Greedy decoding, chat template, max_new_tokens=256, batched (left padding). reasoning tokens = generated tokens excluding EOS/padding; gen time/item = amortised share of batch wall time proportional to generated tokens (8 CPU threads). Correct = parsed answer (last 'Answer:' number, else last number) == gold.
