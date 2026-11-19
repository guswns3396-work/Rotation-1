"""Question 6 checks: moderation slopes, between-person SD of effects, share explained by a baseline trait."""
import math

import numpy as np

from ihs_causal.estimators.hetero import chi2_sf, drwcls_hetero, reml
from ihs_causal.results import add_bh
from ihs_causal.simulate import simulate_mrt


def test_chi2_sf_known_values():
    assert abs(chi2_sf(3.841458820694124, 1) - 0.05) < 1e-6
    assert abs(chi2_sf(18.307038053275146, 10) - 0.05) < 1e-6
    assert abs(chi2_sf(10.0, 10) - 0.44049328506521257) < 1e-8
    # large df: compare with the Wilson-Hilferty normal approximation
    k, x = 1000, 1200.0
    zwh = ((x / k) ** (1 / 3) - (1 - 2 / (9 * k))) / math.sqrt(2 / (9 * k))
    approx = 0.5 * math.erfc(zwh / math.sqrt(2))
    assert abs(chi2_sf(x, k) - approx) / approx < 0.02


def test_reml_recovers_between_study_variance():
    rng = np.random.default_rng(1)
    G = 4000
    v = rng.uniform(0.05, 0.5, G)
    y = 1.0 + rng.normal(0, 0.3, G) + rng.normal(0, np.sqrt(v))
    b, cov, tau2 = reml(y, v)
    assert abs(b[0] - 1.0) < 4 * math.sqrt(cov[0, 0])
    assert abs(math.sqrt(tau2) - 0.3) < 0.03


def test_hetero_recovers_moderation_and_person_variation():
    frame, truth = simulate_mrt(n_people=600, n_decisions=200, sd_u=0.2, slope1=0.2, seed=21)
    z = frame.extra["z"]
    frame.sweep_values = z[:, None]
    frame.sweep_names = ["z"]
    frame.baseline_traits = ["z"]
    frame.time_index = np.tile(np.arange(200), 600)
    est = drwcls_hetero(frame, bootstrap=100, permutations=500)
    t = est.table
    slope = t[(t.arm == "arm1") & (t.term == "mod:z")].iloc[0]
    sd_z = frame.sweep_values[:, 0].std()
    assert abs(slope.estimate / sd_z - truth["arm1_slope_z"]) < 4 * slope.se / sd_z
    h1 = est.diagnostics["heterogeneity"]["arm1"]
    true_tau = math.sqrt(0.2 ** 2 + (0.2 * sd_z) ** 2)
    assert h1["tau_ci"][0] - 0.05 < true_tau < h1["tau_ci"][1] + 0.05
    assert h1["method"] == "split_half" and h1["p_hetero"] < 0.01
    assert 0.25 < h1["explained_by_baseline"] < 0.75          # z explains about half of the person-level variance
    h2 = est.diagnostics["heterogeneity"]["arm2"]
    assert h2["tau_ci"][0] < 0.05 and h2["tau"] < 0.12         # arm 2 has a constant effect
    assert len(est.diagnostics["person_effects"]) > 1000


def test_bh_q_values_are_monotone_and_bounded():
    import pandas as pd
    est = pd.DataFrame({"run_id": "r", "contrast_label": "c", "arm": "a", "term": [f"mod:{i}" for i in range(5)],
                        "p": [0.001, 0.02, 0.03, 0.5, 0.9]})
    q = add_bh(est)["q_bh"].to_numpy()
    assert np.allclose(q, [0.005, 0.05, 0.05, 0.625, 0.9])


def test_weekly_block_variance_matches_iid_without_correlation_and_grows_with_it():
    from ihs_causal.estimators.hetero import person_effects
    rng = np.random.default_rng(3)
    people, days = 300, 140
    cluster = np.repeat(np.arange(people), days)
    t = np.tile(np.arange(days), people)
    y = rng.standard_normal(people * days)
    iid = person_effects(y, cluster, 10)
    blk = person_effects(y, cluster, 10, t // 7)
    assert 0.85 < np.median(blk.v / iid.v) < 1.15
    week_shock = np.repeat(rng.standard_normal(people * days // 7), 7)      # correlation within weeks
    y2 = y + week_shock
    ratio = person_effects(y2, cluster, 10, t // 7).v / person_effects(y2, cluster, 10).v
    assert np.median(ratio) > 3


def test_split_half_sign_flip_holds_its_size_with_unequal_noise():
    from ihs_causal.estimators.hetero import split_half_test
    rng = np.random.default_rng(5)
    rejections, reps = 0, 400
    for _ in range(reps):
        sd = rng.lognormal(0, 1.0, 500)               # very unequal noise between people, no true heterogeneity
        A, B = rng.normal(0, sd), rng.normal(0, sd)
        rejections += split_half_test(A, B, rng, bootstrap=50, draws=400)["p_hetero"] < 0.05
    assert rejections / reps < 0.08
    sd = rng.lognormal(0, 0.3, 500)
    tau = rng.normal(0, 1.0, 500)                      # true person effects with SD 1
    res = split_half_test(tau + rng.normal(0, sd), tau + rng.normal(0, sd), rng)
    assert res["p_hetero"] < 0.01 and res["tau_ci"][0] < 1.0 < res["tau_ci"][1] + 0.1
