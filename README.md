ACE (Automated Contact Extractor) Project Summary
ACE is a full-stack web application designed to automate the extraction, normalization, and deduplication of contact information (specifically phone numbers and associated names) from various sources, including images and existing datasets.

🏗️ Architecture
Backend
Framework: Python + FastAPI
Key Libraries:
easyocr: For Optical Character Recognition (extracting text from images).
pandas: For handling CSV/Excel dataset processing.
phonenumbers: For parsing and normalizing phone numbers (Google's libphonenumber port).
opencv (implied by image processing strategies): For image enhancement before OCR.
Endpoints:
POST /extract: Accepts images, runs multi-strategy OCR, extracts contacts, and returns deduplicated results.
POST /process-dataset: Accepts CSV/Excel headers, identifies phone columns, normalizes numbers, and removes duplicates.
Frontend
Framework: React + Vite
Styling: Vanilla CSS (index.css) with utility classes.
Key Components:
UploadZone: Handles file selection and drag-and-drop.
ResultsTable: Displays extracted data (Name, Phone, Confidence).
Export
: Generates .xlsx files using xlsx library on the client side.
🚀 Key Features
Image-based Extraction (OCR)

Support for batch uploading of images.
Adaptive Strategies: Tries multiple image processing techniques (original, enhanced, binarized, grayscale, resized) to maximize extraction success.
Heuristic Association: Attempts to link phone numbers with names found in adjacent text lines.
Dataset Normalization

Upload CSV or Excel files.
Auto-detects phone number columns (e.g., "mobile", "cell", "tel").
Smart Normalization: Converts various formats (e.g., 
(123) 456-7890
, +91 999...) into a standardized format using phonenumbers (defaulting to US or preserving raw digits if invalid).
Deduplication

Intra-batch: Prevents duplicate numbers from appearing in the same upload session.
Strict Mode: Ensures unique phone numbers in the final output.
Export

Download clean, processed data as an Excel spreadsheet (.xlsx).
📁 Key File Structure
backend/main.py
: API entry point and logic for endpoints.
backend/extractor.py
: Core logic for regex matching, phone normalization, and linking names to numbers.
backend/ocr_engine.py
: Wrapper around EasyOCR with image preprocessing methods.
frontend/src/App.jsx
: Main UI controller handling state, uploads, and exports.
