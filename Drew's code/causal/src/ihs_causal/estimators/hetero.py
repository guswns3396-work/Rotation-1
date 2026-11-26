"""Question 6: who responds. One cross-fitted DR-WCLS pseudo-outcome per arm, then everything else is cheap:

1. Moderation. For each candidate moderator (baseline trait or context), the pseudo-outcome is regressed on
   [1, z], z the moderator standardised over the rows where it is observed. The slope is the change in the excursion
   effect per one standard deviation of the moderator; participant-clustered standard errors. Benjamini-Hochberg
   q-values across moderators are added when results are read (results.add_bh).
2. Variation between people (primary: split half). Each person's study weeks are split alternately into two halves and
   their mean pseudo-outcome computed in each. Because messages are randomized day by day, the noise in the two halves is
   independent given the person's true effect, so the covariance of the halves across people estimates tau^2, the
   variance of true person-level effects. A participant bootstrap gives an interval, and a sign-flip test (each
   person's product of half deviations keeps or flips its sign) gives a p-value for tau = 0. A REML
   random-effects model with per-person variances is reported alongside.
   Empirical-Bayes shrinkage pulls each person's effect toward the mean in proportion to its noise.
3. Explained by baseline. The share of tau^2 removed by baseline traits, with the trait model fitted on one half and
   applied to the other so that shared noise cannot be explained away.

The REML side-model uses per-person variances that treat a person's decisions as independent (`person_variance: iid`,
the default) or as correlated within study weeks (`weekly_blocks`, noisier with few weeks per person).
"""
from __future__ import annotations

import math
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ihs_causal.estimators.core import ESTIMATORS, Estimates, _collect
from ihs_causal.estimators.frame import AnalysisFrame
from ihs_causal.estimators.nuisance import crossfit_arm_means
from ihs_causal.estimators.wls import cluster_sums, wls_cluster


def chi2_sf(x: float, df: float) -> float:
    """Upper tail of the chi-square distribution: regularized upper incomplete gamma Q(df/2, x/2)."""
    a, z = df / 2.0, x / 2.0
    if z <= 0:
        return 1.0
    if z < a + 1:
        term = total = 1.0 / a
        n = a
        for _ in range(2000):
            n += 1; term *= z / n; total += term
            if abs(term) < abs(total) * 1e-14:
                break
        return max(0.0, 1.0 - total * math.exp(-z + a * math.log(z) - math.lgamma(a)))
    b, c, d = z + 1 - a, 1e300, 1.0 / (z + 1 - a)
    h = d
    for i in range(1, 2000):
        an = -i * (i - a); b += 2
        d = an * d + b; d = 1.0 / (d if abs(d) > 1e-300 else 1e-300)
        c = b + an / c; c = c if abs(c) > 1e-300 else 1e-300
        delta = d * c; h *= delta
        if abs(delta - 1) < 1e-14:
            break
    return min(1.0, h * math.exp(-z + a * math.log(z) - math.lgamma(a)))


def reml(y: np.ndarray, v: np.ndarray, X: Optional[np.ndarray] = None, iters: int = 200):
    """Random-effects (meta-)regression y_i = X_i b + u_i + e_i, u ~ N(0, tau2), e ~ N(0, v_i). Returns (b, cov_b, tau2)."""
    n = y.size
    X = np.ones((n, 1)) if X is None else X
    w = 1 / v
    b = np.linalg.lstsq(X * np.sqrt(w)[:, None], y * np.sqrt(w), rcond=None)[0]
    q = float(np.sum(w * (y - X @ b) ** 2))
    p = X.shape[1]
    tau2 = max(0.0, (q - (n - p)) / max(np.sum(w) - np.sum(w ** 2) / np.sum(w), 1e-12))   # DerSimonian-Laird start
    for _ in range(iters):
        w = 1 / (v + tau2)
        XtW = X.T * w
        cov = np.linalg.pinv(XtW @ X)
        b = cov @ (XtW @ y)
        r = y - X @ b
        P_diag = w - np.einsum("ij,jk,ki->i", X * w[:, None], cov, XtW)     # diagonal of the REML projection
        new = max(0.0, tau2 + np.sum(w ** 2 * r ** 2 - P_diag) / np.sum(w ** 2))
        if abs(new - tau2) < 1e-10 * (1 + tau2):
            tau2 = new
            break
        tau2 = new
    w = 1 / (v + tau2)
    cov = np.linalg.pinv((X.T * w) @ X)
    b = cov @ ((X.T * w) @ y)
    return b, cov, tau2


def person_effects(ytil: np.ndarray, cluster: np.ndarray, min_rows: int, block: Optional[np.ndarray] = None) -> pd.DataFrame:
    """Per-person mean pseudo-outcome and its sampling variance.

    block=None treats a person's decisions as independent. With block labels (e.g. study week), the variance is the
    cluster-robust variance of the mean with blocks as clusters, which allows correlation within a block."""
    ids, s1 = cluster_sums(ytil[:, None], cluster)
    _, n = cluster_sums(np.ones((ytil.size, 1)), cluster)
    n, s1 = n[:, 0], s1[:, 0]
    mean = s1 / n
    if block is None:
        _, s2 = cluster_sums((ytil ** 2)[:, None], cluster)
        var = np.where(n > 1, (s2[:, 0] - n * mean ** 2) / np.maximum(n - 1, 1), np.nan) / n
        nb = n
    else:
        pos = np.searchsorted(ids, cluster)
        key = pos.astype(np.int64) * 1_000_000 + block.astype(np.int64)
        bkeys, bsum = cluster_sums(np.column_stack([ytil, np.ones_like(ytil)]), key)
        bpos = (bkeys // 1_000_000).astype(np.int64)
        dev = bsum[:, 0] - bsum[:, 1] * mean[bpos]
        ss = np.bincount(bpos, weights=dev ** 2, minlength=ids.size)
        nb = np.bincount(bpos, minlength=ids.size).astype(float)
        var = np.where(nb > 1, nb / np.maximum(nb - 1, 1) * ss / n ** 2, np.nan)
    df = pd.DataFrame({"cluster": ids, "n": n.astype(int), "blocks": nb.astype(int), "tau_hat": mean, "v": var})
    keep = (df.n >= min_rows) & (df.v > 0)
    if block is not None:
        keep &= df.blocks >= 4
    return df[keep].reset_index(drop=True)


def split_half(ytil: np.ndarray, cluster: np.ndarray, t: np.ndarray, min_rows: int) -> pd.DataFrame:
    """Per-person mean pseudo-outcome in even and in odd study weeks.

    With randomized treatment the pseudo-outcome noise in the two halves is independent given the person's effect, so
    the covariance of the two halves across people estimates the variance of true person-level effects, with no
    within-person variance estimate needed and robust to correlation between days."""
    ids = np.unique(cluster)
    pos = np.searchsorted(ids, cluster)
    half = (np.asarray(t) // 7) % 2
    keys, sums = cluster_sums(np.column_stack([ytil, np.ones_like(ytil)]), pos.astype(np.int64) * 2 + half)
    S = np.zeros((ids.size, 2)); N = np.zeros((ids.size, 2))
    S[keys // 2, keys % 2] = sums[:, 0]
    N[keys // 2, keys % 2] = sums[:, 1]
    ok = (N >= min_rows).all(axis=1)
    return pd.DataFrame({"cluster": ids[ok], "A": S[ok, 0] / N[ok, 0], "B": S[ok, 1] / N[ok, 1], "nA": N[ok, 0], "nB": N[ok, 1]})


def split_half_test(A: np.ndarray, B: np.ndarray, rng: np.random.Generator, bootstrap: int = 400, draws: int = 2000):
    """tau^2 = covariance of the two halves across people; participant-bootstrap interval for tau; sign-flip p-value.

    The sign-flip null flips the sign of each person's own product of half deviations, which keeps the pairing of a
    person's two (equally noisy) halves; shuffling halves across people would understate the null spread when noise
    varies between people."""
    tau2 = float(np.cov(A, B)[0, 1])
    idx = rng.integers(0, A.size, (bootstrap, A.size))
    Ab, Bb = A[idx], B[idx]
    boots = ((Ab - Ab.mean(axis=1, keepdims=True)) * (Bb - Bb.mean(axis=1, keepdims=True))).sum(axis=1) / (A.size - 1)
    P = (A - A.mean()) * (B - B.mean())
    null = (rng.choice([-1.0, 1.0], size=(draws, P.size)) @ P) / (P.size - 1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"tau2": tau2, "tau": float(np.sqrt(max(tau2, 0.0))), "tau_ci": [float(np.sqrt(max(lo, 0.0))), float(np.sqrt(max(hi, 0.0)))],
            "p_hetero": float((1 + np.sum(null >= tau2)) / (1 + draws)), "split_half_r": float(np.corrcoef(A, B)[0, 1])}


@ESTIMATORS.register("drwcls_hetero")
def drwcls_hetero(frame: AnalysisFrame, learner: str = "ridge", folds: int = 5, features: Optional[np.ndarray] = None,
                  seed: int = 20261117, min_person_rows: int = 10, bootstrap: int = 400, permutations: int = 2000,
                  min_half_rows: int = 5, person_variance: str = "iid", **_: object) -> Estimates:
    n, K = frame.n, frame.n_arms
    feats = features if features is not None else np.column_stack([frame.controls, frame.moderators])
    mu = crossfit_arm_means(feats, frame.y, frame.arm, K + 1, frame.cluster, learner=learner, k=folds, seed=seed)
    rows = np.arange(n)
    resid = frame.y - mu[rows, frame.arm]
    p = frame.prob
    ref = (frame.arm == 0) / p[:, 0]
    sweep_vals = getattr(frame, "sweep_values", np.zeros((n, 0)))
    sweep_names: List[str] = list(getattr(frame, "sweep_names", []))
    traits: List[str] = [t for t in getattr(frame, "baseline_traits", []) if t in sweep_names]
    ones = np.ones(n)
    pieces, extra_rows, person_tables, hists, hetero_info = [], [], [], {}, {}
    skipped = {}       # moderators with too few recorded values (fewer than 100 decisions) or a single value
    for j, name in enumerate(sweep_names):
        m = sweep_vals[:, j]
        ok = np.isfinite(m)
        if ok.sum() < 100:
            skipped[name] = f"recorded at {int(ok.sum())} decisions"
        elif np.nanstd(m[ok]) == 0:
            skipped[name] = "the same value everywhere"
    rng = np.random.default_rng(seed)
    for k in range(1, K + 1):
        arm_name = frame.arm_names[k]
        ytil = ((frame.arm == k) / p[:, k] - ref) * resid + mu[:, k] - mu[:, 0]
        res = wls_cluster(ones[:, None], ytil, ones, frame.cluster)
        pieces.append((k, "effect", float(res.coef[0]), float(res.se[0]), res.clusters, res.infl[:, 0]))
        # 1. moderation, one moderator at a time
        for j, name in enumerate(sweep_names):
            if name in skipped:
                continue
            m = sweep_vals[:, j]
            ok = np.isfinite(m)
            sd = float(m[ok].std())
            z = (m[ok] - m[ok].mean()) / sd
            r = wls_cluster(np.column_stack([np.ones(ok.sum()), z]), ytil[ok], ones[ok], frame.cluster[ok])
            pieces.append((k, f"mod:{name}", float(r.coef[1]), float(r.se[1]), r.clusters, r.infl[:, 1]))
            extra_rows.append({"arm": arm_name, "term": f"mod:{name}", "moderator_sd": sd, "n_rows_moderator": int(ok.sum())})
        # 2. variation between people
        t_idx = getattr(frame, "time_index", None)
        block = (t_idx // 7) if (person_variance == "weekly_blocks" and t_idx is not None) else None
        pe = person_effects(ytil, frame.cluster, min_person_rows, block)
        G = len(pe)
        if G >= 20:
            y_i, v_i = pe.tau_hat.to_numpy(), pe.v.to_numpy()
            b, cov, tau2_reml = reml(y_i, v_i)
            w0 = 1 / v_i
            mu_fe = np.sum(w0 * y_i) / np.sum(w0)
            Q = float(np.sum(w0 * (y_i - mu_fe) ** 2))
            info = {"people": G, "mean_effect": float(b[0]), "mean_effect_se": float(math.sqrt(cov[0, 0])),
                    "median_rows_per_person": float(pe.n.median()),
                    "reml": {"tau": math.sqrt(tau2_reml), "Q": Q, "Q_df": G - 1, "Q_p": chi2_sf(Q, G - 1), "person_variance": person_variance}}
            sh = split_half(ytil, frame.cluster, t_idx, min_half_rows) if t_idx is not None else None
            if sh is not None and len(sh) >= 20:
                A, B = sh.A.to_numpy(), sh.B.to_numpy()
                test = split_half_test(A, B, rng, bootstrap, permutations)
                tau2 = test["tau2"]
                info.update({"method": "split_half", **test, "split_half_people": int(len(A))})
            else:
                boots = [reml(y_i[idx], v_i[idx], iters=60)[2] for idx in (rng.integers(0, G, G) for _ in range(bootstrap))]
                lo, hi = np.percentile(boots, [2.5, 97.5])
                tau2 = tau2_reml
                info.update({"method": "reml", "tau2": tau2, "tau": math.sqrt(tau2), "tau_ci": [math.sqrt(lo), math.sqrt(hi)],
                             "p_hetero": info["reml"]["Q_p"]})
            tau2_use = max(tau2, 0.0)
            shrink = tau2_use / (tau2_use + v_i)
            pe["tau_shrunk"] = b[0] + shrink * (y_i - b[0])
            pe["post_sd"] = np.sqrt(shrink * v_i)
            pe["arm"] = arm_name
            person_tables.append(pe)
            info["share_shrunk_positive"] = float(np.mean(pe["tau_shrunk"] > b[0])) if tau2_use > 0 else None
            # 3. how much of the between-person variance the baseline traits explain (cross-fitted between the halves)
            if traits and info.get("method") == "split_half" and tau2 > 0:
                tv = pd.DataFrame(sweep_vals[:, [sweep_names.index(t) for t in traits]], columns=traits)
                tv["cluster"] = frame.cluster
                per = tv.groupby("cluster")[traits].first().reindex(sh.cluster.to_numpy())
                okp = per.notna().all(axis=1).to_numpy()
                if okp.sum() > len(traits) + 30:
                    Z = per.to_numpy()[okp]
                    Z = (Z - Z.mean(axis=0)) / np.where(Z.std(axis=0) > 0, Z.std(axis=0), 1)
                    X = np.column_stack([np.ones(okp.sum()), Z])
                    A_, B_ = A[okp], B[okp]
                    resA = A_ - X @ np.linalg.lstsq(X, B_, rcond=None)[0]
                    resB = B_ - X @ np.linalg.lstsq(X, A_, rcond=None)[0]
                    full = float(np.cov(A_, B_)[0, 1])
                    left = float(np.cov(resA, resB)[0, 1])
                    info["explained_by_baseline"] = float(min(1.0, max(0.0, 1 - left / full))) if full > 0 else None
                    info["explained_people"] = int(okp.sum())
            hetero_info[arm_name] = info
            counts, edges = np.histogram(pe["tau_shrunk"], bins=24)
            hists[arm_name] = {"edges": [float(e) for e in edges], "counts": [int(c) for c in counts]}
    est = _collect(frame, pieces, {"estimator": "drwcls_hetero", "learner": learner, "folds": folds,
                                   "heterogeneity": hetero_info, "shrunk_hist": hists, "moderators_skipped": skipped,
                                   "note": ("between-person SD from alternating study weeks (split-half covariance), "
                                            "permutation p-value; REML with per-person variance shown alongside")})
    if extra_rows:
        est.table = est.table.merge(pd.DataFrame(extra_rows), on=["arm", "term"], how="left")
    if person_tables:
        est.diagnostics["person_effects"] = pd.concat(person_tables, ignore_index=True)
    return est
