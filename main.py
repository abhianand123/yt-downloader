import os
from yt_dlp import YoutubeDL

def convert_music_url_to_youtube(url):
    """Convert YouTube Music URLs to regular YouTube URLs."""
    if "music.youtube.com" in url:
        converted_url = url.replace("music.youtube.com", "youtube.com")
        print("\n🔄 Converting YouTube Music link to YouTube link...")
        print(f"   Before: {url}")
        print(f"   After:  {converted_url}\n")
        return converted_url
    return url


def print_progress(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip()
        speed = d.get('_speed_str', '').strip()
        eta = d.get('eta', 0)
        print(f"\r⬇️  {percent} | {speed} | ETA: {eta}s", end='', flush=True)
    elif d['status'] == 'finished':
        print("\n✅ Finished downloading, now processing...")

def download_media(url, format_choice):
    base_output = os.path.join("Downloads", "%(playlist_title)s", "%(playlist_index)s - %(title)s.%(ext)s")

    ydl_opts = {
        'outtmpl': base_output,
        'ignoreerrors': True,
        'noplaylist': False,
        'progress_hooks': [print_progress],
        'geo_bypass': True,
        'age_limit': 0,
        'extract_flat': False,
        'force_generic_extractor': False,
    }

    if format_choice == "mp3":
        ydl_opts.update({
            'format': 'bestaudio/best',
            'writethumbnail': True,
            'postprocessors': [
                {'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'},
                {'key': 'EmbedThumbnail'},
                {'key': 'FFmpegMetadata'},
            ],
            'addmetadata': True,
        })
    else:  # MP4
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4',
        })

    os.makedirs("Downloads", exist_ok=True)
    with YoutubeDL(ydl_opts) as ydl:
        print("\n🎬 Download started...\n")
        ydl.download([url])
        print("\n✅ All downloads completed!\n")

def main():
    print("🎧 YouTube / YouTube Music Downloader (MP3 & MP4)")
    print("---------------------------------------------------")
    url = input("🔗 Enter YouTube or YouTube Music URL: ").strip()

    # Convert YouTube Music URLs to YouTube URLs
    url = convert_music_url_to_youtube(url)

    print("\n🎵 Choose format:")
    print("1. MP3 (audio only)")
    print("2. MP4 (video)")
    choice = input("Enter 1 or 2: ").strip()

    format_choice = "mp3" if choice == "1" else "mp4" if choice == "2" else None
    if not format_choice:
        print("❌ Invalid input!")
        return

    download_media(url, format_choice)

if __name__ == "__main__":
    main()
