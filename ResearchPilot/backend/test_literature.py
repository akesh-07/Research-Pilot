import requests
import json

payload = {
    "research_question": "Test question",
    "uploaded_files": []
}

try:
    response = requests.post("http://localhost:8000/api/literature/summarize", json=payload)
    print("Status Code:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
