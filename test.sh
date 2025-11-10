#!/bin/bash
set -euo pipefail

# Colors for output
GREEN='[0;32m'
RED='[0;31m'
YELLOW='[1;33m'
NC='[0m' # No Color

# Use Python 3.12 for JSON formatting (required)
if ! command -v python3.12 &> /dev/null; then
    echo -e "${RED}Error: Python 3.12 is required but not found${NC}"
    echo "Please install Python 3.12:"
    echo "  - macOS: brew install python@3.12"
    exit 1
fi
PYTHON_CMD="python3.12"
if [ -f "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
elif [ -f "venv/bin/python3.12" ]; then
    PYTHON_BIN="venv/bin/python3.12"
else
    PYTHON_BIN="python3.12"
fi

echo -e "${YELLOW}Starting TV Show Chat System Tests...${NC}
"

# Check if the server is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${RED}Error: Server is not running. Please start the server first.${NC}"
    exit 1
fi

# Function to run a test and format output
run_test() {
    local name=$1
    local endpoint=$2
    local method=${3:-GET}
    local data=${4:-""}

    echo -e "${YELLOW}Testing: ${name}${NC}"
    echo "Endpoint: ${endpoint}"

    if [ "$method" = "POST" ]; then
        response=$(curl -s -X POST -H "Content-Type: application/json" -d "$data" "http://localhost:8000${endpoint}")
    else
        response=$(curl -s "http://localhost:8000${endpoint}")
    fi

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Request successful${NC}"
        echo "Response:"
        echo "$response" | $PYTHON_CMD -m json.tool
    else
        echo -e "${RED}✗ Request failed${NC}"
        exit 1
    fi
    echo "----------------------------------------"
}

# Run all tests
echo -e "
${YELLOW}1. Testing Health Endpoints${NC}"
run_test "Overall Health" "/health"
run_test "Vector Store Health" "/health/vector-store"
run_test "Model Health" "/health/model"

echo -e "
${YELLOW}2. Testing System State${NC}"
run_test "System Test" "/api/test"

echo -e "
${YELLOW}3. Testing Search Functionality${NC}"
run_test "Default Search" "/api/test-search"
run_test "Custom Search" "/api/test-search?query=Willow%20uses%20magic&limit=2"

echo -e "
${YELLOW}4. Testing Vector Store State${NC}"
echo "Checking vector store status..."
vector_store_status=$(curl -s http://localhost:8000/health/vector-store | $PYTHON_CMD -c "import sys, json; print(json.load(sys.stdin)['status'])")
if [ "$vector_store_status" = "healthy" ]; then
    echo -e "${GREEN}✓ Vector store is healthy${NC}"
else
    echo -e "${RED}✗ Vector store is not healthy${NC}"
    exit 1
fi

echo -e "
${YELLOW}5. Testing Document Store${NC}"
if [ -d "app/data/episodes" ]; then
    episode_files=$(ls app/data/episodes/season_*.json 2>/dev/null | wc -l)
    echo -e "${GREEN}✓ Found ${episode_files} season files${NC}"
else
    echo -e "${RED}✗ Episode directory not found${NC}"
    exit 1
fi

if [ -d "app/data/chroma" ]; then
    echo -e "${GREEN}✓ ChromaDB data directory exists${NC}"
else
    echo -e "${RED}✗ ChromaDB data directory not found${NC}"
    exit 1
fi

echo -e "
${YELLOW}6. Testing Crawler Status${NC}"
CRAWLER_TMP_FILE=$(mktemp)
if $PYTHON_BIN scripts/scrape_episodes.py --status > "$CRAWLER_TMP_FILE"; then
    echo -e "${GREEN}✓ Crawler status command succeeded${NC}"
    head -n 10 "$CRAWLER_TMP_FILE"
else
    echo -e "${RED}✗ Crawler status command failed${NC}"
    cat "$CRAWLER_TMP_FILE"
    rm -f "$CRAWLER_TMP_FILE"
    exit 1
fi
rm -f "$CRAWLER_TMP_FILE"

echo -e "
${YELLOW}7. Importing Latest Content into Document Store${NC}"
if $PYTHON_BIN scripts/scrape_episodes.py --import-latest; then
    echo -e "${GREEN}✓ Import succeeded${NC}"
else
    echo -e "${RED}✗ Import failed${NC}"
    exit 1
fi

echo -e "
${YELLOW}8. Reindexing ChromaDB${NC}"
if $PYTHON_BIN scripts/scrape_episodes.py --reindex-chroma; then
    echo -e "${GREEN}✓ Reindex succeeded${NC}"
else
    echo -e "${RED}✗ Reindex failed${NC}"
    exit 1
fi

echo -e "
${YELLOW}9. Testing Data Pipeline Integrity${NC}"
$PYTHON_BIN <<'PYCODE'
import json
import sys
import urllib.request
from pathlib import Path

GREEN = '[0;32m'
RED = '[0;31m'
NC = '[0m'

def fail(msg):
    print(f"{RED}ERROR: {msg}{NC}")
    sys.exit(1)

EXPECTED_EPISODES = {
    1: 12,
    2: 22,
    3: 22,
    4: 22,
    5: 22,
    6: 22,
    7: 22,
}
EXPECTED_SEASON_KEYS = {f"season_{season}" for season in EXPECTED_EPISODES}
EXPECTED_TOTAL = sum(EXPECTED_EPISODES.values())

def validate_counts(label, counts):
    missing = [season for season in EXPECTED_EPISODES if season not in counts]
    if missing:
        fail(f"{label}: missing seasons {missing}")
    for season, expected in EXPECTED_EPISODES.items():
        actual = counts[season]
        if actual != expected:
            fail(f"{label}: season {season} expected {expected} episodes, found {actual}")

content_path = Path('app/content/btvs_all_seasons.json')
if not content_path.exists():
    fail('Content file btvs_all_seasons.json not found (run scripts/crawl.sh)')
with content_path.open('r', encoding='utf-8') as f:
    content_data = json.load(f)

if set(content_data.keys()) != EXPECTED_SEASON_KEYS:
    fail(f"Content file seasons mismatch. Expected {sorted(EXPECTED_SEASON_KEYS)}, found {sorted(content_data.keys())}")

content_counts = {
    int(season_key.split('_')[1]): len(episodes)
    for season_key, episodes in content_data.items()
}
validate_counts("Content JSON", content_counts)
content_total = sum(content_counts.values())
if content_total != EXPECTED_TOTAL:
    fail(f"Content JSON total expected {EXPECTED_TOTAL}, found {content_total}")

doc_dir = Path('app/data/episodes')
doc_files = sorted(doc_dir.glob('season_*.json'))
if not doc_files:
    fail('No document store season files found')
doc_counts = {}
for file in doc_files:
    season_num = int(file.stem.split('_')[1])
    with file.open('r', encoding='utf-8') as f:
        doc_counts[season_num] = len(json.load(f))
validate_counts("Document store", doc_counts)
doc_total = sum(doc_counts.values())

embed_dir = Path('app/data/embeddings')
embed_files = sorted(embed_dir.glob('season_*_embeddings.json'))
if not embed_files:
    fail('No embedding season files found')
embedding_counts = {}
for file in embed_files:
    season_num = int(file.stem.split('_')[1])
    with file.open('r', encoding='utf-8') as f:
        embedding_counts[season_num] = len(json.load(f))
validate_counts("Embeddings store", embedding_counts)

try:
    with urllib.request.urlopen('http://localhost:8000/api/test') as resp:
        api_data = json.load(resp)
except Exception as exc:
    fail(f'Failed to fetch /api/test: {exc}')

vector_section = api_data.get('vector_store', {})
vector_total = vector_section.get('total_episodes')
chroma_total = vector_section.get('chromadb_episodes', vector_total)
api_content = api_data.get('content', {})
api_total = api_content.get('total_episodes')
api_counts = api_content.get('season_counts', {})
if isinstance(api_counts, dict):
    api_counts = {int(k): v for k, v in api_counts.items()}

print("Season coverage summary:")
for season in sorted(EXPECTED_EPISODES):
    print(
        f"  Season {season}: content={content_counts.get(season)} "
        f"doc={doc_counts.get(season)} "
        f"embeddings={embedding_counts.get(season)} "
        f"api={api_counts.get(season) if api_counts else None}"
    )

print(f"Totals - Content: {content_total} | Document store: {doc_total} | Vector store: {vector_total} | ChromaDB: {chroma_total} | API content: {api_total}")

if None in (vector_total, chroma_total, api_total) or not api_counts:
    fail('Invalid API response for /api/test')

validate_counts("API content summary", api_counts)
if api_total != EXPECTED_TOTAL:
    fail(f"API content total expected {EXPECTED_TOTAL}, found {api_total}")

if not (content_total == doc_total == vector_total == chroma_total == EXPECTED_TOTAL):
    fail('Episode counts do not match across pipeline')

print(f"{GREEN}SUCCESS: Data pipeline integrity verified{NC}")
PYCODE

echo -e "
${YELLOW}Test Summary:${NC}"
echo "----------------------------------------"
echo "✓ Health endpoints tested"
echo "✓ System state verified"
echo "✓ Search functionality tested"
echo "✓ Vector store state checked"
echo "✓ Document store verified"
echo "✓ Latest content imported"
echo "✓ ChromaDB reindexed"
echo "✓ Data pipeline integrity verified"
echo "----------------------------------------"

echo -e "
${GREEN}All tests completed!${NC}"
echo "Check the output above for any errors or warnings."
