import io
from PIL import Image, ImageDraw, ImageFont
from ocr_engine import ocr_engine
from extractor import extractor

def create_test_image(text_lines, size=(400, 200), bg_color=(255, 255, 255), text_color=(0, 0, 0)):
    image = Image.new('RGB', size, color=bg_color)
    draw = ImageDraw.Draw(image)
    # Load default font
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        font = ImageFont.load_default()
    
    y = 20
    for line in text_lines:
        draw.text((20, y), line, fill=text_color, font=font)
        y += 40
        
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

def test_extraction():
    print("Test 1: Clear Image")
    image_bytes = create_test_image(["~ Test User", "+91 99999 88888"])
    
    # Simulate main.py logic
    strategies = ['original', 'enhanced', 'binarized', 'grayscale', 'resized']
    
    best_contacts = []
    successful_strategy = None
    
    for strategy in strategies:
        print(f"  Trying strategy: {strategy}")
        ocr_results = ocr_engine.process_image_with_strategy(image_bytes, strategy=strategy)
        contacts = extractor.extract_contacts(ocr_results)
        
        if contacts:
            if any(extractor.is_valid_contact(c) for c in contacts):
                best_contacts = contacts
                successful_strategy = strategy
                print(f"  Success with {strategy}!")
                break
            if not best_contacts:
                best_contacts = contacts

    if best_contacts:
        print("  Extracted:")
        for c in best_contacts:
            print(f"    Name: {c['name']}, Phone: {c['phone']}, Valid: {extractor.is_valid_contact(c)}")
    else:
        print("  Failed to extract valid contacts.")

    print("\nTest 2: Very Low Contrast Image (Should fail original, pass enhanced or binarized)")
    # RGB(254, 254, 254) is almost white.
    image_bytes_very_low_contrast = create_test_image(["~ Ghost User", "+91 77777 66666"], text_color=(254, 254, 254))
    
    successful_strategy = None
    best_contacts = []
    
    for strategy in strategies:
        print(f"  Trying strategy: {strategy}")
        ocr_results = ocr_engine.process_image_with_strategy(image_bytes_very_low_contrast, strategy=strategy)
        contacts = extractor.extract_contacts(ocr_results)
        
        # Debug print to see if we get anything
        # print(f"    {strategy} Raw OCR: {ocr_results}")
        
        if contacts:
             if any(extractor.is_valid_contact(c) for c in contacts):
                best_contacts = contacts
                successful_strategy = strategy
                print(f"  Success with {strategy}!")
                break
    
    if best_contacts:
        print(f"  Final Result (Strategy: {successful_strategy}):")
        for c in best_contacts:
             print(f"    Name: {c['name']}, Phone: {c['phone']}")
    else:
        print("  Failed all strategies.")

if __name__ == "__main__":
    test_extraction()
