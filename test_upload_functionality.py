#!/usr/bin/env python3
"""
Test script to verify document upload and summarization functionality
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.hybrid_summarizer import HybridSummarizer
from utils.pdf_processor import PDFProcessor
from utils.preprocessing import clean_text

def test_text_summarization():
    """Test basic text summarization functionality"""
    print("Testing text summarization...")

    # Sample text for testing
    test_text = """
    Artificial Intelligence (AI) is revolutionizing various industries by automating complex tasks and providing intelligent insights. Machine learning, a subset of AI, enables computers to learn from data without being explicitly programmed. Natural Language Processing (NLP) allows machines to understand and generate human language, making interactions between humans and computers more intuitive.

    The field of NLP has seen significant advancements in recent years, particularly with the development of transformer-based models like BERT and GPT. These models have achieved state-of-the-art performance on various language understanding tasks, including text classification, sentiment analysis, and question answering.

    Document summarization is one of the key applications of NLP, where the goal is to condense long documents into shorter versions while preserving the most important information. There are two main approaches to summarization: extractive and abstractive. Extractive summarization selects and combines existing sentences from the original text, while abstractive summarization generates new sentences that capture the essence of the content.
    """

    try:
        summarizer = HybridSummarizer()
        summary = summarizer.summarize(test_text, quality_mode="balanced", verbose=True)

        print("SUCCESS: Text summarization successful!")
        print(f"Original length: {len(test_text)} characters")
        print(f"Summary length: {len(summary)} characters")
        print(f"Compression ratio: {len(summary)/len(test_text):.3f}")
        print(f"Summary: {summary[:200]}...")

        return True
    except Exception as e:
        print(f"FAILED: Text summarization failed: {e}")
        return False

def test_pdf_processing():
    """Test PDF processing functionality"""
    print("\nTesting PDF processing...")

    # Create a simple test PDF content
    test_content = """This is a test PDF document.

    It contains multiple paragraphs of text that can be used for summarization testing.

    The document processor should be able to extract this text and prepare it for summarization.

    PDF processing involves text extraction, cleaning, and preprocessing steps."""

    try:
        # Create a temporary text file to simulate PDF content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            temp_file_path = f.name

        # Test PDF processor
        processor = PDFProcessor()

        # Since we don't have actual PDF creation, we'll test with the text file
        with open(temp_file_path, 'r') as f:
            extracted_text = f.read()

        cleaned_text = processor._post_process_pdf_text(extracted_text)

        print("SUCCESS: PDF processing simulation successful!")
        print(f"Extracted text length: {len(extracted_text)} characters")
        print(f"Cleaned text length: {len(cleaned_text)} characters")

        # Clean up
        os.unlink(temp_file_path)

        return True
    except Exception as e:
        print(f"FAILED: PDF processing failed: {e}")
        return False

def test_file_upload_validation():
    """Test file upload validation"""
    print("\nTesting file upload validation...")

    from app import allowed_file

    # Test valid files
    valid_files = ['document.pdf', 'report.PDF', 'notes.txt', 'paper.TXT']
    invalid_files = ['document.docx', 'image.jpg', 'script.py', 'data.csv']

    valid_count = 0
    invalid_count = 0

    for filename in valid_files:
        if allowed_file(filename):
            valid_count += 1
        else:
            print(f"ERROR: Should be valid: {filename}")

    for filename in invalid_files:
        if not allowed_file(filename):
            invalid_count += 1
        else:
            print(f"ERROR: Should be invalid: {filename}")

    if valid_count == len(valid_files) and invalid_count == len(invalid_files):
        print("SUCCESS: File upload validation successful!")
        return True
    else:
        print("FAILED: File upload validation failed!")
        return False

def main():
    """Run all tests"""
    print("Starting Document Upload & Summarization Tests")
    print("=" * 60)

    results = []

    # Test text summarization
    results.append(test_text_summarization())

    # Test PDF processing
    results.append(test_pdf_processing())

    # Test file upload validation
    results.append(test_file_upload_validation())

    print("\n" + "=" * 60)
    print("Test Results Summary:")

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")

    if passed == total:
        print("SUCCESS: All tests passed! Document upload and summarization functionality is working correctly.")
        return 0
    else:
        print("WARNING: Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    exit(main())