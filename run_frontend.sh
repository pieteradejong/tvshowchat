#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_section() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

# Check if we're in the project root
if [ ! -d "frontend" ]; then
    echo -e "${RED}Error: frontend directory not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

print_section "Starting Frontend Development Server"

cd frontend || exit 1

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
fi

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${YELLOW}⚠️  Warning: Backend server doesn't appear to be running${NC}"
    echo "Frontend will start, but API calls will fail."
    echo "Start the backend with: ./run.sh"
    echo ""
fi

echo -e "${GREEN}Starting Vite dev server...${NC}"
echo "Frontend will be available at: http://localhost:5173"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

npm run dev

