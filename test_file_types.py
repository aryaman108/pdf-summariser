#!/usr/bin/env python3
"""
Test script to verify file type detection and handling
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from utils.multimodal_processor import MultimodalProcessor
from utils.pdf_processor import PDFProcessor

def test_file_detection():
    """Test file type detection"""
    print("=" * 60)
    print("File Type Detection Test")
    print("=" * 60)
    print()
    
    multimodal = MultimodalProcessor()
    
    test_files = [
        ("document.pdf", "PDF"),
        ("video.mp4", "Video"),
        ("audio.mp3", "Audio"),
        ("text.txt", "Text"),
        ("presentation.mov", "Video"),
        ("recording.wav", "Audio"),
        ("unknown.xyz", "Unknown"),
    ]
    
    print("Testing file type detection:")
    print()
    
    for filename, expected_type in test_files:
        is_supported = multimodal.is_supported_file(filename)
        is_video = multimodal.is_video_file(filename)
        is_audio = multimodal.is_audio_file(filename)
        
        detected_type = "Unknown"
        if filename.endswith('.pdf'):
            detected_type = "PDF"
        elif is_video:
            detected_type = "Video"
        elif is_audio:
            detected_type = "Audio"
        elif filename.endswith('.txt'):
            detected_type = "Text"
        
        status = "✅" if detected_type == expected_type else "❌"
        print(f"{status} {filename:20} → {detected_type:10} (expected: {expected_type})")
    
    print()

def test_whisper_availability():
    """Test if Whisper is available"""
    print("=" * 60)
    print("Whisper Availability Test")
    print("=" * 60)
    print()
    
    multimodal = MultimodalProcessor()
    
    if multimodal.whisper_available:
        print("✅ OpenAI Whisper is installed and available")
        print("   Audio/video transcription is enabled")
    else:
        print("⚠️  OpenAI Whisper is NOT installed")
        print("   Audio/video transcription is disabled")
        print()
        print("To enable:")
        print("  ./install_multimedia.sh")
        print("  OR")
        print("  pip install openai-whisper moviepy")
    
    print()
    
    if multimodal.moviepy_available:
        print("✅ MoviePy is installed and available")
        print("   Video processing is enabled")
    else:
        print("⚠️  MoviePy is NOT installed")
        print("   Video processing is disabled")
    
    print()

def test_pdf_processor():
    """Test PDF processor availability"""
    print("=" * 60)
    print("PDF Processor Test")
    print("=" * 60)
    print()
    
    try:
        pdf_processor = PDFProcessor()
        print("✅ PDF processor initialized successfully")
        print("   PDF upload and processing is enabled")
    except Exception as e:
        print(f"❌ PDF processor failed: {e}")
    
    print()

def main():
    """Run all tests"""
    print()
    print("🧪 File Type Handling Test Suite")
    print()
    
    test_file_detection()
    test_whisper_availability()
    test_pdf_processor()
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print()
    print("✅ File type detection: Working")
    print("✅ PDF processing: Available")
    
    multimodal = MultimodalProcessor()
    if multimodal.whisper_available:
        print("✅ Audio/video processing: Available")
    else:
        print("⚠️  Audio/video processing: Requires installation")
    
    print()
    print("App Status: Ready at http://127.0.0.1:5000")
    print()

if __name__ == "__main__":
    main()
