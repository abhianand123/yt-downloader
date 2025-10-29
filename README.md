# YouTube/YouTube Music Downloader - Web Edition

A beautiful web-based YouTube and YouTube Music downloader with glassmorphism design and blue theme. Features a modern, responsive frontend connected to a Flask backend API.

## Features

✅ **Beautiful Glassmorphism UI** - Modern glass design with blue theme  
✅ **YouTube Music Support** - Automatically converts YouTube Music URLs to regular YouTube URLs  
✅ **Guaranteed Audio in Videos** - Video downloads always include both video and audio tracks  
✅ **Multiple Quality Options** - Choose from various video resolutions and audio qualities  
✅ **Playlist Support** - Download entire playlists with automatic organization  
✅ **Auto-Zipping** - Automatically creates ZIP files for multiple downloads  
✅ **Format Conversion** - Converts audio to MP3 format  
✅ **Real-time Progress** - Track download progress in real-time  
✅ **Responsive Design** - Works seamlessly on desktop and mobile devices  

## Installation

### Prerequisites

1. **Python 3.7+** - [Download Python](https://www.python.org/downloads/)
2. **FFmpeg** - Required for audio extraction and format conversion

#### Installing FFmpeg

**Windows:**
- Download from [FFmpeg Official Website](https://ffmpeg.org/download.html)
- Extract to a folder (e.g., `C:\ffmpeg\`)
- Add `C:\ffmpeg\bin` to your PATH environment variable

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

### Installing Dependencies

1. Navigate to the project directory:
```bash
cd "YT DOWNLOAD"
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Starting the Server

1. Run the Flask application:
```bash
python app.py
```

2. Open your web browser and navigate to:
```
http://localhost:5000
```

### Using the Web Interface

1. **Enter URL**: Paste a YouTube or YouTube Music URL in the input field
2. **Analyze**: Click the "Analyze" button to fetch video information
3. **Configure Options**:
   - Select download type (Video or Audio Only)
   - Choose quality preference
   - Set output directory (default: Downloads)
   - For playlists, optionally enable ZIP creation
4. **Download**: Click "Start Download" to begin the download process
5. **Monitor Progress**: Watch real-time download progress in the progress card

## Supported URL Types

### Single Videos:
- `https://www.youtube.com/watch?v=VIDEO_ID`
- `https://music.youtube.com/watch?v=VIDEO_ID`

### Playlists:
- `https://www.youtube.com/playlist?list=PLAYLIST_ID`
- `https://music.youtube.com/playlist?list=PLAYLIST_ID`

## API Endpoints

The Flask backend exposes the following REST API endpoints:

- `GET /` - Serve the main frontend page
- `POST /api/video-info` - Get video/playlist information and available qualities
- `POST /api/download` - Start download process
- `GET /api/download-status/<download_id>` - Get download status
- `GET /api/download-file?file=<path>` - Download a file

## Project Structure

```
YT DOWNLOAD/
├── app.py              # Flask backend API
├── index.html          # Frontend HTML
├── requirements.txt    # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css  # Glassmorphism styles
│   └── js/
│       └── main.js    # Frontend JavaScript
└── Downloads/          # Default download directory
```

## Troubleshooting

### Common Issues

**"Error connecting to server"**
- Make sure Flask server is running (`python app.py`)
- Check that port 5000 is not being used by another application

**"No audio in video downloads"**
- Ensure FFmpeg is properly installed and in PATH
- The script uses format selection that guarantees audio inclusion

**"FFmpeg not found"**
- Reinstall FFmpeg and ensure it's in your system PATH
- Restart your terminal/command prompt after installation

**"No formats found"**
- The video might be age-restricted or region-locked
- Try a different video/playlist

**CORS Errors**
- Make sure `flask-cors` is installed: `pip install flask-cors`
- The app should handle CORS automatically, but check browser console for errors

### Browser Compatibility

- Chrome/Edge (Recommended)
- Firefox
- Safari
- Modern browsers with ES6+ support

## Legal Notice

This tool is for personal use only. Please respect:
- YouTube's Terms of Service
- Copyright laws
- Content creators' rights

Only download content you have the right to access and use.

## Development

### Running in Debug Mode

The Flask app runs in debug mode by default. For production, modify `app.py`:

```python
if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)
```

### Customizing Theme

Edit `static/css/style.css` to customize colors and styling. The theme uses CSS variables:

```css
:root {
    --primary-blue: #3b82f6;
    --glass-bg: rgba(255, 255, 255, 0.1);
    /* ... */
}
```

## License

This project is for personal use only.

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Ensure all dependencies are properly installed
3. Verify your URLs are correct
4. Check that FFmpeg is working by running `ffmpeg -version` in your terminal

