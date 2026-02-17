
import pytest
from extractor import extractor
from fastapi.testclient import TestClient
from main import app
from unittest.mock import MagicMock, patch

client = TestClient(app)

def test_normalize_phone():
    """Test phone number normalization directly."""
    assert extractor.normalize_phone("+1 123-456-7890") == "11234567890"  # Normalized to start with 1
    assert extractor.normalize_phone("(123) 456-7890") == "11234567890"   # Normalized to start with 1
    assert extractor.normalize_phone("123 456 7890") == "11234567890"     # Normalized to start with 1
    assert extractor.normalize_phone("+91 99999 88888") == "919999988888" # International kept as is
    assert extractor.normalize_phone("123.456.7890") == "11234567890"     # Normalized to start with 1
    assert extractor.normalize_phone("") == ""
    assert extractor.normalize_phone(None) == ""

@patch('ocr_engine.ocr_engine')
def test_deduplication(mock_ocr_engine):
    """Test that duplicate phone numbers are removed from the response."""
    
    # Mock OCR results to return the same phone number for multiple files
    # file1 has contact1
    # file2 has contact1 (duplicate)
    
    # We need to mock process_image_with_strategy and extract_contacts interactions
    # But since main.py imports extractor and calls it, we can just mock what ocr returns
    # and let the real extractor do its job, OR clearer: mock extractor.extract_contacts to return fixed data
    
    with patch('extractor.extractor.extract_contacts') as mock_extract:
        # File 1 returns Contact A
        # File 2 returns Contact A
        # File 3 returns Contact B
        
        contact_a = {
            "name": "User A", 
            "phone": "1234567890", 
            "confidence": 0.9, 
            "raw_text": "text"
        }
        
        contact_b = {
            "name": "User B", 
            "phone": "0987654321", 
            "confidence": 0.95, 
            "raw_text": "text"
        }

        # Side effect for sequential calls: file1 -> [A], file2 -> [A], file3 -> [B]
        # main.py loops strategies. We need to be careful.
        # main.py logic:
        # for file in files:
        #   for strategy in strategies:
        #      ocr_results = ...
        #      contacts = extractor.extract_contacts(ocr_results)
        #      if contacts: ... break
        
        # So we mock extract_contacts to return [contact_a] on first valid call per file
        # But wait, it's called once per strategy. 
        # Simplest approach: Just let it return [contact_a] always.
        
        # Scenario: 2 files uploaded. Both return contact_a.
        mock_extract.side_effect = [[contact_a], [contact_a], [contact_b]] 
        
        # We need physical files to upload.
        files = [
            ('files', ('file1.png', b'content', 'image/png')),
            ('files', ('file2.png', b'content', 'image/png')),
            ('files', ('file3.png', b'content', 'image/png'))
        ]
        
        # We also need to mock ocr_engine.process_image_with_strategy so it doesn't actually run OCR
        mock_ocr_engine.process_image_with_strategy.return_value = [] # Content doesn't matter since we mock extractor
        
        response = client.post("/extract", files=files)
        assert response.status_code == 200
        data = response.json()['results']
        
        # We sent 3 files.
        # file1 -> returns User A
        # file2 -> returns User A (should be deduplicated if logic works across files?)
        # Wait, the logic I implemented is per-request. So yes.
        # file3 -> returns User B
        
        print(data)
        
        # Check that we have 3 entry results corresponding to 3 files
        # BUT wait, the requirements said: "If the same phone number appears multiple times across sources or entries, include it only once in the output."
        # My implementation removes the second entry entirely or just the contact info?
        # My implementation: 
        # if phone and phone not in seen_phones: ... results.append(...)
        # else: ... results.append(...) is NOT called.
        # So if file2 produces a duplicate, it produces NO result entry in `results` list?
        # The user said: "include it only once in the output". 
        # If I have 3 input files, and 2 are duplicates, should the output list have 2 or 3 items?
        # Usually file processing endpoints return 1 result per file.
        # BUT if the goal is "Contact Extraction", maybe a flat list of unique contacts is desired?
        # The user request: "remove any duplicates. If the same phone number appears multiple times across sources or entries, include it only once in the output."
        # This strongly implies a list of UNIQUE CONTACTS, not necessarily 1-to-1 mapping to files if duplicates exist.
        
        phones = [item['phone'] for item in data if 'phone' in item]
        assert phones.count("1234567890") == 1
        assert "0987654321" in phones
        
        # Verify total unique contacts
        # If file2 was skipped, len(data) might be 2.
        assert len(data) == 2

if __name__ == "__main__":
    # Manually run if pytest not installed, but we should use pytest
    try:
        test_normalize_phone()
        print("test_normalize_phone passed")
    except AssertionError as e:
        print(f"test_normalize_phone failed: {e}")
