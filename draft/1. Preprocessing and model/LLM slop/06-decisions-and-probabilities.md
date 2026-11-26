# 06. Decisions, arms and randomization probabilities

**Summary.** This note covers, separately for the 2024 and 2025 cohorts, how a daily decision was made, which arms
existed, how a message was drawn from the shared pool, how the published decision tables were built, which
decisions the analysis keeps, and what each published probability means. In 2024 a fixed policy sent a message with
probability 0.5 and drew the message uniformly from the participant's remaining cores; the 2024 table was rebuilt on
November 16, 2026 from the full-year notification log, including a server numbering bug that removed some sleep
messages from the pool. In 2025, Thompson-sampling agents chose among no message and nine message types inside a
weekly domain; the released probabilities are posterior-averaged (and, by default in the engine, averaged over agent
selection), not the single-draw vector logged at the decision, and the fitted decisions of September 4-27, 2025 have
their probabilities withheld. Both cohorts keep only delivered sends and retrospectively reachable no-send days for the
main analysis, and the last section shows how the `ihs_causal` engine turns these files into comparisons.

## Contents

- [Conventions and sources](#conventions-and-sources)
- [Trial design as it bears on the data](#trial-design-as-it-bears-on-the-data)
  - [Arms, strategies and domains (both cohorts)](#arms-strategies-and-domains-both-cohorts)
  - [2024 design](#2024-design)
  - [2025 design](#2025-design)
  - [How a message was chosen from the pool](#how-a-message-was-chosen-from-the-pool)
- [Decision tables: 2024](#decision-tables-2024)
- [Decision tables: 2025](#decision-tables-2025)
- [Randomization probabilities: 2024](#randomization-probabilities-2024)
- [Randomization probabilities: 2025](#randomization-probabilities-2025)
- [Clipping, floors and renormalization](#clipping-floors-and-renormalization)
- [Message coding](#message-coding)
- [How the engine reads decisions and probabilities](#how-the-engine-reads-decisions-and-probabilities)
- [Source conflicts and how they were resolved](#source-conflicts-and-how-they-were-resolved)
- [Open and unverified items](#open-and-unverified-items)
- [Facts other notes should carry](#facts-other-notes-should-carry)

## Conventions and sources

Status labels, used on every rule:

| Label | Meaning |
|---|---|
| **Applied** | In the published files and the engine that current results use |
| **Staged, not applied** | A built candidate exists but the published files and engine do not use it |
| **Proposed** | Written down as a plan; nothing built or adopted |
| **Withheld** | Deliberately blanked or held out of the published files |
| **Superseded** | Was applied or proposed earlier; replaced by a later rule |

Source abbreviations used in `[src: ...]`:

| Abbreviation | What it is |
|---|---|
| `<shared>` | The shared study folder (data root). Its `README.md` is cited by section title. |
| `<vault>` | The project's Obsidian notes ("Jack IHS Moderator Analysis"). `<board>` = `<vault>/Audit Message Board.md`, cited by post date and time. |
| `causal/...` | The `ihs_causal` engine in this repository (being moved to the repository root). |
| `<server>` | A local read-only mirror of the 2025 server's `agents/` code, copied June 19-21, 2026. Not in this repository; it may differ from the code that ran on a given 2025 date. |
| `<memory>` | Dated working notes kept by the assistant across sessions; used only as background and checked against records where possible. |

Counts come from READMEs, manifests, validation JSON and notes; no study data file was opened for this note. Counts of
fewer than 10 people are written as "fewer than 10". Effect estimates are deliberately left out.

Sibling notes: [01 raw sources](01-raw-sources.md), [02 hourly files](02-hourly-files.md),
[03 clocks and time zones](03-clocks-and-time-zones.md), [04 audit corrections](04-audit-corrections.md),
[05 mood timing](05-mood-timing.md), [07 outcome windows](07-outcome-windows.md), [08 controls](08-controls.md),
[09 moderators](09-moderators.md), [10 analysis rules](10-analysis-rules.md), [11 model](11-model.md).

## Trial design as it bears on the data

### Arms, strategies and domains (both cohorts)

Both cohorts use the same ten-action vocabulary: no message, or one of nine message types formed by a therapeutic
strategy and whether the message is from the pool designed to show the participant's own data. There is no Distanced
Self-Talk data type. [src: `<server>/agents/config.py` `ARM_LABELS`, `ARM_MAP`; `<vault>/Data Preprocessing/03 Behavior Probability Data Design.md` § "IHS 2025 action vocabulary"]

| 2025 `action_id` | Label | Strategy | Pool |
|---:|---|---|---|
| 0 | NoSend | none | none |
| 1 | CSNoData | Cognitive Strategies (CS) | no data |
| 2 | CSData | Cognitive Strategies | own data |
| 3 | BSNoData | Behavioral Strategies (BS) | no data |
| 4 | BSData | Behavioral Strategies | own data |
| 5 | MINoData | Motivational Interviewing (MI) | no data |
| 6 | MIData | Motivational Interviewing | own data |
| 7 | MfnData | Mindfulness (Mfn) | own data |
| 8 | MfnNoData | Mindfulness | no data |
| 9 | DSTNoData | Distanced Self-Talk (DST) | no data |

- Note the order of 7 and 8: Mindfulness puts Data before NoData, unlike the other strategies. An older 2024 helper
  also reversed the two Mindfulness IDs relative to 2025. Always join and compare on labels, not numeric IDs. The engine
  does. [src: `<server>/agents/config.py` `ARM_LABELS`; `<vault>/Data Preprocessing/05 Non-Corral Probability Export Report.md` § "2024: binary fields retained"; `causal/src/ihs_causal/data/decisions.py` `ARMS`]
- In the 2024 files `action_id` is binary (0 = no send, 1 = send); the category lives in `action_category_label`,
  `strategy` and `personalization`. [src: `<shared>/ProbabilityVariableDictionary.csv` rows `action_id`, `action_category_label`]
- Domains are mood, steps and sleep. In 2024 the domain is a property of the message drawn; in 2025 it is fixed for the
  participant's week by the schedule, and the agent then chooses within it. [src: `<shared>/README.md` § "Actual message domain and domain probabilities"; `<server>/agents/BuildSchedule.py`]
- Strategy and data display are one joint action, not two independent randomizations, in both cohorts. [src: `<vault>/Data Preprocessing/03 Behavior Probability Data Design.md` § "IHS 2025 action vocabulary"; `<shared>/README.md` § "November 11, 2026 — all probability scopes in one CSV"]

### 2024 design

| Element | 2024 | Status | Source |
|---|---|---|---|
| Study year | July 1, 2024 to June 30, 2025 | **Applied** | `<shared>/README.md` § "Update, November 16, 2026 — 2024 decision table rebuilt..." |
| Decision unit | One opportunity per participant per UTC day; the UTC date is the decision day (Drew, November 16, 2026) | **Applied** | `<vault>/Audit Decision Summary 2026-11-14.md` § "2024 decision file rebuilt from the notification log — Fable, November 16" |
| Send probability | 0.5 every study-year day for everyone (Drew's statement of the design; the original 2024 server code is not available, only the notification log) | **Applied** | `<memory>/project-ihs-2024-design-facts.md` (2026-11-16); `<shared>/ProbabilityVariableDictionary.csv` row `p_send` |
| Agents | None. `selected_agent` is blank throughout 2024 | fact | `<shared>/ProbabilityVariableDictionary.csv` row `selected_agent` |
| Message choice | Uniform over the participant's remaining eligible cores across all domains, not "domain first" (inferred from the log; see below) | **Applied** (as the inferred model) | `<vault>/2024 Message Selection Bug and Decision Table.md` § "Other rules the log settles" |
| Send time | Drew recalls 3 pm in the server's time zone; no-send hours are imputed from neighbouring sends. Details in [03](03-clocks-and-time-zones.md) | unverified against server code | `<memory>/project-ihs-2024-design-facts.md`; `<vault>/2024 Message Selection Bug and Decision Table.md` § "Known limits" |
| Pre-internship series | `Preinternship-2` to `Preinternship-19`, one every four days from April 19 to June 26, 2024, texts unrelated to the core pool. Kept as 44,111 baseline rows with blank probabilities; not part of randomized analyses | **Applied** (excluded from analysis) | `<vault>/2024 Message Selection Bug and Decision Table.md` § "The bug"; `<vault>/Data Preprocessing/20 Rebuilt 2024 Decisions and Timezone Probe.md` |

### 2025 design

**Policy periods.** The 2025 policy ran in three regimes. [src: `<board>` posts 2026-11-17 00:34 and 00:51 (Fable, with Drew's statement); `<memory>/project-ihs-2024-design-facts.md` (2026-11-17)]

| Period | What decided | Note |
|---|---|---|
| July 2-24, 2025 | Warm-up: every decision by the Random policy | Intended (Drew, November 17, 2026) |
| July 25 to October 28, 2025 | Nine fitted agents per domain, chosen evenly (1/9). Their models held the prior plus the warm-up decisions and were not retrained on later decisions | From server logs; Drew's statement covers the warm-up and the joint start |
| From October 29-31, 2025 | Weekly retraining on all accumulated decisions (steps Wednesday, sleep Thursday, mood Friday) and Corral agent selection, visible from October 30 | Training sets jumped about 4.5-fold in one update |

Decisions start June 30, 2025; study windows start July 1, 2025 and the study year ends June 30, 2026.
[src: `<vault>/Data Preprocessing/22 Validated 2025 Message Matches and Window Timing.md`; `<shared>/README.md` § "November 16, 2026 — 2025 decisions extended through June 30, 2026"]

**Weekly schedule.** A weekly `AgentSchedule.csv` gives each participant one agent tag per day. In the mirrored
`BuildSchedule.py`, every participant gets a permanent group (0, 1 or 2) by a shuffled round-robin when first seen, and
the week's domain is `(group + week number) mod 3` over Steps, Sleep, Mood, so domains rotate weekly with a randomly
assigned phase and a third of participants are in each domain each week. Participants not on the training list get
the fixed tag `<Domain>Random` (the control group); the others get one fitted agent per day, drawn when the schedule is
built from the latest Corral weights for that domain. [src: `<server>/agents/BuildSchedule.py` (lines 37-131)] The
historical versions of this script are not verified; one line in the mirror is set "for FIRST WEEK" so that everyone is
a control, which matches the warm-up but not later weeks. [src: `<server>/agents/BuildSchedule.py` line 45; `<vault>/Data Preprocessing/03 Behavior Probability Data Design.md` § "Source code and numerical audit boundary"] Status: description of what ran; the domain-rotation detail is **unverified** against historical code (see [conflicts](#source-conflicts-and-how-they-were-resolved)).

**Agents.** There are 27 fitted agents (`MoodAgent1`-`9`, `SleepAgent1`-`9`, `StepsAgent1`-`9`) and three Random
agents (`MoodRandom`, `SleepRandom`, `StepsRandom`). Agent numbers identify models with different priors and ridge
settings, not strategies. [src: `<server>/agents/config.py` `DOMAINS`, `AGENT_NUMBERS`, `RANDOM_AGENT_SUFFIX`; `<shared>/ProbabilityVariableDictionary.csv` row `selected_agent`; `<board>` 2026-11-17 00:22] Each fitted agent is a Thompson sampler (`LightManager`): it draws one parameter vector from its posterior, scores the nine send types, turns the scores into the ten-action "behaviour" probability vector, and samples the action from it. The file name "BehaviorAgentProbabilities" refers to this behaviour policy. [src: `<server>/agents/LightManager.py` `decide`, `_bounded_send_probs`]

**How a fitted agent's probabilities are formed** (mirrored code): a softmax over the nine send-type scores gives the
split among types, and a bounded logistic of the mean score gives the total send probability, held between 1/7 and 6/7.
There is no floor on individual message types. [src: `<server>/agents/LightManager.py` `_bounded_send_probs`, `behaviour_prob_mc_fast`, `p_send_bounds=(1/7, 6/7)`]

**Random policy.** No message with probability 0.5 and each of the nine types with 1/18. A decision gets the Random
label in two ways: a scheduled `<Domain>Random` slot (control group or warm-up), or a fallback inside
`MakeDecisions.py` when the participant has no context row that day, the agent tag is malformed, the model file is
missing, or the Thompson step fails. Fallback rows are written with the same Random vector and label, so the published
Random probabilities are conditional on the recorded Random branch; the probability of entering a fallback is not
reconstructed. [src: `<server>/agents/config.py` `BASELINE_PROB_10`; `<server>/agents/MakeDecisions.py` main loop; `<shared>/CorralProbabilities20261104/README.md` § "Quality and interpretation"] Known fallbacks: fewer than 10 of the 2,312 recorded Random decisions on June 20-30, 2026 were scheduled as fitted; 1,605 recorded `StepsRandom` decisions over the year came from fitted plans. [src: `<vault>/Data Preprocessing/24 Fable Review - Probability Scopes and Garmin Sleep.md`; `<vault>/Results and Document Compilation/Activity Deep Dive/Evidence/2025 Scheduled Random Steps Lottery.md` § "Schedule and assignment verification"] The size of the fixed control group is stated differently in two places (213 participants plus each participant's warm-up month in the engine design note of November 17; 90 people on Random all year in a November 22 board post); **unverified**. [src: `<vault>/Causal Analysis Engine/ihs-causal Design.md`; `<board>` 2026-11-22] In the main analysis set, 47,491 decisions were under the Random policy: 78% of July 2025, 8-11% of most later months, 20% of March 2026. [src: `<board>` 2026-11-16 23:46]

**Agent selection (Corral).** Weights over the nine agents in a domain were uniform (1/9) through October 29, 2025 and
log-mapped, schedule-specific weights from October 30, 2025 (logged each Monday; rounded to six decimals). From
November, weight concentrated on one agent per domain (sleep agent 3, steps agent 1, mood agent 2).
[src: `<shared>/CorralProbabilities20261104/README.md` § "Effective Corral cutoff"; `<shared>/README.md` § "November 11, 2026 — all probability scopes in one CSV"; `<board>` 2026-11-17 00:22 and 00:34]

**Decision time and context.** The daily decision run (`MakeDecisions.py`) writes the day's Decisions file at about
14:50-14:57 New York time (18:50 UTC in summer; the directions note gives 18:50 UTC daily), about four minutes before
the first notification; sends then go out mostly at 19:00 or 20:00 UTC (3 pm Eastern). The context is the participant's last row of that UTC day in the
standardized daily events table (built at 18:00 UTC). The `hour_utc` in the probability file is a date label, not the
decision time. Clock details are in [03](03-clocks-and-time-zones.md); the window anchor is in [07](07-outcome-windows.md).
[src: `<vault>/Directions for Codex - 2025 Probability Archive Fix.md` § "1.1"; `<memory>/project-ihs-2025-window-anchor-and-delivery.md` (2026-11-16); `<server>/agents/MakeDecisions.py` context lookup; `<vault>/Data Preprocessing/22 Validated 2025 Message Matches and Window Timing.md` § "Timing and boundary rules"]

### How a message was chosen from the pool

| Step | 2024 | 2025 |
|---|---|---|
| Send or not | 0.5 | Agent's or Random vector |
| Which pool | All remaining eligible cores, any domain or strategy | The scheduled domain and the chosen type (one of 27 domain-by-type pools) |
| Which core | Uniform over eligible cores: the 358 cores minus cores already successfully delivered before that UTC day, minus core N-1 for each delivered `Preinternship-N` (bug below). Failed sends do not use up a core | Uniform over the participant's least-used cores in that pool (rotation); the history count rises on assignment |
| Which wording | One of four variants per core, fixed by the tier of the message's statistic (see [Message coding](#message-coding)) | Same, with slightly different tier boundaries; an unreadable statistic gives the neutral variant |
| Evidence | Inferred from the notification log (server code unavailable); replayed with zero discrepancies | Mirrored `DailyDecisionsToMessages.py`; a replay matched all 191,381 logged variants |

[src: `<vault>/2024 Message Selection Bug and Decision Table.md`; `<shared>/ProbabilityVariableDictionary.csv` row `p_CSNoData` processing; `<server>/agents/DailyDecisionsToMessages.py` lines 93-162; `<vault>/Results and Document Compilation/Activity Deep Dive/Activity critique.md` (Codex, line 23); `<vault>/Results and Document Compilation/Activity Deep Dive/Activity Messages and the Data Fallback.md`]

Consequences:

- 2024 domain, strategy and data probabilities are not uniform: they follow the counts of remaining cores. 2025 core
  choice is not part of any published probability; the published 2025 probabilities stop at the type level.
  [src: `<shared>/README.md` § "Probability interpretation"; `<shared>/README.md` § "Shared IHS message pool"]
- Wording variants are not independently randomized in either cohort. [src: `<vault>/Results and Document Compilation/Activity Deep Dive/Activity critique.md` line 23]

## Decision tables: 2024

### Files (current)

| File in `<shared>` | Rows x columns | One row per | Status |
|---|---|---|---|
| `2024BehaviorAgentProbabilities.csv` | 362,808 x 51 | 44,111 preserved baseline rows plus one row per participant per **reachable** study-year UTC day (318,697 rows, 917 participants) | **Applied** (engine input) |
| `2024DecisionHistoryComplete.csv` | 343,100 x 54 | Every linked participant (940) x every study-year UTC day (365), including undelivered sends and unreachable days; adds `delivered`, `n_attempts`, `reach` | **Applied** as companion (not read by the engine) |
| `audit/CollaborativeAudit/Opus/Decisions2024/candidate/2024MessageTypeProbabilities.csv.gz` | not stated | Domain-by-type probabilities per decision (`p_<domain>_<arm>`) | **Staged, not applied** in the shared root; read by the engine only where `config/paths.yaml` points to it (see [engine](#how-the-engine-reads-decisions-and-probabilities)) |

SHA-256: main `c5adc147f636...`, history `01babcbe6eba...`; previous main file `f294d6700945...` (backed up).
[src: `<shared>/ProbabilitySourceManifest.json`; `<shared>/ProbabilityExportValidation.json`; `<shared>/README.md` § "Update, November 16, 2026 — 2024 decision table rebuilt..."; `<vault>/Causal Analysis Engine/ihs-causal Design.md` § "Message-type probabilities"]

### How the 2024 table was built (November 16, 2026)

- **Source.** The full-year notification log (186,166 rows, April 19, 2024 to July 1, 2025; 173,868 internship
  attempts) and the 358-core catalogue. The 2024 server code is not available; rules were inferred from the log.
  **Applied.** [src: `<shared>/README.md` § "Update, November 16, 2026..."; `<vault>/2024 Message Selection Bug and Decision Table.md` § "How sure is this"]
- **Completed day grid.** Every linked participant gets a decision every UTC day of the study year. A day with a
  logged internship attempt is a send (`action_id` 1); a day without one is an inferred no-send (`action_id` 0). Attempts
  fall on 49.7% of account-days; 13 accounts have gaps of 15-30 days, so a few no-send days are probably days the job did
  not run. All raw dates have at most one internship attempt per participant-day in the linked study-year population.
  **Applied** (no-sends are an assumption, not logged randomizations). [src: `<vault>/2024 Message Selection Bug and Decision Table.md` § "The decision file", "Known limits"; `<vault>/Data Preprocessing/20 Rebuilt 2024 Decisions and Timezone Probe.md` § "What was checked"]
- **Times.** Sends keep the attempt timestamp (`time_source = attempt`); no-send hours are imputed from neighbouring
  attempts with a nearest-hour and one-hour DST heuristic (`time_source = imputed`). `time_uncertain = 1` flags 5,116
  ambiguous hours in the history and 5,099 in the main file; other imputed hours are still inferred. `hour_utc` floors
  `recorded_time_utc`. See [03](03-clocks-and-time-zones.md). **Applied.** [src: `<shared>/ProbabilityVariableDictionary.csv` rows `hour_utc`, `time_source`, `time_uncertain`; `<shared>/ProbabilityExportValidation.json`]
- **Pool and probabilities.** See [Randomization probabilities: 2024](#randomization-probabilities-2024). `pool_size`
  = 358 minus baseline-blocked and previously successfully delivered distinct cores. **Applied.** [src: `<shared>/ProbabilityVariableDictionary.csv` row `pool_size`]
- **Independent review.** Codex replayed all 343,100 history rows from the raw log and catalogue: zero discrepancies
  in all 27 conditional probability columns, pool sizes, send and delivery flags, notification identities and times,
  reach labels and imputed hours; sum identities hold to 2.2e-16. This verifies the implementation of the inferred
  model, not that every absent notification was a randomized no-send. [src: `<vault>/Data Preprocessing/20 Rebuilt 2024 Decisions and Timezone Probe.md` § "What was checked"; `<shared>/ProbabilityExportValidation.json` `checks`]
- **Reproduction limit.** The construction scripts (`s03`-`s05`) document a staged workflow and must not be rerun
  against the current 51-column file; the older `build_probability_exports.py` does not reproduce the current release.
  [src: `<shared>/ProbabilitySourceManifest.json` `reproduction_limit`]

### The 2024 message selection bug

A participant who had been delivered `Preinternship-N` was never afterwards sent core N-1. The likely cause is a
row-number collision: the server's "already sent" list did not distinguish the pre-internship list from the core list.
Cores 1-18 are all sleep messages, so the bug lowers the sleep share. [src: `<vault>/2024 Message Selection Bug and Decision Table.md` § "The bug"; `<vault>/Audit Decision Summary 2026-11-14.md` § "2024 decision file rebuilt..."]

| Test on the raw log | Result |
|---|---|
| Draws of a blocked core | 0, against about 7,400 expected without the rule |
| Pairs with a delivered `Preinternship-N` | 10,629; core N-1 drawn afterwards in none |
| Same test with offset 0 or 2 | 1,140 and 648 pairs drawn, so only N-1 fits |
| Domain shares predicted with the rule | 37.2% mood, 34.0% steps, 28.7% sleep; observed 37.2%, 34.0%, 28.8% |
| Domain fit without the rule | chi-square 729 on 2 df, against 0.3 with it |
| A failed send uses up its core? | No: failed cores redrawn 2,813 times, 2,720 expected if failures do not count |
| A failed baseline delivery blocks its core? | No |

[src: `<vault>/2024 Message Selection Bug and Decision Table.md` § "How sure is this", "Other rules the log settles"]

Effect on probabilities (previously published rows): mean `p_mood` 0.359 to 0.372, `p_steps` 0.328 to 0.340, `p_sleep`
0.313 to 0.287 (typically 9% lower for sleep, up to 15%). `p_send` is unaffected. **Applied** (rebuilt file).
[src: `<vault>/2024 Message Selection Bug and Decision Table.md` § "Effect on the probabilities"]

### Exclusions and accounts (2024)

| Rule | Count | Status | Source |
|---|---|---|---|
| Accounts whose `STUDY_PARTICIPANT_ID` is the literal `NA` in the 2024 roster are left out | 56 such IDs in the roster; 18 appear in the decision data; 958 accounts in the log leave 940 linked participants | **Applied** | `<shared>/README.md` § "Accounts excluded from the current analysis"; `<vault>/2024 Message Selection Bug and Decision Table.md` § "Known limits" |
| Baseline (pre-internship) rows kept in the main file but outside randomized analyses | 44,111 rows, probabilities blank | **Applied** | `<shared>/README.md` § "November 16, 2026 — current 2024 decisions independently reviewed" |
| Undelivered sends removed from the main file (kept in the history, `delivered = 0`); never recoded as no-send | 12,022 undelivered attempt-days of 169,847 (7.1%) | **Applied** | `<shared>/ProbabilityExportValidation.json` `history_2024`; `<shared>/README.md` § "Update, November 16, 2026..." |
| No-send days retrospectively unreachable or unclear removed from the main file | reach: 318,697 reachable, 24,231 unreachable, 172 unclear (history; unreachable includes the undelivered send days) | **Applied** | `<shared>/ProbabilityExportValidation.json` `history_2024.reach` |
| One repeated delivery of an already-delivered core (the only repeat in 160,559 deliveries; fewer than 10 participants). Kept and flagged; under strict depletion its core-level probability is zero, so drop it from any analysis that divides by a core-level probability; type, strategy and domain analyses need no exclusion | 1 decision | **Applied** (kept) | `<shared>/README.md` § "Update, November 16, 2026..."; `<vault>/Data Preprocessing/20 Rebuilt 2024 Decisions and Timezone Probe.md` § "Qualifications" |
| Correction of that participant's pool (152 rows in each file, `pool_size` + 1, largest probability change 0.004), for the next rebuild | 152 rows | **Staged, not applied** | `<shared>/README.md` § "Update, November 16, 2026..."; `<vault>/Audit Decision Summary 2026-11-14.md` |

**Reach rule (2024).** An attempted day takes its delivery outcome. A no-send day takes the state of its previous and
next attempt days if they agree; at the start or end of a participant's record the one available neighbour is
extended; disagreement is "unclear". Failed sends come in runs consistent with an unregistered app or device; 108
participants have such a period, covering 7% of participant-days. Of 958 accounts, 843 never fail, 27 never deliver, 80
deliver then fail for good, and fewer than 10 fail first then deliver or switch back and forth; only 70 of 13,168 failed
days fall between two deliveries. Drew approved "reachable days only" on November 16, 2026. **Applied.** This is a
retrospective classification that uses later outcomes, not a measured pre-decision availability flag; Codex recommends
an assignment-based sensitivity analysis on the full history, which is **Proposed**. [src: `<vault>/Data Preprocessing/20 Rebuilt 2024 Decisions and Timezone Probe.md` § "Qualifications for analysis"; `<vault>/2024 Message Selection Bug and Decision Table.md` § "Why reachable days only"; `<vault>/Audit Decision Summary 2026-11-14.md`]

Resulting main study rows: 318,697 = 157,825 delivered sends (49.5%) + 160,872 inferred no-sends, 917 participants.
Compared with the previous file: 149,771 rows kept with the same send decision and message, 494 no-sends dropped as
unreachable or unclear, 168,926 added (January to June 2025 and missing July to December days); 2,444 retained no-send
rows changed hour (2,459 before the reach filter). [src: `<shared>/ProbabilityExportValidation.json` `current_2024`; `<vault>/Data Preprocessing/20 Rebuilt 2024 Decisions and Timezone Probe.md` § "What was checked"]

### Superseded 2024 versions

| Version | What changed later | Status |
|---|---|---|
| September 17, 2026 export: 202,624 rows, 99,687 raw attempts plus 102,937 gap-filled "NoMessage" rows copied from an old event table; `p_send = 0.5` only July to December | Gap-filled no-sends replaced by a completed UTC-day grid | **Superseded** |
| September 30 to November 11, 2026: 194,376 rows / 48 columns, failed and double attempts removed, category, domain and 15 domain-by-strategy probabilities with the rule "a core is removed after its first attempt, including failed attempts" | Failed attempts do not deplete; `Preinternship-N` blocks core N-1; full year added; reach rule | **Superseded** November 16, 2026 |
| The README's September 30 "Applied exclusions" table (date correction 59, double attempts 134, failed attempts 5,330, accounts 2,725 rows) | Only the account exclusion carries over; the others are replaced by the rebuild | **Superseded** except the account rule |

[src: `<vault>/Data Preprocessing/05 Non-Corral Probability Export Report.md`; `<shared>/README.md` §§ "Applied exclusions", "Probability interpretation", "Domain by strategy joint probabilities — November 11, 2026", "Update, November 16, 2026..."]

## Decision tables: 2025

### Files (current)

| File in `<shared>` | Rows x columns | One row per | Engine reads | Status |
|---|---|---|---|---|
| `2025BehaviorAgentProbabilities.csv` | 388,613 x 167 | Logged decision (participant x day), June 30, 2025 to June 30, 2026; 1,067 accounts | yes | **Applied** |
| `2025DecisionTiming.csv` | 388,613 x 39 | Same decisions: exact message linkage, delivery evidence, window anchor, reach and analysis flags | yes | **Applied** |
| `2025DecisionWindows.parquet` | 388,809 x 25 | Full window grid (decisions plus synthetic history and gap rows) with boundary masks and main flags | no | **Applied** as companion |
| `2025AllAgentProbabilities.csv` (and zip) | 3,599,455 x 23 | (decision, candidate agent): nine fitted candidates in the scheduled domain, plus the exact Random row where Random acted. Not additional decisions | no | **Applied** as companion |
| `audit/2025BehaviorAgentProbabilitiesAudit.csv` | not stated | Decision: source paths, timing semantics, separate Behavior scalar (`p_observed_action_separate_mc`) and comparison flags | no | audit |
| `audit/CollaborativeAudit/Codex/FableReview20261116/2025LoggedDrawProbabilityAudit.csv.gz` | 388,613 x 20 | Decision: the logged single-draw vector `p_0..p_9` (six significant figures) | no | audit only |
| `CorralProbabilities20261104/` | 376,940 rows | Corral mixture companion through June 19, 2026, with `_given_send` fields and weights by date; source of the `p_marginal_*` and `corral_w_*` columns, which the main file now carries through June 30 | no | companion, not extended to the June tail |

SHA-256 of the current root files: probabilities `539dfa1739bb...` (since November 19, 2026; `6704c3b2968a...` before),
all-agent `8a6009129d49...`, timing `825e04e45462...`, windows `59db581a8d5f...`.
[src: `<shared>/README.md` §§ "Which 2025 file should Jack use?", "November 16, 2026 — 2025 decisions extended...", "September 2025 fitted probabilities — November 19, 2026"; `<shared>/audit/2025SeptemberFittedProbabilityExclusion.json`; `<vault>/Data Preprocessing/07 Current Files and Version Register.md`; `<vault>/Data Preprocessing/24 Fable Review - Probability Scopes and Garmin Sleep.md`; `<shared>/CorralProbabilities20261104/README.md`]

### How the 2025 tables were built

- **Decision source.** The server's daily `Decisions/<date>Decisions.csv` (participant, date label, agent, action,
  `p_0..p_9`, `P_behavior`): 355 files for June 30, 2025 to June 19, 2026 (376,940 decisions), plus 11 files for June
  20-30, 2026 (11,673 decisions). All 355 reproduce the probability file's participant, timestamp, selected agent and
  action exactly. **Applied.** [src: `<vault>/Directions for Codex - 2025 Probability Archive Fix.md` § "3.1"; `<vault>/Data Preprocessing/22 Validated 2025 Message Matches and Window Timing.md` § "What was validated"]
- **Probability source.** The released `p_*` columns come from the server's all-agent archive
  (`Probabilities/<Domain>/MasterProbabilities.csv`, columns `P_<agent>_<arm>`), not from the Decisions file. Joins use
  participant plus source UTC date and require exact agreement of selected agent and action, because 12,810 decision
  and probability timestamps disagree. This confirms record identity, not that the archived model snapshot and context
  match the decision (`historical_model_alignment = record_identity_checked_snapshot_not_recomputed`). **Applied.**
  [src: `<vault>/Data Preprocessing/03 Behavior Probability Data Design.md` § "Source code and numerical audit boundary"; `<vault>/Directions for Codex - 2025 Probability Archive Fix.md` § "1.1", "1.6"]
- **Message linkage.** `DailyDecisionsToMessages.py` writes `<date>Messages.csv` with the core and notification
  identifier for each assigned send: 354 files (July 14, 2025 missing). All 191,900 Message-send records agree with the
  archived message list on notification ID, core, type and domain. Decisions are matched to the returned notification
  export (619,401 rows; 783 exact duplicate records removed on all four fields) by **exact notification ID,
  participant and UTC date**, never by nearest time. For the study period through June 19, 2026, 190,369 sent decisions
  match exactly; 146,393 of them have a successful attempt. A broad participant-day match would have given 146,587
  successes, 194 of them with the wrong recorded action. **Applied.** [src: `<vault>/Data Preprocessing/22 Validated 2025 Message Matches and Window Timing.md` §§ "What was validated", "Timing and boundary rules"]
- **Anchors.** Matched sends anchor at the floored hour of the logged attempt (median delay into the hour 192 s,
  maximum 1,334 s); no-sends take that UTC day's single observed send hour, flagged as imputed. `hour_utc` in the
  probability file stays the old date label; use `window_anchor_utc` from the timing file. Details in
  [03](03-clocks-and-time-zones.md) and [07](07-outcome-windows.md). **Applied.** [src: same, § "Timing and boundary rules"; `<shared>/README.md` § "November 16, 2026 — validated 2025 timing companions"]
- **No cohort exclusions.** No tester or account exclusions, action recoding, flooring or renormalization were
  applied to the 2025 probability files. Participants without hourly data stay in the decision files (1,067 accounts
  against 928 in the hourly file). **Applied.** [src: `<shared>/README.md` § "November 11, 2026 — all probability scopes in one CSV", § "Read these limitations before analysis"]

### Whole-day and row exclusions from source-record conflicts (2025)

Assignments and probabilities on these days are kept in the files; the analysis flags exclude them.

| Date | Evidence | Handling | Status |
|---|---|---|---|
| July 1, 2025 | Decisions file marks all 1,046 decisions NoSend; Messages has 526 sends; no internship attempts. The Decisions file was rewritten July 11 | Whole day out of analysis | **Applied** |
| July 14, 2025 | No Messages file for 1,065 decisions (554 marked sent) | Whole day out; imputed boundary only | **Applied** |
| November 13, 2025 | 753 of 1,060 actions differ between Decisions and Messages (267 send to NoSend, 242 NoSend to send, 244 different types); the sends do not fit the day's recorded probabilities; the Decisions file was rewritten the next day. Drew: "No November 13" | Whole day out | **Applied** |
| October 27, 2025 | Sends in two batches (19 and 21 UTC); 617 no-sends cannot be timed; one notification has two distinct successful attempts | Those 617 no-sends and the repeated attempt out; matched single sends kept | **Applied** |
| July 7, 2025 | A NoSend row with an extra logged internship notification (fewer than 10 decisions) | That row out | **Applied** |

[src: `<vault>/Data Preprocessing/22 Validated 2025 Message Matches and Window Timing.md` § "Exceptions and disposition"; `<vault>/Audit Decision Summary 2026-11-14.md` §§ "Second batch (November 16)", "Decided by Drew on November 16 (evening)"; `<memory>/project-ihs-2025-window-anchor-and-delivery.md`]

A uniform fallback on November 13 is plausible from the action frequencies, but the retained files do not identify
what ran, so no new probabilities were assigned. [src: `<vault>/Data Preprocessing/22 ...md` § "Independent Fable comparison"]

### Delivery (2025)

- **Sent is not delivered.** `action_sent = 1` records the chosen action. About 23% of decisions marked sent were not
  delivered (no registered device, or no associated user): 146,393 of 190,369 exactly matched sends succeeded through
  June 19, 2026; in the June 20-30 tail 4,314 of 6,250 succeeded (1,462 NoRegisteredMobileDevice, 459 NoAssociatedUser,
  12 PastNotificationEndDate, 3 ServiceError). `Succeeded` is the platform's delivery status, not proof the message was
  read. [src: `<vault>/Audit Decision Summary 2026-11-14.md` § "Decision times (November 16)"; `<vault>/Data Preprocessing/22 ...md` § "What was validated"; `<vault>/Data Preprocessing/23 June Tail and Approved Rebuild Plan.md`]
- **Rule.** Decisions marked sent but not delivered are not used for causal analysis, as in 2024 (Drew, November 16,
  2026: "In this respect the two datasets should be the same"). They stay in both files with their assignment and
  probabilities, are never recoded as no-send, and still delimit their own day in the window grid. **Applied.**
  [src: `<memory>/project-ihs-2025-window-anchor-and-delivery.md`; `<vault>/Data Preprocessing/22 ...md` § "Timing and boundary rules" item 4]
- **Caution.** Dropping undelivered sends and unreachable days is a selection after assignment; Codex recommends an
  assignment-based analysis alongside. Drew: the delivered-send analysis is the goal; an assignment-based analysis may
  come later. **Proposed** (not run). [src: `<vault>/Audit Decision Summary 2026-11-14.md` §§ "Decided by Drew on November 16 (evening)", "Still for Drew and Jack"]

### Reach restriction and main analysis flags (2025)

**Reach rule** (approved by Drew on November 16, 2026, "Yes, same as 2024"). Use every returned internship attempt,
successful or not, from March 1, 2025 to July 8, 2026 (end exclusive). Remove exact duplicate events and take the
earliest attempt's success per participant and UTC day. An attempted day takes that state; a no-attempt day takes
the state of its neighbouring attempt days if they agree, is "unclear" if they disagree, extends a single available
neighbour, and is "unclear" with no neighbours. Failed sends stay assigned sends and are excluded by the delivery flag.
**Applied** to the main flags; retrospective, not a measure of availability at the decision.
[src: `<vault>/Data Preprocessing/22 ...md` § "Reach rule and independently verified scope correction"; `<shared>/README.md` § "November 16, 2026 — reach restriction applied to 2025 main flags"]

Using the full attempt history made six no-send days (June 14-19, 2026; fewer than 10 participants) "unclear",
because a later failed attempt on June 22 is available. Fable accepted that correction. **Applied.**
[src: same; `<vault>/Data Preprocessing/22 ...md` § "Subsequent board decisions and review"]

Flags in `2025DecisionTiming.csv` (and the window parquet):

| Flag | Definition | Through June 19, 2026 | Through June 30, 2026 (current) | Status |
|---|---|---:|---:|---|
| `retain_delivered_analysis` | Validated single successful sends plus concordant no-sends, outside excluded days | 328,135 (146,371 + 181,764) | not stated | **Superseded** as main flag; kept for sensitivity |
| `retain_delivered_analysis_window` | Above, with a supported next boundary | 326,599 | not stated | kept for sensitivity |
| `retain_delivered_analysis_with_history` | Above, with a supported previous boundary too | 324,070 | not stated | kept for sensitivity |
| `reach_assumption_pass` | Send, or retrospectively reachable no-send | | | **Applied** (component) |
| `retain_main_reach_retrospective` | `retain_delivered_analysis` and reach | 288,121 (146,371 sends + 141,750 no-sends) | 296,194 (150,685 + 145,509) | **Applied**; the engine's analysis flag |
| `main_window_reach_retrospective` | `..._window` and reach | 286,704 (922 participants) | 294,777 | **Applied** (approved main post-outcome flag) |
| `main_with_history_reach_retrospective` | `..._with_history` and reach | 284,368 | 292,441 | **Applied** when the previous window is used as history |

Other added fields: `reachability_retrospective`, `reachability_basis`, `reachability_scope`. The 1,242 synthetic
history and gap rows of the grid carry zero analysis flags. Compared with the unrestricted flag, the reach rule removes
40,008 no-sends (39,648 unreachable, 360 unclear) before the six-day correction. The earlier count 141,756 no-sends and
286,710 windows predates that correction.
[src: `<vault>/Data Preprocessing/22 ...md` §§ "Main analysis counts", "Added fields in both files", "Independent Fable comparison"; `<shared>/README.md` § "November 16, 2026 — 2025 decisions extended..."; `<board>` 2026-11-16 23:46; `<vault>/Audit Decision Summary 2026-11-14.md` § "Still for Drew and Jack"]

### June 20-30, 2026 tail extension

- The decision archive first ended June 19, 2026 (the local copy date), while the notification log showed 6,250
  internship attempts from 1,059 participants over June 20-30. The eleven Decisions, Messages and Behavior files were
  pulled from the server. [src: `<vault>/Data Preprocessing/22 ...md` § "Subsequent board decisions and review"; `<board>` 2026-11-18T13:45 (Codex) item 1]
- Added: 11,673 decisions for 1,062 participants, 6,250 assigned sends (4,314 delivered) and 5,423 no-sends, all sends
  exactly matched to notification attempts. Every earlier row, probability byte and window row is unchanged; the study
  ends June 30, 2026 and later archived decisions were not added. Main counts each rise by 8,073. Built by Codex,
  independently replayed by Fable, released on Drew's word on November 16, 2026. **Applied.** [src: `<shared>/README.md` § "November 16, 2026 — 2025 decisions extended through June 30, 2026"; `<vault>/Data Preprocessing/23 June Tail and Approved Rebuild Plan.md`]
- For 1,106 added no-send days, reach rests on one neighbouring attempt because the send log ends June 30 (947 of them
  June 28-30). Kept as a label. [src: `<shared>/README.md` § "November 16, 2026 — 2025 decisions extended..."]
- Schedules corroborate 2,310 of 2,312 tail Random assignments; fewer than 10 were scheduled fitted but recorded
  Random (fallback, cause not logged). [src: `<vault>/Data Preprocessing/24 ...md`]
- `audit/2025ConditionalAgentProbabilityAudit.csv` was not extended to the tail. Wearable data in the hourly files stop
  around June 20, 2026 for Fitbit, Garmin heart rate and mood (see [02](02-hourly-files.md)). [src: `<shared>/README.md` § "November 16, 2026 — 2025 decisions extended..."; `<vault>/Audit Decision Summary 2026-11-14.md` § "Scan of the published 2025 hourly file"]

## Randomization probabilities: 2024

All 2024 study-year probabilities are those of the **inferred** policy, not recovered server vectors. Baseline rows
are blank (policy unverified, not zero). [src: `<shared>/ProbabilityVariableDictionary.csv` rows `p_send`, `p_CSNoData`]

| Columns | Meaning | Conditioning | Status |
|---|---|---|---|
| `p_send`, `p_no_send` | 0.5 and 0.5 on every study-year row | none | **Applied** |
| `p_CSNoData` ... `p_DSTNoData` (9) | Remaining cores of that type / `pool_size` | **given a send**; the nine sum to 1 | **Applied** |
| `p_mood`, `p_steps`, `p_sleep` | Remaining cores of that domain / `pool_size` | given a send; sum to 1 | **Applied** |
| `p_<domain>_<strategy>` (15) | Remaining cores in that domain-by-strategy cell / `pool_size`, Data and NoData combined | given a send; the 15 sum to 1; each domain's five sum to `p_<domain>`; each strategy summed over domains equals its type marginal | **Applied** |
| `p_<domain>_<arm>` (27) in `2024MessageTypeProbabilities.csv.gz` | Remaining cores in that domain-by-type cell / pool | given a send; summed over domains and over data display they reproduce the published `p_<arm>` and `p_<domain>_<strategy>` on all 318,697 study rows (largest difference 1.4e-16) | **Staged, not applied** (file); used by the engine where configured |

Usage rules (all **Applied** in the README): multiply a content probability by `p_send` for the unconditional
send-and-content probability; divide a joint by a positive `p_<domain>` for strategy given a send in that domain; never
multiply separate domain and strategy marginals to get a joint. Probabilities are present on no-send rows too (they
describe what would have been drawn). [src: `<shared>/README.md` §§ "Domain by strategy joint probabilities — November 11, 2026", "Actual message domain and domain probabilities"; `<vault>/Data Preprocessing/20 ...md` § "Probability meaning"; `<vault>/Causal Analysis Engine/ihs-causal Design.md` § "Message-type probabilities"]

Initial pool: 358 cores (129 mood, 118 steps, 111 sleep), each with four wording variants. Initial cores by type:
DSTNoData 72, MINoData 41, BSData 41, MfnNoData 38, CSNoData 36, CSData 35, MfnData 34, MIData 31, BSNoData 30. So even
before depletion the type probabilities are not uniform. Each of the 27 domain-by-type cells had 3,491 to 11,681 sends
from 8 to 26 distinct cores. [src: `<shared>/README.md` § "Actual message domain and domain probabilities"; `<vault>/Data Preprocessing/05 ...md` § "2024: binary fields retained"; `<board>` 2026-11-16 23:46]

## Randomization probabilities: 2025

### What the server computed

Three different quantities exist for each fitted decision. [src: `<vault>/Data Preprocessing/24 Fable Review - Probability Scopes and Garmin Sleep.md` § "Probability definitions"; `<vault>/Directions for Codex - 2025 Probability Archive Fix.md` §§ "1.1", "11"; `<server>/agents/BuildProbabilitiesDaily.py` `N_DRAWS = 100000`; `<server>/agents/BuildBehaviorProbabilities.py` `N_DRAWS = 1000_000`]

| Quantity | Where | How computed | Conditioning |
|---|---|---|---|
| Logged single-draw vector `p_0..p_9` and `P_behavior` | Daily Decisions file (`MakeDecisions.py`) | One posterior parameter draw, turned into ten probabilities; the action is sampled from them | History **and** the one realized Thompson draw |
| Behavior scalar | `Probabilities/Behavior/<date>_BehaviorProbabilities.csv` (`BuildBehaviorProbabilities.py`), right after the decisions | Average over 1,000,000 draws, for the **action taken** only, acting agent | History, selected agent |
| All-agent archive `P_<agent>_<arm>` | `Probabilities/<Domain>/...Probabilities.csv` and `MasterProbabilities.csv` (`BuildProbabilitiesDaily.py`), run later | Average over 100,000 draws (a lighter script uses 10,000), every agent and every action, with whichever model file is newest when it runs | History, each agent |

### Published scopes

| Columns in `2025BehaviorAgentProbabilities.csv` | Meaning | Status |
|---|---|---|
| `p_no_send`, nine `p_<type>`, `p_send`, `p_observed_action` | Selected agent's `P_<agent>_<arm>` from the archive (or the exact Random vector); the nine type values are **unconditional** on sending and sum with `p_no_send` to 1 | **Applied**; engine `prob_scope: selected` |
| `p_marginal_no_send`, nine `p_marginal_<type>`, `p_marginal_send`, `p_marginal_observed_action` | Mixture before agent selection: sum over the nine agents of Corral weight times that agent's vector, within the scheduled domain. Random rows keep the conditional Random vector | **Applied**; engine default `prob_scope: marginal` |
| `p_agent1_*` ... `p_agent9_*` (incl. `_send`) | Each fitted agent's vector in `decision_domain`, whichever was selected | **Applied** (not read by the engine) |
| `corral_w_agent1` ... `9` | Agent-selection probabilities; blank on Random rows | **Applied** |
| `p_strategy_<s>`, `p_data`, `p_no_data` and the `p_marginal_` versions | Sums of the type columns; the five strategies sum to send, Data plus NoData sums to send; DST has only NoData; no-send excluded | **Applied** (the engine recomputes its own) |
| `mixture_probability_scope`, `mixture_reconstruction_status`, `corral_weight_method`, `corral_weight_log_timestamp`, `corral_schedule_week`, candidate counts, `probability_quality` | Provenance and diagnostics | **Applied** |
| Logged `p_0..p_9` | Separate audit file only | Not a published scope |

Scope counts: 286,647 fitted-agent mixtures, 101,938 conditional Random baselines and 28 unavailable mixtures (the 28
missing selected vectors). Mixture arithmetic error is at most 3.3e-16; complete vectors sum to 1 within 1e-5 (source
rounding). "Conditional" in these files means conditional on an agent, not on sending; none of the fields marginalizes
over the weekly domain schedule. [src: `<shared>/README.md` § "November 11, 2026 — all probability scopes in one CSV"; `<shared>/audit/2025ProbabilityScopesChecks.json`; `<shared>/ProbabilityVariableDictionary.csv`]

The all-agent table gives, for every decision, each of the nine candidates' vectors in the scheduled domain and the
probability each assigns to the recorded action (zero is possible for an unselected candidate); `candidate_agent`,
`candidate_domain` and `is_selected_agent` must be kept. [src: `<shared>/README.md` §§ "Which 2025 file should Jack use?", "Which action was actually taken?"]

### Domain, strategy and domain-by-strategy probabilities (2025)

- The domain is set by the weekly schedule, not drawn at the decision, so within a participant's week the probability
  of a message in another domain is exactly 0 and the probability of a message in the week's domain is `p_send`. There
  are no `p_mood`/`p_steps`/`p_sleep` columns for 2025. [src: `<shared>/ProbabilityVariableDictionary.csv` rows `p_mood`, `decision_domain`; `causal/src/ihs_causal/data/decisions.py` `decisions_2025`]
- A strategy marginal in 2025 is therefore already the domain-by-strategy joint for the scheduled domain, and the
  type probability is the domain-by-type probability. Both are unconditional on sending (unlike 2024). [src: same; `<shared>/README.md` § "Which 2025 file should Jack use?"]

### Released probabilities versus the logged single-draw vector

**Rule: weight 2025 analyses with the released probabilities, not `p_0..p_9`. Applied.**

- The logged vector is the distribution given one random parameter draw. The code's own comment on the equivalent step
  says it is conditional on the draw and not the true probability. `P_<agent>_<arm>` averages over draws and is the
  probability of the action given the history: the propensity. Fable withdrew a proposal to substitute `p_0..p_9` on
  November 16, 2026 after reading the code. [src: `<board>` 2026-11-16 19:27; `<vault>/Data Preprocessing/24 ...md` § "Probability definitions"]
- The logged vector is a valid conditional probability under a larger information set, and it fits the realized
  actions better because the action was drawn from it. That does not make it a better weighting denominator: averaging
  over internal randomization that affects outcomes only through the action reduces inverse-weight variance (with
  equal-probability draws giving q(a) = 0.9 or 0.1, the marginal is 0.5; both inverse-selection indicators have mean 1,
  variances 4.56 and 1). [src: `<vault>/Data Preprocessing/24 ...md` § "Probability definitions"]
- The logged vector puts zero on at least one type on 6,638 main-mask rows; in sleep weeks a single draw typically puts
  nearly all send probability on one type, so it would need a floor and cannot support type-against-type comparisons
  there. [src: `<vault>/Data Preprocessing/24 ...md`; `<vault>/Directions for Codex - 2025 Probability Archive Fix.md` § "2"]
- On November 18, 2026 Fable proposed adding the decision-time vector as a new primary scope ("Fix A"), labelling rows
  by archive alignment ("Fix B") and recomputing on the server ("Fix C"). Drew's decision on November 22, 2026: "The
  released ones, are the right ones." Fix A and the recommendation to use decision-time vectors are **Superseded**;
  Fix B labels are **Proposed**, not built; Fix C produced a server discovery inventory, control replays and private
  September 4-27 reconstructions, none of which was published. [src: `<vault>/Directions for Codex - 2025 Probability Archive Fix.md`; `<board>` 2026-11-22 17:21 and register row AUD-02-F05; `<memory>/project-ihs-2025-type-probabilities.md` (2026-11-22 correction)]
- Codex's control replays favoured keeping the saved archive: on August 8 and September 3, 2025 the selected-agent
  archive value for the action taken was within 0.005 of the Behavior scalar on 854 of 854 and 814 of 852 decisions,
  against 533 and 522 for the best replays. [src: `<board>` 2026-11-18T16:09 (Codex)]
- Marginal versus selected: both are released and valid with the matching conditioning (marginalizing over or
  conditioning on agent selection). The engine uses marginal by default. [src: `<vault>/Data Preprocessing/03 ...md` § "Future product — Corral-weighted action probabilities"; `causal/src/ihs_causal/defaults.yaml` `prob_scope`]

### September 4-27, 2025 fitted probabilities withheld

- **Rule.** For the 20,448 fitted-agent decisions of September 4-27, 2025, every numeric probability (selected-agent,
  per-agent, mixture, agent-selection weights) is blank in both probability files, marked
  `probability_quality = september_fitted_probabilities_withheld`; assignments are kept. The 5,064 scheduled Random
  decisions in the same days keep 0.5 and 1/18. In the all-agent file 184,032 rows are blanked. Release
  `20261119_september_fitted_probabilities`, November 19, 2026. **Withheld.** [src: `<shared>/README.md` § "September 2025 fitted probabilities — November 19, 2026"; `<shared>/audit/2025SeptemberFittedProbabilityExclusion.json`]
- **Why.** All 72 daily all-agent files for September 4-27 were last written on September 28, 2025, by a rerun with
  later models; September 4-19 match the September 28 models, and no earlier copies or backups of those grids survive.
  Private reconstructions recovered the ten pre-selection probabilities only partly (all ten within half a point on
  914 of 979 higher-reliability and 331 of 725 lower-reliability comparison decisions on September 29 and October 2;
  all 90 per-agent values on 189 of 1,704). The dated replay files are available for sensitivity analyses only. [src: `<board>` 2026-11-18T16:45 and 17:17 (Codex), 2026-11-19 "September 3 case review and September 4–27 model provenance"; `<vault>/Data Preprocessing/07 Current Files and Version Register.md` § "November 19 · Private September 2025 probability reconstruction"]
- Nonmissing selected and marginal probabilities: 368,137 of 388,613 rows (= 388,613 minus 20,448 withheld minus 28
  missing). [src: `<shared>/ProbabilityVariableDictionary.csv` row `p_send` `nonmissing_2025`]
- The engine treats them as "probability not published": they drop out of every comparison. Engine check on November
  19, 2026: combined-device analyses use 7-12% fewer decisions. [src: `causal/docs/DESIGN.md` § "Estimators" ("Rows left out"); `<board>` 2026-11-19 "IDLE: the local slot is free"]

### Known source-quality issues that remain in the released 2025 probabilities

| Issue | Size | Handling | Status |
|---|---|---|---|
| Recorded action has probability 0 in the archived selected vector | 1,426 (July 184, August 630, September 612, 2025); 1,425 have a positive Behavior scalar (median 0.857143); 1,364 passed the main timing mask before the September withholding | Never used as an IPW denominator; the engine's floor removes them from any comparison involving that type | **Applied** (kept, flagged in `probability_quality`) |
| Positive but below 1e-6 | 695 | Flagged | **Applied** |
| Missing selected vectors | 28 | Blank, never zero or Random | **Applied** |
| Behavior-scalar archive names a different agent or action for that participant-date | 998 | Scalar not attached; decision kept | **Applied** |
| Archive and Behavior scalar differ by more than 0.02 | 20,331 of 371,711 identity-matched pairs (median difference about 1e-6, 99th percentile about 0.534) | Diagnostic only | **Applied** |
| Archive not aligned with the acting model or context before September 28, 2025 (Fable, November 18: "later model" days July 25 to August 3, August 9-10, September 4-19; "not aligned" days elsewhere before September 28; tiers Random 101,938 / later model 23,879 / not aligned 31,068 / aligned 231,728) | see tiers | September 4-27 withheld (above); other days kept on Codex's control replays and Drew's November 22 decision; an `archive_alignment` label was proposed | Earlier days **Applied** as released; label **Proposed** |
| Archive noisier from September 28 to October 28, 2025 (about 4,000-10,000 draws; SD up to 0.008) | | None needed (unbiased noise) | **Applied** |

[src: `<shared>/README.md` § "Read these limitations before analysis"; `<vault>/Data Preprocessing/05 ...md` § "Important finding"; `<vault>/Data Preprocessing/24 ...md`; `<vault>/Directions for Codex - 2025 Probability Archive Fix.md` §§ "1.2", "1.4", "4", "11"; `causal/docs/DESIGN.md`]

The Behavior scalar (`p_observed_action_separate_mc` in the audit companion) is the designed, more accurate value for
the action taken, but it says nothing about actions not taken, so it cannot support a floor or a mixture. Publishing it
as a main-file column was **Proposed** (November 18) and not applied. Fourteen of 77 Behavior files from July 20 to
October 5, 2025 were last written after their decision date and August 4, 2025 has none. [src: `<vault>/Directions for Codex - 2025 Probability Archive Fix.md` § "11"; `<board>` 2026-11-18T13:52 (Codex)]

## Clipping, floors and renormalization

| Layer | Rule | Status | Source |
|---|---|---|---|
| 2025 server, fitted agents | Total send probability held in [1/7, 6/7] by a bounded logistic; no floor on individual types (softmax). Recorded type probabilities below 0.001 are common in sleep weeks (SleepAgent3 from December 2025) and step weeks (StepsAgent1 from mid-January 2026); mood weeks rarely go below 0.01 | historical fact | `<server>/agents/LightManager.py` `_bounded_send_probs`; `<vault>/Causal Analysis Engine/ihs-causal Design.md` (warning box, November 17) |
| 2025 server, Random | Exactly 0.5 and 1/18 | historical fact | `<server>/agents/config.py` `BASELINE_PROB_10` |
| 2024 inferred policy | 0.5 send; type probabilities are pool counts (zero only for an exhausted cell) | historical model | `<shared>/README.md` § "Update, November 16, 2026..." |
| Published files (both cohorts) | No flooring, no renormalization, no imputation of missing as zero; Corral weights are rounded to six decimals, so a zero weight may not be exact | **Applied** | `<shared>/README.md` § "November 11, 2026 — all probability scopes in one CSV"; `<shared>/CorralProbabilities20261104/README.md` |
| Engine | Drop a decision from a comparison when a compared arm's unconditional probability is below `min_prob` (`positivity: pairwise` checks only the reference and the arm compared; Drew's choice, November 17, 2026); drop arms with fewer than `min_arm_rows` decisions; renormalize probabilities over the compared arms. No weight clipping or truncation. Engine defaults are `min_prob` 0.001 and `min_arm_rows` 200; the report and the presentation use 0.001 for 2024, 0.01 for 2025 and 50 decisions per arm (see [10](10-analysis-rules.md#probability-floor)) | **Applied** | `causal/src/ihs_causal/defaults.yaml`; `causal/src/ihs_causal/design/contrasts.py` `_frame`, `_items`; `report/config/analysis.yaml` `probability`, `min_arm_rows` |
| Floor 0.02 for decision-time vectors; weights capped at 20 for Behavior-scalar weighting | | **Superseded** / not in the engine | `<vault>/Directions for Codex - 2025 Probability Archive Fix.md` §§ "2", "11" |

Under the joint (all-arm) floor, the engine would lose 21% (strategies) and 27% (types) of in-scope step-week decisions
and 42% and 50% of sleep-week decisions in 2025; under the pairwise default the loss per arm is 8-15% in step weeks and
16-46% in sleep weeks; 2024 loses almost nothing. [src: `<vault>/Causal Analysis Engine/ihs-causal Design.md` (warning box)]

## Message coding

### Domain, strategy and data shown versus not

| Field | 2024 source | 2025 source | Status |
|---|---|---|---|
| Domain | `domain` from the catalogue metric of the message sent: Mood to mood, Step Count to steps, Hours of Sleep to sleep. Blank on no-sends and pre-internship rows | `decision_domain` from the selected agent's prefix (the scheduled week's domain), on every row; the timing file's `message_domain` agrees on sends | **Applied** |
| Strategy | Catalogue `ApproachName`: CS, BS, MI, Mfn, DST | Prefix of `action_label` | **Applied** |
| Data shown versus not | `personalization` from catalogue `DataContext` (TRUE = Data, FALSE = NoData) | Suffix of `action_label` | **Applied** |

`personalization` (the engine's `data`) is the **assigned pool**, a category label. It does not record whether a number
was actually displayed or whether wearable data existed for the participant; that depends on the tier (below).
[src: `<shared>/ProbabilityVariableDictionary.csv` rows `domain`, `decision_domain`, `strategy`, `personalization`; `<vault>/Data Preprocessing/22 ...md` § "What was validated"]

### Shared message pool

`<shared>/IHSMessagePool.csv` is the internship pool used by both cohorts: 1,432 notification variants across 358 cores,
16 columns (`Notification Identifier`, `Core Message ID`, `Text`, metric and trigger fields, `ApproachName`,
`DataContext`, design metadata). Both cohorts keep the `Internship2024-...` identifiers. It matches the 2025 server's
`MessageList.csv` on IDs, cores, text, metrics and functions (triggers differ only in formatting; the server copy adds
`Action`/`Agent` columns). It is a catalogue, not a delivery log; it excludes the pre-internship messages. Each core
belongs to exactly one domain-by-type pool and has four rows. **Applied.** [src: `<shared>/README.md` § "Shared IHS message pool"; `<vault>/Results and Document Compilation/Activity Deep Dive/Activity Messages and the Data Fallback.md` (line 152)]

### Tiers and wording variants

- Each core has four variants, one per tier of one of the domain's nine statistics (average, minimum and maximum over
  7 days, 30 days and since the phase began; each message uses one, by rotation): **neutral** (statistic missing or
  0), **low**, **medium**, **high**, with cut points L and H from the message list, the same in both cohorts. Data
  messages also insert the number. [src: `<vault>/Results and Document Compilation/Data Shown vs Not, by Statistic Tier.md` § "How the tiers were rebuilt"; `<memory>/project-ihs-message-tier-comma-faults.md` (2026-11-25)]
- **2025 rule:** low if value < L, high if value >= H; value from the server's daily custom-field file of the decision
  day; a missing, zero or unparsable value gives the neutral variant. Rebuilt tiers match 100% of logged sends.
  [src: same; `<server>/agents/DailyDecisionsToMessages.py` `pick_variant`]
- **2024 rule:** low if value <= L, high if value > H; value = the last update before 20:00 UTC that day from the
  participant-update log. Rebuilt tiers match 99.99% of sends. [src: `<vault>/Results and Document Compilation/Data Shown vs Not, by Statistic Tier.md`]
- The tier tables are audit material (`<shared>/audit/CollaborativeAudit/Opus/Tiers-20261124/`, participant level,
  not reviewed by Codex). They are not in the published decision files and the engine does not read them. Tier and
  availability moderators are covered in [09](09-moderators.md). **Staged, not applied.** [src: same]

### Thousands-comma faults (steps statistics)

Step statistics were stored as strings with a thousands comma (for example "12,345"; about 90% of 2025 values).

| Cohort | What the server did | Consequence | Source |
|---|---|---|---|
| 2025 | `pd.to_numeric(..., errors="coerce")` turned comma strings into missing, so the neutral variant (generic text) was chosen | 97% of sent steps messages, data and no-data, were neutral (July to December 2025); none was "high"; steps data-pool messages almost never showed a number. Behavioral Strategies steps data pool: 10,794 of 11,032 assigned sends (97.8%, including the June tail) used the generic fallback; a separate Codex count gives 10,280 of 10,507 steps data-pool messages (scope not stated). Every comma value was at least 1,000; every unformatted nonzero value was below 1,000. Mood and sleep tiers were well filled, though about half of mood and sleep messages were still neutral (46-57%) | `<vault>/Results and Document Compilation/Data Shown vs Not, by Statistic Tier.md`; `<vault>/Results and Document Compilation/Activity Deep Dive/Activity Messages and the Data Fallback.md`; `<server>/agents/DailyDecisionsToMessages.py` line 119; `<memory>/project-ihs-causal-audit-20261120.md` |
| 2024 | Read the digits before the comma ("12,345" read as 12) | 72% of steps messages were framed "low"; none "high"; the inserted number was correct because the text inserts the stored string. Neutral shares 26-27% | `<vault>/Results and Document Compilation/Data Shown vs Not, by Statistic Tier.md` |

These are facts about what participants received; nothing in the data can or should correct them, and the published
actions and probabilities are unaffected (the fault is downstream of the action draw). The 2025 steps "data versus no
data" contrast therefore does not test data display. Whether every neutral mood or sleep data variant omits the number
is not stated in the sources (**unverified**). [src: `<vault>/Results and Document Compilation/Activity Deep Dive/Activity Messages and the Data Fallback.md` (line 16); `<memory>/project-ihs-message-tier-comma-faults.md`]

## How the engine reads decisions and probabilities

### Files and columns

| Cohort | File (standard name in the data folder) | Columns required by `check.py` |
|---|---|---|
| 2024 | `2024BehaviorAgentProbabilities.csv` | `decision_id`, `participant_id`, `decision_date`, `hour_utc`, `action_sent`, `domain`, `strategy`, `personalization`, `core_message_id`, `time_source`, `p_send`, `p_no_send`, nine `p_<type>`, `p_mood/steps/sleep`, 15 `p_<domain>_<strategy>` |
| 2024 | `2024MessageTypeProbabilities.csv.gz` (optional) | `decision_id`, 27 `p_<domain>_<type>`. Without it the 2024 message-type questions have nothing to estimate |
| 2025 | `2025BehaviorAgentProbabilities.csv` | `decision_id`, `participant_id`, `decision_date`, `action_sent`, `decision_domain`, `action_label`, `p_marginal_no_send`, nine `p_marginal_<type>`; `p_no_send` and nine `p_<type>` for `prob_scope: selected` |
| 2025 | `2025DecisionTiming.csv` | `decision_id`, `window_anchor_utc`, `retain_main_reach_retrospective`, `message_domain`, `core_message_id` |

The engine does not read `2024DecisionHistoryComplete.csv`, `2025DecisionWindows.parquet`, `2025AllAgentProbabilities.csv`,
the Behavior scalar, the logged-draw audit or the tier tables. `config/paths.yaml` can point any file elsewhere; on the
machine that produced the current results it points the 2024 message-type file at the staged candidate in
`<shared>/audit/CollaborativeAudit/Opus/Decisions2024/candidate/`. [src: `causal/src/ihs_causal/check.py` `NEEDS`, `OPTIONAL_FILES`; `causal/src/ihs_causal/paths.py` `FILES`; `causal/config/paths.example.yaml`; `<vault>/Causal Analysis Engine/ihs-causal Design.md` § "Message-type probabilities"]

### Common decision schema

`causal/src/ihs_causal/data/decisions.py` (`decisions_2024`, `decisions_2025`) builds one table per cohort with the
same columns, so contrasts never branch on cohort. **Applied.**

| Engine column | 2024 | 2025 |
|---|---|---|
| `anchor_hour` | `hour_utc` (floored attempt or imputed hour) | `window_anchor_utc` from the timing file |
| `in_analysis` | decision date July 1, 2024 to June 30, 2025 and `time_source` present (drops the 44,111 baseline rows; the file already holds only delivered sends and reachable no-sends) | `retain_main_reach_retrospective` = 1 (296,194 decisions) |
| `send` | `action_sent` | `action_sent` |
| `domain` | message domain (blank for no-sends) | scheduled week's domain, for every row |
| `strategy`, `data`, `arm` | from `strategy`, `personalization` (`data` = -1 for no-sends) | from `action_label` |
| `p_none`, `p_send` | file values | `p_marginal_no_send` (or `p_no_send`); `p_send` = 1 - `p_none` |
| `p_arm_<type>` | `p_send` x `p_<type>` | `p_marginal_<type>` (or `p_<type>`) |
| `p_dom_<d>` | `p_send` x `p_<d>` | `p_send` in d's weeks, exactly 0 otherwise |
| `p_dom_<d>_<s>` | `p_send` x `p_<d>_<s>` | sum of that strategy's types in d's weeks, 0 otherwise |
| `p_strat_<s>`, `p_data`, `p_nodata` | sums of `p_arm_*` | sums of `p_arm_*` |
| `p_type_<d>_<type>` | `p_send` x companion `p_<d>_<type>`, missing without the file | `p_arm_<type>` in d's weeks, 0 otherwise |

All probabilities in the engine table are unconditional (they include the probability of sending). The exact zeros for
other domains' weeks are set even where the file is blank (September 4-27 fitted rows), so such rows count as out of
scope rather than as missing probabilities. [src: `causal/src/ihs_causal/data/decisions.py` module docstring and both adapters]

Windows are built from the `in_analysis` decisions only (next-decision windows, 20-28 hours); see [07](07-outcome-windows.md). [src: `causal/src/ihs_causal/data/features.py` `window_stats`; `causal/src/ihs_causal/defaults.yaml` `window`]

### Contrasts

Each contrast picks decisions by arm, attaches the unconditional probability of each compared arm, and hands an
`AnalysisFrame` to the estimator. Arm 0 is the reference. [src: `causal/src/ihs_causal/design/contrasts.py`]

| Contrast | Question | Reference | Compared arm(s) | Probabilities | In standing configs |
|---|---|---|---|---|---|
| `any_vs_none` | Q1 | no send | any send | `p_none`, `p_send` | primary, q6 |
| `domain_vs_none` | Q4 (own domain) / Q5 (cross) | no send | send in domain d, for each d | `p_none`, `p_dom_<d>` | primary, q6 |
| `strategy_vs_none` | Q2 | no send | each strategy within the outcome's domain | `p_none`, `p_dom_<d>_<s>` | primary |
| `strategy_pairwise` | Q2 | CS messages in d | other strategies in d | `p_dom_<d>_<s>` | no |
| `data_vs_nodata` | Q3 | no-data sends (all domains) | data sends | `p_nodata`, `p_data` | primary |
| `data_within_strategy` | Q3 | `<s>NoData` | `<s>Data`, for CS, BS, MI, Mfn | `p_arm_*` | primary |
| `type_vs_none` | Q2T | no send | each of nine types in the outcome's domain | `p_none`, `p_type_<d>_<type>` | primary |
| `type_any_vs_none` | Q2T | no send | each type, any domain | `p_none`, `p_arm_<type>` | no |

[src: `causal/src/ihs_causal/design/contrasts.py`; `causal/config/primary_2024.yaml`, `primary_2025.yaml`, `q6_2024.yaml`, `q6_2025.yaml`, `pipeline.yaml`; `causal/docs/DESIGN.md` § "Questions"]

Frame rules (**Applied**, `causal/src/ihs_causal/design/contrasts.py` `_frame`, `_items`):

1. Keep a decision when it received one of the compared arms, its outcome is present, every compared probability is
   present and at least `min_prob` (checked on the unconditional values; engine default 0.001, report and
   presentation 0.001 for 2024 and 0.01 for 2025), and every moderator is present.
2. With `positivity: pairwise` (default) a multi-arm contrast becomes one frame per arm against the reference, so only
   those two probabilities are checked; `joint` checks all arms in one frame, as in Jack's notebook.
3. Drop non-reference arms with fewer than `min_arm_rows` kept decisions (engine default 200; the report and the
   presentation use 50 since 2026-11-24).
4. Renormalize the probabilities over the remaining compared arms; this is the propensity once rows are restricted to
   decisions that received one of them.
5. Removed decisions are counted by reason: "probability not published" (blank, e.g. September 4-27, 2025 fitted),
   "no compared message possible" (all non-reference probabilities exactly 0, e.g. another domain's week in 2025;
   out of scope by design), "below the floor".

Consequences: in 2025 a domain, strategy or type contrast effectively compares messages with no-message days inside
that domain's weeks, because no-sends in other weeks have probability 0 for the compared message. In 2024 every
study-year no-send can serve as reference for every domain. `date_from` and `date_to` restrict decision dates.
The WCLS numerator probability `p_tilde` is the mean of each renormalized probability column; DR-WCLS uses the
renormalized probabilities directly. Model details are in [11](11-model.md). [src: `causal/src/ihs_causal/design/contrasts.py`; `causal/src/ihs_causal/estimators/frame.py`; `causal/src/ihs_causal/estimators/core.py` `wcls`, `drwcls`; `causal/docs/DESIGN.md` § "Estimators"]

### Data versions behind results

Each stored result records the SHA-256 of every input. The engine README lists the files behind results as of
November 18, 2026: 2025 decisions `6704c3b2968a` (before the September withholding), timing `825e04e45462`; 2024
decisions `c5adc147f636`, message types `686c1f4366ba`. Results computed from the November 19 file (`539dfa17...`)
leave out the September 4-27 fitted decisions; the app flags results made from an earlier file. [src: `causal/README.md` § "The data files"; `causal/docs/DESIGN.md` § "Data files"; `<board>` 2026-11-19 "IDLE: the local slot is free"]

## Source conflicts and how they were resolved

| Topic | Sources disagree | Resolution |
|---|---|---|
| 2025 weighting probabilities | November 18 directions recommend decision-time vectors as primary; November 16 review, Codex replays and Drew (November 22) say released averaged probabilities | Released probabilities (later, dated decision by Drew; code semantics) |
| Whether failed 2024 sends use up a core | README "Probability interpretation" (November 11): yes; rebuild (November 16): no | No (later record, log test 2,813 vs 2,720) |
| 2024 no-sends whose hour changed | 2,459 (README) vs 2,444 (review note) | Both right: 2,459 over all old study rows, 2,444 among rows kept after the reach filter |
| 2025 reachable no-sends and windows | 141,756 / 286,710 (decision summary) vs 141,750 / 286,704 (current) | Current counts; the six-day June 14-19 scope correction removed six rows |
| 2024 main-file fingerprint | Version register's November 19 fingerprint list gives `f294d670...`; manifest, validation file, README and engine README give `c5adc147...` and call `f294d670...` the previous file | `c5adc147...` is current; the register list is stale for this file |
| How the 2025 week's domain is assigned | Engine design and docstrings say "randomized by week"; an activity note says "a separate draw"; mirrored `BuildSchedule.py` rotates domains weekly from a randomly assigned permanent group | Code taken as the mechanism (random phase, deterministic rotation), **unverified** against the historical script; engine use is unaffected because it compares within a domain's weeks |
| How a fitted agent splits send probability among types | Engine design note: proportional to predicted benefit; mirrored code: softmax of scores | Code (`_bounded_send_probs`); both agree there is no floor and the send total is held in [1/7, 6/7] |
| When the 2025 `hour_utc` label became midnight | July 25 (decision summary) vs August 11, 2025 (directions note) | Not resolved here; irrelevant to analysis because the timing file's anchor is used; see [03](03-clocks-and-time-zones.md) |
| Size of the 2025 Random control group | 213 participants plus warm-up months (engine design note) vs 90 people all year (board, November 22) | **Unverified**; definitions likely differ |
| Behavior scalar written "minutes after" every decision | Directions note vs Codex file times (14 of 77 files rewritten later) | The scalar stays the designed value; timing claim **unverified** for those dates |

## Open and unverified items

- 2024: no-send days are inferred; job outages cannot be ruled out. The 2024 server code is unavailable. The staged
  repeated-core correction is not applied. The 2024 message-type file is staged and not in the shared root.
  [src: `<shared>/ProbabilityExportValidation.json` `limits`; `<vault>/Causal Analysis Engine/ihs-causal Design.md`]
- 2025: the probability of a Random fallback is not reconstructed; Corral mixtures are reconstructed from rounded
  weights and finite Monte Carlo vectors, not certified historical propensities; archive alignment before September 28,
  2025 is unresolved except for the withheld September 4-27 days; Fix B labels not built. [src: `<shared>/CorralProbabilities20261104/README.md`; `<vault>/Directions for Codex - 2025 Probability Archive Fix.md`]
- Both: reach is retrospective; the assignment-based sensitivity analysis is not run. [src: `<vault>/Audit Decision Summary 2026-11-14.md`]
- Not checked for this note: the historical versions of `BuildSchedule.py`, `MakeDecisions.py` and
  `DailyDecisionsToMessages.py` (only the June 2026 mirror was read); the 2024 send hour; whether neutral mood and sleep
  data variants omit the number.

## Facts other notes should carry

For [07 outcome windows](07-outcome-windows.md):

- 2025 anchors come from `window_anchor_utc` (floored logged attempt for sends; the day's single observed send hour,
  flagged imputed, for no-sends), never from `hour_utc`. 2024 anchors are `hour_utc` (floored attempt or imputed no-send
  hour; 5,099 uncertain in the main file).
- The published 2025 grid was built from every decision before filtering and supplies window-level flags
  (`main_window_reach_retrospective` 294,777; `main_with_history_reach_retrospective` 292,441). The engine instead takes
  the decision-level `retain_main_reach_retrospective` (296,194) and builds its own next-decision windows over those
  decisions only, with a 20-28 hour span rule. Note 07 should state whether these agree and which counts the results use.
- Failed sends and conflicting days still delimit their own days in the published grid; excluded whole days are July 1,
  July 14 and November 13, 2025, plus 617 October 27 no-sends.
- Hourly wearable data end near June 20, 2026 while decisions run to June 30, 2026.

For [09 moderators](09-moderators.md):

- `personalization`/`data` is the assigned pool, not whether a number was shown. Tier rules differ by cohort
  (2025: low < L, high >= H; 2024: low <= L, high > H), the statistic is one of nine per domain chosen by rotation, and
  the 2024 statistic is the last update before 20:00 UTC.
- The steps comma faults: 2025 steps messages 97% neutral (data display essentially absent); 2024 steps 72% framed
  "low" with the correct number shown; no "high" steps messages in either cohort.
- Tier tables live only in the audit folder and are not reviewed by Codex.

For [10 analysis rules](10-analysis-rules.md) and [11 model](11-model.md):

- 2025 weights: released probabilities, marginal scope by default; never `p_0..p_9`; September 4-27 fitted decisions
  have no probabilities. 2024 content probabilities are conditional on sending and the engine multiplies by `p_send`.
- Floor (pairwise) 0.001 in 2024 and 0.01 in 2025 and arm minimum 50 in the report and presentation (engine
  defaults 0.001 and 200), renormalization over compared arms, no weight truncation.
- In 2025 sleep weeks after late October 2025 the fitted policy sends almost only BSData (SleepAgent3), so sleep-week
  strategy and type comparisons have overlap mainly before October 27, 2025 and in Random-policy rows.
  [src: `<board>` 2026-11-17 00:22]
