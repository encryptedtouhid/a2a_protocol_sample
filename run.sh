#!/usr/bin/env bash
# A2A Protocol Sample — one-stop shell helper.
#
# Works on Linux, macOS, and Windows (Git Bash or WSL). Handles venv creation,
# dependency install, and launching the server / webhook / demo scripts.
#
# Usage:
#   ./run.sh setup            Create .venv and install requirements
#   ./run.sh server           Run the A2A sample server on :8000
#   ./run.sh webhook          Run the push-notification webhook on :9000
#   ./run.sh demo <name|idx>  Run a demo script (e.g. 01 or 01_discovery)
#   ./run.sh list             List available demos
#   ./run.sh clean            Delete the .venv
#   ./run.sh help             Show this help

set -euo pipefail

# -- locate this script so relative paths always work ------------------------
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

VENV_DIR="${VENV_DIR:-.venv}"

# -- cross-platform venv paths ----------------------------------------------
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)  # Git Bash / Cygwin on Windows
    VENV_BIN="$VENV_DIR/Scripts"
    VENV_PY="$VENV_BIN/python.exe"
    ;;
  *)
    VENV_BIN="$VENV_DIR/bin"
    VENV_PY="$VENV_BIN/python"
    ;;
esac

# -- pick a bootstrap python to create the venv -----------------------------
pick_bootstrap_python() {
  for candidate in python3 python py; do
    if command -v "$candidate" >/dev/null 2>&1; then
      # "py" on Windows wants the -3 flag
      if [ "$candidate" = "py" ]; then
        echo "py -3"
      else
        echo "$candidate"
      fi
      return 0
    fi
  done
  echo "error: no python interpreter found on PATH (tried python3, python, py)" >&2
  return 1
}

cmd_setup() {
  if [ ! -x "$VENV_PY" ]; then
    local boot
    boot="$(pick_bootstrap_python)"
    echo ">> creating venv at $VENV_DIR using '$boot'"
    # shellcheck disable=SC2086
    $boot -m venv "$VENV_DIR"
  else
    echo ">> venv already exists at $VENV_DIR"
  fi
  echo ">> upgrading pip"
  "$VENV_PY" -m pip install --disable-pip-version-check --upgrade pip >/dev/null
  echo ">> installing requirements"
  "$VENV_PY" -m pip install --disable-pip-version-check -r requirements.txt
  echo ">> done."
}

ensure_venv() {
  if [ ! -x "$VENV_PY" ]; then
    echo "venv missing — run: ./run.sh setup" >&2
    exit 1
  fi
}

cmd_server() {
  ensure_venv
  exec "$VENV_PY" demos/run_server.py
}

cmd_webhook() {
  ensure_venv
  exec "$VENV_PY" demos/webhook_receiver.py
}

cmd_list() {
  echo "available demos:"
  # shellcheck disable=SC2012
  ls demos/ | grep -E '^[0-9]{2}_.*\.py$' | sed 's/^/  /'
}

cmd_demo() {
  ensure_venv
  local arg="${1:-}"
  if [ -z "$arg" ]; then
    echo "usage: ./run.sh demo <name|idx>" >&2
    cmd_list
    exit 2
  fi

  local match
  match="$(ls demos/ | grep -E "^${arg}(_.*)?\.py$" || true)"
  if [ -z "$match" ]; then
    echo "no demo matches '$arg'" >&2
    cmd_list
    exit 1
  fi
  if [ "$(echo "$match" | wc -l | tr -d ' ')" -gt 1 ]; then
    echo "multiple demos match '$arg':" >&2
    echo "$match" >&2
    exit 1
  fi
  echo ">> running demos/$match"
  exec "$VENV_PY" "demos/$match"
}

cmd_clean() {
  if [ -d "$VENV_DIR" ]; then
    echo ">> removing $VENV_DIR"
    rm -rf "$VENV_DIR"
  fi
}

cmd_help() {
  # Print the header block (lines starting with "# " until the first blank line).
  awk '
    NR == 1 { next }                 # skip shebang
    /^$/    { exit }                 # stop at first blank line
    /^# ?/  { sub(/^# ?/, ""); print }
  ' "$0"
}

main() {
  local sub="${1:-help}"
  shift || true
  case "$sub" in
    setup)   cmd_setup   "$@" ;;
    server)  cmd_server  "$@" ;;
    webhook) cmd_webhook "$@" ;;
    demo)    cmd_demo    "$@" ;;
    list)    cmd_list    "$@" ;;
    clean)   cmd_clean   "$@" ;;
    help|-h|--help) cmd_help ;;
    *)
      echo "unknown command: $sub" >&2
      cmd_help
      exit 2
      ;;
  esac
}

main "$@"
