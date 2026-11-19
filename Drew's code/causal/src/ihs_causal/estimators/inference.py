"""Normal-theory p-values and intervals, and a multiplier bootstrap for simultaneous intervals across a family of estimates.

The bootstrap reuses the per-participant influence contributions saved with each estimate, so it never refits a model:
a family of 50 estimates over 900 participants with 2,000 draws takes a fraction of a second.
"""
from __future__ import annotations

import math
from typing import Dict, Sequence, Tuple

import numpy as np

_erfc = np.vectorize(math.erfc, otypes=[float])
Z95 = 1.959963984540054


def two_sided_p(z: np.ndarray) -> np.ndarray:
    return _erfc(np.abs(np.asarray(z, dtype=float)) / math.sqrt(2.0))


def align_influence(items: Sequence[Tuple[np.ndarray, np.ndarray]]) -> Tuple[np.ndarray, np.ndarray]:
    """Stack per-cluster influence vectors from several estimates onto one cluster index (zeros where absent).

    items: sequence of (cluster_ids (G_j,), influence (G_j,)). Returns (all cluster ids (G,), matrix (G, J)).
    """
    ids = np.unique(np.concatenate([c for c, _ in items]))
    out = np.zeros((ids.size, len(items)))
    for j, (c, v) in enumerate(items):
        out[np.searchsorted(ids, c), j] = v
    return ids, out


def simultaneous_critical_value(psi: np.ndarray, se: np.ndarray, level: float = 0.95, draws: int = 2000,
                                seed: int = 20261117, chunk: int = 500) -> float:
    """Critical value c such that est +/- c*se covers all J estimates jointly with probability `level`.

    psi: (G, J) per-cluster influence contributions; se: (J,) standard errors of the same estimates.
    """
    rng = np.random.default_rng(seed)
    G, J = psi.shape
    scaled = psi / np.where(se > 0, se, np.inf)[None, :]
    maxima = np.empty(draws)
    for start in range(0, draws, chunk):
        b = min(chunk, draws - start)
        xi = rng.standard_normal((b, G))
        maxima[start:start + b] = np.abs(xi @ scaled).max(axis=1)
    return float(np.quantile(maxima, level))


def summarize(est: np.ndarray, se: np.ndarray) -> Dict[str, np.ndarray]:
    est = np.asarray(est, dtype=float)
    se = np.asarray(se, dtype=float)
    z = np.divide(est, se, out=np.full_like(est, np.nan), where=se > 0)
    return {"estimate": est, "se": se, "z": z, "p": two_sided_p(z), "ci_low": est - Z95 * se, "ci_high": est + Z95 * se}
