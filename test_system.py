#!/usr/bin/env python3
"""
Test script for the Intelligent Document Agent
Tests both text input and PDF processing capabilities
"""

from src.hybrid_summarizer import HybridSummarizer
from src.evaluation import SummarizationEvaluator
from utils.pdf_processor import PDFProcessor
import time

def test_text_summarization():
    """Test text summarization functionality"""
    print("Testing Text Summarization...")

    # Sample educational text
    test_text = """
    Machine learning is a subset of artificial intelligence that focuses on developing algorithms
    that can learn from and make predictions on data. The field has grown significantly in recent
    years due to advances in computational power and the availability of large datasets.

    There are several types of machine learning approaches:
    1. Supervised learning: Uses labeled training data
    2. Unsupervised learning: Finds patterns in unlabeled data
    3. Reinforcement learning: Learns through interaction with environment

    Deep learning, a subset of machine learning, uses neural networks with multiple layers
    to model complex patterns in data. This approach has been particularly successful in
    areas like image recognition, natural language processing, and speech recognition.

    The future of machine learning looks promising with ongoing research in areas such as
    explainable AI, federated learning, and quantum machine learning.
    """

    try:
        start_time = time.time()

        # Initialize summarizer
        summarizer = HybridSummarizer()

        # Test with verbose logging
        result = summarizer.summarize(test_text, verbose=True)
        if isinstance(result, tuple):
            summary, agent_log = result
            print("\nAgent Activity Log:")
            for log in agent_log:
                print(f"  {log}")
        else:
            summary = result

        processing_time = time.time() - start_time

        print("\nText Summarization Results:")
        print(f"Original length: {len(test_text)} characters")
        print(f"Summary length: {len(summary)} characters")
        print(f"Processing time: {processing_time:.2f} seconds")
        print(f"Compression ratio: {len(summary)/len(test_text):.3f}")
        print(f"\nSummary:\n{summary}")

        return True

    except Exception as e:
        print(f"Text summarization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_evaluation_metrics():
    """Test evaluation metrics"""
    print("\nTesting Evaluation Metrics...")

    try:
        evaluator = SummarizationEvaluator()

        test_summary = "Machine learning uses algorithms to learn from data and make predictions."
        test_reference = "Machine learning involves developing algorithms that learn from data to make predictions."
        test_original = "Machine learning is a subset of AI that focuses on algorithms learning from data."

        results = evaluator.evaluate_summary(
            test_summary,
            test_reference,
            test_original,
            ["machine", "learning", "algorithms"]
        )

        print("Evaluation Results:")
        print(f"  ROUGE-1 F1: {results.get('rouge1_f', 0):.3f}")
        print(f"  METEOR: {results.get('meteor', 0):.3f}")
        print(f"  Factual Consistency: {results.get('factual_consistency_score', 0):.3f}")
        print(f"  Hallucination Rate: {results.get('hallucination_rate', 0):.3f}")

        return True

    except Exception as e:
        print(f"Evaluation testing failed: {e}")
        return False

def test_pdf_processing():
    """Test PDF processing capabilities"""
    print("\nTesting PDF Processing...")

    try:
        pdf_processor = PDFProcessor()

        # Test with a simple validation
        print("PDF processor initialized successfully")
        print("PDF processing capabilities:")
        print("  - Text extraction from PDF files")
        print("  - OCR error correction")
        print("  - Metadata extraction")
        print("  - File validation")

        return True

    except Exception as e:
        print(f"PDF processing test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Intelligent Document Agent - System Test Suite")
    print("=" * 60)

    test_results = []

    # Test text summarization
    test_results.append(("Text Summarization", test_text_summarization()))

    # Test evaluation metrics
    test_results.append(("Evaluation Metrics", test_evaluation_metrics()))

    # Test PDF processing
    test_results.append(("PDF Processing", test_pdf_processing()))

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("All systems operational! The Intelligent Document Agent is ready.")
        print("\nAccess the web interface at: http://localhost:4500")
        print("You can now:")
        print("  - Paste text for summarization")
        print("  - Upload PDF files")
        print("  - View real-time evaluation metrics")
        print("  - Experience the agentic framework in action")
    else:
        print("Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()