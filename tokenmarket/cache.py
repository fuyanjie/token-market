"""Append-only JSONL cache of real model outputs.

Key = (model_name, sha256(rendered user prompt), max_new_tokens). One line per key:
  model_name, prompt_sha256, max_new_tokens, pool_task_id, difficulty, gold,
  raw_text, parsed_answer, explicit_answer, correct, reasoning_tokens (generated tokens, excl. EOS/pad),
  gen_time_s (amortised per-item share of the batch wall time, proportional to generated tokens),
  batch_size, batch_time_s, created_ts
"""
from __future__ import annotations

import json
import os
from typing import Dict, Optional, Tuple

from .backends import prompt_sha256

Key = Tuple[str, str, int]


class OutputCache:
    def __init__(self, path: str):
        self.path = path
        self._data: Dict[Key, Dict] = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        rec = json.loads(line)
                        self._data[self.key_of(rec)] = rec

    @staticmethod
    def key_of(rec: Dict) -> Key:
        return rec["model_name"], rec["prompt_sha256"], int(rec["max_new_tokens"])

    def get(self, model_name: str, prompt: str, max_new_tokens: int) -> Optional[Dict]:
        return self._data.get((model_name, prompt_sha256(prompt), int(max_new_tokens)))

    def put(self, rec: Dict) -> None:
        k = self.key_of(rec)
        if k in self._data:
            return
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        self._data[k] = rec

    def __len__(self) -> int:
        return len(self._data)
