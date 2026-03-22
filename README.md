# AI-Based Plagiarism Analyzer (Phase 1)

A modular plagiarism detection system built with Python (Flask) and natural language processing techniques.

## Features
- **Text & File Input**: Paste text or upload `.txt` files.
- **NLP Processing**: Tokenization, stopword removal, and TF-IDF vectorization.
- **Similarity Detection**:
  - Document-level comparison using Cosine Similarity.
  - Sentence-level matching with a 0.7 similarity threshold.
- **Modern UI**: Clean result dashboard with overall percentage and highlighted matches.

## Project Structure
```text
chartgpt/
├── app.py               # Flask entry point
├── api/
│   └── routes.py        # API endpoints for analysis
├── core/
│   └── analyzer.py      # NLP Logic (TF-IDF, Cosine Similarity)
├── data/
│   └── documents.json   # Sample dataset
├── ui/
│   ├── templates/       # HTML files
│   └── static/          # CSS & JS files
└── requirements.txt     # Python dependencies
```

## Setup Instructions

### 1. Install Dependencies
Ensure you have Python installed. Run the following command in your terminal:
```bash
pip install -r requirements.txt
```

### 2. Run the Application
Start the Flask server:
```bash
python app.py
```

### 3. Access the UI
Open your browser and navigate to:
`http://127.0.0.1:5000`

## Implementation Details
- **TF-IDF**: Used to represent text as numerical vectors.
- **Cosine Similarity**: Measures the orientation of vectors to determine similarity regardless of document length.
- **NLTK**: Handles tokenization and stopword removal for cleaner analysis.
