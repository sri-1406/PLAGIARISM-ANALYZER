import os
import io
import cv2
import numpy as np
from PIL import Image

_EASYOCR_READER = None

def get_easyocr_reader():
    global _EASYOCR_READER
    if _EASYOCR_READER is None:
        import easyocr
        print("[OCR] Initializing EasyOCR engine for English handwriting...")
        _EASYOCR_READER = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _EASYOCR_READER


def detect_and_crop_document(img):
    """
    Detect document boundary in image and apply perspective transform
    to crop and unskew paper.
    """
    try:
        h, w = img.shape[:2]
        image_area = h * w
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Morphological closing to join edge gaps
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return img

        # Find largest contour that looks like a document (>= 15% of image area)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        doc_cnt = None

        for cnt in contours[:5]:
            area = cv2.contourArea(cnt)
            if area < image_area * 0.15:
                continue
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)
            if len(approx) == 4:
                doc_cnt = approx
                break

        if doc_cnt is None:
            return img

        # Order 4 corners: top-left, top-right, bottom-right, bottom-left
        pts = doc_cnt.reshape(4, 2)
        rect = np.zeros((4, 2), dtype="float32")

        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)] # top-left
        rect[2] = pts[np.argmax(s)] # bottom-right

        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)] # top-right
        rect[3] = pts[np.argmax(diff)] # bottom-left

        (tl, tr, br, bl) = rect
        width_A = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        width_B = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(width_A), int(width_B))

        height_A = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        height_B = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(height_A), int(height_B))

        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))
        return warped
    except Exception as e:
        print(f"[OCR Doc Crop Warning] {e}")
        return img


def deskew_image(img):
    """
    Detect text skew angle and rotate image to straighten text lines horizontally.
    """
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
        # Invert grayscale for text contour detection
        inv = cv2.bitwise_not(gray)
        thresh = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        coords = np.column_stack(np.where(thresh > 0))
        if len(coords) < 100:
            return img

        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Ignore tiny angles or extreme angles (likely false detection)
        if abs(angle) < 0.5 or abs(angle) > 25:
            return img

        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        return rotated
    except Exception as e:
        print(f"[OCR Deskew Warning] {e}")
        return img


def remove_shadows_and_normalize_bg(gray):
    """
    Remove uneven background shadows, lighting gradients, and paper stains
    via morphological background division.
    """
    try:
        # Estimate background illumination using large morphological dilation
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (19, 19))
        bg = cv2.morphologyEx(gray, cv2.MORPH_DILATE, kernel)
        bg = cv2.medianBlur(bg, 21)

        # Divide grayscale by background estimate to normalize light
        normalized = cv2.divide(gray, bg, scale=255.0)
        return np.uint8(np.clip(normalized, 0, 255))
    except Exception as e:
        print(f"[OCR Background Normalization Warning] {e}")
        return gray


def enhance_contrast_and_denoise(norm_gray):
    """
    Enhance handwriting contrast using CLAHE and apply bilateral filtering
    to smooth paper grain while retaining thin ink strokes.
    """
    try:
        # Apply CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(norm_gray)

        # Bilateral filter preserves sharp edges (ink lines) while smoothing noise
        denoised = cv2.bilateralFilter(enhanced, d=7, sigmaColor=50, sigmaSpace=50)
        return denoised
    except Exception as e:
        print(f"[OCR Contrast Enhancement Warning] {e}")
        return norm_gray


def segment_text_lines(gray):
    """
    Segment image into horizontal line strips using row projection profiles.
    Returns a list of image crops, each corresponding to one line of handwriting.
    """
    try:
        h, w = gray.shape[:2]
        # Otsu binarization for line profile
        inv_bin = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

        # Horizontal projection profile (count text pixels per row)
        proj = np.sum(inv_bin, axis=1) // 255

        # Find line bands where text pixel count > threshold
        min_pixels_per_row = max(3, int(w * 0.005))
        in_line = False
        start_y = 0
        line_crops = []

        for y, val in enumerate(proj):
            if not in_line and val > min_pixels_per_row:
                in_line = True
                start_y = y
            elif in_line and val <= min_pixels_per_row:
                in_line = False
                end_y = y
                line_h = end_y - start_y
                if line_h >= 8: # Filter tiny noise lines
                    # Add top and bottom padding
                    pad = max(3, int(line_h * 0.15))
                    crop_y1 = max(0, start_y - pad)
                    crop_y2 = min(h, end_y + pad)
                    line_crops.append((crop_y1, crop_y2, gray[crop_y1:crop_y2, :]))

        if in_line:
            end_y = h
            if end_y - start_y >= 8:
                pad = 4
                crop_y1 = max(0, start_y - pad)
                crop_y2 = min(h, end_y + pad)
                line_crops.append((crop_y1, crop_y2, gray[crop_y1:crop_y2, :]))

        # Sort lines top-to-bottom
        line_crops.sort(key=lambda x: x[0])
        return [crop for (_, _, crop) in line_crops]
    except Exception as e:
        print(f"[OCR Line Segmentation Warning] {e}")
        return []


def extract_handwritten_text(image_input):
    """
    Full Computer Vision + OCR pipeline for Handwritten English Text:
    1. Document detection & perspective cropping
    2. Skew correction / rotation
    3. Shadow & background illumination normalization
    4. CLAHE contrast enhancement & bilateral denoising
    5. Horizontal line segmentation
    6. EasyOCR handwriting line recognition with confidence evaluation & anti-hallucination filtering
    """
    image_bytes = None

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

    try:
        # Decode byte stream to OpenCV BGR image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return {"text": "", "confidence": 0.0, "error": "Failed to decode image format."}

        # Step 1: Detect document boundary and crop/unskew perspective
        cropped_doc = detect_and_crop_document(img)

        # Step 2: Deskew rotation
        deskewed_doc = deskew_image(cropped_doc)

        # Convert to Grayscale
        gray = cv2.cvtColor(deskewed_doc, cv2.COLOR_BGR2GRAY)

        # Step 3: Remove shadows and normalize background illumination
        norm_gray = remove_shadows_and_normalize_bg(gray)

        # Step 4: Enhance contrast (CLAHE) & Denoise (Bilateral Filter)
        cleaned_image = enhance_contrast_and_denoise(norm_gray)

        # Step 5: Segment individual lines
        line_crops = segment_text_lines(cleaned_image)

        reader = get_easyocr_reader()

        final_lines = []
        confidences = []

        if line_crops and len(line_crops) > 0:
            # Process line-by-line in reading order
            for line_img in line_crops:
                results = reader.readtext(
                    line_img,
                    paragraph=False,
                    decoder='greedy',
                    beamWidth=5,
                    batch_size=1,
                    text_threshold=0.3,
                    low_text=0.2,
                    link_threshold=0.3
                )
                line_text_parts = []
                for res in results:
                    if len(res) >= 2:
                        txt = res[1].strip()
                        conf = float(res[2]) if len(res) >= 3 else 0.8
                        # Filter ultra-low confidence hallucinated single symbol noise (< 15% confidence)
                        if conf < 0.15 or (len(txt) == 1 and conf < 0.25 and not txt.isalnum() and txt not in "+-=*/()[]{}%#$@!?.,:;"):
                            continue
                        line_text_parts.append(txt)
                        confidences.append(conf)

                if line_text_parts:
                    final_lines.append(" ".join(line_text_parts))
        else:
            # Fallback: process entire cleaned image at once if line segmentation yielded no distinct lines
            results = reader.readtext(
                cleaned_image,
                paragraph=True,
                decoder='greedy',
                text_threshold=0.3,
                low_text=0.2,
                link_threshold=0.3
            )
            for res in results:
                if len(res) >= 2:
                    txt = res[1].strip()
                    conf = float(res[2]) if len(res) >= 3 else 0.8
                    if conf >= 0.15 and txt:
                        final_lines.append(txt)
                        confidences.append(conf)

        extracted_text = "\n".join(final_lines)
        avg_confidence = float(np.mean(confidences)) if confidences else 0.0

        if extracted_text.strip():
            return {
                "text": extracted_text,
                "confidence": round(avg_confidence * 100, 2),
                "method": "Advanced OpenCV Preprocessing Pipeline + EasyOCR English Handwriting Engine"
            }
        else:
            return {
                "text": "",
                "confidence": 0.0,
                "error": "No readable handwritten text detected after contrast enhancement and line segmentation."
            }

    except Exception as e:
        print(f"[OCR Pipeline Error] {e}")
        return {
            "text": "",
            "confidence": 0.0,
            "error": f"Handwriting OCR pipeline error: {str(e)}"
        }
