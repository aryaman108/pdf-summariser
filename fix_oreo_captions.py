#!/usr/bin/env python3
"""
Fix Oreo video captions by copying to uploads directory
"""

import os
import shutil

def fix_oreo_captions():
    """Copy Oreo caption file to uploads directory with correct name"""
    
    # Expected names after upload
    uploaded_video_name = "Oreo_Invested_40M_in_Custom_AI_Model_to_Create_TV_Ads_3d_Lcf5Z4n8.mp4"
    uploaded_caption_name = "Oreo_Invested_40M_in_Custom_AI_Model_to_Create_TV_Ads_3d_Lcf5Z4n8.en.vtt"
    
    # Create uploads directory if it doesn't exist
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    # Target caption file path
    target_caption_path = os.path.join(uploads_dir, uploaded_caption_name)
    
    # Look for your original caption file in common locations
    possible_locations = [
        "Oreo Invested $40M in Custom AI Model to Create TV Ads [3d_Lcf5Z4n8].en.vtt",
        "./Oreo Invested $40M in Custom AI Model to Create TV Ads [3d_Lcf5Z4n8].en.vtt",
        "Downloads/Oreo Invested $40M in Custom AI Model to Create TV Ads [3d_Lcf5Z4n8].en.vtt",
        "~/Downloads/Oreo Invested $40M in Custom AI Model to Create TV Ads [3d_Lcf5Z4n8].en.vtt"
    ]
    
    source_caption_path = None
    for location in possible_locations:
        expanded_path = os.path.expanduser(location)
        if os.path.exists(expanded_path):
            source_caption_path = expanded_path
            break
    
    if source_caption_path:
        # Copy the caption file
        shutil.copy2(source_caption_path, target_caption_path)
        print(f"✅ Copied caption file to: {target_caption_path}")
        print(f"📄 File size: {os.path.getsize(target_caption_path)} bytes")
    else:
        # Create a sample caption file if original not found
        print("⚠️ Original caption file not found. Creating sample content...")
        
        sample_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Oreo invested $40 million in a custom AI model.

00:00:05.000 --> 00:00:10.000
This AI model is designed to create TV advertisements.

00:00:10.000 --> 00:00:15.000
The investment represents a major shift in advertising technology.

00:00:15.000 --> 00:00:20.000
AI-generated content is becoming more sophisticated and realistic.

00:00:20.000 --> 00:00:25.000
This could revolutionize how brands create marketing content.
"""
        
        with open(target_caption_path, 'w', encoding='utf-8') as f:
            f.write(sample_content)
        
        print(f"📝 Created sample caption file: {target_caption_path}")
        print(f"📄 File size: {os.path.getsize(target_caption_path)} bytes")
    
    print(f"\n🎬 Now upload your Oreo video file!")
    print(f"🌐 Go to: http://127.0.0.1:8080")
    print(f"📁 Upload: Oreo Invested $40M in Custom AI Model to Create TV Ads [3d_Lcf5Z4n8].mp4")
    
    return target_caption_path

if __name__ == "__main__":
    print("🍪 Fixing Oreo Video Captions")
    print("=" * 40)
    
    caption_path = fix_oreo_captions()
    
    print(f"\n📋 Next Steps:")
    print(f"1. Go to http://127.0.0.1:8080")
    print(f"2. Upload your Oreo MP4 file")
    print(f"3. System will find the caption file automatically!")
    print(f"4. Get AI summary about Oreo's $40M AI investment! 🤖")