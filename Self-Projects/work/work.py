import fitz  # PyMuPDF
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch
import cv2
import numpy as np

def deskew_image(img, max_skew=15):
    """
    Deskew an image by detecting skew angle from text-like regions.
    """
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Use adaptive threshold to detect handwriting/printed text
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY_INV, 15, 10
    )

    coords = np.column_stack(np.where(thresh > 0))

    if len(coords) == 0:
        print("⚠️ No foreground detected — skipping deskew.")
        return img

    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle += 90

    if abs(angle) < max_skew:
        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(img, M, (w, h),
                                 flags=cv2.INTER_CUBIC,
                                 borderMode=cv2.BORDER_REPLICATE)
        print(f"✅ Deskewed by {angle:.2f} degrees.")
        return rotated
    else:
        print(f"⛔ Skew angle too large ({angle:.2f}°) — skipping.")
        return img

def extract_crop_from_pdf(pdf_path, page_number, crop_box, model_path):
    """
    Extract cropped region from a scanned PDF and apply handwritten OCR using TrOCR.

    Args:
        pdf_path (str): Path to PDF file.
        page_number (int): Page number to extract (0-based index).
        crop_box (tuple): (left, upper, right, lower) pixel coordinates.
        model_path (str): Local directory with TrOCR handwritten model.

    Returns:
        str: Extracted handwritten text.
    """
    # Step 1: Open PDF and convert to high-res image
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)

    zoom = 2  # 144 DPI
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Step 2: Convert to OpenCV format and deskew
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    img_deskewed = deskew_image(img_cv)

    # Convert back to PIL for cropping
    img_pil_deskewed = Image.fromarray(cv2.cvtColor(img_deskewed, cv2.COLOR_BGR2RGB))

    # Step 3: Crop region of interest
    cropped_img = img_pil_deskewed.crop(crop_box)

    # Step 4: Load TrOCR
    processor = TrOCRProcessor.from_pretrained(model_path, local_files_only=True)
    model = VisionEncoderDecoderModel.from_pretrained(model_path, local_files_only=True)
    model.eval()

    # Step 5: OCR inference
    inputs = processor(images=cropped_img, return_tensors="pt")
    with torch.no_grad():
        generated_ids = model.generate(inputs["pixel_values"])
    text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return text.strip()

# === USAGE ===
if __name__ == "__main__":
    pdf_path = "scanned_handwritten.pdf"
    page_number = 0
    crop_box = (100, 200, 600, 300)  # Adjust this based on your need
    model_path = "./trocr-handwritten"

    result = extract_crop_from_pdf(pdf_path, page_number, crop_box, model_path)
    print("Extracted Text:", result)
