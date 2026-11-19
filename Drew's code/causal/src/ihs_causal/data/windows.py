"""Outcome windows and fast window aggregation.

Window definitions (registered in WINDOWS; the configuration names one):
  next_decision  Jack's grid. Decisions of a participant are laid on a daily grid: day index t advances by
                 max(1, round(gap / 24 h)) between consecutive decisions. The post window runs from this decision's anchor
                 to the next grid day's start (the next decision's anchor if it falls on the next day, else anchor + 24 h);
                 the pre window is the previous grid day ([previous anchor + 24 h x (days skipped), anchor)).
  fixed          post = [anchor + post_start_h, anchor + post_end_h), pre = [anchor - pre_len_h, anchor).

Aggregation uses prefix sums over the hourly table sorted by (participant, hour): every window's sum, count and sum of
squares is two array lookups, so all windows for all decisions and all columns take about a second. Rules needing order
statistics (median, max) gather each window's rows once with one vectorized index build.
"""
from __future__ import annotations

from typing import Dict, Iterable

import numpy as np
import pandas as pd

from ihs_causal.registry import Registry

WINDOWS = Registry("window")
SHIFT = np.int64(32)


@WINDOWS.register("next_decision")
def next_decision_windows(dec: pd.DataFrame, **_: object) -> pd.DataFrame:
    """dec: pid_code, anchor_hour (one row per decision). Returns t, post_start, post_end, pre_start, pre_end (hours; -1 = none)."""
    d = dec[["pid_code", "anchor_hour"]].copy()
    d["_row"] = np.arange(len(d))
    d = d.sort_values(["pid_code", "anchor_hour"], kind="stable")
    pid = d["pid_code"].to_numpy()
    h = d["anchor_hour"].to_numpy().astype(np.int64)
    first = np.r_[True, pid[1:] != pid[:-1]]
    gap = np.r_[0, np.diff(h)]
    steps = np.where(first, 0, np.maximum(1, np.rint(gap / 24.0))).astype(np.int64)
    group = np.cumsum(first) - 1
    t = np.cumsum(steps) - np.concatenate([[0], np.cumsum(steps)])[np.flatnonzero(first)][group]
    last = np.r_[pid[1:] != pid[:-1], True]
    next_h = np.r_[h[1:], 0]
    next_steps = np.r_[steps[1:], 0]
    post_end = np.where(~last & (next_steps == 1), next_h, h + 24)
    prev_h = np.r_[0, h[:-1]]
    pre_start = np.where(first, -1, prev_h + 24 * (steps - 1))
    pre_end = np.where(first, -1, h)
    out = pd.DataFrame({"t": t, "post_start": h, "post_end": post_end, "pre_start": pre_start, "pre_end": pre_end}, index=d["_row"].to_numpy())
    return out.sort_index().reset_index(drop=True)


@WINDOWS.register("fixed")
def fixed_windows(dec: pd.DataFrame, post_start_h: int = 0, post_end_h: int = 24, pre_len_h: int = 24, **_: object) -> pd.DataFrame:
    h = dec["anchor_hour"].to_numpy().astype(np.int64)
    d = dec[["pid_code", "anchor_hour"]].copy()
    d["_row"] = np.arange(len(d))
    d = d.sort_values(["pid_code", "anchor_hour"], kind="stable")
    first = np.r_[True, d["pid_code"].to_numpy()[1:] != d["pid_code"].to_numpy()[:-1]]
    t_sorted = np.arange(len(d)) - np.maximum.accumulate(np.where(first, np.arange(len(d)), 0))
    t = np.empty(len(d), dtype=np.int64)
    t[d["_row"].to_numpy()] = t_sorted
    return pd.DataFrame({"t": t, "post_start": h + post_start_h, "post_end": h + post_end_h, "pre_start": h - pre_len_h, "pre_end": h})


class WindowAggregator:
    """Prefix-sum index over an hourly table sorted by (pid_code, hour)."""

    def __init__(self, hourly: pd.DataFrame):
        self.h = hourly
        self.key = (hourly["pid_code"].to_numpy().astype(np.int64) << SHIFT) | hourly["hour"].to_numpy().astype(np.int64)
        if not (np.diff(self.key) > 0).all():
            raise ValueError("hourly table must be sorted by (pid_code, hour) with one row per participant-hour")

    def bounds(self, pid_code: np.ndarray, start: np.ndarray, end: np.ndarray):
        pid = pid_code.astype(np.int64) << SHIFT
        ok = (start >= 0) & (end > start) & (pid_code >= 0)
        lo = np.searchsorted(self.key, pid | np.maximum(start, 0), side="left")
        hi = np.searchsorted(self.key, pid | np.maximum(end, 0), side="left")
        hi = np.where(ok, hi, lo)
        return lo, hi, ok

    def stats_array(self, values: np.ndarray, lo: np.ndarray, hi: np.ndarray, ok: np.ndarray, rules: Iterable[str]) -> Dict[str, np.ndarray]:
        """Window statistics of one hourly array (aligned with the hourly table). Prefix sums are built and dropped per
        call, so memory stays at a few arrays however many columns are aggregated.
        Rules: n (non-missing hours), sum (NaN when no hour has a value), sum0 (missing hours count as 0), mean, sd."""
        v = np.asarray(values, dtype=np.float64)
        m = ~np.isnan(v)
        z = np.where(m, v, 0.0)
        rules = list(rules)
        cs = np.concatenate([[0.0], np.cumsum(z)])
        s = cs[hi] - cs[lo]
        del cs
        n = None
        if any(r in ("n", "sum", "mean", "sd") for r in rules):
            cn = np.concatenate([[0], np.cumsum(m, dtype=np.int64)])
            n = (cn[hi] - cn[lo]).astype(float)
            del cn
        out: Dict[str, np.ndarray] = {}
        with np.errstate(invalid="ignore", divide="ignore"):
            for r in rules:
                if r == "n":
                    out[r] = np.where(ok, n, np.nan)
                elif r == "sum0":
                    out[r] = np.where(ok, s, np.nan)
                elif r == "sum":
                    out[r] = np.where(ok & (n > 0), s, np.nan)
                elif r == "mean":
                    out[r] = np.where(ok & (n > 0), s / n, np.nan)
                elif r == "sd":
                    cq = np.concatenate([[0.0], np.cumsum(z * z)])
                    var = (cq[hi] - cq[lo] - s * s / n) / (n - 1)
                    out[r] = np.where(ok & (n > 1), np.sqrt(np.clip(var, 0, None)), np.nan)
                else:
                    raise ValueError(f"unknown window rule {r}")
        return out

    def stats(self, col: str, lo: np.ndarray, hi: np.ndarray, ok: np.ndarray, rules: Iterable[str]) -> Dict[str, np.ndarray]:
        """Statistics of a column of the hourly table; also supports median and max."""
        rules = list(rules)
        simple = [r for r in rules if r not in ("median", "max")]
        out = self.stats_array(self.h[col].to_numpy(dtype=np.float64), lo, hi, ok, simple) if simple else {}
        for r in rules:
            if r in ("median", "max"):
                out[r] = self._order_stat(col, lo, hi, ok, r)
        return out

    def _order_stat(self, col: str, lo, hi, ok, rule: str) -> np.ndarray:
        length = np.where(ok, hi - lo, 0)
        total = int(length.sum())
        res = np.full(lo.shape[0], np.nan)
        if total == 0:
            return res
        win = np.repeat(np.arange(lo.shape[0]), length)
        pos = np.arange(total) - np.repeat(np.cumsum(length) - length, length) + np.repeat(lo, length)
        vals = self.h[col].to_numpy(dtype=np.float64)[pos]
        keep = ~np.isnan(vals)
        g = pd.Series(vals[keep]).groupby(win[keep])
        agg = g.median() if rule == "median" else g.max()
        res[agg.index.to_numpy()] = agg.to_numpy()
        return res
