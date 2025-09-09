import torch
from transformers import RobertaTokenizer, RobertaModel
import nltk
from nltk.tokenize import sent_tokenize

class RobertaExtractiveSummarizer:
    def __init__(self, model_name='roberta-base'):
        self.tokenizer = RobertaTokenizer.from_pretrained(model_name)
        self.model = RobertaModel.from_pretrained(model_name)
        self.model.eval()
        nltk.download('punkt')

    def get_sentence_embeddings(self, sentences):
        embeddings = []
        for sentence in sentences:
            inputs = self.tokenizer(sentence, return_tensors='pt', truncation=True, max_length=512)
            with torch.no_grad():
                outputs = self.model(**inputs)
            embeddings.append(outputs.last_hidden_state.mean(dim=1).squeeze())
        return torch.stack(embeddings)

    def summarize(self, text, num_sentences=3):
        sentences = sent_tokenize(text)
        if len(sentences) <= num_sentences:
            return text

        embeddings = self.get_sentence_embeddings(sentences)
        # Simple scoring: use first sentence as reference
        ref_embedding = embeddings[0]
        scores = torch.cosine_similarity(embeddings, ref_embedding.unsqueeze(0), dim=1)
        top_indices = torch.topk(scores, num_sentences).indices
        top_sentences = [sentences[i] for i in sorted(top_indices.tolist())]
        return ' '.join(top_sentences)