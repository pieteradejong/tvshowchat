# Roadmap

## Current Status Assessment

### ✅ What Works:
1. **ChromaDB Integration** - 12 episodes loaded and searchable
2. **Backend API** - Search endpoints functional
3. **Frontend UI** - React components exist
4. **Document Store** - File-based storage working

### ❌ What Needs Fixing:
1. **API Route Conflict** - Two `/api/search` endpoints (different formats)
2. **Frontend-Backend Mismatch** - Response format doesn't match
3. **Crawler Not Integrated** - Manual only, not testable
4. **Data Pipeline Gaps** - Not fully automated
5. **Test Coverage** - Missing crawler and frontend tests

---

## Implementation Plan

### Phase 1: Fix API Response Format (Critical - Blocks Frontend)

**Problem:** Frontend expects array, but gets different format from different endpoints

**Tasks:**
1. Fix `/api/routes/search.py` to return correct format
2. Remove duplicate `/api/search` in `app/api/api.py` or make it consistent
3. Ensure response matches frontend `SearchResult` interface
4. Fix `/api/test` endpoint error (`'season'` key issue)

**Test:** `./test.sh` should verify search returns correct format

---

### Phase 2: Functional Crawler Integration

**Goal:** Make crawler testable and integrate into pipeline

**Tasks:**
1. Create crawler script: `scripts/scrape_episodes.py`
2. Add crawler health check endpoint: `/api/health/crawler`
3. Add crawler status endpoint: `/api/crawler/status`
4. Integrate into `init.sh` (optional, or keep manual)
5. Add data validation after scraping

**Test:** `./test.sh` should verify:
- Crawler can be invoked
- Crawler saves data correctly
- Data appears in document store
- Data appears in ChromaDB

---

### Phase 3: Data Saving & Loading Verification

**Goal:** Ensure complete data pipeline works end-to-end

**Tasks:**
1. Verify data saves correctly at each stage:
   - Content JSON → Document Store
   - Document Store → ChromaDB
2. Add data integrity checks
3. Add endpoint to verify data completeness
4. Add endpoint to trigger re-indexing

**Test:** `./test.sh` should verify:
- Data exists at each stage
- Episode counts match
- Embeddings are present
- ChromaDB has correct data

---

### Phase 4: Frontend Integration & Testing

**Goal:** Working frontend that can search and display results

**Tasks:**
1. Fix API response format to match frontend
2. Test frontend can call backend
3. Verify search results display correctly
4. Add frontend build check to `test.sh`
5. Test CORS is working

**Test:** `./test.sh` should verify:
- Frontend can be built
- Frontend can call API
- Search returns results
- Results display correctly

---

## Detailed Step-by-Step Plan

### Step 1: Fix API Response Format (30 min)

**Issue:** Frontend expects:
```typescript
interface SearchResult {
  season: number;
  episode: string;
  title: string;
  airdate: string;
  content_type: string;
  text: string;
  score: number;
  characters: string[];
  themes: string[];
  context: string;
}
```

**Current:** `/api/routes/search.py` returns this format ✅
**Problem:** `/api/api.py` also has `/api/search` with different format ❌

**Fix:**
1. Remove `/api/search` from `app/api/api.py` (keep only in routes)
2. Ensure `/api/routes/search.py` returns correct format
3. Fix `/api/test` endpoint to handle missing 'season' key

**Test:**
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query":"vampire","limit":2}' | python3.12 -m json.tool
```

---

### Step 2: Create Testable Crawler Script (1 hour)

**Create:** `scripts/scrape_episodes.py`

**Features:**
- Can scrape single season or all seasons
- Saves to content JSON
- Validates data
- Returns status/statistics
- Can be called from command line

**Usage:**
```bash
# Scrape Season 1
python scripts/scrape_episodes.py --season 1

# Scrape all seasons
python scripts/scrape_episodes.py --all

# Check status
python scripts/scrape_episodes.py --status
```

**Add API Endpoints:**
- `GET /api/crawler/status` - Check crawler status
- `POST /api/crawler/scrape` - Trigger scraping (optional)

---

### Step 3: Add Data Pipeline Tests to test.sh (30 min)

**Add to test.sh:**
1. **Crawler Test** - Verify crawler can run
2. **Data Integrity Test** - Verify data at each stage:
   - Content JSON files exist
   - Document store has episodes
   - ChromaDB has episodes
   - Counts match across all stages
3. **Frontend Build Test** - Verify frontend can build
4. **End-to-End Search Test** - Test full flow

---

### Step 4: Fix Frontend Integration (1 hour)

**Tasks:**
1. Verify API response format matches frontend
2. Test CORS configuration
3. Build frontend and verify it works
4. Test search from frontend
5. Add error handling

**Test:** Manual + automated via test.sh

---

### Step 5: Expand to All Seasons (After above works)

**Tasks:**
1. Run crawler for all 7 seasons
2. Verify all data loads correctly
3. Test search across all seasons
4. Performance testing

---

## Updated test.sh Structure

```bash
# 1. Health Endpoints (existing)
# 2. System State (existing)
# 3. Search Functionality (existing)
# 4. Vector Store State (existing)
# 5. Document Store (existing)

# 6. NEW: Crawler Test
# 7. NEW: Data Pipeline Integrity
# 8. NEW: Frontend Build Test
# 9. NEW: End-to-End Search Test
```

---

## Priority Order

1. **Fix API Response Format** (Blocks frontend)
2. **Add Crawler Tests** (Verify data pipeline)
3. **Fix Frontend Integration** (Complete user flow)
4. **Expand to All Seasons** (Scale up)

---

## Success Criteria

## Roadmap

### Pipeline Expansion (Multi-Season Support)

1. **Crawler Multi-Season Support**
   - Update `app/services/scraping/crawl.py` to iterate seasons 1–7
   - Adjust validation to handle season-specific episode counts (12 vs 22)
   - Expand `scripts/scrape_episodes.py` with `--season N` and improve `--all` logging

2. **Document Store Refresh CLI**
   - Add helper or CLI to re-run `BuffyDocumentStore.import_from_json` on latest content
   - Optionally add `--reindex` flag to clear and repopulate ChromaDB from disk

3. **ChromaDB Reindex Command**
   - Provide CLI command to reset collection and call `_populate_chromadb()`
   - Ensure embeddings are regenerated or reused correctly

4. **Test Suite Updates**
   - Update `test.sh` pipeline integrity checks for new total episode counts (all seasons)
   - Assert document store and API return all 7 season numbers

5. **Manual Verification & Documentation**
   - Scrape all seasons (`--all --force`), re-import, and reindex
   - Update README, TESTING_GUIDE, DATA_PIPELINE with multi-season instructions



✅ **Crawler:**
- Can scrape episodes successfully
- Saves data correctly
- Validates data
- Testable via `./test.sh`

✅ **Data Pipeline:**
- Content JSON → Document Store ✅
- Document Store → ChromaDB ✅
- All stages verifiable via `./test.sh`

✅ **Frontend:**
- Can search episodes
- Displays results correctly
- Error handling works
- Testable via `./test.sh`

✅ **Testing:**
- `./test.sh` verifies all components
- All tests pass
- Can verify end-to-end flow

