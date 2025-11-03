# 🎬 YouTube Video Download Guide

## 🚀 **Quick Start**

### **Method 1: Using the Helper Script**

```bash
# Interactive mode
python download_youtube_with_captions.py

# Command line mode
python download_youtube_with_captions.py "https://www.youtube.com/watch?v=VIDEO_ID"

# With options
python download_youtube_with_captions.py "VIDEO_URL" -q 720p -l en es -o my_videos
```

### **Method 2: Direct yt-dlp Commands**

```bash
# Basic download with English captions
yt-dlp --write-subs --write-auto-subs --sub-lang en "VIDEO_URL"

# High quality with captions
yt-dlp --write-subs --write-auto-subs --sub-lang en --format "mp4[height<=720]" "VIDEO_URL"

# Multiple languages
yt-dlp --write-subs --write-auto-subs --sub-lang en,es,fr "VIDEO_URL"
```

## 📋 **Command Options Explained**

| Option                                  | Purpose                                   |
| --------------------------------------- | ----------------------------------------- |
| `--write-subs`                          | Download manual subtitles (human-created) |
| `--write-auto-subs`                     | Download auto-generated captions          |
| `--sub-lang en`                         | Download English subtitles                |
| `--format "mp4[height<=720]"`           | Download 720p MP4 format                  |
| `--output "%(title)s [%(id)s].%(ext)s"` | Custom filename pattern                   |

## 🎯 **Best Practices**

### **For Educational Content**

```bash
# TED Talks, lectures, tutorials
yt-dlp --write-subs --write-auto-subs --sub-lang en --format "mp4[height<=720]" "VIDEO_URL"
```

### **For Entertainment Content**

```bash
# TV shows, movies, comedy clips
yt-dlp --write-subs --write-auto-subs --sub-lang en --format "webm[height<=480]" "VIDEO_URL"
```

### **For Multilingual Content**

```bash
# International content
yt-dlp --write-subs --write-auto-subs --sub-lang en,es,fr,de --format "mp4" "VIDEO_URL"
```

## 📁 **File Output**

After downloading, you'll get files like:

```
Video Title [VIDEO_ID].mp4           # Video file
Video Title [VIDEO_ID].en.vtt        # English captions
Video Title [VIDEO_ID].es.vtt        # Spanish captions (if available)
Video Title [VIDEO_ID].live_chat.json  # Live chat (if available)
```

## 🔧 **Troubleshooting**

### **No Captions Available**

```bash
# Check what's available first
yt-dlp --list-subs "VIDEO_URL"
```

### **Download Only Captions**

```bash
# Skip video download, get only captions
yt-dlp --write-subs --write-auto-subs --sub-lang en --skip-download "VIDEO_URL"
```

### **Specific Caption Format**

```bash
# Force SRT format instead of VTT
yt-dlp --write-subs --write-auto-subs --sub-lang en --sub-format srt "VIDEO_URL"
```

## 🎬 **Example Workflows**

### **Workflow 1: Educational Video**

```bash
# 1. Download video with captions
yt-dlp --write-subs --write-auto-subs --sub-lang en "https://www.youtube.com/watch?v=EDUCATIONAL_VIDEO"

# 2. Upload to Intelligent Document Agent
# Go to http://127.0.0.1:8080 → File Upload → Select video file

# 3. Get AI summary of the educational content
```

### **Workflow 2: Multiple Videos**

```bash
# Create a playlist file (urls.txt)
echo "https://www.youtube.com/watch?v=VIDEO1" > urls.txt
echo "https://www.youtube.com/watch?v=VIDEO2" >> urls.txt

# Download all with captions
yt-dlp --write-subs --write-auto-subs --sub-lang en --batch-file urls.txt
```

## 🌐 **Integration with Document Agent**

### **Supported Formats**

- ✅ MP4 with embedded or companion captions
- ✅ WebM with .vtt caption files
- ✅ Any video format + .srt/.vtt files

### **Caption File Patterns**

The system automatically detects:

- `video.vtt` (exact match)
- `video.en.vtt` (language-specific)
- `video.english.vtt` (language name)
- Similar named files in same directory

### **Upload Process**

1. **Download** video with captions using methods above
2. **Navigate** to http://127.0.0.1:8080
3. **Click** "File Upload" tab
4. **Select** the video file (system finds captions automatically)
5. **Choose** quality mode and upload
6. **Get** AI-generated summary of video content

## 💡 **Pro Tips**

1. **Always use both** `--write-subs` and `--write-auto-subs` for maximum coverage
2. **Check caption availability** with `--list-subs` first
3. **Use 720p quality** for good balance of size and quality
4. **Download to organized folders** for easy management
5. **Keep video and caption files together** in same directory

---

**Ready to download and summarize YouTube content with AI!** 🚀
