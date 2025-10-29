import os
import shutil
import zipfile
import platform
from flask import Flask, request, jsonify, send_file
from yt_dlp import YoutubeDL
from flask_cors import CORS
import threading
import time
import atexit

app = Flask(__name__)
CORS(app)

# Global variables to track download progress
download_status = {}

def cleanup_old_downloads():
    """Remove downloads older than 1 hour that are not currently downloading."""
    try:
        downloads_dir = 'Downloads'
        if not os.path.exists(downloads_dir):
            return
        
        current_time = time.time()
        for item in os.listdir(downloads_dir):
            item_path = os.path.join(downloads_dir, item)
            
            # Skip if this is an active download
            if item in download_status:
                continue
                
            try:
                # Check if it's a directory (download folder) or file (zip)
                if os.path.isdir(item_path) or item.endswith('.zip'):
                    # Get file/folder modification time
                    if os.path.isdir(item_path):
                        mod_time = os.path.getmtime(item_path)
                    else:
                        mod_time = os.path.getmtime(item_path)
                    
                    # If older than 1 hour (3600 seconds) and not being downloaded, delete it
                    if current_time - mod_time > 3600:
                        if os.path.isdir(item_path):
                            shutil.rmtree(item_path, ignore_errors=True)
                        else:
                            os.remove(item_path)
            except Exception as e:
                print(f"Error cleaning up {item}: {e}")
    except Exception as e:
        print(f"Error in cleanup: {e}")

def periodic_cleanup():
    """Periodically clean up old downloads."""
    while True:
        time.sleep(1800)  # Run every 30 minutes
        cleanup_old_downloads()

# Start cleanup thread
cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
cleanup_thread.start()

# Run initial cleanup
cleanup_old_downloads()

def convert_music_url_to_youtube(url):
    """Convert YouTube Music URLs to regular YouTube URLs."""
    if "music.youtube.com" in url:
        converted_url = url.replace("music.youtube.com", "youtube.com")
        return converted_url
    return url

def get_cookie_config():
    """Get cookie configuration for yt-dlp to bypass bot detection."""
    cookie_config = {}
    
    # First, try to use cookies file if provided via environment variable
    cookies_file = os.environ.get('YOUTUBE_COOKIES_FILE')
    if cookies_file and os.path.exists(cookies_file):
        cookie_config['cookiefile'] = cookies_file
        return cookie_config
    
    # Check if we're in a server/container environment (no GUI browsers)
    # Skip browser cookie extraction in these cases
    home_dir = os.path.expanduser('~')
    
    # Detect server/container environments
    is_server_env = (
        os.path.exists('/.dockerenv') or  # Docker container
        os.environ.get('SERVER_SOFTWARE') or  # Some hosting environments
        os.environ.get('DYNO') or  # Heroku
        home_dir.startswith('/root') or  # Running as root (common in containers)
        'CI' in os.environ  # CI/CD environments
    )
    
    if is_server_env:
        # In server environments, don't try browser cookies
        # User should provide cookies file via YOUTUBE_COOKIES_FILE env var
        return cookie_config
    
    # Try to detect available browsers and use their cookies
    # Only try browser cookies on desktop/local environments
    system = platform.system().lower()
    
    available_browsers = []
    if system == 'windows':
        # On Windows, try Chrome, Edge, Firefox
        available_browsers = ['chrome', 'edge', 'firefox', 'opera', 'brave']
    elif system == 'linux':
        # On Linux, try Chromium, Chrome, Firefox
        available_browsers = ['chromium', 'chrome', 'firefox', 'opera', 'brave']
    elif system == 'darwin':  # macOS
        # On macOS, try Chrome, Safari, Firefox
        available_browsers = ['chrome', 'safari', 'firefox', 'opera', 'brave']
    
    # Try the first browser only (to avoid too many cookie extraction attempts)
    # If it fails, yt-dlp will show an error, so we rely on error handling in the calling code
    if available_browsers:
        # Try just the first one - if it fails, the error will be caught
        cookie_config['cookiesfrombrowser'] = (available_browsers[0],)
    
    return cookie_config

def progress_hook(d, status_key):
    """Hook to track download progress."""
    if d['status'] == 'downloading':
        # Try to get progress from multiple sources
        percent = 0
        
        # Try _percent_str first
        percent_str = d.get('_percent_str', '').strip()
        if percent_str:
            try:
                percent = float(percent_str.rstrip('%'))
            except:
                pass
        
        # If no percent_str, try to calculate from downloaded/total
        if percent == 0:
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
            if total > 0:
                percent = (downloaded / total) * 100
        
        # If still no progress, set to 50% as fallback
        if percent == 0:
            percent = 50
        
        download_status[status_key] = {
            'status': 'downloading',
            'progress': percent,
            'speed': d.get('_speed_str', ''),
            'eta': d.get('eta', 0)
        }
    elif d['status'] == 'finished':
        download_status[status_key] = {'status': 'processing', 'progress': 100}

def download_media(url, format_choice, status_key, download_dir, format_id=None):
    """Download media from YouTube."""
    try:
        download_status[status_key] = {'status': 'starting', 'progress': 0}
        
        output_template = os.path.join(download_dir, "%(title)s.%(ext)s")
        
        ydl_opts = {
            'outtmpl': output_template,
            'ignoreerrors': True,
            'noplaylist': False,
            'geo_bypass': True,
            'age_limit': 0,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            },
        }
        
        # Add cookie support to bypass bot detection
        ydl_opts.update(get_cookie_config())

        # Create custom progress hook with proper threading
        def hook(d):
            progress_hook(d, status_key)
        
        ydl_opts['progress_hooks'] = [hook]

        if format_choice == "mp3":
            ydl_opts.update({
                'format': 'bestaudio/bestaudio/best',
                'writethumbnail': True,
                'postprocessors': [
                    {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'},
                    {'key': 'EmbedThumbnail'},
                    {'key': 'FFmpegMetadata'},
                ],
                'addmetadata': True,
            })
        else:  # MP4
            if format_id:
                # If specific format is selected, ensure it has video/audio and merge if needed
                # Try format_id first, but fallback to best if it fails
                ydl_opts.update({
                    'format': f'{format_id}/bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                })
            else:
                # Use best quality with wide compatibility
                ydl_opts.update({
                    'format': 'bestvideo+bestaudio/best',
                    'merge_output_format': 'mp4',
                })

        os.makedirs(download_dir, exist_ok=True)
        
        # Try download with cookies first, fallback to no cookies if cookie extraction fails
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except Exception as cookie_error:
            error_str = str(cookie_error).lower()
            # Check if error is related to cookie extraction
            if 'cookie' in error_str or 'could not find' in error_str or 'chrome' in error_str or 'firefox' in error_str:
                # Retry without cookies
                ydl_opts_no_cookies = ydl_opts.copy()
                # Remove cookie-related options
                ydl_opts_no_cookies.pop('cookiefile', None)
                ydl_opts_no_cookies.pop('cookiesfrombrowser', None)
                
                with YoutubeDL(ydl_opts_no_cookies) as ydl:
                    ydl.download([url])
            else:
                # Not a cookie error, re-raise
                raise
        
        download_status[status_key] = {'status': 'completed', 'progress': 100}
    except Exception as e:
        download_status[status_key] = {'status': 'error', 'error': str(e)}

@app.route('/')
def index():
    """Serve the main page."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Downloader</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .container {
            width: 100%;
            max-width: 600px;
        }

        .glass-card {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            border-radius: 24px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            padding: 40px;
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .header h1 {
            color: #fff;
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        }

        .subtitle {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1rem;
        }

        .form-container {
            display: flex;
            flex-direction: column;
            gap: 25px;
        }

        .input-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .input-group label {
            color: #fff;
            font-weight: 600;
            font-size: 1rem;
        }

        .input-group input[type="text"] {
            padding: 15px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.2);
            color: #fff;
            font-size: 1rem;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
        }

        .input-group input[type="text"]:focus {
            outline: none;
            border-color: rgba(255, 255, 255, 0.5);
            background: rgba(255, 255, 255, 0.25);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        .input-group input[type="text"]::placeholder {
            color: rgba(255, 255, 255, 0.6);
        }

        .format-selection {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .format-selection label {
            color: #fff;
            font-weight: 600;
            font-size: 1rem;
        }

        .radio-group {
            display: flex;
            gap: 15px;
        }

        .radio-option {
            flex: 1;
            display: flex;
            align-items: center;
            padding: 12px 20px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.15);
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .radio-option:hover {
            background: rgba(255, 255, 255, 0.25);
            transform: translateY(-2px);
        }

        .radio-option input[type="radio"] {
            margin-right: 10px;
            cursor: pointer;
        }

        .radio-option span {
            color: #fff;
            font-weight: 500;
        }

        .radio-option input[type="radio"]:checked + span {
            font-weight: 700;
            color: #fff;
        }

        .quality-select {
            width: 100%;
            padding: 15px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.2);
            color: #fff;
            font-size: 1rem;
            backdrop-filter: blur(10px);
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .quality-select:focus {
            outline: none;
            border-color: rgba(255, 255, 255, 0.5);
            background: rgba(255, 255, 255, 0.25);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        .quality-select option {
            background: #667eea;
            color: #fff;
        }

        button {
            padding: 15px 30px;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-align: center;
        }

        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #fff;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }

        .btn-success {
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            color: #fff;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }

        .btn-success:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.2);
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }

        .btn-secondary:hover {
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }

        .status-container, .download-container {
            margin-top: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .status-info {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        #statusText {
            color: #fff;
            font-weight: 500;
        }

        .progress-bar {
            width: 100%;
            height: 12px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            overflow: hidden;
            position: relative;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            width: 0%;
            transition: width 0.3s ease;
            border-radius: 10px;
        }

        .success-message {
            text-align: center;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .success-message p {
            color: #38ef7d;
            font-size: 1.2rem;
            font-weight: 600;
        }

        .hidden {
            display: none;
        }

        @media (max-width: 768px) {
            .glass-card {
                padding: 30px 20px;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .radio-group {
                flex-direction: column;
            }
        }

        @keyframes pulse {
            0%, 100% {
                opacity: 1;
            }
            50% {
                opacity: 0.5;
            }
        }

        .loading {
            animation: pulse 2s ease-in-out infinite;
        }

        .developer-section, .about-section {
            margin-top: 30px;
            width: 100%;
            max-width: 600px;
        }

        .dev-card, .about-card {
            background: rgba(255, 255, 255, 0.12);
            backdrop-filter: blur(15px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.25);
            padding: 25px;
            box-shadow: 0 6px 24px rgba(0, 0, 0, 0.15);
        }

        .dev-header, .about-header {
            margin-bottom: 15px;
        }

        .dev-header h3, .about-header h3 {
            color: #fff;
            font-size: 1.3rem;
            margin: 0;
            text-align: center;
        }

        .dev-content {
            text-align: center;
        }

        .dev-name {
            color: #fff;
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 10px;
        }

        .dev-link {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            color: #fff;
            text-decoration: none;
            font-size: 1.1rem;
            padding: 12px 24px;
            background: linear-gradient(135deg, #E4405F 0%, #F56040 100%);
            border-radius: 12px;
            transition: all 0.3s ease;
        }

        .dev-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(229, 64, 95, 0.4);
        }

        .instagram-icon {
            width: 24px;
            height: 24px;
            display: inline-block;
            vertical-align: middle;
        }

        .about-content {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .about-item {
            color: #fff;
        }

        .about-item strong {
            display: block;
            margin-bottom: 8px;
            font-size: 1.1rem;
            color: #fff;
        }

        .about-item p {
            margin: 0;
            line-height: 1.6;
            color: rgba(255, 255, 255, 0.9);
        }

        .about-item ul {
            margin: 0;
            padding-left: 20px;
            list-style: none;
        }

        .about-item ul li {
            margin-bottom: 8px;
            line-height: 1.6;
            color: rgba(255, 255, 255, 0.9);
        }

        .warning-notice {
            background: rgba(255, 152, 0, 0.2);
            border: 1px solid rgba(255, 152, 0, 0.4);
            border-radius: 12px;
            padding: 15px;
            margin-top: 15px;
        }

        .warning-notice strong {
            display: block;
            color: #ff9800;
            margin-bottom: 8px;
            font-size: 1rem;
        }

        .warning-notice p {
            margin: 0;
            color: #fff;
            line-height: 1.6;
            font-size: 0.95rem;
        }

        .warning-notice p + p {
            margin-top: 12px;
        }

        .warning-notice p strong {
            color: #ff9800;
        }

        .top-warning-notice {
            background: rgba(33, 150, 243, 0.2);
            border: 1px solid rgba(33, 150, 243, 0.4);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 20px;
        }

        .top-warning-notice strong {
            display: block;
            color: #2196f3;
            margin-bottom: 8px;
            font-size: 1rem;
        }

        .top-warning-notice p {
            margin: 0;
            color: #fff;
            line-height: 1.6;
            font-size: 0.95rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="glass-card">
            <div class="header">
                <h1>🎬 YouTube Downloader</h1>
                <p class="subtitle">Download videos and audio from YouTube & YouTube Music</p>
            </div>
            
            <div class="form-container">
                <div class="top-warning-notice">
                    <strong>⚠️ Important:</strong>
                    <p>Always click "Fetch Available Formats" after entering a new link to get the best quality options!</p>
                </div>
                
                <div class="input-group">
                    <label for="url">🔗 URL</label>
                    <input type="text" id="url" placeholder="https://youtube.com/... or https://music.youtube.com/..." />
                </div>
                
                <button id="fetchBtn" class="btn-primary">
                    <span>🔍 Fetch Available Formats</span>
                </button>
                
                <div id="qualitySelector" class="format-selection hidden">
                    <label>🎥 Select Quality</label>
                    <select id="qualitySelect" class="quality-select">
                    </select>
                </div>
                
                <div class="format-selection">
                    <label>📥 Format</label>
                    <div class="radio-group">
                        <label class="radio-option">
                            <input type="radio" name="format" value="mp3" />
                            <span>🎵 MP3 (Audio)</span>
                        </label>
                        <label class="radio-option">
                            <input type="radio" name="format" value="mp4" checked />
                            <span>🎬 MP4 (Video)</span>
                        </label>
                    </div>
                </div>
                
                <button id="downloadBtn" class="btn-primary hidden">
                    <span>⬇️ Download</span>
                </button>
            </div>
            
            <div id="statusContainer" class="status-container hidden">
                <div class="status-info">
                    <p id="statusText">Preparing download...</p>
                    <div class="progress-bar">
                        <div id="progressFill" class="progress-fill"></div>
                    </div>
                    <button id="cancelBtn" class="btn-secondary">Cancel</button>
                </div>
            </div>
            
            <div id="downloadContainer" class="download-container hidden">
                <div class="success-message">
                    <p>✅ Download Complete!</p>
                    <button id="downloadFileBtn" class="btn-success">📥 Download File</button>
                    <button id="newDownloadBtn" class="btn-secondary">New Download</button>
                </div>
            </div>
        </div>
        
        <!-- Developer Info -->
        <div class="developer-section">
            <div class="dev-card">
                <div class="dev-header">
                    <h3>🌟 Developed by</h3>
                </div>
                <div class="dev-content">
                    <p class="dev-name">Abhi Anand</p>
                    <a href="https://www.instagram.com/chessbasebgs" target="_blank" class="dev-link">
                        <svg class="instagram-icon" viewBox="0 0 24 24" width="24" height="24">
                            <path fill="currentColor" d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.071 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                        </svg>
                        @chessbasebgs
                    </a>
                </div>
            </div>
        </div>
        
        <!-- About Section -->
        <div class="about-section">
            <div class="about-card">
                <div class="about-header">
                    <h3>🎬 YTDownloader Pro</h3>
                </div>
                <div class="about-content">
                    <div class="about-item">
                        <strong>📥 What it does:</strong>
                        <p>Download high-quality YouTube videos and audio files with ease. Supports both YouTube and YouTube Music links (including playlists!), with automatic quality selection and automatic playlist handling.</p>
                    </div>
                    <div class="about-item">
                        <strong>✨ Features:</strong>
                        <ul>
                            <li>🎬 Download videos in multiple quality options (144p to 4K)</li>
                            <li>🎵 Extract MP3 audio with embedded metadata</li>
                            <li>📋 Download entire playlists (YouTube & YouTube Music)</li>
                            <li>📦 Automatic ZIP creation for multiple files</li>
                            <li>🔄 YouTube Music link conversion</li>
                            <li>⚡ Real-time progress tracking</li>
                        </ul>
                    </div>
                    <div class="warning-notice">
                        <strong>⚠️ Important Notices:</strong>
                        <p>1. Sometimes files may not download correctly if you select an audio format from the quality fetcher but choose "Video (MP4)" in the download options. Make sure to match the selected format with the download type (Audio/Video) for best results.</p>
                        <p>2. <strong>Download files immediately after generation!</strong> Files are only available for 5 minutes and will be automatically deleted from the server after that time.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let statusKey = null;
        let statusCheckInterval = null;
        let videoFormats = [];
        let selectedFormatId = null;

        // DOM Elements
        const urlInput = document.getElementById('url');
        const fetchBtn = document.getElementById('fetchBtn');
        const downloadBtn = document.getElementById('downloadBtn');
        const cancelBtn = document.getElementById('cancelBtn');
        const statusContainer = document.getElementById('statusContainer');
        const downloadContainer = document.getElementById('downloadContainer');
        const statusText = document.getElementById('statusText');
        const progressFill = document.getElementById('progressFill');
        const downloadFileBtn = document.getElementById('downloadFileBtn');
        const newDownloadBtn = document.getElementById('newDownloadBtn');
        const qualitySelector = document.getElementById('qualitySelector');
        const qualitySelect = document.getElementById('qualitySelect');

        // Event Listeners
        fetchBtn.addEventListener('click', fetchFormats);
        downloadBtn.addEventListener('click', startDownload);
        cancelBtn.addEventListener('click', cancelDownload);
        downloadFileBtn.addEventListener('click', downloadFile);
        newDownloadBtn.addEventListener('click', resetForm);
        qualitySelect.addEventListener('change', (e) => {
            selectedFormatId = e.target.value;
            
            // Auto-switch format based on selected quality
            const selectedFormat = videoFormats.find(f => f.format_id === selectedFormatId);
            if (selectedFormat) {
                // If audio only format selected, switch to MP3
                if (selectedFormat.vcodec === 'none' && selectedFormat.acodec !== 'none') {
                    document.querySelector('input[name="format"][value="mp3"]').checked = true;
                }
                // If video format selected, switch to MP4
                else if (selectedFormat.vcodec !== 'none') {
                    document.querySelector('input[name="format"][value="mp4"]').checked = true;
                }
            }
        });

        function fetchFormats() {
            const url = urlInput.value.trim();
            
            if (!url) {
                alert('Please enter a YouTube URL');
                return;
            }
            
            fetchBtn.disabled = true;
            fetchBtn.textContent = 'Loading...';
            
            fetch('/api/info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    fetchBtn.disabled = false;
                    fetchBtn.textContent = '🔍 Fetch Available Formats';
                    return;
                }
                
                videoFormats = data.formats;
                
                // Populate quality selector
                qualitySelect.innerHTML = '<option value="">Best available</option>';
                videoFormats.forEach(format => {
                    const option = document.createElement('option');
                    option.value = format.format_id;
                    option.textContent = `${format.quality} (${format.ext.toUpperCase()})`;
                    qualitySelect.appendChild(option);
                });
                
                // Show quality selector and download button
                qualitySelector.classList.remove('hidden');
                downloadBtn.classList.remove('hidden');
                fetchBtn.disabled = false;
                fetchBtn.textContent = '🔍 Fetch Available Formats';
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
                fetchBtn.disabled = false;
                fetchBtn.textContent = '🔍 Fetch Available Formats';
            });
        }

        function startDownload() {
            const url = urlInput.value.trim();
            const format = document.querySelector('input[name="format"]:checked').value;
            
            if (!url) {
                alert('Please enter a YouTube URL');
                return;
            }
            
            // Show status container
            statusContainer.classList.remove('hidden');
            downloadContainer.classList.add('hidden');
            
            // Update button state
            downloadBtn.disabled = true;
            downloadBtn.classList.add('loading');
            
            // Start download
            fetch('/api/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url, format, format_id: selectedFormatId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                    resetForm();
                    return;
                }
                
                statusKey = data.status_key;
                checkStatus();
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
                resetForm();
            });
        }

        function checkStatus() {
            if (!statusKey) return;
            
            statusCheckInterval = setInterval(() => {
                fetch(`/api/status/${statusKey}`)
                    .then(response => response.json())
                    .then(data => {
                        updateStatus(data);
                        
                        if (data.status === 'completed') {
                            clearInterval(statusCheckInterval);
                            downloadComplete();
                        } else if (data.status === 'error') {
                            clearInterval(statusCheckInterval);
                            alert('Download failed: ' + data.error);
                            resetForm();
                        }
                    })
                    .catch(error => {
                        console.error('Error checking status:', error);
                    });
            }, 1000);
        }

        function updateStatus(status) {
            const statusMessages = {
                'starting': 'Starting download...',
                'downloading': `Downloading... ${status.progress || 0}%`,
                'processing': 'Processing...',
                'completed': 'Download complete!',
                'error': 'Error occurred'
            };
            
            statusText.textContent = statusMessages[status.status] || 'Unknown status';
            progressFill.style.width = `${status.progress || 0}%`;
        }

        function downloadComplete() {
            statusContainer.classList.add('hidden');
            downloadContainer.classList.remove('hidden');
            downloadBtn.disabled = false;
            downloadBtn.classList.remove('loading');
        }

        function downloadFile() {
            if (!statusKey) return;
            
            // Open download link in new tab
            window.location.href = `/api/download_file/${statusKey}`;
        }

        function cancelDownload() {
            clearInterval(statusCheckInterval);
            
            if (statusKey) {
                // Optional: Send cancel request to server
                fetch(`/api/cleanup/${statusKey}`, { method: 'POST' });
            }
            
            resetForm();
        }

        function resetForm() {
            clearInterval(statusCheckInterval);
            statusKey = null;
            statusContainer.classList.add('hidden');
            downloadContainer.classList.add('hidden');
            downloadBtn.disabled = false;
            downloadBtn.classList.remove('loading');
            urlInput.value = '';
            statusText.textContent = 'Preparing download...';
            progressFill.style.width = '0%';
        }
    </script>
</body>
</html>
    """


@app.route('/api/info', methods=['POST'])
def get_video_info():
    """Get video info and available formats."""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Convert YT Music URL if needed
    url = convert_music_url_to_youtube(url)
    
    try:
        # Cookie support configuration
        cookie_config = get_cookie_config()
        
        # First check if it's a playlist (use flat extraction for speed)
        ydl_opts_flat = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            },
            **cookie_config
        }
        
        # Try with cookies first, fallback to no cookies if cookie extraction fails
        try:
            with YoutubeDL(ydl_opts_flat) as ydl_flat:
                quick_info = ydl_flat.extract_info(url, download=False)
        except Exception as cookie_error:
            error_str = str(cookie_error).lower()
            # Check if error is related to cookie extraction
            if 'cookie' in error_str or 'could not find' in error_str or 'chrome' in error_str or 'firefox' in error_str:
                # Retry without cookies
                cookie_config = {}
                ydl_opts_flat = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                    'extractor_args': {
                        'youtube': {
                            'player_client': ['android', 'web']
                        }
                    }
                }
                with YoutubeDL(ydl_opts_flat) as ydl_flat:
                    quick_info = ydl_flat.extract_info(url, download=False)
            else:
                # Not a cookie error, re-raise
                raise
        
        # Check if it's a playlist
        if quick_info.get('_type') == 'playlist':
            # For playlists, get formats from first video only (much faster)
            entries = quick_info.get('entries', [])
            if entries and len(entries) > 0:
                first_video_id = entries[0].get('id')
                if first_video_id:
                    first_url = f"https://www.youtube.com/watch?v={first_video_id}"
                    # Extract detailed info only for first video
                    ydl_opts = {
                        'quiet': True,
                        'no_warnings': True,
                        'extractor_args': {
                            'youtube': {
                                'player_client': ['android', 'web']
                            }
                        },
                        **cookie_config
                    }
                    with YoutubeDL(ydl_opts) as ydl:
                        try:
                            first_info = ydl.extract_info(first_url, download=False)
                            formats_source = first_info.get('formats', [])
                        except Exception as e:
                            error_str = str(e).lower()
                            # Check if error is related to cookie extraction
                            if 'cookie' in error_str or 'could not find' in error_str or 'chrome' in error_str or 'firefox' in error_str:
                                # Retry without cookies
                                ydl_opts_no_cookies = {
                                    'quiet': True,
                                    'no_warnings': True,
                                    'extractor_args': {
                                        'youtube': {
                                            'player_client': ['android', 'web']
                                        }
                                    }
                                }
                                with YoutubeDL(ydl_opts_no_cookies) as ydl_retry:
                                    try:
                                        first_info = ydl_retry.extract_info(first_url, download=False)
                                        formats_source = first_info.get('formats', [])
                                    except Exception as retry_error:
                                        # If retry also fails, return empty formats
                                        formats_source = []
                                        print(f"Error extracting first video info: {retry_error}")
                            else:
                                # If first video fails for other reasons, return empty formats
                                formats_source = []
                                print(f"Error extracting first video info: {e}")
                else:
                    formats_source = []
            else:
                formats_source = []
            info = quick_info  # Use quick_info for playlist title/thumbnail
        else:
            # Single video - extract all formats normally
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web']
                    }
                },
                **cookie_config
            }
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    formats_source = info.get('formats', [])
            except Exception as cookie_error:
                error_str = str(cookie_error).lower()
                # Check if error is related to cookie extraction
                if 'cookie' in error_str or 'could not find' in error_str or 'chrome' in error_str or 'firefox' in error_str:
                    # Retry without cookies
                    ydl_opts_no_cookies = {
                        'quiet': True,
                        'no_warnings': True,
                        'extractor_args': {
                            'youtube': {
                                'player_client': ['android', 'web']
                            }
                        }
                    }
                    with YoutubeDL(ydl_opts_no_cookies) as ydl:
                        info = ydl.extract_info(url, download=False)
                        formats_source = info.get('formats', [])
                else:
                    # Not a cookie error, re-raise
                    raise
        
        # Process formats (same for both playlist and single video)
        formats = []
        for f in formats_source:
            vcodec = f.get('vcodec', '')
            acodec = f.get('acodec', '')
            ext = f.get('ext', 'unknown')
            
            # Skip thumbnail/image-only formats
            if ext.lower() in ['webp', 'jpg', 'jpeg', 'png'] and vcodec == 'none' and acodec == 'none':
                continue
            
            if vcodec != 'none' or acodec != 'none':
                height = f.get('height')
                format_id = f.get('format_id')
                filesize = f.get('filesize', 0)
                
                # Skip video-only formats (video without audio)
                if vcodec != 'none' and acodec == 'none':
                    continue
                
                quality_label = ''
                if height:
                    quality_label = f"{height}p"
                elif vcodec == 'none' and acodec != 'none':
                    quality_label = "Audio only"
                else:
                    quality_label = "Unknown"
                
                formats.append({
                    'format_id': format_id,
                    'quality': quality_label,
                    'ext': ext,
                    'vcodec': vcodec,
                    'acodec': acodec,
                    'filesize': filesize
                })
        
        # Determine if it's a playlist
        is_playlist = quick_info.get('_type') == 'playlist'
        playlist_count = len(quick_info.get('entries', [])) if is_playlist else 1
        
        return jsonify({
            'title': info.get('title', 'Unknown'),
            'thumbnail': info.get('thumbnail', ''),
            'formats': formats,
            'is_playlist': is_playlist,
            'playlist_count': playlist_count
        })
    except Exception as e:
        error_msg = str(e)
        if 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
            return jsonify({'error': 'Request timed out. The playlist may be too large. Please try downloading directly without fetching formats.'}), 408
        return jsonify({'error': f'Error fetching video info: {error_msg}'}), 400

@app.route('/api/download', methods=['POST'])
def download():
    """Handle download request."""
    data = request.json
    url = data.get('url')
    format_id = data.get('format_id')
    format_choice = data.get('format', 'mp4')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Convert YT Music URL if needed
    url = convert_music_url_to_youtube(url)
    
    status_key = os.urandom(8).hex()
    download_dir = os.path.join('Downloads', status_key)
    
    # Start download in background thread
    thread = threading.Thread(target=download_media, args=(url, format_choice, status_key, download_dir, format_id))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status_key': status_key})

@app.route('/api/status/<status_key>')
def get_status(status_key):
    """Get download status."""
    status = download_status.get(status_key, {'status': 'unknown'})
    return jsonify(status)

@app.route('/api/download_file/<status_key>')
def download_file(status_key):
    """Download the file."""
    download_dir = os.path.join('Downloads', status_key)
    
    if not os.path.exists(download_dir):
        return jsonify({'error': 'Download not found'}), 404
    
    files = os.listdir(download_dir)
    
    if not files:
        return jsonify({'error': 'No files found'}), 404
    
    # Store paths for cleanup
    temp_paths = []
    
    try:
        # If multiple files, create zip
        if len(files) > 1:
            zip_path = os.path.join('Downloads', f'{status_key}.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in files:
                    file_path = os.path.join(download_dir, file)
                    zipf.write(file_path, file)
            
            temp_paths.append(zip_path)
            temp_paths.append(download_dir)
            
            return send_file(zip_path, as_attachment=True, download_name=f'yt_download_{status_key}.zip')
        else:
            # Single file
            file_path = os.path.join(download_dir, files[0])
            temp_paths.append(file_path)
            temp_paths.append(download_dir)
            
            return send_file(file_path, as_attachment=True)
    finally:
        # Schedule cleanup after 300 seconds (5 minutes)
        # But only if download is complete
        def delayed_cleanup():
            time.sleep(300)
            # Check if download is still in progress
            current_status = download_status.get(status_key, {})
            if current_status.get('status') not in ['downloading', 'starting', 'processing']:
                # Download is complete or failed, safe to cleanup
                for path in temp_paths:
                    try:
                        if os.path.isdir(path):
                            shutil.rmtree(path, ignore_errors=True)
                        elif os.path.exists(path):
                            os.remove(path)
                    except:
                        pass
        
        cleanup_thread = threading.Thread(target=delayed_cleanup, daemon=True)
        cleanup_thread.start()

@app.route('/api/cleanup/<status_key>', methods=['POST'])
def cleanup(status_key):
    """Clean up downloaded files."""
    download_dir = os.path.join('Downloads', status_key)
    zip_path = os.path.join('Downloads', f'{status_key}.zip')
    
    if os.path.exists(download_dir):
        shutil.rmtree(download_dir)
    if os.path.exists(zip_path):
        os.remove(zip_path)
    
    download_status.pop(status_key, None)
    
    return jsonify({'success': True})

if __name__ == '__main__':
    os.makedirs('Downloads', exist_ok=True)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)


