#!/bin/bash

# Exit on error
set -e

# Function to print section headers
print_section() {
    echo ""
    echo "=== $1 ==="
    echo ""
}

# Function to check if a service is running
check_service() {
    local url=$1
    local expected_status=$2
    local response=$(curl -s -w "\n%{http_code}" "$url")
    local body=$(echo "$response" | head -n1)
    local status_code=$(echo "$response" | tail -n1)
    
    if [ "$status_code" = "$expected_status" ]; then
        return 0
    fi
    return 1
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
    if [[ "$name" == "backend" ]]; then
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
    local name=$1
    if [ -f "${name}.pid" ]; then
        echo "Stopping $name..."
        kill $(cat "${name}.pid") 2>/dev/null || true
        rm "${name}.pid"
        echo "✅ $name stopped"
    fi
}

# Function to cleanup on exit
cleanup() {
    echo ""
    print_section "Cleaning Up"
    stop_service "redis"
    stop_service "backend"
    stop_service "frontend"
    exit 0
}

# Set up cleanup on script exit
trap cleanup EXIT INT TERM

print_section "🚀 Starting TV Show Chat Application"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./init.sh first"
    exit 1
fi

# Function to verify Python environment
verify_python_env() {
    local python_path=$(which python)
    if [[ ! "$python_path" =~ "venv" ]]; then
        echo "❌ Python is not running from virtual environment: $python_path"
        echo "Please ensure you're running the script from the project root directory"
        exit 1
    fi
    echo "✅ Using Python from virtual environment: $python_path"
}

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Verify Python environment
verify_python_env

# Verify uvicorn is installed in virtual environment
if ! python -c "import uvicorn" 2>/dev/null; then
    echo "❌ uvicorn is not installed in virtual environment"
    echo "Please run ./init.sh to install dependencies"
    exit 1
fi
echo "✅ uvicorn is installed in virtual environment"

# Create logs directory if it doesn't exist
mkdir -p app/logs

# Start Redis if not running
print_section "Starting Redis Stack"
if ! redis-cli ping &> /dev/null; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Start Redis Stack directly since it's installed as a cask
        /opt/homebrew/Caskroom/redis-stack-server/7.2.0-v10/bin/redis-stack-server &
        sleep 5  # Give it time to start
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start redis-stack
    fi
fi

# Verify Redis is running and has required modules
echo "🔍 Verifying Redis Stack modules..."
if ! redis-cli module list | grep -q "ReJSON" || ! redis-cli module list | grep -q "search"; then
    echo "❌ Redis Stack modules (ReJSON, RediSearch) not found. Please ensure Redis Stack is properly installed."
    exit 1
fi

# Verify Redis is running
if ! redis-cli ping &> /dev/null; then
    echo "❌ Redis Stack failed to start"
    exit 1
fi
echo "✅ Redis Stack is running with required modules"

# Start Backend
print_section "Starting Backend"
# Use the virtual environment's Python and uvicorn explicitly
start_service "backend" "python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload" "app/logs/backend.log"

# Wait for backend to be ready
wait_for_service "Backend" "http://localhost:8000/health" "200" 10

# Check backend services
echo "Checking backend services..."
if ! check_service "http://localhost:8000/health/redis" "200"; then
    echo "⚠️  Redis service is not healthy"
fi
if ! check_service "http://localhost:8000/health/model" "200"; then
    echo "⚠️  Model service is not healthy"
fi

# Start Frontend
print_section "Starting Frontend"
cd frontend
start_service "frontend" "npm run dev" "../app/logs/frontend.log"
cd ..

# Wait for frontend to be ready (using port check instead of HTTP status)
wait_for_service "Frontend" "http://localhost:5173" "" 10

print_section "✅ All Services Running"
echo "The application is now available at:"
echo "   - Frontend: http://localhost:5173"
echo "   - Backend API: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo ""
echo "Health check endpoints:"
echo "   - Backend: http://localhost:8000/health"
echo "   - Redis: http://localhost:8000/health/redis"
echo "   - Model: http://localhost:8000/health/model"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep the script running and show logs
tail -f app/logs/backend.log app/logs/frontend.log 