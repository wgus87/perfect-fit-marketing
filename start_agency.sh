#!/bin/bash

# AI Marketing Agency Startup Script
# This script starts all components of the automated marketing agency

echo "🚀 Starting AI Marketing Agency System..."

# Set working directory
cd "$(dirname "$0")"

# Check if virtual environment exists for dashboard
if [ ! -d "agency_dashboard/venv" ]; then
    echo "❌ Dashboard virtual environment not found. Please run setup first."
    exit 1
fi

# Function to check if port is available
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Function to start background process
start_background() {
    local name=$1
    local command=$2
    local logfile=$3
    
    echo "📦 Starting $name..."
    nohup $command > $logfile 2>&1 &
    local pid=$!
    echo $pid > "${name}.pid"
    echo "✅ $name started (PID: $pid)"
}

# Create logs directory
mkdir -p logs

# Check required ports
echo "🔍 Checking required ports..."
if ! check_port 5000; then
    echo "❌ Port 5000 (Flask API) is in use. Please stop the conflicting service."
    exit 1
fi

# Start Flask API Backend
echo "🌐 Starting Flask API Backend..."
cd agency_dashboard
source venv/bin/activate
start_background "flask_api" "python src/main.py" "../logs/flask_api.log"
cd ..

# Wait for Flask to start
echo "⏳ Waiting for Flask API to start..."
sleep 5

# Test Flask API
if curl -s http://localhost:5000/api/dashboard/overview > /dev/null; then
    echo "✅ Flask API is running"
else
    echo "❌ Flask API failed to start"
    exit 1
fi

# Start AI Agent Orchestrator
echo "🤖 Starting AI Agent Orchestrator..."
start_background "orchestrator" "python agency_orchestrator.py" "logs/orchestrator.log"

# Wait for orchestrator to initialize
sleep 3

# Test orchestrator
if python agency_orchestrator.py status > /dev/null 2>&1; then
    echo "✅ AI Agent Orchestrator is running"
else
    echo "❌ AI Agent Orchestrator failed to start"
fi

echo ""
echo "🎉 AI Marketing Agency System Started Successfully!"
echo ""
echo "📊 Dashboard: http://localhost:5000"
echo "🔧 API Endpoints: http://localhost:5000/api/dashboard/"
echo "🤖 Orchestrator Status: python agency_orchestrator.py status"
echo ""
echo "📝 Logs:"
echo "   - Flask API: logs/flask_api.log"
echo "   - Orchestrator: logs/orchestrator.log"
echo ""
echo "🛑 To stop the system: ./stop_agency.sh"
echo ""

# Show current status
echo "📈 Current System Status:"
python agency_orchestrator.py status | head -20

echo ""
echo "✨ The AI Marketing Agency is now running and will automatically:"
echo "   • Generate leads daily at 9:00 AM"
echo "   • Research prospects every 2 hours"
echo "   • Score leads every hour"
echo "   • Qualify leads every 3 hours"
echo "   • Send outreach daily at 10:00 AM"
echo "   • Process sales daily at 2:00 PM"
echo "   • Manage clients daily at 5:00 PM"
echo ""
echo "💰 Target: 6-figure revenue through automated lead generation and sales!"

