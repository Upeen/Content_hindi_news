#!/bin/bash

# ===========================================
# Breaking News Finder - Startup Script
# Hindi News Competitor Analysis Tool
# ===========================================

echo "📰 Breaking News Finder"
echo "========================"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Resolve python command (python3 preferred, fallback to python)
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python not found. Please install Python 3.x."
    exit 1
fi
echo "🐍 Using: $PYTHON_CMD ($(${PYTHON_CMD} --version))"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment (detect Windows vs Unix)
echo "📦 Activating virtual environment..."
if [ -f "venv/Scripts/activate" ]; then
    # Windows (Git Bash / MINGW / Cygwin)
    source venv/Scripts/activate
    VENV_PYTHON="venv/Scripts/python"
elif [ -f "venv/bin/activate" ]; then
    # Linux / macOS
    source venv/bin/activate
    VENV_PYTHON="venv/bin/python"
else
    echo "❌ Could not find venv activate script."
    exit 1
fi

# Install dependencies if needed
# Double-guard: flag file missing OR streamlit not importable (catches stale flag from git)
if [ ! -f ".packages_installed" ] || ! "$VENV_PYTHON" -c "import streamlit" &>/dev/null; then
    echo "📥 Installing dependencies..."
    "$VENV_PYTHON" -m pip install --upgrade pip
    "$VENV_PYTHON" -m pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        touch .packages_installed
        echo "✅ Dependencies installed successfully."
    else
        echo "❌ Failed to install dependencies."
        exit 1
    fi
else
    echo "✅ Dependencies already installed."
fi

# Check if data directory exists
if [ ! -d "data" ]; then
    echo "📁 Creating data directory..."
    mkdir -p data
fi

# Check if port 8501 is busy and kill it if so
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" || "$OSTYPE" == "cygwin" ]]; then
    PID=$(netstat -ano | findstr :8501 | findstr LISTENING | awk '{print $5}' | head -n 1)
    if [ -n "$PID" ]; then
        echo "⚠️ Port 8501 is busy by PID $PID. Killing it..."
        taskkill /F /PID $PID &>/dev/null
    fi
fi

# Start Streamlit
echo "🚀 Starting Streamlit server..."
if [ -n "$PORT" ]; then
    echo "🌐 Running in cloud environment on port $PORT"
    "$VENV_PYTHON" -m streamlit run app.py --server.port "$PORT" --server.address 0.0.0.0 --server.headless true
else
    echo "🌐 Running locally on port 8501"
    "$VENV_PYTHON" -m streamlit run app.py --server.headless false --browser.gatherUsageStats false
fi
