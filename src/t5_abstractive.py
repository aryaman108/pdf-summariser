from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

class T5AbstractiveSummarizer:
    def __init__(self, model_name='google/flan-t5-small'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name, torch_dtype=torch.float32)
        # Ensure model is on CPU and properly loaded
        self.model = self.model.to('cpu')
        self.model.eval()

    def constrained_decode(self, input_ids, keywords, max_length=150, min_length=30):
        """Generate summary with constrained decoding to include key terms"""
        if not keywords:
            # Fallback to standard generation
            return self.model.generate(
                input_ids,
                max_length=max_length,
                min_length=min_length,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True,
                do_sample=False
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
            max_length=max_length,
            min_length=min_length,
            length_penalty=2.0,
            num_beams=6,  # Increased beams for better constrained search
            early_stopping=True,
            do_sample=False,
            force_words_ids=force_words_ids if force_words_ids else None,
            no_repeat_ngram_size=3  # Prevent repetition
        )

    def summarize(self, text, keywords=None, max_length=150, min_length=30, use_constrained=False):
        """
        Generate abstractive summary with optional constrained decoding
        Args:
            text: Input text to summarize
            keywords: List of keywords to constrain generation (from extractive phase)
            use_constrained: Whether to use constrained decoding (disabled due to device issues)
        """
        # Prepare input for FLAN-T5
        if keywords and use_constrained:
            # Use keywords in prompt for better grounding
            keyword_str = ", ".join(keywords[:5])
            input_text = f"Summarize the following text, ensuring to include key concepts like {keyword_str}: {text}"
        else:
            input_text = f"Summarize the following text: {text}"

        inputs = self.tokenizer(
            input_text,
            return_tensors='pt',
            max_length=512,
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
                    max_length=max_length,
                    min_length=min_length,
                    length_penalty=2.0,
                    num_beams=4,
                    early_stopping=True,
                    do_sample=False
                )
        else:
            summary_ids = self.model.generate(
                inputs['input_ids'],
                max_length=max_length,
                min_length=min_length,
                length_penalty=2.0,
                num_beams=4,
                early_stopping=True,
                do_sample=False
            )

        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)

        # Post-process to ensure fluency
        summary = self.post_process_summary(summary)

        return summary

    def post_process_summary(self, summary):
        """Post-process summary for better fluency"""
        import re

        # Capitalize first letter
        if summary:
            summary = summary[0].upper() + summary[1:]

        # Ensure ends with proper punctuation
        if summary and not summary.endswith(('.', '!', '?')):
            summary += '.'

        # Remove extra whitespace
        summary = re.sub(r'\s+', ' ', summary).strip()

        return summary