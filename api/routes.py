import os
import sqlite3
import json
from flask import Blueprint, request, jsonify, send_file
from core.analyzer import PlagiarismAnalyzer
from core.report_generator import ReportGenerator
from pypdf import PdfReader
import docx
import io
from datetime import datetime

DATABASE_PATH = 'database.db'

def save_report(text, results):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        pct = results.get('overall_percentage', 0)
        cursor.execute(
            'INSERT INTO reports (text, percentage, results) VALUES (?, ?, ?)',
            (text, pct, json.dumps(results))
        )
        conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        conn.close()

api_bp = Blueprint('api', __name__)

# Initialize analyzer
DATA_ROOT = os.path.join(os.path.dirname(__file__), '..', 'data')
analyzer = PlagiarismAnalyzer(DATA_ROOT)
report_gen = ReportGenerator()

@api_bp.route('/analyze', methods=['POST'])
def analyze_text():
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({"error": "No text provided"}), 400
    
    try:
        results = analyzer.analyze(text)
        save_report(text, results) # Persist to DB
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/reports', methods=['GET'])
def get_reports():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, text, percentage, timestamp FROM reports ORDER BY timestamp DESC')
        reports = []
        for row in cursor.fetchall():
            reports.append({
                "id": row[0],
                "preview": row[1][:100] + "...",
                "percentage": row[2],
                "timestamp": row[3]
            })
        return jsonify(reports)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

from pypdf import PdfReader
import docx

def get_text_from_file(file):
    filename = file.filename.lower()
    content = ""
    try:
        if filename.endswith('.txt'):
            content = file.read().decode('utf-8')
        elif filename.endswith('.pdf'):
            reader = PdfReader(file)
            content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif filename.endswith('.docx'):
            doc = docx.Document(file)
            content = "\n".join([para.text for para in doc.paragraphs])
        return content
    except Exception as e:
        print(f"Error extracting text: {e}")
        return ""

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    content = get_text_from_file(file)
    if not content:
        return jsonify({"error": "Could not extract text or file is unsupported/empty."}), 400
    
    try:
        results = analyzer.analyze(content)
        save_report(content, results)
        return jsonify({
            "text": content,
            "results": results
        })
    except Exception as e:
        return jsonify({"error": f"Failed to process document: {str(e)}"}), 500

@api_bp.route('/multi-check', methods=['POST'])
def multi_check():
    if 'files' not in request.files:
        return jsonify({"error": "No files uploaded"}), 400
    
    files = request.files.getlist('files')
    if not files or (len(files) == 1 and files[0].filename == ''):
        return jsonify({"error": "At least two files are required for comparison."}), 400
    
    documents = []
    for file in files:
        if file.filename == '': continue
        text = get_text_from_file(file)
        if text.strip():
            documents.append({
                "name": file.filename,
                "content": text
            })
    
    if len(documents) < 2:
        return jsonify({"error": "Need at least two documents with readable text."}), 400
    
    try:
        results = analyzer.compare_documents(documents)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/download-report', methods=['POST'])
def download_report():
    data = request.json
    mode = data.get('mode', 'single')
    
    try:
        if mode == 'single':
            text = data.get('text', '')
            results = data.get('results', {})
            pdf_buffer = report_gen.generate_single_report(text, results)
            filename = f"Plagiarism_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            doc_names = data.get('document_names', [])
            matrix = data.get('matrix', {})
            pairwise = data.get('pairwise_results', [])
            pdf_buffer = report_gen.generate_multi_report(doc_names, matrix, pairwise)
            filename = f"Multi_Compare_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

