import os
import sqlite3
import json
from flask import Blueprint, request, jsonify
from core.analyzer import PlagiarismAnalyzer
from pypdf import PdfReader
import docx

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
DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'documents.json')
analyzer = PlagiarismAnalyzer(DATA_PATH)

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

@api_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
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
        else:
            return jsonify({"error": "Unsupported file format. Please use .txt, .pdf, or .docx"}), 400
        
        if not content.strip():
            return jsonify({"error": "Could not extract text from the file or file is empty."}), 400
            
        results = analyzer.analyze(content)
        save_report(content, results) # Persist to DB
        return jsonify({
            "text": content,
            "results": results
        })
    except Exception as e:
        return jsonify({"error": f"Failed to process document: {str(e)}"}), 500

