
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from main import app
import main

client = TestClient(app)

def test_single_file_deduplication_top_to_bottom():
    """
    Verify: If a phone number appears multiple times in one image, 
    only the first occurrence (top-to-bottom) is kept.
    """
    # Mock OCR engine to return two results with same phone number but different Y coordinates
    def mock_process(content, strategy='original'):
        if content == b'single_file_dupe':
            return [
                # Top one (y=10) - Should be kept
                ( [[0,10],[100,10],[100,20],[0,20]], "Top Instance", 0.9 ),
                # Bottom one (y=100) - Should be discarded
                ( [[0,100],[100,100],[100,120],[0,120]], "Bottom Instance", 0.8 ) 
            ]
        return []

    # Mock extractor normalization to simulate same phone number
    # We'll use the real extractor but mock the OCR return to yield "Top Instance" and "Bottom Instance" text
    # that resolves to the same phone number.
    # Actually, let's just mock the OCR return to return identical phone numbers in text.
    def mock_process_simple(content, strategy='original'):
        if content == b'single_file_dupe':
            return [
                # Top: 212-555-0001
                ( [[0,10],[100,10],[100,20],[0,20]], "User One", 0.9 ),
                ( [[0,30],[100,30],[100,50],[0,50]], "212-555-0001", 0.9 ),
                
                # Bottom: 212-555-0001 (Duplicate in same file)
                ( [[0,100],[100,100],[100,120],[0,120]], "User Two", 0.9 ),
                ( [[0,130],[100,130],[100,150],[0,150]], "212-555-0001", 0.9 ) 
            ]
        return []

    original_method = main.ocr_engine.process_image_with_strategy
    main.ocr_engine.process_image_with_strategy = mock_process_simple
    
    
    try:
        files = [('files', ('single_dupe.png', b'single_file_dupe', 'image/png'))]
        response = client.post("/extract", files=files)
        assert response.status_code == 200
        results = response.json()['results']
        
        print(f"\nDEBUG: Results received: {results}")

        # Should have exactly 1 result for this file
        assert len(results) == 1
        assert results[0]['phone'] == '12125550001'
        assert results[0]['name'] == 'User One' # The top one

    finally:
         main.ocr_engine.process_image_with_strategy = original_method


def test_multi_file_deduplication_first_processed():
    """
    Verify: If the same phone number appears across multiple uploaded images, 
    only the first instance processed is kept.
    """
    def mock_process_multi(content, strategy='original'):
        if content == b'file_a':
             return [
                ( [[0,10],[100,10],[100,20],[0,20]], "User File A", 0.9 ),
                ( [[0,30],[100,30],[100,50],[0,50]], "212-555-9999", 0.9 )
            ]
        elif content == b'file_b':
             return [
                ( [[0,10],[100,10],[100,20],[0,20]], "User File B", 0.9 ),
                ( [[0,30],[100,30],[100,50],[0,50]], "212-555-9999", 0.9 ) # Same number
            ]
        return []

    original_method = main.ocr_engine.process_image_with_strategy
    main.ocr_engine.process_image_with_strategy = mock_process_multi
    
    try:
        # File A acts as "first processed" (assuming list order preservation)
        files = [
            ('files', ('file_a.png', b'file_a', 'image/png')),
            ('files', ('file_b.png', b'file_b', 'image/png'))
        ]
        response = client.post("/extract", files=files)
        assert response.status_code == 200
        results = response.json()['results']
        
        # Should have exactly 1 valid result
        valid_results = [r for r in results if r.get('phone')]
        assert len(valid_results) == 1
        assert valid_results[0]['phone'] == '12125559999'
        assert valid_results[0]['name'] == 'User File A'
        assert valid_results[0]['filename'] == 'file_a.png'

    finally:
         main.ocr_engine.process_image_with_strategy = original_method

if __name__ == "__main__":
    test_single_file_deduplication_top_to_bottom()
    test_multi_file_deduplication_first_processed()
    print("Detailed Deduplication Tests Passed!")
