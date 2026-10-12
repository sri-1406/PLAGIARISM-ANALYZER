import os
from flask import Blueprint, request, jsonify
from core.ai_content_detector import AIContentDetector
from api.routes import get_text_from_file

ai_detection_bp = Blueprint('ai_detection', __name__)

@ai_detection_bp.route('/status', methods=['GET'])
def ai_status():
    """Returns the operational status of the AI Content Detection model."""
    detector = AIContentDetector.get_instance()
    status = detector.get_status()
    return jsonify({
        "success": True,
        "status": status
    }), 200

@ai_detection_bp.route('/detect', methods=['POST'])
def detect_ai_content():
    """
    Dedicated endpoint for AI-generated content detection.
    Accepts raw JSON { "text": "..." } or multipart file upload (.txt, .pdf, .docx).
    Does NOT modify plagiarism calculations or existing database records.
    """
    text_content = ""
    source_filename = None

    # Check for multipart file upload first
    if 'file' in request.files:
        uploaded_file = request.files['file']
        if uploaded_file and uploaded_file.filename != '':
            source_filename = uploaded_file.filename
            text_content = get_text_from_file(uploaded_file)
            if not text_content or not text_content.strip():
                return jsonify({
                    "error": "Could not extract readable text from the uploaded file.",
                    "valid": False
                }), 400

    # Otherwise parse JSON payload
    elif request.is_json:
        payload = request.get_json(silent=True) or {}
        text_content = payload.get('text', '')
    
    # Or fallback to form data
    elif 'text' in request.form:
        text_content = request.form.get('text', '')

    if not text_content or not text_content.strip():
        return jsonify({
            "error": "No text provided for AI content analysis. Please enter text or upload a document.",
            "valid": False
        }), 400

    try:
        detector = AIContentDetector.get_instance()
        analysis = detector.detect(text_content)

        if not analysis.get('valid', False):
            status_code = 400 if "No text" in analysis.get('error', '') else 500
            return jsonify(analysis), status_code

        response_data = {
            "success": True,
            "filename": source_filename,
            **analysis
        }
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({
            "error": f"Internal error during AI content detection: {str(e)}",
            "valid": False
        }), 500
