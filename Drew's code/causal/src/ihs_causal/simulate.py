"""Simulated micro-randomized trials with known effects, for tests, benchmarks and checking new estimators.

Three arms (0 = reference). Randomization probabilities depend on a time-varying covariate x, so unweighted regression
would be biased when the outcome model is wrong; the outcome has a non-linear term in x that a linear outcome model
misses. True excursion effects:  arm 1 vs 0 = effect1 + slope1 * z  (z is a person-level trait with mean 0),
arm 2 vs 0 = effect2.  Person-level heterogeneity sd_u adds a random effect to arm 1.
"""
from __future__ import annotations

from typing import Dict, Tuple

import numpy as np

from ihs_causal.estimators.frame import AnalysisFrame


def simulate_mrt(n_people: int = 300, n_decisions: int = 100, effect1: float = 0.3, slope1: float = 0.2,
                 effect2: float = -0.1, sd_u: float = 0.2, seed: int = 1) -> Tuple[AnalysisFrame, Dict[str, float]]:
    rng = np.random.default_rng(seed)
    n = n_people * n_decisions
    person = np.repeat(np.arange(n_people), n_decisions)
    z_person = rng.standard_normal(n_people)
    b_person = rng.standard_normal(n_people)
    u_person = sd_u * rng.standard_normal(n_people)
    z, b, u = z_person[person], b_person[person], u_person[person]
    x = rng.standard_normal(n)
    sig = 1.0 / (1.0 + np.exp(-1.5 * x))
    p1 = 0.5 * (0.15 + 0.7 * sig)
    p2 = 0.5 - p1
    p0 = np.full(n, 0.5)
    prob = np.column_stack([p0, p1, p2])
    cum = prob.cumsum(axis=1)
    draw = rng.random(n)
    arm = (draw[:, None] > cum).sum(axis=1)
    y = (1.0 + b + 0.8 * x + 0.5 * x ** 2
         + (arm == 1) * (effect1 + slope1 * z + u)
         + (arm == 2) * effect2
         + rng.standard_normal(n))
    frame = AnalysisFrame(y=y, arm=arm, prob=prob, cluster=person, controls=x[:, None], moderators=np.zeros((n, 0)),
                          arm_names=["none", "arm1", "arm2"], control_names=["x"])
    truth = {"arm1": effect1, "arm2": effect2, "arm1_slope_z": slope1}
    frame.extra = {"z": z}   # type: ignore[attr-defined]
    return frame, truth
