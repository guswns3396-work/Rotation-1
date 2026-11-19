"""Decision tables: one row per randomized decision, in one schema for both cohorts.

Columns
    decision_id, participant_id, decision_date
    anchor_hour      int64 hours since 1970 UTC: the hour that starts the post-decision window (the logged send or,
                     for a no-send, its assigned time), floored to the hour
    in_analysis      bool: the decision belongs to the analysis set (delivered sends and reachable no-sends in the
                     study year; for 2025 the approved main flag)
    send             0/1
    domain           mood / steps / sleep (the message's domain; for 2025 the week's randomized domain), else ""
    strategy         CS / BS / MI / Mfn / DST, or "" for a no-send
    data             1 if the message shows the participant's own data, 0 if not, -1 for a no-send
    arm              NoSend, CSData, CSNoData, BSData, BSNoData, MIData, MINoData, MfnData, MfnNoData, DSTNoData
Randomization probabilities, all unconditional (they include the probability of sending):
    p_none, p_send, p_arm_<arm>, p_dom_<domain>, p_dom_<domain>_<strategy>, p_strat_<strategy>, p_data, p_nodata,
    p_type_<domain>_<arm>   one message type (strategy x own-data display) within one domain. 2025: the agent's
                            probability of the arm in that domain's weeks. 2024: from the companion file
                            2024MessageTypeProbabilities.csv.gz (rebuilt message pools); missing if the file is absent.
Every adapter fills the same columns, so contrasts never need to know which cohort they are working on.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from ihs_causal.data.hourly import hours_from_timestamps

ARMS = ["CSData", "CSNoData", "BSData", "BSNoData", "MIData", "MINoData", "MfnData", "MfnNoData", "DSTNoData"]
DOMAINS = ["mood", "steps", "sleep"]
STRATEGIES = ["CS", "BS", "MI", "Mfn", "DST"]
ADAPTERS: Dict[int, object] = {}


def _hour(series: pd.Series) -> np.ndarray:
    ts = pd.to_datetime(series.astype("string"), format="ISO8601", utc=True, errors="coerce").dt.tz_convert(None)
    return hours_from_timestamps(ts)


def _num(df: pd.DataFrame, col: str) -> np.ndarray:
    return pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)


def _derived_probabilities(out: pd.DataFrame) -> None:
    for s in STRATEGIES:
        out[f"p_strat_{s}"] = sum(out[f"p_arm_{a}"] for a in ARMS if a.startswith(s) and not (s == "MI" and a.startswith("Mfn")))
    out["p_data"] = sum(out[f"p_arm_{a}"] for a in ARMS if a.endswith("Data") and not a.endswith("NoData"))
    out["p_nodata"] = sum(out[f"p_arm_{a}"] for a in ARMS if a.endswith("NoData"))


def _arm_label(strategy: pd.Series, data: np.ndarray, send: np.ndarray) -> np.ndarray:
    lab = np.where(send == 1, strategy.fillna("").astype(str) + np.where(data == 1, "Data", "NoData"), "NoSend")
    return lab


def decisions_2024(path_behavior, path_message_types=None) -> pd.DataFrame:
    """2024 cohort. The published table keeps delivered sends and reachable no-sends in the study year, plus earlier
    baseline rows. Probabilities in the file for arms, domains and domain x strategy are conditional on sending; they are
    multiplied by p_send here."""
    df = pd.read_csv(path_behavior, dtype=str, keep_default_na=False, na_values=[""])
    out = pd.DataFrame({"decision_id": df["decision_id"], "participant_id": df["participant_id"], "decision_date": df["decision_date"]})
    out["anchor_hour"] = _hour(df["hour_utc"])
    send = pd.to_numeric(df["action_sent"], errors="coerce").fillna(0).astype(int).to_numpy()
    out["send"] = send
    out["domain"] = df["domain"].fillna("").to_numpy()
    out["strategy"] = df["strategy"].fillna("").to_numpy()
    data = np.where(df["personalization"].fillna("") == "Data", 1, np.where(df["personalization"].fillna("") == "NoData", 0, -1))
    out["data"] = np.where(send == 1, data, -1)
    out["arm"] = _arm_label(df["strategy"], data, send)
    out["core_message_id"] = df["core_message_id"].fillna("")
    in_year = (df["decision_date"] >= "2024-07-01") & (df["decision_date"] <= "2025-06-30")
    out["in_analysis"] = in_year.to_numpy() & (df["time_source"].notna().to_numpy())
    p_send = _num(df, "p_send")
    out["p_send"] = p_send
    out["p_none"] = _num(df, "p_no_send")
    for a in ARMS:
        out[f"p_arm_{a}"] = p_send * _num(df, f"p_{a}")
    for d in DOMAINS:
        out[f"p_dom_{d}"] = p_send * _num(df, f"p_{d}")
        for s in STRATEGIES:
            out[f"p_dom_{d}_{s}"] = p_send * _num(df, f"p_{d}_{s}")
    _derived_probabilities(out)
    types = None
    if path_message_types is not None and Path(path_message_types).exists():
        types = pd.read_csv(path_message_types, dtype={"decision_id": str}).set_index("decision_id")
    for d in DOMAINS:
        for a in ARMS:
            col = f"p_{d}_{a}"
            out[f"p_type_{d}_{a}"] = p_send * out["decision_id"].map(types[col]).to_numpy(dtype=float) if types is not None else np.nan
    out["cohort"] = 2024
    return out


def decisions_2025(path_behavior, path_timing, prob_scope: str = "marginal") -> pd.DataFrame:
    """2025 cohort. The domain is randomized by week; within a week the deployed policy chooses no-send or one of nine
    arms. prob_scope 'marginal' uses the probability of each action over the agent-selection step (p_marginal_*);
    'selected' uses the selected agent's own distribution (p_*). The window anchor and the main analysis flag come from
    the published timing file."""
    pre_cols = [f"{pre}{a}" for a in ["no_send"] + ARMS for pre in ("p_marginal_", "p_")]
    need = {"decision_id", "participant_id", "decision_date", "action_sent", "decision_domain", "action_label"} | set(pre_cols)
    beh = pd.read_csv(path_behavior, dtype=str, keep_default_na=False, na_values=[""], usecols=lambda c: c in need)
    tim = pd.read_csv(path_timing, dtype=str, keep_default_na=False, na_values=[""],
                      usecols=["decision_id", "window_anchor_utc", "retain_main_reach_retrospective", "message_domain", "core_message_id"])
    df = beh.merge(tim, on="decision_id", how="left", validate="one_to_one")
    pre = "p_marginal_" if prob_scope == "marginal" else "p_"
    out = pd.DataFrame({"decision_id": df["decision_id"], "participant_id": df["participant_id"], "decision_date": df["decision_date"]})
    out["anchor_hour"] = _hour(df["window_anchor_utc"])
    send = pd.to_numeric(df["action_sent"], errors="coerce").fillna(0).astype(int).to_numpy()
    out["send"] = send
    week_domain = df["decision_domain"].fillna("").str.lower().to_numpy()
    out["domain"] = week_domain
    label = df["action_label"].fillna("")
    strat = label.str.extract(r"^(CS|BS|MI|Mfn|DST)", expand=False).fillna("")
    out["strategy"] = np.where(send == 1, strat, "")
    is_data = label.str.endswith("Data") & ~label.str.endswith("NoData")
    out["data"] = np.where(send == 1, is_data.astype(int), -1)
    out["arm"] = np.where(send == 1, label, "NoSend")
    out["core_message_id"] = df["core_message_id"].fillna("")
    out["in_analysis"] = (df["retain_main_reach_retrospective"].fillna("").str.lower().isin(["1", "true"])).to_numpy()
    out["p_none"] = _num(df, f"{pre}no_send")
    out["p_send"] = 1 - out["p_none"]
    for a in ARMS:
        out[f"p_arm_{a}"] = _num(df, f"{pre}{a}")
    # another domain's week is an exact 0 even where a probability is not published (the September 2025 fitted
    # decisions are blank), so such a decision counts as out of scope, not as a missing probability
    for d in DOMAINS:
        in_week = week_domain == d
        out[f"p_dom_{d}"] = np.where(in_week, out["p_send"], 0.0)
        for s in STRATEGIES:
            out[f"p_dom_{d}_{s}"] = np.where(in_week, sum(out[f"p_arm_{a}"] for a in ARMS if a.startswith(s) and not (s == "MI" and a.startswith("Mfn"))), 0.0)
    _derived_probabilities(out)
    for d in DOMAINS:
        in_week = week_domain == d
        for a in ARMS:
            out[f"p_type_{d}_{a}"] = np.where(in_week, out[f"p_arm_{a}"], 0.0)
    out["cohort"] = 2025
    out["prob_scope"] = prob_scope
    return out


ADAPTERS[2024] = decisions_2024
ADAPTERS[2025] = decisions_2025
