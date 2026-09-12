# tvshowchat — Project Dossier

_Snapshot taken 2026-09-08. Everything below was verified against the working tree and
`git` at that date; where a claim comes from an existing doc rather than from the code,
it says so._

This is the "buffy project": the repo is named `tvshowchat`, but the only series it
carries data for is *Buffy the Vampire Slayer*. Nothing in the workspace is named
`buffy`, which is why it doesn't turn up under that name.

---

## 1. Identity

| Field | Value |
|---|---|
| Path | `projects/tvshowchat` |
| Remote | `git@github.com:pieteradejong/tvshowchat.git` |
| Visibility | **Public** |
| Description (GitHub) | "get answers to questions about tv shows based on vector embeddings" |
| Archived | No |
| License | MIT — `Copyright (c) 2023 Pieter de Jong` (matches the canonical name convention) |
| Last pushed | 2025-12-11 |
| Disk footprint | 1.1 GB total |

## 2. What it is

Semantic search and a chat/explore UI over *Buffy the Vampire Slayer* episode content.
Episode text is scraped from a fan wiki, embedded with a local sentence-transformer
model, and stored in a persistent ChromaDB collection (`buffy_episodes`). A FastAPI
backend serves search plus a growing set of derived-data endpoints; a React/Vite
frontend renders search, chat, and several visualization modes (timeline, character
sparklines, experiments, "reminiscence" views, and an in-progress series grid).

## 3. Stack

**Backend** (`requirements.txt`, pinned exactly)
- Python 3.12 (`runtime.txt` → `python-3.12.0`)
- FastAPI 0.104.1 + uvicorn 0.24.0
- ChromaDB 0.4.22
- sentence-transformers 2.5.1 / torch 2.2.1 / numpy 1.26.4
- Embedding model: `all-MiniLM-L6-v2`, vendored under `app/models/`
- Scraping: beautifulsoup4, lxml, aiohttp, requests, tenacity, ratelimit
- Dev: pytest 7.4.3, black 23.11.0, ruff 0.1.6, mypy 1.7.1

**Frontend** (`frontend/package.json`, caret ranges — not pinned)
- React 18 + TypeScript 5.3 + Vite 5
- TanStack React Query 5, axios, react-router-dom 6
- d3 7.9 (all the visualization work), Tailwind 3.4, Headless UI, Heroicons, zod

Note: the backend follows the workspace exact-pinning convention; the frontend does not.

## 4. Repo state (as of 2026-09-08)

- Current branch: **`feat/series-ux-polish`** (tracks `origin/feat/series-ux-polish`)
- Branches: `main`, `feat/series-ux-polish` — both exist on the remote
- `feat/series-ux-polish` is **2 commits ahead of `main`**, and **0 commits behind `origin/main`**
- Nothing unpushed on the current branch
- Last commit: `b12481f` (2025-12-11) "Add grid visualization brainstorming and implementation guide"

Recent history:

```
b12481f Add grid visualization brainstorming and implementation guide
370155f feat: Add reminiscence visualization features
620d623 feat(vis): add v1 series visualization (timeline, sparklines, detail)
a4a5a0b Consolidate UX to intent-based tabs: Search + Explore
025f397 Improve Chat and Use Cases UI layout and visual distinction
```

### Uncommitted work — 11 modified, 4 untracked

This is a coherent, unfinished feature: **the Series Grid visualization**.

Modified (`+183 / -38`):

```
.gitignore                                                  +17
app/api/routes/series.py                                    +74
docs/ROADMAP.md                                             +49
frontend/src/App.tsx                                        +17/-1
frontend/src/components/TimelineView.tsx                     ~1
frontend/src/components/experiments/EpisodeSimilarityMap.tsx
frontend/src/components/experiments/TemporalArcExplorer.tsx
frontend/src/components/experiments/ThemeCooccurrenceMatrix.tsx
frontend/src/components/reminiscence/CharacterMomentsTimeline.tsx
frontend/src/components/reminiscence/QuoteExplorer.tsx
frontend/src/components/reminiscence/SeasonComparison.tsx
```

Untracked (676 lines of new code, none of it committed anywhere):

```
app/services/grid_data.py                       210 lines
frontend/src/services/grid.ts                    58
frontend/src/services/seriesGridModel.ts        113
frontend/src/components/grid/GridCell.tsx        67
frontend/src/components/grid/GridView.tsx        99
frontend/src/components/grid/SeriesGrid.tsx     129
```

The `.gitignore` change is a real design decision that isn't recorded anywhere else: it
introduces a **raw / derived / db** data layout (`app/data/raw/`, `app/data/derived/`,
`app/data/db/chroma/`) and marks the existing `app/data/chroma`, `app/data/episodes`,
`app/data/embeddings` paths as "legacy paths (kept for backwards-compat during
transition)". That migration is started but not finished.

The `docs/ROADMAP.md` diff documents the grid initiative: Phase 1 marked complete
(SeriesGrid + GridCell components, `/api/grid/quotes-density`, `/api/grid/episodes`,
Grid tab, quote-density heatmap, precomputed `grid_episodes.json`), Phases 2–4 planned.

**Risk:** ~676 lines of untracked source has no backup outside this laptop. Committing it
to a branch is the single highest-value action on this repo.

## 5. Layout

```
tvshowchat/
├── app/
│   ├── api/
│   │   ├── main.py            # FastAPI app, health endpoints, router wiring
│   │   ├── api.py             # root/static/HTML routes
│   │   └── routes/
│   │       ├── search.py      # semantic search
│   │       ├── series.py      # series, reminiscence, grid data
│   │       └── experiments.py # exploratory analytics endpoints
│   ├── services/
│   │   ├── vector_store.py        (30K — the big one)
│   │   ├── series_vis_data.py     (17K)
│   │   ├── grid_data.py           (untracked, new)
│   │   ├── data_pipeline.py, data_loader.py
│   │   ├── embed.py, embed_all_seasons.py, embedding_service.py
│   │   ├── scraping/          # crawl.py — the fandom crawler
│   │   ├── pipeline/, storage/, embeddings/, search/
│   ├── content/btvs_all_seasons.json   # canonical dataset, 3.0 MB, tracked
│   ├── data/                  # chroma persistence, episodes, embeddings, backups
│   ├── models/all-MiniLM-L6-v2/        # embedding model
│   └── test/                  # test_api.py, test_crawl.py
├── frontend/src/
│   ├── App.tsx
│   ├── components/            # Search, Chat*, Explore, SeriesVis, TimelineView,
│   │                          # CharacterSparklines, experiments/, reminiscence/, grid/
│   └── services/, types/, hooks/, utils/
├── scripts/                   # crawl.sh, scrape_episodes.py, init_data.py
├── docs/                      # see §10
├── init.sh, run.sh, run_frontend.sh, test.sh
├── Dockerfile, docker-compose.yml, render.yaml, .dockerignore
└── ARCHITECTURE.md, README.md, PROJECT_STATUS.md, ROADMAP.md, DEPLOYMENT*.md
```

## 6. API surface

All feature routers are mounted under `/api`; the root router is included last so it
doesn't shadow them.

**Health** (`app/api/main.py`)

| Endpoint | Purpose |
|---|---|
| `GET /health` | overall |
| `GET /health/redis` | Redis |
| `GET /health/chromadb` | ChromaDB |
| `GET /health/vector-store` | vector store |
| `GET /health/model` | embedding model |
| `GET /health/store` | document store |
| `GET /health/pipeline` | data pipeline |

**Search** (`app/api/routes/search.py`)

| Endpoint | Purpose |
|---|---|
| `POST /api/search` | the main semantic search |
| `GET /api/test-search` | canned search, used by `test.sh` |
| `GET /api/test` | system self-test |

**Series / reminiscence / grid** (`app/api/routes/series.py`)

| Endpoint | Purpose |
|---|---|
| `GET /api/series/episodes` | episode dataset for the timeline |
| `GET /api/series/character-arcs` | per-character arcs |
| `GET /api/reminiscence/quotes` | quote explorer |
| `GET /api/reminiscence/character-moments` | character moments timeline |
| `GET /api/reminiscence/season-comparison` | season comparison |
| `GET /api/grid/quotes-density` | **uncommitted** — quote counts per episode cell |
| `GET /api/grid/episodes` | **uncommitted** — unified precomputed grid data |

**Experiments** (`app/api/routes/experiments.py`)

| Endpoint | Purpose |
|---|---|
| `GET /api/experiments/character-relationships` | |
| `GET /api/experiments/theme-cooccurrence` | |
| `GET /api/experiments/episode-similarity` | |
| `GET /api/experiments/character-journey` | |
| `GET /api/experiments/temporal-arcs` | |

**Root** (`app/api/api.py`): `GET /`, `GET /vite`, `GET /vite.svg`, plus duplicate
`GET /health` and `GET /health/model` definitions that also exist in `main.py`.

## 7. Data

- **Canonical dataset:** `app/content/btvs_all_seasons.json` — 3.0 MB, tracked in git,
  a JSON object keyed `season_1` … `season_7`. All 144 episodes.
- **Source:** `https://buffy.fandom.com/` — `app/services/scraping/crawl.py` walks
  `wiki/List_of_Buffy_the_Vampire_Slayer_episodes` and follows per-episode links.
  Rate-limited (`ratelimit`) with retries (`tenacity`).
- **Grid geometry:** 7 seasons × up to 22 episodes — `12, 22, 22, 22, 22, 22, 22`.
- **Vector store:** ChromaDB collection `buffy_episodes`, persisted at
  `app/data/chroma` (47 MB, gitignored).
- **Backups:** `app/data/backup_YYYYMMDD_HHMMSS/` — **11 snapshot dirs**, 2.4–2.6 MB
  each, from 2025-11-08 through 2025-12-11. Gitignored (`app/data/backup_*/`), so
  they're pure local disk cost.

**What's actually tracked in git** (checked, because the directories are large):
- `app/models/` — only 10 files: configs, `tokenizer.json`, `vocab.txt`. The weights are
  excluded by `.gitignore` (`app/models/**/*.bin`, `**/*.pt`). Good — the 88 MB on disk
  is almost entirely untracked.
- `app/data/` — only three `.gitkeep` files. The 77 MB is untracked.
- `app/dump.rdb` **is tracked** — an 88-byte Redis dump from 2023 that shouldn't be in
  the repo.

Pipeline entry points:
```
./scripts/crawl.sh                                   # crawl seasons missing from btvs_all_seasons.json
python3.12 scripts/scrape_episodes.py --status       # crawler coverage report
python3.12 scripts/scrape_episodes.py --reindex-chroma  # rebuild the buffy_episodes collection
python3.12 scripts/init_data.py                      # initialize data dirs
```

## 8. Commands

```bash
./init.sh          # Python 3.12 venv, requirements, data dirs, download embedding model
./run.sh           # kills stale uvicorn, verifies env + data dirs, starts FastAPI on :8000
./run_frontend.sh  # npm install if needed, warns if backend is down, vite dev on :5173
./test.sh          # curl-driven suite: health, vector store, model, /api/test, searches
```

`run.sh` is not the `templates/` `run.sh <subcommand>` dispatcher — it takes no
arguments and only starts the backend. Frontend scripts live in `frontend/package.json`:
`dev`, `build` (`tsc && vite build`), `lint`, `format`, `type-check`, `preview`.

Service URLs: API `http://localhost:8000`, docs `/docs`, frontend `http://localhost:5173`.

Tests: `app/test/test_api.py`, `app/test/test_crawl.py`, plus a `tests/` tree with
`unit/` and `integration/` subdirs. `test.sh` is an HTTP smoke suite against a running
server, not a pytest runner.

## 9. Deployment

- **Target:** Render, via `render.yaml` blueprint — service `tvshowchat-api`, Docker
  runtime, `branch: main`, `plan: starter` (512 MB, with a commented-out note that
  `standard`/2 GB is recommended), `healthCheckPath: /health`, `autoDeploy: true`.
- `Dockerfile` + `docker-compose.yml` + `.dockerignore` present.
- Four separate deployment docs exist, three of which read as troubleshooting logs:
  `DEPLOYMENT.md`, `DEPLOYMENT_CHECKLIST.md`, `RENDER_BUILD_FIX.md`,
  `RENDER_COMMIT_ISSUE.md`, `SWITCH_TO_DOCKER.md`. Whether the deployment is currently
  live was not verified in this snapshot.

Memory pressure is the obvious constraint: torch + sentence-transformers + ChromaDB on a
512 MB starter plan is tight, which is likely what the RENDER_* docs are about.

## 10. Documentation inventory

| File | Date | Notes |
|---|---|---|
| `README.md` | 2025-11-15 | 12K, full ToC. Claims all 7 seasons ingested and verified. |
| `ARCHITECTURE.md` | 2025-11-08 | |
| `PROJECT_STATUS.md` | 2025-11-08 | **Stale** — see §11 |
| `ROADMAP.md` (root) | 2025-12-11 | 14K. "complete dataset (all 7 seasons), pipeline verified" |
| `docs/ROADMAP.md` | 2025-12-12 | 12K. Duplicate roadmap, modified but uncommitted |
| `docs/DATA_PIPELINE.md` | 2025-11-08 | `docs/ROADMAP.md` flags it as describing the old single-season flow |
| `docs/GRID_VISUALIZATION_IDEAS.md` | 2025-12-11 | 14 visualization concepts |
| `docs/GRID_IMPLEMENTATION_GUIDE.md` | 2025-12-11 | 19K technical spec for the grid |
| `docs/REMINISCENCE_VIZ_IDEAS.md` | 2025-11-16 | |
| `docs/VIS_ROADMAP.md` | 2025-11-16 | v1/v2/v3 visualization scope |
| `docs/IMPLEMENTATION_PLAN.md` | 2025-11-08 | |
| `docs/TESTING_GUIDE.md` | 2025-11-08 | |
| `docs/architecture.html`, `docs/mermaid.html` | | rendered diagrams |
| `blog.txt`, `.cursorrules` | 2025-05-28 | |

## 11. Known problems

1. **676 lines of untracked source.** The grid feature exists only in the working tree.
   No branch, no remote, no backup.
2. **`PROJECT_STATUS.md` contradicts everything else.** It says "Only Season 1 is
   currently ingested", "Data coverage: **15%** (Season 1 of 7)". The README, the root
   `ROADMAP.md`, and `docs/ROADMAP.md` all say Seasons 1–7 are loaded and `test.sh`
   validates seven-season coverage. The status file is the stale one and misstates the
   project by a factor of seven.
3. **Two roadmaps.** `ROADMAP.md` and `docs/ROADMAP.md` are different documents with
   overlapping scope; only the `docs/` one is being updated.
4. **`docs/DATA_PIPELINE.md` is known-stale** — flagged in `docs/ROADMAP.md` itself.
5. **Unfinished data-layout migration.** The `raw`/`derived`/`db` split is in the
   uncommitted `.gitignore` with the old paths labelled "legacy … during transition".
6. **`app/dump.rdb` is tracked** — a stray 2023 Redis dump in a public repo.
7. **Duplicate health routes** — `/health` and `/health/model` are defined in both
   `app/api/main.py` and `app/api/api.py`.
8. **819 MB `venv/` inside the project dir**, plus 11 gitignored backup snapshots
   (~27 MB) and a 104 MB `.git`. The venv is the bulk of the 1.1 GB; it's disposable
   (`./init.sh` rebuilds it) but it makes every workspace-wide `find`/`grep`/backup
   slower.
9. **`app/app.log` (96 KB) and root `app.log`** are on disk; log paths are gitignored.
10. **Frontend deps use caret ranges** while the backend pins exactly.

Nothing sensitive was found: no `.env` files tracked, no credentials in the manifests,
the only outbound host in the crawler is `buffy.fandom.com`, and the vendored model
files come from the published `all-MiniLM-L6-v2` distribution.

---

## 12. Public web resources about Buffy the Vampire Slayer

Catalogued 2026-09-08. This is the significant, currently-reachable public surface — not
an exhaustive crawl of everything that mentions the show. Grouped by what each is
actually good for as a data source. **Only `buffy.fandom.com` is used by this project
today** (`app/services/scraping/crawl.py`).

### Primary source — currently used

| Site | URL | What it gives you |
|---|---|---|
| Buffyverse Wiki (Fandom) | https://buffy.fandom.com/ | The most comprehensive fan encyclopedia for Buffy + Angel. Episode articles, characters, locations, and a [Category:Transcripts](https://buffy.fandom.com/wiki/Category:Transcripts). This repo's crawler enters at [List of episodes](https://buffy.fandom.com/wiki/List_of_Buffy_the_Vampire_Slayer_episodes). |

### Transcripts and scripts

| Site | URL | Notes |
|---|---|---|
| BuffyWorld | http://www.buffyworld.com/ | Transcripts, screencaps and **original screenplays** for every Buffy and Angel episode — the screenplays differ from what aired, so script-vs-transcript is a real comparison axis. ⚠️ **Currently does not resolve**: the domain is still registered (Njalla nameservers) but publishes no A record for the apex or `www` as of 2026-09-08. Historical copies are in the Wayback Machine. |
| Buffyverse Wiki transcripts | https://buffy.fandom.com/wiki/Category:Transcripts | Wiki-hosted transcripts, same source the crawler already reaches. |
| AleXander's Transcripts | https://fanlore.org/wiki/AleXander%27s_Transcripts | The canonical fan transcripts, begun 1997, now mirrored across fansites. Fanlore documents the provenance — Fox issued a C&D to the original host in 1999, so mirrors vary in completeness. |
| Angelfire transcript mirror | https://www.angelfire.com/ny4/amai/Buffy/rscripts.html | Old per-season mirror. Fragile, but a fallback if a primary is down. |
| Internet Archive — script books | https://archive.org/details/buffyvampireslay02whed · https://archive.org/details/buffyvampireslay0000unse_q2u9 | Scans of the officially published *Buffy the Vampire Slayer: The Script Book* volumes (borrowable, not raw text). |
| Original 1992 film script | https://buffy.fandom.com/wiki/Buffy_the_Vampire_Slayer_(film)/Original_script | Whedon's pre-rewrite film script. |

### Structured episode metadata

| Site | URL | Notes |
|---|---|---|
| Wikipedia — episode list | https://en.wikipedia.org/wiki/List_of_Buffy_the_Vampire_Slayer_episodes | 144 episodes across 7 seasons plus the unaired pilot. Clean tables, per-season articles (e.g. [season 2](https://en.wikipedia.org/wiki/Buffy_the_Vampire_Slayer_season_2)) and per-episode articles with production/reception sections. |
| Wikidata | https://www.wikidata.org/wiki/Q934759 | Machine-readable entity graph — queryable via SPARQL, good for reconciling IDs across sources. |
| TMDB | https://www.themoviedb.org/tv/95-buffy-the-vampire-slayer | Free API with episode, cast, crew, stills and overviews. The most practical structured backfill for this project. |
| TheTVDB | https://thetvdb.com/series/buffy-the-vampire-slayer | Episode/air-date authority; API requires a key. |
| epguides | https://epguides.com/BuffytheVampireSlayer/ | Plain titles-and-air-dates guide, trivially parseable. |
| `btvs-angel-api` | https://github.com/Thatskat/btvs-angel-api | A small third-party API returning episode/cast/crew for Buffy *and* Angel — name, season, episode number, air date, description. Worth reading for its data shape even if not consumed directly. |
| Vrya's Buffyverse Database | http://vrya.net/bdb/ | Quotes, character arcs and AKA lists — closest external analogue to this project's own character-arc and quote endpoints. ⚠️ Returns Cloudflare **526** (bad origin certificate) on probe; may need plain HTTP or the Wayback Machine. |
| TV Database Wiki | https://tvdatabase.fandom.com/wiki/Buffy_the_Vampire_Slayer | Secondary Fandom mirror. |
| Ultimate Pop Culture Wiki | https://ultimatepopculture.fandom.com/wiki/List_of_Buffy_the_Vampire_Slayer_episodes | Another Fandom mirror of the episode list. |

Subtitle corpora (OpenSubtitles and similar) would be the highest-fidelity dialogue
source with timecodes, but no Buffy-specific, clearly-licensed subtitle dataset was
found in this pass — treat that as an open question rather than an available source.

### Scholarly

| Site | URL | Notes |
|---|---|---|
| *Slayage: The International Journal of Buffy+* | https://slayage.ejournals.una.edu/about | Peer-reviewed journal, founded January 2001 by David Lavery and Rhonda V. Wilcox. Renamed several times; current title since 2021. |
| Slayage open-access archive | https://ir.una.edu/collection/e9b56410-21e0-4f25-8e06-ea5a1d96ecbd | Full back catalogue, open access, at the University of North Alabama. |
| Association for the Study of Buffy+ | https://buffystudies.org/ | The journal's parent organization; conferences and CFPs. |
| Wikipedia — Buffy studies | https://en.wikipedia.org/wiki/Buffy_studies | Overview of the field, which spans sociology, anthropology, philosophy and religious studies. |
| Slayage legacy archive | http://offline.buffy.de/www.slayage.tv/index.html | Mirror of the original slayage.tv. |

### Fan community and commentary

| Site | URL | Notes |
|---|---|---|
| Buffy-Boards | https://buffy-boards.com/ | Active general discussion forum. |
| Fan Forum — Buffy & Angel | https://www.fanforum.com/f11/ | Long-running vBulletin board. |
| SlayAlive | https://slayalive.com/ | Forum; its ["useful Buffy reference sites" thread](https://slayalive.com/archive/index.php/t-124.html) is a curated link list worth mining. |
| BuffyForums | https://x.com/BuffyForums | Currently offline for a refresh; announcements via X. |
| *Buffering the Vampire Slayer* | https://www.bufferingcast.com/ · [Wikipedia](https://en.wikipedia.org/wiki/Buffering_the_Vampire_Slayer) | The best-known episode-by-episode podcast (Jenny Owen Youngs, Kristin Russo). A spoiler-inclusive rewatch series, *Once More, With Spoilers*, was announced 2024-11-07. |
| Podcast directories | https://podcast.feedspot.com/buffy_the_vampire_slayer_podcasts/ · https://www.millionpodcasts.com/buffy-the-vampire-slayer-podcasts/ | Aggregated lists of Buffy podcasts. |
| Fanlore | https://fanlore.org/ | Fandom-history wiki; the reliable place for provenance on fan artifacts (see the transcripts entry above). |

### Reachability check, 2026-09-08

Each link was probed from this machine. Confirmed reachable (HTTP 200): `buffy-boards.com`,
`buffystudies.org`, `bufferingcast.com`, `epguides.com`, `github.com/Thatskat/btvs-angel-api`.
Confirmed broken: `buffyworld.com` (no DNS A record), `vrya.net/bdb/` (Cloudflare 526).
**Inconclusive** — connection refused instantly, which is consistent with this sandbox's
outbound network restrictions rather than the sites being down, so verify manually before
concluding anything: `slayage.ejournals.una.edu`, `www.angelfire.com`. Fandom, Wikipedia,
Wikidata, TMDB, TheTVDB, Fanlore and Internet Archive were not probed directly; they were
returned live by search on the same date.

### Notes on using these

- **Licensing.** Fandom wikis are CC BY-SA — derived datasets carry attribution and
  share-alike obligations. Transcripts and screenplays are of murkier status; the 1999
  Fox C&D against the original transcript host is the cautionary precedent. This repo is
  public and MIT-licensed while `btvs_all_seasons.json` (3.0 MB of scraped wiki content)
  is committed into it — the license of that data is not currently stated anywhere in
  the repo, which is worth resolving.
- **Be a good citizen.** The existing crawler already rate-limits and retries; keep that
  for any new source, and respect each site's `robots.txt`.
- **Scrape once, cache forever.** The canonical-JSON-plus-derived-artifacts pattern this
  project already uses is the right shape; add new sources as new raw files under the
  planned `app/data/raw/`, not as live fetches.

---

_Generated by Claude Code. Facts verified against the working tree at
`feat/series-ux-polish` @ `b12481f` with 15 uncommitted changes; external links verified
by web search on 2026-09-08._
