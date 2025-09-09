from transformers import T5Tokenizer, T5ForConditionalGeneration

class T5AbstractiveSummarizer:
    def __init__(self, model_name='t5-small'):
        self.tokenizer = T5Tokenizer.from_pretrained(model_name)
        self.model = T5ForConditionalGeneration.from_pretrained(model_name)

    def summarize(self, text, max_length=150, min_length=30):
        input_text = "summarize: " + text
        inputs = self.tokenizer.encode(input_text, return_tensors='pt', max_length=512, truncation=True)
        summary_ids = self.model.generate(inputs, max_length=max_length, min_length=min_length, length_penalty=2.0, num_beams=4, early_stopping=True)
        summary = self.tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        return summary