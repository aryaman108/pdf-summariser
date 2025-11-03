#!/usr/bin/env python3
"""
YouTube Video Downloader with Captions
Perfect for the Intelligent Document Agent
"""

import subprocess
import sys
import os
import argparse

def download_youtube_video(url, output_dir=".", quality="720p", languages=["en"]):
    """
    Download YouTube video with captions
    
    Args:
        url: YouTube video URL
        output_dir: Directory to save files
        quality: Video quality (720p, 480p, 1080p, etc.)
        languages: List of subtitle languages to download
    """
    
    print(f"🎬 Downloading YouTube video with captions...")
    print(f"📹 URL: {url}")
    print(f"📁 Output: {output_dir}")
    print(f"🎯 Quality: {quality}")
    print(f"🌐 Languages: {', '.join(languages)}")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Build yt-dlp command
    cmd = [
        "yt-dlp",
        "--write-subs",           # Download manual subtitles
        "--write-auto-subs",      # Download auto-generated subtitles
        "--sub-lang", ",".join(languages),  # Subtitle languages
        "--output", f"{output_dir}/%(title)s [%(id)s].%(ext)s",  # Output filename pattern
    ]
    
    # Add quality filter
    if quality:
        height = quality.replace("p", "")
        cmd.extend(["--format", f"mp4[height<={height}]"])
    
    # Add URL
    cmd.append(url)
    
    try:
        print("🚀 Starting download...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Download completed successfully!")
            print("\n📁 Files downloaded:")
            
            # List downloaded files
            for file in os.listdir(output_dir):
                if any(ext in file for ext in ['.mp4', '.webm', '.mkv', '.vtt', '.srt']):
                    print(f"   {file}")
            
            print(f"\n💡 Ready to upload to Intelligent Document Agent!")
            print(f"🌐 Web interface: http://127.0.0.1:8080")
            
        else:
            print("❌ Download failed!")
            print(f"Error: {result.stderr}")
            
    except FileNotFoundError:
        print("❌ yt-dlp not found!")
        print("Install with: pip install yt-dlp")
        return False
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Download YouTube videos with captions")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("-o", "--output", default="downloads", help="Output directory")
    parser.add_argument("-q", "--quality", default="720p", help="Video quality (720p, 480p, 1080p)")
    parser.add_argument("-l", "--languages", nargs="+", default=["en"], help="Subtitle languages")
    
    args = parser.parse_args()
    
    success = download_youtube_video(
        url=args.url,
        output_dir=args.output,
        quality=args.quality,
        languages=args.languages
    )
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Go to http://127.0.0.1:8080")
        print("2. Click 'File Upload' tab")
        print("3. Upload the downloaded video file")
        print("4. The system will automatically find and use the caption files!")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # Interactive mode
        print("🎬 YouTube Video Downloader with Captions")
        print("=" * 50)
        
        url = input("Enter YouTube URL: ").strip()
        if not url:
            print("❌ No URL provided")
            sys.exit(1)
        
        quality = input("Video quality (720p, 480p, 1080p) [720p]: ").strip() or "720p"
        
        download_youtube_video(url, quality=quality)
    else:
        main()