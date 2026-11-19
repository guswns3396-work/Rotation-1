"""Configuration: YAML files describing one analysis or a sweep of analyses.

A configuration file has a `base` mapping (one run's settings, merged over the package defaults) and an optional
`sweep` mapping from dotted keys to lists of values; the sweep expands to every combination. Every run gets a stable
`run_id`, a hash of its settings, so a run that has already been computed with the same inputs is never repeated.

    name: primary_2024
    base:
      cohort: 2024
      estimator: {name: wcls}
    sweep:
      outcome: [mood, steps, sleep]
      contrast: [send_vs_none, domain_vs_none]

Paths to the data live in a separate, per-machine `paths.yaml` (see config/paths.example.yaml), so the same analysis
configuration runs on Drew's and Jack's machines.
"""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
from pathlib import Path
from typing import Any, Dict, Iterator, List

import yaml

PACKAGE_DEFAULTS = Path(__file__).with_name("defaults.yaml")


def deep_merge(base: Dict[str, Any], over: Dict[str, Any]) -> Dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def set_dotted(d: Dict[str, Any], dotted: str, value: Any) -> None:
    keys = dotted.split(".")
    for k in keys[:-1]:
        d = d.setdefault(k, {})
    d[keys[-1]] = value


def get_dotted(d: Dict[str, Any], dotted: str, default: Any = None) -> Any:
    for k in dotted.split("."):
        if not isinstance(d, dict) or k not in d:
            return default
        d = d[k]
    return d


def stable_hash(obj: Any, length: int = 12) -> str:
    text = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:length]


def load_yaml(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def defaults() -> Dict[str, Any]:
    return load_yaml(PACKAGE_DEFAULTS)


def expand(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Expand a configuration (base + sweep) into a list of fully specified runs."""
    base = deep_merge(defaults(), config.get("base", {}))
    sweep = config.get("sweep") or {}
    keys = list(sweep)
    runs = []
    for combo in itertools.product(*[sweep[k] for k in keys]) if keys else [()]:
        spec = copy.deepcopy(base)
        for k, v in zip(keys, combo):
            set_dotted(spec, k, v)
        spec["run_id"] = run_id(spec)
        spec["config_name"] = config.get("name", "unnamed")
        runs.append(spec)
    return runs


def run_id(spec: Dict[str, Any]) -> str:
    """Hash of everything that affects the numbers (labels and bookkeeping keys excluded). A setting left unset (None)
    is left out, so adding a new optional setting does not change the ids of runs stored before it existed."""
    ignore = {"run_id", "config_name", "label", "family", "notes"}
    return stable_hash({k: v for k, v in spec.items() if k not in ignore and v is not None})


def iter_specs(path: Path) -> Iterator[Dict[str, Any]]:
    yield from expand(load_yaml(path))
