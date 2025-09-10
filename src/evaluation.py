import nltk
from nltk.translate.bleu_score import sentence_bleu
from rouge_score import rouge_scorer
import numpy as np
from collections import Counter
import math

nltk.download('punkt')

class SummarizationEvaluator:
    def __init__(self):
        self.rouge_scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)

    def compute_rouge(self, generated_summary, reference_summary):
        """Compute ROUGE scores"""
        scores = self.rouge_scorer.score(reference_summary, generated_summary)

        return {
            'rouge1_f': scores['rouge1'].fmeasure,
            'rouge1_p': scores['rouge1'].precision,
            'rouge1_r': scores['rouge1'].recall,
            'rouge2_f': scores['rouge2'].fmeasure,
            'rouge2_p': scores['rouge2'].precision,
            'rouge2_r': scores['rouge2'].recall,
            'rougeL_f': scores['rougeL'].fmeasure,
            'rougeL_p': scores['rougeL'].precision,
            'rougeL_r': scores['rougeL'].recall
        }

    def compute_meteor(self, generated_summary, reference_summary):
        """Compute METEOR score (simplified implementation)"""
        def tokenize(text):
            return nltk.word_tokenize(text.lower())

        gen_tokens = tokenize(generated_summary)
        ref_tokens = tokenize(reference_summary)

        # Simple METEOR approximation using BLEU-like n-gram matching
        if not gen_tokens or not ref_tokens:
            return 0.0

        # Unigram precision and recall
        gen_counter = Counter(gen_tokens)
        ref_counter = Counter(ref_tokens)

        # Calculate precision and recall
        precision = sum((gen_counter & ref_counter).values()) / len(gen_tokens) if gen_tokens else 0
        recall = sum((gen_counter & ref_counter).values()) / len(ref_tokens) if ref_tokens else 0

        # F-mean with alpha=0.9 (standard METEOR weighting)
        if precision + recall == 0:
            return 0.0

        f_mean = (10 * precision * recall) / (9 * precision + recall)
        return f_mean

    def compute_bleu(self, generated_summary, reference_summary):
        """Compute BLEU score"""
        gen_tokens = nltk.word_tokenize(generated_summary.lower())
        ref_tokens = nltk.word_tokenize(reference_summary.lower())

        if not gen_tokens:
            return 0.0

        # BLEU-4 with smoothing
        weights = [(1, 0, 0, 0), (0.5, 0.5, 0, 0), (0.33, 0.33, 0.33, 0), (0.25, 0.25, 0.25, 0.25)]
        bleu_scores = []

        for weight in weights:
            try:
                score = sentence_bleu([ref_tokens], gen_tokens, weights=weight,
                                    smoothing_function=nltk.translate.bleu_score.SmoothingFunction().method1)
                bleu_scores.append(score)
            except:
                bleu_scores.append(0.0)

        return {
            'bleu1': bleu_scores[0],
            'bleu2': bleu_scores[1],
            'bleu4': bleu_scores[3]
        }

    def compute_factual_consistency(self, generated_summary, original_text, keywords):
        """Check factual consistency by measuring keyword retention"""
        gen_lower = generated_summary.lower()
        orig_lower = original_text.lower()

        retained_keywords = sum(1 for keyword in keywords if keyword.lower() in gen_lower)
        keyword_coverage = retained_keywords / len(keywords) if keywords else 0

        # Check for potential hallucinations (words in summary not in original)
        gen_words = set(nltk.word_tokenize(gen_lower))
        orig_words = set(nltk.word_tokenize(orig_lower))
        novel_words = gen_words - orig_words
        hallucination_rate = len(novel_words) / len(gen_words) if gen_words else 0

        return {
            'keyword_coverage': keyword_coverage,
            'hallucination_rate': hallucination_rate,
            'factual_consistency_score': keyword_coverage * (1 - hallucination_rate)
        }

    def evaluate_summary(self, generated_summary, reference_summary, original_text, keywords):
        """Comprehensive evaluation of a generated summary"""
        results = {}

        # ROUGE scores
        rouge_scores = self.compute_rouge(generated_summary, reference_summary)
        results.update(rouge_scores)

        # METEOR score
        results['meteor'] = self.compute_meteor(generated_summary, reference_summary)

        # BLEU scores
        bleu_scores = self.compute_bleu(generated_summary, reference_summary)
        results.update(bleu_scores)

        # Factual consistency
        consistency_scores = self.compute_factual_consistency(generated_summary, original_text, keywords)
        results.update(consistency_scores)

        # Summary statistics
        results['summary_length'] = len(generated_summary.split())
        results['compression_ratio'] = len(generated_summary.split()) / len(original_text.split()) if original_text.split() else 0

        return results

    def print_evaluation_report(self, results):
        """Print a formatted evaluation report"""
        print("\n" + "="*50)
        print("SUMMARIZATION EVALUATION REPORT")
        print("="*50)

        print("\nROUGE Scores:")
        print(f"  ROUGE-1 F1: {results.get('rouge1_f', 0):.3f}")
        print(f"  ROUGE-2 F1: {results.get('rouge2_f', 0):.3f}")
        print(f"  ROUGE-L F1: {results.get('rougeL_f', 0):.3f}")

        print("\nBLEU Scores:")
        print(f"  BLEU-1: {results.get('bleu1', 0):.3f}")
        print(f"  BLEU-2: {results.get('bleu2', 0):.3f}")
        print(f"  BLEU-4: {results.get('bleu4', 0):.3f}")

        print("\nOther Metrics:")
        print(f"  METEOR: {results.get('meteor', 0):.3f}")
        print(f"  Keyword Coverage: {results.get('keyword_coverage', 0):.3f}")
        print(f"  Hallucination Rate: {results.get('hallucination_rate', 0):.3f}")

        print("\nFactual Consistency:")
        print(f"  Factual Consistency Score: {results.get('factual_consistency_score', 0):.3f}")

        print("\nSummary Statistics:")
        print(f"  Summary Length: {results.get('summary_length', 0)} words")
        print(f"  Compression Ratio: {results.get('compression_ratio', 0):.3f}")

def batch_evaluate(self, summaries_data):
    """Evaluate multiple summaries and return aggregate statistics"""
    all_results = []

    for data in summaries_data:
        result = self.evaluate_summary(
            data['generated'],
            data['reference'],
            data['original'],
            data.get('keywords', [])
        )
        all_results.append(result)

    # Compute averages
    avg_results = {}
    for key in all_results[0].keys():
        if isinstance(all_results[0][key], (int, float)):
            avg_results[key] = np.mean([r[key] for r in all_results])

    return avg_results, all_results