"""Run a configuration: every run x every contrast item -> estimates, stored with full provenance.

Results live in <work_dir>/results/:
  estimates.parquet   one row per (run, contrast item, arm, term): estimate, se, CI, p, sample sizes, settings
  influence.parquet   per-participant influence contributions of every estimate (for simultaneous intervals)
  runs.jsonl          one line per run: settings, input fingerprints, package version, timings, diagnostics
A run whose run_id is already stored from the same input files is skipped unless force=True. A run stored from other
files (a data file was updated since) is redone and replaces the earlier result; `stale_specs` lists every such run.
"""
from __future__ import annotations

import contextlib
import json
import time
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from ihs_causal import __version__
from ihs_causal.design.contrasts import CONTRASTS
from ihs_causal.estimators import ESTIMATORS
from ihs_causal.results import ResultStore
from ihs_causal.workspace import Workspace

SETTING_COLUMNS = ["cohort", "outcome", "contrast", "device", "apple_source", "prob_scope"]


def standard_specs(plan_path) -> Dict[int, Tuple[List[str], List[Dict]]]:
    """The standing analyses of a pipeline file (config/pipeline.yaml): {cohort: (configuration files, runs)}."""
    from pathlib import Path
    from ihs_causal.config import iter_specs, load_yaml
    plan_path = Path(plan_path)
    out: Dict[int, Tuple[List[str], List[Dict]]] = {}
    for c, files in (load_yaml(plan_path) or {}).items():
        files = list(files or [])
        specs = [s for f in files for s in iter_specs(plan_path.parent / f)]
        other = sorted({str(s["cohort"]) for s in specs if int(s["cohort"]) != int(c)})
        if other:
            raise ValueError(f"{plan_path.name} lists configurations for cohort {', '.join(other)} under {c}")
        out[int(c)] = (files, specs)
    return out


def _empty_key(inputs: Dict) -> Dict:
    """What a 'nothing to estimate' record is tied to: the input files and the package version, so a fixed release
    tries such runs again."""
    return {"inputs": inputs, "package": __version__}


def pending_specs(specs: List[Dict], ws: Workspace, force: bool = False) -> List[Dict]:
    """The runs `run_specs` computes: every run with force, else those not stored from the current input files (a run
    that had nothing to estimate on the current files, with this package version, counts as stored)."""
    if force:
        return list(specs)
    store = ResultStore(ws.paths.results_dir)
    done = store.run_ids()
    stored_inputs = {rid: m.get("inputs") for rid, m in store.manifests().items()}
    empty = store.empty_runs()
    current: Dict[int, Dict[str, str]] = {}
    out = []
    for spec in specs:
        cohort, rid = int(spec["cohort"]), spec["run_id"]
        if cohort not in current:
            current[cohort] = ws.inputs(cohort)
        if not ((rid in done and stored_inputs.get(rid) == current[cohort]) or empty.get(rid) == _empty_key(current[cohort])):
            out.append(spec)
    return out


def run_specs(specs: List[Dict], ws: Workspace, force: bool = False, log=print, lock=None, on_stored=None) -> pd.DataFrame:
    """`lock` (the app's) is held while the store is written, so a reader never sees a half-written file;
    `on_stored(run_id)` is called after each run is stored, or recorded as having nothing to estimate."""
    store = ResultStore(ws.paths.results_dir)
    lock = lock or contextlib.nullcontext()
    todo = {id(s) for s in pending_specs(specs, ws, force)}
    current: Dict[int, Dict[str, str]] = {}
    tables = []
    for i, spec in enumerate(specs, 1):
        rid = spec["run_id"]
        cohort = int(spec["cohort"])
        if cohort not in current:
            current[cohort] = ws.inputs(cohort)
        if id(spec) not in todo:
            continue
        t0 = time.perf_counter()
        df = ws.features(spec)
        t_feat = time.perf_counter() - t0
        est_spec = dict(spec["estimator"])
        name = est_spec.pop("name")
        items_out, infl_out, diag_out, person_out, item_secs = [], [], [], [], []
        for label, question, scope, frame, info in CONTRASTS.get(spec["contrast"])(df, spec["outcome"], spec):
            if frame.n == 0 or frame.n_arms == 0:
                diag_out.append({"contrast_label": label, **info, "skipped": "no rows or no arms"})
                continue
            t1 = time.perf_counter()
            est = ESTIMATORS.get(name)(frame, features=getattr(frame, "features", None), **est_spec)
            tab = est.table.copy()
            ref_y = frame.y[frame.arm == 0]
            tab["sd_reference_outcome"] = float(ref_y.std()) if ref_y.size > 1 else np.nan
            tab["contrast_label"], tab["question"], tab["scope"] = label, question, scope
            tab["seconds"] = time.perf_counter() - t1
            item_secs.append(float(tab["seconds"].iloc[0]))
            items_out.append(tab)
            for (arm, term), (clusters, vec) in est.influence.items():
                infl_out.append((label, arm, term, clusters, vec))
            pe = est.diagnostics.pop("person_effects", None)
            if pe is not None:
                pe = pe.assign(contrast_label=label)
                person_out.append(pe)
            diag_out.append({"contrast_label": label, **info, **{k: v for k, v in est.diagnostics.items()}})
        if not items_out:
            with lock:
                store.mark_empty(rid, _empty_key(current[cohort]))
            if on_stored:
                on_stored(rid)
            log(f"[{i}/{len(specs)}] {spec['config_name']} {rid}: nothing estimable"); continue
        tab = pd.concat(items_out, ignore_index=True)
        tab.insert(0, "run_id", rid)
        tab.insert(1, "config_name", spec["config_name"])
        for c in SETTING_COLUMNS:
            tab[c] = spec.get(c)
        tab["estimator"] = name
        tab["learner"] = spec["estimator"].get("learner", "")
        tab["window"] = json.dumps(spec["window"], sort_keys=True)
        tab["keep"] = json.dumps(spec.get("keep", {}), sort_keys=True)
        tab["moderators"] = ",".join(spec.get("moderators", []))
        tab["date_from"] = spec.get("date_from") or ""
        tab["date_to"] = spec.get("date_to") or ""
        tab["min_prob"] = float(spec.get("min_prob", 1e-3))
        tab["min_arm_rows"] = int(spec.get("min_arm_rows", 200))
        tab["positivity"] = spec.get("positivity", "joint")      # runs stored before the setting existed used joint
        tab["label"] = spec.get("label", "")
        tab["family"] = spec.get("family", "")
        with lock:
            if person_out:
                store.add_person_effects(rid, pd.concat(person_out, ignore_index=True))
            store.add(tab, infl_out, {"run_id": rid, "spec": spec, "package_version": __version__,
                                      "seconds_features": round(t_feat, 2), "diagnostics": diag_out,
                                      "inputs": current[cohort]})
        if on_stored:
            on_stored(rid)
        tables.append(tab)
        log(f"[{i}/{len(specs)}] {spec['config_name']} {spec['cohort']} {spec.get('device', ''):<8} {spec['outcome']:>5} {spec['contrast']:<20} "
            f"{len(tab):>3} estimates in {sum(item_secs):.2f}s (features {t_feat:.1f}s)")
    return pd.concat(tables, ignore_index=True) if tables else pd.DataFrame()


def stale_specs(ws: Workspace) -> List[Dict]:
    """Stored analyses made from other input files than the current ones, with their settings, ready to rerun.
    Ordered so that runs sharing a cohort, window and keep rules follow each other (their tables are built once)."""
    store = ResultStore(ws.paths.results_dir)
    current = {c: v["inputs"] for c, v in ws.current_inputs().items()}
    specs = []
    for m in store.older_data(current):
        s = dict(m["spec"])
        s.setdefault("positivity", "joint")     # stored before the setting existed: those runs checked every arm at once
        specs.append(s)
    return sorted(specs, key=lambda s: (int(s["cohort"]), json.dumps(s.get("window"), sort_keys=True),
                                        json.dumps(s.get("keep", {}), sort_keys=True), str(s.get("prob_scope")), s["config_name"]))
