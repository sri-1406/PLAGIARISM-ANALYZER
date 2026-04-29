import os
import sqlite3
from flask import Flask, render_template
from api.routes import api_bp

app = Flask(__name__, 
            static_folder='ui/static',
            template_folder='ui/templates')

# Register the API blueprint
app.register_blueprint(api_bp, url_prefix='/api')

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

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    # Ensure data and reports directories exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('reports', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
