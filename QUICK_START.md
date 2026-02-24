# DriftGuardAI Frontend - Quick Start Guide

## 🚀 30-Second Start

### macOS/Linux
```bash
./start.sh
```

### Windows
```bash
start.bat
```

That's it! Frontend will open at `http://localhost:5173`

## 📋 Prerequisites

- **Node.js 16+** (download from nodejs.org)
- **Backend API** running at `http://localhost:5000`
- **Git** (optional, for cloning)

## 🛠️ Manual Setup

### 1. Install Dependencies
```bash
npm install
```

### 2. Create Environment File
```bash
cp .env.example .env
```

### 3. Update Backend URL (if needed)
Edit `.env`:
```env
VITE_API_BASE_URL=http://localhost:5000/api
```

### 4. Start Development Server
```bash
npm run dev
```

### 5. Open in Browser
```
http://localhost:5173
```

## 🔑 Default Credentials

Use credentials provided by your backend:

```
Email: demo@driftguardai.com
Password: [check with your team]
```

## 📁 Project Structure

```
src/
├── pages/           # Page components
├── components/      # Reusable components
├── services/        # API integration
├── styles/          # CSS styling
└── App.tsx          # Main app
```

## 🎯 Main Features

- **Dashboard**: View all models with status
- **Model Details**: Risk charts, drift/fairness metrics
- **Governance**: Policy evaluation and deployment
- **Audit**: Deployment history and audit trail
- **Authentication**: Secure JWT login

## 📊 Available Pages

1. **Login** (`/login`)
   - JWT authentication
   - Email/password form

2. **Dashboard** (`/dashboard`)
   - All models grid
   - Status indicators
   - Risk scores

3. **Model Detail** (`/model/:modelId`)
   - Risk history chart
   - Drift metrics
   - Fairness metrics
   - Governance status
   - Deployment controls

4. **Governance** (`/governance`)
   - Policy management
   - Model evaluation
   - Deployment workflow

5. **Audit** (`/audit`)
   - Deployment history
   - Audit trail

## 🔨 Development Commands

```bash
# Start development server (hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# TypeScript check
npx tsc --noEmit
```

## 🌐 Backend API

The frontend expects these endpoints:

### Auth
- `POST /api/auth/login`

### Models
- `GET /api/models`
- `GET /api/models/:id`
- `GET /api/models/:id/drift`
- `GET /api/models/:id/fairness`
- `GET /api/models/:id/risk-history`

### Governance
- `GET /api/governance/policies`
- `POST /api/governance/evaluate/:modelId`
- `POST /api/models/:id/deploy`

### Audit
- `GET /api/audit/deployments`
- `GET /api/audit/trail`

## ⚙️ Environment Variables

Create `.env` file:

```env
# Backend API URL
VITE_API_BASE_URL=http://localhost:5000/api

# Other variables (as needed)
```

## 🐛 Troubleshooting

### "Cannot find module 'react-router-dom'"
```bash
npm install
```

### "API not responding"
1. Check backend is running: `http://localhost:5000`
2. Verify `VITE_API_BASE_URL` in `.env`
3. Check backend CORS settings

### "Port 5173 already in use"
Change port:
```bash
npm run dev -- --port 3000
```

### "Build fails"
```bash
rm -rf node_modules package-lock.json
npm install
npm run build
```

## 📱 Testing on Mobile

Start development server, then:

```bash
# Get your machine IP
ipconfig getifaddr en0  # macOS/Linux
ipconfig              # Windows

# Open on mobile device
http://<your-ip>:5173
```

## 🚀 Production Deployment

### Build
```bash
npm run build
# Output: dist/ directory
```

### Deploy Options

**Vercel (Recommended)**
```bash
npm i -g vercel
vercel
```

**Netlify**
```bash
npm i -g netlify-cli
netlify deploy --prod --dir=dist
```

**GitHub Pages**
```bash
# Configure in vite.config.ts
# Set base: '/repo-name/'
npm run build
```

**Traditional Server**
```bash
# Copy dist/ to your web server
cp -r dist/* /var/www/html/
```

## 🔐 Security

- JWT tokens stored in localStorage
- Automatic token injection in requests
- Protected routes
- HTTPS recommended for production

## 📊 Performance

- Build time: ~7 seconds
- Bundle size: ~200KB gzipped
- Hot reload: instant
- Production optimized

## 🎯 Next Steps

1. **Start frontend**: `npm run dev`
2. **Login**: Use provided credentials
3. **Explore**: Navigate dashboard → model details → governance
4. **Test**: Try evaluating policies and deploying models
5. **Customize**: Modify components as needed

## 📚 Documentation

- **FRONTEND.md** - Complete feature documentation
- **IMPLEMENTATION.md** - Detailed technical guide
- **Backend API docs** - Check backend repository

## 🤝 Support

- Check backend logs for API issues
- Verify environment variables
- Clear browser cache (Ctrl+Shift+Delete)
- Check browser console (F12)

## ✅ Verification Checklist

- [ ] Node.js installed (v16+)
- [ ] Backend running on port 5000
- [ ] `.env` file created
- [ ] Dependencies installed (`npm install`)
- [ ] Dev server started (`npm run dev`)
- [ ] Browser opens to `http://localhost:5173`
- [ ] Can login with credentials
- [ ] Dashboard loads
- [ ] Can navigate to model details

## 🎉 You're Ready!

The DriftGuardAI frontend is ready for development and production use.

Happy coding! 🚀
