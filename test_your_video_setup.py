#!/usr/bin/env python3
"""
Test script to demonstrate how your specific video setup will work
"""

import os
import sys
sys.path.insert(0, '.')

from utils.multimodal_processor import MultimodalProcessor

def simulate_your_video_test():
    """Simulate testing your video file setup"""
    
    # Your file setup
    video_name = "Stanley being just a little abrupt with people  - The Office US [D6ise6PvuV4].webm"
    caption_name = "Stanley being just a little abrupt with people  - The Office US [D6ise6PvuV4].en.vtt"
    
    print("🎬 Testing Your Video Setup")
    print("=" * 60)
    print(f"Video file: {video_name}")
    print(f"Caption file: {caption_name}")
    print()
    
    # Create a sample VTT content to demonstrate
    sample_vtt_content = """WEBVTT

00:00:00.000 --> 00:00:03.000
Stanley: Did I stutter?

00:00:03.000 --> 00:00:06.000
Jim: No, Stanley, you didn't stutter.

00:00:06.000 --> 00:00:09.000
Stanley: Then why are you still talking?

00:00:09.000 --> 00:00:12.000
Dwight: Stanley is being very direct today.

00:00:12.000 --> 00:00:15.000
Michael: That's just Stanley being Stanley.
"""
    
    processor = MultimodalProcessor()
    
    # Test VTT parsing
    print("📝 Testing VTT Content Parsing:")
    print("-" * 40)
    
    try:
        parsed_text = processor._parse_vtt_content(sample_vtt_content)
        print(f"✅ Successfully parsed VTT content")
        print(f"📊 Extracted {len(parsed_text)} characters")
        print(f"📄 Content preview: {parsed_text[:100]}...")
        
        print("\n🔍 How the system will find your caption file:")
        print("1. ✓ Check for exact match: video.vtt")
        print("2. ✓ Check for language-specific: video.en.vtt ← YOUR FILE!")
        print("3. ✓ Check for similar names in directory")
        
        print("\n💡 Your setup should work because:")
        print("• WebM format is supported")
        print("• VTT format is supported")
        print("• Language-specific naming (.en.vtt) is now supported")
        print("• The system will find files with similar base names")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def create_test_files():
    """Create test files to demonstrate the functionality"""
    
    # Create a test video filename (empty file for demo)
    test_video = "test_video.webm"
    test_caption = "test_video.en.vtt"
    
    # Create sample VTT content
    vtt_content = """WEBVTT

00:00:00.000 --> 00:00:03.000
This is a test caption.

00:00:03.000 --> 00:00:06.000
The system can now extract text from VTT files.

00:00:06.000 --> 00:00:09.000
Language-specific files like .en.vtt are supported.
"""
    
    # Create test files
    with open(test_video, 'w') as f:
        f.write("")  # Empty video file for demo
    
    with open(test_caption, 'w') as f:
        f.write(vtt_content)
    
    print(f"📁 Created test files:")
    print(f"   {test_video}")
    print(f"   {test_caption}")
    
    # Test the extraction
    processor = MultimodalProcessor()
    
    try:
        print(f"\n🧪 Testing caption extraction...")
        captions = processor.extract_captions_from_video(test_video)
        
        if captions:
            print(f"✅ SUCCESS: Extracted {len(captions)} characters")
            print(f"📝 Content: {captions}")
        else:
            print("❌ No captions extracted")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Clean up test files
        try:
            os.remove(test_video)
            os.remove(test_caption)
            print(f"\n🧹 Cleaned up test files")
        except:
            pass

if __name__ == "__main__":
    print("🎯 Your Video Setup Analysis")
    print("=" * 60)
    
    simulate_your_video_test()
    
    print("\n" + "=" * 60)
    print("🧪 Live Test with Sample Files")
    print("=" * 60)
    
    create_test_files()
    
    print("\n" + "=" * 60)
    print("📋 Next Steps for Your Files:")
    print("1. Make sure both files are in the same directory")
    print("2. Upload the .webm file through the web interface")
    print("3. The system will automatically find the .en.vtt file")
    print("4. Check the server logs for detailed extraction info")
    print("\n🌐 Web interface: http://127.0.0.1:8080")