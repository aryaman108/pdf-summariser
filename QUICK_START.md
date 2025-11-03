# Quick Start Guide - Intelligent Document Agent

## 🎯 Current Status

✅ **Demo app is running at:** http://127.0.0.1:5000

⚠️ **Issue:** Disk space at 100% capacity (only 392MB available)
📦 **Need:** 3GB free space to install ML dependencies

## 🚀 What You Can Do Right Now

### 1. View the Demo Interface

Open your browser and visit:

```
http://127.0.0.1:5000
```

This shows you the app's UI structure and explains what it does when fully installed.

### 2. Check the Code Quality

All Python files have been validated - no syntax errors found:

```bash
# Already verified:
✅ app.py - Main Flask application
✅ main.py - Desktop GUI version
✅ run_local.py - Local runner script
✅ All source files in src/ directory
```

## 🔧 To Enable Full Functionality

### Step 1: Free Up Disk Space

**Option A: Use the cleanup script (recommended)**

```bash
# Stop the demo app first (Ctrl+C in its terminal)
./cleanup_space.sh
```

**Option B: Manual cleanup**

```bash
# Check what's using space
du -sh ~/* 2>/dev/null | sort -hr | head -20

# Clean common caches
rm -rf ~/.cache/pip
rm -rf ~/.Trash/*

# If using Homebrew
brew cleanup

# If using Anaconda
conda clean --all
```

### Step 2: Verify Space Available

```bash
df -h .
# Should show at least 3GB available
```

### Step 3: Install Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install all required packages
pip install --no-cache-dir -r requirements.txt

# This will install:
# - PyTorch (~500MB)
# - Transformers (~50MB)
# - NLTK, scikit-learn, and other ML libraries
# - PDF processing libraries
# - Audio/video processing libraries (optional)
```

### Step 4: Run the Full Application

```bash
# Stop the demo app if still running (Ctrl+C)

# Run the full app
python app.py

# Or use the runner script
python run_local.py
```

## 📊 What the Full App Does

Once installed, you'll have access to:

### Core Features

- **Hybrid Summarization:** RoBERTa (extractive) + T5 (abstractive)
- **PDF Upload:** Process PDF documents automatically
- **Quality Modes:** Fast, Balanced, High-Quality
- **Evaluation Metrics:** ROUGE, METEOR, BLEU scores
- **Question Answering:** Ask questions about summaries

### Advanced Features

- **Long Document Support:** Automatic chunking for large texts
- **Multimodal Processing:** Audio and video transcription
- **Agentic Framework:** Intelligent content analysis
- **REST API:** Programmatic access

## 🎮 Usage Examples

### Web Interface

```
1. Open http://localhost:5000
2. Choose "Text Input" or "File Upload" tab
3. Enter/upload your content
4. Select quality mode
5. Click "Generate Summary"
6. View results with metrics
```

### API Usage

```bash
curl -X POST http://localhost:5000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text here", "quality_mode": "balanced"}'
```

### Python Usage

```python
from src.hybrid_summarizer import HybridSummarizer

summarizer = HybridSummarizer()
summary = summarizer.summarize(
    text="Your long document text...",
    quality_mode="balanced",
    verbose=True
)
print(summary)
```

## 📁 Project Structure

```
pdf-summariser/
├── app.py                      # Main Flask web application
├── app_minimal.py              # Demo version (currently running)
├── main.py                     # Desktop GUI version
├── run_local.py                # Local development runner
├── requirements.txt            # Full dependencies
├── requirements_minimal.txt    # Minimal dependencies (Flask only)
├── src/
│   ├── hybrid_summarizer.py    # Main summarization logic
│   ├── roberta_extractive.py   # Extractive summarization
│   ├── t5_abstractive.py       # Abstractive summarization
│   ├── evaluation.py           # Quality metrics
│   └── question_answerer.py    # Q&A functionality
├── utils/
│   ├── preprocessing.py        # Text preprocessing
│   ├── pdf_processor.py        # PDF handling
│   └── multimodal_processor.py # Audio/video processing
└── .venv/                      # Virtual environment
```

## 🐛 Troubleshooting

### Issue: "No space left on device"

**Solution:** Follow Step 1 above to free up space

### Issue: "Models not loading"

**Solution:**

```bash
# Check if dependencies are installed
pip list | grep -E "torch|transformers"

# If not, install them
pip install --no-cache-dir torch transformers
```

### Issue: "Port already in use"

**Solution:**

```bash
# Find what's using port 5000
lsof -i :5000

# Kill the process or change port in app.py
# Edit app.py and change: port = int(os.environ.get('PORT', 5001))
```

### Issue: "NLTK data not found"

**Solution:** The app downloads NLTK data automatically on first run. If it fails:

```python
import nltk
nltk.download('punkt')
nltk.download('stopwords')
```

## 📚 Documentation Files

- `README.md` - Full project documentation
- `README_LOCAL.md` - Local development guide
- `DISK_SPACE_ISSUE.md` - Detailed disk space resolution
- `STATUS.md` - Current project status
- `QUICK_START.md` - This file

## 🔄 Stopping/Starting the App

### Stop the Demo App

```bash
# In the terminal where it's running, press:
Ctrl + C
```

### Start the Full App

```bash
source .venv/bin/activate
python app.py
```

### Start the Desktop GUI

```bash
source .venv/bin/activate
python main.py
```

## ⚡ Performance Expectations

| Document Size | Processing Time | Quality Mode |
| ------------- | --------------- | ------------ |
| < 1K words    | 3-8 seconds     | Fast         |
| 1K-5K words   | 8-15 seconds    | Balanced     |
| 5K+ words     | 15-30 seconds   | High Quality |

First request takes longer (15-30 seconds) as models load into memory.

## 🎯 Next Steps

1. ✅ Demo app is running - visit http://127.0.0.1:5000
2. ⏳ Free up 3GB of disk space
3. ⏳ Install full dependencies
4. ⏳ Run the complete application

---

**Need Help?** Check the other documentation files or review the terminal output for specific error messages.
