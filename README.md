# Plagiarism Analyzer (ChartGPT)

A sophisticated plagiarism detection tool designed to analyze documents, compare multiple files, and detect collusion using advanced NLP techniques.

![Plagiarism Analyzer UI](ui/static/screenshot.png)

## 🚀 Features

- **Single Document Analysis**: Paste text or upload a document to check for plagiarism against an indexed dataset.
- **Multi-Compare**: Compare multiple documents simultaneously to identify similarities between them.
- **Collusion Detection**: Specialized algorithms to detect potential collusion between different authors.
- **Dynamic UI**: A modern, responsive interface with Dark Mode support and real-time analysis feedback.
- **Report Generation**: Export detailed plagiarism reports in PDF format.
- **Advanced NLP**: Utilizes TF-IDF vectorization, scikit-learn, and NLTK for high-accuracy text matching.

## 🛠️ Technology Stack

- **Backend**: Python 3.x, Flask
- **Frontend**: HTML5, Vanilla CSS3, JavaScript (ES6+)
- **Database**: SQLite3
- **Data Science**: Scikit-learn, NumPy, NLTK
- **File Handling**: PyPDF2, python-docx
- **Reporting**: ReportLab, FPDF2

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sri-1406/PLAGIARISM-ANALYZER.git
   cd PLAGIARISM-ANALYZER
   ```

2. **Set up a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download NLTK data**:
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('stopwords')
   ```

## 🏃 Usage

1. **Start the application**:
   ```bash
   python app.py
   ```

2. **Access the Web UI**:
   Open your browser and navigate to `http://127.0.0.1:5000`.

3. **Analyze Documents**:
   - Paste text or upload `.pdf`, `.docx`, or `.txt` files.
   - Click "Analyze" to see similarity scores and highlighted matches.

## 📁 Project Structure

- `app.py`: Main entry point and Flask configuration.
- `core/`: Core logic including the analyzer, indexer, and checker.
- `api/`: REST API endpoints for frontend-backend communication.
- `ui/`: Frontend templates (HTML) and static assets (CSS/JS).
- `data/`: Directory for storing reference documents.
- `reports/`: Generated plagiarism reports.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.
