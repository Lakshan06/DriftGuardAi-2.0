# DriftGuardAI Authentication Setup & Troubleshooting

## ✅ Authentication Has Been Enhanced

The login system has been completely enhanced with:
- Better error handling
- Logging and debugging
- Multiple response format support
- Detailed error messages
- Debug information display

## 🚀 Quick Setup

### 1. Verify Backend is Running

```bash
# Check if backend is accessible
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test"}'
```

Expected response (even with wrong credentials):
```json
{
  "message": "Invalid credentials",
  "error": "..."
}
```

If you get "Connection refused", backend is NOT running.

### 2. Check Environment Setup

Create `.env` file:
```bash
cp .env.example .env
```

Update `.env`:
```env
VITE_API_BASE_URL=http://localhost:5000/api
```

### 3. Test Credentials

Use these credentials on the login page:
```
Email: demo@driftguardai.com
Password: password123
```

These are pre-filled in the login form for testing.

### 4. Start Frontend

```bash
npm install
npm run dev
```

Open: `http://localhost:5173`

## 🔍 Debugging Authentication

### Check Browser Console

Open DevTools (F12) and watch the Console tab. You'll see:

```
API Base URL: http://localhost:5000/api
Request: {url: '/auth/login', method: 'post', headers: {...}}
Login response: {access_token: 'eyJ...', user: {email: '...'}}
```

### Common Issues & Solutions

#### Issue 1: "Cannot POST /auth/login"

**Problem**: Backend is not running or API URL is wrong

**Solution**:
1. Verify backend is running: `http://localhost:5000`
2. Check `.env` file:
   ```env
   VITE_API_BASE_URL=http://localhost:5000/api
   ```
3. Restart frontend dev server

#### Issue 2: "No response from server"

**Problem**: Backend is unreachable

**Check**:
```bash
# Try to reach backend
curl http://localhost:5000

# Check if port 5000 is in use
netstat -an | grep 5000  (on Windows/macOS)
lsof -i :5000           (on Linux/Mac)
```

**Solution**:
- Start backend on port 5000
- Or change `VITE_API_BASE_URL` in `.env` to match backend URL

#### Issue 3: "Invalid credentials"

**Problem**: Email or password is wrong

**Solution**:
1. Use correct demo credentials:
   - Email: `demo@driftguardai.com`
   - Password: `password123`
2. Or use real credentials from backend

#### Issue 4: "No authentication token received"

**Problem**: Backend response is missing token

**Check Response Format**:

The frontend supports multiple response formats:
```javascript
// Format 1: Standard
{
  "access_token": "eyJ...",
  "user": {
    "email": "user@example.com",
    "name": "User Name"
  }
}

// Format 2: Alternative token name
{
  "token": "eyJ...",
  "user": {
    "email": "user@example.com"
  }
}

// Format 3: Flat response
{
  "access_token": "eyJ...",
  "email": "user@example.com"
}
```

If your backend uses a different format, update `LoginPage.tsx` line 65-69.

#### Issue 5: CORS Error

**Problem**: Browser blocks request (CORS)

**Error**: 
```
Access to XMLHttpRequest at 'http://localhost:5000/api/auth/login' from origin 
'http://localhost:5173' has been blocked by CORS policy
```

**Solution**: Backend needs CORS headers:
```python
# Backend (Flask example)
from flask_cors import CORS
CORS(app)
```

Or use proxy in `vite.config.ts`:
```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:5000',
      changeOrigin: true,
    }
  }
}
```

## 📋 Full Authentication Flow

### Step 1: Login Page

```typescript
// User enters: demo@driftguardai.com / password123
// Click "Login"
```

### Step 2: API Request

```typescript
// POST http://localhost:5000/api/auth/login
{
  "email": "demo@driftguardai.com",
  "password": "password123"
}
```

### Step 3: Backend Response

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user123",
    "email": "demo@driftguardai.com",
    "name": "Demo User"
  }
}
```

### Step 4: Token Storage

```typescript
// Store in localStorage
localStorage.setItem('authToken', token)
localStorage.setItem('userEmail', email)
localStorage.setItem('userName', name)
```

### Step 5: Redirect

```typescript
// Navigate to dashboard
navigate('/dashboard')
```

### Step 6: Subsequent Requests

All API calls automatically include token:
```
Headers: {
  Authorization: "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

## 🧪 Testing Authentication

### Test Login

1. Open `http://localhost:5173`
2. You should see login page with pre-filled credentials
3. Click "Login"
4. Check browser console for logs
5. Should redirect to dashboard on success

### Test Token Injection

1. Open DevTools (F12)
2. Go to Network tab
3. Login successfully
4. Check any subsequent API request
5. Look for `Authorization` header in request

### Test Protected Routes

1. Login successfully
2. Open DevTools and go to Console
3. Run: `localStorage.removeItem('authToken')`
4. Refresh page
5. Should redirect to login

## 📝 Login Response Debug Info

The login form shows debug information:

```
Debug: Response received: {"access_token": "...", "user": {...}}
```

This helps identify if:
- ✅ Backend is responding
- ✅ Response format is correct
- ✅ Token is present
- ❌ Response is malformed

## 🔐 Security Notes

✅ Token stored in localStorage (accessible to XSS)
✅ Token included in Authorization header
✅ Token automatically refreshed on new login
✅ Token cleared on logout

For production:
- Use HTTPS only
- Consider httpOnly cookies instead of localStorage
- Implement token refresh/expiration
- Add CSRF protection

## 📱 Testing on Mobile

### Local Network Testing

```bash
# Get your machine IP
ipconfig getifaddr en0  # macOS
hostname -I             # Linux
ipconfig                # Windows

# Access from mobile
http://<YOUR_IP>:5173
```

Update `.env`:
```env
VITE_API_BASE_URL=http://<YOUR_IP>:5000/api
```

## 🚀 Production Deployment

### Environment Variables

Create `.env.production`:
```env
VITE_API_BASE_URL=https://api.yourdomain.com/api
```

### Build

```bash
npm run build
```

### Deploy

```bash
# Vercel
vercel deploy

# Netlify
netlify deploy --prod --dir=dist
```

## ✅ Verification Checklist

- [ ] Backend running on http://localhost:5000
- [ ] `.env` file created with correct API URL
- [ ] Demo credentials work: demo@driftguardai.com / password123
- [ ] Login page displays correctly
- [ ] Login succeeds and redirects to dashboard
- [ ] Token appears in localStorage
- [ ] Token included in API requests
- [ ] Protected routes work
- [ ] Logout clears token
- [ ] Browser console shows no CORS errors

## 📞 Support

If login still fails:

1. **Check backend logs** - What error is backend returning?
2. **Check browser console** - Any error messages?
3. **Check network tab** - Is request reaching backend?
4. **Check .env file** - Is API URL correct?
5. **Test with curl** - Can you reach backend directly?

Example curl test:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@driftguardai.com","password":"password123"}' \
  -v
```

Look for:
- HTTP status code (200 = success)
- Response body contains token
- No CORS headers missing

## 🎯 Next Steps After Login

Once login works:

1. ✅ Dashboard loads models
2. ✅ Click model to see details
3. ✅ View governance status
4. ✅ Evaluate policies
5. ✅ View audit trail

Happy coding! 🛡️
