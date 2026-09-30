import os
import sqlite3
import json
import io
import shutil
from datetime import datetime
from functools import wraps

from flask import Blueprint, request, jsonify, send_file, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from pypdf import PdfReader
import docx

from core.version_comparator import VersionComparator
from core.version_report_generator import VersionReportGenerator

DATABASE_PATH = 'database.db'
VC_STORAGE_ROOT = os.path.join(os.path.dirname(__file__), '..', 'storage', 'version_control')
VC_REPORTS_DIR = os.path.join(VC_STORAGE_ROOT, 'reports')

os.makedirs(VC_REPORTS_DIR, exist_ok=True)

version_bp = Blueprint('version_bp', __name__)
comparator = VersionComparator()
report_generator = VersionReportGenerator()

ALLOWED_EXTENSIONS = {'.txt', '.pdf', '.docx'}

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_vc_db():
    """Ensure Version Control tables exist in database.db safely."""
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS private_document_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            document_name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS private_document_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            version_number INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            extracted_text TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES private_document_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS version_comparisons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            prev_version_id INTEGER NOT NULL,
            new_version_id INTEGER NOT NULL,
            version_similarity REAL NOT NULL,
            matching_percentage REAL NOT NULL,
            statistics TEXT,
            detailed_matches TEXT,
            report_path TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (group_id) REFERENCES private_document_groups(id) ON DELETE CASCADE,
            FOREIGN KEY (prev_version_id) REFERENCES private_document_versions(id) ON DELETE CASCADE,
            FOREIGN KEY (new_version_id) REFERENCES private_document_versions(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({"error": "Authentication required. Please sign in to access Version Control."}), 401
        return f(*args, **kwargs)
    return decorated_function

def extract_text_from_file_object(file_obj, filename):
    """Extract clean text from .txt, .pdf, or .docx upload object."""
    ext = os.path.splitext(filename.lower())[1]
    content = ""
    try:
        if ext == '.txt':
            content = file_obj.read().decode('utf-8', errors='ignore')
        elif ext == '.pdf':
            reader = PdfReader(file_obj)
            content = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif ext == '.docx':
            doc = docx.Document(file_obj)
            content = "\n".join([para.text for para in doc.paragraphs])
        return content.strip()
    except Exception as e:
        print(f"Extraction error for {filename}: {e}")
        return ""

# ==============================================================================
# AUTHENTICATION ROUTES
# ==============================================================================

@version_bp.route('/auth/status', methods=['GET'])
def auth_status():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"authenticated": False, "user": None})
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, email FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        session.clear()
        return jsonify({"authenticated": False, "user": None})
        
    return jsonify({
        "authenticated": True,
        "user": {
            "id": user['id'],
            "name": user['name'],
            "email": user['email']
        }
    })

@version_bp.route('/auth/register', methods=['POST'])
def auth_register():
    data = request.json or request.form
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not name or not email or not password:
        return jsonify({"error": "All fields (name, email, password) are required."}), 400
    if len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters long."}), 400
    if '@' not in email:
        return jsonify({"error": "Please enter a valid email address."}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE email=?", (email,))
    if c.fetchone():
        conn.close()
        return jsonify({"error": "An account with this email already exists. Please log in."}), 409

    pwd_hash = generate_password_hash(password)
    c.execute("INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)", (name, email, pwd_hash))
    user_id = c.lastrowid
    conn.commit()
    conn.close()

    session['user_id'] = user_id
    session['user_name'] = name
    session['user_email'] = email

    return jsonify({
        "success": True,
        "message": "Account created successfully.",
        "user": {"id": user_id, "name": name, "email": email}
    })

@version_bp.route('/auth/login', methods=['POST'])
def auth_login():
    data = request.json or request.form
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, name, email, password_hash FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()

    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({"error": "Invalid email or password. Please try again."}), 401

    session['user_id'] = user['id']
    session['user_name'] = user['name']
    session['user_email'] = user['email']

    return jsonify({
        "success": True,
        "message": "Logged in successfully.",
        "user": {"id": user['id'], "name": user['name'], "email": user['email']}
    })

@version_bp.route('/auth/logout', methods=['POST'])
def auth_logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})

# ==============================================================================
# VERSION CONTROL — DOCUMENT GROUPS & VERSIONS
# ==============================================================================

@version_bp.route('/vc/groups', methods=['GET'])
@login_required
def get_document_groups():
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    
    # Query groups with version counts and latest update
    c.execute('''
        SELECT g.id, g.document_name, g.created_at,
               COUNT(v.id) as version_count,
               MAX(v.version_number) as latest_version,
               MAX(v.created_at) as last_updated
        FROM private_document_groups g
        LEFT JOIN private_document_versions v ON g.id = v.group_id
        WHERE g.user_id = ?
        GROUP BY g.id
        ORDER BY g.id DESC
    ''', (user_id,))
    
    groups = []
    for row in c.fetchall():
        groups.append({
            "id": row['id'],
            "name": row['document_name'],
            "document_name": row['document_name'],
            "created_at": row['created_at'],
            "version_count": row['version_count'],
            "latest_version": row['latest_version'] or 1,
            "last_updated": row['last_updated'] or row['created_at']
        })

    # Query total statistics for user dashboard
    c.execute('''
        SELECT COUNT(v.id) as total_versions
        FROM private_document_groups g
        JOIN private_document_versions v ON g.id = v.group_id
        WHERE g.user_id = ?
    ''', (user_id,))
    total_versions_row = c.fetchone()
    total_versions = total_versions_row['total_versions'] if total_versions_row else len(groups)

    c.execute("SELECT COUNT(id) as total_comps FROM version_comparisons WHERE user_id = ?", (user_id,))
    total_comps_row = c.fetchone()
    total_comps = total_comps_row['total_comps'] if total_comps_row else 0

    conn.close()
    return jsonify({
        "groups": groups,
        "total_groups": len(groups),
        "total_versions": total_versions,
        "total_comparisons": total_comps
    })

@version_bp.route('/vc/groups', methods=['POST'])
@login_required
def create_document_group():
    user_id = session['user_id']
    doc_name = (request.form.get('document_name') or request.form.get('name') or '').strip()
    
    if 'file' not in request.files:
        return jsonify({"error": "Initial document file is required to create a Version Control group."}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({"error": "No file selected."}), 400
        
    orig_filename = secure_filename(file.filename) or "document_v1.txt"
    ext = os.path.splitext(orig_filename.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Unsupported file format. Please upload .pdf, .docx, or .txt documents."}), 400

    if not doc_name:
        # Default to file base name without extension
        doc_name = os.path.splitext(orig_filename)[0].replace('_', ' ').replace('-', ' ').title()

    extracted_text = extract_text_from_file_object(file, orig_filename)
    if not extracted_text:
        return jsonify({"error": "Could not extract readable text from document. Ensure document is not empty or encrypted."}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO private_document_groups (user_id, document_name) VALUES (?, ?)", (user_id, doc_name))
    group_id = c.lastrowid

    # Create permanent isolated directory structure:
    # storage/version_control/user_<id>/document_<group_id>/version_1/
    version_dir = os.path.join(VC_STORAGE_ROOT, f"user_{user_id}", f"document_{group_id}", "version_1")
    os.makedirs(version_dir, exist_ok=True)
    permanent_file_path = os.path.join(version_dir, orig_filename)

    file.seek(0)
    file.save(permanent_file_path)

    c.execute('''
        INSERT INTO private_document_versions 
        (group_id, user_id, version_number, filename, file_path, extracted_text)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (group_id, user_id, 1, orig_filename, permanent_file_path, extracted_text))
    version_id = c.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": f"Document Group '{doc_name}' created with Version 1.",
        "group_id": group_id,
        "version_id": version_id,
        "version_number": 1,
        "document_name": doc_name
    })

@version_bp.route('/vc/groups/<int:group_id>', methods=['GET'])
@login_required
def get_group_details(group_id):
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    # Strict ownership check
    c.execute("SELECT id, document_name, created_at FROM private_document_groups WHERE id=? AND user_id=?", (group_id, user_id))
    group = c.fetchone()
    if not group:
        conn.close()
        return jsonify({"error": "Document group not found or unauthorized."}), 404

    # Versions list
    c.execute('''
        SELECT id, version_number, filename, file_path, created_at 
        FROM private_document_versions 
        WHERE group_id=? AND user_id=?
        ORDER BY version_number ASC
    ''', (group_id, user_id))
    
    versions = []
    for row in c.fetchall():
        file_size = 0
        if os.path.exists(row['file_path']):
            file_size = os.path.getsize(row['file_path'])
        
        ext = os.path.splitext(row['filename'])[1].upper().lstrip('.') or 'TXT'
        versions.append({
            "id": row['id'],
            "version_number": row['version_number'],
            "filename": row['filename'],
            "file_type": ext,
            "file_size": file_size,
            "created_at": row['created_at']
        })

    # Comparisons history
    c.execute('''
        SELECT c.id, c.prev_version_id, c.new_version_id, c.version_similarity, 
               c.matching_percentage, c.created_at,
               v1.version_number as v1_num, v1.filename as v1_name,
               v2.version_number as v2_num, v2.filename as v2_name
        FROM version_comparisons c
        JOIN private_document_versions v1 ON c.prev_version_id = v1.id
        JOIN private_document_versions v2 ON c.new_version_id = v2.id
        WHERE c.group_id=? AND c.user_id=?
        ORDER BY c.id DESC
    ''', (group_id, user_id))

    comparisons = []
    for row in c.fetchall():
        comparisons.append({
            "id": row['id'],
            "prev_version_id": row['prev_version_id'],
            "new_version_id": row['new_version_id'],
            "v1_num": row['v1_num'],
            "v1_name": row['v1_name'],
            "v2_num": row['v2_num'],
            "v2_name": row['v2_name'],
            "version_similarity": row['version_similarity'],
            "matching_percentage": row['matching_percentage'],
            "created_at": row['created_at']
        })

    conn.close()

    return jsonify({
        "group": {
            "id": group['id'],
            "document_name": group['document_name'],
            "created_at": group['created_at']
        },
        "versions": versions,
        "comparisons": comparisons
    })

@version_bp.route('/vc/groups/<int:group_id>', methods=['DELETE'])
@login_required
def delete_document_group(group_id):
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    # Strict ownership check
    c.execute("SELECT id FROM private_document_groups WHERE id=? AND user_id=?", (group_id, user_id))
    group = c.fetchone()
    if not group:
        conn.close()
        return jsonify({"error": "Document group not found or unauthorized."}), 404

    # Remove storage files for this group
    group_storage_dir = os.path.join(VC_STORAGE_ROOT, f"user_{user_id}", f"document_{group_id}")
    if os.path.exists(group_storage_dir):
        try:
            shutil.rmtree(group_storage_dir)
        except Exception as e:
            print(f"Error removing group files: {e}")

    # Remove database entries (cascades)
    c.execute("DELETE FROM version_comparisons WHERE group_id=? AND user_id=?", (group_id, user_id))
    c.execute("DELETE FROM private_document_versions WHERE group_id=? AND user_id=?", (group_id, user_id))
    c.execute("DELETE FROM private_document_groups WHERE id=? AND user_id=?", (group_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Document group and all versions deleted successfully."})

@version_bp.route('/vc/groups/<int:group_id>/versions', methods=['POST'])
@login_required
def upload_new_version(group_id):
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    # Strict ownership check
    c.execute("SELECT id, document_name FROM private_document_groups WHERE id=? AND user_id=?", (group_id, user_id))
    group = c.fetchone()
    if not group:
        conn.close()
        return jsonify({"error": "Document group not found or unauthorized."}), 404

    if 'file' not in request.files:
        conn.close()
        return jsonify({"error": "File is required."}), 400

    file = request.files['file']
    if not file or file.filename == '':
        conn.close()
        return jsonify({"error": "No file selected."}), 400

    orig_filename = secure_filename(file.filename) or "document_new_version.txt"
    ext = os.path.splitext(orig_filename.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        conn.close()
        return jsonify({"error": "Unsupported format. Only .pdf, .docx, and .txt documents are supported."}), 400

    extracted_text = extract_text_from_file_object(file, orig_filename)
    if not extracted_text:
        conn.close()
        return jsonify({"error": "Could not extract readable text from document."}), 400

    # Calculate next version number
    c.execute("SELECT MAX(version_number) FROM private_document_versions WHERE group_id=? AND user_id=?", (group_id, user_id))
    row = c.fetchone()
    next_ver = (row[0] or 1) + 1

    # Isolated physical storage
    version_dir = os.path.join(VC_STORAGE_ROOT, f"user_{user_id}", f"document_{group_id}", f"version_{next_ver}")
    os.makedirs(version_dir, exist_ok=True)
    permanent_file_path = os.path.join(version_dir, orig_filename)

    file.seek(0)
    file.save(permanent_file_path)

    c.execute('''
        INSERT INTO private_document_versions 
        (group_id, user_id, version_number, filename, file_path, extracted_text)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (group_id, user_id, next_ver, orig_filename, permanent_file_path, extracted_text))
    new_version_id = c.lastrowid
    conn.commit()

    # Optional immediate comparison
    compare_with_id = request.form.get('compare_with_version_id')
    comparison_response = None

    if compare_with_id:
        try:
            compare_with_id = int(compare_with_id)
            c.execute("SELECT id, version_number, filename, extracted_text FROM private_document_versions WHERE id=? AND group_id=? AND user_id=?", (compare_with_id, group_id, user_id))
            base_ver = c.fetchone()
            if base_ver:
                v1_info = {"id": base_ver['id'], "version_number": base_ver['version_number'], "filename": base_ver['filename']}
                v2_info = {"id": new_version_id, "version_number": next_ver, "filename": orig_filename}

                comp_result = comparator.compare_versions(
                    base_ver['extracted_text'],
                    extracted_text,
                    v1_name=f"Version {base_ver['version_number']}",
                    v2_name=f"Version {next_ver}"
                )

                c.execute('''
                    INSERT INTO version_comparisons 
                    (user_id, group_id, prev_version_id, new_version_id, version_similarity, matching_percentage, statistics, detailed_matches)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, group_id, base_ver['id'], new_version_id,
                    comp_result['version_similarity'],
                    comp_result['matching_percentage'],
                    json.dumps(comp_result['statistics']),
                    json.dumps(comp_result['detailed_comparison'])
                ))
                comp_id = c.lastrowid

                # Pre-generate PDF report
                pdf_buf = report_generator.generate_report(
                    group_name=group['document_name'],
                    v1_info=v1_info,
                    v2_info=v2_info,
                    comparison_data=comp_result,
                    user_name=session.get('user_name', 'Authorized User'),
                    report_id=comp_id
                )
                rep_path = os.path.join(VC_REPORTS_DIR, f"report_vc_{comp_id}.pdf")
                with open(rep_path, 'wb') as rf:
                    rf.write(pdf_buf.getbuffer())

                c.execute("UPDATE version_comparisons SET report_path=? WHERE id=?", (rep_path, comp_id))
                conn.commit()

                comparison_response = {
                    "id": comp_id,
                    "comparison_id": comp_id,
                    "v1_info": v1_info,
                    "v2_info": v2_info,
                    "prev_version": v1_info,
                    "new_version": v2_info,
                    "version_similarity": comp_result['version_similarity'],
                    "matching_percentage": comp_result['matching_percentage'],
                    "statistics": comp_result['statistics'],
                    "detailed_matches": comp_result['detailed_comparison'],
                    "detailed_comparison": comp_result['detailed_comparison'],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            print(f"Auto-comparison error: {e}")

    conn.close()

    return jsonify({
        "success": True,
        "message": f"Version {next_ver} uploaded successfully.",
        "version_id": new_version_id,
        "version_number": next_ver,
        "filename": orig_filename,
        "comparison": comparison_response
    })

# ==============================================================================
# VERSION COMPARISON ENDPOINTS
# ==============================================================================

@version_bp.route('/vc/compare', methods=['POST'])
@login_required
def compare_arbitrary_versions():
    user_id = session['user_id']
    data = request.json or {}
    v1_id = data.get('v1_id')
    v2_id = data.get('v2_id')

    if not v1_id or not v2_id:
        return jsonify({"error": "Both v1_id and v2_id are required for comparison."}), 400

    try:
        v1_id = int(v1_id)
        v2_id = int(v2_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid version ID format."}), 400

    if v1_id == v2_id:
        return jsonify({"error": "Please select two different versions to compare."}), 400

    conn = get_db()
    c = conn.cursor()

    # Strict ownership check on both versions
    c.execute('''
        SELECT v.id, v.group_id, v.version_number, v.filename, v.extracted_text, g.document_name
        FROM private_document_versions v
        JOIN private_document_groups g ON v.group_id = g.id
        WHERE v.id IN (?, ?) AND v.user_id = ?
    ''', (v1_id, v2_id, user_id))
    rows = c.fetchall()

    if len(rows) != 2:
        conn.close()
        return jsonify({"error": "One or both versions not found or unauthorized."}), 404

    # Determine which is base and which is revision
    row_map = {int(r['id']): r for r in rows}
    r1 = row_map.get(v1_id)
    r2 = row_map.get(v2_id)

    if not r1 or not r2:
        conn.close()
        return jsonify({"error": "One or both versions not found or unauthorized."}), 404

    if r1['group_id'] != r2['group_id']:
        conn.close()
        return jsonify({"error": "Cannot compare versions from different document groups."}), 400

    group_id = r1['group_id']
    group_name = r1['document_name']

    v1_info = {"id": r1['id'], "version_number": r1['version_number'], "filename": r1['filename']}
    v2_info = {"id": r2['id'], "version_number": r2['version_number'], "filename": r2['filename']}

    comp_result = comparator.compare_versions(
        r1['extracted_text'],
        r2['extracted_text'],
        v1_name=f"Version {r1['version_number']}",
        v2_name=f"Version {r2['version_number']}"
    )

    c.execute('''
        INSERT INTO version_comparisons 
        (user_id, group_id, prev_version_id, new_version_id, version_similarity, matching_percentage, statistics, detailed_matches)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id, group_id, r1['id'], r2['id'],
        comp_result['version_similarity'],
        comp_result['matching_percentage'],
        json.dumps(comp_result['statistics']),
        json.dumps(comp_result['detailed_comparison'])
    ))
    comp_id = c.lastrowid

    # Pre-generate PDF report
    pdf_buf = report_generator.generate_report(
        group_name=group_name,
        v1_info=v1_info,
        v2_info=v2_info,
        comparison_data=comp_result,
        user_name=session.get('user_name', 'Authorized User'),
        report_id=comp_id
    )
    rep_path = os.path.join(VC_REPORTS_DIR, f"report_vc_{comp_id}.pdf")
    with open(rep_path, 'wb') as rf:
        rf.write(pdf_buf.getbuffer())

    c.execute("UPDATE version_comparisons SET report_path=? WHERE id=?", (rep_path, comp_id))
    conn.commit()
    conn.close()

    comp_obj = {
        "id": comp_id,
        "comparison_id": comp_id,
        "group_id": group_id,
        "group_name": group_name,
        "v1_info": v1_info,
        "v2_info": v2_info,
        "prev_version": v1_info,
        "new_version": v2_info,
        "version_similarity": comp_result['version_similarity'],
        "matching_percentage": comp_result['matching_percentage'],
        "statistics": comp_result['statistics'],
        "detailed_matches": comp_result['detailed_comparison'],
        "detailed_comparison": comp_result['detailed_comparison'],
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return jsonify({
        "success": True,
        "comparison": comp_obj,
        "comparison_id": comp_id,
        "group_id": group_id,
        "group_name": group_name,
        "v1_info": v1_info,
        "v2_info": v2_info,
        "prev_version": v1_info,
        "new_version": v2_info,
        "version_similarity": comp_result['version_similarity'],
        "matching_percentage": comp_result['matching_percentage'],
        "statistics": comp_result['statistics'],
        "detailed_matches": comp_result['detailed_comparison'],
        "detailed_comparison": comp_result['detailed_comparison']
    })

@version_bp.route('/vc/comparisons/<int:comparison_id>', methods=['GET'])
@login_required
def get_comparison_result(comparison_id):
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    # Strict ownership check
    c.execute('''
        SELECT c.*, g.document_name,
               v1.version_number as v1_num, v1.filename as v1_name,
               v2.version_number as v2_num, v2.filename as v2_name
        FROM version_comparisons c
        JOIN private_document_groups g ON c.group_id = g.id
        JOIN private_document_versions v1 ON c.prev_version_id = v1.id
        JOIN private_document_versions v2 ON c.new_version_id = v2.id
        WHERE c.id=? AND c.user_id=?
    ''', (comparison_id, user_id))
    comp = c.fetchone()
    conn.close()

    if not comp:
        return jsonify({"error": "Comparison record not found or unauthorized."}), 404

    stats = json.loads(comp['statistics']) if comp['statistics'] else {}
    detailed = json.loads(comp['detailed_matches']) if comp['detailed_matches'] else []

    v1_info = {"id": comp['prev_version_id'], "version_number": comp['v1_num'], "filename": comp['v1_name']}
    v2_info = {"id": comp['new_version_id'], "version_number": comp['v2_num'], "filename": comp['v2_name']}

    comp_obj = {
        "id": comp['id'],
        "comparison_id": comp['id'],
        "group_id": comp['group_id'],
        "group_name": comp['document_name'],
        "created_at": comp['created_at'],
        "v1_info": v1_info,
        "v2_info": v2_info,
        "prev_version": v1_info,
        "new_version": v2_info,
        "version_similarity": comp['version_similarity'],
        "matching_percentage": comp['matching_percentage'],
        "statistics": stats,
        "detailed_matches": detailed,
        "detailed_comparison": detailed
    }

    return jsonify({
        "comparison": comp_obj,
        "comparison_id": comp['id'],
        "group_id": comp['group_id'],
        "group_name": comp['document_name'],
        "created_at": comp['created_at'],
        "v1_info": v1_info,
        "v2_info": v2_info,
        "prev_version": v1_info,
        "new_version": v2_info,
        "version_similarity": comp['version_similarity'],
        "matching_percentage": comp['matching_percentage'],
        "statistics": stats,
        "detailed_matches": detailed,
        "detailed_comparison": detailed
    })

@version_bp.route('/vc/comparisons/<int:comparison_id>/report', methods=['GET'])
@login_required
def download_comparison_report(comparison_id):
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    # Strict ownership check
    c.execute('''
        SELECT c.*, g.document_name,
               v1.version_number as v1_num, v1.filename as v1_name, v1.extracted_text as v1_text,
               v2.version_number as v2_num, v2.filename as v2_name, v2.extracted_text as v2_text
        FROM version_comparisons c
        JOIN private_document_groups g ON c.group_id = g.id
        JOIN private_document_versions v1 ON c.prev_version_id = v1.id
        JOIN private_document_versions v2 ON c.new_version_id = v2.id
        WHERE c.id=? AND c.user_id=?
    ''', (comparison_id, user_id))
    comp = c.fetchone()
    conn.close()

    if not comp:
        return jsonify({"error": "Comparison report not found or unauthorized."}), 404

    rep_path = comp['report_path']
    if not rep_path or not os.path.exists(rep_path):
        # Regenerate dynamically
        v1_info = {"id": comp['prev_version_id'], "version_number": comp['v1_num'], "filename": comp['v1_name']}
        v2_info = {"id": comp['new_version_id'], "version_number": comp['v2_num'], "filename": comp['v2_name']}
        
        comp_data = {
            "version_similarity": comp['version_similarity'],
            "matching_percentage": comp['matching_percentage'],
            "statistics": json.loads(comp['statistics']) if comp['statistics'] else {},
            "detailed_comparison": json.loads(comp['detailed_matches']) if comp['detailed_matches'] else []
        }
        
        pdf_buf = report_generator.generate_report(
            group_name=comp['document_name'],
            v1_info=v1_info,
            v2_info=v2_info,
            comparison_data=comp_data,
            user_name=session.get('user_name', 'Authorized User'),
            report_id=comp['id']
        )
        rep_path = os.path.join(VC_REPORTS_DIR, f"report_vc_{comparison_id}.pdf")
        with open(rep_path, 'wb') as rf:
            rf.write(pdf_buf.getbuffer())

    download_name = f"Version_Similarity_Report_V{comp['v1_num']}_vs_V{comp['v2_num']}.pdf"
    return send_file(
        rep_path,
        as_attachment=True,
        download_name=download_name,
        mimetype='application/pdf'
    )

@version_bp.route('/vc/versions/<int:version_id>/download', methods=['GET'])
@login_required
def download_version_file(version_id):
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    # Strict ownership check
    c.execute("SELECT filename, file_path FROM private_document_versions WHERE id=? AND user_id=?", (version_id, user_id))
    ver = c.fetchone()
    conn.close()

    if not ver or not os.path.exists(ver['file_path']):
        return jsonify({"error": "Version file not found on server or unauthorized."}), 404

    return send_file(
        ver['file_path'],
        as_attachment=True,
        download_name=ver['filename']
    )

@version_bp.route('/vc/versions/<int:version_id>', methods=['DELETE'])
@login_required
def delete_version(version_id):
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()

    # Strict ownership check
    c.execute("SELECT id, group_id, file_path FROM private_document_versions WHERE id=? AND user_id=?", (version_id, user_id))
    ver = c.fetchone()
    if not ver:
        conn.close()
        return jsonify({"error": "Version not found or unauthorized."}), 404

    # Ensure this is not the only version in group
    c.execute("SELECT COUNT(*) FROM private_document_versions WHERE group_id=? AND user_id=?", (ver['group_id'], user_id))
    count = c.fetchone()[0]
    if count <= 1:
        conn.close()
        return jsonify({"error": "Cannot delete the sole version of a document group. Delete the entire document group instead."}), 400

    # Delete physical file
    if os.path.exists(ver['file_path']):
        try:
            os.remove(ver['file_path'])
        except Exception as e:
            print(f"Error removing version file: {e}")

    # Remove comparisons referencing this version
    c.execute("DELETE FROM version_comparisons WHERE (prev_version_id=? OR new_version_id=?) AND user_id=?", (version_id, version_id, user_id))
    # Delete version record
    c.execute("DELETE FROM private_document_versions WHERE id=? AND user_id=?", (version_id, user_id))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Version deleted successfully."})
