"""Cached access to the inputs: hourly tables, decision tables, baseline traits, window statistics and analysis tables.

Disk caches (Parquet, keyed by the fingerprints of the input files and a version number per builder):
  hourly         the compact hourly table of a cohort
  decisions      the common-schema decision table
  window_stats   layer 1 of the analysis table, per cohort and window definition (the expensive part)
In memory: window statistics and baseline traits are kept for the life of the process (the server keeps them between
runs); analysis tables (layer 2) are rebuilt from them in milliseconds for each device and keep-rule setting.
Bump a builder's number in VERSIONS when its output changes, so stale tables are rebuilt.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import pandas as pd

from ihs_causal.cache import Cache
from ihs_causal.data.decisions import ADAPTERS
from ihs_causal.data.features import CONTEXT, TRAITS, apply_rules, baseline_traits, in_dates, survey_catalog, window_stats
from ihs_causal.data.hourly import read_hourly
from ihs_causal.paths import Paths, fingerprint

VERSIONS = {"hourly": 1, "decisions": 4, "window_stats": 3}


class Workspace:
    def __init__(self, paths: Paths, log=print):
        self.paths = paths
        self.cache = Cache(paths.cache_dir)
        self.log = log
        self._mem: Dict[Tuple, object] = {}

    def fp(self, cohort: int, kind: str) -> str:
        return fingerprint(self.paths.file(cohort, kind), self.paths.work_dir / "fingerprints.json")

    def inputs(self, cohort: int) -> Dict[str, str]:
        """Fingerprints of the files a cohort's results depend on (for 2024 also the message-type file, when present)."""
        kinds = ["hourly", "decisions", "surveys"] + (["timing"] if int(cohort) == 2025 else [])
        if int(cohort) == 2024 and self.paths.file(2024, "message_types").exists():
            kinds.append("message_types")
        return {k: self.fp(cohort, k) for k in kinds}

    def current_inputs(self) -> Dict[int, Dict[str, Dict[str, str]]]:
        """For each cohort whose files are on this machine: the fingerprint and the path of every input file."""
        out = {}
        for c in (2024, 2025):
            try:
                fps = self.inputs(c)
            except FileNotFoundError:
                continue
            out[c] = {"inputs": fps, "files": {k: str(self.paths.file(c, k)) for k in fps}}
        return out

    def _memo(self, key: Tuple, build):
        if key not in self._mem:
            self._mem[key] = build()
        return self._mem[key]

    def hourly(self, cohort: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Not kept in memory: it is only needed to build window statistics, which are."""
        key = {"cohort": cohort, "hourly": self.fp(cohort, "hourly"), "v": VERSIONS["hourly"]}
        holder = {}

        def make_hourly():
            self.log(f"reading the {cohort} hourly file (once per data version)")
            h, codes, counts = read_hourly(self.paths.file(cohort, "hourly"))
            holder["codes"] = codes
            self.log(f"  {counts}")
            return h
        h = self.cache.get_or_build("hourly", key, make_hourly)
        codes = self.cache.get_or_build("hourly_codes", key, lambda: holder["codes"] if "codes" in holder else read_hourly(self.paths.file(cohort, "hourly"))[1])
        return h, codes

    def decisions(self, cohort: int, prob_scope: str = "marginal") -> pd.DataFrame:
        def build():
            if int(cohort) == 2024:
                mt = self.paths.file(2024, "message_types")
                key = {"cohort": 2024, "decisions": self.fp(2024, "decisions"), "message_types": self.fp(2024, "message_types") if mt.exists() else "",
                       "v": VERSIONS["decisions"]}
                return self.cache.get_or_build("decisions", key, lambda: ADAPTERS[2024](self.paths.file(2024, "decisions"), mt))
            key = {"cohort": 2025, "decisions": self.fp(2025, "decisions"), "timing": self.fp(2025, "timing"),
                   "prob_scope": prob_scope, "v": VERSIONS["decisions"]}
            return self.cache.get_or_build("decisions", key, lambda: ADAPTERS[2025](self.paths.file(2025, "decisions"),
                                                                                       self.paths.file(2025, "timing"), prob_scope))
        return self._memo(("decisions", int(cohort), prob_scope), build)

    def date_range(self, cohort: int):
        """First and last decision date in the cohort's analysis set (for the Run form)."""
        def build():
            d = self.decisions(cohort)
            d = d.loc[d["in_analysis"], "decision_date"].astype(str).str[:10]
            return [d.min(), d.max()] if len(d) else None
        return self._memo(("date_range", int(cohort)), build)

    def traits(self, cohort: int, extra: Tuple[str, ...] = ()) -> pd.DataFrame:
        extra = tuple(sorted(set(extra)))
        return self._memo(("traits", int(cohort), extra), lambda: baseline_traits(self.paths.file(cohort, "surveys"), extra))

    def survey_catalog(self, cohort: int) -> List[Dict]:
        """Baseline survey columns a moderator analysis can use, with the share of respondents who answered."""
        return self._memo(("survey_catalog", int(cohort)), lambda: survey_catalog(self.paths.file(cohort, "surveys")))

    @staticmethod
    def survey_moderators(spec: Dict) -> Tuple[str, ...]:
        """Moderators a spec names that come from the survey file rather than the wearable and mood history."""
        names = list(spec.get("moderator_sweep", [])) + list(spec.get("moderators", []))
        return tuple(sorted({m for m in names if m not in CONTEXT and m not in TRAITS}))

    def stats(self, spec: Dict) -> pd.DataFrame:
        cohort = int(spec["cohort"])
        keep = spec.get("keep", {})
        night = (keep.get("night_start_hour", 22), keep.get("night_end_hour", 7))
        win = {k: v for k, v in spec["window"].items() if k not in ("span_min", "span_max")}
        base = {k: v for k, v in self.inputs(cohort).items() if k != "message_types"}      # window statistics do not use message types
        key = {"cohort": cohort, "window": win, "night": list(night), "inputs": base, "v": VERSIONS["window_stats"]}

        def build():
            h, codes = self.hourly(cohort)
            dec = self.decisions(cohort, "marginal")
            self.log(f"building {cohort} window statistics for window {win} (once per window definition)")
            return window_stats(dec, h, codes, win, night[0], night[1])
        return self._memo(("stats", str(key)), lambda: self.cache.get_or_build("window_stats", key, build))

    def features(self, spec: Dict) -> pd.DataFrame:
        """Layer 2, memoized for the most recent settings (runs in a batch usually share them)."""
        stats = self.stats(spec)
        extra = self.survey_moderators(spec)
        key = (id(stats), str(sorted(spec.get("keep", {}).items())), spec.get("device", "combined"), spec.get("apple_source", ""),
               str(sorted(spec.get("window", {}).items())), spec.get("prob_scope", "marginal"), spec.get("date_from"), spec.get("date_to"), extra)
        if self._mem.get("features_key") == key:
            return self._mem["features_val"]
        val = apply_rules(stats, self.traits(int(spec["cohort"]), extra), spec.get("keep", {}), spec.get("device", "combined"),
                          spec.get("apple_source", "watch_then_phone"), spec.get("window", {}))
        dec = self.decisions(int(spec["cohort"]), spec.get("prob_scope", "marginal") if int(spec["cohort"]) == 2025 else "marginal")
        pcols = [c for c in dec.columns if c.startswith("p_")]
        val = val.drop(columns=[c for c in val.columns if c.startswith("p_")]).merge(dec[["decision_id"] + pcols], on="decision_id", how="left", validate="many_to_one")
        val = in_dates(val, spec.get("date_from"), spec.get("date_to"))
        self._mem["features_key"], self._mem["features_val"] = key, val
        return val
