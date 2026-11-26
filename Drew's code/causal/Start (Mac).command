#!/bin/bash
# Double-click to start the IHS causal app (macOS; on Linux run `bash "Start (Mac).command"`). The first start sets up a
# private Python environment in the .venv folder (a few minutes; needs the internet). Later starts take seconds.
# Close this window, or press Ctrl+C in it, to stop the app.
cd "$(dirname "$0")" || exit 1
VPY=".venv/bin/python"
PIPOPTS="--disable-pip-version-check"

finish() { echo; read -r -p "Press Return to close this window. " _; exit "${1:-0}"; }
fail() {
  echo
  echo "Setup did not finish (see the messages above). Check the internet connection, delete the .venv folder, and"
  echo "start this again. If it fails again, send the messages above to Drew."
  finish 1
}
# a Python 3.9 or later with venv; skips the macOS placeholder that only offers to install the developer tools
usable() {
  local p
  p=$(command -v "$1" 2>/dev/null) || return 1
  if [ "$p" = "/usr/bin/python3" ] && ! xcode-select -p >/dev/null 2>&1; then return 1; fi
  "$p" -c 'import sys, venv; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1
}

if [ -x "$VPY" ] && ! "$VPY" -c 'import numpy, pandas, pyarrow, yaml' >/dev/null 2>&1; then
  echo "The Python environment in .venv is incomplete or was moved; setting it up again."
  rm -rf .venv
fi

if [ ! -x "$VPY" ]; then
  BASE=""
  for c in python3.12 python3.11 python3.13 python3.10 python3.9 python3.14 python3 /opt/homebrew/bin/python3 \
           /usr/local/bin/python3 "$HOME/miniforge3/bin/python3" "$HOME/miniconda3/bin/python3" "$HOME/anaconda3/bin/python3" \
           /opt/miniconda3/bin/python3 /opt/anaconda3/bin/python3; do
    if usable "$c"; then BASE=$(command -v "$c"); break; fi
  done
  if [ -n "$BASE" ]; then
    echo "Setting up a private Python environment in .venv (first start only; a few minutes, needs the internet)..."
    "$BASE" -m venv .venv || fail
  else
    # no Python: use uv (it fetches its own Python), installing it first if the user agrees
    UV=$(command -v uv 2>/dev/null)
    [ -z "$UV" ] && [ -x "$HOME/.local/bin/uv" ] && UV="$HOME/.local/bin/uv"
    [ -z "$UV" ] && [ -x "$HOME/.cargo/bin/uv" ] && UV="$HOME/.cargo/bin/uv"
    if [ -z "$UV" ]; then
      echo "Python 3.9 or later was not found on this computer."
      echo "The app can set up its own Python with uv, a small installer from astral.sh. No administrator rights needed."
      read -r -p "Install uv now? [Y/n] " answer
      case "$answer" in
        [nN]*) echo "Install Python from https://www.python.org/downloads/, then start this again."
               open "https://www.python.org/downloads/" 2>/dev/null; finish 1 ;;
      esac
      curl -LsSf https://astral.sh/uv/install.sh | sh || fail
      UV="$HOME/.local/bin/uv"; [ -x "$UV" ] || UV="$HOME/.cargo/bin/uv"; [ -x "$UV" ] || fail
    fi
    echo "Setting up Python with uv (first start only; a few minutes, needs the internet)..."
    "$UV" venv --seed --python 3.12 .venv || fail
  fi
  echo "Installing numpy, pandas, pyarrow and pyyaml..."
  "$VPY" -m pip install $PIPOPTS -r requirements.txt || fail
  cp requirements.txt .venv/installed-requirements.txt
fi

if ! cmp -s requirements.txt .venv/installed-requirements.txt; then
  echo "The requirements changed; updating .venv..."
  "$VPY" -m pip install $PIPOPTS -r requirements.txt || fail
  cp requirements.txt .venv/installed-requirements.txt
fi
# the package itself is read from src/ in this folder, so updates to the code take effect at the next start
"$VPY" -c "import sysconfig, pathlib; pathlib.Path(sysconfig.get_paths()['purelib'], 'ihs_causal_src.pth').write_text(str(pathlib.Path('src').resolve()) + '\n')" || fail

echo "Starting the app; it opens in your browser. Keep this window open while you use it."
"$VPY" -m ihs_causal.cli serve "$@" || finish 1
