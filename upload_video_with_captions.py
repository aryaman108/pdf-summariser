#!/usr/bin/env python3
"""
Upload video with companion caption files to the Intelligent Document Agent
"""

import requests
import os
import sys

def upload_video_with_captions(video_path, caption_path=None, server_url="http://127.0.0.1:8080"):
    """
    Upload video file and process with companion captions
    
    Args:
        video_path: Path to video file
        caption_path: Path to caption file (optional, will auto-detect)
        server_url: Server URL
    """
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    # Auto-detect caption file if not provided
    if not caption_path:
        base_path = os.path.splitext(video_path)[0]
        possible_captions = [
            base_path + ".vtt",
            base_path + ".en.vtt", 
            base_path + ".srt",
            base_path + ".en.srt"
        ]
        
        for cap_file in possible_captions:
            if os.path.exists(cap_file):
                caption_path = cap_file
                break
    
    if caption_path and os.path.exists(caption_path):
        print(f"📄 Found caption file: {os.path.basename(caption_path)}")
        
        # Copy caption file to same directory as video with matching name
        video_dir = os.path.dirname(video_path)
        video_base = os.path.splitext(os.path.basename(video_path))[0]
        caption_ext = os.path.splitext(caption_path)[1]
        
        # Create matching caption file name
        new_caption_path = os.path.join(video_dir, video_base + caption_ext)
        
        if caption_path != new_caption_path:
            import shutil
            shutil.copy2(caption_path, new_caption_path)
            print(f"📋 Copied caption file to: {os.path.basename(new_caption_path)}")
    
    print(f"🎬 Uploading video: {os.path.basename(video_path)}")
    print(f"🌐 Server: {server_url}")
    
    try:
        with open(video_path, 'rb') as video_file:
            files = {'file': video_file}
            data = {'quality_mode': 'balanced'}
            
            response = requests.post(server_url, files=files, data=data)
            
            if response.status_code == 200:
                print("✅ Upload successful!")
                
                # Check if summary was generated
                if "summary" in response.text.lower():
                    print("🎯 Summary generated successfully!")
                    return True
                else:
                    print("⚠️ Upload successful but no summary generated")
                    print("Check the web interface for details")
                    return False
            else:
                print(f"❌ Upload failed: {response.status_code}")
                print(response.text[:500])
                return False
                
    except Exception as e:
        print(f"❌ Error uploading: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("🎬 Video Upload with Captions")
        print("=" * 40)
        print("Usage:")
        print("  python upload_video_with_captions.py video_file.webm")
        print("  python upload_video_with_captions.py video_file.webm caption_file.vtt")
        print()
        
        # Interactive mode
        video_path = input("Enter video file path: ").strip().strip('"')
        if not video_path:
            print("❌ No video file provided")
            return
        
        caption_path = input("Enter caption file path (optional): ").strip().strip('"')
        caption_path = caption_path if caption_path else None
        
        upload_video_with_captions(video_path, caption_path)
    else:
        video_path = sys.argv[1]
        caption_path = sys.argv[2] if len(sys.argv) > 2 else None
        
        upload_video_with_captions(video_path, caption_path)

if __name__ == "__main__":
    main()