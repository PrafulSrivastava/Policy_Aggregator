# Debugging Guide - White Screen Issue

## Logging System

I've added comprehensive logging throughout the application. All logs are prefixed with tags like `[INDEX]`, `[APP]`, `[AUTH]`, etc. to make them easy to filter.

## Expected Log Flow

When the app loads successfully, you should see logs in this order:

### 1. Initialization
```
[INDEX] Initializing React app...
[INDEX] React version: 19.2.3
[INDEX] Environment: development
[INDEX] API Base URL: http://localhost:8000 (default)
[INDEX] ✅ Root element found: <div id="root">
[INDEX] Creating React root...
[INDEX] ✅ React root created
[INDEX] Rendering app with ErrorBoundary...
[INDEX] ✅ App render call completed
[INDEX] Waiting for components to mount...
```

### 2. App Component
```
[APP] App component loading...
[APP] App component rendering, setting up providers...
[APP] AppRoutes component rendering...
```

### 3. Authentication
```
[AUTH] AuthProvider initializing...
[AUTH] useEffect running, checking for existing session...
[AUTH] Token found in localStorage: No (or Yes with length)
[AUTH] ⚠️ No token found, user not authenticated (or ✅ Token found)
[AUTH] Setting isLoading to false
[AUTH] Rendering AuthProvider with state: { isAuthenticated: false, isLoading: false, hasError: false }
```

### 4. Routing
```
[APP] ⏳ Showing loading state... (if isLoading is true)
OR
[APP] 🔒 Not authenticated, showing login routes (if not authenticated)
OR
[APP] ✅ Authenticated, showing protected routes (if authenticated)
```

### 5. Page Components
```
[LOGIN] Login page component rendering... (if on login page)
OR
[DASHBOARD] Dashboard component rendering... (if on dashboard)
[LAYOUT] Layout component rendering with children
[NAVBAR] Navbar component rendering...
```

### 6. API Calls (if authenticated)
```
[API] Initializing API client...
[API] Base URL: http://localhost:8000
[API] ✅ API client initialized
[API] Request: GET /api/dashboard - Token attached (or No token)
[API] ✅ Response: GET /api/dashboard - Status: 200
```

## What to Look For

### If you see logs stopping at a certain point:

1. **Stops at `[INDEX]`**: React isn't mounting
   - Check for JavaScript errors in console
   - Verify `index.tsx` is loading (Network tab)

2. **Stops at `[APP]`**: App component has an error
   - Check ErrorBoundary for caught errors
   - Look for import errors

3. **Stops at `[AUTH]`**: AuthContext has an issue
   - Check if `useAuth` hook is being called outside provider
   - Verify localStorage access

4. **Stops at `[API]`**: API initialization failed
   - Check if axios is installed
   - Verify environment variables

5. **No logs at all**: JavaScript isn't executing
   - Check browser console for syntax errors
   - Verify Vite dev server is running
   - Check Network tab for failed module loads

## Common Error Patterns

### Error: "Cannot find module"
```
Look for: Module not found errors in console
Fix: Run `npm install`
```

### Error: "useAuth must be used within AuthProvider"
```
Look for: [AUTH] errors about context
Fix: Check component hierarchy - all components using useAuth must be inside <AuthProvider>
```

### Error: "Failed to fetch" or CORS errors
```
Look for: [API] ❌ Response error with status 0 or CORS errors
Fix: Check backend is running and CORS is configured
```

### Error: White screen with no logs
```
Look for: Nothing in console
Fix: 
1. Check if JavaScript is enabled
2. Check Network tab for failed requests
3. Try hard refresh (Ctrl+Shift+R)
4. Check if there are syntax errors preventing execution
```

## Filtering Logs in Console

You can filter logs by prefix:
- `[INDEX]` - Initialization
- `[APP]` - App component
- `[AUTH]` - Authentication
- `[API]` - API calls
- `[LOGIN]` - Login page
- `[DASHBOARD]` - Dashboard page
- `[LAYOUT]` - Layout component
- `[NAVBAR]` - Navbar component
- `[ERROR-BOUNDARY]` - Caught errors

## Next Steps

1. **Open browser DevTools (F12)**
2. **Go to Console tab**
3. **Refresh the page**
4. **Copy all logs** (especially any red errors)
5. **Share the logs** so we can identify where it's failing

The logs will show exactly where the application is stopping, making it much easier to fix the white screen issue.


