# data

Put the shared study files here. Git ignores everything in this folder except this README and the `.gitignore`, so
nothing here is ever committed or pushed. The repository is public, so participant data must never leave this folder
through git.

The analysis package in `Drew's code/causal/` reads these files. Its setup page, shown on the first start, suggests this
folder. You can point it at another folder instead, such as the shared folder itself. Jack's notebooks can use it too,
with `data_path` in `config.yml`.

| Cohort | File | Needed for |
|---|---|---|
| 2025 | `dfHourly2025.csv` | wearable and mood outcomes and history |
| 2025 | `2025BehaviorAgentProbabilities.csv` | decisions and randomization probabilities |
| 2025 | `2025DecisionTiming.csv` | window anchors and the analysis flag |
| 2025 | `2025SurveyData.csv` | baseline traits |
| 2024 | `dfHourly2024.csv` | wearable and mood outcomes and history |
| 2024 | `2024BehaviorAgentProbabilities.csv` | decisions and randomization probabilities |
| 2024 | `2024SurveyData.csv` | baseline traits |
| 2024 | `2024MessageTypeProbabilities.csv.gz` (optional) | the 2024 message-type questions only |

- **Mood-corrected hourly files (optional):** put them in a subfolder, `Hourly_MoodCorrected_20261117/`, holding
  `dfHourly2024.csv` and `dfHourly2025.csv`. Setup then uses them, and they are what the current results were made from.
- **Per cohort:** a cohort runs once its own files are all here.
- **Checking:** the setup page, or `ihs-causal check`, lists what is found and the start of each file's SHA-256.
  Matching fingerprints mean matching results.
