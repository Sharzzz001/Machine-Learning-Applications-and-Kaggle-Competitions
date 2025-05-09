import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io

# If Tesseract is not in your system PATH, set its full path
# Example: r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = r"C:\Path\To\tesseract.exe"

# Define rules: {filename: (keyword, page_number)}
PDF_RENAME_RULES = {
    "AAF.pdf": ("account opening form", 0),  # 0-based index
    "KYC.pdf": ("kyc documentation", 1),
    # Add more rules as needed
}

def extract_text_from_page(pdf_path, page_number):
    try:
        with fitz.open(pdf_path) as doc:
            if page_number >= len(doc):
                return ""
            page = doc.load_page(page_number)
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data)).convert("RGB")
            text = pytesseract.image_to_string(image)
            return text.lower()
    except Exception as e:
        print(f"Error extracting text from {pdf_path} page {page_number + 1}: {e}")
        return ""

def determine_new_filename(pdf_path):
    for new_filename, (keyword, page_num) in PDF_RENAME_RULES.items():
        text = extract_text_from_page(pdf_path, page_num)
        if keyword in text:
            return new_filename
    return None

def process_pdf(pdf_path, output_dir):
    new_filename = determine_new_filename(pdf_path)
    if new_filename:
        new_path = os.path.join(output_dir, new_filename)
        os.rename(pdf_path, new_path)
        print(f"Renamed: {os.path.basename(pdf_path)} → {new_filename}")
    else:
        print(f"No match found for: {os.path.basename(pdf_path)}")

def process_all_pdfs(folder_path):
    for file in os.listdir(folder_path):
        if file.lower().endswith(".pdf"):
            process_pdf(os.path.join(folder_path, file), folder_path)

# Example usage
if __name__ == "__main__":
    input_folder = r"C:\Path\To\Your\PDFs"
    process_all_pdfs(input_folder)


import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import matplotlib.pyplot as plt

# Optional: set Tesseract path if it's not in your system PATH
# pytesseract.pytesseract.tesseract_cmd = r"C:\Path\To\tesseract.exe"

def extract_text_and_image(pdf_path, page_number):
    with fitz.open(pdf_path) as doc:
        if page_number >= len(doc):
            print(f"Page {page_number + 1} out of range.")
            return None, None
        page = doc.load_page(page_number)
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        text = pytesseract.image_to_string(image)
        return image, text

def test_pdf_page():
    pdf_path = input("Enter full path to PDF: ").strip()
    page_input = input("Enter page number to test (1-based): ").strip()

    try:
        page_number = int(page_input) - 1
        image, text = extract_text_and_image(pdf_path, page_number)
        if image:
            print("\n--- OCR Extracted Text ---\n")
            print(text.strip())
            print("\n--- Displaying Image ---")
            plt.imshow(image)
            plt.axis("off")
            plt.show()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_pdf_page()

