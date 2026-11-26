"""Causal excursion-effect estimators: WCLS (Boruvka et al. 2018) and DR-WCLS (doubly robust, cross-fitted).

Both take an AnalysisFrame with K+1 arms (arm 0 is the reference) and return, for every non-reference arm k and every
term of S = [1, moderators], the excursion effect of arm k against arm 0:

    beta_k(S) = E[ Y(k) - Y(0) | S ]   under the randomization probabilities p_tilde (numerator) used for weighting.

With no moderators the single term "effect" is the marginal excursion effect. With moderators, centre them first; the
"effect" term is then the effect at the moderator means and each moderator term is the change in effect per unit.

WCLS
    weights  W = p_tilde[A] / p(A | H)
    model    Y ~ [1, controls] + sum_k (1{A=k} - p_tilde_k) * S
DR-WCLS (constant p_tilde, so the final regression is unweighted)
    mu_a(H)  cross-fitted outcome model under arm a (other participants' rows only)
    Y~_k     = (1{A=k}/p_k - 1{A=0}/p_0) * (Y - mu_A(H)) + mu_k(H) - mu_0(H)
    model    Y~_k ~ S
Standard errors are participant-clustered sandwich estimates. With known randomization probabilities and cross-fitting,
ignoring the nuisance-estimation error is asymptotically valid.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from ihs_causal.estimators.frame import AnalysisFrame
from ihs_causal.estimators.inference import summarize
from ihs_causal.estimators.nuisance import crossfit_arm_means
from ihs_causal.estimators.wls import WLSResult, wls_cluster
from ihs_causal.registry import Registry

ESTIMATORS = Registry("estimator")


@dataclass
class Estimates:
    table: pd.DataFrame                                         # one row per (arm, term)
    influence: Dict[Tuple[str, str], Tuple[np.ndarray, np.ndarray]] = field(default_factory=dict)
    diagnostics: Dict[str, object] = field(default_factory=dict)


def _term_names(frame: AnalysisFrame) -> List[str]:
    return ["effect"] + list(frame.moderator_names)


def _collect(frame: AnalysisFrame, pieces: List[Tuple[int, str, float, float, np.ndarray, np.ndarray]],
             diagnostics: Dict[str, object]) -> Estimates:
    arms = [frame.arm_names[k] for k, *_ in pieces]
    terms = [t for _, t, *_ in pieces]
    est = np.array([e for _, _, e, *_ in pieces])
    se = np.array([s for _, _, _, s, *_ in pieces])
    stats = summarize(est, se)
    table = pd.DataFrame({"arm": arms, "reference": frame.arm_names[0], "term": terms, **stats})
    table["n_rows"] = frame.n
    table["n_participants"] = int(np.unique(frame.cluster).size)
    table["n_arm"] = [int((frame.arm == k).sum()) for k, *_ in pieces]
    table["n_reference"] = int((frame.arm == 0).sum())
    influence = {(frame.arm_names[k], t): (c, v) for k, t, _, _, c, v in pieces}
    return Estimates(table=table, influence=influence, diagnostics=diagnostics)


def _weight_diagnostics(w: np.ndarray) -> Dict[str, float]:
    return {"weight_max": float(w.max()), "weight_mean": float(w.mean()),
            "weight_ess_fraction": float(w.sum() ** 2 / (w ** 2).sum() / w.size)}


@ESTIMATORS.register("wcls")
def wcls(frame: AnalysisFrame, **_: object) -> Estimates:
    n, K = frame.n, frame.n_arms
    S = np.column_stack([np.ones(n), frame.moderators])
    pt = frame.p_tilde
    p_obs = frame.prob[np.arange(n), frame.arm]
    w = pt[frame.arm] / p_obs
    blocks = [((frame.arm == k).astype(float) - pt[k])[:, None] * S for k in range(1, K + 1)]
    X = np.column_stack([np.ones(n), frame.controls] + blocks)
    res: WLSResult = wls_cluster(X, frame.y, w, frame.cluster)
    se = res.se
    offset = 1 + frame.controls.shape[1]
    q1 = S.shape[1]
    terms = _term_names(frame)
    pieces = []
    for k in range(1, K + 1):
        for j in range(q1):
            idx = offset + (k - 1) * q1 + j
            pieces.append((k, terms[j], float(res.coef[idx]), float(se[idx]), res.clusters, res.infl[:, idx]))
    diag = {"estimator": "wcls", **_weight_diagnostics(w), "min_p_observed": float(p_obs.min())}
    return _collect(frame, pieces, diag)


@ESTIMATORS.register("drwcls")
def drwcls(frame: AnalysisFrame, learner: str = "ridge", folds: int = 5, features: Optional[np.ndarray] = None,
           mu: Optional[np.ndarray] = None, seed: int = 20261117, **_: object) -> Estimates:
    n, K = frame.n, frame.n_arms
    if mu is None:
        feats = features if features is not None else np.column_stack([frame.controls, frame.moderators])
        mu = crossfit_arm_means(feats, frame.y, frame.arm, K + 1, frame.cluster, learner=learner, k=folds, seed=seed)
    rows = np.arange(n)
    resid = frame.y - mu[rows, frame.arm]
    p = frame.prob
    ref = (frame.arm == 0) / p[:, 0]
    S = np.column_stack([np.ones(n), frame.moderators])
    ones = np.ones(n)
    terms = _term_names(frame)
    pieces = []
    for k in range(1, K + 1):
        ytil = ((frame.arm == k) / p[:, k] - ref) * resid + mu[:, k] - mu[:, 0]
        res = wls_cluster(S, ytil, ones, frame.cluster)
        se = res.se
        for j in range(S.shape[1]):
            pieces.append((k, terms[j], float(res.coef[j]), float(se[j]), res.clusters, res.infl[:, j]))
    r2 = {}
    for a in range(K + 1):
        sel = frame.arm == a
        if sel.sum() > 1:
            vy = frame.y[sel].var()
            r2[frame.arm_names[a]] = float(1 - ((frame.y[sel] - mu[sel, a]) ** 2).mean() / vy) if vy > 0 else float("nan")
    diag = {"estimator": "drwcls", "learner": learner, "folds": folds, "nuisance_r2_out_of_fold": r2,
            "min_p_observed": float(p[rows, frame.arm].min())}
    return _collect(frame, pieces, diag)
