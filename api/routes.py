import os
import sqlite3
import json
from flask import Blueprint, request, jsonify, send_file
from core.analyzer import PlagiarismAnalyzer
from core.report_generator import ReportGenerator
from core.ai_content_detector import AIContentDetector
from pypdf import PdfReader
import docx
import io
from datetime import datetime

DATABASE_PATH = 'database.db'
REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')

# Ensure reports directory exists
if not os.path.exists(REPORTS_DIR):
    os.makedirs(REPORTS_DIR)

def save_report(text, results, filename='pasted_text.txt'):
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        pct = results.get('overall_percentage', 0)
        cursor.execute(
            'INSERT INTO reports (text, percentage, results, filename) VALUES (?, ?, ?, ?)',
            (text, pct, json.dumps(results), filename)
        )
        report_id = cursor.lastrowid
        conn.commit()
        return report_id
    except Exception as e:
        print(f"DB Error: {e}")
        return None
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

        # Seamless AI content analysis integration for single document
        try:
            ai_detector = AIContentDetector.get_instance()
            ai_result = ai_detector.detect(text)
            if ai_result and ai_result.get('valid'):
                results['ai_analysis'] = ai_result
        except Exception as ae:
            print(f"Warning: AI detection during single analysis: {ae}")

        report_id = save_report(text, results) # Persist to DB
        
        # Pre-generate PDF report (safely isolated)
        if report_id:
            try:
                pdf_buffer = report_gen.generate_single_report(
                    text, results,
                    filename="Direct_Text_Input.txt",
                    report_id=report_id,
                    file_type="RAW TEXT"
                )
                report_path = os.path.join(REPORTS_DIR, f"report_{report_id}.pdf")
                with open(report_path, 'wb') as f:
                    f.write(pdf_buffer.getbuffer())
                results['report_id'] = report_id
            except Exception as pe:
                print(f"Warning: PDF report pre-generation skipped ({pe}). Will be generated on demand.")

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/reports', methods=['GET'])
def get_reports():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id, text, percentage, results, timestamp, filename FROM reports ORDER BY id DESC')
        reports = []
        for row in cursor.fetchall():
            res_data = {}
            if row[3]:
                try:
                    res_data = json.loads(row[3])
                except Exception:
                    pass

            text_val = row[1] or ""
            clean_preview = " ".join(text_val.split())
            if len(clean_preview) > 130:
                clean_preview = clean_preview[:130] + "..."

            flagged = res_data.get('plagiarized_sentences', [])
            flagged_count = len(flagged) if isinstance(flagged, list) else (flagged or 0)
            fname = row[5] if (len(row) > 5 and row[5]) else f"document_{row[0]}.txt"

            reports.append({
                "id": row[0],
                "filename": fname,
                "preview": clean_preview,
                "full_text": text_val,
                "percentage": row[2] or 0.0,
                "total_sentences": res_data.get('total_sentences', 0),
                "flagged_sentences": flagged_count,
                "timestamp": row[4]
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
        if hasattr(file, 'seek'):
            file.seek(0)

        if filename.endswith('.txt'):
            raw_bytes = file.read()
            for encoding in ('utf-8', 'utf-8-sig', 'latin-1', 'cp1252'):
                try:
                    content = raw_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            if not content and raw_bytes:
                content = raw_bytes.decode('utf-8', errors='replace')
        elif filename.endswith('.pdf'):
            reader = PdfReader(file)
            page_texts = []
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    page_texts.append(t)
            content = "\n\n".join(page_texts)
        elif filename.endswith('.docx') or filename.endswith('.doc'):
            doc = docx.Document(file)
            content = "\n\n".join([para.text for para in doc.paragraphs if para.text.strip()])

        if hasattr(file, 'seek'):
            file.seek(0)

        return content.strip()
    except Exception as e:
        print(f"Error extracting text from {filename}: {e}")
        return ""

@api_bp.route('/extract-text', methods=['POST'])
def extract_text_endpoint():
    """
    Ultra-fast dedicated text extraction endpoint.
    Extracts text from .txt, .pdf, or .docx files in milliseconds without
    triggering expensive plagiarism analysis or ReportLab PDF generation.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    content = get_text_from_file(file)
    if not content:
        return jsonify({"error": "Could not extract readable text. Ensure file is not empty or corrupted."}), 400
    
    words = content.split()
    return jsonify({
        "success": True,
        "text": content,
        "filename": file.filename,
        "word_count": len(words),
        "char_count": len(content)
    }), 200

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

        # Seamless AI content analysis integration for single document upload
        try:
            ai_detector = AIContentDetector.get_instance()
            ai_result = ai_detector.detect(content)
            if ai_result and ai_result.get('valid'):
                results['ai_analysis'] = ai_result
        except Exception as ae:
            print(f"Warning: AI detection during file upload analysis: {ae}")

        report_id = save_report(content, results, filename=file.filename)
        
        # Pre-generate PDF report (safely isolated from text extraction & analysis)
        if report_id:
            try:
                ext = os.path.splitext(file.filename)[1].lstrip('.').upper() or 'PDF'
                pdf_buffer = report_gen.generate_single_report(
                    content, results,
                    filename=file.filename,
                    report_id=report_id,
                    file_type=ext
                )
                report_path = os.path.join(REPORTS_DIR, f"report_{report_id}.pdf")
                with open(report_path, 'wb') as f:
                    f.write(pdf_buffer.getbuffer())
            except Exception as pe:
                print(f"Warning: PDF report pre-generation skipped ({pe}). Will be generated on demand.")
        
        return jsonify({
            "text": content,
            "results": results,
            "report_id": report_id,
            "ai_analysis": results.get('ai_analysis')
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

        # Seamless AI content analysis integration for multi-documents
        try:
            ai_detector = AIContentDetector.get_instance()
            ai_docs = []
            ai_probs = []
            for doc in documents:
                ai_d = ai_detector.detect(doc['content'])
                ai_info = {
                    "name": doc['name'],
                    "word_count": ai_d.get('word_count', 0),
                    "char_count": ai_d.get('char_count', 0),
                    "ai_probability": ai_d.get('ai_probability', 0.0),
                    "human_probability": ai_d.get('human_probability', 0.0),
                    "classification": ai_d.get('classification', 'Inconclusive'),
                    "confidence": ai_d.get('confidence', 'Moderate'),
                    "is_short_text": ai_d.get('is_short_text', False),
                    "assessment_detail": ai_d.get('assessment_detail', '')
                }
                ai_docs.append(ai_info)
                if not ai_d.get('is_short_text', False):
                    ai_probs.append(ai_d.get('ai_probability', 0.0))

            avg_ai = round(sum(ai_probs) / len(ai_probs), 1) if ai_probs else (
                round(sum(d['ai_probability'] for d in ai_docs) / len(ai_docs), 1) if ai_docs else 0.0
            )
            highest_ai_doc = max(ai_docs, key=lambda x: x['ai_probability']) if ai_docs else None
            ai_flagged_count = sum(1 for d in ai_docs if d.get('classification') == 'Likely AI-generated')
            human_count = sum(1 for d in ai_docs if d.get('classification') == 'Likely human-written')
            mixed_count = len(ai_docs) - ai_flagged_count - human_count

            # Sort documents from low to high by AI Likelihood
            ai_docs.sort(key=lambda x: float(x.get('ai_probability', 0.0)))

            results['ai_analysis'] = {
                "documents": ai_docs,
                "average_ai_probability": avg_ai,
                "highest_ai_doc": highest_ai_doc,
                "ai_flagged_count": ai_flagged_count,
                "human_count": human_count,
                "mixed_count": mixed_count
            }
        except Exception as me:
            print(f"Warning: Multi-document AI detection error: {me}")

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/download/<int:report_id>', methods=['GET'])
def download_report_direct(report_id):
    report_path = os.path.join(REPORTS_DIR, f"report_{report_id}.pdf")
    
    # Always generate/refresh dynamically from database so reports use latest clean formatting
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT text, results, filename FROM reports WHERE id=?', (report_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            text_content, results_json, filename_from_db = row
            results_data = json.loads(results_json) if results_json else {}
            pdf_buffer = report_gen.generate_single_report(
                text_content, results_data,
                filename=filename_from_db,
                report_id=report_id
            )
            with open(report_path, 'wb') as f:
                f.write(pdf_buffer.getbuffer())
    except Exception as e:
        print(f"Error generating fresh report {report_id}: {e}")


    if not os.path.exists(report_path):
        return jsonify({"error": "Report file not found on server."}), 404
        
    try:
        # ULTIMATE HEADER SET: Force the filename and extension at the protocol level
        filename = f"Plagiarism_Report_{report_id}.pdf"
        response = send_file(
            report_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
        response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.headers["Content-Type"] = "application/pdf"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response
    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

@api_bp.route('/download-report', methods=['POST'])
def download_report_legacy():
    # Keep legacy POST for multi-compare or backward compatibility if needed
    data = request.json
    if not data:
        return jsonify({"error": "Missing request data"}), 400
        
    mode = data.get('mode', 'single')
    
    try:
        if mode == 'single':
            text = data.get('text', '')
            results = data.get('results', {})
            filename_val = data.get('filename') or results.get('filename') or results.get('file_name') or "Submitted_Document.pdf"
            report_id_val = results.get('report_id') or data.get('report_id')
            file_type_val = data.get('file_type') or results.get('file_type') or "PDF"
            pdf_buffer = report_gen.generate_single_report(
                text, results,
                filename=filename_val,
                report_id=report_id_val,
                file_type=file_type_val
            )
            filename = f"Plagiarism_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        else:
            doc_names = data.get('document_names', [])
            matrix = data.get('matrix', {})
            pairwise = data.get('pairwise_results', [])
            report_id_val = data.get('report_id')
            ai_analysis_val = data.get('ai_analysis')
            pdf_buffer = report_gen.generate_multi_report(doc_names, matrix, pairwise, report_id=report_id_val, ai_analysis=ai_analysis_val)
            filename = f"Multi_Compare_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return send_file(
            pdf_buffer,
            as_attachment=True,
            download_name=filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

