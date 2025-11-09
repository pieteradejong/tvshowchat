# Data Pipeline Documentation

## Complete Data Flow

### 1. **Data Source: Web Scraping** ✅
**Location:** `app/services/scraping/crawl.py`

**Process:**
- Scrapes from `https://buffy.fandom.com/wiki/List_of_Buffy_the_Vampire_Slayer_episodes`
- Extracts episode data (summary, synopsis, quotes, trivia, production info, etc.)
- Generates embeddings using SentenceTransformer
- Validates data using `app/services/pipeline/validation.py`
- **Saves to:** `app/content/btvs_all_seasons.json`

**CLI Helper:**
```bash
# Inspect pipeline status (content/document store/ChromaDB)
python3.12 scripts/scrape_episodes.py --status

# Import latest crawl snapshot into document store
python3.12 scripts/scrape_episodes.py --import-latest

# Rebuild ChromaDB collection from document store
python3.12 scripts/scrape_episodes.py --reindex-chroma

# Force a full re-crawl (expensive)
python3.12 scripts/scrape_episodes.py --all --force
```

**Current State:**
- ✅ Scraping code exists and works (`scripts/scrape_episodes.py`)
- ✅ Unified content snapshot `btvs_all_seasons.json` contains Seasons 1–7 (144 episodes)
- ⚠️ Scraping / refresh is manual (not automated in `init.sh`)

---

### 2. **Content Storage** ✅
**Location:** `app/content/btvs_all_seasons.json`

**Format:**
```json
{
  "season_1": {
    "01": {
      "episode_number": "01",
      "episode_title": "Welcome to the Hellmouth",
      "episode_airdate": "March 10, 1997",
      "episode_summary": [...],
      "episode_synopsis": [...],
      "summary_embedding": [...],
      ...
    }
  }
}
```

**Current State:**
- ✅ Single canonical JSON file: `app/content/btvs_all_seasons.json`
- ✅ Covers seven seasons with per-episode metadata and embeddings
- ⚠️ No timestamped history retained (rerun crawl to refresh)

---

### 3. **Document Store (File-Based Backup)** ✅
**Location:** `app/services/storage/document_store.py`

**Process:**
- Loads from content JSON files via `import_from_json()`
- Converts to `EpisodeDocument` dataclass
- **Saves to:**
  - Episodes: `app/data/episodes/season_*.json`
  - Embeddings: `app/data/embeddings/season_*_embeddings.json`
- Creates automatic backups in `app/data/backup_*/`

**Auto-Import on Startup:**
- `app/api/main.py` checks if document store is empty
- If empty, finds latest content JSON file and imports it
- This happens automatically when server starts

**Current State:**
- ✅ Seasons 1–7 exported to `app/data/episodes/season_*.json` via `--import-latest`
- ✅ Matching embeddings created in `app/data/embeddings/season_*_embeddings.json`
- ✅ Auto-import on startup keeps document store in sync

---

### 4. **ChromaDB Vector Store** ✅
**Location:** `app/services/vector_store.py`

**Process:**
- `AdvancedVectorStore.__init__()` initializes ChromaDB
- `_populate_chromadb()` loads episodes from document store
- Reads episode data from `app/data/episodes/season_*.json`
- Reads embeddings from `app/data/embeddings/season_*_embeddings.json`
- Generates embeddings if missing
- **Saves to:** `app/data/chroma/` (SQLite + binary files)

**Auto-Population:**
- Checks if ChromaDB collection is empty (`collection.count() == 0`)
- If empty, automatically populates from document store
- Happens on first startup or when ChromaDB is cleared

**Current State:**
- ✅ ChromaDB initialized: `app/data/chroma/chroma.sqlite3`
- ✅ 144 episodes loaded in ChromaDB collection `buffy_episodes`
- ✅ Auto-population works after document-store import
- ✅ Search functionality uses ChromaDB

---

## Complete Pipeline Flow

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

---

## Current Pipeline Status

### ✅ **Working Components:**

1. **Scraping** ✅
   - Code exists and functional
   - Can scrape from buffy.fandom.com
   - Generates embeddings during scraping
   - Saves to content JSON files

2. **Content Storage** ✅
   - Canonical snapshot: `app/content/btvs_all_seasons.json`
   - Contains Seasons 1–7 (144 episodes + embeddings)

3. **Document Store** ✅
   - Auto-imports from content JSON on startup
   - Seasons 1–7 present under `app/data/episodes/season_*.json`
   - Embeddings saved in `app/data/embeddings/season_*_embeddings.json`

4. **ChromaDB** ✅
   - 144 episodes loaded in collection `buffy_episodes`
   - Auto-populates from document store
   - Search functionality works
   - File size grows with full dataset (~5.6 MB)

### ⚠️ **Gaps/Issues:**

1. **Scraping Not Automated**
   - Refresh is manual: `./scripts/crawl.sh` (or Python CLI flags)
   - Not integrated into `init.sh` or scheduled job

2. **Multiple Pipeline Implementations**
   - `app/services/data_pipeline.py` - Different implementation (not used?)
   - `app/services/data_loader.py` - References VectorStore (different from AdvancedVectorStore?)
   - `app/services/scraping/crawl.py` - Actual scraping code
   - Some confusion about which pipeline is active

---

## How to Complete the Pipeline

### Option 1: Scrape All Seasons (Recommended)

```bash
# Crawl any seasons missing from btvs_all_seasons.json
./scripts/crawl.sh

# Force a clean re-crawl (expensive)
./scripts/crawl.sh --all --force

# Then refresh downstream stores
python3.12 scripts/scrape_episodes.py --import-latest
python3.12 scripts/scrape_episodes.py --reindex-chroma
```

### Option 2: Use Existing Content Files

If you have content files with all seasons:
1. Place them in `app/data/episodes/` as `season_*.json`
2. Place embedding backups in `app/data/embeddings/season_*_embeddings.json`
3. Restart server - ChromaDB will auto-populate

### Option 3: Manual Import

```bash
# Import from content JSON
python -c "
from app.services.storage.document_store import get_store
store = get_store()
store.import_from_json('app/content/btvs_all_seasons.json')
"

# Then restart server - ChromaDB will populate
```

---

## Verification Commands

```bash
# Check content files
ls -lh app/content/btvs_all_seasons.json

# Check document store
ls -lh app/data/episodes/season_*.json

# Check ChromaDB
python3.12 << 'EOF'
import chromadb
from pathlib import Path
client = chromadb.PersistentClient(path="app/data/chroma")
collection = client.get_collection("buffy_episodes")
print(f"Episodes in ChromaDB: {collection.count()}")
EOF

# Check via API (if server running)
curl http://localhost:8000/api/test | python3.12 -m json.tool | grep chromadb_episodes
```

---

## Summary

**✅ YES - Complete Pipeline Exists:**
1. Scraping → Content JSON ✅
2. Content JSON → Document Store ✅ (auto on startup)
3. Document Store → ChromaDB ✅ (auto if empty)

**✅ YES - Data Successfully Loaded:**
- ChromaDB has 144 episodes (Seasons 1–7)
- Search functionality works
- All components operational

**⚠️  Gaps:**
- Scraping is manual (not automated)
- Multiple pipeline implementations exist (some unused)

