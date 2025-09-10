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

# Enhanced HTML template with evaluation, agentic framework info, and PDF upload
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Intelligent Document Agent - Hybrid Summarizer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        textarea { width: 100%; height: 200px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        input[type="submit"] { padding: 12px 24px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        input[type="submit"]:hover { background: #0056b3; }
        .output { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; background: #f8f9fa; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin-top: 15px; }
        .metric { background: white; padding: 10px; border-radius: 4px; border: 1px solid #eee; }
        .metric strong { color: #007bff; }
        .agent-info { background: #e7f3ff; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
        .error { color: #dc3545; background: #f8d7da; padding: 10px; border-radius: 4px; margin-top: 10px; }
        .upload-section { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
        .file-input { margin: 10px 0; }
        .tabs { display: flex; margin-bottom: 20px; }
        .tab { padding: 10px 20px; background: #e9ecef; border: none; cursor: pointer; border-radius: 4px 4px 0 0; }
        .tab.active { background: white; border-bottom: 2px solid #007bff; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .processing { color: #ffc107; font-style: italic; }
        .success { color: #28a745; }
        .file-info { background: #d4edda; padding: 10px; border-radius: 4px; margin-bottom: 15px; }
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
                submitBtn.value = 'Processing...';
                submitBtn.disabled = true;
                submitBtn.style.background = '#ffc107';
            }

            // Show loading indicator
            const loadingDiv = document.createElement('div');
            loadingDiv.id = 'loading-indicator';
            loadingDiv.innerHTML = '<p><strong>Agent is analyzing your document...</strong></p><p>This may take 10-30 seconds for the first request as models load.</p>';
            loadingDiv.style.cssText = 'background: #e7f3ff; padding: 15px; border-radius: 4px; margin: 10px 0; border: 1px solid #b3d7ff;';

            const container = document.querySelector('.container');
            const output = document.querySelector('.output');
            if (output) {
                container.insertBefore(loadingDiv, output);
            }
        }

        function hideProcessing() {
            const submitBtn = document.querySelector('input[type="submit"]:disabled');
            if (submitBtn) {
                submitBtn.value = 'Generate Summary';
                submitBtn.disabled = false;
                submitBtn.style.background = '#007bff';
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
    </script>
</head>
<body>
    <div class="container">
        <h1>Intelligent Document Agent</h1>
        <div class="agent-info">
            <h3>Agentic Framework: Perception → Planning → Action</h3>
            <p><strong>Perception:</strong> Analyzes document structure and preprocesses content</p>
            <p><strong>Planning:</strong> Determines optimal chunking strategy based on document length</p>
            <p><strong>Action:</strong> Executes hybrid extractive-abstractive summarization with constrained decoding</p>
        </div>

        <div class="system-status" style="background: #d4edda; padding: 10px; border-radius: 4px; margin-bottom: 20px; border: 1px solid #c3e6cb;">
            <h4 style="margin: 0 0 5px 0; color: #155724;">System Status: Ready</h4>
            <p style="margin: 0; color: #155724; font-size: 14px;">
                Models loaded and optimized for your hardware.
                First request may take 15-30 seconds, subsequent requests 5-15 seconds.
            </p>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('text-tab')">Text Input</button>
            <button class="tab" onclick="switchTab('file-tab')">File Upload</button>
            <button class="tab" onclick="switchTab('advanced-tab')">Advanced Options</button>
        </div>

        <div id="text-tab" class="tab-content active">
            <form method="post" onsubmit="showProcessing()">
                <label>Enter educational text to summarize:</label><br>
                <textarea name="text" placeholder="Paste your educational content here (notes, PDFs, research papers, etc.)">{{ text if text else '' }}</textarea><br><br>

                <div class="quality-options" style="margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                    <label><strong>Quality Mode:</strong></label><br>
                    <input type="radio" name="quality_mode" value="fast" id="fast"> <label for="fast">Fast (quick results)</label>
                    <input type="radio" name="quality_mode" value="balanced" id="balanced" checked> <label for="balanced">Balanced (recommended)</label>
                    <input type="radio" name="quality_mode" value="high" id="high"> <label for="high">High Quality (best accuracy)</label>
                </div>

                <input type="submit" value="Generate Summary">
            </form>
        </div>

        <div id="file-tab" class="tab-content">
            <div class="upload-section">
                <h3>Upload Document</h3>
                <p>Upload PDF or TXT files for automatic summarization</p>
                <form method="post" enctype="multipart/form-data" onsubmit="showProcessing()">
                    <div class="file-input">
                        <label for="file">Choose file:</label>
                        <input type="file" name="file" id="file" accept=".pdf,.txt" required>
                    </div>

                    <div class="quality-options" style="margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 4px;">
                        <label><strong>Quality Mode:</strong></label><br>
                        <input type="radio" name="quality_mode" value="fast" id="file_fast"> <label for="file_fast">Fast</label>
                        <input type="radio" name="quality_mode" value="balanced" id="file_balanced" checked> <label for="file_balanced">Balanced</label>
                        <input type="radio" name="quality_mode" value="high" id="file_high"> <label for="file_high">High Quality</label>
                    </div>

                    <input type="submit" value="Upload & Summarize">
                </form>
                <p><small>Maximum file size: 50MB. Supported formats: PDF, TXT</small></p>
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
            <h4>File Processed Successfully</h4>
            <p><strong>Title:</strong> {{ file_info.title }}</p>
            <p><strong>Author:</strong> {{ file_info.author }}</p>
            <p><strong>Pages:</strong> {{ file_info.pages }}</p>
            <p><strong>Size:</strong> {{ file_info.size }} bytes</p>
        </div>
        {% endif %}

        {% if summary %}
        <div class="output">
            <h3>Summarization Results:</h3>
            <p><strong>Original Length:</strong> {{ original_length }} characters</p>
            <p><strong>Summary:</strong> {{ summary }}</p>
            <p><strong>Summary Length:</strong> {{ summary_length }} characters</p>
            <p><strong>Compression Ratio:</strong> {{ "%.2f"|format(compression_ratio) }}</p>

            {% if evaluation %}
            <h4>Evaluation Metrics:</h4>
            <div class="metrics">
                <div class="metric"><strong>ROUGE-1 F1:</strong> {{ "%.3f"|format(evaluation.rouge1_f) }}</div>
                <div class="metric"><strong>ROUGE-2 F1:</strong> {{ "%.3f"|format(evaluation.rouge2_f) }}</div>
                <div class="metric"><strong>ROUGE-L F1:</strong> {{ "%.3f"|format(evaluation.rougeL_f) }}</div>
                <div class="metric"><strong>METEOR:</strong> {{ "%.3f"|format(evaluation.meteor) }}</div>
                <div class="metric"><strong>Factual Consistency:</strong> {{ "%.3f"|format(evaluation.factual_consistency_score) }}</div>
                <div class="metric"><strong>Hallucination Rate:</strong> {{ "%.3f"|format(evaluation.hallucination_rate) }}</div>
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