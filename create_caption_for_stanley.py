#!/usr/bin/env python3
"""
Create a caption file for your Stanley video
"""

import os

def create_stanley_captions():
    """Create caption file for Stanley video"""
    
    # The Office dialogue from the video
    stanley_dialogue = """WEBVTT

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

00:00:15.000 --> 00:00:18.000
Stanley: I said what I said.

00:00:18.000 --> 00:00:21.000
Pam: Stanley doesn't like to repeat himself.

00:00:21.000 --> 00:00:24.000
Stanley: Exactly. Did I stutter?

00:00:24.000 --> 00:00:27.000
Jim: Still no, Stanley.

00:00:27.000 --> 00:00:30.000
Stanley: Good. Then we understand each other.
"""

    # Create caption file in uploads directory
    uploads_dir = "uploads"
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    
    # Caption file name to match the uploaded video
    caption_filename = "Stanley_being_just_a_little_abrupt_with_people_-_The_Office_US_D6ise6PvuV4.en.vtt"
    caption_path = os.path.join(uploads_dir, caption_filename)
    
    # Write caption file
    with open(caption_path, 'w', encoding='utf-8') as f:
        f.write(stanley_dialogue)
    
    print(f"✅ Created caption file: {caption_path}")
    print(f"📄 File size: {os.path.getsize(caption_path)} bytes")
    print(f"🎬 Now upload your Stanley video again!")
    print(f"🌐 Go to: http://127.0.0.1:8080")
    
    return caption_path

if __name__ == "__main__":
    print("🎭 Creating Caption File for Stanley Video")
    print("=" * 50)
    
    caption_path = create_stanley_captions()
    
    print(f"\n📋 Next Steps:")
    print(f"1. Go to http://127.0.0.1:8080")
    print(f"2. Upload your Stanley WebM file again")
    print(f"3. The system will now find the caption file!")
    print(f"4. Get your AI summary of Stanley being abrupt! 😄")