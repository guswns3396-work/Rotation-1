"""Build the single-file HTML results viewer from the results store.

The page is self-contained (no network access needed), so it can be opened from disk or e-mailed. It holds only
aggregate estimates and sample sizes; no participant-level values or identifiers are embedded.
"""
from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from ihs_causal import __version__
from ihs_causal.results import ResultStore, add_bh, add_simultaneous

TEMPLATE = Path(__file__).with_name("template.html")
FAMILY_COLS = ["config_name", "cohort", "device", "apple_source", "question", "estimator", "window", "keep", "prob_scope", "moderators",
               "min_prob", "positivity", "date_from", "date_to"]
KEEP = ["run_id", "config_name", "family", "label", "cohort", "question", "contrast", "contrast_label", "scope", "outcome", "arm",
        "reference", "term", "estimate", "se", "ci_low", "ci_high", "sim_low", "sim_high", "p", "n_rows", "n_participants",
        "n_arm", "n_reference", "sd_reference_outcome", "estimator", "learner", "window", "keep", "device", "apple_source",
        "prob_scope", "moderators", "seconds", "q_bh", "moderator_sd", "n_rows_moderator", "min_prob", "min_arm_rows", "positivity",
        "date_from", "date_to"]


def _clean(v):
    if isinstance(v, (float, np.floating)):
        return None if not math.isfinite(float(v)) else round(float(v), 6)
    if isinstance(v, (np.integer,)):
        return int(v)
    return v


def build_payload(results_dir: Path, project_dir: Path = None, mode: str = "static", current: dict = None) -> dict:
    """Everything the page shows: estimates (aggregates only), run settings, diagnostics and the data notes.
    `current` ({cohort: {"inputs": {kind: SHA-256}, "files": {kind: path}}}, from Workspace.current_inputs) lets the page
    flag runs made from older data files and list the files in use."""
    cur = {int(c): v["inputs"] for c, v in (current or {}).items()}
    store = ResultStore(results_dir) if results_dir is not None else None     # None: the app before a data folder is chosen
    stamp = store.stamp() if store else "none"   # read first: a result stored while this payload is built changes it, so the page refetches
    est = store.estimates() if store else pd.DataFrame()
    rows, runs, diags = [], [], []
    if not est.empty:
        est = est.copy()
        # runs stored before the floor was recorded used the defaults
        for c, v in (("min_prob", 1e-3), ("min_arm_rows", 200), ("positivity", "joint")):
            est[c] = est[c].fillna(v) if c in est else v
        for c in FAMILY_COLS:
            if c not in est:
                est[c] = ""
            est[c] = est[c].fillna("").astype(str)
        est = add_simultaneous(est, store.influence, FAMILY_COLS)      # reads only the influence rows it needs
        est = add_bh(est)
        cols = [k for k in KEEP if k in est.columns]
        rows = [{k: _clean(v) for k, v in zip(cols, vals)} for vals in est[cols].itertuples(index=False, name=None)]
    if store and store.runs_path.exists():
        latest = {}
        for line in store.runs_path.read_text(encoding="utf-8").splitlines():
            m = json.loads(line)
            latest[m["run_id"]] = m
        for m in latest.values():
            spec = m.get("spec", {})
            runs.append({"run_id": m["run_id"], "config_name": spec.get("config_name"), "cohort": spec.get("cohort"), "device": spec.get("device"),
                         "apple_source": spec.get("apple_source"), "family": spec.get("family", ""), "label": spec.get("label", ""),
                         "outcome": spec.get("outcome"), "contrast": spec.get("contrast"), "inputs": m.get("inputs", {}),
                         "moderators": spec.get("moderator_sweep", []),
                         "older_data": int(spec.get("cohort", 0)) in cur and m.get("inputs") != cur[int(spec.get("cohort", 0))],
                         "seconds_features": m.get("seconds_features"), "package_version": m.get("package_version")})
            for d in m.get("diagnostics", []):
                diags.append({"run_id": m["run_id"], "config_name": spec.get("config_name"), "cohort": spec.get("cohort"), "device": spec.get("device"),
                              "apple_source": spec.get("apple_source"), "outcome": spec.get("outcome"), "positivity": spec.get("positivity", "joint"),
                              **{k: _clean(v) if not isinstance(v, (dict, list)) else v for k, v in d.items()}})
    notes = {}
    notes_path = (Path(project_dir) / "config" / "data_notes.yaml") if project_dir else None
    if notes_path and notes_path.exists():
        import yaml
        for k, v in (yaml.safe_load(notes_path.read_text(encoding="utf-8")) or {}).items():
            if isinstance(v, dict):     # notes about particular files, keyed by the start of their SHA-256
                fps = list(cur.get(int(k), {}).values())
                hit = [str(text) for prefix, text in v.items() if any(fp.startswith(str(prefix)) for fp in fps)]
                if hit:
                    notes[str(k)] = " ".join(hit)
            elif v:
                notes[str(k)] = v
    from ihs_causal.config import defaults
    return {"generated": datetime.now().astimezone().isoformat(timespec="minutes"), "version": __version__, "mode": mode,
            "results_stamp": stamp, "estimates": rows, "runs": runs, "diagnostics": diags, "notes": notes, "defaults": defaults(),
            "current_inputs": {str(c): v for c, v in (current or {}).items()}}


def render_html(payload: dict) -> str:
    text = json.dumps(payload, default=str, separators=(",", ":")).replace("</", "<\\/")
    return TEMPLATE.read_text(encoding="utf-8").replace("/*__DATA__*/null", text)


def build_viewer(results_dir: Path, out: Path, project_dir: Path = None, current: dict = None) -> None:
    payload = build_payload(results_dir, project_dir, mode="static", current=current)
    if not payload["estimates"]:
        raise SystemExit("no results yet; run a configuration first")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_html(payload), encoding="utf-8")
