# Caption Extraction Improvements

## 🎯 Problem Solved

Fixed the issue where videos with captions were showing "No captions/subtitles found" error, even when captions were available.

## 🔧 Improvements Made

### 1. Enhanced Caption Extraction Methods

- **Method 1**: Extract embedded subtitle tracks from video files
- **Method 2**: Check for companion subtitle files (.srt, .vtt, .ass, etc.)
- **Method 3**: Extract text from video metadata/descriptions
- **Better parsing**: Improved SRT and VTT subtitle format parsing

### 2. Improved Debugging & Logging

- Detailed video stream analysis
- Step-by-step extraction logging
- Better error messages with specific guidance
- File size and content validation

### 3. Enhanced Error Messages

- Clear explanations of what went wrong
- Specific instructions for different scenarios
- Alternative solutions (text input, PDF upload)
- References to helper tools and guides

### 4. Helper Tools Created

- `test_caption_extraction.py`: Test if a video has extractable captions
- `add_captions_guide.md`: Comprehensive guide for adding captions to videos
- Better web interface error messages

## 🚀 How to Use

### Test Your Videos

```bash
python test_caption_extraction.py your_video.mp4
```

### Supported Caption Types

1. **Embedded subtitles**: Professional videos, YouTube downloads with captions
2. **Companion files**: Place `.srt`, `.vtt`, etc. files with same name as video
3. **Metadata text**: Videos with descriptive text in metadata

### Download YouTube Videos with Captions

```bash
yt-dlp --write-subs --write-auto-subs --sub-lang en "https://youtube.com/watch?v=VIDEO_ID"
```

## 📋 Technical Changes

### Files Modified

- `utils/multimodal_processor.py`: Enhanced caption extraction logic
- `app.py`: Improved error handling and user guidance
- Added helper scripts and documentation

### Key Improvements

- Multiple extraction methods with fallbacks
- Better subtitle format parsing (SRT, VTT, ASS, etc.)
- Detailed logging for troubleshooting
- Lower threshold for caption acceptance (50 chars vs 100)
- Comprehensive error messages with actionable solutions

## 🎬 Video Requirements

### ✅ Videos That Will Work

- YouTube videos downloaded with `--write-subs`
- Videos with embedded subtitle tracks
- Videos with companion subtitle files
- Professional videos with built-in captions

### ❌ Videos That Won't Work

- Screen recordings without captions
- Phone videos without subtitles
- Videos without any text content
- Audio-only files (transcription disabled)

## 🔍 Troubleshooting

### Still Getting "No Captions Found"?

1. Use the test script to verify: `python test_caption_extraction.py video.mp4`
2. Check the server logs for detailed extraction attempts
3. Try creating a manual `.srt` file with the same name as your video
4. Use the "Text Input" tab as an alternative

### Common Solutions

- **YouTube videos**: Download with captions using yt-dlp
- **Manual captions**: Create `.srt` files with matching filenames
- **Alternative**: Copy transcript text and use direct text input
- **Fallback**: Upload PDF or text files instead

## 📊 Expected Results

The improved system now provides:

- **Better success rate** for caption extraction
- **Clear debugging information** in server logs
- **Helpful error messages** with specific guidance
- **Multiple extraction methods** with automatic fallbacks
- **User-friendly tools** for testing and troubleshooting

---

**Application Status**: ✅ Running on http://127.0.0.1:8080 with enhanced caption extraction
