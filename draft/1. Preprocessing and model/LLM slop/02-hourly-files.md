# The hourly files: dfHourly2024.csv and dfHourly2025.csv

**Summary.** Each cohort has one hourly CSV with exactly 25 columns: a participant, a UTC hour, a local clock label, steps and heart-rate measures for four device channels (Fitbit, Garmin, Apple Health phone, Apple Health watch), a mood score, and sleep minutes for five channels. Device channels are kept separate; the files contain no combined or "best device" column and no decisions or probabilities. Current results use the dated copies in `<shared>/Hourly_MoodCorrected_20261117/` (2024 SHA-256 prefix `c16bd124c02d`, 2025 prefix `2df0f3e1131d`), which are newer than the two root files in `<shared>`. Both copies hold one row per participant and known UTC hour, keep rows with unknown UTC separately, and leave unresolved or contradictory values blank rather than guessing. This note gives the schema, then each stream and device as it is built in those files, with the status of every rule, the missing-value conventions, validation, and a version history. Clock reconstruction, the November audit corrections and mood timing are covered in [clocks](03-clocks-and-time-zones.md), [audit corrections](04-audit-corrections.md) and [mood timing](05-mood-timing.md).

## Contents

- [Which files current results use](#which-files-current-results-use)
- [Status labels and placeholders](#status-labels-and-placeholders)
- [Row unit, keys and calendar](#row-unit-keys-and-calendar)
- [Column dictionary](#column-dictionary)
- [Time stamps in the files](#time-stamps-in-the-files)
- [How each file was built](#how-each-file-was-built)
- [Steps](#steps)
- [Heart rate](#heart-rate)
- [Resting heart rate](#resting-heart-rate)
- [Sleep: rules shared by all devices](#sleep-rules-shared-by-all-devices)
- [Fitbit sleep](#fitbit-sleep)
- [Garmin sleep](#garmin-sleep)
- [Apple Health sleep](#apple-health-sleep)
- [Mood](#mood)
- [Priority between devices and between apps](#priority-between-devices-and-between-apps)
- [Deduplication summary](#deduplication-summary)
- [Missing values and zeros](#missing-values-and-zeros)
- [Why hours are missing](#why-hours-are-missing)
- [Validation](#validation)
- [How the analysis engine reads the files](#how-the-analysis-engine-reads-the-files)
- [Version history](#version-history)
- [2024 coverage by month](#2024-coverage-by-month)
- [Open items](#open-items)
- [Sources consulted](#sources-consulted)

## Which files current results use

| Cohort | File | Rows | Participants | SHA-256 | Base |
|---|---|---:|---:|---|---|
| 2024 | `<shared>/Hourly_MoodCorrected_20261117/dfHourly2024.csv` | 7,376,544 | 931 | `c16bd124c02d42a7366328a812776e47b4b4520dd436178c8b0463cf3ba8bf98` | Stage C 2024 rebuild of November 17 (`a158a0a9…`) |
| 2025 | `<shared>/Hourly_MoodCorrected_20261117/dfHourly2025.csv` | 8,564,451 | 928 | `2df0f3e1131d9e6406abf6e38facfe0e8489f1288d02b6492048bf72396f8fb0` | Coordinated 2025 rebuild published November 17 (`84555a10…`) |

[src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md` § "Version identity"; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json` (`rows`, `participants`); `<vault>/Data Preprocessing/07 Current Files and Version Register.md` § "Which files to use"]

The engine's per-machine paths file overrides both cohorts' hourly input to these two files; the committed template shows the override, and the data notes shown with results are keyed to the hash prefixes `c16bd124c02d` and `2df0f3e1131d`. Every result records the SHA-256 of its inputs. [src: `causal/config/paths.example.yaml` (`files:` block); `causal/config/data_notes.yaml`]

**The root files are older.** `<shared>/dfHourly2024.csv` is still the November 15 full-year file (`67d15a8a…`, 7,462,876 rows) and `<shared>/dfHourly2025.csv` is the November 17 coordinated rebuild before the mood fix (`84555a10…`). Anything computed from the root files predates the current inputs. [src: `<vault>/Data Preprocessing/07 Current Files and Version Register.md` § "Which files to use"; `<shared>/README.md` § "Hourly files for mood analyses — November 17, 2026"]

**Review status.** Both dated files were switched into the engine at Drew's request on November 17, before their independent review. I found no record of that review being completed on the coordination board through November 23. The 2024 Stage C base was itself awaiting review; the 2025 base was independently accepted at 16:58 ET on November 17. [src: `<vault>/Audit Message Board.md` (posts of 2026-11-17 21:35, 22:16 and 23:03); `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "File identity and row contract"]

## Status labels and placeholders

Every rule below carries one status:

- **Applied**: in the files current results use (the two files above).
- **Staged, not applied**: built and stored as a candidate, not in those files.
- **Proposed**: described or approved as a rule, not built into those files.
- **Superseded**: used in an earlier release, replaced in the current files.

Where a rule is Applied in one cohort and not the other, or only in part of a cohort's date range, the text says so. Placeholders `<shared>`, `<vault>`, `<preprocessing-repo>`, `<raw2024>`, `<server2025>` are defined in [the raw sources note](01-raw-sources.md#how-to-read-this-note). The engine is cited as `causal/...`.

## Row unit, keys and calendar

**One row per participant and known UTC hour.** In both current files every known UTC hour appears once per participant. Rows whose UTC time could not be established are kept as separate rows with a blank `time_utc`. **Applied** (2025 since November 17 16:56; 2024 since Stage C). [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "File identity and row contract"; `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` § "Checks and exceptions"; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json` (`duplicate_known_utc_keys`: 0)]

| | 2024 (Stage C base) | 2025 (November 17 base) |
|---|---:|---:|
| Rows with blank `time_utc` | 124,883 | 7,201 |
| Known UTC hours with blank `time_local` | 57,433 | 55,188 |
| Fractional UTC (minutes not zero) | 0 | 0 (integer UTC hours only) |

[src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`shape`); `<vault>/Data Preprocessing/Attachments/Jack_Hourly_Manifest_20261117.json` (`shape`)]

The mood correction then supplied local labels on some of these hours (2024: 2 supplied, 127 corrected; 2025: 763 supplied, 526 corrected) and added 96 rows (2024) and 17 rows (2025). [src: `<shared>/audit/CollaborativeAudit/Codex/MoodTiming20261117/build.json`]

**Superseded key.** Releases from September 30 to November 15 (2024) and to November 13 (2025) used `(participant_id, time_utc, time_local)` as the key and kept several rows with different local labels at one UTC hour (89,984 such participant/UTC groups in 2024 and 31,354 in 2025 on November 13). Code that counted rows per window could overcount; the UTC consolidation removed this. **Superseded.** [src: `<shared>/README.md` § "Calendar and timestamps"; `<vault>/Data Preprocessing/08 Preprocessing Audit 2024 and 2025.md` § "Coverage and clocks"; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "File identity and row contract"]

**Calendar.** Each participant has rows for every hour from the first through the last date on which any wearable, sleep or mood record exists, including whole days with no observations. Known nonexistent daylight-saving hours are omitted. This rule was introduced on September 30 and carried through every later release; empty hours have blank measurement cells and `Mood = 0`. Hours outside a participant's first-to-last span have no row. **Applied.** [src: `<shared>/README.md` § "Calendar and timestamps"; `<shared>/audit/HourlyMoodPublicationChecks.json` (`calendar_rule`)]

Some rows exist only to carry a daily resting heart rate: 3,072 hours on 372 participant-days in 2024 (added in Stage C) and 3,168 rows from 132 watch days of 10 participants in 2025. They imply no wear. **Applied.** [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`RHR_only_grid`); `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Sources and reviewed dispositions"]

**Rows are not sorted** in a guaranteed order; sort by participant and UTC hour. Import `participant_id` as text. [src: `<shared>/README.md` § "Calendar and timestamps"]

**Excluded accounts (2024).** All 56 app accounts whose study ID is the literal `NA` marker are excluded. **Applied** since September 30. [src: `<shared>/README.md` § "Accounts excluded from the current analysis"]

## Column dictionary

Both files have these 25 columns in this order. Blank means missing. Device columns are never summed or substituted for each other in the file.

| # | Column | Unit | Meaning | 2024 notes | 2025 notes |
|---:|---|---|---|---|---|
| 1 | `participant_id` | text | Pseudonymous study ID | 931 people | 928 people |
| 2 | `time_utc` | timestamp | Start of the UTC hour; blank if unresolved | 124,883 blank (base) | 7,201 blank |
| 3 | `time_local` | timestamp | Start of the same hour on the participant's assigned local clock; blank if unresolved | Labels chosen by evidence (see [Time stamps](#time-stamps-in-the-files)) | Day clock from approved tiers where supported |
| 4 | `Fitbit_steps` | steps | Steps in the hour | Positive-only source: no recorded zeros in July–December 2024 (as of November 13) | Nightly source positive-only; API days have zero grids |
| 5 | `Fitbit_hr_avg` | bpm | Mean of valid samples in the hour | | |
| 6 | `Fitbit_hr_max` | bpm | Maximum valid sample in the hour | | |
| 7 | `Fitbit_RHR` | bpm | Daily resting HR, repeated on every hour of that local date | | |
| 8 | `Garmin_steps` | steps | Steps in the hour from 15-minute epochs | Explicit zeros | Full 3,600 s coverage required |
| 9 | `Garmin_hr_avg` | bpm | Mean | | |
| 10 | `Garmin_hr_max` | bpm | Maximum | | |
| 11 | `Garmin_RHR` | bpm | Daily, repeated | Final/longest daily summary | Final/longest daily summary |
| 12 | `HealthkitPhone_steps` | steps (can be fractional) | Apple Health records classed as phone, including app-written records that survive the app rules | Server rebuild (hours from 2024-03-31) | Server rebuild from March 1, 2025; older build before |
| 13 | `HealthkitPhone_hr_avg` | bpm | Mean | | |
| 14 | `HealthkitPhone_hr_max` | bpm | Maximum | | |
| 15 | `HealthkitPhone_RHR` | bpm | Daily, repeated | Distinct-value mean | Distinct-value mean |
| 16 | `HealthkitWatch_steps` | steps (can be fractional) | Apple Watch records | | |
| 17 | `HealthkitWatch_hr_avg` | bpm | Mean | | |
| 18 | `HealthkitWatch_hr_max` | bpm | Maximum | | |
| 19 | `HealthkitWatch_RHR` | bpm | Daily, repeated | Last value of the day | Last value of the day |
| 20 | `Mood` | 1–10 | Latest mood response completed in that UTC hour; **0 = no response** | 104,314 positive hours | 87,252 positive hours |
| 21 | `Fitbit_sleep_minutes` | minutes 0–60 | Minutes asleep in the hour | | |
| 22 | `Garmin_sleep_minutes` | minutes 0–60 | Minutes asleep in the hour | | |
| 23 | `HealthkitPhone_sleep_minutes` | minutes 0–60 | Apple Health sleep attributed to a phone | | |
| 24 | `HealthkitWatch_sleep_minutes` | minutes 0–60 | Apple Health sleep attributed to a watch | | |
| 25 | `HealthkitUnknown_sleep_minutes` | minutes 0–60 | Apple Health sleep with unknown device class | Entirely blank | Values only before March 1, 2025 (see [Apple Health sleep](#apple-health-sleep)) |

[src: `<vault>/Data Preprocessing/07 Current Files and Version Register.md` § "Fixed hourly schema"; `<shared>/README.md` §§ "Hourly datasets — November 11, 2026", "Sleep", "Mood and missing values"; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`; `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`column_coverage`)]

Diagnostic columns (Garmin step source and coverage, processing flags, held-reading counts) live in separate audit files and must not be added to the main CSV. [src: `<vault>/Data Preprocessing/07 Current Files and Version Register.md` § "Fixed hourly schema", § "Supplemental files"]

**Companion files to use with the hourly files:**

| File | Cohort | Rows | Use |
|---|---|---:|---|
| `<shared>/Hourly_MoodCorrected_20261117/MoodResponses2024.csv.gz`, `MoodResponses2025.csv.gz` | both | one per scored response | Exact UTC and local time of every response, including same-hour resubmissions |
| `<shared>/Hourly_FullYear_20261117_StageC/DailyRestingHeartRate2024.csv.gz` | 2024 | 218,179 | Daily RHR by participant and local date, including 278 dates with no hourly local label |
| `<shared>/audit/DailyRestingHeartRate2025.csv.gz` | 2025 | 227,942 | Same for 2025; keeps 852 participant/source days absent from the hourly grid |
| `<shared>/Hourly_FullYear_20261117_StageC/PhoneStepParts2024.csv.gz` | 2024 | | Phone steps split into iPhone and app parts for 43 people |
| `<shared>/audit/HourlyProcessingFlags2025.csv.gz` | 2025 | 727,638 | Why a 2025 cell is blank or held; join on the key scope stated in each row |
| `<shared>/audit/HealthKitHRHeldReadings2025.csv.gz` | 2025 | 11,607 | Hours whose HR excludes same-second readings |
| `<shared>/audit/GarminHourlyDiagnostics2025.csv` | 2025 | 1,147,634 | Garmin step source, coverage seconds and quality flags |

[src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` § "Companion files"; `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`daily_companion_rows`); `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Audit companions and joins"]

## Time stamps in the files

- `time_utc` is always the start of a whole UTC hour; there are no fractional UTC keys in either current file. **Applied.** [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`fractional_utc`: 0); `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "File identity and row contract"]
- `time_local` labels the start of that UTC hour on the participant's assigned clock. In half-hour or quarter-hour time zones its minutes can be nonzero. **Applied.** [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md` § "How to use the files"]
- Values from records in half-hour or quarter-hour zones that fall across two UTC hours are withheld rather than split (see [Withheld values](#missing-values-and-zeros)). **Applied.** The September–November releases instead kept UTC times with nonzero minutes in such zones; **Superseded.** [src: `<shared>/README.md` § "Calendar and timestamps"; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Sources and reviewed dispositions"]
- **How the 2024 local label was chosen in Stage C** (counts of rows by basis): consistent label across the hour's observed records 5,458,226; the only existing grid label 1,628,618; the published mood label 102,674; a mood local hour corroborated by the response record 1,542; RHR-only hours 3,072; rows without UTC keep their original label 124,883; unresolved, left blank 57,433. **Applied.** [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`clock_choices`); `<shared>/audit/CollaborativeAudit/Codex/Hourly2024StageC/assemble.py`]
- **How the 2025 local label was chosen:** one consistent label from the hour's data wins; conflicting labels use the approved day clock only when it matches a source candidate; empty and daily-only hours use a supported clock or the one unique existing label; otherwise blank. Native Garmin UTC times never move; only their local label can. **Applied.** [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "File identity and row contract"; `<shared>/audit/CollaborativeAudit/Codex/HourlyMerge20261117/build_candidate.py`]
- The clock sources (2024 participant-update history; 2025 phone-record offsets, mood offset, reminder send time, roster zone) and their tiers are in [clocks and time zones](03-clocks-and-time-zones.md).
- **String format.** The September build wrote `time_utc` as `YYYY-MM-DDTHH:MM:SSZ` and `time_local` as `YYYY-MM-DDTHH:MM:SS`. The exact format in the current files was not checked for this note (unverified); the engine parses ISO 8601 in either form. A mixed `T`/space separator once broke a parser in Jack's notebook. [src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `publish`; `causal/src/ihs_causal/data/hourly.py`, `_hours_since_epoch`; `<vault>/Data Preprocessing/11 RHR Timing and Source Coverage Audit.md` § "Next decisions and remaining audit coverage" (parser candidate)]

## How each file was built

Both files descend from one processor build and a chain of dated, backed-up releases (see [Version history](#version-history)).

1. **September 29, 2026: raw to hourly (19 columns).** `<preprocessing-repo>/scripts/build_compact_ihs.py` read the raw Fitbit, Garmin and Apple Health steps and HR sources, deduplicated, resolved each record's clock, allocated to hours, and joined daily RHR from the per-device RHR processors. [src: `<shared>/Hourly_Rebuilt_20260929/README.md`; `<preprocessing-repo>/scripts/build_compact_ihs.py`]
2. **September 30: mood and complete calendars (20 columns)**, then removal of the 56 `NA` accounts (2024). [src: `<shared>/audit/HourlyMoodPublicationChecks.json`; `<shared>/README.md` § "Accounts excluded from the current analysis"]
3. **October 1: five sleep columns (25 columns)** from the per-device sleep processors in `<preprocessing-repo>/src/mobile_health_preprocessing/devices/*/sleep.py`. [src: `<shared>/audit/HourlySleepPublicationChecks.json`]
4. **2025 only, November 11–13: Garmin epoch steps** recovered from the server and 1,136 conflicts corrected. [src: `<shared>/README.md` §§ "Supported Garmin conflict correction — November 13, 2026 (current)" to "Previous Garmin recovery — November 11, 2026"]
5. **2024 only, November 14–15: January–June 2025 follow-up** (local Q3Q4 Fitbit, server Garmin, native Apple Health) merged into the full-year file. [src: `<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md`; `<shared>/Hourly_FullYear_20261115/README.md`]
6. **2025 only, November 17: coordinated rebuild.** Apple Health rebuilt on the server ("v3", March 1, 2025 to July 8, 2026), reviewed Fitbit and Garmin sleep, RHR rules, approved day clock, then consolidation to one row per UTC hour. Pipeline: `prepare.py` → `review_conflicts.py` → `reconcile_sleep.py` → `verify_garmin.py` → `build_candidate.py` → … → `consolidate_utc.py` → `validate_utc.py`. [src: `<shared>/audit/CollaborativeAudit/Codex/HourlyMerge20261117/REPORT.md` § "Reproduction"]
7. **2024 only, November 17: Stages A, B, C.** Stage A (Fitbit short wakes removed; Garmin RHR from the final daily summary through January 1, 2025); Stage B (Garmin RHR for January–June 2025; Garmin sleep-zero convention matched to 2025; baseline Fitbit steps for April–June 2024); Stage C (Apple Health from the "2024 v3" server rebuild, phone step split, one row per UTC hour). [src: `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/build_2024_stage_a.py` and `build_2024_stage_b.py` (docstrings); `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/stage_a/stage_a_summary.json`, `stage_b/stage_b_summary.json`; `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`]
8. **Both, November 17: mood moved to each response's exact UTC completion hour.** [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`]

**Consequence for date ranges in 2025.** The v3 Apple Health rebuild, the Garmin sleep rebuild and the day-clock rerouting of Fitbit and mood apply only inside March 1, 2025 to July 8, 2026. Rows before March 1, 2025 (the 2025 cohort's pre-study baseline back to April 2024) keep the September–October processing, except Garmin steps (the November 11–13 epoch recovery covers those dates), the Garmin final-summary RHR rule (5,556 changed cells lie outside the window) and the one-row-per-UTC-hour consolidation, which apply to all dates. [src: `<shared>/audit/CollaborativeAudit/Codex/HourlyMerge20261117/build_candidate.py` (`LO`, `HI`, `IN_SCOPE`); `<shared>/README.md` § "Initial full-period Garmin recovery — November 13, 2026 (historical)"; `<vault>/Audit Message Board.md` (posts of 2026-11-17 16:09 and 16:20)]

**Consequence for 2024.** Apple Health is rebuilt for the whole file range, so there is no Apple Health seam at January 1, 2025. Some native-device rules still differ between July–December 2024 and January–June 2025 (listed under each stream). [src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` § "Which time and value each stream uses"; `<shared>/Hourly_FullYear_20261115/README.md` § "Corrections and remaining checks"]

## Steps

General rules from the September build that still hold for values it produced:

- **Hourly allocation.** Interval records are split across hours in proportion to elapsed UTC time when both ends have a defensible offset; point records count at their start hour. Records with a missing or non-positive end get one second at their start. Step totals are conserved (checked per bucket). Hourly totals can therefore be fractional. **Applied** for values from that build. [src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `aggregate_bucket`; `<shared>/Hourly_Rebuilt_20260929/README.md`]
- **Manual entries** (Apple Health `HKWasUserEntered`) are excluded. **Applied** (both cohorts, both builds). [src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `raw_query`, `dedup_sql`; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Sources and reviewed dispositions"]
- **Contradictory values in one UTC hour** (from records placed on two local labels) are blank, with originals kept in the audit. **Applied** (2025 since November 17; 2024 since Stage C). [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Withheld hourly values after UTC consolidation"; `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` § "Which time and value each stream uses"]

### Fitbit steps

**2024.**
- Source: local minute-level exports `fitbit_intraday_steps_2024cohort_{BLQ1Q2,Q3Q4}.csv` (positive minutes only), summed per local hour and placed on the UTC hour of the 2024 clock. No zeros are recorded: a blank means no positive minute or no wear. **Applied.** [src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `raw_query`; `<vault>/Data Preprocessing/08 Preprocessing Audit 2024 and 2025.md` § "Prioritized findings" (536,847 values, no zeros, July–December 2024)]
- January–June 2025 follow-up: Q3Q4 labels moved one hour later before March 9, 2025 at 02:00 (seasonal export-clock correction). **Applied** (November 15). [src: `<shared>/Hourly_FullYear_20261115/README.md` § "Sources and processing" item 4; `<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md` § "Sources and rules"] Detail in [clocks](03-clocks-and-time-zones.md).
- Baseline April 1 to June 30, 2024: hourly sums pulled from the server filled into existing rows with the same local hour and a blank cell: 152,179 of 159,244 staged hours (260 people). Not placed: 4,110 hours of fewer than 10 people not in the file, 2,951 hours where two rows matched the local hour, 4 hours with no UTC row on the date. **Applied** (Stage B). [src: `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/stage_b/stage_b_summary.json`]
- Stage C: 154 UTC hours with differing Fitbit step contributions and 1,622 cells from fractional intervals are withheld (blank). **Applied.** [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`native_collisions`, `fractional_native_cells`)]

**2025.**
- Source: nightly positive-only minutes plus the two mirrored API days (June 19–20, 2026, with explicit zero grids). An API record is dropped when an identical nightly record exists (same participant, start, end, value); otherwise API rows are added. **Applied.** [src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `dedup_sql`; `<preprocessing-repo>/inventory/source_inventory.md` § "2025 · fitbit · steps"]
- Clock: in-scope hours moved to the approved day clock where approved; transition days, reminder-only days without mood support and fractional offsets held. **Applied** (March 1, 2025 to July 8, 2026). Before March 1, 2025: roster zone plus cross-device evidence. [src: `<shared>/audit/CollaborativeAudit/Codex/HourlyMerge20261117/build_candidate.py` (`fitbit_clock_map`)] See [clocks](03-clocks-and-time-zones.md).
- Withheld after consolidation: 559 hours with contradictory values, 1,039 fractional. **Applied.** [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Withheld hourly values after UTC consolidation"]
- June 18–20, 2026 all-zero Fitbit days: raised for the next 2025 candidate; **Proposed** (not in the current file). [src: `<vault>/Audit Message Board.md` (posts of 2026-11-17 18:11–18:43)]

### Garmin steps

**2024.**
- Source: 15-minute epochs (local `BLQ1Q2`; January–June 2025 from the server). Each epoch's steps are allocated to the UTC hours it overlaps; the offset gives the local label. Malformed offsets are repaired against the named-zone history for the local label only; UTC is not changed. **Applied.** [src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `corrected_anchor_sql`; `<vault>/Data Preprocessing/16 Garmin Boundary Recovery and HealthKit UTC Correction.md` § "Why the additional 20 rows are separated"]
- Activity components: the September rule deduplicates on time, offset and value, so distinct activities with equal counts in the same interval collapse (77 intervals, 43 participants, 7,258 candidate steps, 40 of them in July–December 2024). The January–June 2025 follow-up keeps distinct components. The July–December collapse is **Applied** (not corrected); a correction is **Proposed**. [src: `<vault>/Data Preprocessing/08 Preprocessing Audit 2024 and 2025.md` § "Prioritized findings"; `<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md` § "Earlier Garmin-completed candidate (preserved)"]
- Stage C: 30 hours with differing contributions and 1,145 fractional cells withheld. **Applied.** [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json`]

**2025.**
- Source: `GARMINEPOCHSUMMARY` epochs recovered from the server (available April 4, 2024 to July 6, 2026). Activity components within an epoch are added. A usable hour needs all 3,600 seconds covered without hard exceptions; partial hours stay blank and are listed in the audit; daily totals are never used to rescale or fill. Fewer than 10 participants in half-hour or quarter-hour zones are reaggregated on their recorded local-hour boundaries. **Applied.** [src: `<shared>/README.md` §§ "Previous Garmin recovery — November 11, 2026", "Initial full-period Garmin recovery — November 13, 2026 (historical)"]
- 1,136 earlier values that disagreed with the epochs were replaced; 16 conflicts and 305 values without a usable epoch counterpart were kept and flagged. **Applied** (November 13, carried forward). [src: `<shared>/README.md` § "Supported Garmin conflict correction — November 13, 2026 (current)"; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Sources and reviewed dispositions"]
- 321 fractional-interval cells withheld after consolidation. **Applied.** [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Withheld hourly values after UTC consolidation"]
- Before November 11 only June 2026 API intervals existed for 2025 Garmin steps. **Superseded.** [src: `<shared>/Hourly_Rebuilt_20260929/README.md`]

### Apple Health steps

**2024 (all dates): server rebuild "2024 v3" plus a phone split.**
- Per-record UTC intervals from `IHS_2024` sample tables, after deletion records, sync-version and copy reconciliation; phone and watch kept separate; held source hours (104 class-hours) masked. The run was requested for the whole range of the published 2024 file; the hours it actually returned span 2024-03-31 16:00 to 2025-07-07 04:00 UTC. Apple Health step, HR and sleep cells come only from this return, so those columns are blank outside that span (whether the November 15 file had earlier Apple Health values is unverified). **Applied** (Stage C). [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`source_bounds`, computed over the Apple Health table in `<shared>/audit/CollaborativeAudit/Codex/Hourly2024StageC/finish.py`)] [src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` § "Which time and value each stream uses"; `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`source_hold_counts`); `<shared>/audit/CollaborativeAudit/Codex/Hourly2024StageC/assemble.py`]
- App rules requested for the server run to match 2025: native Garmin priority (Garmin Connect copies removed where the participant has native Garmin data), Oura left out of hours with iPhone steps, manual entries excluded. That the server applied each of these is unverified here; the returned components are consistent. [src: `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/post_2024_server_run_20261117.py` (board post text)]
- **Phone split.** For the 43 people with app-written phone steps (19 already known plus 24 detected), the phone value is the iPhone's own count in hours where the server reports iPhone steps, otherwise the largest single app; other apps are dropped. This lowered 8,811 cells for 19 people; among the affected people, hours above 12,000 steps fell from 97 to 0. 67 hours held. **Applied.** [src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` §§ "Which time and value each stream uses", "Checks and exceptions"; `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`phone`, `phone_subgroups`); `<shared>/audit/CollaborativeAudit/Codex/Hourly2024StageC/phone.py`]
- Values the old build had put on rows with no UTC (20,269 phone and 150 watch step cells) are archived, not used. **Applied.** [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`unknown_utc_hk_legacy`)]
- Day-long app totals stay spread across the day's hours as the source allocates them (Drew's instruction); the spread hours are listed separately (6,964 in 2024). **Applied.** The November 15 follow-up rule that held day-long totals is **Superseded**. [src: `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." (rebuild plan and side-list paragraphs); `<shared>/Hourly_FullYear_20261115/README.md` § "Sources and processing" item 3]
- Superseded for 2024: the September build's sample-key deduplication and text-based device classing (no app or sync identity), which double-counted synced copies and app copies. [src: `<vault>/Data Preprocessing/09 HealthKit Identity and Source Audit.md`]

**2025, March 1, 2025 to July 8, 2026: server rebuild "v3".**
- UTC source times; participant/key/type deletion records; sync and insertion lineage; latest copy per writer, class and interval; manual records excluded; native Garmin identities suppress Garmin Connect phone copies; in hours with positive native iPhone steps Oura copies are dropped, Oura-only hours remain; valid long intervals keep proportional allocation. **Applied.** [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Sources and reviewed dispositions"; `<vault>/Data Preprocessing/25 Fable Follow-up - Sleep Exceptions and Source Rules.md` § "Recorded choices and build order"]
- 464 phone hours with a real source conflict are blank (450 had a rebuilt value); no old value is used instead. **Applied.** [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Sources and reviewed dispositions"]
- Hours where the phone's records carry two offsets are placed by each record's own UTC time (that is what v3 does). [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Sources and reviewed dispositions"]
- Day-long app totals stay spread (8,049 hours listed). **Applied.** [src: `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." (side-list paragraph)]
- **iPhone-first for every app (not only Oura).** Approved by Drew on November 17 for both cohorts; applied to 2024 in Stage C, but the 2025 file current results use predates it. In 2025 it concerns 88 people (43 double-counted over about 28,600 hours since March 1, 2025). **Proposed** for 2025 (approved, not applied): the same server run returned the 2025 parts (88 people pulled, run complete), but no 2025 candidate has been built from them. [src: private server repository, `reports/phone-step-parts/parts-20261118T014838249448Z-cp000011.md`; `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." (phone step column paragraph); `<vault>/Audit Message Board.md` (post of 2026-11-17 18:43); `<vault>/Data Preprocessing/07 Current Files and Version Register.md` § "Which files to use" ("The 2025 phone-step and Fitbit follow-ups remain separate")]

**2025, before March 1, 2025 (pre-study baseline).**
- September build: nightly records, deduplicated on participant, device class, start, end, offset, value and sample key; device class read from product-type and device text (watch, then phone, then other wearable, else unknown); `other_wearable` and `unknown` classes left out of the main columns. Local wall time placed by the 2025 clock. Known problems remain here (synced copies, app copies counted as phone). **Applied** for these dates only. [src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `dedup_sql`, `publish`; `<preprocessing-repo>/src/mobile_health_preprocessing/devices/healthkit/heart_rate.py`, `_device_class_sql`; `<vault>/Data Preprocessing/09 HealthKit Identity and Source Audit.md`]

## Heart rate

**Common rule.** `*_hr_avg` is the mean and `*_hr_max` the maximum of valid samples in the hour; zero and negative samples are invalid, never zero heart rate. Mean HR never exceeds maximum (checked). **Applied.** [src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `aggregate_bucket`; `<vault>/Data Preprocessing/08 Preprocessing Audit 2024 and 2025.md` § "Checks that passed"]

| Cohort | Device | How built | Withheld or held | Status |
|---|---|---|---|---|
| 2024 | Fitbit | Local point samples (local wall time) placed by the 2024 clock; January–June 2025 labels shifted by the seasonal rule (27,749,458 samples reconcile) | Stage C: 435 hours with differing contributions (the traced cases are two non-overlapping fragments of one hour; a plain average of fragment means differs from the sample-weighted mean by up to 18 bpm, so the hour is withheld rather than averaged), 266 fractional | Applied |
| 2024 | Garmin | Samples timed as daily-summary start + sample offset; a daily anchor is adjusted only across a corroborated DST change; UTC kept | Stage C: 426 hours (mean) with differing contributions, 214 fractional | Applied |
| 2024 | Apple Health | Server "2024 v3": mean and max of surviving samples per UTC hour and class; conflicting same-source readings excluded but the hour kept (8,545 class-hours had held readings); 34 hours from an unclassified source have no column | | Applied |
| 2025 | Fitbit | Nightly samples (validated cache) plus API; day clock in scope | 1,031 contradictory (mean), 46 fractional | Applied |
| 2025 | Garmin | As 2024 | 948 contradictory (mean), 271 fractional | Applied |
| 2025 | Apple Health, from March 1, 2025 | Server v3; same-second readings from one writer set aside as conflicting versions (265,732 groups); Drew approved keeping the rebuilt hour from surviving readings: 11,599 of 11,607 affected hours kept, 8 blank; 12 unknown-class hours to an audit file | Listed in `HealthKitHRHeldReadings2025.csv.gz` | Applied |
| 2025 | Apple Health, before March 1, 2025 | September build from nightly samples, text-based class | | Applied (these dates only) |

[src: `<shared>/Hourly_FullYear_20261115/README.md` § "Sources and processing" item 4; `<vault>/Data Preprocessing/19 Sleep Timing and Coverage Follow-up.md` § "Fitbit HR: repeated UTC hours contain separate fragments"; `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`native_collisions`, `fractional_native_cells`, `source_hold_counts`, `source_records_with_unmapped_hr_class`); `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`; `<preprocessing-repo>/scripts/build_compact_ihs.py`, `corrected_anchor_sql`; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`; `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." (heart-rate holds paragraph)]

An exact rerun keeping same-second readings was not requested. **Proposed** (declined for now). [src: `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." (heart-rate holds paragraph)]

## Resting heart rate

**Common rule.** RHR is one value per participant and local date, written on every hour of that date (both occurrences of a repeated fall-back hour). It is blank on hours whose local date is unresolved. It is the device's final daily estimate, available retrospectively, not a value known before a decision. Do not count repeated hourly cells as observations; use the daily companion files for daily analyses. **Applied.** [src: `<shared>/Hourly_Rebuilt_20260929/README.md`; `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` § "Which time and value each stream uses"; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Audit companions and joins"; `<vault>/Data Preprocessing/11 RHR Timing and Source Coverage Audit.md` § "1. RHR pre-decision timing"]

| Cohort | Device | Daily rule | Status |
|---|---|---|---|
| both | Fitbit | Daily export value; if several, highest representation priority (nightly over API in 2025), then mean of distinct positive values. 2024 follow-up days from the local Q3Q4/quarterly RHR files are included | Applied |
| 2024 | Garmin | Final, longest daily summary: 2,499 days / 65,840 cells through January 1, 2025 (Stage A) and 1,834 days / 44,004 cells for January–June 2025 (Stage B) | Applied |
| 2024 | Garmin | Mean of distinct values across summary versions | Superseded |
| 2025 | Garmin | Reviewed final/longest-summary candidate; daily values kept in the companion where the local label is unresolved | Applied |
| 2024 | Apple Watch | Server "2024 v3": last value of the day (latest end, then latest insertion), on complete interior dates; the two extraction-boundary dates keep earlier values; 7 class-days held | Applied |
| 2024 | Apple phone class | Server "2024 v3": mean of distinct values | Applied |
| 2025 | Apple Watch, phone | Same rules, on complete local days March 2, 2025 to July 6, 2026; extraction-edge days keep prior values; 18 local days with conflicting sources blank | Applied |
| 2025 | Apple phone class (Garmin Connect) | Date-relabel "A0": Garmin Connect writes the day's RHR at the next midnight; 29 days confirmed by record replay (24 values changed, 5 blanked) | Applied |
| 2025 | same | 75 unconfirmed days keep the server value and are flagged, pending surviving source records | Staged, not applied |
| 2024, 2025 | Apple Health before the rebuild | Mean of distinct values across all versions | Superseded (2024 entirely; 2025 from March 2, 2025) |

[src: `<preprocessing-repo>/src/mobile_health_preprocessing/devices/fitbit/resting_heart_rate.py` (`conflict_rule`); `<vault>/Data Preprocessing/11 RHR Timing and Source Coverage Audit.md` § "2. Daily RHR source coverage"; `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/stage_a/stage_a_summary.json`; `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/stage_b/stage_b_summary.json`; `<shared>/audit/CollaborativeAudit/Codex/Hourly2024StageC/source.py` (`INTERIOR`, `daily`); `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`source_hold_counts`); `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Sources and reviewed dispositions"; `<vault>/Data Preprocessing/23 June Tail and Approved Rebuild Plan.md` § "Hourly rebuild choices recorded from Drew"]

The 2024 Fitbit and Garmin January–June 2025 RHR days (20,458 Fitbit and 12,226 Garmin participant-days) were missing from the November 13 file because the original stage read only `BLQ1Q2` files; the follow-up merge added the Fitbit days from the relocated local files and the Garmin days from the server. That every one of those days is now present is unverified here. [src: `<vault>/Data Preprocessing/11 RHR Timing and Source Coverage Audit.md` § "2. Daily RHR source coverage"; `<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md` § "Sources and rules"]

## Sleep: rules shared by all devices

- **Unit.** Minutes asleep within the hour, 0 to 60, fractional allowed. Awake and in-bed-only time is not sleep. **Applied.** [src: `<shared>/README.md` § "Sleep"]
- **Do not sum device columns.** Devices can record the same night; phone records can differ greatly from watch records. Choose one source or an explicit priority. [src: `<shared>/README.md` § "Sleep"]
- **Episodes of 20 hours or more** are excluded from analytic values (kept in the raw source). **Applied** (all processors and the v3 rebuilds). [src: `<preprocessing-repo>/src/mobile_health_preprocessing/devices/fitbit/sleep.py` (`MAX_SLEEP_EPISODE_HOURS`); `.../devices/healthkit/sleep.py`; `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/post_2024_server_run_20261117.py` ("the under-20-hour rule")]
- **Zeros mean different things by device and period** (table in [Missing values and zeros](#missing-values-and-zeros)). Calendar filling alone never creates a sleep zero. **Applied.** [src: `<shared>/README.md` § "Sleep"]
- **Timing.** Sleep is placed on hours by the same clock as the device's other streams; no seasonal shift was applied to Fitbit sleep (detailed episode ends match daily logs unshifted, and match none when shifted by ±1 hour). [src: `<vault>/Data Preprocessing/18 Expanded Year Sleep and Coverage Audit.md` § "Fitbit sleep timing remains a separate question"]
- **Nights are the analysis unit** for sleep effects; hourly sleep is also used as a feature, so hourly placement matters. [src: design facts stated by Drew, analyst notes of 2026-11-16]

## Fitbit sleep

**2024: processor rules (local detailed sleep logs).**
- Stage records with level `asleep`, `light`, `deep` or `rem` count as asleep; `wake` and `restless` do not. Overlapping asleep intervals are unioned per participant, then split across local hours by overlap. **Applied.** [src: `<preprocessing-repo>/src/mobile_health_preprocessing/devices/fitbit/sleep.py`, `_historical_query`]
- **Covered-date zeros.** Every hour of a covered sleep date (the log's `SLEEPLOGDATE`, else the end date; including dates with only non-asleep stages) that has no asleep minutes is set to 0. The sleep date's 24 hours are local hours, so zeros can fall far from the night. **Applied.** [src: same function (`coverage_dates`, `grid`); `<vault>/Data Preprocessing/19 Sleep Timing and Coverage Follow-up.md` § "Year-boundary coverage depends on zero handling"]
- **Short wakes removed.** The export marks brief wakes (at most 3 minutes) as short-data `wake` records inside asleep stages; the processor counted them as sleep. Stage A subtracted them where the episode's stage boundaries match exactly and the corrected total matches Fitbit's daily summary within one minute: 275,769 cells applied (of 275,840 candidates; 71 sat on ambiguous rows). Median 20.5 minutes removed per episode. Episodes outside that support (12,425 hours held for episode/summary reconciliation, 386 for old-value mismatch, a cluster of 2.5–3.5 minute residuals in 1,381 episodes) keep the original values, short wakes included. **Applied** (both halves of the study year). [src: `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/stage_a/stage_a_summary.json`; `<vault>/Data Preprocessing/18 Expanded Year Sleep and Coverage Audit.md` § "Fitbit sleep: short wakes were counted as sleep"; `<vault>/Data Preprocessing/19 Sleep Timing and Coverage Follow-up.md` § "Remaining sleep residuals are source disagreements"]
- **Clock.** The processor leaves time unresolved; the October 1 publication placed each hour with the 2024 clock (participant updates). [src: `<preprocessing-repo>/src/mobile_health_preprocessing/devices/fitbit/sleep.py` (`'unresolved' timezone_source`); `<shared>/audit/HourlySleepPublicationChecks.json` (`clock_summary`)]
- Stage C: 53 hours with differing contributions and 72 fractional cells withheld. **Applied.** [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json`]

**2025 before stage reconciliation: processor rules (nightly summaries).**
- Overlapping nightly summaries are grouped; the one with the latest `MODIFIEDDATE`, then most minutes asleep, then latest end is kept. If API stage intervals lie inside the summary, do not overlap and sum to within 2 minutes of its minutes asleep, they are used; otherwise the summary's minutes asleep are spread over the episode window in proportion to overlap (fraction = minutes asleep / window length). The summary end date's 24 hours are zero-filled where no sleep is allocated. **Applied** where not replaced by the stage reconciliation below (mainly before March 2025 and in held hours). [src: `<preprocessing-repo>/src/mobile_health_preprocessing/devices/fitbit/sleep.py`, `_nightly_api_query`]

**2025 stage reconciliation (November 17).**
- Stage records from `FITBITSLEEPLOGDETAILS` give corrected asleep intervals (asleep union minus intersecting short wakes). Each sleep log (latest revision) is accepted when it does not overlap another log, was not on the earlier exception list, has one minutes-asleep value, and its stage-derived asleep minutes match Fitbit's total within 3 minutes. Otherwise the log's hours keep the published values. **Applied.** [src: `<shared>/audit/CollaborativeAudit/Codex/HourlyMerge20261117/reconcile_sleep.py`; `<vault>/Data Preprocessing/25 Fable Follow-up - Sleep Exceptions and Source Rules.md` § "Recorded choices and build order"]
- An hour is replaced only when all its stage minutes are accounted for by accepted logs; it is placed with the approved day clock, or on the single existing row when the clock is not approved; ambiguous placement keeps the published value. Counts: 449,228 valid stage hours; 437,860 placed; 11,368 keep published values (ambiguous placement); 23,682 log-exception hours and 180 insufficient-coverage hours keep published values. The exception list has 3,469 logs. **Applied.** [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Sources and reviewed dispositions"; `<vault>/Data Preprocessing/26 Validated Fitbit and Garmin Sleep Fixes.md` § "Fitbit resolution"]
- Stage hours after the nightly log snapshot ends (June 19, 2026 at 20:03) cannot be validated and are held (missing validation, not zero sleep). [src: `<vault>/Data Preprocessing/26 Validated Fitbit and Garmin Sleep Fixes.md` § "Coverage and merge limits"]
- Fitbit stage times are wall-clock labels on the device's clock; on the night the clocks went back (November 1–2, 2025) placement loses an hour, and most out-of-tolerance logs added in review were from that night. [src: `<shared>/audit/CollaborativeAudit/Codex/HourlyMerge20261117/reconcile_sleep.py` (comment); `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." (Fitbit sleep paragraph)]
- After consolidation: 880 contradictory and 52 fractional Fitbit sleep hours withheld. **Applied.** [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Withheld hourly values after UTC consolidation"]

## Garmin sleep

**Processor rules (both cohorts, `garmin/sleep.py`).**
- One summary is chosen from each cluster of overlapping episode versions, ranked by validation label priority, then usable exact stages, then smallest stage-versus-summary discrepancy, then latest insertion. **Applied.** [src: `<preprocessing-repo>/src/mobile_health_preprocessing/devices/garmin/sleep.py`, `select_canonical_episodes`]
- Exact stages (`deep`, `light`, `rem`, `sleep`, `asleep`) are allocated to the hours they cover; `awake` and `unmeasurable` are not sleep. If stages are missing, overlapping or do not match the summary, the summary's sleep duration is spread over the window `duration + awake + unmeasurable`, each hour receiving overlap × duration / window. **Applied.** [src: same file, module docstring, `prepare_episode_windows`, `allocate_exact_stage_episodes`, `allocate_summary_only_episodes`]
- Timestamped naps are unioned and only nap time not already covered by main sleep is added. 2025 nap totals without start and end times are kept in an audit file and never allocated. **Applied.** [src: same file, `allocate_nap_episodes`; `<shared>/README.md` § "Sleep"]
- Zeros are hours inside a recorded episode with no asleep time (awake or unmeasurable portions). [src: `<shared>/README.md` § "Sleep"]

**2024.**
- `BLQ1Q2` local files plus the January–June 2025 server pull (433 follow-up episodes held for stage or offset problems). **Applied.** [src: `<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md` § "Earlier Garmin-completed candidate (preserved)"]
- Zero convention matched to 2025: a zero in an hour that overlaps no Garmin sleep summary is blanked (118,303 cells); zeros inside a summary span (813) and 196 legacy zeros on rows without UTC are kept. Minutes asleep unchanged. **Applied** (Stage B). The follow-up build's whole-date zero filling is **Superseded**. [src: `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/stage_b/stage_b_summary.json`; `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/build_2024_stage_b.py` (docstring B2); `<vault>/Data Preprocessing/18 Expanded Year Sleep and Coverage Audit.md` § "Sleep zeros create a January processing seam"]

**2025, March 1, 2025 to July 8, 2026: revision-aware rebuild.**
- Server-validated parent summaries with revision-specific validation labels and reviewed stage records, run through the processor's own functions (`annotate_summary_versions`, `build_garmin_sleep_hourly`). An independent SQL reproduces all 21,308 episode selections and 178,876 hours; 178,779 hours placed. 13 episodes of fewer than 10 people with equal-ranked alternatives are blank (118 hours). Summary-fallback episodes are flagged in the episode audit. Garmin UTC times never move; local labels follow the approved clock. **Applied.** [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Sources and reviewed dispositions"; `<shared>/audit/CollaborativeAudit/Codex/HourlyMerge20261117/reconcile_sleep.py`; `<vault>/Data Preprocessing/26 Validated Fitbit and Garmin Sleep Fixes.md` § "Garmin resolution"]
- Before March 1, 2025: October 1 processor output from nightly summaries and API stages (API stages used only when non-overlapping and reconciled to the nightly components). **Applied** for those dates. [src: `<preprocessing-repo>/inventory/source_inventory.md` § "2025 · garmin · sleep"]

## Apple Health sleep

**Current rule (2024 all dates; 2025 from March 1, 2025): server v3.**
- Asleep categories are unioned in UTC per class (phone, watch) before allocation. A zero needs an explicit awake interval; in-bed-only time, absent hours and dates with only a sleep record do not create zeros. Records with positive-length source holds are masked; zero-length records contribute nothing (281 in 2025); 23 phone hours touched by one invalid 22.4-hour interval are blank (2025). **Applied.** [src: `<shared>/Hourly_FullYear_20261115/README.md` § "Sources and processing" item 6; `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` § "Which time and value each stream uses"; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Sources and reviewed dispositions"]
- The server returned phone and watch classes only, so `HealthkitUnknown_sleep_minutes` is blank throughout 2024 and is cleared inside the 2025 rebuild window; it holds values only before March 1, 2025 in 2025. **Applied.** [src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`; `<shared>/audit/CollaborativeAudit/Codex/HourlyMerge20261117/build_candidate.py` (`clear_cells` for `HealthkitUnknown_sleep_minutes`)]
- Effect on 2024 nonmissing cells (Stage B → Stage C): phone sleep 1,822,420 → 146,166; watch sleep 691,798 → 286,573. The drop is the removal of whole-date inferred zeros, not lost sleep. [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`column_coverage`)]

**Earlier rule (processor `healthkit/sleep.py`).** Categories `asleep`, `asleepCore`, `asleepDeep`, `asleepREM` are sleep; `awake` and `inBed` are tracked separately. Exact duplicates are dropped (nightly preferred over API); manual entries excluded; overlapping intervals unioned per class; every hour of a date on which any interval of that class ends (including in-bed-only and awake-only dates) is zero-filled where no sleep is allocated. **Superseded** for 2024 and for 2025 from March 1, 2025; **Applied** for 2025 before March 1, 2025. [src: `<preprocessing-repo>/src/mobile_health_preprocessing/devices/healthkit/sleep.py`; `<vault>/Data Preprocessing/09 HealthKit Identity and Source Audit.md` § "Cross-review with Opus" (in-bed-only covered dates)]

## Mood

Summary only; rules and evidence are in [mood timing](05-mood-timing.md).

- `Mood` is the score of the latest response **completed** in that UTC hour; a UTC hour includes its start and excludes the next hour's start. Hours without a response have `Mood = 0`; values are never carried to other hours. **Applied.** [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md` § "How to use the files"; `<shared>/README.md` § "Mood and missing values"]
- 2024: the UTC instant comes from the offset on each raw response; 105,639 responses → 104,314 positive hours (1,325 superseded by a later response in the same hour); 885 participants. 2025: the UTC instant comes from the server's question-result export, matched to every one of 89,252 scored responses; → 87,252 positive hours (2,000 superseded); 864 participants. **Applied.** [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`; `<shared>/audit/CollaborativeAudit/Codex/MoodTiming20261117/build.json`]
- `time_local` at a response hour is the respondent's clock at the start of the UTC hour; daily RHR was looked up again where this changed the local date. [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md` § "Evidence for the two corrections"]
- Superseded: the September 30 2025 placement that read survey `ENDDATE` as UTC (mood 4–8 hours early), and earlier placements on duplicated local-label rows. [src: `<shared>/README.md` § "Mood and missing values"; `causal/config/data_notes.yaml`]
- The engine converts `Mood = 0` to missing. A single 2025 response with score 0 cannot be told apart from no response in the hourly file (it is absent from the scored set of 89,252; inference, unverified). [src: `causal/src/ihs_causal/data/hourly.py`, `read_hourly`; `<shared>/audit/HourlyMoodPublicationChecks.json` (`source_zero_scores`)]

## Priority between devices and between apps

- **Between devices: none in the files.** Fitbit, Garmin, Apple phone, Apple watch (and unknown Apple sleep) are separate columns; no value is chosen or summed across them. **Applied.** [src: `<shared>/Hourly_Rebuilt_20260929/README.md` ("Phone and watch values are separate; neither is a fallback for the other"); `<shared>/README.md` § "Sleep"]
- **Superseded:** the September 17 151-column files had combined compatibility columns that preferred watch, then other wearable, phone and unknown, with ties broken Fitbit, Garmin, HealthKit. [src: `<vault>/Data Preprocessing/02 Processing and Validation.md` § "Upstream raw-to-hourly processing" item 5; `<vault>/Data Preprocessing/01 Hourly Data Dictionary.md`]
- **Within Apple Health, by writing app** (affects the phone column): native Garmin data suppress Garmin Connect copies; iPhone steps suppress Oura copies in the same hour; in 2024 (43 people) the iPhone count, else the largest single app, for every app. Details and statuses under [Apple Health steps](#apple-health-steps).
- **Nightly versus API** (2025): exact nightly duplicates win; API rows add what nightly lacks. **Applied.** [src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `dedup_sql`]
- **Analysis-side device choice** (which device's column is an outcome) is made by the engine, not in the files: see [How the analysis engine reads the files](#how-the-analysis-engine-reads-the-files).

## Deduplication summary

| Level | Rule | Status |
|---|---|---|
| September build, all devices (steps, HR) | Drop manual entries; drop API rows with an identical nightly record; keep one row per participant, device, start, end, offset, value and sample key | Applied for values still from that build (2024 Fitbit and Garmin; 2025 Fitbit, Garmin HR, Apple Health before March 1, 2025) |
| Garmin 2024 steps | That rule collapses equal-count activity components (July–December 2024) | Applied (known undercount; correction Proposed) |
| Garmin 2025 steps | Epoch activity components added, not collapsed | Applied |
| Apple Health (v3) | Deletion records by participant, key and type; highest sync version then latest insertion; latest copy per writer, class and interval; app-copy suppression | Applied (2024 all dates; 2025 from March 1, 2025) |
| Fitbit 2025 sleep logs | Latest revision per participant, start and end | Applied |
| Garmin sleep | One summary per cluster of overlapping versions; revision-aware in 2025 | Applied |
| UTC consolidation | Identical copies at one UTC hour collapse; contradictory values blank | Applied |
| Mood | Latest completed response per UTC hour | Applied |

[src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `dedup_sql`; `<vault>/Data Preprocessing/08 Preprocessing Audit 2024 and 2025.md`; `<shared>/Hourly_FullYear_20261115/README.md` § "Sources and processing" item 1; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`; `<shared>/audit/CollaborativeAudit/Codex/HourlyMerge20261117/reconcile_sleep.py`]

## Missing values and zeros

**Blank** means no usable measurement for that device and hour. **Zero** is an observation whose meaning depends on the stream:

| Column | What a zero means | What a blank means |
|---|---|---|
| `Fitbit_steps` | 2024: none in July–December 2024 (positive-only export; checked November 13). 2025: 6,026 zero hours on November 13; in the November 17 base the only Fitbit step zeros are 6,004 cells on June 18–20, 2026 (SCAN-02-F03, board post of 2026-11-17 17:52), near the mirrored API days; their source is unverified | No positive minute, not worn, not synced, or withheld |
| `Garmin_steps` | Fully covered hour with no steps (Garmin writes zeros in every worn hour) | Hour not fully covered (2025) or no epoch |
| `Healthkit*_steps` | A recorded zero (rare) | No record; phone steps mean "has steps", not wear |
| `*_hr_avg`, `*_hr_max`, `*_RHR` | Never valid (zeros and negatives are invalid) | No valid sample or daily value |
| `Fitbit_sleep_minutes` | Covered sleep date with no asleep time in that hour (local date grid) | Date not covered, or withheld |
| `Garmin_sleep_minutes` | Hour inside a recorded episode with no asleep time | Outside any episode |
| `Healthkit*_sleep_minutes` (v3) | Explicit awake interval in the hour | No sleep record (in-bed-only does not count) |
| `HealthkitUnknown_sleep_minutes`, Apple sleep in 2025 before March 1, 2025 | Covered date (including in-bed-only dates) | Not covered |
| `Mood` | No response in that hour (sentinel, not a score) | Not used |

[src: `<shared>/README.md` §§ "Sleep", "Mood and missing values"; `<vault>/Data Preprocessing/08 Preprocessing Audit 2024 and 2025.md` §§ "Prioritized findings", "Coverage and clocks"; `<vault>/Data Preprocessing/09 HealthKit Identity and Source Audit.md` § "Cross-review with Opus"; `causal/src/ihs_causal/data/features.py` (module docstring)]

A zero does not establish that the device was worn continuously or that the person was awake. [src: `<shared>/README.md` § "Sleep"]

**Withheld values.** Values are left blank, never guessed, when: two different values meet at one UTC hour; a record cannot be assigned to one whole UTC hour (half-hour or quarter-hour zones); a source is held for conflicting versions or an invalid interval; or the local date of a daily value is unresolved. Originals are kept in audit files. **Applied.** Counts for 2025 after consolidation:

| Column | Contradictory | Fractional |
|---|---:|---:|
| `Fitbit_hr_avg` / `_max` | 1,031 / 1,013 | 46 / 46 |
| `Fitbit_sleep_minutes` | 880 | 52 |
| `Fitbit_steps` | 559 | 1,039 |
| `Garmin_hr_avg` / `_max` | 948 / 779 | 271 / 271 |
| `Garmin_steps` | — | 321 |
| `Mood` (superseded by the mood fix) | — | 17 |

[src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Withheld hourly values after UTC consolidation"] The 2024 equivalents are in the stream sections above. [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json`]

Exact rebucketing of fractional intervals from source records is **Proposed**. [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Validation and remaining work"]

## Why hours are missing

1. **No row.** Hours before a participant's first or after their last record date have no row. [src: `<shared>/README.md` § "Calendar and timestamps"]
2. **Device not used or not synced.** Most blank cells. Coverage falls through the year (2024: 865 participants with a row in July 2024, 576 in June 2025; see the [monthly table](#2024-coverage-by-month)).
3. **Source exports only positive events** (2024 Fitbit steps; 2025 nightly Fitbit steps). [src: `<preprocessing-repo>/inventory/source_inventory.md` §§ "2024 · fitbit · steps", "2025 · fitbit · steps"]
4. **Coverage rules.** 2025 Garmin steps need a fully covered hour. [src: `<shared>/README.md` § "Previous Garmin recovery — November 11, 2026"]
5. **Withheld or held values** (previous section).
6. **Unresolved clock.** Rows with no UTC cannot enter UTC windows (124,883 in 2024 Stage C, including all old Apple Health values on such rows, which were archived; 7,201 in 2025). Daily RHR is blank on hours with no local label; use the daily companion. [src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` § "Checks and exceptions"; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`]
7. **End of the 2025 local snapshot.** Fitbit, Garmin heart rate and mood stop on June 20, 2026 while decisions run to June 30; data for June 21–30 are thin. Closing this needs a small server pull: **Proposed**. [src: `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." (scan of the published 2025 file); `causal/config/data_notes.yaml`]
8. **Historical gaps that later releases closed.** In the first mood comparison (September 30), 32,376 2024 reports fell outside the participant's wearable date range (2024 mood ran into July 2025 while wearables then ended in January 2025), 2,379 fell in missing hours on dates with wearable rows, and 4,155 2025 reports fell in missing hours; the complete calendars and the full-year expansion closed these. **Superseded** as a description of the current files. [src: `<shared>/README.md` § "Why hours were missing"; `<shared>/audit/HourlyMoodPublicationChecks.json` (`initial_gap_investigation`)]

## Validation

| Release | Checks recorded |
|---|---|
| September 29 build | CSV-to-Parquet content verification; schema; step-total conservation and HR sample-count checks per bucket; nine builder regression tests |
| September 30 mood and calendar | All source reports represented; retained 19 columns byte-identical; complete calendars (no unexplained gaps); latest-report selection; zeros in non-report hours |
| October 1 sleep | Every original field and row order kept; every sleep value matched to its source key; per-participant and device totals reconciled; daylight-saving folds; account exclusions |
| November 11–13 (2025 Garmin) | Every non-target cell byte-compared to the backup; independent readback; diagnostics updated for exactly the changed rows |
| November 15 (2024 full year) | Strict CSV readback of every original key and unaffected cell; independent step allocation (48,663 records) and sleep union (160,734 writer-hours) |
| November 17 (2025) | Full readback; schema and order; 928-person scope; unique UTC hours; every baseline row has a key-map destination; each column independently regrouped from source contributions; 118 tied Garmin sleep blanks; all 1,152 earlier Garmin adjudications |
| November 17 Stage C (2024) | All 419 server chunks verified; final CSV compared with each native and Apple Health stream (0 mismatches, 0 duplicate UTC keys); phone split reproduces 217,671 hours within rounding; daily RHR checked on 314,996 grid days |
| November 17 mood | Reopened and compared with a separate raw replay: every selected score, UTC hour and local label matched; 0 differing main-window memberships for 2025; no unexpected wearable or key changes |

[src: `<shared>/Hourly_Rebuilt_20260929/README.md`; `<shared>/audit/HourlyMoodPublicationChecks.json`; `<shared>/audit/HourlySleepPublicationChecks.json` (`independent_saved_csv_checks`); `<shared>/README.md` § "Supported Garmin conflict correction — November 13, 2026 (current)"; `<shared>/Hourly_FullYear_20261115/README.md` § "Verification"; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Validation and remaining work"; `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` § "Checks and exceptions"; `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`day_value_checks`); `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json`]

**Range screens** (November 13, both files): no negative steps, no non-positive observed HR, sleep within 0–60, mean HR never above maximum, mood within 0–10. These establish internal consistency, not correctness: a duplicated step count passes every range check. [src: `<vault>/Data Preprocessing/08 Preprocessing Audit 2024 and 2025.md` § "Checks that passed"]

## How the analysis engine reads the files

These are analysis-side rules in `causal/src/ihs_causal/data/hourly.py` (`read_hourly`), **Applied** in current results:

- `participant_id`, `time_utc`, `time_local` are read as text and parsed as ISO 8601; `time_utc` becomes whole hours since 1970-01-01 UTC.
- **Rows without a UTC time are dropped** (counted in the build log).
- `Mood` values of 0 become missing.
- If a file still had two rows for one UTC hour, they would be combined (steps and sleep summed, HR, RHR and mood averaged, max HR maximum). The current files have no such rows, so this does not act.

Which device's column becomes an outcome, and which windows are kept, is decided later in `causal/src/ihs_causal/data/features.py`: per participant, "combined" uses the instrument (Fitbit, Garmin, Apple) with the most observed hours in their post windows; Apple is the watch for each hour, else the phone (`watch_then_phone`, default) or watch only; an hour counts as observed when it has a heart-rate value or a positive step count. [src: `causal/src/ihs_causal/data/features.py` (module docstring)] Those rules belong to the model notes, not to preprocessing. `causal/src/ihs_causal/data/sleep.py` also links native sleep episodes to decisions; whether current sleep results use it rather than the hourly sleep columns was not checked for this note (unverified).

## Version history

Rows and participants are for the file as released. "Status" is relative to current results.

| Date (2026) | Release | Cohort | Rows / people / columns | SHA-256 (prefix) | What changed | Status |
|---|---|---|---|---|---|---|
| Sep 17 | Annual export, 151 columns | 2024 | 4,360,907 / 940 / 151 | `9e01c967` | Device-specific wide columns plus combined compatibility columns; fixed UTC−4 display for unresolved hours | Superseded |
| Sep 17 | same | 2025 | 6,738,045 / 920 / 151 | `07dea0cc` | | Superseded |
| Sep 29 | Compact rebuild (`Hourly_Rebuilt_20260929`) | 2024 | 4,255,152 / 938 / 19 | `8a677177` | Four device channels, explicit clocks, no fixed offset | Superseded (base of all later files) |
| Sep 29 | same | 2025 | 6,681,374 / 919 / 19 | `7642ecae` | | Superseded |
| Sep 30 | Mood and complete calendars | 2024 | 6,567,091 / 948 / 20 | `0a327812` | `Mood`; every local hour first to last date | Superseded |
| Sep 30 | same | 2025 | 8,430,742 / 928 / 20 | `8bd90d6a` | 2025 mood from survey `ENDDATE` read as UTC | Superseded |
| Sep 30 | Account exclusion | 2024 | 6,490,440 / 931 / 20 | `c54175e9` | 56 `NA` accounts removed (76,651 rows) | Superseded (rule still applied) |
| Oct 1 | Sleep columns | 2024 | 6,542,792 / 931 / 25 | `046fd23b` | Five sleep columns; sleep-only hours added | Superseded |
| Oct 1 | same | 2025 | 8,455,984 / 928 / 25 | `36e5e921` | | Superseded |
| Nov 11 | Garmin epoch recovery, calendar 2025 | 2025 | 8,461,025 / 928 / 25 | `e3943544` | +515,926 Garmin step values (207,500 zeros), +5,041 rows; diagnostics moved to a sidecar | Superseded |
| Nov 13 | Garmin full-period recovery | 2025 | 8,485,055 / 928 / 25 | `3b037b94` | +493,238 values, +24,030 rows | Superseded |
| Nov 13 | Garmin conflict correction | 2025 | 8,485,055 / 928 / 25 | `962ea65a` | 1,136 cells replaced; 16 kept and flagged | Superseded (corrections carried forward) |
| Nov 14–15 | Follow-up candidates (`Hourly_Followup_20261114`, `_Garmin_20261114`, `_ReviewedSeams_20261115`) | 2024 | 7,437,115 / 7,456,861 / 7,456,861; 931; 25 | `95a644e8`, `f9f19676`, `dcfe54cc` | January–June 2025 local, Garmin, reviewed seams | Superseded (never published) |
| Nov 15 | Full-year expansion (root `dfHourly2024.csv`) | 2024 | 7,462,876 / 931 / 25 | `67d15a8a` | January–June 2025 rebuilt; native Apple Health reconciled for the follow-up; Fitbit seasonal HR correction | Superseded for current results; still the root file |
| Nov 17 16:56 ET | Coordinated rebuild (root `dfHourly2025.csv`) | 2025 | 8,564,434 / 928 / 25 | `84555a10` | Apple Health v3 from March 1, 2025; Fitbit and Garmin sleep; RHR rules; day clock; one row per UTC hour | Base of current file; still the root file |
| Nov 17 (local stages) | Stages A and B | 2024 | 7,462,876 / 931 / 25 | `9e9dcb5d`, `b27caca2` | Fitbit short wakes; Garmin RHR; Garmin sleep zeros; baseline Fitbit steps | Intermediate (carried into Stage C) |
| Nov 17 ~21:35 ET | Stage C (`Hourly_FullYear_20261117_StageC`) | 2024 | 7,376,448 / 931 / 25 | `a158a0a9` | Apple Health "2024 v3" all dates; phone split; one row per UTC hour | Base of current file; independent review pending |
| Nov 17 ~22:16 ET | **Mood-corrected** (`Hourly_MoodCorrected_20261117`) | 2024 | **7,376,544 / 931 / 25** | **`c16bd124`** | Mood at exact UTC completion hour; +96 rows | **Applied (current results)**; independent review pending |
| same | same | 2025 | **8,564,451 / 928 / 25** | **`2df0f3e1`** | Same for 2025; +17 rows | **Applied (current results)**; independent review pending |

[src: `<vault>/Data Preprocessing/01 Hourly Data Dictionary.md` § "Delivered files"; `<vault>/Data Preprocessing/02 Processing and Validation.md` § "Delivered file fingerprints"; `<shared>/Hourly_Rebuilt_20260929/README.md`; `<shared>/audit/HourlyMoodPublicationChecks.json`; `<shared>/audit/HourlySleepPublicationChecks.json`; `<shared>/audit/GarminSchemaRestoration2025Checks.json`; `<shared>/audit/GarminFullPeriodMerge2025Checks.json`; `<shared>/README.md` §§ "Supported Garmin conflict correction — November 13, 2026 (current)", "Previous Garmin recovery — November 11, 2026"; `<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md`; `<shared>/Hourly_FullYear_20261115/README.md`; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`; `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/stage_a/stage_a_summary.json`, `stage_b/stage_b_summary.json`; `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json`; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`; `<vault>/Audit Message Board.md` (posts of 2026-11-17)]

Backups of each replaced root file are under `<shared>/backups/<date>_<topic>/`. The audit trail of each correction is in [audit corrections](04-audit-corrections.md).

## 2024 coverage by month

Participant-hours with a step, heart-rate or sleep value from each channel in the 2024 Stage C file (channels can overlap in an hour). The mood correction does not change these columns.

| UTC month | Participants with a row | Fitbit | Garmin | Apple phone | Apple watch |
|---|---:|---:|---:|---:|---:|
| 2024-07 | 865 | 147,573 | 52,243 | 319,615 | 211,929 |
| 2024-08 | 836 | 135,476 | 51,329 | 305,615 | 194,744 |
| 2024-09 | 794 | 123,082 | 51,717 | 278,744 | 171,537 |
| 2024-10 | 760 | 116,684 | 52,682 | 273,628 | 169,410 |
| 2024-11 | 736 | 103,885 | 49,994 | 250,437 | 154,253 |
| 2024-12 | 709 | 103,131 | 51,671 | 245,563 | 146,627 |
| 2025-01 | 679 | 101,244 | 50,162 | 233,542 | 145,600 |
| 2025-02 | 667 | 86,593 | 46,969 | 202,374 | 127,896 |
| 2025-03 | 644 | 91,095 | 53,481 | 217,396 | 134,437 |
| 2025-04 | 629 | 85,099 | 50,619 | 202,349 | 123,263 |
| 2025-05 | 611 | 85,702 | 51,749 | 204,687 | 119,786 |
| 2025-06 | 576 | 71,596 | 46,394 | 179,597 | 102,177 |

[src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` § "Study-year coverage"]

Nonmissing cells in the 2024 Stage C file: Fitbit steps 1,074,459; Garmin steps 749,739; Apple phone steps 3,464,998; Apple watch steps 1,893,448; Fitbit HR 1,341,764; Garmin HR 611,936; Apple watch HR 2,094,032; Apple phone HR 256,094; Fitbit sleep 1,208,503; Garmin sleep 172,575; Apple phone sleep 146,166; Apple watch sleep 286,573; positive mood 105,050 (104,314 after the mood fix). [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`column_coverage.obs`); `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`] Equivalent 2025 column counts were not found in a readable report (not tabulated here).

## Open items

| Item | Cohort | Status |
|---|---|---|
| Independent review of Stage C and the mood-corrected pair | both | Pending |
| iPhone-first phone steps for every app | 2025 | Proposed (approved; server parts returned, no candidate built) |
| June 18–20, 2026 all-zero Fitbit days | 2025 | Proposed |
| Fitbit, Garmin HR and mood after June 20, 2026 | 2025 | Proposed (needs a server pull) |
| 75 unconfirmed A0 Apple phone-RHR date relabels | 2025 | Staged, not applied |
| Exact rebucketing of fractional-offset values | both | Proposed |
| Garmin 2024 equal-count activity components (July–December) | 2024 | Proposed |
| Fitbit 2024 sleep episodes held from the short-wake fix; 2.5–3.5 minute residuals | 2024 | Applied as is (originals kept) |
| Processing seams at January 1, 2025 for native devices (Fitbit step clock, Garmin step components, Fitbit/Garmin sleep-zero inference) | 2024 | Open; see [audit corrections](04-audit-corrections.md) |
| Pre-March 2025 rows of the 2025 file keep September rules (Apple Health copies, covered-date sleep zeros) | 2025 | Applied as is; affects baseline only |
| HealthKit same-second HR exact rerun | both | Proposed (not requested) |

[src: sections above]

## Sources consulted

- `<shared>/README.md`; `<shared>/Hourly_Rebuilt_20260929/README.md`; `<shared>/Hourly_FullYear_20261115/README.md`; `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` and `Validation2024.json`; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md` and `MoodTimingValidation.json`; `<shared>/audit/HourlyMoodPublicationChecks.json`, `HourlySleepPublicationChecks.json`, `GarminSchemaRestoration2025Checks.json`, `GarminFullPeriodMerge2025Checks.json`; `<shared>/audit/CollaborativeAudit/Codex/HourlyMerge20261117/` (`REPORT.md`, `build_candidate.py`, `reconcile_sleep.py`); `<shared>/audit/CollaborativeAudit/Codex/Hourly2024StageC/` (`common.py`, `source.py`, `phone.py`, `assemble.py`, `input_checks.json`); `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/` (stage A and B scripts and summaries); `<shared>/audit/CollaborativeAudit/Codex/MoodTiming20261117/` (`sources.json`, `build.json`)
- `<vault>/Data Preprocessing/` notes 00, 01, 02, 07, 08, 09, 11, 15–19, 23, 25, 26, 30, 31 and `Attachments/Jack_Hourly_Manifest_20261117.json`; `<vault>/Audit Decision Summary 2026-11-14.md`; `<vault>/Audit Message Board.md` (posts of November 17)
- `<preprocessing-repo>/README.md`; `<preprocessing-repo>/scripts/build_compact_ihs.py`; `<preprocessing-repo>/src/mobile_health_preprocessing/devices/fitbit/{sleep,resting_heart_rate}.py`, `devices/garmin/sleep.py`, `devices/healthkit/{sleep,heart_rate}.py`; `<preprocessing-repo>/inventory/source_inventory.md`
- `causal/config/data_notes.yaml`, `causal/config/paths.example.yaml`, `causal/src/ihs_causal/data/hourly.py`, `causal/src/ihs_causal/data/features.py`
