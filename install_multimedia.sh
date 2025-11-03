#!/bin/bash

# Install multimedia dependencies for audio/video processing

echo "============================================================"
echo "Multimedia Support Installation"
echo "============================================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check available disk space
AVAILABLE=$(df -k . | tail -1 | awk '{print $4}')
NEEDED=$((2 * 1024 * 1024))  # 2GB in KB

echo "Checking disk space..."
echo "Available: $(($AVAILABLE / 1024))MB"
echo "Required: ~2GB"
echo ""

if [ $AVAILABLE -lt $NEEDED ]; then
    echo "⚠️  Warning: Low disk space. Installation may fail."
    echo "Consider freeing up more space before continuing."
    echo ""
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
fi

# Install OpenAI Whisper
echo "============================================================"
echo "Installing OpenAI Whisper (speech-to-text)..."
echo "============================================================"
pip install --no-cache-dir openai-whisper
if [ $? -eq 0 ]; then
    echo "✅ Whisper installed successfully"
else
    echo "❌ Whisper installation failed"
    exit 1
fi
echo ""

# Install MoviePy
echo "============================================================"
echo "Installing MoviePy (video processing)..."
echo "============================================================"
pip install --no-cache-dir moviepy
if [ $? -eq 0 ]; then
    echo "✅ MoviePy installed successfully"
else
    echo "❌ MoviePy installation failed"
    exit 1
fi
echo ""

# Check for FFmpeg
echo "============================================================"
echo "Checking FFmpeg..."
echo "============================================================"
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg is already installed!"
    ffmpeg -version | head -1
else
    echo "⚠️  FFmpeg not found!"
    echo ""
    echo "FFmpeg is required for video processing."
    echo "Please install it using:"
    echo ""
    echo "  macOS:   brew install ffmpeg"
    echo "  Linux:   sudo apt-get install ffmpeg"
    echo "  Windows: Download from https://ffmpeg.org/download.html"
    echo ""
    read -p "Do you want to install FFmpeg now (macOS only)? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v brew &> /dev/null; then
            echo "Installing FFmpeg via Homebrew..."
            brew install ffmpeg
            if [ $? -eq 0 ]; then
                echo "✅ FFmpeg installed successfully"
            else
                echo "❌ FFmpeg installation failed"
            fi
        else
            echo "❌ Homebrew not found. Please install FFmpeg manually."
        fi
    fi
fi
echo ""

# Test imports
echo "============================================================"
echo "Testing installations..."
echo "============================================================"

python -c "import whisper; print('✅ Whisper import successful')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Whisper import failed"
fi

python -c "import moviepy.editor; print('✅ MoviePy import successful')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ MoviePy import failed"
fi

echo ""
echo "============================================================"
echo "Installation Summary"
echo "============================================================"
echo ""
echo "Installed packages:"
pip list | grep -E "whisper|moviepy|ffmpeg"
echo ""

# Check if app is running
if lsof -i :5000 &> /dev/null; then
    echo "⚠️  The app is currently running on port 5000"
    echo ""
    echo "To enable multimedia support:"
    echo "  1. Stop the app (Ctrl+C in its terminal)"
    echo "  2. Restart with: python app.py"
else
    echo "✅ Ready to start the app with multimedia support!"
    echo ""
    echo "Start the app with:"
    echo "  python app.py"
fi

echo ""
echo "============================================================"
echo "Supported formats after installation:"
echo "============================================================"
echo "Audio: MP3, WAV, FLAC, M4A, AAC, OGG"
echo "Video: MP4, AVI, MOV, MKV, WebM, FLV"
echo ""
echo "The app will automatically transcribe speech to text"
echo "and then generate summaries of the spoken content."
echo "============================================================"
