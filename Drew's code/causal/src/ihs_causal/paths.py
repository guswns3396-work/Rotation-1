"""Where the data and the working directory are, on this machine.

`ihs-causal setup DATA_FOLDER` writes config/paths.yaml from config/paths.example.yaml with `data_root` set to the folder
that holds the shared files (dfHourly2024.csv, 2024BehaviorAgentProbabilities.csv, ...). paths.yaml is per machine and
is never committed.
Input files are fingerprinted (SHA-256) once and the fingerprint is remembered by path, size and modification time,
so every cached table and every result records exactly which data version produced it.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ihs_causal.config import load_yaml

FILES = {      # the shared files each cohort reads; `ihs-causal check` lists the columns each must have
    2024: {"hourly": "dfHourly2024.csv", "decisions": "2024BehaviorAgentProbabilities.csv", "surveys": "2024SurveyData.csv",
           "message_types": "2024MessageTypeProbabilities.csv.gz"},
    2025: {"hourly": "dfHourly2025.csv", "decisions": "2025BehaviorAgentProbabilities.csv",
           "timing": "2025DecisionTiming.csv", "surveys": "2025SurveyData.csv"},
}


@dataclass
class Paths:
    data_root: Path
    work_dir: Path
    project_dir: Path
    overrides: Dict = None

    def file(self, cohort: int, kind: str) -> Path:
        """A shared file; paths.yaml can point any file elsewhere under `files: {2024: {message_types: ...}}`.
        A relative path there is inside data_root, so one paths file works on every machine that has the shared folder."""
        o = ((self.overrides or {}).get(int(cohort)) or (self.overrides or {}).get(str(cohort)) or {}).get(kind)
        if not o:
            return self.data_root / FILES[int(cohort)][kind]
        p = Path(o).expanduser()
        return p if p.is_absolute() else self.data_root / p

    @property
    def cache_dir(self) -> Path:
        return self.work_dir / "cache"

    @property
    def results_dir(self) -> Path:
        return self.work_dir / "results"


def find_project_dir(start: Optional[Path] = None) -> Path:
    """The project folder: the current folder or one above it, else the folder this package was installed from."""
    p = (start or Path.cwd()).resolve()
    for cand in [p, *p.parents, Path(__file__).resolve().parents[2]]:
        if (cand / "pyproject.toml").exists() and (cand / "src" / "ihs_causal").exists():
            return cand
    return p


def load_paths(path: Optional[Path] = None) -> Paths:
    project = find_project_dir()
    cfg_path = path or Path(os.environ.get("IHS_CAUSAL_PATHS", project / "config" / "paths.yaml"))
    if not cfg_path.exists():
        raise FileNotFoundError(f"no paths file at {cfg_path}. Run `ihs-causal setup /path/to/shared/folder` once on this "
                                f"machine (or copy config/paths.example.yaml to config/paths.yaml and set data_root).")
    cfg = load_yaml(cfg_path)
    data_root = Path(cfg["data_root"]).expanduser()
    work_dir = Path(cfg.get("work_dir", project / "work")).expanduser()
    if not work_dir.is_absolute():
        work_dir = project / work_dir
    return Paths(data_root=data_root, work_dir=work_dir, project_dir=project, overrides=cfg.get("files") or {})


def plan_paths(project_dir: Path, data_root: Path) -> Tuple[Paths, Dict, List[str]]:
    """The settings `setup` would write for a data folder, from config/paths.example.yaml: data_root, the work folder,
    and each file the example reads from elsewhere, kept only if it exists in this folder. A missing one falls back to
    the standard file, with a note, so a fresh machine still runs (and its results record which file they came from)."""
    project_dir = Path(project_dir)
    ex_path = project_dir / "config" / "paths.example.yaml"
    example = load_yaml(ex_path) if ex_path.exists() else {}
    root = Path(data_root).expanduser().resolve()
    files: Dict[int, Dict[str, str]] = {}
    notes: List[str] = []
    for c, kinds in (example.get("files") or {}).items():
        for kind, rel in (kinds or {}).items():
            p = Path(str(rel)).expanduser()
            if (p if p.is_absolute() else root / p).exists():
                files.setdefault(int(c), {})[kind] = Path(str(rel)).as_posix()
            else:
                notes.append(f"{c} {kind}: {Path(str(rel)).as_posix()} is not in this folder, so the standard "
                             f"{FILES[int(c)][kind]} is read instead. Results can differ from those made with the other file.")
    # changing the folder on a machine already set up keeps its own file settings that still point at existing files
    cur_path = project_dir / "config" / "paths.yaml"
    current = load_yaml(cur_path) if cur_path.exists() else {}
    for c, kinds in (current.get("files") or {}).items():
        for kind, val in (kinds or {}).items():
            p = Path(str(val)).expanduser()
            if (p if p.is_absolute() else root / p).exists():
                files.setdefault(int(c), {})[kind] = p.as_posix()
                notes = [n for n in notes if not n.startswith(f"{c} {kind}:")]
            else:
                notes.append(f"{c} {kind}: the earlier setting {p.as_posix()} is not found from this folder and is dropped.")
    work = Path(str(current.get("work_dir") or example.get("work_dir", "work"))).expanduser()
    work = work if work.is_absolute() else project_dir / work
    return Paths(data_root=root, work_dir=work, project_dir=project_dir, overrides=files), files, notes


def write_paths_file(project_dir: Path, data_root: Path, files: Dict) -> Path:
    """Write config/paths.yaml (see plan_paths) and return its path."""
    project_dir = Path(project_dir)
    ex_path, cur_path = project_dir / "config" / "paths.example.yaml", project_dir / "config" / "paths.yaml"
    work = ((load_yaml(cur_path) if cur_path.exists() else {}).get("work_dir")
            or (load_yaml(ex_path) if ex_path.exists() else {}).get("work_dir", "work"))
    lines = ["# This machine's data location, written by `ihs-causal setup` or the app's setup page. Never committed.",
             "# config/paths.example.yaml explains every option.",
             f'data_root: "{Path(data_root).as_posix()}"', f"work_dir: {work}"]
    if files:
        lines.append("files:")
        for c in sorted(files, reverse=True):
            lines.append(f"  {c}:")
            lines += [f'    {k}: "{v}"' for k, v in files[c].items()]
    out = project_dir / "config" / "paths.yaml"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def fingerprint(path: Path, registry_file: Optional[Path] = None) -> str:
    """SHA-256 of a file, remembered by (path, size, mtime) so large files are hashed once."""
    st = path.stat()
    key = f"{path.resolve()}|{st.st_size}|{int(st.st_mtime)}"
    memo: Dict[str, str] = {}
    if registry_file and registry_file.exists():
        memo = json.loads(registry_file.read_text(encoding="utf-8"))
    if key in memo:
        return memo[key]
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    digest = h.hexdigest()
    if registry_file:
        registry_file.parent.mkdir(parents=True, exist_ok=True)
        memo[key] = digest
        registry_file.write_text(json.dumps(memo, indent=1), encoding="utf-8")
    return digest
