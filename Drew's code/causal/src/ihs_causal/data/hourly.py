"""Hourly measurements: read the 25-column hourly file once into a compact, cached table.

Output (cached Parquet, one row per participant and UTC hour):
    pid_code (int32), hour (int64, hours since 1970-01-01 UTC), local_hour (int64 or -1),
    one float32 column per measurement, named <Device>_<stream> as in the source (Fitbit_steps, HealthkitWatch_hr_avg, ...)
    plus Mood (survey score; the source's 0 means "no response" and becomes missing).
Rows with no UTC time cannot enter UTC windows and are dropped (counted in the build log).
Where a file still has two rows for one UTC hour, they are combined: summed for steps and sleep minutes, averaged
for heart rate, resting heart rate and mood, maximum for maximum heart rate.
"""
from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.csv as pacsv

STREAM_AGG = {"steps": "sum", "sleep_minutes": "sum", "hr_avg": "mean", "hr_max": "max", "RHR": "mean"}
DEVICES = ["Fitbit", "Garmin", "HealthkitPhone", "HealthkitWatch", "HealthkitUnknown"]


def measurement_columns(columns) -> Dict[str, str]:
    """Map each measurement column to its aggregation rule."""
    out = {}
    for c in columns:
        if c == "Mood":
            out[c] = "mean"
            continue
        dev, _, stream = c.partition("_")
        if dev in DEVICES and stream in STREAM_AGG:
            out[c] = STREAM_AGG[stream]
    return out


def hours_from_timestamps(ts: pd.Series) -> np.ndarray:
    """Whole hours since 1970-01-01 of tz-naive timestamps, -1 where missing. Converts to nanoseconds first: pandas 2
    parses text to nanosecond resolution, pandas 3 to coarser units, so the raw integers differ between versions."""
    v = ts.to_numpy(dtype="datetime64[ns]")
    return np.where(np.isnat(v), -1, v.astype(np.int64) // 3_600_000_000_000).astype(np.int64)


def _hours_since_epoch(strings: pd.Series, utc: bool) -> np.ndarray:
    ts = pd.to_datetime(strings, format="ISO8601", utc=utc, errors="coerce")
    if utc:
        ts = ts.dt.tz_convert(None)
    return hours_from_timestamps(ts)


def read_hourly(path) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, int]]:
    """Returns (hourly table, participant code table, build counts)."""
    text_cols = {c: pa.string() for c in ("participant_id", "time_utc", "time_local")}
    table = pacsv.read_csv(str(path), convert_options=pacsv.ConvertOptions(strings_can_be_null=True, column_types=text_cols))
    df = table.to_pandas()
    rules = measurement_columns(df.columns)
    counts = {"rows_read": int(len(df))}
    hour = _hours_since_epoch(df["time_utc"].astype("string"), utc=True)
    local = _hours_since_epoch(df["time_local"].astype("string"), utc=False)
    keep = hour >= 0
    counts["rows_without_utc_dropped"] = int((~keep).sum())
    pids = pd.Categorical(df["participant_id"].astype("string"))
    out = pd.DataFrame({"pid_code": pids.codes.astype(np.int32), "hour": hour, "local_hour": local})
    for c in rules:
        v = pd.to_numeric(df[c], errors="coerce").astype("float32")
        if c == "Mood":
            v = v.where(v > 0)
        out[c] = v
    out = out[keep]
    dup = out.duplicated(["pid_code", "hour"], keep=False)
    counts["rows_in_repeated_utc_hours"] = int(dup.sum())
    if dup.any():
        single = out[~dup]
        agg = {c: rules[c] for c in rules}
        agg["local_hour"] = "min"
        multi = out[dup].groupby(["pid_code", "hour"], as_index=False).agg(agg)
        out = pd.concat([single, multi], ignore_index=True)
    out = out.sort_values(["pid_code", "hour"], kind="stable").reset_index(drop=True)
    counts["participant_hours"] = int(len(out))
    codes = pd.DataFrame({"pid_code": np.arange(len(pids.categories), dtype=np.int32), "participant_id": pids.categories.astype(str)})
    return out, codes, counts
