import os
import argparse
import sys
import docx
from pypdf import PdfReader
from sklearn.metrics.pairwise import cosine_similarity

# Add parent directory to path to find 'core'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.analyzer import PlagiarismAnalyzer

# Initialize analyzer (empty dataset for this tool as we compare provided files)
analyzer = PlagiarismAnalyzer(os.path.join(os.path.dirname(__file__), '..', 'data', 'documents.json'))

def extract_text(file_path):
    """Extract text from .txt, .pdf, or .docx files."""
    ext = os.path.splitext(file_path)[1].lower()
    content = ""
    try:
        if ext == '.txt':
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        elif ext == '.pdf':
            reader = PdfReader(file_path)
            content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext == '.docx':
            doc = docx.Document(file_path)
            content = "\n".join([para.text for para in doc.paragraphs])
        else:
            return None
    except Exception as e:
        return None
    
    return content

def main():
    parser = argparse.ArgumentParser(description="Collusion Detector - Find similarities between multiple student submissions.")
    parser.add_argument("directory", help="Directory containing documents to compare.")
    parser.add_argument("-t", "--threshold", type=float, default=0.5, help="Similarity threshold to report (default 0.5).")
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory.")
        sys.exit(1)

    files = [os.path.join(args.directory, f) for f in os.listdir(args.directory) if os.path.isfile(os.path.join(args.directory, f))]
    docs = []
    
    print(f"[+] Loading {len(files)} files from {args.directory}...")
    for f in files:
        text = extract_text(f)
        if text and len(text.strip()) > 50:
            docs.append({"filename": os.path.basename(f), "content": text})

    if len(docs) < 2:
        print("Error: Need at least 2 valid documents to compare.")
        sys.exit(1)

    print(f"[+] Comparing documents for collusion (internal similarity)...")
    
    # Preprocess all documents for speed
    doc_contents = [d["content"] for d in docs]
    try:
        tfidf_matrix = analyzer.vectorizer.fit_transform(doc_contents)
        similarities = cosine_similarity(tfidf_matrix)

        found = False
        print("\n" + "="*60)
        print("COLLUSION REPORT (Internal Similarity Between Documents)")
        print("="*60)
        
        for i in range(len(docs)):
            for j in range(i + 1, len(docs)):
                score = similarities[i][j]
                if score >= args.threshold:
                    if score >= 0.8:
                        level = "High Plagiarism"
                    elif score >= 0.6:
                        level = "Moderate Plagiarism"
                    else:
                        level = "Low Plagiarism"
                        
                    found = True
                    print(f"(!) {docs[i]['filename']} ↔ {docs[j]['filename']}")
                    print(f"    Similarity: {round(score*100, 2)}% ({level})")
                    print("-" * 30)

        if not found:
            print("No significant internal similarity detected among files.")
            
    except Exception as e:
        print(f"Error during analysis: {e}")

if __name__ == "__main__":
    main()
