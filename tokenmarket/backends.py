"""Inference backends: MockLLM (simulated), local_hf (real local Qwen models via an output cache), real (API)."""
from __future__ import annotations

import gc
import hashlib
import json
import os
import random
import re
import time
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# v1 prompt (kept for RealLLMBackend / backwards compatibility)
PROMPT = ("Solve the problem step by step, then give the final integer on the last line "
          "as 'Answer: <number>'.\n\nProblem: {q}")
# v2 prompt used for local_hf sellers and the output cache. Changing it invalidates the cache
# (cache key includes sha256 of the rendered prompt).
PROMPT_V2 = ("Solve the following problem. Reason briefly in a few short steps, then end with a final "
             "line of the form \"Answer: <number>\".\n\nProblem: {q}")


def render_prompt(question: str) -> str:
    return PROMPT_V2.format(q=question)


def prompt_sha256(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


@dataclass
class BackendResult:
    answer: Optional[int]
    reasoning_tokens: int
    raw: str = ""
    confidence: Optional[float] = None   # seller-side confidence signal (see confidence docs)
    gen_time_s: Optional[float] = None   # measured generation time (local_hf only)


# 'Answer:' followed (on the same line) by up to 16 non-digit decorations such as **, $, \(, \boxed{
_ANS_RE = re.compile(r"Answer\s*[:：][^\d\n]{0,16}?(-?\d[\d,]*(?:\.\d+)?)", re.IGNORECASE)
_NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def _to_int(s: str) -> Optional[int]:
    s = s.replace(",", "")
    try:
        f = float(s)
    except ValueError:
        return None
    return int(round(f)) if abs(f - round(f)) < 1e-9 else None


def parse_answer(text: str) -> Tuple[Optional[int], bool, int]:
    """Robust answer parser. Returns (answer, explicit, n_distinct_answer_values).
    explicit=True iff an 'Answer: <number>' marker was found (the LAST one wins); otherwise falls back
    to the last number anywhere in the text. Non-integer numbers parse to None."""
    marks = _ANS_RE.findall(text or "")
    if marks:
        vals = {_to_int(m) for m in marks}
        return _to_int(marks[-1]), True, len(vals)
    nums = _NUM_RE.findall(text or "")
    return (_to_int(nums[-1]) if nums else None), False, 0


def parse_final_number(text: str) -> Optional[int]:
    return parse_answer(text)[0]


def format_confidence(raw: str, answer: Optional[int], tokens: int, max_new_tokens: int) -> float:
    """Deterministic answer-format / self-consistency confidence proxy for real model outputs
    (no extra model calls, so it is free and cacheable):
      0.0  no parseable number
      0.2  no explicit 'Answer:' line (fallback parse) or generation truncated at max_new_tokens
      0.4  several 'Answer:' lines with different values (self-inconsistent)
      0.6  explicit answer but the value never appears in the reasoning before the 'Answer:' line
      0.9  explicit, consistent answer that is also derived in the reasoning text
    """
    if answer is None:
        return 0.0
    ans, explicit, n_vals = parse_answer(raw)
    if not explicit or tokens >= max_new_tokens:
        return 0.2
    if n_vals > 1:
        return 0.4
    head = raw[:raw.lower().rfind("answer")]
    derived = any(_to_int(n) == answer for n in _NUM_RE.findall(head))
    return 0.9 if derived else 0.6


class Backend(ABC):
    name = "base"

    @abstractmethod
    def solve(self, task, model_name: str, model_profile: Dict, effort: float,
              rng: random.Random) -> BackendResult:
        ...


class MockLLM(Backend):
    """P(correct) = actual model accuracy at task difficulty; wrong answers are perturbed gold.
    Confidence is noisy and only weakly informative: N(correct_mean | wrong_mean, std) clipped to [0,1]."""
    name = "mock"

    def __init__(self, confidence_cfg: Optional[Dict] = None):
        c = confidence_cfg or {}
        self.conf_correct = float(c.get("correct_mean", 0.75))
        self.conf_wrong = float(c.get("wrong_mean", 0.45))
        self.conf_std = float(c.get("std", 0.15))

    def solve(self, task, model_name, model_profile, effort, rng):
        acc = float(model_profile["accuracy"][task.difficulty])
        mean = model_profile["tokens_mean"] * (0.6 + 0.3 * task.difficulty) * effort
        tokens = int(max(20, rng.gauss(mean, model_profile["tokens_std"])))
        if rng.random() < acc:
            ans = task.gold
        else:
            delta = rng.choice([-1, 1]) * rng.randint(1, max(2, abs(task.gold) // 5 + 1))
            ans = task.gold + delta
        conf = rng.gauss(self.conf_correct if ans == task.gold else self.conf_wrong, self.conf_std)
        return BackendResult(ans, tokens, raw=f"[mock:{model_name}] Answer: {ans}",
                             confidence=min(1.0, max(0.0, conf)))


class LocalHFRunner:
    """Batched greedy generation with a local HF causal LM on CPU (fp32, left padding, chat template).
    transformers / torch are imported lazily so mock-only runs need neither."""

    def __init__(self, model_name: str, num_threads: int = 8):
        self.model_name = model_name
        self.num_threads = num_threads
        self._tok = None
        self._model = None

    def load(self):
        if self._model is None:
            import torch  # lazy
            from transformers import AutoModelForCausalLM, AutoTokenizer  # lazy
            torch.set_num_threads(self.num_threads)
            self._tok = AutoTokenizer.from_pretrained(self.model_name, padding_side="left")
            if self._tok.pad_token is None:
                self._tok.pad_token = self._tok.eos_token
            self._model = AutoModelForCausalLM.from_pretrained(self.model_name, dtype=torch.float32)
            self._model.eval()
        return self

    def unload(self):
        self._model = None
        self._tok = None
        gc.collect()

    def generate(self, prompts: List[str], max_new_tokens: int) -> Tuple[List[Tuple[str, int]], float]:
        """Returns ([(text, n_generated_tokens), ...], batch_wall_time_s). Token count excludes
        padding and the terminating EOS token."""
        import torch  # lazy
        self.load()
        texts = [self._tok.apply_chat_template([{"role": "user", "content": p}], tokenize=False,
                                               add_generation_prompt=True) for p in prompts]
        enc = self._tok(texts, return_tensors="pt", padding=True)
        eos = self._model.generation_config.eos_token_id
        eos_ids = set(eos if isinstance(eos, (list, tuple)) else [eos]) | {self._tok.pad_token_id}
        t0 = time.time()
        with torch.inference_mode():
            out = self._model.generate(**enc, do_sample=False, max_new_tokens=int(max_new_tokens),
                                       temperature=None, top_p=None, top_k=None,
                                       pad_token_id=self._tok.pad_token_id)
        dt = time.time() - t0
        res = []
        for row in out[:, enc["input_ids"].shape[1]:].tolist():
            n = next((i for i, t in enumerate(row) if t in eos_ids), len(row))
            res.append((self._tok.decode(row[:n], skip_special_tokens=True), n))
        return res, dt


class CachedLocalBackend(Backend):
    """local_hf seller backend at simulation time: serves the ACTUAL model's precomputed output for the
    task's prompt from the output cache (see tokenmarket/cache.py). Never loads a model; a cache miss is
    an error (run the precompute stage first)."""
    name = "local_hf"

    def __init__(self, cache, max_new_tokens: int):
        self.cache = cache
        self.max_new_tokens = int(max_new_tokens)

    def solve(self, task, model_name, model_profile, effort, rng):
        rec = self.cache.get(model_name, render_prompt(task.question), self.max_new_tokens)
        if rec is None:
            raise KeyError(f"no cached output for {model_name} on {task.task_id}; run --precompute-only first")
        ans = rec["parsed_answer"]
        return BackendResult(ans, int(rec["reasoning_tokens"]), rec["raw_text"],
                             confidence=format_confidence(rec["raw_text"], ans, int(rec["reasoning_tokens"]),
                                                          self.max_new_tokens),
                             gen_time_s=float(rec["gen_time_s"]))


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


def make_backend(name: str, cfg: Dict, cache=None) -> Backend:
    """Simulation-time backends. local_hf serves from the output cache (precompute stage fills it)."""
    bcfg = cfg.get("backends", {})
    if name == "mock":
        return MockLLM(cfg.get("market", {}).get("mock_confidence"))
    if name == "local_hf":
        if cache is None:
            raise ValueError("local_hf backend needs an OutputCache")
        return CachedLocalBackend(cache, int(bcfg.get("local_hf", {}).get("max_new_tokens", 256)))
    if name == "real":
        r = bcfg["real"]
        return RealLLMBackend(r["base_url"], r["api_key_env"], r.get("model_map", {}), r.get("timeout_s", 60))
    raise ValueError(f"unknown backend {name}")
