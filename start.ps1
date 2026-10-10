# TempMail Pro - Quick Start Script (Windows)

Write-Host "🚀 Starting TempMail Pro..." -ForegroundColor Cyan

# Check if Docker is available
if (Get-Command docker -ErrorAction SilentlyContinue) {
    Write-Host "🐳 Docker detected. Using Docker Compose..." -ForegroundColor Green
    docker-compose up -d
    Write-Host "✅ Services started!" -ForegroundColor Green
    Write-Host "📧 Frontend: http://localhost:3000" -ForegroundColor Yellow
    Write-Host "🔧 Backend API: http://localhost:8000" -ForegroundColor Yellow
    Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Yellow
    exit 0
}

Write-Host "📦 Docker not found. Starting locally..." -ForegroundColor Yellow

# Backend
Write-Host "🔧 Starting backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt; uvicorn app.main:app --reload --port 8000"

# Frontend
Write-Host "🎨 Starting frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm install; npm run dev"

Write-Host "✅ Both services starting!" -ForegroundColor Green
Write-Host "📧 Frontend: http://localhost:3000" -ForegroundColor Yellow
Write-Host "🔧 Backend API: http://localhost:8000" -ForegroundColor Yellow

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")