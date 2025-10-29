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

### 📋 **Step 4: Configure YouTube Cookies (REQUIRED for Railway)**

**⚠️ IMPORTANT:** Railway runs in containers without browser access. YouTube requires cookies to prevent bot detection. You MUST add cookies for the app to work.

#### Export Cookies from Your Browser:

1. **Install Browser Extension** (Easiest Method):
   - Install "Get cookies.txt LOCALLY" extension:
     - Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
     - Firefox: https://addons.mozilla.org/firefox/addon/get-cookiestxt-locally/
   
2. **Export Cookies**:
   - Go to https://www.youtube.com (make sure you're logged in)
   - Click the extension icon
   - Click "Export" → Save as `cookies.txt`

3. **Alternative: Using yt-dlp** (if you have it installed):
   ```bash
   yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com"
   ```

#### Add Cookies to Railway (EASIEST METHOD):

**Method 1: Using YOUTUBE_COOKIES_TEXT (Recommended for Railway)**

1. **Open your `cookies.txt` file** in a text editor (Notepad, VS Code, etc.)
2. **Copy the ENTIRE contents** of the file (Ctrl+A, Ctrl+C)
3. **In Railway Dashboard**:
   - Open your project
   - Go to **Variables** tab (in left sidebar or **Settings** → **Environment Variables**)
   - Click **"+ New Variable"** or **"Add Variable"**
   - Name: `YOUTUBE_COOKIES_TEXT`
   - Value: **Paste the entire contents** of your cookies.txt file here
   - Click **"Add"** or **"Save"**
4. **Railway will auto-redeploy** - wait 1-2 minutes

**Method 2: Using File Path (Alternative)**

If you prefer to commit cookies.txt to your repo:
1. Add `cookies.txt` to your repository (⚠️ ONLY if repo is PRIVATE)
2. In Railway, add environment variable:
   - Name: `YOUTUBE_COOKIES_FILE`
   - Value: `/app/cookies.txt`
3. Redeploy

**🔒 Security Note:** 
- Cookies contain your session authentication. 
- **NEVER commit cookies.txt to a PUBLIC repository**
- Use Railway's environment variables (YOUTUBE_COOKIES_TEXT) - they're encrypted and private

### 📋 **Step 5: Test Your Deployed App**

Visit your Railway URL and test:
- Enter a YouTube URL
- Fetch formats
- Download a video/audio
- Check that everything works

### 🎉 **Step 6: Share Your App**

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

### If app shows "Sign in to confirm you're not a bot" error:
**This means cookies are not configured!**

1. **Check if cookies are set**:
   - Go to Railway → Your Project → Variables
   - Verify `YOUTUBE_COOKIES_TEXT` exists and has content
   
2. **Re-export cookies**:
   - Cookies expire! Re-export from your browser
   - Make sure you're logged into YouTube when exporting
   - Update Railway variable with new cookie content
   
3. **Verify cookie format**:
   - Cookie file should start with `# Netscape HTTP Cookie File`
   - Should contain multiple lines with domain, flags, path, etc.
   - Make sure you copied the ENTIRE file content

4. **Check Railway logs**:
   - Look for cookie-related errors
   - Redeploy after adding cookies

### If app doesn't work:
1. Check Railway logs for errors
2. Verify the app URL is correct
3. Try redeploying: Click on project → Settings → Deployments → Redeploy
4. **Most common issue**: Missing cookies - see error above

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

