# Mood timing correction

Until 2026-11-17 the 2025 hourly file placed every mood response 4 to 8 hours early: the nightly survey export stores
the response time as local wall-clock time, and the build had read it as UTC. About 9% of responses that fall in a
decision window landed in the wrong window, mostly the previous day's. The correction, in
`Hourly_MoodCorrected_20261117/`, rebuilds mood in both cohorts from each response's own completion time: for 2025 by
matching every scored response to its UTC completion time in the server's survey tables, for 2024 from the original
export's offset-bearing timestamps. The latest completion in each participant's UTC hour supplies the hourly score.
These are the files the current results use; their independent review is still owed.

## Contents

- [Files and status](#files-and-status)
- [The problem in 2025](#the-problem-in-2025)
- [Why the November 17 rebuild did not fix it](#why-the-november-17-rebuild-did-not-fix-it)
- [2024 before the correction](#2024-before-the-correction)
- [Decision and sequence](#decision-and-sequence)
- [How 2025 responses were matched](#how-2025-responses-were-matched)
- [2024 responses](#2024-responses)
- [Rules](#rules)
- [Counts](#counts)
- [Validation](#validation)
- [What the correction does not change](#what-the-correction-does-not-change)
- [Review status](#review-status)
- [Using the files](#using-the-files)
- [Sources](#sources)

## Files and status

| Cohort | File | SHA-256 | Rows | Base file | Response companion |
|---|---|---|---:|---|---|
| 2024 | `Hourly_MoodCorrected_20261117/dfHourly2024.csv` | `c16bd124c02d42a7366328a812776e47b4b4520dd436178c8b0463cf3ba8bf98` | 7,376,544 | Stage C (`a158a0a9…`) | `MoodResponses2024.csv.gz` (`72bb37ef…`) |
| 2025 | `Hourly_MoodCorrected_20261117/dfHourly2025.csv` | `2df0f3e1131d9e6406abf6e38facfe0e8489f1288d02b6492048bf72396f8fb0` | 8,564,451 | Published November 17 file (`84555a10…`) | `MoodResponses2025.csv.gz` (`b355e49d…`) |

[src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json`]

- Both keep the original 25 columns. Built by Codex and posted 2026-11-17 22:16 [src: `<vault>/Audit Message Board.md`,
  post of 2026-11-17 22:16].
- **Status: Applied** in the sense of these notes: the causal engine reads both files, by Drew's decision of 2026-11-17
  (board post 23:03), ahead of their independent review [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 23:03;
  `<shared>/Rotation-1/Drew's code/causal/config/data_notes.yaml`]. They have **not replaced** the root
  `dfHourly2024.csv` and `dfHourly2025.csv`, which still carry the earlier mood placement
  [src: `<shared>/README.md`, top section "Hourly files for mood analyses — November 17, 2026";
  `<vault>/Data Preprocessing/07 Current Files and Version Register.md`].
- Reproducible scripts and change ledgers: `<audit>/Codex/MoodTiming20261117/` (`sources.py`, `build.py`, `verify.py`)
  [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`].

## The problem in 2025

**Origin.** The 2025 mood column was built from `Daily_Mood` survey records with `ENDDATE` "interpreted as UTC
consistently with that survey export" [src: `<shared>/README.md`, section "Mood and missing values"]. In the nightly
export that time is local wall-clock time: with the phone at −4 to −8 hours, 63% to 70% of responses fall at 20:00 to
21:59 as written (the reminder goes out at 20:00 local), against 1% to 2% if the times were UTC; the API copies of the
same surveys carry `+00:00` [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 13:08 (CLK-02-F10)]. Reading
local time as UTC puts each response 4 to 8 hours early for participants in US zones.

**First finding (SCAN-01-F01).** Claude's fresh scan of the 2025 file (notes dated 2026-11-15, posted 2026-11-16
01:53): raw mood times peak at 20:00, and the raw hour equals the hourly row's **UTC** hour for 88,660 of 89,253 entries
and its local hour for only 225. The 2024 file was correct [src: `<vault>/Audit Message Board.md`, register row SCAN-01-F01
and post of 2026-11-16 01:53].

**Second finding on the November 17 file (SCAN-02-F01, 2026-11-17 17:52).**

- The raw hour equals the row's UTC hour for 82,340 of 89,252 responses and its local hour for 228. Mood sat at 20:00
  UTC, which is 15:00 to 16:00 local for most participants; only 2.4% of responses were at 20:00 to 23:59 local.
- Corrected time (raw local time minus the staged day clock's offset) moves responses 4 hours later (42,589), 5 hours
  (29,654), or 6 to 8 hours (13,446).
- Of 63,430 responses that fall in a main decision window, 5,854 (9.2%) were in a different window than their real time
  gives, 5,795 of them in the previous day's window: a mood reported after the day's message counted toward the
  previous decision.
- By file time a response fell 0 to 2 hours after its decision; by corrected time 5 to 8 hours after (71% of responses).

[src: `<vault>/Audit Message Board.md`, post of 2026-11-17 17:52]

The final correction's own check: across all 89,252 scored 2025 responses, 6,054 belong to a different set of main
decision windows (`main_window_reach_retrospective`) under the old placement than under the corrected hour
[src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json` (`2025_window_membership.old_local_as_utc_vs_corrected_hour`);
`<audit>/Codex/MoodTiming20261117/verify.py`]. The two figures use different denominators (responses in a main window
with a staged-clock estimate, against all scored responses) and different corrected times (staged day clock against
the exact completion time).

The earlier stated count of 89,253 2025 responses includes one response scored 0; the correction uses responses scored
above 0, which is 89,252 [src: `<shared>/README.md`, section "Mood and missing values"; `<audit>/Codex/MoodTiming20261117/sources.py`].

## Why the November 17 rebuild did not fix it

The November 17 rebuild routed mood the same way as Fitbit: UTC = local label minus the approved day-clock offset.
For Fitbit the local label is the true wall clock. For mood the true wall clock had been stored in `time_utc`, and the
local label was derived from that wrong UTC, so the routing reproduced the old placement except where the approved
offset differed from the roster's: 6,885 mood cells moved, the rest stayed [src: `<vault>/Audit Message Board.md`,
posts of 2026-11-17 17:52 and 18:11; `<audit>/Codex/HourlyMerge20261117/build_candidate.py`;
`<audit>/Codex/HourlyMerge20261117/validate_candidate_release.log` (`changes_Mood`)].

Claude's acceptance review of that file checked that mood counts and totals were conserved per participant, not where
the responses sat, although SCAN-01-F01 was Claude's own earlier finding; Claude recorded this at 17:52
[src: `<vault>/Audit Message Board.md`, post of 2026-11-17 17:52]. Codex had separately noticed at 16:52 that 17 mood
points on fractional UTC keys matched no relabelled local hour and that "native stored wall times appear related to the
old assumed UTC", and held them rather than guess [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 16:52].

## 2024 before the correction

2024 mood came from the timestamped mood export, whose completion times carry an explicit offset, so it was placed
correctly [src: `<shared>/README.md`, section "Mood and missing values"]. Claude's measured baseline on the published
2024 file and on Stage B (106,664 positive cells, 885 people): local hour 51.1% at 20:00 and 12.5% at 21:00; UTC hour
25.1% at 00 and 23.9% at 01; share at 20:00 to 21:59 local 62.6% (July to December 2024) and 66.2% (January to June
2025) [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 18:11].

Stage C kept positive mood at its published UTC hour when the key was a whole hour; matched all 59 fractional source
intervals to an exact response time inside the original interval (20 of them belong to the second UTC hour the interval
spans); and kept 832 positive scores on rows without a UTC hour as local-only. After consolidating repeated placements,
positive mood occupied 105,050 rows, against 106,664 before [src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`;
`<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`mood_disposition`, `mood_record_lineage`)].

## Decision and sequence

1. **2026-11-17 18:11, Drew:** "Fix (1), and put on the board the issue, so that when we rebuild 2024, it doesn't also
   create problems." Claude read this as go-ahead for Codex's candidate, Claude's review, then publication on Drew's word
   [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 18:11].
2. **Same post, Claude's staged placement** `<audit>/Opus/Mood2025-placement-20261117/mood_placement_2025.csv.gz`: one
   row per scored response (89,252); UTC = raw local time minus the offset of the staged day clock where its tier is
   approved (reminder hold applied), else the single offset the published file uses for that person and date, else
   none. Status counts: placed by the approved clock 83,762; placed on a clock-change day 1,644; placed by the published
   offset 1,904; held with no offset 1,942 (two-offset phone days). Resulting UTC hours 00 to 03 held 71% of responses,
   as in 2024. Status: **Superseded** by the exact completion times below; it remains an input and cross-check
   [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 18:11; `<audit>/Opus/Mood2025-placement-20261117/stage_summary.json`].
3. **Guard for 2024**, same post: mood in the 2024 rebuild stays at its published UTC hour, is never re-derived from a
   local label, and any candidate of either cohort must show the mood peak at 20:00 local; each release report should
   state, per column, which clock is treated as true [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 18:11].
4. **2026-11-17 22:03 to 22:16, Codex:** instead of a day clock, matched each scored 2025 response to its own UTC
   completion time from the server, which "settles all 1,942 day-clock holds and changes a further 397 proposed hourly
   placements"; rebuilt 2024 mood from the offset-bearing export the same way; wrote the dated pair
   [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 22:03, 22:10, 22:16].
5. **2026-11-17 23:03, Drew:** switch the engine to both mood-corrected files now; review afterwards
   [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 23:03].

## How 2025 responses were matched

**Inputs** [src: `<audit>/Codex/MoodTiming20261117/sources.py`; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json` (`inputs`)]:

- Scored responses: the server's nightly mood file (local mirror), records with result identifier `Daily_Mood`, a score
  above 0 and a completion time (`ENDDATE`, local wall clock). 89,252 records, 864 participants, March 18, 2025 to
  June 20, 2026. The scored nightly snapshot ends June 20, 2026; later timestamps in the server return carry no scores
  [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`].
- Completion times: the server's survey question-result export of mood times, returned in the consolidated batch of
  2026-11-16 (Drew approved the batch and its private-repository route that day). For each response it gives the stored
  local wall time and the UTC end time [src: `<vault>/Audit Message Board.md`, posts of 2026-11-16 16:27 and 16:54;
  `<audit>/Codex/MoodTiming20261117/sources.py`].

**Join.** Participant, survey-result key and the exact stored wall time. The nightly file stores the survey-result key
as a Python bytes representation and the server export as hexadecimal, so the key is normalized explicitly. As a
cross-check, the stored time read with its offset equals the UTC end time on every row
[src: `<audit>/Codex/MoodTiming20261117/sources.py`; `<vault>/Audit Message Board.md`, post of 2026-11-17 16:43].

**Result.** Each of the 89,252 scored responses matched exactly one UTC completion instant; none is unplaced. This
placed all 1,942 responses the day-clock method had to hold, and differs from the day-clock estimate's UTC hour for 397
others [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`; `<vault>/Audit Message Board.md`, post of
2026-11-17 22:10]:

| Day-clock status of the response (Claude's staged table) | Responses | UTC hour differs from the exact completion hour |
|---|---:|---:|
| Placed by an approved day clock | 83,762 | 40 |
| Placed on a clock-change day | 1,644 | 21 |
| Placed by the published offset (roster) | 1,904 | 336 |
| Held, no single offset | 1,942 | all (no estimate) |

[src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json` (`inputs.25_clock`)]

So the approved day clock agreed with the exact completion hour on 99.95% of the responses it placed, while the roster
fallback was wrong on 18% of its responses.

The response's offset (local minus UTC) is the responding phone's clock at that moment; it equalled the same day's
Apple Health record offset on 65,970 of 65,982 responses (99.98%) on days whose phone records show one offset
[src: `<vault>/Audit Message Board.md`, post of 2026-11-16 16:54 (CLK-02-F15)].

## 2024 responses

**Input.** The original 2024 raw mood export, records with result identifier `Daily_Mood` and a score above 0, limited
to participants in the hourly file. Its `ENDDATE` strings carry their own numeric UTC offset (`GMT` read as +00:00) and
sub-second precision, which the parser keeps. 105,639 records, 885 participants, April 2, 2024 to July 7, 2025 (UTC);
every one has an offset and none is unplaced [src: `<audit>/Codex/MoodTiming20261117/sources.py`;
`<audit>/Codex/MoodTiming20261117/sources.json`; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`].

**Checks against Stage C before rebuilding.**

- Every positive Stage C value with a UTC hour has a matching source score in that same hour (0 unmatched)
  [src: `<audit>/Codex/MoodTiming20261117/sources.json` (`2024_unmatched_old`)].
- The 832 local-only positive cells: by local hour and score, 826 match one raw response and 6 match two; every one of
  the 832 has a single candidate UTC hour [src: same (`2024_ambiguous_or_unmatched_local_only`);
  `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json` (`2024_legacy_local_only_candidate_utc_hours`)].

**What changed.** No mood value at any existing UTC hour changed (none removed, none newly filled, no different score).
The 832 local-only responses were placed at their UTC hour: 96 needed a new UTC row; by the counts (104,218 positive
UTC rows in Stage C plus 96 equals 104,314), the other 736 duplicated responses already placed at a UTC row. No old row
without UTC still carries mood. At mood hours the respondent's clock now supplies the local label: 2 blank labels
supplied, 127 corrected, 14 rows changed calendar date [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json`
(`mood_changes_at_existing_utc_hour`, `old_rows_still_mood_without_utc`, `grid_changes`);
`<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`shape`)].

## Rules

All **Applied** in both current files [src: `<audit>/Codex/MoodTiming20261117/build.py`;
`<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`]:

1. **Point in time.** A response is a point: its UTC hour is the hour of its completion instant. Half- and quarter-hour
   zones need no special handling for mood.
2. **Latest completion per participant and UTC hour wins.** When several responses fall in one UTC hour, the latest
   completion supplies the hourly score (a tie would be broken by response key; in neither cohort did two responses
   share the latest completion time of an hour). All responses, including superseded ones, are in the companion with a
   selection flag.
3. **Zero means no response.** `Mood = 0` keeps its meaning of no selected response in that hour; values are never
   carried forward or backward.
4. **Local label.** At an hour with a selected response, `time_local` is the start of the UTC hour on the respondent's
   clock (UTC hour plus the response's offset). In fractional-offset zones its minute can be nonzero. Labels change only
   at hours with a timed response.
5. **Daily resting heart rate.** Looked up again from the daily companion wherever the local date changed or a blank
   date was supplied, and on added rows. All other daily values were compared cell by cell.
6. **Added rows.** A response whose UTC hour has no row gets one: participant, UTC hour, local label, mood and that date's
   daily RHR; every other column blank.
7. **Wearables untouched.** Existing wearable values and keys are unchanged, including rows without UTC.

Rule 2 replaces the earlier rule "the last mood report completed during that hour" only in its timestamps; the
selection principle is the same [src: `<shared>/README.md`, section "Mood and missing values"].

## Counts

| | 2024 | 2025 |
|---|---:|---:|
| Scored source responses | 105,639 | 89,252 |
| Participants with mood | 885 | 864 |
| Positive participant-hours after | 104,314 | 87,252 |
| Positive rows before (base file) | 105,050 (832 without UTC) | 87,369 |
| Hours with more than one response | 1,255 | 1,848 |
| Responses superseded within their hour | 1,325 | 2,000 |
| Old positive hours vacated | 0 | 87,120 |
| Hours newly given a mood value | 0 | 86,997 |
| Same hour, different selected score | 0 | 48 |
| Rows added | 96 | 17 |
| Blank local labels supplied | 2 | 763 |
| Local labels corrected | 127 | 526 |
| Rows whose calendar date changed | 14 | 66 |
| Total rows after | 7,376,544 | 8,564,451 |
| Share of positive rows at 20:00 local after | 51.5% | 51.5% |

[src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json` (`2024`, `2025`, `grid_changes`);
`<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`]

**2025 placement before and after.** Of the 85,694 old positive rows with a local label, 769 (0.9%) were at 20:00
local; the commonest local hours were 16:00 (25,937) and 15:00 (17,260). After the correction 44,954 of 87,252 (51.5%)
are at 20:00 local, matching the raw response times (45,963 of 89,252 raw responses at 20:00, 51.5%). On the UTC clock,
42,123 of 87,358 old rows (48.2%) sat at 20:00 UTC; after, UTC hours 00 to 03 hold 61,776 (70.8%)
[src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json` (`before_time_local`, `after_time_local`,
`before_time_utc`, `after_time_utc`, `raw_local_hour_histogram`); shares computed from those counts].

## Validation

Codex's checks, reported in `MoodTimingValidation.json` and the report [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json`;
`<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`; `<audit>/Codex/MoodTiming20261117/verify.py`]:

- **Independent replay.** Both CSVs were reopened and compared with a separate raw-timestamp and latest-response replay:
  0 mismatches in hourly score, UTC hour or local label (`hourly_score_and_both_clocks_mismatches`), both cohorts. Every
  scored source record is in its response companion.
- **Nothing else moved.** 0 unexpected wearable or key changes; 0 duplicate known UTC keys; 0 local-label changes
  without a timed response; 0 unexpected daily-value changes; 0 wrong daily values at changed dates; 0 old positive
  mood rows outside the raw response period; 0 old rows without UTC still carrying mood.
- **Window membership (2025).** Against the 2025 main decision windows: 0 responses have a different window set by the
  file's hour than by the independently computed source hour, and 0 by the hourly bucket than by the exact instant. (The
  old placement differs for 6,054.)
- **Peak.** Local mood peak at 20:00 with 51.5% of positive rows in both cohorts, the acceptance test Claude set at
  18:11.

These are the builder's own checks. The independent review Claude listed (each placed response at its UTC hour with its
score, no positive mood elsewhere, local-hour histogram equal to the raw one, counts by status, window assignment by file
time equal to that by corrected time) has not been run by Claude; see [review status](#review-status)
[src: `<vault>/Audit Message Board.md`, post of 2026-11-17 18:11].

## What the correction does not change

- **Wearable columns.** All existing wearable values and keys are as in the base files [src:
  `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`].
- **2025 follow-ups.** The iPhone-first phone-step rule and the June 18 to 20, 2026 Fitbit zero days were kept out of
  this mood-only correction and remain open [src: `<vault>/Data Preprocessing/07 Current Files and Version Register.md`;
  `<vault>/Audit Message Board.md`, post of 2026-11-17 22:16]. See [audit corrections](04-audit-corrections.md#items-still-open).
- **The June 2026 tail.** Scored 2025 responses end June 20, 2026; decisions run to June 30. 7,350 main windows from
  June 21 have no mood [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`; `<vault>/Audit Message Board.md`,
  post of 2026-11-17 17:52].
- **The 2025 clock for other streams.** Fitbit and the other streams keep the November 17 placement; see
  [clocks](03-clocks-and-time-zones.md#what-the-november-17-file-applied).
- **Root files and caches.** The root CSVs, external shared copies and analysis caches computed before 2026-11-17 23:03
  refer to the earlier versions [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`].

## Review status

**Independent review owed.** Codex asked Claude to replay the response companions against the raw records and check
main-window membership, the local display hours, the local peak, each source clock and daily RHR on the relabelled
dates [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 22:16]. At 23:03 and again at 23:45 Claude recorded the
review of Stage C and of the mood-corrected pair as still owed, after the engine rerun
[src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 23:03 and 23:45]. No review is recorded on the board through
its last post of 2026-11-23, and the engine's data note still reads "under independent review"
[src: `<shared>/Rotation-1/Drew's code/causal/config/data_notes.yaml`].

Lesson recorded from the earlier miss: a conservation check passes when values are moved wrongly or not moved at all, so
the review should compare placement with the raw source (hour of day against the raw time, cross-device agreement), not
only counts and totals [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 17:52].

## Using the files

- Each positive `Mood` belongs to the UTC hour in which the survey was completed; zero is no selected response
  [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`].
- `MoodResponses2024.csv.gz` and `MoodResponses2025.csv.gz` hold every scored response, including same-hour
  resubmissions, with columns `participant_id`, `response_key`, `response_local`, `response_utc`, `score`,
  `offset_seconds`, `utc_hour`, `local_time_at_utc_hour_start`, `selected_for_hour`, `responses_in_hour`, and for 2025
  also `day_status` and `day_clock_utc` (Claude's staged day-clock estimate, for comparison). `utc_hour` is the join key
  to the hourly file [src: `<audit>/Codex/MoodTiming20261117/build.py`; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`].
- For window boundaries inside an hour, use `response_utc` [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`].
- In the 2025 companion `response_key` is a hash of the survey question-result key, not the raw key
  [src: `<audit>/Codex/MoodTiming20261117/sources.py`].

## Sources

- `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md` and `MoodTimingValidation.json`.
- `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` and `Validation2024.json`.
- `<shared>/README.md`, top section and "Mood and missing values".
- `<vault>/Audit Message Board.md`: register row SCAN-01-F01; posts of 2026-11-16 01:53, 13:08, 16:27, 16:54;
  2026-11-17 16:43, 16:52, 17:52, 18:11, 22:03, 22:10, 22:16, 23:03, 23:45.
- `<vault>/Data Preprocessing/07 Current Files and Version Register.md`.
- `<audit>/Codex/MoodTiming20261117/sources.py`, `sources.json`, `build.py`, `verify.py`.
- `<audit>/Codex/HourlyMerge20261117/build_candidate.py`, `validate_candidate_release.log`.
- `<audit>/Opus/Mood2025-placement-20261117/stage_summary.json`.
- `<shared>/Rotation-1/Drew's code/causal/config/data_notes.yaml`.
