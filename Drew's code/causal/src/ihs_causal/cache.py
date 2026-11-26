"""Content-addressed cache for expensive intermediate tables (cleaned hourly streams, decision tables, windows,
nuisance predictions). A table is stored once per key; the key includes the fingerprints of the input files, so a new
data release invalidates exactly the tables built from it and nothing else.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict

import pandas as pd

from ihs_causal.config import stable_hash


class Cache:
    def __init__(self, root: Path):
        self.root = Path(root)

    def _paths(self, kind: str, key: Dict[str, Any]):
        h = stable_hash(key, 16)
        d = self.root / kind
        return d / f"{h}.parquet", d / f"{h}.json"

    def get_or_build(self, kind: str, key: Dict[str, Any], build: Callable[[], pd.DataFrame]) -> pd.DataFrame:
        data_path, key_path = self._paths(kind, key)
        if data_path.exists():
            return pd.read_parquet(data_path)
        df = build()
        data_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = data_path.with_suffix(".tmp")
        df.to_parquet(tmp, index=False)
        tmp.replace(data_path)
        key_path.write_text(json.dumps(key, indent=1, sort_keys=True, default=str), encoding="utf-8")
        return df

    def clear(self, kind: str = "") -> int:
        target = self.root / kind if kind else self.root
        n = 0
        for p in target.rglob("*"):
            if p.is_file():
                p.unlink(); n += 1
        return n
