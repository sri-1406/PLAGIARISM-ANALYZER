import sys
import os

print("--- DIAGNOSTIC CHECK ---")
print(f"Python Version: {sys.version}")
print(f"CWD: {os.getcwd()}")

try:
    import flask
    print("Flask: OK")
except:
    print("Flask: MISSING")

try:
    import sqlite3
    conn = sqlite3.connect('test.db')
    conn.close()
    os.remove('test.db')
    print("SQLite: OK")
except Exception as e:
    print(f"SQLite: ERROR - {e}")

try:
    from api.routes import api_bp
    print("API Routes Import: OK")
except Exception as e:
    print(f"API Routes Import: FAILED - {e}")
    import traceback
    traceback.print_exc()

print("--- END CHECK ---")
