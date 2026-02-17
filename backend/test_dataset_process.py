import io
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from main import app
from extractor import extractor

client = TestClient(app)

def test_dataset_processing_deduplication():
    # Create a sample CSV in memory
    csv_content = """Name,Phone
Alice,123-456-7890
Bob,(123) 456-7890
Charlie,+1 123 456 7890
Dave,9876543210
Eve,+91 98765 43210
Frank,
"""
    files = {
        'file': ('test_contacts.csv', csv_content, 'text/csv')
    }

    response = client.post("/process-dataset", files=files)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    # Load response as Excel
    with io.BytesIO(response.content) as f:
        df = pd.read_excel(f)
    
    assert 'Normalized Phone' in df.columns
    
    # Get normalized phones
    phones = df['Normalized Phone'].dropna().astype(str).tolist()
    
    # Check uniqueness
    assert len(phones) == len(set(phones))
    
    # Verify specific numbers
    assert "11234567890" in phones
    assert "19876543210" in phones
    assert "919876543210" in phones
    
    # Verify count: Alice/Bob/Charlie (1) + Dave (1) + Eve (1) = 3 unique valid numbers
    assert len(phones) == 3

def test_dataset_excel_upload():
    # Create a sample Excel in memory
    df_input = pd.DataFrame({
        'Contact Name': ['Test1', 'Test2'],
        'Mobile Number': ['555-0101', '555-0101'] # Duplicate
    })
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_input.to_excel(writer, index=False)
    output.seek(0)
    
    files = {
        'file': ('test_contacts.xlsx', output, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    }
    
    response = client.post("/process-dataset", files=files)
    assert response.status_code == 200
    
    with io.BytesIO(response.content) as f:
        df_result = pd.read_excel(f)
        
    # Check deduplication
    valid_phones = df_result['Normalized Phone'].dropna().tolist()
    assert len(valid_phones) == 1
    # 555-0101 -> normalized
    assert str(valid_phones[0]) == "5550101"
