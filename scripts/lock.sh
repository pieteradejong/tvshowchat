#!/usr/bin/env bash
# Regenerate the hash-pinned lockfiles from pyproject.toml and requirements-dev.in.
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
        --emit-index-url \
        --quiet \
        ${upgrade[@]+"${upgrade[@]}"}
}

compile pyproject.toml requirements.txt
# pip needs to know where torch's +cpu wheels live. Safe as an extra index
# only because every install is --require-hashes: a candidate from either
# index whose hash isn't in this file is discarded.
sed -i.bak 's#^--index-url https://pypi.org/simple$#&\
--extra-index-url https://download.pytorch.org/whl/cpu#' requirements.txt
rm -f requirements.txt.bak
compile requirements-dev.in requirements-dev.txt
echo "Locked: requirements.txt ($(grep -c '==' requirements.txt) packages)," \
     "requirements-dev.txt ($(grep -c '==' requirements-dev.txt) packages)"
