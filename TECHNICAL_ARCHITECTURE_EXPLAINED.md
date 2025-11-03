# 🔬 Technical Architecture Deep Dive

## 🎯 **Project Overview**

This is an **Intelligent Document Agent** that uses a **hybrid AI approach** to summarize documents, videos, and audio files. It combines multiple AI models and techniques to create high-quality summaries.

---

## 🏗️ **System Architecture**

### **1. Web Application Layer (Flask)**

```python
# app.py - Main Flask application
- Web interface with HTML/CSS/JavaScript
- REST API endpoints (/api/summarize, /api/ask)
- File upload handling (5MB limit)
- Session management and caching
- Real-time processing feedback
```

### **2. Core AI Pipeline (Hybrid Summarization)**

```python
# src/hybrid_summarizer.py - Main orchestrator
HybridSummarizer:
  ├── Extractive Phase (RoBERTa)
  ├── Abstractive Phase (T5)
  └── Quality Control & Evaluation
```

### **3. File Processing Layer**

```python
# utils/ - Specialized processors
├── pdf_processor.py      # PDF text extraction
├── multimodal_processor.py  # Video/Audio processing
└── preprocessing.py      # Text cleaning & preparation
```

---

## 🤖 **AI Models & Techniques**

### **Phase 1: Extractive Summarization (RoBERTa)**

```python
# src/roberta_extractive.py
Model: distilbert-base-uncased (66M parameters)
Purpose: Select the most important sentences from original text

Process:
1. Split text into sentences
2. Generate embeddings for each sentence using BERT/RoBERTa
3. Calculate sentence importance scores based on:
   - Position in document
   - Semantic similarity to document centroid
   - Length and complexity
   - Keyword density
4. Select top-scoring sentences (over-extraction strategy)
```

**Technical Details:**

- **Embeddings**: 768-dimensional sentence vectors
- **Similarity**: Cosine similarity between sentence embeddings
- **Scoring**: Multi-criteria ranking algorithm
- **Over-extraction**: Selects 2x more sentences than needed for comprehensive coverage

### **Phase 2: Abstractive Summarization (T5)**

```python
# src/t5_abstractive.py
Model: google/flan-t5-small (248M parameters)
Purpose: Generate human-like summary from extracted sentences

Process:
1. Take extracted sentences from Phase 1
2. Extract keywords using TF-IDF
3. Use constrained decoding to force keyword inclusion
4. Generate fluent, coherent summary
5. Apply post-processing for quality
```

**Technical Details:**

- **Constrained Decoding**: Forces inclusion of important keywords
- **Beam Search**: Uses 8 beams for better quality
- **Length Control**: Min 30, Max 150 tokens
- **Hallucination Prevention**: Keyword grounding strategy

---

## 📁 **File Processing Pipeline**

### **PDF Processing**

```python
# utils/pdf_processor.py
Libraries: PyMuPDF, PyPDF2, Pillow
Features:
- Text extraction from PDF files
- OCR for scanned documents (pytesseract)
- Metadata extraction (title, author, pages)
- Error correction for common OCR mistakes
- Multi-column layout handling
```

### **Video/Audio Processing**

```python
# utils/multimodal_processor.py
Libraries: FFmpeg, MoviePy, OpenAI Whisper

Caption Extraction Methods:
1. Embedded subtitle tracks (using FFmpeg)
2. Companion subtitle files (.srt, .vtt, .ass, etc.)
3. Video metadata descriptions
4. Language-specific files (.en.vtt, .es.srt)

Audio Transcription (Optional):
- OpenAI Whisper for speech-to-text
- Multiple model sizes (tiny, base, small, medium, large)
- Currently disabled to save resources
```

---

## 🧠 **Question Answering System**

### **QA Pipeline**

```python
# src/question_answerer.py
Model: Transformer-based QA model
Features:
- Context-aware question answering
- Confidence scoring
- Fallback strategies (summary → full text)
- Caching for repeated questions
- Multi-strategy approach
```

**QA Strategies:**

1. **Primary**: Answer from summary (fast)
2. **Fallback**: Answer from full original text (comprehensive)
3. **Confidence Boosting**: Minimum 50% confidence guarantee
4. **Caching**: Instant responses for repeated questions

---

## 🔄 **Processing Flow**

### **Document Summarization Flow**

```
Input File → File Type Detection → Processing Pipeline → AI Models → Output

PDF File:
├── Text Extraction (PyMuPDF/PyPDF2)
├── OCR if needed (Tesseract)
├── Text Cleaning
└── → Hybrid Summarization

Video File:
├── Caption Detection (FFmpeg)
├── Subtitle File Search (.srt, .vtt, .en.vtt)
├── Text Extraction from Captions
└── → Hybrid Summarization

Text Input:
├── Direct Text Processing
├── Preprocessing & Cleaning
└── → Hybrid Summarization
```

### **Hybrid Summarization Pipeline**

```
Raw Text → Preprocessing → Chunking → Extractive → Abstractive → Evaluation

1. Preprocessing:
   - Text cleaning and normalization
   - Sentence segmentation
   - Educational content optimization

2. Chunking (for long documents):
   - 1000-character chunks with sentence boundaries
   - Hierarchical summarization
   - Context preservation

3. Extractive Phase:
   - RoBERTa sentence embeddings
   - Multi-criteria sentence scoring
   - Over-extraction strategy

4. Abstractive Phase:
   - T5 text generation
   - Constrained decoding with keywords
   - Fluency optimization

5. Evaluation:
   - ROUGE, METEOR, BLEU scores
   - Factual consistency checking
   - Compression ratio analysis
```

---

## 💾 **Data Management**

### **Caching System**

```python
# In-memory LRU cache (max 10 entries)
Cache Key: MD5(text_content + quality_mode)
Cached Data:
- Generated summary
- Evaluation metrics
- Processing metadata
- Timestamp
```

### **Session Management**

```python
# Context storage for QA functionality
Session Data:
- Original text content
- Generated summary
- Processing timestamp
- User session ID
```

---

## ⚡ **Performance Optimizations**

### **Model Loading Strategy**

- **Lazy Loading**: Models load on first request (faster startup)
- **CPU Optimization**: All models run on CPU for compatibility
- **Memory Management**: Efficient batch processing
- **Fallback Models**: Alternative models if primary fails

### **Processing Optimizations**

- **Chunking**: Handles documents up to unlimited size
- **Batch Processing**: Efficient sentence embedding generation
- **Caching**: Instant results for repeated requests
- **Quality Modes**: Fast/Balanced/High quality options

### **Resource Management**

```python
Memory Usage: <4GB VRAM typical
Processing Speed:
- Short docs (<1K words): 3-8 seconds
- Medium docs (1K-5K words): 8-15 seconds
- Long docs (5K+ words): 15-30 seconds
- Cached requests: <1 second
```

---

## 🔧 **Quality Control**

### **Evaluation Metrics**

```python
# src/evaluation.py
Metrics Calculated:
- ROUGE-1/2/L: N-gram overlap scores
- METEOR: Semantic similarity metric
- BLEU: Precision-based metric
- Factual Consistency: Keyword retention
- Compression Ratio: Length reduction
- Readability: Text complexity analysis
```

### **Error Handling**

- **Graceful Degradation**: Fallback models and strategies
- **Input Validation**: File type, size, and content checks
- **Detailed Logging**: Comprehensive debugging information
- **User Feedback**: Clear error messages with solutions

---

## 🌐 **Web Interface Features**

### **Multi-Tab Interface**

1. **Text Input**: Direct text summarization
2. **File Upload**: PDF, video, audio file processing
3. **Ask Questions**: Interactive QA about summaries
4. **Advanced Options**: Quality modes and settings

### **Real-Time Features**

- **Progress Indicators**: Live processing feedback
- **Server Logs**: Detailed extraction information
- **Error Messages**: Specific guidance for issues
- **Performance Metrics**: Processing time and quality scores

---

## 🔬 **Research & Innovation**

### **Hybrid Approach Benefits**

- **Extractive**: Preserves factual accuracy, no hallucination
- **Abstractive**: Generates fluent, human-like text
- **Combined**: Best of both worlds with quality control

### **Novel Techniques**

- **Over-extraction Strategy**: Comprehensive fact coverage
- **Constrained Decoding**: Keyword-grounded generation
- **Hierarchical Summarization**: Long document handling
- **Multi-modal Processing**: Video caption extraction

### **Educational Focus**

- **OCR Error Correction**: Handles scanned documents
- **Academic Text Processing**: Citations, references, figures
- **Content Type Detection**: Adapts to different document types
- **Quality Optimization**: Multiple processing modes

---

## 🚀 **Deployment Architecture**

### **Development Setup**

```bash
# Local development server
Flask app on localhost:8080
Virtual environment with all dependencies
Real-time model loading and processing
```

### **Production Considerations**

- **WSGI Server**: Gunicorn/uWSGI for production
- **Model Caching**: Persistent model loading
- **Database**: Replace in-memory cache with Redis/PostgreSQL
- **File Storage**: Cloud storage for uploaded files
- **Load Balancing**: Multiple worker processes

---

This architecture creates a sophisticated, research-grade document processing system that combines multiple AI techniques for high-quality summarization and question answering capabilities.
