# TV Show Chat - Roadmap & Implementation Plan

## Project Overview

**Goal**: Personal project / Portfolio piece hosted on Render  
**Status**: Core platform working, complete dataset (all 7 seasons), pipeline verified  
**Focus**: Complete dataset verification and robust pipeline testing

---

## Current Status (November 2025)

### ✅ Completed

**Core Platform**
- FastAPI backend with ChromaDB vector store
- React 18 + TypeScript frontend
- Semantic search across Buffy episodes
- Docker deployment configuration for Render

**Data & Pipeline**
- All 7 seasons scraped (144 episodes total)
- Content file: `app/content/btvs_all_seasons.json` (complete)
- Document store: `app/data/episodes/season_*.json` (all 7 seasons)
- Embeddings: `app/data/embeddings/season_*_embeddings.json` (all 7 seasons)
- ChromaDB: `app/data/chroma/` (13MB, populated with 144 episodes)
- Search verified across all 7 seasons

**Tooling**
- Crawler CLI: `scripts/scrape_episodes.py` (status, import, reindex)
- Test suite: `./test.sh` (health, search, pipeline integrity, cross-season search)
- Auto-import on startup (document store syncs from content JSON)

### ✅ Completed Milestones

1. **API Alignment**
   - Removed duplicate `/api/search` implementations
   - Fixed `/api/test` sample episode handling and stats output
   - Updated frontend components (`Search.tsx`, `ChatWindow.tsx`) for the new response shape

2. **Crawler & Pipeline Diagnostics**
   - Added `scripts/scrape_episodes.py` with `--status`/`--all`/`--season` modes
   - Integrated crawler status + pipeline integrity verification into `./test.sh`
   - Documented testing workflow (`docs/TESTING_GUIDE.md`) and pipeline overview

3. **Pipeline Helpers**
   - Added document-store import command (`scripts/scrape_episodes.py --import-latest`)
   - Added Chroma reindex command (`scripts/scrape_episodes.py --reindex-chroma`)
   - Extended `./test.sh` to exercise import and reindex flows

4. **Multi-Season Pipeline**
   - Crawler extended to all 7 seasons (144 episodes)
   - Document store contains all season files
   - ChromaDB populated with complete dataset
   - Search tested and verified across all seasons

5. **Documentation Consolidation**
   - Consolidated planning docs into single roadmap
   - Complete pipeline workflow documented
   - Health checks and monitoring added

---

## Data Pipeline

### Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. WEB SCRAPING (Manual)                                    │
│    app/services/scraping/crawl.py                           │
│    ↓                                                         │
│    buffy.fandom.com → BeautifulSoup → Validation            │
│    ↓                                                         │
│    app/content/btvs_all_seasons.json                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. CONTENT STORAGE                                           │
│    app/content/btvs_all_seasons.json (canonical snapshot)   │
│    - 7 seasons, 144 episodes                                │
│    - Includes embeddings, metadata, summaries               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. DOCUMENT STORE (Auto-import on startup)                  │
│    app/api/main.py → BuffyDocumentStore.import_from_json()  │
│    ↓                                                         │
│    app/data/episodes/season_*.json                          │
│    app/data/embeddings/season_*_embeddings.json             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. CHROMADB VECTOR STORE (Auto-populate if empty)           │
│    AdvancedVectorStore._populate_chromadb()                  │
│    ↓                                                         │
│    app/data/chroma/chroma.sqlite3                           │
│    app/data/chroma/{uuid}/*.bin                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. SEARCH API                                                │
│    AdvancedVectorStore.search_episodes()                     │
│    Uses ChromaDB for fast vector similarity search          │
└─────────────────────────────────────────────────────────────┘
```

### Pipeline Workflow

**Complete Refresh Workflow:**

1. **Crawl** (if needed):
   ```bash
   # Crawl any seasons missing from btvs_all_seasons.json
   ./scripts/crawl.sh
   
   # Or force a full re-crawl
   ./scripts/crawl.sh --all --force
   
   # Or crawl specific season
   ./scripts/crawl.sh --season 5
   ```

2. **Import to Document Store**:
   ```bash
   python3.12 scripts/scrape_episodes.py --import-latest
   ```
   This imports the latest content JSON into the document store, creating:
   - `app/data/episodes/season_*.json` (episode data)
   - `app/data/embeddings/season_*_embeddings.json` (cached embeddings)

3. **Reindex ChromaDB**:
   ```bash
   python3.12 scripts/scrape_episodes.py --reindex-chroma
   ```
   This rebuilds the ChromaDB collection from the document store.

4. **Verify**:
   ```bash
   # Check pipeline status
   python3.12 scripts/scrape_episodes.py --status
   
   # Run full test suite
   ./test.sh
   ```

**Auto-Import on Startup:**
- When the server starts, `app/api/main.py` checks if the document store is empty
- If empty, it automatically imports from `app/content/btvs_all_seasons.json`
- ChromaDB auto-populates if the collection is empty

### Pipeline Health Checks

**Status Command:**
```bash
python3.12 scripts/scrape_episodes.py --status
```

Shows:
- Content JSON file status and episode counts
- Document store season files and counts
- ChromaDB collection status and size

**API Health Endpoints:**
- `GET /health` - Overall application health
- `GET /health/vector-store` - ChromaDB status
- `GET /health/model` - Embedding model status
- `GET /api/test` - Complete system snapshot with episode counts

**Test Suite:**
```bash
./test.sh
```

Tests:
- Health endpoints
- System state (`/api/test`)
- Search functionality
- Search across all seasons
- Vector store state
- Document store integrity
- Pipeline integrity (all stages match)

---

## Current Priorities

### Priority 1: Dataset Verification ✅ COMPLETE

- ✅ All 7 seasons present in content JSON (144 episodes)
- ✅ All 7 seasons in document store (144 episodes)
- ✅ All 144 episodes in ChromaDB collection
- ✅ Search works across all seasons
- ✅ No missing or corrupted data

### Priority 2: Pipeline Testing ✅ COMPLETE

- ✅ `./test.sh` covers all pipeline stages
- ✅ Test for search across all seasons added
- ✅ Data integrity tests verify all stages
- ✅ Tests are idempotent and reliable
- ✅ Pipeline workflow documented

---

## Future Enhancements

### UI Improvements

**Timeline Mode**
- Chronological view of multi-episode arcs
- Frontend-only implementation (no backend changes)
- List/timeline toggle
- Episode grouping and sorting

**Compact Search Results**
- Two-line summary with "show details" toggle
- Theme chips and character badges
- List-and-preview layout
- Hover tooltips and keyboard navigation

**Context Presentation**
- Primary paragraph with supporting snippets
- Theme icons/labels for instant readability
- Grouping/sorting by theme, character, or season

**Interaction Enhancements**
- Hover previews
- Keyboard shortcuts
- Quick actions (watchlist, export timeline)

### Performance

- Search performance benchmarking
- Query optimization
- Caching strategies
- Lazy loading improvements

### Deployment

- Automated data refresh (optional)
- Monitoring and alerting
- Backup strategies
- Multi-show support (parameterize content source)

---

## Success Criteria

### Dataset Completeness ✅

- ✅ All 7 seasons present in content JSON (144 episodes)
- ✅ All 7 seasons in document store (144 episodes)
- ✅ All 144 episodes in ChromaDB collection
- ✅ Search works across all seasons
- ✅ No missing or corrupted data

### Pipeline Reliability ✅

- ✅ `./test.sh` passes all checks
- ✅ Pipeline workflow is documented
- ✅ Health checks show correct status
- ✅ Error recovery procedures documented
- ✅ Tests are idempotent and reliable

### Documentation Quality ✅

- ✅ Single consolidated roadmap document
- ✅ Complete pipeline workflow documented
- ✅ Troubleshooting guide available
- ✅ README reflects current state
- ✅ Portfolio-ready documentation

---

## Key Files

**Pipeline Components**
- `scripts/scrape_episodes.py` - Crawler and pipeline CLI
- `app/services/scraping/crawl.py` - Web scraping logic
- `app/services/storage/document_store.py` - Document store
- `app/services/vector_store.py` - ChromaDB integration
- `test.sh` - Automated test suite

**Documentation**
- `ROADMAP.md` - This file (consolidated planning)
- `ARCHITECTURE.md` - System architecture (technical reference)
- `README.md` - Quick start and overview
- `docs/TESTING_GUIDE.md` - Testing instructions
- `docs/DATA_PIPELINE.md` - Detailed pipeline documentation

---

## Progress Summary

- **Backend & Pipeline**: 95% (complete dataset, verified pipeline)
- **Frontend**: 75% (core flows work; UI improvements pending)
- **Data Coverage**: 100% (all 7 seasons, 144 episodes)
- **Automation & Tooling**: 90% (test harness complete, health checks added)
- **Documentation**: 90% (consolidated, workflow documented)

---

## Change Log

- **Nov 2025**: 
  - Completed multi-season ingestion (all 7 seasons, 144 episodes)
  - Verified dataset across entire pipeline
  - Enhanced test suite with cross-season search tests
  - Consolidated all planning docs into single ROADMAP.md
  - Added pipeline health check endpoint
  - Documented complete pipeline workflow

- **Oct 2025**: 
  - Migrated to ChromaDB, consolidated docs
  - Added crawler status & pipeline tests
  - Standardized scripts on Python 3.12
  - Fixed `/api/test`, aligned frontend components

---

## Notes

- `ARCHITECTURE.md` kept separate as technical reference
- Focus on portfolio-readiness (clear, concise, professional)
- Emphasize data completeness and pipeline reliability
- Document for future maintainability
- All 7 seasons verified and searchable

