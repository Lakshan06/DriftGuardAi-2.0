#!/bin/bash

echo "🛡️  DriftGuardAI Frontend - Quick Start"
echo "======================================"
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+"
    exit 1
fi

echo "✅ Node.js version: $(node --version)"
echo "✅ npm version: $(npm --version)"
echo ""

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    echo ""
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Created .env with default backend URL: http://localhost:5000/api"
    echo "   Update this if your backend runs on a different URL"
    echo ""
fi

echo "🚀 Starting DriftGuardAI Frontend..."
echo "   Frontend: http://localhost:5173"
echo "   Backend: $(grep VITE_API_BASE_URL .env)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

npm run dev
