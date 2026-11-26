"""The analysis table, built in two layers so that changing a keep rule or a device costs milliseconds.

Layer 1, window statistics (window_stats; cached on disk per cohort and window definition)
    For every decision's post and pre window and every instrument: summed steps, hours the device was observed,
    observed hours overnight, mean heart rate, mean resting heart rate, summed sleep minutes and hours with sleep; and
    mood mean, SD and count. Built once with prefix sums, one instrument at a time to keep memory low.

Layer 2, keep rules and device choice (apply_rules; recomputed on demand)
    Outcomes and history covariates for the chosen device under the chosen keep rules.

Instruments
    fitbit, garmin           the device's own columns
    apple                    Apple Watch for each hour, else the iPhone (and, for sleep, else Apple sleep of unknown source)
    apple_watch              Apple Watch only
An hour is observed for an instrument when it has a heart-rate value or a positive step count (a zero step cell is not
evidence of wear: Garmin writes zeros in every hour). For an iPhone without a watch the only evidence is steps, so for
those people "observed" means "has steps".

Keep rules (all parameters live under `keep:` in the configuration)
    steps   kept when the window has at least `steps_min_observed_hours` observed hours; a blank step cell in an observed
            hour counts as zero. Outcome: log(1 + steps).
    sleep   the unit is the night: kept when a sleep record exists in the window. A night shorter than
            `sleep_short_night_minutes` is kept only if the device was observed for at least `sleep_night_wear_min` of the
            overnight hours (`night_start_hour` to `night_end_hour`, local time). No record means missing, not zero.
            Outcome: minutes asleep.
    mood    kept when the window holds a response. Outcome: mean response.
    every   the window must be a day long: its span lies in [span_min, span_max] hours (default 20 to 28).

Devices
    combined    each person contributes their main instrument: the one among Fitbit, Garmin and Apple with the most observed
                hours in their post windows. Mood is kept for everyone, including people without a wearable.
    fitbit, garmin, apple
                that instrument for everyone who has it (at least one observed hour); mood is restricted to those people,
                so a device view describes one group of participants.
    apple_source  `watch_then_phone` (default) or `watch_only` chooses which Apple instrument is used.
"""
from __future__ import annotations

import re
from typing import Dict, List

import numpy as np
import pandas as pd

from ihs_causal.data.windows import WINDOWS, WindowAggregator

BASELINE = ["Age", "Sex", "depr0", "PHQtot0", "GADtot0", "Neu0_published", "SLE0"]
TRAITS = BASELINE + ["EFE0"]
INSTRUMENTS = ["fitbit", "garmin", "apple", "apple_watch"]
OUTCOMES = {"mood": "Mood_post", "steps": "log_steps_post", "sleep": "sleep_minutes_post"}
# history covariates built from the wearable and mood data (everything else a moderator can name is a survey column)
CONTEXT = ["Mood_pre", "Mood_sd_pre", "Mood_n_pre", "log_steps_pre", "sleep_minutes_pre", "hr_avg_pre", "RHR_pre",
           "observed_hours_pre", "watch_share_pre", "device_is_fitbit", "device_is_garmin", "t"]
# baseline-only survey questions without a wave suffix (depression history, age on moving to the US)
_BASELINE_UNSUFFIXED = re.compile(r"^(Age|Sex|AgeMoveUS|depr[A-Z]\w*)$")
_WAVE0 = re.compile(r"(_0$|[A-Za-z]0$|[A-Za-z]0_|0_published$)")


def is_baseline_column(name: str) -> bool:
    """A survey column answered at baseline (wave 0): PHQtot0, stress3_0, medication0_Antidepressants, Neu0_published,
    plus the baseline-only questions without a suffix. Follow-up waves (PHQtot2, stress10_3) are not baseline, so using
    them as moderators would condition on something measured after messages began."""
    if name.startswith("survey_") or name.endswith(("_TEXT", "TEXT", "_selections")) or name in ("DutyDate0", "enddate0", "relevantInfo0"):
        return False
    return bool(_BASELINE_UNSUFFIXED.match(name) or _WAVE0.search(name))


def baseline_traits(path, extra=()) -> pd.DataFrame:
    """Baseline traits from the survey file: the standard set plus any other survey columns named in `extra`
    (a name the file does not have becomes an empty column)."""
    want = list(dict.fromkeys(list(TRAITS) + [c for c in extra if c not in TRAITS]))
    s = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""], usecols=lambda c: c in ["PARTICIPANTIDENTIFIER"] + want)
    out = pd.DataFrame({"participant_id": s["PARTICIPANTIDENTIFIER"]})
    for c in want:
        out[c] = pd.to_numeric(s[c], errors="coerce") if c in s else np.nan
    out["Sex"] = out["Sex"].map({1: 0.0, 2: 1.0})
    return out.drop_duplicates("participant_id")


def survey_catalog(path) -> List[Dict]:
    """Baseline survey columns usable as moderators: numeric with at least two values. For each, the share of survey
    respondents with a value. Names and shares only; no participant values leave this function."""
    s = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])
    out = []
    for c in s.columns:
        if c == "PARTICIPANTIDENTIFIER" or not is_baseline_column(c):
            continue
        v = pd.to_numeric(s[c], errors="coerce")
        if v.nunique() >= 2:
            out.append({"name": c, "coverage": round(float(v.notna().mean()), 3)})
    return out


def _col(h: pd.DataFrame, name: str) -> np.ndarray:
    return h[name].to_numpy(dtype=np.float64) if name in h else np.full(len(h), np.nan)


def _first(*arrays: np.ndarray) -> np.ndarray:
    out = arrays[0].copy()
    for a in arrays[1:]:
        out = np.where(np.isnan(out), a, out)
    return out


def instrument_hours(h: pd.DataFrame, inst: str, night_start: int, night_end: int) -> Dict[str, np.ndarray]:
    """Hourly arrays for one instrument: steps, hr, sleep, rhr (NaN where absent), and 0/1 indicators."""
    W = {k: _col(h, f"HealthkitWatch_{k}") for k in ("steps", "hr_avg", "sleep_minutes", "RHR")}
    if inst in ("fitbit", "garmin"):
        dev = "Fitbit" if inst == "fitbit" else "Garmin"
        a = {"steps": _col(h, f"{dev}_steps"), "hr": _col(h, f"{dev}_hr_avg"), "sleep": _col(h, f"{dev}_sleep_minutes"), "rhr": _col(h, f"{dev}_RHR")}
    elif inst == "apple_watch":
        a = {"steps": W["steps"], "hr": W["hr_avg"], "sleep": W["sleep_minutes"], "rhr": W["RHR"]}
    else:
        P = {k: _col(h, f"HealthkitPhone_{k}") for k in ("steps", "hr_avg", "sleep_minutes", "RHR")}
        a = {"steps": _first(W["steps"], P["steps"]), "hr": _first(W["hr_avg"], P["hr_avg"]),
             "sleep": _first(W["sleep_minutes"], P["sleep_minutes"], _col(h, "HealthkitUnknown_sleep_minutes")),
             "rhr": _first(W["RHR"], P["RHR"])}
        with np.errstate(invalid="ignore"):
            a["watch_obs"] = (~np.isnan(W["hr_avg"]) | (W["steps"] > 0)).astype(np.float64)
    with np.errstate(invalid="ignore"):
        obs = ~np.isnan(a["hr"]) | (a["steps"] > 0)      # a zero step cell is not evidence of wear (Garmin writes zeros)
    lh = h["local_hour"].to_numpy()
    hod = np.where(lh >= 0, lh % 24, -1)
    if night_start > night_end:
        night = (hod >= night_start) | ((hod >= 0) & (hod < night_end))
    else:
        night = (hod >= night_start) & (hod < night_end)
    a["obs"] = obs.astype(np.float64)
    a["obs_night"] = (obs & night).astype(np.float64)
    a["steps_obs"] = np.where(obs, np.nan_to_num(a["steps"]), np.nan)        # a blank step cell in an observed hour is 0
    a["sleep_pos"] = np.where(a["sleep"] > 0, 1.0, np.nan)
    return a


def window_stats(dec: pd.DataFrame, hourly: pd.DataFrame, codes: pd.DataFrame, window: Dict, night_start: int = 22,
                 night_end: int = 7) -> pd.DataFrame:
    """Layer 1. dec: decision table (any cohort). Returns one row per analysis decision with window statistics."""
    dec = dec.copy()
    code_of = dict(zip(codes["participant_id"], codes["pid_code"]))
    dec["pid_code"] = dec["participant_id"].map(code_of).fillna(-1).astype(np.int64)
    dec = dec[(dec["anchor_hour"] >= 0) & dec["in_analysis"]].reset_index(drop=True)
    w = WINDOWS.get(window.get("name", "next_decision"))(dec, **{k: v for k, v in window.items() if k not in ("name", "span_min", "span_max")})
    dec = pd.concat([dec, w], axis=1)
    agg = WindowAggregator(hourly)
    pid = dec["pid_code"].to_numpy()
    sides = {side: agg.bounds(pid, dec[f"{side}_start"].to_numpy(), dec[f"{side}_end"].to_numpy()) for side in ("post", "pre")}
    new: Dict[str, np.ndarray] = {}
    mood = _col(hourly, "Mood")
    for side, (lo, hi, ok) in sides.items():
        start, end = dec[f"{side}_start"].to_numpy(), dec[f"{side}_end"].to_numpy()
        new[f"span_{side}"] = np.where(ok, end - start, np.nan).astype(float)
        st = agg.stats_array(mood, lo, hi, ok, ["mean", "sd", "n"])
        new[f"mood_mean_{side}"], new[f"mood_sd_{side}"], new[f"mood_n_{side}"] = st["mean"], st["sd"], st["n"]
    for inst in INSTRUMENTS:
        arrays = instrument_hours(hourly, inst, night_start, night_end)
        for side, (lo, hi, ok) in sides.items():
            new[f"{inst}_steps_sum_{side}"] = agg.stats_array(arrays["steps_obs"], lo, hi, ok, ["sum0"])["sum0"]
            new[f"{inst}_obs_h_{side}"] = agg.stats_array(arrays["obs"], lo, hi, ok, ["sum0"])["sum0"]
            new[f"{inst}_obs_night_h_{side}"] = agg.stats_array(arrays["obs_night"], lo, hi, ok, ["sum0"])["sum0"]
            new[f"{inst}_hr_mean_{side}"] = agg.stats_array(arrays["hr"], lo, hi, ok, ["mean"])["mean"]
            new[f"{inst}_rhr_mean_{side}"] = agg.stats_array(arrays["rhr"], lo, hi, ok, ["mean"])["mean"]
            new[f"{inst}_sleep_sum_{side}"] = agg.stats_array(arrays["sleep"], lo, hi, ok, ["sum0"])["sum0"]
            new[f"{inst}_sleep_h_{side}"] = agg.stats_array(arrays["sleep_pos"], lo, hi, ok, ["n"])["n"]
            if "watch_obs" in arrays:
                new[f"{inst}_watch_obs_h_{side}"] = agg.stats_array(arrays["watch_obs"], lo, hi, ok, ["sum0"])["sum0"]
        del arrays
    keep_cols = ["decision_id", "participant_id", "pid_code", "decision_date", "anchor_hour", "send", "domain", "strategy", "data",
                 "arm", "t", "post_start", "post_end", "pre_start", "pre_end"]
    out = pd.concat([dec[[c for c in keep_cols if c in dec.columns]], pd.DataFrame(new)], axis=1)
    for c in new:
        out[c] = out[c].astype(np.float32)
    return out


def apply_rules(stats: pd.DataFrame, traits: pd.DataFrame, keep: Dict, device: str = "combined",
                apple_source: str = "watch_then_phone", window: Dict = None) -> pd.DataFrame:
    """Layer 2. Outcomes and covariates for one device under one set of keep rules."""
    window = window or {}
    span_min, span_max = window.get("span_min", 20), window.get("span_max", 28)
    H = keep.get("steps_min_observed_hours", 10)
    short = keep.get("sleep_short_night_minutes", 180)
    wear_min = keep.get("sleep_night_wear_min", 0.67)
    ns, ne = keep.get("night_start_hour", 22), keep.get("night_end_hour", 7)
    night_len = (24 - ns + ne) if ns > ne else (ne - ns)
    cands = {"fitbit": "fitbit", "garmin": "garmin", "apple": "apple_watch" if apple_source == "watch_only" else "apple"}
    base_cols = [c for c in stats.columns if not any(c.startswith(i + "_") for i in INSTRUMENTS) and not c.startswith("mood_")]
    df = stats[base_cols].copy()
    f64 = lambda c: stats[c].to_numpy(dtype=np.float64)
    span_ok = {s: (f64(f"span_{s}") >= span_min) & (f64(f"span_{s}") <= span_max) for s in ("post", "pre")}
    per: Dict[str, Dict[str, np.ndarray]] = {}
    for key, inst in cands.items():
        d = {}
        for s in ("post", "pre"):
            obs = f64(f"{inst}_obs_h_{s}")
            d[f"log_steps_{s}"] = np.where(span_ok[s] & (obs >= H), np.log1p(f64(f"{inst}_steps_sum_{s}")), np.nan)
            sl, sl_h = f64(f"{inst}_sleep_sum_{s}"), f64(f"{inst}_sleep_h_{s}")
            wear = f64(f"{inst}_obs_night_h_{s}") / night_len
            d[f"sleep_minutes_{s}"] = np.where(span_ok[s] & (sl_h > 0) & ((sl >= short) | (wear >= wear_min)), sl, np.nan)
            d[f"observed_hours_{s}"] = obs
            d[f"hr_avg_{s}"] = f64(f"{inst}_hr_mean_{s}")
            d[f"RHR_{s}"] = f64(f"{inst}_rhr_mean_{s}")
            wcol = f"{inst}_watch_obs_h_{s}"
            with np.errstate(invalid="ignore", divide="ignore"):
                d[f"watch_share_{s}"] = f64(wcol) / np.where(obs > 0, obs, np.nan) if wcol in stats else np.full(len(stats), np.nan)
        per[key] = d
    pid = stats["pid_code"].to_numpy()
    if device == "combined":
        tot = pd.DataFrame({k: per[k]["observed_hours_post"] for k in cands}).assign(pid=pid).groupby("pid").sum()
        main = tot.idxmax(axis=1).where(tot.max(axis=1) > 0, "")
        chosen = pd.Series(pid).map(main).fillna("").to_numpy(dtype=object)
        in_view = np.ones(len(stats), bool)
    elif device in cands:
        chosen = np.full(len(stats), device, dtype=object)
        in_view = pd.Series(per[device]["observed_hours_post"]).groupby(pid).transform("sum").to_numpy() > 0
    else:
        raise ValueError(f"unknown device '{device}'; use combined, apple, garmin or fitbit")
    out_cols: Dict[str, np.ndarray] = {}
    for name in per["fitbit"]:
        vals = np.full(len(stats), np.nan)
        for k in cands:
            sel = chosen == k
            vals[sel] = per[k][name][sel]
        out_cols[name] = np.where(in_view, vals, np.nan)
    for s in ("post", "pre"):
        out_cols[f"Mood_{s}"] = np.where(span_ok[s] & (f64(f"mood_n_{s}") > 0) & in_view, f64(f"mood_mean_{s}"), np.nan)
        out_cols[f"Mood_sd_{s}"] = f64(f"mood_sd_{s}")
        out_cols[f"Mood_n_{s}"] = f64(f"mood_n_{s}")
    for k in ("fitbit", "garmin"):
        out_cols[f"device_is_{k}"] = (chosen == k).astype(float)
    df = pd.concat([df, pd.DataFrame(out_cols)], axis=1)
    df["device"] = chosen
    df["in_device_view"] = in_view
    return df.merge(traits, on="participant_id", how="left")


def covariate_matrix(df: pd.DataFrame, names: List[str], indicators: bool):
    """Median-impute over the given rows; optionally add a missingness indicator per variable that has missing values.
    Variables that are absent or constant are dropped."""
    if len(df) == 0:
        return np.zeros((0, 0)), []
    cols, out_names = [], []
    for c in names:
        if c not in df.columns:
            continue
        v = df[c].to_numpy(dtype=float)
        miss = np.isnan(v)
        med = np.nanmedian(v) if (~miss).any() else 0.0
        cols.append(np.where(miss, med, v)); out_names.append(c)
        if indicators and miss.any() and (~miss).any():
            cols.append(miss.astype(float)); out_names.append(f"{c}_miss")
    X = np.column_stack(cols) if cols else np.zeros((len(df), 0))
    keep = X.std(axis=0) > 0 if X.shape[1] else np.zeros(0, bool)
    return X[:, keep], [n for n, k in zip(out_names, keep) if k]


def in_dates(df: pd.DataFrame, date_from=None, date_to=None) -> pd.DataFrame:
    """Decisions whose decision_date (YYYY-MM-DD) lies in [date_from, date_to]; an end left as None is open.
    History covariates still come from the day before, even when that day is outside the range."""
    if not date_from and not date_to:
        return df
    d = df["decision_date"].astype(str).str[:10]
    m = np.ones(len(df), bool)
    if date_from:
        m &= (d >= str(date_from)).to_numpy()
    if date_to:
        m &= (d <= str(date_to)).to_numpy()
    return df.loc[m].reset_index(drop=True)
