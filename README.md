# YouTube & YouTube Music Downloader

A beautiful glassmorphism web application to download YouTube videos and audio files.

## Features

- 🎬 Download YouTube videos as MP4
- 🎵 Download YouTube audio as MP3
- 🔄 Automatic YouTube Music link conversion
- 📦 Automatic ZIP creation for multiple files
- 🎨 Modern glassmorphism UI design
- 📊 Real-time download progress tracking

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg (required for audio conversion):
- Windows: Download from https://ffmpeg.org/download.html
- Add FFmpeg to your system PATH

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

3. Enter a YouTube or YouTube Music URL
4. Select your preferred format (MP3 or MP4)
5. Click Download and wait for completion
6. Click the download button to get your file(s)

## Supported Formats

- MP3: High-quality audio with embedded thumbnails and metadata
- MP4: Best quality video with audio

## Cookie Configuration (Bot Detection Bypass)

YouTube requires cookies to prevent bot detection, especially when hosted on cloud platforms. The app automatically tries to use browser cookies locally, but **you MUST configure cookies when deploying to Railway or other cloud platforms**.

### For Local Development

**Option 1: Automatic Browser Cookies**
The app automatically tries to use cookies from Chrome if available. Make sure you're logged into YouTube in your browser.

**Option 2: Manual Cookie File**
Export cookies and set the environment variable:

1. Install browser extension: ["Get cookies.txt LOCALLY"](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
2. Go to YouTube and export cookies as `cookies.txt`
3. Set environment variable:
```bash
# Windows PowerShell
$env:YOUTUBE_COOKIES_TEXT=(Get-Content cookies.txt -Raw)
python app.py

# Linux/Mac
export YOUTUBE_COOKIES_TEXT="$(cat cookies.txt)"
python app.py
```

### For Railway/Cloud Deployment (REQUIRED)

**⚠️ IMPORTANT:** Railway runs in containers without browser access. Cookies are **REQUIRED**.

1. Export cookies using "Get cookies.txt LOCALLY" browser extension
2. Copy the ENTIRE contents of `cookies.txt`
3. In Railway Dashboard → Variables → Add Variable:
   - Name: `YOUTUBE_COOKIES_TEXT`
   - Value: Paste the entire cookie file content
4. Railway will auto-redeploy

📖 **Full Railway deployment guide**: See `DEPLOYMENT_GUIDE.md`

For more information, see: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp

## Notes

- YouTube Music links are automatically converted to YouTube links
- Multiple files are automatically zipped
- Progress is tracked in real-time
- All files are temporarily stored in the `Downloads` folder

