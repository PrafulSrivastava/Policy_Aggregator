# White Screen - No Logs Debugging Checklist

## If NO logs appear at all, follow these steps:

### Step 1: Verify Dev Server is Running
```bash
# Check if server is running on port 3000
# You should see: "Local: http://localhost:3000/"
```

### Step 2: Check Browser Console Settings
1. Open DevTools (F12)
2. Go to **Console** tab
3. **Check the filter settings:**
   - Make sure "All levels" is selected (not just Errors)
   - Clear any text filters
   - Make sure console isn't cleared automatically

### Step 3: Test if JavaScript is Working
1. Open browser console
2. Type: `console.log('TEST')` and press Enter
3. **If this doesn't show up**, JavaScript might be disabled
4. Check browser settings → Site permissions → JavaScript

### Step 4: Check Network Tab
1. Open DevTools → **Network** tab
2. Refresh the page
3. Look for:
   - `index.tsx` - Should load with status 200
   - `index.css` - Should load with status 200
   - Any files with **red status** (404, 500, etc.)

### Step 5: Check for Console Errors
1. Look for **red error messages** in console
2. Common errors:
   - "Failed to load module"
   - "Cannot find module"
   - "Unexpected token"
   - CORS errors

### Step 6: Test Simple HTML
1. Navigate to: `http://localhost:3000/test-simple.html`
2. **If this works**, the issue is with React/TypeScript
3. **If this doesn't work**, the dev server isn't serving files

### Step 7: Check Browser
1. Try a **different browser** (Chrome, Firefox, Edge)
2. Try **incognito/private mode**
3. Clear browser cache (Ctrl+Shift+Delete)

### Step 8: Verify File Structure
Make sure these files exist:
- ✅ `frontend/index.html`
- ✅ `frontend/index.tsx`
- ✅ `frontend/index.css`
- ✅ `frontend/App.tsx`
- ✅ `frontend/vite.config.ts`

### Step 9: Check Vite Dev Server Output
Look at the terminal where `npm run dev` is running:
- Should show: "Local: http://localhost:3000/"
- Should show: "ready in X ms"
- **Any errors in the terminal?**

### Step 10: Manual Test
1. Open browser
2. Go to: `http://localhost:3000`
3. Right-click → **View Page Source**
4. **Do you see the HTML?** (Should see `<div id="root">`)
5. **Is there a script tag?** (Vite injects this automatically)

## What to Report

If still no logs, please provide:

1. **Browser console screenshot** (even if empty)
2. **Network tab screenshot** (showing all requests)
3. **Terminal output** from `npm run dev`
4. **Browser name and version**
5. **Any error messages** (even if they seem unrelated)

## Quick Test Commands

```bash
# In frontend directory:

# 1. Check if dev server is running
netstat -ano | findstr :3000

# 2. Kill any process on port 3000 (if needed)
# Then restart: npm run dev

# 3. Check for TypeScript errors
npx tsc --noEmit

# 4. Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

## Expected Behavior

When you open `http://localhost:3000`, you should see:

1. **In HTML source:** `<div id="root">` exists
2. **In console:** At minimum, the inline script log: `🔴 HTML SCRIPT TAG: This should appear immediately`
3. **In Network tab:** `index.tsx` loads successfully
4. **On screen:** Either login page or dashboard (not white screen)

If NONE of these happen, the dev server isn't working correctly.


