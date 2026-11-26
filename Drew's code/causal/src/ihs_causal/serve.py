"""`ihs-causal serve`: the results viewer as a local app that can also run analyses.

Python standard library only. Listens on 127.0.0.1, so only this computer can reach it. Runs are queued and executed one
at a time on a worker thread (the desktop runs one heavy job at a time); window statistics stay in memory between runs,
so changing a device, keep rule or estimator costs seconds.

Endpoints
  GET  /               the viewer, with the current results embedded
  GET  /api/payload    the results (JSON), for refreshing after a run
  GET  /api/options    choices and defaults for the Run form
  GET  /api/jobs       {"jobs": queued, running and finished jobs with their log lines, "stamp": results version}
  POST /api/setup      {"data_root": folder} -> checks the folder (headers only) and, if a cohort can run, saves it
  POST /api/standard   queue every standing analysis in config/pipeline.yaml not yet stored, one job per cohort
  POST /api/run        {form fields} -> job (its run ids, cohort and device, so the page can show exactly its results)
  POST /api/refresh    rerun every stored analysis made from older data files
  POST /api/delete     {"config_name": ...} removes those stored runs

The page polls /api/jobs and refetches the results whenever the stamp changes (a run finished here, or `ihs-causal run`
stored results from a terminal), so every tab always shows everything stored.

Without config/paths.yaml (a new machine) the app starts on a setup page that asks for the data folder, so nothing has to
be typed in a terminal: the setup page, then *Run the standard analyses*, then the results.
"""
from __future__ import annotations

import copy
import gc
import json
import os
import queue
import re
import threading
import time
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional

from ihs_causal.check import check_files, report_json
from ihs_causal.config import defaults, expand
from ihs_causal.data.features import CONTEXT, TRAITS, is_baseline_column
from ihs_causal.paths import FILES, Paths, load_paths, plan_paths, write_paths_file
from ihs_causal.results import ResultStore
from ihs_causal.runner import pending_specs, run_specs, stale_specs, standard_specs
from ihs_causal.viewer.build import build_payload, render_html
from ihs_causal.workspace import Workspace

QUESTION_CONTRASTS = {"Q1": ["any_vs_none"], "Q2": ["strategy_vs_none"], "QT": ["type_vs_none"],
                      "Q3": ["data_vs_nodata", "data_within_strategy"], "Q45": ["domain_vs_none"]}
HETERO_ESTIMATOR = {"name": "drwcls_hetero", "learner": "ridge", "folds": 5, "min_person_rows": 10, "bootstrap": 400, "permutations": 2000}
CONTEXT_MODERATORS = [["Mood_pre", "Mood the day before"], ["log_steps_pre", "Steps the day before"],
                      ["sleep_minutes_pre", "Sleep the night before"], ["t", "Days into the study"]]
BASELINE_MODERATORS = [["Age", "Age"], ["Sex", "Sex"], ["depr0", "Depression history"], ["PHQtot0", "PHQ-9 at baseline"],
                       ["GADtot0", "GAD-7 at baseline"], ["Neu0_published", "Neuroticism"], ["SLE0", "Stressful life events"],
                       ["EFE0", "Early family environment"]]
WHO_DEFAULT_QUESTIONS = ["Q1", "Q45"]      # who responds with no question ticked: any message and the message domains


def _moderators(form: Dict, cohort: int, survey_columns) -> List[str]:
    """The moderators chosen in the form: ticked names plus any other baseline survey columns typed in. Typed names must
    be baseline survey columns with values (`survey_columns`, when known); the named traits are always accepted and are
    reported as skipped if the cohort has no values for them (2025 has no neuroticism score)."""
    ticked = form.get("moderators")
    if ticked is None:
        ticked = [m for m, _ in CONTEXT_MODERATORS + BASELINE_MODERATORS]
    if isinstance(ticked, str):
        ticked = [ticked]
    typed = [m for m in re.split(r"[,;\s]+", str(form.get("extra_moderators") or "")) if m]
    named = {m for m, _ in CONTEXT_MODERATORS + BASELINE_MODERATORS} | set(CONTEXT) | set(TRAITS)
    if survey_columns is not None:
        bad = [m for m in typed if m not in named and m not in survey_columns]
        if bad:
            follow_up = [m for m in bad if not is_baseline_column(m)]
            raise ValueError(f"not a baseline survey column with values in {cohort}: {', '.join(bad)}"
                             + (". Follow-up survey answers came after messages began, so they cannot moderate the effect." if follow_up else ""))
    order = [m for m, _ in CONTEXT_MODERATORS + BASELINE_MODERATORS]
    mods = [m for m in order if m in ticked] + [m for m in list(ticked) + typed if m not in order]
    return list(dict.fromkeys(mods))


def specs_from_form(form: Dict, survey_columns=None) -> List[Dict]:
    """The runs a Run-form submission asks for. Every run carries the form's label in its settings (`saved_as`), so two
    saved analyses with the same settings are stored apart and neither takes over the other's name."""
    d = defaults()
    label = (form.get("label") or "").strip() or time.strftime("run %Y-%m-%d %H:%M:%S")
    base = {"cohort": int(form.get("cohort", d["cohort"])), "device": form.get("device", d["device"]),
            "apple_source": form.get("apple_source", d["apple_source"]), "prob_scope": form.get("prob_scope", d["prob_scope"]),
            "label": label, "family": "", "saved_as": label}
    win = copy.deepcopy(d["window"])
    if form.get("window") == "fixed":
        win = {"name": "fixed", "post_start_h": 0, "post_end_h": int(form.get("fixed_hours", 24)), "pre_len_h": int(form.get("fixed_hours", 24)),
               "span_min": 0, "span_max": 10_000}
    else:
        win["span_min"] = float(form.get("span_min", win["span_min"]))
        win["span_max"] = float(form.get("span_max", win["span_max"]))
    base["window"] = win
    keep = copy.deepcopy(d["keep"])
    for k in keep:
        if k in form and form[k] not in ("", None):
            keep[k] = float(form[k]) if "." in str(form[k]) else int(form[k])
    base["keep"] = keep
    base["min_prob"] = float(form.get("min_prob") or d["min_prob"])
    base["min_arm_rows"] = int(float(form.get("min_arm_rows") or d["min_arm_rows"]))
    if not 0 <= base["min_prob"] < 0.5:
        raise ValueError("the probability floor must be at least 0 and below 0.5")
    for k in ("date_from", "date_to"):
        v = str(form.get(k) or "").strip()
        if v:
            try:
                time.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError(f"dates must look like 2025-12-01 (got {v!r})")
            base[k] = v
    if base.get("date_from") and base.get("date_to") and base["date_from"] > base["date_to"]:
        raise ValueError("the start date is after the end date")
    base["positivity"] = form.get("positivity") or d.get("positivity", "pairwise")
    if base["positivity"] not in ("joint", "pairwise"):
        raise ValueError("positivity must be 'joint' or 'pairwise'")
    base["estimator"] = {"name": form.get("estimator", "drwcls"), "learner": form.get("learner", "ridge"), "folds": int(form.get("folds", 5))}
    outcomes = form.get("outcomes") or ["mood", "steps", "sleep"]
    asked = list(form.get("questions") or [])
    who = bool(form.get("who")) or "Q6" in asked          # "Q6" in questions: older pages asked for who responds that way
    questions = [q for q in asked if q in QUESTION_CONTRASTS] or (WHO_DEFAULT_QUESTIONS if who else ["Q1"])
    contrasts = [c for q in questions for c in QUESTION_CONTRASTS[q]]
    specs: List[Dict] = expand({"name": label, "base": base, "sweep": {"outcome": outcomes, "contrast": contrasts}})
    if who:
        mods = _moderators(form, base["cohort"], survey_columns)
        if not mods:
            raise ValueError("tick at least one characteristic for Who responds")
        context = {m for m, _ in CONTEXT_MODERATORS} | set(CONTEXT)
        b6 = {**base, "estimator": {**HETERO_ESTIMATOR, "learner": base["estimator"]["learner"], "folds": base["estimator"]["folds"]},
              "moderator_sweep": mods, "baseline_traits": [m for m in mods if m not in context], "family": "q6-custom"}
        specs += expand({"name": label + " (Q6)", "base": b6, "sweep": {"outcome": outcomes, "contrast": contrasts}})
    return specs


class App:
    def __init__(self, paths: Optional[Paths], project_dir: Optional[Path] = None):
        """`paths` None: no data folder chosen yet on this machine; the page shows the setup page until one is."""
        self.project_dir = Path(project_dir) if project_dir else (paths.project_dir if paths else Path.cwd())
        self.paths: Optional[Paths] = None
        self.ws: Optional[Workspace] = None
        self.store: Optional[ResultStore] = None
        self._report: Optional[Dict] = None
        self.jobs: List[Dict] = []
        self.q: "queue.Queue[Dict]" = queue.Queue()
        self.lock = threading.Lock()            # the job list
        self.store_lock = threading.Lock()      # the results files: the worker writes and the page reads under it
        self._current: Dict = {}
        if paths is not None:
            self._activate(paths)
        threading.Thread(target=self._worker, daemon=True).start()

    def _activate(self, paths: Paths) -> None:
        self.ws = Workspace(paths, log=self._log)
        self.store = ResultStore(paths.results_dir)
        self._report = None
        self.paths = paths              # last, so a reader that sees paths also sees the workspace and store

    def _need_data(self) -> None:
        if self.paths is None:
            raise ValueError("choose the data folder first, on the setup page")

    def busy(self) -> bool:
        with self.lock:
            return any(j["status"] in ("queued", "running") for j in self.jobs)

    # ---------- the data folder ----------
    def cohort_report(self) -> Dict:
        """`ihs-causal check` on the data folder (column names only), kept until the folder changes."""
        if self._report is None and self.paths is not None:
            self._report = check_files(self.paths, hashes=False)
        return self._report or {}

    def suggest_folder(self) -> str:
        """A folder holding study files near the package, if any: a `data` folder of the repository it sits in
        (Rotation-1/data), or a folder above it (the package may sit inside the shared folder)."""
        names = {n for kinds in FILES.values() for n in kinds.values()}
        for up in [self.project_dir, *self.project_dir.parents][:6]:
            for cand in (up / "data", up):
                try:
                    if any((cand / n).exists() for n in names):
                        return str(cand)
                except OSError:
                    continue
        return ""

    def setup(self, data_root: str) -> Dict:
        """Check a data folder and, if at least one cohort can run from it, save it as this machine's data folder."""
        if self.busy():
            raise ValueError("wait for the running analyses to finish before changing the data folder")
        raw = str(data_root or "").strip().strip('"').strip("'").strip()
        if not raw:
            raise ValueError("paste the path of the folder that holds the study files")
        root = Path(raw).expanduser()
        if not root.is_dir():
            raise ValueError(f"there is no folder at {root}")
        paths, files, notes = plan_paths(self.project_dir, root)
        report = check_files(paths, hashes=False)
        ready = [c for c, r in report.items() if r["ready"]]
        out = {"saved": False, "ready": ready, "notes": notes, "data_root": str(paths.data_root),
               "report": report_json(report, paths.data_root)}
        if ready:
            target = write_paths_file(self.project_dir, paths.data_root, files)
            self._activate(load_paths(target))
            out["saved"] = True
        return out

    def setup_info(self) -> Dict:
        info = {"needed": self.paths is None, "data_root": str(self.paths.data_root) if self.paths else ""}
        if self.paths is None:
            info["suggestion"] = self.suggest_folder()
        return info

    # ---------- the standing analyses (config/pipeline.yaml) ----------
    def _plan(self) -> Dict:
        return standard_specs(self.project_dir / "config" / "pipeline.yaml")

    def standard_status(self) -> Dict:
        """For each cohort: how many standing analyses are stored (or had nothing to estimate), and whether its files
        are complete in the data folder."""
        if self.paths is None:
            return {}
        try:
            plan = self._plan()
        except (OSError, ValueError) as e:
            return {"error": str(e)}
        stored = self.store.run_ids() | set(self.store.empty_runs())
        rep = self.cohort_report()
        return {str(c): {"total": len(specs), "stored": sum(s["run_id"] in stored for s in specs),
                         "ready": bool(rep.get(c, {}).get("ready")), "status": rep.get(c, {}).get("status", "files not checked")}
                for c, (_files, specs) in plan.items()}

    def run_standard(self) -> Dict:
        """One job per cohort whose files are complete; each runs only the analyses not yet stored from these files."""
        self._need_data()
        rep = self.cohort_report()
        with self.lock:
            active = {j["cohort"] for j in self.jobs if j["kind"] == "standard" and j["status"] in ("queued", "running")}
        jobs = [self._enqueue(specs, f"Standard analyses, {c}", kind="standard")
                for c, (_files, specs) in self._plan().items() if rep.get(c, {}).get("ready") and c not in active]
        if not jobs:
            return {"error": "Nothing to start: the standard analyses are already queued, or no cohort's files are "
                             "complete in the data folder (the About tab shows the folder)."}
        return {"jobs": jobs}

    def _log(self, msg: str) -> None:
        job = self._current
        if job:
            with self.lock:
                job["log"].append(msg)
        print(msg, flush=True)

    def survey_columns(self, cohort: int):
        if self.ws is None:
            return None
        try:
            return {c["name"] for c in self.ws.survey_catalog(cohort)}
        except FileNotFoundError:        # no survey file on this machine: typed names are not checked
            return None

    def submit(self, form: Dict) -> Dict:
        self._need_data()
        cohort = int(form.get("cohort", defaults()["cohort"]))
        specs = specs_from_form(form, self.survey_columns(cohort))
        return self._enqueue(specs, specs[0]["label"] if specs else "")

    def refresh(self) -> Dict:
        """Queue every stored analysis made from older data files, with its own settings."""
        self._need_data()
        specs = stale_specs(self.ws)
        if not specs:
            return {"error": "Every stored analysis already uses the current data files."}
        return self._enqueue(specs, "Rerun on the current data files", kind="refresh")

    def _enqueue(self, specs: List[Dict], label: str, kind: str = "run") -> Dict:
        s0 = specs[0] if specs else {}
        job = {"id": len(self.jobs) + 1, "label": label, "kind": kind, "config_names": sorted({s["config_name"] for s in specs}),
               "run_ids": sorted({s["run_id"] for s in specs}), "who": any(s.get("family") == "q6-custom" for s in specs),
               "cohort": s0.get("cohort"), "device": s0.get("device"), "apple_source": s0.get("apple_source"),
               "status": "queued", "runs": len(specs), "stored": 0, "log": [], "submitted": time.strftime("%H:%M:%S"), "seconds": None}
        with self.lock:
            self.jobs.append(job)
        self.q.put({"job": job, "specs": specs})
        return job

    def _worker(self) -> None:
        while True:
            item = self.q.get()
            job = item["job"]
            self._current = job
            job["status"] = "running"
            t0 = time.perf_counter()

            def stored(_rid, job=job):
                job["stored"] += 1
            try:
                specs = item["specs"]
                if job["kind"] == "standard":
                    # a fresh workspace frees the previous cohort's tables; then only what is not stored yet
                    self.ws = Workspace(self.paths, log=self._log)
                    gc.collect()
                    self._log("Checking which standard analyses are already stored (the first time, this fingerprints the data files)...")
                    specs = pending_specs(specs, self.ws)
                    job["runs"], job["run_ids"] = len(specs), sorted({s["run_id"] for s in specs})
                    self._log(f"{len(specs)} to run." if specs else "All of them are already stored from these data files.")
                run_specs(specs, self.ws, force=True, log=self._log, lock=self.store_lock, on_stored=stored)
                job["status"] = "done"
            except Exception as e:      # report the error in the job, keep the server alive
                job["status"] = "failed"
                job["log"].append(f"{type(e).__name__}: {e}")
                job["log"].append(traceback.format_exc(limit=3))
            job["seconds"] = round(time.perf_counter() - t0, 1)
            self._current = {}

    def date_ranges(self) -> Dict:
        out = {}
        if self.ws is None:
            return out
        for c in (2025, 2024):
            try:
                out[str(c)] = self.ws.date_range(c)
            except Exception:       # a cohort's files may be missing on another machine
                out[str(c)] = None
        return out

    def moderator_catalog(self) -> Dict:
        """Choices for Who responds: the named characteristics, and every baseline survey column with values, with the
        share of each cohort's survey respondents who answered (names and shares only)."""
        survey = {}
        for c in (2025, 2024):
            try:
                survey[str(c)] = self.ws.survey_catalog(c) if self.ws is not None else []
            except FileNotFoundError:
                survey[str(c)] = []
        return {"context": CONTEXT_MODERATORS, "baseline": BASELINE_MODERATORS, "survey": survey}

    def payload(self) -> Dict:
        if self.paths is None:          # setup page: no results to read yet
            p = build_payload(None, self.project_dir, mode="serve")
        else:
            current = self.ws.current_inputs()
            with self.store_lock:
                p = build_payload(self.paths.results_dir, self.paths.project_dir, mode="serve", current=current)
        p["date_ranges"] = self.date_ranges()
        p["moderator_catalog"] = self.moderator_catalog()
        p["setup"] = self.setup_info()
        p["standard"] = self.standard_status()
        return p

    def jobs_state(self) -> Dict:
        with self.lock:
            jobs = [{k: (v[-40:] if k == "log" else v) for k, v in j.items()} for j in self.jobs[::-1]]
        return {"jobs": jobs, "stamp": self.store.stamp() if self.store is not None else "none"}

    def options(self) -> Dict:
        d = defaults()
        return {"defaults": {"cohort": d["cohort"], "device": d["device"], "apple_source": d["apple_source"], "prob_scope": d["prob_scope"],
                             "min_prob": d["min_prob"], "min_arm_rows": d["min_arm_rows"], "positivity": d.get("positivity", "pairwise"),
                             "window": d["window"], "keep": d["keep"], "estimator": d["estimator"]},
                "cohorts": [2025, 2024], "devices": ["combined", "apple", "garmin", "fitbit"],
                "questions": [["Q1", "Any message"], ["Q45", "Message domains (own and cross)"], ["Q2", "Strategies"], ["QT", "Message types (strategy and own data)"], ["Q3", "Showing own data"]],
                "who_responds": "who: true adds moderation and person-level variation for every chosen question",
                "moderators": self.moderator_catalog(), "estimators": ["drwcls", "wcls"], "learners": ["ridge", "mean"]}


def make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # keep the console quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code: int = 200) -> None:
            self._send(code, json.dumps(obj, default=str).encode("utf-8"), "application/json")

        def do_GET(self):
            try:
                if self.path in ("/", "/index.html"):
                    html = render_html(app.payload())
                    return self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
                if self.path == "/api/payload":
                    return self._json(app.payload())
                if self.path == "/api/options":
                    return self._json(app.options())
                if self.path == "/api/jobs":
                    return self._json(app.jobs_state())
            except Exception as e:      # e.g. a results file being replaced; the page retries
                traceback.print_exc()
                return self._json({"error": f"{type(e).__name__}: {e}"}, 503)
            self._send(404, b"not found", "text/plain")

        def do_POST(self):
            if self.headers.get("Origin") not in (None, f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"):
                return self._send(403, b"forbidden", "text/plain")
            n = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(n) or b"{}")
            except json.JSONDecodeError:
                return self._send(400, b"bad json", "text/plain")
            if self.path == "/api/setup":
                try:
                    return self._json(app.setup(body.get("data_root", "")))
                except ValueError as e:
                    return self._json({"error": str(e)}, 400)
                except Exception as e:
                    return self._json({"error": f"{type(e).__name__}: {e}"}, 400)
            if self.path == "/api/standard":
                try:
                    return self._json(app.run_standard())
                except Exception as e:
                    return self._json({"error": f"{type(e).__name__}: {e}"}, 400)
            if self.path == "/api/run":
                try:
                    return self._json(app.submit(body))
                except Exception as e:
                    return self._json({"error": f"{type(e).__name__}: {e}"}, 400)
            if self.path == "/api/refresh":
                try:
                    return self._json(app.refresh())
                except Exception as e:
                    return self._json({"error": f"{type(e).__name__}: {e}"}, 400)
            if self.path == "/api/delete":
                if app.store is None:
                    return self._json({"removed": 0})
                with app.store_lock:
                    n_removed = app.store.prune(body.get("config_name", ""), set())
                return self._json({"removed": n_removed})
            self._send(404, b"not found", "text/plain")
    return Handler


class _Server(ThreadingHTTPServer):
    allow_reuse_address = os.name != "nt"       # on Windows, SO_REUSEADDR would let a second app share the port


def app_answers(url: str) -> bool:
    """Whether an ihs-causal app already answers at `url` (so starting it twice opens the running one)."""
    import urllib.request
    try:
        with urllib.request.urlopen(url + "api/jobs", timeout=2) as r:
            return "jobs" in json.loads(r.read().decode("utf-8"))
    except Exception:       # nothing listening, or something else
        return False


def serve(paths: Optional[Paths], project_dir: Optional[Path] = None, port: int = 8766, open_browser: bool = True) -> int:
    url = f"http://127.0.0.1:{port}/"
    if app_answers(url):
        print(f"ihs-causal is already running at {url}; opening it in the browser.", flush=True)
        if open_browser:
            webbrowser.open(url)
        return 0
    app = App(paths, project_dir)
    try:
        server = _Server(("127.0.0.1", port), make_handler(app))
    except OSError as e:
        print(f"Port {port} is in use by another program ({e}). Start with --port 8770, or another number.", flush=True)
        return 1
    where = f"results in {paths.results_dir}" if paths else "first start on this computer: choose the data folder in the browser"
    print(f"ihs-causal is running at {url} ({where}). Keep this window open while you use it; close it or press "
          f"Ctrl+C to stop.", flush=True)
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
