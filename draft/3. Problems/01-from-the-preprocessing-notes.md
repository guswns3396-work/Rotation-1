# Problems found while writing the preprocessing notes

**Summary.** Twenty-two problems, open questions and owed checks that turned up while writing the detailed
preprocessing notes in [`1. Preprocessing and model/LLM slop/`](../1.%20Preprocessing%20and%20model/LLM%20slop/00-overview.md).
Each entry says what it is, what it affects, whether fixing it could change the current numbers, its status, a next
step, and where the detail is. Claude wrote this on 2026-11-25 from those notes, which two reviewers had checked against
the code and records. The "could change numbers" judgments and the next steps are Claude's, not measured effects or
decisions. Placeholders such as `<vault>` and `<scratch>` are explained in the
[overview](../1.%20Preprocessing%20and%20model/LLM%20slop/00-overview.md#how-to-read-these-notes).

## Contents

- [How to read the entries](#how-to-read-the-entries)
- [At a glance](#at-a-glance)
- [Where to start](#where-to-start)
- [Data the results rest on](#data-the-results-rest-on): P01 to P07
- [Clocks and timing](#clocks-and-timing): P08
- [Decisions and probabilities](#decisions-and-probabilities): P09 to P13
- [Moderators](#moderators): P14 to P16
- [Pipeline and reproducibility](#pipeline-and-reproducibility): P17 to P20
- [Documentation](#documentation): P21
- [Other unconfirmed facts](#other-unconfirmed-facts): P22

## How to read the entries

- **Status** uses the notes' words: Applied, Staged (not applied), Proposed, Approved (not applied), Held, Deferred,
  Open, Unverified.
- **Could change numbers?**
  - **Yes**: fixing it changes data or rows the current results use.
  - **Possibly**: it might, depending on a check not yet done.
  - **Reading**: the numbers stay; what they mean, or how they are labelled, changes.
  - **Rebuild**: the numbers stay; it affects whether someone else can rebuild them.
  - **Docs**: a document is wrong; the code and the numbers are not.
- IDs are stable, so other text can link to `#p03-...` headings.

## At a glance

| ID | Problem | Cohort | Could change numbers? | Status |
|---|---|---|---|---|
| [P01](#p01-the-current-hourly-files-have-not-been-independently-reviewed) | The current hourly files have not been independently reviewed | Both | Possibly | Open |
| [P02](#p02-the-hourly-files-at-the-top-of-the-shared-folder-are-older-versions) | The hourly files at the top of the shared folder are older versions | Both | No, for current results | Waits on P01 |
| [P03](#p03-the-2025-iphone-first-phone-step-rule-is-approved-but-not-built) | The 2025 iPhone-first phone-step rule is approved but not built | 2025 | Yes | Approved, not applied |
| [P04](#p04-apple-watch-sync-summaries-that-repeat-the-fine-samples) | Apple Watch sync summaries that repeat the fine samples | 2025 | Possibly | Staged, not applied |
| [P05](#p05-75-garmin-connect-resting-heart-rate-days-not-re-dated) | 75 Garmin Connect resting heart rate days not re-dated | 2025 | Yes, slightly | Held |
| [P06](#p06-the-last-days-of-the-2025-data-june-18-to-30-2026) | The last days of the 2025 data, June 18 to 30, 2026 | 2025 | Yes, slightly | Proposed; deferred |
| [P07](#p07-smaller-staged-or-proposed-data-fixes) | Smaller staged or proposed data fixes | Both | Slightly | Various |
| [P08](#p08-the-2025-clock-fix-is-partial) | The 2025 clock fix is partial | Both | Possibly | Applied with holds |
| [P09](#p09-two-counts-of-the-2025-decisions) | Two counts of the 2025 decisions | 2025 | Possibly | Unverified |
| [P10](#p10-known-weaknesses-in-the-released-2025-probabilities) | Known weaknesses in the released 2025 probabilities | 2025 | Possibly | Released as is |
| [P11](#p11-little-overlap-in-2025-sleep-weeks) | Little overlap in 2025 sleep weeks | 2025 | Reading | Fact of the trial |
| [P12](#p12-steps-messages-did-not-show-what-their-labels-say) | Steps messages did not show what their labels say | Both | Reading | Fact of the trial |
| [P13](#p13-2024-decisions-are-partly-inferred-and-reach-is-retrospective) | 2024 decisions are partly inferred, and reach is retrospective | Both | Possibly | Open |
| [P14](#p14-not-every-moderator-is-measured-before-the-decision) | Not every moderator is measured before the decision | Both | Reading | Open |
| [P15](#p15-the-report-and-the-presentation-split-moderators-differently) | The report and the presentation split moderators differently | Both | Yes, between the two documents | Open |
| [P16](#p16-inputs-used-as-supplied) | Inputs used as supplied | Both | Possibly | Unverified |
| [P17](#p17-the-presentation-cannot-be-rebuilt-from-the-repository) | The presentation cannot be rebuilt from the repository | Both | Rebuild | Open |
| [P18](#p18-the-presentations-tables-skip-the-reports-privacy-guard) | The presentation's tables skip the report's privacy guard | Both | No | Open |
| [P19](#p19-one-cohort-rows-labelled-pooled-in-the-presentation) | One-cohort rows labelled "pooled" in the presentation | 2024 | Reading | Open |
| [P20](#p20-stored-results-and-uncommitted-engine-code) | Stored results and uncommitted engine code | Both | Possibly | Open |
| [P21](#p21-documentation-that-lags-the-code) | Documentation that lags the code | Both | Docs | Open |
| [P22](#p22-other-unconfirmed-facts) | Other unconfirmed facts | Both | Mostly no | Unverified |

## Where to start

Claude's suggestion, if only a few get done:

1. **P17, the scratch scripts.** Four scripts behind the presentation sit in a temporary folder that can be cleared.
   Moving them is quick and prevents a loss.
2. **P01, the review.** Every result uses the unreviewed hourly files.
3. **P03, P05 and P06 in one 2025 rebuild.** The server parts for P03 and P05 have already been returned.
4. **P09, one count.** A cross-tabulation of two flags settles it.
5. **P18 before the presentation is shared further.**

## Data the results rest on

### P01. The current hourly files have not been independently reviewed

- **What.** Every current result uses the mood-corrected hourly pair (`Hourly_MoodCorrected_20261117`), whose 2024 file
  is the Stage C rebuild with mood re-placed. They were put into use on 2026-11-17 with their review still owed. No
  review is recorded on the audit board through its last post of 2026-11-23, and the engine's data note still says
  "under independent review".
- **Affects.** Every outcome, day-before value and hourly moderator, in both cohorts.
- **Could change numbers?** Possibly.
- **Status.** Open.
- **Next step.** A review that compares placement with the raw sources (the hour of day against the raw time, agreement
  across devices), not only counts and totals. The audit's own lesson: a conservation check passes when values are moved
  wrongly or not moved at all.
- **Detail.** [05, Review status](../1.%20Preprocessing%20and%20model/LLM%20slop/05-mood-timing.md#review-status);
  [04, Items still open](../1.%20Preprocessing%20and%20model/LLM%20slop/04-audit-corrections.md#items-still-open).

### P02. The hourly files at the top of the shared folder are older versions

- **What.** The shared folder's `dfHourly2024.csv` is the November 15 version and its `dfHourly2025.csv` the November 17
  version without the mood fix. The engine reads the newer pair through its per-machine paths file. Anything that reads
  the root files directly gets different data from the results.
- **Affects.** Work done on the root files.
- **Could change numbers?** No, for the current results; yes, for anything built on the root files.
- **Status.** Waits on P01: the root files are to be replaced once the reviewed files are accepted.
- **Next step.** Replace them after the review, or say at the top of the shared README which pair is current.
- **Detail.** [04, Items still open](../1.%20Preprocessing%20and%20model/LLM%20slop/04-audit-corrections.md#items-still-open);
  [02, Which files current results use](../1.%20Preprocessing%20and%20model/LLM%20slop/02-hourly-files.md#which-files-current-results-use).

### P03. The 2025 iPhone-first phone-step rule is approved but not built

- **What.** In 2025 the phone step column still adds other apps' counts to the iPhone's (Garmin Connect for people
  without a native Garmin stream, RingConn, Ultrahuman, COROS, Huami and others). In the published file 22,608
  person-hours for 38 people had an iPhone count plus an app count that no rule removed, 0.81% of phone step hours,
  concentrated in a few people; they caused most phone hours above 12,000 steps. Drew approved the iPhone-first rule on
  2026-11-17. The server pass returned the 2025 parts (88 people), but no 2025 file was built from them. 2024 has the
  rule (Stage C).
- **Affects.** 2025 steps outcomes and step day-before values for the people concerned; phone-device views.
- **Could change numbers?** Yes, for 2025 steps.
- **Status.** Approved, not applied.
- **Next step.** Build the 2025 phone column from the returned parts as was done for 2024, then rerun.
- **Detail.** [04, iPhone-first phone step column](../1.%20Preprocessing%20and%20model/LLM%20slop/04-audit-corrections.md#iphone-first-phone-step-column).

### P04. Apple Watch sync summaries that repeat the fine samples

- **What.** In 2025, 23,601 Watch sync summaries (25,881 records, 198 participants) equal the native records inside
  their interval. Removing them would change 5,766 hours, about 22.7 million steps. Codex staged a candidate on
  2026-11-13; it was never put to Drew and is not in the rebuild plan. Whether the November copy rules already removed
  some of them is unverified, and a later scan found overlapping Watch records in extreme hours of the current base file.
- **Affects.** 2025 steps on Apple Watch hours.
- **Could change numbers?** Possibly; yes if the duplicates are still in the file.
- **Status.** Staged, not applied; unverified.
- **Next step.** Count how many of the staged duplicates remain in the current 2025 file, then put the rule to Drew.
- **Detail.** [04, Corrections proposed or staged but not applied](../1.%20Preprocessing%20and%20model/LLM%20slop/04-audit-corrections.md#corrections-proposed-or-staged-but-not-applied)
  (HK-01-R01); [04, Items still open](../1.%20Preprocessing%20and%20model/LLM%20slop/04-audit-corrections.md#items-still-open), item 9.

### P05. 75 Garmin Connect resting heart rate days not re-dated

- **What.** Garmin Connect writes the day's resting heart rate into Apple Health at the next midnight, so the build
  averaged two days' values on some dates. Drew approved the date fix on 2026-11-16. It is applied to 29 days in 2025
  (24 values changed, 5 blanked). 75 days are held and flagged: 67 that the local snapshot cannot replay and 8 that were
  applied and then reverted. The server returned an 83-row component for them; no 2025 file applies it. Where measured,
  the change is a median 1.75 bpm, at most 4.5.
- **Affects.** 2025 resting heart rate. The engine's DR-WCLS outcome model uses it; the report's and presentation's
  standard figures do not.
- **Could change numbers?** Yes, slightly, where resting heart rate is used.
- **Status.** Applied for 29 days; 75 held.
- **Next step.** Apply the returned component at the next 2025 rebuild (with P03).
- **Detail.** [04, Garmin Connect resting heart rate date fix](../1.%20Preprocessing%20and%20model/LLM%20slop/04-audit-corrections.md#garmin-connect-resting-heart-rate-date-fix).

### P06. The last days of the 2025 data, June 18 to 30, 2026

- **What.** Decisions run to June 30, 2026, but Fitbit, Garmin heart rate and mood in the hourly file stop at the June
  20 snapshot: 7,350 main windows from June 21 have no mood and no Fitbit data. June 18 to 20 also hold the file's only
  Fitbit step zeros (6,004 cells, 134 to 190 people a day), and 65 main windows pass the coverage rule with zero steps.
  Blanking those zeros was proposed. Filling the tail needs a server pull, which Drew deferred ("can wait").
- **Affects.** 2025 whole-year and January to June periods. In the last ten days mood stops for everyone, and Fitbit
  users lose their steps and sleep outcomes while people on other devices keep theirs, so the mix of people changes.
  The report and the presentation already drop zero-step windows; the engine's own analyses do not.
- **Could change numbers?** Yes, slightly.
- **Status.** Zeros: Proposed. Tail: Deferred.
- **Next step.** Blank the June 18 to 20 Fitbit zeros, and either pull the tail or end 2025 analyses at June 20.
- **Detail.** [04, 2025 decision files June tail extension](../1.%20Preprocessing%20and%20model/LLM%20slop/04-audit-corrections.md#2025-decision-files-june-tail-extension);
  [04, Corrections proposed or staged but not applied](../1.%20Preprocessing%20and%20model/LLM%20slop/04-audit-corrections.md#corrections-proposed-or-staged-but-not-applied).

### P07. Smaller staged or proposed data fixes

| Item | Cohort | Size | Status |
|---|---|---|---|
| Fitbit nights about 3 minutes off the device's own total; subtracting their timed brief wakes would cut the error from +23 to +3 minutes | 2024 | 1,380 nights | Proposed |
| Fitbit resting heart rate on days with an explicit zero heart-rate count and no data | Both | 9 published days | Proposed |
| Garmin step conflicts kept and flagged; values without an epoch counterpart (GAR-25) | 2025 | 16 and 305 values | Open |
| Garmin equal-count activity components, July to December (GAR-24) | 2024 | Not sized | Proposed |
| Repeated core message in the decisions | 2024 | 152 rows, fewer than 10 participants | Staged, not applied |
| Values on quarter- and half-hour UTC keys, withheld until an exact local rebucket | Both | 12,035 hours in 2025 | Withheld; rebucket proposed |
| Heart-rate variant keeping same-second readings | Both | Not sized | Not requested |

- **Could change numbers?** Slightly, in the streams named.
- **Next step.** Fold these into the next rebuild with P03 and P05.
- **Detail.** [04, Corrections proposed or staged but not applied](../1.%20Preprocessing%20and%20model/LLM%20slop/04-audit-corrections.md#corrections-proposed-or-staged-but-not-applied);
  [04, Items still open](../1.%20Preprocessing%20and%20model/LLM%20slop/04-audit-corrections.md#items-still-open);
  [02, Open items](../1.%20Preprocessing%20and%20model/LLM%20slop/02-hourly-files.md#open-items).

## Clocks and timing

### P08. The 2025 clock fix is partial

- **What.** In 2025, Apple Health is placed by each record's own UTC time and Fitbit by an approved day-level clock.
  Fitbit keeps its original placement on held days: 754 reminder-held days, 1,214 clock-change days, days with an
  unapproved tier or none, and days with an offset that is not a whole hour. A later check found held Fitbit hours off
  the hour for fewer than 10 of 21 testable people. Rows before March 1, 2025 (baseline) keep the original clock.
- **Also.**
  - 55,188 known UTC hours in 2025 (763 since filled by the mood correction) and 57,431 in 2024 have no local time
    label, so local-time features there are missing.
  - The engine drops 124,883 2024 rows that have no UTC hour.
  - 2024 Fitbit sleep from January 1 to March 9, 2025 was not shifted with steps and heart rate; untested.
  - Fitbit stage sleep loses an hour on the night the clocks went back (November 1 to 2, 2025).
- **Affects.** 2025 Fitbit outcomes on held days; baseline values before March 2025; local-time features in both cohorts.
- **Could change numbers?** Possibly.
- **Status.** Applied with holds; the rest Open.
- **Next step.** Count how many analysed windows fall on held Fitbit days, to see whether the holds matter.
- **Detail.** [03, Status summary](../1.%20Preprocessing%20and%20model/LLM%20slop/03-clocks-and-time-zones.md#status-summary);
  [03, Open clock items](../1.%20Preprocessing%20and%20model/LLM%20slop/03-clocks-and-time-zones.md#open-clock-items).

## Decisions and probabilities

### P09. Two counts of the 2025 decisions

- **What.** The engine keeps 296,194 decisions (the decision-level reach flag) and builds its own windows to the next
  decision. The published window grid's flag marks 294,777 (292,441 with history). Nobody has checked how the two sets
  differ, or whether the difference of 1,417 is decisions the published grid left out for a reason.
- **Affects.** The 2025 sample in every analysis.
- **Could change numbers?** Possibly; at most about 0.5% of 2025 decisions.
- **Status.** Unverified.
- **Next step.** Cross-tabulate the two flags and state which count the results use.
- **Detail.** [06, Facts other notes should carry](../1.%20Preprocessing%20and%20model/LLM%20slop/06-decisions-and-probabilities.md#facts-other-notes-should-carry);
  [07, Unverified](../1.%20Preprocessing%20and%20model/LLM%20slop/07-outcome-windows.md#unverified).

### P10. Known weaknesses in the released 2025 probabilities

- **What.** The released probabilities are kept by Drew's decision of 2026-11-22, with these weaknesses:
  - On some days before September 28, 2025 the archive does not match the acting model (23,879 decisions labelled "later
    model", 31,068 "not aligned"). Only September 4 to 27 is withheld.
  - Corral mixtures are rebuilt from rounded weights and finite Monte Carlo draws, not certified propensities.
  - The probability of a Random fallback is not reconstructed.
  - 1,426 recorded actions have probability 0 in the archived vector; the floor removes them from comparisons with that
    type.
  - An `archive_alignment` label was proposed and not built.
- **Affects.** 2025 weights, in every 2025 comparison.
- **Could change numbers?** Possibly.
- **Status.** Released as is; the label is Proposed.
- **Next step.** Build the alignment label and, as a check, rerun the main comparisons on aligned days only.
- **Detail.** [06, Known source-quality issues](../1.%20Preprocessing%20and%20model/LLM%20slop/06-decisions-and-probabilities.md#known-source-quality-issues-that-remain-in-the-released-2025-probabilities);
  [06, Open and unverified items](../1.%20Preprocessing%20and%20model/LLM%20slop/06-decisions-and-probabilities.md#open-and-unverified-items).

### P11. Little overlap in 2025 sleep weeks

- **What.** After late October 2025 the fitted sleep policy sends almost only one message type (BSData), and its other
  type probabilities often fall below the floor. Sleep-week strategy and type comparisons therefore rest mainly on
  decisions before October 27, 2025 and on Random-policy rows. The pairwise floor drops 16% to 46% of sleep-week
  decisions per arm, against 8% to 15% in step weeks; 2024 loses almost nothing.
- **Affects.** 2025 sleep-week comparisons.
- **Could change numbers?** Reading: these estimates describe a narrower set of weeks than "whole year" suggests.
- **Status.** A fact of the trial.
- **Next step.** State the effective date range beside sleep-week results.
- **Detail.** [06, Clipping, floors and renormalization](../1.%20Preprocessing%20and%20model/LLM%20slop/06-decisions-and-probabilities.md#clipping-floors-and-renormalization);
  [06, Facts other notes should carry](../1.%20Preprocessing%20and%20model/LLM%20slop/06-decisions-and-probabilities.md#facts-other-notes-should-carry).

### P12. Steps messages did not show what their labels say

- **What.** Step statistics were stored as text with a thousands comma ("12,345").
  - **2025:** the server could not read them, so 97% of sent steps messages were the neutral, generic variant, and steps
    "data" messages almost never showed a number.
  - **2024:** the server read only the digits before the comma, so 72% of steps messages were framed "low" and none
    "high", though the number shown was correct.
- **Affects.** Every "data versus no data" or tier comparison in the steps domain. The 2025 steps contrast does not test
  data display.
- **Could change numbers?** Reading. The data and probabilities are right; this is what participants received.
- **Status.** A fact of the trial; nothing to correct.
- **Next step.** Say so wherever a steps "data" comparison is shown.
- **Detail.** [06, Thousands-comma faults](../1.%20Preprocessing%20and%20model/LLM%20slop/06-decisions-and-probabilities.md#thousands-comma-faults-steps-statistics);
  [09, The thousands-comma faults](../1.%20Preprocessing%20and%20model/LLM%20slop/09-moderators.md#the-thousands-comma-faults).

### P13. 2024 decisions are partly inferred, and reach is retrospective

- **What.**
  - 2024 no-send days are inferred from the logs; job outages cannot be ruled out. The 2024 server code is not
    available.
  - The 2024 message-type probability file is a staged candidate, not in the shared folder. The presentation's 2024
    "data" comparison reads it through the engine's local paths file, and its fingerprint was not checked.
  - In both cohorts, whether a message could have reached someone is judged after the fact, and the assignment-based
    sensitivity analysis has not been run (Drew rated it a low-priority extra on 2026-11-16).
- **Affects.** 2024 reference (no-send) rows; the 2024 "data" comparison; the delivered-send estimand in both cohorts.
- **Could change numbers?** Possibly for the 2024 "data" comparison; Reading for the rest.
- **Status.** Open.
- **Next step.** Put the 2024 message-type file in the shared folder with its fingerprint.
- **Detail.** [06, Open and unverified items](../1.%20Preprocessing%20and%20model/LLM%20slop/06-decisions-and-probabilities.md#open-and-unverified-items);
  [10, Unverified](../1.%20Preprocessing%20and%20model/LLM%20slop/10-analysis-rules.md#unverified).

## Moderators

### P14. Not every moderator is measured before the decision

- **What.** The vault's screen and joint-model notes say every moderator is measured before the decision. The code
  disagrees for these:

  | Moderator | What comes after the decision |
  |---|---|
  | Day's high, warmth against own usual, rain, snow, precipitation | The decision date's afternoon and evening and the whole next date. Weather cannot be changed by a message |
  | Device | Chosen from observed hours over the whole year |
  | Sleep midpoint against own usual | Usual midpoint over the whole file |
  | Circadian caps | 99th percentiles over all participant-days |
  | HRV device type and its centring | Chosen and averaged over the whole file |
  | HRV, decisions not at 3 pm | The 24-hour bucket assumes a 3 pm decision; about 1% of decisions are at another time |
  | 2024 statistic tiers | Read at 20:00 UTC, up to an hour after a 3 pm local decision in Eastern daylight time |
  | Daytime sleep signs | The previous decision's 24-hour window can overrun the current decision when sends are under 24 hours apart |

- **Affects.** Reading moderator effects as conditions in place before the message.
- **Could change numbers?** Reading, except the 2024 tiers and the HRV bucket, where a strict cut-off could move a few
  decisions between levels.
- **Status.** Open.
- **Next step.** Correct the notes' wording. For the person-level descriptors, either call them whole-year descriptors or
  rebuild them from the period before each decision.
- **Detail.** [09, Measured at or after the decision](../1.%20Preprocessing%20and%20model/LLM%20slop/09-moderators.md#measured-at-or-after-the-decision);
  [09, Code against notes](../1.%20Preprocessing%20and%20model/LLM%20slop/09-moderators.md#code-against-notes), item 1.

### P15. The report and the presentation split moderators differently

- **What.**
  - **Median.** The report splits a continuous moderator at the median per cohort, comparison and compared arm. The
    presentation splits per cohort, period and outcome, over all decisions with the outcome and before any comparison's
    filters; its own docstrings say otherwise.
  - **"Usual."** The previous-week and person families use the mean of all earlier days (at least seven). The "against
    own usual" moderators for last night's sleep, mood and steps use the report's own past mean (at least three values,
    including the current day-before value).
  - **Figure 2 against figure 1b.** Figure 2's "alone" fits keep unrecorded decisions in their own group and apply no
    `MIN_HALF`, so they match figure 1b closely, not exactly.
  - **Tier cut points.** `tier_feats.py` takes the 2024 cut points from the 2025 server's message list, where
    `tier_effects.py` uses the 2024 list. They agree only if the two lists agree, which is asserted, not checked.
- **Affects.** The same moderator can give different levels in the report and the presentation.
- **Could change numbers?** Yes, between the two documents; each is consistent within itself.
- **Status.** Open.
- **Next step.** Pick one splitting rule for both documents, and compare the two message lists' cut points.
- **Detail.** [09, Code against notes](../1.%20Preprocessing%20and%20model/LLM%20slop/09-moderators.md#code-against-notes);
  [10, Where code and documentation disagree](../1.%20Preprocessing%20and%20model/LLM%20slop/10-analysis-rules.md#where-code-and-documentation-disagree), item 4.

### P16. Inputs used as supplied

- **What.** Several inputs are read as they came, without a check of how they were made:
  - The circadian files: how they define a date and their two-day fitting window.
  - Gridded weather: whether a day is labelled by the morning that ends it, which would shift values by a day.
  - The app weather feed: forecast or observation, and its precipitation units (the 0.05 threshold depends on them).
  - Garmin's `CALENDARDATE` for HRV: assumed to be the night ending that morning.
  - The 2024 participant-update timestamps: assumed to be UTC.
  - Baseline neuroticism: possibly missing for all of 2025.
- **Affects.** Circadian, weather and HRV moderators; 2024 tiers; baseline controls.
- **Could change numbers?** Possibly.
- **Status.** Unverified.
- **Next step.** Ask whoever made the circadian files for a description; check the weather day label against one
  station.
- **Detail.** [09, Unverified](../1.%20Preprocessing%20and%20model/LLM%20slop/09-moderators.md#unverified);
  [09, Circadian misalignment](../1.%20Preprocessing%20and%20model/LLM%20slop/09-moderators.md#circadian-misalignment).

## Pipeline and reproducibility

### P17. The presentation cannot be rebuilt from the repository

- **What.**
  - The presentation's pipeline (five scripts and `build_data.py`) is in the vault.
  - Three audit caches it reads (the moderator screen, daytime sleep, tiers) are in the audit area.
  - Four scripts (the two tier builders and the two that make figure 1's tables) are in a temporary session folder that
    can be cleared.
  - All of them name fixed locations on one machine.
  - The daytime-sleep caches are not rebuilt when the study files change. The moderator cache is checked for row
    alignment, not content.
  - Whether figure 1's source tables match a run of the current scripts is unverified.
- **Affects.** Whether anyone else can rebuild the presentation, and whether its numbers follow data changes.
- **Could change numbers?** Rebuild; possibly for figure 1 and the daytime-sleep rows.
- **Status.** Open; part of the reorganisation.
- **Next step.** Move the four scripts into the repository first, since they can be lost. Then the pipeline, with its
  locations in one config file like the report's `config/inputs.yaml`.
- **Detail.** [09, Built outside the repository](../1.%20Preprocessing%20and%20model/LLM%20slop/09-moderators.md#built-outside-the-repository);
  [10, Unverified](../1.%20Preprocessing%20and%20model/LLM%20slop/10-analysis-rules.md#unverified).

### P18. The presentation's tables skip the report's privacy guard

- **What.** The report refuses any results table with an identifying column, more than 2,000 rows, or a count from 1 to
  9 (`report/ihs_report/guard.py`). The presentation pipeline only asserts that three identifier names are absent. Its
  count columns are not checked against a minimum cell size, and its participant-level moderator cache is written
  outside the repository.
- **Affects.** The tables behind the presentation page.
- **Could change numbers?** No; this is a safeguard on what gets shared.
- **Status.** Open.
- **Next step.** Pass the presentation's tables through `guard.py` (naming count columns `n_...`) before the page is
  shared further.
- **Detail.** [10, The aggregate-only guard](../1.%20Preprocessing%20and%20model/LLM%20slop/10-analysis-rules.md#the-aggregate-only-guard).

### P19. One-cohort rows labelled "pooled" in the presentation

- **What.** Figures 1b and 2 pool the cohorts that have a finite, positive standard error. With only one, the "pooled"
  row is that cohort's estimate. Circadian and HRV measures exist for 2024 only, so their "pooled" rows are 2024 rows.
  The report shows a pooled row only when every cohort has the comparison.
- **Affects.** Labels in figures 1b and 2.
- **Could change numbers?** Reading.
- **Status.** Open.
- **Next step.** Label such rows "2024 only", or leave them out of pooled panels.
- **Detail.** [10, Pooling the cohorts](../1.%20Preprocessing%20and%20model/LLM%20slop/10-analysis-rules.md#pooling-the-cohorts).

### P20. Stored results and uncommitted engine code

- **What.** The engine's step-record rule (`window-stats-v5`) and its 0.2.2 estimator fix are in the working tree,
  not committed. The results store is keyed on the input files and the outcome-rule version, not on the package or
  estimator version. A run stored with the new key but before the estimator fix would therefore not be redone; whether
  any exists is unverified. The date of the step-rule change is unverified too (2026-11-20 by Claude's notes).
- **Affects.** Whether a stored result was made with the current estimator.
- **Could change numbers?** Possibly, through stale stored results.
- **Status.** Open.
- **Next step.** Commit the engine, and add its version to the store key; that redoes anything older once.
- **Detail.** [11, Where code and documentation disagree](../1.%20Preprocessing%20and%20model/LLM%20slop/11-model.md#where-code-and-documentation-disagree),
  item 1; [07, Unverified](../1.%20Preprocessing%20and%20model/LLM%20slop/07-outcome-windows.md#unverified).

## Documentation

### P21. Documentation that lags the code

In each case the code is right and the document is out of date.

| Where | Says | The code |
|---|---|---|
| Engine design notes (`causal/docs/DESIGN.md` and the vault's design note) | A blank step cell in an observed hour is a real zero | Treats a blank cell as missing; a window needs at least one step record |
| Engine README, "Rules built in" | Steps need at least 10 observed hours | Also needs a step record |
| Engine design notes | 2024 anchors "at the decision hour" | Anchors at the logged send or assigned time (`hour_utc`) |
| Engine design notes | The cohorts are "never pooled" | True of the engine; the report and the presentation pool |
| Engine README and design notes | Floor 0.001, 200 per arm | These are engine defaults; the report and presentation use 0.001 (2024), 0.01 (2025) and 50 per arm |
| Report README, "What is in the report" | Levels need 200 sends | 50 since 2026-11-24 |
| Report README, on collinearity | Collinearity is unlikely | True for the engine's five controls; the standard set's flags and added moderators can be collinear in a subset, which the engine handles since 0.2.2 |
| Report README, on the engine's stored results | The store is keyed on the input files | The key also includes the outcome-rule version, so older runs are flagged and can be redone |
| `report/ihs_report/build/history.py` | The own past mean is filled with the cohort mean | Filled with the mean of the defined own-mean values (a mean of running means) |
| `report/ihs_report/pooling.py` | The inverse-variance average "equals" one stacked model | Only approximately, with sandwich variances |
| `<scratch>/usual_set_temperature.py` | "the report uses 200" | 50 |
| Presentation `screen_fit.py`, `joint_fit.py` | Median among the analysed decisions | Median over all decisions with the outcome (P15) |
| Vault screen and joint-model notes | Every moderator is measured before the decision | See P14 |

- **Could change numbers?** Docs.
- **Next step.** Update these in one pass when the engine is committed (P20).
- **Detail.** [07](../1.%20Preprocessing%20and%20model/LLM%20slop/07-outcome-windows.md#where-code-and-documentation-disagree),
  [08](../1.%20Preprocessing%20and%20model/LLM%20slop/08-controls.md#where-code-and-documentation-disagree),
  [10](../1.%20Preprocessing%20and%20model/LLM%20slop/10-analysis-rules.md#where-code-and-documentation-disagree),
  [11](../1.%20Preprocessing%20and%20model/LLM%20slop/11-model.md#where-code-and-documentation-disagree), each under
  "Where code and documentation disagree".

## Other unconfirmed facts

### P22. Other unconfirmed facts

- **A stale fingerprint.** The vault's version register gives the 2024 decision file as `f294d670…`; the current file is
  `c5adc147…`, and every other record calls `f294d670…` the previous file. Fix the register.
- **The size of the 2025 Random control group.** 213 participants plus warm-up months (engine design note) against 90
  people all year (audit board, 2026-11-22). The definitions likely differ.
- **How the 2025 week's domain was assigned.** The docs say "randomized by week"; the mirrored `BuildSchedule.py`
  rotates domains weekly from a randomly assigned permanent group. Engine comparisons are unaffected because they stay
  within a domain's weeks, but the design description should match the code.
- **Whether recording an outcome depends on the message,** in each cohort. It matters for the estimand.
- **Whether `PHQtot0` uses the same item coding in both cohorts.**
- **Whether the presentation applies any multiplicity adjustment.**
- **Whether the Dropbox copies match the local files' fingerprints.**
- **The 2025 mood count.** 89,253 source reports against 89,252 scored responses; probably the single zero score,
  which cannot be told apart from "no response".
- **Two smaller items not re-checked on the rebuilt files:** a smart scale's readings in phone-class resting heart rate,
  and Apple Watch resting heart rate days above 120 bpm.
- **The engine's simultaneous critical value** divides influence sums without the $G/(G-1)$ factor by standard errors
  with it, so the value is smaller by about $\sqrt{(G-1)/G}$. Negligible with hundreds of participants.

- **Could change numbers?** Mostly no.
- **Detail.** [06, Source conflicts and how they were resolved](../1.%20Preprocessing%20and%20model/LLM%20slop/06-decisions-and-probabilities.md#source-conflicts-and-how-they-were-resolved);
  [01, Unverified items](../1.%20Preprocessing%20and%20model/LLM%20slop/01-raw-sources.md#unverified-items);
  [04, Items still open](../1.%20Preprocessing%20and%20model/LLM%20slop/04-audit-corrections.md#items-still-open);
  [08, Unverified](../1.%20Preprocessing%20and%20model/LLM%20slop/08-controls.md#unverified);
  [10, Unverified](../1.%20Preprocessing%20and%20model/LLM%20slop/10-analysis-rules.md#unverified);
  [11, Unverified](../1.%20Preprocessing%20and%20model/LLM%20slop/11-model.md#unverified).
