# How to Switch Render Service to Docker

Since Render doesn't allow changing the runtime type after creation, you have two options:

## Option 1: Create New Service via Blueprint (Easiest)

1. **Go to Render Dashboard** → Click **"New"** → **"Blueprint"**
2. **Connect your repository**: `pieteradejong/tvshowchat`
3. Render will automatically:
   - Detect `render.yaml`
   - Create a new service with Docker runtime
   - Configure all settings automatically
4. **Delete the old service** after verifying the new one works

## Option 2: Manually Create New Docker Service

1. **Create New Service:**
   - Render Dashboard → **"New"** → **"Web Service"**
   - Connect repository: `pieteradejong/tvshowchat`
   - **Branch**: `main`

2. **CRITICAL Settings:**
   - **Runtime**: Select **"Docker"** (NOT Python!)
   - **Name**: `tvshowchat` (or keep default)
   - **Region**: Choose closest to you
   - **Branch**: `main`

3. **Build & Deploy Settings:**
   - **Dockerfile Path**: `./Dockerfile` (or leave blank)
   - **Docker Context**: `.` (root)
   - **Build Command**: (leave blank)
   - **Start Command**: (leave blank - uses Dockerfile CMD)

4. **Service Settings:**
   - **Plan**: Starter (512MB) or Standard (2GB)
   - **Auto-Deploy**: Enabled
   - **Health Check Path**: `/health`

5. **Environment Variables** (add these):
   - `PYTHONUNBUFFERED=1`
   - `PYTHONDONTWRITEBYTECODE=1`
   - `PORT=8000` (optional - Render sets this)

6. **Create Service** and wait for deployment

7. **After it works**, delete the old Python service

## Option 3: Delete and Recreate (If you want to keep the same URL)

**Warning**: This will give you a new URL unless you pay for a custom domain.

1. **Delete the current service** (Settings → Danger Zone → Delete Service)
2. **Create new service** using Option 1 or 2 above

## Verifying Docker is Working

After deployment, check the logs:

✅ **Build logs should show:**
```
# Stage 1: Build frontend
# Stage 2: Build Python dependencies  
# Stage 3: Production stage
```

✅ **Runtime logs should show:**
```
Assets mounted from /app/app/static/assets
Static files mounted from /app/app/static
```

✅ **Root URL should show:** React frontend HTML (not the fallback message)

## Quick Test

After switching to Docker, visit your Render URL:
- Should show: React frontend interface
- Should NOT show: "Frontend not available. API is running" message

