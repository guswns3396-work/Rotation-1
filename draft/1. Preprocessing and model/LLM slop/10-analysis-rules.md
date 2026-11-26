# 10. Analysis rules: from decision rows to analysis frames

**Summary.** A comparison takes the cohort's analysis table (one row per analysed decision, with outcomes, controls and
probabilities) and keeps the decisions that received one of the compared arms, have the outcome, have published
probabilities at or above the floor for both arms, and, where a moderator is in the model, have the moderator. Arms
with fewer than `min_arm_rows` decisions left are dropped; the report and the presentation set this to 50 messages
(lowered from 200 on 2026-11-24), and use a floor of 0.001 in 2024 and 0.01 in 2025. Each cohort is fitted on its own
over a period (whole year, July to December, and in the presentation January to June), and the report and presentation
then pool the two cohorts by inverse variance. Moderators with missing values are handled by complete cases in the
report and in the presentation's one-moderator screen, and by a "not recorded" group in the presentation's joint model.
Every results table the report stores passes an aggregate-only guard; the presentation's scripts do not use it.

## Contents

- [The order of operations](#the-order-of-operations)
- [Cohorts](#cohorts)
- [Periods](#periods)
- [Which decisions enter each comparison](#which-decisions-enter-each-comparison)
- [Row filters inside a comparison](#row-filters-inside-a-comparison)
- [Probability floor](#probability-floor)
- [Positivity: pairwise or joint](#positivity-pairwise-or-joint)
- [Smallest arm](#smallest-arm)
- [Exclusions, all in one list](#exclusions-all-in-one-list)
- [Moderators with missing values](#moderators-with-missing-values)
- [Splitting a moderator into levels](#splitting-a-moderator-into-levels)
- [Pooling the cohorts](#pooling-the-cohorts)
- [Multiplicity](#multiplicity)
- [Settings by pipeline](#settings-by-pipeline)
- [The aggregate-only guard](#the-aggregate-only-guard)
- [Where code and documentation disagree](#where-code-and-documentation-disagree)
- [Unverified](#unverified)

## The order of operations

1. **Analysis table per cohort.** Engine `Workspace.features` under the settings of `Context.spec(cohort)`: combined
   device, default keep rules, probabilities merged; then, in the report, the zero-step rule and own past means.
   [src: report/ihs_report/build/tables.py, analysis_table; report/ihs_report/context.py, Context.spec;
   causal/src/ihs_causal/workspace.py, Workspace.features] Windows and outcomes: [07](07-outcome-windows.md); controls:
   [08](08-controls.md).
2. **Period.** Rows whose decision date lies in the period. [src: report/ihs_report/build/tables.py, period_rows]
3. **Rows with the outcome** (the report's and presentation's `_slim` keeps only these, plus the columns needed).
   [src: report/ihs_report/moderation.py, _slim]
4. **Comparison.** The engine's contrast generator assigns arms and probabilities and applies the row filters below,
   returning one analysis frame per compared arm. [src: causal/src/ihs_causal/design/contrasts.py, _frame, _items]
5. **Fit.** WCLS on each frame ([11](11-model.md)).
6. **Pool** the cohorts; add p and q values.

## Cohorts

- **2024 and 2025 are fitted separately**, always: each frame holds one cohort. Applied.
  [src: report/ihs_report/analyses/pooled_effects.py; report/ihs_report/moderation.py, fit_cohort;
  <vault>/Presentation Plots/pipeline/screen_fit.py, fit_cohort]
- **The engine never pools.** Its app and standing analyses report each cohort separately.
  [src: causal/docs/DESIGN.md, "Questions"]
- **The report and the presentation pool after fitting** ([below](#pooling-the-cohorts)). Drew asked on 2026-11-22 for
  message-against-none and strategy effects pooled across cohorts. This supersedes the earlier framing of 2025 as a
  separate second test (2026-11-16) for these pipelines. Applied. [src: report/config/analysis.yaml, `cohorts`
  ("fitted separately, then pooled"); Drew's request of 2026-11-22, project memory]
- **Cohorts with special inputs.** Circadian and heart-rate-variability measures exist for 2024 only, so those
  moderator families run on 2024 alone. [src: report/config/analysis.yaml, `circadian.cohorts`, `hrv.cohorts`;
  <vault>/Presentation Plots/pipeline/screen_fit.py, `__main__`]
- **Earlier cohorts** (2023, the earlier "events" builds) are separate report chapters, outside these rules.
  [src: report/config/analysis.yaml, `prior_builds`, `cohort_2023`]

## Periods

A period restricts decisions by **decision date** (`decision_date`, first ten characters), inclusive. `{year}` is the
cohort's starting year and `{next_year}` the year after. Controls and history are not cut: day-before values, own past
means and study day come from the whole-year table. [src: report/ihs_report/build/tables.py, period_rows;
causal/src/ihs_causal/data/features.py, in_dates]

| Period | Definition | 2024 cohort | 2025 cohort | Used by | Status |
|---|---|---|---|---|---|
| Whole year | No date limit: the whole analysis set | 2024-07-01 to 2025-06-30 | Decisions flagged `retain_main_reach_retrospective`: study windows from July 1, 2025 to June 30, 2026, less the excluded whole days (July 1, July 14 and November 13, 2025) | Engine default, report, presentation | Applied |
| July-December | `date_to: "{year}-12-31"` | 2024-07-01 to 2024-12-31 | Start of the flagged set to 2025-12-31 | Report, presentation | Applied |
| January-June | `date_from: "{next_year}-01-01"` | 2025-01-01 to 2025-06-30 | 2026-01-01 to 2026-06-30 (wearable data stop near June 20, 2026) | Presentation only | Applied (presentation) |
| July-December, engine configs | `date_from: "<year>-07-01"`, `date_to: "<year>-12-31"` | 2024-07-01 to 2024-12-31 | 2025-07-01 to 2025-12-31 | `causal/config/july_december_2024.yaml`, `july_december_2025.yaml` (uncommitted, not in `pipeline.yaml`) | Option, not default |

[src: report/config/analysis.yaml, `periods`; <vault>/Presentation Plots/pipeline/screen_fit.py, PERIODS;
causal/src/ihs_causal/data/decisions.py, decisions_2024, decisions_2025; causal/config/july_december_2024.yaml,
july_december_2025.yaml; causal/config/pipeline.yaml; 2025 dates and excluded days as recorded in
[06](06-decisions-and-probabilities.md#whole-day-and-row-exclusions-from-source-record-conflicts-2025)]

- **The July-December period has no start date in the report or presentation.** It starts where the analysis set
  starts, which is 2024-07-01 for 2024 by the engine's rule and wherever the flag starts for 2025.
- **Cumulative curves** (presentation figure 1b, top) refit on every decision from the start of a run through each
  cutoff. Run "jul" starts at the cohort's July 1 and ends with June 30; run "jan" starts on January 1. Cutoffs: day 27
  of the run, then every 7 days, skipping a weekly cutoff within 3 days of December 31 or June 30, plus those two dates.
  The July-December curve is the "jul" run cut at December 31, so its last point is the July-December estimate.
  [src: <vault>/Presentation Plots/pipeline/cumulative_fit.py, runs, curves]
- **Report-specific periods for moderators:** weather, circadian and heart-rate-variability moderation use the whole
  year (`weather.period`, `circadian.period`, `hrv.period`). [src: report/config/analysis.yaml]

## Which decisions enter each comparison

The report and presentation pass `domains=[outcome]`, so domain and strategy comparisons use only messages of the
outcome's own domain. The engine's standing analyses also run cross-domain comparisons.
[src: report/ihs_report/analyses/pooled_effects.py and report/ihs_report/moderation.py, fit_cohort (both call
`ctx.spec(..., domains=[outcome])`); <vault>/Presentation Plots/pipeline/screen_fit.py, fit_cohort;
causal/src/ihs_causal/design/contrasts.py, domain_vs_none, strategy_vs_none]

| Name in results | Engine contrast | Message arm | Reference arm | Probabilities (arm; reference) | Status |
|---|---|---|---|---|---|
| `all` | `any_vs_none` | Every delivered send, any domain | Every no-message decision | `p_send`; `p_none` | Applied |
| `any` (own domain) | `domain_vs_none` | Sends whose domain is the outcome's | Every no-message decision | `p_dom_<d>`; `p_none` | Applied |
| `CS`, `BS`, `MI`, `Mfn`, `DST` | `strategy_vs_none` | Own-domain sends with that strategy, own-data and no-data versions together | Every no-message decision | `p_dom_<d>_<s>`; `p_none` | Applied |
| `data` (presentation) | `own_data_vs_nodata`, registered by `screen_fit.py` | Own-domain sends of CS, BS, MI or Mfn that show own data | The same without own data | $\sum_s$ `p_type_<d>_<s>Data`; $\sum_s$ `p_type_<d>_<s>NoData`, over CS, BS, MI, Mfn | Applied (presentation) |

[src: causal/src/ihs_causal/design/contrasts.py, any_vs_none, domain_vs_none, strategy_vs_none;
<vault>/Presentation Plots/pipeline/screen_fit.py, own_data_vs_nodata, CONTRASTS; report/ihs_report/moderation.py,
ENGINE_CONTRASTS, _key]

- **Sends of other domains or strategies are in neither arm.** In `any` and the strategy comparisons they are left out,
  not counted as reference decisions. [src: contrasts.py, _frame (`arm = -1` rows dropped)]
- **2025: domain comparisons run inside that domain's weeks.** The domain was randomized by week. The engine sets
  `p_dom_<d>` and `p_dom_<d>_<s>` to exactly 0 outside domain $d$'s weeks, so no-message decisions there fall below the
  floor and are counted as "no compared message possible". `all` uses every week.
  [src: causal/src/ihs_causal/data/decisions.py, decisions_2025; contrasts.py, _frame]
- **2024: no weekly domain.** `p_dom_<d>` is the send probability times the published send-conditional domain
  probability, so the reference is every no-message decision of the year. [src: decisions.py, decisions_2024]
- **The `data` comparison needs readable statistics and message-type probabilities.** It is restricted to decisions
  where all nine of the outcome domain's statistics were readable by the server (`<o>_n_avail >= 9`, built in the
  presentation's stage 1; see [09](09-moderators.md)). DST has no own-data version and is excluded. Its probabilities
  are message-type probabilities: in 2025 the arm probability inside the domain's weeks; in 2024 from the companion
  file `2024MessageTypeProbabilities.csv.gz`, which `causal/config/paths.example.yaml` lists as staged under review.
  Without that file the 2024 `data` comparison has no rows. [src: <vault>/Presentation Plots/pipeline/screen_fit.py,
  fit_cohort (`readable`); <vault>/Presentation Plots/pipeline/tier_feats.py, feats; causal/src/ihs_causal/data/decisions.py]
- **Engine-only comparisons**, not used by the report or presentation: `strategy_pairwise`, `data_vs_nodata` (all
  domains), `data_within_strategy`, `type_vs_none`, `type_any_vs_none`. [src: contrasts.py, module docstring]
- Probability columns and their 2024 and 2025 construction: [06](06-decisions-and-probabilities.md).

## Row filters inside a comparison

Applied, in this order, for every frame. [src: causal/src/ihs_causal/design/contrasts.py, _frame]

1. **The decision received one of the compared arms.**
2. **Outcome recorded** (finite). Outcomes are never imputed.
3. **Every compared arm's probability published** (finite). Counted as "probability not published".
4. **Every compared arm's probability at least `min_prob`.** Counted as "no compared message possible" when every
   non-reference probability is exactly 0, otherwise "below the floor".
5. **Each named moderator recorded** (finite): complete cases for the moderators.
6. **Arms with fewer than `min_arm_rows` of the remaining decisions are dropped**, never the reference.
7. **Probabilities renormalised** over the arms that remain:
   $p_{i,a} \leftarrow \pi_{i,a} / \sum_{b} \pi_{i,b}$ ([11](11-model.md#probabilities-in-the-model)).
8. **Controls median-imputed and moderators centred** on the frame's rows ([08](08-controls.md#missing-values-in-the-engine),
   [11](11-model.md#moderators-and-centring)).

The engine records per frame: candidate rows, rows without the outcome, rows with an unpublished probability, rows with
no compared message possible, rows below the floor, arms dropped as small, rows analysed. The report keeps the counts of
unpublished and below-floor rows with each estimate. [src: contrasts.py, _frame (`info`); report/ihs_report/estimate.py,
contrast_rows]

## Probability floor

| Cohort | Engine default | Engine `july_december_*.yaml` | Report | Presentation |
|---|---|---|---|---|
| 2024 | 0.001 | 0.01 | 0.001 | 0.001 |
| 2025 | 0.001 | 0.01 | 0.01 | 0.01 |

The presentation reads the floor through `ctx.spec`, so it always matches the report. Applied (report and
presentation). A floor of 0.05 is tried in the report's "other levers" check only (Option).
[src: causal/src/ihs_causal/defaults.yaml, `min_prob`; causal/config/july_december_2024.yaml;
report/config/analysis.yaml, `probability`, `levers.floor`; report/ihs_report/context.py, Context.spec]

- The floor checks both compared arms, the reference included.
- **2025 probabilities are the released (marginal) ones**, over the agent-selection step (`prob_scope: marginal`).
  Drew, 2026-11-22: these are the right ones. Applied. [src: report/config/analysis.yaml, `probability.2025.scope`;
  causal/src/ihs_causal/data/decisions.py, decisions_2025]
- **2025-09-04 to 2025-09-27:** the fitted-agent decisions have no released probability and take part in no comparison
  (filter 3). Scheduled random-policy decisions in that range keep their probabilities.
  [src: report/config/analysis.yaml, `probability.2025.withheld`; causal/docs/DESIGN.md, "Rows left out";
  <vault>/Causal Analysis Engine/ihs-causal Design.md, "September 2025 probabilities withheld"]

## Positivity: pairwise or joint

`positivity: pairwise` (default since Drew's choice of 2026-11-17): a comparison with more than two arms runs one frame
per arm against the reference, and the floor checks only those two arms. `joint` (as in Jack's notebook) puts every arm
in one frame and checks all of them, so one rare arm removes the decision for all. Two-arm comparisons are the same
either way. The report and presentation do not change it, so every strategy comparison there is a set of pairwise
frames. Pairwise: Applied; joint: Option, not default.
[src: causal/src/ihs_causal/defaults.yaml, `positivity`; causal/src/ihs_causal/design/contrasts.py, module docstring,
_items]

## Smallest arm

| Pipeline | `min_arm_rows` | Status | Source |
|---|---|---|---|
| Engine default and standing analyses | 200 | Applied in the engine | `causal/src/ihs_causal/defaults.yaml` |
| Report | 50 (was 200; lowered 2026-11-24) | Applied; 200 Superseded | `report/config/analysis.yaml`, `min_arm_rows` |
| Presentation | 50 (`MIN_ARM`, merged over `ctx.spec`) | Applied | `<vault>/Presentation Plots/pipeline/screen_fit.py`, MIN_ARM; joint_fit.py and cumulative_fit.py reuse it |
| Report fake-data mode | 50 | Applied (tests only) | `report/config/analysis.yaml`, `fake.overrides` |

- **What is counted:** decisions in the non-reference arm after filters 1 to 5, so in a moderator fit the arm needs
  50 messages with the moderator recorded. The reference arm is never dropped. Under pairwise positivity a dropped arm
  leaves its frame with the reference arm only, and no estimate is made. [src: contrasts.py, _frame; report/ihs_report/estimate.py,
  contrast_rows (skips frames with no arms)]
- **Report display levels** (the two sides of a moderator) are separate fits, so each side needs 50 messages.
  [src: report/ihs_report/moderation.py, fit_cohort and module docstring]
- **Presentation halves and groups** add their own minimum: each half of a split needs at least 30 messages and 30
  reference decisions (`MIN_HALF`), and each of the four groups of the two-moderator model 30 of each (`MIN_GROUP`).
  [src: <vault>/Presentation Plots/pipeline/screen_fit.py, MIN_HALF, halves, MIN_GROUP, quarters]

## Exclusions, all in one list

| Reason | Where | Status |
|---|---|---|
| Outside the analysis set: 2024 outside 2024-07-01 to 2025-06-30 or without `time_source`; 2025 not flagged (undelivered sends, unreachable no-sends) | `causal/src/ihs_causal/data/decisions.py`; [06](06-decisions-and-probabilities.md) | Applied |
| Whole 2025 days July 1, July 14 and November 13 (Drew: "No November 13", 2026-11-16), and some October 27 no-sends | Through the timing file's flag ([06](06-decisions-and-probabilities.md#whole-day-and-row-exclusions-from-source-record-conflicts-2025)); not visible in engine code | Applied |
| No anchor | `data/features.py`, `window_stats` | Applied |
| Participant absent from the hourly file (no outcomes) | `data/windows.py`, `WindowAggregator.bounds` | Applied |
| Outcome missing: keep rule, window length, zero-step rule | [07](07-outcome-windows.md) | Applied |
| In neither compared arm | `contrasts.py`, `_frame` | Applied |
| Probability not published (2025 fitted decisions, September 4 to 27) | `contrasts.py`, `_frame` | Applied |
| No compared message possible (2025, another domain's week) | `contrasts.py`, `_frame` | Applied |
| A compared probability below the floor | `contrasts.py`, `_frame` | Applied |
| Moderator not recorded, when the moderator is in the model (except presentation figure 2) | `contrasts.py`, `_frame` | Applied |
| Arm too small | `contrasts.py`, `_frame` | Applied |
| `data` comparison: fewer than nine statistics readable | `screen_fit.py`, `fit_cohort` | Applied (presentation) |
| Half or group below 30 messages or 30 reference decisions | `screen_fit.py`, `halves`, `quarters` | Applied (presentation) |
| 2025 withheld decisions without a released probability, from fitting the components of the fuller control sets | `report/ihs_report/controls.py`, `released_rows` | Applied (report fuller sets) |

## Moderators with missing values

| Where | How the moderator enters | A decision without the moderator | Status |
|---|---|---|---|
| Engine, `moderators` setting (WCLS, DR-WCLS) | Effect part only, centred; a control only if also listed | Dropped from that fit (complete cases) | Applied when set; the standing primary analyses set none |
| Engine, question 6 (`drwcls_hetero`) | Pseudo-outcome regressed on the standardized moderator alone | Dropped for that moderator only; a moderator recorded at fewer than 100 decisions, or constant, is not estimated | Applied (engine) |
| Report, every moderator analysis (`moderation.fit_cohort`) | Control and moderator, standard controls | Dropped from the moderation fit; the overall effect is fitted on every decision with the outcome; the moderated model's effect term refers to decisions with the measure | Applied |
| Presentation figure 1b (`screen_fit.py`) | Half indicator as control and moderator | Indicator missing, so dropped from that fit (complete cases) | Applied |
| Presentation figure 2 (`joint_fit.py`) | Each upper-half indicator (0 where not recorded) and, if any are missing, a not-recorded indicator, all as controls and moderators | Kept: it sits in that moderator's own "not recorded" group, so every model uses every analysed decision | Applied |
| Presentation cumulative curves | No moderator | Not applicable | Applied |

[src: causal/src/ihs_causal/design/contrasts.py, _frame; causal/src/ihs_causal/estimators/hetero.py, drwcls_hetero;
report/ihs_report/moderation.py, fit_cohort and module docstring; <vault>/Presentation Plots/pipeline/screen_fit.py,
indicator, fit_cohort; <vault>/Presentation Plots/pipeline/joint_fit.py, splits, module docstring]

Consequence of complete cases [derived]: in the report and figure 1b, a moderator recorded for part of a cohort gives a
moderation estimate for that part only, which can differ from the overall effect for reasons unrelated to the moderator.
The report states this for its `est` column. [src: report/ihs_report/moderation.py, module docstring]

How each moderator is built, and its coverage: [09](09-moderators.md).

## Splitting a moderator into levels

| Pipeline | Continuous moderator | Yes/no | Other kinds | Status |
|---|---|---|---|---|
| Report | Test: slope per unit. Display levels: at or below vs above the median, taken over the comparison's decisions with the outcome and the measure recorded, before the probability floor, per compared arm; or a fixed cut named for the measure | 0 vs 1 (cut 0.5) | — | Applied |
| Presentation figure 1b and 2 | Upper half = above the median of the moderator over every decision with the outcome in that cohort, period and outcome; the same cut for every comparison. If the upper share falls outside 20% to 80% (ties at the median), the upper half is "at or above" | above 0.5 | `pos`: above 0; `nine`: at least 9; tiers: the named tier against the other two | Applied |

[src: report/ihs_report/moderation.py, fit_cohort, _medians; <vault>/Presentation Plots/pipeline/screen_fit.py,
indicator; <vault>/Presentation Plots/pipeline/joint_fit.py, splits]

In the presentation the two halves and their difference all come from one model; the report fits its display levels
separately. Details of both: [11](11-model.md#linear-combinations-from-influence-values).

## Pooling the cohorts

Fixed-effect inverse-variance average of the two cohort estimates ([11](11-model.md#pooling-across-cohorts) has the
formulas). Applied in the report and the presentation; never in the engine.

| Pipeline | When a pooled row exists | Source |
|---|---|---|
| Report, message and strategy effects | Only when the comparison is estimable in every cohort | `report/ihs_report/analyses/pooled_effects.py` |
| Report, moderator analyses | Only when every cohort has that comparison and moderator; a pooled level only when every cohort has it | `report/ihs_report/moderation.py`, pooled_rows |
| Presentation figure 1b, figure 2 | Pools the cohorts with a finite, positive standard error; **with only one, the "pooled" row is that cohort's estimate** | `<vault>/Presentation Plots/pipeline/screen_fit.py`, combine; joint_fit.py, finish |
| Presentation figure 2, "all together" test | Both cohorts' coefficient vectors on their shared terms, combined by inverse-variance matrices; with one cohort, that cohort's test | `joint_fit.py`, finish |
| Presentation cumulative curves | At each cutoff where every cohort with a curve has that cutoff | `cumulative_fit.py`, curves |

The 2024-only moderator families (circadian, heart rate variability) therefore appear as "pooled" rows in the
presentation's tables carrying the 2024 estimate. [derived from screen_fit.combine]

## Multiplicity

- **Report:** Benjamini-Hochberg q-values over the moderation tests of the main sample (the pooled rows, or the single
  cohort), within an analysis; for message and strategy effects, over the pooled p-values within a period. Applied.
  [src: report/ihs_report/moderation.py, finish; report/ihs_report/analyses/pooled_effects.py;
  report/ihs_report/pooling.py, benjamini_hochberg]
- **Presentation:** the pipeline writes p-values without adjustment (figures 1b and 2), a Wald test of all eleven
  moderators together (figure 2), and a simultaneous band across the cutoffs of each cumulative curve. Whether the
  plotting code adjusts further was not checked. [src: <vault>/Presentation Plots/pipeline/screen_fit.py, combine;
  joint_fit.py, finish; cumulative_fit.py, crit]
- **Engine app:** simultaneous 95% intervals per family by a multiplier bootstrap, a family being the effect estimates
  that share configuration, cohort, device, Apple source, question, estimator, window, keep rules, probability settings
  (scope, floor, positivity), moderators, sleep measure and dates; Benjamini-Hochberg q-values across moderators within each question-6 arm. [src:
  causal/src/ihs_causal/viewer/build.py, FAMILY_COLS; causal/src/ihs_causal/results.py, add_simultaneous, add_bh]

## Settings by pipeline

| Setting | Engine defaults | Engine `july_december_*.yaml` | Report (`ctx.spec`) | Presentation |
|---|---|---|---|---|
| Estimator | `drwcls` | `wcls` | `wcls` | `wcls` (called directly) |
| Device | `combined` | `combined` | `combined` | `combined` (report table) |
| Apple source | `watch_then_phone` | `watch_only` | `watch_then_phone` | `watch_then_phone` |
| 2025 probabilities | `marginal` | `marginal` | `marginal` | `marginal` |
| Floor 2024 / 2025 | 0.001 / 0.001 | 0.01 / 0.01 | 0.001 / 0.01 | 0.001 / 0.01 |
| Smallest arm | 200 | 200 | 50 | 50 |
| Positivity | `pairwise` | `pairwise` | `pairwise` | `pairwise` |
| Controls | engine five | engine five | standard | standard |
| Zero-step rule | no | no | yes | yes |
| Periods | whole year | July-December | whole year; July-December | July-December; whole year; January-June |

[src: causal/src/ihs_causal/defaults.yaml; causal/config/july_december_2024.yaml, july_december_2025.yaml;
report/config/analysis.yaml; report/ihs_report/context.py, Context.spec; <vault>/Presentation Plots/pipeline/screen_fit.py]

## The aggregate-only guard

`report/ihs_report/guard.py`, `check_aggregate`, runs on every results table before the report stores it. Applied
(report). [src: report/ihs_report/guard.py; report/ihs_report/store.py (calls check_aggregate before writing)] It
refuses a table that has any of the following.

- **A column that identifies a person, decision or message instance:** names `participant_id`,
  `participantidentifier`, `pid`, `pid_code`, `decision_id`, `cluster`, `device_name`, `zip`, `zip_code`, `email`,
  `name`, or any name containing `participant` or `identifier` (case-insensitive). The report therefore names its
  participant counts `n_people`.
- **More than 2,000 rows**, which "looks like row-level data".
- **A count below the minimum cell size:** any column whose name starts with `n_` with a value above 0 and below 10.

The guard is "deliberately blunt": a table that needs an exception should be redesigned. [src: guard.py, docstring]

Not covered by the guard:

- **The presentation pipeline** writes its source tables with only an assertion that none of `participant_id`, `pid`,
  `pid_code` is a column. Its count columns (`n_lo`, `n_hi`, `people`, `n`, `sends`, `rows`) are not checked against a
  minimum cell size. Its stage-1 moderator cache is participant-level and is written to the audit area outside the
  repository. [src: <vault>/Presentation Plots/pipeline/screen_fit.py, combine; joint_fit.py, finish;
  cumulative_fit.py, `__main__`; screen_mods.py, module docstring]
- **The engine** keeps person-level effects only in its `work/` folder and tests that its snapshot holds no participant
  identifiers. [src: causal/docs/DESIGN.md, "Who responds" and "Validation"]

## Where code and documentation disagree

Code wins in every case below.

1. **Smallest arm in the report README.** `report/README.md` ("What is in the report") says "Weather and other levels
   need 200 sends (`min_arm_rows`), so 29 snow levels the audit showed are blank". `report/config/analysis.yaml` has
   been 50 since 2026-11-24.
2. **Pooling.** `causal/docs/DESIGN.md` says the cohorts "are analysed separately and never pooled". True of the
   engine; the report and presentation pool.
3. **Engine docs on the floor and arm size** (`causal/README.md`, `causal/docs/DESIGN.md`: 0.001 and 200) describe the
   engine defaults, not the report's or presentation's settings.
4. **Presentation median.** `screen_fit.py` and `joint_fit.py` say continuous moderators are split "at their median
   among the analysed decisions of that cohort, period and outcome". The code takes the median over every decision with
   the outcome in that cohort and period, before any comparison's filters, and uses that cut for every comparison.

## Unverified

- The 2025 flagged set's dates and excluded days are taken from [06](06-decisions-and-probabilities.md), not checked
  against the timing file here.
- Whether the 2024 message-type probability file used for the presentation's 2024 `data` comparison is the staged
  candidate named in `causal/config/paths.example.yaml`: the engine's local `config/paths.yaml`, which the report and
  the presentation read because the report has no paths file of its own, names that staged candidate's path; the
  file's fingerprint was not checked.
- Whether the presentation's plotting code applies any multiplicity adjustment.
- Whether the source tables of presentation figure 1 (`usual_set_temperature.csv`, `tier_effects.csv`) match a run of
  the current scripts. The scripts are not in the pipeline folder but in `<scratch>` (`usual_set_temperature.py`,
  `tier_effects.py`); as read for this review they use the report's code, standard controls, released probabilities
  and 50 messages per arm.
