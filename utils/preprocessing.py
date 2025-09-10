import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import sent_tokenize, word_tokenize
import string

# Robust NLTK setup with fallback handling
try:
    # Try to download NLTK data
    nltk.download('stopwords', quiet=True, force=False)
    nltk.download('wordnet', quiet=True, force=False)
    nltk.download('punkt', quiet=True, force=False)
except Exception as e:
    print(f"NLTK download warning: {e}")
    try:
        # Fallback: try to use existing data
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer
        from nltk.tokenize import sent_tokenize, word_tokenize
        print("Using existing NLTK data")
    except:
        print("NLTK data not available, using basic fallbacks")
        # Define minimal fallbacks
        import re
        def sent_tokenize(text):
            return re.split(r'[.!?]+', text)
        def word_tokenize(text):
            return text.split()

def clean_ocr_text(text):
    """Handle common OCR errors and noise in educational documents"""
    # Fix common OCR misrecognitions
    ocr_fixes = {
        r'\b1\b': 'I',  # 1 -> I
        r'\b0\b': 'O',  # 0 -> O
        r'\bl\b': 'I',  # l -> I
        r'\b\|\b': 'I',  # | -> I
        r'\b@\b': 'a',  # @ -> a
        r'\b&\b': 'et',  # & -> et
        r'\b\$\b': 'S',  # $ -> S
    }
    for pattern, replacement in ocr_fixes.items():
        text = re.sub(pattern, replacement, text)

    # Remove page numbers, headers, footers (common in PDFs)
    text = re.sub(r'\n\s*\d+\s*\n', '\n', text)  # Page numbers
    text = re.sub(r'^.*?(?=Abstract|Introduction|Chapter|Section)', '', text, flags=re.MULTILINE | re.IGNORECASE)  # Remove headers

    # Remove citations and references
    text = re.sub(r'\[\d+\]', '', text)  # [1], [2], etc.
    text = re.sub(r'\(\w+ et al\., \d{4}\)', '', text)  # (Smith et al., 2020)

    # Remove figure/table captions
    text = re.sub(r'(Figure|Table|Fig\.)\s*\d+.*?\n', '', text, flags=re.IGNORECASE)

    return text

def normalize_whitespace(text):
    """Normalize whitespace and line breaks"""
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)
    # Replace multiple newlines with double newline (paragraph breaks)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def clean_text(text):
    """Enhanced text cleaning for educational content with capitalization preservation"""
    text = clean_ocr_text(text)
    text = normalize_whitespace(text)

    # Remove remaining special characters but keep sentence punctuation and preserve case
    text = re.sub(r'[^a-zA-Z\s\.\!\?\,\;\:\-\'\"]', '', text)

    # Fix spacing around punctuation
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)

    # Preserve capitalization for proper nouns and sentence starts
    # Only convert to lowercase if it's clearly not a proper noun
    sentences = text.split('. ')
    processed_sentences = []

    for sentence in sentences:
        if sentence.strip():
            # Capitalize first letter of each sentence
            sentence = sentence.strip()
            if sentence:
                sentence = sentence[0].upper() + sentence[1:]
            processed_sentences.append(sentence)

    text = '. '.join(processed_sentences)

    return text

def segment_sentences(text):
    """Improved sentence segmentation for academic text with robust fallback"""
    # First try the simple regex-based approach as primary method
    import re

    # Handle abbreviations common in academic writing
    abbreviations = ['et al.', 'i.e.', 'e.g.', 'cf.', 'vs.', 'etc.', 'Dr.', 'Prof.', 'Fig.', 'Table', 'Eq.']
    temp_text = text
    for abbr in abbreviations:
        temp_text = temp_text.replace(abbr, abbr.replace('.', '###'))

    # Simple sentence splitting based on periods, exclamation marks, and question marks
    sentences = re.split(r'(?<=[.!?])\s+', temp_text.strip())

    # Restore periods in abbreviations and filter
    processed_sentences = []
    for sent in sentences:
        sent = sent.replace('###', '.').strip()
        # Filter out very short sentences that might be artifacts
        if len(sent) > 10 and not sent.isspace():
            processed_sentences.append(sent)

    # If we got reasonable sentences, return them
    if processed_sentences and len(processed_sentences) <= len(sentences) * 1.5:
        return processed_sentences

    # Fallback: try NLTK if regex didn't work well
    try:
        from nltk.tokenize import sent_tokenize
        nltk_sentences = sent_tokenize(text)
        if nltk_sentences:
            return nltk_sentences
    except (LookupError, ImportError):
        pass

    # Final fallback: return the whole text as one sentence
    return [text.strip()] if text.strip() else []

def preprocess_text(text, remove_stopwords=True, lemmatize=True):
    """Enhanced preprocessing with options"""
    text = clean_text(text)

    if remove_stopwords or lemmatize:
        words = word_tokenize(text)
        stop_words = set(stopwords.words('english')) if remove_stopwords else set()
        lemmatizer = WordNetLemmatizer() if lemmatize else None

        processed_words = []
        for word in words:
            if remove_stopwords and word.lower() in stop_words:
                continue
            if lemmatize:
                word = lemmatizer.lemmatize(word)
            processed_words.append(word)

        return ' '.join(processed_words)
    else:
        return text

def preprocess_for_summarization(text):
    """Specialized preprocessing for summarization that preserves important context"""
    # Clean OCR errors but preserve structure
    text = clean_ocr_text(text)
    text = normalize_whitespace(text)

    # Remove only problematic special characters, keep most punctuation
    text = re.sub(r'[^a-zA-Z\s\.\!\?\,\;\:\-\'\"\%\&\(\)\[\]\{\}\+\=\*\/]', '', text)

    # Fix spacing around punctuation
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    text = re.sub(r'([.,!?;:])\s+', r'\1 ', text)

    # Preserve sentence structure and capitalization
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    processed_sentences = []

    for sentence in sentences:
        sentence = sentence.strip()
        if sentence:
            # Capitalize first letter
            sentence = sentence[0].upper() + sentence[1:] if sentence else sentence
            processed_sentences.append(sentence)

    return ' '.join(processed_sentences)

def extract_keywords(text, top_n=10):
    """Extract important keywords from text for constrained decoding"""
    words = word_tokenize(text.lower())
    stop_words = set(stopwords.words('english'))
    words = [word for word in words if word not in stop_words and len(word) > 2]

    # Simple frequency-based keyword extraction
    from collections import Counter
    word_freq = Counter(words)
    keywords = [word for word, _ in word_freq.most_common(top_n)]

    return keywords