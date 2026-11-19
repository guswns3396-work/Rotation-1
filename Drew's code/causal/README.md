# ihs-causal

Fast, modular causal excursion-effect analysis for the IHS micro-randomized trials (2024 and 2025 cohorts, analysed
separately), with a results app that can also run new analyses. Anyone with the shared study files can run the whole
pipeline and the app from this repository. The methods are in [docs/DESIGN.md](docs/DESIGN.md).

## What the repository holds

- **In it:** the code, the analysis configurations, tests that run on fake data, and the docs.
- **Never in it** (`.gitignore`): study data, `config/paths.yaml` (your machine's data location), and `work/` (caches,
  results, person-level effects, snapshots).
- **Results stay local.** The app and snapshots hold aggregate results only, but they are study results; person-level
  effect estimates stay in `work/results/person_effects.parquet`. Check with Drew before sharing anything from `work/`
  outside the study team.

## Start the app

No installation and no terminal commands are needed.

1. **Double-click the launcher** in this folder: **`Start (Windows).bat`** on Windows, or **`Start (Mac).command`** on a
   Mac.
   - The first start sets up a private Python environment in the `.venv` folder here. It takes a few minutes and
     needs the internet. Later starts take seconds.
   - It uses any Python 3.9 or later already on the computer. If there is none, it offers to install
     [uv](https://docs.astral.sh/uv/), a small tool from astral.sh that brings its own Python and needs no
     administrator rights. Nothing else is installed outside this folder.
   - The app opens in the browser. Keep the launcher's window open while you use it; close the window to stop the app.
     Starting it again while it runs just opens it again.
2. **The first time, choose the data folder**, the one holding the shared study files. The app checks the files,
   reading their column names only, and remembers the folder. To change it later, go to About and click *Change…*.
3. **Click *Run the standard analyses*.** This runs questions 1 to 6 for every device and outcome. It takes roughly 15
   minutes the first time and about 4 GB of memory. Results appear as each analysis is stored, and the app can be used
   meanwhile. Analyses already stored from the same files are never redone, so the app can be closed partway and
   started again.

**Tested:**
- **Windows:** a first start with Python 3.12 downloaded pandas 3.1, numpy 2.5 and pyarrow 26 in about a minute.
  The same analyses on pandas 2.3 give the same estimates.
- **Mac:** the Mac launcher has not yet been run on a Mac.

**On a Mac, the first time:**
- If macOS says the launcher cannot be opened because it comes from the internet, right-click it and choose *Open*.
- If it says you lack permission, open Terminal in this folder and run `bash "Start (Mac).command"` once.

## Command line (optional)

Everything the app does can also be run from a terminal, for scripting or for a server without a browser. With conda:

```bash
conda env create -f environment.yml
conda activate ihs-causal
pip install -e .
```

Or install into any Python 3.9 or later with `pip install -e ".[test]"`. The dependencies, listed in
`requirements.txt`, are numpy, pandas, pyarrow and pyyaml. Then:

```bash
ihs-causal setup "/path/to/shared folder"   # what the app's first page does: writes config/paths.yaml, then checks
pytest -q                                   # the install, on fake data only (about 15 seconds)
ihs-causal reproduce                        # every standing analysis, then a static snapshot
ihs-causal serve                            # the app
```

- **What `check` shows:** every file the engine reads, whether it has the columns needed, and the start of its
  SHA-256. Fix anything marked `NOT FOUND` or `MISSING COLUMNS`. See *The data files* below.
- **`reproduce` options:** `--cohort 2025` runs one cohort; `--dry-run` counts what would run.
- **Without installing:** run any command as `python -m ihs_causal.cli <command>` with `PYTHONPATH=src`.
- **With the launcher's environment:** run commands as `.venv/Scripts/python -m ihs_causal.cli <command>` on Windows,
  or `.venv/bin/python -m ihs_causal.cli <command>` on a Mac.
- **Where to run commands:** from this folder, which is where they find `config/`. Or point `IHS_CAUSAL_PATHS` at a
  paths file.

## The data files

| Cohort | File in the shared folder | Needed for |
|---|---|---|
| 2025 | `dfHourly2025.csv` | wearable and mood outcomes and history |
| 2025 | `2025BehaviorAgentProbabilities.csv` | decisions and randomization probabilities |
| 2025 | `2025DecisionTiming.csv` | window anchors and the analysis flag |
| 2025 | `2025SurveyData.csv` | baseline traits |
| 2024 | `dfHourly2024.csv` | wearable and mood outcomes and history |
| 2024 | `2024BehaviorAgentProbabilities.csv` | decisions and randomization probabilities |
| 2024 | `2024SurveyData.csv` | baseline traits |
| 2024 | `2024MessageTypeProbabilities.csv.gz` (optional) | the 2024 message-type questions only; without it they have nothing to estimate |

A cohort whose files are missing is skipped. `config/paths.yaml` can read any file from somewhere else under `files:`,
where a relative path is inside the shared folder. Setup (the app's first page, or `ihs-causal setup`) takes these
from `config/paths.example.yaml`, which points the hourly files at the dated mood-corrected copies
(`Hourly_MoodCorrected_20261117/`) that every current result uses. Where the folder has no such copy, setup reads the
standard file instead and says so. Delete those lines from the example once the reviewed files replace the standard
ones.

**Getting the same numbers.** Results depend only on the settings and the input files. Every stored result records the
SHA-256 of each file that made it, and the About tab lists them. If `ihs-causal check` prints the same fingerprints on
two machines, `reproduce` gives the same estimates. Cross-fitting folds and bootstraps use fixed seeds; only the last
digits can differ between library versions. The files behind the results as of November 18, 2026 began:

| Cohort | hourly | decisions | timing | surveys | message types |
|---|---|---|---|---|---|
| 2025 | `2df0f3e1131d` | `6704c3b2968a` | `825e04e45462` | `7a9285b1cfbc` | — |
| 2024 | `c16bd124c02d` | `c5adc147f636` | — | `2db2f48f7ef6` | `686c1f4366ba` |

## Commands

```bash
ihs-causal setup FOLDER        # write config/paths.yaml for this machine, then check the files
ihs-causal check               # every file found, with the columns needed, and its fingerprint (headers only)
ihs-causal reproduce           # every standing analysis in config/pipeline.yaml, then the snapshot
ihs-causal serve               # the results app in your browser; its Run tab runs new analyses
ihs-causal run config/X.yaml   # one configuration (--force recomputes stored runs)
ihs-causal view                # a static HTML snapshot of the results (work/ihs_causal_results.html)
ihs-causal refresh             # rerun every stored analysis made from older data files (--dry-run lists them)
ihs-causal prune config/X.yaml # drop stored runs a changed configuration no longer produces
ihs-causal list                # registered outcomes, contrasts, estimators, learners, windows
ihs-causal selftest            # the estimators on simulated trials at study scale
```

When a data file changes, the app flags the analyses made from the earlier file at the top of the page, with a button
that reruns them on the current files. A rerun replaces the earlier result.

The app checks the results store every few seconds and reloads whenever something was stored or removed, including runs
started with `ihs-causal run` in a terminal. Each run in the Run tab is saved under its label: two saved analyses with
the same settings are kept apart, and running a label again replaces it. *Show results* opens exactly that run's
estimates at its own cohort and device.

### Who responds

Tick *Who responds* in the Run tab to estimate, for every question ticked above it (any message, domains, strategies,
message types, own data), how each message's effect changes with each characteristic, and how much true effects vary
between people. Choose the characteristics: the context of the day before, the standard baseline traits, and any other
baseline (wave 0) survey column, typed or picked from the list with the share of respondents who answered it.
Follow-up survey waves are refused, because they were answered after messages began. Every other setting in the form
(device, dates, keep rules, probability floor) applies. The *Who responds* tab shows a grid of characteristics against
messages for any saved analysis, with a plot and a table for the column or row you click. A characteristic a cohort has
no values for is listed as not estimated. For example, 2025 has no neuroticism score.

## Configurations shipped

| File | What it runs |
|---|---|
| `pipeline.yaml` | The standard analyses, by cohort: what *Run the standard analyses* and `ihs-causal reproduce` run |
| `primary_2025.yaml`, `primary_2024.yaml` | Questions 1 to 5, every device (Combined, Apple, Garmin, Fitbit), all three outcomes |
| `primary_2025_apple_watch.yaml`, `primary_2024_apple_watch.yaml` | The same for Apple, watch data only |
| `q6_2025.yaml`, `q6_2024.yaml` | Question 6 (moderators and variation between people), every device |
| `data_notes.yaml` | Notes about particular data files, shown above a cohort's results where that file is in use |
| `paths.example.yaml` | The template for `config/paths.yaml` |

## Writing a configuration

A configuration has a `base` (settings merged over the defaults in `src/ihs_causal/defaults.yaml`, which hold the
primary specification) and a `sweep` (any key, dotted for nested keys, with a list of values; every combination runs):

```yaml
name: steps_observed_hours
base:
  cohort: 2025
  outcome: steps
  device: apple
  apple_source: watch_only
sweep:
  keep.steps_min_observed_hours: [6, 8, 10, 12, 14]
  contrast: [any_vs_none, domain_vs_none]
```

Add it to `config/pipeline.yaml` to make it a standing analysis.

## Rules built in

- **Devices:** `combined` (each person's main device), `apple` (watch, else phone; `apple_source: watch_only` for the
  watch alone), `garmin`, `fitbit`.
- **Keep rules:**
  - Steps need at least 10 observed hours in the day (heart rate or steps present).
  - Sleep is kept per night when a sleep record exists; short nights only if the device was worn overnight.
  - Mood is kept when a response exists.
  - All are settings under `keep:`, and the app's About tab explains them.
- **Low probabilities:**
  - Decisions where a compared arm had a probability below `min_prob` (0.001) are left out, and so are arms with fewer
    than `min_arm_rows` (200) decisions.
  - With `positivity: pairwise` (the default) a multi-arm contrast runs one comparison per arm and checks only the two
    arms compared. `joint` checks every arm at once.
  - All three are settings in the Run tab.
- **Dates:** `date_from` and `date_to` (YYYY-MM-DD, inclusive) restrict an analysis to a range of decision dates. Unset
  means the whole study year.
- **Message types:** `type_vs_none` compares each of the nine types (strategy with or without own data) with no message.

## Layout

```
Start (Windows).bat, Start (Mac).command   double-click launchers (environment in .venv/, then the app)
requirements.txt                           the four dependencies, for the launchers and pyproject.toml
src/ihs_causal/
  data/        hourly.py, decisions.py, windows.py, features.py (window statistics + keep rules)
  design/      contrasts.py
  estimators/  frame.py, wls.py, core.py (WCLS, DR-WCLS), hetero.py (question 6), nuisance.py, inference.py
  config.py  paths.py  check.py  cache.py  workspace.py  runner.py  results.py  serve.py  cli.py  simulate.py
  viewer/      build.py, template.html
config/        paths.example.yaml, pipeline.yaml, primary_*.yaml, q6_*.yaml, data_notes.yaml
docs/          DESIGN.md
tests/         unit tests; test_end_to_end.py and test_app_setup.py run the pipeline and the app's first start on
               fake files in the real formats (fake_shared_files.py)
scripts/       serve_dev.py (the app without installing)
```
