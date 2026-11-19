# Drew's code

Drew's work in Jack's repository, kept apart from Jack's own files: nothing outside this folder and `data/` is changed.
Study data never go into git: they belong in the repository's `data/` folder, where git ignores everything (see
`data/README.md`).

| Folder | What it is |
|---|---|
| `causal/` | The `ihs-causal` package: causal excursion-effect analyses for both cohorts, with a results app. Start it by double-clicking `causal/Start (Windows).bat` or `causal/Start (Mac).command`; see `causal/README.md`, and `causal/docs/DESIGN.md` for the methods. Its caches and results stay in `causal/work/`, which git ignores. |
| `notebooks/1_preprocess.ipynb`, `environment.yml` | A copy of Jack's preprocessing notebook with a timestamp-parsing fix (below). |

## The notebook copy (November 16, 2026)

| File | Copied from | Change |
|---|---|---|
| `notebooks/1_preprocess.ipynb` | `notebooks/1_preprocess.ipynb` at commit `063fb21` | Timestamp parsing (below) |
| `environment.yml` | `environment.yml` at the same commit | `pandas` becomes `pandas>=2.0` |

Jack's notebook read timestamps in two places, and both broke on the data files of that time:

- **UTC time.** The 2025 hourly file holds two formats (`2025-07-01T08:00:00Z` and `2025-07-01 08:00:00+00:00`). With the current pandas, the original line stops with an error on the second format. The copy reads both.
- **Local time.** The original helper expects a space between date and time. The files use a `T`, so it returned a blank for every row. The copy reads both.

Three lines change and one comment line is added. Nothing else differs from Jack's notebook at `063fb21`.

**Checks:**
- The patch is Codex's. It applies cleanly to commit `063fb21`.
- Fable checked the same parsing on every row of both hourly files (15,027,847 rows): no value fails to parse and no local time changes.

**Since then:** Jack's notebook has moved on. Commits up to `3c9c2a4` change its own timestamp handling (`native_local`, rows without UTC time dropped explicitly). This copy has not been compared with them, and may no longer be needed.
