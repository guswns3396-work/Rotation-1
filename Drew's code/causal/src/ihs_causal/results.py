"""The results store, and simultaneous intervals within families of estimates."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Set, Tuple

import numpy as np
import pandas as pd

from ihs_causal.estimators.inference import align_influence, simultaneous_critical_value


class ResultStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.est_path = self.root / "estimates.parquet"
        self.infl_path = self.root / "influence.parquet"
        self.runs_path = self.root / "runs.jsonl"

    def stamp(self) -> str:
        """Changes whenever a stored result is added, replaced or removed (file sizes and modification times)."""
        parts = []
        for p in (self.est_path, self.runs_path):
            st = p.stat() if p.exists() else None
            parts.append(f"{st.st_mtime_ns}-{st.st_size}" if st else "0")
        return "/".join(parts)

    def run_ids(self) -> Set[str]:
        if not self.est_path.exists():
            return set()
        return set(pd.read_parquet(self.est_path, columns=["run_id"])["run_id"].unique())

    def manifests(self) -> Dict[str, Dict]:
        """The latest manifest of every stored run, by run_id (settings, input fingerprints, diagnostics)."""
        out: Dict[str, Dict] = {}
        if self.runs_path.exists():
            for line in self.runs_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    m = json.loads(line)
                    out[m["run_id"]] = m
        return out

    def older_data(self, current: Dict[int, Dict[str, str]]) -> List[Dict]:
        """Manifests of stored runs made from other input files than `current` ({cohort: {kind: SHA-256}}).
        A cohort missing from `current` (its files are not on this machine) is never flagged."""
        ids = self.run_ids()
        out = []
        for rid, m in self.manifests().items():
            c = int(m.get("spec", {}).get("cohort", 0))
            if rid in ids and c in current and m.get("inputs") != current[c]:
                out.append(m)
        return out

    def estimates(self) -> pd.DataFrame:
        return pd.read_parquet(self.est_path) if self.est_path.exists() else pd.DataFrame()

    def influence(self, run_ids=None) -> pd.DataFrame:
        """The influence table, or only the rows of `run_ids`."""
        if not self.infl_path.exists():
            return pd.DataFrame()
        if run_ids is None:
            return pd.read_parquet(self.infl_path)
        try:
            return pd.read_parquet(self.infl_path, filters=[("run_id", "in", list(run_ids))])
        except Exception:       # e.g. a store whose runs saved no influence rows has no run_id column to filter on
            df = pd.read_parquet(self.infl_path)
            return df[df["run_id"].isin(list(run_ids))] if "run_id" in df else df

    @property
    def empty_path(self) -> Path:
        return self.root / "empty_runs.json"

    def empty_runs(self) -> Dict[str, Dict]:
        """Runs that had nothing to estimate (e.g. too few decisions in every arm), with the input files and package
        version they were tried with, so a full rerun does not retry them until either changes."""
        return json.loads(self.empty_path.read_text(encoding="utf-8")) if self.empty_path.exists() else {}

    def mark_empty(self, run_id: str, inputs: Dict) -> None:
        d = self.empty_runs()
        d[run_id] = inputs
        self.empty_path.write_text(json.dumps(d, indent=1, sort_keys=True), encoding="utf-8")

    @property
    def person_path(self) -> Path:
        return self.root / "person_effects.parquet"

    def add_person_effects(self, run_id: str, table: pd.DataFrame) -> None:
        """Participant-level effect estimates (question 6). Local only: never embedded in the viewer."""
        table = table.assign(run_id=run_id)
        if self.person_path.exists():
            old = pd.read_parquet(self.person_path)
            table = pd.concat([old[old.run_id != run_id], table], ignore_index=True)
        table.to_parquet(self.person_path, index=False)

    def prune(self, config_name: str, keep_run_ids: Set[str]) -> int:
        """Remove stored runs of `config_name` whose run_id the configuration no longer produces."""
        est = self.estimates()
        if est.empty:
            return 0
        drop = set(est.loc[(est.config_name == config_name) & ~est.run_id.isin(keep_run_ids), "run_id"])
        if not drop:
            return 0
        est[~est.run_id.isin(drop)].to_parquet(self.est_path, index=False)
        infl = self.influence()
        if len(infl):
            infl[~infl.run_id.isin(drop)].to_parquet(self.infl_path, index=False)
        if self.person_path.exists():
            pe = pd.read_parquet(self.person_path)
            pe[~pe.run_id.isin(drop)].to_parquet(self.person_path, index=False)
        if self.runs_path.exists():
            lines = [l for l in self.runs_path.read_text(encoding="utf-8").splitlines() if json.loads(l)["run_id"] not in drop]
            self.runs_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return len(drop)

    def add(self, table: pd.DataFrame, influence: Iterable[Tuple], manifest: Dict) -> None:
        rid = manifest["run_id"]
        old = self.estimates()
        if len(old):
            old = old[old.run_id != rid]
        pd.concat([old, table], ignore_index=True).to_parquet(self.est_path, index=False)
        rows = [pd.DataFrame({"run_id": rid, "contrast_label": lab, "arm": arm, "term": term,
                              "cluster": np.asarray(c), "psi": np.asarray(v, dtype=np.float32)}) for lab, arm, term, c, v in influence]
        new_infl = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
        old_infl = self.influence()
        if len(old_infl):
            old_infl = old_infl[old_infl.run_id != rid]
        pd.concat([old_infl, new_infl], ignore_index=True).to_parquet(self.infl_path, index=False)
        if self.runs_path.exists():      # one manifest per run: a rerun replaces the earlier line
            lines = [l for l in self.runs_path.read_text(encoding="utf-8").splitlines() if l.strip() and json.loads(l)["run_id"] != rid]
            self.runs_path.write_text("".join(l + "\n" for l in lines), encoding="utf-8")
        with open(self.runs_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(manifest, default=str) + "\n")


_CRIT_CACHE: Dict[Tuple, Tuple[float, Tuple]] = {}     # family members and SEs -> (critical value, members with influence)


def add_simultaneous(est: pd.DataFrame, infl, family_cols: Sequence[str], term: str = "effect",
                     draws: int = 2000) -> pd.DataFrame:
    """Within each family (rows sharing family_cols, restricted to `term`), the multiplier-bootstrap critical value and
    simultaneous 95% intervals. Rows outside `term` get NaN.

    `infl` is the influence table, or a function run_ids -> the influence rows of those runs. The bootstrap is
    deterministic (fixed seed), so a family's critical value is cached by its members and their standard errors: a
    rerun changes the standard errors and is recomputed; the families of untouched runs cost nothing."""
    est = est.copy()
    est["crit_simultaneous"] = np.nan
    key = ["run_id", "contrast_label", "arm", "term"]
    fams = []
    for _, fam in est[est.term == term].groupby(list(family_cols)):
        members = tuple(zip(fam.run_id, fam.contrast_label, fam.arm, fam.term))
        ck = (members, tuple(np.round(fam.se.to_numpy(dtype=float), 12)), draws)
        fams.append((fam.index.to_numpy(), members, ck))
    missing = [f for f in fams if f[2] not in _CRIT_CACHE]
    if missing:
        if callable(infl):
            infl = infl(sorted({m[0] for _, members, _ in missing for m in members}))
        groups = {k: g for k, g in infl.groupby(key)} if len(infl) else {}
        for idx, members, ck in missing:
            items, have = [], []
            for m in members:
                g = groups.get(m)
                if g is not None:
                    items.append((g["cluster"].to_numpy(), g["psi"].to_numpy(dtype=float))); have.append(m)
            if len(items) < 2:
                _CRIT_CACHE[ck] = (1.959963984540054, tuple(have))
                continue
            _, psi = align_influence(items)
            se = est.loc[idx, "se"].to_numpy()[[members.index(m) for m in have]]
            _CRIT_CACHE[ck] = (simultaneous_critical_value(psi, se, draws=draws), tuple(have))
    for idx, members, ck in fams:
        c, have = _CRIT_CACHE[ck]
        sel = [i for i, m in zip(idx, members) if m in set(have)]
        if sel:
            est.loc[sel, "crit_simultaneous"] = c
    if len(_CRIT_CACHE) > 20000:
        _CRIT_CACHE.clear()
    est["sim_low"] = est["estimate"] - est["crit_simultaneous"] * est["se"]
    est["sim_high"] = est["estimate"] + est["crit_simultaneous"] * est["se"]
    return est


def add_bh(est: pd.DataFrame, prefix: str = "mod:") -> pd.DataFrame:
    """Benjamini-Hochberg q-values across moderator terms within each (run, contrast item, arm)."""
    est = est.copy()
    est["q_bh"] = np.nan
    sel = est["term"].astype(str).str.startswith(prefix) & est["p"].notna()
    for _, g in est[sel].groupby(["run_id", "contrast_label", "arm"]):
        order = g["p"].sort_values()
        m = len(order)
        q = (order.to_numpy() * m / np.arange(1, m + 1))
        q = np.minimum.accumulate(q[::-1])[::-1].clip(max=1)
        est.loc[order.index, "q_bh"] = q
    return est
