# 🚂 Deploy IDF Creator to Railway

## Quick Start (5 Minutes)

### 1. Create Railway Account
Go to https://railway.app and sign up with GitHub

### 2. Deploy Your Project

**Option A: From GitHub (Recommended)**
```
1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Choose your repository
4. Railway auto-detects and deploys!
```

**Option B: From CLI**
```bash
npm i -g @railway/cli
railway login
railway init
railway up
```

### 3. Set API Keys (Optional)

In Railway Dashboard → Variables:
```
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
```

### 4. Done! 

Your app is live at: `https://your-project.up.railway.app`

---

## Files Created for Railway

✅ `railway.json` - Railway configuration
✅ `Procfile` - Startup command
✅ `runtime.txt` - Python version
✅ `railway_config.py` - Config helper
✅ `railway_setup.sh` - Setup script
✅ `web_interface.py` - Updated for Railway
✅ `.railwayignore` - Files to ignore

---

## What Gets Deployed

- ✅ Web interface (Flask app)
- ✅ All modules and enhancements
- ✅ Natural language processing
- ✅ Document upload
- ✅ IDF generation
- ✅ Full EnergyPlus compatibility

---

## Environment Variables

Set in Railway Dashboard:

```
OPENAI_API_KEY=sk-... (optional, for LLM features)
ANTHROPIC_API_KEY=sk-... (optional, for Claude)
PORT=auto (Railway sets automatically)
```

---

## Cost

**Railway Free Tier**:
- $5 credit/month
- 500 hours compute
- Perfect for testing!

**Estimated Usage**:
- Web app: ~50MB RAM
- Per request: ~$0.0001 (with LLM)
- Free tier: ~100 requests/day

---

## Quick Deploy Commands

```bash
# Push to GitHub
git add .
git commit -m "Ready for Railway"
git push origin main

# Deploy (if using CLI)
railway up

# View logs
railway logs

# Open in browser
railway open
```

---

## Next Steps

1. **Deploy** to Railway
2. **Get URL** from dashboard
3. **Test** the web interface
4. **Share** with users!

🎉 **Your IDF Creator is ready to deploy to Railway!**

