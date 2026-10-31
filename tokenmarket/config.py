"""Config loading (v3): a YAML file may `extends: <other.yaml>` (path relative to the file); mappings are
deep-merged, lists and scalars in the child replace the parent's."""
from __future__ import annotations

import copy
import os
from typing import Dict

import yaml


def deep_merge(base: Dict, over: Dict) -> Dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_config(path: str) -> Dict:
    with open(path, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    parent = cfg.pop("extends", None)
    if parent:
        cfg = deep_merge(load_config(os.path.join(os.path.dirname(path), parent)), cfg)
    return cfg
