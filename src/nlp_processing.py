from transformers import pipeline

def summarize_text(text):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    summary = summarizer(text, max_length=150, min_length=40, do_sample=False)
    return summary[0]['summary_text']

if __name__ == "__main__":
    # Example text - replace with your extracted PDF text
    sample_text = (
        "Inthispaper,westudytheestimation ofarank-onespikedtensor inthepresenceof "
        "heavy tailed noise. Our results highlight some of the fundamental similarities and dif- "
        "ferences in the tradeoff between statistical and computational efficiencies under heavy "
        "tailed and Gaussian noise. Inparticular ..."
    )
    print("Summary:\n", summarize_text(sample_text))