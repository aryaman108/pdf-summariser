"""
Minimal version of the Intelligent Document Agent
This version runs without ML models to demonstrate the app structure
"""
from flask import Flask, request, render_template_string, jsonify
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'intelligent-document-agent-key'

# Simplified HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Intelligent Document Agent - Demo Mode</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        }
        h1 {
            color: #4f46e5;
            text-align: center;
            margin-bottom: 10px;
        }
        .warning {
            background: #fef3c7;
            border: 2px solid #f59e0b;
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
        }
        .warning h3 {
            color: #92400e;
            margin-top: 0;
        }
        .info {
            background: #e0f2fe;
            border: 2px solid #0369a1;
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
        }
        textarea {
            width: 100%;
            height: 200px;
            padding: 15px;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            font-family: inherit;
            font-size: 1rem;
            resize: vertical;
        }
        .btn {
            padding: 15px 30px;
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 700;
            font-size: 1.1rem;
            margin-top: 15px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(79, 70, 229, 0.3);
        }
        .output {
            background: #f8fafc;
            padding: 20px;
            border-radius: 12px;
            margin-top: 20px;
            border: 1px solid #e2e8f0;
        }
        code {
            background: #1e293b;
            color: #10b981;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Intelligent Document Agent</h1>
        <p style="text-align: center; color: #64748b;">Demo Mode - ML Models Not Loaded</p>
        
        <div class="warning">
            <h3>⚠️ Disk Space Issue Detected</h3>
            <p><strong>Current Status:</strong> Your disk is at 100% capacity (only 392MB available)</p>
            <p><strong>Required:</strong> ~3GB free space to install ML dependencies (PyTorch, Transformers)</p>
            <p><strong>Action Needed:</strong></p>
            <ol>
                <li>Free up at least 3GB of disk space</li>
                <li>Run: <code>pip install --no-cache-dir torch transformers nltk scikit-learn</code></li>
                <li>Restart the application with: <code>python app.py</code></li>
            </ol>
        </div>

        <div class="info">
            <h3>📋 What This App Does (When Fully Installed)</h3>
            <ul>
                <li><strong>Hybrid Summarization:</strong> Combines RoBERTa (extractive) + T5 (abstractive) models</li>
                <li><strong>PDF Processing:</strong> Extract and summarize PDF documents</li>
                <li><strong>Quality Modes:</strong> Fast, Balanced, and High-Quality processing</li>
                <li><strong>Evaluation Metrics:</strong> ROUGE, METEOR, BLEU scores</li>
                <li><strong>Question Answering:</strong> Ask questions about summarized content</li>
            </ul>
        </div>

        <form method="post">
            <h3>Try the Interface (Demo Mode)</h3>
            <textarea name="text" placeholder="Enter text here... (Note: Summarization requires ML models to be installed)">{{ text if text else '' }}</textarea>
            <button type="submit" class="btn">Generate Summary (Demo)</button>
        </form>

        {% if text %}
        <div class="output">
            <h3>Demo Output</h3>
            <p><strong>Original Length:</strong> {{ text|length }} characters</p>
            <p><strong>Status:</strong> ML models not loaded. Install dependencies to enable summarization.</p>
            <p><strong>Your text preview:</strong></p>
            <p style="background: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0;">
                {{ text[:500] }}{% if text|length > 500 %}...{% endif %}
            </p>
        </div>
        {% endif %}

        <div class="info" style="margin-top: 30px;">
            <h3>🔧 Installation Steps</h3>
            <p><strong>1. Check disk space:</strong></p>
            <code>df -h .</code>
            
            <p style="margin-top: 15px;"><strong>2. Clean up space (if needed):</strong></p>
            <code>rm -rf ~/.cache/pip</code><br>
            <code>brew cleanup</code> (if using Homebrew)
            
            <p style="margin-top: 15px;"><strong>3. Install dependencies:</strong></p>
            <code>pip install --no-cache-dir -r requirements.txt</code>
            
            <p style="margin-top: 15px;"><strong>4. Run the full app:</strong></p>
            <code>python app.py</code>
        </div>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    text = ''
    if request.method == 'POST':
        text = request.form.get('text', '')
    
    return render_template_string(HTML_TEMPLATE, text=text)

@app.route('/api/summarize', methods=['POST'])
def api_summarize():
    """REST API endpoint"""
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    return jsonify({
        'error': 'ML models not loaded. Please install dependencies first.',
        'status': 'demo_mode',
        'required_space': '~3GB',
        'install_command': 'pip install --no-cache-dir torch transformers nltk scikit-learn'
    }), 503

if __name__ == '__main__':
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 60)
    print("Intelligent Document Agent - DEMO MODE")
    print("=" * 60)
    print()
    print("⚠️  WARNING: ML models not loaded due to disk space constraints")
    print()
    print("Current Status:")
    print("  - Disk Usage: 100% (only 392MB available)")
    print("  - Required: ~3GB free space")
    print()
    print("To enable full functionality:")
    print("  1. Free up at least 3GB of disk space")
    print("  2. Run: pip install --no-cache-dir torch transformers nltk scikit-learn")
    print("  3. Run: python app.py")
    print()
    print("=" * 60)
    print(f"Demo server running at: http://{host}:{port}")
    print("=" * 60)
    
    app.run(host=host, port=port, debug=False)
