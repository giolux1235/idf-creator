# 🚂 Railway Deployment Instructions

## Ready to Deploy!

Your IDF Creator is ready for Railway. Follow these steps:

---

## Step 1: Create GitHub Repository

### Option A: Using GitHub CLI (If installed)
```bash
# Install GitHub CLI if not installed
# brew install gh (on Mac)

# Create repo
gh repo create idf-creator --public --source=. --remote=origin

# Push to GitHub
git push -u origin main
```

### Option B: Manual GitHub Creation

1. Go to https://github.com/new
2. Create new repository named `idf-creator`
3. **Don't** initialize with README (we have one)
4. Copy the commands and run:
```bash
git remote add origin https://github.com/YOUR_USERNAME/idf-creator.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy to Railway

### Via Railway Dashboard:

1. **Go to Railway**: https://railway.app
2. **Sign up** with GitHub
3. **Click "New Project"**
4. **Select "Deploy from GitHub repo"**
5. **Choose your repo** (`idf-creator`)
6. **Railway auto-detects and deploys!** ✨

### Via Railway CLI:

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize and deploy
railway init
railway up
```

---

## Step 3: Add Environment Variables

In Railway Dashboard → Your Project → Variables:

```
OPENAI_API_KEY=sk-your-key-here (optional, for LLM features)
ANTHROPIC_API_KEY=sk-ant-your-key (optional, for Claude)
```

**Note**: Railway automatically sets `PORT` - don't set it manually.

---

## Step 4: Get Your URL

Railway provides a public URL like:
```
https://idf-creator-production.up.railway.app
```

Share this with users!

---

## What's Included

✅ Complete IDF Creator with all features:
- Natural language input
- Document upload
- LLM integration (OpenAI/Anthropic)
- 6 enhancement modules
- CBECS validation
- Web interface
- CLI interface
- EnergyPlus compatibility

✅ Deployment files:
- `Procfile` - Tells Railway how to start
- `runtime.txt` - Python version
- `railway.json` - Railway config
- `requirements.txt` - Dependencies
- `web_interface.py` - Web app

---

## Testing After Deployment

1. Open your Railway URL
2. Enter building description
3. Add documents (optional)
4. Click "Generate IDF File"
5. Download the IDF
6. Run in EnergyPlus to verify

---

## Cost

**Railway Free Tier**:
- $5 credit/month
- Perfect for testing!
- App uses ~50MB RAM
- ~100 requests/day

---

## Commands Summary

```bash
# 1. Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/idf-creator.git
git push -u origin main

# 2. Deploy to Railway (via dashboard at railway.app)

# 3. Monitor
railway logs  # Via CLI
# Or check dashboard for logs
```

---

## Troubleshooting

### "Module not found" error
- Check `requirements.txt` includes all dependencies
- Railway installs from requirements.txt automatically

### App won't start
- Check logs: `railway logs`
- Verify `Procfile` content
- Ensure port is from env var, not hardcoded

### Files not persisting
- Railway resets files between deploys
- Use Railway Volumes for persistence
- Or store files in external storage

---

## Next Steps

✅ Code committed locally
⏭️ Push to GitHub
⏭️ Deploy on Railway
⏭️ Set environment variables
⏭️ Share your URL!

**Go to https://railway.app and deploy now!** 🚀

