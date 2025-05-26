#!/bin/bash

# Exit on error
set -e

# Function to print section headers
print_section() {
    echo ""
    echo "=== $1 ==="
    echo ""
}

# Function to check command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        echo "❌ $1 is not installed. $2"
        return 1
    fi
    return 0
}

print_section "🚀 Initializing TV Show Chat Development Environment"

# Check and install system dependencies
print_section "System Dependencies Check"

# Check Python
if ! check_command "python3" "Please install Python 3.8 or higher."; then
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; v = sys.version_info; print(f"{v.major}.{v.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo "❌ Python version must be 3.9 or higher. Current version: $PYTHON_VERSION"
    echo "Recommended: Install Python 3.9 using:"
    echo "   - macOS: brew install python@3.9"
    echo "   - Ubuntu: sudo apt install python3.9"
    echo "   - Windows: Download from https://www.python.org/downloads/"
    exit 1
fi
echo "✅ Python version $PYTHON_VERSION detected"

# Check pip
if ! check_command "pip3" "Please install pip."; then
    exit 1
fi

# Check Node.js
if ! check_command "node" "Please install Node.js 18 or higher."; then
    echo "Installation instructions:"
    echo "   - macOS: brew install node"
    echo "   - Ubuntu: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
    echo "   - Windows: Download from https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version must be 18 or higher. Current version: $(node -v)"
    exit 1
fi
echo "✅ Node.js version $(node -v) detected"

# Check npm
if ! check_command "npm" "Please install npm."; then
    exit 1
fi
echo "✅ npm version $(npm -v) detected"

# Check and install Redis
print_section "Redis Setup"

if ! check_command "redis-stack-server" "Installing Redis Stack..."; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install redis-stack
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        echo "Please install Redis Stack using your package manager:"
        echo "   - Ubuntu/Debian: Follow instructions at https://redis.io/docs/stack/get-started/installation/install-stack-linux/"
        exit 1
    else
        echo "Unsupported operating system. Please install Redis Stack manually."
        exit 1
    fi
fi

# Check Redis status
echo "🔍 Checking Redis Stack status..."
if ! redis-cli ping &> /dev/null; then
    echo "⚠️  Redis Stack is not running. Starting Redis Stack..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Start Redis Stack directly since it's installed as a cask
        /opt/homebrew/Caskroom/redis-stack-server/7.2.0-v10/bin/redis-stack-server &
        sleep 5  # Give it time to start
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo systemctl start redis-stack
    fi
    
    # Wait for Redis to start
    echo "Waiting for Redis Stack to start..."
    for i in {1..5}; do
        if redis-cli ping &> /dev/null; then
            break
        fi
        echo "Attempt $i/5: Waiting for Redis Stack..."
        sleep 2
    done
fi

# Verify Redis is running and has required modules
echo "🔍 Verifying Redis Stack modules..."
if ! redis-cli module list | grep -q "ReJSON" || ! redis-cli module list | grep -q "search"; then
    echo "❌ Redis Stack modules (ReJSON, RediSearch) not found. Please ensure Redis Stack is properly installed."
    exit 1
fi

# Verify Redis is running
if ! redis-cli ping &> /dev/null; then
    echo "❌ Redis Stack failed to start. Please check Redis logs:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "   tail -f /opt/homebrew/var/log/redis-stack.log"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "   sudo systemctl status redis-stack"
        echo "   sudo journalctl -u redis-stack"
    fi
    exit 1
fi
echo "✅ Redis Stack is installed and running with required modules"

# Create necessary directories (non-Python operations)
print_section "Creating Project Structure"
mkdir -p app/{api,services/{scraping,pipeline,embeddings,search},models,config,utils}
mkdir -p app/{content,logs}
mkdir -p tests/{unit,integration}
mkdir -p frontend/src/{components,hooks,services,types,utils}

# Create necessary __init__.py files
touch app/__init__.py
touch app/api/__init__.py
touch app/services/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py

# Python Environment Setup
print_section "Python Environment Setup"

# Remove all __pycache__ directories for a clean start
echo "🧹 Removing all __pycache__ directories..."
find . -name "__pycache__" -exec rm -rf {} +

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3.9 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install wheel
echo "⬆️  Upgrading pip and installing wheel..."
python -m pip install --upgrade pip wheel

# Clean any existing installations that might be broken
echo "🧹 Cleaning existing installations..."
python -m pip uninstall -y uvicorn fastapi redis redis-om pydantic

# Install/upgrade requirements
echo "📚 Installing/updating Python dependencies..."

# Install system dependencies for macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍺 Installing system dependencies via Homebrew..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew is not installed. Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install sentencepiece via Homebrew
    echo "📦 Installing sentencepiece via Homebrew..."
    brew install sentencepiece
    
    # Install PyTorch for macOS
    echo "🖥️  Installing PyTorch for macOS..."
    python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install other requirements
echo "📦 Installing Python packages..."
python -m pip install -r requirements.txt

# Verify critical packages
echo "🔍 Verifying critical package installation..."
python -c "
import sys
from importlib.metadata import distributions
required = {
    'fastapi', 'uvicorn', 'redis', 'pydantic', 
    'sentence-transformers', 'torch', 'transformers'
}
installed = {dist.metadata['Name'].lower() for dist in distributions()}
missing = required - installed
if missing:
    print('❌ Missing required packages:', missing)
    sys.exit(1)
print('✅ All required Python packages are installed')
"

# Verify uvicorn specifically
python -c "
try:
    import uvicorn
    print('✅ uvicorn version', uvicorn.__version__, 'installed')
except ImportError as e:
    print('❌ uvicorn import failed:', e)
    import sys; sys.exit(1)
"

# Download embedding model
print_section "Setting up Embedding Model"
echo "🤖 Setting up embedding model..."
python3 -c "
from sentence_transformers import SentenceTransformer
import os
model_path = 'app/models/all-MiniLM-L6-v2'
if not os.path.exists(model_path):
    print('Downloading model...')
    model = SentenceTransformer('all-MiniLM-L6-v2')
    model.save(model_path)
    print('Model downloaded and saved.')
else:
    print('Model already exists.')
"

# Frontend Setup (non-Python operations)
print_section "Frontend Setup"
echo "🎨 Setting up frontend..."

if [ -d "frontend" ]; then
    cd frontend
    
    # Install frontend dependencies
    echo "📦 Installing frontend dependencies..."
    npm install
    
    # Check for vulnerabilities
    echo "🔍 Checking for npm vulnerabilities..."
    npm audit
    
    # Return to root directory
    cd ..
else
    echo "❌ Frontend directory not found. Please ensure the repository is properly cloned."
    exit 1
fi

# Environment Setup (non-Python operations)
print_section "Environment Configuration"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOL
# Backend
REDIS_HOST=localhost
REDIS_PORT=6379
MODEL_NAME=all-MiniLM-L6-v2
MODEL_PATH=app/models/all-MiniLM-L6-v2
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOL
fi

# Create .env file for frontend if it doesn't exist
if [ ! -f "frontend/.env" ]; then
    echo "📝 Creating frontend .env file..."
    cat > frontend/.env << EOL
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOL
fi

# Final Checks (in venv context)
print_section "Final Checks"

# Check if all required directories exist
for dir in "venv" "app/api" "app/services" "app/models" "frontend"; do
    if [ ! -d "$dir" ]; then
        echo "❌ Required directory $dir is missing"
        exit 1
    fi
done

# Check if model exists
if [ ! -d "app/models/all-MiniLM-L6-v2" ]; then
    echo "❌ Embedding model is missing"
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping &> /dev/null; then
    echo "❌ Redis is not running"
    exit 1
fi

# Verify Python environment
echo "🔍 Verifying Python environment..."
python3 -c "
import sys
from importlib.metadata import distributions
required = {
    'fastapi', 'uvicorn', 'redis', 'sentence-transformers',
    'torch', 'transformers'
}
installed = {dist.metadata['Name'].lower() for dist in distributions()}
missing = required - installed
if missing:
    print('❌ Missing required packages:', missing)
    sys.exit(1)
print('✅ All required Python packages are installed')
"

print_section "✅ Initialization Complete"
echo "You can now:"
echo "   - Run './run.sh' to start the application"
echo "   - Activate the virtual environment with 'source venv/bin/activate'"
echo "   - Run tests with 'pytest'"
echo ""
echo "The application will be available at:"
echo "   - Frontend: http://localhost:5173"
echo "   - Backend API: http://localhost:8000"
echo "   - API Documentation: http://localhost:8000/docs"
echo ""
echo "Health check endpoints:"
echo "   - Backend: http://localhost:8000/health"
echo "   - Redis: http://localhost:8000/health/redis"
echo "   - Model: http://localhost:8000/health/model"
