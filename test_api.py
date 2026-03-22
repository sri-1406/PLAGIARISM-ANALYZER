import requests
import json

url = "http://127.0.0.1:8000/api/analyze"
payload = {"text": "Artificial Intelligence is the simulation of human intelligence processes by machines. This is unique."}


headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
