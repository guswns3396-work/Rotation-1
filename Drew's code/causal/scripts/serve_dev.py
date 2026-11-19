"""Start the results app from a source checkout without installing the package.

    python scripts/serve_dev.py

Works from any folder, with any Python that has numpy, pandas, pyarrow and pyyaml. Extra arguments are passed on, e.g.
--port 8770 or --no-browser.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from ihs_causal.cli import main  # noqa: E402

sys.exit(main(["serve"] + sys.argv[1:]))
