@echo off
echo 🛡️  DriftGuardAI Frontend - Quick Start
echo ======================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 16+
    exit /b 1
)

echo ✅ Node.js version:
node --version
echo ✅ npm version:
npm --version
echo.

REM Check if dependencies are installed
if not exist "node_modules" (
    echo 📦 Installing dependencies...
    call npm install
    echo.
)

REM Check if .env exists
if not exist ".env" (
    echo ⚙️  Creating .env file from template...
    copy .env.example .env
    echo 📝 Created .env with default backend URL: http://localhost:5000/api
    echo    Update this if your backend runs on a different URL
    echo.
)

echo 🚀 Starting DriftGuardAI Frontend...
echo    Frontend: http://localhost:5173
echo    Backend: http://localhost:5000/api
echo.
echo Press Ctrl+C to stop
echo.

call npm run dev
