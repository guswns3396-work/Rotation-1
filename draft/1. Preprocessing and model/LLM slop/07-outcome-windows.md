# 07. Outcome windows: from the hourly file to one outcome per decision

**Summary.** Each analysed decision gets one value of each outcome, made by summing or averaging the hourly file over a
window that starts at the hour of the logged send (for a no-message decision, the hour a message would have gone out)
and ends at the next day's decision. Steps are log(1 + total steps) on days when the device was observed for at least
10 hours and has at least one step record, and the report and the presentation also treat a total below one step as
missing. Sleep is the minutes asleep recorded in that window, which holds the night after the message, kept when a
sleep record exists (a short night only if the device was worn overnight); mood is the mean of the survey responses
completed in the window. The same rules applied to the previous day's window give the "day before" values used as
controls ([08](08-controls.md)). Everything here describes the engine's working tree at version 0.2.2, outcome rules
`window-stats-v5`, unless a rule says otherwise.

## Contents

- [Scope and sources](#scope-and-sources)
- [The steps from file to outcome](#the-steps-from-file-to-outcome)
- [Anchor](#anchor)
- [Which decisions get a window](#which-decisions-get-a-window)
- [The daily grid: post and pre windows](#the-daily-grid-post-and-pre-windows)
- [Window length rule](#window-length-rule)
- [Instruments and device view](#instruments-and-device-view)
- [Observed hours (wear)](#observed-hours-wear)
- [Steps](#steps)
- [Zero-step days](#zero-step-days)
- [Sleep that night: the clock window](#sleep-that-night-the-clock-window)
- [Sleep from complete episodes (option)](#sleep-from-complete-episodes-option)
- [Mood](#mood)
- [The day-before values](#the-day-before-values)
- [Other window statistics](#other-window-statistics)
- [Outcome transforms not used by default](#outcome-transforms-not-used-by-default)
- [Rule versions and caching](#rule-versions-and-caching)
- [2024 and 2025 side by side](#2024-and-2025-side-by-side)
- [Where code and documentation disagree](#where-code-and-documentation-disagree)
- [Unverified](#unverified)

## Scope and sources

- **Engine.** `causal/`, Python package `ihs_causal`, version 0.2.2 (`causal/pyproject.toml`,
  `causal/src/ihs_causal/__init__.py`). The version bump and several files are uncommitted, among them `data/features.py`,
  `data/hourly.py`, `workspace.py`, `estimators/wls.py`, `estimators/core.py`, `runner.py`, `defaults.yaml`, and the
  new `data/sleep.py`. This note describes the working tree, which is what produced the current results. The engine is
  cited as `causal/...`; it is moving to the repository root.
- **Report.** `report/` builds its analysis table by calling the engine and then adds the zero-step rule and history
  columns (`report/ihs_report/build/tables.py`, `analysis_table`).
- **Presentation.** `<vault>/Presentation Plots/pipeline/` reads the report's analysis table, so it inherits every
  outcome rule of the report.
- **Upstream notes.** Hourly columns and how sleep minutes are placed in hours: [02](02-hourly-files.md) (sleep from
  Fitbit: [02, Fitbit sleep](02-hourly-files.md#fitbit-sleep)). Local and UTC clocks: [03](03-clocks-and-time-zones.md).
  Mood placement at survey completion time: [05](05-mood-timing.md). Decision tables, delivery, reachability and
  probabilities: [06](06-decisions-and-probabilities.md).

## The steps from file to outcome

| Step | What happens | Code |
|---|---|---|
| 1 | The hourly file becomes one row per participant and UTC hour (repeated hours merged) | `causal/src/ihs_causal/data/hourly.py`, `read_hourly` |
| 2 | One decision table per cohort: anchor hour, analysis flag, arm, probabilities | `causal/src/ihs_causal/data/decisions.py`, `decisions_2024`, `decisions_2025` |
| 3 | Analysis-set decisions with an anchor are laid on a daily grid; post and pre windows | `causal/src/ihs_causal/data/features.py`, `window_stats`; `data/windows.py`, `next_decision_windows` |
| 4 | Layer 1: window statistics per instrument (sums, counts, means), cached on disk | `data/features.py`, `window_stats` |
| 5 | Layer 2: keep rules and device choice give outcomes and day-before values | `data/features.py`, `apply_rules` |
| 6 | Probabilities merged; optional date range | `causal/src/ihs_causal/workspace.py`, `Workspace.features`; `data/features.py`, `in_dates` |
| 7 | Report only: zero-step rule, then own past means | `report/ihs_report/build/tables.py`, `analysis_table`; `report/ihs_report/build/history.py` |

## Anchor

**Rule: a window starts at the anchor hour, the anchor timestamp floored to the whole UTC hour.** Applied.
[src: causal/src/ihs_causal/data/hourly.py, hours_from_timestamps; causal/src/ihs_causal/data/decisions.py, _hour]

- **2025: the logged send.** The anchor is `window_anchor_utc` from `2025DecisionTiming.csv`: the logged send attempt
  for a message; for a no-message decision, the day's observed send hour, flagged as imputed in the timing file. Applied.
  [src: causal/src/ihs_causal/data/decisions.py, decisions_2025 and module docstring; the no-message rule as recorded in
  [06, Facts other notes should carry](06-decisions-and-probabilities.md#facts-other-notes-should-carry)]
- **2024: `hour_utc` from `2024BehaviorAgentProbabilities.csv`.** The engine uses that column as the anchor; the module
  docstring describes every anchor as "the logged send or, for a no-send, its assigned time". In the 2024 file
  `hour_utc` floors `recorded_time_utc`: the attempt time for a message (`time_source` = attempt) and, for a
  no-message day, an hour imputed from neighbouring attempts (`time_source` = imputed, some flagged `time_uncertain`).
  2024 no-message days are inferred from the absence of an attempt, not logged randomizations. Applied.
  [src: causal/src/ihs_causal/data/decisions.py, decisions_2024; [06, How the 2024 table was built](06-decisions-and-probabilities.md#how-the-2024-table-was-built-november-16-2026)]
- **2024 is the template.** Drew decided on 2026-11-16 that 2025 windows start at the logged send, as in 2024: "In this
  respect the two datasets should be the same." [src: Drew's decision of 2026-11-16, project memory]
- **Superseded: anchoring 2025 at the decision file's `hour_utc`.** In the 2025 decision file that column is a
  midnight-UTC date label, many hours before the message, so windows anchored there were mostly before the message.
  The engine never reads it for 2025. [src: Drew's decision of 2026-11-16, project memory;
  causal/src/ihs_causal/data/decisions.py, decisions_2025 reads `window_anchor_utc` only]
- **What flooring does.** The hour that contains the send belongs to the post window, including the minutes of that
  hour before the send. The pre window ends at the start of that hour. A step, sleep minute or mood response logged in
  the send hour but before the send therefore counts as after the message. [src: causal/src/ihs_causal/data/windows.py,
  next_decision_windows (post_start = anchor hour, pre_end = anchor hour); hourly resolution of the hourly table]
- **No anchor, no window.** A decision whose anchor is missing (anchor hour -1) is dropped before windows are built.
  [src: causal/src/ihs_causal/data/features.py, window_stats, filter `anchor_hour >= 0`]
- The complete-episode sleep option uses the exact 2025 anchor (to the minute) where it lies within one hour of the
  floored anchor ([below](#sleep-from-complete-episodes-option)).

## Which decisions get a window

Only decisions in the analysis set are placed on the grid. All other rows are removed before any window is built.
[src: causal/src/ihs_causal/data/features.py, window_stats, filter `in_analysis`]

| Cohort | Analysis set (`in_analysis`) | Status | Source |
|---|---|---|---|
| 2024 | `decision_date` from 2024-07-01 to 2025-06-30 inclusive, and `time_source` not blank. The published table holds delivered sends and reachable no-sends (plus earlier baseline rows, which the date rule drops). | Applied | `causal/src/ihs_causal/data/decisions.py`, `decisions_2024` |
| 2025 | `retain_main_reach_retrospective` is `1` or `true` in the timing file. Sends are kept if delivered, no-sends if the participant was reachable. | Applied | `causal/src/ihs_causal/data/decisions.py`, `decisions_2025`; [06](06-decisions-and-probabilities.md) |

- **Undelivered sends are excluded, not recoded as no-sends.** Drew, 2026-11-16, for 2025 to match 2024. The flag
  carries it out. Applied. [src: Drew's decision of 2026-11-16, project memory; decisions.py module docstring]
- **Unreachable no-send days are dropped in 2025 as in 2024.** Drew, 2026-11-16 ("Yes, same as 2024"), kept labelled
  as an analysis assumption. Applied through the flag. [src: Drew's decision of 2026-11-16, project memory]
- **Availability.** The engine has no separate availability indicator. Being in the analysis set is what makes a
  decision available. A comparison can narrow this further: in 2025 a domain's comparisons use only that domain's
  weeks, through a zero probability elsewhere ([10](10-analysis-rules.md#which-decisions-enter-each-comparison)).
  [src: causal/src/ihs_causal/data/decisions.py; causal/src/ihs_causal/design/contrasts.py, _frame]
- **Participants absent from the hourly file** get the participant code -1. The window aggregator returns nothing for
  that code, so every outcome is missing and these participants never enter a fit.
  [src: causal/src/ihs_causal/data/windows.py, WindowAggregator.bounds (`pid_code >= 0`);
  causal/src/ihs_causal/data/features.py, window_stats]
- **Excluded decisions leave a hole in the grid.** Because they are removed first, the days they occupied are treated
  as skipped days (next section).
- **2025: the engine builds its own windows, not the published grid's.** The timing file also carries window-level
  flags (`main_window_reach_retrospective`, `main_with_history_reach_retrospective`) from a grid built over every
  decision, in which failed sends and conflicting days still delimit their own days. The engine reads only the
  decision-level flag and lays its grid over the flagged decisions alone, with its own 20 to 28 hour span rule. So a
  decision followed by an undelivered send gets a 24-hour window in the engine, where the published grid ends it at the
  undelivered send's anchor; and the engine keeps flagged decisions whose published window flag is false if its own
  span rule passes. Whether the two sets of windows agree decision by decision was not checked. Applied (engine rule).
  [src: causal/src/ihs_causal/data/decisions.py, decisions_2025 (reads `retain_main_reach_retrospective` only);
  causal/src/ihs_causal/data/features.py, window_stats; [06, Reach restriction and main analysis flags](06-decisions-and-probabilities.md#reach-restriction-and-main-analysis-flags-2025)]
- **Whole days out of the 2025 set** (July 1, July 14 and November 13, 2025, and some October 27 no-sends) are
  excluded through the flag, so they too appear as skipped days. [src: [06](06-decisions-and-probabilities.md#whole-day-and-row-exclusions-from-source-record-conflicts-2025)]
- **End of the 2025 year.** Hourly wearable data stop near June 20, 2026 while decisions run to June 30, 2026, so the
  last days have no wearable outcomes. [src: [06, June 20-30, 2026 tail extension](06-decisions-and-probabilities.md#june-20-30-2026-tail-extension);
  [02](02-hourly-files.md)]

## The daily grid: post and pre windows

Window definition `next_decision` (the default, called "Jack's grid" in the code). Applied.
[src: causal/src/ihs_causal/data/windows.py, next_decision_windows; causal/src/ihs_causal/defaults.yaml, `window.name`]

For one participant, sort the analysed decisions by anchor hour $h_1 < h_2 < \dots$ (hours since 1970, UTC). Then

$$s_1 = 0,\qquad s_j = \max\big(1,\ \mathrm{rint}\big((h_j - h_{j-1})/24\big)\big)\ \ (j \ge 2),\qquad t_j = \sum_{l \le j} s_l .$$

`rint` rounds half to even, so any gap of up to 35 hours counts as one grid day and a gap of 36 hours as two.

| Quantity | Definition |
|---|---|
| Study day `t` | $t_j$: grid days since the participant's first analysed decision (0 for that decision). Skipped and excluded days count. |
| Post window | $[h_j,\ e_j)$ with $e_j = h_{j+1}$ when the next decision is one grid day later ($s_{j+1} = 1$), else $e_j = h_j + 24$. The last decision gets $h_j + 24$. |
| Pre window | None for the first decision. Otherwise $[h_{j-1} + 24(s_j - 1),\ h_j)$: yesterday's window when decisions are consecutive, else the interpolated grid day before $h_j$. |

- **Consecutive days share a boundary.** When $s_j = 1$ the pre window of decision $j$ is exactly the post window of
  decision $j-1$, so the day-before value is yesterday's outcome.
- **Worked example from the engine's test** (hours): anchors 100, 124, 172, 197 give post windows [100, 124),
  [124, 148), [172, 197), [197, 221) and pre windows none, [100, 124), [148, 172), [172, 197); study days 0, 1, 3, 4.
  [src: causal/tests/test_windows.py, test_next_decision_grid_matches_jacks_rules]
- **Windows are half-open in whole UTC hours.** Each hourly row stands for one hour ([02](02-hourly-files.md)).
- **Alternative `fixed` windows** (post $[h + a, h + b)$, pre $[h - L, h)$, study day = the decision's position in the
  participant's sequence): Option, not default. [src: causal/src/ihs_causal/data/windows.py, fixed_windows]

## Window length rule

**A window counts only when its span lies in [20, 28] hours** (`window.span_min` = 20, `window.span_max` = 28), checked
separately for the post window (outcomes) and the pre window (day-before values), for steps, sleep and mood alike.
Applied. [src: causal/src/ihs_causal/defaults.yaml, `window`; causal/src/ihs_causal/data/features.py, apply_rules
(`span_ok`)]

- A gap that rounds to one grid day but is shorter than 20 hours or longer than 28 hours leaves that decision's
  outcomes missing. [derived from the two rules above]
- Totals are not rescaled to 24 hours: a 27-hour window sums 27 hours of steps or sleep. [src: data/features.py,
  window_stats (plain sums)]

## Instruments and device view

| Instrument | Steps, heart rate, resting heart rate | Sleep minutes | Source |
|---|---|---|---|
| `fitbit` | `Fitbit_*` columns | `Fitbit_sleep_minutes` | `causal/src/ihs_causal/data/features.py`, `instrument_hours` |
| `garmin` | `Garmin_*` columns | `Garmin_sleep_minutes` | same |
| `apple` | Apple Watch value for each hour, else the iPhone's | Watch, else iPhone, else Apple sleep of unknown source | same |
| `apple_watch` | Apple Watch only | Apple Watch only | same |

**Device view** (`device`):

- **Combined** (`combined`). Applied in the report and the presentation (`engine.device: combined`). Each participant
  contributes one main instrument for all their decisions: whichever of Fitbit, Garmin and Apple has the most observed
  hours summed over the participant's post windows. Ties go to the first in that order. A participant with no observed
  hour on any instrument has no wearable outcomes but keeps mood. Mood is kept for everyone, including people without a
  wearable. [src: causal/src/ihs_causal/data/features.py, apply_rules; report/config/analysis.yaml, `engine.device`]
- **Single device** (`fitbit`, `garmin`, `apple`): the instrument for everyone with at least one observed post hour on
  it. Mood is restricted to the same people, so a view describes one group. Applied in the engine's standing analyses
  (`causal/config/primary_*.yaml`); Option, not default, for the report and presentation.
  [src: causal/src/ihs_causal/data/features.py, apply_rules; causal/config/primary_2024.yaml, primary_2025.yaml]
- **Apple source** (`apple_source`): `watch_then_phone` (default; Applied in the report and presentation, which do not
  set it) or `watch_only` (Option; used by the engine's `primary_*_apple_watch.yaml` and by the uncommitted
  `july_december_*.yaml`). In the combined view this setting also decides which Apple instrument competes for "main".
  [src: causal/src/ihs_causal/defaults.yaml; causal/config/primary_2024_apple_watch.yaml;
  causal/config/july_december_2024.yaml]

## Observed hours (wear)

- **An hour is observed for an instrument when it has a heart-rate value or a positive step count.** A zero step cell is
  not evidence of wear, because Garmin writes zeros in every hour. For a participant with only an iPhone the only
  evidence is steps. Applied. [src: causal/src/ihs_causal/data/features.py, instrument_hours]
- For the `apple` instrument the heart rate and steps are the watch's where present, else the phone's, so either
  device's signal makes the hour observed. [src: same]
- **Overnight hours** are local hours 22:00 to 06:59 (`keep.night_start_hour` = 22, `keep.night_end_hour` = 7), nine
  hours in all. An hour without a local time never counts as overnight. [src: causal/src/ihs_causal/data/features.py,
  instrument_hours and apply_rules (`night_len`); causal/src/ihs_causal/defaults.yaml]
- Per window the engine stores the observed hours and the observed overnight hours. [src: data/features.py,
  window_stats]

## Steps

**Outcome.** $Y = \log(1 + S)$, where $S$ is the sum of every recorded step cell of the instrument in the post window,
zero cells included. Column `log_steps_post`. Applied.
[src: causal/src/ihs_causal/data/features.py, window_stats (`steps` array, rule `sum`) and apply_rules]

**Kept when** all of the following hold. Applied (engine working tree, `window-stats-v5`).
[src: causal/src/ihs_causal/data/features.py, module docstring and apply_rules]

1. The post window's span is 20 to 28 hours.
2. The instrument was observed in at least `keep.steps_min_observed_hours` = 10 hours of the window.
3. The window holds at least one step record. A recorded zero counts as a record; heart rate alone does not supply a
   step total. With no record the sum is missing, not zero.

Notes:

- **Repeated hours in the hourly file** are merged by summing steps with at least one value required, so an hour whose
  rows are all blank stays blank (hourly cache version 2). [src: causal/src/ihs_causal/data/hourly.py, read_hourly;
  causal/src/ihs_causal/workspace.py, VERSIONS] Details in [02](02-hourly-files.md).
- **Scale.** The report reads an effect $b$ on this scale as a change of $100(\exp(b) - 1)$ percent
  [src: report/ihs_report/analyses/pooled_effects.py, module docstring]. Because the outcome is $\log(1 + S)$, not
  $\log S$, that reading is approximate for small totals. [derived]
- **The report and the presentation apply one more rule** to the same column: [Zero-step days](#zero-step-days).

## Zero-step days

"Zero-step days" are kept step windows whose total is zero. Four rules have applied or been proposed:

| Rule | Status | Source |
|---|---|---|
| A blank step cell in an observed hour counts as zero, and the window total is never missing once 10 hours are observed. A day with heart rate but no step records became a zero-step day. | Superseded (committed code, outcome rules up to `window-stats-v4`) | `git diff` of `causal/src/ihs_causal/data/features.py` against HEAD (`instrument_hours`, `window_stats`) |
| A window needs at least one step record; blank cells contribute nothing. A total of recorded zeros is still kept as zero. | Applied (engine working tree, `window-stats-v5`; dated 2026-11-20 in the audit memory, unverified against git, which has no commit for it) | `causal/src/ihs_causal/data/features.py`, `window_stats`, `apply_rules`; `causal/tests/test_rules.py` |
| A day whose step total is below one step is treated as not measured, for the outcome (`log_steps_post`) and for the day before (`log_steps_pre`). | Applied in the report and the presentation (`steps.zero_days_missing: true`, decided 2026-11-20). Not applied in runs of the engine's own app. | `report/ihs_report/build/history.py`, `zero_step_days_missing`; `report/config/analysis.yaml`; `report/ihs_report/build/tables.py`, `analysis_table` |
| Also treat as missing a day inside a run of days with device hours and no step records. | Proposed in the audit of 2026-11-20; not applied | `<vault>/Causal Analysis Engine/Audit of Causal Results 2026-11-20.md`, section 3 |

The report's rule keeps a value only when $e^{Y} - 1 \ge 1$, that is a total of at least one step. It runs before the
own past means are computed, so those means also leave zero days out ([08](08-controls.md#the-standard-set)).
[src: report/ihs_report/build/history.py, zero_step_days_missing; report/ihs_report/build/tables.py, analysis_table]

## Sleep that night: the clock window

**Outcome.** Minutes asleep: the sum of the instrument's sleep minutes over the hours of the post window, blank hours
counting as zero. Column `sleep_minutes_post`. The window runs from the send hour to the next day's decision, so it
holds the night after the message. Applied (`sleep_measure: null`, the default).
[src: causal/src/ihs_causal/data/features.py, window_stats (rule `sum0`) and apply_rules;
causal/src/ihs_causal/defaults.yaml, `sleep_measure`]

**Kept when** all of the following hold. Applied.
[src: causal/src/ihs_causal/data/features.py, apply_rules; causal/src/ihs_causal/defaults.yaml, `keep`]

1. The post window's span is 20 to 28 hours.
2. At least one hour of the window has sleep minutes above zero. No sleep record means missing, not zero.
3. Either the total is at least `keep.sleep_short_night_minutes` = 180 minutes, or the device was observed in at least
   `keep.sleep_night_wear_min` = 0.67 of the overnight hours:
   $\text{observed overnight hours in the window} / 9 \ge 0.67$.

Notes:

- **Minimum wear in hours.** $0.67 \times 9 = 6.03$, so a short night needs at least 7 observed overnight hours. The
  denominator is always 9, even when a window longer than 24 hours holds more than nine overnight hours.
  [derived from apply_rules (`night_len`)]
- **Which night.** The night after the message: the window starts at the send hour and ends at the next decision. The
  2026-11-18 investigation describes the outcome as minutes asleep "from the message (about 3 pm) to the next day's
  decision". [src: <vault>/Causal Analysis Engine/Mindfulness and Sleep Investigation.md, "What was compared"]
- **Daytime sleep is in the window.** The engine neither drops nor flags day-sleep nights. Any sleep between the send
  hour and the next decision counts, naps included. A sleep that began before the send hour contributes only its part
  after that hour; for a participant sleeping by day the window can hold the end of one sleep and the start of the next.
  The audit of 2026-11-20 named these nights as the ones the clock window measures worst.
  [src: causal/src/ihs_causal/data/features.py, window_stats; <vault>/Causal Analysis Engine/Audit of Causal Results
  2026-11-20.md, section 3, item 3]
- **The presentation's daytime-sleep moderator** is built separately from the hourly sleep profile
  ([09](09-moderators.md)); it does not change the outcome.
- **How sleep minutes reach the hours** (Fitbit episodes, Garmin and Apple rules) is in
  [02, Fitbit sleep](02-hourly-files.md#fitbit-sleep) and the rest of [02](02-hourly-files.md).

## Sleep from complete episodes (option)

`sleep_measure: complete_episode`. Option, not default. Neither the report nor the presentation sets it, and no standing
configuration in `causal/config/` names it; the app's Run tab can run it, alone or beside the clock window. It follows
the audit's proposal of 2026-11-20 to build sleep from episodes and attach each to the decision before it began
(Proposed there, now available as this option).
[src: causal/src/ihs_causal/data/sleep.py; causal/src/ihs_causal/workspace.py, Workspace.features and episode_stats;
causal/tests/test_sleep_episodes.py; <vault>/Causal Analysis Engine/Audit of Causal Results 2026-11-20.md, section 3]

It needs `next_decision` windows and an episode file per cohort (file kind `sleep_episodes`, default names
`2024SleepEpisodes.parquet` and `2025SleepEpisodes.parquet`, with columns `participant_id`, `device`, `writer`,
`start_local`, `end_local`, `start_utc`, `end_utc`, `minutes`, `short_or_nap`). How the episode files are made is not in
the engine. [src: causal/src/ihs_causal/paths.py, FILES; causal/src/ihs_causal/data/sleep.py, EPISODE_COLUMNS]

Rules, version `native-main-episode-v1` [src: causal/src/ihs_causal/data/sleep.py, link_episodes and local_offset]:

1. **Episodes used:** at least 120 minutes and not flagged `short_or_nap`.
2. **Slot:** each decision's [anchor, post-window end). In 2025 the slot starts at the exact anchor when it lies within
   one hour of the floored anchor. Garmin episodes are matched in UTC. Other devices are matched in local time: the slot
   is shifted by the participant's local offset, taken from the paired local and UTC hour nearest the anchor within 24
   hours. The offset is withheld near an unresolved clock switch (the nearest hours on either side, each within two
   hours, disagree) and when it falls outside -12 to +14 hours.
3. **Link by onset:** an episode belongs to the latest slot that starts at or before its onset, provided the onset is
   before that slot's end. Its full duration is kept even when it runs past the slot.
4. **One per decision:** the longest linked episode; a tie goes to the earliest onset.
5. Two slots of one participant with the same start are both dropped.
6. `apple` takes episodes written by any Apple source; `apple_watch` only those written by the watch.
7. **Kept** when the post window's span is 20 to 28 hours and an episode is linked. No wear rule and no 180-minute rule
   apply. [src: causal/src/ihs_causal/workspace.py, Workspace.features]

## Mood

**Outcome.** The mean of the mood responses whose hour falls in the post window. Column `Mood_post`. Applied.
[src: causal/src/ihs_causal/data/features.py, window_stats (`mood_mean_post`) and apply_rules]

- **Source.** The hourly `Mood` column, the survey score; a value of 0 means "no response" and becomes missing.
  [src: causal/src/ihs_causal/data/hourly.py, read_hourly] The files in use place each response at its exact completion
  time (`Hourly_MoodCorrected_20261117`). [src: causal/config/data_notes.yaml; causal/config/paths.example.yaml] See
  [05](05-mood-timing.md).
- **Kept when** the post window's span is 20 to 28 hours, it holds at least one response, and, in a single-device view,
  the participant is in that view. [src: data/features.py, apply_rules]
- **Which survey.** Whatever responses were completed between the send hour and the next day's decision. It is not "the
  next survey": a response after the next decision belongs to the next window, and a window without one is missing. Two
  responses in one window are averaged. [derived from window_stats and apply_rules]
- **Scale.** Points on the 1 to 10 scale. [src: report/ihs_report/moderation.py, module docstring;
  report/ihs_report/analyses/pooled_effects.py, module docstring]
- `Mood_sd_pre` and `Mood_n_pre` (SD and number of responses in the pre window) are stored without the span check.
  They are outcome-model variables for DR-WCLS, not WCLS controls. [src: data/features.py, apply_rules;
  causal/src/ihs_causal/defaults.yaml, `nuisance`]

## The day-before values

The pre window gets the same keep rules as the post window. Applied.
[src: causal/src/ihs_causal/data/features.py, apply_rules (loop over `post` and `pre`)]

| Column | Value | Missing when |
|---|---|---|
| `Mood_pre` | Mean mood response in the pre window | No pre window (first analysed decision), span outside 20 to 28 hours, no response, or (single-device view) participant not in the view |
| `log_steps_pre` | log(1 + steps) in the pre window | As for steps; in the report and presentation also a total below one step |
| `sleep_minutes_pre` | Minutes asleep in the pre window: the night before this decision | As for sleep |

- When decisions are consecutive the pre window is exactly yesterday's post window, so these are yesterday's outcomes.
  After a skipped or excluded day the pre window is the interpolated grid day before the anchor.
  [src: causal/src/ihs_causal/data/windows.py, next_decision_windows]
- **A date range does not cut history.** With `date_from` set, the first decision in range still takes its day-before
  values from the day before, outside the range. [src: causal/src/ihs_causal/data/features.py, in_dates]
- Their use as controls, and the report's own past means built from them, are in [08](08-controls.md).

## Other window statistics

Layer 1 also stores, per window and instrument: mean heart rate, mean resting heart rate, observed hours, observed
overnight hours, hours with sleep, and (Apple) hours observed by the watch. Layer 2 turns them into `hr_avg_pre`,
`RHR_pre`, `observed_hours_pre`, `watch_share_pre` (watch hours over observed hours) and the main-device indicators
`device_is_fitbit`, `device_is_garmin`. They enter the DR-WCLS outcome model and some moderators, not the WCLS
controls. [src: causal/src/ihs_causal/data/features.py, window_stats, apply_rules, CONTEXT;
causal/src/ihs_causal/defaults.yaml, `nuisance`]

## Outcome transforms not used by default

The report's "other levers" check refits every comparison with the outcome capped. Option, not default: no presentation
figure or main report estimate uses it. [src: report/ihs_report/analyses/other_levers.py, module docstring;
report/config/analysis.yaml, `levers`]

- `clip_cohort`: the outcome capped at the 2.5th and 97.5th percentiles of the cohort's values.
- `clip_own`: capped at the participant's own past mean plus and minus 2 within-participant SDs; decisions without an
  own past mean are left as they are.

## Rule versions and caching

- **Builder versions:** hourly table 2, decision table 4, window statistics 5. A cached table is rebuilt when its
  version or an input file's fingerprint changes. [src: causal/src/ihs_causal/workspace.py, VERSIONS]
- **Outcome-rule version recorded with every result.** Each stored engine run records the input file fingerprints plus
  `outcome_rules: window-stats-v5`; a run stored under other inputs or rules is flagged as made from older data and is
  rerun by `ihs-causal refresh` or `reproduce`. Runs with complete episodes also record the episode file's fingerprint
  and `episode_rules: native-main-episode-v1`. [src: causal/src/ihs_causal/workspace.py, Workspace.result_inputs;
  causal/src/ihs_causal/results.py, inputs_match, older_data; causal/src/ihs_causal/runner.py, pending_specs]
- **The report's cache** keys on the same fingerprints and outcome-rule version, on all of `report/config/analysis.yaml`,
  and on the code of the engine's data, design and estimator modules. [src: report/ihs_report/context.py,
  Context.inputs; report/README.md, "How the cache works"]

## 2024 and 2025 side by side

| Item | 2024 | 2025 | Source |
|---|---|---|---|
| Anchor column | `hour_utc` (decision file): attempt hour for messages, imputed hour for no-message days | `window_anchor_utc` (timing file): logged attempt for messages, the day's observed send hour for no-message days | `data/decisions.py`; [06](06-decisions-and-probabilities.md) |
| Analysis set | 2024-07-01 to 2025-06-30 with `time_source` | `retain_main_reach_retrospective` (study windows from July 1, 2025 to June 30, 2026, whole days excluded) | `data/decisions.py`; [06](06-decisions-and-probabilities.md) |
| Wearable data at the end of the year | Through June 30, 2025 (not checked here) | Stop near June 20, 2026 | [06](06-decisions-and-probabilities.md), [02](02-hourly-files.md) |
| Hourly file in use | `Hourly_MoodCorrected_20261117/dfHourly2024.csv` (Codex's November 17 rebuild with mood at completion time) | `Hourly_MoodCorrected_20261117/dfHourly2025.csv` (published November 17 file with mood at completion time) | `causal/config/data_notes.yaml`, `paths.example.yaml` |
| Episode option, exact anchor | Not used (floored hour) | Used when within one hour | `workspace.py`, `episode_stats` |
| Window, keep and device rules | Identical | Identical | `data/features.py` |

## Where code and documentation disagree

Code wins in every case below.

1. **Blank step cells.** `causal/docs/DESIGN.md` ("Keep rules") and `<vault>/Causal Analysis Engine/ihs-causal
   Design.md` say "a blank step cell in an observed hour is a real zero". The working-tree code treats a blank cell as
   missing and requires at least one step record; the module docstring and the app's About text were updated, the
   design documents were not.
2. **Anchor wording for 2024.** `causal/docs/DESIGN.md` says 2024 anchors "at the decision hour"; the
   `decisions.py` docstring says every anchor is the logged send or assigned time. Both refer to the same column,
   `hour_utc`, which floors the attempt time for messages and an imputed hour for no-message days
   ([06](06-decisions-and-probabilities.md#how-the-2024-table-was-built-november-16-2026)). "Decision hour" is loose.
3. **Engine README keep rule for steps** ("at least 10 observed hours") omits the step-record requirement.
   [src: causal/README.md, "Rules built in"]
4. **Engine defaults against the values in use.** The engine's defaults are a floor of 0.001 and an arm minimum of
   200; the report and presentation use 0.001 for 2024, 0.01 for 2025 and 50
   ([10](10-analysis-rules.md#settings-by-pipeline)). Note 06 now states both.

## Unverified

- The date of the step-record change (`window-stats-v5`): the audit memory says 2026-11-20; it is uncommitted.
- Whether the engine's 2025 windows agree with the published grid's window flags, and how many flagged decisions the
  engine keeps that the published window flag does not (no data were opened for these notes).
- How the sleep-episode files are built; the engine only reads them.
- That the send hour's pre-send minutes matter in practice; the boundary effect follows from the code, its size was not
  checked here.
