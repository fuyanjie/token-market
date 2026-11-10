# Third-party data licences

Both raw files in `data/raw/` and the derived subset `data/long_tasks.jsonl` (48 items) come from MIT-licensed
datasets. The raw test splits are committed unchanged (≈1.2 MB) so that `scripts/build_long_tasks.py` can rebuild
the subset deterministically.

## GSM8K — `data/raw/gsm8k_test.jsonl`
Source: openai/grade-school-math (test split), https://github.com/openai/grade-school-math
Licence: MIT License — Copyright (c) 2021 OpenAI
Used: 28 hardest test items (most reference-solution steps / longest solution; seeded draw from the top 84).

## MATH-500 — `data/raw/math500_test.jsonl`
Source: HuggingFaceH4/MATH-500, the 500-problem test subset from openai/prm800k, https://github.com/openai/prm800k
Licence: MIT License — Copyright (c) 2023 OpenAI
(The problems originate from the MATH dataset by Hendrycks et al., which is also released under the MIT License.)
Used: 20 items with a plain integer answer (`^-?\d+$`) and level >= 3 (seeded draw).

## MIT License text

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
