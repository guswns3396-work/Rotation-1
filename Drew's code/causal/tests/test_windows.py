"""Window definitions and window aggregation, against hand-worked examples and brute force."""
import numpy as np
import pandas as pd

from ihs_causal.data.windows import WindowAggregator, fixed_windows, next_decision_windows


def test_next_decision_grid_matches_jacks_rules():
    # participant 7: anchors at hours 100, 124 (next day), 172 (two days later), 197 (25 h later: next day)
    # participant 3 interleaved, input order shuffled, to check row mapping
    dec = pd.DataFrame({"pid_code": [7, 3, 7, 7, 3, 7], "anchor_hour": [172, 500, 100, 197, 524, 124]})
    w = next_decision_windows(dec)
    got = {(p, a): tuple(r) for p, a, r in zip(dec.pid_code, dec.anchor_hour, w[["t", "post_start", "post_end", "pre_start", "pre_end"]].itertuples(index=False))}
    assert got[(7, 100)] == (0, 100, 124, -1, -1)
    assert got[(7, 124)] == (1, 124, 148, 100, 124)    # next decision skips a day: post window is 24 h
    assert got[(7, 172)] == (3, 172, 197, 148, 172)    # pre window is the interpolated grid day [124 + 24, 172)
    assert got[(7, 197)] == (4, 197, 221, 172, 197)    # last decision: post window is 24 h
    assert got[(3, 500)] == (0, 500, 524, -1, -1)
    assert got[(3, 524)] == (1, 524, 548, 500, 524)


def test_fixed_windows():
    dec = pd.DataFrame({"pid_code": [1, 1], "anchor_hour": [100, 124]})
    w = fixed_windows(dec, post_start_h=1, post_end_h=25, pre_len_h=12)
    assert w.post_start.tolist() == [101, 125] and w.post_end.tolist() == [125, 149] and w.pre_start.tolist() == [88, 112]


def test_aggregator_matches_brute_force():
    rng = np.random.default_rng(0)
    rows = []
    for pid in range(3):
        hours = np.sort(rng.choice(np.arange(1000, 1200), size=150, replace=False))
        vals = rng.normal(100, 30, size=150)
        vals[rng.random(150) < 0.2] = np.nan
        rows.append(pd.DataFrame({"pid_code": pid, "hour": hours, "x": vals}))
    h = pd.concat(rows, ignore_index=True)
    agg = WindowAggregator(h)
    pid = np.array([0, 1, 2, 2, 1])
    start = np.array([1000, 1050, 1100, 1190, 1300])
    end = np.array([1024, 1070, 1128, 1200, 1324])
    lo, hi, ok = agg.bounds(pid, start, end)
    st = agg.stats("x", lo, hi, ok, ["sum", "n", "mean", "sd", "median", "max"])
    for i in range(len(pid)):
        sub = h[(h.pid_code == pid[i]) & (h.hour >= start[i]) & (h.hour < end[i])]["x"].dropna()
        if len(sub) == 0:
            assert st["n"][i] == 0 and np.isnan(st["sum"][i])
            continue
        assert np.isclose(st["sum"][i], sub.sum()) and st["n"][i] == len(sub)
        assert np.isclose(st["mean"][i], sub.mean()) and np.isclose(st["median"][i], sub.median()) and np.isclose(st["max"][i], sub.max())
        if len(sub) > 1:
            assert np.isclose(st["sd"][i], sub.std(ddof=1))
