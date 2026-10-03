#!/usr/bin/env bash
# Check functions are invoked indirectly, through `check <name> <function>`.
# shellcheck disable=SC2329
#
# Every check CI runs, runnable locally. CI calls one section per job; run
# with no arguments to run them all.
#
#   ./scripts/check.sh                    all sections (docker build only if a daemon is up)
#   ./scripts/check.sh python lockfiles   just those sections
#   ./scripts/check.sh docker --build     build the image and smoke-test it
#   ./scripts/check.sh install-actionlint fetch the pinned, checksum-verified actionlint
#
# Sections: python lockfiles frontend workflows docker secrets
# A failing check doesn't stop the run; the summary lists every result and
# the exit code is non-zero if any check failed.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 2
ROOT=$(pwd)

PY="$ROOT/venv/bin"
TOOLS="$ROOT/.tools/bin"
IMAGE="tvshowchat-api:check"
HADOLINT_IMAGE="hadolint/hadolint:v2.15.1@sha256:32dac94127fd60b7b7e3fbfc65e1383b9b5e25c9bfd7b8536de7a539fe68a12d"
ACTIONLINT_VERSION="1.7.12"
# Read via indirect expansion in install_actionlint.
# shellcheck disable=SC2034
ACTIONLINT_SHA256_linux_amd64="8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"
# shellcheck disable=SC2034
ACTIONLINT_SHA256_darwin_arm64="aba9ced2dee8d27fecca3dc7feb1a7f9a52caefa1eb46f3271ea66b6e0e6953f"

if [ -t 1 ]; then RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; BOLD=$'\033[1m'; RESET=$'\033[0m'
else RED=; GREEN=; YELLOW=; BOLD=; RESET=; fi

RESULTS=()
FAILED=0
LOG=$(mktemp -t tvshowchat-check.XXXXXX)
trap 'rm -f "$LOG"' EXIT

section() { printf '\n%s== %s ==%s\n' "$BOLD" "$1" "$RESET"; }

# check <name> <command...>: run quietly; on failure show the last of its output.
check() {
    local name=$1; shift
    if "$@" >"$LOG" 2>&1; then
        printf '  %sPASS%s  %s\n' "$GREEN" "$RESET" "$name"
        RESULTS+=("PASS  $name")
    else
        printf '  %sFAIL%s  %s\n' "$RED" "$RESET" "$name"
        tail -n 25 "$LOG" | sed 's/^/        /'
        RESULTS+=("FAIL  $name")
        FAILED=1
        return 1
    fi
}

skip() {
    printf '  %sSKIP%s  %s (%s)\n' "$YELLOW" "$RESET" "$1" "$2"
    RESULTS+=("SKIP  $1 ($2)")
}

need() { command -v "$1" >/dev/null 2>&1; }

# ---------------------------------------------------------------------------
# python: lint, tests, vulnerability audit
# ---------------------------------------------------------------------------
python_venv_exists() { [ -x "$PY/python" ] || { echo "no venv: run ./init.sh"; return 1; }; }
python_version_is_312() { "$PY/python" -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version'; }
python_no_chromadb() { ! "$PY/python" -c 'import chromadb' 2>/dev/null; }
pip_audit() {
    # --strict: a package that can't be audited fails the check rather than
    # being silently skipped. PyTorch's local "+cpu" builds aren't on PyPI, so
    # they're audited as the upstream release they're built from (advisories
    # are filed against that). Hashes don't apply to the renamed pins, so this
    # runs --no-deps; the lock is already fully pinned.
    local tmp rc
    tmp=$(mktemp)
    sed -E 's/^(torch==[0-9.]+)\+cpu/\1/' "$1" > "$tmp"
    "$PY/pip-audit" --strict --no-deps --disable-pip --progress-spinner off -r "$tmp"; rc=$?
    rm -f "$tmp"
    return "$rc"
}

section_python() {
    section python
    check "venv exists" python_venv_exists || return
    check "venv is Python 3.12" python_version_is_312
    check "installed packages are consistent (pip check)" "$PY/pip" check
    check "ChromaDB is not installed" python_no_chromadb
    check "ruff (pyflakes, bugbear, bandit)" "$PY/ruff" check .
    check "pytest unit tests" "$PY/pytest" -q tests/unit
    check "pytest integration tests (API, rankings, model)" "$PY/pytest" -q tests/integration
    check "pip-audit runtime lock" pip_audit requirements.txt
    check "pip-audit dev lock" pip_audit requirements-dev.txt
}

# ---------------------------------------------------------------------------
# lockfiles: everything pinned, hashed, and in sync with its input
# ---------------------------------------------------------------------------
pyproject_pins_exact() {
    "$PY/python" - <<'EOF'
import re, sys, tomllib
deps = tomllib.load(open("pyproject.toml", "rb"))["project"]["dependencies"]
bad = [d for d in deps if not re.fullmatch(r"[A-Za-z0-9_.\-\[\]]+==[^=<>~!*,; ]+", d)]
dev = [l.strip() for l in open("requirements-dev.in") if l.strip() and not l.startswith(("#", "-c"))]
bad += [d for d in dev if "==" not in d or re.search(r"[<>~!*]", d)]
print("\n".join(bad)); sys.exit(1 if bad else 0)
EOF
}

every_locked_package_has_hashes() {
    local f
    for f in requirements.txt requirements-dev.txt; do
        awk -v f="$f" '
            /^[A-Za-z0-9]/ { if (pkg != "" && !hashed) { print f ": no hash for " pkg; bad=1 } pkg=$1; hashed=0; next }
            /--hash=sha256:/ { hashed=1 }
            END { if (pkg != "" && !hashed) { print f ": no hash for " pkg; bad=1 } exit bad }
        ' "$f" || return 1
    done
}

only_known_indexes() {
    local unexpected
    unexpected=$(grep -hE '^--(extra-)?index-url' requirements.txt requirements-dev.txt \
        | grep -vxE -e '--index-url https://pypi.org/simple' -e '--extra-index-url https://download.pytorch.org/whl/cpu')
    [ -z "$unexpected" ] || { echo "unexpected index: $unexpected"; return 1; }
}

dev_lock_has_no_index_lines() {
    # pip resets its index list at each --index-url; one here would drop the
    # PyTorch index set by requirements.txt when both are installed together.
    ! grep -nE '^--(extra-)?index-url' requirements-dev.txt
}

no_cuda_packages() {
    ! grep -nE '^(nvidia-|triton==|cuda-)' requirements.txt
}

python_locks_are_fresh() {
    # Re-lock into a scratch copy and compare: catches an edited pyproject.toml
    # or requirements-dev.in that nobody re-locked.
    local tmp
    tmp=$(mktemp -d)
    cp pyproject.toml requirements-dev.in requirements.txt requirements-dev.txt "$tmp"/
    mkdir -p "$tmp/scripts" && cp scripts/lock.sh "$tmp/scripts/"
    PATH="$PY:$PATH" "$tmp/scripts/lock.sh" >/dev/null || { rm -rf "$tmp"; return 1; }
    local rc=0
    diff -u requirements.txt "$tmp/requirements.txt" || rc=1
    diff -u requirements-dev.txt "$tmp/requirements-dev.txt" || rc=1
    rm -rf "$tmp"
    return "$rc"
}

npm_pins_exact() {
    node -e '
        const p = require("./frontend/package.json");
        const bad = Object.entries({...p.dependencies, ...p.devDependencies})
            .filter(([, v]) => !/^\d+\.\d+\.\d+$/.test(v)).map(([k, v]) => k + "@" + v);
        if (bad.length) { console.log(bad.join("\n")); process.exit(1); }'
}

npm_lock_integrity() {
    node -e '
        const lock = require("./frontend/package-lock.json");
        if (lock.lockfileVersion < 3) { console.log("lockfileVersion " + lock.lockfileVersion); process.exit(1); }
        const bad = [];
        for (const [path, pkg] of Object.entries(lock.packages)) {
            if (!path || pkg.link) continue;
            if (!pkg.integrity) bad.push("no integrity: " + path);
            if (pkg.resolved && !pkg.resolved.startsWith("https://registry.npmjs.org/")) bad.push("non-registry source: " + path + " " + pkg.resolved);
        }
        if (bad.length) { console.log(bad.join("\n")); process.exit(1); }'
}

section_lockfiles() {
    section lockfiles
    check "pyproject.toml and requirements-dev.in pin exactly (==)" pyproject_pins_exact
    check "every locked Python package carries sha256 hashes" every_locked_package_has_hashes
    check "only PyPI and the PyTorch CPU index are used" only_known_indexes
    check "dev lock has no index lines (would reset pip's index list)" dev_lock_has_no_index_lines
    check "no CUDA/GPU packages in the runtime lock" no_cuda_packages
    if [ -x "$PY/uv" ] || need uv; then
        check "requirements*.txt match their inputs (re-lock diff)" python_locks_are_fresh
    else
        skip "requirements*.txt match their inputs" "uv not installed"
    fi
    if need node; then
        check "frontend/package.json pins exactly (no ^ or ~)" npm_pins_exact
        check "package-lock.json: v3, integrity on every package, npmjs registry only" npm_lock_integrity
    else
        skip "frontend pin checks" "node not installed"
    fi
}

# ---------------------------------------------------------------------------
# frontend: install from lock, lint, types, build, audit
# ---------------------------------------------------------------------------
node_matches_nvmrc() {
    local want have
    want=$(cut -d. -f1 .nvmrc)
    have=$(node --version | sed 's/^v//' | cut -d. -f1)
    [ "$want" = "$have" ] || { echo "node $(node --version), .nvmrc wants $(cat .nvmrc) (run: nvm use)"; return 1; }
}
in_frontend() { (cd frontend && "$@"); }
npm_audit_with_exceptions() {
    # Every advisory fails unless frontend/audit-exceptions.json lists its ID
    # with an unexpired date (each one also recorded in DECISIONS.md).
    # shellcheck disable=SC2016  # ${...} below is JavaScript, not shell
    (cd frontend && npm audit --json 2>/dev/null; true) | node -e '
        const audit = JSON.parse(require("fs").readFileSync(0, "utf8"));
        const { exceptions } = require("./frontend/audit-exceptions.json");
        const today = new Date().toISOString().slice(0, 10);
        const allowed = new Map(exceptions.map((e) => [e.advisory, e]));
        let bad = 0;
        for (const [name, v] of Object.entries(audit.vulnerabilities || {})) {
            for (const via of v.via) {
                if (typeof via !== "object") continue;
                const id = via.url.split("/").pop();
                const ex = allowed.get(id);
                if (!ex) { console.log(`${via.severity} ${name} ${id}: not in audit-exceptions.json`); bad = 1; }
                else if (ex.expires < today) { console.log(`${name} ${id}: exception expired ${ex.expires}`); bad = 1; }
                else console.log(`accepted until ${ex.expires}: ${name} ${id}`);
            }
        }
        process.exit(bad);'
}

no_source_maps_shipped() { ! find frontend/dist -name '*.map' | grep -q .; }

section_frontend() {
    section frontend
    need node || { skip "frontend" "node not installed"; return; }
    check "node major matches .nvmrc" node_matches_nvmrc
    check "npm ci (lockfile only, install scripts disabled)" in_frontend npm ci --ignore-scripts --no-audit --no-fund
    check "eslint (zero warnings)" in_frontend npm run -s lint
    check "tsc type-check" in_frontend npm run -s type-check
    check "vite production build" in_frontend npm run -s build
    check "no source maps in the production bundle" no_source_maps_shipped
    check "npm audit (any advisory fails unless excepted, with expiry)" npm_audit_with_exceptions
}

# ---------------------------------------------------------------------------
# workflows: GitHub Actions security
# ---------------------------------------------------------------------------
install_actionlint() {
    local os arch key sum url tmp
    os=$(uname -s | tr '[:upper:]' '[:lower:]')
    arch=$(uname -m); [ "$arch" = x86_64 ] && arch=amd64; [ "$arch" = aarch64 ] && arch=arm64
    key="ACTIONLINT_SHA256_${os}_${arch}"
    sum=${!key:-}
    [ -n "$sum" ] || { echo "no pinned actionlint checksum for ${os}_${arch}"; return 1; }
    url="https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/actionlint_${ACTIONLINT_VERSION}_${os}_${arch}.tar.gz"
    tmp=$(mktemp -d)
    curl -fsSL -o "$tmp/a.tgz" "$url" || { rm -rf "$tmp"; return 1; }
    echo "$sum  $tmp/a.tgz" | shasum -a 256 -c - || { rm -rf "$tmp"; return 1; }
    mkdir -p "$TOOLS" && tar -xzf "$tmp/a.tgz" -C "$TOOLS" actionlint
    rm -rf "$tmp"
    "$TOOLS/actionlint" --version
}

actionlint_bin() {
    if [ -x "$TOOLS/actionlint" ]; then echo "$TOOLS/actionlint"; elif need actionlint; then command -v actionlint; fi
}

run_actionlint() { "$(actionlint_bin)" -shellcheck= .github/workflows/*.yml; }

run_zizmor() {
    # Online mode (GH_TOKEN set, as in CI) also checks for impostor commits
    # and known-vulnerable actions; offline mode runs the static audits.
    if [ -n "${GH_TOKEN:-}" ]; then "$PY/zizmor" --persona regular .github/workflows
    else env -u GH_TOKEN "$PY/zizmor" --offline --persona regular .github/workflows; fi
}

actions_pinned_by_sha() {
    # Third-party actions must be pinned to a full commit SHA. Exempt: local
    # actions and this account's own reusable workflows (called @main on purpose).
    local bad
    bad=$(grep -nE '^\s*-?\s*uses:' .github/workflows/*.yml \
        | grep -vE 'uses:\s*\./' \
        | grep -vE 'uses:\s*pieteradejong/' \
        | grep -vE 'uses:\s*[^@[:space:]]+@[0-9a-f]{40}(\s|$)')
    [ -z "$bad" ] || { echo "$bad"; return 1; }
}

workflows_declare_permissions() {
    local f bad=0
    for f in .github/workflows/*.yml; do
        grep -qE '^permissions:' "$f" || { echo "$f: no top-level permissions"; bad=1; }
        grep -qE '^permissions:\s*write-all' "$f" && { echo "$f: write-all"; bad=1; }
    done
    return "$bad"
}

checkouts_drop_credentials() {
    local f co pc bad=0
    for f in .github/workflows/*.yml; do
        co=$(grep -cE 'uses:\s*actions/checkout@' "$f")
        pc=$(grep -cE 'persist-credentials:\s*false' "$f")
        [ "$co" -le "$pc" ] || { echo "$f: $co checkout(s), $pc with persist-credentials: false"; bad=1; }
    done
    return "$bad"
}

no_dangerous_triggers() { ! grep -nE '^\s*(pull_request_target|workflow_run)\s*:' .github/workflows/*.yml; }

no_untrusted_input_in_run() {
    ! grep -nE '\$\{\{\s*github\.(event\.(issue|pull_request|comment|review|head_commit|commits)|head_ref)' .github/workflows/*.yml
}

security_workflow_present() { grep -q 'pieteradejong/dotfiles/.github/workflows/security-reusable.yml' .github/workflows/*.yml; }

section_workflows() {
    section workflows
    if [ -n "$(actionlint_bin)" ]; then check "actionlint" run_actionlint
    else skip "actionlint" "run: ./scripts/check.sh install-actionlint"; fi
    if [ -x "$PY/zizmor" ]; then check "zizmor (Actions security audit)" run_zizmor
    else skip "zizmor" "not in venv: pip install --require-hashes -r requirements-dev.txt"; fi
    check "every third-party action pinned to a commit SHA" actions_pinned_by_sha
    check "every workflow declares top-level permissions" workflows_declare_permissions
    check "every checkout sets persist-credentials: false" checkouts_drop_credentials
    check "no pull_request_target / workflow_run triggers" no_dangerous_triggers
    check "no untrusted event fields interpolated" no_untrusted_input_in_run
    check "shared security workflow (gitleaks + gate) is called" security_workflow_present
    if need shellcheck; then check "shellcheck scripts" shellcheck scripts/*.sh
    else skip "shellcheck" "not installed"; fi
}

# ---------------------------------------------------------------------------
# docker: static checks, and with --build a full build + smoke test
# ---------------------------------------------------------------------------
hadolint_container() { docker run --rm -i "$HADOLINT_IMAGE" < Dockerfile; }

from_lines_digest_pinned() {
    # The whole instruction must be image@digest (optionally AS stage) — a
    # digest that only appears in a trailing comment doesn't count.
    ! grep -nE '^FROM ' Dockerfile | grep -vE '^[0-9]+:FROM [^[:space:]@#]+@sha256:[0-9a-f]{64}( AS [A-Za-z0-9_-]+)?[[:space:]]*$'
}

final_user_non_root() {
    local user
    user=$(grep -E '^USER ' Dockerfile | tail -n 1 | awk '{print $2}')
    [ -n "$user" ] || { echo "no USER instruction"; return 1; }
    case "$user" in 0|0:*|root|root:*) echo "USER $user"; return 1;; esac
}

dockerignore_excludes_local_state() {
    local p bad=0
    for p in app/data/ app/static/ app/models/ venv/ .git frontend/node_modules/; do
        grep -qxF "$p" .dockerignore || { echo "missing from .dockerignore: $p"; bad=1; }
    done
    return "$bad"
}

docker_build() { docker build --pull -t "$IMAGE" .; }

# Runs inside the container: with no network at all, the app must still
# start, load the model and answer searches — proof nothing is fetched at runtime.
SMOKE_PY='
import json, os, time, urllib.request
base = "http://127.0.0.1:8000"
for _ in range(120):
    try:
        urllib.request.urlopen(base + "/health", timeout=2); break
    except Exception:
        time.sleep(1)
def get(p): return json.load(urllib.request.urlopen(base + p, timeout=120))
assert get("/health")["status"] == "success"
assert get("/health/pipeline")["consistency"] == "all_stages_match"
req = urllib.request.Request(base + "/api/search", data=json.dumps({"query": "Xander becomes a hyena", "limit": 3}).encode(),
                             headers={"content-type": "application/json"})
hits = json.load(urllib.request.urlopen(req, timeout=120))
assert (hits[0]["season"], hits[0]["episode"]) == (1, "06"), hits[0]
assert os.getuid() != 0, "running as root"
print("smoke ok: uid", os.getuid(), "top hit", hits[0]["title"])
'

docker_smoke_offline() {
    local cid rc
    cid=$(docker run -d --network none "$IMAGE") || return 1
    docker exec "$cid" python -c "$SMOKE_PY"; rc=$?
    [ "$rc" -eq 0 ] || docker logs "$cid" 2>&1 | tail -n 20
    docker rm -f "$cid" >/dev/null
    return "$rc"
}

docker_image_contents() {
    docker run --rm --network none --entrypoint sh "$IMAGE" -c '
        set -e
        for p in /app/.git /app/tests /app/venv /app/requirements-dev.txt /app/app/models /app/app/dump.rdb /app/scripts; do
            [ ! -e "$p" ] || { echo "should not be in image: $p"; exit 1; }
        done
        [ -z "$(ls -A /app/app/data/episodes)" ] || { echo "local episode data baked into image"; exit 1; }
        [ -f /app/app/static/index.html ] || { echo "frontend build missing"; exit 1; }
        ! touch /app/app/main_written 2>/dev/null || { echo "app code is writable by the runtime user"; exit 1; }
        touch /app/app/data/.write_test && rm /app/app/data/.write_test
        test "$HF_HUB_OFFLINE" = 1
        echo "contents ok"'
}

section_docker() {
    section docker
    if need hadolint; then check "hadolint" hadolint Dockerfile
    elif docker info >/dev/null 2>&1; then check "hadolint (pinned container)" hadolint_container
    else skip "hadolint" "not installed and no Docker daemon"; fi
    check "every FROM pinned by sha256 digest" from_lines_digest_pinned
    check "final stage runs as a non-root user" final_user_non_root
    check ".dockerignore keeps local state out of the image" dockerignore_excludes_local_state
    if [ "$DOCKER_BUILD" = 1 ]; then
        if docker info >/dev/null 2>&1; then
            check "docker build" docker_build || return
            check "image contents (no dev files/data, read-only code, offline env)" docker_image_contents
            check "container smoke test with networking disabled" docker_smoke_offline
        else
            skip "docker build + smoke test" "no Docker daemon (colima start)"
        fi
    fi
}

# ---------------------------------------------------------------------------
# secrets: local secret scan (CI runs gitleaks via the shared security workflow)
# ---------------------------------------------------------------------------
section_secrets() {
    section secrets
    if need gitleaks; then check "gitleaks (full history)" gitleaks git --no-banner --redact .
    else skip "gitleaks" "not installed; CI runs it via security.yml"; fi
    check "no .env files tracked" sh -c '! git ls-files | grep -E "(^|/)\.env($|\.)" | grep -v "\.example$"'
}

# ---------------------------------------------------------------------------

SECTIONS=()
DOCKER_BUILD=0
for arg in "$@"; do
    case "$arg" in
        --build) DOCKER_BUILD=1 ;;
        install-actionlint) install_actionlint; exit $? ;;
        python|lockfiles|frontend|workflows|docker|secrets) SECTIONS+=("$arg") ;;
        -h|--help) sed -n '/^# Every check/,/^# the exit code/p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "unknown argument: $arg (try --help)"; exit 2 ;;
    esac
done
if [ ${#SECTIONS[@]} -eq 0 ]; then
    SECTIONS=(lockfiles python frontend workflows docker secrets)
    docker info >/dev/null 2>&1 && DOCKER_BUILD=1
fi

for s in "${SECTIONS[@]}"; do "section_$s"; done

printf '\n%sSummary%s\n' "$BOLD" "$RESET"
for r in "${RESULTS[@]}"; do
    case "$r" in
        PASS*) printf '  %s%s%s\n' "$GREEN" "$r" "$RESET" ;;
        FAIL*) printf '  %s%s%s\n' "$RED" "$r" "$RESET" ;;
        *)     printf '  %s%s%s\n' "$YELLOW" "$r" "$RESET" ;;
    esac
done
exit "$FAILED"
