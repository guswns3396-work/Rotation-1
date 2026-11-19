"""`ihs-causal check`: are the shared files where config/paths.yaml says, with the columns the engine reads?

Reads column names only, never values, so its output holds no participant data and can be pasted anywhere. For each
file it reports where it is, any columns missing, and the start of its SHA-256. The About tab and every stored result
record the same fingerprints, so two machines can confirm they analyse the same files.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

from ihs_causal.data.decisions import ARMS, DOMAINS, STRATEGIES
from ihs_causal.data.features import TRAITS
from ihs_causal.data.hourly import measurement_columns
from ihs_causal.paths import Paths, fingerprint

_ARM_P = [f"p_{a}" for a in ARMS]
# kind -> (required columns, {optional column: what it is for}); one entry per file the engine reads
NEEDS: Dict[int, Dict[str, tuple]] = {
    2024: {
        "hourly": (["participant_id", "time_utc", "time_local"], {"Mood": "mood outcomes"}),
        "decisions": (["decision_id", "participant_id", "decision_date", "hour_utc", "action_sent", "domain", "strategy",
                       "personalization", "core_message_id", "time_source", "p_send", "p_no_send"] + _ARM_P
                      + [f"p_{d}" for d in DOMAINS] + [f"p_{d}_{s}" for d in DOMAINS for s in STRATEGIES], {}),
        "surveys": (["PARTICIPANTIDENTIFIER"], {t: "baseline traits" for t in TRAITS}),
        "message_types": (["decision_id"] + [f"p_{d}_{a}" for d in DOMAINS for a in ARMS], {}),
    },
    2025: {
        "hourly": (["participant_id", "time_utc", "time_local"], {"Mood": "mood outcomes"}),
        "decisions": (["decision_id", "participant_id", "decision_date", "action_sent", "decision_domain", "action_label",
                       "p_marginal_no_send"] + [f"p_marginal_{a}" for a in ARMS],
                      {c: "prob_scope: selected" for c in ["p_no_send"] + _ARM_P}),
        "timing": (["decision_id", "window_anchor_utc", "retain_main_reach_retrospective", "message_domain", "core_message_id"], {}),
        "surveys": (["PARTICIPANTIDENTIFIER"], {t: "baseline traits" for t in TRAITS}),
    },
}
# files a cohort can run without; what is missing without them
OPTIONAL_FILES = {(2024, "message_types"): "the 2024 message-type questions (type_vs_none) have nothing to estimate"}


def _check_file(path: Path, required: List[str], optional: Dict[str, str], kind: str) -> Dict:
    r = {"exists": path.exists(), "missing": [], "notes": []}
    if not r["exists"]:
        return r
    try:
        cols = list(pd.read_csv(path, nrows=0).columns)       # the header only
    except Exception as e:      # noqa: BLE001 - reported, not raised
        r["missing"] = [f"not readable as CSV ({type(e).__name__})"]
        return r
    r["missing"] = [c for c in required if c not in cols]
    gaps: Dict[str, List[str]] = {}
    for c, why in optional.items():
        if c not in cols:
            gaps.setdefault(why, []).append(c)
    for why, names in gaps.items():
        r["notes"].append(f"no {', '.join(names)} ({why})")
    if kind == "hourly":
        n = sum(1 for c in measurement_columns(cols) if c != "Mood")
        if n == 0:
            r["missing"].append("device columns such as Fitbit_steps or HealthkitWatch_hr_avg")
        else:
            r["notes"].append(f"{n} device measurement columns")
    return r


def check_files(paths: Paths, cohorts: Iterable[int] = (2024, 2025), hashes: bool = True) -> Dict[int, Dict]:
    """For each cohort: every file's location, missing columns and fingerprint, and whether the cohort can run.
    A cohort is `ready` when every file it needs is present with the columns the engine reads."""
    out: Dict[int, Dict] = {}
    for c in cohorts:
        files = []
        for kind, (required, optional) in NEEDS[int(c)].items():
            p = paths.file(c, kind)
            r = {"kind": kind, "path": p, "optional": (int(c), kind) in OPTIONAL_FILES, "sha256": "",
                 **_check_file(p, required, optional, kind)}
            if hashes and r["exists"] and not r["missing"]:
                r["sha256"] = fingerprint(p, paths.work_dir / "fingerprints.json")
            files.append(r)
        needed = [f for f in files if not f["optional"]]
        broken = [f for f in files if f["exists"] and f["missing"]]
        absent = [f for f in needed if not f["exists"]]
        if not any(f["exists"] for f in needed):
            status = "not on this machine"
        elif absent or broken:
            status = "cannot run: " + "; ".join([f"{f['kind']} file not found" for f in absent]
                                                + [f"{f['kind']} file lacks {', '.join(f['missing'][:4])}"
                                                   + (" ..." if len(f["missing"]) > 4 else "") for f in broken])
        else:
            status = "ready"
            gone = [OPTIONAL_FILES[(int(c), f["kind"])] for f in files if f["optional"] and not f["exists"]]
            if gone:
                status += " (without the optional files: " + "; ".join(gone) + ")"
        out[int(c)] = {"files": files, "ready": status.startswith("ready"), "status": status}
    return out


def _show(p: Path, data_root: Path) -> str:
    """A file's path relative to the data folder when it is inside it."""
    try:
        return Path(p).resolve().relative_to(Path(data_root).resolve()).as_posix()
    except ValueError:
        return str(p)


def _state(f: Dict) -> str:
    if not f["exists"]:
        return "optional, not found" if f["optional"] else "NOT FOUND"
    return "MISSING COLUMNS" if f["missing"] else "ok"


def report_json(report: Dict[int, Dict], data_root: Path) -> Dict[str, Dict]:
    """The report for the app's setup page: per cohort, its status and each file's state."""
    return {str(c): {"ready": r["ready"], "status": r["status"],
                     "files": [{"kind": f["kind"], "state": _state(f), "path": _show(f["path"], data_root), "missing": f["missing"],
                                "notes": f["notes"], "optional": f["optional"]} for f in r["files"]]}
            for c, r in report.items()}


def format_report(report: Dict[int, Dict], data_root: Path) -> str:
    lines = [f"data_root: {data_root}"]
    for c, rep in report.items():
        lines.append(f"\n{c}: {rep['status']}")
        for f in rep["files"]:
            line = f"  {f['kind']:<14}{_state(f):<20}{_show(f['path'], data_root)}"
            if f["sha256"]:
                line += f"   sha256 {f['sha256'][:12]}"
            lines.append(line)
            if f["missing"]:
                lines.append(f"  {'':<14}lacks: {', '.join(f['missing'])}")
            for n in f["notes"]:
                lines.append(f"  {'':<14}{n}")
    return "\n".join(lines)
