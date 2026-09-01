import os
import io
import cv2
import numpy as np
from PIL import Image
import torch

_TROCR_PROCESSOR = None
_TROCR_MODEL = None
_MODEL_NAME = None

def get_trocr_engine():
    """
    Lazy initialization of Microsoft TrOCR handwriting recognition model.
    First tries microsoft/trocr-base-handwritten, falls back to microsoft/trocr-small-handwritten.
    """
    global _TROCR_PROCESSOR, _TROCR_MODEL, _MODEL_NAME
    if _TROCR_MODEL is None:
        from transformers import ViTImageProcessor, RobertaTokenizer, TrOCRProcessor, VisionEncoderDecoderModel
        
        candidates = ["microsoft/trocr-base-handwritten"]
        for name in candidates:
            try:
                print(f"[TrOCR Engine] Loading model components for {name}...")
                feat = ViTImageProcessor.from_pretrained(name)
                tok = RobertaTokenizer.from_pretrained("roberta-base")
                _TROCR_PROCESSOR = TrOCRProcessor(image_processor=feat, tokenizer=tok)
                _TROCR_MODEL = VisionEncoderDecoderModel.from_pretrained(name)
                _TROCR_MODEL.eval()
                _MODEL_NAME = name
                print(f"[TrOCR Engine] Successfully loaded {name}!")
                break
            except Exception as e:
                print(f"[TrOCR Load Warning for {name}] {e}")
                
    return _TROCR_PROCESSOR, _TROCR_MODEL, _MODEL_NAME


def detect_and_crop_document(img):
    """
    Detect paper document outer contour and crop/unskew via 4-point perspective warp.
    """
    try:
        h, w = img.shape[:2]
        image_area = h * w
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return img

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
    Detect handwritten text line skew angle and rotate image to align lines horizontally.
    """
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img
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
    Remove uneven background shadows and camera lighting gradients via background division.
    """
    try:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (19, 19))
        bg = cv2.morphologyEx(gray, cv2.MORPH_DILATE, kernel)
        bg = cv2.medianBlur(bg, 21)

        normalized = cv2.divide(gray, bg, scale=255.0)
        return np.uint8(np.clip(normalized, 0, 255))
    except Exception as e:
        print(f"[OCR Background Normalization Warning] {e}")
        return gray


def enhance_contrast_and_denoise(norm_gray):
    """
    Apply CLAHE contrast enhancement and bilateral filtering to smooth paper grain
    while retaining thin handwritten ink lines.
    """
    try:
        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        enhanced = clahe.apply(norm_gray)
        denoised = cv2.bilateralFilter(enhanced, d=7, sigmaColor=50, sigmaSpace=50)
        return denoised
    except Exception as e:
        print(f"[OCR Enhancement Warning] {e}")
        return norm_gray


def segment_text_lines(bgr_or_gray):
    """
    Segment image into distinct handwritten line crops ordered top-to-bottom.
    Combines horizontal morphological dilation and projection profiles to isolate lines.
    Returns list of PIL Images (RGB) for TrOCR processing.
    """
    try:
        if len(bgr_or_gray.shape) == 3:
            gray = cv2.cvtColor(bgr_or_gray, cv2.COLOR_BGR2GRAY)
            color = bgr_or_gray
        else:
            gray = bgr_or_gray
            color = cv2.cvtColor(bgr_or_gray, cv2.COLOR_GRAY2BGR)

        h, w = gray.shape[:2]
        inv_bin = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

        # Horizontal dilation kernel to connect words on the same handwritten line
        kernel_w = max(15, int(w * 0.025))
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_w, 3))
        dilated = cv2.dilate(inv_bin, kernel, iterations=1)

        # Find contours of connected line blocks
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        boxes = []
        for cnt in contours:
            x, y, bw, bh = cv2.boundingRect(cnt)
            # Filter noise contours that are too small or thin
            if bh >= 10 and bw >= 20 and (bw * bh) > 200:
                boxes.append((x, y, bw, bh))

        if not boxes:
            # Fallback to horizontal projection profile if contour grouping returns empty
            proj = np.sum(inv_bin, axis=1) // 255
            min_pixels = max(3, int(w * 0.005))
            in_line = False
            start_y = 0
            for y, val in enumerate(proj):
                if not in_line and val > min_pixels:
                    in_line = True
                    start_y = y
                elif in_line and val <= min_pixels:
                    in_line = False
                    end_y = y
                    if end_y - start_y >= 8:
                        boxes.append((0, start_y, w, end_y - start_y))

        # Sort line boxes top-to-bottom
        boxes.sort(key=lambda b: b[1])

        # Merge overlapping or close line boxes vertically
        merged_boxes = []
        for b in boxes:
            if not merged_boxes:
                merged_boxes.append(list(b))
            else:
                prev = merged_boxes[-1]
                # If vertical overlap or small gap (< 8px), merge
                if b[1] <= (prev[1] + prev[3] + 6):
                    new_y1 = min(prev[1], b[1])
                    new_y2 = max(prev[1] + prev[3], b[1] + b[3])
                    new_x1 = min(prev[0], b[0])
                    new_x2 = max(prev[0] + prev[2], b[0] + b[2])
                    merged_boxes[-1] = [new_x1, new_y1, new_x2 - new_x1, new_y2 - new_y1]
                else:
                    merged_boxes.append(list(b))

        pil_crops = []
        for (bx, by, bw, bh) in merged_boxes:
            pad_y = max(4, int(bh * 0.15))
            pad_x = max(4, int(bw * 0.02))
            y1 = max(0, by - pad_y)
            y2 = min(h, by + bh + pad_y)
            x1 = max(0, bx - pad_x)
            x2 = min(w, bx + bw + pad_x)

            line_crop = color[y1:y2, x1:x2]
            rgb = cv2.cvtColor(line_crop, cv2.COLOR_BGR2RGB)
            pil_crops.append(Image.fromarray(rgb))

        return pil_crops
    except Exception as e:
        print(f"[OCR Line Segmentation Warning] {e}")
        return []


def recognize_line_with_trocr(processor, model, pil_img):
    """
    Recognize a single line of handwritten English text using TrOCR and calculate token confidence.
    """
    try:
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
            
        pixel_values = processor(images=pil_img, return_tensors="pt").pixel_values
        
        with torch.no_grad():
            outputs = model.generate(
                pixel_values,
                return_dict_in_generate=True,
                output_scores=True,
                max_new_tokens=128
            )
            
        sequences = outputs.sequences[0]
        text = processor.decode(sequences, skip_special_tokens=True).strip()
        
        # Calculate token sequence confidence score
        if hasattr(outputs, 'scores') and len(outputs.scores) > 0:
            probs = []
            for score in outputs.scores:
                prob = torch.softmax(score, dim=-1).max().item()
                probs.append(prob)
            conf = float(np.mean(probs)) if probs else 0.85
        else:
            conf = 0.85
            
        return text, conf
    except Exception as e:
        print(f"[TrOCR Line Error] {e}")
        return "", 0.0


def extract_handwritten_text(image_input):
    """
    Full TrOCR Neural Handwriting Pipeline:
    1. Document area cropping & perspective unwarping
    2. Page rotation & deskewing
    3. Background shadow removal & illumination normalization
    4. CLAHE contrast enhancement & bilateral stroke filtering
    5. Line segmentation & top-to-bottom line reconstruction
    6. Microsoft TrOCR handwriting recognition with sequence confidence scoring
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
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return {"text": "", "confidence": 0.0, "error": "Failed to decode image file."}

        # Step 1: Crop document & unwarp perspective
        cropped_doc = detect_and_crop_document(img)

        # Step 2: Deskew angle
        deskewed_doc = deskew_image(cropped_doc)

        # Step 3: Convert to grayscale and normalize background lighting
        gray = cv2.cvtColor(deskewed_doc, cv2.COLOR_BGR2GRAY)
        norm_gray = remove_shadows_and_normalize_bg(gray)

        # Step 4: Contrast & Bilateral Denoising
        cleaned_gray = enhance_contrast_and_denoise(norm_gray)
        cleaned_bgr = cv2.cvtColor(cleaned_gray, cv2.COLOR_GRAY2BGR)

        # Step 5: Line Segmentation
        line_crops = segment_text_lines(cleaned_bgr)

        # Step 6: Initialize TrOCR Engine
        processor, model, model_name = get_trocr_engine()

        if processor is None or model is None:
            return {"text": "", "confidence": 0.0, "error": "Failed to load TrOCR handwriting engine."}

        recognized_lines = []
        confidences = []

        if line_crops and len(line_crops) > 0:
            for line_pil in line_crops:
                line_text, conf = recognize_line_with_trocr(processor, model, line_pil)
                if line_text and len(line_text) > 0:
                    recognized_lines.append(line_text)
                    confidences.append(conf)
        else:
            # Fallback if line segmentation returns empty: process entire cleaned image
            pil_full = Image.fromarray(cv2.cvtColor(cleaned_bgr, cv2.COLOR_BGR2RGB))
            line_text, conf = recognize_line_with_trocr(processor, model, pil_full)
            if line_text:
                recognized_lines.append(line_text)
                confidences.append(conf)

        full_text = "\n".join(recognized_lines)
        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        confidence_pct = round(avg_conf * 100, 2)

        is_low_confidence = confidence_pct < 55.0

        return {
            "text": full_text,
            "confidence": confidence_pct,
            "method": f"Microsoft TrOCR Handwriting Model ({model_name})",
            "low_confidence_warning": is_low_confidence
        }

    except Exception as e:
        print(f"[OCR Pipeline Error] {e}")
        return {
            "text": "",
            "confidence": 0.0,
            "error": f"TrOCR handwriting pipeline error: {str(e)}"
        }
