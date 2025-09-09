# Text Summarizer with RoBERTa and T5

A hybrid text summarization project using RoBERTa for extractive summarization and T5 for abstractive summarization, based on analysis of 15 research papers.

## Features

- **Hybrid Approach**: Combines extractive (RoBERTa) and abstractive (T5) methods for optimal summarization
- **Research-Backed**: Implements techniques from papers on BERT, RoBERTa, T5, and hybrid summarization
- **Easy to Use**: Simple Python script for quick summarization

## Installation

```bash
pip install transformers torch datasets nltk sentencepiece
```

## Usage

```bash
python main.py
```

## Project Structure

- `main.py`: Main application script
- `src/`: Source code modules
  - `roberta_extractive.py`: RoBERTa-based extractive summarization
  - `t5_abstractive.py`: T5-based abstractive summarization
  - `hybrid_summarizer.py`: Integration of both methods
- `utils/preprocessing.py`: Text preprocessing utilities
- `plan.md`: Detailed project plan and paper analysis

## Example Output

Original text (1231 chars) about AI gets summarized to key points in ~272 characters.

## Research Papers Analyzed

The project is based on analysis of 15 research papers covering:

- Extractive vs Abstractive summarization
- BERT, RoBERTa, T5, GPT models
- Hybrid approaches and fine-tuning techniques
- Consistency loss and reinforcement learning methods

## License

MIT License
