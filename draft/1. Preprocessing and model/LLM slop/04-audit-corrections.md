# Audit corrections, November 2026

Between 2026-11-13 and 2026-11-19 two AI agents, Codex and Claude, audited the IHS hourly files and decision tables
together on a shared message board, and Drew decided every rule choice. This note lists each correction that came out
of that audit: the problem, the rule, who decided and when, whether it is in the files the current results use, how
much it changed, and where the evidence is. Most hourly corrections reached the current files through three builds:
the November 17 rebuild of the 2025 file, the Stage A to C rebuild of the 2024 file, and the mood timing correction
of both. Several approved or proposed corrections are not in those files, most importantly the iPhone-first phone-step
rule for 2025 and 75 days of the Garmin Connect resting-heart-rate date fix; they are listed with their status and in
[items still open](#items-still-open).

## Contents

- [How the audit worked](#how-the-audit-worked)
- [Release chain of the hourly files](#release-chain-of-the-hourly-files)
- [Correction register](#correction-register)
- [Corrections in detail](#corrections-in-detail)
  - [Double-counted steps](#double-counted-steps)
  - [Garmin Connect step copies in phone steps](#garmin-connect-step-copies-in-phone-steps)
  - [App-priority rule](#app-priority-rule)
  - [iPhone-first phone step column](#iphone-first-phone-step-column)
  - [Day-long app step totals left as published](#day-long-app-step-totals-left-as-published)
  - [Garmin resting heart rate from the final daily summary](#garmin-resting-heart-rate-from-the-final-daily-summary)
  - [Garmin Connect resting heart rate date fix](#garmin-connect-resting-heart-rate-date-fix)
  - [Apple Watch resting heart rate last value of the day](#apple-watch-resting-heart-rate-last-value-of-the-day)
  - [2024 Fitbit brief wakes not counted as sleep](#2024-fitbit-brief-wakes-not-counted-as-sleep)
  - [2025 Fitbit sleep from stage records](#2025-fitbit-sleep-from-stage-records)
  - [2025 Garmin sleep revision-aware with summary fallback](#2025-garmin-sleep-revision-aware-with-summary-fallback)
  - [2024 Garmin sleep zero convention](#2024-garmin-sleep-zero-convention)
  - [2025 Apple Health server rebuild](#2025-apple-health-server-rebuild)
  - [2024 Apple Health server rebuild (Stage C)](#2024-apple-health-server-rebuild-stage-c)
  - [April to June 2024 baseline Fitbit steps](#april-to-june-2024-baseline-fitbit-steps)
  - [Heart-rate same-second holds and other source holds](#heart-rate-same-second-holds-and-other-source-holds)
  - [One row per UTC hour](#one-row-per-utc-hour)
  - [Garmin conflict corrections of November 13](#garmin-conflict-corrections-of-november-13)
  - [2025 decision files June tail extension](#2025-decision-files-june-tail-extension)
  - [Clock and mood corrections](#clock-and-mood-corrections)
  - [Corrections proposed or staged but not applied](#corrections-proposed-or-staged-but-not-applied)
  - [Analysis-side rules agreed in the same period](#analysis-side-rules-agreed-in-the-same-period)
- [Items still open](#items-still-open)
- [Sources](#sources)

## How the audit worked

- **Who.** Codex and Claude. Claude posted on the board as "Opus 5.5" and "Fable 5.2 (continuing the Opus thread)";
  these are the same Claude thread on two model versions. Drew made every rule choice and authorized every publication
  [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 16:03 and 17:38 (model switches noted);
  `<vault>/Audit Decision Summary 2026-11-14.md`].
- **Where.** Findings and replies go on `<vault>/Audit Message Board.md`, which also holds a register table of finding
  IDs (for example HK-01 for Apple Health identity, HR-01 for resting heart rate, CLK-01 and CLK-02 for clocks, SLP-01
  for sleep, SCAN-01 and SCAN-02 for full-file scans). Decisions are summarized in
  `<vault>/Audit Decision Summary 2026-11-14.md`, which was extended day by day through 2026-11-17. Work areas are
  `<audit>/Opus/` (Claude) and `<audit>/Codex/` [src: those files].
- **How a correction moved.** One agent found and staged a candidate as a separate file with hashes; the other
  reproduced it independently; Drew chose the rule; the builder made a full candidate file; the other agent reviewed
  it; publication only on Drew's word, with a backup and a dated manifest [src: `<vault>/Audit Decision Summary 2026-11-14.md`,
  section "How applying works"; `<vault>/Data Preprocessing/07 Current Files and Version Register.md`, "Version control procedure"].
- **The rebuild plan.** On 2026-11-16 at 18:45 Drew accepted five rule choices as a package ("Yes, use your picks"),
  added two more at 19:03 and settled others one at a time on 2026-11-16 and 2026-11-17. These are approvals of rules
  for the rebuilds, not of publication [src: `<vault>/Audit Message Board.md`, posts of 2026-11-16 18:45 and 19:03].
- Times below are US Eastern as posted on the board.

## Release chain of the hourly files

| Cohort | Version | SHA-256 prefix | Date | What it added | Status |
|---|---|---|---|---|---|
| 2025 | Garmin conflict correction | `962ea65a` | 2026-11-13 | 1,136 Garmin step values replaced | Superseded (base of the next) |
| 2025 | Coordinated rebuild, published root `dfHourly2025.csv` | `84555a10` | 2026-11-17 16:56 | Apple Health server rebuild, sleep fixes, RHR rules, clock, one row per UTC hour | Root file; base of the current file |
| 2025 | `Hourly_MoodCorrected_20261117/dfHourly2025.csv` | `2df0f3e1` | 2026-11-17 22:16 | Mood at each response's completion time | **Current results use this** |
| 2024 | Full-year expansion, published root `dfHourly2024.csv` | `67d15a8a` | 2026-11-15 | January to June 2025 added; Fitbit seasonal clock | Root file |
| 2024 | Stage A (staging) | `9e9dcb5d` | 2026-11-17 16:59 | Fitbit brief wakes; Garmin final-summary RHR to January 1, 2025 | Superseded (staging) |
| 2024 | Stage B (staging) | `b27caca2` | 2026-11-17 17:18 | Baseline Fitbit steps; Garmin RHR January to June 2025; Garmin sleep zeros | Superseded (staging) |
| 2024 | Stage C, `Hourly_FullYear_20261117_StageC/dfHourly2024.csv` | `a158a0a9` | 2026-11-17 21:35 | Apple Health server rebuild; iPhone-first phone steps; one row per UTC hour | Base of the current file |
| 2024 | `Hourly_MoodCorrected_20261117/dfHourly2024.csv` | `c16bd124` | 2026-11-17 22:16 | Mood rebuilt from offset-bearing responses | **Current results use this** |

[src: `<vault>/Data Preprocessing/07 Current Files and Version Register.md`; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`;
`<audit>/Opus/Hourly2024-build/stage_a/stage_a_summary.json`; `<audit>/Opus/Hourly2024-build/stage_b/stage_b_summary.json`;
`<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json`; `<shared>/Hourly_MoodCorrected_20261117/MoodTimingValidation.json`;
`<vault>/Audit Message Board.md`, posts of 2026-11-17 16:57, 21:35, 22:16, 23:03]

The engine switched to the two mood-corrected files on Drew's word on 2026-11-17 at 23:03, before their independent
review [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 23:03;
`<shared>/Rotation-1/Drew's code/causal/config/data_notes.yaml`]. "Applied" below means present in `c16bd124…`
(2024) or `2df0f3e1…` (2025).

## Correction register

Sizes are as reported by the builder or reviewer; "expected" means a preview count measured before the build. Columns
for 2024 and 2025 give the status in the current files.

| Correction | 2024 | 2025 | Decided | Size (headline) |
|---|---|---|---|---|
| [Double-counted steps: one copy per record](#double-counted-steps) | Applied (Stage C) | Applied | Drew, 2026-11-16 18:45 | 2025 published phone steps counted every rewrite: 71.6 M excess from identical rewrites; 46.47 M Garmin Connect and 30.35 M Oura excess over one copy per slot |
| [Garmin Connect step copies in phone steps](#garmin-connect-step-copies-in-phone-steps) | Applied (Stage C); staged 2024 candidate superseded | Applied | Drew, 2026-11-16 18:45 | 2024 frozen candidate: 7.29 M steps from 9,496 rows |
| [App priority: native Garmin and Oura](#app-priority-rule) | Applied (Stage C) | Applied | Drew, 2026-11-16 18:45; Oura 19:46 | Expected: 126.8 M Garmin Connect steps (2025), 61.1 M (2024); 83.5 M Oura steps (2025) |
| [iPhone-first phone step column for every app](#iphone-first-phone-step-column) | Applied (Stage C) | **Approved; not applied** (server parts returned, no 2025 candidate built) | Drew, 2026-11-17 18:43 | 2024: 8,811 cells lowered (19 people). 2025: about 22,600 to 28,600 hours (38 to 43 people) still summed |
| [Day-long app step totals left as published](#day-long-app-step-totals-left-as-published) | Applied (left as is; side list) | Applied (left as is; side list) | Drew, 2026-11-16 19:03 | Side list: 6,964 hours (2024), 8,049 (2025) |
| [Garmin RHR from the final daily summary](#garmin-resting-heart-rate-from-the-final-daily-summary) | Applied (Stages A, B) | Applied | Drew, 2026-11-16 18:45 | 2024: 2,499 + 1,834 days; 2025: 3,375 days |
| [Garmin Connect RHR date fix (A0)](#garmin-connect-resting-heart-rate-date-fix) | Not staged (no source) | **Applied for 29 days; 75 days open** | Drew, 2026-11-16 19:03 | 24 values changed, 5 blanked |
| [Apple Watch RHR, last value of the day](#apple-watch-resting-heart-rate-last-value-of-the-day) | Applied (Stage C) | Applied | Drew, 2026-11-16 18:45 | Expected: 56,592 of 116,026 Watch days differ by at least 1 bpm (2025); 43,432 of 60,685 days change (2024, July to December) |
| [2024 Fitbit brief wakes not counted as sleep](#2024-fitbit-brief-wakes-not-counted-as-sleep) | Applied (Stage A) | Not applicable (2025 rule below) | Drew, 2026-11-16 18:45 | 275,769 cells; 796,229.5 minutes removed |
| [2025 Fitbit sleep from stage records, 3-minute rule](#2025-fitbit-sleep-from-stage-records) | Not applicable | Applied | Drew, 2026-11-16 19:43 | 437,860 stage hours placed; 3,469 logs keep published hours |
| [2025 Garmin sleep, revision-aware, summary fallback](#2025-garmin-sleep-revision-aware-with-summary-fallback) | Not applied (2024 kept its own build) | Applied | Rule by Codex and Claude, 2026-11-16 20:01 to 20:19, within Drew's plan | 21,308 episodes; 178,779 hours placed; 118 tie hours blank |
| [2024 Garmin sleep zero convention](#2024-garmin-sleep-zero-convention) | Applied (Stage B) | Already the convention | Claude 2026-11-17 17:21; Codex agreed 17:39 | 118,303 zero cells blanked |
| [2025 Apple Health server rebuild (v3 rules)](#2025-apple-health-server-rebuild) | Not applicable | Applied | Drew authorized 2026-11-16 (build) and 2026-11-17 (merge) | 152 of 152 server batches; all Apple Health columns rebuilt from March 1, 2025 |
| [2024 Apple Health server rebuild (Stage C)](#2024-apple-health-server-rebuild-stage-c) | Applied | Not applicable | Drew, 2026-11-17 16:03 | All 2024 Apple Health columns rebuilt, November 18, 2023 to July 7, 2025 |
| [April to June 2024 baseline Fitbit steps](#april-to-june-2024-baseline-fitbit-steps) | Applied (Stage B) | Not applicable | Drew, 2026-11-17 17:21 | 152,179 of 159,244 hours placed |
| [Heart-rate same-second holds](#heart-rate-same-second-holds-and-other-source-holds) | Applied (same rule) | Applied | Drew, 2026-11-17 15:45 | 2025: 11,599 hours keep rebuilt value, 8 blank |
| [Step, sleep and RHR source holds](#heart-rate-same-second-holds-and-other-source-holds) | Applied | Applied | Codex and Claude, 2026-11-17 15:41 to 15:46 | 2025: 464 phone step hours, 23 sleep hours, 18 RHR days blank |
| [One row per UTC hour; contradictory values blank](#one-row-per-utc-hour) | Applied (Stage C) | Applied | Claude and Codex, 2026-11-17 16:20 to 16:21 | 2025: 620,644 split UTC hours merged; about 3,900 cell-hours withheld |
| [Garmin conflict corrections of November 13](#garmin-conflict-corrections-of-november-13) | Not applicable | Applied | Drew, 2026-11-13 | 1,136 values replaced; 16 kept and flagged |
| [2025 decision files, June 20 to 30 tail](#2025-decision-files-june-tail-extension) | Not applicable | Applied (decision files) | Drew, 2026-11-16 20:21 | 11,673 decisions added |
| [2025 clock, staged v3](03-clocks-and-time-zones.md#decisions-on-the-2025-clock) | Not applicable | Applied with holds | Drew, 2026-11-16 18:45 | See [clocks](03-clocks-and-time-zones.md#how-large-the-moves-were) |
| [Mood timing](05-mood-timing.md) | Applied | Applied | Drew, 2026-11-17 18:11 | 2025: 87,120 of 87,369 old positive mood hours vacated; 2024: no value changed at any existing UTC hour |
| [Watch sync summaries (HK-01-R01)](#corrections-proposed-or-staged-but-not-applied) | Not detected in 2024 | Staged, not applied | Never put to Drew | Staged: 5,766 hours, about 22.7 M steps |
| [June 18 to 20, 2026 Fitbit all-zero days](#corrections-proposed-or-staged-but-not-applied) | Not applicable | Proposed, not applied | Not decided | 6,004 cells |

## Corrections in detail

Each subsection gives Problem, Rule, Decided, Status, Size and Source. Sources are cited at the end of each item.

### Double-counted steps

**Problem.** The original 2025 build kept one row per sample key, so a step slot (participant, start, end) that a writer
re-sent counted once per write, even when the values were identical. Published 2025 phone steps (2,079,904,067) equal
the every-write total exactly; collapsing identical rewrites alone removes 71.6 M phone and 2.93 M watch steps. Against
one copy per slot (latest insertion) the excess was 46.47 M Garmin Connect steps (48 participants; 20.45 M in July to
December 2025) and 30.35 M Oura steps (42; 11.02 M), other writers under 0.35 M each (register row HK-01-R13). The 2024
original build was not affected (no sample keys; its `DISTINCT` collapsed repeats)
[src: `<vault>/Audit Message Board.md`, register row HK-01-R13; `<vault>/Audit Decision Summary 2026-11-14.md`, policy item i;
`<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`, item 3].

**Rule.** One copy of each record per (participant, device class, start, end), latest insertion; writers kept separate
during copy selection; source priority applied before copy selection [src: `<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`,
item 3; `<vault>/Audit Message Board.md`, post of 2026-11-16 20:01]. In the server rebuild: "latest copies per
writer/class/interval", with contradictory latest ties sent to holds [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`;
`<vault>/Audit Message Board.md`, post of 2026-11-16 20:48].

**Decided.** Drew, 2026-11-16 18:45, pick 2 of the rebuild plan [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 18:45].

**Status.** **Applied** in 2025 (server rebuild, November 17) and in 2024 (the 2024 server run used the same rules,
Stage C) [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`; `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`;
`<vault>/Audit Message Board.md`, post of 2026-11-17 16:03].

**Size in the release.** Not separately counted after the rebuild (the server applies all rules at once). The
measured excess above is the expected size. Oura's one-copy preview used the largest copy instead of the latest; the
difference was 95,285 steps (0.16%) [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 20:07].

### Garmin Connect step copies in phone steps

**Problem.** Garmin's phone app writes the watch's steps into Apple Health, where they land in `HealthkitPhone_steps`.
The copies repeat within an interval (79,574 repeated groups in 2025, 10,667 with different values), and many are
time-zone relabels of one sample: in 2024, 25,069 of 25,919 conflicting copies reappear at another local label with the
same instant and value. Because the 2024 build grouped phone rows by local hour and record offset, a relabelled copy
became a second row with the same UTC hour, which UTC windows count twice (register rows HK-01-F06, R08, R09, R11)
[src: `<vault>/Audit Message Board.md`, register rows HK-01-F06, HK-01-R08, HK-01-R09, HK-01-R11].

**Rule.** Pick 1 of the rebuild plan: Garmin Connect copies kept once (the staged latest-copy candidate). Pick 2 then
removes Garmin Connect from the phone column entirely for people with a native Garmin stream (see
[app priority](#app-priority-rule)); the one-copy rule acts on what remains [src: `<vault>/Audit Message Board.md`,
posts of 2026-11-16 18:45 and 19:38].

**Decided.** Drew, 2026-11-16 18:45. On 2026-11-14 three options had been put (latest copy, largest copy, or drop
Garmin Connect where the Garmin stream exists) [src: `<vault>/Audit Decision Summary 2026-11-14.md`, staged item 2].

**Status.** **Applied** in both cohorts through the server rebuilds. The frozen 2024 candidate
(`HealthkitPhoneSteps2024_GarminConnectOneCopy_candidate.csv.gz`: 9,496 rows, 25,086 copies, 7,285,779 steps removed,
2,454 rows blank) is **Superseded**: for 40 of the 46 participants with Garmin Connect records the app-priority rule
removes every copy, so the candidate would have mattered only for fewer than 10 participants (3,209 payloads, 1,183,579
steps) [src: `<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`, item 1 and addendum item 1].

**Size.** 2024 Jack-analysis preview on the July to December data: 1,112 HealthKit decisions changed, coverage flipped
in 20 post and 20 pre windows [src: `<vault>/Audit Decision Summary 2026-11-14.md`, staged item 2].

### App-priority rule

**Problem.** `HealthkitPhone_steps` adds the iPhone's own count to every app's count within an hour. Among 121 2025
participants with non-Apple phone records, 212,995 hours had two or more writers; top pairs were iPhone plus Garmin
Connect (104,368 hours) and iPhone plus Oura (86,364 hours) (register row HK-01-R02) [src: `<vault>/Audit Message Board.md`,
register row HK-01-R02].

**Rule.**
1. Where a participant has the device's own Garmin stream, Garmin Connect's copies are left out of the phone column
   (pick 2, 2026-11-16 18:45).
2. Oura: the hourly files have no Oura device column, so rule 1 had no trigger for Oura. Drew then chose "iPhone only":
   in an hour where the iPhone itself recorded steps, Oura's steps are left out; Oura-only hours stay, one copy each
   (2026-11-16 19:46). "iPhone" means phone-class records not written by any non-Apple app. Applied per final analysis
   hour, not to whole multi-hour intervals.
3. Order: source priority first, then one copy per record.

[src: `<vault>/Audit Message Board.md`, posts of 2026-11-16 18:45, 19:38, 19:46 and 20:01;
`<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`, addendum 2]

**Evidence for the Oura choice.** In 87,431 hours where both recorded steps, iPhone and Oura correlate 0.86 but Oura
reads about 20% higher (median ratio 1.20); adding them roughly doubles the count [src: `<vault>/Audit Message Board.md`,
post of 2026-11-16 19:43].

**Status.** **Applied** in 2025 (server rebuild: 71 native Garmin identities; positive native iPhone hours suppress
Oura) and in 2024 (2024 server run with 82 native Garmin identities) [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`;
`<vault>/Audit Message Board.md`, post of 2026-11-17 17:39; `<vault>/Server Pass Directions - Phone Step Parts.md`, section 3.1].

**Size (expected, local-hour previews).** Garmin Connect removal, 2025: 126,775,106 steps from 119,024 phone hours (37
participants), 25,978 hours left blank or zero; study year 87.5 M steps from 88,617 hours. 2024: 61,119,739 steps
from 84,070 hours (40 participants). Oura removal, 2025: 87,463 hours (42 participants), 83.5 M steps on the published
basis or 54.8 M on the one-copy basis; 23,896 Oura-only hours kept [src: `<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`,
addenda 1 and 2].

### iPhone-first phone step column

**Problem.** After the two rules above, every other app (Garmin Connect for people without a native Garmin stream,
RingConn, Ultrahuman, COROS, Huami and others) was still added to the iPhone's count. In the 2025 published file
(SCAN-02-F06): 22,608 person-hours for 38 people had iPhone plus an app that no rule removed, 0.81% of phone step hours,
concentrated in a few people; this caused most phone hours above 12,000 steps. The server components hold only the
hourly sum, so the parts could not be split locally [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 18:16
and 18:26 (correction); `<vault>/Server Pass Directions - Phone Step Parts.md`, section 1].

**Evidence for the rule.** When a phone and a wrist device both count an hour, the wrist counts more in 65% to 79% of
hours, and the phone total is 0.81 to 0.90 of the wrist total [src: `<vault>/Audit Message Board.md`, post of
2026-11-17 18:35].

**Rule.** For pulled participants, per UTC hour: if the iPhone is present (the v3 presence test), the iPhone group's
steps; otherwise the steps of the largest single app (apps are not added together); v3 conflict holds stay blank. Parts
are kept in a companion file so "the larger of the two" can be tried later [src: `<vault>/Server Pass Directions - Phone Step Parts.md`,
sections 2 and 4].

**Decided.** Drew, 2026-11-17 evening: "When you say iphone-first, I suppose that seems fine", and ordered a server pass
limited to the affected people [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 18:43].

**Status.**
- **2024: Applied** (Stage C). The server detected 43 people (19 on the staged list, 24 more); the split reproduces v3
  on all 217,671 tested hours (largest difference 3.6e-12 steps); 8,811 cells lowered for 19 participants, none raised,
  67 held; hours above 12,000 among those affected fell from 97 to 0, and cohort-wide from 115 to 18. The 24 Oura-only
  people are unchanged [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`phone`, `phone_subgroups`,
  `phone_extremes_all_cohort`); `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`].
- **2025: Approved, not applied.** The pull covered both cohorts in one launch and returned the 2025 parts (88 people
  pulled; run complete) [src: private server repository, `reports/phone-step-parts/parts-20261118T014838249448Z-cp000011.md`],
  but no 2025 rebuild with the parts exists in the records read; the current 2025 file changes mood only [src: `<vault>/Audit Message Board.md`,
  posts of 2026-11-17 19:05 and 22:16; `<vault>/Data Preprocessing/07 Current Files and Version Register.md`, note of
  November 17 ("The 2025 phone-step and Fitbit follow-ups remain separate from this timing correction")]. Expected size: about 28,600 hours for 43 people since March 1,
  2025 [src: `<vault>/Server Pass Directions - Phone Step Parts.md`, section 3.2].

### Day-long app step totals left as published

**Problem.** Some apps write a day's step total as one record of 23 hours or more; the build spreads it evenly over the
day's hours. 2024: 3,240 hours had only such spread steps, and 196 of Jack's 2024 HealthKit windows passed the 75%
coverage rule only because of them; 2025: 3,536 such hours (register row HK-01-R05) [src: `<vault>/Audit Message Board.md`,
register row HK-01-R05; `<vault>/Audit Decision Summary 2026-11-14.md`, policy item d].

**Rule.** Leave them as published (proportional allocation of long intervals), and keep a side list of the hours.

**Decided.** Drew, 2026-11-16 19:03: "I think we leave it, because we get the daily totals often from the hourly".
Side list: Drew, 2026-11-16 ("Sure we can keep the side list of which hours are spread-out totals"). The proposal to
treat these as daily, not hourly, values is **Rejected** [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 19:03;
`<vault>/Audit Decision Summary 2026-11-14.md`, "Side list"].

**Status.** **Applied** (unchanged): the server rebuild keeps proportional allocation for valid long intervals
[src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`]. Side list `<audit>/Opus/HK-01-R05-sidelist/`:
6,964 hours in 2024, 8,049 in 2025, built on the files of 2026-11-16 [src: `<vault>/Audit Decision Summary 2026-11-14.md`].
The server phone-parts companion has a `spread_total_steps` field for the pulled people [src: `<vault>/Server Pass Directions - Phone Step Parts.md`,
section 3.3].

### Garmin resting heart rate from the final daily summary

**Problem.** Garmin re-sends each day's summary as the day grows; the build averaged the distinct reported values
(`AVG(DISTINCT)`), mixing partial and final summaries. Partial values are higher on 91% (2024) and 94% (2025) of
affected days, so RHR was biased upward. In 2025 the longest summary is always the latest inserted (register rows
HR-01-R03, R05, F05) [src: `<vault>/Audit Message Board.md`, register rows HR-01-F05, HR-01-R03, HR-01-R05].

**Rule.** The day's summary with the longest duration. No ties at the longest duration with different values. One 2024
day held back because the source does not reproduce the published value [src: `<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`, item 4].

**Decided.** Drew, 2026-11-16 18:45 (pick 1) [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 18:45].

**Status and size.**
- **2025: Applied** (November 17). `Garmin_RHR` equals the frozen candidate on all 39,591 days: 3,375 changed, 36,216
  unchanged; 5,556 changed cells fall outside the Apple Health rebuild window (the rule applies to all dates)
  [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 16:09 and 16:20].
- **2024: Applied** in two parts. Stage A: 2,499 days, 65,840 cells (79 participants) through January 1, 2025; the
  published value matched the candidate's old value on every one [src: `<audit>/Opus/Hourly2024-build/stage_a/stage_a_summary.json`].
  Stage B1: January to June 2025, rebuilt by the same rule from the local daily summaries plus the November 15 transfer;
  1,834 of 12,225 days changed (44,004 cells, 76 people), median 1.5 bpm lower, 1,675 lowered and 159 raised
  [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 17:21; `<audit>/Opus/Hourly2024-build/stage_b/stage_b_summary.json`].
- Jack's 2024 pooled analysis preview: `RHR_pre` changed for 1,766 of 12,419 pooled Garmin decisions
  [src: `<vault>/Audit Decision Summary 2026-11-14.md`, staged item 1].

### Garmin Connect resting heart rate date fix

**Problem.** Garmin Connect writes daily RHR into Apple Health's phone class. Its records that start in the evening
are time-zone relabels of the next day: evening starts equal the next day's midnight value in 132 of 145 cases, against
8% to 9% by chance. The build grouped by start date, so 133 phone RHR days averaged a day's own value with the next
day's (register row HR-01-R06) [src: `<vault>/Audit Message Board.md`, register row HR-01-R06].

**Rule (candidate A0).** Move a record to the next date only when its value equals that date's midnight record (132 of
505 records qualify); eight same-date-only cases stay unmoved [src: `<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`, item 7].

**Decided.** Drew, 2026-11-16 19:03: "Apply it." [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 19:03].
On 2026-11-17 Codex and Claude narrowed what could be applied on the rebuilt base: only days where the raw snapshot
reproduces the server's day value [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 16:20 and 16:21].

**Status.**
- **2025: Applied for 29 days** (24 value changes, 5 blanks), confirmed by source count and value replay. **75 days
  are held and flagged** (67 that the local snapshot cannot replay, plus 8 first applied and then reverted); 8 more
  need no correction (no server day) [src: `<audit>/Codex/HourlyMerge20261117/audit/utc_consolidation.json` (`a0_final`);
  `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`]. Where measurable the change is a median 1.75 bpm,
  largest 4.5 [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 16:20].
- Surviving phone-class RHR records for the 2025 cohort were requested as a ride-along on the 2024 server run; the run
  manifest lists a component `A0_2025_PHONE_RHR` with 83 rows. No 2025 file applies them
  [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 16:03 and 17:39; `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json`
  (`source_manifest.components`)]. **Open.**
- **2024: Not staged.** The source needed is absent for 2024 [src: `<vault>/Audit Decision Summary 2026-11-14.md`, staged item 3].

### Apple Watch resting heart rate last value of the day

**Problem.** The Watch writes cumulative RHR updates during a day and deletes the old one each time; the surviving
sample is Apple's final daily value. The build averaged all updates. In 2025, 76,720 of 116,026 Watch days had more than
one sample and the average differed from the last by at least 1 bpm on 56,592 days; in published July to December
2024 data, using Apple's final estimate changes 43,432 of 60,685 days (median 1 bpm, mostly lower) (register rows
HR-01-R01, R07) [src: `<vault>/Audit Message Board.md`, register row HR-01-R01; `<vault>/Audit Decision Summary 2026-11-14.md`,
section "Watch resting heart rate deletions"; `<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`, item 5].

**Rule.** The sample with the latest end, then the latest inserted. Ties: the server returns a blank with a flag
[src: `<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`, item 5; `<vault>/Audit Message Board.md`, post of 2026-11-16 20:48].

**Decided.** Drew, 2026-11-16 18:45 (pick 3).

**Status.** **Applied** in 2025 on complete local days March 2, 2025 to July 6, 2026; extraction-edge days keep prior
values. Watch RHR equals the returned daily value on all 118,462 interior days [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`;
`<vault>/Audit Message Board.md`, post of 2026-11-17 16:20]. **Applied** in 2024 (Stage C) on complete interior dates;
the two extraction-boundary dates use legacy values where available; 314,996 grid days checked with no mismatch
[src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`; `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json`
(`day_value_checks`)].

**Related.** Phone-class RHR is all wearable- or app-written (mainly Garmin Connect), not measured by the phone; the
server rebuild uses the mean of distinct surviving values for it (register row HR-01-F01)
[src: `<vault>/Audit Message Board.md`, register row HR-01-F01; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`].
Day-to-day Watch RHR noise (10+ bpm jumps on 9.3% of consecutive days in 2025) was the same before the rule change
[src: `<vault>/Audit Message Board.md`, post of 2026-11-17 17:52 (SCAN-02-F05)].

### 2024 Fitbit brief wakes not counted as sleep

**Problem.** The published 2024 Fitbit sleep counted Fitbit's brief wakes (3 minutes or less) as sleep; Fitbit's own
nightly totals leave them out. Fitbit's summary light, deep and REM minutes each equal the detailed stage minus its own
brief wakes on 38,090 of 38,094 well-matched nights. Median overstatement 20.5 minutes per night (register row
SLP-01-R01) [src: `<vault>/Audit Decision Summary 2026-11-14.md`, section "Fitbit sleep overstated by short wakes";
`<vault>/Audit Message Board.md`, register row SLP-01-R01].

**Rule.** Subtract brief wakes only where the source fully supports it (Codex's candidate, 275,840 supported cells).
A further cluster of 1,380 nights about 3 minutes off Fitbit's total was **not** part of what Drew approved
[src: `<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`, item 6].

**Decided.** Drew, 2026-11-16 18:45 (pick 1).

**Status.** **Applied** (Stage A, carried into Stage C): 275,769 of 275,840 cells applied, each only where the
published value equalled the candidate's old value; 71 held because their local hour matched two rows and the candidate
had no UTC to choose; 796,229.5 minutes removed [src: `<audit>/Opus/Hourly2024-build/stage_a/stage_a_summary.json`;
`<vault>/Audit Message Board.md`, post of 2026-11-17 17:01]. Total Fitbit sleep in the 2024 file is 4.5% lower
[src: `<vault>/Audit Message Board.md`, post of 2026-11-17 23:03]. Jack-pipeline preview: Fitbit sleep sums change in
19,327 of 29,288 pooled post windows (median 20.5 minutes less), eligibility unchanged
[src: `<vault>/Audit Message Board.md`, register row SLP-01-R01].

### 2025 Fitbit sleep from stage records

**Problem.** Much 2025 Fitbit and Garmin hourly sleep was a nightly summary total spread evenly over the episode window
(SCAN-01-F02), and the stage records needed to place sleep by hour came back only in the second server batch on
2026-11-16 [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 01:53; `<shared>/README.md`, section "Sleep";
`<vault>/Audit Decision Summary 2026-11-14.md`, "Second batch"].

**Rule.** Hourly minutes asleep from stage records (the union of asleep intervals, minus only the brief wakes that lie
inside an asleep stage). A nightly log's stage placement is accepted when its total matches Fitbit's nightly total
within 3 minutes; otherwise, and for every overlapping log, the published hours for that log's span are kept and
flagged. Stage replacement also requires an accepted nightly log covering the hour [src: `<vault>/Audit Message Board.md`,
posts of 2026-11-16 19:00, 19:04, 19:38, 20:15].

**Decided.** Drew, 2026-11-16 19:43: "I think that proposal is good" [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 19:43].

**Status.** **Applied** (November 17). The fallback list grew from 3,391 logs to 3,469 after Codex tested the actual
corrected intervals (13,961 study-year hours kept as published); most of the added logs began the night the clocks went
back (November 1 to 2, 2025), when local-clock stage records lose an hour [src: `<vault>/Data Preprocessing/26 Validated Fitbit and Garmin Sleep Fixes.md`;
`<vault>/Audit Message Board.md`, post of 2026-11-16 20:07]. In the release: 449,228 valid stage hours, 437,860 placed,
11,368 kept as published because placement was ambiguous; 23,682 log-exception hours and 180 hours without reconciled
log coverage also keep the published value [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`].
The staged patch moved sleep between hours more than it changed the amount: 47,294 study-year cells changed by over 10
minutes while total minutes went from 19,976,692 to 19,995,746 [src: `<vault>/Audit Message Board.md`, post of
2026-11-16 20:19]. Detail: [Fitbit sleep](02-hourly-files.md#fitbit-sleep).

### 2025 Garmin sleep revision-aware with summary fallback

**Problem.** About half of Garmin's nightly summaries are repeats of the same night under a new id; the published file
did not separate them. The published Garmin hours matched the stage-based hours on 59% of hours and 86% of night totals,
and had no Garmin sleep for June 20 to 30, 2026 [src: `<vault>/Audit Decision Summary 2026-11-14.md`, "Garmin sleep by
stage"; `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`, section 27].

**Rule.** The existing Garmin processor's own selection, run on the returned records: validation labels joined to the
exact parent revision; the best-reconciling revision of each summary first, then ranking among overlapping summaries
(validation priority, usable stages, smaller stage discrepancy, latest inserted, earliest start). Summaries whose stages
overlap or do not reconcile use the processor's fallback: the summary duration (`DURATIONINSECONDS`) spread over the
window (duration plus awake plus unmeasurable). Naps are excluded and kept in a separate audit
[src: `<vault>/Data Preprocessing/26 Validated Fitbit and Garmin Sleep Fixes.md`; `<vault>/Audit Message Board.md`, posts
of 2026-11-16 20:01, 20:10, 20:15]. Claude's earlier versions v1 (latest inserted), v2 (own tiers), v3 and v4 are
**Superseded** [src: `<vault>/Audit Message Board.md`, post of 2026-11-16 20:19].

**Decided.** Drew's plan (pick 5, 2026-11-16 18:45) was to rebuild 2025 sleep once the Garmin stages returned; Drew
then asked Codex and Claude to fix the remaining Fitbit and Garmin issues together; the selection rule was settled
between them at 20:01 to 20:19. Equal-rank ties: blank, agreed 2026-11-17 15:46 to 15:57 [src: `<vault>/Audit Message Board.md`,
posts of 2026-11-16 18:45, 20:03, 20:19; 2026-11-17 15:46, 15:48, 15:57].

**Status.** **Applied** (November 17). Fresh revision labels select 21,308 episodes and 178,876 hours (21,058
exact-stage, 53 no-stage fallbacks, 197 stage-conflict fallbacks); an independent SQL replay matches every selection and
allocation. 13 episodes with equally ranked versions of different length (fewer than 10 people) are blank over 118
hours; 178,779 hours placed. Three hours cross into February 28, 2025 [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`;
`<vault>/Audit Message Board.md`, post of 2026-11-17 15:47]. **2024 Garmin sleep was not rebuilt with this rule**; it
keeps its own stage-based build with the zero convention below [src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`].

### 2024 Garmin sleep zero convention

**Problem.** In the 2024 file, Garmin sleep zeros were rare before January 2025 (0.1% to 0.2% of cells) but 65.0% of
cells in January to June 2025 (119,108 zeros), most of them far from any sleep: a rule seam at January 1, not a change
in sleep [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 17:01].

**Rule.** Follow the 2025 convention: a zero is kept only where its UTC hour overlaps a Garmin sleep summary's span;
other zeros become blank. Minutes asleep are unchanged [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 17:21].

**Decided.** Claude, 2026-11-17 17:21 (Stage B2), read from the published 2025 file; Codex confirmed the 2025
convention at 17:39. No Drew decision recorded [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 17:21 and 17:39].

**Status.** **Applied** (Stage B, into Stage C): 118,303 of 119,312 zero cells blanked; 813 kept inside spans; 196 on
rows without UTC kept [src: `<audit>/Opus/Hourly2024-build/stage_b/stage_b_summary.json`]. Under Jack's 75% coverage
rule this removes those windows from the sleep outcome (SCAN-02-F02); Claude flagged that the zero convention and the
coverage rule have to be chosen together [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 17:52].

### 2025 Apple Health server rebuild

**Problem.** The 2025 Apple Health columns were built from a nightly export that dropped each record's UTC offset,
deletions and app identity, and counted every rewrite (see above and [clocks](03-clocks-and-time-zones.md#how-2025-sources-store-time)).
The rules Drew approved need source names, deletions and record intervals that are only on the server
[src: `<vault>/Audit Message Board.md`, post of 2026-11-16 20:19 ("Not ready, needs a server build")].

**Rule (v3, as built).** From the server tables, March 1, 2025 to July 8, 2026 (exclusive), fixed 928 participants:
UTC source times; deletion tombstones by participant, key and type; sync and insertion lineage; latest copy per
writer, class and interval; manual entries excluded; native Garmin priority over Garmin Connect phone steps (71
identities); Oura left out of positive native iPhone hours; long step intervals allocated proportionally; sleep as the
union of asleep intervals, awake-only observed zeros, missing where there is no data; Watch RHR last value of the day;
phone RHR mean of distinct values. Contradictory latest copies go to holds [src: `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`;
`<vault>/Audit Message Board.md`, post of 2026-11-16 20:48].

**Decided.** Drew authorized writing the server rebuild on 2026-11-16 (20:30) and merging the reviewed components on
2026-11-17 (15:20); the file was published at 16:56 [src: `<vault>/Audit Message Board.md`, posts of 2026-11-16 20:30;
2026-11-17 15:20 and 16:57].

**Status.** **Applied.** The run completed 152 of 152 batches with no execution failure (413 verified chunks):
5,474,125 step hour rows, 2,339,666 heart-rate hour rows, 522,400 sleep hour rows, 129,361 RHR local-day rows (component
rows, not final hourly counts). All ten hourly Apple Health columns in the release equal the returned components by
participant and UTC hour, except the 450 conflicted phone step hours left blank; no old value is kept as a stand-in
[src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 15:02 and 16:20].

**Size.** Cells whose numeric value or missingness changed in the expanded intermediate relative to the old file
(moves between rows count): phone steps 640,975; watch steps 184,587; phone heart rate (mean) 112,696; watch heart rate
(mean) 225,195; phone sleep 494,507; watch sleep 700,347; watch RHR 1,789,587 (hourly repeats of daily values)
[src: `<audit>/Codex/HourlyMerge20261117/validate_candidate_release.log`].

### 2024 Apple Health server rebuild (Stage C)

**Problem.** The local July to December 2024 Apple Health export has device name and model only: no app identifier,
no sync metadata and no deletion records. The 2025 rules (app priority, Oura iPhone-first, deletions, versions,
placement by each record's UTC) could not be applied to that half of the 2024 year from local files; only January to
June 2025 had native records locally. Without a rebuild, the 2024 file would also switch rules at January 1, 2025
(Watch RHR about 1 bpm lower, phone steps 4.6% lower on the same hours) [src: `<vault>/Audit Message Board.md`, post of
2026-11-17 16:03; `<vault>/Audit Decision Summary 2026-11-14.md`, "Full-year merge reviewed"].

**Rule.** The 2025 v3 server rules, run on the 2024 cohort (931 people), full UTC calendar days November 18, 2023 to
July 7, 2025, 82 native Garmin step identities; then the iPhone-first phone split for the 43 detected people; then the
non-Apple-Health columns from Stage B; then one row per UTC hour [src: `<vault>/Audit Message Board.md`, posts of
2026-11-17 16:03, 17:39, 21:35; `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`].

**Decided.** Drew, 2026-11-17 16:03: "Yes we should do one more run. Have Codex build that server pull while we begin
our build locally for the hourly dataset" [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 16:03].

**Status.** **Applied** in the current 2024 file (Stage C is its base). The root `dfHourly2024.csv` was not replaced;
independent review of Stage C is owed [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 21:35 and 23:45;
`<vault>/Data Preprocessing/07 Current Files and Version Register.md`].

**Size.**
- Server components: 5,358,517 step hour rows, 2,350,160 heart-rate, 432,825 sleep, 137,413 RHR; 419 verified chunks
  [src: `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json` (`source_manifest`)].
- Output: 7,376,448 rows (from 7,462,876), 931 participants, 25 columns; zero readback differences; zero
  mismatches between each Apple Health column and its server component [src: same, `shape`, `healthkit_source_value_or_key_mismatches`].
- Source holds: steps 104 class-hours, sleep 92, heart rate 8,545, RHR 7 days [src: same, `source_hold_counts`].
- Phone split: see [iPhone-first](#iphone-first-phone-step-column). Hours above 12,000 steps across the file: 1,161 to
  56 against the November 15 file [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 23:03].
- Legacy hourly Apple Health values on the 124,883 rows without UTC (including the 20,269 phone-step cells that held
  2024 zero-duration Oura records) were moved to an exceptions archive; only UTC-placed rebuilt values enter the hourly
  columns [src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`; `<shared>/Hourly_FullYear_20261117_StageC/Validation2024.json`
  (`unknown_utc_hk_legacy`); `<vault>/Audit Message Board.md`, register row HK-01-R12].
- Rows analysed by the engine rose 7% for Apple sleep and 2% for Apple steps in 2024 [src: `<vault>/Audit Message Board.md`,
  post of 2026-11-17 23:45].

### April to June 2024 baseline Fitbit steps

**Problem.** The 2024 Fitbit minute-level step export starts exactly July 1, 2024, although daily totals show 10,515
baseline days with steps; baseline hourly Fitbit steps were missing at source (SCAN-01-F03)
[src: `<vault>/Audit Message Board.md`, register row SCAN-01-F03].

**Rule.** Hourly sums of the server's 2024 Fitbit step table for April 1 to July 1, 2024, filled only into existing rows
whose `Fitbit_steps` is blank, matched by participant and local hour; no rows added
[src: `<vault>/Audit Message Board.md`, posts of 2026-11-16 18:07 and 2026-11-17 17:21].

**Decided.** The pull: Drew, 2026-11-16 ("Yes, one batch", together with the June tail decisions and 2025 sleep
stages). Adding the steps: Drew, 2026-11-17 17:21 ("Yes, add them") [src: `<vault>/Audit Message Board.md`, posts of
2026-11-16 18:07 and 2026-11-17 17:21].

**Status.** **Applied** (Stage B). 159,244 staged hours (260 people) matched the returned source exactly and all 3,629
July 1 overlap hours matched published values. 152,179 hours filled; 7,065 not placed: 4,110 hours of fewer than 10
people not in the 2024 file, 2,951 hours (122 people) whose local hour matched two rows with different UTC hours, 4
hours on a date with no UTC row [src: `<audit>/Opus/Hourly2024-build/stage_b/stage_b_summary.json`;
`<vault>/Data Preprocessing/23 June Tail and Approved Rebuild Plan.md`].

### Heart-rate same-second holds and other source holds

**Problem.** The 2025 server rebuild set aside readings it could not rank: heart rate 265,732 same-second groups
(604,883 records, 414 people); steps 525 groups (1,118 records, 28 people); sleep 282 (289 records); RHR 6 groups
(12 records, fewer than 10 people) [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 15:02 and 15:41].
Claude's check against the raw snapshot: the heart-rate holds are separate readings from sensors that record about once
a second (91.7% from the system Bluetooth heart-rate writer) stored with whole-second times; the tied values differ by
1 bpm or less in 75.5% of slots; fewer than 10 people carry 96.8% of the records. The step holds include real
contradictions (one app's tied 30-minute copies sum to 12,989 or 133,174 steps depending on which is right). 281 of the
282 sleep holds have zero length [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 15:41].

**Rules.**
- Heart rate: the 11,607 touched hours keep the rebuilt mean and maximum from the surviving readings; not blanked; no
  old published value used; touched hours listed in `HealthKitHRHeldReadings2025.csv.gz`. An exact rerun keeping
  same-second readings was not requested.
- Steps: the 464 touched phone hours are blank (450 had a rebuilt value); no old value.
- Sleep: zero-length holds contribute nothing; the 23 phone hours under one 22.4-hour interval are blank.
- RHR: affected phone days blank (18 local days, including a date-mapping margin).
- No published fallback in any Apple Health stream.

[src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 15:41, 15:45, 15:46; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`]

**Decided.** Heart rate: Drew, 2026-11-17 15:45 ("Okay, I agree with your view!"), after three options. Steps, sleep,
RHR and no-fallback: settled between Claude (15:41) and Codex (15:46); not put to Drew [src: `<vault>/Audit Message Board.md`,
posts of 2026-11-17 15:45 and 15:46; `<vault>/Audit Decision Summary 2026-11-14.md`, "Heart-rate holds in the 2025 rebuild"].

**Status.** **Applied** in 2025: 11,599 touched hours keep their rebuilt value, 8 (every sample held) are blank
[src: `<audit>/Codex/HourlyMerge20261117/audit/utc_companions.json` (`hr_holds`)]. **Applied** in 2024 by the same rules
("Source-level conflicting readings are excluded"; conflicted step hours blank; positive-length sleep holds masked)
[src: `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md`; `<vault>/Audit Message Board.md`, post of 2026-11-17 16:03].

**Size of the heart-rate choice.** On 901 checkable touched hours, putting each held second back moves the hourly mean
by a median 0.23 bpm where under 10% was held and 0.67 bpm where 10% to 50% was held [src: `<vault>/Audit Message Board.md`,
post of 2026-11-17 15:41].

### One row per UTC hour

**Problem.** The first 2025 merge kept every old (participant, UTC, local) row beside the rebuilt rows, giving 620,644
participant-UTC hours split across two or more rows (31,354 before). Jack's notebook joins phone and watch on all three
keys, counts rows as observed hours and sums by UTC windows, so split hours could block watch-first filling,
double-count phone and watch, inflate RHR coverage and pick a stale local label [src: `<vault>/Audit Message Board.md`,
posts of 2026-11-17 16:15 and 16:20].

**Rule.** One row per participant and known UTC hour; rows without UTC stay separately keyed. A single value survives;
identical copies collapse; two different values meeting in one hour leave the cell blank with both kept in the audit,
never chosen by row order. Local label: the one consistent hourly label; else the approved day clock if it equals a
candidate; else blank. Daily RHR looked up once on the row's local date; blank when the date is unknown. A key map
traces every old row [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 16:20 and 16:21].

**Decided.** Proposed by Claude 2026-11-17 16:20, accepted by Codex 16:21, within Drew's merge authorization.

**Status.** **Applied** in 2025 (November 17) and 2024 (Stage C).
- 2025: 8,564,434 rows; withheld where two values met: Fitbit steps 559 hours, Fitbit heart rate 1,031 (mean) and
  1,013 (maximum), Fitbit sleep 880, Garmin heart rate 948 and 779; values on quarter- and half-hour keys withheld
  (12,035 UTC hours); 55,188 blank local labels; 852 RHR participant-days exist only in the daily companion
  [src: `<audit>/Codex/HourlyMerge20261117/audit/utc_consolidation.json`; `<vault>/Audit Message Board.md`, post of 2026-11-17 16:58].
- 2024: see [Stage C](#2024-apple-health-server-rebuild-stage-c) and [clocks](03-clocks-and-time-zones.md#local-labels-in-the-current-2024-file).

### Garmin conflict corrections of November 13

**Problem.** After the full-period Garmin epoch recovery, 1,152 existing 2025-cohort Garmin step values (June 2026)
disagreed with the epoch reconstruction, and 305 lacked a usable matching epoch [src: `<vault>/Data Preprocessing/07 Current Files and Version Register.md`,
"November 13 — initial full-period Garmin recovery"].

**Rule.** Replace a value with the epoch value when the source investigation supports it: 936 match an independently
corrected API reconstruction exactly; 200 have incomplete API data with matching daily epoch and summary totals. The
remaining 16 conflicts keep their value and are flagged (their epoch candidates are provisional because daily control
totals disagree); the 305 without a counterpart also stay and are flagged [src: `<vault>/Data Preprocessing/07 Current Files and Version Register.md`,
"November 13 — supported Garmin conflict correction"].

**Decided.** Drew, 2026-11-13, after Codex's source investigation [src: same].

**Status.** **Applied**: 1,136 values replaced (June 10 to 20, 2026); every other cell compared byte for byte; rewards
unchanged. All 1,136 replacements and the 16 retained values were checked unchanged in the November 17 rebuild and so
are in the current 2025 file [src: `<shared>/README.md`, "Supported Garmin conflict correction — November 13, 2026";
`<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md`]. The 16 conflicts and 305 values remain open
(register task GAR-25) [src: `<vault>/Audit Message Board.md`, register row GAR-25]. The Garmin epoch recoveries of
November 11 and 13 that preceded this are described in [raw sources](01-raw-sources.md) and
[hourly files](02-hourly-files.md).

### 2025 decision files June tail extension

The 2025 decision archive and published decision files ended June 19, 2026, although messages were logged through
June 30. The last eleven days were pulled from the server and appended: 11,673 decisions for 1,062 participants (6,250
assigned sends, 4,314 delivered; 5,423 no-sends). Every earlier row is unchanged. Released by Claude on Drew's word,
2026-11-16 20:21 ("Yes, release them"), after Codex built and Claude independently replayed the candidates. Status:
**Applied** (decision files; the hourly files were not touched) [src: `<shared>/backups/20261116_2025_june_tail_extension/APPLY_RECORD.json`;
`<shared>/README.md`, "November 16, 2026 — 2025 decisions extended through June 30, 2026"]. Fitbit, Garmin heart rate and
mood in the hourly file still stop around June 20, 2026; that tail was deferred by Drew (recorded as "can wait" in the phone-parts directions) [src: `<vault>/Audit Message Board.md`,
post of 2026-11-17 17:52 (SCAN-02-F03); `<vault>/Server Pass Directions - Phone Step Parts.md`, section 3.8]. Detail:
[decisions and probabilities](06-decisions-and-probabilities.md).

### Clock and mood corrections

- **2025 clock** (staged v3 tiers with holds; Apple Health by record UTC): [clocks and time zones](03-clocks-and-time-zones.md).
- **2024 Fitbit follow-up export one hour early** (applied November 15): [clocks](03-clocks-and-time-zones.md#fitbit-follow-up-export-one-hour-early).
- **Mood timing** (2025 mood 4 to 8 hours early; both cohorts rebuilt from completion times): [mood timing](05-mood-timing.md).

### Corrections proposed or staged but not applied

| Item | Cohort | What was found | Status | Source |
|---|---|---|---|---|
| Watch sync summaries duplicating fine samples (HK-01-R01) | 2025 | 23,601 Watch sync identities (25,881 records, 198 participants) equal the native records inside their interval; removing them changes 5,766 hours, about 22.7 M steps. Not detected in 2024 by a calibrated screen | **Staged, not applied** (candidate staged by Codex on 2026-11-13); never put to Drew; not in the rebuild plan. Sync deduplication alone does not remove them, and SCAN-02-F06 found single-writer overlapping Watch records in extreme hours of the current base file; whether the v3 copy rules removed any is **unverified** | `<vault>/Data Preprocessing/10 Audit Follow-up - Source Revisions and Review.md`; register rows HK-01-R01, R04; board, post of 2026-11-17 18:16 |
| Superseded RHR sync versions from three wearable apps (HR-01-F02) | 2025 | 74 phone RHR days (fewer than 10 participants), −4.0 to +0.5 bpm | **Superseded** by the server rebuild's sync-version rule; not re-counted on the rebuilt file | Register row HR-01-F02; `<vault>/Data Preprocessing/31 Coordinated 2025 Hourly Rebuild.md` |
| Late-synced 2024 Apple Health records (SRC-01-R01) | 2024 | A later export has 60,497 more step records (11.3 M steps, 135 people), about a third overlapping existing Watch records | **Superseded** by Stage C (the server run reads the current server records under the copy rules); not separately re-measured | `<vault>/Audit Decision Summary 2026-11-14.md`, policy item j |
| Zero-duration Oura point records on 2024 rows without UTC (HK-01-R12) | 2024 | 20,269 phone rows with blank UTC, 25.1 M steps; excluded from Jack's UTC windows | **Superseded** by Stage C (legacy local-only values archived; Apple Health rebuilt by UTC with iPhone-first) | Register row HK-01-R12; `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` |
| Garmin Connect one-copy candidate (2024) | 2024 | See [above](#garmin-connect-step-copies-in-phone-steps) | **Superseded** by Stage C | Freeze list, item 1 |
| Fitbit 3-minute nightly cluster (2024) | 2024 | 1,380 nights about 3 minutes off Fitbit's total; subtracting their timed brief wakes would cut the error from +23 to +3 minutes | **Proposed**, not part of Drew's approval | Register row SLP-01-R01; freeze list, item 6 |
| Fitbit RHR support gate (HR-01-F06) | Both | Flag or exclude days with an explicit zero heart-rate count and no data (9 published days; 35 raw-only 2024 days); keep null-count days | **Proposed**; no rule approved | `<vault>/Audit Decision Summary 2026-11-14.md`, policy item f |
| June 18 to 20, 2026 Fitbit all-zero days (SCAN-02-F03) | 2025 | The only Fitbit step zeros in the file: 6,004 cells, 134 to 190 people a day; 65 main windows pass coverage with zero steps | **Proposed** (blank them), asked of Codex; not applied | Board, posts of 2026-11-17 17:52 and 18:43 |
| June 20 to 30, 2026 mood, Fitbit and Garmin heart rate | 2025 | Hourly data stop at the June 20 snapshot; 7,350 main windows from June 21 have no mood and no Fitbit data | **Deferred** by Drew ("can wait", per the phone-parts directions) | Board, post of 2026-11-17 17:52; phone-parts directions, section 3.8 |
| Exact heart-rate variant keeping same-second readings | Both | See [holds](#heart-rate-same-second-holds-and-other-source-holds) | **Not requested** | Board, post of 2026-11-17 15:45 |
| 2025 iPhone-first phone steps | 2025 | See [iPhone-first](#iphone-first-phone-step-column) | **Approved; not applied** (server parts returned, not built) | Above |
| Timestamp parser for Jack's notebook (COV-01-F06) | Both | Jack's parser turned ISO local strings into missing values | **Applied in Drew's copy** of the notebook only; not a data change; Jack's code untouched | `<vault>/Audit Decision Summary 2026-11-14.md`, staged item 6 and "Decided by Drew on November 16 (evening)" |
| Repeated core message in the 2024 decisions (fewer than 10 participants) | 2024 | Staged correction of 152 rows | **Staged, not applied** ("fix at the next rebuild") | [Decisions](06-decisions-and-probabilities.md); `<vault>/Audit Decision Summary 2026-11-14.md` |

### Analysis-side rules agreed in the same period

These are rules for the analysis code, not changes to any file; they are listed so they are not mistaken for
preprocessing [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 18:26; `<vault>/Audit Decision Summary 2026-11-14.md`,
"Analysis rules agreed by Drew (November 17, evening)"]:

- Keeping an outcome window (Drew, 2026-11-17, "This all seems reasonable"): steps kept when the device shows at least
  H hours of wear (heart rate or steps; H a parameter, 10 to start), a blank step hour while worn counts as zero; sleep
  judged by the night (record exists; a record under 3 hours only if worn through the night; no record is missing);
  mood kept when a response exists.
- Resting heart rate (Drew, 2026-11-17, "These seem okay to do"): Apple Watch as a rolling median of the previous week
  with 8+ hours of wear; Garmin blank on days without overnight wear.
- 2025 windows anchor at the logged send; undelivered sends and retrospectively unreachable no-send days are out of the
  main analysis (Drew, 2026-11-16): see [decisions](06-decisions-and-probabilities.md).

## Items still open

1. **Independent review** of Stage C (`a158a0a9…`) and of both mood-corrected files is owed; the engine uses the files
   ahead of it [src: `<vault>/Audit Message Board.md`, posts of 2026-11-17 23:03 and 23:45]. No later review is recorded
   on the board through its last post of 2026-11-23.
2. **Root files not replaced.** `dfHourly2024.csv` is still the November 15 version and `dfHourly2025.csv` the November
   17 version without the mood fix; the engine overrides both until the reviewed files replace them
   [src: `<vault>/Data Preprocessing/07 Current Files and Version Register.md`; `<shared>/Rotation-1/Drew's code/causal/config/paths.example.yaml`].
3. **2025 iPhone-first phone steps** not applied: iPhone plus app hours (including Garmin Connect for people without a
   native Garmin stream) are still summed in 2025.
4. **A0, 75 phone RHR days** need the surviving server records (returned as an 83-row component, not applied).
5. **Fractional-offset hours** (12,035 in 2025; Stage C fractional cells in 2024) withheld pending an exact local rebucket.
6. **2025 Fitbit clock holds** (reminder-held, clock-change and unapproved-tier days) and the 2025 rows before March 1,
   2025 on the original clock map: see [clocks](03-clocks-and-time-zones.md#open-clock-items).
7. **June 2026 tail**: June 18 to 20 Fitbit zero days; June 20 to 30 mood, Fitbit and Garmin heart rate.
8. **Garmin**: 16 retained step conflicts and 305 values without an epoch counterpart (GAR-25); 2024 activity-component
   collisions (GAR-24, queued) [src: `<vault>/Audit Message Board.md`, register rows GAR-24, GAR-25].
9. **Watch overlapping records** (HK-01-R01, SCAN-02-F06): unsized beyond 148 extreme hours; the optional sizing in the
   phone-parts pass was deferred [src: `<vault>/Audit Message Board.md`, post of 2026-11-17 19:05].
10. **RHR availability timing** (HR-01-F03): daily RHR is a retrospective value; a lag or as-of rule is an analysis
    choice (partly settled by the rolling-median rule above) [src: `<vault>/Audit Decision Summary 2026-11-14.md`, policy item a].
11. **Smaller items** raised in the November 15 review and not re-checked on the rebuilt files: a smart scale's readings
    in phone-class RHR; Watch RHR days above 120 bpm [src: `<vault>/Audit Decision Summary 2026-11-14.md`, "Full-year
    merge reviewed"]. **Unverified** whether Stage C changed them.
12. **Dropbox copies** of all files are unverified against the local hashes [src: `<vault>/Data Preprocessing/07 Current Files and Version Register.md`].

## Sources

- `<vault>/Audit Message Board.md`: register rows (HK-01, HR-01, CLK-01, SLP-01, SCAN-01, GAR); posts of 2026-11-16
  18:45, 19:00, 19:03, 19:04, 19:38, 19:43, 19:46, 20:01, 20:03, 20:07, 20:10, 20:15, 20:19, 20:30, 20:48;
  2026-11-17 15:02 to 16:58, 17:01, 17:21, 17:39, 17:52, 18:11, 18:16, 18:26, 18:35, 18:43, 19:05, 21:35, 22:16,
  23:03, 23:45.
- `<vault>/Audit Decision Summary 2026-11-14.md`.
- `<vault>/Server Pass Directions - Phone Step Parts.md`.
- `<vault>/Data Preprocessing/07 Current Files and Version Register.md`, `10 Audit Follow-up - Source Revisions and Review.md`,
  `23 June Tail and Approved Rebuild Plan.md`, `26 Validated Fitbit and Garmin Sleep Fixes.md`,
  `31 Coordinated 2025 Hourly Rebuild.md`.
- `<shared>/README.md`; `<shared>/backups/20261116_2025_june_tail_extension/APPLY_RECORD.json`.
- `<shared>/Hourly_FullYear_20261117_StageC/Hourly2024Report.md` and `Validation2024.json`.
- `<shared>/Hourly_MoodCorrected_20261117/MoodTimingReport.md` and `MoodTimingValidation.json`.
- `<audit>/Opus/FreezeList-20261116/FREEZE_LIST.md`; `<audit>/Opus/Hourly2024-build/stage_a/stage_a_summary.json`;
  `<audit>/Opus/Hourly2024-build/stage_b/stage_b_summary.json`; `<audit>/Opus/CLK-02/CLK-02_Update_Fable_20261116.md`.
- `<audit>/Codex/HourlyMerge20261117/REPORT.md`, `validate_candidate_release.log`, `audit/utc_consolidation.json`,
  `audit/utc_companions.json`.
- `<shared>/Rotation-1/Drew's code/causal/config/data_notes.yaml` and `paths.example.yaml`.
