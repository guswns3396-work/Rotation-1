"""Weighted least squares with participant-clustered sandwich variance. Every estimator in the package reduces to this.

Speed notes: one pass builds X'WX and X'Wy with BLAS; per-cluster score sums use np.add.reduceat on rows sorted by
cluster once, so there is no Python loop over participants. For n = 300,000 rows and 40 columns a fit takes well
under a second.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class WLSResult:
    coef: np.ndarray        # (p,)
    cov: np.ndarray         # (p, p) cluster-robust covariance, small-sample factor G/(G-1)
    infl: np.ndarray        # (G, p) per-cluster influence: coef - truth is approximately infl.sum(axis=0)
    clusters: np.ndarray    # (G,) cluster ids, aligned with infl rows
    n: int

    @property
    def se(self) -> np.ndarray:
        return np.sqrt(np.clip(np.diag(self.cov), 0, None))


def cluster_sums(values: np.ndarray, cluster: np.ndarray):
    """Sum rows of `values` within clusters. Returns (unique cluster ids, sums)."""
    order = np.argsort(cluster, kind="stable")
    c_sorted = cluster[order]
    starts = np.flatnonzero(np.r_[True, c_sorted[1:] != c_sorted[:-1]])
    sums = np.add.reduceat(values[order], starts, axis=0)
    return c_sorted[starts], sums


def wls_cluster(X: np.ndarray, y: np.ndarray, w: np.ndarray, cluster: np.ndarray) -> WLSResult:
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    w = np.asarray(w, dtype=float)
    n, p = X.shape
    Xw = X * w[:, None]
    bread = Xw.T @ X
    try:
        bread_inv = np.linalg.inv(bread)
    except np.linalg.LinAlgError:
        bread_inv = np.linalg.pinv(bread)
    coef = bread_inv @ (Xw.T @ y)
    resid = y - X @ coef
    scores = Xw * resid[:, None]                     # (n, p)
    clusters, s = cluster_sums(scores, cluster)      # (G, p)
    infl = s @ bread_inv.T                           # (G, p)
    G = infl.shape[0]
    factor = G / (G - 1) if G > 1 else 1.0
    cov = factor * (infl.T @ infl)
    return WLSResult(coef=coef, cov=cov, infl=infl, clusters=clusters, n=n)
