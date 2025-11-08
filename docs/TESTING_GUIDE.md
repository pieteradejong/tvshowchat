# Testing Guide - ChromaDB Integration

## Quick Start Testing

### Step 1: Start the Server
```bash
./run.sh
```

This will:
- ✅ Check Python environment
- ✅ Verify dependencies (including ChromaDB)
- ✅ Start FastAPI server
- ✅ Check health endpoints automatically

### Step 2: Watch for Success Indicators

When `./run.sh` runs, look for these in the output:

**✅ Good Signs:**
```
✅ ChromaDB directory found
✅ All required packages installed
✅ Server is running
✅ Vector store is healthy
```

**❌ Warning Signs:**
```
⚠️  ChromaDB directory not found
⚠️  Vector store is not healthy
❌ Server failed to start
```

### Step 3: Run Automated Tests

In a **new terminal** (keep the server running), run:
```bash
./test.sh
```

This automated test script performs the following checks:

#### 1. Health Endpoints
- **`/health`** - Overall system health check
- **`/health/vector-store`** - ChromaDB vector store health
- **`/health/model`** - Embedding model (SentenceTransformer) health

#### 2. System State
- **`/api/test`** - Comprehensive system test that:
  - Returns vector store statistics (episode count, seasons, collection info)
  - Retrieves a sample episode
  - Performs a test search query ("Buffy fights vampires")

#### 3. Search Functionality
- **`/api/test-search`** (default) - Tests search with default query "Willow uses magic"
- **`/api/test-search?query=Willow%20uses%20magic&limit=2`** - Tests custom search query

#### 4. Vector Store State
- Checks if `/health/vector-store` returns `"status": "healthy"`
- Verifies ChromaDB is operational

#### 5. Document Store Verification
- Checks if `app/data/episodes/` directory exists
- Counts season files (`season_*.json`)
- Checks if `app/data/chroma/` directory exists (ChromaDB data)

#### 6. Crawler Status
- Runs `scripts/scrape_episodes.py --status`
- Verifies crawler script is accessible
- Prints scraper/document store/ChromaDB summary

**Manual crawler usage:**
```bash
# Inspect pipeline status without modifying data
python3.12 scripts/scrape_episodes.py --status

# Force a re-crawl (Season 1 currently implemented)
python3.12 scripts/scrape_episodes.py --all --force
```

---

## Manual Testing Steps

### 1. Check Health Endpoints

```bash
# Overall health
curl http://localhost:8000/health | python3 -m json.tool

# ChromaDB health
curl http://localhost:8000/health/chromadb | python3 -m json.tool

# Vector store health
curl http://localhost:8000/health/vector-store | python3 -m json.tool

# Model health
curl http://localhost:8000/health/model | python3 -m json.tool
```

**Expected Response:**
```json
{
  "status": "healthy",
  "message": "ChromaDB is healthy"
}
```

### 2. Check System Stats

```bash
curl http://localhost:8000/api/test | python3 -m json.tool
```

**Look for:**
- `chromadb_episodes`: Should show number of episodes loaded (e.g., 12 for Season 1)
- `total_episodes`: Should match your episode count
- `test_search`: Should return results

**Expected Response:**
```json
{
  "status": "healthy",
  "vector_store": {
    "total_episodes": 12,
    "chromadb_episodes": 12,
    "collection_name": "buffy_episodes",
    "model": "all-MiniLM-L6-v2"
  },
  "test_search": {
    "query": "Buffy fights vampires",
    "results": [...]
  }
}
```

### 3. Test Search Functionality

```bash
# Simple test search
curl "http://localhost:8000/api/test-search?query=Willow%20uses%20magic&limit=3" | python3 -m json.tool

# Full search API
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Buffy and Angel romantic scenes", "limit": 5}' | python3 -m json.tool
```

**Expected Response:**
```json
[
  {
    "season": 1,
    "episode": "07",
    "title": "Angel",
    "airdate": "...",
    "content_type": "summary",
    "text": "...",
    "score": 0.85,
    "characters": ["Buffy", "Angel"],
    "themes": ["romance", "vampire"],
    "context": "Features characters: Buffy, Angel | Themes: romance, vampire"
  },
  ...
]
```

### 4. Check ChromaDB Data Directory

```bash
# Check if ChromaDB persisted data
ls -la app/data/chroma/

# Should see files like:
# - chroma.sqlite3 (or similar)
# - Various parquet files
```

---

## What to Look For

### ✅ Success Indicators:

1. **Startup Logs:**
   ```
   Populating ChromaDB from document store...
   Populated ChromaDB with 12 episodes
   Vector store (ChromaDB) initialized successfully
   ```

2. **Health Checks:**
   - All endpoints return `"status": "healthy"`
   - No errors in logs

3. **Search Results:**
   - Returns relevant episodes
   - Scores are reasonable (0.0-1.0)
   - Results include metadata (characters, themes, context)

4. **Performance:**
   - Search completes in <500ms
   - No timeouts

### ❌ Failure Indicators:

1. **Startup Errors:**
   ```
   Vector store initialization failed: ...
   ChromaDB query failed: ...
   ```

2. **Health Check Failures:**
   ```json
   {
     "status": "unhealthy",
     "error": "..."
   }
   ```

3. **Empty Search Results:**
   ```json
   []
   ```

4. **Missing Data:**
   - `chromadb_episodes: 0` when you have episodes
   - No ChromaDB files in `app/data/chroma/`

---

## Troubleshooting

### Issue: ChromaDB not populating

**Check:**
```bash
# Verify episode data exists
ls app/data/episodes/

# Check logs
tail -f app/logs/backend.log
```

**Fix:** ChromaDB auto-populates on first startup. If it doesn't:
1. Delete `app/data/chroma/` directory
2. Restart server
3. It will repopulate automatically

### Issue: Search returns empty results

**Check:**
```bash
# Verify ChromaDB has data
curl http://localhost:8000/api/test | python3 -m json.tool
# Look for chromadb_episodes > 0
```

**Fix:** If `chromadb_episodes` is 0, ChromaDB needs to be populated. Restart the server.

### Issue: Import errors

**Check:**
```bash
# Verify ChromaDB is installed
source venv/bin/activate
python -c "import chromadb; print('OK')"
```

**Fix:** If import fails:
```bash
./init.sh  # Reinstall dependencies
```

---

## Quick Test Commands

Copy-paste these to quickly verify everything works:

```bash
# 1. Health check
curl -s http://localhost:8000/health | python3 -m json.tool | grep -A 5 "chromadb"

# 2. Count episodes in ChromaDB
curl -s http://localhost:8000/api/test | python3 -m json.tool | grep "chromadb_episodes"

# 3. Test search
curl -s "http://localhost:8000/api/test-search?query=vampire&limit=2" | python3 -m json.tool | head -20

# 4. Check ChromaDB files
ls -lh app/data/chroma/ | head -5
```

---

## Expected First Run Behavior

**First time running `./run.sh`:**

1. **ChromaDB directory created** → `app/data/chroma/`
2. **ChromaDB collection created** → `buffy_episodes`
3. **Episodes loaded** → You'll see: "Populating ChromaDB from document store..."
4. **Data persisted** → Files created in `app/data/chroma/`
5. **Search works** → Can query episodes

**Subsequent runs:**

1. **ChromaDB loads existing data** → No repopulation needed
2. **Faster startup** → No data loading step
3. **Search works immediately**

---

## Success Criteria

✅ **Everything works if:**
- `./run.sh` completes without errors
- Health endpoints return "healthy"
- `chromadb_episodes` > 0 in stats
- Search returns relevant results
- No errors in logs

🎉 **You're ready to use the system!**

