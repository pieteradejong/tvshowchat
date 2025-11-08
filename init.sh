#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FORCE_RECREATE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --recreate-venv)
            FORCE_RECREATE=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: ./init.sh [--recreate-venv]"
            exit 1
            ;;
    esac
done

# Function to print section headers
print_section() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

# Function to check Python version
check_python_version() {
    local min_version="3.12.0"
    if ! command -v python3.12 &> /dev/null; then
        echo -e "${RED}❌ Python 3.12 is not installed. Please install it first.${NC}"
        echo -e "You can install it using:"
        echo -e "  - macOS: brew install python@3.12"
        echo -e "  - Linux: Use your distribution's package manager"
        exit 1
    fi
    
    local current_version=$(python3.12 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
    if [ "$(printf '%s\n' "$min_version" "$current_version" | sort -V | head -n1)" != "$min_version" ]; then
        echo -e "${RED}❌ Python version 3.12 or higher is required. Current version: $current_version${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Python version $current_version is compatible${NC}"
}

# Function to install Python dependencies
install_python_deps() {
    print_section "Installing Python Dependencies"

    local recreate=$FORCE_RECREATE
    if [ -d "venv" ] && [ -f "venv/bin/python" ] && [ "$FORCE_RECREATE" = false ]; then
        echo -e "${GREEN}🔄 Using existing Python virtual environment (venv/)${NC}"
    else
        if [ -d "venv" ]; then
            echo -e "${YELLOW}🧹 Removing existing Python virtual environment (venv/) ...${NC}"
            rm -rf venv
        fi
        echo -e "${GREEN}🐍 Creating Python 3.12 virtual environment ...${NC}"
        python3.12 -m venv venv
    fi

    if [ ! -d "venv" ] || [ ! -f "venv/bin/activate" ]; then
        echo -e "${RED}❌ Virtual environment setup failed (missing venv/bin/activate)${NC}"
        exit 1
    fi

    source venv/bin/activate

    venv_python_version=$(python -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
    if [[ ! "$venv_python_version" =~ ^3\.12\. ]]; then
        echo -e "${RED}❌ Virtual environment Python version mismatch. Expected Python 3.12.x, got $venv_python_version${NC}"
        echo -e "${YELLOW}Hint: Re-run ./init.sh --recreate-venv to rebuild the environment.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Using Python $venv_python_version in virtual environment${NC}"

    echo -e "${GREEN}🧹 Removing all __pycache__, .pytest_cache, and .ruff_cache directories ...${NC}"
    find . -type d -name "__pycache__" -exec rm -rf {} +
    rm -rf .pytest_cache .ruff_cache

    echo "Upgrading pip..."
    python -m pip install --upgrade pip

    echo "Installing project dependencies..."
    python -m pip install -r requirements.txt

    echo "Verifying critical package installation..."
    declare -A package_imports=(
        ["fastapi"]="fastapi"
        ["uvicorn"]="uvicorn"
        ["chromadb"]="chromadb"
        ["sentence-transformers"]="sentence_transformers"
    )

    for package in "${!package_imports[@]}"; do
        import_name="${package_imports[$package]}"
        echo -n "Checking $package... "
        if python -c "import sys; sys.path.insert(0, '.'); import $import_name; print('OK')" 2>/dev/null; then
            echo -e "${GREEN}✓${NC}"
        else
            echo -e "${RED}✗${NC}"
            echo -e "${RED}❌ Failed to import $package. Please check the installation.${NC}"
            echo "You can try:"
            echo "  1. source venv/bin/activate"
            echo "  2. python -c 'import $import_name'"
            echo "  3. If that fails, try: pip install --force-reinstall $package"
            exit 1
        fi
    done
    echo -e "${GREEN}✅ All critical packages installed successfully${NC}"
}

# Function to setup data directories
setup_data_dirs() {
    print_section "Setting up Data Directories"
    
    # Create necessary directories
    mkdir -p app/data/episodes
    mkdir -p app/data/chroma
    mkdir -p app/logs
    
    echo -e "${GREEN}✅ Data directories created${NC}"
}

# Main script
print_section "Initializing TV Show Chat System"

# Check Python version first
check_python_version

# Install Python dependencies
install_python_deps

# Setup data directories
setup_data_dirs

# Initialize data
print_section "Initializing Data"
echo "Running data initialization script..."
# Use venv's python (which is python3.12)
if [ -n "$VIRTUAL_ENV" ] && [ -f "$VIRTUAL_ENV/bin/python" ]; then
    $VIRTUAL_ENV/bin/python scripts/init_data.py
else
    python3.12 scripts/init_data.py
fi

print_section "✅ Initialization Complete"
echo -e "${GREEN}The system is now ready to run!${NC}"
echo "To start the system, run:"
echo "   ./run.sh"
