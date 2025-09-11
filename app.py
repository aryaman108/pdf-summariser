from flask import Flask, request, render_template_string, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from src.hybrid_summarizer import HybridSummarizer
from src.evaluation import SummarizationEvaluator
from utils.preprocessing import clean_text
from utils.pdf_processor import PDFProcessor
import time
import os
import traceback

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'intelligent-document-agent-key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'txt'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize components
pdf_processor = PDFProcessor()

# Simple in-memory cache for summaries (LRU with max 10 entries)
summary_cache = {}
MAX_CACHE_SIZE = 10

def get_cache_key(text, quality_mode):
    """Generate cache key from text content and parameters"""
    import hashlib
    content = f"{text[:1000]}{quality_mode}".encode('utf-8')  # Use first 1000 chars + quality mode
    return hashlib.md5(content).hexdigest()

def get_cached_summary(cache_key):
    """Get summary from cache if available"""
    if cache_key in summary_cache:
        return summary_cache[cache_key]
    return None

def set_cached_summary(cache_key, summary_data):
    """Store summary in cache"""
    if len(summary_cache) >= MAX_CACHE_SIZE:
        # Remove oldest entry (simple FIFO)
        oldest_key = next(iter(summary_cache))
        del summary_cache[oldest_key]
    summary_cache[cache_key] = summary_data

# Global summarizer instance - use module-level access
_summarizer = None

def get_summarizer():
    """Get or create summarizer instance"""
    global _summarizer
    if _summarizer is None:
        try:
            from src.hybrid_summarizer import HybridSummarizer
            _summarizer = HybridSummarizer()
            print("[SUCCESS] Models loaded successfully!")
        except Exception as e:
            print(f"[WARNING] Could not load models: {e}")
            raise
    return _summarizer

# Skip loading models at startup to speed up app launch
print("Intelligent Document Agent - Initializing...")
print("Models will be loaded on first request to speed up startup")

print("System ready at: http://localhost:5000")
print("Web Interface: http://localhost:5000")
print("API Endpoint: http://localhost:5000/api/summarize")
print("")
print("Expected performance:")
print("   - First request: 15-30 seconds (models loading)")
print("   - Subsequent requests: 3-10 seconds")
print("   - Cached requests: < 1 second")
print("   - Long documents: 10-25 seconds")
print("")
print("Ready to accept PDF uploads and text summarization requests!")

# Ensure NLTK data is available
try:
    import nltk
    import ssl
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context

    # Set up NLTK data path
    nltk_data_dir = os.path.join(os.path.dirname(__file__), 'nltk_data')
    if not os.path.exists(nltk_data_dir):
        os.makedirs(nltk_data_dir)
    nltk.data.path.insert(0, nltk_data_dir)

    # Download required NLTK data
    required_packages = ['punkt', 'punkt_tab', 'stopwords', 'wordnet']
    for package in required_packages:
        try:
            nltk.download(package, quiet=True, force=False)
        except Exception as e:
            print(f"Warning: Could not download {package}: {e}")

    print("NLTK data setup completed")
except Exception as e:
    print(f"Warning: NLTK setup issue: {e}")
    # Fallback: try to use system NLTK data
    try:
        import nltk
        nltk.data.path.append(nltk.data.find('.'))
    except:
        print("NLTK fallback setup failed")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def process_uploaded_file(file):
    """Process uploaded file and extract text"""
    if file.filename == '':
        return None, "No file selected"

    if not allowed_file(file.filename):
        return None, "File type not allowed. Please upload PDF or TXT files."

    file_handle = None
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # Save the uploaded file
        file.save(filepath)

        # Process based on file type
        if filename.lower().endswith('.pdf'):
            # Open file for PDF processing
            file_handle = open(filepath, 'rb')
            text = pdf_processor.extract_text_from_pdf(file_handle)
            file_handle.close()
            file_handle = None

            # Get metadata
            metadata_handle = open(filepath, 'rb')
            metadata = pdf_processor.get_pdf_metadata(metadata_handle)
            metadata_handle.close()
        else:  # TXT file
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            metadata = {
                'title': filename,
                'author': 'Unknown',
                'pages': 1,
                'size': os.path.getsize(filepath)
            }

        # Clean up uploaded file with retry mechanism
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                break
            except OSError as e:
                if attempt == max_retries - 1:
                    print(f"Warning: Could not delete uploaded file {filepath}: {e}")
                else:
                    import time
                    time.sleep(0.1)  # Wait a bit before retrying

        if not text.strip():
            return None, "No readable text found in the file"

        return text, metadata

    except Exception as e:
        # Ensure file handle is closed if still open
        if file_handle:
            try:
                file_handle.close()
            except:
                pass

        # Clean up file if it exists
        try:
            if 'filepath' in locals() and os.path.exists(filepath):
                os.remove(filepath)
        except:
            pass

        return None, f"Error processing file: {str(e)}"

# Enhanced HTML template with modern UI design
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Intelligent Document Agent - Hybrid Summarizer</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { box-sizing: border-box; }
        html {
            scroll-behavior: smooth;
        }
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            background-attachment: fixed;
            min-height: 100vh;
            color: #1e293b;
            line-height: 1.6;
            position: relative;
            overflow-x: hidden;
        }

        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background:
                radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(120, 219, 226, 0.2) 0%, transparent 50%);
            pointer-events: none;
            z-index: -1;
        }

        .container {
            max-width: 1300px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.98);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
            overflow: hidden;
            margin-top: 25px;
            margin-bottom: 25px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            animation: containerSlideIn 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }

        @keyframes containerSlideIn {
            from {
                opacity: 0;
                transform: translateY(30px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }

        .header {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #ec4899 100%);
            color: white;
            padding: 50px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }

        .header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="25" cy="25" r="1" fill="white" opacity="0.1"/><circle cx="75" cy="75" r="1" fill="white" opacity="0.1"/><circle cx="50" cy="10" r="0.5" fill="white" opacity="0.15"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
            opacity: 0.3;
        }

        .header h1 {
            margin: 0;
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 15px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: relative;
            z-index: 1;
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 50%, #e2e8f0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: titleGlow 3s ease-in-out infinite alternate;
        }

        @keyframes titleGlow {
            from { filter: brightness(1); }
            to { filter: brightness(1.1); }
        }

        .header p {
            margin: 0;
            opacity: 0.95;
            font-size: 1.2rem;
            font-weight: 400;
            position: relative;
            z-index: 1;
        }

        .content {
            padding: 40px;
            position: relative;
        }

        .agent-info {
            background: linear-gradient(135deg, #e0f2fe 0%, #f3e8ff 50%, #fce7f3 100%);
            padding: 25px;
            border-radius: 16px;
            margin-bottom: 35px;
            border: 1px solid rgba(79, 70, 229, 0.1);
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.08);
            position: relative;
            overflow: hidden;
        }

        .agent-info::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
        }

        .agent-info h3 {
            margin: 0 0 18px 0;
            color: #1e293b;
            font-size: 1.4rem;
            font-weight: 700;
            position: relative;
        }

        .agent-info p {
            margin: 8px 0;
            color: #475569;
            font-size: 1rem;
            font-weight: 500;
        }

        .system-status {
            background: linear-gradient(135deg, #dcfce7 0%, #ecfdf5 100%);
            padding: 20px 25px;
            border-radius: 16px;
            margin-bottom: 35px;
            border: 1px solid #bbf7d0;
            box-shadow: 0 4px 15px rgba(34, 197, 94, 0.08);
        }

        .system-status h4 {
            margin: 0 0 10px 0;
            color: #166534;
            font-size: 1.1rem;
            font-weight: 700;
        }

        .system-status p {
            margin: 0;
            color: #166534;
            font-size: 0.95rem;
            font-weight: 500;
        }

        .tabs {
            display: flex;
            margin-bottom: 35px;
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border-radius: 16px;
            padding: 8px;
            gap: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }

        .tab {
            flex: 1;
            padding: 16px 24px;
            background: transparent;
            border: none;
            cursor: pointer;
            border-radius: 12px;
            font-weight: 600;
            color: #64748b;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            font-size: 1rem;
            position: relative;
            overflow: hidden;
        }

        .tab::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
            transition: left 0.6s;
        }

        .tab:hover::before {
            left: 100%;
        }

        .tab:hover {
            background: rgba(255,255,255,0.6);
            transform: translateY(-2px);
        }

        .tab.active {
            background: white;
            color: #1e293b;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            font-weight: 700;
            transform: translateY(-2px);
        }

        .tab-content {
            display: none;
            animation: fadeIn 0.5s ease-in-out;
        }

        .tab-content.active { display: block; }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .form-group {
            margin-bottom: 25px;
            position: relative;
        }

        .form-group label {
            display: block;
            margin-bottom: 12px;
            font-weight: 600;
            color: #374151;
            font-size: 1.1rem;
        }

        textarea {
            width: 100%;
            height: 220px;
            padding: 20px;
            border: 2px solid #e5e7eb;
            border-radius: 16px;
            font-family: inherit;
            font-size: 1rem;
            resize: vertical;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(10px);
        }

        textarea:focus {
            outline: none;
            border-color: #4f46e5;
            box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.15), 0 8px 25px rgba(79, 70, 229, 0.1);
            background: white;
            transform: translateY(-2px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        textarea:focus::placeholder {
            color: #9ca3af;
            transform: translateX(5px);
            transition: all 0.3s ease;
        }

        textarea::placeholder {
            color: #9ca3af;
            font-style: italic;
        }

        .quality-options {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            padding: 25px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            margin: 25px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        }

        .quality-options label {
            margin-bottom: 15px;
            display: block;
            font-weight: 700;
            color: #1e293b;
            font-size: 1.1rem;
        }

        .radio-group {
            display: flex;
            gap: 25px;
            flex-wrap: wrap;
        }

        .radio-option {
            display: flex;
            align-items: center;
            gap: 10px;
            cursor: pointer;
            padding: 12px 18px;
            border-radius: 12px;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.6);
            border: 2px solid transparent;
        }

        .radio-option:hover {
            background: white;
            border-color: #4f46e5;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.1);
        }

        .radio-option input[type="radio"] {
            width: 20px;
            height: 20px;
            accent-color: #4f46e5;
            transform: scale(1);
            transition: transform 0.2s ease;
        }

        .radio-option input[type="radio"]:checked {
            transform: scale(1.1);
        }

        .radio-option input[type="radio"]:focus {
            outline: 2px solid #4f46e5;
            outline-offset: 2px;
        }

        .radio-option label {
            font-weight: 500;
            color: #374151;
            cursor: pointer;
        }

        .btn {
            padding: 16px 32px;
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #ec4899 100%);
            color: white;
            border: none;
            border-radius: 16px;
            cursor: pointer;
            font-weight: 700;
            font-size: 1.1rem;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            display: inline-flex;
            align-items: center;
            gap: 10px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.2);
        }

        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
            transition: left 0.6s;
        }

        .btn:hover::before {
            left: 100%;
        }

        .btn:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 12px 40px rgba(79, 70, 229, 0.4);
        }

        .btn:active {
            transform: translateY(-1px) scale(0.98);
            transition: all 0.1s ease;
        }

        .btn::after {
            content: '';
            position: absolute;
            top: 50%;
            left: 50%;
            width: 0;
            height: 0;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.3);
            transform: translate(-50%, -50%);
            transition: width 0.6s, height 0.6s;
        }

        .btn:active::after {
            width: 300px;
            height: 300px;
        }

        .btn:disabled {
            background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
            cursor: not-allowed;
            transform: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .upload-section {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            padding: 30px;
            border-radius: 16px;
            border: 2px dashed #cbd5e1;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .upload-section:hover {
            border-color: #4f46e5;
            background: linear-gradient(135deg, #f0f4ff 0%, #e8f2ff 100%);
        }

        .upload-section h3 {
            margin: 0 0 12px 0;
            color: #1e293b;
            font-size: 1.3rem;
            font-weight: 700;
        }

        .upload-section p {
            margin: 0 0 25px 0;
            color: #64748b;
            font-size: 1rem;
        }

        .file-input {
            margin: 25px 0;
        }

        .file-input input[type="file"] {
            display: none;
        }

        .file-input label {
            display: inline-block;
            padding: 15px 25px;
            background: linear-gradient(135deg, #e2e8f0 0%, #f1f5f9 100%);
            color: #475569;
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-weight: 600;
            border: 2px solid transparent;
        }

        .file-input label:hover {
            background: linear-gradient(135deg, #cbd5e1 0%, #e2e8f0 100%);
            border-color: #4f46e5;
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.1);
        }

        .output {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 50%, #e8f4fd 100%);
            padding: 30px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            margin-top: 35px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            position: relative;
            overflow: hidden;
        }

        .output::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(135deg, #4f46e5, #7c3aed, #ec4899);
        }

        .output h3 {
            margin: 0 0 25px 0;
            color: #1e293b;
            font-size: 1.6rem;
            font-weight: 700;
        }

        .output p {
            margin: 12px 0;
            color: #475569;
            line-height: 1.7;
            font-size: 1rem;
        }

        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-top: 25px;
        }

        .metric {
            background: white;
            padding: 25px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .metric::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
        }

        .metric:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }

        .metric strong {
            color: #4f46e5;
            font-size: 1.2rem;
            font-weight: 700;
            display: block;
            margin-bottom: 8px;
        }

        .metric p {
            margin: 0;
            color: #1e293b;
            font-size: 1.8rem;
            font-weight: 800;
            line-height: 1.2;
        }

        .error {
            background: linear-gradient(135deg, #fef2f2 0%, #fef2f2 100%);
            color: #dc2626;
            padding: 20px 25px;
            border-radius: 16px;
            border: 1px solid #fecaca;
            margin-top: 25px;
            box-shadow: 0 4px 15px rgba(220, 38, 38, 0.08);
        }

        .file-info {
            background: linear-gradient(135deg, #dcfce7 0%, #ecfdf5 100%);
            padding: 20px 25px;
            border-radius: 16px;
            border: 1px solid #bbf7d0;
            margin-bottom: 25px;
            box-shadow: 0 4px 15px rgba(34, 197, 94, 0.08);
        }

        .file-info h4 {
            margin: 0 0 12px 0;
            color: #166534;
            font-size: 1.1rem;
            font-weight: 700;
        }

        .file-info p {
            margin: 6px 0;
            color: #166534;
            font-weight: 500;
        }

        .loading-indicator {
            background: linear-gradient(135deg, #e0f2fe 0%, #f3e8ff 50%, #fce7f3 100%);
            padding: 25px;
            border-radius: 16px;
            text-align: center;
            border: 1px solid #bae6fd;
            margin: 25px 0;
            box-shadow: 0 4px 15px rgba(79, 70, 229, 0.08);
        }

        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 25px;
            margin: 35px 0;
        }

        .feature-card {
            background: white;
            padding: 30px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .feature-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(135deg, #4f46e5, #7c3aed, #ec4899);
        }

        .feature-card:hover {
            transform: translateY(-8px) rotate(1deg) scale(1.02);
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
        }

        .feature-card::after {
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(135deg, #4f46e5, #7c3aed, #ec4899);
            border-radius: 18px;
            z-index: -1;
            opacity: 0;
            transition: opacity 0.4s ease;
        }

        .feature-card:hover::after {
            opacity: 0.3;
        }

        .feature-card h4 {
            margin: 0 0 18px 0;
            color: #1e293b;
            font-size: 1.2rem;
            font-weight: 700;
        }

        .feature-card ul {
            margin: 0;
            padding-left: 22px;
        }

        .feature-card li {
            margin: 10px 0;
            color: #64748b;
            font-size: 0.95rem;
            line-height: 1.5;
        }

        @media (max-width: 768px) {
            .container {
                margin: 15px;
                border-radius: 16px;
            }
            .header {
                padding: 35px 25px;
            }
            .header h1 {
                font-size: 2.2rem;
            }
            .content {
                padding: 25px;
            }
            .tabs {
                flex-direction: column;
                gap: 6px;
            }
            .radio-group {
                flex-direction: column;
                gap: 15px;
            }
            .metrics {
                grid-template-columns: 1fr;
                gap: 15px;
            }
            .feature-grid {
                grid-template-columns: 1fr;
                gap: 20px;
            }
        }

        @media (max-width: 480px) {
            .header h1 {
                font-size: 1.8rem;
            }
            .content {
                padding: 20px;
            }
            .btn {
                padding: 14px 24px;
                font-size: 1rem;
            }
        }
    </style>
    <script>
        function switchTab(tabName) {
            // Hide all tab contents
            const contents = document.querySelectorAll('.tab-content');
            contents.forEach(content => content.classList.remove('active'));

            // Remove active class from all tabs
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => tab.classList.remove('active'));

            // Show selected tab content
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }

        function showProcessing() {
            const submitBtn = document.querySelector('input[type="submit"]:not([disabled])');
            if (submitBtn) {
                submitBtn.innerHTML = '<span class="spinner"></span> Processing...';
                submitBtn.disabled = true;
            }

            // Show loading indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.id = 'loading-indicator';
            loadingDiv.className = 'loading-indicator';
            loadingDiv.innerHTML = `
                <div style="display: flex; align-items: center; justify-content: center; gap: 15px;">
                    <div class="spinner" style="width: 24px; height: 24px; border: 3px solid #e0e7ff; border-top: 3px solid #4f46e5; border-radius: 50%; animation: spin 1s linear infinite;"></div>
                    <div>
                        <strong style="color: #1e293b;">Agent is analyzing your document...</strong>
                        <p style="margin: 5px 0 0 0; color: #64748b; font-size: 0.9rem;">This may take 10-30 seconds for the first request as models load.</p>
                    </div>
                </div>
            `;

            const content = document.querySelector('.content');
            const output = document.querySelector('.output');
            if (output) {
                content.insertBefore(loadingDiv, output);
            } else {
                content.appendChild(loadingDiv);
            }
        }

        function hideProcessing() {
            const submitBtn = document.querySelector('input[type="submit"]:disabled');
            if (submitBtn) {
                submitBtn.innerHTML = 'Generate Summary';
                submitBtn.disabled = false;
            }

            // Hide loading indicator
            const loadingDiv = document.getElementById('loading-indicator');
            if (loadingDiv) {
                loadingDiv.remove();
            }
        }

        // Auto-hide loading on page load (for form resubmission)
        window.addEventListener('load', function() {
            hideProcessing();
        });

        // Add CSS animation for spinner
        const style = document.createElement('style');
        style.textContent = `
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .spinner {
                animation: spin 1s linear infinite;
                filter: drop-shadow(0 2px 4px rgba(79, 70, 229, 0.3));
            }

            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.1); }
            }

            .loading-indicator {
                animation: pulse 2s ease-in-out infinite;
            }
        `;
        document.head.appendChild(style);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Intelligent Document Agent</h1>
            <p>Advanced Hybrid Text Summarization Powered by RoBERTa & T5</p>
        </div>
        <div class="content">
            <div class="agent-info">
                <h3>Agentic Framework: Perception → Planning → Action</h3>
                <p><strong>Perception:</strong> Analyzes document structure and preprocesses content</p>
                <p><strong>Planning:</strong> Determines optimal chunking strategy based on document length</p>
                <p><strong>Action:</strong> Executes hybrid extractive-abstractive summarization with constrained decoding</p>
            </div>

            <div class="system-status">
                <h4>System Status: Ready</h4>
                <p>Models loaded and optimized for your hardware. First request may take 15-30 seconds, subsequent requests 5-15 seconds.</p>
            </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('text-tab')">Text Input</button>
            <button class="tab" onclick="switchTab('file-tab')">File Upload</button>
            <button class="tab" onclick="switchTab('advanced-tab')">Advanced Options</button>
        </div>

            <div id="text-tab" class="tab-content active">
                <form method="post" onsubmit="showProcessing()">
                    <div class="form-group">
                        <label for="text-input">Enter educational text to summarize:</label>
                        <textarea name="text" id="text-input" placeholder="Paste your educational content here (notes, PDFs, research papers, etc.)">{{ text if text else '' }}</textarea>
                    </div>

                    <div class="quality-options">
                        <label>Quality Mode:</label>
                        <div class="radio-group">
                            <div class="radio-option">
                                <input type="radio" name="quality_mode" value="fast" id="fast">
                                <label for="fast">Fast (quick results)</label>
                            </div>
                            <div class="radio-option">
                                <input type="radio" name="quality_mode" value="balanced" id="balanced" checked>
                                <label for="balanced">Balanced (recommended)</label>
                            </div>
                            <div class="radio-option">
                                <input type="radio" name="quality_mode" value="high" id="high">
                                <label for="high">High Quality (best accuracy)</label>
                            </div>
                        </div>
                    </div>

                    <button type="submit" class="btn">Generate Summary</button>
                </form>
            </div>

            <div id="file-tab" class="tab-content">
                <div class="upload-section">
                    <h3>Upload Document</h3>
                    <p>Upload PDF or TXT files for automatic summarization</p>
                    <form method="post" enctype="multipart/form-data" onsubmit="showProcessing()">
                        <div class="file-input">
                            <input type="file" name="file" id="file" accept=".pdf,.txt" required>
                            <label for="file">Choose file to upload</label>
                        </div>

                        <div class="quality-options">
                            <label>Quality Mode:</label>
                            <div class="radio-group">
                                <div class="radio-option">
                                    <input type="radio" name="quality_mode" value="fast" id="file_fast">
                                    <label for="file_fast">Fast</label>
                                </div>
                                <div class="radio-option">
                                    <input type="radio" name="quality_mode" value="balanced" id="file_balanced" checked>
                                    <label for="file_balanced">Balanced</label>
                                </div>
                                <div class="radio-option">
                                    <input type="radio" name="quality_mode" value="high" id="file_high">
                                    <label for="file_high">High Quality</label>
                                </div>
                            </div>
                        </div>

                        <button type="submit" class="btn">Upload & Summarize</button>
                    </form>
                    <p style="margin: 15px 0 0 0; font-size: 0.9rem; color: #64748b;">
                        Maximum file size: 50MB. Supported formats: PDF, TXT
                    </p>
                </div>
            </div>

        <div id="advanced-tab" class="tab-content">
            <div class="advanced-section">
                <h3>Advanced Summarization Options</h3>

                <div class="feature-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">
                    <div class="feature-card" style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
                        <h4>Quality Modes</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><strong>Fast:</strong> Quick results, basic accuracy</li>
                            <li><strong>Balanced:</strong> Optimal quality-speed ratio</li>
                            <li><strong>High:</strong> Maximum accuracy, slower processing</li>
                        </ul>
                    </div>

                    <div class="feature-card" style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
                        <h4>Agentic Features</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>Content type detection</li>
                            <li>Complexity analysis</li>
                            <li>Topic extraction</li>
                            <li>Adaptive processing</li>
                        </ul>
                    </div>

                    <div class="feature-card" style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
                        <h4>Quality Metrics</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>ROUGE, METEOR, BLEU scores</li>
                            <li>Factual consistency</li>
                            <li>Readability analysis</li>
                            <li>Semantic coherence</li>
                        </ul>
                    </div>

                    <div class="feature-card" style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
                        <h4>Document Support</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>PDF text extraction</li>
                            <li>OCR error correction</li>
                            <li>Long document chunking</li>
                            <li>Hierarchical summarization</li>
                        </ul>
                    </div>
                </div>

                <div class="performance-info" style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4>Performance Characteristics</h4>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div>
                            <strong>Short Documents (< 1K words):</strong><br>
                            3-8 seconds processing
                        </div>
                        <div>
                            <strong>Medium Documents (1K-5K words):</strong><br>
                            8-15 seconds processing
                        </div>
                        <div>
                            <strong>Long Documents (5K+ words):</strong><br>
                            15-30 seconds processing
                        </div>
                    </div>
                </div>

                <div class="api-info" style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4>API Access</h4>
                    <p><strong>REST Endpoint:</strong> <code>POST /api/summarize</code></p>
                    <p><strong>Web Interface:</strong> <code>http://localhost:4500</code></p>
                    <p><strong>Parameters:</strong> text, quality_mode, file (for uploads)</p>
                </div>
            </div>
        </div>

            {% if file_info %}
            <div class="file-info">
                <h4>File Processed Successfully</h4>
                <p><strong>Title:</strong> {{ file_info.title }}</p>
                <p><strong>Author:</strong> {{ file_info.author }}</p>
                <p><strong>Pages:</strong> {{ file_info.pages }}</p>
                <p><strong>Size:</strong> {{ file_info.size }} bytes</p>
            </div>
            {% endif %}

            {% if summary %}
            <div class="output">
                <h3>Summarization Results</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
                        <strong style="color: #4f46e5;">Original Length:</strong>
                        <p style="margin: 5px 0 0 0; font-size: 1.2rem; font-weight: 600;">{{ original_length }} chars</p>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
                        <strong style="color: #4f46e5;">Summary Length:</strong>
                        <p style="margin: 5px 0 0 0; font-size: 1.2rem; font-weight: 600;">{{ summary_length }} chars</p>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
                        <strong style="color: #4f46e5;">Compression Ratio:</strong>
                        <p style="margin: 5px 0 0 0; font-size: 1.2rem; font-weight: 600;">{{ "%.2f"|format(compression_ratio) }}</p>
                    </div>
                </div>

                <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
                    <strong style="color: #4f46e5; display: block; margin-bottom: 10px;">Generated Summary:</strong>
                    <p style="margin: 0; line-height: 1.6; color: #374151;">{{ summary }}</p>
                </div>

                {% if evaluation %}
                <h4 style="color: #1e293b; margin-bottom: 15px;">Quality Metrics</h4>
                <div class="metrics">
                    <div class="metric">
                        <strong>ROUGE-1 F1</strong>
                        <p>{{ "%.3f"|format(evaluation.rouge1_f) }}</p>
                    </div>
                    <div class="metric">
                        <strong>ROUGE-2 F1</strong>
                        <p>{{ "%.3f"|format(evaluation.rouge2_f) }}</p>
                    </div>
                    <div class="metric">
                        <strong>ROUGE-L F1</strong>
                        <p>{{ "%.3f"|format(evaluation.rougeL_f) }}</p>
                    </div>
                    <div class="metric">
                        <strong>METEOR</strong>
                        <p>{{ "%.3f"|format(evaluation.meteor) }}</p>
                    </div>
                    <div class="metric">
                        <strong>Factual Consistency</strong>
                        <p>{{ "%.3f"|format(evaluation.factual_consistency_score) }}</p>
                    </div>
                    <div class="metric">
                        <strong>Hallucination Rate</strong>
                        <p>{{ "%.3f"|format(evaluation.hallucination_rate) }}</p>
                    </div>
                </div>
                {% endif %}
            </div>
            {% endif %}

            {% if error %}
            <div class="error">
                <strong>Error:</strong> {{ error }}
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    text = ''
    summary = None
    original_length = 0
    summary_length = 0
    compression_ratio = 0
    evaluation = None
    error = None
    file_info = None

    if request.method == 'POST':
        # Check if file was uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                text, metadata = process_uploaded_file(file)
                if text:
                    file_info = metadata
                else:
                    error = metadata  # metadata contains error message
                    text = ''
        else:
            # Text input
            text = request.form.get('text', '')

        if text and not error:
            try:
                start_time = time.time()

                # Get quality mode from form data
                quality_mode = request.form.get('quality_mode', 'balanced')

                # Check cache first
                cache_key = get_cache_key(text, quality_mode)
                cached_result = get_cached_summary(cache_key)

                if cached_result:
                    print(f"Cache hit! Returning cached summary for {len(text)} characters...")
                    summary = cached_result['summary']
                    original_length = cached_result['original_length']
                    summary_length = cached_result['summary_length']
                    compression_ratio = cached_result['compression_ratio']
                    evaluation = cached_result.get('evaluation')
                    processing_time = time.time() - start_time
                    print(f"Cached result returned in {processing_time:.2f} seconds")
                else:
                    print(f"Starting summarization for {len(text)} characters...")
                    print(f"Quality mode: {quality_mode}")

                    # Get or create summarizer instance
                    try:
                        current_summarizer = get_summarizer()
                    except Exception as e:
                        error = f"Failed to initialize summarizer: {str(e)}"
                        return render_template_string(HTML_TEMPLATE,
                                                    text=text,
                                                    summary=None,
                                                    original_length=0,
                                                    summary_length=0,
                                                    compression_ratio=0,
                                                    evaluation=None,
                                                    error=error,
                                                    file_info=file_info)

                    try:
                        evaluator = SummarizationEvaluator()
                    except Exception as e:
                        print(f"Warning: Could not initialize evaluator: {e}")
                        evaluator = None

                    # Generate summary with quality mode and verbose logging (Unicode-safe)
                    summary_result = current_summarizer.summarize(text, verbose=True, quality_mode=quality_mode)
                    if isinstance(summary_result, tuple):
                        summary, agent_log = summary_result
                        print("Agent Activity Log:")
                        for log_entry in agent_log:
                            # Safe Unicode handling for Windows console
                            try:
                                print(f"  {log_entry}")
                            except UnicodeEncodeError:
                                # Fallback to ASCII-only output
                                safe_log = log_entry.encode('ascii', 'ignore').decode('ascii')
                                print(f"  {safe_log}")
                    else:
                        summary = summary_result

                    # Calculate metrics
                    original_length = len(text)
                    summary_length = len(summary)
                    compression_ratio = summary_length / original_length if original_length > 0 else 0

                    # Basic evaluation (using original text as reference for demonstration)
                    # In practice, you'd have human-written reference summaries
                    if evaluator:
                        evaluation_results = evaluator.evaluate_summary(
                            summary,
                            text[:500],  # Simplified: using first 500 chars as reference
                            text,
                            []  # Keywords would be extracted during summarization
                        )
                        evaluation = evaluation_results

                    processing_time = time.time() - start_time
                    print(f"Summarization completed in {processing_time:.2f} seconds")
                    print(f"Compression ratio: {compression_ratio:.3f}")

                    # Cache the result for future use
                    summary_data = {
                        'summary': summary,
                        'original_length': original_length,
                        'summary_length': summary_length,
                        'compression_ratio': compression_ratio,
                        'evaluation': evaluation,
                        'timestamp': time.time()
                    }
                    set_cached_summary(cache_key, summary_data)
                    print("Result cached for future requests")

            except Exception as e:
                error = f"Summarization failed: {str(e)}"
                print(f"Error during summarization: {e}")
                print(f"Full traceback: {traceback.format_exc()}")

    return render_template_string(HTML_TEMPLATE,
                                text=text,
                                summary=summary,
                                original_length=original_length,
                                summary_length=summary_length,
                                compression_ratio=compression_ratio,
                                evaluation=evaluation,
                                error=error,
                                file_info=file_info)

@app.route('/api/summarize', methods=['POST'])
def api_summarize():
    """REST API endpoint for summarization"""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400

    try:
        summarizer = get_summarizer()
        quality_mode = data.get('quality_mode', 'balanced')
        summary = summarizer.summarize(data['text'], quality_mode=quality_mode)

        return jsonify({
            'summary': summary,
            'original_length': len(data['text']),
            'summary_length': len(summary),
            'compression_ratio': len(summary) / len(data['text']) if data['text'] else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use environment variables for production deployment
    import os
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'

    app.run(host=host, port=port, debug=debug)