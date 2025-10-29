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

## Notes

- YouTube Music links are automatically converted to YouTube links
- Multiple files are automatically zipped
- Progress is tracked in real-time
- All files are temporarily stored in the `Downloads` folder

