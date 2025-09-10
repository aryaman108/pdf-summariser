from nltk.tokenize import sent_tokenize

# Import preprocessing functions directly to avoid import issues
try:
    from ..utils.preprocessing import preprocess_for_summarization
except ImportError:
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from utils.preprocessing import preprocess_for_summarization
    except ImportError:
        # Define fallback if import fails
        def preprocess_for_summarization(text):
            """Fallback preprocessing function"""
            import re
            # Basic cleaning while preserving structure
            text = re.sub(r'[^a-zA-Z\s\.\!\?\,\;\:\-\'\"\%\&\(\)\[\]\{\}\+\=\*\/]', '', text)
            text = re.sub(r'\s+', ' ', text).strip()
            return text

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
import time
# NLTK punkt is handled centrally in app.py

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

    def summarize(self, text, extractive_sentences=5, use_chunking=True, verbose=False, quality_mode="balanced"):
        """
        Enhanced summarization method with quality improvements:
        1. Multi-pass refinement for better accuracy
        2. Quality-based sentence selection
        3. Contextual coherence enhancement
        4. Length optimization based on content complexity
        """
        agent_log = []

        # ===== QUALITY ENHANCEMENT =====
        # Adjust parameters based on quality mode
        if quality_mode == "high":
            extractive_sentences = max(extractive_sentences, 7)  # More sentences for high quality
            use_refinement = True
        elif quality_mode == "fast":
            extractive_sentences = min(extractive_sentences, 3)  # Fewer sentences for speed
            use_refinement = False
        else:  # balanced
            use_refinement = True

        # ===== PERCEPTION PHASE =====
        if verbose:
            agent_log.append("PERCEPTION: Analyzing document characteristics...")

        # Enhanced document analysis with better preprocessing
        original_length = len(text)
        cleaned_text = preprocess_for_summarization(text)
        cleaned_length = len(cleaned_text)

        # Advanced content analysis
        content_analysis = self._analyze_content_quality(cleaned_text)
        sentences = segment_sentences(cleaned_text)

        perception_results = {
            'original_length': original_length,
            'cleaned_length': cleaned_length,
            'content_type': content_analysis['type'],
            'complexity_score': content_analysis['complexity'],
            'key_topics': content_analysis['topics'],
            'num_sentences': len(sentences),
            'quality_mode': quality_mode
        }

        if verbose:
            agent_log.append(f"   Document: {original_length} chars, Complexity: {content_analysis['complexity']:.2f}")
            agent_log.append(f"   Content Type: {content_analysis['type']}, Topics: {', '.join(content_analysis['topics'][:3])}")

        # ===== PLANNING PHASE =====
        strategy = self._plan_processing_strategy(
            cleaned_text, perception_results, use_chunking, extractive_sentences
        )

        if verbose:
            agent_log.append(f"   Strategy: {strategy['approach']}, Quality: {quality_mode}")

        # ===== ACTION PHASE =====
        start_time = time.time()

        if strategy['approach'] == 'chunked':
            # Enhanced chunked processing
            chunks = self.chunk_document(cleaned_text, strategy['chunk_size'])
            chunk_summaries = []

            for i, chunk in enumerate(chunks):
                chunk_summary = self.summarize_chunk_enhanced(
                    chunk, strategy['extractive_sentences'], content_analysis
                )
                chunk_summaries.append(chunk_summary)

            # Enhanced hierarchical summarization
            final_summary = self.hierarchical_summarize_enhanced(chunk_summaries, content_analysis)

        else:
            # Enhanced single document processing
            final_summary = self.summarize_single_enhanced(
                cleaned_text, strategy['extractive_sentences'], content_analysis, use_refinement
            )

        # Quality post-processing
        final_summary = self._post_process_summary(final_summary, content_analysis)

        processing_time = time.time() - start_time

        if verbose:
            agent_log.append(f"   Summary Generated: {len(final_summary)} chars in {processing_time:.2f}s")
            agent_log.append("AGENT CYCLE COMPLETE")

        return (final_summary, agent_log) if verbose else final_summary

    def _analyze_content_quality(self, text):
        """Advanced content analysis for quality optimization"""
        words = text.split()
        sentences = text.split('.')

        # Complexity analysis
        avg_word_length = sum(len(word) for word in words) / len(words) if words else 0
        avg_sentence_length = len(words) / len(sentences) if sentences else 0

        # Topic extraction (simple keyword frequency)
        common_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        keywords = [word.lower() for word in words if len(word) > 3 and word.lower() not in common_words]
        from collections import Counter
        topic_words = [word for word, _ in Counter(keywords).most_common(10)]

        # Content type detection
        academic_indicators = ['research', 'study', 'analysis', 'methodology', 'conclusion', 'abstract', 'et al']
        educational_indicators = ['chapter', 'lesson', 'exercise', 'assignment', 'study', 'notes']

        academic_score = sum(1 for indicator in academic_indicators if indicator in text.lower())
        educational_score = sum(1 for indicator in educational_indicators if indicator in text.lower())

        if academic_score > educational_score:
            content_type = 'academic'
        elif educational_score > 0:
            content_type = 'educational'
        else:
            content_type = 'general'

        # Complexity score (0-1 scale)
        complexity = min(1.0, (avg_word_length * avg_sentence_length) / 1000)

        return {
            'type': content_type,
            'complexity': complexity,
            'topics': topic_words,
            'avg_word_length': avg_word_length,
            'avg_sentence_length': avg_sentence_length
        }

    def summarize_chunk_enhanced(self, chunk, num_sentences, content_analysis):
        """Enhanced chunk summarization with quality optimization"""
        # Extract with quality-based selection
        extracted_text, keywords = self.extractive.summarize(
            chunk, num_sentences=num_sentences, over_extract=True
        )

        # Adjust abstractive parameters based on content
        text_length = len(extracted_text.split())
        if content_analysis['complexity'] > 0.7:
            # Complex content: more detailed summary
            max_length = min(200, int(text_length * 2))
            min_length = max(50, int(text_length // 3))
        else:
            # Simple content: concise summary
            max_length = min(150, int(text_length * 1.5))
            min_length = max(30, int(text_length // 4))

        summary = self.abstractive.summarize(
            extracted_text,
            keywords=keywords,
            max_length=max_length,
            min_length=min_length,
            use_constrained=True
        )

        return summary

    def summarize_single_enhanced(self, text, num_sentences, content_analysis, use_refinement=True):
        """Enhanced single document summarization with better context preservation"""
        # Extract more sentences to ensure comprehensive coverage
        base_sentences = max(num_sentences, 5)  # Ensure at least 5 sentences for context

        # First pass: extract comprehensive set of sentences
        extracted_text, keywords = self.extractive.summarize(
            text, num_sentences=base_sentences, over_extract=True
        )

        # Ensure we have enough content for meaningful summarization
        if len(extracted_text.split()) < 50:
            # If extraction is too short, use more sentences
            extracted_text, keywords = self.extractive.summarize(
                text, num_sentences=base_sentences * 2, over_extract=True
            )

        # Calculate optimal summary length - be more generous for better context
        text_length = len(extracted_text.split())
        if content_analysis['complexity'] > 0.7:
            # Complex content: detailed summary
            max_length = min(250, int(text_length * 1.8))
            min_length = max(80, int(text_length * 0.6))
        else:
            # Simple content: comprehensive but concise
            max_length = min(200, int(text_length * 1.5))
            min_length = max(60, int(text_length * 0.5))

        # Generate summary with enhanced parameters for better context
        summary = self.abstractive.summarize(
            extracted_text,
            keywords=keywords,
            max_length=max_length,
            min_length=min_length,
            use_constrained=True
        )

        return summary

    def _refine_extraction(self, extracted_text, keywords, content_analysis):
        """Refine extracted content while preserving context and coherence"""
        sentences = extracted_text.split('. ')

        if len(sentences) <= 3:
            # Don't over-refine short extractions
            return extracted_text, keywords

        # Score sentences based on content analysis but preserve order
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0

            # Position bonus (preserve document flow)
            if i == 0:  # First sentence often sets context
                score += 3
            elif i == len(sentences) - 1:  # Last sentence often provides conclusion
                score += 2
            elif i < len(sentences) * 0.3:  # Early sentences important for context
                score += 1

            # Topic relevance (but don't over-weight)
            sentence_words = set(sentence.lower().split())
            topic_overlap = len(sentence_words.intersection(set(content_analysis['topics'])))
            score += min(topic_overlap, 2)  # Cap at 2 to prevent over-weighting

            # Length appropriateness (moderate preference)
            word_count = len(sentence.split())
            if 10 <= word_count <= 25:  # Optimal sentence length range
                score += 1

            # Keyword density (light weighting to preserve context)
            keyword_density = sum(1 for keyword in keywords if keyword.lower() in sentence.lower())
            score += min(keyword_density, 1)  # Cap at 1

            scored_sentences.append((sentence, score, i))  # Keep original order

        # Sort by score but maintain some original order
        scored_sentences.sort(key=lambda x: (x[1], -x[2]), reverse=True)  # Score first, then reverse order

        # Select sentences while preserving context (don't remove more than 30%)
        max_removal = max(1, int(len(sentences) * 0.3))
        selected_sentences = scored_sentences[:len(sentences) - max_removal]

        # Sort back to original order for coherence
        selected_sentences.sort(key=lambda x: x[2])

        refined_text = '. '.join([s[0] for s in selected_sentences])

        return refined_text, keywords

    def hierarchical_summarize_enhanced(self, chunk_summaries, content_analysis):
        """Enhanced hierarchical summarization"""
        if len(chunk_summaries) == 1:
            return chunk_summaries[0]

        # Combine with overlap to maintain coherence
        combined_text = ' '.join(chunk_summaries)

        # Extract key points from combined summaries
        extracted_text, keywords = self.extractive.summarize(
            combined_text,
            num_sentences=max(3, len(chunk_summaries)),
            over_extract=True
        )

        # Generate final summary with coherence focus
        final_summary = self.abstractive.summarize(
            extracted_text,
            keywords=keywords,
            use_constrained=True,
            max_length=250,  # Longer for final summary
            min_length=50
        )

        return final_summary

    def _post_process_summary(self, summary, content_analysis):
        """Enhanced post-processing for coherence and context preservation"""
        if not summary:
            return summary

        # Ensure summary starts with capital letter
        summary = summary[0].upper() + summary[1:] if summary else summary

        # Add topic context if missing and beneficial
        first_sentence = summary.split('.')[0] if '.' in summary else summary
        if content_analysis['topics'] and len(first_sentence.split()) < 12:
            # Add contextual information for short summaries
            main_topic = content_analysis['topics'][0]
            if main_topic.lower() not in first_sentence.lower():
                summary = f"This {content_analysis['type']} content discusses {main_topic}. {summary}"

        # Enhance coherence by ensuring logical flow
        summary = self._enhance_summary_coherence(summary, content_analysis)

        # Ensure proper punctuation
        if summary and not summary.endswith(('.', '!', '?')):
            summary += '.'

        return summary

    def _enhance_summary_coherence(self, summary, content_analysis):
        """Enhance summary coherence and logical flow"""
        import re

        # Split into sentences for analysis
        sentences = re.split(r'(?<=[.!?])\s+', summary.strip())
        if len(sentences) <= 1:
            return summary

        # Analyze sentence relationships and add transition words if needed
        enhanced_sentences = [sentences[0]]  # Keep first sentence as is

        transition_words = {
            'cause_effect': ['therefore', 'consequently', 'as a result', 'thus'],
            'addition': ['additionally', 'furthermore', 'moreover', 'also'],
            'contrast': ['however', 'although', 'despite', 'while'],
            'sequence': ['then', 'next', 'afterward', 'subsequently']
        }

        for i in range(1, len(sentences)):
            current_sentence = sentences[i].strip()
            if not current_sentence:
                continue

            # Simple heuristic: if sentence starts with certain words, might need transition
            first_word = current_sentence.split()[0].lower() if current_sentence.split() else ""

            # Add transition based on content type and sentence position
            if content_analysis['type'] == 'academic':
                if i == 1 and not any(word in current_sentence.lower() for word in ['however', 'although', 'therefore']):
                    # Add academic transition for second sentence
                    transition = transition_words['addition'][0]
                    current_sentence = f"{transition.capitalize()} {current_sentence[0].lower() + current_sentence[1:] if current_sentence else current_sentence}"
            elif content_analysis['type'] == 'educational':
                if len(sentences) > 2 and i == len(sentences) - 1:
                    # Add concluding transition for educational content
                    transition = transition_words['sequence'][0]
                    current_sentence = f"{transition.capitalize()} {current_sentence[0].lower() + current_sentence[1:] if current_sentence else current_sentence}"

            enhanced_sentences.append(current_sentence)

        return ' '.join(enhanced_sentences)

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