"""Keep rules and device choice (layer 2), on a small hand-made statistics table."""
import numpy as np
import pandas as pd

from ihs_causal.data.features import INSTRUMENTS, apply_rules, instrument_hours

KEEP = {"steps_min_observed_hours": 10, "sleep_short_night_minutes": 180, "sleep_night_wear_min": 0.67, "night_start_hour": 22, "night_end_hour": 7}


def _stats(rows):
    """rows: list of dicts with pid and per-instrument overrides; everything else defaults to 'no data'."""
    out = []
    for i, r in enumerate(rows):
        d = {"decision_id": f"d{i}", "participant_id": f"p{r['pid']}", "pid_code": r["pid"], "t": i, "span_post": 24.0, "span_pre": 24.0,
             "mood_mean_post": r.get("mood", np.nan), "mood_sd_post": np.nan, "mood_n_post": 1.0 if "mood" in r else 0.0,
             "mood_mean_pre": np.nan, "mood_sd_pre": np.nan, "mood_n_pre": 0.0}
        for inst in INSTRUMENTS:
            for side in ("post", "pre"):
                d.update({f"{inst}_steps_sum_{side}": 0.0, f"{inst}_obs_h_{side}": 0.0, f"{inst}_obs_night_h_{side}": 0.0, f"{inst}_hr_mean_{side}": np.nan,
                          f"{inst}_rhr_mean_{side}": np.nan, f"{inst}_sleep_sum_{side}": 0.0, f"{inst}_sleep_h_{side}": 0.0})
            if inst == "apple":
                d.update({"apple_watch_obs_h_post": 0.0, "apple_watch_obs_h_pre": 0.0})
        for k, v in r.items():
            if k not in ("pid", "mood"):
                d[k] = v
        out.append(d)
    return pd.DataFrame(out)


TRAITS = pd.DataFrame({"participant_id": ["p1", "p2"], "Age": [30.0, 40.0]})


def test_steps_kept_by_observed_hours_not_by_step_count():
    st = _stats([{"pid": 1, "fitbit_obs_h_post": 12, "fitbit_steps_sum_post": 0.0},       # worn, no steps: kept as a real zero
                 {"pid": 1, "fitbit_obs_h_post": 9, "fitbit_steps_sum_post": 5000.0},     # too few observed hours: dropped
                 {"pid": 1, "fitbit_obs_h_post": 10, "fitbit_steps_sum_post": 800.0, "span_post": 30.0}])  # not a day long: dropped
    df = apply_rules(st, TRAITS, KEEP, device="fitbit")
    assert df.log_steps_post.iloc[0] == 0.0
    assert np.isnan(df.log_steps_post.iloc[1]) and np.isnan(df.log_steps_post.iloc[2])


def test_sleep_short_nights_need_overnight_wear():
    st = _stats([{"pid": 1, "garmin_sleep_sum_post": 420.0, "garmin_sleep_h_post": 8, "garmin_obs_h_post": 1},
                 {"pid": 1, "garmin_sleep_sum_post": 120.0, "garmin_sleep_h_post": 2, "garmin_obs_night_h_post": 8, "garmin_obs_h_post": 20},
                 {"pid": 1, "garmin_sleep_sum_post": 120.0, "garmin_sleep_h_post": 2, "garmin_obs_night_h_post": 3, "garmin_obs_h_post": 20},
                 {"pid": 1, "garmin_obs_h_post": 24}])                                    # worn, no sleep record: missing, not zero
    v = apply_rules(st, TRAITS, KEEP, device="garmin").sleep_minutes_post.to_numpy()
    assert v[0] == 420 and v[1] == 120 and np.isnan(v[2]) and np.isnan(v[3])


def test_combined_uses_main_device_and_device_views_restrict_mood():
    st = _stats([{"pid": 1, "fitbit_obs_h_post": 20, "fitbit_steps_sum_post": 1000.0, "apple_obs_h_post": 5, "mood": 3.0},
                 {"pid": 1, "fitbit_obs_h_post": 18, "apple_obs_h_post": 15, "apple_steps_sum_post": 400.0},
                 {"pid": 2, "mood": 4.0}])                                                 # no wearable at all
    comb = apply_rules(st, TRAITS, KEEP, device="combined")
    assert list(comb.device) == ["fitbit", "fitbit", ""]
    assert comb.Mood_post.notna().sum() == 2                                               # mood kept for everyone
    fit = apply_rules(st, TRAITS, KEEP, device="fitbit")
    assert fit.Mood_post.notna().sum() == 1                                                # person 2 has no Fitbit
    app = apply_rules(st, TRAITS, KEEP, device="apple")
    assert np.isnan(app.log_steps_post.iloc[0]) and np.isclose(app.log_steps_post.iloc[1], np.log1p(400))


def test_zero_step_cells_are_not_wear_evidence():
    h = pd.DataFrame({"local_hour": [10, 23, 3], "Garmin_steps": [0.0, 0.0, 50.0], "Garmin_hr_avg": [np.nan, 60.0, np.nan],
                      "Garmin_sleep_minutes": [np.nan, 30.0, np.nan], "Garmin_RHR": [np.nan] * 3})
    a = instrument_hours(h, "garmin", 22, 7)
    assert list(a["obs"]) == [0.0, 1.0, 1.0] and list(a["obs_night"]) == [0.0, 1.0, 1.0]
    assert np.isnan(a["steps_obs"][0]) and a["steps_obs"][1] == 0.0
