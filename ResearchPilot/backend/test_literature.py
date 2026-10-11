import requests
import json

payload = {
    "research_question": "Machine learning for research workflows and multi-agent systems",
    "uploaded_files": [
        {
            "filename": "MP RP1.pdf",
            "extracted_text_path": "backend/uploads/MP RP1_extracted.txt"
        }
    ],
    "max_web_results": 1
}

try:
    response = requests.post("http://localhost:8000/api/literature/summarize", json=payload)
    print("Status Code:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print("Error:", e)
