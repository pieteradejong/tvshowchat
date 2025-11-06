#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Use Python 3.12 for JSON formatting (required)
if ! command -v python3.12 &> /dev/null; then
    echo -e "${RED}Error: Python 3.12 is required but not found${NC}"
    echo "Please install Python 3.12:"
    echo "  - macOS: brew install python@3.12"
    exit 1
fi
PYTHON_CMD="python3.12"

echo -e "${YELLOW}Starting TV Show Chat System Tests...${NC}\n"

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
    fi
    echo "----------------------------------------"
}

# Run all tests
echo -e "\n${YELLOW}1. Testing Health Endpoints${NC}"
run_test "Overall Health" "/health"
run_test "Vector Store Health" "/health/vector-store"
run_test "Model Health" "/health/model"

echo -e "\n${YELLOW}2. Testing System State${NC}"
run_test "System Test" "/api/test"

echo -e "\n${YELLOW}3. Testing Search Functionality${NC}"
run_test "Default Search" "/api/test-search"
run_test "Custom Search" "/api/test-search?query=Willow%20uses%20magic&limit=2"

echo -e "\n${YELLOW}4. Testing Vector Store State${NC}"
echo "Checking vector store status..."
vector_store_status=$(curl -s http://localhost:8000/health/vector-store | $PYTHON_CMD -c "import sys, json; print(json.load(sys.stdin)['status'])")
if [ "$vector_store_status" = "healthy" ]; then
    echo -e "${GREEN}✓ Vector store is healthy${NC}"
else
    echo -e "${RED}✗ Vector store is not healthy${NC}"
fi

echo -e "\n${YELLOW}5. Testing Document Store${NC}"
if [ -d "app/data/episodes" ]; then
    episode_files=$(ls app/data/episodes/season_*.json 2>/dev/null | wc -l)
    echo -e "${GREEN}✓ Found ${episode_files} season files${NC}"
else
    echo -e "${RED}✗ Episode directory not found${NC}"
fi

if [ -d "app/data/chroma" ]; then
    echo -e "${GREEN}✓ ChromaDB data directory exists${NC}"
else
    echo -e "${RED}✗ ChromaDB data directory not found${NC}"
fi

echo -e "\n${YELLOW}Test Summary:${NC}"
echo "----------------------------------------"
echo "✓ Health endpoints tested"
echo "✓ System state verified"
echo "✓ Search functionality tested"
echo "✓ Vector store state checked"
echo "✓ Document store verified"
echo "----------------------------------------"

echo -e "\n${GREEN}All tests completed!${NC}"
echo "Check the output above for any errors or warnings." 