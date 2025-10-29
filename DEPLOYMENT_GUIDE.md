# 🚀 Deployment Guide - YouTube Downloader

## Complete Step-by-Step Instructions

### 📋 **Step 1: Prepare Your Files**

Your project is already ready! You have:
- ✅ `app.py` (Flask backend with HTML)
- ✅ `requirements.txt` (dependencies)
- ✅ `Procfile` (tells Railway how to run)
- ✅ `runtime.txt` (Python version)
- ✅ `.gitignore` (excludes unnecessary files)

### 📋 **Step 2: Create GitHub Repository**

1. **Go to GitHub**: https://github.com
   - Sign in or create account: https://github.com/signup

2. **Create New Repository**:
   - Click **"New"** (green button) or go to: https://github.com/new
   - Repository name: `yt-full-download` (or any name you like)
   - Description: "YouTube & YouTube Music Downloader with Glassmorphism UI"
   - Set to **Public** or **Private** (your choice)
   - **DON'T** check "Add a README"
   - Click **"Create repository"**

3. **Upload Your Code**:
   Open PowerShell in your project folder and run:

   ```powershell
   git init
   git add .
   git commit -m "Initial commit - YouTube Downloader App"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/yt-full-download.git
   git push -u origin main
   ```
   
   Replace `YOUR_USERNAME` with your GitHub username.

### 📋 **Step 3: Deploy to Railway**

1. **Sign Up/Login to Railway**:
   - Go to: https://railway.app
   - Click **"Start a New Project"** or **"Sign Up"**
   - Sign up with GitHub (recommended - one click)

2. **Deploy Your App**:
   - After login, click **"New Project"**
   - Select **"Deploy from GitHub repo"**
   - Authorize Railway to access GitHub if prompted
   - Select your repository: `yt-full-download`
   - Railway will auto-detect Flask and start deploying

3. **Wait for Deployment**:
   - Railway will show "Deploying..." 
   - Takes about 2-3 minutes
   - You'll see "Success" when done

4. **Get Your App URL**:
   - Click on your project
   - Look for "Settings" tab
   - Find **"Generate Domain"** and click it
   - Your app URL: `your-app-name.up.railway.app`

### 📋 **Step 4: Test Your Deployed App**

Visit your Railway URL and test:
- Enter a YouTube URL
- Fetch formats
- Download a video/audio
- Check that everything works

### 🎉 **Step 5: Share Your App**

Share your Railway URL with friends!
Example: `https://your-app-name.up.railway.app`

---

## 🔧 **Important Links:**

- **GitHub**: https://github.com
- **Railway**: https://railway.app
- **Railway Sign Up**: https://railway.app/signup
- **Your App** (after deployment): https://railway.app/dashboard

---

## ⚠️ **Troubleshooting:**

### If deployment fails:
1. Check Railway logs (click on your project → View Logs)
2. Make sure all files are pushed to GitHub
3. Verify `requirements.txt` has all dependencies

### If app doesn't work:
1. Check Railway logs for errors
2. Verify the app URL is correct
3. Try redeploying: Click on project → Settings → Deployments → Redeploy

---

## 📝 **Quick Commands:**

```powershell
# Navigate to project folder
cd "c:\Users\abhi5\OneDrive\Desktop\yt full download"

# Initialize git (if not done)
git init

# Add all files
git add .

# Commit
git commit -m "Ready for deployment"

# Push to GitHub
git push -u origin main
```

---

**Need Help?** Check:
- Railway Docs: https://docs.railway.app
- GitHub Docs: https://docs.github.com

