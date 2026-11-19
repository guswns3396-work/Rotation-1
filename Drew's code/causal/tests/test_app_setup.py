"""The app on a new computer: it starts without a data folder, the setup page saves one, and *Run the standard
analyses* fills the results, with no terminal commands. Fake files only."""
import json
import threading
import time
import urllib.request

import pytest

from fake_shared_files import SMALL_PIPELINE, make_project, write_shared_files
from ihs_causal.serve import App, _Server, app_answers, make_handler


@pytest.fixture()
def fresh(tmp_path, monkeypatch):
    proj, shared = make_project(tmp_path), write_shared_files(tmp_path / "shared")
    (proj / "config" / "pipeline.yaml").write_text(SMALL_PIPELINE, encoding="utf-8")     # the small standing set
    monkeypatch.chdir(proj)
    return proj, shared


def _wait(app, seconds=180):
    t0 = time.time()
    while app.busy():
        assert time.time() - t0 < seconds, "jobs did not finish"
        time.sleep(0.2)


def test_first_start_setup_page_then_standard_analyses(fresh):
    proj, shared = fresh
    app = App(None, proj)
    p = app.payload()
    assert p["setup"]["needed"] and p["estimates"] == [] and p["standard"] == {}
    assert app.jobs_state()["stamp"] == p["results_stamp"]            # the page does not reload while setup is open
    with pytest.raises(ValueError, match="data folder"):
        app.submit({"cohort": 2025})
    with pytest.raises(ValueError, match="no folder"):
        app.setup(str(shared / "missing"))
    bad = app.setup(str(proj))                                        # a folder without study files is not saved
    assert not bad["saved"] and bad["ready"] == [] and not (proj / "config" / "paths.yaml").exists()
    res = app.setup(f'"{shared}"')                                    # pasted with quotes, as Windows' Copy as path gives
    assert res["saved"] and sorted(res["ready"]) == [2024, 2025]
    assert any("is not in this folder" in n for n in res["notes"])
    assert (proj / "config" / "paths.yaml").exists() and app.paths is not None
    assert json.dumps(res).count("FAKE20") == 0                      # file names and states only
    p = app.payload()
    assert not p["setup"]["needed"] and p["setup"]["data_root"]
    assert p["standard"] == {"2025": {"total": 9, "stored": 0, "ready": True, "status": p["standard"]["2025"]["status"]},
                             "2024": {"total": 2, "stored": 0, "ready": True, "status": p["standard"]["2024"]["status"]}}
    jobs = app.run_standard()["jobs"]
    assert [j["label"] for j in jobs] == ["Standard analyses, 2025", "Standard analyses, 2024"]
    assert "error" in app.run_standard()                              # already queued: not queued twice
    _wait(app)
    assert [j["status"] for j in app.jobs] == ["done", "done"]
    st = app.payload()["standard"]
    assert st["2025"]["stored"] == 9 and st["2024"]["stored"] == 2  # the empty 2024 message-type run counts as done
    again = app.run_standard()["jobs"]                                # nothing left: the jobs finish at once
    _wait(app)
    assert all(j["runs"] == 0 and j["status"] == "done" for j in again)


def test_setup_page_suggests_the_repository_data_folder(tmp_path):
    repo = tmp_path / "Rotation-1"
    proj = make_project(repo / "Drew's code")              # the package inside the repository, as in Jack's repo
    assert App(None, proj).suggest_folder() == ""           # an empty data folder is not suggested
    write_shared_files(repo / "data", n_people=3, n_days=7)
    assert App(None, proj).suggest_folder() == str(repo / "data")


def test_http_routes_and_second_start(fresh):
    proj, shared = fresh
    app = App(None, proj)
    server = _Server(("127.0.0.1", 0), make_handler(app))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}/"
    try:
        html = urllib.request.urlopen(url, timeout=10).read().decode("utf-8")
        assert "Where are the study files?" in html or '"needed":true' in html
        assert app_answers(url)                                       # a second start opens this one instead
        req = urllib.request.Request(url + "api/setup", data=json.dumps({"data_root": str(shared)}).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        res = json.loads(urllib.request.urlopen(req, timeout=30).read())
        assert res["saved"]
        payload = json.loads(urllib.request.urlopen(url + "api/payload", timeout=30).read())
        assert payload["setup"]["needed"] is False and set(payload["standard"]) == {"2025", "2024"}
    finally:
        server.shutdown()
        server.server_close()
    assert not app_answers(url)
