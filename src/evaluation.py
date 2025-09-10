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
        """Enhanced comprehensive evaluation of a generated summary"""
        results = {}

        # Basic NLP metrics
        rouge_scores = self.compute_rouge(generated_summary, reference_summary)
        results.update(rouge_scores)

        results['meteor'] = self.compute_meteor(generated_summary, reference_summary)

        bleu_scores = self.compute_bleu(generated_summary, reference_summary)
        results.update(bleu_scores)

        # Enhanced factual consistency
        consistency_scores = self.compute_factual_consistency(generated_summary, original_text, keywords)
        results.update(consistency_scores)

        # Advanced quality metrics
        quality_scores = self.compute_quality_metrics(generated_summary, original_text)
        results.update(quality_scores)

        # Readability metrics
        readability_scores = self.compute_readability_metrics(generated_summary)
        results.update(readability_scores)

        # Summary statistics
        results['summary_length'] = len(generated_summary.split())
        results['compression_ratio'] = len(generated_summary.split()) / len(original_text.split()) if original_text.split() else 0

        # Overall quality score
        results['overall_quality_score'] = self.compute_overall_quality_score(results)

        return results

    def compute_quality_metrics(self, summary, original_text):
        """Compute advanced quality metrics"""
        # Semantic coherence (simplified)
        summary_sentences = summary.split('.')
        coherence_score = min(1.0, len(summary_sentences) / 5)  # Prefer 3-5 sentences

        # Information density
        summary_words = set(summary.lower().split())
        original_words = set(original_text.lower().split())
        novel_words = summary_words - original_words
        information_density = 1 - (len(novel_words) / len(summary_words)) if summary_words else 0

        # Topic coverage
        original_topics = self._extract_topics(original_text)
        summary_topics = self._extract_topics(summary)
        topic_overlap = len(set(original_topics) & set(summary_topics))
        topic_coverage = topic_overlap / len(original_topics) if original_topics else 0

        return {
            'semantic_coherence': coherence_score,
            'information_density': information_density,
            'topic_coverage': topic_coverage
        }

    def compute_readability_metrics(self, text):
        """Compute readability metrics"""
        words = text.split()
        sentences = text.split('.')

        if not words or not sentences:
            return {'flesch_score': 0, 'readability_level': 'unknown'}

        # Simplified Flesch Reading Ease
        avg_words_per_sentence = len(words) / len(sentences)
        avg_syllables_per_word = sum(self._count_syllables(word) for word in words) / len(words)

        flesch_score = 206.835 - (1.015 * avg_words_per_sentence) - (84.6 * avg_syllables_per_word)
        flesch_score = max(0, min(100, flesch_score))  # Clamp to 0-100

        # Determine readability level
        if flesch_score >= 90:
            level = '5th grade'
        elif flesch_score >= 80:
            level = '6th grade'
        elif flesch_score >= 70:
            level = '7th grade'
        elif flesch_score >= 60:
            level = '8th-9th grade'
        elif flesch_score >= 50:
            level = '10th-12th grade'
        elif flesch_score >= 30:
            level = 'college'
        else:
            level = 'college graduate'

        return {
            'flesch_score': flesch_score,
            'readability_level': level
        }

    def compute_overall_quality_score(self, metrics):
        """Compute overall quality score from all metrics"""
        weights = {
            'rouge1_f': 0.15,
            'rouge2_f': 0.15,
            'rougeL_f': 0.15,
            'meteor': 0.10,
            'factual_consistency_score': 0.20,
            'semantic_coherence': 0.10,
            'information_density': 0.10,
            'topic_coverage': 0.05
        }

        score = 0
        total_weight = 0

        for metric, weight in weights.items():
            if metric in metrics:
                score += metrics[metric] * weight
                total_weight += weight

        return score / total_weight if total_weight > 0 else 0

    def _extract_topics(self, text, top_n=10):
        """Extract main topics from text"""
        words = text.lower().split()
        stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'])
        filtered_words = [word for word in words if len(word) > 3 and word not in stop_words]

        from collections import Counter
        word_freq = Counter(filtered_words)
        return [word for word, _ in word_freq.most_common(top_n)]

    def _count_syllables(self, word):
        """Count syllables in a word (simplified)"""
        word = word.lower()
        count = 0
        vowels = "aeiouy"

        if word[0] in vowels:
            count += 1

        for i in range(1, len(word)):
            if word[i] in vowels and word[i-1] not in vowels:
                count += 1

        if word.endswith("e"):
            count -= 1

        return max(1, count)

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