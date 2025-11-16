# Render is Using Old Commit

## Problem
Render is checking out commit `a171223` which doesn't have the `.dockerignore` fix.

The fix is in commit `7d67570` (and later), but Render is using an older commit.

## Solution

### When Creating New Service:

1. **In Render Dashboard**, when creating the service:
   - **Branch**: Make sure it's set to `main` (not a specific commit)
   - **Auto-Deploy**: Enable it (so it picks up new commits)

2. **Or use Blueprint**:
   - The `render.yaml` now specifies `branch: main`
   - This ensures Render uses the latest commits

### If Service Already Created:

1. **Go to Settings** → **Build & Deploy**
2. **Branch**: Change to `main` (if it's set to a specific commit)
3. **Manual Deploy** → **Clear build cache & deploy**

### Verify Latest Commit

After deployment, check build logs:
- Should show commit `e509994` or `7d67570` 
- Should NOT show commit `a171223`

If it still shows `a171223`, Render needs to be reconfigured to use `main` branch.

