# Deploying IDF Creator to Railway 🚂

## Quick Deploy (5 minutes)

### Step 1: Create Railway Account

1. Go to https://railway.app
2. Sign up with GitHub (easiest)
3. Click "New Project"

### Step 2: Deploy from GitHub

**Option A: Deploy Existing Repo**
1. Click "Deploy from GitHub repo"
2. Select your repository
3. Railway automatically detects Python

**Option B: Connect via CLI**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

### Step 3: Set Environment Variables

In Railway dashboard → Variables tab, add:

```
OPENAI_API_KEY=sk-your-openai-key (optional)
ANTHROPIC_API_KEY=sk-ant-your-key (optional)
ENVIRONMENT=production
```

### Step 4: Deploy!

Railway will:
- ✅ Install dependencies from `requirements.txt`
- ✅ Run `railway_setup.sh` (if exists)
- ✅ Start `web_interface.py` on port provided by Railway
- ✅ Expose URL automatically

### Step 5: Get Your URL

Railway provides a public URL like:
```
https://your-project.up.railway.app
```

Share this URL and use it directly!

---

## Manual Setup (If Needed)

### 1. Add Python Version

Create `runtime.txt`:
```
python-3.11.0
```

### 2. Create Procfile

Create `Procfile`:
```
web: python web_interface.py
```

### 3. Update Web Interface for Railway

The `web_interface.py` is already configured to read Railway's PORT environment variable.

---

## Environment Variables

Set these in Railway Dashboard → Variables:

### Required
```
PORT=auto (Railway sets this automatically)
```

### Optional but Recommended
```
OPENAI_API_KEY=sk-your-key
ANTHROPIC_API_KEY=sk-ant-your-key
ENVIRONMENT=production
```

### Optional Configuration
```
PYTHONUNBUFFERED=1
```

---

## File Structure for Railway

```
IDF-Creator/
├── web_interface.py      # Main web app (entry point)
├── Procfile              # Startup command
├── runtime.txt           # Python version
├── requirements.txt      # Dependencies
├── railway.json          # Railway config
├── railway_config.py     # Config helper
├── railway_setup.sh      # Setup script
├── main.py               # IDF generation
├── nlp_cli.py            # CLI interface
├── src/
│   ├── nlp_building_parser.py
│   ├── enhanced_location_fetcher.py
│   ├── professional_idf_generator.py
│   └── ... (all other modules)
├── config.yaml           # Configuration
└── artifacts/            # Output directory
    └── desktop_files/
        └── idf/          # Generated IDF files
```

---

## Deployment Checklist

### Before Deploying
- [ ] Test locally: `python web_interface.py`
- [ ] Check `requirements.txt` is up to date
- [ ] Set API keys in Railway dashboard
- [ ] Ensure `Procfile` exists
- [ ] Check `runtime.txt` for Python version

### After Deploying
- [ ] Test URL is accessible
- [ ] Try uploading a description
- [ ] Check logs for errors
- [ ] Test IDF generation
- [ ] Verify downloads work

---

## Railway Features to Use

### Custom Domain

1. Go to Settings → Domains
2. Add custom domain
3. Railway provides SSL automatically

### Environment Variables

All sensitive keys should be in Railway dashboard:
- Don't commit API keys to repo
- Use Railway's environment variables
- They're encrypted automatically

### Persistent Storage

By default, files uploaded/deleted between deployments.
To persist, use Railway's volume storage:
1. Settings → Volumes
2. Mount `/app/artifacts`
3. Files persist across deployments

### Monitoring

Railway provides:
- Logs (real-time)
- Metrics (CPU, memory, network)
- Alerts (via email/webhook)

---

## Troubleshooting

### Deployment Fails

**Problem**: Build fails

**Solution**:
```bash
# Check Railway logs
railway logs

# Common issues:
# - Missing dependencies in requirements.txt
# - Python version mismatch
# - Missing files
```

### App Starts But Won't Load

**Problem**: 502 Bad Gateway

**Solution**:
```bash
# Check web_interface.py is configured for Railway:
# 1. Should listen on port from PORT env var
# 2. Should listen on 0.0.0.0 (all interfaces)

# Verify in logs:
railway logs
```

### API Key Not Working

**Problem**: LLM features not working

**Solution**:
1. Go to Railway dashboard → Variables
2. Add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
3. Redeploy or restart

---

## Cost Estimate

### Railway Pricing

**Free Tier**:
- $5 credit/month (enough for development)
- 500 hours/month compute
- 100 GB bandwidth

**Hobby** ($5/month):
- $5 credit included
- Pay as you go after

### IDF Creator Usage

**Typical usage**:
- Web app: ~50MB RAM
- Per request: ~200ms compute
- Bandwidth: ~500KB per IDF generated

**Free tier handles**:
- ~100 requests/day
- Light to moderate usage

---

## Alternative Deployments

### Heroku

Similar to Railway but more expensive:
```bash
heroku create
git push heroku main
```

### Render

Free tier with limitations:
1. Sign up at render.com
2. New Web Service
3. Connect GitHub repo
4. Deploy

### Fly.io

Good for global distribution:
```bash
fly launch
fly deploy
```

---

## Monitoring After Deployment

### Check Logs

```bash
# Railway CLI
railway logs

# Or in dashboard
railway dashboard → Logs tab
```

### Monitor Performance

Railway Dashboard shows:
- CPU usage
- Memory usage
- Request count
- Response times

### Set Up Alerts

1. Dashboard → Settings → Notifications
2. Add email/webhook for alerts
3. Get notified of errors/downtime

---

## Production Checklist

Before going live:

- [ ] Set all environment variables
- [ ] Test all features end-to-end
- [ ] Add custom domain (optional)
- [ ] Set up monitoring/alerts
- [ ] Configure backup/volumes
- [ ] Test error handling
- [ ] Review security
- [ ] Add rate limiting (if needed)

---

## Quick Reference

### Deploy Command

```bash
# Via CLI
railway up

# Via GitHub
# Just push to main branch
git push origin main
```

### Environment Variables

```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### View Logs

```bash
railway logs
```

### Restart App

```bash
railway restart
```

### Access Database

Railway provides PostgreSQL if needed:
```
DATABASE_URL=postgresql://...
```

---

## Summary

✅ **Railway deployment is ready!**

Just:
1. Push code to GitHub
2. Connect to Railway
3. Set API keys
4. Deploy!

Your app will be live at: `https://your-project.up.railway.app`

🎉 **Share your IDF Creator with the world!**

