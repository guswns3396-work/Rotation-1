"""The one object every estimator consumes.

A contrast builder (ihs_causal.design) turns a decision table into an AnalysisFrame for one outcome:
the rows to analyse, which arm each row received (0 is the reference arm), the randomization
probability of every analysed arm at that decision, the participant of each row, and the covariates.
Estimators never look at the decision table, so they work the same for every cohort and contrast.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


@dataclass
class AnalysisFrame:
    y: np.ndarray                 # (n,) outcome, no missing values
    arm: np.ndarray               # (n,) int in 0..K; 0 is the reference arm
    prob: np.ndarray              # (n, K+1) P(arm a | history), renormalised over the analysed arms
    cluster: np.ndarray           # (n,) participant code (int)
    controls: np.ndarray          # (n, p) control covariates for the outcome model, no intercept column
    moderators: np.ndarray        # (n, q) effect moderators S, no intercept column (q may be 0)
    arm_names: List[str]
    control_names: List[str] = field(default_factory=list)
    moderator_names: List[str] = field(default_factory=list)
    p_tilde: Optional[np.ndarray] = None   # (K+1,) numerator probabilities; default: mean of prob columns
    label: str = ""

    def __post_init__(self) -> None:
        n = self.y.shape[0]
        self.y = np.asarray(self.y, dtype=float)
        self.arm = np.asarray(self.arm, dtype=np.int64)
        self.prob = np.asarray(self.prob, dtype=float)
        self.cluster = np.asarray(self.cluster)
        self.controls = self._rows(self.controls, n)
        self.moderators = self._rows(self.moderators, n)
        k1 = len(self.arm_names)
        if self.prob.shape != (n, k1):
            raise ValueError(f"prob has shape {self.prob.shape}, expected {(n, k1)}")
        for name, a in (("arm", self.arm), ("cluster", self.cluster), ("controls", self.controls), ("moderators", self.moderators)):
            if a.shape[0] != n:
                raise ValueError(f"{name} has {a.shape[0]} rows, expected {n}")
        if self.arm.min(initial=0) < 0 or self.arm.max(initial=0) >= k1:
            raise ValueError("arm codes must lie in 0..K")
        if not np.isfinite(self.y).all():
            raise ValueError("outcome has missing or infinite values; drop those rows in the contrast builder")
        if not (np.isfinite(self.controls).all() and np.isfinite(self.moderators).all()):
            raise ValueError("covariates have missing values; impute or drop them in the contrast builder")
        p_obs = self.prob[np.arange(n), self.arm]
        if (p_obs <= 0).any():
            raise ValueError(f"{int((p_obs <= 0).sum())} rows received an arm with recorded probability 0")
        if self.p_tilde is None:
            self.p_tilde = self.prob.mean(axis=0) if n else np.full(k1, np.nan)
        self.p_tilde = np.asarray(self.p_tilde, dtype=float)

    @staticmethod
    def _rows(a, n: int) -> np.ndarray:
        """A covariate block as an (n, columns) array. A frame with no rows (a comparison where no decision qualifies,
        e.g. the 2024 message types without their probability file) stays valid, so the runner can skip it."""
        a = np.asarray(a, dtype=float)
        if n == 0:
            return a.reshape(0, a.shape[1] if a.ndim == 2 else 0)
        return a.reshape(n, -1)

    @property
    def n(self) -> int:
        return int(self.y.shape[0])

    @property
    def n_arms(self) -> int:
        """Number of non-reference arms K."""
        return len(self.arm_names) - 1

    def subset(self, mask: np.ndarray) -> "AnalysisFrame":
        return AnalysisFrame(self.y[mask], self.arm[mask], self.prob[mask], self.cluster[mask], self.controls[mask],
                             self.moderators[mask], self.arm_names, self.control_names, self.moderator_names,
                             self.p_tilde, self.label)
