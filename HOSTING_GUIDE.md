# Hosting Guide - Free Platforms

This guide will help you deploy your YouTube Downloader to free hosting platforms.

## 🚀 Quick Deployment Options

### Option 1: Render.com (Recommended - Easiest)

1. **Sign up** at [render.com](https://render.com) (free tier available)

2. **Create a New Web Service:**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository or push code manually

3. **Configure the service:**
   - **Name:** youtube-downloader (or your choice)
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Python Version:** 3.11.6

4. **Deploy:**
   - Click "Create Web Service"
   - Render will automatically build and deploy your app
   - Your app will be live at `https://your-app-name.onrender.com`

**Note:** Render free tier spins down after 15 minutes of inactivity. First request may take ~30 seconds to wake up.

---

### Option 2: Railway.app

1. **Sign up** at [railway.app](https://railway.app) (free tier with $5 credit/month)

2. **Deploy:**
   - Click "New Project"
   - Select "Deploy from GitHub repo" or "Upload files"
   - Railway auto-detects Python and deploys

3. **Configure:**
   - Railway automatically detects `Procfile` and installs dependencies
   - No additional configuration needed!

4. **Your app will be live** at `https://your-app-name.railway.app`

---

### Option 3: Fly.io

1. **Install Fly CLI:**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Sign up/Login:**
   ```bash
   fly auth signup  # or fly auth login
   ```

3. **Launch your app:**
   ```bash
   fly launch
   ```

4. **Follow the prompts** - Fly.io will configure everything

**Your app will be live** at `https://your-app-name.fly.dev`

---

### Option 4: PythonAnywhere

1. **Sign up** at [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Upload files:**
   - Go to Files tab
   - Upload all your project files

3. **Create Web App:**
   - Go to Web tab
   - Click "Add a new web app"
   - Choose Flask and Python 3.11
   - Point to your `app.py`

4. **Configure WSGI:**
   - Edit the WSGI file to import your app
   - Reload web app

**Your app will be live** at `https://yourusername.pythonanywhere.com`

---

## 📝 Before Deploying

### 1. Push to GitHub (if using Git-based deployment)

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### 2. Update API Base URL

The `main.js` file now automatically detects the environment, so no changes needed! ✅

### 3. Test Locally First

```bash
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000` to test everything works.

---

## 🔧 Environment Variables (Optional)

Some platforms allow setting environment variables:

- `PORT` - Automatically set by hosting platforms
- `FLASK_ENV` - Set to `production` for production mode

---

## ⚠️ Important Notes

1. **FFmpeg Requirement:** Some hosting platforms don't have FFmpeg pre-installed. You may need to:
   - Check if the platform supports FFmpeg
   - Use a platform-specific solution
   - Consider using a Docker deployment with FFmpeg included

2. **File Storage:** Free tiers have limitations on disk space. Downloaded files are temporary and cleaned up.

3. **Rate Limits:** Free tiers often have rate limits - be aware of request limits.

4. **Sleep Mode:** Free Render.com apps sleep after 15 min inactivity (first request will be slow).

---

## 🐳 Docker Option (Advanced)

If you need FFmpeg or more control, create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT"]
```

---

## 🎯 Recommended: Render.com

**Why Render?**
- ✅ Easiest setup
- ✅ Free tier available
- ✅ Automatic deployments from GitHub
- ✅ Good documentation
- ✅ Supports Python apps well

**Steps:**
1. Push code to GitHub
2. Connect GitHub to Render
3. Select repository
4. Render auto-detects settings
5. Deploy!

---

## 📞 Need Help?

If you encounter issues:
1. Check platform logs for errors
2. Ensure all dependencies are in `requirements.txt`
3. Verify Python version matches `runtime.txt`
4. Check that `Procfile` exists and is correct

---

## 🔗 Quick Links

- [Render.com Documentation](https://render.com/docs)
- [Railway.app Documentation](https://docs.railway.app)
- [Fly.io Documentation](https://fly.io/docs)
- [PythonAnywhere Documentation](https://help.pythonanywhere.com/)

Good luck with your deployment! 🚀

