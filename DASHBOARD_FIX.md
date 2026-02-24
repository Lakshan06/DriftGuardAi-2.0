# Dashboard Crash Fix - Complete Guide

## ✅ Issues Fixed

1. **Password Hashing** - Replaced bcrypt with PBKDF2-SHA256 to avoid compatibility issues
2. **API Routing** - Added `/api` prefix to all routers
3. **Login Endpoint** - Changed from form data to JSON
4. **Models Response** - Now returns proper PaginatedModelsResponse format
5. **Frontend API Calls** - Updated to use trailing slashes
6. **Error Handling** - Added ErrorBoundary component for crash recovery
7. **Defensive Null Checks** - Added null checks in DashboardPage

## 🚀 How to Run the Application

### Backend
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

### Frontend (in a new terminal)
```bash
npm run dev
# This will start Vite dev server on http://localhost:5173
```

## 🧪 Testing the Dashboard

1. **Login with**:
   - Email: `testuser@example.com`
   - Password: `password123`

2. **Access the dashboard** at `http://localhost:5173/dashboard`

3. **Register a model** using the "Register Model" button

## 🔍 Troubleshooting

### Dashboard Still Crashes?

1. **Check browser console** (F12) for JavaScript errors
2. **Check backend logs** for API errors
3. **Clear browser cache**: Ctrl+Shift+Delete
4. **Clear localStorage**: 
   ```javascript
   localStorage.clear()
   ```
5. **Restart both servers** (backend and frontend)

### Common Issues

**Issue**: "Cannot read property of undefined"
- **Fix**: The data from API is missing expected fields. Check backend response format.

**Issue**: 401 Unauthorized on /api/models/
- **Fix**: Token expired. Login again and save the new token to localStorage.

**Issue**: CORS errors
- **Fix**: Backend CORS middleware is enabled. Check if API server is running.

### Check API Health

```bash
# Check if backend is running
curl http://localhost:5000/health

# Login and get token
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"password123"}'

# Test models endpoint
curl -X GET "http://localhost:5000/api/models/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 📝 Database

The database is SQLite at: `backend/driftguardai.db`

To reset the database:
```bash
rm backend/driftguardai.db
# Restart the backend server
```

## 🎯 Key Files Changed

- `backend/app/main.py` - Added `/api` prefix to routers
- `backend/app/api/deps.py` - Fixed OAuth2 token URL
- `backend/app/api/model_registry.py` - Fixed response format
- `backend/app/core/security.py` - Replaced bcrypt with PBKDF2-SHA256
- `src/services/api.ts` - Improved error handling
- `src/services/dashboardAPI.ts` - Added trailing slashes
- `src/pages/DashboardPage.tsx` - Added defensive null checks
- `src/components/ErrorBoundary.tsx` - New error boundary component
- `src/App.tsx` - Wrapped with ErrorBoundary

## 🎉 Success Indicators

- ✅ Backend runs without bcrypt errors
- ✅ Login returns JWT token successfully
- ✅ API endpoints return data with correct format
- ✅ Frontend builds without errors
- ✅ Dashboard loads without crashing
- ✅ Models list displays (empty initially)
