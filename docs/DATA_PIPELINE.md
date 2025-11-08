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
- ✅ Content JSON file present: `btvs_all_seasons.json`
- ⚠️  Scraping is **manual** (not automated in init.sh)
- ⚠️  Only Season 1 data currently scraped (12 episodes)

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
- ✅ 4 timestamped JSON files exist
- ✅ Latest file contains Season 1 (12 episodes)
- ⚠️  Seasons 2-7 not yet scraped

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
- ✅ Season 1 loaded: `app/data/episodes/season_1.json` (12 episodes)
- ✅ Embeddings file exists: `app/data/embeddings/season_1_embeddings.json`
- ✅ Auto-import works on startup

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
- ✅ ChromaDB initialized: `app/data/chroma/chroma.sqlite3` (604 KB)
- ✅ **12 episodes loaded** in ChromaDB collection `buffy_episodes`
- ✅ Auto-population works
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
│    app/content/*.json (4 files, latest has Season 1)        │
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
   - 4 content JSON files exist
   - Latest file has Season 1 (12 episodes)

3. **Document Store** ✅
   - Auto-imports from content JSON on startup
   - Season 1 loaded: `app/data/episodes/season_1.json`
   - Embeddings saved: `app/data/embeddings/season_1_embeddings.json`

4. **ChromaDB** ✅
   - **12 episodes successfully loaded**
   - Auto-populates from document store
   - Search functionality works
   - File size: 604 KB

### ⚠️ **Gaps/Issues:**

1. **Scraping Not Automated**
   - Scraping is manual: `python app/services/scraping/crawl.py`
   - Not integrated into `init.sh` or `scripts/init_data.py`
   - Only Season 1 scraped (Seasons 2-7 missing)

2. **Incomplete Data**
   - Only Season 1 available (12 episodes)
   - Need to scrape Seasons 2-7 for complete dataset

3. **Multiple Pipeline Implementations**
   - `app/services/data_pipeline.py` - Different implementation (not used?)
   - `app/services/data_loader.py` - References VectorStore (different from AdvancedVectorStore?)
   - `app/services/scraping/crawl.py` - Actual scraping code
   - Some confusion about which pipeline is active

---

## How to Complete the Pipeline

### Option 1: Scrape All Seasons (Recommended)

```bash
# Run scraping for all seasons
python app/services/scraping/crawl.py

# This will update: app/content/btvs_all_seasons.json
# Then restart server - it will auto-import and populate ChromaDB
```

### Option 2: Use Existing Content Files

If you have content files with all seasons:
1. Place them in `app/data/episodes/` as `season_*.json`
2. Restart server - ChromaDB will auto-populate

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
- ChromaDB has **12 episodes** (Season 1)
- Search functionality works
- All components operational

**⚠️  Gaps:**
- Scraping is manual (not automated)
- Only Season 1 data (need Seasons 2-7)
- Multiple pipeline implementations exist (some unused)

