"""Hours since 1970 must not depend on the resolution pandas parses timestamps to: pandas 2 gives nanoseconds, pandas 3
coarser units. Reading the raw integers as nanoseconds put every row of an hourly file into a handful of hours under
pandas 3, so every analysis came out empty (found on a fresh install, 2026-11-19)."""
import numpy as np
import pandas as pd
import pytest

from ihs_causal.data.decisions import _hour
from ihs_causal.data.hourly import _hours_since_epoch, hours_from_timestamps

TEXT = ["2025-08-04T14:00:00Z", "2025-08-04T14:59:59Z", "2025-08-05T00:30:00Z", None]
EXPECTED = [487310, 487310, 487320, -1]          # 2025-08-04 14:00 UTC is second 1,754,316,000: hour 487,310


@pytest.mark.parametrize("unit", ["s", "ms", "us", "ns"])
def test_hours_are_the_same_at_every_resolution(unit):
    ts = pd.to_datetime(pd.Series(TEXT), utc=True, format="ISO8601").dt.tz_convert(None).dt.as_unit(unit)
    assert hours_from_timestamps(ts).tolist() == EXPECTED


def test_hourly_and_decision_readers():
    assert _hours_since_epoch(pd.Series(TEXT, dtype="string"), utc=True).tolist() == EXPECTED
    assert _hour(pd.Series(TEXT, dtype=object)).tolist() == EXPECTED
    local = pd.Series(["2025-08-04T14:00:00", "garbled"], dtype="string")
    assert _hours_since_epoch(local, utc=False).tolist() == [487310, -1]
    assert hours_from_timestamps(pd.Series(pd.to_datetime(["1970-01-01 01:00"]))).dtype == np.int64
