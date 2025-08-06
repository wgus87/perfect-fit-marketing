#!/bin/bash

# AI Marketing Agency Stop Script
# This script stops all components of the automated marketing agency

echo "🛑 Stopping AI Marketing Agency System..."

# Set working directory
cd "$(dirname "$0")"

# Function to stop process by PID file
stop_process() {
    local name=$1
    local pidfile="${name}.pid"
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            echo "🔄 Stopping $name (PID: $pid)..."
            kill "$pid"
            
            # Wait for graceful shutdown
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "⚠️  Force killing $name..."
                kill -9 "$pid"
            fi
            
            echo "✅ $name stopped"
        else
            echo "⚠️  $name was not running"
        fi
        rm -f "$pidfile"
    else
        echo "⚠️  No PID file found for $name"
    fi
}

# Stop AI Agent Orchestrator
stop_process "orchestrator"

# Stop Flask API Backend
stop_process "flask_api"

# Kill any remaining processes on our ports
echo "🧹 Cleaning up remaining processes..."

# Kill processes on port 5000 (Flask)
if lsof -ti:5000 > /dev/null 2>&1; then
    echo "🔄 Stopping processes on port 5000..."
    lsof -ti:5000 | xargs kill -9 2>/dev/null || true
fi

# Clean up any Python processes related to our agency
pkill -f "agency_orchestrator.py" 2>/dev/null || true
pkill -f "src/main.py" 2>/dev/null || true

echo ""
echo "✅ AI Marketing Agency System Stopped Successfully!"
echo ""
echo "📝 Log files preserved in logs/ directory"
echo "🚀 To restart: ./start_agency.sh"
echo ""

