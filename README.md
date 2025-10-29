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

YouTube may sometimes require authentication to prevent bot detection. The application automatically tries to use cookies from your Chrome browser. If you encounter authentication errors, you can:

### Option 1: Use Browser Cookies Automatically
The app will automatically try to use cookies from Chrome if available. Make sure you're logged into YouTube in your Chrome browser.

### Option 2: Export Cookies Manually
If automatic browser cookie detection doesn't work (e.g., on servers), you can export cookies manually:

1. Install a browser extension like "Get cookies.txt LOCALLY" or use yt-dlp's cookie export:
```bash
yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com"
```

2. Save the exported cookies to a file (e.g., `cookies.txt`)

3. Set the environment variable before running the app:
```bash
# Windows PowerShell
$env:YOUTUBE_COOKIES_FILE="C:\path\to\cookies.txt"
python app.py

# Windows CMD
set YOUTUBE_COOKIES_FILE=C:\path\to\cookies.txt
python app.py

# Linux/Mac
export YOUTUBE_COOKIES_FILE="/path/to/cookies.txt"
python app.py
```

For more information, see: https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp

## Notes

- YouTube Music links are automatically converted to YouTube links
- Multiple files are automatically zipped
- Progress is tracked in real-time
- All files are temporarily stored in the `Downloads` folder

