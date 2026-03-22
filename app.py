from flask import Flask, render_template
from flask_cors import CORS
import os
from api.routes import api_bp

# Note: We configure templates and static to be inside the 'ui' directory
app = Flask(__name__, 
            template_folder='ui/templates', 
            static_folder='ui/static')
CORS(app)

# Register routes
app.register_blueprint(api_bp, url_prefix='/api')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Using 8000 as default to avoid common Windows port 5000 conflicts
    app.run(debug=True, port=8000)

