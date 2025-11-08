#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_SCRIPT="$ROOT_DIR/scripts/scrape_episodes.py"
CONTENT_FILE="$ROOT_DIR/app/content/btvs_all_seasons.json"
SEASON_RANGE=(1 2 3 4 5 6 7)

PYTHON_BIN="$ROOT_DIR/venv/bin/python"
if [[ ! -x "$PYTHON_BIN" ]]; then
    if command -v python3.12 >/dev/null 2>&1; then
        PYTHON_BIN="$(command -v python3.12)"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="$(command -v python3)"
    else
        echo "Python 3 interpreter not found. Install python3.12 or create the project virtualenv." >&2
        exit 1
    fi
fi

usage() {
    cat <<EOF
Usage: $(basename "$0") [--all] [--season N ...] [--force]

Options:
  --all          Crawl all seasons (overrides --season)
  --season N...  Crawl specific season numbers (space-separated list)
  --force        Re-crawl even if data already exists
  --help         Show this help text

Without --all or --season, the script crawls only seasons missing from btvs_all_seasons.json.
EOF
}

ALL=false
FORCE=false
SEASON_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --all)
            ALL=true
            shift
            ;;
        --season)
            shift
            if [[ $# -eq 0 ]]; then
                echo "Expected one or more season numbers after --season" >&2
                exit 1
            fi
            while [[ $# -gt 0 && "$1" != --* ]]; do
                SEASON_ARGS+=("$1")
                shift
            done
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage
            exit 1
            ;;
    esac
done

if [[ "$ALL" == true && ${#SEASON_ARGS[@]} -gt 0 ]]; then
    echo "Cannot use --all with --season." >&2
    exit 1
fi

CMD_ARGS=()

if [[ "$ALL" == true ]]; then
    CMD_ARGS=(--all)
elif [[ ${#SEASON_ARGS[@]} -gt 0 ]]; then
    CMD_ARGS=(--season "${SEASON_ARGS[@]}")
else
    if [[ "$FORCE" == true ]]; then
        echo "Force flag provided without specific seasons; crawling all seasons."
        CMD_ARGS=(--all)
    else
        existing_seasons=$(
            CONTENT_FILE="$CONTENT_FILE" "$PYTHON_BIN" <<'PY'
import json
import os
from pathlib import Path

content_path = Path(os.environ["CONTENT_FILE"])
if not content_path.exists():
    print("", end="")
    raise SystemExit

with content_path.open("r", encoding="utf-8") as fh:
    data = json.load(fh)

seasons = []
for key, value in data.items():
    if not key.startswith("season_"):
        continue
    try:
        seasons.append(int(key.split("_")[1]))
    except (IndexError, ValueError):
        continue

print(",".join(str(s) for s in sorted(set(seasons))), end="")
PY
        )

        missing=$(
            EXISTING="$existing_seasons" "$PYTHON_BIN" <<'PY'
import os

existing = set()
raw = os.environ.get("EXISTING", "")
if raw:
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            existing.add(int(part))

missing = [str(s) for s in range(1, 8) if s not in existing]
print(" ".join(missing), end="")
PY
        )

        read -r -a missing_array <<< "$missing"

        if [[ ${#missing_array[@]} -eq 0 ]]; then
            rel_path="${CONTENT_FILE#$ROOT_DIR/}"
            echo "All seasons already present in ${rel_path}. Nothing to crawl."
            exit 0
        fi

        echo "Missing seasons detected: ${missing_array[*]}"
        CMD_ARGS=(--season "${missing_array[@]}")
    fi
fi

if [[ "$FORCE" == true ]]; then
    CMD_ARGS+=(--force)
fi

rel_script="${PYTHON_SCRIPT#$ROOT_DIR/}"
echo "Running: $rel_script ${CMD_ARGS[*]}"
"$PYTHON_BIN" "$PYTHON_SCRIPT" "${CMD_ARGS[@]}"

