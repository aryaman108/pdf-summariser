#!/usr/bin/env python3
"""
Debug script for your specific video files
"""

import sys
import os
sys.path.insert(0, '.')

from utils.multimodal_processor import MultimodalProcessor

def debug_file(filepath):
    """Debug a specific file"""
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    
    print(f"🔍 Debugging file: {os.path.basename(filepath)}")
    print("=" * 60)
    
    processor = MultimodalProcessor()
    
    # Check file size
    file_size = os.path.getsize(filepath)
    print(f"📊 File size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    # Check if supported
    is_supported = processor.is_supported_file(filepath)
    print(f"📁 Supported format: {'✅ Yes' if is_supported else '❌ No'}")
    
    # Check file type
    is_video = processor.is_video_file(filepath)
    is_audio = processor.is_audio_file(filepath)
    print(f"🎬 Video file: {'✅ Yes' if is_video else '❌ No'}")
    print(f"🎵 Audio file: {'✅ Yes' if is_audio else '❌ No'}")
    
    # Check file header
    try:
        with open(filepath, 'rb') as f:
            header = f.read(12)
        
        print(f"🔢 File header (hex): {header.hex()}")
        print(f"🔤 File header (ascii): {header}")
        
        # Test validation
        is_valid = processor._validate_file_header(header, filepath)
        print(f"✅ Header validation: {'✅ Pass' if is_valid else '❌ Fail'}")
        
    except Exception as e:
        print(f"❌ Error reading header: {e}")
    
    # Check for companion files
    base_path = os.path.splitext(filepath)[0]
    directory = os.path.dirname(filepath) or '.'
    
    print(f"\n📁 Checking for companion subtitle files...")
    subtitle_extensions = ['.srt', '.vtt', '.ass', '.ssa', '.sub', '.sbv']
    language_codes = ['', '.en', '.eng', '.english', '.es', '.fr', '.de']
    
    found_subtitles = []
    
    # Check exact matches
    for ext in subtitle_extensions:
        subtitle_file = base_path + ext
        if os.path.exists(subtitle_file):
            found_subtitles.append(subtitle_file)
    
    # Check language-specific
    for lang in language_codes:
        if not lang:
            continue
        for ext in subtitle_extensions:
            subtitle_file = base_path + lang + ext
            if os.path.exists(subtitle_file):
                found_subtitles.append(subtitle_file)
    
    # Check similar names in directory
    try:
        video_basename = os.path.basename(base_path)
        for filename in os.listdir(directory):
            if filename.startswith(video_basename):
                for ext in subtitle_extensions:
                    if filename.endswith(ext):
                        subtitle_file = os.path.join(directory, filename)
                        if subtitle_file not in found_subtitles:
                            found_subtitles.append(subtitle_file)
    except Exception as e:
        print(f"⚠️ Could not scan directory: {e}")
    
    if found_subtitles:
        print(f"✅ Found {len(found_subtitles)} subtitle files:")
        for sub in found_subtitles:
            sub_size = os.path.getsize(sub)
            print(f"   📄 {os.path.basename(sub)} ({sub_size:,} bytes)")
    else:
        print("❌ No subtitle files found")
    
    # Try caption extraction if it's a video
    if is_video and is_supported:
        print(f"\n🎬 Testing caption extraction...")
        try:
            captions = processor.extract_captions_from_video(filepath)
            if captions:
                print(f"✅ SUCCESS: Extracted {len(captions)} characters")
                print(f"📝 Preview: {captions[:200]}...")
            else:
                print("❌ No captions extracted")
        except Exception as e:
            print(f"❌ Caption extraction failed: {e}")
    
    print("\n" + "=" * 60)

def main():
    # Test your specific files
    test_files = [
        "Stanley being just a little abrupt with people  - The Office US [D6ise6PvuV4].webm",
        "videoplayback (4).mp4"
    ]
    
    print("🔍 Debugging Your Video Files")
    print("=" * 60)
    
    for filepath in test_files:
        if os.path.exists(filepath):
            debug_file(filepath)
        else:
            print(f"⚠️ File not found: {filepath}")
            print("   (Make sure the file is in the current directory)")
        print()
    
    # Also check for any video files in current directory
    print("📁 Scanning current directory for video files...")
    video_extensions = ['.mp4', '.webm', '.avi', '.mov', '.mkv', '.flv']
    
    found_videos = []
    try:
        for filename in os.listdir('.'):
            for ext in video_extensions:
                if filename.lower().endswith(ext):
                    found_videos.append(filename)
    except Exception as e:
        print(f"❌ Error scanning directory: {e}")
    
    if found_videos:
        print(f"✅ Found {len(found_videos)} video files:")
        for video in found_videos:
            print(f"   🎬 {video}")
        
        print(f"\n💡 To test any of these files:")
        print(f"   python debug_your_files.py filename.mp4")
    else:
        print("❌ No video files found in current directory")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific file
        debug_file(sys.argv[1])
    else:
        # Test your known files
        main()