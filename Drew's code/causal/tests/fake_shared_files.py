"""Small fake copies of the shared files, in their real formats, for end-to-end tests. No study data.

Both cohorts: one decision a day per person at 14:00 UTC, a message with probability 1/2 and one of nine message types
uniformly. Fitbit for even-numbered people and an Apple Watch for odd-numbered ones, worn all day. A message raises steps
in the following 24 hours by `step_effect` on the log scale, so the any-message effect on steps is known.
2025 domains rotate by week; 2024 draws a domain per message. 2025 has no neuroticism score, as in the real survey file.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd

from ihs_causal.data.decisions import ARMS, DOMAINS, STRATEGIES

START = {2024: "2024-08-05", 2025: "2025-08-04"}
ANCHOR_HOUR = 14


def _strategy(arm: str) -> str:
    return next(s for s in STRATEGIES if arm.startswith(s))


def _cohort(folder: Path, cohort: int, n_people: int, n_days: int, step_effect: float, rng: np.random.Generator) -> Dict:
    pids = [f"FAKE{cohort}-{i:03d}" for i in range(n_people)]
    days = pd.date_range(START[cohort], periods=n_days, freq="D")
    # decisions
    P, D = np.meshgrid(np.arange(n_people), np.arange(n_days), indexing="ij")
    P, D = P.ravel(), D.ravel()
    send = rng.random(P.size) < 0.5
    arm = np.where(send, np.array(ARMS)[rng.integers(0, len(ARMS), P.size)], "NoSend")
    anchor = days[D] + pd.Timedelta(hours=ANCHOR_HOUR)
    dec = pd.DataFrame({"decision_id": [f"d{cohort}-{p}-{d}" for p, d in zip(P, D)],
                        "participant_id": np.array(pids)[P], "decision_date": days[D].strftime("%Y-%m-%d"),
                        "action_sent": send.astype(int)})
    if cohort == 2025:
        week_domain = np.array(DOMAINS)[(D // 7 + P) % 3]
        dec["decision_domain"] = np.char.capitalize(week_domain.astype(str))
        dec["action_label"] = arm
        for pre in ("p_marginal_", "p_"):
            dec[f"{pre}no_send"] = 0.5
            for a in ARMS:
                dec[f"{pre}{a}"] = 0.5 / len(ARMS)
        dec.to_csv(folder / "2025BehaviorAgentProbabilities.csv", index=False)
        pd.DataFrame({"decision_id": dec.decision_id, "window_anchor_utc": anchor.strftime("%Y-%m-%dT%H:%M:%SZ"),
                      "retain_main_reach_retrospective": "True", "message_domain": np.where(send, week_domain, ""),
                      "core_message_id": np.where(send, "m1", "")}).to_csv(folder / "2025DecisionTiming.csv", index=False)
    else:
        domain = np.array(DOMAINS)[rng.integers(0, 3, P.size)]
        dec["hour_utc"] = anchor.strftime("%Y-%m-%dT%H:%M:%SZ")
        dec["domain"] = np.where(send, domain, "")
        dec["strategy"] = [(_strategy(a) if s else "") for a, s in zip(arm, send)]
        dec["personalization"] = [("NoData" if a.endswith("NoData") else "Data") if s else "" for a, s in zip(arm, send)]
        dec["core_message_id"] = np.where(send, "m1", "")
        dec["time_source"] = "logged"
        dec["p_send"], dec["p_no_send"] = 0.5, 0.5
        for a in ARMS:
            dec[f"p_{a}"] = 1 / len(ARMS)
        for d in DOMAINS:
            dec[f"p_{d}"] = 1 / 3
            for s in STRATEGIES:
                dec[f"p_{d}_{s}"] = sum(1 for a in ARMS if _strategy(a) == s) / len(ARMS) / 3
        dec.to_csv(folder / "2024BehaviorAgentProbabilities.csv", index=False)
    # hourly: every hour of the study for every person
    hours = pd.date_range(days[0], periods=(n_days + 1) * 24, freq="h")
    H = hours.size
    hp = np.repeat(np.arange(n_people), H)
    t = np.tile(np.arange(H), n_people)
    hod = np.tile(hours.hour.to_numpy(), n_people)
    awake = (hod >= 7) & (hod < 22)
    person_level = np.exp(rng.normal(0, 0.3, n_people))[hp]
    day_noise = np.exp(rng.normal(0, 0.2, (n_people, n_days + 1)))[hp, t // 24]
    steps = np.where(awake, rng.poisson(300, hp.size) * person_level * day_noise, 0.0)
    # a message raises steps from its decision hour to the next day's decision hour
    lift = np.ones(hp.size)
    sent_pd = send.reshape(n_people, n_days)
    window_day = (t - ANCHOR_HOUR) // 24            # the decision day whose post window holds this hour
    ok = (window_day >= 0) & (window_day < n_days)
    lift[ok] = np.where(sent_pd[hp[ok], window_day[ok]], np.exp(step_effect), 1.0)
    steps = np.round(steps * lift)
    hr = 70 + rng.normal(0, 5, hp.size)
    sleep = np.where((hod >= 23) | (hod < 6), np.clip(rng.normal(52, 6, hp.size), 0, 60), np.nan)
    mood = np.where((hod == 20) & (rng.random(hp.size) < 0.6), rng.integers(1, 11, hp.size), np.nan)
    fitbit = (hp % 2 == 0)
    hourly = pd.DataFrame({"participant_id": np.array(pids)[hp],
                           "time_utc": np.tile(hours.strftime("%Y-%m-%dT%H:%M:%SZ"), n_people),
                           "time_local": np.tile(hours.strftime("%Y-%m-%dT%H:%M:%S"), n_people), "Mood": mood})
    for dev, mask in (("Fitbit", fitbit), ("HealthkitWatch", ~fitbit)):
        hourly[f"{dev}_steps"] = np.where(mask, steps, np.nan)
        hourly[f"{dev}_hr_avg"] = np.where(mask, hr, np.nan)
        hourly[f"{dev}_sleep_minutes"] = np.where(mask, sleep, np.nan)
        hourly[f"{dev}_RHR"] = np.where(mask, 60.0, np.nan)
    hourly.to_csv(folder / f"dfHourly{cohort}.csv", index=False)
    # baseline survey (plus one follow-up column, which moderator analyses must refuse)
    s = pd.DataFrame({"PARTICIPANTIDENTIFIER": pids, "Age": rng.integers(24, 35, n_people), "Sex": rng.integers(1, 3, n_people),
                      "depr0": rng.integers(0, 2, n_people), "PHQtot0": rng.integers(0, 20, n_people),
                      "GADtot0": rng.integers(0, 18, n_people),
                      "Neu0_published": np.nan if cohort == 2025 else rng.normal(3, 0.7, n_people).round(2),
                      "SLE0": rng.integers(0, 8, n_people), "EFE0": rng.integers(0, 30, n_people),
                      "sleepAve0": rng.normal(7, 1, n_people).round(1), "PHQtot2": rng.integers(0, 20, n_people)})
    s.to_csv(folder / f"{cohort}SurveyData.csv", index=False)
    return {"decisions": len(dec), "hours": len(hourly)}


PACKAGE = Path(__file__).resolve().parents[1]
SMALL_CONFIGS = {
    "e2e_2025.yaml": """
name: e2e_2025
base: {cohort: 2025, min_arm_rows: 20}
sweep:
  device: [combined, apple]
  outcome: [steps, mood]
  contrast: [any_vs_none, type_vs_none]
""",
    "e2e_q6_2025.yaml": """
name: e2e_q6_2025
base:
  cohort: 2025
  outcome: steps
  contrast: any_vs_none
  estimator: {name: drwcls_hetero, learner: ridge, folds: 5, min_person_rows: 10, bootstrap: 100, permutations: 200}
  moderator_sweep: [Mood_pre, t, Age, PHQtot0, Neu0_published, sleepAve0]
  baseline_traits: [Age, PHQtot0, Neu0_published, sleepAve0]
""",
    "e2e_2024.yaml": """
name: e2e_2024
base: {cohort: 2024, outcome: steps, min_arm_rows: 20}
sweep:
  contrast: [any_vs_none, type_vs_none]
""",
}
SMALL_PIPELINE = "2025: [e2e_2025.yaml, e2e_q6_2025.yaml]\n2024: [e2e_2024.yaml]\n"


def make_project(root: Path) -> Path:
    """A project folder as a fresh checkout has it (the shipped config folder, no paths.yaml, no work folder), plus small
    configurations for the fake files in e2e_pipeline.yaml."""
    import shutil
    proj = Path(root) / "ihs-causal"
    (proj / "src" / "ihs_causal").mkdir(parents=True)          # marks the project folder for find_project_dir
    (proj / "pyproject.toml").write_text("", encoding="utf-8")
    shutil.copytree(PACKAGE / "config", proj / "config", ignore=shutil.ignore_patterns("paths.yaml"))
    for name, text in SMALL_CONFIGS.items():
        (proj / "config" / name).write_text(text, encoding="utf-8")
    (proj / "config" / "e2e_pipeline.yaml").write_text(SMALL_PIPELINE, encoding="utf-8")
    return proj


def write_shared_files(folder: Path, n_people: int = 48, n_days: int = 56, step_effect: float = 0.3, seed: int = 7) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    for cohort in (2024, 2025):
        _cohort(folder, cohort, n_people, n_days, step_effect, rng)
    return folder
