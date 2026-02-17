import re
import phonenumbers

class ContactExtractor:
    def __init__(self):
        # Regex patterns for phone numbers
        # Matches: +1 234-567-8901, (234) 567-8901, 234 567 8901, 0123456789
        self.phone_pattern = re.compile(r'''
            (?:(?:\+?1\s*(?:[.-]\s*)?)?(?:\(\s*([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9])\s*\)|([2-9]1[02-9]|[2-9][02-8]1|[2-9][02-8][02-9]))\s*(?:[.-]\s*)?)?([2-9]1[02-9]|[2-9][02-9]1|[2-9][02-9]{2})\s*(?:[.-]\s*)?([0-9]{4})
        ''', re.VERBOSE)
        
        
        # Simple fallback for international numbers or looser formats
        # Updated to support: 
        # - US style: +1 123-456-7890
        # - Indian style: +91 99999 88888 (5 space 5)
        # - Continuous: +919999988888
        self.simple_phone_pattern = re.compile(r'(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\d{5}[-.\s]?\d{5})')

    def normalize_phone(self, phone_str):
        """
        Normalizes a phone number string to just digits using phonenumbers library.
        Default region is US.
        Example: 
        '+1 (123) 456-7890' -> '11234567890'
        '123-456-7890' -> '11234567890' (US default)
        '+44 7123 456 789' -> '447123456789'
        '001 123 456 7890' -> '11234567890' (Handle 00 as +)
        """
        if not phone_str:
            return ""
            
        # Ensure input is string
        if not isinstance(phone_str, str):
            phone_str = str(phone_str)

        cleaned = phone_str.strip()
        
        # specific fix for '00' as '+' (common international prefix)
        if cleaned.startswith('00'):
            cleaned = '+' + cleaned[2:]

        try:
            # Parse with 'US' as default region
            parsed_number = phonenumbers.parse(cleaned, "US")
            
            # Check validity to avoid coercing unrelated numbers (e.g. Aus 04...) into US +1 format
            if phonenumbers.is_valid_number(parsed_number):
                 formatted = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
                 if formatted.startswith('+'):
                    return formatted[1:]
                 return formatted
            else:
                 # If invalid for US (and no country code provided that made it valid otherwise),
                 # return raw digits. Better to have "04..." than "+104..."
                 return re.sub(r'\D', '', phone_str)
            
        except phonenumbers.NumberParseException:
             # Fallback: simple digit extraction
             return re.sub(r'\D', '', phone_str)

    def extract_contacts(self, ocr_results):
        """
        ocr_results: List of (bbox, text, prob)
        Returns: List of dicts {'name': str, 'phone': str, 'confidence': float}
        """
        candidates = []
        
        # Sort results by vertical position (top to bottom)
        # bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        # We use y1 (top-left y) for sorting
        # CRITICAL: This sorting ensures that when we iterate and filter duplicates later,
        # we prioritize the occurence appearing first (top-most) in the document.
        sorted_results = sorted(ocr_results, key=lambda x: x[0][0][1])

        for i, (bbox, text, prob) in enumerate(sorted_results):
            # Check for phone number
            phone_match = self.simple_phone_pattern.search(text)
            if phone_match:
                raw_phone = phone_match.group(0).strip()
                phone = self.normalize_phone(raw_phone)
                
                # Heuristic: Name is likely in the line directly above
                name = "Unknown"
                if i > 0:
                    prev_text = sorted_results[i-1][1].strip()
                    # Basic name validation: 
                    # - 2-4 words
                    # - Mostly alphabetic
                    # - Capitalized first letters (optional looking at OCR quality)
                    words = prev_text.split()
                    if 1 <= len(words) <= 4 and not any(c.isdigit() for c in prev_text):
                        name = prev_text
                
                # Construct result
                candidates.append({
                    "name": name,
                    "phone": phone,
                    "confidence": prob, # Using OCR confidence of the phone line for now
                    "raw_phone": raw_phone,
                    "raw_text": text
                })
        
        return candidates

    def is_valid_contact(self, contact):
        """
        Validates a contact dictionary.
        Returns True if valid, False otherwise.
        """
        if not contact:
            return False
            
        name = contact.get('name')
        phone = contact.get('phone')
        
        # Check name
        if not name or name == "Unknown":
            return False
            
        # Basic name validation (reused from extract_contacts logic)
        words = name.split()
        if not (1 <= len(words) <= 4):
            return False
        if any(c.isdigit() for c in name):
            return False
            
        # Check phone
        if not phone:
            return False
            
        return True

extractor = ContactExtractor()
