
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app
from extractor import extractor

from ocr_engine import ocr_engine

client = TestClient(app)

import main

def test_strict_deduplication():
    # ... comments ...
    
    # Define mock ...
    def mock_process(content, strategy='original'):
        # ... logic ...
        with open("debug_log.txt", "a") as f:
             f.write(f"Mock called with strategy={strategy}\n")
        text = content.decode('utf-8')
        if text == "phone_us_1":
            return [ ( [[0,0],[100,0],[100,20],[0,20]], "User One", 0.9 ),
                     ( [[0,30],[100,30],[100,50],[0,50]], "(212) 555-1234", 0.9 ) ]
        elif text == "phone_us_2":
            return [ ( [[0,0],[100,0],[100,20],[0,20]], "User One", 0.9 ),
                     ( [[0,30],[100,30],[100,50],[0,50]], "212-555-1234", 0.9 ) ]
        elif text == "phone_us_3":
             return [ ( [[0,0],[100,0],[100,20],[0,20]], "User One Diff Format", 0.9 ),
                     ( [[0,30],[100,30],[100,50],[0,50]], "+1 212 555 1234", 0.9 ) ]
        elif text == "phone_us_new":
            return [ ( [[0,0],[100,0],[100,20],[0,20]], "User Two", 0.9 ),
                     ( [[0,30],[100,30],[100,50],[0,50]], "4155559999", 0.9 ) ]
        elif text == "phone_intl":
            return [ ( [[0,0],[100,0],[100,20],[0,20]], "User Intl", 0.9 ),
                     ( [[0,30],[100,30],[100,50],[0,50]], "+91 99999 88888", 0.9 ) ]
        return []

    # Manual patch
    original_method = main.ocr_engine.process_image_with_strategy
    main.ocr_engine.process_image_with_strategy = mock_process
    
    try:
        # Prepare files
        files = [
            ('files', ('file1.png', b'phone_us_1', 'image/png')),
            ('files', ('file2.png', b'phone_us_2', 'image/png')),
            ('files', ('file3.png', b'phone_us_3', 'image/png')),
            ('files', ('file4.png', b'phone_us_new', 'image/png')),
            ('files', ('file5.png', b'phone_intl', 'image/png')),
        ]

        response = client.post("/extract", files=files)
        assert response.status_code == 200
        results = response.json()['results']
    
        print("Results:", results)
        
        # Check valid phones in results
        valid_phones = [r['phone'] for r in results if r.get('phone')]
        
        assert len(valid_phones) == 3
        # Check unique US normalized
        assert "12125551234" in valid_phones
        assert valid_phones.count("12125551234") == 1
        
        # Check new US normalized
        assert "14155559999" in valid_phones
        
        # Check international
        assert "919999988888" in valid_phones
        
        # Verify result count (duplicates should be skipped/merged)
        assert len(results) == 3
        
    finally:
        main.ocr_engine.process_image_with_strategy = original_method

if __name__ == "__main__":
    test_strict_deduplication()
    print("Test Passed!")
