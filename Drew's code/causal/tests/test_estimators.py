"""Estimator checks on simulated trials with known effects."""
import time

import numpy as np

from ihs_causal.estimators import AnalysisFrame, drwcls, wcls
from ihs_causal.estimators.inference import align_influence, simultaneous_critical_value
from ihs_causal.estimators.wls import wls_cluster
from ihs_causal.simulate import simulate_mrt


def _get(est, arm, term="effect"):
    t = est.table
    row = t[(t.arm == arm) & (t.term == term)].iloc[0]
    return row.estimate, row.se


def test_wls_matches_lstsq_and_clustered_variance_is_positive():
    rng = np.random.default_rng(0)
    X = np.column_stack([np.ones(500), rng.standard_normal((500, 3))])
    y = X @ np.array([1.0, 2.0, -1.0, 0.5]) + rng.standard_normal(500)
    res = wls_cluster(X, y, np.ones(500), np.repeat(np.arange(50), 10))
    assert np.allclose(res.coef, np.linalg.lstsq(X, y, rcond=None)[0])
    assert (np.diag(res.cov) > 0).all()
    assert np.allclose(res.infl.sum(axis=0), 0, atol=1e-8)   # scores sum to zero at the solution


def test_wcls_and_drwcls_recover_marginal_effects():
    frame, truth = simulate_mrt(n_people=400, n_decisions=150, seed=3)
    for fit in (wcls(frame), drwcls(frame)):
        for arm in ("arm1", "arm2"):
            est, se = _get(fit, arm)
            assert abs(est - truth[arm]) < 4 * se, (fit.diagnostics["estimator"], arm, est, se)


def test_moderator_slope_recovered():
    frame, truth = simulate_mrt(n_people=400, n_decisions=150, seed=5)
    z = frame.extra["z"]
    mod = AnalysisFrame(frame.y, frame.arm, frame.prob, frame.cluster, frame.controls, (z - z.mean())[:, None],
                        frame.arm_names, frame.control_names, ["z"])
    for fit in (wcls(mod), drwcls(mod)):
        est, se = _get(fit, "arm1", "z")
        assert abs(est - truth["arm1_slope_z"]) < 4 * se
        est2, se2 = _get(fit, "arm2", "z")
        assert abs(est2) < 4 * se2


def test_wcls_interval_coverage_is_near_nominal():
    hits, reps = 0, 120
    for s in range(reps):
        frame, truth = simulate_mrt(n_people=120, n_decisions=40, seed=1000 + s)
        est, se = _get(wcls(frame), "arm1")
        hits += abs(est - truth["arm1"]) <= 1.96 * se
    assert 0.88 <= hits / reps <= 0.99


def test_drwcls_is_more_efficient_than_wcls_here():
    frame, _ = simulate_mrt(n_people=300, n_decisions=100, seed=7)
    _, se_w = _get(wcls(frame), "arm1")
    _, se_d = _get(drwcls(frame), "arm1")
    assert se_d <= se_w * 1.05


def test_simultaneous_critical_value_exceeds_pointwise():
    frame, _ = simulate_mrt(n_people=200, n_decisions=60, seed=9)
    fit = wcls(frame)
    items = [fit.influence[("arm1", "effect")], fit.influence[("arm2", "effect")]]
    _, psi = align_influence(items)
    c = simultaneous_critical_value(psi, fit.table.se.to_numpy(), draws=1000)
    assert 1.96 < c < 2.6


def test_speed_at_study_scale():
    frame, _ = simulate_mrt(n_people=900, n_decisions=330, seed=11)   # about 300,000 decisions
    t0 = time.perf_counter(); wcls(frame); t_w = time.perf_counter() - t0
    t0 = time.perf_counter(); drwcls(frame); t_d = time.perf_counter() - t0
    print(f"wcls {t_w:.2f}s, drwcls {t_d:.2f}s on {frame.n:,} rows")
    assert t_w < 5 and t_d < 30
