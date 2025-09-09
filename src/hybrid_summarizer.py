from .roberta_extractive import RobertaExtractiveSummarizer
from .t5_abstractive import T5AbstractiveSummarizer

class HybridSummarizer:
    def __init__(self):
        self.extractive = RobertaExtractiveSummarizer()
        self.abstractive = T5AbstractiveSummarizer()

    def summarize(self, text, extractive_sentences=5):
        # Step 1: Extractive summarization
        extracted_text = self.extractive.summarize(text, num_sentences=extractive_sentences)
        # Step 2: Abstractive summarization on extracted text
        final_summary = self.abstractive.summarize(extracted_text)
        return final_summary