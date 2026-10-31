"""Inference backends. MockLLM is the default; LocalHF and RealLLM are opt-in."""
from __future__ import annotations

import json
import os
import random
import re
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional

PROMPT = ("Solve the problem step by step, then give the final integer on the last line "
          "as 'Answer: <number>'.\n\nProblem: {q}")


@dataclass
class BackendResult:
    answer: Optional[int]
    reasoning_tokens: int
    raw: str = ""


def parse_final_number(text: str) -> Optional[int]:
    m = re.findall(r"Answer\s*[:：]\s*(-?\d[\d,]*)", text)
    nums = m or re.findall(r"-?\d[\d,]*", text)
    if not nums:
        return None
    try:
        return int(nums[-1].replace(",", ""))
    except ValueError:
        return None


class Backend(ABC):
    name = "base"

    @abstractmethod
    def solve(self, task, model_name: str, model_profile: Dict, effort: float,
              rng: random.Random) -> BackendResult:
        ...


class MockLLM(Backend):
    """P(correct) = actual model accuracy at task difficulty; wrong answers are perturbed gold."""
    name = "mock"

    def solve(self, task, model_name, model_profile, effort, rng):
        acc = float(model_profile["accuracy"][task.difficulty])
        mean = model_profile["tokens_mean"] * (0.6 + 0.3 * task.difficulty) * effort
        tokens = int(max(50, rng.gauss(mean, model_profile["tokens_std"])))
        if rng.random() < acc:
            ans = task.gold
        else:
            delta = rng.choice([-1, 1]) * rng.randint(1, max(2, abs(task.gold) // 5 + 1))
            ans = task.gold + delta
        return BackendResult(ans, tokens, raw=f"[mock:{model_name}] Answer: {ans}")


class LocalHFBackend(Backend):
    """Qwen/Qwen2.5-0.5B-Instruct on CPU via transformers (lazy import). All simulated models map to
    the same weights; 'weaker' models get a smaller max_new_tokens budget (hf_max_new_tokens)."""
    name = "local_hf"

    def __init__(self, model_name: str = "Qwen/Qwen2.5-0.5B-Instruct"):
        self.model_name = model_name
        self._tok = None
        self._model = None

    def _load(self):
        if self._model is None:
            from transformers import AutoModelForCausalLM, AutoTokenizer  # lazy
            self._tok = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForCausalLM.from_pretrained(self.model_name)
            self._model.eval()

    def solve(self, task, model_name, model_profile, effort, rng):
        self._load()
        msgs = [{"role": "user", "content": PROMPT.format(q=task.question)}]
        text = self._tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        inputs = self._tok(text, return_tensors="pt")
        out = self._model.generate(**inputs, do_sample=False,
                                   max_new_tokens=int(model_profile.get("hf_max_new_tokens", 256)))
        gen = out[0][inputs["input_ids"].shape[1]:]
        raw = self._tok.decode(gen, skip_special_tokens=True)
        return BackendResult(parse_final_number(raw), int(len(gen)), raw)


class RealLLMBackend(Backend):
    """OpenAI-compatible chat-completions client (urllib only). Unused by default; key from env."""
    name = "real"

    def __init__(self, base_url: str, api_key_env: str, model_map: Dict[str, str], timeout_s: int = 60):
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.model_map = model_map
        self.timeout_s = timeout_s

    def solve(self, task, model_name, model_profile, effort, rng):
        key = os.environ.get(self.api_key_env)
        if not key:
            raise RuntimeError(f"RealLLMBackend requires env var {self.api_key_env}")
        body = json.dumps({"model": self.model_map.get(model_name, model_name),
                           "messages": [{"role": "user", "content": PROMPT.format(q=task.question)}],
                           "temperature": 0}).encode()
        req = urllib.request.Request(f"{self.base_url}/chat/completions", data=body, method="POST",
                                     headers={"Content-Type": "application/json",
                                              "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            data = json.loads(resp.read().decode())
        raw = data["choices"][0]["message"].get("content") or ""
        usage = data.get("usage", {})
        details = usage.get("completion_tokens_details") or {}
        tokens = details.get("reasoning_tokens") or usage.get("completion_tokens", 0)
        return BackendResult(parse_final_number(raw), int(tokens), raw)


def make_backend(name: str, cfg: Dict) -> Backend:
    bcfg = cfg.get("backends", {})
    if name == "mock":
        return MockLLM()
    if name == "local_hf":
        return LocalHFBackend(bcfg.get("local_hf", {}).get("model_name", "Qwen/Qwen2.5-0.5B-Instruct"))
    if name == "real":
        r = bcfg["real"]
        return RealLLMBackend(r["base_url"], r["api_key_env"], r.get("model_map", {}), r.get("timeout_s", 60))
    raise ValueError(f"unknown backend {name}")
