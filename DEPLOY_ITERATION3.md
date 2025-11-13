# Deploy Iteration 3 to Railway

## Current Status ✅

- **Commit**: `e53d3eb9828492bcaccfe69f84b21962a39a3d04`
- **Branch**: `iteration3-baseline`
- **GitHub**: Already pushed ✅
- **Warnings**: 242 (best performance)

## Deployment Steps

### Option 1: Railway Dashboard (Recommended)

1. **Go to Railway Dashboard**
   - Visit: https://railway.app
   - Login with your GitHub account

2. **Open Your Project**
   - Find project: `idf-creator` (or the one connected to `web-production-3092c`)
   - If you don't have a project, create new one:
     - Click "New Project"
     - Select "Deploy from GitHub repo"
     - Choose: `giolux1235/idf-creator`

3. **Set Branch to iteration3-baseline**
   - Go to project Settings
   - Find "Source" or "GitHub" section
   - Change branch from `main` to `iteration3-baseline`
   - Save changes

4. **Deploy**
   - Railway will automatically deploy
   - Or click "Redeploy" button
   - Wait 2-5 minutes for deployment

5. **Verify Deployment**
   - Check "Deployments" tab for success
   - Check "Logs" tab for startup messages
   - Look for: "🌐 Starting IDF Creator Web Interface..."

### Option 2: Railway CLI

```bash
# Login to Railway
npx -y @railway/cli login

# Link to existing project (if needed)
cd "/Users/giovanniamenta/IDF - CREATOR 2/idf-creator"
npx -y @railway/cli link

# Deploy
npx -y @railway/cli up
```

## After Deployment

1. **Get the Service URL**
   - Railway dashboard → Settings → Domains
   - Should be: `https://web-production-3092c.up.railway.app` (or similar)

2. **Test the Deployment**
   ```bash
   cd "/Users/giovanniamenta/energyplus test"
   node comprehensive-idf-test.mjs
   ```

3. **Expected Results**
   - Should match iteration 3's results: **242 warnings**
   - All 5 tests should pass
   - No fatal errors

## Troubleshooting

### If URL Changed
- Update test files with new URL:
  - `comprehensive-idf-test.mjs`
  - `comprehensive-idf-test-iterative.mjs`
  - Other test files

### If Deployment Fails
- Check Railway logs for errors
- Verify `requirements.txt` is up to date
- Check `web_interface.py` starts correctly locally

### If Warnings Don't Match
- Verify correct branch is deployed (`iteration3-baseline`)
- Check commit hash matches: `e53d3eb9828492bcaccfe69f84b21962a39a3d04`
- Ensure no environment variable changes

## Verification Checklist

- [ ] Code pushed to GitHub ✅
- [ ] Railway project connected to GitHub repo
- [ ] Branch set to `iteration3-baseline`
- [ ] Deployment successful
- [ ] Service URL confirmed
- [ ] Test run shows ~242 warnings (matching iteration 3)

---

**Deployment Date**: $(date)
**Commit**: e53d3eb9828492bcaccfe69f84b21962a39a3d04
**Branch**: iteration3-baseline

