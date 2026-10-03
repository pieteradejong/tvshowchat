# Decisions

Append-only. Supersede an entry with a new one that links back; don't edit old ones.

## 1. Replace ChromaDB with an exact in-memory cosine index
**Date:** 2026-10-01
**Context:** ChromaDB 0.4.22 carried one critical and one high Dependabot advisory with no patched
release in the 0.4 line, and the corpus is 144 vectors of 384 dims — far below the size where an
approximate index pays for itself. `docs/SEARCH_ACCURACY.md` had already concluded a vector
database was unnecessary.
**Decision:** Exact brute-force cosine over a unit-normalised NumPy matrix, built from the
document store on first search (`AdvancedVectorStore._nearest`). The candidate-then-boost pipeline
is unchanged: top `limit×3` (or `limit×2` with a season filter) by cosine, then character/theme
boosts. Rejected: upgrading ChromaDB (a large API jump to keep a dependency the data doesn't need).
**Verified:** `./venv/bin/pytest tests/unit/test_vector_index.py` → 9 passed;
`./venv/bin/pytest` → 47 passed.

## 2. Re-record the search ranking baseline on the exact engine
**Date:** 2026-10-01
**Context:** `tests/fixtures/search_baseline.json` (2026-09-12) was meant to prove the engine swap
changed nothing. Running `scripts/capture_search_baseline.py verify` twice against the *unchanged*
ChromaDB engine drifted on 9 and then 7 of 23 queries: HNSW is approximate, so the candidate set
fed into the boosts varied between runs. The baseline was one random draw and could not certify
anything.
**Decision:** Re-record the baseline on the exact engine, which drifted from the old baseline on
5 of 23 queries (all at rank 4–5 except the stopword query "the") — less than the old engine
drifted from itself. The new baseline is deterministic and is now the regression net for the
dependency upgrades. Rejected: tolerating drift in `verify` (it would also hide real regressions).
**Verified:** two `verify` runs on the exact engine produced identical rankings
(`diff` of both outputs, excluding log lines → no difference); after recapture,
`verify` → `OK - all 23 queries return identical top-5 rankings.`

## 3. Upgrade every Python dependency and lock with hashes
**Date:** 2026-10-01
**Context:** 53 open Dependabot alerts against `requirements.txt` (torch critical; aiohttp, lxml,
chromadb high), and nothing pinned transitive packages or their content.
**Decision:** Direct dependencies in `requirements.in` / `requirements-dev.in`, compiled by
`scripts/lock.sh` (uv, `--universal --generate-hashes`, PyPI only) into hash-locked
`requirements.txt` / `requirements-dev.txt`; installs use `--require-hashes`. Upgraded to current
releases (torch 2.2.1→2.14.1, sentence-transformers 2.5.1→6.1.0, numpy 1.26→2.5, FastAPI
0.104→0.142). Dropped `chromadb`, `aiohttp` (only dead modules used it), `websockets`,
`huggingface_hub`, `python-json-logger`, `python-dotenv` as direct pins (unused or transitive);
moved `black`/`mypy`/`ruff`/`pytest` out of the runtime image.
**Verified:** after a clean `--require-hashes` install, `scripts/capture_search_baseline.py verify`
→ `OK - all 23 queries return identical top-5 rankings.`; the corpus-vs-query model check in
`tests/integration/test_search_quality.py` passes (cosine > 0.999 on 4 episodes).
`pip-audit --strict --require-hashes --disable-pip -r requirements.txt` → `No known
vulnerabilities found` (same for `requirements-dev.txt`). The first lock had kept a stale
`python-dotenv==1.0.0` (uv prefers pins already in the output file); `scripts/lock.sh --upgrade`
re-resolved it to 1.2.4.

## 4. Pin the embedding model to a Hugging Face commit
**Date:** 2026-10-01
**Context:** Every load site called `SentenceTransformer("all-MiniLM-L6-v2")`, which resolves the
`main` revision on huggingface.co at each start. An upstream change — benign or not — would alter
query vectors silently while the corpus vectors stayed fixed. The `app/models/` copy was never
used (and its weights are gitignored).
**Decision:** `app/services/embedder.py` is the only loader, pinned to
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (the revision the corpus vectors match; it ships
`model.safetensors`, not a pickle). A unit test fails if any app code constructs the model
directly.
**Verified:** `./venv/bin/pytest tests/unit/test_embedder.py tests/integration/test_search_quality.py`
→ passed.

## 5. Install torch from PyTorch's CPU-only index
**Date:** 2026-10-01
**Context:** The PyPI `torch` wheel for Linux depends on ~20 CUDA/nvidia/triton packages
(several GB). This service is CPU-only and deploys to a 512 MB Render instance; the GPU stack is
pure supply-chain surface and image weight. The workspace rule is "one registry" unless the
README says why.
**Decision:** Runtime dependencies move from `requirements.in` to `pyproject.toml` so uv can bind
`torch` — and only `torch` — to `https://download.pytorch.org/whl/cpu` (`explicit = true` index +
`[tool.uv.sources]`). Every other package still resolves from PyPI. The lock carries the PyTorch
index as `--extra-index-url` for pip; that is safe only because every install uses
`--require-hashes`, which discards any artifact whose hash isn't locked. The README and
`scripts/check.sh` (`only_known_indexes`, `no_cuda_packages`) state and enforce this.
Rejected: PyPI torch (the CUDA stack); a global extra index at resolve time (lets the PyTorch
index serve any package name — dependency confusion).
**Verified:** `./scripts/lock.sh` → `requirements.txt (64 packages)` (was 82);
`grep -cE '^(nvidia|triton|cuda)' requirements.txt` → `0`; Docker build on linux/arm64 installed
`torch==2.14.1+cpu` from the lock with `--require-hashes`.

## 6. CI runs the same script developers run
**Date:** 2026-10-01
**Context:** The old `ci.yml` installed unpinned `ruff`/`pytest` on Python 3.9 with tag-pinned
actions, and had been failing since 2025 (35 ruff errors). Nothing checked the frontend, the
workflows themselves, or the image.
**Decision:** `scripts/check.sh` holds every check, in sections; `ci.yml` runs one section per
job (python+lockfiles, frontend, workflows, docker --build). Plus CodeQL (`security-extended`,
Python + TypeScript) and Dependabot for Actions, Docker, npm and pip. Rejected: separate check
logic in YAML (drifts from what developers run locally).
**Verified:** PARTIAL. Locally, `./scripts/check.sh` (all six sections, including
`docker --build`) → 40 of 41 checks PASS; the one FAIL (ruff E741 in a new test) was fixed and
`./scripts/check.sh python lockfiles workflows` then exited 0 with no FAIL or SKIP. The
container smoke test passed with `--network none` (model loaded offline, search returned s01e06,
uid 10001). `tests/unit/test_check_script.py` → 18 passed (each guard FAILs on its injected
fault). NOT YET: the workflows on GitHub — recheck after the first push of
`ci/secure-pipeline`.

## 7. Accept GHSA-vfj7-8cjw-p6xm (braces) until 2026-11-01
**Date:** 2026-10-02
**Context:** A high-severity `braces` advisory (stack-exhaustion DoS via deeply nested patterns)
was published after the frontend upgrade and failed CI's `npm audit`. Every `braces` version is
affected (3.0.3 is the latest release). It arrives only through Tailwind 3's build tooling
(`chokidar`, `micromatch`). Policy for High in a public project: upgrade within 7 days, or record
why it is not exploitable.
**Decision:** Not exploitable here: build-time only, never shipped or run in production, and the
only glob patterns it sees are this repo's own Tailwind `content` globs. Accepted by advisory ID
in `frontend/audit-exceptions.json` with an expiry; `check.sh` fails on any other advisory and on
this one after 2026-11-01. The real fix is the Tailwind 4 migration, deferred until the UI can be
checked visually (it changes class names and border/ring defaults). Rejected: lowering the audit
level or `--omit=dev` (both would hide future advisories wholesale).
**Verified:** `./scripts/check.sh frontend` → `PASS npm audit (any advisory fails unless
excepted, with expiry)`, printing `accepted until 2026-11-01: braces GHSA-vfj7-8cjw-p6xm`.

## 8. Index lines only in the runtime lock; audit torch+cpu as its upstream release
**Date:** 2026-10-02
**Context:** The first CI run failed to install `torch==2.14.1+cpu`: pip resets its index list
at every `--index-url` line, and `requirements-dev.txt` (read second) carried one, dropping the
PyTorch index set by `requirements.txt`. Invisible on macOS, where torch comes from PyPI. Then
`pip-audit --strict` on Linux refused `torch+cpu` (not on PyPI).
**Decision:** `lock.sh` emits index lines into `requirements.txt` only; `check.sh` enforces it
(`dev lock has no index lines`, with a fault-injection test). `pip-audit` audits `+cpu` pins as
the upstream release they are built from (`--no-deps`, lock fully pinned), keeping `--strict`.
**Verified:** in `python:3.12.15-slim` (linux/arm64): `pip install --require-hashes -r
requirements-dev.txt -r requirements.txt` → torch `2.14.1+cpu` installed; the rewritten audit →
`No known vulnerabilities found`, exit 0. Linux/amd64: NOT YET — next CI run.
