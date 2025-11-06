#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Exit on error
set -e

# Function to print section headers
print_section() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

# Function to check if a service is running
check_service() {
    local url=$1
    local expected_status=$2
    local status=$(curl -s -o /dev/null -w "%{http_code}" $url)
    [ "$status" = "$expected_status" ]
}

# Function to wait for a service
wait_for_service() {
    local service=$1
    local url=$2
    local expected_status=${3:-200}  # Default to 200 if not provided
    local max_attempts=${4:-10}      # Default to 10 attempts if not provided
    local attempt=1

    echo "Waiting for $service to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if [ "$service" = "Frontend" ]; then
            # For frontend, we just check if the port is open
            if curl -s -f "http://localhost:5173" > /dev/null; then
                echo "✅ $service is ready!"
                return 0
            fi
        else
            # For backend, we check the health endpoint
            if check_service "$url" "$expected_status"; then
                echo "✅ $service is ready!"
                return 0
            fi
        fi
        
        echo "Attempt $attempt/$max_attempts: $service not ready yet..."
        if [ -f "app/logs/backend.log" ]; then
            echo "Latest backend logs:"
            tail -n 5 app/logs/backend.log
        fi
        sleep 2
        attempt=$((attempt + 1))
    done
    echo "❌ $service failed to start after $max_attempts attempts"
    if [ -f "app/logs/backend.log" ]; then
        echo "Backend logs:"
        cat app/logs/backend.log
    fi
    return 1
}

# Function to start a service in the background
start_service() {
    local name=$1
    local command=$2
    local log_file=$3

    echo "Starting $name..."
    # Ensure we're using the virtual environment's Python
    if [ "$name" = "backend" ]; then
        # Use the virtual environment's Python and uvicorn
        $command > "$log_file" 2>&1 &
    else
        $command > "$log_file" 2>&1 &
    fi
    echo $! > "${name}.pid"
    echo "✅ $name started (PID: $(cat ${name}.pid))"
}

# Function to stop a service
stop_service() {
    local service=$1
    print_section "Stopping $service"
    
    case $service in
        "uvicorn")
            pkill -f "uvicorn app.api.main:app" || true
            ;;
        "redis")
            pkill -f "redis-server" || true
            ;;
        *)
            echo "Unknown service: $service"
            ;;
    esac
}

# Function to verify Python environment
verify_python_env() {
    print_section "Verifying Python Environment"
    
    # Check if Python 3.12 is available (required)
    if ! command -v python3.12 &> /dev/null; then
        python_version=$(python3 --version 2>&1 || echo "not found")
        echo "❌ Python 3.12 is required but not found. Found: $python_version"
        echo "Please install Python 3.12:"
        echo "  - macOS: brew install python@3.12"
        echo "  - Linux: Use your distribution's package manager"
        exit 1
    fi
    
    python_version=$(python3.12 --version 2>&1)
    echo "✅ Python 3.12 detected: $python_version"
    PYTHON_CMD="python3.12"
    
    # Check virtual environment
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "⚠️  No virtual environment detected"
        if [ -f "venv/bin/activate" ]; then
            echo "🔄 Activating virtual environment..."
            source venv/bin/activate
            echo "✅ Virtual environment activated: $VIRTUAL_ENV"
        else
            echo "❌ Virtual environment not found at venv/"
            echo "Please run initialization script first:"
            echo "   ./init.sh"
            exit 1
        fi
    else
        echo "✅ Virtual environment detected: $VIRTUAL_ENV"
    fi
    
    # Check critical packages
    echo "🔍 Verifying critical package installation..."
    missing_packages=()
    
    # Check each package individually (avoiding associative arrays for better compatibility)
    # Note: package names vs import names may differ (e.g., sentence-transformers vs sentence_transformers)
    packages=("fastapi" "uvicorn" "chromadb" "sentence_transformers")
    
    # Use the virtual environment's Python if available (it's python3.12)
    # Otherwise use python3.12 directly
    if [ -n "$VIRTUAL_ENV" ] && [ -f "$VIRTUAL_ENV/bin/python" ]; then
        PYTHON_CMD="$VIRTUAL_ENV/bin/python"
        # Verify venv uses Python 3.12
        VENV_VERSION=$($VIRTUAL_ENV/bin/python --version 2>&1)
        if ! echo "$VENV_VERSION" | grep -E "Python 3\.12" > /dev/null; then
            echo "⚠️  Warning: Virtual environment does not use Python 3.12"
            echo "   Found: $VENV_VERSION"
            echo "   Recreate venv with: rm -rf venv && ./init.sh"
        fi
    else
        PYTHON_CMD="python3.12"
    fi
    
    for package in "${packages[@]}"; do
        if ! $PYTHON_CMD -c "import $package" &> /dev/null; then
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -ne 0 ]; then
        echo "❌ Missing required packages: {${missing_packages[*]}}"
        echo "Please run initialization script to install dependencies:"
        echo "   ./init.sh"
        exit 1
    else
        echo "✅ All required packages installed"
    fi
}

# Function to verify data directory
verify_data_dir() {
    print_section "Verifying Data Directory"
    
    # Check if data directory exists
    if [ ! -d "app/data" ]; then
        echo "❌ Data directory not found"
        echo "Please run initialization script first:"
        echo "   ./init.sh"
        exit 1
    fi
    
    # Check if ChromaDB directory exists
    if [ ! -d "app/data/chroma" ]; then
        echo "⚠️  ChromaDB directory not found"
        echo "Please run data initialization:"
        echo "   python scripts/init_data.py"
    else
        echo "✅ ChromaDB directory found"
    fi
    
    # Check if episode data exists
    if [ ! -d "app/data/episodes" ]; then
        echo "⚠️  Episode data directory not found"
        echo "Please run data initialization:"
        echo "   python scripts/init_data.py"
    else
        echo "✅ Episode data directory found"
    fi
}

# Main script
print_section "Starting TV Show Chat System"

# Stop any running services
stop_service "uvicorn"

# Verify environment
verify_python_env
verify_data_dir

# Start the FastAPI server
print_section "Starting FastAPI Server"
# Ensure we use Python 3.12 (prefer venv's python which is python3.12)
# The FastAPI app is in app.api.main, not app.main
# Run from project root so Python can find the 'app' module
cd "$(dirname "$0")" || exit 1
if [ -n "$VIRTUAL_ENV" ] && [ -f "$VIRTUAL_ENV/bin/python" ]; then
    $VIRTUAL_ENV/bin/python -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000 &
else
    python3.12 -m uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000 &
fi
UVICORN_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
for i in {1..5}; do
    if check_service "http://localhost:8000/health" "200"; then
        echo "✅ Server is running"
        break
    fi
    if [ $i -eq 5 ]; then
        echo "❌ Server failed to start"
        exit 1
    fi
    echo "Attempt $i/5: Waiting for server..."
    sleep 2
done

# Check system health
print_section "Checking System Health"
if ! check_service "http://localhost:8000/health" "200"; then
    echo "⚠️  Server is not healthy"
fi

if ! check_service "http://localhost:8000/health/vector-store" "200"; then
    echo "⚠️  Vector store is not healthy"
fi

if ! check_service "http://localhost:8000/health/model" "200"; then
    echo "⚠️  Model service is not healthy"
fi

# Print service URLs
print_section "Service URLs"
echo "   - API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo "   - Health: http://localhost:8000/health"
echo "   - Vector Store: http://localhost:8000/health/vector-store"
echo "   - Model: http://localhost:8000/health/model"

# Wait for user input to stop
echo -e "\n${GREEN}System is running!${NC}"
echo "Press Ctrl+C to stop all services"
wait $UVICORN_PID 