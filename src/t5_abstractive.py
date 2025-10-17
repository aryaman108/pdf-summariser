from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class T5AbstractiveSummarizer:
    def __init__(self, model_name='google/flan-t5-small'):
        try:
            print(f"[INFO] Loading {model_name} model...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name, dtype=torch.float32)
            # Ensure model is on CPU and properly loaded
            self.model = self.model.to('cpu')
            self.model.eval()
            print(f"[SUCCESS] {model_name} model loaded successfully")
        except Exception as e:
            print(f"[ERROR] Failed to load {model_name}: {e}")
            print("[INFO] Using fallback: trying to load from local cache or alternative model")
            # Fallback to a very small model if available
            try:
                self.tokenizer = AutoTokenizer.from_pretrained('t5-small')
                self.model = AutoModelForSeq2SeqLM.from_pretrained('t5-small', dtype=torch.float32)
                self.model = self.model.to('cpu')
                self.model.eval()
                print("[SUCCESS] Fallback T5 model loaded successfully")
            except Exception as e2:
                print(f"[ERROR] Fallback model also failed: {e2}")
                raise e

    def constrained_decode(self, input_ids, keywords, max_length=150, min_length=30):
        """Generate summary with constrained decoding to include key terms"""
        try:
            if not keywords:
                # Fallback to standard generation
                return self.model.generate(
                    input_ids,
                    max_length=int(max_length),
                    min_length=int(min_length),
                    length_penalty=1.5,
                    num_beams=8,
                    early_stopping=True,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.2
                )

            # Create force_words_ids for constrained generation
            force_words_ids = []
            for keyword in keywords[:5]:  # Limit to top 5 keywords to avoid over-constraining
                # Tokenize keyword and add to force words
                keyword_tokens = self.tokenizer.encode(keyword, add_special_tokens=False)
                if keyword_tokens:
                    force_words_ids.append(keyword_tokens)

            return self.model.generate(
                input_ids,
                max_length=int(max_length),
                min_length=int(min_length),
                length_penalty=1.5,
                num_beams=8,
                early_stopping=True,
                do_sample=False,  # Disable sampling when using force_words_ids
                force_words_ids=force_words_ids if force_words_ids else None,
                no_repeat_ngram_size=3
            )
        except Exception as e:
            print(f"Constrained decoding failed, falling back to standard generation: {e}")
            # Fallback to standard generation
            return self.model.generate(
                input_ids,
                max_length=int(max_length),
                min_length=int(min_length),
                length_penalty=1.5,  # Reduced for more natural length
                num_beams=8,  # Increased for better quality
                early_stopping=True,
                do_sample=True,  # Enable sampling for diversity
                temperature=0.7,  # Add controlled randomness
                top_p=0.9,  # Nucleus sampling
                repetition_penalty=1.2,  # Reduce repetition
                no_repeat_ngram_size=3
            )

    def summarize(self, text, keywords=None, max_length=150, min_length=30, use_constrained=False):
        """
        Generate abstractive summary with optional constrained decoding
        Args:
            text: Input text to summarize
            keywords: List of keywords to constrain generation (from extractive phase)
            use_constrained: Whether to use constrained decoding (disabled due to device issues)
        """
        # Enhanced context-preserving prompt engineering with better instructions
        if keywords and use_constrained:
            # Use keywords but preserve original context with more specific instructions
            keyword_str = ", ".join(keywords[:8])  # Include more keywords for better coverage
            input_text = f"""Please provide a comprehensive and accurate summary of the following text. Your task is to capture all the essential information, main ideas, and key relationships while strictly maintaining the original context and meaning.

IMPORTANT: Focus on these key concepts and ensure they are properly represented: {keyword_str}

Summary requirements:
- Include ALL essential information and main points from the original text
- Preserve the logical flow and relationships between ideas
- Maintain complete factual accuracy - do not add, remove, or alter information
- Avoid hallucinations or introducing concepts not present in the original
- Keep the summary coherent, well-structured, and logically organized
- Use clear, precise language that reflects the original text's tone and style
- Ensure the summary tells the complete story without losing important context

Text to summarize: {text}"""
        else:
            input_text = f"""Create a comprehensive and highly accurate summary of the following text that captures ALL the essential information, main ideas, and key relationships while strictly preserving the original context and meaning.

Critical requirements:
- Include ALL important facts, concepts, and details from the original text
- Maintain the complete logical structure and flow of ideas
- Preserve 100% factual accuracy - never add or alter information
- Avoid any hallucinations or fabricated content
- Keep the summary coherent, well-organized, and contextually complete
- Use precise language that accurately reflects the original text
- Ensure no important information or context is lost

Text to summarize: {text}"""

        inputs = self.tokenizer(
            input_text,
            return_tensors='pt',
            max_length=1024,  # Increased for better context capture
            truncation=True,
            padding=True
        )

        # Temporarily disable constrained decoding due to device compatibility issues
        if use_constrained and keywords:
            try:
                summary_ids = self.constrained_decode(
                    inputs['input_ids'],
                    keywords,
                    max_length=max_length,
                    min_length=min_length
                )
            except Exception as e:
                print(f"Constrained decoding failed, falling back to standard generation: {e}")
                summary_ids = self.model.generate(
                    inputs['input_ids'],
                    max_length=int(max_length),
                    min_length=int(min_length),
                    length_penalty=1.5,
                    num_beams=8,
                    early_stopping=True,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=3
                )
        else:
            summary_ids = self.model.generate(
                inputs['input_ids'],
                max_length=int(max_length),
                min_length=int(min_length),
                length_penalty=1.5,
                num_beams=8,
                early_stopping=True,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                repetition_penalty=1.2
            )

        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        # Post-process to ensure fluency
        summary = self.post_process_summary(summary)

        # Ensure proper encoding for display
        summary = summary.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')

        return summary

    def post_process_summary(self, summary):
        """Enhanced post-processing for better fluency and coherence"""
        import re

        if not summary:
            return summary

        # Capitalize first letter
        summary = summary[0].upper() + summary[1:]

        # Fix sentence capitalization within the summary
        sentences = re.split(r'(?<=[.!?])\s+', summary.strip())
        processed_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 1:
                # Capitalize first letter of each sentence
                sentence = sentence[0].upper() + sentence[1:]
                processed_sentences.append(sentence)

        summary = ' '.join(processed_sentences)

        # Ensure ends with proper punctuation
        if summary and not summary.endswith(('.', '!', '?')):
            summary += '.'

        # Remove extra whitespace and normalize spacing
        summary = re.sub(r'\s+', ' ', summary).strip()

        # Fix common grammatical issues
        summary = re.sub(r'\s+([.,!?;:])', r'\1', summary)  # Remove space before punctuation
        summary = re.sub(r'([.,!?;:])\s+', r'\1 ', summary)  # Ensure space after punctuation

        # Remove trailing punctuation from abbreviations that might be mistaken
        summary = re.sub(r'\b(et al)\.', r'\1', summary, flags=re.IGNORECASE)

        return summary