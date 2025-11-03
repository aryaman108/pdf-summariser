#!/usr/bin/env python3
"""
Test script to check if a video file has extractable captions
"""

import sys
import os
sys.path.insert(0, '.')

from utils.multimodal_processor import MultimodalProcessor

def test_video_captions(video_path):
    """Test caption extraction for a video file"""
    if not os.path.exists(video_path):
        print(f"❌ File not found: {video_path}")
        return
    
    print(f"🎬 Testing caption extraction for: {os.path.basename(video_path)}")
    print("=" * 60)
    
    processor = MultimodalProcessor()
    
    # Test if file is supported
    if not processor.is_video_file(video_path):
        print("❌ File is not a supported video format")
        return
    
    # Try to extract captions
    try:
        captions = processor.extract_captions_from_video(video_path)
        
        if captions:
            print(f"✅ SUCCESS: Extracted {len(captions)} characters")
            print("\n📝 First 200 characters of extracted text:")
            print("-" * 40)
            print(captions[:200] + "..." if len(captions) > 200 else captions)
            print("-" * 40)
        else:
            print("❌ No captions found")
            print("\n💡 Tips for videos with captions:")
            print("• Make sure the video has embedded subtitle tracks")
            print("• Include a .srt or .vtt file with the same name")
            print("• Check if the video has descriptive metadata")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_caption_extraction.py <video_file>")
        print("Example: python test_caption_extraction.py my_video.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    test_video_captions(video_path)