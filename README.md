# Heterogeneous Effects of Digital Health Messages in Medical Interns

Rotation project estimating overall and participant-level causal effects of mobile health notifications on mood, sleep, and step count in the Intern Health Study (2024 cohort, 2025 if time permits), using DR-WCLS pseudo-outcomes.

**Authors:** Jack Yang, Andrew Jones, Srijan Sen · **Contact:** Jack Yang (yhyunjoo@umich.edu)
**Current deliverable:** Internal report, due October 21, 2026

For background, aims, variables, and the full analysis plan, see [`proposal/proposal.pdf`](proposal/proposal.pdf).

## Repository layout

```
proposal/              Analytic memo (LaTeX source, bibliography, figures, PDF)
1_preprocess.ipynb     Python: build the analysis dataset from raw device, survey and intervention data
2_analysis.ipynb       R: H1, H2 and moderation analyses
config.yml             Local, uncommitted: path to the secure data directory
```

## Setup

Create `config.yml` in the repository root (do not commit it):

```yaml
data_path: /path/to/secure/storage
```

**Python** (preprocessing): pandas, numpy and the other packages imported in the first cell of `1_preprocess.ipynb`.

**R** (analysis, R 4.5): `yaml`, `here`, `readr`, `dplyr`, `tibble`, `tidyr`, `geepack`, `ranger`, `remotes`, and `MRTpostInfLASSO`, installed by the notebook from [WHD-Lab/DR_WCLS_LASSO](https://github.com/WHD-Lab/DR_WCLS_LASSO) at a pinned commit.

## Pipeline

Run the notebooks in order.

### 1. `1_preprocess.ipynb`

- **Interventions:** decisions, treatment (`action_id`, `message_metric`, `strategy`), and logged randomization probabilities. Adds combined strategy probabilities `p_strat_<code>` (Data + NoData versions) and `strategy_code` (CS, BS, MI, Mfn, DST), with checks that probabilities sum to 1.
- **Contexts:** hourly device and mood data, reshaped from wide to long by device; missing UTC times recovered from local time.
- **Windows:** one row per participant × device × window index `t`. Window `t` starts at decision `t` (or an interpolated time on days without a decision) and ends at the next window. `<stream>_post` summarizes window `t` (the proximal outcome) and `<stream>_pre` summarizes window `t − 1` (history).
- **Derived variables:** `log_steps_{pre,post}`, coverage shares `<stream>_cov_{pre,post}` (hours with data / window length), local-time `dow` and `weekend`.
- **Baseline survey** merged by participant.

Output: `processed/data_final_2024.csv` in the data directory.

### 2. `2_analysis.ipynb`

- **Data checks and variables:** treatment labels, probability checks, and coverage and window-length thresholds (step and sleep totals set to missing below 75% coverage or outside 20–28 h windows).
- **H1:** effect of a domain-specific message vs. no message on the outcome in its own domain (mood, log steps, sleep), plus any message vs. none. DR-WCLS pseudo-outcomes with cross-fitted random forest outcome models and known randomization probabilities; sandwich SEs clustered by participant; WCLS check; optional device-specific sensitivity analyses.
- **H2:** effect of each strategy vs. no message within each domain, with a Wald test that strategy effects are equal and Holm-adjusted pairwise differences. Includes a check of the independence assumption between message domain and strategy (`H2_MODE = "any_domain"` if it fails).
- **Moderation of strategy effects:** one moderator at a time and all jointly per strategy; tests of whether each moderator's slope differs across strategies (H4: PHQ-9, H5: depression history); baseline × context interactions per strategy.

Results are written to `results/H1`, `results/H2` and `results/moderation` inside the data directory, not the repository.

## Data and privacy

**Do not commit participant data** — raw or processed survey/device data, participant IDs, or participant-level results. Keep data in approved secure storage and reference it via the uncommitted `config.yml`. Commit only aggregate, de-identified outputs, and check your diff before pushing.

In particular:

- The saved pseudo-outcome files (`pseudo_*.rds`) are participant-level and stay in secure storage.
- **Clear notebook outputs before committing**; printed tables and data previews can contain participant-level values.
- Add `config.yml` to `.gitignore`.
