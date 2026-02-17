
from PIL import Image, ImageDraw, ImageFont
import os

def create_image():
    # Create white image
    img = Image.new('RGB', (800, 600), color='white')
    d = ImageDraw.Draw(img)
    
    # Text to draw
    # 1. Standard US (should be 5551234567)
    # 2. Duplicate of 1
    # 3. Explicit US (should be 15551234567)
    # 4. International (should be 919999988888)
    
    text = """
    Contact List:
    
    User A: (555) 123-4567
    User B: (555) 123-4567
    User C: +1 555 123 4567
    User D: +91 99999 88888
    User E: 555-000-1111
    """
    
    # Draw text (using default font if custom not available, though explicit font is better)
    # For default, font=None works but mighty be small. 
    # Let's try to load a default font or just let PIL handle it.
    try:
        # Windows usually has arial
        font = ImageFont.truetype("arial.ttf", 24)
    except IOError:
        font = None # Fallback to default
    
    d.text((50, 50), text, fill=(0,0,0), font=font)
    
    # Save
    if not os.path.exists('screenshots'):
        os.makedirs('screenshots')
        
    img.save('screenshots/test_dummy.png')
    print("Created screenshots/test_dummy.png")

if __name__ == "__main__":
    create_image()
