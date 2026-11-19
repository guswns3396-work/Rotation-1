"""Command line: ihs-causal <command>

  setup DATA_FOLDER [--force]         write config/paths.yaml for this machine, then check the files
  check [--no-hash]                   are the shared files there, with the columns the engine reads? (headers only)
  reproduce [--cohort N] [--dry-run]  run every standing analysis in config/pipeline.yaml, then build the snapshot
  run CONFIG [CONFIG ...] [--force]   run every analysis in the configuration(s); finished runs are skipped
  prune CONFIG [CONFIG ...]           drop stored runs of these configurations that the files no longer produce
  refresh [--dry-run]                 rerun every stored analysis made from older data files (same settings, current files)
  view [--out FILE]                   build a static HTML snapshot of the results (for sharing)
  serve [--port N] [--no-browser]     the results viewer as a local app that can also run analyses
  list                                show registered outcomes, contrasts, estimators, learners and windows
  selftest                            simulated trials with known effects: checks the estimators and their speed
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def _cmd_setup(args) -> int:
    from ihs_causal.paths import find_project_dir, plan_paths, write_paths_file
    project = find_project_dir()
    target = project / "config" / "paths.yaml"
    if target.exists() and not args.force:
        print(f"{target} already exists; add --force to replace it")
        return 1
    root = Path(str(args.data_folder).strip().strip('"').strip("'")).expanduser()
    if not root.is_dir():
        print(f"no folder at {root}")
        return 1
    paths, files, notes = plan_paths(project, root)
    print(f"wrote {write_paths_file(project, paths.data_root, files)}")
    for n in notes:
        print(f"  note: {n}")
    print()
    args.paths, args.no_hash = None, False
    return _cmd_check(args)


def _cmd_check(args) -> int:
    from ihs_causal.check import check_files, format_report
    from ihs_causal.paths import load_paths
    paths = load_paths(Path(args.paths) if args.paths else None)
    if not args.no_hash:
        print("fingerprinting the files (a large file takes a few seconds, once)")
    report = check_files(paths, hashes=not args.no_hash)
    print(format_report(report, paths.data_root))
    ready = [c for c, r in report.items() if r["ready"]]
    print(f"\n{'Ready to run: ' + ', '.join(map(str, ready)) if ready else 'No cohort can run yet.'}")
    return 0 if ready else 1


def _cmd_reproduce(args) -> int:
    import gc
    from ihs_causal.check import NEEDS, check_files
    from ihs_causal.paths import load_paths
    from ihs_causal.results import ResultStore
    from ihs_causal.runner import pending_specs, run_specs, standard_specs
    from ihs_causal.workspace import Workspace
    paths = load_paths(Path(args.paths) if args.paths else None)
    plan_path = Path(args.pipeline) if args.pipeline else paths.project_dir / "config" / "pipeline.yaml"
    try:
        plan = standard_specs(plan_path)
    except ValueError as e:
        print(f"{e}; fix it first")
        return 1
    cohorts = [int(c) for c in args.cohort] if args.cohort else list(plan)
    report = check_files(paths, [c for c in cohorts if c in NEEDS], hashes=False)
    t0 = time.perf_counter()
    failed = False
    for c in cohorts:
        if c not in plan or c not in report:
            print(f"{c}: not in {plan_path}"); failed = True
            continue
        if not report[c]["ready"]:
            print(f"{c}: skipped, {report[c]['status']} (`ihs-causal check` shows the details)")
            continue
        files, specs = plan[c]
        ws = Workspace(paths)       # one per cohort, so a cohort's tables are freed before the next is built
        todo = pending_specs(specs, ws, force=args.force)
        print(f"{c}: {len(specs)} analyses in {', '.join(files)}; {len(todo)} to run, "
              f"{len(specs) - len(todo)} already stored from these files")
        if todo and not args.dry_run:
            run_specs(todo, ws, force=True)
        del ws
        gc.collect()
    if args.dry_run:
        return 1 if failed else 0
    if not args.no_view and ResultStore(paths.results_dir).run_ids():
        _cmd_view(argparse.Namespace(paths=args.paths, out=None))
    print(f"done in {time.perf_counter() - t0:.0f}s. `ihs-causal serve` opens the results app.")
    return 1 if failed else 0


def _cmd_run(args) -> int:
    from ihs_causal.config import iter_specs
    from ihs_causal.paths import load_paths
    from ihs_causal.runner import run_specs
    from ihs_causal.workspace import Workspace
    paths = load_paths(Path(args.paths) if args.paths else None)
    ws = Workspace(paths)
    specs = [s for c in args.configs for s in iter_specs(Path(c))]
    print(f"{len(specs)} runs in {', '.join(args.configs)}; data from {paths.data_root}")
    t0 = time.perf_counter()
    run_specs(specs, ws, force=args.force)
    print(f"done in {time.perf_counter() - t0:.1f}s; results in {paths.results_dir}")
    return 0


def _cmd_prune(args) -> int:
    from ihs_causal.config import iter_specs, load_yaml
    from ihs_causal.paths import load_paths
    from ihs_causal.results import ResultStore
    paths = load_paths(Path(args.paths) if args.paths else None)
    store = ResultStore(paths.results_dir)
    for c in args.configs:
        name = load_yaml(Path(c)).get("name", "unnamed")
        n = store.prune(name, {s["run_id"] for s in iter_specs(Path(c))})
        print(f"{name}: removed {n} superseded runs")
    return 0


def _cmd_refresh(args) -> int:
    from collections import Counter
    from ihs_causal.paths import load_paths
    from ihs_causal.results import ResultStore
    from ihs_causal.runner import run_specs, stale_specs
    from ihs_causal.workspace import Workspace
    paths = load_paths(Path(args.paths) if args.paths else None)
    ws = Workspace(paths)
    specs = stale_specs(ws)
    total = len(ResultStore(paths.results_dir).run_ids())
    print(f"{len(specs)} of {total} stored analyses were made from older data files")
    for (c, name), n in sorted(Counter((s["cohort"], s["config_name"]) for s in specs).items(), key=str):
        print(f"  {c} {name}: {n}")
    if args.dry_run or not specs:
        return 0
    t0 = time.perf_counter()
    run_specs(specs, ws, force=True)
    print(f"done in {time.perf_counter() - t0:.1f}s; results in {paths.results_dir}")
    return 0


def _cmd_view(args) -> int:
    from ihs_causal.paths import load_paths
    from ihs_causal.viewer.build import build_viewer
    paths = load_paths(Path(args.paths) if args.paths else None)
    out = Path(args.out) if args.out else paths.work_dir / "ihs_causal_results.html"
    from ihs_causal.workspace import Workspace
    build_viewer(paths.results_dir, out, paths.project_dir, current=Workspace(paths).current_inputs())
    print(f"viewer written to {out}")
    return 0


def _cmd_serve(args) -> int:
    import os
    from ihs_causal.paths import find_project_dir, load_paths
    from ihs_causal.serve import serve
    try:
        paths = load_paths(Path(args.paths) if args.paths else None)
    except FileNotFoundError:
        if args.paths or os.environ.get("IHS_CAUSAL_PATHS"):
            raise
        paths = None            # first start on this machine: the app opens on its setup page
    return serve(paths, find_project_dir(), port=args.port, open_browser=not args.no_browser)


def _cmd_list(args) -> int:
    from ihs_causal.data.features import OUTCOMES
    from ihs_causal.data.windows import WINDOWS
    from ihs_causal.design.contrasts import CONTRASTS
    from ihs_causal.estimators import ESTIMATORS, LEARNERS
    print("outcomes:   ", ", ".join(OUTCOMES))
    print("contrasts:  ", ", ".join(CONTRASTS.names()))
    print("estimators: ", ", ".join(ESTIMATORS.names()))
    print("learners:   ", ", ".join(LEARNERS.names()))
    print("windows:    ", ", ".join(WINDOWS.names()))
    return 0


def _cmd_selftest(args) -> int:
    from ihs_causal.estimators import drwcls, wcls
    from ihs_causal.simulate import simulate_mrt
    frame, truth = simulate_mrt(n_people=900, n_decisions=330, seed=11)
    ok = True
    for fn in (wcls, drwcls):
        t0 = time.perf_counter(); res = fn(frame); dt = time.perf_counter() - t0
        for arm in ("arm1", "arm2"):
            r = res.table[(res.table.arm == arm) & (res.table.term == "effect")].iloc[0]
            hit = abs(r.estimate - truth[arm]) < 4 * r.se
            ok &= hit
            print(f"{fn.__name__:7} {arm}: estimate {r.estimate:+.3f} (truth {truth[arm]:+.3f}, se {r.se:.3f}) {'ok' if hit else 'MISS'}")
        print(f"{fn.__name__:7} {frame.n:,} rows in {dt:.2f}s")
    return 0 if ok else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="ihs-causal", description="IHS causal excursion-effect analysis")
    p.add_argument("--paths", help="paths file (default: config/paths.yaml or $IHS_CAUSAL_PATHS)")
    sub = p.add_subparsers(dest="cmd", required=True)
    su = sub.add_parser("setup", help="write config/paths.yaml for this machine")
    su.add_argument("data_folder", help="the shared folder holding dfHourly2025.csv, 2025BehaviorAgentProbabilities.csv, ...")
    su.add_argument("--force", action="store_true", help="replace an existing config/paths.yaml"); su.set_defaults(fn=_cmd_setup)
    ck = sub.add_parser("check", help="check the shared files (column names only)")
    ck.add_argument("--no-hash", action="store_true", help="skip the SHA-256 fingerprints"); ck.set_defaults(fn=_cmd_check)
    rp = sub.add_parser("reproduce", help="run every standing analysis, then build the snapshot")
    rp.add_argument("--cohort", action="append", help="only this cohort (repeatable)")
    rp.add_argument("--pipeline", help="pipeline file (default config/pipeline.yaml)")
    rp.add_argument("--force", action="store_true", help="recompute runs already stored from the same files")
    rp.add_argument("--dry-run", action="store_true", help="only count what would run")
    rp.add_argument("--no-view", action="store_true", help="skip the static snapshot"); rp.set_defaults(fn=_cmd_reproduce)
    r = sub.add_parser("run"); r.add_argument("configs", nargs="+"); r.add_argument("--force", action="store_true"); r.set_defaults(fn=_cmd_run)
    pr = sub.add_parser("prune"); pr.add_argument("configs", nargs="+"); pr.set_defaults(fn=_cmd_prune)
    rf = sub.add_parser("refresh"); rf.add_argument("--dry-run", action="store_true"); rf.set_defaults(fn=_cmd_refresh)
    v = sub.add_parser("view"); v.add_argument("--out"); v.set_defaults(fn=_cmd_view)
    sv = sub.add_parser("serve"); sv.add_argument("--port", type=int, default=8766); sv.add_argument("--no-browser", action="store_true"); sv.set_defaults(fn=_cmd_serve)
    sub.add_parser("list").set_defaults(fn=_cmd_list)
    sub.add_parser("selftest").set_defaults(fn=_cmd_selftest)
    args = p.parse_args(argv)
    try:
        return args.fn(args)
    except FileNotFoundError as e:      # a missing paths file or data file: say what to do, without a traceback
        print(f"ihs-causal {args.cmd}: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
