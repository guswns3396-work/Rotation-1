# Clocks and time zones

Every hourly row carries a UTC hour (`time_utc`) and a local clock label (`time_local`), and each stream reaches its
UTC hour by a different route. In the 2024 cohort the route is simple and checked: each phone reported its time zone
about once an hour, with UTC timestamps, and the build follows that history on 99.1% of the hours that can be tested.
In the 2025 cohort most sources store local wall-clock time with no offset, the original build filled the gaps with one
roster zone per participant, and the November 2026 audit found that about 5.5% to 6.6% of Apple Health hours sat at
the wrong UTC hour by the records' own offsets (more for some device columns). The November 17 rebuild of the 2025 file re-placed Apple Health by each record's own UTC
time and Fitbit by an approved day-level clock (staged clock version 3, with holds), but it carried the mood error
forward; mood was fixed separately in the files the current results use (see [mood timing](05-mood-timing.md)). This
note gives the rules, the evidence, the size of every move, and which parts are applied, staged or still open.

## Contents

- [Status labels and files](#status-labels-and-files)
- [Terms](#terms)
- [2024 cohort](#2024-cohort)
  - [The phone time-zone history](#the-phone-time-zone-history)
  - [How each 2024 stream gets its UTC hour](#how-each-2024-stream-gets-its-utc-hour)
  - [Checks of the 2024 clock](#checks-of-the-2024-clock)
  - [Fitbit follow-up export one hour early](#fitbit-follow-up-export-one-hour-early)
  - [Local labels in the current 2024 file](#local-labels-in-the-current-2024-file)
  - [Known 2024 clock exceptions](#known-2024-clock-exceptions)
- [2025 cohort](#2025-cohort)
  - [How 2025 sources store time](#how-2025-sources-store-time)
  - [The original 2025 clock map](#the-original-2025-clock-map)
  - [Evidence gathered on 2026-11-16](#evidence-gathered-on-2026-11-16)
  - [The 8 pm mood reminder](#the-8-pm-mood-reminder)
  - [Two-offset days](#two-offset-days)
  - [Staged clock versions 1 to 3](#staged-clock-versions-1-to-3)
  - [Decisions on the 2025 clock](#decisions-on-the-2025-clock)
  - [What the November 17 file applied](#what-the-november-17-file-applied)
  - [What the current 2025 file adds](#what-the-current-2025-file-adds)
  - [How large the moves were](#how-large-the-moves-were)
- [Status summary](#status-summary)
- [Open clock items](#open-clock-items)
- [Sources](#sources)

## Status labels and files

Every rule below carries one of these labels:

- **Applied**: in the hourly files the current results use.
- **Staged, not applied**: built as a separate file and reviewed or awaiting review, but not in those files.
- **Proposed**: described or put to Drew, nothing built or nothing approved.
- **Rejected** or **Superseded**: decided against, or replaced by a later rule or file.

The current results (the causal engine) read two dated files, not the root `dfHourly2024.csv` and `dfHourly2025.csv`
[src: `<shared>/Rotation-1/Drew's code/causal/config/data_notes.yaml`; `<shared>/Rotation-1/Drew's code/causal/config/paths.example.yaml`;
`<vault>/Audit Message Board.md`, post of 2026-11-17 23:03]:

| Cohort | File | SHA-256 prefix | Built from |
|---|---|---|---|
| 2024 | `Hourly_MoodCorrected_20261117/dfHourly2024.csv` | `c16bd124c02d` | Stage C 2024 rebuild (`a158a0a9…`) plus the mood timing correction |
| 2025 | `Hourly_MoodCorrected_20261117/dfHourly2025.csv` | `2df0f3e1131d` | November 17 published 2025 file (`84555a10…`) plus the mood timing correction |

[src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json`
(`input_sha256`)]

Both dated files were still awaiting independent review when the engine switched to them; see
[review status](05-mood-timing.md#review-status). The root `dfHourly2024.csv` is still the November 15 version
(`67d15a8a…`), which predates Stage C [src: `<vault>/Data Preprocessing/07 Current Files and Version Register.md`].

## Terms

- **Offset**: local time minus UTC, in hours (US Eastern is −5 in winter, −4 in summer).
- **Local label**: the `time_local` value of a row. A file's offset for an hour is its local label minus its UTC label.
- **Moved**: a row whose offset under a new rule differs from the published one, so it would sit at a different UTC
  hour. Counts of moved hours are of published rows, not of new measurements.
- **Study year**: July 1, 2024 to June 30, 2025 for the 2024 cohort; July 1, 2025 to June 30, 2026 for the 2025
  cohort. The files hold earlier and later rows too [src: `<vault>/Data Preprocessing/07 Current Files and Version Register.md`].
- **Day clock** (2025 only): one offset per participant and local date, used for streams with no offset of their own.
- **Tier**: the source of a day clock (phone records, mood stamps, reminder, and so on).

## 2024 cohort

### The phone time-zone history

The 2024 cohort's clock comes from the study app's participant-update export: each phone reported its zone name and UTC
offset about once an hour. The export has 6,218,526 rows from February 2024 to July 2025; 2,293,336 carry a zone, from
1,011 participants; the median gap between reports is 1.0 hour and 99% of gaps are under 26 hours. Compressed to runs
of constant zone and offset it is 10,761 runs, a median of 8 per participant
[src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, section 1]. (The export itself holds participant-level
data and is not opened for these notes.)

**The update timestamps are UTC.** Eastern phones switch from −4 to −5 at 06:00:25 UTC on 2024-11-03 and back at
07:00:02 UTC on 2025-03-09, which only fits UTC [src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, section 1].
The share README states the same assumption for the build: "Update timestamps are assumed UTC"
[src: `<shared>/README.md`, section "Calendar and timestamps"].

**How the build uses it** (status: **Applied**; it is the original 2024 build's rule, carried into every later 2024
version):

- The named zone in force at each UTC hour is applied with that zone's own daylight-saving rules, not the last
  reported numeric offset [src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, section 1].
- Outside the history's coverage the calendar extends the same named zone forward, but **not backward before a
  participant's first update** [src: `<shared>/README.md`, section "Calendar and timestamps"].
- Carrying a named zone through an unobserved period does not establish that the participant did not travel. Unresolved
  or conflicting zone evidence is left missing, not filled with a fixed offset [src: `<shared>/README.md`, section
  "Calendar and timestamps"].
- Participants with no identifiable zone get a complete UTC calendar with a blank `time_local`
  [src: `<shared>/README.md`, section "Calendar and timestamps"].

### How each 2024 stream gets its UTC hour

| Stream | Clock that is true at the source | How the current 2024 file places it | Status |
|---|---|---|---|
| Fitbit steps, heart rate, sleep, RHR | Local wall clock (no offset in the export) | Local time converted with the phone zone history, as in the original build; inherited unchanged through Stages A to C | Applied |
| Fitbit, January 1 to March 9, 2025 (follow-up export) | Export labels one hour early | +1 hour before 2025-03-09 02:00 local, steps and heart rate | Applied (see [below](#fitbit-follow-up-export-one-hour-early)) |
| Fitbit baseline steps, April to June 2024 | Local wall clock | Filled into existing rows by participant and local hour, so they take that row's UTC hour; not placed where a local hour matched two rows | Applied (Stage B) |
| Garmin steps, heart rate, sleep | Absolute (epoch plus watch offset) | Native UTC; malformed offsets repaired against the participant's zone without changing UTC or duration | Applied |
| Apple Health steps, heart rate, sleep, RHR | Record start and end with their own offset | Stage C: rebuilt on the server from each record's own UTC endpoints, by the 2025 v3 rules | Applied (Stage C) |
| Mood | Completion time with an explicit offset | Current file: each response at the UTC hour of its own completion time | Applied (mood correction) |
| Daily RHR (all devices) | Local date | Repeated on rows whose local date is established; separate daily companion | Applied |

[src: Fitbit and Garmin: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, section 2 ("In 2024 the phone's hourly
zone history did that job"); `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`, table "Which time and value each stream uses";
`<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md`, sections "Sources and rules" and "Earlier Garmin-completed candidate";
baseline steps: `<audit>/Opus/Hourly2024-build/stage_b/stage_b_summary.json`; Apple Health: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`;
`<vault>/Audit Message Board.md`, post of 2026-11-17 17:39; mood: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`]

Notes on the table:

- Before Stage C, the 2024 Apple Health rows were build groups of (participant, local hour, record offset), so a record
  relabelled across zones became a second row with the same UTC hour (register row HK-01-R11). Stage C replaces this
  with the server's UTC-interval rebuild [src: `<vault>/Audit Message Board.md`, register row HK-01-R11;
  `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`]. See
  [the 2024 Apple Health rebuild](04-audit-corrections.md#2024-apple-health-server-rebuild-stage-c).
- Baseline Fitbit steps: 152,179 of 159,244 staged hours were placed; 2,951 hours (122 people) were not, because their
  local hour matched two published rows with different UTC hours, so the offset was ambiguous
  [src: `<audit>/Opus/Hourly2024-build/stage_b/stage_b_summary.json`].
- 2024 mood was already placed from offset-bearing timestamps before the correction; the correction changed no mood
  value at any existing UTC hour (details in [mood timing](05-mood-timing.md#2024-responses)).

### Checks of the 2024 clock

**Against the phone history** (Claude, 2026-11-16). For each published hourly row the phone's zone at that UTC hour
was applied with its own rules. An hour is "firm" when it lies inside one run of the history
[src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, section 1]:

| Firm participant-hours (930 participants) | Hours | Share |
|---|---:|---:|
| One row, offset matches the phone | 6,372,816 | 99.12% |
| Two or more rows for the UTC hour, one matches | 52,285 | 0.81% |
| One row, offset differs from the phone | 4,314 | 0.07% |
| Two or more rows, none matches | 101 | 0.00% |

- The 4,314 differing hours are spread over 555 participants and every month; most are one hour off.
- Between two runs (switch time unknown) 98.9% of rows match one of the two neighbouring zones.
- 156,487 rows fall before a participant's first report and 333,195 after the last; they cannot be tested.
- The check uses the same zone field the build used, so it tests the processing, not the zone field itself.

[src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, section 1; this was measured on the file of that date,
before Stage C]

**Against the notification log.** 2024 local labels match the zone implied by each 3 pm-local notification on 99.7%
of attempt hours (119,705 of 120,059), across both daylight-saving changes. The roster zone differed from the
notification on 5.4% of send-days, and the file followed the notification on 7,528 of those
[src: `<vault>/Audit Message Board.md`, post of 2026-11-16 02:14 (CLK-02-F01)].

**Cross-device lags.** Weekly lags between two step sources of the same person put Fitbit at the wrong UTC hour in
49 of 4,288 participant-weeks and Garmin in 15 of 2,492 in the 2024 file; the Phone-versus-Watch control shifted in
11 of 19,484 weeks [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 02:14 (CLK-02-F02)].

### Fitbit follow-up export one hour early

**Problem.** The 2024 cohort's January to June 2025 Fitbit export (not the July to December 2024 data) labels every
minute one hour early until the US daylight-saving start on 2025-03-09, then labels correctly. Participants in zones
without daylight saving show the same pattern, so it is an export error, not the participants' clocks
[src: `<vault>/Audit Decision Summary 2026-11-14.md`, section "Fitbit follow-up clock settled — Opus, November 15"].

**Evidence.**

- Paired daily totals: before March 9, +1 hour alone matches exactly on 4,876 participant-days against 3 for unchanged
  labels; after March 9, unchanged labels win 8,716 to 7. 175 of 179 participants favour +1 hour before March 9; 158
  of 163 favour unchanged labels afterwards; none favours the opposite rule
  [src: `<vault>/Data Preprocessing/14 Fitbit Clock, Decision Time and Boundary Sources.md`].
- A seasonal rule (+1 hour before March 9 02:00) matches 117 of 132 March 9 daily totals, against 71 unchanged and 55
  for a constant +1 hour [src: `<vault>/Data Preprocessing/15 Fitbit Transition and HealthKit Garmin Recovery.md`].
- Heart rate, which runs overnight, shows the switch at each participant's local 02:00; on March 9 the labels 01:00 and
  02:00 are empty in every US zone [src: `<vault>/Audit Message Board.md`, post of 2026-11-15 02:59 (SRC-01-F07);
  `<vault>/Audit Decision Summary 2026-11-14.md`].
- At the December 31 to January 1 seam, January 1 minute totals match the daily summary for 59 of 63 participants at
  +1 hour against 15 unshifted [src: `<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md`,
  section "Subsequent Fitbit boundary review"].

**Rule.** Add one hour to the follow-up export's labels before 2025-03-09 02:00 local; leave later labels unchanged.
Applied to Fitbit steps and, after Claude's review found heart rate still an hour behind steps, to Fitbit heart rate
too. **Not applied to Fitbit sleep** ("I will not shift sleep by analogy"); sleep timing for January to March 9, 2025
remains unverified [src: `<vault>/Audit Message Board.md`, posts of 2026-11-15 02:59 (Claude: heart rate one hour
behind steps) and 12:33 (Codex: shift heart rate too, not sleep); `<vault>/Data Preprocessing/17 Full 2024 Cohort Follow-up Rebuild.md`].

**Who and when.** Codex built the rule; Claude reviewed it on 2026-11-15; it went out in the November 15 full-year
publication of `dfHourly2024.csv` under Drew's 2026-11-14 authorization of the full-year rebuild
[src: `<vault>/Audit Decision Summary 2026-11-14.md`, section "Full-year scope authorized"; `<shared>/README.md`,
section "November 15, 2026 — 2024 full-year expansion published locally"].

**Status: Applied** (steps and heart rate); carried through Stages A to C into the current 2024 file
[src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`]. The published July to December 2024 Fitbit data
were tested separately and favour their existing labels, so no shift applies there
[src: `<vault>/Data Preprocessing/14 Fitbit Clock, Decision Time and Boundary Sources.md`].

### Local labels in the current 2024 file

Stage C rebuilt the 2024 file to one row per participant and known UTC hour, then chose one local label per row
[src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`]:

| Label basis | Rows |
|---|---:|
| One consistent label across the hour's hourly data | 5,458,226 |
| Single label from the existing calendar grid (empty hours) | 1,628,618 |
| Published mood label (response-bearing hours) | 102,674 |
| Corroborated mood local hour | 1,542 |
| Daily-RHR-only rows | 3,072 |
| Local label unresolved (blank) | 57,433 |
| Original local-only rows (no UTC) | 124,883 |

[src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`clock_choices`)]

- The 124,883 local-only rows have no UTC hour. Their native hourly measurements and mood stay on their original local
  keys; their legacy hourly Apple Health values were moved to an exceptions archive, and only UTC-matched rebuilt Apple
  Health values enter the hourly columns. No UTC key was imputed [src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`].
- Daily RHR is blank on the 57,433 rows with an unresolved label; 278 participant-dates exist only in the daily
  companion `DailyRestingHeartRate2024.csv.gz` [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json`
  (`RHR_absent_local_day`); `<vault>/Data Preprocessing/07 Current Files and Version Register.md`].
- The mood correction then supplied 2 missing local labels and corrected 127 at mood hours, changing the calendar date
  of 14 rows [src: `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json` (`grid_changes`)]. The engine
  counted 57,431 known UTC hours without a local label in the current 2024 file [src: `<vault>/Audit Message Board.md`,
  post of 2026-11-17 23:03].

### Known 2024 clock exceptions

- **Fitbit heart rate stacked at zone changes (July to December 2024).** 176 Fitbit heart-rate UTC hours (78 people)
  hold two rows; in 27 of the 41 exactly reproducible cases two real hours of wear were put into one UTC hour, so the
  2024 build mistimed some zone changes. Merging pairs changes 198 decision windows by a median 0.0006 bpm. No rule was
  adopted (register row CLK-01-R02) [src: `<vault>/Audit Message Board.md`, register row CLK-01-R02;
  `<vault>/Audit Decision Summary 2026-11-14.md`, section "Fitbit heart-rate clock at time-zone changes"]. Stage C's
  one-row-per-UTC-hour rule blanks an hour where two different native values meet: 435 Fitbit mean-heart-rate hours
  and 426 maximum hours were withheld this way [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json`
  (`native_collisions`)]. Status: **Applied** (withholding); re-timing **Proposed**, not done.
- **Withheld in Stage C** because two native values met in one UTC hour: Fitbit steps 154 hours, Fitbit sleep 53,
  Garmin steps 30, Garmin heart rate 426 (mean) and 345 (maximum). Values on fractional UTC keys (half- and quarter-hour
  zones) were also withheld: Fitbit steps 1,622 cells, Fitbit heart rate 266, Fitbit sleep 72, Garmin steps 1,145,
  Garmin heart rate 214, Garmin sleep 29. Originals are in the Stage C audit [src:
  `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`native_collisions`, `fractional_native_cells`)].
  Status: **Applied**.

## 2025 cohort

### How 2025 sources store time

| Source | What is stored | Consequence |
|---|---|---|
| Apple Health, nightly export | `STARTDATE` local wall-clock time, no offset (only sleep records carry a zone, in metadata) | UTC hour depends on the zone the build assumes |
| Apple Health, server database | Each record's start stored with its real UTC offset; the nightly export dropped it | The offset can be recovered from the server |
| Fitbit | Local time, no zone, anywhere (database, nightly, API, sleep-log modification time, last-sync field all tested); its API offset column is always zero; sleep stage times are stored with `+00:00` | No direct offset; must borrow a clock |
| Garmin | Epoch seconds plus the watch's own offset | Absolute; UTC needs no clock |
| Mood, nightly file (`Daily_Mood`) | Local wall-clock time | UTC depends on the clock; see [mood timing](05-mood-timing.md) |
| Mood, server survey tables | Each response's time stored with the responding phone's offset | The offset can be recovered |
| Daily API files | A per-record offset for Apple Health and Garmin | Server folders start 2026-05-01, so they cover two months only |
| Roster (`STUDYPARTICIPANTS`) | One zone per participant; no zone-history table in the 2025 schema | The fallback when nothing else exists |

[src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, sections 2 and 7; `<vault>/Audit Message Board.md`, posts of
2026-11-16 13:08 (CLK-02-F10) and 16:54 (CLK-02-F15); `<vault>/Audit Message Board.md`, post of 2026-11-16 19:00 (Fitbit
stage times stored `+00:00`)]

Fitbit-native sources tested and rejected as clocks: the sleep-log modification time trails the sleep's end by a
median 195 hours, and the daily last-sync field is a date, exactly midnight in 84% of fresh values
[src: `<vault>/Audit Message Board.md`, post of 2026-11-16 13:08].

### The original 2025 clock map

The original 2025 build (the compact builder, functions `evidence()` and `make_clocks()`) uses a record's own offset or
zone **only for the local hour that record was seen in**, and the roster zone for every other hour. Its code comment
reads "Evidence covers observed local clock hours only, never unobserved multi-day gaps"
[src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, section 3]. 86.3% of the map's hours are roster fallback
[src: `<vault>/Audit Message Board.md`, post of 2026-11-16 02:14 (CLK-02-F03)].

What that produced, before any fix:

- **The roster is the internship location.** Before July 2025 it differs from the participant's own record offsets on
  20.3% of single-offset days, against 5.6% to 5.8% in the study year: spring data predate the move
  [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 12:45 (CLK-02-F09)].
- **Daytime stretches flip to the roster.** 9,074 daytime stretches (264 participants) lie between nights whose sleep
  records show the same zone, yet the map switched to a different roster zone during the day. They held 4.3% of the
  file's Watch step rows (3.1% in the study year) and 2.6% of Phone step rows, mostly 1 to 3 hours off (register row
  CLK-01-R03) [src: `<vault>/Audit Decision Summary 2026-11-14.md`, section "2025 clock map uses the roster zone
  against the participant's own evidence"].
- **Roster contradicted on 7.1% of checkable days.** On 59,783 participant-days with an offset-bearing record (555
  participants), 6.0% contradict the roster outright and 1.1% partly; 53,431 Apple Health or Fitbit hours on those days
  were still placed with the roster zone, and 28,959 more lay between two contradicting days
  [src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, sections 3 and 4].
- **Stacked hours.** 7,113 step hours had two local hours put into one UTC hour, about 97% at a switch between record
  evidence and roster fallback (register row CLK-01-R01). Codex qualified this: the residual does not rule out other
  overlaps, and placement under the map does not settle the historical clock [src: `<vault>/Audit Message Board.md`,
  register row CLK-01-R01; `<vault>/Audit Decision Summary 2026-11-14.md`, policy item g].

Status of the original map: **Superseded** inside March 1, 2025 to July 8, 2026 for Apple Health, Fitbit and Garmin
local labels by the November 17 rebuild ([below](#what-the-november-17-file-applied)); still in force for 2025-cohort
rows outside that window and for Fitbit hours the rebuild held back.

### Evidence gathered on 2026-11-16

All of this came from server pulls Drew approved through the private repository on 2026-11-16, one at a time and then
in two consolidated batches [src: `<vault>/Audit Decision Summary 2026-11-14.md`, section "2025 clock: how much the
roster zone is contradicted"; `<vault>/Audit Message Board.md`, posts of 2026-11-16 12:13, 14:45, 15:22, 16:09, 16:27].

| Finding (register row) | Result | Source |
|---|---|---|
| Offset history (CLK-02-F09) | 171,864 of 3,152,057 published Apple Health hours on single-offset study-year days (5.5%) carry a different offset from the database; 39 participants who differ from the roster on over half their days hold 146,832 of them. Confirmed against Garmin: in 28 of 29 testable weeks the Phone-Garmin lag equals the file-minus-database difference | Board, post of 2026-11-16 12:45 |
| Correction to F09 by Codex | On days with several recorded offsets, 11,977 Apple Health hours match no recorded offset (not 26,168: 14,191 match an intermediate offset) | `<vault>/Data Preprocessing/21 IHS2025 Clock Evidence and Survey Probe.md` |
| Full passes over steps and heart-rate tables (CLK-02-F12) | 199,055 of 3,018,780 published step hours (6.6%) and 109,929 of 1,712,924 heart-rate hours (6.4%) sit at the wrong UTC hour by their own records; replaces the 5.5% | `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, section 13 |
| Fitbit follows the phone (CLK-02-F10) | Lag zero in 6,548 of 6,651 testable Phone-Fitbit weeks (224 participants). 246 of 306 Fitbit participants have a phone history; 60 do not, holding a quarter of Fitbit hours | Board, post of 2026-11-16 13:08 |
| Reminder clock (CLK-02-F11) | See [the 8 pm mood reminder](#the-8-pm-mood-reminder) | Section 11 of the update report |
| Mood stamps (CLK-02-F15) | The survey table stores each response with the phone's offset: equal to the Apple Health record offset on 65,970 of 65,982 responses (99.98%) on `phone` days. For Fitbit participants with no phone day, where reminder and roster disagree, mood sides with the reminder on 358 of 402 responses | Board, post of 2026-11-16 16:54 |
| Hour-level record offsets (CLK-02-F16) | Each device column against its own class's records starting that hour: file differs on 7.5% of phone step hours, 6.6% watch steps, 13.8% phone heart rate, 6.2% watch heart rate. Phone and watch differ in the same hour on 3.6% of heart-rate hours | Board, post of 2026-11-16 16:58 |

### The 8 pm mood reminder

The 2025 app sends a `MoodReminder` notification at 20:00 on each participant's own clock, so 20:00 minus the UTC send
time gives that clock's offset (Drew's idea) [src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, section 11;
`<vault>/Data Preprocessing/21 IHS2025 Clock Evidence and Survey Probe.md`].

- A 200,000-row aggregate sample (March 18 to September 24, 2025) had 109,372 of 113,397 successful reminders (96.45%)
  in UTC hours 00 to 04, as expected for US zones [src: `<vault>/Data Preprocessing/21 IHS2025 Clock Evidence and Survey Probe.md`].
- The participant-level send times (approved by Drew, private repository, 2026-11-16) were tested where the phone's
  offset is known (836 participants, 214,050 days): the reminder's clock equals the phone's on 98.2% of days, the
  roster on 93.0%. When the roster is wrong (14,924 days) the reminder has the phone's offset on 13,607. Where reminder
  and roster disagree the reminder is right on 80% of days [src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`,
  section 11].
- It covers all 60 Fitbit participants without a phone history, on 91% of their Fitbit days. For them the published
  file's offset differed from the reminder's on 34,110 of 293,668 covered Fitbit hours (11.6%); fewer than 10
  participants, whose roster zones were 9.5 to 16 hours off, held 25,877 of those hours [src: same, section 11].
- **Limits.** The reminder's clock refreshes when the app is used: 90% right on the day a phone changes zone, 98% a
  week later; most wrong days sit in 27 long stretches (26 participants) where it kept an old zone for over a month.
  Scheduled but undelivered reminders are right less often (87.5%) and are not used. Offsets are known only modulo 24
  hours (a slot that could be −10 or +14 is read as −10), and a 20:00 schedule is assumed for everyone; the schedule
  definition was not seen [src: same, section 11; `<audit>/Opus/CLK-02/stage_clock_2025/STAGE_NOTE.md`, "Limits"].

### Two-offset days

On 12,019 participant-days in the 2025 cohort the phone's own records carry two or more offsets (travel days, mostly).
The staged day clock gives these days no offset (tier `phone_two`) [src: `<audit>/Opus/CLK-02/stage_clock_2025/STAGE_NOTE.md`].

- **Run files cannot place them.** A run's first and last times span whole stretches of days, so an hour inside one
  run's span was not necessarily recorded at that offset (Codex's review, 2026-11-16 15:49). Claude withdrew an earlier
  claim that most could be placed that way [src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, section 15].
- **Hour-level export (CLK-02-F14).** On these days 85% of published step hours and 82% of heart-rate hours have one
  offset among the records starting in that hour, and the published file differs from it on 47% and 40% of them.
  Apple Health sleep hours on these days are mostly zero-minute fill [src: same, section 16].
- **Re-timed by the records' own UTC (CLK-02-F20).** 1,350,372 step records (742 participants) carry their UTC times.
  Summed back into local hours they reproduce 98% of published phone hours and 96% of watch hours; placed by UTC, about a
  third of those days' steps sit in a different UTC hour (phone 33.8%, watch 32.1%)
  [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 18:51].
- **Staged files** (status: **Staged, not applied**; superseded for Apple Health by the server rebuild):
  `two_offset_days_steps_hr_utc.csv.gz` (214,736 rows; every writer summed, one-copy and app-priority rules not applied,
  so re-timed published values, not final ones), `two_offset_days_sleep_utc.csv.gz` (12,996 rows, partial coverage,
  evidence only), and a flag list of 700 half-hour-offset heart-rate rows that were floored into one UTC hour and need
  proper UTC grouping [src: `<audit>/Opus/CLK-02/stage_clock_2025/STAGE_NOTE.md`; `<vault>/Audit Message Board.md`, posts
  of 2026-11-16 19:00, 19:38 and 20:01].

**Resolution in the current 2025 file.** Apple Health on these days is placed by each record's own UTC endpoints in
the server rebuild, which needs no day clock; an hour whose records carry two offsets keeps its UTC placement and gets a
blank local label (flag `multiple_source_offsets_local_label_unknown`, 28,717 flags) [src: `<vault>/Audit Message Board.md`,
post of 2026-11-16 20:30; `<audit>/Codex/HourlyMerge20261117/build_candidate.py`; `<audit>/Codex/HourlyMerge20261117/audit/utc_companions.json`].
Fitbit hours on these days are **not moved** (no approved day offset) and are flagged; mood responses on them are placed
by their own completion time in the current file ([mood timing](05-mood-timing.md#how-2025-responses-were-matched)).

### Staged clock versions 1 to 3

All three versions were staged by Claude on Drew's instruction on 2026-11-16, in `<audit>/Opus/CLK-02/stage_clock_2025/`
(older versions in `v1_superseded/` and `v2_superseded/`). Each is a table of 337,358 participant-days (928
participants, March 1, 2025 to July 7, 2026) giving a day offset and its tier; a blank offset means "keep the file's
placement" [src: `<audit>/Opus/CLK-02/stage_clock_2025/STAGE_NOTE.md`].

| Version (time staged) | Tier order | Change from the previous version | Status |
|---|---|---|---|
| v1 (15:17) | Phone offset in three tiers, then delivered reminder, then short fills between agreeing days; roster otherwise | First version; undelivered reminders not used | Superseded by v2 |
| v2 (15:39) | Each Apple Health stream on its own table's offset; the day clock for Fitbit and mood from the record tables, step-summary tables only where no record exists | After the full step and heart-rate passes; 97% of days keep v1's offset; 8,140 days dropped because records show two offsets | Superseded by v3 |
| v3 (18:01) | As v2, plus a `mood` day tier (13,086 days) above `reminder`, and an hour-level record-start file | After the consolidated batch showed mood carries the phone's clock | Partly applied (see below) |

[src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, sections 12, 13 and 24; `<audit>/Opus/CLK-02/stage_clock_2025/STAGE_NOTE.md`]

**Version 3 tiers** [src: `<audit>/Opus/CLK-02/stage_clock_2025/STAGE_NOTE.md`, "Day clock tiers"; approval status from
`<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`, item 8]:

| Tier | Rule | Days | Check | Approved for the rebuild |
|---|---|---:|---|---|
| `phone` | Record tables show one offset that day; step-summary tables agree or are absent | 243,582 | Reminder equals it on 98.6% of days | Yes |
| `phone_records` | As above, but step-summary tables add another offset; the record offset is used | 22,141 | Reminder equals it on 96.1% | Yes |
| `phone_stats` | No record; step-summary tables show one offset | 2,264 | Reminder equals it on 93.7% | No (not put to Drew) |
| `phone_two_resolved` | No record; summaries show two or more; the delivered reminder equals one | 137 | none | No (held) |
| `mood` | No phone offset; that day's mood responses carry one offset | 13,086 | Equals the Apple Health offset on 99.98% of responses | Yes |
| `reminder` | No phone or mood offset; one offset from a delivered reminder | 31,728 | Equals the phone on 98.4% where known | Yes, with a hold (below) |
| `filled` | Nearest known days either side agree, at most 14 days apart | 200 | About 99% on phone days | No (not put to Drew) |
| `phone_two` | Records show two or more offsets | 12,019 | none | No offset (Apple Health by record UTC) |
| `reminder_two` | Two reminder offsets that day | 2 | none | No offset |
| `roster` | Nothing else | 12,199 | none | No offset (published placement) |

The v3 hour-level file `clock_hours_2025_record_start.csv.gz` lists 873,006 published Apple Health hours whose
records starting in that hour carry exactly one offset that differs from the file's. Codex accepted it as a separate
evidence tier on 2026-11-16; it does not cover contributions from intervals that started in an earlier hour
[src: `<audit>/Opus/CLK-02/stage_clock_2025/STAGE_NOTE.md`, "The hour-level file"]. Status: **Superseded** for
Apple Health by the server's record-UTC rebuild.

### Decisions on the 2025 clock

1. **Drew, 2026-11-16 18:45** ("Yes, use your picks", pick 4): apply the phone-record tiers, the `mood` tier and the
   `reminder` tier of v3, each Apple Health stream on its own table's offset, and **hold back the Fitbit hours where the
   reminder overrides the roster with no on-time mood response in the stretch**. `filled` and `phone_stats` were not put
   to Drew and count as not approved. Drew approved knowing Codex had then accepted only the record-based evidence
   [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 18:45].
2. **Freeze list, 2026-11-16 19:23**: the held-back days are 754 participant-days (36 participants), 7,769 Fitbit hours,
   6,084 in the study year (`held_back_fitbit_days_2025.csv.gz`). `phone_two_resolved` is also held. Days whose clock
   differs from the previous known day cannot be placed by a day table: 1,214 Fitbit clock-change days (233
   participants, 25,146 Fitbit hours) are flagged and not moved (`fitbit_clock_change_days_2025.csv.gz`). Days with a
   non-whole-hour offset (357 days, 21 people) "must be split across two UTC hours"
   [src: `<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`, item 8; `<vault>/Audit Message Board.md`, post of
   2026-11-17 16:24 (21 people)].
3. **Codex, 2026-11-16 20:30** (clock disposition): accepts the mood tier as response-stamped clock evidence and the
   reminder tier as a retrospective inferred-clock tier "with its weaker provenance retained"; use direct record
   timestamps for Apple Health and mood wherever available; for Fitbit keep the reminder-without-mood holdout and do not
   move ambiguous, blank, unapproved or clock-change-day rows; do not prorate heart-rate maxima or fabricate sleep
   placement from a day offset [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 20:30].
4. **Codex and Claude, 2026-11-17 16:23 to 16:24**: values on quarter- and half-hour UTC keys are withheld from the
   UTC grid for this release, originals kept in the audit; an exact rebucket from local minute and epoch data is
   possible later [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 16:23 and 16:24].

### What the November 17 file applied

The November 17 rebuild (`84555a10…`, published 2026-11-17 16:56 on Drew's authorization of the merge) is the base of
the current 2025 file. Its clock rules, per stream [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`;
`<audit>/Codex/HourlyMerge20261117/REPORT.md`; `<audit>/Codex/HourlyMerge20261117/build_candidate.py`]:

| Stream | Rule applied | Scope |
|---|---|---|
| Apple Health (steps, heart rate, sleep, RHR; phone and watch) | Rebuilt on the server from each record's own UTC start and end; local label from the records' source offset when they carry one offset, blank when two or more | Source records March 1, 2025 to July 8, 2026 (exclusive); RHR on complete local days March 2, 2025 to July 6, 2026 |
| Fitbit (steps, heart rate, RHR, sleep) | UTC = local label minus the approved day-clock offset when the day's disposition is "approved" (tiers `phone`, `phone_records`, `mood`, `reminder`, not reminder-held, not a clock-change day, whole-hour offset, one row for the local hour); otherwise the published placement is kept and flagged | Rows with UTC (or local time when UTC is blank) in March 1, 2025 to July 8, 2026 |
| Reconciled Fitbit sleep (stage records) | Placed with the approved day clock; else the published UTC if the local hour has one row; else held | Same window |
| Garmin (native) | UTC unchanged; the local label is moved to the approved day clock where exactly one candidate exists; conflicting duplicate values keep their published placement | Same window |
| Mood | Routed like Fitbit, from the local label; this reproduced the old error (see below) | Superseded by the mood correction |
| Values on fractional UTC keys | Withheld, originals in the audit | All |

Counts from the rebuild (cells, not hours, and across several columns):

- 473,982 Fitbit and mood cells moved by the approved day clock, and 78,019 native Garmin cells relabelled to a new
  local hour, in the expanded intermediate [src: `<audit>/Codex/HourlyMerge20261117/audit/build_checks.json`
  (`new_cells_by_origin`)].
- Fitbit placement of reconciled sleep stage hours: 406,081 by the approved day clock, 31,779 at the published UTC,
  11,368 held as ambiguous [src: `<audit>/Codex/HourlyMerge20261117/validate_candidate_release.log`].
- Final flag counts (cell level, Fitbit and mood columns): clock held because the tier is unapproved or missing
  327,352; clock-change day 102,870; reminder without mood support 34,499; fractional offset 3,107; several local rows
  2,753 [src: `<audit>/Codex/HourlyMerge20261117/audit/utc_companions.json` (`flags_by_reason`)].
- Local labels in the final file: one consistent hourly label 6,073,828 rows; approved day clock on empty or daily-only
  hours 2,081,181; single existing label 339,822; approved clock matching one of several hourly labels 7,214;
  unresolved (blank) 55,188 [src: `<audit>/Codex/HourlyMerge20261117/audit/utc_consolidation.json` (`local_labels`)].
  Of 60,339 hours with conflicting labels, 7,214 took a candidate through the day clock and 53,125 are blank; none got a
  label outside its candidates [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 16:58].
- 12,035 UTC hours on quarter- or half-hour keys left the grid; their values are withheld (Fitbit steps 1,039, Fitbit
  heart rate 46, Fitbit sleep 52, Garmin steps 321, Garmin heart rate 271, mood 17) [src: `<vault>/Audit Message Board.md`,
  post of 2026-11-17 16:58; `<audit>/Codex/HourlyMerge20261117/audit/utc_consolidation.json` (`hourly_holds`)].

**Mood in the November 17 file was still wrong.** The raw `Daily_Mood` time is a local wall-clock time; the earlier
2025 file had stored it in `time_utc`, so its local label was derived from the wrong UTC. Routing mood "like Fitbit"
from that label reproduced the old placement except on 6,885 cells where the approved offset differed from the roster's.
Mood stayed 4 to 8 hours early (SCAN-02-F01) [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 17:52 and 18:11].
Claude's acceptance review at 16:58 had checked only that mood counts and totals were conserved per participant
[src: same, post of 2026-11-17 17:52].

**Rows outside March 1, 2025 to July 8, 2026.** The 2025 file starts in April 2024. Rows before March 1, 2025 were not
in the server rebuild or the clock routing, so they keep the original build's placement (roster plus same-hour record
evidence) [src: `<audit>/Codex/HourlyMerge20261117/build_candidate.py` (`IN_SCOPE`); `<audit>/Codex/HourlyMerge20261117/REPORT.md`].
Whether any analysis window reaches those rows depends on the decision dates; see
[decisions and probabilities](06-decisions-and-probabilities.md).

### What the current 2025 file adds

The current 2025 file (`2df0f3e1…`) changes only mood and the fields mood touches: every scored response is placed at
the UTC hour of its own completion time from the server survey table, and at hours with a verified response the
response's clock supplies the row's local label. It supplied 763 previously blank local labels, corrected 526, and
changed the local date of 66 rows (daily RHR was looked up again there) [src:
`<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md`; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json`
(`grid_changes`)]. Wearable values and keys are unchanged. Full detail: [mood timing](05-mood-timing.md).

### How large the moves were

Shares of study-year hours that each version would move, as staged (estimates on the then-published file, not counts
of what the rebuild changed):

| Stream | v1 (2026-11-16 15:17) | v2 (15:39) | v3 (18:01) |
|---|---:|---:|---:|
| Apple Health steps | 7.0% (all Apple Health) | 6.5% | 6.5% (198,816 of 3,080,858) |
| Apple Health heart rate | (in the 7.0%) | 6.2% | 6.2% (109,854 of 1,767,715) |
| Apple Health sleep | (in the 7.0%) | 7.9% | 7.9% (96,809 of 1,227,975) |
| Fitbit | 7.7% | 7.3% | 7.4% (93,976 of 1,276,664) |
| Mood | 6.2% | 5.6% | 5.6% (3,654 of 64,996) |

[src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, sections 12 and 13; `<audit>/Opus/CLK-02/stage_clock_2025/STAGE_NOTE.md`,
"What would move"]

Under v3, of the moved steps, heart-rate and Fitbit hours, 155,403 move by up to one hour, 119,405 by two to four
hours and 127,838 by five hours or more; 42 participants with over half their steps or Fitbit hours moved hold 193,344
of the 292,792 moved steps and Fitbit hours. Garmin's UTC is already right; its local label would move on 10,641 of
519,816 hours [src: `<audit>/Opus/CLK-02/stage_clock_2025/STAGE_NOTE.md`]. Of the 96,809 moved Apple Health sleep
hours, 74,593 are zero-minute fill, not observations [src: same].

Direct measures of misplacement in the then-published file: 5.5% of Apple Health hours (offset history), 6.6% of step
and 6.4% of heart-rate hours (full record passes), and 6.2% to 13.8% by device column at hour level (see
[evidence](#evidence-gathered-on-2026-11-16)).

**Effect on Jack's windows** (sensitivity, his recipe applied to 2025, no treatment contrast): the staged clock changes
4.3% to 5.8% of pooled step-outcome windows that pass his threshold, depending on tiers and counting; 1.4% to 2.0% by
more than a tenth of the step total; 2.9% of sleep-outcome windows; 1.4% of mood windows (910 of 63,547). About 36 participants
hold 71% of the changed windows; no Garmin window changes [src: `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`,
sections 14 and 15]. The earlier, narrower November 15 what-if (only stretches between agreeing sleep evidence)
changed 1.5% of windows [src: `<vault>/Audit Decision Summary 2026-11-14.md`]. By comparison, anchoring 2025 windows at
the logged send rather than the midnight label changes 66% of step outcomes by more than 10%
[src: `<vault>/Audit Decision Summary 2026-11-14.md`, "The questions as first put"].

**What the rebuild actually moved** cannot be read as one share: Apple Health was rebuilt from records (its clock
change is inseparable from the other v3 rules), and Fitbit and mood moves are counted in cells across columns (473,982
moved; see [above](#what-the-november-17-file-applied)). A per-stream count of moved hours in the November 17 file is
not in the records read: **unverified**.

## Status summary

| Rule | 2024 cohort | 2025 cohort |
|---|---|---|
| Phone zone history (UTC update timestamps) for non-absolute streams | Applied | Not available (no zone history on the server) |
| Fitbit follow-up +1 hour before 2025-03-09 02:00 (steps, heart rate) | Applied | Not applicable |
| Same shift for Fitbit sleep | Not applied (unverified) | Not applicable |
| Apple Health placed by each record's own UTC endpoints (server rebuild) | Applied (Stage C, November 18, 2023 to July 7, 2025) | Applied (March 1, 2025 to July 8, 2026) |
| Original roster-plus-same-hour-evidence map | Not used | Superseded inside March 2025 to July 2026; still in force outside it and on held Fitbit days |
| Day clock v3, tiers `phone`, `phone_records`, `mood`, `reminder` for Fitbit | Not applicable | Applied, with holds |
| Reminder override without on-time mood (754 days, 6,084 study-year Fitbit hours) | Not applicable | Held (Fitbit stays at published placement) |
| Tiers `phone_stats`, `filled`, `phone_two_resolved` | Not applicable | Not approved; treated as blank |
| Fitbit clock-change days (1,214) | Not applicable | Flagged, not moved |
| Day clock v1, v2 | Not applicable | Superseded |
| Hour-level record-start file; two-offset-day staged files | Not applicable | Staged, not applied; superseded for Apple Health by the server rebuild |
| Mood routed by the day clock (November 17 file) | Not applicable | Superseded by the mood correction |
| Mood at each response's own completion UTC | Applied | Applied |
| Values on quarter- and half-hour UTC keys | Withheld (Applied) | Withheld (Applied); exact rebucket Proposed |
| Garmin local label from the approved day clock | Not applicable | Applied (UTC unchanged) |
| One local label per UTC hour; conflicting labels blank unless the day clock matches a candidate | Applied (Stage C) | Applied |

## Open clock items

1. **2025 Fitbit on held days.** The reminder-held days (754), clock-change days (1,214), days with unapproved or no
   tier, and days with a non-whole-hour offset keep the original placement, which rests on the roster where no
   same-hour evidence existed [src: `<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`, item 8;
   `<audit>/Codex/HourlyMerge20261117/audit/utc_companions.json`]. The later SCAN-02 check found Fitbit hours under a
   clock hold off the hour for fewer than 10 of 21 testable people (correlation 0.56) [src: `<vault>/Audit Message Board.md`, post
   of 2026-11-17 17:52 (SCAN-02-F04)].
2. **Fractional-offset hours.** 12,035 UTC hours in 2025 (and the Stage C fractional cells in 2024) are withheld
   pending an exact rebucket from local minute and epoch data, which needs no server pull
   [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 16:24 and 16:58].
3. **Unresolved local labels.** 55,188 known UTC hours in the November 17 2025 file (763 supplied since by the mood
   correction) and 57,431 in the current 2024 file have a blank `time_local`; local-time features there must come from
   elsewhere or be missing [src: `<audit>/Codex/HourlyMerge20261117/audit/utc_consolidation.json`;
   `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json`; `<vault>/Audit Message Board.md`, post of
   2026-11-17 23:03].
4. **2024 local-only rows.** 124,883 rows without a UTC hour are kept on their local keys; the engine drops them
   [src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`; `<vault>/Audit Message Board.md`, post of
   2026-11-17 23:45].
5. **2025 rows before March 1, 2025** keep the original clock map.
6. **2024 Fitbit sleep, January 1 to March 9, 2025**: not shifted with steps and heart rate; untested.
7. **Fitbit stage sleep across the 2025 fall-back night.** Fitbit stage records are on the device's local clock, so the
   night the clocks went back (November 1 to 2, 2025) loses an hour; 66 of 72 extra nonreconciling logs started that
   night and keep the published hours [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 20:07]. See
   [Fitbit sleep](02-hourly-files.md#fitbit-sleep).
8. **Independent review** of both current files is owed ([review status](05-mood-timing.md#review-status)).

## Sources

- `<vault>/Audit Message Board.md`: posts of 2026-11-15 (Fitbit seasonal review), 2026-11-16 02:14, 12:45, 13:08,
  16:54, 16:58, 18:45, 18:51, 19:00, 19:38, 20:01, 20:07, 20:30; 2026-11-17 16:20 to 16:58, 17:52, 18:11, 23:03, 23:45;
  register rows CLK-01-R01 to R03 and HK-01-R11.
- `<vault>/Audit Decision Summary 2026-11-14.md`.
- `<vault>/Data Preprocessing/07 Current Files and Version Register.md`, `14 Fitbit Clock, Decision Time and Boundary Sources.md`,
  `15 Fitbit Transition and HealthKit Garmin Recovery.md`, `17 Full 2024 Cohort Follow-up Rebuild.md`,
  `21 IHS2025 Clock Evidence and Survey Probe.md`, `31 Coordinated 2025 Hourly Rebuild.md`.
- `<shared>/README.md`, section "Calendar and timestamps".
- `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` and `Validation2024.json`.
- `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md` and `MoodTimingValidation.json`.
- `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`; `<audit>/Opus/CLK-02/stage_clock_2025/STAGE_NOTE.md`.
- `<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`.
- `<audit>/Opus/Hourly2024-build/stage_b/stage_b_summary.json`.
- `<audit>/Codex/HourlyMerge20261117/REPORT.md`, `build_candidate.py`, `validate_candidate_release.log`,
  `audit/build_checks.json`, `audit/utc_consolidation.json`, `audit/utc_companions.json`.
- `<shared>/Rotation-1/Drew's code/causal/config/data_notes.yaml` and `paths.example.yaml`.
