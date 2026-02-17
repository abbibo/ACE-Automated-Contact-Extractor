# ACE (Automated Contact Extractor) Project Summary

ACE is a full-stack web application designed to automate the extraction, normalization, and deduplication of contact information (specifically phone numbers and associated names) from various sources, including images and existing datasets.

## 🏗️ Architecture

### Backend

- **Framework**: Python + FastAPI
- **Key Libraries**:
  - `easyocr`: For Optical Character Recognition (extracting text from images).
  - `pandas`: For handling CSV/Excel dataset processing.
  - `phonenumbers`: For parsing and normalizing phone numbers (Google's libphonenumber port).
  - `opencv` (implied by image processing strategies): For image enhancement before OCR.
- **Endpoints**:
  - `POST /extract`: Accepts images, runs multi-strategy OCR, extracts contacts, and returns deduplicated results.
  - `POST /process-dataset`: Accepts CSV/Excel headers, identifies phone columns, normalizes numbers, and removes duplicates.

### Frontend

- **Framework**: React + Vite
- **Styling**: Vanilla CSS (`index.css`) with utility classes.
- **Key Components**:
  - `UploadZone`: Handles file selection and drag-and-drop.
  - `ResultsTable`: Displays extracted data (Name, Phone, Confidence).
  - `Export`: Generates .xlsx files using `xlsx` library on the client side.

## 🚀 Key Features

### Image-based Extraction (OCR)

- Support for batch uploading of images.
- **Adaptive Strategies**: Tries multiple image processing techniques (original, enhanced, binarized, grayscale, resized) to maximize extraction success.
- **Heuristic Association**: Attempts to link phone numbers with names found in adjacent text lines.

### Dataset Normalization

- Upload CSV or Excel files.
- Auto-detects phone number columns (e.g., "mobile", "cell", "tel").
- **Smart Normalization**: Converts various formats (e.g., `(123) 456-7890`, `+91 999...`) into a standardized format using `phonenumbers` (defaulting to US or preserving raw digits if invalid).

### Deduplication

- **Intra-batch**: Prevents duplicate numbers from appearing in the same upload session.
- **Strict Mode**: Ensures unique phone numbers in the final output.

### Export

- Download clean, processed data as an Excel spreadsheet (.xlsx).

## 📁 Key File Structure

- `backend/main.py`: API entry point and logic for endpoints.
- `backend/extractor.py`: Core logic for regex matching, phone normalization, and linking names to numbers.
- `backend/ocr_engine.py`: Wrapper around EasyOCR with image preprocessing methods.
- `frontend/src/App.jsx`: Main UI controller handling state, uploads, and exports.

---

## Prerequisites

- Python 3.8+
- Node.js (v18+ recommended)

## Setup & Installation

### Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Frontend

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

## Running the Application

You need to run the backend and frontend in **two separate terminals**.

### Terminal 1: Backend

```bash
cd backend
python main.py
```

Server runs at: http://localhost:8000

### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

App runs at: http://localhost:5173

## Application Access

Open your browser and navigate to: **http://localhost:5173**
