# Intelligent Document Agent - Local Development

## Quick Start

1. **Activate Virtual Environment:**
   ```bash
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

2. **Run the Application:**
   ```bash
   python run_local.py
   ```
   Or directly:
   ```bash
   python app.py
   ```

3. **Open Browser:**
   - Web Interface: http://localhost:5000
   - API Endpoint: http://localhost:5000/api/summarize

## Features

### 📄 Document Upload & Summarization
- **PDF Support**: Upload PDF files up to 50MB
- **Text Input**: Direct text summarization
- **Quality Modes**:
  - Fast: Quick results (3-8 seconds)
  - Balanced: Optimal quality-speed ratio (recommended)
  - High Quality: Maximum accuracy (8-25 seconds)

### 🤖 AI-Powered Summarization
- **Hybrid Approach**: Combines extractive and abstractive methods
- **RoBERTa + T5 Models**: State-of-the-art transformer models
- **Intelligent Chunking**: Handles long documents automatically
- **Content Analysis**: Detects document type and complexity

### ⚡ Performance Optimizations
- **Model Pre-loading**: Models load at startup for faster responses
- **Smart Caching**: Repeated requests served instantly
- **Batch Processing**: Optimized for multiple sentences
- **Memory Management**: Efficient resource usage

## API Usage

### Web Interface
Simply open http://localhost:5000 in your browser and use the intuitive web interface.

### REST API
```bash
curl -X POST http://localhost:5000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Your text here", "quality_mode": "balanced"}'
```

### File Upload via API
```bash
curl -X POST http://localhost:5000/ \
  -F "file=@document.pdf" \
  -F "quality_mode=balanced"
```

## System Requirements

- **Python**: 3.8+
- **RAM**: 4GB+ recommended (8GB+ for large documents)
- **Storage**: 2GB+ for models
- **Internet**: Required for initial model download

## Troubleshooting

### Common Issues

1. **Models not loading:**
   - Check internet connection
   - Ensure sufficient RAM (4GB+)
   - Wait for initial download (may take 5-10 minutes)

2. **Port already in use:**
   - Change port in app.py: `port = int(os.environ.get('PORT', 5001))`

3. **Memory errors:**
   - Reduce batch size in roberta_extractive.py
   - Use 'fast' quality mode for large documents

4. **PDF processing fails:**
   - Ensure PDF is not password-protected
   - Check file size (max 50MB)
   - Try with a different PDF

### Logs
Check the terminal output for detailed error messages and performance metrics.

## Development

### Project Structure
```
ext-summarizer-roberta-t5/
├── app.py                 # Main Flask application
├── run_local.py          # Local development runner
├── requirements.txt       # Python dependencies
├── src/
│   ├── hybrid_summarizer.py    # Main summarization logic
│   ├── roberta_extractive.py   # Extractive summarization
│   └── t5_abstractive.py       # Abstractive summarization
├── utils/
│   ├── pdf_processor.py        # PDF text extraction
│   └── preprocessing.py        # Text preprocessing
└── uploads/              # Temporary file storage
```

### Adding New Features
1. Modify the relevant module in `src/` or `utils/`
2. Update the web interface in `app.py`
3. Test with `python test_upload_functionality.py`
4. Update documentation

## Performance Tips

- **For speed**: Use 'fast' quality mode
- **For accuracy**: Use 'high' quality mode
- **For large documents**: The system automatically chunks and processes efficiently
- **Caching**: Repeated requests with same content are served instantly

## Support

If you encounter issues:
1. Check the terminal logs for error messages
2. Ensure all dependencies are installed
3. Verify system requirements are met
4. Try restarting the application

The application is now ready for local development and testing! 🎉