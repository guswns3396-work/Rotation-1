"""Settings: run ids stay stable when an optional setting is unset; the date range; the Run form's checks."""
import pandas as pd
import pytest

from ihs_causal.config import expand, run_id
from ihs_causal.data.features import in_dates
from ihs_causal.serve import specs_from_form


def test_unset_settings_do_not_change_the_run_id():
    spec = expand({"name": "x", "base": {"cohort": 2025, "outcome": "sleep"}})[0]
    assert spec["date_from"] is None and spec["date_to"] is None
    without = {k: v for k, v in spec.items() if k not in ("date_from", "date_to")}
    assert run_id(spec) == run_id(without)
    dated = {**spec, "date_from": "2025-12-01"}
    assert run_id(dated) != run_id(spec)


def test_date_range_is_inclusive_and_open_ended():
    df = pd.DataFrame({"decision_date": ["2025-11-30", "2025-12-01", "2026-01-15", "2026-03-01"], "x": range(4)})
    assert in_dates(df, "2025-12-01", "2026-01-15").x.tolist() == [1, 2]
    assert in_dates(df, "2026-01-15", None).x.tolist() == [2, 3]
    assert in_dates(df, None, "2025-12-01").x.tolist() == [0, 1]
    assert in_dates(df).x.tolist() == [0, 1, 2, 3]


def test_run_form_dates():
    specs = specs_from_form({"cohort": 2025, "questions": ["Q1"], "outcomes": ["sleep"], "date_from": "2025-12-01", "date_to": "2026-02-28"})
    assert {(s["date_from"], s["date_to"]) for s in specs} == {("2025-12-01", "2026-02-28")}
    blank = specs_from_form({"cohort": 2025, "questions": ["Q1"], "outcomes": ["sleep"], "date_from": "", "date_to": ""})
    assert all(s["date_from"] is None and s["date_to"] is None for s in blank)
    with pytest.raises(ValueError):
        specs_from_form({"cohort": 2025, "questions": ["Q1"], "date_from": "12/01/2025"})
    with pytest.raises(ValueError):
        specs_from_form({"cohort": 2025, "questions": ["Q1"], "date_from": "2026-02-01", "date_to": "2025-12-01"})
