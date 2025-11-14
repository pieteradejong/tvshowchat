# Deployment Guide for Render

## Critical: Use Docker Deployment

**IMPORTANT**: This application **must** use Docker deployment on Render. The Python buildpack will NOT work because:
1. The frontend needs to be built (requires Node.js)
2. Static files need to be copied to the correct location
3. Multi-stage Docker build handles both frontend and backend

## Setting Up Docker Deployment on Render

### Option 1: Using Render Blueprint (Recommended)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml` and create the service with Docker

### Option 2: Manual Docker Setup

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New"** → **"Web Service"**
3. Connect your GitHub repository
4. **CRITICAL**: Set the following:
   - **Environment**: `Docker` (NOT Python!)
   - **Dockerfile Path**: `./Dockerfile` (or leave blank if in root)
   - **Docker Context**: `.` (root directory)
   - **Build Command**: (leave blank - handled by Dockerfile)
   - **Start Command**: (leave blank - handled by Dockerfile CMD)
5. Configure settings:
   - **Plan**: Starter (512MB) or Standard (2GB recommended)
   - **Health Check Path**: `/health`
   - **Auto-Deploy**: Enabled (optional)

### Environment Variables

These are optional (defaults work):
- `PORT=8000` (Render sets this automatically)
- `PYTHONUNBUFFERED=1`
- `PYTHONDONTWRITEBYTECODE=1`

## Verifying Docker Deployment

After deployment, check the logs:

1. **Build logs should show:**
   ```
   # Stage 1: Build frontend
   # Stage 2: Build Python dependencies
   # Stage 3: Production stage
   ```

2. **Runtime logs should show:**
   ```
   Assets mounted from /app/app/static/assets
   Static files mounted from /app/app/static
   ```

3. **If you see errors like:**
   ```
   RuntimeError: Directory '/opt/render/project/src/app/static' does not exist
   ```
   This means Render is using the Python buildpack instead of Docker.

## Troubleshooting

### Problem: "Directory does not exist" error

**Cause**: Render is using Python buildpack instead of Docker.

**Solution**:
1. Go to your service settings in Render Dashboard
2. Change **Environment** from "Python" to "Docker"
3. Set **Dockerfile Path** to `./Dockerfile`
4. Redeploy

### Problem: Frontend not showing

**Cause**: Frontend build might have failed or static files not copied.

**Solution**:
1. Check build logs for frontend build errors
2. Verify `app/static/index.html` exists in the Docker image
3. Check that assets are being served at `/assets/*`

### Problem: API routes not working

**Cause**: Route order might be wrong.

**Solution**: Verify API routes are registered before static file mounts in `app/api/main.py`.

## Local Testing

Test the Docker setup locally before deploying:

```bash
# Build the image
docker build -t tvshowchat-api .

# Run the container
docker run -p 8000:8000 tvshowchat-api

# Test the frontend
curl http://localhost:8000/
# Should return HTML, not JSON
```

## Expected Behavior

- **Root (`/`)**: Serves React frontend HTML
- **Assets (`/assets/*`)**: Serves CSS, JS, images
- **API (`/api/*`)**: Serves API endpoints
- **Health (`/health`)**: Health check endpoint

If you see JSON at the root instead of HTML, Docker deployment is not being used.

