from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import shutil
import os
import pandas as pd
import io
from fastapi.responses import StreamingResponse

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "*", # Allow all origins for initial deployment (restrict this in production!)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

from ocr_engine import ocr_engine
from extractor import extractor

@app.post("/extract")
async def extract_contacts(files: List[UploadFile] = File(...)):
    results = []
    # Deduplication Scope: Per upload batch.
    # We maintain a set of seen phones for the entire request (all files).
    # 1. Single File: effectively handled because we process contacts top-to-bottom (see extractor.py sorting), 
    #    so the first one is added to seen_phones and subsequent duplicates in the same file are skipped.
    # 2. Multiple Files: effectively handled because seen_phones persists across the file loop. 
    #    If a number was found in a previous file, it will be skipped here.
    seen_phones = set()
    
    # Initialize OCR engine if not already (it lazy loads in class)
    if not ocr_engine.reader:
         # In a real app we might handle this better, but ocr_engine.init handles internal checks
         pass

    for file in files:
        try:
            contents = await file.read()
            # Define strategies to try
            strategies = ['original', 'enhanced', 'binarized', 'grayscale', 'resized']
            
            best_contacts = []
            successful_strategy = None

            for strategy in strategies:
                print(f"Processing {file.filename} with strategy: {strategy}")
                ocr_results = ocr_engine.process_image_with_strategy(contents, strategy=strategy)
                contacts = extractor.extract_contacts(ocr_results)
                
                # Check if we got any valid contacts
                if contacts:
                    # simplistic check: if ANY contact is valid, we consider this strategy successful
                    if any(extractor.is_valid_contact(c) for c in contacts):
                        best_contacts = contacts
                        successful_strategy = strategy
                        break # Stop retrying
                    
                    # If we found contacts but they weren't "valid" (e.g. name was Unknown),
                    # we keep them as a fallback if no better strategy works
                    if not best_contacts:
                         best_contacts = contacts
            
            # Add to results
            if best_contacts:
                for contact in best_contacts:
                    phone = contact['phone']
                    # Deduplication check: strict check against seen_phones
                    if phone and phone not in seen_phones:
                        seen_phones.add(phone)
                        results.append({
                            "filename": file.filename,
                            "name": contact['name'],
                            "phone": phone,
                            "confidence": contact['confidence'],
                            "strategy": successful_strategy or "fallback"
                        })
                    elif not phone:
                         # Handle case where contact found but no phone (unlikely given logic, but safe)
                         pass
            else:
                 results.append({
                        "filename": file.filename,
                        "name": "No contact found",
                        "phone": "",
                        "confidence": 0.0,
                        "strategy": "all_failed"
                    })

        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e),
                "status": "failed"
            })
            
    # Final Validation Step: functional double-check for uniqueness
    # (Though logic above should handle it, this meets the 'Final validation step' requirement)
    final_results = []
    final_seen = set()
    for res in results:
        p = res.get('phone')
        if p:
            if p not in final_seen:
                final_seen.add(p)
                final_results.append(res)
            # Else: Duplicate crept in? Skip it.
        else:
            # Keep failures or no-phone entries
            final_results.append(res)
            
    return {"results": final_results}

@app.post("/process-dataset")
async def process_dataset(file: UploadFile = File(...)):
    # Read file into Pandas DataFrame
    contents = await file.read()
    
    try:
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        elif file.filename.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Invalid file format. Please upload CSV or Excel.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

    # Identify phone column
    phone_col = None
    possible_names = ['phone', 'mobile', 'contact', 'cell', 'number', 'tel']
    
    # Case-insensitive search
    col_map = {c.lower(): c for c in df.columns}
    for name in possible_names:
        for col in col_map:
            if name in col:
                phone_col = col_map[col]
                break
        if phone_col:
            break
            
    # Fallback to first column if no match found
    if not phone_col and not df.empty:
        phone_col = df.columns[0]
        
    if not phone_col:
        raise HTTPException(status_code=400, detail="Could not identify phone number column and file is empty.")

    # Normalize phone numbers
    # Create a new column 'Normalized Phone'
    # We use the existing extractor instance
    df['Normalized Phone'] = df[phone_col].astype(str).apply(extractor.normalize_phone)
    
    # Remove rows where Normalized Phone is empty (invalid numbers)
    df = df[df['Normalized Phone'] != ""]
    
    # Deduplicate based on 'Normalized Phone'
    # keep='first' retains the first occurrence
    df_deduped = df.drop_duplicates(subset=['Normalized Phone'], keep='first')
    
    # Final Validation Step: strict cross-check
    unique_phones = df_deduped['Normalized Phone'].unique()
    if len(df_deduped) != len(unique_phones):
        # This should theoretically not happen after drop_duplicates, but serves as the requested "final validation step"
        # If it happens, we re-deduplicate or raise error. 
        # For robustness, we enforce uniquness again.
        df_deduped = df_deduped.drop_duplicates(subset=['Normalized Phone'])

    # Verify again
    assert len(df_deduped) == len(df_deduped['Normalized Phone'].unique())

    # Create Excel output
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_deduped.to_excel(writer, index=False)
    output.seek(0)
    
    return StreamingResponse(
        output, 
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=processed_{file.filename}.xlsx"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
