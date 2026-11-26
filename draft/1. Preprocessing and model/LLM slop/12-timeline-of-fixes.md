# 12. Timeline of fixes

**Summary.** What was done to the data, in date order: from the first full exports in September 2026 to the
files and settings the current results use. Each row says what changed, what problem it fixed, whether it is in the
current files ("Now"), and which note has the detail. This page only orders what notes 02 to 11 already record. It
adds no new facts. Claude wrote it on 2026-11-26. Times are US Eastern, as posted on the audit board.

"Now" uses the notes' status words: **Applied** (in the current files or code), **Superseded** (replaced by a later
row), **Withheld**, **Approved, not applied**, **Partly applied**. Fixes found but not applied, and other open
problems, are listed in [3. Problems](../../3.%20Problems/01-from-the-preprocessing-notes.md).

## Before September 2026

The raw device exports and server data of each cohort were turned into hourly rows by the device-processing package:
one module per device and stream, summed or averaged to the hour. [01](01-raw-sources.md) describes the raw sources
and [02](02-hourly-files.md) how each stream becomes an hourly column.

## September and October 2026: first full builds

| When | What changed | Problem it fixed | Now | Detail |
|---|---|---|---|---|
| Sep 17 | Annual hourly export of both cohorts (151 columns). First 2024 decision export | First full-year files | Superseded | [02](02-hourly-files.md#version-history), [06](06-decisions-and-probabilities.md#superseded-2024-versions) |
| Sep 29 | Compact hourly rebuild: four device channels, an explicit clock per stream | The export showed unresolved hours at a fixed UTC−4 | Superseded; base of every later file | [02](02-hourly-files.md#version-history) |
| Sep 30 | Mood added; every local hour filled from first to last date; 56 `NA` accounts removed from 2024 | Mood not yet in the files; hours missing from the calendar; accounts marked `NA` | Superseded, but the account rule still applies. The 2025 mood clock set here was later found wrong (Nov 17) | [02](02-hourly-files.md#version-history) |
| Sep 30 | 2024 decision table rebuilt: failed and double send attempts removed, message probabilities added | Failed and duplicate attempts counted as decisions | Superseded Nov 16 | [06](06-decisions-and-probabilities.md#superseded-2024-versions) |
| Oct 1 | Five sleep columns added to both cohorts | No sleep data | Superseded by the November sleep rules | [02](02-hourly-files.md#version-history) |

## November 4 to 15: probabilities, Garmin, the 2024 full year

| When | What changed | Problem it fixed | Now | Detail |
|---|---|---|---|---|
| Nov 4 and 11 | 2025 Corral mixture probabilities built (Nov 4), then every 2025 probability scope released in one file (Nov 11) | The agent that chose each message was itself picked at random (Corral), so a message's probability depends on that draw too | Applied: the source of the released marginal probabilities | [06](06-decisions-and-probabilities.md#files-current) |
| Nov 11 to 13 | Garmin step data recovered from epoch files (about a million values) | Garmin step values missing from the 2025 file | Applied | [02](02-hourly-files.md#version-history), [01](01-raw-sources.md) |
| Nov 13 | 1,136 conflicting Garmin step values replaced (Drew) | The recovery disagreed with existing values | Applied; 16 kept and flagged | [04](04-audit-corrections.md#garmin-conflict-corrections-of-november-13) |
| Nov 13 | The joint audit starts: Codex and Claude on a shared board, Drew decides | | | [04](04-audit-corrections.md#how-the-audit-worked) |
| Nov 15 | 2024 file extended to the full study year (January to June 2025); Fitbit follow-up export moved one hour | 2024 wearable data ended in January 2025 while the study year ran to June; the follow-up Fitbit export was an hour early | Superseded by Stage C (Nov 17), which keeps both fixes | [02](02-hourly-files.md#version-history), [03](03-clocks-and-time-zones.md#fitbit-follow-up-export-one-hour-early) |

## November 16: the decision day

| When | What changed | Problem it fixed | Now | Detail |
|---|---|---|---|---|
| Nov 16 | 2024 decision table rebuilt from the full-year notification log | A server numbering bug had removed some sleep messages from the pool; failed sends had been treated as using up a message | Applied | [06](06-decisions-and-probabilities.md#how-the-2024-table-was-built-november-16-2026) |
| Nov 16 | Rules for which decisions count, both cohorts: windows start at the logged send; undelivered sends excluded; only no-send days a message could have reached; three whole 2025 days excluded | 2025 had used the date label, and about 23% of its "sent" decisions were never delivered | Applied | [07](07-outcome-windows.md#anchor), [06](06-decisions-and-probabilities.md) |
| Nov 16, 20:21 | 2025 decisions extended through June 30, 2026 (11,673 decisions) | The decision files stopped on June 19 | Applied to the decision files; the hourly data still stop around June 20 | [04](04-audit-corrections.md#2025-decision-files-june-tail-extension) |
| Nov 16 | Server pulls of time-zone evidence for 2025; clock versions 1 to 3 staged | The 2025 clock used each person's enrolment time zone, and 5.5% of Apple Health hours disagreed with the records' own offsets | Feeds the Nov 17 rebuild | [03](03-clocks-and-time-zones.md#evidence-gathered-on-2026-11-16), [03](03-clocks-and-time-zones.md#staged-clock-versions-1-to-3) |
| Nov 16, 18:45 to 20:19 | Drew approves the rebuild rules: one copy per step record, app priority, Garmin and Apple Watch resting heart rate, Fitbit brief wakes (2024), Fitbit sleep (2025), the 2025 day clock, the Garmin Connect resting-heart-rate date fix. Codex and Claude settle the 2025 Garmin sleep rule within his plan | Steps counted once per rewrite (2025 phone steps inflated by tens of millions); resting heart rate from the wrong daily value; sleep built in ways that disagreed with the devices | Applied in the Nov 17 builds, except 75 days of the date fix | [04](04-audit-corrections.md#correction-register) |

## November 17: the rebuilds

| When | What changed | Problem it fixed | Now | Detail |
|---|---|---|---|---|
| Nov 17, 15:41 to 16:24 | Holds for contradictory values; one row per UTC hour; values on quarter- and half-hour keys withheld | The same hour appeared on several rows; two values met in one hour | Applied | [04](04-audit-corrections.md#one-row-per-utc-hour) |
| Nov 17, 16:56 | 2025 coordinated rebuild published: Apple Health rebuilt on the server from each record's own UTC time; new sleep, resting-heart-rate and clock rules | Everything approved on Nov 16 for 2025 | Applied, except mood (next rows) | [04](04-audit-corrections.md#2025-apple-health-server-rebuild), [03](03-clocks-and-time-zones.md#what-the-november-17-file-applied) |
| Nov 17, 16:59 and 17:18 | 2024 Stages A and B: Fitbit brief wakes, Garmin resting heart rate, Garmin sleep zeros, baseline Fitbit steps | 2024 versions of the Nov 16 rules | Applied through Stage C | [04](04-audit-corrections.md#release-chain-of-the-hourly-files) |
| Nov 17, 17:52 to 18:11 | A full-file scan finds 2025 mood 4 to 8 hours early; Drew orders mood re-placed in both cohorts | The Sep 30 build read local survey times as UTC | Fixed at 22:16 | [05](05-mood-timing.md#the-problem-in-2025) |
| Nov 17, 18:43 | Drew approves iPhone-first phone steps; one server pass that evening returns the parts for both cohorts | Other apps' step counts were added to the iPhone's | Applied in 2024 (Stage C); **approved, not applied** in 2025 (the parts were never built into a file) | [04](04-audit-corrections.md#iphone-first-phone-step-column) |
| Nov 17, 21:35 | 2024 Stage C: Apple Health rebuilt on the server, iPhone-first, one row per UTC hour | 2024 versions of the same rules | Applied | [04](04-audit-corrections.md#2024-apple-health-server-rebuild-stage-c) |
| Nov 17, 22:16 | Mood-corrected pair: mood placed at each response's completion hour, both cohorts | The mood clock above | **Applied: these are the current hourly files.** Independent review still owed | [05](05-mood-timing.md), [05](05-mood-timing.md#review-status) |
| Nov 17, 23:03 | The engine switches to the mood-corrected pair | | Applied | [04](04-audit-corrections.md#release-chain-of-the-hourly-files) |
| Nov 17 | Analysis rules: steps need 10 worn hours; sleep judged by the night; pairwise positivity | | Applied | [04](04-audit-corrections.md#analysis-side-rules-agreed-in-the-same-period), [10](10-analysis-rules.md#positivity-pairwise-or-joint) |

## November 18 to 25: probabilities and analysis settings

| When | What changed | Problem it fixed | Now | Detail |
|---|---|---|---|---|
| Nov 18 | Review of the 2025 probability archive; three fixes proposed | The archived probabilities did not match the acting model on some days before September 28, 2025 | Proposed only; see Nov 19 and Nov 22 | [06](06-decisions-and-probabilities.md#known-source-quality-issues-that-remain-in-the-released-2025-probabilities) |
| Nov 19 | Fitted probabilities for September 4 to 27, 2025 withheld | A September 28, 2025 rerun with later models had overwritten those days' archives, and no reconstruction was good enough to publish | Withheld | [06](06-decisions-and-probabilities.md#september-4-27-2025-fitted-probabilities-withheld) |
| Nov 20 | A step window needs at least one step record; in the report and presentation, a day under one step counts as unmeasured | Blank cells were counted as zero steps | Applied (date of the engine change unverified) | [07](07-outcome-windows.md#where-code-and-documentation-disagree) |
| Nov 22 | Drew settles the 2025 weights: the released, posterior-averaged probabilities; report and presentation pool the cohorts after fitting | The decision-time vector is a single Thompson draw | Applied | [06](06-decisions-and-probabilities.md#randomization-probabilities-2025), [10](10-analysis-rules.md#pooling-the-cohorts) |
| Nov 23 | Engine 0.2.2: collinear controls detected and dropped | Earlier versions inverted singular matrices without warning, so some standard errors were wrong | Applied (working tree, uncommitted) | [11](11-model.md#the-collinearity-fault-and-its-fix) |
| Nov 24 | Smallest arm lowered from 200 to 50 messages in the report and presentation | At 200, many moderator levels were left blank | Applied | [10](10-analysis-rules.md#smallest-arm) |
| Nov 24 to 25 | Message tiers rebuilt; the thousands-comma faults found | | Nothing to fix: it records what participants saw | [06](06-decisions-and-probabilities.md#thousands-comma-faults-steps-statistics) |
