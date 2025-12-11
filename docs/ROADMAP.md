# Roadmap

## Current Snapshot (November 2025)

- ✅ ChromaDB-backed search is live and stable (Season 1 data loaded)
- ✅ Backend `/api/search` response matches the frontend contract
- ✅ Frontend search + chat prototype work against the unified API
- ✅ Crawler now generates `btvs_all_seasons.json` (Seasons 1–7) and incremental wrapper `scripts/crawl.sh` handles missing-season detection
- ✅ `./test.sh` now validates seven-season coverage end-to-end
- ⚠️ README and `docs/DATA_PIPELINE.md` describe the old single-season ingestion flow
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

3. **Pipeline Helpers**
   - Added document-store import command (`scripts/scrape_episodes.py --import-latest`)
   - Added Chroma reindex command (`scripts/scrape_episodes.py --reindex-chroma`)
   - Extended `./test.sh` to exercise import and reindex flows

4. **Docs & Tooling Refresh**
   - Consolidated architecture diagrams into `ARCHITECTURE.md`
   - Created `docs/ROADMAP.md` as the single source for planning
   - Added README table of contents and documentation index for easier onboarding

---

## Focus Area: Multi-Season Pipeline Expansion (in progress)

### Goals
- Scrape and ingest Seasons 1–7
- Re-import document store + regenerate/refresh ChromaDB collections
- Extend automated tests to assert the larger dataset

### Plan
1. **Crawler Enhancements** ✅
   1.1 Update `app/services/scraping/crawl.py` to iterate all season tables and handle varying episode counts (12 vs 22)  
   1.2 Add per-season crawl flag `--season N` (and `--force`) to `scripts/scrape_episodes.py`  
   1.3 Improve logging/progress output for long runs and add basic retry handling  
   1.4 Capture crawl metadata (season totals, timestamps) for later integrity checks  
   _Delivered via the unified crawl workflow and latest `btvs_all_seasons.json` artifact._

2. **Ingestion Helpers**
   2.1 Add CLI entry (or script flag) to rerun `BuffyDocumentStore.import_from_json` on latest content snapshot
   2.2 Provide a `--reindex` or `--refresh-chroma` option that clears/represents the Chroma collection
   2.3 Ensure embeddings are regenerated only when missing and reuse cached vectors otherwise
   2.4 Expose helper to inspect collection stats (total episodes, season coverage)

3. **Automated Testing Upgrades** (in progress)
   3.1 ✅ Update `./test.sh` integrity checks to expect ~144 episodes and 7 seasons  
   3.2 ✅ Extend integrity step to validate `app/data/embeddings` counts alongside episodes  
   3.3 ✅ Ensure `/api/test` returns season coverage list; fail if mismatched  
   3.4 (Optional) Add frontend build smoke test (`npm run build`) and surface errors clearly  
   _3.1–3.3 delivered via the enhanced multi-season validation in `test.sh` and tighter `/api/test` checks._

4. **Documentation Updates** (Next up)
   4.1 Update README quick-start with multi-season ingestion workflow (crawl → import → reindex)  
   4.2 Expand `docs/DATA_PIPELINE.md` with new CLI commands and season coverage notes  
   4.3 Refresh `docs/TESTING_GUIDE.md` expected outputs (full dataset) and troubleshooting tips  
   4.4 Capture crawl/import/reindex runbook in `docs/ROADMAP.md` for future automation

---

## Refactoring Priorities

### Data Organization: Separate Raw Data from Aggregated Stats

**Problem**: Currently, `season_stats.json` is stored alongside raw season data files (`season_*.json`) in `app/data/episodes/`, causing confusion and requiring defensive code to filter it out when iterating season files.

**Goal**: Establish clear separation between:
- **Raw/primary data**: Episode transcripts, metadata, embeddings
- **Derived/aggregated data**: Statistics, analytics, computed metrics

**Proposed Structure**:

```
app/data/
├── episodes/                    # Raw episode data only
│   ├── season_1.json
│   ├── season_2.json
│   └── ...
├── embeddings/                   # Raw embeddings only
│   ├── season_1_embeddings.json
│   └── ...
├── stats/                        # Aggregated/computed data
│   ├── season_stats.json
│   ├── character_arcs.json
│   ├── character_moments.json
│   ├── quotes.json
│   └── episodes.json            # Aggregated episode index
└── chroma/                       # Vector store (unchanged)
```

**Implementation Plan**:

1. **Directory Restructure**
   - Create `app/data/stats/` directory
   - Move `season_stats.json`, `character_arcs.json`, `character_moments.json`, `quotes.json`, `episodes.json` to `app/data/stats/`
   - Update `.gitignore` if needed

2. **Code Updates**
   - Update `app/services/series_vis_data.py` to write stats files to `app/data/stats/`
   - Update `app/api/routes/series.py` to read from `app/data/stats/`
   - Remove all defensive `season_stats.json` filtering code (no longer needed)
   - Update any hardcoded paths in scripts and services

3. **Documentation**
   - Update `docs/DATA_PIPELINE.md` with new directory structure
   - Update README if it references data locations
   - Document the distinction between raw data and derived stats

4. **Testing**
   - Update `test.sh` to verify stats directory structure
   - Ensure all stats endpoints still work after migration
   - Verify no regressions in data generation pipelines

**Benefits**:
- Clearer data organization and purpose
- Eliminates need for defensive filtering code
- Easier to understand what's raw vs. computed
- Better separation of concerns
- Easier to add new stat types without cluttering episode directory

**Related Issues**:
- Currently requires filtering `season_stats.json` in multiple places (vector_store.py, main.py, document_store.py, etc.)
- Risk of accidentally processing stats files as season data
- Unclear which files are source data vs. derived data

---

## Backlog / Nice-to-Haves

- Incremental crawling (only fetch seasons missing from `app/content/`)
- Automated nightly crawl and reindex script
- Frontend UX polish (loading states, improved context display)
- Chat UX evolution once semantic search is fully scoped
- Performance benchmarking with the full dataset

---

## UI Ideas

### Compact Search Results
- Collapse each result into a two-line summary (title + relevance blurb + score) with a “show details” toggle.
- Promote top match cues (theme chips, character badges, similarity heat bar) directly beside the title.
- Consider a list-and-preview layout: tight list on the left, expanded detail panel on the right.
- Provide hover tooltips or keyboard navigation to skim results quickly.

### Context Presentation
- Primary paragraph plus carousel or inline chips for supporting snippets instead of large text blocks.
- Icons/labels (🎵 musical, 💔 breakup) derived from detected themes for instant readability.
- Allow grouping/sorting by theme, character, or season to cluster related hits.

### Timeline / Arc Views
- Timeline mode for multi-episode queries (e.g., “Spike redemption”) with chronological markers.
- Threaded view where each episode is a node containing the key moment and optional expansion.
- Ability to pin episodes into a saved collection/timeline for later viewing.
- Provide a front-end–only prototype that derives episode ordering and grouping from existing `/api/search` data.

### Interaction Enhancements
- Hover previews that show the first sentence without expanding the card.
- Keyboard shortcuts to move between results and toggle details.
- Quick actions to add an episode to a watchlist or export a timeline.

_Captured @UI_IDEAS for future iteration._

---

## UI Initiative: Timeline Mode (Front-End First)

### Goals
- Give users a chronological view of multi-episode arcs entirely in the client.
- Keep existing `/api/search` response contract; no backend changes required for phase one.
- Provide a fast way to switch between list and timeline layouts.

### Phase 1 – Threaded Timeline Prototype
1. Add a list/timeline toggle within the Search tab (remember selection in component state).
2. Create a client-side transformer that groups search hits by episode (`season`, `episode`), sorts by airdate, and merges snippets.
3. Implement a vertical “thread” view: spine, nodes per episode, compact card with title, labels, primary snippet, expandable details.
4. Reuse existing chips (themes, characters) inside the timeline nodes for quick context.
5. Ensure responsiveness (mobile column vs. desktop thread) and keyboard navigation parity.

### Phase 2 – Enhanced Interactions (post-prototype)
- Add filters (by season, character) and per-node quick actions (save to watchlist / open in chat).
- Introduce optional horizontal timeline for wide screens.
- Support deep links (`?view=timeline&query=...`) and persistent layout preference.
- Explore arc detection callouts (e.g., “View as timeline” when multiple seasons detected).

---

## Success Criteria

- `scripts/scrape_episodes.py --status` reports Seasons 1–7 with correct episode counts
- Document store (`app/data/episodes`) contains seven season files and matching embeddings
- ChromaDB collection `buffy_episodes` reports the same total count via `/api/test`
- `./test.sh` passes and highlights the expanded dataset in the summary
- README and docs clearly describe how to ingest and verify all seasons
