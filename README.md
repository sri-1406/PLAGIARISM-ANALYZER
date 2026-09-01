# Plagiarism Analyzer (ChartGPT)

A sophisticated plagiarism detection tool designed to analyze documents, compare multiple files, extract handwritten text from images via OCR, and detect collusion using advanced NLP techniques.

![Plagiarism Analyzer UI](ui/static/screenshot.png)

## 🚀 Features

- **Single Document Analysis**: Paste text or upload a document to check for plagiarism against an indexed dataset.
- **Handwritten Text OCR**: Extract handwritten and printed text directly from image uploads (`.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.webp`) using deep learning OCR.
- **Multi-Compare**: Compare multiple documents simultaneously to identify similarities between them.
- **Collusion Detection**: Specialized algorithms to detect potential collusion between different authors.
- **Dynamic UI**: A modern, responsive interface with Dark Mode support and real-time analysis feedback.
- **Report Generation**: Export detailed plagiarism reports in PDF format.
- **Advanced NLP**: Utilizes TF-IDF vectorization, scikit-learn, and NLTK for high-accuracy text matching.

## 🛠️ Technology Stack

- **Backend**: Python 3.x, Flask
- **OCR Engine**: EasyOCR, OpenCV (Image Preprocessing & Contrast Enhancement), PyTesseract
- **Frontend**: HTML5, Vanilla CSS3, JavaScript (ES6+)
- **Database**: SQLite3
- **Data Science**: Scikit-learn, NumPy, NLTK
- **File Handling**: PyPDF2, python-docx, Pillow
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

3. **Analyze Documents & Handwritten Images**:
   - Paste text or upload `.pdf`, `.docx`, `.txt`, or image files (`.png`, `.jpg`, `.jpeg`, etc.).
   - Use the **📷 Handwriting OCR** button to extract text from handwritten notes directly into the editor.
   - Click "Analyze" to see similarity scores and highlighted matches.

## 📁 Project Structure

- `app.py`: Main entry point and Flask configuration.
- `core/`: Core logic including analyzer, indexer, report generator, and `ocr.py` handwriting engine.
- `api/`: REST API endpoints (`/api/analyze`, `/api/upload`, `/api/ocr`, `/api/multi-check`).
- `ui/`: Frontend templates (HTML) and static assets (CSS/JS).
- `data/`: Directory for storing reference documents.
- `reports/`: Generated plagiarism reports.

## 👥 Contributors

- **BINDU C S** ([@just-da-way-im](https://github.com/just-da-way-im)) - Contributor & Developer

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.
