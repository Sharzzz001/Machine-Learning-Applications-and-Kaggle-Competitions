import fitz  # PyMuPDF
from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
import os

def load_pdf_page_as_image(pdf_path, page_number, dpi=300):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_number)
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img

def crop_image(image, left, upper, right, lower):
    return image.crop((left, upper, right, lower))

def run_tr_ocr(model_path, image):
    processor = TrOCRProcessor.from_pretrained(model_path)
    model = VisionEncoderDecoderModel.from_pretrained(model_path)
    model.eval()

    pixel_values = processor(images=image, return_tensors="pt").pixel_values

    with torch.no_grad():
        generated_ids = model.generate(pixel_values)
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    return generated_text

def main():
    # === Configuration ===
    pdf_path = "your_file.pdf"
    page_number = 0  # 0-indexed
    crop_box = (100, 200, 600, 400)  # (left, upper, right, lower)
    trocr_model_path = "./trocr-handwritten"  # Local path to downloaded TrOCR

    # === Load and Crop Image ===
    full_image = load_pdf_page_as_image(pdf_path, page_number)
    cropped_image = crop_image(full_image, *crop_box)
    
    # Optional: View the cropped image
    # cropped_image.show()

    # === Run OCR ===
    text = run_tr_ocr(trocr_model_path, cropped_image)
    print("OCR Output:", text)

if __name__ == "__main__":
    main()
