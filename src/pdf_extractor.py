import pdfplumber
import os

def extract_text_from_pdfs(pdf_folder):
    texts = {}
    for filename in os.listdir(pdf_folder):
        if filename.endswith('.pdf'):
            with pdfplumber.open(os.path.join(pdf_folder, filename)) as pdf:
                text = "\n".join(page.extract_text() for page in pdf.pages if page.extract_text())
                texts[filename] = text
    return texts

if __name__ == "__main__":
    pdf_folder = os.path.join(os.path.dirname(__file__), "../data/pdfs/")
    pdf_texts = extract_text_from_pdfs(pdf_folder)
    for name, text in pdf_texts.items():
        print(f"{name}:\n{text[:500]}...\n")