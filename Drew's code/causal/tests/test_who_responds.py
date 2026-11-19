"""Who responds from the Run form: any question, any characteristic, saved analyses kept apart; baseline survey columns."""
import numpy as np
import pandas as pd
import pytest

from ihs_causal.data.features import baseline_traits, is_baseline_column, survey_catalog
from ihs_causal.estimators.hetero import drwcls_hetero
from ihs_causal.serve import specs_from_form
from ihs_causal.simulate import simulate_mrt


def test_who_responds_runs_for_every_chosen_question_with_the_chosen_characteristics():
    specs = specs_from_form({"cohort": 2025, "label": "types", "questions": ["QT", "Q3"], "outcomes": ["sleep"], "who": True,
                             "moderators": ["Mood_pre", "PHQtot0"], "extra_moderators": "hours0, sleepAve0",
                             "min_prob": "0.01", "keep": None}, survey_columns={"hours0", "sleepAve0"})
    main = [s for s in specs if s["family"] == ""]
    who = [s for s in specs if s["family"] == "q6-custom"]
    assert sorted(s["contrast"] for s in main) == sorted(s["contrast"] for s in who) == ["data_vs_nodata", "data_within_strategy", "type_vs_none"]
    for s in who:
        assert s["estimator"]["name"] == "drwcls_hetero"
        assert s["moderator_sweep"] == ["Mood_pre", "PHQtot0", "hours0", "sleepAve0"]
        assert s["baseline_traits"] == ["PHQtot0", "hours0", "sleepAve0"]       # context the day before is not a trait
        assert s["min_prob"] == 0.01 and s["config_name"] == "types (Q6)"


def test_who_responds_alone_uses_any_message_and_domains():
    specs = specs_from_form({"cohort": 2024, "questions": ["Q6"], "outcomes": ["mood"]})       # the older page's way of asking
    assert sorted({s["contrast"] for s in specs if s["family"] == "q6-custom"}) == ["any_vs_none", "domain_vs_none"]


def test_saved_analyses_with_the_same_settings_are_stored_apart():
    a = specs_from_form({"cohort": 2025, "label": "first", "questions": ["Q1"], "outcomes": ["sleep"]})
    b = specs_from_form({"cohort": 2025, "label": "second", "questions": ["Q1"], "outcomes": ["sleep"]})
    again = specs_from_form({"cohort": 2025, "label": "first", "questions": ["Q1"], "outcomes": ["sleep"]})
    assert a[0]["run_id"] != b[0]["run_id"]
    assert a[0]["run_id"] == again[0]["run_id"]        # rerunning a saved analysis under its own name replaces it


def test_typed_characteristics_must_be_baseline_survey_columns():
    with pytest.raises(ValueError, match="Follow-up"):
        specs_from_form({"cohort": 2025, "questions": ["Q1"], "who": True, "extra_moderators": "PHQtot2"}, survey_columns={"hours0"})
    with pytest.raises(ValueError, match="not a baseline survey column"):
        specs_from_form({"cohort": 2025, "questions": ["Q1"], "who": True, "extra_moderators": "nosuch0"}, survey_columns={"hours0"})
    with pytest.raises(ValueError, match="at least one"):
        specs_from_form({"cohort": 2025, "questions": ["Q1"], "who": True, "moderators": []})


def test_baseline_columns():
    for name in ["PHQtot0", "Neu0_published", "stress3_0", "mspss10_0", "medication0_Antidepressants", "hours0", "Age", "Sex", "deprAge", "AgeMoveUS"]:
        assert is_baseline_column(name), name
    for name in ["PHQtot2", "stress10_1", "mspss10_3", "SLE4", "survey_record_present0", "caffeine0_OtherTEXT", "caffeine0_selections", "Year", "anxious"]:
        assert not is_baseline_column(name), name


def test_survey_catalog_and_extra_traits(tmp_path):
    p = tmp_path / "s.csv"
    pd.DataFrame({"PARTICIPANTIDENTIFIER": ["a", "b", "c", "d"], "Age": ["30", "31", "", "40"], "Sex": ["1", "2", "2", "1"],
                  "hours0": ["60", "70", "", ""], "hours2": ["50", "40", "30", "20"], "clerk0": ["1", "1", "1", "1"]}).to_csv(p, index=False)
    cat = {c["name"]: c["coverage"] for c in survey_catalog(p)}
    assert cat == {"Age": 0.75, "Sex": 1.0, "hours0": 0.5}          # follow-up and single-valued columns are left out
    t = baseline_traits(p, extra=("hours0",))
    assert t["hours0"].tolist()[:2] == [60.0, 70.0] and t["Sex"].tolist() == [0.0, 1.0, 1.0, 0.0]
    assert t["PHQtot0"].isna().all()                                 # a standard trait the file lacks is an empty column


def test_hetero_reports_characteristics_it_could_not_use():
    frame, _ = simulate_mrt(n_people=200, n_decisions=60, seed=3)
    z = frame.extra["z"]
    empty = np.full(frame.n, np.nan)
    frame.sweep_values = np.column_stack([z, empty, np.ones(frame.n)])
    frame.sweep_names = ["z", "Neu0_published", "constant"]
    frame.baseline_traits = ["z"]
    frame.time_index = np.tile(np.arange(60), 200)
    est = drwcls_hetero(frame, bootstrap=20, permutations=50)
    assert set(est.table.term) >= {"effect", "mod:z"} and "mod:Neu0_published" not in set(est.table.term)
    assert set(est.diagnostics["moderators_skipped"]) == {"Neu0_published", "constant"}
