
import requests
import os
import time
import sys
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import io

BASE_URL = "http://localhost:8000"

def create_test_image_local():
    """Generates a test image with phone numbers."""
    img = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img)
    text = """
    Contact List:
    User Test: (555) 123-9999
    User Dupe: (555) 123-9999
    """
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        font = ImageFont.load_default()
    
    d.text((50, 50), text, fill=(0,0,0), font=font)
    path = "temp_test_image.png"
    img.save(path)
    return path

def create_test_csv_local():
    """Generates a test CSV with phone numbers."""
    data = {"Name": ["Alice", "Bob"], "Phone": ["555-000-1111", "555-000-1111"]}
    df = pd.DataFrame(data)
    path = "temp_test_data.csv"
    df.to_csv(path, index=False)
    return path

def check_health():
    print("Checking /health...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=5)
        if resp.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {resp.status_code} {resp.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused. Is the server running?")
        return False

def test_extract(image_path):
    print("\nTesting /extract endpoint...")
    with open(image_path, "rb") as f:
        files = {"files": (os.path.basename(image_path), f, "image/png")}
        try:
            resp = requests.post(f"{BASE_URL}/extract", files=files)
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                print(f"✅ /extract passed. Found {len(results)} extraction results.")
                # Basic validation
                for res in results:
                    print(f"   - Found: {res.get('name')}: {res.get('phone')}")
                return True
            else:
                print(f"❌ /extract failed: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
            print(f"❌ /extract exception: {e}")
            return False

def test_process_dataset(csv_path):
    print("\nTesting /process-dataset endpoint...")
    with open(csv_path, "rb") as f:
        files = {"file": (os.path.basename(csv_path), f, "text/csv")}
        try:
            resp = requests.post(f"{BASE_URL}/process-dataset", files=files)
            if resp.status_code == 200:
                print("✅ /process-dataset passed. Received file response.")
                # Verify it's an excel file
                if "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in resp.headers.get("Content-Type", ""):
                     print("   - Content-Type verified.")
                return True
            else:
                print(f"❌ /process-dataset failed: {resp.status_code} {resp.text}")
                return False
        except Exception as e:
             print(f"❌ /process-dataset exception: {e}")
             return False

if __name__ == "__main__":
    if not check_health():
        sys.exit(1)
        
    img_path = create_test_image_local()
    csv_path = create_test_csv_local()
    
    try:
        success = True
        if not test_extract(img_path): success = False
        if not test_process_dataset(csv_path): success = False
        
        if success:
            print("\n🎉 All E2E tests passed!")
            sys.exit(0)
        else:
            print("\n⚠️ Some tests failed.")
            sys.exit(1)
    finally:
        # Cleanup
        if os.path.exists(img_path): os.remove(img_path)
        if os.path.exists(csv_path): os.remove(csv_path)
