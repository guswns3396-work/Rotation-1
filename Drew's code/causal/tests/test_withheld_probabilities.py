"""2025 decisions whose probabilities are not published (the September 4-27, 2025 fitted decisions, blank since the
November 19, 2026 release) are left out of every comparison and counted under their own reason in the diagnostics;
another domain's week stays 'no compared message possible'. Fake files only."""
import numpy as np
import pandas as pd

from fake_shared_files import write_shared_files
from ihs_causal.data.decisions import ARMS, decisions_2025
from ihs_causal.design.contrasts import CONTRASTS
from ihs_causal.paths import Paths
from ihs_causal.workspace import Workspace

WITHHELD = ("2025-08-20", "2025-08-31")


def _blank(shared):
    p = shared / "2025BehaviorAgentProbabilities.csv"
    df = pd.read_csv(p, dtype=str, keep_default_na=False)
    rows = (df.decision_date >= WITHHELD[0]) & (df.decision_date <= WITHHELD[1])
    cols = [c for c in df.columns if c.startswith("p_")]
    df.loc[rows, cols] = ""
    df.to_csv(p, index=False)
    return int(rows.sum())


def test_withheld_probabilities_are_dropped_and_counted(tmp_path):
    shared = write_shared_files(tmp_path / "shared", n_people=30, n_days=42)
    n_blank = _blank(shared)
    dec = decisions_2025(shared / "2025BehaviorAgentProbabilities.csv", shared / "2025DecisionTiming.csv")
    blank = dec.decision_date.between(*WITHHELD).to_numpy()
    assert blank.sum() == n_blank and dec.loc[blank, "p_none"].isna().all()
    for d in ("mood", "steps", "sleep"):           # another domain's week is an exact 0, published or not
        other = blank & (dec.domain.to_numpy() != d)
        assert (dec.loc[other, f"p_dom_{d}"] == 0).all() and (dec.loc[other, f"p_type_{d}_{ARMS[0]}"] == 0).all()
        assert dec.loc[blank & ~other, f"p_dom_{d}"].isna().all()

    paths = Paths(data_root=shared, work_dir=tmp_path / "work", project_dir=tmp_path, overrides={})
    ws = Workspace(paths, log=lambda m: None)
    spec = {"cohort": 2025, "outcome": "steps", "device": "combined", "window": {"name": "next_decision"}, "keep": {},
            "controls": [], "min_prob": 0.001, "min_arm_rows": 20}
    df = ws.features(spec)
    in_blank = df.decision_date.astype(str).between(*WITHHELD).to_numpy() & df.log_steps_post.notna().to_numpy()
    (_, _, _, frame, info), = CONTRASTS.get("any_vs_none")(df, "steps", spec)
    assert info["rows_probability_missing"] == int(in_blank.sum()) > 0
    assert info["rows_no_message_possible"] == 0 and frame.n == info["rows_candidate"] - info["rows_outcome_missing"] - int(in_blank.sum())
    _, _, _, frame_d, info_d = next(i for i in CONTRASTS.get("domain_vs_none")(df, "steps", spec) if i[2] == "steps")
    steps_week = df.domain.to_numpy() == "steps"
    assert info_d["rows_probability_missing"] == int((in_blank & steps_week).sum())    # only the steps weeks' blanks
    no_send = df.send.to_numpy() == 0            # in other weeks only no-message decisions are candidates here
    assert info_d["rows_no_message_possible"] == int((~steps_week & no_send & df.log_steps_post.notna().to_numpy()).sum())
    assert np.isfinite(frame_d.prob).all()
