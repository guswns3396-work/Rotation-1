"""Contrasts: which decisions, which arms, which probabilities. Each turns the analysis table into AnalysisFrames.

A contrast yields one or more (label, question, frame) items. Arm 0 is the reference. Probabilities are the
unconditional randomization probabilities of each analysed arm, renormalised over the analysed arms, which is the
correct propensity once rows are restricted to decisions that received one of those arms.

Registered contrasts (the six questions Drew set, 2026-11-16):
  any_vs_none          Q1  any delivered message vs no message
  strategy_vs_none     Q2  each strategy in one domain vs no message (Jack's H2, within domain)
  strategy_pairwise    Q2  strategies against a reference strategy, among messages in one domain
  data_vs_nodata       Q3  message showing own data vs not, among messages (all domains and strategies)
  data_within_strategy Q3  Data vs NoData version of the same strategy, among messages of that strategy
  domain_vs_none       Q4/Q5  messages of one domain vs no message; own domain when it matches the outcome, else cross
  type_vs_none         Q2T    each message type (strategy x own-data display) in the outcome's domain vs no message
  type_any_vs_none     Q2T    each message type in any domain vs no message
Rules shared by all contrasts: decisions where an analysed arm has probability below `min_prob` are dropped (positivity);
arms with fewer than `min_arm_rows` rows (after the outcome filter) are dropped.
`positivity` says which probabilities the floor checks in contrasts with more than two arms:
  pairwise  (default, Drew's choice on 2026-11-17) only the reference and the arm compared with it; one frame per arm, so a decision where some other arm was
            nearly impossible still counts for the arms that were possible. Each frame keeps the decisions that got the
            reference or that arm, with probabilities renormalised over the two.
  joint     every arm in the contrast, as in Jack's notebook; one frame holds all arms
"""
from __future__ import annotations

from typing import Dict, Iterator, List, Tuple

import numpy as np
import pandas as pd

from ihs_causal.data.decisions import ARMS, DOMAINS, STRATEGIES
from ihs_causal.data.features import OUTCOMES, covariate_matrix
from ihs_causal.estimators.frame import AnalysisFrame
from ihs_causal.registry import Registry

CONTRASTS = Registry("contrast")
OUTCOME_DOMAIN = {"mood": "mood", "steps": "steps", "sleep": "sleep"}


def _frame(df: pd.DataFrame, outcome: str, arm_masks: List[np.ndarray], arm_probs: List[np.ndarray], arm_names: List[str],
           spec: Dict, label: str) -> Tuple[AnalysisFrame, Dict]:
    y = df[OUTCOMES[outcome]].to_numpy(dtype=float)
    arm = np.full(len(df), -1)
    for k, m in enumerate(arm_masks):
        arm[m] = k
    P = np.column_stack(arm_probs).astype(float)
    min_prob = spec.get("min_prob", 1e-3)
    keep = (arm >= 0) & np.isfinite(y) & np.isfinite(P).all(axis=1) & (P >= min_prob).all(axis=1)
    for m in spec.get("moderators", []):   # moderator analyses use complete cases for the moderator, as in Jack's notebook
        keep &= np.isfinite(df[m].to_numpy(dtype=float))
    # Removed decisions are counted by reason: a probability not published (2025, September 4-27, the fitted decisions);
    # none of the compared messages possible (2025, another domain's week: out of scope by design); below the floor
    cand = (arm >= 0) & np.isfinite(y)
    with np.errstate(invalid="ignore"):
        no_message = cand & ((P[:, 1:] == 0).all(axis=1) if P.shape[1] > 1 else np.zeros(len(df), bool))
        missing = cand & ~no_message & ~np.isfinite(P).all(axis=1)
        low = cand & ~missing & ~no_message & ~(P >= min_prob).all(axis=1)
    info = {"arms_compared": list(arm_names), "rows_candidate": int((arm >= 0).sum()), "rows_outcome_missing": int(((arm >= 0) & ~np.isfinite(y)).sum()),
            "rows_probability_missing": int(missing.sum()), "rows_no_message_possible": int(no_message.sum()),
            "rows_dropped_low_probability": int(low.sum())}
    # drop small arms (never the reference)
    min_rows = spec.get("min_arm_rows", 200)
    active = [0] + [k for k in range(1, len(arm_names)) if ((arm == k) & keep).sum() >= min_rows]
    info["arms_dropped_small"] = [arm_names[k] for k in range(1, len(arm_names)) if k not in active]
    keep &= np.isin(arm, active)
    remap = {old: new for new, old in enumerate(active)}
    arm2 = np.array([remap[a] for a in arm[keep]], dtype=np.int64) if keep.any() else np.zeros(0, np.int64)
    P2 = P[keep][:, active]
    P2 = P2 / P2.sum(axis=1, keepdims=True)
    sub = df.loc[keep]
    controls, cnames = covariate_matrix(sub, spec["controls"], indicators=spec.get("control_indicators", False))
    mods, mnames = covariate_matrix(sub, spec.get("moderators", []), indicators=False)
    if mods.shape[1]:
        mods = mods - mods.mean(axis=0)
    frame = AnalysisFrame(y=y[keep], arm=arm2, prob=P2, cluster=sub["pid_code"].to_numpy(), controls=controls,
                          moderators=mods, arm_names=[arm_names[k] for k in active], control_names=cnames,
                          moderator_names=mnames, label=label)
    if spec.get("nuisance"):
        feats, fnames = covariate_matrix(sub, spec["nuisance"], indicators=True)
        frame.features = feats            # type: ignore[attr-defined]
    frame.time_index = sub["t"].to_numpy()   # type: ignore[attr-defined]   # day index on the window grid
    sweep = [m for m in spec.get("moderator_sweep", []) if m in sub.columns]
    if sweep:   # candidate moderators for question 6, missing values kept; each is analysed on its own complete cases
        frame.sweep_values = sub[sweep].to_numpy(dtype=float)        # type: ignore[attr-defined]
        frame.sweep_names = sweep                                     # type: ignore[attr-defined]
        frame.baseline_traits = [t for t in spec.get("baseline_traits", []) if t in sweep]   # type: ignore[attr-defined]
    info["rows_analysed"] = frame.n
    return frame, info


def _items(head: Tuple, df: pd.DataFrame, outcome: str, masks: List[np.ndarray], probs: List[np.ndarray], names: List[str],
           spec: Dict, label: str) -> Iterator:
    """All arms in one frame, or (positivity 'pairwise') one frame per arm against the reference."""
    if spec.get("positivity", "pairwise") == "pairwise" and len(names) > 2:
        for k in range(1, len(names)):
            yield head + _frame(df, outcome, [masks[0], masks[k]], [probs[0], probs[k]], [names[0], names[k]], spec, label)
    else:
        yield head + _frame(df, outcome, masks, probs, names, spec, label)


def _sent(df):
    return df["send"].to_numpy() == 1


def _none(df):
    return df["send"].to_numpy() == 0


@CONTRASTS.register("any_vs_none")
def any_vs_none(df: pd.DataFrame, outcome: str, spec: Dict) -> Iterator:
    yield ("Any message vs none", "Q1", "any") + _frame(df, outcome, [_none(df), _sent(df)],
                                                         [df["p_none"].to_numpy(), df["p_send"].to_numpy()], ["none", "message"], spec, "any")


@CONTRASTS.register("domain_vs_none")
def domain_vs_none(df: pd.DataFrame, outcome: str, spec: Dict) -> Iterator:
    for d in spec.get("domains", DOMAINS):
        q = "Q4" if OUTCOME_DOMAIN[outcome] == d else "Q5"
        m = _sent(df) & (df["domain"].to_numpy() == d)
        yield (f"{d} message vs none", q, d) + _frame(df, outcome, [_none(df), m], [df["p_none"].to_numpy(), df[f"p_dom_{d}"].to_numpy()],
                                                       ["none", f"{d} message"], spec, d)


@CONTRASTS.register("strategy_vs_none")
def strategy_vs_none(df: pd.DataFrame, outcome: str, spec: Dict) -> Iterator:
    for d in spec.get("domains", [OUTCOME_DOMAIN[outcome]]):
        masks, probs, names = [_none(df)], [df["p_none"].to_numpy()], ["none"]
        for s in STRATEGIES:
            masks.append(_sent(df) & (df["domain"].to_numpy() == d) & (df["strategy"].to_numpy() == s))
            probs.append(df[f"p_dom_{d}_{s}"].to_numpy()); names.append(s)
        yield from _items((f"strategies in {d} messages vs none", "Q2", d), df, outcome, masks, probs, names, spec, d)


@CONTRASTS.register("strategy_pairwise")
def strategy_pairwise(df: pd.DataFrame, outcome: str, spec: Dict) -> Iterator:
    ref = spec.get("reference_strategy", "CS")
    order = [ref] + [s for s in STRATEGIES if s != ref]
    for d in spec.get("domains", [OUTCOME_DOMAIN[outcome]]):
        masks = [_sent(df) & (df["domain"].to_numpy() == d) & (df["strategy"].to_numpy() == s) for s in order]
        probs = [df[f"p_dom_{d}_{s}"].to_numpy() for s in order]
        yield from _items((f"strategies vs {ref}, {d} messages", "Q2", d), df, outcome, masks, probs, order, spec, d)


@CONTRASTS.register("data_vs_nodata")
def data_vs_nodata(df: pd.DataFrame, outcome: str, spec: Dict) -> Iterator:
    data = df["data"].to_numpy()
    yield ("own data shown vs not", "Q3", "any") + _frame(df, outcome, [_sent(df) & (data == 0), _sent(df) & (data == 1)],
                                                          [df["p_nodata"].to_numpy(), df["p_data"].to_numpy()], ["no data", "data"], spec, "any")


@CONTRASTS.register("data_within_strategy")
def data_within_strategy(df: pd.DataFrame, outcome: str, spec: Dict) -> Iterator:
    arm = df["arm"].to_numpy()
    for s in ["CS", "BS", "MI", "Mfn"]:
        yield (f"{s}: own data shown vs not", "Q3", s) + _frame(df, outcome, [arm == f"{s}NoData", arm == f"{s}Data"],
                                                                [df[f"p_arm_{s}NoData"].to_numpy(), df[f"p_arm_{s}Data"].to_numpy()],
                                                                [f"{s} no data", f"{s} data"], spec, s)


TYPE_LABEL = {a: (a[:-6] + ", no data") if a.endswith("NoData") else (a[:-4] + ", own data") for a in ARMS}


@CONTRASTS.register("type_vs_none")
def type_vs_none(df: pd.DataFrame, outcome: str, spec: Dict) -> Iterator:
    for d in spec.get("domains", [OUTCOME_DOMAIN[outcome]]):
        masks, probs, names = [_none(df)], [df["p_none"].to_numpy()], ["none"]
        for a in ARMS:
            masks.append(_sent(df) & (df["domain"].to_numpy() == d) & (df["arm"].to_numpy() == a))
            probs.append(df[f"p_type_{d}_{a}"].to_numpy()); names.append(TYPE_LABEL[a])
        yield from _items((f"message types in {d} messages vs none", "Q2T", d), df, outcome, masks, probs, names, spec, d)


@CONTRASTS.register("type_any_vs_none")
def type_any_vs_none(df: pd.DataFrame, outcome: str, spec: Dict) -> Iterator:
    masks, probs, names = [_none(df)], [df["p_none"].to_numpy()], ["none"]
    for a in ARMS:
        masks.append(_sent(df) & (df["arm"].to_numpy() == a))
        probs.append(df[f"p_arm_{a}"].to_numpy()); names.append(TYPE_LABEL[a])
    yield from _items(("message types, any domain, vs none", "Q2T", "any"), df, outcome, masks, probs, names, spec, "any")
