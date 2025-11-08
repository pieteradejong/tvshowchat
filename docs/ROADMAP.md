# Roadmap

## Current Snapshot (November 2025)

- ✅ ChromaDB-backed search is live and stable (Season 1 data loaded)
- ✅ Backend `/api/search` response matches the frontend contract
- ✅ Frontend search + chat prototype work against the unified API
- ✅ `./test.sh` covers health checks, search smoke tests, crawler status, and pipeline integrity counts
- ⚠️ Multi-season data ingestion still pending (currently only Season 1)
- ⚠️ Manual re-import / reindex helpers are limited
- ⚠️ Automated frontend build/test pipeline not yet implemented

---

## Completed Milestones

1. **API Alignment**
   - Removed duplicate `/api/search` implementations
   - Fixed `/api/test` sample episode handling and stats output
   - Updated frontend components (`Search.tsx`, `ChatWindow.tsx`) for the new response shape

2. **Crawler & Pipeline Diagnostics**
   - Added `scripts/scrape_episodes.py` with `--status`/`--all` modes
   - Integrated crawler status + pipeline integrity verification into `./test.sh`
   - Documented testing workflow (`docs/TESTING_GUIDE.md`) and pipeline overview (`docs/DATA_PIPELINE.md`)

3. **Docs & Tooling Refresh**
   - Consolidated architecture diagrams into `ARCHITECTURE.md`
  - Created `docs/ROADMAP.md` as the single source for planning
   - Added README table of contents and documentation index for easier onboarding

---

## Focus Area: Multi-Season Pipeline Expansion

### Goals
- Scrape and ingest Seasons 1–7
- Re-import document store + regenerate/refresh ChromaDB collections
- Extend automated tests to assert the larger dataset

### Plan
1. **Crawler Enhancements**
   - Update `app/services/scraping/crawl.py` to iterate all season tables
   - Support `scripts/scrape_episodes.py --season N` for targeted updates
   - Improve logging / progress output for long runs

2. **Ingestion Helpers**
   - Add CLI entry points to rerun `BuffyDocumentStore.import_from_json` and `_populate_chromadb()`
   - Provide `--reindex` option to rebuild embeddings or purge stale ChromaDB data

3. **Automated Testing Upgrades**
   - Update `./test.sh` integrity checks to expect the full episode count (~144)
   - Ensure API stats enumerate all seasons; fail fast if any are missing
   - (Optional) Add frontend build smoke test (`npm run build`)

4. **Documentation Updates**
   - Record new usage instructions in README + `docs/DATA_PIPELINE.md`
   - Note season coverage/status in `docs/ROADMAP.md`

---

## Backlog / Nice-to-Haves

- Incremental crawling (only fetch seasons missing from `app/content/`)
- Automated nightly crawl and reindex script
- Frontend UX polish (loading states, improved context display)
- Chat UX evolution once semantic search is fully scoped
- Performance benchmarking with the full dataset

---

## Success Criteria

- `scripts/scrape_episodes.py --status` reports Seasons 1–7 with correct episode counts
- Document store (`app/data/episodes`) contains seven season files and matching embeddings
- ChromaDB collection `buffy_episodes` reports the same total count via `/api/test`
- `./test.sh` passes and highlights the expanded dataset in the summary
- README and docs clearly describe how to ingest and verify all seasons
