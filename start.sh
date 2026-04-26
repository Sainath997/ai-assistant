#!/usr/bin/env bash
# Start backend + frontend dev servers concurrently

set -e

echo "🤖 Starting AI Assistant..."

# Activate virtual env if it exists
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Start backend in background
python main.py &
BACKEND_PID=$!
echo "✅ Backend running (PID $BACKEND_PID) → http://localhost:8000"

# Start frontend dev server
cd ui
npm run dev &
FRONTEND_PID=$!
echo "✅ Frontend running (PID $FRONTEND_PID) → http://localhost:5173"

echo ""
echo "🚀 Aria is ready at http://localhost:5173"
echo "   Press Ctrl+C to stop both servers."

# Wait and forward signals
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT
wait
