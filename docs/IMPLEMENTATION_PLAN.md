# TV Show Chat - Implementation Plan (Q4 2025)

This plan captures the remaining engineering work now that the core ChromaDB-based search pipeline and frontend integration are online.

---

## Phase 0 (Completed)

- ✅ Standardized on Python 3.12 across all tooling (`init.sh`, `run.sh`, `test.sh`)
- ✅ Migrated vector search to ChromaDB with persistent storage
- ✅ Unified `/api/search` response for the frontend
- ✅ Added crawler/status CLI and automated pipeline integrity checks
- ✅ Consolidated documentation (architecture, roadmap, testing)

---

## Phase 1 – Multi-Season Data Ingestion

| Task | Owner | Acceptance Criteria |
| --- | --- | --- |
| Extend crawler to Seasons 1–7 (`app/services/scraping/crawl.py`) | Backend | `scripts/scrape_episodes.py --all --force` produces JSON with keys `season_1` … `season_7` |
| Add per-season crawl option (`--season N`) | Backend | Command exits 0 and saves a new file for the requested season |
| Improve crawler logging and retry handling | Backend | Logs progress per season; failures bubble appropriate exit code |
| Introduce document-store re-import helper | Backend | CLI (or script flag) runs `BuffyDocumentStore.import_from_json` on latest content |
| Provide ChromaDB reindex command | Backend | CLI (or script flag) clears and repopulates collection; reports episode count |

---

## Phase 2 – Test & Verification Enhancements

| Task | Area | Acceptance Criteria |
| --- | --- | --- |
| Update `./test.sh` to assert full episode counts (~144) | Tooling | Pipeline integrity step fails if counts mismatch or seasons missing |
| Add guard rails for embeddings (`app/data/embeddings`) | Tooling | Script checks for matching season files / counts |
| Optional: add frontend build check (`npm run build`) | Frontend | Test suite exits non-zero if build fails |
| Expand `docs/TESTING_GUIDE.md` with new steps | Docs | Guide describes pipeline integrity assertions & expected outputs |

---

## Phase 3 – Quality & UX Improvements

| Task | Notes |
| --- | --- |
| Incremental crawling (skip existing seasons unless `--force`) | Requires tracking most recent content per season |
| API endpoints for reindex / stats | Convenience wrappers once CLI flow is stable |
| Frontend polish (loading states, richer result metadata) | Improves perceived latency with larger dataset |
| Performance benchmarking with all seasons | Capture baseline latency for search & crawler |

---

## Long-Term Backlog

- Automated nightly crawl & reindex job (cron or GitHub Actions)
- Multi-show support (parameterize content source)
- Chat UX iteration once search quality validated at scale
- Deployment packaging (Docker, environment-driven config)

---

## Success Metrics

- ChromaDB collection reports same episode count as content/document store (via `/api/test`)
- `./test.sh` passes after multi-season ingestion on a clean workspace
- README + docs describe ingestion/reindex flow accurately
- Frontend remains responsive (<1s query time) with full dataset
