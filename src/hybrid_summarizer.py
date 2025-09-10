try:
    from .roberta_extractive import RobertaExtractiveSummarizer
    from .t5_abstractive import T5AbstractiveSummarizer
    from ..utils.preprocessing import clean_text, segment_sentences
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from src.roberta_extractive import RobertaExtractiveSummarizer
    from src.t5_abstractive import T5AbstractiveSummarizer
    from utils.preprocessing import clean_text, segment_sentences
import nltk
from nltk.tokenize import sent_tokenize
import time

nltk.download('punkt')

class HybridSummarizer:
    def __init__(self):
        self.extractive = RobertaExtractiveSummarizer()
        self.abstractive = T5AbstractiveSummarizer()
        self.max_chunk_length = 1000  # Characters per chunk

    def chunk_document(self, text, max_length=1000):
        """Divide long documents into manageable chunks"""
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = ""
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)
            if current_length + sentence_length > max_length and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
                current_length = sentence_length
            else:
                current_chunk += " " + sentence
                current_length += sentence_length

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def summarize_chunk(self, chunk, extractive_sentences=5):
        """Summarize a single chunk"""
        extracted_text, keywords = self.extractive.summarize(
            chunk,
            num_sentences=extractive_sentences,
            over_extract=True
        )
        summary = self.abstractive.summarize(
            extracted_text,
            keywords=keywords,
            use_constrained=True
        )
        return summary

    def hierarchical_summarize(self, chunk_summaries):
        """Perform final summarization on chunk summaries"""
        if len(chunk_summaries) == 1:
            return chunk_summaries[0]

        # Combine all chunk summaries
        combined_text = " ".join(chunk_summaries)

        # Extract key points from combined summaries
        extracted_text, keywords = self.extractive.summarize(
            combined_text,
            num_sentences=max(3, len(chunk_summaries)),
            over_extract=True
        )

        # Generate final coherent summary
        final_summary = self.abstractive.summarize(
            extracted_text,
            keywords=keywords,
            use_constrained=True,
            max_length=200  # Longer for final summary
        )

        return final_summary

    def summarize(self, text, extractive_sentences=5, use_chunking=True, verbose=False):
        """
        Main summarization method implementing the Intelligent Document Agent framework:
        1. Perception: Analyze document structure and content characteristics
        2. Planning: Determine optimal processing strategy based on analysis
        3. Action: Execute the hybrid summarization pipeline
        """
        agent_log = []

        # ===== PERCEPTION PHASE =====
        if verbose:
            agent_log.append("🤖 PERCEPTION: Analyzing document characteristics...")

        # Document analysis
        original_length = len(text)
        cleaned_text = clean_text(text)
        cleaned_length = len(cleaned_text)

        # Content type detection
        content_type = self._detect_content_type(cleaned_text)
        noise_level = self._assess_noise_level(text, cleaned_text)

        # Complexity assessment
        sentences = segment_sentences(cleaned_text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

        perception_results = {
            'original_length': original_length,
            'cleaned_length': cleaned_length,
            'content_type': content_type,
            'noise_level': noise_level,
            'num_sentences': len(sentences),
            'avg_sentence_length': avg_sentence_length
        }

        if verbose:
            agent_log.append(f"   📊 Document: {original_length} chars → {cleaned_length} chars after cleaning")
            agent_log.append(f"   📋 Content Type: {content_type}, Noise Level: {noise_level:.2f}")
            agent_log.append(f"   📝 Sentences: {len(sentences)}, Avg Length: {avg_sentence_length:.1f} words")

        # ===== PLANNING PHASE =====
        if verbose:
            agent_log.append("🎯 PLANNING: Determining processing strategy...")

        # Strategy determination
        strategy = self._plan_processing_strategy(
            cleaned_text, perception_results, use_chunking, extractive_sentences
        )

        if verbose:
            agent_log.append(f"   📋 Strategy: {strategy['approach']}")
            if strategy['chunks_needed']:
                agent_log.append(f"   📦 Chunking: {strategy['num_chunks']} chunks of ~{strategy['chunk_size']} chars")
            agent_log.append(f"   🎯 Extractive Sentences: {strategy['extractive_sentences']}")

        # ===== ACTION PHASE =====
        if verbose:
            agent_log.append("⚡ ACTION: Executing summarization pipeline...")

        start_time = time.time()

        if strategy['approach'] == 'chunked':
            # Long document: divide-and-conquer approach
            chunks = self.chunk_document(cleaned_text, strategy['chunk_size'])

            if verbose:
                agent_log.append(f"   📦 Processing {len(chunks)} chunks...")

            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                if verbose:
                    agent_log.append(f"      Chunk {i+1}/{len(chunks)}: {len(chunk)} chars")

                chunk_summary = self.summarize_chunk(chunk, strategy['extractive_sentences'])
                chunk_summaries.append(chunk_summary)

            # Hierarchical final summarization
            final_summary = self.hierarchical_summarize(chunk_summaries)

        else:
            # Short document: direct hybrid summarization
            extracted_text, keywords = self.extractive.summarize(
                cleaned_text,
                num_sentences=strategy['extractive_sentences'],
                over_extract=True
            )

            if verbose:
                agent_log.append(f"   🔍 Extracted {len(extracted_text.split('.'))} sentences")
                agent_log.append(f"   🏷️ Keywords: {', '.join(keywords[:5])}")

            final_summary = self.abstractive.summarize(
                extracted_text,
                keywords=keywords,
                use_constrained=True
            )

        processing_time = time.time() - start_time

        if verbose:
            agent_log.append(f"   ✅ Summary Generated: {len(final_summary)} chars in {processing_time:.2f}s")
            agent_log.append("🎉 AGENT CYCLE COMPLETE")

        # Return summary and optional agent log
        if verbose:
            return final_summary, agent_log
        else:
            return final_summary

    def _detect_content_type(self, text):
        """Detect content type for processing optimization"""
        text_lower = text.lower()

        # Academic indicators
        academic_indicators = ['abstract', 'introduction', 'methodology', 'conclusion', 'references', 'et al.', 'doi:']
        academic_score = sum(1 for indicator in academic_indicators if indicator in text_lower)

        # Educational indicators
        educational_indicators = ['chapter', 'lesson', 'exercise', 'assignment', 'study', 'notes', 'lecture']
        educational_score = sum(1 for indicator in educational_indicators if indicator in text_lower)

        if academic_score > educational_score:
            return 'academic'
        elif educational_score > 0:
            return 'educational'
        else:
            return 'general'

    def _assess_noise_level(self, original, cleaned):
        """Assess noise level in the document"""
        if len(original) == 0:
            return 0.0
        noise_ratio = 1 - (len(cleaned) / len(original))
        return min(noise_ratio, 1.0)  # Cap at 100%

    def _plan_processing_strategy(self, text, perception, use_chunking, base_sentences):
        """Plan the optimal processing strategy"""
        strategy = {
            'approach': 'direct',
            'chunks_needed': False,
            'num_chunks': 1,
            'chunk_size': self.max_chunk_length,
            'extractive_sentences': base_sentences
        }

        # Determine if chunking is needed
        if use_chunking and len(text) > self.max_chunk_length * 2:
            strategy['approach'] = 'chunked'
            strategy['chunks_needed'] = True
            strategy['num_chunks'] = max(2, len(text) // self.max_chunk_length)
            strategy['chunk_size'] = len(text) // strategy['num_chunks']

            # Adjust extractive sentences based on content type
            if perception['content_type'] == 'academic':
                strategy['extractive_sentences'] = max(3, base_sentences // 2)  # More conservative for academic
            else:
                strategy['extractive_sentences'] = base_sentences

        return strategy