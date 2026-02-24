#!/bin/bash

echo "🛡️  DriftGuardAI - Authentication Diagnostic"
echo "==========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Node.js
echo "📋 Checking prerequisites..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js${NC} $NODE_VERSION"
else
    echo -e "${RED}❌ Node.js${NC} not found"
    exit 1
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✅ npm${NC} $NPM_VERSION"
else
    echo -e "${RED}❌ npm${NC} not found"
    exit 1
fi

echo ""

# Check backend
echo "🔍 Checking backend connectivity..."
if curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test","password":"test"}' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend API${NC} is accessible at http://localhost:5000/api"
else
    echo -e "${RED}❌ Backend API${NC} not responding at http://localhost:5000"
    echo "   Make sure backend is running:"
    echo "   cd backend && npm start"
    exit 1
fi

echo ""

# Check .env file
echo "📝 Checking environment setup..."
if [ -f ".env" ]; then
    API_URL=$(grep VITE_API_BASE_URL .env | cut -d'=' -f2)
    echo -e "${GREEN}✅ .env file${NC} found"
    echo "   API URL: $API_URL"
else
    echo -e "${YELLOW}⚠️  .env file${NC} not found"
    echo "   Creating from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Created${NC} .env file"
    else
        echo -e "${RED}❌ .env.example${NC} not found"
    fi
fi

echo ""

# Check dependencies
echo "📦 Checking dependencies..."
if [ -d "node_modules" ]; then
    echo -e "${GREEN}✅ Dependencies${NC} installed"
else
    echo -e "${YELLOW}⚠️  Dependencies${NC} not installed"
    echo "   Run: npm install"
fi

echo ""

# Summary
echo "✅ Diagnostic complete!"
echo ""
echo "Next steps:"
echo "1. npm install         (if needed)"
echo "2. npm run dev         (start frontend)"
echo "3. Open http://localhost:5173 in browser"
echo "4. Use credentials: demo@driftguardai.com / password123"
echo ""
