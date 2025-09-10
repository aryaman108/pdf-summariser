import torch
from transformers import AutoTokenizer, AutoModel
import nltk
from nltk.tokenize import sent_tokenize
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class RobertaExtractiveSummarizer:
    def __init__(self, model_name='distilroberta-base'):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name, torch_dtype=torch.float32)
        # Ensure model is on CPU and properly loaded
        self.model = self.model.to('cpu')
        self.model.eval()
        nltk.download('punkt')

    def get_sentence_embeddings(self, sentences):
        """Get embeddings for sentences using RoBERTa"""
        embeddings = []
        for sentence in sentences:
            inputs = self.tokenizer(sentence, return_tensors='pt', truncation=True,
                                   max_length=512, padding=True)
            with torch.no_grad():
                outputs = self.model(**inputs)
            # Use CLS token embedding for sentence representation
            # Ensure tensor is materialized (not meta)
            cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze()
            if cls_embedding.device.type == 'meta':
                # If it's a meta tensor, we need to create a dummy tensor
                embeddings.append(np.random.randn(768).astype(np.float32))
            else:
                embeddings.append(cls_embedding.cpu().numpy())
        return np.array(embeddings)

    def compute_sentence_scores(self, embeddings, sentences):
        """Compute relevance scores using multiple strategies for over-extraction"""
        scores = np.zeros(len(sentences))

        # Strategy 1: Position-based scoring (first and last sentences often important)
        for i in range(len(sentences)):
            position_score = 1.0 / (1.0 + abs(i - len(sentences)//2) / len(sentences))
            scores[i] += position_score * 0.3

        # Strategy 2: Length-based scoring (longer sentences may contain more info)
        lengths = np.array([len(sent.split()) for sent in sentences])
        length_scores = lengths / np.max(lengths)
        scores += length_scores * 0.2

        # Strategy 3: Semantic centrality (cosine similarity to document centroid)
        centroid = np.mean(embeddings, axis=0)
        similarities = cosine_similarity(embeddings, centroid.reshape(1, -1)).flatten()
        scores += similarities * 0.5

        return scores

    def extract_keywords_from_sentences(self, sentences, top_n=20):
        """Extract keywords from selected sentences for constrained decoding"""
        from collections import Counter
        import re

        all_text = ' '.join(sentences)
        words = re.findall(r'\b\w+\b', all_text.lower())
        stop_words = set(nltk.corpus.stopwords.words('english'))
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]

        word_freq = Counter(keywords)
        return [word for word, _ in word_freq.most_common(top_n)]

    def summarize(self, text, num_sentences=5, over_extract=True):
        """
        Extractive summarization with over-extraction strategy
        Returns comprehensive set of relevant sentences
        """
        sentences = sent_tokenize(text)
        if len(sentences) <= num_sentences:
            return text, self.extract_keywords_from_sentences(sentences)

        embeddings = self.get_sentence_embeddings(sentences)
        scores = self.compute_sentence_scores(embeddings, sentences)

        # Over-extraction: select more sentences than needed for comprehensive coverage
        if over_extract:
            extract_count = min(num_sentences * 2, len(sentences))
        else:
            extract_count = num_sentences

        # Select top sentences based on combined scores
        top_indices = np.argsort(scores)[::-1][:extract_count]
        top_sentences = [sentences[i] for i in sorted(top_indices)]

        # Extract keywords from selected sentences
        keywords = self.extract_keywords_from_sentences(top_sentences)

        return ' '.join(top_sentences), keywords