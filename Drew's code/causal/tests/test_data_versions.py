"""Stored results remember the data files that made them: older ones are flagged and redone, never silently kept."""
import json

import pandas as pd

from ihs_causal.results import ResultStore
from ihs_causal.viewer.build import build_payload


def _add(store, rid, cohort, inputs, value=1.0):
    table = pd.DataFrame({"run_id": [rid], "config_name": ["c"], "cohort": [cohort], "contrast_label": ["x"], "arm": ["a"],
                          "term": ["effect"], "question": ["Q1"], "estimate": [value], "se": [0.1], "ci_low": [value - 0.2],
                          "ci_high": [value + 0.2], "p": [0.5]})
    store.add(table, [], {"run_id": rid, "spec": {"run_id": rid, "cohort": cohort, "config_name": "c"}, "inputs": inputs})


def test_data_notes_follow_the_files_in_use(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "data_notes.yaml").write_text(
        '2025:\n  "abc123": note for file abc\n  "def456": note for file def\n2024: always shown\n', encoding="utf-8")
    cur = {2025: {"inputs": {"hourly": "abc123ff", "decisions": "99"}, "files": {}}, 2024: {"inputs": {"hourly": "x"}, "files": {}}}
    assert build_payload(None, tmp_path, current=cur)["notes"] == {"2025": "note for file abc", "2024": "always shown"}
    cur[2025]["inputs"]["hourly"] = "0000"
    assert build_payload(None, tmp_path, current=cur)["notes"] == {"2024": "always shown"}     # another file: no note


def test_older_data_is_flagged_by_cohort(tmp_path):
    store = ResultStore(tmp_path)
    _add(store, "r1", 2024, {"hourly": "old"})
    _add(store, "r2", 2024, {"hourly": "new"})
    _add(store, "r3", 2025, {"hourly": "x"})
    older = store.older_data({2024: {"hourly": "new"}})
    assert [m["run_id"] for m in older] == ["r1"]          # 2025 is not on this machine here, so never flagged
    assert {m["run_id"] for m in store.older_data({2024: {"hourly": "new"}, 2025: {"hourly": "y"}})} == {"r1", "r3"}


def test_rerun_replaces_the_result_and_its_manifest(tmp_path):
    store = ResultStore(tmp_path)
    _add(store, "r1", 2024, {"hourly": "old"}, value=1.0)
    _add(store, "r1", 2024, {"hourly": "new"}, value=2.0)
    assert store.estimates().estimate.tolist() == [2.0]
    lines = [json.loads(l) for l in store.runs_path.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 1 and lines[0]["inputs"] == {"hourly": "new"}
    assert store.older_data({2024: {"hourly": "new"}}) == []


def test_viewer_marks_older_runs(tmp_path):
    store = ResultStore(tmp_path)
    _add(store, "r1", 2024, {"hourly": "old"})
    _add(store, "r2", 2024, {"hourly": "new"})
    cur = {2024: {"inputs": {"hourly": "new"}, "files": {"hourly": "D:/x/dfHourly2024.csv"}}}
    p = build_payload(tmp_path, current=cur)
    assert {r["run_id"]: r["older_data"] for r in p["runs"]} == {"r1": True, "r2": False}
    assert p["current_inputs"]["2024"]["files"]["hourly"].endswith("dfHourly2024.csv")
    assert all(not r["older_data"] for r in build_payload(tmp_path)["runs"])     # without current files nothing is flagged


def test_cached_simultaneous_intervals_match_and_follow_reruns(tmp_path):
    import numpy as np
    from ihs_causal.results import _CRIT_CACHE, add_simultaneous
    rng = np.random.default_rng(5)
    store = ResultStore(tmp_path)
    for rid in ("r1", "r2"):
        table = pd.DataFrame({"run_id": rid, "config_name": "c", "contrast_label": "x", "arm": ["a", "b"], "term": "effect",
                              "estimate": [0.1, 0.2], "se": [0.05, 0.06]})
        infl = [("x", arm, "effect", np.arange(50), rng.normal(0, 0.3, 50)) for arm in ("a", "b")]
        store.add(table, infl, {"run_id": rid, "spec": {"run_id": rid}})
    est = store.estimates()
    _CRIT_CACHE.clear()
    full = add_simultaneous(est, store.influence(), ["run_id"])
    lazy = add_simultaneous(est, store.influence, ["run_id"])          # from the cache, reading nothing
    assert np.allclose(full.crit_simultaneous, lazy.crit_simultaneous) and (full.crit_simultaneous > 1.96).all()
    est.loc[est.run_id == "r1", "se"] = [0.5, 0.06]                    # a rerun changes the standard errors
    again = add_simultaneous(est, store.influence, ["run_id"])
    r1, r2 = again.run_id == "r1", again.run_id == "r2"
    assert not np.allclose(again.crit_simultaneous[r1], full.crit_simultaneous[r1])
    assert np.allclose(again.crit_simultaneous[r2], full.crit_simultaneous[r2])
