# TV Show Chat

A semantic search and chat application for TV show transcripts, built with Python and React.

## Table of Contents

- [Quick Start](#quick-start)
- [Features](#features)
- [Tech Stack](#tech-stack)
  - [Backend](#backend)
  - [Frontend](#frontend)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the Application](#running-the-application)
  - [Backend](#backend-1)
  - [Frontend](#frontend-1)
- [Project Structure](#project-structure)
- [Data Pipeline](#data-pipeline)
- [Documentation](#documentation)
- [Development](#development)
  - [Adding New Episodes](#adding-new-episodes)
  - [Testing](#testing)
  - [Data Pipeline Utilities](#data-pipeline-utilities)
- [Security and CI/CD](#security-and-cicd)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

The repository includes the complete `btvs_all_seasons.json` dataset (all 7 seasons, 144 episodes). The pipeline is fully set up and verified.

1. **Initialize dependencies & environment**
   ```bash
   ./init.sh
   ```
   Creates/updates the Python 3.12 virtualenv, installs requirements, prepares data directories, and downloads the embedding model.

2. **Run the backend (FastAPI)**
   ```bash
   ./run.sh
   ```
   Starts the API at http://localhost:8000. The document store auto-populates from the tracked dataset on first startup, and the in-memory search index is built on the first search.

3. **Run the frontend (React/Vite)**
   ```bash
   ./run_frontend.sh
   ```
   Serves the UI at http://localhost:5173 and proxies API calls to the backend.

4. **Run the integrated test suite (optional)**
   ```bash
   ./test.sh
   ```
   Requires the backend to be running. Verifies health endpoints, search across all seasons, document store, embeddings, and ensures the content, document store and search index counts match (144 total episodes across all 7 seasons).

To refresh the dataset later, follow the [Multi-Season Refresh Workflow](#multi-season-refresh-workflow); otherwise no scraping is required.

## Features

- **Semantic Search**: Find relevant episodes and scenes using natural language queries
- **Vector Search**: Exact in-memory cosine search over one embedding per episode — deterministic, no database
- **Modern UI**: Clean, responsive interface built with React and TailwindCSS
- **FastAPI Backend**: High-performance API with automatic OpenAPI documentation

## Tech Stack

### Backend
- Python 3.12
- FastAPI 0.142 + Uvicorn 0.54
- Sentence Transformers 6.1 / PyTorch 2.14, model `sentence-transformers/all-MiniLM-L6-v2`
  pinned to an exact Hugging Face commit (`app/services/embedder.py`)
- NumPy 2.5 for the search index (brute-force cosine; 144 vectors need no vector database)

Every Python dependency is locked with sha256 hashes — see
[Security and CI/CD](#security-and-cicd).
- Uvicorn (ASGI Server)

### Frontend
- Node.js 24 LTS (`.nvmrc`)
- React 18, React Router 7, TanStack Query 5, d3 7
- TypeScript 5.9, TailwindCSS 3.4
- Vite 8, ESLint 10 (flat config, `frontend/eslint.config.js`)

## Prerequisites

- Python 3.12
- pip (Python package manager)
- git

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/tvshowchat.git
cd tvshowchat
```

2. Run the initialization script:
```bash
./init.sh
```

This will:
- Create a Python virtual environment
- Install all required dependencies
- Set up the data directories
- Download the embedding model

## Running the Application

### Backend

1. Start the backend server:
```bash
./run.sh
```

This will:
- Start the FastAPI server
- Load the embedding model (the search index is built on the first search)
- Make the API available at http://localhost:8000

2. Access the backend:
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Pipeline Health: http://localhost:8000/health/pipeline (shows episode counts at each stage)
- Vector Store Status: http://localhost:8000/health/vector-store
- Model Status: http://localhost:8000/health/model

### Frontend

1. Start the frontend (in a new terminal):
```bash
./run_frontend.sh
```

This will:
- Start the Vite development server
- Make the frontend available at http://localhost:5173
- Automatically reload on file changes

2. Open your browser:
- Frontend: http://localhost:5173
- The frontend will connect to the backend API automatically

**Note:** Make sure the backend is running before starting the frontend, otherwise API calls will fail.

## Project Structure

```
tvshowchat/
├── app/
│   ├── api/            # FastAPI routes and endpoints
│   ├── services/       # Business logic and services
│   │   ├── scraping/   # Web scraping utilities
│   │   ├── pipeline/   # Data processing pipeline
│   │   └── embeddings/ # Embedding generation
│   ├── models/         # Data models and schemas
│   ├── data/          # Data storage
│   │   ├── episodes/  # Episode transcripts (backup)
│   │   └── embeddings/ # Vector embeddings (backup)
│   └── logs/          # Application logs
├── scripts/           # Utility scripts
├── tests/            # Test suite
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

## Data Pipeline

1. **Data Collection**: Episode transcripts are collected and stored in JSON format
2. **Text Processing**: Transcripts are cleaned and prepared for embedding
3. **Embedding Generation**: Text is converted to vector embeddings using Sentence Transformers
4. **Indexing**: On the first search, the episode vectors are loaded into one normalised NumPy matrix
5. **Search**: The query is embedded with the same pinned model, scored by exact cosine against every
   episode, and the top candidates are re-ranked by character and theme boosts. Results are
   deterministic: the same query always returns the same ranking.

## Documentation

- `ROADMAP.md` – **Consolidated roadmap and implementation plan** (start here for planning)
- `ARCHITECTURE.md` – High-level system design and diagrams
- `docs/DATA_PIPELINE.md` – Detailed ingestion and storage pipeline
- `docs/TESTING_GUIDE.md` – Automated and manual testing instructions

**Current Status**: All 7 seasons (144 episodes) are ingested and searchable. The pipeline is fully verified and tested. See `ROADMAP.md` for complete details.

## Development

### Adding New Episodes

1. Place episode transcripts in `app/data/episodes/` in JSON format
2. Run the initialization script to load them into the document store:
```bash
python scripts/init_data.py
```

### Testing

Two layers:

**1. `pytest` — no server needed, runs in CI.**

```bash
./venv/bin/pytest            # everything (~15 s once the model is cached)
./venv/bin/pytest tests/unit # fast; never loads the embedding model
```

| File | Guards |
|---|---|
| `tests/unit/test_dataset.py` | The tracked dataset: 7 seasons, 144 episodes, field types, 384-dim vectors |
| `tests/unit/test_vector_index.py` | The search index: exact order, season filter, deterministic ties, rebuilds, ChromaDB gone |
| `tests/unit/test_embedder.py` | The model is pinned to a full commit sha, and no app code loads it any other way |
| `tests/integration/test_api.py` | Health, search, input bounds (422s), CORS, and that a 500 never leaks exception text |
| `tests/integration/test_search_quality.py` | Rankings match `tests/fixtures/search_baseline.json`; the query model still matches the corpus vectors |
| `tests/unit/test_check_script.py` | `scripts/check.sh` itself: injects 18 faults (unpinned action, `^` range, digest-less `FROM`, root `USER`, CUDA package, foreign index, stale lock, …) into a scratch copy and asserts the matching check FAILs |

The ranking baseline is the regression net for refactors and dependency upgrades: if a change
moves any of the 23 recorded top-5 rankings, the suite fails. Re-record it only for a deliberate
search change (`./venv/bin/python scripts/capture_search_baseline.py capture`).

To run every check CI runs (lint, tests, audits, lockfiles, workflows, Docker), use
[`./scripts/check.sh`](#one-script-for-every-check-scriptschecksh).

**2. `./test.sh` — end-to-end against a running server.**

**Prerequisites:** The server must be running (`./run.sh`)

**What it tests:**
1. **Health Endpoints** - `/health`, `/health/vector-store`, `/health/model`, `/health/pipeline`
2. **System State** - `/api/test` (vector store stats, sample episode, test search)
3. **Search Functionality** - `/api/test-search` (default and custom queries)
4. **Search Across All Seasons** - Verifies search works for all 7 seasons
5. **Vector Store Status** - Verifies the search index holds 144 episodes
6. **Data Directories** - Checks for episode and embedding files
7. **Crawler Status** - Runs `scripts/scrape_episodes.py --status`
8. **Pipeline Integrity** - Verifies all stages match (content → document store → search index)

**Expected Results:**
- All endpoints return `200 OK`
- Search returns relevant episode results across all 7 seasons
- Vector store shows healthy status with 144 episodes
- Data directories contain expected files (7 season files in episodes and embeddings)
- Pipeline integrity verified (all stages match: 144 episodes)

See `docs/TESTING_GUIDE.md` for detailed testing documentation.

### Data Pipeline Utilities

Use the crawler helper scripts for manual checks or to refresh scraped data:
```bash
python3.12 scripts/scrape_episodes.py --status          # snapshot of pipeline health
python3.12 scripts/scrape_episodes.py --import-latest    # import latest crawl into document store
python3.12 scripts/scrape_episodes.py --reindex          # rebuild the search index and print its stats
python3.12 scripts/scrape_episodes.py --all --force      # re-crawl and regenerate content JSON
./scripts/crawl.sh                                       # crawl any seasons missing from btvs_all_seasons.json
./scripts/crawl.sh --season 5                            # crawl a specific season
./scripts/crawl.sh --all --force                         # force a full re-crawl
```

### Multi-Season Refresh Workflow

The canonical dataset lives at `app/content/btvs_all_seasons.json`. To regenerate embeddings and the search index for all seven seasons:

1. `./scripts/crawl.sh` — fetch missing seasons (no-op if coverage is complete).
2. `python3.12 scripts/scrape_episodes.py --import-latest` — sync the document store (`app/data/episodes` + embeddings).
3. `python3.12 scripts/scrape_episodes.py --reindex` — rebuild the search index from the document store and check its counts.
4. `./test.sh` — validates that content, document store, embeddings, vector store, and API all report 144 episodes across Seasons 1–7.

## Security and CI/CD

Work started 2026-10-01 on branch `ci/secure-pipeline`. Decisions and their verification are in
[`DECISIONS.md`](DECISIONS.md). This table is the current state; items move to ✅ only with a
verification command run.

| Area | Status | What it means |
|---|---|---|
| Python dependencies | ✅ | Hash-locked (`--require-hashes`), all upgraded; `pip-audit --strict`: 0 known vulnerabilities |
| Frontend dependencies | ✅ | Exact pins, `npm ci` from the lockfile; `npm audit`: one accepted build-time advisory (below), nothing else |
| Vulnerable / unused components | ✅ | ChromaDB (no fix available), aiohttp and four dead modules removed |
| Embedding model | ✅ | Pinned to a Hugging Face commit; baked into the image, so production never downloads it |
| API hardening | ✅ | No exception text in responses, bounded search input, CORS without credentials, INFO logging |
| Tests | ✅ | 66 pytest tests: ranking baseline, leak checks, and fault-injection tests proving each CI guard fails when broken |
| CUDA-free install | ✅ | `torch` from PyTorch's CPU index (bound to `torch` only): 82 → 64 locked packages, no GPU stack |
| Container image | ✅ | Digest-pinned bases, non-root (uid 10001), read-only code; smoke-tested with networking disabled |
| CI pipeline | ✅ | SHA-pinned actions, read-only token, lint/test/audit/build, CodeQL — green on GitHub (PR #1) |
| Security workflow | ⏳ blocked | `security.yml` calls the shared dotfiles workflow, which isn't on dotfiles `main` yet |
| Deploy gate (Render) | ✅ configured | Auto-deploy stays off (refactor); when re-enabled, `checksPass` deploys `main` only after CI passes |
| Branch protection on `main` | ⏳ needs your OK | Require PRs and passing checks before merge — a GitHub settings change |
| Local check script | ✅ | `scripts/check.sh`: 42 checks in 6 sections, the same ones CI runs |

### Dependencies and lockfiles

Python dependencies are declared in two input files and locked into two hash-pinned files:

| Edit this | Locked into | Contains |
|---|---|---|
| `requirements.in` | `requirements.txt` | Runtime dependencies (what ships in the image) |
| `requirements-dev.in` | `requirements-dev.txt` | Test, lint and audit tools (never shipped) |

Every package, direct or transitive, is pinned to an exact version with its sha256 hashes, and
installs use `pip install --require-hashes`. A package swapped on PyPI after locking fails to
install instead of running.

```bash
# change a version in requirements*.in, then:
./scripts/lock.sh                                                  # needs uv (brew install uv)
./venv/bin/pip install --require-hashes -r requirements.txt -r requirements-dev.txt
./venv/bin/pytest                                                  # the ranking baseline catches drift
```

**Accepted advisories.** `frontend/audit-exceptions.json` lists npm advisories judged not
exploitable here, each with a reason and an expiry date; `check.sh` fails on anything not listed
and on listed entries once expired. Currently: `braces` GHSA-vfj7-8cjw-p6xm (build-time only, no
fixed release, expires 2026-11-01 — see `DECISIONS.md` #7). The Python lock never mixes index
lines across files: pip resets its index list at each `--index-url`, so only `requirements.txt`
carries them (`DECISIONS.md` #8).

The frontend pins every dependency exactly in `frontend/package.json` (no `^` or `~`) and installs
with `npm ci`, which fails if `package-lock.json` doesn't match. Use Node 24 (`nvm use`).

### One script for every check: `scripts/check.sh`

CI runs exactly this script, one section per job, so a green local run means a green CI run.

```bash
./scripts/check.sh                       # everything (builds the image if Docker is running)
./scripts/check.sh python lockfiles      # just those sections
./scripts/check.sh docker --build        # build the image and smoke-test it
./scripts/check.sh install-actionlint    # fetch pinned actionlint, verify its sha256
```

| Section | Checks |
|---|---|
| `lockfiles` | Inputs pin with `==`; every locked package has sha256 hashes; only PyPI + the PyTorch CPU index; the dev lock has no index lines; no CUDA packages; `requirements*.txt` match their inputs (re-lock and diff); `package.json` has no `^`/`~`; `package-lock.json` is v3 with integrity hashes and npmjs-only sources |
| `python` | Python 3.12 venv; `pip check`; ChromaDB absent; ruff (incl. bandit security rules); pytest unit + integration; `pip-audit --strict` on both locks |
| `frontend` | Node matches `.nvmrc`; `npm ci --ignore-scripts`; ESLint with zero warnings; `tsc`; Vite build; no source maps shipped; `npm audit` fails on any advisory not in `audit-exceptions.json` (or expired) |
| `workflows` | actionlint; zizmor (Actions security audit); every third-party action pinned to a commit SHA; top-level `permissions` on every workflow; `persist-credentials: false` on every checkout; no `pull_request_target`/`workflow_run`; no untrusted event fields in expressions; the shared security workflow is called; shellcheck (pinned via the dev lock) |
| `docker` | hadolint; every `FROM` digest-pinned; non-root `USER`; `.dockerignore` excludes local state. With `--build`: builds the image, checks its contents (no dev files or local data, code not writable, offline env), then starts it **with networking disabled** and runs health, pipeline and search checks inside it |
| `secrets` | gitleaks over full history (if installed; CI runs it via `security.yml`); no tracked `.env` files |

A failing check doesn't stop the run: the summary lists every PASS/FAIL/SKIP and the exit code is
non-zero if anything failed. Local prerequisites: `./init.sh`, Node 24 (`nvm use`), and for the
optional parts `hadolint`, `gitleaks` (Homebrew) and Colima for Docker.

### CI pipeline

| Workflow | Runs on | Does |
|---|---|---|
| `ci.yml` | every push and PR | Four parallel jobs — `python`+`lockfiles`, `frontend`, `workflows`, `docker --build` — each one `scripts/check.sh` section |
| `codeql.yml` | PRs, pushes to `main`, weekly | CodeQL SAST (`security-extended`) for Python and TypeScript |
| `security.yml` | every push and PR | The shared workflow from `pieteradejong/dotfiles`: gitleaks over full history + the security gate |
| Dependabot alerts | continuous | Vulnerability alerts only. Update PRs stay **off** by workspace policy: they'd be bot commits that never pass the local gate. Bumps are deliberate: edit the pin, re-lock, run `check.sh` |

How the workflows themselves are hardened:

- **Actions pinned by full commit SHA** (with the version in a comment); a tag can be moved to
  malicious code, a SHA can't. Bump them deliberately: `gh api repos/<owner>/<action>/commits/<tag> --jq .sha`.
- **Read-only token by default** (`permissions: contents: read`). The only write anywhere is
  `security-events: write` on the CodeQL job, which it needs to upload results.
- **`persist-credentials: false`** on every checkout, so no later step can push with the token.
- **No `pull_request_target` or `workflow_run`**, and no PR titles, bodies or branch names in
  expressions — the usual ways a fork's PR gets code execution with secrets.
- **Tools are pinned and verified too:** zizmor, pip-audit, uv and shellcheck come from the hash
  lock, so CI and local runs use identical versions (an unpinned runner shellcheck once reported
  different rule codes); actionlint is
  downloaded at a pinned version and checked against its sha256.
- **The Python job runs on Linux**, so `pip-audit` covers the Linux-only `torch+cpu` pin that
  a macOS run skips.

### Deployment gate

`render.yaml` deploys the `main` branch from the `Dockerfile`. Auto-deploy is **off** for the
duration of the engine refactor (`autoDeployTrigger: "off"`). When it is re-enabled it must be
`checksPass`: Render then deploys a commit on `main` only after every GitHub check on it has
passed. Together with branch protection on `main` (required PRs + required checks), nothing
reaches production without passing the full pipeline.

### Container image

`Dockerfile` builds three stages: the frontend (`node:24.21.0-slim`), Python dependencies plus the
embedding model, and a slim runtime (`python:3.12.15-slim`).

- **Base images pinned by digest**, not tag. A tag can be re-pointed; a digest can't.
- **Installs only from the lockfiles:** `pip install --require-hashes`, and `npm ci --ignore-scripts`
  (no package install scripts run during the build).
- **The model is downloaded once, at build time,** at the pinned revision. The runtime sets
  `HF_HUB_OFFLINE=1`, so the container never fetches code or weights from the internet.
- **Runs as an unprivileged user** (uid 10001). Code is root-owned and read-only to the app;
  only `app/data/` and `app/logs/` are writable.
- **Nothing local leaks in:** `.dockerignore` excludes `app/data/`, `app/static/`, `app/models/`,
  logs, the Redis dump and dev-only files. The app imports the tracked dataset on first start.
- **`exec` makes uvicorn PID 1**, so it receives SIGTERM directly for clean shutdowns.

## Docker Deployment

The project includes Docker configuration for consistent, reproducible deployments on Render or any Docker-compatible platform.

### Local Docker Testing

Test the Docker setup locally before deploying:

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run directly
docker build -t tvshowchat-api .
docker run -p 8000:8000 tvshowchat-api
```

The API will be available at `http://localhost:8000`.

### Deploying to Render

Render supports Docker deployments for maximum consistency. Two options:

#### Option 1: Using Dockerfile (Recommended)

1. **Connect your repository** to Render
2. **Create a new Web Service**
3. **Set the following:**
   - **Environment**: Docker
   - **Dockerfile Path**: `./Dockerfile` (or leave blank if in root)
   - **Docker Context**: `.` (root directory)
   - **Plan**: Starter (512MB) or Standard (2GB recommended)
   - **Health Check Path**: `/health`

4. **Environment Variables** (optional, defaults work):
   - `PORT=8000` (Render sets this automatically)
   - `PYTHONUNBUFFERED=1`
   - `PYTHONDONTWRITEBYTECODE=1`

5. **Deploy!** Render will:
   - Build the Docker image from your Dockerfile
   - Run the container with the optimized settings
   - Handle health checks automatically

#### Option 2: Using render.yaml (Blueprint)

The repository includes a `render.yaml` blueprint for automated setup:

1. In Render Dashboard, click **New** → **Blueprint**
2. Connect your repository
3. Render will automatically detect `render.yaml` and create the service

The blueprint is configured for:
- **Starter tier** (512MB RAM) - should work after memory optimizations
- **Standard tier** (2GB RAM) - recommended for production (uncomment in render.yaml)

### Docker Features

- **Multi-stage build**: Smaller final image size (~500MB vs ~2GB)
- **Optimized layers**: Better caching for faster rebuilds
- **Health checks**: Automatic container health monitoring
- **Production-ready**: Only production dependencies included
- **Memory optimized**: Lazy-loading of expensive operations

### Data Persistence

For production deployments, ensure data persistence:

1. **Mount volumes** for `app/data/` (episodes, embeddings)
2. **Use Render's disk storage** or external storage (S3, etc.)
3. **Backup strategy**: Regular backups of `app/data/` directory

The Docker setup creates necessary directories but data should be:
- Pre-populated in the image, OR
- Mounted from persistent storage, OR
- Loaded on first startup (current behavior)

### Troubleshooting

**Out of memory errors:**
- Upgrade to Standard tier (2GB RAM)
- Check memory usage: `docker stats`
- Review lazy-loading optimizations in code

**Slow startup:**
- First request may take 2-5s longer (builds embeddings on demand)
- Subsequent requests are fast
- Consider pre-warming on deployment

**Health check failures:**
- Check logs: `docker logs <container-id>`
- Verify port is correct (Render sets PORT env var)
- Ensure `/health` endpoint is accessible

## Roadmap

Status as of 2026-10-01. The longer-term plan is in `ROADMAP.md`; this section tracks the
open problems found during the 2026-09 review.

### Search quality (highest priority)

- [ ] **Most of each episode is never indexed.** `app/services/scraping/crawl.py` embeds each
  episode's whole summary as one vector, but `all-MiniLM-L6-v2` reads only the first 256 tokens
  (median summary ≈ 1,537 tokens), so ~85% of the text is silently dropped. That's why the
  app's own example query, "episode where Buffy dies", can't find `s05e22` *The Gift*.
- [ ] **Switch to chunk-level indexing:** one vector per summary paragraph, prefixed with the
  episode title, scored max-over-chunks (~1,837 vectors, 2.7 MB).
- [ ] **Switch the embedding model.** Chunking plus `bge-small-en-v1.5` raises R@5 on the
  known-answer queries from 50% to 80% (MRR 0.399 → 0.624). Neither change helps much alone.
  Details: `docs/SEARCH_ACCURACY.md`.
- [x] **Replace ChromaDB with brute-force cosine search.** Done 2026-10-01: exact cosine over a
  NumPy matrix (`app/services/vector_store.py`). ChromaDB's approximate index was also
  *non-deterministic* — two runs of the old engine disagreed on 7–9 of 23 baseline rankings —
  so the baseline was re-recorded on the exact engine, which is stable run to run.
- [ ] **Choose the hosted query embedder.** Deployment can't host a model, so queries must be
  embedded by a hosted API using the same model as the corpus. Run each candidate through
  `scripts/eval_retrieval.py` before choosing.
- [ ] **Grow the known-answer set** in `scripts/eval_retrieval.py` beyond 20 queries;
  differences under ~10 points are currently noise.

### Repository hygiene

- [ ] **Remove `app/dump.rdb`** from git: a stray 2023 Redis dump in a public repo.
- [x] **Fix `.github/workflows/ci.yml`.** Done 2026-10-01: rewritten — see
  [Security and CI/CD](#security-and-cicd).
- [x] **Pin frontend dependencies exactly.** Done 2026-10-01, together with the upgrades that
  cleared all 66 frontend advisories (`npm audit`: 0): Vite 5→8, React Router 6→7,
  ESLint 8 (end-of-life)→10, typescript-eslint 6→8, axios 1.20.
- [ ] **Remove the duplicate health routes.** `/health` and `/health/model` are defined in
  both `app/api/main.py` and `app/api/api.py`.
- [ ] **Finish the data-layout migration** to `raw/` / `derived/` / `db/`; `.gitignore` still
  carries the legacy paths "during transition".
- [ ] **Clean up local leftovers:** the 819 MB `venv/` inside the project (rebuilt by
  `./init.sh`), 11 backup snapshots in `app/data/`, `app.log` / `app/app.log`, and
  `.DS_Store` files. None are tracked; they slow down workspace-wide searches and backups.
- [x] **Add real tests.** Done 2026-10-01: 66 pytest tests (see [Testing](#testing)), runnable
  without a server.

### Security fixes made along the way (2026-10-01)

- [x] The embedding model was fetched from Hugging Face at the moving `main` revision on every
  start; it is now pinned to commit `1110a24…` and loaded only via `app/services/embedder.py`.
- [x] HTTP 500 responses returned raw exception text (paths, library errors) to clients; they now
  return a generic message and log the detail server-side.
- [x] `/api/search` accepted unbounded input; `query` is capped at 500 characters, `limit` at
  1–50, `season` at 1–7 (out-of-range returns 422).
- [x] CORS sent `allow_credentials=True` though the app has no cookies or auth; now off.
- [x] The root logger ran at DEBUG in production, logging every outbound HTTP call; now INFO.
- [x] Four dead modules (Redis-era `embed*.py`, `data_pipeline.py`) removed, taking `aiohttp`
  and its advisories with them.
- [x] `data_loader.py` passed the data directory as the *model name* to `EmbeddingService`.
- [x] Frontend d3 force graphs mutated react-query's cached data in place, and the theme network
  rendered circles from a different array than the simulation moved (so nodes never moved);
  both now simulate typed copies.

### Frontend

- [ ] **Migrate Tailwind 3 → 4** before 2026-11-01. Removes the `braces` advisory accepted in
  `frontend/audit-exceptions.json`. Use `npx @tailwindcss/upgrade@<exact version>`, then check
  every view in a browser: v4 renames classes (`shadow-sm`→`shadow-xs`, `rounded`→`rounded-sm`)
  and changes `border`/`ring` defaults.

### Documentation

- [ ] **Delete or rewrite `PROJECT_STATUS.md`.** It still says only Season 1 is ingested;
  all 7 seasons are.
- [ ] **Merge the two roadmaps.** `ROADMAP.md` and `docs/ROADMAP.md` overlap; only the
  `docs/` one has been kept up to date.
- [ ] **Update `docs/DATA_PIPELINE.md`.** It describes the old single-season flow.
- [ ] **Refresh `docs/PROJECT_DOSSIER.md`.** Its repo-state section (2026-09-08) is
  out of date; the grid feature it calls uncommitted was committed in `1592660`.
- [ ] **Fix the clone URL** under Installation (`yourusername` → `pieteradejong`).
- [ ] **Add a project `CLAUDE.md`** with exact commands and gotchas for AI assistants.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

The **code** in this project is licensed under the MIT License - see the LICENSE file for details.

The **episode datasets** are derived from the [Buffyverse Wiki](https://buffy.fandom.com/) and
remain under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/), which requires
attribution and share-alike on any redistribution. See [NOTICE.md](NOTICE.md) for the full
statement and what it means if you reuse the data.



