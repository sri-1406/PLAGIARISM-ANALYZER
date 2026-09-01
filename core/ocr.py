import os
import numpy as np
from PIL import Image
import io

# Global reader instance for lazy loading
_EASYOCR_READER = None

def get_easyocr_reader():
    global _EASYOCR_READER
    if _EASYOCR_READER is None:
        import easyocr
        print("[OCR] Initializing EasyOCR engine...")
        _EASYOCR_READER = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _EASYOCR_READER

def preprocess_image_for_handwriting(image_bytes):
    """
    Preprocess image to enhance handwritten text visibility.
    Applies grayscale conversion, CLAHE (Contrast Limited Adaptive Histogram Equalization),
    and subtle denoising.
    """
    try:
        import cv2
        
        # Decode byte stream to OpenCV BGR image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply CLAHE to equalize contrast (helps with light/faded handwriting)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Mild Denoising
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10, templateWindowSize=7, searchWindowSize=21)
        
        return denoised
    except Exception as e:
        print(f"[OCR Preprocess Warning] OpenCV processing skipped: {e}")
        return None

def extract_handwritten_text(image_input):
    """
    Extracts text from handwritten or printed document images.
    :param image_input: Bytes, File Storage object, PIL Image, or File Path.
    :return: dict with 'text', 'confidence', 'method'
    """
    image_bytes = None
    
    # Normalize input to raw bytes
    if isinstance(image_input, bytes):
        image_bytes = image_input
    elif hasattr(image_input, 'read'):
        image_bytes = image_input.read()
        if hasattr(image_input, 'seek'):
            image_input.seek(0)
    elif isinstance(image_input, str) and os.path.exists(image_input):
        with open(image_input, 'rb') as f:
            image_bytes = f.read()
    elif isinstance(image_input, Image.Image):
        buf = io.BytesIO()
        image_input.save(buf, format='PNG')
        image_bytes = buf.getvalue()
        
    if not image_bytes:
        return {"text": "", "confidence": 0.0, "error": "Invalid or empty image provided."}
        
    # Primary Engine: EasyOCR
    try:
        reader = get_easyocr_reader()
        
        # Preprocess image
        preprocessed = preprocess_image_for_handwriting(image_bytes)
        input_data = preprocessed if preprocessed is not None else image_bytes
        
        # Run EasyOCR with paragraph grouping enabled
        results = reader.readtext(input_data, paragraph=True)
        
        extracted_lines = []
        confidences = []
        
        for item in results:
            if len(item) == 3:
                bbox, text, conf = item
                confidences.append(float(conf))
            elif len(item) == 2:
                bbox, text = item
                confidences.append(0.85)
            else:
                continue
                
            if text and text.strip():
                extracted_lines.append(text.strip())
                
        full_text = "\n".join(extracted_lines)
        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        
        if full_text.strip():
            return {
                "text": full_text,
                "confidence": round(avg_conf * 100, 2),
                "method": "EasyOCR (Handwriting & Scene Text Engine)"
            }
    except Exception as e:
        print(f"[OCR EasyOCR Error] {e}")
        
    # Fallback Engine 2: PyTesseract (if binary installed)
    try:
        import pytesseract
        pil_img = Image.open(io.BytesIO(image_bytes))
        tesseract_text = pytesseract.image_to_string(pil_img, config='--psm 6')
        if tesseract_text.strip():
            return {
                "text": tesseract_text.strip(),
                "confidence": 75.0,
                "method": "PyTesseract OCR"
            }
    except Exception as e:
        print(f"[OCR Tesseract Fallback Error] {e}")
        
    return {
        "text": "",
        "confidence": 0.0,
        "error": "Failed to extract readable text from the image. Ensure the image is clear and well-lit."
    }
