# Moderators: how each one is built

This note defines every moderator used in the report and in the presentation: what it measures, when it is measured
against the decision, which data it comes from, which "usual" it is compared with, how it is split, how a missing
value is handled, and where it is shown. The report tests weather, circadian misalignment, heart rate variability,
engagement and study time, each per unit of the measure with two display levels. The presentation screens 42 single
moderators in nine families as upper-against-lower halves (figure 1b), adds one two-way family (daytime sleep and
warmth), and puts eleven moderators into one model (figure 2). Most moderators are known before the 3 pm decision; the
weather measures are not (they cover the decision date and the next day), and a few person-level descriptors use the
whole study year. Everything the presentation adds beyond the report's own columns is built outside the repository:
in the presentation pipeline, in audit caches, and in scratch scripts that sit in a temporary folder and must be moved
into the repository.

Path shorthands used below:

- `report/...` is the report project in the repository; `causal/...` is the causal engine in the repository (for now
  under `Drew's code/causal`).
- `<vault>/...` is the project folder in Drew's notes vault, outside the repository. `<vault>/Presentation Plots/...` is
  the presentation pipeline in its `Results and Document Compilation/` folder; the results notes are cited as
  `<vault>/Results and Document Compilation/<note>.md` and are used for definitions only.
- `<audit>/...` is the collaborative audit folder, outside the repository.
- `<scratch>/...` is a temporary session folder. Scripts there are at risk of being cleared and must be moved into the
  repository.

Related notes: [hourly files](02-hourly-files.md), [decisions and probabilities](06-decisions-and-probabilities.md),
[outcome windows](07-outcome-windows.md), [analysis rules](10-analysis-rules.md), [the model](11-model.md) (WCLS and
centring of moderators).

## Contents

- [Summary table](#summary-table)
- [Where the moderators are used](#where-the-moderators-are-used)
- [Rules shared by all moderators](#rules-shared-by-all-moderators)
  - [Timing against the decision](#timing-against-the-decision)
  - [Splits in the report](#splits-in-the-report)
  - [Splits in the presentation](#splits-in-the-presentation)
  - [Minimum group sizes](#minimum-group-sizes)
  - [Missing values](#missing-values)
- [Weather](#weather)
  - [The daily weather table](#the-daily-weather-table)
  - [The app weather feed](#the-app-weather-feed)
  - [Day's high](#days-high)
  - [Warmth against own monthly usual](#warmth-against-own-monthly-usual)
  - [Rain](#rain)
  - [Snow](#snow)
  - [Precipitation amount](#precipitation-amount)
- [Recent sleep](#recent-sleep)
  - [Daytime sleep signs](#daytime-sleep-signs)
  - [Last night's sleep](#last-nights-sleep)
  - [Last night's sleep against own usual](#last-nights-sleep-against-own-usual)
- [Mood and steps before the decision](#mood-and-steps-before-the-decision)
- [Previous week](#previous-week)
- [Engagement and time in study](#engagement-and-time-in-study)
- [The person](#the-person)
  - [Usual mood, sleep and steps](#usual-mood-sleep-and-steps)
  - [Baseline PHQ-9](#baseline-phq-9)
  - [Other baseline traits](#other-baseline-traits)
  - [Device](#device)
- [Circadian misalignment](#circadian-misalignment)
- [Heart rate variability](#heart-rate-variability)
  - [Building the daily table](#building-the-daily-table)
  - [The three measures](#the-three-measures)
- [Message statistic tiers](#message-statistic-tiers)
  - [What a tier is](#what-a-tier-is)
  - [How the tiers were rebuilt](#how-the-tiers-were-rebuilt)
  - [The thousands-comma faults](#the-thousands-comma-faults)
  - [The three tier moderators](#the-three-tier-moderators)
  - [Data shown vs not](#data-shown-vs-not)
- [Daytime sleep and warmth together](#daytime-sleep-and-warmth-together)
- [The joint model's eleven moderators](#the-joint-models-eleven-moderators)
- [Explored, not shown](#explored-not-shown)
- [Built outside the repository](#built-outside-the-repository)
- [Code against notes](#code-against-notes)
- [Measured at or after the decision](#measured-at-or-after-the-decision)
- [Unverified](#unverified)
- [Sources](#sources)

## Summary table

"Moment" moderators describe the decision's day; "person" moderators describe the participant. A "running" person
moderator is recomputed at each decision from earlier days only, so it changes over the year. Keys are the column
names in the code (report column, then the presentation's key where it differs). "1b" is the presentation's moderator
screen, "fig 2" its joint model.

| Moderator | Level | Source | Timing against the decision | Split | Status |
|---|---|---|---|---|---|
| Day's high (`wm_tmax10`; `tmax`) | Moment | Daily weather table: station or gridded daily high at the program's postal code | Decision date and the next date: **spans the decision** | Report: per 10 °C, levels at the comparison's median. 1b: median split | **Both** |
| Warmth against own monthly usual (`wm_anom5`; `anom`) | Moment | Same, minus the participant's mean high for that calendar month | Spans the decision; the monthly mean uses the whole month | Report: per 5 °C, median levels. 1b, joint family, fig 2: median split | **Both** |
| Rain on either day (`wm_rain`; `rain`) | Moment | Precipitation of 1 mm or more on either date | Spans the decision | Yes/no | **Both** |
| Snow on either day (`wm_snow`; `snow`) | Moment | Any snowfall on either date (stations only) | Spans the decision | Yes/no | **Both** |
| Precipitation amount (`wm_logprcp`) | Moment | log(1 + mm over both dates) | Spans the decision | Per log mm; median levels | **In the report** |
| Daytime sleep signs (`daytime`) | Moment | Audit hourly cache: asleep in the hour before, or a recent daytime main sleep | Before: the hour before, and the previous seven decisions' windows | Yes/no; unknown left out | **In the presentation**; **Built outside the repository** |
| Last night's sleep (`pre_h`) | Moment | Engine's day-before sleep (`sleep_minutes_pre`) | Pre window, ends at the decision | Median split | **In the presentation**; **Built outside the repository** |
| Last night's sleep against own usual (`def_h`) | Moment | Day-before sleep minus own past mean | Before | Median split | **In the presentation** (1b, fig 2); **Built outside the repository** |
| Mood before the decision (`mood_pre`) | Moment | Engine's day-before mood (`Mood_pre`) | Before | Median split | **In the presentation**; **Built outside the repository** |
| Mood before against own usual (`mood_dev`) | Moment | Day-before mood minus own past mean | Before | Median split | **In the presentation** (1b, fig 2); **Built outside the repository** |
| Steps before the decision (`steps_pre`) | Moment | Engine's day-before log steps (`log_steps_pre`) | Before | Median split | **In the presentation**; **Built outside the repository** |
| Steps before against own usual (`steps_dev`) | Moment | Day-before log steps minus own past mean | Before | Median split | **In the presentation** (1b, fig 2); **Built outside the repository** |
| Previous week's mood, steps, sleep (`mood7`, `steps7`, `sleep7`) | Moment | Mean of earlier days' outcomes over calendar days d−7 to d−1 | Before | Median split | **In the presentation**; **Built outside the repository** |
| Previous week against own usual (`mood7_dev`, `steps7_dev`, `sleep7_dev`) | Moment | Previous week minus the mean of all earlier days | Before | Median split | **In the presentation**; **Built outside the repository** |
| Usual mood, steps, sleep (`mood_usual`, `steps_usual`, `sleep_usual`) | Person (running) | Mean of all earlier days' outcomes, at least seven | Before | Median split | **In the presentation** (1b, fig 2); **Built outside the repository** |
| Baseline PHQ-9 (`PHQtot0`; `phq`) | Person | Baseline survey, via the engine | Before the study | Median split | **In the presentation** (1b, fig 2); a control, not a moderator, in the report |
| Baseline GAD-7 (`GADtot0`; `gad`) | Person | Baseline survey | Before the study | Median split | **In the presentation** |
| Baseline neuroticism (`Neu0_published`; `neu`) | Person | Baseline survey | Before the study | Median split | **In the presentation** |
| Depression history (`depr0`; `depr`) | Person | Baseline survey | Before the study | Yes/no | **In the presentation** |
| Device (`device_is_fitbit`; `fitbit`) | Person | Engine: main device by observed hours over the whole study | **Uses the whole year** | Yes/no: Fitbit against any other (or none) | **In the presentation** (1b, fig 2) |
| Mood entries in the past week (`sg_eng7`; `eng7`) | Moment | Days among the previous seven calendar days with a mood entry | Before | Report: per entry; levels none vs at least one. 1b: none vs at least one | **Both** |
| Time in study (`sg_t30`; `t30`) | Moment | Study day / 30 | Known in advance | Report: per 30 days, median levels. 1b, fig 2: median split | **Both** |
| First 30 days (`sg_early`; `early`) | Moment | Study day below 30 | Known in advance | Yes/no | **Both** |
| 7-day tier: low (`<outcome>_tier7`; `tier_low`) | Moment | Rebuilt server statistic tier of the outcome's domain | Before (2024: see the 20:00 UTC caveat) | Low against medium or high; neutral left out | **In the presentation**; **Built outside the repository** |
| 7-day tier: high (`<outcome>_tier7`; `tier_high`) | Moment | Same | Same | High against low or medium; neutral left out | **In the presentation**; **Built outside the repository** |
| Statistics the server could read (`<outcome>_n_avail`; `avail`) | Moment | How many of the domain's nine statistics the server could parse | Same | All nine against fewer | **In the presentation**; **Built outside the repository** |
| Heart-rate clock against sleep midpoint (`cm_crpo_d1`, `cm_crpo_m7`) | Moment | 2024 circadian files, used as supplied | Day before; seven days before | Report: per hour, median levels. 1b: median split | **Both** (2024 only) |
| Model clock against sleep midpoint (`cm_crco_d1`, `cm_crco_m7`) | Moment | Same | Same | Same | **Both** (2024 only) |
| Two clocks against each other (`cm_internal_d1`, `cm_internal_m7`) | Moment | Same | Same | Report: per unit of the model clock's uncertainty. 1b: median split | **Both** (2024 only) |
| Sleep midpoint away from own usual (`cm_midoff_d1`, `cm_midoff_m7`) | Moment | Same; usual = circular mean over the whole file | Day before; **usual uses the whole year** | Report: per hour, median levels. 1b: median split | **Both** (2024 only) |
| HRV before the decision against own usual (`hv_today`) | Moment | 2024 daily HRV table built from raw exports | 24 hours before 3 pm | Report: per own SD, median levels. 1b: median split | **Both** (2024 only) |
| HRV over the previous 7 days against own usual (`hv_week`) | Moment | Same | Seven dates before the decision date | Same | **Both** (2024 only) |
| Usual HRV against others on the same device type (`hv_usual`) | Person (running) | Same | Before; device type chosen over the whole file | Report: per doubling, median levels. 1b: median split | **Both** (2024 only) |
| Daytime sleep and warmth together (`dw_*`) | Moment | `daytime` and `wm_anom5` in one model | Daytime before; warmth spans the decision | Four groups | **In the presentation**; **Built outside the repository** |
| The eleven together (figure 2) | Mixed | Six moment and five person moderators above | As each | Upper against lower, plus a "not recorded" group | **In the presentation**; **Built outside the repository** |

## Where the moderators are used

**Report.** Five analyses test moderators, each over the whole year:

| Analysis | Moderators | Cohorts | Controls |
|---|---|---|---|
| `weather_moderation` | rain, precipitation amount, day's high, warmth against own monthly usual, snow | 2024, 2025, pooled | Standard |
| `weather_moderation_long` | the same | 2024, 2025, pooled | Long history, as principal components |
| `circadian_moderation` | eight circadian measures | 2024 | Standard |
| `hrv_moderation` | three HRV measures | 2024 | Standard |
| `engagement_moderation` | mood entries in the past week, time in study, first 30 days | 2024, 2025, pooled | Standard |

[src: report/ihs_report/analyses/weather_moderation.py, weather_moderation_long.py, circadian_moderation.py,
hrv_moderation.py, engagement_moderation.py; report/config/analysis.yaml, `weather.period`, `circadian`, `hrv`]

Every report analysis runs seven comparisons per outcome against no message: any message, a message of the outcome's
own domain, and each of the five strategies. For each measure it reports the change in the message effect per unit of
the measure from a model with the measure as a control and as a moderator ("inter"), the effect at the measure's
average among decisions that have it ("est"), and the effect at a lower and a higher level from separate fits on each
side of a cut ("lo", "hi"). The levels are for display; "inter" is the test.
[src: report/ihs_report/moderation.py, module docstring and `fit_cohort`]

**Presentation.** The page `<vault>/Presentation Plots/plots.html` has three figures:

- **Figure 1**, the "usual set" of overall effects. No moderator, except that its "data shown vs not" row is restricted
  to decisions with all nine own-domain statistics readable ([Data shown vs not](#data-shown-vs-not)).
  [src: <vault>/Presentation Plots/build_data.py, module docstring]
- **Figure 1b**, the moderator screen for the effect picked in figure 1: the families of `FAMILY_ORDER` (weather, recent
  sleep, before the decision, previous week, the person, engagement and time in study, message statistic tier,
  circadian misalignment (2024 only), heart-rate variability (2024 only), daytime sleep and warmth), each shown as the
  upper half minus the lower half or as both halves. Its top panel is a cumulative effect curve, not a moderator.
  [src: <vault>/Presentation Plots/plots.html, `FAMILY_ORDER`; pipeline/screen_fit.py, `FAMILIES`, `JOINT`;
  pipeline/cumulative_fit.py]
- **Figure 2**, eleven moderators in one model, "together" and "alone".
  [src: <vault>/Presentation Plots/pipeline/joint_fit.py, `MODS`]

The presentation's comparisons are the report's seven plus own-domain data vs no data (Cognitive Strategies,
Behavioral Strategies, Motivational Interviewing and mindfulness, data and no-data versions within the outcome's
domain, among decisions with all nine statistics readable). Periods: July–December, whole year, January–June. Cohorts:
2024, 2025, and pooled by inverse variance; the circadian and HRV families are fitted for 2024 only, and where only one
cohort has an estimate the pooled row is that cohort. Controls: the report's standard set. Released probabilities;
at least 50 messages per arm. [src: <vault>/Presentation Plots/pipeline/screen_fit.py, `CONTRASTS`,
`own_data_vs_nodata`, `PERIODS`, `MIN_ARM`, `fit_cohort`, `combine`, `__main__`]

How the presentation gets its moderator columns: `screen_mods.py` builds every moderator once per cohort and writes one
participant-level table per cohort to `<audit>/Opus/ModScreen-20261124/mods_<cohort>.parquet`. It takes the weather,
engagement, circadian and HRV columns from the report's own build modules, so those definitions are identical to the
report's; it derives the recent-sleep, before-the-decision, previous-week and usual columns from the report's analysis
table; and it adds the daytime-sleep sign and the statistic tiers from audit caches. The fitting scripts refuse to run
if the cache does not line up row by row (participant and day) with the current analysis table.
[src: <vault>/Presentation Plots/pipeline/screen_mods.py, `build`; screen_fit.py, `fit_cohort` assertion]

## Rules shared by all moderators

### Timing against the decision

- The study sent at 15:00 local time on 99% of dated decisions (as stated in the HRV builder).
  [src: report/ihs_report/build/hrv_build.py, module docstring]
- The engine's default window, `next_decision`, lays each participant's decisions on a daily grid. The post window of a
  decision runs from its anchor to the next decision's anchor when that falls on the next grid day, otherwise for 24
  hours; the pre window is the previous grid day, ending at the current anchor. So the outcome window of every earlier
  decision ends at or before the current decision, and any moderator built from earlier decisions' outcomes is known
  before the current one. Detail in [outcome windows](07-outcome-windows.md).
  [src: causal/src/ihs_causal/data/windows.py, `next_decision_windows`; causal/src/ihs_causal/defaults.yaml, `window`]
- Moderators that are not known before the decision are listed in
  [Measured at or after the decision](#measured-at-or-after-the-decision).

### Splits in the report

- **Continuous measure:** tested per unit. The two display levels are at or below, and above, the median of the measure
  over that comparison's decisions (the reference and the compared arm) that have the outcome and the measure
  recorded, taken before the probability floor (decisions without a probability still drop out). The median is per
  cohort, per comparison and per compared arm.
  [src: report/ihs_report/moderation.py, `_medians`, `fit_cohort` (`cut is False`)]
- **Yes/no measure:** tested yes against no; levels no and yes (cut at 0.5). [src: moderation.py, `fit_cohort`]
- **A named cut:** mood entries in the past week is cut at 0: no entries (at or below 0) against at least one.
  [src: report/ihs_report/build/signal.py, `MODERATORS`]
- Ties at the median go to the lower level (`v <= cut`). [src: moderation.py, `fit_cohort`, `levels`]

### Splits in the presentation

One indicator per moderator, made by `indicator` [src: <vault>/Presentation Plots/pipeline/screen_fit.py, `indicator`]:

| Kind | Upper level | Used for |
|---|---|---|
| `cont` | Above the median of the moderator over all decisions of that cohort and period that have the outcome and the moderator recorded (before any probability rule and for all arms, not per comparison) | Every continuous moderator |
| `bin` | Value above 0.5 | Rain, snow, daytime sleep, depression history, device, first 30 days |
| `pos` | Value above 0 | Mood entries in the past week |
| `nine` | Value 9 or more | Statistics readable |
| `low`, `high` | Tier equals low (or high); neutral is unknown | 7-day tier |

- **Ties:** if the share above the median falls outside 20–80% (heavy ties), values equal to the median go to the upper
  half instead. [src: screen_fit.py, `indicator`]
- **The model:** one WCLS fit per moderator and comparison, with the report's standard controls plus the indicator as a
  control and as the moderator (centred by the engine). Both halves and the difference come from that one fit, with
  standard errors from the per-participant influence values. [src: screen_fit.py, module docstring, `halves`]
- **The "data" comparison** takes its median from all decisions of the cohort, period and outcome, then keeps only the
  decisions with all nine statistics readable. [src: screen_fit.py, `fit_cohort`, `readable`]
- **Figure 2** uses the same splits ("Splits are those of figure 1b").
  [src: <vault>/Presentation Plots/pipeline/joint_fit.py, module docstring, `splits`]

### Minimum group sizes

| Rule | Value | Where | Meaning |
|---|---|---|---|
| `min_arm_rows` | 50 | Report and presentation | An arm with fewer decisions than this (after the moderator's complete-case filter) is not estimated; in the report a display level with fewer sends is left blank |
| `MIN_HALF` | 30 | Figure 1b, single moderators | For each compared arm, each half needs at least 30 messages and at least 30 reference decisions (no message; no-data messages in the "data" comparison), or that arm is skipped |
| `MIN_GROUP` | 30 | Figure 1b, daytime sleep and warmth | Each of the four groups needs at least 30 messages and 30 reference decisions |
| none further | | Figure 2 | Only `min_arm_rows` applies |

[src: report/config/analysis.yaml, `min_arm_rows` ("was 200; lowered 2026-11-24"); causal/src/ihs_causal/design/contrasts.py,
`_frame`; <vault>/Presentation Plots/pipeline/screen_fit.py, `MIN_ARM`, `MIN_HALF`, `MIN_GROUP`, `halves`, `quarters`;
joint_fit.py, `fit`]

### Missing values

- **Engine rule:** in any fit with a moderator, a decision whose moderator is missing is dropped (complete cases for the
  moderator). Missing controls are filled with the median over the fitted rows. Detail in [the model](11-model.md).
  [src: causal/src/ihs_causal/design/contrasts.py, `_frame` ("complete cases for the moderator");
  causal/src/ihs_causal/data/features.py, `covariate_matrix`]
- **Report:** the test and both levels use only decisions with the measure recorded; the overall effect uses all
  decisions. The "est" column is the effect among decisions that have the measure, which can differ from the overall
  effect when the measure covers part of the cohort. [src: report/ihs_report/moderation.py, module docstring]
- **Figure 1b:** recorded decisions only. An unknown moderator gives a missing indicator, and the engine drops the
  decision from that fit. [src: screen_fit.py, `indicator`; contrasts.py, `_frame`]
- **Daytime sleep and warmth:** decisions with both recorded. [src: screen_fit.py, `fit_cohort` JOINT branch]
- **Figure 2:** nothing is dropped for a missing moderator. For each of the eleven, the upper-half indicator is set to 0
  where the moderator is not recorded, and a "not recorded" indicator (added only when some value is missing) enters
  as a control and a moderator. The reference group is therefore "lower half, recorded"; the upper-half coefficient is
  upper minus lower among recorded decisions. The not-recorded coefficients are fitted but not shown.
  [src: <vault>/Presentation Plots/pipeline/joint_fit.py, `splits`, `fit_cohort`]

## Weather

All five weather measures describe the weather at the participant's training program, not where the participant was.
They are built in the repository by the report's code, and the presentation reads the same columns.
[src: report/ihs_report/build/weather.py, module docstring; <vault>/Presentation Plots/pipeline/screen_mods.py, `build`]

### The daily weather table

`<cohort>WeatherDaily.parquet` has one row per participant and date from July 1 of the cohort year to July 1 of the
next year inclusive, so the day after the last decision can be read. A supplied copy is used as it is; otherwise the
report builds it once into the engine's work folder from raw files and rebuilds it when a raw file, a setting or the
code changes. [src: report/ihs_report/build/weather_build.py, module docstring, `daily`, `build`; report/README.md,
"Further input files"]

Raw inputs: each cohort's survey file, the app weather feed (2024 only), the list of participants with decisions, and
a folder of public files: the Census 2024 ZCTA gazetteer (`zcta.zip`), ACS 2024 5-year total population
(`acsdt5y2024-b01003.dat`), the GHCN-Daily station list and year files (`stations.txt`, `<year>.csv.gz`), and
nClimGrid-Daily monthly files (`nclimgrid/ncdd-*.nc`). [src: report/README.md, "Further input files";
weather_build.py, module docstring]

Settings: `near_km` 10, `max_km` 50, `other_stations` 20, `min_share` 0.90, `min_share_snow` 0.50, `rain_mm` 1.0.
[src: report/config/analysis.yaml, `weather_build`, `weather.rain_mm`]

**Step 1. A program postal code for every participant.** Best source first:

1. The direct source. 2024: the commonest program postal code in the app weather feed (rows of type
   `Program_WeatherData`). 2025: the survey field `ProgramZipCode`. Confidence "high".
2. Otherwise the postal code of other participants (from both cohorts' direct sources) with the same 10-digit program
   code (`ResidencyProgram`, digits only, padded to 10). Confidence "medium" when the code maps to one postal code,
   "low" when it maps to several that all lie within `near_km` (the commonest is used).
3. Otherwise the postal code of participants with the same program name (`ProgramName`, or the free-text program
   fields, lower-cased with punctuation removed and "&" read as "and", exact match). Confidence "low".
4. A code or name that maps to several postal codes more than `near_km` apart gives none.
5. In a feed cohort (2024), a participant still without a program postal code falls back to the commonest personal
   postal code in the feed (rows of type `WeatherData`), flagged `personal_fallback`.

Participants with decisions, or in the feed, who are missing from the survey file are added with no survey fields.
Postal codes of all cohorts are assigned together, because one cohort's participants can supply another's.
[src: weather_build.py, `zip_assignments`, `_resolve`, `_infer`, `read_feed_zips`, `norm_code`, `norm_name`, `zip5`, `build`]

Postal codes are sensitive: the assignments are written only to the engine's work folder, and the daily table does not
hold them. [src: report/README.md, "Where things live"; weather_build.py, module docstring]

**Step 2. A point for every postal code.** The ZCTA internal point from the gazetteer. A postal code that is not a ZCTA
(often a single hospital) gets the population-weighted centre of the ZCTAs sharing its first three digits, with ACS
2024 total population as the weight. [src: weather_build.py, `zip_points`]

**Step 3. Candidate stations.** US GHCN-Daily stations within `max_km` (50 km) of the point: every airport station
(network `USW`) in range, plus the `other_stations` (20) nearest stations of other networks.
[src: weather_build.py, `candidates`]

**Step 4. Station values.** Daily `TMAX`, `TMIN`, `PRCP` and `SNOW` of the candidates, from the GHCN-Daily year files,
read from June 25 of the first cohort year to July 5 after the last. Any value with a quality flag is dropped.
Temperature needs both `TMAX` and `TMIN` with `TMIN` ≤ `TMAX`; precipitation and snow must be 0 or more. Units:
temperature and precipitation are stored in tenths and divided by 10 (°C, mm); snow is in mm.
[src: weather_build.py, `station_obs`, `daily`, `build`]

**Step 5. Gridded fallback.** NOAA nClimGrid-Daily (about 4.6 km cells): daily high, low and precipitation at the
nearest valid cell within four cells of the point. It needs the `h5py` package; without it the fallback is left out
and, per the README, a few hundred participant-days lose their value. There is no gridded snowfall.
[src: weather_build.py, `grid_values`; report/README.md, "Further input files"]

**Step 6. A value for each postal code and date,** separately for temperature, precipitation and snowfall. Candidates
are ordered airport stations first, then by distance. The **primary station** is the first candidate with values on at
least `min_share` (90%) of the cohort year's days (50% for snowfall, which many stations report only in winter). On a
day the primary station has no value, the next candidate in that order that has one is used ("station_fallback"); for
temperature and precipitation, failing that, the gridded value ("grid"). Each row records its source, station,
network, distance and whether its day was shifted; a `quality` column summarises the temperature and precipitation
sources (`station_primary`, `station_with_fallback`, `uses_grid`, `no_location`, `incomplete`). `rain_day` is 1 at
`rain_mm` (1 mm) or more. [src: weather_build.py, `daily`, `choose`, `DAILY_COLUMNS`]

**Day alignment (the morning-observer shift).** A station whose observation time is before noon reports the 24 hours
ending that morning, so its value is moved back one day. Stations with no observation time are not moved. Every
gridded value is moved back one day, on the code's statement that grid values are labelled by the morning that ends
their period. The README lists this alignment as needing independent review.
[src: weather_build.py, module docstring, `daily` (`obs_time` < 1200), `grid_values` (`label_date` − 1 day);
report/README.md, "Still to do for replicability"]

**Checks and coverage, as documented.** The rebuilt tables were identical in every cell to the tables made during the
audit of November 22, 2026 (checked November 23). [src: report/README.md, "Further input files"] The weather results
note reports, for the rebuilt table: weather on the decision date and the next for 92% (2024) and 97% (2025) of kept
decisions, against 51% and 87% for an earlier build; 845 of 917 (2024) and 888 of 922 (2025) participants in the
analysis with weather; fifteen 2024 participants on the personal-location fallback; a median station distance of 8 km;
and a check of daily highs against the app feed for January to June 2025.
[src: <vault>/Results and Document Compilation/Weather as a Control and Moderator of Message Effects.md, "The weather table"]
The README notes that some snowfall values are implausibly high. [src: report/README.md, "Still to do for replicability"]

### The app weather feed

`Weather/Weather_IHS_<cohort>.csv`, supplied for the 2024 cohort only: one row per participant, date and kind of
location (`Program_WeatherData` for the training program, `WeatherData` for the participant's own location), with
postal code, low and high temperature, precipitation, snow accumulation and probability of precipitation.
[src: report/config/analysis.yaml, `weather_feed`; report/ihs_report/inputs.py, `EXTRA_FILES`;
report/ihs_report/build/blocks.py, `FEED_COLUMNS`, `feed_features`]

It has two roles, neither as a moderator:

- **Source of 2024 program postal codes** for the weather table (step 1 above). [src: weather_build.py, `read_feed_zips`]
- **A control block** in the report's precision chapter: the feed's values for the decision date and the next, with the
  participant's own location preferred over the program's, plus log precipitation, any rain (precipitation above 0.05
  in the feed's units) and the high against the participant's mean high over the whole feed.
  [src: report/ihs_report/build/blocks.py, `feed_features`, `weather_feed`; report/chapters/_precision.qmd]

The results note describes the feed as calling more rain than the stations, "consistent with a forecast"; whether it
is a forecast or an observation is unverified. [src: <vault>/Results and Document Compilation/Weather as a Control and
Moderator of Message Effects.md, "The weather table"]

### Day's high

- **Definition:** the mean of the daily high on the decision date and the next date, in units of 10 °C:
  (high on d + high on d+1) / 20. Missing if either date lacks a high.
  [src: report/ihs_report/build/weather.py, `add_weather` (`wm_tmax10`)]
- **Timing:** spans the decision (see [Measured at or after the decision](#measured-at-or-after-the-decision)). The
  outcome window runs from the message into the next day, so both dates are summarised; a message cannot change the
  weather, which is the code's and the report's argument for using it as a moderator.
  [src: weather.py, module docstring; report/chapters/_weather-moderation.qmd]
- **Baseline compared with:** none; it is the absolute temperature.
- **Split:** report, per 10 °C with colder and warmer halves at the comparison's median; 1b, median split ("cooler
  half", "warmer half"). [src: report/ihs_report/tables.py, `LEVEL_NAMES`; screen_fit.py, `FAMILIES["weather"]`]
- **Status: Both.** Also tested in the report under long-history controls.
  [src: report/ihs_report/analyses/weather_moderation_long.py]

### Warmth against own monthly usual

- **Definition:** for each date, the daily high minus the participant's own mean daily high over that calendar month
  (all days of the month in the participant's weather table); the measure is the mean of this departure over the
  decision date and the next, in units of 5 °C. Missing if either date lacks a high.
  [src: weather.py, `load_daily` (`anom`), `add_weather` (`wm_anom5`)]
- **The "usual":** the participant's monthly mean high at the program location over the whole calendar month,
  including days after the decision. Participants sharing a program postal code share the same usual. It removes the
  time of year and the place. Because the table ends on July 1 of the next year, that date forms a one-day month whose
  departure is 0 by construction. [src: weather.py, `load_daily`; weather_build.py, `daily` (date range)]
- **Timing:** spans the decision; the usual uses the whole month.
- **Split:** report, per 5 °C with "cooler than usual" and "warmer than usual" levels at the comparison's median; 1b,
  the daytime-and-warmth family and figure 2, median split with the same labels. The labels mean below and above the
  **median departure**, not below and above zero. [src: report/ihs_report/tables.py, `LEVEL_NAMES`; screen_fit.py,
  `FAMILIES["weather"]`, `JOINT`; joint_fit.py, `MODS`]
- **Status: Both** (report weather chapter; presentation 1b, the joint family and figure 2).

### Rain

- **Definition:** 1 if the decision date or the next date had at least `rain_mm` (1.0 mm) of precipitation, else 0.
  Missing unless both dates have a precipitation value. [src: weather.py, `add_weather` (`wm_rain`);
  report/config/analysis.yaml, `weather.rain_mm`]
- **Timing:** spans the decision.
- **Split:** yes against no in both places. [src: weather.py, `MEASURES`; screen_fit.py, `FAMILIES["weather"]`]
- **Status: Both.**

### Snow

- **Definition:** 1 if the decision date or the next date had any snowfall (above 0 mm), else 0. Missing unless both
  dates have a snowfall value. Snowfall comes from stations only (primary station at a 50% share, then any candidate
  with a value), with no gridded fallback, so it is missing more often than the other measures.
  [src: weather.py, `add_weather` (`wm_snow`); weather_build.py, `daily`]
- **Timing:** spans the decision.
- **Split:** yes against no. Snow days are few, so the report's snow level is blank for most single strategies.
  [src: report/chapters/_weather-moderation.qmd, "How to read these"]
- **Status: Both.**

### Precipitation amount

- **Definition:** log(1 + precipitation in mm summed over the decision date and the next), with negative values set to
  0. Missing unless both dates have a value. [src: weather.py, `add_weather` (`wm_logprcp`)]
- **Timing:** spans the decision.
- **Split:** report, per log mm with less and more precipitation at the comparison's median. It is built into the
  presentation's moderator cache but is not in any presentation family.
  [src: report/ihs_report/tables.py, `LEVEL_NAMES`; screen_mods.py, `build`; screen_fit.py, `FAMILIES`]
- **Status: In the report.**

## Recent sleep

### Daytime sleep signs

**Status: In the presentation** (1b "Recent sleep", the daytime-and-warmth family, figure 2). **Built outside the
repository:** the sign is derived in `screen_mods.py` from the audit's participant-level caches
`<audit>/Opus/MfnSleep-20261118/cache/base_<cohort>.parquet` and `prof_<cohort>.npz`, made on November 18, 2026 by
`m01_build_tables.py` from the engine's analysis table and hourly file of that date. If the study files change, these
caches are not rebuilt automatically. [src: <vault>/Presentation Plots/pipeline/screen_mods.py, `DAYTIME`, `daytime`;
<audit>/Opus/MfnSleep-20261118/m01_build_tables.py, module docstring]

The hourly profile holds, for each decision and the participant's main device, minutes asleep, steps, heart rate and an
"observed" flag for each hour from 24 hours before the decision hour to 48 hours after, plus the local hour of day of
the decision (from the nearest hour that has a local label). See [hourly files](02-hourly-files.md).
[src: m01_build_tables.py, `OFFS`, `anchor_lhod`]

Definition [src: screen_mods.py, `daytime`]:

1. **Main sleep of a decision's window:** in the 24 hours from the decision hour, the longest run of consecutive hours
   with any sleep (the first such run if tied). Its onset is the local clock hour of its first hour. The window counts
   only if the engine's sleep outcome for that decision is recorded, the run exists, and the local hour is known.
2. **Daytime main sleep:** onset from 05:00 to 16:59 local.
3. **Recent daytime pattern:** among the participant's previous seven decisions (rows, not calendar days), at least
   three with a main-sleep onset, the share with a daytime onset is 0.5 or more.
4. **Asleep in the hour before:** 20 or more minutes asleep in the hour before the decision hour.
5. **Seen:** the device observed, or any sleep recorded, in the three hours before the decision.
6. **The sign:** 1 ("signs of daytime sleep") if asleep in the hour before **or** a recent daytime pattern; 0 ("no sign")
   if neither, the recent share is known, and the device was seen; otherwise unknown.

- **Timing:** before the decision. The previous seven decisions' 24-hour windows end at or before the current decision
  when consecutive sends are 24 hours apart. Two edge cases: if two consecutive sends are less than 24 hours apart, the
  previous decision's fixed 24-hour window runs past the current decision by the difference (rare with 3 pm sends);
  and "asleep in the hour before" marks sleep in progress, which continues past the message. A "strict" variant using
  only windows that ended before the decision was explored ([Explored, not shown](#explored-not-shown)).
  [src: screen_mods.py, `daytime`; <scratch>/daytime.py, module docstring; <vault>/Results and Document
  Compilation/Daytime Sleep and Message Effects - Follow-up Checks.md, "Limits"]
- **Baseline compared with:** none; a yes/no state.
- **Split:** yes/no as is; unknown decisions are left out in 1b and form a "not recorded" group in figure 2.
- **Coverage, as documented:** the same definition (rebuilt in `<scratch>/daytime.py`) flags "either sign" on 3.3%
  (2024) and 4.1% (2025) of decisions and "neither" on 26% and 29%; the rest are unknown.
  [src: <vault>/Results and Document Compilation/Daytime Sleep and Message Effects - Follow-up Checks.md, "Method"]
- **Origin:** the rule is the audit's (`m27_followups.py`), carried over unchanged.
  [src: <audit>/Opus/MfnSleep-20261118/m27_followups.py, docstring and flag code]

### Last night's sleep

- **Definition:** `sleep_minutes_pre` / 60, in hours: minutes asleep on the participant's main device in the pre window
  (the previous grid day, ending at the decision). The engine keeps a window's sleep only if the window is 20 to 28
  hours long, has at least one hour with sleep, and has either 180 or more minutes asleep or the device worn for at
  least 67% of the 22:00–07:00 night. "Last night" is the presentation's label: the window also holds any daytime sleep
  in the 24 hours before the decision. [src: screen_mods.py, `build` (`pre_h`); causal/src/ihs_causal/data/features.py,
  device-view block (`sleep_minutes_{s}`); see [outcome windows](07-outcome-windows.md)]
- **Timing:** before the decision.
- **Split:** median split ("shorter", "longer"). [src: screen_fit.py, `FAMILIES["recent sleep"]`]
- **Status: In the presentation** (1b). **Built outside the repository** (the derived column lives in `screen_mods.py`).

### Last night's sleep against own usual

- **Definition:** (`sleep_minutes_pre` − `own_sleep`) / 60, in hours, where `own_sleep` is the participant's mean of
  `sleep_minutes_pre` over their decisions up to **and including** this one, once at least three values exist
  (`own_past_mean_min_days` = 3). Missing where the own mean is not yet available or last night's sleep is missing.
  [src: screen_mods.py, `build` (`def_h`); report/ihs_report/build/history.py, `add_own_past_mean`;
  report/config/analysis.yaml, `controls.own_past_mean_min_days`]
- **The "usual":** this running mean includes the current day-before value, needs only three values, and is the
  report's own-past-mean control. It differs from the "usual" of the previous-week and person families (earlier days
  only, at least seven); see [Code against notes](#code-against-notes).
- **Timing:** before the decision.
- **Split:** median split ("below usual", "above usual").
- **Coverage, as documented:** recorded on only about a quarter of decisions (stated together with mood before against
  usual). [src: <vault>/Results and Document Compilation/Moderators Together - Context and Baseline in One Model.md, "Method"]
- **Status: In the presentation** (1b and figure 2). **Built outside the repository.**

## Mood and steps before the decision

Four moderators in 1b's "Before the decision" family; the two "against own usual" ones are also in figure 2.
All are **In the presentation** and **Built outside the repository** (derived in `screen_mods.py` from engine columns).
[src: screen_mods.py, `build`; screen_fit.py, `FAMILIES["before the decision"]`; joint_fit.py, `MODS`]

| Moderator | Definition | Usual | Split labels |
|---|---|---|---|
| Mood before the decision (`mood_pre`) | `Mood_pre`: mean of the mood entries in the pre window (needs a window of 20–28 hours and at least one entry) | none | lower, higher |
| Mood before against own usual (`mood_dev`) | `Mood_pre` − `own_mood`, where the own mean is recorded | `own_mood`: mean of `Mood_pre` over the participant's decisions up to and including this one, at least three values | below usual, above usual |
| Steps before the decision (`steps_pre`) | `log_steps_pre`: log(1 + steps) in the pre window on the main device, kept when the device was observed for at least 10 hours; a total below one step counts as missing (decided 2026-11-20) | none | fewer, more |
| Steps before against own usual (`steps_dev`) | `log_steps_pre` − `own_steps` (log scale, so a ratio to the usual) | `own_steps`: as for mood, on log steps | below usual, above usual |

[src: causal/src/ihs_causal/data/features.py, device-view block (`log_steps_{s}`, `Mood_{s}`); report/ihs_report/build/history.py,
`zero_step_days_missing`, `add_own_past_mean`; report/ihs_report/build/tables.py, `analysis_table`;
report/config/analysis.yaml, `steps.zero_days_missing`]

- **Timing:** before the decision (the pre window ends at the decision; see [outcome windows](07-outcome-windows.md)).
- **Split:** median split.
- **Coverage, as documented:** mood before against own usual is recorded on only about a quarter of decisions.
  [src: <vault>/Results and Document Compilation/Moderators Together - Context and Baseline in One Model.md, "Method"]

## Previous week

Six moderators in 1b's "Previous week" family. All **In the presentation** and **Built outside the repository**.
[src: <vault>/Presentation Plots/pipeline/screen_mods.py, `history`, `MIN_VALUES`, `MIN_OWN`;
screen_fit.py, `FAMILIES["previous week"]`]

Built from each earlier decision's **post-window outcome**, one value per participant and calendar day:

- mood: `Mood_post` (points);
- steps: exp(`log_steps_post`) − 1, divided by 1,000 (thousands of steps a day, on the raw scale; the zero-step rule
  and the engine's 10-observed-hours rule apply);
- sleep: `sleep_minutes_post` / 60 (hours).

| Moderator | Definition | Split labels |
|---|---|---|
| Previous week's mood, steps, sleep (`mood7`, `steps7`, `sleep7`) | Mean over calendar days d−7 to d−1 (a 7-day window closed on the left, so the decision day is excluded), when at least three of those days have a value (`MIN_VALUES` = 3) | lower half, upper half |
| Previous week against own usual (`mood7_dev`, `steps7_dev`, `sleep7_dev`) | Previous week minus the participant's usual: the mean over **all earlier days**, available once at least seven earlier days have a value (`MIN_OWN` = 7) | below usual, above usual |

- **Timing:** before the decision. An earlier day's post window ends at or before the current decision under the
  engine's window rule. [src: causal/src/ihs_causal/data/windows.py, `next_decision_windows`]
- **Split:** median split.
- **Coverage, as documented:** last week's mood is recorded for 25–30% of decisions, steps 74–77%, sleep 30–34%.
  [src: <vault>/Results and Document Compilation/Cross-Domain Moderators of Message Effects.md, "Method"]

## Engagement and time in study

Three moderators, the same columns in the report and the presentation. **Status: Both** (report signal chapter;
presentation 1b "Engagement and time in study"; time in study also in figure 2).
[src: report/ihs_report/build/signal.py, `add_signal`, `MODERATORS`; report/ihs_report/analyses/engagement_moderation.py;
screen_fit.py, `FAMILIES["engagement"]`; joint_fit.py, `MODS`]

| Moderator | Definition | Report test and levels | Presentation split |
|---|---|---|---|
| Mood entries in the past week (`sg_eng7`) | Number of the previous seven calendar days (day numbers counted from the cohort's first decision date) on which the participant's decision had a mood outcome (`Mood_post` recorded). A day without a decision counts as no entry | Per entry; no entries against at least one | `pos`: none against at least one |
| Time in study (`sg_t30`) | Study day `t` / 30. `t` is the participant's day on the engine's daily grid, 0 at their first decision | Per 30 days; earlier and later half at the comparison's median | Median split ("earlier half", "later half") |
| First 30 days (`sg_early`) | 1 if `t` < 30, else 0 | Yes against no; levels "after day 30" and "first 30 days" | Yes/no |

[src: report/ihs_report/build/signal.py, `add_signal`; report/ihs_report/build/history.py, `add_person_day` (`h_dnum`);
causal/src/ihs_causal/data/windows.py, `next_decision_windows` (`t`); report/ihs_report/tables.py, `LEVEL_NAMES`]

- **Timing:** before the decision. Mood entries come from earlier decisions' post windows, which end at or before the
  current decision; study time is known in advance.
- **Collinearity:** study day `t` is already a control, so the report's time-in-study test (`sg_t30` = `t` / 30) has
  exactly collinear controls; since engine 0.2.2 the estimator drops the redundant direction. The module docstring
  speaks of two collinear study-time tests, but `sg_early` is not a linear function of `t`. The presentation's half
  indicator is not collinear with `t`. [src: report/ihs_report/analyses/engagement_moderation.py, docstring; report/README.md,
  "A fault in the engine, fixed in engine 0.2.2"]
- **Not a moderator:** `sg_half` (alternate weeks) is built here for the split-half consistency check only.
  [src: signal.py, `add_signal`]

## The person

### Usual mood, sleep and steps

- **Definition:** `mood_usual`, `steps_usual`, `sleep_usual`: the participant's mean of the post-window outcome over all
  earlier days (mood in points; steps in thousands a day, raw scale; sleep in hours), available once at least seven
  earlier days have a value (`MIN_OWN` = 7). [src: <vault>/Presentation Plots/pipeline/screen_mods.py, `history`]
- **Level:** labelled "the person" (1b) and "who" (figure 2), but it is a **running** mean, recomputed at each decision
  from earlier days only, so it changes within a person over the year and is missing early in the study.
- **Timing:** before the decision.
- **Split:** median split ("lower half", "upper half").
- **Coverage, as documented:** usual mood exists for about 64% of decisions.
  [src: <vault>/Results and Document Compilation/Cross-Domain Moderators of Message Effects.md, "Method"]
- **Status: In the presentation** (1b and figure 2). **Built outside the repository.**

### Baseline PHQ-9

- **Definition:** `PHQtot0`, the baseline PHQ-9 total, a participant trait merged by the engine.
  [src: causal/src/ihs_causal/data/features.py, `merge(traits)`; causal/src/ihs_causal/defaults.yaml]
- **Timing:** before the study (baseline survey; the exact survey timing was not re-checked here).
- **Split:** median split; median over the decisions of the cohort, period and outcome (so weighted by decisions, not
  by people).
- **Status: In the presentation** (1b and figure 2). In the report it is one of the engine's five controls, not a
  moderator. [src: report/config/analysis.yaml, `controls.engine`; screen_fit.py, `FAMILIES["person"]`; joint_fit.py, `MODS`]

### Other baseline traits

Engine trait columns, split in 1b only. **Status: In the presentation** (1b). [src: screen_fit.py, `FAMILIES["person"]`]

| Moderator | Column | Split |
|---|---|---|
| Baseline anxiety (GAD-7) | `GADtot0` | Median ("lower half", "upper half") |
| Baseline neuroticism | `Neu0_published` | Median |
| Depression history | `depr0` | Yes/no ("no history", "history") |

The daytime-sleep subgroup note says the published neuroticism score was unavailable in 2025. If so, 1b skips it for
2025 (a moderator with no values cannot be split) and its pooled row is the 2024 estimate; unverified on the current
files. [src: <vault>/Results and Document Compilation/Daytime Sleep Subgroup Moderation.md, "Estimation";
screen_fit.py, `fit_cohort` (`np.unique(...) < 2`), `combine`]

### Device

- **Definition:** `device_is_fitbit` = 1 when the participant's main device is a Fitbit, else 0. The main device is
  the instrument (Fitbit, Garmin, Apple) with the most observed hours summed over the post windows of **all** the
  participant's decisions; a participant with no observed hours has no main device and gets 0. So "other device"
  holds Garmin and Apple users and, for mood, participants with no wearable.
  [src: causal/src/ihs_causal/data/features.py, device-view block (`device == "combined"`, `device_is_{k}`)]
- **Level:** person, fixed for the year.
- **Timing:** **uses the whole study year**, including hours after the decision.
- **Split:** yes/no ("other device", "Fitbit").
- **Status: In the presentation** (1b and figure 2).

## Circadian misalignment

**Status: Both** (report physiology chapter; presentation 1b, 2024 only). The presentation uses the report's columns.
[src: report/ihs_report/build/circadian.py; report/ihs_report/analyses/circadian_moderation.py;
screen_mods.py, `build`; screen_fit.py, `FAMILIES["circadian"]`, `__main__`]

- **Source:** three files supplied for the 2024 cohort, `Daily Circadian Metrics/aish_<Fitbit|Garmin|HealthKit>_2024_results_cleaned.csv`,
  **used as supplied**: how they were made is not documented in this project. One row per participant and date with
  two estimates of the body clock's phase and the sleep midpoint. When a participant-date is in more than one file,
  the row fitted to the most data points is kept (none is, in the 2024 files).
  [src: report/ihs_report/inputs.py, `EXTRA_FILES`; circadian.py, module docstring, `load_daily`;
  report/README.md, "Still to do for replicability"; report/config/analysis.yaml, `circadian.cohorts`]
- **Clocks:** the heart-rate clock (CRPO in the files) is the phase of the daily rhythm fitted to heart rate and
  activity; the model clock (CRCO) is the phase of a model of the central clock updated with the heart-rate clock.
  [src: circadian.py, module docstring]

| Measure | Definition | Unit |
|---|---|---|
| Heart-rate clock against sleep midpoint (`crpo`) | `crpo_sleep_misalignment_abs`, capped at its 99th percentile over all participant-days | hours |
| Model clock against sleep midpoint (`crco`) | `crco_sleep_misalignment_abs`, capped likewise | hours |
| Two clocks against each other (`internal`) | `internal_misalignment_abs`, capped likewise; scaled by the model clock's uncertainty in the files, so not in hours | units of that uncertainty |
| Sleep midpoint away from own usual (`midoff`) | Absolute circular distance between the day's sleep midpoint and the participant's usual midpoint: the circular mean of all their midpoints over the **whole file** | hours |

Each measure is used twice: `cm_<measure>_d1`, the value for the date before the decision date; and `cm_<measure>_m7`,
the mean over that date and the six before it (dates d−7 to d−1 on a calendar grid), when at least `week_min_days` (3)
of them have a value. [src: circadian.py, `load_daily`, `add_circadian`, `MEASURES`;
report/config/analysis.yaml, `circadian.clip_quantile`, `circadian.week_min_days`]

- **Timing:** before the decision. A day's estimate is fitted to a two-day window that ends that day, so the day before
  the decision is the latest value that cannot include the message. Two parts use the whole year: the usual midpoint
  of `midoff` (the report states this as a limit) and the 99th-percentile caps.
  [src: circadian.py, module docstring; report/chapters/_physiology-moderation.qmd, "Limits"]
- **Split:** report, per hour (per unit for `internal`) with "less misaligned" and "more misaligned" halves at the
  comparison's median ("closer to usual", "further from usual" for `midoff`); 1b, median split ("less misaligned",
  "more misaligned"). [src: report/ihs_report/tables.py, `_CIRCADIAN`; screen_fit.py, `FAMILIES["circadian"]`]
- **Missing values:** each test uses decisions with that measure; the report shows the coverage.
  [src: report/chapters/_physiology-moderation.qmd, `tbl-circadian-coverage`]
- **Coverage, as documented:** 371 of 917 participants; a day-before value for 24% of all decisions, and among decisions
  with the outcome about 29% (steps), 44% (mood) and 65% (sleep).
  [src: <vault>/Results and Document Compilation/Circadian Misalignment and Heart Rate Variability as Moderators.md,
  "Data" and "All comparisons"]
- **Not a moderator:** the precision chapter's circadian control block uses more columns from the same files (phases and
  sleep times on a circle, rhythm level, size and persistence, signed misalignments, seven-row means), lagged one day
  and capped at the 1st and 99th percentiles. [src: report/ihs_report/build/blocks.py, `circadian_features`, `circadian`]

## Heart rate variability

**Status: Both** (report physiology chapter; presentation 1b, 2024 only). The presentation uses the report's columns.
[src: report/ihs_report/build/hrv.py; report/ihs_report/analyses/hrv_moderation.py; screen_mods.py, `build`;
screen_fit.py, `FAMILIES["heart-rate variability"]`]

### Building the daily table

`<cohort>HRVDaily.parquet`, built for 2024 only from the raw wearable exports when no supplied copy exists. One row per
participant, date and device type: `hrv_log` (mean of log values that day), `hrv_sd`, `n` (readings), `source`, and for
Fitbit `hf_log` and `lf_log`. [src: report/ihs_report/build/hrv_build.py, module docstring, `build`;
report/config/analysis.yaml, `hrv.cohorts`]

- **The 3 pm local decision assumption:** a reading belongs to the decision date whose 24 hours before the 3 pm decision
  contain it, taken as the date of the reading's local time plus `bucket_shift_hours` (9). A reading at 15:00 on day
  d−1 through 14:59 on day d belongs to date d. [src: hrv_build.py, module docstring, `fitbit_daily`, `healthkit_daily`;
  report/config/analysis.yaml, `hrv.bucket_shift_hours`]
- **Fitbit** (`Wearable/Fitbit/Intraday/Intraday HRV/`, a folder of files): intraday RMSSD during sleep, local
  timestamps. Repeated participant-timestamps dropped; RMSSD must be positive; high- and low-frequency power floored
  at 1 before the log. [src: hrv_build.py, `fitbit_daily`]
- **Apple Health** (`Wearable/HealthKit/Intraday/intraday HRV/`, one file): intraday SDNN. **The header is one column
  short**: rows carry nine fields under eight names, so the file is read by position: participant in field 2, the
  reading's start time in field 3 (local wall time = its first 19 characters), the value in field 5 (which sits under
  the header's date column). Values must be above 0 and below 400; repeated participant-start times dropped.
  [src: hrv_build.py, module docstring, `healthkit_daily`]
- **Garmin** (`Wearable/Garmin/Daily/garmin_hrvsummary_2024cohort_BLQ1Q2.csv`): one nightly average (`LASTNIGHTAVG`)
  per calendar date, with no shift; when a date has several rows the longest recording is kept.
  [src: hrv_build.py, `garmin_daily`]
- **Checks:** identical in every cell to the audit's table of November 22, 2026; not independently reviewed.
  [src: report/README.md, "Further input files", "Still to do for replicability"]

### The three measures

The three device types measure different things (Apple Watch SDNN, Fitbit RMSSD during sleep, Garmin nightly
average), so each participant keeps one device type, the one with the most days in the file, and is compared only with
their own past or with others on the same device type. [src: report/ihs_report/build/hrv.py, module docstring, `load_daily`]

| Measure | Definition |
|---|---|
| HRV before the decision against own usual (`hv_today`) | (that date's `hrv_log` − the participant's mean over their earlier dates) / the SD over those earlier dates, once at least `usual_min_days` (5) earlier dates exist; SD floored at `sd_floor` (0.05); result capped at ±`z_cap` (4) |
| HRV over the previous 7 days against own usual (`hv_week`) | The same, for the mean of `hrv_log` over the seven dates before the decision date (d−7 to d−1, calendar grid, at least `week_min_days` = 3 with a value) |
| Usual HRV against others on the same device type (`hv_usual`) | (the participant's mean over earlier dates − the mean of that quantity over all participant-days on the same device type) / ln 2, in doublings: 1 is a usual level twice that of others |

[src: hrv.py, `load_daily`, `add_hrv`, `MEASURES`; report/config/analysis.yaml, `hrv`]

- **Timing:** before the decision, given a 3 pm decision. All three are looked up on the decision date's row, so they
  exist only on dates with that day's own value (`hv_week` too, although its week could have values).
  [src: hrv.py, `load_daily` (week merged onto daily rows), `add_hrv`]
- **Whole-year parts:** the choice of device type (most days over the whole file) and the device-type mean that centres
  `hv_usual` (all participant-days) use the whole year; the participant's own part of `hv_usual` uses earlier dates only.
- **Level:** `hv_today` and `hv_week` are moment moderators; `hv_usual` is a running person moderator.
- **Split:** report, per own SD (`hv_today`, `hv_week`) or per doubling (`hv_usual`), with lower and higher halves at
  the comparison's median; 1b, median split. [src: report/ihs_report/tables.py, `MEASURE_UNIT`, `LEVEL_NAMES`]
- **Coverage, as documented:** 714 participants (Apple 525, Fitbit 259, Garmin 37 as listed by device); 47% of all
  decisions, falling from 63% in July to 34% in June; among decisions with the outcome 64% (steps), 74% (mood), 76%
  (sleep). [src: <vault>/Results and Document Compilation/Circadian Misalignment and Heart Rate Variability as
  Moderators.md, "Data" and "All comparisons"]

## Message statistic tiers

**Status: In the presentation** (1b "Message statistic tier"; the all-nine restriction on the "data" comparison in
figures 1, 1b and 2). **Built outside the repository** throughout: the participant-level tier tables were built by
`<scratch>/tier_build_2025.py` and `<scratch>/tier_parse_2024.py` into `<audit>/Opus/Tiers-20261124/`, and
`<vault>/Presentation Plots/pipeline/tier_feats.py` turns them into moderator columns. The scratch scripts live in a
temporary folder and must be moved into the repository.

### What a tier is

Every message (data or no-data version) has four variants, chosen from one of the domain's nine statistics: the average,
maximum and minimum over 7 days, 30 days and since the phase began (`Metric_<Domain>_<Avg|Max|Min>_<7Days|30Days|PhaseBegin>`).
The tier is **neutral** when the statistic is missing or 0, **low** below the message list's cut point L ("Trigger
Low"), **high** above H ("Trigger High"), **medium** in between. Data messages also insert the number.
[src: <vault>/Results and Document Compilation/Data Shown vs Not, by Statistic Tier.md, opening and "How the tiers were
rebuilt"; <scratch>/tier_build_2025.py, `tier_of`]

| Cohort | Boundary rule | Source of the statistic at the decision | Check against every sent message |
|---|---|---|---|
| 2025 | low if value < L, high if value ≥ H | The 2025 server's custom-field file for the decision day | Logged value equals the file on 100% of sends; recomputed tier equals the logged tier on 100% |
| 2024 | low if value ≤ L, high if value > H (chosen by agreement with the logged tiers) | The last update before 20:00 UTC on the decision date, from the 2024 participant-update log (statistic fields only) | Rebuilt tier equals the logged tier on 99.99% of sends |

[src: <scratch>/tier_build_2025.py, `tier_of` and validation block; <scratch>/tier_effects.py, `tier`, `feats_2024`;
<vault>/Presentation Plots/pipeline/tier_feats.py, `tier`, `feats`; <vault>/Results and Document Compilation/Data Shown
vs Not, by Statistic Tier.md, "How the tiers were rebuilt"]

### How the tiers were rebuilt

- **2025** (`<scratch>/tier_build_2025.py`): reads the statistic columns of the server's daily custom-field files (one
  row per participant and file day; the last row kept for a repeated participant-day), validates them against the
  logged metric value and tier of every sent message (the tier is the last digit of the notification identifier), and
  writes per participant-day and domain: `<domain>_n_avail` (how many of the nine statistics parse to a non-zero
  number), and the tier and value of the 7-day, 30-day and phase averages. Values are parsed as the server parsed them
  (`pd.to_numeric`), so a value written with a thousands comma is unreadable. Output:
  `<audit>/Opus/Tiers-20261124/tiers_2025.parquet`. [src: <scratch>/tier_build_2025.py]
- **2024** (`<scratch>/tier_parse_2024.py`): reads only the `Metric_<Mood|Sleep|Steps>_<Avg|Max|Min>_<window>` pairs from
  the 2024 participant-update log, which also holds names and emails that are never read into the output. Keeps the
  participant, timestamp (parsed as UTC), field, the value with commas removed, and `num_leading`, the digits before
  any comma (what the 2024 server read). Output: `<audit>/Opus/Tiers-20261124/metric_updates_2024.parquet`.
  [src: <scratch>/tier_parse_2024.py]
- **Moderator columns** (`tier_feats.py`): 2025, the custom-field row of the participant and decision date; 2024, for
  each of the nine fields the last `num_leading` update at or before 20:00 UTC on the decision date. Then per domain
  `<domain>_n_avail` (0–9, non-zero values) and `<domain>_tier7`, the tier of `Metric_<Domain>_Avg_7Days` by the
  cohort's rule. The 2024 log gives every decision a value, so 2024 `n_avail` is never missing; a 2025 decision with no
  custom-field row for that day has no value. [src: tier_feats.py, `feats`]
- **Cut points:** `tier_feats.py` takes L and H from the 2025 server's message list (`agents/Master/MessageList.csv` in
  the 2025 server folder) for both cohorts; `tier_effects.py` takes the 2024 cohort's from the 2024 message list
  workbook. The tier note says the cut points are the same in both cohorts (unverified here).
  [src: tier_feats.py, `CUTS`; <scratch>/tier_effects.py, `cuts`; Data Shown vs Not note, "How the tiers were rebuilt"]

### The thousands-comma faults

Step statistics are stored as text with a thousands comma ("12,345"). [src: memory note
project-ihs-message-tier-comma-faults (2026-11-25); <scratch>/tier_parse_2024.py, `has_comma`]

- **2025:** the server's `pd.to_numeric` could not read a value with a comma, so the statistic counted as missing and
  the message fell to the neutral variant. As documented, most step values had a comma (about 90%), 97% of steps
  messages were neutral, none were "high", and steps data messages never showed a number. In the tier columns, a 2025
  steps statistic is readable only when it was under 1,000; no 2025 steps decision has all nine readable, so the
  2025 steps "data" comparison is not estimable and its pooled row is 2024's.
- **2024:** the server read the digits before the comma ("12,345" as 12), so most steps messages were framed "low" (72%
  as documented) and none "high", while the number displayed in data messages was right. In the tier columns these
  values count as readable and carry the mis-read tier, which is the tier participants actually received.

[src: <vault>/Results and Document Compilation/Data Shown vs Not, by Statistic Tier.md, "Verdict", "Sent messages by
tier", "Own-domain data vs no data"; memory note project-ihs-message-tier-comma-faults (2026-11-25);
<vault>/Presentation Plots/build_data.py, module docstring]

### The three tier moderators

All are measured on the outcome's own domain (`{o}` in the code is the outcome) and are median-free.
[src: <vault>/Presentation Plots/pipeline/screen_fit.py, `FAMILIES["message tier"]`, `indicator`]

| Moderator | Column | Upper level | Lower level | Unknown (left out) |
|---|---|---|---|---|
| 7-day average tier: low (`tier_low`) | `<o>_tier7` | low | medium or high | neutral, or no value |
| 7-day average tier: high (`tier_high`) | `<o>_tier7` | high | low or medium | neutral, or no value |
| Statistics the server could read (`avail`) | `<o>_n_avail` | all nine | fewer than nine | no value |

- **Timing:** before the decision for 2025 (the values the server used, checked on every send). For 2024 the reference
  is 20:00 UTC on the decision date, which is 16:00 for a participant on Eastern daylight time, one hour after a 3 pm
  local decision; an update in that hour would be post-decision. The 99.99% agreement with the logged tiers suggests
  this is rare, but it is not ruled out. [src: tier_feats.py, `feats` (`Timedelta(hours=20)`)]
- **Status: In the presentation** (1b). **Built outside the repository.**

### Data shown vs not

The presentation's "data shown vs not" comparison (own-domain data against no-data versions of Cognitive Strategies,
Behavioral Strategies, Motivational Interviewing and mindfulness; Distanced Self-Talk has no data version) is restricted
to decisions where all nine own-domain statistics were readable (`<o>_n_avail` ≥ 9), so that every data message could
show a number. This restriction is used in figure 1 (from `<scratch>/tier_effects.py`, group "all 9"), figure 1b,
the cumulative curves and figure 2 (from `tier_feats.py`). It is a subgroup restriction, not a moderator.
[src: <vault>/Presentation Plots/build_data.py, module docstring and `t` filter; screen_fit.py, `own_data_vs_nodata`,
`readable`; cumulative_fit.py, `readable`; joint_fit.py, `readable`; <scratch>/tier_effects.py, `groups`]

## Daytime sleep and warmth together

**Status: In the presentation** (1b, "Daytime sleep and warmth"). **Built outside the repository.**
[src: <vault>/Presentation Plots/pipeline/screen_fit.py, `JOINT`, `quarters`, `fit_cohort`; plots.html, `JOINT_GROUPS`]

- **The two splits:** daytime sleep signs, yes/no as is ("no sign", "daytime sleep"); warmth against own monthly usual
  (`wm_anom5`), median split over all decisions of that cohort and period with the outcome and the measure recorded,
  as in 1b ("cooler than usual",
  "warmer than usual", meaning below or above the median departure).
- **The model:** one WCLS fit per comparison with the standard controls plus the daytime indicator, the warmth
  indicator and their product, each as a control and a moderator (centred by the engine). Decisions need both
  recorded.
- **Rows shown,** each a contrast of two of the four groups, with standard errors from the influence values:

| Key | Label | Lower level | Upper level |
|---|---|---|---|
| `dw_day_warm` | Daytime sleep vs no sign, warmer days | no sign, warmer | daytime sleep, warmer |
| `dw_day_cool` | Daytime sleep vs no sign, cooler days | no sign, cooler | daytime sleep, cooler |
| `dw_warm_day` | Warmer vs cooler than usual, daytime sleep | daytime sleep, cooler | daytime sleep, warmer |
| `dw_warm_none` | Warmer vs cooler than usual, no sign | no sign, cooler | no sign, warmer |
| `dw_inter` | Does warmth change the daytime-sleep gap? | the gap on cooler days | the gap on warmer days |

- **Minimum sizes:** each of the four groups needs at least `MIN_GROUP` (30) messages and 30 reference decisions per
  compared arm; a comparison where an indicator is constant on the fitted rows is skipped.
- **Timing:** the daytime sign is before the decision; warmth spans it.

## The joint model's eleven moderators

**Status: In the presentation** (figure 2). **Built outside the repository.**
[src: <vault>/Presentation Plots/pipeline/joint_fit.py, `MODS`, `splits`, `fit`, `fit_cohort`, `finish`]

| Group | Moderator | Column | Kind |
|---|---|---|---|
| When | Day's high against own monthly usual | `wm_anom5` | median split |
| When | Last night's sleep against own usual | `def_h` | median split |
| When | Daytime sleep | `daytime` | yes/no |
| When | Mood before the decision against own usual | `mood_dev` | median split |
| When | Steps before the decision against own usual | `steps_dev` | median split |
| When | Time in study | `sg_t30` | median split |
| Who | Usual mood | `mood_usual` | median split |
| Who | Usual sleep | `sleep_usual` | median split |
| Who | Usual steps | `steps_usual` | median split |
| Who | Baseline depression (PHQ-9) | `PHQtot0` | median split |
| Who | Device | `device_is_fitbit` | yes/no |

- **Splits:** those of figure 1b.
- **Missing values:** the "not recorded" groups described in [Missing values](#missing-values); every analysed decision
  is used. The page shows each moderator's recorded share.
- **Together and alone:** "together" is a moderator's upper-half coefficient in one model with all eleven upper-half
  indicators and every not-recorded indicator, plus the standard controls; "alone" is the same moderator in a model
  with only its own upper-half and not-recorded indicators, on the same decisions.
- **"All eleven together":** a Wald test that the eleven upper-half coefficients are all zero, per cohort; pooled across
  cohorts with inverse-variance matrices over the terms both cohorts have.
- **Minimum sizes:** only `min_arm_rows` (50); no `MIN_HALF` or `MIN_GROUP`.
- **Timing:** nine are known before the decision; warmth spans it, and the device uses the whole year. "Usual" moderators are
  running means, not fixed traits, despite the "who" label.

## Explored, not shown

Each of these was computed but is in neither the report nor the presentation. All are **Built outside the repository**.

- **Other daytime-sleep definitions** (`<scratch>/daytime.py`): asleep in the hour before alone; the recent pattern
  alone; a "strict" pattern over windows d−2 to d−8 (so every episode used had ended before the decision), without the
  asleep-before sign. [src: <scratch>/daytime.py, `flags`]
- **Earlier daytime-sleep subgroup screen:** moderation within daytime-sleep subgroups, scaled per SD of each
  moderator, with 2025 fitted on selected-agent probability vectors and a 2% floor, which predates the decision to use
  released probabilities (2026-11-22). [src: <vault>/Results and Document Compilation/Daytime Sleep Subgroup Moderation.md,
  "Estimation"; report/config/analysis.yaml, `probability.2025`]
- **Per-unit temperature moderation over three periods** (`<scratch>/usual_set_temperature.py`): the report's
  `fit_cohort` with the day's high and warmth against own usual, three periods, `min_arm_rows` 50 and the engine's
  `data_vs_nodata` comparison added. Only its overall rows reach figure 1; its moderation rows are not shown.
  [src: <scratch>/usual_set_temperature.py; <vault>/Presentation Plots/build_data.py, `u` filter]
- **Tier groups** (`<scratch>/tier_effects.py`): effects within none, one to eight, or all nine statistics readable,
  and within each 7-day tier (neutral, low, medium, high). Only the "all 9" group reaches the presentation.
  [src: <scratch>/tier_effects.py, `groups`; build_data.py]
- **Cross-domain per-unit moderators** (scratch scripts run on 2026-11-24, not read for this note): last week's,
  usual and 24-hour-before mood, steps and sleep as per-unit moderators, and by fifths. The previous-week definitions
  match screen_mods; the "usual" there is described as at least seven earlier days.
  [src: <vault>/Results and Document Compilation/Cross-Domain Moderators of Message Effects.md, "Method"]
- **Control blocks, not moderators:** weather (including log snowfall capped at 600 mm), the app weather feed,
  circadian, HRV, wear, time of day, sleep timing, heart rate, quarterly survey, baseline traits and holidays enter the
  report's precision chapter as controls only. [src: report/ihs_report/build/blocks.py, module docstring and `BLOCKS`]

## Built outside the repository

| Piece | What it does | Where |
|---|---|---|
| Presentation pipeline | Builds the moderator cache, fits figures 1b and 2 and the cumulative curves, writes the page's data | `<vault>/Presentation Plots/pipeline/screen_mods.py`, `screen_fit.py`, `joint_fit.py`, `cumulative_fit.py`, `tier_feats.py`; `<vault>/Presentation Plots/build_data.py` |
| Moderator cache | One participant-level table per cohort with every moderator; per-family fits | `<audit>/Opus/ModScreen-20261124/` (written by `screen_mods.py` and `screen_fit.py`) |
| Daytime-sleep inputs | Analysis rows and hourly profiles from November 18, 2026 | `<audit>/Opus/MfnSleep-20261118/cache/`, made by `<audit>/Opus/MfnSleep-20261118/m01_build_tables.py` |
| Tier tables | Participant-day tiers (2025) and statistic updates (2024) | `<audit>/Opus/Tiers-20261124/`, made by `<scratch>/tier_build_2025.py` and `<scratch>/tier_parse_2024.py` |
| Figure 1 sources | Overall usual-set effects; the all-nine "data" row | `<scratch>/usual_set_temperature.py`, `<scratch>/tier_effects.py` |
| Tier cut points | L and H per statistic | The 2025 server's `agents/Master/MessageList.csv` (read by `tier_feats.py`) |

Things to fix when these move into the repository:

- The four `<scratch>` scripts sit in a temporary session folder and must be moved into the repository before it is
  cleared.
- `usual_set_temperature.py` and `tier_effects.py` name the report folder by a fixed path on one machine (already its
  current place at the repository root); `tier_effects.py` also reads the raw 2024 message list and notification log
  by fixed paths.
- The pipeline and scratch scripts name fixed locations on one machine (the report folder, the audit cache folders, the 2025
  server's message list, the raw 2024 and 2025 server exports); these need to become configured paths like the
  report's `config/inputs.yaml`.
- The daytime-sleep caches are not rebuilt when the study files change; the moderator cache is checked for row
  alignment but not for content.

[src: screen_mods.py, `REPORT`, `CACHE`, `DAYTIME`; screen_fit.py, `CACHE`; tier_feats.py, `WORK`, `_ml`;
<scratch>/usual_set_temperature.py, `REPORT`; <scratch>/tier_effects.py, `REPORT`, `ml24`;
<scratch>/tier_build_2025.py; <scratch>/tier_parse_2024.py, `SRC`]

## Code against notes

Code wins in each case.

1. **"All measured before the decision."** The screen and joint-model notes say every moderator is measured before the
   decision. The code's weather measures cover the decision date and the next date, and the device uses the whole
   year. The report and the weather note state the weather timing correctly. [src: <vault>/Results and Document
   Compilation/Usual-Set Moderator Screen.md, "Method"; Moderators Together - Context and Baseline in One Model.md,
   "Method"; report/ihs_report/build/weather.py, `add_weather`; causal/src/ihs_causal/data/features.py, device block]
2. **Minimum sends per level.** The report README says weather and other levels need 200 sends (`min_arm_rows`); the
   config sets 50, lowered on 2026-11-24. `<scratch>/usual_set_temperature.py` also says "the report uses 200".
   [src: report/README.md, "What is in the report"; report/config/analysis.yaml, `min_arm_rows`]
3. **Where the median is taken.** The report's weather chapter says days are split "at each cohort's median daily
   high". The code takes the median per cohort, comparison and compared arm. The presentation takes it per cohort,
   period and outcome over all decisions with the outcome. [src: report/chapters/_weather-moderation.qmd;
   report/ihs_report/moderation.py, `_medians`; screen_fit.py, `indicator`]
4. **"Alone" in figure 2 against figure 1b.** The joint note says the alone fits give the same answers as 1b, which uses
   recorded decisions only. In code they differ in two ways: alone keeps unrecorded decisions in a not-recorded group,
   and it applies no `MIN_HALF`. The note reports the agreement as close, not exact. [src: Moderators Together note,
   "Method"; joint_fit.py, `splits`, `fit`; screen_fit.py, `halves`]
5. **Two "usuals".** The cross-domain note defines "usual" as the mean of all earlier days, at least seven; that holds for
   the previous-week and person families (`screen_mods.history`). The "against own usual" moderators for last night's
   sleep, mood before and steps before use the report's own past mean instead: at least three values, including the
   current day-before value. [src: Cross-Domain Moderators note, "Method"; screen_mods.py, `history`, `build`;
   report/ihs_report/build/history.py, `add_own_past_mean`]
6. **Tier rules "the same as tier_effects.py".** `tier_feats.py` says so, but takes 2024 cut points from the 2025
   server's message list where `tier_effects.py` uses the 2024 list. They agree only if the lists agree, which the tier
   note asserts. [src: tier_feats.py, docstring and `CUTS`; <scratch>/tier_effects.py, `cuts`]
7. **"Before the 3 pm decision."** The daytime follow-up note says the asleep-before sign is the hour before the 3 pm
   decision; the code uses the hour before the decision hour, whatever it is. The same for 99% of decisions.
   [src: Daytime Sleep and Message Effects - Follow-up Checks.md, "Method"; screen_mods.py, `daytime`]

## Measured at or after the decision

| Moderator | What is after the decision | Where it is used |
|---|---|---|
| Day's high, warmth against own usual, rain, snow, precipitation amount | The decision date's afternoon and evening and the whole next date; for warmth, the monthly usual uses the whole month | Report; 1b; joint family; figure 2 (warmth). Exogenous: a message cannot change the weather |
| Device | Main device chosen from observed hours over the whole year | 1b; figure 2 |
| Sleep midpoint away from own usual | Usual midpoint over the whole file | Report; 1b |
| Circadian caps | 99th percentiles over all participant-days | Report; 1b |
| HRV device type and `hv_usual` centring | Device type with the most days over the whole file; device-type mean over all participant-days | Report; 1b |
| HRV, decisions not at 3 pm | The 24-hour bucket assumes a 3 pm decision; for an earlier decision, readings up to 3 pm can follow it (about 1% of decisions are not at 15:00) | Report; 1b |
| 2024 statistic tiers | Reference 20:00 UTC can be up to an hour after a 3 pm local decision (Eastern daylight time) | 1b; "data" restriction |
| Daytime sleep signs | Asleep in the hour before marks sleep in progress; the previous decision's fixed 24-hour window can overrun the current decision when sends are under 24 hours apart | 1b; joint family; figure 2 |

## Unverified

- The gridded values' one-day shift (whether nClimGrid-Daily labels a day by the morning that ends it), and the
  morning-observer shift in general; both flagged for review in the README.
- Whether the app weather feed is a forecast or an observation, and its precipitation units (the 0.05 threshold).
- What Garmin's `CALENDARDATE` refers to (assumed: the night ending that morning, so before 3 pm).
- The Apple Health field positions beyond what the builder states; the local-time reading of the first 19 characters.
- How the circadian files define a date and the two-day fitting window (files used as supplied).
- That the 2024 participant-update timestamps are in UTC (the parser assumes so).
- That the tier cut points are the same in both cohorts (stated in the tier note).
- Whether baseline neuroticism is missing for all of 2025 in the current files.
- The exact timing of the baseline surveys.
- The coverage figures quoted from results notes were not recomputed for this note.

## Sources

Repository:

- `report/README.md`: "Further input files", "Where things live", "A fault in the engine", "What is in the report",
  "Still to do for replicability".
- `report/config/analysis.yaml`: `controls`, `min_arm_rows`, `weather_build`, `weather`, `circadian`, `hrv`,
  `weather_feed`, `steps`, `probability`.
- `report/ihs_report/build/weather_build.py`, `weather.py`, `hrv_build.py`, `hrv.py`, `circadian.py`, `signal.py`,
  `history.py`, `tables.py`, `profiles.py` (hour-by-hour features, controls only), `blocks.py`.
- `report/ihs_report/moderation.py`, `inputs.py`, `controls.py`, `estimate.py`, `tables.py`.
- `report/ihs_report/analyses/weather_moderation.py`, `weather_moderation_long.py`, `circadian_moderation.py`,
  `hrv_moderation.py`, `engagement_moderation.py`.
- `report/chapters/_weather-moderation.qmd`, `_physiology-moderation.qmd`, `_signal.qmd`, `_precision.qmd`.
- `causal/src/ihs_causal/design/contrasts.py` (`_frame`), `causal/src/ihs_causal/data/features.py` (device view,
  `covariate_matrix`), `causal/src/ihs_causal/data/windows.py`, `causal/src/ihs_causal/defaults.yaml`.

Outside the repository:

- `<vault>/Presentation Plots/pipeline/screen_mods.py`, `screen_fit.py`, `tier_feats.py`, `joint_fit.py`,
  `cumulative_fit.py`; `<vault>/Presentation Plots/build_data.py`; `<vault>/Presentation Plots/plots.html` (page code
  only, not its data block).
- `<audit>/Opus/MfnSleep-20261118/m01_build_tables.py`, `mfnlib.py`, `m27_followups.py` (scripts only).
- `<scratch>/tier_build_2025.py`, `tier_parse_2024.py`, `tier_effects.py`, `usual_set_temperature.py`, `daytime.py`
  (temporary folder; to be moved into the repository).
- Results notes in `<vault>/Results and Document Compilation/`, for definitions and documented coverage only:
  `Usual-Set Moderator Screen.md`, `Moderators Together - Context and Baseline in One Model.md`, `Data Shown vs Not, by
  Statistic Tier.md`, `Weather as a Control and Moderator of Message Effects.md`, `Daytime Sleep and Message Effects -
  Follow-up Checks.md`, `Daytime Sleep Subgroup Moderation.md`, `Circadian Misalignment and Heart Rate Variability as
  Moderators.md`, `Cross-Domain Moderators of Message Effects.md`.
- Memory notes (dated background): project-ihs-message-tier-comma-faults (2026-11-25),
  feedback-moderator-plots-include-main-comparisons (2026-11-24).
