#!/usr/bin/env bash
# Regenerate the hash-pinned lockfiles from requirements*.in.
# Every package (direct and transitive) gets an exact version and its sha256
# hashes, so `pip install --require-hashes` refuses anything that was swapped.
#
#   ./scripts/lock.sh            keep existing transitive pins where still valid
#   ./scripts/lock.sh --upgrade  re-resolve every transitive package to its latest
set -euo pipefail
cd "$(dirname "$0")/.."

upgrade=()
if [ "${1:-}" = "--upgrade" ]; then
    upgrade=(--upgrade)
fi

compile() {
    uv pip compile "$1" \
        --output-file "$2" \
        --generate-hashes \
        --universal \
        --python-version 3.12 \
        --index-url https://pypi.org/simple \
        --no-header \
        --quiet \
        ${upgrade[@]+"${upgrade[@]}"}
}

compile requirements.in requirements.txt
compile requirements-dev.in requirements-dev.txt
echo "Locked: requirements.txt ($(grep -c '==' requirements.txt) packages)," \
     "requirements-dev.txt ($(grep -c '==' requirements-dev.txt) packages)"
