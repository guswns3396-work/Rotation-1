# 08. Control sets

**Summary.** The effect models adjust for variables measured before each decision. The engine's WCLS uses five:
day-before mood, steps and sleep, study day, and baseline PHQ-9, with missing values filled by the median. The report's
standard set adds the participant's own past mean of the outcome and two missing-value flags; it is the set behind the
report's effect estimates and the presentation's figures (each pipeline script calls
`control_sets.effect_controls(ctx, cohort, t, "standard", outcome, None)`). Three fuller sets (week, long, long_others)
add the outcome's earlier days, the other outcomes, weekday, device and other participants' same-day values; they enter
as principal components and are used only in the report's precision chapter and one weather analysis. In WCLS the
controls change precision, not the quantity estimated ([11](11-model.md#estimand)); no row is ever dropped for a
missing control.

## Contents

- [Which set each pipeline uses](#which-set-each-pipeline-uses)
- [The engine's five](#the-engines-five)
- [Missing values in the engine](#missing-values-in-the-engine)
- [The standard set](#the-standard-set)
- [The week set](#the-week-set)
- [The long set](#the-long-set)
- [The long_others set](#the-long_others-set)
- [How the fuller sets enter the model](#how-the-fuller-sets-enter-the-model)
- [Moderators as controls](#moderators-as-controls)
- [Outcome-model variables (DR-WCLS)](#outcome-model-variables-dr-wcls)
- [The prediction test](#the-prediction-test)
- [What the presentation uses](#what-the-presentation-uses)
- [Where code and documentation disagree](#where-code-and-documentation-disagree)
- [Unverified](#unverified)

## Which set each pipeline uses

The sets are nested: each contains the one before. [src: report/ihs_report/controls.py, module docstring, columns]

| Set (`level`) | Columns | Used by | Status |
|---|---|---|---|
| `engine` | The engine's five | Engine WCLS runs (`controls` in `causal/src/ihs_causal/defaults.yaml`); report precision chapter (`control_effects`) | Applied in the engine; Option in the report |
| `standard` | engine + own past mean of the outcome + two flags (8 columns) | Report: message and strategy effects (`pooled_effects`), every moderator analysis by default (`moderation.fit_cohort`); presentation: figure 1b (`screen_fit.py`, `cumulative_fit.py`) and figure 2 (`joint_fit.py`); figure 1 by the statement in `cumulative_fit.py` that it uses "the same model" (the scripts that make figure 1's source tables are not in the pipeline folder; `<scratch>/usual_set_temperature.py` and `<scratch>/tier_effects.py` both use the standard set) | Applied |
| `week` | engine + weekday + the outcome's previous week (16 columns) | Report precision chapter only | Option, not default |
| `long` | week + longer history, other outcomes, device, squared study day (38 columns) | Report precision chapter; weather under long-history controls (`weather_moderation_long`); further control blocks (`control_blocks`) | Option, not default |
| `long_others` | long + other participants' same-date values (40 columns) | Report precision chapter only | Option, not default |

[src: report/ihs_report/controls.py, columns, LEVELS; report/ihs_report/analyses/pooled_effects.py;
report/ihs_report/moderation.py, fit_cohort (default `level="standard"`); report/ihs_report/analyses/control_effects.py,
control_sets.py; report/ihs_report/analyses/weather_moderation_long.py; <vault>/Presentation Plots/pipeline/screen_fit.py,
joint_fit.py, cumulative_fit.py, fit_cohort]

Column counts are derived from `columns()`; the engine and standard sets enter the model as they are, the fuller sets
as components ([below](#how-the-fuller-sets-enter-the-model)).

## The engine's five

`controls: [Mood_pre, log_steps_pre, sleep_minutes_pre, t, PHQtot0]`, the same list in the engine defaults and in the
report's settings (`controls.engine`). Applied.
[src: causal/src/ihs_causal/defaults.yaml, `controls`; report/config/analysis.yaml, `controls.engine`]

| Column | What it is | How it is computed | Missing before imputation when |
|---|---|---|---|
| `Mood_pre` | Day-before mood | Mean mood response in the pre window (yesterday's window when decisions are consecutive) | No pre window, span outside 20 to 28 hours, or no response |
| `log_steps_pre` | Day-before steps | log(1 + steps) in the pre window under the steps keep rule (10 observed hours, a step record) | Keep rule fails; in the report and presentation also a total below one step |
| `sleep_minutes_pre` | Last night's sleep | Minutes asleep in the pre window, which runs from yesterday's decision to this one, under the sleep keep rule | Keep rule fails (no record, or a short night without overnight wear) |
| `t` | Study day | Grid days since the participant's first analysed decision; skipped and excluded days count | Never |
| `PHQtot0` | Baseline depression (PHQ-9 total) | Column `PHQtot0` of `<cohort>SurveyData.csv`, read as a number and joined by participant; the first row per participant is kept | No survey row or no value |

[src: causal/src/ihs_causal/data/features.py, apply_rules, baseline_traits; causal/src/ihs_causal/data/windows.py,
next_decision_windows; report/ihs_report/build/history.py, zero_step_days_missing]

Window and keep rules behind the day-before values: [07](07-outcome-windows.md#the-day-before-values). The study day
is not reset by a date range or a period: a January to June fit keeps the study day counted from the participant's
first analysed decision in July or later. [src: causal/src/ihs_causal/data/features.py, window_stats (study day built
on the whole analysis set), in_dates]

## Missing values in the engine

Applied. [src: causal/src/ihs_causal/data/features.py, covariate_matrix; causal/src/ihs_causal/design/contrasts.py,
_frame]

- **Median imputation per analysis frame.** Each control's missing values are replaced by its median over the rows of
  that frame, the decisions left after every row filter of the comparison ([10](10-analysis-rules.md)). The median is
  therefore recomputed for each comparison, each compared arm under pairwise positivity, each cohort, period and
  moderator subset. A control with no value in the frame is set to 0, which makes it constant, so it is dropped (two
  items below).
- **No missing-value flags by default.** `control_indicators: true` would add a 0/1 flag for each control that has
  gaps; no configuration, report setting or presentation script sets it. Option, not default.
- **Constant columns are dropped**, including a flag that does not vary within the frame.
- **A control named but absent from the table is skipped silently.**
- **Rows are never dropped for a missing control.** Only the outcome, the probabilities and the moderators are
  complete-case ([10](10-analysis-rules.md#row-filters-inside-a-comparison)).

## The standard set

Engine five plus three columns for the analysed outcome $o$: `own_<o>`, `own_<o>_miss`, `pre_<o>_miss`, where $o$ is
`steps`, `mood` or `sleep`. Applied in the report's effect estimates and in the presentation.
[src: report/ihs_report/build/history.py, add_own_past_mean, own_controls; report/ihs_report/controls.py, columns;
report/config/analysis.yaml, `controls.own_past_mean_min_days`]

**Own past mean.** Sort the cohort's analysis table by participant and study day. For participant $i$ at decision $j$,
with $y^{\mathrm{pre}}_{il}$ the day-before value of outcome $o$ at decision $l$ (`log_steps_pre`, `Mood_pre` or
`sleep_minutes_pre`),

$$\mathrm{own}_{ij} = \frac{1}{n_{ij}} \sum_{l \le j,\ y^{\mathrm{pre}}_{il}\ \mathrm{recorded}} y^{\mathrm{pre}}_{il},
\qquad n_{ij} = \#\{l \le j : y^{\mathrm{pre}}_{il}\ \mathrm{recorded}\},$$

defined once $n_{ij} \ge 3$ (`own_past_mean_min_days` = 3).

- The sum runs up to and including the current decision's day-before value, so the mean covers yesterday and earlier
  windows, never the current window. [src: report/ihs_report/build/history.py, add_own_past_mean (`expanding` over
  the day-before column, current row included)]
- **Where it is not yet defined** it is filled with the mean of `own_<o>` over every row of the cohort table where it
  is defined, and `own_<o>_miss` = 1.
- `pre_<o>_miss` = 1 where the day-before value of the analysed outcome is missing. The engine then median-imputes that
  day-before value, so together they act as the usual missing-indicator adjustment. Only the analysed outcome's
  day-before value gets a flag; the other two day-before controls are imputed without one.
- **Steps:** the zero-step rule runs first, so days below one step are missing in the day-before column, in the own
  mean and in the flag ([07](07-outcome-windows.md#zero-step-days)). [src: report/ihs_report/build/tables.py,
  analysis_table (order of calls)]
- **Built once per cohort on the whole year.** Own means and flags come from the cohort's whole analysis table, so a
  period fit (July to December, January to June) uses own means that may draw on days outside the period, always
  earlier ones. Decisions outside the analysis set are not in the table and contribute nothing.
  [src: report/ihs_report/build/tables.py, analysis_table, period_rows]
- **Origin.** The audit of 2026-11-20 found that the analyses did not adjust for each participant's usual level and
  proposed own past means with missing-history flags; the report adopted them.
  [src: <vault>/Causal Analysis Engine/Audit of Causal Results 2026-11-20.md, section 3, item 2]

## The week set

engine + `wd1` ... `wd6` + `h_<o>_mean7`, `h_<o>_sd7`, `h_<o>_n7`, `h_<o>_lag7`, `h_<o>_last3_minus_prev4`.
Option, not default. [src: report/ihs_report/controls.py, columns; report/ihs_report/build/history.py, add_history,
add_long_history]

History columns are computed on a calendar grid, one cell per participant and day:

- **Day number** `h_dnum`: days since the cohort table's first decision date. **Weekday** `h_wd`: of the decision date,
  Monday = 0. **Participant** `h_pi`. The table must have at most one decision per participant and day, or the build
  stops with an error. [src: report/ihs_report/build/history.py, add_person_day]
- **Values** are the outcome column of earlier days (`log_steps_post` after the zero-step rule, `sleep_minutes_post`,
  `Mood_post`): each earlier day's own post window. When the send time moves, a few hours of an earlier day's window
  can overlap the current day-before window; nothing comes from after the current decision.
  [src: report/ihs_report/build/history.py, comment block above MIN_VALUES]
- `wd1` to `wd6` are 0/1 for Tuesday to Sunday (Monday is the reference). [src: add_long_history]

| Column | Definition | Blank until (`long_history.min_values`) |
|---|---|---|
| `h_<o>_mean7` | Mean over the previous 7 calendar days | 2 values |
| `h_<o>_sd7` | SD over the previous 7 days | 3 values |
| `h_<o>_n7` | Number of values in the previous 7 days | never blank |
| `h_<o>_lag7` | The value 7 days before | blank when that day has none |
| `h_<o>_last3_minus_prev4` | Mean of days 1 to 3 before minus mean of days 4 to 7 before | 2 values in each part |

[src: report/config/analysis.yaml, `long_history.min_values`; report/ihs_report/build/history.py, add_history]

## The long set

week + `h_<o>_lag1` ... `h_<o>_lag6` + `h_<o>_mean28`, `h_<o>_n28`, `h_<o>_own_mean`, `h_<o>_own_sd`, `h_<o>_own_n`,
`h_<o>_own_weekday_mean` + for each of the two other outcomes $o'$: `h_<o'>_mean7`, `h_<o'>_own_mean`, `h_<o'>_sd7` +
`dev_fitbit`, `dev_garmin`, `dev_apple` + `t2`. Option, not default ("long history").
[src: report/ihs_report/controls.py, columns; report/ihs_report/build/history.py, add_history, add_long_history]

| Column | Definition | Blank until |
|---|---|---|
| `h_<o>_lag1` ... `lag6` | The value 1 to 6 calendar days before | that day has no value |
| `h_<o>_mean28`, `n28` | Mean and count over the previous 28 days | mean: 5 values |
| `h_<o>_own_mean`, `own_sd`, `own_n` | Mean, SD and count over every earlier day | mean 3, SD 5 values |
| `h_<o>_own_weekday_mean` | Mean over earlier days on the same weekday | 2 values |
| `dev_fitbit`, `dev_garmin`, `dev_apple` | Main device in the combined view (0/1) | never |
| `t2` | $(t/100)^2$ | never |

`h_<o>_own_mean` differs from the standard set's `own_<o>`: it averages earlier days' outcomes on the calendar grid,
where `own_<o>` averages day-before values over analysed decisions. [derived from history.add_history and
add_own_past_mean]

## The long_others set

long + `h_<o>_others_same_date` and `h_<o>_others_same_date_dev`. Option, not default.
[src: report/ihs_report/controls.py, columns; report/ihs_report/build/history.py, add_history]

- `others_same_date`: the mean of the outcome over the other participants on the same calendar date.
- `others_same_date_dev`: the same date's mean, over other participants, of each one's departure from their own past
  mean (`h_<o>_own_mean`).
- These are same-day outcomes of other people, measured after their own decisions. The code's comment says they are
  "not affected by this participant's message", which assumes no interference between participants.

## How the fuller sets enter the model

The engine and standard sets enter as plain columns. The week, long and long_others sets (and any `extra` block added to
them) enter as standardized principal components, fitted once per cohort and outcome. Applied wherever those sets are
used. [src: report/ihs_report/controls.py, effect_controls, components]

1. **Rows that fit the components:** decisions with the outcome recorded that can take part as far as probability
   release goes. In 2025, decisions in the `withheld` range (2025-09-04 to 2025-09-27) without a released probability
   are left out of the fit. Always the whole year, whatever the period of the effect estimate.
   [src: report/ihs_report/controls.py, released_rows, effect_controls; report/config/analysis.yaml,
   `probability.2025.withheld`; report/ihs_report/moderation.py, fit_cohort docstring]
2. **Missing values:** each column's missing values are replaced by its median over the fitting rows; a 0/1 flag is
   added for each column missing on more than 0.5% of the fitting rows (`long_history.flag_missing_above` = 0.005).
3. **Scaling:** every column is standardized with the fitting rows' mean and SD; columns with SD at most $10^{-9}$ are
   dropped.
4. **Components:** singular value decomposition of the fitting rows; components with a singular value above $10^{-4}$
   times the largest are kept, which removes exact collinearity. Scores are scaled to unit mean square on the fitting
   rows: $\text{scores} = A V_{\text{kept}} \operatorname{diag}(s_{\text{kept}})^{-1} \sqrt{n_{\text{fit}}}$.
5. **Scored rows:** every decision with the outcome recorded. The columns are named `pc_<o>_pc0`, `pc_<o>_pc1`, ... and
   replace the set's raw columns among the controls.

## Moderators as controls

The engine puts a moderator only in the effect part of the model unless it is also listed among the controls. The
report and the presentation list it in both. Applied.
[src: causal/src/ihs_causal/design/contrasts.py, _frame; report/ihs_report/moderation.py, fit_cohort
(`controls=controls + [col], moderators=[col]`)]

- **Report moderator analyses:** the measure is added to the standard set and used as the moderator. Its display
  levels are separate fits on the two subsets with the standard set only.
- **Presentation, figure 1b** (`screen_fit.py`): the half indicator `_ind` is added to the standard set and used as the
  moderator. The two-moderator family adds `_a`, `_b` and their product `_ab`.
  [src: <vault>/Presentation Plots/pipeline/screen_fit.py, fit_cohort]
- **Presentation, figure 2** (`joint_fit.py`): every upper-half indicator `_u_<key>` and every not-recorded indicator
  `_n_<key>` is added to the standard set and used as a moderator. [src: <vault>/Presentation
  Plots/pipeline/joint_fit.py, fit_cohort, splits]
- A moderator that is an exact function of a control (study time over 30 next to the study day `t`) makes the controls
  collinear; the engine handles that since 0.2.2 ([11](11-model.md#the-collinearity-fault-and-its-fix)).

## Outcome-model variables (DR-WCLS)

The engine's default estimator, DR-WCLS, does not use the `controls` list. Its outcome model uses `nuisance`:
`Mood_pre`, `Mood_sd_pre`, `Mood_n_pre`, `log_steps_pre`, `sleep_minutes_pre`, `hr_avg_pre`, `RHR_pre`,
`observed_hours_pre`, `watch_share_pre`, `device_is_fitbit`, `device_is_garmin`, `t`, `Age`, `Sex`, `depr0`,
`PHQtot0`, `GADtot0`, `Neu0_published`, `SLE0`. Missing values are median-filled over the frame with a 0/1 flag for
every variable with gaps; empty and constant columns are dropped. Applied in the engine's standing analyses; not used by
the report or presentation, which run WCLS and set `nuisance` to none.
[src: causal/src/ihs_causal/defaults.yaml, `nuisance`; causal/src/ihs_causal/design/contrasts.py, _frame;
report/ihs_report/context.py, Context.spec] Fitting details: [11](11-model.md#dr-wcls).

`Sex` is recoded 1 to 0 and 2 to 1. [src: causal/src/ihs_causal/data/features.py, baseline_traits]

## The prediction test

How the sets were compared, not a rule used in any estimate. Option (report precision chapter only).
[src: report/ihs_report/controls.py, cv_predict, bound; report/ihs_report/analyses/control_sets.py;
report/config/analysis.yaml, `prediction`]

- **Held-out prediction:** for each cohort and outcome, ridge regression (penalty 10 on standardized columns) of the
  outcome on a set's columns, 5 folds by participant (seed 7); missing values set to the training fold's median, with a
  flag for columns missing on more than 0.5% of rows. The root mean square error on held-out participants is compared
  between sets; the fit always uses the whole year.
- **Ceiling:** what is left after each participant's whole-year mean and the date, then the participant's weekday
  pattern, then yesterday's departure. It uses the future, so it bounds what any control set can reach.
- The reasoning in the code: the outcome variance controls leave unexplained sets the interval width, so a set that
  predicts held-out participants better gives thinner intervals. [src: report/ihs_report/controls.py, module docstring]

## What the presentation uses

Every presentation script gets its controls from the same call:

```python
ctrl, _, _ = control_sets.effect_controls(ctx, cohort, t, "standard", outcome, None)
```

where `control_sets` is `report/ihs_report/controls.py` (imported as `from ihs_report import controls as control_sets`)
and `t` is the report's analysis table with the weather columns added (`weather.weather_table`). For the standard set
with no extra columns the call returns the column list unchanged:

`Mood_pre, log_steps_pre, sleep_minutes_pre, t, PHQtot0, own_<o>, own_<o>_miss, pre_<o>_miss`

The engine then median-imputes them within each frame. Figure 1b and figure 2 add their split indicators
([above](#moderators-as-controls)); the cumulative curves add nothing. Applied.
[src: <vault>/Presentation Plots/pipeline/screen_fit.py, joint_fit.py, cumulative_fit.py, fit_cohort;
report/ihs_report/controls.py, effect_controls; report/ihs_report/build/weather.py, weather_table]

## Where code and documentation disagree

1. **Fill value for the own past mean.** `report/ihs_report/build/history.py` says the own mean is "filled with the
   cohort mean where not yet available". The code fills it with the mean of the defined own-mean values across the
   cohort table, a mean of running means, not the cohort mean of the outcome. Code wins.
2. **Report README on collinearity** says "with the engine's five controls collinearity is unlikely". True for the five;
   the standard set's flags and the moderators added as controls can still be collinear in a subset, which the engine
   handles since 0.2.2. [src: report/README.md, "A fault in the engine"]

## Unverified

- Whether `PHQtot0` has the same item coding in both cohorts' survey files (the engine reads it as given).
- Whether the cohort tables ever hold two decisions for one participant and day (the history build would stop); no
  such error is recorded in the code or notes read here.
