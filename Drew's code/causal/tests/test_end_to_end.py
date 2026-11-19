"""The whole pipeline on fake copies of the shared files: setup, check, reproduce, the snapshot. No study data needed,
so a fresh checkout can confirm it works before it is pointed at the real files."""
import json

import pandas as pd
import pytest

from fake_shared_files import make_project, write_shared_files
from ihs_causal.cli import main
from ihs_causal.config import iter_specs


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    root = tmp_path_factory.mktemp("e2e")
    proj, shared = make_project(root), write_shared_files(root / "shared")
    with pytest.MonkeyPatch.context() as mp:
        mp.chdir(proj)
        yield proj, shared


def test_setup_writes_paths_and_check_reads_headers(project, capsys):
    proj, shared = project
    # the example reads the hourly files from dated copies this folder does not have: setup falls back, with a note
    assert main(["setup", str(shared)]) == 0
    out = capsys.readouterr().out
    assert "Hourly_MoodCorrected_20261117/dfHourly2025.csv is not in this folder" in out
    text = (proj / "config" / "paths.yaml").read_text(encoding="utf-8")
    assert f'data_root: "{shared.resolve().as_posix()}"' in text and "files:" not in text
    assert "2025: ready" in out and "2024: ready (without the optional files" in out
    assert "sha256" in out and "FAKE20" not in out      # column names and fingerprints only, never values
    assert main(["check", "--no-hash"]) == 0
    capsys.readouterr()
    assert main(["setup", str(shared)]) == 1             # an existing paths.yaml is kept without --force
    assert "already exists" in capsys.readouterr().out


def test_setup_keeps_files_the_folder_has(tmp_path, monkeypatch):
    proj, shared = make_project(tmp_path), write_shared_files(tmp_path / "shared", n_people=4, n_days=7)
    (shared / "Hourly_MoodCorrected_20261117").mkdir()
    (shared / "dfHourly2025.csv").rename(shared / "Hourly_MoodCorrected_20261117" / "dfHourly2025.csv")
    monkeypatch.chdir(proj)
    main(["setup", str(shared)])
    text = (proj / "config" / "paths.yaml").read_text(encoding="utf-8")
    assert 'hourly: "Hourly_MoodCorrected_20261117/dfHourly2025.csv"' in text and "2024:" not in text
    from ihs_causal.paths import load_paths
    assert load_paths().file(2025, "hourly") == shared.resolve() / "Hourly_MoodCorrected_20261117" / "dfHourly2025.csv"


def test_reproduce_runs_every_cohort_and_builds_the_snapshot(project, capsys):
    proj, shared = project
    if not (proj / "config" / "paths.yaml").exists():
        pytest.skip("needs test_setup_writes_paths_and_check_reads_headers")
    pipeline = str(proj / "config" / "e2e_pipeline.yaml")
    assert main(["reproduce", "--pipeline", pipeline]) == 0
    out = capsys.readouterr().out
    assert "2025: 9 analyses" in out and "2024: 2 analyses" in out
    results = proj / "work" / "results"
    est = pd.read_parquet(results / "estimates.parquet")
    for cohort in (2025, 2024):
        r = est[(est.cohort == cohort) & (est.contrast == "any_vs_none") & (est.outcome == "steps") & (est.device == "combined")
                & (est.term == "effect") & (est.estimator == "drwcls")].iloc[0]
        assert abs(r.estimate - 0.3) < 4 * r.se, (cohort, r.estimate, r.se)       # the effect built into the fake files
    # message types: 2025 estimates nine types; 2024 has no message-type file, so that run is recorded as empty
    assert est[(est.cohort == 2025) & (est.contrast == "type_vs_none") & (est.term == "effect")].arm.nunique() == 9
    empty = json.loads((results / "empty_runs.json").read_text(encoding="utf-8"))
    types_2024 = next(s["run_id"] for s in iter_specs(proj / "config" / "e2e_2024.yaml") if s["contrast"] == "type_vs_none")
    assert types_2024 in empty and types_2024 not in set(est.run_id)
    # who responds: the survey column is estimated; 2025 has no neuroticism score, so it is reported as not estimated
    q6 = est[est.config_name == "e2e_q6_2025"]
    assert {"mod:sleepAve0", "mod:PHQtot0", "mod:Mood_pre"} <= set(q6.term)
    assert "mod:Neu0_published" not in set(q6.term)
    runs = [json.loads(l) for l in (results / "runs.jsonl").read_text(encoding="utf-8").splitlines()]
    q6_diag = next(m for m in runs if m["spec"]["config_name"] == "e2e_q6_2025")["diagnostics"][0]
    assert "Neu0_published" in q6_diag["moderators_skipped"]
    # the snapshot holds aggregates only: person-level effects stay in the local store
    html = (proj / "work" / "ihs_causal_results.html").read_text(encoding="utf-8")
    assert "FAKE2025-" not in html and "FAKE2024-" not in html
    assert (results / "person_effects.parquet").exists()
    # a second run has nothing to do, including the run that had nothing to estimate
    assert main(["reproduce", "--pipeline", pipeline, "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "2025: 9 analyses" in out and "0 to run, 9 already stored" in out and "0 to run, 2 already stored" in out
