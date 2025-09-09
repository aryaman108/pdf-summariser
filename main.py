from src.hybrid_summarizer import HybridSummarizer

def main():
    summarizer = HybridSummarizer()
    sample_text = """
A kind, old elephant was walking by a river when he saw a wise old crocodile stuck on a shallow sandbank with its tail caught. The crocodile, who was usually known for being selfish, called out to the elephant for help. The elephant, despite knowing the crocodile's nature, decided to help. 
He carefully nudged the sandbank with his trunk, dislodging the crocodile's tail. The crocodile was freed and, in its typical selfish fashion, started to swim away without so much as a thank you. 
"Wait!" called the elephant. "You didn't even thank me for saving your life!" 
The crocodile scoffed, "Why should I? You are a great big elephant, and I am a small crocodile. I am lucky you did not eat me!"
Just then, a wise old owl who had been watching from a nearby tree hooted, "It is not always wise to help those who do not appreciate it."
The elephant realized the owl was right, and from that day on, he learned to choose his friends and those he helped more carefully, understanding that true friendship and appreciation go hand-in-hand. 
This is a classic example of a moral story where the wise old elephant demonstrates kindness, but the selfish crocodile shows a lack of gratitude. The owl's advice highlights a valuable lesson about the importance of gratitude in relationships and the consequences of helping the unappreciative. 
    """
    summary = summarizer.summarize(sample_text)
    print("Original Text Length:", len(sample_text))
    print("Summary:", summary)
    print("Summary Length:", len(summary))

if __name__ == "__main__":
    main()