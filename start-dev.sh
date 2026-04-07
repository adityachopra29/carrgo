#!/bin/bash
# Start both backend and frontend for local development

echo "Starting Carrgo - Development Mode"
echo "===================================="

# Start backend
echo "[1/3] Starting backend on http://localhost:8000..."
cd backend

# Locate and activate virtualenv (supports .venv/ or venv/)
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
elif [ -f "venv/bin/activate" ]; then
  source venv/bin/activate
else
  echo "  No virtualenv found. Creating .venv and installing dependencies..."
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt --quiet
fi

python3 seed.py 2>/dev/null
uvicorn app.main:app --port 8000 --reload --log-level info &
BACKEND_PID=$!
cd ..

sleep 2

# Start frontend
echo "[2/3] Starting frontend on http://localhost:3000..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "[3/3] Ready!"
echo "  Backend:  http://localhost:8000  (API docs: http://localhost:8000/docs)"
echo "  Frontend: http://localhost:3000"
echo "  Mode:     Simulation (no Vapi API key)"
echo ""
echo "Press Ctrl+C to stop both servers."

# Trap Ctrl+C to kill both
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait
