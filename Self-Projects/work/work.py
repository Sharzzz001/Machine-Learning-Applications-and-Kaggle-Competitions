import fitz  # PyMuPDF
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import torch

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

    # Step 1: Open PDF and convert to image
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)

    # Increase resolution (DPI) for better OCR accuracy
    zoom = 2  # 2 = 144 DPI, 3 = 216 DPI, etc.
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

    # Step 2: Crop the region
    cropped_img = img.crop(crop_box)

    # Step 3: Load TrOCR model and processor from local path
    processor = TrOCRProcessor.from_pretrained(model_path, local_files_only=True)
    model = VisionEncoderDecoderModel.from_pretrained(model_path, local_files_only=True)
    model.eval()

    # Step 4: Run OCR
    inputs = processor(images=cropped_img, return_tensors="pt")
    with torch.no_grad():
        generated_ids = model.generate(inputs["pixel_values"])
    text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return text.strip()

# === USAGE ===
if __name__ == "__main__":
    pdf_path = "scanned_handwritten.pdf"
    page_number = 0  # First page
    crop_box = (100, 200, 600, 300)  # Adjust this (left, upper, right, lower)
    model_path = "./trocr-handwritten"  # Local folder with trocr-base-handwritten

    result = extract_crop_from_pdf(pdf_path, page_number, crop_box, model_path)
    print("Extracted Text:", result)
