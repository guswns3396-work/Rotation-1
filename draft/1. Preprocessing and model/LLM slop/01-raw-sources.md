# Raw data sources by cohort

**Summary.** The IHS micro-randomized trial data used here come from three cohorts. The 2023 cohort is used only to compare against earlier builds. The 2024 cohort (study year July 1, 2024 to June 30, 2025) arrived as quarterly CSV exports from the study platform, later completed by read-only pulls from the `IHS_2024` server database. The 2025 cohort (study year June 30, 2025 to June 30, 2026) comes from the study server: cumulative "nightly" CSV exports, a few daily API snapshots, the server's own decision and message files, and pulls from the `IHS_2025` database. The cohorts differ in how timestamps are stored: 2024 Apple Health and mood records carry a UTC offset, while 2025 nightly Apple Health and Fitbit records are local wall-clock times with no offset. Fitbit carries no offset in either cohort. This note lists what each source holds, its time span, how its timestamps are stored, and which raw streams exist but are not used. How these sources become hourly rows is in [the hourly files note](02-hourly-files.md). Clock reconstruction is in [clocks and time zones](03-clocks-and-time-zones.md).

## Contents

- [How to read this note](#how-to-read-this-note)
- [Cohorts at a glance](#cohorts-at-a-glance)
- [2023 cohort](#2023-cohort)
- [2024 cohort](#2024-cohort)
  - [2024 folder layout](#2024-folder-layout)
  - [2024 Fitbit](#2024-fitbit)
  - [2024 Garmin](#2024-garmin)
  - [2024 Apple Health (HealthKit)](#2024-apple-health-healthkit)
  - [2024 server pulls from IHS_2024](#2024-server-pulls-from-ihs_2024)
  - [2024 Oura and Google Health](#2024-oura-and-google-health)
  - [2024 mood surveys](#2024-mood-surveys)
  - [2024 baseline and quarterly surveys](#2024-baseline-and-quarterly-surveys)
  - [2024 notification log](#2024-notification-log)
  - [2024 participant updates and time-zone history](#2024-participant-updates-and-time-zone-history)
  - [2024 subject list and account exclusions](#2024-subject-list-and-account-exclusions)
  - [2024 weather](#2024-weather)
- [2025 cohort](#2025-cohort)
  - [2025 server and local mirror layout](#2025-server-and-local-mirror-layout)
  - [2025 nightly exports](#2025-nightly-exports)
  - [2025 API snapshots](#2025-api-snapshots)
  - [2025 server database tables pulled for rebuilds](#2025-server-database-tables-pulled-for-rebuilds)
  - [2025 Fitbit](#2025-fitbit)
  - [2025 Garmin](#2025-garmin)
  - [2025 Apple Health (HealthKit)](#2025-apple-health-healthkit)
  - [2025 Oura and Google Health](#2025-oura-and-google-health)
  - [2025 mood surveys](#2025-mood-surveys)
  - [2025 baseline and quarterly surveys](#2025-baseline-and-quarterly-surveys)
  - [2025 decisions, messages and notifications](#2025-decisions-messages-and-notifications)
  - [2025 participant roster, time zones and custom fields](#2025-participant-roster-time-zones-and-custom-fields)
  - [2025 weather](#2025-weather)
- [Message pool and message coding (both cohorts)](#message-pool-and-message-coding-both-cohorts)
- [Timestamp storage summary](#timestamp-storage-summary)
- [Raw streams that exist but are unused](#raw-streams-that-exist-but-are-unused)
- [Conflicts between sources and how they were resolved](#conflicts-between-sources-and-how-they-were-resolved)
- [Unverified items](#unverified-items)
- [Sources consulted](#sources-consulted)

## How to read this note

**Placeholders.** Paths outside the repository are written with placeholders:

| Placeholder | Meaning |
|---|---|
| `<shared>` | The shared analysis folder (hourly files, decision files, `README.md`, `audit/`) |
| `<vault>` | The project's Obsidian notes (`Data Preprocessing/` numbered notes, audit board, decision summary) |
| `<preprocessing-repo>` | The Mobile Health Preprocessing package that built the first hourly files |
| `<raw2024>` | The 2024 cohort raw export folder (`InterventionMessages`, `Mood`, `ParticipantUpdates`, `SubjectList`, `Survey Data`, `Wearable`, `Weather`) |
| `<server2025>` | The local mirror of the 2025 study server (`data/` with `nightly`, `api`, `participants`, `custom_fields`; `agents/` with the online agents' files) |
| `<raw2023>` | The 2023 cohort raw export folder |
| `<prior-data>` | Earlier decision-level builds (`dfEvents2023/2024/2025.csv`) |

**Status labels.** Facts about raw files have no status. Where a source feeds a processing rule, the rule's status is given as in the other notes: **Applied** (in the hourly files current results use: `<shared>/Hourly_MoodCorrected_20261117/dfHourly2024.csv` and `dfHourly2025.csv`), **Staged, not applied**, **Proposed**, or **Superseded**.

**What was read.** Folder and file names were listed (two levels deep); raw data files were not opened. Counts come from READMEs, reports, validation and manifest JSON files, the source inventory in `<preprocessing-repo>`, and the vault notes. All counts are aggregates.

## Cohorts at a glance

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| Role here | Earlier-build comparison only | Analysed cohort | Analysed cohort |
| Study year | Not restated here | July 1, 2024 to June 30, 2025 | Decisions June 30, 2025 to June 30, 2026 |
| Raw form | Historical CSV exports | Quarterly platform exports (BL, Q1–Q4), plus `IHS_2024` server pulls | Server: nightly cumulative exports, daily API snapshots, agent files, `IHS_2025` database pulls |
| Wearables | Fitbit, Garmin, Apple Health; SensorKit | Fitbit, Garmin, Apple Health | Fitbit, Garmin, Apple Health; Oura (unmapped) |
| Participants in current hourly file | n/a | 931 | 928 |
| Hourly file UTC span | n/a | 2023-11-18 14:00 to 2025-07-07 05:00 | 2024-04-03 07:00 to 2026-07-06 10:00 |

[src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "File identity and row contract"; `<shared>/README.md` § "November 16, 2026 — 2025 decisions extended through June 30, 2026"; `<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md`]

The cohort year is a label, not a calendar filter. Both hourly files contain pre-study (baseline) records, and the 2025 file starts in April 2024 because some participants' devices synced older history (Garmin epochs from April 4, 2024). [src: `<shared>/README.md` § "Initial full-period Garmin recovery — November 13, 2026 (historical)"]

Decision files cover more people than the hourly files: 940 participant IDs in 2024 and 1,067 in 2025, against 931 and 928 in the hourly tables. [src: `<shared>/README.md` § "Read these limitations before analysis"]

## 2023 cohort

Used only to compare against earlier builds; nothing from 2023 enters the 2024 or 2025 hourly files.

| Folder in `<raw2023>` | Contents (names only) |
|---|---|
| `InterventionMessages/` | 2021/2022 pre-internship messages, 2022 internship messages, a 2022–23 message coding sheet "FOR ANALYSIS", a 2023 pilot generative-AI message sheet, `notification_sent_2023.csv`, `notification_rating_2023.csv` |
| `Mood/` | Daily-average and timestamped mood files; baseline, Q1, Q2–Q3 and Q4 mood files |
| `SensorKit/` | Ambient light, keyboard usage, message and phone usage, visits, retention lists, a dictionary, and 2022/2023 "data by type" summaries |
| `SubjectList/` | `IDlist.csv`, `ProgramList.csv` |
| `Survey Data/` | 2023 survey exports, GME variables, program codes |
| `Wearable/` | `Combined/` (daily step, sleep and RHR products from an earlier R pipeline), `Fitbit/`, `Garmin/`, `GarminNew/`, `HealthKit/`, `Scripts/` (R aggregation scripts) |

[src: file listing of `<raw2023>`]

The preprocessing package's source inventory lists 2023 Fitbit, Garmin and Apple Health steps, sleep, heart rate, RHR and HRV as present, with the legacy combined products as QA references only. [src: `<preprocessing-repo>/inventory/source_inventory.md` § "Source roots", § "Core year × device × stream coverage"]

A decision-level 2023 build with next-24-hour rewards exists in `<prior-data>/dfEvents2023.csv` (245,307 decisions, 1,338 participants, send probability 0.5). The 2023 message pool differs from the 2024/2025 pool, so 2023 is not a reliable test of findings about specific 2024/2025 messages. [src: analyst working notes dated 2026-11-22, not checked against the file; unverified]

## 2024 cohort

### 2024 folder layout

| Folder in `<raw2024>` | Contents |
|---|---|
| `Wearable/Fitbit/` | `Daily/` (daily RHR by quarter, daily sleep logs by quarter, `dailyData`), `Intraday/` (steps, HR, HRV, detailed sleep logs, activity logs), `Devices/`, a note |
| `Wearable/Garmin/` | `Daily/` (daily summary BLQ1Q2 and Q3Q4; activity, HRV, Move IQ, sleep, stress and user-metric summaries for BLQ1Q2), `Intraday/` (epochs, HR samples, HRV samples, naps, sleep score, sleep stages, stress and body battery, all BLQ1Q2), a note |
| `Wearable/HealthKit/` | `Daily/` (daily steps, daily activity summary, Apple Watch daily RHR), `Intraday/` (minutely and hourly steps, HR by quarter, HRV, sleep, exercise time), `AppleWatchDevices_2024.csv` |
| `Mood/` | `Mood_2024_cohort_withTimestamp.csv`, `Mood_2024_cohort_dailyAverage.csv`, `raw/` (`Mood_2024_raw.csv`, `Mood_BL.csv`, `MoodQ1.csv`, `MoodQ2.csv`, `Mood_Q3_2024.csv`, `Mood_Q4_2024.csv`), `Script/` (an R preprocessing script), `SpeechSensorSubjects/` (mood for the speech-sensor subset) |
| `Survey Data/` | `IHSdata_2024_07302025.csv`, `IHSdata_2024_ProgramSpecialty_03052926.csv`, `IHS_SurveyData_Dictionary_V9_temp.xlsx`, an R script |
| `InterventionMessages/` | `IHS 2024 Messages List FINAL.xlsx`, `2024 Pre-Internship Messages.xlsx`, `notification_sent_2024cohort_BLQ1Q2.csv` |
| `ParticipantUpdates/` | `ParticipantUpdates_2024.csv` (about 1.8 GB), an R time-zone script and RData file, one other small CSV |
| `SubjectList/` | `IDlist.csv`, `IDlist_plusTZ.csv` |
| `Weather/` | `Weather_IHS_2024.csv` (about 58 MB) |

[src: file listing of `<raw2024>`]

**Export periods.** Files are split by period: `BL` (baseline, before the internship), `Q1` to `Q4` (quarters of the internship year), or combined as `BLQ1Q2` and `Q3Q4`. The `Q3Q4` files hold most of the January to June 2025 follow-up. Several streams (all Garmin intraday files, the notification log) exist locally only as `BLQ1Q2`; their January to June 2025 parts came from the server. [src: file listing of `<raw2024>`; `<vault>/Data Preprocessing/08 Preprocessing Audit 2024 and 2025.md` § "Prioritized findings"; `<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md` § "Remaining processing and assignment recovery"]

**Relocated files.** The original September builds read a 2024 folder that no longer exists; all 19 recorded 2024 raw-input paths in the stream manifests point to absent locations. `<raw2024>` is a relocated and more complete export (it adds later quarters). File-name matches alone do not prove the relocated files are byte-identical to the original build inputs. [src: `<vault>/Data Preprocessing/08 Preprocessing Audit 2024 and 2025.md` § "Prioritized findings", row "Build provenance needs a portable raw inventory"; `<vault>/Data Preprocessing/09 HealthKit Identity and Source Audit.md` § "HK-01-F04 — 2024 remains unresolved"]

### 2024 Fitbit

| Stream | Files in `<raw2024>/Wearable/Fitbit/` | Fields | Notes |
|---|---|---|---|
| Steps | `Intraday/Intraday Steps/fitbit_intraday_steps_2024cohort_{BLQ1Q2,Q3Q4}.csv` | `PARTICIPANTIDENTIFIER, RECORD_DATE, METRIC_VALUE` | Minute-level, **positive events only**: minutes with zero steps are absent, so a zero is never recorded |
| Heart rate | `Intraday/Intraday HR/fitbit_intraday_HR_2024cohort_{BL,Q1,Q2,Q3,Q4}.csv` | same three fields | Point samples, local wall time |
| Sleep | `Intraday/Intraday SleepDetailedLogs/fitbit_SleepDetailedLogs_2024cohort_{BL..Q4}.csv`; `Daily/daily_SleepLogs/fitbit_SleepLogs_2024cohort_{BL..Q4}.csv` | detailed: `SLEEPLOGDATE, TYPE, STARTDATE, ENDDATE, VALUE (stage), MODIFIEDDATE`; daily log: totals such as `MINUTESASLEEP`, `TIMEINBED`, stage minutes, `ISMAINSLEEP`, `LOGTYPE` | Detailed stage intervals are primary; daily logs validate totals. The stage export includes short-wake records (`ShortSleepLevel` / `wake`) |
| Resting HR | `Daily/daily_RHR/fitbit_RHR_2024cohort_{BL..Q4}.csv` | `RECORD_DATE, RESTINGHEARTRATE` | One value per day (date only) |
| Daily data | `Daily/dailyData/fitbit_dailydata_2024cohort_{BLQ1Q2,Q3Q4}.csv` | calories, distance, floors, HR zone minutes, activity minutes, steps, `RESTINGHEARTRATE`, `HEARTRATEINTRADAYMINUTECOUNT`, breathing rate, daily HRV RMSSD, SpO2, skin temperature | Used for reconciliation checks only |
| HRV | `Intraday/Intraday HRV/fitbit_intraday_HRV_2024cohort_{BL,Q1Q2,Q3Q4}.csv` | `RECORD_DATE, RMSSD, COVERAGE, HF, LF` | Unused |
| Activity logs, devices | `Intraday/Intraday ActivityLogs/...`, `Devices/fitbit_devices_2024cohort_{BLQ1Q2,Q3Q4}.csv` | workouts; device lists | Unused |

[src: file listing of `<raw2024>`; `<preprocessing-repo>/inventory/source_inventory.md` §§ "2024 · fitbit · steps", "· sleep", "· heart_rate", "· resting_heart_rate", "· hrv"; `<vault>/Data Preprocessing/18 Expanded Year Sleep and Coverage Audit.md` § "Fitbit sleep: short wakes were counted as sleep"]

**Timestamps.** Fitbit records are local wall-clock times with no offset or time zone. Fitbit does not record a time zone, so the UTC hour depends on the clock assigned from other sources. [src: `<preprocessing-repo>/inventory/source_inventory.md` § "2024 · fitbit · heart_rate" ("Point samples are local-naive"); `<vault>/Data Preprocessing/11 RHR Timing and Source Coverage Audit.md` § "Record timestamps and the cutoff" (Fitbit RHR exports give dates and values only)]

**Export clock in the follow-up file.** The `Q3Q4` step and HR exports appear to carry winter labels one hour behind: the reviewed rule adds one hour to follow-up labels before March 9, 2025 at 02:00 and leaves later labels unchanged. The original extraction SQL was not found. Detail and status are in [clocks and time zones](03-clocks-and-time-zones.md). [src: `<vault>/Data Preprocessing/15 Fitbit Transition and HealthKit Garmin Recovery.md` § "Fitbit: direction is better supported; transition remains a diagnostic"; `<shared>/Hourly_FullYear_20261115/README.md` § "Sources and processing", item 4]

### 2024 Garmin

| Stream | Files in `<raw2024>/Wearable/Garmin/` | Fields | Notes |
|---|---|---|---|
| Steps | `Intraday/garmin_epochsummary_2024cohort_BLQ1Q2.csv` | `STARTTIMEINSECONDS, STARTTIMEOFFSETINSECONDS, DURATIONINSECONDS, ACTIVITYTYPE, STEPS, ...` | 15-minute epochs (at most 900 s) with explicit zeros; one row per activity component, so several rows can share an interval |
| Heart rate | `Intraday/garmin_heartrate_2024cohort_BLQ1Q2.csv` joined to `Daily/daily summary/garmin_dailysummary_2024cohort_{BLQ1Q2,Q3Q4}.csv` | samples: `SUMMARYID, OFFSETINSECONDS, HEARTRATE`; anchor: daily summary start | Sample time = daily summary start + sample offset |
| Sleep | `Intraday/garmin_sleepstage_...`, `Intraday/garmin_nap_...`, `Daily/garmin_SleepSummary_...` (all BLQ1Q2) | stages `SUMMARYID, START/ENDTIMEINSECONDS, SLEEPLEVEL`; summaries with `DURATIONINSECONDS`, deep/light/REM/awake/unmeasurable seconds, `VALIDATION`, `INSERTEDDATE` | Several summary versions per night are common |
| Resting HR | `Daily/daily summary/garmin_dailysummary_2024cohort_{BLQ1Q2,Q3Q4}.csv` | `RESTINGHEARTRATEINBEATSPERMINUTE`, `CALENDARDATE`, start and duration | Zeros are invalid |
| Other | activity, HRV, Move IQ, stress, user-metric summaries; HRV samples; sleep score; stress and body battery samples | | Unused |

[src: file listing of `<raw2024>`; `<preprocessing-repo>/inventory/source_inventory.md` §§ "2024 · garmin · steps", "· sleep", "· heart_rate", "· resting_heart_rate"; `<vault>/Data Preprocessing/16 Garmin Boundary Recovery and HealthKit UTC Correction.md` § "Transfer and source identity"]

**Timestamps.** Garmin stores absolute time (epoch seconds, UTC) plus the watch's offset in seconds. The UTC instant is reliable; the offset is occasionally malformed (for example −21,540 s, i.e. −5 h 59 min, for fewer than 10 participants). [src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `raw_query` and `corrected_anchor_sql`; `<vault>/Data Preprocessing/16 Garmin Boundary Recovery and HealthKit UTC Correction.md` § "Why the additional 20 rows are separated"]

**Coverage gap in local files.** Local Garmin intraday files are `BLQ1Q2` only; January to June 2025 Garmin epochs, HR, sleep and daily summaries came from the server (next section). The local Q3Q4 daily summary is the only local Garmin follow-up file. [src: file listing of `<raw2024>`; `<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md` § "Earlier Garmin-completed candidate (preserved)"]

### 2024 Apple Health (HealthKit)

| Stream | Files in `<raw2024>/Wearable/HealthKit/` | Fields | Notes |
|---|---|---|---|
| Steps (minutely) | `Intraday/intraday steps/minutely steps/healthkit_intraday_steps_2024cohort_{BL,Q1,Q2,Q3,Q4}.csv` | `STARTDATE, RECORD_DATE, VALUE` (+ `DEVICEMODEL, SOURCEPRODUCTTYPE` in some files) | Raw intervals; the September build read only these |
| Steps (hourly, daily) | `.../hourly steps/healthkit_intraday_hourly_steps_...`, `Daily/dailly_steps/...` | | Pre-aggregated; QA reference only |
| Heart rate | `Intraday/intraday HR/healthkit_intraday_HR_2024cohort_{BL,Q1..Q4}.csv` | `STARTDATE, RECORD_DATE, VALUE, SOURCEPRODUCTTYPE` | |
| Sleep | `Intraday/intraday sleep/hk_Sleep_2024cohort.csv` | category intervals with `SOURCEPRODUCTTYPE` | The original build read `.tsv` files that are no longer present; this CSV has product type but no writing-source ID or metadata |
| Resting HR | `Daily/daily_RHR/HealthKit_daily_rhr_AppleWatch_2024cohort.csv` | `STARTDATE, RECORD_DATE, VALUE, SOURCEPRODUCTTYPE` | |
| Other | HRV, exercise time, daily activity summary, `AppleWatchDevices_2024.csv` | | Unused |

[src: file listing of `<raw2024>`; `<preprocessing-repo>/inventory/source_inventory.md` §§ "2024 · healthkit · steps", "· sleep", "· heart_rate", "· resting_heart_rate"; `<preprocessing-repo>/scripts/build_compact_ihs.py`, `raw_query`; `<vault>/Data Preprocessing/09 HealthKit Identity and Source Audit.md` § "Cross-review with Opus"]

**Timestamps.** Each 2024 Apple Health record carries an explicit UTC offset on its start (and end) time. [src: `<vault>/Data Preprocessing/11 RHR Timing and Source Coverage Audit.md` § "Record timestamps and the cutoff"; `<vault>/Data Preprocessing/15 Fitbit Transition and HealthKit Garmin Recovery.md` § "HealthKit: rebuild from actual samples"]

**What the local files lack.** No writing-app identifier, no sync identifier or version, and no deletion records; device model only. Repeated payloads with different sample IDs therefore cannot be resolved from local files, and a "phone" record may come from an app (Garmin Connect, Oura and others) writing on the phone. [src: `<vault>/Data Preprocessing/09 HealthKit Identity and Source Audit.md` §§ "HK-01-F03", "HK-01-F04"; analyst board post of 2026-11-17 stored as `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/post_2024_server_run_20261117.py`]

**Status of use.** In the current 2024 hourly file, Apple Health columns come entirely from the `IHS_2024` server rebuild (below), not from these local files. Values the old build had placed on rows without a UTC time are archived, not used. **Applied** (Stage C, November 17). [src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` § "Checks and exceptions"; `<shared>/audit/CollaborativeAudit/Codex/Hourly2024StageC/assemble.py`]

### 2024 server pulls from IHS_2024

Several gaps were filled with read-only pulls from the `IHS_2024` schema on the study server (run by Drew; aggregate commands; returned through a private repository). All are 2024-cohort follow-up or baseline, not 2025-cohort data.

| Pull (date returned) | Tables and scope | Size | Used in current file? |
|---|---|---|---|
| Garmin follow-up (Nov 14) | Epoch summaries, HR samples, daily summaries, sleep summaries and stages, sleep scores; Jan–Jun 2025 with Dec/Jul padding; naps verified empty | 1,835,555 epochs; 23,435,081 HR samples; 22,944 daily summaries; 14,248 sleep summaries; 284,332 stage records; 36,351 scores | **Applied** (merged Nov 15, carried into Stage C) |
| Garmin boundary (Nov 14) | `GARMINEPOCHSUMMARY`, 29-participant group, Dec 30, 2024 to Jan 3, 2025 UTC | 15,298 rows / 27 participants | Diagnostic for the year-end boundary. The November 15 release says the reviewed Garmin and Apple Health boundary fixes are included; which transfer supplied each value is unverified |
| Native HealthKit follow-up (Nov 15) | `HEALTHKITSAMPLES_{STEPS,HEARTRATE,RESTINGHEARTRATE,SLEEPANALYSISINTERVAL}`, deletion table and type map; 931-person cohort; Dec 30, 2024 to Jul 7, 2025 | Steps 10,024,635 records / 560 people; HR 27,429,844 / 390; RHR 183,908 / 388; sleep 890,460 / 293; 3,288,417 deletion entries | **Superseded** for hourly values by the whole-range server rebuild below |
| HealthKit server rebuild "2024 v3" (Nov 17) | Same four streams rebuilt on the server by the 2025 rules, requested for the whole range of the published 2024 file; returned as hourly components with diagnostics and holds | Hourly rows: steps 5,358,517; HR 2,350,160; sleep 432,825; RHR (local days) 137,413; 419 chunks; HealthKit hours span 2024-03-31 16:00 to 2025-07-07 04:00 UTC | **Applied** (Stage C) |
| Baseline Fitbit steps (Nov 16) | Hourly sums of `IHS_2024.FITBIT_STEPS`, April 1 to July 1, 2024 | 159,244 hours / 260 people | **Applied** (152,179 hours placed in Stage B) |
| Phone step parts (Nov 18 UTC) | Phone-class steps split by writing app for people with app copies | 43 people in 2024 | **Applied** (Stage C) |
| Full-year notification log (Nov 16) | Notification attempts | 186,166 rows, April 19, 2024 to July 1, 2025 | Used for decisions (see [decisions and probabilities](06-decisions-and-probabilities.md)) |

[src: `<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md` §§ "Native HealthKit transfer — complete and verified November 15", "Earlier Garmin-completed candidate (preserved)"; `<vault>/Data Preprocessing/16 Garmin Boundary Recovery and HealthKit UTC Correction.md` § "Transfer and source identity"; `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`source_manifest`, `source_bounds`, `phone`); `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/stage_b/stage_b_summary.json`; `<shared>/README.md` § "Update, November 16, 2026 — 2024 decision table rebuilt from the full-year notification log"]

The server tables keep what the local exports dropped: sample keys, writing source, sync metadata, insertion dates, explicit offsets and deletion records. The "2024 v3" run was requested with the same rules as the 2025 v3 rebuild (tombstones, sync and slot reconciliation, manual entries excluded, native Garmin priority for steps, Oura left out of iPhone hours, UTC hour by record). The returned components match that design; I did not read the server code to confirm every rule (unverified). [src: `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/post_2024_server_run_20261117.py` (board post text); `<shared>/audit/CollaborativeAudit/Codex/Hourly2024StageC/input_checks.json`]

### 2024 Oura and Google Health

No Oura export exists for 2024. Oura data reach the 2024 files only as Apple Health records written by the Oura app on the phone (handled by the phone-step rules). No Google Health data exist for either analysed cohort; the preprocessing package has a separate tester-only Google Health processor that is not registered in the annual builder. [src: `<preprocessing-repo>/inventory/source_inventory.md` §§ "2024 · oura · steps" etc.; `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`phone_subgroups`); `<preprocessing-repo>/docs/GOOGLE_HEALTH_HOURLY.md` (opening section)]

### 2024 mood surveys

| File in `<raw2024>/Mood/` | Use |
|---|---|
| `raw/Mood_2024_raw.csv` | Source of the current (November 17) mood placement: 105,639 scored responses, 885 participants, scores 1–10, local 2024-04-02 10:32 to 2025-07-06 21:55 (UTC 2024-04-02 14:32 to 2025-07-07 01:55) |
| `Mood_2024_cohort_withTimestamp.csv` | Source of the September 30 mood column (same 105,639 reports); **Superseded** as the mood source |
| `Mood_2024_cohort_dailyAverage.csv`; `raw/Mood_BL.csv`, `MoodQ1.csv`, `MoodQ2.csv`, `Mood_Q3_2024.csv`, `Mood_Q4_2024.csv`; `SpeechSensorSubjects/` | Unused by the hourly builds (contents not inspected) |

[src: `<shared>/audit/CollaborativeAudit/Codex/MoodTiming20261117/sources.json`; `<shared>/audit/HourlyMoodPublicationChecks.json` (cohort 2024 `mood_source`, `source_reports`); file listing of `<raw2024>`]

**Timestamps.** Every 2024 scored response has an explicit UTC offset on its completion time (`ENDDATE`), so its UTC instant is known directly. [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md` § "Evidence for the two corrections"; `<shared>/README.md` § "Mood and missing values"]

A push reminder for the mood survey goes out at 8 pm local time; the local completion-hour peak is 20:00 (51.5% of positive rows). [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md` § "Version identity"; design fact stated by Drew, recorded in the analyst notes of 2026-11-16]

Mood timing rules are in [mood timing](05-mood-timing.md).

### 2024 baseline and quarterly surveys

| File in `<raw2024>/Survey Data/` | Contents |
|---|---|
| `IHSdata_2024_07302025.csv` | Participant-level baseline and quarterly questionnaire data (one row per participant, waves in separate columns) |
| `IHSdata_2024_ProgramSpecialty_03052926.csv` | Program and specialty supplement, joined one-to-one by `userid` |
| `IHS_SurveyData_Dictionary_V9_temp.xlsx` | Historical dictionary spanning many years |

Questionnaires span April 2, 2024 to June 30, 2025. Wave end dates are calendar dates with no time zone; no submission history exists for 2024. These feed `<shared>/2024SurveyData.csv` (1,047 participants × 1,052 columns). [src: `<shared>/SurveyDataREADME.md` §§ "Baseline and follow-up waves", "Validation and reproducibility"; `<vault>/Data Preprocessing/06 Survey Data Harmonization.md` § "Files and row units"]

Some 2024 stress and `SLE*` items contain source zeros that may be export defaults; they are retained as is. [src: `<shared>/SurveyDataREADME.md` § "Missingness and checkboxes"]

### 2024 notification log

- `<raw2024>/InterventionMessages/notification_sent_2024cohort_BLQ1Q2.csv` covers only the first part of the year. [src: file listing; `<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md` § "Remaining processing and assignment recovery"]
- The full-year log (186,166 rows, April 19, 2024 to July 1, 2025) came from the server and is the source of the current 2024 decision table. It records notification attempts with their status; it does not record randomizations, so no-send days are inferred. [src: `<shared>/README.md` § "Update, November 16, 2026 — 2024 decision table rebuilt from the full-year notification log"; `<vault>/Data Preprocessing/20 Rebuilt 2024 Decisions and Timezone Probe.md`]
- The original 2024 server code is not available; rules were inferred from the log. Pre-internship messages (April to June 2024) were a separate scheduled series. [src: design facts stated by Drew, analyst notes of 2026-11-16]

Time basis, delivery status and decision construction are in [decisions and probabilities](06-decisions-and-probabilities.md).

### 2024 participant updates and time-zone history

`<raw2024>/ParticipantUpdates/ParticipantUpdates_2024.csv` (about 1.8 GB) is a log of participant record updates. It provides an hourly history of the phone's named time zone and reported offset. Its timestamps have no time zone and are **assumed to be UTC** (an assumption recorded in every build; the November 16 clock audit found that Eastern phones' daylight-saving switch times fit only UTC, see [clocks and time zones](03-clocks-and-time-zones.md#the-phone-time-zone-history)). It also holds the message statistics (`Metric_*` custom fields) used to tailor messages. **The file also contains direct identifiers; it was not opened for this note** and only its statistic and time-zone fields have been read in earlier work. [src: `<shared>/Hourly_Rebuilt_20260929/README.md` (time-zone paragraph); `<shared>/README.md` § "Calendar and timestamps"; `<vault>/Results and Document Compilation/Data Shown vs Not, by Statistic Tier.md` § "How the tiers were rebuilt"]

The September build converted it into `participant_update_states_2024.csv` (one row per update with participant, update time, zone name and reported offset) inside the preprocessing build folder. The 2024 clock map uses this history first (priority 20), with device evidence below it (priority 10); it is never extrapolated backward before the first update. Against each phone's own hourly zone history, 99.9% of single-row hours in the 2024 file carry the phone's offset. [src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `make_clocks`; `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: how much the roster zone is contradicted..."] Detail in [clocks and time zones](03-clocks-and-time-zones.md).

### 2024 subject list and account exclusions

`<raw2024>/SubjectList/IDlist.csv` links app accounts to study IDs; `IDlist_plusTZ.csv` adds a time-zone field (use in builds unverified). All 56 account IDs whose `STUDY_PARTICIPANT_ID` is the literal `NA` marker are excluded from the 2024 analysis files (76,651 hourly rows across 17 accounts removed on September 30, 2026). **Applied.** [src: `<shared>/README.md` § "Accounts excluded from the current analysis"]

### 2024 weather

`<raw2024>/Weather/Weather_IHS_2024.csv` exists. It is not used in the hourly files. A separate app weather feed for 2024 was supplied on November 22, 2026 for use as a control variable outside the hourly files. [src: file listing of `<raw2024>`; analyst notes of 2026-11-22 (unverified against files)]

## 2025 cohort

### 2025 server and local mirror layout

The 2025 study ran on the study server, with an Oracle database (`IHS_2025` schema). `<server2025>` is a local mirror of two parts of it:

| Folder | Contents (names only) |
|---|---|
| `data/nightly/` | Cumulative nightly exports per device and stream (table below), `nightly_mood.csv`, `nightly_survey.csv`, `study_participants.csv` |
| `data/api/` | Daily API snapshots; only `2026-06-19/` and `2026-06-20/` are mirrored (13 files each) |
| `data/participants/` | 357 daily roster snapshots, `2025-06-30` to `2026-06-21` |
| `data/custom_fields/` | 359 daily custom-field files, `2025-06-27` to `2026-06-21` |
| `agents/Decisions/` | 709 daily files: `<date>Decisions.csv` and `<date>Messages.csv`, June 30, 2025 to June 19, 2026 |
| `agents/Master/` | `MessageList.csv`, `MessageHistory.csv`, participant and tester lists, `TrainParticipantTimezones.csv`, the server's own `dfHourly.csv`, `dfNightlyHourly.csv`, `dfEvents.csv`, `Rewards.csv` |
| `agents/Probabilities/`, `Rewards/`, `Schedules/` (51 weekly folders), `Ledgers/`, `Logs/`, `Timings/`, `Testers/` | The online agents' probability, reward, schedule and training files |

[src: file listing of `<server2025>`; analyst notes on server access, 2026-11-16]

The mirror holds no time-zone history; the server database has none either (`STUDYPARTICIPANTS` has one zone per participant, plus a withdrawal date the 2024 schema lacks). [src: analyst notes of the 2026-11-16 server probe; `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." ("the database has no zone-history table")]

### 2025 nightly exports

| File in `<server2025>/data/nightly/` | Representation |
|---|---|
| `fitbit_nightly_steps.csv` | Positive-only minute history (`RECORD_DATE, METRIC_VALUE`) |
| `fitbit_nightly_hr-003.csv` | Point samples |
| `fitbit_nightly_sleep.csv` | Sleep log summaries (`STARTDATE, ENDDATE, MINUTESASLEEP, ...`, `ISMAINSLEEP`, `MODIFIEDDATE`); no stages |
| `fitbit_nightly_rhr.csv` | Daily RHR |
| `garmin_nightly_steps.csv` | **Daily** summaries (steps per day, RHR and other daily fields), not epochs |
| `garmin_nightly_hr-001.csv` | HR samples (`SUMMARYID, OFFSETINSECONDS, HEARTRATE`) |
| `garmin_nightly_sleep.csv` | Sleep summaries with `VALIDATION`, `INSERTEDDATE`, `TOTALNAPDURATIONINSECONDS`; no stages |
| `garmin_nightly_summary.csv`, `garmin_nightly_activity_summary.csv` | Daily summaries (RHR source); activity summary |
| `apple_nightly_steps-004.csv` (about 9.6 GB), `apple_nightly_hr-005.csv` (about 28 GB), `apple_nightly_sleep.csv`, `apple_nightly_rhr.csv` | Apple Health samples with `HEALTHKITSAMPLEKEY`, source name/version/product type, device fields, `METADATA`, `INSERTEDDATE` |
| `oura_nightly_activities.csv`, `oura_nightly_hr.csv`, `oura_nightly_sleep.csv` | Oura daily activity, HR points, sleep summaries |
| `nightly_mood.csv`, `nightly_survey.csv` | Mood scores; all questionnaire answers |
| `study_participants.csv` | Roster snapshot, one `TIMEZONE` per participant |

[src: file listing of `<server2025>`; `<preprocessing-repo>/inventory/source_inventory.md` §§ "2025 · fitbit · steps" through "2025 · oura · hrv"]

**Timestamps.** Nightly Apple Health and Fitbit times are local wall-clock times with **no offset**; the export dropped the offsets the database keeps. Garmin is epoch seconds plus the watch offset, so it is absolute. [src: `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." ("2025 times are local. Apple Health and Fitbit records carry no offset ... Garmin is absolute"); analyst notes, server probe of 2026-11-16]

**End of the local snapshot.** The mirrored nightly files end around June 19–20, 2026: the Fitbit nightly sleep log ends June 19 at 20:03, scored nightly mood ends June 20, 2026, and in the published 2025 hourly file Fitbit, Garmin heart rate and mood stop on June 20, 2026 while decisions run to June 30. [src: `<vault>/Data Preprocessing/26 Validated Fitbit and Garmin Sleep Fixes.md` § "Coverage and merge limits"; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md` § "Evidence for the two corrections"; `<vault>/Audit Decision Summary 2026-11-14.md` (scan of the published 2025 file, November 17)]

### 2025 API snapshots

`<server2025>/data/api/<date>/` holds day-specific API records: `apple_api_{steps,hr,sleep,rhr}.csv`, `fitbit_api_{steps,hr,sleep,rhr}.csv`, `garmin_api_{steps,hr1,hr2,sleep}.csv`, `api_mood.csv`. Common fields: `participantIdentifier, type, value, startDate, startDateOffset, observationDate, observationDateOffset, insertedDate, modifiedDate, dataSource`. [src: file listing; `<preprocessing-repo>/inventory/source_inventory.md` § "2025 · fitbit · steps" (header)]

- Apple Health and Garmin API records carry a per-record offset. Fitbit API offsets are placeholders (often zero) and are not UTC evidence. [src: analyst notes of 2026-11-16; `<preprocessing-repo>/src/mobile_health_preprocessing/devices/fitbit/heart_rate.py` (`api_time_rule`); `.../devices/fitbit/steps.py` (`api_time_rule`)]
- Fitbit API step snapshots contain explicit zero-minute grids, unlike the positive-only nightly file. Garmin `hr1` is activity-detail HR and `hr2` daily HR. [src: `<preprocessing-repo>/inventory/source_inventory.md` §§ "2025 · fitbit · steps", "2025 · garmin · heart_rate"]
- Only two days (June 19–20, 2026) are mirrored locally; the server's API folders start May 1, 2026. API rows therefore matter only for those days in the local builds. [src: analyst notes of the 2026-11-16 server probe]

### 2025 server database tables pulled for rebuilds

| Table(s) in `IHS_2025` | Used for | Status in current 2025 file |
|---|---|---|
| `HEALTHKITSAMPLES_{STEPS,HEARTRATE,RESTINGHEARTRATE,SLEEPANALYSISINTERVAL}` with the deletion table | "v3" Apple Health rebuild, March 1, 2025 to July 8, 2026 UTC, 928 people; offsets stored as `TIMESTAMP WITH TIME ZONE` | **Applied** |
| `HEALTHKITSTATISTICS_*` | Offset evidence and diagnostics only | Not used for values |
| `GARMINEPOCHSUMMARY` | Garmin hourly steps (epochs April 4, 2024 to July 6, 2026) | **Applied** |
| `GARMINSLEEPSUMMARY` (validated parents) and Garmin stage tables | Revision-aware Garmin sleep | **Applied** |
| `FITBITSLEEPLOGS`, `FITBITSLEEPLOGDETAILS` | Fitbit stage-level sleep; stage times are stored with `+00:00` but are wall-clock labels | **Applied** (with exceptions) |
| `ANALYTICSEVENTS_NOTIFICATIONSENT` | Message attempts and the 8 pm `MoodReminder` sends (UTC) | Decisions; clock evidence |
| Push-opened events | Retrieved | Unused |
| `SURVEYQUESTIONRESULTS` (mood times) | UTC completion instant of each mood answer | **Applied** (mood timing) |
| `STUDYPARTICIPANTS` | One zone per participant; withdrawal date | Clock fallback |

[src: `<vault>/Data Preprocessing/30 Shared Query HealthKit Full Rebuild.md` § "Execution and coverage"; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Sources and reviewed dispositions"; `<shared>/README.md` § "Initial full-period Garmin recovery — November 13, 2026 (historical)"; `<shared>/audit/CollaborativeAudit/Codex/HourlyMerge20261117/reconcile_sleep.py` (comment on Fitbit `+00` labels); `<shared>/audit/CollaborativeAudit/Codex/MoodTiming20261117/sources.json`; analyst notes of 2026-11-16]

### 2025 Fitbit

- **Steps:** nightly positive-only minutes plus the two mirrored API days. No offset anywhere. [src: `<preprocessing-repo>/inventory/source_inventory.md` § "2025 · fitbit · steps"]
- **Heart rate:** nightly samples (read through a cached, validated sample table) plus API. The September 29 reconciliation corrected the API occurrence field. [src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `raw_query`; `<preprocessing-repo>/README.md` § "Documentation"]
- **Sleep:** nightly log summaries (no stages); stage records came later from `FITBITSLEEPLOGDETAILS`. [src: `<preprocessing-repo>/src/mobile_health_preprocessing/devices/fitbit/sleep.py`, `_nightly_api_query`; `<vault>/Data Preprocessing/26 Validated Fitbit and Garmin Sleep Fixes.md`]
- **RHR:** nightly daily values plus API (nightly preferred). [src: `<preprocessing-repo>/src/mobile_health_preprocessing/devices/fitbit/resting_heart_rate.py`]
- **Clock:** no source holds a Fitbit offset (database tables, nightly, API, sleep-log modified dates and the custom field for last sync were all tested). Fitbit follows the phone's clock in 98.5% of testable weeks. [src: `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." (Fitbit paragraph); analyst notes of 2026-11-16]
- **HRV:** absent from the 2025 exports. [src: `<preprocessing-repo>/inventory/source_inventory.md` § "2025 · fitbit · hrv"]

### 2025 Garmin

- **Steps:** the nightly file has daily totals only. Hourly steps come from `GARMINEPOCHSUMMARY` pulls (November 11 and 13); before that only the June 2026 API intervals were available and daily totals were never spread across hours. [src: `<shared>/Hourly_Rebuilt_20260929/README.md` (Garmin paragraph); `<shared>/README.md` §§ "Previous Garmin recovery — November 11, 2026", "Initial full-period Garmin recovery — November 13, 2026 (historical)"]
- **Heart rate:** nightly samples joined to daily summary IDs, plus API `hr1`/`hr2`. [src: `<preprocessing-repo>/inventory/source_inventory.md` § "2025 · garmin · heart_rate"]
- **Sleep:** nightly summaries (several versions per night; validation labels); stages from the database. Untimestamped nap totals (`TOTALNAPDURATIONINSECONDS`) have no occurrence time. [src: `<preprocessing-repo>/inventory/source_inventory.md` § "2025 · garmin · sleep"; `<shared>/README.md` § "Sleep"]
- **RHR:** embedded in both the nightly summary and nightly steps daily-summary files; no dedicated API RHR. [src: `<preprocessing-repo>/inventory/source_inventory.md` § "2025 · garmin · resting_heart_rate"]
- **Timestamps:** epoch seconds plus offset (absolute). Offsets that are not quarter-hour multiples are flagged nonstandard; fewer than 10 participants have half-hour or quarter-hour clocks. [src: `<shared>/README.md` § "Previous Garmin recovery — November 11, 2026"]

### 2025 Apple Health (HealthKit)

- **Nightly files** carry sample key, source name/version/product type, device fields, metadata and insertion date, but times are local wall time with no offset. [src: `<preprocessing-repo>/inventory/source_inventory.md` § "2025 · healthkit · steps" (header); `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..."]
- **Database tables** keep the true offset on every record, deletion records ("tombstones"), sync identifiers and versions, and writing source. These were used for the v3 rebuild (March 1, 2025 onward). [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` § "Sources and reviewed dispositions"]
- **Known raw-source problems** (2025 export, found November 13): repeated synchronization copies and older versions (387,553 multi-version phone sync IDs across 37 participants), coarse summaries duplicating finer watch records, and app-written records (Oura 4,179,729 raw step records / 42 people; Garmin Connect 516,793 / 48; smaller apps) classed as "phone" because the classifier reads product-type text. [src: `<vault>/Data Preprocessing/09 HealthKit Identity and Source Audit.md` §§ "HK-01-F01" to "HK-01-F03"]
- **HRV:** absent. [src: `<preprocessing-repo>/inventory/source_inventory.md` § "2025 · healthkit · hrv"]

### 2025 Oura and Google Health

Oura nightly files exist (daily activity with five-minute class codes, HR points, sleep summaries with five-minute phases and nightly HRV). They have no hourly mapping and there is no Oura column; Oura steps enter only as Apple Health phone-class records written by the Oura app, governed by the iPhone-first rule (see [the hourly files note](02-hourly-files.md#apple-health-steps)). No Google Health data exist. [src: `<preprocessing-repo>/inventory/source_inventory.md` §§ "2025 · oura · steps" to "2025 · oura · hrv"; `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." (Oura decision, November 16)]

### 2025 mood surveys

| Source | Contents | Time basis |
|---|---|---|
| `<server2025>/data/nightly/nightly_mood.csv` | 89,252 scored responses (scores 1–10), 864 participants, local 2025-03-18 09:13 to 2026-06-20 00:13 | Wall time on the phone's clock, no offset |
| `<server2025>/data/nightly/nightly_survey.csv` | All questionnaire answers including `Daily_Mood` records; source of `<shared>/2025SurveyResponseHistory.csv` (372,037 rows) | `ENDDATE` without a reliable zone |
| `SURVEYQUESTIONRESULTS` mood times (server pull, November 16) | UTC completion instant per answer, matched to every scored response by participant, survey-result key and stored wall time | UTC |
| `api/<date>/api_mood.csv` | Two mirrored days | Not used |

[src: `<shared>/audit/CollaborativeAudit/Codex/MoodTiming20261117/sources.json`; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md` § "Evidence for the two corrections"; `<shared>/SurveyDataREADME.md` § "Files and row units"]

The September 30 build treated the survey `ENDDATE` as UTC, which placed 2025 mood 4 to 8 hours early; this is **Superseded** by the November 17 correction. Mood responses are stored in the database with the phone's own offset. Detail in [mood timing](05-mood-timing.md). [src: `<shared>/README.md` § "Mood and missing values"; `causal/config/data_notes.yaml`; `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." (consolidated pull paragraph)]

The 8 pm `MoodReminder` push is sent on each participant's own clock and was used as clock evidence. [src: `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." (reminder paragraph)]

### 2025 baseline and quarterly surveys

`nightly_survey.csv` holds every questionnaire submission (baseline and quarterly waves, daily mood, comments, feedback, administration). Waves are identified by `SURVEYRESULTKEY` and phase-specific `interest0`–`interest4`; repeated submissions keep the latest whole questionnaire. The history spans March 18, 2025 to June 20, 2026. Birthdate questions (1,061 rows) are excluded from shared files. Wave dates are UTC dates of completion. These feed `<shared>/2025SurveyData.csv` (1,162 participants × 1,052 columns). [src: `<shared>/SurveyDataREADME.md` §§ "Baseline and follow-up waves", "Birthdates, age and free text"]

### 2025 decisions, messages and notifications

- `<server2025>/agents/Decisions/<date>Decisions.csv` (one row per scheduled decision: participant, timestamp label, selected agent, action) and `<date>Messages.csv` (one row per message to send: notification ID, core message, arm, domain). Locally 355 Decisions and 354 Messages files, June 30, 2025 to June 19, 2026 (the July 14, 2025 Messages file is missing). June 20–30, 2026 files were later retrieved from the server. [src: `<vault>/Data Preprocessing/22 Validated 2025 Message Matches and Window Timing.md`; `<shared>/README.md` § "November 16, 2026 — 2025 decisions extended through June 30, 2026"]
- The decision file's time is a date label (midnight UTC), not a send time; the server writes the day's decisions about four minutes before the first message, and messages go out at 19:00 or 20:00 UTC (3 pm Eastern). [src: `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..." (decision times and later corrections)]
- Notification attempts and their status (`Success`, `NoRegisteredMobileDevice`, `NoAssociatedUser`, `PastNotificationEndDate`, `ServiceError`) come from `ANALYTICSEVENTS_NOTIFICATIONSENT` (UTC). [src: `<vault>/Data Preprocessing/23 June Tail and Approved Rebuild Plan.md`]
- Probability files: `agents/Probabilities/{Behavior,Mood,Sleep,Steps}/`. [src: `<vault>/Data Preprocessing/02 Processing and Validation.md` § "Historical decision sources"]

All of this is covered in [decisions and probabilities](06-decisions-and-probabilities.md).

### 2025 participant roster, time zones and custom fields

- `data/nightly/study_participants.csv`: one `TIMEZONE` per participant (the "roster zone"). It is the fallback clock for 2025 and is contradicted on 7.1% of checkable participant-days. [src: `<preprocessing-repo>/scripts/build_compact_ihs.py`, `make_clocks`; `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..."]
- `data/participants/` (357 daily roster snapshots) and `agents/Master/TrainParticipantTimezones.csv`: roster-related files; their use in the hourly builds is unverified (I found no reference in the build code read for this note).
- `data/custom_fields/` (359 daily files): per-participant custom fields, including the message statistics (`Metric_*`) the server used to tailor that day's messages, and a Fitbit last-sync field (tested and rejected as a Fitbit clock). [src: `<vault>/Results and Document Compilation/Data Shown vs Not, by Statistic Tier.md` § "How the tiers were rebuilt"; analyst notes of 2026-11-16]

### 2025 weather

No weather file was found in the local 2025 mirror. Whether a 2025 weather feed exists elsewhere is unverified.

## Message pool and message coding (both cohorts)

| Source | Contents |
|---|---|
| `<raw2024>/InterventionMessages/IHS 2024 Messages List FINAL.xlsx` (and its CSV copy) | The internship message catalogue shared by 2024 and 2025 |
| `<shared>/IHSMessagePool.csv` | Unchanged copy of that catalogue: 1,432 notification variants across 358 core messages, 16 columns (`Notification Identifier`, `Core Message ID`, `Text`, metric and trigger fields, `ApproachName` (strategy), `DataContext`, design metadata) |
| `<server2025>/agents/Master/MessageList.csv` | 2025 server copy; identical IDs, cores, text, metrics and functions, plus `Action`/`Agent` columns |
| `<raw2024>/InterventionMessages/2024 Pre-Internship Messages.xlsx` | Separate pre-internship series; not in the pool |

Both cohorts keep the `Internship2024-...` notification IDs. [src: `<shared>/README.md` § "Shared IHS message pool"]

**Tailoring statistics.** Every message (data or no data) has four variants chosen from one of the domain's nine statistics (average, minimum, maximum over 7 days, 30 days and since the phase began): neutral when missing or zero, low below cut point L, medium, high above H. Data messages also display the number. Cut points are the same in both cohorts, but the tier rule differs at the boundaries (2025: low < L, high ≥ H; 2024: low ≤ L, high > H). The statistic comes from the decision day's custom-field file in 2025 and from the last participant update before 20:00 UTC in 2024. [src: `<vault>/Results and Document Compilation/Data Shown vs Not, by Statistic Tier.md` § "How the tiers were rebuilt"]

**Step statistics with thousands separators.** Step statistics were stored with a comma (for example "12,345"). The 2025 server could not parse them, so 97% of steps messages fell to the neutral variant and steps data messages never displayed data; the 2024 server read the digits before the comma, so 72% of steps messages were framed "low" while displaying the right number. These are facts about what participants saw, not processing choices of ours. [src: `<vault>/Results and Document Compilation/Data Shown vs Not, by Statistic Tier.md` §§ "Verdict", "Sent messages by tier, July–December"]

## Timestamp storage summary

| Cohort | Source | Stored as | Consequence |
|---|---|---|---|
| 2024 | Fitbit steps, HR, sleep (local exports) | Local wall time, no offset | Clock from participant updates; Q3Q4 winter labels shifted (see 03) |
| 2024 | Fitbit RHR | Date only | Attached to the local date |
| 2024 | Garmin epochs, HR, sleep | Epoch seconds (UTC) + watch offset | Absolute; malformed offsets repaired for the local label only |
| 2024 | Apple Health local exports | Local time with explicit offset per record | UTC known per record |
| 2024 | Apple Health server rebuild (v3) | UTC hour per record, with min/max source offset | Placed by UTC |
| 2024 | Mood (`ENDDATE`) | Local time with explicit offset | UTC known |
| 2024 | Participant updates | No zone; assumed UTC | Basis of the 2024 clock (assumption, supported by the daylight-saving switch times) |
| 2024 | Surveys | Calendar dates, no zone | |
| 2025 | Apple Health nightly | Local wall time, no offset | Offset only from database tables |
| 2025 | Apple Health database (v3) | `TIMESTAMP WITH TIME ZONE` | UTC known per record |
| 2025 | Fitbit nightly, API | Local wall time; API offsets are placeholders | No Fitbit offset anywhere |
| 2025 | Fitbit sleep stages (database) | `+00:00` suffix, but wall-clock labels | Not UTC |
| 2025 | Garmin nightly, epochs, sleep | Epoch seconds + offset | Absolute |
| 2025 | API snapshots (Apple, Garmin) | Per-record offset | Two days mirrored |
| 2025 | Mood nightly | Wall time on the phone clock | UTC from `SURVEYQUESTIONRESULTS` |
| 2025 | Notifications, mood reminders | UTC event times | Clock evidence |
| 2025 | Decision files | Midnight UTC date label | Not a send time |
| 2025 | Roster | One named zone per participant | Fallback clock |

[src: sections above; `<vault>/Audit Decision Summary 2026-11-14.md` § "2025 clock: ..."; analyst notes of the 2026-11-16 server probes]

## Raw streams that exist but are unused

None of these enter the hourly files. "Unused" means unused by the builds documented here; some were used for audits or as one-off controls.

| Cohort | Device or source | Unused streams |
|---|---|---|
| 2024 | Fitbit | Intraday HRV (RMSSD, HF, LF, coverage); activity logs (workouts); `dailyData` (calories, floors, distance, HR zone minutes, breathing rate, daily HRV, SpO2, skin temperature; used only for reconciliation); device lists |
| 2024 | Apple Health | HRV; exercise time; daily activity summary (energy, exercise, stand hours); pre-aggregated hourly and daily steps (QA only); Apple Watch device list; all local exports for hourly values after Stage C (audit and archive only) |
| 2024 | Garmin | Stress samples and summaries; body battery; HRV summary and samples; sleep score; Move IQ; user metrics (VO2max); activity summary; daily-summary step totals (reconciliation only) |
| 2024 | Mood | Daily-average file; quarterly raw mood files; speech-sensor subset |
| 2024 | Other | Weather file; `IDlist_plusTZ.csv` time-zone field (unverified) |
| 2025 | Oura | All three nightly files (no hourly mapping, no column) |
| 2025 | Garmin | Activity summary; sleep score fields; untimestamped nap totals (kept in an audit file) |
| 2025 | Fitbit, Apple Health | HRV (absent at source); Apple Health statistics tables (diagnostics only) |
| 2025 | Server | Push-opened events; the server's own `dfHourly.csv`, `dfNightlyHourly.csv`, `dfEvents.csv`; daily roster snapshots (use unverified) |
| 2023 | All | SensorKit (ambient light, keyboard, phone and message usage, visits); everything else, except earlier-build comparisons |

[src: analyst notes of 2026-11-22 (inventory of unused 2024 streams); `<preprocessing-repo>/inventory/source_inventory.md` (2024 headers, 2025 Oura and HRV rows); `<preprocessing-repo>/scripts/build_compact_ihs.py`, `raw_query` (streams read); `<shared>/README.md` § "Sleep" (untimestamped naps); file listings]

## Conflicts between sources and how they were resolved

- **2025 mood time basis.** `<shared>/README.md` § "Mood and missing values" says 2025 `ENDDATE` was interpreted as UTC. The November 17 mood report shows the stored time is wall time on the phone clock and replaces it with the server's UTC instant. The later record wins.
- **2025 mood count.** The September 30 build reports 89,253 source reports including one score of 0; the November 17 mood source has 89,252 scored responses, all 1–10. The difference matches the single zero-score response, which cannot be told apart from the no-response sentinel `Mood = 0` in the hourly file; that this is the explanation is my inference (unverified). [src: `<shared>/audit/HourlyMoodPublicationChecks.json` (`source_zero_scores`); `<shared>/audit/CollaborativeAudit/Codex/MoodTiming20261117/sources.json`]
- **2024 raw paths.** The preprocessing inventory points at the original 2024 folder with `BLQ1Q2` files only; `<raw2024>` is the relocated, more complete export. This note describes `<raw2024>` and flags that original build inputs cannot be proven identical.
- **2024 Apple Health sleep file.** The inventory lists `hk_Sleep_*.tsv`; only a CSV with fewer fields exists in `<raw2024>`. Moot for the current file, whose Apple Health sleep comes from the server rebuild.

## Unverified items

- Exact export date ranges of each 2024 quarterly file (only names were listed).
- Whether `IDlist_plusTZ.csv`, the 2025 `participants/` snapshots and `TrainParticipantTimezones.csv` feed any build.
- That the "2024 v3" server run applied every 2025 v3 rule (requested; returned components consistent).
- Existence of a 2025 weather feed.
- The 2023 decision-level counts (taken from analyst notes, not checked against the file).

## Sources consulted

- `<shared>/README.md`; `<shared>/SurveyDataREADME.md`; `<shared>/Hourly_Rebuilt_20260929/README.md`; `<shared>/Hourly_FullYear_20261115/README.md`; `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` and `Validation2024.json`; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md` and `MoodTimingValidation.json`; `<shared>/audit/HourlyMoodPublicationChecks.json`; `<shared>/audit/CollaborativeAudit/Codex/MoodTiming20261117/sources.json`; `<shared>/audit/CollaborativeAudit/Codex/Hourly2024StageC/` (`input_checks.json`, scripts); `<shared>/audit/CollaborativeAudit/Opus/Hourly2024-build/` (scripts and summaries)
- `<vault>/Data Preprocessing/` notes 02, 06, 08, 09, 11, 15, 16, 17, 18, 20, 22, 23, 26, 30, 31; `<vault>/Audit Decision Summary 2026-11-14.md`; `<vault>/Results and Document Compilation/Data Shown vs Not, by Statistic Tier.md`
- `<preprocessing-repo>/README.md`; `<preprocessing-repo>/inventory/source_inventory.md`; `<preprocessing-repo>/scripts/build_compact_ihs.py`; `<preprocessing-repo>/src/mobile_health_preprocessing/devices/` (Fitbit, Garmin, HealthKit processors); `<preprocessing-repo>/docs/GOOGLE_HEALTH_HOURLY.md`
- File and folder names in `<raw2024>`, `<server2025>`, `<raw2023>`
- `causal/config/data_notes.yaml`
