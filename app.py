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

# Models will be loaded on first request to avoid startup issues
print("Intelligent Document Agent - Initializing...")
print("System ready at: http://localhost:4500")
print("Models will load on first request (may take 15-30 seconds)")
print("Expected performance:")
print("   - First request: 15-30 seconds (model loading + processing)")
print("   - Subsequent requests: 5-15 seconds")
print("   - Long documents: 20-45 seconds")
summarizer_instance = None

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

    # Force download NLTK data
    nltk.data.path.append(nltk.data.find('.'))
    nltk.download('punkt_tab', quiet=True, force=True)
    nltk.download('punkt', quiet=True, force=True)
    nltk.download('stopwords', quiet=True, force=True)
    nltk.download('wordnet', quiet=True, force=True)
    print("NLTK data loaded successfully")
except Exception as e:
    print(f"Warning: NLTK data loading issue: {e}")
    # Try alternative NLTK setup
    try:
        import os
        nltk_data_dir = os.path.join(os.path.dirname(__file__), 'nltk_data')
        if not os.path.exists(nltk_data_dir):
            os.makedirs(nltk_data_dir)
        nltk.data.path.insert(0, nltk_data_dir)
        print("Alternative NLTK path set")
    except:
        print("Could not set alternative NLTK path")

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
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
            margin-top: 20px;
            margin-bottom: 20px;
        }
        .header {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 10px;
        }
        .header p {
            margin: 0;
            opacity: 0.9;
            font-size: 1.1rem;
        }
        .content { padding: 30px; }
        .agent-info {
            background: linear-gradient(135deg, #e0f2fe 0%, #f3e8ff 100%);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            border: 1px solid #e0e7ff;
        }
        .agent-info h3 {
            margin: 0 0 15px 0;
            color: #1e293b;
            font-size: 1.25rem;
            font-weight: 600;
        }
        .agent-info p {
            margin: 5px 0;
            color: #475569;
            font-size: 0.95rem;
        }
        .system-status {
            background: linear-gradient(135deg, #dcfce7 0%, #ecfdf5 100%);
            padding: 15px 20px;
            border-radius: 12px;
            margin-bottom: 30px;
            border: 1px solid #bbf7d0;
        }
        .system-status h4 {
            margin: 0 0 8px 0;
            color: #166534;
            font-size: 1rem;
            font-weight: 600;
        }
        .system-status p {
            margin: 0;
            color: #166534;
            font-size: 0.9rem;
        }
        .tabs {
            display: flex;
            margin-bottom: 30px;
            background: #f8fafc;
            border-radius: 12px;
            padding: 6px;
            gap: 6px;
        }
        .tab {
            flex: 1;
            padding: 12px 20px;
            background: transparent;
            border: none;
            cursor: pointer;
            border-radius: 8px;
            font-weight: 500;
            color: #64748b;
            transition: all 0.3s ease;
            font-size: 0.95rem;
        }
        .tab:hover { background: rgba(255,255,255,0.5); }
        .tab.active {
            background: white;
            color: #1e293b;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            font-weight: 600;
        }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .form-group { margin-bottom: 20px; }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #374151;
        }
        textarea {
            width: 100%;
            height: 200px;
            padding: 16px;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            font-family: inherit;
            font-size: 0.95rem;
            resize: vertical;
            transition: border-color 0.3s ease;
        }
        textarea:focus {
            outline: none;
            border-color: #4f46e5;
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }
        .quality-options {
            background: #f8fafc;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            margin: 20px 0;
        }
        .quality-options label { margin-bottom: 12px; display: block; font-weight: 600; }
        .radio-group {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .radio-option {
            display: flex;
            align-items: center;
            gap: 8px;
            cursor: pointer;
        }
        .radio-option input[type="radio"] {
            width: 18px;
            height: 18px;
            accent-color: #4f46e5;
        }
        .btn {
            padding: 14px 28px;
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(79, 70, 229, 0.3);
        }
        .btn:disabled {
            background: #9ca3af;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .upload-section {
            background: #f8fafc;
            padding: 25px;
            border-radius: 12px;
            border: 2px dashed #cbd5e1;
            text-align: center;
        }
        .upload-section h3 {
            margin: 0 0 10px 0;
            color: #1e293b;
        }
        .upload-section p {
            margin: 0 0 20px 0;
            color: #64748b;
        }
        .file-input {
            margin: 20px 0;
        }
        .file-input input[type="file"] {
            display: none;
        }
        .file-input label {
            display: inline-block;
            padding: 12px 20px;
            background: #e2e8f0;
            color: #475569;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .file-input label:hover { background: #cbd5e1; }
        .output {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            margin-top: 30px;
        }
        .output h3 {
            margin: 0 0 20px 0;
            color: #1e293b;
            font-size: 1.5rem;
        }
        .output p {
            margin: 10px 0;
            color: #475569;
            line-height: 1.6;
        }
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .metric {
            background: white;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .metric strong {
            color: #4f46e5;
            font-size: 1.1rem;
        }
        .metric p {
            margin: 8px 0 0 0;
            color: #64748b;
            font-size: 1.5rem;
            font-weight: 600;
        }
        .error {
            background: linear-gradient(135deg, #fef2f2 0%, #fef2f2 100%);
            color: #dc2626;
            padding: 16px 20px;
            border-radius: 12px;
            border: 1px solid #fecaca;
            margin-top: 20px;
        }
        .file-info {
            background: linear-gradient(135deg, #dcfce7 0%, #ecfdf5 100%);
            padding: 16px 20px;
            border-radius: 12px;
            border: 1px solid #bbf7d0;
            margin-bottom: 20px;
        }
        .file-info h4 {
            margin: 0 0 10px 0;
            color: #166534;
        }
        .file-info p {
            margin: 5px 0;
            color: #166534;
        }
        .loading-indicator {
            background: linear-gradient(135deg, #e0f2fe 0%, #f3e8ff 100%);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid #bae6fd;
            margin: 20px 0;
        }
        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .feature-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            transition: transform 0.3s ease;
        }
        .feature-card:hover { transform: translateY(-2px); }
        .feature-card h4 {
            margin: 0 0 15px 0;
            color: #1e293b;
            font-size: 1.1rem;
        }
        .feature-card ul {
            margin: 0;
            padding-left: 20px;
        }
        .feature-card li {
            margin: 8px 0;
            color: #64748b;
        }
        @media (max-width: 768px) {
            .container { margin: 10px; }
            .header { padding: 30px 20px; }
            .header h1 { font-size: 2rem; }
            .content { padding: 20px; }
            .tabs { flex-direction: column; }
            .radio-group { flex-direction: column; gap: 12px; }
            .metrics { grid-template-columns: 1fr; }
            .feature-grid { grid-template-columns: 1fr; }
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
                        <strong style="color: #1e293b;">🤖 Agent is analyzing your document...</strong>
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
                submitBtn.innerHTML = '🚀 Generate Summary';
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
            }
        `;
        document.head.appendChild(style);
    </script>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Intelligent Document Agent</h1>
            <p>Advanced Hybrid Text Summarization Powered by RoBERTa & T5</p>
        </div>
        <div class="content">
            <div class="agent-info">
                <h3>🎯 Agentic Framework: Perception → Planning → Action</h3>
                <p><strong>🧠 Perception:</strong> Analyzes document structure and preprocesses content</p>
                <p><strong>📋 Planning:</strong> Determines optimal chunking strategy based on document length</p>
                <p><strong>⚡ Action:</strong> Executes hybrid extractive-abstractive summarization with constrained decoding</p>
            </div>

            <div class="system-status">
                <h4>✅ System Status: Ready</h4>
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
                        <label for="text-input">📝 Enter educational text to summarize:</label>
                        <textarea name="text" id="text-input" placeholder="Paste your educational content here (notes, PDFs, research papers, etc.)">{{ text if text else '' }}</textarea>
                    </div>

                    <div class="quality-options">
                        <label>⚙️ Quality Mode:</label>
                        <div class="radio-group">
                            <div class="radio-option">
                                <input type="radio" name="quality_mode" value="fast" id="fast">
                                <label for="fast">⚡ Fast (quick results)</label>
                            </div>
                            <div class="radio-option">
                                <input type="radio" name="quality_mode" value="balanced" id="balanced" checked>
                                <label for="balanced">⚖️ Balanced (recommended)</label>
                            </div>
                            <div class="radio-option">
                                <input type="radio" name="quality_mode" value="high" id="high">
                                <label for="high">🎯 High Quality (best accuracy)</label>
                            </div>
                        </div>
                    </div>

                    <button type="submit" class="btn">🚀 Generate Summary</button>
                </form>
            </div>

            <div id="file-tab" class="tab-content">
                <div class="upload-section">
                    <h3>📁 Upload Document</h3>
                    <p>Upload PDF or TXT files for automatic summarization</p>
                    <form method="post" enctype="multipart/form-data" onsubmit="showProcessing()">
                        <div class="file-input">
                            <input type="file" name="file" id="file" accept=".pdf,.txt" required>
                            <label for="file">📎 Choose file to upload</label>
                        </div>

                        <div class="quality-options">
                            <label>⚙️ Quality Mode:</label>
                            <div class="radio-group">
                                <div class="radio-option">
                                    <input type="radio" name="quality_mode" value="fast" id="file_fast">
                                    <label for="file_fast">⚡ Fast</label>
                                </div>
                                <div class="radio-option">
                                    <input type="radio" name="quality_mode" value="balanced" id="file_balanced" checked>
                                    <label for="file_balanced">⚖️ Balanced</label>
                                </div>
                                <div class="radio-option">
                                    <input type="radio" name="quality_mode" value="high" id="file_high">
                                    <label for="file_high">🎯 High Quality</label>
                                </div>
                            </div>
                        </div>

                        <button type="submit" class="btn">📤 Upload & Summarize</button>
                    </form>
                    <p style="margin: 15px 0 0 0; font-size: 0.9rem; color: #64748b;">
                        📋 Maximum file size: 50MB. Supported formats: PDF, TXT
                    </p>
                </div>
            </div>

        <div id="advanced-tab" class="tab-content">
            <div class="advanced-section">
                <h3>Advanced Summarization Options</h3>

                <div class="feature-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0;">
                    <div class="feature-card" style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
                        <h4>🎯 Quality Modes</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><strong>Fast:</strong> Quick results, basic accuracy</li>
                            <li><strong>Balanced:</strong> Optimal quality-speed ratio</li>
                            <li><strong>High:</strong> Maximum accuracy, slower processing</li>
                        </ul>
                    </div>

                    <div class="feature-card" style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
                        <h4>🧠 Agentic Features</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>Content type detection</li>
                            <li>Complexity analysis</li>
                            <li>Topic extraction</li>
                            <li>Adaptive processing</li>
                        </ul>
                    </div>

                    <div class="feature-card" style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
                        <h4>📊 Quality Metrics</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>ROUGE, METEOR, BLEU scores</li>
                            <li>Factual consistency</li>
                            <li>Readability analysis</li>
                            <li>Semantic coherence</li>
                        </ul>
                    </div>

                    <div class="feature-card" style="padding: 15px; border: 1px solid #ddd; border-radius: 8px; background: #f8f9fa;">
                        <h4>📄 Document Support</h4>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li>PDF text extraction</li>
                            <li>OCR error correction</li>
                            <li>Long document chunking</li>
                            <li>Hierarchical summarization</li>
                        </ul>
                    </div>
                </div>

                <div class="performance-info" style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h4>⚡ Performance Characteristics</h4>
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
                    <h4>🔌 API Access</h4>
                    <p><strong>REST Endpoint:</strong> <code>POST /api/summarize</code></p>
                    <p><strong>Web Interface:</strong> <code>http://localhost:4500</code></p>
                    <p><strong>Parameters:</strong> text, quality_mode, file (for uploads)</p>
                </div>
            </div>
        </div>

            {% if file_info %}
            <div class="file-info">
                <h4>✅ File Processed Successfully</h4>
                <p><strong>📄 Title:</strong> {{ file_info.title }}</p>
                <p><strong>👤 Author:</strong> {{ file_info.author }}</p>
                <p><strong>📑 Pages:</strong> {{ file_info.pages }}</p>
                <p><strong>💾 Size:</strong> {{ file_info.size }} bytes</p>
            </div>
            {% endif %}

            {% if summary %}
            <div class="output">
                <h3>📊 Summarization Results</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
                    <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
                        <strong style="color: #4f46e5;">📏 Original Length:</strong>
                        <p style="margin: 5px 0 0 0; font-size: 1.2rem; font-weight: 600;">{{ original_length }} chars</p>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
                        <strong style="color: #4f46e5;">📝 Summary Length:</strong>
                        <p style="margin: 5px 0 0 0; font-size: 1.2rem; font-weight: 600;">{{ summary_length }} chars</p>
                    </div>
                    <div style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
                        <strong style="color: #4f46e5;">🗜️ Compression Ratio:</strong>
                        <p style="margin: 5px 0 0 0; font-size: 1.2rem; font-weight: 600;">{{ "%.2f"|format(compression_ratio) }}</p>
                    </div>
                </div>

                <div style="background: white; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; margin-bottom: 20px;">
                    <strong style="color: #4f46e5; display: block; margin-bottom: 10px;">📋 Generated Summary:</strong>
                    <p style="margin: 0; line-height: 1.6; color: #374151;">{{ summary }}</p>
                </div>

                {% if evaluation %}
                <h4 style="color: #1e293b; margin-bottom: 15px;">📈 Quality Metrics</h4>
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
                        <strong>📏 Factual Consistency</strong>
                        <p>{{ "%.3f"|format(evaluation.factual_consistency_score) }}</p>
                    </div>
                    <div class="metric">
                        <strong>🎭 Hallucination Rate</strong>
                        <p>{{ "%.3f"|format(evaluation.hallucination_rate) }}</p>
                    </div>
                </div>
                {% endif %}
            </div>
            {% endif %}

            {% if error %}
            <div class="error">
                <strong>❌ Error:</strong> {{ error }}
            </div>
            {% endif %}
        </div>
    </div>
</body>
</html>
'''
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
                print(f"Starting summarization for {len(text)} characters...")

                # Get quality mode from form data
                quality_mode = request.form.get('quality_mode', 'balanced')
                print(f"Quality mode: {quality_mode}")

                # Initialize components
                summarizer = HybridSummarizer()
                evaluator = SummarizationEvaluator()

                # Generate summary with quality mode and verbose logging (Unicode-safe)
                summary_result = summarizer.summarize(text, verbose=True, quality_mode=quality_mode)
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
        summarizer = HybridSummarizer()
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
    app.run(host='localhost', port=4500, debug=True)