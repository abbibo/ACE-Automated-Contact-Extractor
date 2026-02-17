
import os
import sys
import re
import argparse
import phonenumbers
from ocr_engine import ocr_engine
# We can reuse extractor regexes but normalization logic is custom
from extractor import extractor 

def custom_normalize(phone_str):
    """
    Normalizes a phone number string according to strict rules:
    - Digits only.
    - No country code unless explicitly shown in the original string.
    - If valid US number without explicit country code, return 10 digits.
    - If valid US number WITH explicit country code (+1), return 11 digits (1 + 10 digits).
    - If valid International number, return full digits including country code.
    """
    if not phone_str:
        return ""
        
    original_str = str(phone_str).strip()
    
    # Check for explicit country code indicators in the original string
    has_explicit_plus = original_str.startswith('+')
    has_explicit_00 = original_str.startswith('00')
    
    # Basic cleanup for parsing (phonenumbers lib handles formats well)
    # specific fix for '00' as '+' 
    cleaned_for_parsing = original_str
    if has_explicit_00:
        cleaned_for_parsing = '+' + original_str[2:]
    
    try:
        # Parse with 'US' as default region
        parsed_number = phonenumbers.parse(cleaned_for_parsing, "US")
        
        if phonenumbers.is_valid_number(parsed_number):
            # Get E164 format (e.g. +14155552671)
            e164_format = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
            # Remove the '+'
            digits_only = e164_format[1:]
            
            # Logic for stripping implicit country code
            # If the number is from the default region (US, country code 1)
            if parsed_number.country_code == 1:
                # If the original string did NOT have an explicit country code indicator
                # We strip the leading '1'
                # How to detect "explicit country code"?
                # If original had '+1' or '001' -> Explicit.
                # If original had '1-...' at start? ambiguous, but usually in US '1' is the trunk prefix, not country code.
                # However, E.164 standardization adds '1'.
                
                # Let's look at the original string again.
                # If the user wrote "1 (555) 123..." that's usually just trunk prefix in domestic dialing.
                # If the user wrote "+1 (555)..." that's explicit country code.
                
                # The requirement: "no country codes unless explicitly shown".
                # If image has "(555) 123-4567", distinct from "+1 (555) 123-4567"?
                # Standardizing:
                # (555) 123-4567 -> 5551234567
                # +1 (555) 123-4567 -> 15551234567
                
                if has_explicit_plus or has_explicit_00:
                    return digits_only # Return full with country code (e.g. 1555...)
                else:
                    return digits_only[1:] # Strip the leading '1' (e.g. 555...)
            else:
                # Non-US numbers: usually implied to have country code if valid?
                # Actually, if I parse "0412 345 678" (AU) with default region US, it might fail or parse differently.
                # If it parsed successfully as a valid number, it likely has a country code or we guessed region.
                # Users usually have US numbers or Int numbers with +.
                return digits_only
        else:
            # Invalid but maybe just digits?
            return re.sub(r'\D', '', original_str)
            
    except phonenumbers.NumberParseException:
        # Fallback
        return re.sub(r'\D', '', original_str)

def process_folder(folder_path):
    if not os.path.isdir(folder_path):
        print(f"Error: Folder '{folder_path}' not found.")
        return []

    print(f"Scanning folder: {folder_path}")
    image_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
    files = [f for f in os.listdir(folder_path) if os.path.splitext(f.lower())[1] in image_extensions]
    
    if not files:
        print("No image files found in the folder.")
        return []

    all_phones = []
    
    # Initialize OCR (lazy load)
    if not ocr_engine.reader:
        print("Initializing OCR engine (this simulates startup)...")
        # Accessing reader property triggers init
        _ = ocr_engine.reader

    for filename in files:
        file_path = os.path.join(folder_path, filename)
        print(f"Processing: {filename}...")
        
        try:
            with open(file_path, 'rb') as f:
                image_bytes = f.read()
                
            # Use 'original' strategy for speed, maybe 'enhanced' if needed. 
            # The backend tries multiple, we can simplify or be robust.
            # Let's try 'original' then 'enhanced' if nothing found?
            # For this script, let's just use 'original' and 'enhanced' combined results to be safe.
            
            strategies = ['original', 'enhanced']
            file_phones = set()
            
            for strategy in strategies:
                ocr_results = ocr_engine.process_image_with_strategy(image_bytes, strategy=strategy)
                
                # Extract using extractor's regex but our custom normalization
                # Reuse extractor's logic for finding candidates
                regex = extractor.simple_phone_pattern
                
                for _, text, _ in ocr_results:
                     # Check for phone number
                    phone_match = regex.search(text)
                    if phone_match:
                        raw_phone = phone_match.group(0).strip()
                        normalized = custom_normalize(raw_phone)
                        if normalized and len(normalized) >= 7: # Basic length filter
                            file_phones.add(normalized)
            
            if file_phones:
                print(f"  Found: {', '.join(file_phones)}")
                all_phones.extend(file_phones)
            else:
                print("  No phones found.")
                
        except Exception as e:
            print(f"  Error processing {filename}: {e}")

    return all_phones

def main():
    parser = argparse.ArgumentParser(description="Analyze screenshots for phone numbers.")
    parser.add_argument("--dir", default="screenshots", help="Directory containing screenshots")
    args = parser.parse_args()
    
    folder_path = args.dir
    # Handle relative paths:
    if not os.path.isabs(folder_path):
        folder_path = os.path.join(os.getcwd(), folder_path)

    raw_phones = process_folder(folder_path)
    
    # Final Deduplication
    unique_phones = sorted(list(set(raw_phones)))
    
    print("\n" + "="*30)
    print("FINAL CONSOLIDATED LIST")
    print("="*30)
    
    if unique_phones:
        for p in unique_phones:
            print(p)
            
        # Save to file
        output_file = "extracted_numbers.txt"
        with open(output_file, "w") as f:
            for p in unique_phones:
                f.write(p + "\n")
        print(f"\nSaved {len(unique_phones)} unique numbers to {output_file}")
    else:
        print("No phone numbers found.")

if __name__ == "__main__":
    main()
