# How to Add Captions to Your Videos

The Intelligent Document Agent can extract text from videos with captions. Here are several ways to ensure your videos work with the system:

## ✅ Supported Caption Types

### 1. Embedded Subtitle Tracks

Videos with built-in subtitle tracks (like professional videos or YouTube downloads with captions)

### 2. Companion Subtitle Files

Place a subtitle file with the same name as your video:

- `my_video.mp4` + `my_video.srt`
- `my_video.mp4` + `my_video.vtt`
- Supported formats: `.srt`, `.vtt`, `.ass`, `.ssa`, `.sub`, `.sbv`

### 3. Video Metadata

Videos with descriptive text in their metadata/description fields

## 🛠️ How to Add Captions to Your Videos

### Method 1: Download YouTube Videos with Captions

```bash
# Using yt-dlp (recommended)
yt-dlp --write-subs --write-auto-subs --sub-lang en "https://youtube.com/watch?v=VIDEO_ID"

# This downloads both video and subtitle files
```

### Method 2: Create SRT Files Manually

Create a `.srt` file with the same name as your video:

```
1
00:00:00,000 --> 00:00:05,000
This is the first subtitle line.

2
00:00:05,000 --> 00:00:10,000
This is the second subtitle line.
```

### Method 3: Use Auto-Captioning Tools

- **YouTube Studio**: Upload to YouTube, enable auto-captions, download
- **Rev.com**: Professional transcription service
- **Otter.ai**: AI-powered transcription
- **Whisper**: OpenAI's speech-to-text (if you enable it)

### Method 4: Embed Subtitles in Video

```bash
# Using FFmpeg to embed SRT into MP4
ffmpeg -i input.mp4 -i subtitles.srt -c copy -c:s mov_text output.mp4
```

## 🧪 Testing Your Videos

Use the test script to check if your video has extractable captions:

```bash
python test_caption_extraction.py your_video.mp4
```

## 📋 Troubleshooting

### "No captions found" Error

1. **Check file format**: Ensure it's a supported video format
2. **Verify captions exist**: Use the test script above
3. **Check companion files**: Make sure subtitle files have exact same name
4. **Try different formats**: Convert subtitles to .srt format

### Common Issues

- **YouTube videos**: Download with `--write-subs` flag
- **Screen recordings**: Usually don't have captions - add manually
- **Phone videos**: Rarely have captions - create subtitle file
- **Professional videos**: Often have embedded captions

## 💡 Best Practices

1. **Use SRT format**: Most compatible subtitle format
2. **Match filenames exactly**: `video.mp4` needs `video.srt`
3. **Check encoding**: Use UTF-8 encoding for subtitle files
4. **Test first**: Use the test script before uploading large files

## 🔧 Alternative: Direct Text Input

If caption extraction fails, you can:

1. Copy text from YouTube's transcript feature
2. Use the "Text Input" tab in the web interface
3. Upload a PDF or text file instead

---

**Need help?** The application provides detailed error messages to guide you through the process.
