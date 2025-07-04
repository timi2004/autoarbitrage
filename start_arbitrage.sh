#!/bin/bash

# =====================================================
# Arbitrage System Startup Script for Linux/Mac
# =====================================================

echo ""
echo "================================================"
echo "         ARBITRAGE SYSTEM LAUNCHER"
echo "================================================"
echo ""

# Change to the script directory
cd "$(dirname "$0")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        print_status $RED "❌ Python is not installed or not in PATH"
        print_status $RED "   Please install Python 3.8+ and try again"
        echo ""
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# Verify Python version
python_version=$($PYTHON_CMD --version 2>&1 | grep -oP '\d+\.\d+')
if [[ "$(echo "$python_version >= 3.8" | bc -l)" != "1" ]]; then
    print_status $YELLOW "⚠️ Python version $python_version detected"
    print_status $YELLOW "   Python 3.8+ is recommended"
fi

# Check if we're in the right directory (look for required files)
if [ ! -f "startup_manager.py" ]; then
    print_status $RED "❌ startup_manager.py not found"
    print_status $RED "   Please run this script from the agent directory"
    echo ""
    exit 1
fi

if [ ! -f "config_manager.py" ]; then
    print_status $RED "❌ config_manager.py not found"
    print_status $RED "   Please run this script from the agent directory"
    echo ""
    exit 1
fi

if [ ! -f "mainrunner.py" ]; then
    print_status $RED "❌ mainrunner.py not found"
    print_status $RED "   Please run this script from the agent directory"
    echo ""
    exit 1
fi

# Make sure the startup_manager.py is executable
chmod +x startup_manager.py 2>/dev/null

# Run the startup manager
print_status $BLUE "🚀 Starting Arbitrage System..."
echo ""

$PYTHON_CMD startup_manager.py

# Check the exit code
exit_code=$?
if [ $exit_code -ne 0 ]; then
    echo ""
    print_status $RED "❌ Startup failed with exit code $exit_code"
    print_status $RED "   Please check the error messages above."
    echo ""
    exit $exit_code
else
    echo ""
    print_status $GREEN "✅ Startup completed successfully!"
    echo ""
fi