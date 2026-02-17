
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

def test_upload():
    files = [
        ('files', ('test.txt', b'content', 'text/plain'))
    ]
    # We expect this to fail gracefully or process depending on logic
    try:
        response = client.post("/extract", files=files)
        print("Status Code:", response.status_code)
        print("Response JSON:", json.dumps(response.json(), indent=2))
    except Exception as e:
        print("Exception during request:", e)

if __name__ == "__main__":
    from unittest.mock import patch, MagicMock
    from ocr_engine import ocr_engine
    
    # Simple patch to simulate success without full OCR
    def mock_process(content, strategy='original'):
        return []
        
    with patch.object(ocr_engine, 'process_image_with_strategy', side_effect=mock_process):
        test_upload()
