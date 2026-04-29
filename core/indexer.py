import os
import json
import joblib
import nltk
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from .analyzer import PlagiarismAnalyzer

# Configuration
DATA_ROOT = os.path.join(os.path.dirname(__file__), '..', 'data')
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')

if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

def build_index():
    print("--- Starting Indexing Process ---")
    
    # 1. Initialize Analyzer (to use its preprocessing and loading logic)
    analyzer = PlagiarismAnalyzer(DATA_ROOT)
    
    if not analyzer.dataset:
        print("Error: No documents found in data directory.")
        return

    print(f"Loaded {len(analyzer.dataset)} documents.")

    # 2. Prepare all comparison units (Full docs, sentences, and chunks)
    doc_contents = [doc['content'] for doc in analyzer.dataset]
    
    all_sentence_units = []
    unit_to_doc_map = []

    print("Segmenting documents into sentences and sliding windows...")
    for doc in analyzer.dataset:
        doc_sents = sent_tokenize(doc['content'])
        
        # Add individual sentences
        for s in doc_sents:
            s_clean = s.strip()
            if s_clean and len(s_clean.split()) > 5:
                all_sentence_units.append(s_clean)
                unit_to_doc_map.append({
                    "title": doc['title'], 
                    "id": doc['id'],
                    "source_url": doc.get('source_url', doc.get('source', 'N/A'))
                })
        
        # Add sliding windows (2 and 3 sentences)
        for size in [2, 3]:
            windows = analyzer._get_sliding_windows(doc_sents, window_size=size)
            for w in windows:
                all_sentence_units.append(w["text"])
                unit_to_doc_map.append({
                    "title": doc['title'], 
                    "id": doc['id'],
                    "source_url": doc.get('source_url', doc.get('source', 'N/A'))
                })

    print(f"Total comparison units (sentences/chunks): {len(all_sentence_units)}")

    # 3. Train Vectorizer on EVERYTHING to build the full vocabulary
    # We combine doc contents and sentence units for a comprehensive vocabulary
    print("Training TF-IDF Vectorizer...")
    all_text_for_vocab = doc_contents + all_sentence_units
    analyzer.vectorizer.fit(all_text_for_vocab)

    # 4. Precompute Matrices
    print("Precomputing TF-IDF matrices...")
    doc_vectors = analyzer.vectorizer.transform(doc_contents)
    sentence_unit_vectors = analyzer.vectorizer.transform(all_sentence_units)

    # 5. Save everything
    print(f"Saving models to {MODELS_DIR}...")
    joblib.dump(analyzer.vectorizer, os.path.join(MODELS_DIR, 'vectorizer.joblib'))
    joblib.dump(doc_vectors, os.path.join(MODELS_DIR, 'doc_vectors.joblib'))
    joblib.dump(sentence_unit_vectors, os.path.join(MODELS_DIR, 'sentence_unit_vectors.joblib'))
    
    # Save metadata needed for mapping results
    from datetime import datetime
    metadata = {
        "dataset": analyzer.dataset,
        "unit_to_doc_map": unit_to_doc_map,
        "indexed_at": datetime.now().isoformat()
    }
    joblib.dump(metadata, os.path.join(MODELS_DIR, 'metadata.joblib'))

    print("--- Indexing Complete! ---")

if __name__ == "__main__":
    build_index()
