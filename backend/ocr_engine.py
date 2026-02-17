import easyocr
import io
from PIL import Image
import numpy as np
from PIL import Image, ImageEnhance, ImageOps

class OCREngine:
    def __init__(self, languages=['en']):
        print("Initializing EasyOCR...")
        try:
            self.reader = easyocr.Reader(languages)
            print("EasyOCR initialized.")
        except Exception as e:
            print(f"Error initializing EasyOCR: {e}")
            self.reader = None

    def process_image(self, image_bytes: bytes):
        """
        Process image bytes directly using default strategy or just pass through to easyocr
        This is kept for backward compatibility if needed, but main logic should use process_image_with_strategy
        """
        return self.process_image_with_strategy(image_bytes, 'original')

    def process_image_with_strategy(self, image_bytes: bytes, strategy: str = 'original'):
        if not self.reader:
             raise Exception("OCR Engine not initialized")

        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Apply preprocessing based on strategy
            image = self._preprocess_image(image, strategy)

            # Convert to numpy array for EasyOCR
            image_np = np.array(image)
            
            # detail=0 returns just the text list. detail=1 (default) returns bounding box, text, confidence
            results = self.reader.readtext(image_np, detail=1) 
            return results
        except Exception as e:
            print(f"Error processing image with strategy {strategy}: {e}")
            return []

    def _preprocess_image(self, image: Image.Image, strategy: str) -> Image.Image:
        if strategy == 'original':
            return image
        
        # Convert to RGB if not already
        if image.mode != 'RGB':
            image = image.convert('RGB')

        if strategy == 'grayscale':
             return ImageOps.grayscale(image)
        
        elif strategy == 'enhanced':
            # Increase contrast and sharpness
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)
            return image

        elif strategy == 'resized':
            # Resize by 2x
            width, height = image.size
            return image.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
            
        elif strategy == 'binarized':
             # Convert to grayscale then binarize
             image = ImageOps.grayscale(image)
             # Simple thresholding
             threshold = 128
             return image.point(lambda p: 255 if p > threshold else 0)

        return image

ocr_engine = OCREngine()
