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
        # NLTK punkt is handled centrally in app.py

    def get_sentence_embeddings(self, sentences):
        """Get embeddings for sentences using RoBERTa"""
        embeddings = []
        for sentence in sentences:
            inputs = self.tokenizer(sentence, return_tensors='pt', truncation=True,
                                   max_length=512, padding=True)
            with torch.no_grad():
                outputs = self.model(**inputs)
            # Use CLS token embedding for sentence representation
            try:
                cls_embedding = outputs.last_hidden_state[:, 0, :].squeeze()
                embeddings.append(cls_embedding.cpu().numpy())
            except Exception as e:
                # Fallback: create a zero tensor with correct shape
                print(f"Warning: Error processing sentence embedding: {e}")
                fallback_embedding = np.zeros(768, dtype=np.float32)
                embeddings.append(fallback_embedding)
        return np.array(embeddings)

    def compute_sentence_scores(self, embeddings, sentences):
        """Enhanced sentence scoring with improved semantic and contextual analysis"""
        scores = np.zeros(len(sentences))

        # Strategy 1: Enhanced position-based scoring with document structure awareness
        for i in range(len(sentences)):
            # Boost first and last sentences significantly
            if i == 0:
                position_score = 1.2  # First sentence often contains main topic
            elif i == len(sentences) - 1:
                position_score = 1.1  # Last sentence often contains conclusion
            else:
                # Gaussian-like distribution peaking at center
                position_score = np.exp(-0.5 * ((i - len(sentences)//2) / (len(sentences)//3))**2)
            scores[i] += position_score * 0.25

        # Strategy 2: Improved length-based scoring with optimal range detection
        lengths = np.array([len(sent.split()) for sent in sentences])
        # Optimal sentence length range (10-25 words) gets highest score
        optimal_length = 17.5  # Middle of optimal range
        length_scores = 1.0 - np.abs(lengths - optimal_length) / optimal_length
        length_scores = np.clip(length_scores, 0.1, 1.0)  # Ensure minimum score
        scores += length_scores * 0.15

        # Strategy 3: Enhanced semantic centrality with multiple reference points
        centroid = np.mean(embeddings, axis=0)
        similarities = cosine_similarity(embeddings, centroid.reshape(1, -1)).flatten()

        # Also compute similarity to first and last sentences as reference points
        if len(sentences) > 2:
            first_sim = cosine_similarity(embeddings, embeddings[0].reshape(1, -1)).flatten()
            last_sim = cosine_similarity(embeddings, embeddings[-1].reshape(1, -1)).flatten()
            # Combine centrality with document flow similarity
            combined_sim = (similarities * 0.6) + (first_sim * 0.2) + (last_sim * 0.2)
            scores += combined_sim * 0.35
        else:
            scores += similarities * 0.35

        # Strategy 4: Enhanced lexical diversity with information density
        lexical_scores = np.array([self._compute_lexical_diversity(sent) for sent in sentences])
        scores += lexical_scores * 0.12

        # Strategy 5: Improved named entity and keyword density
        entity_scores = np.array([self._compute_entity_density(sent) for sent in sentences])
        scores += entity_scores * 0.13

        # Strategy 6: NEW - Sentence connectivity and coherence scoring
        connectivity_scores = self._compute_sentence_connectivity(sentences, embeddings)
        scores += connectivity_scores * 0.1

        return scores

    def _compute_lexical_diversity(self, sentence):
        """Compute lexical diversity score for a sentence"""
        words = sentence.lower().split()
        if len(words) < 3:
            return 0.0

        # Remove common stopwords
        stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        filtered_words = [word for word in words if word not in stop_words]

        if not filtered_words:
            return 0.0

        # Calculate unique word ratio
        unique_ratio = len(set(filtered_words)) / len(filtered_words)
        return min(unique_ratio, 1.0)  # Cap at 1.0

    def _compute_entity_density(self, sentence):
        """Compute named entity density score"""
        words = sentence.split()
        if not words:
            return 0.0

        # Simple heuristics for named entities
        entity_indicators = 0
        capitalized_words = [word for word in words if word and word[0].isupper()]

        # Look for patterns that might indicate named entities
        for i, word in enumerate(words):
            if word and word[0].isupper():
                # Check for title case patterns
                if len(word) > 3:  # Likely a proper noun
                    entity_indicators += 1
                # Check for consecutive capitalized words (multi-word entities)
                if i < len(words) - 1 and words[i+1] and words[i+1][0].isupper():
                    entity_indicators += 0.5

        return min(entity_indicators / len(words), 1.0)

    def _compute_sentence_connectivity(self, sentences, embeddings):
        """Compute sentence connectivity scores based on semantic flow"""
        if len(sentences) < 3:
            return np.ones(len(sentences)) * 0.5  # Neutral score for short texts

        connectivity_scores = np.zeros(len(sentences))

        # Compute pairwise similarities between consecutive sentences
        for i in range(len(sentences) - 1):
            similarity = cosine_similarity(
                embeddings[i].reshape(1, -1),
                embeddings[i+1].reshape(1, -1)
            )[0][0]

            # Boost sentences that connect well to their neighbors
            connectivity_scores[i] += similarity * 0.6
            connectivity_scores[i+1] += similarity * 0.4

        # Normalize scores
        if np.max(connectivity_scores) > 0:
            connectivity_scores = connectivity_scores / np.max(connectivity_scores)

        return connectivity_scores

    def extract_keywords_from_sentences(self, sentences, top_n=20):
        """Enhanced keyword extraction with TF-IDF-like scoring"""
        from collections import Counter
        import re
        import math

        all_text = ' '.join(sentences)
        words = re.findall(r'\b\w+\b', all_text.lower())

        # Enhanced stop words list
        stop_words = set(nltk.corpus.stopwords.words('english'))
        additional_stops = {'also', 'however', 'therefore', 'thus', 'hence', 'accordingly',
                           'consequently', 'similarly', 'likewise', 'moreover', 'furthermore',
                           'additionally', 'besides', 'further', 'then', 'after', 'before'}
        stop_words.update(additional_stops)

        # Filter and clean words
        filtered_words = []
        for word in words:
            if (len(word) > 2 and
                word not in stop_words and
                not word.isdigit() and
                not any(char.isdigit() for char in word)):  # Remove words with numbers
                filtered_words.append(word)

        if not filtered_words:
            return []

        word_freq = Counter(filtered_words)

        # Calculate enhanced scores
        total_words = len(filtered_words)
        keyword_scores = {}

        for word, freq in word_freq.items():
            # TF (Term Frequency) - normalized
            tf = freq / total_words

            # Document frequency penalty (words that appear in too many sentences)
            sentence_count = sum(1 for sent in sentences if word in sent.lower())
            df_penalty = math.log(len(sentences) / (1 + sentence_count))

            # Length bonus (prefer meaningful words)
            length_bonus = min(len(word) / 10, 1.0)

            # Position bonus (words in first/last sentences)
            position_bonus = 0
            if sentences:
                first_sent = sentences[0].lower()
                last_sent = sentences[-1].lower() if len(sentences) > 1 else ""
                if word in first_sent or word in last_sent:
                    position_bonus = 0.2

            # Calculate final score
            score = (tf * 0.5) + (df_penalty * 0.2) + (length_bonus * 0.2) + (position_bonus * 0.1)
            keyword_scores[word] = score

        # Sort by score and return top keywords
        sorted_keywords = sorted(keyword_scores.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_keywords[:top_n]]

    def summarize(self, text, num_sentences=5, over_extract=True):
        """
        Enhanced extractive summarization with comprehensive coverage
        Returns comprehensive set of relevant sentences
        """
        sentences = sent_tokenize(text)
        if len(sentences) <= num_sentences:
            return text, self.extract_keywords_from_sentences(sentences)

        embeddings = self.get_sentence_embeddings(sentences)
        scores = self.compute_sentence_scores(embeddings, sentences)

        # Enhanced over-extraction for better coverage
        if over_extract:
            # Extract more sentences to ensure comprehensive coverage
            extract_count = min(num_sentences * 2, len(sentences))
            # Ensure we have at least 5 sentences for short texts
            extract_count = max(extract_count, min(5, len(sentences)))
        else:
            extract_count = num_sentences

        # Select top sentences based on combined scores
        top_indices = np.argsort(scores)[::-1][:extract_count]
        top_sentences = [sentences[i] for i in sorted(top_indices)]

        # Ensure we capture the most important information
        # Always include the first sentence if it's highly scored
        if 0 not in top_indices and len(sentences) > 3:
            first_score = scores[0]
            if first_score > np.mean(scores):  # If first sentence is above average
                top_sentences.insert(0, sentences[0])

        # Extract keywords from selected sentences
        keywords = self.extract_keywords_from_sentences(top_sentences)

        return ' '.join(top_sentences), keywords