#!/bin/bash
# TempMail Pro - Quick Start Script

set -e

echo "🚀 Starting TempMail Pro..."

# Check if Docker is available
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "🐳 Docker detected. Using Docker Compose..."
    docker-compose up -d
    echo "✅ Services started!"
    echo "📧 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📚 API Docs: http://localhost:8000/docs"
    exit 0
fi

echo "📦 Docker not found. Starting locally..."

# Backend
echo "🔧 Starting backend..."
cd backend
python -m venv venv 2>/dev/null || true
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || true
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Frontend
echo "🎨 Starting frontend..."
cd ../frontend
npm install
npm run dev &
FRONTEND_PID=$!

echo "✅ Both services started!"
echo "📧 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"

# Wait for user input
read -p "Press Enter to stop services..."

kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
echo "👋 Services stopped."