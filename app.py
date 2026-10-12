import os
import sqlite3
from flask import Flask, render_template
from api.routes import api_bp
from api.version_routes import version_bp, init_vc_db
from api.ai_detection_routes import ai_detection_bp

app = Flask(__name__, 
            static_folder='ui/static',
            template_folder='ui/templates')

# Configure secret key for session-based user authentication
app.secret_key = os.environ.get('SECRET_KEY', 'plagiarism_analyzer_secure_session_key_2026')

# Register the API blueprints
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(version_bp, url_prefix='/api')
app.register_blueprint(ai_detection_bp, url_prefix='/api/ai')

DATABASE_PATH = 'database.db'

def init_db():
    if not os.path.exists(DATABASE_PATH):
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT,
                percentage REAL,
                results TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    init_vc_db()

@app.route('/')
def index():
    return render_template('index.html')

def preload_ai_detector():
    """Warms up the AI content detection model in a background daemon thread."""
    try:
        from core.ai_content_detector import AIContentDetector
        detector = AIContentDetector.get_instance()
        detector.load_model()
    except Exception as e:
        print(f"AI Detector warmup notification: {e}")

if __name__ == '__main__':
    init_db()
    # Ensure data and reports directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    
    # Warm up AI detector asynchronously in the background so it's instantly ready
    import threading
    threading.Thread(target=preload_ai_detector, daemon=True).start()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
