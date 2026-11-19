"""Outcome-model learners for DR-WCLS, cross-fitted by participant.

Default learner: ridge regression with the penalty chosen by generalized cross-validation, computed from one
eigendecomposition per fit (no inner loop), so a fold fit costs about as much as one least-squares solve.
Other learners register under LEARNERS and must provide fit(X, y) and predict(X).
"""
from __future__ import annotations

from typing import Callable, Optional

import numpy as np

from ihs_causal.registry import Registry

LEARNERS = Registry("learner")


class RidgeGCV:
    def __init__(self, grid: Optional[np.ndarray] = None):
        self.grid = grid if grid is not None else np.logspace(-6, 1, 29)   # multiples of n

    def fit(self, X: np.ndarray, y: np.ndarray) -> "RidgeGCV":
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        n = X.shape[0]
        self.x_mean = X.mean(axis=0)
        self.x_sd = X.std(axis=0)
        self.x_sd[self.x_sd == 0] = 1.0
        self.y_mean = y.mean()
        if X.shape[1] == 0:
            self.beta = np.zeros(0)
            self.lam = 0.0
            return self
        Z = (X - self.x_mean) / self.x_sd
        yc = y - self.y_mean
        d, V = np.linalg.eigh(Z.T @ Z)
        d = np.clip(d, 0, None)
        zv = V.T @ (Z.T @ yc)
        yy = float(yc @ yc)
        best = None
        for lam in self.grid * n:
            inv = 1.0 / (d + lam)
            rss = yy - 2 * np.sum(zv ** 2 * inv) + np.sum(d * zv ** 2 * inv ** 2)
            df = np.sum(d * inv)
            gcv = rss / (n * (1 - df / n) ** 2)
            if best is None or gcv < best[0]:
                best = (gcv, lam)
        self.lam = best[1]
        self.beta = V @ (zv / (d + self.lam))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.beta.size == 0:
            return np.full(X.shape[0], self.y_mean)
        return self.y_mean + ((np.asarray(X, dtype=float) - self.x_mean) / self.x_sd) @ self.beta


class MeanLearner:
    def fit(self, X: np.ndarray, y: np.ndarray) -> "MeanLearner":
        self.m = float(np.mean(y))
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        return np.full(X.shape[0], self.m)


LEARNERS.register("ridge")(RidgeGCV)
LEARNERS.register("mean")(MeanLearner)


def participant_folds(cluster: np.ndarray, k: int, seed: int = 20261117) -> np.ndarray:
    """Fold number for every row; all rows of a participant share a fold."""
    ids, inverse = np.unique(cluster, return_inverse=True)
    rng = np.random.default_rng(seed)
    return (rng.permutation(ids.size) % k)[inverse].astype(np.int64)


def crossfit_arm_means(features: np.ndarray, y: np.ndarray, arm: np.ndarray, n_arms_total: int, cluster: np.ndarray,
                       learner: str = "ridge", k: int = 5, seed: int = 20261117, min_rows: int = 50) -> np.ndarray:
    """mu[i, a]: cross-fitted prediction of the outcome under arm a for row i, from a model fitted only on
    other participants' rows that received arm a. Arms with fewer than `min_rows` training rows fall back to the mean."""
    make: Callable = LEARNERS.get(learner)
    folds = participant_folds(cluster, k, seed)
    mu = np.empty((y.shape[0], n_arms_total))
    for f in range(k):
        test = folds == f
        for a in range(n_arms_total):
            train = (~test) & (arm == a)
            model = make() if train.sum() >= min_rows else MeanLearner()
            if train.sum() == 0:
                mu[test, a] = np.nan
                continue
            model.fit(features[train], y[train])
            mu[test, a] = model.predict(features[test])
    if np.isnan(mu).any():
        col_means = np.nanmean(mu, axis=0)
        mu = np.where(np.isnan(mu), col_means[None, :], mu)
    return mu
