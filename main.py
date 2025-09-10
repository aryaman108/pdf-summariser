from src.hybrid_summarizer import HybridSummarizer
import tkinter as tk
from tkinter import scrolledtext

def summarize_text(input_area, output_area):
    input_text = input_area.get(1.0, tk.END).strip()
    if not input_text:
        output_area.insert(tk.END, "Please enter some text to summarize.\n")
        return

    try:
        summarizer = HybridSummarizer()
        summary = summarizer.summarize(input_text)

        original_length = len(input_text)
        summary_length = len(summary)

        output_area.delete(1.0, tk.END)
        output_area.insert(tk.END, f"Original Text Length: {original_length}\n\n")
        output_area.insert(tk.END, f"Summary:\n{summary}\n\n")
        output_area.insert(tk.END, f"Summary Length: {summary_length} characters\n")
    except Exception as e:
        output_area.delete(1.0, tk.END)
        output_area.insert(tk.END, f"Error during summarization: {str(e)}\n")

def main():
    root = tk.Tk()
    root.title("Hybrid Text Summarizer")
    root.geometry("800x600")
    
    # Input area
    tk.Label(root, text="Enter text to summarize:").pack(pady=5)
    input_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=15)
    input_area.pack(pady=5)
    
    # Sample text button
    def load_sample():
        sample = """
A kind, old elephant was walking by a river when he saw a wise old crocodile stuck on a shallow sandbank with its tail caught. The crocodile, who was usually known for being selfish, called out to the elephant for help. The elephant, despite knowing the crocodile's nature, decided to help. 
He carefully nudged the sandbank with his trunk, dislodging the crocodile's tail. The crocodile was freed and, in its typical selfish fashion, started to swim away without so much as a thank you. 
"Wait!" called the elephant. "You didn't even thank me for saving your life!" 
The crocodile scoffed, "Why should I? You are a great big elephant, and I am a small crocodile. I am lucky you did not eat me!"
Just then, a wise old owl who had been watching from a nearby tree hooted, "It is not always wise to help those who do not appreciate it."
The elephant realized the owl was right, and from that day on, he learned to choose his friends and those he helped more carefully, understanding that true friendship and appreciation go hand-in-hand. 
This is a classic example of a moral story where the wise old elephant demonstrates kindness, but the selfish crocodile shows a lack of gratitude. The owl's advice highlights a valuable lesson about the importance of gratitude in relationships and the consequences of helping the unappreciative. 
        """
        input_area.delete(1.0, tk.END)
        input_area.insert(1.0, sample)
    
    tk.Button(root, text="Load Sample Text", command=load_sample).pack(pady=5)
    
    # Summarize button
    tk.Button(root, text="Summarize", command=lambda: summarize_text(input_area, output_area), bg="lightblue").pack(pady=5)
    
    # Output area
    tk.Label(root, text="Summary Output:").pack(pady=5)
    output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=10)
    output_area.pack(pady=5)
    
    root.mainloop()

if __name__ == "__main__":
    main()