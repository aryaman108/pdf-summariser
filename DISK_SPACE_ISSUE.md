# Disk Space Issue - Resolution Guide

## Current Status

Your system has **critical disk space issues** that prevent the full installation of the Intelligent Document Agent:

- **Disk Usage:** 100% (196GB used out of 228GB)
- **Available Space:** Only 392MB
- **Required Space:** ~3GB for ML dependencies

## What's Running Now

I've started a **demo version** of the app that runs without ML models:

- **URL:** http://127.0.0.1:5000
- **Status:** Running (minimal Flask app)
- **Functionality:** Shows the UI structure but cannot perform summarization

## Why the Full App Won't Install

The application requires these large ML packages:

1. **PyTorch** (~150MB download, ~500MB installed)
2. **Transformers** (~12MB download, ~50MB installed)
3. **Model files** (~1-2GB when first used)
4. **Other dependencies** (~500MB)

**Total:** ~3GB of free space needed

## How to Fix This

### Option 1: Free Up Disk Space (Recommended)

#### Check what's using space:

```bash
# Check largest directories in your home folder
du -sh ~/* 2>/dev/null | sort -hr | head -20

# Check Homebrew cache (if installed)
du -sh /usr/local/Cellar 2>/dev/null

# Check Python caches
du -sh ~/.cache 2>/dev/null
```

#### Clean up common space hogs:

```bash
# Clean pip cache
rm -rf ~/.cache/pip

# Clean Homebrew cache (if using Homebrew)
brew cleanup

# Clean conda cache (if using Anaconda)
conda clean --all

# Empty trash
rm -rf ~/.Trash/*

# Clean Xcode derived data (if you have Xcode)
rm -rf ~/Library/Developer/Xcode/DerivedData/*

# Clean Docker (if installed)
docker system prune -a
```

#### After freeing space:

```bash
# Verify you have enough space
df -h .

# Install dependencies
source .venv/bin/activate
pip install --no-cache-dir -r requirements.txt

# Run the full app
python app.py
```

### Option 2: Use External Storage

If you can't free up space on your main drive:

```bash
# Create project on external drive
cd /Volumes/ExternalDrive
git clone <your-repo>
cd pdf-summariser

# Create virtual environment there
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --no-cache-dir -r requirements.txt

# Run the app
python app.py
```

### Option 3: Use Cloud/Remote Development

Consider using:

- **Google Colab** (free GPU access)
- **GitHub Codespaces** (cloud development environment)
- **AWS Cloud9** or **Azure Cloud Shell**

## What I've Done

1. ✅ **Identified the issue:** Disk at 100% capacity
2. ✅ **Installed minimal dependencies:** Flask and Werkzeug only
3. ✅ **Created demo app:** Running at http://127.0.0.1:5000
4. ✅ **Created this guide:** Step-by-step resolution instructions

## Files Created

- `app_minimal.py` - Demo version that runs without ML models
- `requirements_minimal.txt` - Minimal dependencies (Flask only)
- `DISK_SPACE_ISSUE.md` - This guide

## Next Steps

1. **Visit http://127.0.0.1:5000** to see the demo interface
2. **Free up at least 3GB** of disk space using the commands above
3. **Install full dependencies:**
   ```bash
   source .venv/bin/activate
   pip install --no-cache-dir -r requirements.txt
   ```
4. **Stop the demo app** (Ctrl+C in the terminal)
5. **Run the full app:**
   ```bash
   python app.py
   ```

## Disk Space Breakdown

Current large items on your system:

- Hugging Face cache: 3.9GB at `~/.cache/huggingface`
- (Run the commands above to find more)

## Testing Without Full Installation

If you want to test the code structure without installing ML models:

```bash
# The demo app is already running at:
http://127.0.0.1:5000

# You can also check the code for errors:
python -m py_compile app.py
python -m py_compile main.py
```

## Support

If you continue to have issues:

1. Check the terminal output for specific error messages
2. Verify disk space: `df -h .`
3. Check installed packages: `pip list`
4. Review the logs in the terminal where the app is running

---

**Current Status:** Demo app running successfully at http://127.0.0.1:5000
**Action Required:** Free up 3GB of disk space to enable full functionality
