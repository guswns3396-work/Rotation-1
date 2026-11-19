"""Contrasts: the probability floor (joint or pairwise) and the message-type contrast, on synthetic decisions."""
import numpy as np
import pandas as pd

from ihs_causal.data.decisions import ARMS, DOMAINS, STRATEGIES
from ihs_causal.design.contrasts import CONTRASTS, TYPE_LABEL


def _decisions(n_people=60, days=100, seed=0):
    """Mood-domain decisions. For the first half of the people DST is impossible (probability 0); everyone else can
    get every arm. Probabilities are unconditional, as in the engine's decision tables."""
    rng = np.random.default_rng(seed)
    pid = np.repeat(np.arange(n_people), days)
    n = pid.size
    no_dst = pid < n_people // 2
    p_none = np.full(n, 0.4)
    p_arm = {a: np.full(n, 0.6 / len(ARMS)) for a in ARMS}
    p_arm["DSTNoData"] = np.where(no_dst, 0.0, 0.6 / len(ARMS))
    others = [a for a in ARMS if a != "DSTNoData"]
    for a in others:   # the DST share goes to the other eight types
        p_arm[a] = np.where(no_dst, 0.6 / len(others), p_arm[a])
    P = np.column_stack([p_none] + [p_arm[a] for a in ARMS])
    assert np.allclose(P.sum(axis=1), 1)
    u = rng.random(n)[:, None]
    pick = (u > np.cumsum(P, axis=1)).sum(axis=1)
    arm = np.array(["NoSend"] + ARMS)[pick]
    send = (arm != "NoSend").astype(int)
    strategy = np.array([next((s for s in STRATEGIES if a.startswith(s) and not (s == "MI" and a.startswith("Mfn"))), "") if a != "NoSend" else ""
                         for a in arm])
    df = pd.DataFrame({"pid_code": pid, "t": np.tile(np.arange(days), n_people), "send": send, "arm": arm,
                       "domain": np.where(send == 1, "mood", ""), "strategy": strategy,
                       "data": np.where(send == 1, (~pd.Series(arm).str.endswith("NoData")).astype(int), -1),
                       "p_none": p_none, "p_send": 1 - p_none})
    for a in ARMS:
        df[f"p_arm_{a}"] = p_arm[a]
    for d in DOMAINS:
        on = 1.0 if d == "mood" else 0.0
        df[f"p_dom_{d}"] = (1 - p_none) * on
        for s in STRATEGIES:
            df[f"p_dom_{d}_{s}"] = sum(p_arm[a] for a in ARMS if a.startswith(s) and not (s == "MI" and a.startswith("Mfn"))) * on
        for a in ARMS:
            df[f"p_type_{d}_{a}"] = p_arm[a] * on
    df["Mood_post"] = rng.normal(size=n) + 0.3 * send
    return df


SPEC = {"controls": ["t"], "min_prob": 1e-3, "min_arm_rows": 50}


def test_joint_floor_drops_decisions_where_any_arm_was_impossible():
    df = _decisions()
    (label, q, scope, frame, info), = list(CONTRASTS.get("type_vs_none")(df, "mood", {**SPEC, "positivity": "joint"}))
    assert q == "Q2T" and frame.arm_names == ["none"] + [TYPE_LABEL[a] for a in ARMS]
    assert info["rows_analysed"] == int((df.pid_code >= 30).sum())          # only people for whom every type was possible
    assert info["rows_dropped_low_probability"] == int((df.pid_code < 30).sum())
    assert np.allclose(frame.prob.sum(axis=1), 1)


def test_pairwise_floor_keeps_decisions_where_only_another_arm_was_impossible():
    df = _decisions()
    items = list(CONTRASTS.get("type_vs_none")(df, "mood", {**SPEC, "positivity": "pairwise"}))
    assert len(items) == len(ARMS)
    by_arm = {it[3].arm_names[1]: it for it in items}
    cs = by_arm[TYPE_LABEL["CSData"]]
    rows = df[df.arm.isin(["NoSend", "CSData"])]
    assert cs[4]["rows_analysed"] == len(rows)                               # both halves count for CS, own data
    expect = rows.p_arm_CSData / (rows.p_none + rows.p_arm_CSData)
    assert np.allclose(np.sort(cs[3].prob[:, 1]), np.sort(expect.to_numpy()))
    dst = by_arm[TYPE_LABEL["DSTNoData"]]
    assert dst[4]["rows_analysed"] == int((df.arm.isin(["NoSend", "DSTNoData"]) & (df.pid_code >= 30)).sum())


def test_strategies_get_the_same_floor_choice():
    df = _decisions()
    joint = list(CONTRASTS.get("strategy_vs_none")(df, "mood", {**SPEC, "positivity": "joint"}))
    pair = list(CONTRASTS.get("strategy_vs_none")(df, "mood", {**SPEC, "positivity": "pairwise"}))
    assert len(joint) == 1 and len(pair) == len(STRATEGIES)
    assert sum(it[4]["rows_analysed"] for it in pair) > joint[0][4]["rows_analysed"]


def test_type_probabilities_add_up_to_domain_and_arm_probabilities():
    df = _decisions()
    for d in DOMAINS:
        assert np.allclose(sum(df[f"p_type_{d}_{a}"] for a in ARMS), df[f"p_dom_{d}"])
    for a in ARMS:
        assert np.allclose(sum(df[f"p_type_{d}_{a}"] for d in DOMAINS), df[f"p_arm_{a}"])


def test_pairwise_is_the_default():
    df = _decisions()
    assert len(list(CONTRASTS.get("type_vs_none")(df, "mood", SPEC))) == len(ARMS)
