@echo off
setlocal enabledelayedexpansion

echo.
echo 🛡️  DriftGuardAI - Authentication Diagnostic
echo ============================================
echo.

REM Check Node.js
echo 📋 Checking prerequisites...
where node >nul 2>nul
if errorlevel 1 (
    echo ❌ Node.js not found
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
    echo ✅ Node.js !NODE_VERSION!
)

where npm >nul 2>nul
if errorlevel 1 (
    echo ❌ npm not found
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
    echo ✅ npm !NPM_VERSION!
)

echo.

REM Check backend
echo 🔍 Checking backend connectivity...
powershell -Command "try { $null = Invoke-WebRequest -Uri 'http://localhost:5000/api/auth/login' -Method POST -ContentType 'application/json' -Body '{\"email\":\"test\",\"password\":\"test\"}' -ErrorAction SilentlyContinue; exit 0 } catch { exit 1 }"
if errorlevel 1 (
    echo ❌ Backend API not responding at http://localhost:5000
    echo    Make sure backend is running:
    echo    cd backend ^&^& npm start
    exit /b 1
) else (
    echo ✅ Backend API is accessible at http://localhost:5000/api
)

echo.

REM Check .env file
echo 📝 Checking environment setup...
if exist ".env" (
    echo ✅ .env file found
    for /f "tokens=2 delims==" %%i in ('findstr /C:"VITE_API_BASE_URL" .env') do set API_URL=%%i
    echo    API URL: !API_URL!
) else (
    echo ⚠️  .env file not found
    if exist ".env.example" (
        copy .env.example .env
        echo ✅ Created .env file
    ) else (
        echo ❌ .env.example not found
    )
)

echo.

REM Check dependencies
echo 📦 Checking dependencies...
if exist "node_modules" (
    echo ✅ Dependencies installed
) else (
    echo ⚠️  Dependencies not installed
    echo    Run: npm install
)

echo.

REM Summary
echo ✅ Diagnostic complete!
echo.
echo Next steps:
echo 1. npm install         (if needed)
echo 2. npm run dev         (start frontend)
echo 3. Open http://localhost:5173 in browser
echo 4. Use credentials: demo@driftguardai.com / password123
echo.
