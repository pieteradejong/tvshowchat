# Render Deployment Checklist

## Critical Issues Fixed ✅

1. ✅ **`.dockerignore`** - Removed `frontend/` exclusion (commit `7d67570`)
2. ✅ **`render.yaml`** - Added `branch: main` specification (commit `bf74fac`)
3. ✅ **Dockerfile** - Proper multi-stage build with frontend compilation

## Potential Issues to Watch For

### 1. Commit/Branch Mismatch ⚠️
**Problem**: Render using old commit (`a171223`) instead of latest (`bf74fac`)

**Solution**: 
- Ensure **Branch** is set to `main` in Render Dashboard
- Not a specific commit hash
- Use Blueprint (auto-detects `render.yaml` with `branch: main`)

### 2. Build Context Size
**Problem**: Large build context can slow builds

**Current**: ~4.26MB (acceptable)
**Optimization**: `.dockerignore` already excludes unnecessary files

### 3. Frontend Build Output
**Problem**: Vite outputs to `dist/` by default

**Verification**: Dockerfile copies from `/frontend/dist` to `./app/static` ✅

### 4. Static File Path Resolution
**Problem**: Path resolution in container (`/app/app/static` vs `/app/static`)

**Current**: Uses `Path(__file__).parent.parent.absolute() / "static"` 
- `__file__` = `/app/app/api/main.py`
- `parent.parent` = `/app/app`
- Static dir = `/app/app/static` ✅

### 5. Environment Variables
**Problem**: Missing required env vars

**Required**:
- `PORT` (Render sets automatically)
- `PYTHONUNBUFFERED=1` (in Dockerfile ENV)
- `PYTHONDONTWRITEBYTECODE=1` (in Dockerfile ENV)

### 6. Frontend Dependencies
**Problem**: `npm ci` fails if `package-lock.json` is out of sync

**Current**: Uses `npm ci` (requires exact lockfile match) ✅

### 7. Build Cache
**Problem**: Render may cache old build context

**Solution**: Use "Clear build cache & deploy" in Render Dashboard

## Verification Steps

After deployment, check:

1. **Build logs show**:
   ```
   ✅ Stage 1: Build frontend
   ✅ Stage 2: Build Python dependencies
   ✅ Stage 3: Production stage
   ```

2. **Runtime logs show**:
   ```
   ✅ Assets mounted from /app/app/static/assets
   ✅ Static files mounted from /app/app/static
   ```

3. **Root URL shows**:
   - ✅ React frontend HTML (not fallback message)
   - ✅ Frontend loads and API calls work

4. **Commit in logs**:
   - ✅ Should be `bf74fac` or `e509994` (latest)
   - ❌ Should NOT be `a171223` (old, without fix)

## Common Render Issues

### Issue: "Directory not found"
**Cause**: Using old commit or Python buildpack
**Fix**: Use Docker runtime with latest `main` branch

### Issue: "Build context too large"
**Cause**: Not excluding files in `.dockerignore`
**Fix**: Already optimized ✅

### Issue: "Frontend not showing"
**Cause**: Static files not copied or wrong path
**Fix**: Verify Dockerfile copies `dist/` to `app/static/` ✅

### Issue: "npm ci fails"
**Cause**: `package-lock.json` out of sync
**Fix**: Rebuild lockfile: `cd frontend && npm install`

## Next Steps

1. **In Render Dashboard**:
   - Create new service with Docker runtime
   - Set Branch to `main` (not specific commit)
   - Or use Blueprint (auto-configures everything)

2. **After deployment**:
   - Verify build uses latest commit
   - Check logs for successful frontend build
   - Test root URL shows React frontend

3. **If still failing**:
   - Check build logs for specific error
   - Verify commit hash matches latest (`git log --oneline -1`)
   - Use "Clear build cache & deploy"

