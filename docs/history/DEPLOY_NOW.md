# 🚀 Deploy to Railway - Step by Step

## ✅ Your Code is Ready!

All files are committed locally. Follow these steps:

---

## Step 1: Create GitHub Repository

1. Go to: **https://github.com/new**
2. Fill in:
   - **Repository name**: `idf-creator`
   - **Description**: `Intelligent EnergyPlus IDF Generator from Natural Language`
   - **Visibility**: Public or Private (your choice)
   - ⚠️ **Important**: Do NOT check "Add a README file"
   - ⚠️ **Important**: Do NOT add .gitignore or license (we have them)
3. Click **"Create repository"**

---

## Step 2: Push Your Code to GitHub

After creating the repo, GitHub will show you commands. Run these in your terminal:

```bash
cd "/Users/giovanniamenta/IDF - CREATOR "

# Add the remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/idf-creator.git

# Rename branch to main if needed
git branch -M main

# Push to GitHub
git push -u origin main
```

**Note**: Replace `YOUR_USERNAME` with your actual GitHub username.

---

## Step 3: Deploy on Railway

1. Go to: **https://railway.app**
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. You'll see a list of your repositories
5. Click **"idf-creator"**
6. Railway automatically:
   - Detects Python
   - Reads `Procfile`
   - Installs from `requirements.txt`
   - Starts `web_interface.py`
   - Provides a public URL

---

## Step 4: (Optional) Add Environment Variables

In Railway Dashboard → Your Project → Variables:

Add these if you have API keys:

```
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

---

## Step 5: Get Your URL

Railway provides a public URL like:
```
https://idf-creator-production.up.railway.app
```

**Share this URL with users!**

---

## Quick Copy-Paste Commands

### After creating GitHub repo, run:

```bash
cd "/Users/giovanniamenta/IDF - CREATOR "
git remote add origin https://github.com/YOUR_USERNAME/idf-creator.git
git branch -M main
git push -u origin main
```

### Then go to Railway and search for:
```
idf-creator
```

---

## What Happens During Deployment

Railway will:
1. ✅ Clone your GitHub repo
2. ✅ Detect it's a Python project
3. ✅ Install dependencies from `requirements.txt`
4. ✅ Run `Procfile` command: `python web_interface.py`
5. ✅ Start your Flask web server
6. ✅ Provide public URL

**Time**: ~2-5 minutes

---

## Test Your Deployment

1. Open your Railway URL
2. Enter building description
3. Click "Generate IDF File"
4. Download the file
5. Verify it works!

---

## Repository Name for Railway

**Search for**: `idf-creator`

Or your GitHub username will be visible when you connect Railway to GitHub.

---

## Need Help?

- GitHub: https://docs.github.com/en/get-started/quickstart/create-a-repo
- Railway: https://docs.railway.app/getting-started

---

## Summary

**GitHub Repository**: Create at https://github.com/new  
**Name**: `idf-creator`  
**Railway**: Deploy from that repo  
**URL**: Railway provides automatically  

**Do it now!** 🚀

