#!/usr/bin/env python3
"""
YouTube/YouTube Music Downloader Flask API with playlist support and zipping functionality
"""

import os
import re
import json
import zipfile
import tempfile
import threading
import uuid
import time
import glob
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import yt_dlp
from typing import List, Optional, Dict

app = Flask(__name__, template_folder='.', static_folder='static', static_url_path='/static')
CORS(app)

# Store download progress
download_progress = {}

class YouTubeDownloader:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        self.downloaded_files = []
        
    def convert_yt_music_to_yt(self, url: str) -> str:
        """Convert YouTube Music URL to regular YouTube URL"""
        if 'music.youtube.com' in url:
            converted_url = url.replace('music.youtube.com', 'youtube.com')
            return converted_url
        return url
    
    def extract_playlist_info(self, url: str) -> Dict:
        """Extract playlist information from URL"""
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        playlist_id = query_params.get('list', [None])[0]
        return {
            'is_playlist': 'list=' in url,
            'playlist_id': playlist_id,
            'url': url
        }
    
    def get_available_qualities(self, url: str, audio_only: bool = False) -> Dict:
        """Get all available qualities for a YouTube video with proper format info"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                
                # Filter formats based on audio_only preference
                filtered_formats = []
                
                for fmt in formats:
                    resolution = self._get_format_resolution(fmt)
                    
                    format_info = {
                        'format_id': fmt.get('format_id'),
                        'ext': fmt.get('ext', 'unknown'),
                        'resolution': resolution,
                        'filesize': fmt.get('filesize'),
                        'vcodec': fmt.get('vcodec', 'none'),
                        'acodec': fmt.get('acodec', 'none'),
                        'format_note': fmt.get('format_note', ''),
                        'height': fmt.get('height'),
                        'width': fmt.get('width'),
                        'has_audio': fmt.get('acodec') != 'none',
                        'has_video': fmt.get('vcodec') != 'none',
                    }
                    
                    if audio_only:
                        if format_info['has_audio'] and not format_info['has_video']:
                            filtered_formats.append(format_info)
                    else:
                        if format_info['has_video'] and format_info['has_audio']:
                            filtered_formats.append(format_info)
                
                # Sort based on type
                if audio_only:
                    filtered_formats.sort(key=lambda x: x.get('filesize', 0) or 0, reverse=True)
                else:
                    filtered_formats.sort(key=lambda x: self._get_resolution_value(x['resolution']), reverse=True)
                
                return {
                    'qualities': filtered_formats,
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'thumbnail': info.get('thumbnail', ''),
                }
                
            except Exception as e:
                print(f"Error getting available qualities: {e}")
                return None
    
    def _get_format_resolution(self, fmt: Dict) -> str:
        """Extract resolution information from format dict"""
        if fmt.get('format_note') and fmt['format_note'] != 'none':
            return fmt['format_note']
        elif fmt.get('height'):
            height = fmt['height']
            return f"{height}p"
        elif fmt.get('quality'):
            return f"{fmt['quality']}"
        else:
            return 'Unknown'
    
    def _get_resolution_value(self, resolution: str) -> int:
        """Convert resolution string to numeric value for sorting"""
        if resolution == 'Unknown' or not resolution:
            return 0
        
        numbers = re.findall(r'\d+', resolution)
        if numbers:
            return int(numbers[-1])
        return 0
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to readable format"""
        if not seconds:
            return "N/A"
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in bytes to human readable format"""
        if not size_bytes:
            return "Unknown"
        
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    
    def download_video(self, url: str, format_id: str = None, audio_only: bool = False, 
                      output_dir: str = None, progress_callback=None) -> Dict:
        """Download a single video with proper merging"""
        url = self.convert_yt_music_to_yt(url)
        
        # Use temp directory if not specified (for browser downloads)
        if output_dir is None:
            output_dir = self.temp_dir
        Path(output_dir).mkdir(exist_ok=True)
        
        if audio_only:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [progress_callback] if progress_callback else [],
            }
        else:
            if format_id:
                ydl_opts = {
                    'format': format_id,
                    'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                    'progress_hooks': [progress_callback] if progress_callback else [],
                }
            else:
                ydl_opts = {
                    'format': 'bestvideo+bestaudio/best',
                    'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }],
                    'progress_hooks': [progress_callback] if progress_callback else [],
                }
        
        try:
            # Get list of files before download
            files_before = set()
            if os.path.exists(output_dir):
                files_before = set(os.listdir(output_dir))
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Find the actual downloaded file
                filename = None
                if os.path.exists(output_dir):
                    files_after = set(os.listdir(output_dir))
                    new_files = files_after - files_before
                    
                    if new_files:
                        # Get the most recently modified file
                        file_paths = [os.path.join(output_dir, f) for f in new_files if os.path.isfile(os.path.join(output_dir, f))]
                        if file_paths:
                            filename = max(file_paths, key=os.path.getmtime)
                
                # Fallback: try to get from info
                if not filename:
                    try:
                        prepared_filename = ydl.prepare_filename(info)
                        base_name = os.path.splitext(prepared_filename)[0]
                        for ext in ['.mp3', '.mp4', '.webm', '.m4a', '.mkv']:
                            possible_file = base_name + ext
                            if os.path.exists(possible_file):
                                filename = possible_file
                                break
                    except:
                        pass
                
                if filename and os.path.exists(filename):
                    self.downloaded_files.append(filename)
                    return {
                        'success': True,
                        'filename': filename,
                        'basename': os.path.basename(filename)
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Downloaded file not found'
                    }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_playlist(self, url: str, format_id: str = None, audio_only: bool = False,
                         output_dir: str = None, progress_callback=None) -> Dict:
        """Download entire playlist with proper merging"""
        url = self.convert_yt_music_to_yt(url)
        playlist_info = self.extract_playlist_info(url)
        
        if not playlist_info['is_playlist']:
            return {
                'success': False,
                'error': 'Provided URL is not a playlist'
            }
        
        # Use temp directory if not specified (for browser downloads)
        if output_dir is None:
            output_dir = self.temp_dir
        playlist_dir = os.path.join(output_dir, f"playlist_{playlist_info['playlist_id']}")
        
        if audio_only:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(playlist_dir, '%(playlist_title)s - %(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'progress_hooks': [progress_callback] if progress_callback else [],
            }
        else:
            if format_id:
                ydl_opts = {
                    'format': format_id,
                    'outtmpl': os.path.join(playlist_dir, '%(playlist_title)s - %(title)s.%(ext)s'),
                    'progress_hooks': [progress_callback] if progress_callback else [],
                }
            else:
                ydl_opts = {
                    'format': 'bestvideo+bestaudio/best',
                    'outtmpl': os.path.join(playlist_dir, '%(playlist_title)s - %(title)s.%(ext)s'),
                    'postprocessors': [{
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }],
                    'progress_hooks': [progress_callback] if progress_callback else [],
                }
        
        try:
            # Ensure playlist directory exists
            Path(playlist_dir).mkdir(exist_ok=True, parents=True)
            
            # Get list of files before download
            files_before = set()
            if os.path.exists(playlist_dir):
                files_before = set(os.listdir(playlist_dir))
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Get list of files after download
                files_after = set()
                downloaded_files = []
                if os.path.exists(playlist_dir):
                    # Wait a bit for filesystem to catch up
                    time.sleep(0.3)
                    files_after = set(os.listdir(playlist_dir))
                    new_files = files_after - files_before
                    
                    # Sort by modification time to get actual downloaded files
                    file_paths = []
                    for filename in new_files:
                        file_path = os.path.join(playlist_dir, filename)
                        if os.path.isfile(file_path) and not filename.endswith('.part'):
                            file_paths.append(file_path)
                    
                    # Sort by modification time (newest first)
                    file_paths.sort(key=os.path.getmtime, reverse=True)
                    downloaded_files = file_paths
                
                # Fallback: if we couldn't find files by diff, try to get from entries
                if not downloaded_files and info.get('entries'):
                    for entry in info['entries']:
                        if entry:
                            try:
                                filename = ydl.prepare_filename(entry)
                                # Check for actual file (handle MP3 conversion)
                                base_name = os.path.splitext(filename)[0]
                                for ext in ['.mp3', '.mp4', '.webm', '.m4a', '.mkv', '.m4v']:
                                    possible_file = base_name + ext
                                    if os.path.exists(possible_file) and os.path.isfile(possible_file):
                                        downloaded_files.append(possible_file)
                                        break
                                # Also try without extension changes
                                if os.path.exists(filename) and os.path.isfile(filename):
                                    if filename not in downloaded_files:
                                        downloaded_files.append(filename)
                            except Exception as e:
                                print(f"Error processing entry: {e}")
                                continue
                
                # If still no files, scan the directory for media files
                if not downloaded_files and os.path.exists(playlist_dir):
                    for pattern in ['*.mp3', '*.mp4', '*.webm', '*.m4a', '*.mkv']:
                        found = glob.glob(os.path.join(playlist_dir, pattern))
                        for f in found:
                            if f not in downloaded_files:
                                downloaded_files.append(f)
                
                return {
                    'success': True,
                    'files': downloaded_files,
                    'count': len(downloaded_files),
                    'playlist_dir': playlist_dir
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_zip_fast(self, files: List[str], zip_filename: str = "downloads.zip") -> str:
        """Create a zip file quickly without progress updates"""
        if not files or len(files) == 0:
            return None
        
        # Filter to only existing files
        existing_files = [f for f in files if os.path.exists(f) and os.path.isfile(f)]
        
        if len(existing_files) == 0:
            print("No existing files to zip")
            return None
        
        try:
            # Ensure zip filename has .zip extension
            if not zip_filename.endswith('.zip'):
                zip_filename += '.zip'
            
            # Remove existing zip file if it exists
            if os.path.exists(zip_filename):
                try:
                    os.remove(zip_filename)
                except:
                    pass
            
            # Use ZIP_STORED (no compression) for maximum speed
            print(f"Creating ZIP file: {zip_filename} with {len(existing_files)} files")
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_STORED) as zipf:
                for idx, file in enumerate(existing_files, 1):
                    try:
                        if not os.path.exists(file):
                            print(f"File {idx} does not exist: {file}")
                            continue
                        filename_only = os.path.basename(file)
                        print(f"Adding file {idx}/{len(existing_files)}: {filename_only}")
                        zipf.write(file, filename_only)
                    except Exception as e:
                        print(f"Warning: Could not add {file} to zip: {e}")
                        continue
            
            # Verify zip file was created
            if os.path.exists(zip_filename) and os.path.getsize(zip_filename) > 0:
                print(f"ZIP file created successfully: {zip_filename} ({os.path.getsize(zip_filename)} bytes)")
                return zip_filename
            else:
                print(f"ZIP file creation failed or file is empty: {zip_filename}")
                return None
                
        except Exception as e:
            print(f"Error creating zip file: {e}")
            # Clean up partial zip if it exists
            if os.path.exists(zip_filename):
                try:
                    os.remove(zip_filename)
                except:
                    pass
            return None
    
    def cleanup(self):
        """Clean up temporary files"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

# Global downloader instance
downloader = YouTubeDownloader()

@app.route('/')
def index():
    """Serve the main frontend page"""
    return render_template('index.html')

@app.route('/style.css')
def serve_css():
    """Serve CSS file from root"""
    return send_file('style.css', mimetype='text/css')

@app.route('/main.js')
def serve_js():
    """Serve JavaScript file from root"""
    return send_file('main.js', mimetype='application/javascript')

@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    """Get video/playlist information and available qualities"""
    try:
        data = request.json
        url = data.get('url')
        audio_only = data.get('audio_only', False)
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        converted_url = downloader.convert_yt_music_to_yt(url)
        playlist_info = downloader.extract_playlist_info(converted_url)
        qualities = downloader.get_available_qualities(converted_url, audio_only)
        
        if not qualities:
            return jsonify({'success': False, 'error': 'Failed to fetch video information'}), 400
        
        # Format qualities for frontend
        formatted_qualities = []
        for i, fmt in enumerate(qualities['qualities'], 1):
            formatted_qualities.append({
                'id': i,
                'format_id': fmt['format_id'],
                'label': 'Best' if i == 1 else ('High' if i == 2 else 'Medium') if audio_only else fmt['resolution'],
                'resolution': fmt['resolution'],
                'size': downloader._format_size(fmt['filesize']) if fmt['filesize'] else 'Unknown',
                'ext': fmt['ext'].upper()
            })
        
        response = {
            'success': True,
            'title': qualities['title'],
            'duration': downloader._format_duration(qualities['duration']),
            'thumbnail': qualities.get('thumbnail', ''),
            'is_playlist': playlist_info['is_playlist'],
            'playlist_id': playlist_info['playlist_id'],
            'qualities': formatted_qualities
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def download():
    """Start download process"""
    try:
        data = request.json
        url = data.get('url')
        format_id = data.get('format_id')
        audio_only = data.get('audio_only', False)
        # Use temp directory for browser downloads instead of saving to server
        output_dir = downloader.temp_dir
        create_zip = data.get('create_zip', False)
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        converted_url = downloader.convert_yt_music_to_yt(url)
        playlist_info = downloader.extract_playlist_info(converted_url)
        
        # Use selected format_id or None for auto
        selected_format_id = None
        if format_id and format_id != 'auto':
            # Get the format_id from the qualities list
            qualities = downloader.get_available_qualities(converted_url, audio_only)
            try:
                format_id_int = int(format_id)
                if qualities and len(qualities['qualities']) >= format_id_int:
                    selected_format_id = qualities['qualities'][format_id_int - 1]['format_id']
            except (ValueError, IndexError):
                # If format_id is invalid, fall back to auto
                selected_format_id = None
        
        # Generate unique download ID
        download_id = str(uuid.uuid4())
        
        # Initialize progress
        download_progress[download_id] = {
            'status': 'downloading',
            'progress': 0,
            'current_file': '',
            'message': 'Starting download...'
        }
        
        # Progress callback for yt-dlp
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    progress = min(int((downloaded / total) * 90), 90)  # Cap at 90% during download
                    download_progress[download_id]['progress'] = progress
                    download_progress[download_id]['message'] = f"Downloading: {downloader._format_size(downloaded)} / {downloader._format_size(total)}"
                else:
                    download_progress[download_id]['message'] = 'Downloading...'
            elif d['status'] == 'finished':
                download_progress[download_id]['progress'] = 90
                download_progress[download_id]['message'] = 'Download complete, finalizing...'
        
        # Run download in background thread
        def download_thread():
            try:
                if playlist_info['is_playlist']:
                    result = downloader.download_playlist(
                        url, 
                        selected_format_id,
                        audio_only,
                        output_dir,
                        progress_hook
                    )
                    
                    if result['success']:
                        # Update progress immediately after download
                        download_progress[download_id]['progress'] = 95
                        download_progress[download_id]['message'] = f"Downloaded {result['count']} files"
                        
                        # Create ZIP if requested
                        if create_zip:
                            zip_filename = f"playlist_{playlist_info['playlist_id']}.zip"
                            zip_path = os.path.join(output_dir, zip_filename)
                            download_progress[download_id]['message'] = f'Creating ZIP file...'
                            download_progress[download_id]['progress'] = 96
                            
                            # Create zip without progress updates (much faster)
                            zip_result = downloader.create_zip_fast(result['files'], zip_path)
                            
                            if zip_result and os.path.exists(zip_result):
                                # Store relative path for serving
                                download_progress[download_id].update({
                                    'status': 'completed',
                                    'progress': 100,
                                    'message': f"✅ Successfully downloaded {result['count']} files and created ZIP",
                                    'download_file': zip_result,
                                    'download_filename': zip_filename,
                                    'file_count': len(result['files'])
                                })
                            else:
                                download_progress[download_id].update({
                                    'status': 'completed',
                                    'progress': 100,
                                    'message': f"✅ Successfully downloaded {result['count']} files (ZIP creation failed)",
                                    'file_count': len(result['files']),
                                    'warning': 'ZIP creation failed, but files were downloaded successfully'
                                })
                        else:
                            # For playlists without ZIP, use first file as download (or provide all files)
                            if result['files'] and len(result['files']) > 0:
                                # For single file playlist, download that file
                                # For multiple files, download first one (user can request ZIP)
                                first_file = result['files'][0]
                                download_progress[download_id].update({
                                    'status': 'completed',
                                    'progress': 100,
                                    'message': f"✅ Successfully downloaded {result['count']} files",
                                    'download_file': first_file,
                                    'download_filename': os.path.basename(first_file),
                                    'file_count': len(result['files']),
                                    'warning': 'For multiple files, enable ZIP option to download all at once'
                                })
                            else:
                                download_progress[download_id].update({
                                    'status': 'completed',
                                    'progress': 100,
                                    'message': f"✅ Successfully downloaded {result['count']} files",
                                    'file_count': len(result['files'])
                                })
                    else:
                        download_progress[download_id] = {
                            'status': 'error',
                            'error': result.get('error', 'Unknown error')
                        }
                else:
                    result = downloader.download_video(
                        url,
                        selected_format_id,
                        audio_only,
                        output_dir,
                        progress_hook
                    )
                    
                    if result['success']:
                        download_progress[download_id].update({
                            'status': 'completed',
                            'progress': 100,
                            'message': f"✅ Download completed: {result['basename']}",
                            'download_file': result['filename'],
                            'download_filename': result['basename']
                        })
                    else:
                        download_progress[download_id] = {
                            'status': 'error',
                            'error': result.get('error', 'Unknown error')
                        }
            except Exception as e:
                download_progress[download_id] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        thread = threading.Thread(target=download_thread)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'download_id': download_id,
            'message': 'Download started'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/download-status/<download_id>', methods=['GET'])
def download_status(download_id):
    """Get download status"""
    progress = download_progress.get(download_id, {
        'status': 'unknown',
        'message': 'Download not found'
    })
    return jsonify(progress)

@app.route('/api/download-file', methods=['GET'])
def download_file():
    """Serve a file for browser download"""
    filepath = request.args.get('file')
    if not filepath:
        return jsonify({'error': 'File path is required'}), 400
    
    # Validate file path is in temp directory for security
    if not filepath.startswith(downloader.temp_dir):
        return jsonify({'error': 'Invalid file path'}), 403
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    
    # Get filename from path
    filename = os.path.basename(filepath)
    
    return send_file(filepath, as_attachment=True, download_name=filename)

if __name__ == "__main__":
    # Use environment variables for production, defaults for local
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)